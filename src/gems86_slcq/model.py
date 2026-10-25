"""Strict 4-Quadrant Eroded-Domain Leave-One-Quadrant-Out (LOQO) 5-Fold (80/20
Hide-Matched) PU Specialists with Fold-Safe Out-of-Quadrant BMR Residuals and
Cover-Conditioned Noisy-OR Fusion for Lane H86M-SLCQ.

Crucial spatial-seam fix (IR-86M-STDP-QUAD-SEAM):
  Uses ``gems57.holdout.quadrant_ids(footprint)`` (splitting at the footprint
  median row/col, ym=936, xm=1504 on GEMS) rather than bounding-box ``(H//2, W//2)``
  (1865, 1646), and erodes each training domain ``quad != q`` by ``DOMAIN_ERODE=12``
  pixels (1.2 km), creating a 2.4 km spatial dead-zone between training labels/BMR
  fits and the scored quadrant region.
"""

from __future__ import annotations

from dataclasses import dataclass
import gc
from pathlib import Path
import sys

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

VENDOR = Path(__file__).resolve().parents[2] / "vendor"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from gems57.holdout import DOMAIN_ERODE, quadrant_ids
from src.gems86_ewcs.features import compute_elastic_fields
from .features import BMR_FOLD_NAMES, ELASTIC_NAMES
from .operators import extract_bmr_residual_planes, fit_bmr_weights


@dataclass(frozen=True)
class SLCQConfig:
    collar_px: float = 3.0
    blind_neg_buffer_px: float = 8.0
    domain_erode_px: int = DOMAIN_ERODE
    n_neg_blind: int = 160_000
    n_neg_kin: int = 210_000
    n_comp_splits: int = 5
    learning_rate: float = 0.055
    tau0_logit: float = -4.55
    beta_logit: float = 1.68
    blind_hgb_weight: float = 0.64
    blind_corrob_weight: float = 0.36
    alpha_blind_min: float = 0.24
    alpha_blind_max: float = 0.58
    alpha_kin: float = 0.76
    seed: int = 861325


def true_footprint_quadrants(valid: np.ndarray) -> np.ndarray:
    """Return exact ``gems57.holdout.quadrant_ids(valid)`` {-1, 0, 1, 2, 3}."""
    return quadrant_ids(np.asarray(valid, dtype=bool))


def calibrate_footprint_quadrant_posterior(
    raw_prob: np.ndarray,
    valid: np.ndarray,
    quad: np.ndarray | None = None,
    *,
    tau0: float = -4.55,
    beta: float = 1.68,
) -> np.ndarray:
    """Calibrate out-of-quadrant raw probabilities into a quadrant-balanced sparse
    posterior in (0, 1) using ONLY unlabelled score quantiles within each true
    footprint quadrant {0, 1, 2, 3}."""
    fp = np.asarray(valid, dtype=bool)
    q_grid = true_footprint_quadrants(fp) if quad is None else np.asarray(quad, dtype=np.int8)
    out = np.zeros(fp.shape, dtype=np.float32)

    for q in range(4):
        qm = fp & (q_grid == q)
        if not qm.any():
            continue
        p = np.clip(raw_prob[qm].astype(np.float64), 1e-6, 1.0 - 1e-6)
        ell = np.log(p / (1.0 - p))
        med = float(np.median(ell))
        p90 = float(np.percentile(ell, 90.0))
        scale = max(p90 - med, 1e-4)
        z = np.clip((ell - med) / scale, -6.0, 8.0)
        logits = float(tau0) + float(beta) * z
        out[qm] = (1.0 / (1.0 + np.exp(-logits))).astype(np.float32)
    return out


def _robust_norm(arr: np.ndarray, valid: np.ndarray) -> np.ndarray:
    v = np.asarray(valid, dtype=bool)
    vals = arr[v]
    if vals.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    med = float(np.median(vals))
    q75, q25 = np.percentile(vals, [75.0, 25.0])
    scale = float(max((q75 - q25) * 0.7413, np.std(vals) * 0.5, 1e-6))
    z = (arr.astype(np.float32) - med) / scale
    return np.where(v, np.clip(z, -8.0, 12.0), np.float32(0.0)).astype(np.float32)


def compute_fold_bmr_planes(
    psi_bmr: np.ndarray,
    b13_grav: np.ndarray,
    b15_zb: np.ndarray,
    cot_r: np.ndarray,
    cot_c: np.ndarray,
    valid: np.ndarray,
    train_mask: np.ndarray,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Fit Cordell-Bouguer forward gravity model strictly on ``valid & train_mask``
    (zero target-quadrant B13 bytes) and return normalized BMR residual step planes."""
    v = np.asarray(valid, dtype=bool)
    tm = v & np.asarray(train_mask, dtype=bool)
    w = fit_bmr_weights(psi_bmr, b13_grav, tm)
    g_hat = np.tensordot(w.astype(np.float32), psi_bmr, axes=([0], [0])).astype(np.float32)
    res = np.where(v, np.asarray(b13_grav, dtype=np.float32) - g_hat, np.float32(0.0))
    g_pull, lc_pull = extract_bmr_residual_planes(res, b15_zb, cot_r, cot_c, v)
    planes = {
        "bmr_grad_adaptive_pullback": _robust_norm(g_pull, v),
        "bmr_lc_step_nodike": _robust_norm(lc_pull, v),
    }
    return planes, w


def partition_visible_components_k(
    vis_cat: np.ndarray, n_splits: int, seed: int
) -> list[np.ndarray]:
    """Partition 8-connected components of ``vis_cat`` into ``n_splits`` disjoint masks."""
    k = max(int(n_splits), 2)
    comp, n_comp = ndi.label(vis_cat, structure=np.ones((3, 3), dtype=int))
    if n_comp < k:
        H = vis_cat.shape[0]
        out: list[np.ndarray] = []
        edges = np.linspace(0, H, k + 1, dtype=int)
        for i in range(k):
            m = np.zeros_like(vis_cat, dtype=bool)
            m[edges[i] : edges[i + 1], :] = vis_cat[edges[i] : edges[i + 1], :]
            out.append(m)
        return out
    rng = np.random.default_rng(seed)
    perm = rng.permutation(np.arange(1, n_comp + 1))
    out = []
    for i in range(k):
        lut = np.zeros(n_comp + 1, dtype=bool)
        lut[perm[i::k]] = True
        out.append(lut[comp])
    return out


def _extract_rows(
    X_static: np.ndarray,
    flat_idx: np.ndarray,
    extra_planes: dict[str, np.ndarray] | None = None,
    extra_keys: tuple[str, ...] = (),
) -> np.ndarray:
    n_s, _, W = X_static.shape
    ys, xs = np.divmod(flat_idx, W)
    n_e = len(extra_keys) if extra_planes is not None else 0
    out = np.empty((flat_idx.size, n_s + n_e), dtype=np.float32)
    out[:, :n_s] = X_static[:, ys, xs].T.astype(np.float32)
    if n_e and extra_planes is not None:
        for j, k in enumerate(extra_keys):
            out[:, n_s + j] = extra_planes[k][ys, xs].astype(np.float32)
    return out


def _predict_chunked(
    clfs: tuple[HistGradientBoostingClassifier, ...],
    weights: tuple[float, ...],
    X_static: np.ndarray,
    extra_planes: dict[str, np.ndarray] | None,
    extra_keys: tuple[str, ...],
    mask: np.ndarray,
    chunk_rows: int = 256,
) -> np.ndarray:
    H, W = mask.shape
    n_s = X_static.shape[0]
    n_e = len(extra_keys) if extra_planes is not None else 0
    out = np.zeros((H, W), dtype=np.float32)

    for r0 in range(0, H, chunk_rows):
        r1 = min(H, r0 + chunk_rows)
        m = mask[r0:r1]
        if not m.any():
            continue
        ys, xs = np.nonzero(m)
        X_chunk = np.empty((ys.size, n_s + n_e), dtype=np.float32)
        X_chunk[:, :n_s] = X_static[:, r0 + ys, xs].T.astype(np.float32)
        if n_e and extra_planes is not None:
            for j, k in enumerate(extra_keys):
                X_chunk[:, n_s + j] = extra_planes[k][r0 + ys, xs].astype(np.float32)
        prob = np.zeros(ys.size, dtype=np.float32)
        for clf, w in zip(clfs, weights):
            prob += np.float32(w) * clf.predict_proba(X_chunk)[:, 1].astype(np.float32)
        sub = out[r0:r1]
        sub[ys, xs] = prob
    return out


def _make_hgb(
    *,
    max_iter: int,
    learning_rate: float,
    max_leaf_nodes: int,
    min_samples_leaf: int,
    l2_regularization: float,
    seed: int,
) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=max_iter,
        learning_rate=learning_rate,
        max_leaf_nodes=max_leaf_nodes,
        min_samples_leaf=min_samples_leaf,
        l2_regularization=l2_regularization,
        early_stopping=False,
        random_state=seed,
    )


def fuse_cover_conditioned_noisy_or(
    p_blind: np.ndarray,
    p_kin: np.ndarray,
    cover_propensity: np.ndarray,
    valid: np.ndarray,
    *,
    alpha_blind_min: float = 0.24,
    alpha_blind_max: float = 0.58,
    alpha_kin: float = 0.76,
) -> np.ndarray:
    """Cover-conditioned Noisy-OR fusion."""
    fp = np.asarray(valid, dtype=bool)
    pb = np.clip(np.asarray(p_blind, dtype=np.float32), 0.0, 1.0)
    pk = np.clip(np.asarray(p_kin, dtype=np.float32), 0.0, 1.0)
    cc = np.clip(np.asarray(cover_propensity, dtype=np.float32), 0.0, 1.0)
    w_blind = float(alpha_blind_min) + float(alpha_blind_max - alpha_blind_min) * cc
    fused = 1.0 - (1.0 - w_blind * pb) * (1.0 - float(alpha_kin) * pk)
    return np.where(fp, np.clip(fused, 0.0, 1.0), np.float32(0.0)).astype(np.float32)


def fit_predict_oof_slcq(
    stack: dict[str, object],
    vis_cat: np.ndarray,
    cfg: SLCQConfig,
    *,
    precomputed_elastic: dict[str, np.ndarray] | None = None,
    seed_base_offset: int = 0,
) -> dict[str, object]:
    """Assemble strict 4-quadrant out-of-fold (LOQO) surfaces across ``valid``.

    Key efficiency + rigor property:
      - Precomputes the ``K = 5`` (80% visible / 20% held-out) disjoint whole-component
        elastic fields ONCE on ``vis_cat``, then inside each quadrant ``q in {0, 1, 2, 3}``
        extracts ONLY training rows inside the eroded outer domain
        ``train_dom_q = erosion((quad >= 0) & (quad != q), 12 px) & fp`` and fits
        ``BMR`` weights strictly on ``train_dom_q``!
      - Every pixel in quadrant ``q`` is predicted strictly out-of-quadrant (minimum
        2.4 km separation between training pixels and ``folds[q]['region']``), and all
        4 quadrants are out-of-fold simultaneously so global 37,654-dot allocation has
        zero in-sample vs out-of-sample quadrant distortion!
    """
    fp = np.asarray(stack["valid"], dtype=bool)
    quad = true_footprint_quadrants(fp)
    vis_full = np.asarray(vis_cat, dtype=bool) & fp
    el_eval = (
        precomputed_elastic
        if precomputed_elastic is not None
        else compute_elastic_fields(vis_full, fp)
    )

    # Precompute 5-fold (80/20 hide-matched) component elastic fields ONCE for vis_full,
    # caching ONLY the sampled training rows per quadrant so peak RAM stays tiny!
    d_vis = ndi.distance_transform_edt(~vis_full)
    k_splits = max(int(cfg.n_comp_splits), 2)
    comp_masks = partition_visible_components_k(
        vis_full, k_splits, seed=cfg.seed + seed_base_offset + 5
    )

    train_doms = [
        (
            ndi.binary_erosion((quad >= 0) & (quad != q), iterations=int(cfg.domain_erode_px))
            & fp
            if cfg.domain_erode_px > 0
            else (quad >= 0) & (quad != q) & fp
        )
        for q in range(4)
    ]

    # Fit out-of-quadrant BMR planes for all 4 quadrants first (very fast, 6x6 ridge solve)
    bmr_by_q: list[dict[str, np.ndarray]] = []
    bmr_weights_by_q: list[list[float]] = []
    bmr_oof = {k: np.zeros(fp.shape, dtype=np.float32) for k in BMR_FOLD_NAMES}
    for q in range(4):
        q_mask = fp & (quad == q)
        bmr_q, w_q = compute_fold_bmr_planes(
            stack["psi_bmr"],
            stack["b13_grav"],
            stack["b15_zb"],
            stack["cot_r"],
            stack["cot_c"],
            fp,
            train_doms[q],
        )
        bmr_by_q.append(bmr_q)
        bmr_weights_by_q.append([round(float(v), 6) for v in w_q])
        for k in BMR_FOLD_NAMES:
            bmr_oof[k][q_mask] = bmr_q[k][q_mask]

    # Sample negative pools per outer quadrant for 5-fold (80/20) kinematic PU & 2-fold E3
    neg_k_by_q: list[np.ndarray] = []
    for q in range(4):
        rng_q = np.random.default_rng(cfg.seed + seed_base_offset + 50 + q)
        pool = np.flatnonzero((train_doms[q] & (d_vis > cfg.collar_px)).ravel())
        rng_q.shuffle(pool)
        neg_k_by_q.append(pool)

    extra_kin_keys = BMR_FOLD_NAMES + ELASTIC_NAMES
    X_kin_parts: list[list[np.ndarray]] = [[] for _ in range(4)]
    y_kin_parts: list[list[np.ndarray]] = [[] for _ in range(4)]

    for s_idx, held_s in enumerate(comp_masks):
        vis_80 = vis_full & ~held_s
        d_80 = ndi.distance_transform_edt(~vis_80)
        el_80 = compute_elastic_fields(vis_80, fp)
        for q in range(4):
            pos_s = np.flatnonzero((held_s & train_doms[q] & (d_80 > cfg.collar_px)).ravel())
            pool_q = neg_k_by_q[q]
            neg_per = min(cfg.n_neg_kin // k_splits, pool_q.size // k_splits)
            neg_s = pool_q[s_idx * neg_per : (s_idx + 1) * neg_per]
            idx_s = np.concatenate([pos_s, neg_s])
            y_s = np.concatenate(
                [np.ones(pos_s.size, dtype=np.int8), np.zeros(neg_s.size, dtype=np.int8)]
            )
            merged_ex = {**bmr_by_q[q], **{ek: el_80[ek] for ek in ELASTIC_NAMES}}
            X_kin_parts[q].append(_extract_rows(stack["X_slcq"], idx_s, merged_ex, extra_kin_keys))
            y_kin_parts[q].append(y_s)
        del d_80, el_80
        gc.collect()
    del comp_masks

    # Also build 2-fold (50/50) cross-component samples for matched E3 ablation ONCE
    comp_a = partition_visible_components_k(vis_full, 2, seed=cfg.seed + seed_base_offset + 70)
    X_abl_parts: list[list[np.ndarray]] = [[] for _ in range(4)]
    y_abl_parts: list[list[np.ndarray]] = [[] for _ in range(4)]
    for s_idx, held_s in enumerate(comp_a):
        vis_other = vis_full & ~held_s
        d_other = ndi.distance_transform_edt(~vis_other)
        el_o = compute_elastic_fields(vis_other, fp)
        for q in range(4):
            pos_s = np.flatnonzero((held_s & train_doms[q] & (d_other > cfg.collar_px)).ravel())
            pool_q = neg_k_by_q[q]
            half_neg = min(cfg.n_neg_kin // 2, pool_q.size // 2)
            neg_s = pool_q[s_idx * half_neg : (s_idx + 1) * half_neg]
            idx_s = np.concatenate([pos_s, neg_s])
            y_s = np.concatenate(
                [np.ones(pos_s.size, dtype=np.int8), np.zeros(neg_s.size, dtype=np.int8)]
            )
            X_abl_parts[q].append(
                _extract_rows(
                    stack["X_abl"],
                    idx_s,
                    {"iso_tip_halo": el_o["iso_tip_halo"]},
                    ("iso_tip_halo",),
                )
            )
            y_abl_parts[q].append(y_s)
        del d_other, el_o
        gc.collect()
    del comp_a, neg_k_by_q

    raw_blind_oof = np.zeros(fp.shape, dtype=np.float32)
    raw_kin_oof = np.zeros(fp.shape, dtype=np.float32)
    raw_e3_oof = np.zeros(fp.shape, dtype=np.float32)

    for q in range(4):
        q_mask = fp & (quad == q)
        if not q_mask.any():
            continue

        # 1. Blind specialist fit on train_doms[q] -> predict on q_mask
        rng_b = np.random.default_rng(cfg.seed + seed_base_offset + 110 + q)
        pos_b = np.flatnonzero((vis_full & train_doms[q]).ravel())
        neg_pool_b = np.flatnonzero((train_doms[q] & (d_vis > cfg.blind_neg_buffer_px)).ravel())
        neg_b = rng_b.choice(neg_pool_b, size=min(cfg.n_neg_blind, neg_pool_b.size), replace=False)
        del neg_pool_b
        idx_b = np.concatenate([pos_b, neg_b])
        y_b = np.concatenate(
            [np.ones(pos_b.size, dtype=np.int8), np.zeros(neg_b.size, dtype=np.int8)]
        )
        X_b = _extract_rows(stack["X_slcq"], idx_b, bmr_by_q[q], BMR_FOLD_NAMES)
        del pos_b, neg_b, idx_b

        clf_b1 = _make_hgb(
            max_iter=215,
            learning_rate=cfg.learning_rate,
            max_leaf_nodes=47,
            min_samples_leaf=110,
            l2_regularization=2.8,
            seed=cfg.seed + seed_base_offset + 120 + q,
        ).fit(X_b, y_b)
        clf_b2 = _make_hgb(
            max_iter=230,
            learning_rate=cfg.learning_rate,
            max_leaf_nodes=31,
            min_samples_leaf=130,
            l2_regularization=3.6,
            seed=cfg.seed + seed_base_offset + 130 + q,
        ).fit(X_b, y_b)
        del X_b, y_b
        rb = _predict_chunked(
            (clf_b1, clf_b2), (0.55, 0.45), stack["X_slcq"], bmr_by_q[q], BMR_FOLD_NAMES, q_mask
        )
        raw_blind_oof[q_mask] = rb[q_mask]
        del clf_b1, clf_b2, rb

        # 2. 5-fold (80/20) kinematic specialist fit on train_doms[q] -> predict on q_mask
        X_k = np.vstack(X_kin_parts[q])
        y_k = np.concatenate(y_kin_parts[q])
        X_kin_parts[q].clear()
        y_kin_parts[q].clear()
        clf_k1 = _make_hgb(
            max_iter=230,
            learning_rate=cfg.learning_rate,
            max_leaf_nodes=53,
            min_samples_leaf=95,
            l2_regularization=2.5,
            seed=cfg.seed + seed_base_offset + 160 + q,
        ).fit(X_k, y_k)
        clf_k2 = _make_hgb(
            max_iter=245,
            learning_rate=cfg.learning_rate,
            max_leaf_nodes=35,
            min_samples_leaf=115,
            l2_regularization=3.5,
            seed=cfg.seed + seed_base_offset + 170 + q,
        ).fit(X_k, y_k)
        del X_k, y_k
        eval_ex = {**bmr_by_q[q], **{ek: el_eval[ek] for ek in ELASTIC_NAMES}}
        rk = _predict_chunked(
            (clf_k1, clf_k2), (0.55, 0.45), stack["X_slcq"], eval_ex, extra_kin_keys, q_mask
        )
        raw_kin_oof[q_mask] = rk[q_mask]
        del clf_k1, clf_k2, eval_ex, rk

        # 3. Matched pixel-local E3 ablation fit on train_doms[q] -> predict on q_mask
        X_a = np.vstack(X_abl_parts[q])
        y_a = np.concatenate(y_abl_parts[q])
        X_abl_parts[q].clear()
        y_abl_parts[q].clear()
        clf_a = _make_hgb(
            max_iter=210,
            learning_rate=0.06,
            max_leaf_nodes=47,
            min_samples_leaf=110,
            l2_regularization=2.5,
            seed=cfg.seed + seed_base_offset + 190 + q,
        ).fit(X_a, y_a)
        del X_a, y_a
        ra = _predict_chunked(
            (clf_a,),
            (1.0,),
            stack["X_abl"],
            {"iso_tip_halo": el_eval["iso_tip_halo"]},
            ("iso_tip_halo",),
            q_mask,
        )
        raw_e3_oof[q_mask] = ra[q_mask]
        del clf_a, ra
        gc.collect()

    del d_vis, bmr_by_q
    p_hgb_blind = calibrate_footprint_quadrant_posterior(
        raw_blind_oof, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    l_prob = np.clip(
        0.005 + 0.990 * np.asarray(stack["L_slcq"], dtype=np.float32), 1e-4, 0.9999
    )
    p_corrob = calibrate_footprint_quadrant_posterior(
        l_prob, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    p_blind = np.where(
        fp,
        cfg.blind_hgb_weight * p_hgb_blind + cfg.blind_corrob_weight * p_corrob,
        np.float32(0.0),
    ).astype(np.float32)
    p_kin = calibrate_footprint_quadrant_posterior(
        raw_kin_oof, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    surf_e1 = fuse_cover_conditioned_noisy_or(
        p_blind,
        p_kin,
        stack["cover_propensity"],
        fp,
        alpha_blind_min=cfg.alpha_blind_min,
        alpha_blind_max=cfg.alpha_blind_max,
        alpha_kin=cfg.alpha_kin,
    )
    surf_e3 = calibrate_footprint_quadrant_posterior(
        raw_e3_oof, fp, quad, tau0=cfg.tau0_logit, beta=cfg.beta_logit
    )
    return {
        "surf_e1": surf_e1,
        "p_blind": p_blind,
        "p_kin": p_kin,
        "surf_e3": surf_e3,
        "bmr_oof": bmr_oof,
        "bmr_weights_by_quadrant": bmr_weights_by_q,
    }
