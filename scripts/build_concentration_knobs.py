#!/usr/bin/env python3
"""CONCENTRATION knob session: three single-axis variants of R0, 2026-10-23.

Why this axis, in one paragraph
-------------------------------
The metric's own algebra, calibrated on the only live difference in the ledger
(40,199 -> 37,654 dots = +0.0070, all of the removed dots at >= 2 px from the catalogue),
fixes ``D = 20,200`` and ``T = 5,610`` at R0's 0.2778 CLAIM.  Two consequences decide the
axis: (i) deleting a dot that earns no credit is worth ``+0.2T/D^2 = +2.75e-6`` and deleting
a dot that covers truth is worth about ``-1.0e-5``, so unguided MASS cuts are a coin flip;
(ii) *relocating* a dot from a place with no credit to a place that may hold truth costs
nothing and can pay ``+4.7e-5`` per newly covered truth pixel.  Relocation with an informed
destination prior is therefore the only operation in the brief's axis list with a positive
expected change that does not depend on identifying useless dots.  That is CONCENTRATION,
and its evidence in the ledger is one file at one setting: 1 km blocks, 15 % moved, top
fifth of blocks.  This session moves exactly one knob at a time off that setting.

The floor this axis must clear
-----------------------------
A relocation is a *no-op* in expectation when the destination is chosen at random: a random
cell is within the 3 px kernel of about ``0.031`` truth-credit units (0.29 cells x 0.35 mean
credit at ``|G| ~ 15.8k``), i.e. about ``+1.4e-6`` per moved dot.  Any gain above that is the
prior doing work, and any loss below it is the prior being anti-informative.  Every number
written here is a MODEL, not a score.

What is written
---------------
``releases/axis86/<id>.tif``            NaN outside the footprint (brief spec form)
``releases/axis86/<id>-zeros.tif``      zeros outside (fallback twin; upload only one)
``evidence/concentration_knobs_20261023.json``   run card, gates, parent diffs
``ledger/variants_concentration_knobs.json``     entries for the single ledger generator

Nothing here contacts DrivenData, scores a submission, or spends a slot.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems86_axis import bands as bandmod  # noqa: E402
from gems86_axis import gates, grid_io, variants  # noqa: E402
from gems86_axis.grid_io import dot8  # noqa: E402

DATE_TAG = "20261023"
R0_ID = "h33-2b2"
R0_REL = ("data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-"
          "20261004T220000Z-e5eb6e7e-zeros.tif")
EXT_REL = ".cache/gems_data/external/geodawn_extensions_u8.tif"
EXT_SHA = "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b"
R0_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"

#: The one setting already in the ledger (conc15, PR #37): block 10 px, move 0.15, dest 0.20.
#: Each variant below changes exactly one of those three, so any live difference between two
#: of them is attributable to that knob.
VARIANTS = [
    {
        "token": "conc15-b5km", "value": "b5km-move15",
        "block_px": 50, "move": 0.15, "dest_frac": 0.20,
        "knob": "block size only: 1 km -> 5 km (dose and destination share unchanged)",
        "predicted_change": 0.004, "predicted_range": [-0.002, 0.010],
        "mechanism": ("mapping effort is a km-scale process (quadrangle-by-quadrangle compilation "
                      "with 1:24k source maps), so a 5 km block should carry the prior more "
                      "cleanly than a 1 km block, at the cost of much coarser destinations"),
    },
    {
        "token": "conc24", "value": "b1km-move24",
        "block_px": 10, "move": 0.24, "dest_frac": 0.20,
        "knob": "dose only: 15 % -> 24 % of dots moved (48 % of dots changed, inside the brief's "
                "1-50 % band; block size and destination share unchanged)",
        "predicted_change": 0.008, "predicted_range": [0.001, 0.015],
        "mechanism": ("if the 1 km prior is real, the gain should grow with dose until the source "
                      "pool (lowest-prior dots) stops being credit-free or the destinations "
                      "saturate; this arm measures the slope, which is what decides whether a "
                      "third, larger dose is worth a slot"),
    },
    {
        "token": "conc15-t05", "value": "b1km-move15-t05",
        "block_px": 10, "move": 0.15, "dest_frac": 0.05,
        "knob": "destination selectivity only: top fifth -> top 5 % of blocks (dose and block "
                "size unchanged)",
        "predicted_change": 0.007, "predicted_range": [0.001, 0.013],
        "mechanism": ("a sharper prior concentrates the same 5,648 moved dots on the strongest "
                      "fifth-as-many blocks; the gain per moved dot should rise and the coverage "
                      "cost (fewer distinct destination blocks) should too — this arm separates "
                      "prior quality from prior breadth, which no built file does"),
    },
]

SESSION_NOTE = "UNSCORED; MODEL prediction only"


def sha256(path: Path) -> str:
    return grid_io.sha256_file(path)


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              check=True).stdout.decode().strip()
    except Exception:  # pragma: no cover
        return "unknown"


def verify(path: Path, expected: str, label: str) -> dict:
    if not path.is_file():
        raise SystemExit(f"missing pinned input {label}: {path}")
    got = sha256(path)
    if got != expected:
        raise SystemExit(f"PIN MISMATCH {label}: {got} != {expected}")
    return {"label": label, "path": str(path.relative_to(ROOT)), "sha256": got,
            "bytes": path.stat().st_size, "verified": True,
            "organizer_authenticated": False}


def density_cv(mask: np.ndarray, footprint: np.ndarray, block_px: int) -> dict:
    d = variants.block_density(mask, footprint, block_px)
    return {k: v for k, v in d.items() if k != "counts"}


def known_hashes(ledger: Path) -> set[str]:
    out: set[str] = set()
    if ledger.is_file():
        with ledger.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                for col in ("sha256", "sha256_nan", "sha256_zeros"):
                    v = (row.get(col) or "").strip()
                    if len(v) == 64:
                        out.add(v)
    for f in (ROOT / "data/scored_fleet").glob("*.tif"):
        out.add(sha256(f))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="releases/axis86")
    ap.add_argument("--ledger", default="ledger/submissions.csv")
    ap.add_argument("--only", nargs="*", default=None, help="build only these tokens")
    a = ap.parse_args()
    t0 = time.time()

    ctx = grid_io.load_context()
    catalogue_sha = sha256(Path(ctx["catalogue_path"]))
    sample_sha = sha256(Path(ctx["sample_path"]))
    pins = [{"label": "existing_faults", "path": "data/bridge/existing_faults.tif",
             "sha256": catalogue_sha, "verified": catalogue_sha.startswith("7ba308cc")},
            {"label": "sample_submission", "path": "data/bridge/sample_submission.tif",
             "sha256": sample_sha, "verified": sample_sha.startswith("2176d08e")},
            verify(ROOT / R0_REL, R0_SHA, "scored_h33_2_b2_zeros"),
            verify(ROOT / EXT_REL, EXT_SHA, "ext_geodawn_extensions_u8")]
    if not all(p["verified"] for p in pins):
        raise SystemExit(f"pin verification failed: {pins}")

    r0 = grid_io.load_dots(ROOT / R0_REL, ctx["footprint"])
    # Only the upward-continued TMI band is needed for this axis' prior.  bands.load_bands()
    # also opens the 32 MB topographic and int16 DEM mirrors, which this session does not use
    # and does not restore; the construction below is byte-identical to its TMI line.
    import rasterio

    with rasterio.open(ROOT / EXT_REL) as src:
        names = list(src.descriptions)
        tmi_q = src.read(names.index(bandmod.TMI_BAND) + 1)
    bands = {"tmi_up150": (tmi_q > 0).astype(np.float32) * tmi_q.astype(np.float32)}
    bands["tmi_grad"] = bandmod.gradient_magnitude(bands["tmi_up150"], fill_value=0.0)
    print(f"[ctx] footprint={int(ctx['footprint'].sum())} catalogue={int(ctx['catalogue'].sum())} "
          f"R0 dots={int(r0.sum())}", flush=True)

    known = known_hashes(ROOT / a.ledger)
    todo = [v for v in VARIANTS if not a.only or v["token"] in a.only]
    cards = []
    for spec in todo:
        block_px = spec["block_px"]
        prior_pack = variants.block_prior(ctx, bands, ctx["catalogue"], block_px=block_px)
        mask, st = variants.concentration(r0, ctx, bands, prior_pack["prior"], spec["move"],
                                          grid_io.PARENT_CAT_CLEARANCE_PX,
                                          grid_io.PARENT_MIN_SPACING_PX,
                                          block_px=block_px, dest_block_frac=spec["dest_frac"])
        st["value"] = spec["value"]
        st["block_density_at_variant_block"] = {
            "before": density_cv(r0, ctx["footprint"], block_px),
            "after": density_cv(mask, ctx["footprint"], block_px)}
        st["block_density_at_1km"] = {"before": density_cv(r0, ctx["footprint"], 10),
                                      "after": density_cv(mask, ctx["footprint"], 10)}
        ident = dot8(mask)
        stem = f"gems86-{R0_ID}-{spec['token']}-{DATE_TAG}-{ident}"
        diff = variants.parent_diff(r0, mask, ctx["footprint"])
        if not (1.0 <= diff["pct_changed_of_parent"] <= 50.0):
            raise SystemExit(f"{stem}: {diff['pct_changed_of_parent']}% changed is outside the "
                             "brief's 1-50 % band for a non-SNAP variant")
        note = (f"GEMSDOE86 {R0_ID} {st['axis']} {spec['value']} | {diff['variant_dots']} dots, "
                f"{diff['pct_changed_of_parent']}% changed vs R0 | {SESSION_NOTE}")
        note = note[:140]
        pair = grid_io.write_pair(mask, ctx, ROOT / a.out, stem, name=stem, note=note)
        gate = {}
        for mode in ("nan", "zeros"):
            gate[mode] = gates.run_all(pair[mode]["path"], ctx, known,
                                       grid_io.PARENT_CAT_CLEARANCE_PX)
            if gate[mode]["passed"]:
                known.add(pair[mode]["sha256"])
            if not gate[mode]["passed"]:
                print(f"[FAIL] {stem} {mode}: "
                      f"{[k for k, v in gate[mode].items() if isinstance(v, dict) and not v.get('passed')]}",
                      flush=True)
        card = {
            "id": stem, "axis": st["axis"], "value": spec["value"], "token": ident,
            "knob": spec["knob"], "mechanism": spec["mechanism"],
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "parent": {"id": R0_ID, "file": R0_REL, "sha256": R0_SHA},
            "predicted_change": spec["predicted_change"],
            "predicted_range": spec["predicted_range"],
            "prediction_class": "MODEL",
            "rule": st["placement_rule"],
            "stats": st, "parent_diff": diff, "note": note, "note_chars": len(note),
            "gates": gate, "artifacts": pair, "git_sha": git_sha(),
            "inputs": [p for p in pins],
        }
        cards.append(card)
        rp = Path(pair["zeros"]["path"]).with_suffix(".json")
        rp.write_text(json.dumps(card, indent=2) + "\n")
        print(f"[{spec['value']:18s}] {stem} dots={diff['variant_dots']} "
              f"changed={diff['pct_changed_of_parent']}% moved={st['moved_placed']} "
              f"gates={'PASS' if gate['zeros']['passed'] and gate['nan']['passed'] else 'FAIL'}",
              flush=True)

    out = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session": "GEMSDOE86 concentration-knob session",
        "axis": "CONCENTRATION",
        "parent_claimed_live": "0.2778 CLAIM (owner-reported; no submission-page receipt)",
        "elapsed_s": round(time.time() - t0, 1),
        "inputs_verified": pins,
        "calibration": {
            "live_pair_used": "solo-d28 40,199 dots = 0.2708 CLAIM -> R0 37,654 dots = 0.2778 CLAIM",
            "implied_d": 20200.0, "implied_t": 5610.0,
            "per_dot_cost_of_a_zero_credit_dot": 2.75e-6,
            "per_truth_pixel_value": 4.68e-5,
            "random_destination_floor_per_moved_dot": 1.4e-6,
            "note": "MODEL. Both inputs to the rate are CLAIMs; the whole calibration is a MODEL.",
        },
        "constants": {"parent_min_spacing_px": grid_io.PARENT_MIN_SPACING_PX,
                      "parent_cat_clearance_px": grid_io.PARENT_CAT_CLEARANCE_PX,
                      "already_spent_setting": "b1km-move15 (conc15, PR #37)"},
        "variants": cards,
    }
    ev = ROOT / "evidence/concentration_knobs_20261023.json"
    ev.parent.mkdir(parents=True, exist_ok=True)
    ev.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {ev} ({out['elapsed_s']}s)", flush=True)
    print("next: python scripts/emit_concentration_knob_entries.py && python scripts/build_ledger.py",
          flush=True)
    return 0 if all(c["gates"]["zeros"]["passed"] and c["gates"]["nan"]["passed"] for c in cards) else 1


if __name__ == "__main__":
    raise SystemExit(main())
