#!/usr/bin/env python3
"""MASS axis on the R0 incumbent: drop / add 10% by the parent's own ranking.

Parent (R0)
-----------
``h33-h33-2-b2`` (GEMSDOE32), 37,654 unit-mass dots, sha256
``c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`` (CLAIM 0.2778,
no receipt).  R0 must rebuild byte-for-byte before any candidate is written.

The parent's own ranking (rebuilt from the recorded recipe, not stored)
-----------------------------------------------------------------------
R0's lineage is H19-5 (121,131 binary ridge cells) -> greedy 2.8 px thinning
(``d2.8``, 44,090 dots) -> collar prunes at 1 px (40,199) and 2 px (37,654).
The thinning traversal is the deterministic FIFO-BFS visitation order of
``gems27.thinning`` (GEMSDOE28 commit 94b027b, mirrored by
``scripts/build_r0_prune.original_visit_rank``).  This session *validates* that
ranking before using it: greedy acceptance in visit order, suppressing cells
within 2.8 px of an accepted dot, reproduces the pinned ``d2.8`` dot set
**exactly** (44,090 dots, 0 differing cells).  A row-major traversal does not
(14,225 differing cells), so the BFS order is the recipe's actual priority:
earlier-visited cells claimed territory first.

Variants (each differs from R0 only in mass, selected by that ranking)
----------------------------------------------------------------------
``massminus10``  drop the 3,765 R0 dots with the *highest* visit rank
                 (lowest priority: visited last, they won the least territory).
``massplus10``   add the 3,765 next-ranked H19-5 cells: eligible cells are in
                 the footprint, off the catalogue, > 2 px from it (R0's own
                 collar), not already dots, taken in ascending visit rank
                 (the highest-priority cells the thinning suppressed).

Known confounders, measured and reported rather than hidden
-----------------------------------------------------------
* The BFS order is seeded row-major by connected component, so visit rank is
  geographically structured: the dropped tail sits in late-visited (southern)
  components and the added cells in early-visited (northern) ones.  A live
  move therefore tests *traversal-ranked* mass, not mass in the abstract;
  quadrant shares are reported for both edit sets.
* Added cells were suppressed by the 2.8 px rule, so nearly all lie within
  2.8 px of an existing dot: the plus variant also tests kernel redundancy.
* The minus variant only deletes; the plus variant only adds.

Evidence classes: gates MEASUREMENT; catalogue hide-and-recover PROXY (report
only, never a gate or score); predicted live change MODEL.

Usage
-----
    .venv/bin/python scripts/build_mass_axis.py --build
    .venv/bin/python scripts/build_mass_axis.py --measure   # re-validate on disk
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
from scipy.spatial import cKDTree
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "scripts"))

import prune_collar as pc  # noqa: E402  (house writer / validator / proxy)
from build_r0_prune import original_visit_rank, profile_from_catalogue, serialize  # noqa: E402

PARENT_SHORT = "h33-h33-2-b2"
DATE_TAG = "20261023"
SEED = 20261023
FRAC = 0.10
OUT_DIR = ROOT / "releases" / "mass"

PIN_H19 = "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d"
PIN_D28 = "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"
H19_FILE = ROOT / "data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif"
D28_FILE = ROOT / "data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
BASE_FILE = ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"

PREDICTIONS = {
    "massminus10": ("-0.003 (MODEL, band -0.012..+0.006). Dropping the traversal-tail 10% saves the "
                    "false-positive mass of average ridge dots but deletes the only cover of the "
                    "small late-visited southern ridges; at DTI 0.28 a dot must earn credit > 0.056 "
                    "to pay, so the net is near the bar and slightly negative."),
    "massplus10": ("-0.006 (MODEL, band -0.016..+0.002). The next-ranked cells were suppressed by "
                   "the 2.8 px rule, so ~99% sit within one kernel radius of an existing dot: their "
                   "marginal truth credit is mostly already claimed (max operator), while each "
                   "still pays close to full false-positive mass."),
}
NOTES = {
    "massminus10": "R0 h33-h33-2-b2 MASS-10%: drop 3765 lowest-priority traversal-tail dots, 33889 left; predicted -0.003 MODEL",
    "massplus10": "R0 h33-h33-2-b2 MASS+10%: add 3765 next-ranked H19-5 cells, d>2px off catalogue, 41419 dots; predicted -0.006 MODEL",
}


def sha256_file(path: Path) -> str:
    return pc.sha256_file(path)


def check_pin(path: Path, pin: str, label: str) -> None:
    if not path.is_file():
        raise SystemExit(f"missing pinned input {label}: {path}")
    got = sha256_file(path)
    if got != pin:
        raise SystemExit(f"SHA-256 mismatch for {label}: {got} != {pin}")


def read_binary(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1)
    return footprint & np.isfinite(a) & (a > 0.5)


def greedy_thin(mask: np.ndarray, rank: np.ndarray, min_dist: float = 2.8) -> np.ndarray:
    """Accept cells in ascending ``rank`` unless within ``min_dist`` of an accepted dot."""
    ys, xs = np.nonzero(mask)
    order = np.argsort(rank[ys, xs], kind="stable")
    ys, xs = ys[order], xs[order]
    blocked = np.zeros(mask.shape, bool)
    out = np.zeros(mask.shape, bool)
    r = int(np.ceil(min_dist))
    offs = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
            if dy * dy + dx * dx < min_dist * min_dist]
    h, w = mask.shape
    for y, x in zip(ys.tolist(), xs.tolist()):
        if blocked[y, x]:
            continue
        out[y, x] = True
        for dy, dx in offs:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                blocked[ny, nx] = True
    return out


def build_mass_variants(parent: np.ndarray, h19: np.ndarray, rank: np.ndarray,
                        distance: np.ndarray, footprint: np.ndarray,
                        frac: float = FRAC) -> dict[str, dict]:
    """The two MASS edits.  Pure functions of the declared inputs (deterministic)."""
    n0 = int(parent.sum())
    n_change = int(round(frac * n0))
    # minus: highest visit rank = lowest priority in the recipe's traversal
    py, px = np.nonzero(parent)
    porder = np.argsort(rank[py, px], kind="stable")
    drop = np.zeros_like(parent)
    drop[py[porder[-n_change:]], px[porder[-n_change:]]] = True
    minus = parent & ~drop
    # plus: next-ranked eligible H19-5 cells in ascending visit rank
    eligible = h19 & footprint & (distance > 2.0) & ~parent
    ey, ex = np.nonzero(eligible)
    eorder = np.argsort(rank[ey, ex], kind="stable")
    if len(ey) < n_change:
        raise ValueError(f"only {len(ey)} eligible cells for {n_change} additions")
    add = np.zeros_like(parent)
    add[ey[eorder[:n_change]], ex[eorder[:n_change]]] = True
    plus = parent | add
    return {
        "massminus10": {"dots": minus, "removed": drop, "added": np.zeros_like(parent),
                        "n_change": n_change,
                        "rule": "drop the highest-visit-rank 10% of R0 dots"},
        "massplus10": {"dots": plus, "removed": np.zeros_like(parent), "added": add,
                       "n_change": n_change,
                       "rule": "add the lowest-visit-rank eligible H19-5 cells (footprint, "
                               "d_cat > 2 px, not already dots)"},
    }


def spatial_stats(mask: np.ndarray) -> dict:
    ys, xs = np.nonzero(mask)
    h, w = mask.shape
    if len(ys) == 0:
        return {"n": 0}
    return {"n": int(len(ys)), "mean_row": round(float(ys.mean()), 1),
            "mean_col": round(float(xs.mean()), 1),
            "share_south_half_pct": round(100.0 * float((ys >= h / 2).mean()), 2),
            "share_west_half_pct": round(100.0 * float((xs < w / 2).mean()), 2)}


def nn_stats(mask: np.ndarray) -> dict:
    pts = np.argwhere(mask)
    d = cKDTree(pts).query(pts, k=2)[0][:, 1]
    return {"mean_px": round(float(d.mean()), 3), "median_px": round(float(np.median(d)), 3),
            "fraction_below_2_8px": round(float((d < 2.8).mean()), 4)}


def feature_percentiles(g: pc.Grids, sets: dict[str, np.ndarray]) -> dict:
    """Label-free band response per dot set (percentile of |value - median| in footprint)."""
    path = ROOT / "data/bridge/training_features.tif"
    if not path.is_file():
        return {"evidence_class": "MEASUREMENT", "status": "SKIPPED_FEATURE_STACK_ABSENT"}
    check_pin(path, pc.PIN_FEATURES, "training_features.tif")
    out = {"evidence_class": "MEASUREMENT (label-free)",
           "statistic": "percentile of |value - footprint median|, averaged per dot set; 0.5 = background",
           "bands": {}}
    with rasterio.open(path) as src:
        names = [(src.descriptions[i] or src.tags(i + 1).get("band_name") or f"band{i+1}").split(" - ")[0]
                 for i in range(src.count)]
        for name in pc.FEATURE_BANDS:
            if name not in names:
                continue
            a = src.read(names.index(name) + 1).astype("float64")
            ok = g.footprint & np.isfinite(a) & (a > -1e30)
            v = a[ok]
            dev = np.abs(v - np.median(v))
            order = dev.argsort().argsort() / max(1, dev.size - 1)
            pct = np.full(a.shape, np.nan)
            pct[ok] = order
            out["bands"][name] = {k: round(float(np.nanmean(pct[m])), 4) for k, m in sets.items()}
    return out


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:  # pragma: no cover
        return "unknown"


def main() -> int:
    # Historical variant builders obey the same literal pre-placement stop.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="write releases/mass/ + evidence + ledger rows")
    ap.add_argument("--measure", action="store_true", help="rebuild in memory, re-validate on-disk files")
    ap.add_argument("--draws", type=int, default=6)
    args = ap.parse_args()
    if not (args.build or args.measure):
        ap.error("choose --build or --measure")

    g = pc.load_grids()  # verifies sample / catalogue / parent pins
    check_pin(H19_FILE, PIN_H19, "H19-5 field")
    check_pin(D28_FILE, PIN_D28, "d2.8 dot set")
    print(f"[1/6] inputs verified; parent {int(g.parent.sum()):,} dots")

    h19 = read_binary(H19_FILE, g.footprint) & ~g.catalogue
    d28 = read_binary(D28_FILE, g.footprint)
    base = read_binary(BASE_FILE, g.footprint)

    # --- parent gate: rebuild R0 dot set AND file bytes ---------------------
    rebuilt = base & (g.distance > 2.0)
    if not np.array_equal(rebuilt, g.parent):
        raise SystemExit("R0 dot set does not reproduce; STOP (parent approximation is forbidden)")
    cache = ROOT / ".cache" / "mass_axis"
    cache.mkdir(parents=True, exist_ok=True)
    rebuilt_path = cache / "r0-rebuilt-zeros.tif"
    serialize(rebuilt, g.footprint, rebuilt_path, "zeros", profile_from_catalogue())
    if sha256_file(rebuilt_path) != pc.PIN_PARENT:
        raise SystemExit("R0 sha256 does not reproduce; STOP (parent approximation is forbidden)")
    print("[2/6] R0 rebuilt byte-exactly (sha256 c55bafc4…)")

    # --- ranking gate: the recipe traversal must reproduce d2.8 exactly -----
    rank = original_visit_rank(h19)
    thin = greedy_thin(h19, rank, 2.8)
    if not np.array_equal(thin, d28):
        raise SystemExit(f"ranking does not reproduce d2.8: {int((thin ^ d28).sum())} differing cells; STOP")
    print("[3/6] ranking validated: greedy visit-order thinning == pinned d2.8 (44,090 dots, 0 diff)")

    variants = build_mass_variants(g.parent, h19, rank, g.distance, g.footprint)
    n0 = int(g.parent.sum())
    for key, v in variants.items():
        dots = v["dots"]
        assert not (dots & g.catalogue).any(), key
        assert int(dots.sum()) == n0 + int(v["added"].sum()) - int(v["removed"].sum())
    print(f"[4/6] variants built: " + ", ".join(
        f"{k}={int(v['dots'].sum()):,}" for k, v in variants.items()))

    # --- report-only instruments -------------------------------------------
    rng = np.random.default_rng(SEED)
    draws = pc.holdout_draws(g.catalogue, rng, args.draws)
    canary_rows = []
    for f in draws:
        active = g.footprint & ~f["known"]
        truth = active & f["truth"]
        dvis = ndi.distance_transform_edt(~f["known"])
        for name, surf in (("h19_5_binary", h19.astype(float)), ("negative_distance_to_visible", -dvis)):
            canary_rows.append({"draw": f["draw"], "feature": name,
                                "auc": float(roc_auc_score(truth[active], surf[active])),
                                "withheld_positives": int(truth.sum())})
    canary = {"status": "PASS" if max(r["auc"] for r in canary_rows) <= 0.90 else "STOP_INVESTIGATE",
              "threshold": 0.90, "max_auc": max(r["auc"] for r in canary_rows), "rows": canary_rows}
    if canary["status"] != "PASS":
        raise SystemExit(f"leakage canary > 0.90: {canary['max_auc']}; STOP and investigate")

    dot_sets = {"R0": g.parent, **{k: v["dots"] for k, v in variants.items()}}
    proxy = pc.proxy_scores(dot_sets, draws, g.footprint)
    feats = feature_percentiles(g, {"parent": g.parent,
                                    "dropped_massminus10": variants["massminus10"]["removed"],
                                    "retained_massminus10": variants["massminus10"]["dots"],
                                    "added_massplus10": variants["massplus10"]["added"]})
    d_to_parent = ndi.distance_transform_edt(~g.parent)
    add = variants["massplus10"]["added"]
    print(f"[5/6] proxy + canary done (canary max AUC {canary['max_auc']:.3f})")

    # --- write / validate ----------------------------------------------------
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, v in variants.items():
        dots = v["dots"]
        diff = pc.diff_stats(g.parent, dots)
        stem_base = f"{PARENT_SHORT}-{key}-{DATE_TAG}"
        scratch = OUT_DIR / f".{stem_base}-zeros.tmp.tif"
        scratch.unlink(missing_ok=True)
        pc.write_tiff(scratch, dots, g.footprint, "zeros")
        zeros_sha = sha256_file(scratch)
        sha8 = zeros_sha[:8]
        final_zeros = OUT_DIR / f"{stem_base}-{sha8}-zeros.tif"
        final_nan = OUT_DIR / f"{stem_base}-{sha8}.tif"
        if args.build:
            for p in (final_zeros, final_nan):
                p.unlink(missing_ok=True)
            scratch.replace(final_zeros)
            pc.write_tiff(final_nan, dots, g.footprint, "nan")
        else:
            scratch.unlink(missing_ok=True)
            if not (final_zeros.is_file() and final_nan.is_file()):
                raise SystemExit(f"--measure: missing release twins for {key} ({stem_base}-{sha8})")
        v_nan = pc.validate(final_nan, g, "nan")
        v_zeros = pc.validate(final_zeros, g, "zeros")
        if not (v_nan["all_checks_passed"] and v_zeros["all_checks_passed"]):
            raise SystemExit(f"format gates failed for {key}")
        dup = pc.uniqueness_vs_disk(final_nan)
        if dup["duplicate"]:
            raise SystemExit(f"exact-hash duplicate for {key}: {dup['exact_hash_duplicates']}")
        rel = proxy["candidates"][key]
        extra = {
            "removed_spatial": spatial_stats(v["removed"]) if v["removed"].any() else None,
            "added_spatial": spatial_stats(v["added"]) if v["added"].any() else None,
            "nn_parent": nn_stats(g.parent), "nn_candidate": nn_stats(dots),
        }
        if key == "massplus10":
            extra["added_within_2_8px_of_parent_pct"] = round(
                100.0 * float((d_to_parent[add] < 2.8).mean()), 2)
            extra["added_min_catalogue_distance_px"] = float(g.distance[add].min())
        if key == "massminus10":
            extra["dropped_rank_range"] = [int(rank[v["removed"]].min()), int(rank[v["removed"]].max())]
        row = {
            "id": final_nan.stem, "parent": PARENT_SHORT, "axis": "MASS",
            "value": "minus10pct" if key == "massminus10" else "plus10pct",
            "rule": v["rule"], "n_dots": diff["n_candidate"], "pct_changed": diff["pct_of_parent_changed"],
            "sha256": v_nan["sha256"], "sha256_zeros": zeros_sha, "sha8": sha8,
            "encoding": "nan", "status": "BUILT",
            "files": [str(final_nan.relative_to(ROOT)), str(final_zeros.relative_to(ROOT))],
            "diff": diff, "validation_nan": v_nan, "validation_zeros": v_zeros,
            "gate_all_pass": True, "exact_hash_duplicate": dup,
            "proxy": {"proxy_dti_mean": rel["proxy_dti_mean"], "delta_vs_R0_mean": rel["delta_vs_R0_mean"],
                      "delta_vs_R0_ci95": rel["delta_vs_R0_ci95"], "folds_improved": rel["folds_improved"],
                      "draws": proxy["draws"], "evidence_class": "PROXY"},
            "predicted_change": PREDICTIONS[key], "receipt_score": "", "receipt_date": "",
            "extra": extra,
        }
        receipt = {
            "id": row["id"], "parent": "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros",
            "axis": "MASS", "value": row["value"], "role": "candidate",
            "n_dots": row["n_dots"], "pct_changed": row["pct_changed"],
            "dot_digest": pc.dot_digest(dots) if hasattr(pc, "dot_digest") else None,
            "zeros": {"file": final_zeros.name, "sha256": zeros_sha, "bytes": final_zeros.stat().st_size,
                      "validator": {k: v_zeros[k] for k in ("checks", "all_checks_passed",
                                                             "on_catalogue_dots", "min_catalogue_distance_px")}},
            "nan": {"file": final_nan.name, "sha256": v_nan["sha256"], "bytes": final_nan.stat().st_size,
                    "validator": {k: v_nan[k] for k in ("checks", "all_checks_passed",
                                                         "on_catalogue_dots", "min_catalogue_distance_px")}},
            "submission_name": final_nan.stem, "note": NOTES[key], "note_chars": len(NOTES[key]),
            "predicted_live_change": PREDICTIONS[key], "evidence_class": "MODEL",
            "approved_for_weekly_slot": False, "submission_slots_used": 0, "diff": diff,
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if args.build:
            final_zeros.with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        rows.append(row)
        print(f"      {row['id']}: {row['n_dots']:,} dots ({row['pct_changed']:+.2f}% changed), gates PASS")

    if args.build:
        evidence = {
            "schema": "gems86.mass-axis.v1",
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "axis": "MASS", "seed": SEED, "git_sha": _git_sha(),
            "parent": {"id": PARENT_SHORT, "sha256": pc.PIN_PARENT, "n_dots": n0,
                       "live_0_2778": "CLAIM (no receipt)"},
            "ranking": {
                "definition": "FIFO-BFS visitation rank of H19-5 cells (gems27.thinning, GEMSDOE28 94b027b), "
                              "mirrored by scripts/build_r0_prune.original_visit_rank",
                "validation": "greedy 2.8 px acceptance in ascending rank reproduces the pinned d2.8 dot "
                              "set exactly (44,090 dots, 0 differing cells); row-major order does not",
                "interpretation": "traversal priority (earlier cells claimed 2.8 px territory first); "
                                  "spatial/content-blind, not a geological probability",
            },
            "r0_rebuild": {"dot_set_matches": True, "sha256_matches": True, "bytes": 219065},
            "leakage_canary": canary,
            "proxy": proxy,
            "proxy_verdict": ("REPORT ONLY. A catalogue-avoiding field sits at this instrument's floor, "
                              "so these numbers are a negative control, never a gate or a prediction."),
            "feature_percentiles": feats,
            "ring_table_parent": pc.ring_table(g, g.parent),
            "variants": rows,
        }
        (ROOT / "evidence" / "mass_axis_20261023.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        (ROOT / "ledger" / "variants_mass.json").write_text(
            json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        print("[6/6] wrote evidence/mass_axis_20261023.json and ledger/variants_mass.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
