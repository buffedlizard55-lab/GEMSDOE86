#!/usr/bin/env python3
"""Measured audit of the highest-scoring file on each of the nine requested GEMSDOE sites.

Inputs are the exact owner-published GeoTIFFs (downloaded from each owner's public GitHub
repository archive via codeload.github.com, or the byte-identical local copy in
``data/scored_fleet``). Every number below is measured from the bytes; the owner scores are
transcribed from ``registry/prior_scores.csv`` and are OWNER-REPORTED, never verified.

Usage:
  python scripts/nine_site_audit.py --fleet /tmp/fleet/extract --out docs/evidence/nine-site-audit-20261027.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
from gems57 import uniqueness as U  # noqa: E402


def _finite(o):
    """Replace NaN/Inf with null so the JSON is strict (the repo loader rejects non-finite tokens)."""
    if isinstance(o, float) and not math.isfinite(o):
        return None
    if isinstance(o, dict):
        return {k: _finite(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_finite(v) for v in o]
    return o

EXPECTED_SHAPE = (3730, 3292)
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)

# (site, owner-reported name, owner-reported score, path relative to --fleet or ROOT, provenance)
BEST = [
    ("GEMSDOE32", "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros", 0.2778,
     "GEMSDOE32-main/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", "codeload"),
    ("GEMSDOE36", "anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros", 0.2750,
     "GEMSDOE36-main/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", "codeload"),
    ("GEMSDOE28", "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan", 0.2710,
     "GEMSDOE28-main/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif", "codeload"),
    ("GEMSDOE31", "h27-4-solo-d28-20261004-8acb75e1-nan", 0.2708,
     "GEMSDOE31-main/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif", "codeload"),
    ("GEMSDOE33", "h33d-analog-tip-stepover-r30-20261004-cb490425926e", 0.2632,
     "GEMSDOE33-main/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif", "codeload"),
    ("GEMSDOE25", "dotted-h19-5-d2-8-20261002-e56ea318af89-nan", 0.2600,
     "GEMSDOE25-main/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif", "codeload"),
    ("GEMSDOE30", "d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca", 0.2600,
     "GEMSDOE30-main/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif", "codeload"),
    ("GEMSDOE27", "topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan", 0.2449,
     "GEMSDOE27-main/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif", "codeload"),
    ("GEMSDOE24", "h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan", 0.2477,
     "GEMSDOE24-main/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif", "codeload"),
]
# NaN-outside twins, measured for the format comparison only
TWINS = [
    ("GEMSDOE32", "GEMSDOE32-main/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-nan.tif"),
    ("GEMSDOE36", "GEMSDOE36-main/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-nan.tif"),
    ("GEMSDOE28", "GEMSDOE28-main/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"),
    ("GEMSDOE31", "GEMSDOE31-main/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif"),
    ("GEMSDOE33", "GEMSDOE33-main/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif"),
    ("GEMSDOE25", "GEMSDOE25-main/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"),
    ("GEMSDOE30", "GEMSDOE30-main/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif"),
    ("GEMSDOE27", "GEMSDOE27-main/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif"),
    ("GEMSDOE24", "GEMSDOE24-main/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif"),
]
BRIDGE = ROOT / "data/bridge"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def footprint_and_catalogue() -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(BRIDGE / "sample_submission.tif") as s:
        fp = np.isfinite(s.read(1))
    with rasterio.open(BRIDGE / "existing_faults.tif") as s:
        cat = s.read(1)
    return fp, (cat == 1) & fp


def format_receipt(path: Path, fp: np.ndarray, cat: np.ndarray) -> tuple[dict, np.ndarray]:
    with rasterio.open(path) as ds:
        a = ds.read(1)
        meta = dict(crs_epsg=ds.crs.to_epsg() if ds.crs else None, shape=list(ds.shape),
                    transform_matches=tuple(float(v) for v in ds.transform)[:6] == EXPECTED_TRANSFORM,
                    dtype=ds.dtypes[0], count=ds.count, nodata=ds.nodata)
    nan = np.isnan(a)
    finite = np.isfinite(a)
    fv = a[finite]
    dots = finite & (a > 0)
    rec = dict(
        sha256=sha256(path), bytes=path.stat().st_size, **meta,
        shape_matches=meta["shape"] == list(EXPECTED_SHAPE),
        nan_total=int(nan.sum()), nan_inside_footprint=int((nan & fp).sum()),
        nan_outside_footprint=int((nan & ~fp).sum()),
        inf_total=int(np.isinf(a).sum()),
        finite_min=float(fv.min()) if fv.size else None, finite_max=float(fv.max()) if fv.size else None,
        finite_values_in_0_1=bool(fv.size and fv.min() >= 0.0 and fv.max() <= 1.0),
        distinct_finite_values=[float(v) for v in np.unique(fv)[:8]],
        nonzero_outside_footprint=int((finite & (a != 0) & ~fp).sum()),
        dots_inside_footprint=int((dots & fp).sum()), dots_outside_footprint=int((dots & ~fp).sum()),
        dots_on_catalogue=int((dots & cat).sum()),
        form=("NaN outside footprint (organizer-example style)" if nan.any() else
              "all-finite, zeros outside footprint (portal-safe form)"),
    )
    rec["in_range_gate_all_pixels"] = bool(rec["nan_total"] == 0 and rec["inf_total"] == 0
                                           and rec["finite_values_in_0_1"])
    return rec, dots & fp


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fleet", default="/tmp/fleet/extract")
    ap.add_argument("--out", default="docs/evidence/nine-site-audit-20261027.json")
    args = ap.parse_args()
    fleet = Path(args.fleet)
    fp, cat = footprint_and_catalogue()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")

    rows, dotsets = [], {}
    for site, name, score, rel, prov in BEST:
        path = fleet / rel
        rec, dots = format_receipt(path, fp, cat)
        rec.update(site=site, owner_name=name, owner_score=score, owner_score_class="OWNER-REPORTED (no organizer receipt)",
                   file=rel, provenance=prov)
        rows.append(rec)
        dotsets[site] = dots
        if site == "GEMSDOE32":
            # byte-identity with the repo-local copy used by earlier lanes
            local = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
            rec["identical_to_repo_local_copy"] = sha256(local) == rec["sha256"]

    twins = []
    for site, rel in TWINS:
        path = fleet / rel
        rec, dots = format_receipt(path, fp, cat)
        best = next(r for r in rows if r["site"] == site)
        dots_match = int(np.count_nonzero(dots ^ dotsets[site]))
        twins.append(dict(site=site, file=rel, sha256=rec["sha256"], form=rec["form"],
                          nan_total=rec["nan_total"], dots_inside_footprint=rec["dots_inside_footprint"],
                          symmetric_difference_vs_best_dots=dots_match,
                          best_dots=best["dots_inside_footprint"]))

    pair = {}
    sites = [r["site"] for r in rows]
    for a in sites:
        for b in sites:
            if a == b:
                continue
            pair[f"{a}->{b}"] = U.dot_overlap(dotsets[a], dotsets[b])
    best_pairs = sorted(((v, k) for k, v in pair.items()), reverse=True)
    mx = {}
    for a in sites:
        mx[a] = max((v, k) for k, v in pair.items() if k.startswith(a + "->"))
    result = dict(
        schema="gems86.nine-site-audit.v1",
        session="fb68389e",
        started_utc=started,
        finished_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        evidence_class="MEASURED-FILE-AUDIT (format + overlap); owner scores are OWNER-REPORTED",
        footprint_cells=int(fp.sum()), catalogue_cells=int(cat.sum()),
        files=rows, nan_twins=twins,
        overlap_rule="dot_overlap(A,B) = fraction of A's dots within 3 px of any B dot (gems57.uniqueness)",
        pairwise_overlap=pair,
        max_overlap_by_site={a: dict(value=mx[a][0], vs=mx[a][1].split("->")[1]) for a in sites},
        threshold_overlap=0.70,
        pairs_over_threshold=[k for k, v in pair.items() if v > 0.70],
        top_pairs=[dict(pair=k, overlap=v) for v, k in best_pairs[:12]],
        notes=[
            "Overlap is directional; the lane rule uses the larger direction.",
            "No holdout result is included here; see research/H87 pre-registration and run cards.",
        ],
    )
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_finite(result), indent=2, sort_keys=True, allow_nan=False) + "\n")
    for r in rows:
        print(f"{r['site']:10s} {r['owner_score']:.4f}  dots={r['dots_inside_footprint']:6d}  nan_total={r['nan_total']:8d}  "
              f"in_range_all={r['in_range_gate_all_pixels']}  sha={r['sha256'][:12]}")
    print("pairs over 0.70:", len(result["pairs_over_threshold"]), "of", len(pair))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
