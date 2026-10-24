"""Unit tests for the catalogue-blind H86E-MMT feature transform."""
import json
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

from src.gems86_mmt.features import build_marker_features, feature_names, rank01

ROOT = Path(__file__).resolve().parents[1]


def test_rank01_is_bounded_and_deterministic():
    fp = np.ones((3, 4), dtype=bool)
    a = np.arange(12, dtype=np.float32).reshape(3, 4)
    got = rank01(a, fp)
    assert got.dtype == np.float32
    assert np.all((got >= 0) & (got <= 1))
    assert np.array_equal(got, rank01(a, fp))


def test_marker_features_are_finite_and_masked(tmp_path: Path):
    path = tmp_path / "features.tif"
    h, w = 32, 32
    yy, xx = np.mgrid[:h, :w]
    bands = np.empty((9, h, w), dtype=np.float32)
    bands[1] = np.sin(xx / 3.0) + yy / 40.0       # RTP (band 2)
    bands[2] = np.cos(yy / 4.0) + xx / 50.0       # TMI HG (band 3)
    bands[5] = 10.0 + xx / 20.0                   # TC (band 6)
    bands[8] = np.sin((xx + yy) / 5.0)            # TMI VG (band 9)
    for i in (0, 3, 4, 6, 7):
        bands[i] = (i + 1) * 0.1
    with rasterio.open(
        path, "w", driver="GTiff", height=h, width=w, count=9,
        dtype="float32", crs="EPSG:32611",
        transform=Affine(100, 0, 0, 0, -100, h * 100),
    ) as dst:
        dst.write(bands)

    fp = np.ones((h, w), dtype=bool)
    fp[:2, :3] = False
    fields = build_marker_features(path, fp)
    assert tuple(fields) == feature_names()
    for name, field in fields.items():
        assert field.shape == fp.shape, name
        assert field.dtype == np.float32, name
        assert np.isfinite(field).all(), name
        assert np.all(field[~fp] == 0), name


def test_mmt_preregistration_and_run_card_are_explicitly_negative():
    prereg = json.loads((ROOT / "research/H86E_MMT_PREREGISTRATION.json").read_text())
    assert 3 <= len(prereg["arms"]) <= 5
    assert prereg["budget"] == {"max_arms": 3, "max_hours": 2, "dots": 44090}
    assert prereg["holdout"]["alpha"] == 0.2
    assert prereg["holdout"]["beta"] == 0.8
    card = json.loads((ROOT / "docs/evidence/h86e-mmt-run-card.json").read_text())
    assert card["verdict"] == "negative"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    assert card["holdout_dti"]["evidence_class"] == "HOLDOUT-DTI"
    assert card["holdout_dti"]["withheld_positive_pixels"] == 11321
    assert card["correlation_overlap_vs_registry"]["pa86_02"]["gate_pass"] is False
