"""Memory-bounded (< 900 MiB peak RSS) translation-invariant feature builder for H86K-STDP:
  - Multi-Altitude 2-D FFT Harmonic Upward-Continued Salem-Fairhead (2007) Tilt-Angle
    Zero-Contour Sharpness & Lateral Dip-Migration (z0=100 m vs z1=400 m)
  - Bilinear Up-Dip Hanging-Wall Fault-Emergence Pullback along (-grad Z_b)
  - Intrabasin Rollover Keystone Hinge Curvature & Aseismic Creep Deficit
  - Up-Hydraulic-Head Advected DOE GDR #1391 Fournier Geothermometer Disequilibrium,
    2-m Shallow Temperature Probe Thermal Walls, & Paleo-Sinter/Travertine Vents
  - GeoDAWN Survey-Block Seam Veto (acquisition_block_id_100m.tif) & 10 m DEM
    Quantile-Matched 3DEP 1 m LiDAR Swath Debiasing.

Zero raw regional levels enter any feature plane, and ``dist_known_fault_px`` is
strictly forbidden and audited unread.
"""

from __future__ import annotations

import csv
import gc
import hashlib
from pathlib import Path
import struct
import sys
import zipfile

import numpy as np
from numpy.lib.format import open_memmap
import rasterio
from rasterio.warp import transform as warp_transform
from scipy import ndimage as ndi
from scipy.fft import fftfreq, irfft2, rfft2, rfftfreq

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
for _p in (ROOT_DIR, SRC_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems86.io import BANDS, BAND_PHYSICS_VERIFIED, NODATA
from gems86_mcsp.features import (
    _hessian_ridge_and_eccentricity,
    _structure_tensor_intersection,
    riesz_monogenic_phase_congruency,
)
from scripts.restore_data import EXTERNAL_PINS

BANNED_CSV_COLUMNS: frozenset[str] = frozenset({"dist_known_fault_px"})

EXPECTED_NATIVE_BANDS: dict[int, str] = {
    2: "rtp",
    3: "tmi_hg",
    4: "geod_2ndinv",
    5: "iso_grav_anom_slope",
    6: "tc",
    7: "geod_shearrate",
    8: "geod_dilaterate",
    9: "tmi_vg",
    10: "deq_n100a15",
    11: "iso_grav_anom_vg",
    12: "det_elev",
    13: "iso_grav_anom",
    15: "depth_to_base_surf",
    16: "ieq_n100a15",
    17: "cond_surf",
    18: "iso_grav_anom_hg",
    19: "det_elev_slope",
}

GDR_AND_AUDIT_PINS: dict[str, str] = {
    "acquisition_block_id_100m.tif": "2c0785c4b3ec46c734d1be7a7aedbb3e816201100ab358033a3af074418c894a",
    "gdr_wellspring_in_footprint.csv": "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea",
    "gdr_volcanic_vents_in_footprint.csv": "f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883f4974542ff6a0bf",
    "2m_temperature_probe_INGENIOUS_regional_data.zip": "1301f70d230058e616ea5d34d1c7a32fabf7d49198172f376c59c89bd652eca3",
    "paleo_geothermal_regional.zip": "faffcf697f32dbbf6cbb317cd1effb3e305538ce38eb239d72d0c6fa071e91ca",
}

STDP_STATIC_NAMES: tuple[str, ...] = (
    "salem_rtp_tilt_zero_z100",
    "salem_grav_tilt_zero_z100",
    "salem_rtp_dip_migration",
    "salem_grav_dip_migration",
    "updip_pullback_grav_step",
    "updip_pullback_rtp_step",
    "updip_pullback_monogenic",
    "updip_pullback_cond_neck",
    "intrabasin_keystone_hinge",
    "tmi_up150_wavenumber_si",
    "hydro_magnetite_destruction",
    "aseismic_creep_deficit",
    "transtens_strain_rate_hp",
    "microseismic_swarm_hp",
    "uphead_geotherm_diseq",
    "probe2m_uphead_thermal_wall",
    "paleo_sinter_vent_corridor",
    "rad_kth_alteration_seamfree",
    "rad_uth_redox_seamfree",
    "geotherm_conjugate_intersect",
    "lidar1m_scarp_swath_debiased",
    "lidar1m_curv_dipole_debiased",
    "topo10_piedmont_curv_break",
    "chi10_drainage_knick_step",
)

ABLATION_LOCAL_NAMES: tuple[str, ...] = (
    "local_rtp_gradmag_s2",
    "local_grav_slope_b5",
    "local_depth_gradmag_s3",
    "local_elev_slope_b19",
    "local_lidar_step_debiased",
    "local_topo10_slope_p90",
    "local_strain_2ndinv_hp",
    "local_geotherm_iso_blur",
)

FOLD_ELASTIC_NAMES: tuple[str, ...] = (
    "wing_crack_lobe",
    "collinear_tip_cone",
    "stepover_bridge",
    "broadside_stress_shadow",
)


def _sha256_path(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_stdp_input_contract(ext_dir: Path | None = None) -> dict:
    """Verify band semantics in src/gems86/io.py and all SHA-256 external pins."""
    for idx, expected in EXPECTED_NATIVE_BANDS.items():
        actual = BANDS.get(idx)
        if actual != expected:
            raise RuntimeError(
                f"Band contract mismatch at Band {idx}: expected {expected!r}, got {actual!r}"
            )
    for req_override in (5, 6, 11, 18):
        if req_override not in BAND_PHYSICS_VERIFIED:
            raise RuntimeError(f"Missing verified physics override for Band {req_override}")

    ext_verified: dict[str, str] = {}
    if ext_dir is not None:
        ext_root = Path(ext_dir)
        all_pins = {**EXTERNAL_PINS, **GDR_AND_AUDIT_PINS}
        for fname, expected_sha in all_pins.items():
            p = ext_root / fname
            if not p.is_file():
                raise FileNotFoundError(f"Missing pinned external input: {p}")
            got = _sha256_path(p)
            if got != expected_sha:
                raise RuntimeError(
                    f"SHA-256 mismatch for {fname}: got {got}, expected {expected_sha}"
                )
            ext_verified[fname] = got

    return {
        "verified_native_bands": {str(k): v for k, v in EXPECTED_NATIVE_BANDS.items()},
        "verified_overrides": {str(k): BAND_PHYSICS_VERIFIED[k] for k in (5, 6, 11, 18)},
        "verified_external_sha256": ext_verified,
        "banned_csv_columns": sorted(BANNED_CSV_COLUMNS),
    }


def _masked_gaussian(arr: np.ndarray, valid: np.ndarray, sigma: float) -> np.ndarray:
    v = valid.astype(np.float32)
    num = ndi.gaussian_filter(np.where(valid, arr, 0.0).astype(np.float32), sigma=sigma, mode="nearest")
    den = ndi.gaussian_filter(v, sigma=sigma, mode="nearest")
    return np.where(valid & (den > 1e-5), num / np.maximum(den, 1e-5), 0.0).astype(np.float32)


def _masked_gradients(arr: np.ndarray, valid: np.ndarray, sigma: float = 1.5) -> tuple[np.ndarray, np.ndarray]:
    sm = _masked_gaussian(arr, valid, sigma)
    gy = ndi.gaussian_filter(sm, sigma=1.0, order=(1, 0), mode="nearest").astype(np.float32)
    gx = ndi.gaussian_filter(sm, sigma=1.0, order=(0, 1), mode="nearest").astype(np.float32)
    gy[~valid] = 0.0
    gx[~valid] = 0.0
    return gx, gy


def _robust_pos_z(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    vals = arr[mask]
    if vals.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    med = float(np.median(vals))
    q75, q25 = np.percentile(vals, [75.0, 25.0])
    scale = float(max((q75 - q25) * 0.7413, np.std(vals) * 0.5, 1e-6))
    z = (arr.astype(np.float32) - med) / scale
    return np.where(mask, np.clip(z, -8.0, 12.0), np.float32(0.0))


def _rank01(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros(arr.shape, dtype=np.float32)
    vals = np.nan_to_num(arr[mask], nan=0.0, posinf=0.0, neginf=0.0)
    if vals.size == 0 or np.ptp(vals) == 0.0:
        return out
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float32)
    ranks[order] = np.linspace(0.0, 1.0, vals.size, dtype=np.float32)
    out[mask] = ranks
    return out


def _read_native(ds: rasterio.DatasetReader, idx: int, valid: np.ndarray) -> np.ndarray:
    a = ds.read(idx).astype(np.float32)
    bad = ~np.isfinite(a) | (a <= NODATA * 0.5) | ~valid
    if bad.any():
        med = float(np.median(a[~bad])) if (~bad).any() else 0.0
        a[bad] = med
    return a


def _read_ext(ext_dir: Path, fname: str, idx: int, valid: np.ndarray) -> np.ndarray:
    with rasterio.open(ext_dir / fname) as ds:
        a = ds.read(idx).astype(np.float32)
    a[~np.isfinite(a) | ~valid] = 0.0
    return a


def salem_multialt_tilt_and_migration(
    field: np.ndarray,
    valid: np.ndarray,
    *,
    z0_m: float = 100.0,
    z1_m: float = 400.0,
    cell_m: float = 100.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute multi-altitude 2-D FFT harmonic Salem-Fairhead (2007) tilt zero-contour
    sharpness at z0 and lateral dip-migration |theta(z1) - theta(z0)| * sech^2(theta(z0)/0.50).

    Properties verified by unit test:
      1. Contrast invariance: multiplying ``field`` by any positive scalar c > 0 leaves
         both outputs invariant (up to machine precision + epsilon stabilizer).
      2. Dip selectivity: a vertical step produces high zero-contour sharpness at x0 and
         near-zero lateral migration, whereas an asymmetric dipping ramp produces strong
         multi-altitude tilt migration toward the hanging wall.
    """
    f = np.asarray(field, dtype=np.float32)
    v = np.asarray(valid, dtype=bool)
    H, W = f.shape

    # Remove ultra-long regional level and feather outside valid over 6 px to prevent wrap-ringing
    f_hp = f - _masked_gaussian(f, v, sigma=36.0)
    taper = ndi.gaussian_filter(v.astype(np.float32), sigma=4.0, mode="constant")
    f_in = np.where(v, f_hp, np.float32(0.0)) * taper
    del f_hp, taper

    spec = rfft2(f_in, s=(H, W))
    del f_in
    ky = fftfreq(H, d=cell_m).astype(np.float32)[:, None]
    kx = rfftfreq(W, d=cell_m).astype(np.float32)[None, :]
    kr = np.sqrt(kx * kx + ky * ky)
    k_nyq = float(0.5 / cell_m)
    anti_ring = np.exp(-((kr / (0.75 * k_nyq)) ** 4)).astype(np.float32)

    def _tilt_at_alt(z_m: float) -> np.ndarray:
        up = np.exp(-2.0 * np.pi * float(z_m) * kr).astype(np.float32) * anti_ring
        phi_z = irfft2(spec * up, s=(H, W)).astype(np.float32)
        dz_phi = irfft2(spec * (2.0 * np.pi * kr * up), s=(H, W)).astype(np.float32)
        gx = ndi.gaussian_filter(phi_z, sigma=1.0, order=(0, 1), mode="nearest") / float(cell_m)
        gy = ndi.gaussian_filter(phi_z, sigma=1.0, order=(1, 0), mode="nearest") / float(cell_m)
        gh = np.hypot(gx, gy)
        eps = float(max(np.percentile(gh[v], 10) * 0.05, 1e-9)) if v.any() else 1e-9
        return np.arctan2(dz_phi, gh + eps).astype(np.float32)

    th0 = _tilt_at_alt(z0_m)
    th1 = _tilt_at_alt(z1_m)
    del spec, kr, anti_ring

    dt_x = ndi.gaussian_filter(th0, sigma=1.2, order=(0, 1), mode="nearest")
    dt_y = ndi.gaussian_filter(th0, sigma=1.2, order=(1, 0), mode="nearest")
    grad_th0 = np.hypot(dt_x, dt_y).astype(np.float32)
    del dt_x, dt_y

    sech0 = (1.0 / np.cosh(np.clip(th0 / 0.35, -8.0, 8.0))) ** 2
    sech_wide = (1.0 / np.cosh(np.clip(th0 / 0.50, -8.0, 8.0))) ** 2
    sharp_z0 = np.where(v, grad_th0 * sech0, np.float32(0.0)).astype(np.float32)
    dip_mig = np.where(v, np.abs(th1 - th0) * sech_wide, np.float32(0.0)).astype(np.float32)
    return sharp_z0, dip_mig


def updip_hangingwall_pullback(
    deep_plane: np.ndarray,
    depth_to_basement_m: np.ndarray,
    valid: np.ndarray,
    *,
    dip_deg: float = 60.0,
    max_shift_px: float = 8.0,
    cell_m: float = 100.0,
    pulled_weight: float = 0.68,
) -> tuple[np.ndarray, np.ndarray]:
    """Project a subsurface fault-step plane up-dip from hanging-wall basin to surface emergence.

    For a fault breaking the surface at x0 and dipping at ``dip_deg`` into the basin along
    u_downdip = +grad(Z_b) / (||grad(Z_b)|| + 5 m/px), the subsurface contact sits at
    x_deep = x0 + ds * u_downdip, where ds = clip((Z_b(x0 + 3*u_downdip)/cell_m)*cot(dip), 0, max_shift).
    Evaluating ``deep_plane`` at x_deep maps buried potential-field/MT steps back onto x0.
    Also returns the hanging-wall rollover keystone curvature (-d^2 Z_b / du^2).
    """
    plane = np.asarray(deep_plane, dtype=np.float32)
    zb = np.maximum(np.asarray(depth_to_basement_m, dtype=np.float32), 0.0)
    v = np.asarray(valid, dtype=bool)
    H, W = plane.shape

    zb_sm = _masked_gaussian(zb, v, sigma=3.5)
    gz_r = ndi.gaussian_filter(zb_sm, sigma=1.5, order=(1, 0), mode="nearest")
    gz_c = ndi.gaussian_filter(zb_sm, sigma=1.5, order=(0, 1), mode="nearest")
    gnorm = np.hypot(gz_r, gz_c) + np.float32(5.0)
    ur = (gz_r / gnorm).astype(np.float32)
    uc = (gz_c / gnorm).astype(np.float32)

    rr, cc = np.indices((H, W), dtype=np.float32)
    zb_ahead = ndi.map_coordinates(
        zb_sm,
        [np.clip(rr + 3.0 * ur, 0.0, H - 1.0), np.clip(cc + 3.0 * uc, 0.0, W - 1.0)],
        order=1,
        mode="nearest",
    )
    cot_dip = float(1.0 / np.tan(np.deg2rad(dip_deg)))
    ds = np.clip((zb_ahead / float(cell_m)) * cot_dip, 0.0, float(max_shift_px)).astype(
        np.float32
    )
    pulled = ndi.map_coordinates(
        plane,
        [np.clip(rr + ds * ur, 0.0, H - 1.0), np.clip(cc + ds * uc, 0.0, W - 1.0)],
        order=1,
        mode="nearest",
    ).astype(np.float32)

    combined = (float(pulled_weight) * pulled + (1.0 - float(pulled_weight)) * plane).astype(
        np.float32
    )
    combined[~v] = 0.0

    # Directional rollover bending curvature along dip normal: -d^2(Z_b)/du^2
    z_rr = ndi.gaussian_filter(zb_sm, sigma=2.5, order=(2, 0), mode="nearest")
    z_cc = ndi.gaussian_filter(zb_sm, sigma=2.5, order=(0, 2), mode="nearest")
    z_rc = ndi.gaussian_filter(zb_sm, sigma=2.5, order=(1, 1), mode="nearest")
    d2z_du2 = ur * ur * z_rr + 2.0 * ur * uc * z_rc + uc * uc * z_cc
    basin_gate = np.exp(-(((zb_sm - 850.0) / 750.0) ** 2)) * (zb_sm > 80.0).astype(np.float32)
    keystone = np.where(v, np.maximum(-d2z_du2, 0.0) * basin_gate, np.float32(0.0)).astype(
        np.float32
    )
    return combined, keystone


def _geodawn_seam_keep_mask(ext_dir: Path, valid: np.ndarray) -> np.ndarray:
    """Compute soft seam-veto weight in [0.15, 1.0] from acquisition_block_id_100m.tif."""
    blk = _read_ext(ext_dir, "acquisition_block_id_100m.tif", 1, valid)
    b_max = ndi.maximum_filter(blk, size=3, mode="nearest")
    b_min = ndi.minimum_filter(blk, size=3, mode="nearest")
    seam = valid & (b_max != b_min) & (b_min > 0)
    seam_halo = ndi.gaussian_filter(
        ndi.binary_dilation(seam, iterations=2).astype(np.float32), sigma=1.2, mode="nearest"
    )
    seam_halo = np.clip(seam_halo / max(float(seam_halo.max()), 1e-6), 0.0, 1.0)
    return np.where(valid, 1.0 - 0.80 * seam_halo, np.float32(0.0)).astype(np.float32)


def _gdr_geothermal_planes(
    ext_dir: Path,
    valid: np.ndarray,
    dem_mean: np.ndarray,
    accessed_columns: dict[str, tuple[str, ...]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build (uphead_geotherm_diseq, probe2m_uphead_wall, paleo_sinter_corridor, iso_geoth_ablation)
    without ever reading ``dist_known_fault_px``."""
    shape = valid.shape

    # Smooth topographic hydraulic head for up-gradient vector +grad(z_DEM)
    dem_sm = _masked_gaussian(dem_mean, valid, sigma=6.0)
    gr = ndi.gaussian_filter(dem_sm, sigma=2.5, order=(1, 0), mode="nearest")
    gc_ = ndi.gaussian_filter(dem_sm, sigma=2.5, order=(0, 1), mode="nearest")
    gn = np.hypot(gr, gc_) + np.float32(1.5)
    ur_up = (gr / gn).astype(np.float32)
    uc_up = (gc_ / gn).astype(np.float32)
    del dem_sm, gr, gc_, gn

    # 1. Well & spring Fournier geothermometer disequilibrium (up-head shifted vs isotropic ablation)
    ws_cols = ("row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c")
    assert not (set(ws_cols) & BANNED_CSV_COLUMNS)
    accessed_columns["gdr_wellspring_in_footprint.csv"] = ws_cols

    imp_up = np.zeros(shape, dtype=np.float32)
    imp_iso = np.zeros(shape, dtype=np.float32)
    with (ext_dir / "gdr_wellspring_in_footprint.csv").open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or not set(ws_cols).issubset(reader.fieldnames):
            raise RuntimeError("Unexpected header in gdr_wellspring_in_footprint.csv")
        for row in reader:
            try:
                r = int(row["row"])
                c = int(row["col"])
            except (KeyError, ValueError):
                continue
            if not (0 <= r < shape[0] and 0 <= c < shape[1]) or not valid[r, c]:
                continue
            t_meas = float(row["temp_c"]) if row.get("temp_c") else 0.0
            t_qtz = float(row["geothermquartz_c"]) if row.get("geothermquartz_c") else 0.0
            t_ch = float(row["geothermchalc_c"]) if row.get("geothermchalc_c") else 0.0
            t_cat = float(row["geothermcat_c"]) if row.get("geothermcat_c") else 0.0
            t_res = max(t_qtz, t_ch, min(t_cat, 260.0))
            diseq = max(t_res - max(t_meas, 14.0), 0.0) / 85.0
            direct = max(t_meas - 20.0, 0.0) / 45.0
            score = float(min(0.65 * diseq + 0.35 * max(t_res - 75.0, 0.0) / 95.0 + 0.30 * direct, 5.0))
            if score <= 0.02:
                continue
            if score > imp_iso[r, c]:
                imp_iso[r, c] = score
            ru = int(np.clip(round(r + 3.5 * float(ur_up[r, c])), 0, shape[0] - 1))
            cu = int(np.clip(round(c + 3.5 * float(uc_up[r, c])), 0, shape[1] - 1))
            if score > imp_up[ru, cu]:
                imp_up[ru, cu] = score

    uphead_diseq = (
        0.65 * ndi.gaussian_filter(imp_up, sigma=4.5, mode="constant")
        + 0.35 * ndi.gaussian_filter(imp_up, sigma=13.0, mode="constant")
    ).astype(np.float32)
    iso_geoth = ndi.gaussian_filter(imp_iso, sigma=10.0, mode="constant").astype(np.float32)
    uphead_diseq[~valid] = 0.0
    iso_geoth[~valid] = 0.0
    del imp_up, imp_iso

    # 2. DOE GDR #1391 2-m temperature probes (3,800 sites) up-head thermal wall
    with zipfile.ZipFile(ext_dir / "2m_temperature_probe_INGENIOUS_regional_data.zip") as zf:
        dbf = zf.read(
            "2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf"
        )
        shp = zf.read(
            "2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.shp"
        )
    nrec, hdr_len, rec_len = struct.unpack("<IHH", dbf[4:12])
    fields: list[tuple[str, int]] = []
    pos = 32
    while dbf[pos] != 0x0D:
        fields.append((dbf[pos : pos + 11].split(b"\x00")[0].decode("ascii"), dbf[pos + 16]))
        pos += 32
    accessed_columns["2m_temperature_probe_n83geo.dbf"] = ("F2mDAB",)

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
        f2m_val = 0.0
        for fn, fl in fields:
            if fn == "F2mDAB":
                txt = row_bytes[off : off + fl].decode("utf-8", errors="replace").strip()
                f2m_val = float(txt) if txt else 0.0
            off += fl
        lons.append(x)
        lats.append(y)
        dabs.append(f2m_val)
    del dbf, shp

    xs, ys = warp_transform("EPSG:4269", "EPSG:32611", lons, lats)
    cols = np.floor((np.asarray(xs) - 243350.0) / 100.0).astype(np.int32)
    rows = np.floor((4508550.0 - np.asarray(ys)) / 100.0).astype(np.int32)
    inb = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])

    p_anom = np.zeros(shape, dtype=np.float32)
    p_cnt = np.zeros(shape, dtype=np.float32)
    dab_pos = np.clip(np.nan_to_num(np.asarray(dabs, dtype=np.float32), nan=0.0), 0.0, 15.0)
    r_ib = rows[inb]
    c_ib = cols[inb]
    # Shift probe observations 2.5 px up hydraulic head before smoothing
    r_sh = np.clip(np.rint(r_ib + 2.5 * ur_up[r_ib, c_ib]).astype(np.int32), 0, shape[0] - 1)
    c_sh = np.clip(np.rint(c_ib + 2.5 * uc_up[r_ib, c_ib]).astype(np.int32), 0, shape[1] - 1)
    np.maximum.at(p_anom, (r_sh, c_sh), dab_pos[inb])
    np.add.at(p_cnt, (r_sh, c_sh), 1.0)
    del ur_up, uc_up

    num = ndi.gaussian_filter(p_anom, sigma=8.5, mode="constant")
    den = ndi.gaussian_filter((p_cnt > 0).astype(np.float32), sigma=8.5, mode="constant")
    plume = (num / (den + 0.01)).astype(np.float32)
    del p_anom, p_cnt, num, den
    ty = ndi.gaussian_filter(plume, sigma=3.5, order=(1, 0), mode="nearest")
    tx = ndi.gaussian_filter(plume, sigma=3.5, order=(0, 1), mode="nearest")
    t_wall = np.hypot(ty, tx).astype(np.float32)
    probe_wall = np.where(
        valid, 0.58 * _rank01(t_wall, valid) + 0.42 * _rank01(plume, valid), np.float32(0.0)
    ).astype(np.float32)
    del plume, ty, tx, t_wall

    # 3. Paleo-geothermal sinter/travertine/tufa (726 sites) + Quaternary volcanic vents
    with zipfile.ZipFile(ext_dir / "paleo_geothermal_regional.zip") as zf:
        lines = zf.read("Paleo_geothermal_final.csv").decode("utf-8", errors="replace").splitlines()
    accessed_columns["Paleo_geothermal_final.csv"] = ("Long_deg_NAD83", "Lat_deg_NAD83")
    slons: list[float] = []
    slats: list[float] = []
    for row in csv.DictReader(lines):
        try:
            slons.append(float(row["Long_deg_NAD83"]))
            slats.append(float(row["Lat_deg_NAD83"]))
        except (KeyError, ValueError):
            continue
    sxs, sys_ = warp_transform("EPSG:4269", "EPSG:32611", slons, slats)
    scols = np.floor((np.asarray(sxs) - 243350.0) / 100.0).astype(np.int32)
    srows = np.floor((4508550.0 - np.asarray(sys_)) / 100.0).astype(np.int32)
    sinb = (srows >= 0) & (srows < shape[0]) & (scols >= 0) & (scols < shape[1])
    vent_src = np.zeros(shape, dtype=bool)
    vent_src[srows[sinb], scols[sinb]] = True

    vv_cols = ("row", "col")
    assert not (set(vv_cols) & BANNED_CSV_COLUMNS)
    accessed_columns["gdr_volcanic_vents_in_footprint.csv"] = vv_cols
    with (ext_dir / "gdr_volcanic_vents_in_footprint.csv").open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                vr = int(row["row"])
                vc = int(row["col"])
            except (KeyError, ValueError):
                continue
            if 0 <= vr < shape[0] and 0 <= vc < shape[1]:
                vent_src[vr, vc] = True

    d_vent = ndi.distance_transform_edt(~vent_src).astype(np.float32)
    sinter_corridor = np.where(
        valid,
        0.65 * np.exp(-d_vent / 6.5) + 0.35 * np.exp(-d_vent / 20.0),
        np.float32(0.0),
    ).astype(np.float32)
    del vent_src, d_vent
    return uphead_diseq, probe_wall, sinter_corridor, iso_geoth


def build_stdp_static_stack(
    feature_tif: Path,
    ext_dir: Path,
    *,
    out_stdp_path: Path | None = None,
    out_ablation_path: Path | None = None,
    footprint: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """Stream all 24 H86K-STDP planes + L_stdp corroboration + 8 ablation planes
    into float16 disk-backed memmaps within < 900 MiB peak RSS."""
    qc = verify_stdp_input_contract(ext_dir)
    accessed_cols: dict[str, tuple[str, ...]] = {}

    with rasterio.open(feature_tif) as ds:
        H, W = ds.height, ds.width
        b2_probe = ds.read(2).astype(np.float32)
        feat_valid = np.isfinite(b2_probe) & (b2_probe > NODATA * 0.5)
        del b2_probe

    valid = feat_valid if footprint is None else (feat_valid & np.asarray(footprint, dtype=bool))
    n_stdp = len(STDP_STATIC_NAMES)
    n_abl = len(ABLATION_LOCAL_NAMES)

    if out_stdp_path is not None:
        out_stdp_path.parent.mkdir(parents=True, exist_ok=True)
        X_stdp = open_memmap(out_stdp_path, mode="w+", dtype=np.float16, shape=(n_stdp, H, W))
    else:
        X_stdp = np.zeros((n_stdp, H, W), dtype=np.float16)

    if out_ablation_path is not None:
        out_ablation_path.parent.mkdir(parents=True, exist_ok=True)
        X_abl = open_memmap(out_ablation_path, mode="w+", dtype=np.float16, shape=(n_abl, H, W))
    else:
        X_abl = np.zeros((n_abl, H, W), dtype=np.float16)

    def _put_stdp(name: str, arr: np.ndarray) -> None:
        idx = STDP_STATIC_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_stdp[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    def _put_abl(name: str, arr: np.ndarray) -> None:
        idx = ABLATION_LOCAL_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_abl[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    seam_keep = _geodawn_seam_keep_mask(ext_dir, valid)

    fam_pullback = np.zeros((H, W), dtype=np.float32)
    fam_geotherm = np.zeros((H, W), dtype=np.float32)
    fam_scarp = np.zeros((H, W), dtype=np.float32)
    fam_tect = np.zeros((H, W), dtype=np.float32)

    with rasterio.open(feature_tif) as ds:
        # 1. Basement depth Z_b + Multi-altitude Salem Tilt on RTP & Gravity + Up-Dip Pullback
        zb_m = _read_native(ds, 15, valid)
        z_gx, z_gy = _masked_gradients(zb_m, valid, sigma=3.0)
        _put_abl("local_depth_gradmag_s3", np.hypot(z_gx, z_gy))
        del z_gx, z_gy

        b2 = _read_native(ds, 2, valid)
        rtp_gx, rtp_gy = _masked_gradients(b2, valid, sigma=2.0)
        _put_abl("local_rtp_gradmag_s2", np.hypot(rtp_gx, rtp_gy))
        del rtp_gx, rtp_gy

        salem_rtp_z0, salem_rtp_mig = salem_multialt_tilt_and_migration(b2, valid)
        salem_rtp_z0 = (salem_rtp_z0 * seam_keep).astype(np.float32)
        salem_rtp_mig = (salem_rtp_mig * seam_keep).astype(np.float32)
        _put_stdp("salem_rtp_tilt_zero_z100", salem_rtp_z0)
        _put_stdp("salem_rtp_dip_migration", salem_rtp_mig)
        mpc_rtp, _, _ = riesz_monogenic_phase_congruency(b2, valid)
        mpc_rtp = (mpc_rtp * seam_keep).astype(np.float32)

        # Hydrothermal magnetite destruction along structural steps: local RTP laplacian trough
        rtp_trough = np.maximum(_masked_gaussian(b2, valid, 9.0) - _masked_gaussian(b2, valid, 2.0), 0.0)
        del b2
        gc.collect()

        b13 = _read_native(ds, 13, valid)
        b5 = _read_native(ds, 5, valid)
        _put_abl("local_grav_slope_b5", b5)
        del b5

        salem_grav_z0, salem_grav_mig = salem_multialt_tilt_and_migration(b13, valid)
        _put_stdp("salem_grav_tilt_zero_z100", salem_grav_z0)
        _put_stdp("salem_grav_dip_migration", salem_grav_mig)
        mpc_grav, _, _ = riesz_monogenic_phase_congruency(b13, valid)
        del b13

        # Up-dip hanging-wall pullback onto near-surface fault emergence
        pull_grav, keystone_raw = updip_hangingwall_pullback(salem_grav_z0, zb_m, valid)
        _put_stdp("updip_pullback_grav_step", pull_grav)
        pull_rtp, _ = updip_hangingwall_pullback(salem_rtp_z0, zb_m, valid)
        _put_stdp("updip_pullback_rtp_step", pull_rtp)
        mono_joint = (0.55 * mpc_grav + 0.45 * mpc_rtp).astype(np.float32)
        pull_mono, _ = updip_hangingwall_pullback(mono_joint, zb_m, valid)
        _put_stdp("updip_pullback_monogenic", pull_mono)

        keystone = (keystone_raw * (0.35 + 0.65 * mono_joint)).astype(np.float32)
        _put_stdp("intrabasin_keystone_hinge", keystone)
        del keystone_raw, salem_rtp_z0, salem_rtp_mig, salem_grav_z0, salem_grav_mig

        hydro_demag = (_rank01(rtp_trough, valid) * (0.55 * mpc_grav + 0.45 * _rank01(pull_grav, valid)) * seam_keep).astype(
            np.float32
        )
        del rtp_trough, mpc_rtp, mpc_grav, mono_joint
        _put_stdp("hydro_magnetite_destruction", hydro_demag)

        fam_pullback += (
            0.30 * _rank01(pull_grav, valid)
            + 0.24 * _rank01(pull_rtp, valid)
            + 0.30 * _rank01(pull_mono, valid)
            + 0.16 * _rank01(keystone, valid)
        )
        del pull_rtp, keystone
        gc.collect()

        # 2. Upward-continuation TMI wavenumber SI + Conductive fault-gouge up-dip pullback
        b3 = _read_native(ds, 3, valid)
        b9 = _read_native(ds, 9, valid)
        h_tmi0 = np.hypot(b3, b9)
        del b3, b9
        tmi150 = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 4, valid)
        ux, uy = _masked_gradients(tmi150, valid, sigma=1.8)
        del tmi150
        h_tmi150 = np.hypot(ux, uy)
        del ux, uy
        r0 = _rank01(h_tmi0, valid)
        r150 = _rank01(h_tmi150, valid)
        del h_tmi0, h_tmi150
        wavenumber_si = (np.sqrt(r0 * r150 + 1e-8) * (1.0 - np.abs(r0 - r150)) * seam_keep).astype(
            np.float32
        )
        del r0, r150
        _put_stdp("tmi_up150_wavenumber_si", wavenumber_si)
        fam_pullback += 0.14 * _rank01(wavenumber_si, valid)
        del wavenumber_si

        b17 = _read_native(ds, 17, valid)
        cond_log = np.log1p(np.maximum(b17 - float(np.min(b17[valid])), 0.0))
        del b17
        cond_ridge, cond_ecc = _hessian_ridge_and_eccentricity(cond_log, valid, sigma=2.4)
        del cond_log
        cond_neck_raw = (cond_ridge * (cond_ecc**2)).astype(np.float32)
        del cond_ridge, cond_ecc
        pull_cond, _ = updip_hangingwall_pullback(cond_neck_raw, zb_m, valid)
        del cond_neck_raw, zb_m
        _put_stdp("updip_pullback_cond_neck", pull_cond)
        fam_geotherm += 0.22 * _rank01(pull_cond, valid) + 0.16 * _rank01(hydro_demag, valid)
        del pull_cond, hydro_demag
        gc.collect()

        # 3. Aseismic Transtensional Strain-Energy Deficit & Microseismic Swarms
        b4 = _read_native(ds, 4, valid)
        b7 = _read_native(ds, 7, valid)
        b8 = _read_native(ds, 8, valid)
        inv_hp = b4 - _masked_gaussian(b4, valid, 24.0)
        _put_abl("local_strain_2ndinv_hp", inv_hp)
        dil_hp = np.maximum(b8 - _masked_gaussian(b8, valid, 24.0), 0.0)
        shr_hp = np.maximum(b7 - _masked_gaussian(b7, valid, 24.0), 0.0)
        del b4, b7, b8
        transtens = (np.sqrt(shr_hp * dil_hp + 1e-12) + 0.35 * np.maximum(inv_hp, 0.0)).astype(
            np.float32
        )
        del inv_hp, dil_hp, shr_hp
        _put_stdp("transtens_strain_rate_hp", transtens)

        b10 = _read_native(ds, 10, valid)
        b16 = _read_native(ds, 16, valid)
        eq_prox = np.exp(-np.maximum(b10, 0.0) / float(np.median(b10[valid]) + 1e-6))
        eq_hp = eq_prox - _masked_gaussian(eq_prox, valid, 24.0)
        ieq_hp = b16 - _masked_gaussian(b16, valid, 24.0)
        del b10, b16, eq_prox
        swarm_hp = (_rank01(eq_hp, valid) + 0.5 * _rank01(ieq_hp, valid)).astype(np.float32)
        _put_stdp("microseismic_swarm_hp", swarm_hp)

        # Contrarian aseismic creep/locked-fault deficit: high transtensional strain minus historical seismicity
        z_str = _robust_pos_z(transtens, valid)
        z_ieq = _robust_pos_z(ieq_hp, valid)
        creep_def = np.where(valid, np.maximum(z_str - 0.65 * np.maximum(z_ieq, 0.0), 0.0), np.float32(0.0)).astype(
            np.float32
        )
        del eq_hp, ieq_hp, z_str, z_ieq
        _put_stdp("aseismic_creep_deficit", creep_def)
        fam_tect += (
            0.28 * _rank01(transtens, valid)
            + 0.22 * _rank01(creep_def, valid)
            + 0.14 * _rank01(swarm_hp, valid)
        )
        del transtens, creep_def, swarm_hp

        b19 = _read_native(ds, 19, valid)
        _put_abl("local_elev_slope_b19", b19)
        b12 = _read_native(ds, 12, valid)
        elev_ridge, _ = _hessian_ridge_and_eccentricity(b12, valid, sigma=2.0)
        del b12
        slope_rel = b19 / (_masked_gaussian(b19, valid, 12.0) + float(np.percentile(b19[valid], 25) + 1e-4))
        del b19
        gc.collect()

    # 4. External DOE GDR #1391 Up-Head Geothermal Conduits + Seam-Free GeoDAWN Radiometrics
    z_m = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 5, valid)
    lahontan_band = np.exp(-(((z_m - 1330.0) / 18.0) ** 2)) + 0.65 * np.exp(
        -(((z_m - 1205.0) / 15.0) ** 2)
    )
    lahontan_band = np.where(valid & (z_m > 900.0), lahontan_band, 0.0).astype(np.float32)

    uphead_diseq, probe_wall, sinter_corr, iso_geoth = _gdr_geothermal_planes(
        ext_dir, valid, z_m, accessed_cols
    )
    del z_m
    _put_abl("local_geotherm_iso_blur", iso_geoth)
    del iso_geoth
    # Structural corroboration weight so point geothermal observations track fault conduits
    struct_gate = (0.30 + 0.70 * (0.55 * _rank01(pull_mono, valid) + 0.45 * _rank01(pull_grav, valid))).astype(
        np.float32
    )
    uphead_diseq_g = (uphead_diseq * struct_gate).astype(np.float32)
    probe_wall_g = (probe_wall * struct_gate).astype(np.float32)
    sinter_corr_g = (sinter_corr * struct_gate).astype(np.float32)
    del uphead_diseq, probe_wall, sinter_corr, struct_gate
    _put_stdp("uphead_geotherm_diseq", uphead_diseq_g)
    _put_stdp("probe2m_uphead_thermal_wall", probe_wall_g)
    _put_stdp("paleo_sinter_vent_corridor", sinter_corr_g)
    fam_geotherm += (
        0.18 * _rank01(uphead_diseq_g, valid)
        + 0.16 * _rank01(probe_wall_g, valid)
        + 0.12 * _rank01(sinter_corr_g, valid)
    )
    del uphead_diseq_g, probe_wall_g, sinter_corr_g

    rad_K = _read_ext(ext_dir, "geodawn_rad_u8.tif", 1, valid)
    rad_Th = _read_ext(ext_dir, "geodawn_rad_u8.tif", 2, valid)
    ext_ThK = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 1, valid)
    kth_ratio = (rad_K + 1.0) / (rad_Th + 8.0) - 0.35 * (ext_ThK / 255.0)
    del rad_K, ext_ThK
    kth_gx, kth_gy = _masked_gradients(kth_ratio, valid, sigma=1.8)
    del kth_ratio
    rad_kth = (np.hypot(kth_gx, kth_gy) * seam_keep * (1.0 - 0.55 * lahontan_band)).astype(np.float32)
    del kth_gx, kth_gy
    _put_stdp("rad_kth_alteration_seamfree", rad_kth)

    rad_U = _read_ext(ext_dir, "geodawn_rad_u8.tif", 3, valid)
    ext_UTh = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 3, valid)
    uth_field = 0.6 * (ext_UTh / 255.0) + 0.4 * ((rad_U + 1.0) / (rad_Th + 8.0))
    del rad_U, rad_Th, ext_UTh
    uth_gx, uth_gy = _masked_gradients(uth_field, valid, sigma=1.8)
    del uth_field
    rad_uth = (np.hypot(uth_gx, uth_gy) * seam_keep * (1.0 - 0.40 * lahontan_band)).astype(np.float32)
    del uth_gx, uth_gy, seam_keep
    _put_stdp("rad_uth_redox_seamfree", rad_uth)
    fam_geotherm += 0.16 * _rank01(rad_kth, valid)
    del rad_kth, rad_uth
    gc.collect()

    # 5. Swath-Debiased 3DEP 1 m LiDAR + 10 m DEMPiedmont Curvature + Fluvial Chi Knickzones
    topo_asp = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 7, valid)
    lahontan_mimic = np.where(
        valid,
        np.clip(
            lahontan_band * (topo_asp / 255.0) * (1.0 - np.clip(_rank01(pull_grav, valid), 0.0, 1.0)),
            0.0,
            1.0,
        ),
        np.float32(0.0),
    ).astype(np.float32)
    del lahontan_band

    topo_curv = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 6, valid)
    topo_hs = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 8, valid)
    topo10_pied = (
        (
            0.40 * (topo_hs / 255.0)
            + 0.35 * (topo_curv / 255.0)
            + 0.25 * (0.6 * np.clip(slope_rel / 3.0, 0.0, 1.5) + 0.4 * _rank01(elev_ridge, valid))
        )
        * (0.4 + 0.6 * (topo_asp / 255.0))
        * (1.0 - 0.55 * lahontan_mimic)
    ).astype(np.float32)
    del topo_curv, topo_hs, topo_asp, slope_rel, elev_ridge
    _put_stdp("topo10_piedmont_curv_break", topo10_pied)
    fam_scarp += 0.34 * _rank01(topo10_pied, valid)

    topo_slope_10m = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 1, valid) / 255.0
    _put_abl("local_topo10_slope_p90", topo_slope_10m)

    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as lds:
        li_has = valid & (lds.read(12) > 0)
    li_miss = valid & ~li_has

    def _put_lidar_swath_debiased(
        target_mm: np.ndarray, idx: int, arr_obs: np.ndarray, fb_10m: np.ndarray
    ) -> np.ndarray:
        z_obs = _robust_pos_z(arr_obs, li_has)
        z_fb = _robust_pos_z(fb_10m, li_miss) if np.any(li_miss) else np.zeros_like(z_obs)
        merged_z = np.zeros(valid.shape, dtype=np.float32)
        merged_z[li_has] = z_obs[li_has]
        merged_z[li_miss] = z_fb[li_miss]
        target_mm[idx] = np.clip(merged_z, -32.0, 32.0).astype(np.float16)

        r_obs = _rank01(arr_obs, li_has)
        r_fb = _rank01(fb_10m, li_miss) if np.any(li_miss) else np.zeros_like(r_obs)
        merged_r = np.zeros(valid.shape, dtype=np.float32)
        merged_r[li_has] = r_obs[li_has]
        merged_r[li_miss] = r_fb[li_miss]
        return merged_r

    li_step = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 3, valid)
    _put_lidar_swath_debiased(
        X_abl, ABLATION_LOCAL_NAMES.index("local_lidar_step_debiased"), li_step / 255.0, topo_slope_10m
    )
    del topo_slope_10m

    li_cross = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 8, valid)
    li_coh = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 10, valid)
    li_scarp = (
        (li_step / 255.0)
        * (0.5 + 0.5 * (li_cross / 255.0))
        * (0.35 + 0.65 * (li_coh / 255.0))
        * (1.0 - 0.65 * lahontan_mimic)
    ).astype(np.float32)
    del li_step, li_cross
    li_scarp_r = _put_lidar_swath_debiased(
        X_stdp, STDP_STATIC_NAMES.index("lidar1m_scarp_swath_debiased"), li_scarp, topo10_pied
    )
    fam_scarp += 0.42 * li_scarp_r

    li_dn = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 6, valid)
    li_up = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 7, valid)
    li_ln = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 4, valid)
    li_lp = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 5, valid)
    li_dip = (
        (np.maximum(li_dn, li_up) / 255.0)
        * np.sqrt((li_ln / 255.0) * (li_lp / 255.0) + 1e-6)
        * (0.4 + 0.6 * (li_coh / 255.0))
    ).astype(np.float32)
    del li_dn, li_up, li_ln, li_lp, li_coh
    li_dip_r = _put_lidar_swath_debiased(
        X_stdp, STDP_STATIC_NAMES.index("lidar1m_curv_dipole_debiased"), li_dip, topo10_pied
    )
    fam_scarp += 0.24 * li_dip_r
    del li_scarp, li_dip, li_dip_r, li_has, li_miss

    # Multi-physics pulled-back fault-intersection invariant (Faulds & Hinz 2015)
    comp_trace = (
        0.38 * _rank01(pull_grav, valid)
        + 0.26 * _rank01(pull_mono, valid)
        + 0.22 * li_scarp_r
        + 0.14 * _rank01(topo10_pied, valid)
    ).astype(np.float32)
    del pull_grav, pull_mono, li_scarp_r, topo10_pied
    conj_inter = _structure_tensor_intersection(comp_trace, valid, sigma_grad=1.2, sigma_int=4.0)
    del comp_trace
    _put_stdp("geotherm_conjugate_intersect", conj_inter)
    fam_geotherm += 0.24 * _rank01(conj_inter, valid)
    del conj_inter

    chi_step = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 1, valid)
    chi_ksn = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 3, valid)
    chi_area = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 4, valid)
    area_norm = np.clip((chi_area / 1000.0 - 4.0) / 3.0, 0.2, 1.5)
    del chi_area
    chi_knick = (
        0.6 * _rank01(np.maximum(chi_step, 0.0) / area_norm, valid)
        + 0.4 * _rank01(np.maximum(chi_ksn, 0.0), valid)
    ).astype(np.float32)
    del chi_step, chi_ksn, area_norm
    _put_stdp("chi10_drainage_knick_step", chi_knick)
    fam_tect += 0.36 * _rank01(chi_knick, valid)
    del chi_knick

    L_raw = (
        0.36 * fam_pullback
        + 0.22 * fam_geotherm
        + 0.28 * fam_scarp
        + 0.14 * fam_tect
        - 0.18 * lahontan_mimic
    )
    del fam_pullback, fam_geotherm, fam_scarp, fam_tect, lahontan_mimic
    L_stdp = _rank01(L_raw, valid)
    del L_raw
    gc.collect()

    if out_stdp_path is not None:
        X_stdp.flush()
        del X_stdp
        X_stdp = np.load(out_stdp_path, mmap_mode="r")
    if out_ablation_path is not None:
        X_abl.flush()
        del X_abl
        X_abl = np.load(out_ablation_path, mmap_mode="r")

    qc["accessed_csv_columns"] = {k: list(v) for k, v in accessed_cols.items()}
    return X_stdp, L_stdp, X_abl, valid, qc
