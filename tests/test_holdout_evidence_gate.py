"""All archived HOLDOUT-DTI schemas need valid numbers, counts and intervals."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.audit_release import archived_holdout

ROOT = Path(__file__).resolve().parents[1]


def control(**updates):
    result = dict(withheld_positive_pixels=123, holdout_dti=0.2, holdout_ci95=[0.1, 0.3])
    result.update(updates)
    return result


CONFIG = dict(holdout_kind="gmc_control", context="synthetic-evidence.json")


@pytest.mark.parametrize("field,value", [
    ("holdout_dti", True), ("holdout_dti", -0.01), ("holdout_dti", 1.01),
    ("holdout_dti", float("nan")), ("holdout_dti", float("inf")), ("holdout_dti", "0.2"),
    ("holdout_ci95", [0.4, 0.1]), ("holdout_ci95", [0, float("inf")]),
    ("holdout_ci95", [False, 0.3]), ("holdout_ci95", [0.1]),
    ("holdout_ci95", [-0.1, 0.3]), ("holdout_ci95", [0.1, 1.1]),
    ("withheld_positive_pixels", True), ("withheld_positive_pixels", 0),
    ("withheld_positive_pixels", -1), ("withheld_positive_pixels", 1.5),
])
def test_impossible_historical_performance_fails_closed(field, value):
    with pytest.raises(ValueError, match="Invalid archived HOLDOUT-DTI"):
        archived_holdout(CONFIG, control(**{field: value}))


def test_valid_archived_evidence_and_unvalidated_variant_are_distinct():
    h = archived_holdout(CONFIG, control())
    assert h["value"] == 0.2 and h["withheld_positives"] == 123
    empty = archived_holdout({**CONFIG, "holdout_kind": "unvalidated_variant"}, {})
    assert empty["value"] is empty["ci95"] is empty["withheld_positives"] is None
    assert empty["status"] == "NOT_VALIDATED_FOR_THIS_VARIANT"


@pytest.mark.parametrize("delta,ci", [(True, [0, 0.1]), (2, [0, 0.1]), (0.1, [0.2, -0.1]),
                                     (0.1, [0, float("nan")]), (0.1, None)])
def test_paired_delta_fields_are_checked_in_every_normalized_schema(delta, ci):
    config = dict(holdout_kind="gfco_whole_components", context="synthetic-gfco.json")
    context = dict(holdout_dti=dict(evidence_class="HOLDOUT-DTI", evaluator_version="gems57-pooled-hide-v2",
        buffered_whole_components_loqo=dict(withheld_positives=123, candidate_dti=0.2, ci95=[0.1, 0.3],
            paired_delta_vs_d28=delta, paired_delta_vs_d28_ci95=ci)))
    with pytest.raises(ValueError, match="paired HOLDOUT-DTI"):
        archived_holdout(config, context)


@pytest.mark.parametrize("version", ["", None, "ORGANIZER-CONFIRMED", "gems57-pooled-hide-v2-fake"])
def test_invalid_evaluator_is_not_published_as_shared_evidence(version):
    config = dict(holdout_kind="gfco_whole_components", context="synthetic-gfco.json")
    context = dict(holdout_dti=dict(evidence_class="HOLDOUT-DTI", evaluator_version=version,
        buffered_whole_components_loqo=dict(withheld_positives=123, candidate_dti=0.2, ci95=[0.1, 0.3],
            paired_delta_vs_d28=0.01, paired_delta_vs_d28_ci95=[-0.01, 0.02])))
    with pytest.raises(ValueError, match="evaluator"):
        archived_holdout(config, context)


def test_every_existing_historical_schema_remains_valid_without_rewriting_archives():
    index = json.loads((ROOT / "registry/artifact_cards.json").read_text())
    for config in index["artifacts"]:
        path = ROOT / config["context"]
        original = path.read_bytes()
        archived_holdout(config, deepcopy(json.loads(original)))
        assert path.read_bytes() == original


@pytest.mark.parametrize("field", ["submission_ready", "safe_to_submit", "approved_for_weekly_slot"])
@pytest.mark.parametrize("value", [True, 1, 0, "false", None, [], {}])
def test_present_authorization_flags_must_be_exact_json_false(field, value):
    from scripts.audit_release import explicit_no_authorization
    assert explicit_no_authorization({field: value}) is False
    assert explicit_no_authorization({field: False}) is True
    assert explicit_no_authorization({}) is True  # legacy field absence, not permission
