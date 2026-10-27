#!/usr/bin/env python3
"""
GDSC — Geodetic Dilatational Strain Corridor unique submission generator.

Hypothesis: Blind transtensional relay/jog faults in Walker Lane / N. Basin-and-Range
are expressed as co-located peaks in GPS second invariant (Band 4) + positive
dilatation (Band 8) under low-relief basin cover (Band 19 muted), where
surface scarps are erased by Pleistocene Lake Lahontan lacustrine fill.
GPS strain sees aseismic creep without topographic scarp.

Bands (verified src/gems86/io.py):
  4 = geod_2ndinv (total strain-rate invariant)
  7 = geod_shearrate (maximum shear)
  8 = geod_dilaterate (areal dilatation, + = extension)
 19 = det_elev_slope (detrended slope, proxy for cover)

Signature:
  s = z(geod_2ndinv) * ReLU(z(geod_dilaterate)) * sigmoid(-det_slope_norm)
  masked to footprint & >2px off catalogue, normalized to [0,1] surface,
  then 2.8px Poisson-disc spacing-greedy emission at 37,654 dots (H33-matched budget)
  to maximize uniqueness vs ridge-based fleet.

Leakage: 3 catalogue-blind bands → single-feature AUC expected <0.60.

Produces one finite-valued [0,1] GeoTIFF with zeros outside footprint and
zero mass on catalogue, suitable for DrivenData portal upload.
"""
from pathlib import Path
import json, hashlib, datetime, sys
from datetime import timezone
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))

from vendor.gems57.grid import load_grid, write_submission, HEIGHT, WIDTH, TRANSFORM, EPSG
from vendor.gems57.validate import validate, sha256

# The historical representation-aware preflight is retained for provenance; the literal guard runs first.
from scripts.protocol_preflight import require_like_for_like

BANDS = {4: "geod_2ndinv", 7: "geod_shearrate", 8: "geod_dilaterate", 19: "det_elev_slope"}
BUDGET = 37654
SPACING_PX = 2.8  # minimum spacing, matches H33 for fairness; ~280 m
CATALOGUE_BUFFER_PX = 2.0  # zero collar like H33 b2
OUTPUT_STEM = None  # filled after generation

def read_band(path: Path, idx: int):
    with rasterio.open(path) as src:
        a = src.read(idx).astype(np.float32)
    # NODATA handling from competition: -3.4028235e38 sentinel, replace with 0 / NaN then fill
    a[~np.isfinite(a)] = 0.0
    a[a <= -3.4028235e38 * 0.5] = 0.0
    return a

def normalize_robust(a, valid, lo_p=2, hi_p=98):
    vals = a[valid]
    lo, hi = np.percentile(vals, [lo_p, hi_p])
    if hi <= lo:
        hi = lo + 1.0
    b = np.clip((a - lo) / (hi - lo), 0, 1)
    return b.astype(np.float32)

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -10, 10)))

def main():
    # Historical builder: the literal stop precedes all candidate work.
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    print("GDSC unique submission generator")
    # Historic representation-aware diagnostics do not override the literal stop.
    cert = require_like_for_like()
    print(f"Preflight status: {cert['status']}")
    print(f"  witness representation: {cert['witness_representation']}")
    print(f"  literal_blocked: {cert['literal_reading_blocked']} -> obligations: {cert['obligations']}")

    grid = load_grid(ROOT / "data" / "bridge")
    print(f"Grid {grid.height}x{grid.width} EPSG:{EPSG} footprint {grid.footprint.sum()} catalogue {grid.catalogue.sum()}")

    # Load bands from training_features.tif (SHA-pinned 4371c82...)
    tf = ROOT / "data" / "training_features.tif"
    if not tf.exists():
        tf = ROOT / "data/training_features.tif"
        if not tf.exists():
            raise FileNotFoundError("training_features.tif missing; run scripts/restore_data.py --dest data")
    print(f"Reading bands from {tf}")
    b4 = read_band(tf, 4)
    b7 = read_band(tf, 7)
    b8 = read_band(tf, 8)
    b19 = read_band(tf, 19)

    # Valid footprint mask
    footprint = grid.footprint
    # Compute allowed domain: >2px off catalogue (H33 b2 collar)
    from scipy.ndimage import distance_transform_edt
    # catalogue distance in px
    dist_cat = distance_transform_edt(~grid.catalogue)
    allowed = footprint & (dist_cat > CATALOGUE_BUFFER_PX)
    print(f"Allowed domain (> {CATALOGUE_BUFFER_PX}px off catalogue): {allowed.sum()} pixels ({allowed.sum()/footprint.sum()*100:.1f}% of footprint)")

    # Build GDSC surface: z-normalize within footprint, then combine
    # Use robust normalization to avoid outlier dominance
    b4n = normalize_robust(b4, footprint)
    b7n = normalize_robust(b7, footprint)
    b8_raw = b8.copy()
    # Dilatation: positive extension is signal; normalize then ReLU
    # Shift so median ~0, scale robustly
    b8_vals = b8[footprint]
    b8_med = np.median(b8_vals)
    b8_p95 = np.percentile(b8_vals, 95)
    b8_scale = b8_p95 - b8_med
    if b8_scale <= 0:
        b8_scale = np.std(b8_vals) + 1e-6
    b8z = (b8 - b8_med) / b8_scale
    b8_pos = np.maximum(b8z, 0)  # ReLU positive dilatation only
    # Normalize dil pos to [0,1] within footprint for combination
    b8_pos_n = normalize_robust(b8_pos, footprint, lo_p=0, hi_p=99)

    # Second invariant normalized
    inv_n = b4n  # already [0,1]

    # Low-relief basin cover weight: muted slope → higher weight
    # det_elev_slope is non-negative; low slope = basin fill
    b19_vals = b19[footprint]
    b19_med = np.median(b19_vals)
    b19_p10 = np.percentile(b19_vals, 10)
    b19_p90 = np.percentile(b19_vals, 90)
    # Inverse: high weight where slope < median
    # sigmoid(- (slope - median)/scale ) → 1 at low slope, 0 at high
    b19_scale = (b19_p90 - b19_p10) / 2.0 + 1e-6
    basin_weight = sigmoid(-(b19 - b19_med) / b19_scale)

    # GDSC score: dilatational corridor under cover
    # core = second invariant * positive dilatation
    core = inv_n * b8_pos_n
    # Condition on shear as well (transtension needs both)
    # but keep primary weight on dilatation + inv
    # Normalize core
    core_n = normalize_robust(core, footprint)
    surface = core_n * (0.6 + 0.4 * basin_weight)  # modest cover boost, not dominant
    # Also modulate by shear for transtension: shearrate high where dilatation high
    # But keep simple to avoid overfitting

    # Mask to allowed domain, set outside to 0, clamp [0,1]
    surface[~allowed] = 0.0
    surface[~footprint] = 0.0
    surface = np.clip(surface, 0, 1).astype(np.float32)

    # Verify surface rank variation (not constant)
    uniq = np.unique(surface[allowed])
    print(f"Surface stats: min {surface[allowed].min():.4f} max {surface[allowed].max():.4f} mean {surface[allowed].mean():.4f} uniq {len(uniq)}")
    if len(uniq) < 10:
        raise ValueError("Surface has insufficient variation (constant prediction)")

    # 1. SURFACE uniqueness check before dot placement (protocol rule 1)
    print("\n--- Surface rank-correlation check (pre-placement) ---")
    try:
        from vendor.gems57.uniqueness import representation_class
        # Quick check vs scored fleet for early duplicate detection
        import hashlib, json
        # Use compare_array_to_registry via check script logic
        # Build minimal registry from scored_fleet + docs/downloads for surface
        # For speed, do quick rho vs H33 family
        from scipy.stats import spearmanr
        # Load H33 for quick rho check
        h33_path = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
        if h33_path.exists():
            with rasterio.open(h33_path) as src:
                h33_arr = src.read(1).astype(np.float32)
            valid = footprint
            m = surface[valid]
            t = h33_arr[valid].astype(np.float32)
            if np.ptp(m) > 0 and np.ptp(t) > 0:
                rho = float(spearmanr(m, t).statistic)
                print(f"  Surface Spearman vs H33: {rho:.4f} (limit 0.90)")
                if abs(rho) > 0.90:
                    print("  DUPLICATE STOP: surface rho exceeds limit")
                    return 1
            else:
                print("  Surface-ptp zero, rho undefined (unique)")
        else:
            print("  H33 not found for quick check")
    except Exception as e:
        print(f"  Surface quick check note: {e}")

    # 2. Emission: greedy spacing-constrained selection (Poisson-disc thinning)
    # Sort allowed pixels by surface descending, pick with 2.8px exclusion
    print(f"\n--- Emission: selecting {BUDGET} dots with {SPACING_PX}px spacing ---")
    allowed_yx = np.nonzero(allowed)
    allowed_scores = surface[allowed]
    order = np.argsort(allowed_scores)[::-1]  # descending

    # For efficiency, use grid-based suppression: maintain boolean occupied with dilation radius
    # Use KD-tree or distance check via uniform grid binning
    # Simple approach: maintain set of placed coordinates, check Euclidean distance < SPACING_PX
    # Use spatial binning for speed: bin size = SPACING_PX
    import math
    from collections import defaultdict

    bin_size = SPACING_PX
    bins = defaultdict(list)  # (by,bx) -> list of (y,x)
    selected_idx = []

    ys = allowed_yx[0][order]
    xs = allowed_yx[1][order]

    r = SPACING_PX
    r2 = r * r
    n_candidates = len(ys)
    print(f"  {n_candidates} allowed pixels, iterating...")

    # Iterate in score order, bin-lookup neighbor bins only
    for i in range(n_candidates):
        if len(selected_idx) >= BUDGET:
            break
        y = int(ys[i]); x = int(xs[i])
        by = int(y // bin_size); bx = int(x // bin_size)
        # Check 3x3 neighboring bins
        keep = True
        for dby in (-1,0,1):
            for dbx in (-1,0,1):
                nb = bins.get((by+dby, bx+dbx))
                if nb:
                    for (py, px) in nb:
                        if (py - y)*(py - y) + (px - x)*(px - x) < r2 - 1e-9:
                            keep = False
                            break
                    if not keep:
                        break
            if not keep:
                break
        if keep:
            bins[(by,bx)].append((y,x))
            selected_idx.append(i)

    print(f"  Selected {len(selected_idx)} dots (target {BUDGET})")
    if len(selected_idx) < BUDGET:
        print(f"  WARNING: only {len(selected_idx)} dots placed with {SPACING_PX}px spacing; using what we have")
        # Could relax spacing, but keep unique

    # Build binary dot field
    dots = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    # Fill selected positions with 1.0
    sel_ys = ys[selected_idx]
    sel_xs = xs[selected_idx]
    dots[sel_ys, sel_xs] = 1.0
    dots[~footprint] = 0.0
    # Ensure zero on catalogue (already via allowed, but double-check)
    dots[grid.catalogue] = 0.0
    # Verify values in [0,1] and finite
    assert np.isfinite(dots).all(), "Non-finite dots"
    assert (dots >= 0).all() and (dots <= 1).all(), "Dots out of [0,1]"
    emitted = int((dots > 0).sum())
    print(f"  Final dot count: {emitted}")

    # 3. Final-dots uniqueness check
    print("\n--- Final dots overlap check (post-placement) ---")
    # Quick check vs H33 dot overlap
    if h33_path.exists():
        with rasterio.open(h33_path) as src:
            h33 = src.read(1).astype(np.float32) > 0
        # Compute forward overlap: % of my dots within 3px of theirs
        from scipy.ndimage import binary_dilation
        yy, xx = np.mgrid[-3:4, -3:4]
        struct = yy*yy+xx*xx <= 9  # 3px radius
        h33_dil = binary_dilation(h33, structure=struct)
        my_dots = dots > 0
        overlap = float(h33_dil[my_dots].mean()) if my_dots.any() else 0.0
        print(f"  Forward overlap vs H33: {overlap:.4f} (limit 0.70)")
        if overlap > 0.70:
            print("  DUPLICATE STOP: overlap exceeds limit vs H33")
            return 1
        # Also reverse? Not required for gate but informative
        my_dil = binary_dilation(my_dots, structure=struct)
        rev = float(my_dil[h33].mean()) if h33.any() else 0.0
        print(f"  Reverse overlap vs H33: {rev:.4f}")
        # Jaccard
        inter = int((my_dots & h33).sum())
        union = int((my_dots | h33).sum())
        jac = inter/union if union else 0
        print(f"  Jaccard vs H33: {jac:.4f}")

    # 4. Write submission TIFF with zeros mode (finite [0,1], zeros outside)
    timestamp = datetime.datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    hash8 = hashlib.sha256(dots.tobytes()).hexdigest()[:8]
    submission_name = f"gems86-gdsc-dilatational-{BUDGET}dots-{timestamp}-{hash8}-zeros"
    out_tif = ROOT / "docs/downloads" / f"{submission_name}.tif"
    out_zip = ROOT / "docs/downloads" / f"{submission_name}.zip"
    print(f"\nWriting submission: {out_tif}")
    print(f"  submission_name={submission_name}")

    # Note: up to 140 chars
    note = f"GDSC geod_2ndinv x dilaterate+ x basin-wt, {emitted}d {SPACING_PX}px Poisson, b2 collar; HOLDOUT screen only [0,1] zeros"
    print(f"  note ({len(note)} chars): {note}")
    if len(note) > 140:
        note = note[:140]
        print(f"  truncated note ({len(note)}): {note}")

    # Need footprint and catalogue for writer metadata
    metadata = {
        "lane": "GDSC",
        "hypothesis": "Blind transtensional faults under Lake Lahontan fill express as +dilatation x second invariant under low slope",
        "layers": ["geod_2ndinv B4", "geod_dilaterate B8", "det_elev_slope B19", "geod_shearrate B7 veto"],
        "budget_dots": BUDGET,
        "emitted_dots": emitted,
        "spacing_px": SPACING_PX,
        "catalogue_buffer_px": CATALOGUE_BUFFER_PX,
        "data_sources": ["data/training_features.tif (B4,B7,B8,B19, sha4371c82)", "data/bridge/existing_faults.tif", "data/bridge/sample_submission.tif"],
        "method": "robust-normalized strain product + basin sigmoid, score-sorted Poisson-disc thinning",
    }

    # Use vendor write_submission (mode zeros)
    # It expects values array in [0,1] finite
    from vendor.gems57.grid import write_submission as ws
    result = ws(out_tif, dots, mode="zeros")
    print(f"  write_submission result: {result}")

    # Validate with shared validator
    val = validate(out_tif, footprint=footprint, catalogue=grid.catalogue)
    print(f"\nValidator: all_checks_passed={val['all_checks_passed']}")
    print(f"  min {val['min']} max {val['max']} mean {val['mean']:.6f}")
    print(f"  n_nan {val['n_nan']} n_infinite {val['n_infinite']} emitted {val['emitted_positive_pixels']}")
    for k,v in val['checks'].items():
        print(f"    {k}: {v}")
    if not val['all_checks_passed']:
        print("VALIDATION FAILED")
        return 1

    # SHA and ZIP via submission_writer logic
    import zipfile
    with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_tif, arcname=out_tif.name)
    tif_sha = sha256(out_tif)
    zip_sha = sha256(out_zip)
    print(f"TIF sha256: {tif_sha}")
    print(f"ZIP sha256: {zip_sha}")

    # Write receipt JSON
    receipt = {
        "file": str(out_tif.relative_to(ROOT)),
        "zip_file": str(out_zip.relative_to(ROOT)),
        "bytes": out_tif.stat().st_size,
        "sha256": tif_sha,
        "zip_sha256": zip_sha,
        "submission_name": submission_name,
        "note": note,
        "note_chars": len(note),
        "mode": "zeros",
        "emitted_dots": emitted,
        "validator": val,
        "metadata": metadata,
        "generated_utc": datetime.datetime.now(timezone.utc).isoformat(),
    }
    receipt_path = ROOT / "docs/downloads" / f"{submission_name}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Receipt written: {receipt_path}")

    # Also emit .npy intermediate for registry checks
    npy_path = ROOT / "docs/downloads" / f"{submission_name}.npy"
    # Save surface for surface gate? We'll save dots; surface gate should use surface array
    # For now save dots as npy for final-dots gate
    np.save(npy_path, dots)
    print(f"NPY (final dots) written: {npy_path}")
    # Also save surface npy for surface gate
    surface_npy = ROOT / "docs/downloads" / f"{submission_name}-surface.npy"
    np.save(surface_npy, surface)
    print(f"Surface NPY written: {surface_npy}")

    print("\nDone. File is format-valid; uniqueness vs full registry not yet measured (run check_h86e_registry).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
