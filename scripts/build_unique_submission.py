#!/usr/bin/env python3
"""Build a unique, contrarian GEMS submission GeoTIFF.

Scientific rationale (contrarian, distinct from every lane in this repo)
-----------------------------------------------------------------------
Every lane in GEMSDOE86 drives emission from *distance to the mapped
USGS/INGENIOUS catalogue* (distance-to-visible-fault, tip continuation,
trace coherence, snap-to-catalogue).  That is exactly what the scored
truth is *not*: the competition rewards faults MISSING from the catalogue,
and the writer forbids dots on mapped faults anyway.

This lane instead targets blind / off-catalogue geothermal faults with a
*geophysical-propensity* surface that uses no distance-to-catalogue feature
at all:

* geod_dilaterate (band 8)   -- volumetric strain, the direct surface
  expression of deep crustal dilation that feeds blind geothermal faults.
* tc / band 6                -- GeoDAWN radiometric Total Count, a proxy
  for near-surface hydrothermal alteration / clay (band-physics verified:
  r=+0.997140 vs GeoDAWN TC; NOT magnetic tilt).
* iso_grav_anom + slope (bands 13, 5) -- density-contrast boundaries at
  basin edges / buried fault blocks (Gallardo & Meju cross-gradient idea,
  applied as a univariate structural detector).
* depth_to_base_surf (band 15)  -- thick sedimentary cover marks blind,
  basin-bounding faults that have no surface trace in the catalogue.
* ieq_n100a15 (band 17)      -- seismicity density as a weak independent
  corroborator of active structure.

Each band is rank-normalized over the footprint (monotone transform, robust
to outliers), averaged into a soft propensity surface in [0,1], then a 3 px
collar around the mapped catalogue is removed so every dot falls OFF the
catalogue (satisfying the writer's zero-on-catalogue rule and the
off-catalogue discovery premise).  The surface is continuous (not a dot
field), so the literal saturated-prior overlap reading carries no
duplication information; uniqueness is established by rank correlation and
forward 3 px dot overlap vs the indexed registry (reported side by side).

No training is fitted here: this is a deterministic, reproducible physical
surface, so there is no leakage canary failure (no model fit to truth).

Labels: every score-like number is HOLDOUT-DTI (shared evaluator,
gems57-pooled-hide-v2) or a local format/registry measurement.  Nothing is
written as an organizer-confirmed score.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor" / "template66"))

from gems57 import grid as grid_mod
from gems57.grid import load_grid
from gems57.submission_writer import write_submission
from gems57 import uniqueness as uniq
from src.gems86 import instrument
from src.gems86.io import read_band, BAND_PHYSICS_VERIFIED

FEATURES_TIF = ROOT / "data" / "bridge" / "training_features.tif"
BRIDGE = ROOT / "data" / "bridge"

# Band -> (display name, physical role).  Band 6/11/18 use the verified
# physics labels (see BAND_PHYSICS_VERIFIED), not the header names.
BANDS = {
    "geod_dilaterate": 8,     # volumetric strain (dilation)
    "tc": 6,                  # GeoDAWN radiometric Total Count (alteration proxy)
    "iso_grav_anom": 13,      # isostatic gravity anomaly (density contrast)
    "iso_grav_anom_slope": 5, # horizontal gravity-gradient magnitude
    "depth_to_base_surf": 15, # sediment cover (blind basin-bounding faults)
    "ieq_n100a15": 17,        # seismicity density (weak corroborator)
}
WEIGHTS = {
    "geod_dilaterate": 0.30,
    "tc": 0.25,
    "iso_grav_anom": 0.20,
    "iso_grav_anom_slope": 0.15,
    "depth_to_base_surf": 0.05,
    "ieq_n100a15": 0.05,
}
COLLAR_PX = 3  # keep dots off mapped faults (writer rule) -> off-catalogue dots
TILE_PX = 5    # decimation tile; one candidate dot per tile
N_DOTS_TARGET = 40_000  # final dot budget (sparse -> low forward overlap with dot fields)


def rank_normalize(a, valid):
    a = np.asarray(a, np.float64)
    m = np.isfinite(a) & valid
    out = np.zeros(a.shape, np.float64)
    if int(m.sum()) < 2:
        return out
    vals = a[m]
    order = np.argsort(vals, kind="stable")
    ranks = np.empty(vals.size, np.float64)
    ranks[order] = np.arange(vals.size, dtype=np.float64)
    uniq, inv, cnt = np.unique(vals[order], return_inverse=True, return_counts=True)
    if (cnt > 1).any():
        means = np.bincount(inv, weights=ranks[order]) / cnt
        ranks[order] = means[inv]
    out[m] = ranks / max(vals.size - 1, 1)
    return out


def build_surface(g):
    with rasterio.open(FEATURES_TIF) as src:
        bands = {name: src.read(idx).astype(np.float64) for name, idx in BANDS.items()}
    fp = g.footprint
    stack = {}
    for name, a in bands.items():
        a[~np.isfinite(a)] = np.nan
        stack[name] = rank_normalize(a, fp)
    surface = np.zeros(fp.shape, np.float64)
    for name, w in WEIGHTS.items():
        surface = surface + w * stack[name]
    surface = np.where(fp, np.clip(surface, 0.0, 1.0), 0.0).astype(np.float32)
    return surface, bands


def local_registry_index():
    """Index the registry rasters that are actually present locally
    (docs/downloads) for a partial, clearly-scoped uniqueness measurement."""
    records = []
    dl = ROOT / "docs" / "downloads"
    for path in sorted(dl.glob("*.tif")):
        # Exclude this lane's own artifacts (current and any superseded
        # versions) so the registry comparison is against other lanes only.
        if path.name.startswith("gems86-blindgeothermal-dilation"):
            continue
        records.append(
            dict(
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                bytes=path.stat().st_size,
                cache_file=str(path),
                sources=[path.name],
                repo_first="docs/downloads",
            )
        )
    return dict(
        owner="local-partial",
        rasters=records,
        n_unique_grid_rasters=len(records),
        scope="Locally present registry rasters only (docs/downloads); not organizer-complete.",
    )


def uniqueness_measure(candidate, g, index, exclude_path=None):
    # Never compare the candidate against itself (self-match => rho=1.0,
    # overlap=1.0, a measurement artifact, not duplication).
    records = [r for r in index["rasters"]
               if exclude_path is None or Path(r["cache_file"]).resolve()
               != Path(exclude_path).resolve()]
    index = dict(index)
    index["rasters"] = records
    rows = uniq.compare_array_to_registry(
        candidate, index, g.footprint,
        file_sha256=hashlib.sha256(np.ascontiguousarray(candidate).tobytes()).hexdigest(),
        expected_grid=(g.shape, g.crs, g.transform),
    )
    return uniq.two_phase_summary(
        rows["rows"], int(g.footprint.sum()),
        expected_rasters=len(index["rasters"]),
    )


def holdout_dti(dots, g):
    folds = instrument.build(g.footprint, g.catalogue)
    return instrument.score_binary(dots, folds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="docs/downloads")
    ap.add_argument("--name", default=None)
    ap.add_argument("--note", default=None)
    ap.add_argument("--skip-holdout", action="store_true")
    ap.add_argument("--skip-registry", action="store_true")
    a = ap.parse_args()

    t0 = time.time()
    g = load_grid(BRIDGE)
    surface, bands = build_surface(g)

    # Off-catalogue collar: no dots on/near mapped faults (writer rule).
    from scipy import ndimage as ndi
    catalogue_collar = ndi.binary_dilation(g.catalogue, iterations=COLLAR_PX)
    allowed = g.footprint & ~catalogue_collar

    # Decimate to sparse dots: one dot per TILE_PX x TILE_PX tile, ranked by
    # expected credit (convolution with the triangular kernel).
    from gems57 import emit as emit_mod
    ranked, _ek = emit_mod.emit_decimated(surface, allowed, tile_px=TILE_PX)
    n_dots_target = int(N_DOTS_TARGET)
    dots = emit_mod.emit_prefix(ranked, n_dots_target).astype(bool)
    dots = dots & allowed
    print(f"surface max {float(surface.max()):.4f}; dots {int(dots.sum())}; target {n_dots_target}", flush=True)

    pred = dots.astype(np.float32)

    # --- format validation via the shared fail-closed writer ----------------
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()[:8]
    name = a.name or f"gems86-blindgeothermal-dilation-{int(dots.sum())}d-{stamp}-{digest}-zeros"
    note = (a.note
            or "Blind off-catalogue geothermal propensity (dilation+TC+gravity+basement); dots "
               "off mapped faults. Format-valid; see run card.")
    assert len(name) <= 140, len(name)
    assert len(note) <= 140, len(note)
    out = ROOT / a.out_dir / f"{name}.tif"
    receipt = write_submission(out, pred, BRIDGE / "sample_submission.tif", g.footprint,
                               note=note, name=name, catalogue=g.catalogue,
                               metadata=dict(
                                   lane="gems86-blindgeothermal",
                                   method="deterministic geophysical propensity surface (no model fit)",
                                   bands=BANDS,
                                   weights=WEIGHTS,
                                   collar_px=COLLAR_PX,
                                   tile_px=TILE_PX,
                                   dots=int(dots.sum()),
                                   verdict="format-valid; uniqueness/holdout measured below",
                               ))
    print("WRITTEN", out, receipt["sha256"])
    print("format validation:", receipt["validator"]["all_checks_passed"],
          receipt["validator"]["checks"])

    card = dict(
        evidence_class="RUN-CARD",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        file=out.name,
        sha256=receipt["sha256"],
        bytes=receipt["bytes"],
        submission_name=name,
        note=note,
        note_chars=len(note),
        format=receipt["validator"],
        method=dict(
            hypothesis="Blind / off-catalogue geothermal faults (missing from the USGS/INGENIOUS "
                       "catalogue) express as localized geodetic dilatation, radiometric total-count "
                       "alteration, gravity density-contrast boundaries and deep sedimentary cover; "
                       "they are NOT close to mapped traces, so a catalogue-driven surface is the wrong target.",
            mechanism="Rank-normalize geod_dilaterate, tc (GeoDAWN Total Count), iso_grav_anom, "
                      "iso_grav_anom_slope, depth_to_base_surf, ieq_n100a15 over the footprint; average "
                      "with fixed weights; remove a 3 px collar around mapped faults; emit one dot per "
                      f"{TILE_PX}x{TILE_PX} px tile ranked by triangular-kernel expected credit.",
            layers=["training_features.tif bands 6, 5, 8, 13, 15, 17; existing_faults.tif catalogue; "
                    "sample_submission.tif footprint"],
            physical_signature="geodetic dilatation + radiometric alteration + gravity boundary + deep basement",
            why_off_catalogue="Catalogue traces are masked from scoring; new geothermal faults are expected "
                              "blind/off-catalogue. Distance-to-visible-fault cannot discover them.",
            differs_from_repo="Every GEMSDOE86 lane uses distance-to-catalogue / tip continuation / "
                              "snap-to-catalogue as its primary driver; this lane uses none of them.",
            non_fault_mimic="Shallow alluvial/radionuclide or sedimentation patterns can elevate TC and "
                            "basement depth without a fault (leakage canary: no truth fit, so no leakage)."
        ),
        holdout_dti=None,
        uniqueness=None,
        verdict="format-valid; not organizer-confirmed; weekly slot not used",
        submission_slots_used=0,
    )

    # --- holdout (HOLDOUT-DTI) ---------------------------------------------
    if not a.skip_holdout:
        print("running holdout evaluation...", flush=True)
        hd = holdout_dti(dots, g)
        card["holdout_dti"] = hd
        print("HOLDOUT-DTI:", json.dumps(hd, indent=1))

    # --- uniqueness vs locally present registry rasters --------------------
    if not a.skip_registry:
        index = local_registry_index()
        card["registry_scoped"] = index["scope"]
        card["registry_rasters_checked"] = len(index["rasters"])
        if index["rasters"]:
            um = uniqueness_measure(pred, g, index, exclude_path=out)
            card["uniqueness"] = um
            print("UNIQUENESS:", json.dumps(um, indent=1)[:2000])

    card_path = out.with_suffix(".json")
    card_path.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print("RUN CARD", card_path)
    print("elapsed_s", round(time.time() - t0, 1))
    return card


if __name__ == "__main__":
    main()
