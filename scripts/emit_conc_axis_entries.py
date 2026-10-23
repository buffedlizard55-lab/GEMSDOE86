#!/usr/bin/env python3
"""Append this session's CONCENTRATION entries to ``ledger/variants_concentration.json``.

The repository keeps ONE ledger generator (``scripts/build_ledger.py``), which reads the set of
``ledger/variants_*.json`` files.  This script converts this session's run card
(``evidence/conc_axis_20261023.json``) into that schema and **appends** it to the existing file,
so the entries PR #37 wrote (``(PRUNE, collar3px)``, ``(CONCENTRATION, b1km-move15)``,
``(SNAP, 2px)``) are preserved rather than overwritten.  It never writes ``submissions.csv``
directly and never invents a receipt.

Usage::  .venv/bin/python scripts/emit_conc_axis_entries.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_CARD = ROOT / "evidence" / "conc_axis_20261023.json"
LEDGER_VARIANTS = ROOT / "ledger" / "variants_concentration.json"
PR = "https://github.com/buffedlizard55-lab/GEMSDOE86/pull/39"


def entry_for(v: dict) -> dict:
    d = v["parent_diff"]
    s = v["stats"]
    return {
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
        "status": "BUILT",
        "duplicate_of": "",
        "predicted_change": v["predicted_text"],
        "source_url": PR,
        "diff": {
            "n_parent": d["parent_dots"], "n_candidate": d["variant_dots"],
            "retained": d["shared_dots"], "removed": d["dropped"], "added": d["added"],
            "pct_of_parent_changed": d["pct_changed_of_parent"],
            "pct_changed": d["pct_changed_of_parent"],
            "jaccard": d["jaccard"], "count_exact": d["count_delta"] == 0,
            "axis_note": s["placement_rule"],
        },
        "gates_passed": bool(v["gates"]["nan"]["passed"] and v["gates"]["zeros"]["passed"]),
        "blocks": {
            "block_size": s["block_size"], "moved": s["moved_placed"],
            "moved_target": s["moved_target"], "dest_blocks": s.get("dest_blocks"),
            "density_cv_occupied_parent": s["block_density_parent"]["density_cv_occupied"],
            "density_cv_occupied_variant": s["block_density_variant"]["density_cv_occupied"],
            "occupied_blocks_parent": s["block_density_parent"]["occupied_blocks"],
            "occupied_blocks_variant": s["block_density_variant"]["occupied_blocks"],
            "mean_dots_per_occupied_block_parent":
                s["block_density_parent"]["mean_dots_per_occupied_block"],
            "mean_dots_per_occupied_block_variant":
                s["block_density_variant"]["mean_dots_per_occupied_block"],
            "min_cat_edt_px": s["min_cat_edt_variant"],
        },
        "new_mass_clearance": v["new_mass_clearance"],
    }


def main() -> int:
    card = json.loads(RUN_CARD.read_text())
    existing = json.loads(LEDGER_VARIANTS.read_text()) if LEDGER_VARIANTS.is_file() else []
    have = {(e.get("axis", "").lower(), e.get("value", "")) for e in existing}
    fresh = []
    for v in card["variants"]:
        key = (v["axis"].lower(), v["value"])
        if key in have:
            print(f"  skip duplicate (axis, value) = {key}")
            continue
        fresh.append(entry_for(v))
        have.add(key)
    out = existing + fresh
    LEDGER_VARIANTS.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"wrote": str(LEDGER_VARIANTS.relative_to(ROOT)),
                      "total_entries": len(out), "appended": [e["id"] for e in fresh]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
