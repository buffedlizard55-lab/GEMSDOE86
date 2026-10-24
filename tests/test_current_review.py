"""Fresh audit receipts must not silently reuse a historical session date."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import shutil

import pytest

from scripts import audit_release, build_site

ROOT = Path(__file__).resolve().parents[1]


def spt_site_fixture(tmp_path, monkeypatch):
    """Isolate incoming SPT-page safety checks without disabling the audit."""
    from scripts import audit_legacy_spt
    for rel in (
        "docs/evidence/release-readiness.json", "docs/evidence/all-artifacts-registry.json",
        "docs/evidence/latest-review-run-card.json", "docs/evidence/fleet-feed.json",
        "docs/evidence/spt-full-support-witness-audit.json", "docs/evidence/spt-run-card.json",
        "docs/evidence/spt-legacy-audit.json", "docs/evidence/protocol-preflight.json",
        "research/upstream/spt-original-run-card.json", "research/registry_witness_pin.json",
        "registry/prior_scores.csv", "registry/site_targets.json",
        "data/bridge/sample_submission.tif", "data/bridge/existing_faults.tif",
        "submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.tif",
        "submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.zip",
        "submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.json",
    ):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    monkeypatch.setattr(audit_legacy_spt, "verify_shared_pins", lambda _: {"pinned": True})
    report = audit_release.strict_json(tmp_path / "docs/evidence/release-readiness.json")
    monkeypatch.setattr(build_site, "build_report", lambda _: deepcopy(report))
    return tmp_path


def test_current_review_binds_actual_measurement_without_relabeling_old_results():
    report = audit_release.strict_json(ROOT / "docs/evidence/release-readiness.json")
    registry = audit_release.strict_json(ROOT / "docs/evidence/all-artifacts-registry.json")
    card = audit_release.current_review_card(report, registry)
    archived = audit_release.session_card(report)
    assert card["date_utc"] == datetime.fromisoformat(registry["measured_utc"]).date().isoformat()
    assert archived["date_utc"] == "2026-10-23"
    assert card["registry_measured_utc"] == registry["measured_utc"]
    assert card["raster_sha256"] is card["submission_name"] is None
    assert card["holdout_dti"]["status"] == "NOT_RUN_PROTOCOL_STOP"
    assert card["holdout_dti"]["value"] is card["holdout_dti"]["ci95"] is None
    assert card["new_candidate_generated"] is card["submission_ready"] is False
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    assert card["verdict"] == "negative"
    assert len(card["note"]) <= 140
    assert card["release_report_sha256"] == audit_release.sha256(ROOT / "docs/evidence/release-readiness.json")


@pytest.mark.parametrize("timestamp", ["2026-10-24T10:00:00", "2026-10-24T10:00:00+02:00", "not-a-date"])
def test_measurement_timestamp_requires_explicit_utc(timestamp):
    report = audit_release.strict_json(ROOT / "docs/evidence/release-readiness.json")
    registry = {"measured_utc": timestamp}
    with pytest.raises(ValueError):
        audit_release.current_review_card(report, registry)


@pytest.mark.parametrize("change", [
    {"release_report_sha256": "stale"},
    {"registry_measurement_sha256": "stale"},
    {"registry_measured_utc": "2000-01-01T00:00:00+00:00"},
    {"verdict": "promote"},
    {"submission_ready": True},
    {"new_candidate_generated": True},
])
def test_site_rejects_stale_or_optimistic_current_review(tmp_path, monkeypatch, change):
    for rel in (
        "docs/evidence/release-readiness.json", "docs/evidence/all-artifacts-registry.json",
        "docs/evidence/latest-review-run-card.json", "docs/evidence/fleet-feed.json",
        "docs/evidence/spt-full-support-witness-audit.json", "docs/evidence/spt-run-card.json",
        "submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.tif",
        "submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.json",
        "registry/prior_scores.csv", "registry/site_targets.json",
    ):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    report = audit_release.strict_json(tmp_path / "docs/evidence/release-readiness.json")
    monkeypatch.setattr(build_site, "build_report", lambda _: deepcopy(report))
    path = tmp_path / "docs/evidence/latest-review-run-card.json"
    card = audit_release.strict_json(path)
    card.update(change)
    path.write_text(json.dumps(card))
    with pytest.raises(ValueError, match="Current review is stale"):
        build_site.render(tmp_path)


def test_spt_candidate_with_full_witness_overlap_is_not_presented_as_downloadable():
    audit = audit_release.strict_json(ROOT / "docs/evidence/spt-full-support-witness-audit.json")
    card = audit_release.strict_json(ROOT / "docs/evidence/spt-run-card.json")
    page = (ROOT / "docs/submit.html").read_text()
    assert audit["candidate_dot_overlap_within_3px_of_witness"] == 1.0
    assert audit["candidate_dot_overlap_within_3px_of_witness"] > audit["literal_overlap_limit"]
    assert audit["verdict"] == "negative_duplicate_stop_do_not_submit"
    assert card["verdict"] == "negative" and card["submission_ready"] is False
    assert card["correlation_overlap_vs_registry"]["final_dots_forward_overlap_3px"] == audit["candidate_dot_overlap_within_3px_of_witness"]
    assert card["correlation_overlap_vs_registry"]["witness_sha256"] == audit["witness_sha256"]
    assert card.get("download_url") is None
    assert "raw.githubusercontent.com" not in json.dumps(card)
    assert "DO NOT SUBMIT" in page
    assert "READY TO DOWNLOAD" not in page
    assert "raw.githubusercontent.com" not in page
    assert "spt-full-support-witness-audit.json" in page


def test_site_rejects_spt_download_url(tmp_path, monkeypatch):
    spt_site_fixture(tmp_path, monkeypatch)
    path = tmp_path / "docs/evidence/spt-run-card.json"
    card = audit_release.strict_json(path)
    card["download_url"] = "https://example.invalid/candidate.tif"
    path.write_text(json.dumps(card))
    with pytest.raises(ValueError, match="Corrective run card|Historical SPT|SPT candidate is stale or violates"):
        build_site.render(tmp_path)


def test_site_rejects_optimistic_spt_witness_audit(tmp_path, monkeypatch):
    spt_site_fixture(tmp_path, monkeypatch)
    path = tmp_path / "docs/evidence/spt-full-support-witness-audit.json"
    audit = audit_release.strict_json(path)
    audit["candidate_dot_overlap_within_3px_of_witness"] = 0.2
    path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="SPT candidate is stale or violates"):
        build_site.render(tmp_path)
