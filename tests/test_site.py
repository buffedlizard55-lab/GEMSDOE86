"""The published site must expose the current fail-closed decision accurately."""
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_current_download_page_is_prominent_and_fail_closed():
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    h86b = json.loads((DOCS / "evidence/h86b-gfco-run-card.json").read_text())
    rmrb = json.loads((DOCS / "evidence/rmrb86-run-card.json").read_text())
    assert Path(h86b["submission_file"]).name in html
    assert h86b["submission_name"] in html
    assert h86b["raster_sha256"] in html
    assert "DO NOT SUBMIT" in html
    assert "NO CANDIDATE IS AUTHORIZED" in html
    assert "SAFE TO DOWNLOAD FOR AUDIT" in html
    assert "download-status.html" in html
    assert "OK TO DOWNLOAD AND SUBMIT" not in html
    assert h86b["verdict"] == "negative"
    assert h86b["submission_ready"] is False
    assert h86b["approved_for_weekly_slot"] is False
    assert rmrb["safe_to_download"] is True
    assert rmrb["safe_to_submit"] is False


def test_current_zip_contains_exactly_one_h86b_tiff():
    card = json.loads((DOCS / "evidence/h86b-gfco-run-card.json").read_text())
    tiff_path = ROOT / card["submission_file"]
    zip_path = ROOT / card["zip_file"]
    assert tiff_path.is_file() and zip_path.is_file()
    with zipfile.ZipFile(zip_path) as bundle:
        assert bundle.namelist() == [tiff_path.name]
        assert bundle.read(tiff_path.name) == tiff_path.read_bytes()


def test_generated_summary_marks_owner_score_absent_and_experiment_not_run():
    summary = json.loads((DOCS / "data/summary.json").read_text())
    assert summary["decision"] == "DO NOT SUBMIT"
    assert summary["organizer_confirmed_score"] is None
    assert summary["organizer_receipt_present"] is False
    assert summary["current_review"]["new_experiments_run"] == 0
    assert summary["current_review"]["new_candidate_generated"] is False
    assert summary["latest_evaluated_lane"]["validator"]["checks_passed"] == 15
    assert summary["latest_evaluated_lane"]["validator"]["checks_total"] == 15
    assert len(summary["artifacts"]) == 6
