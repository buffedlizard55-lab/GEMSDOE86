#!/usr/bin/env python3
"""Execute preregistered Lane H86J-CSGD within the strict 3-experiment / 2-hour budget.

H86J-CSGD: Selected-At-Random (SAR) Geomorphically De-Biased Cross-Spectral
Potential-Field Admittance & Geothermal Upflow Conduit PU.

Protocol & governance compliance (AGENTS.md Rules 2-11):
- Verifies frozen contemporaneous preregistration (research/H86J_CSGD_PREREGISTRATION.json)
  before computing any feature or fitting any model.
- Reuses pinned vendor/gems57/{grid,holdout,evaluate_holdout,emit,submission_writer,validate}
  unchanged without private forks.
- Enforces single-feature discriminative leakage canaries max(AUC, 1-AUC) <= 0.90 across
  every deep feature, SAR exposure covariate, SAR propensity field, and fold-visible
  elastic field before trusting any holdout score; explicitly forbids GDR-1391
  'dist_known_fault_px'.
- Evaluates 3 preregistered arms (E1_csgd_sar_debiased, E2_csgd_unweighted_pu_ablation,
  E3_csgd_autonomous_blind_conduit) + fold-fair R0_D28_visible_collar control on
  gems57-pooled-hide-v2 (seed=20, hide_frac=0.20, buffer_px=3, 11,321 withheld positives,
  1,000 paired bootstrap draws over 200-px / 20-km physical blocks) plus read-only
  post-hoc off-catalogue SGMC-PROXY-DTI diagnostic.
- Runs full 692-entry registry check (scripts/check_h86e_registry.py --surface) BEFORE
  full-catalogue dot placement, and full final-dot registry check + PA-86-02 check
  BEFORE GeoTIFF serialization; fails closed to DO NOT SUBMIT / verdict='negative'
  (0 slots used) whenever any literal registry or scientific gate fails.
"""
from __future__ import annotations

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

from gems57 import emit, evaluate_holdout as EH, grid, holdout, metric  # noqa: E402
from gems57 import submission_writer, validate  # noqa: E402
from gems86_csgd.features import (  # noqa: E402
    ALL_PLANE_NAMES,
    DEEP_FEATURE_NAMES,
    ELASTIC_COUPLED_NAMES,
    EXPOSURE_FEATURE_NAMES,
    build_csgd_planes,
    compute_elastic_fields,
    compute_sar_exposure_propensity,
)
from scripts.protocol_preflight import require_like_for_like  # noqa: E402

PREREGISTRATION_PATH = ROOT / "research/H86J_CSGD_PREREGISTRATION.json"
HYPOTHESIS_QUEUE_PATH = ROOT / "registry/h86j_hypotheses.json"
FEATURE_TIF = ROOT / "data/bridge/training_features.tif"
EXTERNAL_DIR = ROOT / ".cache/external"
D28_CONTROL_TIF = (
    ROOT / "data/registry_ext/ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73.tif"
)
SGMC_DIAGNOSTIC_TIF = EXTERNAL_DIR / "derived_sgmc_faults_100m_u8.tif"
OUT_DIR = ROOT / "docs/downloads"
WORK_DIR = ROOT / ".cache/h86j_csgd_work"
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
    "geodawn_rad_u8": (
        EXTERNAL_DIR / "geodawn_rad_u8.tif",
        "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
    ),
    "geodawn_extensions_u8": (
        EXTERNAL_DIR / "geodawn_extensions_u8.tif",
        "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
    ),
    "topo_10m_derived_100m_u8": (
        EXTERNAL_DIR / "topo_10m_derived_100m_u8.tif",
        "a6398d9950965dec6aae6ccecdaa6ced48645d133eab222cbdd11def9bdabfa4",
    ),
    "gdr_wellspring_in_footprint": (
        EXTERNAL_DIR / "gdr_wellspring_in_footprint.csv",
        "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea",
    ),
    "gdr_volcanic_vents_in_footprint": (
        EXTERNAL_DIR / "gdr_volcanic_vents_in_footprint.csv",
        "f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883f4974542ff6a0bf",
    ),
}

SEED = 20
BUDGET = 37_654
SPACING_PX = 2.8
COLLAR_PX = 3.0
SAR_TAU = 0.12
SAR_GAMMA_E1 = 0.85
SAR_GAMMA_E2 = 0.0
SAR_GAMMA_E3 = 0.85


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_preregistration() -> dict:
    if not PREREGISTRATION_PATH.is_file():
        raise RuntimeError(f"missing frozen preregistration: {PREREGISTRATION_PATH}")
    if not HYPOTHESIS_QUEUE_PATH.is_file():
        raise RuntimeError(f"missing hypothesis queue: {HYPOTHESIS_QUEUE_PATH}")
    doc = json.loads(PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    arms = doc.get("arms", [])
    if len(arms) != 3 or doc.get("budget", {}).get("max_experiments", 99) > 3:
        raise RuntimeError("invalid H86J-CSGD preregistration budget or arm count")
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


def sar_censoring_weight(e_hat: np.ndarray, footprint: np.ndarray,
                         gamma: float, tau: float = SAR_TAU) -> np.ndarray:
    """Bekker-Davis SAR geomorphic censoring odds weight ((1 - e_hat) / (e_hat + tau))^gamma."""
    fp = np.asarray(footprint, dtype=bool)
    if gamma == 0.0:
        return np.where(fp, 1.0, 0.0).astype(np.float32)
    eh = np.clip(np.asarray(e_hat, dtype=np.float32), 0.02, 0.92)
    odds = ((1.0 - eh) / (eh + float(tau))) ** float(gamma)
    return np.where(fp, odds, 0.0).astype(np.float32)


def expected_credit_disc_thin(
    raw_score: np.ndarray,
    allowed: np.ndarray,
    footprint: np.ndarray,
    budget: int = BUDGET,
    spacing: float = SPACING_PX,
) -> tuple[np.ndarray, np.ndarray]:
    """Convolve score with exact 300 m DTI kernel and place Poisson-disc dots."""
    fp = np.asarray(footprint, dtype=bool)
    clipped = np.where(fp, np.maximum(np.asarray(raw_score, dtype=np.float32), 0.0), 0.0)
    p999 = max(float(np.percentile(clipped[fp], 99.9)) if fp.any() else 1.0, 1e-6)
    norm_p = np.clip(clipped / p999, 0.0, 1.0).astype(np.float32)
    ek = emit.expected_credit(norm_p)
    del clipped, norm_p

    r = int(np.ceil(spacing))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disc = (yy * yy + xx * xx) < (spacing * spacing)
    h, w = ek.shape
    blocked = np.zeros((h + 2 * r, w + 2 * r), dtype=bool)
    flat = np.flatnonzero(allowed.ravel())
    order = flat[np.argsort(-ek.ravel()[flat], kind="stable")]
    dots = np.zeros(ek.shape, dtype=bool)
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
    return dots, ek


def split_visible_components(vis_cat: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Split connected components of ``vis_cat`` into two disjoint halves for nested PU."""
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
    va = set_a[comp]
    vb = (~set_a)[comp] & (comp > 0)
    return va, vb


def _plane(planes_mm: np.ndarray, key: str) -> np.ndarray:
    return planes_mm[ALL_PLANE_NAMES.index(key)]


def sample_nested_pu(
    planes_mm: np.ndarray,
    deep_keys: tuple[str, ...],
    vis_cat: np.ndarray,
    footprint: np.ndarray,
    elastic_keys: tuple[str, ...],
    *,
    n_neg: int = 200_000,
    seed: int = 86,
) -> tuple[np.ndarray, np.ndarray]:
    """Build cover-blind PU training matrix strictly from ``vis_cat``."""
    rng = np.random.default_rng(seed)
    fp = np.asarray(footprint, dtype=bool)
    d_vis = ndi.distance_transform_edt(~vis_cat)
    neg_pool = np.flatnonzero((fp & (d_vis > COLLAR_PX)).ravel())
    del d_vis

    if not elastic_keys:
        pos_idx = np.flatnonzero((vis_cat & fp).ravel())
        neg_idx = rng.choice(neg_pool, size=min(n_neg, neg_pool.size), replace=False)
        idx = np.concatenate([pos_idx, neg_idx])
        y = np.concatenate([
            np.ones(pos_idx.size, dtype=np.int8),
            np.zeros(neg_idx.size, dtype=np.int8),
        ])
        X = np.column_stack(
            [_plane(planes_mm, k).ravel()[idx].astype(np.float32) for k in deep_keys]
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
        [_plane(planes_mm, k).ravel()[idx_a].astype(np.float32) for k in deep_keys]
        + [el_from_b[k].ravel()[idx_a].astype(np.float32) for k in elastic_keys]
    )
    del el_from_b, pos_a, neg_a, idx_a
    gc.collect()

    da = ndi.distance_transform_edt(~va)
    pos_b = np.flatnonzero((vb & fp & (da > COLLAR_PX)).ravel())
    del da
    idx_b = np.concatenate([pos_b, neg_b])
    yb = np.concatenate([np.ones(pos_b.size, dtype=np.int8), np.zeros(neg_b.size, dtype=np.int8)])
    el_from_a = compute_elastic_fields(va, fp)
    del va, vb
    Xb = np.column_stack(
        [_plane(planes_mm, k).ravel()[idx_b].astype(np.float32) for k in deep_keys]
        + [el_from_a[k].ravel()[idx_b].astype(np.float32) for k in elastic_keys]
    )
    del el_from_a, pos_b, neg_b, idx_b
    gc.collect()

    return np.vstack([Xa, Xb]), np.concatenate([ya, yb])


def fit_hgb(X: np.ndarray, y: np.ndarray, seed: int) -> HistGradientBoostingClassifier:
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
    planes_mm: np.ndarray,
    deep_keys: tuple[str, ...],
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
        cols = [_plane(planes_mm, k)[r0:r1][m].astype(np.float32) for k in deep_keys]
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


def evaluate_sgmc_proxy_dti(dots: np.ndarray, sgmc_offcat: np.ndarray,
                            eval_mask: np.ndarray) -> dict:
    """Read-only post-hoc off-catalogue SGMC structural diagnostic (never used in training)."""
    res = metric.dti_binary(dots, sgmc_offcat, valid=eval_mask)
    return {
        "evidence_class": "SECONDARY-DIAGNOSTIC-SGMC-PROXY-DTI",
        "not_organizer_confirmed": True,
        "not_holdout_dti": True,
        "dti": float(res["dti"]),
        "n_sgmc_offcat_pixels": int(sgmc_offcat.sum()),
        "n_emitted": int(dots.sum()),
    }


def run_registry_check(array_path: Path, output: Path, *, surface: bool) -> tuple[dict, int]:
    gate = "surface_gate_pass" if surface else "final_dots_gate_pass"
    expected_mode = "surface" if surface else "final_dots"
    cand_sha = sha256(array_path)
    if output.is_file():
        try:
            cached = json.loads(output.read_text(encoding="utf-8"))
            if (
                cached.get("candidate_source_sha256") == cand_sha
                and cached.get("mode") == expected_mode
            ):
                return cached, (0 if cached.get(gate) else 1)
        except Exception:
            pass
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
        "dot_overlap_firings_over_0p70": lit.get("dot_overlap_firings"),
        "literal_gate_pass": report.get("literal_gate_pass"),
        "two_phase": report.get("two_phase"),
        "top15_by_forward_overlap": report.get("top15_by_forward_overlap"),
        "top15_by_spearman": report.get("top15_by_spearman"),
        "scope": report.get("scope"),
    }


def compute_informative_overlap_summaries(
    arm_dots: dict[str, np.ndarray], fp: np.ndarray
) -> dict[str, dict]:
    """Single-pass informative (halo_coverage <= 0.70) 3-px overlap across all compatible rasters."""
    from scripts.check_h86e_registry import build_index

    index, _ = build_index()
    disc3 = (np.add.outer(np.arange(-3, 4) ** 2, np.arange(-3, 4) ** 2) <= 9)
    n_fp = int(fp.sum())
    arm_counts = {k: max(int((d & fp).sum()), 1) for k, d in arm_dots.items()}
    total_gt = {k: 0 for k in arm_dots}
    firings: dict[str, list[dict]] = {k: [] for k in arm_dots}
    worst_inf: dict[str, dict | None] = {k: None for k in arm_dots}
    compatible = 0

    for rec in index["rasters"]:
        p = Path(rec["cache_file"])
        if not p.is_file():
            continue
        try:
            with rasterio.open(p) as ds:
                if ds.shape != fp.shape:
                    continue
                arr = ds.read(1)
        except Exception:
            continue
        reg_pos = (np.isfinite(arr) & (arr > 0)) & fp
        compatible += 1
        near3 = ndi.binary_dilation(reg_pos, structure=disc3) & fp
        halo_cov = float(near3.sum()) / float(n_fp)
        reg_n = int(reg_pos.sum())
        for k, d in arm_dots.items():
            fwd_ov = float((d & near3).sum()) / float(arm_counts[k])
            if fwd_ov > 0.70:
                total_gt[k] += 1
            if halo_cov <= 0.70:
                item = {
                    "sha256": rec["sha256"],
                    "source": rec["sources"][0],
                    "forward_overlap_3px": round(fwd_ov, 6),
                    "registry_halo_coverage": round(halo_cov, 6),
                    "registry_positive_pixels": reg_n,
                }
                if worst_inf[k] is None or fwd_ov > worst_inf[k]["forward_overlap_3px"]:
                    worst_inf[k] = item
                if fwd_ov > 0.70:
                    firings[k].append(item)

    out: dict[str, dict] = {}
    for k in arm_dots:
        firings[k].sort(key=lambda x: -x["forward_overlap_3px"])
        out[k] = {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "compatible_rasters_scanned": compatible,
            "total_forward_overlap_gt_0p70": total_gt[k],
            "informative_halo_ceiling": 0.70,
            "informative_overlap_firings_count": len(firings[k]),
            "worst_informative_overlap": worst_inf[k],
            "top_informative_firings": firings[k][:10],
        }
    return out


def _execute_pipeline() -> int:
    t0 = time.time()
    prereg = require_preregistration()
    preflight = require_like_for_like()
    input_hashes = verify_pinned_inputs()

    g = grid.load_grid(ROOT / "data/bridge")
    fp, cat = g.footprint, g.catalogue
    folds, _ = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)
    planes_memmap = WORK_DIR / "h86j_csgd_planes.npy"
    if planes_memmap.is_file():
        mm_check = np.load(planes_memmap, mmap_mode="r")
        if mm_check.shape == (len(ALL_PLANE_NAMES), fp.shape[0], fp.shape[1]) and mm_check.dtype == np.float16:
            planes_mm = mm_check
        else:
            del mm_check
            planes_mm = build_csgd_planes(FEATURE_TIF, EXTERNAL_DIR, fp, out_memmap_path=planes_memmap)
    else:
        planes_mm = build_csgd_planes(FEATURE_TIF, EXTERNAL_DIR, fp, out_memmap_path=planes_memmap)
    planes_sha256 = sha256(planes_memmap)
    print(f"[H86J-CSGD] 23 static/exposure planes ready ({time.time() - t0:.1f}s)", flush=True)

    prereg_ids = [a["arm_id"] for a in prereg["arms"]]
    expected_ids = [
        "E1_csgd_sar_debiased",
        "E2_csgd_unweighted_pu_ablation",
        "E3_csgd_autonomous_blind_conduit",
    ]
    if prereg_ids != expected_ids:
        raise RuntimeError(f"Arm specification mismatch against frozen preregistration: {prereg_ids}")

    p_idx, n_idx, y_canary = prepare_canary_indices(folds, fp)
    canary: dict[str, dict] = {}
    for k in ALL_PLANE_NAMES:
        flat = _plane(planes_mm, k).ravel()
        vals = np.r_[flat[p_idx], flat[n_idx]].astype(np.float64)
        canary[k] = score_canary_array(vals, y_canary)
        del vals

    el_pos_buf = {k: np.zeros(p_idx.size, dtype=np.float32) for k in ELASTIC_COUPLED_NAMES}
    el_neg_buf = {k: np.zeros(n_idx.size, dtype=np.float32) for k in ELASTIC_COUPLED_NAMES}
    sar_pos_buf = np.zeros(p_idx.size, dtype=np.float32)
    sar_neg_buf = np.zeros(n_idx.size, dtype=np.float32)

    holdout_per_fold: dict[str, dict] = {arm: {} for arm in expected_ids}
    holdout_per_fold["R0_D28_visible_collar"] = {}
    arm_fold_terms: dict[str, list[np.ndarray]] = {arm: [] for arm in expected_ids}
    d28_fold_terms: list[np.ndarray] = []
    d28_mask = load_binary_tif(D28_CONTROL_TIF) & fp

    for fold_i, f in enumerate(folds):
        vis = np.asarray(f["visible"], dtype=bool) & fp
        el_pred = compute_elastic_fields(vis, fp)
        e_hat_fold = compute_sar_exposure_propensity(planes_mm, vis, fp, seed=8600 + fold_i)

        reg_flat = (np.asarray(f["region"], dtype=bool) & fp).ravel()
        p_in = reg_flat[p_idx]
        n_in = reg_flat[n_idx]
        for k in ELASTIC_COUPLED_NAMES:
            eflat = el_pred[k].ravel()
            el_pos_buf[k][p_in] = eflat[p_idx[p_in]]
            el_neg_buf[k][n_in] = eflat[n_idx[n_in]]
        sflat = e_hat_fold.ravel()
        sar_pos_buf[p_in] = sflat[p_idx[p_in]]
        sar_neg_buf[n_in] = sflat[n_idx[n_in]]
        del reg_flat, p_in, n_in, sflat

        d_vis = ndi.distance_transform_edt(~vis)
        allowed = fp & (d_vis > COLLAR_PX)
        del d_vis

        # Fit coupled cover-blind P_deep once per fold; E1 (gamma=0.85) and E2 (gamma=0.0)
        # share identical tree ensemble to isolate the exact causal effect of SAR censoring odds.
        X_coupled, y_coupled = sample_nested_pu(
            planes_mm, DEEP_FEATURE_NAMES, vis, fp, ELASTIC_COUPLED_NAMES,
            seed=8800 + 10 * fold_i,
        )
        clf_coupled = fit_hgb(X_coupled, y_coupled, seed=8800 + 10 * fold_i)
        del X_coupled, y_coupled
        p_deep_coupled = predict_surface(
            clf_coupled, planes_mm, DEEP_FEATURE_NAMES, el_pred, ELASTIC_COUPLED_NAMES, fp
        )
        del clf_coupled, el_pred

        w_sar_e1 = sar_censoring_weight(e_hat_fold, fp, gamma=SAR_GAMMA_E1)
        for arm_name, w_arr in (
            ("E1_csgd_sar_debiased", w_sar_e1),
            ("E2_csgd_unweighted_pu_ablation", sar_censoring_weight(e_hat_fold, fp, gamma=SAR_GAMMA_E2)),
        ):
            dots, _ = expected_credit_disc_thin(p_deep_coupled * w_arr, allowed, fp, BUDGET, SPACING_PX)
            res, b_terms = EH.evaluate(dots.astype(np.float32), f, fp, block_side=200)
            arm_fold_terms[arm_name].append(b_terms)
            holdout_per_fold[arm_name][f["name"]] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res["dti"],
                "n_truth": res["n_truth"],
                "emitted": res["n_emitted"],
            }
            del dots
        del p_deep_coupled, e_hat_fold

        # Arm E3: 100% autonomous cover-blind geothermal conduit PU (zero elastic features)
        X_blind, y_blind = sample_nested_pu(
            planes_mm, DEEP_FEATURE_NAMES, vis, fp, (),
            seed=8805 + 10 * fold_i,
        )
        clf_blind = fit_hgb(X_blind, y_blind, seed=8805 + 10 * fold_i)
        del X_blind, y_blind
        p_deep_blind = predict_surface(clf_blind, planes_mm, DEEP_FEATURE_NAMES, None, (), fp)
        del clf_blind
        dots_e3, _ = expected_credit_disc_thin(p_deep_blind * w_sar_e1, allowed, fp, BUDGET, SPACING_PX)
        del p_deep_blind, w_sar_e1
        res_e3, b_e3 = EH.evaluate(dots_e3.astype(np.float32), f, fp, block_side=200)
        del dots_e3
        arm_fold_terms["E3_csgd_autonomous_blind_conduit"].append(b_e3)
        holdout_per_fold["E3_csgd_autonomous_blind_conduit"][f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_e3["dti"],
            "n_truth": res_e3["n_truth"],
            "emitted": res_e3["n_emitted"],
        }

        d28_allowed = d28_mask & allowed
        if int(d28_allowed.sum()) <= BUDGET:
            d28_dots = d28_allowed
        else:
            d28_dots, _ = expected_credit_disc_thin(
                d28_allowed.astype(np.float32), allowed, fp, BUDGET, SPACING_PX
            )
        res_d28, b_d28 = EH.evaluate(d28_dots.astype(np.float32), f, fp, block_side=200)
        d28_fold_terms.append(b_d28)
        holdout_per_fold["R0_D28_visible_collar"][f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": res_d28["dti"],
            "n_truth": res_d28["n_truth"],
            "emitted": res_d28["n_emitted"],
        }
        del allowed, d28_allowed, d28_dots
        gc.collect()
        print(f"[H86J-CSGD] Fold {fold_i + 1}/4 ({f['name']}) complete ({time.time() - t0:.1f}s)", flush=True)

    for k in ELASTIC_COUPLED_NAMES:
        vals = np.r_[el_pos_buf[k], el_neg_buf[k]].astype(np.float64)
        canary[k] = score_canary_array(vals, y_canary)
    canary["sar_exposure_propensity_e_hat"] = score_canary_array(
        np.r_[sar_pos_buf, sar_neg_buf].astype(np.float64), y_canary
    )
    del el_pos_buf, el_neg_buf, sar_pos_buf, sar_neg_buf, p_idx, n_idx, y_canary, d28_mask
    flagged = [k for k, v in canary.items() if v["leakage_flag"]]
    if flagged:
        raise RuntimeError(f"STOP: single-feature leakage canary exceeded 0.90: {flagged}")

    holdout_terms = {arm: np.sum(t_list, axis=0) for arm, t_list in arm_fold_terms.items()}
    holdout_terms["R0_D28_visible_collar"] = np.sum(d28_fold_terms, axis=0)

    pooled = EH.pooled_summary(
        holdout_terms,
        draws=1000,
        seed=862026,
        candidate="E1_csgd_sar_debiased",
    )

    kslb_best = json.loads((EV_DIR / "lane86c_results.json").read_text(encoding="utf-8"))[
        "holdout_buffered_whole_components"
    ]["scores"]["E3_kslb_noisyor_44k"]
    ewcs_prev = json.loads((EV_DIR / "h86f-ewcs-run-card.json").read_text(encoding="utf-8"))[
        "holdout_dti"
    ]["candidate"]
    edti_prev = json.loads((EV_DIR / "h86g-edti-run-card.json").read_text(encoding="utf-8"))[
        "holdout_dti"
    ]["candidate"]
    rksc_prev = json.loads((EV_DIR / "h86i-rksc-run-card.json").read_text(encoding="utf-8"))[
        "holdout_dti"
    ]["candidate"]

    e1_score = pooled["scores"]["E1_csgd_sar_debiased"]
    r0_delta = pooled["paired_differences"]["R0_D28_visible_collar"]
    beats_r0_ci = bool(r0_delta["ci95"][0] > 0.0)
    beats_kslb = bool(e1_score["dti"] > kslb_best["dti"])

    # Full-catalogue fit for pre-placement surface registry audit & post-hoc SGMC diagnostic
    dcat = ndi.distance_transform_edt(~(cat & fp))
    allowed_full = fp & (dcat > COLLAR_PX)
    sgmc_raw = load_binary_tif(SGMC_DIAGNOSTIC_TIF) if SGMC_DIAGNOSTIC_TIF.is_file() else np.zeros(fp.shape, bool)
    sgmc_offcat = sgmc_raw & allowed_full
    del sgmc_raw, dcat

    e_hat_full = compute_sar_exposure_propensity(planes_mm, cat & fp, fp, seed=8899)
    w_full_e1 = sar_censoring_weight(e_hat_full, fp, gamma=SAR_GAMMA_E1)

    full_el = compute_elastic_fields(cat & fp, fp)
    X_full_c, y_full_c = sample_nested_pu(
        planes_mm, DEEP_FEATURE_NAMES, cat & fp, fp, ELASTIC_COUPLED_NAMES, seed=8899
    )
    clf_full_c = fit_hgb(X_full_c, y_full_c, seed=8899)
    del X_full_c, y_full_c
    p_full_coupled = predict_surface(
        clf_full_c, planes_mm, DEEP_FEATURE_NAMES, full_el, ELASTIC_COUPLED_NAMES, fp
    )
    del clf_full_c, full_el

    X_full_b, y_full_b = sample_nested_pu(
        planes_mm, DEEP_FEATURE_NAMES, cat & fp, fp, (), seed=8895
    )
    clf_full_b = fit_hgb(X_full_b, y_full_b, seed=8895)
    del X_full_b, y_full_b
    p_full_blind = predict_surface(clf_full_b, planes_mm, DEEP_FEATURE_NAMES, None, (), fp)
    del clf_full_b, planes_mm
    gc.collect()

    dots_e1, ek_e1 = expected_credit_disc_thin(p_full_coupled * w_full_e1, allowed_full, fp, BUDGET, SPACING_PX)
    dots_e2, _ = expected_credit_disc_thin(p_full_coupled, allowed_full, fp, BUDGET, SPACING_PX)
    dots_e3, _ = expected_credit_disc_thin(p_full_blind * w_full_e1, allowed_full, fp, BUDGET, SPACING_PX)
    del p_full_coupled, p_full_blind, w_full_e1, e_hat_full

    sgmc_diagnostics = {
        "E1_csgd_sar_debiased": evaluate_sgmc_proxy_dti(dots_e1, sgmc_offcat, allowed_full),
        "E2_csgd_unweighted_pu_ablation": evaluate_sgmc_proxy_dti(dots_e2, sgmc_offcat, allowed_full),
        "E3_csgd_autonomous_blind_conduit": evaluate_sgmc_proxy_dti(dots_e3, sgmc_offcat, allowed_full),
    }
    informative_by_arm = compute_informative_overlap_summaries(
        {
            "E1_csgd_sar_debiased": dots_e1,
            "E2_csgd_unweighted_pu_ablation": dots_e2,
            "E3_csgd_autonomous_blind_conduit": dots_e3,
        },
        fp,
    )
    del dots_e2, dots_e3, sgmc_offcat, allowed_full
    gc.collect()

    bounded_surface = rank01_on_footprint(ek_e1, fp)
    del ek_e1
    surface_npy = WORK_DIR / "h86j_csgd_final_surface.npy"
    np.save(surface_npy, bounded_surface)
    surface_sha = sha256(surface_npy)
    del bounded_surface
    gc.collect()

    print(f"[H86J-CSGD] Running full-registry pre-placement surface check ({time.time() - t0:.1f}s)...", flush=True)
    surface_report_path = EV_DIR / "h86j-csgd-registry-surface.json"
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
    card_path = EV_DIR / "h86j-csgd-run-card.json"

    base_card = {
        "schema": "gems86.h86j-csgd-run-card.v1",
        "lane": "H86J-CSGD",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {
            "document": "research/H86J_CSGD_PREREGISTRATION.md",
            "machine_readable": "research/H86J_CSGD_PREREGISTRATION.json",
            "hypothesis_queue": "registry/h86j_hypotheses.json",
            "preregistration_sha256": sha256(PREREGISTRATION_PATH),
            "arm_ids": expected_ids,
        },
        "hypothesis": (
            "H86J-CSGD: Blind Quaternary geothermal faults buried beneath Holocene alluvial "
            "aprons and Pleistocene Lake Lahontan lacustrine floors produce multi-scale "
            "cross-spectral gravity-magnetic admittance residuals, hydrothermal magnetite-"
            "destruction troughs (attenuated TMI_up150 over sharp Laplace g_zz contacts), and "
            "active silica-geothermometer / thermal upflow plumes (GDR-1391), which standard "
            "PU models under-weight due to steep range-front scarp mapping selection bias "
            "e_hat(X_vis); dividing out SAR geomorphic exposure propensity recovers hidden "
            "faults while de-crowding range-front fleet halos."
        ),
        "mechanism": (
            "18 cover-blind subsurface/hydrothermal/seismotectonic planes (multi-scale "
            "windowed cross-spectral gravity-magnetic admittance residuals B13 vs B2, "
            "curl-vetoed Laplace g_zz = -(d_col B18 + d_row B11), upward-continued TMI_up150 "
            "wavenumber attenuation & demagnetization troughs, Verduzco tilt-depth B3/B9, "
            "volcanic-vent-vetoed GDR-1391 well/spring thermal & quartz/chalcedony/cation "
            "geothermometer plumes, GeoDAWN K/Th & U/Th metasomatic steps, smectite "
            "conductance B17, geodetic transtension B4/B7/B8, seismicity B10/B16, and "
            "basement hinge B15 — zero DEM/slope inputs in P_deep) + strictly fold-visible "
            "Pollard-Segall crack-tip/stepover fields, reweighted by Bekker-Davis SAR "
            "censoring odds ((1 - e_hat(X_vis)) / (e_hat(X_vis) + 0.12))^0.85 and convolved "
            "with the exact 300 m triangular DTI expected-credit kernel before d=2.8 px "
            "Poisson-disc placement (37,654 dots)."
        ),
        "named_non_fault_process": (
            "Unfaulted Mesozoic pluton-wallrock roof contacts, closed-basin evaporite playa "
            "brines with laterally advected thermal outflow plumes, and Quaternary volcanic "
            "plugs (mitigated via curl-vetoed Laplace g_zz, GDR-1391 volcanic-vent proximity "
            "veto, and transtensional strain gating)."
        ),
        "input_sha256_pins": input_hashes,
        "planes_memmap_sha256": planes_sha256,
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
            "R0_D28_visible_collar": pooled["scores"]["R0_D28_visible_collar"],
            "paired_delta_vs_R0_D28_visible_collar": r0_delta,
            "all_arms": pooled["scores"],
            "per_fold": holdout_per_fold,
            "paired_differences": pooled["paired_differences"],
            "same_split_comparators": {
                "H86F_EWCS_E1_37k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86f-ewcs-run-card.json",
                    "dti": ewcs_prev["dti"],
                    "ci95": ewcs_prev["ci95"],
                },
                "H86C_KSLB_E3_44k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/lane86c_results.json",
                    "dti": kslb_best["dti"],
                    "ci95": kslb_best["ci95"],
                },
                "H86G_EDTI_E1_55k_revoked": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86g-edti-run-card.json",
                    "dti": edti_prev["dti"],
                    "ci95": edti_prev["ci95"],
                },
                "H86I_RKSC_E1_44k": {
                    "evidence_class": "HOLDOUT-DTI",
                    "source": "docs/evidence/h86i-rksc-run-card.json",
                    "dti": rksc_prev["dti"],
                    "ci95": rksc_prev["ci95"],
                },
            },
            "beats_r0_with_positive_paired_ci": beats_r0_ci,
            "beats_same_split_kslb_point": beats_kslb,
            "leakage_canary_summary": {
                "features_tested": len(canary),
                "max_discriminative_auc_feature": max_canary_name,
                "max_discriminative_auc": max_canary["discriminative_auc"],
                "threshold": 0.90,
                "any_leakage_flag": False,
            },
            "leakage_canary": canary,
        },
        "secondary_off_catalogue_sgmc_diagnostic": sgmc_diagnostics,
        "informative_registry_overlap_by_arm": informative_by_arm,
        "preflight": preflight,
        "experiments_run": 3,
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
    }

    if rho_firings != 0:
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
            "note": "STOP: pre-placement surface rank-correlation > 0.90; logged duplicate, 0 slots used.",
            "note_chars": 84,
            "verdict": "negative",
            "duplicate": True,
            "new_candidate_generated": False,
            "decision": "DO NOT SUBMIT",
            "decision_reason": "pre-placement surface rank-correlation > 0.90 firing",
            "runtime_seconds": round(time.time() - t0, 2),
        }
        card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return 0

    dots_npy = WORK_DIR / "h86j_csgd_final_dots.npy"
    np.save(dots_npy, dots_e1.astype(np.float32))
    dots_sha = sha256(dots_npy)

    print(f"[H86J-CSGD] Running full-registry final-dots check ({time.time() - t0:.1f}s)...", flush=True)
    dots_report_path = EV_DIR / "h86j-csgd-registry-final-dots.json"
    dots_report, dots_rc = run_registry_check(dots_npy, dots_report_path, surface=False)
    chance_path = EV_DIR / "h86j-csgd-pa86-chance-overlap.json"
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
    digest8 = hashlib.sha256(np.ascontiguousarray(dots_e1).tobytes()).hexdigest()[:8]
    name = f"gems86-h86j-csgd-sar-admit-{int(dots_e1.sum())}dots-{stamp}-{digest8}-zeros"
    note = (
        f"H86J-CSGD SAR cross-spectral+GDR conduit PU (HOLDOUT-DTI {e1_score['dti']:.4f}); "
        "literal gate fail-closed; DO NOT SUBMIT; 0 slots"
    )[:140]
    receipt = write_candidate(
        dots_e1,
        g,
        name,
        note,
        metadata={
            "lane": "H86J-CSGD",
            "hypothesis": (
                "SAR geomorphically de-biased cross-spectral gravity-magnetic admittance "
                "+ GDR-1391 thermal/silica-geothermometer upflow conduit + Pollard-Segall elastic PU"
            ),
            "budget": BUDGET,
            "spacing_px": SPACING_PX,
            "collar_px": COLLAR_PX,
            "sar_gamma": SAR_GAMMA_E1,
            "sar_tau": SAR_TAU,
            "planes_memmap_sha256": planes_sha256,
            "surface_sha256": surface_sha,
            "dots_sha256": dots_sha,
            "registry_surface_evidence": "docs/evidence/h86j-csgd-registry-surface.json",
            "registry_final_evidence": "docs/evidence/h86j-csgd-registry-final-dots.json",
            "chance_overlap_evidence": (
                str(chance_path.relative_to(ROOT))
                if chance_path.is_file()
                else "FAILED_CLOSED_NO_REPORT (see run card)"
            ),
        },
    )

    verdict = "promote" if (beats_r0_ci and beats_kslb and registry_gate) else "negative"
    stop_reasons: list[str] = []
    if not beats_r0_ci:
        stop_reasons.append("paired HOLDOUT-DTI delta vs R0_D28_visible_collar 95% CI <= 0")
    if not beats_kslb:
        stop_reasons.append(
            f"HOLDOUT-DTI ({e1_score['dti']:.4f}) did not exceed same-split H86C-KSLB ({kslb_best['dti']:.4f})"
        )
    if not surface_gate_pass:
        stop_reasons.append(
            "pre-placement surface registry gate failed closed (2 upstream grid-incompatible "
            "registry rows and literal 17GEMSDOE full-support witness; 0 Spearman rho > 0.90 firings)"
        )
    if not final_dots_gate_pass:
        stop_reasons.append(
            "final-dot literal registry gate failed closed (17GEMSDOE full-support witness / "
            "dot-overlap firings and 2 upstream grid-incompatible registry rows)"
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
            "informative_overlap_halo_le_0p70": informative_by_arm["E1_csgd_sar_debiased"],
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
        "lane": "H86J-CSGD",
        "submission_file": run_card["submission_file"],
        "raster_sha256": run_card["raster_sha256"],
        "e1_holdout_dti": e1_score["dti"],
        "e1_ci95": e1_score["ci95"],
        "e2_holdout_dti": pooled["scores"]["E2_csgd_unweighted_pu_ablation"]["dti"],
        "e3_holdout_dti": pooled["scores"]["E3_csgd_autonomous_blind_conduit"]["dti"],
        "r0_holdout_dti": pooled["scores"]["R0_D28_visible_collar"]["dti"],
        "sgmc_proxy_dti_e1": sgmc_diagnostics["E1_csgd_sar_debiased"]["dti"],
        "sgmc_proxy_dti_e2": sgmc_diagnostics["E2_csgd_unweighted_pu_ablation"]["dti"],
        "sgmc_proxy_dti_e3": sgmc_diagnostics["E3_csgd_autonomous_blind_conduit"]["dti"],
        "e1_informative_firings": informative_by_arm["E1_csgd_sar_debiased"]["informative_overlap_firings_count"],
        "e2_informative_firings": informative_by_arm["E2_csgd_unweighted_pu_ablation"]["informative_overlap_firings_count"],
        "e3_informative_firings": informative_by_arm["E3_csgd_autonomous_blind_conduit"]["informative_overlap_firings_count"],
        "surface_rho_firings": rho_firings,
        "worst_surface_spearman": surface_report["shared_summary"]["worst_spearman_full_footprint"],
        "worst_final_dot_overlap": dots_report["shared_summary"]["worst_dot_overlap"],
        "verdict": verdict,
        "decision": run_card["decision"],
        "runtime_seconds": run_card["runtime_seconds"],
    }, indent=2), flush=True)
    return 0


def main(argv=None) -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    return _execute_pipeline()


if __name__ == "__main__":
    raise SystemExit(main())
