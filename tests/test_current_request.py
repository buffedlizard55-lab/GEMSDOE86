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
    named = set(re.findall(r"https://buffedlizard55-lab\.github\.io/([^/\s]+)/", prompt))
    targets = strict_json(ROOT / "registry/site_targets.json")["sites"]
    assert len(targets) == 92
    assert named == {t["repository"].split("/")[-1] for t in targets}
    with (ROOT / "registry/prior_scores.csv").open(newline="") as stream:
        ledger = list(csv.DictReader(stream))
    scored = re.findall(r"^([^\n:]+):[ \t]*(0\.\d+)[ \t]*$", prompt, re.M)
    registered = {(r["submission"], r["score"]) for r in ledger}
    assert len(scored) == 115
    assert sum(1 for r in ledger if r["score"]) == 113
    assert all((name, value) in registered for name, value in scored)
    assert all(r["evidence_class"].startswith("OWNER-REPORTED") for r in ledger if r["score"])


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
