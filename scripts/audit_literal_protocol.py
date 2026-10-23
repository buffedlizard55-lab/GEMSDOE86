"""Recompute the H86B two-phase literal uniqueness audit; create no candidate.

This is an audit-only script. It rechecks the retained H86B final-dot TIFF
against every raster in the prior five-row cross-lane audit plus the pinned
dense witness, revalidates local file format, and records why the missing
pre-placement surface cannot clear the protocol. It never fits a model, places
dots, invokes the submission writer, or spends a competition slot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import rasterio
from gems57 import gates as GT
from gems57 import grid as G
from gems57 import uniqueness as U
from gems57 import validate as V
from scripts.strict_uniqueness import phase_status

CARD_IN = ROOT / "docs/evidence/h86b-gfco-run-card.json"
CROSSLANE_IN = ROOT / "docs/evidence/h86b_crosslane_uniqueness.json"
PREFLIGHT_IN = ROOT / "docs/evidence/protocol-preflight.json"
WITNESS = ROOT / "data/registry/dense-witness.tif"
OUTPUT = ROOT / "docs/evidence/review-20261023-run-card.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(), parse_constant=lambda value: (_ for _ in ()).throw(
        ValueError(f"Non-finite JSON constant {value!r} in {path}")))


def _expected_grid(grid):
    return (grid.shape, grid.crs, grid.transform)


def _registry_records(crosslane: dict) -> list[dict]:
    records = []
    for row in crosslane["rows"]:
        records.append({
            "repo": row.get("repo"),
            "submission": row["submission"],
            "file": row["file"],
            "sha256": row["sha256"],
        })
    preflight = _load_json(PREFLIGHT_IN)
    records.append({
        "repo": "buffedlizard55-lab/17GEMSDOE",
        "submission": Path(preflight["source_path"]).name,
        "file": str(WITNESS),
        "sha256": preflight["witness_sha256"],
    })
    # Stable deduplication by pinned bytes; keep the first public source label.
    result, seen = [], set()
    for record in records:
        if record["sha256"] not in seen:
            seen.add(record["sha256"])
            result.append(record)
    return result


def build_card() -> dict:
    h86b = _load_json(CARD_IN)
    crosslane = _load_json(CROSSLANE_IN)
    stored_preflight = _load_json(PREFLIGHT_IN)
    grid = G.load_grid(ROOT / "data/bridge")
    expected_grid = _expected_grid(grid)

    candidate = ROOT / h86b["submission_file"]
    if not candidate.is_file():
        raise FileNotFoundError(f"retained H86B audit raster is missing: {candidate}")
    candidate_sha = sha256(candidate)
    if candidate_sha != h86b["raster_sha256"]:
        raise ValueError("H86B candidate SHA256 does not match its archived run card")

    with rasterio.open(candidate) as source:
        if source.count != 1 or (source.shape, source.crs, source.transform) != expected_grid:
            raise ValueError("H86B candidate grid differs from the pinned competition grid")
        prediction = source.read(1)

    records = _registry_records(crosslane)
    final_dot_audit = U.compare_array_to_registry(
        prediction, records, grid.footprint, file_sha256=candidate_sha,
        expected_grid=expected_grid,
    )
    final_phase = phase_status(final_dot_audit)

    witness_certificate = U.saturation_certificate(
        WITNESS, grid.footprint, grid.footprint & ~grid.catalogue,
        expected_grid=expected_grid,
    )
    if witness_certificate["witness_sha256"] != stored_preflight["witness_sha256"]:
        raise ValueError("dense-witness SHA256 no longer matches the stored preflight pin")

    # The H86B surface was not retained. The exact universal bound is still
    # sufficient: the witness is positive on every footprint pixel; the lane
    # zeros the surface outside the footprint; any nonempty in-footprint
    # surface therefore has 1.0 forward overlap before placement.
    surface_audit = {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "direct_surface_raster_retained": False,
        "direct_surface_remeasurement_performed": False,
        "historical_surface_registry_rasters_checked": h86b["correlation_overlap_vs_registry"]["rasters_checked"],
        "historical_surface_max_abs_spearman": h86b["correlation_overlap_vs_registry"]["surface_worst_abs_spearman"],
        "historical_surface_scope": h86b["correlation_overlap_vs_registry"]["scope"],
        "dense_witness_positive_pixels": witness_certificate["positive_pixels"],
        "footprint_pixels": int(grid.footprint.sum()),
        "allowed_pixels": witness_certificate["allowed_pixels"],
        "uncovered_allowed_pixels": witness_certificate["uncovered_allowed_pixels"],
        "forward_3px_overlap_lower_bound": (
            1.0 if witness_certificate["universal_overlap_blocker"] else None
        ),
        "bound_is_direct_surface_measurement": False,
        "stop_required": bool(witness_certificate["universal_overlap_blocker"]),
        "basis": (
            "Exact support implication, not a replayed surface statistic: the hash-pinned witness is positive "
            "at every scored-footprint pixel; the lane's surface is zero outside the footprint. Therefore "
            "every nonempty in-footprint surface support is a subset of the witness support and has forward "
            "3-pixel overlap 1.0 (>0.70) before any placement. The surface file itself was not retained."
        ),
    }

    validator = V.validate(candidate, footprint=grid.footprint, catalogue=grid.catalogue)
    template_format = GT.format_report(
        candidate, ROOT / "data/bridge/sample_submission.tif", footprint=grid.footprint,
    )
    local_validator_pass = bool(validator["all_checks_passed"] and template_format["ok"])
    holdouts = h86b["holdout_dti"]
    note = h86b["note"]
    if len(note) > 140:
        raise ValueError("submission note exceeds the 140-character limit")

    final_rows = []
    for row in final_dot_audit["rows"]:
        final_rows.append({
            "repo": row.get("repo"),
            "submission": row.get("submission"),
            "registry_sha256": row.get("sha256"),
            "candidate_dots_within_3px_of_registry": row.get("my_dots_within_3px_of_theirs"),
            "spearman_full_footprint": row.get("spearman_full_footprint"),
            "identical_bytes": row.get("identical_bytes"),
            "identical_decoded_predictions": row.get("identical_decoded_predictions"),
            "literal_blocker": next((
                block["reasons"] for block in final_phase["blockers"]
                if block.get("submission") == row.get("submission")
            ), []),
        })

    return {
        "review_date_utc": "2026-10-23",
        "evidence_class": "AUDIT-ONLY-NEGATIVE-RUN-CARD",
        "hypothesis": h86b["hypothesis"],
        "mechanism": h86b["mechanism"],
        "named_non_fault_mimic": h86b["non_fault_mimic"],
        "candidate_generated_this_review": False,
        "experiments_run_this_review": 0,
        "historical_experiments_in_lane": h86b["experiments_run"],
        "competition_slots_used_this_review": 0,
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": h86b["holdout_dti"]["evaluator_version"],
            "withheld_positives": holdouts["buffered_whole_components_loqo"]["withheld_positives"],
            "candidate_dti": holdouts["buffered_whole_components_loqo"]["candidate_dti"],
            "ci95": holdouts["buffered_whole_components_loqo"]["ci95"],
            "paired_delta_vs_d28_incumbent": holdouts["buffered_whole_components_loqo"]["paired_delta_vs_d28"],
            "paired_delta_vs_d28_incumbent_ci95": holdouts["buffered_whole_components_loqo"]["paired_delta_vs_d28_ci95"],
            "paired_delta_vs_h33_b2_foldfair": holdouts["buffered_whole_components_loqo"]["paired_delta_vs_h33_foldfair"],
            "paired_delta_vs_h33_b2_foldfair_ci95": holdouts["buffered_whole_components_loqo"]["paired_delta_vs_h33_foldfair_ci95"],
            "point_estimate_beats_incumbents": holdouts["point_estimate_beats_all_3_holdouts"],
            "95_percent_ci_beats_incumbents": holdouts["beats_incumbent"],
            "scope_note": "This is a historical HOLDOUT-DTI measurement for the retained H86B artifact, not an organizer score and not a new experiment in this review.",
        },
        "additional_holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": h86b["holdout_dti"]["evaluator_version"],
            "segment_hide_all": holdouts["segment_hide_all"],
            "segment_hide_detached": holdouts["segment_hide_detached"],
            "scope_note": "Each view is a separately reported spatial holdout; do not combine the estimates or treat them as leaderboard scores.",
        },
        "leakage_canary": {
            "evidence_class": "HOLDOUT-FEATURE-CANARY",
            **h86b["leakage_canary_auc"],
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "pre_placement_surface": surface_audit,
            "final_dots": {
                "evidence_class": "REGISTRY-MEASUREMENT",
                "raster_sha256": candidate_sha,
                "candidate_positive_pixels": int((prediction > 0).sum()),
                "rasters_checked": final_dot_audit["registry_rasters_checked"],
                "complete_accessible_scan": final_dot_audit["complete_accessible_scan"],
                "scope": "Directly remeasured against the five hash-pinned prior rows in the existing cross-lane audit plus the pinned dense witness. This is not a complete organizer registry.",
                "rows": final_rows,
                "phase_status": final_phase,
                "stop_required": bool(final_phase["blockers"]),
            },
            "complete_registry_clearance": False,
            "decision": "negative; the surface is blocked by an exact universal bound and the final dots trigger literal overlap against prior rasters",
        },
        "raster_sha256": candidate_sha,
        "validator_output": {
            "evidence_class": "LOCAL-FORMAT-VALIDATION",
            "status": "PASS" if local_validator_pass else "FAIL",
            "shared_validator_checks": validator["checks"],
            "shared_validator_all_checks_passed": validator["all_checks_passed"],
            "template_format_ok": template_format["ok"],
            "template_format_problems": template_format["problems"],
            "emitted_positive_pixels": validator["emitted_positive_pixels"],
            "no_nan_inside_footprint": validator["checks"].get("in_footprint_all_finite") is True,
            "values_in_0_1": validator["checks"].get("in_footprint_range_0_1") is True,
            "crs_shape_transform_match": all(validator["checks"].get(key) is True for key in (
                "dimensions_3730x3292", "crs_epsg_32611", "transform_matches_sample_submission")),
            "organizer_acceptance": "not verified; no organizer receipt",
        },
        "submission_name": h86b["submission_name"],
        "submission_note": note,
        "submission_note_characters": len(note),
        "existing_artifact_path": h86b["submission_file"],
        "safe_to_download_for_audit": True,
        "safe_to_submit": False,
        "organizer_confirmed_score": None,
        "leaderboard_claims": {
            "evidence_class": "UNVERIFIED-OWNER-OR-USER-REPORTED",
            "values": [0.2778, 0.3195, 0.4413],
            "status": "No authenticated submission-page receipt in this checkout; none is treated as an ORGANIZER-CONFIRMED score or compared to HOLDOUT-DTI.",
        },
        "untried_hypotheses": "See research/NEXT_HYPOTHESES_20261023.md; four distinct concepts are ranked, and previously implemented H86B features are explicitly excluded from the novelty claims.",
        "limitations": [
            "No new candidate TIFF, model fit, holdout experiment, or competition submission was created in this review.",
            "The H86B pre-placement surface raster was not retained; the stated 1.0 overlap is an exact support bound from the pinned universal witness, not a direct replayed surface measurement.",
            "The cross-lane registry subset is incomplete and not organizer-authenticated; no uniqueness clearance can be granted.",
            "The repository's restored bridge/sample/fault rasters are owner-supplied mirrors, not independently organizer-authenticated source receipts.",
            "No fresh official competition leaderboard or submission receipt was obtained; user/owner leaderboard values remain unverified.",
            "The H86B holdout metrics are historical local HOLDOUT-DTI, not public leaderboard or organizer-confirmed scores.",
        ],
        "submission_ready": False,
        "approved_for_weekly_slot": False,
        "verdict": "negative",
        "decision": "STOP: do not generate or submit a nonempty candidate while the universal literal-overlap blocker stands.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    card = build_card()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "output": str(args.output),
        "raster_sha256": card["raster_sha256"],
        "candidate_generated_this_review": card["candidate_generated_this_review"],
        "surface_stop": card["correlation_overlap_vs_registry"]["pre_placement_surface"]["stop_required"],
        "final_dot_stop": card["correlation_overlap_vs_registry"]["final_dots"]["stop_required"],
        "submission_ready": card["submission_ready"],
        "verdict": card["verdict"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
