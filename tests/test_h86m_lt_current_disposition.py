"""H86M-LT's historical promotion must not become current upload approval."""
import json
from pathlib import Path

from scripts import audit_release

ROOT = Path(__file__).resolve().parents[1]
STEM = "gems86-h86m-lt-tomography-37654dots-20261025T174610Z-7b4ebdf5-zeros"


def test_h86m_lt_inventory_and_current_disposition_are_fail_closed():
    inventory = json.loads((ROOT / "docs/evidence/download-inventory.json").read_text())
    entry = next(item for item in inventory["artifacts"] if item["file"].endswith(f"{STEM}.tif"))
    assert entry["status"].startswith("DO NOT SUBMIT")
    assert entry["approved_for_weekly_slot"] is False

    disposition = json.loads((ROOT / "docs/evidence/h86m-lt-current-disposition.json").read_text())
    assert disposition["historical_lane_verdict"] == "promote"
    assert disposition["verdict"] == "negative"
    assert disposition["holdout_dti"] is None
    assert disposition["safe_to_submit"] is False
    assert disposition["approved_for_weekly_slot"] is False
    assert disposition["submission_slots_used"] == 0

    historical = json.loads((ROOT / "docs/evidence/h86m-lt-run-card.json").read_text())
    assert historical["verdict"] == "promote"  # preserve scientific history
    assert historical["safe_to_submit"] is False


def test_live_release_report_rejects_h86m_lt_despite_valid_format():
    report = audit_release.build_report()
    artifact = next(item for item in report["artifacts"] if item["file"].endswith(f"{STEM}.tif"))
    disposition = json.loads((ROOT / "docs/evidence/h86m-lt-current-disposition.json").read_text())
    assert disposition["historical_lane_verdict"] == "promote"
    assert artifact["verdict"] == "negative"
    assert artifact["safe_to_download_for_audit"] is True
    assert artifact["safe_to_submit"] is False
    assert artifact["historical_holdout"]["evidence_class"] == "NO-HOLDOUT-DTI"
    assert artifact["historical_holdout"]["value"] is None
    assert artifact["registry_measurement"]["forward_overlap_3px"] == 1.0
    assert report["decision"] == "DO NOT SUBMIT"


def test_archived_holdout_does_not_turn_tomography_projection_into_score():
    config = {
        "holdout_kind": "h86m_lt_unvalidated",
        "context": "docs/evidence/h86m-lt-current-disposition.json",
    }
    context = json.loads((ROOT / config["context"]).read_text())
    result = audit_release.archived_holdout(config, context)
    assert result["evidence_class"] == "NO-HOLDOUT-DTI"
    assert result["status"] == "NOT_VALIDATED_FOR_THIS_VARIANT"
    assert result["value"] is None
    assert result["ci95"] is None
    assert result["withheld_positives"] is None


def test_h86m_lt_page_never_calls_historical_artifact_upload_ready():
    page = (ROOT / "docs/h86m-lt.html").read_text().lower()
    assert "do not submit" in page
    assert "audit only" in page
    assert "ok to submit? yes" not in page
    assert "download the submission file" not in page
