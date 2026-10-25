"""Fold-safe geophysical surfaces for the H86L lane.

Frozen before any holdout score (see research/H86L_VFGR_PREREGISTRATION.md):

* ``SIGMA_EDGE_PX = 2.0`` — expected magnetic/gravity edge width around a
  visible fault (200 m). Not tuned on holdout.
* ``COH_SIGMA_PX = 1.5`` — structure-tensor smoothing.
* ``BMR_SMOOTH_PX = 8.0`` — basement-relief wavelength removed before the
  gravity residual (800 m).
* Percentile clip ``(2, 98)`` is computed on the training mask only.

Catalogue geometry enters only through the caller-supplied visible-fault
distance. Withheld faults must already be absent from that mask.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

SIGMA_EDGE_PX = 2.0
COH_SIGMA_PX = 1.5
BMR_SMOOTH_PX = 8.0
PERCENTILE = (2.0, 98.0)


def _train_percentiles(values: np.ndarray, train: np.ndarray) -> tuple[float, float]:
    sample = values[train]
    if sample.size < 100:
        raise ValueError("training mask is too small to set a frozen percentile scale")
    lo, hi = np.percentile(sample, PERCENTILE)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        raise ValueError("training percentile scale is degenerate")
    return float(lo), float(hi)


def robust_unit(values: np.ndarray, train: np.ndarray) -> np.ndarray:
    """Map ``values`` to [0, 1] using training-mask percentiles only."""
    lo, hi = _train_percentiles(values, train)
    return np.clip((values - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def structure_coherence(field: np.ndarray, sigma: float = COH_SIGMA_PX) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(coherence, gradient magnitude)`` of a 2-D field.

    Coherence is ``(λ1 − λ2) / (λ1 + λ2)`` of the Gaussian-smoothed structure
    tensor. It is 1 on a single-orientation edge and 0 on isotropic texture.
    """
    gy, gx = np.gradient(np.asarray(field, dtype=np.float64))
    gxx = ndi.gaussian_filter(gx * gx, sigma)
    gyy = ndi.gaussian_filter(gy * gy, sigma)
    gxy = ndi.gaussian_filter(gx * gy, sigma)
    trace = gxx + gyy
    det = gxx * gyy - gxy * gxy
    disc = np.sqrt(np.maximum(trace * trace - 4.0 * det, 0.0))
    lam1 = 0.5 * (trace + disc)
    lam2 = 0.5 * (trace - disc)
    coh = (lam1 - lam2) / (lam1 + lam2 + 1e-12)
    mag = np.sqrt(np.maximum(lam1, 0.0))
    return coh.astype(np.float32), mag.astype(np.float32)


def expected_edge_weight(distance_px: np.ndarray, sigma: float = SIGMA_EDGE_PX) -> np.ndarray:
    """Gaussian expected-edge profile of a visible fault, in pixels."""
    d = np.asarray(distance_px, dtype=np.float64)
    return np.exp(-0.5 * (d / float(sigma)) ** 2).astype(np.float32)


def fit_edge_residual(edge: np.ndarray, distance_px: np.ndarray, train: np.ndarray,
                      sigma: float = SIGMA_EDGE_PX) -> tuple[np.ndarray, float]:
    """Subtract a visible-fault expected edge fit on ``train`` only.

    Model: ``edge ≈ a * exp(-d² / 2σ²)``, ``a >= 0`` frozen from training
    pixels where the weight exceeds 0.05. The residual is ``relu(edge - a w)``.
    A withheld fault must not be inside ``train``'s visible-fault distance.
    """
    edge = np.asarray(edge, dtype=np.float64)
    weight = expected_edge_weight(distance_px, sigma).astype(np.float64)
    mask = np.asarray(train, dtype=bool) & (weight > 0.05) & np.isfinite(edge)
    if int(mask.sum()) < 100:
        raise ValueError("not enough training pixels to fit the expected edge")
    ww = weight[mask]
    ee = edge[mask]
    scale = float(np.dot(ww, ee) / (np.dot(ww, ww) + 1e-12))
    scale = max(scale, 0.0)
    residual = np.maximum(edge - scale * weight, 0.0)
    return residual.astype(np.float32), scale


def corroborated_residual_surface(mag_edge: np.ndarray, grav_edge: np.ndarray,
                                  distance_px: np.ndarray, train: np.ndarray, footprint: np.ndarray,
                                  *, subtract: bool) -> tuple[np.ndarray, dict]:
    """Geometric-mean residual edge gated by structure-tensor coherence.

    ``subtract=False`` is the raw-edge control: the same coherence operator and
    the same emitter, with the expected-edge term forced to zero.
    """
    train = np.asarray(train, dtype=bool) & np.asarray(footprint, dtype=bool)
    mag_u = robust_unit(mag_edge, train)
    grav_u = robust_unit(grav_edge, train)
    if subtract:
        mag_r, a_mag = fit_edge_residual(mag_u, distance_px, train)
        grav_r, a_grav = fit_edge_residual(grav_u, distance_px, train)
    else:
        mag_r, grav_r = mag_u, grav_u
        a_mag = a_grav = 0.0
    coh_m, _ = structure_coherence(mag_r)
    coh_g, _ = structure_coherence(grav_r)
    raw = np.sqrt(np.clip(mag_r, 0, None) * np.clip(grav_r, 0, None)) * (0.5 * (coh_m + coh_g))
    surface = robust_unit(raw, train)
    surface = np.where(footprint, surface, 0.0).astype(np.float32)
    return surface, {"a_mag": a_mag, "a_grav": a_grav, "subtract": bool(subtract)}


def basement_mass_balance_surface(gravity: np.ndarray, depth: np.ndarray,
                                  train: np.ndarray, footprint: np.ndarray,
                                  sigma: float = BMR_SMOOTH_PX) -> tuple[np.ndarray, dict]:
    """Residual gravity after a training-only linear basement-slab term.

    ``gravity ≈ a + b * smooth(depth)`` is fit by ordinary least squares on
    ``train`` only. The published physical claim is the coherent gradient of
    ``gravity - (a + b * smooth(depth))``, not the raw anomaly and not the
    basement surface itself.
    """
    train = np.asarray(train, dtype=bool) & np.asarray(footprint, dtype=bool)
    if int(train.sum()) < 100:
        raise ValueError("training mask is too small for the basement fit")
    depth_s = ndi.gaussian_filter(np.asarray(depth, dtype=np.float64), sigma)
    g = np.asarray(gravity, dtype=np.float64)
    x = depth_s[train]
    y = g[train]
    x_mean = float(x.mean())
    y_mean = float(y.mean())
    var = float(np.dot(x - x_mean, x - x_mean))
    if var <= 0.0:
        raise ValueError("basement depth has no training variance")
    slope = float(np.dot(x - x_mean, y - y_mean) / var)
    intercept = y_mean - slope * x_mean
    residual = g - (intercept + slope * depth_s)
    coh, mag = structure_coherence(residual.astype(np.float32))
    raw = coh * mag
    surface = robust_unit(raw, train)
    surface = np.where(footprint, surface, 0.0).astype(np.float32)
    y_hat = intercept + slope * x
    ss_tot = float(np.dot(y - y_mean, y - y_mean))
    ss_res = float(np.dot(y - y_hat, y - y_hat))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return surface, {
        "intercept": intercept,
        "slope": slope,
        "training_r2": r2,
        "smooth_sigma_px": sigma,
    }
