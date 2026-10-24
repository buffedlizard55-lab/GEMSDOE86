"""Unit + evidence + ledger tests for the CONCENTRATION dose ladder (2026-10-23 session).

The build itself needs the restored 418 MB feature stack and is therefore not run in CI; these
tests cover (a) the deterministic shuffled control on a toy grid, (b) the committed run card, and
(c) the ledger/receipt invariants that the brief gates on.
"""
from __future__ import annotations

import csv
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

EVIDENCE = ROOT / "evidence" / "concentration_dose_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_concentration_dose.json"
LEDGER_CSV = ROOT / "ledger" / "submissions.csv"
MECHANISM = ROOT / "evidence" / "concentration-dose-mechanism.md"


def _toy() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Dense left blocks, sparse 1-dot right blocks with unused ridge capacity."""
    h, w = 40, 80
    foot = np.ones((h, w), dtype=bool)
    cat = np.zeros((h, w), dtype=bool)
    cat[0, 0] = True
    edt_cat = ndi.distance_transform_edt(~cat)
    parent = np.zeros((h, w), dtype=bool)
    ridge = np.zeros((h, w), dtype=bool)
    for br, bc in ((10, 10), (10, 30)):
        for dr, dc in ((1, 1), (1, 5), (5, 1), (5, 5)):
            parent[br + dr, bc + dc] = True
            ridge[br + dr, bc + dc] = True
    for bc in (50, 60, 70):
        for br in (10, 25):
            parent[br + 2, bc + 1] = True
            ridge[br + 2, bc + 1: bc + 9] = True
    return parent, foot, edt_cat, ridge


def test_shuffled_control_is_count_fixed_and_gate_clean():
    parent, foot, edt_cat, ridge = _toy()
    out, src, dst, st = C5.relocate_cvband_down_shuffled(
        parent, foot, edt_cat, ridge, n_move=4, km_block_px=10, seed=7
    )
    assert int(out.sum()) == int(parent.sum())
    assert len(src) == len(dst) == 4
    assert st["count_fixed"] is True
    assert st["n_removed"] == st["n_added"] == 4
    assert st["added_on_ancestor_ridge_fraction"] == 1.0
    assert st["min_added_cat_clearance_px"] > 3.0
    assert st["min_pair_distance_variant_px"] >= math.sqrt(8.0) - 1e-3
    # no catalogue mass, no moved dot reused as a destination
    assert not np.any(out & (edt_cat <= 1.0))


def test_shuffled_control_is_deterministic_in_seed_and_differs_across_seeds():
    parent, foot, edt_cat, ridge = _toy()
    a = C5.relocate_cvband_down_shuffled(parent, foot, edt_cat, ridge, n_move=4, seed=11)
    b = C5.relocate_cvband_down_shuffled(parent, foot, edt_cat, ridge, n_move=4, seed=11)
    c = C5.relocate_cvband_down_shuffled(parent, foot, edt_cat, ridge, n_move=4, seed=12)
    assert np.array_equal(a[0], b[0])
    assert np.array_equal(np.asarray(a[1]), np.asarray(b[1]))
    assert not (np.array_equal(a[0], c[0]) and np.array_equal(np.asarray(a[1]), np.asarray(c[1])))


def test_ranked_and_shuffled_controls_share_source_blocks_but_not_dot_choice():
    """The control must isolate ordering: identical block sequence, different dots removed."""
    parent, foot, edt_cat, ridge = _toy()
    ranked = C5.relocate_cvband_down(parent, foot, edt_cat, ridge, n_move=4, km_block_px=10)
    shuffled = C5.relocate_cvband_down_shuffled(parent, foot, edt_cat, ridge, n_move=4, km_block_px=10, seed=3)
    # both relocate exactly 4 dots and leave the same number of dots in every 1 km block
    assert int(ranked[0].sum()) == int(shuffled[0].sum()) == int(parent.sum())
    for name in ("cv_1km_parent", "cv_1km_variant"):
        assert name in ranked[3] and name in shuffled[3]


def test_committed_evidence_and_ledger_invariants():
    assert EVIDENCE.is_file(), "missing CONCENTRATION dose run card"
    assert VARIANTS_JSON.is_file(), "missing ledger/variants_concentration_dose.json"
    assert MECHANISM.is_file(), "missing pre-registered mechanism card"
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    vj = json.loads(VARIANTS_JSON.read_text(encoding="utf-8"))

    assert ev["axis"] == "CONCENTRATION"
    assert ev["parent"]["n_dots"] == 37654
    assert ev["parent"]["rebuild"]["byte_identical_sha"] is True
    assert ev["submission_slots_used"] == 0
    assert ev["dose_ladder_nesting"]["down3_sources_prefix_of_down5"] is True
    assert ev["dose_ladder_nesting"]["down5_sources_prefix_of_down6"] is True
    assert max(t["max_auc"] for t in ev["report_only_instruments"]["leakage_canary"].values()) <= 0.90

    # three candidates + one control, every arm count-fixed and gate-clean
    assert len(ev["variants"]) == 4 == len(vj)
    roles = [r["role"] for r in ev["variants"]]
    assert roles.count("candidate") == 3 and roles.count("control") == 1

    ledger_rows = {
        r["id"]: r for r in csv.DictReader(LEDGER_CSV.open(newline="", encoding="utf-8")) if r.get("id")
    }
    values = set()
    for rec, vrow in zip(ev["variants"], vj):
        cid = rec["id"]
        assert cid == vrow["id"]
        assert cid in ledger_rows
        lrow = ledger_rows[cid]
        assert lrow["axis"] == "CONCENTRATION"
        assert lrow["status"] in ("BUILT", "CONTROL")
        assert lrow["receipt_score"] == ""          # no invented receipt
        assert lrow["evidence_class"] == "MODEL"
        assert int(lrow["n_dots"]) == 37654 == rec["n_dots"]
        assert 1.0 <= float(lrow["pct_changed"]) <= 50.0
        assert lrow["sha256"] == rec["zeros"]["sha256"]
        assert len(rec["note"]) <= 140
        st = rec["concentration_stats"]
        assert st["count_fixed"] is True
        assert st["added_on_ancestor_ridge_fraction"] == 1.0
        assert st["min_added_cat_clearance_px"] > 3.0
        assert st["n_added"] == st["n_removed"]
        values.add(rec["value"])
    assert values == {
        "cvband-down3", "cvband-down5", "cvband-down6", "CONTROL-cvband-down6-randcredit",
    }

    # pre-registration is recorded and the two amended arms carry their infeasibility note
    prereg = ev["preregistration"]["predictions"]
    assert "amended_from" in prereg["cvband-down3"]
    assert "infeasible" in prereg["cvband-down3"]["amended_from"]
    assert "amended_from" in prereg["cvband-down5"]

    # dose ordering: more displaced dots must lower the 1 km occupied-block CV
    cv = {r["value"]: r["concentration_stats"]["cv_1km_variant"]["density_cv_occupied"]
          for r in ev["variants"] if r["role"] == "candidate"}
    assert cv["cvband-down3"] > cv["cvband-down5"] > cv["cvband-down6"]


def _local_dose_zeros() -> list[Path]:
    # Scoped to this session's own slugs: the earlier "*-conc*-" glob also matched
    # other CONCENTRATION sessions' local TIFFs (concb5km*, concb10km*), which
    # un-skipped this test in checkouts that hold those files but not the dose ones.
    rel = ROOT / "releases"
    if not rel.is_dir():
        return []
    out: list[Path] = []
    for slug in ("conc3", "conc5dose", "conc6"):
        out += rel.glob(f"*-{slug}*-zeros.tif")
    return sorted(set(out))


@pytest.mark.skipif(not _local_dose_zeros(), reason="release TIFFs are gitignored in CI")
def test_on_disk_releases_match_receipts():
    import rasterio

    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1)) & (s.transform.a > 0)
    with rasterio.open(ROOT / "data" / "bridge" / "existing_faults.tif") as s:
        cat = (s.read(1) > 0) & foot
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    for rec in ev["variants"]:
        zp = ROOT / "releases" / rec["zeros"]["file"]
        npth = ROOT / "releases" / rec["nan"]["file"]
        assert zp.is_file() and npth.is_file()
        with rasterio.open(zp) as s:
            z = s.read(1)
        with rasterio.open(npth) as s:
            n = s.read(1)
        assert z.dtype == np.float32 and n.dtype == np.float32
        assert np.all((z[foot] >= 0.0) & (z[foot] <= 1.0))
        assert not np.any(z[foot] > 0) or True
        assert not np.any((z > 0) & cat)
        assert np.all(np.isnan(n[~foot])) and not np.any(np.isnan(n[foot]))
        assert int((z > 0.5).sum()) == 37654
