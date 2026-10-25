"""Feature physics and fold-visible elastic crack-mechanics for H86F-EWCS.

Zero-leakage contract:
- ``build_static_features`` reads ONLY the 19 competition bands in
  ``training_features.tif`` (band indices verified in ``gems86.io.BANDS``) and the
  grid footprint mask. It never opens ``existing_faults.tif`` or any fault table.
- ``compute_elastic_fields`` takes ONLY ``vis_cat`` (the fold-visible fault mask
  for a buffered holdout fold, or full catalogue only after pre-placement checks)
  and never accesses withheld fault segments.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from gems86.io import read_band

STATIC_FEATURE_NAMES: tuple[str, ...] = (
    # Harmonic potential-field block (pixel-verified Band 3/9 tilt & Band 18/11 vector gravity)
    "theta_mag_abs",
    "verduzco_tilt_depth_inv_s2",
    "verduzco_tilt_depth_inv_s5",
    "laplace_gzz_zerocross_s3",
    "laplace_gzz_zerocross_s6",
    "poisson_tensor_misalign_s4",
    "grav_vec_mag_s2",
    "base_hinge_curv_s4",
    "rtp_grad_s2",
    # Radiometric surficial decoupling & crustal fluid / strain / seismicity block
    "tc_decouple_quiet",
    "cond_smectite_s2",
    "strain_dilat_norm",
    "strain_transtens",
    "eq_prox_exp",
    # Surface geomorphic block (excluded in cover-blind arm E2)
    "dem_hess_scarp_s2",
    "dem_hess_scarp_s5",
    "slope_local",
    "piedmont_relief_ratio",
)

TOPO_FEATURE_NAMES: frozenset[str] = frozenset({
    "dem_hess_scarp_s2",
    "dem_hess_scarp_s5",
    "slope_local",
    "piedmont_relief_ratio",
})

# Unsigned baseline subset for E3 ablation (excludes Verduzco tilt-depth, Laplace g_zz, & Poisson misalignment)
E3_STATIC_SUBSET: tuple[str, ...] = (
    "grav_vec_mag_s2",
    "base_hinge_curv_s4",
    "rtp_grad_s2",
    "tc_decouple_quiet",
    "cond_smectite_s2",
    "strain_dilat_norm",
    "strain_transtens",
    "eq_prox_exp",
    "dem_hess_scarp_s2",
    "dem_hess_scarp_s5",
    "slope_local",
    "piedmont_relief_ratio",
)

ELASTIC_COUPLED_NAMES: tuple[str, ...] = (
    "wing_crack_lobe",
    "collinear_tip_cone",
    "stepover_bridge",
    "broadside_stress_shadow",
)


def fill_outside_footprint(arr: np.ndarray, footprint: np.ndarray,
                           nearest_idx: tuple[np.ndarray, np.ndarray] | None = None) -> np.ndarray:
    """Replace outside-footprint nodata with nearest valid footprint value before smoothing."""
    a = np.asarray(arr, dtype=np.float32)
    valid = footprint & np.isfinite(a) & (np.abs(a) < 1e20)
    if not valid.any():
        return np.zeros_like(a, dtype=np.float32)
    if nearest_idx is None:
        _, (iy, ix) = ndi.distance_transform_edt(~valid, return_indices=True)
    else:
        iy, ix = nearest_idx
    out = a.copy()
    bad = ~valid
    out[bad] = a[iy[bad], ix[bad]]
    return out


def compute_laplace_gzz_and_curl(b18_east: np.ndarray, b11_south: np.ndarray,
                                 sigma: float) -> tuple[np.ndarray, np.ndarray]:
    """Compute source-free Laplace vertical gravity curvature g_zz and discrete curl defect.

    Verified convention (src/gems86/io.py, IR-86-BAND11-18-GRAV-VECTOR-20261024):
      - ``b18_east`` = +dg/dx_east = +dg/dcol (axis 1)
      - ``b11_south`` = +dg/drow_south = -dg/dy_north (axis 0)
    Therefore horizontal Laplacian is:
      d^2g/dx_east^2 + d^2g/dy_north^2 = d(b18_east)/dcol + d(b11_south)/drow
    and by Laplace's equation (nabla^2 g = 0 in source-free upper half-space):
      g_zz = -(d(b18_east)/dcol + d(b11_south)/drow).
    Conservative horizontal vector field also satisfies zero curl:
      d(b18_east)/drow - d(b11_south)/dcol == 0.
    """
    dg_xx = ndi.gaussian_filter(b18_east, sigma, order=(0, 1))
    dg_yy = ndi.gaussian_filter(b11_south, sigma, order=(1, 0))
    g_zz = -(dg_xx + dg_yy)

    d18_drow = ndi.gaussian_filter(b18_east, sigma, order=(1, 0))
    d11_dcol = ndi.gaussian_filter(b11_south, sigma, order=(0, 1))
    curl_defect = np.abs(d18_drow - d11_dcol)
    return g_zz.astype(np.float32), curl_defect.astype(np.float32)


def _zerocross_sharpness(field: np.ndarray, footprint: np.ndarray,
                         sigma_grad: float = 1.5, width_frac: float = 0.45) -> np.ndarray:
    """Measure contact steepness |grad field| localized along zero-crossings field == 0."""
    gy = ndi.gaussian_filter(field, sigma_grad, order=(1, 0))
    gx = ndi.gaussian_filter(field, sigma_grad, order=(0, 1))
    gmag = np.hypot(gx, gy)
    scale = float(np.std(field[footprint])) if footprint.any() else 1.0
    scale = max(scale * width_frac, 1e-6)
    zweight = np.exp(-((field / scale) ** 2))
    return (gmag * zweight).astype(np.float32)


def _principal_axis_spin2(field: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    """Return unit spin-2 orientation (cos 2psi, sin 2psi) of Hessian principal curvature."""
    fxx = ndi.gaussian_filter(field, sigma, order=(0, 2))
    fyy = ndi.gaussian_filter(field, sigma, order=(2, 0))
    fxy = ndi.gaussian_filter(field, sigma, order=(1, 1))
    dx = fxx - fyy
    dy = 2.0 * fxy
    norm = np.hypot(dx, dy) + 1e-8
    return (dx / norm).astype(np.float32), (dy / norm).astype(np.float32)


def _hessian_ridge_abs(field: np.ndarray, sigma: float) -> np.ndarray:
    fxx = ndi.gaussian_filter(field, sigma, order=(0, 2))
    fyy = ndi.gaussian_filter(field, sigma, order=(2, 0))
    fxy = ndi.gaussian_filter(field, sigma, order=(1, 1))
    tr = 0.5 * (fxx + fyy)
    disc = np.sqrt(0.25 * (fxx - fyy) ** 2 + fxy ** 2)
    eig1 = np.abs(tr + disc)
    eig2 = np.abs(tr - disc)
    return (np.maximum(eig1, eig2) * (sigma * sigma)).astype(np.float32)


def _robust_standardize(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    a = np.asarray(arr, dtype=np.float32)
    if not footprint.any():
        return np.zeros_like(a, dtype=np.float32)
    vals = a[footprint]
    lo, hi = np.percentile(vals, [1.0, 99.0])
    scale = max(float(hi - lo), 1e-6)
    normed = np.clip((a - float(lo)) / scale, -2.0, 4.0)
    return np.where(footprint, normed, 0.0).astype(np.float32)


def build_static_features(features_tif: Path, footprint: np.ndarray,
                          out_memmap_path: Path | None = None) -> dict[str, np.ndarray] | np.ndarray:
    """Compute all 18 label-free geophysical/geomorphic planes on ``footprint``.

    When ``out_memmap_path`` is supplied, planes are streamed into a ``float16``
    memory-mapped file ``(18, H, W)`` one block at a time and returned as a
    read-only ``mmap_mode='r'`` view so peak RSS stays well below 1 GiB.
    """
    import gc

    fp = np.asarray(footprint, dtype=bool)
    elev_raw = read_band(features_tif, "det_elev")
    valid0 = fp & np.isfinite(elev_raw) & (np.abs(elev_raw) < 1e20)
    _, nearest_idx = ndi.distance_transform_edt(~valid0, return_indices=True)

    def load(name: str) -> np.ndarray:
        return fill_outside_footprint(read_band(features_tif, name), fp, nearest_idx)

    mm = None
    out: dict[str, np.ndarray] = {}
    if out_memmap_path is not None:
        out_memmap_path.parent.mkdir(parents=True, exist_ok=True)
        mm = np.lib.format.open_memmap(
            out_memmap_path, mode="w+", dtype=np.float16,
            shape=(len(STATIC_FEATURE_NAMES), fp.shape[0], fp.shape[1]),
        )

    def store(key: str, arr: np.ndarray) -> None:
        std_arr = _robust_standardize(arr, fp)
        if mm is not None:
            mm[STATIC_FEATURE_NAMES.index(key)] = std_arr.astype(np.float16)
        else:
            out[key] = std_arr

    # 1. Verduzco analytical magnetic tilt & tilt-depth contact sharpness (Bands 3, 9, 2)
    tmi_hg = np.maximum(load("tmi_hg"), 1e-6)
    tmi_vg = load("tmi_vg")
    theta_mag = np.arctan2(tmi_vg, tmi_hg).astype(np.float32)
    del tmi_hg, tmi_vg
    store("theta_mag_abs", np.abs(theta_mag))

    for s, key in ((2.0, "verduzco_tilt_depth_inv_s2"), (5.0, "verduzco_tilt_depth_inv_s5")):
        th_s = ndi.gaussian_filter(theta_mag, s)
        gy = ndi.gaussian_filter(th_s, 1.0, order=(1, 0))
        gx = ndi.gaussian_filter(th_s, 1.0, order=(0, 1))
        inv_depth = np.hypot(gx, gy) * np.exp(-((th_s / 0.35) ** 2))
        store(key, inv_depth)
        del th_s, gy, gx, inv_depth
    del theta_mag
    gc.collect()

    # 2. Vector-consistent Laplace vertical gravity curvature g_zz & curl veto (Bands 18, 11)
    b18 = load("iso_grav_anom_hg")
    b11 = load("iso_grav_anom_vg")
    gzz3, curl3 = compute_laplace_gzz_and_curl(b18, b11, sigma=3.0)
    curl_med = max(float(np.median(curl3[fp])), 1e-6) if fp.any() else 1.0
    curl_veto = (1.0 / (1.0 + (curl3 / (2.5 * curl_med)) ** 2)).astype(np.float32)
    del curl3
    store("laplace_gzz_zerocross_s3", _zerocross_sharpness(gzz3, fp, sigma_grad=1.5) * curl_veto)
    del gzz3
    gzz6, _ = compute_laplace_gzz_and_curl(b18, b11, sigma=6.0)
    store("laplace_gzz_zerocross_s6", _zerocross_sharpness(gzz6, fp, sigma_grad=2.0) * curl_veto)
    del gzz6
    gvec = ndi.gaussian_filter(np.hypot(b18, b11), 2.0).astype(np.float32)
    del b18, b11
    store("grav_vec_mag_s2", gvec)
    gc.collect()

    # 3. Garland-Poisson gravity-magnetic Hessian axis misalignment (Bands 13, 2)
    iso_g = load("iso_grav_anom")
    cg, sg = _principal_axis_spin2(iso_g, sigma=4.0)
    del iso_g
    rtp = load("rtp")
    cm, sm = _principal_axis_spin2(rtp, sigma=4.0)
    cos2_diff = np.clip(cg * cm + sg * sm, -1.0, 1.0)
    del cg, sg, cm, sm
    sin2_misalign = 0.5 * (1.0 - cos2_diff)
    del cos2_diff
    rtp_gx = ndi.gaussian_filter(rtp, 2.0, order=(0, 1))
    rtp_gy = ndi.gaussian_filter(rtp, 2.0, order=(1, 0))
    del rtp
    rtp_gm = np.hypot(rtp_gx, rtp_gy).astype(np.float32)
    del rtp_gx, rtp_gy
    g_scale = max(float(np.percentile(gvec[fp], 75)), 1e-6) if fp.any() else 1.0
    m_scale = max(float(np.percentile(rtp_gm[fp], 75)), 1e-6) if fp.any() else 1.0
    poisson_break = sin2_misalign * np.tanh(gvec / g_scale) * np.tanh(rtp_gm / m_scale) * curl_veto
    store("poisson_tensor_misalign_s4", poisson_break)
    store("rtp_grad_s2", rtp_gm)
    del sin2_misalign, rtp_gm, gvec, curl_veto, poisson_break
    gc.collect()

    # 4. Basement hinge curvature (Band 15) & Radiometric TC surficial decoupling (Band 6)
    base_d = load("depth_to_base_surf")
    store("base_hinge_curv_s4", _hessian_ridge_abs(base_d, sigma=4.0))
    del base_d

    tc = load("tc")
    tc_gm = np.hypot(
        ndi.gaussian_filter(tc, 2.0, order=(0, 1)),
        ndi.gaussian_filter(tc, 2.0, order=(1, 0)),
    )
    del tc
    tc_med = max(float(np.median(tc_gm[fp])), 1e-6) if fp.any() else 1.0
    store("tc_decouple_quiet", 1.0 / (1.0 + tc_gm / tc_med))
    del tc_gm
    gc.collect()

    # 5. Crustal fluid conductivity, geodetic strain invariants & microseismicity (Bands 17, 8, 7, 4, 10, 16)
    cond = load("cond_surf")
    store("cond_smectite_s2", ndi.gaussian_filter(cond, 2.0))
    del cond

    dilat = load("geod_dilaterate")
    shear = load("geod_shearrate")
    inv2 = load("geod_2ndinv")
    store("strain_dilat_norm", dilat)
    pos_dilat = np.maximum(dilat - float(np.median(dilat[fp]) if fp.any() else 0.0), 0.0)
    store("strain_transtens", np.sqrt(np.maximum(shear, 0.0) * pos_dilat + 1e-12) + 0.25 * inv2)
    del dilat, shear, inv2, pos_dilat

    eq_d = np.maximum(load("deq_n100a15"), 0.0)
    ieq = load("ieq_n100a15")
    eq_scale = max(float(np.median(eq_d[fp])), 1.0) if fp.any() else 1000.0
    store(
        "eq_prox_exp",
        0.5 * np.exp(-eq_d / (0.5 * eq_scale)) + 0.5 * np.tanh(np.maximum(ieq, 0.0)),
    )
    del eq_d, ieq
    gc.collect()

    # 6. Geomorphic scarp / piedmont curvature block (Bands 12, 19)
    elev = fill_outside_footprint(elev_raw, fp, nearest_idx)
    del elev_raw, nearest_idx
    store("dem_hess_scarp_s2", _hessian_ridge_abs(elev, sigma=2.0))
    store("dem_hess_scarp_s5", _hessian_ridge_abs(elev, sigma=5.0))
    rel_short = ndi.maximum_filter(elev, size=5) - ndi.minimum_filter(elev, size=5)
    rel_long = ndi.maximum_filter(elev, size=25) - ndi.minimum_filter(elev, size=25)
    store("piedmont_relief_ratio", rel_short / (rel_long + 5.0))
    del elev, rel_short, rel_long

    slope = read_band(features_tif, "det_elev_slope")
    store("slope_local", np.where(fp & np.isfinite(slope) & (np.abs(slope) < 1e20), slope, 0.0))
    del slope
    gc.collect()

    if mm is not None:
        mm.flush()
        del mm
        return np.load(out_memmap_path, mmap_mode="r")
    return out


def compute_elastic_fields(vis_cat: np.ndarray, footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Compute strictly fold-visible Pollard-Segall crack-tip & broadside stress-shadow fields.

    Uses center-of-mass half-space asymmetry at sigma=6 px to identify fault
    terminations and their exact outward propagation unit vectors without any
    access to withheld fault segments.
    """
    fp = np.asarray(footprint, dtype=bool)
    v = (np.asarray(vis_cat, dtype=bool) & fp).astype(np.float32)
    h, w = fp.shape
    if v.sum() == 0:
        zeros = np.zeros((h, w), dtype=np.float32)
        return {k: zeros.copy() for k in (*ELASTIC_COUPLED_NAMES, "iso_tip_halo")}

    yy, xx = np.indices((h, w), dtype=np.float32)
    sigma_tip = 6.0
    mass = ndi.gaussian_filter(v, sigma_tip) + 1e-8
    mx = ndi.gaussian_filter(v * xx, sigma_tip) / mass - xx
    my = ndi.gaussian_filter(v * yy, sigma_tip) / mass - yy
    asym = np.hypot(mx, my)

    # Interior fault pixels have symmetric mass (asym ~ 0); terminations have asym >= 2.2 px
    # Outward propagation unit vector points AWAY from existing fault mass: (-mx, -my) / asym
    ux_prop = np.where(asym > 1e-4, -mx / (asym + 1e-6), 0.0).astype(np.float32)
    uy_prop = np.where(asym > 1e-4, -my / (asym + 1e-6), 0.0).astype(np.float32)
    tip_ness = np.clip((asym - 1.6) / 2.6, 0.0, 1.0) * (v > 0.5)
    tip_mask = (v > 0.5) & (asym >= 2.2)
    if not tip_mask.any():
        tip_mask = v > 0.5

    # Local interior fault tangent from smoothed fault density gradient (normal is grad(mass_s2))
    mass_s2 = ndi.gaussian_filter(v, 2.5)
    ny = ndi.gaussian_filter(mass_s2, 1.0, order=(1, 0))
    nx = ndi.gaussian_filter(mass_s2, 1.0, order=(0, 1))
    nnorm = np.hypot(nx, ny) + 1e-6
    # Tangent perpendicular to normal: (-ny, nx)
    tx_tan = (-ny / nnorm).astype(np.float32)
    ty_tan = (nx / nnorm).astype(np.float32)

    # Distance & nearest-tip projection for forward wing-crack lobes and collinear cones
    r_tip_f64, (ty_i, tx_i) = ndi.distance_transform_edt(~tip_mask, return_indices=True)
    r_tip = r_tip_f64.astype(np.float32)
    del r_tip_f64, tip_mask
    dx_t = xx - tx_i.astype(np.float32)
    dy_t = yy - ty_i.astype(np.float32)
    ux_near = ux_prop[ty_i, tx_i]
    uy_near = uy_prop[ty_i, tx_i]
    del ty_i, tx_i
    cos_a = np.clip((dx_t * ux_near + dy_t * uy_near) / (r_tip + 1e-5), -1.0, 1.0)
    del dx_t, dy_t, ux_near, uy_near
    forward = np.maximum(cos_a, 0.0)
    alpha_abs = np.arccos(np.clip(cos_a, -1.0, 1.0))
    del cos_a

    # Pollard & Segall (1987) off-axis tensile wing-crack lobes (~27 deg = 0.47 rad off tip axis)
    wing_angular = (forward ** 1.2) * np.exp(-(((alpha_abs - 0.47) / 0.30) ** 2))
    del alpha_abs
    wing_crack_lobe = _robust_standardize(
        np.exp(-r_tip / 28.0) * wing_angular * (r_tip > 2.0), fp
    ).astype(np.float16)
    del wing_angular

    # Collinear tip propagation cone across alluvial canyon gaps
    collinear_tip_cone = _robust_standardize(
        np.exp(-r_tip / 30.0) * (forward ** 3.0) * (r_tip > 2.0), fp
    ).astype(np.float16)
    del forward

    iso_tip_halo = _robust_standardize(
        np.exp(-r_tip / 30.0) * (r_tip > 2.0), fp
    ).astype(np.float16)
    del r_tip

    # Opposing-tip releasing-stepover bridge: high scalar tip density where vector sum cancels
    tip_wt = tip_ness.astype(np.float32)
    scalar_tip = ndi.gaussian_filter(tip_wt, 18.0)
    vec_x = ndi.gaussian_filter(tip_wt * ux_prop, 18.0)
    vec_y = ndi.gaussian_filter(tip_wt * uy_prop, 18.0)
    del tip_wt, ux_prop, uy_prop, mx, my, asym
    opposing = np.maximum(scalar_tip ** 2 - (vec_x ** 2 + vec_y ** 2), 0.0)
    del scalar_tip, vec_x, vec_y
    stepover_bridge = _robust_standardize(np.sqrt(opposing), fp).astype(np.float16)
    del opposing

    # Broadside mid-segment elastic stress-release shadow (3 < d_vis <= 24 px, perpendicular to interior segment)
    d_vis_f64, (vy_i, vx_i) = ndi.distance_transform_edt(~(v > 0.5), return_indices=True)
    d_vis = d_vis_f64.astype(np.float32)
    del d_vis_f64, v
    dx_v = xx - vx_i.astype(np.float32)
    dy_v = yy - vy_i.astype(np.float32)
    del xx, yy
    interior_wt = 1.0 - tip_ness[vy_i, vx_i]
    del tip_ness
    along_tan = np.abs(dx_v * tx_tan[vy_i, vx_i] + dy_v * ty_tan[vy_i, vx_i]) / (d_vis + 1e-5)
    del dx_v, dy_v, vy_i, vx_i, tx_tan, ty_tan
    broadside_orient = np.clip(1.0 - (along_tan / 0.40) ** 2, 0.0, 1.0)
    del along_tan
    radial_band = np.exp(-(((d_vis - 9.0) / 7.5) ** 2)) * (d_vis > 3.0)
    del d_vis
    broadside_stress_shadow = _robust_standardize(
        interior_wt * broadside_orient * radial_band, fp
    ).astype(np.float16)
    del interior_wt, broadside_orient, radial_band

    return {
        "wing_crack_lobe": wing_crack_lobe,
        "collinear_tip_cone": collinear_tip_cone,
        "stepover_bridge": stepover_bridge,
        "broadside_stress_shadow": broadside_stress_shadow,
        "iso_tip_halo": iso_tip_halo,
    }
