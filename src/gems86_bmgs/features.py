"""Cover-blind multi-physics feature builder for Lane H86M-BMGS.

Implements three untried physics mechanisms synthesized from the queued GEMSDOE86
research backlog while enforcing strict zero-leakage and low-memory guarantees:

1. Out-of-Quadrant (``quad != q``, zero fault labels) 2-D FFT Upward-Continued
   Athy-Compacted Basement Mass-Balance Gravity Residual (``BMR``):
   predicts smooth Cenozoic sediment-fill gravity from ``Band 15``
   (``depth_to_base_surf``) at ``z = 200 m, 800 m`` plus Athy compaction
   ``Z_b^2 / (Z_b + 1200 m)`` and ``z = 4000 m`` regional baseline, subtracting it
   from ``Band 13`` (``iso_grav_anom``) to isolate intrabasin horst/relay density
   steps, Laplace ``g_zz`` zero-crossing sharpness, and vector angular discordance
   against verified ``(Band 18 = +dg/dx_east, Band 11 = +dg/drow_south)``.
2. 8-Azimuth Steerable Quadrature Odd-Step vs Even-Dike Phase Asymmetry (``GSST``):
   evaluates paired odd-symmetric fault-step filters ``O_theta`` and even-symmetric
   dike/channel ridge filters ``E_theta`` across 8 azimuths at ``sigma = (2.0, 4.5)``
   px, computing ``relu(|O_theta| - 0.85 * E_env_theta)`` on seam-vetoed ``Band 2``
   (``rtp``) and ``r_BMR`` to suppress Northern Nevada Rift mafic dike swarms while
   extracting local geophysical strike ``theta_hat in [0, pi)``.
3. Transtensional Conductance-Neck Bridge (``CNT``) & Dilatation-Gated Shallow
   Pullback (``<= 3.0 px`` max shift):
   isolates narrow anisotropic ``Band 17`` (``cond_surf``) saddle necks and horst
   boundary steps gated by positive geodetic dilatation/shear (``Bands 8, 7``),
   and restricts footwall pullback strictly to ``<= 3.0 px`` on shallow normal-fault
   margins (fixing ``GEMSDOE92`` = 0.0255 and ``H86K-STDP`` = 0.1380 deep/strike-slip
   over-shifting).
4. Strictly excludes ``dist_known_fault_px`` from DOE GDR #1391 tables and excludes
   raw 100 m DEM ``Band 12`` / ``Band 19`` feature planes from the cover-blind
   specialist stack ``X_bmgs``.
"""

from __future__ import annotations

import gc
import hashlib
from pathlib import Path
import sys

import numpy as np
from numpy.lib.format import open_memmap
import rasterio
from scipy import ndimage as ndi
from scipy.fft import fftfreq, irfft2, rfft2, rfftfreq

SRC_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = SRC_DIR.parent
for _p in (str(ROOT_DIR), str(SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gems86.io import BANDS, BAND_PHYSICS_VERIFIED, NODATA
from gems86_stdp.features import (
    BANNED_CSV_COLUMNS,
    GDR_AND_AUDIT_PINS,
    _gdr_geothermal_planes,
    _geodawn_seam_keep_mask,
    _masked_gaussian,
    _masked_gradients,
    _rank01,
    _read_ext,
    _read_native,
    _robust_pos_z,
)
from scripts.restore_data import EXTERNAL_PINS

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

BMGS_STATIC_NAMES: tuple[str, ...] = (
    "bmr_resid_grad_z100",
    "bmr_laplace_gzz_s2",
    "bmr_vector_discordance",
    "gsst_rtp_odd_step_seamfree",
    "gsst_bmr_odd_step",
    "gsst_cross_field_spin2",
    "garland_poisson_step",
    "cnt_transtens_cond_neck",
    "cnt_cond_horstsaddle_step",
    "dilatation_gated_shallow_pullback",
    "kostrov_byerlee_dilation_tendency",
    "aseismic_creep_deficit",
    "microseismic_brittle_swarm_hp",
    "tmi_up150_depth_persistence",
    "hydro_magnetite_trough",
    "rad_kth_potassic_seamfree",
    "rad_uth_redox_seamfree",
    "uphead_geotherm_diseq",
    "probe2m_uphead_thermal_wall",
    "paleo_sinter_vent_corridor",
    "lidar1m_scarp_debiased",
    "lidar1m_unilateral_polarity",
    "topo10_piedmont_scarp_break",
    "chi10_fluvial_knick_step",
)

ABLATION_RAW_NAMES: tuple[str, ...] = (
    "raw_grav_slope_b5",
    "raw_depth_gradmag_s3",
    "raw_tmi_hg_b3",
    "raw_cond_iso_blur",
    "raw_elev_slope_b19",
    "raw_topo10_slope_p90",
    "raw_strain_2ndinv_hp",
    "raw_geotherm_iso_blur",
)

# NW Great Basin extension (sigma_3 ~ N112E -> optimal normal strike N22E in grid angle
# measured from +col east toward +row south: compass N22E corresponds to dx=sin(22),
# drow=-cos(22) -> strike angle atan2(-cos(22), sin(22)) mod pi).
_STRIKE_N22E_GRID = float(np.mod(np.arctan2(-np.cos(np.deg2rad(22.0)), np.sin(np.deg2rad(22.0))), np.pi))
# Walker Lane dextral strike ~ N35W -> dx=-sin(35), drow=-cos(35)
_STRIKE_N35W_GRID = float(np.mod(np.arctan2(-np.cos(np.deg2rad(35.0)), -np.sin(np.deg2rad(35.0))), np.pi))


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_bmgs_input_contract(ext_dir: Path | None = None) -> dict:
    """Assert Band 1..19 semantics against src/gems86/io.py and SHA-256 external pins."""
    for idx, expected_name in EXPECTED_NATIVE_BANDS.items():
        actual = BANDS.get(idx)
        if actual != expected_name:
            raise RuntimeError(
                f"Band index mismatch at Band {idx}: expected {expected_name!r}, got {actual!r}"
            )
    if "Total Count" not in BAND_PHYSICS_VERIFIED.get(6, ""):
        raise RuntimeError("Band 6 physics override (GeoDAWN Total Count) missing in io.py")
    if "drow_south" not in BAND_PHYSICS_VERIFIED.get(11, ""):
        raise RuntimeError("Band 11 physics override (+dg/drow_south) missing in io.py")
    if "dx_east" not in BAND_PHYSICS_VERIFIED.get(18, ""):
        raise RuntimeError("Band 18 physics override (+dg/dx_east) missing in io.py")

    ext_verified: dict[str, str] = {}
    if ext_dir is not None:
        all_pins: dict[str, str] = {**EXTERNAL_PINS, **GDR_AND_AUDIT_PINS}
        for fname, expected_sha in sorted(all_pins.items()):
            p = ext_dir / fname
            if not p.is_file():
                raise FileNotFoundError(f"Missing required external input: {p}")
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
        "raw_dem_bands_excluded_from_cover_blind": [12, 19],
    }


def _quadrant_grid(shape: tuple[int, int]) -> np.ndarray:
    h, w = shape
    yy, xx = np.indices((h, w), sparse=True)
    return ((yy >= h // 2).astype(np.int8) * 2 + (xx >= w // 2).astype(np.int8)).astype(np.int8)


def _fft_upward_continue(
    field: np.ndarray,
    valid: np.ndarray,
    altitudes_m: tuple[float, ...],
    *,
    cell_m: float = 100.0,
) -> list[np.ndarray]:
    """2-D FFT harmonic upward continuation exp(-2*pi*z*|k|) with boundary feathering."""
    f = np.asarray(field, dtype=np.float32)
    v = np.asarray(valid, dtype=bool)
    h, w = f.shape
    med = float(np.median(f[v])) if v.any() else 0.0
    taper = ndi.gaussian_filter(v.astype(np.float32), sigma=5.0, mode="constant")
    f_centered = np.where(v, f - med, np.float32(0.0)) * taper
    spec = rfft2(f_centered, s=(h, w))
    del f_centered, taper

    ky = fftfreq(h, d=cell_m).astype(np.float32)[:, None]
    kx = rfftfreq(w, d=cell_m).astype(np.float32)[None, :]
    kr = np.sqrt(kx * kx + ky * ky)
    k_nyq = float(0.5 / cell_m)
    anti_ring = np.exp(-((kr / (0.78 * k_nyq)) ** 4)).astype(np.float32)

    outs: list[np.ndarray] = []
    for z_m in altitudes_m:
        filt = np.exp(-2.0 * np.pi * float(z_m) * kr).astype(np.float32) * anti_ring
        up = (irfft2(spec * filt, s=(h, w)) + med).astype(np.float32)
        up[~v] = med
        outs.append(up)
    return outs


def out_of_quadrant_bmr_gravity(
    iso_grav_b13: np.ndarray,
    depth_base_b15: np.ndarray,
    grav_vg_b11: np.ndarray,
    grav_hg_b18: np.ndarray,
    valid: np.ndarray,
    quad: np.ndarray | None = None,
    *,
    cell_m: float = 100.0,
    subsample_step: int = 4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute Out-of-Quadrant (quad != q, zero fault labels) Spectral Basement
    Mass-Balance Gravity Residual r_BMR and its 3 structural derivative planes:
      1. bmr_resid_grad_z100: |grad(UC_100(r_BMR))|
      2. bmr_laplace_gzz_s2: Laplace vertical curvature zero-crossing sharpness
      3. bmr_vector_discordance: vector discrepancy between observed (B18, B11) and
         forward-modeled basin-fill gravity gradient (d(g_basin)/dcol, d(g_basin)/drow)
      plus r_BMR itself (for downstream GSST odd-step quadrature analysis).
    """
    b13 = np.asarray(iso_grav_b13, dtype=np.float32)
    zb = np.maximum(np.asarray(depth_base_b15, dtype=np.float32), 0.0)
    b11 = np.asarray(grav_vg_b11, dtype=np.float32)
    b18 = np.asarray(grav_hg_b18, dtype=np.float32)
    v = np.asarray(valid, dtype=bool)
    h, w = b13.shape
    if quad is None:
        quad = _quadrant_grid((h, w))

    # Athy compaction nonlinear depth proxy: density contrast decays below ~1.2 km
    zb_comp = (zb * zb / (zb + 1200.0)).astype(np.float32)
    zb_uc200, zb_uc800 = _fft_upward_continue(zb, v, (200.0, 800.0), cell_m=cell_m)
    (zcomp_uc200,) = _fft_upward_continue(zb_comp, v, (200.0,), cell_m=cell_m)
    (b13_reg4000,) = _fft_upward_continue(b13, v, (4000.0,), cell_m=cell_m)
    del zb_comp

    # Fit OLS mass-balance strictly on quad != q (zero label access)
    g_basin_pred = np.zeros((h, w), dtype=np.float32)
    stride_mask = np.zeros((h, w), dtype=bool)
    stride_mask[:: max(int(subsample_step), 1), :: max(int(subsample_step), 1)] = True

    for q in range(4):
        tr = v & (quad != q) & stride_mask
        if int(tr.sum()) < 32:
            tr = v & (quad != q)
        if int(tr.sum()) < 8:
            tr = v
        X_tr = np.column_stack(
            [
                np.ones(int(tr.sum()), dtype=np.float64),
                zb_uc200[tr].astype(np.float64),
                zb_uc800[tr].astype(np.float64),
                zcomp_uc200[tr].astype(np.float64),
                b13_reg4000[tr].astype(np.float64),
            ]
        )
        y_tr = b13[tr].astype(np.float64)
        # Ridge-stabilized normal equations for numerical Conditioning
        xtx = X_tr.T @ X_tr
        reg = np.diag([0.0, 1e-6, 1e-6, 1e-6, 1e-6]) * max(float(np.trace(xtx)), 1.0)
        beta = np.linalg.solve(xtx + reg, X_tr.T @ y_tr)

        te = quad == q
        g_basin_pred[te] = (
            beta[0]
            + beta[1] * zb_uc200[te]
            + beta[2] * zb_uc800[te]
            + beta[3] * zcomp_uc200[te]
            + beta[4] * b13_reg4000[te]
        ).astype(np.float32)

    del zb_uc200, zb_uc800, zcomp_uc200, b13_reg4000, stride_mask
    r_bmr = np.where(v, b13 - g_basin_pred, np.float32(0.0)).astype(np.float32)

    # Plane 1: Horizontal gradient magnitude of upward-continued r_BMR at z=100 m
    (r_uc100,) = _fft_upward_continue(r_bmr, v, (100.0,), cell_m=cell_m)
    rg_x, rg_y = _masked_gradients(r_uc100, v, sigma=1.2)
    bmr_grad_z100 = np.where(v, np.hypot(rg_x, rg_y), np.float32(0.0)).astype(np.float32)
    del r_uc100, rg_x, rg_y

    # Plane 2: Laplace vertical derivative curvature sharpness g_zz = -(d2/dx2 + d2/dy2) r_BMR
    r_sm = _masked_gaussian(r_bmr, v, sigma=2.0)
    r_xx = ndi.gaussian_filter(r_sm, sigma=1.5, order=(0, 2), mode="nearest")
    r_yy = ndi.gaussian_filter(r_sm, sigma=1.5, order=(2, 0), mode="nearest")
    gzz = -(r_xx + r_yy).astype(np.float32)
    del r_sm, r_xx, r_yy
    gzz_gx = ndi.gaussian_filter(gzz, sigma=1.0, order=(0, 1), mode="nearest")
    gzz_gy = ndi.gaussian_filter(gzz, sigma=1.0, order=(1, 0), mode="nearest")
    gzz_grad = np.hypot(gzz_gx, gzz_gy).astype(np.float32)
    del gzz_gx, gzz_gy
    gzz_scale = float(max(np.percentile(np.abs(gzz[v]), 65), 1e-6)) if v.any() else 1.0
    zero_cross = (1.0 / np.cosh(np.clip(gzz / (0.45 * gzz_scale), -8.0, 8.0))) ** 2
    bmr_gzz_s2 = np.where(v, gzz_grad * zero_cross, np.float32(0.0)).astype(np.float32)
    del gzz, gzz_grad, zero_cross

    # Plane 3: Vector gradient discordance vs verified observed (B18=+dg/dx_east, B11=+dg/drow_south)
    gp_sm = _masked_gaussian(g_basin_pred, v, sigma=1.5)
    del g_basin_pred
    gp_col = ndi.gaussian_filter(gp_sm, sigma=1.0, order=(0, 1), mode="nearest") / float(cell_m)
    gp_row = ndi.gaussian_filter(gp_sm, sigma=1.0, order=(1, 0), mode="nearest") / float(cell_m)
    del gp_sm
    # Match physical units empirically via robust median ratio on valid mask
    obs_mag = np.hypot(b18, b11)
    pred_mag = np.hypot(gp_col, gp_row)
    unit_scale = (
        float(np.median(obs_mag[v]) / max(np.median(pred_mag[v]), 1e-8))
        if v.any()
        else 1.0
    )
    dx_disc = b18 - unit_scale * gp_col
    dr_disc = b11 - unit_scale * gp_row
    disc_mag = np.hypot(dx_disc, dr_disc)
    cos_ang = (b18 * gp_col + b11 * gp_row) / (obs_mag * pred_mag + 1e-7)
    ang_weight = 0.5 * (1.0 - np.clip(cos_ang, -1.0, 1.0))
    bmr_vec_disc = np.where(v, disc_mag * (0.45 + 0.55 * ang_weight), np.float32(0.0)).astype(
        np.float32
    )
    return r_bmr, bmr_grad_z100, bmr_gzz_s2, bmr_vec_disc


def steerable_quadrature_step_asymmetry(
    field: np.ndarray,
    valid: np.ndarray,
    *,
    sigmas: tuple[float, ...] = (2.0, 4.5),
    dike_veto: float = 0.85,
    n_azimuths: int = 8,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """8-azimuth steerable quadrature odd-step vs even-dike asymmetry (GSST).

    For fault strike azimuth ``theta_k = k * pi / n_azimuths`` and cross-strike
    normal ``phi_k = theta_k + pi/2``:
      - ``O_k = sigma * (cos(phi_k) * f_x + sin(phi_k) * f_y)`` peaks on odd fault steps
        and vanishes on dike crests.
      - ``E_k = sigma^2 * (cos^2(phi_k)*f_xx + 2*cos*sin*f_xy + sin^2(phi_k)*f_yy)``
        peaks on symmetric volcanic dikes/channels and vanishes on fault-step inflections.
      - ``E_env_k = max(|E_k|, gaussian(|E_k|, sigma=0.9*sigma))`` suppresses both dike
        crests and dike-flank double-ridges.

    Returns ``(odd_step_dominance, theta_strike_rad, spin2_coherence)`` where
    ``theta_strike_rad in [0, pi)`` is measured in grid ``(col, row)`` coordinates.
    """
    f = np.asarray(field, dtype=np.float32)
    v = np.asarray(valid, dtype=bool)
    h, w = f.shape
    f_hp = f - _masked_gaussian(f, v, sigma=28.0)
    f_clean = np.where(v, f_hp, np.float32(0.0))
    del f_hp

    thetas = np.linspace(0.0, np.pi, n_azimuths, endpoint=False, dtype=np.float32)
    phis = thetas + np.float32(0.5 * np.pi)

    best_step = np.zeros((h, w), dtype=np.float32)
    c2_acc = np.zeros((h, w), dtype=np.float32)
    s2_acc = np.zeros((h, w), dtype=np.float32)
    w_acc = np.zeros((h, w), dtype=np.float32)

    for sig in sigmas:
        s = float(sig)
        # order=(row_order, col_order) -> fy is order=(1,0), fx is order=(0,1)
        fx = ndi.gaussian_filter(f_clean, sigma=s, order=(0, 1), mode="nearest") * s
        fy = ndi.gaussian_filter(f_clean, sigma=s, order=(1, 0), mode="nearest") * s
        fxx = ndi.gaussian_filter(f_clean, sigma=s, order=(0, 2), mode="nearest") * (s * s)
        fyy = ndi.gaussian_filter(f_clean, sigma=s, order=(2, 0), mode="nearest") * (s * s)
        fxy = ndi.gaussian_filter(f_clean, sigma=s, order=(1, 1), mode="nearest") * (s * s)

        for k in range(n_azimuths):
            th = float(thetas[k])
            ph = float(phis[k])
            cp = float(np.cos(ph))
            sp = float(np.sin(ph))
            odd = np.abs(cp * fx + sp * fy)
            even = np.abs(cp * cp * fxx + 2.0 * cp * sp * fxy + sp * sp * fyy)
            even_env = np.maximum(
                even,
                1.15 * ndi.gaussian_filter(even, sigma=max(0.85 * s, 0.8), mode="nearest"),
            )
            step_k = np.maximum(odd - float(dike_veto) * even_env, 0.0).astype(np.float32)
            best_step = np.maximum(best_step, step_k)
            w_k = step_k * step_k
            c2_acc += w_k * float(np.cos(2.0 * th))
            s2_acc += w_k * float(np.sin(2.0 * th))
            w_acc += w_k
        del fx, fy, fxx, fyy, fxy

    best_step[~v] = 0.0
    theta_strike = (0.5 * np.arctan2(s2_acc, c2_acc)) % np.float32(np.pi)
    theta_strike[~v] = 0.0
    spin2_coh = np.where(v, np.hypot(c2_acc, s2_acc) / (w_acc + 1e-6), np.float32(0.0)).astype(
        np.float32
    )
    return best_step, theta_strike.astype(np.float32), spin2_coh


def transtensional_conductance_neck(
    cond_b17: np.ndarray,
    dilate_b8: np.ndarray,
    shear_b7: np.ndarray,
    topo10_slope01: np.ndarray,
    theta_strike: np.ndarray,
    valid: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute (cnt_transtens_cond_neck, cnt_cond_horstsaddle_step).

    Narrow hydrothermal smectite/brine fault zones exhibit positive cross-strike
    negative curvature ``-d^2 log(1+C) / dn^2 > 0`` (conductive corridor/saddle neck)
    or strong cross-strike gradient ``|d log(1+C) / dn|`` (horst-basin fault contact),
    whereas broad flat saline playas have isotropic high conductance and near-zero
    cross-strike curvature.
    """
    v = np.asarray(valid, dtype=bool)
    logc = np.log1p(np.maximum(np.asarray(cond_b17, dtype=np.float32), 0.0))
    logc_sm = _masked_gaussian(logc, v, sigma=1.8)

    # Normal to geophysical strike theta_strike: phi = theta_strike + pi/2
    phi = np.asarray(theta_strike, dtype=np.float32) + np.float32(0.5 * np.pi)
    cp = np.cos(phi).astype(np.float32)
    sp = np.sin(phi).astype(np.float32)

    cx = ndi.gaussian_filter(logc_sm, sigma=2.2, order=(0, 1), mode="nearest")
    cy = ndi.gaussian_filter(logc_sm, sigma=2.2, order=(1, 0), mode="nearest")
    cxx = ndi.gaussian_filter(logc_sm, sigma=2.6, order=(0, 2), mode="nearest")
    cyy = ndi.gaussian_filter(logc_sm, sigma=2.6, order=(2, 0), mode="nearest")
    cxy = ndi.gaussian_filter(logc_sm, sigma=2.6, order=(1, 1), mode="nearest")

    # Cross-strike vs along-strike second derivative -> narrow conductive ridge/saddle neck
    d2_across = cp * cp * cxx + 2.0 * cp * sp * cxy + sp * sp * cyy
    cs = -sp
    ss = cp
    d2_along = cs * cs * cxx + 2.0 * cs * ss * cxy + ss * ss * cyy
    neck_raw = np.maximum(-d2_across + 0.35 * np.abs(d2_along), 0.0).astype(np.float32)

    # Cross-strike horst-margin conductivity step
    horst_step_raw = np.hypot(cx, cy) * (0.45 + 0.55 * np.abs(cp * cx + sp * cy) / (np.hypot(cx, cy) + 1e-6))

    # Transtensional opening gate (positive dilatation Band 8 + dextral shear Band 7)
    z_dil = _robust_pos_z(np.asarray(dilate_b8, dtype=np.float32), v)
    z_shr = _robust_pos_z(np.asarray(shear_b7, dtype=np.float32), v)
    tt_gate = 0.35 + 0.65 / (1.0 + np.exp(-np.clip(0.85 * z_dil + 0.45 * z_shr, -8.0, 8.0)))

    # Suppress flat regional high-conductance playa interiors where slope ~ 0 and broad C is extreme
    c_reg = _masked_gaussian(logc, v, sigma=14.0)
    c_p85 = float(np.percentile(c_reg[v], 85)) if v.any() else 1.0
    flat_playa = np.clip((c_reg - c_p85) / max(c_p85 * 0.35, 1e-4), 0.0, 1.0) * np.exp(
        -np.asarray(topo10_slope01, dtype=np.float32) / 0.06
    )
    playa_keep = (1.0 - 0.55 * flat_playa).astype(np.float32)

    cnt_neck = np.where(v, neck_raw * tt_gate * playa_keep, np.float32(0.0)).astype(np.float32)
    cnt_step = np.where(v, horst_step_raw * tt_gate * playa_keep, np.float32(0.0)).astype(
        np.float32
    )
    return cnt_neck, cnt_step


def dilatation_gated_shallow_pullback(
    subsurface_step: np.ndarray,
    depth_base_b15: np.ndarray,
    dilate_b8: np.ndarray,
    shear_b7: np.ndarray,
    valid: np.ndarray,
    *,
    max_shift_px: float = 3.0,
    dip_deg: float = 62.0,
    cell_m: float = 100.0,
) -> np.ndarray:
    """Shallow normal-regime-gated footwall pullback capped strictly at <= 3.0 px.

    Fixes GEMSDOE92 (0.0255) and H86K-STDP (0.1380) over-shifting:
      - Strike-slip regimes (shear >= dilatation) and deep basins (Z_b >> 900 m)
        receive near-zero shift (retaining pixel-accurate steep contacts).
      - Shallow normal-fault margins (dilatation > shear, Z_b ~ 100-700 m) pull
        hanging-wall steps footwall-ward by at most 3.0 px (300 m).
    """
    plane = np.asarray(subsurface_step, dtype=np.float32)
    zb = np.maximum(np.asarray(depth_base_b15, dtype=np.float32), 0.0)
    v = np.asarray(valid, dtype=bool)
    h, w = plane.shape

    zb_sm = _masked_gaussian(zb, v, sigma=3.0)
    gz_r = ndi.gaussian_filter(zb_sm, sigma=1.5, order=(1, 0), mode="nearest")
    gz_c = ndi.gaussian_filter(zb_sm, sigma=1.5, order=(0, 1), mode="nearest")
    gnorm = np.hypot(gz_r, gz_c) + np.float32(5.0)
    ur = (gz_r / gnorm).astype(np.float32)
    uc = (gz_c / gnorm).astype(np.float32)

    z_dil = _robust_pos_z(np.asarray(dilate_b8, dtype=np.float32), v)
    z_shr = _robust_pos_z(np.asarray(shear_b7, dtype=np.float32), v)
    normal_gate = (1.0 / (1.0 + np.exp(-np.clip(1.1 * (z_dil - 0.65 * z_shr), -8.0, 8.0)))) * np.exp(
        -zb_sm / 900.0
    )

    cot_dip = float(1.0 / np.tan(np.deg2rad(dip_deg)))
    ds = np.clip((zb_sm / float(cell_m)) * cot_dip, 0.0, float(max_shift_px)) * normal_gate
    ds = ds.astype(np.float32)

    rr, cc = np.indices((h, w), dtype=np.float32)
    pulled = ndi.map_coordinates(
        plane,
        [np.clip(rr + ds * ur, 0.0, h - 1.0), np.clip(cc + ds * uc, 0.0, w - 1.0)],
        order=1,
        mode="nearest",
    ).astype(np.float32)
    out = np.where(v, 0.55 * pulled + 0.45 * plane, np.float32(0.0)).astype(np.float32)
    return out


def build_bmgs_static_stack(
    feature_tif: Path,
    ext_dir: Path,
    *,
    out_bmgs_path: Path | None = None,
    out_ablation_path: Path | None = None,
    out_strike_path: Path | None = None,
    footprint: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """Stream all 24 cover-blind H86M-BMGS planes + strike field + corroboration prior
    + 8 ablation planes into float16 disk-backed memmaps within < 900 MiB RSS.

    Returns ``(X_bmgs, theta_strike, L_bmgs, X_abl, valid, qc_dict)``.
    """
    qc = verify_bmgs_input_contract(ext_dir)
    accessed_cols: dict[str, tuple[str, ...]] = {}

    with rasterio.open(feature_tif) as ds:
        h, w = ds.height, ds.width
        b2_probe = ds.read(2).astype(np.float32)
        feat_valid = np.isfinite(b2_probe) & (b2_probe > NODATA * 0.5)
        del b2_probe

    valid = feat_valid if footprint is None else (feat_valid & np.asarray(footprint, dtype=bool))
    quad = _quadrant_grid((h, w))
    n_bmgs = len(BMGS_STATIC_NAMES)
    n_abl = len(ABLATION_RAW_NAMES)

    if out_bmgs_path is not None:
        out_bmgs_path.parent.mkdir(parents=True, exist_ok=True)
        X_bmgs = open_memmap(out_bmgs_path, mode="w+", dtype=np.float16, shape=(n_bmgs, h, w))
    else:
        X_bmgs = np.zeros((n_bmgs, h, w), dtype=np.float16)

    if out_ablation_path is not None:
        out_ablation_path.parent.mkdir(parents=True, exist_ok=True)
        X_abl = open_memmap(out_ablation_path, mode="w+", dtype=np.float16, shape=(n_abl, h, w))
    else:
        X_abl = np.zeros((n_abl, h, w), dtype=np.float16)

    def _put_bmgs(name: str, arr: np.ndarray) -> None:
        idx = BMGS_STATIC_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_bmgs[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    def _put_abl(name: str, arr: np.ndarray) -> None:
        idx = ABLATION_RAW_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_abl[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    seam_keep = _geodawn_seam_keep_mask(ext_dir, valid)
    topo_slope_10m = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 1, valid) / 255.0
    _put_abl("raw_topo10_slope_p90", topo_slope_10m)

    corrob_acc = np.zeros((h, w), dtype=np.float32)

    with rasterio.open(feature_tif) as ds:
        # --- Block 1: Out-of-Quadrant Spectral BMR Gravity ---
        zb_m = _read_native(ds, 15, valid)
        z_gx, z_gy = _masked_gradients(zb_m, valid, sigma=3.0)
        _put_abl("raw_depth_gradmag_s3", np.hypot(z_gx, z_gy))
        del z_gx, z_gy

        b13 = _read_native(ds, 13, valid)
        b11 = _read_native(ds, 11, valid)
        b18 = _read_native(ds, 18, valid)
        b5 = _read_native(ds, 5, valid)
        _put_abl("raw_grav_slope_b5", b5)
        del b5

        r_bmr, bmr_grad_z100, bmr_gzz_s2, bmr_vec_disc = out_of_quadrant_bmr_gravity(
            b13, zb_m, b11, b18, valid, quad
        )
        del b13, b11, b18
        _put_bmgs("bmr_resid_grad_z100", bmr_grad_z100)
        _put_bmgs("bmr_laplace_gzz_s2", bmr_gzz_s2)
        _put_bmgs("bmr_vector_discordance", bmr_vec_disc)
        corrob_acc += 0.14 * _rank01(bmr_grad_z100, valid) + 0.08 * _rank01(bmr_gzz_s2, valid)
        del bmr_gzz_s2, bmr_vec_disc
        gc.collect()

        # --- Block 2: 8-Azimuth GSST Quadrature Odd-Step vs Even-Dike ---
        b2 = _read_native(ds, 2, valid)
        b3 = _read_native(ds, 3, valid)
        _put_abl("raw_tmi_hg_b3", b3)
        b9 = _read_native(ds, 9, valid)

        gsst_rtp_raw, th_rtp, coh_rtp = steerable_quadrature_step_asymmetry(b2, valid)
        gsst_rtp = (gsst_rtp_raw * seam_keep).astype(np.float32)
        del gsst_rtp_raw
        gsst_bmr, th_bmr, coh_bmr = steerable_quadrature_step_asymmetry(r_bmr, valid)

        _put_bmgs("gsst_rtp_odd_step_seamfree", gsst_rtp)
        _put_bmgs("gsst_bmr_odd_step", gsst_bmr)

        # Combined spin-2 dominant geophysical strike theta_strike in [0, pi)
        w_rtp = _rank01(gsst_rtp, valid) * coh_rtp
        w_bmr = _rank01(gsst_bmr, valid) * coh_bmr
        c2_tot = w_rtp * np.cos(2.0 * th_rtp) + 1.25 * w_bmr * np.cos(2.0 * th_bmr)
        s2_tot = w_rtp * np.sin(2.0 * th_rtp) + 1.25 * w_bmr * np.sin(2.0 * th_bmr)
        theta_strike = ((0.5 * np.arctan2(s2_tot, c2_tot)) % np.float32(np.pi)).astype(np.float32)
        theta_strike[~valid] = 0.0
        del c2_tot, s2_tot, w_rtp, w_bmr

        # Cross-field spin-2 strike alignment between RTP odd-step and BMR gravity odd-step
        cross_spin2 = (
            np.sqrt(_rank01(gsst_rtp, valid) * _rank01(gsst_bmr, valid) + 1e-7)
            * 0.5
            * (1.0 + np.cos(2.0 * (th_rtp - th_bmr)))
            * seam_keep
        ).astype(np.float32)
        _put_bmgs("gsst_cross_field_spin2", cross_spin2)
        corrob_acc += (
            0.12 * _rank01(gsst_bmr, valid)
            + 0.10 * _rank01(gsst_rtp, valid)
            + 0.08 * _rank01(cross_spin2, valid)
        )
        del th_rtp, th_bmr, coh_rtp, coh_bmr, cross_spin2

        # Garland (1951) Poisson ratio lateral jump across local fault normal
        rtp_gx, rtp_gy = _masked_gradients(b2, valid, sigma=1.8)
        bmr_gx, bmr_gy = _masked_gradients(r_bmr, valid, sigma=1.8)
        del r_bmr
        log_poisson = np.log((np.hypot(rtp_gx, rtp_gy) + 0.05) / (np.hypot(bmr_gx, bmr_gy) + 0.05))
        del rtp_gx, rtp_gy, bmr_gx, bmr_gy
        lp_x, lp_y = _masked_gradients(log_poisson, valid, sigma=1.8)
        del log_poisson
        phi_n = theta_strike + np.float32(0.5 * np.pi)
        garland_step = (np.abs(np.cos(phi_n) * lp_x + np.sin(phi_n) * lp_y) * seam_keep).astype(
            np.float32
        )
        del lp_x, lp_y
        _put_bmgs("garland_poisson_step", garland_step)
        del garland_step

        # TMI upward-continued depth persistence & hydrothermal magnetite trough
        tmi_up150 = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 4, valid) / 255.0
        asig_surf = np.hypot(b3, b9)
        del b3, b9
        up_gx, up_gy = _masked_gradients(tmi_up150, valid, sigma=2.0)
        del tmi_up150
        depth_persist = (
            np.hypot(up_gx, up_gy)
            / (_rank01(asig_surf, valid) + 0.25)
            * seam_keep
        ).astype(np.float32)
        del up_gx, up_gy, asig_surf
        _put_bmgs("tmi_up150_depth_persistence", depth_persist)
        del depth_persist

        # Cross-strike positive second derivative (+d^2 RTP / dn^2) magnetite destruction trough
        b2_sm = _masked_gaussian(b2, valid, sigma=2.2)
        del b2
        b2_xx = ndi.gaussian_filter(b2_sm, sigma=2.0, order=(0, 2), mode="nearest")
        b2_yy = ndi.gaussian_filter(b2_sm, sigma=2.0, order=(2, 0), mode="nearest")
        b2_xy = ndi.gaussian_filter(b2_sm, sigma=2.0, order=(1, 1), mode="nearest")
        del b2_sm
        cp_n = np.cos(phi_n)
        sp_n = np.sin(phi_n)
        d2rtp_dn2 = cp_n * cp_n * b2_xx + 2.0 * cp_n * sp_n * b2_xy + sp_n * sp_n * b2_yy
        del b2_xx, b2_yy, b2_xy, cp_n, sp_n, phi_n
        b6_tc = _read_native(ds, 6, valid)  # verified GeoDAWN Total Count > 0
        volc_gate = 0.35 + 0.65 * _rank01(b6_tc, valid)
        del b6_tc
        mag_trough = (np.maximum(d2rtp_dn2, 0.0) * volc_gate * seam_keep).astype(np.float32)
        del d2rtp_dn2, volc_gate
        _put_bmgs("hydro_magnetite_trough", mag_trough)
        del mag_trough, gsst_rtp
        gc.collect()

        # --- Block 3: CNT Transtensional Conductance Neck + Shallow Pullback + Tectonics ---
        b17 = _read_native(ds, 17, valid)
        _put_abl("raw_cond_iso_blur", _masked_gaussian(np.log1p(np.maximum(b17, 0.0)), valid, 6.0))
        b7 = _read_native(ds, 7, valid)
        b8 = _read_native(ds, 8, valid)
        b4 = _read_native(ds, 4, valid)
        b4_hp = b4 - _masked_gaussian(b4, valid, sigma=30.0)
        _put_abl("raw_strain_2ndinv_hp", b4_hp)

        cnt_neck, cnt_step = transtensional_conductance_neck(
            b17, b8, b7, topo_slope_10m, theta_strike, valid
        )
        del b17
        _put_bmgs("cnt_transtens_cond_neck", cnt_neck)
        _put_bmgs("cnt_cond_horstsaddle_step", cnt_step)
        corrob_acc += 0.08 * _rank01(cnt_neck, valid) + 0.06 * _rank01(cnt_step, valid)
        del cnt_neck

        shallow_pb = dilatation_gated_shallow_pullback(
            0.60 * _rank01(gsst_bmr, valid) + 0.40 * _rank01(cnt_step, valid),
            zb_m,
            b8,
            b7,
            valid,
            max_shift_px=3.0,
            dip_deg=62.0,
        )
        del gsst_bmr, cnt_step
        _put_bmgs("dilatation_gated_shallow_pullback", shallow_pb)

        # Kostrov-Byerlee slip + dilation tendency in NW Great Basin stress field
        opt_norm = 0.5 * (1.0 + np.cos(2.0 * (theta_strike - _STRIKE_N22E_GRID)))
        opt_dext = 0.5 * (1.0 + np.cos(2.0 * (theta_strike - _STRIKE_N35W_GRID)))
        kostrov = (
            (0.65 * opt_norm + 0.35 * opt_dext)
            * (0.40 + 0.60 * _rank01(b4, valid))
        ).astype(np.float32)
        del opt_norm, opt_dext, b4
        _put_bmgs("kostrov_byerlee_dilation_tendency", kostrov)
        del kostrov

        b10 = _read_native(ds, 10, valid)
        b16 = _read_native(ds, 16, valid)
        eq_comb = 0.55 * _robust_pos_z(b10, valid) + 0.45 * _robust_pos_z(b16, valid)
        del b10, b16
        eq_hp = eq_comb - _masked_gaussian(eq_comb, valid, sigma=24.0)
        del eq_comb
        strain_z = (
            0.45 * _robust_pos_z(b4_hp, valid)
            + 0.35 * _robust_pos_z(b8, valid)
            + 0.20 * _robust_pos_z(b7, valid)
        )
        del b4_hp, b7, b8
        creep_def = np.maximum(strain_z - 0.65 * np.maximum(eq_hp, 0.0), 0.0).astype(np.float32)
        _put_bmgs("aseismic_creep_deficit", creep_def)
        _put_bmgs("microseismic_brittle_swarm_hp", eq_hp.astype(np.float32))
        del creep_def, eq_hp, strain_z

        # Ablation-only raw B19 slope; smooth B12 used ONLY for hydraulic-head direction & Lahontan veto
        b19_abl = _read_native(ds, 19, valid)
        _put_abl("raw_elev_slope_b19", b19_abl)
        del b19_abl

        b12_head = _read_native(ds, 12, valid)
        lahontan_band = np.maximum(
            np.exp(-(((b12_head - 1330.0) / 28.0) ** 2)),
            np.exp(-(((b12_head - 1205.0) / 24.0) ** 2)),
        ).astype(np.float32)

    # --- Block 4: Up-Hydraulic-Head GDR #1391 Geothermal & Seam-Free Radiometrics ---
    uphead_diseq, probe_wall, sinter_corr, iso_geoth = _gdr_geothermal_planes(
        ext_dir, valid, b12_head, accessed_cols
    )
    del b12_head
    _put_abl("raw_geotherm_iso_blur", iso_geoth)
    del iso_geoth

    struct_gate = (0.32 + 0.68 * (0.55 * _rank01(bmr_grad_z100, valid) + 0.45 * _rank01(shallow_pb, valid))).astype(
        np.float32
    )
    del bmr_grad_z100, shallow_pb
    uphead_g = (uphead_diseq * struct_gate).astype(np.float32)
    probe_g = (probe_wall * struct_gate).astype(np.float32)
    sinter_g = (sinter_corr * struct_gate).astype(np.float32)
    del uphead_diseq, probe_wall, sinter_corr, struct_gate
    _put_bmgs("uphead_geotherm_diseq", uphead_g)
    _put_bmgs("probe2m_uphead_thermal_wall", probe_g)
    _put_bmgs("paleo_sinter_vent_corridor", sinter_g)
    corrob_acc += 0.08 * _rank01(uphead_g, valid) + 0.07 * _rank01(probe_g, valid) + 0.05 * _rank01(sinter_g, valid)
    del uphead_g, probe_g, sinter_g

    rad_K = _read_ext(ext_dir, "geodawn_rad_u8.tif", 1, valid)
    rad_Th = _read_ext(ext_dir, "geodawn_rad_u8.tif", 2, valid)
    ext_ThK = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 1, valid)
    kth_ratio = (rad_K + 1.0) / (rad_Th + 8.0) - 0.35 * (ext_ThK / 255.0)
    del rad_K, ext_ThK
    kth_gx, kth_gy = _masked_gradients(kth_ratio, valid, sigma=1.8)
    del kth_ratio
    rad_kth = (np.hypot(kth_gx, kth_gy) * seam_keep * (1.0 - 0.55 * lahontan_band)).astype(np.float32)
    del kth_gx, kth_gy
    _put_bmgs("rad_kth_potassic_seamfree", rad_kth)

    rad_U = _read_ext(ext_dir, "geodawn_rad_u8.tif", 3, valid)
    ext_UTh = _read_ext(ext_dir, "geodawn_extensions_u8.tif", 3, valid)
    uth_field = 0.6 * (ext_UTh / 255.0) + 0.4 * ((rad_U + 1.0) / (rad_Th + 8.0))
    del rad_U, rad_Th, ext_UTh
    uth_gx, uth_gy = _masked_gradients(uth_field, valid, sigma=1.8)
    del uth_field
    rad_uth = (np.hypot(uth_gx, uth_gy) * seam_keep * (1.0 - 0.40 * lahontan_band)).astype(np.float32)
    del uth_gx, uth_gy, seam_keep
    _put_bmgs("rad_uth_redox_seamfree", rad_uth)
    corrob_acc += 0.05 * _rank01(rad_kth, valid)
    del rad_kth, rad_uth
    gc.collect()

    # --- Block 5: 10m-Debiased 3DEP 1m LiDAR Scarps & Piedmont/Fluvial Breaks (Zero B12/B19) ---
    topo_curv = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 6, valid) / 255.0
    topo_asp = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 7, valid) / 255.0
    topo_hs = _read_ext(ext_dir, "topo_10m_derived_100m_u8.tif", 8, valid) / 255.0
    piedmont_gate = 0.45 + 0.55 * (1.0 - np.exp(-zb_m / 45.0)) * np.exp(-zb_m / 2200.0)
    del zb_m
    lahontan_mimic = np.clip(lahontan_band * topo_asp, 0.0, 1.0)
    del lahontan_band
    topo10_pied = (
        (0.42 * topo_hs + 0.36 * topo_curv + 0.22 * topo_slope_10m)
        * (0.40 + 0.60 * topo_asp)
        * piedmont_gate
        * (1.0 - 0.55 * lahontan_mimic)
    ).astype(np.float32)
    del topo_curv, topo_asp, topo_hs, topo_slope_10m, piedmont_gate
    _put_bmgs("topo10_piedmont_scarp_break", topo10_pied)

    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as lds:
        li_has = valid & (lds.read(12) > 0)
    li_miss = valid & ~li_has

    def _put_lidar_debiased(idx: int, arr_obs: np.ndarray, fb_10m: np.ndarray) -> np.ndarray:
        z_obs = _robust_pos_z(arr_obs, li_has)
        z_fb = _robust_pos_z(fb_10m, li_miss) if np.any(li_miss) else np.zeros_like(z_obs)
        merged_z = np.zeros(valid.shape, dtype=np.float32)
        merged_z[li_has] = z_obs[li_has]
        merged_z[li_miss] = z_fb[li_miss]
        X_bmgs[idx] = np.clip(merged_z, -32.0, 32.0).astype(np.float16)

        r_obs = _rank01(arr_obs, li_has)
        r_fb = _rank01(fb_10m, li_miss) if np.any(li_miss) else np.zeros_like(r_obs)
        merged_r = np.zeros(valid.shape, dtype=np.float32)
        merged_r[li_has] = r_obs[li_has]
        merged_r[li_miss] = r_fb[li_miss]
        return merged_r

    li_step = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 3, valid) / 255.0
    li_cross = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 8, valid) / 255.0
    li_coh = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 10, valid) / 255.0
    li_scarp = (li_step * (0.5 + 0.5 * li_cross) * (0.35 + 0.65 * li_coh) * (1.0 - 0.60 * lahontan_mimic)).astype(
        np.float32
    )
    del li_step, li_cross
    li_scarp_r = _put_lidar_debiased(
        BMGS_STATIC_NAMES.index("lidar1m_scarp_debiased"), li_scarp, topo10_pied
    )
    del li_scarp

    li_dn = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 6, valid) / 255.0
    li_up = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 7, valid) / 255.0
    li_ln = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 4, valid) / 255.0
    li_lp = _read_ext(ext_dir, "lidar_scarp_features_u8.tif", 5, valid) / 255.0
    # Unilateral scarp step polarity (one-sided footwall bench vs symmetric gully)
    li_unilat = (
        np.abs(li_up - li_dn)
        + 0.65 * np.maximum(li_up, li_dn) * np.sqrt(li_ln * li_lp + 1e-6)
    ) * (0.4 + 0.6 * li_coh)
    del li_dn, li_up, li_ln, li_lp, li_coh
    li_uni_r = _put_lidar_debiased(
        BMGS_STATIC_NAMES.index("lidar1m_unilateral_polarity"), li_unilat.astype(np.float32), topo10_pied
    )
    del li_unilat, li_has, li_miss

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
    _put_bmgs("chi10_fluvial_knick_step", chi_knick)

    corrob_acc += (
        0.09 * li_scarp_r
        + 0.04 * li_uni_r
        + 0.04 * _rank01(topo10_pied, valid)
        + 0.04 * _rank01(chi_knick, valid)
        - 0.12 * lahontan_mimic
    )
    del li_scarp_r, li_uni_r, topo10_pied, chi_knick, lahontan_mimic
    L_bmgs = _rank01(corrob_acc, valid)
    del corrob_acc
    gc.collect()

    if out_strike_path is not None:
        out_strike_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(out_strike_path, theta_strike.astype(np.float16))

    if out_bmgs_path is not None:
        X_bmgs.flush()
        del X_bmgs
        X_bmgs = np.load(out_bmgs_path, mmap_mode="r")
    if out_ablation_path is not None:
        X_abl.flush()
        del X_abl
        X_abl = np.load(out_ablation_path, mmap_mode="r")

    qc["accessed_csv_columns"] = {k: list(v) for k, v in accessed_cols.items()}
    return X_bmgs, theta_strike, L_bmgs, X_abl, valid, qc
