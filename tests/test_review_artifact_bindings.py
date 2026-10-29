"""Ensure the prose review is bound to the immutable evidence JSON, not hand-copied guesses."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "research/SESSION_20261029_6AD5BDD2_REVIEW.md"


def _load(relative):
    return json.loads((ROOT / relative).read_text())


def test_per_site_table_matches_score_source_and_immutable_file_receipts():
    report = REPORT.read_text()
    audit = _load("docs/evidence/focus9-score-source-audit-20261029.json")
    immutable = {item["site"]: item for item in _load(
        "docs/evidence/focus9-immutable-files-20261029.json")["files"]}
    for claim in audit["per_site_claims"]:
        site = claim["site"]
        row = next(line for line in report.splitlines() if line.startswith(f"| [{site}]") )
        binding = claim["historical_file_immutable_repository_binding"]
        byte_audit = claim["historical_file_byte_audit"]
        expected_name = Path(byte_audit["path"]).name
        display_claim = claim["submission_claim"].removesuffix("-nan")
        overlap = claim["uniqueness_vs_other_focus9_files"]
        assert display_claim in row
        assert f"{claim['supplied_score']:.4f}" in row
        assert byte_audit["sha256"][:12] in row
        assert expected_name in row
        assert binding["commit_pinned_url"] in row
        assert f"{overlap['max_directed_3px_overlap']:.4f} vs {overlap['worst_comparator']}" in row
        receipt = immutable[site]
        assert receipt["sha256"] == byte_audit["sha256"]
        assert receipt["commit_sha"] == binding["commit_sha"]
        assert receipt["path"] == byte_audit["path"]
        assert claim["submission_authorized"] is False
        assert claim["organizer_confirmed"] is False


def test_metadata_only_new_path_table_matches_feed_delta_and_d30_disposition():
    report = REPORT.read_text()
    delta = _load("docs/evidence/focus9-feed-delta-20261029.json")
    paths = []
    for site in delta["sites"]:
        for entry in site["added_tif_paths"]:
            paths.append(entry["path"])
            assert entry["content_bytes_fetched_or_verified"] is False
            assert entry["score_status"].startswith("UNKNOWN") or entry["score_status"].startswith("UNSCORED")
            assert entry["path"] in report
    assert len(paths) == delta["new_tif_path_count"] == 9
    d30 = next(site for site in delta["sites"] if site["site"] == "GEMSDOE30")
    stopped = next(entry for entry in d30["added_tif_paths"] if "165045Z" in entry["path"])
    assert stopped["download_decision"] == "OWNER_MARKED_NOT_FOR_DOWNLOAD_OR_SUBMISSION"
    assert "NOT for download or submission" in report
    assert "metadata only" in report.lower()


def test_d32_rescore_source_hash_and_reported_holdout_match_the_pinned_capture():
    audit = _load("docs/evidence/focus9-score-source-audit-20261029.json")
    card = _load("docs/evidence/session-6ad5bdd2-run-card.json")
    source = audit["highest_supplied_focus9_claim"]["separate_owner_repository_holdout"]
    card_source = card["separate_owner_repository_holdout_context"]
    assert source["source_content_sha256"] == "eebd75b181f89dfe36262d25ccc068bba1b2b0afb589ef675af1cffa630d8e9b"
    assert source["source_content_sha256"] == card_source["source_content_sha256"]
    assert source["source_git_blob_sha1"] == card_source["source_git_blob_sha1"]
    assert source["source_url"] == card_source["source_url"]
    assert source["value"] == card_source["value"] == 0.00451537871535044
    assert source["ci95"] == card_source["ci95"] == [0.0038164175817344387, 0.005261598301920283]
    assert source["withheld_positives"] == card_source["withheld_positives"] == 22232
    assert "not a leaderboard score" in source["evidence_class"].lower()
