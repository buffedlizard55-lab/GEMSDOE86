"""Axis contract for TRACKB (src/gems86/trackb.py), synthetic grids only."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems86 import trackb as TB  # noqa: E402


def line(n=14, step=3):
    m = np.zeros((30, 60), bool)
    m[15, 5:5 + step * n:step] = True
    return m


def test_straight_line_becomes_one_trace_over_1km():
    traces, st = TB.extract_traces(line(), 30.0)
    assert st["n_traces"] == 1 and traces[0]["length_px"] >= 10.0
    assert traces[0]["mean_turn_deg"] < 1.0 and traces[0]["n_dots"] == 14


def test_sharp_bend_splits_at_strict_ceiling():
    m = np.zeros((60, 60), bool)
    m[10, 5:35:3] = True            # east arm
    m[13:40:3, 32] = True           # south arm (90 deg bend)
    strict, _ = TB.extract_traces(m, 20.0)
    assert all(t["max_turn_deg_measured"] <= 20.0 + 1e-9 for t in strict)


def test_isolated_dots_form_no_trace():
    m = np.zeros((50, 50), bool)
    m[5, 5] = m[25, 25] = m[45, 45] = True
    traces, st = TB.extract_traces(m, 40.0)
    assert traces == [] and st["n_traced_dots"] == 0


def test_variants_differ_only_in_turn_ceiling():
    m = line()
    a, _ = TB.extract_traces(m, 20.0)
    b, _ = TB.extract_traces(m, 40.0)
    assert [t["dot_indices"] for t in a] == [t["dot_indices"] for t in b]


def test_rasterize_drops_new_mass_inside_clearance():
    shape = (30, 60)
    m = line()
    pts = TB.dot_points(m)
    traces, _ = TB.extract_traces(m, 30.0)
    edt = np.full(shape, 99.0)
    edt[:, 25:28] = 1.0             # catalogue wall the segment must not paint
    foot = np.ones(shape, bool)
    out, st = TB.rasterize(traces, pts, shape, edt, foot)
    assert st["new_segment_px_dropped_clearance"] > 0
    assert not out[:, 25:28][~m[:, 25:28]].any()  # only inherited member dots may remain
    assert out[m].all()             # member dots always kept
