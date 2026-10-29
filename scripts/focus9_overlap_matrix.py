"""Measure 3-px forward overlap between the nine Focus-9 immutable files.

Reads docs/evidence/focus9-immutable-files-20261029.json, fetches each file by
git blob SHA from api.github.com (allowlisted), verifies SHA-256 and byte size
against the receipt, then computes pairwise forward overlap:
  fwd(A->B) = fraction of A's dots lying within 3 px (Euclidean) of some B dot.
A dot is a finite pixel with value > 0 (the repo's literal support rule).
Output: docs/evidence/session-ff849f98-nine-site-overlap.json
This is a REGISTRY-MEASUREMENT of historical owner files. It is not an
organizer receipt, a holdout score, or upload authorisation.
"""
import hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs/evidence/focus9-immutable-files-20261029.json"
OUT = ROOT / "docs/evidence/session-ff849f98-nine-site-overlap.json"
CACHE = ROOT / ".cache/focus9"


def fetch(row):
    dest = CACHE / (row["site"] + ".tif")
    if not dest.is_file():
        url = f"https://api.github.com/repos/{row['repository']}/git/blobs/{row['git_blob_sha1']}"
        subprocess.run(["curl", "-sSfL", "-H", "Accept: application/vnd.github.raw", url, "-o", str(dest)], check=True)
    data = dest.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    ok = sha == row["sha256"] and len(data) == int(row["bytes"])
    return dest, sha, len(data), ok


def dots(path):
    with rasterio.open(path) as s:
        a = s.read(1)
        crs, shape, tr = str(s.crs), s.shape, list(s.transform)[:6]
    return (np.isfinite(a) & (a > 0)), {"crs": crs, "shape": list(shape), "transform": tr}


def main():
    rec = json.loads(RECEIPT.read_text())
    CACHE.mkdir(parents=True, exist_ok=True)
    masks, meta = {}, {}
    for row in rec["files"]:
        dest, sha, n, ok = fetch(row)
        if not ok:
            print(f"HASH MISMATCH {row['site']}: {sha} {n}", file=sys.stderr)
            sys.exit(2)
        m, info = dots(dest)
        masks[row["site"]] = m
        meta[row["site"]] = {"sha256_verified": True, "bytes": n, "dots": int(m.sum()), **info}
    sites = list(masks)
    # Distance transforms per site: distance from each pixel to nearest dot.
    dist = {s: distance_transform_edt(~masks[s]) for s in sites}
    matrix = {}
    for a in sites:
        for b in sites:
            if a == b:
                continue
            matrix.setdefault(a, {})[b] = round(float((dist[b][masks[a]] <= 3).mean()), 4)
    worst = {a: max(matrix[a].values()) for a in sites}
    out = {
        "schema": "gems86.session-ff849f98.nine-site-overlap.v1",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "REGISTRY-MEASUREMENT",
        "source_receipt": "docs/evidence/focus9-immutable-files-20261029.json",
        "metric": "forward 3-px overlap: fraction of row-site dots within 3 px of any column-site dot",
        "gate": 0.70,
        "sites": meta,
        "forward_overlap": matrix,
        "max_forward_overlap_vs_peers": worst,
        "unique_under_0p70_gate": {a: worst[a] <= 0.70 for a in sites},
        "scope": "Nine historical owner files only. Not all 92 repositories; not organizer receipts; not upload authorisation.",
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"max_forward_overlap_vs_peers": worst, "dots": {s: meta[s]["dots"] for s in sites}}, indent=2))


if __name__ == "__main__":
    main()
