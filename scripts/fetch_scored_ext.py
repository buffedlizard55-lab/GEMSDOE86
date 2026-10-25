#!/usr/bin/env python3
"""Fetch scored fleet rasters that are absent from the pinned registry snapshot.

For every OWNER-REPORTED score row in ``registry/prior_scores.csv`` without
local bytes, list the site repository tree via ``gh api`` and download each
``.tif`` blob whose normalised basename equals the scored name (optional site
prefix, encoding suffixes ignored).  Files land in the git-ignored
``data/scored_ext/`` as ``SITE__basename.tif``; a receipt with repo, ref, path,
blob id, bytes and SHA-256 is written to ``docs/evidence/scored-ext-receipt.json``.
These bytes are comparison/likelihood inputs only -- never features or dots.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]
from gems86_llp import fleet as FL  # noqa: E402

OWNER = "buffedlizard55-lab"
OUT = ROOT / "data/scored_ext"
RECEIPT = ROOT / "docs/evidence/scored-ext-receipt.json"
MAX_BYTES = 60_000_000


def gh_json(endpoint: str):
    r = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:200])
    return json.loads(r.stdout)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cands = [c for c in FL.scored_candidates(ROOT) if not c["files"]]
    by_site: dict[str, list[dict]] = {}
    for c in cands:
        by_site.setdefault(c["site"], []).append(c)
    rows, errors = [], []
    for site, items in sorted(by_site.items()):
        try:
            meta = gh_json(f"repos/{OWNER}/{site}")
            ref = gh_json(f"repos/{OWNER}/{site}/commits/{meta['default_branch']}")["sha"]
            tree = gh_json(f"repos/{OWNER}/{site}/git/trees/{ref}?recursive=1")
        except Exception as exc:  # unreachable repo: a stated scope limit
            errors.append(dict(site=site, error=str(exc)))
            continue
        tifs = [t for t in tree.get("tree", []) if t["type"] == "blob" and t["path"].lower().endswith(".tif")]
        for c in items:
            nm = FL._norm(c["submission"])
            pat = re.compile(r"^([a-z0-9]+[-_])?" + re.escape(nm) + r"$")
            hits = [t for t in tifs if pat.match(FL._norm(t["path"]))]
            if not hits:
                errors.append(dict(site=site, submission=c["submission"], error="no matching .tif in tree"))
                continue
            for t in hits:
                if t.get("size", 0) > MAX_BYTES:
                    errors.append(dict(site=site, path=t["path"], error="blob too large"))
                    continue
                dest = OUT / f"{site}__{Path(t['path']).name}"
                if not dest.is_file():
                    part = dest.with_suffix(".partial")
                    with part.open("wb") as fh:
                        subprocess.run(["gh", "api", f"repos/{OWNER}/{site}/git/blobs/{t['sha']}",
                                        "-H", "Accept: application/vnd.github.raw"],
                                       stdout=fh, check=True, timeout=600)
                    if part.stat().st_size != t["size"]:
                        part.unlink()
                        errors.append(dict(site=site, path=t["path"], error="size mismatch"))
                        continue
                    part.replace(dest)
                rows.append(dict(site=site, submission=c["submission"], repo=f"{OWNER}/{site}", ref=ref,
                                 path=t["path"], blob=t["sha"], bytes=dest.stat().st_size,
                                 sha256=FL.sha256(dest), dest=str(dest.relative_to(ROOT))))
                print(f"ok {site} {Path(t['path']).name}", flush=True)
    RECEIPT.write_text(json.dumps(dict(
        evidence_class="DATA-MEASUREMENT (owner public repos via GitHub API; not organizer bytes)",
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        files=rows, errors=errors), indent=1) + "\n")
    print(json.dumps(dict(fetched=len(rows), errors=len(errors))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
