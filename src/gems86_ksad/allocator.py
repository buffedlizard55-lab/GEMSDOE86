"""Elkan (2001) Bayes subsampling recalibration and Minoux-exact Dinkelbach
Submodular K3-Supremum Expected-DTI Allocation for Lane H86I-KSAD.
"""
from __future__ import annotations

import heapq
import numpy as np

from gems57 import metric


def elkan_bayes_recalibrate(
    prob_raw: np.ndarray,
    neg_subsample_ratio: float,
    valid: np.ndarray | None = None,
) -> np.ndarray:
    """Correct case-control / negative-subsampled probabilities to true prior odds.

    When negatives are subsampled by factor ``r = N_neg_pool / N_neg_sampled >= 1``,
    Bayes' theorem gives ``p_true = p_raw / (p_raw + r * (1 - p_raw))``.
    """
    r = max(float(neg_subsample_ratio), 1e-6)
    p = np.clip(np.asarray(prob_raw, dtype=np.float32), 0.0, 1.0 - 1e-7)
    denom = p + r * (1.0 - p)
    cal = np.divide(p, denom, out=np.zeros_like(p), where=denom > 0.0)
    if valid is not None:
        cal = np.where(valid, cal, 0.0)
    return cal.astype(np.float32)


def expected_self_credit_k3(
    prob_bayes: np.ndarray,
    radius_px: float = metric.RADIUS_PX,
) -> np.ndarray:
    """Noisy-OR expected self-credit ``M_hat(x) = 1 - prod_{||d||<=R} (1 - k(d)*p(x+d))``."""
    p = np.clip(np.asarray(prob_bayes, dtype=np.float32), 0.0, 0.999999)
    h, w = p.shape
    r = int(np.ceil(radius_px))
    dy, dx, kw = metric.offsets(radius_px)
    p_pad = np.zeros((h + 2 * r, w + 2 * r), dtype=np.float32)
    p_pad[r : r + h, r : r + w] = p
    log_miss = np.zeros((h, w), dtype=np.float32)
    for j, i, k in zip(dy, dx, kw):
        prod = np.clip(float(k) * p_pad[r + int(j) : r + int(j) + h, r + int(i) : r + int(i) + w], 0.0, 0.999999)
        log_miss += np.log1p(-prod)
    return (1.0 - np.exp(log_miss)).astype(np.float32)


def dinkelbach_submodular_k3_allocate(
    prob_bayes: np.ndarray,
    allowed: np.ndarray,
    *,
    budget_cap: int = 37654,
    lambda_dti: float = 0.17,
    min_sep_px: float = 2.4,
    alpha: float = metric.ALPHA,
    radius_px: float = metric.RADIUS_PX,
    max_candidates: int = 280000,
) -> np.ndarray:
    """Minoux (1978) lazy-greedy maximization of the monotone-submodular Dinkelbach
    expected-DTI objective:

        Delta Phi(x | S) = (1 - alpha*lambda*) * sum_{y} p(y) * max(0, K_R(x,y) - C_S(y))
                           - alpha * lambda* * (1 - M_hat(x))

    Stops when either ``|S| == budget_cap`` or ``max_x Delta Phi(x | S) <= 0``.
    """
    p = np.clip(np.asarray(prob_bayes, dtype=np.float32), 0.0, 1.0)
    allow = np.asarray(allowed, dtype=bool)
    if p.shape != allow.shape:
        raise ValueError("prob_bayes and allowed shape mismatch")
    h, w = p.shape
    out = np.zeros((h, w), dtype=bool)
    if budget_cap <= 0 or not allow.any():
        return out

    r = int(np.ceil(max(radius_px, min_sep_px))) + 1
    hp, wp = h + 2 * r, w + 2 * r
    dy, dx, kw_f64 = metric.offsets(radius_px)
    kw = kw_f64.astype(np.float32)
    kern_offs = np.array([int(j) * wp + int(i) for j, i in zip(dy, dx)], dtype=np.int64)

    sep_list = []
    if min_sep_px > 0.0:
        sr = int(np.ceil(min_sep_px))
        s2 = float(min_sep_px) * float(min_sep_px)
        for j in range(-sr, sr + 1):
            for i in range(-sr, sr + 1):
                if j * j + i * i < s2:
                    sep_list.append(j * wp + i)
    sep_offs = np.array(sep_list, dtype=np.int64)

    p_pad = np.zeros(hp * wp, dtype=np.float32)
    p_pad_2d = p_pad.reshape(hp, wp)
    p_pad_2d[r : r + h, r : r + w] = p

    g0 = np.zeros((h, w), dtype=np.float32)
    for j, i, k in zip(dy, dx, kw):
        g0 += float(k) * p_pad_2d[r + int(j) : r + int(j) + h, r + int(i) : r + int(i) + w]

    m_hat = expected_self_credit_k3(p, radius_px=radius_px)
    w_t = float(1.0 - alpha * lambda_dti)
    fp_cost = (float(alpha * lambda_dti) * (1.0 - m_hat)).astype(np.float32)
    phi0 = w_t * g0 - fp_cost

    cand_mask = allow & (phi0 > 0.0)
    cand_flat = np.flatnonzero(cand_mask.ravel())
    if cand_flat.size == 0:
        return out

    phi0_flat = phi0.ravel()[cand_flat]
    if cand_flat.size > max_candidates:
        keep = np.argpartition(-phi0_flat, max_candidates)[:max_candidates]
        cand_flat = cand_flat[keep]
        phi0_flat = phi0_flat[keep]

    ys, xs = np.divmod(cand_flat, w)
    pad_idx = (ys + r) * wp + (xs + r)
    fp_cand = fp_cost.ravel()[cand_flat]

    # Deterministic tie-break using candidate flat index
    heap: list[tuple[float, int, int, float]] = [
        (-float(ub), int(fi), int(pi), float(fpc))
        for ub, fi, pi, fpc in zip(phi0_flat, cand_flat, pad_idx, fp_cand)
    ]
    heapq.heapify(heap)

    cov = np.zeros(hp * wp, dtype=np.float32)
    blocked = np.zeros(hp * wp, dtype=bool)
    picked: list[int] = []

    while heap and len(picked) < budget_cap:
        neg_ub, fi, pi, fpc = heapq.heappop(heap)
        if blocked[pi]:
            continue
        nbr = pi + kern_offs
        rem = kw - cov[nbr]
        np.maximum(rem, 0.0, out=rem)
        gain_phi = w_t * float(np.dot(p_pad[nbr], rem)) - fpc
        if gain_phi <= 0.0:
            continue
        if heap and -gain_phi > heap[0][0] + 1e-7:
            heapq.heappush(heap, (-gain_phi, fi, pi, fpc))
            continue
        picked.append(fi)
        cov[nbr] = np.maximum(cov[nbr], kw)
        if sep_offs.size:
            blocked[pi + sep_offs] = True
        else:
            blocked[pi] = True

    if picked:
        out.ravel()[np.asarray(picked, dtype=np.int64)] = True
    return out


def pointwise_disc_thin(
    score: np.ndarray,
    allowed: np.ndarray,
    *,
    budget: int = 37654,
    spacing_px: float = 2.8,
    max_candidates: int = 400000,
) -> np.ndarray:
    """Standard deterministic greedy Poisson-disc thinner (used for Arm E2 & controls)."""
    s = np.asarray(score, dtype=np.float32)
    allow = np.asarray(allowed, dtype=bool) & np.isfinite(s) & (s > 0.0)
    h, w = s.shape
    out = np.zeros((h, w), dtype=bool)
    if budget <= 0 or not allow.any():
        return out
    flat = np.flatnonzero(allow.ravel())
    vals = s.ravel()[flat]
    if flat.size > max_candidates:
        keep = np.argpartition(-vals, max_candidates)[:max_candidates]
        flat = flat[keep]
        vals = vals[keep]
    # Deterministic sort: descending score, ascending flat index
    order = np.lexsort((flat, -vals))
    flat = flat[order]

    rad = int(np.ceil(spacing_px))
    hp, wp = h + 2 * rad, w + 2 * rad
    s2 = float(spacing_px) * float(spacing_px)
    offs = np.array(
        [j * wp + i for j in range(-rad, rad + 1) for i in range(-rad, rad + 1) if j * j + i * i < s2],
        dtype=np.int64,
    )
    blocked = np.zeros(hp * wp, dtype=bool)
    ys, xs = np.divmod(flat, w)
    pad_idx = (ys + rad) * wp + (xs + rad)
    picked: list[int] = []
    for fi, pi in zip(flat.tolist(), pad_idx.tolist()):
        if blocked[pi]:
            continue
        picked.append(fi)
        blocked[pi + offs] = True
        if len(picked) >= budget:
            break
    if picked:
        out.ravel()[np.asarray(picked, dtype=np.int64)] = True
    return out
