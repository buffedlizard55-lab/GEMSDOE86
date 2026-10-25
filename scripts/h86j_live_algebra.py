#!/usr/bin/env python3
"""Closed-form bounds on the hidden live truth implied by two pixel-exact
fleet edits (H86J-LSI review, Q1).

Both edits are pure deletions verified pixel-exactly in this repository
(``docs/evidence/h86f-h33-forensics.json``, ``research/H33_ANALYSIS.md``):

* GEMSDOE25 d2.8 (44,090 dots, 0.2600)  -> GEMSDOE28 (40,199, 0.2708):
  delete 3,891 dots at catalogue distance exactly 1 px.
* GEMSDOE28 (40,199, 0.2708) -> GEMSDOE32 H33 (37,654, 0.2778):
  delete 2,545 dots at catalogue distance in (1, 2] px.

For a binary field, DTI = T / D with D = 0.2 T + 0.2 (n - M) + 0.8 G.
Deleting b dots that carried no truth credit and no self-credit leaves T and
M unchanged and lowers D by 0.2 b, hence T = 0.2 b / (1/DTI0 - 1/DTI1).
If the deleted dots carried any credit the same score gain requires a larger
T, so each value is a LOWER bound on T.  Scores are OWNER-REPORTED (4 d.p.);
the rounding interval is propagated.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/evidence/h86j-live-algebra.json"

EDITS = [
    {"edit": "GEMSDOE25 d2.8 -> GEMSDOE28 (delete d_cat = 1 px)", "b": 3891,
     "dti0": 0.2600, "dti1": 0.2708, "n1": 40199},
    {"edit": "GEMSDOE28 -> GEMSDOE32 H33 (delete 1 < d_cat <= 2 px)", "b": 2545,
     "dti0": 0.2708, "dti1": 0.2778, "n1": 37654},
]
HALF_ULP = 0.00005


def t_lower(b, d0, d1):
    return 0.2 * b / (1.0 / d0 - 1.0 / d1)


def main() -> int:
    rows = []
    for e in EDITS:
        t = t_lower(e["b"], e["dti0"], e["dti1"])
        lo = t_lower(e["b"], e["dti0"] - HALF_ULP, e["dti1"] + HALF_ULP)
        hi = t_lower(e["b"], e["dti0"] + HALF_ULP, e["dti1"] - HALF_ULP)
        D1 = t / e["dti1"]
        # G range: FP between 0 (upper G) and n1 - T/3 (dots on lines; M ~ T/3)
        g_upper = (D1 - 0.2 * t) / 0.8
        g_lines = (D1 - 0.2 * t - 0.2 * (e["n1"] - t / 3.0)) / 0.8
        rows.append({**e, "T_lower_bound": t, "T_rounding_interval": [lo, hi],
                     "D_after": D1, "G_if_FP_zero": g_upper,
                     "G_if_dots_on_lines_M_eq_T_over_3": g_lines})
    doc = {"evidence_class": "DERIVED from OWNER-REPORTED scores + pixel-exact edits (not a score)",
           "formula": "T = 0.2 b / (1/DTI0 - 1/DTI1)  (lower bound)",
           "rows": rows}
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    print(json.dumps(doc, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
