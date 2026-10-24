"""Compare proof content exactly, excluding only measurement wall-clock fields."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FILES = ('docs/evidence/protocol-preflight.json', 'docs/evidence/protocol-run-card.json')


def content(record, *, run_card=False):
    result = deepcopy(record)
    witness = result['correlation_overlap_vs_registry']['universal_witness'] if run_card else result
    # Permit old archived records with a date only, but validate new timestamps.
    date = witness.pop('measured_date_utc')
    datetime.strptime(date, '%Y-%m-%d')
    stamp = witness.pop('measured_utc', None)
    if stamp is not None:
        instant = datetime.fromisoformat(stamp)
        if instant.utcoffset() != timezone.utc.utcoffset(instant) or instant.date().isoformat() != date:
            raise ValueError('Measurement timestamp must agree with date in UTC')
    return result


if __name__ == '__main__':
    for filename in FILES:
        expected = json.loads(subprocess.check_output(['git', 'show', 'HEAD:' + filename], cwd=ROOT))
        actual = json.loads((ROOT / filename).read_text())
        if content(expected, run_card=filename.endswith('run-card.json')) != content(actual, run_card=filename.endswith('run-card.json')):
            raise SystemExit(f'Proof content changed: {filename}')
    print('PASS: proof content reproduced exactly; only UTC measurement time excluded')
