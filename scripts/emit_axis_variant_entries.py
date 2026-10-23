#!/usr/bin/env python3
"""Emit ``ledger/variants_concentration.json`` in the canonical variant schema.

The repository keeps ONE ledger generator (``scripts/build_ledger.py``) which reads a set of
``ledger/variants_*.json`` files.  This script converts this session's run card
(``evidence/axis_variants.json``) into that schema instead of writing a second generator.

Statuses are assigned here, deliberately:

* ``CONCENTRATION / b1km-move15`` was unbuilt on ``main`` when this branch merged, so it is
  ``BUILT``.
* ``PRUNE / collar3px`` and ``SNAP / 2px`` collide with ``(parent, axis, value)`` keys already
  in the ledger from parallel sessions (``PRUNE / 3`` and ``SNAP / 2``).  Brief section 6
  dedupes on exactly that key, so both are recorded ``BUILT-DUPLICATE`` and are NOT slot
  candidates.  They stay on disk for audit; they are not promoted.

Usage::  .venv/bin/python scripts/emit_axis_variant_entries.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_CARD = ROOT / "evidence" / "axis_variants.json"
OUT = ROOT / "ledger" / "variants_concentration.json"

#: (axis, value) keys already built on main by parallel sessions, checked at merge time.
ALREADY_BUILT_ON_MAIN = {("PRUNE", "collar3px"): "PRUNE / 3", ("SNAP", "2px"): "SNAP / 2"}

PREDICTIONS = {
    "PRUNE": ("+0.004 (MODEL). Widen the catalogue collar from the parent's 2 px to 3 px and "
              "refill to hold the count. DUPLICATE of (PRUNE,3) already in the ledger; not a "
              "slot candidate."),
    "SNAP": ("+0.004 (MODEL). Move each dot <= 2 px to the strongest TMI/DEM edge response. "
             "DUPLICATE of (SNAP,2) already in the ledger; that arm's own instrument reads "
             "negative against a random-response null, so this is not a slot candidate."),
    "CONCENTRATION": ("+0.006 (range +0.003..+0.010, MODEL). Move 15% of dots out of the "
                      "lowest-prior 1 km blocks into the highest-prior fifth, count fixed, "
                      "placement geometric only. Block-density CV 0.6235 -> 0.7644, i.e. away "
                      "from the reported 0.51-0.59 band, which is the stated falsifier."),
}


def main() -> int:
    card = json.loads(RUN_CARD.read_text())
    entries = []
    for v in card["variants"]:
        d = v["parent_diff"]
        s = v["stats"]
        key = (v["axis"], v["value"])
        dup = ALREADY_BUILT_ON_MAIN.get(key)
        entry = {
            "site": "GEMSDOE86",
            "id": v["id"],
            "parent": "h33-h33-2-b2",
            "axis": v["axis"].lower(),
            "value": v["value"],
            "encoding": "nan",
            "n_dots": d["variant_dots"],
            "pct_changed": d["pct_changed_of_parent"],
            "sha256": v["artifacts"]["nan"]["sha256"],
            "sha8": v["token"],
            "sha256_zeros": v["artifacts"]["zeros"]["sha256"],
            "files": [str(Path(v["artifacts"]["nan"]["path"]).relative_to(ROOT)),
                      str(Path(v["artifacts"]["zeros"]["path"]).relative_to(ROOT))],
            "status": "BUILT-DUPLICATE" if dup else "BUILT",
            "duplicate_of": dup or "",
            "predicted_change": PREDICTIONS.get(v["axis"], ""),
            "source_url": "https://github.com/buffedlizard55-lab/GEMSDOE86/pull/37",
            "diff": {
                "n_parent": d["parent_dots"], "n_candidate": d["variant_dots"],
                "retained": d["shared_dots"], "removed": d["dropped"], "added": d["added"],
                "pct_of_parent_changed": d["pct_changed_of_parent"],
                "pct_changed": d["pct_changed_of_parent"],
                "jaccard": d["jaccard"], "count_exact": d["count_delta"] == 0,
                "axis_note": s.get("refill_pool") or s.get("placement_rule") or s.get("response", ""),
            },
            "gates_passed": bool(v["gates"]["nan"]["passed"] and v["gates"]["zeros"]["passed"]),
        }
        if v["axis"] == "CONCENTRATION":
            entry["blocks"] = {
                "block_size": s["block_size"], "moved": s["moved_placed"],
                "moved_target": s["moved_target"],
                "dest_blocks": s.get("dest_blocks"),
                "density_cv_occupied_parent": s["block_density_parent"]["density_cv_occupied"],
                "density_cv_occupied_variant": s["block_density_variant"]["density_cv_occupied"],
                "occupied_blocks_parent": s["block_density_parent"]["occupied_blocks"],
                "occupied_blocks_variant": s["block_density_variant"]["occupied_blocks"],
                "min_cat_edt_px": s["min_cat_edt_variant"],
            }
        if v["axis"] == "SNAP":
            entry["movement"] = {
                "n_snapped": s["dots_moved"], "mean_displacement_px_moved": s["mean_displacement_px"],
                "median_displacement_px_moved": s["median_displacement_px"],
                "max_displacement_px": s["max_displacement_px"],
                "blocked_by_occupancy": s["dots_blocked_by_occupancy"],
                "blocked_by_clearance": s["dots_blocked_by_clearance"],
                "cat_edt_mean_before": s["cat_edt_mean_parent"],
                "cat_edt_mean_after": s["cat_edt_mean_variant"],
            }
        if v["axis"] == "PRUNE":
            entry["refill"] = {
                "removed": s["removed_dots"], "refilled": s["refilled_dots"],
                "at_parent_spacing": s.get("refilled_at_parent_spacing"),
                "at_relaxed_spacing": s.get("refilled_at_relaxed_spacing"),
                "shortfall": s["refill_shortfall"],
                "cat_edt_mean_before": s["cat_edt_mean_parent"],
                "cat_edt_mean_after": s["cat_edt_mean_variant"],
                "min_cat_edt_px": s["min_cat_edt_variant"],
            }
        entries.append(entry)
    OUT.write_text(json.dumps(entries, indent=2) + "\n")
    print(json.dumps({"wrote": str(OUT.relative_to(ROOT)), "entries": len(entries),
                      "built": [e["id"] for e in entries if e["status"] == "BUILT"],
                      "duplicates": [e["id"] for e in entries if e["status"] != "BUILT"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
