"""Observability-Weighted Exposure-Deconfounded Eroded-LOQO PU-HGB Specialist,
Nested Leak-Free Continuation Fields, and Prior-Weighted Dual-Regime Fusion
for Lane H86S-DWAD."""

from __future__ import annotations

from dataclasses import dataclass
import gc
import hashlib

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from sklearn.ensemble import HistGradientBoostingClassifier

from .features import DWAD_CONT_NAMES
from .operators import (
    _rank01_mask,
    dilatational_stepover_sharpen,
    prior_weighted_quadrant_blend,
)


@dataclass(frozen=True)
class DWADConfig:
    collar_px: float = 3.0
    neg_buffer_coupled_px: float = 4.5
    neg_buffer_blind_px: float = 7.5
    erode_train_px: int = 12
    observability_gamma: float = 1.25
    n_neg_coupled: int = 175_000
    n_neg_blind: int = 165_000
    hgb_max_depth: int = 4
    hgb_max_iter: int = 140
    hgb_learning_rate: float = 0.055
    hgb_min_samples_leaf: int = 120
    hgb_l2_regularization: float = 8.0
    blind_hgb_weight: float = 0.66
    blind_prior_weight: float = 0.34
    dual_regime_blind_floor_weight: float = 0.52
    quadrant_pooled_blend_alpha: float = 0.62
    tau0_logit: float = -4.52
    beta_logit: float = 1.62
    crest_gain: float = 0.11
    flank_trim: float = 0.08
    seed: int = 862027


def _extract_tips_and_tangents(vis_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Extract segment endpoint coordinates (N, 2) and unit outward tangent vectors (N, 2)."""
    v = np.asarray(vis_mask, dtype=bool)
    if not v.any():
        return np.zeros((0, 2), dtype=np.float32), np.zeros((0, 2), dtype=np.float32)

    lbl, n_comp = ndi.label(v, structure=np.ones((3, 3), dtype=np.int8))
    if n_comp == 0:
        return np.zeros((0, 2), dtype=np.float32), np.zeros((0, 2), dtype=np.float32)

    # Neighbour count in 3x3 window: endpoints/corners have <= 2 visible neighbours
    nb = ndi.convolve(v.astype(np.int16), np.ones((3, 3), dtype=np.int16), mode="constant", cval=0) - 1
    tip_cand = v & (nb <= 2)

    slices = ndi.find_objects(lbl)
    tips_list: list[tuple[float, float]] = []
    tang_list: list[tuple[float, float]] = []
    for cid, sl in enumerate(slices, start=1):
        if sl is None:
            continue
        sub = lbl[sl] == cid
        rr, cc = np.nonzero(sub)
        if rr.size < 3:
            continue
        r_abs = rr.astype(np.float32) + float(sl[0].start)
        c_abs = cc.astype(np.float32) + float(sl[1].start)
        rc_mean = np.array([r_abs.mean(), c_abs.mean()], dtype=np.float32)
        pts = np.stack([r_abs - rc_mean[0], c_abs - rc_mean[1]], axis=1)
        cov = (pts.T @ pts) / float(max(pts.shape[0] - 1, 1))
        eigvals, eigvecs = np.linalg.eigh(cov)
        axis = eigvecs[:, int(np.argmax(eigvals))].astype(np.float32)
        proj = pts @ axis
        for sign in (-1.0, 1.0):
            idx = int(np.argmax(sign * proj))
            tr, tc = float(r_abs[idx]), float(c_abs[idx])
            # Refine outward tangent from local 12-px neighbourhood inside the component
            d2 = (r_abs - tr) ** 2 + (c_abs - tc) ** 2
            near = (d2 > 0.5) & (d2 <= 144.0)
            if int(near.sum()) >= 2:
                dr = tr - float(r_abs[near].mean())
                dc = tc - float(c_abs[near].mean())
                nrm = float(np.hypot(dr, dc))
                if nrm > 1e-4:
                    ur, uc = dr / nrm, dc / nrm
                else:
                    ur, uc = float(sign * axis[0]), float(sign * axis[1])
            else:
                ur, uc = float(sign * axis[0]), float(sign * axis[1])
            tips_list.append((tr, tc))
            tang_list.append((ur, uc))
    if not tips_list:
        rr_t, cc_t = np.nonzero(tip_cand)
        if rr_t.size == 0:
            return np.zeros((0, 2), dtype=np.float32), np.zeros((0, 2), dtype=np.float32)
        pts = np.stack([rr_t, cc_t], axis=1).astype(np.float32)
        return pts, np.zeros_like(pts)
    return np.asarray(tips_list, dtype=np.float32), np.asarray(tang_list, dtype=np.float32)


def compute_dwad_continuation_fields(
    vis_mask: np.ndarray, valid: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Compute 4 fold-visible structural continuation planes + distance ``d_vis``.

    Planes (shape ``(4, H, W)`` float16):
      0. ``dwad_cont_strike_bridge_1p8km``: anisotropic along-strike projection peaking
         at 700-2,000 m ahead of visible fault tips (bridges unmapped range-front/basin gaps).
      1. ``dwad_cont_conjugate_stepover``: +-26 deg Riedel/releasing-stepover off-axis lobes
         peaking at 500-2,200 m (Faulds & Hinz geothermal stepover geometry).
      2. ``dwad_cont_tip_dilation_cone``: forward crack-tip stress decay ``(r0/(d+r0))^0.8``.
      3. ``dwad_cont_far_basin_corridor``: smooth 1.5-4.2 km regional fault-corridor envelope.
    """
    fp = np.asarray(valid, dtype=bool)
    v = np.asarray(vis_mask, dtype=bool) & fp
    H, W = fp.shape
    out = np.zeros((len(DWAD_CONT_NAMES), H, W), dtype=np.float16)
    if not v.any():
        return out, np.full((H, W), 999.0, dtype=np.float32)

    d_vis = ndi.distance_transform_edt(~v).astype(np.float32)
    tips, tangs = _extract_tips_and_tangents(v)

    rr_fp, cc_fp = np.nonzero(fp)
    q_pts = np.stack([rr_fp.astype(np.float32), cc_fp.astype(np.float32)], axis=1)

    if tips.shape[0] >= 2:
        tree = cKDTree(tips)
        k_nn = min(4, tips.shape[0])
        dists, idxs = tree.query(q_pts, k=k_nn, workers=-1)
        if k_nn == 1:
            dists = dists[:, None]
            idxs = idxs[:, None]

        bridge_acc = np.zeros(rr_fp.size, dtype=np.float32)
        step_acc = np.zeros(rr_fp.size, dtype=np.float32)
        cone_acc = np.zeros(rr_fp.size, dtype=np.float32)

        ca26, sa26 = float(np.cos(np.deg2rad(26.0))), float(np.sin(np.deg2rad(26.0)))
        for j in range(k_nn):
            tj = tips[idxs[:, j]]
            uj = tangs[idxs[:, j]]
            dr = q_pts[:, 0] - tj[:, 0]
            dc = q_pts[:, 1] - tj[:, 1]
            dist = np.maximum(dists[:, j].astype(np.float32), 0.5)
            rx = dr / dist
            ry = dc / dist
            cos_fwd = np.maximum(rx * uj[:, 0] + ry * uj[:, 1], 0.0)

            # 1. Strike bridge peaking around 11-18 px (1.1 - 1.8 km), deliberately not hugging 3 px
            radial_bridge = (dist / 13.0) * np.exp(1.0 - dist / 13.0)
            b_val = radial_bridge * (cos_fwd ** 3)
            np.maximum(bridge_acc, b_val, out=bridge_acc)

            # 2. Conjugate +-26 deg Riedel / releasing-stepover lobes (6 - 22 px)
            u_p_r = uj[:, 0] * ca26 - uj[:, 1] * sa26
            u_p_c = uj[:, 0] * sa26 + uj[:, 1] * ca26
            u_m_r = uj[:, 0] * ca26 + uj[:, 1] * sa26
            u_m_c = -uj[:, 0] * sa26 + uj[:, 1] * ca26
            cos_step = np.maximum(
                np.maximum(rx * u_p_r + ry * u_p_c, rx * u_m_r + ry * u_m_c), 0.0
            )
            radial_step = (dist / 11.0) * np.exp(1.0 - dist / 11.0)
            s_val = radial_step * (cos_step ** 4)
            np.maximum(step_acc, s_val, out=step_acc)

            # 3. Crack-tip tensile stress decay cone
            c_val = np.power(8.0 / (dist + 8.0), 0.85) * (0.25 + 0.75 * (cos_fwd ** 2))
            np.maximum(cone_acc, c_val, out=cone_acc)

        p0 = np.zeros((H, W), dtype=np.float32)
        p1 = np.zeros((H, W), dtype=np.float32)
        p2 = np.zeros((H, W), dtype=np.float32)
        p0[rr_fp, cc_fp] = bridge_acc
        p1[rr_fp, cc_fp] = step_acc
        p2[rr_fp, cc_fp] = cone_acc
    else:
        p0 = np.exp(-d_vis / 14.0).astype(np.float32)
        p1 = np.exp(-d_vis / 12.0).astype(np.float32)
        p2 = np.exp(-d_vis / 9.0).astype(np.float32)

    # 4. Smooth 1.5-4.2 km structural corridor envelope (peaks ~18 px off mapped trace)
    p3 = ((d_vis / 18.0) * np.exp(1.0 - d_vis / 18.0)).astype(np.float32)

    for k, plane in enumerate((p0, p1, p2, p3)):
        med = float(np.median(plane[fp]))
        mad = float(np.median(np.abs(plane[fp] - med))) + 1e-5
        z = np.where(fp, np.clip((plane - med) / (1.4826 * mad), -16.0, 16.0), 0.0)
        out[k] = z.astype(np.float16)
    return out, d_vis


def _split_components(vis_mask: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Partition visible 8-connected components into two halves for nested leak-free features."""
    v = np.asarray(vis_mask, dtype=bool)
    lbl, n_comp = ndi.label(v, structure=np.ones((3, 3), dtype=np.int8))
    if n_comp <= 1:
        return v.copy(), v.copy()
    rng = np.random.default_rng(seed)
    perm = rng.permutation(np.arange(1, n_comp + 1))
    half_a = np.zeros(n_comp + 1, dtype=bool)
    half_a[perm[::2]] = True
    mask_a = half_a[lbl]
    mask_b = v & (~mask_a)
    return mask_a, mask_b


def _eroded_train_domain(eval_mask: np.ndarray, valid: np.ndarray, erode_px: int) -> np.ndarray:
    fp = np.asarray(valid, dtype=bool)
    ev = np.asarray(eval_mask, dtype=bool) & fp
    if not ev.any():
        return fp.copy()
    d_ev = ndi.distance_transform_edt(~ev)
    return fp & (~ev) & (d_ev > float(erode_px))


def _sample_pu_dataset(
    X_static: np.ndarray,
    cont_a_on_b: tuple[np.ndarray, np.ndarray] | None,
    vis_a: np.ndarray,
    vis_b: np.ndarray,
    d_vis_full: np.ndarray,
    train_dom: np.ndarray,
    observability: np.ndarray | None,
    *,
    gamma: float,
    neg_buffer_px: float,
    n_neg: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build nested leak-free PU training matrix (X, y, sample_weight).

    When ``cont_a_on_b`` is supplied:
      - Positives inside ``vis_b`` receive continuation fields computed ONLY from ``vis_a``;
      - Positives inside ``vis_a`` receive continuation fields computed ONLY from ``vis_b``;
      - Unlabeled negatives at ``d_vis > neg_buffer_px`` randomly draw from ``cont_a`` or ``cont_b``
        and are weighted by ``observability(x) ** gamma`` (``gamma = 1.25`` in DWAD, ``0.0`` in E3).
    """
    rng = np.random.default_rng(seed)
    pos_a = np.asarray(vis_a, dtype=bool) & train_dom
    pos_b = np.asarray(vis_b, dtype=bool) & train_dom
    ra, ca = np.nonzero(pos_a)
    rb, cb = np.nonzero(pos_b)

    neg_pool = train_dom & (d_vis_full > float(neg_buffer_px))
    rn_all, cn_all = np.nonzero(neg_pool)
    if rn_all.size > int(n_neg):
        sel = rng.choice(rn_all.size, size=int(n_neg), replace=False)
        rn, cn = rn_all[sel], cn_all[sel]
    else:
        rn, cn = rn_all, cn_all

    n_st = X_static.shape[0]
    n_ct = 0 if cont_a_on_b is None else cont_a_on_b[0].shape[0]
    n_tot = ra.size + rb.size + rn.size
    X = np.empty((n_tot, n_st + n_ct), dtype=np.float32)
    y = np.zeros(n_tot, dtype=np.int8)

    n_pos = ra.size + rb.size
    y[:n_pos] = 1
    if ra.size:
        X[: ra.size, :n_st] = X_static[:, ra, ca].T.astype(np.float32)
    if rb.size:
        X[ra.size : n_pos, :n_st] = X_static[:, rb, cb].T.astype(np.float32)
    X[n_pos:, :n_st] = X_static[:, rn, cn].T.astype(np.float32)

    if cont_a_on_b is not None:
        cont_from_a, cont_from_b = cont_a_on_b
        # Positives in A see continuation from B; positives in B see continuation from A!
        if ra.size:
            X[: ra.size, n_st:] = cont_from_b[:, ra, ca].T.astype(np.float32)
        if rb.size:
            X[ra.size : n_pos, n_st:] = cont_from_a[:, rb, cb].T.astype(np.float32)
        use_a = rng.random(rn.size) < 0.5
        idx_a = np.nonzero(use_a)[0]
        idx_b = np.nonzero(~use_a)[0]
        if idx_a.size:
            X[n_pos + idx_a, n_st:] = cont_from_a[:, rn[idx_a], cn[idx_a]].T.astype(np.float32)
        if idx_b.size:
            X[n_pos + idx_b, n_st:] = cont_from_b[:, rn[idx_b], cn[idx_b]].T.astype(np.float32)

    # Sample weights: class-balanced positives vs observability-weighted unlabeled negatives
    w = np.ones(n_tot, dtype=np.float32)
    if observability is not None and gamma > 0.0:
        obs_neg = np.clip(observability[rn, cn].astype(np.float32), 0.10, 1.0)
        w_neg = np.power(obs_neg, float(gamma)).astype(np.float32)
    else:
        w_neg = np.ones(rn.size, dtype=np.float32)
    # Normalize negative sum to 2.2x positive sum so positive/negative logit scale stays consistent
    neg_sum = float(w_neg.sum()) + 1e-6
    w[n_pos:] = w_neg * (2.2 * float(max(n_pos, 1)) / neg_sum)
    return X, y, w


def _predict_domain(
    clf: HistGradientBoostingClassifier,
    X_static: np.ndarray,
    X_cont: np.ndarray | None,
    domain: np.ndarray,
    chunk: int = 350_000,
) -> np.ndarray:
    rr, cc = np.nonzero(domain)
    out = np.zeros(domain.shape, dtype=np.float32)
    if rr.size == 0:
        return out
    n_st = X_static.shape[0]
    n_ct = 0 if X_cont is None else X_cont.shape[0]
    buf_pred = np.empty(rr.size, dtype=np.float32)
    for s in range(0, rr.size, chunk):
        e = min(s + chunk, rr.size)
        rs, cs = rr[s:e], cc[s:e]
        Xm = np.empty((e - s, n_st + n_ct), dtype=np.float32)
        Xm[:, :n_st] = X_static[:, rs, cs].T.astype(np.float32)
        if X_cont is not None:
            Xm[:, n_st:] = X_cont[:, rs, cs].T.astype(np.float32)
        buf_pred[s:e] = clf.predict_proba(Xm)[:, 1].astype(np.float32)
    out[rr, cc] = buf_pred
    return out


def _calibrate_sparse_posterior(
    rank_surface: np.ndarray,
    valid: np.ndarray,
    *,
    tau0: float = -4.52,
    beta: float = 1.62,
) -> np.ndarray:
    """Map [0, 1] rank-calibrated surface to sparse fault occupancy probability in (0, 1)."""
    m = np.asarray(valid, dtype=bool)
    u = np.clip(np.asarray(rank_surface, dtype=np.float32), 1e-5, 1.0 - 1e-5)
    # Inverse-normal-like upper-tail stretch emphasizing top 0.5-3% structural ridges
    z_tail = np.log(u / (1.0 - u))
    logits = np.clip(float(tau0) + float(beta) * np.maximum(z_tail, -3.5), -14.0, 5.0)
    p = 1.0 / (1.0 + np.exp(-logits))
    return np.where(m, p, np.float32(0.0)).astype(np.float32)


def fit_predict_loqo_dwad_surfaces(
    X_dwad: np.ndarray,
    X_abl: np.ndarray,
    L_dwad: np.ndarray,
    observability: np.ndarray,
    dilaterate_b8: np.ndarray,
    regions: list[tuple[str, np.ndarray, np.ndarray]],
    valid: np.ndarray,
    cfg: DWADConfig = DWADConfig(),
) -> dict[str, np.ndarray]:
    """Fit strict 12-px-eroded 4-fold LOQO models across ``regions`` and return
    calibrated probability surfaces for ``E1``, ``E2``, and ``E3``."""
    fp = np.asarray(valid, dtype=bool)
    H, W = fp.shape

    p_coupled_raw = np.zeros((H, W), dtype=np.float32)
    p_blind_raw = np.zeros((H, W), dtype=np.float32)
    p_abl_raw = np.zeros((H, W), dtype=np.float32)
    d_vis_eval = np.zeros((H, W), dtype=np.float32)
    quad_ids = np.full((H, W), -1, dtype=np.int8)

    # Cache continuation tensors per distinct visible mask (4 holdout folds or 1 full deployment mask)
    cont_cache: dict[str, dict[str, object]] = {}
    for _, _, vis_mask in regions:
        vh = hashlib.sha1(np.packbits(np.asarray(vis_mask, dtype=bool).ravel())).hexdigest()
        if vh not in cont_cache:
            vis_a, vis_b = _split_components(vis_mask, seed=cfg.seed + 31 * (len(cont_cache) + 1))
            cont_full, d_vis = compute_dwad_continuation_fields(vis_mask, fp)
            cont_a, _ = compute_dwad_continuation_fields(vis_a, fp)
            cont_b, _ = compute_dwad_continuation_fields(vis_b, fp)
            # Isotropic Euclidean decay for ablation E3
            iso_full = np.exp(-d_vis / 11.0)[None, :, :].astype(np.float16)
            d_a = ndi.distance_transform_edt(~(vis_a & fp)).astype(np.float32)
            d_b = ndi.distance_transform_edt(~(vis_b & fp)).astype(np.float32)
            iso_a = np.exp(-d_a / 11.0)[None, :, :].astype(np.float16)
            iso_b = np.exp(-d_b / 11.0)[None, :, :].astype(np.float16)
            cont_cache[vh] = {
                "vis_a": vis_a,
                "vis_b": vis_b,
                "cont_full": cont_full,
                "cont_a": cont_a,
                "cont_b": cont_b,
                "d_vis": d_vis,
                "iso_full": iso_full,
                "iso_a": iso_a,
                "iso_b": iso_b,
            }

    def _make_hgb(seed_val: int) -> HistGradientBoostingClassifier:
        return HistGradientBoostingClassifier(
            max_depth=cfg.hgb_max_depth,
            max_iter=cfg.hgb_max_iter,
            learning_rate=cfg.hgb_learning_rate,
            min_samples_leaf=cfg.hgb_min_samples_leaf,
            l2_regularization=cfg.hgb_l2_regularization,
            early_stopping=False,
            random_state=seed_val,
        )

    for q_idx, (_, eval_mask, vis_mask) in enumerate(regions):
        ev = np.asarray(eval_mask, dtype=bool) & fp
        quad_ids[ev] = q_idx
        train_dom = _eroded_train_domain(eval_mask, fp, cfg.erode_train_px)
        vh = hashlib.sha1(np.packbits(np.asarray(vis_mask, dtype=bool).ravel())).hexdigest()
        cc = cont_cache[vh]
        d_vis_eval[ev] = cc["d_vis"][ev]

        # 1. Coupled observability-deconfounded DWAD specialist
        Xc, yc, wc = _sample_pu_dataset(
            X_dwad,
            (cc["cont_a"], cc["cont_b"]),
            cc["vis_a"],
            cc["vis_b"],
            cc["d_vis"],
            train_dom,
            observability,
            gamma=cfg.observability_gamma,
            neg_buffer_px=cfg.neg_buffer_coupled_px,
            n_neg=cfg.n_neg_coupled,
            seed=cfg.seed + 101 * (q_idx + 1),
        )
        clf_c1 = _make_hgb(cfg.seed + 211 * (q_idx + 1)).fit(Xc, yc, sample_weight=wc)
        clf_c2 = _make_hgb(cfg.seed + 223 * (q_idx + 1)).fit(Xc, yc, sample_weight=wc)
        del Xc, yc, wc
        p_coupled_raw[ev] = (
            0.5 * _predict_domain(clf_c1, X_dwad, cc["cont_full"], ev)[ev]
            + 0.5 * _predict_domain(clf_c2, X_dwad, cc["cont_full"], ev)[ev]
        )
        del clf_c1, clf_c2

        # 2. Pure zero-catalogue blind observability-deconfounded DWAD specialist
        Xb, yb, wb = _sample_pu_dataset(
            X_dwad,
            None,
            cc["vis_a"],
            cc["vis_b"],
            cc["d_vis"],
            train_dom,
            observability,
            gamma=cfg.observability_gamma,
            neg_buffer_px=cfg.neg_buffer_blind_px,
            n_neg=cfg.n_neg_blind,
            seed=cfg.seed + 307 * (q_idx + 1),
        )
        clf_b1 = _make_hgb(cfg.seed + 401 * (q_idx + 1)).fit(Xb, yb, sample_weight=wb)
        clf_b2 = _make_hgb(cfg.seed + 419 * (q_idx + 1)).fit(Xb, yb, sample_weight=wb)
        del Xb, yb, wb
        p_blind_raw[ev] = (
            0.5 * _predict_domain(clf_b1, X_dwad, None, ev)[ev]
            + 0.5 * _predict_domain(clf_b2, X_dwad, None, ev)[ev]
        )
        del clf_b1, clf_b2

        # 3. Matched unweighted, un-advected point-local + isotropic tip ablation (E3)
        Xa, ya, wa = _sample_pu_dataset(
            X_abl,
            (cc["iso_a"], cc["iso_b"]),
            cc["vis_a"],
            cc["vis_b"],
            cc["d_vis"],
            train_dom,
            None,
            gamma=0.0,
            neg_buffer_px=cfg.neg_buffer_blind_px,
            n_neg=cfg.n_neg_blind,
            seed=cfg.seed + 503 * (q_idx + 1),
        )
        clf_a = _make_hgb(cfg.seed + 601 * (q_idx + 1)).fit(Xa, ya, sample_weight=wa)
        del Xa, ya, wa
        p_abl_raw[ev] = _predict_domain(clf_a, X_abl, cc["iso_full"], ev)[ev]
        del clf_a
        gc.collect()

    del cont_cache
    gc.collect()

    eval_union = (quad_ids >= 0) & fp

    # Prior-weighted quadrant calibration (alpha_pool = 0.62) for E2 and E1
    r_blind_hgb = prior_weighted_quadrant_blend(
        p_blind_raw, eval_union, quad_ids, alpha_pool=cfg.quadrant_pooled_blend_alpha
    )
    r_prior = prior_weighted_quadrant_blend(
        L_dwad, eval_union, quad_ids, alpha_pool=cfg.quadrant_pooled_blend_alpha
    )
    blind_comb = (
        cfg.blind_hgb_weight * r_blind_hgb + cfg.blind_prior_weight * np.power(r_prior, 1.15)
    ).astype(np.float32)
    r_blind_final = prior_weighted_quadrant_blend(
        blind_comb, eval_union, quad_ids, alpha_pool=cfg.quadrant_pooled_blend_alpha
    )
    s_e2 = dilatational_stepover_sharpen(
        _calibrate_sparse_posterior(
            r_blind_final, eval_union, tau0=cfg.tau0_logit, beta=cfg.beta_logit
        ),
        dilaterate_b8,
        eval_union,
        crest_gain=cfg.crest_gain,
        flank_trim=cfg.flank_trim,
    )

    # Dual-regime fusion for E1: blind floor weight >= 0.52 rising in low-observability
    # covered basins and >1 km off catalogue so E1 discovers far-field faults and avoids
    # crowding previous near-tip submissions.
    r_coupled = prior_weighted_quadrant_blend(
        p_coupled_raw, eval_union, quad_ids, alpha_pool=cfg.quadrant_pooled_blend_alpha
    )
    cover = np.clip(1.0 - observability, 0.0, 1.0).astype(np.float32)
    far_ramp = np.clip((d_vis_eval - 7.0) / 14.0, 0.0, 1.0).astype(np.float32)
    w_blind = np.clip(
        cfg.dual_regime_blind_floor_weight + 0.16 * cover + 0.14 * far_ramp, 0.52, 0.84
    ).astype(np.float32)
    e1_comb = ((1.0 - w_blind) * r_coupled + w_blind * r_blind_final).astype(np.float32)
    r_e1_final = prior_weighted_quadrant_blend(
        e1_comb, eval_union, quad_ids, alpha_pool=cfg.quadrant_pooled_blend_alpha
    )
    s_e1 = dilatational_stepover_sharpen(
        _calibrate_sparse_posterior(
            r_e1_final, eval_union, tau0=cfg.tau0_logit, beta=cfg.beta_logit
        ),
        dilaterate_b8,
        eval_union,
        crest_gain=cfg.crest_gain,
        flank_trim=cfg.flank_trim,
    )

    # Ablation E3: equal-share quadrant rank (alpha_pool = 0.0) without stepover sharpening
    r_abl_eq = prior_weighted_quadrant_blend(p_abl_raw, eval_union, quad_ids, alpha_pool=0.0)
    s_e3 = _calibrate_sparse_posterior(
        r_abl_eq, eval_union, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )

    return {
        "E1_surface": s_e1,
        "E2_surface": s_e2,
        "E3_surface": s_e3,
        "p_coupled_raw": p_coupled_raw,
        "p_blind_raw": p_blind_raw,
        "p_abl_raw": p_abl_raw,
        "d_vis_eval": d_vis_eval,
    }
