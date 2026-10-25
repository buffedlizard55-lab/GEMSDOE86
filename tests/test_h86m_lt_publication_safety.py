import json
from pathlib import Path

from scripts import audit_release

ROOT = Path(__file__).resolve().parents[1]
STEM = "gems86-h86m-lt-tomography-37654dots-20261025T174610Z-7b4ebdf5-zeros"


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_h86m_lt_is_registered_audit_only_and_stopped_by_literal_witness():
    card = load("docs/evidence/h86m-lt-run-card.json")
    inventory = load("docs/evidence/download-inventory.json")
    cards = load("registry/artifact_cards.json")
    release = load("docs/evidence/release-readiness.json")
    entry = next(item for item in inventory["artifacts"] if item["file"].endswith(STEM + ".tif"))
    mapping = next(item for item in cards["artifacts"] if item["stem"] == STEM)

    assert entry["status"] == "DO NOT SUBMIT"
    assert entry["approved_for_weekly_slot"] is False
    assert mapping["holdout_kind"] == "h86m_lt_unvalidated"
    assert card["historical_lane_verdict"].startswith("promote under the lane-local")
    assert card["verdict"] == "negative"
    assert card["safe_to_submit"] is card["submission_ready"] is False
    assert card["approved_for_weekly_slot"] is False
    holdout = card["holdout_dti"]
    assert holdout["evidence_class"] == "HOLDOUT-DTI"
    assert holdout["status"] == "NOT_RUN_NO_ASSIGNED_HOLDOUT_LANE_AND_SHARED_CACHE_ABSENT"
    assert holdout["value"] is holdout["ci95"] is holdout["withheld_positives"] is None
    literal = card["correlation_overlap_vs_registry"]["current_literal_witness"]
    assert literal["status"] == "FAIL_LITERAL_STOP"
    assert literal["candidate_forward_overlap"] == 1.0 > literal["overlap_limit"] == 0.70
    artifact = next(item for item in release["artifacts"] if item["file"].endswith(STEM + ".tif"))
    assert artifact["safe_to_submit"] is False
    assert artifact["status"].startswith("DO NOT SUBMIT")
    assert artifact["registry_measurement"]["forward_overlap_3px"] == 1.0


def test_h86m_lt_publication_surfaces_do_not_recommend_upload():
    page = (ROOT / "docs/h86m-lt.html").read_text(encoding="utf-8").lower()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    receipt = load(f"docs/downloads/{STEM}.json")
    assert "is this file ok to submit? no" in page
    assert "no upload is authorized" in page
    assert "is this file ok to submit? yes" not in page
    assert "do not submit — audit download only" in readme.lower()
    assert "1.0 forward overlap" in readme
    assert receipt["safe_to_submit"] is False
    assert receipt["metadata"]["verdict"] == "negative"


def test_h86m_lt_unvalidated_holdout_is_normalized_as_no_score():
    cards = load("registry/artifact_cards.json")["artifacts"]
    config = next(item for item in cards if item["stem"] == STEM)
    card = load("docs/evidence/h86m-lt-run-card.json")
    result = audit_release.archived_holdout(config, card)
    assert result["status"] == "NOT_VALIDATED_NO_HOLDOUT_LITERAL_DUPLICATE_STOP"
    assert result["value"] is result["ci95"] is result["withheld_positives"] is None
    assert "projections, not HOLDOUT-DTI" in result["caveat"]
