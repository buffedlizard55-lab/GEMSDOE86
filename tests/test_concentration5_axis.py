"""Synthetic and receipt tests for the 5 km CONCENTRATION dose ladder."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems86 import concentration5 as C5  # noqa: E402
from gems86_axis import variants  # noqa: E402


@pytest.fixture(scope="module")
def synthetic():
    shape = (100, 100)
    foot = np.ones(shape, bool)
    cat = np.zeros(shape, bool)
    cat[10:90, 50] = True
    edt = ndi.distance_transform_edt(~cat)
    parent = np.zeros(shape, bool)
    for r in range(3, 100, 6):
        for c in range(3, 100, 6):
            if edt[r, c] > 2.0:
                parent[r, c] = True
    # Four contrasting 5 km blocks.  This is a prior input, not a truth raster.
    tmi = np.zeros(shape, np.float32)
    tmi[:50, :50] = 0.1
    tmi[:50, 50:] = 0.8
    tmi[50:, :50] = 0.3
    tmi[50:, 50:] = 1.2
    ctx = {"footprint": foot, "catalogue": cat}
    prior_pack = C5.make_prior(ctx, tmi)
    return parent, ctx, prior_pack


def test_all_doses_hold_count_dose_exclusions_and_prior_direction(synthetic):
    parent, ctx, prior_pack = synthetic
    dropped = {}
    for frac in C5.DOSES:
        value = C5.value_for(frac)
        mask, st = C5.build(parent, ctx, prior_pack["prior"], frac)
        diff = variants.parent_diff(parent, mask, ctx["footprint"])
        assert int(mask.sum()) == int(parent.sum())
        assert st["moved_placed"] == st["moved_target"] == round(frac * int(parent.sum()))
        assert diff["dropped"] == diff["added"] == st["moved_placed"]
        assert st["placed_at_relaxed_spacing"] == 0
        assert st["pct_parent_dots_moved"] == pytest.approx(100 * frac, abs=0.25)  # integer-dose rounding
        assert 1 <= diff["pct_changed_of_parent"] <= 50
        assert not (mask & ctx["catalogue"]).any()
        clearance = C5.new_mass_clearance(parent, mask, ctx["catalogue"])
        assert clearance["passed"] and clearance["minimum_px"] > 3.0
        separation = C5.prior_separation(parent, mask, prior_pack["prior"])
        assert separation["passed"] and separation["destination_minus_source"] > 0
        density = C5.density_report(parent, mask, ctx["footprint"])
        assert set(density) == {"1000m", "5000m"}
        assert density["5000m"]["variant"]["density_cv_occupied"] > 0
        dropped[value] = parent & ~mask
    values = tuple(C5.value_for(f) for f in C5.DOSES)
    for a, b in zip(values, values[1:]):
        assert not (dropped[a] & ~dropped[b]).any(), "source doses must be nested"


def test_unregistered_dose_fails_closed(synthetic):
    parent, ctx, prior_pack = synthetic
    with pytest.raises(ValueError, match="unregistered dose"):
        C5.build(parent, ctx, prior_pack["prior"], 0.05)


def test_truth_translation_has_no_wraparound():
    truth = np.zeros((6, 7), bool)
    truth[0, 6] = True
    truth[2, 3] = True
    shifted = C5.shift_truth(truth, -2, 1)
    assert shifted[0, 4]                       # the interior point moved (2,3)->(0,4)
    assert not shifted[0, 6]                   # source cleared
    assert int(shifted.sum()) == 1             # edge point fell off, never wrapped
    assert not C5.shift_truth(truth, 20, 0).any()


def test_preflight_receipt_is_byte_exact():
    receipt = json.loads((ROOT / "evidence/r0_preflight_20261023.json").read_text())
    assert receipt["status"] == "PASS"
    assert receipt["r0"]["byte_exact"]
    assert receipt["r0"]["differing_cells"] == 0
    assert receipt["r0"]["rebuilt_dots"] == 37654
    assert receipt["r0"]["rebuilt_sha256"] == \
        "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"


VARIANTS = ROOT / "ledger/variants_concentration5.json"
RUN_CARD = ROOT / "evidence/concentration5_axis_20261023.json"


@pytest.mark.skipif(not VARIANTS.is_file(), reason="5 km rasters not built in this checkout")
def test_release_receipt_schema_and_unique_axis_values():
    entries = json.loads(VARIANTS.read_text())
    assert len(entries) == 3
    assert {e["value"] for e in entries} == set(C5.value_for(f) for f in C5.DOSES)
    assert len({(e["parent"], e["axis"], e["value"]) for e in entries}) == 3
    assert len({e["sha256"] for e in entries} | {e["sha256_zeros"] for e in entries}) == 6
    for entry in entries:
        assert entry["status"] == "BUILT"
        assert entry["gates_passed"]
        assert entry["n_dots"] == 37654
        assert 1 <= entry["pct_changed"] <= 50
        assert len(entry["sha256"]) == len(entry["sha256_zeros"]) == 64
        assert entry["blocks"]["block_size"].startswith("5000 m")
        assert entry["blocks"]["min_cat_edt_px_new_mass"] > 3.0
        assert entry["diff"]["count_exact"]
        assert not entry["approved_for_weekly_slot"]


@pytest.mark.skipif(not RUN_CARD.is_file(), reason="5 km run card not built in this checkout")
def test_run_card_labels_and_report_only_instruments():
    card = json.loads(RUN_CARD.read_text())
    assert card["session_axis"] == "CONCENTRATION"
    assert card["no_submission"]
    assert card["parent"]["rebuild"]["byte_exact"]
    assert card["instruments"]["leakage_canary"]["max_auc"] <= 0.90
    proxy = card["instruments"]["catalogue_hide_recover_proxy"]
    assert proxy["evidence_class"] == "PROXY" and "REPORT-ONLY" in proxy["status"]
    for score in proxy["scores"].values():
        assert score["withheld_positive_pixels"] > 0
        assert len(score["ci95"]) == 2
    assert card["instruments"]["sgmc_offcatalogue_surrogate"]["evidence_class"] == "MODEL"
    for variant in card["variants"]:
        assert variant["evidence_class"] == "MODEL"
        assert variant["note_chars"] == len(variant["note"]) <= 140
        assert variant["submission_slots_used"] == 0
