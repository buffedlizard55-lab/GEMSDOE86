#!/usr/bin/env python3
"""Run the preregistered H86F-PCC signed basement-step lane.

Three fixed arms, shared holdout, shared writer, shared registry checker.
No weekly slot is selected here.  A format-valid TIFF is written only after
the pre-placement rank test shows no Spearman firing above 0.90.  The file is
marked safe to submit only if every preregistered scientific and registry gate
passes.  Otherwise it is an audit download and the decision is DO NOT SUBMIT.
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

from gems57 import emit, evaluate_holdout as EH, grid, holdout  # noqa: E402
from gems57 import submission_writer, validate  # noqa: E402
from gems86_pcc.features import build_polarity_features, feature_names, rank01  # noqa: E402
from scripts.protocol_preflight import require_like_for_like  # noqa: E402

BUDGET = 44_090
SEED = 20
FEATURE_TIF = ROOT / "data/training_features.tif"
D28 = ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
H33 = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
OUT_DIR = ROOT / "docs/downloads"
EV_DIR = ROOT / "docs/evidence"
WORK_DIR = ROOT / "data/work"
PREREGISTRATION = ROOT / "research/H86F_PCC_PREREGISTRATION.json"
CANDIDATE = "E1_pcc_signed"


def require_preregistration() -> dict:
    if not PREREGISTRATION.is_file():
        raise RuntimeError(f"missing preregistration: {PREREGISTRATION}")
    doc = json.loads(PREREGISTRATION.read_text(encoding="utf-8"))
    arms = [arm for arm in doc.get("arms", []) if arm.get("role") in {
        "preregistered candidate", "cover-filter control", "unsigned-alignment control"}]
    if len(arms) != 3:
        raise RuntimeError("H86F-PCC must freeze exactly 3 runnable arms")
    if doc.get("candidate_arm") != CANDIDATE:
        raise RuntimeError("candidate arm drifted from the frozen preregistration")
    required = {"layers", "transform", "non_fault_mimic", "uncatalogued_rationale",
                "novelty", "cost", "official_data"}
    if any(not required.issubset(arm) for arm in doc.get("arms", [])):
        raise RuntimeError("H86F-PCC preregistration is missing required hypothesis fields")
    if not 3 <= len(doc.get("arms", [])) <= 5:
        raise RuntimeError("H86F-PCC must record 3-5 hypotheses")
    if doc.get("budget", {}).get("max_arms") != 3 or doc.get("budget", {}).get("max_hours") != 2:
        raise RuntimeError("H86F-PCC budget drifted from the 3-arm/2-hour limit")
    if doc.get("holdout", {}).get("alpha") != 0.2 or doc.get("holdout", {}).get("beta") != 0.8:
        raise RuntimeError("H86F-PCC DTI weights drifted")
    if doc.get("budget", {}).get("dots") != BUDGET:
        raise RuntimeError("emission budget drifted from the preregistration")
    return doc


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
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


def holdout_arm(surface: np.ndarray, folds: list[dict], fp: np.ndarray,
                budget: int) -> tuple[np.ndarray, dict]:
    terms = []
    per_fold = {}
    for fold in folds:
        visible = np.asarray(fold["visible"], bool)
        allowed = fp & (ndi.distance_transform_edt(~visible) > 3.0)
        dots = make_dots(surface, allowed, budget)
        result, block_terms = EH.evaluate(dots.astype(np.float32), fold, fp, block_side=200)
        terms.append(block_terms)
        per_fold[fold["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": result["dti"],
            "n_truth": result["n_truth"],
            "emitted": result["n_emitted"],
        }
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
    pos = np.flatnonzero(truth.ravel())
    neg_idx = np.flatnonzero(neg.ravel())
    rng = np.random.default_rng(86_1025)
    neg_idx = rng.choice(neg_idx, size=min(300_000, neg_idx.size), replace=False)
    y = np.r_[np.ones(pos.size), np.zeros(neg_idx.size)]
    out = {}
    for name in feature_names():
        values = features[name].ravel()
        sample = np.r_[values[pos], values[neg_idx]].astype(np.float64)
        auc = float(roc_auc_score(y, sample)) if np.ptp(sample) else 0.5
        discriminative = max(auc, 1.0 - auc)
        out[name] = {
            "evidence_class": "LEAKAGE-CANARY",
            "auc": auc,
            "discriminative_auc": discriminative,
            "threshold": 0.90,
            "leakage_flag": bool(discriminative > 0.90),
            "n_positive": int(pos.size),
            "n_negative_sampled": int(neg_idx.size),
        }
    return out


def run_registry_check(array_path: Path, output: Path, *, surface: bool) -> dict:
    cmd = [sys.executable, str(ROOT / "scripts/check_h86e_registry.py"),
           str(array_path), str(output)]
    if surface:
        cmd.append("--surface")
    completed = subprocess.run(cmd, cwd=ROOT, check=False)
    report = json.loads(output.read_text())
    report["checker_exit_code"] = int(completed.returncode)
    return report


def run_chance_check(registry_report: Path, candidate_path: Path, output: Path) -> dict:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/pa86_chance_overlap.py"),
         str(registry_report), str(candidate_path), str(output)],
        cwd=ROOT, check=False,
    )
    if not output.is_file():
        return {"gate_pass": False, "checker_exit_code": int(completed.returncode),
                "error": "PA-86-02 did not write a report"}
    report = json.loads(output.read_text())
    report["checker_exit_code"] = int(completed.returncode)
    return report


def write_candidate(dots: np.ndarray, g, name: str, note: str, metadata: dict) -> dict:
    pred = np.where(dots & g.footprint, 1.0, 0.0).astype(np.float32)
    path = OUT_DIR / f"{name}.tif"
    receipt = submission_writer.write_submission(
        path, pred, ROOT / "data/bridge/sample_submission.tif", g.footprint,
        note=note, name=name, catalogue=g.catalogue, metadata=metadata,
    )
    disk = validate.validate(path, g.footprint, g.catalogue)
    if not disk["all_checks_passed"]:
        raise RuntimeError("independent on-disk validator failed")
    receipt["independent_disk_validation"] = disk
    path.with_suffix(".json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    return receipt


def rho_firings(report: dict) -> int | None:
    phase = report.get("two_phase") or {}
    literal = phase.get("literal_reading") or {}
    value = literal.get("rho_firings")
    return None if value is None else int(value)


def main() -> int:
    started = time.time()
    preregistration = require_preregistration()
    preflight = require_like_for_like()
    g = grid.load_grid(ROOT / "data/bridge")
    if not FEATURE_TIF.is_file():
        raise FileNotFoundError(f"missing pinned feature raster: {FEATURE_TIF}")
    fp, cat = g.footprint, g.catalogue
    folds, _quad = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)
    withheld = int(np.logical_or.reduce([np.asarray(f["truth"], bool) for f in folds]).sum())

    print("building polarity features", flush=True)
    fields = build_polarity_features(FEATURE_TIF, fp)
    feature_hashes = {
        name: save_array(WORK_DIR / f"h86f_pcc_{name}.npy", fields[name])
        for name in feature_names()
    }
    leakage = canary(fields, folds, fp)
    leakage_stop = any(v["leakage_flag"] for v in leakage.values())

    arms = {
        "E1_pcc_signed": fields["pcc_signed"],
        "E2_pcc_cover": fields["pcc_cover"],
        "E3_pcc_unsigned": fields["pcc_unsigned"],
    }
    holdout_terms = {}
    holdout_per_fold = {}
    if not leakage_stop:
        for arm, surface in arms.items():
            print(f"holdout {arm}", flush=True)
            terms, per = holdout_arm(surface, folds, fp, BUDGET)
            holdout_terms[arm] = terms
            holdout_per_fold[arm] = per
        for label, path in (("R0_D28_visible_collar", D28), ("H33_visible_collar", H33)):
            if path.is_file():
                terms, per = holdout_arm(load_binary(path).astype(np.float32), folds, fp, BUDGET)
                holdout_terms[label] = terms
                holdout_per_fold[label] = per
    pooled = None
    if holdout_terms:
        pooled = EH.pooled_summary(holdout_terms, draws=1000, seed=86_1025, candidate=CANDIDATE)

    current_best = json.loads((EV_DIR / "lane86c_results.json").read_text())[
        "holdout_buffered_whole_components"]["scores"]["E3_kslb_noisyor_44k"]
    same_split = withheld == int(current_best["withheld_positive_pixels"])
    e1 = None if pooled is None else pooled["scores"][CANDIDATE]
    best_delta = None if pooled is None else pooled["paired_differences"][pooled["best_comparable_control"]]
    beats_current = bool(
        same_split and e1 is not None
        and e1["dti"] > current_best["dti"]
        and e1["ci95"][0] > current_best["ci95"][1]
    )
    beats_controls = bool(best_delta is not None and best_delta["ci95"][0] > 0)

    surface_path = WORK_DIR / "h86f_pcc_final_surface.npy"
    save_array(surface_path, rank01(fields["pcc_signed"], fp))
    surface_report_path = EV_DIR / "h86f-pcc-registry-surface.json"
    print("registry surface check", flush=True)
    surface_report = run_registry_check(surface_path, surface_report_path, surface=True)
    rho_stop = rho_firings(surface_report)
    if rho_stop is None:
        raise RuntimeError("surface registry check did not return a rank-correlation count")
    # Rank drift is a lane collision. Incomparable grids are reported, not ignored.
    place = (not leakage_stop) and rho_stop == 0
    dots_report = None
    chance = None
    receipt = None
    name = None
    note = None
    final_dots = None
    if place:
        allowed = fp & (ndi.distance_transform_edt(~cat) > 3.0)
        final_dots = make_dots(fields["pcc_signed"], allowed, BUDGET)
        dots_path = WORK_DIR / "h86f_pcc_final_dots.npy"
        save_array(dots_path, final_dots.astype(np.float32))
        dots_report_path = EV_DIR / "h86f-pcc-registry-final-dots.json"
        print("registry final-dot check", flush=True)
        dots_report = run_registry_check(dots_path, dots_report_path, surface=False)
        chance_path = EV_DIR / "h86f-pcc-pa86-chance-overlap.json"
        chance = run_chance_check(dots_report_path, dots_path, chance_path)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
        name = f"gems86-h86f-pcc-signed-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"
        note = ("H86F-PCC signed grav-RTP-basement polarity, survey-axis veto; "
                "holdout is not a leaderboard score; no slot used")[:140]
        receipt = write_candidate(
            final_dots, g, name, note,
            metadata={
                "lane": "H86F-PCC",
                "hypothesis": "signed polarity-consistent basement step",
                "budget": BUDGET,
                "feature_hashes": feature_hashes,
                "surface_sha256": sha256(surface_path),
                "dots_sha256": sha256(dots_path),
            },
        )

    registry_errors = list(surface_report.get("errors") or [])
    if dots_report is not None:
        registry_errors.extend(dots_report.get("errors") or [])
    registry_complete = bool(
        surface_report.get("registry_complete_for_index")
        and (dots_report or {}).get("registry_complete_for_index")
        and not registry_errors
    )
    pa_pass = bool(chance and chance.get("gate_pass") is True)
    dots_pass = bool(dots_report and dots_report.get("final_dots_gate_pass") is True)
    surface_pass = bool(surface_report.get("surface_gate_pass") is True and not surface_report.get("errors"))
    promote = bool(
        place and beats_current and beats_controls and registry_complete
        and pa_pass and dots_pass and surface_pass and receipt is not None
    )
    reasons = []
    if leakage_stop:
        reasons.append("leakage canary exceeded 0.90")
    if not same_split:
        reasons.append("withheld-positive count does not match the historical KSLB split")
    if e1 is None:
        reasons.append("holdout was not scored")
    elif not beats_current:
        reasons.append("candidate does not beat same-split HOLDOUT-DTI best with separated CIs")
    if not beats_controls:
        reasons.append("paired HOLDOUT-DTI delta versus best preregistered control is not strictly positive")
    if rho_stop:
        reasons.append("pre-placement surface rank correlation exceeded 0.90; placement stopped")
    if surface_report.get("errors"):
        reasons.append("registry contains incomparable grids; complete-scan gate is false")
    if dots_report is not None and not dots_pass:
        reasons.append("final-dot like-for-like registry gate failed")
    if chance is not None and not pa_pass:
        if chance.get("error"):
            reasons.append("PA-86-02 script refused the incomplete registry and wrote no firing count")
        else:
            reasons.append(f"PA-86-02 informative overlap firings: {chance.get('informative_firings')}")
    if not reasons and promote:
        reasons.append("scientific and registry gates passed; weekly slot was not auto-spent")
    if not reasons:
        reasons.append("gates did not all pass")

    decision = "OK TO DOWNLOAD AND SUBMIT" if promote else "DO NOT SUBMIT"
    run_card = {
        "schema": "gems86.h86f-pcc-run-card.v1",
        "lane": "H86F-PCC",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {
            "document": "research/H86F_PCC_PREREGISTRATION.md",
            "machine_readable": "research/H86F_PCC_PREREGISTRATION.json",
            "candidate_arm": CANDIDATE,
            "hypotheses_recorded": len(preregistration["arms"]),
        },
        "hypothesis": (
            "A basement step missing from the Quaternary catalogue offsets density and "
            "magnetization under cover. Gravity and RTP gradients point toward the footwall "
            "while depth-to-basement points the other way. Unsigned edge alignment accepts "
            "the anti-parallel case and is not the same mechanism."
        ),
        "mechanism": (
            "Bands 13, 2, 15 and 12 are differentiated on the north-up grid at 150 m and 400 m. "
            "Signed polarity is the minimum of the two scales, times structure-tensor coherence, "
            "an oblique-to-90/180 survey-axis weight, gradient-magnitude ranks, and a soft "
            "topographic-density veto. Catalogue pixels are not features."
        ),
        "named_non_fault_process": (
            "Unfaulted basin-fill facies contacts, volcanic flow edges, and residual GeoDAWN "
            "E-W flight-line or N-S tie-line corrugations can mimic a signed basement step."
        ),
        "named_non_fault_mimic": (
            "Unfaulted basin-fill facies contacts, volcanic flow edges, and residual GeoDAWN "
            "E-W flight-line or N-S tie-line corrugations can mimic a signed basement step."
        ),
        "source_layers": [
            "training_features.tif band 13 iso_grav_anom",
            "training_features.tif band 2 rtp",
            "training_features.tif band 15 depth_to_base_surf",
            "training_features.tif band 12 det_elev",
            "training_features.tif band 19 det_elev_slope",
            "USGS GeoDAWN DOI 10.5066/P93LGLVQ flight-line azimuth 90 and tie-line azimuth 180",
        ],
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "design": "buffered whole-component quadrant draw, seed 20, hide fraction 0.20, visible-fault collar 3 px, pooled 200-px physical blocks",
            "withheld_positive_pixels": withheld,
            "same_split_as_historical_kslb": same_split,
            "candidate": e1,
            "paired_delta_vs_best_preregistered_control": best_delta,
            "best_preregistered_control": None if pooled is None else pooled["best_comparable_control"],
            "current_holdout_best_same_split": {
                "evidence_class": "HOLDOUT-DTI",
                "source": "docs/evidence/lane86c_results.json",
                "arm": "E3_kslb_noisyor_44k",
                "dti": current_best["dti"],
                "ci95": current_best["ci95"],
                "withheld_positive_pixels": current_best["withheld_positive_pixels"],
                "note": "historical same-split comparator only if withheld counts match; not re-run by this lane",
            },
            "beats_current_with_separated_ci": beats_current,
            "paired_delta_beats_control": beats_controls,
            "all_arms": None if pooled is None else pooled["scores"],
            "paired_differences": None if pooled is None else pooled["paired_differences"],
            "per_fold": holdout_per_fold,
            "leakage_canary": leakage,
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "surface_preplacement": {
                "report": str(surface_report_path.relative_to(ROOT)),
                "registry_rasters_measured": surface_report.get("registry_rasters_measured"),
                "registry_rasters_expected": surface_report.get("registry_rasters_expected"),
                "registry_errors": surface_report.get("errors"),
                "surface_gate_pass": surface_report.get("surface_gate_pass"),
                "rho_firings": rho_stop,
                "complete_accessible_scan": (surface_report.get("shared_summary") or {}).get("complete_accessible_scan"),
                "worst_spearman_full_footprint": (surface_report.get("shared_summary") or {}).get("worst_spearman_full_footprint"),
                "two_phase_like_for_like_duplicate": ((surface_report.get("two_phase") or {}).get("like_for_like_reading") or {}).get("duplicate"),
            },
            "final_dots": None if dots_report is None else {
                "report": "docs/evidence/h86f-pcc-registry-final-dots.json",
                "registry_rasters_measured": dots_report.get("registry_rasters_measured"),
                "registry_errors": dots_report.get("errors"),
                "final_dots_gate_pass": dots_report.get("final_dots_gate_pass"),
                "complete_accessible_scan": (dots_report.get("shared_summary") or {}).get("complete_accessible_scan"),
                "worst_dot_overlap": (dots_report.get("shared_summary") or {}).get("worst_dot_overlap"),
                "worst_spearman_full_footprint": (dots_report.get("shared_summary") or {}).get("worst_spearman_full_footprint"),
            },
            "pa86_02": chance,
            "incompatible_grid_note": (
                "Two pinned inventory rasters are not on the submission grid. They are recorded "
                "as registry errors and block a complete-scan pass. They are not resampled and "
                "are not treated as a duplicate firing."
            ),
        },
        "raster_sha256": None if receipt is None else receipt["sha256"],
        "validator_output": None if receipt is None else {
            "evidence_class": "LOCAL-FORMAT-VALIDATION",
            "all_checks_passed": receipt["independent_disk_validation"]["all_checks_passed"],
            "no_nan_inside_footprint": receipt["independent_disk_validation"]["checks"]["in_footprint_all_finite"],
            "values_in_0_1": receipt["independent_disk_validation"]["checks"]["range_0_1_guaranteed"],
            "crs_shape_transform_match": all(
                receipt["independent_disk_validation"]["checks"][key]
                for key in ("crs_epsg_32611", "dimensions_3730x3292", "transform_matches_sample_submission")
            ),
            "checks": receipt["independent_disk_validation"]["checks"],
            "positive_pixels": receipt["independent_disk_validation"]["emitted_positive_pixels"],
            "min": receipt["independent_disk_validation"]["min"],
            "max": receipt["independent_disk_validation"]["max"],
        },
        "submission_name": name,
        "note": note,
        "note_chars": None if note is None else len(note),
        "verdict": "promote" if promote else "negative",
        "submission_ready": promote,
        "safe_to_submit": promote,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "decision": decision,
        "decision_reason": "; ".join(reasons),
        "experiments_run": 0 if leakage_stop else 3,
        "placement_performed": place,
        "preflight_status": preflight.get("status"),
        "runtime_seconds": time.time() - started,
        "organizer_confirmed": False,
    }
    card_path = EV_DIR / "h86f-pcc-run-card.json"
    card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "submission": None if name is None else f"docs/downloads/{name}.tif",
        "sha256": run_card["raster_sha256"],
        "holdout_dti": None if e1 is None else e1["dti"],
        "holdout_ci95": None if e1 is None else e1["ci95"],
        "withheld_positive_pixels": withheld,
        "current_holdout_best": current_best["dti"],
        "beats_current": beats_current,
        "rho_firings": rho_stop,
        "decision": decision,
        "verdict": run_card["verdict"],
        "reason": run_card["decision_reason"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
