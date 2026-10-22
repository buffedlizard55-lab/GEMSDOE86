"""The published site must link a downloadable file that exists and matches the run card."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_download_link_present():
    html = (DOCS / "index.html").read_text()
    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    assert card["raster_name"] in html
    assert (DOCS / "downloads" / card["raster_name"]).is_file()
    assert "OK TO DOWNLOAD AND SUBMIT" not in html
    assert card["submission_ready"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["verdict"] == "negative"
    assert "DO NOT SUBMIT" in html


def test_zip_contains_single_tiff():
    import zipfile
    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    z = DOCS / "downloads" / (card["raster_name"][:-4] + ".zip")
    assert z.is_file()
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        assert names == [card["raster_name"]]
        assert zf.getinfo(names[0]).file_size > 100_000
