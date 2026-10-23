"""Axis geometry, the parent rebuild, and the shipped release twins.

The artifact tests re-read every committed ``releases/*.tif`` and re-derive the
gates from the bytes, so a release that drifts (wrong grid, mass on the
catalogue, a dot added rather than removed) fails CI rather than a reviewer.

The per-file contract is **axis-aware**: a PRUNE release must only delete dots,
while a RELIEF release must relocate them (equal deletions and insertions, the
parent's count, a >=3 px floor for every inserted cell, and no tightening of the
parent's minimum dot spacing). Both branches check the same shared validator, the
receipt digest, ledger membership and the NaN twin. This widened the test rather
than relaxing it, when the second axis was added to ``releases/`` on 2026-10-23.
"""
import csv
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems57.validate import validate
from src.gems86 import prune as P

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "data" / "bridge"
RELEASES = ROOT / "releases"
FLEET = ROOT / "data" / "scored_fleet"
PARENT = FLEET / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
BASE = FLEET / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"


def _read(path):
    with rasterio.open(path) as ds:
        return ds.read(1)


def _grid():
    from gems57.grid import load_grid
    return load_grid(BRIDGE)


# --------------------------------------------------------------------------- geometry

def test_catalogue_distance_is_euclidean_in_pixels():
    cat = np.zeros((7, 7), bool)
    cat[0, 0] = True
    d = P.catalogue_distance(cat)
    assert d[0, 0] == 0.0
    assert d[0, 3] == 3.0
    assert d[3, 0] == 3.0
    assert d[3, 3] == pytest.approx(np.sqrt(18))


def test_empty_catalogue_is_rejected():
    with pytest.raises(ValueError):
        P.catalogue_distance(np.zeros((4, 4), bool))


def test_shell_ladder_removes_the_expected_cells():
    cat = np.zeros((9, 9), bool)
    cat[4, 4] = True
    d = P.catalogue_distance(cat)
    dots = np.zeros((9, 9), bool)
    dots[4, 5] = dots[5, 5] = dots[4, 6] = dots[6, 5] = dots[4, 7] = True
    assert set(np.round(d[dots], 6)) == {1.0, round(float(np.sqrt(2)), 6), 2.0,
                                        round(float(np.sqrt(5)), 6), 3.0}
    kept = {name: int(P.prune_mask(dots, d, rung["upper"]).sum()) for name, rung in P.RUNGS.items()}
    assert kept == {"r150": 3, "r225": 1, "r283": 1, "r300": 0}


def test_rungs_are_nested():
    rng = np.random.default_rng(7)
    cat = np.zeros((60, 60), bool)
    cat[rng.integers(0, 60, 5), rng.integers(0, 60, 5)] = True
    d = P.catalogue_distance(cat)
    dots = rng.random((60, 60)) > 0.9
    rungs = [P.prune_mask(dots, d, P.RUNGS[k]["upper"]) for k in ("r225", "r283", "r300")]
    assert np.all(rungs[1] <= rungs[0]) and np.all(rungs[2] <= rungs[1])
    assert np.all(rungs[0] <= dots)


def test_control_matches_mass_and_never_touches_the_collar():
    cat = np.zeros((40, 40), bool)
    cat[20, 20] = True
    d = P.catalogue_distance(cat)
    dots = np.zeros((40, 40), bool)
    dots[20, 20:23] = True            # collar dots at 1,2 px
    dots[2:12, 2:12] = True           # far field
    ctl = P.mass_matched_control(dots, d, 10, keep_above=3.0, seed=1)
    assert int(ctl.sum()) == int(dots.sum()) - 10
    assert np.all(ctl[20, 20:23])     # collar untouched
    with pytest.raises(ValueError):
        P.mass_matched_control(dots, d, 10_000, keep_above=3.0, seed=1)


def test_dot_digest_is_position_sensitive_and_stable():
    a = np.zeros((5, 5), bool); a[1, 1] = True
    b = np.zeros((5, 5), bool); b[1, 2] = True
    assert P.dot_digest(a) == P.dot_digest(a.copy())
    assert P.dot_digest(a) != P.dot_digest(b)


def test_prune_variants_may_only_delete():
    cat = np.zeros((20, 20), bool); cat[10, 10] = True
    d = P.catalogue_distance(cat)
    parent = np.zeros((20, 20), bool); parent[10, 11] = True
    child = parent & (d > 1.5)
    stats = P.diff_stats(parent, child, d)
    assert stats["n_added"] == 0
    added = parent.copy(); added[13, 13] = True
    with pytest.raises(ValueError):
        P.diff_stats(parent, added, d)


# --------------------------------------------------------------------------- algebra

def test_collar_prune_decision_rule_against_the_shared_metric():
    """The decision rule the ladder is built on, checked against the real metric.

    A dot that earns no kernel credit only adds false-positive mass, so deleting
    it can never lower DTI. A dot that is the only cover of a truth cell *can*
    lower DTI when deleted. Both directions are asserted, not assumed.
    """
    from gems57 import metric
    truth = np.zeros((40, 40), bool)
    truth[5, 5] = truth[35, 35] = True          # two isolated truth cells

    cover = np.zeros((40, 40), bool)
    cover[5, 5] = True                          # covers one truth cell completely
    base = metric.dti_exact(cover.astype(np.float32), truth)["dti"]
    assert 0.0 < base < 1.0

    # a zero-credit dot (>3 px from every truth cell) only adds false-positive mass
    dead = cover.copy(); dead[20, 20] = True
    assert metric.dti_exact(dead.astype(np.float32), truth)["dti"] < base

    # a dot 2 px from the uncovered truth cell earns 1/3 and pays for itself
    payoff = cover.copy(); payoff[35, 37] = True
    assert metric.dti_exact(payoff.astype(np.float32), truth)["dti"] > base

    # the marginal-inclusion bar quoted in the brief, on the shared metric
    bar = metric.marginal_inclusion_threshold(base)
    assert bar == pytest.approx(0.2 * base)          # the brief's "credit > 0.2 * DTI"
    assert metric.kernel(2.0) > bar                  # a 2 px dot still pays here
    assert metric.kernel(3.0) < bar


# --------------------------------------------------------------------------- parent + releases

@pytest.mark.skipif(not (PARENT.is_file() and BASE.is_file()), reason="pinned fleet rasters absent")
def test_parent_dot_set_is_reproduced_pixel_for_pixel():
    g = _grid()
    d = P.catalogue_distance(g.catalogue)
    rebuilt = P.prune_mask(_read(BASE) > 0, d, 2.0)
    published = _read(PARENT) > 0
    assert int((rebuilt != published).sum()) == 0
    assert int(rebuilt.sum()) == 37654
    assert P.dot_digest(rebuilt) == P.dot_digest(published)


@pytest.mark.skipif(not (PARENT.is_file() and BASE.is_file()), reason="pinned fleet rasters absent")
def test_parent_file_is_reproduced_byte_for_byte(tmp_path):
    """The brief's gate: rebuild R0 and match its sha256, not just its dot set."""
    import sys
    sys.path.insert(0, str(ROOT))
    from scripts.run_prune_ladder import write_with_profile
    g = _grid()
    d = P.catalogue_distance(g.catalogue)
    rebuilt = P.prune_mask(_read(BASE) > 0, d, 2.0).astype(np.float32)
    out = tmp_path / "r0_rebuild.tif"
    sha = write_with_profile(out, np.where(g.footprint, rebuilt, np.float32(0.0)), None)
    assert sha == "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
    assert out.stat().st_size == 219065


@pytest.mark.skipif(not RELEASES.is_dir(), reason="no releases written")
def test_every_release_passes_the_shared_validator_and_the_axis_contract():
    g = _grid()
    parent = _read(PARENT) > 0
    shas = set()
    ledger = {r["sha256"] for r in csv.DictReader(open(ROOT / "ledger" / "submissions.csv")) if r["sha256"]}
    zeros = sorted(RELEASES.glob("*-zeros.tif"))
    if not zeros:
        # rasters are gitignored (data-use policy): rebuild with scripts/run_prune_ladder.py
        pytest.skip("no zeros twins in the working tree; receipts alone cannot re-derive the gates")
    for path in zeros:
        receipt = json.loads(path.with_suffix(".json").read_text())
        rec = validate(path, g.footprint, g.catalogue)
        assert rec["all_checks_passed"], (path.name, rec["checks"])
        assert rec["on_catalogue_positive_pixels"] == 0
        assert rec["sha256"] == receipt["zeros"]["sha256"]
        assert rec["sha256"] in ledger
        shas.add(rec["sha256"])
        dots = _read(path) > 0
        assert int(dots.sum()) == receipt["n_dots"]
        dist = P.catalogue_distance(g.catalogue)
        axis = str(receipt.get("axis", "PRUNE")).upper()
        if axis == "SNAP":
            # a SNAP release is a *movement* of the parent, not a deletion: the
            # count is exact, the exclusion is unchanged, and no dot moved farther
            # than the declared radius (src/gems86/snap.py; tests/test_snap_axis.py).
            # The 1-50 % contract does not apply to SNAP (brief v2 §5), which is why
            # these checks live in this branch and not in the common tail (IR-86-SNAP-03).
            assert int(dots.sum()) == int(parent.sum())
            movement = receipt["movement"]
            assert movement["pct_snapped"] == pytest.approx(receipt["pct_changed"], abs=1e-6)
            assert movement["max_displacement_px"] <= receipt["radius_px"] + 1e-9
            assert not np.any(dots & g.catalogue)
            assert receipt["model"]["evidence_class"] == "MODEL"
            if receipt.get("role", "candidate") == "candidate":
                # this axis shipped predicted-negative on every arm (IR-86-SNAP-01);
                # BUILT-DUPLICATE corroboration arms carry the same verdict, not a bet
                assert receipt["predicted_live_change"] <= 0.0
        elif axis == "RELIEF":
            # RELIEF relocates: equal deletions and insertions, the parent's count,
            # a >= 3 px floor for every inserted cell, and no tightening of the
            # parent's minimum dot spacing. Re-derived from the bytes with the bridge
            # files only (the feature stack is gitignored, so the regime map is not
            # re-derived here); the regime confinement itself is asserted by the
            # builder and re-checkable with tests/test_relief_axis.py.
            from scipy.spatial import cKDTree
            removed, added = parent & ~dots, dots & ~parent
            n_rem, n_add = int(removed.sum()), int(added.sum())
            assert n_rem == n_add, "a RELIEF variant relocates: deletions must equal insertions"
            assert int(dots.sum()) == int(parent.sum()), "a RELIEF variant must fix the count"
            assert float(dist[added].min()) > 3.0 - 1e-9, \
                "newly emitted mass must stay >= 3 px off the catalogue"
            rc = np.column_stack(np.divmod(np.flatnonzero(dots.ravel()), dots.shape[1])).astype(float)
            d2, _ = cKDTree(rc).query(rc, k=2)
            prc = np.column_stack(np.divmod(np.flatnonzero(parent.ravel()), parent.shape[1])).astype(float)
            pd2, _ = cKDTree(prc).query(prc, k=2)
            assert float(d2[:, 1].min()) >= float(pd2[:, 1].min()) - 1e-9, \
                "a RELIEF variant must not tighten the parent's minimum dot spacing"
            stats = dict(pct_changed=round(100.0 * n_rem / int(parent.sum()), 4),
                         n_removed=n_rem, n_added=n_add)
            assert stats["pct_changed"] == pytest.approx(receipt["pct_changed"], abs=1e-4)
            assert 1.0 <= stats["pct_changed"] <= 50.0
        elif axis == "TRACKB":
            # TRACKB relocates donated dots onto along-strike continuations of the
            # parent's own traces (src/gems86/trackb.py). Re-derived from the bytes
            # with the bridge files only: equal deletions and insertions, the parent's
            # count, a >= 3 px catalogue floor for every emitted cell, no tightening of
            # the parent's minimum dot spacing, and the 1-50 % change contract, where
            # pct_changed counts deleted plus inserted cells (IR-86-TRACKB-03).
            from scipy.spatial import cKDTree
            removed, added = parent & ~dots, dots & ~parent
            n_rem, n_add = int(removed.sum()), int(added.sum())
            assert n_rem == n_add, "a TRACKB variant relocates: deletions must equal insertions"
            assert int(dots.sum()) == int(parent.sum()), "a TRACKB variant must fix the count"
            assert float(dist[added].min()) > 3.0 - 1e-9, \
                "newly emitted mass must stay >= 3 px off the catalogue"
            rc = np.column_stack(np.divmod(np.flatnonzero(dots.ravel()), dots.shape[1])).astype(float)
            d2, _ = cKDTree(rc).query(rc, k=2)
            prc = np.column_stack(np.divmod(np.flatnonzero(parent.ravel()), parent.shape[1])).astype(float)
            pd2, _ = cKDTree(prc).query(prc, k=2)
            assert float(d2[:, 1].min()) >= float(pd2[:, 1].min()) - 1e-9, \
                "a TRACKB variant must not tighten the parent's minimum dot spacing"
            pct = round(100.0 * (n_rem + n_add) / int(parent.sum()), 4)
            assert pct == pytest.approx(receipt["pct_changed"], abs=1e-4)
            assert 1.0 <= pct <= 50.0
            assert receipt["trace_set"]["n_traces"] > 0
            assert receipt["evidence_class"] == "MODEL"
        elif axis == "SPACING":
            # SPACING relocates the kernel-crowded pool: equal deletions and
            # insertions, the parent's count, >= 3 px catalogue clearance for every
            # inserted cell, and no tightening of the parent's minimum dot spacing
            # (2.828 px).  The crowded-pair break (>= 3.0 px from the cluster's kept
            # dot) and the three destination geometries need the H19-5 field and the
            # visit-rank reconstruction, so they are asserted by
            # tests/test_spacing_crowdedpool.py and the builder's own gates; here we
            # re-derive what the bytes alone can prove.
            from scipy.spatial import cKDTree
            removed, added = parent & ~dots, dots & ~parent
            n_rem, n_add = int(removed.sum()), int(added.sum())
            assert n_rem == n_add, "a SPACING variant relocates: deletions must equal insertions"
            assert int(dots.sum()) == int(parent.sum()), "a SPACING variant must fix the count"
            assert float(dist[added].min()) > 3.0 - 1e-9, \
                "newly emitted mass must stay >= 3 px off the catalogue"
            rc = np.column_stack(np.divmod(np.flatnonzero(dots.ravel()), dots.shape[1])).astype(float)
            d2, _ = cKDTree(rc).query(rc, k=2)
            prc = np.column_stack(np.divmod(np.flatnonzero(parent.ravel()), parent.shape[1])).astype(float)
            pd2, _ = cKDTree(prc).query(prc, k=2)
            assert float(d2[:, 1].min()) >= float(pd2[:, 1].min()) - 1e-9, \
                "a SPACING variant must not tighten the parent's minimum dot spacing"
            stats = dict(pct_changed=round(100.0 * (n_rem + n_add) / int(parent.sum()), 4))
            assert stats["pct_changed"] == pytest.approx(
                receipt["parent_diff"]["pct_cells_changed"], abs=1e-4)
            movement = receipt["movement"]
            assert receipt["n_moved"] == movement["n_moved"]
            assert receipt["pct_changed"] == pytest.approx(movement["pct_dots_changed"], abs=1e-9)
            assert 1.0 <= receipt["pct_changed"] <= 50.0
            assert movement["displacement_max_px"] <= 16.0 + 16e-9
            assert receipt["predicted_live_change"] is not None
        elif axis == "CONCENTRATION":
            # CONCENTRATION relocates across km blocks on ancestor ridges: equal
            # deletions and insertions, exact parent count, >= 3 px catalogue floor
            # on every newly emitted dot, no tightening of parent minimum dot
            # spacing, and 1-50 % symmetric-diff dot change.
            from scipy.spatial import cKDTree
            removed, added = parent & ~dots, dots & ~parent
            n_rem, n_add = int(removed.sum()), int(added.sum())
            assert n_rem == n_add, "a CONCENTRATION variant relocates: deletions must equal insertions"
            assert int(dots.sum()) == int(parent.sum()), "a CONCENTRATION variant must fix the count"
            assert float(dist[added].min()) > 3.0 - 1e-9, \
                "newly emitted mass must stay >= 3 px off the catalogue"
            rc = np.column_stack(np.divmod(np.flatnonzero(dots.ravel()), dots.shape[1])).astype(float)
            d2, _ = cKDTree(rc).query(rc, k=2)
            prc = np.column_stack(np.divmod(np.flatnonzero(parent.ravel()), parent.shape[1])).astype(float)
            pd2, _ = cKDTree(prc).query(prc, k=2)
            assert float(d2[:, 1].min()) >= float(pd2[:, 1].min()) - 1e-9, \
                "a CONCENTRATION variant must not tighten the parent's minimum dot spacing"
            pct = round(100.0 * (n_rem + n_add) / int(parent.sum()), 4)
            assert pct == pytest.approx(receipt["pct_changed"], abs=1e-4)
            assert 1.0 <= pct <= 50.0
            assert receipt["evidence_class"] == "MODEL"
        else:
            assert np.all(dots <= parent), "a PRUNE variant may only delete dots"
            stats = P.diff_stats(parent, dots, dist)
            assert stats["pct_changed"] == pytest.approx(receipt["pct_changed"], abs=1e-6)
            assert 1.0 <= stats["pct_changed"] <= 50.0
        assert P.dot_digest(dots) == receipt["dot_digest"]
        # spec-form twin: same dots, NaN only outside the footprint
        nan = _read(RELEASES / (path.name.replace("-zeros.tif", ".tif")))
        assert np.array_equal(np.nan_to_num(nan) > 0, dots)
        assert np.all(np.isnan(nan[~g.footprint]))
        assert np.all(np.isfinite(nan[g.footprint]))
    assert len(shas) == len(zeros), "release twins must be distinct from each other"
