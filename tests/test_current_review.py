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
    assert card["holdout_dti"]["status"] == "NOT_RUN_NO_LANE_ASSIGNED"
    assert card["holdout_dti"]["value"] is card["holdout_dti"]["ci95"] is None
    assert "No new lane was selected or run" in card["hypothesis"]
    assert card["correlation_overlap_vs_registry"]["evidence_class"] == "REGISTRY-MEASUREMENT"
    assert "not a candidate" in card["correlation_overlap_vs_registry"]["measurement_scope"]
    assert card["new_candidate_generated"] is card["submission_ready"] is False
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    assert card["verdict"] == "negative"
    assert len(card["note"]) <= 140
    assert card["release_report_sha256"] == audit_release.sha256(ROOT / "docs/evidence/release-readiness.json")


def test_branch_review_run_card_separates_unrun_candidate_from_prior_h86g():
    card = audit_release.strict_json(ROOT / "research/SESSION_20261025_ARENA_B5040_RUN_CARD.json")
    h86g = audit_release.strict_json(ROOT / "docs/evidence/h86g-edti-run-card.json")
    assert card["verdict"] == "negative"
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    assert card["raster_sha256"] is None and card["submission_name"] is None
    assert card["holdout_dti"]["status"] == "NOT_RUN"
    assert card["correlation_overlap_vs_registry"]["candidate_surface_max_spearman"] is None
    assert card["correlation_overlap_vs_registry"]["candidate_final_dot_max_forward_3px_overlap"] is None
    prior = card["previously_promoted_artifact_not_generated_by_this_review"]
    assert prior["raster_sha256"] == h86g["raster_sha256"]
    assert prior["submission_name"] == h86g["submission_name"]
    assert prior["holdout_dti"]["value"] == h86g["holdout_dti"]["candidate"]["dti"]
    assert prior["holdout_dti"]["ci95"] == h86g["holdout_dti"]["candidate"]["ci95"]
    assert prior["like_for_like_registry_measurement"]["gate_pass"] is True
    assert card["current_upload_authorized"] is False
    assert card["safe_to_submit"] is card["approved_for_weekly_slot"] is False
    assert prior["current_upload_decision"].startswith("DO NOT SUBMIT")


def test_current_readme_download_counts_match_fresh_release_inventory():
    report = audit_release.strict_json(ROOT / "docs/evidence/release-readiness.json")
    readme = (ROOT / "README.md").read_text()
    current = readme.split("<!-- CURRENT_REQUEST_20261024_START -->", 1)[0]
    count = report["artifact_count"]
    assert report["locally_valid_artifacts"] == count
    assert f"**{count}** published research TIFFs" in current
    assert "PR #92" in current and "DO NOT SUBMIT" in current
    assert "generated **no new candidate**" in current


def test_current_session_run_card_is_complete_negative_and_scope_labeled():
    card = audit_release.strict_json(ROOT / "docs/evidence/session-live-input-review-run-card.json")
    assert card["verdict"] == "negative"
    assert card["hypothesis"].startswith("No lane was assigned")
    assert card["holdout_dti"]["evidence_class"] == "HOLDOUT-DTI"
    assert card["holdout_dti"]["value"] is card["holdout_dti"]["ci95"] is None
    assert card["correlation_overlap_vs_registry"]["evidence_class"] == "REGISTRY-MEASUREMENT"
    assert card["correlation_overlap_vs_registry"]["universal_literal_forward_overlap_for_any_nonempty_allowed_candidate"] == 1.0
    assert card["live_inputs"]["evidence_class"] == "INPUT-INTEGRITY-MEASUREMENT"
    assert card["raster_sha256"] is card["submission_name"] is None
    assert card["validator_output"]["status"] == "NOT_RUN_NO_NEW_RASTER"
    assert card["safe_to_submit"] is card["approved_for_weekly_slot"] is False
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    assert len(card["note"]) <= 140


def test_site_exposes_live_input_audit_instead_of_trusting_old_preparation_receipt():
    report = audit_release.strict_json(ROOT / "docs/evidence/current-workspace-inputs.json")
    assert report["schema"] == "gems86.live-workspace-inputs.v1"
    assert report["native_inputs_available"] is False
    assert report["preparation"]["status"] == "STALE_OR_INCOMPLETE_RECEIPT"
    assert report["shared_cache"]["status"] == "SHARED_CACHE_NOT_ESTABLISHED"
    rendered = build_site.render(ROOT)
    for filename in ("docs/index.html", "docs/executive-summary.html"):
        html = rendered[filename]
        assert "LIVE INPUT-INTEGRITY-MEASUREMENT" in html
        assert "current-workspace-inputs.json" in html
        assert "NOT AVAILABLE" in html
        assert "0/21 paths currently hash-verified" in html
        assert "SHARED_CACHE_NOT_ESTABLISHED" in html
        assert "historical, not proof that files remain present" in html
        assert "all 19 native bands were restored and prepared" not in html


def test_historical_h86g_promotion_is_not_current_upload_authorization():
    rendered = build_site.render(ROOT)
    home = rendered["docs/index.html"]
    executive = rendered["docs/executive-summary.html"]
    evidence_page = rendered["docs/evidence.html"]

    # Preserve the historical scientific verdict while fail-closing every
    # upload surface under the current literal registry decision.
    for html in (home, executive):
        assert "DO NOT SUBMIT" in html
        assert "historical" in html.lower() and "PROMOTE" in html
        assert "safe_to_submit=false" in html or "does not authorize submission" in html
    h86g = home.split('id="h86g-edti"', 1)[1].split("</section>", 1)[0]
    assert "IS THIS FILE OK TO SUBMIT? NO — DO NOT SUBMIT" in h86g
    assert "PROMOTE under the amended like-for-like interpretation only" in h86g
    assert "safe_to_submit=false" in h86g and "approved_for_weekly_slot=false" in h86g

    format_page = (ROOT / "docs/download-status.html").read_text()
    format_card = json.loads((ROOT / "docs/evidence/session-review-run-card.json").read_text())
    assert "DO NOT SUBMIT any file" in format_page
    assert "historical PA-86-01 PROMOTE verdict" in format_page
    assert format_card["verdict"] == "negative" and format_card["safe_to_submit"] is False
    assert format_card["submission_slots_used"] == 0
    assert "current literal registry rule blocks upload" in format_card["scope"]
    assert "DO NOT SUBMIT" in evidence_page


def test_pr92_candidate_is_explicitly_negative_on_site_and_machine_summary():
    report = audit_release.build_report()
    page = build_site.render(ROOT)
    for name in ("docs/index.html", "docs/executive-summary.html", "docs/submit.html"):
        html = page[name]
        assert "PR #92 ARTIFACT · DO NOT SUBMIT" in html
        assert "SAFE FOR AUDIT DOWNLOAD" in html
        assert "HOLDOUT-DTI</strong> (gems57-pooled-hide-v2, 11,321 withheld positives)" in html
        assert "stop_required=true" in html
        assert "UNIQUE · FORMAT-VALID" not in html
    summary = json.loads(page["docs/data/summary.json"])
    candidate = summary["preexisting_pr92_artifact"]
    assert summary["featured_research_artifact"] is None
    assert summary["current_comparable_holdout_best"] is None
    assert candidate["status"] == "DO NOT SUBMIT"
    assert candidate["holdout_dti"]["evidence_class"] == "HOLDOUT-DTI"
    assert candidate["registry_measurement"]["unique"] is False
    assert candidate["registry_measurement"]["stop_required"] is True
    assert report["new_candidate_generated"] is False


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
        "docs/evidence/current-workspace-inputs.json",
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
    assert card["literal_registry_witness_audit"] == audit
    assert "download_url" not in card
    assert "raw.githubusercontent.com" not in json.dumps(card)
    assert "DO NOT SUBMIT" in page
    assert "READY TO DOWNLOAD" not in page
    assert "raw.githubusercontent.com" not in page
    assert "spt-full-support-witness-audit.json" in page


def test_site_rejects_spt_download_url(tmp_path, monkeypatch):
    for rel in (
        "docs/evidence/release-readiness.json", "docs/evidence/all-artifacts-registry.json",
        "docs/evidence/latest-review-run-card.json", "docs/evidence/fleet-feed.json",
        "docs/evidence/current-workspace-inputs.json",
        "docs/evidence/spt-full-support-witness-audit.json", "docs/evidence/spt-run-card.json",
        "registry/prior_scores.csv", "registry/site_targets.json",
        "submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.tif",
        "submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.json",
    ):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    report = audit_release.strict_json(tmp_path / "docs/evidence/release-readiness.json")
    monkeypatch.setattr(build_site, "build_report", lambda _: deepcopy(report))
    path = tmp_path / "docs/evidence/spt-run-card.json"
    card = audit_release.strict_json(path)
    card["download_url"] = "https://example.invalid/candidate.tif"
    path.write_text(json.dumps(card))
    with pytest.raises(ValueError, match="SPT candidate is stale or violates"):
        build_site.render(tmp_path)


def test_site_rejects_optimistic_spt_witness_audit(tmp_path, monkeypatch):
    for rel in (
        "docs/evidence/release-readiness.json", "docs/evidence/all-artifacts-registry.json",
        "docs/evidence/latest-review-run-card.json", "docs/evidence/fleet-feed.json",
        "docs/evidence/current-workspace-inputs.json",
        "docs/evidence/spt-full-support-witness-audit.json", "docs/evidence/spt-run-card.json",
        "registry/prior_scores.csv", "registry/site_targets.json",
        "submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.tif",
        "submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.json",
    ):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    report = audit_release.strict_json(tmp_path / "docs/evidence/release-readiness.json")
    monkeypatch.setattr(build_site, "build_report", lambda _: deepcopy(report))
    path = tmp_path / "docs/evidence/spt-full-support-witness-audit.json"
    audit = audit_release.strict_json(path)
    audit["candidate_dot_overlap_within_3px_of_witness"] = 0.2
    path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="SPT candidate is stale or violates"):
        build_site.render(tmp_path)


def test_prompt_named_unscored_audit_and_official_rules_citation_are_verified():
    audit = audit_release.strict_json(ROOT / "docs/evidence/prompt-named-unscored-audit-20261024.json")
    assert audit["schema"] == "gems86.prompt-named-unscored-audit.v1"
    assert audit["evidence_class"] == "REGISTRY-MEASUREMENT"
    assert audit["checker_pin"]["gems57_code_changed_since_pin"] is False
    by_site = {a["site"]: a for a in audit["artifacts"]}
    assert set(by_site) == {"GEMSDOE89", "GEMSDOE90"}
    assert by_site["GEMSDOE89"]["prompt_submission_name"] == "gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros"
    assert by_site["GEMSDOE90"]["prompt_submission_name"] == "gems90-cnc-35000dots-20261024T084324Z"
    for item in by_site.values():
        assert item["prompt_score"] is None
        assert item["organizer_confirmed_score"] is False
        assert item["format_all_checks_passed"] is True
        assert item["forward_overlap_3px_vs_17GEMSDOE"] == 1.0
        assert item["forward_overlap_3px_vs_13GEMSDOE_binary"] > 0.70
        assert item["unique_under_literal_protocol"] is False
        assert item["stop_required"] is True
    exec_html = (ROOT / "docs/executive-summary.html").read_text()
    assert "Official Rules §1.1 &amp; §3.4–3.6" in exec_html
    assert "Official Rules §5–6" not in exec_html


def test_swcon_candidate_is_revoked_and_not_downloadable():
    card = audit_release.strict_json(ROOT / "docs/evidence/swcon-run-card.json")
    assert card["verdict"] == "negative"
    assert card["submission_ready"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["download_authorized"] is False
    audit = card["measured_registry_witness_audit"]
    assert audit["unique"] is False and audit["stop_required"] is True
    assert audit["forward_overlap_3px_vs_17GEMSDOE"] == 1.0
    assert audit["forward_overlap_3px_vs_13GEMSDOE_binary"] > 0.70
    assert not (ROOT / "docs/swcon-submission.html").exists()
    assert not list((ROOT / "docs/downloads").glob("gems86-swcon-*"))
    assert not list((ROOT / "submission").glob("gems86-swcon-*"))
    submit_page = (ROOT / "docs/submit.html").read_text()
    assert "IR-86-SWCON-01" in submit_page
    assert "IR-86-FAULTHALO-01" in submit_page
    assert "DO NOT SUBMIT" in submit_page
    faulthalo = audit_release.strict_json(ROOT / "docs/evidence/h86-faulthalo-run-card.json")
    assert faulthalo["verdict"] == "negative"
    assert faulthalo["submission_ready"] is False
    assert faulthalo["ok_to_submit_under_current_protocol"] is False



