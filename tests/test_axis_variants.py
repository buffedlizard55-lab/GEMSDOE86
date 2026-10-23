"""Unit tests for the AXIS session: the metric algebra and the three variant builders.

The algebra test is the one the brief demands ("Algebra (derived; unit-test it)"): it
checks ``DTI = T / (0.2T + 0.2(S-M) + 0.8|G|)`` against the shared template metric on
random small cases, plus the isolated-dot break-even bar ``k > alpha * DTI``.

The variant tests run on a small synthetic grid so the invariants (count, exclusions,
displacement bound, single-axis parent diff) are checked deterministically and fast.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor" / "template66"))

from gems.metric import dti, marginal_credit_bar, tversky_terms  # noqa: E402
from gems86_axis import variants  # noqa: E402


# ---------------------------------------------------------------- metric algebra

def _terms_identity(pred, gt):
    tp, fp, fn = tversky_terms(pred, gt)
    p = np.asarray(pred, dtype=float)
    g = np.asarray(gt) > 0
    s = float(p.sum())
    dist = ndimage.distance_transform_edt(~g) * 100.0
    kmax = np.clip(1.0 - dist / 300.0, 0.0, None)
    m = float((p * kmax).sum())
    return tp, fp, fn, s, m, int(g.sum())


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_dti_algebra_matches_derived_form(seed):
    rng = np.random.default_rng(seed)
    gt = (rng.random((24, 24)) < 0.05).astype(np.int8)
    pred = np.where(rng.random((24, 24)) < 0.08, rng.random((24, 24)), 0.0)
    n_pos = int((gt > 0).sum())
    pred[gt > 0] = np.where(rng.random(n_pos) < 0.5, 1.0, 0.0)

    tp, fp, fn, s, m, n_g = _terms_identity(pred, gt)
    assert tp + fn == pytest.approx(float(n_g), abs=1e-9)
    assert fp == pytest.approx(s - m, abs=1e-9)
    derived = tp / (0.2 * tp + 0.2 * (s - m) + 0.8 * n_g + 1e-9)
    assert dti(pred, gt) == pytest.approx(derived, rel=1e-9, abs=1e-12)


def test_isolated_dot_pays_only_above_alpha_dti():
    """A lone dot earns kernel credit k; it must beat alpha*DTI to raise the score."""
    gt = np.zeros((31, 31), dtype=np.int8)
    gt[15, 15] = 1
    base = np.zeros((31, 31))
    base[15, 25] = 1.0                      # 1 km away -> k = 0
    dti0 = dti(base, gt)
    for offset_px, expect_gain in ((2, True), (3, False)):
        cand = base.copy()
        cand[15, 15 + offset_px] = 1.0
        k = 1.0 - (offset_px * 100.0) / 300.0
        gained = dti(cand, gt) > dti0
        assert gained == expect_gain
        assert (k > marginal_credit_bar(dti0)) == expect_gain


# ---------------------------------------------------------------- variant fixtures

@pytest.fixture()
def ctx():
    h, w = 80, 80
    footprint = np.ones((h, w), dtype=bool)
    footprint[:5, :] = False
    footprint[-5:, :] = False
    catalogue = np.zeros((h, w), dtype=bool)
    catalogue[40, 20:60] = True             # a straight known trace
    catalogue[20:35, 25] = True             # a cross-cutting known trace
    return {"footprint": footprint, "catalogue": catalogue,
            "grid": {"shape": (h, w)}, "sample_path": None, "catalogue_path": None}


@pytest.fixture()
def parent(ctx):
    """A dot field with the parent's geometry: 2*sqrt(2) px spacing, >2 px off catalogue."""
    dots = np.zeros(ctx["footprint"].shape, dtype=bool)
    edt = ndimage.distance_transform_edt(~ctx["catalogue"])
    for r in range(8, 72, 4):
        for c in range(8, 72, 4):
            if ctx["footprint"][r, c] and edt[r, c] > 2.0:
                dots[r, c] = True
    return dots


def _bands(ctx, seed=0):
    rng = np.random.default_rng(seed)
    shape = ctx["footprint"].shape
    grad = rng.random(shape).astype(np.float32)
    grad = ndimage.gaussian_filter(grad, 3)
    return {"tmi_grad": grad, "scarp": {k: rng.random(shape).astype(np.float32)
                                        for k in ("a", "b", "c")}}


def _elig(dots, ctx, clearance=2.0):
    edt = ndimage.distance_transform_edt(~ctx["catalogue"])
    return (dots & ctx["footprint"] & ~ctx["catalogue"] & (edt > clearance))


# ---------------------------------------------------------------- PRUNE

def test_prune_holds_count_widens_collar_and_stays_in_bounds(parent, ctx):
    edt = ndimage.distance_transform_edt(~ctx["catalogue"])
    support = ctx["footprint"] & (edt > 1.0)
    out, st = variants.prune(parent, ctx, radius_px=4.0, support=support,
                             clearance_px=2.0, min_spacing_px=2.8284271247461903)
    assert st["removed_dots"] == int((parent & (edt <= 4.0)).sum()) > 0
    assert out.sum() == parent.sum() - st["refill_shortfall"]
    assert _elig(out, ctx, 2.0).sum() == out.sum()          # exclusions intact
    assert float(edt[out].min()) > 4.0                       # the widened collar holds
    d = variants.parent_diff(parent, out, ctx["footprint"])
    assert d["dropped"] == st["removed_dots"]
    assert 0 < d["pct_changed_of_parent"] <= 50


# ---------------------------------------------------------------- CONCENTRATION

def test_concentration_moves_mass_and_reports_block_cv(parent, ctx):
    bands = _bands(ctx)
    prior_pack = variants.block_prior(ctx, bands, ctx["catalogue"], block_px=10)
    out, st = variants.concentration(parent, ctx, bands, prior_pack["prior"], 0.2,
                                     clearance_px=2.0, min_spacing_px=2.8284271247461903,
                                     block_px=10)
    assert st["moved_placed"] == st["moved_target"]
    assert out.sum() == parent.sum()                          # count fixed
    assert _elig(out, ctx, 2.0).sum() == out.sum()            # same exclusions
    d = variants.parent_diff(parent, out, ctx["footprint"])
    assert d["dropped"] == d["added"] == st["moved_placed"]
    assert 0 < d["pct_changed_of_parent"] <= 50
    assert st["block_density_parent"]["density_cv_occupied"] > 0
    assert st["block_density_variant"]["density_cv_occupied"] > 0
    # mass really did move up-prior
    pv = np.where(np.isfinite(prior_pack["prior"]), prior_pack["prior"], 0.0)
    bid = variants.block_prior(ctx, bands, ctx["catalogue"], block_px=10)["prior"]
    brow = np.repeat(np.arange(bid.shape[0]), 10)[: parent.shape[0]]
    bcol = np.repeat(np.arange(bid.shape[1]), 10)[: parent.shape[1]]
    idx = np.full(parent.shape, -1, dtype=np.int64)
    n = min(brow.size, parent.shape[0])
    m = min(bcol.size, parent.shape[1])
    idx[:n, :m] = (brow[:n, None] * bid.shape[1] + bcol[None, :m])
    ok = idx >= 0
    prior_at = np.where(ok, pv.ravel()[np.clip(idx, 0, None)], -np.inf)
    assert prior_at[out].mean() > prior_at[parent].mean()


# ---------------------------------------------------------------- SNAP

def test_snap_bounded_displacement_count_and_exclusions(parent, ctx):
    bands = _bands(ctx, seed=1)
    resp = bands["tmi_grad"]
    out, st = variants.snap(parent, ctx, resp, max_shift_px=2, clearance_px=2.0)
    assert out.sum() == parent.sum()                          # same count
    assert _elig(out, ctx, 2.0).sum() == out.sum()            # same exclusions
    assert st["max_displacement_px"] <= 2.0 + 1e-9
    # every dot really landed on its window argmax (or was blocked and stayed put)
    edt = ndimage.distance_transform_edt(~ctx["catalogue"])
    offs = [(dy, dx) for dy in range(-2, 3) for dx in range(-2, 3)
            if float(np.hypot(dy, dx)) <= 2.0 + 1e-9]
    rows, cols = np.nonzero(parent)
    checked = 0
    for r, c in list(zip(rows, cols))[:400]:
        if out[r, c]:
            continue
        okmask = ctx["footprint"] & ~ctx["catalogue"] & (edt > 2.0)
        best_rc, best_val = (r, c), -np.inf
        for dy, dx in offs:
            tr, tc = r + dy, c + dx
            if 0 <= tr < out.shape[0] and 0 <= tc < out.shape[1] and okmask[tr, tc]:
                if resp[tr, tc] > best_val:
                    best_val, best_rc = resp[tr, tc], (tr, tc)
        assert out[best_rc], f"dot ({r},{c}) moved to neither its argmax nor stayed put"
        checked += 1
    assert checked > 0
    d = variants.parent_diff(parent, out, ctx["footprint"])
    # SNAP is the one axis the brief exempts from the 1-50% change rule; count must hold
    assert d["count_delta"] == 0 and d["dropped"] == d["added"]
    assert d["dots_changed"] == 2 * st["dots_moved"]


# ---------------------------------------------------------------- parent diff

def test_parent_diff_reports_zero_change_for_identity(parent, ctx):
    d = variants.parent_diff(parent, parent, ctx["footprint"])
    assert d["dots_changed"] == 0 and d["jaccard"] == 1.0
    assert d["pct_changed_of_parent"] == 0.0
