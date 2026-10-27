"""Build the H86E-RIDF final surface and dots (full catalogue as training labels).

Pre-placement gate: protocol_preflight.require_like_for_like() (PA-86-01).
Outputs (gitignored): data/work/h86e_final_surface.npy, data/work/h86e_final_dots.npy
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor"), str(ROOT / "src")]
from gems57 import grid  # noqa: E402
from gems86_ridf import pipeline as P  # noqa: E402
from scripts.protocol_preflight import require_like_for_like  # noqa: E402
from scripts import check_h86e_registry as registry_check  # noqa: E402

BUDGET = 37_654


def main():
    # Historical builder: the literal stop precedes all candidate work.
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    cert = require_like_for_like()
    g = grid.load_grid(ROOT / "data")
    fp, cat = g.footprint, g.catalogue
    feats = np.load(ROOT / "data/work/h86e_features.npy", mmap_mode="r")
    X, y = P.sample_training(feats, cat, fp, seed=86)
    model = P.fit(X, y, seed=86)
    surface = P.predict(model, feats, fp)
    surface_path = ROOT / "data/work/h86e_final_surface.npy"
    surface_report = ROOT / "docs/evidence/h86e_registry_surface.json"
    np.save(surface_path, surface)
    # Check BEFORE disc_thin: a known duplicate must never reach placement.
    code = registry_check.main([str(surface_path), str(surface_report), "--surface"])
    result = json.loads(surface_report.read_text())
    if code or result.get("literal_gate_pass") is not True:
        raise RuntimeError("STOP: surface registry gate failed; no dot placement permitted")
    dcat = ndi.distance_transform_edt(~cat)
    allowed = fp & (dcat > P.COLLAR_PX)
    dots = P.disc_thin(surface, allowed, BUDGET)
    dots_path = ROOT / "data/work/h86e_final_dots.npy"
    dots_report = ROOT / "docs/evidence/h86e_registry_final_dots.json"
    np.save(dots_path, dots)
    code = registry_check.main([str(dots_path), str(dots_report)])
    result = json.loads(dots_report.read_text())
    if code or result.get("literal_gate_pass") is not True:
        raise RuntimeError("STOP: final-dot registry gate failed; no TIFF generation permitted")
    meta = dict(preflight_status=cert["status"], amendment=cert["amendment"],
                witness_representation=cert["witness_representation"],
                training_positives=int(y.sum()), training_negatives=int((y == 0).sum()),
                dots=int(dots.sum()), on_catalogue=int((dots & cat).sum()),
                outside_footprint=int((dots & ~fp).sum()),
                min_dcat_px=float(dcat[dots].min()), median_dcat_px=float(np.median(dcat[dots])))
    (ROOT / "docs/evidence/h86e_final_build.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
