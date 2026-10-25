"""Exact O(N log N) Cost-Effective Lazy Forward (CELF, Minoux 1978) submodular
marginal-kernel-credit allocator on the official 300 m triangular DTI kernel."""

from __future__ import annotations

import heapq
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

VENDOR = Path(__file__).resolve().parents[2] / "vendor"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from gems57.emit import expected_credit
from gems57.metric import OFF_DX, OFF_DY, OFF_K


@dataclass(frozen=True)
class CELFAllocation:
    dots: np.ndarray
    n_dots: int
    total_marginal_credit: float
    n_recomputations: int
    n_candidates: int


def _spacing_disc(min_spacing_px: float) -> tuple[int, np.ndarray]:
    if min_spacing_px <= 0.0:
        return 0, np.ones((1, 1), dtype=bool)
    r = int(math.ceil(float(min_spacing_px)))
    yy, xx = np.ogrid[-r : r + 1, -r : r + 1]
    disc = (yy * yy + xx * xx) < float(min_spacing_px) ** 2
    return r, disc


def celf_allocate_dots(
    surface: np.ndarray,
    allowed: np.ndarray,
    *,
    known_faults: np.ndarray | None = None,
    valid: np.ndarray | None = None,
    budget: int = 37654,
    min_spacing_px: float = 2.8,
    candidate_cap: int = 450_000,
) -> CELFAllocation:
    """Maximize F(S) = sum_y p_truth(y) max_{s in S} k(||y - s||_2) subject to
    ||s - s'||_2 >= min_spacing_px and |S| <= budget via exact CELF lazy greedy.

    By submodularity of weighted max-coverage (Nemhauser, Wolsey & Fisher 1978;
    Minoux 1978), marginal gain dT(s | S) is monotonically non-increasing as S
    grows, so the priority-queue top element whose dirty epoch matches the
    local coverage grid is provably the exact global greedy maximizer at step t.
    """
    surf = np.asarray(surface, dtype=np.float32)
    allow = np.asarray(allowed, dtype=bool)
    if surf.shape != allow.shape or surf.ndim != 2:
        raise ValueError("surface and allowed must share a 2-D grid")
    if budget < 0:
        raise ValueError("budget must be non-negative")
    H, W = surf.shape
    if budget == 0:
        return CELFAllocation(np.zeros((H, W), dtype=bool), 0, 0.0, 0, 0)

    valid_m = np.ones((H, W), dtype=bool) if valid is None else np.asarray(valid, dtype=bool)
    known_m = (
        np.zeros((H, W), dtype=bool)
        if known_faults is None
        else np.asarray(known_faults, dtype=bool)
    )
    p_truth = np.where(valid_m & ~known_m, np.clip(surf, 0.0, 1.0), np.float32(0.0))

    ek0 = expected_credit(p_truth)
    cand_mask = allow & valid_m & ~known_m & (ek0 > 1e-12)
    ys, xs = np.nonzero(cand_mask)
    if ys.size == 0:
        return CELFAllocation(np.zeros((H, W), dtype=bool), 0, 0.0, 0, 0)

    scores0 = ek0[ys, xs].astype(np.float64)
    if ys.size > candidate_cap:
        # Deterministic top-candidate truncation with row-major tie breaking
        order = np.lexsort((xs, ys, -scores0))[:candidate_cap]
        ys = ys[order]
        xs = xs[order]
        scores0 = scores0[order]

    n_cand = int(ys.size)
    # Tuple (-marginal_upper_bound, y, x, seen_epoch): row-major deterministic ties
    heap: list[tuple[float, int, int, int]] = [
        (-float(scores0[i]), int(ys[i]), int(xs[i]), 0) for i in range(n_cand)
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
    # Two kernels of radius <3 px (max integer offset 2) overlap iff |dy|<=4 and |dx|<=4
    dirty_rad = 5

    n_dots = 0
    total_dT = 0.0
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
            kw = off_k[ok]
            rem = np.maximum(kw - cover[nyv, nxv], np.float32(0.0))
            dT = float(np.dot(p_truth[nyv, nxv], rem))
            if dT > 1e-12:
                heapq.heappush(heap, (-dT, y, x, cur_ep))
            continue

        dT_acc = -float(neg_ub)
        if dT_acc <= 1e-12:
            break
        dots[y, x] = True
        n_dots += 1
        total_dT += dT_acc
        blocked[y : y + 2 * r_sp + 1, x : x + 2 * r_sp + 1] |= disc

        ny = y + off_dy
        nx = x + off_dx
        ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
        nyv = ny[ok]
        nxv = nx[ok]
        np.maximum.at(cover, (nyv, nxv), off_k[ok])

        y0 = max(0, y - dirty_rad)
        y1 = min(H, y + dirty_rad + 1)
        x0 = max(0, x - dirty_rad)
        x1 = min(W, x + dirty_rad + 1)
        dirty_epoch[y0:y1, x0:x1] += 1

    return CELFAllocation(
        dots=dots,
        n_dots=n_dots,
        total_marginal_credit=float(total_dT),
        n_recomputations=int(n_recomp),
        n_candidates=n_cand,
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
    """Ablation control: static E[k] descending pass with min_spacing_px exclusion
    and NO submodular residual-coverage updates (matches H86G-EDTI allocator)."""
    surf = np.asarray(surface, dtype=np.float32)
    allow = np.asarray(allowed, dtype=bool)
    H, W = surf.shape
    if budget <= 0:
        return np.zeros((H, W), dtype=bool)
    valid_m = np.ones((H, W), dtype=bool) if valid is None else np.asarray(valid, dtype=bool)
    known_m = (
        np.zeros((H, W), dtype=bool)
        if known_faults is None
        else np.asarray(known_faults, dtype=bool)
    )
    p_truth = np.where(valid_m & ~known_m, np.clip(surf, 0.0, 1.0), np.float32(0.0))
    ek0 = expected_credit(p_truth)
    cand_mask = allow & valid_m & ~known_m & (ek0 > 1e-12)
    ys, xs = np.nonzero(cand_mask)
    if ys.size == 0:
        return np.zeros((H, W), dtype=bool)
    scores = ek0[ys, xs].astype(np.float64)
    order = np.lexsort((xs, ys, -scores))
    if order.size > candidate_cap:
        order = order[:candidate_cap]
    ys = ys[order]
    xs = xs[order]

    r_sp, disc = _spacing_disc(min_spacing_px)
    blocked = np.zeros((H + 2 * r_sp, W + 2 * r_sp), dtype=bool)
    dots = np.zeros((H, W), dtype=bool)
    n_dots = 0
    for i in range(ys.size):
        if n_dots >= budget:
            break
        y = int(ys[i])
        x = int(xs[i])
        if blocked[y + r_sp, x + r_sp]:
            continue
        dots[y, x] = True
        n_dots += 1
        blocked[y : y + 2 * r_sp + 1, x : x + 2 * r_sp + 1] |= disc
    return dots
