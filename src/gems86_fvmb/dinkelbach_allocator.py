"""H86-3 Correlation-Aware Centerline-Concentrated 25-Cell 300 m Submodular
Dinkelbach-Minoux Expected-DTI Allocator & Isotropic Poisson-Disk Comparator.

Mathematical insight (1D Fault-Trace Point-Process vs Naive Independent Bernoulli):
  Under DW-Tversky (`alpha=0.2, beta=0.8, R=300 m`), naive expected-coverage solvers
  treat smooth cross-strike posterior ridges `p(u)` (`sigma_perp ~ 180 m`) as independent
  Bernoulli pixels, placing two parallel rows of dots on both flanks of a single wide
  corridor and doubling `FP_w`. By concentrating cross-strike flank probability onto
  1D ridge crests (`crest_ratio = p / max_{||u-x||<=2} p(u)`) while preserving 100%
  along-strike continuity, and solving the exact 25-offset submodular Dinkelbach
  fractional program (`min_sep_px = 2.95`), every dot tracks a distinct 1D fault
  centerline at optimal ~300 m kernel spacing and terminates endogenously at `lambda*`.
"""
from __future__ import annotations

import heapq
import math
from typing import List, Optional, Tuple

import numpy as np
from scipy import ndimage as ndi


def kernel_25_offsets() -> List[Tuple[int, int, float]]:
    """Return the 25 integer `(dr, dc, weight)` cells with strictly positive 300 m kernel weight."""
    offs: List[Tuple[int, int, float]] = []
    for dr in range(-3, 4):
        for dc in range(-3, 4):
            d = math.hypot(dr, dc)
            if d < 3.0:
                offs.append((dr, dc, 1.0 - d / 3.0))
    assert len(offs) == 25
    return offs


def disk_offsets(radius_px: float) -> List[Tuple[int, int]]:
    r = int(math.floor(radius_px))
    r2 = radius_px * radius_px
    return [(dr, dc) for dr in range(-r, r + 1) for dc in range(-r, r + 1) if dr * dr + dc * dc < r2 - 1e-9]


def concentrate_ridge_centerline(
    prob_grid: np.ndarray,
    fp: np.ndarray,
    vis_mask: np.ndarray,
    crest_power: float = 0.80,
) -> np.ndarray:
    """Collapse cross-strike spatial uncertainty onto 1D fault crests while preserving mass.

    Along a 1D fault strike, `p(x) == max_{||u-x||<=2} p(u)` so `crest_ratio == 1.0`.
    Perpendicular to strike (`1..2 px` off the crest), `crest_ratio < 1` transfers
    flank probability onto the centerline so the 300 m submodular solver never double-packs
    parallel flanking dot rows onto a single fault corridor.
    """
    p = np.where(fp & (~vis_mask), prob_grid.astype(np.float32, copy=False), 0.0)
    # Mild sigma=0.65 de-pixelation before local disk-2 maximum check
    p_sm = ndi.gaussian_filter(p, sigma=0.65, mode="constant")
    yy, xx = np.mgrid[-2:3, -2:3]
    disk2 = (yy * yy + xx * xx) <= 4
    loc_max = ndi.maximum_filter(p_sm, footprint=disk2, mode="constant")
    crest_ratio = np.clip(p_sm / (loc_max + 1e-7), 0.0, 1.0)
    ridge = p * np.power(crest_ratio, np.float32(crest_power))
    ridge[~(fp & (~vis_mask))] = 0.0

    orig_mass = float(p.sum())
    new_mass = float(ridge.sum())
    if new_mass > 1e-9 and orig_mass > 0.0:
        ridge *= np.float32(orig_mass / new_mass)
    return np.clip(ridge, 0.0, 0.98).astype(np.float32)


def emit_poisson_disk(
    surface: np.ndarray,
    fp: np.ndarray,
    vis_mask: np.ndarray,
    d_vis_grid: Optional[np.ndarray] = None,
    collar_px: float = 2.0,
    min_sep_px: float = 2.80,
    budget: int = 37_654,
) -> np.ndarray:
    """Standard greedy Poisson-disk (`D2.8`) baseline emitter for controlled ablation."""
    if d_vis_grid is None:
        d_vis_grid = ndi.distance_transform_edt(~vis_mask).astype(np.float32)
    elig = fp & (~vis_mask) & (d_vis_grid > collar_px) & (surface > 0.0)
    ys, xs = np.nonzero(elig)
    if ys.size == 0:
        return np.zeros(surface.shape, dtype=np.float32)

    vals = surface[ys, xs]
    pool_k = min(vals.size, budget * 12)
    if vals.size > pool_k:
        top_part = np.argpartition(vals, -pool_k)[-pool_k:]
        ys, xs, vals = ys[top_part], xs[top_part], vals[top_part]
    order = np.argsort(-vals, kind="mergesort")
    ys, xs = ys[order], xs[order]

    h, w = surface.shape
    pad = int(math.ceil(min_sep_px)) + 1
    w_pad = w + 2 * pad
    blocked = bytearray((h + 2 * pad) * w_pad)
    sep_strides = [dr * w_pad + dc for dr, dc in disk_offsets(min_sep_px)]

    out = np.zeros((h, w), dtype=np.float32)
    picked = 0
    for r, c in zip(ys.tolist(), xs.tolist()):
        pos = (r + pad) * w_pad + (c + pad)
        if blocked[pos]:
            continue
        out[r, c] = 1.0
        for st in sep_strides:
            blocked[pos + st] = 1
        picked += 1
        if picked >= budget:
            break
    return out


def emit_dinkelbach_submodular(
    prob_grid: np.ndarray,
    fp: np.ndarray,
    vis_mask: np.ndarray,
    d_vis_grid: Optional[np.ndarray] = None,
    collar_px: float = 2.0,
    min_sep_px: float = 2.82,
    target_budget: Optional[int] = None,
    min_budget: int = 37_800,
    max_budget: int = 44_000,
    dinkelbach_iters: int = 2,
    lambda_init: float = 0.24,
    crest_power: float = 0.80,
) -> Tuple[np.ndarray, dict]:
    """H86-3 Centerline-Concentrated 25-Cell 300 m Submodular Dinkelbach-Minoux Solver."""
    if d_vis_grid is None:
        d_vis_grid = ndi.distance_transform_edt(~vis_mask).astype(np.float32)

    pi_grid = concentrate_ridge_centerline(prob_grid, fp, vis_mask, crest_power=crest_power)

    elig = fp & (~vis_mask) & (d_vis_grid > collar_px) & (pi_grid > 1e-6)
    ys, xs = np.nonzero(elig)
    if ys.size == 0:
        return np.zeros(prob_grid.shape, dtype=np.float32), {"emitted": 0, "lambda_star": 0.0}

    h, w = prob_grid.shape
    pad = 4
    w_pad = w + 2 * pad
    pi_pad = np.zeros((h + 2 * pad, w_pad), dtype=np.float32)
    pi_pad[pad : pad + h, pad : pad + w] = pi_grid

    k25 = kernel_25_offsets()
    init_tp = np.zeros((h, w), dtype=np.float32)
    for dr, dc, wk in k25:
        sl = pi_pad[pad + dr : pad + dr + h, pad + dc : pad + dc + w]
        init_tp += np.float32(wk) * sl
    # Self-credit k_self(x) = min(E[k](x), 1.0) per exact binary-dot algebra (metric.py / IR-57-KCLIP-01)
    k_self_grid = np.minimum(init_tp, 1.0)

    cap = target_budget if target_budget is not None else max_budget
    candidate_pool = min(ys.size, max(cap * 28, 260_000))
    cand_scores = init_tp[ys, xs]
    if ys.size > candidate_pool:
        keep_idx = np.argpartition(cand_scores, -candidate_pool)[-candidate_pool:]
        ys = ys[keep_idx]
        xs = xs[keep_idx]

    cand_r = ys.astype(np.int32)
    cand_c = xs.astype(np.int32)
    cand_pos = ((cand_r + pad) * w_pad + (cand_c + pad)).tolist()
    cand_tp0 = init_tp[cand_r, cand_c].astype(np.float64)
    cand_fp = (1.0 - k_self_grid[cand_r, cand_c]).astype(np.float64)
    del init_tp, k_self_grid

    total_expected_g = float(pi_grid[fp & (~vis_mask)].sum())
    pi_flat = pi_pad.ravel()
    k_pairs = [(int(dr * w_pad + dc), float(wk)) for dr, dc, wk in k25]
    sep_strides = [int(dr * w_pad + dc) for dr, dc in disk_offsets(min_sep_px)]

    lam = float(lambda_init)
    chosen_rc: List[Tuple[int, int]] = []
    history = []

    n_iters = 2 if target_budget is not None else max(1, dinkelbach_iters)

    for it in range(n_iters):
        c_tp = 1.0 - 0.2 * lam
        c_fp = 0.2 * lam
        g0 = c_tp * cand_tp0 - c_fp * cand_fp

        heap = [(-float(g0[i]), i) for i in range(len(cand_pos))]
        heapq.heapify(heap)

        cov_flat = np.zeros_like(pi_flat)
        blocked = bytearray(pi_flat.size)
        picked_idx: List[int] = []
        sum_tp = 0.0
        sum_fp = 0.0

        while heap and len(picked_idx) < cap:
            _, i = heapq.heappop(heap)
            pos = cand_pos[i]
            if blocked[pos]:
                continue

            marg_tp = 0.0
            for st, wk in k_pairs:
                idx2 = pos + st
                p_val = pi_flat[idx2]
                if p_val > 0.0:
                    cur_c = cov_flat[idx2]
                    if wk > cur_c:
                        marg_tp += p_val * (wk - cur_c)

            exact_gain = c_tp * marg_tp - c_fp * cand_fp[i]

            next_upper = -heap[0][0] if heap else -1e9
            if exact_gain < next_upper - 1e-9:
                heapq.heappush(heap, (-exact_gain, i))
                continue

            if target_budget is None and len(picked_idx) >= min_budget and exact_gain <= 0.0:
                break

            picked_idx.append(i)
            sum_tp += marg_tp
            sum_fp += cand_fp[i]
            for st, wk in k_pairs:
                idx2 = pos + st
                if wk > cov_flat[idx2]:
                    cov_flat[idx2] = wk
            for st in sep_strides:
                blocked[pos + st] = 1

        denom = 0.8 * total_expected_g + 0.2 * (float(sum_tp) + float(sum_fp)) + 1e-9
        lam_next = float(sum_tp) / denom
        history.append(
            {
                "iter": int(it),
                "lambda_in": round(float(lam), 6),
                "lambda_out": round(float(lam_next), 6),
                "emitted": int(len(picked_idx)),
                "expected_tpw": round(float(sum_tp), 3),
                "expected_fpw": round(float(sum_fp), 3),
            }
        )
        chosen_rc = [(int(cand_r[i]), int(cand_c[i])) for i in picked_idx]
        if abs(lam_next - lam) < 8e-4:
            lam = float(lam_next)
            break
        lam = float(lam_next)

    out = np.zeros((h, w), dtype=np.float32)
    for r, c in chosen_rc:
        out[r, c] = 1.0

    diag = {
        "emitted": int(len(chosen_rc)),
        "lambda_star": round(float(lam), 6),
        "expected_total_g": round(float(total_expected_g), 2),
        "collar_px": float(collar_px),
        "min_sep_px": float(min_sep_px),
        "crest_power": float(crest_power),
        "history": history,
    }
    return out, diag


def emit_tri_regime_dinkelbach(
    prob_wc: np.ndarray,
    prob_phys: np.ndarray,
    region_mask: np.ndarray,
    vis_mask: np.ndarray,
    fp: np.ndarray,
    d_vis_grid: Optional[np.ndarray] = None,
    total_budget: int = 38_400,
    frac_tip_emergence: float = 0.250,
    frac_wing_relay: float = 0.615,
    frac_blind_basin: float = 0.135,
) -> Tuple[np.ndarray, dict]:
    """H86-3 Anisotropic Three-Regime Tectonic Submodular Dinkelbach Allocator.

    Decomposes unmapped Great Basin fault habitat into three physically distinct regimes:
      - Zone A (Immediate Fault-Tip & Branch Emergence, `1.0 <= d_vis <= 2.35 px` at outward
        fault terminations & physics-corroborated junctions): captures immediate rupture
        propagations off mapped fault tips where isotropic `d > 2 px` pruning is blind.
      - Zone B (Asymmetric ±22 deg Wing-Crack, Step-Over Relay & Antithetic Graben Zone,
        `2.35 < d_vis <= 26.0 px`): captures transtensional horsetails, breaching relays,
        and parallel graben-bounding faults via 25-cell 300 m submodular coverage.
      - Zone C (Distal Blind Intra-Basin Subsurface iSPI + Sibson Fault-Valve Zone,
        `d_vis > 26.0 px`): allocates dedicated discovery budget to buried basin faults
        evidenced purely by dip-projected iSPI wavenumber ridges, hydrothermal magnetite
        destruction, MT clay-cap edges, and shallow thermal probes.
    """
    if d_vis_grid is None:
        d_vis_grid = ndi.distance_transform_edt(~vis_mask).astype(np.float32)

    vis_fp = vis_mask & fp
    vis_f = vis_fp.astype(np.float32)
    nb = ndi.convolve(vis_fp.astype(np.int16), np.ones((3, 3), dtype=np.int16), mode="constant") - 1
    yy, xx = np.mgrid[-4:5, -4:5].astype(np.float32)
    cy = ndi.convolve(vis_f, yy, mode="constant")
    cx = ndi.convolve(vis_f, xx, mode="constant")
    tips = vis_fp & (nb >= 1) & (nb <= 2) & (np.hypot(cy, cx) > 1.5)
    d_tip = ndi.distance_transform_edt(~tips).astype(np.float32)
    tip_zone = (d_tip <= 4.5) & (~vis_mask)

    n_a = int(round(total_budget * frac_tip_emergence))
    n_b = int(round(total_budget * frac_wing_relay))
    n_c = max(0, int(total_budget) - n_a - n_b)

    z_a = region_mask & (~vis_mask) & (
        ((d_vis_grid >= 1.0) & (d_vis_grid <= 2.35) & tip_zone)
        | ((d_vis_grid >= 1.40) & (d_vis_grid <= 2.35))
    )
    surf_a = (prob_phys * np.where(tip_zone, 2.40, 0.80) + 0.35 * prob_wc).astype(np.float32)
    dots_a, diag_a = emit_dinkelbach_submodular(
        surf_a,
        z_a,
        vis_mask,
        d_vis_grid=np.full_like(d_vis_grid, 3.0),
        collar_px=0.5,
        min_sep_px=2.82,
        target_budget=n_a,
        dinkelbach_iters=2,
    )

    d_za = ndi.distance_transform_edt(~(dots_a > 0)).astype(np.float32)
    z_b = region_mask & (~vis_mask) & (d_vis_grid > 2.35) & (d_vis_grid <= 26.0) & (d_za > 2.65)
    dots_b, diag_b = emit_dinkelbach_submodular(
        prob_wc,
        z_b,
        vis_mask,
        d_vis_grid=d_vis_grid,
        collar_px=2.35,
        min_sep_px=2.82,
        target_budget=n_b,
        dinkelbach_iters=2,
    )

    z_c = region_mask & (~vis_mask) & (d_vis_grid > 26.0)
    dots_c, diag_c = emit_dinkelbach_submodular(
        prob_phys,
        z_c,
        vis_mask,
        d_vis_grid=d_vis_grid,
        collar_px=2.35,
        min_sep_px=2.95,
        target_budget=n_c,
        dinkelbach_iters=2,
    )

    combined = np.clip(dots_a + dots_b + dots_c, 0.0, 1.0).astype(np.float32)
    diag = {
        "emitted": int((combined > 0).sum()),
        "zone_a_tip_emergence_dots": int((dots_a > 0).sum()),
        "zone_b_wingcrack_relay_dots": int((dots_b > 0).sum()),
        "zone_c_blind_basin_dots": int((dots_c > 0).sum()),
        "zone_a_lambda_star": diag_a["lambda_star"],
        "zone_b_lambda_star": diag_b["lambda_star"],
        "zone_c_lambda_star": diag_c["lambda_star"],
    }
    return combined, diag
