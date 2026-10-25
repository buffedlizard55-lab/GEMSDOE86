"""Exact 300 m triangular-kernel submodular expected-TP_w dot allocation (Minoux 1978).

At a fixed dot budget K, maximizing expected DTI under calibrated fault-presence
weights q(v) >= 0 reduces to monotone submodular weighted max-cover under the
exact competition kernel K_3(d) = max(0, 1 - d / 3) for d < 3 px imported from
`vendor/gems57/metric.py` (`OFF_DY`, `OFF_DX`, `OFF_K`).
"""
from __future__ import annotations

import heapq
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import metric  # noqa: E402


def submodular_kernel_allocate(
    prob: np.ndarray,
    allowed: np.ndarray,
    budget: int = 37654,
    gamma: float = 1.30,
    candidate_pool_mult: int = 10,
) -> np.ndarray:
    """Select `budget` unit dots maximizing sum_v q(v) * max_{u in S} K_3(||u - v||).

    Uses Minoux (1978) accelerated lazy greedy updates on a 3-px zero-padded
    coverage plane so every 29-point kernel evaluation is bounds-check-free.
    """
    h, w = prob.shape
    if budget <= 0:
        return np.zeros((h, w), dtype=np.float32)

    q = np.zeros((h, w), dtype=np.float32)
    mask = allowed & np.isfinite(prob) & (prob > 0.0)
    if not np.any(mask):
        return np.zeros((h, w), dtype=np.float32)
    q[mask] = np.power(np.clip(prob[mask], 0.0, 1.0), np.float32(gamma))

    # Exact initial marginal gain G_0(u) = sum_j q(u + delta_j) * k_j via 2D correlation
    pad = int(metric.RADIUS_PX)  # 3 px
    ker = np.zeros((2 * pad + 1, 2 * pad + 1), dtype=np.float32)
    for dy, dx, kv in zip(metric.OFF_DY, metric.OFF_DX, metric.OFF_K):
        ker[int(dy) + pad, int(dx) + pad] = float(kv)
    init_gain = ndi.correlate(q, ker, mode="constant", cval=0.0)
    init_gain[~allowed] = -1.0

    valid_flat = np.flatnonzero(init_gain > 0.0)
    if valid_flat.size == 0:
        return np.zeros((h, w), dtype=np.float32)

    pool_n = min(valid_flat.size, max(budget * candidate_pool_mult, budget))
    if valid_flat.size > pool_n:
        gains_valid = init_gain.ravel()[valid_flat]
        part = np.argpartition(gains_valid, -pool_n)[-pool_n:]
        cand_flat = valid_flat[part]
    else:
        cand_flat = valid_flat

    # Padded planes (h + 2*pad, w + 2*pad) for branch-free flat indexing
    wp = w + 2 * pad
    q_pad = np.zeros((h + 2 * pad, wp), dtype=np.float32)
    q_pad[pad : pad + h, pad : pad + w] = q
    q_flat = q_pad.ravel()
    cov_flat = np.zeros_like(q_flat)

    off_strides = (
        metric.OFF_DY.astype(np.int64) * wp + metric.OFF_DX.astype(np.int64)
    )
    off_k = metric.OFF_K.astype(np.float32)

    cand_rows = cand_flat // w
    cand_cols = cand_flat % w
    cand_pad_idx = (cand_rows + pad) * wp + (cand_cols + pad)
    cand_gains = init_gain.ravel()[cand_flat]

    # Max-heap via (-gain, tie_break_flat_idx, padded_flat_idx)
    heap: list[tuple[float, int, int]] = [
        (-float(g_val), int(f_idx), int(p_idx))
        for g_val, f_idx, p_idx in zip(cand_gains, cand_flat, cand_pad_idx)
    ]
    heapq.heapify(heap)

    out_flat = np.zeros(h * w, dtype=np.float32)
    selected = 0

    while selected < budget and heap:
        neg_g, f_idx, p_idx = heapq.heappop(heap)
        nbr = p_idx + off_strides
        inc = off_k - cov_flat[nbr]
        # Fast inline marginal gain
        pos = inc > 0.0
        recomputed = float(np.dot(q_flat[nbr[pos]], inc[pos])) if np.any(pos) else 0.0
        if not heap or recomputed >= -heap[0][0] - 1e-9:
            if recomputed <= 0.0:
                break
            out_flat[f_idx] = 1.0
            cov_flat[nbr] = np.maximum(cov_flat[nbr], off_k)
            selected += 1
        elif recomputed > 0.0:
            heapq.heappush(heap, (-recomputed, f_idx, p_idx))

    return out_flat.reshape(h, w)
