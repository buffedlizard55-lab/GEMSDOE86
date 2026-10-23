#!/usr/bin/env python3
"""Thin CLI wrapper delegating directly to unmodified `vendor/gems57/evaluate_holdout.py`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import evaluate_holdout as EH, grid as GRID, holdout as HO  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("prediction_tif", type=Path, help="GeoTIFF prediction on 3730x3292 grid")
    ap.add_argument("--seed", type=int, default=20, help="Holdout seed (default: 20)")
    ap.add_argument("--draws", type=int, default=1000, help="Spatial-block bootstrap draws")
    ap.add_argument("--out", type=Path, default=None, help="Optional JSON output path")
    args = ap.parse_args()

    g = GRID.load_grid(ROOT / "data" / "bridge")
    hc = HO.build_holdout(g, seeds=(args.seed,), modes=("all",))
    with rasterio.open(args.prediction_tif) as ds:
        pred = np.nan_to_num(ds.read(1).astype(np.float32), nan=0.0)
    pred = np.clip(pred, 0.0, 1.0)

    quad = HO.quadrant_ids(g.footprint)
    terms_sum = None
    per_fold = {}
    for cell in hc.cells_of("all"):
        q_region = (quad == cell.fold) & g.footprint
        vis = hc.visible(cell.key)
        hid = hc.hidden_by_cell[cell.key]
        fold_dict = {"region": q_region, "visible": vis, "masked_known": vis, "truth": hid}
        res, terms = EH.evaluate(pred, fold_dict, g.footprint)
        per_fold[HO.FOLD_NAMES[cell.fold]] = res
        terms_sum = terms if terms_sum is None else (terms_sum + terms)

    summary = EH.pooled_summary({"candidate": terms_sum}, draws=args.draws, candidate="candidate")
    out = {"pooled": summary["scores"]["candidate"], "per_fold": per_fold}
    txt = json.dumps(out, indent=2)
    print(txt)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n")


if __name__ == "__main__":
    main()
