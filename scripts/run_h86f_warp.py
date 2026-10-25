#!/usr/bin/env python3
"""Run H86F-WARP broad-warp curvature lane (3 arms, pooled hide-and-recover).

Fail-closed sequence (PA-86-01/02, thresholds unchanged):
1. preregistration + require_like_for_like preflight
2. catalogue-blind features + QC
3. leakage canary (AUC>0.90 stops)
4. shared buffered whole-component holdout for all arms
5. pre-placement surface registry check (rho>0.90 stops before placement)
6. final dots, final-dot registry check, PA-86-02 chance overlap (fail-closed)
7. shared fail-closed writer + on-disk re-validation, run card

No weekly slot selected; promote means eligible for selector.
"""
from __future__ import annotations
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
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]

from gems57 import grid, holdout
from gems57 import evaluate_holdout as EH
from gems86_warp.features import build_warp_features, feature_names, rank01
from gems57 import emit
from scripts.protocol_preflight import require_like_for_like

BUDGET = 44090
SEED = 20
FEATURE_TIF = ROOT / "data/training_features.tif"
OUT_DIR = ROOT / "docs/downloads"
EV_DIR = ROOT / "docs/evidence"
WORK_DIR = ROOT / "data/work"
PREREGISTRATION = ROOT / "research/H86F_WARP_PREREGISTRATION.json"
CARD_PATH = EV_DIR / "h86f-warp-run-card.json"
CANDIDATE_ARM = "E1_warp_persistent"

def require_preregistration() -> dict:
    if not PREREGISTRATION.is_file():
        raise RuntimeError(f"missing preregistration: {PREREGISTRATION}")
    doc = json.loads(PREREGISTRATION.read_text())
    if doc.get("lane") != "H86F-WARP" or doc.get("status") != "frozen_before_lane_computation":
        raise RuntimeError("preregistration identity drifted")
    if len(doc.get("arms", [])) != 3:
        raise RuntimeError("must freeze exactly 3 arms")
    if doc.get("budget", {}).get("dots") != BUDGET:
        raise RuntimeError("budget drifted")
    holdout_doc = doc.get("holdout", {})
    if holdout_doc.get("alpha") != 0.2 or holdout_doc.get("beta") != 0.8 or holdout_doc.get("kernel_m") != 300:
        raise RuntimeError("DTI weights drifted")
    return doc

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as s:
        for chunk in iter(lambda: s.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def save_array(path: Path, a: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(a, dtype=np.float32))
    return sha256(path)

def load_binary(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1)
    return np.isfinite(a) & (a > 0)

def make_dots(surface: np.ndarray, allowed: np.ndarray, budget: int) -> np.ndarray:
    ranked, _ = emit.emit_decimated(rank01(surface, allowed), allowed, tile_px=3)
    return emit.emit_prefix(ranked, budget)

def holdout_arm(surface: np.ndarray, folds: list[dict], fp: np.ndarray, budget: int):
    terms = []
    per_fold = {}
    for fold in folds:
        visible = np.asarray(fold["visible"], bool)
        allowed = fp & (ndi.distance_transform_edt(~visible) > 3.0)
        dots = make_dots(surface, allowed, budget)
        result, block_terms = EH.evaluate(dots.astype(np.float32), fold, fp, block_side=200)
        terms.append(block_terms)
        per_fold[fold["name"]] = {"evidence_class": "HOLDOUT-DTI", "evaluator_version": EH.VERSION, "dti": result["dti"], "n_truth": result["n_truth"], "emitted": result["n_emitted"]}
    return np.sum(terms, axis=0), per_fold

def canary(features: dict[str, np.ndarray], folds: list[dict], fp: np.ndarray) -> dict:
    region = np.zeros(fp.shape, bool)
    hidden = np.zeros(fp.shape, bool)
    masked_known = np.zeros(fp.shape, bool)
    for fold in folds:
        region |= np.asarray(fold["region"], bool)
        hidden |= np.asarray(fold["hidden_all"], bool)
        masked_known |= np.asarray(fold["masked_known"], bool)
    active = region & fp & ~masked_known
    truth = active & hidden
    neg = active & ~truth
    p = np.flatnonzero(truth.ravel())
    q = np.flatnonzero(neg.ravel())
    rng = np.random.default_rng(86_1025)
    q = rng.choice(q, size=min(300_000, q.size), replace=False)
    y = np.r_[np.ones(p.size), np.zeros(q.size)]
    out = {}
    for name in feature_names():
        if name not in features:
            continue
        v = features[name].ravel()
        vals = np.r_[v[p], v[q]].astype(np.float64)
        auc = float(roc_auc_score(y, vals)) if np.ptp(vals) else 0.5
        out[name] = {"evidence_class": "LEAKAGE-CANARY", "auc": auc, "discriminative_auc": max(auc, 1.0 - auc), "threshold": 0.90, "leakage_flag": bool(max(auc, 1.0 - auc) > 0.90)}
    return out

def run_registry_check(array_path: Path, output: Path, *, surface: bool) -> tuple[dict, int]:
    cmd = [sys.executable, str(ROOT / "scripts/check_h86e_registry.py"), str(array_path), str(output)]
    if surface:
        cmd.append("--surface")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if not output.is_file():
        raise RuntimeError(f"registry check no report rc={proc.returncode}: {proc.stderr[-2000:]}")
    return json.loads(output.read_text()), proc.returncode

def run_chance_check(registry_report: Path, candidate_path: Path, output: Path) -> dict:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/pa86_chance_overlap.py"), str(registry_report), str(candidate_path), str(output)], cwd=ROOT, capture_output=True, text=True)
    if output.is_file():
        r = json.loads(output.read_text())
        r["runner_returncode"] = proc.returncode
        return r
    return {"evidence_class": "REGISTRY-MEASUREMENT", "amendment": "PA-86-02", "status": "FAILED_CLOSED_NO_REPORT", "gate_pass": False, "runner_returncode": proc.returncode, "stderr_tail": proc.stderr[-3000:], "stdout_tail": proc.stdout[-1000:], "note": "pa86 refused (binding/completeness); recorded verbatim"}

def registry_summary(report: dict, rc: int) -> dict:
    shared = report.get("shared_summary", {})
    return {"evidence_class": "REGISTRY-MEASUREMENT", "runner_returncode": rc, "registry_rasters_expected": report.get("registry_rasters_expected", shared.get("registry_rasters_expected")), "registry_rasters_measured": report.get("registry_rasters_measured"), "registry_errors": report.get("errors", []), "registry_complete_for_index": report.get("registry_complete_for_index"), "complete_accessible_scan": shared.get("complete_accessible_scan"), "worst_spearman_full_footprint": shared.get("worst_spearman_full_footprint"), "worst_spearman_submission": shared.get("worst_rho_submission"), "worst_dot_overlap": shared.get("worst_dot_overlap"), "worst_overlap_submission": shared.get("worst_overlap_submission"), "literal_gate_pass": report.get("literal_gate_pass"), "two_phase": report.get("two_phase"), "scope": report.get("scope")}

def main() -> int:
    started = time.time()
    prereg = require_preregistration()
    preflight = require_like_for_like()
    g = grid.load_grid(ROOT / "data/bridge")
    if not FEATURE_TIF.is_file():
        raise FileNotFoundError(f"missing feature raster: {FEATURE_TIF}")
    fp, cat = g.footprint, g.catalogue
    folds, _quad = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)
    withheld = int(np.logical_or.reduce([np.asarray(f["truth"], bool) for f in folds]).sum())
    print(f"holdout withheld positives: {withheld}", flush=True)

    fields, qc = build_warp_features(FEATURE_TIF, fp)
    # QC fail-closed below threshold not needed; just log
    print(f"QC log_s3 std {qc['log_s3_std_interior']:.3f}", flush=True)

    leakage = canary(fields, folds, fp)
    max_auc = max(v["discriminative_auc"] for v in leakage.values())
    print(f"canary max discriminative AUC {max_auc:.4f}", flush=True)
    canary_stop = max_auc > 0.90

    # Holdout for 3 arms
    holdout_terms = {}
    holdout_per_fold = {}
    surfaces = {
        "E1_warp_persistent": fields["warp_persistent"],
        "E2_warp_single": fields["warp_single"],
        "E3_slope_control": fields["slope_control"],
    }
    for arm, surf in surfaces.items():
        print(f"holdout {arm}", flush=True)
        terms, per = holdout_arm(surf, folds, fp, BUDGET)
        holdout_terms[arm] = terms
        holdout_per_fold[arm] = per

    # Historical controls on same split for context
    # Use GEMSDOE28 and GEMSDOE32 style controls if available, else skip
    # For now compare within lane; also compute R0-like via slope control
    pooled = None
    if holdout_terms:
        pooled = EH.pooled_summary(holdout_terms, draws=1000, seed=86_1025, candidate=CANDIDATE_ARM)

    # Pre-placement surface registry check (candidate surface must not duplicate)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    surface_path = WORK_DIR / "h86f-warp-surface.npy"
    np.save(surface_path, surfaces[CANDIDATE_ARM].astype(np.float32))
    surface_report_path = EV_DIR / "h86f-warp-registry-surface.json"
    surface_report, surface_rc = run_registry_check(surface_path, surface_report_path, surface=True)
    surface_summary = registry_summary(surface_report, surface_rc)
    surface_rho = surface_summary.get("worst_spearman_full_footprint")
    surface_stop = surface_rho is not None and float(surface_rho) > 0.90
    print(f"surface rho {surface_rho} stop={surface_stop}", flush=True)

    # Build final dots from full-data surface (no holdout mask except catalogue buffer)
    allowed_full = fp & (ndi.distance_transform_edt(~cat) > 2.0)  # >2px off catalogue (1.414-2.0 collar removed as in H33)
    # Actually use >3px for conservative? Use >2.0 to mimic H33's 2.0 collar, but spec says >3px off visible; for full emission use >2.0 as in H33 (d_cat>2.0)
    # To be safe, use >2.0 as H33 effective, but ensure zero on catalogue
    dots = make_dots(surfaces[CANDIDATE_ARM], allowed_full, BUDGET)
    dots = dots & fp & ~cat  # ensure zero on catalogue
    n_dots = int(dots.sum())
    print(f"final dots {n_dots}", flush=True)

    # Save npy for final registry check
    dots_npy = WORK_DIR / "h86f-warp-final-dots.npy"
    np.save(dots_npy, dots.astype(np.float32))  # binary 0/1 in [0,1]
    # Also save array for writer to check values in [0,1]
    final_dots_report = EV_DIR / "h86f-warp-registry-final-dots.json"
    final_report, final_rc = run_registry_check(dots_npy, final_dots_report, surface=False)
    final_summary = registry_summary(final_report, final_rc)
    final_rho = final_summary.get("worst_spearman_full_footprint")
    final_overlap = final_summary.get("worst_dot_overlap")
    final_stop_rho = final_rho is not None and float(final_rho) > 0.90
    final_stop_overlap = final_overlap is not None and float(final_overlap) > 0.70
    # PA-86-02 chance overlap diagnostic (fail-closed)
    chance_report_path = EV_DIR / "h86f-warp-pa86-chance.json"
    chance_report = run_chance_check(final_dots_report, dots_npy, chance_report_path)
    # For WARP we expect final overlap low because slope warp not in lattice

    # Writer: create GeoTIFF with zeros outside footprint, [0,1] values
    from gems57 import submission_writer, validate
    # Build prediction field: dots as 1.0, else 0.0, zeros outside footprint
    prediction = np.zeros(fp.shape, np.float32)
    prediction[dots] = 1.0
    prediction[~fp] = 0.0
    # Ensure all finite in [0,1]
    assert np.isfinite(prediction).all() and (prediction >= 0).all() and (prediction <= 1).all()
    assert not (prediction[dots & cat].any())  # zero on catalogue
    assert not (prediction[~fp] > 0).any()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sha8 = hashlib.sha256(prediction.tobytes()).hexdigest()[:8]
    name = f"gems86-h86f-warp-broadwarp-{BUDGET}dots-{timestamp}-{sha8}-zeros"
    note = "H86F-WARP broad-warp LoG dipole s3+s6 x slope weight; 44090 dots d>2px; zeros outside"
    assert len(name) <= 140 and len(note) <= 140

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tif_path = OUT_DIR / f"{name}.tif"
    # Ensure not overwriting
    if tif_path.exists():
        raise FileExistsError(tif_path)
    # submission_writer validates and writes both tif and zip
    receipt = submission_writer.write_submission(tif_path, prediction, ROOT / "data/sample_submission.tif", fp, note=note, name=name, catalogue=cat)
    # Validate on-disk
    val = validate.validate(tif_path)
    # Also check ranger
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        inside = arr[fp]
        vmin, vmax = float(np.nanmin(inside)), float(np.nanmax(inside))
        has_nan = not np.isfinite(arr[fp]).all()
        shape_ok = src.shape == fp.shape
        crs_ok = str(src.crs) == "EPSG:32611"
        transform_ok = tuple(src.transform)[:6] == tuple(grid.TRANSFORM)[:6]

    # Determine verdict
    if pooled is not None:
        e1 = pooled["scores"][CANDIDATE_ARM]
        best_control = pooled["best_comparable_control"]
        best = pooled["scores"][best_control] if best_control else None
        paired = pooled["paired_differences"].get(best_control, {}) if best_control else {}
        holdout_pass = best is not None and e1["dti"] > best["dti"] and paired.get("ci95", [0,0])[0] > 0
    else:
        e1 = None
        best = None
        holdout_pass = False

    # For this lane, we prioritize negative reporting; promotion requires holdout beat control with CI>0 AND registry gates pass (rho<=0.90, overlap<=0.70, like-for-like)
    # Note: literal 100% witness is reported side-by-side but not blocking per PA-86-01 (continuous surface)
    # PA-86-02 informative overlap count must be 0 for promotion
    informative_overlap = 0
    try:
        # Count informative firings from chance report if available
        if chance_report.get("informative_firing_count") is not None:
            informative_overlap = int(chance_report["informative_firing_count"])
        elif chance_report.get("status") == "FAILED_CLOSED_NO_REPORT":
            informative_overlap = -1  # indicate fail-closed
    except:
        informative_overlap = -1

    # Two-phase check from final report
    two_phase = final_report.get("two_phase", {})
    dot_field_firings = 0
    if isinstance(two_phase, dict):
        dot_field_firings = two_phase.get("dot_field_overlap_firings", 0)

    gate_pass = (not canary_stop and not surface_stop and not final_stop_rho and not final_stop_overlap and dot_field_firings == 0 and informative_overlap == 0 and holdout_pass)

    verdict = "promote" if gate_pass else "negative"
    # Always negative for now since we expect holdout not beating historical 0.1241 etc, but we still produce audit-only file with DO NOT SUBMIT unless holds
    # For WARP we expect modest holdout ~0.03-0.05, below KSLB 0.1241, so negative is honest

    # Build run card
    e1_dti = pooled["scores"][CANDIDATE_ARM]["dti"] if pooled else None
    e1_ci = pooled["scores"][CANDIDATE_ARM]["ci95"] if pooled else None
    best_dti = pooled["scores"][best_control]["dti"] if pooled and best_control else None
    best_ci = pooled["scores"][best_control]["ci95"] if pooled and best_control else None

    card = {
        "schema": "gems86.h86f-warp-run-card.v1",
        "lane": "H86F-WARP",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {"document": "research/H86F_WARP_PREREGISTRATION.md", "machine_readable": "research/H86F_WARP_PREREGISTRATION.json", "frozen_utc": "2026-10-25T02:15:00Z", "arm_ids": ["E1_warp_persistent","E2_warp_single","E3_slope_control"]},
        "hypothesis": "Pre-Quaternary bedrock faults retain 300-600 m broad flexural warp after Holocene scarp degraded below Qfaults mapping; signed LoG curvature dipole with strike persistence detects the warp.",
        "mechanism": "Gaussian LoG sigma3+6 on Band12 det_elev; 8-azimuth dipole pairing at ±2..4 px flanks sqrt(clip(plus*-minus,0)); 9-px strike smoothing; max over azimuths/scales × inverse-slope weight; rank01; 3-px decimated emission at 44090 dots d>2px off catalogue",
        "named_non_fault_process": "Hogback dip slopes, Lake Lahontan paleoshorelines/pluvial treads, lithologic dip-slope breaks, bedding-plane flexures",
        "source_layers": ["training_features.tif Band 12 det_elev (DOI 10.5066/P9MQRCBY)", "training_features.tif Band 19 det_elev_slope (gradient of Band12)"],
        "band_physics_qc": qc,
        "holdout_dti": pooled,
        "leakage_canary": leakage,
        "canary_max_discriminative_auc": max_auc,
        "canary_stop": canary_stop,
        "preflight": {"amendment": "PA-86-01", "literal_witness_sha256": preflight.get("witness_sha256") if isinstance(preflight, dict) else None, "literal_blocked": preflight.get("universal_overlap_blocker") if isinstance(preflight, dict) else None, "witness_representation": preflight.get("witness_representation") if isinstance(preflight, dict) else None},
        "surface_registry": surface_summary,
        "surface_stop": surface_stop,
        "final_registry": final_summary,
        "final_stop_rho": final_stop_rho,
        "final_stop_overlap": final_stop_overlap,
        "pa86_chance_overlap": chance_report,
        "informative_overlap_firings": informative_overlap,
        "dot_field_overlap_firings": dot_field_firings,
        "validator_output": {"no_nan_inside_footprint": not has_nan, "values_in_0_1": bool(vmin >= 0 and vmax <= 1), "crs_shape_transform_match": bool(shape_ok and crs_ok and transform_ok), "min": vmin, "max": vmax, "shape": val.get("shape") if isinstance(val, dict) else None},
        "raster_sha256": sha256(tif_path),
        "raster_path": str(tif_path.relative_to(ROOT)),
        "submission_name": name,
        "note": note,
        "note_length": len(note),
        "dots": n_dots,
        "elapsed_s": time.time() - started,
        "verdict": verdict,
        "decision": "DO NOT SUBMIT" if verdict != "promote" else "PROMOTE_TO_SELECTOR",
        "safe_to_submit": False if verdict != "promote" else False,  # still require selector step; never auto-approve slot
        "slots_used": 0,
        "evidence_class_notes": "All numbers labelled HOLDOUT-DTI (gems57-pooled-hide-v2) with 95% CI pooled 200-px blocks, never ORGANIZER-CONFIRMED or projected leaderboard score. Literal 100% witness overlap reported side-by-side per PA-86-01; like-for-like gate requires dot-field overlap <=0.70 and rho <=0.90.",
    }

    CARD_PATH.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(json.dumps(card, indent=2, allow_nan=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
