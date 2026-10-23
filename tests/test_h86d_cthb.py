"""Unit and integration tests for Lane H86D-CTHB."""
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import audit_h86d  # noqa: E402
import build_site  # noqa: E402
import h86d_features as HF  # noqa: E402
import run_lane86d as RL  # noqa: E402


class H86DCthbTests(unittest.TestCase):
    def test_ast_zero_leakage_in_static_planes(self):
        chk = audit_h86d.ast_zero_leakage_check()
        self.assertTrue(chk["ok"], chk["violations"])
        self.assertEqual(len(HF.STATIC_FEATURE_NAMES), 28)
        self.assertEqual(len(set(HF.STATIC_FEATURE_NAMES)), 28)
        self.assertEqual(len(HF.ALL_FEATURE_NAMES), 35)

    def test_submodular_two_stage_allocator_contracts(self):
        rng = np.random.default_rng(86)
        prob = np.zeros((44, 44), dtype=np.float32)
        prob[12, 8:36] = 0.70
        prob[32, 6:38] = 0.50
        prob += 0.01 * rng.random((44, 44), dtype=np.float32)
        vis = np.zeros((44, 44), dtype=bool)
        vis[12, 3:7] = True
        allowed = np.ones((44, 44), dtype=bool)
        allowed[0:3, :] = False
        allowed[vis] = False

        dots_sub, cov = RL.emit_submodular_minoux(prob, allowed, budget=10)
        self.assertEqual(int(dots_sub.sum()), 10)
        self.assertEqual(cov.shape, (50, 50))
        self.assertLessEqual(float(cov.max()), 1.0001)
        self.assertFalse(bool((dots_sub & ~allowed).any()))

        dots_two = RL.emit_two_stage_submodular(prob, prob * 0.85, vis, allowed, budget=12, near_frac=0.54)
        self.assertEqual(int(dots_two.sum()), 12)
        self.assertFalse(bool((dots_two & ~allowed).any()))

    def test_run_lane86d_and_features_have_no_preflight_bypass(self):
        with self.assertRaises(TypeError):
            RL.main(skip_literal_preflight=True)  # type: ignore[call-arg]
        with mock.patch("scripts.protocol_preflight.measure", return_value={"universal_overlap_blocker": True}):
            with self.assertRaisesRegex(RuntimeError, "STOP_LITERAL_OVERLAP_UNSATISFIABLE"):
                RL.main()
            with self.assertRaisesRegex(RuntimeError, "STOP_LITERAL_OVERLAP_UNSATISFIABLE"):
                HF.main()

    def test_audit_h86d_passes_without_mutating_any_prior_cards(self):
        watched = [
            ROOT / "docs/evidence/run-card.json",
            ROOT / "docs/evidence/h86c-kslb-run-card.json",
            ROOT / "docs/evidence/h86b-gfco-run-card.json",
            ROOT / "docs/evidence/rmrb86-run-card.json",
            ROOT / "evidence/run_card.json",
        ]
        before = {p: p.read_bytes() for p in watched}
        summary = audit_h86d.run()
        self.assertTrue(summary["all_audit_invariants_passed"], summary)
        self.assertEqual(summary["emitted_dots"], 37654)
        self.assertEqual(summary["verdict"], "negative")
        self.assertFalse(summary["approved_for_weekly_slot"])
        for p, raw in before.items():
            self.assertEqual(p.read_bytes(), raw, f"Mutated {p}")

    def test_readme_registers_h86d_exact_bytes_and_note_chars(self):
        rc_check = build_site.main(["--check"])
        self.assertEqual(rc_check, 0)
        readme = (ROOT / "README.md").read_text()
        tif_bytes = (ROOT / "docs/downloads/gems86-h86-cthb-submod-37654dots-20261023T014003Z-zeros.tif").stat().st_size
        self.assertIn(f"| {tif_bytes:,} | 98 |", readme)


if __name__ == "__main__":
    unittest.main()
