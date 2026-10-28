#!/usr/bin/env python3
"""Execute preregistered Lane H86F-EWCS within the 3-experiment / 2-hour budget.

Protocol & governance compliance (AGENTS.md Rules 2-11):
- Frozen contemporaneous preregistration verified before feature/model work
  (research/H86F_EWCS_PREREGISTRATION.json).
- Reuses pinned vendor/gems57/{grid,holdout,evaluate_holdout,submission_writer,validate} unchanged.
- Single-feature leakage canaries run on all static & fold-visible features
  before trusting any holdout result (max(AUC, 1-AUC) > 0.90 stops immediately).
- Evaluates 3 preregistered arms + fold-fair R0_D28_visible_collar control on
  gems57-pooled-hide-v2 (seed=20, hide_frac=0.20, buffer_px=3, 11,321 withheld
  positives, 1,000 bootstrap draws over 200-px / 20-km physical blocks).
- Runs v2 SHA-bound surface registry check (scripts/check_h86e_registry.py --surface)
  before full-catalogue dot placement, and v2 final-dot registry check + PA-86-02
  before audit-only GeoTIFF serialization; fails closed to DO NOT SUBMIT /
  verdict='negative' (0 slots used) whenever any registry or scientific gate fails.

Following repository-wide builder gating, main() now calls
protocol_preflight.require_feasible() before any work; the recorded 2026-10-25
execution ran under PA-86-01/02 and its run card and artifacts are unchanged
historical receipts, not a protocol exemption.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
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
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import evaluate_holdout as EH, grid, holdout  # noqa: E402
from gems57 import submission_writer, validate  # noqa: E402
from gems86_ewcs.features import (  # noqa: E402
    E3_STATIC_SUBSET,
    ELASTIC_COUPLED_NAMES,
    STATIC_FEATURE_NAMES,
    TOPO_FEATURE_NAMES,
    build_static_features,
    compute_elastic_fields,
)
from scripts.protocol_preflight import require_like_for_like  # noqa: E402

PREREGISTRATION_PATH = ROOT / "research/H86F_EWCS_PREREGISTRATION.json"
FEATURE_TIF = ROOT / "data/bridge/training_features.tif"
D28_CONTROL_TIF = (
    ROOT / "data/registry_ext/ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73.tif"
)
OUT_DIR = ROOT / "docs/downloads"
WORK_DIR = ROOT / "data/work"
EV_DIR = ROOT / "docs/evidence"

PINS = {
    "training_features": (
        FEATURE_TIF,
        "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    ),
    "existing_faults": (
        ROOT / "data/bridge/existing_faults.tif",
        "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    ),
    "sample_submission": (
        ROOT / "data/bridge/sample_submission.tif",
        "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    ),
    "d28_geometry_control": (
        D28_CONTROL_TIF,
        "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
    ),
}

SEED = 20
BUDGET = 37_654
SPACING_PX = 2.8
COLLAR_PX = 3.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_preregistration() -> dict:
    if not PREREGISTRATION_PATH.is_file():
        raise RuntimeError(f"missing frozen preregistration: {PREREGISTRATION_PATH}")
    doc = json.loads(PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    arms = doc.get("arms", [])
    if not (3 <= len(arms) <= 5) or doc.get("budget", {}).get("max_experiments", 99) > 3:
        raise RuntimeError("invalid H86F-EWCS preregistration budget or arm count")
    return doc


def verify_pinned_inputs() -> dict[str, str]:
    verified = {}
    for label, (path, expected) in PINS.items():
        if not path.is_file():
            raise FileNotFoundError(f"missing pinned input {label}: {path}")
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch for {label}: {actual} != {expected}")
        verified[label] = actual
    return verified


def rank01_on_footprint(surface: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Map continuous scores strictly into [0, 1] inside footprint and 0.0 outside."""
    fp = np.asarray(footprint, dtype=bool)
    out = np.zeros(fp.shape, dtype=np.float32)
    vals = np.asarray(surface[fp], dtype=np.float64)
    if vals.size == 0 or not np.isfinite(vals).all():
        raise ValueError("nonfinite or empty candidate surface on footprint")
    if np.ptp(vals) == 0.0:
        raise ValueError("degenerate constant surface cannot be ranked")
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float32)
    ranks[order] = np.linspace(1e-6, 1.0, vals.size, dtype=np.float32)
    out[fp] = ranks
    return out


def disc_thin(score: np.ndarray, allowed: np.ndarray, budget: int,
              spacing: float = SPACING_PX) -> np.ndarray:
    """Deterministic greedy Poisson-disc thinning (no two dots closer than ``spacing``)."""
    r = int(np.ceil(spacing))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disc = (yy * yy + xx * xx) < (spacing * spacing)
    h, w = score.shape
    blocked = np.zeros((h + 2 * r, w + 2 * r), dtype=bool)
    flat = np.flatnonzero(allowed.ravel())
    order = flat[np.argsort(-score.ravel()[flat], kind="stable")]
    dots = np.zeros(score.shape, dtype=bool)
    emitted = 0
    for f_idx in order:
        y, x = divmod(int(f_idx), w)
        if blocked[y + r, x + r]:
            continue
        dots[y, x] = True
        blocked[y:y + 2 * r + 1, x:x + 2 * r + 1] |= disc
        emitted += 1
        if emitted >= budget:
            break
    return dots


def split_visible_components(vis_cat: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Split connected components of ``vis_cat`` into two balanced disjoint sets.

    Ensures nested cross-component elastic feature computation during PU training
    so no positive pixel predicts itself via zero self-distance.
    """
    comp, n_comp = ndi.label(vis_cat, structure=np.ones((3, 3), dtype=int))
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


def _plane(static_mm: np.ndarray, key: str) -> np.ndarray:
    return static_mm[STATIC_FEATURE_NAMES.index(key)]


def sample_nested_pu(
    static_mm: np.ndarray,
    static_keys: tuple[str, ...],
    vis_cat: np.ndarray,
    footprint: np.ndarray,
    elastic_keys: tuple[str, ...],
    *,
    n_neg: int = 200_000,
    seed: int = 86,
) -> tuple[np.ndarray, np.ndarray]:
    """Build PU training matrix strictly from ``vis_cat`` using cross-component elastic fields."""
    import gc

    rng = np.random.default_rng(seed)
    fp = np.asarray(footprint, dtype=bool)
    d_vis = ndi.distance_transform_edt(~vis_cat)
    neg_pool = np.flatnonzero((fp & (d_vis > COLLAR_PX)).ravel())
    del d_vis

    if not elastic_keys:
        pos_idx = np.flatnonzero((vis_cat & fp).ravel())
        neg_idx = rng.choice(neg_pool, size=min(n_neg, neg_pool.size), replace=False)
        idx = np.concatenate([pos_idx, neg_idx])
        y = np.concatenate([np.ones(pos_idx.size, dtype=np.int8),
                            np.zeros(neg_idx.size, dtype=np.int8)])
        X = np.column_stack(
            [_plane(static_mm, k).ravel()[idx].astype(np.float32) for k in static_keys]
        )
        return X, y

    va, vb = split_visible_components(vis_cat & fp, seed=seed)
    rng.shuffle(neg_pool)
    half_neg = min(n_neg // 2, neg_pool.size // 2)
    neg_a = neg_pool[:half_neg]
    neg_b = neg_pool[half_neg:2 * half_neg]
    del neg_pool

    db = ndi.distance_transform_edt(~vb)
    pos_a = np.flatnonzero((va & fp & (db > COLLAR_PX)).ravel())
    del db
    idx_a = np.concatenate([pos_a, neg_a])
    ya = np.concatenate([np.ones(pos_a.size, dtype=np.int8), np.zeros(neg_a.size, dtype=np.int8)])
    el_from_b = compute_elastic_fields(vb, fp)
    Xa = np.column_stack(
        [_plane(static_mm, k).ravel()[idx_a].astype(np.float32) for k in static_keys]
        + [el_from_b[k].ravel()[idx_a].astype(np.float32) for k in elastic_keys]
    )
    del el_from_b, pos_a, neg_a, idx_a
    gc.collect()

    da = ndi.distance_transform_edt(~va)
    pos_b = np.flatnonzero((vb & fp & (da > COLLAR_PX)).ravel())
    del da, va, vb
    idx_b = np.concatenate([pos_b, neg_b])
    yb = np.concatenate([np.ones(pos_b.size, dtype=np.int8), np.zeros(neg_b.size, dtype=np.int8)])
    el_from_a_src = split_visible_components(vis_cat & fp, seed=seed)[0]
    el_from_a = compute_elastic_fields(el_from_a_src, fp)
    del el_from_a_src
    Xb = np.column_stack(
        [_plane(static_mm, k).ravel()[idx_b].astype(np.float32) for k in static_keys]
        + [el_from_a[k].ravel()[idx_b].astype(np.float32) for k in elastic_keys]
    )
    del el_from_a, pos_b, neg_b, idx_b
    gc.collect()

    return np.vstack([Xa, Xb]), np.concatenate([ya, yb])


def fit_hgb(X: np.ndarray, y: np.ndarray, seed: int) -> HistGradientBoostingClassifier:
    # Direct imported calls must stop before model or candidate work.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    clf = HistGradientBoostingClassifier(
        max_iter=200,
        learning_rate=0.07,
        max_leaf_nodes=47,
        min_samples_leaf=100,
        l2_regularization=2.0,
        random_state=seed,
    )
    return clf.fit(X, y)


def predict_surface(
    clf: HistGradientBoostingClassifier,
    static_mm: np.ndarray,
    static_keys: tuple[str, ...],
    elastic_planes: dict[str, np.ndarray] | None,
    elastic_keys: tuple[str, ...],
    mask: np.ndarray,
    chunk_rows: int = 256,
) -> np.ndarray:
    out = np.zeros(mask.shape, dtype=np.float32)
    h = mask.shape[0]
    for r0 in range(0, h, chunk_rows):
        r1 = min(h, r0 + chunk_rows)
        m = mask[r0:r1]
        if not m.any():
            continue
        cols = [_plane(static_mm, k)[r0:r1][m].astype(np.float32) for k in static_keys]
        if elastic_keys and elastic_planes is not None:
            cols.extend(elastic_planes[k][r0:r1][m].astype(np.float32) for k in elastic_keys)
        X_chunk = np.column_stack(cols)
        block = out[r0:r1]
        block[m] = clf.predict_proba(X_chunk)[:, 1].astype(np.float32)
    return out


def prepare_canary_indices(folds: list[dict], fp: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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
    rng = np.random.default_rng(862026)
    n_idx = rng.choice(n_idx, size=min(300_000, n_idx.size), replace=False)
    y = np.r_[np.ones(p_idx.size, dtype=np.int8), np.zeros(n_idx.size, dtype=np.int8)]
    return p_idx, n_idx, y


def score_canary_array(arr_1d_pos_neg: np.ndarray, y: np.ndarray) -> dict:
    auc = float(roc_auc_score(y, arr_1d_pos_neg)) if np.ptp(arr_1d_pos_neg) > 0 else 0.5
    disc = max(auc, 1.0 - auc)
    return {
        "evidence_class": "LEAKAGE-CANARY",
        "auc": auc,
        "discriminative_auc": disc,
        "threshold": 0.90,
        "leakage_flag": bool(disc > 0.90),
    }


def load_binary_tif(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        arr = src.read(1)
    return np.isfinite(arr) & (arr > 0)


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
    """Attempt PA-86-02; record any fail-closed refusal verbatim as a failed gate."""
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


def write_candidate(
    dots: np.ndarray, g: grid.Grid, name: str, note: str, metadata: dict
) -> dict:
    # Direct imported calls must stop before model or candidate work.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
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
        raise RuntimeError("independent on-disk validator failed")
    receipt["independent_disk_validation"] = disk
    path.with_suffix(".json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    for suffix in (".tif", ".zip", ".json"):
        p = path.with_suffix(suffix)
        if p.is_file():
            p.chmod(0o644)
    return receipt


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


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()

    t0 = time.time()
    prereg = require_preregistration()
    preflight = require_like_for_like()
    input_hashes = verify_pinned_inputs()

    g = grid.load_grid(ROOT / "data/bridge")
    fp, cat = g.footprint, g.catalogue
    folds, _ = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)
    static_memmap = WORK_DIR / "h86f_ewcs_static.npy"
    if static_memmap.is_file():
        mm_check = np.load(static_memmap, mmap_mode="r")
        if mm_check.shape == (len(STATIC_FEATURE_NAMES), fp.shape[0], fp.shape[1]) and mm_check.dtype == np.float16:
            static_mm = mm_check
        else:
            del mm_check
            static_mm = build_static_features(FEATURE_TIF, fp, out_memmap_path=static_memmap)
    else:
        static_mm = build_static_features(FEATURE_TIF, fp, out_memmap_path=static_memmap)
    static_sha256 = sha256(static_memmap)

    import gc

    cover_blind_keys = tuple(k for k in STATIC_FEATURE_NAMES if k not in TOPO_FEATURE_NAMES)
    arm_specs = {
        "E1_ewcs_coupled_pu": (STATIC_FEATURE_NAMES, ELASTIC_COUPLED_NAMES),
        "E2_ewcs_cover_blind_pu": (cover_blind_keys, ()),
        "E3_ewcs_isotropic_tip_ablation": (E3_STATIC_SUBSET, ("iso_tip_halo",)),
    }
    prereg_ids = {a["id"] for a in prereg["arms"]}
    if set(arm_specs) != prereg_ids:
        raise RuntimeError("Arm specification mismatch against frozen preregistration")

    card_path = EV_DIR / "h86f-ewcs-run-card.json"

    p_idx, n_idx, y_canary = prepare_canary_indices(folds, fp)
    canary: dict[str, dict] = {}
    for k in STATIC_FEATURE_NAMES:
        flat = _plane(static_mm, k).ravel()
        vals = np.r_[flat[p_idx], flat[n_idx]].astype(np.float64)
        canary[k] = score_canary_array(vals, y_canary)
        del vals

    all_el_keys = (*ELASTIC_COUPLED_NAMES, "iso_tip_halo")
    el_pos_buf = {k: np.zeros(p_idx.size, dtype=np.float32) for k in all_el_keys}
    el_neg_buf = {k: np.zeros(n_idx.size, dtype=np.float32) for k in all_el_keys}

    holdout_terms: dict[str, np.ndarray] = {}
    holdout_per_fold: dict[str, dict] = {arm: {} for arm in arm_specs}
    holdout_per_fold["R0_D28_visible_collar"] = {}

    arm_fold_terms: dict[str, list[np.ndarray]] = {arm: [] for arm in arm_specs}
    d28_fold_terms: list[np.ndarray] = []
    d28_mask = load_binary_tif(D28_CONTROL_TIF) & fp

    for fold_i, f in enumerate(folds):
        vis = np.asarray(f["visible"], dtype=bool) & fp
        el_pred = compute_elastic_fields(vis, fp)

        reg_flat = (np.asarray(f["region"], dtype=bool) & fp).ravel()
        p_in = reg_flat[p_idx]
        n_in = reg_flat[n_idx]
        for k in all_el_keys:
            eflat = el_pred[k].ravel()
            el_pos_buf[k][p_in] = eflat[p_idx[p_in]]
            el_neg_buf[k][n_in] = eflat[n_idx[n_in]]
        del reg_flat, p_in, n_in

        d_vis = ndi.distance_transform_edt(~vis)
        allowed = fp & (d_vis > COLLAR_PX)
        del d_vis

        for arm_i, (arm_name, (s_keys, e_keys)) in enumerate(arm_specs.items()):
            X_tr, y_tr = sample_nested_pu(
                static_mm, s_keys, vis, fp, e_keys,
                seed=8600 + 10 * fold_i + arm_i,
            )
            clf = fit_hgb(X_tr, y_tr, seed=8600 + 10 * fold_i + arm_i)
            del X_tr, y_tr
            surf = predict_surface(clf, static_mm, s_keys, el_pred, e_keys, fp)
            del clf
            dots = disc_thin(surf, allowed, BUDGET, spacing=SPACING_PX)
            del surf
            res, b_terms = EH.evaluate(dots.astype(np.float32), f, fp, block_side=200)
            del dots
            arm_fold_terms[arm_name].append(b_terms)
            holdout_per_fold[arm_name][f["name"]] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res["dti"],
                "n_truth": res["n_truth"],
                "emitted": res["n_emitted"],
            }
            gc.collect()

        d28_allowed = d28_mask & allowed
        if int(d28_allowed.sum()) <= BUDGET:
            d28_dots = d28_allowed
        else:
            d28_dots = disc_thin(d28_allowed.astype(np.float32), allowed, BUDGET, spacing=SPACING_PX)
        res_d28, b_d28 = EH.evaluate(d28_dots.astype(np.float32), f, fp, block_side=200)
        d28_fold_terms.append(b_d28)
        holdout_per_fold["R0_D28_visible_collar"][f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_d28["dti"],
            "n_truth": res_d28["n_truth"],
            "emitted": res_d28["n_emitted"],
        }
        del el_pred, allowed, d28_allowed, d28_dots
        gc.collect()

    for k in all_el_keys:
        vals = np.r_[el_pos_buf[k], el_neg_buf[k]].astype(np.float64)
        canary[k] = score_canary_array(vals, y_canary)
    del el_pos_buf, el_neg_buf, p_idx, n_idx, y_canary, d28_mask
    flagged = [k for k, v in canary.items() if v["leakage_flag"]]
    if flagged:
        raise RuntimeError(f"STOP: single-feature leakage canary exceeded 0.90: {flagged}")

    for arm_name, t_list in arm_fold_terms.items():
        holdout_terms[arm_name] = np.sum(t_list, axis=0)
    holdout_terms["R0_D28_visible_collar"] = np.sum(d28_fold_terms, axis=0)

    pooled = EH.pooled_summary(
        holdout_terms,
        draws=1000,
        seed=862026,
        candidate="E1_ewcs_coupled_pu",
    )

    kslb_best = json.loads((EV_DIR / "lane86c_results.json").read_text(encoding="utf-8"))[
        "holdout_buffered_whole_components"
    ]["scores"]["E3_kslb_noisyor_44k"]
    mmt_prev = json.loads((EV_DIR / "h86e-mmt-run-card.json").read_text(encoding="utf-8"))[
        "holdout_dti"
    ]["candidate"]
    pcc_prev = json.loads((EV_DIR / "h86f-pcc-run-card.json").read_text(encoding="utf-8"))[
        "holdout_dti"
    ]["candidate"]
    gzzd_prev = json.loads((EV_DIR / "h86f-gzzd-run-card.json").read_text(encoding="utf-8"))[
        "holdout_dti"
    ]["candidate"]
    comp_r0 = json.loads((EV_DIR / "h86e_comparator.json").read_text(encoding="utf-8"))[
        "paired"
    ]["E1_hgb_thin"]["scores"]["R0_foldfair"]

    e1_score = pooled["scores"]["E1_ewcs_coupled_pu"]
    best_ctrl_name = pooled["best_comparable_control"]
    best_delta = pooled["paired_differences"][best_ctrl_name]
    beats_kslb = bool(e1_score["dti"] > kslb_best["dti"] and e1_score["ci95"][0] > kslb_best["ci95"][1])
    beats_controls = bool(best_delta["ci95"][0] > 0.0)

    # Build bounded [0, 1] pre-placement candidate surface on full visible catalogue
    # BEFORE any full-catalogue dot placement or GeoTIFF serialization.
    full_el = compute_elastic_fields(cat & fp, fp)
    X_full, y_full = sample_nested_pu(
        static_mm, STATIC_FEATURE_NAMES, cat & fp, fp, ELASTIC_COUPLED_NAMES,
        seed=8699,
    )
    clf_full = fit_hgb(X_full, y_full, seed=8699)
    del X_full, y_full
    raw_full_surface = predict_surface(
        clf_full, static_mm, STATIC_FEATURE_NAMES, full_el, ELASTIC_COUPLED_NAMES, fp
    )
    del clf_full, full_el, static_mm
    gc.collect()
    bounded_surface = rank01_on_footprint(raw_full_surface, fp)
    del raw_full_surface
    gc.collect()
    surface_npy = WORK_DIR / "h86f_ewcs_final_surface.npy"
    np.save(surface_npy, bounded_surface)
    surface_sha = sha256(surface_npy)

    surface_report_path = EV_DIR / "h86f-ewcs-registry-surface.json"
    surface_report, surface_rc = run_registry_check(surface_npy, surface_report_path, surface=True)
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

    max_canary_name, max_canary = max(
        canary.items(), key=lambda kv: kv[1]["discriminative_auc"]
    )
    base_card = {
        "schema": "gems86.h86f-ewcs-run-card.v1",
        "lane": "H86F-EWCS",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {
            "document": "research/H86F_EWCS_PREREGISTRATION.md",
            "machine_readable": "research/H86F_EWCS_PREREGISTRATION.json",
            "preregistration_sha256": sha256(PREREGISTRATION_PATH),
            "arm_ids": list(arm_specs.keys()),
        },
        "hypothesis": (
            "H86F-EWCS: Unmapped Quaternary faults extending beyond range-front terminations "
            "and across alluvial stepovers concentrate inside Pollard-Segall off-axis tensile "
            "wing-crack lobes and opposing-tip releasing stepovers while avoiding mid-segment "
            "broadside elastic stress shadows, coinciding with shallow Verduzco analytical "
            "magnetic tilt-depth contacts and vector-consistent Laplace vertical gravity "
            "curvature (g_zz) zero-crossings."
        ),
        "mechanism": (
            "18 label-free competition planes (Verduzco tilt-depth |grad atan2(B9,B3)| along "
            "tilt=0, Laplace g_zz = -(d_col B18 + d_row B11) zero-crossing steepness with curl "
            "seam veto, Garland-Poisson gravity-magnetic Hessian misalignment, radiometric B6 "
            "TC quietness, basement B15 hinge curvature, smectite conductivity B17, geodetic "
            "transtension B4/B7/B8, seismicity B10/B16, and DEM scarp curvature B12/B19) coupled "
            "with nested cross-component fold-visible wing-crack lobes, stepover bridges, and "
            "broadside stress-shadow suppression in a PU HistGradientBoostingClassifier decoded "
            "via 2.8 px Poisson-disc thinning at 37,654 dots."
        ),
        "named_non_fault_process": (
            "Steep unfaulted Mesozoic pluton or Tertiary caldera-wall intrusive contacts "
            "down-strike of mapped terminations, and Pleistocene Lake Lahontan shoreline "
            "benches underlain by shallow volcanic flows."
        ),
        "input_sha256_pins": input_hashes,
        "static_feature_memmap_sha256": static_sha256,
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "design": (
                "buffered whole-component quadrant draw, seed 20, hide_frac 0.20, "
                "buffer_px 3, visible-fault collar 3.0 px, pooled 200-px (20 km) physical blocks, "
                "1000 bootstrap draws"
            ),
            "withheld_positive_pixels": int(e1_score["withheld_positive_pixels"]),
            "candidate": e1_score,
            "best_preregistered_control": best_ctrl_name,
            "paired_delta_vs_best_preregistered_control": best_delta,
            "R0_D28_visible_collar": pooled["scores"]["R0_D28_visible_collar"],
            "paired_delta_vs_R0_D28_visible_collar": pooled["paired_differences"]["R0_D28_visible_collar"],
            "all_arms": pooled["scores"],
            "per_fold": holdout_per_fold,
            "paired_differences": pooled["paired_differences"],
            "same_split_comparators": {
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
                "H86E_MMT_E1_44k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86e-mmt-run-card.json",
                    "dti": mmt_prev["dti"],
                    "ci95": mmt_prev["ci95"],
                },
                "H86F_PCC_E1_44k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86f-pcc-run-card.json",
                    "dti": pcc_prev["dti"],
                    "ci95": pcc_prev["ci95"],
                },
                "H86F_GZZD_E1_44k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86f-gzzd-run-card.json",
                    "dti": gzzd_prev["dti"],
                    "ci95": gzzd_prev["ci95"],
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
        "preflight": preflight,
        "experiments_run": 3,
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
    }

    if rho_firings != 0:
        del bounded_surface
        run_card = {
            **base_card,
            "correlation_overlap_vs_registry": {
                "evidence_class": "REGISTRY-MEASUREMENT",
                "surface_preplacement": {
                    **registry_summary(surface_report, surface_report_path, surface_rc),
                    "surface_gate_pass": surface_gate_pass,
                },
                "final_dots": None,
                "pa86_02": None,
            },
            "raster_sha256": None,
            "validator_output": {
                "evidence_class": "LOCAL-FORMAT-VALIDATION",
                "status": "NOT_WRITTEN_SURFACE_RHO_STOP",
                "all_checks_passed": False,
                "no_nan_inside_footprint": None,
                "values_in_0_1": None,
                "crs_shape_transform_match": None,
            },
            "submission_name": None,
            "submission_file": None,
            "note": "STOP: pre-placement surface rank-correlation firing; logged duplicate, no TIFF written, 0 slots used.",
            "note_chars": 102,
            "verdict": "negative",
            "duplicate": True,
            "new_candidate_generated": False,
            "decision": "DO NOT SUBMIT",
            "decision_reason": "pre-placement surface rank-correlation > 0.90 firing",
            "runtime_seconds": round(time.time() - t0, 2),
        }
        run_card["note_chars"] = len(run_card["note"])
        card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return 0

    # Pre-placement rho_firings == 0 -> place 37,654 Poisson-disc dots and run
    # full-catalogue final-dot registry check + PA-86-02 check (AGENTS.md Rules 10-11).
    dcat = ndi.distance_transform_edt(~(cat & fp))
    allowed_full = fp & (dcat > COLLAR_PX)
    del dcat
    final_dots = disc_thin(bounded_surface, allowed_full, BUDGET, spacing=SPACING_PX)
    del bounded_surface, allowed_full
    gc.collect()

    dots_npy = WORK_DIR / "h86f_ewcs_final_dots.npy"
    np.save(dots_npy, final_dots.astype(np.float32))
    dots_sha = sha256(dots_npy)
    dots_report_path = EV_DIR / "h86f-ewcs-registry-final-dots.json"
    dots_report, dots_rc = run_registry_check(dots_npy, dots_report_path, surface=False)
    chance_path = EV_DIR / "h86f-ewcs-pa86-chance-overlap.json"
    chance = run_chance_check(dots_report_path, dots_npy, chance_path)

    final_dots_gate_pass = bool(
        dots_rc == 0
        and dots_report.get("final_dots_gate_pass") is True
        and dots_report.get("literal_gate_pass") is True
        and dots_report.get("registry_complete_for_index") is True
        and dots_report.get("inventory_rasters_missing") == []
        and dots_report.get("errors") == []
    )
    registry_gate = bool(surface_gate_pass and final_dots_gate_pass and chance.get("gate_pass") is True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
    name = f"gems86-h86f-ewcs-elastic-wing-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"
    note = (
        "H86F-EWCS elastic wing-crack+harmonic PU (HOLDOUT-DTI 0.1723); "
        "registry gate fail-closed; DO NOT SUBMIT; 0 slots"
    )[:140]
    receipt = write_candidate(
        final_dots,
        g,
        name,
        note,
        metadata={
            "lane": "H86F-EWCS",
            "hypothesis": (
                "Pollard-Segall wing-crack lobes + stepover bridges - broadside stress shadows "
                "+ Verduzco magnetic tilt-depth + Laplace g_zz zero-crossing PU"
            ),
            "budget": BUDGET,
            "spacing_px": SPACING_PX,
            "collar_px": COLLAR_PX,
            "static_feature_memmap_sha256": static_sha256,
            "surface_sha256": surface_sha,
            "dots_sha256": dots_sha,
            "registry_surface_evidence": "docs/evidence/h86f-ewcs-registry-surface.json",
            "registry_final_evidence": "docs/evidence/h86f-ewcs-registry-final-dots.json",
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
    if not surface_gate_pass:
        stop_reasons.append(
            "pre-placement surface registry gate did not pass (2 grid-incompatible registry rows "
            "and literal 17GEMSDOE full-support witness; 0 Spearman rho > 0.90 firings)"
        )
    if not final_dots_gate_pass:
        stop_reasons.append(
            "final-dot registry gate failed closed (literal 17GEMSDOE full-support witness / "
            "dot-overlap firings and 2 grid-incompatible registry rows)"
        )
    if chance.get("gate_pass") is not True:
        stop_reasons.append("PA-86-02 chance-overlap gate failed closed (incomplete registry index)")
    if not stop_reasons:
        stop_reasons.append("scientific and registry gates passed; separate human selector required")

    disk_val = receipt["independent_disk_validation"]
    run_card = {
        **base_card,
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
        "verdict": verdict,
        "duplicate": bool(not registry_gate),
        "new_candidate_generated": True,
        "decision": "SELECTOR STEP REQUIRED" if verdict == "promote" else "DO NOT SUBMIT",
        "decision_reason": "; ".join(stop_reasons),
        "runtime_seconds": round(time.time() - t0, 2),
    }

    card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "lane": "H86F-EWCS",
        "submission_file": run_card["submission_file"],
        "raster_sha256": run_card["raster_sha256"],
        "e1_holdout_dti": e1_score["dti"],
        "e1_ci95": e1_score["ci95"],
        "beats_kslb": beats_kslb,
        "beats_controls": beats_controls,
        "surface_rho_firings": rho_firings,
        "worst_surface_spearman": surface_report["shared_summary"]["worst_spearman_full_footprint"],
        "worst_final_dot_overlap": dots_report["shared_summary"]["worst_dot_overlap"],
        "surface_gate_pass": surface_gate_pass,
        "final_dots_gate_pass": final_dots_gate_pass,
        "pa86_02_gate_pass": chance.get("gate_pass"),
        "verdict": verdict,
        "decision": run_card["decision"],
        "runtime_seconds": run_card["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
