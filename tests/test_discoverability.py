import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/build.py"
spec = importlib.util.spec_from_file_location("site_build", MODULE)
site_build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site_build)


def png_size(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"{path} is not a PNG")
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


class DiscoverabilityTests(unittest.TestCase):
    def test_build_keeps_social_tags_and_cover(self):
        site_build.build()
        page = (ROOT / "dist" / "index.html").read_text(encoding="utf-8")
        for marker in site_build.DISCOVERABILITY:
            self.assertIn(marker, page)
        preview = ROOT / "dist" / "assets" / "social-preview.png"
        self.assertEqual(png_size(preview), (1280, 640))
        self.assertEqual(png_size(ROOT / "assets" / "social-preview.png"), (1280, 640))
        linked = json.loads(page.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0])
        self.assertEqual(linked["@type"], "WebSite")
        self.assertEqual(linked["name"], "FreeCloud")
        self.assertEqual(linked["url"], "https://aipmandy.github.io/FreeCloud/")
        self.assertIn("author", linked)
        self.assertNotIn("aggregateRating", linked)
        self.assertNotIn("offers", linked)

    def test_readme_keeps_quick_start_and_author_contact(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/update_offers.py\npython3 scripts/build.py\npython3 -m http.server 8765 --directory dist", readme)
        self.assertIn("AI酋长Andy", readme)
        self.assertIn("流量 AI 联合创始人、星觉 AI 创始人", readme)
        self.assertIn("星觉科技", readme)
        self.assertIn("北京", readme)
        self.assertIn("微信 AIPMAndy", readme)
        self.assertIn("微信号 AIPMAndy", readme)
        self.assertIn("查看活动", readme)
        self.assertIn("data/links.json", readme)


if __name__ == "__main__":
    unittest.main()
