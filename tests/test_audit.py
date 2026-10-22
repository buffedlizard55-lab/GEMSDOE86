import sys
import unittest
import tempfile
import zipfile
import rasterio
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor')]
from scripts.audit import check_pins, run
from gems57.submission_writer import write_submission
from gems57.uniqueness import dot_overlap, surface_rho
from gems57.evaluate_holdout import evaluate
from gems57 import grid, metric


class SafetyTests(unittest.TestCase):
    def test_shared_bytes_unmodified(self):
        self.assertTrue(check_pins())

    def test_current_run_card_is_negative_and_consistent(self):
        # audit.run() is read-only: it must never overwrite the lane run card.
        before = (ROOT / 'docs/evidence/run-card.json').read_bytes()
        result = run()
        self.assertEqual((ROOT / 'docs/evidence/run-card.json').read_bytes(), before)
        self.assertTrue(result['all_audit_checks_passed'])
        self.assertFalse(result['submission_ready'])
        self.assertEqual(result['verdict'], 'negative')
        card = result['run_card']
        self.assertFalse(card['holdout_dti']['beats_incumbent'])
        self.assertIsNotNone(card['raster_sha256'])
        self.assertLessEqual(len(card['note']), 140)

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
