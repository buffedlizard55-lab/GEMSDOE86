from __future__ import annotations

import ast
import inspect
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "vendor")]

from scripts.strict_uniqueness import literal_blockers, phase_status, two_phase_status  # noqa: E402
import run_lane86b  # noqa: E402
import scripts.protocol_preflight as protocol_preflight  # noqa: E402


def row(*, rho=0.0, overlap=0.0, **extra):
    return {
        "repo": "owner/repo",
        "submission": "prior.tif",
        "spearman_full_footprint": rho,
        "my_dots_within_3px_of_theirs": overlap,
        **extra,
    }


def report(rows, *, complete=True):
    return {
        "rows": rows,
        "complete_accessible_scan": complete,
        "registry_rasters_expected": len(rows),
        "registry_rasters_checked": len(rows),
        "missing_or_invalid": 0,
        "source_errors": [],
    }


class StrictUniquenessTests(unittest.TestCase):
    def test_literal_overlap_fires_even_if_jaccard_would_be_small(self):
        blockers = literal_blockers([row(rho=0.05, overlap=0.700001)])
        self.assertEqual(len(blockers), 1)
        self.assertTrue(any("forward 3-px overlap" in reason for reason in blockers[0]["reasons"]))

    def test_exact_thresholds_do_not_fire(self):
        self.assertEqual(literal_blockers([row(rho=0.90, overlap=0.70)]), [])

    def test_rho_above_threshold_fires(self):
        blockers = literal_blockers([row(rho=0.900001, overlap=0.10)])
        self.assertEqual(len(blockers), 1)
        self.assertTrue(any("rank correlation" in reason for reason in blockers[0]["reasons"]))

    def test_non_finite_metrics_fail_closed(self):
        blockers = literal_blockers([row(rho=float("nan"), overlap=float("inf"))])
        self.assertEqual(len(blockers), 1)
        self.assertEqual(len(blockers[0]["reasons"]), 2)

    def test_missing_inventory_certification_fields_fail_closed(self):
        incomplete = {"rows": [row()], "complete_accessible_scan": True}
        self.assertFalse(phase_status(incomplete)["clear_under_literal_rule"])

    def test_missing_metrics_and_comparison_errors_fail_closed(self):
        missing = {"submission": "missing.tif"}
        errored = {"submission": "error.tif", "error": "bad grid"}
        blockers = literal_blockers([missing, errored])
        self.assertEqual(len(blockers), 2)
        self.assertFalse(phase_status(report([row()], complete=False))["clear_under_literal_rule"])
        self.assertFalse(phase_status(report([], complete=True))["clear_under_literal_rule"])

    def test_two_phase_requires_surface_and_final_dots_to_clear(self):
        passing = report([row()], complete=True)
        blocked_final = report([row(overlap=0.71)], complete=True)
        result = two_phase_status(passing, blocked_final)
        self.assertFalse(result["clear_under_literal_rule"])
        self.assertTrue(result["pre_placement_surface"]["clear_under_literal_rule"])
        self.assertFalse(result["final_dots"]["clear_under_literal_rule"])

    def test_runner_has_no_preflight_bypass_and_preflights_before_features(self):
        self.assertNotIn("skip_literal_preflight", inspect.signature(run_lane86b.main).parameters)
        tree = ast.parse((ROOT / "scripts/run_lane86b.py").read_text())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        calls = [
            (node.lineno, node.func.id if isinstance(node.func, ast.Name) else node.func.attr)
            for node in ast.walk(main) if isinstance(node, ast.Call)
        ]
        require_line = min(line for line, name in calls if name == "require_feasible")
        feature_line = min(line for line, name in calls if name == "build_physical_planes")
        self.assertLess(require_line, feature_line)

    def test_failed_preflight_stops_before_feature_build(self):
        with mock.patch.object(protocol_preflight, "require_feasible", side_effect=RuntimeError("blocked")), \
             mock.patch.object(run_lane86b.F, "build_physical_planes") as build:
            with self.assertRaisesRegex(RuntimeError, "blocked"):
                run_lane86b.main()
            build.assert_not_called()

    def test_recorded_review_card_is_negative_and_literal(self):
        import json

        card = json.loads((ROOT / "docs/evidence/review-20261023-run-card.json").read_text())
        self.assertFalse(card["candidate_generated_this_review"])
        self.assertEqual(card["experiments_run_this_review"], 0)
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["submission_ready"])
        self.assertFalse(card["safe_to_submit"])
        surface = card["correlation_overlap_vs_registry"]["pre_placement_surface"]
        self.assertTrue(surface["stop_required"])
        self.assertEqual(surface["forward_3px_overlap_lower_bound"], 1.0)
        rows = card["correlation_overlap_vs_registry"]["final_dots"]["rows"]
        gmc = next(row for row in rows if "gmc-linepost-90568d" in row["submission"])
        dense = next(row for row in rows if row["submission"].startswith("17GEMSDOE_E-proba"))
        self.assertGreater(gmc["candidate_dots_within_3px_of_registry"], 0.70)
        self.assertEqual(dense["candidate_dots_within_3px_of_registry"], 1.0)


if __name__ == "__main__":
    unittest.main()
