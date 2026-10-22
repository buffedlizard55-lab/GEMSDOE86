"""Reproducible preflight. Missing evidence is a negative result, never a PASS."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))

RUN_CARD_SCHEMA_VERSION = 2
EVALUATOR_VERSION = 'gems57-pooled-hide-v2'


def check_pins():
    pin = json.loads((ROOT / 'research/template_pin.json').read_text())
    return all((ROOT / p).is_file() and hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
               for p, h in pin['files'].items())


def _run_card(checks, input_grid):
    """Build the protocol-shaped negative card when no candidate exists.

    Nulls mean "not measured", not zero, not cleared, and not a pass.  This is
    deliberately fail-closed: format and input-grid checks cannot promote a
    prediction in the absence of a lane, feature cache, registry, and holdout.
    """
    blockers = [
        'No single method paragraph/lane was specified in the supplied prompt.',
        'The shared cached feature stack is not present in this checkout or in the pinned upstream trees; no replacement stack was built.',
        'No complete, pinned cross-lane raster registry was supplied or reconstructed.',
        'No feature-alone leakage canary or buffered segment hide-and-recover experiment was run.',
        'No comparable current-best pooled HOLDOUT-DTI with paired spatial CI was established.',
        'No candidate surface or final dots exist; uniqueness and serialized-raster validation are untested.',
        'No organizer submission receipt or authenticated weekly-slot quota was obtained.'
    ]
    return dict(
        schema_version=RUN_CARD_SCHEMA_VERSION,
        generated_utc=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
        hypothesis='Not selected: the required lane/method paragraph is absent.',
        mechanism='None evaluated; ranked ideas in research/REVIEW.md are preregistration only.',
        non_fault_mimic='Not applicable until an authorized method is selected; candidate-specific mimics are documented per hypothesis.',
        holdout_dti=dict(
            evidence_class='HOLDOUT-DTI', status='NOT_RUN',
            evaluator_version=EVALUATOR_VERSION,
            withheld_positive_pixels=None, value=None, ci95=None,
            paired_difference_vs_best=None),
        correlation_overlap_vs_registry=dict(
            evidence_class='REGISTRY-MEASUREMENT', status='NOT_RUN_NO_CANDIDATE',
            complete_registry_scan=False,
            surface_rank_correlation_max=None,
            surface_dots_within_3px_max=None,
            final_dots_within_3px_max=None,
            duplicate_stop_triggered=None),
        raster_sha256=None,
        validator=dict(
            evidence_class='SERIALIZED-RASTER-VALIDATION', status='NOT_RUN_NO_CANDIDATE',
            no_nan_inside_footprint=None,
            values_in_0_1=None,
            single_band_float32=None,
            crs_matches_sample=None,
            shape_matches_sample=None,
            transform_matches_sample=None,
            crs_shape_transform_match=None),
        submission_name=None,
        note='No candidate generated; lane, feature cache, complete registry and comparable baseline are absent.',
        verdict='negative',
        submission_ready=False,
        downloadable_submission_tif=False,
        experiments_run=0,
        preflight_checks=checks,
        input_grid=input_grid,
        blockers=blockers)


def run():
    import numpy as np
    import rasterio
    from gems57 import grid

    checks = {'shared_template_hashes_match': check_pins()}
    details = {}
    sample = ROOT / 'data/sample_submission.tif'
    faults = ROOT / 'data/existing_faults.tif'
    checks['grid_inputs_present'] = sample.is_file() and faults.is_file()
    if checks['grid_inputs_present']:
        with sample.open('rb') as stream:
            checks['sample_mirror_sha_matches'] = hashlib.file_digest(stream, 'sha256').hexdigest() == grid.SHA256_SAMPLE_SUBMISSION
        with faults.open('rb') as stream:
            checks['fault_mirror_sha_matches'] = hashlib.file_digest(stream, 'sha256').hexdigest() == grid.SHA256_EXISTING_FAULTS
        with rasterio.open(sample) as s, rasterio.open(faults) as f:
            foot = np.isfinite(s.read(1)) & (s.read_masks(1) > 0)
            checks['input_grids_match'] = (
                s.count == f.count == 1 and s.shape == f.shape == grid.SHAPE
                and s.crs == f.crs == rasterio.crs.CRS.from_epsg(grid.EPSG)
                and s.transform == f.transform == grid.TRANSFORM)
            details = dict(
                shape=list(s.shape), crs=str(s.crs),
                transform=list(s.transform)[:6],
                footprint_pixels=int(foot.sum()),
                organizer_authenticated=False)

    card = _run_card(checks, details)
    (ROOT / 'docs/evidence/run-card.json').write_text(
        json.dumps(card, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return card


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
