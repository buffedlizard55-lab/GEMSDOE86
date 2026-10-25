"""Minoux-accelerated lazy-greedy submodular 300 m kernel allocator & PU calibrator.

Reuses the exact 300 m triangular kernel ``(OFF_DY, OFF_DX, OFF_K)`` and
``expected_credit`` operator from unchanged ``vendor/gems57/{metric,emit}.py``.
"""
from __future__ import annotations

import heapq
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems57.emit import expected_credit  # noqa: E402
from gems57.metric import OFF_DX, OFF_DY, OFF_K  # noqa: E402


def bayes_prior_calibrate(
    q_prob: np.ndarray,
    pi_train: float,
    pi_target: float,
    footprint: np.ndarray,
) -> np.ndarray:
    """Exact Saerens-Latinne-Decaestecker Bayes prior-shift calibration.

    Transforms subsample training posterior ``q(x) = P_tr(y=1 | x)`` with class
    balance ``pi_train`` into spatial prevalence posterior ``p_cal(x)`` matching
    hidden-fault prevalence ``pi_target`` inside ``footprint``.
    """
    fp = np.asarray(footprint, dtype=bool)
    pi_tr = float(np.clip(pi_train, 1e-5, 1.0 - 1e-5))
    pi_tg = float(np.clip(pi_target, 1e-6, 0.5))
    gamma = (pi_tg * (1.0 - pi_tr)) / ((1.0 - pi_tg) * pi_tr)

    out = np.zeros(fp.shape, dtype=np.float32)
    q = np.clip(np.asarray(q_prob[fp], dtype=np.float64), 1e-6, 1.0 - 1e-6)
    odds = gamma * (q / (1.0 - q))
    out[fp] = (odds / (1.0 + odds)).astype(np.float32)
    return out


def submodular_kernel_allocate(
    p_cal: np.ndarray,
    allowed: np.ndarray,
    budget: int,
    *,
    eta: float = 0.042,
    candidate_cap: int = 320_000,
) -> np.ndarray:
    """Exact Minoux lazy-greedy maximization of linearized Dinkelbach DTI coverage.

    Maximizes the monotone submodular objective at fixed cardinality ``budget``::

        F(S) = sum_u p_cal(u) * max_{x in S} k(||x - u||) + eta * sum_{x in S} k_self(x)

    where ``k(d) = max(1 - d/3, 0)`` is the official 300 m triangular kernel from
    ``vendor/gems57/metric.py`` and ``k_self(x) = min(E[k](x), 1)``. Because
    ``dT(x | S)`` is monotone submodular and ``eta * k_self(x) >= 0`` is modular,
    ``F(S)`` is strictly monotone submodular, so lazy priority-queue evaluation
    returns the exact greedy sequence in ~3 s on the 3730x3292 competition grid.
    """
    p = np.asarray(p_cal, dtype=np.float32)
    alw = np.asarray(allowed, dtype=bool)
    if p.shape != alw.shape:
        raise ValueError(f"shape mismatch: {p.shape} vs {alw.shape}")
    if budget <= 0 or not alw.any():
        return np.zeros(p.shape, dtype=bool)

    h, w = p.shape
    ek = expected_credit(p)
    flat_alw = np.flatnonzero(alw.ravel())
    if flat_alw.size == 0:
        return np.zeros(p.shape, dtype=bool)

    cap = min(int(candidate_cap), int(flat_alw.size))
    cap = max(cap, min(int(budget), int(flat_alw.size)))
    ek_alw = ek.ravel()[flat_alw]
    if cap < flat_alw.size:
        part = np.argpartition(-ek_alw, cap - 1)[:cap]
        cand_flat = flat_alw[part]
    else:
        cand_flat = flat_alw

    kself_all = np.minimum(ek.ravel()[cand_flat].astype(np.float64), 1.0)
    init_gain = ek.ravel()[cand_flat].astype(np.float64) + float(eta) * kself_all
    order = np.argsort(-init_gain, kind="stable")
    cand_flat = cand_flat[order]
    kself = kself_all[order]
    init_gain = init_gain[order]
    del ek, ek_alw, flat_alw, kself_all, order

    ys = (cand_flat // w).astype(np.int32)
    xs = (cand_flat % w).astype(np.int32)
    n_cand = int(cand_flat.size)
    del cand_flat

    cid_grid = np.full((h, w), -1, dtype=np.int32)
    cid_grid[ys, xs] = np.arange(n_cand, dtype=np.int32)

    cover = np.zeros((h, w), dtype=np.float32)
    dots = np.zeros((h, w), dtype=bool)
    dirty = np.zeros(n_cand, dtype=bool)

    # Tie-break by initial rank index `i` for deterministic selection.
    heap: list[tuple[float, int]] = [(-float(init_gain[i]), i) for i in range(n_cand)]
    heapq.heapify(heap)
    del init_gain

    eta_f = float(eta)
    emitted = 0
    target = min(int(budget), n_cand)
    while emitted < target and heap:
        neg_val, i = heapq.heappop(heap)
        y = int(ys[i])
        x = int(xs[i])
        if dots[y, x]:
            continue
        if dirty[i]:
            ny = y + OFF_DY
            nx = x + OFF_DX
            ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
            nyv, nxv, kw = ny[ok], nx[ok], OFF_K[ok]
            dT = float((p[nyv, nxv] * np.maximum(kw - cover[nyv, nxv], 0.0)).sum())
            gain = dT + eta_f * float(kself[i])
            dirty[i] = False
            heapq.heappush(heap, (-gain, i))
            continue

        dots[y, x] = True
        emitted += 1
        ny = y + OFF_DY
        nx = x + OFF_DX
        ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        nyv, nxv, kw = ny[ok], nx[ok], OFF_K[ok]
        np.maximum.at(cover, (nyv, nxv), kw.astype(np.float32))

        # Two 3 px kernels overlap only if |dy| <= 4 and |dx| <= 4 (hypot < 6.0).
        y0, y1 = max(0, y - 5), min(h, y + 6)
        x0, x1 = max(0, x - 5), min(w, x + 6)
        sub = cid_grid[y0:y1, x0:x1].ravel()
        valid_c = sub[sub >= 0]
        dirty[valid_c] = True

    return dots


def disc_thin(
    score: np.ndarray,
    allowed: np.ndarray,
    budget: int,
    spacing: float = 2.8,
) -> np.ndarray:
    """Deterministic greedy Poisson-disc thinning control (for Ablation Arm E3)."""
    r = int(np.ceil(spacing))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disc = (yy * yy + xx * xx) < (spacing * spacing)
    h, w = score.shape
    blocked = np.zeros((h + 2 * r, w + 2 * r), dtype=bool)
    flat = np.flatnonzero(allowed.ravel())
    order = flat[np.argsort(-score.ravel()[flat], kind="stable")]
    dots = np.zeros(score.shape, dtype=bool)
    emitted = 0
    for f_idx in order:
        y, x = divmod(int(f_idx), w)
        if blocked[y + r, x + r]:
            continue
        dots[y, x] = True
        blocked[y:y + 2 * r + 1, x:x + 2 * r + 1] |= disc
        emitted += 1
        if emitted >= budget:
            break
    return dots
