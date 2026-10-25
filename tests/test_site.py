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
    assert "CURRENT DECISION: DO NOT SUBMIT · NO FILE AUTHORIZED" in html
    assert "H86G-EDTI is a preserved historical lane, not a current clearance" in html
    assert "HISTORICAL TIFF — AUDIT DOWNLOAD ONLY" in html
    assert "Download TIFF — audit only · DO NOT SUBMIT" in html
    assert "ONE SELECTOR-READY FILE (H86G-EDTI)" not in html
    assert "IS THIS FILE OK TO SUBMIT? YES" not in html
    assert "submit this file" not in html.casefold()
    assert rmrb["safe_to_download"] is True
    assert rmrb["safe_to_submit"] is False


def test_h33_claim_and_holdout_scores_show_evidence_class_and_context():
    html = (DOCS / "index.html").read_text()
    # The claimed live value is explicitly unverified and the pixel lineage is
    # separated from any causal/leaderboard inference.
    assert "The supplied <code>0.2778</code>" in html
    assert "<strong>OWNER-REPORTED</strong>, not ORGANIZER-CONFIRMED" in html
    assert "removes exactly 2,545 dots" in html and "does not establish that causal balance" in html
    assert "<code>0.3195</code> and <code>0.4413</code>" in html
    assert "No result here establishes that any candidate beats 0.2778" in html
    # The visible historic H86G performance value retains its full evidence class,
    # evaluator, withheld-positive count, CI and non-organizer caveat.
    assert "HOLDOUT-DTI (historical card; not rerun here)" in html
    assert "gems57-pooled-hide-v2, 11,321 withheld positives" in html
    assert "0.0631, 95% CI [0.0468, 0.0806]" in html
    assert "This is not organizer-confirmed" in html
    assert "not a private-test or leaderboard projection" in html


def test_zip_contains_single_tiff():
    import zipfile
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    archive = DOCS / "downloads" / (card["raster_name"][:-4] + ".zip")
    assert archive.is_file()
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        assert names == [card["raster_name"]]
        assert bundle.getinfo(names[0]).file_size > 100_000
