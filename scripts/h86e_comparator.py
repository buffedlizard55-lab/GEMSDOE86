#!/usr/bin/env python3
"""Comparator correction for H86E (not a new experiment).

The R0 recipe is: GEMSDOE25 dotted-h19-5-d2-8 (registry sha256 91eae1ca42ec...)
minus every dot within 2 px of the catalogue.  The fold-fair version applies the
collar with the VISIBLE catalogue only (same comparator as the H86C-KSLB card).
Also scores the H19-5 parent and the d2.8 file as-is on the identical split.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor"), str(ROOT / "src")]

from gems57 import evaluate_holdout as E, grid, holdout as H  # noqa: E402
from gems86_ridf import pipeline as P  # noqa: E402


def by_prefix(inv: list[dict], prefix: str) -> tuple[Path, dict]:
    matches = [r for r in inv if r["sha256"].startswith(prefix)]
    assert len(matches) == 1
    return ROOT / "data/registry_ext" / (matches[0]["sha256"] + ".tif"), matches[0]


def main() -> int:
    inv = json.loads((ROOT / "research/upstream/registry_inventory.json").read_text())["rasters"]
    g = grid.load_grid(ROOT / "data")
    fp = g.footprint
    folds, _ = H.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3)
    dvis = ndi.distance_transform_edt(~folds[0]["visible"])
    d28_path, d28_rec = by_prefix(inv, "91eae1ca42ec")
    with rasterio.open(d28_path) as s:
        d28 = (np.nan_to_num(s.read(1)) > 0) & fp
    arms = {"R0_foldfair_d25_d28_visible_collar": d28 & (dvis > P.COLLAR_PX), "D28_asis": d28}
    for k in ("E1_hgb_thin", "E2_hgb_distal", "E3_hgb_distal_slope"):
        arms[k] = np.load(ROOT / f"data/work/h86e_{k}.npy")
    terms = {k: P.holdout_terms(v, folds, fp)[0] for k, v in arms.items()}
    out = dict(
        evidence_class="HOLDOUT-DTI",
        evaluator_version=E.VERSION,
        comparator_source=dict(sha256=d28_rec["sha256"], sources=d28_rec["sources"][:3]),
        dots={k: int(v.sum()) for k, v in arms.items()},
        paired={},
    )
    for cand in ("E1_hgb_thin", "E2_hgb_distal", "E3_hgb_distal_slope"):
        s = E.pooled_summary(
            {
                cand: terms[cand],
                "R0_foldfair": terms["R0_foldfair_d25_d28_visible_collar"],
                "D28_asis": terms["D28_asis"],
            },
            draws=1000,
            candidate=cand,
        )
        out["paired"][cand] = s
        print(
            cand,
            round(s["scores"][cand]["dti"], 4),
            s["scores"][cand]["ci95"],
            "R0ff",
            round(s["scores"]["R0_foldfair"]["dti"], 4),
            s["scores"]["R0_foldfair"]["ci95"],
            "delta",
            round(s["paired_differences"]["R0_foldfair"]["delta"], 4),
            s["paired_differences"]["R0_foldfair"]["ci95"],
        )
    (ROOT / "docs/evidence/h86e_comparator.json").write_text(
        json.dumps(out, indent=2, allow_nan=False) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
