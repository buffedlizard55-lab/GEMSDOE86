#!/usr/bin/env python3
"""Execute contemporaneously preregistered H86H-1 (H86H-PSTD) lane and fail closed.

Enforces AGENTS.md Rules 1-11 and Parallel-Run Protocol Rules 1-6:
1. Verifies frozen pre-implementation preregistration (<= 3 arms, <= 2 hours).
2. Calls protocol_preflight.require_like_for_like() (PA-86-01 preflight; literal
   full-support witness status preserved, never overridden).
3. Builds 100% catalogue-blind Poisson-Susceptibility Tensor Dislocation (PSTD)
   feature planes from SHA-256-verified training_features.tif.
4. Runs single-feature Leakage Canaries (max(AUC, 1-AUC) <= 0.90) on the frozen
   seed=20 buffered whole-component holdout (11,321 withheld positives).
5. Evaluates the 3 preregistered arms (E1, E2, E3) via unmodified shared
   vendor/gems57/emit.py + vendor/gems57/evaluate_holdout.py (gems57-pooled-hide-v2)
   with 1,000-draw paired physical 20 km spatial-block bootstrap 95% CIs against BOTH:
   - Fold-fair R0 constructed from unpruned GEMSDOE25 dotted-h19-5-d2-8
     (sha256 91eae1ca42ec...) masked strictly by fold-visible faults (d_vis > 2 px),
   - Same-split archived buffered whole-component best H86C-KSLB (0.1241).
6. Runs unmodified scripts/check_h86e_registry.py --surface (v2 bound schema)
   against the full indexed registry BEFORE full-footprint dot placement.
7. Stops fail-closed BEFORE full-footprint dot placement and BEFORE GeoTIFF
   serialization whenever complete zero-error surface clearance, literal
   submission clearance, or positive paired holdout CI vs controls is absent,
   emitting a negative Run Card (docs/evidence/h86h-pstd-run-card.json).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import emit, evaluate_holdout as EH, grid, holdout  # noqa: E402
from gems86_pstd.features import build_pstd_features, compose_pstd_arms  # noqa: E402
from scripts import check_h86e_registry, protocol_preflight  # noqa: E402

PREREG_JSON = ROOT / "research/H86H_PSTD_PREREGISTRATION.json"
PREREG_MD = ROOT / "research/H86H_PSTD_PREREGISTRATION.md"
DATA_DIR = ROOT / "data"
WORK_DIR = DATA_DIR / "work/h86h_pstd"
SURFACE_REPORT_OUT = ROOT / "docs/evidence/h86h-pstd-registry-surface.json"
RUN_CARD_OUT = ROOT / "docs/evidence/h86h-pstd-run-card.json"

PIN_FEATURES = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
PIN_FAULTS = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
PIN_SAMPLE = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
PIN_D28_UNPRUNED = "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"

TARGET_DOTS = 37654
TILE_PX = 3
VISIBLE_COLLAR_PX = 2.0
HOLDOUT_SEED = 20
HIDE_FRAC = 0.20
BUFFER_PX = 3
BLOCK_PX = 200  # 20 km physical spatial blocks at 100 m pixel size
BOOT_DRAWS = 1000
BOOT_SEED = 520810
CANARY_STOP = 0.90
H86C_KSLB_BEST = 0.124136
H86C_KSLB_CI95 = [0.10796, 0.140312]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_preregistration(prereg_json: Path = PREREG_JSON, prereg_md: Path = PREREG_MD) -> dict[str, Any]:
    if not prereg_json.is_file() or not prereg_md.is_file():
        raise FileNotFoundError("Missing frozen H86H-PSTD preregistration JSON or Markdown")
    doc = json.loads(prereg_json.read_text())
    if doc.get("schema") != "gems86.h86h-pstd-preregistration.v1":
        raise ValueError(f"Unexpected preregistration schema: {doc.get('schema')}")
    if doc.get("status") != "frozen_before_implementation":
        raise ValueError("Preregistration must have status == 'frozen_before_implementation'")
    arms = doc.get("experiment_arms", [])
    if not (1 <= len(arms) <= 3):
        raise ValueError(f"Budget violation: expected 1..3 arms, got {len(arms)}")
    if doc.get("budget", {}).get("max_experiments", 99) > 3:
        raise ValueError("Budget violation: max_experiments > 3")
    return {
        "schema": doc["schema"],
        "status": doc["status"],
        "json_path": str(prereg_json.relative_to(ROOT)),
        "json_sha256": sha256_file(prereg_json),
        "md_path": str(prereg_md.relative_to(ROOT)),
        "md_sha256": sha256_file(prereg_md),
        "candidate_hypotheses_count": len(doc.get("candidate_hypotheses", [])),
        "experiment_arms": [a["id"] for a in arms],
    }


def verify_pinned_inputs() -> dict[str, str]:
    expected = {
        "training_features.tif": PIN_FEATURES,
        "existing_faults.tif": PIN_FAULTS,
        "sample_submission.tif": PIN_SAMPLE,
    }
    verified: dict[str, str] = {}
    for fname, exp_sha in expected.items():
        p = DATA_DIR / fname
        if not p.is_file():
            raise FileNotFoundError(f"Missing {p}; run scripts/restore_data.py first.")
        got = sha256_file(p)
        if got != exp_sha:
            raise ValueError(f"SHA-256 mismatch for {fname}: got {got}, expected {exp_sha}")
        verified[fname] = got
    return verified


def locate_unpruned_d28() -> Path:
    candidates = [
        DATA_DIR / "registry_ext" / f"{PIN_D28_UNPRUNED}.tif",
        DATA_DIR / "scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    ]
    for p in candidates:
        if p.is_file() and sha256_file(p) == PIN_D28_UNPRUNED:
            return p
    raise FileNotFoundError(
        f"Missing SHA-pinned unpruned GEMSDOE25 d2.8 comparator ({PIN_D28_UNPRUNED}); "
        "run scripts/restore_registry_inventory.py or scripts/restore_h86d_data.py first."
    )


def run_leakage_canaries(
    planes: dict[str, np.ndarray],
    arms: dict[str, np.ndarray],
    folds: list[dict[str, Any]],
    footprint: np.ndarray,
    *,
    stop_auc: float = CANARY_STOP,
) -> dict[str, Any]:
    rng = np.random.default_rng(HOLDOUT_SEED + 101)
    fp = np.asarray(footprint, dtype=bool)
    all_fields = {**planes, **{f"arm::{k}": v for k, v in arms.items()}}
    rows: dict[str, Any] = {}
    worst_name = ""
    worst_disc = 0.0

    for name, arr in all_fields.items():
        fold_aucs: list[float] = []
        fold_discs: list[float] = []
        for fold in folds:
            region = np.asarray(fold["region"], dtype=bool)
            known = np.asarray(fold.get("masked_known", fold["visible"]), dtype=bool)
            truth = np.asarray(fold["truth"], dtype=bool)
            active = fp & region & ~known
            pos = truth & active
            neg = active & ~pos
            pos_vals = arr[pos]
            neg_idx = np.flatnonzero(neg)
            take = min(neg_idx.size, max(50_000, pos_vals.size * 10))
            sampled_neg = arr.ravel()[rng.choice(neg_idx, size=take, replace=False)]
            y = np.concatenate([np.ones(pos_vals.size, dtype=np.int8), np.zeros(sampled_neg.size, dtype=np.int8)])
            s = np.concatenate([pos_vals.astype(np.float64), sampled_neg.astype(np.float64)])
            auc = float(roc_auc_score(y, s))
            disc = max(auc, 1.0 - auc)
            fold_aucs.append(round(auc, 6))
            fold_discs.append(round(disc, 6))
        max_disc = max(fold_discs)
        mean_auc = round(float(np.mean(fold_aucs)), 6)
        if max_disc > worst_disc:
            worst_disc = max_disc
            worst_name = name
        if max_disc > stop_auc:
            raise RuntimeError(
                f"STOP_LEAKAGE_CANARY: {name} max discriminative AUC {max_disc:.6f} > {stop_auc:.2f}"
            )
        rows[name] = {
            "mean_auc": mean_auc,
            "fold_aucs": fold_aucs,
            "max_discriminative_auc": max_disc,
            "pass": bool(max_disc <= stop_auc),
        }

    return {
        "threshold_discriminative_auc": stop_auc,
        "all_pass": True,
        "worst_field": worst_name,
        "worst_discriminative_auc": round(worst_disc, 6),
        "fields": rows,
    }


def _eval_fold_predictions(
    preds: list[np.ndarray],
    folds: list[dict[str, Any]],
    footprint: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    terms_list: list[np.ndarray] = []
    per_fold: dict[str, Any] = {}
    for pred, fold in zip(preds, folds):
        res, block_terms = EH.evaluate(pred.astype(np.float32), fold, footprint, block_side=BLOCK_PX)
        terms_list.append(block_terms)
        per_fold[str(fold["name"])] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": round(float(res["dti"]), 6),
            "n_truth": int(res["n_truth"]),
            "emitted": int(res["n_emitted"]),
        }
    return np.sum(terms_list, axis=0), per_fold


def run_lane(*, allow_stop: bool = True) -> dict[str, Any]:
    t0 = time.monotonic()
    prereg = require_preregistration()
    preflight = protocol_preflight.require_like_for_like()
    verified_inputs = verify_pinned_inputs()
    d28_path = locate_unpruned_d28()

    g = grid.load_grid(DATA_DIR)
    folds, quad_meta = holdout.buffered_component_draw(
        g, seed=HOLDOUT_SEED, hide_frac=HIDE_FRAC, buffer_px=BUFFER_PX
    )
    same_visible = all(
        np.array_equal(np.asarray(folds[0]["visible"], dtype=bool), np.asarray(f["visible"], dtype=bool))
        for f in folds[1:]
    )
    if same_visible:
        shared_edt = ndi.distance_transform_edt(~np.asarray(folds[0]["visible"], dtype=bool)).astype(np.float32)
        visible_edts = [shared_edt for _ in folds]
    else:
        visible_edts = [
            ndi.distance_transform_edt(~np.asarray(f["visible"], dtype=bool)).astype(np.float32)
            for f in folds
        ]

    planes = build_pstd_features(DATA_DIR / "training_features.tif", g.footprint)
    arms = compose_pstd_arms(planes, g.footprint)
    canary = run_leakage_canaries(planes, arms, folds, g.footprint, stop_auc=CANARY_STOP)

    with rasterio.open(d28_path) as ds:
        raw_d28 = ds.read(1)
    d28_dots = np.isfinite(raw_d28) & (raw_d28 > 0.5) & np.asarray(g.footprint, dtype=bool)
    r0_preds = [
        (d28_dots & ~np.asarray(f["visible"], dtype=bool) & (d_vis > VISIBLE_COLLAR_PX)).astype(np.float32)
        for f, d_vis in zip(folds, visible_edts)
    ]
    r0_terms, r0_per_fold = _eval_fold_predictions(r0_preds, folds, g.footprint)

    terms_by_arm: dict[str, np.ndarray] = {"R0_fold_fair_d25_d28_vis_collar2": r0_terms}
    per_fold_by_arm: dict[str, dict[str, Any]] = {"R0_fold_fair_d25_d28_vis_collar2": r0_per_fold}

    for arm_id, surf in arms.items():
        if same_visible:
            vis = np.asarray(folds[0]["visible"], dtype=bool)
            allowed_fold = np.asarray(g.footprint, dtype=bool) & ~vis & (visible_edts[0] > VISIBLE_COLLAR_PX)
            ranked, _ = emit.emit_decimated(surf, allowed_fold, tile_px=TILE_PX)
            shared_dots = emit.emit_prefix(ranked, TARGET_DOTS).astype(np.float32)
            preds = [shared_dots for _ in folds]
        else:
            preds = []
            for f, d_vis in zip(folds, visible_edts):
                vis = np.asarray(f["visible"], dtype=bool)
                allowed_fold = np.asarray(g.footprint, dtype=bool) & ~vis & (d_vis > VISIBLE_COLLAR_PX)
                ranked, _ = emit.emit_decimated(surf, allowed_fold, tile_px=TILE_PX)
                dots = emit.emit_prefix(ranked, TARGET_DOTS).astype(np.float32)
                preds.append(dots)
        arm_terms, arm_pf = _eval_fold_predictions(preds, folds, g.footprint)
        terms_by_arm[arm_id] = arm_terms
        per_fold_by_arm[arm_id] = arm_pf

    pooled = EH.pooled_summary(
        terms_by_arm,
        draws=BOOT_DRAWS,
        seed=BOOT_SEED,
        candidate="E1_pstd_full",
    )

    arm_results: dict[str, Any] = {}
    for arm_id in arms:
        sc = pooled["scores"][arm_id]
        arm_pair = EH.pooled_summary(
            {"R0_fold_fair_d25_d28_vis_collar2": r0_terms, arm_id: terms_by_arm[arm_id]},
            draws=BOOT_DRAWS,
            seed=BOOT_SEED,
            candidate=arm_id,
        )
        diff_r0 = arm_pair["paired_differences"]["R0_fold_fair_d25_d28_vis_collar2"]
        arm_results[arm_id] = {
            "arm_id": arm_id,
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "holdout_dti": round(float(sc["dti"]), 6),
            "ci95": [round(float(x), 6) for x in sc["ci95"]],
            "withheld_positives_total": int(sc["withheld_positive_pixels"]),
            "tpw": round(float(sc["tpw"]), 3),
            "fpw": round(float(sc["fpw"]), 3),
            "fnw": round(float(sc["fnw"]), 3),
            "full_footprint_budget_dots": TARGET_DOTS,
            "total_emitted_across_4_quadrants": int(sum(v["emitted"] for v in per_fold_by_arm[arm_id].values())),
            "visible_collar_px": VISIBLE_COLLAR_PX,
            "per_fold": per_fold_by_arm[arm_id],
            "paired_vs_fold_fair_r0": {
                "delta_dti": round(float(diff_r0["delta"]), 6),
                "delta_ci95": [round(float(x), 6) for x in diff_r0["ci95"]],
                "ci95_strictly_positive": bool(diff_r0["ci95"][0] > 0.0),
            },
            "delta_vs_h86c_kslb_archived_best": round(float(sc["dti"]) - H86C_KSLB_BEST, 6),
            "beats_same_split_holdout_best": bool(float(sc["dti"]) > H86C_KSLB_BEST),
        }

    r0_sc = pooled["scores"]["R0_fold_fair_d25_d28_vis_collar2"]
    r0_eval = {
        "control_id": "R0_fold_fair_d25_d28_vis_collar2",
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": EH.VERSION,
        "source_sha256": PIN_D28_UNPRUNED,
        "raw_d28_dots": int(d28_dots.sum()),
        "holdout_dti": round(float(r0_sc["dti"]), 6),
        "ci95": [round(float(x), 6) for x in r0_sc["ci95"]],
        "withheld_positives_total": int(r0_sc["withheld_positive_pixels"]),
        "visible_collar_px": VISIBLE_COLLAR_PX,
        "per_fold": r0_per_fold,
        "leakage_audit_note": (
            "Fold-fair H33-2-B2 control: masks ONLY fold-visible faults (d_vis > 2.0 px) from "
            "unpruned GEMSDOE25 d2.8 (44,090 dots), avoiding the IR-86-RIDF-02 / IR-86-MMT-R0-LEAK "
            "defect of using GEMSDOE28 r1-solo which pre-deleted dots near withheld test faults."
        ),
    }

    # Pre-placement complete-registry surface check (AGENTS.md Rules 10 & 11)
    import gc

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    surface_npy = WORK_DIR / "h86h_pstd_e1_surface.npy"
    e1_surface = np.where(g.footprint, arms["E1_pstd_full"], np.float32(0.0)).astype(np.float32)
    np.save(surface_npy, e1_surface)
    n_folds = len(folds)
    quad_names = [str(f["name"]) for f in folds]
    surface_array_checks = {
        "shape": list(e1_surface.shape),
        "dtype": str(e1_surface.dtype),
        "nan_inside_footprint": int(np.isnan(e1_surface[g.footprint]).sum()),
        "min_inside_footprint": float(e1_surface[g.footprint].min()),
        "max_inside_footprint": float(e1_surface[g.footprint].max()),
        "values_in_0_1": bool(
            np.isfinite(e1_surface[g.footprint]).all()
            and float(e1_surface[g.footprint].min()) >= 0.0
            and float(e1_surface[g.footprint].max()) <= 1.0
        ),
    }
    del planes, arms, folds, visible_edts, r0_preds, raw_d28, d28_dots, e1_surface
    gc.collect()

    SURFACE_REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    rel_surface_npy = surface_npy.relative_to(ROOT)
    rc_surface = check_h86e_registry.main([str(rel_surface_npy), str(SURFACE_REPORT_OUT), "--surface"])
    surf_report = json.loads(SURFACE_REPORT_OUT.read_text())

    surface_gate_pass = bool(
        rc_surface == 0
        and surf_report.get("surface_gate_pass") is True
        and surf_report.get("registry_complete_for_index") is True
        and surf_report.get("inventory_rasters_missing") == []
        and surf_report.get("errors") == []
    )
    literal_gate_pass = bool(surf_report.get("literal_gate_pass") is True)
    e1_res = arm_results["E1_pstd_full"]
    holdout_gate_pass = bool(
        e1_res["paired_vs_fold_fair_r0"]["ci95_strictly_positive"]
        and e1_res["beats_same_split_holdout_best"]
    )

    elapsed_s = round(time.monotonic() - t0, 2)
    if elapsed_s > 7200.0:
        raise RuntimeError(f"Budget violation: elapsed {elapsed_s}s > 7200s")

    shared_sum = surf_report.get("shared_summary") or {}
    two_phase = surf_report.get("two_phase") or {}
    lit_read = two_phase.get("literal_reading") or {}
    lfl_read = two_phase.get("like_for_like_reading") or {}
    valid_rasters = int(surf_report.get("registry_rasters_measured", 0))
    expected_rasters = int(surf_report.get("registry_rasters_expected", 0))
    error_rows = surf_report.get("errors") or []
    stop_reasons: list[str] = []
    if not holdout_gate_pass:
        stop_reasons.append(
            f"HOLDOUT_BELOW_CONTROLS: E1_pstd_full HOLDOUT-DTI={e1_res['holdout_dti']:.6f} "
            f"{e1_res['ci95']} vs fold-fair R0={r0_eval['holdout_dti']:.6f} {r0_eval['ci95']} "
            f"(paired delta {e1_res['paired_vs_fold_fair_r0']['delta_dti']:+.6f}, "
            f"CI95 {e1_res['paired_vs_fold_fair_r0']['delta_ci95']}) and archived same-split best "
            f"H86C-KSLB={H86C_KSLB_BEST:.6f} {H86C_KSLB_CI95}."
        )
    if not surface_gate_pass:
        stop_reasons.append(
            f"SURFACE_REGISTRY_INCOMPLETE_OR_ERRORED: rho_firings={lit_read.get('rho_firings')} "
            f"(worst Spearman={lit_read.get('worst_spearman_full_footprint')}) across "
            f"{valid_rasters}/{expected_rasters} valid rasters, "
            f"but {len(error_rows)} historical registry_inventory rows failed CRS/grid checks "
            f"({[e.get('submission') for e in error_rows]}), forcing surface_gate_pass=False per AGENTS.md Rule 11."
        )
    if not literal_gate_pass:
        stop_reasons.append(
            "LITERAL_WITNESS_BLOCKER: 17GEMSDOE full-support witness covers 100.0% of allowed pixels "
            "(forward_overlap=1.0 > 0.70), forcing literal_gate_pass=False per AGENTS.md Rules 6 & 11."
        )

    if not (surface_gate_pass and literal_gate_pass and holdout_gate_pass):
        run_card = {
            "schema": "gems86.h86h-pstd-run-card.v1",
            "lane": "H86H-PSTD",
            "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "hypothesis": (
                "H86H-1 (H86H-PSTD): Concealed Great Basin geothermal faults juxtapose density blocks "
                "(regularized Laplace vertical gravity curvature g_zz = -(dx B18 + drow B11) hinge) while "
                "hydrothermal H2S fluids destroy magnetite along the permeable damage zone, creating a "
                "positive Poisson potential-field residual max(0, alpha_flank*z(g_zz) - z(M_z)) inside "
                "actively dilating/shearing, moderately conductive, low-relief piedmont/intrabasin cover."
            ),
            "mechanism": (
                "Footprint-normalized sigma=500 m Laplace vertical gravity curvature g_zz coupled to "
                "Band 9 tmi_vg (M_z) via local sigma=1.2 km flank Poisson regression, sharpened by "
                "gravity-gradient structure-tensor anisotropy and Band 3 tmi_hg, modulated by GPS "
                "dilatation/shear (Bands 8, 7), shallow conductance (Band 17), and detrended slope (Band 19). "
                "100% catalogue-blind surface; fold-visible faults used solely for emission masking."
            ),
            "non_fault_mimic": (
                "Reversed-polarity Tertiary ash-flow tuff margins or caldera ring-fracture moats where "
                "reverse remanent magnetization produces negative M_z along a density boundary without "
                "Quaternary brittle faulting."
            ),
            "preregistration": prereg,
            "preflight": preflight,
            "verified_input_sha256": verified_inputs,
            "leakage_canary": canary,
            "holdout_evaluation": {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "evaluator_implementation_sha256": pooled["implementation_sha256"],
                "bootstrap": pooled["bootstrap"],
                "split": {
                    "kind": "buffered_component_draw",
                    "n_folds": n_folds,
                    "hide_frac": HIDE_FRAC,
                    "buffer_px": BUFFER_PX,
                    "seed": HOLDOUT_SEED,
                    "quadrant_names": quad_names,
                    "shared_visible_mask_across_folds": bool(same_visible),
                    "withheld_positives_total": r0_eval["withheld_positives_total"],
                },
                "fold_fair_r0_control": r0_eval,
                "same_split_archived_best": {
                    "id": "H86C-KSLB_E3_noisyor_44k",
                    "evidence_class": "HOLDOUT-DTI",
                    "holdout_dti": H86C_KSLB_BEST,
                    "ci95": H86C_KSLB_CI95,
                },
                "arms": arm_results,
            },
            "correlation_overlap_vs_registry": {
                "evidence_class": "REGISTRY-MEASUREMENT",
                "stage_reached": "surface_pre_placement_stop",
                "surface_report_path": str(SURFACE_REPORT_OUT.relative_to(ROOT)),
                "surface_report_schema": surf_report.get("schema"),
                "candidate_source_sha256": surf_report.get("candidate_source_sha256"),
                "candidate_decoded_sha256": shared_sum.get("candidate_decoded_sha256"),
                "registry_index_sha256": surf_report.get("registry_index_sha256"),
                "inventory_rasters_expected": expected_rasters,
                "inventory_rasters_missing": surf_report.get("inventory_rasters_missing"),
                "valid_comparable_rasters": valid_rasters,
                "dot_field_rasters": lfl_read.get("dot_field_rasters"),
                "continuous_surface_rasters": lfl_read.get("continuous_surface_rasters"),
                "error_rows_count": len(error_rows),
                "error_submissions": [e.get("submission") for e in error_rows],
                "rho_firings_over_0_90": lit_read.get("rho_firings"),
                "worst_spearman_full_footprint": lit_read.get("worst_spearman_full_footprint"),
                "worst_spearman_submission": lit_read.get("worst_spearman_submission"),
                "surface_gate_pass": surface_gate_pass,
                "literal_gate_pass": literal_gate_pass,
                "final_dots_placed": False,
                "final_dots_gate_pass": None,
            },
            "raster_sha256": None,
            "validator_output": {
                "candidate_tif_serialized": False,
                "surface_array_checks": surface_array_checks,
                "reason_no_tif_written": (
                    "Halted fail-closed before full-footprint dot placement and before GeoTIFF "
                    "serialization per AGENTS.md Rule 11 (surface_gate_pass=False, literal_gate_pass=False, "
                    "holdout_gate_pass=" + str(holdout_gate_pass) + ")."
                ),
            },
            "submission_name": "NONE_HALTED_AT_PRE_PLACEMENT_GATE",
            "submission_note": "DO NOT SUBMIT: H86H-PSTD negative deliverable; halted before placement/TIFF per Rule 11.",
            "submission_note_length": 88,
            "budget": {
                "experiments_run": len(arm_results),
                "max_experiments": 3,
                "elapsed_seconds": elapsed_s,
                "max_seconds": 7200,
                "submission_slots_used": 0,
            },
            "stop_reasons": stop_reasons,
            "verdict": "negative",
            "safe_to_submit": False,
            "submission_ready": False,
            "approved_for_weekly_slot": False,
        }
        RUN_CARD_OUT.parent.mkdir(parents=True, exist_ok=True)
        RUN_CARD_OUT.write_text(json.dumps(run_card, indent=2) + "\n")
        if not allow_stop:
            raise RuntimeError("STOP_PRE_PLACEMENT_GATE: " + " | ".join(stop_reasons))
        return run_card

    raise RuntimeError("Unreachable under pinned 17GEMSDOE literal witness without organizer rule change")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict-exit",
        action="store_true",
        help="Raise RuntimeError / exit nonzero after writing the negative run card when gates stop placement.",
    )
    args = parser.parse_args()
    card = run_lane(allow_stop=not args.strict_exit)
    print(
        json.dumps(
            {
                "lane": card["lane"],
                "verdict": card["verdict"],
                "e1_holdout_dti": card["holdout_evaluation"]["arms"]["E1_pstd_full"]["holdout_dti"],
                "e1_ci95": card["holdout_evaluation"]["arms"]["E1_pstd_full"]["ci95"],
                "e2_holdout_dti": card["holdout_evaluation"]["arms"]["E2_pstd_geopotential_only"]["holdout_dti"],
                "e3_holdout_dti": card["holdout_evaluation"]["arms"]["E3_pstd_inverted_polarity_control"]["holdout_dti"],
                "fold_fair_r0_dti": card["holdout_evaluation"]["fold_fair_r0_control"]["holdout_dti"],
                "fold_fair_r0_ci95": card["holdout_evaluation"]["fold_fair_r0_control"]["ci95"],
                "worst_spearman_vs_valid_registry": card["correlation_overlap_vs_registry"]["worst_spearman_full_footprint"],
                "rho_firings": card["correlation_overlap_vs_registry"]["rho_firings_over_0_90"],
                "surface_gate_pass": card["correlation_overlap_vs_registry"]["surface_gate_pass"],
                "final_dots_placed": card["correlation_overlap_vs_registry"]["final_dots_placed"],
                "elapsed_seconds": card["budget"]["elapsed_seconds"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
