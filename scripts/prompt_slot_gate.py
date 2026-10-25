"""Apply the owner's stricter holdout/cache/registry requirements to a lane card.

This is a read-only safety overlay. It does not change the H86G-EDTI lane's
own preregistered result, select a submission, or authenticate any live score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(root: Path, rel: str) -> dict:
    with (root / rel).open(encoding="utf-8") as stream:
        return json.load(stream)


def build_gate(root: Path = ROOT) -> dict:
    candidate_path = "docs/evidence/h86g-edti-run-card.json"
    best_path = "docs/evidence/h86f-ewcs-run-card.json"
    cache_path = "docs/evidence/session-cf73474c-data.json"
    registry_path = "docs/evidence/registry-input-grid-review-20261025.json"
    candidate_registry_path = "docs/evidence/h86g-edti-registry.json"
    candidate = read_json(root, candidate_path)
    incumbent = read_json(root, best_path)
    cache = read_json(root, cache_path)
    registry = read_json(root, registry_path)
    candidate_registry = read_json(root, candidate_registry_path)

    c_hold = candidate["holdout_dti"]["candidate"]
    b_hold = incumbent["holdout_dti"]["candidate"]
    same_eval = c_hold["evaluator_version"] == b_hold["evaluator_version"]
    same_count = c_hold["withheld_positive_pixels"] == b_hold["withheld_positive_pixels"]
    if not (same_eval and same_count):
        raise ValueError("Cannot compare prompt's same-split incumbent without matching evaluator and withheld count")
    local_unique = candidate["uniqueness"]
    validation = candidate["validator_output"]
    note = candidate["note"]
    if len(note) != candidate["note_chars"] or len(note) > 140:
        raise ValueError("Candidate note does not match its receipt or exceeds the portal limit")

    reasons = []
    if float(c_hold["dti"]) <= float(b_hold["dti"]):
        reasons.append("The candidate HOLDOUT-DTI point estimate does not exceed the current same-evaluator, same-withheld-count repository incumbent; a paired superiority test against that incumbent is absent.")
    if cache["actual_shared_feature_stack_restored"] is not True:
        reasons.append("The actual shared template cached feature stack is not present; native raw bands are not an authorized substitute under the request.")
    if registry["all_grids_compatible"] is not True or registry["uniqueness_clearance"] is not True:
        reasons.append("The pinned registry inventory is not fully cleared: incompatible/invalid rows remain and this is not a complete candidate comparison.")
    if local_unique["gate_pass"] is not True:
        reasons.append("The candidate failed its local like-for-like uniqueness measurement.")
    if validation["all_checks_passed"] is not True:
        reasons.append("The local GeoTIFF validator failed.")

    raster_path = candidate["submission_file"]
    raster_digest = sha256(root / raster_path)
    if raster_digest != candidate["raster_sha256"]:
        raise ValueError("The H86G TIFF bytes do not match the lane card SHA-256")
    evidence_paths = [candidate_path, best_path, cache_path, registry_path, candidate_registry_path, raster_path]
    return {
        "schema": "gems86.prompt-slot-gate.v1",
        "decision": "DO_NOT_SUBMIT_UNDER_CURRENT_REQUEST",
        "evidence_class": "PROMPT-GATE-REVIEW",
        "candidate_lane": candidate["lane"],
        "hypothesis": candidate["hypothesis"],
        "mechanism": candidate["mechanism"],
        "named_non_fault_process": candidate.get("non_fault_mimic") or "Unfaulted lithologic contacts and volcanic-flow boundaries; see the preregistration for the full named mimic set.",
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": c_hold["evaluator_version"],
            "withheld_positive_count": c_hold["withheld_positive_pixels"],
            "value": c_hold["dti"],
            "ci95": c_hold["ci95"],
            "current_same_evaluator_same_count_incumbent": {
                "evidence_class": "HOLDOUT-DTI",
                "lane": incumbent["lane"],
                "evaluator_version": b_hold["evaluator_version"],
                "withheld_positive_count": b_hold["withheld_positive_pixels"],
                "value": b_hold["dti"],
                "ci95": b_hold["ci95"],
                "comparison_note": "Same evaluator and withheld-positive count; this cross-lane contrast is descriptive, not a paired significance test. H86G-EDTI does not demonstrate that it beats the incumbent."
            },
            "paired_delta_vs_best_H86G_control": candidate["holdout_dti"]["pooled"]["paired_differences"][candidate["holdout_dti"]["pooled"]["best_comparable_control"]],
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "local_dot_field_count": len(candidate_registry["rows"]),
            "surface_max_spearman_local_scope": local_unique["max_spearman"],
            "final_dot_forward_overlap_3px_local_scope": local_unique["max_forward_3px_overlap_dot_fields"],
            "rho_limit": 0.90,
            "overlap_limit": 0.70,
            "local_gate_pass": local_unique["gate_pass"],
            "full_registry_clearance": False,
            "inventory_rasters": registry["indexed_rasters_expected"],
            "grid_compatible_rasters": registry["grid_compatible_rasters"],
            "incompatible_or_invalid_rasters": registry["grid_incompatible_or_invalid_rasters"],
            "scope_note": "Candidate comparisons are against the pinned local dot-field subset. The 690-file byte/grid inventory is not a candidate uniqueness pass; incompatible rows remain blockers."
        },
        "shared_feature_cache_restored": cache["actual_shared_feature_stack_restored"],
        "raster_sha256": candidate["raster_sha256"],
        "validator_output": {
            "class": "local-format-validation; not organizer acceptance",
            "no_nan_inside_footprint": validation["checks"]["in_footprint_all_finite"],
            "values_in_0_1": validation["checks"]["in_footprint_range_0_1"],
            "crs_shape_transform_match": all(validation["checks"][key] for key in ("dimensions_3730x3292", "crs_epsg_32611", "transform_matches_sample_submission")),
            "single_band": validation["checks"]["single_band"],
            "all_local_checks_passed": validation["all_checks_passed"],
        },
        "submission_name": candidate["submission_name"],
        "note": note,
        "weekly_slot_authorized": False,
        "organizer_confirmed_score": None,
        "reasons_not_approved": reasons,
        "verdict": "negative",
        "evidence_sha256": {rel: sha256(root / rel) for rel in evidence_paths},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare generated evidence without writing")
    args = parser.parse_args(argv)
    output = ROOT / "docs/evidence/prompt-slot-gate.json"
    report = build_gate(ROOT)
    if args.check:
        existing = read_json(ROOT, "docs/evidence/prompt-slot-gate.json")
        if existing != report:
            raise SystemExit("prompt slot gate is stale")
    else:
        output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(report["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
