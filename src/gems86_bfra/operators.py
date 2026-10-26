"""Physics & 1-D fault-strand survival operators for Lane H86Q-BFRA.

Implements four translation-invariant operators:
  1. ``broken_plate_flexural_shear_and_rollover``: Third cross-strike directional
     derivative ``-d^3_{nnn} Z_b`` (fault-plane flexural shear inflection) and
     hanging-wall rollover concavity ``-d^2_{nn} Z_b`` of Band 15 (``depth_to_base_surf``)
     along the vector-gravity-corroborated basinward normal ``(nr_basin, nc_basin)``.
  2. ``regolith_and_metasomatic_unmixing``: Scale-invariant two-endmember piedmont
     regolith provenance log-ratio jump ``|Delta_down ln((K*U)/Th^2)|`` on low-slope
     bajadas + hydrothermal potassium-metasomatism excess ``max(0, ln(K/Th) - med)``
     gated by shallow electrical conductivity (Band 17 ``cond_surf``).
  3. ``tmi_vs_rtp_remanence_dislocation``: Cross-strike phase-dislocation invariant
     between normalized Total Magnetic Intensity (Band 14 ``tmi``) and Reduced-to-Pole
     magnetics (Band 2 ``rtp``), corroborated by regional magnetic anomaly gradient
     (Band 1 ``mag_anom``), isolating reverse/oblique thermoremanent volcanic fault blocks.
  4. ``strand_tangent_sharpen_posterior``: Cross-strike Hessian ridge sharpening that
     boosts 1-D fault-strand crests while trimming diffuse 2-D flank/apron concavity
     prior to Exact 6-Ring Bernoulli Dinkelbach-CELF allocation.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from src.gems86_slcq.operators import masked_gaussian
from src.gems86_tcwb.operators import _bilinear_sample_clamped


def _rank01_local(arr: np.ndarray, valid: np.ndarray) -> np.ndarray:
    v = np.asarray(valid, dtype=bool)
    out = np.zeros(arr.shape, dtype=np.float32)
    if not v.any():
        return out
    vals = np.nan_to_num(np.asarray(arr[v], dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)
    if np.ptp(vals) <= 0.0:
        out[v] = np.float32(0.5)
        return out
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float32)
    ranks[order] = np.linspace(0.0, 1.0, vals.size, dtype=np.float32)
    out[v] = ranks
    return out


def broken_plate_flexural_shear_and_rollover(
    b15_zb: np.ndarray,
    b11_grav_south: np.ndarray,
    b18_grav_east: np.ndarray,
    valid: np.ndarray,
    *,
    sigmas_px: tuple[float, ...] = (3.0, 5.0),
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute broken-plate basement flexural shear ``-d^3_{nnn} Z_b`` and
    hanging-wall listric rollover concavity ``-d^2_{nn} Z_b`` gated by Bouguer
    gravity drop into the basin.

    For an idealized normal-fault basement step ``Z_b(x) = (D/2)*(1 + tanh(x/w))``
    along basinward normal ``+n``, ``-d^3_{nnn} Z_b`` peaks directly at ``x = 0``
    (the fault-plane inflection), while ``-d^2_{nn} Z_b > 0`` captures the
    immediate hanging-wall rollover concavity down-dip of the fault trace.
    """
    v = np.asarray(valid, dtype=bool)
    zb = np.asarray(b15_zb, dtype=np.float32)
    b11 = np.asarray(b11_grav_south, dtype=np.float32)
    b18 = np.asarray(b18_grav_east, dtype=np.float32)

    # Basinward unit vector combining +grad(Z_b) and -grad_H(Bouguer)
    zb_dir = masked_gaussian(zb, v, sigma=3.4)
    zr = ndi.gaussian_filter(zb_dir, sigma=1.0, order=(1, 0), mode="nearest")
    zc = ndi.gaussian_filter(zb_dir, sigma=1.0, order=(0, 1), mode="nearest")
    zmag = np.hypot(zr, zc)
    uz_r = np.where(zmag > 1e-5, zr / np.maximum(zmag, 1e-5), np.float32(0.0))
    uz_c = np.where(zmag > 1e-5, zc / np.maximum(zmag, 1e-5), np.float32(0.0))

    b11_s = masked_gaussian(b11, v, sigma=2.2)
    b18_s = masked_gaussian(b18, v, sigma=2.2)
    gmag = np.hypot(b11_s, b18_s)
    ug_r = np.where(gmag > 1e-5, -b11_s / np.maximum(gmag, 1e-5), np.float32(0.0))
    ug_c = np.where(gmag > 1e-5, -b18_s / np.maximum(gmag, 1e-5), np.float32(0.0))

    raw_nr = 0.58 * uz_r + 0.42 * ug_r
    raw_nc = 0.58 * uz_c + 0.42 * ug_c
    nmag = np.hypot(raw_nr, raw_nc)
    nr = np.where(nmag > 1e-5, raw_nr / np.maximum(nmag, 1e-5), np.float32(0.0)).astype(np.float32)
    nc = np.where(nmag > 1e-5, raw_nc / np.maximum(nmag, 1e-5), np.float32(0.0)).astype(np.float32)

    grav_drop = np.maximum(-(nr * b11_s + nc * b18_s), 0.0)
    g_scale = float(np.percentile(grav_drop[v], 68.0)) + 1e-5 if v.any() else 1.0
    grav_gate = np.tanh(grav_drop / g_scale).astype(np.float32)

    d3_acc = np.zeros(zb.shape, dtype=np.float32)
    rollover_acc = np.zeros(zb.shape, dtype=np.float32)
    nr2 = nr * nr
    nc2 = nc * nc
    nr3 = nr2 * nr
    nc3 = nc2 * nc
    nr2_nc = 3.0 * nr2 * nc
    nr_nc2 = 3.0 * nr * nc2

    for sig in sigmas_px:
        s = float(sig)
        zb_s = masked_gaussian(zb, v, sigma=s * 0.65)
        # Second directional derivative for rollover concavity (-d^2_{nn} Z_b > 0)
        z_rr = ndi.gaussian_filter(zb_s, sigma=s, order=(2, 0), mode="nearest")
        z_rc = ndi.gaussian_filter(zb_s, sigma=s, order=(1, 1), mode="nearest")
        z_cc = ndi.gaussian_filter(zb_s, sigma=s, order=(0, 2), mode="nearest")
        d2_nn = (nr2 * z_rr + 2.0 * nr * nc * z_rc + nc2 * z_cc) * (s * s)
        rollover_acc += np.maximum(-d2_nn, 0.0).astype(np.float32)

        # Third directional derivative for flexural shear inflection (-d^3_{nnn} Z_b > 0)
        z_rrr = ndi.gaussian_filter(zb_s, sigma=s, order=(3, 0), mode="nearest")
        z_rrc = ndi.gaussian_filter(zb_s, sigma=s, order=(2, 1), mode="nearest")
        z_rcc = ndi.gaussian_filter(zb_s, sigma=s, order=(1, 2), mode="nearest")
        z_ccc = ndi.gaussian_filter(zb_s, sigma=s, order=(0, 3), mode="nearest")
        d3_nnn = (nr3 * z_rrr + nr2_nc * z_rrc + nr_nc2 * z_rcc + nc3 * z_ccc) * (s * s * s)
        d3_acc += np.maximum(-d3_nnn, 0.0).astype(np.float32)

    inv_n = 1.0 / float(max(len(sigmas_px), 1))
    d3_shear = np.where(v, d3_acc * inv_n * grav_gate, np.float32(0.0)).astype(np.float32)
    rollover = np.where(v, rollover_acc * inv_n * grav_gate, np.float32(0.0)).astype(np.float32)
    return d3_shear, rollover, nr, nc


def regolith_and_metasomatic_unmixing(
    b6_tc: np.ndarray,
    rad_k: np.ndarray,
    rad_th: np.ndarray,
    rad_u: np.ndarray,
    b12_det_elev: np.ndarray,
    b19_elev_slope: np.ndarray,
    b17_cond: np.ndarray,
    valid: np.ndarray,
    *,
    seam_keep: np.ndarray | None = None,
    lahontan_band: np.ndarray | None = None,
    standoff_px: float = 4.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Separate two scale-invariant Aitchison radioelement processes:
      1. ``regolith_felsic_unmix_jump``: Cross-slope jump in the felsic-clast vs
         mature-clay isometric log-ratio ``ln((K*U)/Th^2)/sqrt(6)`` specifically
         weighted toward low-slope piedmont aprons (Band 19) outside Lake Lahontan.
      2. ``hydro_k_over_th_metasom``: Positive local potassium-over-thorium
         metasomatic enrichment ``max(0, ln(K/Th) - G_14(ln(K/Th)))`` corroborated
         by shallow electrical conductivity (Band 17 ``cond_surf``).
    """
    v = np.asarray(valid, dtype=bool)
    k_pos = np.maximum(np.asarray(rad_k, dtype=np.float32), 0.5)
    th_pos = np.maximum(np.asarray(rad_th, dtype=np.float32), 0.5)
    u_pos = np.maximum(np.asarray(rad_u, dtype=np.float32), 0.5)
    tc_pos = np.maximum(np.asarray(b6_tc, dtype=np.float32), 0.5)

    # 1. Piedmont regolith provenance unmixing coordinate (0-degree homogeneous in attenuation)
    ilr_prov = (np.log((k_pos * u_pos) / (th_pos * th_pos + 1e-6)) / np.sqrt(6.0)).astype(
        np.float32
    )
    ilr_sm = masked_gaussian(ilr_prov, v, sigma=1.5)

    elev = np.asarray(b12_det_elev, dtype=np.float32)
    elev_dir = masked_gaussian(elev, v, sigma=4.5)
    dr_up = ndi.gaussian_filter(elev_dir, sigma=1.0, order=(1, 0), mode="nearest")
    dc_up = ndi.gaussian_filter(elev_dir, sigma=1.0, order=(0, 1), mode="nearest")
    gmag = np.hypot(dr_up, dc_up)
    ur_down = np.where(gmag > 1e-6, -dr_up / np.maximum(gmag, 1e-6), np.float32(0.0))
    uc_down = np.where(gmag > 1e-6, -dc_up / np.maximum(gmag, 1e-6), np.float32(0.0))

    H, W = tc_pos.shape
    grid_r, grid_c = np.meshgrid(
        np.arange(H, dtype=np.float32),
        np.arange(W, dtype=np.float32),
        indexing="ij",
    )
    s = float(standoff_px)
    prov_up = _bilinear_sample_clamped(ilr_sm, grid_r - s * ur_down, grid_c - s * uc_down, v)
    prov_dn = _bilinear_sample_clamped(ilr_sm, grid_r + s * ur_down, grid_c + s * uc_down, v)

    ilr_mean = masked_gaussian(ilr_sm, v, sigma=12.0)
    ilr_disp = np.sqrt(masked_gaussian((ilr_sm - ilr_mean) ** 2, v, sigma=12.0) + 1e-4)
    disp_floor = float(np.percentile(ilr_disp[v], 20.0)) + 1e-4 if v.any() else 1.0
    prov_step = np.abs(prov_up - prov_dn) / np.maximum(ilr_disp, disp_floor)

    # Weight toward low-to-moderate piedmont slopes (suppressing steep bedrock cliffs)
    slp = np.maximum(np.asarray(b19_elev_slope, dtype=np.float32), 0.0)
    slp_p75 = float(np.percentile(slp[v], 75.0)) + 1e-4 if v.any() else 1.0
    piedmont_weight = np.exp(-0.55 * (slp / slp_p75)).astype(np.float32)

    seam = np.asarray(seam_keep, dtype=np.float32) if seam_keep is not None else np.float32(1.0)
    lah_gate = (
        1.0 - 0.70 * np.clip(np.asarray(lahontan_band, dtype=np.float32), 0.0, 1.0)
        if lahontan_band is not None
        else np.float32(1.0)
    )
    regolith_jump = np.where(
        v, prov_step * piedmont_weight * seam * lah_gate, np.float32(0.0)
    ).astype(np.float32)

    # 2. Hydrothermal K/Th metasomatic excess x shallow smectite/illite conductivity
    log_k_th = np.log(k_pos / th_pos).astype(np.float32)
    k_th_sm = masked_gaussian(log_k_th, v, sigma=1.6)
    k_th_bg = masked_gaussian(k_th_sm, v, sigma=14.0)
    k_th_std = np.sqrt(masked_gaussian((k_th_sm - k_th_bg) ** 2, v, sigma=14.0) + 1e-4)
    std_floor = float(np.percentile(k_th_std[v], 25.0)) + 1e-4 if v.any() else 1.0
    k_excess = np.maximum((k_th_sm - k_th_bg) / np.maximum(k_th_std, std_floor), 0.0)

    tc_bg = masked_gaussian(tc_pos, v, sigma=14.0)
    tc_active = np.tanh(tc_pos / np.maximum(tc_bg, 1.0)).astype(np.float32)

    cond_pos = np.maximum(np.asarray(b17_cond, dtype=np.float32), 0.0)
    cond_p70 = float(np.percentile(cond_pos[v], 70.0)) + 1e-4 if v.any() else 1.0
    cond_gate = (0.35 + 0.65 * np.tanh(cond_pos / cond_p70)).astype(np.float32)

    hydro_metasom = np.where(
        v, k_excess * cond_gate * tc_active * seam * lah_gate, np.float32(0.0)
    ).astype(np.float32)
    return regolith_jump, hydro_metasom


def tmi_vs_rtp_remanence_dislocation(
    b14_tmi: np.ndarray,
    b2_rtp: np.ndarray,
    b1_mag_anom: np.ndarray,
    nr_basin: np.ndarray,
    nc_basin: np.ndarray,
    valid: np.ndarray,
    *,
    seam_keep: np.ndarray | None = None,
) -> np.ndarray:
    """Detect reverse/oblique thermoremanent magnetization (TRM) fault-block edges
    where normalized Band 14 (TMI) and Band 2 (RTP) cross-strike derivatives diverge
    while Band 1 (regional mag_anom) confirms a genuine crustal magnetic boundary."""
    v = np.asarray(valid, dtype=bool)
    nr = np.asarray(nr_basin, dtype=np.float32)
    nc = np.asarray(nc_basin, dtype=np.float32)

    def _local_norm(field: np.ndarray) -> np.ndarray:
        f = np.asarray(field, dtype=np.float32)
        bg = masked_gaussian(f, v, sigma=16.0)
        hp = f - bg
        rms = np.sqrt(masked_gaussian(hp * hp, v, sigma=16.0) + 1e-4)
        fl = float(np.percentile(rms[v], 20.0)) + 1e-4 if v.any() else 1.0
        return np.where(v, hp / np.maximum(rms, fl), np.float32(0.0)).astype(np.float32)

    tmi_n = _local_norm(b14_tmi)
    rtp_n = _local_norm(b2_rtp)
    mag_n = _local_norm(b1_mag_anom)

    tmi_r = ndi.gaussian_filter(tmi_n, sigma=2.2, order=(1, 0), mode="nearest")
    tmi_c = ndi.gaussian_filter(tmi_n, sigma=2.2, order=(0, 1), mode="nearest")
    rtp_r = ndi.gaussian_filter(rtp_n, sigma=2.2, order=(1, 0), mode="nearest")
    rtp_c = ndi.gaussian_filter(rtp_n, sigma=2.2, order=(0, 1), mode="nearest")
    mag_r = ndi.gaussian_filter(mag_n, sigma=2.5, order=(1, 0), mode="nearest")
    mag_c = ndi.gaussian_filter(mag_n, sigma=2.5, order=(0, 1), mode="nearest")

    dn_tmi = nr * tmi_r + nc * tmi_c
    dn_rtp = nr * rtp_r + nc * rtp_c
    phase_disloc = np.abs(dn_tmi - dn_rtp)

    # Extra boost where RTP and TMI cross-strike gradients actually oppose in sign (reverse TRM!)
    sign_opp = 1.0 + 0.45 * (dn_tmi * dn_rtp < 0.0).astype(np.float32)
    crustal_edge = np.sqrt(np.hypot(mag_r, mag_c) * np.hypot(tmi_r, tmi_c) + 1e-8)

    seam = np.asarray(seam_keep, dtype=np.float32) if seam_keep is not None else np.float32(1.0)
    out = np.where(v, phase_disloc * sign_opp * crustal_edge * seam, np.float32(0.0)).astype(
        np.float32
    )
    return out


def strand_tangent_sharpen_posterior(
    p_surf: np.ndarray,
    valid: np.ndarray,
    *,
    crest_gain: float = 0.14,
    flank_trim: float = 0.12,
    sigma_px: float = 1.25,
) -> np.ndarray:
    """Sharpen calibrated fault-strand posteriors along 1-D ridges prior to
    Exact 6-Ring Bernoulli Dinkelbach-CELF allocation.

    Computes Hessian eigenvalues ``lam1 <= lam2`` of ``p_surf`` at ``sigma_px``:
      - Along a 1-D fault crest, cross-strike curvature ``lam1 < 0`` and ``|lam1| >> |lam2|``.
      - On off-crest halo aprons / troughs, cross-strike curvature ``lam2 > 0`` with
        weak ridge support.
    Returns a strictly bounded ``[0, 0.99]`` float32 posterior preserving ``0`` outside ``valid``.
    """
    v = np.asarray(valid, dtype=bool)
    p = np.where(v, np.clip(np.asarray(p_surf, dtype=np.float32), 0.0, 0.99), np.float32(0.0))
    if not v.any():
        return p

    s = float(sigma_px)
    p_sm = masked_gaussian(p, v, sigma=s * 0.5)
    h_rr = ndi.gaussian_filter(p_sm, sigma=s, order=(2, 0), mode="nearest") * (s * s)
    h_rc = ndi.gaussian_filter(p_sm, sigma=s, order=(1, 1), mode="nearest") * (s * s)
    h_cc = ndi.gaussian_filter(p_sm, sigma=s, order=(0, 2), mode="nearest") * (s * s)

    tr = 0.5 * (h_rr + h_cc)
    rad = np.hypot(0.5 * (h_rr - h_cc), h_rc)
    lam1 = tr - rad  # most negative curvature (cross-strike crest when < 0)
    lam2 = tr + rad  # most positive curvature (concave flank apron when > 0)

    crest = np.maximum(-lam1, 0.0) * (np.maximum(-lam1, 0.0) / (np.abs(lam2) + np.maximum(-lam1, 0.0) + 1e-6))
    flank = np.maximum(lam2, 0.0) * (lam1 > -0.45 * np.maximum(lam2, 0.0)).astype(np.float32)

    r_crest = _rank01_local(crest, v)
    r_flank = _rank01_local(flank, v)
    mult = 1.0 + float(crest_gain) * r_crest - float(flank_trim) * r_flank
    out = np.where(v, np.clip(p * mult, 0.0, 0.99), np.float32(0.0)).astype(np.float32)
    return out
