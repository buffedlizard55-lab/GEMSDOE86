"""Geometry tests for the signed basement-step polarity lane."""
import json
from pathlib import Path

import numpy as np

from src.gems86_pcc.features import (
    assemble_scores,
    feature_names,
    horizontal_gradients,
    oblique_weight,
    rank01,
)

ROOT = Path(__file__).resolve().parents[1]


def _step_fields(rtp_sign: float = 1.0, elev_step: float = 0.0, oblique: bool = True):
    """Basement step. Footwall is the low-index side of an oblique or N-S contact."""
    h, w = 64, 64
    yy, xx = np.mgrid[:h, :w]
    contact = (xx + yy < 60) if oblique else (xx < 32)
    grav = np.where(contact, 8.0, 1.0).astype(np.float64)
    rtp = np.where(contact, 5.0 * rtp_sign, -2.0 * rtp_sign).astype(np.float64)
    depth = np.where(contact, 0.4, 2.5).astype(np.float64)
    elev = elev_step * np.where(contact, 1.0, 0.0).astype(np.float64)
    slope = np.zeros((h, w), np.float64)
    if oblique:
        band = np.abs(xx + yy - 60) <= 2
    else:
        band = np.abs(xx - 32) <= 2
    slope[band] = 0.2
    fp = np.ones((h, w), dtype=bool)
    return grav, rtp, depth, elev, slope, fp, contact


def test_rank01_bounds_and_ties_are_stable():
    fp = np.ones((2, 3), dtype=bool)
    a = np.array([[1.0, 1.0, 3.0], [0.0, 2.0, 2.0]], np.float32)
    got = rank01(a, fp)
    assert got.dtype == np.float32
    assert np.all((got >= 0) & (got <= 1))
    assert np.array_equal(got, rank01(a, fp))


def test_north_up_gradient_sign():
    field = np.zeros((16, 16), np.float64)
    field[:, 8:] = 1.0
    east, north = horizontal_gradients(field, sigma=0.8)
    assert float(east[:, 8].mean()) > 0
    assert abs(float(north.mean())) < abs(float(east[:, 8].mean()))


def test_oblique_weight_rejects_survey_axes():
    axis = oblique_weight(np.array([1.0, 0.0]), np.array([0.0, 1.0]))
    oblique = oblique_weight(np.array([1.0]), np.array([1.0]))
    assert np.allclose(axis, 0.0)
    assert np.allclose(oblique, 1.0)


def test_signed_polarity_prefers_footwall_concordant_step():
    grav, rtp, depth, elev, slope, fp, contact = _step_fields(rtp_sign=1.0)
    fields = assemble_scores(grav, rtp, depth, elev, slope, fp)
    assert tuple(fields) == feature_names()
    step = np.abs((np.mgrid[:64, :64][1] + np.mgrid[:64, :64][0]) - 60) <= 3
    far = contact & (np.mgrid[:64, :64][1] < 8)
    assert float(fields["pcc_polarity"][step].mean()) > float(fields["pcc_polarity"][far].mean())
    assert float(fields["pcc_signed"][step].max()) > 0

    grav, rtp, depth, elev, slope, fp, contact = _step_fields(rtp_sign=-1.0)
    flipped = assemble_scores(grav, rtp, depth, elev, slope, fp)
    step = np.abs((np.mgrid[:64, :64][1] + np.mgrid[:64, :64][0]) - 60) <= 3
    # Anti-parallel RTP must not receive signed polarity credit on the step.
    assert float(flipped["pcc_polarity"][step].max()) == 0.0
    assert float(flipped["pcc_unsigned"][step].mean()) > float(flipped["pcc_signed"][step].mean())

    cardinal = assemble_scores(*_step_fields(oblique=False)[:6])
    assert float(fields["pcc_oblique"].max()) > float(cardinal["pcc_oblique"].max())


def test_fields_are_zero_outside_footprint_and_finite():
    grav, rtp, depth, elev, slope, fp, _contact = _step_fields()
    fp[:3, :4] = False
    fields = assemble_scores(grav, rtp, depth, elev, slope, fp)
    for name, field in fields.items():
        assert field.dtype == np.float32, name
        assert np.isfinite(field).all(), name
        assert np.all(field[~fp] == 0), name


def test_generated_tiff_is_negative_and_matches_the_run_card():
    card = json.loads((ROOT / "docs/evidence/h86f-pcc-run-card.json").read_text())
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    name = card["submission_name"]
    tif = ROOT / "docs/downloads" / f"{name}.tif"
    assert tif.is_file()
    import hashlib
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == card["raster_sha256"]
    assert card["validator_output"]["values_in_0_1"] is True
    assert card["validator_output"]["no_nan_inside_footprint"] is True
    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321
    assert h["candidate"]["dti"] < h["current_holdout_best_same_split"]["dti"]
    assert card["decision"] == "DO NOT SUBMIT"


def test_preregistration_freezes_three_arms_and_candidate():
    doc = json.loads((ROOT / "research/H86F_PCC_PREREGISTRATION.json").read_text())
    assert doc["candidate_arm"] == "E1_pcc_signed"
    assert doc["budget"] == {"max_arms": 3, "max_hours": 2, "dots": 44090}
    assert doc["holdout"]["alpha"] == 0.2 and doc["holdout"]["beta"] == 0.8
    runnable = [arm for arm in doc["arms"] if arm["role"] != "ranked hypothesis, not run"
                and arm["role"] != "not viable this session"]
    assert [arm["id"] for arm in runnable] == ["E1_pcc_signed", "E2_pcc_cover", "E3_pcc_unsigned"]
    required = {"layers", "transform", "non_fault_mimic", "uncatalogued_rationale", "novelty", "cost", "official_data"}
    assert all(required.issubset(arm) for arm in doc["arms"])
    assert 3 <= len(doc["arms"]) <= 5
