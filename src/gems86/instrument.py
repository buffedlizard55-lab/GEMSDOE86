"""Hide-and-recover instrument for GEMSDOE86.

Uses the shared template's whole-component buffered draw
(``gems57.holdout.buffered_component_draw``) and the shared exact evaluator
(``gems57.evaluate_holdout.evaluate`` / ``pooled_summary``) unchanged.

Design (protocol rule 2)
------------------------
* Whole 8-connected mapped-fault components are withheld per label-blind eroded
  quadrant, so no withheld strand is a neighbouring chunk of a visible one.
* A 3 px (300 m) buffer removes the feature-context collar around withheld
  components -> every catalogue-derived feature sees only *visible* faults.
* Visible catalogue pixels are masked out of scoring pixel-exactly.
* Score: pooled DTI, alpha=0.2, beta=0.8, 300 m triangular kernel (3 px).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from gems57 import evaluate_holdout, holdout as holdout_mod


@dataclass
class Fold:
    name: str
    fold: dict            # dict consumed by evaluate_holdout.evaluate
    region: np.ndarray
    active: np.ndarray    # scored domain: footprint & region & ~known
    truth: np.ndarray
    visible: np.ndarray
    known: np.ndarray


def build(footprint: np.ndarray, catalogue: np.ndarray, *, seed: int = 20,
          hide_frac: float = 0.20, buffer_px: int = 3, boundary_px: int = 12) -> list[Fold]:
    class _G:  # minimal grid duck-type expected by the shared draw
        pass

    g = _G()
    g.footprint = np.asarray(footprint, bool)
    g.catalogue = np.asarray(catalogue, bool)
    folds, _quad = holdout_mod.buffered_component_draw(
        g, seed=seed, hide_frac=hide_frac, buffer_px=buffer_px, boundary_px=boundary_px)
    out = []
    for fd in folds:
        active = g.footprint & fd["region"] & ~fd["masked_known"]
        out.append(Fold(name=fd["name"], fold=fd, region=fd["region"], active=active,
                        truth=fd["truth"] & g.footprint,
                        visible=fd["visible"], known=fd["masked_known"]))
    return out


def terms(pred: np.ndarray, folds: Iterable[Fold]) -> np.ndarray:
    """Per-20-km-block (tp, fp, fn, n_truth) terms summed over folds."""
    total = None
    for f in folds:
        _res, t = evaluate_holdout.evaluate(pred, f.fold, f.fold["region"] & _footprint(f),
                                            origin=(0, 0), global_shape=pred.shape)
        total = t if total is None else total + t
    return total


def _footprint(f: Fold) -> np.ndarray:
    # region & active carry the footprint; reconstruct it once per fold
    return f.active | f.known | f.truth


def summarize(terms_by_arm: dict[str, np.ndarray], candidate: str) -> dict:
    return evaluate_holdout.pooled_summary(terms_by_arm, draws=1000, seed=520810,
                                           candidate=candidate)


def score_binary(pred: np.ndarray, folds: Iterable[Fold]) -> dict:
    """Exact pooled DTI of a binary field plus a block-bootstrap 95% CI."""
    t = terms(pred, folds)
    s = summarize({"candidate": t}, candidate="candidate")
    row = s["scores"]["candidate"]
    return dict(dti=row["dti"], ci95=row["ci95"], n_truth=row["withheld_positive_pixels"],
                tp=row["tpw"], fp=row["fpw"], fn=row["fnw"],
                evaluator_version=s["evaluator_version"],
                implementation_sha256=s["implementation_sha256"],
                clusters=s["bootstrap"]["clusters"])
