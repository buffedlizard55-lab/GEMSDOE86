"""Tomography projections must never silently become holdout clearance."""
import json
from pathlib import Path
import pytest
from scripts.audit_release import archived_holdout

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {'holdout_kind': 'h86m_lt_unvalidated',
          'context': 'docs/evidence/h86m-lt-run-card.json'}

def card():
    return json.loads((ROOT / CONFIG['context']).read_text())

def test_lt_is_unvalidated_not_a_zero_score():
    result = archived_holdout(CONFIG, card())
    assert result['status'] == 'NOT_VALIDATED_FOR_THIS_VARIANT'
    assert result['value'] is result['ci95'] is result['withheld_positives'] is None
    assert 'Pearson' in result['caveat']

@pytest.mark.parametrize('key,value', [('verdict', 'promote'), ('safe_to_submit', True),
    ('approved_for_weekly_slot', True), ('submission_slots_used', 1),
    ('holdout_dti', {'value': 0.5}), ('lane', 'unreviewed')])
def test_lt_cannot_launder_projections_or_authorization(key, value):
    context = card()
    context[key] = value
    with pytest.raises(ValueError, match='must remain unvalidated'):
        archived_holdout(CONFIG, context)
