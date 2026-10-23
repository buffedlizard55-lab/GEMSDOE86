"""Check registry-diagnostic reproduction, allowing only last-bit rho drift.

All SHA, identities, counts, gate booleans, overlap and scope must match exactly.
Only Spearman float fields allow 2e-14 absolute error across BLAS/CPU builds.
This does not recompute or change a uniqueness gate or its thresholds.
"""
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FILE = 'docs/evidence/inherited-registry-check.json'
RHO_KEYS = {'worst_spearman_full_footprint', 'spearman_full_footprint'}


def differences(expected, actual, path=''):
    if type(expected) is not type(actual):
        return [path + ': type differs']
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            return [path + ': keys differ']
        return [error for key in expected for error in differences(expected[key], actual[key], path + '/' + key)]
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return [path + ': length differs']
        return [error for i, (x, y) in enumerate(zip(expected, actual)) for error in differences(x, y, path + '/' + str(i))]
    if path.rsplit('/', 1)[-1] in RHO_KEYS and isinstance(expected, float):
        return [] if math.isclose(expected, actual, rel_tol=0, abs_tol=2e-14) else [path + ': rho differs beyond CPU rounding tolerance']
    return [] if expected == actual else [path + ': value differs']


if __name__ == '__main__':
    expected = json.loads(subprocess.check_output(['git', 'show', 'HEAD:' + FILE], cwd=ROOT))
    actual = json.loads((ROOT / FILE).read_text())
    errors = differences(expected, actual)
    if errors:
        raise SystemExit('\n'.join(errors))
    print('PASS: registry diagnostic reproduced (only last-bit rho tolerance; all gates and identities exact)')
