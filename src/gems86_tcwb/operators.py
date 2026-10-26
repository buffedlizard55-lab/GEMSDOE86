"""Physics operators for Lane H86P-TCWB.

Implements five translation-invariant structural-geological operators:
  1. ``downslope_tc_wash_asymmetry``: One-sided downslope radiometric Total Count
     (Band 6 ``tc``, verified GeoDAWN TC) wash-blanket depletion asymmetry and
     unsigned cross-break juxtaposition contrast across mesoscale piedmont slopes,
     with GeoDAWN flight-seam veto and Lahontan shoreline bench suppression.
  2. ``gravity_signed_basement_hinge_kink``: Cross-strike second derivative
     ``n_b^T H(Z_b) n_b`` of Band 15 (``depth_to_base_surf``) strictly signed by
     independent horizontal Bouguer gravity-drop concordance ``-(n_r*B11 + n_c*B18) > 0``.
  3. ``claycap_lateral_fault_seal_termination``: One-sided lateral termination of
     hanging-wall conductive smectite/illite clay caps (Band 17 ``cond_surf``)
     against resistive footwall fault seals, gated by RTP magnetite destruction.
  4. ``seismicity_conditioned_dilatancy_gate``: Multiplicative conjunction of
     positive Great Basin geodetic dilatation/shear strain rates (Bands 7, 8) with
     recorded microseismic proximity/intensity (Bands 10, 16).
  5. ``aitchison_clr_radiometric_jacobian``: Scale-invariant Aitchison (1982)
     centered log-ratio (CLR) compositional Jacobian norm across (Band 6 TC, K, eTh, eU).
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from src.gems86_slcq.operators import masked_gaussian


def _bilinear_sample_clamped(
    field: np.ndarray,
    sample_r: np.ndarray,
    sample_c: np.ndarray,
    valid: np.ndarray,
) -> np.ndarray:
    """Bilinearly sample ``field`` at ``(sample_r, sample_c)`` clamped inside grid bounds,
    propagating nearest-valid values across footprint boundaries to prevent edge cliffs."""
    v = np.asarray(valid, dtype=bool)
    f = np.asarray(field, dtype=np.float32)
    if not v.all() and v.any():
        _, idx = ndi.distance_transform_edt(~v, return_indices=True)
        f_fill = f[idx[0], idx[1]]
    else:
        f_fill = f
    H, W = f.shape
    rr = np.clip(sample_r, 0.0, float(H - 1))
    cc = np.clip(sample_c, 0.0, float(W - 1))
    coords = np.array([rr, cc], dtype=np.float32)
    sampled = ndi.map_coordinates(f_fill, coords, order=1, mode="nearest")
    return np.where(v, sampled, np.float32(0.0)).astype(np.float32)


def downslope_tc_wash_asymmetry(
    b6_tc: np.ndarray,
    b12_det_elev: np.ndarray,
    valid: np.ndarray,
    *,
    seam_keep: np.ndarray | None = None,
    lahontan_band: np.ndarray | None = None,
    standoff_px: float = 4.5,
    director_sigma_px: float = 5.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute signed downslope Total-Count wash depletion asymmetry and unsigned
    cross-slope TC juxtaposition contrast.

    Along the smoothed downslope unit vector ``u_down = -grad(G_sigma(det_elev)) / ||grad||``,
    positive ``asym_signed`` indicates higher Total Count on the upslope footwall
    fanhead/pediment than on the downslope sheetwash-blanketed hanging wall.
    """
    v = np.asarray(valid, dtype=bool)
    tc = np.where(v, np.maximum(np.asarray(b6_tc, dtype=np.float32), 0.0), np.float32(0.0))
    elev = np.asarray(b12_det_elev, dtype=np.float32)

    elev_dir = masked_gaussian(elev, v, sigma=float(director_sigma_px))
    dr_up = ndi.gaussian_filter(elev_dir, sigma=1.0, order=(1, 0), mode="nearest")
    dc_up = ndi.gaussian_filter(elev_dir, sigma=1.0, order=(0, 1), mode="nearest")
    gmag_dir = np.hypot(dr_up, dc_up)
    ur_down = np.where(gmag_dir > 1e-6, -dr_up / np.maximum(gmag_dir, 1e-6), np.float32(0.0))
    uc_down = np.where(gmag_dir > 1e-6, -dc_up / np.maximum(gmag_dir, 1e-6), np.float32(0.0))

    elev_loc = masked_gaussian(elev, v, sigma=2.2)
    dr_loc = ndi.gaussian_filter(elev_loc, sigma=1.0, order=(1, 0), mode="nearest")
    dc_loc = ndi.gaussian_filter(elev_loc, sigma=1.0, order=(0, 1), mode="nearest")
    break_mag = np.hypot(dr_loc, dc_loc)
    break_scale = float(np.percentile(break_mag[v], 65.0)) + 1e-5 if v.any() else 1.0
    break_gate = np.tanh(break_mag / break_scale).astype(np.float32)

    H, W = tc.shape
    grid_r, grid_c = np.meshgrid(
        np.arange(H, dtype=np.float32),
        np.arange(W, dtype=np.float32),
        indexing="ij",
    )
    tc_sm = masked_gaussian(tc, v, sigma=1.4)
    s = float(standoff_px)
    tc_upslope = _bilinear_sample_clamped(tc_sm, grid_r - s * ur_down, grid_c - s * uc_down, v)
    tc_downslope = _bilinear_sample_clamped(tc_sm, grid_r + s * ur_down, grid_c + s * uc_down, v)

    tc_mean = masked_gaussian(tc_sm, v, sigma=12.0)
    tc_disp = np.sqrt(masked_gaussian((tc_sm - tc_mean) ** 2, v, sigma=12.0) + 1e-4)
    disp_floor = float(np.percentile(tc_disp[v], 20.0)) + 1e-4 if v.any() else 1.0
    denom = np.maximum(tc_disp, disp_floor)

    raw_diff = (tc_upslope - tc_downslope) / denom
    gate = break_gate.copy()
    if seam_keep is not None:
        gate = gate * np.asarray(seam_keep, dtype=np.float32)
    if lahontan_band is not None:
        gate = gate * (1.0 - 0.65 * np.clip(np.asarray(lahontan_band, dtype=np.float32), 0.0, 1.0))

    asym_signed = np.where(v, np.maximum(raw_diff, 0.0) * gate, np.float32(0.0)).astype(np.float32)
    contrast_unsigned = np.where(v, np.abs(raw_diff) * gate, np.float32(0.0)).astype(np.float32)
    return asym_signed, contrast_unsigned


def gravity_signed_basement_hinge_kink(
    b15_zb: np.ndarray,
    b11_grav_south: np.ndarray,
    b18_grav_east: np.ndarray,
    valid: np.ndarray,
    *,
    sigmas_px: tuple[float, ...] = (2.2, 4.0),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute vector-gravity-signed cross-strike basement footwall hinge kink.

    Returns ``(signed_kink, nr_basin, nc_basin)`` where ``(nr_basin, nc_basin)`` is
    the unit vector pointing down-dip into deeper basement (``+grad Z_b``). At a
    normal-fault footwall crest, ``d^2 Z_b / dn^2 > 0`` AND Bouguer gravity drops
    into the hanging wall: ``-(nr * B11 + nc * B18) > 0``.
    """
    v = np.asarray(valid, dtype=bool)
    zb = np.asarray(b15_zb, dtype=np.float32)
    b11 = np.asarray(b11_grav_south, dtype=np.float32)
    b18 = np.asarray(b18_grav_east, dtype=np.float32)

    zb_dir = masked_gaussian(zb, v, sigma=3.2)
    zr = ndi.gaussian_filter(zb_dir, sigma=1.0, order=(1, 0), mode="nearest")
    zc = ndi.gaussian_filter(zb_dir, sigma=1.0, order=(0, 1), mode="nearest")
    zmag = np.hypot(zr, zc)
    nr = np.where(zmag > 1e-5, zr / np.maximum(zmag, 1e-5), np.float32(0.0)).astype(np.float32)
    nc = np.where(zmag > 1e-5, zc / np.maximum(zmag, 1e-5), np.float32(0.0)).astype(np.float32)

    # Gravity drop toward deeper basement: -n_b . (B11_south, B18_east) > 0
    b11_s = masked_gaussian(b11, v, sigma=2.0)
    b18_s = masked_gaussian(b18, v, sigma=2.0)
    grav_drop = np.maximum(-(nr * b11_s + nc * b18_s), 0.0)
    g_scale = float(np.percentile(grav_drop[v], 70.0)) + 1e-5 if v.any() else 1.0
    grav_concord = np.tanh(grav_drop / g_scale).astype(np.float32)

    kink_acc = np.zeros(zb.shape, dtype=np.float32)
    for sig in sigmas_px:
        s = float(sig)
        zb_s = masked_gaussian(zb, v, sigma=s * 0.75)
        z_rr = ndi.gaussian_filter(zb_s, sigma=s, order=(2, 0), mode="nearest")
        z_cc = ndi.gaussian_filter(zb_s, sigma=s, order=(0, 2), mode="nearest")
        z_rc = ndi.gaussian_filter(zb_s, sigma=s, order=(1, 1), mode="nearest")
        knn = (nr * nr * z_rr + 2.0 * nr * nc * z_rc + nc * nc * z_cc) * (s * s)
        kink_acc += np.maximum(knn, 0.0).astype(np.float32)
    kink_acc /= float(max(len(sigmas_px), 1))

    signed_kink = np.where(v, kink_acc * grav_concord, np.float32(0.0)).astype(np.float32)
    return signed_kink, nr, nc


def claycap_lateral_fault_seal_termination(
    b17_cond: np.ndarray,
    nr_basin: np.ndarray,
    nc_basin: np.ndarray,
    rtp_demag_trough: np.ndarray,
    valid: np.ndarray,
    *,
    seam_keep: np.ndarray | None = None,
) -> np.ndarray:
    """Detect lateral termination of conductive hanging-wall hydrothermal smectite/illite
    clay caps against resistive footwall fault seals, corroborated by magnetite destruction.

    Along the basinward down-dip normal ``(nr_basin, nc_basin)``, ``grad log(1 + cond_+)``
    is positive where hanging-wall conductance rises sharply across the fault seal.
    """
    v = np.asarray(valid, dtype=bool)
    c_raw = np.asarray(b17_cond, dtype=np.float32)
    c_min = float(np.min(c_raw[v])) if v.any() else 0.0
    cond_log = np.log1p(np.maximum(c_raw - c_min, 0.0)).astype(np.float32)
    cond_sm = masked_gaussian(cond_log, v, sigma=1.8)

    cr = ndi.gaussian_filter(cond_sm, sigma=1.2, order=(1, 0), mode="nearest")
    cc = ndi.gaussian_filter(cond_sm, sigma=1.2, order=(0, 1), mode="nearest")
    one_sided_step = np.maximum(nr_basin * cr + nc_basin * cc, 0.0)
    total_grad = np.hypot(cr, cc)
    # Combine hanging-wall-high polarity (70%) with sharp lateral termination (30%)
    lat_term = 0.70 * one_sided_step + 0.30 * total_grad

    demag = np.maximum(np.asarray(rtp_demag_trough, dtype=np.float32), 0.0)
    d_scale = float(np.percentile(demag[v], 75.0)) + 1e-5 if v.any() else 1.0
    demag_gate = 0.40 + 0.60 * np.tanh(demag / d_scale)
    if seam_keep is not None:
        demag_gate = demag_gate * (0.35 + 0.65 * np.asarray(seam_keep, dtype=np.float32))

    return np.where(v, lat_term * demag_gate, np.float32(0.0)).astype(np.float32)


def seismicity_conditioned_dilatancy_gate(
    b7_shear: np.ndarray,
    b8_dilate: np.ndarray,
    b10_deq: np.ndarray,
    b16_ieq: np.ndarray,
    valid: np.ndarray,
) -> np.ndarray:
    """Multiplicative conjunction of positive high-pass transtensional geodetic strain
    (Bands 7, 8) and microseismic activity (Band 10 proximity & Band 16 intensity)."""
    v = np.asarray(valid, dtype=bool)
    sh = np.asarray(b7_shear, dtype=np.float32)
    dl = np.asarray(b8_dilate, dtype=np.float32)
    deq = np.asarray(b10_deq, dtype=np.float32)
    ieq = np.asarray(b16_ieq, dtype=np.float32)

    dil_pos = np.maximum(dl - masked_gaussian(dl, v, sigma=26.0), 0.0)
    shr_pos = np.maximum(sh - masked_gaussian(sh, v, sigma=26.0), 0.0)
    strain_conj = np.sqrt(dil_pos * shr_pos + 1e-12) + 0.45 * dil_pos
    s_scale = float(np.percentile(strain_conj[v], 75.0)) + 1e-6 if v.any() else 1.0
    strain_gate = np.tanh(strain_conj / s_scale)

    med_deq = float(np.median(np.maximum(deq[v], 0.0))) + 1e-5 if v.any() else 1.0
    eq_prox = np.exp(-np.maximum(deq, 0.0) / (0.65 * med_deq))
    ieq_pos = np.maximum(ieq - float(np.percentile(ieq[v], 35.0)) if v.any() else ieq, 0.0)
    i_scale = float(np.percentile(ieq_pos[v], 85.0)) + 1e-6 if v.any() else 1.0
    seis_gate = np.clip(0.55 * eq_prox + 0.45 * np.tanh(ieq_pos / i_scale), 0.0, 1.0)

    return np.where(v, strain_gate * seis_gate, np.float32(0.0)).astype(np.float32)


def aitchison_clr_radiometric_jacobian(
    b6_tc: np.ndarray,
    rad_k: np.ndarray,
    rad_th: np.ndarray,
    rad_u: np.ndarray,
    valid: np.ndarray,
    *,
    seam_keep: np.ndarray | None = None,
    lahontan_band: np.ndarray | None = None,
    sigma_px: float = 1.8,
) -> np.ndarray:
    """Compute Frobenius norm of the spatial Jacobian of Aitchison (1982) centered
    log-ratios across ``(TC, K, eTh, eU)``.

    Strictly invariant to multiplying all four channels at a pixel by any positive
    scalar ``alpha(x, y) > 0`` (e.g., soil-moisture or vegetation gamma attenuation).
    """
    v = np.asarray(valid, dtype=bool)
    eps = np.float32(1e-3)
    # Normalize channel floors only by positive constant pseudocounts so pointwise
    # multiplicative invariance c * (TC, K, Th, U) holds up to eps -> 0.
    chans = [
        np.maximum(np.asarray(b6_tc, dtype=np.float32), eps),
        np.maximum(np.asarray(rad_k, dtype=np.float32), eps),
        np.maximum(np.asarray(rad_th, dtype=np.float32), eps),
        np.maximum(np.asarray(rad_u, dtype=np.float32), eps),
    ]
    logs = [np.log(c) for c in chans]
    mean_log = 0.25 * (logs[0] + logs[1] + logs[2] + logs[3])

    frob_sq = np.zeros(b6_tc.shape, dtype=np.float32)
    s = float(sigma_px)
    for lg in logs:
        clr_i = masked_gaussian(lg - mean_log, v, sigma=s)
        gr = ndi.gaussian_filter(clr_i, sigma=1.0, order=(1, 0), mode="nearest")
        gc_ = ndi.gaussian_filter(clr_i, sigma=1.0, order=(0, 1), mode="nearest")
        frob_sq += gr * gr + gc_ * gc_

    j_norm = np.sqrt(frob_sq)
    if seam_keep is not None:
        j_norm = j_norm * np.asarray(seam_keep, dtype=np.float32)
    if lahontan_band is not None:
        j_norm = j_norm * (1.0 - 0.55 * np.clip(np.asarray(lahontan_band, dtype=np.float32), 0.0, 1.0))
    return np.where(v, j_norm, np.float32(0.0)).astype(np.float32)
