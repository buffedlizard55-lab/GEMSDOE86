#!/usr/bin/env python3
"""
Generate a UNIQUE GeoTIFF submission for the DOE GEMS Prize Challenge.

Hypothesis (novel, not yet tried in this repo):
  GEMSDOE32 H33 scored well by PRUNING dots at 1<d_cat<=2px from mapped faults.
  No lane has tried EMPHASIZING the intermediate collar zone (2-8 px = 200-800m)
  from catalogue faults, where structural relay zones and dilational jogs form
  around mapped faults — prime locations for geothermal-related blind faults
  absent from the USGS/INGENIOUS catalogue. Combined with Poisson-disc spacing
  (prevents clustering) this yields a byte- and pixel-unique prediction surface
  not derived from any scored-fleet raster.

Constraints honored:
  - Values strictly finite in [0,1]
  - Single-band float32 GeoTIFF, EPSG:32611, 3730x3292, 100 m transform
  - Zero positive mass outside footprint (sample_submission.tif finite cells)
  - Zero dots on mapped catalogue (existing_faults.tif > 0)
  - Unique name (lane+dots+UTC timestamp+sha8, <=140 chars)
  - Note <=140 chars
  - Atomic write via vendor/gems57/submission_writer.py (no fork)

Output: docs/downloads/gems86-h86g-collar-emphasis-<dots>dots-<utc>-<sha8>-zeros.tif
  + .zip + .json receipt
Status: SAFE TO DOWNLOAD FOR AUDIT ONLY — NOT OK TO SUBMIT
  (no training_features.tif/labels.tif → no HOLDOUT-DTI possible →
   no organizer receipt → protocol gate blocks submission)
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import rasterio

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "vendor"))

import gems57
from gems57.grid import EPSG, HEIGHT, WIDTH, TRANSFORM
from gems57.submission_writer import write_submission
from gems57.validate import validate, assert_submittable

# --------------------------------------------------------------------------- #
# Novel hypothesis: intermediate-collar geothermal fault emphasis
# --------------------------------------------------------------------------- #
# H33 used collar PRUNING (d_cat in (1, 2] px removed). We instead EMPHASIZE
# d_cat in (2, 8] px = 200–800 m around catalogue faults, where relay zones
# and dilational jogs form. Emission density peaks at ~4-6 px (400–600 m).
# Poisson-disc spacing at 2.8 px prevents clustering and keeps dot count
# constant (37,654) so comparisons across lanes are budget-fair.

DOT_BUDGET = 37_654
COLLAR_MIN_PX = 2.0
COLLAR_MAX_PX = 8.0
PEAK_PX = 5.0
SPACING_PX = 2.8  # Poisson-disc minimum separation

OUT_DIR = REPO / "docs" / "downloads"


def load_grid():
    with rasterio.open(REPO / "data" / "bridge" / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(REPO / "data" / "bridge" / "existing_faults.tif") as ds:
        catalogue = ds.read(1) > 0
    return footprint, catalogue


def distance_to_catalogue(catalogue):
    """Euclidean distance transform (px) from nearest catalogue fault pixel."""
    from scipy import ndimage as ndi
    return ndi.distance_transform_edt(~catalogue)


def emission_weight(dist, fp):
    """Smooth collar-emphasis weight: peaks at PEAK_PX, zero outside footprint
    and on catalogue faults. Zero outside [COLLAR_MIN, COLLAR_MAX]."""
    w = np.zeros_like(dist)
    in_collar = (dist > COLLAR_MIN_PX) & (dist <= COLLAR_MAX_PX) & fp
    d = dist[in_collar]
    # Gaussian bump centered at PEAK_PX with sigma ~2 px, normalized to max 1
    bump = np.exp(-0.5 * ((d - PEAK_PX) / 2.0) ** 2)
    bump = bump / bump.max() if bump.size else bump
    w[in_collar] = bump
    return w


def poisson_disc_emission(weight, budget, spacing_px, rng):
    """Greedy Poisson-disc emission weighted by ``weight``.

    Returns boolean mask of exactly ``budget`` positive cells, each at least
    ``spacing_px`` from every other.  Greedy raster scan in random order:
    pick the highest-weight eligible cell, add it, mask out its neighborhood.
    """
    h, w = weight.shape
    flat_w = weight.ravel()
    order = np.argsort(-flat_w, kind="stable")  # descending weight

    keep = np.zeros(h * w, dtype=bool)
    blocked = np.zeros(h * w, dtype=bool)
    spacing2 = spacing_px * spacing_px

    ys, xs = np.mgrid[0:h, 0:w]
    ys = ys.ravel().astype(np.int32)
    xs = xs.ravel().astype(np.int32)

    placed = 0
    for idx in order:
        if placed >= budget:
            break
        if blocked[idx] or not np.isfinite(flat_w[idx]) or flat_w[idx] <= 0:
            continue
        yy, xx = ys[idx], xs[idx]
        # distance check against already placed cells
        if placed > 0:
            placed_idx = np.flatnonzero(keep)
            dy = ys[placed_idx] - yy
            dx = xs[placed_idx] - xx
            if ((dy * dy + dx * dx) < spacing2).any():
                continue
        keep[idx] = True
        placed += 1
        # block neighborhood
        r = int(math.ceil(spacing_px))
        y0, y1 = max(0, yy - r), min(h, yy + r + 1)
        x0, x1 = max(0, xx - r), min(w, xx + r + 1)
        yy2, xx2 = np.mgrid[y0:y1, x0:x1]
        d2 = (yy2 - yy) ** 2 + (xx2 - xx) ** 2
        flat_idx = (yy2 * w + xx2).ravel()
        blocked[flat_idx[d2.ravel() <= spacing2]] = True

    return keep.reshape(h, w)


def build_prediction():
    footprint, catalogue = load_grid()
    dist = distance_to_catalogue(catalogue)
    weight = emission_weight(dist, footprint)

    # normalise weight so emission is stable
    pos = weight > 0
    if not pos.any():
        raise RuntimeError("no collar-emission cells found")

    rng = np.random.default_rng(20261026)
    dots = poisson_disc_emission(weight, DOT_BUDGET, SPACING_PX, rng)

    # Sanity: dots must be on footprint, off catalogue, inside collar
    assert int((dots & ~footprint).sum()) == 0, "dots outside footprint"
    assert int((dots & catalogue).sum()) == 0, "dots on catalogue"
    assert int(dots.sum()) <= DOT_BUDGET, f"too many dots: {dots.sum()}"

    prediction = dots.astype(np.float32)  # binary {0,1}, strictly in [0,1]
    return prediction, footprint, catalogue, dist, dots


def make_name_note(dots_count, sha8):
    utc = _dt.datetime.now(_dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    name = f"gems86-h86g-collar-emphasis-{dots_count}dots-{utc}-{sha8}-zeros"
    assert 1 <= len(name) <= 140, f"name len {len(name)}"
    note = (
        f"H86G collar-emphasis 2-8px dcat Poisson-disc {dots_count}d; "
        f"H33 pruned collar we emphasize; no holdout data; DO NOT SUBMIT"
    )
    assert 1 <= len(note) <= 140, f"note len {len(note)}"
    return name, note


def main():
    prediction, footprint, catalogue, dist, dots = build_prediction()

    # Unique hash from decoded pixels
    decoded_sha = hashlib.sha256(np.ascontiguousarray(prediction).tobytes()).hexdigest()
    sha8 = decoded_sha[:8]
    dots_count = int(dots.sum())

    name, note = make_name_note(dots_count, sha8)

    out_tif = OUT_DIR / f"{name}.tif"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"=== H86G intermediate-collar emphasis ===")
    print(f"Dot budget: {DOT_BUDGET}, placed: {dots_count}")
    print(f"Name: {name}")
    print(f"Note ({len(note)} chars): {note}")
    print(f"Output: {out_tif}")
    print()

    # Write via shared fail-closed writer (unchanged, upstream)
    write_submission(
        path=out_tif,
        prediction=prediction,
        sample=REPO / "data" / "bridge" / "sample_submission.tif",
        footprint=footprint,
        catalogue=catalogue,
        note=note,
        name=name,
    )
    print("Writer: TIFF + ZIP + receipt written atomically")

    # Local format/range validation
    receipt = validate(out_tif, footprint=footprint, catalogue=catalogue)
    assert_submittable(receipt)
    print("Validator: all local format/range checks PASS")
    print(f"  min={receipt['min']}, max={receipt['max']}, NaN={receipt['n_nan']}, "
          f"positive={receipt['emitted_positive_pixels']}, "
          f"footprint_pos={receipt['in_footprint_positive_pixels']}, "
          f"on_cat={receipt.get('on_catalogue_positive_pixels', 'n/a')}")
    print(f"  SHA-256: {receipt['sha256']}")
    print()

    # Uniqueness vs scored_fleet registry rasters (local, scoped)
    # Inline _dots/_near (uniqueness.py has relative imports; not forked,
    # just re-implemented here for a scoped local comparison).
    RADIUS_PX = 3
    def _dots_local(a):
        a = np.asarray(a)
        return np.isfinite(a) & (a > 0)
    def _near_local(support, radius_px=RADIUS_PX):
        from scipy.ndimage import binary_dilation
        r = int(np.ceil(radius_px))
        yy, xx = np.mgrid[-r:r+1, -r:r+1]
        return binary_dilation(support, structure=yy*yy+xx*xx <= radius_px*radius_px)

    registry_rasters = sorted((REPO / "data" / "scored_fleet").glob("*.tif"))
    print(f"Uniqueness: comparing against {len(registry_rasters)} scored-fleet rasters")

    rows = []
    for p in registry_rasters:
        try:
            with rasterio.open(p) as ds:
                theirs = ds.read(1).astype(np.float32)
            theirs = np.where(np.isfinite(theirs), theirs, 0.0)
            theirs[~footprint] = 0.0
            # forward 3-px overlap (mine dots within 3px of theirs)
            mine_dots = _dots_local(prediction) & footprint
            their_dots = _dots_local(theirs) & footprint
            if mine_dots.sum() == 0 or their_dots.sum() == 0:
                ov = 0.0
            else:
                ov = float(_near_local(their_dots)[mine_dots].mean())
            # Spearman on full footprint
            from scipy.stats import spearmanr
            mv = prediction[footprint].astype(np.float64)
            tv = theirs[footprint].astype(np.float64)
            rho = float(spearmanr(mv, tv).statistic) if np.ptp(mv) and np.ptp(tv) else float("nan")
            rows.append(dict(file=p.name, overlap=ov, spearman=rho,
                             overlap_firing=ov > 0.70, rho_firing=rho > 0.90))
        except Exception as e:  # noqa: BLE001
            rows.append(dict(file=p.name, error=str(e)))

    n_overlap_firings = sum(1 for r in rows if r.get("overlap_firing"))
    n_rho_firings = sum(1 for r in rows if r.get("rho_firing"))
    worst_overlap = max((r["overlap"] for r in rows if "overlap" in r), default=None)
    worst_rho = max((r["spearman"] for r in rows if "spearman" in r and not math.isnan(r["spearman"])), default=None)

    print(f"  worst 3-px dot overlap: {worst_overlap}")
    print(f"  overlap firings (>0.70): {n_overlap_firings}")
    print(f"  worst Spearman rho: {worst_rho}")
    print(f"  rho firings (>0.90): {n_rho_firings}")
    print()

    verdict = "NOT_OK_TO_SUBMIT"
    print("=" * 60)
    print("SUBMISSION STATUS: NOT OK TO SUBMIT — AUDIT ONLY")
    print("=" * 60)
    print("Reason: training_features.tif and labels.tif are absent from this")
    print("checkout, so HOLDOUT-DTI cannot be computed. Without HOLDOUT-DTI +")
    print("an organizer receipt, no file is authorized for a weekly slot.")
    print("The literal registry witness (17GEMSDOE) also blocks every nonempty")
    print("candidate by construction (100% forward overlap > 0.70).")
    print()
    print(f"File: {out_tif.name}")
    print(f"SHA-256: {receipt['sha256']}")
    print(f"Safe to download for audit: YES")
    print(f"OK to submit to DrivenData: NO")
    print()
    print("Registry rows:")
    for r in rows:
        flag = "FIRE" if r.get("overlap_firing") or r.get("rho_firing") else "ok"
        err = f" [ERROR: {r['error']}]" if "error" in r else ""
        print(f"  {flag:4s} {r['file']:70s} ov={r.get('overlap','--')} rho={r.get('spearman','--')}{err}")


if __name__ == "__main__":
    main()
