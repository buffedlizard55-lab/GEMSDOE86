"""Fresh audit receipts must not silently reuse a historical session date."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import shutil

import pytest

from scripts import audit_release, build_site

ROOT = Path(__file__).resolve().parents[1]


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
