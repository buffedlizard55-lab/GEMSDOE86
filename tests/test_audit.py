import sys
import unittest
import tempfile
import json
import zipfile
import rasterio
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor')]
from scripts.audit import check_pins, run, RUN_CARD
from scripts.check_docs import check_local_links
from scripts.uniqueness_gate import assert_experiment_budget_open, classify_registry_result
from gems57.submission_writer import write_submission
from gems57.uniqueness import dot_overlap, surface_rho
from gems57.evaluate_holdout import evaluate
from gems57 import grid, metric, validate


class SafetyTests(unittest.TestCase):
    def test_shared_bytes_unmodified(self):
        self.assertTrue(check_pins())

    def test_github_pages_local_links_resolve(self):
        self.assertEqual(check_local_links(), [])

    def test_read_only_preflight_preserves_scientific_run_card(self):
        before = RUN_CARD.read_bytes()
        report = run()
        after = RUN_CARD.read_bytes()
        self.assertEqual(before, after)
        self.assertFalse(report['submission_ready'])
        self.assertEqual(report['verdict'], 'negative')
        self.assertTrue(report['run_card_unchanged_by_design'])
        self.assertFalse(report['checks']['literal_uniqueness_gate_clear'])
        self.assertFalse(report['checks']['holdout_protocol_conformant'])

    def test_checked_in_candidate_is_format_valid_but_not_ready(self):
        path = ROOT / 'docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif'
        receipt_path = path.with_suffix('.json')
        receipt = json.loads(receipt_path.read_text())
        local = validate.validate(path)
        self.assertTrue(local['all_checks_passed'])
        self.assertEqual(local['sha256'], receipt['sha256'])
        self.assertEqual(local['emitted_positive_pixels'], 60000)
        self.assertFalse(receipt['submission_ready'])
        self.assertEqual(receipt['uniqueness_gate']['status'], 'FAIL_STOP_DUPLICATE_THRESHOLD')
        self.assertLessEqual(receipt['note_chars'], 140)

    def test_exact_registry_identity_also_stops_promotion(self):
        result = {'complete_accessible_scan': True, 'registry_rasters_checked': 1,
                  'rows': [{'submission': 'same-raster', 'spearman_full_footprint': 0.2,
                            'my_dots_within_3px_of_theirs': 0.2, 'identical_bytes': True}]}
        gate = classify_registry_result(result, stage='unit-test', require_complete=True)
        self.assertFalse(gate['passed'])
        self.assertEqual(gate['status'], 'STOP_DUPLICATE_THRESHOLD')
        self.assertEqual(gate['violations'][0]['checks'][0]['metric'], 'identity')

    def test_literal_overlap_gate_is_not_overridden_by_low_rho_or_jaccard(self):
        result = {
            'complete_accessible_scan': True,
            'registry_rasters_checked': 1,
            'worst_spearman_full_footprint': 0.0003,
            'worst_dot_overlap': 0.995,
            'rows': [{
                'submission': 'saturating-lattice',
                'spearman_full_footprint': 0.0003,
                'my_dots_within_3px_of_theirs': 0.995,
                'jaccard_dot_sets': 0.009,
                'duplicate_by_rho': False,
                'duplicate_by_overlap': True,
            }],
        }
        gate = classify_registry_result(result, stage='unit-test', check_rho=True,
                                         check_overlap=True, require_complete=True)
        self.assertFalse(gate['passed'])
        self.assertEqual(gate['status'], 'STOP_DUPLICATE_THRESHOLD')
        self.assertEqual(gate['violations'][0]['checks'][0]['metric'], 'my_dots_within_3px_of_theirs')

    def test_incomplete_registry_cannot_clear_uniqueness(self):
        result = {'complete_accessible_scan': False, 'registry_rasters_checked': 1,
                  'rows': [{'submission': 'one', 'spearman_full_footprint': 0.1,
                            'my_dots_within_3px_of_theirs': 0.1}]}
        gate = classify_registry_result(result, stage='unit-test', require_complete=True)
        self.assertFalse(gate['passed'])
        self.assertEqual(gate['status'], 'STOP_INCOMPLETE_REGISTRY')

    def test_missing_or_nonfinite_comparison_metrics_block_clearance(self):
        for rho, overlap in [(None, 0.1), (float('nan'), 0.1), (0.1, float('inf'))]:
            with self.subTest(rho=rho, overlap=overlap):
                result = {'complete_accessible_scan': True, 'registry_rasters_checked': 1,
                          'rows': [{'submission': 'uncertain', 'spearman_full_footprint': rho,
                                    'my_dots_within_3px_of_theirs': overlap}]}
                gate = classify_registry_result(result, stage='unit-test', require_complete=True)
                self.assertFalse(gate['passed'])
                self.assertEqual(gate['status'], 'STOP_UNVERIFIED_REGISTRY_ROWS')

    def test_experiment_budget_fails_closed(self):
        assert_experiment_budget_open(2, limit=3)
        with self.assertRaises(RuntimeError):
            assert_experiment_budget_open(3, limit=3)

    def test_writer_rejects_invalid_values_before_writing(self):
        for bad in [np.nan, np.inf, -0.01, 1.01, -9999]:
            with self.subTest(value=bad), self.assertRaises(ValueError):
                write_submission('/tmp/never-created.tif', np.array([[bad]]), 'absent.tif',
                                 np.ones((1,1),bool), name='test', note='test')

    def test_writer_rejects_catalogue_and_outside_footprint(self):
        p = np.ones((2,2))
        for footprint, catalogue in [(np.zeros((2,2),bool), None),
                                     (np.ones((2,2),bool), np.ones((2,2),bool))]:
            with self.assertRaises(ValueError):
                write_submission('/tmp/never-created.tif', p, 'absent.tif', footprint,
                                 catalogue=catalogue, name='test', note='test')

    def test_duplicate_math(self):
        a = np.zeros((20,20)); a[8,8] = 1
        b = np.zeros_like(a); b[8,11] = 1
        self.assertEqual(dot_overlap(a,b), 1)
        b = np.arange(400).reshape(20,20)
        self.assertAlmostEqual(surface_rho(b,b,np.ones_like(b,bool))['spearman_full_footprint'],1)

    def test_metric_against_literal_oracle(self):
        # Synthetic arithmetic test, not a geological experiment or score claim.
        rng = np.random.default_rng(86)
        pred = rng.random((12,12)) * (rng.random((12,12)) < .1)
        truth = rng.random((12,12)) < .05
        fast, slow = metric.dti_exact(pred,truth), metric.dti_bruteforce(pred,truth)
        for key in ('tp','fp','fn','dti'):
            self.assertAlmostEqual(fast[key],slow[key],places=10)

    def test_synthetic_full_grid_writer_roundtrip(self):
        # Ephemeral unit fixture ONLY: never persisted or published as a submission.
        with tempfile.TemporaryDirectory() as tmp:
            sample=Path(tmp)/'sample.tif'
            with rasterio.open(sample,'w',driver='GTiff',height=grid.HEIGHT,width=grid.WIDTH,
                               count=1,dtype='float32',crs=grid.CRS_EPSG,
                               transform=grid.TRANSFORM,compress='deflate') as dst:
                dst.write(np.zeros(grid.SHAPE,np.float32),1)
            pred=np.zeros(grid.SHAPE,np.float32); pred[100,100]=.5
            out=Path(tmp)/'synthetic-test-only.tif'
            receipt=write_submission(out,pred,sample,np.ones(grid.SHAPE,bool),
                                     name='Synthetic unit fixture',note='NOT A COMPETITION CANDIDATE')
            self.assertTrue(receipt['template_report']['ok'])
            self.assertFalse(receipt['approved_for_weekly_slot'])
            with rasterio.open(out) as src:
                self.assertEqual(src.shape,grid.SHAPE)
                self.assertEqual(src.transform,grid.TRANSFORM)
                np.testing.assert_array_equal(src.read(1),pred)
            with zipfile.ZipFile(out.with_suffix('.zip')) as z:
                self.assertEqual(z.namelist(),[out.name])
            with self.assertRaises(FileExistsError):
                write_submission(out,pred,sample,np.ones(grid.SHAPE,bool),name='test',note='test')

    def test_evaluator_rejects_empty_truth(self):
        a=np.zeros((10,10)); mask=np.ones_like(a,bool)
        with self.assertRaises(ValueError):
            evaluate(a, dict(region=mask,visible=a.astype(bool),truth=a.astype(bool)), mask)


if __name__ == '__main__':
    unittest.main()
