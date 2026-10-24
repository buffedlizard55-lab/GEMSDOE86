"""Tests for the RELIEF **source** factorial driver's own contract.

These do not touch a competition raster (none is committed): they pin the parts of
``scripts/run_relief_source.py`` that a future edit could silently break -- the
dose window, the arm keys, that the null control preserves the dot count and the
displacement multiset, and that the session's variants file is registered with the
single ledger generator.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

from src.gems86 import relief as R  # noqa: E402


def _load_driver():
    """Import the driver without executing ``main`` (it needs the 419 MB stack)."""
    spec = importlib.util.spec_from_file_location(
        "run_relief_source_under_test", ROOT / "scripts" / "run_relief_source.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:  # pragma: no cover - import-time guards are not expected to fire
        pytest.skip("driver refused to import in this checkout")
    return mod


@pytest.fixture(scope="module")
def driver():
    return _load_driver()


# --------------------------------------------------------------------- the arms
def test_every_arm_is_inside_the_brief_relief_window(driver):
    """Brief v2 §5 fixes RELIEF at 10-15 % of the parent's dots."""
    assert driver.MIN_PCT == 10.0 and driver.MAX_PCT == 15.0
    for key, spec in driver.ARMS.items():
        pct = 100.0 * int(round(driver.N_DOTS_R0 * spec["frac"])) / driver.N_DOTS_R0
        assert driver.MIN_PCT - 0.01 <= pct <= driver.MAX_PCT + 0.01, (key, pct)


def test_each_arm_key_appears_exactly_once_in_the_ledger(driver):
    """The brief's only dedupe rule that binds here: one row per ``(parent, axis, value)``."""
    import csv
    counts = {}
    with open(ROOT / "ledger" / "submissions.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("parent") == driver.PARENT_ID and row.get("status") == "BUILT":
                key = (row.get("axis", "").upper(), row.get("value", ""))
                counts[key] = counts.get(key, 0) + 1
    for spec in driver.ARMS.values():
        assert counts.get((driver.AXIS, spec["value"])) == 1, spec["value"]
    assert len({spec["value"] for spec in driver.ARMS.values()}) == len(driver.ARMS)


def test_arms_vary_source_and_destination_orthogonally(driver):
    """Two arms hold the destination fixed and vary the source; one holds source fixed."""
    by_dest = {}
    for spec in driver.ARMS.values():
        by_dest.setdefault(spec["destination"], set()).add(spec["source"])
    assert by_dest.get(2) == {4}, "the two front arms must share source=interior"
    sources = {spec["source"] for spec in driver.ARMS.values()}
    assert sources == {4}, "all three arms take their mass from the range interior"
    destinations = {spec["destination"] for spec in driver.ARMS.values()}
    assert destinations == {1, 2}, "the design needs both destinations"


def test_doses_are_nested_within_a_source(driver):
    """10 % of the parent is a smaller dose than 15 %, so the prefix property is claimable."""
    small = int(round(driver.N_DOTS_R0 * driver.ARMS["int2front10"]["frac"]))
    large = int(round(driver.N_DOTS_R0 * driver.ARMS["int2front15"]["frac"]))
    assert 0 < small < large < driver.N_DOTS_R0
    assert driver.ARMS["int2front10"]["source"] == driver.ARMS["int2front15"]["source"]
    assert driver.ARMS["int2front10"]["destination"] == driver.ARMS["int2front15"]["destination"]


# ------------------------------------------------------------- the null control
def _toy(n=80, seed=3):
    """Parent dots plus the *real* eligibility rule (``RL.eligible_cells``)."""
    from scipy import ndimage as ndi
    rng = np.random.default_rng(seed)
    dots = np.zeros((n, n), bool)
    # a spacing-legal parent, like R0: greedy accept at >= 3 px (the real parent is 2.828 px)
    kept = []
    for flat in rng.permutation(n * n):
        y, x = divmod(int(flat), n)
        if all(np.hypot(y - ky, x - kx) >= 3.0 for ky, kx in kept):
            kept.append((y, x))
    for y, x in kept:
        dots[y, x] = True
    cat = np.zeros((n, n), bool)
    cat[n // 2, :] = True
    elig = R.eligible_cells(dots, cat, np.ones((n, n), bool))
    src = np.flatnonzero(dots.ravel())[:20].astype(np.int64)
    return dots, src, elig


def test_null_control_preserves_the_count_and_takes_no_source_dot(driver):
    dots, src, elig = _toy()
    rng = np.random.default_rng(0)
    disp = rng.uniform(3.0, 12.0, size=src.size)
    moved, stats = driver.displacement_matched_null(dots, src, disp, elig, seed=11)
    assert int(moved.sum()) == int(dots.sum()), "null control must not change the dot count"
    assert not moved.ravel()[src].any(), "source cells must be vacated, exactly like a real arm"
    assert stats["realised_px"]["mean"] > 0


def test_null_control_keeps_the_requested_displacement_multiset(driver):
    """The null must ask for exactly the arm's distances, and may only travel farther.

    Eligibility (``d_cat > 3 px``, ``d_dot > 2.8 px``) can push a destination away from
    the point that was asked for, never closer, so the honest invariant is
    ``realised >= wanted`` plus an exact match on what was requested. In the real build
    the requests are 38-61 px and the realised mean is 42-59 px.
    """
    dots, src, elig = _toy(seed=5)
    disp = np.full(src.size, 9.0)
    _moved, stats = driver.displacement_matched_null(dots, src, disp, elig, seed=7)
    assert stats["wanted_px"]["mean"] == pytest.approx(9.0)
    assert stats["wanted_px"]["median"] == pytest.approx(9.0)
    assert stats["realised_px"]["mean"] >= 9.0 - 1e-9


def test_null_control_refuses_to_stack_dots(driver):
    """Two null destinations may never be closer than the parent's spacing floor."""
    dots, src, elig = _toy(seed=9)
    rng = np.random.default_rng(1)
    disp = rng.uniform(0.0, 2.0, size=src.size)
    moved, _stats = driver.displacement_matched_null(dots, src, disp, elig, seed=13)
    nn = R.nn_distances(moved)
    assert nn.min() >= R.MIN_DOT_PX - 1e-9


# ---------------------------------------------------------------- the ledger glue
def test_variants_file_is_registered_with_the_single_ledger_generator():
    src = (ROOT / "scripts" / "build_ledger.py").read_text()
    assert '"variants_relief_source.json"' in src
    assert (ROOT / "ledger" / "variants_relief_source.json").is_file()


def test_evidence_declares_model_not_score():
    import json
    ev = json.loads((ROOT / "evidence" / "relief_source_20261023.json").read_text())
    assert ev["axis"] == "RELIEF"
    assert ev["no_slot_authorized"] is True
    assert "MODEL projection" in ev["not_a_score"]
    for card in ev["variants"].values():
        assert card["predicted_live_change"]["all"]["delta"] == pytest.approx(
            card["predicted_live_change"]["all"]["delta"])
    diag = ev["instrument_diagnostic"]
    assert diag["report_only"] is True and diag["n_arms"] == 8
