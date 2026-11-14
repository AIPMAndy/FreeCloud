#!/usr/bin/env python3
"""Collect public official offer pages. No account, token or paid API required."""
import argparse
import concurrent.futures
import hashlib
import json
import re
import sys
import urllib.request
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ignored = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.ignored:
            self.ignored -= 1

    def handle_data(self, value):
        if not self.ignored and value.strip():
            self.parts.append(value.strip())


class ActivityLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, value):
        if self.current:
            self.parts.append(value)

    def handle_endtag(self, tag):
        if tag == "a" and self.current:
            self.links.append((self.current, " ".join(self.parts)))
            self.current = None


def discover_activity(html, base_url):
    parser = ActivityLinks()
    parser.feed(html)
    for href, label in parser.links:
        url = urljoin(base_url, href)
        parsed = urlparse(url)
        if parsed.scheme == "https" and parsed.hostname == "cloud.tencent.com" and parsed.path.startswith("/act/pro/"):
            if re.search(r"Token Plan|LH Agent|服务器|新客|大促|双11|双十一|年终", label, re.IGNORECASE):
                return url
    return base_url


def visible_text(html):
    parser = PageText()
    parser.feed(html)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def source_region(text, source):
    anchor = source.get("anchor")
    if anchor and anchor in text:
        text = text[text.index(anchor):]
    stop = source.get("stop")
    if stop and stop in text:
        text = text[:text.index(stop)]
    return text


def read_page(url):
    request = urllib.request.Request(url, headers={
        "User-Agent": "FreeCloud/1.0 (+https://github.com/AIPMAndy/FreeCloud)",
        "Accept": "text/html,application/xhtml+xml",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(5_000_001)
        if len(raw) > 5_000_000:
            raise ValueError("page exceeds 5 MB")
        return raw.decode(response.headers.get_content_charset() or "utf-8", "replace"), response.url


def fetch_source(source):
    html, resolved_url = read_page(source["url"])
    if source.get("discoverActivity"):
        campaign_url = discover_activity(html, resolved_url)
        if campaign_url != resolved_url:
            html, resolved_url = read_page(campaign_url)
    text = visible_text(html)
    if len(text) < 100:
        raise ValueError("official page did not contain usable text")
    return {"text": source_region(text, source), "resolvedUrl": resolved_url}


def extract_offer(spec, text):
    pattern = spec.get("pricePattern") or spec["benefitPattern"]
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    amount = match.groupdict().get("amount")
    return {
        "amount": float(amount) if amount else None,
        "priceLabel": f"¥{amount}" if amount else spec["benefitLabel"],
        "priceSuffix": spec.get("priceSuffix", "限时活动"),
        "evidence": match.group(0)[:130],
    }


def extract_signals(text):
    """Small source excerpts, not automatically inferred product or checkout prices."""
    pattern = r"(?:低至\s*)?(?:[¥￥]\s*\d[\d.,]*\s*(?:元)?|\d+(?:\.\d+)?\s*元)(?:\s*[/／]\s*(?:年|月|人|秒))?(?:起)?|\d+(?:\.\d+)?\s*折(?:起)?|双倍\s*Credits|免费试用"
    signals, seen = [], set()
    for match in re.finditer(pattern, text, re.IGNORECASE):
        snippet = text[max(0, match.start() - 20): min(len(text), match.end() + 24)].strip()
        if snippet in seen or re.search(r"返佣|返利|销售热线|分享赚|现金激励", snippet):
            continue
        seen.add(snippet)
        signals.append(snippet)
        if len(signals) == 4:
            break
    return signals


def collect(catalog, previous, fetched, now):
    old_offers = {offer["id"]: offer for offer in previous.get("offers", [])}
    old_sources = {source["id"]: source for source in previous.get("sources", [])}
    sources = []
    for source in catalog["sources"]:
        result = fetched[source["id"]]
        old = old_sources.get(source["id"], {})
        record = {**source, "checkedAt": now}
        record.pop("anchor", None)
        record.pop("stop", None)
        if "error" in result:
            record.update(status="unavailable", error=result["error"], signals=old.get("signals", []),
                          verifiedAt=old.get("verifiedAt"), changedAt=old.get("changedAt"), fingerprint=old.get("fingerprint"))
        else:
            signals = extract_signals(result["text"])
            fingerprint = hashlib.sha256(json.dumps(signals, ensure_ascii=False).encode()).hexdigest()
            record.update(status="ok", signals=signals, verifiedAt=now, resolvedUrl=result["resolvedUrl"],
                          fingerprint=fingerprint, changedAt=now if fingerprint != old.get("fingerprint") else old.get("changedAt", now))
        sources.append(record)
    offers, changes = [], []
    for spec in catalog["offers"]:
        old = old_offers.get(spec["id"], {})
        result = fetched[spec["sourceId"]]
        extracted = extract_offer(spec, result["text"]) if "text" in result else None
        public = {key: value for key, value in spec.items() if key not in {"pricePattern", "benefitPattern", "benefitLabel"}}
        public["checkedAt"] = now
        if extracted:
            public.update(extracted, status="verified", verifiedAt=now)
            changed = old.get("priceLabel") != extracted["priceLabel"] or old.get("priceSuffix") != extracted["priceSuffix"]
            public["changedAt"] = now if changed else old.get("changedAt", now)
            if changed:
                changes.append({"offerId": spec["id"], "title": spec["title"], "provider": spec["provider"],
                                "before": old.get("priceLabel"), "after": extracted["priceLabel"], "at": now})
        elif old.get("verifiedAt"):
            public.update({key: old.get(key) for key in ("amount", "priceLabel", "priceSuffix", "evidence", "verifiedAt", "changedAt")})
            public["status"] = "stale"
        else:
            public.update(status="unconfirmed", amount=None, priceLabel="查看活动", priceSuffix="实时优惠", verifiedAt=None, changedAt=None)
        offers.append(public)
    history = (changes + previous.get("changes", []))[:50]
    return {"generatedAt": now, "sources": sources, "offers": offers, "changes": history}


def load_json(path, fallback=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/offers.json")
    args = parser.parse_args()
    catalog = load_json(ROOT / "data/catalog.json")
    previous = load_json(args.output, {})
    fetched = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(fetch_source, source): source for source in catalog["sources"]}
        for future in concurrent.futures.as_completed(pending):
            source = pending[future]
            try:
                fetched[source["id"]] = future.result()
                print(f"OK {source['id']}")
            except Exception as error:
                fetched[source["id"]] = {"error": f"{type(error).__name__}: {error}"}
                print(f"WARN {source['id']}: {error}", file=sys.stderr)
    now = datetime.now(UTC).isoformat(timespec="seconds")
    data = collect(catalog, previous, fetched, now)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(args.output)
    verified = sum(offer["status"] == "verified" for offer in data["offers"])
    print(f"Verified {verified}/{len(data['offers'])} offers; {len(data['changes'])} history entries")
    if not any("text" in result for result in fetched.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
