"""Re-read every shipped AXIS release from disk and re-run the MUST-pass gates.

This is the brief's end-of-session self-check, made repeatable: it does not trust
``evidence/axis_variants.json``, it takes the digests recorded in ``ledger/submissions.csv``
(the canonical ledger, written only by ``scripts/build_ledger.py``) and re-derives everything
from the bytes on disk - hash, format, value range, NaN placement, catalogue mass, catalogue
clearance and dot count.

The ledger's house convention is that ``sha256`` is the **zeros twin's** digest and ``sha8``
is the dot-set token, so both encodings are checked against what is actually recorded.

It skips cleanly when the release rasters are not in this checkout - the repo gitignores
``releases/*.tif`` pending data-use review - so a clean CI clone does not fail on artifacts
that are deliberately local-only.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems86_axis import gates, grid_io  # noqa: E402
from gems86_axis.grid_io import dot8  # noqa: E402

RELEASES = ROOT / "releases" / "axis86"
LEDGER = ROOT / "ledger" / "submissions.csv"
BRIDGE_OK = (ROOT / "data" / "bridge" / "sample_submission.tif").is_file()
SESSION_PREFIX = "gems86-h33-2b2-"


def _session_rows() -> list[dict]:
    if not LEDGER.is_file():
        return []
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)
                if (r.get("id") or "").startswith(SESSION_PREFIX)]


ROWS = [r for r in _session_rows() if (RELEASES / f"{r['id']}.tif").is_file()]
pytestmark = pytest.mark.skipif(
    not (ROWS and BRIDGE_OK),
    reason="no session release rasters in this checkout (releases/*.tif is gitignored)")


@pytest.fixture(scope="module")
def ctx():
    return grid_io.load_context()


@pytest.mark.parametrize("row", ROWS, ids=[r["id"] for r in ROWS] or ["none"])
def test_release_matches_ledger_and_passes_gates(row, ctx):
    """Every gate must pass, re-read from the file on disk, for both encodings."""
    others = {r["sha256"] for r in ROWS if r["id"] != row["id"]}
    for mode, suffix in (("nan", ""), ("zeros", "-zeros")):
        path = RELEASES / f"{row['id']}{suffix}.tif"
        assert path.is_file(), f"missing release {path}"
        if mode == "zeros":
            assert grid_io.sha256_file(path) == row["sha256"], f"{path.name} hash drift"
        res = gates.run_all(path, ctx, others, grid_io.PARENT_CAT_CLEARANCE_PX)
        assert res["format"]["passed"], res["format"]
        assert res["values"]["passed"], res["values"]
        assert res["catalogue_clearance"]["passed"], res["catalogue_clearance"]
        assert res["ledger_hash"]["passed"], res["ledger_hash"]
        assert res["values"]["n_dots"] == int(row["n_dots"])
        assert res["values"]["dots_on_catalogue"] == 0
        assert res["values"]["mode"] == mode


@pytest.mark.parametrize("row", ROWS, ids=[r["id"] for r in ROWS] or ["none"])
def test_twins_carry_identical_pixels(row, ctx):
    """The nan-outside and zeros-outside twins must be the same dot set."""
    foot = ctx["footprint"]
    a = grid_io.load_dots(RELEASES / f"{row['id']}.tif", foot)
    b = grid_io.load_dots(RELEASES / f"{row['id']}-zeros.tif", foot)
    assert bool((a == b).all()), "the two encodings disagree on the dot set"
    assert int(a.sum()) == int(row["n_dots"])
    assert row["sha8"] == dot8(a), "recorded token is not the dot-set digest"


def test_parent_r0_is_reproducible_from_pinned_bytes(ctx):
    """The parent must stay the hash-pinned R0: 37,654 dots, none on the catalogue."""
    parent = ROOT / ("data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-"
                     "20261004T220000Z-e5eb6e7e-zeros.tif")
    assert parent.is_file(), "parent R0 bytes are not in this checkout"
    assert grid_io.sha256_file(parent) == \
        "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
    dots = grid_io.load_dots(parent, ctx["footprint"])
    assert int(dots.sum()) == 37_654
    assert int((dots & ctx["catalogue"]).sum()) == 0


def test_duplicate_arms_are_not_marked_built():
    """PRUNE/3 and SNAP/2 already existed on main; they must not read as new candidates."""
    rows = _session_rows()
    assert rows, "no session rows in the ledger"
    by_axis = {(r["axis"], r["value"]): r["status"] for r in rows}
    assert by_axis.get(("CONCENTRATION", "b1km-move15")) == "BUILT"
    for axis, value in (("PRUNE", "collar3px"), ("SNAP", "2px")):
        assert by_axis.get((axis, value)) == "BUILT-DUPLICATE", \
            f"({axis},{value}) must be recorded as a duplicate, not a new candidate"
