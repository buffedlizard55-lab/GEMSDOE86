"""H86T-KNDS feature operators and 4-fold eroded LOQO PU model.

All parameters and feature names are frozen in research/H86T_KNDS_PREREGISTRATION.json.
Memory-optimized for <1.2 GB peak RSS on 3.9 GB sandboxes.
"""
from __future__ import annotations

import gc
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

SENTINEL = -3.4028234663852886e38
CHI_SENTINEL = -32000.0
SEED = 20

KNDS_BACKPROJ_FEATURES = (
    "knds_deconfounded_knick",
    "knds_piedmont_hinge_gate",
    "knds_backproj_piedmont",
    "knds_isochi_strike_coh",
)

LOCAL_CHI_FEATURES = (
    "chi_ksn_norm",
    "chi_step_pos",
    "chi_log_area",
    "topo10_slope_aspect_coh",
)

NATIVE_STATIC_FEATURES = (
    "tmi_hg",
    "grav_hg",
    "elev_relief",
    "dem_slope",
    "rtp_tilt_grad",
    "mt_2km_edge",
    "sed_grad",
)

FOLD_VISIBLE_FEATURES = (
    "vis_d_norm",
    "vis_strike_align",
)

NATIVE_BASELINE_FEATURES = NATIVE_STATIC_FEATURES + FOLD_VISIBLE_FEATURES

# HGB trees fit strictly on static (catalogue-free) features so trees cannot
# degenerate onto d_vis == 0 at training positive pixels.
E1_HGB_FEATURES = KNDS_BACKPROJ_FEATURES + LOCAL_CHI_FEATURES + NATIVE_STATIC_FEATURES
E2_HGB_FEATURES = LOCAL_CHI_FEATURES + NATIVE_STATIC_FEATURES
E3_HGB_FEATURES = NATIVE_STATIC_FEATURES

E1_FEATURES = E1_HGB_FEATURES + FOLD_VISIBLE_FEATURES
E2_FEATURES = E2_HGB_FEATURES + FOLD_VISIBLE_FEATURES
E3_FEATURES = E3_HGB_FEATURES + FOLD_VISIBLE_FEATURES
ALL_FEATURE_NAMES = E1_FEATURES


def clean(band: np.ndarray, fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(band, dtype=np.float32)
    ok = fp & np.isfinite(a) & (a > SENTINEL * 0.5)
    return np.where(ok, a, 0.0).astype(np.float32), ok


def rank01(values: np.ndarray, ok: np.ndarray) -> np.ndarray:
    out = np.zeros(values.shape, np.float32)
    v = values[ok]
    if v.size == 0:
        return out
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(v.size, np.float32)
    ranks[order] = np.arange(v.size, dtype=np.float32)
    out[ok] = ranks / max(v.size - 1, 1)
    return out


def rank01_per_quadrant(values: np.ndarray, fp: np.ndarray, test_quads: list[np.ndarray]) -> np.ndarray:
    """Rank-normalize within each spatial quadrant so no quadrant is starved by base-rate shifts."""
    out = np.zeros(values.shape, dtype=np.float32)
    for qm in test_quads:
        if np.any(qm):
            out[qm] = rank01(values, qm)[qm]
    return out


def _grad2d_f32(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute float32 central differences without allocating float64 intermediates."""
    gy = np.empty_like(a, dtype=np.float32)
    gx = np.empty_like(a, dtype=np.float32)
    gy[1:-1, :] = 0.5 * (a[2:, :] - a[:-2, :])
    gy[0, :] = a[1, :] - a[0, :]
    gy[-1, :] = a[-1, :] - a[-2, :]
    gx[:, 1:-1] = 0.5 * (a[:, 2:] - a[:, :-2])
    gx[:, 0] = a[:, 1] - a[:, 0]
    gx[:, -1] = a[:, -1] - a[:, -2]
    return gy, gx


def _gradmag(a: np.ndarray) -> np.ndarray:
    gy, gx = _grad2d_f32(a)
    return np.hypot(gx, gy)


def _sample_shifted(arr: np.ndarray, dy: np.ndarray, dx: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Sample 2D array at integer-rounded offsets (y + dy, x + dx) clamped to grid."""
    h, w = arr.shape
    ys = np.clip(
        np.arange(h, dtype=np.int32)[:, None] + np.rint(dy).astype(np.int32),
        0,
        h - 1,
    )
    xs = np.clip(
        np.arange(w, dtype=np.int32)[None, :] + np.rint(dx).astype(np.int32),
        0,
        w - 1,
    )
    sampled = arr[ys, xs]
    valid = fp & fp[ys, xs]
    return np.where(valid, sampled, 0.0).astype(np.float32)


def build_static_knds_stack(
    read_band,
    fp: np.ndarray,
    chi_tif: Path,
    topo10_tif: Path,
) -> dict[str, np.ndarray]:
    """Build the static (catalogue-free) planes for H86T-KNDS with bounded memory."""
    planes: dict[str, np.ndarray] = {}

    b3, _ = clean(read_band(3), fp)
    planes["tmi_hg"] = rank01(np.abs(b3), fp)
    del b3

    b18, _ = clean(read_band(18), fp)
    planes["grav_hg"] = rank01(np.abs(b18), fp)
    del b18

    b5, _ = clean(read_band(5), fp)
    planes["elev_relief"] = rank01(b5, fp)
    del b5

    b19, _ = clean(read_band(19), fp)
    planes["dem_slope"] = rank01(b19, fp)
    del b19

    b2, _ = clean(read_band(2), fp)
    rtp_sm = ndi.gaussian_filter(b2, 1.5, mode="nearest")
    del b2
    planes["rtp_tilt_grad"] = rank01(_gradmag(rtp_sm), fp)
    del rtp_sm

    b16, _ = clean(read_band(16), fp)
    mt_sm = ndi.gaussian_filter(np.log10(np.clip(b16, 1.0, 1e6)), 1.5, mode="nearest")
    del b16
    planes["mt_2km_edge"] = rank01(_gradmag(mt_sm), fp)
    del mt_sm

    b15, _ = clean(read_band(15), fp)
    zb = np.clip(b15, 0.0, 10000.0)
    del b15
    zb_sm = ndi.gaussian_filter(zb, 1.5, mode="nearest")
    planes["sed_grad"] = rank01(_gradmag(zb_sm), fp)
    del zb_sm

    geophys_edge = (
        0.40 * planes["grav_hg"]
        + 0.35 * planes["tmi_hg"]
        + 0.25 * planes["sed_grad"]
    ).astype(np.float32)
    geophys_sm = ndi.gaussian_filter(geophys_edge, 2.0, mode="nearest")
    del geophys_edge
    ggy, ggx = _grad2d_f32(geophys_sm)
    del geophys_sm
    planes["_geophys_theta"] = np.arctan2(-ggy, ggx).astype(np.float32)
    del ggy, ggx

    planes["_multiline_geophys"] = rank01(
        0.25 * planes["tmi_hg"]
        + 0.25 * planes["grav_hg"]
        + 0.20 * planes["sed_grad"]
        + 0.15 * planes["rtp_tilt_grad"]
        + 0.15 * planes["mt_2km_edge"],
        fp,
    )

    # 2. External 10 m DEM fluvial chi stack (dem10_chi_100m_i16.tif)
    with rasterio.open(chi_tif) as src:
        b1_step_max = src.read(1).astype(np.float32)
        b2_step_min = src.read(2).astype(np.float32)
        b3_ksn = src.read(3).astype(np.float32)
        b4_log_area = src.read(4).astype(np.float32)
        b5_zmean = src.read(5).astype(np.float32)

    valid_chi = fp & (b3_ksn > CHI_SENTINEL) & (b4_log_area > CHI_SENTINEL) & (b5_zmean > CHI_SENTINEL)
    ksn = np.where(valid_chi & (b3_ksn > 0), b3_ksn, 0.0).astype(np.float32)
    step_max = np.where(valid_chi & (b1_step_max > CHI_SENTINEL), b1_step_max * 1e-3, 0.0).astype(np.float32)
    step_min = np.where(valid_chi & (b2_step_min > CHI_SENTINEL), b2_step_min * 1e-3, 0.0).astype(np.float32)
    log_area = np.where(valid_chi, b4_log_area * 1e-3, 0.0).astype(np.float32)
    z_med = float(np.median(b5_zmean[valid_chi])) if np.any(valid_chi) else 1500.0
    zmean = np.where(valid_chi, b5_zmean, z_med).astype(np.float32)
    del b1_step_max, b2_step_min, b3_ksn, b4_log_area, b5_zmean, valid_chi

    chi_step_diff = np.maximum(0.0, step_max - step_min)
    del step_max, step_min
    planes["chi_ksn_norm"] = rank01(np.log1p(ksn), fp)
    del ksn
    planes["chi_step_pos"] = rank01(chi_step_diff, fp)
    del chi_step_diff
    planes["chi_log_area"] = rank01(np.clip(log_area, 3.0, 9.5), fp)

    # 3. External 10 m DEM derived morphometrics (topo_10m_derived_100m_u8.tif)
    with rasterio.open(topo10_tif) as src:
        t10_slope = src.read(1).astype(np.float32) / 255.0
        t10_aspect_coh = src.read(7).astype(np.float32) / 255.0
    planes["topo10_slope_aspect_coh"] = rank01(t10_slope * t10_aspect_coh, fp)
    del t10_slope, t10_aspect_coh

    # 4. H86T-KNDS Plane 1: Footwall Deconfounded Knickzone Intensity
    drainage_gate = np.clip((log_area - 3.5) / 1.5, 0.0, 1.0).astype(np.float32)
    knick_raw = planes["chi_ksn_norm"] * (0.50 + 0.50 * planes["chi_step_pos"]) * drainage_gate
    del drainage_gate

    lahontan_band = np.exp(-0.5 * ((zmean - 1335.0) / 18.0) ** 2).astype(np.float32)
    small_catchment = np.clip((4.8 - log_area) / 1.0, 0.0, 1.0).astype(np.float32)
    w_lahontan = 1.0 - 0.65 * lahontan_band * small_catchment
    del lahontan_band, small_catchment

    b12, _ = clean(read_band(12), fp)
    g12_sm = ndi.gaussian_filter(b12, 2.0, mode="nearest")
    del b12
    g12_lap = ndi.laplace(g12_sm).astype(np.float32)
    del g12_sm
    sill_sym = rank01(np.maximum(0.0, -g12_lap), fp) * (1.0 - planes["grav_hg"])
    del g12_lap
    w_sill = 1.0 - 0.40 * sill_sym
    del sill_sym

    knick_deconf = ndi.gaussian_filter(knick_raw * w_lahontan * w_sill, 1.2, mode="nearest")
    del knick_raw, w_lahontan, w_sill
    planes["knds_deconfounded_knick"] = rank01(knick_deconf, fp)
    del knick_deconf

    # 5. H86T-KNDS Plane 2: Piedmont Apron & Subsurface Basement-Hinge Reception Gate
    log_zb = np.log(np.clip(zb, 10.0, 10000.0))
    del zb
    depth_window = np.exp(-0.5 * ((log_zb - np.log(220.0)) / 1.15) ** 2).astype(np.float32)
    del log_zb
    hinge_step = np.sqrt(planes["grav_hg"] * planes["sed_grad"])
    piedmont_gate = depth_window * (0.35 + 0.65 * hinge_step)
    del depth_window, hinge_step
    planes["knds_piedmont_hinge_gate"] = rank01(piedmont_gate, fp)
    del piedmont_gate

    # 6. H86T-KNDS Plane 3: Drainage-Area-Scaled Downslope Knickzone Back-Projection
    z_smooth = ndi.gaussian_filter(zmean, 4.0, mode="nearest")
    del zmean
    zy, zx = _grad2d_f32(z_smooth)
    del z_smooth
    znorm = np.hypot(zy, zx) + 1e-3
    up_y = (zy / znorm).astype(np.float32)
    up_x = (zx / znorm).astype(np.float32)
    del zy, zx, znorm

    backproj_acc = np.zeros(fp.shape, dtype=np.float32)
    shift_specs = (
        (4.0, 4.0, 0.75),
        (8.0, 4.7, 0.85),
        (14.0, 5.5, 0.95),
        (22.0, 6.3, 1.05),
    )
    knick_src = planes["knds_deconfounded_knick"]
    for s_px, target_log_a, sigma_a in shift_specs:
        k_up = _sample_shifted(knick_src, s_px * up_y, s_px * up_x, fp)
        a_up = _sample_shifted(log_area, s_px * up_y, s_px * up_x, fp)
        w_area = np.exp(-0.5 * ((a_up - target_log_a) / sigma_a) ** 2).astype(np.float32)
        backproj_acc += k_up * (0.35 + 0.65 * w_area)
        del k_up, a_up, w_area
    del log_area

    backproj_gated = ndi.gaussian_filter(
        (backproj_acc / len(shift_specs)) * (0.30 + 0.70 * planes["knds_piedmont_hinge_gate"]),
        1.5,
        mode="nearest",
    )
    del backproj_acc
    planes["knds_backproj_piedmont"] = rank01(backproj_gated, fp)
    del backproj_gated

    # 7. H86T-KNDS Plane 4: Cross-Drainage Along-Strike Iso-Chi Knickzone Coherence
    t_y = -up_x
    t_x = up_y
    del up_y, up_x
    bp = planes["knds_backproj_piedmont"]
    strike_neighbors = np.zeros(fp.shape, dtype=np.float32)
    for d_strike in (4.0, 8.0, 12.0):
        p_plus = _sample_shifted(bp, d_strike * t_y, d_strike * t_x, fp)
        p_minus = _sample_shifted(bp, -d_strike * t_y, -d_strike * t_x, fp)
        strike_neighbors += 0.5 * (p_plus + p_minus)
        del p_plus, p_minus
    del t_y, t_x
    strike_neighbors /= 3.0
    isochi_coh = np.sqrt(bp * strike_neighbors) * (0.50 + 0.50 * planes["topo10_slope_aspect_coh"])
    del strike_neighbors
    planes["knds_isochi_strike_coh"] = rank01(ndi.gaussian_filter(isochi_coh, 1.2, mode="nearest"), fp)
    del isochi_coh
    gc.collect()
    return planes


def build_fold_visible_features(
    visible_faults: np.ndarray,
    fp: np.ndarray,
    geophys_theta: np.ndarray,
) -> dict[str, np.ndarray]:
    """Derive catalogue features strictly from visible_faults (never withheld faults)."""
    vis = visible_faults & fp
    d_vis = ndi.distance_transform_edt(~vis).astype(np.float32)
    # Near-collar relay envelope (decays over 6.5 px = 650 m outside 3 px collar)
    # plus far-field basal floor so >1 km off-catalogue structures also receive dots.
    relay_near = np.exp(-np.clip(d_vis - 3.0, 0.0, 60.0) / 6.5).astype(np.float32)
    vis_d_norm = rank01(relay_near, fp)

    vis_sm = ndi.gaussian_filter(vis.astype(np.float32), 5.0, mode="nearest")
    vy, vx = _grad2d_f32(vis_sm)
    del vis_sm
    v_mag = np.hypot(vy, vx)
    vis_theta = np.arctan2(-vy, vx).astype(np.float32)
    del vy, vx
    cos2 = np.cos(vis_theta - geophys_theta) ** 2
    del vis_theta
    p85 = float(np.percentile(v_mag[fp], 85)) + 1e-6
    strike_gate = np.clip(v_mag / p85, 0.0, 1.0)
    del v_mag
    vis_strike_align = rank01((cos2 * (0.25 + 0.75 * strike_gate)).astype(np.float32), fp)
    del cos2, strike_gate
    gc.collect()
    return {
        "vis_d_norm": vis_d_norm,
        "vis_strike_align": vis_strike_align,
        "_relay_near": relay_near,
        "_d_vis": d_vis,
    }


def _quadrant_splits(fp: np.ndarray, buffer_px: int = 12) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """4 spatial quadrants around footprint median with a 12-px eroded training seam buffer."""
    ys, xs = np.nonzero(fp)
    ym = int(np.median(ys))
    xm = int(np.median(xs))
    del ys, xs
    h, w = fp.shape
    yy = np.arange(h, dtype=np.int32)[:, None]
    xx = np.arange(w, dtype=np.int32)[None, :]
    test_quads = [
        fp & (yy < ym) & (xx < xm),
        fp & (yy < ym) & (xx >= xm),
        fp & (yy >= ym) & (xx < xm),
        fp & (yy >= ym) & (xx >= xm),
    ]
    train_quads = [
        fp & ~((yy < ym + buffer_px) & (xx < xm + buffer_px)),
        fp & ~((yy < ym + buffer_px) & (xx >= xm - buffer_px)),
        fp & ~((yy >= ym - buffer_px) & (xx < xm + buffer_px)),
        fp & ~((yy >= ym - buffer_px) & (xx >= xm - buffer_px)),
    ]
    return train_quads, test_quads


def _physical_prior(planes: dict[str, np.ndarray], arm_id: str, fp: np.ndarray) -> np.ndarray:
    if arm_id == "E1":
        raw = (
            0.35 * planes["knds_isochi_strike_coh"]
            + 0.30 * planes["knds_backproj_piedmont"]
            + 0.20 * planes["knds_piedmont_hinge_gate"]
            + 0.15 * planes["_multiline_geophys"]
        )
    elif arm_id == "E2":
        raw = (
            0.45 * planes["chi_ksn_norm"]
            + 0.25 * planes["chi_step_pos"]
            + 0.15 * planes["topo10_slope_aspect_coh"]
            + 0.15 * planes["_multiline_geophys"]
        )
    elif arm_id == "E3":
        raw = planes["_multiline_geophys"]
    else:
        raise ValueError(f"Unknown arm_id: {arm_id}")
    return rank01(raw, fp)


def fit_predict_loqo_arm(
    planes: dict[str, np.ndarray],
    feature_names: tuple[str, ...],
    visible_faults: np.ndarray,
    fp: np.ndarray,
    arm_id: str,
    n_neg_per_fold: int = 30_000,
) -> np.ndarray:
    """4-fold 12-px eroded LOQO HGB PU (on static features) + quadrant-balanced physical prior."""
    static_names = tuple(
        n for n in feature_names if n not in FOLD_VISIBLE_FEATURES
    )
    train_quads, test_quads = _quadrant_splits(fp, buffer_px=12)
    vis_pos = visible_faults & fp
    dilated_vis = ndi.binary_dilation(vis_pos, iterations=3)
    neg_eligible = fp & ~dilated_vis

    oof_proba = np.zeros(fp.shape, dtype=np.float32)

    for q_idx, (tr_mask, te_mask) in enumerate(zip(train_quads, test_quads)):
        rng = np.random.default_rng(SEED + q_idx)
        pos_grid_idx = np.flatnonzero((vis_pos & tr_mask).ravel())
        neg_pool_idx = np.flatnonzero((neg_eligible & tr_mask).ravel())
        neg_grid_idx = rng.choice(
            neg_pool_idx, size=min(n_neg_per_fold, neg_pool_idx.size), replace=False
        )
        sample_idx = np.r_[pos_grid_idx, neg_grid_idx]
        X_tr = np.column_stack(
            [planes[name].ravel()[sample_idx] for name in static_names]
        ).astype(np.float32)
        y_tr = np.r_[np.ones(pos_grid_idx.size, np.int8), np.zeros(neg_grid_idx.size, np.int8)]

        med = np.median(X_tr, axis=0).astype(np.float32)
        q25, q75 = np.percentile(X_tr, [25, 75], axis=0)
        iqr = np.where((q75 - q25) > 1e-6, q75 - q25, 1.0).astype(np.float32)
        X_tr -= med
        X_tr /= iqr

        clf = HistGradientBoostingClassifier(
            max_iter=60,
            learning_rate=0.08,
            max_leaf_nodes=31,
            min_samples_leaf=50,
            l2_regularization=0.2,
            random_state=SEED + q_idx,
        )
        clf.fit(X_tr, y_tr)
        del X_tr, y_tr

        te_grid_idx = np.flatnonzero(te_mask.ravel())
        chunk_size = 350_000
        for s in range(0, te_grid_idx.size, chunk_size):
            c_idx = te_grid_idx[s : s + chunk_size]
            X_te = np.column_stack(
                [planes[name].ravel()[c_idx] for name in static_names]
            ).astype(np.float32)
            X_te -= med
            X_te /= iqr
            oof_proba.ravel()[c_idx] = clf.predict_proba(X_te)[:, 1].astype(np.float32)
            del X_te

    # Rank-normalize per quadrant so base-rate differences never starve NE/NW
    loqo_q_rank = rank01_per_quadrant(oof_proba, fp, test_quads)
    del oof_proba
    phys_q_rank = rank01_per_quadrant(_physical_prior(planes, arm_id, fp), fp, test_quads)
    relay_env = planes["_relay_near"] * (0.45 + 0.55 * planes["vis_strike_align"])
    coupled_score = 0.56 * loqo_q_rank + 0.34 * phys_q_rank + 0.10 * relay_env
    del loqo_q_rank, phys_q_rank, relay_env
    gc.collect()
    return rank01_per_quadrant(coupled_score, fp, test_quads)
