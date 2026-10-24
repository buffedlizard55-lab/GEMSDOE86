"""Unit, evidence, ledger, and on-disk release tests for 5 km CONCENTRATION."""
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

from gems86 import concentration_5km as C5  # noqa: E402

RELEASES = ROOT / "releases"
EVIDENCE = ROOT / "evidence" / "concentration_5km_axis_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_concentration_5km.json"
LEDGER_CSV = ROOT / "ledger" / "submissions.csv"


def test_zhang_suen_tips_and_junctions():
    mask = np.zeros((31, 31), dtype=bool)
    # Crossing X-fault at (15, 15) -> 4 tips + central junction
    for k in range(4, 27):
        mask[k, k] = True
        mask[k, 30 - k] = True
    topo = C5.skeleton_tips_and_junctions(mask)
    assert int(topo["tips"].sum()) == 4
    assert int(topo["junctions"].sum()) >= 1
    assert topo["tips"][4, 4] and topo["tips"][26, 26]
    assert topo["tips"][4, 26] and topo["tips"][26, 4]


def test_local_agc_equalizes_two_terrane_amplitudes():
    foot = np.ones((80, 160), dtype=bool)
    field = np.zeros((80, 160), dtype=np.float32)
    # Left half: high-magnetization basalt step (+100); right half: weak sedimentary step (+20)
    field[40:, :80] = 100.0
    field[40:, 80:] = 20.0
    grad, agc = C5.local_agc_gradient(field, foot, window_px=31, floor=0.05)
    raw_ratio = float(grad[40, 30]) / float(grad[40, 130])
    agc_ratio = float(agc[40, 30]) / float(agc[40, 130])
    assert raw_ratio == pytest.approx(5.0, rel=0.05)
    assert 0.85 <= agc_ratio <= 1.15


def test_relocate_5km_ridge_up_strict_nesting_and_constraints():
    h, w = 60, 120
    foot = np.ones((h, w), dtype=bool)
    cat = np.zeros((h, w), dtype=bool)
    cat[2, 2] = True  # single known-fault pixel in corner
    edt_cat = ndi.distance_transform_edt(~cat)

    # Eight 30x30 blocks (2x4); place 16 parent dots in low-prior left blocks and build
    # rich unused ridge lines in high-prior right blocks
    parent = np.zeros((h, w), dtype=bool)
    ridge = np.zeros((h, w), dtype=bool)
    for idx, r in enumerate(range(10, 50, 4)):
        parent[r, 15] = True
        ridge[r, 15] = True
        if idx < 6:
            parent[r, 25] = True
            ridge[r, 25] = True

    for r in range(8, 56, 4):
        for c in range(70, 114):
            ridge[r, c] = True

    prior_blocks = np.array(
        [[-2.0, -1.0, 2.5, 2.2], [-1.5, -0.5, 2.0, 1.8]], dtype=np.float64
    )
    out4, src4, dst4, st4 = C5.relocate_5km_ridge_up(
        parent, foot, edt_cat, ridge, prior_blocks,
        n_move=4, block_px=30, dest_block_frac=0.50,
    )
    out8, src8, dst8, st8 = C5.relocate_5km_ridge_up(
        parent, foot, edt_cat, ridge, prior_blocks,
        n_move=8, block_px=30, dest_block_frac=0.50,
    )

    assert int(out4.sum()) == int(parent.sum()) == int(out8.sum())
    assert st4["n_removed"] == st4["n_added"] == 4
    assert st8["n_removed"] == st8["n_added"] == 8
    assert st4["added_on_ancestor_ridge_fraction"] == 1.0
    assert st8["added_on_ancestor_ridge_fraction"] == 1.0
    assert st8["min_added_cat_clearance_px"] > 3.0
    assert st8["min_pair_distance_variant_px"] >= math.sqrt(8.0) - 1e-4
    # Exact prefix nesting
    assert np.array_equal(src4, src8[:4])
    assert np.array_equal(dst4, dst8[:4])


def test_relocate_cvband_down_lowers_occupied_cv_with_fixed_count():
    h, w = 40, 80
    foot = np.ones((h, w), dtype=bool)
    cat = np.zeros((h, w), dtype=bool)
    cat[0, 0] = True
    edt_cat = ndi.distance_transform_edt(~cat)

    parent = np.zeros((h, w), dtype=bool)
    ridge = np.zeros((h, w), dtype=bool)
    # Over-pack two 10x10 blocks with 4 dots each
    for br, bc in ((10, 10), (10, 30)):
        for dr, dc in ((1, 1), (1, 5), (5, 1), (5, 5)):
            parent[br + dr, bc + dc] = True
            ridge[br + dr, bc + dc] = True
    # Create six sparse 1-dot 10x10 blocks that also have unused ridge capacity
    for idx, bc in enumerate((50, 60, 70)):
        for br in (10, 25):
            parent[br + 2, bc + 1] = True
            ridge[br + 2, bc + 1 : bc + 9] = True

    out, src, dst, st = C5.relocate_cvband_down(
        parent, foot, edt_cat, ridge, n_move=4, km_block_px=10
    )
    assert int(out.sum()) == int(parent.sum())
    assert len(src) == len(dst) == 4
    assert st["added_on_ancestor_ridge_fraction"] == 1.0
    assert st["min_added_cat_clearance_px"] > 3.0
    assert st["cv_1km_variant"]["density_cv_occupied"] < st["cv_1km_parent"]["density_cv_occupied"]


def test_committed_evidence_and_ledger_invariants():
    assert EVIDENCE.is_file(), "missing master run card"
    assert VARIANTS_JSON.is_file(), "missing variants_concentration_5km.json"
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    vj = json.loads(VARIANTS_JSON.read_text(encoding="utf-8"))
    assert ev["axis"] == "CONCENTRATION"
    assert ev["parent"]["n_dots"] == 37654
    assert ev["parent"]["rebuild"]["byte_identical_sha"] is True
    assert ev["prior_5km_summary"]["nesting_verified_up4_in_up8"] is True
    assert ev["submission_slots_used"] == 0

    # Leakage canary must stay <= 0.90 across all features/targets
    canary = ev["report_only_instruments"]["leakage_canary"]
    assert max(t["max_auc"] for t in canary.values()) <= 0.90

    # PR #37 forensic audit recorded
    audit = ev["pr37_b1km_move15_forensic_audit"]
    assert audit["geometry"]["violates_brief_sec4_3px_clearance"] is True
    assert audit["measured_sgmc_model"]["all"]["delta"] < 0.0

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
        if rec["value"] == "b5km-cvband-down4":
            assert 0.51 <= st["cv_1km_variant"]["density_cv_occupied"] <= 0.59
        seen_values.add(rec["value"])
    assert seen_values == {"b5km-ridge-up8", "b5km-ridge-up4", "b5km-cvband-down4"}


def _local_conc5_zeros() -> list[Path]:
    # Only the 5 km session's three arms (up8/up4/cvband-down4); later CONCENTRATION
    # sessions (e.g. the pediment arms) have their own on-disk receipts/tests.
    return sorted(
        p for p in RELEASES.glob("*-concb5km*-zeros.tif")
        if any(s in p.name for s in ("b5kmup8", "b5kmup4", "b5kmdown4"))
    ) if RELEASES.is_dir() else []


@pytest.mark.skipif(not _local_conc5_zeros(), reason="CONCENTRATION 5 km TIFFs are gitignored in CI")
def test_on_disk_releases_match_receipts_and_nesting():
    import rasterio

    parent_path = (
        ROOT
        / "data"
        / "scored_fleet"
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
    for zp in _local_conc5_zeros():
        rec = json.loads(zp.with_suffix(".json").read_text(encoding="utf-8"))
        np_path = zp.with_name(zp.name.replace("-zeros.tif", ".tif"))
        assert np_path.is_file()
        assert hashlib.sha256(zp.read_bytes()).hexdigest() == rec["zeros"]["sha256"]
        assert hashlib.sha256(np_path.read_bytes()).hexdigest() == rec["nan"]["sha256"]
        with rasterio.open(zp) as sz, rasterio.open(np_path) as sn:
            az = sz.read(1)
            an = sn.read(1)
        dots = az > 0.5
        assert np.array_equal(np.isfinite(an) & (an > 0.5), dots)
        assert np.all(np.isnan(an[~foot])) and np.all(np.isfinite(an[foot]))
        assert np.all(az[~foot] == 0.0)
        assert int(dots.sum()) == 37654
        assert not np.any(dots & cat)
        added = dots & ~parent
        assert float(edt_cat[added].min()) > 3.0
        by_val[rec["value"]] = dots

    # Verify strict subset nesting directly from the written pixel rasters
    add4 = by_val["b5km-ridge-up4"] & ~parent
    add8 = by_val["b5km-ridge-up8"] & ~parent
    rem4 = parent & ~by_val["b5km-ridge-up4"]
    rem8 = parent & ~by_val["b5km-ridge-up8"]
    assert np.all(add4 <= add8) and int(add4.sum()) == 1506 and int(add8.sum()) == 3012
    assert np.all(rem4 <= rem8) and int(rem4.sum()) == 1506 and int(rem8.sum()) == 3012
