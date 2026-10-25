"""Exact 3-Strand Frechet-Comonotonic Fault-Tube Survival Self-Credit &
Dinkelbach Fractional-Programming CELF (Minoux 1978) Submodular Allocator
on the Official 300 m Triangular DTI Kernel for Lane H86M-PFTE.

Mathematical Properties (verified by unit tests):
  1. Deterministic Exactness: when p in {0, 1}^{H x W}, comonotonic tube self-credit
     equals max_{||delta||_2 <= 3} G(y + delta) * K(delta) identically.
  2. Frechet-Hoeffding Bounds: for all p in [0, 1]^{H x W} and all spin-2 orientations,
       p(y) <= k_self_tube(y) <= k_self_indep_bernoulli(y) <= 1.
  3. Headless Spin-2 Gauge Invariance: flipping strike angle theta -> theta + pi swaps
     flanking tubes T_{-1} <-> T_{+1} and leaves 1 - (1-M_{-1})(1-M_0)(1-M_{+1})
     invariant up to floating-point associativity.
  4. Diffuse-Apron Suppression: along a single 1-D fault ridge (|d_perp| <= 1.05 px),
     comonotonic coupling evaluates the weighted strand supremum rather than inflating
     self-credit as 1 - prod_j (1 - p_j) across 7-9 correlated pixels.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from pathlib import Path
import sys

import numpy as np

VENDOR = Path(__file__).resolve().parents[2] / "vendor"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from gems57.emit import expected_credit
from gems57.metric import ALPHA, BETA, EPS, OFF_DX, OFF_DY, OFF_K


@dataclass(frozen=True)
class ComonotonicDCELFAllocation:
    dots: np.ndarray
    n_dots: int
    total_covered_credit: float
    total_self_credit: float
    final_lambda: float
    n_recomputations: int
    n_candidates: int
    outer_lambdas: tuple[float, ...]


def _spacing_disc(min_spacing_px: float) -> tuple[int, np.ndarray]:
    if min_spacing_px <= 0.0:
        return 0, np.ones((1, 1), dtype=bool)
    r = int(math.ceil(float(min_spacing_px)))
    yy, xx = np.ogrid[-r : r + 1, -r : r + 1]
    disc = (yy * yy + xx * xx) < float(min_spacing_px) ** 2
    return r, disc


def _sorted_kernel_levels() -> tuple[np.ndarray, np.ndarray]:
    """Return descending distinct nonzero kernel weights and per-offset ring indices."""
    rounded = np.round(OFF_K.astype(np.float64), 12)
    uniq_desc = np.array(sorted(set(rounded.tolist()), reverse=True), dtype=np.float64)
    level_of_off = np.array(
        [int(np.where(uniq_desc == rw)[0][0]) for rw in rounded], dtype=np.int32
    )
    dw = np.empty_like(uniq_desc)
    dw[:-1] = uniq_desc[:-1] - uniq_desc[1:]
    dw[-1] = uniq_desc[-1]
    return uniq_desc, dw, level_of_off


_UNIQ_W, _DW_LEVELS, _OFF_RING_IDX = _sorted_kernel_levels()


def comonotonic_tube_self_credit_points(
    p_truth: np.ndarray,
    ys: np.ndarray,
    xs: np.ndarray,
    c2_strike: np.ndarray | None = None,
    s2_strike: np.ndarray | None = None,
    *,
    tube_halfwidth_px: float = 1.05,
    chunk_size: int = 65536,
) -> np.ndarray:
    """Evaluate exact 3-strand Frechet-comonotonic tube-survival self-credit at (ys, xs).

    Offsets within |d_perp| <= tube_halfwidth_px of the local fault trace belong to the
    central comonotonic strand T_0; offsets on opposite flanks (d_perp < -hw, d_perp > +hw)
    form flanking strands T_{-1}, T_{+1}. Within each strand G_j = 1[U_s < p_j], while
    distinct parallel strands combine independently.
    """
    p = np.clip(np.asarray(p_truth, dtype=np.float32), 0.0, 1.0)
    H, W = p.shape
    ys_i = np.asarray(ys, dtype=np.int64)
    xs_i = np.asarray(xs, dtype=np.int64)
    n_pts = ys_i.size
    if n_pts == 0:
        return np.zeros(0, dtype=np.float32)

    pad = 3
    p_pad = np.pad(p, pad, mode="constant", constant_values=0.0)
    off_dy = OFF_DY.astype(np.int64)
    off_dx = OFF_DX.astype(np.int64)
    off_dy_f = OFF_DY.astype(np.float32)[None, :]
    off_dx_f = OFF_DX.astype(np.float32)[None, :]
    n_rings = _DW_LEVELS.size
    hw = float(tube_halfwidth_px)

    out = np.empty(n_pts, dtype=np.float32)
    for s0 in range(0, n_pts, chunk_size):
        s1 = min(n_pts, s0 + chunk_size)
        yc = ys_i[s0:s1, None] + pad + off_dy[None, :]
        xc = xs_i[s0:s1, None] + pad + off_dx[None, :]
        vals = p_pad[yc, xc]  # (B, 29)

        if c2_strike is None or s2_strike is None:
            c2 = np.ones((s1 - s0, 1), dtype=np.float32)
            s2 = np.zeros((s1 - s0, 1), dtype=np.float32)
        else:
            c2 = np.asarray(c2_strike[ys_i[s0:s1], xs_i[s0:s1]], dtype=np.float32)[:, None]
            s2 = np.asarray(s2_strike[ys_i[s0:s1], xs_i[s0:s1]], dtype=np.float32)[:, None]

        theta = 0.5 * np.arctan2(s2, c2)
        sin_t = np.sin(theta).astype(np.float32)
        cos_t = np.cos(theta).astype(np.float32)
        # Normal vector to fault strike (cos theta, sin theta) in (x_east, r_south) is (-sin theta, cos theta)
        d_perp = -off_dx_f * sin_t + off_dy_f * cos_t  # (B, 29)

        m_neg_mask = d_perp < -hw
        m_mid_mask = np.abs(d_perp) <= hw
        m_pos_mask = d_perp > hw

        b_len = s1 - s0
        m_neg = np.zeros(b_len, dtype=np.float32)
        m_mid = np.zeros(b_len, dtype=np.float32)
        m_pos = np.zeros(b_len, dtype=np.float32)
        acc = np.zeros(b_len, dtype=np.float32)

        for r_idx in range(n_rings):
            ring_cols = np.where(_OFF_RING_IDX == r_idx)[0]
            vr = vals[:, ring_cols]
            m_neg = np.maximum(
                m_neg, np.max(np.where(m_neg_mask[:, ring_cols], vr, 0.0), axis=1)
            )
            m_mid = np.maximum(
                m_mid, np.max(np.where(m_mid_mask[:, ring_cols], vr, 0.0), axis=1)
            )
            m_pos = np.maximum(
                m_pos, np.max(np.where(m_pos_mask[:, ring_cols], vr, 0.0), axis=1)
            )
            # Symmetric combination across left/right flanking tubes preserves theta <-> theta + pi
            surv_2flank = (np.float32(1.0) - m_neg) * (np.float32(1.0) - m_pos)
            hit_prob = np.float32(1.0) - (np.float32(1.0) - m_mid) * surv_2flank
            acc += np.float32(_DW_LEVELS[r_idx]) * hit_prob

        out[s0:s1] = np.clip(acc, 0.0, 1.0)

    return out


def comonotonic_tube_self_credit(
    p_truth: np.ndarray,
    c2_strike: np.ndarray | None = None,
    s2_strike: np.ndarray | None = None,
    *,
    mask: np.ndarray | None = None,
    tube_halfwidth_px: float = 1.05,
) -> np.ndarray:
    """2-D grid wrapper for 3-strand Frechet-comonotonic tube-survival self-credit."""
    p = np.asarray(p_truth, dtype=np.float32)
    if p.ndim != 2:
        raise ValueError("p_truth must be a 2-D array")
    H, W = p.shape
    if mask is None:
        ys, xs = np.nonzero(np.ones((H, W), dtype=bool))
    else:
        ys, xs = np.nonzero(np.asarray(mask, dtype=bool))
    out = np.zeros((H, W), dtype=np.float32)
    if ys.size:
        out[ys, xs] = comonotonic_tube_self_credit_points(
            p,
            ys,
            xs,
            c2_strike,
            s2_strike,
            tube_halfwidth_px=tube_halfwidth_px,
        )
    return out


def _run_single_dinkelbach_celf_pass(
    p_truth: np.ndarray,
    ek_cand: np.ndarray,
    ks_cand: np.ndarray,
    cand_ys: np.ndarray,
    cand_xs: np.ndarray,
    *,
    lam: float,
    budget: int,
    min_spacing_px: float,
) -> tuple[np.ndarray, int, float, float, int]:
    """Exact Minoux (1978) lazy-greedy CELF pass for fixed Dinkelbach ratio ``lam``."""
    H, W = p_truth.shape
    lam_c = float(np.clip(lam, 0.0, 0.999))
    w_tp = 1.0 - ALPHA * lam_c
    w_fp = ALPHA * lam_c

    ub0 = w_tp * ek_cand - w_fp * (1.0 - ks_cand)
    ks_map: dict[tuple[int, int], float] = {}
    heap: list[tuple[float, int, int, int]] = []
    for i in range(cand_ys.size):
        yi = int(cand_ys[i])
        xi = int(cand_xs[i])
        ks_map[(yi, xi)] = float(ks_cand[i])
        heap.append((-float(ub0[i]), yi, xi, 0))
    heapq.heapify(heap)

    r_sp, disc = _spacing_disc(min_spacing_px)
    blocked = np.zeros((H + 2 * r_sp, W + 2 * r_sp), dtype=bool)
    cover = np.zeros((H, W), dtype=np.float32)
    dirty_epoch = np.zeros((H, W), dtype=np.int32)
    dots = np.zeros((H, W), dtype=bool)

    off_dy = OFF_DY
    off_dx = OFF_DX
    off_k = OFF_K.astype(np.float32)
    dirty_rad = 5

    n_dots = 0
    total_T = 0.0
    total_M = 0.0
    n_recomp = 0

    while n_dots < budget and heap:
        neg_ub, y, x, seen_ep = heapq.heappop(heap)
        if blocked[y + r_sp, x + r_sp]:
            continue
        cur_ep = int(dirty_epoch[y, x])
        ks_val = ks_map[(y, x)]
        if cur_ep != seen_ep:
            n_recomp += 1
            ny = y + off_dy
            nx = x + off_dx
            ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
            nyv = ny[ok]
            nxv = nx[ok]
            rem = np.maximum(off_k[ok] - cover[nyv, nxv], np.float32(0.0))
            dT = float(np.dot(p_truth[nyv, nxv], rem))
            if dT > 1e-12:
                g_val = w_tp * dT - w_fp * (1.0 - ks_val)
                heapq.heappush(heap, (-g_val, y, x, cur_ep))
            continue

        ny = y + off_dy
        nx = x + off_dx
        ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
        nyv = ny[ok]
        nxv = nx[ok]
        rem = np.maximum(off_k[ok] - cover[nyv, nxv], np.float32(0.0))
        dT_acc = float(np.dot(p_truth[nyv, nxv], rem))
        if dT_acc <= 1e-12:
            continue

        dots[y, x] = True
        n_dots += 1
        total_T += dT_acc
        total_M += ks_val
        blocked[y : y + 2 * r_sp + 1, x : x + 2 * r_sp + 1] |= disc
        np.maximum.at(cover, (nyv, nxv), off_k[ok])

        y0 = max(0, y - dirty_rad)
        y1 = min(H, y + dirty_rad + 1)
        x0 = max(0, x - dirty_rad)
        x1 = min(W, x + dirty_rad + 1)
        dirty_epoch[y0:y1, x0:x1] += 1

    return dots, n_dots, total_T, total_M, n_recomp


def comonotonic_dcelf_allocate_dots(
    surface: np.ndarray,
    allowed: np.ndarray,
    *,
    c2_strike: np.ndarray | None = None,
    s2_strike: np.ndarray | None = None,
    known_faults: np.ndarray | None = None,
    valid: np.ndarray | None = None,
    budget: int = 37654,
    min_spacing_px: float = 2.8,
    candidate_cap: int = 450_000,
    outer_iterations: int = 2,
    initial_lambda: float = 0.19,
    tube_halfwidth_px: float = 1.05,
) -> ComonotonicDCELFAllocation:
    """Allocate up to ``budget`` spacing-constrained dots via 3-Strand Frechet-Comonotonic
    Fault-Tube Survival Self-Credit + Dinkelbach Fractional-Programming CELF."""
    surf = np.asarray(surface, dtype=np.float32)
    allow = np.asarray(allowed, dtype=bool)
    if surf.shape != allow.shape or surf.ndim != 2:
        raise ValueError("surface and allowed must share a 2-D grid")
    if budget < 0 or outer_iterations < 1:
        raise ValueError("budget must be >= 0 and outer_iterations >= 1")
    H, W = surf.shape
    if budget == 0:
        return ComonotonicDCELFAllocation(
            np.zeros((H, W), dtype=bool), 0, 0.0, 0.0, 0.0, 0, 0, ()
        )

    valid_m = np.ones((H, W), dtype=bool) if valid is None else np.asarray(valid, dtype=bool)
    known_m = (
        np.zeros((H, W), dtype=bool)
        if known_faults is None
        else np.asarray(known_faults, dtype=bool)
    )
    active = valid_m & ~known_m
    p_truth = np.where(active, np.clip(surf, 0.0, 1.0), np.float32(0.0))

    ek0 = expected_credit(p_truth)
    cand_mask = allow & active & (ek0 > 1e-12)
    ys, xs = np.nonzero(cand_mask)
    if ys.size == 0:
        return ComonotonicDCELFAllocation(
            np.zeros((H, W), dtype=bool), 0, 0.0, 0.0, 0.0, 0, 0, ()
        )

    # Pre-filter candidate pool generously (2x cap) before exact continuous-angle tube evaluation
    pre_cap = min(ys.size, max(candidate_cap * 2, candidate_cap))
    if ys.size > pre_cap:
        order_pre = np.lexsort((xs, ys, -ek0[ys, xs].astype(np.float64)))[:pre_cap]
        ys = ys[order_pre]
        xs = xs[order_pre]

    ks_pts = comonotonic_tube_self_credit_points(
        p_truth,
        ys,
        xs,
        c2_strike,
        s2_strike,
        tube_halfwidth_px=tube_halfwidth_px,
    ).astype(np.float64)
    ek_pts = ek0[ys, xs].astype(np.float64)

    if ys.size > candidate_cap:
        init_score = (1.0 - ALPHA * initial_lambda) * ek_pts - ALPHA * initial_lambda * (
            1.0 - ks_pts
        )
        order = np.lexsort((xs, ys, -init_score))[:candidate_cap]
        ys = ys[order]
        xs = xs[order]
        ek_pts = ek_pts[order]
        ks_pts = ks_pts[order]

    n_expected_truth = max(float(p_truth[active].sum()), 2500.0)
    lam = float(np.clip(initial_lambda, 0.02, 0.85))
    lambdas: list[float] = []
    total_recomp = 0
    dots = np.zeros((H, W), dtype=bool)
    n_dots = 0
    total_T = 0.0
    total_M = 0.0

    for _ in range(outer_iterations):
        lambdas.append(lam)
        dots, n_dots, total_T, total_M, n_rec = _run_single_dinkelbach_celf_pass(
            p_truth,
            ek_pts,
            ks_pts,
            ys,
            xs,
            lam=lam,
            budget=budget,
            min_spacing_px=min_spacing_px,
        )
        total_recomp += n_rec
        denom = ALPHA * (total_T + float(n_dots) - total_M) + BETA * n_expected_truth + EPS
        lam = float(np.clip(total_T / denom, 0.02, 0.85))

    return ComonotonicDCELFAllocation(
        dots=dots,
        n_dots=n_dots,
        total_covered_credit=total_T,
        total_self_credit=total_M,
        final_lambda=lam,
        n_recomputations=total_recomp,
        n_candidates=int(ys.size),
        outer_lambdas=tuple(lambdas),
    )


def static_ek_spacing_allocate(
    surface: np.ndarray,
    allowed: np.ndarray,
    *,
    known_faults: np.ndarray | None = None,
    valid: np.ndarray | None = None,
    budget: int = 37654,
    min_spacing_px: float = 2.8,
    candidate_cap: int = 450_000,
) -> np.ndarray:
    """Controlled ablation allocator: static E[k] ranking with Poisson-disc spacing."""
    surf = np.asarray(surface, dtype=np.float32)
    allow = np.asarray(allowed, dtype=bool)
    H, W = surf.shape
    valid_m = np.ones((H, W), dtype=bool) if valid is None else np.asarray(valid, dtype=bool)
    known_m = (
        np.zeros((H, W), dtype=bool)
        if known_faults is None
        else np.asarray(known_faults, dtype=bool)
    )
    p_truth = np.where(valid_m & ~known_m, np.clip(surf, 0.0, 1.0), np.float32(0.0))
    ek0 = expected_credit(p_truth)
    ys, xs = np.nonzero(allow & valid_m & ~known_m & (ek0 > 1e-12))
    out = np.zeros((H, W), dtype=bool)
    if ys.size == 0 or budget <= 0:
        return out
    sc = ek0[ys, xs].astype(np.float64)
    order = np.lexsort((xs, ys, -sc))[:candidate_cap]
    ys = ys[order]
    xs = xs[order]
    r_sp, disc = _spacing_disc(min_spacing_px)
    blocked = np.zeros((H + 2 * r_sp, W + 2 * r_sp), dtype=bool)
    n = 0
    for i in range(ys.size):
        if n >= budget:
            break
        y = int(ys[i])
        x = int(xs[i])
        if blocked[y + r_sp, x + r_sp]:
            continue
        out[y, x] = True
        n += 1
        blocked[y : y + 2 * r_sp + 1, x : x + 2 * r_sp + 1] |= disc
    return out
