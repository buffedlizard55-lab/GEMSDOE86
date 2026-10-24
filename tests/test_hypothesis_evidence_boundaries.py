"""Planning evidence safeguards, not model or holdout validation."""
import json
from pathlib import Path

PLAN = json.loads((Path(__file__).resolve().parents[1] / 'registry/h86c_hypotheses.json').read_text())


def test_planning_cannot_be_read_as_measured_improvement():
    assert 'untested hypotheses' in PLAN['evidence_boundary']
    assert PLAN['experiments_run'] == 0
    for h in PLAN['hypotheses']:
        assert h['holdout_dti'] is None
        assert h['ci95'] is None
        assert h['status'].startswith('NOT_RUN')


def test_external_sources_require_actual_obtainability_check():
    for h in PLAN['hypotheses']:
        if h['external_data_required']:
            assert h['obtainability'].startswith('NOT_VERIFIED_THIS_SESSION')
            assert h['data_readiness'].startswith('NOT_VIABLE_YET')


def test_magnetic_minimum_curvature_sign_and_nonunique_interpretation():
    signature = PLAN['hypotheses'][2]['signature']
    assert 'positive cross-strike second derivative of rtp' in signature
    assert 'negative second derivative of -rtp' in signature
    assert 'not diagnostic' in signature
    # f(x)=x^2 is a trough; its negation is a peak, not a trough.
    values = [1, 0, 1]
    assert values[0] - 2 * values[1] + values[2] > 0
    assert -values[0] + 2 * values[1] - values[2] < 0


def test_uncertain_band_semantics_not_silently_assumed():
    assert 'Do not use tc until' in PLAN['hypotheses'][1]['signature']
    assert 'Exclude tc until' in PLAN['hypotheses'][3]['signature']
    assert 'must not be treated as independent' in PLAN['hypotheses'][0]['why_unmapped']
