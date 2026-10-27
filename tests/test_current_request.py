"""Preserve the request while keeping its unverified scores out of measured evidence."""
import csv
import hashlib
from pathlib import Path
import re

from scripts.audit_release import strict_json

ROOT = Path(__file__).resolve().parents[1]


def test_full_current_request_is_embedded_without_changing_earlier_archive():
    readme = (ROOT / "README.md").read_text()
    current26_rev2 = readme.split("<!-- CURRENT_REQUEST_20261026_REV2_START -->", 1)[1].split("<!-- CURRENT_REQUEST_20261026_REV2_END -->", 1)[0]
    assert current26_rev2.strip() == (ROOT / "research/REQUEST_20261026_REV2.md").read_text().strip()
    current26 = readme.split("<!-- CURRENT_REQUEST_20261026_START -->", 1)[1].split("<!-- CURRENT_REQUEST_20261026_END -->", 1)[0]
    assert current26.strip() == (ROOT / "research/REQUEST_20261026.md").read_text().strip()
    current25_rev2 = readme.split("<!-- CURRENT_REQUEST_20261025_REV2_START -->", 1)[1].split("<!-- CURRENT_REQUEST_20261025_REV2_END -->", 1)[0]
    assert current25_rev2.strip() == (ROOT / "research/REQUEST_20261025_REV2.md").read_text().strip()
    current25 = readme.split("<!-- CURRENT_REQUEST_20261025_START -->", 1)[1].split("<!-- CURRENT_REQUEST_20261025_END -->", 1)[0]
    assert current25.strip() == (ROOT / "research/REQUEST_20261025.md").read_text().strip()
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
    assert sum(1 for r in ledger if r["score"]) == 124  # 119 + 5 (2026-10-26 rev2 Focus-9 owner claims), never a retroactive archive edit
    assert all((name, value) in registered for name, value in scored)
    assert all(r["evidence_class"].startswith("OWNER-REPORTED") for r in ledger if r["score"])
    assert set(unscored_named) == {
        "gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros",
        "gems90-cnc-35000dots-20261024T084324Z",
    }
    # They were unscored in this immutable archive; subsequent 2026-10-25/26 requests
    # supplied owner-reported numbers for 89/90, 91/92, and the 5 Focus-9 2026-10-25 runs.
    updated = {"gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros": "0.0301",
               "gems90-cnc-35000dots-20261024T084324Z": "0.0749"}
    rev2_updated = {
        "gems91-s17-cwpc-20261025T052212Z-bf21d9a4bd-zeros": "0.1367",
        "gems91-s17-lftg-20261025T160014Z-7b6bf90844-zeros": "0.1823",
        "gemsdoe92-listricdip-updip50-37654-20261025T190000Z-zeros": "0.0255",
    }
    req26_updated = {
        "gems91-s17-cwpc-e3-37654dots-20261025T150000Z-4d124f1d-zeros": "0.1367",
    }
    req26_rev2_focus9 = {
        "gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-zeros": "0.0859",
        "h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros": "0.0742",
        "h29-hydrothermal-piedmont-celf-20261025-511898747886-allfinite": "0.2190",
        "s18-mxtp-20261025-3e95505c011a-allfinite": "0.0217",
        "MSDB1-edge44090-20261025-e7856ec3f14a": "0.1462",
    }
    for row in ledger:
        if row["submission"] in unscored_named:
            assert row["score"] == updated[row["submission"]]
            assert row["evidence_class"].startswith("OWNER-REPORTED (2026-10-25 request")
        if row["submission"] in rev2_updated:
            assert row["score"] == rev2_updated[row["submission"]]
            assert row["evidence_class"].startswith("OWNER-REPORTED (2026-10-25 rev2 request")
        if row["submission"] in req26_updated:
            assert row["score"] == req26_updated[row["submission"]]
            assert row["evidence_class"].startswith("OWNER-REPORTED (2026-10-26 request")
        if row["submission"] in req26_rev2_focus9:
            assert row["score"] == req26_rev2_focus9[row["submission"]]
            assert row["evidence_class"].startswith("OWNER-REPORTED (2026-10-26 rev2 Focus-9 request")
    req26_rev2_text = (ROOT / "research/REQUEST_20261026_REV2.md").read_text()
    req26_rev2_scores = re.findall(r"^([^\n:]+):[ \t]*(0\.\d+)[ \t]*$", req26_rev2_text, re.M)
    assert all((name, value) in registered for name, value in req26_rev2_scores)
    with (ROOT / "ledger/submissions.csv").open(newline="") as stream:
        canonical_ledger = list(csv.DictReader(stream))
    canonical_by_name = {r["name"]: r for r in canonical_ledger}
    for name in unscored_named:
        assert name in canonical_by_name
        assert canonical_by_name[name]["score"] == updated[name]
        assert canonical_by_name[name]["evidence_class"] == "CLAIM"


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


def test_focus9_summary_corrects_gemsdoe28_best_and_marks_historical_rows_not_submit_ready():
    page = (ROOT / "docs/executive-summary.html").read_text()
    assert "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif" in page
    assert "<strong>0.2710</strong>" in page
    assert "Best scored GEMSDOE28 row; H27-4 is 0.2708" in page
    assert "Unique vs Focus-9 / H33?" in page
    assert "measured 3-px overlap with H33" in page
    assert "Not estimable: no new eligible raster" in page
    assert "NO FILE IS CLEARED TO DOWNLOAD AND SUBMIT" in page
    assert "OWNER-REPORTED" in page


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


def test_earlier_full_request_bytes_are_frozen_and_current_scores_remain_claims():
    for name, digest in {
        "REQUEST_20261024.md": "0a232bf7981e146813478d591fc554d59323fb5631b101f529546f8bdffb031e",
        "REQUEST_20261023.md": "f97442adbbdf3efb16a515445f9ec6a28283188053d95a63b443e5b34afa97db",
        "OWNER_PROMPT.md": "70c0e08c6d465b4d56654066d9f5e3dc1fdcdec971dd5b81d29fb94b14a7e3c0",
    }.items():
        assert hashlib.sha256((ROOT / "research" / name).read_bytes()).hexdigest() == digest
    current = (ROOT / "research/REQUEST_20261025.md").read_text()
    scores = re.findall(r"^([^\n:]+):[ \t]*(0\.\d+)[ \t]*$", current, re.M)
    assert len(scores) == 117  # duplicate H33 mentions are retained as supplied
    with (ROOT / "registry/prior_scores.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert all((name, value) in {(r["submission"], r["score"]) for r in rows} for name, value in scores)
    assert "REQUEST_20261025.md" in (ROOT / "PROMPT.md").read_text()
