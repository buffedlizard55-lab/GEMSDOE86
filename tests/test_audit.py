import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "vendor")]

from gems57 import grid, metric
from gems57.evaluate_holdout import evaluate
from gems57.submission_writer import write_submission
from gems57.uniqueness import dot_overlap, surface_rho
from scripts.audit import check_pins, run
from scripts.run_lane86 import emit_nms_topk, emit_submodular_minoux, emit_two_stage_submodular


class SafetyAndLaneTests(unittest.TestCase):
    def test_shared_bytes_unmodified(self):
        self.assertTrue(check_pins(ROOT))

    def test_missing_evidence_is_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            card = run(Path(tmp), write_audit_receipt=False)
            self.assertFalse(card["submission_ready"])
            self.assertEqual(card["verdict"], "negative")
            self.assertIsNone(card["raster_sha256"])
            self.assertEqual(card["holdout_dti"]["status"], "NOT_RUN")
            self.assertLessEqual(len(card["note"]), 140)

    def test_live_repository_audit_and_artifact_integrity(self):
        rep = run(ROOT, write_audit_receipt=False)
        self.assertTrue(rep["ok"], msg=f"Failed checks: {[k for k, v in rep['checks'].items() if not v]}")
        self.assertEqual(rep["verdict"], "promote")
        self.assertTrue(rep["submission_ready"])
        self.assertLessEqual(len(rep["note"]), 140)
        for required_check in (
            "shared_template_hashes_match",
            "tif_exists",
            "zip_exists",
            "tif_sha256_matches_card",
            "single_band_float32",
            "crs_epsg_32611",
            "shape_3730x3292",
            "transform_matches_pinned",
            "nodata_is_none",
            "all_pixels_finite",
            "strictly_in_0_1",
            "emitted_dots_match_card",
            "zip_sha256_matches_card",
            "zip_contains_single_matching_tif",
            "note_le_140_chars",
            "leakage_canary_pass",
            "uniqueness_gate_pass",
            "holdout_gate_pass",
            "docs_pages_synced_to_artifact",
        ):
            self.assertTrue(rep["checks"].get(required_check), msg=f"Check failed: {required_check}")

    def test_no_leaked_dist_known_fault_px_loaded(self):
        for rel in ("scripts/h86_features.py", "scripts/run_lane86.py"):
            src = (ROOT / rel).read_text()
            self.assertNotIn('open(EXT_DIR / "dist_known_fault_px', src)
            self.assertNotIn("data/external/dist_known_fault_px.tif", src)

    def test_submodular_allocator_mask_and_budget_contracts(self):
        rng = np.random.default_rng(86)
        prob = np.zeros((40, 40), dtype=np.float32)
        prob[10, 8:32] = 0.65
        prob[26, 6:34] = 0.45
        prob += 0.01 * rng.random((40, 40), dtype=np.float32)
        vis = np.zeros((40, 40), dtype=bool)
        vis[10, 4:7] = True
        allowed = np.ones((40, 40), dtype=bool)
        allowed[0:3, :] = False
        allowed[vis] = False

        dots_sub, cov = emit_submodular_minoux(prob, allowed, budget=10)
        self.assertEqual(int(dots_sub.sum()), 10)
        self.assertEqual(cov.shape, (prob.shape[0] + 6, prob.shape[1] + 6))
        self.assertLessEqual(float(cov.max()), 1.0001)
        self.assertFalse(bool((dots_sub & ~allowed).any()))

        dots_two = emit_two_stage_submodular(prob, prob * 0.8, vis, allowed, budget=12, near_frac=0.5)
        self.assertEqual(int(dots_two.sum()), 12)
        self.assertFalse(bool((dots_two & ~allowed).any()))

        dots_nms = emit_nms_topk(prob, allowed, budget=10)
        self.assertFalse(bool((dots_nms & ~allowed).any()))

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
        self.assertAlmostEqual(surface_rho(b, b, np.ones_like(b, bool))["spearman_full_footprint"], 1)

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
                write_submission(out, pred, sample, np.ones(grid.SHAPE, bool), name="test", note="test")

    def test_evaluator_rejects_empty_truth(self):
        a = np.zeros((10, 10))
        mask = np.ones_like(a, bool)
        with self.assertRaises(ValueError):
            evaluate(a, dict(region=mask, visible=a.astype(bool), truth=a.astype(bool)), mask)


if __name__ == "__main__":
    unittest.main()
