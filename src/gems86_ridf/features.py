"""Catalogue-blind feature stack for the H86E-RIDF lane.

Every feature is computed ONLY from the 19 competition bands in
``training_features.tif`` (band names pinned in ``gems86.io.BANDS``).  No
feature uses the fault catalogue, so no feature can leak withheld truth; the
catalogue enters the lane only as (a) training labels (visible faults only in
the holdout) and (b) the emission collar, both computed from visible faults.

Physical intent (100 m grid):
* Hessian eigenvalues of ``det_elev`` at 1, 2, 4 px: positive major eigenvalue
  = linear trough (erosion along a fractured fault zone), negative minor
  eigenvalue = linear crest / scarp shoulder.
* Local relief and slope texture: range interiors versus basin floors.
* Gradient magnitude and tilt of RTP magnetics and isostatic gravity:
  lithologic/basement offsets across faults.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from gems86.io import BANDS, read_band

BASE = [name for _, name in sorted(BANDS.items())]


def _hessian_eigs(z: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    zxx = ndi.gaussian_filter(z, sigma, order=(0, 2))
    zyy = ndi.gaussian_filter(z, sigma, order=(2, 0))
    zxy = ndi.gaussian_filter(z, sigma, order=(1, 1))
    tr = 0.5 * (zxx + zyy)
    disc = np.sqrt(0.25 * (zxx - zyy) ** 2 + zxy ** 2)
    s2 = sigma * sigma  # scale-normalised (Lindeberg)
    return ((tr + disc) * s2).astype(np.float32), ((tr - disc) * s2).astype(np.float32)


def _grad_mag(a: np.ndarray, sigma: float) -> np.ndarray:
    gx = ndi.gaussian_filter(a, sigma, order=(0, 1))
    gy = ndi.gaussian_filter(a, sigma, order=(1, 0))
    return np.hypot(gx, gy).astype(np.float32)


def feature_names() -> list[str]:
    names = list(BASE)
    for s in (1, 2, 4):
        names += [f"dem_hess_major_s{s}", f"dem_hess_minor_s{s}"]
    names += ["dem_relief_w5", "dem_relief_w15", "slope_std_s3", "dem_resid_s10",
              "rtp_gm_s2", "rtp_gm_s6", "grav_gm_s2", "grav_gm_s6",
              "mag_tilt", "grav_tilt"]
    return names


def build(features_tif: Path, footprint: np.ndarray, out_path: Path) -> list[str]:
    """Write an (n_features, H, W) float16 memmap; returns feature names."""
    names = feature_names()
    h, w = footprint.shape
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float16,
                                   shape=(len(names), h, w))

    def put(name, arr):
        a = np.asarray(arr, np.float32)
        a = np.where(footprint, a, 0.0)
        # robust standardisation inside the footprint keeps float16 safe
        v = a[footprint]
        lo, hi = np.percentile(v, [0.5, 99.5])
        scale = max(hi - lo, 1e-6)
        a = np.clip((a - lo) / scale, -2.0, 3.0)
        mm[names.index(name)] = a.astype(np.float16)

    for name in BASE:
        put(name, read_band(features_tif, name))
    z = read_band(features_tif, "det_elev")
    for s in (1, 2, 4):
        major, minor = _hessian_eigs(z, s)
        put(f"dem_hess_major_s{s}", major)
        put(f"dem_hess_minor_s{s}", minor)
        del major, minor
    put("dem_relief_w5", ndi.maximum_filter(z, 5) - ndi.minimum_filter(z, 5))
    put("dem_relief_w15", ndi.maximum_filter(z, 15) - ndi.minimum_filter(z, 15))
    put("dem_resid_s10", z - ndi.gaussian_filter(z, 10))
    del z
    sl = read_band(features_tif, "det_elev_slope")
    m = ndi.gaussian_filter(sl, 3)
    put("slope_std_s3", np.sqrt(np.maximum(ndi.gaussian_filter(sl * sl, 3) - m * m, 0)))
    del sl, m
    rtp = read_band(features_tif, "rtp")
    put("rtp_gm_s2", _grad_mag(rtp, 2))
    put("rtp_gm_s6", _grad_mag(rtp, 6))
    del rtp
    gr = read_band(features_tif, "iso_grav_anom")
    put("grav_gm_s2", _grad_mag(gr, 2))
    put("grav_gm_s6", _grad_mag(gr, 6))
    del gr
    put("mag_tilt", np.arctan2(read_band(features_tif, "tmi_vg"),
                               np.abs(read_band(features_tif, "tmi_hg")) + 1e-6))
    put("grav_tilt", np.arctan2(read_band(features_tif, "iso_grav_anom_vg"),
                                np.abs(read_band(features_tif, "iso_grav_anom_hg")) + 1e-6))
    mm.flush()
    return names
