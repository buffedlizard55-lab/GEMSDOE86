"""The shipped GeoTIFF must still be the validated artifact, byte for byte."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "evidence" / "run_card.json").read_text())
TIF = ROOT / "docs" / "downloads" / CARD["raster_name"]
SAMPLE = ROOT / "data" / "bridge" / "sample_submission.tif"

pytestmark = pytest.mark.skipif(not TIF.is_file() or not SAMPLE.is_file(), reason="artifact absent")


def test_sha256_matches_card():
    h = hashlib.sha256(TIF.read_bytes()).hexdigest()
    assert h == CARD["raster_sha256"]


def test_grid_and_range():
    with rasterio.open(TIF) as a, rasterio.open(SAMPLE) as b:
        A = a.read(1)
        B = b.read(1)
        assert (a.height, a.width) == (3730, 3292) == (b.height, b.width)
        assert a.count == 1 and a.dtypes[0] == "float32"
        assert a.crs == b.crs and a.transform == b.transform
    assert np.isfinite(A).all()
    assert A.min() >= 0.0 and A.max() <= 1.0
    assert np.isnan(A).sum() == 0
    assert int(((A > 0) & ~np.isfinite(B)).sum()) == 0
    assert int((A > 0).sum()) == CARD["dots"]


def test_receipt_checks():
    rec = json.loads((ROOT / "docs" / "downloads" / (TIF.stem + ".json")).read_text())
    assert rec["validator"]["all_checks_passed"] is True
    assert rec["validator"]["n_nan"] == 0 and rec["validator"]["n_infinite"] == 0
    assert rec["validator"]["on_catalogue_positive_pixels"] == 0
    assert rec["note_chars"] <= 140 and len(rec["submission_name"]) <= 140
