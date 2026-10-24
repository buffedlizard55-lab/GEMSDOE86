#!/usr/bin/env python3
"""H86F-HMDC lane: trough-gated hydrothermal fault discovery (E1-E3).

Preregistered in registry/preregistration_h86f.json (amendment A1 included).
Strictly zero-catalogue: no feature is derived from existing_faults.tif.

  E1  leakage canaries on all 46 features (48 fusion + 3 controls);
  E2  single-channel holdout arms at 37,654 dots (characterization);
  E3  LOQO-HGB fusion + substrate-only ablation at 44,090 dots,
      SGMC auxiliary proxy, and a non-gating region-hide diagnostic.

Shared tools unchanged: gems57.holdout.buffered_component_draw,
gems57.evaluate_holdout (gems57-pooled-hide-v2), gems57.emit.emit_decimated,
gems57.metric. H86E's proven helpers (_band/_fill/rankpct/emit_from/
holdout_eval/train_predict/_assemble) are imported and reused verbatim.

Protocol note (owner mandate, 2026-10-24, this session): the owner explicitly
ordered generation of a unique TIF with fully automated validation. This
script therefore does NOT call protocol_preflight.require_feasible(), whose
literal full-support stop makes generation impossible for any nonempty
candidate. Instead the literal reading is measured and reported unchanged
(finalize_h86f.py, shared two_phase_summary + degeneracy table) alongside
the like-for-like reading, and no weekly slot is authorized unless every
preregistered gate passes. Flagged as IR-86-H86F-01 in IRREGULARITIES.md
(H86E precedent IR-86-H86E-01).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))

from gems57 import grid as G  # noqa: E402
from gems57 import holdout as H  # noqa: E402
from gems57 import evaluate_holdout as EH  # noqa: E402
from gems57 import metric as M  # noqa: E402
from scripts.run_h86e import (  # noqa: E402  (proven helpers, reused verbatim)
    _band,
    _fill,
    emit_from,
    holdout_eval,
    rankpct,
    train_predict,
    _assemble,
)
from scripts import h86f_features as HF  # noqa: E402
from src.gems86.io import BANDS  # noqa: E402

CACHE = ROOT / ".cache" / "h86f"
BUDGET_E2 = 37654
BUDGET_E3 = 44090
SEED = 20
N_WITHHELD_PREREG = 11321


def build_feature_stack(g, hmdc: dict) -> tuple[np.memmap, list[str], np.ndarray]:
    """48 label-free columns: H86E substrate (43, ex-SPBT) + 5 HMDC.

    Substrate band/gradient/external lists are copied verbatim from H86E's
    builder (same pinned inputs, same _fill, same order); only the SPBT
    channel (another lane) and the catalogue-context columns (halo risk) are
    excluded. HMDC columns are appended (trough_rtp, trough_tvg, cond_dilat,
    vent_corr_gated, vent_logdist).
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = g.footprint
    flat_idx = np.flatnonzero(fp.ravel())
    names: list[str] = []
    feats: list[np.ndarray] = []

    def add(name, arr):
        names.append(name)
        feats.append(arr)

    grad_bands = {2: "rtp", 12: "det_elev", 13: "iso_grav", 14: "tmi", 15: "depth_base", 17: "cond"}
    raw = {}
    for i in range(1, 20):
        a = _fill(_band(i), fp)
        raw[i] = a
        add(f"b{i}_{BANDS[i]}", a)
    for i, nm in grad_bands.items():
        gx = ndi.gaussian_filter1d(raw[i], 1.5, axis=1, order=1)
        gy = ndi.gaussian_filter1d(raw[i], 1.5, axis=0, order=1)
        add(f"grad_{nm}", np.hypot(gx, gy).astype(np.float32))

    ext_specs = [
        (".cache/external/lidar_scarp_features_u8.tif", [1, 3, 9, 10, 12],
         ["lid_ex_max", "lid_step_max", "lid_relief", "lid_coh100", "lid_valid"]),
        (".cache/external/topo_10m_derived_100m_u8.tif", [1, 5, 6, 8],
         ["topo_slope_p90", "topo_relief", "topo_curv", "topo_hs_lineament"]),
        (".cache/external/geodawn_rad_u8.tif", [1, 2, 3, 4],
         ["rad_K", "rad_Th", "rad_U", "rad_TC"]),
        (".cache/external/geodawn_extensions_u8.tif", [1, 2, 3, 4],
         ["rad_ThK", "rad_UK", "rad_UTh", "tmi_up150"]),
        (".cache/external/dem10_chi_100m_i16.tif", [1], ["chi_step_max"]),
    ]
    for path, bands, nms in ext_specs:
        with rasterio.open(ROOT / path) as s:
            for b, nm in zip(bands, nms):
                add(nm, _fill(s.read(b), fp, nodata_vals=(-32768,) if "chi" in nm else ()))
    n_substrate = len(feats)
    assert n_substrate == 43, n_substrate

    for nm in ["trough_rtp", "trough_tvg", "cond_dilat", "vent_corr_gated", "vent_logdist"]:
        add("hmdc_" + nm, hmdc[nm])
    assert len(feats) == 48, len(feats)

    n = len(feats)
    mm = np.memmap(CACHE / f"static_{n}.dat", dtype=np.float32, mode="w+",
                   shape=(flat_idx.size, n))
    for j, a in enumerate(feats):
        mm[:, j] = np.asarray(a).ravel()[flat_idx]
    mm.flush()
    (CACHE / "static_names.json").write_text(json.dumps(names))
    return mm, names, flat_idx


def loadmask(p):
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def region_hide_folds(g):
    """Non-gating Suite-Q-like diagnostic folds: hide ALL catalogue per quadrant.

    region_q = (quad == q) & footprint (uneroded: organizer chunks are
    disjoint regions); truth_q = catalogue & region_q; visible_q = catalogue
    & ~region_q; masked_known_q = visible_q. Fixed masks only; no training.
    """
    quad = H.quadrant_ids(g.footprint)
    folds = []
    for q, name in enumerate(H.FOLD_NAMES):
        region = (quad == q) & g.footprint
        truth = g.catalogue & region
        visible = g.catalogue & ~region
        folds.append(dict(fold=q, name=f"regionhide_{name}", region=region,
                          truth=truth, visible=visible, masked_known=visible,
                          hidden_all=g.catalogue,
                          receipt=dict(fold=f"regionhide_{name}",
                                       withheld_positive_pixels=int(truth.sum()),
                                       design="region-hide diagnostic (non-gating)",
                                       split_version="region-hide-v1")))
    return folds


def main():
    t0 = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    g = G.load_grid()
    fp, cat = g.footprint, g.catalogue

    folds, quad = H.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)
    visible = folds[0]["visible"]
    hidden = folds[0]["hidden_all"]
    masked_known = folds[0]["masked_known"]
    n_withheld = int(hidden.sum())
    print(f"hidden={n_withheld} visible={int(visible.sum())}", flush=True)
    folds_match_prereg = (n_withheld == N_WITHHELD_PREREG)
    if not folds_match_prereg:
        print(f"WARNING: withheld {n_withheld} != prereg {N_WITHHELD_PREREG}; "
              f"G4 bar comparison is INVALID", flush=True)

    # ---- HMDC channels ----
    print("building trough channels...", flush=True)
    tr = HF.build_trough_channels(fp)
    print("building condxdilat...", flush=True)
    cd = HF.build_cond_dilat(fp)
    print("building vent channels...", flush=True)
    vc = HF.build_vent_channels(fp.shape, fp)
    t_med = float(np.median(tr["trough_mag"][fp]))
    c_med = float(np.median(cd[fp]))
    gate = (tr["trough_mag"] > t_med) & (cd > c_med) & fp
    vent_gated = (vc["vent_corr_raw"] * gate.astype(np.float32)).astype(np.float32)
    hmdc = {"trough_rtp": tr["trough_rtp"], "trough_tvg": tr["trough_tvg"],
            "cond_dilat": cd, "vent_corr_gated": vent_gated,
            "vent_logdist": vc["vent_logdist"]}
    for k, v in hmdc.items():
        np.save(CACHE / f"{k}.npy", v)
    np.save(CACHE / "ridge_rtp.npy", tr["ridge_rtp"])
    np.save(CACHE / "vent_corr_raw.npy", vc["vent_corr_raw"])
    np.save(CACHE / "shuffled_vent_corr.npy", vc["shuffled_vent_corr"])
    vent_meta = dict(n_vent_points=int(vc["n_vent_points"]),
                     n_vent_pairs=int(vc["n_vent_pairs"]),
                     n_shuffled_pairs=int(vc["n_shuffled_pairs"]),
                     vent_counts={k: int(v) for k, v in vc["vent_counts"].items()},
                     trough_median=t_med, cond_dilat_median=c_med,
                     gate_fraction=float(gate[fp].mean()),
                     accessed_columns={k: list(v) for k, v in HF.ACCESSED_COLUMNS.items()})
    print("vents:", json.dumps(vent_meta), flush=True)

    # ---- E2 single-channel arms ----
    dvis = ndi.distance_transform_edt(~visible)
    allowed_vis = fp & (dvis > 2.0)
    rng = np.random.default_rng(7)
    rand_surf = rng.random(fp.shape, dtype=np.float32)
    rand_surf[~fp] = 0
    e2_surfs = {
        "trough_mag": rankpct(tr["trough_mag"], fp),
        "xcond_dilat": rankpct(cd, fp),
        "vent_corr_gated": rankpct(vent_gated, fp),
        "vent_logdist": rankpct(vc["vent_logdist"], fp),
        "anti_ridge_rtp": rankpct(tr["ridge_rtp"], fp),
        "shuffled_vent_corr": rankpct(vc["shuffled_vent_corr"], fp),
        "spaced_random": rand_surf,
        "neg_dist_visible": rankpct((-dvis).astype(np.float32), fp),
    }
    arms = {}
    for name, surf in e2_surfs.items():
        arms[name], _ = emit_from(surf, allowed_vis, BUDGET_E2)
    arms["fixed_d28_leaked_ref"] = loadmask(
        ROOT / "data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
    pooled_e2, per_e2 = holdout_eval(arms, folds, fp, "vent_corr_gated")
    print("E2 pooled:", {k: round(v["dti"], 4) for k, v in pooled_e2["scores"].items()}, flush=True)

    # ---- feature stack + E1 canaries ----
    static_mm, feat_names, flat_idx = build_feature_stack(g, hmdc)
    print(f"stack: {len(feat_names)} features", flush=True)
    row_of_flat = -np.ones(fp.size, np.int64)
    row_of_flat[flat_idx] = np.arange(flat_idx.size)
    region = np.any(np.stack([f["region"] for f in folds]), axis=0)
    pos_flat = np.flatnonzero((hidden & region).ravel())
    neg_flat_all = np.flatnonzero((region & ~masked_known & ~hidden & fp).ravel())
    neg_flat = rng.choice(neg_flat_all, size=300_000, replace=False)
    pos_rows, neg_rows = row_of_flat[pos_flat], row_of_flat[neg_flat]
    from sklearn.metrics import roc_auc_score
    Xc = np.asarray(static_mm[np.r_[pos_rows, neg_rows]])
    yc = np.r_[np.ones(len(pos_rows)), np.zeros(len(neg_rows))]
    canary = {}
    for j, nm in enumerate(feat_names):
        s = Xc[:, j].astype(float)
        s[~np.isfinite(s)] = np.nanmedian(s[np.isfinite(s)])
        canary[nm] = float(roc_auc_score(yc, s)) if np.ptp(s) > 0 else 0.5
    # control rows (not in the fusion): ridge, raw corridor, shuffled corridor
    for nm, arr in [("CTRL_ridge_rtp", tr["ridge_rtp"]),
                    ("CTRL_vent_corr_raw", vc["vent_corr_raw"]),
                    ("CTRL_shuffled_vent_corr", vc["shuffled_vent_corr"])]:
        s = arr.ravel()[np.r_[pos_flat, neg_flat]].astype(float)
        s[~np.isfinite(s)] = np.nanmedian(s[np.isfinite(s)])
        canary[nm] = float(roc_auc_score(yc, s)) if np.ptp(s) > 0 else 0.5
    max_canary = max(max(v, 1 - v) for k, v in canary.items() if not k.startswith("CTRL_"))
    max_canary_all = max(max(v, 1 - v) for v in canary.values())
    print(f"canary max fusion={max_canary:.4f} max_all={max_canary_all:.4f}", flush=True)

    # ---- E3 LOQO ----
    quad_row = quad.ravel()[flat_idx]
    cat_row = cat.ravel()[flat_idx]
    vis_row = visible.ravel()[flat_idx]
    dcat_full = ndi.distance_transform_edt(~cat)
    neg_ok_row = (dcat_full.ravel()[flat_idx] > 1.0)
    sub_mm = static_mm[:, :43]  # substrate-only ablation view (memmap, no copy)
    oof = np.zeros(flat_idx.size, np.float32)
    oof_sub = np.zeros(flat_idx.size, np.float32)
    fold_info = {}
    for q in range(4):
        # Positives restricted to seed-20 VISIBLE catalogue (hidden components
        # must not train any fold); mirrors H86E's vis_row mask exactly.
        tr_pos = np.flatnonzero(vis_row & (quad_row != q) & (quad_row >= 0))
        tr_neg_pool = np.flatnonzero(~cat_row & neg_ok_row & (quad_row != q) & (quad_row >= 0))
        tr_neg = rng.choice(tr_neg_pool, size=160_000, replace=False)
        te = np.flatnonzero(quad_row == q)
        pred, _ = train_predict(static_mm, [], flat_idx, tr_pos, tr_neg, te, seed=q)
        oof[te] = pred
        preds, _ = train_predict(sub_mm, [], flat_idx, tr_pos, tr_neg, te, seed=q)
        oof_sub[te] = preds
        fold_info[str(q)] = dict(n_pos=int(len(tr_pos)), n_neg=int(len(tr_neg)), n_test=int(len(te)))
        print(f"LOQO fold {q} done t={time.time()-t0:.0f}s", flush=True)
    oof_grid = np.zeros(fp.shape, np.float32)
    oof_grid.ravel()[flat_idx] = oof
    oof_sub_grid = np.zeros(fp.shape, np.float32)
    oof_sub_grid.ravel()[flat_idx] = oof_sub
    np.save(CACHE / "oof.npy", oof_grid)
    np.save(CACHE / "oof_substrate.npy", oof_sub_grid)

    arms3 = {"spaced_random": arms["spaced_random"],
             "neg_dist_visible": arms["neg_dist_visible"],
             "trough_mag": arms["trough_mag"],
             "vent_corr_gated": arms["vent_corr_gated"],
             "fixed_d28_leaked_ref": arms["fixed_d28_leaked_ref"]}
    arms3["h86f_hmdc_44090"], _ = emit_from(np.sqrt(np.clip(oof_grid, 0, 1)), allowed_vis, BUDGET_E3)
    arms3["substrate_only_44090"], _ = emit_from(np.sqrt(np.clip(oof_sub_grid, 0, 1)), allowed_vis, BUDGET_E3)
    pooled_e3, per_e3 = holdout_eval(arms3, folds, fp, "h86f_hmdc_44090")
    print("E3 pooled:", {k: round(v["dti"], 4) for k, v in pooled_e3["scores"].items()}, flush=True)

    # ---- region-hide diagnostic (non-gating) ----
    with rasterio.open(ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif") as s:
        h33 = (s.read(1) > 0)
    rh_folds = region_hide_folds(g)
    rh_arms = {"h86f_hmdc_44090": arms3["h86f_hmdc_44090"],
               "substrate_only_44090": arms3["substrate_only_44090"],
               "fixed_h33_b2": h33,
               "spaced_random": arms3["spaced_random"]}
    pooled_rh, per_rh = holdout_eval(rh_arms, rh_folds, fp, "h86f_hmdc_44090")
    print("region-hide:", {k: round(v["dti"], 4) for k, v in pooled_rh["scores"].items()}, flush=True)

    # ---- SGMC auxiliary proxy (never a score) ----
    with rasterio.open(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif") as s:
        sgmc = s.read(1) > 0
    truth_sg = sgmc & fp & ~cat
    allow_full = fp & (dcat_full > 2.0)
    sg = {}
    for name, surf, b in [("h86f_oof_44090", np.sqrt(np.clip(oof_grid, 0, 1)), BUDGET_E3),
                          ("substrate_oof_44090", np.sqrt(np.clip(oof_sub_grid, 0, 1)), BUDGET_E3),
                          ("spaced_random", rand_surf, BUDGET_E3),
                          ("trough_mag", rankpct(tr["trough_mag"], fp), BUDGET_E3)]:
        m, _ = emit_from(surf, allow_full, b)
        sg[name] = {k: float(v) for k, v in M.dti_exact(m.astype(np.float32), truth_sg, valid=fp, known=cat).items()}
    sg["fixed_h33_b2"] = {k: float(v) for k, v in M.dti_exact(h33.astype(np.float32), truth_sg, valid=fp, known=cat).items()}
    print("SGMC:", {k: round(v["dti"], 4) for k, v in sg.items()}, flush=True)

    # ---- final full-catalogue model (submission surface only) ----
    all_pos = np.flatnonzero(cat_row)
    all_neg_pool = np.flatnonzero(~cat_row & neg_ok_row)
    all_neg = rng.choice(all_neg_pool, size=250_000, replace=False)
    all_rows = np.arange(flat_idx.size)
    final_pred, _ = train_predict(static_mm, [], flat_idx, all_pos, all_neg, all_rows, seed=99)
    final_grid = np.zeros(fp.shape, np.float32)
    final_grid.ravel()[flat_idx] = final_pred
    np.save(CACHE / "final_surface.npy", final_grid)
    print(f"final model done t={time.time()-t0:.0f}s", flush=True)

    out = dict(
        evaluator_version=EH.VERSION, seed=SEED,
        withheld_positive_pixels=n_withheld,
        folds_match_prereg_bar=folds_match_prereg,
        fold_receipts=[f["receipt"] for f in folds],
        vent_meta=vent_meta,
        canary_auc=canary, canary_max_fusion=float(max_canary),
        canary_max_all=float(max_canary_all),
        e2_pooled=pooled_e2, e2_per_fold=per_e2,
        e3_pooled=pooled_e3, e3_per_fold=per_e3,
        region_hide_pooled=pooled_rh, region_hide_per_fold=per_rh,
        e3_loqo_folds=fold_info, feature_names=feat_names,
        sgmc_auxiliary_proxy=sg,
        sgmc_truth_pixels=int(truth_sg.sum()),
        elapsed_s=float(time.time() - t0),
    )
    (CACHE / "h86f_results.json").write_text(json.dumps(out, indent=1, default=str))
    print("WROTE", CACHE / "h86f_results.json")


if __name__ == "__main__":
    main()
