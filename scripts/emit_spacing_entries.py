#!/usr/bin/env python3
"""Emit ``ledger/variants_spacing.json`` in the canonical variant schema.

One generator owns the ledger (``scripts/build_ledger.py``); this converts the session's run card
(``evidence/spacing_axis_20261023.json``) into that schema instead of writing a second generator,
and it is where the statuses are decided:

* ``(SPACING, pdisk16)``, ``(SPACING, lattice16)``, ``(SPACING, strike16)`` are new
  ``(parent, axis, value)`` keys: SPACING is the one brief-5 axis no earlier session built, so all
  three are ``BUILT``.
* ``(SPACING, random16)`` is the null control the axis was designed around.  It is recorded
  ``CONTROL``, never promoted to a slot candidate, so nobody mistakes a displacement artifact for
  a bet.

Usage::  .venv/bin/python scripts/emit_spacing_entries.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_CARD = ROOT / "evidence" / "spacing_axis_20261023.json"
OUT = ROOT / "ledger" / "variants_spacing.json"
ARMS = ("pdisk", "lattice", "strike")
CONTROL = "random"

#: Preregistered before the surrogate was read: the axis's promise is that a *law* beats chance.
PREDICTIONS = {
    "pdisk": ("+0.0015 (MODEL; band +0.0015..+0.0072, translated-ensemble bracket). Relocate every "
              "dot owning <=16 of its 29 kernel-disc cells to the largest local gap, any "
              "direction. Below the 0.01 evidence floor by design: this is a mechanism probe, not "
              "a score play. Falsifier: live delta <= -0.005, i.e. the coverage the surrogate pays "
              "for is off-fault mass the live metric charges for."),
    "lattice": ("+0.0019 (MODEL; band +0.0019..+0.0072). Same selection and objective, "
                 "destinations restricted to a hexagonal covering lattice (a=5.196 px). The largest "
                 "surrogate read and the largest coverage gain per unit of displacement. Same "
                 "falsifier as pdisk; a second falsifier is IR-86-CONC-02's band, since an even "
                 "arrangement is what 'spread the mass' would look like."),
    "strike": ("+0.0020 (MODEL; band +0.0020..+0.0050, 3/4 quadrants positive). Same selection and "
                "objective, destinations restricted to the local dot ridge (+/-1 px across, >=2 px "
                "along), so mass extends the trace instead of leaving it: the only arm whose "
                "false-positive term rises by less than half the others. Falsifier: live delta "
                "<= -0.005 while pdisk/lattice are flat, which says the kernel is isotropic and "
                "trace continuity buys nothing."),
    "random": ("+0.0002 (MODEL; band +0.0002..+0.0050). NULL CONTROL, not a slot candidate: the "
                "same dots relocated to a uniform random eligible cell in the same window. Every "
                "arm is read against this number, not against zero."),
}


def main() -> int:
    card = json.loads(RUN_CARD.read_text())
    sgmc = card["instruments"]["sgmc_offcatalogue_surrogate"]["arms"]
    entries = []
    for law in ARMS + (CONTROL,):
        v = card["variants"][law]
        d = v["parent_diff"]
        st = v["stats"]
        sel = v["selection"]
        pred = sgmc["control_random" if law == CONTROL else law]
        entries.append({
            "site": "GEMSDOE86",
            "id": v["id"],
            "parent": "h33-h33-2-b2",
            "axis": "spacing",
            "value": v["value"],
            "encoding": "nan",
            "n_dots": d["variant_dots"],
            "pct_changed": d["pct_changed_of_parent"],
            "sha256": v["artifacts"]["nan"]["sha256"],
            "sha8": v["token"],
            "sha256_zeros": v["artifacts"]["zeros"]["sha256"],
            "files": [str(Path(v["artifacts"]["nan"]["path"]).relative_to(ROOT)),
                      str(Path(v["artifacts"]["zeros"]["path"]).relative_to(ROOT))],
            "status": "CONTROL" if law == CONTROL else "BUILT",
            "slot_candidate": law in ARMS,
            "predicted_change": PREDICTIONS[law],
            "source_url": "https://github.com/buffedlizard55-lab/GEMSDOE86/tree/arena/c8365759-gemsdoe86",
            "diff": {
                "n_parent": d["parent_dots"], "n_candidate": d["variant_dots"],
                "retained": d["shared_dots"], "removed": d["dropped"], "added": d["added"],
                "pct_of_parent_changed": d["pct_changed_of_parent"],
                "pct_relocated_of_parent": st["pct_relocated_of_parent"],
                "jaccard": d["jaccard"], "count_exact": d["count_delta"] == 0,
                "axis_note": st["placement_rule"],
            },
            "spacing": {
                "credit_threshold_cells": sel["credit_threshold"],
                "kernel_disc_cells": sel["kernel_disc_cells"],
                "selected_dots": sel["n_selected"],
                "placed": st["moved_placed"], "unplaced_kept_in_place": st["moved_unplaced"],
                "placed_after_widening": st["placed_outside_window"],
                "strike_isotropic_fallback": st["strike_fallback_isotropic"],
                "window_px": st["window_px"], "floor_px": st["floor_px"],
                "clearance_px_new_mass": st["clearance_px"],
                "mean_displacement_px": st["mean_displacement_px"],
                "max_displacement_px": st["max_displacement_px"],
                "nn_mean_px_before_after": [st["parent_nn"]["nn_mean_px"],
                                            st["variant_nn"]["nn_mean_px"]],
                "dots_below_kernel_radius_before_after":
                    [st["parent_nn"]["dots_below_kernel_radius"],
                     st["variant_nn"]["dots_below_kernel_radius"]],
                "exclusive_cells_mean_before_after": [st["exclusive_parent"]["exclusive_cells_mean"],
                                                      st["exclusive_variant"]["exclusive_cells_mean"]],
                "union_cover_gain_cells": st["union_cover_gain_cells"],
                "parent_redundancy_fraction": sel["parent_redundancy_fraction"],
                "min_cat_edt_px_variant": st["cat_edt_min_variant"],
                "destinations_on_support_surface_pct": None,   # filled from the support read below
            },
            "model": {
                "instrument": "SGMC off-catalogue exact DTI (gems57.metric.dti_binary), RELIEF convention",
                "delta": pred["delta"], "relative_pct": pred["relative_pct"],
                "delta_tp": pred["delta_tp"], "delta_fp": pred["delta_fp"],
                "quadrant_positive": f"{pred['quadrant_sign_agreement']}/4",
                "translated_mean": pred["translated_mean"],
                "translated_range": [pred["translated_min"], pred["translated_max"]],
                "evidence_class": "MODEL",
                "control_delta": sgmc["control_random"]["delta"],
                "law_minus_control": round(pred["delta"] - sgmc["control_random"]["delta"], 6),
            },
            "gates_passed": bool(v["gates"]["nan"]["passed"] and v["gates"]["zeros"]["passed"]
                                  and v["new_mass_gate"]["passed"]),
            "receipt_score": "",
        })
    support = card["instruments"]["support_surface_read"]["arms"]
    for e in entries:
        law = e["id"].split("-sp-")[1].split("16-")[0]
        e["spacing"]["destinations_on_support_surface_pct"] = support[law]["destinations_on_support_pct"]
    OUT.write_text(json.dumps(entries, indent=2) + "\n")
    print(json.dumps({"wrote": str(OUT.relative_to(ROOT)), "entries": len(entries),
                      "built": [e["id"] for e in entries if e["status"] == "BUILT"],
                      "control": [e["id"] for e in entries if e["status"] == "CONTROL"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
