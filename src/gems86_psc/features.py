"""H86K-PSC: persistent potential-field saddle-connector features.

For a smoothed field F, a saddle has Hessian eigenvalues of opposite sign
(det H < 0).  Saddle strength = sqrt(-det H) at pixels where det H < 0,
computed at sigma=1 and sigma=3 px; persistence = min(rank_s1, rank_s3),
gated by (1 - rank|grad F|) because a true saddle is a low-gradient pass
between highs/lows.  Surface = geometric mean of rtp and gravity saddle
persistence, multiplied by (0.5 + 0.5 * depth-saddle concordance rank).
Band 15 is gravity-derived: disclosed concordance, not independence.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi


def rank01(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros(a.shape, np.float32)
    v = a[mask].astype(np.float64)
    if v.size == 0 or np.ptp(v) == 0:
        return out
    order = np.argsort(v, kind="mergesort")
    r = np.empty(v.size, np.float32); r[order] = np.linspace(0, 1, v.size, dtype=np.float32)
    out[mask] = r
    return out


def _saddle_one(field: np.ndarray, mask: np.ndarray, sigma: float) -> np.ndarray:
    f = ndi.gaussian_filter(field, sigma, mode="nearest")
    gy, gx = np.gradient(f)
    gyy, gyx = np.gradient(gy); gxy, gxx = np.gradient(gx)
    det = gxx * gyy - gxy * gyx
    strength = np.where(det < 0, np.sqrt(np.maximum(-det, 0.0)), 0.0).astype(np.float32)
    grad = np.hypot(gx, gy).astype(np.float32)
    return rank01(strength, mask) * (1.0 - rank01(grad, mask))


def saddle_persistence(field: np.ndarray, mask: np.ndarray) -> np.ndarray:
    s1 = _saddle_one(field, mask, 1.0)
    s3 = _saddle_one(field, mask, 3.0)
    return np.minimum(s1, s3)


def gradient_ridge(field: np.ndarray, mask: np.ndarray) -> np.ndarray:
    f = ndi.gaussian_filter(field, 1.5, mode="nearest")
    gy, gx = np.gradient(f)
    return rank01(np.hypot(gx, gy).astype(np.float32), mask)


def build_surfaces(bands: dict[str, np.ndarray], mask: np.ndarray) -> dict[str, np.ndarray]:
    """bands keys: rtp, grav, depth. Returns named planes + E1/C1/C2 surfaces."""
    planes = {
        "saddle_rtp": saddle_persistence(bands["rtp"], mask),
        "saddle_grav": saddle_persistence(bands["grav"], mask),
        "saddle_depth": saddle_persistence(bands["depth"], mask),
        "ridge_rtp": gradient_ridge(bands["rtp"], mask),
        "ridge_grav": gradient_ridge(bands["grav"], mask),
    }
    geo = np.sqrt(np.clip(planes["saddle_rtp"], 0, 1) * np.clip(planes["saddle_grav"], 0, 1))
    planes["C2_psc_nodepth"] = geo.astype(np.float32)
    planes["E1_psc"] = (geo * (0.5 + 0.5 * planes["saddle_depth"])).astype(np.float32)
    planes["C1_ridge"] = np.sqrt(np.clip(planes["ridge_rtp"], 0, 1) * np.clip(planes["ridge_grav"], 0, 1)).astype(np.float32)
    return planes
