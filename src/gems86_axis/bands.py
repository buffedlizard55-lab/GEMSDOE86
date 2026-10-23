"""Hash-pinned external bands, dequantised, and the two responses the axes consume.

Only USGS-published GeoDAWN products and USGS/derived topographic products are used here.
Lidar-derived rasters are deliberately NOT loaded: brief section 5 allows them for SNAP
only "if the human supplies them", and the human supplied the GeoDAWN/DEM mirror set only.

Band semantics come from the mirrors' own sidecar metadata
(``.cache/gems_data/external/geodawn_extensions.json``, ``geodawn_rad.json`` and the
``band_name``/``q_rule`` TIFF tags on the topographic product); DOI 10.5066/P93LGLVQ,
USGS ScienceBase item 657e1d85d34e23d3533209f7 (public domain).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / ".cache" / "gems_data" / "external"

TMI_BAND = "TMI_up150"          # geodawn_extensions_u8.tif, upward-continued TMI
SCARP_BANDS = ("curv_prof_absmax", "slope_max", "hs_lineament")  # topo_10m_derived_100m_u8.tif


def _read(path: Path) -> tuple[np.ndarray, dict]:
    import rasterio

    with rasterio.open(path) as src:
        arr = src.read()
        names = list(src.descriptions)
        tags = {i: dict(src.tags(i)) for i in range(1, src.count + 1)}
        nodata = src.nodatavals
    return arr, {"names": names, "tags": tags, "nodata": nodata,
                 "shape": arr.shape[1:], "dtype": str(arr.dtype)}


def _dequant_u8(band: np.ndarray, tags: dict) -> np.ndarray:
    """Invert ``v = lo + (q-1)/254*(hi-lo); q=0 nodata`` exactly as the tag states."""
    lo = float(tags["q_lo"])
    hi = float(tags["q_hi"])
    out = np.full(band.shape, np.nan, dtype=np.float32)
    live = band > 0
    out[live] = lo + (band[live].astype(np.float64) - 1.0) / 254.0 * (hi - lo)
    return out


def load_bands(ext_dir: str | Path = EXT) -> dict:
    """Return dequantised TMI, scarp-response composites and the DEM mean, all float32."""
    ext_dir = Path(ext_dir)
    ext_arr, ext_meta = _read(ext_dir / "geodawn_extensions_u8.tif")
    topo_arr, topo_meta = _read(ext_dir / "topo_10m_derived_100m_u8.tif")
    dem_arr, dem_meta = _read(ext_dir / "dem10_chi_100m_i16.tif")

    i_tmi = ext_meta["names"].index(TMI_BAND)
    tmi = (ext_arr[i_tmi] > 0).astype(np.float32) * ext_arr[i_tmi].astype(np.float32)

    scarp = {}
    for nm in SCARP_BANDS:
        i = topo_meta["names"].index(nm)
        scarp[nm] = _dequant_u8(topo_arr[i], topo_meta["tags"][i + 1])
    i_dem = topo_meta["names"].index("dem_mean")
    dem_mean = _dequant_u8(topo_arr[i_dem], topo_meta["tags"][i_dem + 1])

    i_z = dem_meta["names"].index("zmean_m")
    nodata = dem_meta["nodata"][0]
    zmean = np.where(dem_arr[i_z] == nodata, np.nan, dem_arr[i_z].astype(np.float32))

    return {"tmi_up150": tmi, "scarp": scarp, "dem_mean": dem_mean, "zmean_m": zmean,
            "meta": {"extensions": ext_meta["names"], "topo": topo_meta["names"],
                     "dem_chi": dem_meta["names"]}}


def gradient_magnitude(field: np.ndarray, fill_value: float = 0.0) -> np.ndarray:
    """Sobel-gradient magnitude with NaNs filled by ``fill_value`` (documented, not silent)."""
    from scipy import ndimage

    a = np.nan_to_num(np.asarray(field, dtype=np.float32), nan=fill_value)
    gy = ndimage.sobel(a, axis=0) / 8.0
    gx = ndimage.sobel(a, axis=1) / 8.0
    return np.hypot(gy, gx).astype(np.float32)


def zscore(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    sd = float(np.nanstd(a))
    if not np.isfinite(sd) or sd <= 0:
        return np.zeros_like(a)
    return ((a - float(np.nanmean(a))) / sd).astype(np.float32)
