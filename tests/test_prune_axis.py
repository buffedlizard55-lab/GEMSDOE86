"""Unit tests for the PRUNE axis harness (scripts/prune_collar.py, scripts/build_ledger.py).

These are cheap, synthetic checks on the *rules*, not on the released rasters:

* the DTI algebra used in the brief is re-derived from the shared metric code;
* the collar definitions are exact set operations with no accidental overlap;
* relocation preserves count, keeps dots off the catalogue and past the 3 px
  boundary, and is deterministic;
* the ledger's identity/dedupe rules collapse only what they claim to collapse;
* if ``releases/`` is populated, every file passes the brief's gates, the
  ``-nan`` and ``-zeros`` twins carry the same dots, and no file duplicates an
  existing digest.
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

from gems57.metric import dti_exact  # noqa: E402


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


prune = _load("prune_collar")
ledger = _load("build_ledger")


# --------------------------------------------------------------------- algebra
def test_dti_matches_the_brief_algebra():
    """DTI = T / (0.2T + 0.2(S - M) + 0.8|G|) for unit-mass dots (brief section 2)."""
    rng = np.random.default_rng(3)
    truth = np.zeros((24, 24), bool)
    truth[6:18, 11] = True          # one straight trace
    pred = np.zeros((24, 24), np.float32)
    for y, x in rng.integers(0, 24, size=(40, 2)):
        pred[y, x] = 1.0

    res = dti_exact(pred, truth)
    T, F, N = res["tp"], res["fp"], float(res["n_truth"])
    S = float(pred.sum())
    M = S - F                     # FP_w = sum p*(1 - max_g k)  =>  M = S - FP_w
    closed = T / (0.2 * T + 0.2 * (S - M) + 0.8 * N)
    assert closed == pytest.approx(res["dti"], rel=0, abs=1e-9)


def test_empty_and_full_edge_cases():
    truth = np.zeros((10, 10), bool)
    truth[5, 5] = True
    none = np.zeros((10, 10), np.float32)
    assert dti_exact(none, truth)["dti"] == 0.0
    full = np.ones((10, 10), np.float32)
    assert dti_exact(full, truth)["dti"] > 0.0


# -------------------------------------------------------------------- variants
def _synthetic_grid():
    """Catalogue = one vertical trace at column 5; parent dots hug it."""
    h = w = 40
    catalogue = np.zeros((h, w), bool)
    catalogue[5:35, 5] = True
    from scipy import ndimage as ndi
    distance = ndi.distance_transform_edt(~catalogue)
    footprint = np.ones((h, w), bool)
    parent = np.zeros((h, w), bool)
    for x in (7, 8, 9, 12, 20):                      # distances 2,3,4,7,15
        parent[10:20, x] = True
    return prune.Grids(footprint=footprint, catalogue=catalogue, distance=distance,
                       parent=parent, sample=np.zeros((h, w), np.float32))


def test_collar_definitions_are_exact_sets():
    g = _synthetic_grid()
    v = prune.build_variants(g)
    d = g.distance

    removed3 = g.parent & ~v["prune3"]["dots"]
    assert removed3.any()
    assert (d[removed3] > 2.0).all() and (d[removed3] <= 3.0).all()
    # everything outside the 2-3 px ring survives
    keep = g.parent & ((d <= 2.0) | (d > 3.0))
    assert (v["prune3"]["dots"][keep]).all()

    removed4 = g.parent & ~v["prune4"]["dots"]
    assert (d[removed4] > 2.0).all() and (d[removed4] <= 4.0).all()
    assert int(removed4.sum()) > int(removed3.sum())


def test_relocation_preserves_count_and_constraints():
    g = _synthetic_grid()
    v = prune.build_variants(g)
    dots = v["prune3r"]["dots"]
    assert int(dots.sum()) == int(g.parent.sum())
    new = dots & ~g.parent
    assert new.any()
    assert not (new & g.catalogue).any()
    assert (g.distance[new] > 3.0).all()
    assert not (new & ~g.footprint).any()
    # kept dots are untouched: no dot moved from outside the pruned ring
    assert (v["prune3r"]["dots"] & (g.parent & (g.distance > 3.0))).sum() == \
           (g.parent & (g.distance > 3.0)).sum()


def test_relocation_is_deterministic():
    g = _synthetic_grid()
    a = prune.build_variants(g)["prune3r"]["dots"]
    b = prune.build_variants(g)["prune3r"]["dots"]
    assert np.array_equal(a, b)


def test_predictions_exist_for_every_variant():
    for axis, value, _ in prune.VARIANTS:
        key = f"{axis}{value}"
        assert key in prune.PREDICTIONS
        assert "MODEL" in prune.PREDICTIONS[key]


# ---------------------------------------------------------------------- ledger
def test_sha8_ignores_date_stamps():
    assert ledger.sha8_of("h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros") == "e5eb6e7e"
    assert ledger.sha8_of("h27-4-solo-d28-20261004-8acb75e1-nan") == "8acb75e1"
    assert ledger.sha8_of("gems-submission-20260925T001403Z-7f00890a") == "7f00890a"
    assert ledger.sha8_of("2314b599") == "2314b599"


def test_fill_suffix_twins_collapse():
    a = ledger.fingerprint("r7-nms3-dem10-scarp_0c9199f14e62")
    b = ledger.fingerprint("r7-nms3-dem10-scarp_0c9199f14e62_allfinite")
    assert a == b
    assert ledger.fingerprint("x-20261020-849a0f04-nan") == ledger.fingerprint("x-20261020-849a0f04-zeros")


def test_ledger_never_claims_a_receipt():
    rows = list(csv.DictReader((ROOT / "ledger" / "submissions.csv").open(encoding="utf-8")))
    assert rows
    for r in rows:
        assert r["evidence_class"] in {"CLAIM", "NO-EVIDENCE", "MODEL", "RECEIPT"}
        if r["evidence_class"] != "RECEIPT":
            assert r["receipt_score"] == ""
            assert r["receipt"] == "N"
        # a projection is never written into a score column
        if r["status"] == "BUILT":
            assert r["predicted_change"]
            assert r["score"] == ""


def test_ledger_is_reproducible():
    target = ROOT / "ledger" / "submissions.csv"
    text = ledger.render(ledger.build_rows() + ledger.variant_rows())
    assert target.read_bytes().decode("utf-8") == text, \
        "ledger/submissions.csv is stale; rerun build_ledger.py"


# -------------------------------------------------------------------- releases
def _releases() -> list[Path]:
    """Our twins: releases/ holds pure-deletion PRUNE files, releases/refill/ the refill design."""
    out = []
    for d in (ROOT / "releases", ROOT / "releases" / "refill"):
        if d.is_dir():
            out += sorted(p for p in d.glob("*prune*.tif"))
    return out


def _ours() -> list[Path]:
    """Only the files this branch built (the other session's ladder lives in releases/ too)."""
    return [p for p in _releases() if "prune4" in p.name or "prune3r" in p.name]


@pytest.mark.skipif(not _ours(), reason="no releases built in this checkout")
def test_every_release_passes_the_brief_gates():
    g = prune.load_grids()
    for path in _ours():
        mode = "zeros" if path.stem.endswith("-zeros") else "nan"
        rep = prune.validate(path, g, mode)
        assert rep["all_checks_passed"], (path.name, rep["checks"])
        # house naming: <parent>-<tag>-<date>-<zeros8>[-zeros].tif.  The NaN twin
        # carries the ZEROS digest in its name (the pair is named once), so only
        # the zeros file embeds its own digest.
        if mode == "zeros":
            assert path.stem.split("-")[6] == rep["sha256"][:8]
        assert rep["n_dots"] > 0


@pytest.mark.skipif(not _ours(), reason="no releases built in this checkout")
def test_nan_and_zeros_twins_carry_the_same_dots():
    import rasterio
    pairs = {}
    for path in _ours():
        stem = path.stem.replace("-zeros", "")
        key = "-".join(stem.split("-")[:-1])          # parent-tag-date
        pairs.setdefault(key, {})["zeros" if path.stem.endswith("-zeros") else "nan"] = path
    for key, d in pairs.items():
        assert set(d) == {"nan", "zeros"}, (key, list(d))
        a = rasterio.open(d["nan"]).read(1)
        b = rasterio.open(d["zeros"]).read(1)
        assert np.array_equal(np.isfinite(a) & (a > 0), b > 0)


@pytest.mark.skipif(not _ours(), reason="no releases built in this checkout")
def test_no_release_duplicates_a_known_digest():
    for path in _ours():
        rep = prune.uniqueness_vs_disk(path)
        assert not rep["duplicate"], (path.name, rep["exact_hash_duplicates"])


@pytest.mark.skipif(not _ours(), reason="no releases built in this checkout")
def test_release_names_follow_the_brief_convention():
    for path in _ours():
        parts = path.stem.split("-")
        # <parent>-<axis><value>-<yyyymmdd>-<sha8>[-zeros], parent = h33-h33-2-b2
        assert parts[:4] == ["h33", "h33", "2", "b2"]
        assert parts[4].startswith("prune")
        assert len(parts) in (7, 8)
        assert parts[5] == prune.DATE_TAG
        assert len(parts[6]) == 8
        assert len(parts) == 7 or parts[7] == "zeros"


@pytest.mark.skipif(not _ours(), reason="no releases built in this checkout")
def test_evidence_card_matches_releases():
    card = json.loads((ROOT / "evidence" / "prune_axis_20261023.json").read_text(encoding="utf-8"))
    on_disk = {p.stat().st_size for p in _ours()}
    built = [v for v in card["variants"] if v.get("status") != "WITHDRAWN"]
    assert built
    for v in built:
        assert v["gate_all_pass"]
        assert v["validation_nan"]["bytes"] in on_disk
        assert v["validation_zeros"]["bytes"] in on_disk
        assert v["proxy"]["evidence_class"] == "PROXY"
        assert v["pct_changed"] == pytest.approx(v["diff"]["pct_of_parent_changed"], abs=1e-9)


@pytest.mark.skipif(not _ours(), reason="no releases built in this checkout")
def test_refill_variant_only_lives_in_the_refill_directory():
    """A PRUNE release in releases/ may only delete dots; the refill design is elsewhere."""
    import rasterio
    parent = prune.load_grids().parent
    for path in (ROOT / "releases").glob("*prune*.tif"):
        dots = rasterio.open(path).read(1) > 0
        assert np.all(dots <= parent), path.name
    for path in (ROOT / "releases" / "refill").glob("*.tif"):
        dots = rasterio.open(path).read(1) > 0
        assert (dots & ~parent).any(), "the refill variant must add dots, else it is a plain prune"
