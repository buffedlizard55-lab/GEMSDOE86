"""The H86L-FMC audit artifact is registered without upgrading its verdict."""
import json
from pathlib import Path

from scripts import audit_release

ROOT = Path(__file__).resolve().parents[1]
STEM = "gems86-h86l-fmc-minconsensus-37654dots-20261025T161053Z-zeros"


def test_h86l_fmc_is_registered_as_negative_and_leakage_suspect():
    inventory = audit_release.strict_json(ROOT / "docs/evidence/download-inventory.json")["artifacts"]
    config = audit_release.strict_json(ROOT / "registry/artifact_cards.json")["artifacts"]
    rows = [row for row in inventory if Path(row["file"]).stem == STEM]
    configs = [row for row in config if row["stem"] == STEM]
    assert len(rows) == len(configs) == 1
    assert rows[0]["status"].startswith("DO NOT SUBMIT")
    assert rows[0]["approved_for_weekly_slot"] is False
    assert configs[0]["holdout_kind"] == "h86l_fmc"

    run_card = audit_release.strict_json(ROOT / configs[0]["context"])
    holdout = audit_release.archived_holdout(configs[0], run_card)
    assert holdout["evidence_class"] == "HOLDOUT-DTI"
    assert holdout["status"] == "ARCHIVED_LEAKAGE_SUSPECT_NOT_PROMOTION_EVIDENCE"
    assert holdout["evaluator_version"] == "gems57-pooled-hide-v2"
    assert holdout["withheld_positives"] == 11_321
    assert holdout["value"] == 0.0
    assert holdout["ci95"] == [0.0, 0.0]
    assert "fleet-ancestry leakage" in holdout["caveat"]
    assert run_card["verdict"] == "negative"
    assert run_card["safe_to_submit"] is False
    assert run_card["approved_for_weekly_slot"] is False
    assert run_card["submission_slots_used"] == 0


def test_h86l_holdout_cannot_be_relabelled_or_given_slot_authority():
    inventory = audit_release.strict_json(ROOT / "docs/evidence/download-inventory.json")["artifacts"]
    config = next(row for row in audit_release.strict_json(ROOT / "registry/artifact_cards.json")["artifacts"]
                  if row["stem"] == STEM)
    run_card = audit_release.strict_json(ROOT / config["context"])
    for field, value in (("verdict", "promote"), ("submission_slots_used", 1)):
        changed = dict(run_card)
        changed[field] = value
        try:
            audit_release.archived_holdout(config, changed)
        except ValueError:
            pass
        else:
            raise AssertionError(f"H86L-FMC accepted invalid {field}={value!r}")
