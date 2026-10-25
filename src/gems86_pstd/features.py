"""Catalogue-blind Poisson potential-field dislocation & Laplace-gravity hinge operators (H86H-PSTD).

Physics & Coordinate Verification
---------------------------------
All band indices match ``src/gems86/io.py::BANDS`` and the empirical pixel-level
physics audit ``docs/evidence/band-physics-verification-20261024.json``:
- Band 2: ``rtp`` (reduced-to-pole magnetic anomaly)
- Band 3: ``tmi_hg`` (horizontal magnetic gradient magnitude)
- Band 7: ``geod_shearrate`` (GPS shear strain rate)
- Band 8: ``geod_dilaterate`` (GPS dilatation rate)
- Band 9: ``tmi_vg`` (vertical magnetic derivative M_z)
- Band 11: ``iso_grav_anom_vg`` -> +dg_iso/drow_south = -dg_iso/dy_north
- Band 17: ``cond_surf`` (surface electrical conductance)
- Band 18: ``iso_grav_anom_hg`` -> +dg_iso/dcol_east = +dg_iso/dx_east
- Band 19: ``det_elev_slope`` (detrended topographic slope)

In raster coordinates (col increases eastward, row increases southward):
    g_east = +Band 18,    g_south = +Band 11 = -g_north
Therefore Laplace's potential-field equation (g_xx + g_yy + g_zz = 0) yields:
    g_zz = -(dg_east/dx_east + dg_north/dy_north)
         = -(d(Band 18)/dcol + d(Band 11)/drow)
regularized at sigma = 5.0 px (500 m) with footprint-normalized Gaussian
smoothing so outside-footprint NoData sentinels (-3.4028e+38) never bleed inward.

By Poisson's potential-field theorem (Poisson 1826; Cordell & Taylor 1971), an
unfaulted homogeneous source body with magnetization-to-density contrast ratio
alpha = dJ / (G * drho) obeys M_z = alpha * g_zz + c locally. Hydrothermal
fluid circulation along permeable basement-bounding fault conduits destroys
magnetite (Fe3O4 -> pyrite/leucoxene) while preserving bulk basement density
juxtaposition, creating a positive magnetite-destruction Poisson residual:
    R_Poisson = max(0, alpha_flank * z(g_zz) + c_flank - z(M_z))
localized along gravity-gradient structure-tensor hinges |grad_h g|.

NOTE: ``existing_faults.tif`` is NEVER read or referenced anywhere in this module.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi

NODATA_FLOOR = -1.0e37

FEATURE_NAMES = (
    "laplace_gzz_hinge",
    "grav_tensor_anisotropy",
    "poisson_mag_destruction_residual",
    "poisson_mag_excess_control",
    "strain_coulomb_favorability",
    "cond_alteration_gate",
    "low_relief_piedmont_gate",
)


def _clean_band(raw: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    valid = footprint & np.isfinite(raw) & (raw > NODATA_FLOOR)
    med = float(np.median(raw[valid])) if np.any(valid) else 0.0
    out = np.where(valid, raw.astype(np.float32, copy=False), np.float32(med))
    out = np.where(footprint, out, np.float32(0.0))
    return out, valid.astype(np.float32)


def _smooth_masked(arr: np.ndarray, weights: np.ndarray, sigma_px: float) -> np.ndarray:
    if sigma_px <= 0.0:
        return np.where(weights > 0.0, arr, np.float32(0.0)).astype(np.float32)
    num = ndi.gaussian_filter((arr * weights).astype(np.float32), sigma=float(sigma_px), mode="nearest")
    den = ndi.gaussian_filter(weights.astype(np.float32), sigma=float(sigma_px), mode="nearest")
    return np.where(den > 1e-5, num / np.maximum(den, np.float32(1e-5)), np.float32(0.0)).astype(np.float32)


def _robust_z(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    vals = arr[footprint]
    if vals.size == 0:
        return np.zeros_like(arr, dtype=np.float32)
    med = float(np.median(vals))
    iqr = float(np.percentile(vals, 75.0) - np.percentile(vals, 25.0))
    scale = max(iqr / 1.3489795, 1e-6)
    z = (arr.astype(np.float32) - np.float32(med)) / np.float32(scale)
    return np.where(footprint, np.clip(z, -8.0, 8.0), np.float32(0.0)).astype(np.float32)


def _rank01(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    out = np.zeros(arr.shape, dtype=np.float32)
    vals = arr[footprint]
    n = vals.size
    if n <= 1:
        return out
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(n, dtype=np.float32)
    ranks[order] = np.linspace(0.0, 1.0, n, dtype=np.float32)
    out[footprint] = ranks
    return out


def compute_pstd_arrays(
    *,
    b2_rtp: np.ndarray,
    b3_tmi_hg: np.ndarray,
    b7_shear: np.ndarray,
    b8_dilate: np.ndarray,
    b9_tmi_vg: np.ndarray,
    b11_grav_south: np.ndarray,
    b17_cond: np.ndarray,
    b18_grav_east: np.ndarray,
    b19_slope: np.ndarray,
    footprint: np.ndarray,
    dx_km: float = 0.1,
    dy_km: float = 0.1,
    sigma_grav_px: float = 5.0,
    sigma_flank_px: float = 12.0,
) -> dict[str, np.ndarray]:
    """Compute catalogue-blind H86H-PSTD geophysical feature planes from raw arrays."""
    fp = np.asarray(footprint, dtype=bool)
    _, w2 = _clean_band(b2_rtp, fp)
    c3, w3 = _clean_band(b3_tmi_hg, fp)
    c7, _ = _clean_band(b7_shear, fp)
    c8, _ = _clean_band(b8_dilate, fp)
    c9, w9 = _clean_band(b9_tmi_vg, fp)
    c11, w11 = _clean_band(b11_grav_south, fp)
    c17, _ = _clean_band(b17_cond, fp)
    c18, w18 = _clean_band(b18_grav_east, fp)
    c19, _ = _clean_band(b19_slope, fp)

    w_grav = np.minimum(w11, w18)
    g_east = _smooth_masked(c18, w_grav, sigma_grav_px)
    g_south = _smooth_masked(c11, w_grav, sigma_grav_px)

    # Interior safety mask: prevent edge derivative spikes at footprint border
    interior = ndi.binary_erosion(w_grav > 0.5, iterations=2) & fp
    dg_east_dcol = np.gradient(g_east, float(dx_km), axis=1).astype(np.float32)
    dg_south_drow = np.gradient(g_south, float(dy_km), axis=0).astype(np.float32)

    # Verified Laplace vertical curvature: g_zz = -(d B18 / dcol + d B11 / drow)
    g_zz = np.where(interior, -(dg_east_dcol + dg_south_drow), np.float32(0.0))
    z_gzz = _robust_z(g_zz, fp)

    # Gravity-gradient hinge & structure-tensor strike coherence
    grad_mag = np.hypot(g_east, g_south).astype(np.float32)
    j_xx = _smooth_masked(g_east * g_east, w_grav, sigma_grav_px)
    j_yy = _smooth_masked(g_south * g_south, w_grav, sigma_grav_px)
    j_xy = _smooth_masked(g_east * g_south, w_grav, sigma_grav_px)
    trace = j_xx + j_yy + np.float32(1e-8)
    anisotropy = np.sqrt(np.maximum((j_xx - j_yy) ** 2 + np.float32(4.0) * (j_xy ** 2), np.float32(0.0))) / trace
    grav_tensor_anisotropy = np.where(fp, np.clip(anisotropy, 0.0, 1.0), np.float32(0.0)).astype(np.float32)

    # Zero-crossing / steepest inflection of g_zz sits directly over steep density contacts
    dgzz_dr, dgzz_dc = np.gradient(z_gzz, float(dy_km), float(dx_km))
    gzz_grad = np.where(interior, np.hypot(dgzz_dr, dgzz_dc).astype(np.float32), np.float32(0.0))
    laplace_gzz_hinge = _rank01(grad_mag * (np.float32(0.5) + _rank01(gzz_grad, fp)), fp)

    # Local flank Poisson regression: z(M_z) ~ alpha_flank * z(g_zz) + c_flank over sigma_flank_px (1.2 km)
    w_mag = np.minimum(w_grav, np.minimum(w9, np.minimum(w2, w3)))
    m_z_reg = _smooth_masked(c9, w_mag, max(1.5, 0.3 * sigma_grav_px))
    z_mz = _robust_z(m_z_reg, fp)

    mu_x = _smooth_masked(z_gzz, w_mag, sigma_flank_px)
    mu_y = _smooth_masked(z_mz, w_mag, sigma_flank_px)
    cov_xy = _smooth_masked(z_gzz * z_mz, w_mag, sigma_flank_px) - mu_x * mu_y
    var_x = np.maximum(_smooth_masked(z_gzz * z_gzz, w_mag, sigma_flank_px) - mu_x * mu_x, np.float32(0.05))
    alpha_flank = np.clip(cov_xy / (var_x + np.float32(0.25)), np.float32(-3.0), np.float32(3.0))
    z_mz_pred = alpha_flank * (z_gzz - mu_x) + mu_y

    # Hydrothermal magnetite destruction creates M_z deficit relative to flank Poisson prediction,
    # corroborated by analytical magnetic tilt sharpening |tmi_hg| / (|tmi_vg| + eps)
    mag_hg_z = _rank01(_smooth_masked(c3, w3, 1.5), fp)
    raw_deficit = np.maximum(z_mz_pred - z_mz, np.float32(0.0))
    raw_excess = np.maximum(z_mz - z_mz_pred, np.float32(0.0))

    poisson_mag_destruction_residual = _rank01(
        np.where(interior, raw_deficit * (np.float32(0.5) + np.float32(0.5) * mag_hg_z), np.float32(0.0)),
        fp,
    )
    poisson_mag_excess_control = _rank01(
        np.where(interior, raw_excess * (np.float32(0.5) + np.float32(0.5) * mag_hg_z), np.float32(0.0)),
        fp,
    )

    # Active crustal strain favorability (dilatation + shear rate)
    z_dil = _robust_z(c8, fp)
    z_shr = _robust_z(c7, fp)
    strain_coulomb_favorability = _rank01(np.float32(0.65) * z_dil + np.float32(0.35) * z_shr, fp)

    # Moderate shallow conductance gate (clay/smectite alteration while tapering extreme flat salt-pan maxima)
    z_cond = _robust_z(c17, fp)
    cond_bell = np.tanh(np.maximum(z_cond + np.float32(0.5), np.float32(0.0))) * np.exp(
        -np.maximum(z_cond - np.float32(2.5), np.float32(0.0)) ** 2 / np.float32(8.0)
    )
    cond_alteration_gate = _rank01(cond_bell.astype(np.float32), fp)

    # Low-to-moderate piedmont/intrabasin slope gate (concealed alluvial/pediment cover vs bare steep cliffs)
    slope_r = _rank01(c19, fp)
    piedmont_weight = np.float32(1.0) - np.float32(0.55) * (slope_r - np.float32(0.45)) ** 2
    low_relief_piedmont_gate = _rank01(piedmont_weight, fp)

    return {
        "laplace_gzz_hinge": laplace_gzz_hinge,
        "grav_tensor_anisotropy": grav_tensor_anisotropy,
        "poisson_mag_destruction_residual": poisson_mag_destruction_residual,
        "poisson_mag_excess_control": poisson_mag_excess_control,
        "strain_coulomb_favorability": strain_coulomb_favorability,
        "cond_alteration_gate": cond_alteration_gate,
        "low_relief_piedmont_gate": low_relief_piedmont_gate,
    }


def build_pstd_features(features_tif: Path, footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Load verified native bands from training_features.tif and build H86H-PSTD planes."""
    with rasterio.open(features_tif) as ds:
        dx_km = abs(float(ds.transform.a)) / 1000.0
        dy_km = abs(float(ds.transform.e)) / 1000.0
        b2 = ds.read(2)
        b3 = ds.read(3)
        b7 = ds.read(7)
        b8 = ds.read(8)
        b9 = ds.read(9)
        b11 = ds.read(11)
        b17 = ds.read(17)
        b18 = ds.read(18)
        b19 = ds.read(19)
    return compute_pstd_arrays(
        b2_rtp=b2,
        b3_tmi_hg=b3,
        b7_shear=b7,
        b8_dilate=b8,
        b9_tmi_vg=b9,
        b11_grav_south=b11,
        b17_cond=b17,
        b18_grav_east=b18,
        b19_slope=b19,
        footprint=footprint,
        dx_km=dx_km,
        dy_km=dy_km,
    )


def compose_pstd_arms(planes: dict[str, np.ndarray], footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Compose the three preregistered [0, 1] surfaces for H86H-PSTD (E1, E2, E3)."""
    fp = np.asarray(footprint, dtype=bool)
    hinge = planes["laplace_gzz_hinge"]
    aniso = planes["grav_tensor_anisotropy"]
    p_def = planes["poisson_mag_destruction_residual"]
    p_exc = planes["poisson_mag_excess_control"]
    strain = planes["strain_coulomb_favorability"]
    cond = planes["cond_alteration_gate"]
    piedmont = planes["low_relief_piedmont_gate"]

    geopotential_core = (
        np.float32(0.42) * p_def
        + np.float32(0.38) * hinge
        + np.float32(0.20) * aniso
    ) * (np.float32(0.50) + np.float32(0.50) * hinge * p_def)

    context_mod = (
        np.float32(0.45) * strain
        + np.float32(0.30) * cond
        + np.float32(0.25) * piedmont
    )
    e1_raw = geopotential_core * (np.float32(0.55) + np.float32(0.45) * context_mod)
    e2_raw = geopotential_core
    e3_raw = (
        np.float32(0.42) * p_exc
        + np.float32(0.38) * hinge
        + np.float32(0.20) * aniso
    ) * (np.float32(0.50) + np.float32(0.50) * hinge * p_exc)

    return {
        "E1_pstd_full": _rank01(e1_raw, fp),
        "E2_pstd_geopotential_only": _rank01(e2_raw, fp),
        "E3_pstd_inverted_polarity_control": _rank01(e3_raw, fp),
    }
