"""Unit and release-invariant tests for the H86J-TVHS geological lane."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio
from rasterio.transform import Affine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems86_tvhs.features import (  # noqa: E402
    ALL_STATIC_NAMES,
    BY_NAME,
    COUPLED_KINEMATIC_NAMES,
    NATIVE_ABLATION_NAMES,
    TVHS_NOVEL_STATIC_NAMES,
    compute_exposure_propensity_weights,
    compute_faulds_hinz_kinematic_fields,
    compute_ggt_invariants,
)


def test_pedersen_rasmussen_ggt_separates_2d_sheet_step_from_circular_3d_plug():
    """Pedersen-Rasmussen (1990) D_2D must be ~1 on a 2-D step and ~0 on a 3-D plug."""
    yy, xx = np.mgrid[-40:41, -40:41].astype(np.float32)
    fp = np.ones_like(xx, dtype=bool)

    # 1) Infinite N-S 2-D normal-fault gravity step: g(x) = tanh(x / 5) => dg/dx_east = B18 > 0, B11 = 0
    g_step = np.tanh(xx / 5.0)
    b18_step = np.gradient(g_step, axis=1).astype(np.float32)
    b11_step = np.zeros_like(b18_step)
    ggt_step = compute_ggt_invariants(b18_step, b11_step, fp, sigma=1.8)

    # 2) Radially symmetric 3-D pluton/caldera plug: g(r) = exp(-r^2 / 128)
    r2 = xx * xx + yy * yy
    g_plug = np.exp(-r2 / 128.0)
    b18_plug = np.gradient(g_plug, axis=1).astype(np.float32)
    b11_plug = np.gradient(g_plug, axis=0).astype(np.float32)
    ggt_plug = compute_ggt_invariants(b18_plug, b11_plug, fp, sigma=1.8)

    assert float(ggt_step["d_2d"][40, 35]) > 0.99
    assert float(ggt_plug["d_2d"][40, 40]) < 0.05
    assert float(ggt_step["sheet_2d_score"][40, 35]) > float(ggt_plug["sheet_2d_score"][40, 40])


def test_spin2_hessian_conjugate_intersection_cone_fires_on_x_junction_not_straight_fault():
    """Regression test: spin-2 Hessian orientation must detect symmetric 1-px X-junctions."""
    h, w = 81, 81
    fp = np.ones((h, w), dtype=bool)

    # Straight N-S fault through col 40, truncated at row 44 so tip exists but no conjugate crossing
    vis_straight = np.zeros((h, w), dtype=bool)
    vis_straight[10:45, 40] = True
    kin_straight = compute_faulds_hinz_kinematic_fields(vis_straight, fp)

    # Conjugate X-junction crossing at (40, 40) at +/-45 degrees
    vis_x = np.zeros((h, w), dtype=bool)
    for k in range(-22, 23):
        vis_x[40 + k, 40 + k] = True
        vis_x[40 + k, 40 - k] = True
    kin_x = compute_faulds_hinz_kinematic_fields(vis_x, fp)

    max_straight = float(kin_straight["conjugate_intersection_cone"][34:47, 34:47].max())
    max_x = float(kin_x["conjugate_intersection_cone"][34:47, 34:47].max())
    assert max_x > 0.80
    assert max_straight < 0.05
    assert set(kin_x.keys()) == set(COUPLED_KINEMATIC_NAMES)


def test_exposure_propensity_weights_upweight_covered_basins_without_labels(tmp_path: Path):
    """Exposure-propensity weights must be bounded in [1.0, 2.5] and higher in flat basins than steep bedrock."""
    h, w = 40, 40
    fp = np.ones((h, w), dtype=bool)
    transform = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)

    # Create tiny synthetic 19-band training_features.tif and 9-band topo_10m_derived_100m_u8.tif
    feat_tif = tmp_path / "training_features.tif"
    slope_idx = int(BY_NAME["det_elev_slope"])  # 1-based band index
    with rasterio.open(
        feat_tif,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=19,
        dtype="float32",
        crs="EPSG:32611",
        transform=transform,
    ) as ds:
        for b in range(1, 20):
            if b == slope_idx:
                # Left half: steep bedrock (25 deg); right half: flat basin (0.4 deg)
                arr = np.where(np.arange(w)[None, :] < 20, 25.0, 0.4).astype(np.float32) * np.ones(
                    (h, 1), dtype=np.float32
                )
            else:
                arr = np.zeros((h, w), dtype=np.float32)
            ds.write(arr, b)

    ext_dir = tmp_path / "external"
    ext_dir.mkdir()
    with rasterio.open(
        ext_dir / "topo_10m_derived_100m_u8.tif",
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=9,
        dtype="uint8",
        crs="EPSG:32611",
        transform=transform,
    ) as ds_t10:
        hi_left = np.where(np.arange(w)[None, :] < 20, 230, 10).astype(np.uint8) * np.ones(
            (h, 1), dtype=np.uint8
        )
        for b in range(1, 10):
            ds_t10.write(hi_left if b in (3, 5) else np.ones((h, w), dtype=np.uint8), b)

    weights = compute_exposure_propensity_weights(feat_tif, ext_dir, fp)
    assert weights.shape == (h, w)
    assert np.all(np.isfinite(weights))
    assert float(weights.min()) >= 1.0 - 1e-6
    assert float(weights.max()) <= 2.5 + 1e-6
    assert float(weights[:, 32].mean()) > float(weights[:, 6].mean())
    assert len(ALL_STATIC_NAMES) == len(NATIVE_ABLATION_NAMES) + len(TVHS_NOVEL_STATIC_NAMES) == 26


def test_h86j_preregistration_and_serialized_artifact_invariants():
    """Verify frozen hypothesis queue, 3-arm budget cap, SHA-256 bindings, and [0, 1] GeoTIFF bytes."""
    hyp = json.loads((ROOT / "registry/h86j_hypotheses.json").read_text(encoding="utf-8"))
    prereg = json.loads((ROOT / "research/H86J_TVHS_PREREGISTRATION.json").read_text(encoding="utf-8"))
    card = json.loads((ROOT / "docs/evidence/h86j-tvhs-run-card.json").read_text(encoding="utf-8"))
    inv = json.loads((ROOT / "docs/evidence/download-inventory.json").read_text(encoding="utf-8"))

    assert 3 <= len(hyp["hypotheses"]) <= 5
    for item in hyp["hypotheses"]:
        assert item["layers"]
        assert item["non_fault_mimic"].strip()
    assert len(prereg["arms"]) == 3
    assert card["experiments_run"] == 3
    assert card["submission_slots_used"] == 0
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["submission_ready"] is False
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert 1 <= card["note_chars"] == len(card["note"]) <= 140
    assert card["leakage_canary"]["max_discriminative_auc"] <= 0.90
    assert card["leakage_canary"]["any_flagged_over_0p90"] is False

    tif_path = ROOT / card["submission_file"]
    zip_path = ROOT / card["zip_file"]
    rcpt_path = ROOT / card["receipt_file"]
    assert tif_path.is_file() and zip_path.is_file() and rcpt_path.is_file()

    tif_bytes = tif_path.read_bytes()
    assert hashlib.sha256(tif_bytes).hexdigest() == card["raster_sha256"]
    assert hashlib.sha256(zip_path.read_bytes()).hexdigest() == card["zip_sha256"]
    rcpt = json.loads(rcpt_path.read_text(encoding="utf-8"))
    assert rcpt["sha256"] == card["raster_sha256"]
    assert rcpt["note"] == card["note"]

    inv_entry = next(a for a in inv["artifacts"] if a["file"] == card["submission_file"])
    assert inv_entry["sha256"] == card["raster_sha256"]
    assert inv_entry["status"] == "DO NOT SUBMIT"
    assert inv_entry["approved_for_weekly_slot"] is False

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert zf.read(tif_path.name) == tif_bytes

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert (ds.height, ds.width) == (3730, 3292)
        assert str(ds.crs) == "EPSG:32611"
        arr = ds.read(1)
        assert arr.dtype == np.float32
        assert not np.isnan(arr).any()
        assert not np.isinf(arr).any()
        assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
        assert int((arr > 0).sum()) == 37654
