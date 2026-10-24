"""Preserve the request while keeping its unverified scores out of measured evidence."""
import csv
from pathlib import Path
import re

from scripts.audit_release import strict_json

ROOT = Path(__file__).resolve().parents[1]


def test_full_current_request_is_embedded_without_changing_earlier_archive():
    readme = (ROOT / "README.md").read_text()
    current24 = readme.split("<!-- CURRENT_REQUEST_20261024_START -->", 1)[1].split("<!-- CURRENT_REQUEST_20261024_END -->", 1)[0]
    current23 = readme.split("<!-- CURRENT_REQUEST_20261023_START -->", 1)[1].split("<!-- CURRENT_REQUEST_20261023_END -->", 1)[0]
    earlier = readme.split("<!-- OWNER_PROMPT_ARCHIVE_START -->", 1)[1].split("<!-- OWNER_PROMPT_ARCHIVE_END -->", 1)[0]
    assert current24.strip() == (ROOT / "research/REQUEST_20261024.md").read_text().strip()
    assert current23.strip() == (ROOT / "research/REQUEST_20261023.md").read_text().strip()
    assert earlier.strip() == (ROOT / "research/OWNER_PROMPT.md").read_text().strip()


def test_every_named_current_project_and_reported_submission_is_traceable():
    prompt = (ROOT / "research/REQUEST_20261024.md").read_text()
    prompt_urls = set(re.findall(r"https://buffedlizard55-lab\.github\.io/[^\s]+", prompt))
    named = set(re.findall(r"https://buffedlizard55-lab\.github\.io/([^/\s]+)/", prompt))
    targets = strict_json(ROOT / "registry/site_targets.json")["sites"]
    assert len(targets) == 92
    assert named == {t["repository"].split("/")[-1] for t in targets}
    assert prompt_urls == {t["site_url"] for t in targets}
    with (ROOT / "registry/prior_scores.csv").open(newline="") as stream:
        ledger = list(csv.DictReader(stream))
    assert prompt_urls == {r["source_url"] for r in ledger}
    scored = re.findall(r"^([^\n:]+):[ \t]*(0\.\d+)[ \t]*$", prompt, re.M)
    unscored_named = re.findall(r"^([A-Za-z0-9._-]+):[ \t]*$", prompt, re.M)
    registered = {(r["submission"], r["score"]) for r in ledger}
    assert len(scored) == 115
    assert sum(1 for r in ledger if r["score"]) == 113
    assert all((name, value) in registered for name, value in scored)
    assert all(r["evidence_class"].startswith("OWNER-REPORTED") for r in ledger if r["score"])
    assert set(unscored_named) == {
        "gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros",
        "gems90-cnc-35000dots-20261024T084324Z",
    }
    assert all((name, "") in registered for name in unscored_named)
    for row in ledger:
        if row["submission"] in unscored_named:
            assert row["score"] == ""
            assert row["evidence_class"].startswith("PROMPT-NAMED UNSCORED")
    with (ROOT / "ledger/submissions.csv").open(newline="") as stream:
        canonical_ledger = list(csv.DictReader(stream))
    canonical_by_name = {r["name"]: r for r in canonical_ledger}
    for name in unscored_named:
        assert name in canonical_by_name
        assert canonical_by_name[name]["score"] == ""
        assert canonical_by_name[name]["evidence_class"] == "NO-EVIDENCE"


def test_default_pipeline_audits_all_artifacts_without_selecting_latest_or_training():
    makefile = (ROOT / "Makefile").read_text()
    assert "all: data audit site verify" in makefile
    assert "ls -t" not in makefile
    workflow = (ROOT / ".github/workflows/pages.yml").read_text()
    assert "schedule:" in workflow
    assert "audit_release.py --measure-registry" in workflow
    assert "refresh_fleet.py" in workflow
    assert "run_lane" not in workflow
    assert "build_submission.py" not in workflow


def test_current_review_and_readme_deliverable_links_exist():
    readme = (ROOT / "README.md").read_text().split("<!-- CURRENT_REQUEST_20261024_START -->", 1)[0]
    for relative in re.findall(r"\]\(([^():#\s]+)(?:#[^)]*)?\)", readme):
        assert (ROOT / relative).is_file(), relative
    review23 = (ROOT / "research/SESSION_20261023_REVIEW.md").read_text()
    assert "highest-priority new-TIFF requirement is unmet" in review23
    assert "Pass 1" in review23 and "Pass 2" in review23 and "Pass 3" in review23
    review24 = (ROOT / "research/SESSION_20261024_REVIEW.md").read_text()
    assert "No new unique competition GeoTIFF is cleared" in review24
    assert "Pass 1" in review24 and "Pass 2" in review24 and "Pass 3" in review24


def test_current_session_card_is_complete_negative_and_not_presented_as_a_download():
    card = strict_json(ROOT / "docs/evidence/session-20261024-run-card.json")
    hypotheses = strict_json(ROOT / "registry/h86c_hypotheses.json")["hypotheses"]
    assert card["hypothesis"].startswith(f"{hypotheses[0]['id']}: ")
    assert "H86C-MMT" not in card["hypothesis"]
    assert card["verdict"] == "negative"
    assert card["holdout_dti"]["evidence_class"] == "HOLDOUT-DTI"
    assert card["holdout_dti"]["status"] == "NOT_RUN_PROTOCOL_STOP"
    assert card["holdout_dti"]["value"] is None and card["holdout_dti"]["ci95"] is None
    assert card["correlation_overlap_vs_registry"]["evidence_class"] == "REGISTRY-MEASUREMENT"
    assert card["raster_sha256"] is None and card["submission_name"] is None
    assert card["validator_output"]["status"] == "NOT_RUN_NO_NEW_RASTER"
    assert len(card["note"]) <= 140
    assert not card["new_candidate_generated"] and not card["submission_ready"]
    assert card["experiments_run"] == card["submission_slots_used"] == 0
    for relative in ("research/SESSION_20261024_REVIEW.md", "docs/evidence/release-readiness.json",
                     "docs/evidence/all-artifacts-registry.json", "docs/evidence/fleet-feed.json"):
        assert (ROOT / relative).is_file()
