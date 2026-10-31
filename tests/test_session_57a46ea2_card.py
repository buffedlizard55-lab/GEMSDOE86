"""The 2026-10-30 review card must preserve a fail-closed no-candidate result."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "docs/evidence/session-57a46ea2-run-card.json"


def test_current_review_card_is_negative_and_has_no_submission_claim():
    card = json.loads(CARD.read_text())
    assert card["session"] == "arena/57a46ea2-gemsdoe86"
    assert card["verdict"] == "negative"
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["experiments_run"] == 0
    assert card["submission_slots_used"] == 0
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None
    assert card["holdout_dti"]["status"] == "NOT_RUN"
    assert card["holdout_dti"]["evaluator_version"] == "gems57-pooled-hide-v2"
    assert card["holdout_dti"]["withheld_positives"] is None
    assert card["holdout_dti"]["value"] is None
    assert card["holdout_dti"]["ci95"] is None
    assert card["validator_output"]["status"] == "NOT_RUN_NO_CANDIDATE"


def test_current_card_binds_the_fresh_registry_measurement_and_input_receipt():
    card = json.loads(CARD.read_text())
    expected = {
        "protocol_preflight_sha256": "docs/evidence/protocol-preflight-20261030.json",
        "current_input_audit_sha256": "docs/evidence/session-57a46ea2-inputs-20261030.json",
        "all_artifacts_registry_sha256": "docs/evidence/session-57a46ea2-archive/all-artifacts-registry.json",
    }
    for field, relative in expected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == card[field]

    proof = json.loads((ROOT / "docs/evidence/protocol-preflight-20261030.json").read_text())
    assert proof["status"] == "STOP_LITERAL_OVERLAP_UNSATISFIABLE"
    assert proof["allowed_pixels"] == 5_106_385
    assert proof["direct_support_uncovered_allowed_pixels"] == 0
    assert proof["thresholds_unchanged"] is True
    assert card["pinned_witness_measurement"]["registry_complete"] is False
    assert card["pinned_witness_measurement"]["registry_rasters_measured"] == 1


def test_focus9_score_claims_are_not_promoted_to_verified_scores():
    card = json.loads(CARD.read_text())
    claims = card["score_claims"]
    assert "OWNER-REPORTED / UNVERIFIED" in claims["gemsdoe32_h33_0_2778"]
    assert "not verified" in claims["leaderboard_0_3195_and_0_4413"]
    assert claims["new_candidate_score_estimate"].startswith("NOT ESTIMABLE")
    assert card["software_review"]["pytest_summary"].startswith("1206 passed")
