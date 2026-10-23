"""Re-read every shipped AXIS release from disk and re-run the MUST-pass gates.

This is the brief's end-of-session self-check, made repeatable: it does not trust
``evidence/axis_variants.json``, it takes the SHA-256 digests recorded in
``ledger/submissions.csv`` and re-derives everything from the bytes on disk - hash, format,
value range, NaN placement, catalogue mass, catalogue clearance, and the parent-diff counts.

It skips cleanly when the releases have not been built in this checkout, so a clean CI clone
that only carries the bridge rasters does not fail on missing artifacts.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems86_axis import gates, grid_io  # noqa: E402

RELEASES = ROOT / "releases"
LEDGER = ROOT / "ledger" / "submissions.csv"
BRIDGE_OK = (ROOT / "data" / "bridge" / "sample_submission.tif").is_file()


def _built_rows() -> list[dict]:
    if not LEDGER.is_file():
        return []
    with LEDGER.open(newline="") as fh:
        return [r for r in csv.DictReader(fh) if r.get("status") == "BUILT"]


ROWS = _built_rows()
pytestmark = pytest.mark.skipif(
    not (ROWS and BRIDGE_OK), reason="no BUILT ledger rows or bridge rasters in this checkout")


@pytest.fixture(scope="module")
def ctx():
    return grid_io.load_context()


@pytest.mark.parametrize("row", ROWS, ids=[r["id"] for r in ROWS] or ["none"])
def test_release_matches_ledger_and_passes_gates(row, ctx):
    known = {row["sha256_nan"], row["sha256_zeros"]}
    for mode in ("nan", "zeros"):
        path = RELEASES / f"{row['id']}.tif" if mode == "nan" else RELEASES / f"{row['id']}-zeros.tif"
        assert path.is_file(), f"missing release {path}"
        assert grid_io.sha256_file(path) == row[f"sha256_{mode}"], f"{path.name} hash drift"
        res = gates.run_all(path, ctx, known - {row[f"sha256_{mode}"]},
                            grid_io.PARENT_CAT_CLEARANCE_PX)
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
    for row in ROWS:
        assert int(row["n_dots"]) == 37_654, f"{row['id']} does not hold the parent's count"
