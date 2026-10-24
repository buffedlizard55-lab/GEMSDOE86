"""Unit, evidence, ledger and on-disk release tests for the surface-extension arms."""
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
sys.path.insert(0, str(ROOT / "vendor" / "template66"))

from gems86 import concentration_5km as C5  # noqa: E402
from gems86 import concentration_surfext as SE  # noqa: E402

RELEASES = ROOT / "releases"
EVIDENCE = ROOT / "evidence" / "concentration_surfext_axis_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_concentration_surfext.json"
LEDGER_CSV = ROOT / "ledger" / "submissions.csv"
VALUES = ("b5km-surfext-down10", "b5km-surfext-down15", "b5km-surfext-down10-randdst")


def _synthetic_case():
    """Two dense H19-5-like rows plus a distant unused ridge row, one catalogue pixel."""
    h, w = 80, 200
    foot = np.ones((h, w), dtype=bool)
    cat = np.zeros((h, w), dtype=bool)
    cat[0, 0] = True
    edt_cat = ndi.distance_transform_edt(~cat)
    occupied = np.zeros((h, w), dtype=bool)
    for row in (20, 24):
        for col in range(20, 100, 3):
            occupied[row, col] = True
    free_surface = np.zeros((h, w), dtype=bool)
    for row in (50, 54, 58):
        for col in range(120, 190):
            free_surface[row, col] = True
    return foot, cat, edt_cat, occupied, free_surface


def test_source_order_pops_densest_block_lowest_credit_first():
    """The removal rule must be the merged cvband rule: densest block, lowest unique credit.

    Equivalence with the merged implementation is proven end to end by the
    builder's byte-exact reproduction of the merged b5km-cvband-down4 file
    (``merged_arm_reproduction.matched`` in the evidence card, asserted below);
    this unit test pins the two ordering properties that make it that rule.
    """
    h, w = 80, 120
    foot = np.ones((h, w), dtype=bool)
    a_rows, a_cols = [], []
    for i, col in enumerate(range(20, 26)):      # 6 dots, densest 1 km block
        a_rows.append(20)
        a_cols.append(col)
    b_rows, b_cols = [40, 40, 40], [40, 41, 42]  # 3 dots, sparser block
    parent = np.zeros((h, w), dtype=bool)
    parent[a_rows, a_cols] = True
    parent[b_rows, b_cols] = True
    credits = np.array([5.0, 4.0, 3.0, 2.0, 1.0, 0.0, 9.0, 9.0, 9.0])
    order = SE.redundant_source_order(parent, foot, n_max=9, unique_credit_dots=credits)
    # The denser block is drained to its 3-dot floor first, lowest unique credit first;
    # the sparser block then contributes its own lowest-credit dot and the walk stops.
    assert [tuple(x) for x in order] == [(20, 25), (20, 24), (20, 23), (20, 22), (40, 40)]
    # A 1-2 dot block is never drained, so the walk can never empty a block.
    assert SE.redundant_source_order(parent, foot, n_max=9, unique_credit_dots=credits).shape[0] == 5


def test_source_order_is_dose_independent():
    foot, _, _, parent, _ = _synthetic_case()
    short = SE.redundant_source_order(parent, foot, n_max=5)
    long = SE.redundant_source_order(parent, foot, n_max=11)
    assert np.array_equal(short, long[:5])


def test_relocation_constraints_and_count():
    foot, cat, edt_cat, parent, free_surface = _synthetic_case()
    n_move = 6
    dots, src, dst, st = SE.relocate_surface_extension(
        parent, foot, edt_cat, free_surface, n_move=n_move)
    assert st["count_fixed"] and st["n_dots"] == int(parent.sum())
    assert st["n_added"] == st["n_removed"] == n_move
    added = dots & ~parent
    assert np.all(free_surface[added])
    assert float(edt_cat[added].min()) > 3.0
    assert st["min_pair_distance_variant_px"] >= st["min_pair_distance_parent_px"] - 1e-6
    assert not np.any(dots & cat)


def test_destination_capacity_raises_instead_of_silently_shrinking():
    foot, cat, edt_cat, parent, free_surface = _synthetic_case()
    with pytest.raises(ValueError, match="capacity|available"):
        SE.relocate_surface_extension(parent, foot, edt_cat, free_surface, n_move=5000)


def test_random_order_control_keeps_sources_and_leaves_the_surface():
    foot, cat, edt_cat, parent, free_surface = _synthetic_case()
    n_move = 6
    _, src_t, dst_t, _ = SE.relocate_surface_extension(
        parent, foot, edt_cat, free_surface, n_move=n_move)
    control_dest = np.ones_like(free_surface, dtype=bool) & ~free_surface & ~parent
    ctl, src_c, dst_c, st = SE.relocate_surface_extension(
        parent, foot, edt_cat, control_dest, n_move=n_move, order_seed=86)
    assert np.array_equal(src_t, src_c)
    assert not np.any(free_surface[ctl & ~parent])
    assert st["added_on_destination_surface_fraction"] == 1.0
    assert st["count_fixed"]


def test_determinism():
    foot, cat, edt_cat, parent, free_surface = _synthetic_case()
    a = SE.relocate_surface_extension(parent, foot, edt_cat, free_surface, n_move=5)[0]
    b = SE.relocate_surface_extension(parent, foot, edt_cat, free_surface, n_move=5)[0]
    assert np.array_equal(a, b)


@pytest.mark.skipif(not EVIDENCE.is_file(), reason="session evidence card absent")
def test_evidence_card_brackets_and_controls():
    card = json.loads(EVIDENCE.read_text())
    assert card["axis"] == "CONCENTRATION"
    audit = card["surface_capacity_audit"]
    assert audit["parent_dots_on_off5"] == 0
    assert audit["free_slots_on_off5"] > 4000
    assert card["merged_arm_reproduction"]["matched"] is True
    model = card["report_only_instruments"]["sgmc_model"]
    proxy = card["report_only_instruments"]["hide_and_recover_proxy"]["arms"]
    for value in VALUES:
        assert value in model and value in proxy
        assert model[value]["sign_replication"]["n_quadrants"] == 4
        # Report-only instruments must stay inside the |0.01| evidence floor.
        assert abs(model[value]["all"]["delta"]) < 0.02
        assert abs(proxy[value]["delta_vs_R0"]) < 0.01
    # The matched control must be strictly weaker than the treatment on both instruments,
    # otherwise the ridge attribution is not supported and the card has to be rewritten.
    ctl = "b5km-surfext-down10-randdst"
    assert model["b5km-surfext-down10"]["all"]["delta"] > model[ctl]["all"]["delta"]
    assert proxy["b5km-surfext-down10"]["delta_vs_R0"] > proxy[ctl]["delta_vs_R0"]
    assert "instrument_confound" in card and "live_credit_budget_projection" in card


@pytest.mark.skipif(not VARIANTS_JSON.is_file(), reason="session ledger source absent")
def test_ledger_rows_are_recorded_and_hash_unique():
    rows = json.loads(VARIANTS_JSON.read_text())
    assert {r["value"] for r in rows} == set(VALUES)
    ledger = list(csv.DictReader(LEDGER_CSV.open(newline="", encoding="utf-8")))
    known = [r["sha256"] for r in ledger if r.get("sha256")]
    for row in rows:
        assert row["pct_changed"] <= 50.0
        assert row["n_dots"] == 37654
        known = [r["sha256"] for r in ledger
                 if r.get("sha256") and r.get("id") != row["id"]]
        assert row["sha256_zeros"] not in known, f"{row['value']} duplicates an existing sha256"
        matching = [r for r in ledger if r.get("id") == row["id"]]
        assert matching, f"{row['id']} missing from ledger/submissions.csv"
        assert matching[0]["value"] == row["value"]


@pytest.mark.skipif(not EVIDENCE.is_file(), reason="session evidence card absent")
def test_written_twins_re_read_from_disk():
    import rasterio

    card = json.loads(EVIDENCE.read_text())
    sample = ROOT / "data" / "bridge" / "sample_submission.tif"
    with rasterio.open(sample) as src:
        footprint = np.isfinite(src.read(1))
    with rasterio.open(ROOT / "data" / "bridge" / "existing_faults.tif") as src:
        catalogue = src.read(1) > 0
    for receipt in card["variants"]:
        for encoding in ("zeros", "nan"):
            path = RELEASES / receipt[encoding]["file"]
            if not path.is_file():
                pytest.skip("local release TIFF is gitignored and not present in this checkout")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == receipt[encoding]["sha256"]
            with rasterio.open(path) as src:
                arr = src.read(1)
                assert src.count == 1 and src.dtypes[0] == "float32"
                assert str(src.crs).endswith("32611")
            assert not np.any((np.nan_to_num(arr, nan=0.0) > 0) & catalogue)
            assert float(np.nanmax(np.where(footprint, arr, 0.0))) <= 1.0
