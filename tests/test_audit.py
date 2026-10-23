import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]

from scripts.audit import check_pins, run
from gems57.submission_writer import write_submission
from gems57.uniqueness import dot_overlap, surface_rho
from gems57.evaluate_holdout import evaluate
from gems57 import grid, metric, validate as VAL


class SafetyTests(unittest.TestCase):
    def test_shared_bytes_unmodified(self):
        self.assertTrue(check_pins())

    def test_missing_evidence_is_not_ready(self):
        before = (ROOT / "docs/evidence/run-card.json").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            card = run(evidence_path=Path(tmp) / "absent-run-card.json", write_out=None)
        after = (ROOT / "docs/evidence/run-card.json").read_bytes()
        self.assertEqual(before, after, "run() must never clobber docs/evidence/run-card.json")
        self.assertFalse(card["submission_ready"])
        self.assertEqual(card["verdict"], "negative")
        self.assertIsNone(card["raster_sha256"])
        self.assertEqual(card["holdout_dti"]["status"], "NOT_RUN")
        self.assertLessEqual(len(card["note"]), 140)

    def test_writer_rejects_invalid_values_before_writing(self):
        for bad in [np.nan, np.inf, -0.01, 1.01, -9999]:
            with self.subTest(value=bad), self.assertRaises(ValueError):
                write_submission(
                    "/tmp/never-created.tif",
                    np.array([[bad]]),
                    "absent.tif",
                    np.ones((1, 1), bool),
                    name="test",
                    note="test",
                )

    def test_writer_rejects_catalogue_and_outside_footprint(self):
        p = np.ones((2, 2))
        for footprint, catalogue in [
            (np.zeros((2, 2), bool), None),
            (np.ones((2, 2), bool), np.ones((2, 2), bool)),
        ]:
            with self.assertRaises(ValueError):
                write_submission(
                    "/tmp/never-created.tif",
                    p,
                    "absent.tif",
                    footprint,
                    catalogue=catalogue,
                    name="test",
                    note="test",
                )

    def test_duplicate_math(self):
        a = np.zeros((20, 20))
        a[8, 8] = 1
        b = np.zeros_like(a)
        b[8, 11] = 1
        self.assertEqual(dot_overlap(a, b), 1)
        b = np.arange(400).reshape(20, 20)
        self.assertAlmostEqual(
            surface_rho(b, b, np.ones_like(b, bool))["spearman_full_footprint"], 1
        )

    def test_metric_against_literal_oracle(self):
        rng = np.random.default_rng(86)
        pred = rng.random((12, 12)) * (rng.random((12, 12)) < 0.1)
        truth = rng.random((12, 12)) < 0.05
        fast, slow = metric.dti_exact(pred, truth), metric.dti_bruteforce(pred, truth)
        for key in ("tp", "fp", "fn", "dti"):
            self.assertAlmostEqual(fast[key], slow[key], places=10)

    def test_synthetic_full_grid_writer_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "sample.tif"
            with rasterio.open(
                sample,
                "w",
                driver="GTiff",
                height=grid.HEIGHT,
                width=grid.WIDTH,
                count=1,
                dtype="float32",
                crs=grid.CRS_EPSG,
                transform=grid.TRANSFORM,
                compress="deflate",
            ) as dst:
                dst.write(np.zeros(grid.SHAPE, np.float32), 1)
            pred = np.zeros(grid.SHAPE, np.float32)
            pred[100, 100] = 0.5
            out = Path(tmp) / "synthetic-test-only.tif"
            receipt = write_submission(
                out,
                pred,
                sample,
                np.ones(grid.SHAPE, bool),
                name="Synthetic unit fixture",
                note="NOT A COMPETITION CANDIDATE",
            )
            self.assertTrue(receipt["template_report"]["ok"])
            self.assertFalse(receipt["approved_for_weekly_slot"])
            with rasterio.open(out) as src:
                self.assertEqual(src.shape, grid.SHAPE)
                self.assertEqual(src.transform, grid.TRANSFORM)
                np.testing.assert_array_equal(src.read(1), pred)
            with zipfile.ZipFile(out.with_suffix(".zip")) as z:
                self.assertEqual(z.namelist(), [out.name])
            with self.assertRaises(FileExistsError):
                write_submission(
                    out, pred, sample, np.ones(grid.SHAPE, bool), name="test", note="test"
                )

    def test_evaluator_rejects_empty_truth(self):
        a = np.zeros((10, 10))
        mask = np.ones_like(a, bool)
        with self.assertRaises(ValueError):
            evaluate(a, dict(region=mask, visible=a.astype(bool), truth=a.astype(bool)), mask)

    def test_generated_h86_wvb_submission_validated_without_human_intervention(self):
        """Automated end-to-end validation of the H86-WVB GeoTIFF, ZIP, and Run Card."""
        card_path = ROOT / "docs" / "evidence" / "run-card.json"
        self.assertTrue(card_path.is_file())
        card = run(evidence_path=card_path, write_out=None)
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

        # Verify protocol fields on Run Card
        self.assertEqual(card["holdout_dti"]["label"], "HOLDOUT-DTI")
        self.assertIsNone(card["organizer_confirmed_score"])
        self.assertTrue(card["leakage_canary"]["passed"])
        self.assertLessEqual(card["leakage_canary"]["max_single_feature_discriminative_auc_seed20"], 0.90)
        self.assertLessEqual(card["leakage_canary"]["max_single_feature_discriminative_auc_seed21"], 0.90)
        self.assertLessEqual(len(card["submission_note"]), 140)
        self.assertLessEqual(card["experiments_used"], 3)
        self.assertIn(card["verdict"], ("promote", "negative"))
        # Literal 3-px overlap fired on gems10-h25/h28 (>0.70), so verdict must be 'negative'
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["submission_ready"])

    def test_docs_pages_reference_current_artifact(self):
        card = json.loads((ROOT / "docs" / "evidence" / "run-card.json").read_text())
        tif_name = Path(card["artifact_paths"]["tif"]).name
        for page in ("index.html", "executive-summary.html"):
            html = (ROOT / "docs" / page).read_text()
            self.assertIn(tif_name, html, f"{page} must link directly to {tif_name}")
            self.assertIn(card["raster_sha256"][:16], html, f"{page} must display current SHA-256")


if __name__ == "__main__":
    unittest.main()
