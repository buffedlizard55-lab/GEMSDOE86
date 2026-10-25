"""The published site must expose real downloads and fail closed on slot authorization."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_download_links_and_fail_closed_decision():
    html = (DOCS / "index.html").read_text()
    parallel = json.loads((ROOT / "evidence/run_card.json").read_text())
    rmrb = json.loads((DOCS / "evidence/rmrb86-run-card.json").read_text())
    for name in (parallel["raster_name"], Path(rmrb["download_file"]).name):
        assert name in html
        assert (DOCS / "downloads" / name).is_file()
    assert "DO NOT SUBMIT" in html
    # Current literal full-support witness stop applies to every nonempty file.
    # The old H86G lane verdict remains archival and must not authorize upload.
    assert "NO FILE CLEARED FOR SUBMISSION" in html
    assert "DO NOT SUBMIT" in html
    assert "H86G-EDTI artifact retains its historical like-for-like lane verdict" in html
    assert "Download one-TIFF ZIP — audit only, DO NOT SUBMIT" in html
    assert "submit this file" not in html.lower()
    readiness = json.loads((DOCS / "evidence/release-readiness.json").read_text())
    assert readiness["decision"] == "DO NOT SUBMIT"
    assert readiness["submission_ready"] is False
    assert readiness["safe_to_submit"] is False
    assert all(a["status"].startswith("DO NOT SUBMIT") for a in readiness["artifacts"])
    assert all(a["safe_to_submit"] is False for a in readiness["artifacts"])
    h86g = next(a for a in readiness["artifacts"] if a.get("source_card") == "docs/evidence/h86g-edti-run-card.json")
    assert h86g["historical_lane_verdict"] == "promote"
    assert h86g["literal_registry_stop"] is True
    assert rmrb["safe_to_download"] is True
    assert rmrb["safe_to_submit"] is False


def test_h33_claim_and_holdout_scores_show_evidence_class_and_context():
    html = (DOCS / "index.html").read_text()
    # Fleet-page scores are owner claims, not organizer-confirmed results.
    assert "0.2778</code> OWNER-REPORTED; not organizer-confirmed" in html
    assert "0.3195</code> and <code>0.4413</code> current-leaderboard values are OWNER-REPORTED and unverified" in html
    # Every visible holdout score includes its evaluator, withheld-positive count,
    # and interval; the paired delta is explicitly labeled as holdout evidence.
    assert "<strong>HOLDOUT-DTI</strong> (<code>gems57-pooled-hide-v2</code>, <code>22,893</code> withheld positives)" in html
    assert "<code>H86D-CTHB</code> = <code>0.1133</code>, 95% CI <code>[0.0965, 0.1297]</code>" in html
    assert "<code>H33-2-B2</code> fold-fair control = <code>0.1056</code>, 95% CI <code>[0.0936, 0.1166]</code>" in html
    assert "paired HOLDOUT-DTI delta = <code>+0.0076</code>, 95% CI <code>[-0.0101, +0.0241]</code>" in html
    assert "Do not infer a leaderboard projection from holdout results." in html


def test_zip_contains_single_tiff():
    import zipfile
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    archive = DOCS / "downloads" / (card["raster_name"][:-4] + ".zip")
    assert archive.is_file()
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        assert names == [card["raster_name"]]
        assert bundle.getinfo(names[0]).file_size > 100_000
