"""Zero-leakage cross-spectral, hydrothermal, and SAR censoring physics for H86J-CSGD.

Strict leakage & governance contract:
1. ``build_csgd_planes`` reads ONLY ``training_features.tif`` (band indices verified
   against ``src/gems86/io.py::BANDS``) and SHA-pinned label-free external products
   (``geodawn_rad_u8.tif``, ``geodawn_extensions_u8.tif``, ``topo_10m_derived_100m_u8.tif``,
   ``gdr_wellspring_in_footprint.csv``, ``gdr_volcanic_vents_in_footprint.csv``).
2. ``FORBIDDEN_GDR_COLUMNS`` (``dist_known_fault_px``) is explicitly blocked and never
   accessed from either GDR-1391 CSV table.
3. ``DEEP_FEATURE_NAMES`` contains ZERO topographic slope or DEM scarp features;
   surficial geomorphic cover planes live exclusively in ``EXPOSURE_FEATURE_NAMES``
   to estimate the Selected-At-Random (SAR) mapping propensity ``e_hat(X_vis)``.
4. Fold-visible elastic crack-tip/stepover fields delegate to
   ``gems86_ewcs.features.compute_elastic_fields(vis_cat, footprint)`` using strictly
   fold-visible fault pixels ``vis_cat``.
"""
from __future__ import annotations

import csv
import gc
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.linear_model import LogisticRegression

from gems86.io import read_band
from gems86_ewcs.features import (
    ELASTIC_COUPLED_NAMES,
    _hessian_ridge_abs,
    _robust_standardize,
    _zerocross_sharpness,
    compute_elastic_fields,
    compute_laplace_gzz_and_curl,
    fill_outside_footprint,
)

FORBIDDEN_GDR_COLUMNS: frozenset[str] = frozenset({"dist_known_fault_px"})
ALLOWED_WELLSPRING_COLUMNS: tuple[str, ...] = (
    "row",
    "col",
    "temp_c",
    "geothermquartz_c",
    "geothermchalc_c",
    "geothermcat_c",
)
ALLOWED_VENT_COLUMNS: tuple[str, ...] = ("row", "col")

DEEP_FEATURE_NAMES: tuple[str, ...] = (
    "cspa_admit_resid_s4",
    "cspa_admit_resid_s9",
    "cspa_coherence_break_s6",
    "hydro_demag_trough_s4",
    "mag_up150_wavenumber_s3",
    "verduzco_tilt_depth_inv_s2",
    "verduzco_tilt_depth_inv_s5",
    "laplace_gzz_zerocross_s3",
    "laplace_gzz_zerocross_s6",
    "grav_vec_mag_s2",
    "base_hinge_curv_s4",
    "gdr_thermal_upflow_s10",
    "gdr_silica_geotherm_s14",
    "rad_k_th_metasom_grad_s3",
    "rad_u_th_redox_step_s3",
    "cond_smectite_neck_s3",
    "strain_transtens",
    "eq_prox_exp",
)

EXPOSURE_FEATURE_NAMES: tuple[str, ...] = (
    "vis_slope_local",
    "vis_piedmont_relief_ratio",
    "vis_cenozoic_fill_depth",
    "vis_tc_outcrop_grad",
    "vis_lahontan_rework",
)

ALL_PLANE_NAMES: tuple[str, ...] = DEEP_FEATURE_NAMES + EXPOSURE_FEATURE_NAMES


def _grad_mag(field: np.ndarray, sigma: float) -> np.ndarray:
    gx = ndi.gaussian_filter(field, sigma, order=(0, 1))
    gy = ndi.gaussian_filter(field, sigma, order=(1, 0))
    return np.hypot(gx, gy).astype(np.float32)


def compute_cross_spectral_admittance_residual(
    iso_grav: np.ndarray,
    rtp: np.ndarray,
    sigma_lo: float,
    sigma_hi: float,
    win_sigma: float,
    reg_frac: float = 0.05,
) -> tuple[np.ndarray, np.ndarray]:
    """Windowed band-limited gravity-magnetic admittance residual step & coherence deficit.

    Within band-pass waveband ``[sigma_lo, sigma_hi]``:
      dg = G_{sigma_lo}(g) - G_{sigma_hi}(g)
      dm = G_{sigma_lo}(m) - G_{sigma_hi}(m)
      H_GM(x) = <dg * dm>_W / (<dm^2>_W + lambda)
      g_uncomp(x) = dg(x) - H_GM(x) * dm(x)

    Returns ``(|grad g_uncomp|, 1 - rho_GM^2)`` as float32 arrays.
    """
    dg = (ndi.gaussian_filter(iso_grav, sigma_lo) - ndi.gaussian_filter(iso_grav, sigma_hi)).astype(np.float32)
    dm = (ndi.gaussian_filter(rtp, sigma_lo) - ndi.gaussian_filter(rtp, sigma_hi)).astype(np.float32)

    cov_gm = ndi.gaussian_filter(dg * dm, win_sigma)
    var_m = ndi.gaussian_filter(dm * dm, win_sigma)
    var_g = ndi.gaussian_filter(dg * dg, win_sigma)

    m_reg = max(float(np.median(var_m)) * reg_frac, 1e-6)
    g_reg = max(float(np.median(var_g)) * reg_frac, 1e-6)

    admittance = cov_gm / (var_m + m_reg)
    g_uncomp = dg - admittance * dm
    resid_step = _grad_mag(g_uncomp, max(1.5, 0.5 * sigma_lo))

    coh2 = np.clip((cov_gm * cov_gm) / ((var_m + m_reg) * (var_g + g_reg)), 0.0, 1.0)
    coherence_deficit = (1.0 - coh2).astype(np.float32)
    return resid_step.astype(np.float32), coherence_deficit


def _parse_finite_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    txt = raw.strip()
    if not txt or txt.lower() in {"nan", "none", "null", "na", "-999", "-9999"}:
        return None
    try:
        val = float(txt)
    except ValueError:
        return None
    return val if np.isfinite(val) else None


def load_gdr_thermal_and_vent_fields(
    wellspring_csv: Path,
    vents_csv: Path,
    shape: tuple[int, int],
    footprint: np.ndarray,
    vent_veto_sigma_px: float = 12.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rasterize label-free GDR-1391 thermal & silica geothermometer plumes with vent veto.

    Explicitly ignores ``FORBIDDEN_GDR_COLUMNS`` (``dist_known_fault_px``) so known-fault
    proximity can never leak into holdout folds.
    """
    h, w = shape
    fp = np.asarray(footprint, dtype=bool)
    temp_excess = np.zeros((h, w), dtype=np.float32)
    geotherm_excess = np.zeros((h, w), dtype=np.float32)
    vent_mask = np.zeros((h, w), dtype=np.float32)

    with wellspring_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"empty header in {wellspring_csv}")
        missing = [c for c in ALLOWED_WELLSPRING_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"missing required GDR wellspring columns {missing}")
        for row in reader:
            # Never touch FORBIDDEN_GDR_COLUMNS ('dist_known_fault_px')
            r_f = _parse_finite_float(row.get("row"))
            c_f = _parse_finite_float(row.get("col"))
            if r_f is None or c_f is None:
                continue
            ri, ci = int(round(r_f)), int(round(c_f))
            if not (0 <= ri < h and 0 <= ci < w) or not fp[ri, ci]:
                continue
            tc = _parse_finite_float(row.get("temp_c"))
            if tc is not None and 20.0 < tc <= 350.0:
                exc = float(np.log1p(tc - 20.0))
                if exc > temp_excess[ri, ci]:
                    temp_excess[ri, ci] = exc

            gt_candidates = []
            for col_name in ("geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
                gv = _parse_finite_float(row.get(col_name))
                if gv is not None and 90.0 < gv <= 400.0:
                    gt_candidates.append(gv)
            if gt_candidates:
                g_exc = float(np.log1p(max(gt_candidates) - 90.0))
                if g_exc > geotherm_excess[ri, ci]:
                    geotherm_excess[ri, ci] = g_exc

    with vents_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"empty header in {vents_csv}")
        missing_v = [c for c in ALLOWED_VENT_COLUMNS if c not in reader.fieldnames]
        if missing_v:
            raise ValueError(f"missing required GDR vent columns {missing_v}")
        for row in reader:
            r_f = _parse_finite_float(row.get("row"))
            c_f = _parse_finite_float(row.get("col"))
            if r_f is None or c_f is None:
                continue
            ri, ci = int(round(r_f)), int(round(c_f))
            if 0 <= ri < h and 0 <= ci < w:
                vent_mask[ri, ci] = 1.0

    if vent_mask.sum() > 0:
        vent_halo = ndi.gaussian_filter(vent_mask, vent_veto_sigma_px)
        vent_peak = max(float(vent_halo.max()), 1e-6)
        vent_veto = (1.0 - 0.85 * np.clip(vent_halo / (0.35 * vent_peak), 0.0, 1.0)).astype(np.float32)
    else:
        vent_veto = np.ones((h, w), dtype=np.float32)

    thermal_plume = (
        0.60 * ndi.gaussian_filter(temp_excess, 8.0)
        + 0.40 * ndi.gaussian_filter(temp_excess, 18.0)
    ) * vent_veto
    silica_plume = (
        0.55 * ndi.gaussian_filter(geotherm_excess, 10.0)
        + 0.45 * ndi.gaussian_filter(geotherm_excess, 22.0)
    ) * vent_veto
    return thermal_plume.astype(np.float32), silica_plume.astype(np.float32), vent_veto


def _load_u8_band(tif_path: Path, band_idx: int, fp: np.ndarray,
                  nearest_idx: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    with rasterio.open(tif_path) as ds:
        raw = ds.read(band_idx).astype(np.float32)
    valid = fp & (raw > 0.0) & np.isfinite(raw)
    if not valid.any():
        return np.zeros_like(raw, dtype=np.float32)
    if (~valid & fp).any():
        _, (iy, ix) = ndi.distance_transform_edt(~valid, return_indices=True)
        out = raw.copy()
        bad = ~valid
        out[bad] = raw[iy[bad], ix[bad]]
        return out
    return fill_outside_footprint(raw, fp, nearest_idx)


def build_csgd_planes(
    features_tif: Path,
    external_dir: Path,
    footprint: np.ndarray,
    out_memmap_path: Path | None = None,
) -> dict[str, np.ndarray] | np.ndarray:
    """Compute all 23 label-free planes (18 cover-blind deep + 5 SAR exposure covariates)."""
    fp = np.asarray(footprint, dtype=bool)
    elev_raw = read_band(features_tif, "det_elev")
    valid0 = fp & np.isfinite(elev_raw) & (np.abs(elev_raw) < 1e20)
    _, nearest_idx = ndi.distance_transform_edt(~valid0, return_indices=True)

    def load_tf(name: str) -> np.ndarray:
        return fill_outside_footprint(read_band(features_tif, name), fp, nearest_idx)

    mm = None
    out: dict[str, np.ndarray] = {}
    if out_memmap_path is not None:
        out_memmap_path.parent.mkdir(parents=True, exist_ok=True)
        mm = np.lib.format.open_memmap(
            out_memmap_path,
            mode="w+",
            dtype=np.float16,
            shape=(len(ALL_PLANE_NAMES), fp.shape[0], fp.shape[1]),
        )

    def store(key: str, arr: np.ndarray) -> None:
        std_arr = _robust_standardize(arr, fp)
        if mm is not None:
            mm[ALL_PLANE_NAMES.index(key)] = std_arr.astype(np.float16)
        else:
            out[key] = std_arr

    # 1. Vector gravity Laplace g_zz, curl veto, and cross-spectral admittance residuals
    b18 = load_tf("iso_grav_anom_hg")
    b11 = load_tf("iso_grav_anom_vg")
    gzz3, curl3 = compute_laplace_gzz_and_curl(b18, b11, sigma=3.0)
    curl_med = max(float(np.median(curl3[fp])), 1e-6) if fp.any() else 1.0
    curl_veto = (1.0 / (1.0 + (curl3 / (2.5 * curl_med)) ** 2)).astype(np.float32)
    del curl3
    gzz3_zc = _zerocross_sharpness(gzz3, fp, sigma_grad=1.5) * curl_veto
    del gzz3
    store("laplace_gzz_zerocross_s3", gzz3_zc)

    gzz6, _ = compute_laplace_gzz_and_curl(b18, b11, sigma=6.0)
    store("laplace_gzz_zerocross_s6", _zerocross_sharpness(gzz6, fp, sigma_grad=2.0) * curl_veto)
    del gzz6
    gvec = ndi.gaussian_filter(np.hypot(b18, b11), 2.0).astype(np.float32)
    del b18, b11
    store("grav_vec_mag_s2", gvec)

    iso_g = load_tf("iso_grav_anom")
    rtp = load_tf("rtp")
    resid_s4, _ = compute_cross_spectral_admittance_residual(
        iso_g, rtp, sigma_lo=2.5, sigma_hi=7.0, win_sigma=10.0
    )
    store("cspa_admit_resid_s4", resid_s4 * curl_veto)
    del resid_s4

    resid_s9, coh_def = compute_cross_spectral_admittance_residual(
        iso_g, rtp, sigma_lo=6.0, sigma_hi=16.0, win_sigma=20.0
    )
    store("cspa_admit_resid_s9", resid_s9 * curl_veto)
    del resid_s9, iso_g
    g_scale = max(float(np.percentile(gvec[fp], 75)), 1e-6) if fp.any() else 1.0
    store("cspa_coherence_break_s6", coh_def * np.tanh(gvec / g_scale) * curl_veto)
    del coh_def, gvec, curl_veto
    gc.collect()

    # 2. Upward-continued TMI_up150 wavenumber attenuation & hydrothermal demagnetization trough
    ext_tif = external_dir / "geodawn_extensions_u8.tif"
    tmi_up150 = _load_u8_band(ext_tif, 4, fp, nearest_idx)
    rtp_gm = _grad_mag(rtp, 2.5)
    del rtp
    up_gm = _grad_mag(tmi_up150, 2.5)
    del tmi_up150
    rtp_med = max(float(np.median(rtp_gm[fp])), 1e-6) if fp.any() else 1.0
    up_med = max(float(np.median(up_gm[fp])), 1e-6) if fp.any() else 1.0
    wavenumber_ratio = np.log((rtp_gm / rtp_med + 0.15) / (up_gm / up_med + 0.15))
    store("mag_up150_wavenumber_s3", wavenumber_ratio)
    # Hydrothermal magnetite destruction: sharp gravity contact where upward-continued TMI step is subdued
    demag_trough = gzz3_zc / (1.0 + (up_gm / up_med))
    store("hydro_demag_trough_s4", demag_trough)
    del rtp_gm, up_gm, wavenumber_ratio, demag_trough, gzz3_zc
    gc.collect()

    # 3. Verduzco magnetic tilt-depth sharpness (Bands 3, 9)
    tmi_hg = np.maximum(load_tf("tmi_hg"), 1e-6)
    tmi_vg = load_tf("tmi_vg")
    theta_mag = np.arctan2(tmi_vg, tmi_hg).astype(np.float32)
    del tmi_hg, tmi_vg
    for s, key in ((2.0, "verduzco_tilt_depth_inv_s2"), (5.0, "verduzco_tilt_depth_inv_s5")):
        th_s = ndi.gaussian_filter(theta_mag, s)
        inv_d = _grad_mag(th_s, 1.0) * np.exp(-((th_s / 0.35) ** 2))
        store(key, inv_d)
        del th_s, inv_d
    del theta_mag
    gc.collect()

    # 4. Basement hinge (Band 15) + GDR-1391 thermal & silica geothermometer plumes + GeoDAWN K/Th/U
    base_d = load_tf("depth_to_base_surf")
    store("base_hinge_curv_s4", _hessian_ridge_abs(base_d, sigma=4.0))

    thermal_plume, silica_plume, vent_veto = load_gdr_thermal_and_vent_fields(
        external_dir / "gdr_wellspring_in_footprint.csv",
        external_dir / "gdr_volcanic_vents_in_footprint.csv",
        fp.shape,
        fp,
        vent_veto_sigma_px=12.0,
    )
    store("gdr_thermal_upflow_s10", thermal_plume)
    store("gdr_silica_geotherm_s14", silica_plume)
    del thermal_plume, silica_plume

    rad_tif = external_dir / "geodawn_rad_u8.tif"
    k_band = _load_u8_band(rad_tif, 1, fp, nearest_idx)
    th_band = _load_u8_band(rad_tif, 2, fp, nearest_idx)
    k_z = _robust_standardize(k_band, fp)
    th_z = _robust_standardize(th_band, fp)
    del k_band, th_band
    k_metasom = (k_z - 0.85 * th_z) * vent_veto
    del k_z, th_z
    store("rad_k_th_metasom_grad_s3", _grad_mag(k_metasom, 3.0))
    del k_metasom

    uth_band = _load_u8_band(ext_tif, 3, fp, nearest_idx)
    store("rad_u_th_redox_step_s3", _grad_mag(uth_band, 3.0) * vent_veto)
    del uth_band, vent_veto
    gc.collect()

    # 5. Smectite conductance neck (Band 17), geodetic transtension (Bands 4, 7, 8) & seismicity (Bands 10, 16)
    cond = load_tf("cond_surf")
    cond_ridge = _hessian_ridge_abs(cond, sigma=3.5)
    store("cond_smectite_neck_s3", 0.55 * ndi.gaussian_filter(cond, 2.0) + 0.45 * cond_ridge)
    del cond, cond_ridge

    dilat = load_tf("geod_dilaterate")
    shear = load_tf("geod_shearrate")
    inv2 = load_tf("geod_2ndinv")
    pos_dilat = np.maximum(dilat - float(np.median(dilat[fp]) if fp.any() else 0.0), 0.0)
    store("strain_transtens", np.sqrt(np.maximum(shear, 0.0) * pos_dilat + 1e-12) + 0.25 * inv2)
    del dilat, shear, inv2, pos_dilat

    eq_d = np.maximum(load_tf("deq_n100a15"), 0.0)
    ieq = load_tf("ieq_n100a15")
    eq_scale = max(float(np.median(eq_d[fp])), 1.0) if fp.any() else 1000.0
    store("eq_prox_exp", 0.5 * np.exp(-eq_d / (0.5 * eq_scale)) + 0.5 * np.tanh(np.maximum(ieq, 0.0)))
    del eq_d, ieq
    gc.collect()

    # 6. SAR Geomorphic Exposure / Censoring Covariates ONLY (never passed into P_deep)
    slope = read_band(features_tif, "det_elev_slope")
    slope_clean = np.where(fp & np.isfinite(slope) & (np.abs(slope) < 1e20), slope, 0.0).astype(np.float32)
    store("vis_slope_local", slope_clean)
    del slope, slope_clean

    elev = fill_outside_footprint(elev_raw, fp, nearest_idx)
    del elev_raw
    rel_short = ndi.maximum_filter(elev, size=5) - ndi.minimum_filter(elev, size=5)
    rel_long = ndi.maximum_filter(elev, size=25) - ndi.minimum_filter(elev, size=25)
    store("vis_piedmont_relief_ratio", rel_short / (rel_long + 5.0))
    del elev, rel_short, rel_long

    store("vis_cenozoic_fill_depth", base_d)
    del base_d

    tc = load_tf("tc")
    store("vis_tc_outcrop_grad", _grad_mag(tc, 2.0))
    del tc

    dem_u8 = _load_u8_band(external_dir / "topo_10m_derived_100m_u8.tif", 9, fp, nearest_idx)
    del nearest_idx
    # Quantized uint8 value 45.0 == 1338 m Pleistocene Lake Lahontan highstand shoreline
    lahontan_rework = (1.0 / (1.0 + np.exp((dem_u8 - 46.0) / 3.0))).astype(np.float32)
    store("vis_lahontan_rework", lahontan_rework)
    del dem_u8, lahontan_rework
    gc.collect()

    if mm is not None:
        mm.flush()
        del mm
        return np.load(out_memmap_path, mmap_mode="r")
    return out


def compute_sar_exposure_propensity(
    planes_mm: np.ndarray | dict[str, np.ndarray],
    vis_cat: np.ndarray,
    footprint: np.ndarray,
    *,
    seed: int = 86,
    max_samples: int = 240_000,
) -> np.ndarray:
    """Estimate Selected-At-Random (SAR) surficial scarp mapping propensity ``e_hat(X_vis)``.

    Fits ``P(mapped in vis_cat | X_vis, strong deep potential-field support)`` strictly
    from fold-visible faults ``vis_cat`` and exposure covariates ``EXPOSURE_FEATURE_NAMES``,
    calibrated onto ``[0.03, 0.90]`` so steep exposed bedrock has high mappability while
    Holocene alluvial aprons and Lahontan-reworked floors have low mappability.
    """
    fp = np.asarray(footprint, dtype=bool)

    def _get(name: str) -> np.ndarray:
        if isinstance(planes_mm, dict):
            return planes_mm[name]
        return planes_mm[ALL_PLANE_NAMES.index(name)]

    deep_energy = np.maximum.reduce([
        _get("grav_vec_mag_s2").astype(np.float32),
        _get("cspa_admit_resid_s4").astype(np.float32),
        _get("verduzco_tilt_depth_inv_s2").astype(np.float32),
    ])
    thresh = float(np.percentile(deep_energy[fp], 70.0)) if fp.any() else 0.0
    domain = fp & (deep_energy >= thresh)
    del deep_energy

    d_vis = ndi.distance_transform_edt(~(np.asarray(vis_cat, dtype=bool) & fp))
    mapped = domain & (d_vis <= 2.0)
    unmapped = domain & (d_vis > 5.0)
    del d_vis, domain

    pos_idx = np.flatnonzero(mapped.ravel())
    neg_idx = np.flatnonzero(unmapped.ravel())
    del mapped, unmapped
    if pos_idx.size < 20 or neg_idx.size < 20:
        # Fallback monotone slope propensity on tiny synthetic test grids
        sl = _get("vis_slope_local").astype(np.float32)
        p95 = max(float(np.percentile(sl[fp], 95.0)) if fp.any() else 1.0, 1e-5)
        e_fallback = np.clip(0.05 + 0.80 * np.clip(sl / p95, 0.0, 1.0), 0.03, 0.90)
        return np.where(fp, e_fallback, 0.0).astype(np.float32)

    rng = np.random.default_rng(seed)
    n_pos = min(pos_idx.size, max_samples // 2)
    n_neg = min(neg_idx.size, max_samples - n_pos)
    p_sub = rng.choice(pos_idx, size=n_pos, replace=False)
    n_sub = rng.choice(neg_idx, size=n_neg, replace=False)
    idx = np.concatenate([p_sub, n_sub])
    y = np.concatenate([np.ones(n_pos, dtype=np.int8), np.zeros(n_neg, dtype=np.int8)])

    X = np.column_stack([_get(k).ravel()[idx].astype(np.float32) for k in EXPOSURE_FEATURE_NAMES])
    clf = LogisticRegression(C=1.0, max_iter=300, class_weight="balanced", random_state=seed)
    clf.fit(X, y)

    out = np.zeros(fp.shape, dtype=np.float32)
    h = fp.shape[0]
    for r0 in range(0, h, 512):
        r1 = min(h, r0 + 512)
        m = fp[r0:r1]
        if not m.any():
            continue
        Xc = np.column_stack([_get(k)[r0:r1][m].astype(np.float32) for k in EXPOSURE_FEATURE_NAMES])
        block = out[r0:r1]
        block[m] = clf.predict_proba(Xc)[:, 1].astype(np.float32)

    # Calibrate 5th..95th percentile linearly onto [0.05, 0.85] (clipped to [0.03, 0.90])
    lo, hi = np.percentile(out[fp], [5.0, 95.0])
    span = max(float(hi - lo), 1e-5)
    calibrated = np.clip(0.05 + 0.80 * ((out - float(lo)) / span), 0.03, 0.90)
    return np.where(fp, calibrated, 0.0).astype(np.float32)


__all__ = [
    "ALL_PLANE_NAMES",
    "DEEP_FEATURE_NAMES",
    "ELASTIC_COUPLED_NAMES",
    "EXPOSURE_FEATURE_NAMES",
    "FORBIDDEN_GDR_COLUMNS",
    "build_csgd_planes",
    "compute_cross_spectral_admittance_residual",
    "compute_elastic_fields",
    "compute_sar_exposure_propensity",
    "load_gdr_thermal_and_vent_fields",
]
