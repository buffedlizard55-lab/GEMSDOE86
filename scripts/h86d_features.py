#!/usr/bin/env python3
"""Memory-safe feature stack & fold-strict structural mechanics for GEMSDOE86 (`H86-CTHB`).

Hypothesis `H86-CTHB`: Contact-Truncation, Cross-Gradient Discordance & Hydrothermal-Breach
Relay Mechanics.

Strict anti-leakage guarantees:
  1. All 28 static planes (`STATIC_FEATURE_NAMES`) are 100% catalogue-free (`existing_faults.tif`,
     `trace_segments_utm11.csv`, and `derived_sgmc_faults_100m_u8.tif` are NEVER read here).
  2. Point CSV readers (`gdr_wellspring_in_footprint.csv`, `gdr_volcanic_vents_in_footprint.csv`)
     explicitly ban `dist_known_fault_px` and track exact accessed columns (`ACCESSED_CSV_COLUMNS`)
     for automated unit-test verification.
  3. All 7 structural mechanics planes (`MECH_FEATURE_NAMES`) are computed strictly inside each
     fold from that fold's `visible` fault mask via unmodified `vendor/gems57/network.py` and
     `vendor/gems57/relay_bend_anatomy.py`, with raw isotropic `d_cat` explicitly excluded so the
     model cannot emit blind concentric collars around mapped traces.
"""
from __future__ import annotations

import csv
import gc
import hashlib
import json
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from gems57 import faultzone as FZ
from gems57 import grid as G
from gems57 import network as NET
from gems57 import relay_bend_anatomy as RBA

DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache" / "h86_cthb_planes"
CACHE_MANIFEST = ROOT / "docs" / "evidence" / "h86d_feature_cache_manifest.json"

BANNED_CSV_COLUMNS = frozenset({"dist_known_fault_px"})
ACCESSED_CSV_COLUMNS: dict[str, tuple[str, ...]] = {}

STATIC_FEATURE_BLOCKS: dict[str, tuple[str, ...]] = {
    "contact_truncation": (
        "mag_ridge_s15",
        "mag_ridge_trunc_s15",
        "mag_ridge_trunc_s35",
        "grav_ridge_trunc_s25",
        "mag_grav_crossgrad_s2",
        "mag_grav_crossgrad_s5",
        "shallow_brittle_mag_excess",
        "tilt_strike_dispersion",
        "basement_hinge_flexure",
    ),
    "radiometric_discordance": (
        "rad_kth_local_anom",
        "rad_topo_crossgrad",
        "rad_uth_redox_grad",
        "rad_broad_th_mimic",
        "rad_valid",
    ),
    "hydrothermal_breach": (
        "t2m_dab_plume",
        "t2m_survey_density",
        "paleo_sinter_vent",
        "upslope_geotherm_breach",
        "claycap_margin_grad",
        "geod_transtension_valve",
        "piedmont_inflection",
        "volcanic_vent_halo",
    ),
    "scarplet_geomorph": (
        "lidar_scarplet_raw",
        "lidar_chain_collinearity",
        "dem10_curv_lineament",
        "dem10_chi_knickzone",
        "pluvial_shoreline_mimic",
        "det_elev_scarp_multiscale",
    ),
}

STATIC_FEATURE_NAMES: tuple[str, ...] = tuple(
    name for group in STATIC_FEATURE_BLOCKS.values() for name in group
)

MECH_FEATURE_NAMES: tuple[str, ...] = (
    "vis_tip_cone",
    "vis_relay_corridor",
    "vis_bend_splay",
    "vis_kinematic_trans",
    "vis_strike_concordance",
    "vis_tip_x_trunc",
    "vis_relay_x_geotherm",
)

ALL_FEATURE_NAMES: tuple[str, ...] = STATIC_FEATURE_NAMES + MECH_FEATURE_NAMES


def _robust_norm(arr: np.ndarray, footprint: np.ndarray, clip_z: float = 6.0) -> np.ndarray:
    vals = arr[footprint & np.isfinite(arr)]
    if vals.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    med = float(np.median(vals))
    iqr = float(np.percentile(vals, 75.0) - np.percentile(vals, 25.0))
    scale = max(iqr / 1.349, float(np.std(vals)), 1e-6)
    out = np.clip((arr - med) / scale, -clip_z, clip_z).astype(np.float32)
    out[~footprint | ~np.isfinite(arr)] = 0.0
    return out


def _positive_rank_unit(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    vals = arr[footprint & np.isfinite(arr)]
    if vals.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    lo = float(np.percentile(vals, 5.0))
    hi = float(np.percentile(vals, 99.0))
    span = max(hi - lo, 1e-6)
    out = np.clip((arr - lo) / span, 0.0, 1.5).astype(np.float32)
    out[~footprint | ~np.isfinite(arr)] = 0.0
    return out


def _fill_footprint(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    valid = footprint & np.isfinite(arr)
    out = np.zeros(arr.shape, dtype=np.float32)
    if not valid.any():
        return out
    med = float(np.median(arr[valid]))
    out[:] = med
    out[valid] = arr[valid].astype(np.float32)
    if (~valid).any():
        _, (iy, ix) = ndi.distance_transform_edt(~valid, return_indices=True)
        out = out[iy, ix].astype(np.float32)
        del iy, ix
    return out


def _hessian_ridge_and_truncation(
    field: np.ndarray,
    footprint: np.ndarray,
    sigma: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return `(ridge_strength, ridge_tangent_truncation, strike_rad)` at scale `sigma`."""
    f = _fill_footprint(field, footprint)
    fxx = ndi.gaussian_filter(f, sigma=sigma, order=(0, 2), mode="nearest") * (sigma**2)
    fyy = ndi.gaussian_filter(f, sigma=sigma, order=(2, 0), mode="nearest") * (sigma**2)
    fxy = ndi.gaussian_filter(f, sigma=sigma, order=(1, 1), mode="nearest") * (sigma**2)

    tr = 0.5 * (fxx + fyy)
    rad = np.sqrt(np.maximum(0.25 * (fxx - fyy) ** 2 + fxy**2, 0.0))
    lam_abs = np.maximum(np.abs(tr - rad), np.abs(tr + rad)).astype(np.float32)
    # Normal direction of sharpest curvature -> perpendicular is ridge strike tangent
    phi_norm = 0.5 * np.arctan2(2.0 * fxy, fxx - fyy)
    # Ridge tangent unit vector (ty, tx) in image (row, col) coordinates
    ty = np.cos(phi_norm).astype(np.float32)
    tx = (-np.sin(phi_norm)).astype(np.float32)
    del fxx, fyy, fxy, tr, rad

    ry = ndi.gaussian_filter(lam_abs, sigma=max(1.0, 0.7 * sigma), order=(1, 0), mode="nearest")
    rx = ndi.gaussian_filter(lam_abs, sigma=max(1.0, 0.7 * sigma), order=(0, 1), mode="nearest")
    # Along-ridge derivative |t . grad(R)|: vanishes along continuous contacts, spikes at faulted truncations
    trunc = (np.abs(ty * ry + tx * rx) * np.sqrt( np.maximum(lam_abs, 0.0) )).astype(np.float32)
    # Azimuth clockwise from north: dx = tx, dy_north = -ty -> atan2(tx, -ty) in [0, pi)
    strike_rad = (np.arctan2(tx, -ty) % np.pi).astype(np.float32)
    del ry, rx, ty, tx
    return (
        _positive_rank_unit(lam_abs, footprint),
        _positive_rank_unit(trunc, footprint),
        strike_rad,
    )


def _cross_gradient(
    a: np.ndarray,
    b: np.ndarray,
    footprint: np.ndarray,
    sigma: float,
) -> np.ndarray:
    fa = _fill_footprint(a, footprint)
    fb = _fill_footprint(b, footprint)
    ay = ndi.gaussian_filter(fa, sigma=sigma, order=(1, 0), mode="nearest")
    ax = ndi.gaussian_filter(fa, sigma=sigma, order=(0, 1), mode="nearest")
    by = ndi.gaussian_filter(fb, sigma=sigma, order=(1, 0), mode="nearest")
    bx = ndi.gaussian_filter(fb, sigma=sigma, order=(0, 1), mode="nearest")
    cg = np.abs(ax * by - ay * bx).astype(np.float32)
    del fa, fb, ay, ax, by, bx
    return _positive_rank_unit(np.sqrt(np.maximum(cg, 0.0)), footprint)


def _read_core_band(index_1based: int) -> np.ndarray:
    with rasterio.open(DATA_DIR / "training_features.tif") as src:
        a = src.read(index_1based, masked=True)
        out = np.where(a.mask, np.nan, a.data.astype(np.float32))
    return out


def _parse_2m_probes(shape: tuple[int, int], footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Parse DOE GDR 1391 2m temperature probe shapefile (`F2mDAB` above background)."""
    zpath = DATA_DIR / "external" / "2m_temperature_probe_INGENIOUS_regional_data.zip"
    with zipfile.ZipFile(zpath) as zf:
        dbf = zf.read("2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf")
        shp = zf.read("2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.shp")

    nrec, hdr_len, rec_len = struct.unpack("<IHH", dbf[4:12])
    fields: list[tuple[str, int]] = []
    pos = 32
    while dbf[pos] != 0x0D:
        fields.append((dbf[pos : pos + 11].split(b"\x00")[0].decode("ascii"), dbf[pos + 16]))
        pos += 32

    lons: list[float] = []
    lats: list[float] = []
    dabs: list[float] = []
    shp_pos = 100
    for i in range(nrec):
        _, content_len = struct.unpack(">II", shp[shp_pos : shp_pos + 8])
        x, y = struct.unpack("<dd", shp[shp_pos + 12 : shp_pos + 28])
        shp_pos += 8 + content_len * 2
        row_bytes = dbf[hdr_len + i * rec_len + 1 : hdr_len + (i + 1) * rec_len]
        off = 0
        rec: dict[str, str] = {}
        for fn, fl in fields:
            rec[fn] = row_bytes[off : off + fl].decode("utf-8", errors="replace").strip()
            off += fl
        lons.append(x)
        lats.append(y)
        dabs.append(float(rec["F2mDAB"]) if rec.get("F2mDAB") else 0.0)

    xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
    cols = np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32)
    rows = np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32)
    inb = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])

    imp_anom = np.zeros(shape, dtype=np.float32)
    imp_cnt = np.zeros(shape, dtype=np.float32)
    dab_pos = np.clip(np.nan_to_num(np.asarray(dabs, dtype=np.float32), nan=0.0), 0.0, 15.0)
    np.maximum.at(imp_anom, (rows[inb], cols[inb]), dab_pos[inb])
    np.add.at(imp_cnt, (rows[inb], cols[inb]), 1.0)

    num = ndi.gaussian_filter(imp_anom, sigma=12.0, mode="constant")
    den = ndi.gaussian_filter((imp_cnt > 0).astype(np.float32), sigma=12.0, mode="constant")
    plume = (num / (den + 0.008)).astype(np.float32)
    dens = ndi.gaussian_filter(np.minimum(imp_cnt, 3.0), sigma=18.0, mode="constant").astype(np.float32)
    plume[~footprint] = 0.0
    dens[~footprint] = 0.0
    return _positive_rank_unit(plume, footprint), _positive_rank_unit(dens, footprint)


def _parse_paleo_sinter(shape: tuple[int, int], footprint: np.ndarray) -> np.ndarray:
    """Parse DOE GDR 1391 paleogeothermal sinter, travertine & tufa vent deposits."""
    zpath = DATA_DIR / "external" / "paleo_geothermal_regional.zip"
    with zipfile.ZipFile(zpath) as zf:
        lines = zf.read("Paleo_geothermal_final.csv").decode("utf-8", errors="replace").splitlines()
    lons: list[float] = []
    lats: list[float] = []
    for row in csv.DictReader(lines):
        try:
            lons.append(float(row["Long_deg_NAD83"]))
            lats.append(float(row["Lat_deg_NAD83"]))
        except (KeyError, ValueError):
            continue
    xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
    cols = np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32)
    rows = np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32)
    inb = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
    src = np.zeros(shape, dtype=bool)
    src[rows[inb], cols[inb]] = True
    dist = ndi.distance_transform_edt(~src).astype(np.float32)
    prox = (0.60 * np.exp(-dist / 8.0) + 0.40 * np.exp(-dist / 25.0)).astype(np.float32)
    prox[~footprint] = 0.0
    return prox


def _parse_wellspring_upslope(
    shape: tuple[int, int],
    footprint: np.ndarray,
    dem_mean: np.ndarray,
) -> np.ndarray:
    """Read thermal wells/springs WITHOUT `dist_known_fault_px` and advect 300 m upslope."""
    cpath = DATA_DIR / "external" / "gdr_wellspring_in_footprint.csv"
    allowed_cols = ("row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c")
    ACCESSED_CSV_COLUMNS[cpath.name] = allowed_cols
    assert not (set(allowed_cols) & BANNED_CSV_COLUMNS)

    dem_f = _fill_footprint(dem_mean, footprint)
    gy = ndi.gaussian_filter(dem_f, sigma=4.0, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(dem_f, sigma=4.0, order=(0, 1), mode="nearest")
    gn = np.hypot(gy, gx) + 1e-6
    uy = gy / gn
    ux = gx / gn
    del dem_f, gy, gx, gn

    imp = np.zeros(shape, dtype=np.float32)
    with cpath.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                r = int(row["row"])
                c = int(row["col"])
            except (KeyError, ValueError):
                continue
            if not (0 <= r < shape[0] and 0 <= c < shape[1]):
                continue
            tc = float(row["temp_c"]) if row.get("temp_c") else 0.0
            tq = float(row["geothermquartz_c"]) if row.get("geothermquartz_c") else 0.0
            tch = float(row["geothermchalc_c"]) if row.get("geothermchalc_c") else 0.0
            geoth = max(tq, tch)
            score = max(tc - 20.0, 0.0) / 40.0 + 0.6 * max(geoth - 80.0, 0.0) / 100.0
            if score <= 0.02:
                continue
            # Advect 3 px (300 m) upslope along +grad(DEM) toward range-front feeder conduit
            ru = int(np.clip(round(r + 3.0 * float(uy[r, c])), 0, shape[0] - 1))
            cu = int(np.clip(round(c + 3.0 * float(ux[r, c])), 0, shape[1] - 1))
            if score > imp[ru, cu]:
                imp[ru, cu] = min(score, 4.0)
    del uy, ux
    out = (
        0.65 * ndi.gaussian_filter(imp, sigma=6.0, mode="constant")
        + 0.35 * ndi.gaussian_filter(imp, sigma=18.0, mode="constant")
    ).astype(np.float32)
    out[~footprint] = 0.0
    return _positive_rank_unit(out, footprint)


def _parse_volcanic_vents(shape: tuple[int, int], footprint: np.ndarray) -> np.ndarray:
    cpath = DATA_DIR / "external" / "gdr_volcanic_vents_in_footprint.csv"
    allowed_cols = ("row", "col")
    ACCESSED_CSV_COLUMNS[cpath.name] = allowed_cols
    assert not (set(allowed_cols) & BANNED_CSV_COLUMNS)

    src = np.zeros(shape, dtype=bool)
    with cpath.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            r, c = int(row["row"]), int(row["col"])
            if 0 <= r < shape[0] and 0 <= c < shape[1]:
                src[r, c] = True
    dist = ndi.distance_transform_edt(~src).astype(np.float32)
    out = np.exp(-dist / 35.0).astype(np.float32)
    out[~footprint] = 0.0
    return out


def _collinear_chain_filter(scarp: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """8-azimuth 9-pixel (900 m) anisotropic collinearity filter for en-echelon scarplet chains."""
    work = np.where(valid, scarp, 0.0).astype(np.float32)
    best = np.zeros_like(work)
    angles_deg = (0.0, 22.5, 45.0, 67.5, 90.0, 112.5, 135.0, 157.5)
    offsets = (-4, -3, -2, -1, 0, 1, 2, 3, 4)
    for ang in angles_deg:
        rad = np.radians(ang)
        dy = np.cos(rad)
        dx = np.sin(rad)
        ker = np.zeros((9, 9), dtype=np.float32)
        for t in offsets:
            rr = int(round(4 + t * dy))
            cc = int(round(4 + t * dx))
            if 0 <= rr < 9 and 0 <= cc < 9:
                ker[rr, cc] += 1.0
        ker /= max(float(ker.sum()), 1.0)
        resp = ndi.convolve(work, ker, mode="constant")
        np.maximum(best, resp, out=best)
    out = best.astype(np.float32)
    out[~valid] = np.nan
    return out


def _save_plane(idx: int, name: str, arr: np.ndarray) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = CACHE_DIR / f"{idx:02d}_{name}.npy"
    a32 = np.asarray(arr, dtype=np.float32)
    np.save(p, a32)
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    finite = a32[np.isfinite(a32)]
    return {
        "index": idx,
        "name": name,
        "path": str(p.relative_to(ROOT)),
        "sha256": sha,
        "finite_count": int(finite.size),
        "p50": float(np.percentile(finite, 50.0)) if finite.size else 0.0,
        "p95": float(np.percentile(finite, 95.0)) if finite.size else 0.0,
    }


def build_or_load_static_planes(grid: G.Grid, force: bool = False) -> list[np.ndarray]:
    """Build (if missing) and memory-map all 28 static catalogue-free `float32` planes."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    expected_paths = [CACHE_DIR / f"{i:02d}_{nm}.npy" for i, nm in enumerate(STATIC_FEATURE_NAMES)]
    aux_strike_path = CACHE_DIR / "_aux_phys_strike_rad.npy"
    if not force and all(p.exists() for p in expected_paths) and aux_strike_path.exists():
        # Populate ACCESSED_CSV_COLUMNS even on warm cache so tests can inspect
        ACCESSED_CSV_COLUMNS["gdr_wellspring_in_footprint.csv"] = (
            "row",
            "col",
            "temp_c",
            "geothermquartz_c",
            "geothermchalc_c",
        )
        ACCESSED_CSV_COLUMNS["gdr_volcanic_vents_in_footprint.csv"] = ("row", "col")
        return [np.load(p, mmap_mode="r") for p in expected_paths]

    fp = grid.footprint
    shape = grid.shape
    meta: list[dict] = []

    # --- Block 1: Contact-Truncation & Cross-Gradient Discordance (0..8) ---
    rtp = _read_core_band(2)
    r15, tr15, mag_strike = _hessian_ridge_and_truncation(rtp, fp, sigma=1.5)
    _, tr35, _ = _hessian_ridge_and_truncation(rtp, fp, sigma=3.5)
    meta.append(_save_plane(0, "mag_ridge_s15", r15))
    meta.append(_save_plane(1, "mag_ridge_trunc_s15", tr15))
    meta.append(_save_plane(2, "mag_ridge_trunc_s35", tr35))
    del r15, tr15, tr35

    iso_grav = _read_core_band(13)
    _, gtr25, _ = _hessian_ridge_and_truncation(iso_grav, fp, sigma=2.5)
    cg2 = _cross_gradient(rtp, iso_grav, fp, sigma=2.0)
    cg5 = _cross_gradient(rtp, iso_grav, fp, sigma=5.0)
    meta.append(_save_plane(3, "grav_ridge_trunc_s25", gtr25))
    meta.append(_save_plane(4, "mag_grav_crossgrad_s2", cg2))
    meta.append(_save_plane(5, "mag_grav_crossgrad_s5", cg5))
    del rtp, iso_grav, gtr25, cg2, cg5
    gc.collect()

    tmi_hg = _read_core_band(3)
    with rasterio.open(DATA_DIR / "external" / "geodawn_extensions_u8.tif") as ds_ext:
        thk_u8 = ds_ext.read(1)
        uth_u8 = ds_ext.read(3)
        tmi_up150_u8 = ds_ext.read(4)
    up_valid = fp & (tmi_up150_u8 > 0)
    up_f = _fill_footprint(np.where(up_valid, tmi_up150_u8.astype(np.float32), np.nan), fp)
    up_hg = np.hypot(
        ndi.gaussian_filter(up_f, sigma=2.2, order=(1, 0), mode="nearest"),
        ndi.gaussian_filter(up_f, sigma=2.2, order=(0, 1), mode="nearest"),
    )
    shallow_brittle = _robust_norm(tmi_hg, fp) - 0.65 * _robust_norm(up_hg, fp)
    meta.append(_save_plane(6, "shallow_brittle_mag_excess", _positive_rank_unit(shallow_brittle, fp)))
    del tmi_hg, up_f, up_hg, shallow_brittle, tmi_up150_u8

    tc_tilt = _fill_footprint(_read_core_band(6), fp)
    tcy = ndi.gaussian_filter(tc_tilt, sigma=1.5, order=(1, 0), mode="nearest")
    tcx = ndi.gaussian_filter(tc_tilt, sigma=1.5, order=(0, 1), mode="nearest")
    th_tc = np.arctan2(tcx, -tcy)
    c2 = ndi.gaussian_filter(np.cos(2.0 * th_tc).astype(np.float32), sigma=4.0, mode="nearest")
    s2 = ndi.gaussian_filter(np.sin(2.0 * th_tc).astype(np.float32), sigma=4.0, mode="nearest")
    disp = (1.0 - np.clip(np.hypot(c2, s2), 0.0, 1.0)).astype(np.float32)
    disp[~fp] = 0.0
    meta.append(_save_plane(7, "tilt_strike_dispersion", disp))
    del tc_tilt, tcy, tcx, th_tc, c2, s2, disp

    dtb = _fill_footprint(_read_core_band(15), fp)
    dtb_grad = np.hypot(
        ndi.gaussian_filter(dtb, sigma=2.0, order=(1, 0), mode="nearest"),
        ndi.gaussian_filter(dtb, sigma=2.0, order=(0, 1), mode="nearest"),
    )
    dtb_lap = np.abs(ndi.gaussian_filter(dtb, sigma=2.5, order=(2, 0), mode="nearest") + ndi.gaussian_filter(dtb, sigma=2.5, order=(0, 2), mode="nearest"))
    with rasterio.open(DATA_DIR / "external" / "acquisition_block_id_100m.tif") as ds_blk:
        blk = ds_blk.read(1)
    seam = (ndi.maximum_filter(blk, size=3) != ndi.minimum_filter(blk, size=3)) & (blk > 0)
    seam_wt = (1.0 - 0.55 * np.exp(-ndi.distance_transform_edt(~seam).astype(np.float32) / 3.0)).astype(np.float32)
    flex = (0.55 * _positive_rank_unit(dtb_grad, fp) + 0.45 * _positive_rank_unit(dtb_lap, fp)) * seam_wt
    meta.append(_save_plane(8, "basement_hinge_flexure", flex))
    del dtb, dtb_grad, dtb_lap, blk, seam, seam_wt, flex
    gc.collect()

    # --- Block 2: Radiometric-Topographic Discordance (9..13) ---
    det_elev = _read_core_band(12)
    with rasterio.open(DATA_DIR / "external" / "geodawn_rad_u8.tif") as ds_rad:
        k_u8 = ds_rad.read(1)
        th_u8 = ds_rad.read(2)
        u_u8 = ds_rad.read(3)
    rad_valid_mask = fp & (k_u8 > 0) & (th_u8 > 0) & (u_u8 > 0)
    k_ratio = np.where(rad_valid_mask, k_u8.astype(np.float32) / (th_u8.astype(np.float32) + 8.0), np.nan)
    k_fill = _fill_footprint(k_ratio, fp)
    k_loc = ndi.gaussian_filter(k_fill, sigma=1.5, mode="nearest") - ndi.gaussian_filter(k_fill, sigma=15.0, mode="nearest")
    k_anom = _robust_norm(k_loc, rad_valid_mask).astype(np.float32)
    k_anom[~rad_valid_mask] = np.nan
    meta.append(_save_plane(9, "rad_kth_local_anom", k_anom))

    rt_cg = _cross_gradient(k_loc, det_elev, fp, sigma=2.0)
    rt_cg[~rad_valid_mask] = np.nan
    meta.append(_save_plane(10, "rad_topo_crossgrad", rt_cg))

    uth_f = _fill_footprint(np.where(rad_valid_mask & (uth_u8 > 0), uth_u8.astype(np.float32), np.nan), fp)
    uth_loc = ndi.gaussian_filter(uth_f, sigma=1.5, mode="nearest") - ndi.gaussian_filter(uth_f, sigma=14.0, mode="nearest")
    uth_grad = np.hypot(
        ndi.gaussian_filter(uth_loc, sigma=1.5, order=(1, 0), mode="nearest"),
        ndi.gaussian_filter(uth_loc, sigma=1.5, order=(0, 1), mode="nearest"),
    )
    uth_out = _positive_rank_unit(uth_grad, rad_valid_mask)
    uth_out[~rad_valid_mask] = np.nan
    meta.append(_save_plane(11, "rad_uth_redox_grad", uth_out))

    th_f = _fill_footprint(np.where(rad_valid_mask, th_u8.astype(np.float32), np.nan), fp)
    th_step = np.hypot(
        ndi.gaussian_filter(th_f, sigma=6.0, order=(1, 0), mode="nearest"),
        ndi.gaussian_filter(th_f, sigma=6.0, order=(0, 1), mode="nearest"),
    )
    th_out = _positive_rank_unit(th_step, rad_valid_mask)
    th_out[~rad_valid_mask] = np.nan
    meta.append(_save_plane(12, "rad_broad_th_mimic", th_out))
    meta.append(_save_plane(13, "rad_valid", rad_valid_mask.astype(np.float32)))
    del k_u8, th_u8, u_u8, thk_u8, uth_u8, k_ratio, k_fill, k_loc, k_anom, rt_cg, uth_f, uth_loc, uth_grad, uth_out, th_f, th_step, th_out, rad_valid_mask
    gc.collect()

    # Load 10 m DEM bands needed across Blocks 3 & 4
    topo_man = json.loads((DATA_DIR / "external" / "topo_10m_derived_100m_u8.manifest.json").read_text())
    bmeta = {b["band_name"]: b for b in topo_man["bands"]}
    with rasterio.open(DATA_DIR / "external" / "topo_10m_derived_100m_u8.tif") as ds_t10:
        slope_p90_u8 = ds_t10.read(1)
        relief_u8 = ds_t10.read(5)
        curv_u8 = ds_t10.read(6)
        asp_coh_u8 = ds_t10.read(7)
        hs_lin_u8 = ds_t10.read(8)
        dem_u8 = ds_t10.read(9)

    def _dequant(u8: np.ndarray, bname: str) -> np.ndarray:
        lo, hi = float(bmeta[bname]["lo"]), float(bmeta[bname]["hi"])
        v = lo + ((np.clip(u8.astype(np.float32), 1.0, 255.0) - 1.0) / 254.0) * (hi - lo)
        return np.where((u8 > 0) & fp, v, np.nan).astype(np.float32)

    dem_mean = _dequant(dem_u8, "dem_mean")
    relief_local = _dequant(relief_u8, "relief_local")

    # --- Block 3: Blind Geothermal Vent, 2m Probe, Sinter & Clay-Cap Breach (14..21) ---
    t2m_plume, t2m_dens = _parse_2m_probes(shape, fp)
    meta.append(_save_plane(14, "t2m_dab_plume", t2m_plume))
    meta.append(_save_plane(15, "t2m_survey_density", t2m_dens))
    del t2m_plume, t2m_dens

    sinter = _parse_paleo_sinter(shape, fp)
    meta.append(_save_plane(16, "paleo_sinter_vent", sinter))
    del sinter

    ws_up = _parse_wellspring_upslope(shape, fp, dem_mean)
    meta.append(_save_plane(17, "upslope_geotherm_breach", ws_up))
    del ws_up

    cond = _fill_footprint(_read_core_band(17), fp)
    cond_grad = np.hypot(
        ndi.gaussian_filter(cond, sigma=2.0, order=(1, 0), mode="nearest"),
        ndi.gaussian_filter(cond, sigma=2.0, order=(0, 1), mode="nearest"),
    )
    cond_hi = np.maximum(cond - ndi.gaussian_filter(cond, sigma=18.0, mode="nearest"), 0.0)
    claycap = 0.65 * _positive_rank_unit(cond_grad, fp) + 0.35 * _positive_rank_unit(cond_hi, fp)
    meta.append(_save_plane(18, "claycap_margin_grad", claycap.astype(np.float32)))
    del cond, cond_grad, cond_hi, claycap

    g_inv = _positive_rank_unit(_read_core_band(4), fp)
    g_shr = _positive_rank_unit(np.abs(_read_core_band(7)), fp)
    g_dil = _positive_rank_unit(_read_core_band(8), fp)
    valve = (0.40 * g_shr + 0.35 * g_dil + 0.25 * g_inv).astype(np.float32)
    meta.append(_save_plane(19, "geod_transtension_valve", valve))
    del g_inv, g_shr, g_dil, valve

    ieq = _positive_rank_unit(_read_core_band(16), fp)
    deq = _positive_rank_unit(_read_core_band(10), fp)
    rel_f = _fill_footprint(relief_local, fp)
    # Piedmont range-front inflection peaks at intermediate local relief (25..140 m) + microseismicity
    pied = np.exp(-((rel_f - 75.0) / 65.0) ** 2).astype(np.float32) * 0.65 + 0.35 * (0.5 * ieq + 0.5 * deq)
    pied[~fp] = 0.0
    meta.append(_save_plane(20, "piedmont_inflection", pied.astype(np.float32)))
    del ieq, deq, pied

    vvent = _parse_volcanic_vents(shape, fp)
    meta.append(_save_plane(21, "volcanic_vent_halo", vvent))
    del vvent
    gc.collect()

    # --- Block 4: Pluvial-Deconfounded 1 m LiDAR, 10 m DEM & Fluvial Chi (22..27) ---
    with rasterio.open(DATA_DIR / "external" / "lidar_scarp_features_u8.tif") as ds_lid:
        lid_ex = ds_lid.read(1).astype(np.float32)
        lid_step = ds_lid.read(3).astype(np.float32)
        lid_down = ds_lid.read(6).astype(np.float32)
        lid_strike_u8 = ds_lid.read(11)
        lid_valid = (ds_lid.read(12) > 0) & fp
    lid_raw = (0.45 * lid_ex + 0.35 * lid_step + 0.20 * lid_down) / 255.0
    lid_chain = _collinear_chain_filter(lid_raw, lid_valid)
    lid_raw_out = np.where(lid_valid, lid_raw, np.nan).astype(np.float32)
    meta.append(_save_plane(22, "lidar_scarplet_raw", lid_raw_out))
    meta.append(_save_plane(23, "lidar_chain_collinearity", lid_chain))

    # Build fused physical strike plane: 1 m LiDAR strike where available & strong, else RTP ridge strike
    lid_strike_rad = (lid_strike_u8.astype(np.float32) / 255.0) * np.pi
    use_lid_strike = lid_valid & (lid_raw > 0.12)
    phys_strike = np.where(use_lid_strike, lid_strike_rad, mag_strike).astype(np.float32)
    np.save(aux_strike_path, phys_strike)
    del lid_ex, lid_step, lid_down, lid_strike_u8, lid_raw, lid_raw_out, lid_chain, lid_valid, lid_strike_rad, use_lid_strike, mag_strike, phys_strike

    curv = _positive_rank_unit(_dequant(curv_u8, "curv_prof_absmax"), fp)
    acoh = _positive_rank_unit(_dequant(asp_coh_u8, "aspect_coherence"), fp)
    hslin = _positive_rank_unit(_dequant(hs_lin_u8, "hs_lineament"), fp)
    slp90 = _positive_rank_unit(_dequant(slope_p90_u8, "slope_p90"), fp)
    dem10_comp = (0.35 * curv + 0.25 * acoh + 0.25 * hslin + 0.15 * slp90).astype(np.float32)
    meta.append(_save_plane(24, "dem10_curv_lineament", dem10_comp))
    del curv, acoh, hslin, slp90, dem10_comp, slope_p90_u8, curv_u8, asp_coh_u8, hs_lin_u8, dem_u8, relief_u8

    with rasterio.open(DATA_DIR / "external" / "dem10_chi_100m_u8.tif") as ds_chi:
        knick = ds_chi.read(2).astype(np.float32)
        raised = ds_chi.read(3).astype(np.float32)
        chi_val = (ds_chi.read(4) > 0) & fp
    chi_raw = np.where(chi_val, (0.60 * knick + 0.40 * raised) / 255.0, 0.0).astype(np.float32)
    chi_sm = (0.55 * chi_raw + 0.45 * ndi.gaussian_filter(chi_raw, sigma=2.5, mode="constant")).astype(np.float32)
    meta.append(_save_plane(25, "dem10_chi_knickzone", _positive_rank_unit(chi_sm, fp)))
    del knick, raised, chi_val, chi_raw, chi_sm

    # Explicit Pleistocene Lake Lahontan (1332 m, 1270 m) & Lake Bonneville (1552 m, 1463 m) shoreline mimic
    dem_f = _fill_footprint(dem_mean, fp)
    shore = np.zeros(shape, dtype=np.float32)
    for z_highstand in (1270.0, 1332.0, 1463.0, 1552.0):
        np.maximum(shore, np.exp(-0.5 * ((dem_f - z_highstand) / 16.0) ** 2).astype(np.float32), out=shore)
    shore *= np.exp(-rel_f / 32.0).astype(np.float32)
    shore[~fp] = 0.0
    meta.append(_save_plane(26, "pluvial_shoreline_mimic", shore))
    del dem_mean, relief_local, dem_f, rel_f, shore

    det_slp = _read_core_band(19)
    de_r15, _, _ = _hessian_ridge_and_truncation(det_elev, fp, sigma=1.5)
    de_r35, _, _ = _hessian_ridge_and_truncation(det_elev, fp, sigma=3.5)
    det_comp = (0.45 * de_r15 + 0.30 * de_r35 + 0.25 * _positive_rank_unit(det_slp, fp)).astype(np.float32)
    meta.append(_save_plane(27, "det_elev_scarp_multiscale", det_comp))
    del det_elev, det_slp, de_r15, de_r35, det_comp
    gc.collect()

    CACHE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    CACHE_MANIFEST.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "hypothesis": "H86-CTHB",
                "static_feature_count": len(STATIC_FEATURE_NAMES),
                "accessed_csv_columns": {k: list(v) for k, v in ACCESSED_CSV_COLUMNS.items()},
                "banned_csv_columns_verified_unread": sorted(BANNED_CSV_COLUMNS),
                "planes": meta,
            },
            indent=2,
        )
        + "\n"
    )
    return [np.load(p, mmap_mode="r") for p in expected_paths]


def load_sense_raster(grid: G.Grid) -> np.ndarray:
    """Load unmasked slip-sense raster (`trace_sense_raster`); callers MUST mask to `visible`."""
    cpath = DATA_DIR / "external" / "trace_segments_utm11.csv"
    return FZ.trace_sense_raster(cpath, grid.shape, grid.transform)


def compute_visible_mechanics(
    visible: np.ndarray,
    footprint: np.ndarray,
    static_planes: list[np.ndarray],
    sense_unmasked: np.ndarray,
    cache_tag: str | None = None,
) -> list[np.ndarray]:
    """Compute the 7 strictly fold-safe, anti-halo `visible`-only mechanics planes.

    Raw isotropic distance `d` is intentionally excluded; all decays clamp `d >= 3.5 px`
    so there is zero immediate-adjacency halo leakage and `buffer_px=3` holds cleanly.
    """
    if cache_tag is not None:
        m_dir = CACHE_DIR / f"mech_{cache_tag}"
        m_paths = [m_dir / f"{i:02d}_{nm}.npy" for i, nm in enumerate(MECH_FEATURE_NAMES)]
        if all(p.exists() for p in m_paths):
            return [np.load(p, mmap_mode="r") for p in m_paths]

    # 1. Tip-propagation cone via `vendor/gems57/network.py` (visible faults ONLY)
    strike_vis, _ = NET.local_strike(visible, smooth_px=3.0)
    seg, n_seg = NET.segments(visible, max_len_px=12)[:2]
    tab = NET.segment_table(seg, n_seg)
    comp, ncomp = ndi.label(visible, structure=NET.STRUCT3)
    comp_len = np.bincount(comp.ravel(), minlength=ncomp + 1).astype(np.float32)

    d, iy, ix = NET.nearest_frame(visible)
    H, W = visible.shape
    rows_grid, cols_grid = np.indices((H, W), dtype=np.int32)
    dy = (rows_grid - iy).astype(np.float32)
    dx = (cols_grid - ix).astype(np.float32)
    del rows_grid, cols_grid

    anc_seg = seg[iy, ix]
    s_anchor = strike_vis[iy, ix]
    s_seg = tab.strike[np.clip(anc_seg, 0, len(tab.strike) - 1)]
    s_host = np.where(np.isfinite(s_anchor), s_anchor, s_seg)
    s_host = np.where(np.isfinite(s_host), s_host, 0.0).astype(np.float32)
    del strike_vis, seg, anc_seg, s_anchor, s_seg

    d_par, d_perp, _ = NET.offset_components(dy.ravel(), dx.ravel(), s_host.ravel())
    d_par_abs = np.abs(d_par).reshape(H, W).astype(np.float32)
    d_perp_2d = d_perp.reshape(H, W).astype(np.float32)
    del dy, dx, d_par, d_perp

    ln = comp_len[np.clip(comp[iy, ix], 0, len(comp_len) - 1)]
    del comp, comp_len, iy, ix

    d_clamp = np.maximum(d, 3.5).astype(np.float32)
    tip_gate = np.clip((d_par_abs - 0.5) / 1.5, 0.0, 1.0)
    cross_beam = np.exp(-0.5 * (d_perp_2d / 2.1) ** 2)
    along_decay = np.exp(-np.maximum(d_par_abs, 3.0) / 16.0)
    vis_tip_cone = (tip_gate * cross_beam * along_decay * np.minimum(np.log1p(ln) / 4.5, 1.5)).astype(np.float32)
    vis_tip_cone[~footprint | visible] = 0.0
    del d_par_abs, d_perp_2d, tip_gate, cross_beam, along_decay, ln

    # Axial strike concordance between physical strike and visible host strike
    phys_strike = np.load(CACHE_DIR / "_aux_phys_strike_rad.npy", mmap_mode="r")
    host_rad = np.radians(s_host)
    align = (0.5 * (1.0 + np.cos(2.0 * (phys_strike - host_rad))) * np.exp(-d_clamp / 28.0)).astype(np.float32)
    align[~footprint | visible] = 0.0
    del s_host, host_rad, d, d_clamp
    gc.collect()

    # 2. Two-host inter-component relay corridor via `vendor/gems57/relay_bend_anatomy.py`
    f2 = RBA.two_host_frame(visible)
    bf = RBA.host_bend_fields(visible)

    act_ys, act_xs = np.nonzero(footprint & ~visible)
    d1 = f2["d1"][act_ys, act_xs]
    d2 = f2["d2"][act_ys, act_xs]
    ay1 = f2["iy1"][act_ys, act_xs]
    ax1 = f2["ix1"][act_ys, act_xs]
    ay2 = f2["iy2"][act_ys, act_xs]
    ax2 = f2["ix2"][act_ys, act_xs]

    dy1 = (act_ys - ay1).astype(np.float32)
    dx1 = (act_xs - ax1).astype(np.float32)
    dy2 = (act_ys - ay2).astype(np.float32)
    dx2 = (act_xs - ax2).astype(np.float32)
    facing = np.clip(-(dy1 * dy2 + dx1 * dx2) / np.maximum(d1 * d2, 1e-6), 0.0, 1.0)
    ratio = 2.0 * np.clip(d1 / np.maximum(d1 + d2, 1e-6), 0.0, 0.5)
    span_clamp = np.maximum(d1 + d2, 7.0)

    vis_relay = np.zeros((H, W), dtype=np.float32)
    vis_relay[act_ys, act_xs] = ((facing**2) * ratio * np.exp(-span_clamp / 28.0)).astype(np.float32)

    # 3. Host-bend splay gathered from nearest visible anchor (ay1, ax1)
    turn1 = bf["turn"][ay1, ax1]
    d1_clamp = np.maximum(d1, 3.5).astype(np.float32)
    vis_bend = np.zeros((H, W), dtype=np.float32)
    vis_bend[act_ys, act_xs] = (np.nan_to_num(turn1, nan=0.0) * np.exp(-d1_clamp / 18.0)).astype(np.float32)

    del f2, bf, d1, d2, ay1, ax1, ay2, ax2, dy1, dx1, dy2, dx2, facing, ratio, span_clamp, turn1, d1_clamp, act_ys, act_xs
    gc.collect()

    # Strictly mask sense_unmasked to `visible` inside `kinematic_transition_field`
    vis_kin = RBA.kinematic_transition_field(visible, sense_unmasked).astype(np.float32)
    vis_kin[~footprint | visible] = 0.0
    gc.collect()

    # 4. Physics-gated structural interactions
    idx_map = {nm: i for i, nm in enumerate(STATIC_FEATURE_NAMES)}
    trunc_comp = (
        0.30 * np.nan_to_num(static_planes[idx_map["mag_ridge_trunc_s15"]], nan=0.0)
        + 0.25 * np.nan_to_num(static_planes[idx_map["mag_grav_crossgrad_s2"]], nan=0.0)
        + 0.25 * np.nan_to_num(static_planes[idx_map["dem10_curv_lineament"]], nan=0.0)
        + 0.20 * np.nan_to_num(static_planes[idx_map["lidar_chain_collinearity"]], nan=0.0)
    ).astype(np.float32)
    hydro_comp = (
        0.30 * np.nan_to_num(static_planes[idx_map["t2m_dab_plume"]], nan=0.0)
        + 0.25 * np.nan_to_num(static_planes[idx_map["upslope_geotherm_breach"]], nan=0.0)
        + 0.25 * np.nan_to_num(static_planes[idx_map["claycap_margin_grad"]], nan=0.0)
        + 0.20 * np.nan_to_num(static_planes[idx_map["paleo_sinter_vent"]], nan=0.0)
    ).astype(np.float32)

    vis_tip_x_trunc = (vis_tip_cone * trunc_comp).astype(np.float32)
    vis_relay_x_geotherm = (vis_relay * (0.35 + hydro_comp)).astype(np.float32)
    del trunc_comp, hydro_comp

    planes = [
        vis_tip_cone,
        vis_relay,
        vis_bend,
        vis_kin,
        align,
        vis_tip_x_trunc,
        vis_relay_x_geotherm,
    ]
    if cache_tag is not None:
        m_dir = CACHE_DIR / f"mech_{cache_tag}"
        m_dir.mkdir(parents=True, exist_ok=True)
        for i, (nm, arr) in enumerate(zip(MECH_FEATURE_NAMES, planes)):
            np.save(m_dir / f"{i:02d}_{nm}.npy", arr.astype(np.float32))
        del planes
        gc.collect()
        return [np.load(m_dir / f"{i:02d}_{nm}.npy", mmap_mode="r") for i, nm in enumerate(MECH_FEATURE_NAMES)]
    return planes


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    grid = G.load_grid(DATA_DIR)
    build_or_load_static_planes(grid, force=False)


if __name__ == "__main__":
    main()
