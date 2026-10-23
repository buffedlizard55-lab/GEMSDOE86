"""Tests for the CONCENTRATION knob session (2026-10-23).

Three things are locked here, because they are the claims a reader cannot re-derive from the prose:

1. **Single-knob design.** Each arm differs from the already-spent setting
   (``b1km-move15``: block 10 px, move 0.15, dest_frac 0.20) in exactly one of the three knobs.
   If two knobs changed, a live difference between two arms would not be attributable.
2. **The brief's non-SNAP band.** Every non-SNAP variant changes 1-50 % of the parent's dots.
3. **The prior decomposition is honest.** ``single_term_prior`` reproduces each term of
   ``variants.block_prior`` on a small grid, so the catalogue-only / TMI-only arms really are the
   two halves of the mixed prior and not a different construction.

The on-disk release checks skip cleanly when the (gitignored) TIFFs are absent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems86_axis import variants  # noqa: E402

BUILD = ROOT / "scripts" / "build_concentration_knobs.py"
ENTRIES = ROOT / "ledger" / "variants_concentration_knobs.json"
RUN_CARD = ROOT / "evidence" / "concentration_knobs_20261023.json"


def _specs() -> list[dict]:
    """The build script's VARIANTS list, imported without running main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_concentration_knobs", BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.VARIANTS


SPENT = {"block_px": 10, "move": 0.15, "dest_frac": 0.20}
SPECS = _specs()


def test_three_variants_and_distinct_values():
    assert len(SPECS) == 3
    assert len({s["value"] for s in SPECS}) == 3
    assert len({s["token"] for s in SPECS}) == 3
    assert not any(s["value"] == "b1km-move15" for s in SPECS), "the spent setting must not be rebuilt"


@pytest.mark.parametrize("spec", SPECS, ids=[s["token"] for s in SPECS])
def test_exactly_one_knob_moves_off_the_spent_setting(spec):
    changed = [k for k in SPENT if spec[k] != SPENT[k]]
    assert len(changed) == 1, f"{spec['token']} changes {changed}; the design is single-knob"


def test_non_snap_change_band_is_respected_by_design():
    """A move of fraction f changes 2f of the dots; the brief allows 1-50 %."""
    for spec in SPECS:
        assert 0.01 <= 2 * spec["move"] <= 0.50 + 1e-12, spec["token"]


def test_predictions_are_model_class_and_inside_the_evidence_band():
    for spec in SPECS:
        assert spec["predicted_change"] == 0 or abs(spec["predicted_change"]) < 0.01
        lo, hi = spec["predicted_range"]
        assert lo <= spec["predicted_change"] <= hi
        assert lo > -0.02 and hi < 0.02, "this axis must not claim a large effect"


# ------------------------------------------------------------------ prior decomposition

def _toy_ctx(seed=0):
    rng = np.random.default_rng(seed)
    footprint = np.zeros((60, 60), bool)
    footprint[5:55, 5:55] = True
    catalogue = np.zeros_like(footprint)
    catalogue[10:50, 30:32] = True
    catalogue[30:32, 10:50] = True
    catalogue &= footprint
    tmi = rng.random((60, 60)).astype(np.float32)
    bands = {"tmi_up150": tmi, "tmi_grad": variants.__dict__.get("np") and
             np.abs(np.gradient(tmi)[0]) + np.abs(np.gradient(tmi)[1])}
    return {"footprint": footprint, "catalogue": catalogue, "grid": {"shape": footprint.shape}}, bands


def test_single_term_priors_sum_to_the_mixed_prior():
    """mixed prior == z(cat) + z(tmi) block-by-block, up to float32 rounding."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "measure_concentration_instruments",
        ROOT / "scripts" / "measure_concentration_instruments.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ctx, bands = _toy_ctx()
    mixed = variants.block_prior(ctx, bands, ctx["catalogue"], block_px=10)["prior"]
    single = (mod.single_term_prior(ctx, bands, ctx["catalogue"], 10, "cat")
              + mod.single_term_prior(ctx, bands, ctx["catalogue"], 10, "tmi"))
    finite = np.isfinite(mixed)
    assert np.array_equal(finite, np.isfinite(single))
    assert np.allclose(mixed[finite], single[finite], atol=1e-5)


def test_shuffled_prior_preserves_the_multiset_and_the_footprint_mask():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "measure_concentration_instruments",
        ROOT / "scripts" / "measure_concentration_instruments.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ctx, bands = _toy_ctx()
    pack = variants.block_prior(ctx, bands, ctx["catalogue"], block_px=10)
    prior = pack["prior"]
    shuffled = mod.shuffled_prior(prior, pack["footprint_blocks"])
    finite = np.isfinite(prior)
    assert np.array_equal(finite, np.isfinite(shuffled))
    assert np.allclose(np.sort(prior[finite]), np.sort(shuffled[finite]))
    assert not np.allclose(prior[finite], shuffled[finite]), "the shuffle must actually move values"


# ------------------------------------------------------------------ on-disk artifacts

HAS_TIFFS = ENTRIES.is_file() and RUN_CARD.is_file() and (
    ROOT / "releases" / "axis86").is_dir() and bool(list((ROOT / "releases" / "axis86").glob("gems86-h33-2b2-conc*.tif")))
needs_tiffs = pytest.mark.skipif(not HAS_TIFFS, reason="release TIFFs are gitignored / absent")


@needs_tiffs
def test_ledger_entries_carry_the_preregistration_trail():
    entries = json.loads(ENTRIES.read_text())
    assert len(entries) == 3
    statuses = [e["status"] for e in entries]
    assert statuses.count("BUILT") == 2 and statuses.count("BUILT-DUPLICATE") == 1
    for e in entries:
        assert e["status"] in ("BUILT", "BUILT-DUPLICATE")
        if e["status"] == "BUILT-DUPLICATE":
            assert e["duplicate_of"], "a duplicate must say what it duplicates"
        assert e["parent"] == "h33-h33-2-b2"
        assert e["gates_passed"] is True
        assert 1.0 <= float(e["pct_changed"]) <= 50.0
        assert e["preregistered_change"] is not None
        assert "MODEL" in e["predicted_change"]
        assert e["report_only_proxy"]["evidence_class"] == "PROXY"
        assert e["blocks"]["moved"] == e["blocks"]["moved_target"], "no placement shortfall allowed"
        assert len(e["sha256"]) == 64 and len(e["sha256_zeros"]) == 64


@needs_tiffs
def test_release_files_pass_the_hard_gates_and_keep_the_parent_geometry():
    from gems86_axis import gates, grid_io

    ctx = grid_io.load_context()
    parent = grid_io.load_dots(ROOT / ("data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-"
                                       "20261004T220000Z-e5eb6e7e-zeros.tif"), ctx["footprint"])
    entries = json.loads(ENTRIES.read_text())
    known: set[str] = set()
    for e in entries:
        for suffix in ("", "-zeros"):
            path = ROOT / "releases" / "axis86" / f"{e['id']}{suffix}.tif"
            assert path.is_file(), path
            res = gates.run_all(path, ctx, known, grid_io.PARENT_CAT_CLEARANCE_PX)
            assert res["passed"], (path.name, {k: v for k, v in res.items() if k == "values"})
            known.add(res["sha256"])
            dots = grid_io.load_dots(path, ctx["footprint"])
            assert int(dots.sum()) == int(parent.sum()), "count must be fixed on this axis"


@needs_tiffs
def test_notes_fit_the_form():
    entries = json.loads(ENTRIES.read_text())
    for e in entries:
        note = json.loads((ROOT / "releases" / "axis86" / f"{e['id']}-zeros.json").read_text())
        text = note.get("note") or note.get("GEMS_NOTE") or ""
        assert 0 < len(text) <= 140, (e["id"], len(text))


@needs_tiffs
def test_every_arm_changed_something_and_no_arm_is_a_duplicate_digest():
    entries = json.loads(ENTRIES.read_text())
    digests = [e["sha256_zeros"] for e in entries]
    assert len(set(digests)) == len(digests)
    for e in entries:
        assert e["diff"]["removed"] > 0 and e["diff"]["added"] > 0
        assert e["diff"]["count_exact"] is True
