"""Unit, evidence, ledger, and on-disk release tests for the CONCENTRATION down-dose ladder."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from gems86 import concentration_5km as C5  # noqa: E402

EVIDENCE = ROOT / "evidence" / "concentration_dose_axis_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_concentration_dose.json"
LEDGER_CSV = ROOT / "ledger" / "submissions.csv"

DOSE_VALUES = {"b5km-cvband-down2", "b5km-cvband-down6", "b5km-cvband-downmax"}
RELEASES = ROOT / "releases"
DOSE_IDS = (
    "h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown2-20261023-f0ee647f",
    "h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown6-20261023-1ed78e0f",
    "h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdownmax-20261023-d4a42664",
)


def test_relocate_cvband_down_sources_are_prefix_nested_across_doses():
    """down2's removal list must be a prefix of down6's, which prefixes downmax's."""
    h, w = 40, 80
    foot = np.ones((h, w), dtype=bool)
    cat = np.zeros((h, w), dtype=bool)
    cat[0, 0] = True
    edt_cat = ndi.distance_transform_edt(~cat)

    parent = np.zeros((h, w), dtype=bool)
    ridge = np.zeros((h, w), dtype=bool)
    # Three over-packed 10x10 blocks (4 dots each, wholly inside one block) ...
    for br, bc in ((10, 10), (10, 30), (20, 10)):
        for dr, dc in ((1, 1), (1, 5), (5, 1), (5, 5)):
            parent[br + dr, bc + dc] = True
            ridge[br + dr, bc + dc] = True
    # ... and six sparse 1-dot blocks with unused ridge capacity.
    for bc in (50, 60, 70):
        for br in (10, 25):
            parent[br + 2, bc + 1] = True
            ridge[br + 2, bc + 1 : bc + 9] = True

    out2, src2, _, st2 = C5.relocate_cvband_down(parent, foot, edt_cat, ridge, n_move=2)
    out6, src6, _, st6 = C5.relocate_cvband_down(parent, foot, edt_cat, ridge, n_move=4)
    assert int(out2.sum()) == int(out6.sum()) == int(parent.sum())
    assert np.array_equal(src6[:2], src2)
    assert st2["added_on_ancestor_ridge_fraction"] == 1.0
    assert st6["min_added_cat_clearance_px"] > 3.0
    # CV falls as the dose rises
    assert (
        st6["cv_1km_variant"]["density_cv_occupied"]
        < st2["cv_1km_variant"]["density_cv_occupied"]
        < st2["cv_1km_parent"]["density_cv_occupied"]
    )


def test_committed_evidence_and_ledger_invariants():
    assert EVIDENCE.is_file(), "missing dose run card"
    assert VARIANTS_JSON.is_file(), "missing variants_concentration_dose.json"
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    vj = json.loads(VARIANTS_JSON.read_text(encoding="utf-8"))
    assert ev["axis"] == "CONCENTRATION"
    assert ev["parent"]["n_dots"] == 37654
    assert ev["parent"]["rebuild"]["byte_identical_sha"] is True

    # The released down4 anchor must have rebuilt byte-exactly before anything was written.
    anchor = ev["down4_regression_anchor"]
    assert anchor["byte_identical"] is True
    assert anchor["rebuilt_zeros_sha256"] == anchor["zeros_sha256"]

    # Source-prefix nesting across the whole ladder (incl. the anchor) recorded and true.
    nesting = ev["dose_ladder"]["source_prefix_nesting"]
    assert set(nesting) == {
        "b5km-cvband-down2",
        "b5km-cvband-down4(anchor)",
        "b5km-cvband-down6",
    }
    assert all(v["exact_prefix_of_downmax_master_sequence"] for v in nesting.values())

    # CV ladder monotone downward in dose, including the anchor point.
    cv = ev["dose_ladder"]["cv_1km"]
    assert cv["R0"] > cv["b5km-cvband-down2"] > cv["b5km-cvband-down4(anchor)"] > cv["b5km-cvband-down6"] > cv["b5km-cvband-downmax"]

    # Leakage canary must stay <= 0.90 across all features/targets.
    canary = ev["report_only_instruments"]["leakage_canary"]
    assert max(t["max_auc"] for t in canary.values()) <= 0.90

    assert len(ev["variants"]) == 3 == len(vj)
    assert {r["value"] for r in vj} == DOSE_VALUES
    ledger_rows = {
        r["id"]: r
        for r in csv.DictReader(LEDGER_CSV.open(newline="", encoding="utf-8"))
        if r.get("id")
    }
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
        assert st["count_fixed"] is True
        # Every dose arm must be positive on the SGMC surrogate with 4/4 quadrants.
        assert rec["model_delta_sgmc"] > 0.0
    # The ceiling must be a recorded structural fact.
    ceiling = ev["dose_ladder"]["downmax_ceiling"]["max_feasible_n_move"]
    assert 1506 < ceiling <= 3012


def test_dose_values_are_new_in_the_full_ledger():
    """Brief section 5: each (axis, value) pair is built once across all sessions."""
    rows = list(csv.DictReader(LEDGER_CSV.open(newline="", encoding="utf-8")))
    conc = [r for r in rows if r.get("axis") == "CONCENTRATION"]
    seen = {}
    for r in conc:
        key = (r["axis"], r["value"])
        seen[key] = seen.get(key, 0) + 1
    for v in DOSE_VALUES:
        assert seen.get(("CONCENTRATION", v), 0) == 1, f"{v} must appear exactly once"
    # and the prior down4 anchor is untouched
    assert seen.get(("CONCENTRATION", "b5km-cvband-down4"), 0) == 1


def _local_dose_zeros() -> list[Path]:
    if not RELEASES.is_dir():
        return []
    return [RELEASES / f"{cid}-zeros.tif" for cid in DOSE_IDS if (RELEASES / f"{cid}-zeros.tif").is_file()]


@pytest.mark.skipif(not _local_dose_zeros(), reason="dose-ladder TIFFs are gitignored in CI")
def test_on_disk_releases_match_receipts():
    import rasterio

    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(ROOT / "data" / "bridge" / "existing_faults.tif") as s:
        cat = (s.read(1) > 0) & foot
    edt_cat = ndi.distance_transform_edt(~cat)

    for rec in ev["variants"]:
        zpath = RELEASES / rec["zeros"]["file"]
        assert zpath.is_file(), zpath
        import hashlib

        digest = hashlib.sha256(zpath.read_bytes()).hexdigest()
        assert digest == rec["zeros"]["sha256"]
        with rasterio.open(zpath) as src:
            arr = src.read(1)
        dots = arr > 0.5
        assert int(dots.sum()) == 37654 == rec["n_dots"]
        assert not np.any(dots & cat)
        # Parent survivors may sit anywhere in (2.0, 3.0] px; only ADDED dots must clear > 3.0 px.
        assert float(edt_cat[dots].min()) > 2.0
        assert rec["concentration_stats"]["min_added_cat_clearance_px"] > 3.0
        assert not np.any(dots & ~foot)
