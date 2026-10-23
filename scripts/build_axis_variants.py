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
    "PRUNE": "+0.004 (range +0.002..+0.006); MODEL, below the 0.01 evidence band",
    "CONCENTRATION": "+0.006 (range +0.003..+0.010); MODEL, at the 0.01 evidence band",
    "SNAP": "+0.004 (range +0.001..+0.008); MODEL, below the 0.01 evidence band",
}


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


def dot8(mask: np.ndarray) -> str:
    """Deterministic identity token for a dot set (independent of any filename or tag)."""
    packed = np.packbits(mask.astype(np.uint8).ravel())
    h = hashlib.sha256()
    h.update(np.array(mask.shape, dtype=np.int64).tobytes())
    h.update(packed.tobytes())
    return h.hexdigest()[:8]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--axes", nargs="+", default=["PRUNE", "CONCENTRATION", "SNAP"])
    ap.add_argument("--out", default="releases")
    ap.add_argument("--ledger", default="ledger/submissions.csv")
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
    ledger = ROOT / a.ledger
    header = ("id,parent,axis,value,n_dots,pct_changed,sha256_nan,sha256_zeros,"
              "status,predicted_change,receipt_score,receipt_date")
    existing: list[list[str]] = []
    if ledger.is_file():
        lines = ledger.read_text().splitlines()
        if lines:
            header = lines[0]
        existing = [ln.split(",") for ln in lines[1:] if ln.strip()]
    # The brief dedupes on exact hash and on repeated (parent, axis, value).  A rebuild of
    # the same axis/value replaces its own BUILT row instead of being rejected by it.
    keep, replaced = [], []
    for row in existing:
        key = (row[1], row[2], row[3]) if len(row) > 3 else None
        if key and any(key == (R0_ID, ax, val) for ax, val in _axis_values(a.axes)):
            replaced.append(row[0])
        else:
            keep.append(row)
    existing = keep
    known_sha: set[str] = set()
    for row in existing:
        known_sha.update(c for c in row if len(c) == 64)
    for f in (ROOT / "data/scored_fleet").glob("*.tif"):
        known_sha.add(grid_io.sha256_file(f))
    if replaced:
        print(f"[ledger] replaced prior BUILT rows for the same (parent, axis, value): {replaced}",
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
        card = {"id": stem, "axis": st["axis"], "value": st["value"], "token": ident,
                "parent": {"id": R0_ID, "file": R0_REL, "sha256": pins[2]["sha256"]},
                "stats": {k: v for k, v in st.items() if k != "counts"},
                "parent_diff": diff, "note": note, "note_chars": len(note),
                "gates": gate, "artifacts": pair,
                "git_sha": git_sha()}
        cards.append(card)
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

    ledger.parent.mkdir(parents=True, exist_ok=True)
    lines = [header] + [",".join(r) for r in existing]
    for c in rows:
        lines.append(",".join([
            c["id"], R0_ID, c["axis"], c["value"], str(c["parent_diff"]["variant_dots"]),
            str(c["parent_diff"]["pct_changed_of_parent"]),
            c["artifacts"]["nan"]["sha256"], c["artifacts"]["zeros"]["sha256"],
            "BUILT", PREDICTIONS.get(c["axis"], ""), "", ""]))
    ledger.write_text("\n".join(lines) + "\n")
    print(f"wrote {ev} and {ledger} ({out['elapsed_s']}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
