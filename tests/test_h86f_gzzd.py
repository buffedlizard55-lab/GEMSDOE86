"""Unit tests for the H86F-GZZD Laplace dipole transform and its gates.

The synthetic test builds an exact gravity step: Band 13 is a smooth ramp,
Bands 18/11 are its analytic image-coordinate derivatives, Band 15 steps the
other way (deeper basement on the gravity-low side). The dipole statistic
must localize on the step line; a same-polarity (monopolar) field must not.
"""
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine

from src.gems86_gzzd.features import build_gzzd_features, dipole_pairing, feature_names

ROOT = Path(__file__).resolve().parents[1]


def _write_features(path: Path, bands19: np.ndarray) -> None:
    h, w = bands19.shape[1:]
    with rasterio.open(
        path, "w", driver="GTiff", height=h, width=w, count=19,
        dtype="float32", crs="EPSG:32611",
        transform=Affine(100, 0, 0, 0, -100, h * 100),
    ) as dst:
        dst.write(bands19)


def test_dipole_pairing_requires_opposite_signs():
    plus = np.array([2.0, -2.0, 2.0, 0.0], np.float32)
    minus = np.array([-3.0, 3.0, 3.0, -1.0], np.float32)
    got = dipole_pairing(plus, minus)
    assert got[0] == pytest.approx(np.sqrt(6.0))
    assert got[1] == pytest.approx(np.sqrt(6.0))
    assert got[2] == 0.0  # same-sign flanks: monopolar, not a step dipole
    assert got[3] == 0.0


def test_synthetic_basement_step_localizes(tmp_path: Path):
    h, w = 96, 96
    xx = np.tile(np.arange(w, dtype=np.float32), (h, 1))
    # Gravity low east of x=48 (downthrown, thicker low-density fill).
    grav = (-8.0 * np.tanh((xx - 48.0) / 3.0)).astype(np.float32)
    gx = np.gradient(grav, axis=1).astype(np.float32)
    grow = np.gradient(grav, axis=0).astype(np.float32)
    bands = np.zeros((19, h, w), np.float32)
    bands[4] = np.hypot(gx, grow)                     # Band 5 magnitude
    bands[10] = grow                                  # Band 11 = dg/drow
    bands[12] = grav                                  # Band 13
    bands[14] = 400.0 + 300.0 * np.tanh((xx - 48.0) / 3.0)  # Band 15 deeper east
    bands[17] = gx                                    # Band 18 = dg/dx
    path = tmp_path / "training_features.tif"
    _write_features(path, bands)

    fp = np.ones((h, w), bool)
    fp[:2, :3] = False
    fields, qc = build_gzzd_features(path, fp)
    assert tuple(fields) == feature_names()
    for name, field in fields.items():
        assert field.shape == fp.shape and field.dtype == np.float32, name
        assert np.isfinite(field).all(), name
        assert np.all(field[~fp] == 0), name
    assert qc["corr_gzz_vs_neg_laplacian_band13"] > 0.99

    dipole = fields["gzzd_dipole"][40:56, :]
    near_step = dipole[:, 45:52].mean()
    far = np.concatenate([dipole[:, 5:20].ravel(), dipole[:, 75:90].ravel()]).mean()
    assert near_step > 5.0 * max(far, 1e-12)
    # Concordant construction (depth up where gravity down): E1 keeps the step response.
    conc = fields["gzzd_concordant"][40:56, 45:52].mean()
    assert conc >= 0.9 * near_step


def test_preregistration_is_frozen_and_complete():
    doc = json.loads((ROOT / "research/H86F_GZZD_PREREGISTRATION.json").read_text())
    assert doc["lane"] == "H86F-GZZD"
    assert doc["status"] == "frozen_before_lane_computation"
    assert 3 <= len(doc["ranked_hypotheses"]) <= 5
    assert [a["id"] for a in doc["arms"]] == [
        "E1_gzzd_concordant", "E2_gzzd_dipole", "E3_gravmag_edge_control",
    ]
    assert doc["budget"] == {"max_arms": 3, "max_hours": 2, "dots": 44090}
    assert doc["holdout"]["alpha"] == 0.2 and doc["holdout"]["beta"] == 0.8
    assert doc["holdout"]["kernel_m"] == 300
    required = {"layers", "transform", "non_fault_mimic", "uncatalogued_rationale",
                "novelty", "cost", "official_data"}
    for item in (*doc["ranked_hypotheses"], *doc["arms"]):
        assert required.issubset(item), item["id"]
    top = doc["ranked_hypotheses"][0]
    assert top["id"] == "H86F-GZZD"


def test_run_card_if_present_is_consistent_and_slot_free():
    card_path = ROOT / "docs/evidence/h86f-gzzd-run-card.json"
    if not card_path.is_file():
        pytest.skip("lane not run in this checkout yet")
    card = json.loads(card_path.read_text())
    assert card["lane"] == "H86F-GZZD"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321
    assert all(not v["leakage_flag"] for v in h["leakage_canary"].values())
    if card["verdict"] == "promote":
        assert h["beats_current_with_separated_ci"] is True
        assert h["paired_delta_beats_control"] is True
        assert card["decision"] == "SELECTOR STEP REQUIRED"
    else:
        assert card["verdict"] == "negative"
        assert card["decision"] == "DO NOT SUBMIT"
    if card["raster_sha256"] is not None:
        v = card["validator_output"]
        assert v["all_checks_passed"] is True
        assert v["values_in_0_1"] is True and v["no_nan_inside_footprint"] is True
        assert v["min"] >= 0.0 and v["max"] <= 1.0
        assert card["note_chars"] == len(card["note"]) <= 140
        assert len(card["submission_name"]) <= 140
