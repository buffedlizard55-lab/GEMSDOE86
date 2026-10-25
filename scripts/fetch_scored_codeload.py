#!/usr/bin/env python3
"""Codeload fallback for scripts/fetch_scored_ext.py (no REST-API quota used).

Streams ``codeload.github.com/<owner>/<site>/tar.gz/HEAD`` and keeps only
``.tif`` members whose normalised basename equals a scored name of that site.
The tarball's top directory carries the resolved commit SHA, which is recorded
with bytes and SHA-256 in ``docs/evidence/scored-ext-receipt.json`` (merged).
Comparison/likelihood inputs only -- never features or dots.
"""
from __future__ import annotations

import json
import re
import sys
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]
from gems86_llp import fleet as FL  # noqa: E402

OWNER = "buffedlizard55-lab"
OUT = ROOT / "data/scored_ext"
RECEIPT = ROOT / "docs/evidence/scored-ext-receipt.json"


def main(argv=None) -> int:
    sites_only = set(argv or sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    cands = [c for c in FL.scored_candidates(ROOT) if not c["files"]]
    by_site: dict[str, list[dict]] = {}
    for c in cands:
        if not sites_only or c["site"] in sites_only:
            by_site.setdefault(c["site"], []).append(c)
    prev = json.loads(RECEIPT.read_text()) if RECEIPT.is_file() else {"files": [], "errors": []}
    rows = [r for r in prev.get("files", [])]
    errors = []
    for site, items in sorted(by_site.items()):
        pats = [(c, re.compile(r"^([a-z0-9]+[-_])?" + re.escape(FL._norm(c["submission"])) + r"$")) for c in items]
        url = f"https://codeload.github.com/{OWNER}/{site}/tar.gz/HEAD"
        found = 0
        try:
            with urllib.request.urlopen(url, timeout=600) as resp, tarfile.open(fileobj=resp, mode="r|gz") as tf:
                for m in tf:
                    if not m.isfile() or not m.name.lower().endswith(".tif"):
                        continue
                    base = FL._norm(m.name)
                    hit = [c for c, p in pats if p.match(base)]
                    if not hit:
                        continue
                    dest = OUT / f"{site}__{Path(m.name).name}"
                    with tf.extractfile(m) as src, dest.open("wb") as fh:
                        fh.write(src.read())
                    top = m.name.split("/", 1)[0]
                    rows.append(dict(site=site, submission=hit[0]["submission"], repo=f"{OWNER}/{site}",
                                     tar_top=top, path=m.name.split("/", 1)[1], bytes=dest.stat().st_size,
                                     sha256=FL.sha256(dest), dest=str(dest.relative_to(ROOT)),
                                     via="codeload tar.gz/HEAD"))
                    found += 1
                    print(f"ok {site} {Path(m.name).name}", flush=True)
        except Exception as exc:
            errors.append(dict(site=site, error=str(exc)[:200]))
            continue
        if not found:
            errors.append(dict(site=site, error="no matching .tif in HEAD tarball",
                               submissions=[c["submission"] for c in items]))
    RECEIPT.write_text(json.dumps(dict(
        evidence_class="DATA-MEASUREMENT (owner public repos via codeload; not organizer bytes)",
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        files=rows, errors=errors), indent=1) + "\n")
    print(json.dumps(dict(fetched=len(rows), errors=len(errors))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
