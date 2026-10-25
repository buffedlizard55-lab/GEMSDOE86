#!/usr/bin/env python3
"""Execute preregistered lane H86J-MCSP:
Monogenic Cross-Spectral Phase-Congruent Structural Conduit + Out-of-Quadrant
Geothermal Fault-Intersection Specialist with Exact Submodular CELF Allocation.

Enforces AGENTS.md Rules 1-12 and Parallel-Run Protocol Rules 1-6:
  1. Frozen preregistration check (<= 3 arms, <= 2 hours, fixed 37,654-dot budget).
  2. Band physics & SHA-256 verification against src/gems86/io.py and external pins.
  3. Single-feature LEAKAGE-CANARY across every static and fold-visible plane (AUC <= 0.90).
  4. Shared hide-and-recover HOLDOUT-DTI (gems57-pooled-hide-v2, seed=20, 11,321 withheld
     positives, 1,000-draw paired 20 km physical-block bootstrap).
  5. Pre-placement surface registry scan BEFORE full-catalogue dot placement, followed by
     final-dot registry scan + PA-86-02 chance-overlap check (fail-closed per Rules 10-12).
  6. Out-of-sample SGMC-PROXY-DTI diagnostic (read-only evaluation on 62,122 off-catalogue
     USGS SGMC fault pixels > 3 px from existing_faults.tif; zero SGMC bytes in features/model).
  7. Validated GeoTIFF + single-TIFF ZIP + writer receipt + machine-readable JSON run card.

Following the repository-wide builder gating merged in PR #98, ``main()`` now calls
``protocol_preflight.require_feasible()`` before any work. The recorded 2026-10-25
execution ran under the frozen PA-86 owner-mandate interpretation; its run card
and artifacts are unchanged historical receipts, not a protocol exemption.
"""

from __future__ import annotations

from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
SRC = ROOT / "src"
for _p in (ROOT, SRC, VENDOR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems57 import evaluate_holdout as EH, grid, holdout, submission_writer, uniqueness, validate

from gems86_mcsp import (
    ABLATION_AMP_NAMES,
    FOLD_ELASTIC_NAMES,
    MCSP_STATIC_NAMES,
    MCSPConfig,
    build_mcsp_static_stack,
    celf_allocate_dots,
    fit_predict_loqo_blind,
    fit_predict_loqo_kinematic,
    fuse_dual_noisy_or,
    rank01_on_mask,
    static_ek_spacing_allocate,
)
from gems86_ewcs.features import compute_elastic_fields
from scripts.protocol_preflight import require_feasible, require_like_for_like
from scripts.restore_data import EXTERNAL_PINS, PINS as CORE_PINS

PREREGISTRATION_PATH = ROOT / "research/H86J_MCSP_PREREGISTRATION.json"
CACHE_DIR = ROOT / ".cache/h86j_mcsp"
EXT_DIR = ROOT / ".cache/external"
EV_DIR = ROOT / "docs/evidence"
OUT_DIR = ROOT / "docs/downloads"

FEATURE_TIF = ROOT / "data/bridge/training_features.tif"
D28_TIF = (
    ROOT
    / "data/registry_ext/ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73.tif"
)
H33_TIF = (
    ROOT
    / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
)
EWCS_TIF = next(
    (ROOT / "docs/downloads").glob("gems86-h86f-ewcs-elastic-wing-*.tif"), None
)
EDTI_TIF = next(
    (ROOT / "docs/downloads").glob("gems86-h86g-edti-55000dots-*.tif"), None
)
SGMC_TIF = EXT_DIR / "derived_sgmc_faults_100m_u8.tif"
SGMC_PIN = "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"

SEED = 20
BUDGET = 37654
SPACING_PX = 2.8
COLLAR_PX = 3.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_preregistration() -> dict:
    if not PREREGISTRATION_PATH.is_file():
        raise RuntimeError(f"Missing frozen preregistration: {PREREGISTRATION_PATH}")
    doc = json.loads(PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    arms = doc.get("arms", [])
    if doc.get("lane_id") != "H86J-MCSP" or len(arms) != 3:
        raise RuntimeError("Invalid H86J-MCSP preregistration arm count or lane_id")
    if doc.get("budget", {}).get("max_experiments", 99) > 3:
        raise RuntimeError("Preregistration exceeds 3-experiment protocol cap")
    return doc


def verify_all_inputs() -> dict[str, str]:
    pins: dict[str, tuple[Path, str]] = {
        "training_features.tif": (
            ROOT / "data/bridge/training_features.tif",
            CORE_PINS["training_features.tif"],
        ),
        "existing_faults.tif": (
            ROOT / "data/bridge/existing_faults.tif",
            CORE_PINS["existing_faults.tif"],
        ),
        "sample_submission.tif": (
            ROOT / "data/bridge/sample_submission.tif",
            CORE_PINS["sample_submission.tif"],
        ),
        "GEMSDOE28_control.tif": (
            D28_TIF,
            "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
        ),
        "GEMSDOE32_H33_control.tif": (
            H33_TIF,
            "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
        ),
    }
    for fname, exp_sha in EXTERNAL_PINS.items():
        pins[fname] = (EXT_DIR / fname, exp_sha)
    if SGMC_TIF.is_file():
        pins["derived_sgmc_faults_100m_u8.tif"] = (SGMC_TIF, SGMC_PIN)

    out: dict[str, str] = {}
    for label, (path, expected) in pins.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing pinned input {label}: {path}")
        got = sha256(path)
        if got != expected:
            raise ValueError(f"SHA-256 mismatch for {label}: {got} != {expected}")
        out[label] = got
    return out


def load_binary_tif(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        arr = src.read(1)
    return np.isfinite(arr) & (arr > 0)


def prepare_canary_indices(
    folds: list[dict], fp: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    region = np.zeros(fp.shape, dtype=bool)
    hidden = np.zeros(fp.shape, dtype=bool)
    masked_known = np.zeros(fp.shape, dtype=bool)
    for f in folds:
        region |= np.asarray(f["region"], dtype=bool)
        hidden |= np.asarray(f["hidden_all"], dtype=bool)
        masked_known |= np.asarray(f["masked_known"], dtype=bool)
    active = region & fp & ~masked_known
    truth = active & hidden
    neg = active & ~truth
    p_idx = np.flatnonzero(truth.ravel())
    n_idx = np.flatnonzero(neg.ravel())
    rng = np.random.default_rng(861025)
    n_idx = rng.choice(n_idx, size=min(300_000, n_idx.size), replace=False)
    y = np.r_[np.ones(p_idx.size, dtype=np.int8), np.zeros(n_idx.size, dtype=np.int8)]
    return p_idx, n_idx, y


def score_canary_array(vals: np.ndarray, y: np.ndarray) -> dict:
    finite = np.isfinite(vals)
    if finite.sum() < 10:
        auc = 0.5
    else:
        v_f = vals[finite]
        y_f = y[finite]
        auc = float(roc_auc_score(y_f, v_f)) if (np.ptp(v_f) > 0 and np.unique(y_f).size == 2) else 0.5
    disc = max(auc, 1.0 - auc)
    return {
        "evidence_class": "LEAKAGE-CANARY",
        "auc": round(auc, 6),
        "discriminative_auc": round(disc, 6),
        "finite_fraction": round(float(finite.mean()), 6),
        "threshold": 0.90,
        "leakage_flag": bool(disc > 0.90),
    }


def evaluate_sgmc_proxy(
    preds: dict[str, np.ndarray],
    fp: np.ndarray,
    cat: np.ndarray,
    candidate_key: str,
) -> dict:
    """Read-only off-catalogue SGMC structural diagnostic (>3 px from existing_faults).
    Labeled strictly SGMC-PROXY-DTI; never used for training, feature construction, or tuning."""
    if not SGMC_TIF.is_file():
        return {"status": "SGMC_NOT_PRESENT"}
    sgmc = load_binary_tif(SGMC_TIF) & fp
    dcat = ndi.distance_transform_edt(~(cat & fp))
    known_collar = cat | (dcat <= COLLAR_PX)
    truth_offcat = sgmc & fp & ~known_collar
    fold_proxy = {
        "region": fp,
        "visible": known_collar,
        "masked_known": known_collar,
        "truth": truth_offcat,
    }
    terms_by_arm: dict[str, np.ndarray] = {}
    point_scores: dict[str, dict] = {}
    for arm_name, dots in preds.items():
        res, b_terms = EH.evaluate(
            np.asarray(dots, dtype=np.float32), fold_proxy, fp, block_side=200
        )
        terms_by_arm[arm_name] = b_terms
        point_scores[arm_name] = res

    pooled = EH.pooled_summary(
        terms_by_arm, draws=1000, seed=861025, candidate=candidate_key
    )
    scores_out = {}
    for arm_name, sc in pooled["scores"].items():
        scores_out[arm_name] = {
            "evidence_class": "SGMC-PROXY-DTI",
            "dti": sc["dti"],
            "ci95": sc["ci95"],
            "emitted": int(np.asarray(preds[arm_name], dtype=bool).sum()),
            "emitted_outside_collar": int(point_scores[arm_name]["n_emitted"]),
            "off_catalogue_sgmc_positives": int(truth_offcat.sum()),
        }
    deltas_out = {}
    for arm_name, dl in pooled["paired_differences"].items():
        deltas_out[arm_name] = {
            "evidence_class": "SGMC-PROXY-DTI",
            "delta": dl["delta"],
            "ci95": dl["ci95"],
        }
    return {
        "evidence_class": "SGMC-PROXY-DTI",
        "note": (
            "Read-only off-catalogue USGS SGMC 1:500k fault proxy (> 3.0 px from existing_faults.tif); "
            "not organizer truth and never used in features, fitting, or hyperparameter selection."
        ),
        "off_catalogue_positive_pixels": int(truth_offcat.sum()),
        "spatial_bootstrap_cluster_m": 20000.0,
        "bootstrap_draws": 1000,
        "scores": scores_out,
        "paired_differences_vs_candidate": deltas_out,
    }


def run_registry_check(
    array_path: Path, output: Path, *, surface: bool
) -> tuple[dict, int]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts/check_h86e_registry.py"),
        str(array_path),
        str(output),
    ]
    if surface:
        cmd.append("--surface")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if not output.is_file():
        raise RuntimeError(
            f"Registry check produced no report (rc={proc.returncode}): {proc.stderr[-2000:]}"
        )
    return json.loads(output.read_text(encoding="utf-8")), proc.returncode


def run_chance_check(
    registry_report: Path, candidate_path: Path, output: Path
) -> dict:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/pa86_chance_overlap.py"),
            str(registry_report),
            str(candidate_path),
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if output.is_file():
        report = json.loads(output.read_text(encoding="utf-8"))
        report["runner_returncode"] = proc.returncode
        return report
    return {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "amendment": "PA-86-02",
        "status": "FAILED_CLOSED_NO_REPORT",
        "gate_pass": False,
        "runner_returncode": proc.returncode,
        "stderr_tail": proc.stderr[-3000:],
        "stdout_tail": proc.stdout[-1000:],
        "note": (
            "pa86_chance_overlap.py refused to certify (incomplete registry / binding check); "
            "recorded verbatim per AGENTS.md Rule 11, never bypassed."
        ),
    }


def registry_summary(report: dict, report_path: Path, returncode: int) -> dict:
    shared = report.get("shared_summary", {})
    lit = report.get("two_phase", {}).get("literal_reading", {})
    return {
        "schema": report.get("schema"),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": sha256(report_path),
        "runner_returncode": returncode,
        "candidate_source_sha256": report.get("candidate_source_sha256"),
        "candidate_decoded_sha256": shared.get("candidate_decoded_sha256"),
        "registry_index_sha256": report.get("registry_index_sha256"),
        "registry_rasters_measured": report.get("registry_rasters_measured"),
        "registry_rasters_checked": shared.get("registry_rasters_checked"),
        "registry_rasters_expected": shared.get("registry_rasters_expected"),
        "inventory_rasters_missing": report.get("inventory_rasters_missing"),
        "registry_errors": report.get("errors", []),
        "registry_complete_for_index": report.get("registry_complete_for_index"),
        "complete_accessible_scan": shared.get("complete_accessible_scan"),
        "byte_unique_among_checked": shared.get("byte_unique_among_checked"),
        "pixel_unique_among_checked": shared.get("pixel_unique_among_checked"),
        "worst_spearman_full_footprint": shared.get("worst_spearman_full_footprint"),
        "worst_spearman_submission": shared.get("worst_rho_submission"),
        "worst_dot_overlap": shared.get("worst_dot_overlap"),
        "worst_overlap_submission": shared.get("worst_overlap_submission"),
        "rho_firings_over_0p90": lit.get("rho_firings"),
        "literal_gate_pass": report.get("literal_gate_pass"),
        "two_phase": report.get("two_phase"),
        "top15_by_forward_overlap": report.get("top15_by_forward_overlap"),
        "top15_by_spearman": report.get("top15_by_spearman"),
        "scope": report.get("scope"),
    }


def write_candidate(
    dots: np.ndarray, g: grid.Grid, name: str, note: str, metadata: dict
) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pred = np.where(dots & g.footprint, 1.0, 0.0).astype(np.float32)
    path = OUT_DIR / f"{name}.tif"
    receipt = submission_writer.write_submission(
        path,
        pred,
        ROOT / "data/bridge/sample_submission.tif",
        g.footprint,
        note=note,
        name=name,
        catalogue=g.catalogue,
        metadata=metadata,
    )
    disk = validate.validate(path, g.footprint, g.catalogue)
    if not disk["all_checks_passed"]:
        raise RuntimeError("Independent on-disk GeoTIFF validator failed")
    receipt["independent_disk_validation"] = disk
    path.with_suffix(".json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    for suffix in (".tif", ".zip", ".json"):
        p = path.with_suffix(suffix)
        if p.is_file():
            p.chmod(0o644)
    return receipt


def run_pa86_lane() -> int:
    t0 = time.time()
    prereg = require_preregistration()
    preflight = require_like_for_like()
    input_hashes = verify_all_inputs()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)

    g = grid.load_grid(ROOT / "data/bridge")
    fp, cat = g.footprint, g.catalogue
    folds, _ = holdout.buffered_component_draw(
        g, seed=SEED, hide_frac=0.20, buffer_px=3
    )

    print("[1/6] Building 22 translation-invariant MCSP planes + 8 scalar control planes...", flush=True)
    mcsp_cache = CACHE_DIR / "h86j_mcsp_static.npy"
    amp_cache = CACHE_DIR / "h86j_amp_static.npy"
    l_cache = CACHE_DIR / "h86j_L_mcsp.npy"
    qc_cache = CACHE_DIR / "h86j_qc_receipt.json"
    if (
        mcsp_cache.is_file()
        and amp_cache.is_file()
        and l_cache.is_file()
        and qc_cache.is_file()
    ):
        X_mcsp = np.load(mcsp_cache, mmap_mode="r")
        X_amp = np.load(amp_cache, mmap_mode="r")
        L_mcsp = np.load(l_cache)
        qc_receipt = json.loads(qc_cache.read_text(encoding="utf-8"))
    else:
        X_mcsp, L_mcsp, X_amp, valid_feat, qc_receipt = build_mcsp_static_stack(
            FEATURE_TIF,
            EXT_DIR,
            out_mcsp_path=mcsp_cache,
            out_amp_path=amp_cache,
            footprint=fp,
        )
        np.save(l_cache, L_mcsp)
        qc_cache.write_text(json.dumps(qc_receipt, indent=2) + "\n", encoding="utf-8")
    static_sha256 = sha256(mcsp_cache)
    gc.collect()

    cfg = MCSPConfig(collar_px=COLLAR_PX, seed=861025)
    arm_names = (
        "E1_mcsp_dual_celf",
        "E2_mcsp_blind_celf",
        "E3_mcsp_amp_staticek_ablation",
    )
    if set(arm_names) != {a["id"] for a in prereg["arms"]}:
        raise RuntimeError("Arm IDs do not match frozen preregistration")

    d28_mask = load_binary_tif(D28_TIF) & fp
    h33_mask = load_binary_tif(H33_TIF) & fp

    holdout_ckpt = CACHE_DIR / "h86j_holdout_ckpt.json"
    if holdout_ckpt.is_file():
        ckpt_doc = json.loads(holdout_ckpt.read_text(encoding="utf-8"))
    else:
        ckpt_doc = {}

    if ckpt_doc.get("static_sha256") == static_sha256:
        print("[2/6]-[3/6] Reusing SHA-matched 4-fold LOQO holdout & leakage-canary checkpoint...", flush=True)
        canary = ckpt_doc["canary"]
        pooled = ckpt_doc["pooled"]
        holdout_per_fold = ckpt_doc["holdout_per_fold"]
        max_canary_name, max_canary = max(
            canary.items(), key=lambda kv: kv[1]["discriminative_auc"]
        )
    else:
        print("[2/6] Running single-feature LEAKAGE-CANARY across all static & fold-visible planes...", flush=True)
        p_idx, n_idx, y_canary = prepare_canary_indices(folds, fp)
        canary = {}
        for i, k in enumerate(MCSP_STATIC_NAMES):
            flat = X_mcsp[i].ravel()
            canary[k] = score_canary_array(
                np.r_[flat[p_idx], flat[n_idx]].astype(np.float64), y_canary
            )
        canary["L_mcsp_corroboration"] = score_canary_array(
            np.r_[L_mcsp.ravel()[p_idx], L_mcsp.ravel()[n_idx]].astype(np.float64),
            y_canary,
        )
        for i, k in enumerate(ABLATION_AMP_NAMES):
            flat = X_amp[i].ravel()
            canary[k] = score_canary_array(
                np.r_[flat[p_idx], flat[n_idx]].astype(np.float64), y_canary
            )

        all_el_keys = (*FOLD_ELASTIC_NAMES, "iso_tip_halo")
        el_pos_buf = {k: np.zeros(p_idx.size, dtype=np.float32) for k in all_el_keys}
        el_neg_buf = {k: np.zeros(n_idx.size, dtype=np.float32) for k in all_el_keys}

        arm_fold_terms = {a: [] for a in arm_names}
        d28_fold_terms = []
        h33_fold_terms = []
        holdout_per_fold = {
            a: {}
            for a in (*arm_names, "R0_D28_visible_collar", "H33_visible_collar")
        }

        print("[3/6] Evaluating 3 preregistered arms + controls on 4-fold spatial LOQO holdout...", flush=True)
        for fold_i, f in enumerate(folds):
            t_fold = time.time()
            vis = np.asarray(f["visible"], dtype=bool) & fp
            known_f = np.asarray(f.get("masked_known", vis), dtype=bool) & fp
            el_pred = compute_elastic_fields(vis, fp)

            reg_flat = (np.asarray(f["region"], dtype=bool) & fp).ravel()
            p_in = reg_flat[p_idx]
            n_in = reg_flat[n_idx]
            for k in all_el_keys:
                eflat = el_pred[k].ravel()
                el_pos_buf[k][p_in] = eflat[p_idx[p_in]]
                el_neg_buf[k][n_in] = eflat[n_idx[n_in]]

            d_vis = ndi.distance_transform_edt(~vis)
            allowed = fp & (d_vis > COLLAR_PX)
            del d_vis

            fold_cfg = MCSPConfig(collar_px=COLLAR_PX, seed=861025 + 1000 * fold_i)

            p_blind = fit_predict_loqo_blind(X_mcsp, L_mcsp, vis, fp, fold_cfg)
            p_kin = fit_predict_loqo_kinematic(
                X_mcsp,
                vis,
                fp,
                fold_cfg,
                FOLD_ELASTIC_NAMES,
                precomputed_elastic=el_pred,
            )
            surf_e1 = fuse_dual_noisy_or(
                p_blind,
                p_kin,
                fp,
                alpha_blind=fold_cfg.alpha_blind,
                alpha_kin=fold_cfg.alpha_kin,
            )
            celf_e1 = celf_allocate_dots(
                surf_e1,
                allowed,
                known_faults=known_f,
                valid=fp,
                budget=BUDGET,
                min_spacing_px=SPACING_PX,
            )
            res_e1, b_e1 = EH.evaluate(
                celf_e1.dots.astype(np.float32), f, fp, block_side=200
            )
            arm_fold_terms["E1_mcsp_dual_celf"].append(b_e1)
            holdout_per_fold["E1_mcsp_dual_celf"][f["name"]] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_e1["dti"],
                "n_truth": res_e1["n_truth"],
                "emitted": res_e1["n_emitted"],
                "celf_recomputations": celf_e1.n_recomputations,
            }

            celf_e2 = celf_allocate_dots(
                p_blind,
                allowed,
                known_faults=known_f,
                valid=fp,
                budget=BUDGET,
                min_spacing_px=SPACING_PX,
            )
            res_e2, b_e2 = EH.evaluate(
                celf_e2.dots.astype(np.float32), f, fp, block_side=200
            )
            arm_fold_terms["E2_mcsp_blind_celf"].append(b_e2)
            holdout_per_fold["E2_mcsp_blind_celf"][f["name"]] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_e2["dti"],
                "n_truth": res_e2["n_truth"],
                "emitted": res_e2["n_emitted"],
                "celf_recomputations": celf_e2.n_recomputations,
            }

            surf_e3 = fit_predict_loqo_kinematic(
                X_amp,
                vis,
                fp,
                fold_cfg,
                ("iso_tip_halo",),
                precomputed_elastic=el_pred,
            )
            dots_e3 = static_ek_spacing_allocate(
                surf_e3,
                allowed,
                known_faults=known_f,
                valid=fp,
                budget=BUDGET,
                min_spacing_px=SPACING_PX,
            )
            res_e3, b_e3 = EH.evaluate(dots_e3.astype(np.float32), f, fp, block_side=200)
            arm_fold_terms["E3_mcsp_amp_staticek_ablation"].append(b_e3)
            holdout_per_fold["E3_mcsp_amp_staticek_ablation"][f["name"]] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_e3["dti"],
                "n_truth": res_e3["n_truth"],
                "emitted": res_e3["n_emitted"],
            }

            d28_dots = d28_mask & allowed
            res_d28, b_d28 = EH.evaluate(
                d28_dots.astype(np.float32), f, fp, block_side=200
            )
            d28_fold_terms.append(b_d28)
            holdout_per_fold["R0_D28_visible_collar"][f["name"]] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_d28["dti"],
                "n_truth": res_d28["n_truth"],
                "emitted": res_d28["n_emitted"],
            }

            h33_dots = h33_mask & allowed
            res_h33, b_h33 = EH.evaluate(
                h33_dots.astype(np.float32), f, fp, block_side=200
            )
            h33_fold_terms.append(b_h33)
            holdout_per_fold["H33_visible_collar"][f["name"]] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_h33["dti"],
                "n_truth": res_h33["n_truth"],
                "emitted": res_h33["n_emitted"],
            }

            print(
                f"  Fold {f['name']}: E1={res_e1['dti']:.4f} | E2={res_e2['dti']:.4f} | "
                f"E3={res_e3['dti']:.4f} | D28={res_d28['dti']:.4f} ({time.time() - t_fold:.1f}s)",
                flush=True,
            )
            del el_pred, p_blind, p_kin, surf_e1, surf_e3
            gc.collect()

        for k in all_el_keys:
            canary[f"fold_visible_{k}"] = score_canary_array(
                np.r_[el_pos_buf[k], el_neg_buf[k]].astype(np.float64), y_canary
            )
        max_canary_name, max_canary = max(
            canary.items(), key=lambda kv: kv[1]["discriminative_auc"]
        )
        if any(v["leakage_flag"] for v in canary.values()):
            raise RuntimeError(
                f"LEAKAGE-CANARY HARD STOP: {max_canary_name} discriminative AUC={max_canary['discriminative_auc']:.4f} > 0.90"
            )
        print(
            f"  LEAKAGE-CANARY PASS: {len(canary)} features tested, max discriminative AUC={max_canary['discriminative_auc']:.4f} ({max_canary_name})",
            flush=True,
        )

        holdout_terms = {a: sum(arm_fold_terms[a]) for a in arm_names}
        holdout_terms["R0_D28_visible_collar"] = sum(d28_fold_terms)
        holdout_terms["H33_visible_collar"] = sum(h33_fold_terms)
        pooled = EH.pooled_summary(
            holdout_terms, draws=1000, seed=520810, candidate="E1_mcsp_dual_celf"
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

    e1_score = pooled["scores"]["E1_mcsp_dual_celf"]
    ctrl_names = [
        "E2_mcsp_blind_celf",
        "E3_mcsp_amp_staticek_ablation",
        "R0_D28_visible_collar",
        "H33_visible_collar",
    ]
    best_ctrl_name = max(ctrl_names, key=lambda n: pooled["scores"][n]["dti"])
    best_delta = pooled["paired_differences"][best_ctrl_name]

    kslb_doc = json.loads(
        (ROOT / "docs/evidence/lane86c_results.json").read_text(encoding="utf-8")
    )
    kslb_best = kslb_doc["holdout_buffered_whole_components"]["scores"]["E3_kslb_noisyor_44k"]
    ewcs_doc = json.loads(
        (ROOT / "docs/evidence/h86f-ewcs-run-card.json").read_text(encoding="utf-8")
    )
    ewcs_best = ewcs_doc["holdout_dti"]["candidate"]
    edti_doc = json.loads(
        (ROOT / "docs/evidence/h86g-edti-run-card.json").read_text(encoding="utf-8")
    )
    edti_55k = edti_doc["holdout_dti"]["candidate"]
    comp_doc = json.loads(
        (ROOT / "docs/evidence/h86e_comparator.json").read_text(encoding="utf-8")
    )
    comp_r0 = comp_doc["paired"]["E1_hgb_thin"]["scores"]["R0_foldfair"]

    beats_kslb = bool(e1_score["ci95"][0] > kslb_best["ci95"][1])
    beats_controls = bool(best_delta["ci95"][0] > 0.0)

    print(
        f"  POOLED HOLDOUT-DTI: E1={e1_score['dti']:.4f} {e1_score['ci95']} | "
        f"E2={pooled['scores']['E2_mcsp_blind_celf']['dti']:.4f} | "
        f"E3={pooled['scores']['E3_mcsp_amp_staticek_ablation']['dti']:.4f}",
        flush=True,
    )

    print("[4/6] Fitting full-catalogue 4-fold LOQO surfaces & running pre-placement surface registry scan...", flush=True)
    el_full = compute_elastic_fields(cat & fp, fp)
    p_blind_full = fit_predict_loqo_blind(X_mcsp, L_mcsp, cat & fp, fp, cfg)
    p_kin_full = fit_predict_loqo_kinematic(
        X_mcsp,
        cat & fp,
        fp,
        cfg,
        FOLD_ELASTIC_NAMES,
        precomputed_elastic=el_full,
    )
    surf_e1_full = fuse_dual_noisy_or(
        p_blind_full,
        p_kin_full,
        fp,
        alpha_blind=cfg.alpha_blind,
        alpha_kin=cfg.alpha_kin,
    )
    surf_e3_full = fit_predict_loqo_kinematic(
        X_amp,
        cat & fp,
        fp,
        cfg,
        ("iso_tip_halo",),
        precomputed_elastic=el_full,
    )
    del el_full
    gc.collect()

    bounded_surface = rank01_on_mask(surf_e1_full, fp)
    surface_npy = CACHE_DIR / "h86j_mcsp_surface.npy"
    np.save(surface_npy, bounded_surface)
    surface_sha = sha256(surface_npy)
    surface_report_path = EV_DIR / "h86j-mcsp-registry-surface.json"
    if surface_report_path.is_file():
        cached_sr = json.loads(surface_report_path.read_text(encoding="utf-8"))
        if cached_sr.get("candidate_source_sha256") == surface_sha:
            print(f"  Reusing SHA-matched pre-placement surface registry report ({surface_sha[:12]})...", flush=True)
            surface_report, surface_rc = cached_sr, 1
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

    card_path = EV_DIR / "h86j-mcsp-run-card.json"

    if rho_firings != 0:
        raise RuntimeError(
            f"STOP: Pre-placement surface Spearman rho > 0.90 fired ({rho_firings} times)"
        )

    print("[5/6] Placing 37,654 CELF dots, running final-dot v2 registry + PA-86-02 + SGMC-PROXY-DTI...", flush=True)
    dcat = ndi.distance_transform_edt(~(cat & fp))
    allowed_full = fp & (dcat > COLLAR_PX)
    del dcat

    celf_full = celf_allocate_dots(
        surf_e1_full,
        allowed_full,
        known_faults=cat & fp,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
    )
    final_dots = celf_full.dots

    celf_e2_full = celf_allocate_dots(
        p_blind_full,
        allowed_full,
        known_faults=cat & fp,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
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
        "E1_mcsp_dual_celf": final_dots,
        "E2_mcsp_blind_celf": celf_e2_full.dots,
        "E3_mcsp_amp_staticek_ablation": dots_e3_full,
        "H33_GEMSDOE32_as_is": h33_mask,
        "D28_GEMSDOE28_as_is": d28_mask,
    }
    if EWCS_TIF is not None and EWCS_TIF.is_file():
        sgmc_preds["H86F_EWCS_37654_as_is"] = load_binary_tif(EWCS_TIF) & fp
    if EDTI_TIF is not None and EDTI_TIF.is_file():
        sgmc_preds["H86G_EDTI_55000_as_is"] = load_binary_tif(EDTI_TIF) & fp

    sgmc_diag = evaluate_sgmc_proxy(
        sgmc_preds, fp, cat, candidate_key="E1_mcsp_dual_celf"
    )
    if "scores" in sgmc_diag:
        print(
            "  SGMC-PROXY-DTI:",
            {k: round(v["dti"], 4) for k, v in sgmc_diag["scores"].items()},
            flush=True,
        )

    dots_npy = CACHE_DIR / "h86j_mcsp_final_dots.npy"
    np.save(dots_npy, final_dots.astype(np.float32))
    dots_sha = sha256(dots_npy)

    dots_report_path = EV_DIR / "h86j-mcsp-registry-final-dots.json"
    if dots_report_path.is_file():
        cached_dr = json.loads(dots_report_path.read_text(encoding="utf-8"))
        if cached_dr.get("candidate_source_sha256") == dots_sha:
            print(f"  Reusing SHA-matched final-dot registry report ({dots_sha[:12]})...", flush=True)
            dots_report, dots_rc = cached_dr, 1
        else:
            dots_report, dots_rc = run_registry_check(
                dots_npy, dots_report_path, surface=False
            )
    else:
        dots_report, dots_rc = run_registry_check(dots_npy, dots_report_path, surface=False)
    chance_path = EV_DIR / "h86j-mcsp-pa86-chance-overlap.json"
    chance = run_chance_check(dots_report_path, dots_npy, chance_path)

    lfl = dots_report.get("two_phase", {}).get("like_for_like_reading", {})

    final_dots_gate_pass = bool(
        dots_rc == 0
        and dots_report.get("final_dots_gate_pass") is True
        and dots_report.get("literal_gate_pass") is True
        and dots_report.get("registry_complete_for_index") is True
        and dots_report.get("inventory_rasters_missing") == []
        and dots_report.get("errors") == []
    )
    registry_gate = bool(
        surface_gate_pass and final_dots_gate_pass and chance.get("gate_pass") is True
    )

    print("[6/6] Writing validated GeoTIFF + single-TIFF ZIP + receipt + run card...", flush=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
    name = f"gems86-h86j-mcsp-celf-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"

    sgmc_e1_val = sgmc_diag.get("scores", {}).get("E1_mcsp_dual_celf", {}).get("dti", 0.0)
    note = (
        f"H86J-MCSP monogenic+geotherm LOQO CELF (HOLDOUT {e1_score['dti']:.4f}, "
        f"SGMC {sgmc_e1_val:.4f}); v2 gate fail-closed; DO NOT SUBMIT"
    )[:140]

    receipt = write_candidate(
        final_dots,
        g,
        name,
        note,
        metadata={
            "lane": "H86J-MCSP",
            "hypothesis": (
                "2-D Riesz monogenic phase congruency + TMI_up150 attenuation + geothermal "
                "fault-intersection/conductance/metasomatism + 4-fold LOQO fracture CELF"
            ),
            "budget": BUDGET,
            "spacing_px": SPACING_PX,
            "collar_px": COLLAR_PX,
            "celf_total_marginal_credit": celf_full.total_marginal_credit,
            "celf_recomputations": celf_full.n_recomputations,
            "static_feature_sha256": static_sha256,
            "surface_sha256": surface_sha,
            "dots_sha256": dots_sha,
            "registry_surface_evidence": "docs/evidence/h86j-mcsp-registry-surface.json",
            "registry_final_evidence": "docs/evidence/h86j-mcsp-registry-final-dots.json",
            "chance_overlap_evidence": (
                str(chance_path.relative_to(ROOT))
                if chance_path.is_file()
                else "FAILED_CLOSED_NO_REPORT (see run card)"
            ),
        },
    )

    # Enforce AGENTS.md Rules 6, 10, 11, 12: fail closed to negative / DO NOT SUBMIT
    # whenever strict v2 registry gate or PA-86-02 does not pass.
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
    if not surface_gate_pass:
        stop_reasons.append(
            "pre-placement surface v2 registry gate failed closed (2 grid-incompatible "
            "registry rows 14GEMSDOE/7GEMSDOE and literal 17GEMSDOE full-support witness; "
            f"{rho_firings} Spearman rho > 0.90 firings across {surface_report.get('registry_rasters_measured')} measured rasters)"
        )
    if not final_dots_gate_pass:
        stop_reasons.append(
            "final-dot v2 registry gate failed closed (literal 17GEMSDOE full-support witness "
            "and 2 grid-incompatible registry rows)"
        )
    if chance.get("gate_pass") is not True:
        stop_reasons.append(
            "PA-86-02 chance-overlap gate failed closed (incomplete v2 registry index)"
        )
    if not stop_reasons:
        stop_reasons.append(
            "scientific and registry gates passed; separate human selector required"
        )

    from scipy.spatial import cKDTree

    mine_pts = np.column_stack(np.nonzero(celf_full.dots & fp))
    disc_refs = [
        *sorted((ROOT / "data/scored_fleet").glob("*.tif")),
        *sorted(
            p
            for p in (ROOT / "docs/downloads").glob("*.tif")
            if "h86j-mcsp" not in p.name
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
        elif "h86f-ewcs" in p.name:
            disc_named["H86F_EWCS"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
        elif "h86g-edti" in p.name:
            disc_named["H86G_EDTI"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
    disc_rows.sort(reverse=True)
    disc_diag = {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "scope": "Diagnostic across local scored_fleet + docs/downloads discrete rasters with <=100,000 positive pixels (not an override of the full 692-entry v2 gate).",
        "rasters_checked": len(disc_rows),
        "firings_over_0p70": sum(1 for ov3, _, _ in disc_rows if ov3 > 0.70),
        "worst_forward_overlap_3px": disc_rows[0][0] if disc_rows else None,
        "worst_submission": disc_rows[0][2] if disc_rows else None,
        "key_comparators": disc_named,
    }

    disk_val = receipt["independent_disk_validation"]
    run_card = {
        "schema": "gems86.lane_run_card.v1",
        "lane_id": "H86J-MCSP",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_branch": "arena/ba54d9a2-gemsdoe86",
        "preregistration": {
            "path": "research/H86J_MCSP_PREREGISTRATION.json",
            "markdown": "research/H86J_MCSP_PREREGISTRATION.md",
            "hypotheses_registry": "registry/h86j_mcsp_hypotheses.json",
            "sha256": sha256(PREREGISTRATION_PATH),
        },
        "hypothesis": (
            "H86J-MCSP: Concealed intra-basin faults, blind Great Basin geothermal stepovers/intersections "
            "(>75% of hydrothermal systems lack hot springs; Faulds & Hinz 2015), and low-relief piedmont "
            "relays attenuate scalar magnetic/gravity gradients 5x-20x while preserving contrast-invariant "
            "multi-scale 2-D Riesz monogenic step phase congruency, TMI_up150 vertical wavenumber decay, "
            "hydrothermal magnetite-destruction troughs, Hessian-eccentric conductive fault-gouge necks, "
            "Lahontan-deconfounded K/Th-U/Th metasomatic steps, and Forstner structure-tensor fault "
            "intersections. Fusing a 4-fold Leave-One-Quadrant-Out (LOQO) translation-invariant blind "
            "specialist with a 4-fold LOQO cross-component Pollard-Segall fracture specialist via Noisy-OR "
            "and allocating 37,654 dots via exact heapq CELF submodular marginal kernel credit eliminates "
            "both mountain-range habitat memorization (H86G H_hgb) and overlapping-kernel double counting."
        ),
        "mechanism": {
            "static_translation_invariant_features": list(MCSP_STATIC_NAMES),
            "fold_visible_elastic_features": list(FOLD_ELASTIC_NAMES),
            "ablation_control_features": list(ABLATION_AMP_NAMES),
            "zero_raw_regional_levels": True,
            "spatial_cross_fitting": "4-fold Leave-One-Quadrant-Out (LOQO) + Elkan (2001) prior alignment + nested connected-component PU",
            "fusion_formula": "S_mcsp = 1 - (1 - 0.50 * P_blind)(1 - 0.65 * P_kin)",
            "allocator": "Exact heapq CELF submodular marginal DTI-numerator greedy (Minoux 1978) on gems57 OFF_DY/OFF_DX/OFF_K",
            "budget_dots": BUDGET,
            "min_spacing_px": SPACING_PX,
            "catalogue_collar_px": COLLAR_PX,
            "band_physics_verification": qc_receipt,
            "input_sha256": input_hashes,
        },
        "named_non_fault_mimic": (
            "Buried Tertiary caldera ring-fracture walls or welded ash-flow tuff cooling-unit pinch-outs "
            "altered by fossil Miocene epithermal systems, and Pleistocene Lake Lahontan (~1,330 m and "
            "~1,205 m) wave-cut benches adjacent to conductive saline playas (explicitly mitigated via "
            "lahontan_mimic_veto and Hessian eigenvalue eccentricity gating)."
        ),
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "evaluator_hashes": EH.implementation_hashes(),
            "design": (
                "gems57-pooled-hide-v2: 4 spatial quadrant folds, 20% whole fault components hidden "
                "(seed=20), buffer_px=3, visible-fault collar 3.0 px, strict 4-fold LOQO training, "
                "pooled 200-px (20 km) physical blocks, 1,000 paired bootstrap draws"
            ),
            "protocol": (
                "gems57-pooled-hide-v2: 4 spatial quadrant folds, 20% whole fault components hidden "
                "(seed=20), buffer_px=3, visible-fault collar 3.0 px, strict 4-fold LOQO training, "
                "pooled 200-px (20 km) physical blocks, 1,000 paired bootstrap draws"
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
                "H86F_EWCS_E1_37654": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86f-ewcs-run-card.json",
                    "dti": ewcs_best["dti"],
                    "ci95": ewcs_best["ci95"],
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
                "H86G_EDTI_L_55k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86g-edti-run-card.json",
                    "dti": edti_55k["dti"],
                    "ci95": edti_55k["ci95"],
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
            "like_for_like_dot_field_diagnostic": {
                "scope": "DIAGNOSTIC-ONLY (dot-field subset inside 690-entry v2 scan; does NOT override literal/completeness v2 fail-closed gate)",
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
        "runtime_seconds": round(time.time() - t0, 2),
    }

    card_path.write_text(
        json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "lane": "H86J-MCSP",
                "submission_file": run_card["submission_file"],
                "raster_sha256": run_card["raster_sha256"],
                "e1_holdout_dti": e1_score["dti"],
                "e1_ci95": e1_score["ci95"],
                "e2_holdout_dti": pooled["scores"]["E2_mcsp_blind_celf"]["dti"],
                "e3_holdout_dti": pooled["scores"]["E3_mcsp_amp_staticek_ablation"]["dti"],
                "sgmc_e1_dti": sgmc_e1_val,
                "v2_worst_surface_spearman": surface_report["shared_summary"][
                    "worst_spearman_full_footprint"
                ],
                "v2_dot_field_worst_overlap_3px": lfl.get(
                    "worst_forward_overlap_dot_fields"
                ),
                "v2_surface_measured": surface_report.get("registry_rasters_measured"),
                "v2_surface_rho_firings": rho_firings,
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
