"""Unit tests for the TRACKB geometry (``src/gems86/trackb.py``).

The two defects this session actually hit are regression-tested explicitly:

* ``dot_support``/``trace_runs`` once returned indices into the dot *list* instead
  of flat raster cells, which scattered the support field over empty cells
  (silently: every shape check still passed);
* ``select_donors`` once accepted ``support >= 0`` as the dot mask, which is true
  for every cell of the raster, so the "donors" were mostly empty cells and the
  count-fixed gate fired (IR-86-TRACKB-02).

No test here reads competition truth; the fixtures are synthetic rasters.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.gems86 import trackb as TB  # noqa: E402


def _diagonal_field(length: int = 14, shape: tuple[int, int] = (40, 40)) -> np.ndarray:
    """Dots on an east-west line, spaced 2 px apart -- just like the parent.

    East-west is used because the detector's strike bins are multiples of 10
    degrees: a 45-degree fixture would fall *between* bins and its dots would
    wander out of the +/-0.75 px corridor, which is correct behaviour but a poor
    fixture (it was this session's first, wrong, test).
    """
    dots = np.zeros(shape, bool)
    row = 5
    for i in range(length):
        dots[row, 4 + 2 * i] = True
    return dots


def test_strike_azimuth_convention():
    # +x (east) -> 090, +y (down/south) -> 000, NW-SE diagonal -> 135
    assert TB.strike_azimuth(0.0) == pytest.approx(90.0)
    assert TB.strike_azimuth(90.0) == pytest.approx(0.0)
    assert TB.strike_azimuth(45.0) == pytest.approx(45.0)
    assert TB.strike_azimuth(135.0) == pytest.approx(135.0)


def test_trace_runs_find_a_straight_line():
    dots = _diagonal_field()
    runs = TB.trace_runs(dots)
    assert runs, "a 14-dot diagonal line must produce at least one run"
    longest = max(r["length_px"] for r in runs)
    assert longest >= 20.0                      # 13 gaps of 2 px, plus 1
    run = max(runs, key=lambda r: r["length_px"])
    assert run["theta_deg"] == pytest.approx(0.0)
    assert run["dot_flat"].size == 14


def test_dot_support_lands_on_dots_only():
    """Regression: support must be non-zero on the line's cells and nowhere else."""
    dots = _diagonal_field()
    runs = TB.trace_runs(dots)
    support = TB.dot_support(dots, runs)
    assert support.shape == dots.shape
    assert int((support > 0).sum()) == int(dots.sum())
    assert not np.any(support[~dots])


def test_trace_table_length_filter_and_dedupe():
    dots = _diagonal_field()
    runs = TB.trace_runs(dots)
    long_only = TB.trace_table(dots, runs, min_len_px=20.0)
    assert len(long_only) == 1                  # one physical line, one trace
    assert long_only[0]["n_dots"] == 14
    assert TB.trace_table(dots, runs, min_len_px=10_000.0) == []


def test_select_donors_only_returns_dots():
    """Regression: donors are dots, never empty cells (IR-86-TRACKB-02)."""
    dots = _diagonal_field()
    support = np.zeros(dots.shape, float)
    donors = TB.select_donors(dots, support, 5)
    assert int(donors.sum()) == 5
    assert not np.any(donors & ~dots)
    with pytest.raises(ValueError):
        TB.select_donors(dots, support, int(dots.sum()) + 1)


def test_plan_extension_respects_collar_and_spacing():
    dots = _diagonal_field(length=8)
    runs = TB.trace_runs(dots)
    traces = TB.trace_table(dots, runs, min_len_px=10.0)
    footprint = np.ones(dots.shape, bool)
    distance = np.full(dots.shape, 99.0)
    # put a catalogue block just past the line's lower end so the walk must stop
    distance[:, 30:] = 1.0
    added, stats = TB.plan_extension(dots, traces, footprint, distance, n_add=50)
    assert stats["requested_added"] == 50
    assert int(added.sum()) == stats["added"] <= 50
    assert not np.any(added & dots)
    assert distance[added].min() > TB.CLEARANCE_PX
    # no new cell may sit inside the parent's own dot separation
    both = np.argwhere(added | dots)
    for row, col in np.argwhere(added):
        gaps = np.hypot(both[:, 0] - row, both[:, 1] - col)
        gaps = gaps[gaps > 0]
        assert gaps.min() >= TB.MIN_SEP_PX - 1e-9


def test_apply_swap_is_count_fixed():
    dots = _diagonal_field()
    remove = np.zeros(dots.shape, bool)
    remove[5, 4] = True
    add = np.zeros(dots.shape, bool)
    add[30, 30] = True
    child = TB.apply_swap(dots, remove, add)
    assert int(child.sum()) == int(dots.sum())
    assert child[30, 30] and not child[5, 4]
    with pytest.raises(ValueError):
        TB.apply_swap(dots, remove, np.zeros(dots.shape, bool))
    with pytest.raises(ValueError):
        TB.apply_swap(dots, dots & add, add)


def test_diff_stats_and_broken_traces():
    dots = _diagonal_field()
    child = dots.copy()
    child[5, 4] = False
    child[20, 20] = True
    diff = TB.diff_stats(dots, child)
    assert diff["count_fixed"] and diff["removed"] == 1 and diff["added"] == 1
    assert diff["pct_changed"] == pytest.approx(200.0 / int(dots.sum()), abs=1e-3)  # rounded to 4 dp
    runs = TB.trace_runs(dots)
    traces = TB.trace_table(dots, runs, min_len_px=10.0)
    broken = TB.broken_traces(traces, child)
    assert broken["dots_lost_from_traces"] == 1


def test_geojson_and_paragraph_are_deterministic():
    dots = _diagonal_field()
    runs = TB.trace_runs(dots)
    traces = TB.trace_table(dots, runs, min_len_px=10.0)
    distance = np.full(dots.shape, 7.0)
    from rasterio.transform import Affine
    transform = Affine(100.0, 0.0, 0.0, 0.0, -100.0, 4000.0)
    first = TB.traces_to_geojson(traces, {0: 3}, transform, "EPSG:32611", distance)
    second = TB.traces_to_geojson(traces, {0: 3}, transform, "EPSG:32611", distance)
    assert first == second
    feature = first["features"][0]
    assert feature["geometry"]["type"] == "LineString"
    assert feature["properties"]["strike_azimuth_deg"] == pytest.approx(90.0)
    assert "Falsifier" in feature["properties"]["evidence_paragraph"]
    assert feature["properties"]["dots_added_by_this_edit"] == 3
