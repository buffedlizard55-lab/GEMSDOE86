"""Live (full-catalogue) fitting and posterior sharpening for the G86 lane."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import convolve
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

COLLAR_PX = 3


def build_posterior(stack: dict[str, np.ndarray], catalogue: np.ndarray, allowed: np.ndarray,
                    *, prior: float, footprint: np.ndarray | None = None,
                    suppress_px: int = 0, n_neg: int = 300_000,
                    seed: int = 7) -> np.ndarray:
    """Fit on ``catalogue`` positives; return the prior-corrected posterior field.

    The posterior is *not* masked to ``allowed`` -- exactly as in the validated
    fold path, where ``allowed`` only restricts where the allocator may put a
    dot.  Masking the posterior first would remove the catalogue-flank mass that
    the expected-credit convolution needs, and the emission would no longer be
    the one that was validated (measured: holdout DTI 0.0002 instead of 0.1210).
    """
    from scipy import ndimage as ndi
    names = list(stack)
    pos = np.asarray(catalogue, bool)
    dcat = ndi.distance_transform_edt(~pos).astype(np.float32)
    neg_pool = np.asarray(allowed, bool) & (dcat > COLLAR_PX)
    rng = np.random.default_rng(seed)
    py, px = np.nonzero(pos)
    ny, nx = np.nonzero(neg_pool)
    if ny.size > n_neg:
        sel = rng.choice(ny.size, n_neg, replace=False)
        ny, nx = ny[sel], nx[sel]
    Xp = np.stack([np.asarray(stack[k][py, px], np.float32) for k in names], -1)
    Xn = np.stack([np.asarray(stack[k][ny, nx], np.float32) for k in names], -1)
    X = np.concatenate([Xp, Xn])
    y = np.concatenate([np.ones(len(Xp)), np.zeros(len(Xn))])
    del Xp, Xn
    sc = StandardScaler().fit(X)
    clf = LogisticRegression(C=0.5, class_weight="balanced", max_iter=300).fit(sc.transform(X), y)
    del X, y
    offset = float(np.log(prior / (1.0 - prior)))
    p = np.zeros(allowed.shape, np.float32)
    H, W = p.shape
    for r0 in range(0, H, 512):
        r1 = min(H, r0 + 512)
        block = np.stack([np.asarray(stack[k][r0:r1], np.float32) for k in names], -1)
        z = clf.decision_function(sc.transform(block.reshape(-1, len(names)))) + offset
        p[r0:r1] = (1.0 / (1.0 + np.exp(-z))).reshape(r1 - r0, W)
    if footprint is not None:
        p[~np.asarray(footprint, bool)] = 0.0
    if suppress_px > 0:
        # Off-catalogue lane: remove the catalogue-flank mass so that the
        # expected-credit convolution cannot be driven by proximity to a mapped
        # trace.  This is what makes the emission arrangement distinct from the
        # fleet's proximity lanes (see evidence/uniqueness_audit.json).
        near = ndi.distance_transform_edt(~pos) <= float(suppress_px)
        p[near] = 0.0
    return p


# Backwards-compatible alias used by scripts/build_submission.py.
fit_full = build_posterior


def oriented_kernels(sig_par: float = 4.0, sig_perp: float = 1.2, half: int = 9,
                     nang: int = 8) -> list[np.ndarray]:
    """Zero-mean anisotropic Gaussian kernels over 8 orientations (matched line filter)."""
    yy, xx = np.mgrid[-half:half + 1, -half:half + 1].astype(np.float32)
    out = []
    for i in range(nang):
        th = np.pi * i / nang
        u = xx * np.cos(th) + yy * np.sin(th)
        v = -xx * np.sin(th) + yy * np.cos(th)
        k = np.exp(-(u * u / (2 * sig_par ** 2) + v * v / (2 * sig_perp ** 2)))
        k -= k.mean()
        k /= (np.abs(k).sum() + 1e-9)
        out.append(k.astype(np.float32))
    return out


def line_filter(p: np.ndarray, **kw) -> np.ndarray:
    """Max response over orientations: keeps linear, along-strike coherent support."""
    m = np.zeros_like(p)
    for k in oriented_kernels(**kw):
        np.maximum(m, convolve(p, k, mode="constant"), out=m)
    np.clip(m, 0.0, None, out=m)
    return m
