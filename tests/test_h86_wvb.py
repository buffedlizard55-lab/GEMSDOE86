import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]

from scripts.audit_h86_wvb import DEFAULT_RUN_CARD, check_pins, run
from gems57.submission_writer import write_submission
from gems57.uniqueness import dot_overlap, surface_rho
from gems57.evaluate_holdout import evaluate
from gems57 import grid, metric, validate as VAL


class H86WvbTests(unittest.TestCase):
    def test_shared_bytes_unmodified(self):
        self.assertTrue(check_pins())

    def test_missing_evidence_is_not_ready(self):
        before = DEFAULT_RUN_CARD.read_bytes()
        canonical_before = (ROOT / "docs/evidence/run-card.json").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            card = run(evidence_path=Path(tmp) / "absent-run-card.json", write_out=None)
        self.assertEqual(before, DEFAULT_RUN_CARD.read_bytes())
        self.assertEqual(canonical_before, (ROOT / "docs/evidence/run-card.json").read_bytes())
        self.assertFalse(card["submission_ready"])
        self.assertEqual(card["verdict"], "negative")
        self.assertIsNone(card["raster_sha256"])
        self.assertEqual(card["holdout_dti"]["status"], "NOT_RUN")
        self.assertLessEqual(len(card["note"]), 140)

    def test_h86_wvb_cannot_bypass_preflight(self):
        from scripts.run_h86_wvb import main

        with self.assertRaises(TypeError):
            main(skip_literal_preflight=True)
        with patch("scripts.protocol_preflight.require_feasible", side_effect=RuntimeError("STOP")):
            with patch("scripts.run_h86_wvb.build_static_physics_matrix") as build:
                with self.assertRaisesRegex(RuntimeError, "STOP"):
                    main()
                build.assert_not_called()

    def test_generated_h86_wvb_submission_validated_without_human_intervention(self):
        """Automated end-to-end validation of the H86-WVB GeoTIFF, ZIP, and isolated Run Card."""
        self.assertTrue(DEFAULT_RUN_CARD.is_file())
        card = run(evidence_path=DEFAULT_RUN_CARD, write_out=None)
        self.assertTrue(card["preflight_checks"]["shared_template_hashes_match"])
        self.assertTrue(card["preflight_checks"]["artifact_tif_verified"])
        self.assertTrue(card["preflight_checks"]["artifact_zip_verified"])

        tif_path = ROOT / card["artifact_paths"]["tif"]
        zip_path = ROOT / card["artifact_paths"]["zip"]
        self.assertTrue(tif_path.is_file())
        self.assertTrue(zip_path.is_file())

        rec = VAL.validate(tif_path)
        self.assertTrue(rec["all_checks_passed"])
        self.assertEqual(rec["n_nan"], 0)
        self.assertEqual(rec["n_infinite"], 0)
        self.assertGreaterEqual(rec["min"], 0.0)
        self.assertLessEqual(rec["max"], 1.0)
        self.assertEqual(rec["sha256"], card["raster_sha256"])
        self.assertEqual(rec["emitted_positive_pixels"], 37_654)
        self.assertEqual(rec["meta"]["crs"], "EPSG:32611")
        self.assertEqual(rec["meta"]["shape"], [3730, 3292])

        self.assertEqual(card["holdout_dti"]["label"], "HOLDOUT-DTI")
        self.assertIsNone(card["organizer_confirmed_score"])
        self.assertTrue(card["leakage_canary"]["passed"])
        self.assertLessEqual(card["leakage_canary"]["max_single_feature_discriminative_auc_seed20"], 0.90)
        self.assertLessEqual(card["leakage_canary"]["max_single_feature_discriminative_auc_seed21"], 0.90)
        self.assertLessEqual(len(card["submission_note"]), 140)
        self.assertLessEqual(card["experiments_used"], 3)
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["submission_ready"])
        self.assertFalse(card["approved_for_weekly_slot"])
        self.assertFalse(card["safe_to_submit"])

        cross = json.loads((ROOT / card["crosslane_uniqueness_evidence"]).read_text())
        self.assertEqual(cross["candidate_sha256"], card["raster_sha256"])
        self.assertEqual(cross["sibling_lanes_checked"], 6)
        self.assertLessEqual(cross["max_abs_spearman"], 0.90)

    def test_docs_pages_reference_h86_wvb_artifact(self):
        card = json.loads(DEFAULT_RUN_CARD.read_text())
        tif_name = Path(card["artifact_paths"]["tif"]).name
        for page in ("index.html", "executive-summary.html"):
            html = (ROOT / "docs" / page).read_text()
            self.assertIn(tif_name, html, f"{page} must link directly to {tif_name}")
            self.assertIn(card["raster_sha256"][:16], html, f"{page} must display H86-WVB SHA-256")


if __name__ == "__main__":
    unittest.main()
