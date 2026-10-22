"""Reproducible preflight. Missing evidence is a negative result, never a PASS."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))


def check_pins():
    pin = json.loads((ROOT / 'research/template_pin.json').read_text())
    return all((ROOT / p).is_file() and hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
               for p, h in pin['files'].items())


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
            checks['input_grids_match'] = (s.count == f.count == 1 and s.shape == f.shape == grid.SHAPE
                and s.crs == f.crs == rasterio.crs.CRS.from_epsg(grid.EPSG)
                and s.transform == f.transform == grid.TRANSFORM)
            details = dict(shape=list(s.shape), crs=str(s.crs), transform=list(s.transform)[:6],
                           footprint_pixels=int(foot.sum()), organizer_authenticated=False)
    # Explicit blockers: existence alone must never turn these into a science PASS.
    blockers = [
        'No single method paragraph/lane was specified in the supplied prompt.',
        'Shared cached feature stack referenced upstream is not present; no replacement stack was built.',
        'No complete, pinned cross-lane raster registry was supplied or reconstructed.',
        'No feature-alone leakage canary or buffered segment hide-and-recover experiment was run.',
        'No comparable current-best pooled HOLDOUT-DTI with paired spatial CI was established.',
        'No candidate surface or final dots exist; uniqueness and raster validation are untested.'
    ]
    card = dict(hypothesis='H86 provisional: radiometric mixing-residual boundary (not lane-authorized)',
        mechanism='Residual K/Th variation after local lithologic mixing regression, gated by magnetic edge persistence.',
        non_fault_mimic='Lithologic contacts and weathering fronts',
        holdout_dti=dict(evidence_class='HOLDOUT-DTI', status='NOT_RUN', evaluator_version='gems57-pooled-hide-v2',
                         withheld_positives=None, value=None, ci95=None),
        correlation_overlap_vs_registry=dict(status='NOT_RUN', surface=None, final_dots=None, complete=False),
        raster_sha256=None,
        validator=dict(status='NOT_RUN_NO_CANDIDATE', no_nan_inside_footprint=None, values_in_0_1=None,
                       crs_shape_transform_match=None),
        submission_name=None, note='No candidate generated: lane, cached features, complete registry and comparable holdout baseline are missing.',
        verdict='negative', submission_ready=False, experiments_run=0,
        preflight_checks=checks, input_grid=details, blockers=blockers)
    (ROOT / 'docs/evidence/run-card.json').write_text(json.dumps(card, indent=2, allow_nan=False)+'\n')
    return card


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
