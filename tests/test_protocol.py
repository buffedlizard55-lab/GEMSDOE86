"""Safety and synthetic geometry tests; no model experiments or score claims."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import rasterio
from affine import Affine

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor')]
from scripts.session_preflight import run
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

    def test_three_pixel_spacing_does_not_imply_disjoint_kernel_support(self):
        # Geometry only, not HOLDOUT-DTI or a geological experiment. The H33
        # explanation must not claim spacing near R makes radius-R cones disjoint.
        y, x = np.indices((9, 12))
        left = np.maximum(0, 1 - np.hypot(y - 4, x - 4) / 3)
        right = np.maximum(0, 1 - np.hypot(y - 4, x - 7) / 3)
        self.assertTrue(((left > 0) & (right > 0)).any())
        self.assertGreater((left + right).sum(), np.maximum(left, right).sum())

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
        path = ROOT / 'docs/evidence/protocol-run-card.json'
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

    def test_model_entrypoint_stops_before_surface_or_any_experiment(self):
        from scripts.run_lane86 import main
        with patch('scripts.protocol_preflight.measure', return_value={'universal_overlap_blocker': True}), patch('scripts.run_lane86.build_surface') as build:
            with self.assertRaisesRegex(RuntimeError, 'STOP_LITERAL_OVERLAP_UNSATISFIABLE'):
                main()
            build.assert_not_called()

    def test_concurrent_primary_model_entrypoints_also_stop(self):
        from scripts.build_submission import main as build
        from scripts.experiment import main as experiment
        from scripts.run_experiment import run as rmrb86
        from scripts.run_lane86b import main as h86b
        from scripts.run_h86_wvb import main as h86_wvb
        from scripts.run_lane86c import main as h86c
        with patch('scripts.protocol_preflight.measure', return_value={'universal_overlap_blocker': True}):
            for entrypoint in (build, experiment, rmrb86, h86b, h86_wvb, h86c):
                with self.assertRaisesRegex(RuntimeError, 'STOP_LITERAL_OVERLAP_UNSATISFIABLE'):
                    entrypoint()

    def test_registry_reproduction_tolerates_only_last_bit_rho(self):
        from scripts.check_registry_reproduction import differences
        base = {'spearman_full_footprint': .1, 'stop_required': True, 'worst_dot_overlap': 1.0}
        self.assertEqual(differences(base, {**base, 'spearman_full_footprint': .1 + 1e-15}), [])
        self.assertTrue(differences(base, {**base, 'spearman_full_footprint': .1 + 1e-5}))
        self.assertTrue(differences(base, {**base, 'stop_required': False}))
        self.assertTrue(differences(base, {**base, 'worst_dot_overlap': 1.0 - 1e-15}))

    def test_protocol_run_never_overwrites_concurrent_model_card(self):
        path = ROOT / 'docs/evidence/run-card.json'
        before = path.read_bytes()
        run(write=False)
        self.assertEqual(before, path.read_bytes())

    def test_inherited_registry_measurement_is_negative_and_incomplete(self):
        result = json.loads((ROOT / 'docs/evidence/inherited-registry-check.json').read_text())
        model = json.loads((ROOT / 'docs/evidence/run-card.json').read_text())
        self.assertEqual(result['candidate_file_sha256'], model['raster_sha256'])
        self.assertFalse(result['unique'])
        self.assertFalse(result['complete_accessible_scan'])
        self.assertTrue(result['stop_required'])
        self.assertEqual(result['worst_dot_overlap'], 1)
        self.assertTrue(result['rows'][0]['duplicate_by_overlap'])

    def test_pruning_inequality_against_shared_component_formula(self):
        # Synthetic arithmetic identity only, not an experiment or score claim.
        from gems57.metric import dti_from_components, EPS
        rng = np.random.default_rng(86)
        for _ in range(200):
            N = rng.uniform(1, 1000); T = rng.uniform(.1, .9) * N
            F = rng.uniform(.1, 1000); a = rng.uniform(0, T); b = rng.uniform(0, F)
            before = dti_from_components(T, F, N - T)
            after = dti_from_components(T - a, F - b, N - T + a)
            self.assertEqual(after > before, T * b > a * (F + 4 * N + 5 * EPS))

    def test_snapshot_proves_negative_not_fake_candidate_clearance(self):
        card = json.loads((ROOT / 'docs/evidence/protocol-run-card.json').read_text())
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
