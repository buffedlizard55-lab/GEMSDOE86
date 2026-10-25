"""Pure numerical operators for Lane H86N-GSST (gravity step vs compact source).

Uses verified native band physics from src/gems86/io.py:
- Band 13 (iso_grav_anom): isostatic residual gravity anomaly g
- Band 5  (iso_grav_anom_slope): horizontal gravity gradient magnitude |grad_H g|
- Band 11 (iso_grav_anom_vg): signed southward gravity derivative +dg/drow_south
- Band 18 (iso_grav_anom_hg): signed eastward gravity derivative +dg/dcol_east
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata

NODATA = -3.4028234663852886e38


def clean_band(arr: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Replace non-finite and float32 NODATA sentinel pixels with valid footprint mean."""
    a = np.asarray(arr, dtype=np.float64).copy()
    valid = fp & np.isfinite(a) & (a > NODATA * 0.5)
    fill = float(np.mean(a[valid])) if np.any(valid) else 0.0
    a[~valid] = fill
    return a


def rankpct(arr: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Rank-percentile transform in (0, 1] inside the valid footprint."""
    out = np.zeros(arr.shape, dtype=np.float32)
    vals = np.asarray(arr[fp], dtype=np.float64)
    vals = np.nan_to_num(vals, nan=0.0, posinf=0.0, neginf=0.0)
    if vals.size == 0:
        return out
    ranks = rankdata(vals) / float(vals.size)
    out[fp] = ranks.astype(np.float32)
    return out


def _bilinear_sample(field: np.ndarray, y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Fast clipped bilinear interpolation at floating-point (y, x) coordinates."""
    h, w = field.shape
    yc = np.clip(y, 0.0, h - 1.0001)
    xc = np.clip(x, 0.0, w - 1.0001)
    y0 = yc.astype(np.int32)
    x0 = xc.astype(np.int32)
    y1 = np.minimum(y0 + 1, h - 1)
    x1 = np.minimum(x0 + 1, w - 1)
    wy = (yc - y0).astype(np.float32)
    wx = (xc - x0).astype(np.float32)
    f00 = field[y0, x0]
    f01 = field[y0, x1]
    f10 = field[y1, x0]
    f11 = field[y1, x1]
    return (
        (1.0 - wy) * ((1.0 - wx) * f00 + wx * f01)
        + wy * ((1.0 - wx) * f10 + wx * f11)
    ).astype(np.float32)


def gsst_scale_score(
    grav: np.ndarray,
    gx_east: np.ndarray,
    gy_south: np.ndarray,
    sigma: float,
) -> dict[str, np.ndarray]:
    """Compute step-vs-compact shape components at scale ``sigma`` (in pixels).

    Parameters
    ----------
    grav : 2-D array (Band 13 iso_grav_anom, cleaned)
    gx_east : 2-D array (Band 18 +dg/dx_east, cleaned)
    gy_south : 2-D array (Band 11 +dg/drow_south, cleaned)
    sigma : Gaussian smoothing & offset scale in pixels
    """
    ux = ndi.gaussian_filter(gx_east.astype(np.float64), sigma).astype(np.float32)
    uy = ndi.gaussian_filter(gy_south.astype(np.float64), sigma).astype(np.float32)
    gs = ndi.gaussian_filter(grav.astype(np.float64), max(1.0, 0.5 * sigma)).astype(np.float32)
    mag = np.hypot(ux.astype(np.float64), uy.astype(np.float64)).astype(np.float32)
    eps = np.float32(1e-6)
    nx = ux / (mag + eps)
    ny = uy / (mag + eps)
    # Unit strike tangent s = (-ny, nx)
    sx = -ny
    sy = nx

    h, w = grav.shape
    yy, xx = np.meshgrid(
        np.arange(h, dtype=np.float32),
        np.arange(w, dtype=np.float32),
        indexing="ij",
    )

    # 1. Cross-strike step monotonicity & flank gradient sign persistence at +/- sigma
    delta = float(sigma)
    ux_p = _bilinear_sample(ux, yy + delta * ny, xx + delta * nx)
    uy_p = _bilinear_sample(uy, yy + delta * ny, xx + delta * nx)
    ux_m = _bilinear_sample(ux, yy - delta * ny, xx - delta * nx)
    uy_m = _bilinear_sample(uy, yy - delta * ny, xx - delta * nx)

    gn_p = ux_p * nx + uy_p * ny
    gn_m = ux_m * nx + uy_m * ny
    # Normalized flank persistence: positive only when both flanks share the crest gradient sign
    flank_min = np.minimum(gn_p, gn_m) / (mag + eps)
    # Also verify actual potential drop g(x + delta*n) - g(x - delta*n) > 0
    g_p = _bilinear_sample(gs, yy + delta * ny, xx + delta * nx)
    g_m = _bilinear_sample(gs, yy - delta * ny, xx - delta * nx)
    step_drop = np.clip((g_p - g_m) / (2.0 * delta * mag + eps), 0.0, 1.5)
    step_persistence = np.clip(flank_min, 0.0, 1.0) * np.clip(step_drop, 0.0, 1.0)

    # 2. Along-strike extended coherence at +/- 1.5 * sigma vs compact radial curvature
    L_par = float(1.5 * sigma)
    ux_sp = _bilinear_sample(ux, yy + L_par * sy, xx + L_par * sx)
    uy_sp = _bilinear_sample(uy, yy + L_par * sy, xx + L_par * sx)
    ux_sm = _bilinear_sample(ux, yy - L_par * sy, xx - L_par * sx)
    uy_sm = _bilinear_sample(uy, yy - L_par * sy, xx - L_par * sx)
    gn_sp = (ux_sp * nx + uy_sp * ny) / (mag + eps)
    gn_sm = (ux_sm * nx + uy_sm * ny) / (mag + eps)
    along_coherence = np.clip(0.5 * (gn_sp + gn_sm), 0.0, 1.0)

    # Radial divergence of the unit normal |d(nx)/dx + d(ny)/dy| scaled by sigma
    _, dnx_dx = np.gradient(nx.astype(np.float64))
    dny_dy, _ = np.gradient(ny.astype(np.float64))
    radial_curv = np.abs(dnx_dx + dny_dy).astype(np.float32)
    compact_penalty = np.clip(float(sigma) * radial_curv, 0.0, 1.0)

    ext_factor = along_coherence * (1.0 - 0.5 * compact_penalty)
    score = (mag * step_persistence * ext_factor).astype(np.float32)
    return {
        "mag": mag,
        "step_persistence": step_persistence.astype(np.float32),
        "along_coherence": along_coherence.astype(np.float32),
        "radial_curv": radial_curv,
        "score": score,
    }


def compute_gsst_features(
    grav: np.ndarray,
    slope: np.ndarray,
    gy_south: np.ndarray,
    gx_east: np.ndarray,
    fp: np.ndarray,
) -> dict[str, np.ndarray]:
    """Build H86N-GSST surface and matched controls on the footprint."""
    g = clean_band(grav, fp)
    s = clean_band(slope, fp)
    gy = clean_band(gy_south, fp)
    gx = clean_band(gx_east, fp)

    sc3 = gsst_scale_score(g, gx, gy, sigma=3.0)
    sc6 = gsst_scale_score(g, gx, gy, sigma=6.0)

    feats = {
        "gsst_s3": sc3["score"],
        "gsst_s6": sc6["score"],
        "ctrl_raw_grav_slope": s.astype(np.float32),
        "ctrl_compact_curv": (s.astype(np.float32) * sc3["radial_curv"]).astype(np.float32),
    }
    surface_gsst = (
        0.6 * rankpct(feats["gsst_s3"], fp)
        + 0.4 * rankpct(feats["gsst_s6"], fp)
    ).astype(np.float32)
    surfaces = {
        "H86N_GSST": surface_gsst,
        "E0_raw_grav_slope": rankpct(feats["ctrl_raw_grav_slope"], fp),
        "E2_compact_curv": rankpct(feats["ctrl_compact_curv"], fp),
    }
    return {"features": feats, "surfaces": surfaces}
