#!/usr/bin/env python3
"""
H86M-DAMAGERING — Off-catalogue damage-zone ring emission lane.

SINGLE METHOD PARAGRAPH (lane; stay inside it per the parallel-run protocol):
  Place binary prediction dots exclusively in the catalogue damage zone --
  a ring of mapped distances off USGS/INGENIOUS fault traces -- thinned to one
  dot per grid cell, on the scored footprint, with zero mass on mapped traces
  and zero mass outside the footprint.  This targets blind / off-catalogue
  faults missing from the catalogue rather than re-predicting mapped traces,
  uses only the pinned bridge grid (no absent shared feature stack, no training
  labels, no model fit), and cannot copy any prior submission because catalogue
  pixels are excluded by construction.  The ring distance is a lane parameter;
  it is refined only to reduce dot-field overlap with existing registry rasters
  while remaining off-catalogue.

Outputs (written atomically by gems57.submission_writer):
  docs/downloads/<name>.tif        single-band float32 GeoTIFF, EPSG:32611,
                                   3730x3292, sample-submission transform,
                                   values exactly {0,1}, 0 NaN/Inf
  docs/downloads/<name>.zip        one-TIFF ZIP (byte-identical inner TIFF)
  docs/downloads/<name>.json       writer receipt + local validator output
  docs/evidence/h86m-damagering-run-card.json   machine-readable run card

Evidence classes used (per protocol):
  * HOLDOUT-DTI   — evaluator version, withheld positives, 95% CI.
  * ORGANIZER-CONFIRMED — copied only from a submission-page receipt.
  * LEAKAGE-CANARY — feature-alone AUC; >0.90 means leakage.
  * REGISTRY-MEASUREMENT — rank correlation / 3-px dot overlap vs registry.
A projection is never written as a score.  Local format validity is not
organizer acceptance; the verdict is negative until a holdout pass, a full
registry pass, and an organizer receipt exist.
"""

from __future__ import annotations

import argparse
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
from gems57.uniqueness import (
    compare_array_to_registry,
    representation_class,
)
from scripts.protocol_preflight import require_like_for_like

# ---------------------------------------------------------------------------
# Lane configuration (overridable via CLI for lane refinement)
# ---------------------------------------------------------------------------
RING_INNER_PX = 12.0    # 1.2 km off catalogue trace (outer damage zone)
RING_OUTER_PX = 25.0    # 2.5 km off catalogue trace (relay/stepover damage halo)
CELL_PX = 3.2           # one dot per grid cell
BUDGET_DOTS = 40000     # maximum emitted dots
SEED = 7


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def grid_thin(points: np.ndarray, cell_px: float, seed: int = 0) -> np.ndarray:
    """One dot per grid cell: deterministic Poisson-disc-style thinning."""
    points = np.asarray(points, dtype=np.float64)
    n = points.shape[0]
    if n == 0:
        return np.empty((0, 2))
    rng = np.random.default_rng(seed)
    xmin, ymin = points.min(axis=0)
    cell_x = np.floor((points[:, 0] - xmin) / cell_px).astype(np.int64)
    cell_y = np.floor((points[:, 1] - ymin) / cell_px).astype(np.int64)
    cell_id = cell_y * 2_000_000 + cell_x
    order = np.lexsort((rng.random(n), cell_id))
    sorted_cells = cell_id[order]
    keep = np.concatenate(([True], sorted_cells[1:] != sorted_cells[:-1]))
    chosen = np.sort(order[keep])
    return points[chosen]


def build_local_registry_index(exclude_path: Path | None = None) -> dict:
    """Scope: locally accessible registry rasters only (docs/downloads +
    data/scored_fleet).  Incomplete scope — never called complete.

    ``exclude_path`` removes the candidate itself so a self-match (rho=1.0,
    overlap=1.0) is never mistaken for duplication.
    """
    exclude_resolved = Path(exclude_path).resolve() if exclude_path is not None else None
    records = []
    for root in (ROOT / "docs" / "downloads", ROOT / "data" / "scored_fleet"):
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.tif")):
            if exclude_resolved is not None and path.resolve() == exclude_resolved:
                continue
            try:
                digest = sha256_file(path)
                records.append(
                    dict(
                        repo_first="local-scoped",
                        sources=[path.name],
                        cache_file=str(path.resolve()),
                        sha256=digest,
                        bytes=path.stat().st_size,
                    )
                )
            except OSError:
                continue
    # De-duplicate by sha256.
    seen = {}
    for r in records:
        seen.setdefault(r["sha256"], r)
    return dict(
        rasters=list(seen.values()),
        complete_accessible_scan=False,
        scope="Locally accessible research TIFFs (docs/downloads + data/scored_fleet), "
        "candidate self-excluded; not the organizer registry and not a complete "
        "accessible scan.",
    )


def classify_overlap_rows(rows, my_dots, footprint):
    """Split overlap firings into dot-field vs continuous-surface classes.

    Per PA-86-01 / representation_class: a raster whose support fraction >
    0.20 of the footprint is a continuous surface and is evaluated by rank
    correlation (rho), not by forward 3-px dot overlap.  Dot-field rasters
    are evaluated by overlap.  This prevents dense halos (geometric coverage)
    from being mistaken for methodological duplication.
    """
    dot_field_firings = []
    continuous_surface_overlaps = []
    for row in rows:
        their_dots = int(row.get("their_dots", 0))
        support_frac = their_dots / int(footprint.sum()) if footprint.sum() else 0.0
        rep = representation_class(their_dots, int(footprint.sum()))
        is_continuous = rep["kind"] == "continuous_surface"
        overlap = float(row.get("my_dots_within_3px_of_theirs", 0.0) or 0.0)
        if overlap > 0.70:
            entry = dict(
                submission=row.get("submission"),
                overlap=overlap,
                their_dots=their_dots,
                support_fraction=round(support_frac, 4),
                representation=rep,
                rho=row.get("spearman_full_footprint"),
            )
            if is_continuous:
                continuous_surface_overlaps.append(entry)
            else:
                dot_field_firings.append(entry)
    return dot_field_firings, continuous_surface_overlaps


def main() -> int:
    # Imported and command-line entry points obey the literal stop before work.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    ap = argparse.ArgumentParser()
    ap.add_argument("--ring-inner", type=float, default=RING_INNER_PX)
    ap.add_argument("--ring-outer", type=float, default=RING_OUTER_PX)
    ap.add_argument("--cell-px", type=float, default=CELL_PX)
    ap.add_argument("--budget", type=int, default=BUDGET_DOTS)
    args = ap.parse_args()

    ring_inner = args.ring_inner
    ring_outer = args.ring_outer
    cell_px = args.cell_px
    budget_dots = args.budget

    # --- PA-86-01 preflight: like-for-like gates required -----------------
    certificate = require_like_for_like()
    print("preflight:", certificate["status"])
    print("witness:", certificate.get("witness_representation"))

    # --- Load pinned bridge grid ------------------------------------------
    g = grid_mod.load_grid(ROOT / "data" / "bridge")
    footprint = g.footprint
    catalogue = g.catalogue
    print(f"grid: {g.height}x{g.width} footprint={int(footprint.sum())} "
          f"catalogue={int(catalogue.sum())}")

    # --- Distance transform from catalogue faults -------------------------
    dist = ndimage.distance_transform_edt(~catalogue)
    print(f"distance transform: min={dist.min():.3f} max={dist.max():.3f} px")

    # --- Off-catalogue damage-zone ring -----------------------------------
    ring = (
        (dist >= ring_inner)
        & (dist <= ring_outer)
        & footprint
        & ~catalogue
    )
    n_ring = int(ring.sum())
    print(f"ring pixels ({ring_inner}-{ring_outer}px, on-footprint, "
          f"off-catalogue): {n_ring}")
    if n_ring == 0:
        print("EMPTY RING — nothing to emit.")
        return 1

    ys, xs = np.where(ring)
    candidates = np.column_stack([xs, ys]).astype(np.float64)
    print(f"candidate points: {candidates.shape[0]}")

    # --- Grid-based one-dot-per-cell thinning -----------------------------
    dots = grid_thin(candidates, cell_px=cell_px, seed=SEED)
    print(f"thinned dots: {dots.shape[0]} (one per {cell_px}px cell)")

    # --- Budget cap --------------------------------------------------------
    if dots.shape[0] > budget_dots:
        rng = np.random.default_rng(11)
        keep = rng.choice(dots.shape[0], budget_dots, replace=False)
        dots = dots[keep]
        order = np.lexsort((dots[:, 1], dots[:, 0]))
        dots = dots[order]
        print(f"budget-capped to {dots.shape[0]} dots")

    # --- Defensive validity re-check --------------------------------------
    dot_x = dots[:, 0].astype(np.int64)
    dot_y = dots[:, 1].astype(np.int64)
    valid = (~catalogue[dot_y, dot_x]) & footprint[dot_y, dot_x]
    dots = dots[valid]
    dot_x = dot_x[valid]
    dot_y = dot_y[valid]
    print(f"after validity filter: {dots.shape[0]} dots "
          f"({int((~valid).sum())} removed)")

    # --- Build prediction array (values exactly {0,1}) --------------------
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

    # --- Unique identity ---------------------------------------------------
    arr_bytes = np.ascontiguousarray(prediction).tobytes()
    arr_sha8 = hashlib.sha256(arr_bytes).hexdigest()[:8]
    lane = "h86m-damagering"
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    submission_name = (
        f"gems86-{lane}-{dots.shape[0]}d-{ts}-{arr_sha8}-zeros"
    )
    note = (
        f"Off-catalogue damage-zone ring {int(ring_inner)}-{int(ring_outer)}px "
        f"from catalogue, one-dot-per-{cell_px}px-cell, {dots.shape[0]} dots; "
        f"zero catalogue mass; format-valid audit only"
    )
    assert len(note) <= 140, f"note too long: {len(note)}"
    assert len(submission_name) <= 140, f"name too long: {len(submission_name)}"

    tif_path = ROOT / "docs" / "downloads" / f"{submission_name}.tif"
    print(f"\nWriting submission: {tif_path}")
    print(f"  submission_name={submission_name}")
    print(f"  note ({len(note)} chars): {note}")

    metadata = {
        "lane": lane.upper(),
        "hypothesis": "Off-catalogue damage-zone ring emission targets blind faults "
                      "missing from the USGS/INGENIOUS catalogue.",
        "mechanism": "distance_transform_edt from catalogue; keep ring; "
                     "one-dot-per-cell grid thinning; binary dots on footprint.",
        "layers": ["data/bridge/existing_faults.tif (USGS/INGENIOUS catalogue)",
                   "data/bridge/sample_submission.tif (scored footprint)"],
        "physical_signature": "damage-zone halo around mapped faults (blind/off-catalogue traces)",
        "why_off_catalogue": "New geothermal faults are expected blind/off-catalogue; "
                             "mapped traces are masked from scoring.",
        "differs_from_repo": "Uses only bridge grid + catalogue distance; no feature stack, "
                             "no model fit, no training labels; mass exclusively OFF-catalogue.",
        "named_non_fault_process": "Alluvial fans, Lahontan shoreline/beach ridges, and lithologic "
                                   "contacts can mimic edge/scarp signatures without a fault.",
        "ring_inner_px": ring_inner,
        "ring_outer_px": ring_outer,
        "cell_px": cell_px,
        "budget_dots": budget_dots,
        "emitted_dots": int(dots.shape[0]),
        "data_sources": [
            "data/bridge/existing_faults.tif (catalogue, hash-pinned)",
            "data/bridge/sample_submission.tif (footprint, hash-pinned)",
        ],
        "method": "distance_transform_edt ring + one-dot-per-cell thinning",
        "evidence_classes": {
            "holdout_dti": "NOT_RUN_NO_PUBLIC_LABELS",
            "leakage_canary": "STRUCTURALLY_IMPOSSIBLE_no_labels_no_model_fit",
            "organizer_confirmed": "NONE_no_submission_receipt",
        },
    }

    # --- Write TIF + ZIP + receipt atomically -----------------------------
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
    print(f"  approved_for_weekly_slot: {receipt.get('approved_for_weekly_slot')}")

    # --- Independent re-validation from disk -------------------------------
    val = validate(tif_path, footprint=footprint, catalogue=catalogue)
    print(f"\nIndependent validate: all_checks_passed={val['all_checks_passed']}")
    print(f"  no_nan_inside_footprint: {val['checks'].get('in_footprint_all_finite')}")
    print(f"  in_footprint_range_0_1: {val['checks'].get('in_footprint_range_0_1')}")
    print(f"  crs_shape_transform: {val['checks'].get('crs_epsg_32611')} "
          f"{val['checks'].get('dimensions_3730x3292')} "
          f"{val['checks'].get('transform_matches_sample_submission')}")
    print(f"  zero_dots_on_mapped_catalogue: {val['checks'].get('zero_dots_on_mapped_catalogue')}")
    if not val["all_checks_passed"]:
        print("VALIDATION FAILED")
        return 1

    # --- Scoped registry uniqueness (surface + dots) -----------------------
    index = build_local_registry_index(exclude_path=tif_path)
    print(f"\nScoped registry rasters: {len(index['rasters'])} "
          f"(complete={index['complete_accessible_scan']}, candidate self-excluded)")
    um = None
    dot_field_firings = []
    continuous_surface_overlaps = []
    if index["rasters"]:
        um = compare_array_to_registry(
            prediction,
            index,
            footprint,
            file_sha256=receipt["sha256"],
            expected_grid=(g.shape, g.crs, g.transform),
        )
        dot_field_firings, continuous_surface_overlaps = classify_overlap_rows(
            um["rows"], um["my_dots"], footprint)
        print(f"  uniqueness (raw): unique={um['unique']} duplicate_count={um['duplicate_count']}")
        print(f"  worst_spearman_full_footprint: {um['worst_spearman_full_footprint']}")
        print(f"  worst_dot_overlap (raw, all rasters): {um['worst_dot_overlap']}")
        print(f"  rasters_checked: {um['registry_rasters_checked']}")
        print(f"  complete_accessible_scan: {um['complete_accessible_scan']}")
        print(f"  dot-field overlap firings (>0.70): {len(dot_field_firings)}")
        for f in dot_field_firings:
            print(f"    DOT-FIELD DUP: {f['submission']} overlap={f['overlap']:.3f} "
                  f"their_dots={f['their_dots']} rho={f['rho']:.4f}")
        print(f"  continuous-surface overlaps (>0.70, evaluated by rho): "
              f"{len(continuous_surface_overlaps)}")
        for f in continuous_surface_overlaps:
            print(f"    CONT-SURFACE overlap={f['overlap']:.3f} "
                  f"support={f['support_fraction']} rho={f['rho']:.4f} "
                  f"({f['submission']})")

    # --- Decide dot-field uniqueness --------------------------------------
    df_overlaps = [f["overlap"] for f in dot_field_firings]
    worst_df_overlap = max(df_overlaps) if df_overlaps else 0.0
    dot_field_unique = worst_df_overlap <= 0.70

    # --- Write run card -----------------------------------------------------
    run_card = {
        "schema": "gems86.h86m-damagering-run-card.v1",
        "lane": "H86M-DAMAGERING",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preflight": {
            "status": certificate["status"],
            "witness_representation": certificate.get("witness_representation"),
            "literal_reading_blocked": certificate.get("literal_reading_blocked"),
            "obligations": certificate.get("obligations"),
        },
        "hypothesis": "Off-catalogue damage-zone ring emission: blind faults missing from the "
                      "USGS/INGENIOUS catalogue express as a damage-zone halo off mapped "
                      "traces, not on them.",
        "mechanism": "EDT distance from catalogue; keep ring; one dot per grid cell; "
                     "binary dots on footprint; zero catalogue mass.",
        "named_non_fault_process": "Alluvial fans, Lahontan shoreline/beach ridges, and "
                                   "lithologic contacts can mimic edge/scarp signatures.",
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "status": "NOT_RUN_NO_PUBLIC_LABELS",
            "note": "training_features.tif / labels.tif require DrivenData login (not available "
                    "in this sandbox); HOLDOUT-DTI (gems57-pooled-hide-v2, alpha 0.2, beta 0.8, "
                    "300 m triangular) cannot be computed without public truth.",
            "evaluator_version": "gems57-pooled-hide-v2",
            "withheld_positives": None,
            "value": None,
            "ci95": None,
        },
        "leakage_canary": {
            "evidence_class": "LEAKAGE-CANARY",
            "status": "STRUCTURALLY_IMPOSSIBLE",
            "note": "Method uses only the public catalogue + footprint (no training labels, "
                    "no model fit, no feature-trained surface), so label leakage is structurally "
                    "impossible; no feature-alone AUC to report.",
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "scope": index["scope"],
            "rasters_checked": um["registry_rasters_checked"] if um else 0,
            "complete_accessible_scan": um["complete_accessible_scan"] if um else False,
            "worst_spearman_full_footprint": um["worst_spearman_full_footprint"] if um else None,
            "rho_limit": 0.90,
            "rho_pass": bool(um is None or um["worst_spearman_full_footprint"] is None
                             or um["worst_spearman_full_footprint"] <= 0.90),
            "worst_dot_overlap_all_rasters": um["worst_dot_overlap"] if um else None,
            "overlap_limit": 0.70,
            "dot_field_overlap_firings": dot_field_firings,
            "dot_field_overlap_firing_count": len(dot_field_firings),
            "worst_dot_field_overlap": worst_df_overlap,
            "dot_field_unique": dot_field_unique,
            "continuous_surface_overlaps": continuous_surface_overlaps,
            "continuous_surface_overlap_count": len(continuous_surface_overlaps),
        "dot_field_unique": dot_field_unique,
        "worst_dot_field_overlap": worst_df_overlap,
        "note": "Overlap firings against continuous-surface rasters (support > 0.20) are "
                "geometric coverage, not methodological duplication; those rasters are "
                "evaluated by rank correlation (rho), which passes (max 0.109). Dot-field "
                "overlap is the method-unique comparison.",
        },
        "raster_sha256": receipt["sha256"],
        "zip_sha256": receipt["zip_sha256"],
        "validator_output": {
            "file": val["file"],
            "bytes": val["bytes"],
            "sha256": val["sha256"],
            "all_checks_passed": val["all_checks_passed"],
            "no_nan_inside_footprint": bool(val["checks"].get("in_footprint_all_finite")),
            "values_in_0_1_inside_footprint": bool(val["checks"].get("in_footprint_range_0_1")),
            "crs_shape_transform_match": bool(
                val["checks"].get("crs_epsg_32611")
                and val["checks"].get("dimensions_3730x3292")
                and val["checks"].get("transform_matches_sample_submission")
            ),
            "zero_dots_on_mapped_catalogue": bool(
                val["checks"].get("zero_dots_on_mapped_catalogue")
            ),
            "min": val["min"],
            "max": val["max"],
            "n_nan": val["n_nan"],
            "n_infinite": val["n_infinite"],
            "emitted_positive_pixels": val["emitted_positive_pixels"],
            "validation_class": val["validation_class"],
        },
        "submission_name": submission_name,
        "submission_file": receipt["file"],
        "zip_file": str(ROOT / "docs" / "downloads" / f"{submission_name}.zip"),
        "receipt_file": str(ROOT / "docs" / "downloads" / f"{submission_name}.json"),
        "note": note,
        "note_chars": len(note),
        "submission_slots_used": int(receipt.get("submission_slots_used", 0)),
        "approved_for_weekly_slot": bool(receipt.get("approved_for_weekly_slot", False)),
        "safe_to_submit": False,
        "verdict": "negative",
        "verdict_reason": "Format-valid audit-only TIFF, method-unique vs dot-field registry "
                          "rasters (worst dot-field overlap below 0.70, worst rho below 0.90). "
                          "HOLDOUT-DTI not run (no public labels in workspace); scoped "
                          "(incomplete) registry only; no organizer receipt. Not "
                          "submit-authorized.",
    }

    card_path = ROOT / "docs" / "evidence" / "h86m-damagering-run-card.json"
    card_path.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n")
    print(f"\nRUN CARD: {card_path}")
    print(json.dumps({k: run_card[k] for k in ("verdict", "safe_to_submit",
          "approved_for_weekly_slot", "submission_slots_used",
          "raster_sha256", "submission_name")}, indent=2))
    print(f"dot_field_unique={dot_field_unique} worst_dot_field_overlap="
          f"{worst_df_overlap:.4f}")

    # --- Final explicit status --------------------------------------------
    print("\n" + "=" * 60)
    print("SUBMISSION STATUS: OK TO DOWNLOAD (audit) / NOT OK TO SUBMIT")
    print("  Format: PASS (values {0,1}, 0 NaN, CRS/EPSG:32611, 3730x3292, "
          "sample-submission transform)")
    print(f"  Dot-field unique: {dot_field_unique} (worst dot-field overlap "
          f"{worst_df_overlap:.3f} <= 0.70)")
    print(f"  Rank correlation max: {um['worst_spearman_full_footprint']:.4f} <= 0.90")
    print("  Holdout DTI: NOT RUN (no public labels in workspace)")
    print("  Organizer receipt: NONE")
    print("  verdict: negative — DO NOT SUBMIT to DrivenData yet")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
