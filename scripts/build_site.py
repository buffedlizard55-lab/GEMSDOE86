#!/usr/bin/env python3
"""Fail-closed integrity check for the hand-audited static Pages dashboard.

The parallel integration made the submit/no-submit decision depend on several
independent run cards. Keeping the final HTML explicit is safer than generating
an optimistic page from one lane's receipt. CI calls this script and fails if a
linked local artifact disappears or forbidden readiness language returns.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGES = (DOCS / "index.html", DOCS / "executive-summary.html")
CANDIDATES = (
    "gems86-h86-wvb-submod300-37654dots-20261023T001614Z-zeros.tif",
    "gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.tif",
    "gems86-rmrb-kthu-rtp-37654-20261022-DO-NOT-SUBMIT.tif",
    "gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif",
    "gems86-gmc-linepost-90568d-20261022T222859Z-900ceac1-zeros.tif",
    "gems86-gmc-linepost-offcat-90568d-20261022T224539Z-e6f914e4-zeros.tif",
    "gems86-h86-edge2of5-dotted38000-20261022T225931Z-70513125-zeros.tif",
)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        self.values.extend(value for key, value in attrs if key in {"href", "src"})


def main() -> int:
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        if "OK TO DOWNLOAD AND SUBMIT" in text:
            raise SystemExit(f"fail-closed site violation in {page}: unauthorized readiness phrase")
        if "DO NOT SUBMIT" not in text:
            raise SystemExit(f"missing negative decision in {page}")
        parser = Links()
        parser.feed(text)
        for link in parser.values:
            if link.startswith(("http:", "https:", "mailto:", "#")):
                continue
            target = page.parent / link.split("#", 1)[0]
            if not target.exists():
                raise SystemExit(f"broken local link: {page} -> {link}")
    index = (DOCS / "index.html").read_text(encoding="utf-8")
    for name in CANDIDATES:
        if name not in index or not (DOCS / "downloads" / name).is_file():
            raise SystemExit(f"candidate missing from dashboard or disk: {name}")
    print("Static site integrity: PASS; seven candidates listed; none authorized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
