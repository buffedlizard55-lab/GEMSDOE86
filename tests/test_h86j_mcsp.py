"""Unit, mathematical, and artifact-integrity tests for H86J-MCSP and rate-limit fallbacks."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "src", ROOT / "vendor"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems57.metric import OFF_DX, OFF_DY, OFF_K
from gems86_mcsp.celf import celf_allocate_dots, static_ek_spacing_allocate
from gems86_mcsp.features import (
    MCSP_STATIC_NAMES,
    _hessian_ridge_and_eccentricity,
    _structure_tensor_intersection,
    riesz_monogenic_phase_congruency,
    verify_band_physics_contract,
)
from scripts import restore_protocol_data


def test_band_physics_contract_matches_src_gems86_io():
    contract = verify_band_physics_contract()
    assert len(contract["verified_native_bands"]) == 17
    assert contract["verified_native_bands"]["6"] == "tc"
    assert contract["verified_native_bands"]["11"] == "iso_grav_anom_vg"
    assert contract["verified_native_bands"]["18"] == "iso_grav_anom_hg"
    assert len(MCSP_STATIC_NAMES) == 22


def test_riesz_monogenic_contrast_invariance_and_step_selectivity():
    yy, xx = np.mgrid[0:64, 0:64].astype(np.float32)
    valid = np.ones((64, 64), dtype=bool)
    step_weak = np.tanh((xx - 32.0) / 1.2)
    step_strong = 50.0 * step_weak
    sym_dike = np.exp(-0.5 * ((xx - 32.0) / 2.5) ** 2)

    pc_weak, _, _ = riesz_monogenic_phase_congruency(step_weak, valid)
    pc_strong, _, _ = riesz_monogenic_phase_congruency(step_strong, valid)
    pc_dike, _, _ = riesz_monogenic_phase_congruency(sym_dike, valid)

    assert float(pc_weak[32, 32]) > 0.80
    assert float(np.max(np.abs(pc_weak - pc_strong))) < 1e-4
    assert float(pc_dike[32, 32]) < 0.05


def test_hessian_neck_and_structure_tensor_intersection_discriminate_mimics():
    yy, xx = np.mgrid[0:64, 0:64].astype(np.float32)
    valid = np.ones((64, 64), dtype=bool)
    fault_gouge_line = np.exp(-0.5 * ((xx - 32.0) / 1.8) ** 2)
    equant_playa = np.exp(-0.5 * (((xx - 32.0) ** 2 + (yy - 32.0) ** 2) / (10.0**2)))

    r_line, ecc_line = _hessian_ridge_and_eccentricity(fault_gouge_line, valid, sigma=2.0)
    r_playa, ecc_playa = _hessian_ridge_and_eccentricity(equant_playa, valid, sigma=2.0)
    assert float((r_line * ecc_line)[32, 32]) > 10.0 * float((r_playa * ecc_playa)[32, 32]) + 0.01

    crossed_ridge = np.maximum(
        np.exp(-0.5 * ((xx - 32.0) / 1.8) ** 2),
        np.exp(-0.5 * ((yy - 32.0) / 1.8) ** 2),
    )
    single_ridge = np.exp(-0.5 * ((xx - 32.0) / 1.8) ** 2)
    c_cross = _structure_tensor_intersection(crossed_ridge, valid)
    c_single = _structure_tensor_intersection(single_ridge, valid)
    assert float(c_cross[32, 32]) > 10.0 * float(c_single[32, 32]) + 1e-4


def test_celf_matches_bruteforce_submodular_greedy_and_enforces_spacing():
    rng = np.random.default_rng(861025)
    prob = rng.uniform(0.0, 1.0, (28, 28)).astype(np.float32)
    valid = np.ones((28, 28), dtype=bool)
    known = np.zeros((28, 28), dtype=bool)
    known[0, :] = True
    allowed = valid.copy()
    allowed[:4, :] = False

    res = celf_allocate_dots(
        prob, allowed, known_faults=known, valid=valid, budget=18, min_spacing_px=2.8
    )
    assert res.n_dots == 18
    assert not bool((res.dots & ~allowed).any())

    # Exact brute-force submodular greedy verification using identical OFF_DY/OFF_DX/OFF_K
    p = prob.astype(np.float64).copy()
    p[~valid | known] = 0.0
    best_cov = np.zeros_like(p)
    picked = np.zeros((28, 28), dtype=bool)
    elig = allowed.copy()
    H, W = prob.shape
    offsets = list(zip(OFF_DY.tolist(), OFF_DX.tolist(), OFF_K.tolist()))
    for _ in range(18):
        best_gain = -1.0
        best_rc = None
        for r, c in np.argwhere(elig):
            gain = 0.0
            for dr, dc, kw in offsets:
                rr, cc = int(r) + dr, int(c) + dc
                if 0 <= rr < H and 0 <= cc < W and kw > best_cov[rr, cc]:
                    gain += p[rr, cc] * (kw - best_cov[rr, cc])
            if gain > best_gain + 1e-12:
                best_gain = gain
                best_rc = (int(r), int(c))
        assert best_rc is not None
        br, bc = best_rc
        picked[br, bc] = True
        for dr, dc, kw in offsets:
            rr, cc = br + dr, bc + dc
            if 0 <= rr < H and 0 <= cc < W and kw > best_cov[rr, cc]:
                best_cov[rr, cc] = kw
        for r2 in range(max(0, br - 3), min(H, br + 4)):
            for c2 in range(max(0, bc - 3), min(W, bc + 4)):
                if (r2 - br) ** 2 + (c2 - bc) ** 2 < 2.8**2:
                    elig[r2, c2] = False

    assert np.array_equal(res.dots, picked)
    ek = static_ek_spacing_allocate(
        prob, allowed, known_faults=known, valid=valid, budget=18, min_spacing_px=2.8
    )
    assert int(ek.sum()) == 18


def test_h86j_mcsp_run_card_and_serialized_artifact_invariants():
    card_path = ROOT / "docs/evidence/h86j-mcsp-run-card.json"
    assert card_path.is_file()
    card = json.loads(card_path.read_text(encoding="utf-8"))

    assert card["lane_id"] == "H86J-MCSP"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    assert 1 <= card["note_chars"] == len(card["note"]) <= 140

    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321
    assert h["leakage_canary_summary"]["any_leakage_flag"] is False
    assert h["leakage_canary_summary"]["max_discriminative_auc"] <= 0.90

    sg = card["sgmc_off_catalogue_diagnostic"]
    assert sg["evidence_class"] == "SGMC-PROXY-DTI"
    assert sg["paired_differences_vs_candidate"]["E3_mcsp_amp_staticek_ablation"]["ci95"][0] > 0.0
    assert sg["paired_differences_vs_candidate"]["H86F_EWCS_37654_as_is"]["ci95"][0] > 0.0

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
        arr = ds.read(1)
        assert ds.count == 1
        assert ds.dtypes == ("float32",)
        assert ds.shape == (3730, 3292)
        assert str(ds.crs) == "EPSG:32611"
        assert np.isfinite(arr).all()
        assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
        assert int((arr > 0).sum()) == 37654


def test_rate_limit_fallback_triggers_only_on_api_rate_limit_exceeded(tmp_path):
    raw = b"verified-bytes"
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    rate_err = subprocess.CalledProcessError(
        1, ["gh", "api"], stderr=b"gh: API rate limit exceeded for user ID 1 (HTTP 403)"
    )
    stream = io.BytesIO()
    with (
        patch.object(restore_protocol_data.subprocess, "run", side_effect=rate_err),
        patch.object(restore_protocol_data, "_git_fetch_blob", return_value=raw) as fb,
    ):
        restore_protocol_data.write_blob("owner/repo", blob, stream)
    assert fb.call_count == 1
    assert stream.getvalue() == raw

    non_rate_err = subprocess.CalledProcessError(1, ["gh", "api"], stderr=b"HTTP 500")
    with patch.object(restore_protocol_data.subprocess, "run", side_effect=non_rate_err):
        try:
            restore_protocol_data.write_blob("owner/repo", blob, io.BytesIO())
            raise AssertionError("Expected CalledProcessError")
        except subprocess.CalledProcessError:
            pass
