"""H86G-EDTI feature stack: pinned competition + external grids only.

No catalogue-derived feature is constructed here (preregistration
``research/H86G_EDTI_PREREGISTRATION.md``).  The catalogue enters only as
training labels / emission collar / scoring mask in the runner.

Sentinel handling: the competition stack carries the float32 nodata sentinel
``-3.4028235e+38`` at 3,061 in-footprint cells (``data/prepared_manifest.json``).
Those cells (and every non-finite cell) are filled with the band's footprint
median *before* any derivative is taken, so no sentinel can propagate into a
feature, a posterior, or -- via the fail-closed writer -- a submission value.
Band identities follow ``src/gems86/io.py:Band`` (band 6 is radiometric total
count, pixel-verified; bands 11/18 are signed directional gravity derivatives).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

SENTINEL = -1e30


def _clean(a: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    a = a.astype(np.float32, copy=True)
    bad = ~np.isfinite(a) | (a <= SENTINEL)
    inside = a[footprint & ~bad]
    med = float(np.median(inside)) if inside.size else 0.0
    a[bad] = med
    return a


def _gradmag(a: np.ndarray, sigma: float) -> np.ndarray:
    gy = ndi.gaussian_filter1d(a, sigma, axis=0, order=1, mode="nearest")
    gx = ndi.gaussian_filter1d(a, sigma, axis=1, order=1, mode="nearest")
    return np.hypot(gy, gx).astype(np.float32)


def _lap(a: np.ndarray, sigma: float) -> np.ndarray:
    return ndi.gaussian_laplace(a, sigma, mode="nearest").astype(np.float32)


def build_stack(feature_tif: Path, ext_dir: Path, footprint: np.ndarray,
                out_path: Path) -> tuple[np.memmap, list[str]]:
    """Build (or reuse) the float32 feature memmap; returns (stack, names)."""
    names: list[str] = []
    # 36 stack-derived + 10 lidar + 9 topo + 5 chi + 4 rad + 4 radx = 68.
    n_total = 68
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mm = np.memmap(out_path, dtype=np.float32, mode="w+",
                   shape=(n_total,) + footprint.shape)

    def add(name: str, a: np.ndarray) -> None:
        mm[len(names)] = np.asarray(a, dtype=np.float32)
        names.append(name)

    with rasterio.open(feature_tif) as ds:
        raw = {i: _clean(ds.read(i), footprint) for i in range(1, 20)}

    # --- raw competition bands (identities per src/gems86/io.py) ----------
    add("b01_mag_anom", raw[1])
    add("b02_rtp", raw[2])
    add("b03_tmi_hg", raw[3])
    add("b04_geod_2ndinv", raw[4])
    add("b05_grav_hg_mag", raw[5])
    add("b06_tc_radiometric", raw[6])
    add("b07_geod_shearrate", raw[7])
    add("b08_geod_dilaterate", raw[8])
    add("b09_tmi_vg", raw[9])
    add("b10_log_deq", np.log1p(np.clip(raw[10], 0, None)))
    add("b11_grav_d_south", raw[11])
    add("b12_det_elev", raw[12])
    add("b13_iso_grav", raw[13])
    add("b14_tmi", raw[14])
    logdepth = np.log1p(np.clip(raw[15], 0, None)).astype(np.float32)
    add("b15_log_depth_base", logdepth)
    add("b16_log_ieq", np.log(np.clip(raw[16], 1.0, None)))
    add("b17_cond_surf", raw[17])
    add("b18_grav_d_east", raw[18])
    add("b19_det_elev_slope", raw[19])

    # --- derived potential-field / topographic edges ----------------------
    add("analytic_signal_log", np.log1p(np.hypot(raw[3], raw[9])))
    add("tilt_mag", np.arctan2(raw[9], np.maximum(raw[3], 1e-6)))
    for label, band in (("rtp", raw[2]), ("grav", raw[13]),
                        ("logdepth", logdepth), ("dem", raw[12])):
        add(f"gradmag_{label}_s1p5", _gradmag(band, 1.5))
        add(f"gradmag_{label}_s3", _gradmag(band, 3.0))
    add("lap_rtp_s1p5", _lap(raw[2], 1.5))
    add("abslap_rtp_s1p5", np.abs(_lap(raw[2], 1.5)))
    add("lap_dem_s1p5", _lap(raw[12], 1.5))
    add("gradmag_tc_s2", _gradmag(raw[6], 2.0))
    add("gradmag_cond_s2", _gradmag(raw[17], 2.0))
    # geodetic strain localisation edges (hypothesis H86G-STRAIN, as features)
    add("gradmag_2ndinv_s3", _gradmag(raw[4], 3.0))
    add("gradmag_dilat_s3", _gradmag(raw[8], 3.0))
    del raw

    # --- pinned external grids (uint8/int16 quantised derivatives) ----------
    def add_external(fname: str, prefix: str, skip: set[str]) -> None:
        path = ext_dir / fname
        with rasterio.open(path) as ds:
            for i, desc in enumerate(ds.descriptions, start=1):
                if desc in skip:
                    continue
                a = ds.read(i).astype(np.float32)
                if ds.dtypes[i - 1] == "uint8":
                    a /= 255.0
                add(f"{prefix}_{desc}", a)

    # 'valid' (lidar coverage) and raw circular 'strike' are excluded:
    # coverage must not become a mapping-effort proxy.
    add_external("lidar_scarp_features_u8.tif", "lidar", {"valid", "strike"})
    add_external("topo_10m_derived_100m_u8.tif", "topo", set())
    add_external("dem10_chi_100m_i16.tif", "chi", set())
    add_external("geodawn_rad_u8.tif", "rad", set())
    add_external("geodawn_extensions_u8.tif", "radx", set())

    if len(names) != n_total:
        raise RuntimeError(f"feature count drift: {len(names)} != {n_total}: {names}")
    mm.flush()
    return mm, names


def load_stack(path: Path, n_features: int, shape2d: tuple[int, int]) -> np.memmap:
    return np.memmap(path, dtype=np.float32, mode="r",
                     shape=(n_features,) + tuple(shape2d))
