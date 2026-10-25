"""Unit and blocker tests for the preregistered H86N-EQL lane."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.gems86_eql.features import DEQ_BAND, IEQ_BAND, build_features_from_arrays, rank01
from scripts.run_h86n_eql import shared_cache_status

ROOT = Path(__file__).resolve().parents[1]


def test_native_band_bindings_match_the_registered_schema():
    assert DEQ_BAND == 10
    assert IEQ_BAND == 16


def test_rank01_is_footprint_bounded_and_zero_outside():
    fp = np.ones((9, 11), dtype=bool)
    fp[:2, :3] = False
    values = np.arange(fp.size, dtype=np.float32).reshape(fp.shape)
    ranked = rank01(values, fp)
    assert np.all(ranked[~fp] == 0)
    assert np.all((ranked[fp] >= 0) & (ranked[fp] <= 1))
    assert np.isfinite(ranked).all()
    assert np.ptp(ranked[fp]) > 0


def test_eql_features_are_finite_and_outside_footprint_zero():
    yy, xx = np.mgrid[:31, :37]
    fp = np.ones(yy.shape, dtype=bool)
    fp[:3, :] = False
    fp[-2:, :] = False
    # A diagonal synthetic line tests the intended anisotropy transform without
    # representing a scientific experiment or a submission candidate.
    ieq = np.exp(-((yy - xx * 0.55 - 4.0) ** 2) / 10.0).astype(np.float32)
    ieq += 0.05 * np.sin(xx / 3.0).astype(np.float32)
    deq = (np.abs(yy - 12.0) + 1.0).astype(np.float32)
    features = build_features_from_arrays(ieq, deq, fp)
    assert set(features) == {
        "H86N_EQL", "E0_IEQ_intensity", "E1_DEQ_closeness",
        "E2_catalogue_edge", "E3_single_scale_ridge",
    }
    for value in features.values():
        assert value.shape == fp.shape
        assert np.isfinite(value).all()
        assert np.all(value[~fp] == 0)
        assert np.all((value[fp] >= 0) & (value[fp] <= 1))
    assert np.ptp(features["H86N_EQL"][fp]) > 0


def test_shared_cache_gate_is_currently_fail_closed():
    status = shared_cache_status()
    receipt = json.loads((ROOT / "docs/evidence/feature-cache.json").read_text())
    assert status["available"] is False
    assert status["reason"] in {
        "hash-pinned shared cache bytes are missing",
        "shared cache receipt does not certify visible-catalogue recomputation per fold",
        "shared cache lacks the preregistered seismic channels",
    }
    assert receipt["cache_bytes"] == 982332800
    assert receipt["cache_sha256"] == "873b419b3de7e4e91efe26c7fc7141f0c3b7fd9ce933c015ca87b258003a22f4"


def test_h86n_blocked_run_card_has_no_score_or_raster():
    card = json.loads((ROOT / "docs/evidence/h86n-eql-run-card.json").read_text())
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["experiments_run"] == 0
    assert card["raster_sha256"] is None
    assert card["holdout_dti"]["dti"] is None
    assert card["holdout_dti"]["ci95"] is None
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
