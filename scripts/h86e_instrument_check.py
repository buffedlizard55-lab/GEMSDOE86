"""Instrument-validity check: score pinned fleet rasters on the buffered LOQO split as-is."""
from __future__ import annotations

import glob
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    import numpy as np
    import rasterio
    from scipy import ndimage as ndi
    from scipy.stats import spearmanr

    sys.path[:0] = [str(ROOT / "vendor"), str(ROOT), str(ROOT / "src")]
    from gems57 import evaluate_holdout as E, grid, holdout as H

    t = time.time()
    g = grid.load_grid(ROOT / "data")
    fp = g.footprint
    folds, _ = H.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3)
    print("withheld", int(folds[0]["hidden_all"].sum()), [f["receipt"]["withheld_positive_pixels"] for f in folds], time.time() - t)
    vis = folds[0]["visible"]
    dvis = ndi.distance_transform_edt(~vis)
    scores = {
        "d2-8": 0.2708, "h36-1": 0.2710, "h38-1": 0.2707, "h33-h33-2-b2": 0.2778,
        "h33d": 0.2632, "anderson": 0.2750, "gate_ortho": 0.2376, "cvarlw": 0.2303,
        "lidar03": 0.1152, "mcsc": 0.1917, "trlt": 0.1627, "ptcf": 0.2343,
        "h76_3": 0.1555, "choquet": 0.0943, "cont-poisson": 0.0041,
        "punoisyor": 0.1886, "gvcd": 0.0573,
    }

    def pooled(dots):
        terms = []
        for f in folds:
            _, tm = E.evaluate(dots.astype(np.float32), f, fp)
            terms.append(tm)
        tot = np.sum(terms, axis=0).sum(axis=0)
        return float(E.from_terms(tot)), np.sum(terms, axis=0)

    out = []
    for p in sorted(glob.glob(str(ROOT / "data/scored_fleet/*.tif"))):
        key = [k for k in scores if k in p]
        with rasterio.open(p) as s:
            a = np.nan_to_num(s.read(1))
        d = (a > 0) & fp
        raw, _ = pooled(d)
        fair, _ = pooled(d & (dvis > 2.0))
        out.append(
            dict(
                file=p.split("/")[-1],
                lb=scores[key[0]] if len(key) == 1 else None,
                holdout_raw=raw,
                holdout_visible_collar=fair,
                n=int(d.sum()),
            )
        )
        print(f"{p.split('/')[-1][:60]:60s} lb={out[-1]['lb']} raw={raw:.4f} n={d.sum()}", flush=True)
    xs = [(o["lb"], o["holdout_raw"]) for o in out if o["lb"] is not None]
    print("spearman LB vs buffered-LOQO holdout:", spearmanr([a for a, _ in xs], [b for _, b in xs]))
    (ROOT / "docs/evidence/h86e_instrument_check.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
