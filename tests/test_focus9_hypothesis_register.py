"""Focus-9 proposal register must count only well-formed, repository-screened ideas."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "registry/focus9_novel_hypotheses_20261028.json"


def test_focus9_ranked_hypotheses_have_complete_semantic_fields_and_stay_unrun():
    document = json.loads(REGISTER.read_text())
    hypotheses = document["ranked_hypotheses"]
    assert 3 <= len(hypotheses) <= 5
    assert [item["rank"] for item in hypotheses] == list(range(1, len(hypotheses) + 1))
    assert len({item["id"] for item in hypotheses}) == len(hypotheses)

    required = {
        "name", "status", "expected_dti_improvement", "implementation_cost", "layers",
        "targeted_physical_signature", "why_it_may_find_uncatalogued_faults",
        "named_non_fault_mimic", "difference_from_repository_methods",
        "official_free_sources", "availability_decision",
    }
    for item in hypotheses:
        assert required <= item.keys()
        assert item["status"] == "PROPOSED_NOT_RUN"
        assert item["layers"] and all(isinstance(layer, str) for layer in item["layers"])
        assert item["official_free_sources"]
        assert isinstance(item["expected_dti_improvement"], str)
        assert isinstance(item["implementation_cost"], str)


def test_inherited_hypothesis_drafts_are_not_misrepresented_as_novel_ranked_items():
    document = json.loads(REGISTER.read_text())
    dispositions = document["review_disposition"]
    drafts = {item["id"]: item for item in dispositions["unranked_drafts_not_counted"]}
    assert dispositions["counted_ranked_hypotheses"] == len(document["ranked_hypotheses"]) == 3
    assert drafts["F9N-4_STEPPED_SCarp_GEOMORPHIC_INDEX"]["status"] == "REQUIRES_SCHEMA_CORRECTION_AND_NOVELTY_RESCREEN"
    assert drafts["F9N-5_GROUNDWATER_SPRING_VEGETATION_ALIGNMENT_INDEX"]["status"] == "EXCLUDED_AS_REPEAT"
    assert "H86J_LSI_REVIEW.md" in json.dumps(document["novelty_screen"]["excluded_as_repeats_or_executed"])
