"""Current branch review card must remain negative without inventing a score or candidate."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "docs/evidence/session-9b7ca9b8-run-card.json"


def test_current_review_card_is_explicitly_negative_and_has_no_submission_file():
    card = json.loads(CARD.read_text())
    assert card["session_branch"] == "arena/9b7ca9b8-gemsdoe86"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["new_candidate_generated"] is False
    assert card["unique_tiff_requirement_satisfied"] is False
    assert card["submission_status"] == "NO CANDIDATE TIFF — DO NOT SUBMIT"
    assert card["submission_name"] is None
    assert card["raster_sha256"] is None
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    assert card["score_estimate"] is None
    assert card["submission_note_character_count"] == len(card["submission_note"]) <= 140


def test_current_review_card_preserves_protocol_evidence_boundaries():
    card = json.loads(CARD.read_text())
    holdout = card["holdout_dti"]
    assert holdout["evidence_class"] == "HOLDOUT-DTI"
    assert holdout["status"].startswith("NOT_RUN")
    assert holdout["evaluator_version"] is None
    assert holdout["withheld_positives"] is None
    assert holdout["value"] is None and holdout["ci95"] is None
    assert card["leakage_canary"]["status"] == "NOT_RUN_NO_FEATURES"
    overlap = card["correlation_overlap_vs_registry"]
    assert overlap["evidence_class"] == "REGISTRY-MEASUREMENT"
    assert overlap["candidate_surface_spearman"] is None
    assert overlap["candidate_final_dot_overlap_3px"] is None
    assert overlap["uncovered_allowed_pixels"] == 0
    assert overlap["implied_forward_overlap_for_any_nonempty_allowed_candidate"] == 1.0
    assert overlap["registry_complete"] is False
    assert card["validator_output"]["status"] == "NOT_RUN_NO_NEW_RASTER"


def test_owner_claim_and_feed_are_not_promoted_to_verified_scores():
    card = json.loads(CARD.read_text())
    claim = card["focus9_historical_claim"]
    assert claim["site"] == "GEMSDOE32" and claim["value"] == 0.2778
    assert claim["evidence_class"] == "OWNER-REPORTED / UNVERIFIED"
    assert claim["organizer_confirmed"] is False
    assert claim["receipt_binds_score_to_exact_tiff"] is False
    feed = card["feed"]
    assert feed["evidence_class"] == "REPOSITORY-METADATA"
    assert feed["repositories_requested"] == feed["repositories_snapshotted"] == 92
    assert feed["organizer_receipts"] == 0
    assert feed["new_path_scores"] == "UNKNOWN_NOT_INFERRED_FROM_GIT_METADATA"
