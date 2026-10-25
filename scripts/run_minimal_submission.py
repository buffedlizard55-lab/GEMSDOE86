#!/usr/bin/env python3
"""Minimal submission using only key geophysical features + catalogue geometry.

Avoids heavy GMC computation by using pre-computed structural features from
the cached .npy files if available, or computing only essential features.
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
from src.gems86.io import read_band, BANDS

BRIDGE = ROOT / "data" / "bridge"
FEATURES_TIF = BRIDGE / "training_features.tif"
CACHE = ROOT / ".cache" / "features"
K_PRIOR = 11_321
BUDGET_RATIO = 8.0
COLLAR_PX = 3
TILE_PX = 3


def rank_normalize(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    a = np.asarray(a, np.float32)
    m = np.isfinite(a) & valid
    out = np.zeros(a.shape, np.float32)
    n = int(m.sum())
    if n < 2:
        return out
    vals = a[m]
    order = np.argsort(vals, kind="stable")
    ranks = np.empty(n, np.float32)
    ranks[order] = np.arange(n, dtype=np.float32)
    if n > 1:
        uniq, inv, cnt = np.unique(vals[order], return_inverse=True, return_counts=True)
        if (cnt > 1).any():
            sums = np.bincount(inv, weights=ranks[order])
            means = (sums / cnt).astype(np.float32)
            ranks[order] = means[inv]
    out[m] = ranks / max(n - 1, 1)
    return out


def line_filter(p: np.ndarray, sig_par: float = 4.0, sig_perp: float = 1.2, half: int = 9, nang: int = 8) -> np.ndarray:
    from scipy.ndimage import convolve
    m = np.zeros_like(p)
    yy, xx = np.mgrid[-half:half+1, -half:half+1].astype(np.float32)
    for i in range(nang):
        th = np.pi * i / nang
        u = xx * np.cos(th) + yy * np.sin(th)
        v = -xx * np.sin(th) + yy * np.cos(th)
        k = np.exp(-(u*u/(2*sig_par**2) + v*v/(2*sig_perp**2)))
        k -= k.mean()
        k /= (np.abs(k).sum() + 1e-9)
        np.maximum(m, convolve(p, k.astype(np.float32), mode="constant"), out=m)
    np.clip(m, 0.0, None, out=m)
    return m


def build_posterior(stack: dict, catalogue: np.ndarray, allowed: np.ndarray,
                    prior: float, footprint: np.ndarray, suppress_px: int = 0) -> np.ndarray:
    names = list(stack)
    pos = np.asarray(catalogue, bool)
    dcat = ndi.distance_transform_edt(~pos).astype(np.float32)
    neg_pool = np.asarray(allowed, bool) & (dcat > COLLAR_PX)
    rng = np.random.default_rng(7)
    py, px = np.nonzero(pos)
    ny, nx = np.nonzero(neg_pool)
    n_neg = 50_000  # Reduced from 300k to save memory
    if ny.size > n_neg:
        sel = rng.choice(ny.size, n_neg, replace=False)
        ny, nx = ny[sel], nx[sel]
    Xp = np.stack([np.asarray(stack[k][py, px], np.float32) for k in names], -1)
    Xn = np.stack([np.asarray(stack[k][ny, nx], np.float32) for k in names], -1)
    X = np.concatenate([Xp, Xn])
    y = np.concatenate([np.ones(len(Xp)), np.zeros(len(Xn))])
    del Xp, Xn
    sc = StandardScaler().fit(X)
    clf = LogisticRegression(C=0.5, class_weight="balanced", max_iter=300).fit(sc.transform(X), y)
    del X, y
    offset = float(np.log(prior / (1.0 - prior)))
    p = np.zeros(allowed.shape, np.float32)
    H, W = p.shape
    for r0 in range(0, H, 256):
        r1 = min(H, r0 + 256)
        block = np.stack([np.asarray(stack[k][r0:r1], np.float32) for k in names], -1)
        z = clf.decision_function(sc.transform(block.reshape(-1, len(names)))) + offset
        p[r0:r1] = (1.0 / (1.0 + np.exp(-z))).reshape(r1 - r0, W)
    import gc
    gc.collect()
    if footprint is not None:
        p[~np.asarray(footprint, bool)] = 0.0
    if suppress_px > 0:
        near = ndi.distance_transform_edt(~pos) <= float(suppress_px)
        p[near] = 0.0
    return p


def main():
    from scripts.protocol_preflight import require_like_for_like
    cert = require_like_for_like()
    print(f"Protocol gate: {cert['status']}")

    t0 = time.time()
    g = load_grid(BRIDGE)
    fp = g.footprint

    # Use only essential features (no GMC to save memory)
    essential_bands = [
        "tc",           # Band 6 - radiometric Total Count
        "iso_grav_anom", # Band 13 - gravity anomaly
        "iso_grav_anom_slope", # Band 5 - gravity gradient
        "geod_dilaterate", # Band 8 - geodetic dilation
        "geod_shearrate",  # Band 7 - geodetic shear
        "rtp",          # Band 2 - reduced-to-pole magnetics
        "tmi_hg",       # Band 3 - TMI horizontal gradient
        "depth_to_base_surf", # Band 15 - basement depth
        "ieq_n100a15",  # Band 16 - seismicity
    ]

    print("Loading essential features...")
    stack = {}
    for name in essential_bands:
        cache_path = CACHE / f"{name}.npy"
        if cache_path.is_file():
            stack[name] = np.load(cache_path, mmap_mode="r")
        else:
            a = read_band(FEATURES_TIF, name)
            stack[name] = rank_normalize(a, fp).astype(np.float16)
            CACHE.mkdir(parents=True, exist_ok=True)
            np.save(cache_path, stack[name])
        print(f"  {name}: {stack[name].shape}")

    # Catalogue geometry features
    print("Building geometry features...")
    geom = {}
    vis = np.asarray(g.catalogue, bool)
    H, W = vis.shape
    
    # Distance to visible faults
    from scipy.ndimage import distance_transform_edt
    dist, indices = distance_transform_edt(~vis, return_indices=True)
    iy = indices[0].astype(np.int32); ix = indices[1].astype(np.int32)
    geom["d_vis"] = rank_normalize(dist.astype(np.float32), fp).astype(np.float16)
    
    # Tip continuation (simplified)
    deg = ndi.convolve(vis.astype(np.int16), np.ones((3, 3), np.int16), mode="constant") - vis
    tips = vis & (deg <= 1)
    if not tips.any():
        tips = vis.copy()
    d_tip, tip_indices = distance_transform_edt(~tips, return_indices=True)
    tiy = tip_indices[0].astype(np.int32); tix = tip_indices[1].astype(np.int32)
    
    # Local strike from visible faults
    from gems57 import network
    strike, coh = network.local_strike(vis, smooth_px=3.0)
    th = np.radians(np.where(np.isfinite(strike), strike, 0.0))
    ur, uc = -np.cos(th), np.sin(th)
    
    dy = (iy - np.arange(H, dtype=np.int32)[:, None]).astype(np.float32)
    dx = (ix - np.arange(W, dtype=np.int32)[None, :]).astype(np.float32)
    d_par = np.abs(dy * ur + dx * uc)
    d_perp = np.abs(-dx * ur + dy * uc)
    
    t_strike, t_coh = network.local_strike(tips, smooth_px=6.0)
    tth = np.radians(np.where(np.isfinite(t_strike), t_strike, 0.0))
    tur, tuc = -np.cos(tth), np.sin(tth)
    ty = (tiy - np.arange(H, dtype=np.int32)[:, None]).astype(np.float32)
    tx = (tix - np.arange(W, dtype=np.int32)[None, :]).astype(np.float32)
    t_par = np.abs(ty * tur + tx * tuc)
    t_perp = np.abs(-tx * tur + ty * tuc)
    
    cont = np.exp(-t_perp / 2.5) * np.exp(-np.maximum(t_par - 2.0, 0.0) / 30.0)
    geom["tip_continuation"] = rank_normalize(cont.astype(np.float32), fp).astype(np.float16)
    geom["trace_coh"] = rank_normalize(coh.astype(np.float32), fp).astype(np.float16)
    
    # Trace continuation
    near_cont = np.exp(-d_perp / 2.5) * np.exp(-np.maximum(d_par - 3.0, 0.0) / 40.0)
    geom["trace_continuation"] = rank_normalize(near_cont.astype(np.float32), fp).astype(np.float16)
    
    print(f"Geometry features: {list(geom.keys())}")
    stack.update(geom)

    allowed = fp & ~ndi.binary_dilation(g.catalogue, iterations=COLLAR_PX)
    prior_val = K_PRIOR / float(allowed.sum())
    print(f"Allowed: {int(allowed.sum())}, Prior: {prior_val:.6f}")

    # Fit posterior
    print("Fitting posterior...")
    p = build_posterior(stack, g.catalogue, allowed, prior=prior_val, footprint=fp)
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
    expected_grid = (fp.shape, g.crs, g.transform)

    # Pre-placement surface
    pre_surf = np.clip(sharp, 0.0, 1.0).astype(np.float32)
    pre_surf[g.catalogue | ~fp] = 0.0
    
    surf_rep = U.compare_array_to_registry(
        pre_surf, registry_index, fp,
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
        pred, registry_index, fp,
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
    dots_two_phase = U.two_phase_summary(dots_rep["rows"], int(fp.sum()), expected_rasters=len(records))

    surf_unique = surf_summary["unique"]
    dots_unique = dots_summary["unique"]
    print(f"Surface unique: {surf_unique}, Dots unique: {dots_unique}")
    print(f"Surface worst rho: {surf_summary['worst_spearman_full_footprint']:.4f}")
    print(f"Dots worst overlap: {dots_summary['worst_dot_overlap']:.4f}")

    # Write submission
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(pred.tobytes()).hexdigest()[:8]
    name = f"gems86-minimal-{int(dots.sum())}d-{stamp}-{digest}-zeros"
    note = f"GEMSDOE86 minimal: key geophysics + catalogue geometry; {int(dots.sum())} dots; EPSG:32611"
    assert len(note) <= 140

    out = ROOT / "docs" / "downloads" / f"{name}.tif"
    receipt = write_submission(out, pred, BRIDGE / "sample_submission.tif", fp,
                               note=note, name=name, catalogue=g.catalogue,
                               metadata=dict(lane="gems86-minimal",
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
        "lane_id": "MINIMAL-GEOPHYS-GEOM",
        "ok_to_download_and_submit": bool(receipt["validator"]["all_checks_passed"] and surf_unique and dots_unique),
        "verdict": "promote" if (receipt["validator"]["all_checks_passed"] and surf_unique and dots_unique) else "negative",
        "experiments_executed": 1,
        "elapsed_wall_seconds": round(time.time() - t0, 2),
        "weekly_submission_slots_used": 0,
        "hypothesis": "Key geophysical signatures (TC, gravity, geodesy, magnetics) combined with catalogue trace geometry predict hidden fault continuations.",
        "mechanism": "9 key competition bands + 3 catalogue geometry features -> L2 logistic regression -> anisotropic line filter -> decimated ranking emission.",
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

    (ROOT / "run_card_minimal.json").write_text(json.dumps(run_card, indent=2) + "\n")
    print("=" * 76)
    print(f"VERDICT: {run_card['verdict'].upper()} | OK_TO_SUBMIT={run_card['ok_to_download_and_submit']}")
    print(f"Artifact: {out}")
    print("=" * 76)


if __name__ == "__main__":
    main()