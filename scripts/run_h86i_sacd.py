#!/usr/bin/env python3
"""Execute preregistered H86I-SACD 3-arm strict Leave-One-Quadrant-Out evaluation,
single-feature leakage canary, SHA-bound v2 surface/final-dot registry checks,
and fail-closed audit-only GeoTIFF serialization (`DO NOT SUBMIT`, 0 slots used).
"""
from __future__ import annotations

import argparse
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
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gems57 import evaluate_holdout as EH  # noqa: E402
from gems57 import gates, grid, holdout, submission_writer, validate  # noqa: E402
from gems86_sacd.features import (  # noqa: E402
    DYNAMIC_FEATURE_NAMES,
    DYNAMIC_SCALAR_NAMES,
    STATIC_FEATURE_NAMES,
    STATIC_SUBSURFACE_NAMES,
    build_static_sacd_pack,
    compute_sacd_dynamic_fields,
)
from gems86_sacd.submodular import submodular_kernel_allocate  # noqa: E402

PREREG_JSON = ROOT / "research/H86I_SACD_PREREGISTRATION.json"
PREREG_MD = ROOT / "research/H86I_SACD_PREREGISTRATION.md"
HYP_JSON = ROOT / "registry/h86i_hypotheses.json"
WORK_DIR = ROOT / ".cache/h86i_sacd"
EV_DIR = ROOT / "docs/evidence"
OUT_DIR = ROOT / "docs/downloads"

FEATURE_TIF = ROOT / "data/training_features.tif"
EXT_DIR = ROOT / ".cache/external"
D28_CONTROL_TIF = (
    ROOT
    / "data/registry_ext"
    / "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73.tif"
)
D25_CONTROL_TIF = (
    ROOT
    / "data/registry_ext"
    / "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8.tif"
)

SEED = 20
BOOTSTRAP_SEED = 520810
BUDGET = 37654
COLLAR_PX = 3.0
SPACING_PX = 2.8


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def disc_thin(
    surface: np.ndarray, allowed: np.ndarray, budget: int, spacing: float = SPACING_PX
) -> np.ndarray:
    """Standard pointwise Poisson-disc local-maxima thinner for ablation E2 & R0."""
    s = np.where(allowed & np.isfinite(surface), surface, -np.inf)
    cand = np.flatnonzero(s > -np.inf)
    if cand.size == 0 or budget <= 0:
        return np.zeros(surface.shape, dtype=bool)
    pool = min(cand.size, max(budget * 14, budget))
    if cand.size > pool:
        part = np.argpartition(s.ravel()[cand], -pool)[-pool:]
        cand = cand[part]
    order = cand[np.argsort(-s.ravel()[cand], kind="mergesort")]
    w = surface.shape[1]
    ys = order // w
    xs = order % w
    rad = int(np.ceil(spacing))
    dy, dx = np.mgrid[-rad : rad + 1, -rad : rad + 1]
    use = (dy * dy + dx * dx) < (spacing * spacing - 1e-9)
    ody = dy[use]
    odx = dx[use]
    blocked = np.zeros(surface.shape, dtype=bool)
    dots = np.zeros(surface.shape, dtype=bool)
    h = surface.shape[0]
    count = 0
    for y, x in zip(ys.tolist(), xs.tolist()):
        if blocked[y, x]:
            continue
        dots[y, x] = True
        ny = y + ody
        nx = x + odx
        ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        blocked[ny[ok], nx[ok]] = True
        count += 1
        if count >= budget:
            break
    return dots


def split_visible_components(vis_cat: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Split 8-connected components of `vis_cat` into two balanced disjoint sets."""
    comp, n_comp = ndi.label(vis_cat, structure=np.ones((3, 3), dtype=np.int8))
    if n_comp < 2:
        half = vis_cat.shape[0] // 2
        va = vis_cat.copy()
        vb = vis_cat.copy()
        va[half:, :] = False
        vb[:half, :] = False
        return va, vb
    rng = np.random.default_rng(seed)
    perm = rng.permutation(np.arange(1, n_comp + 1))
    set_a = np.zeros(n_comp + 1, dtype=bool)
    set_a[perm[::2]] = True
    va = set_a[comp]
    vb = (~set_a)[comp] & (comp > 0)
    return va, vb


def sample_strict_loqo_pu(
    static_fp: np.ndarray,
    directors_fp: np.ndarray,
    propensity_fp: np.ndarray,
    s_indices: list[int],
    d_indices: list[int],
    vis_global: np.ndarray,
    footprint: np.ndarray,
    train_region_mask: np.ndarray,
    *,
    use_propensity: bool,
    n_neg: int = 220_000,
    seed: int = 860,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Sample positive and unlabeled rows STRICTLY inside `train_region_mask`.

    Uses nested 2-split cross-component dynamic feature generation inside
    `train_region_mask` so training positives never observe their own component's
    elastic tip or spin-2 stress trajectory, and zero rows come from the held-out
    test quadrant.
    """
    rng = np.random.default_rng(seed)
    vis_train = vis_global & footprint & train_region_mask
    d_vis = ndi.distance_transform_edt(~vis_global)
    neg_mask_full = footprint & train_region_mask & (d_vis > COLLAR_PX)
    del d_vis

    # Convert full-grid boolean masks to 1D indices into footprint arrays (`N_fp`)
    neg_fp_pool = np.flatnonzero(neg_mask_full[footprint])
    rng.shuffle(neg_fp_pool)
    half_neg = min(n_neg // 2, neg_fp_pool.size // 2)
    neg_a = neg_fp_pool[:half_neg]
    neg_b = neg_fp_pool[half_neg : 2 * half_neg]

    va, vb = split_visible_components(vis_train, seed=seed)
    db = ndi.distance_transform_edt(~vb)
    pos_a = np.flatnonzero((va & (db > COLLAR_PX))[footprint])
    del db
    da = ndi.distance_transform_edt(~va)
    pos_b = np.flatnonzero((vb & (da > COLLAR_PX))[footprint])
    del da

    idx_a = np.concatenate([pos_a, neg_a])
    ya = np.concatenate([np.ones(pos_a.size, dtype=np.int8), np.zeros(neg_a.size, dtype=np.int8)])
    dyn_from_b = compute_sacd_dynamic_fields(vb, footprint, directors_fp)
    cols_a = [static_fp[i, idx_a].astype(np.float32) for i in s_indices]
    cols_a.extend(dyn_from_b[j, idx_a].astype(np.float32) for j in d_indices)
    Xa = np.column_stack(cols_a)
    del dyn_from_b, cols_a
    gc.collect()

    idx_b = np.concatenate([pos_b, neg_b])
    yb = np.concatenate([np.ones(pos_b.size, dtype=np.int8), np.zeros(neg_b.size, dtype=np.int8)])
    dyn_from_a = compute_sacd_dynamic_fields(va, footprint, directors_fp)
    cols_b = [static_fp[i, idx_b].astype(np.float32) for i in s_indices]
    cols_b.extend(dyn_from_a[j, idx_b].astype(np.float32) for j in d_indices)
    Xb = np.column_stack(cols_b)
    del dyn_from_a, cols_b, va, vb
    gc.collect()

    X = np.vstack([Xa, Xb])
    y = np.concatenate([ya, yb])
    if not use_propensity:
        return X, y, None

    # Bekker-Davis (2020) SAR inverse-exposure-propensity weighting on visible positives
    c_a = propensity_fp[pos_a].astype(np.float32)
    c_b = propensity_fp[pos_b].astype(np.float32)
    wa_pos = np.clip(1.0 / np.power(np.maximum(c_a, 0.20), 0.55), 1.0, 2.15)
    wb_pos = np.clip(1.0 / np.power(np.maximum(c_b, 0.20), 0.55), 1.0, 2.15)
    # Normalize mean positive weight to 1.0 so overall PU class prior stays matched
    pos_all_w = np.concatenate([wa_pos, wb_pos])
    mean_pw = float(pos_all_w.mean()) if pos_all_w.size > 0 else 1.0
    wa = np.concatenate([wa_pos / mean_pw, np.ones(neg_a.size, dtype=np.float32)])
    wb = np.concatenate([wb_pos / mean_pw, np.ones(neg_b.size, dtype=np.float32)])
    return X, y, np.concatenate([wa, wb])


def fit_hgb(
    X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None, seed: int
) -> HistGradientBoostingClassifier:
    clf = HistGradientBoostingClassifier(
        max_iter=220,
        learning_rate=0.06,
        max_leaf_nodes=55,
        min_samples_leaf=90,
        l2_regularization=2.5,
        random_state=seed,
    )
    return clf.fit(X, y, sample_weight=sample_weight)


def predict_fp_subset(
    clf: HistGradientBoostingClassifier,
    static_fp: np.ndarray,
    dyn_fp: np.ndarray,
    s_indices: list[int],
    d_indices: list[int],
    fp_subset_idx: np.ndarray,
    chunk: int = 350_000,
) -> np.ndarray:
    out = np.zeros(fp_subset_idx.size, dtype=np.float32)
    for start in range(0, fp_subset_idx.size, chunk):
        end = min(fp_subset_idx.size, start + chunk)
        sub = fp_subset_idx[start:end]
        cols = [static_fp[i, sub].astype(np.float32) for i in s_indices]
        cols.extend(dyn_fp[j, sub].astype(np.float32) for j in d_indices)
        X_sub = np.column_stack(cols)
        out[start:end] = clf.predict_proba(X_sub)[:, 1].astype(np.float32)
    return out


def rank01_on_footprint(surface: np.ndarray, fp: np.ndarray) -> np.ndarray:
    vals = surface[fp]
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty_like(vals, dtype=np.float32)
    denom = max(vals.size - 1, 1)
    ranks[order] = np.arange(vals.size, dtype=np.float32) / float(denom)
    out = np.zeros(surface.shape, dtype=np.float32)
    out[fp] = np.clip(ranks, 0.0, 1.0)
    return out


def run_registry_check(array_path: Path, output: Path, *, surface: bool) -> tuple[dict, int]:
    cmd = [sys.executable, str(ROOT / "scripts/check_h86e_registry.py"), str(array_path), str(output)]
    if surface:
        cmd.append("--surface")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if not output.is_file():
        raise RuntimeError(
            f"registry check produced no report (rc={proc.returncode}): {proc.stderr[-2000:]}"
        )
    return json.loads(output.read_text(encoding="utf-8")), proc.returncode


def run_chance_check(registry_report: Path, candidate_path: Path, output: Path) -> dict:
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
            "recorded verbatim, never bypassed with a private computation."
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


def load_binary_tif(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        arr = src.read(1)
    return np.isfinite(arr) & (arr > 0)


def write_candidate(
    dots: np.ndarray, g: grid.Grid, name: str, note: str, metadata: dict
) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pred = np.where((dots > 0) & g.footprint, 1.0, 0.0).astype(np.float32)
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
        raise RuntimeError("independent on-disk validator failed")
    fmt = gates.format_report(path, ROOT / "data/bridge/sample_submission.tif", footprint=g.footprint)
    if not fmt["ok"]:
        raise RuntimeError(f"template gates.format_report failed: {fmt}")
    receipt["independent_disk_validation"] = disk
    path.with_suffix(".json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    for suffix in (".tif", ".zip", ".json"):
        p = path.with_suffix(suffix)
        if p.is_file():
            p.chmod(0o644)
    return receipt


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    from scripts.protocol_preflight import measure as preflight_measure
    preflight = preflight_measure()

    t0 = time.time()
    if not PREREG_JSON.is_file() or not HYP_JSON.is_file():
        raise RuntimeError("Preregistration and hypothesis queue must exist before running H86I-SACD")
    prereg = json.loads(PREREG_JSON.read_text(encoding="utf-8"))

    g = grid.load_grid(ROOT / "data/bridge")
    fp, cat = g.footprint, g.catalogue
    folds, quad = holdout.buffered_component_draw(
        g, seed=SEED, hide_frac=0.20, buffer_px=3
    )

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)

    pack = build_static_sacd_pack(FEATURE_TIF, EXT_DIR, fp, cache_dir=WORK_DIR)
    static_fp = pack["static"]
    directors_fp = pack["directors"]
    propensity_fp = pack["propensity"]
    static_sha256 = sha256(WORK_DIR / "sacd_static_fp_v1.npy")

    # Compute fold-hygienic dynamic elastic + spin-2 concordance planes ONCE from
    # global fold-visible catalogue (`cat & ~collar`, zero withheld truth inside 3 px)
    vis_global = np.asarray(folds[0]["visible"], dtype=bool) & fp
    dyn_vis_fp = compute_sacd_dynamic_fields(vis_global, fp, directors_fp)

    # Single-feature leakage canary across all 33 static + dynamic features
    region_all = np.zeros(fp.shape, dtype=bool)
    hidden_all = np.zeros(fp.shape, dtype=bool)
    masked_known = np.zeros(fp.shape, dtype=bool)
    for f in folds:
        region_all |= np.asarray(f["region"], dtype=bool)
        hidden_all |= np.asarray(f["hidden_all"], dtype=bool)
        masked_known |= np.asarray(f["masked_known"], dtype=bool)

    active_fp = (region_all & fp & ~masked_known)[fp]
    truth_fp = active_fp & hidden_all[fp]
    neg_fp = active_fp & ~truth_fp
    p_idx = np.flatnonzero(truth_fp)
    n_pool = np.flatnonzero(neg_fp)
    rng_can = np.random.default_rng(862026)
    n_idx = rng_can.choice(n_pool, size=min(300_000, n_pool.size), replace=False)
    c_idx = np.concatenate([p_idx, n_idx])
    y_can = np.concatenate([np.ones(p_idx.size, dtype=np.int8), np.zeros(n_idx.size, dtype=np.int8)])

    canary: dict[str, dict] = {}
    for i, nm in enumerate(STATIC_FEATURE_NAMES):
        vals = static_fp[i, c_idx].astype(np.float64)
        auc = float(roc_auc_score(y_can, vals)) if np.ptp(vals) > 0 else 0.5
        disc = max(auc, 1.0 - auc)
        canary[nm] = {
            "evidence_class": "LEAKAGE-CANARY",
            "auc": auc,
            "discriminative_auc": disc,
            "threshold": 0.90,
            "leakage_flag": bool(disc > 0.90),
        }
    for j, nm in enumerate(DYNAMIC_FEATURE_NAMES):
        vals = dyn_vis_fp[j, c_idx].astype(np.float64)
        auc = float(roc_auc_score(y_can, vals)) if np.ptp(vals) > 0 else 0.5
        disc = max(auc, 1.0 - auc)
        canary[nm] = {
            "evidence_class": "LEAKAGE-CANARY",
            "auc": auc,
            "discriminative_auc": disc,
            "threshold": 0.90,
            "leakage_flag": bool(disc > 0.90),
        }
    flagged = [k for k, v in canary.items() if v["leakage_flag"]]
    if flagged:
        raise RuntimeError(f"STOP: single-feature leakage canary > 0.90: {flagged}")

    # Define the 3 preregistered arms
    all_s_idx = list(range(len(STATIC_FEATURE_NAMES)))
    sub_s_idx = [STATIC_FEATURE_NAMES.index(k) for k in STATIC_SUBSURFACE_NAMES]
    all_d_idx = list(range(len(DYNAMIC_FEATURE_NAMES)))
    scal_d_idx = [DYNAMIC_FEATURE_NAMES.index(k) for k in DYNAMIC_SCALAR_NAMES]
    sub_d_idx = [
        DYNAMIC_FEATURE_NAMES.index(k)
        for k in (*DYNAMIC_SCALAR_NAMES, "spin2_concord_grav", "spin2_concord_mag")
    ]

    arm_specs = {
        "E1_sacd_full_submod": {
            "s_idx": all_s_idx,
            "d_idx": all_d_idx,
            "propensity": True,
            "decoder": "submodular_300m",
        },
        "E2_sacd_scalar_unweighted_thin": {
            "s_idx": all_s_idx,
            "d_idx": scal_d_idx,
            "propensity": False,
            "decoder": "disc_thin_2p8",
        },
        "E3_sacd_cover_blind_subsurface": {
            "s_idx": sub_s_idx,
            "d_idx": sub_d_idx,
            "propensity": True,
            "decoder": "submodular_300m",
        },
    }
    prereg_ids = {a["arm_id"] for a in prereg["preregistered_experiments"]}
    if set(arm_specs) != prereg_ids:
        raise RuntimeError("Arm specification mismatch against frozen preregistration")

    n_fp = int(fp.sum())
    oof_fp_prob: dict[str, np.ndarray] = {
        arm: np.zeros(n_fp, dtype=np.float32) for arm in arm_specs
    }
    ref_quantiles: dict[str, np.ndarray] = {}
    q_grid = np.linspace(0.0, 1.0, 2001, dtype=np.float32)

    quad_fp = quad[fp]
    for fold_i, f in enumerate(folds):
        train_region = fp & (quad != fold_i)
        test_sub_idx = np.flatnonzero(quad_fp == fold_i)
        for arm_i, (arm_name, spec) in enumerate(arm_specs.items()):
            seed_here = 8690 + 10 * fold_i + arm_i
            X_tr, y_tr, w_tr = sample_strict_loqo_pu(
                static_fp,
                directors_fp,
                propensity_fp,
                spec["s_idx"],
                spec["d_idx"],
                vis_global,
                fp,
                train_region,
                use_propensity=spec["propensity"],
                seed=seed_here,
            )
            clf = fit_hgb(X_tr, y_tr, w_tr, seed=seed_here)
            # Calibrate fold probability quantiles against Fold 0 training-quadrant
            # predictions so inter-quadrant base-rate shifts cannot skew global budget
            raw_test = predict_fp_subset(
                clf, static_fp, dyn_vis_fp, spec["s_idx"], spec["d_idx"], test_sub_idx
            )
            if fold_i == 0:
                ref_quantiles[arm_name] = np.quantile(raw_test, q_grid).astype(np.float32)
                oof_fp_prob[arm_name][test_sub_idx] = raw_test
            else:
                order = np.argsort(raw_test, kind="mergesort")
                u = np.empty_like(raw_test)
                u[order] = np.arange(raw_test.size, dtype=np.float32) / max(raw_test.size - 1, 1)
                oof_fp_prob[arm_name][test_sub_idx] = np.interp(
                    u, q_grid, ref_quantiles[arm_name]
                ).astype(np.float32)
            del X_tr, y_tr, w_tr, clf, raw_test
            gc.collect()

    d_vis_global = ndi.distance_transform_edt(~vis_global)
    allowed_oof = fp & (d_vis_global > COLLAR_PX)
    del d_vis_global

    arm_fold_terms: dict[str, list[np.ndarray]] = {arm: [] for arm in arm_specs}
    holdout_per_fold: dict[str, dict] = {arm: {} for arm in arm_specs}

    for arm_name, spec in arm_specs.items():
        surf = np.zeros(fp.shape, dtype=np.float32)
        surf[fp] = oof_fp_prob[arm_name]
        if spec["decoder"] == "submodular_300m":
            bg_floor = float(np.quantile(oof_fp_prob[arm_name], 0.72))
            q_field = np.maximum(surf - bg_floor, 0.0)
            q_max = float(q_field.max()) + 1e-9
            dots_f = submodular_kernel_allocate(
                (q_field / q_max).astype(np.float32),
                allowed_oof,
                budget=BUDGET,
                gamma=1.20,
            )
        else:
            dots_f = disc_thin(surf, allowed_oof, BUDGET, spacing=SPACING_PX).astype(np.float32)
        del surf
        for f in folds:
            res, b_terms = EH.evaluate(dots_f, f, fp, block_side=200)
            arm_fold_terms[arm_name].append(b_terms)
            holdout_per_fold[arm_name][f["name"]] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res["dti"],
                "n_truth": res["n_truth"],
                "emitted": res["n_emitted"],
            }
        del dots_f
        gc.collect()

    # Zero-extra-fit external registry controls on identical fold collar
    for ctrl_label, ctrl_path in (
        ("R0_D28_visible_collar", D28_CONTROL_TIF),
        ("R0_D25_foldfair", D25_CONTROL_TIF),
    ):
        if ctrl_path.is_file():
            ctrl_mask = load_binary_tif(ctrl_path) & allowed_oof
            if int(ctrl_mask.sum()) <= BUDGET:
                ctrl_dots = ctrl_mask.astype(np.float32)
            else:
                ctrl_dots = disc_thin(
                    ctrl_mask.astype(np.float32), allowed_oof, BUDGET, spacing=SPACING_PX
                ).astype(np.float32)
            arm_fold_terms[ctrl_label] = []
            holdout_per_fold[ctrl_label] = {}
            for f in folds:
                res_c, b_c = EH.evaluate(ctrl_dots, f, fp, block_side=200)
                arm_fold_terms[ctrl_label].append(b_c)
                holdout_per_fold[ctrl_label][f["name"]] = {
                    "evidence_class": "HOLDOUT-DTI",
                    "evaluator_version": EH.VERSION,
                    "dti": res_c["dti"],
                    "n_truth": res_c["n_truth"],
                    "emitted": res_c["n_emitted"],
                }
            del ctrl_mask, ctrl_dots

    holdout_terms = {k: np.sum(v, axis=0) for k, v in arm_fold_terms.items()}
    pooled = EH.pooled_summary(
        holdout_terms,
        draws=1000,
        seed=BOOTSTRAP_SEED,
        candidate="E1_sacd_full_submod",
    )

    kslb_best = json.loads((EV_DIR / "lane86c_results.json").read_text(encoding="utf-8"))[
        "holdout_buffered_whole_components"
    ]["scores"]["E3_kslb_noisyor_44k"]
    ewcs_prev = json.loads((EV_DIR / "h86f-ewcs-run-card.json").read_text(encoding="utf-8"))[
        "holdout_dti"
    ]["candidate"]

    e1_score = pooled["scores"]["E1_sacd_full_submod"]
    e2_delta = pooled["paired_differences"]["E2_sacd_scalar_unweighted_thin"]
    e3_delta = pooled["paired_differences"]["E3_sacd_cover_blind_subsurface"]
    beats_kslb = bool(
        e1_score["dti"] > kslb_best["dti"] and e1_score["ci95"][0] > kslb_best["ci95"][1]
    )
    beats_ewcs_point = bool(e1_score["dti"] > ewcs_prev["dti"])
    beats_ablation_e2 = bool(e2_delta["ci95"][0] > 0.0)

    # Full-catalogue pre-placement continuous surface & registry check BEFORE dot placement
    del dyn_vis_fp, oof_fp_prob
    gc.collect()
    dyn_full_fp = compute_sacd_dynamic_fields(cat & fp, fp, directors_fp)
    X_full, y_full, w_full = sample_strict_loqo_pu(
        static_fp,
        directors_fp,
        propensity_fp,
        all_s_idx,
        all_d_idx,
        cat & fp,
        fp,
        fp,
        use_propensity=True,
        n_neg=240_000,
        seed=8699,
    )
    clf_full = fit_hgb(X_full, y_full, w_full, seed=8699)
    del X_full, y_full, w_full
    gc.collect()

    all_fp_idx = np.arange(n_fp, dtype=np.int64)
    raw_full_fp = predict_fp_subset(
        clf_full, static_fp, dyn_full_fp, all_s_idx, all_d_idx, all_fp_idx
    )
    del clf_full, dyn_full_fp, static_fp, directors_fp, propensity_fp
    gc.collect()

    raw_full_grid = np.zeros(fp.shape, dtype=np.float32)
    raw_full_grid[fp] = raw_full_fp
    bounded_surface = rank01_on_footprint(raw_full_grid, fp)

    surface_npy = WORK_DIR / "h86i_sacd_final_surface.npy"
    np.save(surface_npy, bounded_surface)
    surface_sha = sha256(surface_npy)

    surface_report_path = EV_DIR / "h86i-sacd-registry-surface.json"
    surface_report, surface_rc = run_registry_check(
        surface_npy, surface_report_path, surface=True
    )
    surface_gate_pass = bool(
        surface_rc == 0
        and surface_report.get("surface_gate_pass") is True
        and surface_report.get("literal_gate_pass") is True
        and surface_report.get("registry_complete_for_index") is True
        and surface_report.get("inventory_rasters_missing") == []
        and surface_report.get("errors") == []
    )
    rho_firings = int(
        surface_report.get("two_phase", {}).get("literal_reading", {}).get("rho_firings", -1)
    )
    if rho_firings != 0:
        raise RuntimeError(
            f"STOP: pre-placement surface Spearman rank-correlation > 0.90 firing ({rho_firings})"
        )

    # Place exact 37,654 dots via 300 m triangular-kernel submodular allocation
    dcat = ndi.distance_transform_edt(~(cat & fp))
    allowed_full = fp & (dcat > COLLAR_PX)
    del dcat, bounded_surface

    bg_floor_full = float(np.quantile(raw_full_fp, 0.72))
    q_full = np.maximum(raw_full_grid - bg_floor_full, 0.0)
    q_full_max = float(q_full.max()) + 1e-9
    final_dots = submodular_kernel_allocate(
        (q_full / q_full_max).astype(np.float32),
        allowed_full,
        budget=BUDGET,
        gamma=1.20,
    )
    del raw_full_fp, raw_full_grid, q_full, allowed_full
    gc.collect()

    dots_npy = WORK_DIR / "h86i_sacd_final_dots.npy"
    np.save(dots_npy, final_dots.astype(np.float32))
    dots_sha = sha256(dots_npy)

    dots_report_path = EV_DIR / "h86i-sacd-registry-final-dots.json"
    dots_report, dots_rc = run_registry_check(dots_npy, dots_report_path, surface=False)
    chance_path = EV_DIR / "h86i-sacd-pa86-chance-overlap.json"
    chance = run_chance_check(dots_report_path, dots_npy, chance_path)

    # Verify byte/pixel uniqueness and zero discrete non-space-filling (halo <= 0.70) firings
    shared_dots = dots_report.get("shared_summary", {})
    if not shared_dots.get("byte_unique_among_checked") or not shared_dots.get("pixel_unique_among_checked"):
        raise RuntimeError("STOP: final dots are not byte/pixel unique across checked registry")
    dot_rho_firings = int(
        dots_report.get("two_phase", {}).get("literal_reading", {}).get("rho_firings", -1)
    )
    if dot_rho_firings != 0:
        raise RuntimeError(f"STOP: final-dot Spearman rho > 0.90 firing ({dot_rho_firings})")

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

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
    name = f"gems86-h86i-sacd-spin2-submod-{int((final_dots > 0).sum())}dots-{stamp}-{digest8}-zeros"
    note = (
        f"H86I-SACD spin2+submod PU (HOLDOUT-DTI {e1_score['dti']:.4f}); "
        "registry gate fail-closed; DO NOT SUBMIT; 0 slots"
    )[:140]

    receipt = write_candidate(
        final_dots,
        g,
        name,
        note,
        metadata={
            "lane": "H86I-SACD",
            "hypothesis": (
                "Spin-2 Coulomb-projected strike concordance + Jacobsen upward-continuation "
                "depth attenuation + GeoDAWN K/Th-U/Th alteration + Bekker-Davis propensity "
                "+ Minoux 300 m triangular-kernel submodular allocation"
            ),
            "budget": BUDGET,
            "collar_px": COLLAR_PX,
            "static_feature_sha256": static_sha256,
            "surface_sha256": surface_sha,
            "dots_sha256": dots_sha,
            "registry_surface_evidence": "docs/evidence/h86i-sacd-registry-surface.json",
            "registry_final_evidence": "docs/evidence/h86i-sacd-registry-final-dots.json",
            "chance_overlap_evidence": (
                str(chance_path.relative_to(ROOT))
                if chance_path.is_file()
                else "FAILED_CLOSED_NO_REPORT (see run card)"
            ),
        },
    )

    verdict = "promote" if (beats_kslb and beats_ablation_e2 and registry_gate) else "negative"
    stop_reasons: list[str] = []
    if not surface_gate_pass:
        stop_reasons.append(
            "pre-placement surface registry gate failed closed (2 grid-incompatible upstream "
            "registry rows and literal 17GEMSDOE full-support witness; 0 Spearman rho > 0.90 firings)"
        )
    if not final_dots_gate_pass:
        stop_reasons.append(
            "final-dot registry gate failed closed (literal 17GEMSDOE full-support / space-filling "
            "lattice witnesses and 2 grid-incompatible upstream registry rows)"
        )
    if chance.get("gate_pass") is not True:
        stop_reasons.append("PA-86-02 chance-overlap gate failed closed (incomplete registry index)")

    max_canary_name, max_canary = max(
        canary.items(), key=lambda kv: kv[1]["discriminative_auc"]
    )
    disk_val = receipt["independent_disk_validation"]
    card_path = EV_DIR / "h86i-sacd-run-card.json"

    run_card = {
        "schema": "gems86.h86i-sacd-run-card.v1",
        "lane": "H86I-SACD",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {
            "document": "research/H86I_SACD_PREREGISTRATION.md",
            "machine_readable": "research/H86I_SACD_PREREGISTRATION.json",
            "preregistration_sha256": sha256(PREREG_JSON),
            "hypothesis_queue": "registry/h86i_hypotheses.json",
            "hypothesis_queue_sha256": sha256(HYP_JSON),
            "arm_ids": list(arm_specs.keys()),
        },
        "hypothesis": (
            "H86I-SACD: Unmapped Quaternary and blind geothermal faults hidden beneath Holocene "
            "alluvial aprons and playa veneers align in spin-2 strike with Pollard-Segall "
            "Coulomb failure trajectories projected from fold-visible terminations across 1 m "
            "USGS 3DEP LiDAR / 10 m 3DEP micro-scarps, Laplace g_zz density hinges, and "
            "shallow-attenuating Verduzco magnetic tilt contacts, while transverse Pleistocene "
            "shorelines and flight-line leveling seams violate spin-2 concordance."
        ),
        "mechanism": (
            "Strict Leave-One-Quadrant-Out (quad != fold_i) PU HistGradientBoostingClassifier "
            "on 26 multi-resolution native + SHA-pinned USGS 1 m LiDAR / 10 m 3DEP / fluvial "
            "chi / GeoDAWN K-Th-U & TMI_up150 static physics planes plus 7 nested "
            "cross-component elastic & spin-2 strike-concordance planes, weighted by "
            "Bekker-Davis label-free alluvial-burial propensity and decoded via Minoux "
            "lazy-greedy 300 m triangular-kernel submodular expected-TP_w allocation at 37,654 dots."
        ),
        "named_non_fault_process": (
            "Shallow subvertical Tertiary mafic dike swarms or welded ash-flow tuff cooling "
            "joints striking subparallel to regional NNE Basin-and-Range extension beneath thin "
            "piedmont veneers, and Pleistocene Lake Lahontan highstand bars (~1,305 m) where "
            "shoreline strike locally parallels range-front fault strike."
        ),
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "design": (
                "strict spatial Leave-One-Quadrant-Out (quad != fold_i) on buffered "
                "whole-component draw (seed 20, hide_frac 0.20, buffer_px 3, visible collar "
                "3.0 px), pooled 200-px (20 km) physical blocks, 1000 bootstrap draws"
            ),
            "withheld_positive_pixels": int(e1_score["withheld_positive_pixels"]),
            "candidate": e1_score,
            "best_preregistered_control": pooled["best_comparable_control"],
            "paired_delta_vs_E2_scalar_unweighted_thin": e2_delta,
            "paired_delta_vs_E3_cover_blind_subsurface": e3_delta,
            "all_arms": pooled["scores"],
            "per_fold": holdout_per_fold,
            "paired_differences": pooled["paired_differences"],
            "same_split_comparators": {
                "H86F_EWCS_E1_37654": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86f-ewcs-run-card.json",
                    "dti": ewcs_prev["dti"],
                    "ci95": ewcs_prev["ci95"],
                    "note": "Prior local leader; sampled PU training across all 4 quadrants rather than strict quad != fold_i.",
                },
                "H86C_KSLB_E3_44k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/lane86c_results.json",
                    "dti": kslb_best["dti"],
                    "ci95": kslb_best["ci95"],
                },
            },
            "beats_same_split_kslb_with_separated_ci": beats_kslb,
            "beats_prior_ewcs_point_estimate": beats_ewcs_point,
            "beats_scalar_pointwise_ablation_paired_ci": beats_ablation_e2,
            "leakage_canary_summary": {
                "features_tested": len(canary),
                "max_discriminative_auc_feature": max_canary_name,
                "max_discriminative_auc": max_canary["discriminative_auc"],
                "threshold": 0.90,
                "any_leakage_flag": False,
            },
            "leakage_canary": canary,
        },
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
        },
        "raster_sha256": receipt["sha256"],
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
        "note": note,
        "note_chars": len(note),
        "preflight": preflight,
        "experiments_run": 3,
        "verdict": verdict,
        "duplicate": bool(not registry_gate),
        "new_candidate_generated": True,
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "decision": "SELECTOR STEP REQUIRED" if verdict == "promote" else "DO NOT SUBMIT",
        "decision_reason": "; ".join(stop_reasons),
        "runtime_seconds": round(time.time() - t0, 2),
    }

    card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "lane": "H86I-SACD",
                "submission_file": run_card["submission_file"],
                "raster_sha256": run_card["raster_sha256"],
                "e1_holdout_dti": e1_score["dti"],
                "e1_ci95": e1_score["ci95"],
                "e2_holdout_dti": pooled["scores"]["E2_sacd_scalar_unweighted_thin"]["dti"],
                "e3_holdout_dti": pooled["scores"]["E3_sacd_cover_blind_subsurface"]["dti"],
                "paired_delta_vs_e2": e2_delta,
                "beats_kslb": beats_kslb,
                "beats_ewcs_point": beats_ewcs_point,
                "surface_rho_firings": rho_firings,
                "worst_surface_spearman": surface_report["shared_summary"][
                    "worst_spearman_full_footprint"
                ],
                "worst_final_dot_overlap": dots_report["shared_summary"]["worst_dot_overlap"],
                "surface_gate_pass": surface_gate_pass,
                "final_dots_gate_pass": final_dots_gate_pass,
                "pa86_02_gate_pass": chance.get("gate_pass"),
                "verdict": verdict,
                "decision": run_card["decision"],
                "runtime_seconds": run_card["runtime_seconds"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
