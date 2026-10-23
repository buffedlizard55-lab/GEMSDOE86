#!/usr/bin/env python3
"""Emit ``ledger/variants_mass_econ.json`` from the session's run card, in the canonical schema.

The repository keeps ONE ledger generator (``scripts/build_ledger.py``), which reads every
``ledger/variants_*.json``.  This script converts ``evidence/mass_econ_axis_20261023.json`` into
that schema instead of adding a second generator.

Statuses are assigned deliberately:

* all three rasters pass both encodings' gates and none of their hashes is in the ledger, so they
  are ``BUILT``;
* ``plus10pct-extend-rand`` is additionally marked ``CONTROL`` and ``slot_candidate: false`` --
  it is the null the extend arm is read against, never an upload;
* no arm is a slot candidate: the instrument audit
  (``evidence/mass_instrument_monotonicity.json``) shows the surrogate is monotone in dot count, so
  none of the three MODEL deltas can be attributed to the axis.

Usage::  .venv/bin/python scripts/emit_mass_econ_entries.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_CARD = ROOT / "evidence" / "mass_econ_axis_20261023.json"
AUDIT = ROOT / "evidence" / "mass_instrument_monotonicity.json"
OUT = ROOT / "ledger" / "variants_mass_econ.json"

CONTROL = "plus10pct-extend-rand"


def main() -> int:
    card = json.loads(RUN_CARD.read_text())
    audit = json.loads(AUDIT.read_text()) if AUDIT.is_file() else {}
    entries = []
    for v in card["variants"]:
        d = v["parent_diff"]
        s = v["stats"]
        is_control = v["value"] == CONTROL
        surrogate = card.get("sgmc_surrogate", {}).get("arms", {}).get(v["value"], {})
        entries.append({
            "site": "GEMSDOE86",
            "id": v["id"],
            "parent": "h33-h33-2-b2",
            "axis": "mass",
            "value": v["value"],
            "encoding": "nan",
            "n_dots": d["variant_dots"],
            "pct_changed": d["pct_changed_of_parent"],
            "sha256": v["artifacts"]["nan"]["sha256"],
            "sha8": v["token"],
            "sha256_zeros": v["artifacts"]["zeros"]["sha256"],
            "files": [v["artifacts"]["nan"]["file"], v["artifacts"]["zeros"]["file"]],
            "status": "CONTROL" if is_control else "BUILT",
            "slot_candidate": False,
            "predicted_change": v["predicted_change"],
            "predicted_change_preregistered": v["predicted_change_preregistered"],
            "source_url": "https://github.com/buffedlizard55-lab/GEMSDOE86/tree/arena/c6b14099-gemsdoe86",
            "diff": {
                "n_parent": d["parent_dots"], "n_candidate": d["variant_dots"],
                "retained": d["shared_dots"], "removed": d["dropped"], "added": d["added"],
                "pct_of_parent_changed": d["pct_changed_of_parent"],
                "pct_changed": d["pct_changed_of_parent"],
                "jaccard": d["jaccard"], "count_exact": False,
                "count_delta": d["count_delta"],
                "axis_note": s.get("rule", ""),
            },
            "mass": {
                "dose_dots": card["n_dose"],
                "selection": s.get("selection_rule") or s.get("rule"),
                "unique_credit_dropped_mean": s.get("dropped_credit_mean"),
                "kept_unique_credit_min": s.get("kept_credit_min"),
                "tie_class_at_cut": s.get("tie_class_at_cut"),
                "admissible_cells": s.get("admissible_cells"),
                "candidate_cells": s.get("candidate_cells"),
                "shortfall": s.get("shortfall"),
                "new_mass_min_cat_edt_px": s.get("min_cat_edt_px_added"),
                "new_mass_clearance_ok": s.get("new_mass_clearance_ok"),
                "parent_unique_credit_mean": s.get("marginal_credit_mean")
                or s.get("parent_u_stats", {}).get("marginal_credit_mean"),
                "parent_overlap_writeoff_fraction": s.get("overlap_writeoff_fraction")
                or s.get("parent_u_stats", {}).get("overlap_writeoff_fraction"),
            },
            "model": {
                "instrument": "exact DTI vs off-catalogue USGS SGMC (report-only MODEL)",
                "delta_dti": surrogate.get("delta_dti"),
                "quadrant_deltas": surrogate.get("quadrant_deltas"),
                "quadrants_positive": surrogate.get("quadrants_positive"),
                "translation_range": surrogate.get("translation_range"),
                "law_vs_chance": card.get("sgmc_surrogate", {}).get("law_vs_chance"),
                "instrument_mass_monotone": audit.get("monotone_in_dot_count"),
                "usable_for_this_axis": False,
                "why": ("the surrogate's response to random add/delete is monotone in dot count "
                        "(evidence/mass_instrument_monotonicity.json), so its delta on a "
                        "mass-changing arm measures mass, not the axis"),
            },
            "gates_passed": bool(v["gates"]["nan"]["passed"] and v["gates"]["zeros"]["passed"]),
        })
    OUT.write_text(json.dumps(entries, indent=2) + "\n")
    print(json.dumps({"wrote": str(OUT.relative_to(ROOT)), "entries": len(entries),
                      "built": [e["id"] for e in entries if e["status"] == "BUILT"],
                      "control": [e["id"] for e in entries if e["status"] == "CONTROL"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
