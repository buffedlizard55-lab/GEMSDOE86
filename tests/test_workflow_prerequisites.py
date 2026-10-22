from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from preflight import REQUIRED_DATA, SHARED_FILES, inspect_environment  # noqa: E402
from refresh_leaderboard import parse_leaderboard_html  # noqa: E402
import check_site  # noqa: E402


class PreflightTests(unittest.TestCase):
    def test_empty_workspace_fails_closed(self) -> None:
        report = inspect_environment({"GEMS_DATA_DIR": "/definitely/not/a/real/path"})
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["ready_for_shared_run"])
        self.assertEqual(report["submission_status"], "NO_TIF_GENERATED")
        self.assertTrue(report["blockers"])

    def test_prerequisite_inventory_does_not_claim_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            data_dir = base / "data"
            shared_dir = base / "shared"
            data_dir.mkdir()
            (shared_dir / "vendor" / "gems57").mkdir(parents=True)
            for filename in REQUIRED_DATA:
                (data_dir / filename).write_bytes(b"placeholder-for-existence-test")
            for rel in SHARED_FILES:
                path = shared_dir / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("placeholder", encoding="utf-8")
            stack = base / "cache" / "stack.npy"
            stack.parent.mkdir()
            stack.write_bytes(b"not-a-real-array")
            registry = base / "registry.json"
            registry.write_text("{}", encoding="utf-8")

            report = inspect_environment({
                "GEMS_DATA_DIR": str(data_dir),
                "GEMS_FEATURE_STACK": str(stack),
                "GEMS_SHARED_TEMPLATE": str(shared_dir),
                "GEMS_REGISTRY_INDEX": str(registry),
            })

        self.assertTrue(report["ready_for_shared_run"])
        self.assertEqual(report["status"], "PREREQUISITES_PRESENT_NOT_VALIDATED")
        self.assertEqual(report["submission_status"], "NO_TIF_GENERATED")
        self.assertTrue(any("does not authenticate provenance" in item for item in report["limitations"]))


class LeaderboardParserTests(unittest.TestCase):
    def test_parses_official_style_table_and_labels_scope(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "leaderboard.html"
        rows = parse_leaderboard_html(fixture.read_text(encoding="utf-8"))
        self.assertEqual(rows[0]["rank"], 1)
        self.assertEqual(rows[0]["participant"], "xiaofanhu")
        self.assertEqual(rows[0]["score"], 0.4413)
        self.assertEqual(rows[0]["evidence_class"], "ORGANIZER-CONFIRMED")
        self.assertIn("not a GEMSDOE86 result", rows[0]["evidence_scope"])
        self.assertEqual(rows[2]["participant"], "Batik Shirt Brothers")

    def test_layout_change_is_not_silently_accepted(self) -> None:
        with self.assertRaises(ValueError):
            parse_leaderboard_html("<table><tr><td>no board data</td></tr></table>")


class SiteGateTests(unittest.TestCase):
    def test_current_workspace_has_a_blocked_download_gate(self) -> None:
        self.assertEqual(check_site.check_run_card_and_download_gate(), [])

    def test_unapproved_raster_file_is_rejected(self) -> None:
        original_docs = check_site.DOCS
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp) / "docs"
            (docs / "data").mkdir(parents=True)
            (docs / "downloads").mkdir()
            (docs / "downloads" / "peer.tif").write_bytes(b"not a candidate")
            source_card = json.loads((ROOT / "docs" / "data" / "run-card.json").read_text(encoding="utf-8"))
            (docs / "data" / "run-card.json").write_text(json.dumps(source_card), encoding="utf-8")
            (docs / "index.html").write_text(
                '<p>Do not upload a file</p><a id="submission-download" aria-disabled="true">Locked</a>',
                encoding="utf-8",
            )
            check_site.DOCS = docs
            try:
                errors = check_site.check_run_card_and_download_gate()
            finally:
                check_site.DOCS = original_docs
        self.assertTrue(any("does not mark an artifact approved" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
