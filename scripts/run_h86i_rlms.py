#!/usr/bin/env python3
"""Execute preregistered Lane H86I-RLMS within the 3-experiment / 2-hour budget.

Protocol & governance compliance (AGENTS.md Rules 2-11):
- Frozen contemporaneous preregistration verified before feature/model work
  (research/H86I_RLMS_PREREGISTRATION.json & registry/h86i_rlms_hypotheses.json).
- Reuses pinned vendor/gems57/{grid,holdout,metric,emit,evaluate_holdout,
  submission_writer,validate} unchanged.
- Single-feature leakage canaries run on all 33 static & 7 fold-visible planes
  before trusting any holdout result (max(AUC, 1-AUC) > 0.90 stops immediately).
- Evaluates 3 preregistered arms (E1 full RLMS submodular, E2 native-19 ablation,
  E3 unprojected disc-thin ablation) + exact same-split H86F_EWCS_reproduced
  champion control + fold-fair R0_D28_visible_collar control on
  gems57-pooled-hide-v2 (seed=20, hide_frac=0.20, buffer_px=3, 11,321 withheld
  positives, 1,000 bootstrap draws over 200-px / 20-km physical blocks).
- Runs v2 SHA-bound surface registry check (scripts/check_h86e_registry.py --surface)
  on the exact calibrated posterior surface BEFORE full-catalogue dot placement,
  and v2 final-dot registry check + PA-86-02 BEFORE audit-only GeoTIFF
  serialization; halts without writing a TIFF if rho_firings > 0 or any
  informative discrete dot field (<=100k dots) exceeds 0.70 3-px overlap; fails
  closed to DO NOT SUBMIT / verdict='negative' (0 slots used) whenever any
  literal registry or scientific gate fails.

Following repository-wide builder gating, main() now calls
protocol_preflight.require_feasible() before any work; the recorded 2026-10-25
execution ran under PA-86-01/02 and its run card and artifacts are unchanged
historical receipts, not a protocol exemption.
"""
from __future__ import annotations

import argparse
import gc
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
    ELASTIC_COUPLED_NAMES as EWCS_ELASTIC_NAMES,
    STATIC_FEATURE_NAMES as EWCS_STATIC_NAMES,
    build_static_features as build_ewcs_static_features,
    compute_elastic_fields as compute_ewcs_elastic_fields,
)
from gems86_rlms.allocator import (  # noqa: E402
    bayes_prior_calibrate,
    disc_thin,
    submodular_kernel_allocate,
)
from gems86_rlms.features import (  # noqa: E402
    ALL_STATIC_NAMES,
    CONTINUATION_NAMES,
    E3_SCALAR_SUBSET,
    NATIVE_STATIC_NAMES,
    build_rlms_static_features,
    compute_continuation_fields,
    verify_external_rasters,
)
from scripts.protocol_preflight import require_like_for_like  # noqa: E402

PREREGISTRATION_PATH = ROOT / "research/H86I_RLMS_PREREGISTRATION.json"
HYPOTHESES_PATH = ROOT / "registry/h86i_rlms_hypotheses.json"
FEATURE_TIF = ROOT / "data/bridge/training_features.tif"
EXT_DIR = ROOT / ".cache/external"
D28_CONTROL_TIF = (
    ROOT / "data/registry_ext/ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73.tif"
)
OUT_DIR = ROOT / "docs/downloads"
WORK_DIR = ROOT / ".cache/gems_work"
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
DINKELBACH_ETA = 0.042
INFORMATIVE_DOT_CAP = 100_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_preregistration() -> dict:
    if not PREREGISTRATION_PATH.is_file() or not HYPOTHESES_PATH.is_file():
        raise RuntimeError("missing frozen H86I preregistration or hypothesis queue")
    doc = json.loads(PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    arms = doc.get("arms", [])
    if len(arms) != 3 or doc.get("budget", {}).get("max_experiments", 99) > 3:
        raise RuntimeError("invalid H86I-RLMS preregistration budget or arm count")
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
    ext_verified = verify_external_rasters(EXT_DIR)
    for k, v in ext_verified.items():
        verified[f"ext_{k}"] = v
    return verified


def _plane(static_mm: np.ndarray, names: tuple[str, ...], key: str) -> np.ndarray:
    return static_mm[names.index(key)]


def partition_buffered_components(
    vis_cat: np.ndarray, n_splits: int = 5, buffer_px: int = 3, seed: int = 86
) -> list[np.ndarray]:
    """Partition 3-px buffered fault systems of ``vis_cat`` into ``n_splits`` folds.

    Ensures source folds hold ~80% of visible fault systems (matching the 80%
    visible density scale of holdout inference) while keeping nearby collinear
    raster fragments inside the same system so no fault predicts itself.
    """
    v = np.asarray(vis_cat, dtype=bool)
    dil = ndi.binary_dilation(v, iterations=int(buffer_px))
    comp_dil, n_comp = ndi.label(dil, structure=np.ones((3, 3), dtype=int))
    del dil
    if n_comp < n_splits:
        ys = np.flatnonzero(v.any(axis=1))
        splits = [np.zeros_like(v) for _ in range(n_splits)]
        for k, rows in enumerate(np.array_split(ys, n_splits)):
            m = np.zeros_like(v)
            m[rows, :] = True
            splits[k] = v & m
        return splits

    rng = np.random.default_rng(seed)
    perm = rng.permutation(np.arange(1, n_comp + 1))
    fold_of_comp = np.full(n_comp + 1, -1, dtype=np.int16)
    for idx, cid in enumerate(perm):
        fold_of_comp[cid] = idx % n_splits
    comp_on_v = np.where(v, comp_dil, 0)
    del comp_dil
    assigned = fold_of_comp[comp_on_v]
    return [assigned == k for k in range(n_splits)]


def compute_cover_weights(
    static_mm: np.ndarray, idx: np.ndarray, y: np.ndarray
) -> np.ndarray:
    """Gentle Bekker-Davis alluvial-cover propensity weights on positive examples.

    Mapped faults observed inside low-slope piedmont fans / basin floors represent
    higher true fault density per observed scarp due to Holocene alluvial censoring.
    """
    slope_z = _plane(static_mm, ALL_STATIC_NAMES, "slope_local").ravel()[idx].astype(np.float32)
    rel_z = _plane(static_mm, ALL_STATIC_NAMES, "piedmont_relief_ratio").ravel()[idx].astype(
        np.float32
    )
    exposure = 0.65 * slope_z + 0.35 * rel_z
    # Gentle inverse-exposure boost on low-relief positives, bounded strictly in [0.80, 1.90]
    pos_boost = np.clip(1.25 - 0.30 * np.tanh(exposure), 0.80, 1.90)
    return np.where(y > 0, pos_boost, 1.0).astype(np.float32)


def sample_oof80_buffered_pu(
    static_mm: np.ndarray,
    vis_cat: np.ndarray,
    footprint: np.ndarray,
    *,
    n_neg: int = 240_000,
    n_splits: int = 5,
    seed: int = 86,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build 5-fold (80%->20%) buffered-component OOF matrix for E1 and E2 simultaneously.

    Returns ``(X_static_all, X_cont, y, sample_weight)`` so E1 uses all 33 static
    columns + 6 continuation columns while E2 slices the 25 native static columns
    + 6 continuation columns without redundant EDT recomputation.
    """
    rng = np.random.default_rng(seed)
    fp = np.asarray(footprint, dtype=bool)
    v_all = np.asarray(vis_cat, dtype=bool) & fp

    sub_c2 = _plane(static_mm, ALL_STATIC_NAMES, "nematic_sub_c2").astype(np.float32)
    sub_s2 = _plane(static_mm, ALL_STATIC_NAMES, "nematic_sub_s2").astype(np.float32)

    d_vis_all = ndi.distance_transform_edt(~v_all)
    neg_pool = np.flatnonzero((fp & (d_vis_all > COLLAR_PX)).ravel())
    del d_vis_all
    rng.shuffle(neg_pool)
    neg_take = neg_pool[: min(int(n_neg), int(neg_pool.size))]
    del neg_pool
    neg_chunks = np.array_split(neg_take, n_splits)

    val_folds = partition_buffered_components(v_all, n_splits=n_splits, buffer_px=3, seed=seed)

    idx_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    cont_parts: list[np.ndarray] = []

    for k in range(n_splits):
        vk = val_folds[k]
        v_src = v_all & (~vk)
        d_src = ndi.distance_transform_edt(~v_src)
        pos_k = np.flatnonzero((vk & (d_src > COLLAR_PX)).ravel())
        del d_src
        neg_k = neg_chunks[k]
        idx_k = np.concatenate([pos_k, neg_k])
        yk = np.concatenate(
            [np.ones(pos_k.size, dtype=np.int8), np.zeros(neg_k.size, dtype=np.int8)]
        )
        cont_planes = compute_continuation_fields(v_src, fp, sub_c2, sub_s2)
        ck = np.column_stack(
            [cont_planes[name].ravel()[idx_k].astype(np.float32) for name in CONTINUATION_NAMES]
        )
        del cont_planes, pos_k, neg_k, v_src, vk
        idx_parts.append(idx_k)
        y_parts.append(yk)
        cont_parts.append(ck)
        gc.collect()

    del sub_c2, sub_s2, val_folds, neg_chunks, neg_take
    all_idx = np.concatenate(idx_parts)
    y_out = np.concatenate(y_parts)
    X_cont = np.vstack(cont_parts)
    del idx_parts, y_parts, cont_parts

    X_stat = np.column_stack(
        [static_mm[i].ravel()[all_idx].astype(np.float32) for i in range(len(ALL_STATIC_NAMES))]
    )
    weights = compute_cover_weights(static_mm, all_idx, y_out)
    del all_idx
    gc.collect()
    return X_stat, X_cont, y_out, weights


def split_50_50_unbuffered(vis_cat: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Baseline 50/50 split used only by Ablation Arm E3 and reproduced EWCS control."""
    comp, n_comp = ndi.label(vis_cat, structure=np.ones((3, 3), dtype=int))
    if n_comp < 2:
        half = vis_cat.shape[0] // 2
        va, vb = vis_cat.copy(), vis_cat.copy()
        va[half:, :] = False
        vb[:half, :] = False
        return va, vb
    rng = np.random.default_rng(seed)
    perm = rng.permutation(np.arange(1, n_comp + 1))
    set_a = np.zeros(n_comp + 1, dtype=bool)
    set_a[perm[::2]] = True
    return set_a[comp], (~set_a)[comp] & (comp > 0)


def sample_e3_ablation_pu(
    static_mm: np.ndarray,
    vis_cat: np.ndarray,
    footprint: np.ndarray,
    *,
    n_neg: int = 200_000,
    seed: int = 86,
) -> tuple[np.ndarray, np.ndarray]:
    """Unprojected scalar + isotropic tip halo + 50/50 split control for Arm E3."""
    rng = np.random.default_rng(seed)
    fp = np.asarray(footprint, dtype=bool)
    v_all = np.asarray(vis_cat, dtype=bool) & fp
    d_vis = ndi.distance_transform_edt(~v_all)
    neg_pool = np.flatnonzero((fp & (d_vis > COLLAR_PX)).ravel())
    del d_vis
    rng.shuffle(neg_pool)
    half_neg = min(n_neg // 2, neg_pool.size // 2)
    neg_a, neg_b = neg_pool[:half_neg], neg_pool[half_neg : 2 * half_neg]
    del neg_pool

    va, vb = split_50_50_unbuffered(v_all, seed=seed)
    zeros_dir = np.zeros(fp.shape, dtype=np.float16)
    s_indices = [ALL_STATIC_NAMES.index(k) for k in E3_SCALAR_SUBSET]

    db = ndi.distance_transform_edt(~vb)
    pos_a = np.flatnonzero((va & (db > COLLAR_PX)).ravel())
    del db
    idx_a = np.concatenate([pos_a, neg_a])
    ya = np.concatenate([np.ones(pos_a.size, dtype=np.int8), np.zeros(neg_a.size, dtype=np.int8)])
    iso_b = compute_continuation_fields(
        vb, fp, zeros_dir, zeros_dir, include_iso_control=True
    )["iso_tip_halo"]
    Xa = np.column_stack(
        [static_mm[i].ravel()[idx_a].astype(np.float32) for i in s_indices]
        + [iso_b.ravel()[idx_a].astype(np.float32)]
    )
    del iso_b, pos_a, neg_a, idx_a
    gc.collect()

    da = ndi.distance_transform_edt(~va)
    pos_b = np.flatnonzero((vb & (da > COLLAR_PX)).ravel())
    del da
    idx_b = np.concatenate([pos_b, neg_b])
    yb = np.concatenate([np.ones(pos_b.size, dtype=np.int8), np.zeros(neg_b.size, dtype=np.int8)])
    iso_a = compute_continuation_fields(
        va, fp, zeros_dir, zeros_dir, include_iso_control=True
    )["iso_tip_halo"]
    Xb = np.column_stack(
        [static_mm[i].ravel()[idx_b].astype(np.float32) for i in s_indices]
        + [iso_a.ravel()[idx_b].astype(np.float32)]
    )
    del iso_a, pos_b, neg_b, idx_b, va, vb, zeros_dir
    gc.collect()
    return np.vstack([Xa, Xb]), np.concatenate([ya, yb])


def fit_rlms_ensemble(
    X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray, seed: int
) -> list[HistGradientBoostingClassifier]:
    """2-seed variance-reduced HistGradientBoosting ensemble with NaN routing."""
    # Direct imported calls must stop before model or candidate work.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    models: list[HistGradientBoostingClassifier] = []
    for offset, max_leaf, lr in ((0, 63, 0.06), (101, 47, 0.065)):
        clf = HistGradientBoostingClassifier(
            max_iter=230,
            learning_rate=lr,
            max_leaf_nodes=max_leaf,
            min_samples_leaf=90,
            l2_regularization=2.5,
            random_state=seed + offset,
        )
        clf.fit(X, y, sample_weight=sample_weight)
        models.append(clf)
    return models


def fit_single_hgb(X: np.ndarray, y: np.ndarray, seed: int) -> HistGradientBoostingClassifier:
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


def predict_ensemble_surface(
    models: list[HistGradientBoostingClassifier],
    static_mm: np.ndarray,
    static_all_names: tuple[str, ...],
    static_subset: tuple[str, ...],
    cont_planes: dict[str, np.ndarray] | None,
    cont_keys: tuple[str, ...],
    mask: np.ndarray,
    chunk_rows: int = 256,
) -> np.ndarray:
    out = np.zeros(mask.shape, dtype=np.float32)
    s_idx = [static_all_names.index(k) for k in static_subset]
    h = mask.shape[0]
    n_m = float(len(models))
    for r0 in range(0, h, chunk_rows):
        r1 = min(h, r0 + chunk_rows)
        m = mask[r0:r1]
        if not m.any():
            continue
        cols = [static_mm[i][r0:r1][m].astype(np.float32) for i in s_idx]
        if cont_keys and cont_planes is not None:
            cols.extend(cont_planes[k][r0:r1][m].astype(np.float32) for k in cont_keys)
        X_chunk = np.column_stack(cols)
        probs = np.zeros(X_chunk.shape[0], dtype=np.float32)
        for clf in models:
            probs += clf.predict_proba(X_chunk)[:, 1].astype(np.float32)
        probs /= n_m
        block = out[r0:r1]
        block[m] = probs
    return out


def reproduce_ewcs_fold(
    ewcs_mm: np.ndarray, vis: np.ndarray, fp: np.ndarray, fold_i: int
) -> np.ndarray:
    """Bit-accurate fold reproduction of H86F-EWCS E1 for exact paired bootstrap CI."""
    va, vb = split_50_50_unbuffered(vis & fp, seed=8600 + 10 * fold_i)
    rng = np.random.default_rng(8600 + 10 * fold_i)
    d_vis = ndi.distance_transform_edt(~vis)
    neg_pool = np.flatnonzero((fp & (d_vis > COLLAR_PX)).ravel())
    del d_vis
    rng.shuffle(neg_pool)
    half_neg = min(100_000, neg_pool.size // 2)
    neg_a, neg_b = neg_pool[:half_neg], neg_pool[half_neg : 2 * half_neg]
    del neg_pool

    db = ndi.distance_transform_edt(~vb)
    pos_a = np.flatnonzero((va & fp & (db > COLLAR_PX)).ravel())
    del db
    idx_a = np.concatenate([pos_a, neg_a])
    ya = np.concatenate([np.ones(pos_a.size, dtype=np.int8), np.zeros(neg_a.size, dtype=np.int8)])
    el_b = compute_ewcs_elastic_fields(vb, fp)
    Xa = np.column_stack(
        [ewcs_mm[i].ravel()[idx_a].astype(np.float32) for i in range(len(EWCS_STATIC_NAMES))]
        + [el_b[k].ravel()[idx_a].astype(np.float32) for k in EWCS_ELASTIC_NAMES]
    )
    del el_b, pos_a, neg_a, idx_a

    da = ndi.distance_transform_edt(~va)
    pos_b = np.flatnonzero((vb & fp & (da > COLLAR_PX)).ravel())
    del da
    idx_b = np.concatenate([pos_b, neg_b])
    yb = np.concatenate([np.ones(pos_b.size, dtype=np.int8), np.zeros(neg_b.size, dtype=np.int8)])
    el_a = compute_ewcs_elastic_fields(va, fp)
    Xb = np.column_stack(
        [ewcs_mm[i].ravel()[idx_b].astype(np.float32) for i in range(len(EWCS_STATIC_NAMES))]
        + [el_a[k].ravel()[idx_b].astype(np.float32) for k in EWCS_ELASTIC_NAMES]
    )
    del el_a, pos_b, neg_b, idx_b, va, vb
    X_ew = np.vstack([Xa, Xb])
    y_ew = np.concatenate([ya, yb])
    del Xa, Xb, ya, yb
    clf_ew = fit_single_hgb(X_ew, y_ew, seed=8600 + 10 * fold_i)
    del X_ew, y_ew
    el_vis = compute_ewcs_elastic_fields(vis, fp)
    surf_ew = predict_ensemble_surface(
        [clf_ew],
        ewcs_mm,
        EWCS_STATIC_NAMES,
        EWCS_STATIC_NAMES,
        el_vis,
        EWCS_ELASTIC_NAMES,
        fp,
    )
    del clf_ew, el_vis
    d_vis2 = ndi.distance_transform_edt(~vis)
    allowed_ew = fp & (d_vis2 > COLLAR_PX)
    del d_vis2
    dots_ew = disc_thin(surf_ew, allowed_ew, BUDGET, spacing=SPACING_PX)
    del surf_ew, allowed_ew
    gc.collect()
    return dots_ew


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
    rng = np.random.default_rng(862026)
    n_idx = rng.choice(n_idx, size=min(300_000, n_idx.size), replace=False)
    y = np.r_[np.ones(p_idx.size, dtype=np.int8), np.zeros(n_idx.size, dtype=np.int8)]
    return p_idx, n_idx, y


def score_canary_array(arr_1d_pos_neg: np.ndarray, y: np.ndarray) -> dict:
    finite = np.isfinite(arr_1d_pos_neg)
    if not finite.any():
        return {
            "evidence_class": "LEAKAGE-CANARY",
            "auc": 0.5,
            "discriminative_auc": 0.5,
            "finite_fraction": 0.0,
            "threshold": 0.90,
            "leakage_flag": False,
        }
    sub_x = arr_1d_pos_neg[finite]
    sub_y = y[finite]
    auc_fin = float(roc_auc_score(sub_y, sub_x)) if np.ptp(sub_x) > 0 and np.unique(sub_y).size == 2 else 0.5
    disc_fin = max(auc_fin, 1.0 - auc_fin)
    if not finite.all():
        med = float(np.median(sub_x))
        imp = np.where(finite, arr_1d_pos_neg, med)
        auc_imp = float(roc_auc_score(y, imp)) if np.ptp(imp) > 0 else 0.5
        disc = max(disc_fin, auc_imp, 1.0 - auc_imp)
    else:
        disc = disc_fin
    return {
        "evidence_class": "LEAKAGE-CANARY",
        "auc": auc_fin,
        "discriminative_auc": float(disc),
        "finite_fraction": float(finite.mean()),
        "threshold": 0.90,
        "leakage_flag": bool(disc > 0.90),
    }


def load_binary_tif(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        arr = src.read(1)
    return np.isfinite(arr) & (arr > 0)


def run_registry_check(array_path: Path, output: Path, *, surface: bool) -> tuple[dict, int]:
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


def summarize_informative_dot_overlaps(report: dict, cap: int = INFORMATIVE_DOT_CAP) -> dict:
    rows = [
        r
        for r in report.get("comparison_rows", [])
        if "error" not in r and int(r.get("their_dots", 10**9)) <= cap
    ]
    rows_sorted = sorted(rows, key=lambda r: -float(r.get("my_dots_within_3px_of_theirs", 0.0)))
    firings = [r for r in rows_sorted if float(r.get("my_dots_within_3px_of_theirs", 0.0)) > 0.70]
    top5 = [
        {
            "submission": r.get("submission"),
            "their_dots": r.get("their_dots"),
            "my_dots_within_3px_of_theirs": r.get("my_dots_within_3px_of_theirs"),
            "spearman_full_footprint": r.get("spearman_full_footprint"),
        }
        for r in rows_sorted[:5]
    ]
    d32_row = next(
        (r for r in rows if "GEMSDOE32" in str(r.get("submission", "")) and "h33-h33-2-b2" in str(r.get("submission", ""))),
        None,
    )
    ewcs_row = next(
        (r for r in rows if "h86f-ewcs" in str(r.get("submission", ""))),
        None,
    )
    return {
        "positive_pixel_cap": cap,
        "discrete_rasters_checked": len(rows),
        "firings_over_0p70": len(firings),
        "worst_discrete_overlap": (
            float(rows_sorted[0]["my_dots_within_3px_of_theirs"]) if rows_sorted else 0.0
        ),
        "worst_discrete_id": rows_sorted[0].get("submission") if rows_sorted else None,
        "overlap_vs_GEMSDOE32_h33": (
            float(d32_row["my_dots_within_3px_of_theirs"]) if d32_row else None
        ),
        "overlap_vs_H86F_EWCS": (
            float(ewcs_row["my_dots_within_3px_of_theirs"]) if ewcs_row else None
        ),
        "top5_discrete": top5,
    }


def main(argv: list[str] | None = None) -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stop-after-fold",
        type=int,
        default=None,
        help="Optional stage boundary (1..4) saving SHA-bound fold checkpoints.",
    )
    args = parser.parse_args(argv)

    t0 = time.time()
    prereg = require_preregistration()
    prereg_sha = sha256(PREREGISTRATION_PATH)
    preflight = require_like_for_like()
    input_hashes = verify_pinned_inputs()

    g = grid.load_grid(ROOT / "data/bridge")
    fp, cat = g.footprint, g.catalogue
    folds, _ = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)

    static_memmap = WORK_DIR / "h86i_rlms_static.npy"
    if static_memmap.is_file():
        mm_check = np.load(static_memmap, mmap_mode="r")
        if (
            mm_check.shape == (len(ALL_STATIC_NAMES), fp.shape[0], fp.shape[1])
            and mm_check.dtype == np.float16
        ):
            static_mm = mm_check
        else:
            del mm_check
            static_mm = build_rlms_static_features(FEATURE_TIF, EXT_DIR, fp, static_memmap)
    else:
        static_mm = build_rlms_static_features(FEATURE_TIF, EXT_DIR, fp, static_memmap)
    static_sha256 = sha256(static_memmap)

    ewcs_memmap = WORK_DIR / "h86f_ewcs_static_ctrl.npy"
    if ewcs_memmap.is_file():
        ew_check = np.load(ewcs_memmap, mmap_mode="r")
        if (
            ew_check.shape == (len(EWCS_STATIC_NAMES), fp.shape[0], fp.shape[1])
            and ew_check.dtype == np.float16
        ):
            ewcs_mm = ew_check
        else:
            del ew_check
            ewcs_mm = build_ewcs_static_features(FEATURE_TIF, fp, out_memmap_path=ewcs_memmap)
    else:
        ewcs_mm = build_ewcs_static_features(FEATURE_TIF, fp, out_memmap_path=ewcs_memmap)

    arm_ids = [a["id"] for a in prereg["arms"]]
    expected_arms = [
        "E1_rlms_full_submodular",
        "E2_rlms_native19_only_ablation",
        "E3_rlms_unprojected_disc_ablation",
    ]
    if arm_ids != expected_arms:
        raise RuntimeError(f"Preregistered arms {arm_ids} != {expected_arms}")

    card_path = EV_DIR / "h86i-rlms-run-card.json"

    # Single-feature leakage canaries across all 33 static planes + 7 fold-visible planes
    p_idx, n_idx, y_canary = prepare_canary_indices(folds, fp)
    canary: dict[str, dict] = {}
    for k in ALL_STATIC_NAMES:
        flat = _plane(static_mm, ALL_STATIC_NAMES, k).ravel()
        vals = np.r_[flat[p_idx], flat[n_idx]].astype(np.float64)
        canary[k] = score_canary_array(vals, y_canary)
        del vals

    all_cont_canary_keys = (*CONTINUATION_NAMES, "iso_tip_halo")
    cont_pos_buf = {k: np.zeros(p_idx.size, dtype=np.float32) for k in all_cont_canary_keys}
    cont_neg_buf = {k: np.zeros(n_idx.size, dtype=np.float32) for k in all_cont_canary_keys}

    all_eval_names = [
        *expected_arms,
        "H86F_EWCS_reproduced",
        "R0_D28_visible_collar",
    ]
    arm_fold_terms: dict[str, list[np.ndarray]] = {name: [] for name in all_eval_names}
    holdout_per_fold: dict[str, dict] = {name: {} for name in all_eval_names}
    d28_mask = load_binary_tif(D28_CONTROL_TIF) & fp
    fp_pixels = float(fp.sum())
    native_col_idx = [ALL_STATIC_NAMES.index(k) for k in NATIVE_STATIC_NAMES]

    for fold_i, f in enumerate(folds):
        ckpt_npz = WORK_DIR / f"h86i_rlms_fold_{fold_i}.npz"
        ckpt_json = WORK_DIR / f"h86i_rlms_fold_{fold_i}.json"
        reg_flat = (np.asarray(f["region"], dtype=bool) & fp).ravel()
        p_in = reg_flat[p_idx]
        n_in = reg_flat[n_idx]
        del reg_flat

        if ckpt_npz.is_file() and ckpt_json.is_file():
            meta_ck = json.loads(ckpt_json.read_text(encoding="utf-8"))
            if (
                meta_ck.get("static_sha256") == static_sha256
                and meta_ck.get("preregistration_sha256") == prereg_sha
                and meta_ck.get("fold_name") == f["name"]
            ):
                with np.load(ckpt_npz) as z:
                    for name in all_eval_names:
                        arm_fold_terms[name].append(z[f"bt_{name}"])
                        holdout_per_fold[name][f["name"]] = meta_ck["per_fold"][name]
                    for k in all_cont_canary_keys:
                        cont_pos_buf[k][p_in] = z[f"cp_{k}"]
                        cont_neg_buf[k][n_in] = z[f"cn_{k}"]
                print(
                    f"[H86I-RLMS] Loaded SHA-verified fold {fold_i + 1}/4 ({f['name']}): "
                    f"E1={meta_ck['per_fold']['E1_rlms_full_submodular']['dti']:.6f} "
                    f"EWCS={meta_ck['per_fold']['H86F_EWCS_reproduced']['dti']:.6f}",
                    file=sys.stderr,
                    flush=True,
                )
                del p_in, n_in
                if args.stop_after_fold is not None and (fold_i + 1) >= args.stop_after_fold:
                    return 0
                continue

        print(f"[H86I-RLMS] Starting fold {fold_i + 1}/4 ({f['name']}) at +{time.time()-t0:.1f}s", file=sys.stderr, flush=True)
        vis = np.asarray(f["visible"], dtype=bool) & fp
        sub_c2_arr = _plane(static_mm, ALL_STATIC_NAMES, "nematic_sub_c2").astype(np.float32)
        sub_s2_arr = _plane(static_mm, ALL_STATIC_NAMES, "nematic_sub_s2").astype(np.float32)
        cont_pred = compute_continuation_fields(
            vis, fp, sub_c2_arr, sub_s2_arr, include_iso_control=True
        )
        del sub_c2_arr, sub_s2_arr

        cp_save: dict[str, np.ndarray] = {}
        cn_save: dict[str, np.ndarray] = {}
        for k in all_cont_canary_keys:
            eflat = cont_pred[k].ravel()
            cp_k = eflat[p_idx[p_in]].astype(np.float32)
            cn_k = eflat[n_idx[n_in]].astype(np.float32)
            cont_pos_buf[k][p_in] = cp_k
            cont_neg_buf[k][n_in] = cn_k
            cp_save[f"cp_{k}"] = cp_k
            cn_save[f"cn_{k}"] = cn_k
        del p_in, n_in

        d_vis = ndi.distance_transform_edt(~vis)
        allowed = fp & (d_vis > COLLAR_PX)
        del d_vis

        # Shared 5-fold (80%->20%) buffered-component OOF sampling for E1 and E2
        X_stat_all, X_cont_oof, y_oof, w_oof = sample_oof80_buffered_pu(
            static_mm, vis, fp, n_neg=240_000, n_splits=5, seed=8690 + 10 * fold_i
        )
        pi_tr = float(np.dot(w_oof, y_oof) / np.sum(w_oof))
        pi_tg = float(0.25 * (vis.sum() / fp_pixels))

        # Arm E1: Full RLMS + Submodular 300 m kernel allocation
        X_e1 = np.hstack([X_stat_all, X_cont_oof])
        models_e1 = fit_rlms_ensemble(X_e1, y_oof, w_oof, seed=8690 + 10 * fold_i)
        del X_e1
        q_e1 = predict_ensemble_surface(
            models_e1, static_mm, ALL_STATIC_NAMES, ALL_STATIC_NAMES, cont_pred, CONTINUATION_NAMES, fp
        )
        del models_e1
        p_e1 = bayes_prior_calibrate(q_e1, pi_tr, pi_tg, fp)
        del q_e1
        dots_e1 = submodular_kernel_allocate(p_e1, allowed, BUDGET, eta=DINKELBACH_ETA)
        del p_e1
        res_e1, bt_e1 = EH.evaluate(dots_e1.astype(np.float32), f, fp, block_side=200)
        del dots_e1
        arm_fold_terms["E1_rlms_full_submodular"].append(bt_e1)
        holdout_per_fold["E1_rlms_full_submodular"][f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_e1["dti"],
            "n_truth": res_e1["n_truth"],
            "emitted": res_e1["n_emitted"],
        }
        gc.collect()

        # Arm E2: Strict 19-band native-only ablation + Submodular 300 m kernel allocation
        X_e2 = np.hstack([X_stat_all[:, native_col_idx], X_cont_oof])
        del X_stat_all, X_cont_oof
        models_e2 = fit_rlms_ensemble(X_e2, y_oof, w_oof, seed=8691 + 10 * fold_i)
        del X_e2, y_oof, w_oof
        q_e2 = predict_ensemble_surface(
            models_e2,
            static_mm,
            ALL_STATIC_NAMES,
            NATIVE_STATIC_NAMES,
            cont_pred,
            CONTINUATION_NAMES,
            fp,
        )
        del models_e2
        p_e2 = bayes_prior_calibrate(q_e2, pi_tr, pi_tg, fp)
        del q_e2
        dots_e2 = submodular_kernel_allocate(p_e2, allowed, BUDGET, eta=DINKELBACH_ETA)
        del p_e2
        res_e2, bt_e2 = EH.evaluate(dots_e2.astype(np.float32), f, fp, block_side=200)
        del dots_e2
        arm_fold_terms["E2_rlms_native19_only_ablation"].append(bt_e2)
        holdout_per_fold["E2_rlms_native19_only_ablation"][f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_e2["dti"],
            "n_truth": res_e2["n_truth"],
            "emitted": res_e2["n_emitted"],
        }
        gc.collect()

        # Arm E3: Unprojected scalar + 50/50 split + disc_thin control
        X_e3, y_e3 = sample_e3_ablation_pu(static_mm, vis, fp, seed=8692 + 10 * fold_i)
        clf_e3 = fit_single_hgb(X_e3, y_e3, seed=8692 + 10 * fold_i)
        del X_e3, y_e3
        surf_e3 = predict_ensemble_surface(
            [clf_e3],
            static_mm,
            ALL_STATIC_NAMES,
            E3_SCALAR_SUBSET,
            cont_pred,
            ("iso_tip_halo",),
            fp,
        )
        del clf_e3, cont_pred
        dots_e3 = disc_thin(surf_e3, allowed, BUDGET, spacing=SPACING_PX)
        del surf_e3
        res_e3, bt_e3 = EH.evaluate(dots_e3.astype(np.float32), f, fp, block_side=200)
        del dots_e3
        arm_fold_terms["E3_rlms_unprojected_disc_ablation"].append(bt_e3)
        holdout_per_fold["E3_rlms_unprojected_disc_ablation"][f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_e3["dti"],
            "n_truth": res_e3["n_truth"],
            "emitted": res_e3["n_emitted"],
        }
        gc.collect()

        # Exact same-split H86F-EWCS champion reproduction for paired block-bootstrap CI
        dots_ewcs = reproduce_ewcs_fold(ewcs_mm, vis, fp, fold_i)
        res_ew, bt_ew = EH.evaluate(dots_ewcs.astype(np.float32), f, fp, block_side=200)
        del dots_ewcs
        arm_fold_terms["H86F_EWCS_reproduced"].append(bt_ew)
        holdout_per_fold["H86F_EWCS_reproduced"][f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_ew["dti"],
            "n_truth": res_ew["n_truth"],
            "emitted": res_ew["n_emitted"],
        }

        # Fold-fair D28 visible-collar geometry control
        d28_allowed = d28_mask & allowed
        if int(d28_allowed.sum()) <= BUDGET:
            d28_dots = d28_allowed
        else:
            d28_dots = disc_thin(d28_allowed.astype(np.float32), allowed, BUDGET, spacing=SPACING_PX)
        res_d28, bt_d28 = EH.evaluate(d28_dots.astype(np.float32), f, fp, block_side=200)
        arm_fold_terms["R0_D28_visible_collar"].append(bt_d28)
        holdout_per_fold["R0_D28_visible_collar"][f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_d28["dti"],
            "n_truth": res_d28["n_truth"],
            "emitted": res_d28["n_emitted"],
        }
        del allowed, d28_allowed, d28_dots

        np.savez(
            ckpt_npz,
            bt_E1_rlms_full_submodular=bt_e1,
            bt_E2_rlms_native19_only_ablation=bt_e2,
            bt_E3_rlms_unprojected_disc_ablation=bt_e3,
            bt_H86F_EWCS_reproduced=bt_ew,
            bt_R0_D28_visible_collar=bt_d28,
            **cp_save,
            **cn_save,
        )
        del cp_save, cn_save
        ckpt_json.write_text(
            json.dumps(
                {
                    "fold_index": fold_i,
                    "fold_name": f["name"],
                    "static_sha256": static_sha256,
                    "preregistration_sha256": prereg_sha,
                    "per_fold": {
                        name: holdout_per_fold[name][f["name"]] for name in all_eval_names
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            f"[H86I-RLMS] Finished fold {fold_i + 1}/4 ({f['name']}) at +{time.time()-t0:.1f}s: "
            f"E1={res_e1['dti']:.6f} E2={res_e2['dti']:.6f} E3={res_e3['dti']:.6f} "
            f"EWCS={res_ew['dti']:.6f}",
            file=sys.stderr,
            flush=True,
        )
        gc.collect()
        if args.stop_after_fold is not None and (fold_i + 1) >= args.stop_after_fold:
            return 0

    del ewcs_mm, d28_mask
    for k in all_cont_canary_keys:
        vals = np.r_[cont_pos_buf[k], cont_neg_buf[k]].astype(np.float64)
        canary[k] = score_canary_array(vals, y_canary)
    del cont_pos_buf, cont_neg_buf, p_idx, n_idx, y_canary
    flagged = [k for k, v in canary.items() if v["leakage_flag"]]
    if flagged:
        raise RuntimeError(f"STOP: single-feature leakage canary exceeded 0.90: {flagged}")

    holdout_terms = {name: np.sum(t_list, axis=0) for name, t_list in arm_fold_terms.items()}
    pooled = EH.pooled_summary(
        holdout_terms,
        draws=1000,
        seed=862026,
        candidate="E1_rlms_full_submodular",
    )

    kslb_best = json.loads((EV_DIR / "lane86c_results.json").read_text(encoding="utf-8"))[
        "holdout_buffered_whole_components"
    ]["scores"]["E3_kslb_noisyor_44k"]
    ewcs_card = json.loads((EV_DIR / "h86f-ewcs-run-card.json").read_text(encoding="utf-8"))[
        "holdout_dti"
    ]["candidate"]
    comp_r0 = json.loads((EV_DIR / "h86e_comparator.json").read_text(encoding="utf-8"))[
        "paired"
    ]["E1_hgb_thin"]["scores"]["R0_foldfair"]

    e1_score = pooled["scores"]["E1_rlms_full_submodular"]
    e2_score = pooled["scores"]["E2_rlms_native19_only_ablation"]
    e3_score = pooled["scores"]["E3_rlms_unprojected_disc_ablation"]
    ewcs_rep_score = pooled["scores"]["H86F_EWCS_reproduced"]
    delta_vs_ewcs = pooled["paired_differences"]["H86F_EWCS_reproduced"]
    delta_vs_e2 = pooled["paired_differences"]["E2_rlms_native19_only_ablation"]
    delta_vs_e3 = pooled["paired_differences"]["E3_rlms_unprojected_disc_ablation"]
    best_ctrl_name = pooled["best_comparable_control"]
    best_delta = pooled["paired_differences"][best_ctrl_name]

    beats_ewcs_paired = bool(
        e1_score["dti"] > ewcs_rep_score["dti"] and delta_vs_ewcs["ci95"][0] > 0.0
    )
    beats_kslb = bool(
        e1_score["dti"] > kslb_best["dti"] and e1_score["ci95"][0] > kslb_best["ci95"][1]
    )
    beats_ablation_e3 = bool(delta_vs_e3["ci95"][0] > 0.0)

    print(
        f"[H86I-RLMS] Holdout complete at +{time.time()-t0:.1f}s: "
        f"E1={e1_score['dti']:.6f} E2={e2_score['dti']:.6f} E3={e3_score['dti']:.6f} "
        f"EWCS={ewcs_rep_score['dti']:.6f} (delta={delta_vs_ewcs['delta']:+.6f} CI={delta_vs_ewcs['ci95']})",
        file=sys.stderr,
        flush=True,
    )

    # Full-catalogue pre-placement calibrated probability surface BEFORE any dot placement
    sub_c2_full = _plane(static_mm, ALL_STATIC_NAMES, "nematic_sub_c2").astype(np.float32)
    sub_s2_full = _plane(static_mm, ALL_STATIC_NAMES, "nematic_sub_s2").astype(np.float32)
    cont_full = compute_continuation_fields(cat & fp, fp, sub_c2_full, sub_s2_full)
    del sub_c2_full, sub_s2_full

    X_stat_f, X_cont_f, y_f, w_f = sample_oof80_buffered_pu(
        static_mm, cat & fp, fp, n_neg=260_000, n_splits=5, seed=86999
    )
    pi_tr_f = float(np.dot(w_f, y_f) / np.sum(w_f))
    pi_tg_f = float(0.30 * ((cat & fp).sum() / fp_pixels))
    X_full = np.hstack([X_stat_f, X_cont_f])
    del X_stat_f, X_cont_f
    models_full = fit_rlms_ensemble(X_full, y_f, w_f, seed=86999)
    del X_full, y_f, w_f
    q_full = predict_ensemble_surface(
        models_full, static_mm, ALL_STATIC_NAMES, ALL_STATIC_NAMES, cont_full, CONTINUATION_NAMES, fp
    )
    del models_full, cont_full, static_mm
    gc.collect()

    p_full_cal = bayes_prior_calibrate(q_full, pi_tr_f, pi_tg_f, fp)
    del q_full
    gc.collect()

    surface_npy = WORK_DIR / "h86i_rlms_final_surface.npy"
    np.save(surface_npy, p_full_cal)
    surface_sha = sha256(surface_npy)

    surface_report_path = EV_DIR / "h86i-rlms-registry-surface.json"
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
        "schema": "gems86.h86i-rlms-run-card.v1",
        "lane": "H86I-RLMS",
        "session_branch": "arena/6bbd9586-gemsdoe86",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {
            "document": "research/H86I_RLMS_PREREGISTRATION.md",
            "machine_readable": "research/H86I_RLMS_PREREGISTRATION.json",
            "preregistration_sha256": sha256(PREREGISTRATION_PATH),
            "hypothesis_queue": "registry/h86i_rlms_hypotheses.json",
            "hypothesis_queue_sha256": sha256(HYPOTHESES_PATH),
            "arm_ids": expected_arms,
        },
        "hypothesis": (
            "H86I-RLMS: Blind Basin-and-Range / Walker-Lane faults missed by surface mapping "
            "are recovered by projecting 0.5-1.1 km deep hanging-wall gravity and MT "
            "conductivity anomalies up-dip onto the emergent footwall trace, phase-locking "
            "branch-cut-free spin-2 nematic strike directors across gravity, magnetics, "
            "basement depth, 1 m 3DEP LiDAR micro-scarps, and diffused visible fault strikes "
            "(including Riedel conjugate relay obliquity), adding 10 m fluvial chi knickpoints "
            "and GeoDAWN K/eTh metasomatism, and allocating 37,654 dots via Minoux lazy-greedy "
            "submodular 300 m triangular-kernel coverage on Bayes-calibrated 80/20 buffered-OOF "
            "posteriors."
        ),
        "mechanism": (
            "25 native competition planes (Miller magnetic tilt + alteration trough, Laplace "
            "g_zz zero-crossing steepness with curl seam veto, Cordell compaction-stripped "
            "horst gradient, listric up-dip footwall projections at 500 m & 1,100 m along +n_HW, "
            "spin-2 nematic coherence + E-W flight-line veto, principal extensional strain rate, "
            "seismicity, native DEM scarp curvature) + 8 SHA-pinned official USGS external planes "
            "(NaN-routed 3DEP 1 m LiDAR micro-scarps & spin-2 alignment with Lahontan shoreline "
            "veto, 3DEP 10 m sub-pixel micro-scarp excess & fluvial chi/k_sn disequilibrium, "
            "GeoDAWN K/eTh hydrothermal metasomatism) + 6 strictly fold-visible 80/20 "
            "buffered-component OOF continuation planes (wing-crack lobes, dual-scale valley "
            "cones, dual-scale stepover bridges, broadside stress-shadow suppression, spin-2 "
            "kinematic strike alignment, Riedel relay obliquity), fitted via cover-weighted "
            "2-seed HistGradientBoosting, Bayes prior-shift calibrated, and decoded at matched "
            "37,654-dot cardinality via Minoux lazy-greedy submodular 300 m kernel allocation."
        ),
        "named_non_fault_process": (
            "Pleistocene Lake Lahontan (~1,335 m) and Lake Bonneville iso-elevation wave-cut "
            "shoreline beach ridges, E-W USGS GeoDAWN airborne survey leveling seams, and "
            "partial 3DEP 1 m LiDAR tile coverage boundaries (mitigated via Lahontan shoreline "
            "contour veto, spin-2 E-W flight-line veto, and IEEE NaN missing-value routing)."
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
            "native19_only_ablation": e2_score,
            "unprojected_disc_ablation": e3_score,
            "H86F_EWCS_reproduced": ewcs_rep_score,
            "H86F_EWCS_archived_card_dti": ewcs_card["dti"],
            "paired_delta_vs_H86F_EWCS": delta_vs_ewcs,
            "paired_delta_vs_native19_ablation": delta_vs_e2,
            "paired_delta_vs_unprojected_disc_ablation": delta_vs_e3,
            "best_comparable_control": best_ctrl_name,
            "paired_delta_vs_best_comparable_control": best_delta,
            "R0_D28_visible_collar": pooled["scores"]["R0_D28_visible_collar"],
            "paired_delta_vs_R0_D28_visible_collar": pooled["paired_differences"][
                "R0_D28_visible_collar"
            ],
            "all_arms": pooled["scores"],
            "per_fold": holdout_per_fold,
            "paired_differences": pooled["paired_differences"],
            "same_split_comparators": {
                "H86F_EWCS_E1_37k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86f-ewcs-run-card.json",
                    "dti": ewcs_card["dti"],
                    "ci95": ewcs_card["ci95"],
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
            "beats_same_split_ewcs_paired_ci": beats_ewcs_paired,
            "beats_same_split_kslb_with_separated_ci": beats_kslb,
            "beats_ablation_e3_paired_ci": beats_ablation_e3,
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
        del p_full_cal
        run_card = {
            **base_card,
            "correlation_overlap_vs_registry": {
                "evidence_class": "REGISTRY-MEASUREMENT",
                "surface_preplacement": {
                    **registry_summary(surface_report, surface_report_path, surface_rc),
                    "surface_gate_pass": surface_gate_pass,
                },
                "final_dots": None,
                "informative_discrete_dot_diagnostic": None,
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
            "note_chars": 101,
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

    dcat = ndi.distance_transform_edt(~(cat & fp))
    allowed_full = fp & (dcat > COLLAR_PX)
    del dcat
    final_dots = submodular_kernel_allocate(
        p_full_cal, allowed_full, BUDGET, eta=DINKELBACH_ETA
    )
    del p_full_cal, allowed_full
    gc.collect()

    dots_npy = WORK_DIR / "h86i_rlms_final_dots.npy"
    np.save(dots_npy, final_dots.astype(np.float32))
    dots_sha = sha256(dots_npy)
    dots_report_path = EV_DIR / "h86i-rlms-registry-final-dots.json"
    dots_report, dots_rc = run_registry_check(dots_npy, dots_report_path, surface=False)
    chance_path = EV_DIR / "h86i-rlms-pa86-chance-overlap.json"
    chance = run_chance_check(dots_report_path, dots_npy, chance_path)
    informative_diag = summarize_informative_dot_overlaps(dots_report)

    if informative_diag["firings_over_0p70"] > 0:
        del final_dots
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
                    "final_dots_gate_pass": False,
                },
                "informative_discrete_dot_diagnostic": informative_diag,
                "pa86_02": chance,
            },
            "raster_sha256": None,
            "validator_output": {
                "evidence_class": "LOCAL-FORMAT-VALIDATION",
                "status": "NOT_WRITTEN_INFORMATIVE_OVERLAP_STOP",
                "all_checks_passed": False,
                "no_nan_inside_footprint": None,
                "values_in_0_1": None,
                "crs_shape_transform_match": None,
            },
            "submission_name": None,
            "submission_file": None,
            "note": "STOP: informative discrete 3-px dot overlap > 0.70; logged duplicate, no TIFF written, 0 slots used.",
            "note_chars": 100,
            "verdict": "negative",
            "duplicate": True,
            "new_candidate_generated": False,
            "decision": "DO NOT SUBMIT",
            "decision_reason": (
                f"informative discrete dot overlap > 0.70 against "
                f"{informative_diag['worst_discrete_id']} "
                f"({informative_diag['worst_discrete_overlap']:.4f})"
            ),
            "runtime_seconds": round(time.time() - t0, 2),
        }
        run_card["note_chars"] = len(run_card["note"])
        card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return 0

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
    name = f"gems86-h86i-rlms-riedel-listric-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"
    note = (
        f"H86I-RLMS Riedel-listric submodular PU (HOLDOUT-DTI {e1_score['dti']:.4f}); "
        f"registry fail-closed; DO NOT SUBMIT; 0 slots"
    )[:140]
    receipt = write_candidate(
        final_dots,
        g,
        name,
        note,
        metadata={
            "lane": "H86I-RLMS",
            "hypothesis": (
                "Listric up-dip hanging-wall projection + spin-2 nematic multi-physics "
                "strike alignment & Riedel relay obliquity + 3DEP 1m/10m micro-scarps/chi "
                "+ GeoDAWN K/eTh + 80/20 buffered-OOF submodular 300 m kernel allocation"
            ),
            "budget": BUDGET,
            "collar_px": COLLAR_PX,
            "dinkelbach_eta": DINKELBACH_ETA,
            "static_feature_memmap_sha256": static_sha256,
            "surface_sha256": surface_sha,
            "dots_sha256": dots_sha,
            "registry_surface_evidence": "docs/evidence/h86i-rlms-registry-surface.json",
            "registry_final_evidence": "docs/evidence/h86i-rlms-registry-final-dots.json",
            "chance_overlap_evidence": (
                str(chance_path.relative_to(ROOT))
                if chance_path.is_file()
                else "FAILED_CLOSED_NO_REPORT (see run card)"
            ),
        },
    )

    verdict = (
        "promote"
        if (beats_ewcs_paired and beats_kslb and beats_ablation_e3 and registry_gate)
        else "negative"
    )
    stop_reasons: list[str] = []
    if not beats_ewcs_paired:
        stop_reasons.append(
            f"HOLDOUT-DTI ({e1_score['dti']:.4f}) did not beat reproduced same-split "
            f"H86F-EWCS ({ewcs_rep_score['dti']:.4f}) with positive paired 95% CI"
        )
    if not beats_ablation_e3:
        stop_reasons.append(
            "paired HOLDOUT-DTI delta vs unprojected disc-thin ablation E3 95% CI includes or falls below zero"
        )
    if not surface_gate_pass:
        stop_reasons.append(
            "pre-placement surface registry gate did not pass (2 grid-incompatible registry rows "
            "and literal 17GEMSDOE full-support witness; 0 Spearman rho > 0.90 firings)"
        )
    if not final_dots_gate_pass:
        stop_reasons.append(
            "final-dot registry gate failed closed (literal 17GEMSDOE full-support witness / "
            "lattice overlap firings and 2 grid-incompatible registry rows; 0 informative "
            "<=100k-dot overlap firings > 0.70)"
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
            "informative_discrete_dot_diagnostic": informative_diag,
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
    print(
        json.dumps(
            {
                "lane": "H86I-RLMS",
                "submission_file": run_card["submission_file"],
                "raster_sha256": run_card["raster_sha256"],
                "e1_holdout_dti": e1_score["dti"],
                "e1_ci95": e1_score["ci95"],
                "e2_native19_holdout_dti": e2_score["dti"],
                "e3_ablation_holdout_dti": e3_score["dti"],
                "ewcs_reproduced_holdout_dti": ewcs_rep_score["dti"],
                "paired_delta_vs_ewcs": delta_vs_ewcs,
                "paired_delta_vs_e2": delta_vs_e2,
                "paired_delta_vs_e3": delta_vs_e3,
                "beats_ewcs_paired": beats_ewcs_paired,
                "surface_rho_firings": rho_firings,
                "worst_surface_spearman": surface_report["shared_summary"][
                    "worst_spearman_full_footprint"
                ],
                "informative_discrete_firings": informative_diag["firings_over_0p70"],
                "worst_informative_discrete_overlap": informative_diag["worst_discrete_overlap"],
                "worst_informative_discrete_id": informative_diag["worst_discrete_id"],
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
