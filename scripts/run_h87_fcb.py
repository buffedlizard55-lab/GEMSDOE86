#!/usr/bin/env python3
"""H87-FCB: fair catalogue-distance band dot fields on the shared hide-and-recover holdout.

Preregistration: research/H87_FAIR_CATALOGUE_BAND_PREREGISTRATION.json (read it first).

* Evaluator: vendor/gems57 ``holdout.build_holdout`` / ``holdout.score_cell`` (unmodified).
  Scores are HOLDOUT-DTI (gems57-pooled-hide-v2), never leaderboard scores.
* Every candidate arm is built from VISIBLE traces only, cell by cell, so it cannot see
  withheld truth. The legacy GEMSDOE32 H33 raster was built from the full catalogue; it is
  scored only to quantify leakage and is labelled LEAKAGE-SUSPECT.
* Usage:  python scripts/run_h87_fcb.py --arms N0,B1,O,L,canary --out docs/evidence/...json
          python scripts/run_h87_fcb.py --arms B2,B3 --out docs/evidence/...json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import grid as G, holdout as H, evaluate_holdout as EH  # noqa: E402

SPACING_PX = 2.8284271247461903   # parent-floor minimum pair distance (H33 analysis)
BUDGET_RATIO = 37654 / 60988      # full-grid dot / catalogue-pixel ratio of the 37,654-dot files
BOOT_DRAWS = 1000
BOOT_SEED = 520810
LEGACY_H33 = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
BANDS = {"B1": (1.0, 2.0), "B2": (2.0, 3.0), "B3": (3.0, 5.0)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def thin_nearest_first(cand: np.ndarray, dist: np.ndarray, budget: int) -> np.ndarray:
    """Greedy minimum-spacing thinning, nearest-to-trace first, deterministic tie-break.

    Accepts a candidate only if no accepted dot lies within SPACING_PX. Stops at budget.
    """
    idx = np.flatnonzero(cand.ravel())
    order = idx[np.lexsort((idx, dist.ravel()[idx]))]
    h, w = cand.shape
    r = int(np.ceil(SPACING_PX))
    offs = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
            if 0 < dy * dy + dx * dx < SPACING_PX * SPACING_PX]
    occ = np.zeros((h, w), bool)
    out = np.zeros((h, w), bool)
    n = 0
    for flat in order:
        if n >= budget:
            break
        y, x = divmod(int(flat), w)
        ok = True
        for dy, dx in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and occ[yy, xx]:
                ok = False
                break
        if ok:
            occ[y, x] = True
            out[y, x] = True
            n += 1
    return out


def band_field(fp: np.ndarray, d_vis: np.ndarray, lo: float, hi: float, budget: int) -> np.ndarray:
    cand = fp & (d_vis > lo) & (d_vis <= hi)
    return thin_nearest_first(cand, d_vis, budget)


def uniform_field(fp: np.ndarray, budget: int, seed: int = 20) -> np.ndarray:
    rng = np.random.default_rng(seed)
    idx = np.flatnonzero(fp.ravel())
    pick = rng.choice(idx, size=min(budget, idx.size), replace=False)
    out = np.zeros(fp.size, bool)
    out[pick] = True
    return out.reshape(fp.shape)


def pooled(cell_rows: list[dict], sel: np.ndarray | None = None) -> dict:
    rows = cell_rows if sel is None else [cell_rows[i] for i in sel]
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    fn = sum(r["fn"] for r in rows)
    n_truth = sum(r["n_truth"] for r in rows)
    dti = float(tp / (tp + H.ALPHA * fp + H.BETA * fn + H.EPS)) if (tp + fp + fn) > 0 else 0.0
    return {"dti": dti, "tp": tp, "fp": fp, "fn": fn, "withheld_positives": int(n_truth)}


def boot_ci(cell_rows: list[dict], paired_rows: list[dict] | None = None) -> dict:
    rng = np.random.default_rng(BOOT_SEED)
    n = len(cell_rows)
    draws, diffs = [], []
    for _ in range(BOOT_DRAWS):
        sel = rng.integers(0, n, size=n)
        a = pooled(cell_rows, sel)["dti"]
        draws.append(a)
        if paired_rows is not None:
            diffs.append(a - pooled(paired_rows, sel)["dti"])
    out = {"ci95": [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]}
    if paired_rows is not None:
        out["paired_delta_ci95"] = [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]
        out["paired_delta_point"] = pooled(cell_rows)["dti"] - pooled(paired_rows)["dti"]
    return out


def score_emissions(ctx, make_emission) -> list[dict]:
    rows = []
    for cell in ctx.cells:
        emit = make_emission(cell)
        r = H.score_cell(cell, emit)
        r["key"] = cell.key
        rows.append(r)
    return rows


def auc_from_cells(ctx, d_vis_by_key: dict[str, np.ndarray], neg_per_cell: int = 300_000) -> float:
    """Canary: AUC of -distance-to-visible-trace for truth vs non-truth on scored pixels.

    Negatives are subsampled per cell (fixed seed) to keep the rank statistic tractable;
    every truth pixel is used.
    """
    scores, labels = [], []
    rng = np.random.default_rng(BOOT_SEED)
    for cell in ctx.cells:
        d = d_vis_by_key[cell.key]
        active_full = np.zeros(ctx.grid.footprint.shape, bool)
        active_full[cell.bbox] = cell.active
        t_mask = np.zeros(active_full.shape, bool)
        ty, tx = cell.truth_yx
        t_mask[cell.bbox][ty, tx] = True          # basic slicing -> view, writes through
        pos = np.flatnonzero(t_mask.ravel())
        neg_all = np.flatnonzero((active_full & ~t_mask).ravel())
        neg = rng.choice(neg_all, size=min(neg_per_cell, neg_all.size), replace=False)
        flat_d = d.ravel()
        scores.append(-flat_d[pos])
        labels.append(np.ones(pos.size))
        scores.append(-flat_d[neg])
        labels.append(np.zeros(neg.size))
    s = np.concatenate(scores)
    y = np.concatenate(labels)
    r = rankdata(s)
    n1 = y.sum()
    n0 = y.size - n1
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", required=True, help="comma list from N0,B1,B2,B3,O,L,canary")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]

    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    g = G.load_grid(ROOT / "data/bridge")
    ctx = H.build_holdout(g)
    fp = g.footprint
    cells = ctx.cells
    budgets = {c.key: int(round(BUDGET_RATIO * int((ctx.visible(c.key) & fp).sum()))) for c in cells}

    # Visible-trace distance per cell (full grid), computed once and reused by all arms.
    d_vis = {c.key: ndi.distance_transform_edt(~ctx.visible(c.key)) for c in cells}
    results: dict = {}
    per_cell: dict[str, list[dict]] = {}

    if "O" in arms:
        rows = score_emissions(ctx, lambda c: _truth_full(ctx, c))
        per_cell["O"] = rows
    if "N0" in arms:
        per_cell["N0"] = score_emissions(ctx, lambda c: uniform_field(fp, budgets[c.key]))
    for name in ("B1", "B2", "B3"):
        if name in arms:
            lo, hi = BANDS[name]
            per_cell[name] = score_emissions(
                ctx, lambda c, lo=lo, hi=hi: band_field(fp, d_vis[c.key], lo, hi, budgets[c.key]))
    if "L" in arms:
        with rasterio.open(LEGACY_H33) as src:
            vals = src.read(1)
        legacy = np.isfinite(vals) & (vals > 0) & fp
        per_cell["L"] = score_emissions(ctx, lambda c: legacy)
    if "canary" in arms:
        results["canary_auc_distance_to_visible_trace"] = auc_from_cells(ctx, d_vis)
        results["canary_rule"] = "AUC above 0.90 = leakage until proven otherwise"
        results["canary_status"] = ("LEAKAGE-SUSPECT" if results["canary_auc_distance_to_visible_trace"] > 0.90
                                    else "PASS (below 0.90)")

    summary = {}
    for name, rows in per_cell.items():
        summary[name] = {"pooled": pooled(rows), "ci": boot_ci(rows), "per_cell": {r["key"]: r["dti"] for r in rows}}
        if name in ("B1", "B2", "B3") and "N0" in per_cell:
            summary[name]["vs_N0"] = boot_ci(rows, per_cell["N0"])
    results["arms"] = summary
    results["evaluator"] = {"version": EH.VERSION, "n_cells": len(cells),
                            "withheld_positives_total": int(sum(c.n_truth for c in cells)),
                            "implementation_hashes": EH.implementation_hashes()}
    results["budgets_per_cell"] = budgets
    results["emission_counts"] = {name: None for name in per_cell}
    results["legacy_raster"] = {"path": str(LEGACY_H33.relative_to(ROOT)), "sha256": sha256(LEGACY_H33),
                                "status": "LEAKAGE-SUSPECT (built from full catalogue)"}
    results["label"] = "HOLDOUT-DTI (gems57-pooled-hide-v2)"
    results["started_utc"] = started
    results["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results["arms_run"] = arms
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in results.items() if k != "evaluator"}, indent=2)[:4000])
    return 0


def _truth_full(ctx, cell) -> np.ndarray:
    """Oracle sanity: the withheld truth pixels of one cell (not a candidate)."""
    out = np.zeros(ctx.grid.footprint.shape, bool)
    ty, tx = cell.truth_yx
    sub = out[cell.bbox]
    sub[ty, tx] = True
    out[cell.bbox] = sub
    return out


if __name__ == "__main__":
    raise SystemExit(main())
