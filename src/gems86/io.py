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
NODATA = -3.4028234663852886e38


def read_band(path: Path, name_or_index: int | str) -> np.ndarray:
    idx = BY_NAME[name_or_index] if isinstance(name_or_index, str) else int(name_or_index)
    with rasterio.open(path) as src:
        a = src.read(idx).astype(np.float32)
    a[~np.isfinite(a)] = 0.0
    a[a <= NODATA * 0.5] = 0.0
    return a
