"""Research-priority and source-availability boundaries; not model validation."""
from pathlib import Path

from scripts.audit_release import strict_json

ROOT = Path(__file__).resolve().parents[1]


def test_standalone_spbt_is_historical_negative_and_laplace_extension_remains_distinct():
    plan = strict_json(ROOT / "registry/untried_hypotheses_20261024.json")
    tested = {row["id"]: row for row in plan["previously_tested_methods"]}
    base = tested["H86E-SPBT-BASE"]
    extension = next(row for row in plan["hypotheses"] if row["id"] == "H86E-SPBT-LAPLACE")

    assert base["status"] == "TESTED_NEGATIVE_AS_STANDALONE"
    assert "without Laplace" in base["name"]
    assert base["holdout_dti"]["evidence_class"] == "HOLDOUT-DTI"
    assert base["holdout_dti"]["evaluator_version"] == "gems57-pooled-hide-v2"
    assert base["holdout_dti"]["withheld_positive_pixels"] == 11321
    assert base["holdout_dti"]["ci95"] == [0.0143, 0.0435]
    assert base["recorded_controls"][0]["ci95"] == [0.0202, 0.0438]
    for control in base["recorded_controls"]:
        assert control["evidence_class"] == "HOLDOUT-DTI"
        assert control["evaluator_version"] == base["holdout_dti"]["evaluator_version"]
        assert control["withheld_positive_pixels"] == base["holdout_dti"]["withheld_positive_pixels"]
        assert control["ci95"]
    assert "did not include" in base["implementation_scope"]

    assert extension["status"] == "UNTESTED_EXTENSION_PROTOCOL_STOP"
    assert extension["holdout_dti"] is extension["ci95"] is None
    assert "did not include" in extension["signature"]
    assert "not a claim of a new standalone SPBT" in extension["difference_from_repo"]
    assert "same gravity field" in extension["expected_dti_gain"]


def test_current_queue_has_five_distinct_untried_hypotheses_with_qualitative_only_ranks():
    plan = strict_json(ROOT / "registry/untried_hypotheses_20261024.json")
    assert len(plan["hypotheses"]) == 5
    assert plan["hypotheses"][0]["id"] == "H86E-MMT"
    assert len({h["id"] for h in plan["hypotheses"]}) == 5
    for row in plan["hypotheses"]:
        assert row["holdout_dti"] is None
        assert row["ci95"] is None
        assert row["rank"] in range(1, 6)
        assert "no numeric" in row["expected_dti_gain"].lower()
        assert row["official_basis"]
        assert row["source_availability_ref"] == "docs/evidence/hypothesis-data-availability-20261024.json"


def test_external_data_is_not_called_viable_on_metadata_only_evidence():
    plan = strict_json(ROOT / "registry/untried_hypotheses_20261024.json")
    audit = strict_json(ROOT / "docs/evidence/hypothesis-data-availability-20261024.json")
    assert audit["evidence_class"] == "SOURCE-AVAILABILITY-METADATA"
    assert audit["local_checkout"]["data_training_features_tif_present"] is False
    assert audit["local_checkout"]["shared_feature_cache_present"] is False
    assert audit["local_checkout"]["data_external_directory_present"] is False
    mirror_rows = audit["github_mirror_metadata_only"]
    paleo = next(row for row in mirror_rows if row["path"].endswith("paleo_geothermal_regional.zip"))
    assert paleo["candidate"] == "H86E-HMDC"
    assert paleo["api_listed_bytes"] == 84008
    assert paleo["raw_bytes_downloaded_or_sha256_checked_here"] is False
    wcs = next(row for row in mirror_rows if row["candidate"] == "H86E-WCS")
    assert wcs["is_native_1m_dem_tile"] is False
    for row in plan["hypotheses"]:
        if row["external_data_required"]:
            assert "NOT_VIABLE" in row["data_readiness"]
            assert row["obtainability"]


def test_generated_queue_page_exposes_prior_failure_and_data_limits():
    page = (ROOT / "docs/hypotheses.html").read_text()
    assert "H86E-SPBT-BASE" in page
    assert "H86E-SPBT-LAPLACE" in page
    assert "does not validate or falsify" in page or "does not test or falsify" in page
    assert "HOLDOUT-DTI" in page
    assert "hypothesis-data-availability-20261024.json" in page
    assert "NO NEW SCIENTIFIC EXPERIMENT AUTHORIZED" in page or "PROTOCOL STOP" in page

    home = (ROOT / "docs/index.html").read_text()
    assert "this continuation generated" in home
    assert "not score causality" in home
    assert "OWNER-REPORTED" in home
    assert "DO NOT SUBMIT" in home
