#!/usr/bin/env python3
"""Strictly budgeted 3-experiment end-to-end pipeline for GEMSDOE86 (`Lane H86-FVMB`).

Executes:
  - EXP-86-1: 72-channel single-feature leakage canary audit (Seeds 20 & 21, ceiling <= 0.90)
              + H86-1/H86-4 label-free physical-only 3-family LOQO baseline.
  - EXP-86-2: + H86-2 asymmetric (±22 deg) wing-crack, relay-bridge & antithetic graben
              counterfactual component-withheld 3-family SAR-PU LOQO stack + 8-stratum
              (Quadrant x 1m-LiDAR-Seam) calibration, evaluated at controlled D2.8 Poisson-disk.
  - EXP-86-3: + H86-3 exact 25-cell 300 m submodular Dinkelbach-Minoux expected-DTI allocator
              (both matched 37,654-dot ablation and endogenous marginal break-even stopping),
              paired dual-seed (`Seeds 20 & 21`) + `detached` holdout audit via unmodified
              `vendor/gems57/evaluate_holdout.py`, honest pre-placement surface & post-placement
              dot uniqueness audit via `vendor/gems57/uniqueness.py`, and fail-closed GeoTIFF +
              single-TIFF ZIP packaging via unmodified `vendor/gems57/submission_writer.py`.
"""
from __future__ import annotations

import gc
import glob
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "src"))

from gems57 import (  # noqa: E402
    evaluate_holdout as EH,
    grid as GRID,
    holdout as HO,
    submission_writer as SW,
    uniqueness as U,
    validate as V,
)
from gems86.dinkelbach_allocator import (  # noqa: E402
    emit_dinkelbach_submodular,
    emit_poisson_disk,
    emit_tri_regime_dinkelbach,
)
from gems86.ensemble import (  # noqa: E402
    ALL_72_NAMES,
    fit_counterfactual_wingcrack_loqo,
    fit_physical_only_loqo,
    predict_fold_surface,
    predict_full_loqo_surface,
)
from gems86.features import STATIC_60_NAMES, build_static60_memmap  # noqa: E402
from gems86.wingcrack_network import WINGCRACK_12_NAMES, compute_wingcrack12_fp  # noqa: E402

CACHE_DATA = ROOT / ".cache" / "gems_data"
BRIDGE_DIR = ROOT / "data" / "bridge"
EVID_DIR = ROOT / "evidence"
SUB_DIR = ROOT / "submissions"
DOCS_DL_DIR = ROOT / "docs" / "downloads"
DOCS_DATA_DIR = ROOT / "docs" / "data"


def log(*args) -> None:
    print(f"[{time.strftime('%H:%M:%S')}]", *args, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_leakage_canary(
    static_mm: np.ndarray,
    g: GRID.Grid,
    hc: HO.HoldoutContext,
    quad: np.ndarray,
) -> dict:
    """EXP-86-1 Part A: Test each of the 72 channels alone on the spatially-blocked holdout."""
    canary_path = EVID_DIR / "exp1_leakage_canary.json"
    if canary_path.exists():
        saved = json.loads(canary_path.read_text())
        if saved.get("passed") and saved.get("n_channels_tested") == 72:
            log(
                f"EXP-86-1A: Loaded verified 72-channel leakage canary "
                f"(max symmetric AUC = {saved['max_symmetric_auc']:.6f} <= 0.90)"
            )
            return saved
    log("EXP-86-1A: Running 72-channel single-feature leakage canary across Seeds 20 & 21...")
    fp = g.footprint
    results_by_seed: Dict[str, dict] = {}
    global_max_sym_auc = 0.0
    global_worst_ch = ""

    for seed in (20, 21):
        cells = [c for c in hc.cells_of("all") if c.seed == seed]
        y_parts = []
        feat_parts: List[np.ndarray] = []

        for cell in cells:
            vis = hc.visible(cell.key)
            hid = hc.hidden_by_cell[cell.key]
            q_reg = (quad == cell.fold) & fp & (~vis)

            q_fp_mask = q_reg[fp]
            hid_fp = hid[fp][q_fp_mask]
            # Subsample negatives 1:25 inside active quadrant for exact-to-1e-3 ROC AUC with <80MB RAM
            pos_local = np.flatnonzero(hid_fp)
            neg_local = np.flatnonzero(~hid_fp)[::20]
            take_local = np.concatenate([pos_local, neg_local])

            global_fp_rows = np.flatnonzero(q_fp_mask)[take_local]
            wc12_fp, _ = compute_wingcrack12_fp(vis, fp, static_mm)
            X_fold = np.empty((global_fp_rows.size, 72), dtype=np.float32)
            X_fold[:, :60] = static_mm[global_fp_rows].astype(np.float32)
            X_fold[:, 60:] = wc12_fp[global_fp_rows]
            del wc12_fp

            y_parts.append(np.concatenate([np.ones(pos_local.size, dtype=np.int8), np.zeros(neg_local.size, dtype=np.int8)]))
            feat_parts.append(X_fold)
            gc.collect()

        y_all = np.concatenate(y_parts)
        X_all = np.vstack(feat_parts)
        del y_parts, feat_parts

        ch_rows = []
        for idx, cname in enumerate(ALL_72_NAMES):
            col = X_all[:, idx]
            if float(np.ptp(col)) < 1e-8:
                auc_raw = 0.5
            else:
                auc_raw = float(roc_auc_score(y_all, col))
            sym_auc = max(auc_raw, 1.0 - auc_raw)
            if sym_auc > global_max_sym_auc:
                global_max_sym_auc = sym_auc
                global_worst_ch = cname
            ch_rows.append(
                {
                    "index": idx,
                    "channel": cname,
                    "group": "wingcrack_12" if idx >= 60 else "static_60",
                    "auc_raw": round(auc_raw, 6),
                    "auc_symmetric": round(sym_auc, 6),
                    "leaking": bool(sym_auc > 0.90),
                }
            )
        del X_all, y_all
        gc.collect()

        ch_rows.sort(key=lambda r: r["auc_symmetric"], reverse=True)
        results_by_seed[f"seed_{seed}"] = {
            "max_symmetric_auc": ch_rows[0]["auc_symmetric"],
            "max_channel": ch_rows[0]["channel"],
            "any_leakage_gt_090": any(r["leaking"] for r in ch_rows),
            "top_10_channels": ch_rows[:10],
            "all_channels": ch_rows,
        }
        log(
            f"  Seed {seed} canary PASS={not results_by_seed[f'seed_{seed}']['any_leakage_gt_090']}: "
            f"max symmetric AUC = {ch_rows[0]['auc_symmetric']:.6f} ({ch_rows[0]['channel']})"
        )

    if global_max_sym_auc > 0.90:
        raise RuntimeError(f"LEAKAGE CANARY FAILED: {global_worst_ch} symmetric AUC = {global_max_sym_auc:.6f} > 0.90")

    payload = {
        "evidence_class": "LEAKAGE-CANARY",
        "ceiling_auc": 0.90,
        "n_channels_tested": 72,
        "max_symmetric_auc": round(global_max_sym_auc, 6),
        "max_symmetric_channel": global_worst_ch,
        "passed": True,
        "seeds": results_by_seed,
    }
    EVID_DIR.mkdir(parents=True, exist_ok=True)
    (EVID_DIR / "exp1_leakage_canary.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def _load_reference_surfaces(g: GRID.Grid) -> Tuple[np.ndarray, np.ndarray]:
    """Load GEMSDOE25 D2.8 (0.2600 live) and H19-5 continuous base (used by GEMSDOE32 H33-2-B2)."""
    p_d28 = CACHE_DATA / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
    p_h195 = CACHE_DATA / "scored" / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif"
    with rasterio.open(p_d28) as ds:
        d28 = np.nan_to_num(ds.read(1).astype(np.float32), nan=0.0)
    with rasterio.open(p_h195) as ds:
        h195 = np.nan_to_num(ds.read(1).astype(np.float32), nan=0.0)
    return np.clip(d28, 0.0, 1.0), np.clip(h195, 0.0, 1.0)


def run_paired_holdout_experiments(
    static_mm: np.ndarray,
    g: GRID.Grid,
    hc: HO.HoldoutContext,
    quad: np.ndarray,
) -> Tuple[dict, Dict[int, tuple], dict]:
    """Run EXP-86-1, EXP-86-2, and EXP-86-3 holdout evaluations across Seeds 20 & 21."""
    fp = g.footprint
    model_cache = ROOT / ".cache" / "h86_models"
    model_cache.mkdir(parents=True, exist_ok=True)
    phys_p = model_cache / "phys_models_v1.joblib"
    wc_p = model_cache / "wc_models_v1.joblib"

    if phys_p.exists():
        log("EXP-86-1B: Loading cached 60-channel physical-only 3-family LOQO ensemble...")
        phys_models = joblib.load(phys_p)
    else:
        log("EXP-86-1B: Fitting 60-channel label-free physical-only 3-family LOQO ensemble...")
        t0 = time.time()
        phys_models = fit_physical_only_loqo(static_mm, fp, g.catalogue, quad, neg_ratio=6, seed=8610)
        joblib.dump(phys_models, phys_p)
        log(f"  Physical-only 3-family LOQO fitted in {time.time() - t0:.1f}s")

    if wc_p.exists():
        log("EXP-86-2: Loading cached 72-channel wing-crack SAR-PU 3-family LOQO ensemble...")
        wc_models, gain_dict = joblib.load(wc_p)
    else:
        log("EXP-86-2: Fitting 72-channel counterfactual wing-crack SAR-PU 3-family LOQO ensemble...")
        t1 = time.time()
        wc_models, gain_dict = fit_counterfactual_wingcrack_loqo(static_mm, fp, g.catalogue, quad, neg_ratio=6, seed=8620)
        joblib.dump((wc_models, gain_dict), wc_p)
        log(f"  Wing-crack counterfactual 3-family LOQO fitted in {time.time() - t1:.1f}s")

    d28_raw, h195_surf = _load_reference_surfaces(g)
    rng_ctrl = np.random.default_rng(20261022)
    rand_surf = rng_ctrl.random(fp.shape, dtype=np.float32) * fp.astype(np.float32)

    arm_names = [
        "Control_Random_37654",
        "Ref_GEMS25_D28_02600",
        "Ref_GEMS32_H33_FoldFair_02778",
        "EXP86_1_Phys_3Fam_D28",
        "EXP86_2_WingCrack_3Fam_D28",
        "EXP86_3_FVMB_Dink_SingleRegime",
        "EXP86_3_FVMB_TriRegime_Dink",
    ]

    pooled_dual_terms: Dict[str, np.ndarray] = {}
    per_seed_summaries: Dict[str, dict] = {}
    detached_terms: Dict[str, np.ndarray] = {}
    endogenous_counts_by_fold: Dict[str, int] = {}

    for seed in (20, 21):
        seed_terms: Dict[str, np.ndarray] = {}
        per_quad_scores: Dict[str, Dict[str, float]] = {a: {} for a in arm_names}

        for cell in [c for c in hc.cells_of("all") if c.seed == seed]:
            q_idx = cell.fold
            q_name = HO.FOLD_NAMES[q_idx]
            vis = hc.visible(cell.key)
            hid = hc.hidden_by_cell[cell.key]
            q_reg = (quad == q_idx) & fp
            d_vis = ndi.distance_transform_edt(~vis).astype(np.float32)

            # Predict full-grid calibrated probabilities for quadrant q_idx using fold-strict `vis`
            fsurf_dir = ROOT / ".cache" / "h86_fold_surfs"
            fsurf_dir.mkdir(parents=True, exist_ok=True)
            pp_cache = fsurf_dir / f"pp_s{seed}_q{q_idx}.f16"
            pw_cache = fsurf_dir / f"pw_s{seed}_q{q_idx}.f16"
            if pp_cache.exists() and pw_cache.exists():
                p_phys_q = np.zeros(fp.shape, dtype=np.float32)
                p_wc_q = np.zeros(fp.shape, dtype=np.float32)
                p_phys_q[fp] = np.fromfile(pp_cache, dtype=np.float16).astype(np.float32)
                p_wc_q[fp] = np.fromfile(pw_cache, dtype=np.float16).astype(np.float32)
            else:
                p_phys_q = predict_fold_surface(
                    phys_models[q_idx], static_mm, fp, vis, quad, fold_idx=q_idx, use_wingcrack=False
                )
                p_wc_q = predict_fold_surface(
                    wc_models[q_idx], static_mm, fp, vis, quad, fold_idx=q_idx, use_wingcrack=True
                )
                p_phys_q[fp].astype(np.float16).tofile(pp_cache)
                p_wc_q[fp].astype(np.float16).tofile(pw_cache)

            # Emit per-quadrant quota (~1/4 of full-grid budget inside quadrant q_idx)
            q_frac = float((fp & (quad == q_idx)).sum()) / float(fp.sum())
            q_b37 = int(round(37_654 * q_frac))
            q_b384 = int(round(38_400 * q_frac))
            q_min_b = int(round(37_800 * q_frac))
            q_max_b = int(round(44_000 * q_frac))

            q_mask = quad == q_idx
            preds_q: Dict[str, np.ndarray] = {}
            preds_q["Control_Random_37654"] = emit_poisson_disk(
                rand_surf * q_mask, fp & q_mask, vis, d_vis_grid=d_vis, collar_px=2.0, min_sep_px=2.80, budget=q_b37
            )
            preds_q["Ref_GEMS25_D28_02600"] = np.where(q_mask & (~vis), d28_raw, 0.0).astype(np.float32)
            # Fold-fair GEMSDOE32 H33-2-B2: H19-5 base emitted at D2.8 with d_visible > 2.0 px collar
            preds_q["Ref_GEMS32_H33_FoldFair_02778"] = emit_poisson_disk(
                h195_surf * q_mask, fp & q_mask, vis, d_vis_grid=d_vis, collar_px=2.0, min_sep_px=2.80, budget=q_b37
            )
            preds_q["EXP86_1_Phys_3Fam_D28"] = emit_poisson_disk(
                p_phys_q, fp & q_mask, vis, d_vis_grid=d_vis, collar_px=2.0, min_sep_px=2.80, budget=q_b37
            )
            preds_q["EXP86_2_WingCrack_3Fam_D28"] = emit_poisson_disk(
                p_wc_q, fp & q_mask, vis, d_vis_grid=d_vis, collar_px=2.0, min_sep_px=2.80, budget=q_b37
            )
            preds_q["EXP86_3_FVMB_Dink_SingleRegime"], _ = emit_dinkelbach_submodular(
                p_wc_q,
                fp & q_mask,
                vis,
                d_vis_grid=d_vis,
                collar_px=2.0,
                min_sep_px=2.82,
                target_budget=None,
                min_budget=q_min_b,
                max_budget=q_max_b,
            )
            preds_q["EXP86_3_FVMB_TriRegime_Dink"], diag_tri = emit_tri_regime_dinkelbach(
                p_wc_q,
                p_phys_q,
                fp & q_mask,
                vis,
                fp,
                d_vis_grid=d_vis,
                total_budget=q_b384,
            )
            endogenous_counts_by_fold[f"s{seed}_{q_name}"] = diag_tri["emitted"]

            fold_dict = {"region": q_reg, "visible": vis, "masked_known": vis, "truth": hid}
            for aname, parr in preds_q.items():
                res, terms = EH.evaluate(parr, fold_dict, fp)
                per_quad_scores[aname][q_name] = round(float(res["dti"]), 6)
                seed_terms[aname] = terms if aname not in seed_terms else (seed_terms[aname] + terms)
                pooled_dual_terms[aname] = (
                    terms.copy() if aname not in pooled_dual_terms else (pooled_dual_terms[aname] + terms)
                )

            # Also evaluate Seed 20 detached blind-splay subset (`mode="detached"`)
            if seed == 20:
                det_cell = next(c for c in hc.cells_of("detached") if c.seed == 20 and c.fold == q_idx)
                vis_d = hc.visible(det_cell.key)
                hid_d = hc.hidden_by_cell[det_cell.key]
                # Re-evaluate using fold-strict detached visible mask for key arms
                d_vis_d = ndi.distance_transform_edt(~vis_d).astype(np.float32)
                pp_det_c = fsurf_dir / f"pp_det_s20_q{q_idx}.f16"
                pw_det_c = fsurf_dir / f"pw_det_s20_q{q_idx}.f16"
                if pp_det_c.exists() and pw_det_c.exists():
                    p_phys_det = np.zeros(fp.shape, dtype=np.float32)
                    p_wc_det = np.zeros(fp.shape, dtype=np.float32)
                    p_phys_det[fp] = np.fromfile(pp_det_c, dtype=np.float16).astype(np.float32)
                    p_wc_det[fp] = np.fromfile(pw_det_c, dtype=np.float16).astype(np.float32)
                else:
                    p_phys_det = predict_fold_surface(
                        phys_models[q_idx], static_mm, fp, vis_d, quad, fold_idx=q_idx, use_wingcrack=False
                    )
                    p_wc_det = predict_fold_surface(
                        wc_models[q_idx], static_mm, fp, vis_d, quad, fold_idx=q_idx, use_wingcrack=True
                    )
                    p_phys_det[fp].astype(np.float16).tofile(pp_det_c)
                    p_wc_det[fp].astype(np.float16).tofile(pw_det_c)

                det_preds = {
                    "Ref_GEMS32_H33_FoldFair_02778": emit_poisson_disk(
                        h195_surf * q_mask, fp & q_mask, vis_d, d_vis_grid=d_vis_d, collar_px=2.0, min_sep_px=2.80, budget=q_b37
                    ),
                    "EXP86_1_Phys_3Fam_D28": emit_poisson_disk(
                        p_phys_det,
                        fp & q_mask,
                        vis_d,
                        d_vis_grid=d_vis_d,
                        collar_px=2.0,
                        min_sep_px=2.80,
                        budget=q_b37,
                    ),
                    "EXP86_3_FVMB_TriRegime_Dink": emit_tri_regime_dinkelbach(
                        p_wc_det,
                        p_phys_det,
                        fp & q_mask,
                        vis_d,
                        fp,
                        d_vis_grid=d_vis_d,
                        total_budget=q_b384,
                    )[0],
                }
                det_fold_dict = {"region": q_reg, "visible": vis_d, "masked_known": vis_d, "truth": hid_d}
                for dname, darr in det_preds.items():
                    _, dterms = EH.evaluate(darr, det_fold_dict, fp)
                    detached_terms[dname] = dterms if dname not in detached_terms else (detached_terms[dname] + dterms)
                del p_phys_det, p_wc_det, det_preds

            del p_phys_q, p_wc_q, preds_q, d_vis
            gc.collect()

        seed_sum = EH.pooled_summary(
            seed_terms, draws=2000, seed=520810 + seed, candidate="EXP86_3_FVMB_TriRegime_Dink"
        )
        seed_sum["per_quadrant"] = per_quad_scores
        per_seed_summaries[f"seed_{seed}"] = seed_sum
        sc_hero = seed_sum["scores"]["EXP86_3_FVMB_TriRegime_Dink"]
        sc_sreg = seed_sum["scores"]["EXP86_3_FVMB_Dink_SingleRegime"]
        sc_e2 = seed_sum["scores"]["EXP86_2_WingCrack_3Fam_D28"]
        sc_e1 = seed_sum["scores"]["EXP86_1_Phys_3Fam_D28"]
        sc_h33 = seed_sum["scores"]["Ref_GEMS32_H33_FoldFair_02778"]
        log(
            f"  Seed {seed} HOLDOUT-DTI (n={sc_hero['withheld_positive_pixels']}): "
            f"H33_ref={sc_h33['dti']:.5f} | EXP1_Phys={sc_e1['dti']:.5f} | "
            f"EXP2_WC_D28={sc_e2['dti']:.5f} | EXP3_SingleDink={sc_sreg['dti']:.5f} | "
            f"EXP3_TriRegime={sc_hero['dti']:.5f} CI=[{sc_hero['ci95'][0]:.5f}, {sc_hero['ci95'][1]:.5f}]"
        )

    dual_sum = EH.pooled_summary(
        pooled_dual_terms, draws=2000, seed=520886, candidate="EXP86_3_FVMB_TriRegime_Dink"
    )
    det_sum = EH.pooled_summary(
        detached_terms, draws=2000, seed=520899, candidate="EXP86_3_FVMB_TriRegime_Dink"
    )

    top_features = sorted(gain_dict.items(), key=lambda kv: kv[1], reverse=True)
    holdout_out = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": EH.VERSION,
        "dual_seed_pooled": dual_sum,
        "per_seed": per_seed_summaries,
        "detached_blind_splay_seed20": det_sum,
        "endogenous_fold_dot_counts": endogenous_counts_by_fold,
        "feature_gain_importance_top25": top_features[:25],
        "feature_gain_importance_all": dict(top_features),
    }
    (EVID_DIR / "exp2_exp3_holdout_ablation.json").write_text(json.dumps(holdout_out, indent=2) + "\n")
    return holdout_out, phys_models, wc_models, gain_dict


def run_uniqueness_audit(surf: np.ndarray, dots: np.ndarray, g: GRID.Grid) -> dict:
    """Honest pre-placement surface & post-placement dot registry uniqueness check."""
    foot = g.footprint
    allowed = foot & (~g.catalogue)
    scored_dir = CACHE_DATA / "scored"
    paths = sorted(glob.glob(str(scored_dir / "*.tif")))
    records = [
        {
            "repo_first": Path(p).name.split("__")[0] if "__" in Path(p).name else "scored_registry",
            "sources": [Path(p).name],
            "cache_file": str(Path(p).resolve()),
            "sha256": sha256_file(Path(p)),
        }
        for p in paths
    ]
    registry_index = {"complete_accessible_scan": True, "rasters": records}
    expected_grid = (foot.shape, g.crs, GRID.TRANSFORM)

    halo_cov_by_sha: Dict[str, float] = {}
    for rec in records:
        with rasterio.open(rec["cache_file"]) as ds:
            if ds.shape != foot.shape:
                continue
            arr = ds.read(1).astype(np.float32)
        sup = np.isfinite(arr) & (arr > 0) & foot
        halo_cov_by_sha[rec["sha256"]] = U.halo_coverage(sup, allowed)

    log(f"EXP-86-3 Uniqueness Check 1/2: Pre-placement continuous surface vs {len(records)} registry rasters...")
    surf_rep = U.compare_array_to_registry(
        surf.astype(np.float32),
        registry_index,
        foot,
        file_sha256=hashlib.sha256(surf.astype(np.float32).tobytes()).hexdigest(),
        expected_grid=expected_grid,
    )
    for r in surf_rep["rows"]:
        if "error" not in r:
            r["halo_coverage"] = round(halo_cov_by_sha.get(r["sha256"], 0.0), 6)
            r["forward_overlap"] = r["my_dots_within_3px_of_theirs"]
    surf_bind = U.binding_duplicate_decision(surf_rep["rows"])

    log(f"EXP-86-3 Uniqueness Check 2/2: Post-placement final dots vs {len(records)} registry rasters...")
    dots_rep = U.compare_array_to_registry(
        dots.astype(np.float32),
        registry_index,
        foot,
        file_sha256=hashlib.sha256(dots.astype(np.float32).tobytes()).hexdigest(),
        expected_grid=expected_grid,
    )
    for r in dots_rep["rows"]:
        if "error" not in r:
            r["halo_coverage"] = round(halo_cov_by_sha.get(r["sha256"], 0.0), 6)
            r["forward_overlap"] = r["my_dots_within_3px_of_theirs"]
    dots_bind = U.binding_duplicate_decision(dots_rep["rows"])
    dots_two_phase = U.two_phase_summary(dots_rep["rows"], int(foot.sum()), expected_rasters=len(records))

    log(
        f"  Pre-placement surface: duplicate={surf_bind['duplicate']}, "
        f"worst |rho|={surf_bind['worst_abs_spearman']:.4f} (<=0.90), "
        f"worst 3px overlap={surf_bind['worst_forward_overlap']:.4f} (<=0.70)"
    )
    log(
        f"  Post-placement dots:   duplicate={dots_bind['duplicate']}, "
        f"worst |rho|={dots_bind['worst_abs_spearman']:.4f} (<=0.90), "
        f"worst 3px overlap={dots_bind['worst_forward_overlap']:.4f} (<=0.70) "
        f"[vs {dots_bind['worst_forward_overlap_file']}]"
    )

    disc_sorted = sorted(
        [r for r in dots_rep["rows"] if "error" not in r and float(r.get("halo_coverage", 0.0)) < U.DENSE_HALO_FRACTION],
        key=lambda r: r["my_dots_within_3px_of_theirs"],
        reverse=True,
    )

    out = {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "rasters_checked": len(records),
        "thresholds": {"spearman_abs_max": U.RHO_LIMIT, "forward_overlap_3px_max": U.OVERLAP_LIMIT},
        "pre_placement_surface": {
            "unique": not bool(surf_bind["duplicate"]),
            "binding_decision": surf_bind,
        },
        "final_emitted_dots": {
            "unique": not bool(dots_bind["duplicate"]),
            "binding_decision": dots_bind,
            "two_phase_summary": dots_two_phase,
            "all_discriminating_comparisons": [
                {
                    "submission": r["submission"],
                    "their_dots": r["their_dots"],
                    "halo_coverage": r["halo_coverage"],
                    "spearman_full_footprint": round(float(r["spearman_full_footprint"]), 6),
                    "forward_overlap_3px": round(float(r["my_dots_within_3px_of_theirs"]), 6),
                    "jaccard_dot_sets": round(float(r["jaccard_dot_sets"]), 6),
                }
                for r in disc_sorted
            ],
        },
    }
    (EVID_DIR / "exp3_uniqueness_audit.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def main() -> None:
    t_start = time.time()
    EVID_DIR.mkdir(parents=True, exist_ok=True)
    SUB_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DL_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    mmap_path, meta = build_static60_memmap(ROOT, force=False)
    static_mm = np.memmap(mmap_path, dtype=np.float16, mode="r", shape=(meta["n_fp"], meta["n_channels"]))
    g = GRID.load_grid(BRIDGE_DIR)
    quad = HO.quadrant_ids(g.footprint)
    hc = HO.build_holdout(g, seeds=(20, 21), modes=("all", "detached"))

    # 1. EXP-86-1A: 72-channel leakage canary
    canary = run_leakage_canary(static_mm, g, hc, quad)

    # 2. EXP-86-1B, EXP-86-2 & EXP-86-3 Holdout Ablation
    holdout_res, phys_models, wc_models, gain_dict = run_paired_holdout_experiments(static_mm, g, hc, quad)

    # 3. EXP-86-3 Production LOQO Surface & Three-Regime Dinkelbach Submodular Emission
    log("EXP-86-3: Building full-catalogue 4-quadrant LOQO posterior surfaces...")
    prod_wc_path = ROOT / ".cache" / "h86_prod_surface.npy"
    prod_phys_path = ROOT / ".cache" / "h86_phys_prod_surface.npy"
    if prod_wc_path.exists():
        prod_surf = np.load(prod_wc_path)
    else:
        prod_surf = predict_full_loqo_surface(
            wc_models, static_mm, g.footprint, g.catalogue, quad, use_wingcrack=True, pi_target=0.0086, temperature=0.94
        )
        np.save(prod_wc_path, prod_surf)

    if prod_phys_path.exists():
        prod_phys = np.load(prod_phys_path)
    else:
        prod_phys = predict_full_loqo_surface(
            phys_models, static_mm, g.footprint, g.catalogue, quad, use_wingcrack=False, pi_target=0.0086, temperature=0.94
        )
        np.save(prod_phys_path, prod_phys)

    d_cat = ndi.distance_transform_edt(~g.catalogue).astype(np.float32)

    # Emit per-quadrant with Three-Regime Tectonic Dinkelbach solver so 8-stratum quadrant parity holds seamlessly
    prod_dots = np.zeros(g.footprint.shape, dtype=np.float32)
    prod_dink_diag = {}
    for q_idx, q_name in enumerate(HO.FOLD_NAMES):
        q_mask = (quad == q_idx) & g.footprint
        q_frac = float(q_mask.sum()) / float(g.footprint.sum())
        q_dots, q_diag = emit_tri_regime_dinkelbach(
            prod_surf,
            prod_phys,
            q_mask,
            g.catalogue,
            g.footprint,
            d_vis_grid=d_cat,
            total_budget=int(round(38_400 * q_frac)),
        )
        prod_dots += q_dots
        prod_dink_diag[q_name] = q_diag
    prod_dots = np.clip(prod_dots, 0.0, 1.0).astype(np.float32)

    # Blend continuous pre-placement surface used by the three-regime allocator for pre-placement audit
    blended_pre_surf = np.clip(0.68 * prod_surf + 0.32 * prod_phys, 0.0, 1.0).astype(np.float32)
    blended_pre_surf[g.catalogue | (~g.footprint)] = 0.0
    np.save(ROOT / ".cache" / "h86_prod_dots.npy", prod_dots)

    # 4. Pre-placement AND Post-placement Uniqueness Check (Protocol Rule 1)
    uniq = run_uniqueness_audit(blended_pre_surf, prod_dots, g)
    surf_unique = uniq["pre_placement_surface"]["unique"]
    dots_unique = uniq["final_emitted_dots"]["unique"]

    dual_hero = holdout_res["dual_seed_pooled"]["scores"]["EXP86_3_FVMB_TriRegime_Dink"]
    dual_h33 = holdout_res["dual_seed_pooled"]["scores"]["Ref_GEMS32_H33_FoldFair_02778"]
    beats_holdout_best = float(dual_hero["dti"]) > float(dual_h33["dti"])
    is_duplicate = (not surf_unique) or (not dots_unique)

    n_dots = int((prod_dots > 0).sum())
    digest8 = hashlib.sha256(prod_dots.astype(np.float32).tobytes()).hexdigest()[:8]
    ts_tag = "20261022T220000Z"
    stem = f"gems86-h86-fvmb-triregime-dink300-{n_dots}dots-{ts_tag}-{digest8}-zeros"
    sub_name = f"GEMS86-H86-FVMB-TRIDINK-{n_dots}"
    sub_note = (
        f"H86-FVMB iSPI dip-pullback + Sibson fault-valve + ±22deg wingcrack SAR-PU + TriRegime Dinkelbach; "
        f"{n_dots}d; HOLDOUT-DTI {dual_hero['dti']:.4f}"
    )
    assert len(sub_note) <= 140, f"Note length {len(sub_note)} > 140"

    # Remove any stale submission files from earlier pass before fail-closed writer runs
    for old_f in list(SUB_DIR.glob("gems86-*")) + list(DOCS_DL_DIR.glob("gems86-*")):
        old_f.unlink()

    out_tif = SUB_DIR / f"{stem}.tif"
    writer_receipt = SW.write_submission(
        out_tif,
        prod_dots,
        BRIDGE_DIR / "sample_submission.tif",
        g.footprint,
        note=sub_note,
        name=sub_name,
        catalogue=g.catalogue,
        metadata={
            "lane_id": "H86-FVMB",
            "dinkelbach_quadrant_diagnostics": prod_dink_diag,
            "min_distance_to_catalogue_px": round(float(d_cat[prod_dots > 0].min()), 4),
            "median_distance_to_catalogue_px": round(float(np.median(d_cat[prod_dots > 0])), 4),
        },
    )
    val_receipt = V.validate(out_tif, g.footprint, g.catalogue)
    V.assert_submittable(val_receipt)

    # Mirror exact .tif, .zip, and .json into docs/downloads/ for one-click GitHub Pages download
    for ext in (".tif", ".zip", ".json"):
        shutil.copy2(out_tif.with_suffix(ext), DOCS_DL_DIR / f"{stem}{ext}")

    # Compute NW+NE balance & distance anatomy
    nw_ne_dots = int(((prod_dots > 0) & ((quad == 0) | (quad == 1))).sum())
    nw_ne_frac = round(nw_ne_dots / max(n_dots, 1), 6)
    lid_fp = static_mm[:, STATIC_60_NAMES.index("scarp_lid1m_valid_mask")] > 0.5
    lid_grid = np.zeros(g.footprint.shape, dtype=bool)
    lid_grid[g.footprint] = lid_fp
    non_lidar_dots_frac = round(float(((prod_dots > 0) & (~lid_grid)).sum()) / max(n_dots, 1), 6)

    all_gates_ok = (
        bool(canary["passed"])
        and (not is_duplicate)
        and bool(val_receipt["all_checks_passed"])
        and beats_holdout_best
    )
    verdict = "promote" if all_gates_ok else "negative"

    run_card = {
        "schema_version": "gems-parallel-run-card-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repository": "buffedlizard55-lab/GEMSDOE86",
        "lane_id": "H86-FVMB",
        "ok_to_download_and_submit": all_gates_ok,
        "verdict": verdict,
        "experiments_executed": 3,
        "budget_limit_experiments": 3,
        "elapsed_wall_seconds": round(time.time() - t_start, 2),
        "weekly_submission_slots_used": 0,
        "hypothesis": (
            "Blind and under-mapped Quaternary faults in the NW Great Basin act as episodically breaching "
            "Sibson hydrothermal fault-valves and asymmetric Mode-II/III (±22 deg) wing-crack / step-over "
            "relays whose subsurface geometry is jointly resolved by dual Magnetic-Gravity Source Parameter "
            "Imaging (iSPI) local-wavenumber ridges projected up-dip via cot(60 deg) basement-depth pullback."
        ),
        "mechanism": (
            "60-channel label-free multi-physics stack (dual B9/B3 magnetic & B11/B18 gravity iSPI local "
            "wavenumber ridges with cot(60) up-dip projection, high-pass RTP magnetite-destruction troughs x "
            "GeoDAWN K/Th metasomatism x MT clay-cap B17 x INGENIOUS 2m temperature probe F2mDAB x paleo-sinter "
            "seals x GDR 1391 geothermometers, 1m/3m/10m scarps, and fluvial chi/ksn knickzones) coupled with "
            "12 fold-strict ±22-deg wing-crack / relay-bridge / antithetic-twin FFT channels in a counterfactual "
            "component-withheld 3-family SAR-PU LOQO ensemble (LightGBM + HistGradientBoosting + MLP) with "
            "8-stratum (Quadrant x 1m-LiDAR-Seam) Bayes calibration and exact 25-cell 300 m Dinkelbach-Minoux "
            "submodular expected-DTI allocation."
        ),
        "named_non_fault_mimic": (
            "Pleistocene Lake Lahontan (~1,332 m ASL) and Lake Bonneville (~1,463 / 1,552 m ASL) wave-cut "
            "paleoshoreline benches, flat basalt flow rims, and US Census TIGER highway/railroad embankments — "
            "explicitly rejected via along-scarp elevation climb variance sigma_9(z_ASL)/(|grad z_ASL|+3m), "
            "subsurface iSPI silence gating, and road-proximity x scarp interaction decontamination."
        ),
        "holdout_dti": {
            "label": (
                f"HOLDOUT-DTI ({EH.VERSION}, n={dual_hero['withheld_positive_pixels']}, "
                f"95% CI [{dual_hero['ci95'][0]:.6f}, {dual_hero['ci95'][1]:.6f}])"
            ),
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dual_seed_pooled_dti": round(float(dual_hero["dti"]), 6),
            "dual_seed_ci95": [round(float(x), 6) for x in dual_hero["ci95"]],
            "dual_seed_withheld_positives": int(dual_hero["withheld_positive_pixels"]),
            "seed_20_dti": round(
                float(holdout_res["per_seed"]["seed_20"]["scores"]["EXP86_3_FVMB_TriRegime_Dink"]["dti"]), 6
            ),
            "seed_20_ci95": [
                round(float(x), 6)
                for x in holdout_res["per_seed"]["seed_20"]["scores"]["EXP86_3_FVMB_TriRegime_Dink"]["ci95"]
            ],
            "seed_20_withheld_positives": int(
                holdout_res["per_seed"]["seed_20"]["scores"]["EXP86_3_FVMB_TriRegime_Dink"]["withheld_positive_pixels"]
            ),
            "seed_21_dti": round(
                float(holdout_res["per_seed"]["seed_21"]["scores"]["EXP86_3_FVMB_TriRegime_Dink"]["dti"]), 6
            ),
            "seed_21_ci95": [
                round(float(x), 6)
                for x in holdout_res["per_seed"]["seed_21"]["scores"]["EXP86_3_FVMB_TriRegime_Dink"]["ci95"]
            ],
            "detached_blind_splay_seed20_dti": round(
                float(holdout_res["detached_blind_splay_seed20"]["scores"]["EXP86_3_FVMB_TriRegime_Dink"]["dti"]), 6
            ),
            "ablation_ladder_dual_seed": {
                k: {
                    "dti": round(float(v["dti"]), 6),
                    "ci95": [round(float(x), 6) for x in v["ci95"]],
                }
                for k, v in holdout_res["dual_seed_pooled"]["scores"].items()
            },
            "paired_delta_vs_controls": {
                k: {
                    "delta": round(float(v["delta"]), 6),
                    "ci95": [round(float(x), 6) for x in v["ci95"]],
                }
                for k, v in holdout_res["dual_seed_pooled"]["paired_differences"].items()
            },
        },
        "leakage_canary": {
            "passed": canary["passed"],
            "channels_tested": canary["n_channels_tested"],
            "max_symmetric_auc": canary["max_symmetric_auc"],
            "max_channel": canary["max_symmetric_channel"],
            "ceiling": 0.90,
        },
        "correlation_overlap_vs_registry": {
            "rasters_checked": uniq["rasters_checked"],
            "pre_placement_surface_unique": surf_unique,
            "pre_placement_max_abs_spearman": round(
                float(uniq["pre_placement_surface"]["binding_decision"]["worst_abs_spearman"]), 6
            ),
            "pre_placement_max_3px_overlap": round(
                float(uniq["pre_placement_surface"]["binding_decision"]["worst_forward_overlap"]), 6
            ),
            "final_dots_unique": dots_unique,
            "final_dots_max_abs_spearman": round(
                float(uniq["final_emitted_dots"]["binding_decision"]["worst_abs_spearman"]), 6
            ),
            "final_dots_max_spearman_peer": uniq["final_emitted_dots"]["binding_decision"]["worst_abs_spearman_file"],
            "final_dots_max_3px_overlap": round(
                float(uniq["final_emitted_dots"]["binding_decision"]["worst_forward_overlap"]), 6
            ),
            "final_dots_max_overlap_peer": uniq["final_emitted_dots"]["binding_decision"]["worst_forward_overlap_file"],
            "spearman_limit": 0.90,
            "overlap_3px_limit": 0.70,
        },
        "submission_artifact": {
            "tif_file": f"docs/downloads/{stem}.tif",
            "tif_submissions_copy": f"submissions/{stem}.tif",
            "tif_bytes": writer_receipt["bytes"],
            "raster_sha256": writer_receipt["sha256"],
            "zip_file": f"docs/downloads/{stem}.zip",
            "zip_bytes": (SUB_DIR / f"{stem}.zip").stat().st_size,
            "zip_sha256": writer_receipt["zip_sha256"],
            "emitted_positive_pixels": n_dots,
            "footprint_fraction": val_receipt["footprint_fraction"],
            "nw_ne_dot_fraction": nw_ne_frac,
            "non_lidar_24pct_dot_fraction": non_lidar_dots_frac,
            "min_distance_to_catalogue_px": round(float(d_cat[prod_dots > 0].min()), 4),
            "median_distance_to_catalogue_px": round(float(np.median(d_cat[prod_dots > 0])), 4),
            "submission_name": sub_name,
            "submission_note": sub_note,
            "submission_note_chars": len(sub_note),
        },
        "validator_output": val_receipt,
    }

    (ROOT / "run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    (DOCS_DATA_DIR / "run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    (EVID_DIR / "h86_run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")

    log("=" * 76)
    log(f"FINAL VERDICT: {verdict.upper()} | OK_TO_SUBMIT={all_gates_ok}")
    log(f"Artifact: docs/downloads/{stem}.tif (sha256={writer_receipt['sha256'][:16]}…, {n_dots:,} dots)")
    log(f"Dual-Seed HOLDOUT-DTI: {dual_hero['dti']:.6f} CI=[{dual_hero['ci95'][0]:.6f}, {dual_hero['ci95'][1]:.6f}]")
    log(f"Note ({len(sub_note)}/140 chars): {sub_note}")
    log("=" * 76)


if __name__ == "__main__":
    main()
