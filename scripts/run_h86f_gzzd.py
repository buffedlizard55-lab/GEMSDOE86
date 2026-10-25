#!/usr/bin/env python3
"""Run the preregistered H86F-GZZD Laplace gravity-curvature dipole lane.

Frozen design: ``research/H86F_GZZD_PREREGISTRATION.json`` (checked before any
computation). Three fixed arms at 44,090 dots: ``E1_gzzd_concordant``
(candidate), ``E2_gzzd_dipole`` (ablation), ``E3_gravmag_edge_control``
(unsigned-edge negative control), scored with the unmodified shared
``gems57-pooled-hide-v2`` hide-and-recover evaluator against a fold-fair
``R0_D28_visible_collar`` control on the identical split.

Fail-closed sequence (PA-86-01/02, thresholds unchanged):

1. preregistration + ``require_like_for_like`` preflight;
2. catalogue-blind features + Laplace QC (corr < +0.80 stops);
3. feature-alone leakage canary (discriminative AUC > 0.90 stops);
4. shared buffered whole-component holdout for all arms;
5. pre-placement surface registry check -- a rank-correlation firing
   (rho > 0.90) stops before placement and no TIFF is written; a
   completeness failure without a rho firing never passes, it only permits
   an explicitly negative audit TIFF (frozen in the preregistration);
6. final dots, final-dot registry check, PA-86-02 chance-overlap attempt
   (a fail-closed exception is recorded verbatim as a failed gate);
7. shared fail-closed writer + independent on-disk re-validation, run card.

No weekly slot is selected or used in any outcome. ``promote`` would mean
only "eligible for the separate human selector step".
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
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]

from gems57 import evaluate_holdout as EH, grid, holdout  # noqa: E402
from gems86_gzzd.features import build_gzzd_features, feature_names  # noqa: E402
from gems86_mmt.features import rank01  # noqa: E402
from scripts.protocol_preflight import require_like_for_like  # noqa: E402
from scripts.run_h86e_mmt import holdout_arm, load_binary, make_dots, save_array, sha256, write_candidate  # noqa: E402

BUDGET = 44_090
SEED = 20
FEATURE_TIF = ROOT / "data/training_features.tif"
D28 = ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
OUT_DIR = ROOT / "docs/downloads"
EV_DIR = ROOT / "docs/evidence"
WORK_DIR = ROOT / "data/work"
PREREGISTRATION = ROOT / "research/H86F_GZZD_PREREGISTRATION.json"
CARD_PATH = EV_DIR / "h86f-gzzd-run-card.json"
CANDIDATE_ARM = "E1_gzzd_concordant"


def require_preregistration() -> dict:
    if not PREREGISTRATION.is_file():
        raise RuntimeError(f"missing preregistration: {PREREGISTRATION}")
    doc = json.loads(PREREGISTRATION.read_text(encoding="utf-8"))
    if doc.get("lane") != "H86F-GZZD" or doc.get("status") != "frozen_before_lane_computation":
        raise RuntimeError("H86F-GZZD preregistration identity/status drifted")
    hypotheses = doc.get("ranked_hypotheses", [])
    arms = doc.get("arms", [])
    if not (3 <= len(hypotheses) <= 5):
        raise RuntimeError("H86F-GZZD preregistration must rank 3-5 hypotheses")
    if len(arms) != 3:
        raise RuntimeError("H86F-GZZD preregistration must freeze exactly 3 arms")
    required = {"layers", "transform", "non_fault_mimic", "uncatalogued_rationale",
                "novelty", "cost", "official_data"}
    if any(not required.issubset(item) for item in (*hypotheses, *arms)):
        raise RuntimeError("H86F-GZZD preregistration is missing required hypothesis/arm fields")
    if doc.get("budget") != {"max_arms": 3, "max_hours": 2, "dots": BUDGET}:
        raise RuntimeError("H86F-GZZD budget drifted from the 3-arm/2-hour/44090-dot limit")
    holdout_doc = doc.get("holdout", {})
    if holdout_doc.get("alpha") != 0.2 or holdout_doc.get("beta") != 0.8 or holdout_doc.get("kernel_m") != 300:
        raise RuntimeError("H86F-GZZD DTI weights/kernel drifted")
    return doc


def canary(features: dict[str, np.ndarray], folds: list[dict], fp: np.ndarray) -> dict:
    """Feature-alone leakage canary on withheld positives (shared split)."""
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
        v = features[name].ravel()
        vals = np.r_[v[p], v[q]].astype(np.float64)
        auc = float(roc_auc_score(y, vals)) if np.ptp(vals) else 0.5
        out[name] = {
            "evidence_class": "LEAKAGE-CANARY",
            "auc": auc,
            "discriminative_auc": max(auc, 1.0 - auc),
            "threshold": 0.90,
            "leakage_flag": bool(max(auc, 1.0 - auc) > 0.90),
        }
    return out


def run_registry_check(array_path: Path, output: Path, *, surface: bool) -> tuple[dict, int]:
    cmd = [sys.executable, str(ROOT / "scripts/check_h86e_registry.py"), str(array_path), str(output)]
    if surface:
        cmd.append("--surface")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if not output.is_file():
        raise RuntimeError(
            f"registry check produced no report (rc={proc.returncode}): {proc.stderr[-2000:]}"
        )
    return json.loads(output.read_text()), proc.returncode


def run_chance_check(registry_report: Path, candidate_path: Path, output: Path) -> dict:
    """Attempt PA-86-02; a fail-closed exception is a recorded failed gate."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/pa86_chance_overlap.py"),
         str(registry_report), str(candidate_path), str(output)],
        cwd=ROOT, capture_output=True, text=True,
    )
    if output.is_file():
        report = json.loads(output.read_text())
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
        "note": "pa86_chance_overlap.py refused to certify (binding/completeness); recorded verbatim, never bypassed with a private computation.",
    }


def registry_summary(report: dict, returncode: int) -> dict:
    shared = report.get("shared_summary", {})
    return {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "runner_returncode": returncode,
        "registry_rasters_expected": report.get("registry_rasters_expected", shared.get("registry_rasters_expected")),
        "registry_rasters_measured": report.get("registry_rasters_measured"),
        "registry_rasters_missing": len(report.get("inventory_rasters_missing", [])),
        "registry_errors": report.get("errors", []),
        "registry_complete_for_index": report.get("registry_complete_for_index"),
        "complete_accessible_scan": shared.get("complete_accessible_scan"),
        "byte_unique_among_checked": shared.get("byte_unique_among_checked"),
        "pixel_unique_among_checked": shared.get("pixel_unique_among_checked"),
        "worst_spearman_full_footprint": shared.get("worst_spearman_full_footprint"),
        "worst_spearman_submission": shared.get("worst_rho_submission"),
        "worst_dot_overlap": shared.get("worst_dot_overlap"),
        "worst_overlap_submission": shared.get("worst_overlap_submission"),
        "literal_gate_pass": report.get("literal_gate_pass"),
        "two_phase": report.get("two_phase"),
        "top15_by_forward_overlap": report.get("top15_by_forward_overlap"),
        "top15_by_spearman": report.get("top15_by_spearman"),
        "scope": report.get("scope"),
    }


def main() -> int:
    started = time.time()
    preregistration = require_preregistration()
    preflight = require_like_for_like()
    g = grid.load_grid(ROOT / "data/bridge")
    if not FEATURE_TIF.is_file():
        raise FileNotFoundError(f"missing pinned feature raster: {FEATURE_TIF}")
    fp, cat = g.footprint, g.catalogue
    folds, _quad = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)

    fields, qc = build_gzzd_features(FEATURE_TIF, fp)
    if qc["corr_gzz_vs_neg_laplacian_band13"] < qc["fail_closed_below"]:
        raise RuntimeError(f"STOP: Laplace QC failed ({qc})")
    feature_hashes = {
        name: save_array(WORK_DIR / f"h86f_{name}.npy", fields[name]) for name in feature_names()
    }
    leakage = canary(fields, folds, fp)
    if any(v["leakage_flag"] for v in leakage.values()):
        raise RuntimeError("STOP: a single H86F-GZZD field exceeds the 0.90 leakage-canary threshold")

    arms = {
        "E1_gzzd_concordant": fields["gzzd_concordant"],
        "E2_gzzd_dipole": fields["gzzd_dipole"],
        "E3_gravmag_edge_control": fields["gzzd_edge_control"],
    }
    preregistered_ids = {arm["id"] for arm in preregistration["arms"]}
    if set(arms) != preregistered_ids:
        raise RuntimeError("H86F-GZZD arms differ from the frozen preregistration")

    holdout_terms, holdout_per_fold = {}, {}
    for arm, surface in arms.items():
        terms, per, _example = holdout_arm(surface, folds, fp, BUDGET)
        holdout_terms[arm] = terms
        holdout_per_fold[arm] = per
    d28 = load_binary(D28) & fp
    d28_terms, d28_per, _ = holdout_arm(d28.astype(np.float32), folds, fp, BUDGET)
    holdout_terms["R0_D28_visible_collar"] = d28_terms
    holdout_per_fold["R0_D28_visible_collar"] = d28_per

    pooled = EH.pooled_summary(holdout_terms, draws=1000, seed=86_1025, candidate=CANDIDATE_ARM)
    current_best = json.loads((EV_DIR / "lane86c_results.json").read_text())[
        "holdout_buffered_whole_components"
    ]["scores"]["E3_kslb_noisyor_44k"]
    e1 = pooled["scores"][CANDIDATE_ARM]
    best_delta = pooled["paired_differences"][pooled["best_comparable_control"]]
    beats_current = bool(e1["dti"] > current_best["dti"] and e1["ci95"][0] > current_best["ci95"][1])
    beats_controls = bool(best_delta["ci95"][0] > 0)

    # Pre-placement surface registry check (rank correlation decides drift here).
    final_surface = fields["gzzd_concordant"].copy()
    surface_path = WORK_DIR / "h86f_gzzd_final_surface.npy"
    save_array(surface_path, rank01(final_surface, fp))
    surface_report_path = EV_DIR / "h86f-gzzd-registry-surface.json"
    surface_report, surface_rc = run_registry_check(surface_path, surface_report_path, surface=True)
    surface_gate = bool(surface_report.get("surface_gate_pass"))
    rho_firings = int(
        surface_report.get("two_phase", {}).get("literal_reading", {}).get("rho_firings", -1)
    )

    base_card = {
        "schema": "gems86.h86f-gzzd-run-card.v1",
        "lane": "H86F-GZZD",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {
            "document": "research/H86F_GZZD_PREREGISTRATION.md",
            "machine_readable": str(PREREGISTRATION.relative_to(ROOT)),
            "frozen_utc": preregistration["frozen_utc"],
            "ranked_hypothesis_ids": [h["id"] for h in preregistration["ranked_hypotheses"]],
            "arm_ids": sorted(arms),
        },
        "hypothesis": (
            "A basement fault buried under basin fill steps the density interface, producing a "
            "paired opposite-sign dipole in regularized Laplace gravity curvature gzz with a zero "
            "crossing over the step, whose polarity agrees with the basement-depth and gravity "
            "flank steps, even where no Quaternary scarp exists to catalogue."
        ),
        "mechanism": (
            "gzz = -(d_x Band18 + d_row Band11) at sigma=500 m from the pixel-verified signed "
            "gravity vector (+Band18, -Band11); antisymmetric +/-200-400 m flank pairing of gzz "
            "over 8 strike azimuths with 900 m strike smoothing; E1 applies a soft polarity gate "
            "(1.0 concordant / 0.25 discordant) from Band 15 vs Band 13 flank-step signs; shared "
            "3-px decimated emission at 44,090 dots, >3 px off the (visible/full) catalogue."
        ),
        "named_non_fault_process": (
            "Unfaulted paleovalley or caldera-moat margins infilled by low-density sediment, and "
            "gravity-basement inversion artifacts (Bands 13/15 share inversion ancestry)."
        ),
        "source_layers": [
            "training_features.tif Band 18 iso_grav_anom_hg (signed +dg/dx_east)",
            "training_features.tif Band 11 iso_grav_anom_vg (signed +dg/drow_south)",
            "training_features.tif Band 13 iso_grav_anom",
            "training_features.tif Band 15 depth_to_base_surf",
            "training_features.tif Band 5 iso_grav_anom_slope (E3 control only)",
        ],
        "band_physics_qc": qc,
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "design": "buffered whole-component quadrant draw, seed 20, hide fraction 0.20, visible-fault collar 3 px, pooled 200-px physical blocks",
            "withheld_positive_pixels": int(e1["withheld_positive_pixels"]),
            "candidate": e1,
            "paired_delta_vs_best_preregistered_control": best_delta,
            "best_preregistered_control": pooled["best_comparable_control"],
            "R0_D28_visible_collar": pooled["scores"]["R0_D28_visible_collar"],
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
            "per_fold": holdout_per_fold,
            "leakage_canary": leakage,
        },
        "preflight": preflight,
        "experiments_run": 3,
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
    }

    if rho_firings != 0:
        # Protocol rule 1: surface lane drift (or an unreadable two-phase
        # summary) stops before placement. No TIFF is written.
        card = {
            **base_card,
            "correlation_overlap_vs_registry": {
                "surface_preplacement": {
                    "report": str(surface_report_path.relative_to(ROOT)),
                    **registry_summary(surface_report, surface_rc),
                    "surface_gate_pass": surface_gate,
                    "rho_firings": rho_firings,
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
            "note": "STOP: pre-placement surface rank-correlation firing; logged as duplicate, no TIFF placed, no slot used.",
            "note_chars": 107,
            "verdict": "negative",
            "duplicate": True,
            "decision": "DO NOT SUBMIT",
            "decision_reason": "surface rho firing before placement (protocol rule 1)",
            "runtime_seconds": time.time() - started,
        }
        card["note_chars"] = len(card["note"])
        CARD_PATH.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"decision": "DO NOT SUBMIT", "reason": "surface_rho_stop",
                          "rho_firings": rho_firings, "holdout_dti": e1["dti"]}, indent=2))
        return 0

    # Placement (full catalogue collar) only after the surface check above.
    dcat = ndi.distance_transform_edt(~cat)
    allowed = fp & (dcat > 3.0)
    final_dots = make_dots(final_surface, allowed, BUDGET)
    dots_path = WORK_DIR / "h86f_gzzd_final_dots.npy"
    save_array(dots_path, final_dots.astype(np.float32))
    dots_report_path = EV_DIR / "h86f-gzzd-registry-final-dots.json"
    dots_report, dots_rc = run_registry_check(dots_path, dots_report_path, surface=False)
    chance_path = EV_DIR / "h86f-gzzd-pa86-chance-overlap.json"
    chance = run_chance_check(dots_report_path, dots_path, chance_path)
    final_gate = bool(dots_report.get("final_dots_gate_pass"))
    registry_gate = bool(surface_gate and final_gate and chance.get("gate_pass") is True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
    name = f"gems86-h86f-gzzd-laplace-dipole-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"
    note = "H86F-GZZD Laplace gzz dipole polarity-concordant; see run card gates; no slot used"[:140]
    receipt = write_candidate(
        final_dots, g, name, note,
        metadata={
            "lane": "H86F-GZZD",
            "hypothesis": "regularized Laplace gzz dipole over buried basement step + polarity concordance",
            "budget": BUDGET,
            "feature_hashes": feature_hashes,
            "band_physics_qc": qc,
            "surface_sha256": sha256(surface_path),
            "dots_sha256": sha256(dots_path),
            "registry_surface_evidence": str(surface_report_path.relative_to(ROOT)),
            "registry_final_evidence": str(dots_report_path.relative_to(ROOT)),
            "chance_overlap_evidence": str(chance_path.relative_to(ROOT)) if chance_path.is_file() else "FAILED_CLOSED_NO_REPORT (see run card)",
        },
    )

    verdict = "promote" if (beats_current and beats_controls and registry_gate) else "negative"
    reasons = []
    if not beats_current:
        reasons.append("candidate does not beat current same-split HOLDOUT-DTI best with separated CIs")
    if not beats_controls:
        reasons.append("paired HOLDOUT-DTI delta versus best preregistered control is not strictly positive")
    if not surface_gate:
        reasons.append("pre-placement surface registry gate did not pass (completeness/validity; no rho firing)")
    if not final_gate:
        reasons.append("final-dot like-for-like registry gate failed")
    if chance.get("gate_pass") is not True:
        reasons.append("PA-86-02 chance-overlap gate did not pass")
    if not reasons:
        reasons.append("scientific and like-for-like registry gates passed; separate human selector still required")

    card = {
        **base_card,
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "surface_preplacement": {
                "report": str(surface_report_path.relative_to(ROOT)),
                **registry_summary(surface_report, surface_rc),
                "surface_gate_pass": surface_gate,
                "rho_firings": rho_firings,
            },
            "final_dots": {
                "report": str(dots_report_path.relative_to(ROOT)),
                **registry_summary(dots_report, dots_rc),
                "final_dots_gate_pass": final_gate,
            },
            "pa86_02": chance,
            "literal_dense_surface_note": (
                "The literal support reading is reported unchanged in both registry reports; a "
                "full-support continuous prior gives literal forward overlap 1.0 for every nonempty "
                "dot set. PA-86-01/02 keeps that firing visible and decides on rank correlation "
                "(every raster) plus dot-field overlap; thresholds are unchanged."
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
                for key in ("crs_epsg_32611", "dimensions_3730x3292", "transform_matches_sample_submission")
            ),
            "checks": receipt["independent_disk_validation"]["checks"],
            "positive_pixels": receipt["independent_disk_validation"]["emitted_positive_pixels"],
            "min": receipt["independent_disk_validation"]["min"],
            "max": receipt["independent_disk_validation"]["max"],
        },
        "submission_name": name,
        "submission_file": f"docs/downloads/{name}.tif",
        "note": note,
        "note_chars": len(note),
        "verdict": verdict,
        "duplicate": bool(not registry_gate),
        "decision": "SELECTOR STEP REQUIRED" if verdict == "promote" else "DO NOT SUBMIT",
        "decision_reason": "; ".join(reasons),
        "runtime_seconds": time.time() - started,
    }
    CARD_PATH.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "submission": f"docs/downloads/{name}.tif",
        "sha256": receipt["sha256"],
        "holdout_dti": e1["dti"],
        "holdout_ci95": e1["ci95"],
        "current_holdout_best": current_best["dti"],
        "beats_current": beats_current,
        "beats_controls": beats_controls,
        "surface_gate": surface_gate,
        "final_dots_gate": final_gate,
        "pa86_gate": chance.get("gate_pass"),
        "verdict": verdict,
        "decision": card["decision"],
        "runtime_seconds": card["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
