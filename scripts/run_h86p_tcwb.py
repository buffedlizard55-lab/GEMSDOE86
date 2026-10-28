#!/usr/bin/env python3
"""Execute Preregistered Lane H86P-TCWB (<= 3 Arms, Strict 4-Fold Eroded-LOQO).

Method lane:
  Downslope Radiometric Total-Count Wash-Blanket Asymmetry x Vector-Gravity-Signed
  Basement Hinge Kink x Lateral Hydrothermal Clay-Cap Fault-Seal Termination +
  Seismicity-Conditioned Dilatancy Gate & Aitchison CLR Radiometric Jacobian with
  4.5 px Stress-Shadow De-Crowded Elkan-Bayes LOQO, Radial-Cover Noisy-OR Fusion,
  and Exact 6-Ring Bernoulli Survival Dinkelbach-CELF Allocation.

Following the repository-wide builder gating merged in PR #98, ``main()`` now calls
``protocol_preflight.require_feasible()`` before any work.
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
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
VENDOR = ROOT / "vendor"
for _p in (str(ROOT), str(SRC), str(VENDOR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gems57 import grid, holdout
from gems86_ewcs.features import compute_elastic_fields as compute_ewcs_elastic_fields
from gems86_ksad.physics import compute_kostrov_elastic_fields
from gems86_stdp.dinkelbach_celf import (
    dinkelbach_celf_allocate_dots,
    static_ek_spacing_allocate,
)
from gems86_stdp.model import rank01_on_mask
from gems86_tcwb import (
    ABLATION_LOCAL_NAMES,
    TCWBConfig,
    TCWB_ELASTIC_NAMES,
    TCWB_STATIC_NAMES,
    build_tcwb_static_stack,
    fit_predict_loqo_tcwb_surfaces,
)
from scripts.protocol_preflight import require_feasible, require_like_for_like
from scripts.run_h86k_stdp import (
    BUDGET,
    COLLAR_PX,
    D28_TIF,
    EDTI_TIF,
    EH,
    EV_DIR,
    EWCS_TIF,
    EXT_DIR,
    FEATURE_TIF,
    H33_TIF,
    MCSP_TIF,
    OUT_DIR,
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

CACHE_DIR = ROOT / ".cache/h86p_tcwb"
PREREGISTRATION_PATH = ROOT / "research/H86P_TCWB_PREREGISTRATION.json"
STDP_TIF = next(
    iter(sorted((ROOT / "docs/downloads").glob("gems86-h86k-stdp-*.tif"))), None
)
SLCQ_TIF = next(
    iter(sorted((ROOT / "docs/downloads").glob("gems86-h86m-slcq-*.tif"))), None
)


def _quadrant_regions(fp: np.ndarray, vis_mask: np.ndarray) -> list[tuple[str, np.ndarray, np.ndarray]]:
    q_grid = holdout.quadrant_ids(fp)
    names = ("NW", "NE", "SW", "SE")
    return [(names[q], fp & (q_grid == q), vis_mask) for q in range(4)]


def run_pa86_lane() -> int:
    # Imported callers must obey the same literal stop as the CLI.
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    t0 = time.time()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)

    print(
        "[1/6] Verifying shared template pins, SHA-256 inputs, preregistration & PA-86-01 preflight...",
        flush=True,
    )
    if not PREREGISTRATION_PATH.is_file():
        raise RuntimeError(f"Missing frozen preregistration {PREREGISTRATION_PATH}")
    prereg = json.loads(PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    if prereg.get("lane_id") != "H86P-TCWB" or len(prereg.get("arms", [])) != 3:
        raise RuntimeError("Invalid H86P-TCWB preregistration")
    if list(prereg.get("static_features", [])) != list(TCWB_STATIC_NAMES):
        raise RuntimeError("Static feature list drifted from frozen preregistration")
    if list(prereg.get("fold_visible_elastic_features", [])) != list(TCWB_ELASTIC_NAMES):
        raise RuntimeError("Elastic feature list drifted from frozen preregistration")
    if list(prereg.get("ablation_control_features", [])) != list(ABLATION_LOCAL_NAMES):
        raise RuntimeError("Ablation feature list drifted from frozen preregistration")

    preflight = require_like_for_like()
    input_hashes = verify_all_inputs()

    g = grid.load_grid(ROOT / "data/bridge")
    fp = np.asarray(g.footprint, dtype=bool)
    cat = np.asarray(g.catalogue, dtype=bool)

    print(
        "[2/6] Building 26 H86P-TCWB static planes + 8 ablation planes + TCWB corroboration...",
        flush=True,
    )
    tcwb_mm_path = CACHE_DIR / "tcwb_static26.npy"
    abl_mm_path = CACHE_DIR / "ablation_local8.npy"
    extras_cache = CACHE_DIR / "tcwb_static_extras.npz"
    qc_cache = CACHE_DIR / "tcwb_qc.json"
    if (
        tcwb_mm_path.is_file()
        and abl_mm_path.is_file()
        and extras_cache.is_file()
        and qc_cache.is_file()
    ):
        ex = np.load(extras_cache)
        stack = {
            "X_tcwb": np.load(tcwb_mm_path, mmap_mode="r"),
            "X_abl": np.load(abl_mm_path, mmap_mode="r"),
            "L_tcwb": ex["L_tcwb"],
            "cover_propensity": ex["cover_propensity"],
            "valid": fp,
            "qc": json.loads(qc_cache.read_text(encoding="utf-8")),
        }
    else:
        stack = build_tcwb_static_stack(
            FEATURE_TIF,
            EXT_DIR,
            out_tcwb_path=tcwb_mm_path,
            out_ablation_path=abl_mm_path,
            footprint=fp,
        )
        np.savez(
            extras_cache,
            L_tcwb=stack["L_tcwb"],
            cover_propensity=stack["cover_propensity"],
        )
        qc_cache.write_text(json.dumps(stack["qc"], indent=2) + "\n", encoding="utf-8")
    qc_receipt = stack["qc"]
    static_sha256 = sha256(tcwb_mm_path)
    print(
        f"  Static stack ready ({time.time() - t0:.1f}s) | sha256={static_sha256[:16]}...",
        flush=True,
    )

    print(
        "[3/6] Running single-feature leakage canary & 3 preregistered arms on gems57-pooled-hide-v2...",
        flush=True,
    )
    folds, quad_check = holdout.buffered_component_draw(
        g, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12
    )
    p_idx, n_idx, y_canary = prepare_canary_indices(folds, fp)
    canary: dict[str, dict] = {}
    X_tcwb = stack["X_tcwb"]
    X_abl = stack["X_abl"]

    for i, fname in enumerate(TCWB_STATIC_NAMES):
        pl = X_tcwb[i].ravel()
        canary[fname] = score_canary_array(
            np.r_[pl[p_idx], pl[n_idx]].astype(np.float64), y_canary
        )
    canary["L_tcwb_corroboration"] = score_canary_array(
        np.r_[stack["L_tcwb"].ravel()[p_idx], stack["L_tcwb"].ravel()[n_idx]].astype(
            np.float64
        ),
        y_canary,
    )
    canary["alluvial_cover_propensity"] = score_canary_array(
        np.r_[
            stack["cover_propensity"].ravel()[p_idx],
            stack["cover_propensity"].ravel()[n_idx],
        ].astype(np.float64),
        y_canary,
    )
    for i, fname in enumerate(ABLATION_LOCAL_NAMES):
        pl = X_abl[i].ravel()
        canary[f"ablation_{fname}"] = score_canary_array(
            np.r_[pl[p_idx], pl[n_idx]].astype(np.float64), y_canary
        )

    vis_holdout = np.asarray(folds[0]["visible"], dtype=bool) & fp
    for f in folds[1:]:
        if not np.array_equal(np.asarray(f["visible"], dtype=bool) & fp, vis_holdout):
            raise AssertionError("Expected shared global visible mask across buffered folds")

    el_ksad_ho = compute_kostrov_elastic_fields(vis_holdout, fp)
    for k in TCWB_ELASTIC_NAMES:
        pl = el_ksad_ho[k].ravel()
        canary[f"fold_visible_{k}"] = score_canary_array(
            np.r_[pl[p_idx], pl[n_idx]].astype(np.float64), y_canary
        )
    del el_ksad_ho
    ew_ho = compute_ewcs_elastic_fields(vis_holdout, fp)
    canary["fold_visible_iso_tip_halo"] = score_canary_array(
        np.r_[
            ew_ho["iso_tip_halo"].ravel()[p_idx],
            ew_ho["iso_tip_halo"].ravel()[n_idx],
        ].astype(np.float64),
        y_canary,
    )
    del ew_ho
    gc.collect()

    flagged = [k for k, v in canary.items() if v["leakage_flag"]]
    if flagged:
        raise RuntimeError(f"STOP: Leakage canary > 0.90 fired on: {flagged}")
    max_canary_name, max_canary = max(
        canary.items(), key=lambda kv: kv[1]["discriminative_auc"]
    )
    print(
        f"  Canary PASS ({len(canary)} planes): worst={max_canary_name} "
        f"(disc_auc={max_canary['discriminative_auc']:.4f} <= 0.90)",
        flush=True,
    )

    cfg = TCWBConfig()
    d28_mask = load_binary_tif(D28_TIF) & fp
    h33_mask = load_binary_tif(H33_TIF) & fp

    arm_names = (
        "E1_tcwb_coupled_radial_dcelf",
        "E2_tcwb_blind_piedmont_basement_dcelf",
        "E3_local_unpulled_staticek_ablation",
    )

    t_ho = time.time()
    oof_ho_cache = CACHE_DIR / "oof_ho.npz"
    if oof_ho_cache.is_file():
        _ho_z = np.load(oof_ho_cache)
        oof_ho = {k: _ho_z[k] for k in ("S_e1_coupled", "S_e2_blind", "S_e3_ablation")}
    else:
        ho_regions = _quadrant_regions(fp, vis_holdout)
        oof_ho = fit_predict_loqo_tcwb_surfaces(
            X_tcwb,
            X_abl,
            stack["L_tcwb"],
            stack["cover_propensity"],
            ho_regions,
            fp,
            cfg,
        )
        np.savez(
            oof_ho_cache,
            S_e1_coupled=oof_ho["S_e1_coupled"],
            S_e2_blind=oof_ho["S_e2_blind"],
            S_e3_ablation=oof_ho["S_e3_ablation"],
        )

    d_vis_ho = ndi.distance_transform_edt(~vis_holdout)
    allowed_ho = fp & (d_vis_ho > COLLAR_PX)
    del d_vis_ho

    dc_e1_ho = dinkelbach_celf_allocate_dots(
        oof_ho["S_e1_coupled"],
        allowed_ho,
        known_faults=vis_holdout,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
        outer_iterations=2,
    )
    dc_e2_ho = dinkelbach_celf_allocate_dots(
        oof_ho["S_e2_blind"],
        allowed_ho,
        known_faults=vis_holdout,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
        outer_iterations=2,
    )
    dots_e3_ho = static_ek_spacing_allocate(
        oof_ho["S_e3_ablation"],
        allowed_ho,
        known_faults=vis_holdout,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
    )
    dots_d28_ho = d28_mask & allowed_ho
    dots_h33_ho = h33_mask & allowed_ho

    arm_fold_terms: dict[str, list[np.ndarray]] = {a: [] for a in arm_names}
    d28_fold_terms: list[np.ndarray] = []
    h33_fold_terms: list[np.ndarray] = []
    holdout_per_fold: dict[str, dict] = {
        a: {}
        for a in (*arm_names, "R0_D28_visible_collar", "H33_visible_collar")
    }

    for f in folds:
        qname = f["name"]
        res_e1, b_e1 = EH.evaluate(dc_e1_ho.dots.astype(np.float32), f, fp, block_side=200)
        arm_fold_terms["E1_tcwb_coupled_radial_dcelf"].append(b_e1)
        holdout_per_fold["E1_tcwb_coupled_radial_dcelf"][qname] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_e1["dti"],
            "n_truth": res_e1["n_truth"],
            "emitted": res_e1["n_emitted"],
            "final_lambda": dc_e1_ho.final_lambda,
            "celf_recomputations": dc_e1_ho.n_recomputations,
        }

        res_e2, b_e2 = EH.evaluate(dc_e2_ho.dots.astype(np.float32), f, fp, block_side=200)
        arm_fold_terms["E2_tcwb_blind_piedmont_basement_dcelf"].append(b_e2)
        holdout_per_fold["E2_tcwb_blind_piedmont_basement_dcelf"][qname] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_e2["dti"],
            "n_truth": res_e2["n_truth"],
            "emitted": res_e2["n_emitted"],
            "final_lambda": dc_e2_ho.final_lambda,
            "celf_recomputations": dc_e2_ho.n_recomputations,
        }

        res_e3, b_e3 = EH.evaluate(dots_e3_ho.astype(np.float32), f, fp, block_side=200)
        arm_fold_terms["E3_local_unpulled_staticek_ablation"].append(b_e3)
        holdout_per_fold["E3_local_unpulled_staticek_ablation"][qname] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_e3["dti"],
            "n_truth": res_e3["n_truth"],
            "emitted": res_e3["n_emitted"],
        }

        res_d28, b_d28 = EH.evaluate(dots_d28_ho.astype(np.float32), f, fp, block_side=200)
        d28_fold_terms.append(b_d28)
        holdout_per_fold["R0_D28_visible_collar"][qname] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_d28["dti"],
            "n_truth": res_d28["n_truth"],
            "emitted": res_d28["n_emitted"],
        }

        res_h33, b_h33 = EH.evaluate(dots_h33_ho.astype(np.float32), f, fp, block_side=200)
        h33_fold_terms.append(b_h33)
        holdout_per_fold["H33_visible_collar"][qname] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_h33["dti"],
            "n_truth": res_h33["n_truth"],
            "emitted": res_h33["n_emitted"],
        }
        print(
            f"  Fold {qname}: E1={res_e1['dti']:.4f} | E2={res_e2['dti']:.4f} | "
            f"E3={res_e3['dti']:.4f} | D28={res_d28['dti']:.4f} | H33={res_h33['dti']:.4f}",
            flush=True,
        )

    del oof_ho, dc_e1_ho, dc_e2_ho, dots_e3_ho
    gc.collect()

    terms_by_arm = {a: np.sum(arm_fold_terms[a], axis=0) for a in arm_names}
    terms_by_arm["R0_D28_visible_collar"] = np.sum(d28_fold_terms, axis=0)
    terms_by_arm["H33_visible_collar"] = np.sum(h33_fold_terms, axis=0)
    pooled = EH.pooled_summary(
        terms_by_arm,
        draws=1000,
        seed=861626,
        candidate="E1_tcwb_coupled_radial_dcelf",
    )

    e1_score = pooled["scores"]["E1_tcwb_coupled_radial_dcelf"]
    ctrl_names = [
        "E2_tcwb_blind_piedmont_basement_dcelf",
        "E3_local_unpulled_staticek_ablation",
        "R0_D28_visible_collar",
        "H33_visible_collar",
    ]
    best_ctrl_name = max(ctrl_names, key=lambda n: pooled["scores"][n]["dti"])
    best_delta = pooled["paired_differences"][best_ctrl_name]

    kslb_doc = json.loads(
        (ROOT / "docs/evidence/lane86c_results.json").read_text(encoding="utf-8")
    )
    kslb_best = kslb_doc["holdout_buffered_whole_components"]["scores"]["E3_kslb_noisyor_44k"]
    ksad_doc = json.loads(
        (ROOT / "docs/evidence/h86i-ksad-run-card.json").read_text(encoding="utf-8")
    )
    ksad_best = ksad_doc["holdout_dti"]["candidate"]
    slcq_doc = json.loads(
        (ROOT / "docs/evidence/h86m-slcq-run-card.json").read_text(encoding="utf-8")
    )
    slcq_best = slcq_doc["holdout_dti"]["candidate"]
    mcsp_doc = json.loads(
        (ROOT / "docs/evidence/h86j-mcsp-run-card.json").read_text(encoding="utf-8")
    )
    mcsp_best = mcsp_doc["holdout_dti"]["candidate"]
    stdp_doc = json.loads(
        (ROOT / "docs/evidence/h86k-stdp-run-card.json").read_text(encoding="utf-8")
    )
    stdp_best = stdp_doc["holdout_dti"]["candidate"]
    comp_doc = json.loads(
        (ROOT / "docs/evidence/h86e_comparator.json").read_text(encoding="utf-8")
    )
    comp_r0 = comp_doc["paired"]["E1_hgb_thin"]["scores"]["R0_foldfair"]

    beats_kslb = bool(e1_score["ci95"][0] > kslb_best["ci95"][1])
    beats_controls = bool(best_delta["ci95"][0] > 0.0)

    print(
        f"  POOLED HOLDOUT-DTI ({time.time() - t_ho:.1f}s): "
        f"E1={e1_score['dti']:.4f} {e1_score['ci95']} | "
        f"E2={pooled['scores']['E2_tcwb_blind_piedmont_basement_dcelf']['dti']:.4f} | "
        f"E3={pooled['scores']['E3_local_unpulled_staticek_ablation']['dti']:.4f} | "
        f"E1-best_ctrl({best_ctrl_name})={best_delta['delta']:+.4f} {best_delta['ci95']}",
        flush=True,
    )

    print(
        "[4/6] Fitting full-catalogue strict 4-quadrant OOF surfaces & running pre-placement surface registry scan...",
        flush=True,
    )
    full_cfg = TCWBConfig(seed=cfg.seed + 2000)
    oof_full_cache = CACHE_DIR / "oof_full.npz"
    if oof_full_cache.is_file():
        _fu_z = np.load(oof_full_cache)
        oof_full = {k: _fu_z[k] for k in ("S_e1_coupled", "S_e2_blind", "S_e3_ablation")}
    else:
        full_regions = _quadrant_regions(fp, cat & fp)
        oof_full = fit_predict_loqo_tcwb_surfaces(
            X_tcwb,
            X_abl,
            stack["L_tcwb"],
            stack["cover_propensity"],
            full_regions,
            fp,
            full_cfg,
        )
        np.savez(
            oof_full_cache,
            S_e1_coupled=oof_full["S_e1_coupled"],
            S_e2_blind=oof_full["S_e2_blind"],
            S_e3_ablation=oof_full["S_e3_ablation"],
        )
    surf_e1_full = oof_full["S_e1_coupled"]
    p_blind_full = oof_full["S_e2_blind"]
    surf_e3_full = oof_full["S_e3_ablation"]
    del oof_full, stack
    gc.collect()

    bounded_surface = rank01_on_mask(surf_e1_full, fp)
    surface_npy = CACHE_DIR / "h86p_tcwb_surface.npy"
    np.save(surface_npy, bounded_surface)
    surface_sha = sha256(surface_npy)
    surface_report_path = EV_DIR / "h86p-tcwb-registry-surface.json"
    if surface_report_path.is_file():
        _cached_s = json.loads(surface_report_path.read_text(encoding="utf-8"))
        if _cached_s.get("candidate_source_sha256") == surface_sha:
            surface_report = _cached_s
            surface_rc = 0 if _cached_s.get("surface_gate_pass") is True else 2
        else:
            surface_report, surface_rc = run_registry_check(
                surface_npy, surface_report_path, surface=True
            )
    else:
        surface_report, surface_rc = run_registry_check(
            surface_npy, surface_report_path, surface=True
        )
    rho_firings = int(
        surface_report.get("two_phase", {})
        .get("literal_reading", {})
        .get("rho_firings", 999)
    )
    surface_gate_pass = bool(
        surface_rc == 0
        and surface_report.get("surface_gate_pass") is True
        and surface_report.get("literal_gate_pass") is True
        and surface_report.get("registry_complete_for_index") is True
        and surface_report.get("inventory_rasters_missing") == []
        and surface_report.get("errors") == []
    )
    print(
        f"  Surface registry scan: measured={surface_report.get('registry_rasters_measured')}, "
        f"worst_spearman={surface_report['shared_summary']['worst_spearman_full_footprint']:.4f}, "
        f"rho_firings_over_0p90={rho_firings}",
        flush=True,
    )
    if rho_firings != 0:
        raise RuntimeError(
            f"STOP BEFORE PLACEMENT: Pre-placement surface Spearman rho > 0.90 fired ({rho_firings} times)"
        )

    print(
        "[5/6] Placing 37,654 Dinkelbach-CELF dots & running full-registry final-dot + SGMC-PROXY-DTI checks BEFORE serialization...",
        flush=True,
    )
    dcat = ndi.distance_transform_edt(~(cat & fp))
    allowed_full = fp & (dcat > COLLAR_PX)

    dc_full = dinkelbach_celf_allocate_dots(
        surf_e1_full,
        allowed_full,
        known_faults=cat & fp,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
        outer_iterations=2,
    )
    final_dots = dc_full.dots
    dcat_dots = dcat[final_dots & fp]
    radial_profile = {
        "min_dcat_px": float(dcat_dots.min()),
        "median_dcat_m": float(np.median(dcat_dots) * 100.0),
        "frac_3_to_10px_near_halo": float((dcat_dots <= 10.0).mean()),
        "frac_gt_10px_far_field_gt_1km": float((dcat_dots > 10.0).mean()),
    }
    del dcat, dcat_dots
    print("  Radial profile:", radial_profile, flush=True)

    dc_e2_full = dinkelbach_celf_allocate_dots(
        p_blind_full,
        allowed_full,
        known_faults=cat & fp,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
        outer_iterations=2,
    )
    dots_e3_full = static_ek_spacing_allocate(
        surf_e3_full,
        allowed_full,
        known_faults=cat & fp,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
    )

    sgmc_preds: dict[str, np.ndarray] = {
        "E1_tcwb_coupled_radial_dcelf": final_dots,
        "E2_tcwb_blind_piedmont_basement_dcelf": dc_e2_full.dots,
        "E3_local_unpulled_staticek_ablation": dots_e3_full,
        "H33_GEMSDOE32_as_is": h33_mask,
        "D28_GEMSDOE28_as_is": d28_mask,
    }
    if EWCS_TIF is not None and EWCS_TIF.is_file():
        sgmc_preds["H86F_EWCS_37654_as_is"] = load_binary_tif(EWCS_TIF) & fp
    if MCSP_TIF is not None and MCSP_TIF.is_file():
        sgmc_preds["H86J_MCSP_37654_as_is"] = load_binary_tif(MCSP_TIF) & fp
    if STDP_TIF is not None and STDP_TIF.is_file():
        sgmc_preds["H86K_STDP_37654_as_is"] = load_binary_tif(STDP_TIF) & fp
    if SLCQ_TIF is not None and SLCQ_TIF.is_file():
        sgmc_preds["H86M_SLCQ_37654_as_is"] = load_binary_tif(SLCQ_TIF) & fp
    if EDTI_TIF is not None and EDTI_TIF.is_file():
        sgmc_preds["H86G_EDTI_55000_as_is"] = load_binary_tif(EDTI_TIF) & fp

    sgmc_diag = evaluate_sgmc_proxy(
        sgmc_preds, fp, cat, candidate_key="E1_tcwb_coupled_radial_dcelf"
    )
    if "scores" in sgmc_diag:
        print(
            "  SGMC-PROXY-DTI:",
            {k: round(v["dti"], 4) for k, v in sgmc_diag["scores"].items()},
            flush=True,
        )

    dots_npy = CACHE_DIR / "h86p_tcwb_final_dots.npy"
    np.save(dots_npy, final_dots.astype(np.float32))
    dots_sha = sha256(dots_npy)

    dots_report_path = EV_DIR / "h86p-tcwb-registry-final-dots.json"
    if dots_report_path.is_file():
        _cached_d = json.loads(dots_report_path.read_text(encoding="utf-8"))
        if _cached_d.get("candidate_source_sha256") == dots_sha:
            dots_report = _cached_d
            dots_rc = 0 if _cached_d.get("final_dots_gate_pass") is True else 2
        else:
            dots_report, dots_rc = run_registry_check(
                dots_npy, dots_report_path, surface=False
            )
    else:
        dots_report, dots_rc = run_registry_check(
            dots_npy, dots_report_path, surface=False
        )
    chance_path = EV_DIR / "h86p-tcwb-pa86-chance-overlap.json"
    chance = run_chance_check(dots_report_path, dots_npy, chance_path)
    informative_audit = audit_informative_dot_field_firings(dots_report, fp, cat)
    print(
        f"  Final-dot registry scan: measured={dots_report.get('registry_rasters_measured')}, "
        f"informative_dot_field_firings={informative_audit['informative_dot_field_firings_count']}, "
        f"discrete_le_90k_firings={informative_audit['discrete_le_90k_firings_over_0p70']}, "
        f"worst_le_90k_overlap={informative_audit['worst_discrete_le_90k_overlap_3px']}",
        flush=True,
    )

    shared_dots = dots_report.get("shared_summary", {})
    if not (
        shared_dots.get("byte_unique_among_checked") is True
        and shared_dots.get("pixel_unique_among_checked") is True
    ):
        raise RuntimeError("STOP: Candidate is byte- or pixel-identical to an existing raster")

    lfl = dots_report.get("two_phase", {}).get("like_for_like_reading", {})
    final_dots_gate_pass = bool(
        dots_rc == 0
        and dots_report.get("final_dots_gate_pass") is True
        and dots_report.get("literal_gate_pass") is True
        and dots_report.get("registry_complete_for_index") is True
        and dots_report.get("inventory_rasters_missing") == []
        and dots_report.get("errors") == []
        and informative_audit["informative_dot_field_firings_count"] == 0
    )
    registry_gate = bool(
        surface_gate_pass and final_dots_gate_pass and chance.get("gate_pass") is True
    )

    print("[6/6] Writing validated GeoTIFF + single-TIFF ZIP + receipt + run card...", flush=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
    name = f"gems86-h86p-tcwb-dcelf-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"

    sgmc_e1_val = (
        sgmc_diag.get("scores", {})
        .get("E1_tcwb_coupled_radial_dcelf", {})
        .get("dti", 0.0)
    )
    note = (
        f"H86P-TCWB TCwash+BasementKink+ClaySeal LOQO DCELF (HOLD {e1_score['dti']:.4f}, "
        f"SGMC {sgmc_e1_val:.4f}); v2 fail-closed; DO NOT SUBMIT"
    )[:140]

    receipt = write_candidate(
        final_dots,
        g,
        name,
        note,
        metadata={
            "lane_id": "H86P-TCWB",
            "preregistration": "research/H86P_TCWB_PREREGISTRATION.json",
            "static_feature_sha256": static_sha256,
            "surface_sha256": surface_sha,
            "dots_sha256": dots_sha,
            "registry_surface_evidence": "docs/evidence/h86p-tcwb-registry-surface.json",
            "registry_final_evidence": "docs/evidence/h86p-tcwb-registry-final-dots.json",
            "chance_overlap_evidence": (
                str(chance_path.relative_to(ROOT))
                if chance_path.is_file()
                else "FAILED_CLOSED_NO_REPORT (see run card)"
            ),
        },
    )

    verdict = "promote" if (beats_kslb and beats_controls and registry_gate) else "negative"
    stop_reasons: list[str] = []
    if not beats_kslb:
        stop_reasons.append(
            f"HOLDOUT-DTI ({e1_score['dti']:.4f}) did not beat same-split H86C-KSLB "
            f"({kslb_best['dti']:.4f}) with separated 95% CIs"
        )
    if not beats_controls:
        stop_reasons.append(
            f"paired HOLDOUT-DTI delta vs {best_ctrl_name} 95% CI includes or falls below zero"
        )
    if informative_audit["informative_dot_field_firings_count"] > 0:
        stop_reasons.append(
            f"informative dot-field 3-px overlap > 0.70 fired on {informative_audit['informative_dot_field_firings_count']} rasters"
        )
    if not surface_gate_pass:
        stop_reasons.append(
            "pre-placement surface v2 registry gate failed closed (2 grid-incompatible "
            "registry rows 14GEMSDOE/7GEMSDOE and literal 17GEMSDOE full-support witness; "
            f"{rho_firings} Spearman rho > 0.90 firings across {surface_report.get('registry_rasters_measured')} measured rasters)"
        )
    if not final_dots_gate_pass:
        stop_reasons.append(
            "final-dot v2 registry gate failed closed (literal 17GEMSDOE full-support witness, "
            "13GEMSDOE space-filling lattice, and 2 grid-incompatible registry rows)"
        )
    if chance.get("gate_pass") is not True:
        stop_reasons.append(
            "PA-86-02 chance-overlap gate failed closed (incomplete v2 registry index due to 2 off-grid rows)"
        )
    if not stop_reasons:
        stop_reasons.append(
            "scientific and registry gates passed; separate human selector required"
        )

    mine_pts = np.column_stack(np.nonzero(final_dots & fp))
    disc_refs = [
        *sorted((ROOT / "data/scored_fleet").glob("*.tif")),
        *sorted(
            p
            for p in (ROOT / "docs/downloads").glob("*.tif")
            if "h86p-tcwb" not in p.name
        ),
    ]
    disc_rows: list[tuple[float, int, str]] = []
    disc_named: dict[str, dict] = {}
    for p in disc_refs:
        with rasterio.open(p) as ds:
            if ds.count != 1 or ds.shape != fp.shape:
                continue
            t_arr = ds.read(1)
        supp = np.isfinite(t_arr) & (t_arr > 0) & fp
        nd = int(supp.sum())
        if nd == 0 or nd > 100_000:
            continue
        tree = cKDTree(np.column_stack(np.nonzero(supp)))
        dists, _ = tree.query(mine_pts, distance_upper_bound=3.0 + 1e-9)
        ov3 = float((dists <= 3.0).mean())
        disc_rows.append((ov3, nd, p.name))
        if "h33-h33-2-b2" in p.name:
            disc_named["GEMSDOE32_H33"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
        elif "h86m-slcq" in p.name:
            disc_named["H86M_SLCQ"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
        elif "h86i-ksad" in p.name:
            disc_named["H86I_KSAD"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
        elif "h86j-mcsp" in p.name:
            disc_named["H86J_MCSP"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
        elif "h86k-stdp" in p.name:
            disc_named["H86K_STDP"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
    disc_rows.sort(reverse=True)
    disc_diag = {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "scope": "Diagnostic across local scored_fleet + docs/downloads discrete rasters with <=100,000 positive pixels (not an override of the full v2 gate).",
        "rasters_checked": len(disc_rows),
        "firings_over_0p70": sum(1 for ov3, _, _ in disc_rows if ov3 > 0.70),
        "worst_forward_overlap_3px": disc_rows[0][0] if disc_rows else None,
        "worst_submission": disc_rows[0][2] if disc_rows else None,
        "key_comparators": disc_named,
    }

    disk_val = receipt["independent_disk_validation"]
    run_card = {
        "schema": "gems86.lane_run_card.v1",
        "lane_id": "H86P-TCWB",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_branch": "arena/1595e23f-gemsdoe86",
        "preregistration": {
            "path": "research/H86P_TCWB_PREREGISTRATION.json",
            "markdown": "research/H86P_TCWB_PREREGISTRATION.md",
            "hypotheses_registry": "registry/h86p_hypotheses_20261026.json",
            "sha256": sha256(PREREGISTRATION_PATH),
        },
        "hypothesis": (
            "H86P-TCWB couples five untried translation-invariant Great Basin fault-physics operators—"
            "(1) downslope one-sided Total Count (Band 6 tc) wash-blanket depletion asymmetry across "
            "subtle piedmont breaks, (2) vector-gravity-signed cross-strike basement-depth footwall "
            "hinge kink (Band 15 x Bands 11, 18) pulled back up-dip by adaptive Salem cot(dip), "
            "(3) one-sided hydrothermal smectite/illite clay-cap lateral fault-seal termination "
            "(Band 17 x Band 2 magnetite destruction), (4) seismicity-conditioned transtensional "
            "dilatancy conjunction (Bands 7, 8 x Bands 10, 16), and (5) Aitchison CLR radiometric "
            "compositional Jacobian norm—with 6 fold-visible Kostrov-Pollard fracture-mechanics fields, "
            "4.5 px stress-shadow de-crowded 4-fold eroded-LOQO Elkan-Bayes PU calibration, "
            "radial-and-cover-aware Noisy-OR fusion, and Exact 6-Ring Bernoulli Survival Dinkelbach-CELF "
            "(37,654 dots, d_min=2.8 px, d_cat>3.0 px)."
        ),
        "mechanism": {
            "static_translation_invariant_features": list(TCWB_STATIC_NAMES),
            "fold_visible_elastic_features": list(TCWB_ELASTIC_NAMES),
            "ablation_control_features": list(ABLATION_LOCAL_NAMES),
            "zero_raw_regional_levels": True,
            "spatial_cross_fitting": (
                "Strict 4-quadrant Leave-One-Quadrant-Out using true footprint median "
                "quadrant_ids(fp) (ym=936, xm=1504) with 12-px (1.2 km) training-domain erosion "
                "(2.4 km total dead-zone vs fold eval regions) + disjoint whole-component "
                "elastic PU (4.5 px coupled stress-shadow negative buffer) + Elkan (2001) Bayes "
                "prior-odds recalibration"
            ),
            "fusion_formula": (
                "S_tcwb = 1 - (1 - 0.77 * P_coupled_cal) * (1 - 0.36 * (0.68 + 0.64*c_cover) * "
                "(0.85 + 0.30*tanh(max(d_vis - 8, 0)/10)) * P_blind_cal)"
            ),
            "allocator": (
                "Exact 6-ring Bernoulli survival supremum self-credit + Dinkelbach "
                "fractional-programming CELF (Minoux 1978, 2 outer iterations) on gems57 OFF_DY/OFF_DX/OFF_K"
            ),
            "budget_dots": BUDGET,
            "min_spacing_px": SPACING_PX,
            "catalogue_collar_px": COLLAR_PX,
            "radial_allocation_profile": radial_profile,
            "band_physics_verification": qc_receipt,
            "input_sha256": input_hashes,
        },
        "named_non_fault_mimic": (
            "Unfaulted alluvial fan-toe progradation, playa evaporite rims, Pleistocene Lake Lahontan "
            "(~1,330 m and ~1,205 m) wave-cut shoreline benches, GeoDAWN airborne survey stitch seams, "
            "Miocene Northern Nevada Rift mafic dikes, buried paleovalley thalwegs, and geothermal "
            "injection/quarry seismic swarms."
        ),
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "evaluator_hashes": EH.implementation_hashes(),
            "design": (
                "gems57-pooled-hide-v2: 4 footprint-median spatial quadrants (ym=936, xm=1504), "
                "20% whole fault components hidden (seed=20), buffer_px=3, visible-fault collar 3.0 px, "
                "strict eroded-domain (12 px) 4-fold LOQO + Elkan-Bayes nested component PU, "
                "pooled 200-px (20 km) physical blocks, 1,000 paired bootstrap draws"
            ),
            "protocol": (
                "gems57-pooled-hide-v2: 4 footprint-median spatial quadrants, 20% whole fault "
                "components hidden (seed=20), buffer_px=3, visible-fault collar 3.0 px, "
                "strict eroded-domain 4-fold LOQO, pooled 200-px physical blocks, 1,000 paired draws"
            ),
            "withheld_positive_pixels": int(e1_score["withheld_positive_pixels"]),
            "candidate": e1_score,
            "best_preregistered_control": best_ctrl_name,
            "paired_delta_vs_best_preregistered_control": best_delta,
            "R0_D28_visible_collar": pooled["scores"]["R0_D28_visible_collar"],
            "paired_delta_vs_R0_D28_visible_collar": pooled["paired_differences"][
                "R0_D28_visible_collar"
            ],
            "H33_visible_collar": pooled["scores"]["H33_visible_collar"],
            "paired_delta_vs_H33_visible_collar": pooled["paired_differences"][
                "H33_visible_collar"
            ],
            "all_arms": pooled["scores"],
            "per_fold": holdout_per_fold,
            "paired_differences": pooled["paired_differences"],
            "same_split_comparators": {
                "H86M_SLCQ_E1_37654": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86m-slcq-run-card.json",
                    "dti": slcq_best["dti"],
                    "ci95": slcq_best["ci95"],
                },
                "H86I_KSAD_E2_37654": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86i-ksad-run-card.json",
                    "dti": ksad_best["dti"],
                    "ci95": ksad_best["ci95"],
                },
                "H86J_MCSP_E1_37654": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86j-mcsp-run-card.json",
                    "dti": mcsp_best["dti"],
                    "ci95": mcsp_best["ci95"],
                },
                "H86K_STDP_E1_37654": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86k-stdp-run-card.json",
                    "dti": stdp_best["dti"],
                    "ci95": stdp_best["ci95"],
                },
                "H86C_KSLB_E3_44k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/lane86c_results.json",
                    "dti": kslb_best["dti"],
                    "ci95": kslb_best["ci95"],
                },
                "R0_D25_fold_fair_44k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86e_comparator.json",
                    "dti": comp_r0["dti"],
                    "ci95": comp_r0["ci95"],
                },
            },
            "beats_same_split_kslb_with_separated_ci": beats_kslb,
            "beats_preregistered_controls_paired_ci": beats_controls,
            "leakage_canary_summary": {
                "features_tested": len(canary),
                "max_discriminative_auc_feature": max_canary_name,
                "max_discriminative_auc": max_canary["discriminative_auc"],
                "threshold": 0.90,
                "any_leakage_flag": False,
            },
            "leakage_canary": canary,
        },
        "sgmc_off_catalogue_diagnostic": sgmc_diag,
        "preflight": preflight,
        "experiments_run": 3,
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "surface_preplacement": {
                **registry_summary(surface_report, surface_report_path, surface_rc),
                "surface_gate_pass": surface_gate_pass,
            },
            "final_dots": {
                **registry_summary(dots_report, dots_report_path, dots_rc),
                "final_dots_gate_pass": final_dots_gate_pass,
            },
            "pa86_02": chance,
            "full_registry_informative_dot_field_audit": informative_audit,
            "like_for_like_dot_field_diagnostic": {
                "scope": "DIAGNOSTIC-ONLY (dot-field subset inside full v2 scan; does NOT override literal/completeness v2 fail-closed gate)",
                "dot_field_rasters": lfl.get("dot_field_rasters"),
                "continuous_surface_rasters": lfl.get("continuous_surface_rasters"),
                "worst_forward_overlap_dot_fields": lfl.get("worst_forward_overlap_dot_fields"),
                "worst_forward_overlap_dot_field_submission": lfl.get(
                    "worst_forward_overlap_dot_field_submission"
                ),
                "forward_overlap_firings_dot_fields": lfl.get("forward_overlap_firings"),
                "like_for_like_duplicate": lfl.get("duplicate"),
            },
            "comparable_discrete_100k_diagnostic": disc_diag,
        },
        "dinkelbach_celf_allocation": {
            "emitted_dots": int(dc_full.dots.sum()),
            "total_covered_credit": float(dc_full.total_covered_credit),
            "total_self_credit": float(dc_full.total_self_credit),
            "final_dinkelbach_lambda": float(dc_full.final_lambda),
            "outer_lambdas": [float(x) for x in dc_full.outer_lambdas],
            "celf_recomputations": int(dc_full.n_recomputations),
            "candidate_pool_size": int(dc_full.n_candidates),
        },
        "raster_sha256": receipt["sha256"],
        "zip_sha256": sha256(OUT_DIR / f"{name}.zip"),
        "validator_output": {
            "evidence_class": "LOCAL-FORMAT-VALIDATION",
            "all_checks_passed": disk_val["all_checks_passed"],
            "no_nan_inside_footprint": disk_val["checks"]["in_footprint_all_finite"],
            "values_in_0_1": disk_val["checks"]["range_0_1_guaranteed"],
            "crs_shape_transform_match": all(
                disk_val["checks"][key]
                for key in (
                    "crs_epsg_32611",
                    "dimensions_3730x3292",
                    "transform_matches_sample_submission",
                )
            ),
            "checks": disk_val["checks"],
            "positive_pixels": disk_val["emitted_positive_pixels"],
            "min": disk_val["min"],
            "max": disk_val["max"],
        },
        "submission_name": name,
        "submission_file": f"docs/downloads/{name}.tif",
        "submission_zip": f"docs/downloads/{name}.zip",
        "submission_receipt": f"docs/downloads/{name}.json",
        "note": note,
        "note_chars": len(note),
        "verdict": verdict,
        "duplicate": bool(not registry_gate),
        "new_candidate_generated": True,
        "decision": "SELECTOR STEP REQUIRED" if verdict == "promote" else "DO NOT SUBMIT",
        "decision_reason": "; ".join(stop_reasons),
        "stop_reasons": stop_reasons,
        "runtime_seconds": round(time.time() - t0, 2),
    }

    card_path = EV_DIR / "h86p-tcwb-run-card.json"
    card_path.write_text(
        json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "lane_id": "H86P-TCWB",
                "submission_name": name,
                "submission_file": run_card["submission_file"],
                "raster_sha256": run_card["raster_sha256"],
                "holdout_e1_dti": e1_score["dti"],
                "holdout_e1_ci95": e1_score["ci95"],
                "holdout_e2_blind_dti": pooled["scores"][
                    "E2_tcwb_blind_piedmont_basement_dcelf"
                ]["dti"],
                "holdout_e3_ablation_dti": pooled["scores"][
                    "E3_local_unpulled_staticek_ablation"
                ]["dti"],
                "paired_e1_minus_e3": pooled["paired_differences"][
                    "E3_local_unpulled_staticek_ablation"
                ],
                "sgmc_e1_dti": sgmc_e1_val,
                "radial_profile": radial_profile,
                "v2_worst_surface_spearman": surface_report["shared_summary"][
                    "worst_spearman_full_footprint"
                ],
                "informative_dot_field_firings": informative_audit[
                    "informative_dot_field_firings_count"
                ],
                "worst_discrete_le_90k_overlap": informative_audit[
                    "worst_discrete_le_90k_overlap_3px"
                ],
                "verdict": verdict,
                "decision": run_card["decision"],
                "runtime_seconds": run_card["runtime_seconds"],
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    return run_pa86_lane()


if __name__ == "__main__":
    raise SystemExit(main())
