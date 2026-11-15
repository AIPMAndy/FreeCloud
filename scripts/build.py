#!/usr/bin/env python3
"""Build a dependency-free static site; only public files enter dist/."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "dist"
# Copied with index.html so a later offer refresh cannot publish a page that dropped them.
DISCOVERABILITY = (
    'rel="canonical"',
    'property="og:title"',
    'property="og:description"',
    'property="og:url"',
    'property="og:image"',
    'property="og:image:width" content="1280"',
    'property="og:image:height" content="640"',
    'name="twitter:card" content="summary_large_image"',
    'name="twitter:image"',
    'application/ld+json',
    'assets/social-preview.png',
)


def build():
    TARGET.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "index.html", TARGET / "index.html")
    shutil.copytree(ROOT / "assets", TARGET / "assets", dirs_exist_ok=True)
    page = (TARGET / "index.html").read_text(encoding="utf-8")
    missing = [marker for marker in DISCOVERABILITY if marker not in page]
    preview = TARGET / "assets" / "social-preview.png"
    if missing or not preview.is_file():
        detail = ", ".join(missing) or "assets/social-preview.png"
        raise SystemExit(f"dist is missing discoverability output: {detail}")
    (TARGET / "data").mkdir(exist_ok=True)
    for name in ("offers.json", "links.json"):
        data = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
        (TARGET / "data" / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (TARGET / ".nojekyll").touch()
    print(f"Built {TARGET}")


if __name__ == "__main__":
    build()
