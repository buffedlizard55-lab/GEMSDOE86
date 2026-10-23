"""Unit tests for the gain-gated SNAP build (src/gems86/snap_gated.py; PR #31's
unconditional build is covered by tests/test_snap_axis.py) and its one released
file (snapr2g10; the r1/r2 arms are withdrawn duplicate pairs, IR-86-SNAP-05).

Synthetic checks on the rules -- count preservation, radius bound, eligibility,
gain gate, collision handling, determinism -- plus, when the gitignored release
TIFFs are present in the working tree, a re-derivation of every brief section-6
gate from the bytes on disk.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from src.gems86.snap_gated import percentile_ranks, snap_diff_stats, snap_dots, window_offsets

ROOT = Path(__file__).resolve().parents[1]
RELEASES = ROOT / "releases"


def _field():
    """One ridge of high edge values at column 12; dots scattered around it."""
    h = w = 30
    edge = np.zeros((h, w))
    edge[:, 12] = 1.0
    edge[:, 11] = edge[:, 13] = 0.5
    eligible = np.ones((h, w), bool)
    dots = np.zeros((h, w), bool)
    for y, x in [(5, 10), (8, 14), (11, 12), (15, 20), (20, 11), (25, 25)]:
        dots[y, x] = True
    return dots, edge, eligible


def test_window_offsets_are_euclidean():
    assert len(window_offsets(1.0)) == 5
    assert len(window_offsets(2.0)) == 13
    assert all(d <= 2.0 + 1e-9 for _, _, d in window_offsets(2.0))
    assert (2, 1) not in [(dy, dx) for dy, dx, _ in window_offsets(2.0)]  # sqrt5 > 2


def test_snap_preserves_count_and_respects_radius_and_eligibility():
    dots, edge, eligible = _field()
    eligible[:, 12] = False  # the crest itself is forbidden (e.g. catalogue)
    out, stats = snap_dots(dots, edge, eligible, radius=2.0)
    assert int(out.sum()) == int(dots.sum())
    assert not (out & ~eligible & ~dots).any()
    assert stats["max_displacement_px"] <= 2.0
    # dots at x=10/x=14 can reach the allowed 0.5 shoulders; far dots cannot gain
    assert out[5, 11] and out[8, 13]
    assert out[15, 20] and out[25, 25]
    # a dot already on the (ineligible) crest keeps its own cell as the fallback
    assert out[11, 12]


def test_snap_moves_toward_crest_and_gain_gate_filters_weak_moves():
    dots, edge, eligible = _field()
    out, _ = snap_dots(dots, edge, eligible, radius=2.0)
    assert out[5, 12] and out[8, 12] and out[20, 12]  # may collide-resolve below
    gated, st = snap_dots(dots, edge, eligible, radius=2.0, min_gain=0.75)
    # only gains of +1.0 (from a 0.0 cell to the crest) clear a 0.75 gate
    assert gated[5, 12] and gated[8, 12]
    assert gated[20, 11]  # +0.5 gain stays
    assert st["n_moved"] == 2


def test_snap_collisions_never_lose_a_dot():
    edge = np.zeros((9, 9))
    edge[4, 4] = 1.0
    eligible = np.ones((9, 9), bool)
    dots = np.zeros((9, 9), bool)
    dots[4, 3] = dots[4, 5] = dots[3, 4] = True  # all want (4,4)
    out, stats = snap_dots(dots, edge, eligible, radius=1.0)
    assert int(out.sum()) == 3
    assert out[4, 4]
    assert stats["n_moved"] == 1  # the two losers keep their reserved origins


def test_snap_invalid_origin_stays_and_is_deterministic():
    dots, edge, eligible = _field()
    edge[5, 10] = np.nan
    a, sta = snap_dots(dots, edge, eligible, radius=2.0)
    b, _ = snap_dots(dots, edge, eligible, radius=2.0)
    assert np.array_equal(a, b)
    assert a[5, 10]
    assert sta["n_origin_edge_invalid"] == 1


def test_percentile_ranks_cover_unit_interval():
    vals = np.arange(100, dtype=float).reshape(10, 10)
    valid = np.ones((10, 10), bool)
    valid[0, 0] = False
    r = percentile_ranks(vals, valid)
    assert np.isnan(r[0, 0])
    assert np.nanmin(r) == 0.0 and np.nanmax(r) == pytest.approx(1.0)


def test_snap_diff_stats_counts_relocations():
    p = np.zeros((5, 5), bool)
    p[1, 1] = p[3, 3] = True
    c = np.zeros((5, 5), bool)
    c[1, 2] = c[3, 3] = True
    d = snap_diff_stats(p, c)
    assert d["removed"] == d["added"] == 1
    assert d["pct_dots_moved"] == 50.0
    assert d["pct_of_parent_changed"] == 100.0  # changed cells over parent count


# -------------------------------------------------------------------- releases
def _snap_zeros() -> list[Path]:
    return sorted(RELEASES.glob("*-snapr2g10*-zeros.tif")) if RELEASES.is_dir() else []


@pytest.mark.skipif(not _snap_zeros(), reason="SNAP release TIFFs are gitignored / not built here")
def test_snap_releases_pass_brief_gates_and_match_receipts_and_ledger():
    import rasterio
    from scipy import ndimage as ndi

    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as s:
        footprint = np.isfinite(s.read(1))
        template = (str(s.crs), tuple(s.transform)[:6], (s.height, s.width))
    with rasterio.open(ROOT / "data" / "bridge" / "existing_faults.tif") as s:
        catalogue = (s.read(1) > 0) & footprint
    distance = ndi.distance_transform_edt(~catalogue)
    parent_path = (ROOT / "data" / "scored_fleet" /
                   "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
    with rasterio.open(parent_path) as s:
        parent = s.read(1) > 0
    ledger = {r["sha256"]: r for r in csv.DictReader(open(ROOT / "ledger" / "submissions.csv"))
              if r["sha256"]}

    seen = set()
    for zeros in _snap_zeros():
        receipt = json.loads(zeros.with_suffix(".json").read_text())
        digest = hashlib.sha256(zeros.read_bytes()).hexdigest()
        assert digest == receipt["zeros"]["sha256"] == digest  # file names embed this digest
        assert zeros.stem.endswith(digest[:8] + "-zeros")
        assert digest in ledger and ledger[digest]["axis"] == "SNAP"
        seen.add(digest)
        with rasterio.open(zeros) as s:
            a = s.read(1)
            assert (str(s.crs), tuple(s.transform)[:6], (s.height, s.width)) == template
            assert s.count == 1 and s.dtypes == ("float32",)
        dots = a > 0
        assert int(dots.sum()) == receipt["n_dots"] == int(parent.sum())  # count preserved
        assert not (dots & catalogue).any()
        assert distance[dots].min() > 2.0  # the parent's exclusion, kept (IR-86-SNAP-04)
        assert a[footprint].min() >= 0.0 and a[footprint].max() <= 1.0
        assert np.isfinite(a[footprint]).all() and (a[~footprint] == 0).all()
        # NaN twin: identical dots, NaN only outside the footprint
        with rasterio.open(RELEASES / zeros.name.replace("-zeros.tif", ".tif")) as s:
            nan = s.read(1)
        assert np.array_equal(np.nan_to_num(nan) > 0, dots)
        assert np.isnan(nan[~footprint]).all() and np.isfinite(nan[footprint]).all()
    assert len(seen) == len(_snap_zeros())
