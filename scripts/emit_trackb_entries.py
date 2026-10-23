#!/usr/bin/env python3
"""Emit ledger/variants_trackb.json from the TRACKB run card. All three arms are
BUILT Phase-2 trace products, slot_candidate=false (brief 5: TRACKB is not a
weekly-slot candidate unless the human decides). Predicted change is the SGMC
surrogate delta of the *raster rendering* (MODEL) and is expected negative on
mass grounds alone; it is not a prediction about the traces' Phase-2 value."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
card = json.loads((ROOT / "evidence/trackb_axis_20261023.json").read_text())
sgmc = card["instruments"]["sgmc_offcatalogue_surrogate"]["arms"]
entries = []
for value, v in card["variants"].items():
    d, st = v["parent_diff"], v["chain_stats"]
    entries.append({
        "site": "GEMSDOE86", "id": v["id"], "parent": "h33-h33-2-b2",
        "axis": "trackb", "value": value, "encoding": "nan",
        "n_dots": d["variant_dots"], "pct_changed": d["pct_changed_of_parent"],
        "sha256": v["artifacts"]["nan"]["sha256"], "sha8": v["token"],
        "sha256_zeros": v["artifacts"]["zeros"]["sha256"],
        "files": [v["artifacts"]["nan"]["path"], v["artifacts"]["zeros"]["path"], v["geojson"]],
        "status": "BUILT", "slot_candidate": False,
        "predicted_change": (f"{v['predicted_change_model']:+.3f} (MODEL, SGMC surrogate on the "
                             f"raster rendering; expected negative on mass alone). Phase-2 trace "
                             f"product: {st['n_traces']} traces >=1 km, {st['pct_parent_dots_traced']}% "
                             f"of R0 dots strike-chained. Not a slot candidate unless the human decides."),
        "source_url": "https://github.com/buffedlizard55-lab/GEMSDOE86/tree/arena/821a630a-gemsdoe86",
        "diff": {"n_parent": d["parent_dots"], "n_candidate": d["variant_dots"],
                 "retained": d["shared_dots"], "removed": d["dropped"], "added": d["added"],
                 "pct_of_parent_changed": d["pct_changed_of_parent"], "jaccard": d["jaccard"],
                 "axis_note": f"turning-angle ceiling {st['max_turn_deg']} deg, step <=4.5 px, >=1 km"},
        "trackb": {"n_traces": st["n_traces"], "n_traced_dots": st["n_traced_dots"],
                   "pct_parent_dots_traced": st["pct_parent_dots_traced"],
                   "total_length_km": st["total_length_km"], "median_length_km": st["median_length_km"],
                   "max_length_km": st["max_length_km"], "geojson": v["geojson"],
                   "geojson_sha256": v["geojson_sha256"]},
        "model": {"instrument": "SGMC off-catalogue exact DTI (raster rendering)", "delta": sgmc[value]["delta_vs_r0"],
                  "evidence_class": "MODEL"},
        "gates_passed": bool(v["gates"]["nan"]["passed"] and v["gates"]["zeros"]["passed"]),
        "receipt_score": "",
    })
out = ROOT / "ledger/variants_trackb.json"
out.write_text(json.dumps(entries, indent=2) + "\n")
print(json.dumps({"wrote": str(out.relative_to(ROOT)), "entries": [e["id"] for e in entries]}, indent=2))
