"""Unit and protocol-integrity tests for Lane H86I-RKSC."""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems86_rksc.features import (  # noqa: E402
    ARM_NAMES,
    FEATURE_NAMES,
    compose_rksc_arms,
    compute_rksc_arrays,
    verify_band_contract,
)
from scripts import run_h86i_rksc  # noqa: E402


def test_band_contract_matches_io_bands():
    verify_band_contract()


def test_rksc_detects_piedmont_scarp_and_kth_step_over_flank():
    h, w = 96, 96
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    fp = np.ones((h, w), dtype=bool)
    fp[:4, :] = False
    fp[-4:, :] = False
    fp[:, :4] = False
    fp[:, -4:] = False

    # N-S piedmont scarp centered at x0 = 48 with profile-curvature inflection
    u = (xx - 48.0) / 3.5
    det_elev = (-25.0 * np.tanh(u)).astype(np.float32)
    slope19 = (8.0 / (np.cosh(u) ** 2) + 2.0).astype(np.float32)
    conduit = np.exp(-0.5 * ((xx - 48.0) / 2.2) ** 2).astype(np.float32)

    # Juxtaposed potassic step across x0 = 48 + metasomatic enrichment along conduit
    rad_k = (120.0 + 35.0 * np.tanh(u) + 45.0 * conduit).astype(np.float32)
    rad_th = (100.0 + 10.0 * np.sin(yy / 12.0)).astype(np.float32)
    rad_u = (100.0 + 15.0 * conduit).astype(np.float32)
    rad_tc = (200.0 + 50.0 * np.tanh(u) + 40.0 * conduit).astype(np.float32)

    topo_curv = (40.0 + 180.0 * conduit).astype(np.float32)
    # Non-Lahontan piedmont elevation (u8 ~ 140)
    topo_dem = np.full((h, w), 140.0, dtype=np.float32)

    ones = np.ones((h, w), dtype=np.float32)
    deq = (50.0 * (1.0 - 0.7 * conduit)).astype(np.float32)
    ieq = (10.0 + 30.0 * conduit).astype(np.float32)
    cond = (5.0 + 8.0 * np.tanh(u)).astype(np.float32)

    planes = compute_rksc_arrays(
        b4_geod_2ndinv=ones + conduit,
        b6_rad_tc=rad_tc,
        b7_geod_shearrate=ones + conduit,
        b8_geod_dilaterate=ones + conduit,
        b10_deq=deq,
        b12_det_elev=det_elev,
        b16_ieq=ieq,
        b17_cond_surf=cond,
        b19_det_elev_slope=slope19,
        rad_k_u8=rad_k,
        rad_th_u8=rad_th,
        rad_u_u8=rad_u,
        topo10_curv_u8=topo_curv,
        topo10_dem_u8=topo_dem,
        footprint=fp,
    )
    arms = compose_rksc_arms(planes, fp)
    core_slice = (slice(20, 76), slice(46, 51))
    flank_slice = (slice(20, 76), slice(15, 28))

    assert float(arms["E1_rksc_full"][core_slice].mean()) > float(
        arms["E1_rksc_full"][flank_slice].mean()
    ) + 0.25
    assert float(arms["E1_rksc_full"][core_slice].mean()) > float(
        arms["E3_rksc_lahontan_uncorrected_control"][core_slice].mean()
    )


def test_rksc_nodata_sentinel_immunity_and_bounds():
    h, w = 64, 64
    yy, xx = np.mgrid[0:h, 0:w]
    fp = ((yy - 32) ** 2 + (xx - 32) ** 2) <= 22**2
    rng = np.random.default_rng(869)

    def mk() -> np.ndarray:
        a = rng.normal(50.0, 15.0, size=(h, w)).astype(np.float32)
        a[~fp] = np.float32(-3.4028235e38)
        a[0, 0] = np.nan
        return a

    planes = compute_rksc_arrays(
        b4_geod_2ndinv=mk(),
        b6_rad_tc=np.abs(mk()),
        b7_geod_shearrate=mk(),
        b8_geod_dilaterate=mk(),
        b10_deq=np.abs(mk()),
        b12_det_elev=mk(),
        b16_ieq=np.abs(mk()),
        b17_cond_surf=mk(),
        b19_det_elev_slope=np.abs(mk()),
        rad_k_u8=np.abs(mk()),
        rad_th_u8=np.abs(mk()),
        rad_u_u8=np.abs(mk()),
        topo10_curv_u8=np.abs(mk()),
        topo10_dem_u8=np.abs(mk()),
        footprint=fp,
    )
    assert set(planes) == set(FEATURE_NAMES)
    arms = compose_rksc_arms(planes, fp)
    assert set(arms) == set(ARM_NAMES)
    for name, arr in {**planes, **arms}.items():
        assert arr.dtype == np.float32, name
        assert np.isfinite(arr).all(), name
        assert np.all(arr[~fp] == 0.0), name
        assert float(arr[fp].min()) >= 0.0 and float(arr[fp].max()) <= 1.0, name


def test_rksc_feature_module_never_references_catalogue():
    src_text = (ROOT / "src/gems86_rksc/features.py").read_text()
    tree = ast.parse(src_text)
    doc_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                doc_nodes.add(first.value)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node not in doc_nodes:
            assert "existing_faults" not in node.value
            assert "catalogue" not in node.value
            assert "labels.tif" not in node.value
        if isinstance(node, ast.Attribute):
            assert node.attr != "catalogue"


def test_rksc_preregistration_run_card_and_artifact_contracts(tmp_path):
    prereg = run_h86i_rksc.require_preregistration()
    assert prereg["status"] == "frozen_before_implementation"
    assert prereg["candidate_hypotheses_count"] == 4
    assert len(prereg["experiment_arms"]) == 3

    prereg_doc = json.loads((ROOT / "research/H86I_RKSC_PREREGISTRATION.json").read_text())
    h4 = prereg_doc["candidate_hypotheses"][3]
    assert h4["id"] == "H86I-4_INSAR"
    assert h4["selected_for_validation"] is False
    assert h4["official_data_obtainability"].startswith("NOT_VIABLE_IN_SANDBOX_YET")

    bad_json = tmp_path / "bad.json"
    bad_md = tmp_path / "bad.md"
    bad_md.write_text("# test\n")
    bad_json.write_text(json.dumps(dict(prereg_doc, status="retrospective")))
    with pytest.raises(ValueError, match="frozen_before_implementation"):
        run_h86i_rksc.require_preregistration(bad_json, bad_md)

    card = json.loads((ROOT / "docs/evidence/h86i-rksc-run-card.json").read_text())
    assert card["lane"] == "H86I-RKSC"
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["safe_to_submit"] is False
    assert card["submission_ready"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 3
    assert card["note_chars"] == len(card["note"]) <= 140
    assert card["leakage_canary"]["all_pass"] is True
    assert card["leakage_canary"]["worst_discriminative_auc"] <= 0.90
    assert card["band_physics_qc"]["corr_band6_tc_vs_geodawn_b4_TC"] >= 0.99

    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI"
    assert h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321
    assert h["all_arms"]["E1_rksc_full"]["dti"] > h["all_arms"]["E2_rksc_rad_scarp_only"]["dti"]
    assert h["all_arms"]["E2_rksc_rad_scarp_only"]["dti"] > h["all_arms"]["E3_rksc_lahontan_uncorrected_control"]["dti"]

    reg = card["correlation_overlap_vs_registry"]
    assert reg["surface_preplacement"]["rho_firings"] == 0
    assert reg["surface_preplacement"]["worst_spearman_full_footprint"] <= 0.90
    assert reg["final_dots"]["worst_spearman_full_footprint"] <= 0.90
    assert reg["final_dots"]["byte_unique_among_checked"] is True
    assert reg["final_dots"]["pixel_unique_among_checked"] is True
    assert reg["pa86_02"]["gate_pass"] is False

    tif_path = ROOT / card["submission_file"]
    zip_path = ROOT / card["submission_zip"]
    rec_path = ROOT / card["submission_receipt"]
    assert tif_path.is_file() and zip_path.is_file() and rec_path.is_file()
    assert hashlib.file_digest(tif_path.open("rb"), "sha256").hexdigest() == card["raster_sha256"]
