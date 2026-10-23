#!/usr/bin/env python3
"""REPORT-ONLY instruments for the CONCENTRATION session (never gates, brief section 6).

Three readouts, all fold-fair, all labelled PROXY:

1. ``catalogue hide-and-recover`` (the repo's standard instrument): four spatial folds, whole
   catalogue components withheld, every collar rebuilt from the *visible* catalogue only, DTI
   pooled over 20 km blocks with a paired bootstrap CI.  For this axis the instrument is
   structurally biased **positive** — concentration moves mass toward catalogue-dense blocks,
   and the withheld pixels are catalogue; so the sign of this number is not evidence for the
   live chunks.  It is reported because a *negative* reading would still be informative.

2. ``shuffled-prior null``: the identical dose and block size, with the block prior shuffled
   among footprint blocks (same marginal distribution, no spatial information, fixed seed).
   This is the control that separates "the prior knows something" from "any relocation toward
   a plausible-looking map of blocks scores about the same".  Every arm is read against this.

3. ``SGMC control``: official-kernel DTI against USGS state-map faults that are *not* in the
   competition catalogue, off-catalogue by > 3 px.  Also biased positive for this axis (both
   are catalogue-like maps), stated so nobody mistakes it for an independent score.

Writes ``evidence/concentration_instruments_20261023.json``.  No leaderboard, no labels.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import evaluate_holdout, metric  # noqa: E402
from gems57.grid import load_grid  # noqa: E402
from gems57.holdout import buffered_component_draw  # noqa: E402
from gems86_axis import bands as bandmod  # noqa: E402
from gems86_axis import variants  # noqa: E402

R0_REL = ("data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-"
          "20261004T220000Z-e5eb6e7e-zeros.tif")
D28_REL = ("data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-"
           "20261003-8acb75e1f2cc-nan.tif")
EXT_REL = ".cache/gems_data/external/geodawn_extensions_u8.tif"
SGMC_REL = ".cache/gems_data/external/derived_sgmc_faults_100m_u8.tif"
SEED = 20261023

#: One row per arm.  ``prior`` is the block prior actually used: ``mixed`` is the ledger's own
#: two-term prior, ``shuffle`` permutes it among footprint blocks (no spatial information),
#: ``tmi`` and ``cat`` are the single-term decompositions.  The decomposition is what decides
#: whether any gain can transfer to NEW faults or is only the instrument's circular reward for
#: following the withheld catalogue.
ARMS = [
    {"label": "conc15-b5km", "block_px": 50, "move": 0.15, "dest_frac": 0.20, "prior": "mixed"},
    {"label": "conc24", "block_px": 10, "move": 0.24, "dest_frac": 0.20, "prior": "mixed"},
    {"label": "conc15-t05", "block_px": 10, "move": 0.15, "dest_frac": 0.05, "prior": "mixed"},
    {"label": "null-b1km-move15", "block_px": 10, "move": 0.15, "dest_frac": 0.20, "prior": "shuffle"},
    {"label": "tmi-only-b1km-move15", "block_px": 10, "move": 0.15, "dest_frac": 0.20, "prior": "tmi"},
    {"label": "cat-only-b1km-move15", "block_px": 10, "move": 0.15, "dest_frac": 0.20, "prior": "cat"},
]


def dots_from(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        arr = src.read(1)
    return (np.nan_to_num(arr, nan=0.0) > 0.5) & footprint


def context_bands() -> dict:
    with rasterio.open(ROOT / EXT_REL) as src:
        names = list(src.descriptions)
        q = src.read(names.index(bandmod.TMI_BAND) + 1)
    tmi = (q > 0).astype(np.float32) * q.astype(np.float32)
    return {"tmi_up150": tmi, "tmi_grad": bandmod.gradient_magnitude(tmi, fill_value=0.0)}


def single_term_prior(ctx: dict, bands: dict, catalogue: np.ndarray, block_px: int,
                      term: str) -> np.ndarray:
    """One term of ``variants.block_prior``, identically aggregated and z-scored."""
    foot = ctx["footprint"]
    h, w = foot.shape
    nb, mb = h // block_px, w // block_px
    if term == "cat":
        catf = (catalogue & foot).astype(np.float32)
        field = ndi.uniform_filter(catf, size=3 * block_px, mode="constant")
    elif term == "tmi":
        field = np.nan_to_num(bands["tmi_grad"], nan=0.0)
    else:
        raise ValueError(term)
    blk = field[: nb * block_px, : mb * block_px].reshape(nb, block_px, mb, block_px).mean(axis=(1, 3))
    fpb = foot[: nb * block_px, : mb * block_px].astype(np.float32).reshape(
        nb, block_px, mb, block_px).mean(axis=(1, 3))
    prior = bandmod.zscore(blk)
    prior[fpb <= 0] = -np.inf
    return prior.astype(np.float32)


def arm_prior(arm: dict, ctx: dict, bands: dict, catalogue: np.ndarray) -> np.ndarray:
    pack = variants.block_prior(ctx, bands, catalogue, block_px=arm["block_px"])
    if arm["prior"] == "mixed":
        return pack["prior"]
    if arm["prior"] == "shuffle":
        return shuffled_prior(pack["prior"], pack["footprint_blocks"])
    return single_term_prior(ctx, bands, catalogue, arm["block_px"], arm["prior"])


def shuffled_prior(prior: np.ndarray, footprint_blocks: np.ndarray) -> np.ndarray:
    """Same multiset of block priors, permuted among footprint blocks (fixed seed)."""
    finite = np.isfinite(prior)
    out = np.full(prior.shape, -np.inf, np.float32)
    vals = prior[finite]
    rng = np.random.default_rng(SEED)
    out[finite] = rng.permutation(vals)
    return out


def main() -> int:
    t0 = time.time()
    grid = load_grid(ROOT / "data/bridge")
    foot = grid.footprint
    bands = context_bands()
    d28 = dots_from(ROOT / D28_REL, foot)
    r0 = dots_from(ROOT / R0_REL, foot)
    folds, _draw = buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    # Compact per-fold bookkeeping only: the draw's own receipt carries full-grid arrays that
    # would bloat this evidence file past GitHub's 100 MB blob limit (they are re-derivable from
    # the pinned seed and inputs by re-running this script).
    fold_summary = [{"fold": f["name"],
                     "region_px": int(np.asarray(f["region"]).sum()),
                     "visible_catalogue_px": int(np.asarray(f["visible"]).sum()),
                     "withheld_catalogue_px": int(np.asarray(grid.catalogue).sum())
                                              - int(np.asarray(f["visible"]).sum()),
                     "scored_truth_px": int(np.asarray(f["truth"]).sum())}
                    for f in folds]
    print(f"[folds] {[f['name'] for f in folds]}", flush=True)

    terms: dict[str, list] = {"r0": []}
    for arm in ARMS:
        terms[arm["label"]] = []

    for fold in folds:
        visible = fold["visible"]
        dist_visible = ndi.distance_transform_edt(~visible)
        ctx_fold = {"footprint": foot, "catalogue": visible,
                    "grid": {"shape": foot.shape}}
        parent_fold = d28 & (dist_visible > 2.0)          # the parent's own rule, fold-fair
        _, t_r0 = evaluate_holdout.evaluate(parent_fold.astype(np.float32), fold, foot,
                                            block_side=200, origin=(0, 0),
                                            global_shape=grid.shape)
        terms["r0"].append(t_r0)
        for arm in ARMS:
            label = arm["label"]
            prior = arm_prior(arm, ctx_fold, bands, visible)
            mask, _ = variants.concentration(parent_fold, ctx_fold, bands, prior, arm["move"],
                                             2.0, 2.8284271247461903,
                                             block_px=arm["block_px"],
                                             dest_block_frac=arm["dest_frac"])
            _, t = evaluate_holdout.evaluate(mask.astype(np.float32), fold, foot,
                                             block_side=200, origin=(0, 0),
                                             global_shape=grid.shape)
            terms[label].append(t)
        print(f"[fold {fold['name']}] done ({time.time() - t0:.0f}s)", flush=True)

    pooled = {k: np.sum(np.stack(v), axis=0) for k, v in terms.items()}
    summary = {}
    for arm in ARMS:
        label = arm["label"]
        arms = {"r0": pooled["r0"], label: pooled[label]}
        summary[label] = evaluate_holdout.pooled_summary(arms, draws=1000, seed=SEED,
                                                         candidate=label)
    # paired difference candidate - shuffled-prior null, on the same blocks
    null = "null-b1km-move15"
    null_diff = {}
    for arm in ARMS:
        label = arm["label"]
        if label == null:
            continue
        null_diff[label] = evaluate_holdout.pooled_summary(
            {null: pooled[null], label: pooled[label]}, draws=1000, seed=SEED, candidate=label)

    # ---- SGMC control (independent map, still catalogue-like: stated bias) -------------
    with rasterio.open(ROOT / SGMC_REL) as src:
        sgmc = src.read(1) > 0
    off = sgmc & foot & ~grid.catalogue & (ndi.distance_transform_edt(~grid.catalogue) > 3.0)
    sgmc_scores = {}
    for name, mask in (("r0", r0),):
        r = metric.dti_binary(mask, off, valid=foot, known=grid.catalogue)
        sgmc_scores[name] = {k: r[k] for k in ("dti", "tp", "fp", "fn", "n_truth", "n_emitted")}
    ctx_full = {"footprint": foot, "catalogue": grid.catalogue, "grid": {"shape": foot.shape}}
    for arm in ARMS:
        label = arm["label"]
        prior = arm_prior(arm, ctx_full, bands, grid.catalogue)
        mask, _ = variants.concentration(r0, ctx_full, bands, prior, arm["move"], 2.0,
                                         2.8284271247461903, block_px=arm["block_px"],
                                         dest_block_frac=arm["dest_frac"])
        r = metric.dti_binary(mask, off, valid=foot, known=grid.catalogue)
        sgmc_scores[label] = {k: r[k] for k in ("dti", "tp", "fp", "fn", "n_truth", "n_emitted")}
        sgmc_scores[label]["delta_vs_r0"] = r["dti"] - sgmc_scores["r0"]["dti"]

    out = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 1),
        "evidence_class": "PROXY",
        "never_a_gate": True,
        "design": {
            "holdout": "buffered whole-component catalogue hide-and-recover, seed 20, "
                       "hide_frac 0.20, 3 px context buffer, 20 km pooled blocks",
            "fold_fairness": "the parent's 2 px collar AND the block prior are rebuilt from each "
                             "fold's visible catalogue only; the TMI band is label-free",
            "bias_statement": ("for CONCENTRATION this instrument is structurally biased positive: "
                               "the axis moves mass toward catalogue-dense blocks and the withheld "
                               "positives are catalogue pixels. Only a NEGATIVE reading is "
                               "informative; a positive one must not be read as evidence about the "
                               "live chunks."),
        },
        "fold_summary": fold_summary,
        "pooled": summary,
        "vs_shuffled_prior_null": null_diff,
        "sgmc_control": sgmc_scores,
        "sgmc_note": "SGMC is an independent map but still catalogue-like; it is biased the same "
                     "way as the holdout for this axis.",
    }
    p = ROOT / "evidence/concentration_instruments_20261023.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    def _clean(o):
        if isinstance(o, dict):
            return {k: _clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_clean(v) for v in o]
        if isinstance(o, np.ndarray):
            return _clean(o.tolist())
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        return o

    p.write_text(json.dumps(_clean(out), indent=2) + "\n")
    for label, s in summary.items():
        d = s["paired_differences"]["r0"]
        print(f"{label:20s} r0={s['scores']['r0']['dti']:.5f} "
              f"cand={s['scores'][label]['dti']:.5f} "
              f"delta={d['delta']:+.5f} ci95={[round(x, 5) for x in d['ci95']]}")
    print(f"wrote {p} ({out['elapsed_s']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
