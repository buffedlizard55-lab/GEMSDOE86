"""The branch-specific Focus-9 review card must fail closed and preserve evidence classes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = ROOT / "research/run_cards/focus9_review_20261028_arena_27fef6bb.json"


def test_branch_review_card_is_unrun_and_bound_to_current_stop():
    card = json.loads(CARD_PATH.read_text())
    preflight = json.loads((ROOT / "docs/evidence/protocol-preflight.json").read_text())
    input_audit = json.loads((ROOT / "docs/evidence/registry-input-grid-review-20261028.json").read_text())

    assert card["session_branch"] == "arena/27fef6bb-gemsdoe86"
    assert card["lane_assignment"] is None
    assert card["hypothesis"] is None
    assert card["mechanism"] is None
    assert card["holdout_dti"]["status"] == "NOT_RUN_NO_LANE_ASSIGNED"
    assert card["holdout_dti"]["value"] is None
    assert card["holdout_dti"]["ci95"] is None
    assert card["raster_sha256"] is None
    assert card["candidate_raster"]["generated"] is False
    assert card["validator_output"]["no_nan_inside_footprint"] is None
    assert card["validator_output"]["values_in_0_1"] is None
    assert card["validator_output"]["crs_shape_transform_match"] is None
    assert card["submission"]["name"] is None
    assert card["submission"]["note"] is None
    assert card["submission"]["maximum_note_characters"] == 140
    assert card["submission"]["upload_authorized"] is False
    assert card["submission"]["weekly_slots_used"] == 0
    assert card["experiment_budget"]["experiments_used"] == 0
    assert card["verdict"] == "negative"
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False

    witness = card["correlation_overlap_vs_registry"]["pinned_witness"]
    assert witness["sha256"] == preflight["witness_sha256"]
    assert witness["allowed_pixels"] == preflight["allowed_pixels"]
    assert witness["uncovered_allowed_pixels"] == 0
    assert witness["literal_forward_overlap_lower_bound_for_any_nonempty_candidate"] == 1.0
    assert witness["unchanged_overlap_limit"] == 0.70
    assert card["correlation_overlap_vs_registry"]["candidate_comparisons"] == "NOT RUN — no candidate exists"
    assert card["correlation_overlap_vs_registry"]["registry_completeness"]["input_index_byte_verified"] == input_audit["byte_verified_rasters"]
    assert card["correlation_overlap_vs_registry"]["registry_completeness"]["input_index_complete"] is False

    assert len(card["ranked_unrun_hypotheses"]) == 3
    assert [h["rank"] for h in card["ranked_unrun_hypotheses"]] == [1, 2, 3]
    assert all(h["status"] == "PROPOSED_NOT_RUN" for h in card["ranked_unrun_hypotheses"])


def test_focus9_score_claim_is_not_relabelled_as_holdout_or_organizer_score():
    card = json.loads(CARD_PATH.read_text())
    score = card["focus9_best_score_evidence"]
    assert score["top_site"] == "GEMSDOE32"
    assert score["top_score"] == 0.2778
    assert score["evidence_class"] == "OWNER-REPORTED"
    assert score["organizer_confirmed"] is False
    assert card["holdout_dti"]["value"] is None
    assert card["submission"]["upload_authorized"] is False
