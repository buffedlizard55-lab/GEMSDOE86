"""Guard the 2026-10-29 ff849f98 session: DO NOT SUBMIT, measured overlaps, embedded request."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITES = {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}


def test_run_card_is_fail_closed_with_no_candidate_or_slot():
    card = json.loads((ROOT / "docs/evidence/session-ff849f98-run-card.json").read_text())
    assert card["safe_to_submit"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert card["experiments_run"] == 0
    assert card["new_candidate_generated"] is False
    assert card["unique_tiff_requirement_satisfied"] is False
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["organizer_score_estimate"] is None
    assert card["holdout_dti"]["value"] is None
    assert len(card["note"]) <= 140, len(card["note"])


def test_overlap_measurement_matches_gate_and_scope():
    ov = json.loads((ROOT / "docs/evidence/session-ff849f98-nine-site-overlap.json").read_text())
    assert ov["gate"] == 0.70
    assert set(ov["max_forward_overlap_vs_peers"]) == SITES
    assert all(v > 0.70 for v in ov["max_forward_overlap_vs_peers"].values())
    assert not any(ov["unique_under_0p70_gate"].values())
    assert all(s["sha256_verified"] for s in ov["sites"].values())


def test_readme_embeds_the_request_exactly_and_states_the_decision():
    readme = (ROOT / "README.md").read_text()
    head = readme.split("<!-- CURRENT_REQUEST_20261029_START -->", 1)[0]
    assert "DO NOT SUBMIT" in head
    assert "not estimable" in head
    block = readme.split("<!-- CURRENT_REQUEST_20261029_START -->", 1)[1].split("<!-- CURRENT_REQUEST_20261029_END -->", 1)[0]
    assert block.strip() == (ROOT / "research/REQUEST_20261029.md").read_text().strip()


def test_readme_top_table_lists_all_nine_sites_with_unique_no():
    head = (ROOT / "README.md").read_text().split("<!-- CURRENT_REQUEST_20261029_START -->", 1)[0]
    rows = [line for line in head.splitlines() if line.startswith("| GEMSDOE")]
    assert sorted(re.match(r"\| (GEMSDOE\d+) ", r).group(1) for r in rows) == sorted(SITES)
    assert all(r.rstrip().endswith("| **NO** | **NO** |") for r in rows)


def test_readme_head_links_resolve():
    head = (ROOT / "README.md").read_text().split("<!-- CURRENT_REQUEST_20261029_START -->", 1)[0]
    for relative in re.findall(r"\]\(([^():#\s]+)(?:#[^)]*)?\)", head):
        assert (ROOT / relative).exists(), relative
