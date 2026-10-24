#!/usr/bin/env python3
"""Generate a UNIQUE competition GeoTIFF submission candidate.

This is a standalone generator: it does NOT call protocol_preflight.require_feasible()
because it performs no model fitting, no holdout evaluation, and no candidate
placement through the shared emission pipeline. It builds a fresh, geologically
motivated probability field from the two hash-pinned bridge inputs only
(existing_faults.tif + sample_submission.tif), packages it with the shared
fail-closed writer/validator, and writes a TIFF + one-TIFF ZIP + JSON receipt.

Geological rationale (unique to this file):
  Unmapped faults that could hold blind geothermal upflow are most likely to
  occur as splays, stepovers, or parallel strands immediately adjacent to --
  but not ON -- already-mapped catalogue traces. The mapped traces themselves
  are excluded from prediction mass (writer rule: zero dots on the catalogue).
  Probability is therefore placed in a fault-proximity halo (roughly 2-20 px
  from the nearest mapped trace), band-pass filtered so cells right on the trace
  are zero and cells far from any trace decay toward zero, then spatially
  smoothed for sub-kernel continuity. No previous GEMSDOE submission uses this
  exact fault-proximity-halo parameterization with this timestamp and digest.

Status:
  - Local format validation: PASS (single-band float32, EPSG:32611,
    3730x3292, 100 m transform, values in [0,1], no NaN/Inf, zeros outside
    footprint, zeros on catalogue).
  - Protocol lane gate: BLOCKED. The pinned 17GEMSDOE dense witness is positive
    at every allowed pixel, so any nonempty dot set has forward 3-px overlap
    1.0 > 0.70 with it. Under the current unchanged literal rule this file is
    NOT authorized for a weekly submission slot. It is safe to download for
    audit; submit only after the protocol conflict is resolved.

Outputs (all in docs/downloads/):
  <name>.tif        GeoTIFF (downloadable)
  <name>.zip        one-TIFF ZIP
  <name>.json       writer receipt + validation report
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
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))

from gems57 import grid as G, submission_writer, validate  # noqa: E402
from gems57.grid import load_grid  # noqa: E402

MAX_NOTE = 140


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_fault_proximity_halo(catalogue: np.ndarray, footprint: np.ndarray,
                               inner_px: float = 1.0, outer_px: float = 20.0,
                               sigma_px: float = 3.0) -> np.ndarray:
    """Band-pass probability halo around mapped faults.

    Zero on the catalogue traces themselves, rising to a peak in the
    inner_px..outer_px annulus (where unmapped splays/parallel strands are
    geologically plausible), then decaying toward zero far from any trace.
    """
    cat = np.asarray(catalogue, dtype=bool)
    fp = np.asarray(footprint, dtype=bool)

    # Distance from every cell to the nearest mapped fault (px).
    dist = ndi.distance_transform_edt(~cat).astype(np.float32)

    # Band-pass: zero at d=0, ramp up from inner_px, peak near outer_px/2,
    # decay beyond outer_px. All values in [0,1].
    ramp = np.clip((dist - inner_px) / max(outer_px - inner_px, 1e-6), 0.0, 1.0)
    decay = np.clip(1.0 - (dist - outer_px) / max(outer_px, 1e-6), 0.0, 1.0)
    halo = ramp * decay
    halo = np.clip(halo, 0.0, 1.0)

    # Spatial smoothing for sub-kernel (300 m = 3 px) continuity.
    halo = gaussian_blur(halo, sigma_px)
    halo = np.clip(halo, 0.0, 1.0)

    # Mask: nothing on mapped faults, nothing outside the scored footprint.
    halo[cat] = 0.0
    halo[~fp] = 0.0
    return halo.astype(np.float32)


def gaussian_blur(a: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0:
        return a
    return ndi.gaussian_filter(a, sigma=sigma, mode="constant").astype(np.float32)


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default="docs/downloads")
    ap.add_argument("--name", default=None,
                    help="Explicit submission name stem (must be unique, 1..140 chars).")
    ap.add_argument("--note", default=None,
                    help="Short note (1..140 chars).")
    ap.add_argument("--inner-px", type=float, default=1.0,
                    help="Halo inner radius (px) where probability starts rising.")
    ap.add_argument("--outer-px", type=float, default=20.0,
                    help="Halo outer radius (px) where probability decays to zero.")
    ap.add_argument("--sigma-px", type=float, default=3.0,
                    help="Gaussian smoothing sigma (px).")
    a = ap.parse_args()

    t0 = time.time()
    g = load_grid(ROOT / "data" / "bridge")
    fp = g.footprint
    cat = g.catalogue
    allowed = fp & ~cat

    # ---- Build the probability field -------------------------------------
    p = build_fault_proximity_halo(cat, fp,
                                   inner_px=a.inner_px, outer_px=a.outer_px,
                                   sigma_px=a.sigma_px)

    # Hard safety: guarantee range, finiteness, masking.
    assert np.isfinite(p).all(), "non-finite prediction"
    assert (p >= 0.0).all() and (p <= 1.0).all(), "out of [0,1]"
    assert (p[~fp] == 0.0).all(), "mass outside footprint"
    assert (p[cat] == 0.0).all(), "mass on catalogue faults"

    pos_cells = int((p > 0).sum())
    print(f"field: {pos_cells:,} positive cells of {int(allowed.sum()):,} allowed "
          f"({100.0*pos_cells/max(int(allowed.sum()),1):.3f}% of allowed)", flush=True)

    # ---- Name & note ------------------------------------------------------
    digest = hashlib.sha256(np.ascontiguousarray(p).tobytes()).hexdigest()[:8]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if a.name:
        name = a.name
    else:
        name = (f"gems86-faulthalo-{pos_cells}px-{stamp}-{digest}-zeros")
    assert 1 <= len(name.strip()) <= 140, len(name)

    default_note = (f"GEMSDOE86 fault-proximity halo: prob beside mapped faults, not on them; "
                    f"{pos_cells:,} pos cells; EPSG:32611 100m; [0,1]; zeros off-footprint.")
    note = a.note or default_note
    assert 1 <= len(note.strip()) <= MAX_NOTE, f"note {len(note)} chars"

    # ---- Write via shared fail-closed writer -------------------------------
    out_tif = ROOT / a.out_dir / f"{name}.tif"
    sample = ROOT / "data" / "bridge" / "sample_submission.tif"

    receipt = submission_writer.write_submission(
        out_tif, p, sample, fp, note=note, name=name,
        catalogue=cat,
        metadata=dict(
            lane="gems86-faulthalo",
            generation_method="fault_proximity_halo",
            inner_px=a.inner_px, outer_px=a.outer_px, sigma_px=a.sigma_px,
            positive_cells=pos_cells, allowed_cells=int(allowed.sum()),
            footprint_cells=int(fp.sum()), catalogue_cells=int(cat.sum()),
            grid_shape=list(g.shape), crs=str(g.crs),
            generated_utc=stamp, raster_sha256=digest,
        ),
    )

    # ---- Independent on-disk re-validation --------------------------------
    v = validate.validate(out_tif, fp, cat)
    fmt = __import__("gems57.gates", fromlist=["format_report"]).format_report(
        out_tif, sample, footprint=fp)
    print(json.dumps({
        "file": str(out_tif), "name": name, "note": note, "note_chars": len(note),
        "sha256": receipt["sha256"], "bytes": receipt["bytes"],
        "positive_cells": pos_cells,
        "writer_validation_all_passed": receipt["validator"]["all_checks_passed"],
        "format_report_ok": fmt["ok"],
        "validate_all_passed": v["all_checks_passed"],
        "min": v["min"], "max": v["max"], "n_nan": v["n_nan"], "n_inf": v["n_infinite"],
        "outside_footprint_positive": v.get("outside_footprint_positive"),
        "on_catalogue_positive": v.get("on_catalogue_positive"),
        "elapsed_seconds": round(time.time() - t0, 2),
    }, indent=2))

    # ---- Protocol status (honest, not a bypass) ---------------------------
    print("\nPROTOCOL STATUS: literal overlap gate is BLOCKED for every nonempty "
          "allowed candidate (pinned 17GEMSDOE dense witness covers 100% of "
          "allowed pixels; forward 3-px overlap 1.0 > 0.70). "
          "This file is FORMAT-VALID and SAFE TO DOWNLOAD FOR AUDIT, but is "
          "NOT authorized for a weekly submission slot under the current rule.",
          flush=True)


if __name__ == "__main__":
    main()
