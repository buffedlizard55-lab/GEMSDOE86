#!/usr/bin/env python3
"""Build up to three single-AXIS variants of parent R0, gate them, and write the receipts.

Parent R0 = ``h33-h33-2-b2`` (GEMSDOE32), 37,654 unit-mass dots.  The parent's bytes are
restored from the owner mirror and verified against the SHA-256 pin in
``registry/data_manifest.json`` before anything is derived from them.

Outputs
-------
``releases/<id>.tif``            NaN outside the footprint (spec form)
``releases/<id>-zeros.tif``      zeros outside (fallback twin)
``evidence/axis_variants.json``  run cards: parent diff, gates, mechanism inputs
``ledger/submissions.csv``       one row per variant, status BUILT, receipt_score empty

Nothing here scores a submission, contacts a leaderboard, or chooses a slot.

Usage::

    .venv/bin/python scripts/build_axis_variants.py [--axes PRUNE CONCENTRATION SNAP]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
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

R0_ID = "h33-2b2"
R0_REL = ("data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-"
          "20261004T220000Z-e5eb6e7e-zeros.tif")
R0_MANIFEST_ID = "scored_h33_2_b2_zeros"
SUPPORT_MANIFEST_ID = "scored_h19_5"
DATE_TAG = "20261023"

PRUNE_RADIUS_PX = 3.0
MOVE_FRACTION = 0.15
SNAP_SHIFT_PX = 2

#: Predicted live change, MODEL class only (brief section 8).  None of these is a score.
PREDICTIONS = {
    "PRUNE": {"change": 0.004, "range": [0.002, 0.006],
              "text": "+0.004 (range +0.002..+0.006); MODEL, below the 0.01 evidence band"},
    "CONCENTRATION": {"change": 0.006, "range": [0.003, 0.010],
                      "text": "+0.006 (range +0.003..+0.010); MODEL, at the 0.01 evidence band"},
    "SNAP": {"change": 0.004, "range": [0.001, 0.008],
             "text": "+0.004 (range +0.001..+0.008); MODEL, below the 0.01 evidence band"},
}

#: (axis, value) keys already built on main by parallel sessions, verified at merge time.
#: Brief section 6 dedupes on exactly this key, so a rebuild is corroboration, not a candidate.
ALREADY_BUILT = {("PRUNE", "collar3px"): "PRUNE / 3", ("SNAP", "2px"): "SNAP / 2"}


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              check=True).stdout.decode().strip()
    except Exception:  # pragma: no cover - never blocks a build
        return "unknown"


def pinned(manifest_id: str) -> dict:
    man = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    return {f["id"]: f for f in man["files"]}[manifest_id]


def verify_pin(manifest_id: str, path: Path) -> dict:
    entry = pinned(manifest_id)
    digest = grid_io.sha256_file(path)
    if digest != entry["sha256"] or path.stat().st_size != entry["bytes"]:
        raise SystemExit(f"PIN MISMATCH {manifest_id}: {digest} != {entry['sha256']}")
    return {"id": manifest_id, "path": str(path), "sha256": digest, "bytes": entry["bytes"],
            "repo": entry["repo"], "ref": entry["ref"], "verified": True}



def house_receipt(card: dict, mask, ctx: dict, pair: dict) -> dict:
    """A receipt in the schema the repo's other release arms use.

    ``tests/test_prune_ladder.py`` reads ``<id>-zeros.json`` next to every top-level
    ``-zeros.tif``.  These arms live in a subdirectory (like ``releases/refill/`` and
    ``releases/mass/``) because they do not satisfy that test's PRUNE-only-deletion
    contract, but they still carry the same receipt shape so any tool that reads one
    schema reads all of them.
    """
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from gems86.prune import catalogue_distance, diff_stats, dot_digest  # noqa: PLC0415

    parent = grid_io.load_dots(ROOT / R0_REL, ctx["footprint"])
    dist = catalogue_distance(ctx["catalogue"])
    d = card["parent_diff"]
    axis = card["axis"].upper()
    block = {
        "n_parent": d["parent_dots"], "n_candidate": d["variant_dots"],
        "retained": d["shared_dots"], "removed": d["dropped"], "added": d["added"],
        "pct_of_parent_changed": d["pct_changed_of_parent"],
        "pct_removed": round(100.0 * d["dropped"] / max(d["parent_dots"], 1), 4),
        "pct_added": round(100.0 * d["added"] / max(d["parent_dots"], 1), 4),
        "kept_fraction": round(d["shared_dots"] / max(d["parent_dots"], 1), 6),
        "jaccard": d["jaccard"], "count_exact": d["count_delta"] == 0,
    }
    rec = {
        "id": card["id"], "parent": "h33-h33-2-b2", "axis": axis.lower(),
        "value": card["value"], "generated_utc": card["generated_utc"],
        "role": "duplicate-corroboration" if card["duplicate_of"] else "candidate",
        "slot_candidate": not card["duplicate_of"],
        "slot_reason": (f"duplicate of (parent, axis, value) = {card['duplicate_of']} already in "
                        "the ledger; kept for audit, not a slot candidate (IR-86-CONC-01)"
                        if card["duplicate_of"] else
                        "unbuilt axis on main at merge time; the one new candidate this branch adds"),
        "n_dots": d["variant_dots"], "pct_changed": d["pct_changed_of_parent"],
        "dot_digest": dot_digest(mask), "dot8": card["token"],
        "evidence_class": "MODEL",
        "predicted_live_change": card["predicted_change"],
        "predicted_live_range": card["predicted_range"],
        "diff": block,
        "model": {"evidence_class": "MODEL",
                  "algebra": "DTI = T / (0.2T + 0.2(S-M) + 0.8|G|)",
                  "caution": "no live score and no holdout PROXY was run this session; the "
                             "sign rests on the mechanism card alone"},
        "rule": card["rule"],
        "provenance": {"parent_sha256": card["parent"]["sha256"],
                       "git_sha": card["git_sha"],
                       "builder": "scripts/build_axis_variants.py",
                       "run_card": "evidence/axis_variants.json"},
    }
    if axis == "SNAP":
        s_ = card["stats"]
        rec["radius_px"] = float(s_["max_shift_px"])
        rec["movement"] = {
            "n_parent": d["parent_dots"], "n_candidate": d["variant_dots"],
            "n_snapped": s_["dots_moved"],
            "pct_snapped": round(100.0 * s_["dots_moved"] / max(d["parent_dots"], 1), 4),
            "mean_displacement_px_moved": s_["mean_displacement_px"],
            "median_displacement_px_moved": s_["median_displacement_px"],
            "max_displacement_px": s_["max_displacement_px"],
            "blocked_by_occupancy": s_["dots_blocked_by_occupancy"],
            "blocked_by_clearance": s_["dots_blocked_by_clearance"],
            "catalogue_distance_before_mean_px": s_["cat_edt_mean_parent"],
            "catalogue_distance_after_mean_px": s_["cat_edt_mean_variant"],
            "catalogue_distance_after_min_px": s_["min_cat_edt_variant"],
            "dots_on_catalogue": 0,
            "diff_vs_parent": block,
        }
    if axis == "PRUNE":
        rec["refill"] = card["stats"]
    if axis == "CONCENTRATION":
        rec["blocks"] = {k: v for k, v in card["stats"].items()
                         if k.startswith("block_density") or k in
                         ("block_size", "moved_placed", "moved_target", "dest_blocks",
                          "dest_block_frac", "placement_rule", "source_rule", "prior_terms")}
    for mode in ("nan", "zeros"):
        a = card["artifacts"][mode]
        rec[mode] = {"file": Path(a["path"]).name, "sha256": a["sha256"],
                     "bytes": Path(a["path"]).stat().st_size,
                     "validator": {"all_checks_passed": bool(card["gates"][mode]["passed"]),
                                   "on_catalogue_dots": card["gates"][mode]["values"]["dots_on_catalogue"],
                                   "min_catalogue_distance_px":
                                       card["gates"][mode]["catalogue_clearance"]["min_cat_edt_px"],
                                   "checks": card["gates"][mode]["values"]["checks"]}}
    return rec


def _axis_values(axes: list[str]) -> list[tuple[str, str]]:
    """The (axis, value) keys this invocation will write, for ledger dedupe."""
    out = []
    for ax in axes:
        if ax == "PRUNE":
            out.append(("PRUNE", f"collar{PRUNE_RADIUS_PX:g}px"))
        elif ax == "CONCENTRATION":
            out.append(("CONCENTRATION",
                        f"b{variants.BLOCK_PX // 10}km-move{int(round(100 * MOVE_FRACTION))}"))
        elif ax == "SNAP":
            out.append(("SNAP", f"{SNAP_SHIFT_PX}px"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--axes", nargs="+", default=["PRUNE", "CONCENTRATION", "SNAP"])
    ap.add_argument("--out", default="releases/axis86",
                    help="subdirectory, per the repo convention that arms outside the "
                         "top-level PRUNE-only-deletion contract live in their own dir")
    ap.add_argument("--ledger", default="ledger/submissions.csv",
                    help="read-only: supplies the known-SHA256 set for the dedupe gate")
    a = ap.parse_args()
    t0 = time.time()

    ctx = grid_io.load_context()
    pins = [verify_pin("existing_faults", Path(ctx["catalogue_path"])),
            verify_pin("sample_submission", Path(ctx["sample_path"]))]
    r0_path = ROOT / R0_REL
    pins.append(verify_pin(R0_MANIFEST_ID, r0_path))
    support_path = ROOT / ".cache/gems_data/scored/gems19-h19-5-powerlaw-budget-multiline-" \
                          "corroborated-20260930-e27054cf-nan.tif"
    pins.append(verify_pin(SUPPORT_MANIFEST_ID, support_path))

    r0 = grid_io.load_dots(r0_path, ctx["footprint"])
    support = grid_io.load_dots(support_path, ctx["footprint"])
    bd = bandmod.load_bands()
    bd["tmi_grad"] = bandmod.gradient_magnitude(bd["tmi_up150"], fill_value=0.0)
    scarp_stack = np.stack([np.nan_to_num(bandmod.zscore(bd["scarp"][k]), nan=0.0)
                            for k in bandmod.SCARP_BANDS])
    scarp = scarp_stack.mean(axis=0)
    bd["scarp_composite"] = bandmod.zscore(np.nan_to_num(scarp, nan=0.0))
    snap_response = bandmod.zscore(bd["tmi_grad"]) + bd["scarp_composite"]

    print(f"[ctx] footprint={int(ctx['footprint'].sum())} catalogue={int(ctx['catalogue'].sum())} "
          f"R0 dots={int(r0.sum())} support={int(support.sum())}", flush=True)

    prior_pack = variants.block_prior(ctx, bd, ctx["catalogue"])
    # Read the canonical ledger by COLUMN NAME, never by position: the file is written by
    # scripts/build_ledger.py and its schema belongs to that generator, not to this script.
    ledger = ROOT / a.ledger
    own_keys = set(_axis_values(a.axes))
    known_sha: set[str] = set()
    replaced: list[str] = []
    if ledger.is_file():
        with ledger.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                key = ((row.get("axis") or "").upper(), (row.get("value") or "").strip())
                if key in own_keys:
                    # The brief dedupes on exact hash and on repeated (parent, axis, value).
                    # A rebuild of the same axis/value supersedes its own row instead of
                    # being rejected by its own digest.
                    replaced.append(row.get("id") or row.get("name") or "?")
                    continue
                for col in ("sha256", "sha256_nan", "sha256_zeros"):
                    v = (row.get(col) or "").strip()
                    if len(v) == 64:
                        known_sha.add(v)
    for f in (ROOT / "data/scored_fleet").glob("*.tif"):
        known_sha.add(grid_io.sha256_file(f))
    if replaced:
        print(f"[ledger] superseding prior rows for the same (parent, axis, value): {replaced}",
              flush=True)

    built = []
    if "PRUNE" in a.axes:
        mask, st = variants.prune(r0, ctx, PRUNE_RADIUS_PX, support,
                                  grid_io.PARENT_CAT_CLEARANCE_PX, grid_io.PARENT_MIN_SPACING_PX)
        built.append(("prune3", mask, st))
    if "CONCENTRATION" in a.axes:
        mask, st = variants.concentration(r0, ctx, bd, prior_pack["prior"], MOVE_FRACTION,
                                          grid_io.PARENT_CAT_CLEARANCE_PX,
                                          grid_io.PARENT_MIN_SPACING_PX)
        built.append((f"conc{int(round(100*MOVE_FRACTION))}", mask, st))
    if "SNAP" in a.axes:
        mask, st = variants.snap(r0, ctx, snap_response, SNAP_SHIFT_PX,
                                 grid_io.PARENT_CAT_CLEARANCE_PX)
        built.append(("snap2", mask, st))

    cards, rows = [], []
    for token, mask, st in built:
        ident = dot8(mask)
        stem = f"gems86-{R0_ID}-{token}-{DATE_TAG}-{ident}"
        diff = variants.parent_diff(r0, mask, ctx["footprint"])
        note = (f"GEMSDOE86 {R0_ID} {st['axis']} {st['value']} | {diff['variant_dots']} dots, "
                f"{diff['pct_changed_of_parent']}% changed vs R0 | token {ident} | UNSCORED")
        pair = grid_io.write_pair(mask, ctx, ROOT / a.out, stem, name=stem, note=note)
        gate = {}
        for mode in ("nan", "zeros"):
            gate[mode] = gates.run_all(pair[mode]["path"], ctx, known_sha,
                                       grid_io.PARENT_CAT_CLEARANCE_PX)
            if gate[mode]["passed"]:
                known_sha.add(pair[mode]["sha256"])
        dup = ALREADY_BUILT.get((st["axis"], st["value"]), "")
        pred = PREDICTIONS[st["axis"]]
        card = {"id": stem, "axis": st["axis"], "value": st["value"], "token": ident,
                "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "duplicate_of": dup, "predicted_change": pred["change"],
                "predicted_range": pred["range"],
                "rule": st.get("refill_pool") or st.get("placement_rule") or st.get("response", ""),
                "parent": {"id": R0_ID, "file": R0_REL, "sha256": pins[2]["sha256"]},
                "stats": {k: v for k, v in st.items() if k != "counts"},
                "parent_diff": diff, "note": note, "note_chars": len(note),
                "gates": gate, "artifacts": pair,
                "git_sha": git_sha()}
        cards.append(card)
        receipt = house_receipt(card, mask, ctx, pair)
        rp = Path(pair["zeros"]["path"]).with_suffix(".json")
        rp.write_text(json.dumps(receipt, indent=2) + "\n")
        card["receipt"] = str(rp)
        rows.append(card)
        print(f"[{st['axis']:14s}] {stem}  dots={diff['variant_dots']} "
              f"changed={diff['pct_changed_of_parent']}%  "
              f"gates={'PASS' if gate['nan']['passed'] and gate['zeros']['passed'] else 'FAIL'}",
              flush=True)

    out = {"schema_version": 1, "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "session_axis_set": a.axes, "parent_id": R0_ID,
           "parent_claimed_live": "0.2778 CLAIM (owner-reported; no submission-page receipt)",
           "elapsed_s": round(time.time() - t0, 1),
           "inputs_verified": pins,
           "constants": {"prune_radius_px": PRUNE_RADIUS_PX, "move_fraction": MOVE_FRACTION,
                         "snap_shift_px": SNAP_SHIFT_PX,
                         "block_px": variants.BLOCK_PX,
                         "parent_min_spacing_px": grid_io.PARENT_MIN_SPACING_PX,
                         "parent_cat_clearance_px": grid_io.PARENT_CAT_CLEARANCE_PX},
           "variants": cards}
    ev = ROOT / "evidence/axis_variants.json"
    ev.parent.mkdir(parents=True, exist_ok=True)
    ev.write_text(json.dumps(out, indent=2) + "\n")

    # This repo keeps ONE ledger generator (scripts/build_ledger.py).  This script does not
    # write ledger/submissions.csv; it emits the run card, and the variant entries reach the
    # ledger through scripts/emit_axis_variant_entries.py -> ledger/variants_concentration.json
    # -> scripts/build_ledger.py.  Writing the CSV here would let the file drift.
    print(f"wrote {ev} ({out['elapsed_s']}s)", flush=True)
    print("next: python scripts/emit_axis_variant_entries.py && python scripts/build_ledger.py",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
