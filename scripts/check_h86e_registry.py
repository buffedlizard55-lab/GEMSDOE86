"""Shared-template registry check (PA-86-01 like-for-like + literal, side by side).

Usage:
  python scripts/check_h86e_registry.py SURFACE_OR_DOTS.npy OUT.json [--surface]

Compares one candidate array against every hash-verified raster in the pinned
public owner inventory (research/upstream/registry_inventory.json, 655 rasters,
restored into data/registry_ext/ by sha256) plus this repository's own
published downloads and locally pinned scored-fleet rasters not in the
inventory.  Uses gems57.uniqueness.compare_array_to_registry and
two_phase_summary unchanged.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import grid  # noqa: E402
from gems57.uniqueness import compare_array_to_registry, two_phase_summary  # noqa: E402


def sha(p: Path) -> str:
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def build_index():
    inv = json.loads((ROOT / "research/upstream/registry_inventory.json").read_text())
    rasters, seen, missing = [], set(), []
    for r in inv["rasters"]:
        f = ROOT / "data/registry_ext" / f"{r['sha256']}.tif"
        if not f.exists():
            missing.append(r["sha256"])
            continue
        rasters.append(dict(r, cache_file=str(f)))
        seen.add(r["sha256"])
    extra = sorted((ROOT / "docs/downloads").glob("*.tif")) + sorted((ROOT / "data/scored_fleet").glob("*.tif"))
    for f in extra:
        d = sha(f)
        if d in seen:
            continue
        seen.add(d)
        rasters.append(dict(sha256=d, bytes=f.stat().st_size, blob=None, cache_file=str(f),
                            sources=[f"GEMSDOE86-local:{f.relative_to(ROOT)}"], repo_first="GEMSDOE86-local"))
    complete = not missing
    return dict(rasters=rasters, complete_accessible_scan=complete, errors=[]), missing


def main(argv):
    src, out = Path(argv[0]), Path(argv[1])
    surface = "--surface" in argv
    g = grid.load_grid(ROOT / "data")
    arr = np.load(src).astype(np.float32)
    if not surface:
        arr = (arr > 0).astype(np.float32)
    arr[~g.footprint] = 0
    index, missing = build_index()
    res = compare_array_to_registry(arr, index, g.footprint,
                                    expected_grid=(g.shape, g.crs, g.transform))
    phase = two_phase_summary(res["rows"], int(g.footprint.sum()),
                              expected_rasters=len(index["rasters"]))
    rows = res.pop("rows")
    top = sorted([r for r in rows if "error" not in r],
                 key=lambda r: -r["my_dots_within_3px_of_theirs"])[:15]
    top_rho = sorted([r for r in rows if r.get("spearman_full_footprint") is not None],
                     key=lambda r: -r["spearman_full_footprint"])[:15]
    keep = ("repo", "submission", "sha256", "their_dots", "my_dots_within_3px_of_theirs",
            "their_dots_within_3px_of_mine", "spearman_full_footprint", "jaccard_dot_sets")
    report = dict(
        candidate=str(src), mode="surface" if surface else "final_dots",
        inventory_rasters_missing=missing, registry_rasters_measured=len(rows),
        errors=[r for r in rows if "error" in r],
        shared_summary={k: v for k, v in res.items()},
        two_phase=phase,
        top15_by_forward_overlap=[{k: r.get(k) for k in keep} | {"representation": r.get("representation")} for r in top],
        top15_by_spearman=[{k: r.get(k) for k in keep} | {"representation": r.get("representation")} for r in top_rho],
    )
    if surface:
        # A continuous surface has no dot set; only the rank test is meaningful here.
        report["surface_gate_pass"] = bool(phase["literal_reading"]["rho_firings"] == 0)
    else:
        report["final_dots_gate_pass"] = bool(not phase["like_for_like_reading"]["duplicate"]
                                              and not res["byte_unique_among_checked"] is False)
    out.write_text(json.dumps(report, indent=2, allow_nan=False, default=str) + "\n")
    print(json.dumps({k: report[k] for k in report if k.endswith("gate_pass")}, indent=1))
    print(json.dumps(phase["like_for_like_reading"], indent=1))
    print(json.dumps(phase["literal_reading"], indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
