#!/usr/bin/env python3
"""Historical diagnostic script for Lane SPT (Submodular Poisson-Thinning on
Cross-Fleet Throw-Consensus), now gated fail-closed behind
``scripts.protocol_preflight.require_feasible()``.

Forensic status (IR-86-SPT-02, 2026-10-24):
  - Revoked as ``verdict: "negative"`` (``DO NOT SUBMIT``).
  - The pinned continuous witness ``17GEMSDOE`` (``ab0a0a62...``) covers all
    ``5,106,385 / 5,106,385`` off-catalogue footprint cells within 3 px, so
    ``require_feasible()`` raises ``ProtocolStopError`` before any surface
    construction or dot placement.
  - Even aside from the saturated witness, PR #60's original run had a single-
    feature canary AUC of ``0.4947`` (< 0.50 coin-flip) and masked ``dist_cat``
    using the full ``existing_faults.tif`` catalogue (including withheld test
    folds). In the fold-fair loop below, ``dist_vis`` is restricted strictly to
    fold-visible catalogue faults outside a 10-px split buffer.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))


def roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    order = np.argsort(y_score, kind="mergesort")
    y = y_true[order]
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return 0.5
    ranks = np.arange(1, len(y) + 1, dtype=np.float64)
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


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
        profile = src.profile.copy()
        sample = src.read(1)
        foot = np.isfinite(sample)
        h, w = sample.shape
    with rasterio.open(ROOT / "data/existing_faults.tif") as src:
        cat = (src.read(1) > 0) & foot

    fleet_files = sorted((ROOT / "data/scored_fleet").glob("*.tif"))
    non_pack = [
        p
        for p in fleet_files
        if not any(
            k in p.name
            for k in (
                "GEMSDOE28__",
                "GEMSDOE32__",
                "GEMSDOE33__",
                "GEMSDOE36__",
                "GEMSDOE63__",
                "DO-NOT-SUBMIT",
            )
        )
    ]

    throw_votes = np.zeros((h, w), dtype=np.float32)
    raw_dots = np.zeros((h, w), dtype=np.uint8)
    r = 3
    yy, xx = np.ogrid[-r : r + 1, -r : r + 1]
    kern = np.maximum(0.0, 1.0 - np.hypot(yy, xx) / r).astype(np.float32)
    for p in non_pack:
        with rasterio.open(p) as s:
            arr = s.read(1)
        dots = (np.isfinite(arr) & (arr > 0) & foot).astype(np.float32)
        raw_dots += dots > 0
        throw_votes += ndimage.convolve(dots, kern, mode="constant", cval=0.0)
    throw_votes /= max(len(non_pack), 1)

    gx = ndimage.sobel(throw_votes, axis=1)
    gy = ndimage.sobel(throw_votes, axis=0)
    grad = np.hypot(gx, gy)
    ridge = throw_votes - 0.35 * grad

    r0_path = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    with rasterio.open(r0_path) as s:
        r0 = np.isfinite(s.read(1)) & (s.read(1) > 0) & foot
    budget = int(r0.sum())

    dist_r0 = ndimage.distance_transform_edt(~r0).astype(np.float32)
    penalty = float(os.environ.get("SPT_PENALTY", "0.5"))
    score = (
        ridge
        + 0.15 * (raw_dots.astype(np.float32) / max(len(non_pack), 1))
        - penalty * np.exp(-((dist_r0 / 2.0) ** 2))
    )
    score[~foot] = -1e9

    rng = np.random.default_rng(86)
    pos_idx = np.flatnonzero(cat)
    neg_idx = np.flatnonzero(foot & (~cat))
    sp = rng.choice(pos_idx, size=min(25000, len(pos_idx)), replace=False)
    sn = rng.choice(neg_idx, size=min(25000, len(neg_idx)), replace=False)
    canary_auc = roc_auc(
        np.concatenate([np.ones(len(sp)), np.zeros(len(sn))]),
        np.concatenate([score.ravel()[sp], score.ravel()[sn]]),
    )

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

    fold_results: dict[str, dict] = {}
    for label, r_excl in [("E1_spt_r40", 4.0), ("E2_spt_r35", 3.5), ("E3_spt_r30", 3.0)]:
        tot_tp = tot_fp = tot_fn = 0.0
        per_fold: dict[str, float] = {}
        for fold_id, fold_name in enumerate(["NW", "NE", "SW", "SE"]):
            test_mask = (fold_map == fold_id) & cat
            buf_test = ndimage.distance_transform_edt(~test_mask) <= 10.0
            vis = cat & (~buf_test)
            dist_vis = ndimage.distance_transform_edt(~vis).astype(np.float32)
            allowed_fold = foot & (dist_vis > 2.0)
            cand_fold = greedy_poisson_disk(score, allowed_fold, budget, r_excl=r_excl)
            eval_mask = foot & (~vis)
            res = metric.dti_binary(cand_fold, test_mask, eval_mask)
            per_fold[fold_name] = round(res["dti"], 5)
            tot_tp += res["tp"]
            tot_fp += res["fp"]
            tot_fn += res["fn"]
        denom = tot_tp + 0.2 * tot_fp + 0.8 * tot_fn
        fold_results[label] = {
            "r_excl_px": r_excl,
            "pooled_holdout_dti": round(tot_tp / denom if denom > 0 else 0.0, 5),
            "per_fold": per_fold,
            "canary_auc": round(canary_auc, 4),
        }

    print(json.dumps(fold_results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
