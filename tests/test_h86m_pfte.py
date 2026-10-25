"""Unit and synthetic-oracle tests for Lane H86M-PFTE."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
VENDOR = ROOT / "vendor"
for _p in (ROOT, SRC, VENDOR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems57.metric import OFF_DX, OFF_DY, OFF_K
from gems86_pfte import (
    PFTE_ABLATION_NAMES,
    PFTE_STATIC_NAMES,
    baranov_pseudogravity_decoupling,
    comonotonic_dcelf_allocate_dots,
    comonotonic_tube_self_credit,
    cordell_parker_3d_basin_strip,
    marussi_curvature_eigensystem,
    peclet_across_strike_barrier,
    verify_pfte_input_contract,
)
from gems86_stdp.dinkelbach_celf import exact_six_ring_self_credit


def test_preregistration_and_band_contract_match():
    qc = verify_pfte_input_contract(None)
    assert qc["banned_csv_columns"] == ["dist_known_fault_px"]
    assert qc["verified_native_bands"]["6"] == "tc"
    assert qc["verified_native_bands"]["11"] == "iso_grav_anom_vg"
    assert qc["verified_native_bands"]["18"] == "iso_grav_anom_hg"

    prereg = json.loads((ROOT / "research/H86M_PFTE_PREREGISTRATION.json").read_text())
    assert prereg["lane_id"] == "H86M-PFTE"
    assert len(prereg["arms"]) == 3
    assert prereg["budget"]["max_experiments"] <= 3
    assert prereg["static_features"] == list(PFTE_STATIC_NAMES)
    assert prereg["ablation_control_features"] == list(PFTE_ABLATION_NAMES)


def test_cordell_parker_3d_strip_enhances_intrabasin_fault_over_bowl():
    H, W = 128, 128
    yy, xx = np.indices((H, W), dtype=np.float32)
    valid = np.ones((H, W), dtype=bool)

    # Broad 2,400 m sedimentary basin bowl + sharp intrabasin horst fault at x = 64
    r2 = ((yy - 64.0) / 28.0) ** 2 + ((xx - 64.0) / 28.0) ** 2
    zb = 2400.0 * np.exp(-r2)
    bowl_grav = -24.0 * np.exp(-r2)
    fault_step = 2.6 * np.tanh((xx - 64.0) / 1.8) * np.exp(-(((yy - 64.0) / 30.0) ** 2))
    gz = bowl_grav + fault_step
    gx = ndi.gaussian_filter(gz, sigma=1.0, order=(0, 1)) * 10.0
    gr = ndi.gaussian_filter(gz, sigma=1.0, order=(1, 0)) * 10.0

    raw_slope = np.hypot(gx, gr)
    _, dgx, dgr = cordell_parker_3d_basin_strip(gz, gx, gr, zb, valid)
    strip_slope = np.hypot(dgx, dgr)

    fault_band = (np.abs(xx - 64.0) <= 2.0) & (np.abs(yy - 64.0) <= 16.0)
    flank_band = (np.abs(xx - 44.0) <= 3.0) & (np.abs(yy - 64.0) <= 16.0)
    raw_ratio = float(raw_slope[fault_band].mean() / (raw_slope[flank_band].mean() + 1e-6))
    strip_ratio = float(strip_slope[fault_band].mean() / (strip_slope[flank_band].mean() + 1e-6))
    assert strip_ratio > raw_ratio * 1.25


def test_marussi_rejects_circular_plug_and_detects_nonconservative_seam():
    H, W = 96, 96
    yy, xx = np.indices((H, W), dtype=np.float32)
    valid = np.ones((H, W), dtype=bool)

    # Circular volcanic plug dome at (48, 48): both principal curvatures negative at apex -> det > 0
    plug_pot = 10.0 * np.exp(-(((yy - 48.0) ** 2 + (xx - 48.0) ** 2) / (2.0 * 9.0**2)))
    pgx = ndi.gaussian_filter(plug_pot, sigma=0.8, order=(0, 1))
    pgr = ndi.gaussian_filter(plug_pot, sigma=0.8, order=(1, 0))
    m_plug = marussi_curvature_eigensystem(pgx, pgr, valid, sigma_deriv=1.2)
    apex = (np.abs(yy - 48.0) <= 2.0) & (np.abs(xx - 48.0) <= 2.0)
    assert float(m_plug["contact_saddle"][apex].max()) == 0.0
    assert float(m_plug["curl_clean"][16:-16, 16:-16].min()) > 0.92

    # Non-conservative gridding stitch artifact: step in gx along row=48 with zero gr
    seam_gx = np.where(yy >= 48.0, 5.0, -5.0).astype(np.float32)
    seam_gr = np.zeros((H, W), dtype=np.float32)
    m_seam = marussi_curvature_eigensystem(seam_gx, seam_gr, valid, sigma_deriv=1.2)
    seam_row = (np.abs(yy - 48.0) <= 1.0) & (xx > 20) & (xx < 76)
    away = (np.abs(yy - 20.0) <= 2.0) & (xx > 20) & (xx < 76)
    assert float(m_seam["curl_clean"][seam_row].mean()) < 0.45
    assert float(m_seam["curl_clean"][away].mean()) > 0.95


def test_baranov_pseudogravity_and_peclet_spin2_invariance():
    H, W = 96, 96
    yy, xx = np.indices((H, W), dtype=np.float32)
    valid = np.ones((H, W), dtype=bool)

    # Gravity N-S fault step at x=48, magnetic E-W dike step at y=48 -> orthogonal cross-product peak
    gz = np.tanh((xx - 48.0) / 2.5)
    gx = ndi.gaussian_filter(gz, sigma=1.0, order=(0, 1))
    gr = ndi.gaussian_filter(gz, sigma=1.0, order=(1, 0))
    rtp = 50.0 * np.tanh((yy - 48.0) / 2.5)

    cross_dec, hydro_demag, _ = baranov_pseudogravity_decoupling(rtp, gx, gr, valid)
    inter = (np.abs(xx - 48.0) <= 3.0) & (np.abs(yy - 48.0) <= 3.0)
    corner = (xx < 20) & (yy < 20)
    assert float(cross_dec[inter].mean()) > float(cross_dec[corner].mean()) * 5.0

    # N-S fault strike => theta = pi/2 => c2 = cos(pi) = -1, s2 = 0
    thermal_across = np.tanh((xx - 48.0) / 2.5)  # gradient along x (across N-S strike)
    thermal_along = np.tanh((yy - 48.0) / 2.5)   # gradient along y (along N-S strike)
    c2 = np.full((H, W), -1.0, dtype=np.float32)
    s2 = np.zeros((H, W), dtype=np.float32)

    b_across = peclet_across_strike_barrier(thermal_across, c2, s2, valid, sigma_grad=1.5)
    b_along = peclet_across_strike_barrier(thermal_along, c2, s2, valid, sigma_grad=1.5)
    zone = (np.abs(xx - 48.0) <= 3.0) & (np.abs(yy - 48.0) <= 10.0)
    zone_y = (np.abs(yy - 48.0) <= 3.0) & (np.abs(xx - 48.0) <= 10.0)
    assert float(b_across[zone].mean()) > float(b_along[zone_y].mean()) * 5.0


def test_comonotonic_tube_self_credit_theorems_and_mc_oracle():
    rng = np.random.default_rng(42)
    H, W = 24, 24

    # 1. Exact deterministic identity on binary {0, 1} grid
    g_bin = (rng.random((H, W)) < 0.08).astype(np.float32)
    th = rng.uniform(0.0, np.pi, size=(H, W)).astype(np.float32)
    c2 = np.cos(2.0 * th).astype(np.float32)
    s2 = np.sin(2.0 * th).astype(np.float32)

    ks_bin = comonotonic_tube_self_credit(g_bin, c2, s2)
    ks_indep_bin = exact_six_ring_self_credit(g_bin)
    np.testing.assert_allclose(ks_bin, ks_indep_bin, rtol=1e-6, atol=1e-6)

    # 2. Frechet-Hoeffding bounds: p <= ks_tube <= ks_indep <= 1 everywhere
    p_soft = rng.uniform(0.0, 0.35, size=(H, W)).astype(np.float32)
    ks_tube = comonotonic_tube_self_credit(p_soft, c2, s2)
    ks_indep = exact_six_ring_self_credit(p_soft)
    assert np.all(ks_tube >= p_soft - 1e-6)
    assert np.all(ks_tube <= ks_indep + 1e-5)
    assert np.all((ks_tube >= 0.0) & (ks_tube <= 1.0))

    # 3. Headless spin-2 gauge invariance (theta -> theta + pi leaves (c2, s2) and tube credit invariant)
    th_flip = th + np.float32(np.pi)
    ks_flip = comonotonic_tube_self_credit(
        p_soft, np.cos(2.0 * th_flip).astype(np.float32), np.sin(2.0 * th_flip).astype(np.float32)
    )
    np.testing.assert_allclose(ks_tube, ks_flip, rtol=1e-6, atol=1e-6)

    # 4. Exact agreement with 150,000-draw 3-strand Monte Carlo simulation at interior pixel (12, 12)
    y0, x0 = 12, 12
    theta0 = 0.5 * float(np.arctan2(s2[y0, x0], c2[y0, x0]))
    d_perp = -OFF_DX.astype(np.float64) * np.sin(theta0) + OFF_DY.astype(np.float64) * np.cos(theta0)
    p_nb = np.array([float(p_soft[y0 + dy, x0 + dx]) for dy, dx in zip(OFF_DY, OFF_DX)])
    u_neg = rng.random(150_000)
    u_mid = rng.random(150_000)
    u_pos = rng.random(150_000)
    u_mat = np.where(
        d_perp[None, :] < -1.05,
        u_neg[:, None],
        np.where(np.abs(d_perp[None, :]) <= 1.05, u_mid[:, None], u_pos[:, None]),
    )
    hits = (u_mat < p_nb[None, :]).astype(np.float64) * OFF_K[None, :]
    mc_mean = float(hits.max(axis=1).mean())
    assert abs(float(ks_tube[y0, x0]) - mc_mean) < 3.5e-3


def test_comonotonic_dcelf_spacing_budget_and_determinism():
    rng = np.random.default_rng(7)
    H, W = 64, 64
    surf = rng.uniform(0.001, 0.25, size=(H, W)).astype(np.float32)
    valid = np.ones((H, W), dtype=bool)
    valid[:3, :] = False
    known = np.zeros((H, W), dtype=bool)
    known[30:33, 10:50] = True
    dcat = ndi.distance_transform_edt(~known)
    allowed = valid & (dcat > 3.0)
    c2 = np.ones((H, W), dtype=np.float32)
    s2 = np.zeros((H, W), dtype=np.float32)

    a1 = comonotonic_dcelf_allocate_dots(
        surf, allowed, c2_strike=c2, s2_strike=s2, known_faults=known, valid=valid, budget=45, min_spacing_px=2.8
    )
    a2 = comonotonic_dcelf_allocate_dots(
        surf, allowed, c2_strike=c2, s2_strike=s2, known_faults=known, valid=valid, budget=45, min_spacing_px=2.8
    )
    assert np.array_equal(a1.dots, a2.dots)
    assert a1.n_dots == 45
    assert not np.any(a1.dots & ~allowed)
    assert not np.any(a1.dots & known)

    pts = np.column_stack(np.nonzero(a1.dots))
    tree = cKDTree(pts)
    dists, _ = tree.query(pts, k=2)
    assert float(dists[:, 1].min()) >= 2.8 - 1e-6


def test_h86m_pfte_serialized_artifact_run_card_and_site_banner():
    import json
    import zipfile
    import rasterio

    root = Path(__file__).resolve().parents[1]
    card_path = root / "docs/evidence/h86m-pfte-run-card.json"
    assert card_path.is_file()
    card = json.loads(card_path.read_text(encoding="utf-8"))

    assert card["lane_id"] == "H86M-PFTE"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["experiments_run"] == 3
    assert card["submission_slots_used"] == 0
    assert 1 <= card["note_chars"] <= 140
    assert card["note_chars"] == len(card["note"])

    # Verify E1 Rule 1 stop provenance & emitted E2 binding
    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["emitted_arm"] == "E2_pfte_blind_comonotonic_dcelf"
    assert "0.704069" in h["e1_rule1_disqualification"]
    assert h["e1_kinematic_arm"]["dti"] > 0.13
    assert 0.05 < h["candidate"]["dti"] < 0.10

    # Verify SGMC-PROXY-DTI beats H33 & E3 with 95% CIs strictly > 0
    sg = card["sgmc_off_catalogue_diagnostic"]
    assert sg["scores"]["E2_pfte_blind_comonotonic_dcelf"]["dti"] > 0.120
    assert sg["paired_differences_vs_candidate"]["H33_GEMSDOE32_as_is"]["ci95"][0] > 0.0
    assert sg["paired_differences_vs_candidate"]["E3_unstripped_scalar_indep_ablation"]["ci95"][0] > 0.0
    assert sg["paired_differences_vs_candidate"]["H86J_MCSP_37654_as_is"]["ci95"][0] > 0.0
    assert sg["paired_differences_vs_candidate"]["H86L_FMC_37654_as_is"]["ci95"][0] > 0.0

    # Verify leakage canary & discrete <=90k registry uniqueness
    assert card["leakage_canary"]["all_passed"] is True
    assert card["leakage_canary"]["max_discriminative_auc"] <= 0.90
    reg = card["correlation_overlap_vs_registry"]
    assert reg["pre_placement_surface"]["worst_spearman_full_footprint"] <= 0.90
    assert reg["full_registry_informative_dot_field_audit"]["discrete_le_90k_firings_over_0p70"] == 0
    assert reg["full_registry_informative_dot_field_audit"]["worst_discrete_le_90k_overlap_3px"] <= 0.70

    # Verify GeoTIFF bytes, [0, 1] range, CRS, shape, and ZIP bundle
    tif_path = root / card["submission_file"]
    zip_path = root / card["zip_file"]
    assert tif_path.is_file() and zip_path.is_file()
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        assert str(src.crs) == "EPSG:32611"
        assert arr.shape == (3730, 3292)
        assert np.isfinite(arr).all()
        assert float(arr.min()) == 0.0
        assert float(arr.max()) == 1.0
        assert int((arr > 0).sum()) == 37654
    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]

    # Verify top-of-page Pages banner renders H86M-PFTE clearly as DO NOT SUBMIT
    index_html = (root / "docs/index.html").read_text(encoding="utf-8")
    assert 'id="h86m-pfte-banner"' in index_html
    assert card["raster_sha256"] in index_html

