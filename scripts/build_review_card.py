#!/usr/bin/env python3
"""Bind this independent read-only session's negative card to measured evidence.

Not a model runner, submission writer, method authorization or slot selector.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_release import sha256, strict_json, write_json  # noqa: E402


def build_card(root: Path = ROOT) -> dict:
    proposal_path = root / "registry/h86g_hypotheses.json"
    proposals = strict_json(proposal_path)
    top = proposals["hypotheses"][0]
    report = strict_json(root / "docs/evidence/release-readiness.json")
    registry = strict_json(root / "docs/evidence/all-artifacts-registry.json")
    inputs = strict_json(root / "docs/evidence/registry-input-grid-review-20261025.json")
    proof = strict_json(root / "docs/evidence/protocol-preflight.json")
    if (proposals["lane_assignment"] is not None or top["status"] != "NOT_RUN_PROTOCOL_STOP"
            or report["audit_ok"] is not True or report["safe_to_submit"] is not False
            or report["new_candidate_generated"] is not False
            or proof["universal_overlap_blocker"] is not True
            or inputs["uniqueness_clearance"] is not False):
        raise ValueError("This review card only records the measured no-lane, no-candidate negative state")
    paths = ["research/REQUEST_20261025.md", "registry/h86g_hypotheses.json",
             "data/prepared_manifest.json", "docs/evidence/session-cf73474c-data.json",
             "docs/evidence/registry-input-grid-review-20261025.json",
             "docs/evidence/concurrent-artifact-review-20261025.json",
             "docs/evidence/protocol-preflight.json", "docs/evidence/release-readiness.json",
             "docs/evidence/all-artifacts-registry.json"]
    return dict(
        schema="gems86.independent-session-run-card.v1", session="cf73474c", date_utc="2026-10-25",
        evidence_class="RUN-CARD", measured_registry_utc=registry["measured_utc"],
        hypothesis=f"{top['id']}: {top['name']} (ranked proposal only; not implemented or authorized)",
        mechanism=top["physical_signature"], non_fault_mimic=top["non_fault_mimic"], lane_assignment=None,
        holdout_dti=dict(evidence_class="HOLDOUT-DTI", status="NOT_RUN_PROTOCOL_STOP", value=None,
            ci95=None, evaluator_version=None, planned_evaluator_version="gems57-pooled-hide-v2",
            withheld_positive_count=None, paired_delta=None, paired_ci95=None),
        leakage_canary=dict(status="NOT_RUN_PROTOCOL_STOP", auc=None),
        correlation_overlap_vs_registry=dict(evidence_class="REGISTRY-MEASUREMENT",
            candidate_rho=None, candidate_dot_overlap_3px=None,
            universal_witness_overlap_for_any_nonempty_allowed_candidate=1.0,
            witness_sha256=proof["witness_sha256"], rho_limit=0.90, forward_overlap_limit=0.70,
            allowed_cells=proof["allowed_pixels"], uncovered_allowed_cells=proof["uncovered_allowed_pixels"],
            registry_files_byte_verified=inputs["byte_verified_rasters"],
            registry_grid_incompatible_or_invalid=inputs["grid_incompatible_or_invalid_rasters"],
            scope=f"Witness rejects any nonempty allowed candidate; {inputs['byte_verified_rasters']}-file byte/grid audit is not candidate clearance. Candidate surface and final dots do not exist."),
        raster_sha256=None,
        validator_output=dict(status="NOT_RUN_NO_NEW_RASTER", new_raster_no_nan_inside_footprint=None,
            new_raster_values_in_0_1=None, new_raster_crs_shape_transform_match=None,
            inherited_artifact_format_passes=report["locally_valid_artifacts"],
            inherited_artifact_count=report["artifact_count"],
            inherited_artifact_decision="DO NOT SUBMIT", organizer_acceptance_confirmed=False),
        submission_name=None,
        note="H86G-CSPA not run: literal registry stop; no new raster; zero slots. DO NOT SUBMIT.",
        unique_tiff_requirement_satisfied=False, new_candidate_generated=False,
        submission_ready=False, safe_to_submit=False, approved_for_weekly_slot=False,
        experiments_run=0, submission_slots_used=0, verdict="negative", decision="DO NOT SUBMIT",
        evidence_sha256={rel: sha256(root / rel) for rel in paths},
        limitations=["No single-method lane assigned.", "Actual shared template cached stack not obtained; native bands are not a substitute.",
                     "Two incompatible registry grids remain blockers; no row was excluded or warped.",
                     "No new HOLDOUT-DTI, canary, candidate rho, raster or organizer receipt exists for H86G."],
    )


def main() -> int:
    card = build_card()
    write_json(ROOT / "docs/evidence/session-cf73474c-run-card.json", card)
    print(card["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
