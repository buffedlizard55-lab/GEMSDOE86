"""Physics operators for Lane H86M-SLCQ.

Implements four mathematically testable geophysical transforms:
  1. ``salem_adaptive_dip_and_sharpness``: 2-D vector Newton Salem-Fairhead (2007)
     multi-altitude tilt-contour migration with reflective FFT padding and
     Nadaraya-Watson contact-weighted dip propagation, estimating local fault dip
     cot(delta)(x,y) and down-dip vector without polarity sensitivity (~0 shift on
     subvertical 80-90 deg strike-slip faults, positive down-dip vector on dipping
     normal faults carried cleanly across the hanging-wall-to-emergence zone).
  2. ``adaptive_vector_updip_pullback``: Bilinear hanging-wall-to-emergence pullback
     using the local dip-adaptive displacement vector Delta_s(x,y) = (Z_b/cell_m) * c_vec(x,y).
  3. ``steerable_log_cauchy_step_vs_dike``: 8-azimuth Fourier log-Cauchy odd (step)
     minus even (symmetric volcanic dike/ridge) quadrature filter bank with reflective
     boundary padding, zero DC, and zero linear-ramp response.
  4. ``fit_predict_fold_safe_bmr``: Strict out-of-quadrant Cordell (1973) multi-scale
     Bouguer-compaction forward gravity model predicting Band 13 (iso_grav_anom) from
     Band 15 (depth_to_base_surf) strictly on training-domain pixels and extracting
     translation-invariant residual step features.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.fft import fftfreq, irfft2, rfft2, rfftfreq


def masked_gaussian(arr: np.ndarray, valid: np.ndarray, sigma: float) -> np.ndarray:
    v = np.asarray(valid, dtype=bool).astype(np.float32)
    a = np.where(valid, np.asarray(arr, dtype=np.float32), np.float32(0.0))
    if sigma <= 0.0:
        return a
    num = ndi.gaussian_filter(a, sigma=float(sigma), mode="nearest")
    den = ndi.gaussian_filter(v, sigma=float(sigma), mode="nearest")
    return np.where(valid & (den > 1e-5), num / np.maximum(den, 1e-5), np.float32(0.0)).astype(
        np.float32
    )


def _reflect_pad_for_fft(arr: np.ndarray, valid: np.ndarray, pad: int) -> np.ndarray:
    """Fill outside ``valid`` smoothly via nearest-valid propagation and reflect-pad by ``pad``
    pixels so step functions and ramps have zero periodic wrap-around cliffs in 2-D FFT."""
    v = np.asarray(valid, dtype=bool)
    a = np.asarray(arr, dtype=np.float32)
    if not v.all() and v.any():
        _, idx = ndi.distance_transform_edt(~v, return_indices=True)
        filled = a[idx[0], idx[1]]
    else:
        filled = a
    p = min(int(pad), max(min(a.shape) - 2, 1))
    return np.pad(filled, ((p, p), (p, p)), mode="reflect"), p


def salem_adaptive_dip_and_sharpness(
    field: np.ndarray,
    depth_to_basement_m: np.ndarray | None,
    valid: np.ndarray,
    *,
    z1_m: float = 150.0,
    z2_m: float = 750.0,
    cell_m: float = 100.0,
    max_cot_dip: float = 0.85,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Estimate Salem-Fairhead (2007) tilt zero-contour sharpness at ``z1_m`` and
    polarity-invariant 2-D down-dip cotangent vector ``(cot_r, cot_c)`` + scalar ``cot_mag``.
    """
    f = np.asarray(field, dtype=np.float32)
    v = np.asarray(valid, dtype=bool)
    H, W = f.shape
    dz_px = max((float(z2_m) - float(z1_m)) / float(cell_m), 1e-3)

    f_hp = f - masked_gaussian(f, v, sigma=42.0)
    f_pad, pad = _reflect_pad_for_fft(f_hp, v, pad=28)
    del f_hp
    Hp, Wp = f_pad.shape

    spec = rfft2(f_pad, s=(Hp, Wp))
    del f_pad
    ky = fftfreq(Hp, d=cell_m).astype(np.float32)[:, None]
    kx = rfftfreq(Wp, d=cell_m).astype(np.float32)[None, :]
    kr = np.sqrt(kx * kx + ky * ky)
    k_nyq = float(0.5 / cell_m)
    anti_ring = np.exp(-((kr / (0.75 * k_nyq)) ** 4)).astype(np.float32)

    def _tilt(z_m: float) -> np.ndarray:
        up = np.exp(-2.0 * np.pi * float(z_m) * kr).astype(np.float32) * anti_ring
        phi_z = irfft2(spec * up, s=(Hp, Wp))[pad : pad + H, pad : pad + W].astype(np.float32)
        dz_phi = irfft2(spec * (2.0 * np.pi * kr * up), s=(Hp, Wp))[
            pad : pad + H, pad : pad + W
        ].astype(np.float32)
        gr = ndi.gaussian_filter(phi_z, sigma=1.0, order=(1, 0), mode="nearest") / float(cell_m)
        gc_ = ndi.gaussian_filter(phi_z, sigma=1.0, order=(0, 1), mode="nearest") / float(cell_m)
        gh = np.hypot(gr, gc_)
        eps = float(max(np.percentile(gh[v], 10) * 0.05, 1e-9)) if v.any() else 1e-9
        return np.arctan2(dz_phi, gh + eps).astype(np.float32)

    th1 = _tilt(z1_m)
    th2 = _tilt(z2_m)
    del spec, kr, anti_ring

    th_mid = 0.5 * (th1 + th2)
    gtr = ndi.gaussian_filter(th_mid, sigma=1.2, order=(1, 0), mode="nearest").astype(np.float32)
    gtc = ndi.gaussian_filter(th_mid, sigma=1.2, order=(0, 1), mode="nearest").astype(np.float32)
    gt_sq = gtr * gtr + gtc * gtc
    gt_mag = np.sqrt(gt_sq)

    gt1_r = ndi.gaussian_filter(th1, sigma=1.1, order=(1, 0), mode="nearest")
    gt1_c = ndi.gaussian_filter(th1, sigma=1.1, order=(0, 1), mode="nearest")
    grad_th1 = np.hypot(gt1_r, gt1_c).astype(np.float32)
    sech1 = (1.0 / np.cosh(np.clip(th1 / 0.35, -8.0, 8.0))) ** 2
    sharp_z1 = np.where(v, grad_th1 * sech1, np.float32(0.0)).astype(np.float32)

    eps_g = float(np.percentile(gt_mag[v], 20) * 0.25 + 1e-4) if v.any() else 1e-3
    dth = (th2 - th1).astype(np.float32)
    denom = gt_sq + np.float32(eps_g * eps_g)

    # For finite-thickness Cenozoic basins (Z_b ~ 0.2-2.0 km) after regional high-pass,
    # analytical integration of int_{h1}^{h2} zeta/(zeta+z)^2 dzeta shows d(zeta_bar)/dz ~= 0.31,
    # so dividing by dz_eff_px = dz_px * 0.31 recovers calibrated cot(delta) on dipping basin-margin
    # faults while keeping vertical (90 deg) strike-slip faults identically at 0!
    dz_eff_px = np.float32(dz_px * 0.31)
    c0_r = (-dth * gtr / denom / dz_eff_px).astype(np.float32)
    c0_c = (-dth * gtc / denom / dz_eff_px).astype(np.float32)

    # Nadaraya-Watson contact-weighted smoothing carries buried-contact dip cleanly
    # across the 0..10 px emergence zone without zero-dilution!
    sech_contact = (1.0 / np.cosh(np.clip(th_mid / 0.50, -8.0, 8.0))) ** 2
    w_contact = np.where(v, sech_contact * gt_mag, np.float32(0.0)).astype(np.float32)
    w_floor = float(np.percentile(w_contact[v], 25) * 0.10 + 1e-6) if v.any() else 1e-5
    w_den = ndi.gaussian_filter(w_contact, sigma=5.5, mode="nearest") + np.float32(w_floor)
    cr = (ndi.gaussian_filter(w_contact * c0_r, sigma=5.5, mode="nearest") / w_den).astype(
        np.float32
    )
    cc = (ndi.gaussian_filter(w_contact * c0_c, sigma=5.5, mode="nearest") / w_den).astype(
        np.float32
    )

    if depth_to_basement_m is not None:
        zb = np.maximum(np.asarray(depth_to_basement_m, dtype=np.float32), 0.0)
        zb_sm = masked_gaussian(zb, v, sigma=3.5)
        zr = ndi.gaussian_filter(zb_sm, sigma=1.5, order=(1, 0), mode="nearest").astype(np.float32)
        zc = ndi.gaussian_filter(zb_sm, sigma=1.5, order=(0, 1), mode="nearest").astype(np.float32)
        znorm = np.hypot(zr, zc)
        has_slope = znorm > 8.0
        ur_b = np.where(has_slope, zr / np.maximum(znorm, 1e-5), np.float32(0.0))
        uc_b = np.where(has_slope, zc / np.maximum(znorm, 1e-5), np.float32(0.0))
        cmag0 = np.hypot(cr, cc)
        cr = np.where(has_slope, 0.70 * cr + 0.30 * cmag0 * ur_b, cr).astype(np.float32)
        cc = np.where(has_slope, 0.70 * cc + 0.30 * cmag0 * uc_b, cc).astype(np.float32)

    cmag = np.hypot(cr, cc).astype(np.float32)
    scale = np.where(cmag > float(max_cot_dip), float(max_cot_dip) / np.maximum(cmag, 1e-6), 1.0)
    cr = np.where(v, cr * scale, np.float32(0.0)).astype(np.float32)
    cc = np.where(v, cc * scale, np.float32(0.0)).astype(np.float32)
    cmag = np.where(v, np.minimum(cmag, float(max_cot_dip)), np.float32(0.0)).astype(np.float32)
    return sharp_z1, cmag, cr, cc


def adaptive_vector_updip_pullback(
    deep_plane: np.ndarray,
    depth_to_basement_m: np.ndarray,
    cot_r: np.ndarray,
    cot_c: np.ndarray,
    valid: np.ndarray,
    *,
    cell_m: float = 100.0,
    max_shift_px: float = 12.0,
    pulled_weight: float = 0.75,
) -> np.ndarray:
    """Pull a subsurface step/conduit plane up-dip from hanging wall onto surface emergence
    using the spatially varying 2-D Salem dip-cotangent vector ``(cot_r, cot_c)``."""
    plane = np.asarray(deep_plane, dtype=np.float32)
    zb = np.maximum(np.asarray(depth_to_basement_m, dtype=np.float32), 0.0)
    cr = np.asarray(cot_r, dtype=np.float32)
    cc = np.asarray(cot_c, dtype=np.float32)
    v = np.asarray(valid, dtype=bool)
    H, W = plane.shape

    zb_sm = masked_gaussian(zb, v, sigma=3.0)
    cmag = np.hypot(cr, cc)
    ur = np.where(cmag > 1e-4, cr / np.maximum(cmag, 1e-4), np.float32(0.0))
    uc = np.where(cmag > 1e-4, cc / np.maximum(cmag, 1e-4), np.float32(0.0))

    rr, cc_grid = np.indices((H, W), dtype=np.float32)
    # Probe hanging-wall sediment thickness 4 px down-dip along local Salem dip direction
    zb_hw = ndi.map_coordinates(
        zb_sm,
        [np.clip(rr + 4.0 * ur, 0.0, H - 1.0), np.clip(cc_grid + 4.0 * uc, 0.0, W - 1.0)],
        order=1,
        mode="nearest",
    ).astype(np.float32)
    zb_eff = np.maximum(zb_sm, zb_hw)

    dr = (zb_eff / float(cell_m)) * cr
    dc = (zb_eff / float(cell_m)) * cc
    dmag = np.hypot(dr, dc)
    dscale = np.where(dmag > float(max_shift_px), float(max_shift_px) / np.maximum(dmag, 1e-6), 1.0)
    dr = (dr * dscale).astype(np.float32)
    dc = (dc * dscale).astype(np.float32)

    pulled = ndi.map_coordinates(
        plane,
        [np.clip(rr + dr, 0.0, H - 1.0), np.clip(cc_grid + dc, 0.0, W - 1.0)],
        order=1,
        mode="nearest",
    ).astype(np.float32)

    w_pull = float(pulled_weight) * np.clip(dmag / 1.2, 0.0, 1.0)
    out = w_pull * pulled + (1.0 - w_pull) * plane
    return np.where(v, out, np.float32(0.0)).astype(np.float32)


def steerable_log_cauchy_step_vs_dike(
    field: np.ndarray,
    valid: np.ndarray,
    *,
    wavelength_m: float = 500.0,
    n_orient: int = 8,
    along_strike_ratio: float = 2.2,
    dike_veto_gamma: float = 1.05,
    cell_m: float = 100.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Steerable ``n_orient``-azimuth 2-D Fourier log-Cauchy quadrature filter separating
    odd-symmetric fault-contact steps from even-symmetric volcanic dikes/ridges.

    Removes any global 2-D affine plane (DC + linear ramp) on ``valid`` before reflective
    FFT padding so regional background tilts produce identically zero interior response.
    """
    f = np.asarray(field, dtype=np.float32)
    v = np.asarray(valid, dtype=bool)
    H, W = f.shape

    # Exact 2-D affine plane removal on valid pixels (guarantees zero DC + zero linear ramp!)
    if v.any():
        yy, xx = np.indices((H, W), dtype=np.float32)
        yv = (yy[v] - 0.5 * H) / max(float(H), 1.0)
        xv = (xx[v] - 0.5 * W) / max(float(W), 1.0)
        A = np.column_stack([np.ones(yv.size, dtype=np.float32), xv, yv])
        coef, _, _, _ = np.linalg.lstsq(A.astype(np.float64), f[v].astype(np.float64), rcond=None)
        plane = (
            float(coef[0])
            + float(coef[1]) * ((xx - 0.5 * W) / max(float(W), 1.0))
            + float(coef[2]) * ((yy - 0.5 * H) / max(float(H), 1.0))
        ).astype(np.float32)
        f_det = f - plane
        del yy, xx, yv, xv, A, plane
    else:
        f_det = f

    f_hp = f_det - masked_gaussian(f_det, v, sigma=max(wavelength_m / cell_m * 4.5, 26.0))
    del f_det
    pad_px = int(min(max(round(wavelength_m / cell_m * 3.5), 24), 48))
    f_pad, pad = _reflect_pad_for_fft(f_hp, v, pad=pad_px)
    del f_hp
    Hp, Wp = f_pad.shape

    spec = rfft2(f_pad, s=(Hp, Wp))
    del f_pad
    ky = fftfreq(Hp, d=cell_m).astype(np.float32)[:, None]
    kx = rfftfreq(Wp, d=cell_m).astype(np.float32)[None, :]

    k0 = float(1.0 / max(wavelength_m, cell_m * 2.0))
    sig_par = float(along_strike_ratio * wavelength_m)
    two_pi2_sig2 = float(2.0 * (np.pi**2) * (sig_par**2))

    best_amp2 = np.full((H, W), -1.0, dtype=np.float32)
    best_odd = np.zeros((H, W), dtype=np.float32)
    best_even = np.zeros((H, W), dtype=np.float32)

    for m in range(int(n_orient)):
        phi = float(m) * np.pi / float(n_orient)
        c_p = np.float32(np.cos(phi))
        s_p = np.float32(np.sin(phi))
        k_perp = kx * c_p + ky * s_p
        k_par = -kx * s_p + ky * c_p

        u = np.abs(k_perp) / np.float32(k0)
        w_perp = (u * u) * np.exp(np.float32(2.0) * (np.float32(1.0) - np.minimum(u, 25.0)))
        g_par = np.exp(-np.minimum(np.float32(two_pi2_sig2) * (k_par * k_par), 40.0))
        h_even = (w_perp * g_par).astype(np.float32)
        sgn = np.sign(k_perp).astype(np.float32)

        even_m = irfft2(spec * h_even, s=(Hp, Wp))[pad : pad + H, pad : pad + W].astype(np.float32)
        odd_m = irfft2(spec * (-1j * sgn * h_even), s=(Hp, Wp))[
            pad : pad + H, pad : pad + W
        ].astype(np.float32)

        amp2 = odd_m * odd_m + even_m * even_m
        take = amp2 > best_amp2
        best_amp2 = np.where(take, amp2, best_amp2)
        best_odd = np.where(take, np.abs(odd_m), best_odd)
        best_even = np.where(take, np.abs(even_m), best_even)

    del spec
    amp = np.sqrt(np.maximum(best_amp2, 0.0)).astype(np.float32)
    noise_floor = float(np.percentile(amp[v], 20) + 1e-6) if v.any() else 1e-5
    step_energy = np.maximum(best_odd - np.float32(dike_veto_gamma) * best_even, 0.0).astype(
        np.float32
    )
    step_pc = np.maximum(best_odd - np.float32(dike_veto_gamma) * best_even, 0.0) / (
        amp + np.float32(noise_floor)
    )
    dike_energy = np.maximum(best_even - best_odd, 0.0).astype(np.float32)
    return (
        np.where(v, step_energy, np.float32(0.0)).astype(np.float32),
        np.where(v, np.clip(step_pc, 0.0, 1.0), np.float32(0.0)).astype(np.float32),
        np.where(v, dike_energy, np.float32(0.0)).astype(np.float32),
    )


def garland_poisson_admittance_jump(
    rtp_field: np.ndarray,
    grav_slope_b5: np.ndarray,
    valid: np.ndarray,
    *,
    seam_keep: np.ndarray | None = None,
) -> np.ndarray:
    """Garland (1951) Poisson magnetization-to-density admittance jump across contacts."""
    v = np.asarray(valid, dtype=bool)
    rtp_sm = masked_gaussian(rtp_field, v, sigma=2.0)
    mr = ndi.gaussian_filter(rtp_sm, sigma=1.2, order=(1, 0), mode="nearest")
    mc = ndi.gaussian_filter(rtp_sm, sigma=1.2, order=(0, 1), mode="nearest")
    mag_g = np.hypot(mr, mc).astype(np.float32)
    grav_g = masked_gaussian(np.maximum(grav_slope_b5, 0.0), v, sigma=1.5)

    eps_m = float(np.percentile(mag_g[v], 25) + 1e-4) if v.any() else 1e-3
    eps_g = float(np.percentile(grav_g[v], 25) + 1e-4) if v.any() else 1e-3
    log_admit = np.log((mag_g + eps_m) / (grav_g + eps_g)).astype(np.float32)
    log_admit = masked_gaussian(log_admit, v, sigma=1.8)
    ar = ndi.gaussian_filter(log_admit, sigma=1.2, order=(1, 0), mode="nearest")
    ac = ndi.gaussian_filter(log_admit, sigma=1.2, order=(0, 1), mode="nearest")
    jump = np.hypot(ar, ac).astype(np.float32)
    if seam_keep is not None:
        jump = jump * np.asarray(seam_keep, dtype=np.float32)
    return np.where(v, jump, np.float32(0.0)).astype(np.float32)


def build_bmr_basis(depth_to_basement_m: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Build 6-column Cordell (1973) multi-scale Bouguer-compaction forward basis from B15 only."""
    v = np.asarray(valid, dtype=bool)
    zb_km = np.where(
        v, np.maximum(np.asarray(depth_to_basement_m, dtype=np.float32), 0.0) / 1000.0, 0.0
    )
    H, W = zb_km.shape
    psi = np.zeros((6, H, W), dtype=np.float32)
    psi[0] = v.astype(np.float32)
    psi[1] = zb_km
    psi[2] = np.where(v, 1.0 - np.exp(-zb_km / 1.2), 0.0).astype(np.float32)
    psi[3] = masked_gaussian(zb_km, v, sigma=4.0)
    psi[4] = masked_gaussian(zb_km, v, sigma=12.0)
    psi[5] = masked_gaussian(zb_km, v, sigma=30.0)
    return psi


def fit_bmr_weights(
    psi: np.ndarray,
    b13_grav: np.ndarray,
    train_mask: np.ndarray,
    *,
    ridge_l2: float = 10.0,
) -> np.ndarray:
    """Fit ridge-regularized forward gravity weights strictly on ``train_mask`` pixels."""
    tm = np.asarray(train_mask, dtype=bool)
    X = psi[:, tm].T.astype(np.float64)
    y = np.asarray(b13_grav, dtype=np.float64)[tm]
    if X.shape[0] < 10:
        return np.zeros(psi.shape[0], dtype=np.float64)
    gram = X.T @ X
    reg = np.diag([0.0] + [float(ridge_l2)] * (psi.shape[0] - 1))
    rhs = X.T @ y
    return np.linalg.solve(gram + reg, rhs)


def extract_bmr_residual_planes(
    residual_grav: np.ndarray,
    depth_to_basement_m: np.ndarray,
    cot_r: np.ndarray,
    cot_c: np.ndarray,
    valid: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Extract ONLY translation-invariant residual gradient & odd-step features (never raw level)
    from ``r_BMR = g_obs - g_hat_base(Z_b)``, pulled updip by local Salem ``(cot_r, cot_c)``."""
    v = np.asarray(valid, dtype=bool)
    r_hp = np.asarray(residual_grav, dtype=np.float32) - masked_gaussian(
        residual_grav, v, sigma=36.0
    )
    r_sm = masked_gaussian(r_hp, v, sigma=1.6)
    gr = ndi.gaussian_filter(r_sm, sigma=1.1, order=(1, 0), mode="nearest")
    gc_ = ndi.gaussian_filter(r_sm, sigma=1.1, order=(0, 1), mode="nearest")
    grad_mag = np.where(v, np.hypot(gr, gc_), np.float32(0.0)).astype(np.float32)
    grad_pull = adaptive_vector_updip_pullback(grad_mag, depth_to_basement_m, cot_r, cot_c, v)

    lc_step, _, _ = steerable_log_cauchy_step_vs_dike(
        r_hp, v, wavelength_m=600.0, n_orient=8, dike_veto_gamma=1.05
    )
    lc_pull = adaptive_vector_updip_pullback(lc_step, depth_to_basement_m, cot_r, cot_c, v)
    return grad_pull, lc_pull


def fit_predict_fold_safe_bmr(
    b13_grav: np.ndarray,
    b15_zb: np.ndarray,
    valid: np.ndarray,
    train_mask: np.ndarray,
    *,
    cot_r: np.ndarray | None = None,
    cot_c: np.ndarray | None = None,
    psi: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fit Cordell-Bouguer forward model strictly on ``valid & train_mask`` and return
    ``(bmr_grad_pullback, bmr_lc_step_nodike, weights)`` across ``valid``."""
    v = np.asarray(valid, dtype=bool)
    tm = v & np.asarray(train_mask, dtype=bool)
    basis = build_bmr_basis(b15_zb, v) if psi is None else psi
    w = fit_bmr_weights(basis, b13_grav, tm)
    g_hat = np.tensordot(w.astype(np.float32), basis, axes=([0], [0])).astype(np.float32)
    res = np.where(v, np.asarray(b13_grav, dtype=np.float32) - g_hat, np.float32(0.0))
    cr = np.zeros_like(res) if cot_r is None else cot_r
    cc = np.zeros_like(res) if cot_c is None else cot_c
    g_pull, lc_pull = extract_bmr_residual_planes(res, b15_zb, cr, cc, v)
    return g_pull, lc_pull, w
