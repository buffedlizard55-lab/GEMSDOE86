#!/usr/bin/env python3
"""Measure archived H86T input-label and tied-zero provenance; never fit a model.

The output is a post-hoc diagnostic tied to known input/source hashes, not a
recomputed holdout, candidate raster, or authorization. Files are first verified
against existing mirror pins. The archived card and preregistration stay intact.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import grid  # noqa: E402
from scripts.restore_data import EXTERNAL_PINS, PINS  # noqa: E402
from src.gems86.io import BANDS  # noqa: E402

ARCHIVE_COMMIT = "acff97ac9df403705b05e1b57a6a4b2585df34e9"
ARCHIVE_FEATURE_SHA256 = "b00b0832b1d6f1dc56574437086254a62abeef096a094b1920c9461e5d4da69d"
OUTPUT = ROOT / "docs/evidence/h86t-input-provenance-20261027.json"
SENTINEL = -32000


def verify(path: Path, expected: str):
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"Input SHA-256 mismatch: {path.name}")


def ksn_zero_tie(ksn, log_area, zmean, footprint):
    """Count the exact zero ties in the archived chi_ksn_norm rank input."""
    arrays = [np.asarray(x) for x in (ksn, log_area, zmean, footprint)]
    if len({a.shape for a in arrays}) != 1 or arrays[0].ndim != 2:
        raise ValueError("Expected matching 2-D chi planes and footprint")
    ksn, log_area, zmean, fp = arrays
    fp = fp.astype(bool)
    valid = fp & (ksn > SENTINEL) & (log_area > SENTINEL) & (zmean > SENTINEL)
    ties = int((fp & (~valid | (ksn <= 0))).sum())
    n = int(fp.sum())
    return dict(footprint_pixels=n, input_zero_ties=ties,
                input_zero_tie_fraction=ties / n if n else None,
                # In the original stable rank, all zeros precede positive
                # log1p(ksn) values and are ranked by row-major footprint order.
                legacy_first_zero_rank=0.0 if ties else None,
                legacy_last_zero_rank=(ties - 1) / max(n - 1, 1) if ties else None,
                corrected_all_zero_tie_rank=0.0 if ties else None)


def measure(root=ROOT):
    data = root / "data/bridge"
    native = data / "training_features.tif"
    chi = root / ".cache/external/dem10_chi_100m_i16.tif"
    for path, digest in ((native, PINS["training_features.tif"]),
                         (data / "sample_submission.tif", PINS["sample_submission.tif"]),
                         (data / "existing_faults.tif", PINS["existing_faults.tif"]),
                         (chi, EXTERNAL_PINS[chi.name])):
        verify(path, digest)
    g = grid.load_grid(data)
    with rasterio.open(native) as src:
        observed = [d.split(" - ", 1)[0].strip() if d else None for d in src.descriptions]
        if (src.shape != g.shape or src.crs != g.crs or src.transform != g.transform
                or src.count != len(BANDS) or observed != list(BANDS.values())):
            raise ValueError("Native raster grid or band identities disagree")
        descriptions = list(src.descriptions)
    with rasterio.open(chi) as src:
        if (src.shape != g.shape or src.crs != g.crs or src.transform != g.transform
                or src.count != 5 or src.descriptions[2:5] !=
                ("ksn_max_m0.9", "log10_area_m2_x1000", "zmean_m")):
            raise ValueError("Chi raster grid or required band identities disagree")
        stats = ksn_zero_tie(src.read(3), src.read(4), src.read(5), g.footprint)
    return dict(
        schema="gems86.h86t-posthoc-input-provenance.v1",
        measured_utc=datetime.now(timezone.utc).isoformat(),
        evidence_class="INPUT_AND_CODE_FORENSICS_NOT_HOLDOUT",
        archive_commit=ARCHIVE_COMMIT,
        archived_feature_source_sha256=ARCHIVE_FEATURE_SHA256,
        archived_feature_source_url=f"https://github.com/buffedlizard55-lab/GEMSDOE86/blob/{ARCHIVE_COMMIT}/src/gems86_knds/features.py",
        native_sha256=PINS["training_features.tif"], chi_sha256=EXTERNAL_PINS[chi.name],
        grid=dict(crs=str(g.crs), shape=list(g.shape), transform=list(g.transform)[:6]),
        native_band_descriptions=descriptions,
        legacy_bindings=[
            dict(legacy_feature="elev_relief", band=5, actual_identifier=BANDS[5],
                 qualification="Prior pixel audit identifies a gravity-gradient magnitude proxy, not elevation."),
            dict(legacy_feature="mt_2km_edge", band=16, actual_identifier=BANDS[16],
                 qualification="Earthquake intensity/density identifier, not 2-km magnetotelluric resistivity."),
            dict(legacy_feature="Bouguer sill veto", band=12, actual_identifier=BANDS[12],
                 qualification="Detrended elevation Laplacian, not Bouguer gravity."),
            dict(legacy_feature="grav_hg", band=18, actual_identifier=BANDS[18],
                 qualification="Prior pixel audit identifies an eastward signed gravity derivative; abs() is not its full 2-D magnitude."),
            dict(legacy_feature="rtp_tilt_grad", band=2, actual_identifier=BANDS[2],
                 qualification="Gradient magnitude of smoothed RTP, not a computed magnetic tilt."),
        ],
        chi_ksn_zero_tie=stats,
        conclusion=("The historical stable-argsort rank assigned unequal row-order ranks to tied zero inputs. "
                    "This post-hoc defect and misnamed inputs qualify the geological interpretation; "
                    "the recorded holdout numbers are not rerun or replaced. Impact on the score is unmeasured."),
        physical_override_evidence="docs/evidence/band-physics-verification-20261024.json",
        historical_run_card="docs/evidence/h86t-knds-run-card.json",
        new_model_experiments=0, new_candidate_generated=False, submission_slots_used=0,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="persist the measured, post-hoc forensic receipt")
    args = parser.parse_args(argv)
    doc = measure()
    if args.write:
        OUTPUT.write_text(json.dumps(doc, indent=2, allow_nan=False) + "\n")
    print(json.dumps(doc["chi_ksn_zero_tie"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
