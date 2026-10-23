#!/usr/bin/env python3
"""Literal parallel-run uniqueness gate against the published fleet inventory.

Thresholds are the shared template's (``gems57.uniqueness``): block if
Spearman > 0.90 or if more than 70 % of the candidate's dots lie within 3 px of
one prior raster's dots.  The gate fails closed: a missing prior raster makes the
inventory incomplete and the candidate is *not* certified unique.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

from gems57.grid import load_grid                     # noqa: E402
from gems57 import uniqueness                          # noqa: E402

INDEX = ROOT / "registry" / "registry_index_published_20261021.json"
TIFS = ROOT / ".cache" / "registry" / "tifs"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def build_local_index() -> dict:
    idx = json.loads(INDEX.read_text())
    rows = []
    for r in idx["rasters"]:
        p = TIFS / f"{r['blob']}.tif"
        if not p.is_file():
            raise FileNotFoundError(f"missing registry raster {r['repo']}:{r['path']}")
        rows.append(dict(repo_first=r["repo"], sources=[f"{r['repo']}:{r['path']}"],
                         cache_file=str(p), sha256=sha256_file(p)))
    return dict(rasters=rows, complete_accessible_scan=True, errors=[],
                index_sha256=sha256_file(INDEX), n_rasters=len(rows))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default=None)
    a = ap.parse_args()
    t0 = time.time()
    g = load_grid(ROOT / "data" / "bridge")
    cand = Path(a.candidate) if a.candidate else sorted(
        (ROOT / "docs" / "downloads").glob("gems86-gmc-linepost-*.tif"))[-1]
    index = build_local_index()
    print(f"registry: {index['n_rasters']} rasters, index sha256 {index['index_sha256'][:16]}",
          flush=True)
    result = uniqueness.compare_to_registry(cand, index, g.footprint)
    result["candidate"] = cand.name
    result["candidate_sha256"] = sha256_file(cand)
    result["inventory_index_sha256"] = index["index_sha256"]
    result["inventory_n_rasters"] = index["n_rasters"]
    result["scope"] = ("all 812 unique blobs in the published cross-fleet inventory of "
                       "2026-10-21T02:30Z (68 owner repositories); this is not an organizer "
                       "registry, so unindexed or later files are outside the audit")
    result["elapsed_s"] = round(time.time() - t0, 1)
    out = ROOT / "evidence" / "uniqueness_audit.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("my_dots", "unique", "complete_accessible_scan",
                                              "worst_rho", "worst_overlap", "blocked_by")},
                     indent=2, default=str))


if __name__ == "__main__":
    main()
