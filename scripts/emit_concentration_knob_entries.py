#!/usr/bin/env python3
"""Emit ``ledger/variants_concentration_knobs.json`` for the one canonical ledger generator.

``scripts/build_ledger.py`` is the only writer of ``ledger/submissions.csv``; it ingests a
fixed list of ``ledger/variants_*.json`` files.  This script converts this session's run card
(``evidence/concentration_knobs_20261023.json``) into that schema.  It does not write the CSV.

Predictions are ``MODEL`` and carry the pre-registration trail: the number written in the run
card was fixed before the report-only instruments ran; the number written here is the revised
one, and both are stated so nobody can present the revision as the original bet.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_CARD = ROOT / "evidence" / "concentration_knobs_20261023.json"
INSTRUMENTS = ROOT / "evidence" / "concentration_instruments_20261023.json"
OUT = ROOT / "ledger" / "variants_concentration_knobs.json"
SOURCE_URL = "https://github.com/buffedlizard55-lab/GEMSDOE86/pull/45"

#: (axis, value) keys already in the ledger.  A collision would make the new file a
#: duplicate, not a candidate; the build refuses to write a colliding value, so this is
#: an assertion about the ledger, checked again at merge time.
ALREADY_IN_LEDGER = {("CONCENTRATION", "b1km-move15")}

#: A parallel session (PR #43, branch ``arena/0bcc88da-gemsdoe86``) built
#: ``(CONCENTRATION, b5km-move15)`` from the same parent with the same knobs while this branch was
#: open: its artifact name carries the token ``73802181``, which is this branch's dot-set digest for
#: that arm, i.e. the two are the same dot set.  Brief section 6 dedupes on exactly
#: (parent, axis, value), so this branch's copy is recorded as a duplicate and is not a slot
#: candidate (IR-86-CONC-07).
DUPLICATE_OF = {"b5km-move15": "CONCENTRATION / b5km-move15 (PR #43, identical dot-set token 73802181)"}

REVISED = {
    "b5km-move15": ("+0.001 (MODEL, band -0.008..+0.008). Preregistered +0.004 in the run card "
                    "before any instrument ran. Revised twice, in that order: (i) the hide-and-"
                    "recover proxy gain is circular - the TMI-only prior recovers nothing "
                    "(+0.0008, CI -0.0044..+0.0073) while the catalogue-only prior carries all of "
                    "it (+0.0149); (ii) on the SGMC independent map every arm including the "
                    "shuffled-prior null loses 0.012-0.020, so moving mass costs credit and this "
                    "prior does not earn it back. Prediction is now indistinguishable from zero."),
    "b1km-move24": ("-0.001 (MODEL, band -0.012..+0.008). Preregistered +0.008. Largest dose on "
                    "the axis (48.0% of dots changed, inside the brief's 1-50% band) and therefore "
                    "the largest exposure to the measured cost of moving (SGMC -0.0200 vs the "
                    "shuffled-prior null's -0.0120). Its value is as a dose readout, not a bet."),
    "b1km-move15-t05": ("+0.002 (MODEL, band -0.007..+0.009). Preregistered +0.007. Sharpest "
                        "destination selectivity (top 5% of blocks) and the best proxy in the set "
                        "(+0.0195 vs the +0.0122 of the 5 km arm) - but that proxy ordering is the "
                        "circular catalogue term, and the SGMC control is -0.0139. Below the "
                        "evidence floor either way."),
}


def main() -> int:
    card = json.loads(RUN_CARD.read_text())
    instruments = json.loads(INSTRUMENTS.read_text()) if INSTRUMENTS.is_file() else {}
    entries = []
    for v in card["variants"]:
        d = v["parent_diff"]
        s = v["stats"]
        key = (v["axis"], v["value"])
        if key in ALREADY_IN_LEDGER:
            raise SystemExit(f"{(key)} is already in the ledger; this file would be a duplicate")
        label = v["token"]
        proxy = (instruments.get("pooled", {}).get(label) or {}) if instruments else {}
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
            "status": "BUILT-DUPLICATE" if v["value"] in DUPLICATE_OF else "BUILT",
            "duplicate_of": DUPLICATE_OF.get(v["value"], ""),
            "predicted_change": REVISED[v["value"]],
            "preregistered_change": v["predicted_change"],
            "source_url": SOURCE_URL,
            "diff": {
                "n_parent": d["parent_dots"], "n_candidate": d["variant_dots"],
                "retained": d["shared_dots"], "removed": d["dropped"], "added": d["added"],
                "pct_of_parent_changed": d["pct_changed_of_parent"],
                "pct_changed": d["pct_changed_of_parent"],
                "jaccard": d["jaccard"], "count_exact": d["count_delta"] == 0,
                "axis_note": s.get("placement_rule", ""),
            },
            "gates_passed": bool(v["gates"]["nan"]["passed"] and v["gates"]["zeros"]["passed"]),
            "knob": v["knob"],
            "blocks": {
                "block_size": s["block_size"], "moved": s["moved_placed"],
                "moved_target": s["moved_target"], "dest_blocks": s["dest_blocks"],
                "dest_block_frac": s["dest_block_frac"],
                "placed_at_parent_spacing": s["placed_at_parent_spacing"],
                "placed_at_relaxed_spacing": s["placed_at_relaxed_spacing"],
                "density_cv_occupied_parent":
                    s["block_density_at_variant_block"]["before"]["density_cv_occupied"],
                "density_cv_occupied_variant":
                    s["block_density_at_variant_block"]["after"]["density_cv_occupied"],
                "density_cv_1km_parent":
                    s["block_density_at_1km"]["before"]["density_cv_occupied"],
                "density_cv_1km_variant":
                    s["block_density_at_1km"]["after"]["density_cv_occupied"],
                "occupied_blocks_parent":
                    s["block_density_at_variant_block"]["before"]["occupied_blocks"],
                "occupied_blocks_variant":
                    s["block_density_at_variant_block"]["after"]["occupied_blocks"],
                "min_cat_edt_px": s["min_cat_edt_variant"],
            },
            "report_only_proxy": {
                "evidence_class": "PROXY",
                "delta_vs_r0": (proxy.get("paired_differences", {})
                                .get("r0", {}).get("delta")),
                "ci95": (proxy.get("paired_differences", {}).get("r0", {}).get("ci95")),
                "caveat": ("circular for any catalogue-derived prior: the withheld truth IS the "
                           "catalogue, so the catalogue-density term is rewarded by construction. "
                           "The TMI-only decomposition (PROXY +0.0008) is the non-circular check and "
                           "it is flat. Never a gate, never a score."),
            },
        }
        entries.append(entry)
    OUT.write_text(json.dumps(entries, indent=2) + "\n")
    print(json.dumps({"wrote": str(OUT.relative_to(ROOT)), "entries": len(entries),
                      "ids": [e["id"] for e in entries]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
