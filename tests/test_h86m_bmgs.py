"""Unit and protocol verification tests for Lane H86M-BMGS."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.special import erf

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "src", ROOT / "vendor"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems86_bmgs import (
    ABLATION_RAW_NAMES,
    BANNED_CSV_COLUMNS,
    BMGS_STATIC_NAMES,
    axial_geodesic_strand_sharpen,
    dilatation_gated_shallow_pullback,
    elkan_quadrant_aligned_posterior,
    out_of_quadrant_bmr_gravity,
    steerable_quadrature_step_asymmetry,
    transtensional_conductance_neck,
    verify_bmgs_input_contract,
)


def test_h86m_hypothesis_queue_and_preregistration_contract():
    q_doc = json.loads((ROOT / "registry/h86m_bmgs_hypotheses.json").read_text(encoding="utf-8"))
    assert q_doc["schema"] == "gems86.hypothesis_queue.v1"
    hyps = q_doc["hypotheses"]
    assert 3 <= len(hyps) <= 5
    assert hyps[0]["id"] == "H86M-BMGS"
    assert hyps[0]["status"] == "SELECTED_FOR_VALIDATION"
    assert any(h["status"] == "DEFERRED_EXTERNAL_SOURCE_EGRESS_BLOCKED" for h in hyps)

    prereg = json.loads(
        (ROOT / "research/H86M_BMGS_PREREGISTRATION.json").read_text(encoding="utf-8")
    )
    assert prereg["lane_id"] == "H86M-BMGS"
    assert prereg["budget"]["max_experiments"] == 3
    assert prereg["budget"]["dot_budget"] == 37654
    assert prereg["static_features"] == list(BMGS_STATIC_NAMES)
    assert prereg["ablation_control_features"] == list(ABLATION_RAW_NAMES)
    assert "dist_known_fault_px" in BANNED_CSV_COLUMNS
    assert "dist_known_fault_px" in prereg["banned_columns"]

    qc = verify_bmgs_input_contract(None)
    assert qc["raw_dem_bands_excluded_from_cover_blind"] == [12, 19]


def test_out_of_quadrant_bmr_cancels_smooth_basin_and_preserves_horst_step():
    h, w = 128, 128
    yy, xx = np.indices((h, w), dtype=np.float32)
    valid = np.ones((h, w), dtype=bool)

    # Smooth Cenozoic basin depth bowl across all 4 quadrants
    zb = 1800.0 * np.exp(-(((yy - 64.0) / 36.0) ** 2 + ((xx - 64.0) / 40.0) ** 2))
    # Intrabasin vertical fault step along col=78 uncorrelated with basin center
    horst_step = 4.5 * erf((xx - 78.0) / 2.2)
    b13 = (-0.016 * zb + horst_step).astype(np.float32)
    b18 = np.gradient(b13, axis=1).astype(np.float32) / 100.0
    b11 = np.gradient(b13, axis=0).astype(np.float32) / 100.0

    r_bmr, bmr_grad, bmr_gzz, bmr_disc = out_of_quadrant_bmr_gravity(
        b13, zb, b11, b18, valid, subsample_step=2
    )
    # Away from the horst step (cols 15..55), smooth basin variance is strongly suppressed
    away = (xx >= 15) & (xx <= 55) & (yy >= 15) & (yy <= 110)
    assert float(np.std(r_bmr[away])) < 0.25 * float(np.std(b13[away]))
    # BMR gradient peaks sharply on the intrabasin horst fault at col=78
    step_band = np.abs(xx - 78.0) <= 2.5
    off_band = np.abs(xx - 40.0) <= 4.0
    assert float(bmr_grad[step_band].mean()) > 4.0 * float(bmr_grad[off_band].mean())
    assert np.all(np.isfinite(bmr_gzz)) and np.all(np.isfinite(bmr_disc))


def test_steerable_gsst_suppresses_symmetric_dike_and_recovers_fault_strike():
    h, w = 96, 96
    yy, xx = np.indices((h, w), dtype=np.float32)
    valid = np.ones((h, w), dtype=bool)

    # Vertical N-S fault step at x=28 (strike along +row -> theta = pi/2) vs symmetric dike at x=68
    fault_step = 0.5 * (1.0 + erf((xx - 28.0) / 2.5))
    dike_ridge = np.exp(-0.5 * ((xx - 68.0) / 2.2) ** 2)
    field = (fault_step + dike_ridge).astype(np.float32)

    odd_dom, theta_strike, spin2 = steerable_quadrature_step_asymmetry(
        field, valid, sigmas=(2.0, 4.0), dike_veto=0.85
    )
    fault_resp = float(odd_dom[20:76, 27:30].max())
    dike_crest_resp = float(odd_dom[20:76, 67:70].max())
    assert fault_resp > 3.5 * max(dike_crest_resp, 1e-6)

    # Strike along N-S vertical line has grid strike angle pi/2 rad -> cos(2*theta) ~= -1
    est_theta = float(np.median(theta_strike[24:72, 28]))
    ang_err = abs(np.sin(est_theta - 0.5 * np.pi))
    assert ang_err < 0.15
    assert float(spin2[24:72, 28].mean()) > 0.38

    # Isotropic circular dome has near-zero spin-2 azimuthal coherence at its center
    dome = np.exp(-0.5 * (((xx - 48.0) ** 2 + (yy - 48.0) ** 2) / 36.0)).astype(np.float32)
    _, _, dome_spin2 = steerable_quadrature_step_asymmetry(dome, valid, sigmas=(2.0, 4.0))
    assert float(dome_spin2[47:50, 47:50].mean()) < 0.05


def test_cnt_neck_and_shallow_pullback_respect_physical_regimes():
    h, w = 80, 80
    yy, xx = np.indices((h, w), dtype=np.float32)
    valid = np.ones((h, w), dtype=bool)

    # Narrow conductive fault corridor at x=25 vs broad flat playa in x=52..72
    corridor = 45.0 * np.exp(-0.5 * ((xx - 25.0) / 1.8) ** 2)
    playa = 80.0 * (1.0 / (1.0 + np.exp(-(xx - 48.0) / 2.0)))
    cond_b17 = (corridor + playa).astype(np.float32)
    dilate_b8 = np.where(xx < 42.0, 2.0, -0.5).astype(np.float32)
    shear_b7 = np.ones((h, w), dtype=np.float32) * 0.2
    slope10 = np.where(xx > 50.0, 0.005, 0.08).astype(np.float32)
    strike = np.full((h, w), 0.5 * np.pi, dtype=np.float32)

    neck, step = transtensional_conductance_neck(
        cond_b17, dilate_b8, shear_b7, slope10, strike, valid
    )
    assert float(neck[20:60, 24:27].mean()) > 3.0 * float(neck[20:60, 60:70].mean())
    assert np.all(step >= 0.0)

    # Strike-slip regime (shear >> dilatation) keeps steep contact unshifted
    sub_step = np.exp(-0.5 * ((xx - 40.0) / 1.2) ** 2).astype(np.float32)
    zb_ramp = np.maximum((xx - 34.0) * 120.0, 0.0).astype(np.float32)
    pb_ss = dilatation_gated_shallow_pullback(
        sub_step,
        zb_ramp,
        dilate_b8=np.full((h, w), -2.0, dtype=np.float32),
        shear_b7=np.full((h, w), 3.0, dtype=np.float32),
        valid=valid,
        max_shift_px=3.0,
    )
    peak_col_ss = int(np.argmax(pb_ss[40]))
    assert abs(peak_col_ss - 40) <= 1


def test_elkan_calibration_and_axial_strand_coherence():
    h, w = 64, 64
    valid = np.ones((h, w), dtype=bool)
    raw = np.full((h, w), 0.03, dtype=np.float32)
    # Collinear horizontal strand on row 20 vs isolated 1-pixel speckle at (48, 32)
    raw[20, 16:48] = 0.85
    raw[48, 32] = 0.85

    p_bayes = elkan_quadrant_aligned_posterior(raw, neg_subsample_ratio=25.0, valid=valid)
    assert float(np.median(p_bayes)) < 0.005

    strike_ew = np.zeros((h, w), dtype=np.float32)  # E-W strike -> theta = 0
    p_sharp = axial_geodesic_strand_sharpen(p_bayes, strike_ew, valid)
    assert float(p_sharp[20, 32]) > 1.22 * float(p_sharp[48, 32])
    # Single-pixel / curved point is never multiplicatively crushed below 70% of p_bayes
    assert float(p_sharp[48, 32]) >= 0.70 * float(p_bayes[48, 32])
    assert float(p_sharp.min()) >= 0.0 and float(p_sharp.max()) <= 1.0


def test_h86m_run_card_invariants_when_present():
    card_path = ROOT / "docs/evidence/h86m-bmgs-run-card.json"
    if not card_path.is_file():
        pytest.skip("H86M-BMGS run card not yet generated")
    card = json.loads(card_path.read_text(encoding="utf-8"))
    assert card["lane_id"] == "H86M-BMGS"
    assert card["experiments_run"] == 3
    assert card["submission_slots_used"] == 0
    assert card["note_chars"] <= 140
    assert card["validator_output"]["all_checks_passed"] is True
    assert card["validator_output"]["values_in_0_1"] is True
    assert card["validator_output"]["no_nan_inside_footprint"] is True
    assert card["validator_output"]["crs_shape_transform_match"] is True
    assert card["holdout_dti"]["leakage_canary_summary"]["any_leakage_flag"] is False
    assert card["holdout_dti"]["leakage_canary_summary"]["max_discriminative_auc"] <= 0.90
    assert (
        card["correlation_overlap_vs_registry"]["surface_preplacement"][
            "worst_spearman_full_footprint"
        ]
        <= 0.90
    )
