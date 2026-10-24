"""Feature engineering and visible-only kinematic fields for Lane H86B-GFCO.

All 38 physical, geothermal, and geomorphic planes are strictly label-free:
- Zero bytes read from `existing_faults.tif`, `labels.tif`, or `derived_sgmc_faults_100m_u8.tif`.
- The `dist_known_fault_px` column in GDR-1391 CSVs is explicitly forbidden and never read.
- Each plane is persisted as float32 on disk (`data/cache/h86b_planes/*.npy`) and
  opened via `mmap_mode='r'` so peak RAM stays well below 1 GiB.

Visible-only kinematic fields (`compute_kinematic_components`) take ONLY the fold's
`visible` fault mask (`ctx.visible(cell.key)` or `comp_fold['visible']`) and reuse
`vendor/gems57/faultzone._fragment_stats`, `vendor/gems57/relay_bend_anatomy.two_host_frame`,
and `vendor/gems57/relay_bend_anatomy.host_bend_fields` without modifying `vendor/gems57`.
"""
from __future__ import annotations

import csv
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.linear_model import HuberRegressor

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))
if "gems57" in sys.modules and hasattr(sys.modules["gems57"], "__path__"):
    _vg = str(ROOT / "vendor" / "gems57")
    if _vg not in sys.modules["gems57"].__path__:
        sys.modules["gems57"].__path__.append(_vg)

from gems57 import grid as G
from gems57.faultzone import _fragment_stats
from gems57.relay_bend_anatomy import host_bend_fields, two_host_frame

PLANE_DIR = ROOT / "data" / "cache" / "h86b_planes"

PHYS_FEATURES: tuple[str, ...] = (
    # Block 1: Geothermal vent & blind hydrothermal upflow plumes (8)
    "gt_diseq_s8",
    "gt_diseq_s25",
    "gt_kinlag_s15",
    "gt_thermal_s12",
    "mt_cond_z",
    "mt_cond_grad",
    "mt_cond_ridge",
    "gt_conduit_couple",
    # Block 2: Multi-depth potential-field contact-offset & upward-continuation (12)
    "mag_rtp_grad_s1",
    "mag_rtp_ridge_s1",
    "mag_rtp_ridge_s3",
    "mag_tc_z",
    "mag_tmi_hg_z",
    "mag_verduzco_tilt_grad",
    "mag_up150_atten_grad",
    "mag_turn_disruption",
    "grav_hg_z",
    "grav_tilt_grad",
    "contact_offset_grav_mag",
    "grav_mag_concord",
    # Block 3: Subsurface basement-cover & geodetic transtensional strain (6)
    "base_depth_z",
    "base_step_grad",
    "base_step_ridge",
    "strain_2ndinv_z",
    "strain_dilat_z",
    "strain_transtension",
    # Block 4: 1 m LiDAR scarplets, 100 m geomorphic ridges & rad-topo discordance (12)
    "lidar_valid",
    "lidar_step_z",
    "lidar_ex_z",
    "lidar_face_asym",
    "lidar_piedmont_scarp",
    "lidar_chain_vote",
    "dem_elev_z",
    "dem_slope_z",
    "dem_piedmont_hinge",
    "dem_valley_chain",
    "rad_topo_discord_K",
    "rad_topo_discord_UTh",
)

FORBIDDEN_CSV_COLUMNS = frozenset({"dist_known_fault_px"})


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean_band(a: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ok = valid & np.isfinite(a) & (np.abs(a) < 1e18)
    med = float(np.median(a[ok])) if ok.any() else 0.0
    out = np.where(ok, a, med).astype(np.float32)
    return out, ok


def _robust_z(a: np.ndarray, valid: np.ndarray, clip: float = 8.0) -> np.ndarray:
    out = np.zeros(a.shape, dtype=np.float32)
    ok = valid & np.isfinite(a)
    if not ok.any():
        return out
    vals = a[ok]
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med))) * 1.4826
    if not np.isfinite(mad) or mad < 1e-6:
        mad = max(float(np.std(vals)), 1e-6)
    z = np.clip((vals - med) / mad, -clip, clip)
    out[ok] = z.astype(np.float32)
    return out


def _pos_unit(a: np.ndarray, valid: np.ndarray, pct: float = 99.0) -> np.ndarray:
    out = np.zeros(a.shape, dtype=np.float32)
    ok = valid & np.isfinite(a)
    if not ok.any():
        return out
    vals = a[ok]
    lo = float(np.percentile(vals, 5.0))
    hi = float(np.percentile(vals, pct))
    scale = max(hi - lo, 1e-6)
    out[ok] = np.clip((vals - lo) / scale, 0.0, 1.0).astype(np.float32)
    return out


def _grad_mag(a: np.ndarray, sigma: float) -> np.ndarray:
    gy = ndi.gaussian_filter(a, sigma, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(a, sigma, order=(0, 1), mode="nearest")
    return np.hypot(gx, gy).astype(np.float32)


def _hessian_sym_ridge(a: np.ndarray, sigma: float, mode_sign: str = "both") -> np.ndarray:
    """Scale-normalized Hessian ridge/trough strength (sigma^2 * principal curvature)."""
    s2 = np.float32(sigma * sigma)
    axx = ndi.gaussian_filter(a, sigma, order=(0, 2), mode="nearest") * s2
    ayy = ndi.gaussian_filter(a, sigma, order=(2, 0), mode="nearest") * s2
    axy = ndi.gaussian_filter(a, sigma, order=(1, 1), mode="nearest") * s2
    tr = 0.5 * (axx + ayy)
    rad = np.sqrt(np.maximum(0.25 * (axx - ayy) ** 2 + axy * axy, 0.0))
    l1 = tr + rad
    l2 = tr - rad
    if mode_sign == "ridge":
        # local maximum ridge has negative principal curvature (-l2 > 0)
        return np.maximum(-l2, 0.0).astype(np.float32)
    if mode_sign == "valley":
        # local minimum trough/valley has positive principal curvature (l1 > 0)
        return np.maximum(l1, 0.0).astype(np.float32)
    return np.maximum(np.abs(l1), np.abs(l2)).astype(np.float32)


def _structure_director(a: np.ndarray, grad_sigma: float, tensor_sigma: float):
    """Spin-2 structure-tensor director (tx, ty, coherence) of scalar field `a`."""
    gy = ndi.gaussian_filter(a, grad_sigma, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(a, grad_sigma, order=(0, 1), mode="nearest")
    jxx = ndi.gaussian_filter(gx * gx, tensor_sigma, mode="nearest")
    jyy = ndi.gaussian_filter(gy * gy, tensor_sigma, mode="nearest")
    jxy = ndi.gaussian_filter(gx * gy, tensor_sigma, mode="nearest")
    tr = np.maximum(jxx + jyy, 1e-12)
    # Edge tangent has cos(2*theta_strike) = -(jxx - jyy)/norm, sin(2*theta_strike) = -2*jxy/norm;
    # up to shared sign convention, (jxx - jyy)/tr and 2*jxy/tr encode axial orientation cleanly.
    dx = (jxx - jyy) / tr
    dy = (2.0 * jxy) / tr
    coh = np.clip(np.hypot(dx, dy), 0.0, 1.0).astype(np.float32)
    return dx.astype(np.float32), dy.astype(np.float32), coh


def _axial_chain_excess(field: np.ndarray, length: int = 9, n_angles: int = 8) -> np.ndarray:
    """Directional collinearity excess: max_theta(mean along line) - isotropic mean."""
    half = length // 2
    acc_sum = np.zeros(field.shape, dtype=np.float32)
    acc_max = np.full(field.shape, -1e9, dtype=np.float32)
    t_vals = np.linspace(-half, half, length)
    for k in range(n_angles):
        ang = np.pi * k / n_angles
        ker = np.zeros((length, length), dtype=np.float32)
        rr = np.clip(np.rint(half + t_vals * np.sin(ang)).astype(int), 0, length - 1)
        cc = np.clip(np.rint(half + t_vals * np.cos(ang)).astype(int), 0, length - 1)
        ker[rr, cc] = 1.0
        ker /= max(float(ker.sum()), 1.0)
        resp = ndi.convolve(field, ker, mode="constant", cval=0.0)
        np.maximum(acc_max, resp, out=acc_max)
        acc_sum += resp
    return np.maximum(acc_max - acc_sum / float(n_angles), 0.0).astype(np.float32)


def _save_plane(name: str, arr: np.ndarray, footprint: np.ndarray) -> dict:
    PLANE_DIR.mkdir(parents=True, exist_ok=True)
    out = np.where(footprint & np.isfinite(arr), arr, 0.0).astype(np.float32)
    path = PLANE_DIR / f"{name}.npy"
    np.save(path, out)
    return dict(
        name=name,
        file=str(path.relative_to(ROOT)),
        sha256=_sha256_file(path),
        min=float(out[footprint].min()),
        max=float(out[footprint].max()),
        std=float(out[footprint].std()),
    )


def build_physical_planes(data_dir: Path | None = None, force: bool = False) -> dict:
    """Build or verify all 38 label-free physical/geothermal/geomorphic planes."""
    d = Path(data_dir) if data_dir else ROOT / "data"
    manifest_path = PLANE_DIR / "manifest.json"
    if not force and manifest_path.is_file():
        man = json.loads(manifest_path.read_text())
        if [p["name"] for p in man.get("planes", [])] == list(PHYS_FEATURES) and all(
            (ROOT / p["file"]).is_file() for p in man["planes"]
        ):
            return man

    t0 = time.time()
    # Read ONLY sample_submission.tif for footprint geometry (never existing_faults.tif!)
    with rasterio.open(d / "sample_submission.tif") as ds:
        fp = np.isfinite(ds.read(1))
        shape = fp.shape

    planes_meta: list[dict] = []

    # ------------------------------------------------------------------ #
    # Block 1: GDR-1391 Geothermal Geothermometer Disequilibrium + MT     #
    # ------------------------------------------------------------------ #
    diseq_grid = np.zeros(shape, dtype=np.float32)
    kinlag_grid = np.zeros(shape, dtype=np.float32)
    therm_grid = np.zeros(shape, dtype=np.float32)

    ws_csv = d / "external" / "gdr_wellspring_in_footprint.csv"
    with ws_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        allowed_cols = set(reader.fieldnames or []) - FORBIDDEN_CSV_COLUMNS
        assert "dist_known_fault_px" not in allowed_cols
        for row in reader:
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except (KeyError, ValueError):
                continue
            if not (0 <= r < shape[0] and 0 <= c < shape[1] and fp[r, c]):
                continue
            t_meas = np.nan
            try:
                if row["temp_c"]:
                    t_meas = float(row["temp_c"])
            except ValueError:
                pass
            chem_vals = []
            qtz_v = chalc_v = cat_v = np.nan
            for key_name in ("geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
                try:
                    v = float(row[key_name]) if row[key_name] else np.nan
                except ValueError:
                    v = np.nan
                if np.isfinite(v) and 0.0 < v < 400.0:
                    chem_vals.append(v)
                    if key_name == "geothermquartz_c":
                        qtz_v = v
                    elif key_name == "geothermchalc_c":
                        chalc_v = v
                    elif key_name == "geothermcat_c":
                        cat_v = v
            if chem_vals:
                t_chem = max(chem_vals)
                base_t = t_meas if (np.isfinite(t_meas) and t_meas > 5.0) else 14.0
                diseq = max(0.0, min(t_chem - base_t, 250.0)) / 150.0
                if diseq > diseq_grid[r, c]:
                    diseq_grid[r, c] = diseq
            if np.isfinite(cat_v) and np.isfinite(chalc_v):
                klag = max(0.0, min(cat_v - chalc_v, 180.0)) / 100.0
                if klag > kinlag_grid[r, c]:
                    kinlag_grid[r, c] = klag
            t_cls = (row.get("thermalclass") or "").strip().lower()
            w_th = 0.0
            if np.isfinite(t_meas) and t_meas > 20.0:
                w_th = max(w_th, min((t_meas - 20.0) / 80.0, 1.5))
            if t_cls == "hot":
                w_th = max(w_th, 1.0)
            elif t_cls == "warm":
                w_th = max(w_th, 0.45)
            if w_th > therm_grid[r, c]:
                therm_grid[r, c] = w_th

    vv_csv = d / "external" / "gdr_volcanic_vents_in_footprint.csv"
    vent_grid = np.zeros(shape, dtype=np.float32)
    with vv_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        assert "dist_known_fault_px" not in (set(reader.fieldnames or []) - FORBIDDEN_CSV_COLUMNS)
        for row in reader:
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except (KeyError, ValueError):
                continue
            if 0 <= r < shape[0] and 0 <= c < shape[1] and fp[r, c]:
                vent_grid[r, c] = 1.0

    gt_diseq_s8 = _pos_unit(ndi.gaussian_filter(diseq_grid, 8.0, mode="constant"), fp, 99.5)
    gt_diseq_s25 = _pos_unit(ndi.gaussian_filter(diseq_grid, 25.0, mode="constant"), fp, 99.5)
    gt_kinlag_s15 = _pos_unit(ndi.gaussian_filter(kinlag_grid, 15.0, mode="constant"), fp, 99.5)
    gt_thermal_s12 = _pos_unit(
        ndi.gaussian_filter(therm_grid, 12.0, mode="constant")
        + 0.75 * ndi.gaussian_filter(vent_grid, 20.0, mode="constant"),
        fp,
        99.5,
    )
    del diseq_grid, kinlag_grid, therm_grid, vent_grid

    tf_path = d / "training_features.tif"
    with rasterio.open(tf_path) as tf:
        cond_raw, cond_ok = _clean_band(tf.read(17), fp)
    mt_cond_z = _robust_z(cond_raw, cond_ok)
    mt_cond_grad = _robust_z(_grad_mag(cond_raw, 1.5), cond_ok)
    mt_cond_ridge = _robust_z(_hessian_sym_ridge(cond_raw, 2.0, "both"), cond_ok)
    cond_pos = _pos_unit(np.maximum(mt_cond_z, mt_cond_grad), fp, 99.0)
    gt_conduit_couple = (np.maximum(gt_diseq_s25, gt_thermal_s12) * (0.25 + 0.75 * cond_pos)).astype(np.float32)
    del cond_raw, cond_pos

    for nm, ar in (
        ("gt_diseq_s8", gt_diseq_s8),
        ("gt_diseq_s25", gt_diseq_s25),
        ("gt_kinlag_s15", gt_kinlag_s15),
        ("gt_thermal_s12", gt_thermal_s12),
        ("mt_cond_z", mt_cond_z),
        ("mt_cond_grad", mt_cond_grad),
        ("mt_cond_ridge", mt_cond_ridge),
        ("gt_conduit_couple", gt_conduit_couple),
    ):
        planes_meta.append(_save_plane(nm, ar, fp))
    del gt_diseq_s8, gt_diseq_s25, gt_kinlag_s15, gt_thermal_s12, mt_cond_z, mt_cond_grad, mt_cond_ridge, gt_conduit_couple
    gc.collect()

    # ------------------------------------------------------------------ #
    # Block 2: Multi-Depth Potential-Field Contact-Offset & Attenuation   #
    # ------------------------------------------------------------------ #
    with rasterio.open(tf_path) as tf:
        rtp, rtp_ok = _clean_band(tf.read(2), fp)
        tmi_hg, hg_ok = _clean_band(tf.read(3), fp)
        tc, tc_ok = _clean_band(tf.read(6), fp)
        tmi_vg, vg_ok = _clean_band(tf.read(9), fp)
        tmi, tmi_ok = _clean_band(tf.read(14), fp)
        grav_slope, gs_ok = _clean_band(tf.read(5), fp)
        grav_vg, gvg_ok = _clean_band(tf.read(11), fp)
        grav_hg, ghg_ok = _clean_band(tf.read(18), fp)

    with rasterio.open(d / "external" / "geodawn_extensions_u8.tif") as ext_ds:
        tmi_up150_raw = ext_ds.read(4).astype(np.float32)
    up_ok = tmi_ok & (tmi_up150_raw > 0)

    mag_rtp_grad_s1 = _robust_z(_grad_mag(rtp, 1.2), rtp_ok)
    mag_rtp_ridge_s1 = _robust_z(_hessian_sym_ridge(rtp, 1.2, "both"), rtp_ok)
    mag_rtp_ridge_s3 = _robust_z(_hessian_sym_ridge(rtp, 3.0, "both"), rtp_ok)
    mag_tc_z = _robust_z(tc, tc_ok)
    mag_tmi_hg_z = _robust_z(tmi_hg, hg_ok)

    # Verduzco et al. (2004) magnetic tilt angle horizontal derivative
    tilt_m = np.arctan2(tmi_vg, np.sqrt(tmi_hg * tmi_hg + 1e-6)).astype(np.float32)
    mag_verduzco_tilt_grad = _robust_z(_grad_mag(tilt_m, 1.2), vg_ok & hg_ok)
    del tilt_m, tmi_vg, tmi_hg, tc

    # Upward-continuation 150 m attenuation gradient
    z_tmi = _robust_z(tmi, up_ok)
    z_up150 = _robust_z(tmi_up150_raw, up_ok)
    atten_diff = (z_tmi - z_up150).astype(np.float32)
    mag_up150_atten_grad = _robust_z(_grad_mag(atten_diff, 1.2), up_ok)
    del tmi, tmi_up150_raw, z_tmi, z_up150, atten_diff

    # Multi-scale magnetic director disruption + cross-fault gravity step
    mx1, my1, mcoh1 = _structure_director(rtp, 1.0, 1.5)
    mx5, my5, _ = _structure_director(rtp, 1.5, 5.0)
    turn_disrupt_raw = np.hypot(mx1 - mx5, my1 - my5).astype(np.float32)
    mag_turn_disruption = _robust_z(turn_disrupt_raw, rtp_ok)
    del rtp, mx5, my5

    grav_hg_z = _robust_z(0.6 * _robust_z(grav_hg, ghg_ok) + 0.4 * _robust_z(grav_slope, gs_ok), ghg_ok & gs_ok)
    tilt_g = np.arctan2(grav_vg, np.sqrt(grav_hg * grav_hg + 1e-6)).astype(np.float32)
    grav_tilt_grad = _robust_z(_grad_mag(tilt_g, 1.5), gvg_ok & ghg_ok)
    del grav_vg, grav_slope, tilt_g

    gx2, gy2, gcoh2 = _structure_director(grav_hg, 1.0, 2.5)
    grav_pos = _pos_unit(grav_hg, ghg_ok, 99.0)
    # Contact-offset: magnetic fabric bends/truncates where gravity gradient steps
    contact_offset_grav_mag = _robust_z(turn_disrupt_raw * grav_pos, rtp_ok & ghg_ok)
    # Concordant basement fault: magnetic and gravity directors align
    dot_mg = np.abs(mx1 * gx2 + my1 * gy2) / np.maximum(np.hypot(mx1, my1) * np.hypot(gx2, gy2), 1e-6)
    grav_mag_concord = _robust_z((mcoh1 * gcoh2 * np.clip(dot_mg, 0.0, 1.0)).astype(np.float32), rtp_ok & ghg_ok)
    del mx1, my1, mcoh1, gx2, gy2, gcoh2, turn_disrupt_raw, grav_pos, grav_hg, dot_mg

    for nm, ar in (
        ("mag_rtp_grad_s1", mag_rtp_grad_s1),
        ("mag_rtp_ridge_s1", mag_rtp_ridge_s1),
        ("mag_rtp_ridge_s3", mag_rtp_ridge_s3),
        ("mag_tc_z", mag_tc_z),
        ("mag_tmi_hg_z", mag_tmi_hg_z),
        ("mag_verduzco_tilt_grad", mag_verduzco_tilt_grad),
        ("mag_up150_atten_grad", mag_up150_atten_grad),
        ("mag_turn_disruption", mag_turn_disruption),
        ("grav_hg_z", grav_hg_z),
        ("grav_tilt_grad", grav_tilt_grad),
        ("contact_offset_grav_mag", contact_offset_grav_mag),
        ("grav_mag_concord", grav_mag_concord),
    ):
        planes_meta.append(_save_plane(nm, ar, fp))
    del (
        mag_rtp_grad_s1, mag_rtp_ridge_s1, mag_rtp_ridge_s3, mag_tc_z, mag_tmi_hg_z,
        mag_verduzco_tilt_grad, mag_up150_atten_grad, mag_turn_disruption,
        grav_hg_z, grav_tilt_grad, contact_offset_grav_mag, grav_mag_concord,
    )
    gc.collect()

    # ------------------------------------------------------------------ #
    # Block 3: Subsurface Basement-Cover & Geodetic Strain                #
    # ------------------------------------------------------------------ #
    with rasterio.open(tf_path) as tf:
        s2inv, s2_ok = _clean_band(tf.read(4), fp)
        shear, sh_ok = _clean_band(tf.read(7), fp)
        dilat, dl_ok = _clean_band(tf.read(8), fp)
        bdepth, bd_ok = _clean_band(tf.read(15), fp)

    base_depth_z = _robust_z(bdepth, bd_ok)
    base_step_grad = _robust_z(_grad_mag(bdepth, 1.5), bd_ok)
    base_step_ridge = _robust_z(_hessian_sym_ridge(bdepth, 2.0, "both"), bd_ok)
    strain_2ndinv_z = _robust_z(s2inv, s2_ok)
    strain_dilat_z = _robust_z(dilat, dl_ok)
    strain_transtension = _robust_z(
        (dilat / (np.hypot(shear, dilat) + 1e-6)).astype(np.float32), sh_ok & dl_ok
    )
    del s2inv, shear, dilat, bdepth

    for nm, ar in (
        ("base_depth_z", base_depth_z),
        ("base_step_grad", base_step_grad),
        ("base_step_ridge", base_step_ridge),
        ("strain_2ndinv_z", strain_2ndinv_z),
        ("strain_dilat_z", strain_dilat_z),
        ("strain_transtension", strain_transtension),
    ):
        planes_meta.append(_save_plane(nm, ar, fp))
    del base_depth_z, base_step_grad, base_step_ridge, strain_2ndinv_z, strain_dilat_z, strain_transtension
    gc.collect()

    # ------------------------------------------------------------------ #
    # Block 4: 1m LiDAR Scarplets, 100m DEM Ridges & Rad-Topo Discordance #
    # ------------------------------------------------------------------ #
    with rasterio.open(tf_path) as tf:
        det_elev, de_ok = _clean_band(tf.read(12), fp)
        det_slope, ds_ok = _clean_band(tf.read(19), fp)

    dem_elev_z = _robust_z(det_elev, de_ok)
    dem_slope_z = _robust_z(det_slope, ds_ok)
    lap_elev = ndi.laplace(det_elev).astype(np.float32)
    dem_piedmont_hinge = _robust_z(
        0.65 * _pos_unit(_hessian_sym_ridge(det_slope, 1.5, "ridge"), ds_ok)
        + 0.35 * _pos_unit(-lap_elev, de_ok),
        de_ok & ds_ok,
    )
    valley_raw = _pos_unit(_hessian_sym_ridge(det_elev, 1.5, "valley"), de_ok)
    dem_valley_chain = _robust_z(_axial_chain_excess(valley_raw, length=9, n_angles=8), de_ok)
    del valley_raw

    with rasterio.open(d / "external" / "lidar_scarp_features_u8.tif") as lds:
        ex_max = lds.read(1).astype(np.float32)
        ex_mean = lds.read(2).astype(np.float32)
        step_max = lds.read(3).astype(np.float32)
        lapneg = lds.read(4).astype(np.float32)
        lappos = lds.read(5).astype(np.float32)
        downf = lds.read(6).astype(np.float32)
        upf = lds.read(7).astype(np.float32)
        relief = lds.read(9).astype(np.float32)
        coh100 = lds.read(10).astype(np.float32)
        l_val = (lds.read(12) > 0) & fp

    lidar_valid = l_val.astype(np.float32)
    lidar_step_z = _robust_z(step_max, l_val)
    lidar_ex_z = _robust_z(0.6 * ex_max + 0.4 * ex_mean, l_val)
    lidar_face_asym = _robust_z(0.6 * np.maximum(downf, upf) + 0.4 * np.maximum(lapneg, lappos), l_val)
    slope_01 = _pos_unit(det_slope, ds_ok, 98.0)
    pied_raw = (
        (step_max / 255.0)
        * (0.35 + 0.65 * (coh100 / 255.0))
        / (0.18 + (relief / 255.0) + 0.8 * slope_01)
    ).astype(np.float32)
    pied_raw[~l_val] = 0.0
    lidar_piedmont_scarp = _robust_z(pied_raw, l_val)
    lidar_chain_vote = _robust_z(_axial_chain_excess(_pos_unit(pied_raw, l_val, 99.0), length=9, n_angles=8), l_val)
    del ex_max, ex_mean, step_max, lapneg, lappos, downf, upf, relief, coh100, pied_raw, slope_01
    gc.collect()

    # Radiometric-Topographic Discordance (label-free regression removing elevation/slope/curvature)
    with rasterio.open(d / "external" / "geodawn_rad_u8.tif") as rds:
        K_raw = rds.read(1).astype(np.float32)
    with rasterio.open(d / "external" / "geodawn_extensions_u8.tif") as eds:
        ThK_raw = eds.read(1).astype(np.float32)
        UTh_raw = eds.read(3).astype(np.float32)
    rad_ok = fp & (K_raw > 0) & (ThK_raw > 0) & (UTh_raw > 0) & de_ok & ds_ok
    rng = np.random.default_rng(2026086)
    ry, rx = np.nonzero(rad_ok)
    sub = rng.choice(ry.size, size=min(200_000, ry.size), replace=False)
    abs_lap = np.abs(lap_elev)
    X_topo = np.column_stack([det_elev[ry[sub], rx[sub]], det_slope[ry[sub], rx[sub]], abs_lap[ry[sub], rx[sub]]])

    m_k = HuberRegressor(alpha=0.1, max_iter=200).fit(X_topo, K_raw[ry[sub], rx[sub]])
    k_res = np.where(
        rad_ok,
        K_raw - (m_k.coef_[0] * det_elev + m_k.coef_[1] * det_slope + m_k.coef_[2] * abs_lap + m_k.intercept_),
        0.0,
    ).astype(np.float32)
    k_disc_edge = 0.5 * _pos_unit(_grad_mag(k_res, 1.2), rad_ok) + 0.5 * _pos_unit(
        _hessian_sym_ridge(k_res, 1.5, "both"), rad_ok
    )
    rad_topo_discord_K = _robust_z(_axial_chain_excess(k_disc_edge, length=7, n_angles=8), rad_ok)

    ratio_mix = (0.6 * UTh_raw - 0.4 * ThK_raw).astype(np.float32)
    m_u = HuberRegressor(alpha=0.1, max_iter=200).fit(X_topo, ratio_mix[ry[sub], rx[sub]])
    u_res = np.where(
        rad_ok,
        ratio_mix - (m_u.coef_[0] * det_elev + m_u.coef_[1] * det_slope + m_u.coef_[2] * abs_lap + m_u.intercept_),
        0.0,
    ).astype(np.float32)
    u_disc_edge = 0.5 * _pos_unit(_grad_mag(u_res, 1.2), rad_ok) + 0.5 * _pos_unit(
        _hessian_sym_ridge(u_res, 1.5, "both"), rad_ok
    )
    rad_topo_discord_UTh = _robust_z(_axial_chain_excess(u_disc_edge, length=7, n_angles=8), rad_ok)
    del K_raw, ThK_raw, UTh_raw, det_elev, det_slope, lap_elev, abs_lap, k_res, u_res, k_disc_edge, u_disc_edge, ratio_mix

    for nm, ar in (
        ("lidar_valid", lidar_valid),
        ("lidar_step_z", lidar_step_z),
        ("lidar_ex_z", lidar_ex_z),
        ("lidar_face_asym", lidar_face_asym),
        ("lidar_piedmont_scarp", lidar_piedmont_scarp),
        ("lidar_chain_vote", lidar_chain_vote),
        ("dem_elev_z", dem_elev_z),
        ("dem_slope_z", dem_slope_z),
        ("dem_piedmont_hinge", dem_piedmont_hinge),
        ("dem_valley_chain", dem_valley_chain),
        ("rad_topo_discord_K", rad_topo_discord_K),
        ("rad_topo_discord_UTh", rad_topo_discord_UTh),
    ):
        planes_meta.append(_save_plane(nm, ar, fp))
    gc.collect()

    assert [p["name"] for p in planes_meta] == list(PHYS_FEATURES)
    man = dict(
        schema="h86b-physical-planes-v1",
        catalogue_used=False,
        sgmc_used=False,
        forbidden_csv_columns_excluded=sorted(FORBIDDEN_CSV_COLUMNS),
        n_features=len(planes_meta),
        elapsed_s=round(time.time() - t0, 2),
        planes=planes_meta,
    )
    manifest_path.write_text(json.dumps(man, indent=2) + "\n")
    return man


def open_planes() -> dict[str, np.ndarray]:
    """Memory-map all 38 physical planes read-only."""
    return {name: np.load(PLANE_DIR / f"{name}.npy", mmap_mode="r") for name in PHYS_FEATURES}


def gather_rows(planes: dict[str, np.ndarray], rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    """Extract `(len(rows), 38)` float32 matrix without materializing full planes."""
    X = np.empty((rows.size, len(PHYS_FEATURES)), dtype=np.float32)
    for j, name in enumerate(PHYS_FEATURES):
        X[:, j] = planes[name][rows, cols]
    return X


def compute_kinematic_components(
    visible: np.ndarray,
    bbox: tuple[slice, slice] | None = None,
    pad: int = 44,
) -> dict[str, np.ndarray]:
    """Compute strictly visible-only crack-tip, relay-bridge, and bend-splay fields.

    If `bbox` is provided, computes inside a `pad`-expanded window around `bbox`
    and slices back to `bbox` so fold evaluation is exact within `pad` pixels
    (4.4 km) while running in ~4s and <300 MB RAM.
    """
    vis_full = np.asarray(visible, dtype=bool)
    H_full, W_full = vis_full.shape
    if bbox is not None:
        r0, r1 = bbox[0].start, bbox[0].stop
        c0, c1 = bbox[1].start, bbox[1].stop
        pr0, pr1 = max(0, r0 - pad), min(H_full, r1 + pad)
        pc0, pc1 = max(0, c0 - pad), min(W_full, c1 + pad)
        vis = vis_full[pr0:pr1, pc0:pc1]
        out_sl = (slice(r0 - pr0, r1 - pr0), slice(c0 - pc0, c1 - pc0))
    else:
        vis = vis_full
        out_sl = (slice(None), slice(None))

    h, w = vis.shape
    # 1. Anisotropic forward crack-tip propagation cones from visible segments
    _, _, st = _fragment_stats(vis)
    tip_cone = np.zeros((h, w), dtype=np.float32)
    R_TIP = 26
    for info in st.values():
        L = float(info["length_px"])
        if L < 3.0:
            continue
        w_len = float(min(1.0, np.log1p(L) / np.log(30.0)))
        axis = info["axis"]  # unit vector from p0 -> p1
        # p0 points along -axis, p1 points along +axis
        for pt, uvec in ((info["p0"], -axis), (info["p1"], axis)):
            ty, tx = float(pt[0]), float(pt[1])
            uy, ux = float(uvec[0]), float(uvec[1])
            y0 = max(0, int(np.floor(ty)) - R_TIP)
            y1 = min(h, int(np.ceil(ty)) + R_TIP + 1)
            x0 = max(0, int(np.floor(tx)) - R_TIP)
            x1 = min(w, int(np.ceil(tx)) + R_TIP + 1)
            if y1 <= y0 or x1 <= x0:
                continue
            yy = (np.arange(y0, y1, dtype=np.float32)[:, None] - np.float32(ty))
            xx = (np.arange(x0, x1, dtype=np.float32)[None, :] - np.float32(tx))
            r_par = yy * np.float32(uy) + xx * np.float32(ux)
            r_perp = -yy * np.float32(ux) + xx * np.float32(uy)
            sig_perp = 1.6 + 0.22 * np.maximum(r_par, 0.0)
            cone = np.where(
                r_par > 0.5,
                w_len * np.exp(-r_par / 11.0) * np.exp(-0.5 * (r_perp / sig_perp) ** 2),
                0.0,
            ).astype(np.float32)
            np.maximum(tip_cone[y0:y1, x0:x1], cone, out=tip_cone[y0:y1, x0:x1])

    # 2. Two-host relay-stepover corridor & displacement-scaled bend/splay zone
    th = two_host_frame(vis)
    bend = host_bend_fields(vis, fine_px=3.0, coarse_px=9.0)

    d1 = th["d1"]
    d2 = th["d2"]
    iy1, ix1 = th["iy1"], th["ix1"]
    iy2, ix2 = th["iy2"], th["ix2"]
    L1 = th["comp_len"][th["c1"]]
    L2 = th["comp_len"][th["c2"]]

    yg = np.arange(h, dtype=np.float32)[:, None]
    xg = np.arange(w, dtype=np.float32)[None, :]
    dy1 = yg - iy1.astype(np.float32)
    dx1 = xg - ix1.astype(np.float32)
    dy2 = yg - iy2.astype(np.float32)
    dx2 = xg - ix2.astype(np.float32)
    facing = np.clip(-(dy1 * dy2 + dx1 * dx2) / np.maximum(d1 * d2, 1e-6), 0.0, 1.0)

    len_pair = np.minimum(1.0, np.sqrt(np.log1p(L1) * np.log1p(L2)) / np.float32(np.log(25.0)))
    relay_bridge = (
        np.exp(-(d1 + d2) / 15.0) * (facing ** 1.5) * len_pair * (d1 + d2 <= 38.0)
    ).astype(np.float32)

    turn_at_host = np.clip(bend["turn"][iy1, ix1], 0.0, 1.0)
    w_scale = 5.5 + 1.4 * np.log1p(L1)
    bend_splay = (
        np.exp(-np.maximum(d1 - 2.5, 0.0) / w_scale) * (0.35 + 0.65 * turn_at_host)
    ).astype(np.float32)

    # Zero inside penalized d1 <= 2.0 px flank (thread 11516 / H33-2-B2 collar)
    off_flank = d1 > 2.0
    tip_cone = np.where(off_flank, tip_cone, 0.0)
    relay_bridge = np.where(off_flank, relay_bridge, 0.0)
    bend_splay = np.where(off_flank, bend_splay, 0.0)
    m_kin = np.clip(np.maximum.reduce([tip_cone, 0.90 * relay_bridge, 0.60 * bend_splay]), 0.0, 1.0)

    return dict(
        tip_cone=tip_cone[out_sl].copy(),
        relay_bridge=relay_bridge[out_sl].copy(),
        bend_splay=bend_splay[out_sl].copy(),
        m_kin=m_kin[out_sl].copy(),
        d1=d1[out_sl].copy(),
    )


def main():
    # Direct feature-building must not get around the model entrypoint's STOP.
    # Pure transformation functions remain importable for synthetic unit tests.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    man = build_physical_planes()
    print(f"Built {man['n_features']} physical planes in {man['elapsed_s']}s")


if __name__ == "__main__":
    main()
