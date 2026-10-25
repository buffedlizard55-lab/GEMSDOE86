"""H86J-MPC unit tests: synthetic step/ridge discrimination + invariants.

These pin the step-vs-line convention empirically (preregistration
research/H86J_MPC_PREREGISTRATION.md) before any real field is trusted.
The shipped-card guards then lock the lane's measured *negative* state:
the falsified hypothesis must never be quietly rebranded as promotable.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from gems86_mpc.features import WAVELENGTHS_FINE, corroborate, monogenic_pc

ROOT = Path(__file__).resolve().parents[1]

SHAPE = (128, 128)
FP = np.ones(SHAPE, bool)


def _step(amplitude=1.0):
    a = np.zeros(SHAPE, np.float32)
    a[:, 64:] = amplitude
    return a


def _ridge(amplitude=1.0, sigma=2.0):
    x = np.arange(SHAPE[1], dtype=np.float32)
    prof = amplitude * np.exp(-0.5 * ((x - 64.0) / sigma) ** 2)
    return np.repeat(prof[None, :], SHAPE[0], axis=0).astype(np.float32)


def test_step_is_pc_step_not_pc_line():
    out = monogenic_pc(_step(), FP, WAVELENGTHS_FINE)
    # Compare at the feature centre (column of max pc_step): the local phase
    # rotates away from the centre, so a window-max comparison is unphysical.
    profile = out["pc_step"][64, :]
    col = int(np.argmax(profile))
    assert abs(col - 64) <= 1
    assert profile[col] > 0.5
    # at the step centre the odd (step) response dominates the even (line) one
    assert profile[col] > 2.0 * out["pc_line"][64, col]
    far = out["pc_step"][:, :32]
    assert far.max() < profile[col]


def test_ridge_centre_is_pc_line_not_pc_step():
    out = monogenic_pc(_ridge(), FP, WAVELENGTHS_FINE)
    profile = out["pc_line"][64, :]
    col = int(np.argmax(profile))
    assert abs(col - 64) <= 1
    assert profile[col] > 0.5
    assert profile[col] > 2.0 * out["pc_step"][64, col]


def test_contrast_invariance():
    hi = monogenic_pc(_step(10.0), FP, WAVELENGTHS_FINE)
    lo = monogenic_pc(_step(0.01), FP, WAVELENGTHS_FINE)
    edge = (slice(32, 96), slice(63, 66))
    a, b = hi["pc_step"][edge].max(), lo["pc_step"][edge].max()
    assert a > 0.5 and b > 0.5
    assert abs(float(a) - float(b)) < 0.05  # amplitude detectors would differ 1000x


def test_ranges_and_constant_field():
    out = monogenic_pc(np.ones(SHAPE, np.float32), FP, WAVELENGTHS_FINE)
    for k in ("pc", "pc_step", "pc_line", "stepness"):
        assert np.isfinite(out[k]).all(), k
        assert out[k].min() >= 0.0 and out[k].max() <= 1.0, k
    assert out["pc"].max() < 0.05  # no feature in a constant field


def test_corroborate_bounds():
    rng = np.random.default_rng(3)
    ranks = [rng.random(SHAPE, dtype=np.float32) for _ in range(3)]
    s = corroborate(ranks, FP)
    assert s.shape == SHAPE and np.isfinite(s).all()
    assert 0.0 <= float(s.min()) and float(s.max()) <= 1.0


def test_preregistration_frozen_budget():
    doc = json.loads((ROOT / "research/H86J_MPC_PREREGISTRATION.json").read_text())
    assert doc["budget"]["max_experiments"] == 3 and doc["budget"]["max_hours"] == 2
    assert doc["budget"]["dots_frozen"] == 44090
    assert len(doc["hypotheses_ranked"]) == 5 and len(doc["arms"]) == 3


def test_shipped_card_is_measured_negative_and_bound_to_raster():
    card = json.loads((ROOT / "docs/evidence/h86j-mpc-run-card.json").read_text())
    assert card["verdict"] == "negative" and card["decision"] == "DO NOT SUBMIT"
    assert card["submission_slots_used"] == 0 and card["experiments_run"] == 3
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["organizer_confirmed"] is None
    # Falsification is the measured result: SGMC gate + falsifiers must stay False,
    # canary + floor + local uniqueness stay True.
    assert card["gates"] == {"canary_leakage": True,
                             "sgmc_proxy_beats_H33_paired_ci": False,
                             "catalogue_hide_floor_vs_H33": True,
                             "falsifiers_amplitude_and_line": False,
                             "uniqueness_local_registry": True}
    assert card["sgmc_proxy"]["paired_delta_vs_H33_as_is"]["ci95"][1] < 0
    assert (card["sgmc_proxy"]["candidate"]["dti"]
            < card["ablations"]["AMP-GRADMAG"]["budgets"]["44090"]["sgmc_proxy_dti"])
    hn = card["holdout_dti_normalized"]
    assert hn["evidence_class"] == "HOLDOUT-DTI"
    assert hn["evaluator_version"] == "gems57-pooled-hide-v2" and hn["n_truth"] == 11321
    assert len(card["note"]) == card["note_chars"] <= 140
    assert max(v["discriminative_auc"] for v in card["leakage_canaries"].values()) <= 0.90
    tif = ROOT / card["submission_file"]
    assert tif.is_file()
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == card["raster_sha256"]
    receipt = json.loads(tif.with_suffix(".json").read_text())
    assert receipt["sha256"] == card["raster_sha256"]
    assert receipt["gate_verdict"] == "negative"


def test_shipped_raster_is_binary_grid_locked():
    rasterio = pytest.importorskip("rasterio")
    card = json.loads((ROOT / "docs/evidence/h86j-mpc-run-card.json").read_text())
    with rasterio.open(ROOT / card["submission_file"]) as ds:
        a = ds.read(1)
        assert ds.count == 1 and str(ds.crs) == "EPSG:32611" and ds.shape == (3730, 3292)
        assert ds.nodata is None
    assert np.isfinite(a).all()
    assert set(np.unique(a).tolist()) == {0.0, 1.0}
    assert int((a > 0).sum()) == card["chosen_budget"] == 44090
