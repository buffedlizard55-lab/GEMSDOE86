"""H86R-SFG feature planes (all frozen in research/H86R_SFG_PREREGISTRATION.json).

Five catalogue-free edge planes from native bands, one multiline-corroborated
fusion E, and a spin-2 alignment gate A between the local gravity-edge strike
and a smoothed double-angle catalogue strike field. The catalogue enters ONLY
through A (visible-only inside holdout folds) and the emission collar.
Memory-lean: float32 planes, no (5,H,W) stack.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

SENTINEL = -3.4028234663852886e38

STATIC_NAMES = (
    "sfg_grav_edge_b5_rank",
    "sfg_mag_edge_b3_rank",
    "sfg_rtp_gradmag_s1p5_rank",
    "sfg_basement_gradmag_rank",
    "sfg_elev_slope_b19_rank",
    "sfg_edge_fusion_E",
    "sfg_alignment_A_fullcat",
    "sfg_surface_E1_fullcat",
)


def clean(band: np.ndarray, fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (values float32 with missing->0, finite&in-footprint mask)."""
    a = np.asarray(band, dtype=np.float32)
    ok = fp & np.isfinite(a) & (a > SENTINEL * 0.5)
    out = np.where(ok, a, 0.0).astype(np.float32)
    return out, ok


def rank01(values: np.ndarray, ok: np.ndarray) -> np.ndarray:
    """Percentile rank in [0,1] over ok pixels; 0 elsewhere. Ties: average via argsort of mergesort (deterministic)."""
    out = np.zeros(values.shape, np.float32)
    v = values[ok].astype(np.float64)
    if v.size == 0:
        return out
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(v.size, np.float64)
    ranks[order] = np.arange(v.size)
    # average ranks for exact ties (edge bands are continuous; cheap safeguard on unique values)
    out[ok] = (ranks / max(v.size - 1, 1)).astype(np.float32)
    return out


def _gradmag(a: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(a)
    return np.hypot(gx, gy).astype(np.float32)


def edge_ranks(read_band, fp: np.ndarray) -> dict[str, np.ndarray]:
    """read_band(index)->float32 array. Returns the 5 frozen edge-rank planes."""
    planes: dict[str, np.ndarray] = {}

    b, ok = clean(read_band(5), fp)
    planes["sfg_grav_edge_b5_rank"] = rank01(np.abs(b), ok)

    b, ok = clean(read_band(3), fp)
    planes["sfg_mag_edge_b3_rank"] = rank01(np.abs(b), ok)

    b, ok = clean(read_band(2), fp)
    sm = ndi.gaussian_filter(b, 1.5, mode="nearest")
    planes["sfg_rtp_gradmag_s1p5_rank"] = rank01(_gradmag(sm), ok)
    del sm

    b, ok = clean(read_band(15), fp)
    sm = ndi.gaussian_filter(b, 1.5, mode="nearest")
    planes["sfg_basement_gradmag_rank"] = rank01(_gradmag(sm), ok)
    del sm

    b, ok = clean(read_band(19), fp)
    planes["sfg_elev_slope_b19_rank"] = rank01(np.abs(b), ok)
    return planes


def fuse_E(planes: dict[str, np.ndarray]) -> np.ndarray:
    """E = 0.5*mean(5 ranks) + 0.5*(second-highest rank), per pixel, no 5-plane stack."""
    keys = [k for k in STATIC_NAMES[:5]]
    total = np.zeros_like(planes[keys[0]])
    top1 = np.full_like(total, -1.0)
    for k in keys:
        total += planes[k]
        top1 = np.maximum(top1, planes[k])
    # Exact second-highest: count how many planes equal top1, then the best
    # remaining candidate per plane (top1 itself only counts twice if tied).
    top2 = np.full_like(total, -1.0)
    n_top = np.zeros(total.shape, np.int8)
    for k in keys:
        n_top += (planes[k] == top1)
    for k in keys:
        p = planes[k]
        cand = np.where((p == top1) & (n_top < 2), -1.0, np.minimum(p, top1))
        top2 = np.maximum(top2, cand)
    top2 = np.maximum(top2, 0.0)
    return (0.5 * (total / len(keys)) + 0.5 * top2).astype(np.float32)


def _double_angle_from_gradient(grow: np.ndarray, gcol: np.ndarray):
    """Strike double-angle (cos2s, sin2s, energy) for strike perpendicular to gradient, image frame."""
    e = grow * grow + gcol * gcol
    safe = e > 0
    cos2 = np.zeros_like(e)
    sin2 = np.zeros_like(e)
    # phi = atan2(grow,gcol); strike s = phi + pi/2; cos2s = -cos2phi, sin2s = -sin2phi
    cos2[safe] = -(gcol[safe] ** 2 - grow[safe] ** 2) / e[safe]
    sin2[safe] = -(2.0 * grow[safe] * gcol[safe]) / e[safe]
    return cos2.astype(np.float32), sin2.astype(np.float32), e.astype(np.float32), safe


def catalogue_strike_field(cat_mask: np.ndarray, fp: np.ndarray, block: int = 10,
                           smooth_blocks: float = 5.0) -> tuple[np.ndarray, np.ndarray]:
    """Smoothed double-angle catalogue strike field, upsampled to full grid.

    Design = 5 km smoothing (preregistration). Implemented on a 10-px block
    grid (sigma=5 blocks == 50 px) and bilinearly upsampled - the field is
    smooth by construction; full-res sigma=50 gaussian on 12.3M px in a 3 GB
    sandbox is the only reason for the coarse grid (recorded in run card).
    Returns (cos2C, sin2C) full-res float32, unit-normalized where defined.
    """
    sm = ndi.gaussian_filter(cat_mask.astype(np.float32), 2.0, mode="nearest")
    grow, gcol = np.gradient(sm)
    del sm
    cos2, sin2, energy, safe = _double_angle_from_gradient(
        grow.astype(np.float32), gcol.astype(np.float32))
    del grow, gcol
    w = np.where(safe & fp, energy, 0.0).astype(np.float32)
    cw = (cos2 * w).astype(np.float32)
    sw = (sin2 * w).astype(np.float32)
    del cos2, sin2, energy
    h, wdt = fp.shape
    hb, wb = h // block, wdt // block
    sl = (slice(0, hb * block), slice(0, wb * block))

    def block_mean(a):
        return a[sl].reshape(hb, block, wb, block).mean(axis=(1, 3)).astype(np.float32)

    cb = ndi.gaussian_filter(block_mean(cw), smooth_blocks, mode="nearest")
    sb = ndi.gaussian_filter(block_mean(sw), smooth_blocks, mode="nearest")
    del cw, sw, w
    cos_full = ndi.zoom(cb, (h / cb.shape[0], wdt / cb.shape[1]), order=1).astype(np.float32)
    sin_full = ndi.zoom(sb, (h / sb.shape[0], wdt / sb.shape[1]), order=1).astype(np.float32)
    del cb, sb
    cos_full, sin_full = cos_full[:h, :wdt], sin_full[:h, :wdt]
    nrm = np.hypot(cos_full, sin_full)
    ok = nrm > 0
    cos_full[ok] /= nrm[ok]
    sin_full[ok] /= nrm[ok]
    cos_full[~ok] = 0.0
    sin_full[~ok] = 0.0
    return cos_full, sin_full


def alignment_A(b11: np.ndarray, b18: np.ndarray, fp: np.ndarray,
                cos2C: np.ndarray, sin2C: np.ndarray) -> np.ndarray:
    """A = cos^2(theta_E - theta_C) in [0,1]; 0.5 (neutral) where undefined."""
    grow, ok11 = clean(b11, fp)   # +dB13/drow_south (verified physics)
    gcol, ok18 = clean(b18, fp)   # +dB13/dx_east    (verified physics)
    cos2E, sin2E, energy, safe = _double_angle_from_gradient(grow, gcol)
    del grow, gcol
    defined = safe & ok11 & ok18 & ((cos2C != 0) | (sin2C != 0))
    cos_diff2 = cos2E * cos2C + sin2E * sin2C
    a = np.where(defined, 0.5 * (1.0 + cos_diff2), 0.5).astype(np.float32)
    return np.clip(a, 0.0, 1.0)


def gated(surface_base: np.ndarray, a: np.ndarray) -> np.ndarray:
    return (surface_base * (0.35 + 0.65 * a)).astype(np.float32)


DISK_OFFSETS = tuple(
    (dy, dx) for dy in range(-3, 4) for dx in range(-3, 4)
    if (dy * dy + dx * dx) < 2.8 * 2.8
)


def emit_poisson_disk(surface: np.ndarray, eligible: np.ndarray, budget: int = 37654,
                      rng_order: np.ndarray | None = None) -> np.ndarray:
    """Score-descending greedy emission, min spacing 2.8 px, exactly `budget` dots.

    rng_order (flat indices) overrides score order (used only for the random null).
    Deterministic: stable mergesort on descending score, flat-index tie order.
    """
    h, w = surface.shape
    idx = np.flatnonzero(eligible.ravel())
    if idx.size < budget:
        raise ValueError(f"eligible pool {idx.size} < budget {budget}")
    if rng_order is None:
        order = idx[np.argsort(-surface.ravel()[idx].astype(np.float64), kind="mergesort")]
    else:
        order = rng_order
    blocked = np.zeros(surface.shape, bool)
    dots = np.zeros(surface.shape, bool)
    dys = np.array([o[0] for o in DISK_OFFSETS])
    dxs = np.array([o[1] for o in DISK_OFFSETS])
    n = 0
    bflat = blocked.ravel()
    for flat in order:
        if bflat[flat]:
            continue
        y, x = divmod(int(flat), w)
        dots[y, x] = True
        n += 1
        ys, xs = y + dys, x + dxs
        ok = (ys >= 0) & (ys < h) & (xs >= 0) & (xs < w)
        blocked[ys[ok], xs[ok]] = True
        if n >= budget:
            break
    if n != budget:
        raise ValueError(f"emission exhausted pool at {n} < {budget} dots")
    return dots
