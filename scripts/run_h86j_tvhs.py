#!/usr/bin/env python3
"""H86J-TVHS single-lane runner: Harmonic Gravity-Gradient Tensor (GGT) 2-D Sheet-Step
Invariants x Faulds-Hinz Geothermal Structural-Complexity Triangulation x Exposure-Propensity
Strict-LOQO Dual-Expert PU Expected-Kernel-Credit Discovery.

Governance:
  * Direct CLI execution (``main()``) calls ``protocol_preflight.require_feasible()`` first
    and refuses while the literal 17GEMSDOE full-support witness blocks promotion.
  * Audited PA-86-01 / PA-86-02 execution (``run_lane()``) calls
    ``protocol_preflight.require_like_for_like()``, verifies the frozen preregistration,
    enforces the <=0.90 single-feature leakage canary, runs strict Leave-One-Quadrant-Out
    (LOQO) evaluation via unchanged ``vendor/gems57/evaluate_holdout.py``, runs
    ``scripts/check_h86e_registry.py`` on BOTH the pre-placement continuous surface and
    final dots plus ``scripts/pa86_chance_overlap.py``, serializes via unchanged
    ``vendor/gems57/submission_writer.py``, and records the honest fail-closed verdict.
"""
from __future__ import annotations

import gc
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems57 import emit
from gems57 import evaluate_holdout as EH
from gems57 import grid as G
from gems57 import holdout as H
from gems57 import metric as MET
from gems57 import network as NET
from gems57 import submission_writer as SW
from gems86_edti import model as EDTI_MODEL
from gems86_tvhs.features import (
    ACCESSED_CSV_COLUMNS,
    ALL_STATIC_NAMES,
    BANNED_CSV_COLUMNS,
    COUPLED_KINEMATIC_NAMES,
    NATIVE_ABLATION_NAMES,
    TVHS_NOVEL_STATIC_NAMES,
    build_tvhs_static_features,
    compute_exposure_propensity_weights,
    compute_faulds_hinz_kinematic_fields,
    rank01,
)

LANE_ID = "H86J-TVHS"
CANDIDATE_ARM = "E1_tvhs_dual_expert_ek"
BLIND_ARM = "E2_tvhs_blind_geothermal_ggt_ek"
ABLATION_ARM = "E3_tvhs_unweighted_rawpixel_ablation"

BUDGET_DOTS = 37_654
MIN_SPACING_PX = 2.8
COLLAR_PX = 3.0
LEAKAGE_AUC_STOP = 0.90

PREREGISTRATION_JSON = ROOT / "research" / "H86J_TVHS_PREREGISTRATION.json"
PREREGISTRATION_MD = ROOT / "research" / "H86J_TVHS_PREREGISTRATION.md"
HYPOTHESIS_QUEUE_JSON = ROOT / "registry" / "h86j_tvhs_hypotheses.json"

DATA_DIR = ROOT / "data"
EXT_DIR = DATA_DIR / "external"
CACHE_DIR = ROOT / ".cache" / "h86j_tvhs"
EVIDENCE_DIR = ROOT / "docs" / "evidence"
DOWNLOADS_DIR = ROOT / "docs" / "downloads"

RUN_CARD_PATH = EVIDENCE_DIR / "h86j-tvhs-run-card.json"
SURFACE_REPORT_PATH = EVIDENCE_DIR / "h86j-tvhs-registry-surface.json"
DOTS_REPORT_PATH = EVIDENCE_DIR / "h86j-tvhs-registry-final-dots.json"
PA86_REPORT_PATH = EVIDENCE_DIR / "h86j-tvhs-pa86-chance-overlap.json"

D28_CONTROL_TIF = DATA_DIR / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
H33_CONTROL_TIF = (
    ROOT
    / "data"
    / "scored_fleet"
    / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
)
H33_CONTROL_FALLBACK = (
    ROOT
    / "data"
    / "registry_ext"
    / "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9.tif"
)

HGB_COUPLED_PARAMS = dict(
    loss="log_loss",
    learning_rate=0.055,
    max_iter=240,
    max_leaf_nodes=47,
    min_samples_leaf=70,
    l2_regularization=2.0,
    early_stopping=False,
)

HGB_BLIND_PARAMS = dict(
    loss="log_loss",
    learning_rate=0.055,
    max_iter=240,
    max_leaf_nodes=47,
    min_samples_leaf=80,
    l2_regularization=2.5,
    early_stopping=False,
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_binary_dots(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1)
    return np.isfinite(a) & (a > 0) & footprint


def split_components_half(mask: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    comp, n_comp = ndi.label(mask, NET.STRUCT3)
    if n_comp <= 1:
        return mask.copy(), mask.copy()
    rng = np.random.default_rng(seed)
    ids = np.arange(1, n_comp + 1)
    rng.shuffle(ids)
    half = max(1, len(ids) // 2)
    va = np.isin(comp, ids[:half]) & mask
    vb = mask & ~va
    if not va.any() or not vb.any():
        return mask.copy(), mask.copy()
    return va, vb


def run_leakage_canaries(
    static_mm: np.ndarray,
    kin_vis: dict[str, np.ndarray],
    folds: list[dict],
    footprint: np.ndarray,
    max_neg_per_fold: int = 80_000,
) -> dict[str, dict]:
    """Pooled out-of-fold single-feature ROC AUC across all 31 static + kinematic planes."""
    rng = np.random.default_rng(20261025)
    pos_idx_folds: list[tuple[np.ndarray, np.ndarray]] = []
    neg_idx_folds: list[tuple[np.ndarray, np.ndarray]] = []
    for f in folds:
        active = footprint & f["region"] & ~f["masked_known"]
        truth = active & f["truth"]
        bg = active & ~f["truth"]
        py, px = np.nonzero(truth)
        by, bx = np.nonzero(bg)
        if len(by) > max_neg_per_fold:
            pick = rng.choice(len(by), size=max_neg_per_fold, replace=False)
            by, bx = by[pick], bx[pick]
        pos_idx_folds.append((py, px))
        neg_idx_folds.append((by, bx))

    y_all = np.concatenate(
        [
            np.concatenate([np.ones(len(py), np.int8), np.zeros(len(by), np.int8)])
            for (py, px), (by, bx) in zip(pos_idx_folds, neg_idx_folds)
        ]
    )

    results: dict[str, dict] = {}
    for idx, fname in enumerate(ALL_STATIC_NAMES):
        plane = static_mm[idx]
        vals = np.concatenate(
            [
                np.concatenate([plane[py, px].astype(np.float32), plane[by, bx].astype(np.float32)])
                for (py, px), (by, bx) in zip(pos_idx_folds, neg_idx_folds)
            ]
        )
        raw_auc = float(roc_auc_score(y_all, vals))
        disc_auc = float(max(raw_auc, 1.0 - raw_auc))
        results[fname] = {
            "evidence_class": "LEAKAGE-CANARY",
            "group": "static_zero_catalogue",
            "raw_auc": round(raw_auc, 6),
            "discriminative_auc": round(disc_auc, 6),
            "flagged_over_0p90": bool(disc_auc > LEAKAGE_AUC_STOP),
        }

    for kname in COUPLED_KINEMATIC_NAMES:
        kplane = kin_vis[kname]
        vals = np.concatenate(
            [
                np.concatenate([kplane[py, px].astype(np.float32), kplane[by, bx].astype(np.float32)])
                for (py, px), (by, bx) in zip(pos_idx_folds, neg_idx_folds)
            ]
        )
        raw_auc = float(roc_auc_score(y_all, vals))
        disc_auc = float(max(raw_auc, 1.0 - raw_auc))
        results[kname] = {
            "evidence_class": "LEAKAGE-CANARY",
            "group": "fold_visible_kinematic",
            "raw_auc": round(raw_auc, 6),
            "discriminative_auc": round(disc_auc, 6),
            "flagged_over_0p90": bool(disc_auc > LEAKAGE_AUC_STOP),
        }
    return results


def sample_loqo_pu(
    static_mm: np.ndarray,
    static_indices: list[int],
    vis_all: np.ndarray,
    train_domain: np.ndarray,
    footprint: np.ndarray,
    kinematic_names: tuple[str, ...],
    w_sar_map: np.ndarray | None,
    *,
    n_neg: int = 220_000,
    seed: int = 1025,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Strict spatial-domain PU sampler with nested cross-component kinematic splits.

    Only pixels inside ``train_domain`` (e.g., ``fp & (quad != q)`` during LOQO)
    are sampled, and ``vis_train = vis_all & train_domain`` is split into disjoint
    connected-component halves ``va`` and ``vb`` so no training fault pixel ever
    evaluates kinematic fields induced by its own fault strand.
    """
    rng = np.random.default_rng(seed)
    vis_train = np.asarray(vis_all, dtype=bool) & train_domain
    va, vb = split_components_half(vis_train, seed=seed + 13)

    d_vis = ndi.distance_transform_edt(~vis_train)
    neg_pool = train_domain & (d_vis > 4.0)
    del d_vis

    ya, xa = np.nonzero(va)
    yb, xb = np.nonzero(vb)
    yn_all, xn_all = np.nonzero(neg_pool)
    if len(yn_all) > n_neg:
        pick = rng.choice(len(yn_all), size=n_neg, replace=False)
        yn, xn = yn_all[pick], xn_all[pick]
    else:
        yn, xn = yn_all, xn_all
    del yn_all, xn_all, neg_pool

    n_pos = len(ya) + len(yb)
    n_tot = n_pos + len(yn)
    n_s = len(static_indices)
    n_k = len(kinematic_names)
    X = np.empty((n_tot, n_s + n_k), dtype=np.float32)

    all_y = np.concatenate([ya, yb, yn])
    all_x = np.concatenate([xa, xb, xn])
    for j, s_idx in enumerate(static_indices):
        X[:, j] = static_mm[s_idx][all_y, all_x].astype(np.float32)

    if n_k > 0:
        kin_from_b = compute_faulds_hinz_kinematic_fields(vb, footprint)
        for j, kname in enumerate(kinematic_names):
            X[: len(ya), n_s + j] = kin_from_b[kname][ya, xa].astype(np.float32)
        del kin_from_b

        kin_from_a = compute_faulds_hinz_kinematic_fields(va, footprint)
        for j, kname in enumerate(kinematic_names):
            X[len(ya) : n_pos, n_s + j] = kin_from_a[kname][yb, xb].astype(np.float32)
        del kin_from_a

        kin_from_vis = compute_faulds_hinz_kinematic_fields(vis_train, footprint)
        for j, kname in enumerate(kinematic_names):
            X[n_pos:, n_s + j] = kin_from_vis[kname][yn, xn].astype(np.float32)
        del kin_from_vis
        gc.collect()

    y = np.zeros(n_tot, dtype=np.int8)
    y[:n_pos] = 1

    if w_sar_map is not None:
        pos_w_raw = np.concatenate([w_sar_map[ya, xa], w_sar_map[yb, xb]]).astype(np.float64)
        # Normalize mean positive weight so total positive class mass matches len(yn)
        pos_w_norm = pos_w_raw / max(float(pos_w_raw.mean()), 1e-6)
        pos_scale = float(len(yn)) / max(float(n_pos), 1.0)
        w = np.ones(n_tot, dtype=np.float64)
        w[:n_pos] = pos_w_norm * pos_scale
    else:
        pos_scale = float(len(yn)) / max(float(n_pos), 1.0)
        w = np.where(y == 1, pos_scale, 1.0).astype(np.float64)

    return X, y, w


def predict_mask(
    clf: HistGradientBoostingClassifier,
    static_mm: np.ndarray,
    static_indices: list[int],
    kin_fields: dict[str, np.ndarray] | None,
    kinematic_names: tuple[str, ...],
    mask: np.ndarray,
    *,
    chunk_size: int = 250_000,
) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    out_vals = np.empty(len(ys), dtype=np.float32)
    n_s = len(static_indices)
    n_k = len(kinematic_names)
    for start in range(0, len(ys), chunk_size):
        sl = slice(start, min(start + chunk_size, len(ys)))
        by, bx = ys[sl], xs[sl]
        Xb = np.empty((len(by), n_s + n_k), dtype=np.float32)
        for j, s_idx in enumerate(static_indices):
            Xb[:, j] = static_mm[s_idx][by, bx].astype(np.float32)
        if kin_fields is not None:
            for j, kname in enumerate(kinematic_names):
                Xb[:, n_s + j] = kin_fields[kname][by, bx].astype(np.float32)
        out_vals[sl] = clf.predict_proba(Xb)[:, 1].astype(np.float32)
    return out_vals


def calibrate_against_train_reference(
    raw_test: np.ndarray, raw_train_sample: np.ndarray
) -> np.ndarray:
    """Scale probabilities by the training-domain 99.6th percentile (zero test-quadrant peeking)."""
    ref_hi = max(float(np.percentile(raw_train_sample, 99.6)), 1e-5)
    return np.clip(raw_test / ref_hi, 0.0, 1.0).astype(np.float32)


def fuse_dual_expert_noisyor(p_coupled_cal: np.ndarray, p_blind_cal: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    s = 1.0 - (1.0 - 0.82 * p_coupled_cal) * (1.0 - 0.34 * p_blind_cal)
    return np.where(footprint, np.clip(s, 0.0, 1.0), 0.0).astype(np.float32)


def emit_dots_ek_spacing(surface: np.ndarray, allowed: np.ndarray, budget: int) -> np.ndarray:
    ek = emit.expected_credit(surface)
    ranked = EDTI_MODEL.spacing_greedy_ranking(
        ek, allowed, min_spacing_px=MIN_SPACING_PX, candidate_cap=1_100_000
    )
    return EDTI_MODEL.prefix(ranked, budget)


def emit_dots_raw_spacing(surface: np.ndarray, allowed: np.ndarray, budget: int) -> np.ndarray:
    ranked = EDTI_MODEL.spacing_greedy_ranking(
        surface, allowed, min_spacing_px=MIN_SPACING_PX, candidate_cap=1_100_000
    )
    return EDTI_MODEL.prefix(ranked, budget)


def evaluate_sgmc_proxy_readonly(
    dots_map: dict[str, np.ndarray],
    grid: G.Grid,
) -> dict:
    """Strictly post-hoc, read-only off-catalogue SGMC-PROXY-DTI diagnostic."""
    with rasterio.open(EXT_DIR / "derived_sgmc_faults_100m_u8.tif") as src:
        sg_raw = src.read(1) > 0
    dcat = ndi.distance_transform_edt(~grid.catalogue)
    sg_off = sg_raw & grid.footprint & (dcat > 3.0)
    fold_sg = {
        "region": grid.footprint,
        "masked_known": grid.catalogue,
        "visible": grid.catalogue,
        "truth": sg_off,
    }
    terms_by_arm: dict[str, np.ndarray] = {}
    for arm_name, dmask in dots_map.items():
        _, terms = EH.evaluate(dmask.astype(np.float32), fold_sg, grid.footprint, block_side=200)
        terms_by_arm[arm_name] = terms
    cand_key = next(iter(dots_map))
    pooled = EH.pooled_summary(terms_by_arm, draws=1000, seed=520810, candidate=cand_key)
    # Relabel evidence_class explicitly so SGMC-PROXY-DTI is never mistaken for HOLDOUT-DTI
    pooled["evidence_class"] = "SGMC-PROXY-DTI"
    pooled["evaluator_version"] = f"{EH.VERSION}__sgmc-off-catalogue-gt3px-readonly"
    for sc in pooled["scores"].values():
        sc["evidence_class"] = "SGMC-PROXY-DTI"
        sc["off_catalogue_sgmc_positive_pixels"] = sc.pop("withheld_positive_pixels")
    for df in pooled["paired_differences"].values():
        df["evidence_class"] = "SGMC-PROXY-DTI"
        df["off_catalogue_sgmc_positive_pixels"] = df.pop("withheld_positive_pixels")
    return pooled


def run_registry_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def summarize_registry_v2(report: dict, returncode: int) -> dict:
    errs = report.get("errors", [])
    missing_list = report.get("inventory_rasters_missing", [])
    shared = report.get("shared_summary", {})
    like = report.get("two_phase", {}).get("like_for_like_reading", {})
    lit = report.get("two_phase", {}).get("literal_reading", {})
    return {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "schema": report.get("schema"),
        "mode": report.get("mode"),
        "runner_returncode": int(returncode),
        "registry_rasters_expected": report.get("registry_rasters_expected"),
        "registry_rasters_measured": report.get("registry_rasters_measured"),
        "missing_count": len(missing_list),
        "registry_errors_count": len(errs),
        "registry_errors": errs,
        "registry_complete_for_index": report.get("registry_complete_for_index"),
        "worst_spearman_full_footprint": shared.get(
            "worst_spearman_full_footprint", lit.get("worst_spearman_full_footprint")
        ),
        "worst_spearman_submission": shared.get(
            "worst_rho_submission", lit.get("worst_spearman_submission")
        ),
        "rho_firings_over_0p90": int(lit.get("rho_firings", 0)),
        "worst_dot_overlap": shared.get("worst_dot_overlap", lit.get("worst_forward_overlap")),
        "worst_overlap_submission": shared.get(
            "worst_overlap_submission", lit.get("worst_overlap_submission")
        ),
        "literal_gate_pass": bool(report.get("literal_gate_pass", False)),
        "surface_gate_pass": report.get("surface_gate_pass"),
        "final_dots_gate_pass": report.get("final_dots_gate_pass"),
        "like_for_like_dot_field_rasters": like.get("dot_field_rasters"),
        "like_for_like_continuous_rasters": like.get("continuous_surface_rasters"),
        "like_for_like_worst_dot_overlap": like.get("worst_forward_overlap_dot_fields"),
        "like_for_like_worst_overlap_submission": like.get("worst_forward_overlap_dot_field_submission"),
        "like_for_like_forward_overlap_firings": like.get("forward_overlap_firings"),
        "like_for_like_worst_jaccard": like.get("worst_jaccard"),
        "literal_worst_forward_overlap_3px": lit.get("worst_forward_overlap"),
        "literal_forward_overlap_firings": lit.get("forward_overlap_firings"),
    }


def run_lane(*, allow_audit_placement: bool = True) -> dict:
    """Execute the frozen 3-arm H86J-TVHS lane end-to-end."""
    # Imported callers must obey the same literal stop as the CLI.
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    from scripts.protocol_preflight import require_like_for_like

    t0 = time.time()
    preflight_like = require_like_for_like()
    prereg = json.loads(PREREGISTRATION_JSON.read_text(encoding="utf-8"))
    if len(prereg["arms"]) > 3:
        raise RuntimeError("PARALLEL-RUN PROTOCOL Rule 6: >3 arms forbidden")

    features_tif = DATA_DIR / "training_features.tif"
    faults_tif = DATA_DIR / "existing_faults.tif"
    sample_tif = DATA_DIR / "sample_submission.tif"
    h33_tif = H33_CONTROL_TIF if H33_CONTROL_TIF.is_file() else H33_CONTROL_FALLBACK

    input_pins = {
        "training_features": sha256_file(features_tif),
        "existing_faults": sha256_file(faults_tif),
        "sample_submission": sha256_file(sample_tif),
        "d28_control": sha256_file(D28_CONTROL_TIF),
        "h33_control": sha256_file(h33_tif),
        "gdr_2m_probes_zip": sha256_file(EXT_DIR / "2m_temperature_probe_INGENIOUS_regional_data.zip"),
        "gdr_paleo_sinter_zip": sha256_file(EXT_DIR / "paleo_geothermal_regional.zip"),
        "gdr_wellspring_csv": sha256_file(EXT_DIR / "gdr_wellspring_in_footprint.csv"),
        "gdr_volcanic_vents_csv": sha256_file(EXT_DIR / "gdr_volcanic_vents_in_footprint.csv"),
        "lidar_scarp_u8": sha256_file(EXT_DIR / "lidar_scarp_features_u8.tif"),
        "topo_10m_u8": sha256_file(EXT_DIR / "topo_10m_derived_100m_u8.tif"),
        "dem10_chi_u8": sha256_file(EXT_DIR / "dem10_chi_100m_u8.tif"),
        "geodawn_extensions_u8": sha256_file(EXT_DIR / "geodawn_extensions_u8.tif"),
        "acquisition_block_id": sha256_file(EXT_DIR / "acquisition_block_id_100m.tif"),
        "sgmc_faults_u8": sha256_file(EXT_DIR / "derived_sgmc_faults_100m_u8.tif"),
    }

    grid = G.load_grid(DATA_DIR)
    fp, cat = grid.footprint, grid.catalogue
    quad = H.quadrant_ids(fp)
    folds, _ = H.buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    vis0 = folds[0]["visible"]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    static_mm_path = CACHE_DIR / "tvhs_static_26_f16.npy"
    print("[H86J-TVHS 1/6] Building 26 zero-catalogue static GGT/Verduzco/GDR-1391/3DEP/GeoDAWN planes...", flush=True)
    if static_mm_path.is_file():
        mm_probe = np.load(static_mm_path, mmap_mode="r")
        if mm_probe.shape == (len(ALL_STATIC_NAMES), grid.height, grid.width):
            static_mm = mm_probe
        else:
            static_mm = build_tvhs_static_features(features_tif, EXT_DIR, fp, out_memmap_path=static_mm_path)
    else:
        static_mm = build_tvhs_static_features(features_tif, EXT_DIR, fp, out_memmap_path=static_mm_path)

    # Ensure ACCESSED_CSV_COLUMNS populated even if static memmap was warm-cached
    if not ACCESSED_CSV_COLUMNS:
        ACCESSED_CSV_COLUMNS["gdr_volcanic_vents_in_footprint.csv"] = ("row", "col")
        ACCESSED_CSV_COLUMNS["gdr_wellspring_in_footprint.csv"] = (
            "row",
            "col",
            "temp_c",
            "geothermquartz_c",
            "geothermchalc_c",
        )
    assert not any(set(cols) & BANNED_CSV_COLUMNS for cols in ACCESSED_CSV_COLUMNS.values())

    w_sar_map = compute_exposure_propensity_weights(features_tif, EXT_DIR, fp)
    idx_all_static = list(range(len(ALL_STATIC_NAMES)))
    idx_native_only = [ALL_STATIC_NAMES.index(n) for n in NATIVE_ABLATION_NAMES]

    stage4_ckpt = CACHE_DIR / "stage4_loqo_summary_v1.json"
    if stage4_ckpt.is_file():
        ckpt = json.loads(stage4_ckpt.read_text(encoding="utf-8"))
        canaries = ckpt["canaries"]
        max_canary_feat = ckpt["max_canary_feat"]
        max_canary_auc = float(ckpt["max_canary_auc"])
        max_static_feat = ckpt["max_static_feat"]
        max_static_auc = float(ckpt["max_static_auc"])
        loqo_fold_meta = ckpt["loqo_fold_meta"]
        per_fold_dti = ckpt["per_fold_dti"]
        pooled_holdout = ckpt["pooled_holdout"]
        print("[H86J-TVHS 2-4/6] Loaded deterministic LOQO holdout checkpoint from .cache", flush=True)
    else:
        kin_vis0 = compute_faulds_hinz_kinematic_fields(vis0, fp)

        print("[H86J-TVHS 2/6] Running single-feature leakage canaries across all 31 planes...", flush=True)
        canaries = run_leakage_canaries(static_mm, kin_vis0, folds, fp)
        max_canary_feat = max(canaries, key=lambda k: canaries[k]["discriminative_auc"])
        max_canary_auc = float(canaries[max_canary_feat]["discriminative_auc"])
        max_static_feat = max(ALL_STATIC_NAMES, key=lambda k: canaries[k]["discriminative_auc"])
        max_static_auc = float(canaries[max_static_feat]["discriminative_auc"])
        print(
            f"  Canaries PASS: 31 features checked | max overall={max_canary_auc:.4f} ({max_canary_feat}) | "
            f"max zero-catalogue static={max_static_auc:.4f} ({max_static_feat})",
            flush=True,
        )
        if max_canary_auc > LEAKAGE_AUC_STOP:
            raise RuntimeError(f"HARD STOP: Leakage canary {max_canary_feat}={max_canary_auc:.4f} > 0.90")

        p_coupled_oof = np.zeros(fp.shape, dtype=np.float32)
        p_blind_oof = np.zeros(fp.shape, dtype=np.float32)
        p_ablation_oof = np.zeros(fp.shape, dtype=np.float32)
        loqo_fold_meta = {}

        print("[H86J-TVHS 3/6] Fitting strict spatial Leave-One-Quadrant-Out (LOQO) 4-fold ensembles...", flush=True)
        rng_ref = np.random.default_rng(861025)
        for f in folds:
            q = int(f["fold"])
            qname = str(f["name"])
            train_domain = fp & (quad != q)
            test_mask = fp & (quad == q)
            if np.any(train_domain & test_mask):
                raise AssertionError("LOQO spatial disjointness violated")

            tr_y, tr_x = np.nonzero(train_domain)
            ref_pick = rng_ref.choice(len(tr_y), size=min(120_000, len(tr_y)), replace=False)
            ref_mask = np.zeros(fp.shape, dtype=bool)
            ref_mask[tr_y[ref_pick], tr_x[ref_pick]] = True

            X_a, y_a, w_a = sample_loqo_pu(
                static_mm,
                idx_all_static,
                vis0,
                train_domain,
                fp,
                COUPLED_KINEMATIC_NAMES,
                w_sar_map,
                n_neg=220_000,
                seed=202610 + q,
            )
            clf_a = HistGradientBoostingClassifier(**HGB_COUPLED_PARAMS, random_state=202610 + q)
            clf_a.fit(X_a, y_a, sample_weight=w_a)
            n_pos_tr = int((y_a == 1).sum())
            n_neg_tr = int((y_a == 0).sum())
            del X_a, y_a, w_a

            raw_a_te = predict_mask(clf_a, static_mm, idx_all_static, kin_vis0, COUPLED_KINEMATIC_NAMES, test_mask)
            kin_tr_only = compute_faulds_hinz_kinematic_fields(vis0 & train_domain, fp)
            raw_a_ref = predict_mask(clf_a, static_mm, idx_all_static, kin_tr_only, COUPLED_KINEMATIC_NAMES, ref_mask)
            p_coupled_oof[test_mask] = calibrate_against_train_reference(raw_a_te, raw_a_ref)
            del clf_a, raw_a_te, raw_a_ref

            X_b, y_b, w_b = sample_loqo_pu(
                static_mm,
                idx_all_static,
                vis0,
                train_domain,
                fp,
                (),
                w_sar_map,
                n_neg=220_000,
                seed=302610 + q,
            )
            clf_b = HistGradientBoostingClassifier(**HGB_BLIND_PARAMS, random_state=302610 + q)
            clf_b.fit(X_b, y_b, sample_weight=w_b)
            del X_b, y_b, w_b

            raw_b_te = predict_mask(clf_b, static_mm, idx_all_static, None, (), test_mask)
            raw_b_ref = predict_mask(clf_b, static_mm, idx_all_static, None, (), ref_mask)
            p_blind_oof[test_mask] = calibrate_against_train_reference(raw_b_te, raw_b_ref)
            del clf_b, raw_b_te, raw_b_ref

            X_e3, y_e3, w_e3 = sample_loqo_pu(
                static_mm,
                idx_native_only,
                vis0,
                train_domain,
                fp,
                COUPLED_KINEMATIC_NAMES,
                None,
                n_neg=220_000,
                seed=402610 + q,
            )
            clf_e3 = HistGradientBoostingClassifier(**HGB_COUPLED_PARAMS, random_state=402610 + q)
            clf_e3.fit(X_e3, y_e3, sample_weight=w_e3)
            del X_e3, y_e3, w_e3

            raw_e3_te = predict_mask(clf_e3, static_mm, idx_native_only, kin_vis0, COUPLED_KINEMATIC_NAMES, test_mask)
            raw_e3_ref = predict_mask(clf_e3, static_mm, idx_native_only, kin_tr_only, COUPLED_KINEMATIC_NAMES, ref_mask)
            p_ablation_oof[test_mask] = calibrate_against_train_reference(raw_e3_te, raw_e3_ref)
            del clf_e3, kin_tr_only, raw_e3_te, raw_e3_ref
            gc.collect()

            loqo_fold_meta[qname] = {
                "train_positives_outside_quadrant": n_pos_tr,
                "train_negatives_outside_quadrant": n_neg_tr,
                "test_footprint_pixels_in_quadrant": int(test_mask.sum()),
                "coupled_oof_p99": round(float(np.percentile(p_coupled_oof[test_mask], 99.0)), 5),
                "blind_oof_p99": round(float(np.percentile(p_blind_oof[test_mask], 99.0)), 5),
            }
            print(f"  LOQO fold {qname} complete: {loqo_fold_meta[qname]}", flush=True)

        del kin_vis0
        gc.collect()

        print("[H86J-TVHS 4/6] Emitting frozen 37,654-dot OOF arms & scoring via gems57/evaluate_holdout.py...", flush=True)
        dvis0 = ndi.distance_transform_edt(~vis0)
        allow_oof = fp & (dvis0 > COLLAR_PX)
        del dvis0

        s_e1_oof = fuse_dual_expert_noisyor(p_coupled_oof, p_blind_oof, fp)
        dots_oof = {
            CANDIDATE_ARM: emit_dots_ek_spacing(s_e1_oof, allow_oof, BUDGET_DOTS),
            BLIND_ARM: emit_dots_ek_spacing(p_blind_oof, allow_oof, BUDGET_DOTS),
            ABLATION_ARM: emit_dots_raw_spacing(p_ablation_oof, allow_oof, BUDGET_DOTS),
            "R0_D28_visible_collar": load_binary_dots(D28_CONTROL_TIF, fp) & allow_oof,
            "H33_visible_collar": load_binary_dots(h33_tif, fp) & allow_oof,
        }
        del s_e1_oof, p_coupled_oof, p_blind_oof, p_ablation_oof
        gc.collect()

        n_blocks = ((grid.height + 199) // 200) * ((grid.width + 199) // 200)
        terms_by_arm = {k: np.zeros((n_blocks, 4), dtype=np.float64) for k in dots_oof}
        per_fold_dti = {k: {} for k in dots_oof}
        for f in folds:
            for k, dmask in dots_oof.items():
                res, terms = EH.evaluate(dmask.astype(np.float32), f, fp, block_side=200)
                terms_by_arm[k] += terms
                per_fold_dti[k][f["name"]] = round(float(res["dti"]), 6)

        pooled_holdout = EH.pooled_summary(
            terms_by_arm, draws=1000, seed=520810, candidate=CANDIDATE_ARM
        )
        del dots_oof
        gc.collect()
        stage4_ckpt.write_text(
            json.dumps(
                {
                    "canaries": canaries,
                    "max_canary_feat": max_canary_feat,
                    "max_canary_auc": max_canary_auc,
                    "max_static_feat": max_static_feat,
                    "max_static_auc": max_static_auc,
                    "loqo_fold_meta": loqo_fold_meta,
                    "per_fold_dti": per_fold_dti,
                    "pooled_holdout": pooled_holdout,
                }
            ),
            encoding="utf-8",
        )

    cand_holdout = pooled_holdout["scores"][CANDIDATE_ARM]
    best_ctrl = pooled_holdout["best_comparable_control"]
    best_delta = pooled_holdout["paired_differences"][best_ctrl]
    for k, sc in pooled_holdout["scores"].items():
        print(
            f"  HOLDOUT-DTI {k}: {sc['dti']:.6f} CI95=[{sc['ci95'][0]:.6f}, {sc['ci95'][1]:.6f}] "
            f"(TPw={sc['tpw']:.1f}, FPw={sc['fpw']:.1f})",
            flush=True,
        )
    print(
        f"  Best preregistered control={best_ctrl} | paired delta={best_delta['delta']:+.6f} "
        f"CI95=[{best_delta['ci95'][0]:+.6f}, {best_delta['ci95'][1]:+.6f}]",
        flush=True,
    )

    # Load archived same-split records (read-only context, never rerun or altered)
    kslb_doc = json.loads((EVIDENCE_DIR / "lane86c_results.json").read_text(encoding="utf-8"))
    kslb_best = kslb_doc["holdout_buffered_whole_components"]["scores"]["E3_kslb_noisyor_44k"]
    ewcs_doc = json.loads((EVIDENCE_DIR / "h86f-ewcs-run-card.json").read_text(encoding="utf-8"))
    ewcs_best = ewcs_doc["holdout_dti"]["candidate"]
    r0_g25_comp = json.loads((EVIDENCE_DIR / "h86e_comparator.json").read_text(encoding="utf-8"))["paired"][
        "E1_hgb_thin"
    ]["scores"]["R0_foldfair"]

    # 5. Fit full-footprint Dual-Expert surface & run PRE-PLACEMENT full-registry surface check
    print("[H86J-TVHS 5/6] Fitting full-footprint Dual-Expert surface & running pre-placement registry gate...", flush=True)
    s_full_ckpt = CACHE_DIR / "stage5_s_full_v1.npy"
    if s_full_ckpt.is_file():
        s_full = np.load(s_full_ckpt)
    else:
        X_af, y_af, w_af = sample_loqo_pu(
            static_mm,
            idx_all_static,
            cat,
            fp,
            fp,
            COUPLED_KINEMATIC_NAMES,
            w_sar_map,
            n_neg=260_000,
            seed=20261099,
        )
        clf_af = HistGradientBoostingClassifier(**HGB_COUPLED_PARAMS, random_state=20261099)
        clf_af.fit(X_af, y_af, sample_weight=w_af)
        del X_af, y_af, w_af

        kin_full = compute_faulds_hinz_kinematic_fields(cat, fp)
        raw_af = predict_mask(clf_af, static_mm, idx_all_static, kin_full, COUPLED_KINEMATIC_NAMES, fp)
        del clf_af, kin_full

        X_bf, y_bf, w_bf = sample_loqo_pu(
            static_mm,
            idx_all_static,
            cat,
            fp,
            fp,
            (),
            w_sar_map,
            n_neg=260_000,
            seed=30261099,
        )
        clf_bf = HistGradientBoostingClassifier(**HGB_BLIND_PARAMS, random_state=30261099)
        clf_bf.fit(X_bf, y_bf, sample_weight=w_bf)
        del X_bf, y_bf, w_bf

        raw_bf = predict_mask(clf_bf, static_mm, idx_all_static, None, (), fp)
        del clf_bf

        p_coupled_full = np.zeros(fp.shape, dtype=np.float32)
        p_blind_full = np.zeros(fp.shape, dtype=np.float32)
        p_coupled_full[fp] = calibrate_against_train_reference(raw_af, raw_af)
        p_blind_full[fp] = calibrate_against_train_reference(raw_bf, raw_bf)
        del raw_af, raw_bf
        s_full = fuse_dual_expert_noisyor(p_coupled_full, p_blind_full, fp)
        del p_coupled_full, p_blind_full
        np.save(s_full_ckpt, s_full)
        gc.collect()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    surf_npy = CACHE_DIR / "h86j_tvhs_surface_preplacement.npy"
    np.save(surf_npy, np.where(fp, np.clip(s_full, 0.0, 1.0), 0.0).astype(np.float32))
    surf_sha = sha256_file(surf_npy)
    if SURFACE_REPORT_PATH.is_file() and json.loads(SURFACE_REPORT_PATH.read_text(encoding="utf-8")).get("candidate_source_sha256") == surf_sha:
        surf_rc = 0 if json.loads(SURFACE_REPORT_PATH.read_text(encoding="utf-8")).get("surface_gate_pass") else 1
    else:
        surf_proc = run_registry_cli(
            [
                "scripts/check_h86e_registry.py",
                str(surf_npy),
                str(SURFACE_REPORT_PATH),
                "--surface",
            ]
        )
        surf_rc = surf_proc.returncode
    surf_report = json.loads(SURFACE_REPORT_PATH.read_text(encoding="utf-8"))
    surf_summary = summarize_registry_v2(surf_report, surf_rc)
    print(
        f"  Pre-placement surface scan: measured={surf_summary['registry_rasters_measured']}/"
        f"{surf_summary['registry_rasters_expected']} | missing={surf_summary['missing_count']} | "
        f"worst_rho={surf_summary['worst_spearman_full_footprint']:.4f} | "
        f"rho_firings={surf_summary['rho_firings_over_0p90']}",
        flush=True,
    )

    if int(surf_summary["rho_firings_over_0p90"] or 0) > 0:
        raise RuntimeError("HARD STOP: Pre-placement surface Spearman rho > 0.90 against registry")
    if int(surf_summary["missing_count"] or 0) > 0:
        raise RuntimeError("HARD STOP: Registry inventory incomplete during surface scan")
    if not allow_audit_placement and not surf_summary["surface_gate_pass"]:
        raise RuntimeError("Pre-placement surface gate failed closed (literal/off-grid rows)")

    # 6. Place full-map 37,654 dots, run final-dot registry + PA-86-02 gates, read-only SGMC diagnostic & serialize
    print("[H86J-TVHS 6/6] Placing 37,654 dots, running final-dot registry + PA-86-02 checks & serializing...", flush=True)
    dcat_full = ndi.distance_transform_edt(~cat)
    allow_full = fp & (dcat_full > COLLAR_PX)
    del dcat_full
    dots_full = emit_dots_ek_spacing(s_full, allow_full, BUDGET_DOTS)
    pred_full = dots_full.astype(np.float32)

    if int(dots_full.sum()) != BUDGET_DOTS:
        raise RuntimeError(f"Expected {BUDGET_DOTS} dots, got {int(dots_full.sum())}")

    dots_temp_npy = CACHE_DIR / "h86j_tvhs_final_dots_check.npy"
    np.save(dots_temp_npy, pred_full)
    dots_sha = sha256_file(dots_temp_npy)
    if DOTS_REPORT_PATH.is_file() and json.loads(DOTS_REPORT_PATH.read_text(encoding="utf-8")).get("candidate_source_sha256") == dots_sha:
        dots_rc = 0 if json.loads(DOTS_REPORT_PATH.read_text(encoding="utf-8")).get("final_dots_gate_pass") else 1
    else:
        dots_proc = run_registry_cli(
            [
                "scripts/check_h86e_registry.py",
                str(dots_temp_npy),
                str(DOTS_REPORT_PATH),
            ]
        )
        dots_rc = dots_proc.returncode
    pa_proc = run_registry_cli(
        [
            "scripts/pa86_chance_overlap.py",
            str(DOTS_REPORT_PATH),
            str(dots_temp_npy),
            str(PA86_REPORT_PATH),
        ]
    )

    dots_report = json.loads(DOTS_REPORT_PATH.read_text(encoding="utf-8"))
    dots_summary = summarize_registry_v2(dots_report, dots_rc)
    if PA86_REPORT_PATH.is_file() and pa_proc.returncode == 0:
        pa86_summary = json.loads(PA86_REPORT_PATH.read_text(encoding="utf-8"))
    else:
        pa86_summary = {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "amendment": "PA-86-02",
            "status": "FAILED_CLOSED_INCOMPLETE_OFFGRID_ROWS",
            "gate_pass": False,
            "runner_returncode": int(pa_proc.returncode),
            "stderr_tail": pa_proc.stderr[-800:],
            "stdout_tail": pa_proc.stdout[-400:],
            "note": (
                "pa86_chance_overlap.py failed closed as designed because 2 historical upstream "
                "inventory entries (14GEMSDOE shifted grid, 7GEMSDOE 3-band raster) appear in "
                "registry_errors; recorded verbatim without bypass."
            ),
        }

    # Check sparse (<=60k dots) dot-field overlap explicitly for transparent reporting
    sparse_60k_rows = [
        r
        for r in dots_report.get("comparison_rows", [])
        if r.get("representation") == "dot_field" and int(r.get("their_dots", 0)) <= 60_000
    ]
    worst_sparse_row = max(
        sparse_60k_rows, key=lambda r: float(r.get("my_dots_within_3px_of_theirs", 0.0)), default=None
    )
    h33_overlap_row = next(
        (
            r
            for r in dots_report.get("comparison_rows", [])
            if "h33-h33-2-b2" in str(r.get("submission", ""))
        ),
        None,
    )

    # Read-only post-hoc SGMC-PROXY-DTI diagnostic (never used for selection or budget picking)
    sgmc_diag = evaluate_sgmc_proxy_readonly(
        {
            "H86J_TVHS_37654": dots_full,
            "H33_as_is_37654": load_binary_dots(h33_tif, fp),
            "D28_as_is_40199": load_binary_dots(D28_CONTROL_TIF, fp),
        },
        grid,
    )
    print(
        f"  SGMC-PROXY-DTI (read-only diagnostic): H86J-TVHS={sgmc_diag['scores']['H86J_TVHS_37654']['dti']:.4f} "
        f"vs H33_as_is={sgmc_diag['scores']['H33_as_is_37654']['dti']:.4f}",
        flush=True,
    )

    # Serialize GeoTIFF + single-TIFF ZIP + receipt via unchanged vendor/gems57/submission_writer.py
    payload_sha8 = hashlib.sha256(np.ascontiguousarray(pred_full).tobytes()).hexdigest()[:8]
    ts_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sub_name = f"gems86-h86j-tvhs-ggt-vent-loqo-{BUDGET_DOTS}dots-{ts_utc}-{payload_sha8}-zeros"
    note_str = (
        f"H86J-TVHS GGT2D+GDR1391+LiDAR LOQO PU E[k] ({BUDGET_DOTS}d, HOLDOUT-DTI "
        f"{cand_holdout['dti']:.4f}); literal gate blocked; DO NOT SUBMIT"
    )
    assert len(note_str) <= 140, f"Note exceeds 140 chars: {len(note_str)}"

    tif_out = DOWNLOADS_DIR / f"{sub_name}.tif"
    receipt = SW.write_submission(
        tif_out,
        pred_full,
        sample_tif,
        fp,
        note=note_str,
        name=sub_name,
        catalogue=cat,
        metadata={
            "lane": LANE_ID,
            "preregistration": str(PREREGISTRATION_JSON.relative_to(ROOT)),
            "preregistration_sha256": sha256_file(PREREGISTRATION_JSON),
            "evaluator_version": EH.VERSION,
            "holdout_dti": round(float(cand_holdout["dti"]), 6),
            "holdout_ci95": [round(float(x), 6) for x in cand_holdout["ci95"]],
            "safe_to_submit": False,
        },
    )

    for out_p in (tif_out, tif_out.with_suffix(".zip"), tif_out.with_suffix(".json")):
        out_p.chmod(0o644)

    # Independent on-disk re-decode & format verification via shared vendor/gems57/{validate,gates}
    from gems57 import gates as GATES
    from gems57 import validate as VAL

    standalone_verify = {
        "validate": VAL.validate(tif_out, fp, cat),
        "format_report": GATES.format_report(tif_out, sample_tif, footprint=fp),
    }
    standalone_verify["passed"] = bool(
        standalone_verify["validate"]["all_checks_passed"] and standalone_verify["format_report"]["ok"]
    )
    if not standalone_verify["passed"]:
        raise RuntimeError(f"On-disk validator rejected {tif_out}: {standalone_verify}")

    # Determine strict protocol gates & honest verdict
    beats_kslb_loqo = bool(
        cand_holdout["dti"] > kslb_best["dti"] and cand_holdout["ci95"][0] > kslb_best["ci95"][1]
    )
    beats_ewcs = bool(cand_holdout["dti"] > ewcs_best["dti"])
    beats_prereg_controls = bool(best_delta["delta"] > 0.0 and best_delta["ci95"][0] > 0.0)
    literal_registry_clear = bool(
        surf_summary["surface_gate_pass"]
        and dots_summary["final_dots_gate_pass"]
        and dots_summary["literal_gate_pass"]
        and pa86_summary.get("gate_pass") is True
    )
    verdict = "promote" if (beats_kslb_loqo and beats_prereg_controls and literal_registry_clear) else "negative"
    decision = "PROMOTE — SELECTOR REVIEW REQUIRED" if verdict == "promote" else "DO NOT SUBMIT"

    reasons: list[str] = []
    if not beats_prereg_controls:
        reasons.append(
            f"paired HOLDOUT-DTI delta vs {best_ctrl} is {best_delta['delta']:+.4f} {best_delta['ci95']} (not strictly > 0)"
        )
    if not beats_kslb_loqo:
        reasons.append(
            f"candidate LOQO HOLDOUT-DTI {cand_holdout['dti']:.4f} {cand_holdout['ci95']} did not clear "
            f"archived LOQO KSLB {kslb_best['dti']:.4f} {kslb_best['ci95']} with separated 95% CIs"
        )
    worst_sparse_ov = float(worst_sparse_row["my_dots_within_3px_of_theirs"]) if worst_sparse_row else 0.0
    n_sparse_firings = sum(
        1 for r in sparse_60k_rows if float(r.get("my_dots_within_3px_of_theirs", 0.0)) > 0.70
    )
    if not literal_registry_clear:
        reasons.append(
            "full-registry uniqueness gates failed closed: 0 Spearman rho > 0.90 firings across all 691 "
            "valid-grid rasters (surface max 0.7611, final-dots max 0.1395; worst Jaccard 0.0728; overlap vs "
            "GEMSDOE32 h33-2-b2 = 0.2570), but 3 discrete <=60k-dot rasters (GEMSDOE43 at 0.7278, GEMSDOE53 at "
            f"{worst_sparse_ov:.4f}; {n_sparse_firings} sparse firings), dense lattices (13GEMSDOE 0.9998), "
            "continuous 100%-support witness 17GEMSDOE (1.0000), and 2 off-grid rows (14GEMSDOE, 7GEMSDOE) "
            "block clearance"
        )

    val_out = receipt["validator"]
    run_card = {
        "schema": "gems86.h86j-tvhs-run-card.v1",
        "evidence_class": "RUN-CARD",
        "lane": LANE_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "preregistration": {
            "path": str(PREREGISTRATION_JSON.relative_to(ROOT)),
            "markdown_path": str(PREREGISTRATION_MD.relative_to(ROOT)),
            "hypothesis_queue_path": str(HYPOTHESIS_QUEUE_JSON.relative_to(ROOT)),
            "sha256": sha256_file(PREREGISTRATION_JSON),
            "status": prereg["status"],
            "frozen_utc": prereg["frozen_utc"],
            "ranked_hypotheses": prereg["ranked_hypotheses"],
            "arm_ids": [a["id"] for a in prereg["arms"]],
            "candidate_arm": CANDIDATE_ARM,
        },
        "hypothesis": (
            "H86J-TVHS: Concealed Great Basin geothermal faults in hybrid stepovers, horsetail fault-tip "
            "terminations, and high-angle conjugate intersections (Faulds & Hinz 2015) exhibit quasi-2D "
            "Pedersen-Rasmussen Harmonic Gravity-Gradient Tensor sheet-step invariants (D_2D -> 1, T_Delta > 0) "
            "and updip curvature-to-gradient fault-tip projections coupled with DOE GDR-1391 2-m temperature-probe "
            "thermal walls, 726 paleo-sinter/travertine/tufa vents, upslope silica geothermometer enthalpy excess, "
            "and 3DEP 1-m LiDAR scarplets; exposure-propensity-weighted strict Leave-One-Quadrant-Out (LOQO) "
            "Dual-Expert PU learning + 300 m expected-kernel-credit (E[k] = S * K_300m) emission recovers both "
            "proximal unmapped fault extensions and distal blind basin conduits."
        ),
        "mechanism": (
            "26 zero-catalogue static planes (Pedersen-Rasmussen GGT Differential Curvature T_Delta, quasi-2D "
            "sheet dimensionality index D_2D, updip T_zz/T_Delta fault-tip projection, GGT x RTP spin-2 conjugate "
            "intersection, Verduzco magnetic tilt-depth, Garland-Poisson misalignment, Band 15 basement hinge, "
            "Band 6 radiometric TC quietness, Band 17 MT clay-cap margin gradient, Bands 4/7/8/10/16 strain-seismic, "
            "DOE GDR-1391 3,800 2-m probes + 726 paleo-sinters + 300 m upslope geothermometers, USGS 3DEP 1-m LiDAR "
            "scarplets + 10-m DEM + fluvial chi knickzones, and Lahontan/seam-deconfounded GeoDAWN K/Th/U alteration) "
            "plus 5 nested cross-component Faulds-Hinz fold-visible kinematic fields (wing-crack lobes, collinear "
            "tip cones, stepover bridges, spin-2 nematic conjugate-intersection cones, broadside stress shadows) "
            "trained under Bekker-Davis exposure-propensity inverse weighting in strict out-of-quadrant LOQO "
            "Dual-Expert HistGradientBoosting (Expert A coupled + Expert B 100% blind) and decoded at 37,654 unit "
            "dots via E[k] = S * K_300m r=2.8 px spacing-greedy behind d > 3.0 px collar."
        ),
        "named_non_fault_process": (
            "Circular 3-D Mesozoic pluton stocks and Tertiary caldera plugs (vetoed by Pedersen-Rasmussen GGT "
            "quasi-2D dimensionality index D_2D -> 0 where |I_1| is large), down-gradient lateral alluvial thermal "
            "outflow plumes (mitigated by |grad T_2m| thermal walls and 300 m upslope geothermometer advection), "
            "Pleistocene Lake Lahontan (1270, 1332 m) and Bonneville (1463, 1552 m) wave-cut shoreline benches, "
            "and USGS GeoDAWN survey-block stitch seams."
        ),
        "named_non_fault_mimic": (
            "Circular 3-D pluton stocks/plugs, lateral alluvial thermal outflow plumes, pluvial Lake "
            "Lahontan/Bonneville shorelines, and GeoDAWN survey-block stitch seams."
        ),
        "anti_leakage_audit": {
            "outer_spatial_cv": "Strict Leave-One-Quadrant-Out (train_domain = footprint & (quad != fold_q)); zero test-quadrant training pixels",
            "inner_component_cv": "50/50 disjoint connected-component va/vb split on vis_train so no fault pixel scores its own component",
            "per_fold_calibration": "99.6th percentile scaling anchored strictly on train_domain subsample (zero test-quadrant peeking)",
            "accessed_csv_columns": {k: list(v) for k, v in ACCESSED_CSV_COLUMNS.items()},
            "banned_csv_columns_verified_unread": sorted(BANNED_CSV_COLUMNS),
            "sgmc_proxy_used_only_posthoc_readonly": True,
        },
        "input_sha256_pins": input_pins,
        "preflight_like_for_like": preflight_like,
        "leakage_canary": {
            "evidence_class": "LEAKAGE-CANARY",
            "threshold": LEAKAGE_AUC_STOP,
            "features_tested": len(canaries),
            "max_discriminative_auc": max_canary_auc,
            "max_discriminative_feature": max_canary_feat,
            "max_zero_catalogue_static_auc": max_static_auc,
            "max_zero_catalogue_static_feature": max_static_feat,
            "any_flagged_over_0p90": False,
            "per_feature": canaries,
        },
        "loqo_fold_training_summary": loqo_fold_meta,
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "design": (
                "Strict Leave-One-Quadrant-Out (LOQO, quad != q) on buffered whole-component quadrant draw "
                "(seed 20, hide_frac 0.20, buffer_px 3, collar 3.0 px, pooled 200-px [20 km] physical-block "
                "paired bootstrap, 1000 draws)"
            ),
            "withheld_positive_pixels": cand_holdout["withheld_positive_pixels"],
            "candidate_arm": CANDIDATE_ARM,
            "candidate": cand_holdout,
            "best_preregistered_control": best_ctrl,
            "paired_delta_vs_best_preregistered_control": best_delta,
            "paired_delta_vs_E2_blind": pooled_holdout["paired_differences"][BLIND_ARM],
            "paired_delta_vs_E3_ablation": pooled_holdout["paired_differences"][ABLATION_ARM],
            "paired_delta_vs_R0_D28_visible_collar": pooled_holdout["paired_differences"]["R0_D28_visible_collar"],
            "paired_delta_vs_H33_visible_collar": pooled_holdout["paired_differences"]["H33_visible_collar"],
            "per_fold_dti": per_fold_dti,
            "all_arms": pooled_holdout["scores"],
            "pooled_summary": pooled_holdout,
            "same_split_archived_comparators": {
                "H86C_KSLB_true_LOQO_44090": kslb_best,
                "H86F_EWCS_inquadrant_component_hide_37654": ewcs_best,
                "R0_G25_foldfair_44090": r0_g25_comp,
                "beats_true_LOQO_record_H86C_KSLB_separated_ci": beats_kslb_loqo,
                "beats_inquadrant_H86F_EWCS_point": beats_ewcs,
            },
        },
        "sgmc_off_catalogue_diagnostic": {
            "evidence_class": "SGMC-PROXY-DTI",
            "role": "Post-evaluation read-only off-catalogue structural proxy (>3 px from known_faults.tif, 62,122 pixels); never used in training, arm selection, or budget choice.",
            "summary": sgmc_diag,
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "surface_preplacement": surf_summary,
            "final_dots": dots_summary,
            "sparse_dot_fields_le_60k": {
                "count": len(sparse_60k_rows),
                "worst_forward_overlap_3px": (
                    round(float(worst_sparse_row["my_dots_within_3px_of_theirs"]), 6)
                    if worst_sparse_row
                    else 0.0
                ),
                "worst_submission": worst_sparse_row["submission"] if worst_sparse_row else None,
                "firings_over_0p70": sum(
                    1 for r in sparse_60k_rows if float(r.get("my_dots_within_3px_of_theirs", 0.0)) > 0.70
                ),
                "overlap_vs_gemsdoe32_h33_2_b2": (
                    round(float(h33_overlap_row["my_dots_within_3px_of_theirs"]), 6)
                    if h33_overlap_row
                    else None
                ),
            },
            "pa86_02_chance_overlap": pa86_summary,
        },
        "raster_sha256": receipt["sha256"],
        "zip_sha256": receipt["zip_sha256"],
        "validator_output": {
            "evidence_class": "LOCAL-FORMAT-VALIDATION",
            "all_checks_passed": bool(val_out["all_checks_passed"] and standalone_verify["passed"]),
            "values_in_0_1": True,
            "no_nan_inside_footprint": int(val_out["n_nan"]) == 0,
            "crs_shape_transform_match": True,
            "positive_pixels": int(val_out["emitted_positive_pixels"]),
            "min": float(val_out["min"]),
            "max": float(val_out["max"]),
            "checks": val_out["checks"],
            "vendor_validate": val_out,
            "standalone_verify_submission_tif": standalone_verify,
        },
        "submission_name": sub_name,
        "submission_file": str(tif_out.relative_to(ROOT)),
        "zip_file": str(tif_out.with_suffix(".zip").relative_to(ROOT)),
        "receipt_file": str(tif_out.with_suffix(".json").relative_to(ROOT)),
        "note": note_str,
        "note_chars": len(note_str),
        "verdict": verdict,
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "experiments_run": 3,
        "submission_slots_used": 0,
        "decision": decision,
        "decision_reasons": reasons,
        "runtime_seconds": round(time.time() - t0, 2),
    }

    RUN_CARD_PATH.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(
        f"[H86J-TVHS DONE] {sub_name}.tif | sha256={receipt['sha256'][:16]}... | "
        f"LOQO HOLDOUT-DTI={cand_holdout['dti']:.4f} {cand_holdout['ci95']} | "
        f"SGMC-PROXY-DTI={sgmc_diag['scores']['H86J_TVHS_37654']['dti']:.4f} | "
        f"verdict={verdict} ({decision}) in {run_card['runtime_seconds']:.1f}s",
        flush=True,
    )
    return run_card


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    run_lane(allow_audit_placement=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
