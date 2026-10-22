#!/usr/bin/env python3
"""Build the G86 competition GeoTIFF (validated, fail-closed).

Pipeline (identical to the validated holdout path in ``scripts/run_lane.py``):

1. features: competition structural stack + public USGS/DOE morphological stack
   + the lane's gravity–magnetic cross-gradient transform + catalogue geometry,
   all rank-normalised over the footprint;
2. model: L2 logistic regression fitted on the **full** catalogue as positives
   and background cells > 3 px from any mapped trace as negatives, with the
   King–Zeng prior correction to the documented hidden-positive rate;
3. posterior sharpening: an 8-orientation anisotropic matched filter
   (σ_parallel = 4 px, σ_perpendicular = 1.2 px) — the lane's emission-side
   mechanism, validated on the holdout (+0.035 DTI at fixed budget);
4. emission: shared decimated ranking (one dot per 3 x 3 tile, ranked by the
   shared expected-credit convolution) and a budget of 8 x 11,321 = 90,568 dots,
   the ratio selected on the holdout;
5. packaging: shared fail-closed writer (``gems57.submission_writer``) validates
   the on-disk TIFF against ``sample_submission.tif`` and writes a receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

from gems57 import emit as emit_mod                          # noqa: E402
from gems57.grid import load_grid                            # noqa: E402
from gems57.submission_writer import write_submission        # noqa: E402
from src.gems86 import features as F                         # noqa: E402
from src.gems86.live import line_filter, fit_full            # noqa: E402

FEATURES_TIF = ROOT / ".cache" / "data" / "training_features.tif"
K_PRIOR = 11_321          # withheld positive pixels of the shared holdout (n)
BUDGET_RATIO = 8.0        # dots per prior positive, selected on the holdout
COLLAR_PX = 3


def main() -> None:
    from scripts.protocol_preflight import require_feasible
    require_feasible()  # STOP before training/placement; missing evidence is not a pass.
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="docs/downloads")
    ap.add_argument("--note", default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--collar-px", type=int, default=COLLAR_PX)
    ap.add_argument("--budget-ratio", type=float, default=BUDGET_RATIO)
    ap.add_argument("--suppress-px", type=int, default=0)
    a = ap.parse_args()

    t0 = time.time()
    g = load_grid(ROOT / "data" / "bridge")
    grid_feats = F.structural(FEATURES_TIF, g.footprint, use_gmc=True)
    grid_feats.update(F.external(g.footprint))
    geom = F.geometry(g.catalogue, g.footprint)
    stack = {**{k: v for k, v in grid_feats.items()}, **geom}
    allowed = g.footprint & ~_dilate(g.catalogue, a.collar_px)
    prior = K_PRIOR / float(allowed.sum())

    print(f"features {len(stack)}; allowed {int(allowed.sum())}; prior {prior:.6f}", flush=True)
    p = fit_full(stack, g.catalogue, allowed, prior=prior, footprint=g.footprint,
                 suppress_px=a.suppress_px)
    print(f"posterior fitted in {time.time()-t0:.1f}s; max {p.max():.4g}", flush=True)
    sharp = line_filter(p)
    ranked, _ek = emit_mod.emit_decimated(sharp, allowed, tile_px=3)
    budget = int(round(a.budget_ratio * K_PRIOR))
    dots = emit_mod.emit_prefix(ranked, budget)
    print(f"dots {int(dots.sum())} of budget {budget}", flush=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pred = dots.astype(np.float32)
    digest = hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()[:8]
    tag = "offcat" if a.suppress_px > 0 else "prox"
    name = a.name or f"gems86-gmc-linepost-{tag}-{int(dots.sum())}d-{stamp}-{digest}-zeros"
    note = a.note or (f"GEMSDOE86 GMC cross-gradient + line-matched posterior; "
                      f"{int(dots.sum())} dots, 3px-spaced, EPSG:32611, all-finite [0,1]")
    assert len(note) <= 140, len(note)
    out = ROOT / a.out_dir / f"{name}.tif"
    receipt = write_submission(out, pred, ROOT / "data" / "bridge" / "sample_submission.tif",
                               g.footprint, note=note, name=name, catalogue=g.catalogue,
                               metadata=dict(lane="gems86-gmc-linepost",
                                             holdout_dti="see evidence/run_card.json",
                                             budget=budget, k_prior=K_PRIOR,
                                             feature_count=len(stack),
                                             budget_ratio=a.budget_ratio,
                                             collar_px=a.collar_px,
                                             suppress_px=a.suppress_px))
    print(json.dumps({k: receipt[k] for k in ("file", "sha256", "bytes", "note_chars")}, indent=2))
    v = receipt["validator"]
    print("validation:", v["all_checks_passed"], v["checks"])


def _dilate(mask: np.ndarray, px: int) -> np.ndarray:
    from scipy import ndimage as ndi
    return ndi.binary_dilation(np.asarray(mask, bool), iterations=px)


if __name__ == "__main__":
    main()
