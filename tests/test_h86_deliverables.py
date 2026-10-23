"""Comprehensive automated Pass-2 & Pass-3 verification suite for GEMSDOE86 (`Lane H86-FVMB`)."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "src"))

from gems57 import grid as GRID, validate as V  # noqa: E402
from gems86.dinkelbach_allocator import kernel_25_offsets  # noqa: E402
from gems86.features import STATIC_60_NAMES  # noqa: E402
from gems86.wingcrack_network import WINGCRACK_12_NAMES  # noqa: E402


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_shared_template_pin_unmodified() -> None:
    """Protocol Rule 2: Verify zero private-fork drift across all 23 vendor/gems57 files."""
    pin = json.loads((ROOT / "registry" / "template_pin.json").read_text())
    files = pin["files"]
    assert len(files) == 23
    for rel, expected_sha in files.items():
        local_p = ROOT / rel if rel.startswith("vendor/") else ROOT / "vendor" / "gems57" / Path(rel).name
        assert local_p.is_file(), f"Missing shared template file: {local_p}"
        assert _sha256(local_p) == expected_sha, f"Modified shared file: {local_p}"


def test_anti_leakage_invariants_in_code_and_canary() -> None:
    """Protocol Rule 4/6: No `dist_known_fault_px` read and all 72 channels <= 0.90 AUC."""
    feat_code = (ROOT / "src" / "gems86" / "features.py").read_text()
    # Must never index or select dist_known_fault_px as a feature column
    assert 'df["dist_known_fault_px"]' not in feat_code
    assert len(STATIC_60_NAMES) == 60
    assert len(WINGCRACK_12_NAMES) == 12
    assert len(kernel_25_offsets()) == 25

    canary = json.loads((ROOT / "evidence" / "exp1_leakage_canary.json").read_text())
    assert canary["passed"] is True
    assert canary["n_channels_tested"] == 72
    assert canary["max_symmetric_auc"] <= 0.90


def test_run_card_and_submission_geotiff_all_checks() -> None:
    """Verify GeoTIFF range [0, 1], zero NaN/Inf, zero catalogue overlap, ZIP roundtrip, and Run Card."""
    rc = json.loads((ROOT / "run_card.json").read_text())
    rc_docs = json.loads((ROOT / "docs" / "data" / "run_card.json").read_text())
    assert rc == rc_docs
    assert rc["verdict"] == "promote"
    assert rc["ok_to_download_and_submit"] is True
    assert rc["weekly_submission_slots_used"] == 0
    assert rc["experiments_executed"] <= 3

    art = rc["submission_artifact"]
    assert 1 <= art["submission_note_chars"] <= 140
    assert len(art["submission_note"]) == art["submission_note_chars"]

    tif_docs = ROOT / art["tif_file"]
    tif_sub = ROOT / art["tif_submissions_copy"]
    zip_docs = ROOT / art["zip_file"]
    assert tif_docs.is_file() and tif_sub.is_file() and zip_docs.is_file()
    assert _sha256(tif_docs) == art["raster_sha256"] == _sha256(tif_sub)
    assert _sha256(zip_docs) == art["zip_sha256"]

    with zipfile.ZipFile(zip_docs) as zf:
        assert zf.namelist() == [tif_docs.name]
        assert zf.read(tif_docs.name) == tif_docs.read_bytes()

    g = GRID.load_grid(ROOT / "data" / "bridge")
    val = V.validate(tif_docs, g.footprint, g.catalogue)
    V.assert_submittable(val)
    assert val["all_checks_passed"] is True
    assert val["n_nan"] == 0
    assert val["n_infinite"] == 0
    assert val["min"] == 0.0
    assert val["max"] == 1.0
    assert val["emitted_positive_pixels"] == 38_400

    with rasterio.open(tif_docs) as ds:
        arr = ds.read(1)
        assert ds.nodata is None
        assert ds.dtypes[0] == "float32"
        assert np.all(np.isfinite(arr))
        assert np.all((arr >= 0.0) & (arr <= 1.0))
        assert np.all(arr[~g.footprint] == 0.0)
        assert int((arr[g.catalogue] > 0).sum()) == 0


def test_uniqueness_and_holdout_gates() -> None:
    """Protocol Rule 1 & 4: Verify pre/post uniqueness and statistically significant holdout improvement."""
    uq = json.loads((ROOT / "evidence" / "exp3_uniqueness_audit.json").read_text())
    assert uq["rasters_checked"] >= 26
    assert uq["pre_placement_surface"]["unique"] is True
    assert uq["pre_placement_surface"]["binding_decision"]["worst_abs_spearman"] <= 0.90
    assert uq["pre_placement_surface"]["binding_decision"]["worst_forward_overlap"] <= 0.70
    assert uq["final_emitted_dots"]["unique"] is True
    assert uq["final_emitted_dots"]["binding_decision"]["worst_abs_spearman"] <= 0.90
    assert uq["final_emitted_dots"]["binding_decision"]["worst_forward_overlap"] <= 0.70

    ho = json.loads((ROOT / "evidence" / "exp2_exp3_holdout_ablation.json").read_text())
    hero = ho["dual_seed_pooled"]["scores"]["EXP86_3_FVMB_TriRegime_Dink"]
    h33 = ho["dual_seed_pooled"]["scores"]["Ref_GEMS32_H33_FoldFair_02778"]
    diff = ho["dual_seed_pooled"]["paired_differences"]["Ref_GEMS32_H33_FoldFair_02778"]
    assert hero["dti"] > h33["dti"] + 0.04
    assert diff["ci95"][0] > 0.04


def test_github_pages_local_links_and_assets() -> None:
    """Verify all HTML pages exist and every local href/src resolves on disk."""
    pages = [
        ROOT / "index.html",
        ROOT / "docs" / "index.html",
        ROOT / "docs" / "executive-summary.html",
        ROOT / "docs" / "forensics-and-science.html",
        ROOT / "docs" / "audit-and-irregularities.html",
    ]
    for p in pages:
        assert p.is_file(), f"Missing page: {p}"
        html = p.read_text()
        for ref in re.findall(r'(?:href|src)="([^"]+)"', html):
            if ref.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = (p.parent / ref).resolve()
            assert target.exists(), f"Broken relative link in {p.name}: {ref} -> {target}"
