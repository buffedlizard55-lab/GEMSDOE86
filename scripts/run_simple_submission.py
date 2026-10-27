#!/usr/bin/env python3
"""Simple submission generator using GMC linepost features with decimated ranking.

This is a lightweight version of build_submission.py that avoids heavy caching
and runs the full uniqueness audit.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

from gems57 import emit as EMIT
from gems57.grid import load_grid
from gems57.submission_writer import write_submission
from gems57 import uniqueness as U
from gems57 import validate as V
from src.gems86 import features as F
from src.gems86.live import line_filter, build_posterior

BRIDGE = ROOT / "data" / "bridge"
FEATURES_TIF = BRIDGE / "training_features.tif"
K_PRIOR = 11_321
BUDGET_RATIO = 8.0
COLLAR_PX = 3
TILE_PX = 3


def main():
    from scripts.protocol_preflight import require_like_for_like
    cert = require_like_for_like()
    print(f"Protocol gate: {cert['status']}")

    t0 = time.time()
    g = load_grid(BRIDGE)
    
    # Build features (no caching for simplicity)
    print("Building structural features...")
    grid_feats = F.structural(FEATURES_TIF, g.footprint, use_gmc=True, cache=False)
    print(f"  Structural: {len(grid_feats)} features")
    
    print("Building external features...")
    ext_feats = F.external(g.footprint, cache=False)
    print(f"  External: {len(ext_feats)} features")
    
    print("Building geometry features...")
    geom = F.geometry(g.catalogue, g.footprint)
    print(f"  Geometry: {len(geom)} features")
    
    stack = {**grid_feats, **ext_feats, **geom}
    print(f"Total features: {len(stack)}")

    allowed = g.footprint & ~ndi.binary_dilation(g.catalogue, iterations=COLLAR_PX)
    prior = K_PRIOR / float(allowed.sum())
    print(f"Allowed: {int(allowed.sum())}, Prior: {prior:.6f}")

    # Fit posterior
    print("Fitting posterior...")
    p = build_posterior(stack, g.catalogue, allowed, prior=prior, footprint=g.footprint)
    print(f"Posterior max: {p.max():.4f}")

    # Line filter
    print("Applying line filter...")
    sharp = line_filter(p)

    # Decimated ranking emission
    print("Emitting dots...")
    ranked, _ = EMIT.emit_decimated(sharp, allowed, tile_px=TILE_PX)
    budget = int(round(BUDGET_RATIO * K_PRIOR))
    dots = EMIT.emit_prefix(ranked, budget).astype(bool)
    print(f"Emitted {int(dots.sum())} dots (budget {budget})")

    pred = dots.astype(np.float32)

    # Uniqueness audit (full registry)
    print("Running uniqueness audit...")
    scored_dir = ROOT / "data" / "scored_fleet"
    paths = sorted(scored_dir.glob("*.tif"))
    records = [
        {
            "repo_first": p.name.split("__")[0] if "__" in p.name else "scored_registry",
            "sources": [p.name],
            "cache_file": str(p.resolve()),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in paths
    ]
    registry_index = {"complete_accessible_scan": True, "rasters": records}
    expected_grid = (g.footprint.shape, g.crs, g.transform)

    # Pre-placement surface
    pre_surf = np.clip(sharp, 0.0, 1.0).astype(np.float32)
    pre_surf[g.catalogue | ~g.footprint] = 0.0
    
    surf_rep = U.compare_array_to_registry(
        pre_surf, registry_index, g.footprint,
        file_sha256=hashlib.sha256(pre_surf.tobytes()).hexdigest(),
        expected_grid=expected_grid,
    )
    surf_summary = U.summarize_registry_rows(
        surf_rep["rows"],
        registry_rasters_expected=len(records),
        complete_accessible_scan=True,
        source_errors=[],
        candidate_meta=dict(
            my_file=None, my_dots=int((pre_surf > 0).sum()),
            candidate_decoded_sha256=hashlib.sha256(pre_surf.tobytes()).hexdigest(),
            candidate_file_sha256=None, candidate_rank_variation=True
        ),
        scope="Pre-placement surface audit"
    )

    # Post-placement dots
    dots_rep = U.compare_array_to_registry(
        pred, registry_index, g.footprint,
        file_sha256=hashlib.sha256(pred.tobytes()).hexdigest(),
        expected_grid=expected_grid,
    )
    dots_summary = U.summarize_registry_rows(
        dots_rep["rows"],
        registry_rasters_expected=len(records),
        complete_accessible_scan=True,
        source_errors=[],
        candidate_meta=dict(
            my_file=None, my_dots=int(dots.sum()),
            candidate_decoded_sha256=hashlib.sha256(pred.tobytes()).hexdigest(),
            candidate_file_sha256=None, candidate_rank_variation=True
        ),
        scope="Post-placement dots audit"
    )
    dots_two_phase = U.two_phase_summary(dots_rep["rows"], int(g.footprint.sum()), expected_rasters=len(records))

    surf_unique = surf_summary["unique"]
    dots_unique = dots_summary["unique"]
    print(f"Surface unique: {surf_unique}, Dots unique: {dots_unique}")
    print(f"Surface worst rho: {surf_summary['worst_spearman_full_footprint']:.4f}")
    print(f"Dots worst overlap: {dots_summary['worst_dot_overlap']:.4f}")

    # Write submission
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(pred.tobytes()).hexdigest()[:8]
    name = f"gems86-gmc-linepost-{int(dots.sum())}d-{stamp}-{digest}-zeros"
    note = f"GEMSDOE86 GMC cross-gradient + line-matched posterior; {int(dots.sum())} dots, 3px-spaced, EPSG:32611, all-finite [0,1]"
    assert len(note) <= 140

    out = ROOT / "docs" / "downloads" / f"{name}.tif"
    receipt = write_submission(out, pred, BRIDGE / "sample_submission.tif", g.footprint,
                               note=note, name=name, catalogue=g.catalogue,
                               metadata=dict(lane="gems86-gmc-linepost",
                                             budget=budget, k_prior=K_PRIOR,
                                             feature_count=len(stack),
                                             budget_ratio=BUDGET_RATIO,
                                             collar_px=COLLAR_PX))

    print(f"Written: {out}")
    print(f"SHA256: {receipt['sha256']}")
    print(f"Validation: {receipt['validator']['all_checks_passed']} {receipt['validator']['checks']}")

    # Run card
    run_card = {
        "schema_version": "gems-parallel-run-card-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repository": "buffedlizard55-lab/GEMSDOE86",
        "lane_id": "GMC-LINEPOST",
        "ok_to_download_and_submit": bool(receipt["validator"]["all_checks_passed"] and surf_unique and dots_unique),
        "verdict": "promote" if (receipt["validator"]["all_checks_passed"] and surf_unique and dots_unique) else "negative",
        "experiments_executed": 1,
        "elapsed_wall_seconds": round(time.time() - t0, 2),
        "weekly_submission_slots_used": 0,
        "hypothesis": "Fault traces missing from the catalogue continue the structural grain defined by gravity-magnetic cross-gradient coherence and visible trace geometry.",
        "mechanism": "GMC cross-gradient + structural coherence + catalogue geometry features -> L2 logistic regression -> anisotropic line filter -> decimated ranking emission.",
        "named_non_fault_mimic": "Lithologic contacts with coincident gravity/magnetic gradients but no fault displacement.",
        "holdout_dti": {"status": "NOT_RUN"},
        "uniqueness": {
            "pre_placement_surface": surf_summary,
            "final_dots": dots_summary,
            "two_phase": dots_two_phase,
        },
        "submission_artifact": {
            "tif_file": str(out.relative_to(ROOT)),
            "tif_bytes": receipt["bytes"],
            "raster_sha256": receipt["sha256"],
            "emitted_positive_pixels": int(dots.sum()),
            "footprint_fraction": receipt["validator"]["footprint_fraction"],
            "submission_name": name,
            "submission_note": note,
        },
        "validator_output": receipt["validator"],
    }

    (ROOT / "run_card_gmc.json").write_text(json.dumps(run_card, indent=2) + "\n")
    print("=" * 76)
    print(f"VERDICT: {run_card['verdict'].upper()} | OK_TO_SUBMIT={run_card['ok_to_download_and_submit']}")
    print(f"Artifact: {out}")
    print("=" * 76)


if __name__ == "__main__":
    main()