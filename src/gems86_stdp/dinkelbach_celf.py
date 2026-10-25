"""Exact 6-Ring Bernoulli Survival Supremum Self-Credit & Dinkelbach Fractional-Programming
CELF (Minoux 1978) Submodular Allocator on the Official 300 m Triangular DTI Kernel."""

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
class DinkelbachCELFAllocation:
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


def _grouped_kernel_rings() -> list[tuple[float, list[tuple[int, int]]]]:
    """Group positive OFF_K lattice offsets into descending radial-weight rings."""
    by_w: dict[float, list[tuple[int, int]]] = {}
    for dy, dx, kw in zip(OFF_DY.tolist(), OFF_DX.tolist(), OFF_K.tolist()):
        key = round(float(kw), 12)
        by_w.setdefault(key, []).append((int(dy), int(dx)))
    rings = sorted(by_w.items(), key=lambda kv: -kv[0])
    return [(float(w), offs) for w, offs in rings]


def exact_six_ring_self_credit(p_truth: np.ndarray) -> np.ndarray:
    """Compute E_{G ~ Bern(p)}[max_{||delta||_2 <= 3} G(y + delta) * K(delta)] exactly.

    By the non-negative tail-sum identity over the 6 distinct nonzero radial weights
    1 = w_1 > w_2 > ... > w_6 > w_7 := 0 of OFF_K:
      E[max_j G(y+d_j) K(d_j)] = sum_{r=1}^6 (w_r - w_{r+1}) * (1 - prod_{K(d_j) >= w_r} (1 - p(y+d_j))).
    Uses only two float32 (H, W) arrays (surv, out) and 29 slice multiplications.
    """
    p = np.clip(np.asarray(p_truth, dtype=np.float32), 0.0, 1.0)
    if p.ndim != 2:
        raise ValueError("p_truth must be a 2-D array")
    H, W = p.shape
    rings = _grouped_kernel_rings()
    surv = np.ones((H, W), dtype=np.float32)
    out = np.zeros((H, W), dtype=np.float32)

    for idx, (w_curr, offs) in enumerate(rings):
        w_next = rings[idx + 1][0] if idx + 1 < len(rings) else 0.0
        dw = np.float32(w_curr - w_next)
        for dy, dx in offs:
            # Target cell y receives neighbour y + (dy, dx)
            dst_y0, dst_y1 = max(0, -dy), min(H, H - dy)
            dst_x0, dst_x1 = max(0, -dx), min(W, W - dx)
            src_y0, src_y1 = dst_y0 + dy, dst_y1 + dy
            src_x0, src_x1 = dst_x0 + dx, dst_x1 + dx
            surv[dst_y0:dst_y1, dst_x0:dst_x1] *= (
                np.float32(1.0) - p[src_y0:src_y1, src_x0:src_x1]
            )
        out += dw * (np.float32(1.0) - surv)
    return np.clip(out, 0.0, 1.0)


def _run_single_dinkelbach_celf_pass(
    p_truth: np.ndarray,
    ek0: np.ndarray,
    k_self: np.ndarray,
    cand_ys: np.ndarray,
    cand_xs: np.ndarray,
    *,
    lam: float,
    budget: int,
    min_spacing_px: float,
) -> tuple[np.ndarray, int, float, float, int]:
    """Exact Minoux (1978) lazy-greedy CELF pass for fixed Dinkelbach ratio ``lam``.

    Maximizes sum_{t} [(1 - alpha * lam) * dT(y_t | S_{t-1}) - alpha * lam * (1 - k_self(y_t))].
    Because (1 - alpha * lam) > 0 for all lam in [0, 1] and the self-credit penalty is modular
    (independent of S), g_lam(y | S) is strictly non-increasing in S across all real values,
    preserving 100% lazy-heap optimality.
    """
    H, W = p_truth.shape
    lam_c = float(np.clip(lam, 0.0, 0.999))
    w_tp = 1.0 - ALPHA * lam_c
    w_fp = ALPHA * lam_c

    ek_c = ek0[cand_ys, cand_xs].astype(np.float64)
    ks_c = k_self[cand_ys, cand_xs].astype(np.float64)
    ub0 = w_tp * ek_c - w_fp * (1.0 - ks_c)

    heap: list[tuple[float, int, int, int]] = [
        (-float(ub0[i]), int(cand_ys[i]), int(cand_xs[i]), 0)
        for i in range(cand_ys.size)
    ]
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
                g_val = w_tp * dT - w_fp * (1.0 - float(k_self[y, x]))
                heapq.heappush(heap, (-g_val, y, x, cur_ep))
            continue

        # Accept exact greedy maximizer; verify positive marginal truth credit
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
        total_M += float(k_self[y, x])
        blocked[y : y + 2 * r_sp + 1, x : x + 2 * r_sp + 1] |= disc
        np.maximum.at(cover, (nyv, nxv), off_k[ok])

        y0 = max(0, y - dirty_rad)
        y1 = min(H, y + dirty_rad + 1)
        x0 = max(0, x - dirty_rad)
        x1 = min(W, x + dirty_rad + 1)
        dirty_epoch[y0:y1, x0:x1] += 1

    return dots, n_dots, total_T, total_M, n_recomp


def dinkelbach_celf_allocate_dots(
    surface: np.ndarray,
    allowed: np.ndarray,
    *,
    known_faults: np.ndarray | None = None,
    valid: np.ndarray | None = None,
    budget: int = 37654,
    min_spacing_px: float = 2.8,
    candidate_cap: int = 450_000,
    outer_iterations: int = 2,
    initial_lambda: float = 0.18,
) -> DinkelbachCELFAllocation:
    """Allocate up to ``budget`` spacing-constrained dots via Dinkelbach Fractional CELF."""
    surf = np.asarray(surface, dtype=np.float32)
    allow = np.asarray(allowed, dtype=bool)
    if surf.shape != allow.shape or surf.ndim != 2:
        raise ValueError("surface and allowed must share a 2-D grid")
    if budget < 0 or outer_iterations < 1:
        raise ValueError("budget must be >= 0 and outer_iterations >= 1")
    H, W = surf.shape
    if budget == 0:
        return DinkelbachCELFAllocation(
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
    k_self = exact_six_ring_self_credit(p_truth)

    cand_mask = allow & active & (ek0 > 1e-12)
    ys, xs = np.nonzero(cand_mask)
    if ys.size == 0:
        return DinkelbachCELFAllocation(
            np.zeros((H, W), dtype=bool), 0, 0.0, 0.0, 0.0, 0, 0, ()
        )

    if ys.size > candidate_cap:
        # Rank candidate pool by initial Lagrangian score with row-major tie breaking
        init_score = (1.0 - ALPHA * initial_lambda) * ek0[ys, xs].astype(
            np.float64
        ) - ALPHA * initial_lambda * (1.0 - k_self[ys, xs].astype(np.float64))
        order = np.lexsort((xs, ys, -init_score))[:candidate_cap]
        ys = ys[order]
        xs = xs[order]

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
            ek0,
            k_self,
            ys,
            xs,
            lam=lam,
            budget=budget,
            min_spacing_px=min_spacing_px,
        )
        total_recomp += n_rec
        denom = ALPHA * (total_T + float(n_dots) - total_M) + BETA * n_expected_truth + EPS
        lam = float(np.clip(total_T / denom, 0.02, 0.85))

    return DinkelbachCELFAllocation(
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
