"""Invariant tests for the SNAP variants of R0 (GEMSDOE86, 2026-10-23 session).

These tests read the released files back from disk; they do not rebuild them and never touch the
network, the catalogue's withheld truth, or any submission endpoint.
"""
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evidence" / "snap_variants.json"
RELEASES = ROOT / "releases"

PARENT = ("data/scored_fleet/"
          "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
SAMPLE = ROOT / "data" / "bridge" / "sample_submission.tif"
CATALOGUE = ROOT / "data" / "bridge" / "existing_faults.tif"


@pytest.fixture(scope="module")
def report():
    assert REPORT.is_file(), "run scripts/build_snap_variants.py first"
    return json.loads(REPORT.read_text())


@pytest.fixture(scope="module")
def context():
    with rasterio.open(SAMPLE) as ds:
        footprint = np.isfinite(ds.read(1))
        ref = dict(crs=ds.crs, shape=ds.shape, transform=ds.transform, dtype=ds.dtypes[0])
    with rasterio.open(CATALOGUE) as ds:
        catalogue = ds.read(1) == 1
    with rasterio.open(ROOT / PARENT) as ds:
        parent = ds.read(1) > 0
    return dict(footprint=footprint, ref=ref, catalogue=catalogue, parent=parent)


def _files(report):
    for key, v in report["variants"].items():
        yield key, v["files"]["nan_outside"], v["files"]["zeros_outside"]


def test_three_variants_and_three_distinct_hashes(report):
    assert sorted(report["variants"]) == ["cons2", "hg2", "vg2"]
    shas = {v["gates"][v["files"]["nan_outside"]]["sha256"] for v in report["variants"].values()}
    assert len(shas) == 3
    for v in report["variants"].values():
        assert v["axis"] == "SNAP"
        assert v["parent"] == "h33-h33-2-b2"


def test_parent_hash_is_not_reused_by_any_release(report):
    parent_sha = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
    for _, nan_name, zeros_name in _files(report):
        key = nan_name.split("-snap-")[1].split("-")[0]
        for name in (nan_name, zeros_name):
            assert report["variants"][key]["gates"][name]["sha256"] != parent_sha


def test_every_release_passes_the_brief_gates_on_disk(report, context):
    for _, nan_name, zeros_name in _files(report):
        key = next(k for k, v in report["variants"].items() if v["files"]["nan_outside"] == nan_name)
        for name, nan_outside in ((nan_name, True), (zeros_name, False)):
            path = RELEASES / name
            assert path.is_file(), path
            with rasterio.open(path) as ds:
                a = ds.read(1)
                assert ds.count == 1 and ds.dtypes[0] == "float32"
                assert ds.crs == context["ref"]["crs"]
                assert ds.shape == tuple(context["ref"]["shape"])
                assert tuple(ds.transform)[:6] == tuple(context["ref"]["transform"])[:6]
            fp, cat, parent = context["footprint"], context["catalogue"], context["parent"]
            assert np.isfinite(a[fp]).all(), name
            assert np.isnan(a[fp]).sum() == 0
            assert not (np.isnan(a) & fp).any()
            if nan_outside:
                assert np.isnan(a[~fp]).all()
            else:
                assert (a[~fp] == 0.0).all()
            assert a[fp].min() >= 0.0 and a[fp].max() <= 1.0
            assert int((a[cat] > 0).sum()) == 0, "catalogue mass"
            assert int((a > 0).sum()) == int(parent.sum()) == 37654
            # the twins differ only outside the footprint
            assert report["variants"][key]["gates"][name]["all_checks_passed"]


def test_dot_set_invariants_from_the_report(report):
    for _, v in report["variants"].items():
        d = v["parent_diff"]
        assert d["n_dots"] == 37654
        assert 1.0 <= d["pct_changed"] <= 100.0
        assert d["max_displacement_px"] <= 2.0 + 1e-6, "cap is a 2 px Euclidean radius"
        assert d["min_spacing_px_after"] >= 2.828 - 1e-9, "spacing floor must not be tightened"
        assert d["n_forced_floor_violations"] == 0
        assert d["mean_gain_z_moved"] >= 0.25 - 1e-9, "every moved dot cleared the gain gate"


def test_twins_share_the_dot_set(context, report):
    fp = context["footprint"]
    for _, nan_name, zeros_name in _files(report):
        with rasterio.open(RELEASES / nan_name) as a, rasterio.open(RELEASES / zeros_name) as b:
            ma, mb = a.read(1) > 0, b.read(1) > 0
        assert np.array_equal(ma, mb)
        assert np.array_equal(ma, ma & fp)


def test_rule_constants_are_the_preregistered_ones(report):
    constants = report["rule_constants"]
    assert constants["smooth_sigma_px"] == 1.0
    assert constants["cap_px"] == 2
    assert constants["gain_gate_z"] == 0.25
    assert constants["spacing_floor_px"] == 2.828
    prereg = json.loads((ROOT / "registry" / "preregistration_snap.json").read_text())
    assert prereg["fixed_rule"]["smoothing_sigma_px"] == constants["smooth_sigma_px"]
    assert prereg["fixed_rule"]["gain_gate_z"] == constants["gain_gate_z"]
    assert prereg["fixed_rule"]["spacing_floor_px"] == constants["spacing_floor_px"]


def test_proxy_is_never_reported_as_a_score(report):
    for v in report["holdout_proxy"].values():
        assert v["evidence_class"].startswith("PROXY")
        assert "not a leaderboard score" in v["evidence_class"]
    assert report["leakage_canary"]["verdict"] == "clear"
    assert all(v <= 0.90 for v in report["leakage_canary"]["catalogue_auc"].values())


def test_ledger_rows_exist_for_every_built_release(report):
    import csv
    with (ROOT / "ledger" / "submissions.csv").open(newline="") as fh:
        rows = {r["id"]: r for r in csv.DictReader(fh)}
    for key, v in report["variants"].items():
        row = rows[v["id"]]
        # the (parent, axis) pair was already spent by PR #31 on main, so these are
        # corroborating builds and must never be proposed as slot candidates
        assert row["status"] == "BUILT-DUPLICATE"
        assert row["axis"] == "SNAP" and row["value"] == key
        # house ledger convention: the sha256 column carries the zeros twin's digest
        assert row["sha256"] == v["gates"][v["files"]["zeros_outside"]]["sha256"]
        assert row["receipt_score"] == "", "a receipt is human-supplied, never generated"
        assert "MODEL" in row["evidence_class"]
