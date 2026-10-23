#!/usr/bin/env python3
"""Fail-closed integrity check for the static Pages dashboard.

The site is intentionally hand-audited, not generated from a single model
receipt. CI checks that all retained downloadable rasters are explicitly
listed, and that the current literal-protocol run card remains negative.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGES = (DOCS / "index.html", DOCS / "executive-summary.html", DOCS / "download-status.html")
CANDIDATES = (
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
            raise SystemExit(f"audit-only raster missing from dashboard or disk: {name}")
    import json
    review = json.loads((DOCS / "evidence" / "review-20261023-run-card.json").read_text())
    if (review.get("verdict") != "negative" or review.get("submission_ready") is not False
            or review.get("safe_to_submit") is not False
            or review.get("candidate_generated_this_review") is not False
            or review.get("experiments_run_this_review") != 0):
        raise SystemExit("current review card contradicts the negative no-candidate decision")
    print("Static site integrity: PASS; six retained audit-only rasters listed; none authorized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
