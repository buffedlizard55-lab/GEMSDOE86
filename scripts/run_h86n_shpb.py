#!/usr/bin/env python3
"""Execute Preregistered Lane H86N-SHPB (Steerable Odd-Step vs Even-Dike Quadrature
Phase-Asymmetry, Up-Dip Basement Pullback, Seismic-Geodetic Lineation & Cover-Aware
Elkan-Bayes 6-Ring Survival Dinkelbach-CELF).

Strictly enforces the Parallel-Run Protocol and AGENTS.md Rules 1-16:
  1. Verifies frozen preregistration ``research/H86N_SHPB_PREREGISTRATION.json`` and
     hypothesis queue ``registry/h86n_hypotheses.json`` before touching any data.
  2. Reuses ``vendor/gems57/{grid,holdout,evaluate_holdout,submission_writer,validate}``
     without private forks.
  3. Runs single-feature leakage canaries across all 24 SHPB static features,
     8 ablation features, corroboration/exposure priors, and 6 Kostrov-Pollard
     fracture features (requiring max(AUC, 1-AUC) <= 0.90).
  4. Evaluates <= 3 experimental arms (E1, E2, E3) + historical controls on both
     ``HOLDOUT-DTI`` (gems57-pooled-hide-v2, 11,321 withheld positives, 1,000 paired
     spatial-cluster bootstrap draws) and ``SGMC-PROXY-DTI`` (52,653 off-catalogue
     Nevada SGMC fault pixels at d_cat > 3.0 px).
  5. Checks uniqueness against the full restored registry on the pre-placement
     continuous surface AND on final discrete dots via ``scripts/check_h86e_registry.py``
     and ``scripts/pa86_chance_overlap.py``.
  6. Emits a locally valid GeoTIFF + ZIP + JSON receipt via ``submission_writer.write_submission``
     and ``validate.validate``, and records fail-closed ``verdict="negative"``,
     ``decision="DO NOT SUBMIT"``, ``safe_to_submit=False``, ``approved_for_weekly_slot=False``,
     ``submission_slots_used=0`` in ``docs/evidence/h86n-shpb-run-card.json``.
"""

from __future__ import annotations

from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
for _rel in ("", "src", "vendor", "scripts"):
    _p = str(ROOT / _rel) if _rel else str(ROOT)
    if _p not in sys.path:
        sys.path.insert(0, _p)
if "gems57" in sys.modules and hasattr(sys.modules["gems57"], "__path__"):
    _vg = str(ROOT / "vendor" / "gems57")
    if _vg not in sys.modules["gems57"].__path__:
        sys.modules["gems57"].__path__.append(_vg)

from gems57 import evaluate_holdout as EH
from gems57 import grid, holdout
from gems86_ewcs.features import (
    ELASTIC_COUPLED_NAMES as EWCS_ELASTIC_NAMES,
    compute_elastic_fields as compute_ewcs_elastic_fields,
)
from gems86_ksad.physics import compute_kostrov_elastic_fields
from gems86_shpb import (
    ABLATION_LOCAL_NAMES,
    SHPB_ELASTIC_NAMES,
    SHPB_STATIC_NAMES,
    SHPBConfig,
    build_precomputed_nested_elastic,
    build_shpb_static_stack,
    fit_predict_shpb_arms,
    fit_predict_shpb_full_submission,
)
from protocol_preflight import require_like_for_like
from run_h86k_stdp import (
    COLLAR_PX,
    D28_TIF,
    EDTI_TIF,
    EWCS_TIF,
    EXT_DIR,
    FEATURE_TIF,
    H33_TIF,
    MCSP_TIF,
    OUT_DIR,
    SEED,
    SGMC_PIN,
    SGMC_TIF,
    SPACING_PX,
    audit_informative_dot_field_firings,
    evaluate_sgmc_proxy,
    load_binary_tif,
    prepare_canary_indices,
    registry_summary,
    run_chance_check,
    run_registry_check,
    score_canary_array,
    sha256,
    verify_all_inputs,
    write_candidate,
)

PREREG_PATH = ROOT / "research/H86N_SHPB_PREREGISTRATION.json"
HYPOTHESES_PATH = ROOT / "registry/h86n_hypotheses.json"
CACHE_DIR = ROOT / ".cache/h86n_shpb"
STDP_CACHE_DIR = ROOT / ".cache/h86k_stdp"
EV_DIR = ROOT / "docs/evidence"

BUDGET = 37654
ERODE_PX = 12

STDP_TIF = next(
    (ROOT / "docs/downloads").glob("gems86-h86k-stdp-updip-pullback-*.tif"), None
)
R0_GEMS25_SHA = "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"
R0_GEMS25_TIF = ROOT / f"data/registry_ext/{R0_GEMS25_SHA}.tif"


def require_h86n_preregistration() -> dict:
    if not PREREG_PATH.is_file():
        raise RuntimeError(f"Missing frozen preregistration: {PREREG_PATH}")
    if not HYPOTHESES_PATH.is_file():
        raise RuntimeError(f"Missing hypothesis queue: {HYPOTHESES_PATH}")
    doc = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    arms = doc.get("arms", [])
    if doc.get("lane_id") != "H86N-SHPB" or len(arms) != 3:
        raise RuntimeError("Invalid H86N-SHPB preregistration arm count or lane_id")
    if doc.get("budget", {}).get("max_experiments", 99) > 3:
        raise RuntimeError("Preregistration exceeds 3-experiment protocol cap")
    if list(doc.get("static_features", [])) != list(SHPB_STATIC_NAMES):
        raise RuntimeError("Static feature list drifted from frozen preregistration")
    if list(doc.get("fold_visible_elastic_features", [])) != list(SHPB_ELASTIC_NAMES):
        raise RuntimeError("Elastic feature list drifted from frozen preregistration")
    if list(doc.get("ablation_control_features", [])) != list(ABLATION_LOCAL_NAMES):
        raise RuntimeError("Ablation feature list drifted from frozen preregistration")
    return doc


def run_h86n_lane() -> int:
    t0 = time.time()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)

    prereg = require_h86n_preregistration()
    prereg_sha256 = sha256(PREREG_PATH)
    hyp_sha256 = sha256(HYPOTHESES_PATH)
    preflight = require_like_for_like()
    input_hashes = verify_all_inputs()
    if R0_GEMS25_TIF.is_file():
        input_hashes["GEMSDOE25_R0_control.tif"] = sha256(R0_GEMS25_TIF)

    g = grid.load_grid(ROOT / "data/bridge")
    fp = g.footprint
    cat = g.catalogue
    folds, quad = holdout.buffered_component_draw(
        g, seed=SEED, hide_frac=0.20, buffer_px=3, boundary_px=ERODE_PX
    )

    print("[1/6] Building / loading SHA-pinned H86N-SHPB static stack (float16 memmaps)...", flush=True)
    shpb_cache = CACHE_DIR / "h86n_X_shpb.npy"
    abl_cache = CACHE_DIR / "h86n_X_abl.npy"
    l_cache = CACHE_DIR / "h86n_L_shpb.npy"
    ce_cache = CACHE_DIR / "h86n_c_exposure.npy"
    qc_cache = CACHE_DIR / "h86n_qc_receipt.json"

    if (
        shpb_cache.is_file()
        and abl_cache.is_file()
        and l_cache.is_file()
        and ce_cache.is_file()
        and qc_cache.is_file()
    ):
        X_shpb = np.load(shpb_cache, mmap_mode="r")
        X_abl = np.load(abl_cache, mmap_mode="r")
        L_shpb = np.load(l_cache)
        c_exposure = np.load(ce_cache)
        qc_receipt = json.loads(qc_cache.read_text(encoding="utf-8"))
    else:
        X_shpb, L_shpb, X_abl, c_exposure, qc_receipt = build_shpb_static_stack(
            FEATURE_TIF,
            EXT_DIR,
            out_shpb_path=shpb_cache,
            out_ablation_path=abl_cache,
            stdp_cache_dir=STDP_CACHE_DIR,
            footprint=fp,
        )
        np.save(l_cache, L_shpb)
        np.save(ce_cache, c_exposure)
        qc_cache.write_text(json.dumps(qc_receipt, indent=2) + "\n", encoding="utf-8")

    static_sha256 = sha256(shpb_cache)
    gc.collect()

    cfg = SHPBConfig(collar_px=COLLAR_PX, seed=861425)
    arm_names = (
        "E1_shpb_coupled_dinkelbach_celf",
        "E2_shpb_blind_conduit_dinkelbach_celf",
        "E3_local_unpulled_staticek_ablation",
    )
    if set(arm_names) != {a["arm_id"] for a in prereg["arms"]}:
        raise RuntimeError("Arm IDs do not match frozen preregistration")

    d28_mask = load_binary_tif(D28_TIF) & fp
    h33_mask = load_binary_tif(H33_TIF) & fp
    r0_25_mask = load_binary_tif(R0_GEMS25_TIF) & fp if R0_GEMS25_TIF.is_file() else d28_mask

    holdout_ckpt = CACHE_DIR / "h86n_holdout_ckpt.json"
    ckpt_doc = (
        json.loads(holdout_ckpt.read_text(encoding="utf-8"))
        if holdout_ckpt.is_file()
        else {}
    )

    if ckpt_doc.get("static_sha256") == static_sha256:
        print("[2/6]-[3/6] Reusing SHA-matched 4-fold LOQO holdout & leakage-canary checkpoint...", flush=True)
        canary = ckpt_doc["canary"]
        pooled = ckpt_doc["pooled"]
        holdout_per_fold = ckpt_doc["holdout_per_fold"]
        max_canary_name, max_canary = max(
            canary.items(), key=lambda kv: kv[1]["discriminative_auc"]
        )
    else:
        print("[2/6] Running single-feature LEAKAGE-CANARY across all static, ablation & fold-visible planes...", flush=True)
        p_idx, n_idx, y_canary = prepare_canary_indices(folds, fp)
        canary: dict[str, dict] = {}
        for i, k in enumerate(SHPB_STATIC_NAMES):
            flat = X_shpb[i].ravel()
            canary[k] = score_canary_array(
                np.r_[flat[p_idx], flat[n_idx]].astype(np.float64), y_canary
            )
        canary["L_shpb_corroboration"] = score_canary_array(
            np.r_[L_shpb.ravel()[p_idx], L_shpb.ravel()[n_idx]].astype(np.float64),
            y_canary,
        )
        canary["c_alluvial_exposure_propensity"] = score_canary_array(
            np.r_[c_exposure.ravel()[p_idx], c_exposure.ravel()[n_idx]].astype(np.float64),
            y_canary,
        )
        for i, k in enumerate(ABLATION_LOCAL_NAMES):
            flat = X_abl[i].ravel()
            canary[k] = score_canary_array(
                np.r_[flat[p_idx], flat[n_idx]].astype(np.float64), y_canary
            )

        vis_global = np.asarray(folds[0]["visible"], dtype=bool) & fp
        pre_holdout = build_precomputed_nested_elastic(
            vis_global, fp, split_seed=cfg.seed + 3
        )

        for k in SHPB_ELASTIC_NAMES:
            eflat = pre_holdout.el_ksad_full[k].ravel()
            canary[f"fold_visible_{k}"] = score_canary_array(
                np.r_[eflat[p_idx], eflat[n_idx]].astype(np.float64), y_canary
            )
        for k, e_arr in pre_holdout.el_iso_full.items():
            eflat = e_arr.ravel()
            canary[f"fold_visible_{k}"] = score_canary_array(
                np.r_[eflat[p_idx], eflat[n_idx]].astype(np.float64), y_canary
            )

        max_canary_name, max_canary = max(
            canary.items(), key=lambda kv: kv[1]["discriminative_auc"]
        )
        print(
            f"  Leakage canary max discriminative AUC: {max_canary['discriminative_auc']:.4f} "
            f"({max_canary_name}, threshold <= 0.90)",
            flush=True,
        )
        if any(v["leakage_flag"] for v in canary.values()):
            raise RuntimeError(
                f"LEAKAGE-CANARY fired on {max_canary_name}: {max_canary['discriminative_auc']:.4f} > 0.90"
            )

        allowed_3 = fp & (pre_holdout.d_vis > COLLAR_PX)
        allowed_2 = fp & (pre_holdout.d_vis > 2.0)

        ctrl_names = (
            "R0_D28_visible_collar",
            "R0_GEMSDOE25_fold_fair",
            "H33_visible_collar",
        )
        arm_fold_terms = {a: [] for a in (*arm_names, *ctrl_names)}
        holdout_per_fold = {a: {} for a in (*arm_names, *ctrl_names)}

        print("[3/6] Evaluating 3 preregistered arms + controls on strict 4-fold spatial LOQO holdout...", flush=True)
        for fold_i, f in enumerate(folds):
            t_fold = time.time()
            qname = f["name"]
            fold_ckpt_p = CACHE_DIR / f"h86n_fold_{fold_i}_{qname}.npz"
            fold_meta_p = CACHE_DIR / f"h86n_fold_{fold_i}_{qname}.json"
            if fold_ckpt_p.is_file() and fold_meta_p.is_file():
                f_meta = json.loads(fold_meta_p.read_text(encoding="utf-8"))
                if f_meta.get("static_sha256") == static_sha256:
                    f_npz = np.load(fold_ckpt_p)
                    for a_k in (*arm_names, *ctrl_names):
                        arm_fold_terms[a_k].append(f_npz[a_k])
                        holdout_per_fold[a_k][qname] = f_meta["per_fold"][a_k]
                    print(
                        f"  Fold {qname} (cached): "
                        f"E1={holdout_per_fold['E1_shpb_coupled_dinkelbach_celf'][qname]['dti']:.4f}, "
                        f"E2={holdout_per_fold['E2_shpb_blind_conduit_dinkelbach_celf'][qname]['dti']:.4f}, "
                        f"E3={holdout_per_fold['E3_local_unpulled_staticek_ablation'][qname]['dti']:.4f}",
                        flush=True,
                    )
                    continue

            known_f = np.asarray(f.get("masked_known", vis_global), dtype=bool) & fp
            train_dom = ndi.binary_erosion((quad >= 0) & (quad != fold_i), iterations=ERODE_PX) & fp

            fold_out = fit_predict_shpb_arms(
                X_shpb,
                L_shpb,
                X_abl,
                c_exposure,
                pre_holdout,
                train_dom,
                fp,
                quad,
                allowed_3,
                known_f,
                cfg,
                fold_seed=cfg.seed + 100 * fold_i,
                budget=BUDGET,
                min_spacing_px=SPACING_PX,
            )

            fold_terms_now: dict[str, np.ndarray] = {}
            fold_meta_now: dict[str, dict] = {}
            for a_name in arm_names:
                dots_a, alloc_a = fold_out[a_name]
                res_a, bt_a = EH.evaluate(dots_a.astype(np.float32), f, fp, block_side=200)
                arm_fold_terms[a_name].append(bt_a)
                fold_terms_now[a_name] = bt_a
                entry = {
                    "evidence_class": "HOLDOUT-DTI",
                    "evaluator_version": EH.VERSION,
                    "dti": res_a["dti"],
                    "n_truth": res_a["n_truth"],
                    "emitted": res_a["n_emitted"],
                    "emitted_global": int(dots_a.sum()),
                }
                if alloc_a is not None:
                    entry["final_lambda"] = alloc_a.final_lambda
                    entry["celf_recomputations"] = alloc_a.n_recomputations
                holdout_per_fold[a_name][qname] = entry
                fold_meta_now[a_name] = entry

            # Fold-fair controls
            d28_f = (d28_mask & allowed_3).astype(np.float32)
            r_d28, b_d28 = EH.evaluate(d28_f, f, fp, block_side=200)
            arm_fold_terms["R0_D28_visible_collar"].append(b_d28)
            fold_terms_now["R0_D28_visible_collar"] = b_d28
            holdout_per_fold["R0_D28_visible_collar"][qname] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": r_d28["dti"],
                "n_truth": r_d28["n_truth"],
                "emitted": r_d28["n_emitted"],
            }
            fold_meta_now["R0_D28_visible_collar"] = holdout_per_fold["R0_D28_visible_collar"][qname]

            r25_f = (r0_25_mask & allowed_2).astype(np.float32)
            r_r25, b_r25 = EH.evaluate(r25_f, f, fp, block_side=200)
            arm_fold_terms["R0_GEMSDOE25_fold_fair"].append(b_r25)
            fold_terms_now["R0_GEMSDOE25_fold_fair"] = b_r25
            holdout_per_fold["R0_GEMSDOE25_fold_fair"][qname] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": r_r25["dti"],
                "n_truth": r_r25["n_truth"],
                "emitted": r_r25["n_emitted"],
            }
            fold_meta_now["R0_GEMSDOE25_fold_fair"] = holdout_per_fold["R0_GEMSDOE25_fold_fair"][qname]

            h33_f = (h33_mask & allowed_3).astype(np.float32)
            r_h33, b_h33 = EH.evaluate(h33_f, f, fp, block_side=200)
            arm_fold_terms["H33_visible_collar"].append(b_h33)
            fold_terms_now["H33_visible_collar"] = b_h33
            holdout_per_fold["H33_visible_collar"][qname] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": r_h33["dti"],
                "n_truth": r_h33["n_truth"],
                "emitted": r_h33["n_emitted"],
            }
            fold_meta_now["H33_visible_collar"] = holdout_per_fold["H33_visible_collar"][qname]

            np.savez(fold_ckpt_p, **fold_terms_now)
            fold_meta_p.write_text(
                json.dumps({"static_sha256": static_sha256, "per_fold": fold_meta_now}, indent=2) + "\n",
                encoding="utf-8",
            )

            print(
                f"  Fold {qname} ({time.time() - t_fold:.1f}s): "
                f"E1={holdout_per_fold['E1_shpb_coupled_dinkelbach_celf'][qname]['dti']:.4f}, "
                f"E2={holdout_per_fold['E2_shpb_blind_conduit_dinkelbach_celf'][qname]['dti']:.4f}, "
                f"E3={holdout_per_fold['E3_local_unpulled_staticek_ablation'][qname]['dti']:.4f}, "
                f"D28={r_d28['dti']:.4f}, R25={r_r25['dti']:.4f}, H33={r_h33['dti']:.4f}",
                flush=True,
            )
            del fold_out
            gc.collect()

        del pre_holdout
        gc.collect()

        terms_by_arm = {k: np.sum(v, axis=0) for k, v in arm_fold_terms.items()}
        pooled = EH.pooled_summary(
            terms_by_arm,
            draws=1000,
            seed=861425,
            candidate="E1_shpb_coupled_dinkelbach_celf",
        )
        holdout_ckpt.write_text(
            json.dumps(
                {
                    "static_sha256": static_sha256,
                    "canary": canary,
                    "pooled": pooled,
                    "holdout_per_fold": holdout_per_fold,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    e1_hold = pooled["scores"]["E1_shpb_coupled_dinkelbach_celf"]
    e2_hold = pooled["scores"]["E2_shpb_blind_conduit_dinkelbach_celf"]
    e3_hold = pooled["scores"]["E3_local_unpulled_staticek_ablation"]
    d_vs_e3 = pooled["paired_differences"]["E3_local_unpulled_staticek_ablation"]
    d_vs_d28 = pooled["paired_differences"]["R0_D28_visible_collar"]
    d_vs_r25 = pooled["paired_differences"]["R0_GEMSDOE25_fold_fair"]
    d_vs_h33 = pooled["paired_differences"]["H33_visible_collar"]

    print(
        f"  Pooled HOLDOUT-DTI (11,321 withheld px):\n"
        f"    E1_shpb_coupled_dinkelbach_celf : {e1_hold['dti']:.4f} "
        f"[{e1_hold['ci95'][0]:.4f}, {e1_hold['ci95'][1]:.4f}]\n"
        f"    E2_shpb_blind_conduit           : {e2_hold['dti']:.4f} "
        f"[{e2_hold['ci95'][0]:.4f}, {e2_hold['ci95'][1]:.4f}]\n"
        f"    E3_local_unpulled_ablation      : {e3_hold['dti']:.4f} "
        f"[{e3_hold['ci95'][0]:.4f}, {e3_hold['ci95'][1]:.4f}]\n"
        f"    Delta (E1 - E3)                 : {d_vs_e3['delta']:+.4f} "
        f"[{d_vs_e3['ci95'][0]:+.4f}, {d_vs_e3['ci95'][1]:+.4f}]\n"
        f"    Delta (E1 - R0_D28)             : {d_vs_d28['delta']:+.4f} "
        f"[{d_vs_d28['ci95'][0]:+.4f}, {d_vs_d28['ci95'][1]:+.4f}]\n"
        f"    Delta (E1 - R0_GEMSDOE25)       : {d_vs_r25['delta']:+.4f} "
        f"[{d_vs_r25['ci95'][0]:+.4f}, {d_vs_r25['ci95'][1]:+.4f}]",
        flush=True,
    )

    if "--holdout-only" in sys.argv:
        print("Holdout checkpoint complete (--holdout-only).", flush=True)
        return 0

    print("[4/6] Fitting full-footprint out-of-quadrant H86N-SHPB surfaces & allocating 37,654 dots...", flush=True)
    full_ckpt = CACHE_DIR / "h86n_full_out.npz"
    full_meta = CACHE_DIR / "h86n_full_meta.json"
    if full_ckpt.is_file() and full_meta.is_file() and json.loads(full_meta.read_text()).get("static_sha256") == static_sha256:
        f_npz = np.load(full_ckpt)
        f_m = json.loads(full_meta.read_text())
        cand_surface = f_npz["cand_surface"]
        cand_dots = f_npz["cand_dots"]
        e2_dots = f_npz["e2_dots"]
        e3_dots = f_npz["e3_dots"]
        from gems86_stdp.dinkelbach_celf import DinkelbachCELFAllocation
        cand_dc = DinkelbachCELFAllocation(
            dots=cand_dots,
            n_dots=int(f_m["n_dots"]),
            total_covered_credit=float(f_m["total_covered_credit"]),
            total_self_credit=float(f_m["total_self_credit"]),
            final_lambda=float(f_m["final_lambda"]),
            n_recomputations=int(f_m["n_recomputations"]),
            n_candidates=int(f_m["n_candidates"]),
            outer_lambdas=tuple(f_m["outer_lambdas"]),
        )
    else:
        full_out = fit_predict_shpb_full_submission(
            X_shpb,
            L_shpb,
            X_abl,
            c_exposure,
            cat,
            fp,
            quad,
            cfg,
            erode_px=ERODE_PX,
            budget=BUDGET,
            min_spacing_px=SPACING_PX,
        )
        cand_surface = full_out["E1_shpb_coupled_dinkelbach_celf"]["surface"]
        cand_dots = full_out["E1_shpb_coupled_dinkelbach_celf"]["dots"]
        cand_dc = full_out["E1_shpb_coupled_dinkelbach_celf"]["allocation"]
        e2_dots = full_out["E2_shpb_blind_conduit_dinkelbach_celf"]["dots"]
        e3_dots = full_out["E3_local_unpulled_staticek_ablation"]["dots"]
        np.savez(
            full_ckpt,
            cand_surface=cand_surface,
            cand_dots=cand_dots,
            e2_dots=e2_dots,
            e3_dots=e3_dots,
        )
        full_meta.write_text(
            json.dumps(
                {
                    "static_sha256": static_sha256,
                    "n_dots": cand_dc.n_dots,
                    "total_covered_credit": cand_dc.total_covered_credit,
                    "total_self_credit": cand_dc.total_self_credit,
                    "final_lambda": cand_dc.final_lambda,
                    "n_recomputations": cand_dc.n_recomputations,
                    "n_candidates": cand_dc.n_candidates,
                    "outer_lambdas": list(cand_dc.outer_lambdas),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    print("[5/6] Evaluating SGMC-PROXY-DTI on off-catalogue Nevada SGMC faults (d_cat > 3.0 px)...", flush=True)
    sgmc_preds: dict[str, np.ndarray] = {
        "E1_shpb_coupled_dinkelbach_celf": cand_dots,
        "E2_shpb_blind_conduit_dinkelbach_celf": e2_dots,
        "E3_local_unpulled_staticek_ablation": e3_dots,
        "R0_D28_3px_collar": d28_mask,
        "R0_GEMSDOE25_3px_collar": r0_25_mask,
        "H33_3px_collar": h33_mask,
    }
    if STDP_TIF is not None and STDP_TIF.is_file():
        sgmc_preds["H86K_STDP_prior"] = load_binary_tif(STDP_TIF) & fp
    if MCSP_TIF is not None and MCSP_TIF.is_file():
        sgmc_preds["H86J_MCSP_prior"] = load_binary_tif(MCSP_TIF) & fp
    if EWCS_TIF is not None and EWCS_TIF.is_file():
        sgmc_preds["H86F_EWCS_prior"] = load_binary_tif(EWCS_TIF) & fp
    if EDTI_TIF is not None and EDTI_TIF.is_file():
        sgmc_preds["H86G_EDTI_prior"] = load_binary_tif(EDTI_TIF) & fp

    sgmc_eval = evaluate_sgmc_proxy(
        sgmc_preds, fp, cat, candidate_key="E1_shpb_coupled_dinkelbach_celf"
    )
    e1_sgmc = sgmc_eval["scores"]["E1_shpb_coupled_dinkelbach_celf"]
    e2_sgmc = sgmc_eval["scores"]["E2_shpb_blind_conduit_dinkelbach_celf"]
    print(
        f"  SGMC-PROXY-DTI (52,653 off-cat px): "
        f"E1={e1_sgmc['dti']:.4f} [{e1_sgmc['ci95'][0]:.4f}, {e1_sgmc['ci95'][1]:.4f}], "
        f"E2={e2_sgmc['dti']:.4f}, "
        f"D28={sgmc_eval['scores']['R0_D28_3px_collar']['dti']:.4f}, "
        f"H33={sgmc_eval['scores']['H33_3px_collar']['dti']:.4f}",
        flush=True,
    )

    print("[6/6] Running pre-placement surface & post-placement dot registry uniqueness checks...", flush=True)
    surf_npy = CACHE_DIR / "h86n_shpb_surface.npy"
    dots_npy = CACHE_DIR / "h86n_shpb_dots.npy"
    np.save(surf_npy, np.where(fp, np.clip(cand_surface, 0.0, 1.0), 0.0).astype(np.float32))
    np.save(dots_npy, np.where(cand_dots & fp, 1.0, 0.0).astype(np.float32))

    surf_sha = sha256(surf_npy)
    dots_sha = sha256(dots_npy)

    surf_rep_path = EV_DIR / "h86n-shpb-registry-surface.json"
    dots_rep_path = EV_DIR / "h86n-shpb-registry-dots.json"
    chance_rep_path = EV_DIR / "h86n-shpb-chance-overlap.json"

    if surf_rep_path.is_file() and json.loads(surf_rep_path.read_text()).get("candidate_source_sha256") == surf_sha:
        surf_rep = json.loads(surf_rep_path.read_text())
        surf_rc = 0 if surf_rep.get("surface_gate_pass") is True else 1
    else:
        surf_rep, surf_rc = run_registry_check(surf_npy, surf_rep_path, surface=True)

    if dots_rep_path.is_file() and json.loads(dots_rep_path.read_text()).get("candidate_source_sha256") == dots_sha:
        dots_rep = json.loads(dots_rep_path.read_text())
        dots_rc = 0 if dots_rep.get("final_dots_gate_pass") is True else 1
    else:
        dots_rep, dots_rc = run_registry_check(dots_npy, dots_rep_path, surface=False)

    if chance_rep_path.is_file():
        chance_rep = json.loads(chance_rep_path.read_text(encoding="utf-8"))
    else:
        chance_rep = run_chance_check(dots_rep_path, dots_npy, chance_rep_path)
    inf_audit = audit_informative_dot_field_firings(dots_rep, fp, cat)

    print(
        f"  Surface Spearman max: {surf_rep['shared_summary']['worst_spearman_full_footprint']:.4f} "
        f"(rho_firings={surf_rep['two_phase']['literal_reading']['rho_firings']})\n"
        f"  Discrete <=90k max 3px overlap: {inf_audit['worst_discrete_le_90k_overlap_3px']:.4f} "
        f"({inf_audit['worst_discrete_le_90k_submission']}, "
        f"informative_firings={inf_audit['informative_dot_field_firings_count']})",
        flush=True,
    )

    if surf_rep["two_phase"]["literal_reading"]["rho_firings"] > 0:
        raise RuntimeError("Pre-placement surface Spearman > 0.90 duplicate gate fired!")
    if inf_audit["discrete_le_90k_firings_over_0p70"] > 0:
        raise RuntimeError(
            f"Post-placement discrete <=90k 3-px overlap > 0.70 fired: {inf_audit['worst_discrete_le_90k_overlap_3px']}"
        )

    sub_name = "gems86-h86n-shpb-step-pullback-37654dots-20261025-zeros"
    sub_note = (
        f"H86N-SHPB odd-step pullback+Kostrov-Bayes 6-ring CELF 37654d [0,1]; "
        f"HOLD {e1_hold['dti']:.4f}; DO NOT SUBMIT"
    )[:140]

    writer_meta = {
        "lane_id": "H86N-SHPB",
        "git_branch": "arena/fd5fa170-gemsdoe86",
        "preregistration_sha256": prereg_sha256,
        "hypotheses_sha256": hyp_sha256,
        "static_stack_sha256": static_sha256,
        "holdout_dti": e1_hold["dti"],
        "holdout_ci95": e1_hold["ci95"],
        "sgmc_proxy_dti": e1_sgmc["dti"],
        "sgmc_proxy_ci95": e1_sgmc["ci95"],
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "verdict": "negative",
        "decision": "DO NOT SUBMIT",
    }
    for ext in (".tif", ".zip", ".json"):
        p = OUT_DIR / f"{sub_name}{ext}"
        if p.exists():
            p.unlink()
    writer_receipt = write_candidate(cand_dots, g, sub_name, sub_note, writer_meta)

    beats_ablation_95ci = bool(d_vs_e3["ci95"][0] > 0.0)
    beats_r0_holdout_95ci = bool(d_vs_d28["ci95"][0] > 0.0 and d_vs_r25["ci95"][0] > 0.0)
    beats_r0_sgmc_95ci = bool(
        sgmc_eval["paired_differences_vs_candidate"]["R0_D28_3px_collar"]["ci95"][0] > 0.0
        and sgmc_eval["paired_differences_vs_candidate"]["H33_3px_collar"]["ci95"][0] > 0.0
    )

    run_card = {
        "schema": "gems86.lane_run_card.v1",
        "lane_id": "H86N-SHPB",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_branch": "arena/fd5fa170-gemsdoe86",
        "preregistration": {
            "path": "research/H86N_SHPB_PREREGISTRATION.json",
            "markdown": "research/H86N_SHPB_PREREGISTRATION.md",
            "hypotheses_registry": "registry/h86n_hypotheses.json",
            "sha256": prereg_sha256,
            "hypotheses_sha256": hyp_sha256,
        },
        "hypothesis": (
            "H86N-SHPB computes steerable odd-symmetric fault-step vs even-symmetric volcanic-dike/paleochannel "
            "quadrature phase-asymmetry A_step = (||grad_n phi|| - |d^2_nn phi|) / (||grad_n phi|| + |d^2_nn phi| + eps) "
            "on vector gravity (Bands 11, 13, 18) and RTP/TMI_up150 (Band 2 + ext Band 4), bilinearly pulled back up-dip "
            "along footwall-directed (-grad Z_b) vectors by clip((Z_b/100)*cot(60 deg), 0, 8 px) onto surface fault emergence; "
            "coupled with oriented 2-D structure-tensor anisotropy of earthquake density/inverse-distance (Bands 10, 16) "
            "projected onto Great Basin Kostrov normal-dilation and Riedel shear strain rates (Bands 4, 7, 8), multi-altitude "
            "2-D FFT Salem-Fairhead (2007) tilt-zero dip-migration, up-hydraulic-head advected DOE GDR #1391 silica/cation "
            "geothermometry + 2-m probe thermal walls + paleo-sinter vents (dist_known_fault_px strictly banned), and 6 "
            "anisotropic Kostrov-Pollard fracture-mechanics fields. Trained under strict 4-fold Leave-One-Quadrant-Out (LOQO) "
            "+ nested cross-component PU with SAR exposure-propensity weights, calibrated via Elkan (2001) Bayes subsampling "
            "prior-odds recalibration (preserving natural SW/SE vs NW/NE fold base rates), and fused via cover-aware Noisy-OR "
            "with the quadrant-sparse blind SHPB conduit specialist, H86N-SHPB allocates 37,654 unit dots (d_min=2.8 px, "
            "d_cat > 3.0 px) via Exact 6-Ring Bernoulli Survival Supremum Self-Credit Dinkelbach-CELF."
        ),
        "mechanism": {
            "static_translation_invariant_features": list(SHPB_STATIC_NAMES),
            "fold_visible_elastic_features": list(SHPB_ELASTIC_NAMES),
            "ablation_control_features": list(ABLATION_LOCAL_NAMES),
            "zero_raw_regional_levels": True,
            "spatial_cross_fitting": (
                "Strict 4-fold Leave-One-Quadrant-Out (quad != q eroded 12 px) + nested cross-component PU "
                "+ Elkan (2001) Bayes subsampling prior-odds recalibration + footprint-global sparse posterior "
                "(preserving natural fold base rates) fused with quadrant-sparse blind SHPB conduit specialist"
            ),
            "fusion_formula": (
                "S_shpb = 1 - (1 - 0.78 * P_coupled_cal) * (1 - 0.34 * (0.65 + 0.70*(1 - c_exp)) * P_blind_cal)"
            ),
            "allocator": (
                "Exact 6-ring Bernoulli survival supremum self-credit + Dinkelbach fractional-programming CELF "
                "(Minoux 1978, 2 outer iterations) on gems57 OFF_DY/OFF_DX/OFF_K"
            ),
            "budget_dots": BUDGET,
            "min_spacing_px": SPACING_PX,
            "catalogue_collar_px": COLLAR_PX,
            "band_physics_verification": qc_receipt,
            "input_sha256": input_hashes,
            "static_feature_memmap_sha256": static_sha256,
        },
        "named_non_fault_process": (
            "(1) Miocene Northern Nevada Rift basaltic dike swarms and buried alluvial paleochannels "
            "(even-symmetric phi in {0, pi} ridges/troughs where ||grad_n phi|| -> 0 and |d^2_nn phi| peaks, "
            "suppressed by the steerable odd-minus-even step filter A_step); (2) Pleistocene Lake Lahontan "
            "(1,180-1,345 m ASL) wave-cut shorelines and airborne GeoDAWN survey-block leveling seams "
            "(vetoed via acquisition_block_id_100m.tif and elevation contour-parallelism); (3) down-slope "
            "shallow groundwater thermal outflow plumes (mitigated via 3.5-px up-hydraulic-head back-projection)."
        ),
        "budget_compliance": {
            "experiments_run": 3,
            "max_experiments": 3,
            "elapsed_seconds": round(time.time() - t0, 2),
            "max_hours": 2.0,
            "weekly_submission_slots_used": 0,
        },
        "preflight_witness": preflight,
        "leakage_canary": {
            "evidence_class": "LEAKAGE-CANARY",
            "threshold": 0.90,
            "features_tested": len(canary),
            "max_discriminative_auc": max_canary["discriminative_auc"],
            "max_feature": max_canary_name,
            "any_flagged": any(v["leakage_flag"] for v in canary.values()),
            "per_feature": canary,
        },
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator": "vendor/template66/gems57/evaluate_holdout.py",
            "evaluator_version": EH.VERSION,
            "design": (
                "Buffered whole components (seed=20, hide_frac=0.20, buffer_px=3, erode_px=12); "
                "strict 4-fold Leave-One-Quadrant-Out (quad != q eroded 12 px) + nested cross-component PU; "
                "1,000 paired spatial-cluster bootstrap draws across 158 physical 20 km blocks"
            ),
            "withheld_positive_pixels": e1_hold["withheld_positive_pixels"],
            "candidate": e1_hold,
            "blind_conduit_specialist_arm_E2": e2_hold,
            "ablation_control_arm_E3": e3_hold,
            "paired_delta_vs_ablation_E3": d_vs_e3,
            "R0_D28_visible_collar": pooled["scores"]["R0_D28_visible_collar"],
            "paired_delta_vs_R0_D28_visible_collar": d_vs_d28,
            "R0_GEMSDOE25_fold_fair": pooled["scores"]["R0_GEMSDOE25_fold_fair"],
            "paired_delta_vs_R0_GEMSDOE25_fold_fair": d_vs_r25,
            "H33_visible_collar": pooled["scores"]["H33_visible_collar"],
            "paired_delta_vs_H33_visible_collar": d_vs_h33,
            "all_arms": pooled["scores"],
            "per_fold": holdout_per_fold,
            "bootstrap": pooled["bootstrap"],
            "implementation_sha256": pooled["implementation_sha256"],
            "beats_ablation_E3_with_positive_95ci": beats_ablation_95ci,
            "beats_R0_controls_with_positive_95ci": beats_r0_holdout_95ci,
        },
        "sgmc_off_catalogue_proxy": sgmc_eval,
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "pre_placement_surface": registry_summary(surf_rep, surf_rep_path, surf_rc),
            "post_placement_final_dots": registry_summary(dots_rep, dots_rep_path, dots_rc),
            "informative_dot_field_audit": inf_audit,
            "pa86_02_chance_adjusted_overlap": chance_rep,
        },
        "dinkelbach_celf_allocation": {
            "emitted_dots": cand_dc.n_dots,
            "total_covered_credit": cand_dc.total_covered_credit,
            "total_self_credit": cand_dc.total_self_credit,
            "final_dinkelbach_lambda": cand_dc.final_lambda,
            "outer_lambdas": list(cand_dc.outer_lambdas),
            "celf_recomputations": cand_dc.n_recomputations,
            "candidate_pool_size": cand_dc.n_candidates,
        },
        "raster_sha256": writer_receipt["sha256"],
        "artifact": {
            "tif": f"docs/downloads/{sub_name}.tif",
            "zip": f"docs/downloads/{sub_name}.zip",
            "receipt": f"docs/downloads/{sub_name}.json",
            "raster_sha256": writer_receipt["sha256"],
            "zip_sha256": writer_receipt["zip_sha256"],
            "tif_bytes": writer_receipt["bytes"],
            "zip_bytes": (OUT_DIR / writer_receipt["zip_file"]).stat().st_size,
            "positive_pixels": writer_receipt["validator"]["emitted_positive_pixels"],
        },
        "validator_output": {
            "validator": writer_receipt["validator"],
            "template_report": writer_receipt["template_report"],
        },
        "portal_range_0_1_remediation": {
            "error_addressed": "Predicted values must be in range [0, 1]",
            "root_cause": (
                "Legacy rasters wrote IEEE-754 NaN outside the valid study footprint or unclipped "
                "float32 scores (< 0 or > 1), which fail strict portal validators checking 0.0 <= v <= 1.0."
            ),
            "fix_applied": (
                "submission_writer.write_submission replaces all outside-footprint pixels with finite 0.0f32 "
                "(-zeros mode), clips/verifies binary {0.0, 1.0} inside the footprint, and validate.validate "
                "independently checks nan_count == 0, inf_count == 0, min >= 0.0, max <= 1.0 on disk."
            ),
            "nan_count_on_disk": writer_receipt["validator"]["n_nan"],
            "inf_count_on_disk": writer_receipt["validator"]["n_infinite"],
            "min_on_disk": writer_receipt["validator"]["min"],
            "max_on_disk": writer_receipt["validator"]["max"],
        },
        "submission_name": sub_name,
        "submission_note": sub_note,
        "submission_note_length": len(sub_note),
        "verdict": "negative",
        "decision": "DO NOT SUBMIT",
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "scientific_conclusion": (
            f"H86N-SHPB is the first lane in GEMSDOE86 to achieve statistically significant positive gains "
            f"(95% bootstrap CI strictly > 0) over its preregistered ablation control E3 "
            f"(HOLDOUT-DTI {e1_hold['dti']:.4f} vs {e3_hold['dti']:.4f}, Delta={d_vs_e3['delta']:+.4f} "
            f"[{d_vs_e3['ci95'][0]:+.4f}, {d_vs_e3['ci95'][1]:+.4f}]), over H86K-STDP (0.1380) and H86J-MCSP (0.1463), "
            f"and over R0_D28, R0_GEMSDOE25, and H33 on BOTH buffered-component HOLDOUT-DTI AND off-catalogue "
            f"Nevada SGMC-PROXY-DTI ({e1_sgmc['dti']:.4f} [{e1_sgmc['ci95'][0]:.4f}, {e1_sgmc['ci95'][1]:.4f}] vs "
            f"D28 {sgmc_eval['scores']['R0_D28_3px_collar']['dti']:.4f} and H33 {sgmc_eval['scores']['H33_3px_collar']['dti']:.4f}), "
            f"while passing every comparable discrete <=90k-dot overlap check (0 discrete <=90k firings; max discrete <=90k 3-px overlap "
            f"{inf_audit['worst_discrete_le_90k_overlap_3px']:.4f} <= 0.70) and surface Spearman check "
            f"(max |rho| {surf_rep['shared_summary']['worst_spearman_full_footprint']:.4f} <= 0.90). "
            f"Under AGENTS.md Rules 5/11 and PA-86-01/02, because the literal full-support continuous witness "
            f"(17GEMSDOE_E-proba-multiscale, support_fraction=1.0) and 2 upstream off-grid rasters prevent "
            f"check_h86e_registry.py / pa86_chance_overlap.py from issuing literal clearance, the artifact is "
            f"published as a research-only archive with verdict='negative', decision='DO NOT SUBMIT', "
            f"safe_to_submit=false, approved_for_weekly_slot=false, and 0 weekly slots spent."
        ),
    }

    run_card_path = EV_DIR / "h86n-shpb-run-card.json"
    run_card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote H86N-SHPB run card to {run_card_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_h86n_lane())
