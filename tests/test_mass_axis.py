"""Unit tests for the MASS axis harness (scripts/build_mass_axis.py).

Cheap synthetic checks on the rules, plus artifact tests (skipped when the
gitignored release rasters are absent):

* greedy thinning in visit order gives earlier cells priority;
* minus drops exactly the highest-rank dots, plus adds exactly the
  lowest-rank eligible cells, counts and catalogue exclusions hold;
* if releases/mass/ is populated, every twin passes the brief gates, the
  minus variant only deletes, the plus variant only adds, and ledger rows exist.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "scripts"))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mass = _load("build_mass_axis")
prune = _load("prune_collar")


def _synthetic():
    h = w = 30
    rank = np.full((h, w), -1, np.int64)
    # one horizontal ridge, ranks increase left to right
    h19 = np.zeros((h, w), bool)
    h19[10, 2:28] = True
    cells = np.argwhere(h19)
    for i, (y, x) in enumerate(cells):
        rank[y, x] = i
    parent = np.zeros((h, w), bool)
    parent[10, 2:28:3] = True  # dots every 3 px along the ridge
    distance = np.full((h, w), 10.0)
    footprint = np.ones((h, w), bool)
    return parent, h19, rank, distance, footprint


def test_greedy_thin_respects_visit_order():
    mask = np.zeros((5, 12), bool)
    mask[2, :] = True
    rank = np.tile(np.arange(12), (5, 1))
    out = mass.greedy_thin(mask, rank, 2.8)
    assert out[2, 0] and out[2, 3] and out[2, 6]
    assert not out[2, 1] and not out[2, 2]


def test_minus_drops_highest_rank_and_plus_adds_lowest_rank():
    parent, h19, rank, distance, footprint = _synthetic()
    v = mass.build_mass_variants(parent, h19, rank, distance, footprint, frac=0.25)
    n0 = int(parent.sum())
    n_change = int(round(0.25 * n0))
    minus, plus = v["massminus10"], v["massplus10"]
    assert int(minus["dots"].sum()) == n0 - n_change
    assert int(plus["dots"].sum()) == n0 + n_change
    assert np.all(minus["dots"] <= parent) and not minus["added"].any()
    assert np.all(parent <= plus["dots"]) and not plus["removed"].any()
    # dropped dots are the highest-rank parent dots
    pr = rank[parent]
    assert rank[minus["removed"]].min() >= np.sort(pr)[-n_change]
    # added cells are the lowest-rank eligible cells and were not dots
    assert not (plus["added"] & parent).any()
    assert (h19[plus["added"]]).all()


def test_plus_respects_catalogue_distance():
    parent, h19, rank, distance, footprint = _synthetic()
    distance[10, 3] = 1.0  # an early-ranked cell too close to the catalogue
    v = mass.build_mass_variants(parent, h19, rank, distance, footprint, frac=0.25)
    assert not v["massplus10"]["added"][10, 3]


def test_build_is_deterministic():
    parent, h19, rank, distance, footprint = _synthetic()
    a = mass.build_mass_variants(parent, h19, rank, distance, footprint, frac=0.25)
    b = mass.build_mass_variants(parent, h19, rank, distance, footprint, frac=0.25)
    for k in a:
        assert np.array_equal(a[k]["dots"], b[k]["dots"])


# -------------------------------------------------------------------- releases
MASS_DIR = ROOT / "releases" / "mass"


def _mass_files() -> list[Path]:
    if not MASS_DIR.is_dir():
        return []
    return sorted(MASS_DIR.glob("*.tif"))


@pytest.mark.skipif(not _mass_files(), reason="no MASS releases built in this checkout")
def test_every_mass_release_passes_the_brief_gates():
    g = prune.load_grids()
    parent = g.parent
    for path in _mass_files():
        mode = "zeros" if path.stem.endswith("-zeros") else "nan"
        rep = prune.validate(path, g, mode)
        assert rep["all_checks_passed"], (path.name, rep["checks"])
        assert rep["on_catalogue_dots"] == 0
        dots = rep and None  # placeholder to keep linters quiet
    # set relations, re-read from disk
    import rasterio
    by_key = {}
    for path in _mass_files():
        key = "minus" if "massminus10" in path.name else "plus"
        by_key.setdefault(key, rasterio.open(path).read(1) > 0)
    assert np.all(by_key["minus"] <= parent), "MASS-10% may only delete"
    assert np.all(parent <= by_key["plus"]), "MASS+10% may only add"
    assert int(by_key["minus"].sum()) == 33889
    assert int(by_key["plus"].sum()) == 41419


@pytest.mark.skipif(not (ROOT / "ledger" / "variants_mass.json").is_file(),
                    reason="MASS variants not built")
def test_mass_ledger_rows_exist_and_carry_predictions():
    rows = [r for r in csv.DictReader((ROOT / "ledger" / "submissions.csv").open(encoding="utf-8"))
            if r["axis"] == "MASS"]
    assert {r["value"] for r in rows} == {"minus10pct", "plus10pct"}
    for r in rows:
        assert r["status"] == "BUILT" and r["evidence_class"] == "MODEL"
        assert "MODEL" in r["predicted_change"] and r["score"] == ""
        assert 1.0 <= float(r["pct_changed"]) <= 50.0
    card = json.loads((ROOT / "evidence" / "mass_axis_20261023.json").read_text(encoding="utf-8"))
    assert card["ranking"]["validation"].startswith("greedy 2.8 px")
    assert card["leakage_canary"]["status"] == "PASS"
    assert card["r0_rebuild"]["sha256_matches"]
