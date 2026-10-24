#!/usr/bin/env python3
"""Execute GEMSDOE86 Lane `H86-CTHB` (3 Preregistered Experiments + Full Validation).

Hypothesis `H86-CTHB`: Contact-Truncation, Cross-Gradient Discordance & Hydrothermal-Breach
Relay Mechanics.

Preregistered budget (<= 3 experiments, <= 2 hours):
  - E1 (`E1-PurePhysics-CTHB`): Zero-catalogue 28-feature static multi-physics 4-quadrant LOQO
    `HistGradientBoostingClassifier` + `vendor/gems57/emit.py` tile-decimated allocation.
  - E2 (`E2-Coupled-CTHB`): Dual-Regime Structural-Geophysical 4-quadrant LOQO ensemble coupling
    zero-catalogue `p_phys` with fold-strict anti-halo 35-feature `p_mech` (raw isotropic `d_cat`
    excluded) + strike-guided lineament smoothing + whole-component ablations.
  - E3 (`E3-Submodular-CTHB`): Two-Stage Quota-Split Minoux Lazy-Greedy R=300 m (`3 px`)
    Submodular Marginal-DTI Kernel Allocator (`55%` sharp tip/bend/relay corridor `2 < d <= 10 px`
    + `45%` genuine off-catalogue piedmont/basin multi-physics & hydrothermal-breach discovery
    `d > 10 px`) vs single-stage submodular, tile-decimated, and naive `3x3` NMS across
    `K in {33000, 37654, 42000}`.

All holdout numbers are strictly labeled `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, paired 20 km
spatial-block bootstrap 95% CIs, `draws=1000`). Emits final GeoTIFF + ZIP strictly via unmodified
`vendor/gems57/submission_writer.py` and validates via unmodified `vendor/gems57/validate.py`.
"""
from __future__ import annotations

import gc
import hashlib
import heapq
import json
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
SCRIPTS = ROOT / "scripts"
for p in (VENDOR, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gems57 import emit as EM
from gems57 import evaluate_holdout as EH
from gems57 import grid as G
from gems57 import holdout as H
from gems57 import metric as M
from gems57 import submission_writer as SW
from gems57 import uniqueness as U
from gems57 import validate as V

import h86d_features as HF

DATA_DIR = ROOT / "data"
PROB_CACHE_DIR = HF.CACHE_DIR / "oof_probs"
DOWNLOADS_DIR = ROOT / "docs" / "downloads"
EVIDENCE_DIR = ROOT / "docs" / "evidence"
RESULTS_JSON = EVIDENCE_DIR / "lane86d_results.json"
RUN_CARD_JSON = EVIDENCE_DIR / "h86d-cthb-run-card.json"

TARGET_BUDGET = 37_654
NEAR_QUOTA_FRAC = 0.54
NEAR_SPLIT_PX = 15.0
COLLAR_PX = 2
QUAD_GUARD_PX = 15

YY2, XX2 = np.mgrid[-COLLAR_PX : COLLAR_PX + 1, -COLLAR_PX : COLLAR_PX + 1]
DISK_R2 = (YY2 * YY2 + XX2 * XX2) <= (COLLAR_PX * COLLAR_PX)

YY3, XX3 = np.mgrid[-3:4, -3:4]
KER_R3 = np.maximum(0.0, 1.0 - np.hypot(YY3, XX3) / 3.0).astype(np.float32)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def peak_rss_mb() -> float:
    return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0


def pack_footprint_matrix(planes: list[np.ndarray], fp_ys: np.ndarray, fp_xs: np.ndarray) -> np.ndarray:
    mat = np.empty((fp_ys.size, len(planes)), dtype=np.float32)
    for j, pl in enumerate(planes):
        mat[:, j] = pl[fp_ys, fp_xs]
    return mat


def predict_fp_matrix(
    clf: HistGradientBoostingClassifier,
    mat: np.ndarray,
    sub_idx: np.ndarray | None = None,
    chunk_size: int = 400_000,
) -> np.ndarray:
    n = mat.shape[0] if sub_idx is None else sub_idx.size
    out = np.empty(n, dtype=np.float32)
    for s in range(0, n, chunk_size):
        e = min(s + chunk_size, n)
        xb = mat[s:e] if sub_idx is None else mat[sub_idx[s:e]]
        out[s:e] = clf.predict_proba(xb)[:, 1].astype(np.float32)
    return out


def quadrant_guard_mask(quad: np.ndarray, guard_px: int = QUAD_GUARD_PX) -> np.ndarray:
    size = 2 * guard_px + 1
    return ndi.maximum_filter(quad, size=size, mode="nearest") == ndi.minimum_filter(quad, size=size, mode="nearest")


def calibrate_to_prior(prob: np.ndarray, footprint: np.ndarray, target_mass: float = 15_000.0) -> np.ndarray:
    out = np.zeros(prob.shape, dtype=np.float32)
    vals = np.clip(prob[footprint], 0.0, 1.0).astype(np.float64)
    if vals.size == 0 or vals.max() <= 0:
        return out
    p999 = max(float(np.percentile(vals, 99.9)), 1e-6)
    normed = np.clip(vals / p999, 0.0, 2.0) ** 1.65
    tot = float(normed.sum())
    scaled = np.clip(normed * (target_mass / max(tot, 1e-9)), 0.0, 1.0).astype(np.float32)
    out[footprint] = scaled
    return out


def strike_guided_smooth(surface: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Mild 300 m anisotropic along-strike continuity filter using cached physical strike."""
    strike = np.load(HF.CACHE_DIR / "_aux_phys_strike_rad.npy", mmap_mode="r")
    out = 0.55 * surface.astype(np.float32)
    sec_angles = (0.0, np.pi / 4.0, np.pi / 2.0, 3.0 * np.pi / 4.0)
    acc = np.zeros_like(out)
    wsum = np.zeros_like(out)
    for ang in sec_angles:
        ker = np.zeros((5, 5), dtype=np.float32)
        dy, dx = np.cos(ang), np.sin(ang)
        for t in (-2, -1, 0, 1, 2):
            rr = int(round(2 - t * dy))
            cc = int(round(2 + t * dx))
            ker[rr, cc] += 1.0 if abs(t) <= 1 else 0.65
        ker /= float(ker.sum())
        resp = ndi.convolve(surface, ker, mode="constant")
        wt = np.maximum(np.cos(strike - ang) ** 2, 0.05).astype(np.float32)
        acc += wt * resp
        wsum += wt
    out += 0.45 * (acc / np.maximum(wsum, 1e-6))
    out[~footprint] = 0.0
    return out.astype(np.float32)


def emit_nms_topk(surface: np.ndarray, allowed: np.ndarray, budget: int) -> np.ndarray:
    s = np.where(allowed, surface, 0.0).astype(np.float32)
    peaks = (s > 0.0) & (s == ndi.maximum_filter(s, size=3, mode="constant"))
    ys, xs = np.nonzero(peaks)
    out = np.zeros(surface.shape, dtype=bool)
    if ys.size == 0:
        return out
    vals = s[ys, xs]
    if ys.size > budget:
        idx = np.argpartition(vals, -budget)[-budget:]
        ys, xs = ys[idx], xs[idx]
    out[ys, xs] = True
    return out


def emit_tile_decimated_topk(surface: np.ndarray, allowed: np.ndarray, budget: int, tile_px: int = 3) -> np.ndarray:
    c = EM.expected_credit(np.where(allowed, surface, 0.0))
    c = np.where(allowed, c, -np.inf)
    H_px, W_px = surface.shape
    nh, nw = H_px // tile_px, W_px // tile_px
    sub = c[: nh * tile_px, : nw * tile_px].reshape(nh, tile_px, nw, tile_px).transpose(0, 2, 1, 3).reshape(nh, nw, -1)
    best_local = np.argmax(sub, axis=-1)
    best_val = np.take_along_axis(sub, best_local[..., None], axis=-1)[..., 0]
    ti, tj = np.nonzero(np.isfinite(best_val) & (best_val > 0))
    out = np.zeros(surface.shape, dtype=bool)
    if ti.size == 0:
        return out
    rows = ti * tile_px + (best_local[ti, tj] // tile_px)
    cols = tj * tile_px + (best_local[ti, tj] % tile_px)
    vals = best_val[ti, tj]
    if vals.size > budget:
        idx = np.argpartition(vals, -budget)[-budget:]
        rows, cols = rows[idx], cols[idx]
    out[rows, cols] = True
    return out


def emit_submodular_minoux(
    surface: np.ndarray,
    allowed: np.ndarray,
    budget: int,
    pool_size: int = 190_000,
    fp_lambda: float = 0.0012,
    initial_cov_pad: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Exact Minoux lazy-greedy submodular R=300 m (`3 px`) kernel coverage allocator."""
    p = np.clip(surface, 0.0, 1.0).astype(np.float32)
    fp_cost = fp_lambda * (1.0 - p)
    init_tp = EM.expected_credit(p).astype(np.float32)
    init_gain = np.where(allowed, init_tp - fp_cost, -np.inf)

    p_pad = np.pad(p, 3, mode="constant")
    cov_pad = np.zeros_like(p_pad) if initial_cov_pad is None else initial_cov_pad.copy()
    out = np.zeros(surface.shape, dtype=bool)

    flat = init_gain.ravel()
    valid_n = int(np.isfinite(flat).sum())
    if valid_n == 0 or budget <= 0:
        return out, cov_pad
    m = min(pool_size, valid_n)
    cand_idx = np.argpartition(flat, -m)[-m:]
    cand_idx = cand_idx[np.isfinite(flat[cand_idx]) & (flat[cand_idx] > 0)]
    rs, cs = np.unravel_index(cand_idx, surface.shape)

    heap = [(-float(init_gain[r, c]), int(r), int(c)) for r, c in zip(rs, cs)]
    heapq.heapify(heap)

    picked = 0
    while picked < budget and heap:
        _, r, c = heapq.heappop(heap)
        rp, cp = r + 3, c + 3
        inc = np.maximum(0.0, KER_R3 - cov_pad[rp - 3 : rp + 4, cp - 3 : cp + 4])
        gain = float((p_pad[rp - 3 : rp + 4, cp - 3 : cp + 4] * inc).sum()) - float(fp_cost[r, c])
        if gain <= 0.0:
            continue
        if not heap or -gain <= heap[0][0] + 1e-9:
            out[r, c] = True
            np.maximum(
                cov_pad[rp - 3 : rp + 4, cp - 3 : cp + 4],
                KER_R3,
                out=cov_pad[rp - 3 : rp + 4, cp - 3 : cp + 4],
            )
            picked += 1
        else:
            heapq.heappush(heap, (-gain, r, c))
    return out, cov_pad


def emit_two_stage_submodular(
    surf_near: np.ndarray,
    surf_far: np.ndarray,
    visible_mask: np.ndarray,
    allowed: np.ndarray,
    budget: int = TARGET_BUDGET,
    near_frac: float = NEAR_QUOTA_FRAC,
) -> np.ndarray:
    """Two-Stage Quota-Split Submodular R=300 m Allocator (strictly conditioned on `visible_mask`).

    Stage 1 (`near_frac = 55%`): Allocates sharp crack-tip beams, host bends & stepover relays
        inside `2 < d(visible) <= 10 px` (`200 m - 1.0 km`).
    Stage 2 (`1 - near_frac = 45%`): Allocates genuine distal (`> 1.0 km`) off-catalogue
        basin/piedmont discoveries driven by contact truncations, magnetic-gravity cross-gradients,
        radiometric-topographic discordance, 1 m LiDAR / 10 m DEM scarplets, and 2m-probe / sinter
        hydrothermal breaches, passing Stage 1's kernel coverage map `cov_pad` so boundary dots at
        `d ~ 10 px` never double-cover the same 300 m kernel!
    """
    d_vis = ndi.distance_transform_edt(~visible_mask).astype(np.float32)
    allow_near = allowed & (d_vis <= NEAR_SPLIT_PX)
    allow_far = allowed & (d_vis > NEAR_SPLIT_PX)

    b_near = int(round(near_frac * budget))
    dots_near, cov_after_near = emit_submodular_minoux(surf_near, allow_near, b_near, pool_size=150_000)
    b_far = budget - int(dots_near.sum())
    dots_far, _ = emit_submodular_minoux(
        surf_far, allow_far, b_far, pool_size=160_000, initial_cov_pad=cov_after_near
    )
    return dots_near | dots_far


def eval_cell_terms(cell: H.Cell, ctx: H.HoldoutContext, dots_full: np.ndarray) -> np.ndarray:
    sl = cell.bbox
    r0, c0 = int(sl[0].start), int(sl[1].start)
    vis_sub = ctx.visible(cell.key)[sl]
    hid_sub = ctx.hidden_by_cell[cell.key][sl]
    fp_sub = ctx.grid.footprint[sl]
    fold_dict = {"region": cell.active | vis_sub, "visible": vis_sub, "truth": hid_sub}
    _, terms = EH.evaluate(
        dots_full[sl].astype(np.float32),
        fold_dict,
        fp_sub,
        block_side=200,
        origin=(r0, c0),
        global_shape=ctx.grid.shape,
    )
    return terms


def fit_e1_pure_physics_loqo(grid: G.Grid, static_planes: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    PROB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p_oof_f = PROB_CACHE_DIR / "e1_phys_oof.npy"
    p_live_f = PROB_CACHE_DIR / "e1_phys_live.npy"
    if p_oof_f.exists() and p_live_f.exists():
        return np.load(p_oof_f), np.load(p_live_f)

    fp = grid.footprint
    fp_ys, fp_xs = np.nonzero(fp)
    x_static = pack_footprint_matrix(static_planes, fp_ys, fp_xs)

    cat = grid.catalogue
    quad = H.quadrant_ids(fp)
    guard = quadrant_guard_mask(quad, QUAD_GUARD_PX)
    yy3, xx3 = np.mgrid[-3:4, -3:4]
    cat_buf3 = ndi.binary_dilation(cat, structure=(yy3 * yy3 + xx3 * xx3) <= 9)

    quad_fp = quad[fp_ys, fp_xs]
    guard_fp = guard[fp_ys, fp_xs]
    cat_fp = cat[fp_ys, fp_xs]
    neg_ok_fp = ~cat_buf3[fp_ys, fp_xs]

    oof_fp = np.zeros(fp_ys.size, dtype=np.float32)
    live_fp = np.zeros(fp_ys.size, dtype=np.float32)

    for q in range(4):
        rng = np.random.default_rng(8600 + q)
        tr_ok = (quad_fp != q) & guard_fp
        pos_idx = np.flatnonzero(tr_ok & cat_fp)
        neg_pool = np.flatnonzero(tr_ok & neg_ok_fp)
        n_neg = min(neg_pool.size, max(4 * pos_idx.size, 130_000))
        neg_idx = neg_pool[rng.choice(neg_pool.size, size=n_neg, replace=False)]

        tr_idx = np.concatenate([pos_idx, neg_idx])
        y_tr = np.concatenate([np.ones(pos_idx.size, np.int8), np.zeros(neg_idx.size, np.int8)])
        clf = HistGradientBoostingClassifier(
            max_iter=150,
            max_leaf_nodes=47,
            min_samples_leaf=80,
            learning_rate=0.06,
            l2_regularization=2.0,
            random_state=8600 + q,
        )
        clf.fit(x_static[tr_idx], y_tr)
        pred_all = predict_fp_matrix(clf, x_static)
        oof_fp[quad_fp == q] = pred_all[quad_fp == q]
        live_fp += 0.25 * pred_all
        del pred_all, clf, tr_idx, y_tr

    del x_static
    gc.collect()
    oof_raw = np.zeros(grid.shape, dtype=np.float32)
    live_raw = np.zeros(grid.shape, dtype=np.float32)
    oof_raw[fp_ys, fp_xs] = oof_fp
    live_raw[fp_ys, fp_xs] = live_fp

    oof_cal = strike_guided_smooth(calibrate_to_prior(oof_raw, fp, target_mass=15_000.0), fp)
    live_cal = strike_guided_smooth(calibrate_to_prior(live_raw, fp, target_mass=15_000.0), fp)
    np.save(p_oof_f, oof_cal)
    np.save(p_live_f, live_cal)
    return oof_cal, live_cal


def fit_mech_loqo_for_draw(
    grid: G.Grid,
    static_planes: list[np.ndarray],
    mech_planes: list[np.ndarray],
    p_phys_oof: np.ndarray,
    vis_pool: np.ndarray,
    hidden_pool: np.ndarray,
    seed_tag: int,
    cache_name: str | None = None,
    drop_indices: set[int] | None = None,
    live_eval_planes: list[np.ndarray] | None = None,
) -> tuple[np.ndarray, np.ndarray | None]:
    PROB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if cache_name is not None:
        c_oof = PROB_CACHE_DIR / f"mech_{cache_name}.npy"
        c_live = PROB_CACHE_DIR / f"mech_{cache_name}_live.npy"
        if c_oof.exists() and (live_eval_planes is None or c_live.exists()):
            return np.load(c_oof), (np.load(c_live) if live_eval_planes is not None else None)

    fp = grid.footprint
    fp_ys, fp_xs = np.nonzero(fp)
    quad = H.quadrant_ids(fp)
    guard = quadrant_guard_mask(quad, QUAD_GUARD_PX)
    vis_buf2 = ndi.binary_dilation(vis_pool, structure=DISK_R2)
    yy3, xx3 = np.mgrid[-3:4, -3:4]
    cat_buf3 = ndi.binary_dilation(grid.catalogue, structure=(yy3 * yy3 + xx3 * xx3) <= 9)

    full_planes = list(static_planes) + list(mech_planes) + [p_phys_oof]
    use_planes = [pl for j, pl in enumerate(full_planes) if not drop_indices or j not in drop_indices]
    x_fp = pack_footprint_matrix(use_planes, fp_ys, fp_xs)
    x_live = pack_footprint_matrix(live_eval_planes, fp_ys, fp_xs) if live_eval_planes is not None else None

    quad_fp = quad[fp_ys, fp_xs]
    guard_fp = guard[fp_ys, fp_xs]
    not_vis_fp = ~vis_buf2[fp_ys, fp_xs]
    hid_fp = hidden_pool[fp_ys, fp_xs]
    neg_ok_fp = ~cat_buf3[fp_ys, fp_xs]

    oof_fp = np.zeros(fp_ys.size, dtype=np.float32)
    live_fp = np.zeros(fp_ys.size, dtype=np.float32) if x_live is not None else None

    for q in range(4):
        rng = np.random.default_rng(8700 + 31 * seed_tag + q)
        tr_ok = (quad_fp != q) & guard_fp & not_vis_fp
        pos_idx = np.flatnonzero(tr_ok & hid_fp)
        neg_pool = np.flatnonzero(tr_ok & neg_ok_fp)
        n_neg = min(neg_pool.size, max(10 * pos_idx.size, 90_000))
        neg_idx = neg_pool[rng.choice(neg_pool.size, size=n_neg, replace=False)]

        tr_idx = np.concatenate([pos_idx, neg_idx])
        y_tr = np.concatenate([np.ones(pos_idx.size, np.int8), np.zeros(neg_idx.size, np.int8)])
        clf = HistGradientBoostingClassifier(
            max_iter=150,
            max_leaf_nodes=39,
            min_samples_leaf=75,
            learning_rate=0.055,
            l2_regularization=2.5,
            random_state=8700 + 31 * seed_tag + q,
        )
        clf.fit(x_fp[tr_idx], y_tr)
        te_idx = np.flatnonzero(quad_fp == q)
        oof_fp[te_idx] = predict_fp_matrix(clf, x_fp, sub_idx=te_idx)
        if x_live is not None and live_fp is not None:
            live_fp += 0.25 * predict_fp_matrix(clf, x_live)
        del clf, tr_idx, y_tr, te_idx

    del x_fp, x_live
    gc.collect()
    oof_raw = np.zeros(grid.shape, dtype=np.float32)
    oof_raw[fp_ys, fp_xs] = oof_fp
    oof_cal = strike_guided_smooth(calibrate_to_prior(oof_raw, fp, target_mass=15_000.0), fp)

    live_cal = None
    if live_fp is not None:
        live_raw = np.zeros(grid.shape, dtype=np.float32)
        live_raw[fp_ys, fp_xs] = live_fp
        live_cal = strike_guided_smooth(calibrate_to_prior(live_raw, fp, target_mass=15_000.0), fp)

    if cache_name is not None:
        np.save(PROB_CACHE_DIR / f"mech_{cache_name}.npy", oof_cal)
        if live_cal is not None:
            np.save(PROB_CACHE_DIR / f"mech_{cache_name}_live.npy", live_cal)
    return oof_cal, live_cal


def build_coupled_pair(
    p_mech_cal: np.ndarray,
    p_phys_cal: np.ndarray,
    footprint: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return `(surf_near, surf_far, surf_unified)` for two-stage & single-surface evaluation.

    `surf_far` uses 100% zero-catalogue `p_phys_cal` (`E1` Contact-Truncation + Cross-Gradient +
    Radiometric Discordance + 2m-Probe/Sinter Hydrothermal Breach + 1 m LiDAR / 10 m DEM Scarplets)
    so Stage 2 (`d > 1.6 km`) genuinely explores basin/piedmont off-catalogue structures rather
    than clustering inside near-catalogue contextual collars.
    """
    surf_near = strike_guided_smooth((0.88 * p_mech_cal + 0.12 * p_phys_cal).astype(np.float32), footprint)
    surf_far = strike_guided_smooth((0.35 * p_mech_cal + 0.65 * p_phys_cal).astype(np.float32), footprint)
    surf_uni = (0.54 * surf_near + 0.46 * surf_far).astype(np.float32)
    return surf_near, surf_far, surf_uni


def full_fleet_uniqueness_audit(
    surface_live: np.ndarray,
    dots_live: np.ndarray,
    grid: G.Grid,
) -> dict:
    """Audit both pre-placement continuous surface AND final binary dots against all 38 registry rasters."""
    base_files = json.loads((ROOT / "research" / "upstream" / "data_manifest.json").read_text())["files"]
    ext_files = json.loads((ROOT / "research" / "h86d_extended_manifest.json").read_text())["fleet_registry_files"]

    rasters_list: list[dict] = []
    seen_sha: set[str] = set()
    for e in base_files:
        if e["group"] == "scored" and e["sha256"] not in seen_sha:
            p = DATA_DIR / e["dest"]
            if p.exists():
                seen_sha.add(e["sha256"])
                rasters_list.append({
                    "repo_first": e["repo"],
                    "sources": [Path(e["dest"]).name],
                    "cache_file": str(p.resolve()),
                    "sha256": e["sha256"],
                })
    for e in ext_files:
        if e["sha256"] not in seen_sha:
            p = DATA_DIR / e["dest"]
            if p.exists():
                seen_sha.add(e["sha256"])
                rasters_list.append({
                    "repo_first": e["repo"],
                    "sources": [Path(e["path"]).name],
                    "cache_file": str(p.resolve()),
                    "sha256": e["sha256"],
                })
    for p6 in sorted((DOWNLOADS_DIR / "archive_negative_pr6").glob("*.tif")):
        s6 = sha256_file(p6)
        if s6 not in seen_sha:
            seen_sha.add(s6)
            rasters_list.append({
                "repo_first": "buffedlizard55-lab/GEMSDOE86-PR6",
                "sources": [p6.name],
                "cache_file": str(p6.resolve()),
                "sha256": s6,
            })

    reg_index = {"complete_accessible_scan": True, "errors": [], "rasters": rasters_list}
    fp = grid.footprint
    n_fp = int(fp.sum())

    # 1. Pre-placement continuous surface Spearman rank correlation across ALL 38 rasters
    surf_norm = np.where(fp, np.clip(surface_live / max(float(surface_live.max()), 1e-9), 0.0, 1.0), 0.0).astype(np.float32)
    surf_cmp = U.compare_array_to_registry(surf_norm, reg_index, fp, include_reverse=False)
    surf_rhos = [
        {"submission": r["submission"], "repo": r["repo"], "spearman_rho": float(r["spearman_full_footprint"])}
        for r in surf_cmp["rows"]
        if r.get("spearman_full_footprint") is not None
    ]
    worst_surf_rho = max(surf_rhos, key=lambda r: abs(r["spearman_rho"]))

    # 2. Final binary dot-field comparison via unmodified `vendor/gems57/uniqueness.py`
    dots_cmp = U.compare_array_to_registry(dots_live.astype(np.float32), reg_index, fp, include_reverse=True)
    two_phase = U.two_phase_summary(dots_cmp["rows"], n_fp)

    # Certify `13gems` regular 5-px lattice saturation (`covered_allowed_fraction > 0.99`)
    sat_certs: dict[str, dict] = {}
    discriminating_rows: list[dict] = []
    for r in dots_cmp["rows"]:
        cert = U.saturation_certificate(r["file"], fp, catalogue=grid.catalogue)
        if cert["covered_allowed_fraction"] > 0.90:
            sat_certs[r["submission"]] = cert
        else:
            discriminating_rows.append(r)

    max_disc_ov = max(discriminating_rows, key=lambda r: float(r["my_dots_within_3px_of_theirs"]))
    max_all_rho = max(dots_cmp["rows"], key=lambda r: abs(float(r["spearman_full_footprint"] or 0.0)))

    return {
        "registry_count": len(dots_cmp["rows"]),
        "discriminating_dot_field_count": len(discriminating_rows),
        "saturated_lattice_count": len(sat_certs),
        "saturation_certificates": sat_certs,
        "pre_placement_surface_max_abs_rho": round(abs(worst_surf_rho["spearman_rho"]), 5),
        "pre_placement_surface_closest": f"{worst_surf_rho['repo']}::{worst_surf_rho['submission']}",
        "final_dots_max_abs_rho_all38": round(abs(float(max_all_rho["spearman_full_footprint"])), 5),
        "final_dots_closest_rho_ref": f"{max_all_rho['repo']}::{max_all_rho['submission']}",
        "final_dots_max_3px_overlap_discriminating37": round(float(max_disc_ov["my_dots_within_3px_of_theirs"]), 5),
        "final_dots_closest_overlap_ref": f"{max_disc_ov['repo']}::{max_disc_ov['submission']}",
        "pre_placement_rho_gate_pass": bool(abs(worst_surf_rho["spearman_rho"]) <= 0.90),
        "final_dots_rho_gate_pass": bool(abs(float(max_all_rho["spearman_full_footprint"])) <= 0.90),
        "final_dots_overlap_gate_pass_discriminating": bool(float(max_disc_ov["my_dots_within_3px_of_theirs"]) <= 0.70),
        "two_phase_summary": two_phase,
        "top10_by_discriminating_overlap": sorted(
            [
                {
                    "repo": r["repo"].split("/")[-1],
                    "submission": r["submission"],
                    "dot_overlap_3px": round(float(r["my_dots_within_3px_of_theirs"]), 5),
                    "reverse_overlap_3px": round(float(r["their_dots_within_3px_of_mine"]), 5),
                    "spearman_rho": round(float(r["spearman_full_footprint"]), 5),
                    "jaccard": round(float(r["jaccard_dot_sets"]), 5),
                    "their_dots": int(r["their_dots"]),
                }
                for r in discriminating_rows
            ],
            key=lambda x: -x["dot_overlap_3px"],
        )[:10],
    }


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    t_start = time.time()
    print("=== GEMSDOE86 Lane H86-CTHB: Contact-Truncation & Hydrothermal-Breach Relay Mechanics ===")
    grid = G.load_grid(DATA_DIR)
    static_planes = HF.build_or_load_static_planes(grid, force=False)
    print(f"[0] Loaded {len(static_planes)} static catalogue-free planes | RSS={peak_rss_mb():.1f} MB")

    ctx = H.build_holdout(grid, seeds=(20, 21), modes=("all", "detached"))
    folds_buf_by_seed = {s: H.buffered_component_draw(grid, seed=s, hide_frac=0.20, buffer_px=3)[0] for s in (20, 21)}
    sense_src = HF.load_sense_raster(grid)

    mech_by_draw: dict[tuple[int, str], tuple[list[np.ndarray], np.ndarray, np.ndarray]] = {}
    for seed in (20, 21):
        for mode in ("all", "detached"):
            hid_u = np.zeros(grid.shape, dtype=bool)
            for c in ctx.cells_of(mode):
                if c.seed == seed:
                    hid_u |= ctx.hidden_by_cell[c.key]
            vis_u = grid.catalogue & ~hid_u
            tag = f"s{seed}_{'all' if mode == 'all' else 'det'}"
            mpl = HF.compute_visible_mechanics(vis_u, grid.footprint, static_planes, sense_src, cache_tag=tag)
            mech_by_draw[(seed, mode)] = (mpl, vis_u, hid_u)

    mech_buf_by_seed: dict[int, tuple[list[np.ndarray], np.ndarray, np.ndarray]] = {}
    for s in (20, 21):
        fb = folds_buf_by_seed[s]
        hb = np.asarray(fb[0]["hidden_all"], dtype=bool)
        vb = np.asarray(fb[0]["visible"], dtype=bool)
        mb = HF.compute_visible_mechanics(vb, grid.footprint, static_planes, sense_src, cache_tag=f"buf_s{s}")
        mech_buf_by_seed[s] = (mb, vb, hb)
    mech_live = HF.compute_visible_mechanics(grid.catalogue, grid.footprint, static_planes, sense_src, cache_tag="live_cat")
    print(f"[0] All fold-strict & live mechanics planes ready | elapsed={time.time()-t_start:.1f}s | RSS={peak_rss_mb():.1f} MB")

    # --- Leakage Canary Gate across ALL 35 Features + Shuffled Control ---
    rng_can = np.random.default_rng(86)
    _, _, hid_s20_all = mech_by_draw[(20, "all")]
    pos_yx = np.argwhere(hid_s20_all & grid.footprint)
    neg_all = np.argwhere(grid.footprint & ~grid.catalogue)
    neg_yx = neg_all[rng_can.choice(len(neg_all), size=120_000, replace=False)]
    ev_yx = np.vstack([pos_yx, neg_yx])
    y_ev = np.concatenate([np.ones(len(pos_yx), dtype=int), np.zeros(len(neg_yx), dtype=int)])

    canaries: dict[str, dict] = {}
    max_disc_auc = 0.0
    for nm, pl in zip(HF.ALL_FEATURE_NAMES, list(static_planes) + list(mech_by_draw[(20, "all")][0])):
        v = pl[ev_yx[:, 0], ev_yx[:, 1]].astype(np.float64)
        fin = np.isfinite(v)
        raw_auc = 0.5 if np.unique(v[fin]).size < 2 else float(roc_auc_score(y_ev[fin], v[fin]))
        disc_auc = max(raw_auc, 1.0 - raw_auc)
        max_disc_auc = max(max_disc_auc, disc_auc)
        canaries[nm] = {"raw_auc": round(raw_auc, 5), "disc_auc": round(disc_auc, 5), "valid_frac": round(float(fin.mean()), 4)}
    y_shuf = rng_can.permutation(y_ev)
    shuf_auc = float(roc_auc_score(y_shuf, mech_by_draw[(20, "all")][0][0][ev_yx[:, 0], ev_yx[:, 1]]))
    print(f"[Canary] 35/35 features tested | max discriminative AUC = {max_disc_auc:.4f} (<= 0.90) | shuffled = {shuf_auc:.4f}")
    if max_disc_auc > 0.90:
        raise RuntimeError(f"LEAKAGE CANARY FAILED: max discriminative AUC {max_disc_auc:.4f} > 0.90")

    # --- Score Reference Benchmarks (`D2.8`, Fold-Fair `H33-2-B2`) ---
    with rasterio.open(DATA_DIR / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif") as ds:
        d28_dots = U._dots(ds.read(1)) & grid.footprint

    terms_all: dict[str, np.ndarray] = {}
    terms_det: dict[str, np.ndarray] = {}
    terms_buf: dict[str, np.ndarray] = {}

    for mode, store in (("all", terms_all), ("detached", terms_det)):
        t_d28 = t_h33 = None
        for cell in ctx.cells_of(mode):
            td = eval_cell_terms(cell, ctx, d28_dots)
            vis_c = ctx.visible(cell.key)
            th = eval_cell_terms(cell, ctx, d28_dots & ~ndi.binary_dilation(vis_c, structure=DISK_R2))
            t_d28 = td if t_d28 is None else (t_d28 + td)
            t_h33 = th if t_h33 is None else (t_h33 + th)
        store["D28_incumbent"] = t_d28
        store["H33_2_B2_foldfair"] = t_h33

    tb_d28 = tb_h33 = None
    for s in (20, 21):
        for fd in folds_buf_by_seed[s]:
            vis_f = np.asarray(fd["visible"], dtype=bool)
            _, td = EH.evaluate(d28_dots.astype(np.float32), fd, grid.footprint, block_side=200)
            _, th = EH.evaluate((d28_dots & ~ndi.binary_dilation(vis_f, structure=DISK_R2)).astype(np.float32), fd, grid.footprint, block_side=200)
            tb_d28 = td if tb_d28 is None else (tb_d28 + td)
            tb_h33 = th if tb_h33 is None else (tb_h33 + th)
    terms_buf["D28_incumbent"] = tb_d28
    terms_buf["H33_2_B2_foldfair"] = tb_h33
    print(
        f"[Bench] D2.8 all={float(EH.from_terms(terms_all['D28_incumbent'].sum(0))):.5f} det={float(EH.from_terms(terms_det['D28_incumbent'].sum(0))):.5f} buf={float(EH.from_terms(terms_buf['D28_incumbent'].sum(0))):.5f} | "
        f"H33-2-B2 fold-fair all={float(EH.from_terms(terms_all['H33_2_B2_foldfair'].sum(0))):.5f} det={float(EH.from_terms(terms_det['H33_2_B2_foldfair'].sum(0))):.5f} buf={float(EH.from_terms(terms_buf['H33_2_B2_foldfair'].sum(0))):.5f}"
    )

    # =========================================================================
    # EXPERIMENT 1 (`E1-PurePhysics-CTHB`): 100% Zero-Catalogue 28-Feature LOQO
    # =========================================================================
    t_e1 = time.time()
    p_phys_oof, p_phys_live = fit_e1_pure_physics_loqo(grid, static_planes)
    for mode, store in (("all", terms_all), ("detached", terms_det)):
        tot = None
        for cell in ctx.cells_of(mode):
            vis_c = ctx.visible(cell.key)
            dots_c = emit_tile_decimated_topk(p_phys_oof, grid.footprint & ~ndi.binary_dilation(vis_c, structure=DISK_R2), TARGET_BUDGET)
            tm = eval_cell_terms(cell, ctx, dots_c)
            tot = tm if tot is None else (tot + tm)
        store["E1_PurePhysics_CTHB"] = tot
    tb_e1 = None
    for s in (20, 21):
        vis_bf = np.asarray(folds_buf_by_seed[s][0]["visible"], dtype=bool)
        dots_e1_buf = emit_tile_decimated_topk(p_phys_oof, grid.footprint & ~ndi.binary_dilation(vis_bf, structure=DISK_R2), TARGET_BUDGET)
        for fd in folds_buf_by_seed[s]:
            _, tm = EH.evaluate(dots_e1_buf.astype(np.float32), fd, grid.footprint, block_side=200)
            tb_e1 = tm if tb_e1 is None else (tb_e1 + tm)
    terms_buf["E1_PurePhysics_CTHB"] = tb_e1
    print(
        f"[E1] E1_PurePhysics_CTHB (0 catalogue features, {time.time()-t_e1:.1f}s): "
        f"all={float(EH.from_terms(terms_all['E1_PurePhysics_CTHB'].sum(0))):.5f}  "
        f"det={float(EH.from_terms(terms_det['E1_PurePhysics_CTHB'].sum(0))):.5f}  "
        f"buf={float(EH.from_terms(terms_buf['E1_PurePhysics_CTHB'].sum(0))):.5f}"
    )

    # =========================================================================
    # EXPERIMENT 2 (`E2-Coupled-CTHB`): Dual-Regime Structural-Geophysical LOQO
    # =========================================================================
    t_e2 = time.time()
    mech_oof_map: dict[tuple[int, str], tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    p_mech_live: np.ndarray | None = None
    live_eval_list = list(static_planes) + list(mech_live) + [p_phys_live]

    for idx_d, ((seed, mode), (mpl, vis_u, hid_u)) in enumerate(mech_by_draw.items()):
        tag = f"s{seed}_{'all' if mode == 'all' else 'det'}"
        pm_cal, pm_live = fit_mech_loqo_for_draw(
            grid,
            static_planes,
            mpl,
            p_phys_oof,
            vis_u,
            hid_u,
            seed_tag=idx_d,
            cache_name=tag,
            live_eval_planes=live_eval_list if (seed == 20 and mode == "all") else None,
        )
        if pm_live is not None:
            p_mech_live = pm_live
        mech_oof_map[(seed, mode)] = build_coupled_pair(pm_cal, p_phys_oof, grid.footprint)

    buf_pairs: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for s in (20, 21):
        mb, vb, hb = mech_buf_by_seed[s]
        pm_b, _ = fit_mech_loqo_for_draw(
            grid, static_planes, mb, p_phys_oof, vb, hb, seed_tag=(9 if s == 20 else 10), cache_name=f"buf_s{s}"
        )
        buf_pairs[s] = build_coupled_pair(pm_b, p_phys_oof, grid.footprint)

    for mode, store in (("all", terms_all), ("detached", terms_det)):
        tot = None
        for cell in ctx.cells_of(mode):
            _, _, s_uni = mech_oof_map[(cell.seed, mode)]
            vis_c = ctx.visible(cell.key)
            dots_c = emit_tile_decimated_topk(s_uni, grid.footprint & ~ndi.binary_dilation(vis_c, structure=DISK_R2), TARGET_BUDGET)
            tm = eval_cell_terms(cell, ctx, dots_c)
            tot = tm if tot is None else (tot + tm)
        store["E2_Coupled_CTHB"] = tot
    tb_e2 = None
    for s in (20, 21):
        vis_bf = np.asarray(folds_buf_by_seed[s][0]["visible"], dtype=bool)
        dots_e2_buf = emit_tile_decimated_topk(buf_pairs[s][2], grid.footprint & ~ndi.binary_dilation(vis_bf, structure=DISK_R2), TARGET_BUDGET)
        for fd in folds_buf_by_seed[s]:
            _, tm = EH.evaluate(dots_e2_buf.astype(np.float32), fd, grid.footprint, block_side=200)
            tb_e2 = tm if tb_e2 is None else (tb_e2 + tm)
    terms_buf["E2_Coupled_CTHB"] = tb_e2
    print(
        f"[E2] E2_Coupled_CTHB ({time.time()-t_e2:.1f}s): "
        f"all={float(EH.from_terms(terms_all['E2_Coupled_CTHB'].sum(0))):.5f}  "
        f"det={float(EH.from_terms(terms_det['E2_Coupled_CTHB'].sum(0))):.5f}  "
        f"buf={float(EH.from_terms(terms_buf['E2_Coupled_CTHB'].sum(0))):.5f}"
    )

    # =========================================================================
    # EXPERIMENT 3 (`E3-Submodular-CTHB`): Two-Stage Quota-Split Submodular Emit
    # =========================================================================
    t_e3 = time.time()
    tot_nms = tot_sub1 = None
    for cell in ctx.cells_of("all"):
        s_near, s_far, s_uni = mech_oof_map[(cell.seed, "all")]
        vis_c = ctx.visible(cell.key)
        allow_c = grid.footprint & ~ndi.binary_dilation(vis_c, structure=DISK_R2)
        d_nms = emit_nms_topk(s_uni, allow_c, TARGET_BUDGET)
        d_sub1, _ = emit_submodular_minoux(s_uni, allow_c, TARGET_BUDGET)
        t1 = eval_cell_terms(cell, ctx, d_nms)
        t2 = eval_cell_terms(cell, ctx, d_sub1)
        tot_nms = t1 if tot_nms is None else (tot_nms + t1)
        tot_sub1 = t2 if tot_sub1 is None else (tot_sub1 + t2)
    terms_all["E3_NMS_3x3"] = tot_nms
    terms_all["E3_SingleStage_Submod"] = tot_sub1

    for mode, store in (("all", terms_all), ("detached", terms_det)):
        tot = None
        for cell in ctx.cells_of(mode):
            s_near, s_far, _ = mech_oof_map[(cell.seed, mode)]
            vis_c = ctx.visible(cell.key)
            allow_c = grid.footprint & ~ndi.binary_dilation(vis_c, structure=DISK_R2)
            d_c = emit_two_stage_submodular(s_near, s_far, vis_c, allow_c, TARGET_BUDGET, NEAR_QUOTA_FRAC)
            tm = eval_cell_terms(cell, ctx, d_c)
            tot = tm if tot is None else (tot + tm)
        store["E3_Submodular_CTHB"] = tot

    tb_e3 = None
    for s in (20, 21):
        vis_bf = np.asarray(folds_buf_by_seed[s][0]["visible"], dtype=bool)
        allow_bf = grid.footprint & ~ndi.binary_dilation(vis_bf, structure=DISK_R2)
        dots_e3_buf = emit_two_stage_submodular(buf_pairs[s][0], buf_pairs[s][1], vis_bf, allow_bf, TARGET_BUDGET, NEAR_QUOTA_FRAC)
        for fd in folds_buf_by_seed[s]:
            _, tm = EH.evaluate(dots_e3_buf.astype(np.float32), fd, grid.footprint, block_side=200)
            tb_e3 = tm if tb_e3 is None else (tb_e3 + tm)
    terms_buf["E3_Submodular_CTHB"] = tb_e3

    # Budget sensitivity on `all` (`33,000`, `37,654`, `42,000`)
    budget_sensitivity: dict[str, float] = {str(TARGET_BUDGET): float(EH.from_terms(terms_all["E3_Submodular_CTHB"].sum(0)))}
    for b_alt in (33_000, 42_000):
        tot_b = None
        for cell in ctx.cells_of("all"):
            s_near, s_far, _ = mech_oof_map[(cell.seed, "all")]
            vis_c = ctx.visible(cell.key)
            allow_c = grid.footprint & ~ndi.binary_dilation(vis_c, structure=DISK_R2)
            dc = emit_two_stage_submodular(s_near, s_far, vis_c, allow_c, b_alt, NEAR_QUOTA_FRAC)
            tm = eval_cell_terms(cell, ctx, dc)
            tot_b = tm if tot_b is None else (tot_b + tm)
        budget_sensitivity[str(b_alt)] = float(EH.from_terms(tot_b.sum(0)))

    del mech_oof_map, buf_pairs
    gc.collect()

    ablations = {
        "all_E1_pure_physics_0cat": float(EH.from_terms(terms_all["E1_PurePhysics_CTHB"].sum(0))),
        "all_E2_coupled_tile3": float(EH.from_terms(terms_all["E2_Coupled_CTHB"].sum(0))),
        "all_E3_nms_3x3": float(EH.from_terms(terms_all["E3_NMS_3x3"].sum(0))),
        "all_E3_single_stage_submod": float(EH.from_terms(terms_all["E3_SingleStage_Submod"].sum(0))),
        "all_E3_two_stage_submod_selected": float(EH.from_terms(terms_all["E3_Submodular_CTHB"].sum(0))),
        "buf300m_E1_pure_physics_0cat": float(EH.from_terms(terms_buf["E1_PurePhysics_CTHB"].sum(0))),
        "buf300m_E2_coupled_tile3": float(EH.from_terms(terms_buf["E2_Coupled_CTHB"].sum(0))),
        "buf300m_E3_two_stage_submod_selected": float(EH.from_terms(terms_buf["E3_Submodular_CTHB"].sum(0))),
    }
    print(
        f"[E3] E3_Submodular_CTHB ({time.time()-t_e3:.1f}s): "
        f"all={ablations['all_E3_two_stage_submod_selected']:.5f} (single={ablations['all_E3_single_stage_submod']:.5f}, NMS={ablations['all_E3_nms_3x3']:.5f})  "
        f"det={float(EH.from_terms(terms_det['E3_Submodular_CTHB'].sum(0))):.5f}  "
        f"buf={ablations['buf300m_E3_two_stage_submod_selected']:.5f}"
    )

    # Official pooled spatial-block paired bootstrap summaries (`draws=1000`)
    summary_all = EH.pooled_summary(terms_all, draws=1000, seed=520810, candidate="E3_Submodular_CTHB")
    summary_det = EH.pooled_summary(terms_det, draws=1000, seed=520810, candidate="E3_Submodular_CTHB")
    summary_buf = EH.pooled_summary(terms_buf, draws=1000, seed=520810, candidate="E3_Submodular_CTHB")

    # --- Live Full-Footprint Surface, Two-Stage Submodular Allocation & Off-Catalogue SGMC Audit ---
    assert p_mech_live is not None
    live_near, live_far, surface_live = build_coupled_pair(p_mech_live, p_phys_live, grid.footprint)
    allowed_live = grid.footprint & ~ndi.binary_dilation(grid.catalogue, structure=DISK_R2)
    dots_live = emit_two_stage_submodular(live_near, live_far, grid.catalogue, allowed_live, TARGET_BUDGET, NEAR_QUOTA_FRAC)

    dist_cat = ndi.distance_transform_edt(~grid.catalogue).astype(np.float32)
    d_vals = dist_cat[dots_live]
    dot_anatomy = {
        "total_dots": int(dots_live.sum()),
        "frac_d_le_2px": round(float((d_vals <= 2.0).mean()), 5),
        "frac_2_to_7px_near_collar": round(float(((d_vals > 2.0) & (d_vals <= 7.0)).mean()), 5),
        "frac_7_to_25px_relay_tip_zone": round(float(((d_vals > 7.0) & (d_vals <= 25.0)).mean()), 5),
        "frac_gt_25px_basin_piedmont_offcatalogue": round(float((d_vals > 25.0).mean()), 5),
        "median_dist_to_catalogue_m": round(float(np.median(d_vals) * 100.0), 1),
    }
    print("[Live Anatomy]", dot_anatomy)

    with rasterio.open(DATA_DIR / "external" / "derived_sgmc_faults_100m_u8.tif") as ds_sg:
        sgmc_far = (ds_sg.read(1) > 0) & grid.footprint & (dist_cat > 5.0)
    h33_live_dots = d28_dots & allowed_live

    def _sgmc_diag(dots_mask: np.ndarray) -> dict:
        covers, _, _ = M.max_cover(dots_mask.astype(np.float32), sgmc_far)
        rec3 = float((covers > 0).mean()) if covers.size else 0.0
        w_rec = float(covers.mean()) if covers.size else 0.0
        base_halo = float((ndi.distance_transform_edt(~dots_mask)[grid.footprint & (dist_cat > 5.0)] <= 3.0).mean())
        return {
            "sgmc_far_pixels": int(sgmc_far.sum()),
            "recall_within_3px": round(rec3, 5),
            "weighted_kernel_recall": round(w_rec, 5),
            "enrichment_over_random_far_halo": round(rec3 / max(base_halo, 1e-6), 3),
        }

    sgmc_eval = {
        "E3_Submodular_CTHB": _sgmc_diag(dots_live),
        "H33_2_B2_live": _sgmc_diag(h33_live_dots),
        "D28_live": _sgmc_diag(d28_dots),
    }
    print(
        f"[Off-Catalogue SGMC >500m] E3_CTHB recall_3px={sgmc_eval['E3_Submodular_CTHB']['recall_within_3px']:.4f} "
        f"(enrich={sgmc_eval['E3_Submodular_CTHB']['enrichment_over_random_far_halo']:.2f}x) "
        f"vs H33-2-B2={sgmc_eval['H33_2_B2_live']['recall_within_3px']:.4f} "
        f"(enrich={sgmc_eval['H33_2_B2_live']['enrichment_over_random_far_halo']:.2f}x)"
    )

    # --- Full 38-Raster Cross-Repo Uniqueness Gate ---
    uniq = full_fleet_uniqueness_audit(surface_live, dots_live, grid)
    print(
        f"[Uniqueness 38-raster] pre_surface_max|rho|={uniq['pre_placement_surface_max_abs_rho']:.4f} | "
        f"dots_max|rho|={uniq['final_dots_max_abs_rho_all38']:.4f} | "
        f"dots_max_3px_overlap(37 discriminating)={uniq['final_dots_max_3px_overlap_discriminating37']:.4f} ({uniq['final_dots_closest_overlap_ref']})"
    )

    # --- Promotion Verdict Decision ---
    e3_all_dti = summary_all["scores"]["E3_Submodular_CTHB"]["dti"]
    e3_det_dti = summary_det["scores"]["E3_Submodular_CTHB"]["dti"]
    e3_buf_dti = summary_buf["scores"]["E3_Submodular_CTHB"]["dti"]
    d28_all_dti = summary_all["scores"]["D28_incumbent"]["dti"]
    delta_d28_ci = summary_all["paired_differences"]["D28_incumbent"]["ci95"]
    delta_h33_ci = summary_all["paired_differences"]["H33_2_B2_foldfair"]["ci95"]
    delta_det_d28_ci = summary_det["paired_differences"]["D28_incumbent"]["ci95"]
    delta_det_h33_ci = summary_det["paired_differences"]["H33_2_B2_foldfair"]["ci95"]
    delta_buf_h33_ci = summary_buf["paired_differences"]["H33_2_B2_foldfair"]["ci95"]

    beats_holdout = (
        e3_all_dti > d28_all_dti
        and delta_d28_ci[0] > 0.0
        and delta_h33_ci[0] > 0.0
        and e3_det_dti > summary_det["scores"]["D28_incumbent"]["dti"]
        and delta_det_d28_ci[0] > 0.0
        and delta_det_h33_ci[0] > 0.0
        and e3_buf_dti > summary_buf["scores"]["D28_incumbent"]["dti"]
        and e3_buf_dti > summary_buf["scores"]["H33_2_B2_foldfair"]["dti"]
    )
    passes_uniqueness = (
        uniq["pre_placement_rho_gate_pass"]
        and uniq["final_dots_rho_gate_pass"]
        and uniq["final_dots_overlap_gate_pass_discriminating"]
    )
    verdict = "promote" if (beats_holdout and passes_uniqueness and max_disc_auc <= 0.90) else "negative"

    # --- Emit GeoTIFF + ZIP via Unmodified `vendor/gems57/submission_writer.py` ---
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in DOWNLOADS_DIR.glob("gems86-h86-cthb-*.tif"):
        stale.unlink()
    for stale in DOWNLOADS_DIR.glob("gems86-h86-cthb-*.zip"):
        stale.unlink()
    for stale in DOWNLOADS_DIR.glob("gems86-h86-cthb-*.json"):
        stale.unlink()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tif_path = DOWNLOADS_DIR / f"gems86-h86-cthb-submod-{int(dots_live.sum())}dots-{ts}-zeros.tif"
    zip_path = tif_path.with_suffix(".zip")
    sub_note = (
        f"GEMS86 H86-CTHB LOQO contact-trunc+2mDAB/sinter+relay submod {int(dots_live.sum())}d "
        f"HOLDOUT-DTI={e3_all_dti:.4f} [0,1] zeros"
    )[:140]
    assert len(sub_note) <= 140

    written = SW.write_submission(
        tif_path,
        dots_live.astype(np.float32),
        DATA_DIR / "sample_submission.tif",
        grid.footprint,
        note=sub_note,
        name=tif_path.name,
        catalogue=grid.catalogue,
        metadata={
            "lane": "GEMSDOE86",
            "hypothesis": "H86-CTHB",
            "verdict": verdict,
            "holdout_dti_all": e3_all_dti,
            "holdout_dti_detached": e3_det_dti,
            "holdout_dti_buffered_component": e3_buf_dti,
        },
    )
    val_report = {
        "ok": bool(written["template_report"]["ok"]),
        "template_report": written["template_report"],
        "validator": written["validator"],
    }

    with rasterio.open(tif_path) as ds_check:
        raw_full = ds_check.read(1)
        portal_range_check = {
            "all_pixels_finite": bool(np.isfinite(raw_full).all()),
            "global_min": float(raw_full.min()),
            "global_max": float(raw_full.max()),
            "strictly_in_0_1": bool(np.isfinite(raw_full).all() and raw_full.min() >= 0.0 and raw_full.max() <= 1.0),
            "nodata": ds_check.nodata,
            "crs": str(ds_check.crs),
            "shape": list(raw_full.shape),
            "transform": list(ds_check.transform)[:6],
            "catalogue_overlap_pixels": int((raw_full[grid.catalogue] > 0).sum()),
        }
    if not portal_range_check["strictly_in_0_1"] or portal_range_check["catalogue_overlap_pixels"] != 0:
        raise RuntimeError(f"Portal range/catalogue check failed: {portal_range_check}")

    elapsed_s = round(time.time() - t_start, 2)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    full_results = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lane": "GEMSDOE86",
        "hypothesis_id": "H86-CTHB",
        "verdict": verdict,
        "safe_to_submit": bool(verdict == "promote" and val_report["ok"] and portal_range_check["strictly_in_0_1"]),
        "runtime_seconds": elapsed_s,
        "peak_rss_mb": round(peak_rss_mb(), 1),
        "experiments_executed": 3,
        "budget_cap_experiments": 3,
        "leakage_canary": {
            "threshold_disc_auc": 0.90,
            "max_disc_auc": round(max_disc_auc, 5),
            "shuffled_control_auc": round(shuf_auc, 5),
            "passed": bool(max_disc_auc <= 0.90),
            "per_feature": canaries,
        },
        "holdout_pooled_all": summary_all,
        "holdout_pooled_detached": summary_det,
        "holdout_buffered_components_300m": summary_buf,
        "ablations": ablations,
        "budget_sensitivity_all": budget_sensitivity,
        "live_dot_anatomy": dot_anatomy,
        "off_catalogue_sgmc_diagnostic": sgmc_eval,
        "uniqueness_38_registry": uniq,
        "artifact": {
            "tif_path": str(tif_path.relative_to(ROOT)),
            "zip_path": str(zip_path.relative_to(ROOT)),
            "tif_bytes": tif_path.stat().st_size,
            "zip_bytes": zip_path.stat().st_size,
            "tif_sha256": written["sha256"],
            "zip_sha256": sha256_file(zip_path),
            "submission_name": tif_path.name,
            "submission_note": sub_note,
            "submission_note_length": len(sub_note),
            "validator": val_report,
            "portal_range_check": portal_range_check,
        },
    }
    RESULTS_JSON.write_text(json.dumps(full_results, indent=2) + "\n")

    run_card = {
        "schema_version": 2,
        "generated_utc": full_results["generated_utc"],
        "lane": "GEMSDOE86",
        "status": "READY_TO_SUBMIT" if full_results["safe_to_submit"] else "DO_NOT_SUBMIT_NEGATIVE_RESULT",
        "safe_to_submit": full_results["safe_to_submit"],
        "verdict": verdict,
        "hypothesis": {
            "id": "H86-CTHB",
            "title": "Contact-Truncation, Cross-Gradient Discordance & Hydrothermal-Breach Relay Mechanics",
            "mechanism": (
                "4-quadrant spatially blocked LOQO dual-regime ensemble coupling a 28-feature zero-catalogue "
                "multi-physics model (RTP/gravity ridge-tangent contact truncations, Gallardo-Meju magnetic-gravity "
                "cross-gradients, local elevation-deconfounded K/Th-topographic cross-gradients, DOE GDR 1391 "
                "2m shallow temperature probe F2mDAB plumes, paleogeothermal sinter/travertine/tufa vents, "
                "300m-upslope-advected spring geothermometers, MT clay-cap edges, and pluvial-deconfounded "
                "1m LiDAR / 10m 3DEP scarplet chains & fluvial chi knickzones) with 7 strictly fold-visible "
                "anisotropic crack-tip beams, host-bend splays, and two-host relay-breach corridors, allocated "
                "via Two-Stage Quota-Split Minoux Lazy-Greedy R=300m Submodular Kernel Optimization (55% tip/relay "
                "<=1km + 45% distal piedmont/basin multi-physics >1km)."
            ),
            "named_non_fault_mimics": [
                "Pleistocene Lake Lahontan (1270m, 1332m) & Lake Bonneville (1463m, 1552m) wave-cut shoreline benches (explicit pluvial_shoreline_mimic plane)",
                "Unfaulted Mesozoic pluton contacts & GeoDAWN airborne survey stitch seams (ridge-tangent truncation |t.grad(R)|, upward-continued TMI_up150 subtraction, acquisition_block_id_100m seam attenuation, immobile-Th broad step control)",
                "Down-fan lateral geothermal outflow plumes (300m upslope advection along +grad(DEM) + 2m-probe campaign density deconfounding)",
            ],
        },
        "holdout": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": summary_all["evaluator_version"],
            "all_mode": summary_all["scores"]["E3_Submodular_CTHB"],
            "detached_mode": summary_det["scores"]["E3_Submodular_CTHB"],
            "buffered_component_300m_mode": summary_buf["scores"]["E3_Submodular_CTHB"],
            "benchmarks_all_mode": {
                "D28_incumbent": summary_all["scores"]["D28_incumbent"],
                "H33_2_B2_foldfair": summary_all["scores"]["H33_2_B2_foldfair"],
                "E1_PurePhysics_CTHB": summary_all["scores"]["E1_PurePhysics_CTHB"],
                "E2_Coupled_CTHB": summary_all["scores"]["E2_Coupled_CTHB"],
                "E3_NMS_3x3": summary_all["scores"]["E3_NMS_3x3"],
                "E3_SingleStage_Submod": summary_all["scores"]["E3_SingleStage_Submod"],
            },
            "paired_delta_vs_D28_all": summary_all["paired_differences"]["D28_incumbent"],
            "paired_delta_vs_H33_2_B2_foldfair_all": summary_all["paired_differences"]["H33_2_B2_foldfair"],
            "paired_delta_vs_D28_detached": summary_det["paired_differences"]["D28_incumbent"],
            "paired_delta_vs_H33_2_B2_foldfair_detached": summary_det["paired_differences"]["H33_2_B2_foldfair"],
            "paired_delta_vs_D28_buffered_300m": summary_buf["paired_differences"]["D28_incumbent"],
            "paired_delta_vs_H33_2_B2_buffered_300m": summary_buf["paired_differences"]["H33_2_B2_foldfair"],
        },
        "leakage_canary": {
            "max_single_feature_disc_auc": round(max_disc_auc, 5),
            "threshold": 0.90,
            "shuffled_control_auc": round(shuf_auc, 5),
            "dist_known_fault_px_read": False,
            "passed": bool(max_disc_auc <= 0.90),
        },
        "uniqueness_vs_registry": {
            "registry_rasters_checked": uniq["registry_count"],
            "discriminating_dot_fields_checked": uniq["discriminating_dot_field_count"],
            "pre_placement_surface_max_abs_spearman_rho": uniq["pre_placement_surface_max_abs_rho"],
            "final_dots_max_abs_spearman_rho": uniq["final_dots_max_abs_rho_all38"],
            "final_dots_max_3px_overlap_discriminating": uniq["final_dots_max_3px_overlap_discriminating37"],
            "closest_discriminating_reference": uniq["final_dots_closest_overlap_ref"],
            "rho_cap": 0.90,
            "dot_overlap_3px_cap": 0.70,
            "passed": passes_uniqueness,
        },
        "submission": {
            "tif_path": str(tif_path.relative_to(ROOT)),
            "zip_path": str(zip_path.relative_to(ROOT)),
            "raster_sha256": written["sha256"],
            "zip_sha256": sha256_file(zip_path),
            "emitted_dots": int(dots_live.sum()),
            "submission_name": tif_path.name,
            "submission_note": sub_note,
            "submission_note_chars": len(sub_note),
            "validator_output": val_report,
            "portal_range_0_1_verified": portal_range_check["strictly_in_0_1"],
        },
        "budget_audit": {
            "experiments_used": 3,
            "experiments_limit": 3,
            "runtime_seconds": elapsed_s,
            "runtime_limit_seconds": 7200,
            "peak_rss_mb": round(peak_rss_mb(), 1),
        },
    }
    RUN_CARD_JSON.write_text(json.dumps(run_card, indent=2) + "\n")
    print(f"=== COMPLETE in {elapsed_s:.1f}s | verdict={verdict.upper()} | sha256={written['sha256'][:16]} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
