import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts/update_offers.py"
spec = importlib.util.spec_from_file_location("collector", MODULE)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.offer = {"id": "test", "provider": "aliyun", "sourceId": "official", "referral": "aliyun",
                      "title": "Server", "pricePattern": r"新客 (?P<amount>\d+)元/年", "priceSuffix": "/ 年"}
        self.catalog = {"sources": [{"id": "official", "url": "https://www.aliyun.com/", "provider": "aliyun"}], "offers": [self.offer]}

    def test_scripts_cannot_create_a_price(self):
        text = collector.visible_text('<script>新客 1元/年</script><style>.x{}</style><p>新客 68元/年</p>')
        self.assertEqual(collector.extract_offer(self.offer, text)["amount"], 68)

    def test_unavailable_source_retains_last_price_but_marks_stale(self):
        first = collector.collect(self.catalog, {}, {"official": {"text": "新客 68元/年", "resolvedUrl": "https://www.aliyun.com/"}}, "first")
        second = collector.collect(self.catalog, first, {"official": {"error": "timeout"}}, "second")
        self.assertEqual(second["offers"][0]["status"], "stale")
        self.assertEqual(second["offers"][0]["priceLabel"], "¥68")
        self.assertEqual(second["offers"][0]["verifiedAt"], "first")
        self.assertEqual(second["sources"][0]["status"], "unavailable")

    def test_price_change_has_history_and_does_not_repeat(self):
        def result(price):
            return {"official": {"text": f"新客 {price}元/年", "resolvedUrl": "https://www.aliyun.com/"}}
        first = collector.collect(self.catalog, {}, result(68), "first")
        second = collector.collect(self.catalog, first, result(38), "second")
        third = collector.collect(self.catalog, second, result(38), "third")
        self.assertEqual(second["changes"][0]["before"], "¥68")
        self.assertEqual(second["changes"][0]["after"], "¥38")
        self.assertEqual(len(second["changes"]), len(third["changes"]))
        self.assertEqual(third["offers"][0]["changedAt"], "second")

    def test_missing_price_does_not_become_free(self):
        result = collector.collect(self.catalog, {}, {"official": {"text": "询价中", "resolvedUrl": "https://www.aliyun.com/"}}, "now")
        self.assertIsNone(result["offers"][0]["amount"])
        self.assertEqual(result["offers"][0]["status"], "unconfirmed")

    def test_source_region_removes_unrelated_footer_prices(self):
        text = collector.source_region("header 开始 新客 68元/年 页尾 免费试用", {"anchor": "开始", "stop": "页尾"})
        self.assertNotIn("免费试用", text)

    def test_discovers_current_official_campaign_instead_of_fixed_month(self):
        html = '<a href="https://cloud.tencent.com/act/pro/center">企业中心</a><a href="https://other.example/act/pro/sale">新客1元</a><a href="/act/pro/new-campaign">Token Plan 新客特惠</a>'
        self.assertEqual(collector.discover_activity(html, "https://cloud.tencent.com/act"), "https://cloud.tencent.com/act/pro/new-campaign")

    def test_discovery_falls_back_to_current_activity_index(self):
        self.assertEqual(collector.discover_activity('<a href="/docs">文档</a>', "https://cloud.tencent.com/act"), "https://cloud.tencent.com/act")


if __name__ == "__main__":
    unittest.main()
