#!/usr/bin/env python3
"""G86 lane driver — one code path for the holdout and the live submission.

Stages
------
``holdout``  builds the shared whole-component buffered folds, fits the lane
             model inside each fold on visible positives only, ranks cells with
             the shared decimated emitter and sweeps the dot budget.  Reports
             pooled DTI with a 20 km block-bootstrap 95% CI for both the lane
             arm and its no-cross-gradient ablation.
``live``     refits the identical model on the *full* catalogue, emits with the
             calibrated budget rule, and hands the array to the shared
             fail-closed writer (``gems57.submission_writer``).

Nothing is clipped or repaired: the writer receives an array that is already
finite, inside [0, 1] and zero outside the footprint.
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

from gems57 import emit as emit_mod                      # noqa: E402
from gems57 import grid as grid_mod                      # noqa: E402
from gems57.grid import load_grid                        # noqa: E402
from src.gems86 import features as F                     # noqa: E402
from src.gems86.live import line_filter                  # noqa: E402
from src.gems86 import instrument                        # noqa: E402

FEATURES_TIF = ROOT / ".cache" / "data" / "training_features.tif"
PCACHE = ROOT / ".cache" / "posterior"
GEOM = ("d_vis", "log_d_vis", "d_tip", "log_d_tip", "tip_continuation", "tip_along",
        "tip_cross", "along", "cross", "trace_coh", "density", "trace_continuation")
GMC = ("gmc4_contact", "gmc4_oppose", "gmc4_strike_coh", "gmc4_aligned")
COLLAR_PX = 3


def arms(grid_feats: dict, geom: dict, name: str) -> dict[str, np.ndarray]:
    lid = [k for k in grid_feats if k.startswith(("lid_", "topo_", "rad_", "chi_"))]
    struct = [k for k in grid_feats if k not in lid and k not in GMC]
    gmc = [k for k in grid_feats if k in GMC]
    if name == "lane":
        keys = struct + gmc + list(GEOM)
    elif name == "no_gmc":
        keys = struct + list(GEOM)
    elif name == "no_geom":
        keys = struct + gmc
    elif name == "external_only":
        keys = lid
    else:
        raise KeyError(name)
    return {k: (grid_feats.get(k) if k in grid_feats else geom[k]) for k in keys}


def fit_predict(stack: dict[str, np.ndarray], fold, *, prior: float,
                n_neg: int = 300_000, seed: int = 7, model: str = "logit") -> np.ndarray:
    """Fold posterior: identical code path to the shipped artifact.

    Positives are the *visible* catalogue of the fold; the emission mask is
    ``fold.active``; withheld components are never seen by the fit.
    """
    from src.gems86.live import build_posterior
    if not np.any(fold.visible & fold.region):
        raise ValueError("fold has no visible positives")
    return build_posterior(stack, fold.visible & fold.region, fold.active,
                           prior=prior, footprint=fold.active | fold.known | fold.truth,
                           n_neg=n_neg, seed=seed)


def rank_dots(p: np.ndarray, allowed: np.ndarray, tile_px: int = 3):
    ranked, _ek = emit_mod.emit_decimated(p, allowed, tile_px=tile_px)
    return ranked


@dataclass
class ArmResult:
    arm: str
    ratios: list[float]
    dti: list[float]
    ci: list[list[float]]
    dots: list[int]
    curve: list[dict]


def budget_sweep(ranked_by_fold: dict[str, np.ndarray], folds, ratios) -> ArmResult:
    rows = []
    for r in ratios:
        terms = None
        ndots = 0
        for f in folds:
            k = float(f.truth.sum())
            dots = emit_mod.emit_prefix(ranked_by_fold[f.name], int(round(r * k)))
            ndots += int(dots.sum())
            t = instrument.terms(dots, [f])
            terms = t if terms is None else terms + t
            del dots
        s = instrument.summarize({"candidate": terms}, "candidate")
        row = s["scores"]["candidate"]
        rows.append(dict(ratio=r, dti=row["dti"], ci95=row["ci95"], dots=ndots,
                         n_truth=row["withheld_positive_pixels"]))
        print(f"    ratio {r:5.1f}xK  DTI {row['dti']:.5f}  dots {ndots}", flush=True)
    best = max(rows, key=lambda x: x["dti"])
    return ArmResult("", [x["ratio"] for x in rows], [x["dti"] for x in rows],
                     [x["ci95"] for x in rows], [x["dots"] for x in rows], rows)


def holdout(arm_names_: tuple[str, ...] = ("lane", "no_gmc"),
            ratios=(0.5, 1.0, 2.0, 4.0, 8.0, 16.0), model: str = "logit",
            use_line_filter: bool = True, tag: str = "") -> dict:
    from scripts.protocol_preflight import require_feasible
    require_feasible()  # Imported orchestration must not bypass the CLI stop.
    t0 = time.time()
    g = load_grid(ROOT / "data" / "bridge")
    grid_feats = F.structural(FEATURES_TIF, g.footprint, use_gmc=True)
    grid_feats.update(F.external(g.footprint))
    folds = instrument.build(g.footprint, g.catalogue)
    PCACHE.mkdir(parents=True, exist_ok=True)
    results = {}
    for arm in arm_names_:
        ranked_by_fold = {}
        for f in folds:
            geom = F.geometry(f.visible, g.footprint)
            stack = arms(grid_feats, geom, arm)
            names = list(stack)
            prior = float(f.truth.sum()) / max(float(f.active.sum()), 1.0)
            p = fit_predict(stack, f, prior=prior, model=model)
            allowed = f.active & ~_dilate(f.visible, COLLAR_PX)
            ranked = rank_dots(line_filter(p) if use_line_filter else p, allowed)
            np.save(PCACHE / f"{arm}_{model}_{f.name}_ranked.npy", ranked)
            np.save(PCACHE / f"{arm}_{model}_{f.name}_p.npy", p.astype(np.float16))
            ranked_by_fold[f.name] = ranked
            del geom, stack, p, ranked
            gc.collect()
        print(f"  [{arm}] sweeping budget", flush=True)
        res = budget_sweep(ranked_by_fold, folds, ratios)
        results[arm] = dict(features=names, curve=res.curve,
                            best=max(res.curve, key=lambda x: x["dti"]),
                            elapsed_s=round(time.time() - t0, 1))
        del ranked_by_fold
        gc.collect()
    for arm, r in results.items():
        b = r["best"]
        print(f"[{arm}] BEST ratio {b['ratio']}xK  HOLDOUT-DTI {b['dti']:.5f} "
              f"CI {b['ci95']}  dots {b['dots']}", flush=True)
    out = dict(evidence_class="HOLDOUT-DTI",
               evaluator_version=instrument.evaluate_holdout.VERSION,
               implementation_sha256=instrument.evaluate_holdout.implementation_hashes(),
               n_withheld_positives=int(sum(f.truth.sum() for f in folds)),
               folds=[f.name for f in folds], results=results,
               elapsed_s=round(time.time() - t0, 1))
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence" / f"holdout_sweep_{model}{tag}.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def _dilate(mask: np.ndarray, px: int) -> np.ndarray:
    from scipy import ndimage as ndi
    return ndi.binary_dilation(np.asarray(mask, bool), iterations=px)


def main(argv=None) -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()  # No model experiments under an unsatisfiable protocol.
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="holdout", choices=["holdout"])
    ap.add_argument("--model", default="logit", choices=["logit", "hgb"])
    ap.add_argument("--arms", default="lane")
    ap.add_argument("--ratios", default="4,6,8,10,12")
    ap.add_argument("--no-line-filter", action="store_true")
    ap.add_argument("--tag", default="")
    a = ap.parse_args(argv)
    holdout(tuple(a.arms.split(",")), tuple(float(x) for x in a.ratios.split(",")), a.model,
            use_line_filter=not a.no_line_filter, tag=a.tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
