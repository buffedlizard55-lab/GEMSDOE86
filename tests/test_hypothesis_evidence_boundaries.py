"""The archived preregistration remains historical; live status lives in the current queue."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = json.loads((ROOT / 'registry/h86c_hypotheses.json').read_text())


def test_archived_preregistration_cannot_be_mistaken_for_current_experiment_history():
    assert HISTORICAL["record_type"] == "historical_preregistration_snapshot"
    assert HISTORICAL["current_register"] == "registry/untried_hypotheses_20261024.json"
    assert "not a statement of current experiment history" in HISTORICAL["historical_status_note"]
    assert 'untested hypotheses' in HISTORICAL['evidence_boundary']
    assert HISTORICAL['experiments_run'] == 0
    for h in HISTORICAL['hypotheses']:
        assert h['holdout_dti'] is None
        assert h['ci95'] is None
        assert h['status'].startswith('NOT_RUN')


def test_external_sources_in_original_preregistration_require_obtainability_notes():
    for h in HISTORICAL['hypotheses']:
        if h['external_data_required']:
            assert h['obtainability'].startswith('NOT_VERIFIED_THIS_SESSION')
            assert h['data_readiness'].startswith('NOT_VIABLE_YET')


def test_magnetic_minimum_curvature_sign_and_nonunique_interpretation():
    signature = HISTORICAL['hypotheses'][2]['signature']
    assert 'positive cross-strike second derivative of rtp' in signature
    assert 'negative second derivative of -rtp' in signature
    assert 'not diagnostic' in signature
    # f(x)=x^2 is a trough; its negation is a peak, not a trough.
    values = [1, 0, 1]
    assert values[0] - 2 * values[1] + values[2] > 0
    assert -values[0] + 2 * values[1] - values[2] < 0


def test_uncertain_band_semantics_not_silently_assumed_in_historical_register():
    assert 'Do not use tc until' in HISTORICAL['hypotheses'][1]['signature']
    assert 'Exclude tc until' in HISTORICAL['hypotheses'][3]['signature']
    assert 'must not be treated as independent' in HISTORICAL['hypotheses'][0]['why_unmapped']
