"""Read-only consistency audit of the current run card + published TIF.

HISTORY / BUG FIXED: the previous version wrote a stale 'no candidate'
preflight over docs/evidence/run-card.json, destroying the lane run card
if run after lane86 completed, and its text contradicted the dashboard.
This version NEVER overwrites the run card; the CLI writes a separate
docs/evidence/preflight-audit.json.
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
    """Return the CURRENT run card after verifying it against the TIF on disk."""
    card = json.loads((ROOT / 'docs/evidence/run-card.json').read_text())
    tif = ROOT / card['submission_file']
    sha = hashlib.sha256(tif.read_bytes()).hexdigest() if tif.is_file() else None
    checks = {
        'shared_template_hashes_match': check_pins(),
        'tif_present': tif.is_file(),
        'tif_sha_matches_run_card': sha == card['raster_sha256'],
        'note_le_140_chars': len(card['note']) <= 140,
        'verdict_is_negative': card['verdict'] == 'negative',
        'not_submission_ready': card['submission_ready'] is False,
        'not_approved_for_weekly_slot': card['approved_for_weekly_slot'] is False,
        'holdout_labelled': card['holdout_dti']['evidence_class'] == 'HOLDOUT-DTI',
        'holdout_does_not_beat_incumbent': card['holdout_dti']['beats_incumbent'] is False,
    }
    # H86-1 parallel lane (PR #9), embedded at merge: verify it too, read-only.
    h86 = card.get('parallel_lane_h86_1')
    if h86:
        tif86 = ROOT / h86['raster']['path']
        sha86 = hashlib.sha256(tif86.read_bytes()).hexdigest() if tif86.is_file() else None
        checks.update({
            'h86_1_tif_present': tif86.is_file(),
            'h86_1_tif_sha_matches_card': sha86 == h86['raster_sha256'],
            'h86_1_note_le_140_chars': len(h86['note']) <= 140,
            'h86_1_verdict_is_negative': h86['verdict'] == 'negative',
            'h86_1_not_submission_ready': h86['submission_ready'] is False,
            'h86_1_holdout_labelled': h86['holdout_dti']['evidence_class'] == 'HOLDOUT-DTI',
            'h86_1_validator_pass': h86['validator']['status'] == 'PASS',
            'crosslane_not_duplicate': card.get('crosslane_h86_1_vs_h86_rmrb', {}).get('duplicate_by_literal_gates') is False,
        })
    return dict(run_card=card, audit_checks=checks, all_audit_checks_passed=all(checks.values()),
                verdict=card['verdict'], submission_ready=False)


if __name__ == '__main__':
    result = run()
    (ROOT / 'docs/evidence/preflight-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    (ROOT / 'docs/evidence/audit_check.json').write_text(json.dumps(
        dict(checks=result['audit_checks'], all_checks_passed=result['all_audit_checks_passed'],
             submission_ready=False, verdict=result['verdict'],
             raster_sha256=result['run_card']['raster_sha256'],
             meaning='Read-only cross-verification of the merged two-lane run card against both TIF byte sets; both verdicts negative.'), indent=2) + '\n')
    print(json.dumps(result['audit_checks'], indent=2))
    sys.exit(0 if result['all_audit_checks_passed'] else 1)
