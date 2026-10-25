#!/usr/bin/env python3
"""Fleet stratification of OWNER-REPORTED scores (descriptive, n=17; not causal)."""
from __future__ import annotations

import glob
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.optimize import nnls

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "vendor"), str(ROOT), str(ROOT / "src")]

from gems57 import grid  # noqa: E402
from gems86.io import read_band  # noqa: E402

SCORES = {
    "d2-8": 0.2708,
    "h36-1": 0.2710,
    "h38-1": 0.2707,
    "h33-h33-2-b2": 0.2778,
    "h33d": 0.2632,
    "anderson": 0.2750,
    "gate_ortho": 0.2376,
    "cvarlw": 0.2303,
    "lidar03": 0.1152,
    "mcsc": 0.1917,
    "trlt": 0.1627,
    "ptcf": 0.2343,
    "h76_3": 0.1555,
    "choquet": 0.0943,
    "cont-poisson": 0.0041,
    "punoisyor": 0.1886,
    "gvcd": 0.0573,
}
BINS = [0, 2.01, 4, 8, 16, 32, 64, 1e9]


def main() -> int:
    g = grid.load_grid(ROOT / "data")
    fp = g.footprint
    dcat = ndi.distance_transform_edt(~g.catalogue)
    slope = read_band(str(ROOT / "data/training_features.tif"), "det_elev_slope")
    elev = read_band(str(ROOT / "data/training_features.tif"), "det_elev")
    sv = slope[fp]
    t1, t2 = np.percentile(sv, [33.3, 66.7])
    print("slope terciles", t1, t2)
    rows = []
    for p in sorted(glob.glob(str(ROOT / "data/scored_fleet/*.tif"))):
        key = [k for k in SCORES if k in p]
        if len(key) != 1:
            continue
        with rasterio.open(p) as s:
            a = np.nan_to_num(s.read(1))
        d = (a > 0) & fp
        dc = dcat[d]
        sl = slope[d]
        h = np.histogram(dc, BINS)[0]
        st = np.array([(sl < t1).sum(), ((sl >= t1) & (sl < t2)).sum(), (sl >= t2).sum()])
        rows.append(
            dict(
                k=key[0],
                s=SCORES[key[0]],
                n=int(d.sum()),
                dcat=h.tolist(),
                slope=st.tolist(),
                medslope=float(np.median(sl)),
                medelev=float(np.median(elev[d])),
            )
        )
    for r in sorted(rows, key=lambda r: -r["s"]):
        n = r["n"]
        print(
            f"{r['k']:14s} {r['s']:.4f} n={n} "
            f"dcat%={np.round(100 * np.array(r['dcat']) / n, 1)} "
            f"slope%={np.round(100 * np.array(r['slope']) / n, 1)} "
            f"medslope={r['medslope']:.2f}"
        )
    (ROOT / "docs/evidence/h86e_fleet_strata.json").write_text(
        json.dumps(rows, allow_nan=False) + "\n"
    )
    for cap in (12000, 15000, 20000, 30000):
        x = np.array([r["dcat"] for r in rows], float)
        y = np.array([r["s"] * (0.2 * r["n"] + 0.8 * cap) for r in rows])
        c, res = nnls(x, y)
        print("N", cap, "credit/dot by dcat bin", np.round(c, 3), "resid", round(res, 1))
        x2 = np.array([r["slope"] for r in rows], float)
        c2, res2 = nnls(x2, y)
        print("   by slope tercile", np.round(c2, 3), "resid", round(res2, 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
