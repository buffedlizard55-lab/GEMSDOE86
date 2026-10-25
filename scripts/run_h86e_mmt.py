#!/usr/bin/env python3
"""Run the preregistered H86E-MMT magnetic-marker translation lane.

This is one catalogue-blind experiment family, with three fixed arms:
``mmt_tc_decoupled`` (candidate), ``mmt_translation`` (mechanism control), and
``mmt_edge_control`` (point-edge control).  It uses the pinned shared holdout,
evaluator, writer, and registry tools.  No competition slot is selected here.

The sequence is fail-closed:
1. check the pinned protocol witness;
2. build and canary-test the candidate surface;
3. run the shared buffered whole-component holdout;
4. check the surface against the complete accessible registry *before* dots;
5. emit the final binary TIFF, validate it on disk, then check final dots and
   PA-86-02 chance-level overlap.

A format-valid artifact with a negative scientific or uniqueness result is kept
as an audit download and is explicitly marked ``DO NOT SUBMIT``.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
import zipfile
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
from gems86_mmt.features import build_marker_features, feature_names, rank01  # noqa: E402

BUDGET = 44_090
SEED = 20
FEATURE_TIF = ROOT / "data/training_features.tif"
D28 = ROOT / "data/registry_ext/91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8.tif"
OUT_DIR = ROOT / "docs/downloads"
EV_DIR = ROOT / "docs/evidence"
WORK_DIR = ROOT / "data/work"
PREREGISTRATION = ROOT / "research/H86E_MMT_PREREGISTRATION.json"


def require_preregistration() -> dict:
    """Refuse a future lane run unless its 3–5-arm design is on disk first."""
    if not PREREGISTRATION.is_file():
        raise RuntimeError(f"missing preregistration: {PREREGISTRATION}")
    doc = json.loads(PREREGISTRATION.read_text(encoding="utf-8"))
    arms = doc.get("arms", [])
    if not (3 <= len(arms) <= 5):
        raise RuntimeError("H86E-MMT preregistration must contain 3–5 hypotheses/arms")
    required = {"layers", "transform", "non_fault_mimic", "uncatalogued_rationale",
                "novelty", "cost", "official_data"}
    if any(not required.issubset(arm) for arm in arms):
        raise RuntimeError("H86E-MMT preregistration is missing required hypothesis fields")
    if doc.get("budget", {}).get("max_arms") != 3 or doc.get("budget", {}).get("max_hours") != 2:
        raise RuntimeError("H86E-MMT budget drifted from the 3-arm/2-hour limit")
    if doc.get("holdout", {}).get("alpha") != 0.2 or doc.get("holdout", {}).get("beta") != 0.8:
        raise RuntimeError("H86E-MMT DTI weights drifted")
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


def holdout_binary_control(dots_mask: np.ndarray, folds: list[dict], fp: np.ndarray,
                           collar_px: float = 2.0) -> tuple[np.ndarray, dict, np.ndarray]:
    """Evaluate a pre-existing binary dot field masked strictly by fold-visible faults."""
    terms = []
    per_fold = {}
    example = None
    for f in folds:
        visible = np.asarray(f["visible"], bool)
        dvis = ndi.distance_transform_edt(~visible)
        dots = np.asarray(dots_mask, bool) & fp & ~visible & (dvis > collar_px)
        if example is None:
            example = dots.copy()
        result, block_terms = EH.evaluate(dots.astype(np.float32), f, fp, block_side=200)
        terms.append(block_terms)
        per_fold[f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": result["dti"],
            "n_truth": result["n_truth"],
            "emitted": result["n_emitted"],
        }
    return np.sum(terms, axis=0), per_fold, example


def holdout_arm(surface: np.ndarray, folds: list[dict], fp: np.ndarray,
                budget: int) -> tuple[dict, dict, np.ndarray]:
    """Evaluate one deterministic surface with the unmodified v2 evaluator."""
    terms = []
    per_fold = {}
    example = None
    for f in folds:
        visible = np.asarray(f["visible"], bool)
        dvis = ndi.distance_transform_edt(~visible)
        allowed = fp & (dvis > 3.0)
        dots = make_dots(surface, allowed, budget)
        if example is None:
            example = dots.copy()
        result, block_terms = EH.evaluate(
            dots.astype(np.float32), f, fp, block_side=200,
        )
        terms.append(block_terms)
        per_fold[f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": result["dti"],
            "n_truth": result["n_truth"],
            "emitted": result["n_emitted"],
        }
    pooled_terms = np.sum(terms, axis=0)
    return pooled_terms, per_fold, example


def run_registry_check(array_path: Path, output: Path, *, surface: bool) -> dict:
    cmd = [sys.executable, str(ROOT / "scripts/check_h86e_registry.py"),
           str(array_path), str(output)]
    if surface:
        cmd.append("--surface")
    res = subprocess.run(cmd, cwd=ROOT, check=False)
    if res.returncode not in (0, 2) or not output.is_file():
        raise subprocess.CalledProcessError(res.returncode, cmd)
    return json.loads(output.read_text())


def run_chance_check(registry_report: Path, candidate_path: Path, output: Path) -> dict:
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts/pa86_chance_overlap.py"),
         str(registry_report), str(candidate_path), str(output)],
        cwd=ROOT, check=False,
    )
    if res.returncode not in (0, 2) or not output.is_file():
        raise subprocess.CalledProcessError(res.returncode, "pa86_chance_overlap.py")
    return json.loads(output.read_text())


def canary(features: dict[str, np.ndarray], folds: list[dict], fp: np.ndarray) -> dict:
    region = np.zeros(fp.shape, bool)
    hidden = np.zeros(fp.shape, bool)
    masked_known = np.zeros(fp.shape, bool)
    for f in folds:
        region |= np.asarray(f["region"], bool)
        hidden |= np.asarray(f["hidden_all"], bool)
        masked_known |= np.asarray(f["masked_known"], bool)
    active = region & fp & ~masked_known
    truth = active & hidden
    neg = active & ~truth
    p = np.flatnonzero(truth.ravel())
    q = np.flatnonzero(neg.ravel())
    rng = np.random.default_rng(86_1024)
    q = rng.choice(q, size=min(300_000, q.size), replace=False)
    y = np.r_[np.ones(p.size), np.zeros(q.size)]
    out = {}
    for name in feature_names():
        v = features[name].ravel()
        vals = np.r_[v[p], v[q]].astype(np.float64)
        a = float(roc_auc_score(y, vals)) if np.ptp(vals) else 0.5
        out[name] = {
            "evidence_class": "LEAKAGE-CANARY",
            "auc": a,
            "discriminative_auc": max(a, 1.0 - a),
            "threshold": 0.90,
            "leakage_flag": bool(max(a, 1.0 - a) > 0.90),
        }
    return out


def write_candidate(dots: np.ndarray, g: grid.Grid, name: str, note: str,
                    metadata: dict) -> dict:
    pred = np.where(dots & g.footprint, 1.0, 0.0).astype(np.float32)
    path = OUT_DIR / f"{name}.tif"
    receipt = submission_writer.write_submission(
        path, pred, ROOT / "data/bridge/sample_submission.tif", g.footprint,
        note=note, name=name, catalogue=g.catalogue, metadata=metadata,
    )
    # Independent read-back, not the writer's in-memory report.
    disk = validate.validate(path, g.footprint, g.catalogue)
    if not disk["all_checks_passed"]:
        raise RuntimeError("independent on-disk validator failed")
    receipt["independent_disk_validation"] = disk
    path.with_suffix(".json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    return receipt


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    started = time.time()
    # Historical H86E-MMT negative lane is archived; fail closed on the pinned witness.
    preflight = {"status": "FEASIBLE"}
    preregistration = require_preregistration()
    g = grid.load_grid(ROOT / "data/bridge")
    if not FEATURE_TIF.is_file():
        raise FileNotFoundError(f"missing pinned feature raster: {FEATURE_TIF}")
    fp, cat = g.footprint, g.catalogue
    folds, quad = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)

    fields = build_marker_features(FEATURE_TIF, fp)
    feature_files = {name: str(WORK_DIR / f"h86e_mmt_{name}.npy")
                     for name in feature_names()}
    feature_hashes = {name: save_array(Path(feature_files[name]), fields[name])
                      for name in feature_names()}
    leakage = canary(fields, folds, fp)
    if any(v["leakage_flag"] for v in leakage.values()):
        raise RuntimeError("STOP: a single H86E-MMT feature exceeds the 0.90 leakage-canary threshold")

    arms = {
        "E1_mmt_tc_decoupled": fields["mmt_tc_decoupled"],
        "E2_mmt_translation": fields["mmt_translation"],
        "E3_mmt_edge_control": fields["mmt_edge_control"],
    }
    preregistered_ids = {arm["id"] for arm in preregistration["arms"]}
    if set(arms) - preregistered_ids:
        raise RuntimeError("H86E-MMT arm is not present in the frozen preregistration")
    # D28 is a fold-fair geometry control, not a new candidate. It is rebuilt
    # with the shared visible-catalogue collar on this exact split.
    d28 = load_binary(D28) & fp
    holdout_terms = {}
    holdout_per_fold = {}
    holdout_examples = {}
    for arm, surface in arms.items():
        terms, per, example = holdout_arm(surface, folds, fp, BUDGET)
        holdout_terms[arm] = terms
        holdout_per_fold[arm] = per
        holdout_examples[arm] = example
    d28_terms, d28_per, d28_example = holdout_binary_control(d28, folds, fp, collar_px=2.0)
    holdout_terms["R0_D28_visible_collar"] = d28_terms
    holdout_per_fold["R0_D28_visible_collar"] = d28_per
    holdout_examples["R0_D28_visible_collar"] = d28_example

    pooled = EH.pooled_summary(
        holdout_terms,
        draws=1000,
        seed=86_1024,
        candidate="E1_mmt_tc_decoupled",
    )
    current_best = json.loads((EV_DIR / "lane86c_results.json").read_text())[
        "holdout_buffered_whole_components"
    ]["scores"]["E3_kslb_noisyor_44k"]
    e1 = pooled["scores"]["E1_mmt_tc_decoupled"]
    d28_score = pooled["scores"]["R0_D28_visible_collar"]
    best_delta = pooled["paired_differences"][pooled["best_comparable_control"]]
    beats_current = bool(e1["dti"] > current_best["dti"] and e1["ci95"][0] > current_best["ci95"][1])
    beats_controls = bool(best_delta["ci95"][0] > 0)

    # Final surface is fixed before registry checks.  No final dots exist yet.
    final_surface = fields["mmt_tc_decoupled"].copy()
    # Registry surface comparison uses the same bounded probability convention
    # as a submission; the raw physical response remains in the feature receipt.
    registry_surface = rank01(final_surface, fp)
    surface_path = WORK_DIR / "h86e_mmt_final_surface.npy"
    save_array(surface_path, registry_surface)
    surface_report_path = EV_DIR / "h86e-mmt-registry-surface.json"
    surface_report = run_registry_check(surface_path, surface_report_path, surface=True)
    surface_gate = bool(surface_report.get("surface_gate_pass") and
                        surface_report["inventory_rasters_missing"] == [] and
                        surface_report["errors"] == [])
    if not surface_gate:
        raise RuntimeError("STOP: H86E-MMT complete surface registry gate failed before placement")

    # Placement uses the full catalogue only after the pre-placement surface gate.
    dcat = ndi.distance_transform_edt(~cat)
    allowed = fp & (dcat > 3.0)
    final_dots = make_dots(final_surface, allowed, BUDGET)
    dots_path = WORK_DIR / "h86e_mmt_final_dots.npy"
    save_array(dots_path, final_dots.astype(np.float32))
    dots_report_path = EV_DIR / "h86e-mmt-registry-final-dots.json"
    dots_report = run_registry_check(dots_path, dots_report_path, surface=False)
    chance_path = EV_DIR / "h86e-mmt-pa86-chance-overlap.json"
    chance = run_chance_check(dots_report_path, dots_path, chance_path)
    registry_gate = bool(
        dots_report.get("final_dots_gate_pass")
        and dots_report["inventory_rasters_missing"] == []
        and dots_report["errors"] == []
        and chance["gate_pass"]
    )
    if not registry_gate:
        raise RuntimeError("STOP: H86E-MMT final-dot registry gate failed before serialization")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
    name = f"gems86-h86e-mmt-marker-translation-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"
    note = ("H86E-MMT magnetic marker translation + TC decoupling; "
            "HOLDOUT-DTI negative or selector review required; no slot used")[:140]
    receipt = write_candidate(
        final_dots, g, name, note,
        metadata={
            "lane": "H86E-MMT",
            "hypothesis": "non-zero cross-corridor magnetic-marker translation",
            "budget": BUDGET,
            "feature_hashes": feature_hashes,
            "surface_sha256": sha256(surface_path),
            "dots_sha256": sha256(dots_path),
            "registry_surface_evidence": str(surface_report_path.relative_to(ROOT)),
            "registry_final_evidence": str(dots_report_path.relative_to(ROOT)),
            "chance_overlap_evidence": str(chance_path.relative_to(ROOT)),
        },
    )

    # ``promote`` is only an internal scientific verdict.  Weekly-slot approval
    # is always false; the separate selector must have an organizer receipt.
    verdict = "promote" if (beats_current and beats_controls and registry_gate) else "negative"
    reasons = []
    if not beats_current:
        reasons.append("candidate does not beat current same-instrument HOLDOUT-DTI best with separated CIs")
    if not beats_controls:
        reasons.append("paired HOLDOUT-DTI delta versus best preregistered control is not strictly positive")
    if not registry_gate:
        reasons.append("registry uniqueness gate failed")
    if not reasons:
        reasons.append("scientific and like-for-like registry gates passed; separate organizer selector still required")

    run_card = {
        "schema": "gems86.h86e-mmt-run-card.v1",
        "lane": "H86E-MMT",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {
            "document": str((ROOT / "research/H86E_MMT_PREREGISTRATION.md").relative_to(ROOT)),
            "machine_readable": str(PREREGISTRATION.relative_to(ROOT)),
            "arm_ids": sorted(arms),
        },
        "hypothesis": (
            "Buried accommodation-zone or oblique Walker Lane faults may laterally translate "
            "magnetic marker horizons without a Quaternary surface scarp. A non-zero local "
            "cross-corridor lag between RTP and analytical magnetic-tilt gradients should be "
            "more specific than a pointwise magnetic edge."
        ),
        "mechanism": (
            "Bands 2, 3, and 9 form RTP and analytical magnetic tilt; eight oblique orientations "
            "compare directional gradients at 200-600 m non-zero lags, subtract the zero-lag "
            "registration control, downweight E-W/N-S survey-axis responses, and use Band 6 TC "
            "gradient quietness only as a radiometric decoupling weight."
        ),
        "named_non_fault_process": (
            "Unfaulted lithologic or intrusive contacts, remanent/reversed-polarity volcanic "
            "units, and GeoDAWN flight-line/tie-line leveling seams can create the same apparent "
            "magnetic phase shift."
        ),
        "source_layers": [
            "training_features.tif Band 2 rtp",
            "training_features.tif Bands 3 tmi_hg and 9 tmi_vg",
            "training_features.tif Band 6 tc, pixel-verified as radiometric total count",
        ],
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "design": "buffered whole-component quadrant draw, seed 20, hide fraction 0.20, visible-fault collar 3 px, pooled 200-px physical blocks",
            "withheld_positive_pixels": int(e1["withheld_positive_pixels"]),
            "candidate": e1,
            "paired_delta_vs_best_preregistered_control": best_delta,
            "best_preregistered_control": pooled["best_comparable_control"],
            "R0_D28_visible_collar": d28_score,
            "current_holdout_best_same_split": {
                "evidence_class": "HOLDOUT-DTI",
                "source": "docs/evidence/lane86c_results.json",
                "arm": "E3_kslb_noisyor_44k",
                "dti": current_best["dti"],
                "ci95": current_best["ci95"],
                "note": "historical same-split comparator; not re-run by this lane",
            },
            "beats_current_with_separated_ci": beats_current,
            "paired_delta_beats_control": beats_controls,
            "all_arms": pooled["scores"],
            "paired_differences": pooled["paired_differences"],
            "leakage_canary": leakage,
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "surface_preplacement": {
                "report": str(surface_report_path.relative_to(ROOT)),
                "registry_rasters_measured": surface_report["registry_rasters_measured"],
                "registry_rasters_missing": len(surface_report["inventory_rasters_missing"]),
                "registry_errors": surface_report["errors"],
                "registry_rasters_checked": surface_report["shared_summary"]["registry_rasters_checked"],
                "registry_rasters_expected": surface_report["shared_summary"]["registry_rasters_expected"],
                "complete_accessible_scan": surface_report["shared_summary"]["complete_accessible_scan"],
                "byte_unique_among_checked": surface_report["shared_summary"]["byte_unique_among_checked"],
                "pixel_unique_among_checked": surface_report["shared_summary"]["pixel_unique_among_checked"],
                "surface_gate_pass": surface_gate,
                "two_phase": surface_report["two_phase"],
            },
            "final_dots": {
                "report": str(dots_report_path.relative_to(ROOT)),
                "registry_rasters_measured": dots_report["registry_rasters_measured"],
                "registry_rasters_missing": len(dots_report["inventory_rasters_missing"]),
                "registry_errors": dots_report["errors"],
                "registry_rasters_checked": dots_report["shared_summary"]["registry_rasters_checked"],
                "registry_rasters_expected": dots_report["shared_summary"]["registry_rasters_expected"],
                "complete_accessible_scan": dots_report["shared_summary"]["complete_accessible_scan"],
                "byte_unique_among_checked": dots_report["shared_summary"]["byte_unique_among_checked"],
                "pixel_unique_among_checked": dots_report["shared_summary"]["pixel_unique_among_checked"],
                "final_dots_gate_pass": dots_report.get("final_dots_gate_pass"),
                "two_phase": dots_report["two_phase"],
            },
            "pa86_02": chance,
            "literal_dense_surface_note": (
                "The inherited literal support reading is reported unchanged. A full-support "
                "continuous prior makes literal forward overlap 1.0 for every nonempty dot set; "
                "PA-86-01/02 keeps this firing visible and applies rank correlation to surfaces "
                "and dot-overlap only to dot fields."
            ),
        },
        "raster_sha256": receipt["sha256"],
        "validator_output": {
            "evidence_class": "LOCAL-FORMAT-VALIDATION",
            "all_checks_passed": receipt["independent_disk_validation"]["all_checks_passed"],
            "no_nan_inside_footprint": receipt["independent_disk_validation"]["checks"]["in_footprint_all_finite"],
            "values_in_0_1": receipt["independent_disk_validation"]["checks"]["range_0_1_guaranteed"],
            "crs_shape_transform_match": all(
                receipt["independent_disk_validation"]["checks"][key]
                for key in ("crs_epsg_32611", "dimensions_3730x3292",
                            "transform_matches_sample_submission")
            ),
            "checks": receipt["independent_disk_validation"]["checks"],
            "positive_pixels": receipt["independent_disk_validation"]["emitted_positive_pixels"],
            "min": receipt["independent_disk_validation"]["min"],
            "max": receipt["independent_disk_validation"]["max"],
        },
        "submission_name": name,
        "note": note,
        "note_chars": len(note),
        "verdict": verdict,
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "decision": "SELECTOR STEP REQUIRED" if verdict == "promote" else "DO NOT SUBMIT",
        "decision_reason": "; ".join(reasons),
        "experiments_run": 3,
        "preflight": preflight,
        "runtime_seconds": time.time() - started,
    }
    card_path = EV_DIR / "h86e-mmt-run-card.json"
    card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "submission": str((OUT_DIR / f"{name}.tif").relative_to(ROOT)),
        "sha256": receipt["sha256"],
        "holdout_dti": e1["dti"],
        "holdout_ci95": e1["ci95"],
        "current_holdout_best": current_best["dti"],
        "registry_gate": registry_gate,
        "verdict": verdict,
        "decision": run_card["decision"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
