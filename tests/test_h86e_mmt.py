"""Unit tests for the catalogue-blind H86E-MMT feature transform."""
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine

from src.gems86_mmt.features import (
    ORIENTATIONS_DEG,
    _lag_shift_vector,
    build_marker_features,
    feature_names,
    rank01,
)

ROOT = Path(__file__).resolve().parents[1]


def test_rank01_is_bounded_and_deterministic():
    fp = np.ones((3, 4), dtype=bool)
    a = np.arange(12, dtype=np.float32).reshape(3, 4)
    got = rank01(a, fp)
    assert got.dtype == np.float32
    assert np.all((got >= 0) & (got <= 1))
    assert np.allclose(got.ravel(), np.linspace(0.0, 1.0, 12, dtype=np.float32))
    assert np.array_equal(got, rank01(a, fp))


def test_rank01_eliminates_north_south_tie_ramp_on_binary_fields():
    """Regression test for IR-86-MMT-RANK01-TIE-20261024."""
    fp = np.ones((20, 10), dtype=bool)
    binary = np.zeros((20, 10), dtype=np.float32)
    binary[1, 3] = 1.0
    binary[18, 7] = 1.0
    got = rank01(binary, fp)
    zero_ranks = got[fp & (binary == 0)]
    one_ranks = got[fp & (binary > 0)]
    assert np.all(zero_ranks == 0.0)
    assert np.allclose(one_ranks, 198.0 / 199.0)
    assert float(one_ranks[0]) == float(one_ranks[1])
    # Constant and empty masks return clean zeros without NaN or division errors.
    assert np.all(rank01(np.zeros((4, 4), dtype=np.float32), np.ones((4, 4), dtype=bool)) == 0.0)
    assert np.all(rank01(np.ones((4, 4), dtype=np.float32), np.zeros((4, 4), dtype=bool)) == 0.0)


def test_rank01_handles_nonfinite_values_without_nan_propagation():
    """Pass-2 edge-case regression: NaN/Inf inside footprint must never poison rank01."""
    fp = np.ones((2, 3), dtype=bool)
    arr = np.array([[0.0, np.nan, 1.0], [np.inf, -np.inf, 2.0]], dtype=np.float32)
    got = rank01(arr, fp)
    assert np.isfinite(got).all()
    assert np.all((got >= 0.0) & (got <= 1.0))
    assert got[0, 1] == 0.0 and got[1, 0] == 0.0 and got[1, 1] == 0.0
    assert got[1, 2] > got[0, 2] > got[0, 0]
    assert np.all(rank01(np.full((3, 3), np.nan, dtype=np.float32), np.ones((3, 3), dtype=bool)) == 0.0)


def test_lag_shift_vector_strike_is_orthogonal_to_gradient_normal():
    """Regression test for IR-86-MMT-SHIFT-AXIS-20261024."""
    for theta in ORIENTATIONS_DEG:
        rad = np.deg2rad(theta)
        ndy, ndx = float(np.sin(rad)), float(np.cos(rad))
        sdy, sdx = _lag_shift_vector(theta, 4.0, shift_axis="strike")
        assert abs(ndy * sdy + ndx * sdx) < 1e-12
        assert abs(np.hypot(sdy, sdx) - 4.0) < 1e-12
        ldy, ldx = _lag_shift_vector(theta, 4.0, shift_axis="normal")
        assert abs(ndy * ldy + ndx * ldx - 4.0) < 1e-12
    with pytest.raises(ValueError):
        _lag_shift_vector(30.0, 2.0, shift_axis="invalid")


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
