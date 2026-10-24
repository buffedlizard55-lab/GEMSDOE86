#!/usr/bin/env python3
"""G86 experiment driver: features -> model -> optimal emission -> pooled DTI.

Usage
-----
    python scripts/experiment.py --arm gmc --out evidence/exp1_gmc.json

Arms
----
``structural``  potential-field/structural bands only (no catalogue geometry)
``geometry``    catalogue geometry only (visible-only, per fold)
``full``        structural + geometry
``full_nogmc``  full minus the new cross-gradient features (ablation control)

Every arm is fitted **inside each fold** on visible positives only; the withheld
components are never used for fitting.  Emission uses the shared exact greedy
allocator (``gems57.emit.greedy_allocate``) with ``k_truth`` = the fold's hidden
positive count, and scoring uses the shared exact evaluator.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

from gems57 import emit as emit_mod                     # noqa: E402
from gems57.grid import load_grid                       # noqa: E402
from src.gems86 import features as F                    # noqa: E402
from src.gems86 import instrument                       # noqa: E402

FEATURES_TIF = ROOT / ".cache" / "data" / "training_features.tif"


def arm_names(arm: str, keys: list[str]) -> list[str]:
    gmc = [k for k in keys if k.startswith("gmc")]
    geom = [k for k in keys if not k.startswith("gmc") and k in GEOM_KEYS]
    struct = [k for k in keys if not k.startswith("gmc") and k not in GEOM_KEYS]
    if arm == "gmc":
        return struct + gmc
    if arm == "structural":
        return struct
    if arm == "geometry":
        return geom
    if arm == "external":
        return [k for k in keys if k.startswith(("lid_", "topo_", "rad_", "chi_"))]
    if arm == "full":
        return struct + gmc + geom
    if arm == "full_nogmc":
        return struct + geom
    raise SystemExit(f"unknown arm {arm}")


GEOM_KEYS = {"d_vis", "log_d_vis", "d_tip", "log_d_tip", "tip_continuation", "tip_along",
             "tip_cross", "along", "cross", "trace_coh", "density", "trace_continuation"}


def fit_predict(stack: dict[str, np.ndarray], names: list[str], fold,
                *, n_neg: int = 400_000, seed: int = 7) -> np.ndarray:
    """Fit P(fault | features) on visible positives vs far background; predict grid.

    The class-balanced fit is transformed to a *prevalence-calibrated* probability
    with the King & Zeng (2001) prior correction, using the fold's hidden positive
    rate as the target prior.  This is required by the allocator: its marginal
    test ``dT > c*(1-k)`` is in probability units, so an over-calibrated p makes
    every diffuse cell look worth a dot.
    """
    pos = fold.visible & fold.region
    d_px = _distance_px(fold.visible, fold.name)
    neg_pool = fold.active & ~fold.visible & (d_px > 3.0)
    rng = np.random.default_rng(seed)
    py, px = np.nonzero(pos)
    ny, nx = np.nonzero(neg_pool)
    if ny.size > n_neg:
        sel = rng.choice(ny.size, n_neg, replace=False)
        ny, nx = ny[sel], nx[sel]
    Xp = np.stack([np.asarray(stack[n][py, px], np.float32) for n in names], -1)
    Xn = np.stack([np.asarray(stack[n][ny, nx], np.float32) for n in names], -1)
    y = np.concatenate([np.ones(len(Xp)), np.zeros(len(Xn))])
    Xall = np.concatenate([Xp, Xn])
    sc = StandardScaler().fit(Xall)
    clf = LogisticRegression(C=0.5, class_weight="balanced", max_iter=400)
    clf.fit(sc.transform(Xall), y)
    pi = float(fold.truth.sum()) / max(float(fold.active.sum()), 1.0)
    offset = float(np.log(pi / (1.0 - pi))) - float(np.log(0.5 / 0.5))
    p = np.zeros(fold.visible.shape, np.float32)
    H, W = p.shape
    step = 512
    for r0 in range(0, H, step):
        r1 = min(H, r0 + step)
        block = np.stack([np.asarray(stack[n][r0:r1], np.float32) for n in names], -1)
        z = clf.decision_function(sc.transform(block.reshape(-1, len(names)))) + offset
        p[r0:r1] = (1.0 / (1.0 + np.exp(-z))).reshape(r1 - r0, W)
    p[~fold.active] = 0.0
    return p, clf, sc


_DIST_CACHE: dict[str, np.ndarray] = {}


def _distance_px(visible: np.ndarray, key: str) -> np.ndarray:
    from scipy import ndimage as ndi
    if key not in _DIST_CACHE:
        _DIST_CACHE.clear()
        _DIST_CACHE[key] = ndi.distance_transform_edt(~np.asarray(visible, bool)).astype(np.float32)
    return _DIST_CACHE[key]


def run(arm: str, *, seed: int = 20, hide_frac: float = 0.20, save: Path | None = None,
        use_gmc: bool = True) -> dict:
    from scripts.protocol_preflight import require_feasible
    require_feasible()  # Imported orchestration must not bypass the CLI stop.
    t0 = time.time()
    g = load_grid(ROOT / "data" / "bridge")
    need_struct = arm in ("structural", "full", "full_nogmc", "gmc", "external")
    struct = F.structural(FEATURES_TIF, g.footprint, use_gmc=use_gmc) if need_struct else {}
    if arm in ("external", "full", "full_nogmc"):
        struct.update(F.external(g.footprint))
    print(f"  grid features: {len(struct)}", flush=True)
    folds = instrument.build(g.footprint, g.catalogue, seed=seed, hide_frac=hide_frac)
    all_terms, per_fold = {}, {}
    for f in folds:
        geom = F.geometry(f.visible, g.footprint) if arm in ("geometry", "full", "full_nogmc") else {}
        stack = {**struct, **geom}
        names = arm_names(arm, list(stack))
        p, clf, sc = fit_predict(stack, names, f)
        allowed = f.active & ~_dilate(f.visible, 3)
        k_truth = float(f.truth.sum())
        alloc = emit_mod.greedy_allocate(p, allowed, k_truth)
        res = instrument.score_binary(alloc.emitted, [f])
        per_fold[f.name] = dict(dti=res["dti"], ci95=res["ci95"], n_dots=alloc.n_dots,
                                n_truth=int(k_truth), coverage=float(
                                    (alloc.emitted & f.truth).sum() / max(k_truth, 1)))
        all_terms[f.name] = instrument.terms(alloc.emitted, [f])
        del geom, stack, p
        import gc; gc.collect()
        print(f"  {f.name}: DTI {res['dti']:.4f} dots {alloc.n_dots} "
              f"hit {per_fold[f.name]['coverage']:.3f}", flush=True)
    merged = sum(all_terms.values())
    pooled = instrument.summarize({"candidate": merged}, "candidate")
    row = pooled["scores"]["candidate"]
    out = dict(arm=arm, seed=seed, hide_frac=hide_frac,
               evidence_class="HOLDOUT-DTI", evaluator_version=pooled["evaluator_version"],
               implementation_sha256=pooled["implementation_sha256"],
               pooled_dti=row["dti"], ci95=row["ci95"],
               withheld_positive_pixels=row["withheld_positive_pixels"],
               tpw=row["tpw"], fpw=row["fpw"], fnw=row["fnw"],
               per_fold=per_fold, clusters=pooled["bootstrap"]["clusters"],
               features=names, elapsed_s=round(time.time() - t0, 1))
    print(f"[{arm}] pooled DTI {row['dti']:.5f} CI {row['ci95']} "
          f"(n={row['withheld_positive_pixels']}) in {out['elapsed_s']}s", flush=True)
    if save:
        save.parent.mkdir(parents=True, exist_ok=True)
        save.write_text(json.dumps(out, indent=2) + "\n")
    return out


def _dilate(mask: np.ndarray, px: int) -> np.ndarray:
    from scipy import ndimage as ndi
    return ndi.binary_dilation(np.asarray(mask, bool), iterations=px)


def main() -> None:
    from scripts.protocol_preflight import require_feasible
    require_feasible()  # STOP before training/placement; missing evidence is not a pass.
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="full")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    run(a.arm, save=Path(a.out) if a.out else None)


if __name__ == "__main__":
    main()
