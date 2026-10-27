#!/usr/bin/env python3
"""
Build a UNIQUE GeoTIFF submission for the DOE GEMS Prize Challenge.

Novel hypothesis (experiment 2; not shipped in this repo):
  Geothermal blind faults concentrate where (a) a structural boundary exists
  (gravity-gradient magnitude, band 5) AND (b) hydrothermal radiometric
  alteration is present (airborne Total Count / potassium, band 6) AND (c) the
  site lies in the intermediate collar (2-8 px = 200-800 m) of a mapped
  catalogue fault where relay zones / dilational jogs host strands ABSENT from
  the USGS/INGENIOUS catalogue.
  Dots are POISSON-DISC placed weighted by this geothermal prospectivity
  index, concentrated in high-signal collar cells rather than spread across the
  whole collar.  This is physically grounded in geothermal discovery (blind
  fault-hosted upflow zones) and differs from H33's pure collar-pruning and
  from broad poisson fields.

Constraints honored:
  - Values strictly finite in [0, 1]; single-band float32 GeoTIFF
  - EPSG:32611, 3730x3292, 100 m transform, matches sample_submission.tif
  - Zero positive mass outside footprint; zero dots on mapped catalogue
  - Unique name (<=140 chars); note <= 140 chars
  - Atomic fail-closed write via vendor/gems57/submission_writer.py (shared)

Output: docs/downloads/gems86-geothermal-prospectivity-<dots>dots-<utc>-<sha8>-zeros.tif
  + .zip + .json receipt

Status: FORMAT-VALID (local preflight) / NOT authorized for a weekly slot
  (no HOLDOUT-DTI: protocol blocks require_feasible; no organizer receipt;
   uniqueness verified only against locally available scored_fleet rasters).
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
sys.path.insert(0, str(REPO))

from gems57.submission_writer import write_submission
from gems57.validate import validate, assert_submittable
from src.gems86.io import read_band, BAND_PHYSICS_VERIFIED  # noqa: F401

FEATURES_TIF = REPO / "data" / "training_features.tif"
DOT_BUDGET = 37_654
COLLAR_MIN_PX = 2.0
COLLAR_MAX_PX = 8.0
SPACING_PX = 2.8  # Poisson-disc minimum separation
OUT_DIR = REPO / "docs" / "downloads"


def robust_scale(a, foot):
    """0-1 robust scale over footprint using 2nd-98th percentiles."""
    v = a[foot]
    v = v[np.isfinite(v)]
    if v.size == 0:
        return np.zeros_like(a)
    lo, hi = np.percentile(v, 2), np.percentile(v, 98)
    if hi <= lo:
        return np.zeros_like(a)
    out = np.clip((a - lo) / (hi - lo), 0.0, 1.0)
    out[~foot] = 0.0
    return out


def load_grid():
    with rasterio.open(REPO / "data" / "bridge" / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(REPO / "data" / "bridge" / "existing_faults.tif") as ds:
        catalogue = ds.read(1) > 0
    return footprint, catalogue


def build_prospectivity(footprint, catalogue):
    # Band 5 = iso_grav_anom_slope (scalar 2-D horizontal gravity gradient magnitude)
    # Band 6 = tc (GeoDAWN airborne radiometric Total Count; K-bearing alteration proxy)
    b5 = read_band(FEATURES_TIF, 5)
    b6 = read_band(FEATURES_TIF, 6)
    s5 = robust_scale(b5, footprint)
    s6 = robust_scale(b6, footprint)
    del b5, b6

    from scipy import ndimage as ndi

    dist = ndi.distance_transform_edt(~catalogue)
    collar = (dist > COLLAR_MIN_PX) & (dist <= COLLAR_MAX_PX) & footprint

    # Prospectivity: structural boundary x radiometric alteration, inside collar only.
    # Damp far-from-fault and on-fault cells so dots cluster at blind-strand sites.
    pros = s5 * s6 * collar.astype(np.float64)
    return pros, dist, collar


def poisson_disc_emission(weight, budget, spacing_px, rng):
    h, wgt = weight.shape
    flat_w = weight.ravel()
    order = np.argsort(-flat_w, kind="stable")
    keep = np.zeros(h * wgt, dtype=bool)
    blocked = np.zeros(h * wgt, dtype=bool)
    spacing2 = spacing_px * spacing_px
    ys, xs = np.mgrid[0:h, 0:wgt]
    ys = ys.ravel().astype(np.int32)
    xs = xs.ravel().astype(np.int32)
    placed = 0
    for idx in order:
        if placed >= budget:
            break
        if blocked[idx] or not np.isfinite(flat_w[idx]) or flat_w[idx] <= 0:
            continue
        yy, xx = ys[idx], xs[idx]
        if placed > 0:
            placed_idx = np.flatnonzero(keep)
            dy = ys[placed_idx] - yy
            dx = xs[placed_idx] - xx
            if ((dy * dy + dx * dx) < spacing2).any():
                continue
        keep[idx] = True
        placed += 1
        r = int(math.ceil(spacing_px))
        y0, y1 = max(0, yy - r), min(h, yy + r + 1)
        x0, x1 = max(0, xx - r), min(wgt, xx + r + 1)
        yy2, xx2 = np.mgrid[y0:y1, x0:x1]
        d2 = (yy2 - yy) ** 2 + (xx2 - xx) ** 2
        flat_idx = (yy2 * wgt + xx2).ravel()
        blocked[flat_idx[d2.ravel() <= spacing2]] = True
    return keep.reshape(h, wgt)


def uniqueness_vs_scored_fleet(prediction, footprint):
    from scipy.ndimage import binary_dilation
    from scipy.stats import spearmanr

    RADIUS_PX = 3

    def _dots(a):
        a = np.asarray(a)
        return np.isfinite(a) & (a > 0)

    def _near(support, radius_px=RADIUS_PX):
        r = int(np.ceil(radius_px))
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
        struct = (yy * yy + xx * xx) <= radius_px * radius_px
        return binary_dilation(support, structure=struct)

    registry_rasters = sorted((REPO / "data" / "scored_fleet").glob("*.tif"))
    rows = []
    mine_dots = _dots(prediction) & footprint
    cache = {}
    for p in registry_rasters:
        row = {"file": p.name}
        try:
            with rasterio.open(p) as ds:
                theirs = ds.read(1).astype(np.float32)
            theirs = np.where(np.isfinite(theirs), theirs, 0.0)
            theirs[~footprint] = 0.0
            their_dots = _dots(theirs) & footprint
            if mine_dots.sum() == 0 or their_dots.sum() == 0:
                ov = 0.0
            else:
                if p.name not in cache:
                    cache[p.name] = _near(their_dots)
                ov = float(cache[p.name][mine_dots].mean())
            mv = prediction[footprint].astype(np.float64)
            tv = theirs[footprint].astype(np.float64)
            rho = float(spearmanr(mv, tv).statistic) if (np.ptp(mv) and np.ptp(tv)) else float("nan")
            row.update(
                overlap=ov,
                spearman=rho,
                overlap_firing=ov > 0.70,
                rho_firing=(rho > 0.90) if rho == rho else False,
            )
        except Exception as exc:  # noqa: BLE001
            row["error"] = str(exc)
        rows.append(row)
    n_ov = sum(1 for r in rows if r.get("overlap_firing"))
    n_rho = sum(1 for r in rows if r.get("rho_firing"))
    worst_ov = max((r["overlap"] for r in rows if "overlap" in r), default=None)
    worst_rho = max((r["spearman"] for r in rows if "spearman" in r and r["spearman"] == r["spearman"]), default=None)
    return rows, n_ov, n_rho, worst_ov, worst_rho


def main() -> int:
    footprint, catalogue = load_grid()
    pros, dist, collar = build_prospectivity(footprint, catalogue)
    if not (pros > 0).any():
        raise RuntimeError("no geothermal-prospectivity cells found")

    rng = np.random.default_rng(20261027)
    dots = poisson_disc_emission(pros, DOT_BUDGET, SPACING_PX, rng)

    assert int((dots & ~footprint).sum()) == 0, "dots outside footprint"
    assert int((dots & catalogue).sum()) == 0, "dots on catalogue"
    assert int((dots & ~collar).sum()) == 0, "dots outside collar"
    assert int(dots.sum()) <= DOT_BUDGET, f"too many dots: {dots.sum()}"

    prediction = dots.astype(np.float32)
    decoded_sha = hashlib.sha256(np.ascontiguousarray(prediction).tobytes()).hexdigest()
    sha8 = decoded_sha[:8]
    dots_count = int(dots.sum())
    utc = _dt.datetime.now(_dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    name = f"gems86-geothermal-prospectivity-{dots_count}dots-{utc}-{sha8}-zeros"
    assert 1 <= len(name) <= 140
    note = (
        f"H86 geothermal prospectivity (grav-grad x radiometric TC) 2-8px collar "
        f"{dots_count}d; audit-only, holdout not computed"
    )
    assert 1 <= len(note) <= 140

    out_tif = OUT_DIR / f"{name}.tif"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== GEMSDOE86 geothermal-prospectivity submission ===")
    print(f"Dot budget: {DOT_BUDGET}, placed: {dots_count}")
    print(f"Name: {name}")
    print(f"Note ({len(note)} chars): {note}")
    print(f"Output: {out_tif}")
    print(f"Prospectivity cells: {int((pros>0).sum())}, collar cells: {int(collar.sum())}")

    write_submission(
        path=out_tif,
        prediction=prediction,
        sample=REPO / "data" / "bridge" / "sample_submission.tif",
        footprint=footprint,
        catalogue=catalogue,
        note=note,
        name=name,
    )
    print("Writer: TIFF + one-TIFF ZIP + receipt written atomically")

    receipt = validate(out_tif, footprint=footprint, catalogue=catalogue)
    assert_submittable(receipt)
    print("Validator: all local format/range checks PASS")
    print(f"  min={receipt['min']}, max={receipt['max']}, NaN={receipt['n_nan']}, "
          f"positive={receipt['emitted_positive_pixels']}, on_cat={receipt.get('on_catalogue_positive_pixels')}")
    print(f"  SHA-256: {receipt['sha256']}")

    rows, n_ov, n_rho, worst_ov, worst_rho = uniqueness_vs_scored_fleet(prediction, footprint)
    print(f"Uniqueness: comparing against {len(rows)} scored-fleet rasters")
    print(f"  worst 3-px dot overlap: {worst_ov}  (firings >0.70: {n_ov})")
    print(f"  worst Spearman rho: {worst_rho}  (firings >0.90: {n_rho})")

    print("=" * 60)
    print("SUBMISSION STATUS: FORMAT-VALID / AUDIT ONLY — NOT OK TO SUBMIT")
    print("=" * 60)
    print("No HOLDOUT-DTI (protocol require_feasible blocked; no organizer receipt).")
    print("Safe to download for audit: YES   OK to submit to DrivenData: NO")
    print(f"File: {out_tif.name}  SHA-256: {receipt['sha256']}")
    print("Registry rows:")
    for r in rows:
        flag = "FIRE" if r.get("overlap_firing") or r.get("rho_firing") else "ok"
        err = f" [ERROR: {r.get('error')}]" if "error" in r else ""
        print(f"  {flag:4s} {r['file']:70s} ov={r.get('overlap','--')} rho={r.get('spearman','--')}{err}")

    summary = {
        "schema": "gems86.geothermal-prospectivity-submission.v1",
        "name": name, "note": note, "note_chars": len(note),
        "file": str(out_tif), "sha256": receipt["sha256"], "bytes": receipt["bytes"],
        "dots": dots_count, "budget": DOT_BUDGET,
        "collar_min_px": COLLAR_MIN_PX, "collar_max_px": COLLAR_MAX_PX, "spacing_px": SPACING_PX,
        "format_checks_passed": receipt["all_checks_passed"],
        "min": receipt["min"], "max": receipt["max"], "n_nan": receipt["n_nan"],
        "positive_pixels": receipt["emitted_positive_pixels"],
        "on_catalogue_pixels": receipt.get("on_catalogue_positive_pixels"),
        "holdout_dti": None,
        "holdout_dti_note": "not computable: protocol require_feasible blocked; organizer holdout labels absent; no organizer receipt",
        "ok_to_submit": False, "safe_to_download": True,
        "verdict": "FORMAT_VALID_AUDIT_ONLY_NOT_OK_TO_SUBMIT",
        "uniqueness": {
            "n_rasters": len(rows), "worst_overlap": worst_ov, "worst_spearman": worst_rho,
            "overlap_firings": n_ov, "rho_firings": n_rho, "rows": rows,
        },
    }
    (OUT_DIR / f"{name}.summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
