"""Core geological, geomorphic, hydrothermal, and geomechanical operators for Lane H86S-DWAD."""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata


def _rank01_mask(arr: np.ndarray, valid: np.ndarray) -> np.ndarray:
    m = np.asarray(valid, dtype=bool)
    out = np.zeros(m.shape, dtype=np.float32)
    n = int(m.sum())
    if n <= 1:
        return out
    vals = np.nan_to_num(np.asarray(arr, dtype=np.float32)[m], nan=0.0, posinf=0.0, neginf=0.0)
    r = (rankdata(vals, method="average") - 0.5) / float(n)
    out[m] = r.astype(np.float32)
    return out


def compute_survey_observability(
    zb_m: np.ndarray,
    det_slope_b19: np.ndarray,
    topo_relief_u8: np.ndarray,
    lidar_valid_u8: np.ndarray,
    valid: np.ndarray,
    *,
    floor: float = 0.15,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute surface fault mapping observability O(x) in [floor, 1.0].

    Under Selected-At-Random-is-Violated (SAR) Positive-Unlabeled fault learning,
    unlabeled cells are trustworthy structural negatives primarily where bedrock
    is shallow (small Band 15 depth_to_base_surf), relief/slope is non-zero
    (Band 19 det_elev_slope + 10 m relief), and 1 m 3DEP LiDAR swaths exist.
    Thick low-relief alluvial playas receive O(x) near ``floor`` rather than 1.0.
    """
    m = np.asarray(valid, dtype=bool)
    zb_pos = np.clip(np.nan_to_num(np.asarray(zb_m, dtype=np.float32), nan=0.0), 0.0, 5000.0)
    obs_bedrock = np.where(m, np.exp(-zb_pos / np.float32(250.0)), np.float32(0.0)).astype(np.float32)

    sl_r = _rank01_mask(np.maximum(det_slope_b19, 0.0), m)
    rel_r = _rank01_mask(np.maximum(topo_relief_u8, 0.0), m)
    obs_relief = np.where(m, 0.55 * sl_r + 0.45 * rel_r, np.float32(0.0)).astype(np.float32)

    lid_bin = (np.nan_to_num(np.asarray(lidar_valid_u8, dtype=np.float32), nan=0.0) > 0.5).astype(np.float32)
    obs_lidar = np.where(
        m,
        np.clip(ndi.gaussian_filter(lid_bin, sigma=3.0, mode="nearest"), 0.0, 1.0),
        np.float32(0.0),
    ).astype(np.float32)

    raw_obs = 0.46 * obs_bedrock + 0.36 * obs_relief + 0.18 * obs_lidar
    fl = np.float32(floor)
    obs = np.where(m, fl + (np.float32(1.0) - fl) * np.clip(raw_obs, 0.0, 1.0), np.float32(0.0))
    return obs.astype(np.float32), obs_bedrock, obs_relief, obs_lidar


def downslope_canyon_knickzone_backprojection(
    ksn_max: np.ndarray,
    log10_area_x1000: np.ndarray,
    zmean_m: np.ndarray,
    zb_m: np.ndarray,
    valid: np.ndarray,
    *,
    steps_px: tuple[float, float] = (8.0, 15.0),
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Back-project footwall canyon channel-steepness excess downstream onto piedmont fan apices.

    In detachment-limited stream-power geomorphology (Whipple & Tucker, 1999;
    Perron & Royden, 2013), base-level fall across a range-front normal fault sends
    transient knickpoints upstream into footwall canyons, leaving the modern ksn peak
    800-1,500 m upslope of the active buried piedmont fault trace. Pulling ksn excess
    from upslope coordinates ``(r + s * ur_up, c + s * uc_up)`` maps that signal
    downstream to pixel ``(r, c)``, where positive downslope basement thickening
    ``u_down . grad(Band 15) > 0`` separates active faulted canyon mouths from
    unfaulted erosional pediments.
    """
    m = np.asarray(valid, dtype=bool)
    H, W = m.shape
    ksn = np.clip(np.nan_to_num(np.asarray(ksn_max, dtype=np.float32), nan=0.0), 0.0, 4000.0)
    larea = np.clip(
        np.nan_to_num(np.asarray(log10_area_x1000, dtype=np.float32), nan=0.0) / 1000.0,
        2.0,
        10.5,
    )

    # Drainage-area-deconfounded steepness excess across 12 log10(A) bins
    ksn_excess = np.zeros((H, W), dtype=np.float32)
    edges = np.linspace(3.0, 9.0, 13, dtype=np.float32)
    bin_idx = np.clip(np.digitize(larea, edges) - 1, 0, 11)
    for b in range(12):
        bm = m & (bin_idx == b) & (ksn > 0.0)
        if int(bm.sum()) >= 32:
            med = float(np.median(ksn[bm]))
            mad = float(np.median(np.abs(ksn[bm] - med))) + 1.0
            ksn_excess[bm] = np.clip((ksn[bm] - med) / (1.4826 * mad), 0.0, 12.0)
    ksn_sm = ndi.gaussian_filter(ksn_excess, sigma=1.6, mode="nearest").astype(np.float32)
    ksn_sm[~m] = 0.0

    # Unit upslope vector +grad(zmean_m) / ||grad(zmean_m)||
    z_clean = np.nan_to_num(np.asarray(zmean_m, dtype=np.float32), nan=0.0)
    gr_up = ndi.gaussian_filter(z_clean, sigma=3.5, order=(1, 0), mode="nearest")
    gc_up = ndi.gaussian_filter(z_clean, sigma=3.5, order=(0, 1), mode="nearest")
    gn = np.hypot(gr_up, gc_up)
    grad_gate = np.clip((gn - 1.2) / 6.0, 0.0, 1.0).astype(np.float32)
    ur_up = (gr_up / (gn + np.float32(1.5))).astype(np.float32)
    uc_up = (gc_up / (gn + np.float32(1.5))).astype(np.float32)

    rr, cc = np.meshgrid(
        np.arange(H, dtype=np.float32), np.arange(W, dtype=np.float32), indexing="ij"
    )
    s1, s2 = float(steps_px[0]), float(steps_px[1])
    coords1 = np.array(
        [np.clip(rr + s1 * ur_up, 0.0, H - 1.0), np.clip(cc + s1 * uc_up, 0.0, W - 1.0)],
        dtype=np.float32,
    )
    coords2 = np.array(
        [np.clip(rr + s2 * ur_up, 0.0, H - 1.0), np.clip(cc + s2 * uc_up, 0.0, W - 1.0)],
        dtype=np.float32,
    )
    adv_800 = (
        ndi.map_coordinates(ksn_sm, coords1, order=1, mode="nearest") * grad_gate
    ).astype(np.float32)
    adv_1500 = (
        ndi.map_coordinates(ksn_sm, coords2, order=1, mode="nearest") * grad_gate
    ).astype(np.float32)
    adv_800[~m] = 0.0
    adv_1500[~m] = 0.0

    # Downslope basement-deepening gate: u_down = (-ur_up, -uc_up) dotted with grad(Band 15)
    zb_clean = np.clip(np.nan_to_num(np.asarray(zb_m, dtype=np.float32), nan=0.0), 0.0, 5000.0)
    zb_gr = ndi.gaussian_filter(zb_clean, sigma=2.5, order=(1, 0), mode="nearest")
    zb_gc = ndi.gaussian_filter(zb_clean, sigma=2.5, order=(0, 1), mode="nearest")
    downslope_zb_rate = np.maximum((-ur_up) * zb_gr + (-uc_up) * zb_gc, 0.0).astype(np.float32)
    # Alluvial-apex window: peaks where basement depth transitions across 20..700 m
    apex_win = np.exp(-(((np.log1p(zb_clean) - np.log1p(140.0)) / 1.45) ** 2)).astype(np.float32)
    adv_blend = 0.55 * adv_800 + 0.45 * adv_1500
    apex_gated = np.where(
        m,
        adv_blend * np.log1p(downslope_zb_rate / 4.0) * (0.35 + 0.65 * apex_win),
        np.float32(0.0),
    ).astype(np.float32)

    # Along-contour (range-front strike: (-uc_up, +ur_up)) cross-canyon coherence (+/- 6, 12 px)
    tr = -uc_up
    tc = ur_up
    coh_acc = apex_gated.copy()
    for d in (-12.0, -6.0, 6.0, 12.0):
        c_shift = np.array(
            [np.clip(rr + d * tr, 0.0, H - 1.0), np.clip(cc + d * tc, 0.0, W - 1.0)],
            dtype=np.float32,
        )
        coh_acc += 0.5 * ndi.map_coordinates(apex_gated, c_shift, order=1, mode="nearest")
    strike_coh = np.where(m, coh_acc / 3.0, np.float32(0.0)).astype(np.float32)
    return ksn_sm, adv_800, adv_1500, apex_gated, strike_coh


def sub_claycap_geothermal_feeder_disjunction(
    cond_surf_b17: np.ndarray,
    rtp_b2: np.ndarray,
    grav_slope_b5: np.ndarray,
    uphead_diseq: np.ndarray,
    probe_wall: np.ndarray,
    sinter_corridor: np.ndarray,
    valid: np.ndarray,
    seam_keep: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Isolate brittle hydrothermal feeder margins beneath smectite clay alteration caps.

    1. ``geo_claycap_lateral_margin``: horizontal gradient of log-conductance (Band 17)
       weighted by intermediate-conductance flank factor ``4 u (1 - u)`` to reject
       uniform saline playa brine interiors.
    2. ``geo_subcap_basement_feeder_conj``: triple conjunction of lateral clay-cap
       boundary, hydrothermal magnetite-oxidation RTP trough (``max(0, +laplacian(B2))``),
       and horizontal Bouguer gravity gradient ``Band 5``.
    3. ``geo_uphead_sinter_probe_wall``: up-hydraulic-head GDR #1391 thermal/sinter wall.
    4. ``geo_blind_vent_alignment_ridge``: 8-azimuth anisotropic ridge connecting
       collinear thermal anomalies and feeder margins across covered basins.
    """
    m = np.asarray(valid, dtype=bool)
    sk = np.clip(np.nan_to_num(np.asarray(seam_keep, dtype=np.float32), nan=1.0), 0.0, 1.0)
    cond_pos = np.maximum(np.nan_to_num(np.asarray(cond_surf_b17, dtype=np.float32), nan=0.0), 0.0)
    log_c = np.log1p(cond_pos).astype(np.float32)
    cr = ndi.gaussian_filter(log_c, sigma=2.2, order=(1, 0), mode="nearest")
    cc = ndi.gaussian_filter(log_c, sigma=2.2, order=(0, 1), mode="nearest")
    c_grad = np.hypot(cr, cc).astype(np.float32)
    u_c = _rank01_mask(log_c, m)
    flank_wt = (0.30 + 0.70 * (4.0 * u_c * (1.0 - u_c))).astype(np.float32)
    clay_margin = np.where(m, _rank01_mask(c_grad, m) * flank_wt, np.float32(0.0)).astype(np.float32)

    # Hydrothermal magnetite oxidation destroys magnetic susceptibility along permeable
    # fault conduits, creating narrow positive-Laplacian troughs inside volcanic units.
    b2 = np.nan_to_num(np.asarray(rtp_b2, dtype=np.float32), nan=0.0)
    lap_b2 = (
        ndi.gaussian_filter(b2, sigma=3.2, order=(2, 0), mode="nearest")
        + ndi.gaussian_filter(b2, sigma=3.2, order=(0, 2), mode="nearest")
    )
    mag_destruct = _rank01_mask(np.maximum(lap_b2, 0.0) * sk, m)
    grav_r = _rank01_mask(np.maximum(grav_slope_b5, 0.0), m)
    subcap_conj = np.where(
        m,
        np.power(np.clip(clay_margin * (0.55 * grav_r + 0.45 * mag_destruct), 0.0, 1.0), 0.65),
        np.float32(0.0),
    ).astype(np.float32)

    th_wall = np.where(
        m,
        0.38 * _rank01_mask(uphead_diseq, m)
        + 0.36 * _rank01_mask(probe_wall, m)
        + 0.26 * _rank01_mask(sinter_corridor, m),
        np.float32(0.0),
    ).astype(np.float32)

    # 8-azimuth directional bridge over feeder-enhanced thermal sources
    seed_field = (0.55 * th_wall + 0.45 * subcap_conj).astype(np.float32)
    ridge_max = np.zeros(m.shape, dtype=np.float32)
    for k in range(8):
        ang = k * (np.pi / 8.0)
        rot_deg = float(np.degrees(ang))
        # Separable oriented smoothing via small rotated 15x15 anisotropic Gaussian kernel
        yy, xx = np.mgrid[-7:8, -7:8].astype(np.float32)
        ca, sa = float(np.cos(ang)), float(np.sin(ang))
        u_al = xx * ca + yy * sa
        u_pe = -xx * sa + yy * ca
        kern = np.exp(-0.5 * ((u_al / 5.5) ** 2 + (u_pe / 1.25) ** 2)).astype(np.float32)
        kern /= float(kern.sum())
        resp = ndi.convolve(seed_field, kern, mode="nearest")
        np.maximum(ridge_max, resp, out=ridge_max)
        _ = rot_deg
    iso_bg = ndi.gaussian_filter(seed_field, sigma=5.5, mode="nearest")
    vent_ridge = np.where(m, np.maximum(ridge_max - 0.72 * iso_bg, 0.0), np.float32(0.0)).astype(
        np.float32
    )
    return clay_margin, subcap_conj, th_wall, vent_ridge


def mohr_coulomb_conjugate_slip_tendency(
    geod_2ndinv_b4: np.ndarray,
    geod_shear_b7: np.ndarray,
    geod_dil_b8: np.ndarray,
    grav_vg_b11: np.ndarray,
    grav_hg_b18: np.ndarray,
    rtp_b2: np.ndarray,
    deq_b10: np.ndarray,
    ieq_b16: np.ndarray,
    valid: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Score subsurface lineaments by conjugate Mohr-Coulomb slip & dilatation tendency.

    Unlike H86R-SFG (which required parallelism to smoothed mapped catalogue strike and
    failed on oblique transfer zones), this operator is 100% catalogue-free and peaks
    when potential-field lineament strike lies near conjugate Riedel/Coulomb angles
    (+-28 deg) to the regional-to-transtensional NNE-NE Great Basin SHmax axis, gated
    by shear/second-invariant geodetic strain (Bands 4, 7, 8).
    """
    m = np.asarray(valid, dtype=bool)
    b4 = np.maximum(np.nan_to_num(np.asarray(geod_2ndinv_b4, dtype=np.float32), nan=0.0), 0.0)
    b7 = np.maximum(np.nan_to_num(np.asarray(geod_shear_b7, dtype=np.float32), nan=0.0), 0.0)
    b8 = np.nan_to_num(np.asarray(geod_dil_b8, dtype=np.float32), nan=0.0)

    # Verified gravity gradient vector (+B18 east, -B11 north); fault strike is perpendicular
    gx = ndi.gaussian_filter(
        np.nan_to_num(np.asarray(grav_hg_b18, dtype=np.float32), nan=0.0), sigma=1.8, mode="nearest"
    )
    gy_north = -ndi.gaussian_filter(
        np.nan_to_num(np.asarray(grav_vg_b11, dtype=np.float32), nan=0.0), sigma=1.8, mode="nearest"
    )
    b2 = np.nan_to_num(np.asarray(rtp_b2, dtype=np.float32), nan=0.0)
    mx = ndi.gaussian_filter(b2, sigma=2.0, order=(0, 1), mode="nearest")
    my_north = -ndi.gaussian_filter(b2, sigma=2.0, order=(1, 0), mode="nearest")

    # Lineament tangent azimuth in [0, pi) from combined Spin-2 structure tensor
    g_mag = np.hypot(gx, gy_north) + np.float32(1e-6)
    m_mag = np.hypot(mx, my_north) + np.float32(1e-6)
    tx = -0.65 * (gy_north / g_mag) - 0.35 * (my_north / m_mag)
    ty = 0.65 * (gx / g_mag) + 0.35 * (mx / m_mag)
    theta_strike = np.arctan2(ty, tx)  # azimuth counter-clockwise from East

    # Regional-to-Walker-Lane SHmax rotates smoothly from N25E (65 deg CCW from East)
    # under shear dominance toward N10E (80 deg CCW from East) under pure extension.
    shear_frac = np.clip(b7 / (b4 + np.float32(1e-6)), 0.0, 1.5)
    shmax_ang = np.deg2rad(80.0 - 14.0 * np.clip(shear_frac, 0.0, 1.0)).astype(np.float32)
    delta = np.abs(np.arctan2(np.sin(theta_strike - shmax_ang), np.cos(theta_strike - shmax_ang)))
    # Morris et al. (1996) optimal friction mu ~ 0.6 -> optimal conjugate angle ~ 29 deg (0.506 rad)
    conj_opt = np.float32(np.deg2rad(29.0))
    slip_opt = np.exp(-(((delta - conj_opt) / np.float32(np.deg2rad(19.0))) ** 2)).astype(np.float32)
    line_strength = 0.60 * _rank01_mask(g_mag, m) + 0.40 * _rank01_mask(m_mag, m)
    strain_drive = 0.55 * _rank01_mask(b7, m) + 0.45 * _rank01_mask(b4, m)
    coulomb_ts = np.where(
        m, line_strength * (0.35 + 0.65 * slip_opt) * (0.40 + 0.60 * strain_drive), np.float32(0.0)
    ).astype(np.float32)

    # High-pass seismic swarm x positive transtensional dilatation (Bands 8, 10, 16)
    s10 = np.log1p(np.maximum(np.nan_to_num(np.asarray(deq_b10, dtype=np.float32), nan=0.0), 0.0))
    s16 = np.log1p(np.maximum(np.nan_to_num(np.asarray(ieq_b16, dtype=np.float32), nan=0.0), 0.0))
    seis_hp = np.maximum(s10 - 0.65 * ndi.gaussian_filter(s10, sigma=16.0, mode="nearest"), 0.0) + (
        0.75 * np.maximum(s16 - 0.65 * ndi.gaussian_filter(s16, sigma=16.0, mode="nearest"), 0.0)
    )
    dil_pos = _rank01_mask(np.maximum(b8, 0.0), m)
    dil_swarm = np.where(
        m,
        0.55 * dil_pos + 0.45 * _rank01_mask(seis_hp, m) * (0.35 + 0.65 * dil_pos),
        np.float32(0.0),
    ).astype(np.float32)
    return coulomb_ts, dil_swarm


def prior_weighted_quadrant_blend(
    surface: np.ndarray,
    valid: np.ndarray,
    quad_ids: np.ndarray,
    *,
    alpha_pool: float = 0.62,
) -> np.ndarray:
    """Blend pooled footprint rank with per-quadrant rank.

    Cures both failure modes identified in 2026-10-27 forensics:
      - ``alpha_pool = 0.0`` (uniform 25% per quadrant in H86Q-BFRA) compressed Walker Lane SW;
      - ``alpha_pool = 1.0`` (raw global rank in GEMSDOE33 s33-seisdil) starved NE to 2.0%.
    At ``alpha_pool = 0.62``, fault-dense SW retains ~30-33% dot share while NW, NE,
    and SE each maintain ~20-26% coverage.
    """
    m = np.asarray(valid, dtype=bool)
    q_grid = np.asarray(quad_ids, dtype=np.int8)
    r_pool = _rank01_mask(surface, m)
    r_quad = np.zeros(m.shape, dtype=np.float32)
    for q in range(4):
        qm = m & (q_grid == q)
        if qm.any():
            r_quad[qm] = _rank01_mask(surface, qm)[qm]
    a = np.float32(alpha_pool)
    return np.where(m, a * r_pool + (np.float32(1.0) - a) * r_quad, np.float32(0.0)).astype(
        np.float32
    )


def dilatational_stepover_sharpen(
    prob: np.ndarray,
    dilaterate_b8: np.ndarray,
    valid: np.ndarray,
    *,
    crest_gain: float = 0.11,
    flank_trim: float = 0.08,
) -> np.ndarray:
    """Sharpen 1-D fault crests while suppressing flank trimming inside releasing stepovers."""
    m = np.asarray(valid, dtype=bool)
    p = np.where(m, np.clip(np.asarray(prob, dtype=np.float32), 0.0, 1.0), np.float32(0.0))
    hxx = ndi.gaussian_filter(p, sigma=1.6, order=(0, 2), mode="nearest")
    hyy = ndi.gaussian_filter(p, sigma=1.6, order=(2, 0), mode="nearest")
    hxy = ndi.gaussian_filter(p, sigma=1.6, order=(1, 1), mode="nearest")
    tr = hxx + hyy
    disc = np.hypot(hxx - hyy, 2.0 * hxy)
    lam_min = 0.5 * (tr - disc)
    lam_max = 0.5 * (tr + disc)
    ridge_crest = _rank01_mask(np.maximum(-lam_min, 0.0), m)
    flank_concav = _rank01_mask(np.maximum(lam_max, 0.0), m)

    # Inside positive geodetic dilatation (Band 8 > 0), fault stepovers form broad 2-D
    # damage zones rather than single 1-D lines, so flank_trim relaxes smoothly toward 0.
    dil_shield = _rank01_mask(np.maximum(dilaterate_b8, 0.0), m)
    eff_trim = np.float32(flank_trim) * (np.float32(1.0) - np.float32(0.75) * dil_shield)
    mult = np.clip(
        np.float32(1.0) + np.float32(crest_gain) * ridge_crest - eff_trim * flank_concav,
        0.72,
        1.25,
    )
    return np.where(m, np.clip(p * mult, 0.0, 0.999), np.float32(0.0)).astype(np.float32)
