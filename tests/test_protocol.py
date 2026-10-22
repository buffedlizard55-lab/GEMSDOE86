"""Safety and synthetic geometry tests; no model experiments or score claims."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import rasterio
from affine import Affine

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor')]
from scripts.audit import run
from scripts.protocol_preflight import verify_file
from gems57.uniqueness import saturation_certificate, dot_overlap


class ProtocolTests(unittest.TestCase):
    def fixture(self, path, values, transform=Affine(100, 0, 0, 0, -100, 1000)):
        with rasterio.open(path, 'w', driver='GTiff', height=values.shape[0],
                           width=values.shape[1], count=1, dtype='float32',
                           crs='EPSG:32611', transform=transform) as dst:
            dst.write(values.astype('float32'), 1)

    def test_full_positive_surface_blocks_even_geologically_unrelated_dots(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'prior.tif'
            a = np.full((12, 12), .001, np.float32)
            self.fixture(path, a)
            fp = np.ones(a.shape, bool)
            cat = np.zeros_like(fp); cat[0, :] = True
            report = saturation_certificate(path, fp, cat)
            self.assertTrue(report['universal_overlap_blocker'])
            self.assertEqual(report['uncovered_allowed_pixels'], 0)
            for y, x in [(1, 1), (8, 3), (11, 11)]:
                dots = np.zeros_like(a); dots[y, x] = 1
                self.assertEqual(dot_overlap(dots, a), 1)

    def test_sparse_surface_is_not_a_universal_certificate(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'sparse.tif'
            a = np.zeros((12, 12), np.float32); a[1, 1] = 1
            self.fixture(path, a)
            report = saturation_certificate(path, np.ones_like(a, bool))
            self.assertFalse(report['universal_overlap_blocker'])
            self.assertGreater(report['uncovered_allowed_pixels'], 0)

    def test_empty_allowed_domain_cannot_certify(self):
        a = np.ones((12, 12), bool)
        with self.assertRaises(ValueError):
            saturation_certificate('unused.tif', a, a)
        with self.assertRaises(ValueError):
            saturation_certificate('unused.tif', ~a)

    def test_same_shape_wrong_transform_cannot_certify(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'wrong-grid.tif'
            a = np.ones((12, 12), np.float32)
            self.fixture(path, a)
            with self.assertRaises(ValueError):
                saturation_certificate(path, a.astype(bool), expected_grid=(
                    a.shape, rasterio.crs.CRS.from_epsg(32611), Affine(100, 0, 100, 0, -100, 1000)))

    def test_integrity_checks_reject_corruption_and_wrong_size(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'bytes'
            p.write_bytes(b'test')
            digest = hashlib.sha256(b'test').hexdigest()
            verify_file(p, digest, 4)
            with self.assertRaises(ValueError):
                verify_file(p, digest, 3)
            p.write_bytes(b'evil')
            with self.assertRaises(ValueError):
                verify_file(p, digest, 4)

    def test_nonwriting_audit_preserves_published_evidence(self):
        path = ROOT / 'docs/evidence/run-card.json'
        before = path.read_bytes()
        run(write=False)
        self.assertEqual(before, path.read_bytes())

    def test_corrupt_inputs_and_missing_data_never_clear(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertFalse(run(data_dir=root, write=False)['submission_ready'])
            (root / 'sample_submission.tif').write_bytes(b'corrupt')
            (root / 'existing_faults.tif').write_bytes(b'corrupt')
            card = run(data_dir=root, write=False)
            self.assertFalse(card['preflight_checks']['sample_mirror_sha_matches'])
            self.assertFalse(card['preflight_checks']['input_grids_match'])
            self.assertFalse(card['submission_ready'])

    def test_owner_prompt_is_preserved_in_readme(self):
        readme = (ROOT / 'README.md').read_text()
        archive = readme.split('<!-- OWNER_PROMPT_ARCHIVE_START -->', 1)[1].split('<!-- OWNER_PROMPT_ARCHIVE_END -->', 1)[0]
        self.assertEqual(archive.strip(), (ROOT / 'research/OWNER_PROMPT.md').read_text().strip())

    def test_snapshot_proves_negative_not_fake_candidate_clearance(self):
        card = json.loads((ROOT / 'docs/evidence/run-card.json').read_text())
        cert = card['correlation_overlap_vs_registry']['universal_witness']
        self.assertTrue(cert['universal_overlap_blocker'])
        self.assertEqual(cert['direct_support_uncovered_allowed_pixels'], 0)
        self.assertFalse(cert['registry_complete'])
        self.assertFalse(cert['candidate_generated'])
        self.assertIsNone(card['raster_sha256'])
        self.assertFalse(card['submission_ready'])
        self.assertEqual(card['experiments_run'], 0)


if __name__ == '__main__':
    unittest.main()
