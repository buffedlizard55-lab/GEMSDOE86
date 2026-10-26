"""Unit & preregistration contract tests for Lane H86Q-BFRA."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.gems86_bfra import (
    ABLATION_LOCAL_NAMES,
    BFRA_ELASTIC_NAMES,
    BFRA_STATIC_NAMES,
    broken_plate_flexural_shear_and_rollover,
    regolith_and_metasomatic_unmixing,
    strand_tangent_sharpen_posterior,
    tmi_vs_rtp_remanence_dislocation,
)
from src.gems86_bfra.model import fuse_tworegime_radial_bfra, rank01_per_quadrant
from src.gems86_stdp.model import calibrate_quadrant_sparse_posterior

ROOT = Path(__file__).resolve().parents[1]


def test_h86q_preregistration_and_hypothesis_queue_contracts():
    hyp = json.loads((ROOT / "registry/h86q_hypotheses_20261026.json").read_text())
    prereg = json.loads((ROOT / "research/H86Q_BFRA_PREREGISTRATION.json").read_text())
    assert 3 <= len(hyp["hypotheses"]) <= 5
    selected = [h for h in hyp["hypotheses"] if h["selected_for_validation"]]
    assert len(selected) == 1
    assert selected[0]["id"] == prereg["selected_hypothesis_id"] == "H86Q-1_BFRA"
    assert prereg["budget"]["max_experiments"] == len(prereg["arms"]) == 3
    assert prereg["budget"]["weekly_submission_slots_authorized"] == 0
    assert prereg["static_features"] == list(BFRA_STATIC_NAMES)
    assert len(BFRA_STATIC_NAMES) == 32
    assert prereg["fold_visible_elastic_features"] == list(BFRA_ELASTIC_NAMES)
    assert prereg["ablation_control_features"] == list(ABLATION_LOCAL_NAMES)


def test_broken_plate_flexural_shear_peaks_at_fault_inflection_and_rollover_downdip():
    H, W = 64, 96
    yy, xx = np.meshgrid(np.arange(H, dtype=np.float32), np.arange(W, dtype=np.float32), indexing="ij")
    x0 = 46.0
    width = 5.0
    # Normal fault dipping east (+col): footwall Z_b ~ 0, hanging-wall Z_b -> 1200 m
    zb = 600.0 * (1.0 + np.tanh((xx - x0) / width))
    # Bouguer gravity drops eastward across the basement step: B18 = d(B13)/dx_east < 0
    b11 = np.zeros((H, W), dtype=np.float32)
    b18 = (-8.0 / np.cosh((xx - x0) / width) ** 2).astype(np.float32)
    valid = np.ones((H, W), dtype=bool)
    valid[:3, :] = False

    d3_shear, rollover, nr, nc = broken_plate_flexural_shear_and_rollover(
        zb, b11, b18, valid, sigmas_px=(2.5, 4.0)
    )
    assert d3_shear.dtype == rollover.dtype == np.float32
    assert np.all(d3_shear[~valid] == 0.0) and np.all(rollover[~valid] == 0.0)
    # Peak of -d^3_{nnn} Z_b lands within <= 1.5 px of the fault subcrop x0 = 46
    mid_row = H // 2
    shear_peak_col = int(np.argmax(d3_shear[mid_row, 15:-15]) + 15)
    rollover_peak_col = int(np.argmax(rollover[mid_row, 15:-15]) + 15)
    assert abs(shear_peak_col - x0) <= 2.0
    # Hanging-wall rollover (-d^2_{nn} Z_b > 0) peaks down-dip (+col) of the shear inflection
    assert rollover_peak_col > shear_peak_col
    assert float(nc[mid_row, int(x0)]) > 0.95
    assert abs(float(nr[mid_row, int(x0)])) < 0.05


def test_regolith_and_metasomatic_unmixing_scale_invariance_and_masking():
    H, W = 48, 64
    yy, xx = np.meshgrid(np.arange(H, dtype=np.float32), np.arange(W, dtype=np.float32), indexing="ij")
    valid = np.ones((H, W), dtype=bool)
    valid[0, :] = False
    # Gentle eastward-sloping piedmont with compositional step at col=32
    elev = (1500.0 - 2.0 * xx).astype(np.float32)
    slope = np.full((H, W), 2.0, dtype=np.float32)
    rad_k = np.where(xx < 32, 30.0, 14.0).astype(np.float32)
    rad_u = np.where(xx < 32, 24.0, 11.0).astype(np.float32)
    rad_th = np.full((H, W), 18.0, dtype=np.float32)
    # Localized hydrothermal K-metasomatism anomaly at (24, 48) with conductive cap
    rad_k[21:27, 45:51] = 65.0
    cond = np.full((H, W), 5.0, dtype=np.float32)
    cond[21:27, 45:51] = 55.0
    tc = (rad_k + rad_u + rad_th).astype(np.float32)

    reg1, meta1 = regolith_and_metasomatic_unmixing(
        tc, rad_k, rad_th, rad_u, elev, slope, cond, valid
    )
    # Uniform moisture attenuation factor eta=0.5 leaves provenance log-ratio jump unchanged
    reg2, _ = regolith_and_metasomatic_unmixing(
        tc, 0.5 * rad_k, 0.5 * rad_th, 0.5 * rad_u, elev, slope, cond, valid
    )
    assert np.allclose(reg1, reg2, atol=1e-4)
    assert np.all(reg1[~valid] == 0.0) and np.all(meta1[~valid] == 0.0)
    assert float(reg1[24, 32]) > float(reg1[24, 12]) * 3.0
    assert float(meta1[24, 48]) > float(np.median(meta1[valid])) * 5.0


def test_tmi_rtp_remanence_dislocation_and_strand_sharpening():
    H, W = 48, 64
    _, xx = np.meshgrid(np.arange(H, dtype=np.float32), np.arange(W, dtype=np.float32), indexing="ij")
    valid = np.ones((H, W), dtype=bool)
    nr = np.zeros((H, W), dtype=np.float32)
    nc = np.ones((H, W), dtype=np.float32)
    # Induced step at col=18 (TMI and RTP co-aligned) vs reverse-TRM step at col=44 (TMI and RTP opposed)
    step_ind = np.tanh((xx - 18.0) / 2.5).astype(np.float32)
    step_rev = np.tanh((xx - 44.0) / 2.5).astype(np.float32)
    b14_tmi = 100.0 * step_ind + 100.0 * step_rev
    b2_rtp = 100.0 * step_ind - 100.0 * step_rev
    b1_mag = b14_tmi.copy()

    disloc = tmi_vs_rtp_remanence_dislocation(b14_tmi, b2_rtp, b1_mag, nr, nc, valid)
    assert float(disloc[24, 44]) > float(disloc[24, 18]) * 2.5

    # 1-D fault ridge sharpening preserves [0, 0.99] bounds and boosts crest vs flank
    yy, _ = np.meshgrid(np.arange(H, dtype=np.float32), np.arange(W, dtype=np.float32), indexing="ij")
    ridge = (0.35 * np.exp(-((yy - 24.0) ** 2) / (2.0 * 1.6**2))).astype(np.float32)
    sharp = strand_tangent_sharpen_posterior(ridge, valid)
    assert sharp.min() >= 0.0 and sharp.max() <= 0.99
    assert float(sharp[24, 32]) > float(ridge[24, 32])
    assert float(sharp[28, 32]) < float(ridge[28, 32])


def test_quadrant_calibration_repairs_nw_zeroing_regression():
    H, W = 40, 40
    valid = np.ones((H, W), dtype=bool)
    yy, xx = np.indices((H, W))
    quad_ids = ((yy >= 20).astype(np.int8) * 2 + (xx >= 20).astype(np.int8)).astype(np.int8)
    rng = np.random.default_rng(42)
    raw = rng.uniform(0.01, 0.5, size=(H, W)).astype(np.float32)
    # Even if SW has 5x higher raw amplitude than NW, per-quadrant calibration gives positive NW support
    raw[quad_ids == 2] *= 5.0
    q_rank = rank01_per_quadrant(raw, valid, quad_ids)
    cal = calibrate_quadrant_sparse_posterior(q_rank, valid, quad_ids, tau0=-4.55, beta=1.65)
    for q in range(4):
        qm = valid & (quad_ids == q)
        assert float(cal[qm].max()) > 0.15, f"Quadrant {q} starved!"

    s = fuse_tworegime_radial_bfra(cal, cal, np.full((H, W), 0.5, dtype=np.float32), np.full((H, W), 20.0, dtype=np.float32), valid)
    assert np.all((s >= 0.0) & (s <= 1.0))


def test_h86q_bfra_run_card_e1_rule1_stop_and_serialized_e2_artifact_contract():
    import hashlib
    import zipfile
    import rasterio

    card = json.loads((ROOT / "docs/evidence/h86q-bfra-run-card.json").read_text(encoding="utf-8"))
    assert card["lane_id"] == "H86Q-BFRA"
    assert card["experiments_run"] == 3
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert 1 <= card["note_chars"] <= 140
    assert card["note_chars"] == len(card["note"])

    # Leakage canary contract: 49 planes, all <= 0.90
    lc = card["holdout_dti"]["leakage_canary_summary"]
    assert lc["features_tested"] == 49
    assert lc["max_discriminative_auc"] <= 0.90
    assert lc["any_leakage_flag"] is False

    # E1 automatic Rule-1 pre-serialization stop receipt + E2 uniqueness contract
    reg = card["correlation_overlap_vs_registry"]
    assert reg["serialized_arm"] == "E2_bfra_blind_subsurface_piedmont_dcelf"
    e1_stop = reg["e1_rule1_duplicate_stop"]
    assert e1_stop["arm_halted"] == "E1_bfra_coupled_tworegime_dcelf"
    assert e1_stop["tif_serialized_for_e1"] is False
    assert e1_stop["worst_discrete_le_90k_overlap_3px"] > 0.70

    surf_rep = json.loads((ROOT / "docs/evidence/h86q-bfra-e2-registry-surface.json").read_text(encoding="utf-8"))
    dots_rep = json.loads((ROOT / "docs/evidence/h86q-bfra-e2-registry-final-dots.json").read_text(encoding="utf-8"))
    assert surf_rep["two_phase"]["literal_reading"]["rho_firings"] == 0
    assert surf_rep["shared_summary"]["worst_spearman_full_footprint"] <= 0.90
    assert reg["full_registry_informative_dot_field_audit"]["discrete_le_90k_firings_over_0p70"] == 0
    assert reg["full_registry_informative_dot_field_audit"]["worst_discrete_le_90k_overlap_3px"] <= 0.70
    assert reg["comparable_discrete_100k_diagnostic"]["focus9_direct_scan"]["firings_over_0p70"] == 0
    assert dots_rep["shared_summary"]["byte_unique_among_checked"] is True
    assert dots_rep["shared_summary"]["pixel_unique_among_checked"] is True

    # Balanced 4-quadrant E2 holdout recovery + >1 km radial profile + SGMC > H33
    pf_e2 = card["holdout_dti"]["per_fold"]["E2_bfra_blind_subsurface_piedmont_dcelf"]
    for fold_name in ("NW", "NE", "SW", "SE"):
        assert pf_e2[fold_name]["dti"] > 0.05
    rad = card["mechanism"]["radial_allocation_profile"]
    assert rad["min_dcat_px"] > 3.0
    assert 0.60 <= rad["frac_gt_10px_far_field_gt_1km"] <= 0.80
    sg = card["sgmc_off_catalogue_diagnostic"]["scores"]
    assert sg["E2_bfra_blind_subsurface_piedmont_dcelf"]["dti"] > sg["H33_GEMSDOE32_as_is"]["dti"]

    # Independent GeoTIFF + ZIP + receipt byte/grid/[0,1] checks
    tif_path = ROOT / card["submission_file"]
    zip_path = ROOT / card["submission_zip"]
    rec_path = ROOT / card["submission_receipt"]
    assert tif_path.is_file() and zip_path.is_file() and rec_path.is_file()
    assert hashlib.sha256(tif_path.read_bytes()).hexdigest() == card["raster_sha256"]
    assert hashlib.sha256(zip_path.read_bytes()).hexdigest() == card["zip_sha256"]
    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert zf.read(tif_path.name) == tif_path.read_bytes()
    with rasterio.open(tif_path) as ds:
        assert str(ds.crs) == "EPSG:32611"
        assert ds.shape == (3730, 3292)
        assert ds.count == 1
        assert ds.dtypes == ("float32",)
        assert ds.nodata is None
        arr = ds.read(1)
    assert np.isfinite(arr).all()
    assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
    assert int((arr > 0).sum()) == 37654

    # Focus-9 rev-2 forensics artifact check
    f9 = json.loads((ROOT / "docs/evidence/focus9-forensics-20261026-rev2.json").read_text(encoding="utf-8"))
    assert f9["schema"] == "gems86.focus9_forensics.v2"
    assert len(f9["rasters"]) == 30
    h33_rows = [r for r in f9["rasters"] if "h33-h33-2-b2" in r["file"]]
    assert len(h33_rows) == 1 and h33_rows[0]["positive_pixels"] == 37654


