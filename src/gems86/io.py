"""Raster IO helpers for the pinned competition grid."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio

BANDS = {
    1: "mag_anom", 2: "rtp", 3: "tmi_hg", 4: "geod_2ndinv",
    5: "iso_grav_anom_slope", 6: "tc", 7: "geod_shearrate", 8: "geod_dilaterate",
    9: "tmi_vg", 10: "deq_n100a15", 11: "iso_grav_anom_vg", 12: "det_elev",
    13: "iso_grav_anom", 14: "tmi", 15: "depth_to_base_surf", 16: "ieq_n100a15",
    17: "cond_surf", 18: "iso_grav_anom_hg", 19: "det_elev_slope",
}
BY_NAME = {v: k for k, v in BANDS.items()}
# Pixel-verified physical overrides for mislabeled GeoTIFF band headers
# (see scripts/verify_band_physics.py and docs/evidence/band-physics-verification-20261024.json):
BAND_PHYSICS_VERIFIED = {
    6: "GeoDAWN Airborne Radiometric Total Count TC (strictly positive, min=+2.9534, r=+0.997140 vs geodawn_rad_u8 TC; NOT magnetic tilt)",
    11: "Signed southward directional gravity derivative +d(Band 13)/drow_south = -d(Band 13)/dy_north (r=+0.938102; NOT vertical gravity derivative)",
    18: "Signed eastward directional gravity derivative +d(Band 13)/dx_east (r=+0.948186; NOT unsigned scalar horizontal gradient)",
    5: "Unsigned 2-D horizontal gravity gradient magnitude hypot(Band 11, Band 18) (r=+0.946995)",
}
NODATA = -3.4028234663852886e38


def read_band(path: Path, name_or_index: int | str) -> np.ndarray:
    idx = BY_NAME[name_or_index] if isinstance(name_or_index, str) else int(name_or_index)
    with rasterio.open(path) as src:
        a = src.read(idx).astype(np.float32)
    a[~np.isfinite(a)] = 0.0
    a[a <= NODATA * 0.5] = 0.0
    return a
