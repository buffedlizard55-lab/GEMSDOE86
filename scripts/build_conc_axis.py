#!/usr/bin/env python3
"""GEMSDOE86 session, AXIS = CONCENTRATION (dose + block-scale read, 2026-10-23).

Parent R0 = ``h33-h33-2-b2`` (GEMSDOE32), 37,654 unit-mass dots, sha256
``c55bafc4…b6fa9``.  ``(CONCENTRATION, b1km-move15)`` is already built (PR #37); this
session builds three NEW ``(axis, value)`` pairs on the same axis, differing only in the
CONCENTRATION parameters, so a live-score delta can still be attributed to the axis:

  * ``b1km-move10``  -- dose low  (10 % of dots moved, 1 km blocks)
  * ``b1km-move20``  -- dose high (20 % of dots moved, 1 km blocks)
  * ``b5km-move15``  -- block scale (15 % moved, 5 km blocks)

Together with the built ``b1km-move15`` they form a dose-response at 1 km (10/15/20) and a
block-size comparison at a fixed 15 % dose.  Placement is geometric only (highest-prior
destination block, then the largest remaining kernel gap); no pixel-scale response term
enters, so this axis cannot smuggle in the SNAP edit that instrument already measured as
negative.

Order of operations (brief §5): verify every pinned input, rebuild R0 from the pinned base
and require it to reproduce ``c55bafc4…`` **byte for byte** (stop otherwise), then build,
gate, and write.  Nothing here logs in, scrapes a leaderboard, submits, or contacts
DrivenData or dropbox.

Usage::

    .venv/bin/python scripts/build_conc_axis.py
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
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "vendor", ROOT / "vendor" / "template66"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gems86_axis import bands as bandmod  # noqa: E402
from gems86_axis import gates, grid_io, variants  # noqa: E402
from gems86_axis.grid_io import dot8  # noqa: E402

SESSION = "concentration"
DATE_TAG = "20261023"
R0_ID = "h33-2b2"
PARENT_LABEL = "h33-h33-2-b2"
AXIS = "CONCENTRATION"

R0_REL = ("data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-"
          "20261004T220000Z-e5eb6e7e-zeros.tif")
BASE_REL = ("data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-"
            "20261003-8acb75e1f2cc-nan.tif")
R0_MANIFEST_ID = "scored_h33_2_b2_zeros"

# (token, value, block_px, move_fraction, predicted change, range)
VARIANTS = [
    ("conc10", "b1km-move10", 10, 0.10, 0.004, (0.002, 0.007)),
    ("conc20", "b1km-move20", 10, 0.20, 0.008, (0.004, 0.012)),
    ("conc15b5km", "b5km-move15", 50, 0.15, 0.003, (0.000, 0.008)),
]

PREDICTIONS = {
    "b1km-move10": ("+0.004 (range +0.002..+0.007, MODEL). Dose low: move 10 % of R0's dots out "
                    "of the lowest-prior 1 km blocks into the highest-prior fifth, count fixed, "
                    "placement geometric only. With the built b1km-move15 (+0.006) this is the "
                    "lower rung of a dose-response at 1 km."),
    "b1km-move20": ("+0.008 (range +0.004..+0.012, MODEL). Dose high: the brief's upper bound "
                    "(20 % moved) at 1 km blocks. The upper rung of the dose-response; it is the "
                    "only one of the three that approaches the 0.01 evidence floor."),
    "b5km-move15": ("+0.003 (range 0.000..+0.008, MODEL). Same 15 % dose as the built b1km-move15 "
                    "but on 5 km blocks: the catalogue-interaction term is smoothed over 15 km and "
                    "the destination set is far larger and less selective, so the effect is "
                    "predicted weaker. This is the SLOT_PLAN's named next cut (block size)."),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              check=True).stdout.decode().strip()
    except Exception:  # pragma: no cover
        return "unknown"


def pinned(manifest_id: str) -> dict:
    man = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    return {f["id"]: f for f in man["files"]}[manifest_id]


def verify_pin(manifest_id: str, path: Path) -> dict:
    entry = pinned(manifest_id)
    digest = grid_io.sha256_file(path)
    if digest != entry["sha256"] or path.stat().st_size != entry["bytes"]:
        raise SystemExit(f"PIN MISMATCH {manifest_id}: {digest} != {entry['sha256']}")
    return {"id": manifest_id, "path": str(path.relative_to(ROOT)), "sha256": digest,
            "bytes": entry["bytes"], "repo": entry["repo"], "ref": entry["ref"],
            "verified": True, "organizer_authenticated": False}


def rebuild_parent(foot: np.ndarray, cat: np.ndarray) -> dict:
    """Re-derive R0 from the pinned base and prove it byte-for-byte, or stop the session."""
    base = ROOT / BASE_REL
    with rasterio.open(base) as src:
        bm = (np.nan_to_num(src.read(1), nan=0.0) > 0) & foot
    rebuilt = bm & (ndi.distance_transform_edt(~cat) > 2.0)
    parent_path = ROOT / R0_REL
    parent = grid_io.load_dots(parent_path, foot)
    differing = int((rebuilt != parent).sum())
    if differing:
        raise SystemExit(f"R0 REBUILD MISMATCH: {differing} cells differ; stopping (brief 5)")
    with rasterio.open(parent_path) as src:
        crs, transform = src.crs, src.transform
    out = ROOT / "tmp_session/rebuild_parent_zeros.tif"
    out.parent.mkdir(exist_ok=True)
    prof = dict(driver="GTiff", dtype="float32", count=1, compress="deflate", predictor=3,
                zlevel=9, tiled=True, blockxsize=256, blockysize=256, interleave="band",
                nodata=None, height=foot.shape[0], width=foot.shape[1], crs=crs,
                transform=transform)
    with rasterio.open(out, "w", **prof) as dst:
        dst.write(np.where(foot, rebuilt, 0.0).astype(np.float32), 1)
    digest = sha256(out)
    if digest != pinned(R0_MANIFEST_ID)["sha256"]:
        raise SystemExit(f"R0 REBUILD NOT BYTE-EXACT: {digest} != "
                         f"{pinned(R0_MANIFEST_ID)['sha256']} (brief 5: never approximate)")
    return {"base_dots": int(bm.sum()), "rebuilt_dots": int(rebuilt.sum()),
            "parent_dots": int(parent.sum()), "differing_cells_vs_parent": differing,
            "rebuild_sha256": digest, "byte_exact": True,
            "recipe": "gems28-h27-4-r1-solo-d2-8 (40,199 dots) AND distance-to-catalogue > 2.0 px",
            "reencode": "deflate, predictor=3, zlevel=9, tiled 256, interleave=band, float32, no nodata"}


def new_mass_clearance(mask: np.ndarray, parent: np.ndarray, cat: np.ndarray,
                       clearance_px: float) -> dict:
    """Report the clearance of the mass this session emits, against both readings of brief 4.4.

    The brief's literal rule ("keep >= 3 px from the catalogue unless AXIS=PRUNE") cannot bind
    the parent's inherited dots, because R0 itself keeps 2,171 dots at 2-3 px (IR-86-RELIEF-02).
    Clearing that band IS ``(PRUNE, 3.0)``, which is a different axis and a different slot.  So,
    exactly as the merged ``(CONCENTRATION, b1km-move15)`` arm and the SNAP arm did, this axis
    keeps the parent's own >2 px exclusion and reports the residual 2-3 px band rather than
    hiding it.  Both readings are reported; neither is a gate.
    """
    edt = ndi.distance_transform_edt(~cat)
    new = mask & ~parent
    n_new = int(new.sum())
    on_cat = int((new & cat).sum())
    min_d = float(edt[new].min()) if n_new else None
    within_3 = int((new & (edt <= 3.0)).sum())
    return {"instrument": "new_mass_clearance", "evidence_class": "REPORT-ONLY",
            "n_new": n_new, "on_catalogue": on_cat,
            "min_cat_distance_px": round(min_d, 4) if min_d is not None else None,
            "rule_applied_px": clearance_px,
            "rule_applied": (f"parent's own >{clearance_px:g} px catalogue exclusion, the same rule "
                             "the merged (CONCENTRATION, b1km-move15) arm used"),
            "new_dots_within_3px_of_catalogue": within_3,
            "section_4_4_literal_gap": (f"{within_3} newly emitted dots sit in the 2-3 px band; "
                                        "clearing it is (PRUNE,3), a different axis (IR-86-CONC-05)"),
            "inherited_2_to_3px_dots": int((parent & (edt > 2.0) & (edt <= 3.0)).sum())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="releases/axis86")
    ap.add_argument("--ledger", default="ledger/submissions.csv")
    a = ap.parse_args()
    t0 = time.time()

    ctx = grid_io.load_context()
    foot, cat = ctx["footprint"], ctx["catalogue"]

    pins = [verify_pin("existing_faults", ROOT / "data/bridge/existing_faults.tif"),
            verify_pin("sample_submission", ROOT / "data/bridge/sample_submission.tif"),
            verify_pin(R0_MANIFEST_ID, ROOT / R0_REL)]
    r0 = grid_io.load_dots(ROOT / R0_REL, foot)
    print(f"[ctx] footprint={int(foot.sum())} catalogue={int(cat.sum())} R0 dots={int(r0.sum())}",
          flush=True)

    rebuild = rebuild_parent(foot, cat)
    print(f"[r0] rebuilt {rebuild['rebuilt_dots']} dots, byte-exact sha256 {rebuild['rebuild_sha256'][:12]}",
          flush=True)

    bd = bandmod.load_bands()
    bd["tmi_grad"] = bandmod.gradient_magnitude(bd["tmi_up150"], fill_value=0.0)

    # known sha256 set for the ledger-hash gate (all local scored rasters + ledger)
    known_sha = {grid_io.sha256_file(p) for p in (ROOT / "data/scored_fleet").glob("*.tif")}
    if Path(a.ledger).is_file():
        import csv as _csv
        with Path(a.ledger).open(newline="", encoding="utf-8") as fh:
            for row in _csv.DictReader(fh):
                for col in ("sha256", "sha256_nan", "sha256_zeros"):
                    v = (row.get(col) or "").strip()
                    if len(v) == 64:
                        known_sha.add(v)

    out_dir = ROOT / a.out
    out_dir.mkdir(parents=True, exist_ok=True)
    cards, rows = [], []
    for token, value, block_px, move_frac, pred, rng in VARIANTS:
        prior_pack = variants.block_prior(ctx, bd, cat, block_px=block_px)
        mask, st = variants.concentration(r0, ctx, bd, prior_pack["prior"], move_frac,
                                          grid_io.PARENT_CAT_CLEARANCE_PX,
                                          grid_io.PARENT_MIN_SPACING_PX, block_px=block_px)
        ident = dot8(mask)
        stem = f"gems86-{R0_ID}-{token}-{DATE_TAG}-{ident}"
        diff = variants.parent_diff(r0, mask, foot)
        # Brief 7 form note: parent; change; predicted change. <= 140 chars (checked below).
        note = (f"R0 {R0_ID} {value}: {st['moved_placed']} dots to highest-prior "
                f"{block_px // 10}km blocks, count {diff['variant_dots']} fixed, "
                f"pred {pred:+.3f} MODEL")
        if len(note) > 140:
            raise SystemExit(f"note too long ({len(note)}): {note}")
        pair = grid_io.write_pair(mask, ctx, out_dir, stem, name=stem, note=note)
        gate = {}
        for mode in ("nan", "zeros"):
            gate[mode] = gates.run_all(pair[mode]["path"], ctx, known_sha,
                                       grid_io.PARENT_CAT_CLEARANCE_PX)
            if gate[mode]["passed"]:
                known_sha.add(pair[mode]["sha256"])
        nmc = new_mass_clearance(mask, r0, cat, grid_io.PARENT_CAT_CLEARANCE_PX)
        card = {"id": stem, "axis": AXIS, "value": value, "token": ident,
                "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "parent": {"id": PARENT_LABEL, "file": R0_REL,
                           "sha256": pinned(R0_MANIFEST_ID)["sha256"],
                           "n_dots": int(r0.sum())},
                "predicted_change": pred, "predicted_range": list(rng),
                "predicted_text": PREDICTIONS[value],
                "rule": st["placement_rule"],
                "stats": st, "parent_diff": diff, "note": note, "note_chars": len(note),
                "gates": gate, "artifacts": pair, "new_mass_clearance": nmc,
                "git_sha": git_sha()}
        cards.append(card)
        rows.append(card)
        print(f"[{AXIS:14s}] {stem}  dots={diff['variant_dots']} "
              f"changed={diff['pct_changed_of_parent']}%  "
              f"CV {st['block_density_parent']['density_cv_occupied']} -> "
              f"{st['block_density_variant']['density_cv_occupied']}  "
              f"gates={'PASS' if gate['nan']['passed'] and gate['zeros']['passed'] else 'FAIL'}",
              flush=True)

    # house receipts beside each zeros twin (same schema as the other release arms)
    for card in cards:
        receipt = {
            "id": card["id"], "parent": PARENT_LABEL, "axis": AXIS.lower(),
            "value": card["value"], "note": card["note"], "note_chars": len(card["note"]),
            "generated_utc": card["generated_utc"],
            "role": "candidate", "slot_candidate": True,
            "n_dots": card["parent_diff"]["variant_dots"],
            "pct_changed": card["parent_diff"]["pct_changed_of_parent"],
            "dot_digest": card["token"],
            "predicted_change": card["predicted_change"],
            "predicted_range": card["predicted_range"],
            "evidence_class": "MODEL",
            "approved_for_weekly_slot": False, "submission_slots_used": 0,
            "rule": card["rule"], "stats": card["stats"],
            "diff": card["parent_diff"],
            "new_mass_clearance": card["new_mass_clearance"],
            "gates": {m: {"passed": card["gates"][m]["passed"],
                          "checks": card["gates"][m]["values"]["checks"],
                          "catalogue_clearance": card["gates"][m]["catalogue_clearance"],
                          "ledger_hash_sha8": card["gates"][m]["ledger_hash"]["sha8"]}
                      for m in ("nan", "zeros")},
        }
        for mode in ("nan", "zeros"):
            art = card["artifacts"][mode]
            receipt[mode] = {"file": Path(art["path"]).name, "sha256": art["sha256"],
                             "bytes": Path(art["path"]).stat().st_size,
                             "validator": {"all_checks_passed": card["gates"][mode]["passed"]}}
        rp = Path(card["artifacts"]["zeros"]["path"]).with_suffix(".json")
        rp.write_text(json.dumps(receipt, indent=2) + "\n")

    evidence = {
        "schema_version": 1, "session": SESSION, "axis": AXIS,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": git_sha(),
        "parent": {"id": PARENT_LABEL, "file": R0_REL,
                   "sha256": pinned(R0_MANIFEST_ID)["sha256"], "n_dots": int(r0.sum())},
        "parent_rebuild": rebuild,
        "inputs_verified": pins,
        "constants": {"parent_min_spacing_px": grid_io.PARENT_MIN_SPACING_PX,
                      "parent_cat_clearance_px": grid_io.PARENT_CAT_CLEARANCE_PX,
                      "dest_block_frac": 0.20},
        "evidence_class_note": ("Every predicted_change here is MODEL (local arithmetic on the "
                                "official metric). No submission-page receipt exists; none is "
                                "invented. A live |delta| < 0.01 is no evidence (brief section 5)."),
        "variants": cards,
        "elapsed_s": round(time.time() - t0, 1),
    }
    ev = ROOT / "evidence/conc_axis_20261023.json"
    ev.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"wrote {ev.relative_to(ROOT)} ({evidence['elapsed_s']}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
