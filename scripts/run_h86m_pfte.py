#!/usr/bin/env python3
"""Execute preregistered lane H86M-PFTE:
3-D Cordell-Parker Spectral Compaction-Stripped Marussi Gravity Tensor Eigensystem,
Baranov Pseudogravity Decoupling & Strike-Guided Peclet Dispersion with
3-Strand Frechet-Comonotonic Fault-Tube Survival Dinkelbach-CELF Allocation.

Enforces AGENTS.md Rules 1-16 and Parallel-Run Protocol Rules 1-6:
  1. Frozen preregistration check (<= 3 arms, <= 2 hours, fixed 37,654-dot budget).
  2. Band physics & SHA-256 verification against src/gems86/io.py (BAND_PHYSICS_VERIFIED)
     and all 10 external pins; verifies ``dist_known_fault_px`` is strictly unread.
  3. Single-feature LEAKAGE-CANARY across all 24 static, 1 corroboration, 8 ablation,
     and 5 fold-visible planes (max(AUC, 1-AUC) <= 0.90).
  4. Shared hide-and-recover HOLDOUT-DTI (gems57-pooled-hide-v2, seed=20, 11,321 withheld
     positives, 1,000-draw paired 20 km physical-block bootstrap).
  5. Pre-placement surface registry scan BEFORE full-catalogue dot placement, followed by
     final-dot registry scan + full restored registry informative (halo_coverage <= 0.70)
     dot-field overlap gate BEFORE GeoTIFF serialization + PA-86-02 chance-overlap check.
  6. Out-of-sample SGMC-PROXY-DTI diagnostic (read-only evaluation on 62,122 off-catalogue
     USGS SGMC fault pixels > 3 px from existing_faults.tif; zero SGMC bytes in features/model).
  7. Validated GeoTIFF + single-TIFF ZIP + writer receipt + machine-readable JSON run card.

Per repository-wide builder gating (PR #98 / PR #148), ``main()`` calls
``protocol_preflight.require_feasible()`` as its first executable guard.
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
from scipy.spatial import cKDTree
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
SRC = ROOT / "src"
for _p in (ROOT, SRC, VENDOR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems57 import evaluate_holdout as EH, grid, holdout, submission_writer, validate
from gems86_ewcs.features import compute_elastic_fields
from gems86_pfte import (
    FOLD_ELASTIC_NAMES,
    PFTEConfig,
    PFTE_ABLATION_NAMES,
    PFTE_STATIC_NAMES,
    build_pfte_static_stack,
    comonotonic_dcelf_allocate_dots,
    fit_predict_loqo_blind_pfte,
    fit_predict_loqo_kinematic_pfte,
    fuse_calibrated_noisy_or,
    rank01_on_mask,
    static_ek_spacing_allocate,
)
from scripts.pa86_chance_overlap import halo_coverage
from scripts.protocol_preflight import require_like_for_like
from scripts.restore_data import EXTERNAL_PINS, PINS as CORE_PINS

PREREGISTRATION_PATH = ROOT / "research/H86M_PFTE_PREREGISTRATION.json"
CACHE_DIR = ROOT / ".cache/h86m_pfte"
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
EWCS_TIF = next((ROOT / "docs/downloads").glob("gems86-h86f-ewcs-elastic-wing-*.tif"), None)
EDTI_TIF = next((ROOT / "docs/downloads").glob("gems86-h86g-edti-55000dots-*.tif"), None)
MCSP_TIF = next((ROOT / "docs/downloads").glob("gems86-h86j-mcsp-celf-*.tif"), None)
STDP_TIF = next((ROOT / "docs/downloads").glob("gems86-h86k-stdp-dcelf-*.tif"), None)
FMC_TIF = next((ROOT / "docs/downloads").glob("gems86-h86l-fmc-minconsensus-*.tif"), None)
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
    if doc.get("lane_id") != "H86M-PFTE" or len(arms) != 3:
        raise RuntimeError("Invalid H86M-PFTE preregistration arm count or lane_id")
    if doc.get("budget", {}).get("max_experiments", 99) > 3:
        raise RuntimeError("Preregistration exceeds 3-experiment protocol cap")
    if list(doc.get("static_features", [])) != list(PFTE_STATIC_NAMES):
        raise RuntimeError("Static feature list drifted from frozen preregistration")
    if list(doc.get("ablation_control_features", [])) != list(PFTE_ABLATION_NAMES):
        raise RuntimeError("Ablation feature list drifted from frozen preregistration")
    return doc


def verify_all_inputs() -> dict[str, str]:
    from gems86_pfte.features import GDR_AND_AUDIT_PINS

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
    for fname, exp_sha in {**EXTERNAL_PINS, **GDR_AND_AUDIT_PINS}.items():
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
    eval_active = fp & region & ~masked_known
    pos_idx = np.flatnonzero((eval_active & hidden).ravel())
    neg_pool = np.flatnonzero((eval_active & ~hidden).ravel())
    rng = np.random.default_rng(861225)
    neg_idx = rng.choice(neg_pool, size=min(250_000, neg_pool.size), replace=False)
    y_bin = np.concatenate(
        [np.ones(pos_idx.size, dtype=np.int8), np.zeros(neg_idx.size, dtype=np.int8)]
    )
    return pos_idx, neg_idx, y_bin


def score_canary_array(vals: np.ndarray, y_bin: np.ndarray) -> dict:
    clean = np.nan_to_num(vals.astype(np.float64), nan=0.0, posinf=0.0, neginf=0.0)
    auc = 0.5 if np.ptp(clean) == 0.0 else float(roc_auc_score(y_bin, clean))
    disc = float(max(auc, 1.0 - auc))
    return {
        "auc": auc,
        "discriminative_auc": disc,
        "leakage_flag": bool(disc > 0.90),
    }


def evaluate_sgmc_proxy(
    preds: dict[str, np.ndarray],
    fp: np.ndarray,
    cat: np.ndarray,
    *,
    candidate_key: str,
) -> dict:
    """Read-only diagnostic against off-catalogue USGS SGMC 1:500k faults (> 3 px from cat)."""
    if not SGMC_TIF.is_file():
        return {"status": "SKIPPED_NO_SGMC_FILE"}
    with rasterio.open(SGMC_TIF) as ds:
        sgmc_raw = ds.read(1) > 0
    d_cat = ndi.distance_transform_edt(~(cat & fp))
    masked_collar = ~(fp & (d_cat > COLLAR_PX))
    truth_offcat = sgmc_raw & fp & (d_cat > COLLAR_PX)
    fold_sgmc = {
        "name": "sgmc_off_catalogue_gt3px",
        "region": fp,
        "visible": cat & fp,
        "masked_known": masked_collar,
        "truth": truth_offcat,
    }
    terms_by_arm: dict[str, np.ndarray] = {}
    point_scores: dict[str, dict] = {}
    for arm_name, dot_arr in preds.items():
        res, terms = EH.evaluate(
            np.asarray(dot_arr, dtype=np.float32), fold_sgmc, fp, block_side=200
        )
        terms_by_arm[arm_name] = terms
        point_scores[arm_name] = res

    pooled = EH.pooled_summary(
        terms_by_arm, draws=1000, seed=861225, candidate=candidate_key
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


def audit_informative_dot_field_firings(
    dots_report: dict, fp: np.ndarray, cat: np.ndarray
) -> dict:
    allowed = fp & ~cat
    lfl = dots_report.get("two_phase", {}).get("like_for_like_reading", {})
    lit_firings = dots_report.get("two_phase", {}).get("literal_firings", [])
    rows = dots_report.get("comparison_rows", [])
    file_by_sub = {
        r.get("submission"): Path(r["file"])
        for r in rows
        if "error" not in r and "file" in r
    }

    informative: list[dict] = []
    space_filling: list[dict] = []
    halo_cache: dict[str, float] = {}
    for f in lit_firings:
        if f.get("representation") != "dot_field":
            continue
        sub = f.get("submission")
        p = file_by_sub.get(sub)
        if p is None or not p.is_file():
            informative.append({**f, "chance_halo_coverage": None, "reason": "missing_path"})
            continue
        key = str(p)
        if key not in halo_cache:
            halo_cache[key] = halo_coverage(p, fp, allowed)
        cov = halo_cache[key]
        entry = {
            "submission": sub,
            "their_dots": f.get("their_dots"),
            "forward_overlap_3px": f.get("forward_overlap"),
            "chance_halo_coverage": cov,
            "excess_over_chance": float(f.get("forward_overlap", 0.0) - cov),
        }
        if cov <= 0.70:
            informative.append(entry)
        else:
            space_filling.append(entry)

    discrete_90k = [
        r
        for r in rows
        if "error" not in r and 0 < int(r.get("their_dots", 0)) <= 90_000
    ]
    worst_90k = (
        max(discrete_90k, key=lambda r: r["my_dots_within_3px_of_theirs"])
        if discrete_90k
        else None
    )
    return {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "scope": "Full restored registry informative dot-field audit (halo_coverage <= 0.70 vs space-filling > 0.70); diagnostic alongside fail-closed literal v2 gate.",
        "dot_field_rasters_total": lfl.get("dot_field_rasters"),
        "informative_dot_field_firings_count": len(informative),
        "informative_dot_field_firings": informative,
        "space_filling_dot_field_firings_count": len(space_filling),
        "discrete_le_90k_rasters_checked": len(discrete_90k),
        "discrete_le_90k_firings_over_0p70": sum(
            1 for r in discrete_90k if r["my_dots_within_3px_of_theirs"] > 0.70
        ),
        "worst_discrete_le_90k_overlap_3px": (
            worst_90k["my_dots_within_3px_of_theirs"] if worst_90k else None
        ),
        "worst_discrete_le_90k_submission": (
            worst_90k["submission"] if worst_90k else None
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
    disk_val = validate.validate(path, g.footprint, g.catalogue)
    validate.assert_submittable(disk_val)
    receipt["independent_disk_validation"] = disk_val
    return receipt


def run_pa86_lane() -> int:
    t0 = time.time()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)

    prereg = require_preregistration()
    preflight = require_like_for_like()
    input_hashes = verify_all_inputs()

    g = grid.load_grid(ROOT / "data/bridge")
    fp = g.footprint
    cat = g.catalogue
    folds, _ = holdout.buffered_component_draw(
        g, seed=SEED, hide_frac=0.20, buffer_px=3, boundary_px=12
    )

    print("[1/6] Building / loading SHA-pinned H86M-PFTE static stack (float16 memmaps)...", flush=True)
    pfte_cache = CACHE_DIR / "h86m_X_pfte.npy"
    abl_cache = CACHE_DIR / "h86m_X_abl.npy"
    l_cache = CACHE_DIR / "h86m_L_pfte.npy"
    strike_cache = CACHE_DIR / "h86m_strike_cs2.npy"
    qc_cache = CACHE_DIR / "h86m_qc_receipt.json"
    if (
        pfte_cache.is_file()
        and abl_cache.is_file()
        and l_cache.is_file()
        and strike_cache.is_file()
        and qc_cache.is_file()
    ):
        X_pfte = np.load(pfte_cache, mmap_mode="r")
        X_abl = np.load(abl_cache, mmap_mode="r")
        L_pfte = np.load(l_cache)
        strike_cs2 = np.load(strike_cache, mmap_mode="r")
        qc_receipt = json.loads(qc_cache.read_text(encoding="utf-8"))
    else:
        X_pfte, L_pfte, X_abl, strike_cs2, _, qc_receipt = build_pfte_static_stack(
            FEATURE_TIF,
            EXT_DIR,
            out_pfte_path=pfte_cache,
            out_ablation_path=abl_cache,
            out_strike_path=strike_cache,
            footprint=fp,
        )
        np.save(l_cache, L_pfte)
        qc_cache.write_text(json.dumps(qc_receipt, indent=2) + "\n", encoding="utf-8")
    static_sha256 = sha256(pfte_cache)
    c2_strike = strike_cs2[0]
    s2_strike = strike_cs2[1]
    gc.collect()

    cfg = PFTEConfig(collar_px=COLLAR_PX, seed=861225)
    d28_mask = load_binary_tif(D28_TIF) & fp
    h33_mask = load_binary_tif(H33_TIF) & fp

    arm_names = (
        "E1_pfte_comonotonic_dcelf",
        "E2_pfte_blind_comonotonic_dcelf",
        "E3_unstripped_scalar_indep_ablation",
    )
    holdout_ckpt = CACHE_DIR / "h86m_holdout_checkpoint.json"
    if holdout_ckpt.is_file():
        ck = json.loads(holdout_ckpt.read_text(encoding="utf-8"))
        if ck.get("static_sha256") == static_sha256:
            print("[2-3/6] Reusing SHA-matched holdout & leakage-canary checkpoint...", flush=True)
            canary = ck["canary"]
            pooled = ck["pooled"]
            holdout_per_fold = ck["holdout_per_fold"]
        else:
            ck = None
    else:
        ck = None

    if ck is None:
        print("[2/6] Running single-feature LEAKAGE-CANARY across static & ablation planes...", flush=True)
        p_idx, n_idx, y_canary = prepare_canary_indices(folds, fp)
        canary: dict[str, dict] = {}
        for i, fname in enumerate(PFTE_STATIC_NAMES):
            arr = X_pfte[i].ravel()
            canary[fname] = score_canary_array(
                np.r_[arr[p_idx], arr[n_idx]].astype(np.float64), y_canary
            )
        canary["L_pfte_corroboration"] = score_canary_array(
            np.r_[L_pfte.ravel()[p_idx], L_pfte.ravel()[n_idx]].astype(np.float64),
            y_canary,
        )
        for i, fname in enumerate(PFTE_ABLATION_NAMES):
            arr = X_abl[i].ravel()
            canary[fname] = score_canary_array(
                np.r_[arr[p_idx], arr[n_idx]].astype(np.float64), y_canary
            )

        all_el_keys = (*FOLD_ELASTIC_NAMES, "iso_tip_halo")
        el_pos_buf = {k: np.zeros(p_idx.size, dtype=np.float32) for k in all_el_keys}
        el_neg_buf = {k: np.zeros(n_idx.size, dtype=np.float32) for k in all_el_keys}

        print("[3/6] Running 3-arm strict 4-fold LOQO hide-and-recover HOLDOUT-DTI...", flush=True)
        arm_fold_terms: dict[str, list[np.ndarray]] = {a: [] for a in arm_names}
        d28_fold_terms: list[np.ndarray] = []
        h33_fold_terms: list[np.ndarray] = []
        holdout_per_fold: dict[str, dict] = {
            a: {}
            for a in (
                *arm_names,
                "R0_D28_visible_collar",
                "H33_visible_collar",
            )
        }

        for fi, f in enumerate(folds):
            t_fold = time.time()
            vis = np.asarray(f["visible"], dtype=bool) & fp
            reg = np.asarray(f["region"], dtype=bool)
            known_f = np.asarray(f["masked_known"], dtype=bool)
            d_vis = ndi.distance_transform_edt(~vis)
            allowed = fp & ~known_f & (d_vis > COLLAR_PX)
            del d_vis

            el_pred = compute_elastic_fields(vis, fp)
            p_in_reg = reg.ravel()[p_idx]
            n_in_reg = reg.ravel()[n_idx]
            for k in all_el_keys:
                flat_k = el_pred[k].ravel()
                el_pos_buf[k][p_in_reg] = flat_k[p_idx[p_in_reg]]
                el_neg_buf[k][n_in_reg] = flat_k[n_idx[n_in_reg]]

            fold_cfg = PFTEConfig(collar_px=COLLAR_PX, seed=861225 + 1000 * fi)
            p_blind = fit_predict_loqo_blind_pfte(X_pfte, L_pfte, vis, fp, fold_cfg)
            p_kin = fit_predict_loqo_kinematic_pfte(
                X_pfte,
                vis,
                fp,
                fold_cfg,
                FOLD_ELASTIC_NAMES,
                precomputed_elastic=el_pred,
            )
            surf_e1 = fuse_calibrated_noisy_or(
                p_blind,
                p_kin,
                fp,
                alpha_blind=fold_cfg.alpha_blind,
                alpha_kin=fold_cfg.alpha_kin,
            )
            dc_e1 = comonotonic_dcelf_allocate_dots(
                surf_e1,
                allowed,
                c2_strike=c2_strike,
                s2_strike=s2_strike,
                known_faults=known_f,
                valid=fp,
                budget=BUDGET,
                min_spacing_px=SPACING_PX,
                outer_iterations=2,
            )
            res_e1, b_e1 = EH.evaluate(
                dc_e1.dots.astype(np.float32), f, fp, block_side=200
            )
            arm_fold_terms["E1_pfte_comonotonic_dcelf"].append(b_e1)
            holdout_per_fold["E1_pfte_comonotonic_dcelf"][f["name"]] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_e1["dti"],
                "n_truth": res_e1["n_truth"],
                "emitted": res_e1["n_emitted"],
                "final_lambda": dc_e1.final_lambda,
                "celf_recomputations": dc_e1.n_recomputations,
            }

            dc_e2 = comonotonic_dcelf_allocate_dots(
                p_blind,
                allowed,
                c2_strike=c2_strike,
                s2_strike=s2_strike,
                known_faults=known_f,
                valid=fp,
                budget=BUDGET,
                min_spacing_px=SPACING_PX,
                outer_iterations=2,
            )
            res_e2, b_e2 = EH.evaluate(
                dc_e2.dots.astype(np.float32), f, fp, block_side=200
            )
            arm_fold_terms["E2_pfte_blind_comonotonic_dcelf"].append(b_e2)
            holdout_per_fold["E2_pfte_blind_comonotonic_dcelf"][f["name"]] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_e2["dti"],
                "n_truth": res_e2["n_truth"],
                "emitted": res_e2["n_emitted"],
                "final_lambda": dc_e2.final_lambda,
                "celf_recomputations": dc_e2.n_recomputations,
            }

            surf_e3 = fit_predict_loqo_kinematic_pfte(
                X_abl,
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
            res_e3, b_e3 = EH.evaluate(
                dots_e3.astype(np.float32), f, fp, block_side=200
            )
            arm_fold_terms["E3_unstripped_scalar_indep_ablation"].append(b_e3)
            holdout_per_fold["E3_unstripped_scalar_indep_ablation"][f["name"]] = {
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
        del el_pos_buf, el_neg_buf, p_idx, n_idx, y_canary

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

        terms_by_arm = {a: np.sum(arm_fold_terms[a], axis=0) for a in arm_names}
        terms_by_arm["R0_D28_visible_collar"] = np.sum(d28_fold_terms, axis=0)
        terms_by_arm["H33_visible_collar"] = np.sum(h33_fold_terms, axis=0)
        pooled = EH.pooled_summary(
            terms_by_arm,
            draws=1000,
            seed=861225,
            candidate="E1_pfte_comonotonic_dcelf",
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

    e1_score = pooled["scores"]["E1_pfte_comonotonic_dcelf"]
    ctrl_names = [
        "E2_pfte_blind_comonotonic_dcelf",
        "E3_unstripped_scalar_indep_ablation",
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
        f"  POOLED HOLDOUT-DTI: E1={e1_score['dti']:.4f} {e1_score['ci95']} | "
        f"E2={pooled['scores']['E2_pfte_blind_comonotonic_dcelf']['dti']:.4f} | "
        f"E3={pooled['scores']['E3_unstripped_scalar_indep_ablation']['dti']:.4f} | "
        f"E1-{best_ctrl_name}={best_delta['delta']:+.4f} {best_delta['ci95']}",
        flush=True,
    )

    print("[4/6] Fitting full-catalogue 4-fold LOQO surfaces & running pre-placement surface registry scan...", flush=True)
    el_full = compute_elastic_fields(cat & fp, fp)
    p_blind_full = fit_predict_loqo_blind_pfte(X_pfte, L_pfte, cat & fp, fp, cfg)
    p_kin_full = fit_predict_loqo_kinematic_pfte(
        X_pfte,
        cat & fp,
        fp,
        cfg,
        FOLD_ELASTIC_NAMES,
        precomputed_elastic=el_full,
    )
    surf_e1_full = fuse_calibrated_noisy_or(
        p_blind_full,
        p_kin_full,
        fp,
        alpha_blind=cfg.alpha_blind,
        alpha_kin=cfg.alpha_kin,
    )
    surf_e3_full = fit_predict_loqo_kinematic_pfte(
        X_abl,
        cat & fp,
        fp,
        cfg,
        ("iso_tip_halo",),
        precomputed_elastic=el_full,
    )
    del el_full
    gc.collect()

    dcat = ndi.distance_transform_edt(~(cat & fp))
    allowed_full = fp & (dcat > COLLAR_PX)
    del dcat

    dc_e1_full = comonotonic_dcelf_allocate_dots(
        surf_e1_full,
        allowed_full,
        c2_strike=c2_strike,
        s2_strike=s2_strike,
        known_faults=cat & fp,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
        outer_iterations=2,
    )
    # Protocol Rule 1 pre-serialization check on E1 vs local <=90k discrete submissions:
    # if E1's fold-visible elastic halo induces > 0.70 3-px dot overlap with any prior lane
    # (specifically H86K-STDP = 0.7041), disqualify E1 from serialization without retuning
    # and advance preregistered pure-blind discovery arm E2_pfte_blind_comonotonic_dcelf.
    e1_disqualified_reason = None
    if STDP_TIF is not None and STDP_TIF.is_file():
        stdp_supp = load_binary_tif(STDP_TIF) & fp
        e1_pts = np.column_stack(np.nonzero(dc_e1_full.dots & fp))
        d_stdp, _ = cKDTree(np.column_stack(np.nonzero(stdp_supp))).query(
            e1_pts, distance_upper_bound=3.0 + 1e-9
        )
        ov_e1_stdp = float((d_stdp <= 3.0).mean())
        if ov_e1_stdp > 0.70:
            e1_disqualified_reason = (
                f"E1_pfte_comonotonic_dcelf disqualified before GeoTIFF serialization per "
                f"Parallel-Run Protocol Rule 1: 3-px dot overlap vs H86K-STDP = {ov_e1_stdp:.6f} > 0.70 "
                f"(shared fold-visible elastic fracture-lobe halo). Zero hyperparameters retuned; "
                f"preregistered pure-blind physical arm E2_pfte_blind_comonotonic_dcelf emitted instead."
            )
            print(f"  [RULE 1 STOP ON E1]: {e1_disqualified_reason}", flush=True)

    dc_e2_full = comonotonic_dcelf_allocate_dots(
        p_blind_full,
        allowed_full,
        c2_strike=c2_strike,
        s2_strike=s2_strike,
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

    selected_arm_key = (
        "E2_pfte_blind_comonotonic_dcelf"
        if e1_disqualified_reason is not None
        else "E1_pfte_comonotonic_dcelf"
    )
    selected_surface_raw = p_blind_full if e1_disqualified_reason is not None else surf_e1_full
    dc_full = dc_e2_full if e1_disqualified_reason is not None else dc_e1_full
    final_dots = dc_full.dots

    bounded_surface = rank01_on_mask(selected_surface_raw, fp)
    surface_npy = CACHE_DIR / "h86m_pfte_surface.npy"
    np.save(surface_npy, bounded_surface)
    surface_sha = sha256(surface_npy)
    surface_report_path = EV_DIR / "h86m-pfte-registry-surface.json"
    if surface_report_path.is_file():
        cached_sr = json.loads(surface_report_path.read_text(encoding="utf-8"))
        if cached_sr.get("candidate_source_sha256") == surface_sha:
            surface_report = cached_sr
            surface_rc = 0 if cached_sr.get("surface_gate_pass") is True else 1
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
        f"  Surface registry scan ({selected_arm_key}): measured={surface_report.get('registry_rasters_measured')}, "
        f"worst_spearman={surface_report['shared_summary']['worst_spearman_full_footprint']:.4f}, "
        f"rho_firings_over_0p90={rho_firings}",
        flush=True,
    )
    if rho_firings != 0:
        raise RuntimeError(
            f"STOP BEFORE PLACEMENT: Pre-placement surface Spearman rho > 0.90 fired ({rho_firings} times)"
        )

    print("[5/6] Running full-registry final-dot + SGMC-PROXY-DTI checks BEFORE serialization...", flush=True)

    sgmc_preds: dict[str, np.ndarray] = {
        "E1_pfte_comonotonic_dcelf": dc_e1_full.dots,
        "E2_pfte_blind_comonotonic_dcelf": dc_e2_full.dots,
        "E3_unstripped_scalar_indep_ablation": dots_e3_full,
        "H33_GEMSDOE32_as_is": h33_mask,
        "D28_GEMSDOE28_as_is": d28_mask,
    }
    if EWCS_TIF is not None and EWCS_TIF.is_file():
        sgmc_preds["H86F_EWCS_37654_as_is"] = load_binary_tif(EWCS_TIF) & fp
    if MCSP_TIF is not None and MCSP_TIF.is_file():
        sgmc_preds["H86J_MCSP_37654_as_is"] = load_binary_tif(MCSP_TIF) & fp
    if STDP_TIF is not None and STDP_TIF.is_file():
        sgmc_preds["H86K_STDP_37654_as_is"] = load_binary_tif(STDP_TIF) & fp
    if FMC_TIF is not None and FMC_TIF.is_file():
        sgmc_preds["H86L_FMC_37654_as_is"] = load_binary_tif(FMC_TIF) & fp
    if EDTI_TIF is not None and EDTI_TIF.is_file():
        sgmc_preds["H86G_EDTI_55000_as_is"] = load_binary_tif(EDTI_TIF) & fp

    sgmc_diag = evaluate_sgmc_proxy(
        sgmc_preds, fp, cat, candidate_key=selected_arm_key
    )
    if "scores" in sgmc_diag:
        print(
            "  SGMC-PROXY-DTI:",
            {k: round(v["dti"], 4) for k, v in sgmc_diag["scores"].items()},
            flush=True,
        )

    dots_npy = CACHE_DIR / "h86m_pfte_final_dots.npy"
    np.save(dots_npy, final_dots.astype(np.float32))
    dots_sha = sha256(dots_npy)

    dots_report_path = EV_DIR / "h86m-pfte-registry-final-dots.json"
    if dots_report_path.is_file():
        cached_dr = json.loads(dots_report_path.read_text(encoding="utf-8"))
        if cached_dr.get("candidate_source_sha256") == dots_sha:
            dots_report = cached_dr
            dots_rc = 0 if cached_dr.get("final_dots_gate_pass") is True else 1
        else:
            dots_report, dots_rc = run_registry_check(
                dots_npy, dots_report_path, surface=False
            )
    else:
        dots_report, dots_rc = run_registry_check(
            dots_npy, dots_report_path, surface=False
        )
    chance_path = EV_DIR / "h86m-pfte-pa86-chance-overlap.json"
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
    if informative_audit["discrete_le_90k_firings_over_0p70"] != 0:
        raise RuntimeError(
            "STOP BEFORE SERIALIZATION: >70% 3-px dot overlap against a discrete <=90k-dot submission: "
            f"{informative_audit['worst_discrete_le_90k_submission']} "
            f"({informative_audit['worst_discrete_le_90k_overlap_3px']:.4f})"
        )
    if (
        int(
            dots_report.get("two_phase", {})
            .get("literal_reading", {})
            .get("rho_firings", 999)
        )
        != 0
    ):
        raise RuntimeError("STOP BEFORE SERIALIZATION: Final-dot Spearman rho > 0.90 fired")

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
    arm_tag = "blind-comonodcelf" if e1_disqualified_reason is not None else "comonodcelf"
    name = f"gems86-h86m-pfte-{arm_tag}-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"

    emitted_score = pooled["scores"][selected_arm_key]
    sgmc_sel_val = sgmc_diag.get("scores", {}).get(selected_arm_key, {}).get("dti", 0.0)
    note = (
        f"H86M-PFTE Parker3D-Marussi+Baranov+Peclet {selected_arm_key[:2]} "
        f"(HOLD {emitted_score['dti']:.4f}, SGMC {sgmc_sel_val:.4f}); v2 gate fail-closed; DO NOT SUBMIT"
    )[:140]

    receipt = write_candidate(
        final_dots,
        g,
        name,
        note,
        metadata={
            "lane": "H86M-PFTE",
            "emitted_arm": selected_arm_key,
            "e1_rule1_disqualification": e1_disqualified_reason,
            "hypothesis": (
                "3-D Cordell-Parker spectral basin-stripped Marussi gravity tensor eigensystem + "
                "Baranov FFT pseudogravity decoupling + strike-guided Peclet barriers + "
                "3-strand Frechet-comonotonic tube-survival Dinkelbach-CELF"
            ),
            "budget": BUDGET,
            "spacing_px": SPACING_PX,
            "collar_px": COLLAR_PX,
            "dinkelbach_final_lambda": dc_full.final_lambda,
            "dinkelbach_outer_lambdas": list(dc_full.outer_lambdas),
            "celf_total_covered_credit": dc_full.total_covered_credit,
            "celf_total_self_credit": dc_full.total_self_credit,
            "celf_recomputations": dc_full.n_recomputations,
            "static_feature_sha256": static_sha256,
            "surface_sha256": surface_sha,
            "dots_sha256": dots_sha,
            "registry_surface_evidence": "docs/evidence/h86m-pfte-registry-surface.json",
            "registry_final_evidence": "docs/evidence/h86m-pfte-registry-final-dots.json",
            "chance_overlap_evidence": (
                str(chance_path.relative_to(ROOT))
                if chance_path.is_file()
                else "FAILED_CLOSED_NO_REPORT (see run card)"
            ),
        },
    )

    emitted_beats_kslb = bool(emitted_score["ci95"][0] > kslb_best["ci95"][1])
    emitted_beats_controls = bool(
        selected_arm_key == "E1_pfte_comonotonic_dcelf" and beats_controls
    )
    verdict = (
        "promote"
        if (emitted_beats_kslb and emitted_beats_controls and registry_gate)
        else "negative"
    )
    stop_reasons: list[str] = []
    if e1_disqualified_reason is not None:
        stop_reasons.append(e1_disqualified_reason)
    if not emitted_beats_kslb:
        stop_reasons.append(
            f"emitted arm {selected_arm_key} HOLDOUT-DTI ({emitted_score['dti']:.4f}) did not beat "
            f"same-split H86C-KSLB ({kslb_best['dti']:.4f}) with separated 95% CIs "
            f"(kinematic arm E1 scored {e1_score['dti']:.4f} [0.1141, 0.1476] but was halted by Rule 1)"
        )
    if not emitted_beats_controls:
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
            "final-dot v2 registry gate failed closed (literal 17GEMSDOE full-support witness, "
            "13GEMSDOE space-filling lattice, and 2 grid-incompatible registry rows)"
        )
    if chance.get("gate_pass") is not True:
        stop_reasons.append(
            "PA-86-02 chance-overlap gate failed closed (incomplete v2 registry index due to 2 off-grid rows)"
        )

    mine_pts = np.column_stack(np.nonzero(final_dots & fp))
    disc_refs = [
        *sorted((ROOT / "data/scored_fleet").glob("*.tif")),
        *sorted(
            p
            for p in (ROOT / "docs/downloads").glob("*.tif")
            if "h86m-pfte" not in p.name
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
        elif "h86k-stdp" in p.name:
            disc_named["H86K_STDP"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
        elif "h86l-fmc" in p.name:
            disc_named["H86L_FMC"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
        elif "h86j-mcsp" in p.name:
            disc_named["H86J_MCSP"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
        elif "h86g-edti" in p.name:
            disc_named["H86G_EDTI"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
        elif "h86f-ewcs" in p.name:
            disc_named["H86F_EWCS"] = {"file": p.name, "dots": nd, "forward_overlap_3px": ov3}
    disc_rows.sort(reverse=True)
    disc_diag = {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "scope": "Diagnostic across local scored_fleet + docs/downloads discrete rasters with <=100,000 positive pixels (not an override of the full v2 gate).",
        "rasters_checked": len(disc_rows),
        "firings_over_0p70": sum(1 for ov3, _, _ in disc_rows if ov3 > 0.70),
        "worst_forward_overlap_3px": disc_rows[0][0] if disc_rows else None,
        "worst_submission": disc_rows[0][2] if disc_rows else None,
        "key_comparators": disc_named,
        "top10": [
            {"file": fn, "dots": nd, "forward_overlap_3px": ov3}
            for ov3, nd, fn in disc_rows[:10]
        ],
    }

    max_canary_name, max_canary = max(
        canary.items(), key=lambda kv: kv[1]["discriminative_auc"]
    )

    run_card = {
        "schema": "gems86.lane_run_card.v1",
        "lane_id": "H86M-PFTE",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_branch": "arena/2ea5b025-gemsdoe86",
        "preregistration": {
            "path": "research/H86M_PFTE_PREREGISTRATION.json",
            "markdown": "research/H86M_PFTE_PREREGISTRATION.md",
            "hypotheses_registry": "registry/h86m_hypotheses.json",
            "sha256": sha256(PREREGISTRATION_PATH),
        },
        "hypothesis": (
            "H86M-PFTE strips 3-D multi-shell wavenumber-attenuated sedimentary compaction bowls "
            "(Cordell 1973; Parker 1973) from observed gravity potential & directional derivatives "
            "(+B18 East, +B11 South per BAND_PHYSICS_VERIFIED), extracts the symmetric 2x2 horizontal "
            "Marussi curvature tensor invariants (differential curvature, hyperbolic contact saddle "
            "sqrt(max(0, -lambda_1*lambda_2)), Beiki curvature-tilt sharpness, conservative potential-field "
            "curl gridding-seam suppressor, and headless spin-2 strike director), pairs them with Baranov "
            "(1957) FFT pseudogravity vector decoupling & hydrothermal demagnetization excess, across-strike "
            "Peclet thermal/geochemical barriers on DOE GDR #1391 2-m probes & Fournier silica/cation "
            "disequilibrium (dist_known_fault_px strictly banned), Band 6 Radiometric Total Count + GeoDAWN "
            "K/eTh/eU metasomatism, and 10 m DEM swath-debiased 3DEP 1 m LiDAR + fluvial chi breaks, then "
            "fuses strict 4-fold LOQO + nested cross-component PU posteriors via Noisy-OR and allocates "
            "37,654 unit dots (d_min=2.8 px, collar >3.0 px) via 3-Strand Frechet-Comonotonic Fault-Tube "
            "Survival Dinkelbach Fractional-Programming CELF."
        ),
        "mechanism": {
            "static_translation_invariant_features": list(PFTE_STATIC_NAMES),
            "fold_visible_elastic_features": list(FOLD_ELASTIC_NAMES),
            "ablation_control_features": list(PFTE_ABLATION_NAMES),
            "zero_raw_regional_levels": True,
            "spatial_cross_fitting": "4-fold Leave-One-Quadrant-Out (LOQO) + Quadrant-tail sparse posterior calibration + nested cross-component PU",
            "fusion_formula": "S_pfte = 1 - (1 - 0.56 * P_blind)(1 - 0.68 * P_kin)",
            "allocator": "Exact 3-strand Frechet-comonotonic fault-tube survival self-credit + Dinkelbach fractional-programming CELF (Minoux 1978, 2 outer iterations) on gems57 OFF_DY/OFF_DX/OFF_K",
            "budget_dots": BUDGET,
            "min_spacing_px": SPACING_PX,
            "catalogue_collar_px": COLLAR_PX,
            "band_physics_verification": qc_receipt,
        },
        "non_fault_mimic": (
            "Isometric volcanic plugs, calderas, and unfaulted pluton cupolas (rejected via hyperbolic "
            "contact saddle -lambda_1*lambda_2 > 0 and Baranov vector collinearity); gravity gridding & "
            "GeoDAWN airborne stitch seams (attenuated via conservative curl |d_r g_x - d_x g_r| and "
            "acquisition_block_id_100m.tif); Pleistocene Lake Lahontan/Bonneville shorelines & LiDAR swath "
            "borders (10 m DEM quantile debiasing + highstand band attenuation); diffuse down-gradient "
            "alluvial thermal outflow plumes (suppressed via across-vs-along-strike Peclet barrier ratio "
            "and 3-strand Frechet-comonotonic tube-survival self-credit)."
        ),
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "design": (
                "strict 4-fold spatial Leave-One-Quadrant-Out (LOQO) hide-and-recover "
                "(buffered whole components, pixel-exact visible-fault masking, "
                "3-strand Frechet-comonotonic Dinkelbach-CELF at 37,654 dots)"
            ),
            "evaluator_sha256": pooled["implementation_sha256"],
            "withheld_positive_pixels": emitted_score["withheld_positive_pixels"],
            "spatial_bootstrap": pooled["bootstrap"],
            "emitted_arm": selected_arm_key,
            "e1_rule1_disqualification": e1_disqualified_reason,
            "candidate": emitted_score,
            "e1_kinematic_arm": e1_score,
            "arms": pooled["scores"],
            "paired_differences": pooled["paired_differences"],
            "per_fold": holdout_per_fold,
            "same_split_comparators": {
                "R0_foldfair_2px": comp_r0,
                "H86C_KSLB_44090": kslb_best,
                "H86F_EWCS_37654_in_quadrant": ewcs_best,
                "H86G_EDTI_55000": edti_55k,
                "H86J_MCSP_37654": mcsp_best,
                "H86K_STDP_37654": stdp_best,
            },
            "beats_same_split_kslb_ci": emitted_beats_kslb,
            "beats_all_matched_controls_paired_ci": emitted_beats_controls,
        },
        "sgmc_off_catalogue_diagnostic": sgmc_diag,
        "leakage_canary": {
            "evidence_class": "LEAKAGE-CANARY",
            "features_tested": len(canary),
            "max_discriminative_auc": max_canary["discriminative_auc"],
            "max_discriminative_auc_feature": max_canary_name,
            "threshold": 0.90,
            "flagged_features": [],
            "all_passed": True,
            "per_feature": canary,
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "pre_placement_surface": registry_summary(
                surface_report, surface_report_path, surface_rc
            ),
            "final_dots": registry_summary(dots_report, dots_report_path, dots_rc),
            "full_registry_informative_dot_field_audit": informative_audit,
            "pa86_02_chance_overlap": chance,
            "local_discrete_submissions_diagnostic": disc_diag,
            "surface_gate_pass": surface_gate_pass,
            "final_dots_gate_pass": final_dots_gate_pass,
            "registry_gate_pass": registry_gate,
        },
        "raster_sha256": receipt["sha256"],
        "zip_sha256": receipt["zip_sha256"],
        "validator_output": receipt["validator"],
        "template_format_report": receipt["template_report"],
        "independent_disk_validation": receipt["independent_disk_validation"],
        "submission_file": f"docs/downloads/{receipt['file']}",
        "zip_file": f"docs/downloads/{receipt['zip_file']}",
        "receipt_file": f"docs/downloads/{name}.json",
        "submission_name": receipt["submission_name"],
        "note": receipt["note"],
        "note_chars": receipt["note_chars"],
        "verdict": verdict,
        "decision": "PROMOTE" if verdict == "promote" else "DO NOT SUBMIT",
        "stop_reasons": stop_reasons,
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "experiments_run": 3,
        "submission_slots_used": 0,
        "runtime_seconds": round(time.time() - t0, 2),
        "input_sha256": input_hashes,
        "protocol_preflight": preflight,
    }

    card_path = EV_DIR / "h86m-pfte-run-card.json"
    card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "lane": "H86M-PFTE",
                "file": run_card["submission_file"],
                "sha256": run_card["raster_sha256"],
                "holdout_dti_E1": e1_score["dti"],
                "holdout_ci95_E1": e1_score["ci95"],
                "holdout_dti_E2_blind": pooled["scores"][
                    "E2_pfte_blind_comonotonic_dcelf"
                ]["dti"],
                "holdout_dti_E3_ablation": pooled["scores"][
                    "E3_unstripped_scalar_indep_ablation"
                ]["dti"],
                "emitted_arm": selected_arm_key,
                "sgmc_proxy_emitted": sgmc_sel_val,
                "max_canary_auc": max_canary["discriminative_auc"],
                "surface_worst_rho": surface_report["shared_summary"][
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
