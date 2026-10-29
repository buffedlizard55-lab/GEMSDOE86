"""Tests for scripts/verify_nine_site_lineage.py and its committed evidence.

The helper tests use synthetic arrays only. The evidence tests read the committed
docs/evidence/nine-site-lineage-20261029.json and fail if its safety invariants drift.
"""
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from scripts import verify_nine_site_lineage as v  # noqa: E402

EVIDENCE = ROOT / "docs/evidence/nine-site-lineage-20261029.json"


class DotRuleTests(unittest.TestCase):
    def test_only_finite_positive_cells_are_dots(self):
        a = np.array([[0.0, 1.0, np.nan], [np.inf, -0.5, 0.25]], dtype=np.float32)
        self.assertEqual(v.dot_mask(a).tolist(), [[False, True, False], [False, False, True]])


class LineageTests(unittest.TestCase):
    def test_subset_and_removed_geometry(self):
        parent = np.zeros((4, 4), bool)
        parent[0, :] = True                      # 4 dots
        child = parent.copy()
        child[0, 0] = False                      # one removed
        dist = np.zeros((4, 4))
        dist[0, 0] = 2.0
        out = v.lineage_stats(parent, child, dist)
        self.assertTrue(out["child_subset_of_parent"])
        self.assertEqual(out["removed_dots"], 1)
        self.assertEqual(out["added_dots"], 0)
        self.assertEqual(out["removed_catalogue_distance_px"], {"2.0000": 1})

    def test_addition_breaks_subset(self):
        parent = np.zeros((3, 3), bool)
        parent[1, 1] = True
        child = parent.copy()
        child[0, 0] = True
        out = v.lineage_stats(parent, child, np.zeros((3, 3)))
        self.assertFalse(out["child_subset_of_parent"])
        self.assertEqual(out["added_dots"], 1)


class TopKDiagnosticTests(unittest.TestCase):
    def test_topk_is_exact_inside_footprint(self):
        rng = np.random.default_rng(0)
        vals = rng.random((50, 50))
        fp = np.ones((50, 50), bool)
        fp[:, 40:] = False
        top = v.topk_mask(vals, fp, 100)
        self.assertEqual(int(top.sum()), 100)
        self.assertFalse((top & ~fp).any())
        self.assertTrue(np.all(vals[top] >= np.partition(vals[fp], -100)[-100]))


class EvidenceInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(EVIDENCE.read_text())

    def test_safety_flags_stay_closed(self):
        self.assertEqual(self.doc["decision"], "DO NOT SUBMIT")
        self.assertFalse(self.doc["safe_to_submit"])
        self.assertFalse(self.doc["approved_for_weekly_slot"])
        self.assertEqual(self.doc["submission_slots_used"], 0)
        self.assertTrue(self.doc["not_a_score"])
        self.assertTrue(self.doc["not_a_clearance"])

    def test_every_file_hash_matches_the_audit(self):
        self.assertEqual(len(self.doc["nine_site_files"]), 9)
        for r in self.doc["nine_site_files"]:
            self.assertTrue(r["sha256_matches_audit"])
            self.assertEqual(r["nan_total"], 0)
            self.assertEqual(r["dots_on_catalogue"], 0)
            self.assertEqual(r["dots_outside_footprint"], 0)
            self.assertIn("OWNER-REPORTED", r["owner_score_class"])

    def test_all_72_ordered_pairs_fail_the_0_70_rule(self):
        s = self.doc["pairwise_summary"]
        self.assertEqual(s["ordered_pairs"], 72)
        self.assertEqual(s["pairs_over_0_70"], 72)
        self.assertGreaterEqual(s["min"], 0.70)

    def test_h33_is_a_pure_subset_of_its_gemsdoe31_parent(self):
        h = self.doc["h33_lineage"]
        self.assertTrue(h["child_subset_of_parent"])
        self.assertEqual((h["parent_dots"], h["child_dots"], h["removed_dots"], h["added_dots"]),
                         (40199, 37654, 2545, 0))

    def test_witness_diagnostic_never_claims_clearance(self):
        w = self.doc["witness"]
        self.assertTrue(w["pinned_sha256_matches"])
        self.assertIn("UNCHANGED", w["literal_gate_status"])
        self.assertIn("DIAGNOSTIC ONLY", w["topK_diagnostic"]["definition"])


if __name__ == "__main__":
    unittest.main()


def test_summary_page_has_nine_rows_and_no_projected_or_holdout_number():
    import copy
    import json
    from scripts.build_site import nine_site_summary_page
    lin = json.loads((ROOT / "docs/evidence/nine-site-lineage-20261029.json").read_text())
    page = nine_site_summary_page(lin)
    body = page.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
    assert body.count('<span class="badge bad">NOT ESTIMATED</span>') == 9
    assert body.count('<span class="badge bad">NOT UNIQUE</span>') == 9
    assert "HOLDOUT-DTI run" in page and "ORGANIZER-CONFIRMED receipt" in page
    assert "Do not upload" in page
    # Owner numbers appear only as labelled OWNER-REPORTED values.
    assert page.count("OWNER-REPORTED") >= 9
    bad = copy.deepcopy(lin)
    bad["safe_to_submit"] = True
    import pytest
    with pytest.raises(ValueError):
        nine_site_summary_page(bad)


def test_summary_page_is_linked_from_nine_sites_page():
    import json
    from scripts.build_site import nine_sites_page
    audit = json.loads((ROOT / "docs/evidence/nine-site-audit-20261027.json").read_text())
    cand = json.loads((ROOT / "docs/evidence/h87-fcb-candidate-receipt-20261027.json").read_text())
    exp1 = json.loads((ROOT / "docs/evidence/h87-fcb-experiment1-20261027.json").read_text())
    exp2 = json.loads((ROOT / "docs/evidence/h87-fcb-experiment2-20261027.json").read_text())
    assert 'href="nine-site-summary.html"' in nine_sites_page(audit, cand, exp1, exp2)
