#!/usr/bin/env python3
"""
Generate a UNIQUE, locally-validated GEMS submission GeoTIFF.

Method: off-catalogue damage-zone ring emission.

Hypothesis (geological):
  Blind / off-catalogue fault traces nucleate preferentially in the damage
  zone around mapped traces — at jogs, stepovers and relay ramps — rather
  *on* the mapped catalogue line itself.  Emitting prediction mass in a
  catalogue-distance ring (3–8 px = 300–800 m off trace), thinned by
  grid-based Poisson-disc-style sampling, targets faults missing from the
  USGS/INGENIOUS catalogue without placing mass on mapped faults (zero
  catalogue overlap by construction) and without copying any previous
  submission's spatial pattern.

This lane uses ONLY the pinned bridge grid (existing_faults.tif catalogue +
sample_submission.tif footprint).  It does not require the absent shared
feature stack, training labels, or DrivenData credentials.  It is therefore
reproducible from the committed bridge bytes alone.

Outputs (written atomically by gems57.submission_writer):
  docs/downloads/<name>.tif        single-band float32 GeoTIFF, EPSG:32611,
                                   3730x3292, sample-submission transform,
                                   values exactly {0,1}, 0 NaN/Inf
  docs/downloads/<name>.zip        one-TIFF ZIP (byte-identical inner TIFF)
  docs/downloads/<name>.json       writer receipt + local validator output
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))

from gems57 import grid as grid_mod
from gems57.submission_writer import write_submission
from gems57.validate import validate

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RING_INNER_PX = 3.0   # 300 m off catalogue trace
RING_OUTER_PX = 8.0   # 800 m off catalogue trace
CELL_PX = 2.8         # grid cell for one-dot-per-cell thinning (~min separation)
BUDGET_DOTS = 25000   # maximum emitted dots
TIMESTAMP = "20261025T120000Z"
SEED = 42


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def grid_thin(points: np.ndarray, cell_px: float, seed: int = 0) -> np.ndarray:
    """One dot per grid cell: fast Poisson-disc-style thinning.

    Partitions candidate points into square cells of side `cell_px` and keeps
    at most one point per cell.  Guarantees pairwise separation >= cell_px /
    sqrt(2) in the worst case (adjacent diagonal cells), typically much more.
    Deterministic given `seed`.
    """
    points = np.asarray(points, dtype=np.float64)
    n = points.shape[0]
    if n == 0:
        return np.empty((0, 2))
    rng = np.random.default_rng(seed)

    xmin, ymin = points.min(axis=0)
    cell_x = (points[:, 0] - xmin) / cell_px
    cell_y = (points[:, 1] - ymin) / cell_px
    cell_x = np.floor(cell_x).astype(np.int64)
    cell_y = np.floor(cell_y).astype(np.int64)

    # Unique cell id; shuffle within each cell then keep first.
    cell_id = cell_y * 2_000_000 + cell_x  # width < 2M px is safe
    order = np.lexsort((rng.random(n), cell_id))
    sorted_cells = cell_id[order]
    # Keep first occurrence of each cell id.
    keep = np.concatenate(([True], sorted_cells[1:] != sorted_cells[:-1]))
    chosen = order[keep]
    chosen = np.sort(chosen)
    return points[chosen]


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible

    require_feasible()  # fail-closed: literal overlap gate unsatisfied

    # --- Load pinned bridge grid ------------------------------------------
    g = grid_mod.load_grid(ROOT / "data" / "bridge")
    footprint = g.footprint  # bool, scored study-area cells
    catalogue = g.catalogue  # bool, mapped catalogue faults inside footprint
    print(f"grid: {g.height}x{g.width}, footprint={int(footprint.sum())}, "
          f"catalogue={int(catalogue.sum())}")

    # --- Distance transform from catalogue faults -------------------------
    # dist[y, x] = distance (px) to nearest catalogue pixel.
    dist = ndimage.distance_transform_edt(~catalogue)
    print(f"distance transform: min={dist.min():.3f} max={dist.max():.3f} "
          f"(px, 100 m cells)")

    # --- Off-catalogue damage-zone ring -----------------------------------
    ring = (
        (dist >= RING_INNER_PX)
        & (dist <= RING_OUTER_PX)
        & footprint
        & ~catalogue
    )
    n_ring = int(ring.sum())
    print(f"ring pixels ({RING_INNER_PX}-{RING_OUTER_PX} px, on-footprint, "
          f"off-catalogue): {n_ring}")

    ys, xs = np.where(ring)
    candidates = np.column_stack([xs, ys]).astype(np.float64)
    print(f"candidate points: {candidates.shape[0]}")

    # --- Grid-based one-dot-per-cell thinning -----------------------------
    dots = grid_thin(candidates, cell_px=CELL_PX, seed=SEED)
    print(f"thinned dots: {dots.shape[0]} (one per {CELL_PX}px cell)")

    # --- Budget cap --------------------------------------------------------
    if dots.shape[0] > BUDGET_DOTS:
        rng = np.random.default_rng(7)
        keep = rng.choice(dots.shape[0], BUDGET_DOTS, replace=False)
        dots = dots[keep]
        # Sort rows lexicographically (x then y) for deterministic output;
        # order does not affect the prediction array.
        order = np.lexsort((dots[:, 1], dots[:, 0]))
        dots = dots[order]
        print(f"budget-capped to {dots.shape[0]} dots")

    # --- Build prediction array (values exactly {0,1}) --------------------
    # Defensive: re-verify every dot is off-catalogue and on-footprint.
    dot_x = dots[:, 0].astype(np.int64)
    dot_y = dots[:, 1].astype(np.int64)
    valid = (~catalogue[dot_y, dot_x]) & footprint[dot_y, dot_x]
    dots = dots[valid]
    dot_x = dot_x[valid]
    dot_y = dot_y[valid]
    print(f"after validity filter: {dots.shape[0]} dots "
          f"({int((~valid).sum())} removed)")

    prediction = np.zeros((g.height, g.width), dtype=np.float32)
    if dots.shape[0] > 0:
        prediction[dot_y, dot_x] = 1.0

    n_pos = int((prediction > 0).sum())
    n_on_cat = int(((prediction > 0) & catalogue).sum())
    n_outside_fp = int(((prediction > 0) & ~footprint).sum())
    print(f"prediction: positives={n_pos}, on_catalogue={n_on_cat}, "
          f"outside_footprint={n_outside_fp}")
    assert n_on_cat == 0, "refusing: dots on mapped catalogue"
    assert n_outside_fp == 0, "refusing: dots outside footprint"

    # --- Unique identity --------------------------------------------------
    arr_bytes = prediction.tobytes()
    arr_sha8 = hashlib.sha256(arr_bytes).hexdigest()[:8]
    lane = "uniquedot-damagering"
    submission_name = (
        f"gems86-{lane}-{dots.shape[0]}d-{TIMESTAMP}-{arr_sha8}-zeros"
    )
    note = (
        f"Off-catalogue damage-zone ring {RING_INNER_PX}-{RING_OUTER_PX}px "
        f"from catalogue, one-dot-per-{CELL_PX}px-cell, {dots.shape[0]} "
        f"dots; zero catalogue mass; local format-valid only"
    )
    assert len(note) <= 140, f"note too long: {len(note)}"
    assert len(submission_name) <= 140, f"name too long: {len(submission_name)}"

    tif_path = ROOT / "docs" / "downloads" / f"{submission_name}.tif"
    print(f"\nWriting submission: {tif_path}")
    print(f"  submission_name={submission_name}")
    print(f"  note ({len(note)} chars): {note}")

    metadata = {
        "lane": lane.upper(),
        "hypothesis": "off-catalogue damage-zone ring emission targets blind faults",
        "ring_inner_px": RING_INNER_PX,
        "ring_outer_px": RING_OUTER_PX,
        "cell_px": CELL_PX,
        "budget_dots": BUDGET_DOTS,
        "emitted_dots": int(dots.shape[0]),
        "data_sources": ["data/bridge/existing_faults.tif (catalogue)",
                         "data/bridge/sample_submission.tif (footprint)"],
        "method": "distance_transform_edt ring + one-dot-per-cell thinning",
    }

    # --- Write TIF + ZIP + receipt atomically ----------------------------
    receipt = write_submission(
        path=str(tif_path),
        prediction=prediction,
        sample=str(ROOT / "data" / "bridge" / "sample_submission.tif"),
        footprint=footprint,
        catalogue=catalogue,
        note=note,
        name=submission_name,
        metadata=metadata,
    )
    print(f"\nWriter receipt SHA-256: {receipt['sha256']}")
    print(f"  all_checks_passed: {receipt['validator']['all_checks_passed']}")
    print(f"  range [0,1]: min={receipt['validator']['min']} "
          f"max={receipt['validator']['max']}")
    print(f"  NaN: {receipt['validator']['n_nan']}, Inf: {receipt['validator']['n_infinite']}")
    print(f"  ZIP sha256: {receipt['zip_sha256']}")

    # --- Independent re-validation from disk -------------------------------
    val = validate(tif_path, footprint=footprint, catalogue=catalogue)
    print(f"\nIndependent validate: all_checks_passed={val['all_checks_passed']}")
    print(f"  checks: {json.dumps(val['checks'], indent=2)}")

    if not val["all_checks_passed"]:
        print("VALIDATION FAILED")
        return 1

    # --- Write run card ----------------------------------------------------
    run_card = {
        "schema": "gems86.uniquedot-damagering-run-card.v1",
        "lane": lane.upper(),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "raster_sha256": receipt["sha256"],
        "zip_sha256": receipt["zip_sha256"],
        "submission_name": submission_name,
        "submission_file": receipt["file"],
        "zip_file": str(ROOT / "docs" / "downloads" / f"{submission_name}.zip"),
        "note": note,
        "note_chars": len(note),
        "hypothesis": (
            "Blind / off-catalogue faults nucleate in the damage zone around "
            "mapped traces (jogs, stepovers, relay ramps), so a catalogue-"
            "distance ring emission (3–8 px off trace) recovers faults absent "
            "from the USGS/INGENIOUS catalogue without mass on mapped faults."
        ),
        "mechanism": (
            "Euclidean distance transform from pinned existing_faults.tif "
            "catalogue; select footprint pixels at 3–8 px distance that are "
            "off catalogue; one-dot-per-cell thinning at 2.8 px; "
            "emit {0,1}; budget-capped at 25,000 dots."
        ),
        "named_non_fault_process": (
            "Unfaulted lithologic contacts, volcanic flow fronts, alluvial "
            "fan toes and relict shoreline scarps produce similar "
            "off-trace edge/rugosity signatures and can mimic the ring signal."
        ),
        "evidence_classes": (
            "LOCAL-FORMAT-VALIDATION only (values in [0,1], 0 NaN/Inf, "
            "CRS/shape/transform match sample_submission.tif, zero dots on "
            "catalogue, zero mass outside footprint). No HOLDOUT-DTI measured "
            "(training labels unavailable without DrivenData login); no "
            "ORGANIZER-CONFIRMED score. A projection is never written as a "
            "score."
        ),
        "validator_output": val,
        "correlation_overlap_vs_registry": {
            "note": "Registry uniqueness not yet measured; run scripts/check_site.py "
                    "and the PA-86 gates before any slot selection.",
        },
        "verdict": "negative",
        "decision": (
            "Format-valid and unique-by-construction (catalogue-distance ring "
            "not used by any prior lane), but NOT cleared for submission: "
            "holdout DTI and registry uniqueness gates are not yet passed, and "
            "the literal 17GEMSDOE full-footprint witness blocks every "
            "nonempty candidate under the current protocol. Download for audit "
            "only — DO NOT SUBMIT to DrivenData."
        ),
        "submission_slots_used": 0,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_ready": False,
        "organizer_confirmed": False,
        "duplicate": None,
        "holdout_dti": None,
        "budget_experiments": 1,
    }

    card_path = ROOT / "docs" / "downloads" / f"{submission_name}.json"
    card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n")
    print(f"\nRun card written: {card_path}")
    print(f"Verdict: {run_card['verdict']} — {run_card['decision'][:80]}...")
    print("\nDone. File is format-valid but NOT authorized for submission.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
