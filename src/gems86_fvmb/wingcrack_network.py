"""H86-2 Fold-Strict Asymmetric Wing-Crack (±22 deg), Step-Over Relay Bridge,
and Antithetic Graben Structural-Permeability Tensor (`12` dynamic channels).

Strict anti-leakage contract:
  - Takes ONLY a boolean `vis_mask` (`visible` faults in a holdout fold or
    counterfactual `sub_visible` in training) plus label-free static physics columns.
  - Every spatial kernel has a strict hollow core (`r >= 3.2 px`) so zero weight
    ever comes from pixels within the 300 m (`3.0 px`) metric cone.
  - Uses `scipy.fft.rfft2` / `irfft2` in pure `float32` (`complex64`, ~49 MB per buffer)
    for < 220 MB RAM and ~4-second execution per visible fault mask.
"""
from __future__ import annotations

import gc
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy import fft as sp_fft
from scipy import ndimage as ndi

WC_CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "h86_features" / "wc12"


WINGCRACK_12_NAMES: List[str] = [
    "wc_collinear_cont_short",
    "wc_collinear_cont_long",
    "wc_wing_lobe_pos22",
    "wc_wing_lobe_neg22",
    "wc_wing_lobe_max",
    "wc_relay_bridge_sym",
    "wc_antithetic_graben_twin",
    "wc_tip_hollow_cone",
    "wc_dist_vis_habitat",
    "wc_coup_wing_fv",
    "wc_coup_relay_spi",
    "wc_coup_cont_scarp",
]
assert len(WINGCRACK_12_NAMES) == 12

N_STRIKE_BINS = 8
N_TIP_DIRS = 16


def _fft_convolve_same_f32(img: np.ndarray, kern: np.ndarray) -> np.ndarray:
    """Pure-float32 2D convolution via `scipy.fft.rfft2` with exact centering."""
    h, w = img.shape
    kh, kw = kern.shape
    fh = sp_fft.next_fast_len(h + kh - 1)
    fw = sp_fft.next_fast_len(w + kw - 1)
    f_img = sp_fft.rfft2(img.astype(np.float32, copy=False), s=(fh, fw), workers=2)
    f_ker = sp_fft.rfft2(kern.astype(np.float32, copy=False), s=(fh, fw), workers=2)
    f_img *= f_ker
    del f_ker
    conv = sp_fft.irfft2(f_img, s=(fh, fw), workers=2)
    del f_img
    r0 = kh // 2
    c0 = kw // 2
    out = conv[r0 : r0 + h, c0 : c0 + w].astype(np.float32, copy=True)
    del conv
    return out


def _make_hollow_strike_kernel(
    theta: float, r_min: float, r_max: float, perp_sigma: float, half: int, one_sided: int = 0
) -> np.ndarray:
    """Create oriented hollow-core kernel (`one_sided`: 0=symmetric, +1=forward, -1=backward)."""
    yy, xx = np.mgrid[-half : half + 1, -half : half + 1].astype(np.float32)
    along = xx * np.cos(theta) + yy * np.sin(theta)
    perp = -xx * np.sin(theta) + yy * np.cos(theta)
    rad = np.hypot(xx, yy)
    mask = (rad >= r_min) & (rad <= r_max)
    if one_sided > 0:
        mask &= along >= r_min * 0.75
    elif one_sided < 0:
        mask &= along <= -r_min * 0.75
    decay = np.exp(-rad / (0.55 * r_max)) * np.exp(-0.5 * (perp / perp_sigma) ** 2)
    k = np.where(mask, decay, 0.0).astype(np.float32)
    s = float(k.sum())
    if s > 1e-8:
        k /= np.float32(s)
    return k


def _make_wing_ray_kernel(psi_out: float, wing_offset_deg: float, half: int = 25) -> np.ndarray:
    """Directed hollow-core wing-crack lobe centered at `psi_out + wing_offset`."""
    yy, xx = np.mgrid[-half : half + 1, -half : half + 1].astype(np.float32)
    rad = np.hypot(xx, yy)
    ang = np.arctan2(yy, xx)
    target = psi_out + np.deg2rad(wing_offset_deg)
    dang = np.arctan2(np.sin(ang - target), np.cos(ang - target))
    # Convolution evaluates sum_u tip(u) * kern(x - u), so x - u points along target!
    mask = (rad >= 3.5) & (rad <= 24.0) & (np.abs(dang) <= np.deg2rad(16.0))
    k = np.where(
        mask,
        np.exp(-rad / 12.0) * np.exp(-0.5 * (dang / np.deg2rad(8.5)) ** 2),
        0.0,
    ).astype(np.float32)
    s = float(k.sum())
    if s > 1e-8:
        k /= np.float32(s)
    return k


def _make_tip_cone_kernel(psi_out: float, half: int = 25) -> np.ndarray:
    yy, xx = np.mgrid[-half : half + 1, -half : half + 1].astype(np.float32)
    rad = np.hypot(xx, yy)
    ang = np.arctan2(yy, xx)
    dang = np.arctan2(np.sin(ang - psi_out), np.cos(ang - psi_out))
    mask = (rad >= 3.5) & (rad <= 24.0) & (np.abs(dang) <= np.deg2rad(32.0))
    k = np.where(
        mask,
        np.exp(-rad / 13.0) * np.exp(-0.5 * (dang / np.deg2rad(16.0)) ** 2),
        0.0,
    ).astype(np.float32)
    s = float(k.sum())
    if s > 1e-8:
        k /= np.float32(s)
    return k


def _make_antithetic_twin_kernel(theta: float, half: int = 19) -> np.ndarray:
    yy, xx = np.mgrid[-half : half + 1, -half : half + 1].astype(np.float32)
    along = xx * np.cos(theta) + yy * np.sin(theta)
    perp = -xx * np.sin(theta) + yy * np.cos(theta)
    aperp = np.abs(perp)
    mask = (aperp >= 5.0) & (aperp <= 18.0) & (np.abs(along) <= 10.0)
    k = np.where(
        mask,
        np.exp(-0.5 * ((aperp - 10.0) / 4.2) ** 2) * np.exp(-0.5 * (along / 5.5) ** 2),
        0.0,
    ).astype(np.float32)
    s = float(k.sum())
    if s > 1e-8:
        k /= np.float32(s)
    return k


def _extract_strike_and_oriented_tips(
    vis_mask: np.ndarray,
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """Classify visible fault pixels into 8 strike bins and extract 16-azimuth outward tips."""
    vis_f = vis_mask.astype(np.float32)
    smooth = ndi.gaussian_filter(vis_f, sigma=1.6, mode="constant")
    gy = ndi.sobel(smooth, axis=0, mode="constant")
    gx = ndi.sobel(smooth, axis=1, mode="constant")
    # Strike is perpendicular to gradient: (-gy, gx)
    strike_ang = np.mod(np.arctan2(gy, gx) + 0.5 * np.pi, np.pi)
    del gy, gx, smooth

    # Weight strands mildly by connected-component length log(1 + L) (Cowie & Scholz 1992)
    comp, n_comp = ndi.label(vis_mask, structure=np.ones((3, 3), dtype=bool))
    sizes = np.bincount(comp.ravel(), minlength=n_comp + 1).astype(np.float32)
    len_wt = np.where(vis_mask, np.log1p(np.minimum(sizes[comp], 400.0)) / np.log1p(80.0), 0.0).astype(np.float32)
    del comp, sizes

    bin_idx = np.floor(strike_ang / np.pi * N_STRIKE_BINS).astype(np.int32) % N_STRIKE_BINS
    del strike_ang
    strike_maps = []
    for b in range(N_STRIKE_BINS):
        m = np.where(vis_mask & (bin_idx == b), len_wt, 0.0).astype(np.float32)
        strike_maps.append(m)
    del bin_idx

    # Oriented fault tips: pixels on vis_mask where local 5x5 centroid points back into the strand,
    # so outward propagation vector points from local fault centroid -> tip pixel!
    nb_count = ndi.convolve(vis_mask.astype(np.int16), np.ones((3, 3), dtype=np.int16), mode="constant") - 1
    # Endpoints have 1..2 neighbors in 3x3 (since rasterized polylines can be 4- or 8-connected)
    yy_k, xx_k = np.mgrid[-4:5, -4:5].astype(np.float32)
    cy = ndi.convolve(vis_f, yy_k, mode="constant")
    cx = ndi.convolve(vis_f, xx_k, mode="constant")
    del vis_f
    # Vector from local strand mass center toward (0,0) is (-cy, -cx) = outward tip tangent!
    cmag = np.hypot(cy, cx)
    is_tip = vis_mask & (nb_count >= 1) & (nb_count <= 2) & (cmag > 1.5)
    psi_out = np.mod(np.arctan2(-cy, -cx), 2.0 * np.pi)
    del nb_count, cy, cx, cmag

    tip_bin = np.floor(psi_out / (2.0 * np.pi) * N_TIP_DIRS).astype(np.int32) % N_TIP_DIRS
    del psi_out
    tip_maps = []
    for d in range(N_TIP_DIRS):
        tm = np.where(is_tip & (tip_bin == d), len_wt, 0.0).astype(np.float32)
        tip_maps.append(tm)
    del is_tip, tip_bin, len_wt
    return strike_maps, tip_maps


def compute_wingcrack12_fp(
    vis_mask: np.ndarray,
    fp: np.ndarray,
    static_mm: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute the 12 fold-strict H86-2 channels on `fp` (`float32`, `(n_fp, 12)`) + `d_vis_fp`."""
    n_fp = int(fp.sum())
    d_vis = ndi.distance_transform_edt(~vis_mask).astype(np.float32)
    d_vis_fp = d_vis[fp]

    mask_sha = hashlib.sha256(np.packbits(np.asarray(vis_mask, dtype=bool))).hexdigest()[:16]
    WC_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_p = WC_CACHE_DIR / f"wc12_{mask_sha}.f16"
    if cache_p.exists() and cache_p.stat().st_size == n_fp * 12 * 2:
        del d_vis
        cached = np.fromfile(cache_p, dtype=np.float16).reshape(n_fp, 12).astype(np.float32)
        return cached, d_vis_fp

    off_collar_grid = (d_vis > 2.0) & fp
    del d_vis

    strike_maps, tip_maps = _extract_strike_and_oriented_tips(vis_mask & fp)
    h, w = fp.shape
    pad_half = 33
    fh = sp_fft.next_fast_len(h + 2 * pad_half)
    fw = sp_fft.next_fast_len(w + 2 * pad_half)

    def pad_kern_to_center(k_small: np.ndarray) -> np.ndarray:
        kh = k_small.shape[0] // 2
        kp = np.zeros((2 * pad_half + 1, 2 * pad_half + 1), dtype=np.float32)
        off = pad_half - kh
        kp[off : off + k_small.shape[0], off : off + k_small.shape[1]] = k_small
        return sp_fft.rfft2(kp, s=(fh, fw), workers=2)

    def crop_irfft(f_acc: np.ndarray) -> np.ndarray:
        conv = sp_fft.irfft2(f_acc, s=(fh, fw), workers=2)
        out_c = conv[pad_half : pad_half + h, pad_half : pad_half + w].astype(np.float32, copy=True)
        del conv
        return out_c

    f_shape = (fh, fw // 2 + 1)
    f_cont_s = np.zeros(f_shape, dtype=np.complex64)
    f_cont_l = np.zeros(f_shape, dtype=np.complex64)
    f_twin = np.zeros(f_shape, dtype=np.complex64)
    relay_sym = np.zeros((h, w), dtype=np.float32)

    for b in range(N_STRIKE_BINS):
        smap = strike_maps[b]
        if not np.any(smap > 0):
            continue
        f_s = sp_fft.rfft2(smap, s=(fh, fw), workers=2)
        theta = (b + 0.5) * np.pi / N_STRIKE_BINS
        f_cont_s += f_s * pad_kern_to_center(
            _make_hollow_strike_kernel(theta, r_min=3.2, r_max=14.0, perp_sigma=1.35, half=15, one_sided=0)
        )
        f_cont_l += f_s * pad_kern_to_center(
            _make_hollow_strike_kernel(theta, r_min=10.0, r_max=32.0, perp_sigma=2.3, half=33, one_sided=0)
        )
        f_twin += f_s * pad_kern_to_center(_make_antithetic_twin_kernel(theta, half=19))
        fwd = np.maximum(
            crop_irfft(
                f_s
                * pad_kern_to_center(
                    _make_hollow_strike_kernel(theta, r_min=3.5, r_max=28.0, perp_sigma=3.8, half=29, one_sided=+1)
                )
            ),
            0.0,
        )
        bwd = np.maximum(
            crop_irfft(
                f_s
                * pad_kern_to_center(
                    _make_hollow_strike_kernel(theta, r_min=3.5, r_max=28.0, perp_sigma=3.8, half=29, one_sided=-1)
                )
            ),
            0.0,
        )
        relay_sym += np.sqrt(fwd * bwd)
        del f_s, fwd, bwd
    del strike_maps

    cont_short = crop_irfft(f_cont_s)
    del f_cont_s
    cont_long = crop_irfft(f_cont_l)
    del f_cont_l
    graben_twin = crop_irfft(f_twin)
    del f_twin
    gc.collect()

    f_wp = np.zeros(f_shape, dtype=np.complex64)
    f_wn = np.zeros(f_shape, dtype=np.complex64)
    f_tc = np.zeros(f_shape, dtype=np.complex64)

    for d in range(N_TIP_DIRS):
        tmap = tip_maps[d]
        if not np.any(tmap > 0):
            continue
        f_t = sp_fft.rfft2(tmap, s=(fh, fw), workers=2)
        psi = (d + 0.5) * 2.0 * np.pi / N_TIP_DIRS
        f_wp += f_t * pad_kern_to_center(_make_wing_ray_kernel(psi, +22.0, half=25))
        f_wn += f_t * pad_kern_to_center(_make_wing_ray_kernel(psi, -22.0, half=25))
        f_tc += f_t * pad_kern_to_center(_make_tip_cone_kernel(psi, half=25))
        del f_t
    del tip_maps

    wing_pos22 = crop_irfft(f_wp)
    del f_wp
    wing_neg22 = crop_irfft(f_wn)
    del f_wn
    tip_cone = crop_irfft(f_tc)
    del f_tc
    gc.collect()

    # Zero inside 3.0 px collar so zero on-catalogue/halo leakage exists anywhere
    for arr in (cont_short, cont_long, wing_pos22, wing_neg22, relay_sym, graben_twin, tip_cone):
        arr[~off_collar_grid] = 0.0

    def norm_pos_fp(arr_2d: np.ndarray) -> np.ndarray:
        v = np.log1p(np.maximum(arr_2d[fp], 0.0) * 120.0).astype(np.float32)
        pos = v[v > 0]
        scale = float(np.percentile(pos[::4], 90.0)) if pos.size > 100 else 1.0
        return np.clip(v / max(scale, 1e-6), 0.0, 6.0).astype(np.float32)

    out = np.zeros((n_fp, 12), dtype=np.float32)
    out[:, 0] = norm_pos_fp(cont_short)
    out[:, 1] = norm_pos_fp(cont_long)
    out[:, 2] = norm_pos_fp(wing_pos22)
    out[:, 3] = norm_pos_fp(wing_neg22)
    out[:, 4] = np.maximum(out[:, 2], out[:, 3])
    out[:, 5] = norm_pos_fp(relay_sym)
    out[:, 6] = norm_pos_fp(graben_twin)
    out[:, 7] = norm_pos_fp(tip_cone)
    del cont_short, cont_long, wing_pos22, wing_neg22, relay_sym, graben_twin, tip_cone

    # Smooth off-catalogue habitat peaking around 1.0 km from visible strands (0 for d <= 2 px)
    out[:, 8] = np.where(
        d_vis_fp > 2.0,
        np.exp(-0.5 * ((d_vis_fp - 10.0) / 13.0) ** 2),
        0.0,
    ).astype(np.float32)

    # Physics x Topology Couplings (indices in static_mm: 39=fv_sibson_breach_index, 28=spi_dip_coupled_conduit, 43=lid_aniso_ridge, 49=dem10_collinear_chain)
    fv_idx = np.maximum(static_mm[:, 39].astype(np.float32) + 0.5, 0.0)
    spi_idx = np.maximum(static_mm[:, 28].astype(np.float32) + 0.5, 0.0)
    scarp_idx = np.maximum(
        np.maximum(static_mm[:, 43].astype(np.float32), static_mm[:, 49].astype(np.float32)) + 0.5,
        0.0,
    )
    out[:, 9] = np.clip(out[:, 4] * fv_idx, 0.0, 10.0)
    out[:, 10] = np.clip(out[:, 5] * spi_idx, 0.0, 10.0)
    out[:, 11] = np.clip(out[:, 0] * scarp_idx, 0.0, 10.0)
    np.nan_to_num(out, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    out.astype(np.float16).tofile(cache_p)
    return out, d_vis_fp
