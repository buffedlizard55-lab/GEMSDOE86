"""Unit, mathematical-oracle, and artifact-integrity tests for H86K-STDP."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "src", ROOT / "vendor"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems57.metric import ALPHA, OFF_DX, OFF_DY, OFF_K
from gems86_stdp import (
    ABLATION_LOCAL_NAMES,
    BANNED_CSV_COLUMNS,
    STDP_STATIC_NAMES,
    calibrate_quadrant_sparse_posterior,
    dinkelbach_celf_allocate_dots,
    exact_six_ring_self_credit,
    salem_multialt_tilt_and_migration,
    static_ek_spacing_allocate,
    updip_hangingwall_pullback,
    verify_stdp_input_contract,
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_stdp_band_contract_and_banned_columns():
    qc = verify_stdp_input_contract()
    assert len(qc["verified_native_bands"]) == 17
    assert qc["verified_native_bands"]["6"] == "tc"
    assert qc["verified_native_bands"]["11"] == "iso_grav_anom_vg"
    assert qc["verified_native_bands"]["15"] == "depth_to_base_surf"
    assert qc["verified_native_bands"]["18"] == "iso_grav_anom_hg"
    assert "dist_known_fault_px" in BANNED_CSV_COLUMNS
    assert len(STDP_STATIC_NAMES) == 24
    assert len(ABLATION_LOCAL_NAMES) == 8


def test_exact_six_ring_self_credit_matches_bernoulli_enumeration_and_mc():
    # Single-pixel impulse: exact supremum expectation must equal p * OFF_K radially
    p_imp = np.zeros((13, 13), dtype=np.float32)
    p_imp[6, 6] = 0.73
    ks_imp = exact_six_ring_self_credit(p_imp)
    for dy, dx, kw in zip(OFF_DY.tolist(), OFF_DX.tolist(), OFF_K.tolist()):
        assert abs(float(ks_imp[6 - dy, 6 - dx]) - 0.73 * float(kw)) < 1e-6

    # Random dense field vs Monte Carlo Bernoulli draws
    rng = np.random.default_rng(861125)
    p = rng.uniform(0.0, 0.35, (13, 13)).astype(np.float32)
    ks = exact_six_ring_self_credit(p)
    draws = rng.random((60_000, 13, 13)) < p[None, :, :]
    mc = np.zeros(60_000, dtype=np.float32)
    for dy, dx, kw in zip(OFF_DY.tolist(), OFF_DX.tolist(), OFF_K.tolist()):
        mc = np.maximum(mc, draws[:, 6 + dy, 6 + dx] * float(kw))
    assert abs(float(ks[6, 6]) - float(mc.mean())) < 5e-3


def test_dinkelbach_celf_matches_bruteforce_submodular_greedy_pixel_for_pixel():
    rng = np.random.default_rng(20261025)
    prob = rng.uniform(0.0, 0.55, (24, 24)).astype(np.float32)
    valid = np.ones((24, 24), dtype=bool)
    known = np.zeros((24, 24), dtype=bool)
    known[0, :] = True
    allowed = valid.copy()
    allowed[:3, :] = False

    lam = 0.24
    res = dinkelbach_celf_allocate_dots(
        prob,
        allowed,
        known_faults=known,
        valid=valid,
        budget=15,
        min_spacing_px=2.8,
        outer_iterations=1,
        initial_lambda=lam,
    )
    assert res.n_dots == 15
    assert not bool((res.dots & ~allowed).any())

    # Exact brute-force O(B * |Omega|) oracle
    p = prob.copy()
    p[~valid | known] = 0.0
    ks = exact_six_ring_self_credit(p)
    cov = np.zeros((24, 24), dtype=np.float32)
    picked = np.zeros((24, 24), dtype=bool)
    elig = allowed & valid & ~known
    w_tp = 1.0 - ALPHA * lam
    w_fp = ALPHA * lam
    offs = list(zip(OFF_DY.tolist(), OFF_DX.tolist(), OFF_K.tolist()))

    for _ in range(15):
        best_g = -1e18
        best_rc = None
        for r, c in np.argwhere(elig):
            dT = 0.0
            for dr, dc, kw in offs:
                rr, cc = int(r) + dr, int(c) + dc
                if 0 <= rr < 24 and 0 <= cc < 24 and kw > cov[rr, cc]:
                    dT += float(p[rr, cc]) * (kw - float(cov[rr, cc]))
            if dT <= 1e-12:
                continue
            g = w_tp * dT - w_fp * (1.0 - float(ks[r, c]))
            if g > best_g + 1e-12:
                best_g = g
                best_rc = (int(r), int(c))
        assert best_rc is not None
        br, bc = best_rc
        picked[br, bc] = True
        for dr, dc, kw in offs:
            rr, cc = br + dr, bc + dc
            if 0 <= rr < 24 and 0 <= cc < 24 and kw > cov[rr, cc]:
                cov[rr, cc] = kw
        for r2 in range(max(0, br - 3), min(24, br + 4)):
            for c2 in range(max(0, bc - 3), min(24, bc + 4)):
                if (r2 - br) ** 2 + (c2 - bc) ** 2 < 2.8**2:
                    elig[r2, c2] = False

    assert np.array_equal(res.dots, picked)
    ek = static_ek_spacing_allocate(
        prob, allowed, known_faults=known, valid=valid, budget=15, min_spacing_px=2.8
    )
    assert int(ek.sum()) == 15


def test_salem_contrast_invariance_and_updip_pullback_alignment():
    yy, xx = np.mgrid[0:96, 0:96].astype(np.float32)
    valid = np.ones((96, 96), dtype=bool)
    step = np.tanh((xx - 48.0) / 1.1)
    s1, m1 = salem_multialt_tilt_and_migration(step, valid)
    s50, m50 = salem_multialt_tilt_and_migration(50.0 * step, valid)
    assert float(np.max(np.abs(s1[16:-16, 16:-16] - s50[16:-16, 16:-16]))) < 1e-4
    assert float(np.max(np.abs(m1[16:-16, 16:-16] - m50[16:-16, 16:-16]))) < 1e-4

    # Surface trace at col=30, dipping eastward -> subsurface step peak at col=34
    zb = np.where(xx > 30.0, np.minimum((xx - 30.0) * 231.0, 1200.0), 0.0).astype(
        np.float32
    )
    deep_peak = np.exp(-0.5 * ((xx - 34.0) / 1.2) ** 2).astype(np.float32)
    pulled, keystone = updip_hangingwall_pullback(
        deep_peak, zb, valid, pulled_weight=1.0
    )
    assert int(np.argmax(pulled[48, :])) == 30
    assert keystone.shape == (96, 96) and float(keystone.max()) > 0.0


def test_quadrant_sparse_calibration_eliminates_interquadrant_shift():
    rng = np.random.default_rng(99)
    base_logits = rng.normal(0.0, 1.0, (40, 40))
    # Inject severe artificial baseline depression in NE (rows < 20, cols >= 20)
    shifted = base_logits.copy()
    shifted[:20, 20:] -= 3.5
    raw_p = (1.0 / (1.0 + np.exp(-shifted))).astype(np.float32)
    valid = np.ones((40, 40), dtype=bool)
    cal = calibrate_quadrant_sparse_posterior(raw_p, valid)
    assert abs(float(np.median(cal[:20, :20])) - float(np.median(cal[:20, 20:]))) < 1e-5
    assert 0.005 < float(np.median(cal)) < 0.025


def test_h86k_stdp_run_card_and_serialized_geotiff_invariants():
    card_path = ROOT / "docs/evidence/h86k-stdp-run-card.json"
    assert card_path.is_file()
    card = json.loads(card_path.read_text(encoding="utf-8"))

    assert card["lane_id"] == "H86K-STDP"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    assert 1 <= card["note_chars"] == len(card["note"]) <= 140

    # Verify banned column exclusion in QC receipt
    qc = card["mechanism"]["band_physics_verification"]
    assert "dist_known_fault_px" in qc["banned_csv_columns"]
    for cols in qc["accessed_csv_columns"].values():
        assert "dist_known_fault_px" not in cols

    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321
    assert h["leakage_canary_summary"]["any_leakage_flag"] is False
    assert h["leakage_canary_summary"]["max_discriminative_auc"] <= 0.90
    assert h["per_fold"]["E2_stdp_blind_dinkelbach_celf"]["NE"]["dti"] > 0.05

    sg = card["sgmc_off_catalogue_diagnostic"]
    assert sg["evidence_class"] == "SGMC-PROXY-DTI"
    for comp in (
        "H33_GEMSDOE32_as_is",
        "D28_GEMSDOE28_as_is",
        "H86J_MCSP_37654_as_is",
        "H86F_EWCS_37654_as_is",
        "E3_pixel_local_staticek_ablation",
    ):
        assert sg["paired_differences_vs_candidate"][comp]["ci95"][0] > 0.0, comp

    reg = card["correlation_overlap_vs_registry"]
    assert reg["surface_preplacement"]["rho_firings_over_0p90"] == 0
    assert reg["full_registry_informative_dot_field_audit"]["discrete_le_90k_firings_over_0p70"] == 0

    tif_path = ROOT / card["submission_file"]
    zip_path = ROOT / card["submission_zip"]
    rec_path = ROOT / card["submission_receipt"]
    assert tif_path.is_file() and zip_path.is_file() and rec_path.is_file()
    assert _sha256(tif_path) == card["raster_sha256"]
    assert _sha256(zip_path) == card["zip_sha256"]

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert zf.read(tif_path.name) == tif_path.read_bytes()

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        assert (ds.height, ds.width) == (3730, 3292)
        assert str(ds.crs) == "EPSG:32611"
        arr = ds.read(1)
        assert np.isfinite(arr).all()
        assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
        assert int((arr == 1.0).sum()) == 37654
