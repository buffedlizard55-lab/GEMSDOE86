"""Unit tests for the pediment-window CONCENTRATION arms (pre-registered proposal #2)."""
from __future__ import annotations

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
from gems86 import concentration_pediment as CP  # noqa: E402


def _grid_with_pediment(h=60, w=140):
    """Footprint + catalogue + ridge + a left/right pediment split for tests."""
    foot = np.ones((h, w), dtype=bool)
    cat = np.zeros((h, w), dtype=bool)
    cat[0, 0] = True
    edt_cat = ndi.distance_transform_edt(~cat)

    parent = np.zeros((h, w), dtype=bool)
    ridge = np.zeros((h, w), dtype=bool)
    # Over-pack two 10x10 blocks with 4 dots each (the shave sources)
    for br, bc in ((10, 10), (10, 30)):
        for dr, dc in ((1, 1), (1, 5), (5, 1), (5, 5)):
            parent[br + dr, bc + dc] = True
            ridge[br + dr, bc + dc] = True
    # Sparse 1-dot blocks with unused ridge capacity on both halves
    for idx, bc in enumerate((50, 60, 70)):
        for br in (10, 25):
            parent[br + 2, bc + 1] = True
            ridge[br + 2, bc + 1 : bc + 9] = True
    # Pediment: a "range front" column at x=40 and low-relief cols x>50 only
    ped = np.zeros((h, w), dtype=bool)
    ped[:, 50:] = True
    return foot, cat, edt_cat, parent, ridge, ped


def test_pediment_window_is_truthfree_and_bounds_respected():
    foot = np.ones((30, 40), dtype=bool)
    rl = np.full((30, 40), 5.0)
    rl[:, 20:] = 25.0        # pediment band on the right half
    front = np.zeros((30, 40), dtype=bool)
    front[:, 15] = True      # range-front column
    ped, info = CP.pediment_window(rl, front, foot, relief_lo_m=10, relief_hi_m=40, front_dist_px=10)
    assert ped[:, :21].sum() == 0          # within 10 px of the front -> excluded
    assert ped[:, 26:].all()               # beyond the front distance, in-band
    assert info["truth_inputs_used"] == "NONE (mask is fold-fair by construction)"
    assert 0.0 < info["pct_footprint"] <= 1.0

    with pytest.raises(ValueError, match="non-finite"):
        bad = rl.copy()
        bad[5, 5] = np.nan
        CP.pediment_window(bad, front, foot)


def _separated_grid(h=40, w=90):
    """Grid whose six sparse-block candidates are isolated, so destination order is
    hand-computable and spacing never binds.

    Parent: two 6-dot dense blocks at (10..18, 11..18) and (10..18, 31..38).
    One single-dot sparse block per candidate cell, its dot 5.83 px away, so every
    candidate's post-shave gap is identical (5.83) and the scan order falls through
    to (row, col): (12,52),(12,62),(12,72),(27,52),(27,62),(27,72).
    Pediment window: 50 <= x < 66 -> candidates at x=52 and x=62.
    """
    foot = np.ones((h, w), dtype=bool)
    cat = np.zeros((h, w), dtype=bool)
    cat[0, 0] = True
    edt_cat = ndi.distance_transform_edt(~cat)
    parent = np.zeros((h, w), dtype=bool)
    ridge = np.zeros((h, w), dtype=bool)
    for br, bc in ((10, 10), (10, 30)):
        for dr, dc in ((1, 1), (1, 5), (2, 8), (5, 1), (5, 5), (8, 2)):
            parent[br + dr, bc + dc] = True
            ridge[br + dr, bc + dc] = True
    cands = [(12, 52), (12, 62), (12, 72), (27, 52), (27, 62), (27, 72)]
    for r, c in cands:
        er = r + 5 if r < 20 else r - 5    # same 10-px block row as the candidate
        parent[er, c + 3] = True           # the block's single existing dot, 5.83 px away
        ridge[r, c] = True                 # an unused ridge cell in the same block
    ped = np.zeros((h, w), dtype=bool)
    ped[:, 50:66] = True
    return foot, cat, edt_cat, parent, ridge, ped


LEGACY_ORDER = [(12, 52), (12, 62), (12, 72), (27, 52), (27, 62), (27, 72)]


def test_dest_filter_all_true_is_byte_identical_to_legacy():
    """Regression guard for the refactor: a full-True filter must not move a byte."""
    foot, cat, edt_cat, parent, ridge, _ = _separated_grid()
    legacy = C5.relocate_cvband_down(parent, foot, edt_cat, ridge, n_move=4)
    filtered = C5.relocate_cvband_down(
        parent, foot, edt_cat, ridge, n_move=4, dest_filter=np.ones_like(foot)
    )
    for a, b in zip(legacy, filtered):
        if isinstance(a, np.ndarray):
            assert np.array_equal(a, b)
        else:
            assert a == b


def test_ped_filter_matches_legacy_restricted_to_subset():
    """dest_filter=ped == the legacy destination sequence restricted to the pediment."""
    foot, cat, edt_cat, parent, ridge, ped = _separated_grid()
    legacy_out, legacy_src, legacy_dst, _ = C5.relocate_cvband_down(
        parent, foot, edt_cat, ridge, n_move=6
    )
    ped_out, ped_src, ped_dst, ped_st = CP.build_ped_down(
        parent, foot, edt_cat, ridge, ped, n_move=4, mode="ped"
    )
    # Identical shave sources (the removal loop is destination-blind)
    assert np.array_equal(ped_src, legacy_src[:4])
    # Destinations are exactly the legacy order restricted to the pediment half
    assert [tuple(x) for x in ped_dst] == [rc for rc in LEGACY_ORDER if ped[rc]]
    assert ped[ped_dst[:, 0], ped_dst[:, 1]].all()
    assert int(ped_out.sum()) == int(parent.sum())
    assert ped_st["added_on_ancestor_ridge_fraction"] == 1.0


def test_nonped_filter_is_the_exact_complement():
    foot, cat, edt_cat, parent, ridge, ped = _separated_grid()
    legacy_out, _, legacy_dst, _ = C5.relocate_cvband_down(parent, foot, edt_cat, ridge, n_move=6)
    nped_out, nped_src, nped_dst, _ = CP.build_ped_down(
        parent, foot, edt_cat, ridge, ped, n_move=2, mode="nonped"
    )
    assert [tuple(x) for x in nped_dst] == [rc for rc in LEGACY_ORDER if not ped[rc]]
    assert (~ped[nped_dst[:, 0], nped_dst[:, 1]]).all()
    assert int(nped_out.sum()) == int(parent.sum())


def test_ped_first_prefer_reorders_then_spills():
    foot, cat, edt_cat, parent, ridge, ped = _separated_grid()
    out, src, dst, st = CP.build_ped_down(
        parent, foot, edt_cat, ridge, ped, n_move=5, mode="ped_first"
    )
    assert int(out.sum()) == int(parent.sum())
    assert len(dst) == 5
    # The four pediment candidates are exhausted (in legacy order) BEFORE any spill
    ped_order = [rc for rc in LEGACY_ORDER if ped[rc]]
    assert [tuple(x) for x in dst[:4]] == ped_order
    assert not ped[dst[4][0], dst[4][1]]
    assert tuple(dst[4]) == (12, 72)       # the first non-pediment cell in legacy order


def test_capacity_shortfall_raises_and_stats_helpers():
    foot, cat, edt_cat, parent, ridge, ped = _separated_grid()
    # The non-pediment half only offers two candidates -> a 4-dot ask cannot be met
    with pytest.raises(ValueError, match="capacity"):
        CP.build_ped_down(parent, foot, edt_cat, ridge, ped, n_move=4, mode="nonped")
    # destination_regime_shares on a small hand-built move set
    pedm = np.zeros((10, 10), bool); pedm[:5] = True
    ridge_all = np.ones((10, 10), bool)
    shares = CP.destination_regime_shares(np.array([[1, 1], [7, 7]]), pedm, ridge_all)
    assert shares["ped_fraction"] == 0.5 and shares["ridge_fraction"] == 1.0
    assert CP.destination_regime_shares(np.zeros((0, 2), np.int32), pedm, ridge_all)["n_dst"] == 0


def _local_ped_zeros():
    return sorted(ROOT.glob("releases/*-concb5km*down2p5*-zeros.tif")) + sorted(
        ROOT.glob("releases/*-concb5kmpeddown5*-zeros.tif")
    )


@pytest.mark.skipif(not _local_ped_zeros(), reason="pediment CONCENTRATION TIFFs are gitignored in CI")
def test_on_disk_pediment_releases_match_receipts():
    """On-disk MUST gates, re-checked from the written bytes (brief v2 §6)."""
    import hashlib

    import rasterio
    from gems57 import grid as g57grid

    g = g57grid.load_grid(ROOT / "data" / "bridge")
    foot = np.asarray(g.footprint, bool)
    cat = np.asarray(g.catalogue, bool)
    edt_cat = ndi.distance_transform_edt(~cat)
    parent = None
    for pp in sorted((ROOT / "data" / "scored_fleet").glob("GEMSDOE32*h33-h33-2-b2*zeros.tif")):
        with rasterio.open(pp) as src:
            parent = src.read(1) > 0.5
        break
    assert parent is not None

    seen = set()
    for zp in _local_ped_zeros():
        rec = json.loads(zp.with_suffix(".json").read_text(encoding="utf-8"))
        np_path = zp.with_name(zp.name.replace("-zeros.tif", ".tif"))
        assert np_path.is_file()
        assert hashlib.sha256(zp.read_bytes()).hexdigest() == rec["zeros"]["sha256"]
        assert hashlib.sha256(np_path.read_bytes()).hexdigest() == rec["nan"]["sha256"]
        with rasterio.open(zp) as sz, rasterio.open(np_path) as sn:
            az, an = sz.read(1), sn.read(1)
        dots = az > 0.5
        assert int(dots.sum()) == 37654
        assert not np.any(dots & cat)
        assert float(edt_cat[dots & ~parent].min()) > 3.0
        assert np.all(az[~foot] == 0.0)
        assert np.all(np.isnan(an[~foot])) and np.all(np.isfinite(an[foot]))
        seen.add(rec["value"])
    assert seen == {"b5km-ped-down2p5", "b5km-nonped-down2p5", "b5km-ped-down5"}
