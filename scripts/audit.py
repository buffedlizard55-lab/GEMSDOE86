"""Automated inspection: re-verify the run card against bytes on disk.

No human inspector and no optimistic defaults. This recomputes, from the
serialized candidate TIFF, the SHA256 and every local format/range check via
the unmodified shared validator, confirms the shared template pins, and
checks that the run card's verdict is consistent with its own gates
(fail-closed: inconsistency, missing files or hash drift raise).
"""
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
    from gems57.validate import validate

    checks = {'shared_template_hashes_match': check_pins()}
    card_path = ROOT / 'docs/evidence/run-card.json'
    card = json.loads(card_path.read_text())
    raster = card.get('raster') or {}
    tif = ROOT / (raster.get('path') or '')
    sample = ROOT / 'data/sample_submission.tif'
    faults = ROOT / 'data/existing_faults.tif'
    checks['grid_inputs_present'] = sample.is_file() and faults.is_file()
    checks['candidate_tif_present'] = tif.is_file()
    if checks['grid_inputs_present']:
        with sample.open('rb') as stream:
            checks['sample_mirror_sha_matches'] = hashlib.file_digest(stream, 'sha256').hexdigest() == grid.SHA256_SAMPLE_SUBMISSION
        with faults.open('rb') as stream:
            checks['fault_mirror_sha_matches'] = hashlib.file_digest(stream, 'sha256').hexdigest() == grid.SHA256_EXISTING_FAULTS
    if checks['candidate_tif_present']:
        checks['candidate_sha_matches_card'] = (
            hashlib.sha256(tif.read_bytes()).hexdigest() == card.get('raster_sha256'))
    if checks['candidate_tif_present'] and checks['grid_inputs_present']:
        with rasterio.open(sample) as s:
            foot = np.isfinite(s.read(1))
        with rasterio.open(faults) as f:
            cat = (f.read(1) > 0) & foot
        val = validate(tif, footprint=foot, catalogue=cat)
        checks['candidate_validator_all_pass'] = bool(val['all_checks_passed'])
        checks['candidate_dots_match_card'] = val['emitted_positive_pixels'] == raster.get('dots')
        checks['no_nan_no_inf_allfinite'] = val['n_nan'] == 0 and val['n_infinite'] == 0
        checks['values_in_0_1'] = val['min'] >= 0.0 and val['max'] <= 1.0
    gates = card.get('gates') or {}
    science_ready = bool(gates.get('canary_no_leakage_block')
                         and gates.get('beats_best_comparable_control_ci')
                         and gates.get('surface_rho_le_0p90_accessible')
                         and gates.get('dot_overlap_le_0p70_dotfields')
                         and gates.get('validator_all_checks_passed'))
    checks['verdict_consistent_with_gates'] = (
        card.get('submission_ready') == science_ready
        and card.get('verdict') == ('promote' if science_ready else 'negative'))
    checks['note_le_140_chars'] = len(card.get('note') or '') <= 140
    checks['holdout_labelled'] = (card.get('holdout_dti') or {}).get('evidence_class') == 'HOLDOUT-DTI'
    audit = dict(checks=checks, all_checks_passed=bool(all(checks.values())),
                 submission_ready=card.get('submission_ready'), verdict=card.get('verdict'),
                 raster_sha256=card.get('raster_sha256'),
                 meaning=('all_checks_passed means the card honestly describes the bytes on disk. '
                          'submission_ready is the separate scientific gate verdict and is False '
                          'for this negative candidate: format-valid is NOT submittable.'))
    (ROOT / 'docs/evidence/audit_check.json').write_text(json.dumps(audit, indent=2) + '\n')
    # Back-compatible return shape for tests/callers: card fields + audit.
    return {**card, 'preflight_checks': checks, 'audit': audit}


if __name__ == '__main__':
    out = run()
    print(json.dumps(out['audit'], indent=2))
    raise SystemExit(0 if out['audit']['all_checks_passed'] else 1)
