"""Tomography projections must never silently become holdout clearance."""
import json
from pathlib import Path

import pytest

from scripts.audit_release import archived_holdout

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "holdout_kind": "h86m_lt_unvalidated",
    "context": "docs/evidence/h86m-lt-current-disposition.json",
}


def disposition():
    return json.loads((ROOT / CONFIG["context"]).read_text())


def test_lt_is_unvalidated_not_a_zero_score():
    result = archived_holdout(CONFIG, disposition())
    assert result["status"] == "NOT_VALIDATED_FOR_THIS_VARIANT"
    assert result["evidence_class"] == "NO-HOLDOUT-DTI"
    assert result["value"] is result["ci95"] is result["withheld_positives"] is None
    assert "buffered whole-segment" in result["caveat"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("verdict", "promote"),
        ("historical_lane_verdict", "negative"),
        ("safe_to_submit", True),
        ("approved_for_weekly_slot", True),
        ("submission_slots_used", 1),
        ("holdout_dti", {"value": 0.5}),
        ("artifact", "unreviewed"),
    ],
)
def test_lt_current_disposition_cannot_launder_projections_or_authorization(key, value):
    context = disposition()
    context[key] = value
    with pytest.raises(ValueError, match="current disposition"):
        archived_holdout(CONFIG, context)
