"""Automated unit & integration tests for Lane 7 (`H86-FVMB`).

Compatible with both `pytest` (`ci.yml`, `pages.yml`) and
`python -m unittest discover -s tests -v` (`verify.yml`).
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gems86_fvmb.dinkelbach_allocator import emit_dinkelbach_submodular, emit_tri_regime_dinkelbach, kernel_25_offsets  # noqa: E402
from gems86_fvmb.features import STATIC_60_NAMES  # noqa: E402
from gems86_fvmb.wingcrack_network import WINGCRACK_12_NAMES  # noqa: E402
from scripts import audit_h86_fvmb  # noqa: E402


class H86FvmbTests(unittest.TestCase):
    def test_audit_h86_fvmb_passes_all_gates(self) -> None:
        res = audit_h86_fvmb.run()
        self.assertTrue(res["all_checks_passed"], msg=json.dumps(res, indent=2))
        self.assertEqual(res["verdict"], "negative")
        self.assertFalse(res["submission_ready"])
        self.assertFalse(res["approved_for_weekly_slot"])

    def test_missing_runcard_fails_closed_without_mutation(self) -> None:
        before = audit_h86_fvmb.RUNCARD.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            res = audit_h86_fvmb.run(Path(tmp) / "missing.json")
            self.assertFalse(res["all_checks_passed"])
            self.assertEqual(res["verdict"], "negative")
        self.assertEqual(audit_h86_fvmb.RUNCARD.read_bytes(), before)

    def test_feature_and_kernel_invariants(self) -> None:
        self.assertEqual(len(STATIC_60_NAMES), 60)
        self.assertEqual(len(WINGCRACK_12_NAMES), 12)
        k25 = kernel_25_offsets()
        self.assertEqual(len(k25), 25)
        wsum = sum(w for _, _, w in k25)
        self.assertAlmostEqual(wsum, 9.3802978, places=5)

        feat_src = (ROOT / "src" / "gems86_fvmb" / "features.py").read_text()
        self.assertNotIn('df["dist_known_fault_px"]', feat_src)

    def test_tri_regime_dinkelbach_synthetic_emission(self) -> None:
        h, w = 80, 80
        fp = np.ones((h, w), dtype=bool)
        fp[:2, :] = False
        cat = np.zeros((h, w), dtype=bool)
        cat[25:55, 25] = True
        region = fp.copy()
        rng = np.random.default_rng(86)
        p_cal = rng.uniform(0.0005, 0.015, size=(h, w)).astype(np.float32)
        p_phys = rng.uniform(0.0005, 0.015, size=(h, w)).astype(np.float32)

        emitted, info = emit_tri_regime_dinkelbach(
            p_cal, p_phys, region, cat, fp, total_budget=24
        )
        self.assertEqual(emitted.dtype, np.float32)
        self.assertTrue(np.all((emitted == 0.0) | (emitted == 1.0)))
        self.assertTrue(np.all(emitted[~fp] == 0.0))
        self.assertEqual(int((emitted[cat] > 0).sum()), 0)
        self.assertGreater(info["emitted"], 0)
        self.assertLessEqual(info["emitted"], 24)

        emitted_single, _ = emit_dinkelbach_submodular(
            p_cal, fp, cat, collar_px=2.0, min_sep_px=2.8, target_budget=15
        )
        self.assertEqual(int((emitted_single[cat] > 0).sum()), 0)


if __name__ == "__main__":
    unittest.main()
