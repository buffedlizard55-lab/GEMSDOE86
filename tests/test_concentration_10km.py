"""Unit, evidence, ledger, and on-disk release tests for 10 km CONCENTRATION."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from gems86 import concentration_10km as C10  # noqa: E402

RELEASES = ROOT / "releases"
EVIDENCE = ROOT / "evidence" / "concentration_10km_axis_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_concentration_10km.json"
PREREG = ROOT / "registry" / "preregistration_conc10.json"
LEDGER_CSV = ROOT / "ledger" / "submissions.csv"
VALUES = {"b10km-down8", "b10km-down4", "b10km-ridge-up8"}


def _toy():
    """2x4 grid of 30 px blocks: dense left blocks, sparse occupied right blocks."""
    h, w = 60, 120
    foot = np.ones((h, w), dtype=bool)
    cat = np.zeros((h, w), dtype=bool)
    cat[2, 2] = True
    edt_cat = ndi.distance_transform_edt(~cat)
    parent = np.zeros((h, w), dtype=bool)
    ridge = np.zeros((h, w), dtype=bool)
    # Dense: 16 parent dots in the two left block columns.
    for r in range(10, 50, 4):
        parent[r, 15] = True
        ridge[r, 15] = True
        if r < 34:
            parent[r, 40] = True
            ridge[r, 40] = True
    # Sparse but occupied: 1 dot per right block + rich unused ridge lines.
    for br in (0, 30):
        for bc in (60, 90):
            parent[br + 8, bc + 5] = True
            ridge[br + 8, bc + 5] = True
    for r in range(8, 56, 4):
        ridge[r, 70:114] = True
    return parent, foot, edt_cat, ridge


def test_density_prior_sign_and_occupancy():
    parent, foot, _, _ = _toy()
    dens = C10.occupied_density_blocks(parent, foot, block_px=30)
    assert dens["block_px"] == 30
    assert dens["n_valid_blocks"] == int(dens["valid_blocks"].sum())
    # Prior is the sign-flipped density on valid blocks, -inf elsewhere.
    v = dens["valid_blocks"]
    assert np.allclose(dens["prior_blocks"][v], -dens["density_blocks"][v])
    assert np.all(np.isneginf(dens["prior_blocks"][~v]))
    # Densest block has the lowest (most negative) prior -> donor side.
    assert dens["prior_blocks"][0, 0] < dens["prior_blocks"][0, 3]


def test_relocate_b10km_down_nesting_and_constraints():
    parent, foot, edt_cat, ridge = _toy()
    dens = C10.occupied_density_blocks(parent, foot, block_px=30)
    out4, src4, dst4, st4 = C10.relocate_b10km_down(
        parent, foot, edt_cat, ridge, dens, n_move=4, dest_block_frac=0.50)
    out8, src8, dst8, st8 = C10.relocate_b10km_down(
        parent, foot, edt_cat, ridge, dens, n_move=8, dest_block_frac=0.50)

    assert int(out4.sum()) == int(parent.sum()) == int(out8.sum())
    assert st4["n_removed"] == st4["n_added"] == 4
    assert st8["n_removed"] == st8["n_added"] == 8
    assert st8["added_on_ancestor_ridge_fraction"] == 1.0
    assert st8["min_added_cat_clearance_px"] > 3.0
    assert st8["min_pair_distance_variant_px"] >= math.sqrt(8.0) - 1e-4
    # Donors leave the dense (left) half; destinations enter the sparse (right) half.
    assert np.all(src8[:, 1] < 60)
    assert np.all(dst8[:, 1] >= 60)
    # Exact prefix nesting at fixed destination fraction.
    assert np.array_equal(src4, src8[:4])
    assert np.array_equal(dst4, dst8[:4])


def test_preregistration_covers_built_arms():
    pre = json.loads(PREREG.read_text(encoding="utf-8"))
    assert pre["axis"] == "CONCENTRATION"
    assert {a["value"] for a in pre["arms"]} == VALUES
    assert pre["slots_used"] == 0
    for arm in pre["arms"]:
        assert arm["preregistered_prediction_model"]
        assert arm["falsifier"]


def test_committed_evidence_and_ledger_invariants():
    assert EVIDENCE.is_file(), "missing master run card"
    assert VARIANTS_JSON.is_file(), "missing variants_concentration_10km.json"
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    vj = json.loads(VARIANTS_JSON.read_text(encoding="utf-8"))
    assert ev["axis"] == "CONCENTRATION" and ev["block_px"] == 100
    assert ev["parent"]["n_dots"] == 37654
    assert ev["parent"]["rebuild"]["byte_identical_sha"] is True
    assert ev["design_notes"]["nesting_verified_down4_in_down8"] is True
    assert ev["submission_slots_used"] == 0

    canary = ev["report_only_instruments"]["leakage_canary"]
    assert max(t["max_auc"] for t in canary.values()) <= 0.90

    # R0's canonical 10 km CV is above the band (IR-86-CONC-18): dispersal is the
    # band-ward direction, and both down arms must reduce it.
    cv0 = ev["parent"]["block_density_cv_parent"]["cv_10km"]["density_cv_occupied"]
    assert cv0 > 0.59

    assert len(ev["variants"]) == 3 == len(vj)
    ledger_rows = {
        r["id"]: r
        for r in csv.DictReader(LEDGER_CSV.open(newline="", encoding="utf-8"))
        if r.get("id")
    }
    seen_values = set()
    for rec, vrow in zip(ev["variants"], vj):
        cid = rec["id"]
        assert cid == vrow["id"]
        assert cid in ledger_rows
        lrow = ledger_rows[cid]
        assert lrow["axis"] == "CONCENTRATION"
        assert lrow["status"] == "BUILT"
        assert lrow["receipt_score"] == ""
        assert lrow["evidence_class"] == "MODEL"
        assert int(lrow["n_dots"]) == 37654 == rec["n_dots"]
        assert 1.0 <= float(lrow["pct_changed"]) <= 50.0
        assert lrow["sha256"] == rec["zeros"]["sha256"]
        assert len(rec["note"]) <= 140
        st = rec["concentration_stats"]
        assert st["added_on_ancestor_ridge_fraction"] == 1.0
        assert st["min_added_cat_clearance_px"] > 3.0
        if rec["value"] in ("b10km-down4", "b10km-down8"):
            assert st["cv_10km_variant"]["density_cv_occupied"] < cv0
        seen_values.add(rec["value"])
    assert seen_values == VALUES


def _local_conc10_zeros() -> list[Path]:
    return sorted(RELEASES.glob("*-concb10km*-zeros.tif")) if RELEASES.is_dir() else []


@pytest.mark.skipif(not _local_conc10_zeros(), reason="CONCENTRATION 10 km TIFFs are gitignored in CI")
def test_on_disk_releases_match_receipts_and_nesting():
    import rasterio

    parent_path = (
        ROOT / "data" / "scored_fleet"
        / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    )
    with rasterio.open(parent_path) as s:
        parent = s.read(1) > 0.5
    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(ROOT / "data" / "bridge" / "existing_faults.tif") as s:
        cat = (s.read(1) > 0) & foot
    edt_cat = ndi.distance_transform_edt(~cat)

    by_val = {}
    for zp in _local_conc10_zeros():
        rec = json.loads(zp.with_suffix(".json").read_text(encoding="utf-8"))
        np_path = zp.with_name(zp.name.replace("-zeros.tif", ".tif"))
        assert np_path.is_file()
        assert hashlib.sha256(zp.read_bytes()).hexdigest() == rec["zeros"]["sha256"]
        assert hashlib.sha256(np_path.read_bytes()).hexdigest() == rec["nan"]["sha256"]
        with rasterio.open(zp) as sz, rasterio.open(np_path) as sn:
            az, an = sz.read(1), sn.read(1)
        dots = az > 0.5
        assert np.array_equal(np.isfinite(an) & (an > 0.5), dots)
        assert np.all(np.isnan(an[~foot])) and np.all(np.isfinite(an[foot]))
        assert np.all(az[~foot] == 0.0)
        assert int(dots.sum()) == 37654
        assert not np.any(dots & cat)
        added = dots & ~parent
        assert float(edt_cat[added].min()) > 3.0
        by_val[rec["value"]] = dots

    add4 = by_val["b10km-down4"] & ~parent
    add8 = by_val["b10km-down8"] & ~parent
    rem4 = parent & ~by_val["b10km-down4"]
    rem8 = parent & ~by_val["b10km-down8"]
    assert np.all(add4 <= add8) and int(add4.sum()) == 1506 and int(add8.sum()) == 3012
    assert np.all(rem4 <= rem8) and int(rem4.sum()) == 1506 and int(rem8.sum()) == 3012
