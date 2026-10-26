"""Synthetic-oracle tests for H86P-PFA paired-flank asymmetry (no data downloads)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]
from gems86_pfa.features import PFA_NAMES, STATIC_NAMES, paired_flank_asymmetry  # noqa


def test_step_beats_ridge_and_flat():
    fp = np.ones((81, 81), bool)
    # Vertical step: left 0, right 10, contact at col 40.
    step = np.zeros((81, 81), np.float32); step[:, 40:] = 10.0
    s_step, ax_step = paired_flank_asymmetry(step, fp)
    # Narrow ridge/dike: 3-px wide spike at col 40, same amplitude.
    ridge = np.zeros((81, 81), np.float32); ridge[:, 39:42] = 10.0
    s_ridge, _ = paired_flank_asymmetry(ridge, fp)
    flat = np.full((81, 81), 3.0, np.float32)
    s_flat, _ = paired_flank_asymmetry(flat, fp)
    # On the contact columns the step must dominate the same columns of the ridge.
    assert s_step[:, 38:43].max() > 3.0 * max(s_ridge[:, 38:43].max(), 1e-9)
    assert s_step[:, 38:43].max() > 1.0
    assert s_flat.max() == 0.0
    # Best axis on the contact should be the E-W normal (axis 0 = (0,1)).
    assert int(np.bincount(ax_step[:, 39:42].ravel(), minlength=4).argmax()) == 0


def test_outside_footprint_zero_and_finite():
    rng = np.random.default_rng(0)
    fp = np.zeros((41, 41), bool); fp[5:35, 5:35] = True
    f = (rng.standard_normal((41, 41)) * 5).astype(np.float32)
    s, ax = paired_flank_asymmetry(f, fp)
    assert np.isfinite(s).all() and (s[~fp] == 0).all() and (s >= 0).all()
    assert ax.min() >= 0 and ax.max() < 4


def test_preregistration_is_frozen_and_names_match():
    pre = json.loads((ROOT / "research/H86P_PFA_PREREGISTRATION.json").read_text())
    hyp = json.loads((ROOT / "registry/h86p_pfa_hypotheses.json").read_text())
    assert pre["lane_id"] == "H86P-PFA" and len(pre["arms"]) == 3
    assert pre["budget"] == {"max_experiments": 3, "max_hours": 2, "dots": 37654,
                             "spacing_px": 2.8, "collar_px": 3.0}
    assert len(hyp["hypotheses"]) == 5 and hyp["hypotheses"][0]["id"] == "H86P-PFA"
    assert len(PFA_NAMES) == 8 and len(STATIC_NAMES) == 20
    assert hyp["hypotheses"][4]["status"] == "NOT_VIABLE_IN_SANDBOX_EGRESS"
