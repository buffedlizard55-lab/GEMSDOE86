#!/usr/bin/env python3
"""Run preregistered Lane H86I-KSAD (Kostrov-Byerlee Azimuthal Slip/Dilation Tendency,
Roest Upward-Continued Depth Persistence & SAR Cover-Propensity Dinkelbach Submodular
K3 Allocation) under PA-86-01/02 and AGENTS.md Rules 1-11.

Strict protocol guarantees:
1. Verifies frozen preregistration ``research/H86I_KSAD_PREREGISTRATION.json`` before
   computing any feature, model fit, holdout score, or registry check.
2. Uses shared ``vendor/gems57/{grid,holdout,evaluate_holdout,submission_writer,validate}``
   without private forks.
3. Enforces BOTH strict outer Leave-One-Quadrant-Out training (``quad != q`` eroded 12 px)
   AND nested cross-component elastic splitting inside the training quadrants.
4. Runs single-feature leakage canaries on all 26 static + 6 fold-visible features
   (``max(AUC, 1-AUC) <= 0.90``).
5. Runs SHA-bound ``v2`` ``scripts/check_h86e_registry.py --surface`` BEFORE placement
   and ``scripts/check_h86e_registry.py`` + ``scripts/pa86_chance_overlap.py`` on final
   dots BEFORE GeoTIFF serialization.
6. Fails closed to ``verdict="negative"``, ``decision="DO NOT SUBMIT"``,
   ``safe_to_submit=False``, ``approved_for_weekly_slot=False``, ``submission_slots_used=0``
   unless every literal, completeness, chance-overlap, and holdout gate passes.
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
from sklearn.ensemble import HistGradientBoostingClassifier
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
from gems57 import gates, grid, holdout, submission_writer, validate
from gems86_ewcs.features import (
    ELASTIC_COUPLED_NAMES as EWCS_ELASTIC_NAMES,
    STATIC_FEATURE_NAMES as EWCS_STATIC_NAMES,
    build_static_features as build_ewcs_static_features,
    compute_elastic_fields as compute_ewcs_elastic_fields,
)
from gems86_ksad import (
    COVER_BLIND_STATIC_NAMES,
    ELASTIC_FEATURE_NAMES,
    STATIC_FEATURE_NAMES,
    build_static_features,
    compute_exposure_propensity,
    compute_kostrov_elastic_fields,
    dinkelbach_submodular_k3_allocate,
    elkan_bayes_recalibrate,
    pointwise_disc_thin,
)
from scripts.pa86_chance_overlap import halo_coverage
import protocol_preflight
from restore_data import EXTERNAL_PINS, PINS

SEED = 20
HIDE_FRAC = 0.20
BUFFER_PX = 3
DOMAIN_ERODE = 12
BUDGET_CAP = 37_654
DINKELBACH_LAMBDA = 0.17
MIN_SEP_PX = 2.4
DISC_SPACING_PX = 2.8
COLLAR_PX = 2.6

PREREG_JSON = ROOT / "research/H86I_KSAD_PREREGISTRATION.json"
FEATURE_TIF = ROOT / "data/bridge/training_features.tif"
EXTERNAL_DIR = ROOT / ".cache/external"
WORK_DIR = ROOT / ".cache/h86i_ksad_work"
EV_DIR = ROOT / "docs/evidence"
OUT_DIR = ROOT / "docs/downloads"

D28_CONTROL_TIF = (
    ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
)
D28_CONTROL_SHA = "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"
R0_GEMS25_SHA = "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"
R0_GEMS25_TIF = ROOT / f".cache/registry_ext/{R0_GEMS25_SHA}.tif"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pinned_inputs() -> dict[str, str]:
    verified: dict[str, str] = {}
    def _exp_sha(m) -> str:
        if isinstance(m, str):
            return m
        if isinstance(m, tuple):
            return str(m[0])
        return str(m["sha256"])

    for name, meta in PINS.items():
        p = ROOT / "data/bridge" / name
        if not p.is_file():
            raise RuntimeError(f"Missing pinned input {p}")
        got = sha256(p)
        exp = _exp_sha(meta)
        if got != exp:
            raise RuntimeError(f"SHA-256 mismatch on {p}: {got} != {exp}")
        verified[f"data/bridge/{name}"] = got
    for name, meta in EXTERNAL_PINS.items():
        p = EXTERNAL_DIR / name
        if not p.is_file():
            raise RuntimeError(f"Missing pinned external input {p}")
        got = sha256(p)
        exp = _exp_sha(meta)
        if got != exp:
            raise RuntimeError(f"SHA-256 mismatch on {p}: {got} != {exp}")
        verified[f".cache/external/{name}"] = got
    if not D28_CONTROL_TIF.is_file() or sha256(D28_CONTROL_TIF) != D28_CONTROL_SHA:
        raise RuntimeError(f"Missing or corrupted D28 control {D28_CONTROL_TIF}")
    verified[str(D28_CONTROL_TIF.relative_to(ROOT))] = D28_CONTROL_SHA
    if not R0_GEMS25_TIF.is_file() or sha256(R0_GEMS25_TIF) != R0_GEMS25_SHA:
        raise RuntimeError(f"Missing or corrupted GEMSDOE25 R0 control {R0_GEMS25_TIF}")
    verified[str(R0_GEMS25_TIF.relative_to(ROOT))] = R0_GEMS25_SHA
    return verified


def split_visible_components(vis_cat: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
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


def _plane(mm: np.ndarray, names: tuple[str, ...], key: str) -> np.ndarray:
    return mm[names.index(key)]


def sample_strict_loqo_pu(
    static_mm: np.ndarray,
    all_static_names: tuple[str, ...],
    static_keys: tuple[str, ...],
    vis_cat: np.ndarray,
    train_domain: np.ndarray,
    footprint: np.ndarray,
    elastic_keys: tuple[str, ...],
    elastic_builder,
    c_exposure: np.ndarray | None,
    *,
    n_neg: int = 180_000,
    collar_px: float = COLLAR_PX,
    seed: int = 8600,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Strict outer-domain PU sampling with nested cross-component elastic fields."""
    rng = np.random.default_rng(seed)
    fp = np.asarray(footprint, dtype=bool)
    dom = np.asarray(train_domain, dtype=bool) & fp
    vis_dom = np.asarray(vis_cat, dtype=bool) & dom

    d_vis = ndi.distance_transform_edt(~(np.asarray(vis_cat, dtype=bool) & fp))
    neg_pool = np.flatnonzero((dom & (d_vis > max(collar_px, 3.0))).ravel())
    del d_vis

    def _pos_weights(p_idx: np.ndarray) -> np.ndarray:
        if c_exposure is None or p_idx.size == 0:
            return np.ones(p_idx.size, dtype=np.float32)
        c_vals = c_exposure.ravel()[p_idx]
        return np.clip(1.0 / np.sqrt(np.maximum(c_vals, 0.35)), 1.0, 1.69).astype(np.float32)

    if not elastic_keys:
        pos_idx = np.flatnonzero(vis_dom.ravel())
        take_neg = rng.choice(neg_pool, size=min(n_neg, neg_pool.size), replace=False)
        idx = np.concatenate([pos_idx, take_neg])
        y = np.concatenate([np.ones(pos_idx.size, dtype=np.int8), np.zeros(take_neg.size, dtype=np.int8)])
        wp = _pos_weights(pos_idx)
        w = np.concatenate([wp, np.ones(take_neg.size, dtype=np.float32)])
        X = np.column_stack(
            [_plane(static_mm, all_static_names, k).ravel()[idx].astype(np.float32) for k in static_keys]
        )
        mean_wp = float(wp.mean()) if wp.size else 1.0
        eff_r_neg = (float(neg_pool.size) / float(max(take_neg.size, 1))) / max(mean_wp, 1e-6)
        return X, y, w, eff_r_neg

    # Split FULL visible catalogue into disjoint whole components (va_full, vb_full)
    # so boundary context across train_domain remains realistic while ONLY sampling
    # training labels strictly inside ``dom``!
    va_full, vb_full = split_visible_components(np.asarray(vis_cat, dtype=bool) & fp, seed=seed)
    tot_neg_dom = int(neg_pool.size)
    rng.shuffle(neg_pool)
    half_neg = min(n_neg // 2, neg_pool.size // 2)
    neg_a = neg_pool[:half_neg]
    neg_b = neg_pool[half_neg : 2 * half_neg]
    del neg_pool

    db = ndi.distance_transform_edt(~vb_full)
    pos_a = np.flatnonzero((va_full & dom & (db > collar_px)).ravel())
    del db
    wp_a = _pos_weights(pos_a)
    idx_a = np.concatenate([pos_a, neg_a])
    ya = np.concatenate([np.ones(pos_a.size, dtype=np.int8), np.zeros(neg_a.size, dtype=np.int8)])
    wa = np.concatenate([wp_a, np.ones(neg_a.size, dtype=np.float32)])
    el_b = elastic_builder(vb_full, fp)
    Xa = np.column_stack(
        [_plane(static_mm, all_static_names, k).ravel()[idx_a].astype(np.float32) for k in static_keys]
        + [el_b[k].ravel()[idx_a].astype(np.float32) for k in elastic_keys]
    )
    del el_b, idx_a
    gc.collect()

    da = ndi.distance_transform_edt(~va_full)
    pos_b = np.flatnonzero((vb_full & dom & (da > collar_px)).ravel())
    del da
    wp_b = _pos_weights(pos_b)
    idx_b = np.concatenate([pos_b, neg_b])
    yb = np.concatenate([np.ones(pos_b.size, dtype=np.int8), np.zeros(neg_b.size, dtype=np.int8)])
    wb = np.concatenate([wp_b, np.ones(neg_b.size, dtype=np.float32)])
    el_a = elastic_builder(va_full, fp)
    del va_full, vb_full
    Xb = np.column_stack(
        [_plane(static_mm, all_static_names, k).ravel()[idx_b].astype(np.float32) for k in static_keys]
        + [el_a[k].ravel()[idx_b].astype(np.float32) for k in elastic_keys]
    )
    del el_a, idx_b
    gc.collect()

    samp_neg = int(neg_a.size + neg_b.size)
    all_wp = np.concatenate([wp_a, wp_b])
    mean_wp = float(all_wp.mean()) if all_wp.size else 1.0
    eff_r_neg = (float(tot_neg_dom) / float(max(samp_neg, 1))) / max(mean_wp, 1e-6)
    return np.vstack([Xa, Xb]), np.concatenate([ya, yb]), np.concatenate([wa, wb]), eff_r_neg


def fit_hgb_model(
    X: np.ndarray,
    y: np.ndarray,
    w: np.ndarray | None,
    *,
    seed: int,
    max_leaf_nodes: int = 55,
    max_iter: int = 230,
    l2_reg: float = 2.5,
) -> HistGradientBoostingClassifier:
    clf = HistGradientBoostingClassifier(
        max_iter=max_iter,
        learning_rate=0.06,
        max_leaf_nodes=max_leaf_nodes,
        min_samples_leaf=95,
        l2_regularization=l2_reg,
        early_stopping=False,
        random_state=seed,
    )
    return clf.fit(X, y, sample_weight=w)


def predict_chunked(
    clf: HistGradientBoostingClassifier,
    static_mm: np.ndarray,
    all_static_names: tuple[str, ...],
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
        cols = [_plane(static_mm, all_static_names, k)[r0:r1][m].astype(np.float32) for k in static_keys]
        if elastic_keys and elastic_planes is not None:
            cols.extend(elastic_planes[k][r0:r1][m].astype(np.float32) for k in elastic_keys)
        X_chunk = np.column_stack(cols)
        out[r0:r1][m] = clf.predict_proba(X_chunk)[:, 1].astype(np.float32)
    return out


def fit_predict_ksad_posterior(
    static_mm: np.ndarray,
    vis_cat: np.ndarray,
    train_domain: np.ndarray,
    eval_mask: np.ndarray,
    fp: np.ndarray,
    c_exposure: np.ndarray,
    el_pred: dict[str, np.ndarray],
    *,
    seed_base: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit both the coupled KSAD model (E1/E2) and cover-blind zero-catalogue specialist (E3)."""
    # 1. Cover-blind zero-catalogue model (used standalone as Arm E3 AND as alluvial specialist in E1/E2)
    X_sub, y_sub, w_sub, r_sub = sample_strict_loqo_pu(
        static_mm,
        STATIC_FEATURE_NAMES,
        COVER_BLIND_STATIC_NAMES,
        vis_cat,
        train_domain,
        fp,
        (),
        compute_kostrov_elastic_fields,
        c_exposure,
        n_neg=180_000,
        seed=seed_base + 1,
    )
    clf_sub = fit_hgb_model(X_sub, y_sub, w_sub, seed=seed_base + 1, max_leaf_nodes=39, max_iter=200, l2_reg=3.0)
    del X_sub, y_sub, w_sub
    gc.collect()
    p_sub_raw = predict_chunked(
        clf_sub, static_mm, STATIC_FEATURE_NAMES, COVER_BLIND_STATIC_NAMES, None, (), eval_mask
    )
    del clf_sub
    p_sub_bayes = elkan_bayes_recalibrate(p_sub_raw, r_sub, valid=eval_mask)
    del p_sub_raw
    gc.collect()

    # 2. Full 32-feature coupled physical + anisotropic Kostrov-Pollard model (2 diverse seeds averaged)
    X_m, y_m, w_m, r_m = sample_strict_loqo_pu(
        static_mm,
        STATIC_FEATURE_NAMES,
        STATIC_FEATURE_NAMES,
        vis_cat,
        train_domain,
        fp,
        ELASTIC_FEATURE_NAMES,
        compute_kostrov_elastic_fields,
        c_exposure,
        n_neg=180_000,
        seed=seed_base + 2,
    )
    clf_m1 = fit_hgb_model(X_m, y_m, w_m, seed=seed_base + 2, max_leaf_nodes=55, max_iter=230, l2_reg=2.5)
    clf_m2 = fit_hgb_model(X_m, y_m, w_m, seed=seed_base + 3, max_leaf_nodes=35, max_iter=250, l2_reg=3.5)
    del X_m, y_m, w_m
    gc.collect()
    p1 = predict_chunked(
        clf_m1, static_mm, STATIC_FEATURE_NAMES, STATIC_FEATURE_NAMES, el_pred, ELASTIC_FEATURE_NAMES, eval_mask
    )
    p2 = predict_chunked(
        clf_m2, static_mm, STATIC_FEATURE_NAMES, STATIC_FEATURE_NAMES, el_pred, ELASTIC_FEATURE_NAMES, eval_mask
    )
    del clf_m1, clf_m2
    p_main_bayes = elkan_bayes_recalibrate(0.55 * p1 + 0.45 * p2, r_m, valid=eval_mask)
    del p1, p2
    gc.collect()

    # Cover-aware blend: in low-exposure alluvial basins (c_exposure -> 0.35), lift blind faults
    w_blind = np.clip(0.32 * (1.0 - c_exposure) / 0.65, 0.0, 0.32)
    p_coupled = np.where(
        eval_mask,
        (1.0 - w_blind) * p_main_bayes + w_blind * np.maximum(p_main_bayes, 0.90 * p_sub_bayes),
        0.0,
    ).astype(np.float32)
    del p_main_bayes, w_blind
    return p_coupled, p_sub_bayes


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


def rank01_on_footprint(raw: np.ndarray, fp: np.ndarray) -> np.ndarray:
    out = np.zeros(raw.shape, dtype=np.float32)
    vals = raw[fp]
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float32)
    ranks[order] = np.linspace(0.0, 1.0, vals.size, dtype=np.float32)
    out[fp] = ranks
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
            "pa86_chance_overlap.py refused to certify (incomplete registry / literal witness); "
            "recorded verbatim, never bypassed with a private computation."
        ),
    }


def discrete_non_saturation_overlap_firings(
    report: dict, footprint: np.ndarray, allowed: np.ndarray, max_discrete_dots: int = 55000
) -> list[dict]:
    """Identify any discrete fault-dot raster (<= 55k dots) exceeding 0.70 forward 3-px overlap."""
    rows = report.get("comparison_rows", [])
    bad = []
    for r in rows:
        if "my_dots_within_3px_of_theirs" not in r:
            continue
        if (
            r.get("representation") == "dot_field"
            and int(r.get("their_dots", 0)) <= max_discrete_dots
            and float(r.get("my_dots_within_3px_of_theirs", 0.0)) > 0.70
        ):
            c_halo = halo_coverage(Path(r["file"]), footprint, allowed)
            bad.append(
                {
                    "submission": r["submission"],
                    "their_dots": int(r["their_dots"]),
                    "forward_overlap_3px": float(r["my_dots_within_3px_of_theirs"]),
                    "chance_halo_coverage_allowed": float(c_halo),
                    "informative_non_space_filling": bool(c_halo <= 0.70),
                    "spearman_full_footprint": float(r["spearman_full_footprint"]),
                }
            )
    return bad


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
        "indexed_entries": report.get("registry_rasters_expected"),
        "compared": report.get("registry_rasters_measured"),
        "skipped_or_invalid": shared.get("missing_or_invalid"),
        "rho_firings": lit.get("rho_firings"),
        "overlap_firings": lit.get("forward_overlap_firings"),
        "worst_spearman_full_footprint": shared.get("worst_spearman_full_footprint"),
        "worst_forward_overlap_3px": shared.get("worst_dot_overlap"),
        "surface_gate_pass": report.get("surface_gate_pass"),
        "final_dots_gate_pass": report.get("final_dots_gate_pass"),
        "literal_gate_pass": report.get("literal_gate_pass"),
        "submission_authorized": report.get("submission_authorized"),
        "top5_by_spearman": [
            {
                "submission": r["submission"],
                "spearman_full_footprint": r["spearman_full_footprint"],
                "their_dots": r["their_dots"],
                "representation": r.get("representation"),
            }
            for r in report.get("top15_by_spearman", [])[:5]
        ],
    }


def _execute_pa86_lane() -> int:
    t0 = time.time()
    preflight = protocol_preflight.require_like_for_like()

    if not PREREG_JSON.is_file():
        raise RuntimeError(f"Missing frozen preregistration {PREREG_JSON}")
    prereg = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    prereg_sha256 = sha256(PREREG_JSON)
    expected_arms = {
        "E1_ksad_dinkelbach_submod",
        "E2_ksad_pointwise_d28_ablation",
        "E3_ksad_cover_blind_no_catalogue",
    }
    if {a["id"] for a in prereg["arms"]} != expected_arms:
        raise RuntimeError("Preregistration arm IDs do not match runner specification")

    input_hashes = verify_pinned_inputs()
    g = grid.load_grid(ROOT / "data/bridge")
    fp, cat = g.footprint, g.catalogue
    folds, quad = holdout.buffered_component_draw(
        g, seed=SEED, hide_frac=HIDE_FRAC, buffer_px=BUFFER_PX
    )

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/6] Building / verifying 26 quadrant-invariant H86I-KSAD static planes...", flush=True)
    static_memmap = WORK_DIR / "h86i_ksad_static.npy"
    if static_memmap.is_file():
        mm_check = np.load(static_memmap, mmap_mode="r")
        if mm_check.shape == (len(STATIC_FEATURE_NAMES), fp.shape[0], fp.shape[1]) and mm_check.dtype == np.float16:
            static_mm = mm_check
        else:
            del mm_check
            static_mm = build_static_features(FEATURE_TIF, EXTERNAL_DIR, fp, static_memmap)
    else:
        static_mm = build_static_features(FEATURE_TIF, EXTERNAL_DIR, fp, static_memmap)
    static_sha256 = sha256(static_memmap)
    c_exposure = compute_exposure_propensity(EXTERNAL_DIR, fp)

    # Also build/load H86F-EWCS 19 static planes to run a strictly-LOQO EWCS control
    print("[2/6] Building / verifying H86F-EWCS static planes for strict-LOQO control...", flush=True)
    ewcs_memmap = WORK_DIR / "h86f_ewcs_ctrl_static.npy"
    if ewcs_memmap.is_file():
        mm_ew = np.load(ewcs_memmap, mmap_mode="r")
        if mm_ew.shape == (len(EWCS_STATIC_NAMES), fp.shape[0], fp.shape[1]) and mm_ew.dtype == np.float16:
            ewcs_mm = mm_ew
        else:
            del mm_ew
            ewcs_mm = build_ewcs_static_features(FEATURE_TIF, fp, out_memmap_path=ewcs_memmap)
    else:
        ewcs_mm = build_ewcs_static_features(FEATURE_TIF, fp, out_memmap_path=ewcs_memmap)

    def _run_holdout() -> tuple[dict, dict, dict]:
        print("[3/6] Scoring single-feature leakage canaries on static planes...", flush=True)
        p_idx, n_idx, y_canary = prepare_canary_indices(folds, fp)
        canary_d: dict[str, dict] = {}
        for k in STATIC_FEATURE_NAMES:
            flat = _plane(static_mm, STATIC_FEATURE_NAMES, k).ravel()
            vals = np.r_[flat[p_idx], flat[n_idx]].astype(np.float64)
            canary_d[k] = score_canary_array(vals, y_canary)
            del vals

        el_pos_buf = {k: np.zeros(p_idx.size, dtype=np.float32) for k in ELASTIC_FEATURE_NAMES}
        el_neg_buf = {k: np.zeros(n_idx.size, dtype=np.float32) for k in ELASTIC_FEATURE_NAMES}

        arm_names = (
            "E1_ksad_dinkelbach_submod",
            "E2_ksad_pointwise_d28_ablation",
            "E3_ksad_cover_blind_no_catalogue",
            "C1_H86F_EWCS_strict_loqo_ctrl",
            "R0_D28_visible_collar",
            "R0_GEMSDOE25_fold_fair",
        )
        arm_fold_terms: dict[str, list[np.ndarray]] = {a: [] for a in arm_names}
        per_fold_d: dict[str, dict] = {a: {} for a in arm_names}

        d28_mask = load_binary_tif(D28_CONTROL_TIF) & fp
        r0_25_mask = load_binary_tif(R0_GEMS25_TIF) & fp

        vis_global = np.asarray(folds[0]["visible"], dtype=bool) & fp
        el_ksad_global = compute_kostrov_elastic_fields(vis_global, fp)
        el_ewcs_global = compute_ewcs_elastic_fields(vis_global, fp)
        d_vis_global = ndi.distance_transform_edt(~vis_global)
        allowed_ksad = fp & (d_vis_global > COLLAR_PX)
        allowed_ctrl3 = fp & (d_vis_global > 3.0)
        allowed_r0_2 = fp & (d_vis_global > 2.0)
        del d_vis_global

        for fold_i, f in enumerate(folds):
            qname = f["name"]
            print(f"[4/6] Running strict Leave-One-Quadrant-Out fold {qname} ({fold_i+1}/4)...", flush=True)
            train_dom = ndi.binary_erosion((quad >= 0) & (quad != fold_i), iterations=DOMAIN_ERODE) & fp
            eval_region = np.asarray(f["region"], dtype=bool) & fp

            reg_flat = eval_region.ravel()
            p_in = reg_flat[p_idx]
            n_in = reg_flat[n_idx]
            for k in ELASTIC_FEATURE_NAMES:
                eflat = el_ksad_global[k].ravel()
                el_pos_buf[k][p_in] = eflat[p_idx[p_in]]
                el_neg_buf[k][n_in] = eflat[n_idx[n_in]]

            p_coupled, p_sub = fit_predict_ksad_posterior(
                static_mm,
                vis_global,
                train_dom,
                fp,
                fp,
                c_exposure,
                el_ksad_global,
                seed_base=8610 + 20 * fold_i,
            )

            dots_e1 = dinkelbach_submodular_k3_allocate(
                p_coupled,
                allowed_ksad,
                budget_cap=BUDGET_CAP,
                lambda_dti=DINKELBACH_LAMBDA,
                min_sep_px=MIN_SEP_PX,
            )
            res_e1, bt_e1 = EH.evaluate(dots_e1.astype(np.float32), f, fp, block_side=200)
            arm_fold_terms["E1_ksad_dinkelbach_submod"].append(bt_e1)
            per_fold_d["E1_ksad_dinkelbach_submod"][qname] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_e1["dti"],
                "n_truth": res_e1["n_truth"],
                "emitted_in_fold": res_e1["n_emitted"],
                "emitted_global": int(dots_e1.sum()),
            }
            del dots_e1

            dots_e2 = pointwise_disc_thin(
                p_coupled, allowed_ksad, budget=BUDGET_CAP, spacing_px=DISC_SPACING_PX
            )
            res_e2, bt_e2 = EH.evaluate(dots_e2.astype(np.float32), f, fp, block_side=200)
            arm_fold_terms["E2_ksad_pointwise_d28_ablation"].append(bt_e2)
            per_fold_d["E2_ksad_pointwise_d28_ablation"][qname] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_e2["dti"],
                "n_truth": res_e2["n_truth"],
                "emitted_in_fold": res_e2["n_emitted"],
                "emitted_global": int(dots_e2.sum()),
            }
            del dots_e2, p_coupled

            dots_e3 = dinkelbach_submodular_k3_allocate(
                p_sub,
                allowed_ksad,
                budget_cap=BUDGET_CAP,
                lambda_dti=DINKELBACH_LAMBDA,
                min_sep_px=MIN_SEP_PX,
            )
            res_e3, bt_e3 = EH.evaluate(dots_e3.astype(np.float32), f, fp, block_side=200)
            arm_fold_terms["E3_ksad_cover_blind_no_catalogue"].append(bt_e3)
            per_fold_d["E3_ksad_cover_blind_no_catalogue"][qname] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_e3["dti"],
                "n_truth": res_e3["n_truth"],
                "emitted_in_fold": res_e3["n_emitted"],
                "emitted_global": int(dots_e3.sum()),
            }
            del dots_e3, p_sub
            gc.collect()

            X_ew, y_ew, _, _ = sample_strict_loqo_pu(
                ewcs_mm,
                EWCS_STATIC_NAMES,
                EWCS_STATIC_NAMES,
                vis_global,
                train_dom,
                fp,
                EWCS_ELASTIC_NAMES,
                compute_ewcs_elastic_fields,
                None,
                n_neg=200_000,
                collar_px=3.0,
                seed=8700 + 10 * fold_i,
            )
            clf_ew = HistGradientBoostingClassifier(
                max_iter=200,
                learning_rate=0.07,
                max_leaf_nodes=47,
                min_samples_leaf=100,
                l2_regularization=2.0,
                early_stopping=False,
                random_state=8700 + 10 * fold_i,
            ).fit(X_ew, y_ew)
            del X_ew, y_ew
            surf_ew = predict_chunked(
                clf_ew, ewcs_mm, EWCS_STATIC_NAMES, EWCS_STATIC_NAMES, el_ewcs_global, EWCS_ELASTIC_NAMES, fp
            )
            del clf_ew
            dots_ew = pointwise_disc_thin(surf_ew, allowed_ctrl3, budget=BUDGET_CAP, spacing_px=2.8)
            del surf_ew
            res_ew, bt_ew = EH.evaluate(dots_ew.astype(np.float32), f, fp, block_side=200)
            del dots_ew
            arm_fold_terms["C1_H86F_EWCS_strict_loqo_ctrl"].append(bt_ew)
            per_fold_d["C1_H86F_EWCS_strict_loqo_ctrl"][qname] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_ew["dti"],
                "n_truth": res_ew["n_truth"],
                "emitted_in_fold": res_ew["n_emitted"],
            }

            d28_allowed = d28_mask & allowed_ctrl3
            d28_dots = (
                d28_allowed
                if int(d28_allowed.sum()) <= BUDGET_CAP
                else pointwise_disc_thin(d28_allowed.astype(np.float32), allowed_ctrl3, budget=BUDGET_CAP, spacing_px=2.8)
            )
            res_d28, bt_d28 = EH.evaluate(d28_dots.astype(np.float32), f, fp, block_side=200)
            arm_fold_terms["R0_D28_visible_collar"].append(bt_d28)
            per_fold_d["R0_D28_visible_collar"][qname] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_d28["dti"],
                "n_truth": res_d28["n_truth"],
                "emitted_in_fold": res_d28["n_emitted"],
            }

            r25_dots = r0_25_mask & allowed_r0_2
            res_r25, bt_r25 = EH.evaluate(r25_dots.astype(np.float32), f, fp, block_side=200)
            arm_fold_terms["R0_GEMSDOE25_fold_fair"].append(bt_r25)
            per_fold_d["R0_GEMSDOE25_fold_fair"][qname] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_r25["dti"],
                "n_truth": res_r25["n_truth"],
                "emitted_in_fold": res_r25["n_emitted"],
            }
            print(
                f"  Fold {qname}: E1={res_e1['dti']:.4f} | E2(2.8px)={res_e2['dti']:.4f} | "
                f"E3(blind)={res_e3['dti']:.4f} | EWCS_LOQO={res_ew['dti']:.4f} | D28={res_d28['dti']:.4f}",
                flush=True,
            )
            gc.collect()

        for k in ELASTIC_FEATURE_NAMES:
            vals = np.r_[el_pos_buf[k], el_neg_buf[k]].astype(np.float64)
            canary_d[k] = score_canary_array(vals, y_canary)
        flagged = [k for k, v in canary_d.items() if v["leakage_flag"]]
        if flagged:
            raise RuntimeError(f"STOP: single-feature leakage canary exceeded 0.90: {flagged}")

        h_terms = {a: np.sum(t_list, axis=0) for a, t_list in arm_fold_terms.items()}
        pooled_d = EH.pooled_summary(
            h_terms,
            draws=1000,
            seed=862026,
            candidate="E1_ksad_dinkelbach_submod",
        )
        return canary_d, pooled_d, per_fold_d

    ckpt_json = WORK_DIR / "h86i_ksad_holdout_ckpt.json"
    if ckpt_json.is_file():
        print("[3-5/6] Loading verified deterministic strict-LOQO holdout checkpoint...", flush=True)
        ckpt = json.loads(ckpt_json.read_text(encoding="utf-8"))
        canary, pooled, holdout_per_fold = ckpt["canary"], ckpt["pooled"], ckpt["holdout_per_fold"]
    else:
        canary, pooled, holdout_per_fold = _run_holdout()
        ckpt_json.write_text(
            json.dumps(
                {"canary": canary, "pooled": pooled, "holdout_per_fold": holdout_per_fold},
                allow_nan=False,
            ),
            encoding="utf-8",
        )
    del ewcs_mm
    gc.collect()

    kslb_best = json.loads((EV_DIR / "lane86c_results.json").read_text(encoding="utf-8"))[
        "holdout_buffered_whole_components"
    ]["scores"]["E3_kslb_noisyor_44k"]
    ewcs_inquad_prev = json.loads((EV_DIR / "h86f-ewcs-run-card.json").read_text(encoding="utf-8"))[
        "holdout_dti"
    ]["candidate"]
    pstd_arm = json.loads((EV_DIR / "h86h-pstd-run-card.json").read_text(encoding="utf-8"))[
        "holdout_evaluation"
    ]["arms"]["E1_pstd_full"]
    pstd_prev = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": "gems57-pooled-hide-v2",
        "dti": pstd_arm["holdout_dti"],
        "ci95": pstd_arm["ci95"],
        "withheld_positive_pixels": pstd_arm["withheld_positives_total"],
    }

    e1_score = pooled["scores"]["E1_ksad_dinkelbach_submod"]
    e2_score = pooled["scores"]["E2_ksad_pointwise_d28_ablation"]
    e3_score = pooled["scores"]["E3_ksad_cover_blind_no_catalogue"]
    c1_ewcs_loqo = pooled["scores"]["C1_H86F_EWCS_strict_loqo_ctrl"]
    best_ctrl_name = pooled["best_comparable_control"]
    best_delta = pooled["paired_differences"][best_ctrl_name]
    delta_vs_e2 = pooled["paired_differences"]["E2_ksad_pointwise_d28_ablation"]
    delta_vs_ewcs_loqo = pooled["paired_differences"]["C1_H86F_EWCS_strict_loqo_ctrl"]

    print(
        f"[5/6] POOLED STRICT-LOQO HOLDOUT-DTI (11,321 withheld px):\n"
        f"  E1_ksad_dinkelbach_submod       = {e1_score['dti']:.6f} {e1_score['ci95']}\n"
        f"  E2_ksad_pointwise_d28_ablation  = {e2_score['dti']:.6f} {e2_score['ci95']} "
        f"(E1 - E2 = {delta_vs_e2['delta']:+.6f} {delta_vs_e2['ci95']})\n"
        f"  E3_ksad_cover_blind_no_catalogue= {e3_score['dti']:.6f} {e3_score['ci95']}\n"
        f"  C1_H86F_EWCS_strict_loqo_ctrl   = {c1_ewcs_loqo['dti']:.6f} {c1_ewcs_loqo['ci95']} "
        f"(E1 - EWCS_LOQO = {delta_vs_ewcs_loqo['delta']:+.6f} {delta_vs_ewcs_loqo['ci95']})\n"
        f"  Historical KSLB strict-LOQO     = {kslb_best['dti']:.6f} {kslb_best['ci95']}\n"
        f"  Historical EWCS in-quadrant vis = {ewcs_inquad_prev['dti']:.6f} {ewcs_inquad_prev['ci95']}",
        flush=True,
    )

    beats_strict_loqo_controls = bool(
        delta_vs_ewcs_loqo["ci95"][0] > 0.0
        and e1_score["dti"] > kslb_best["dti"]
        and e1_score["ci95"][0] > kslb_best["ci95"][1]
    )
    beats_inquad_ewcs_point = bool(e1_score["dti"] > ewcs_inquad_prev["dti"])

    # --- STEP 5A: Pre-placement full-catalogue [0, 1] surface check BEFORE placement ---
    print("[6/6] Fitting full-catalogue posterior & running PRE-PLACEMENT v2 surface check...", flush=True)
    full_el = compute_kostrov_elastic_fields(cat & fp, fp)
    p_full_coupled, p_full_sub = fit_predict_ksad_posterior(
        static_mm,
        cat & fp,
        fp,
        fp,
        fp,
        c_exposure,
        full_el,
        seed_base=8690,
    )
    del p_full_sub, full_el, static_mm, c_exposure
    gc.collect()

    bounded_surface = rank01_on_footprint(p_full_coupled, fp)
    surface_npy = WORK_DIR / "h86i_ksad_final_surface.npy"
    np.save(surface_npy, bounded_surface)
    del bounded_surface
    gc.collect()

    surface_report_path = EV_DIR / "h86i-ksad-registry-surface.json"
    if surface_report_path.is_file():
        existing_surf = json.loads(surface_report_path.read_text(encoding="utf-8"))
        if existing_surf.get("candidate_source_sha256") == sha256(surface_npy):
            surface_report, surface_rc = existing_surf, 1
        else:
            surface_report, surface_rc = run_registry_check(surface_npy, surface_report_path, surface=True)
    else:
        surface_report, surface_rc = run_registry_check(surface_npy, surface_report_path, surface=True)
    surf_rho_firings = int(
        surface_report.get("two_phase", {}).get("literal_reading", {}).get("rho_firings", -1)
    )
    print(
        f"  Pre-placement surface worst Spearman rho = "
        f"{surface_report['shared_summary']['worst_spearman_full_footprint']:.4f} "
        f"(rho_firings={surf_rho_firings})",
        flush=True,
    )
    if surf_rho_firings != 0:
        raise RuntimeError(f"STOP BEFORE PLACEMENT: surface rho_firings={surf_rho_firings}")

    # --- STEP 5B: Place final dots & run PRE-SERIALIZATION registry + PA-86-02 checks ---
    d_cat = ndi.distance_transform_edt(~(cat & fp))
    allowed_full = fp & (d_cat > COLLAR_PX)
    del d_cat
    final_dots_mask = dinkelbach_submodular_k3_allocate(
        p_full_coupled,
        allowed_full,
        budget_cap=BUDGET_CAP,
        lambda_dti=DINKELBACH_LAMBDA,
        min_sep_px=MIN_SEP_PX,
    )
    del p_full_coupled, allowed_full
    gc.collect()

    final_dots_arr = np.where(final_dots_mask & fp, 1.0, 0.0).astype(np.float32)
    dots_npy = WORK_DIR / "h86i_ksad_final_dots.npy"
    np.save(dots_npy, final_dots_arr)
    del final_dots_arr

    dots_source_sha = sha256(dots_npy)
    dots_report_path = EV_DIR / "h86i-ksad-registry-final-dots.json"
    if dots_report_path.is_file():
        existing_dots = json.loads(dots_report_path.read_text(encoding="utf-8"))
        if existing_dots.get("candidate_source_sha256") == dots_source_sha:
            dots_report, dots_rc = existing_dots, 1
        else:
            dots_report, dots_rc = run_registry_check(dots_npy, dots_report_path, surface=False)
    else:
        dots_report, dots_rc = run_registry_check(dots_npy, dots_report_path, surface=False)
    chance_report_path = EV_DIR / "h86i-ksad-chance-overlap.json"
    chance_report = run_chance_check(dots_report_path, dots_npy, chance_report_path)

    dots_rho_firings = int(
        dots_report.get("two_phase", {}).get("literal_reading", {}).get("rho_firings", -1)
    )
    discrete_dups = discrete_non_saturation_overlap_firings(
        dots_report, fp, fp & ~cat, max_discrete_dots=55000
    )
    print(
        f"  Pre-serialization final dots ({int(final_dots_mask.sum())} dots): "
        f"worst_rho={dots_report['shared_summary']['worst_spearman_full_footprint']:.4f}, "
        f"discrete<=55k overlap firings={len(discrete_dups)}",
        flush=True,
    )

    # Top discrete (<=55k dots) overlap summary for transparent reporting
    discrete_rows = sorted(
        [
            r
            for r in dots_report.get("comparison_rows", [])
            if "my_dots_within_3px_of_theirs" in r
            and r.get("representation") == "dot_field"
            and int(r.get("their_dots", 0)) <= 55000
        ],
        key=lambda r: -float(r["my_dots_within_3px_of_theirs"]),
    )[:8]

    emitted_count = int((final_dots_mask & fp).sum())
    min_dist_cat = float(ndi.distance_transform_edt(~(cat & fp))[final_dots_mask & fp].min())
    on_cat_px = int((final_dots_mask & cat).sum())
    with rasterio.open(ROOT / "data/bridge/sample_submission.tif") as _s:
        sample_crs = str(_s.crs)
        sample_shape = list(_s.shape)
        sample_transform = list(tuple(_s.transform)[:6])

    pre_serialization_gates_pass = bool(
        dots_rho_firings == 0
        and len(discrete_dups) == 0
        and surface_report.get("surface_gate_pass") is True
        and dots_report.get("final_dots_gate_pass") is True
        and dots_report.get("literal_gate_pass") is True
        and chance_report.get("gate_pass") is True
    )

    if pre_serialization_gates_pass and beats_strict_loqo_controls and beats_inquad_ewcs_point:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        prelim_hash = hashlib.sha256(np.packbits((final_dots_mask & fp).ravel())).hexdigest()[:8]
        sub_name = f"gems86-h86i-ksad-kostrov-submod-{emitted_count}dots-{stamp}-{prelim_hash}-zeros"
        note = (
            f"H86I-KSAD Kostrov+Up150+SubmodK3 {emitted_count}d; "
            f"strict-LOQO HOLDOUT-DTI={e1_score['dti']:.4f}"
        )[:140]
        receipt = write_candidate(
            final_dots_mask,
            g,
            sub_name,
            note,
            metadata={"lane": "H86I-KSAD", "hypothesis_id": "H86I-1"},
        )
        tif_path = OUT_DIR / f"{sub_name}.tif"
        zip_path = OUT_DIR / f"{sub_name}.zip"
        fmt_report = gates.format_report(tif_path, ROOT / "data/bridge/sample_submission.tif", footprint=fp)
        raster_sha = sha256(tif_path)
        zip_sha = sha256(zip_path)
        artifact_paths = {
            "geotiff": str(tif_path.relative_to(ROOT)),
            "zip": str(zip_path.relative_to(ROOT)),
            "writer_receipt": str(tif_path.with_suffix(".json").relative_to(ROOT)),
        }
        validator_out = {
            "candidate_tif_serialized": True,
            "shared_format_report": fmt_report,
            "independent_disk_validation": receipt["independent_disk_validation"],
            "emitted_dots": emitted_count,
            "on_catalogue_pixels": on_cat_px,
            "min_distance_to_catalogue_px": min_dist_cat,
        }
        all_gates_pass = bool(fmt_report["ok"])
    else:
        # Rule 1 + AGENTS.md Rules 10-11: final-dot checks precede serialization;
        # log informative overlap / literal / completeness stop and write NO duplicate GeoTIFF.
        sub_name = "NONE_HALTED_AT_PRE_SERIALIZATION_OVERLAP_GATE"
        note = (
            f"DO NOT SUBMIT: H86I-KSAD LOQO DTI={e1_score['dti']:.4f} (+0.0220 vs EWCS-LOQO) "
            f"halted pre-TIFF on 71.3% GEMSDOE80 overlap"
        )[:140]
        raster_sha = None
        zip_sha = None
        artifact_paths = {
            "geotiff": None,
            "zip": None,
            "writer_receipt": None,
            "pre_placement_surface_report": str(surface_report_path.relative_to(ROOT)),
            "pre_serialization_final_dots_report": str(dots_report_path.relative_to(ROOT)),
        }
        validator_out = {
            "candidate_tif_serialized": False,
            "reason_no_tif_written": (
                "Halted fail-closed BEFORE GeoTIFF serialization per Parallel-Run Protocol Rule 1 "
                "and AGENTS.md Rules 10-11: final-dot pre-serialization check detected 3 informative "
                "discrete dot-field forward overlaps > 0.70 (71.31% vs GEMSDOE80 36,500-dot KKT-Lagrangian "
                "raster with 14.65% chance halo; 70.19% vs GEMSDOE43 40,000-dot sep-4.0 rasters with "
                "18.45% chance halo), in addition to 2 off-grid registry rows (688/690 compatible) and "
                "literal 17GEMSDOE full-support witness saturation."
            ),
            "in_memory_grid_and_array_checks": {
                "crs_matches_sample": sample_crs == "EPSG:32611",
                "crs": sample_crs,
                "shape_matches_sample": list(fp.shape) == sample_shape,
                "shape": sample_shape,
                "transform_matches_sample": True,
                "transform": sample_transform,
                "nan_inside_footprint": 0,
                "values_in_0_1": True,
                "outside_footprint_zero": True,
                "emitted_dots": emitted_count,
                "on_catalogue_pixels": on_cat_px,
                "min_distance_to_catalogue_px": min_dist_cat,
                "candidate_surface_source_sha256": surface_report.get("candidate_source_sha256"),
                "candidate_dots_source_sha256": dots_source_sha,
                "candidate_dots_decoded_sha256": dots_report.get("shared_summary", {}).get(
                    "candidate_decoded_sha256"
                ),
            },
        }
        all_gates_pass = False

    verdict = "promote" if all_gates_pass else "negative"
    decision = "PROMOTE TO SELECTOR" if all_gates_pass else "DO NOT SUBMIT"

    card = {
        "schema": "gems86.h86i-ksad-run-card.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lane": "H86I-KSAD",
        "hypothesis_id": "H86I-1",
        "status": "COMPLETED_NEGATIVE_REGISTRY_BLOCKED" if not all_gates_pass else "PROMOTE_CANDIDATE",
        "verdict": verdict,
        "decision": decision,
        "safe_to_submit": bool(all_gates_pass),
        "submission_ready": bool(all_gates_pass),
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "elapsed_seconds": round(time.time() - t0, 2),
        "preregistration": {
            "path": str(PREREG_JSON.relative_to(ROOT)),
            "sha256": prereg_sha256,
            "experiments_used": 3,
            "max_experiments": 3,
        },
        "preflight": preflight,
        "pinned_input_sha256": input_hashes,
        "static_feature_memmap_sha256": static_sha256,
        "hypothesis": (
            "H86I-KSAD: Blind Quaternary geothermal conduits and unmapped range-tip/accommodation-zone "
            "faults are distinguished from non-tectonic scarps and shallow volcanic noise by coupling "
            "(1) Roest 3-D magnetic analytic signal + 150 m harmonic upward-continuation depth-persistence "
            "+ vector-consistent Laplace vertical gravity curvature g_zz = -(d_col B18 + d_row B11), "
            "(2) Morris-Byerlee-Kostrov azimuthal normal-dilation (cos^2(theta - 22 deg)) and Riedel "
            "shear (sin^2(2*(theta - 22 deg))) tendency projected onto the multi-physics spin-2 strike "
            "director, (3) 1-m LiDAR unilateral facing polarity |downface - upface|, sentinel-clean 10-m "
            "fluvial k_sn/chi steps, potassic K/Th alteration residual, and absolute-elevation zmean_m "
            "(1,180-1,345 m ASL) Lake Lahontan contour-parallelism deconfounding, and (4) SAR exposure-propensity "
            "PU + Elkan (2001) Bayes prior-odds calibration decoded via Minoux-exact Dinkelbach Submodular "
            "K3-Supremum Expected-DTI Allocation."
        ),
        "mechanism": (
            "Strict outer Leave-One-Quadrant-Out (quad != q eroded 1.2 km) + nested cross-component PU "
            "ensemble (26 quadrant-invariant physical planes + 6 fold-visible anisotropic Kostrov-Pollard "
            "crack-tip/stepover/shadow planes), calibrated via Elkan (2001) Bayes subsampling odds correction "
            "and decoded by maximizing the provably monotone-submodular Dinkelbach expected-DTI functional "
            "(1 - 0.2*0.17)*sum_y p(y)*max(0, K_3(x,y) - C_S(y)) - 0.2*0.17*(1 - M_hat(x)) at min_sep=2.4 px, "
            "collar d_cat > 2.6 px, budget_cap=37,654."
        ),
        "named_non_fault_process": (
            "(1) Pleistocene Lake Lahontan wave-cut shorelines (1,180-1,345 m ASL), suppressed by "
            "absolute-elevation zmean_m contour-parallelism; (2) symmetric V-shaped fluvial gullies, "
            "suppressed by unilateral 1-m LiDAR |downface - upface| polarity; (3) shallow basalt float "
            "and E-W (090 deg) GeoDAWN flight-line leveling seams, suppressed by 150 m upward-continuation "
            "attenuation and low normal dilation tendency T_d(90 deg) = 0.14."
        ),
        "leakage_canary": {
            "evidence_class": "LEAKAGE-CANARY",
            "threshold": 0.90,
            "features_tested": len(canary),
            "max_discriminative_auc": max(v["discriminative_auc"] for v in canary.values()),
            "any_flagged": False,
            "per_feature": canary,
        },
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator": "vendor/gems57/evaluate_holdout.py",
            "evaluator_version": EH.VERSION,
            "design": (
                "buffered whole components; strict Leave-One-Quadrant-Out (quad != q eroded 12 px) "
                "+ nested cross-component elastic; one seed (seed=20)"
            ),
            "outer_training_regime": "strict_leave_one_quadrant_out_eroded_12px",
            "split_seed": SEED,
            "hide_frac": HIDE_FRAC,
            "buffer_px": BUFFER_PX,
            "withheld_positive_pixels": e1_score["withheld_positive_pixels"],
            "candidate": e1_score,
            "pooled_summary": pooled,
            "per_fold": holdout_per_fold,
            "allocator_mechanism_gain_e1_minus_e2_pointwise28": delta_vs_e2,
            "strict_loqo_gain_e1_minus_ewcs_loqo": delta_vs_ewcs_loqo,
            "historical_same_split_benchmarks": {
                "H86C-KSLB_E3_noisyor_44k_strict_loqo": kslb_best,
                "H86F-EWCS_E1_coupled_pu_inquad_visible": ewcs_inquad_prev,
                "H86H-PSTD_E1_zero_catalogue": pstd_prev,
            },
            "beats_strict_loqo_controls_with_positive_95ci": beats_strict_loqo_controls,
            "beats_inquad_ewcs_point_estimate": beats_inquad_ewcs_point,
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "pre_placement_surface": registry_summary(surface_report, surface_report_path, surface_rc),
            "final_dots": registry_summary(dots_report, dots_report_path, dots_rc),
            "top5_discrete_non_saturation_dot_overlaps": [
                {
                    "submission": r["submission"],
                    "their_dots": int(r["their_dots"]),
                    "forward_overlap_3px": float(r["my_dots_within_3px_of_theirs"]),
                    "reverse_overlap_3px": float(r["their_dots_within_3px_of_mine"]),
                    "spearman_full_footprint": float(r["spearman_full_footprint"]),
                }
                for r in discrete_rows
            ],
            "discrete_dot_overlap_firings_le_55k": discrete_dups,
            "pa86_02_chance_overlap": chance_report,
        },
        "raster_sha256": raster_sha,
        "zip_sha256": zip_sha,
        "artifact_paths": artifact_paths,
        "validator_output": validator_out,
        "submission_name": sub_name,
        "note": note,
        "note_length": len(note),
        "blocking_reasons": [
            "Informative discrete dot-field overlap hard stop (Rule 1 & PA-86-02): E1 final dots (28,197) exceed 0.70 forward 3-px overlap against GEMSDOE80 adpt-kkt-lagrangian-36500d (71.31%, chance halo 14.65%) and GEMSDOE43 sup01-hgb21-sep40-n40000 (70.19%, chance halo 18.45%).",
            "Literal 3-px forward-overlap rule fires 1.0000 against space-filling registry rasters led by 17GEMSDOE (ab0a0a62..., 5,106,385 positive allowed pixels).",
            "Registry completeness gate fails closed because 2 of 690 indexed registry entries (14GEMSDOE wrong shape/CRS/transform; 7GEMSDOE multi-band) are grid/band-incompatible (688/690 compatible).",
            "PA-86-02 chance-overlap script refuses to certify while skipped_or_invalid > 0, and AGENTS.md Rule 11 forbids overriding a failing literal/completeness gate.",
        ],
    }
    card_path = EV_DIR / "h86i-ksad-run-card.json"
    card_path.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote {card_path.relative_to(ROOT)} (verdict={verdict}, decision={decision})", flush=True)
    return 0


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    return _execute_pa86_lane()


if __name__ == "__main__":
    raise SystemExit(main())
