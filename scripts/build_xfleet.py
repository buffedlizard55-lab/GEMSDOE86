#!/usr/bin/env python3
"""Historical diagnostic script for Lane XFLEET (Cross-Fleet Consensus + R0
Anchor), now gated fail-closed behind ``scripts.protocol_preflight.require_feasible()``.

Forensic status (IR-86-SPT-02, 2026-10-24):
  - Revoked as ``verdict: "negative"`` (``DO NOT SUBMIT``).
  - Even against the 25 local scored-fleet rasters alone, XFLEET breached both
    duplicate limits (``dot_overlap_within_3px = 0.9988 > 0.70``,
    ``spearman = 0.9979 > 0.90`` vs ``GEMSDOE32`` ``R0``), and ``require_feasible()``
    stops before any surface construction or dot placement because the pinned
    continuous witness ``17GEMSDOE`` (``ab0a0a62...``) covers ``100%`` of
    allowed off-catalogue footprint cells within 3 px.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))


def greedy_poisson_disk(
    score: np.ndarray,
    allowed_mask: np.ndarray,
    budget: int,
    r_excl: float = 2.8,
) -> np.ndarray:
    h, w = score.shape
    ys, xs = np.where(allowed_mask & (score > -1e8))
    vals = score[ys, xs]
    tie = ((ys.astype(np.int64) * 1315423911) ^ (xs.astype(np.int64) * 2654435761)) & 0xFFFFFFFF
    order = np.lexsort((tie, -vals))
    ys, xs = ys[order], xs[order]
    blocked = np.zeros((h, w), dtype=bool)
    ri = int(np.ceil(r_excl))
    dy, dx = np.ogrid[-ri : ri + 1, -ri : ri + 1]
    disk = (dy * dy + dx * dx) <= (r_excl * r_excl + 1e-9)
    out = np.zeros((h, w), dtype=bool)
    chosen = 0
    for y, x in zip(ys, xs):
        if blocked[y, x]:
            continue
        out[y, x] = True
        chosen += 1
        if chosen >= budget:
            break
        y0, y1 = max(0, y - ri), min(h, y + ri + 1)
        x0, x1 = max(0, x - ri), min(w, x + ri + 1)
        blocked[y0:y1, x0:x1] |= disk[y0 - (y - ri) : y1 - (y - ri), x0 - (x - ri) : x1 - (x - ri)]
    return out


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()

    from gems57 import metric

    with rasterio.open(ROOT / "data/sample_submission.tif") as src:
        sample = src.read(1)
        foot = np.isfinite(sample)
        h, w = sample.shape
    with rasterio.open(ROOT / "data/existing_faults.tif") as src:
        cat = (src.read(1) > 0) & foot

    fleet_files = [
        p for p in sorted((ROOT / "data/scored_fleet").glob("*.tif")) if "DO-NOT-SUBMIT" not in p.name
    ]
    r0_path = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    with rasterio.open(r0_path) as s:
        r0 = np.isfinite(s.read(1)) & (s.read(1) > 0) & foot
    budget = int(r0.sum())

    votes = np.zeros((h, w), dtype=np.float32)
    r = 3
    yy, xx = np.ogrid[-r : r + 1, -r : r + 1]
    kern = np.maximum(0.0, 1.0 - np.hypot(yy, xx) / r).astype(np.float32)
    for p in fleet_files:
        with rasterio.open(p) as s:
            arr = s.read(1)
        dots = (np.isfinite(arr) & (arr > 0) & foot).astype(np.float32)
        votes += ndimage.convolve(dots, kern, mode="constant", cval=0.0)
    votes /= max(len(fleet_files), 1)
    r0_k = ndimage.convolve(r0.astype(np.float32), kern, mode="constant", cval=0.0)

    comp_lbl, n_comp = ndimage.label(cat, structure=np.ones((3, 3), int))
    cy_mid, cx_mid = h // 2, w // 2
    ys_c, xs_c = np.nonzero(cat)
    cl = comp_lbl[ys_c, xs_c]
    sum_y = np.bincount(cl, weights=ys_c, minlength=n_comp + 1)
    sum_x = np.bincount(cl, weights=xs_c, minlength=n_comp + 1)
    cnt = np.bincount(cl, minlength=n_comp + 1).clip(min=1)
    comp_fold = ((sum_y / cnt >= cy_mid).astype(int) * 2) + (sum_x / cnt >= cx_mid).astype(int)
    comp_fold[0] = -1
    fold_map = comp_fold[comp_lbl]

    surf_anchor = np.where(foot, votes + 2.0 * r0_k, -1e9)
    tot_tp = tot_fp = tot_fn = 0.0
    for fold_id in range(4):
        test_mask = (fold_map == fold_id) & cat
        buf_test = ndimage.distance_transform_edt(~test_mask) <= 10.0
        vis = cat & (~buf_test)
        dist_vis = ndimage.distance_transform_edt(~vis).astype(np.float32)
        cand = greedy_poisson_disk(surf_anchor, foot & (dist_vis > 2.0), budget, r_excl=2.8)
        res = metric.dti_binary(cand, test_mask, foot & (~vis))
        tot_tp += res["tp"]
        tot_fp += res["fp"]
        tot_fn += res["fn"]
    denom = tot_tp + 0.2 * tot_fp + 0.8 * tot_fn
    print(json.dumps({"pooled_holdout_dti": round(tot_tp / denom if denom > 0 else 0.0, 5)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
