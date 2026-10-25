"""Unit and receipt verification tests for the H86I-HVFD lane."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from src.gems86_hvfd import features as F

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_h86i_preregistration_complete_and_frozen():
    prereg_json = ROOT / "research/H86I_HVFD_PREREGISTRATION.json"
    prereg_md = ROOT / "research/H86I_HVFD_PREREGISTRATION.md"
    assert prereg_json.is_file()
    assert prereg_md.is_file()
    prereg = json.loads(prereg_json.read_text(encoding="utf-8"))
    assert prereg["lane"] == "H86I-HVFD"
    assert prereg["budget"]["max_arms"] == 3
    assert prereg["budget"]["max_hours"] <= 2
    hyps = prereg["ranked_hypotheses"]
    assert len(hyps) == 4
    selected = [h for h in hyps if h["selected_for_validation"]]
    assert len(selected) == 1
    assert selected[0]["id"] == "H86I-1_HVFD"
    for h in hyps:
        for key in (
            "rank",
            "id",
            "name",
            "layers",
            "transform",
            "non_fault_mimic",
            "uncatalogued_rationale",
            "novelty",
            "cost",
            "official_data",
        ):
            assert h.get(key), f"Missing {key} in {h.get('id')}"


def test_hvfd_rank01_zero_tie_and_monotonicity():
    fp = np.array([[True, True, True, False], [True, True, True, True]], dtype=bool)
    arr = np.array([[0.0, 0.0, 2.5, 99.0], [0.0, 1.0, 5.0, 0.0]], dtype=np.float32)
    r = F.rank01(arr, fp)
    assert r.dtype == np.float32
    assert r[0, 3] == 0.0  # outside footprint
    # All tied minimum (0.0) cells inside footprint must map to 0.0 (no row-major tie ramp!)
    assert r[0, 0] == 0.0
    assert r[0, 1] == 0.0
    assert r[1, 0] == 0.0
    assert r[1, 3] == 0.0
    assert 0.0 < r[1, 1] < r[0, 2] < r[1, 2] <= 1.0


def test_hvfd_banned_csv_column_guard(tmp_path):
    assert F.BANNED_CSV_COLUMNS == {"dist_known_fault_px"}
    csv_path = tmp_path / "gdr_wellspring_in_footprint.csv"
    csv_path.write_text(
        "row,col,temp_c,geothermquartz_c,geothermchalc_c,dist_known_fault_px\n"
        "5,5,55.0,120.0,110.0,0.0\n",
        encoding="utf-8",
    )
    fp = np.ones((12, 12), dtype=bool)
    dem = np.ones((12, 12), dtype=np.float32) * 1500.0
    out = F._parse_wellspring_upslope(csv_path, (12, 12), fp, dem)
    assert out.shape == (12, 12)
    assert float(out.max()) > 0.0
    assert "dist_known_fault_px" not in F.ACCESSED_CSV_COLUMNS[csv_path.name]


def test_hvfd_disc_thin_prefix_respects_radius_and_collar():
    yy, xx = np.mgrid[0:20, 0:20]
    surface = ((yy + xx + 1) / 40.0).astype(np.float32)
    allowed = np.ones((20, 20), dtype=bool)
    allowed[:3, :] = False
    dots = F.disc_thin_prefix(surface, allowed, budget=15, radius_px=2.8)
    rows, cols = np.nonzero(dots)
    assert int(dots.sum()) == len(rows) == len(cols) <= 15
    assert int(dots.sum()) > 0
    assert not np.any(dots[:3, :])
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            dist = float(np.hypot(rows[i] - rows[j], cols[i] - cols[j]))
            assert dist > 2.8 - 1e-6


def test_hvfd_compose_surface_bounds_and_monotonicity():
    fp = np.ones((8, 8), dtype=bool)
    fp[0, :] = False
    p_blind = np.full((8, 8), 0.4, dtype=np.float32)
    v_vent = np.full((8, 8), 0.5, dtype=np.float32)
    m_trap_zero = np.zeros((8, 8), dtype=np.float32)
    m_trap_high = np.full((8, 8), 0.7, dtype=np.float32)
    s_distal = F.compose_hvfd_surface(p_blind, v_vent, m_trap_zero, fp)
    s_full = F.compose_hvfd_surface(p_blind, v_vent, m_trap_high, fp)
    assert s_distal.shape == (8, 8)
    assert s_full.shape == (8, 8)
    assert np.all(s_distal[0, :] == 0.0)
    assert np.all(s_full[0, :] == 0.0)
    assert np.all(np.isfinite(s_distal)) and np.all(np.isfinite(s_full))
    assert float(s_distal.min()) >= 0.0 and float(s_distal.max()) <= 1.0
    assert float(s_full.min()) >= 0.0 and float(s_full.max()) <= 1.0
    assert float(s_full[1:, :].mean()) > float(s_distal[1:, :].mean())


def test_h86i_hvfd_run_card_and_serialized_artifacts():
    card_path = ROOT / "docs/evidence/h86i-hvfd-run-card.json"
    surf_path = ROOT / "docs/evidence/h86i-hvfd-registry-surface.json"
    dots_path = ROOT / "docs/evidence/h86i-hvfd-registry-final-dots.json"
    pa_path = ROOT / "docs/evidence/h86i-hvfd-chance-overlap.json"
    for p in (card_path, surf_path, dots_path, pa_path):
        assert p.is_file(), f"Missing {p}"

    card = json.loads(card_path.read_text(encoding="utf-8"))
    assert card["lane"] == "H86I-HVFD"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["safe_to_download_for_audit"] is True
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    assert 1 <= len(card["note"]) <= 140

    tif_path = ROOT / card["submission_file"]
    zip_path = ROOT / card["zip_file"]
    rcpt_path = ROOT / card["receipt_file"]
    assert tif_path.is_file() and zip_path.is_file() and rcpt_path.is_file()
    assert _sha256(tif_path) == card["raster_sha256"] == "0325442434733ee10a9d77200b17db86f00d6195d373afeca43d673435216b58"
    assert _sha256(zip_path) == card["zip_sha256"] == "3f9fbcc6bf2ca93ef0846e9b47aec78bc89cd3096476800d5ed44a6327610616"
    assert card["validator_output"]["all_checks_passed"] is True
    assert card["validator_output"]["positive_pixels"] == 37654

    # Holdout DTI invariants
    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321
    scores = h["pooled_summary"]["scores"]
    e1 = scores["E1_hvfd_blind_vent_conduit"]["dti"]
    e2 = scores["E2_hvfd_foldfair_vent_relay_noisyor"]["dti"]
    e3 = scores["E3_hvfd_collar_ablation_44090"]["dti"]
    r0 = scores["R0_G25_foldfair_collar"]["dti"]
    assert e1 > 0.045  # beats all prior zero-catalogue algebraic lanes (~0.029-0.033)
    assert e3 > e2 > r0 > e1
    for arm_score in scores.values():
        assert arm_score["evidence_class"] == "HOLDOUT-DTI"
        assert len(arm_score["ci95"]) == 2
        assert arm_score["ci95"][0] < arm_score["dti"] < arm_score["ci95"][1]

    # Leakage canary invariants
    can = card["leakage_canary"]
    assert can["any_flag"] is False
    assert can["max_discriminative_auc"] <= 0.90
    assert len(can["features"]) == 18

    # Registry reports use relative candidate paths and record 0 rho firings
    surf = json.loads(surf_path.read_text(encoding="utf-8"))
    dots = json.loads(dots_path.read_text(encoding="utf-8"))
    assert not surf["candidate"].startswith("/")
    assert not dots["candidate"].startswith("/")
    assert surf["two_phase"]["literal_reading"]["rho_firings"] == 0
    assert dots["two_phase"]["literal_reading"]["rho_firings"] == 0
    assert surf["shared_summary"]["worst_spearman_full_footprint"] <= 0.90
    assert dots["shared_summary"]["worst_spearman_full_footprint"] <= 0.90
    assert dots["shared_summary"]["byte_unique_among_checked"] is True
    assert dots["shared_summary"]["pixel_unique_among_checked"] is True
    sparse_overlaps = [
        r["my_dots_within_3px_of_theirs"]
        for r in dots["comparison_rows"]
        if r.get("their_dots") is not None and r["their_dots"] <= 100000
    ]
    assert len(sparse_overlaps) >= 460
    assert max(sparse_overlaps) < 0.70
