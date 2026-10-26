#!/usr/bin/env python3
"""
Generate a UNIQUE GeoTIFF submission for the DOE GEMS Prize Challenge.

Novel hypothesis (not tried in any lane of this repo):
  "Basin-center blind-fault via distance-transform ridge emphasis"

Geothermal systems in the northern Great Basin commonly host blind faults
(absent from the USGS/INGENIOUS catalogue) in the *interiors of fault-bounded
basins*, far from range-front mapped traces.  The distance transform of the
catalogue has ridges (local maxima) at basin centers — points equidistant from
opposing range-front faults.  Blind normal faults nucleating in the basin
interior would not appear on surface geologic maps.  Emphasizing dots along
these distance-transform ridges at d_cat > 10 px (> 1 km) targets concealed
basin-interior faults that no catalogue-proximal method can reach.

Why this is unique vs every prior lane:
  - GEMSDOE32 H33 (0.2778 OWNER-REPORTED): 69.8% far-field but still
    30.2% within 1 km of catalogue; dots spread across collar + far field,
    not ridge-concentrated.
  - H86G collar emphasis (parallel branch): smooth 2–8 px collar Gaussian
    immediately adjacent to catalogue faults — opposite extreme.
  - H33 collar pruning removes 1–2 px dots; we place ZERO dots within
    10 px of any catalogue trace.
  - All TCWB / SLCQ / BMGS / PFTE lanes require the 19-band training stack
    which is not present in this checkout; this lane uses only the mapped
    catalogue geometry from existing_faults.tif.

Constraints honored:
  - Values strictly finite in [0, 1], single-band float32 GeoTIFF
  - EPSG:32611, 3730×3292, 100 m transform matching sample_submission.tif
  - Zero positive mass outside footprint (sample_submission.tif finite cells)
  - Zero dots on mapped catalogue (existing_faults.tif > 0)
  - ZERO dots within 10 px (> 1 km) of any catalogue trace — far-field only
  - Unique name (lane+dots+UTC timestamp+sha8, <=140 chars)
  - Note <=140 chars
  - Atomic write via vendor/gems57/submission_writer.py (shared tool, not forked)

Output: docs/downloads/gems86-h86q-basinridge-<dots>dots-<utc>-<sha8>-zeros.tif
  + .zip + .json + .uniqueness.json receipt

Status: SAFE TO DOWNLOAD FOR AUDIT ONLY — NOT OK TO SUBMIT
  (training_features.tif / labels.tif absent → no HOLDOUT-DTI possible;
   no DrivenData auth → no organizer receipt; literal full-support witness
   blocks all nonempty candidates under the current protocol rule)
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

from gems57.submission_writer import write_submission
from gems57.validate import validate, assert_submittable

# --------------------------------------------------------------------------- #
# Novel hypothesis: basin-center blind-fault via distance-transform ridge
# --------------------------------------------------------------------------- #
DOT_BUDGET = 37_654          # budget-fair constant shared with H33/H86 lanes
MIN_DIST_PX = 10.0           # ZERO dots within 10 px (>1 km) of catalogue
RIDGE_WEIGHT_EXPONENT = 1.5  # distance-transform ridge emphasis power
SPACING_PX = 2.8             # Poisson-disc minimum separation (dot de-crowding)
RNG_SEED = 20261026

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


def ridge_weight(dist, footprint, catalogue, min_dist_px):
    """Weight along distance-transform ridges in the far field.

    A ridge cell is a local maximum of the distance transform: moving in any
    cardinal direction decreases distance to the nearest catalogue fault.
    These are basin-center locations equidistant from opposing faults — prime
    blind-fault sites concealed from surface mapping.  Weight is the distance
    value itself (farther from catalogue = more concealed = higher weight),
    raised to RIDGE_WEIGHT_EXPONENT to emphasize deeper basin centers, and
    restricted to the far field (dist > min_dist_px).  Returns the weight
    plus diagnostic masks for reporting.
    """
    from scipy import ndimage as ndi

    # Local maximum in 8-connectivity: a cell is a ridge if its distance
    # equals the maximum over its 3x3 neighborhood.
    max_filt = ndi.maximum_filter(dist, size=3, mode="constant", cval=0.0)
    is_ridge = (dist == max_filt) & (dist > 0)

    # Far-field mask: beyond the 300 m DTI kernel radius, well clear of
    # catalogue traces where blind basin-interior faults hide.
    far_field = (dist > min_dist_px) & footprint & (~catalogue)

    # Primary weight: distance-transform value on ridges, amplified by
    # exponent to concentrate on deep basin centers.
    w = np.zeros_like(dist, dtype=np.float64)
    ridge_far = is_ridge & far_field
    w[ridge_far] = dist[ridge_far] ** RIDGE_WEIGHT_EXPONENT

    # Secondary fill: smooth far-field distance weight so the full budget
    # can be placed even where ridge cells are sparse after spacing.
    # This is weighted lower than ridges by the exponent < 1 relative
    # scaling but still rewards distance from catalogue.
    smooth_far = far_field & ~ridge_far
    if smooth_far.any():
        w[smooth_far] = (dist[smooth_far] ** 0.5) * 0.3

    if w.max() > 0:
        w = w / w.max()
    return w, is_ridge, far_field


def poisson_disc_emission(weight, budget, spacing_px, rng):
    """Greedy Poisson-disc emission weighted by ``weight``.

    Returns boolean mask of up to ``budget`` positive cells, each at least
    ``spacing_px`` from every other.  Greedy raster scan in descending
    weight order.
    """
    h, wgt = weight.shape
    flat_w = weight.ravel()
    order = np.argsort(-flat_w, kind="stable")  # descending weight

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


def build_prediction():
    footprint, catalogue = load_grid()
    dist = distance_to_catalogue(catalogue)
    weight, is_ridge, far_field = ridge_weight(dist, footprint, catalogue, MIN_DIST_PX)

    pos = weight > 0
    if not pos.any():
        raise RuntimeError("no far-field ridge emission cells found")

    n_ridge_cells = int(is_ridge.sum())
    n_far_field_cells = int(far_field.sum())
    n_ridge_far = int((is_ridge & far_field).sum())
    print(f"  far-field cells (d_cat > {MIN_DIST_PX}px): {n_far_field_cells:,}")
    print(f"  distance-transform ridge cells in far field: {n_ridge_far:,}")

    rng = np.random.default_rng(RNG_SEED)
    dots = poisson_disc_emission(weight, DOT_BUDGET, SPACING_PX, rng)

    # Sanity: dots must be on footprint, off catalogue, in far field
    assert int((dots & ~footprint).sum()) == 0, "dots outside footprint"
    assert int((dots & catalogue).sum()) == 0, "dots on catalogue"
    near_cat = dots & (dist <= MIN_DIST_PX)
    assert int(near_cat.sum()) == 0, f"dots within {MIN_DIST_PX}px of catalogue: {int(near_cat.sum())}"
    assert int(dots.sum()) <= DOT_BUDGET, f"too many dots: {dots.sum()}"

    prediction = dots.astype(np.float32)  # binary {0,1}, strictly in [0,1]
    return prediction, footprint, catalogue, dist, weight, dots, is_ridge, far_field


def make_name_note(dots_count, sha8):
    utc = _dt.datetime.now(_dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    name = f"gems86-h86q-basinridge-{dots_count}dots-{utc}-{sha8}-zeros"
    assert 1 <= len(name) <= 140, f"name len {len(name)}"
    note = (
        f"H86Q basin-center distance-ridge {dots_count}d; far-field dcat>10px "
        f"(ridge+smooth); blind basin-interior faults; Poisson-disc 2.8px; "
        f"DO NOT SUBMIT"
    )
    assert 1 <= len(note) <= 140, f"note len {len(note)}"
    return name, note


def local_uniqueness_check(prediction, footprint):
    """Compare against locally accessible registry rasters (docs/downloads +
    data/scored_fleet), EXCLUDING the candidate itself.  Reports worst
    Spearman rho and worst forward 3-px dot overlap."""
    RADIUS_PX = 3

    def _dots(a):
        a = np.asarray(a)
        return np.isfinite(a) & (a > 0)

    def _near(support, radius_px=RADIUS_PX):
        from scipy.ndimage import binary_dilation
        r = int(np.ceil(radius_px))
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
        return binary_dilation(support, structure=yy * yy + xx * xx <= radius_px * radius_px)

    from scipy.stats import spearmanr

    registry_rasters = sorted((REPO / "docs" / "downloads").glob("*.tif")) + \
                         sorted((REPO / "data" / "scored_fleet").glob("*.tif"))
    seen = set()
    unique_rasters = []
    for p in registry_rasters:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique_rasters.append(p)

    print(f"Uniqueness: comparing against {len(unique_rasters)} locally accessible rasters (self-excluded)")

    mine_dots = _dots(prediction) & footprint
    my_near = _near(mine_dots)
    my_decoded = hashlib.sha256(np.ascontiguousarray(prediction).tobytes()).hexdigest()
    rows = []
    for p in unique_rasters:
        try:
            with rasterio.open(p) as ds:
                theirs = ds.read(1).astype(np.float32)
            theirs = np.where(np.isfinite(theirs), theirs, 0.0)
            theirs[~footprint] = 0.0
            their_dots = _dots(theirs) & footprint
            their_near = _near(their_dots)

            # Skip self-comparison: identical decoded pixels
            their_decoded = hashlib.sha256(np.ascontiguousarray(theirs).tobytes()).hexdigest()
            if their_decoded == my_decoded:
                print(f"  SKIP self-match: {p.name}")
                continue

            # Forward 3-px overlap: my dots within 3 px of their dots
            if mine_dots.sum() == 0 or their_dots.sum() == 0:
                ov = 0.0
            else:
                ov = float(their_near[mine_dots].mean())

            # Spearman on full footprint
            mv = prediction[footprint].astype(np.float64)
            tv = theirs[footprint].astype(np.float64)
            if np.ptp(mv) and np.ptp(tv):
                rho = float(spearmanr(mv, tv).statistic)
            else:
                rho = float("nan")

            rows.append(dict(
                file=p.name,
                overlap=ov,
                spearman=rho,
                overlap_firing=ov > 0.70,
                rho_firing=(rho > 0.90) if not math.isnan(rho) else False,
            ))
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

    return rows, worst_overlap, worst_rho, n_overlap_firings, n_rho_firings


def _run():
    prediction, footprint, catalogue, dist, weight, dots, is_ridge, far_field = build_prediction()
    dots_count = int(dots.sum())

    decoded_sha = hashlib.sha256(np.ascontiguousarray(prediction).tobytes()).hexdigest()
    sha8 = decoded_sha[:8]

    name, note = make_name_note(dots_count, sha8)

    out_tif = OUT_DIR / f"{name}.tif"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("H86Q — Basin-center blind-fault via distance-transform ridge emphasis")
    print("=" * 60)
    print(f"Dot budget: {DOT_BUDGET}, placed: {dots_count}")
    print(f"Minimum catalogue distance: {MIN_DIST_PX} px (> 1 km, far-field only)")
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

    # Local uniqueness check (self-excluded)
    rows, worst_overlap, worst_rho, n_ov_fire, n_rho_fire = local_uniqueness_check(prediction, footprint)

    print()
    print("=" * 60)
    print("SUBMISSION STATUS: NOT OK TO SUBMIT — AUDIT ONLY")
    print("=" * 60)
    print("Reason: training_features.tif and labels.tif are absent from this")
    print("checkout, so HOLDOUT-DTI cannot be computed. Without HOLDOUT-DTI +")
    print("an organizer receipt, no file is authorized for a weekly slot.")
    print("The literal full-support witness (17GEMSDOE) also blocks every")
    print("nonempty candidate by construction under the current protocol rule.")
    print()
    print(f"File: {out_tif.name}")
    print(f"SHA-256: {receipt['sha256']}")
    print(f"Safe to download for audit: YES")
    print(f"OK to submit to DrivenData: NO")
    print()

    print("Local registry rows (worst firings first):")
    firing_rows = [r for r in rows if r.get("overlap_firing") or r.get("rho_firing")]
    for r in sorted(rows, key=lambda x: -(x.get("overlap", 0) or 0))[:15]:
        flag = "FIRE" if r.get("overlap_firing") or r.get("rho_firing") else "ok"
        err = f" [ERROR: {r['error']}]" if "error" in r else ""
        print(f"  {flag:4s} {r['file']:70s} ov={r.get('overlap','--')} rho={r.get('spearman','--')}{err}")
    if firing_rows:
        print(f"  >> {len(firing_rows)} firing rows (see full list above)")

    # Save a machine-readable uniqueness report
    report = {
        "schema": "gems86.unique-submission-report.v1",
        "lane": "h86q-basinridge",
        "hypothesis": "basin-center blind-fault via distance-transform ridge emphasis (far-field dcat>10px, ridge+smooth fill)",
        "file": str(out_tif),
        "file_name": out_tif.name,
        "sha256": receipt["sha256"],
        "bytes": receipt["bytes"],
        "submission_name": name,
        "note": note,
        "note_chars": len(note),
        "dots": dots_count,
        "checks": receipt["checks"],
        "all_checks_passed": receipt["all_checks_passed"],
        "min": receipt["min"],
        "max": receipt["max"],
        "n_nan": receipt["n_nan"],
        "emitted_positive_pixels": receipt["emitted_positive_pixels"],
        "in_footprint_positive_pixels": receipt["in_footprint_positive_pixels"],
        "on_catalogue_positive_pixels": receipt.get("on_catalogue_positive_pixels"),
        "worst_local_overlap": worst_overlap,
        "worst_local_rho": worst_rho,
        "local_overlap_firings": n_ov_fire,
        "local_rho_firings": n_rho_fire,
        "registry_rasters_checked": len(rows),
        "submission_status": "NOT_OK_TO_SUBMIT_AUDIT_ONLY",
        "safe_to_download": True,
        "ok_to_submit": False,
        "reason": "No training_features.tif/labels.tif -> no HOLDOUT-DTI; no DrivenData auth -> no organizer receipt; literal witness blocks all nonempty candidates",
    }
    report_path = OUT_DIR / f"{name}.uniqueness.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"\nUniqueness report: {report_path}")


if __name__ == "__main__":
    _run()
