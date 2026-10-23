"""Structural and catalogue-geometry features for the G86 lane.

Two families
------------
``structural`` (catalogue-free, computed once on the full grid)
    * potential-field structural attributes of the competition stack;
    * the lane's new transform, the **gravity-magnetic cross-gradient structural
      coherence** (GMC): the isostatic gravity gradient and the reduced-to-pole
      magnetic gradient are compared pixel by pixel.  Where both fields have a
      strong gradient and the two gradient vectors are collinear, the density
      and magnetisation contrasts share one boundary -- the classical
      cross-gradient structural constraint of Gallardo & Meju (2003, 2004),
      used here as a *detector* rather than as a joint-inversion regulariser.
    * a structure-tensor coherence term that keeps only boundaries that are
      linear over ~1 km, which is what separates a fault trace from an
      isotropic contact blob.

``geometry`` (catalogue-derived, computed per fold from the **visible** mask only)
    * distance to the nearest visible fault, distance to a trace endpoint,
      along-strike tip extrapolation, cross-strike offset and local trace
      coherence, all from :mod:`gems57.network`.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter

from gems57 import network

from .io import read_band

CACHE = Path(".cache") / "features"


# --------------------------------------------------------------------------- #
# robust scaling
# --------------------------------------------------------------------------- #
def rank_normalize(a: np.ndarray, valid: np.ndarray | None = None) -> np.ndarray:
    """Map to [0, 1] by rank over ``valid`` cells; 0 elsewhere.

    Rank normalisation keeps a monotone transform of each feature (it is what a
    linear model needs) without letting a few extreme potential-field values
    dominate the fit.
    """
    a = np.asarray(a, np.float32)
    m = np.isfinite(a) if valid is None else (np.isfinite(a) & valid)
    out = np.zeros(a.shape, np.float32)
    n = int(m.sum())
    if n < 2:
        return out
    vals = a[m]
    order = np.argsort(vals, kind="stable")
    ranks = np.empty(n, np.float32)
    ranks[order] = np.arange(n, dtype=np.float32)
    # average ties so a constant feature maps to 0.5
    if n > 1:
        uniq, inv, cnt = np.unique(vals[order], return_inverse=True, return_counts=True)
        if (cnt > 1).any():
            sums = np.bincount(inv, weights=ranks[order])
            means = (sums / cnt).astype(np.float32)
            ranks[order] = means[inv]
    out[m] = ranks / max(n - 1, 1)
    return out


def _grad(z: np.ndarray, sigma: float):
    gy = gaussian_filter(z, sigma, order=(1, 0), mode="nearest")
    gx = gaussian_filter(z, sigma, order=(0, 1), mode="nearest")
    return gy, gx


def structure_tensor_coherence(gy: np.ndarray, gx: np.ndarray, weight: np.ndarray,
                               win: float) -> np.ndarray:
    """Orientation coherence ``(l1-l2)/(l1+l2)`` of a locally weighted gradient field."""
    w = np.maximum(np.asarray(weight, np.float32), 0.0)
    jxx = gaussian_filter(w * gx * gx, win, mode="nearest")
    jyy = gaussian_filter(w * gy * gy, win, mode="nearest")
    jxy = gaussian_filter(w * gx * gy, win, mode="nearest")
    tr = jxx + jyy
    diff = jxx - jyy
    coh = np.sqrt(diff * diff + 4.0 * jxy * jxy) / np.maximum(tr, 1e-20)
    return np.clip(coh, 0.0, 1.0).astype(np.float32)


def gmc(grav: np.ndarray, mag: np.ndarray, *, sigma: float = 4.0,
        sharp: float = 6.0) -> dict[str, np.ndarray]:
    """Gravity-magnetic cross-gradient structural attributes at one scale.

    Returns (all un-normalised, monotone-increasing in fault likelihood):
      ``contact``  strength x collinearity  -- shared density/magnetisation boundary
      ``oppose``   strength x anti-parallel polarity (the normal-fault polarity
                   for a bedrock/fill contact on the hanging-wall side)
      ``strike_coh``  orientation coherence of the shared boundary over ``sharp`` px
      ``aligned``  ``contact`` restricted to boundaries that are linear over 600 m
    """
    gy, gx = _grad(grav, sigma)
    my, mx = _grad(mag, sigma)
    gm = np.hypot(gy, gx)
    mm = np.hypot(my, mx)
    denom = np.maximum(gm * mm, 1e-12)
    cos_t = (gy * my + gx * mx) / denom            # +1 parallel, -1 anti-parallel
    strength = np.sqrt(np.maximum(gm * mm, 0.0))   # geometric mean of gradient norms
    contact = (np.abs(cos_t) * strength).astype(np.float32)
    oppose = (np.maximum(-cos_t, 0.0) * strength).astype(np.float32)
    coh = structure_tensor_coherence(gy, gx, strength, sharp)
    return dict(contact=contact, oppose=oppose, strike_coh=coh,
                aligned=(contact * coh).astype(np.float32), cos=cos_t.astype(np.float32))


GMC_SCALES = (4.0,)

STRUCTURAL_BANDS = ("tc", "iso_grav_anom_slope", "iso_grav_anom_hg", "tmi_hg",
                    "tmi_vg", "iso_grav_anom_vg", "geod_2ndinv", "det_elev_slope",
                    "depth_to_base_surf", "cond_surf", "ieq_n100a15", "geod_shearrate")


def structural(features_tif: Path, footprint: np.ndarray, *, use_gmc: bool = True,
               cache: bool = True) -> dict[str, np.ndarray]:
    """Full-grid structural feature dict (rank-normalised over the footprint)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out: dict[str, np.ndarray] = {}
    for name in STRUCTURAL_BANDS:
        p = CACHE / f"{name}.npy"
        if cache and p.is_file():
            a = np.load(p, mmap_mode="r")
        else:
            a = rank_normalize(read_band(features_tif, name), footprint).astype(np.float16)
            if cache:
                np.save(p, a)
        out[name] = a
    if use_gmc:
        for sigma in GMC_SCALES:
            key = f"gmc{int(sigma)}"
            p = CACHE / f"{key}.npz"
            if cache and p.is_file():
                z = np.load(p)
                for k in z.files:
                    out[f"{key}_{k}"] = z[k]
                continue
            g = rank_normalize(read_band(features_tif, "iso_grav_anom"), footprint)
            g = gaussian_filter(g, sigma / 2.0, mode="nearest")
            m = rank_normalize(read_band(features_tif, "rtp"), footprint)
            m = gaussian_filter(m, sigma / 2.0, mode="nearest")
            d = gmc(g, m, sigma=sigma)
            pack = {k: rank_normalize(v, footprint).astype(np.float16)
                    for k, v in d.items() if k != "cos"}
            if cache:
                np.savez(p, **pack)
            for k, v in pack.items():
                out[f"{key}_{k}"] = v
            del g, m, d, pack
    return out


def geometry(visible: np.ndarray, footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Catalogue-geometry features from the visible catalogue only.

    ``*_far`` variants are measured from the *tip* rather than from the trace, so
    a cell beyond the end of a strand is scored by how well it continues the
    strand's strike -- the extrapolation an unmapped splay would follow.
    """
    vis = np.asarray(visible, bool)
    H, W = vis.shape
    dist, iy64, ix64 = network.nearest_frame(vis)
    iy = iy64.astype(np.int32); ix = ix64.astype(np.int32)
    del iy64, ix64
    deg = ndi.convolve(vis.astype(np.int16), np.ones((3, 3), np.int16), mode="constant") - vis
    tips = vis & (deg <= 1)
    if not tips.any():
        tips = vis.copy()
    d_tip, (tiy64, tix64) = ndi.distance_transform_edt(~tips, return_indices=True)
    tiy = tiy64.astype(np.int32); tix = tix64.astype(np.int32)
    del tiy64, tix64
    strike, coh = network.local_strike(vis, smooth_px=3.0)
    th = np.radians(np.where(np.isfinite(strike), strike, 0.0))
    ur, uc = -np.cos(th), np.sin(th)
    dy, dx = (iy - np.arange(H, dtype=np.int32)[:, None]).astype(np.float32), \
             (ix - np.arange(W, dtype=np.int32)[None, :]).astype(np.float32)
    d_par = np.abs(dy * ur + dx * uc)
    d_perp = np.abs(-dx * ur + dy * uc)
    t_strike, t_coh = network.local_strike(tips, smooth_px=6.0)
    tth = np.radians(np.where(np.isfinite(t_strike), t_strike, 0.0))
    tur, tuc = -np.cos(tth), np.sin(tth)
    ty, tx = (tiy - np.arange(H, dtype=np.int32)[:, None]).astype(np.float32), \
             (tix - np.arange(W, dtype=np.int32)[None, :]).astype(np.float32)
    t_par = np.abs(ty * tur + tx * tuc)
    t_perp = np.abs(-tx * tur + ty * tuc)
    # continuation of a tip along its own strike: small across-strike offset is good
    cont = np.exp(-t_perp / 2.5) * np.exp(-np.maximum(t_par - 2.0, 0.0) / 30.0)
    dens = gaussian_filter(vis.astype(np.float32), 12.0, mode="constant")
    feats = dict(
        d_vis=dist.astype(np.float32),
        log_d_vis=np.log1p(dist).astype(np.float32),
        d_tip=d_tip.astype(np.float32),
        log_d_tip=np.log1p(d_tip).astype(np.float32),
        tip_continuation=cont.astype(np.float32),
        tip_along=t_par.astype(np.float32),
        tip_cross=t_perp.astype(np.float32),
        along=d_par.astype(np.float32),
        cross=d_perp.astype(np.float32),
        trace_coh=coh.astype(np.float32),
        density=dens.astype(np.float32),
    )
    # same-strike continuation measured from the nearest trace pixel
    near_cont = np.exp(-d_perp / 2.5) * np.exp(-np.maximum(d_par - 3.0, 0.0) / 40.0)
    feats["trace_continuation"] = near_cont.astype(np.float32)
    out = {}
    for k, v in feats.items():
        # rank-normalise inside the footprint so every fold shares one scale
        out[k] = rank_normalize(v, footprint).astype(np.float16)
    del dist, iy, ix, d_tip, tiy, tix, strike, coh, t_strike, t_coh
    return out


# --------------------------------------------------------------------------- #
# external (public USGS/DOE) morphological stack, SHA-256 pinned by restore
# --------------------------------------------------------------------------- #
EXT_CACHE = Path(".cache") / "external"

#: (file, band index, name) -- rank-normalised over the footprint and cached.
EXTERNAL_BANDS = (
    ("lidar_scarp_features_u8.tif", 6, "lid_downface"),
    ("lidar_scarp_features_u8.tif", 7, "lid_upface"),
    ("lidar_scarp_features_u8.tif", 8, "lid_cross"),
    ("lidar_scarp_features_u8.tif", 9, "lid_relief"),
    ("lidar_scarp_features_u8.tif", 3, "lid_step"),
    ("lidar_scarp_features_u8.tif", 4, "lid_lapneg"),
    ("lidar_scarp_features_u8.tif", 5, "lid_lappos"),
    ("topo_10m_derived_100m_u8.tif", 4, "topo_slope_std"),
    ("topo_10m_derived_100m_u8.tif", 6, "topo_curv"),
    ("topo_10m_derived_100m_u8.tif", 8, "topo_hs_lineament"),
    ("topo_10m_derived_100m_u8.tif", 2, "topo_slope_max"),
    ("topo_10m_derived_100m_u8.tif", 5, "topo_relief"),
    ("geodawn_extensions_u8.tif", 2, "rad_UK"),
    ("geodawn_extensions_u8.tif", 1, "rad_ThK"),
    ("dem10_chi_100m_i16.tif", 1, "chi_step_max"),
    ("dem10_chi_100m_i16.tif", 3, "chi_ksn"),
)


def _read_ext(path: Path, band: int) -> np.ndarray:
    import rasterio
    with rasterio.open(path) as src:
        a = src.read(band).astype(np.float32)
        nd = src.nodata
    if nd is not None:
        a[a == nd] = np.nan
    a[~np.isfinite(a)] = np.nan
    return a


def external(footprint: np.ndarray, *, cache: bool = True) -> dict[str, np.ndarray]:
    """Rank-normalised external morphological stack (float16, footprint-scaled).

    Zero is the fill for cells outside the published survey footprint; those
    cells rank lowest, which is the conservative direction (no dot is emitted
    there by the allocator unless the model says so).
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    out: dict[str, np.ndarray] = {}
    for fname, band, name in EXTERNAL_BANDS:
        p = CACHE / f"{name}.npy"
        if cache and p.is_file():
            out[name] = np.load(p, mmap_mode="r")
            continue
        a = _read_ext(EXT_CACHE / fname, band)
        a = np.nan_to_num(a, nan=0.0)
        out[name] = rank_normalize(a, footprint).astype(np.float16)
        np.save(p, out[name])
        del a
    return out
