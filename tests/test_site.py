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
    assert "NO CANDIDATE AUTHORIZED" in html
    assert "OK TO DOWNLOAD AND SUBMIT" not in html
    assert rmrb["safe_to_download"] is True
    assert rmrb["safe_to_submit"] is False


def test_zip_contains_single_tiff():
    import zipfile
    card = json.loads((ROOT / "evidence/run_card.json").read_text())
    archive = DOCS / "downloads" / (card["raster_name"][:-4] + ".zip")
    assert archive.is_file()
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        assert names == [card["raster_name"]]
        assert bundle.getinfo(names[0]).file_size > 100_000
