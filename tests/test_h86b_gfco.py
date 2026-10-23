import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "vendor")]

import h86b_features as F  # noqa: E402
import run_lane86b as R86B  # noqa: E402
from scripts.audit_h86b import RUNCARD, check_pins, run  # noqa: E402
from gems57 import grid, metric, validate  # noqa: E402
from gems57.evaluate_holdout import evaluate  # noqa: E402
from gems57.submission_writer import write_submission  # noqa: E402
from gems57.uniqueness import dot_overlap, surface_rho  # noqa: E402


class H86BGfcoTests(unittest.TestCase):
    def test_shared_bytes_unmodified(self):
        self.assertTrue(check_pins())

    def test_missing_evidence_is_not_ready_and_never_clobbers_runcard(self):
        before = RUNCARD.read_bytes() if RUNCARD.is_file() else None
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nonexistent_results.json"
            out_tmp = Path(tmp) / "tmp_card.json"
            summary = run(results_path=missing, run_card_out=out_tmp)
            self.assertFalse(summary["submission_ready"])
            self.assertFalse(summary["approved_for_weekly_slot"])
            self.assertEqual(summary["verdict"], "negative")
            self.assertFalse(summary["evidence_present"])
        if before is not None:
            self.assertEqual(RUNCARD.read_bytes(), before, "Unit test must never mutate docs/evidence/run-card.json")

    def test_writer_rejects_invalid_values_before_writing(self):
        for bad in [np.nan, np.inf, -np.inf, -0.01, 1.01, -9999.0]:
            with self.subTest(value=bad), self.assertRaises(ValueError):
                write_submission(
                    "/tmp/never-created.tif",
                    np.array([[bad]], dtype=np.float32),
                    "absent.tif",
                    np.ones((1, 1), bool),
                    name="test",
                    note="test",
                )

    def test_writer_rejects_catalogue_and_outside_footprint(self):
        p = np.ones((2, 2), dtype=np.float32)
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
        a = np.zeros((20, 20), dtype=np.float32)
        a[8, 8] = 1.0
        b = np.zeros_like(a)
        b[8, 11] = 1.0
        self.assertEqual(dot_overlap(a, b), 1.0)
        c = np.arange(400, dtype=np.float32).reshape(20, 20)
        self.assertAlmostEqual(surface_rho(c, c, np.ones_like(c, bool))["spearman_full_footprint"], 1.0)

    def test_metric_against_literal_oracle(self):
        rng = np.random.default_rng(86)
        pred = (rng.random((12, 12)) * (rng.random((12, 12)) < 0.1)).astype(np.float32)
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
                write_submission(out, pred, sample, np.ones(grid.SHAPE, bool), name="test", note="test")

    def test_evaluator_rejects_empty_truth(self):
        a = np.zeros((10, 10), dtype=np.float32)
        mask = np.ones_like(a, bool)
        with self.assertRaises(ValueError):
            evaluate(a, dict(region=mask, visible=a.astype(bool), truth=a.astype(bool)), mask)

    def test_h86b_feature_builder_zero_label_leakage_source_audit(self):
        import ast

        self.assertEqual(len(F.PHYS_FEATURES), 38)
        self.assertEqual(len(set(F.PHYS_FEATURES)), 38)
        self.assertIn("dist_known_fault_px", F.FORBIDDEN_CSV_COLUMNS)

        tree = ast.parse((ROOT / "scripts" / "h86b_features.py").read_text())
        fn_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_physical_planes")
        for node in ast.walk(fn_node):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for forbidden in ("gdr_qfaults_traces", "labels.tif", "existing_faults.tif", "derived_sgmc_faults"):
                    self.assertNotIn(forbidden, node.value)
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                self.assertNotEqual(node.slice.value, "dist_known_fault_px")

    def test_ek_poisson_thinning_spacing_and_non_redundancy(self):
        surf = np.zeros((120, 120), dtype=np.float32)
        surf[40:43, 15:105] = 0.8
        surf[80:83, 15:105] = 0.6
        dots = R86B.emit_ek_poisson(surf, np.ones_like(surf, bool), budget=50, r_suppress=2.8)
        yy, xx = np.nonzero(dots)
        self.assertEqual(len(yy), 50)
        nn = cKDTree(np.column_stack([yy, xx])).query(np.column_stack([yy, xx]), k=2)[0][:, 1]
        self.assertGreaterEqual(float(nn.min()), np.sqrt(8.0) - 1e-6)

    def test_published_h86b_geotiff_and_zip_integrity(self):
        card = json.loads(RUNCARD.read_text())
        tif = ROOT / card["submission_file"]
        zp = ROOT / card["zip_file"]
        self.assertTrue(tif.is_file(), f"Missing {tif}")
        self.assertTrue(zp.is_file(), f"Missing {zp}")
        got_sha = hashlib.sha256(tif.read_bytes()).hexdigest()
        self.assertEqual(got_sha, card["raster_sha256"])

        val = validate.validate(tif)
        validate.assert_submittable(val)
        self.assertTrue(val["all_checks_passed"])
        self.assertEqual(val["min"], 0.0)
        self.assertEqual(val["max"], 1.0)
        self.assertEqual(val["emitted_positive_pixels"], 44090)

        with zipfile.ZipFile(zp) as zf:
            self.assertEqual(zf.namelist(), [tif.name])
            self.assertIsNone(zf.testzip())

    def test_run_card_protocol_compliance_and_strict_json(self):
        def _reject(c):
            raise ValueError(c)

        card = json.loads(RUNCARD.read_text(), parse_constant=_reject)
        for req in (
            "hypothesis",
            "mechanism",
            "non_fault_mimic",
            "holdout_dti",
            "leakage_canary_auc",
            "correlation_overlap_vs_registry",
            "raster_sha256",
            "validator",
            "submission_name",
            "note",
            "verdict",
            "submission_ready",
            "approved_for_weekly_slot",
        ):
            self.assertIn(req, card)
        self.assertLessEqual(len(card["note"]), 140)
        self.assertIn(card["verdict"], {"promote", "negative"})
        self.assertEqual(card["experiments_run"], 3)
        self.assertLessEqual(card["leakage_canary_auc"]["max_discriminative_auc"], 0.90)
        self.assertFalse(card["leakage_canary_auc"]["any_leakage_flag"])
        if card["verdict"] == "negative":
            self.assertFalse(card["submission_ready"])
            self.assertFalse(card["approved_for_weekly_slot"])

    def test_audit_cli_matches_published_evidence(self):
        summary = run()
        self.assertTrue(summary["pins_clean"])
        self.assertTrue(summary["format_valid"])
        self.assertTrue(summary["run_card_consistent"])
        self.assertTrue(summary["leakage_canary_pass"])
        self.assertTrue(summary["point_beats_incumbent_all_3_holdouts"])
        self.assertTrue(summary["modern_comparable_uniqueness_diagnostic_only"])
        self.assertFalse(summary["literal_uniqueness_pass"])
        self.assertTrue(summary["historical_literal_reading_duplicate"])
        self.assertFalse(summary["strict_two_phase_literal_status"]["clear_under_literal_rule"])
        self.assertEqual(summary["verdict"], "negative")
        self.assertFalse(summary["approved_for_weekly_slot"])


if __name__ == "__main__":
    unittest.main()
