#!/usr/bin/env python3
"""Build a dependency-free static site; only public files enter dist/."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "dist"


def build():
    TARGET.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "index.html", TARGET / "index.html")
    shutil.copytree(ROOT / "assets", TARGET / "assets", dirs_exist_ok=True)
    (TARGET / "data").mkdir(exist_ok=True)
    for name in ("offers.json", "links.json"):
        data = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
        (TARGET / "data" / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (TARGET / ".nojekyll").touch()
    print(f"Built {TARGET}")


if __name__ == "__main__":
    build()
