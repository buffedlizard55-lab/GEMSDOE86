"""Publication repair must preserve the failed lane, never promote its evidence."""
import copy
import json
from pathlib import Path

import pytest

from scripts.audit_release import archived_holdout

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {"holdout_kind": "h86l_fmc", "context": "docs/evidence/h86l-fmc-run-card.json"}


def archive():
    return json.loads((ROOT / CONFIG["context"]).read_text())


def test_registered_fmc_is_explicitly_leakage_suspect():
    result = archived_holdout(CONFIG, archive())
    assert result["status"] == "ARCHIVED_LEAKAGE_SUSPECT_NOT_PROMOTION_EVIDENCE"
    assert result["value"] == 0.0
    assert result["ci95"] == [0.0, 0.0]
    assert result["withheld_positives"] == 11321
    assert "not fold-visible" in result["design"]
    assert "does not cure" in result["caveat"]


@pytest.mark.parametrize("field,value", [
    ("verdict", "promote"), ("safe_to_submit", True),
    ("approved_for_weekly_slot", True), ("submission_slots_used", 1),
    ("lane_id", "other"),
])
def test_fmc_archive_cannot_be_rebranded(field, value):
    card = archive()
    card[field] = value
    with pytest.raises(ValueError):
        archived_holdout(CONFIG, card)


@pytest.mark.parametrize("mutation", [
    {"evidence_class": "HOLDOUT-DTI"},
    {"candidate": {"dti": float("nan")}},
    {"candidate": {"ci95": [1.0, 0.0]}},
    {"candidate": {"withheld_positive_pixels": True}},
    {"candidate": {"evaluator_version": "unverified"}},
])
def test_fmc_archive_rejects_laundered_or_invalid_holdout(mutation):
    card = copy.deepcopy(archive())
    if "candidate" in mutation:
        card["holdout"]["candidate"].update(mutation["candidate"])
    else:
        card["holdout"].update(mutation)
    with pytest.raises(ValueError):
        archived_holdout(CONFIG, card)


def test_every_download_is_registered_in_both_indexes():
    inventory = json.loads((ROOT / "docs/evidence/download-inventory.json").read_text())
    index = json.loads((ROOT / "registry/artifact_cards.json").read_text())
    published = {p.stem for p in (ROOT / "docs/downloads").glob("*.tif")}
    assert published == {Path(a["file"]).stem for a in inventory["artifacts"]}
    assert published == {a["stem"] for a in index["artifacts"]}


def test_generated_home_preserves_h86l_audit_anchor_without_uniqueness_claim():
    from scripts.build_site import render
    home = render(ROOT)['docs/index.html']
    assert 'id="h86l-fmc"' in home
    panel = home.split('id="h86l-fmc"', 1)[1].split('</section>', 1)[0]
    assert 'DO NOT SUBMIT' in panel
    assert 'not fold-safe hide-and-recover evidence' in panel
    assert 'NEWEST UNIQUE TIFF' not in panel
    assert 'evidence/h86l-fmc-run-card.json' in panel
