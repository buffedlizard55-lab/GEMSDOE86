"""Fleet-feedback projections must not become holdout or upload clearance."""
import copy
import json
from pathlib import Path

import pytest

from scripts.audit_release import archived_holdout

ROOT = Path(__file__).resolve().parents[1]
CONFIG = dict(holdout_kind='h86m_lt_unvalidated', context='docs/evidence/h86m-lt-run-card.json')


def card():
    return json.loads((ROOT / CONFIG['context']).read_text())


def test_tomography_is_registered_without_inventing_holdout():
    result = archived_holdout(CONFIG, card())
    assert result['status'] == 'NOT_VALIDATED_FOR_THIS_VARIANT'
    assert result['value'] is result['ci95'] is result['withheld_positives'] is None
    assert 'Pearson' in result['caveat']


@pytest.mark.parametrize('field,value', [
    ('safe_to_submit', True), ('approved_for_weekly_slot', True),
    ('submission_ready', True), ('verdict', 'promote'), ('submission_slots_used', 1),
])
def test_archive_rejects_promotion(field, value):
    data = card()
    data[field] = value
    with pytest.raises(ValueError):
        archived_holdout(CONFIG, data)


@pytest.mark.parametrize('field,value', [('value', 0.33), ('ci95', [0.3, 0.4]),
    ('withheld_positives', 100), ('evaluator_version', 'invented'),
    ('status', 'PASS')])
def test_archive_rejects_fabricated_holdout(field, value):
    data = copy.deepcopy(card())
    data['holdout_dti'][field] = value
    with pytest.raises(ValueError):
        archived_holdout(CONFIG, data)
