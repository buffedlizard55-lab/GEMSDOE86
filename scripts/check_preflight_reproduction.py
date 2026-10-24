"""Compare preflight evidence exactly except validated measurement time/date.

Historical verification dates, pins, thresholds, counts and verdicts remain exact.
"""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'docs/evidence/protocol-preflight.json': (),
    'docs/evidence/protocol-run-card.json': ('correlation_overlap_vs_registry', 'universal_witness'),
}


def normalized(document, certificate_path=()):
    result = deepcopy(document)
    certificate = result
    for key in certificate_path:
        certificate = certificate[key]
    measured = datetime.fromisoformat(certificate['measured_utc'])
    if measured.utcoffset() != timedelta(0):
        raise ValueError('Measurement must have explicit UTC timezone')
    if certificate['measured_date_utc'] != measured.date().isoformat():
        raise ValueError('Measurement date differs from timestamp')
    del certificate['measured_utc']
    del certificate['measured_date_utc']
    return result


def main():
    for filename, certificate_path in FILES.items():
        expected = json.loads(subprocess.check_output(['git', 'show', 'HEAD:' + filename], cwd=ROOT))
        actual = json.loads((ROOT / filename).read_text())
        if normalized(expected, certificate_path) != normalized(actual, certificate_path):
            raise SystemExit(f'Preflight evidence changed beyond measurement timestamp: {filename}')
    print('PASS: preflight reproduced; only validated UTC measurement time/date may differ')


if __name__ == '__main__':
    main()
