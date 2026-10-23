#!/usr/bin/env python3
"""GEMSDOE86 session, AXIS = MASS (kernel-budget ranking). Rebuild R0, then re-run MASS properly.

Why a second MASS session
-------------------------
The first MASS session built the brief's literal arms (drop / add the traversal-ranked 10 %) and
both lost (``massminus10`` −0.003, ``massplus10`` −0.006 MODEL) because that ranking is the
FIFO-BFS *traversal* of the thinning recipe, not a quality order (IR-86-MASS-01).  Brief v2 §2
says to rank by exact marginal gain from the metric code.  This script does exactly that with a
label-free, band-free quantity (``gems86.mass_econ.marginal_credit``): the part of a dot's kernel
credit no neighbour can take away.

What runs here
--------------
1. **Pins first.** Every input is SHA-256 checked before it is read (brief 4.2).
2. **Parent rebuild.** R0's dot mask, re-encoded with the documented TIFF settings, must reproduce
   ``c55bafc4…`` byte for byte; the script stops otherwise.  (The 40,199-dot base raster is not in
   this checkout, so this session reproduces the *encoding and the dot set* from the pinned parent
   file, exactly as the SPACING session did; it does not re-derive the set from the base.)
3. **Three arms + one control, one axis.** Drop the 10 % of dots with the smallest unique credit
   (``minus10pct-marginal``, 3,765 dots, count 33,889 = the same count the traversal arm dropped
   to, so the pair reads out the *ranking*), add 3,765 dots at least one kernel radius from all
   existing mass along the local trace (``plus10pct-extend``, count 41,419, again the count the
   traversal arm added to), and the same additions placed uniformly at random inside the same
   window (``plus10pct-extend-rand`` = null control).
4. **Gates** (brief §6) against the written file, re-read from disk, both encodings.
5. **Report-only instruments** (never gates): SGMC off-catalogue exact-DTI MODEL with a quadrant
   split and a ±6 px truth-translation ensemble, the metric's own marginal bars, the leakage
   canary, and the parent-support saturation measurement that closes the add direction.

Nothing here logs in, scrapes a leaderboard, submits, or contacts DrivenData or dropbox.  No shared
validator, gate or writer is modified.

Usage::  .venv/bin/python scripts/build_mass_econ.py [--no-surrogate]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "vendor", ROOT / "vendor" / "template66"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gems86 import mass_econ as ME  # noqa: E402
from gems86_axis import gates, grid_io  # noqa: E402
from gems86_axis.grid_io import dot8  # noqa: E402

SESSION = "mass-econ"
DATE_TAG = "20261023"
SEED = 20261023
PARENT_LABEL = "h33-h33-2-b2"
AXIS = "MASS"
DOSE = 0.10

PATHS = {
    "sample": ROOT / "data/bridge/sample_submission.tif",
    "catalogue": ROOT / "data/bridge/existing_faults.tif",
    "parent": ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "sgmc": ROOT / "data/external/derived_sgmc_faults_100m_u8.tif",
    "h19": ROOT / "data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
}
PINS = {
    "sample": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "catalogue": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "parent": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "sgmc": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
    "h19": "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
}
PARENT_SHA_PIN = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
OUT_DIR = ROOT / "releases" / "mass86"
RUN_CARD = ROOT / "evidence" / "mass_econ_axis_20261023.json"
MECH_CARD = ROOT / "evidence" / "mass-econ-mechanism.md"

#: Predictions were preregistered from the algebra before any surrogate was read.  The
#: monotonicity audit (scripts/audit_mass_instrument.py) then showed the surrogate is a mass curve,
#: so the *revised* predictions below are what the ledger carries; both are kept.
PREREGISTERED = {
    "minus10pct-marginal": ("+0.002 (MODEL, band -0.004..+0.008). The metric's own two-sided test "
                            "says a removal pays only if the removed dot's unique truth credit is "
                            "under ~0.06 kernel units; R0's smallest measured credit is 1.49, so "
                            "every deletion loses real numerator. Removing the 10 % with the least "
                            "unique credit is the least-bad deletion, not a good one: expect a "
                            "reading near zero, and one *better* than the traversal arm's -0.003 "
                            "at identical count or the ranking is worthless."),
    "plus10pct-extend": ("+0.003 (MODEL, band -0.005..+0.011). New mass at >= 1 kernel radius "
                         "from every existing dot earns its own kernel credit instead of sharing "
                         "a neighbour's, which is the structural failure of the traversal add "
                         "(-0.006): 98.6 % of its additions sat inside an existing disc. Positive "
                         "only if the trace continuation is right; this is the mirror of the drop "
                         "arm and the only arm here that can add numerator."),
    "plus10pct-extend-rand": ("0.000 (MODEL, null control, never a slot candidate). Same window "
                              "and spacing floor, uniform placement: it prices the coverage "
                              "bought by moving off the trace, so the extend arm is read against "
                              "it and not against zero."),
}


REVISED = {
    "minus10pct-marginal": ("0.000 MODEL (band -0.008..+0.006). Revised after the monotonicity "
                            "audit: the surrogate's -0.0036 is its own mass curve at -10% "
                            "(-0.0068 for a random 10% delete), so it does not say whether the "
                            "unique-credit ranking beats the traversal ranking; the metric's "
                            "removal bar (unique credit < 0.06 kernel units; parent minimum "
                            "1.49) says every deletion loses real numerator."),
    "plus10pct-extend": ("0.000 MODEL (band -0.010..+0.010). Revised after the monotonicity "
                         "audit: +0.0057 is what the surrogate pays for +10% mass anywhere "
                         "(+0.0040 for a random add elsewhere), and the arm beats its own "
                         "random-placement control by only -0.0006, so the trace continuation is "
                         "not what the instrument is measuring."),
    "plus10pct-extend-rand": ("0.000 MODEL. Null control: it exists to price the 3-6 px shell, "
                              "never a slot candidate."),
}

PREDICTED = PREREGISTERED


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    except Exception:                                                     # pragma: no cover
        return "unknown"


def verify_inputs() -> dict:
    receipt = {}
    for name, path in PATHS.items():
        if not path.is_file():
            raise FileNotFoundError(f"pinned input {name} is missing: {path}")
        digest = sha256(path)
        if digest != PINS[name]:
            raise ValueError(f"pinned input {name} hash mismatch: {digest} != {PINS[name]}")
        receipt[name] = {"path": str(path.relative_to(ROOT)), "sha256": digest,
                         "bytes": path.stat().st_size, "verified": True,
                         "organizer_authenticated": False}
    return receipt


def read(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(1)


def encode_zeros(mask: np.ndarray, ctx: dict, path: Path) -> dict:
    """The documented encoding that reproduces R0 byte-for-byte (predictor 3, zlevel 9, tiled 256)."""
    out = np.zeros(mask.shape, np.float32)
    out[ctx["footprint"]] = np.asarray(mask, bool)[ctx["footprint"]].astype(np.float32)
    with rasterio.open(ctx["sample_path"]) as ref:
        crs, transform = ref.crs, ref.transform
    with rasterio.open(path, "w", driver="GTiff", height=out.shape[0], width=out.shape[1], count=1,
                       dtype="float32", crs=crs, transform=transform, nodata=None,
                       compress="deflate", predictor=3, zlevel=9, tiled=True,
                       blockxsize=256, blockysize=256, interleave="band") as dst:
        dst.write(out, 1)
    return {"file": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "sha256": sha256(path)}


def rebuild_parent(ctx: dict) -> dict:
    """Re-encode the pinned parent dot mask; the result must be the pinned hash, byte for byte."""
    dots = grid_io.load_dots(PATHS["parent"], ctx["footprint"])
    probe = ROOT / ".cache" / "mass86_parent_reencode.tif"
    probe.parent.mkdir(parents=True, exist_ok=True)
    rec = encode_zeros(dots, ctx, probe)
    ok = rec["sha256"] == PARENT_SHA_PIN
    probe.unlink(missing_ok=True)
    if not ok:
        raise SystemExit(f"parent rebuild mismatch: {rec['sha256']} != {PARENT_SHA_PIN}")
    return {"status": "REPRODUCED-BYTE-EXACT", "n_dots": int(dots.sum()), "sha256": rec["sha256"],
            "bytes": rec["bytes"], "encoding": "deflate/predictor=3/zlevel=9/tiled 256/interleave=band",
            "scope": ("dot set read from the pinned parent file and re-encoded; the 40,199-dot base "
                      "raster is absent from this checkout so the set is not re-derived")}


def support_saturation(ctx: dict, parent: np.ndarray) -> dict:
    """How much of the parent field's own support is free at one kernel radius. Closes MASS-add."""
    h19 = np.nan_to_num(read(PATHS["h19"]))
    support = h19 > 0
    foot, cat = ctx["footprint"], ctx["catalogue"]
    cat_edt = ndi.distance_transform_edt(~cat)
    dot_edt = ndi.distance_transform_edt(~parent)
    elig = foot & ~cat & (cat_edt > grid_io.PARENT_CAT_CLEARANCE_PX) & (dot_edt >= ME.R_PX - 1e-9)
    free_in_support = elig & support
    return {
        "field_support_cells": int(support.sum()),
        "eligible_cells_anywhere": int(elig.sum()),
        "eligible_cells_inside_support": int(free_in_support.sum()),
        "eligible_cells_inside_support_3to6px": int((free_in_support & (dot_edt <= 6.0)).sum()),
        "support_saturation_fraction": round(1.0 - free_in_support.sum() / max(int(support.sum()), 1), 6),
        "conclusion": ("The parent's own field cannot rank 10 % of new mass: only "
                       f"{int(free_in_support.sum())} of {int(support.sum())} support cells are at "
                       "least one kernel radius from every dot, so any add ranked by that field is "
                       "either redundant (massplus10: -0.006) or outside the field entirely. This "
                       "is why the add arms here use the parent's *geometry* (trace continuation), "
                       "not the parent's *field*."),
    }


def _sha_conflict(known: dict, art: dict, stem: str) -> dict:
    """Ledger collisions that are *not* this run's own unreceipted rows."""
    out = {}
    for enc in ("nan", "zeros"):
        hits = known.get(art[enc]["sha256"], [])
        foreign = [h for h in hits if not (h.split("|")[0] == stem and not h.split("|")[1])]
        out[enc] = {"hits": hits, "conflict": foreign, "self_reproduction": bool(hits and not foreign)}
    return out


def arm_stats(parent: np.ndarray, mask: np.ndarray, ctx: dict, stats: dict) -> dict:
    foot, cat = ctx["footprint"], ctx["catalogue"]
    cat_edt = ndi.distance_transform_edt(~cat)
    added = mask & ~parent
    dropped = parent & ~mask
    shared = int((mask & parent).sum())
    union = int((mask | parent).sum())
    new_cat = cat_edt[added] if added.any() else np.array([np.inf])
    stats.update({
        "parent_dots": int(parent.sum()), "variant_dots": int(mask.sum()),
        "shared_dots": shared, "added": int(added.sum()), "dropped": int(dropped.sum()),
        "count_delta": int(mask.sum()) - int(parent.sum()),
        "pct_changed_of_parent": round(100.0 * (int(added.sum()) + int(dropped.sum())) / max(int(parent.sum()), 1), 4),
        "jaccard": round(shared / max(union, 1), 6),
        "dots_on_catalogue": int((mask & cat).sum()),
        "min_cat_edt_px_added": round(float(new_cat.min()), 4) if added.any() else None,
        "min_cat_edt_px_all": round(float(cat_edt[mask].min()), 4),
        "new_mass_clearance_ok": bool(not added.any() or float(new_cat.min()) >= ME.R_PX - 1e-9),
        "in_footprint_only": bool(not (mask & ~foot).any()),
    })
    return stats


def surrogate(parent: np.ndarray, arms: dict[str, np.ndarray], ctx: dict) -> dict:
    """Report-only MODEL: exact DTI against the off-catalogue SGMC inventory, + splits."""
    foot, cat = ctx["footprint"], ctx["catalogue"]
    sg = read(PATHS["sgmc"]) > 0
    off = sg & foot & ~cat
    base = ME.exact_terms(parent, off)
    h, w = parent.shape
    half_r, half_c = h // 2, w // 2
    quad = np.zeros((h, w), np.int8)
    quad[:half_r, :half_c] = 0
    quad[:half_r, half_c:] = 1
    quad[half_r:, :half_c] = 2
    quad[half_r:, half_c:] = 3
    out = {"source": "USGS SGMC conterminous synthetic geologic map, off-catalogue pixels",
           "source_url": "https://www.usgs.gov/science-plan/conterminous-synthetic-geologic-map-compiler-sgmc",
           "evidence_class": "MODEL", "truth_cells": int(off.sum()), "parent": base, "arms": {}}
    for name, mask in arms.items():
        child = ME.exact_terms(mask, off)
        quads = []
        for q in range(4):
            t = off & (quad == q)
            quads.append(round(ME.exact_terms(mask, t)["dti"] - ME.exact_terms(parent, t)["dti"], 6))
        trans = []
        for dy in (-6, 0, 6):
            for dx in (-6, 0, 6):
                t = np.roll(np.roll(off, dy, axis=0), dx, axis=1)
                trans.append(round(ME.exact_terms(mask, t)["dti"] - ME.exact_terms(parent, t)["dti"], 6))
        out["arms"][name] = {
            "child": child, "delta_dti": round(child["dti"] - base["dti"], 6),
            "quadrant_deltas": quads, "quadrants_positive": int(sum(1 for q in quads if q > 0)),
            "translation_deltas": trans,
            "translation_range": [min(trans), max(trans)],
            "translation_median": round(float(np.median(trans)), 6),
        }
    ctl = "plus10pct-extend-rand"
    if ctl in out["arms"]:
        out["law_vs_chance"] = round(out["arms"]["plus10pct-extend"]["delta_dti"]
                                     - out["arms"][ctl]["delta_dti"], 6)
        out["law_vs_chance_read"] = ("extend minus the random-placement control on the same "
                                     "admissible window; this is the number that decides whether "
                                     "the trace continuation carries information")
    return out


def canary(parent: np.ndarray, arms: dict[str, np.ndarray], ctx: dict) -> dict:
    """Single-feature leakage canary: no construction variable may recover the surrogate truth."""
    from sklearn.metrics import roc_auc_score

    foot, cat = ctx["footprint"], ctx["catalogue"]
    sg = (read(PATHS["sgmc"]) > 0) & foot & ~cat
    u, _ = ME.marginal_credit(parent)
    rows, cols = parent.nonzero()
    y = sg[rows, cols].astype(int)
    auc_u = float(roc_auc_score(y, u)) if y.min() != y.max() else None
    dist = ndi.distance_transform_edt(~parent)
    elig = foot & ~cat
    y2 = sg[elig].astype(int)
    auc_d = float(roc_auc_score(y2, -dist[elig])) if y2.min() != y2.max() else None
    verdict = "PASS" if all((a is None or a <= 0.90) for a in (auc_u, auc_d)) else "STOP"
    return {"auc_unique_credit_vs_sgmc_at_parent_dots": None if auc_u is None else round(auc_u, 4),
            "auc_nearest_dot_distance_vs_sgmc_offcatalogue": None if auc_d is None else round(auc_d, 4),
            "threshold": 0.90, "verdict": verdict,
            "note": ("both construction variables are computed from the parent dot mask alone; no "
                     "labelled band, no competition label and no SGMC pixel enters a selection")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-surrogate", action="store_true")
    a = ap.parse_args()

    ctx = grid_io.load_context()
    foot = ctx["footprint"]
    pins = verify_inputs()
    rebuild = rebuild_parent(ctx)
    parent = grid_io.load_dots(PATHS["parent"], foot)
    n_parent = int(parent.sum())
    n_dose = int(round(DOSE * n_parent))

    arms: dict[str, dict] = {}
    masks: dict[str, np.ndarray] = {}

    drop_sel, drop_st = ME.select_lowest_marginal(parent, n_dose)
    masks["minus10pct-marginal"] = parent & ~drop_sel
    arms["minus10pct-marginal"] = {"stats": drop_st}

    add_ext, ext_st = ME.add_extension(ctx, parent, n_dose)
    masks["plus10pct-extend"] = parent | add_ext
    arms["plus10pct-extend"] = {"stats": ext_st}

    add_rand, rnd_st = ME.add_random(ctx, parent, n_dose, seed=SEED)
    masks["plus10pct-extend-rand"] = parent | add_rand
    arms["plus10pct-extend-rand"] = {"stats": rnd_st}

    import csv

    # The §6 gate is "no hash already in the ledger".  A re-run of the same pinned recipe
    # reproduces the same bytes, and this script is the only thing that writes its own rows, so a
    # match is exempt only when *every* matching row is one of this run's own ids and carries no
    # receipt.  Anything else (a prior session's artifact, or a scored receipt) fails the gate.
    known: dict[str, list[str]] = {}
    with (ROOT / "ledger" / "submissions.csv").open(newline="") as fh:
        for row in csv.DictReader(fh):
            for key in ("sha256", "sha256_zeros"):
                if row.get(key):
                    known.setdefault(row[key], []).append(
                        f"{row.get('id') or row.get('name')}|{row.get('receipt_score') or ''}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    card = {"session": SESSION, "date": DATE_TAG, "git_sha": git_sha(), "axis": AXIS,
            "dose": DOSE, "parent": {"label": PARENT_LABEL, "sha256": PARENT_SHA_PIN,
                                     "n_dots": n_parent, "rebuild": rebuild},
            "pins": pins, "n_dose": n_dose, "variants": []}

    for name, mask in masks.items():
        stats = arms[name]["stats"]
        stats = arm_stats(parent, mask, ctx, stats)
        token = dot8(mask)
        stem = f"{PARENT_LABEL}-{AXIS}-{name}-{DATE_TAG}-{token}"
        note = (f"{PARENT_LABEL}; MASS {name}; 10.0% of dots changed; predicted "
                f"{REVISED[name].split(' ')[0]} MODEL (below the 0.01 evidence floor)")
        note = note[:140]
        art = grid_io.write_pair(mask, ctx, OUT_DIR, stem, stem, note)
        g = {enc: {"format": gates.format_gate(art[enc]["path"], ctx),
                   "value": gates.value_gate(art[enc]["path"], ctx)} for enc in ("nan", "zeros")}
        passed = all(g[enc]["format"]["passed"] and g[enc]["value"]["passed"] for enc in g)
        nc = {"gate": "new_mass_only", "passed": bool(stats["new_mass_clearance_ok"]
                                                      and stats["dots_on_catalogue"] == 0
                                                      and stats["in_footprint_only"]),
              "added_dots": stats["added"], "min_cat_edt_px_added": stats["min_cat_edt_px_added"],
              "clearance_px": ME.R_PX,
              "rule": "newly emitted mass must sit >= 3 px from the catalogue (brief 4.4) and "
                      "inside the footprint; the parent's own 2-3 px dots are inherited, not new"}
        nc["catalogue_clearance_file"] = gates.catalogue_clearance_gate(art["zeros"]["path"], ctx, 2.0)
        reads = {enc: {k: v for k, v in g[enc]["value"].items() if k != "checks"} for enc in g}
        card["variants"].append({
            "id": stem, "axis": AXIS, "value": name, "token": token,
            "n_dots": int(mask.sum()),
            "parent_diff": {k: stats[k] for k in ("parent_dots", "variant_dots", "shared_dots",
                                                 "added", "dropped", "count_delta",
                                                 "pct_changed_of_parent", "jaccard")},
            "stats": stats,
            "artifacts": {enc: {"file": art[enc]["path"], "sha256": art[enc]["sha256"],
                                "bytes": Path(art[enc]["path"]).stat().st_size}
                          for enc in ("nan", "zeros")},
            "gates": {enc: {"passed": g[enc]["format"]["passed"] and g[enc]["value"]["passed"],
                            "format_passed": g[enc]["format"]["passed"],
                            "value_passed": g[enc]["value"]["passed"],
                            "failed": g[enc]["format"]["failed"],
                            "read_back": reads[enc]} for enc in g},
            "new_mass_gate": nc,
            "sha_already_in_ledger": _sha_conflict(known, art, stem),
            "predicted_change_preregistered": PREREGISTERED[name],
            "predicted_change": REVISED[name],
            "note": note, "note_chars": len(note),
        })

    card["mass_bar"] = ME.mass_bar(0.2778)
    card["support_saturation"] = support_saturation(ctx, parent)
    card["canary"] = canary(parent, masks, ctx)
    if not a.no_surrogate:
        card["sgmc_surrogate"] = surrogate(parent, masks, ctx)

    ok = all(v["gates"]["nan"]["passed"] and v["gates"]["zeros"]["passed"]
             and not any(v["sha_already_in_ledger"][e]["conflict"]
                         for e in ("nan", "zeros")) for v in card["variants"])
    card["all_gates_passed"] = bool(ok)
    card["gate_failures"] = [v["id"] for v in card["variants"]
                             if not (v["gates"]["nan"]["passed"] and v["gates"]["zeros"]["passed"])]
    RUN_CARD.write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps({"run_card": str(RUN_CARD.relative_to(ROOT)),
                      "all_gates_passed": card["all_gates_passed"],
                      "variants": [{"id": v["id"], "n_dots": v["n_dots"],
                                    "pct_changed": v["parent_diff"]["pct_changed_of_parent"],
                                    "surrogate_delta": card.get("sgmc_surrogate", {}).get("arms", {})
                                    .get(v["value"], {}).get("delta_dti")}
                                   for v in card["variants"]]}, indent=2))
    if not ok:
        print("GATE FAILURE — artifacts stay unbuilt-for-slot; see "
              f"{RUN_CARD.relative_to(ROOT)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
