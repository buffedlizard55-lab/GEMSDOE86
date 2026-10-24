"""Adversarial publication tests; no geological experiments or slot use."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import numpy as np
import rasterio

from scripts import audit_downloads
from scripts.check_site import check, load_inventory

ROOT = Path(__file__).resolve().parents[1]


class PublicationTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'docs/evidence').mkdir(parents=True)
        (root / 'docs/downloads').mkdir()
        (root / 'index.html').write_text('<a href="docs/index.html">Site</a>')
        (root / 'docs/index.html').write_text('<h1>DO NOT SUBMIT</h1>')
        (root / 'docs/evidence/run-card.json').write_text(json.dumps({'submission_ready': False, 'verdict': 'negative'}))
        entry = copy.deepcopy(json.loads((ROOT / 'docs/evidence/download-inventory.json').read_text())['artifacts'][0])
        path = root / entry['file']
        for suffix in ('.tif', '.zip', '.json'):
            shutil.copyfile((ROOT / entry['file']).with_suffix(suffix), path.with_suffix(suffix))
        self.inventory(root, [entry])
        return entry, path

    def inventory(self, root, entries):
        (root / 'docs/evidence/download-inventory.json').write_text(json.dumps({'artifacts': entries}))

    def test_real_report_reproduces_without_mutating_model_cards(self):
        cards = {p: p.read_bytes() for p in (ROOT / 'docs/evidence').glob('*card.json')}
        actual = audit_downloads.audit()
        expected = json.loads((ROOT / audit_downloads.REPORT).read_text())
        self.assertEqual(actual, expected)
        self.assertEqual(audit_downloads.render(actual), (ROOT / audit_downloads.PAGE).read_text())
        self.assertEqual(actual['artifact_count'], 14)  # 10 inherited + faulthalo + H86E + GAPRES + H86E-MMT
        self.assertFalse(actual['safe_to_submit'])
        card = audit_downloads.review_card(actual)
        self.assertEqual(card, json.loads((ROOT / audit_downloads.CARD).read_text()))
        self.assertEqual(card['verdict'], 'negative')
        self.assertIsNone(card['raster_sha256'])
        self.assertIsNone(card['validator']['values_in_0_1'])
        self.assertLessEqual(len(card['note']), 140)
        for path, before in cards.items():
            self.assertEqual(path.read_bytes(), before)

    def test_missing_inventory_duplicate_paths_and_escaping_paths_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); entry, path = self.fixture(root)
            self.assertEqual(check(root), [])
            for name in ('../escape.tif', '/absolute.tif', 'private.tif', 'docs/downloads/no.json'):
                self.inventory(root, [{**entry, 'file': name}])
                self.assertTrue(check(root), name)
            self.inventory(root, [entry, entry])
            self.assertTrue(check(root))
            self.inventory(root, [entry, {**entry, 'file': 'docs/downloads/./' + path.name}])
            self.assertTrue(check(root))
            (root / 'docs/evidence/download-inventory.json').unlink()
            self.assertTrue(check(root))

    def test_symlink_cannot_publish_repository_only_raster(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); entry, path = self.fixture(root)
            private = root / 'private.tif'
            path.rename(private)
            path.symlink_to(private)
            self.assertTrue(check(root))

    def test_inventory_boolean_and_status_are_not_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); entry, _ = self.fixture(root)
            for changes in ({'approved_for_weekly_slot': 0}, {'approved_for_weekly_slot': True},
                            {'status': 'DO NOT SUBMIT / actually ready'}, {'sha256': 'invalid'}):
                self.inventory(root, [{**entry, **changes}])
                self.assertTrue(check(root))

    def test_zip_required_even_when_not_linked_and_must_match_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, path = self.fixture(root)
            path.with_suffix('.zip').unlink()
            self.assertTrue(check(root))
            with zipfile.ZipFile(path.with_suffix('.zip'), 'w') as z:
                z.writestr(path.name, b'wrong bytes')
            self.assertTrue(check(root))

    def test_tiff_extension_zip_matches_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); entry, path = self.fixture(root)
            new = path.with_suffix('.tiff'); path.rename(new)
            self.inventory(root, [{**entry, 'file': str(new.relative_to(root))}])
            with zipfile.ZipFile(new.with_suffix('.zip'), 'w') as z:
                z.writestr(new.name, new.read_bytes())
            self.assertEqual(check(root), [])

    def test_summary_and_card_cannot_claim_readiness_even_with_a_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); entry, _ = self.fixture(root)
            (root / 'docs/data').mkdir()
            (root / 'docs/data/summary.json').write_text(json.dumps({'submission_ready': False, 'safe_to_submit': True}))
            self.assertTrue(check(root))
            (root / 'docs/data/summary.json').unlink()
            (root / 'docs/evidence/run-card.json').write_text(json.dumps({
                'submission_ready': True, 'verdict': 'promote', 'raster_sha256': entry['sha256']}))
            self.assertTrue(check(root))

    def test_submission_dir_binaries_sidecar_cards_and_ready_html_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            self.assertEqual(check(root), [])
            (root / 'submission').mkdir()
            rogue = root / 'submission/rogue.tif'
            rogue.write_bytes(b'smuggled')
            self.assertTrue(check(root))
            rogue.unlink()
            sidecar = root / 'docs/evidence/spt-run-card.json'
            sidecar.write_text(json.dumps({'verdict': 'promote-candidate', 'submission_ready': True}))
            self.assertTrue(check(root))
            sidecar.unlink()
            bad_html = root / 'docs/submit.html'
            bad_html.write_text('<!doctype html><html><body><h1>READY TO DOWNLOAD</h1></body></html>')
            self.assertTrue(check(root))
            bad_html.write_text('<!doctype html><html><body><a href="https://raw.githubusercontent.com/org/repo/main/submission/x.tif">dl</a></body></html>')
            self.assertTrue(check(root))

    def masks(self):
        with rasterio.open(ROOT / 'data/bridge/sample_submission.tif') as src:
            footprint = np.isfinite(src.read(1)) & (src.read_masks(1) > 0)
        with rasterio.open(ROOT / 'data/bridge/existing_faults.tif') as src:
            catalogue = src.read(1) > 0
        return footprint, catalogue

    def test_bad_receipt_identity_or_approval_fails(self):
        footprint, catalogue = self.masks()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); entry, path = self.fixture(root)
            receipt_path = path.with_suffix('.json')
            original = json.loads(receipt_path.read_text())
            for key, bad in (('sha256', 'bad'), ('bytes', 0), ('note', 'x' * 141),
                             ('submission_name', ''), ('note_chars', -1), ('approved_for_weekly_slot', True),
                             ('promoted', True), ('zip_sha256', 'bad'), ('file', 'another.tif')):
                receipt_path.write_text(json.dumps({**original, key: bad}))
                with self.subTest(key=key), self.assertRaises(ValueError):
                    audit_downloads.audit_artifact(path, entry, ROOT / 'data/bridge/sample_submission.tif', footprint, catalogue)

    def test_invalid_raster_values_fail_even_with_updated_hash_and_receipt(self):
        footprint, catalogue = self.masks()
        y, x = np.argwhere(footprint & ~catalogue)[0]
        for bad in (np.nan, np.inf, -0.01, 1.01):
            with self.subTest(value=bad), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); entry, path = self.fixture(root)
                with rasterio.open(path, 'r+') as src:
                    src.write(np.array([[bad]], np.float32), 1, window=((y, y + 1), (x, x + 1)))
                entry['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                receipt_path = path.with_suffix('.json')
                receipt = json.loads(receipt_path.read_text())
                receipt.update(sha256=entry['sha256'], bytes=path.stat().st_size)
                with zipfile.ZipFile(path.with_suffix('.zip'), 'w') as z:
                    z.writestr(path.name, path.read_bytes())
                receipt['zip_sha256'] = hashlib.sha256(path.with_suffix('.zip').read_bytes()).hexdigest()
                receipt_path.write_text(json.dumps(receipt))
                with self.assertRaisesRegex(ValueError, 'failed checks'):
                    audit_downloads.audit_artifact(path, entry, ROOT / 'data/bridge/sample_submission.tif', footprint, catalogue)

    def test_published_pages_do_not_reintroduce_unsupported_concurrent_claims(self):
        pages = '\n'.join(path.read_text() for path in (ROOT / 'docs').glob('*.html'))
        for unsupported in ('PEER-REVIEWED METHODOLOGY &amp; VALIDATED PROOF',
                            'adjacent dots have non-overlapping triangular tolerance cones',
                            'any non-empty prediction geometrically yields',
                            'Guarantees zero'):
            self.assertNotIn(unsupported, pages)

    def test_h86b_cannot_bypass_preflight(self):
        from scripts.run_lane86b import main
        with self.assertRaises(TypeError):
            main(skip_literal_preflight=True)
        with patch('scripts.protocol_preflight.require_feasible', side_effect=RuntimeError('STOP')):
            with patch('scripts.run_lane86b.F.build_physical_planes') as build:
                with self.assertRaisesRegex(RuntimeError, 'STOP'):
                    main()
                build.assert_not_called()

    def test_tampered_quarantined_submission_bytes_fail_site_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            shutil.copyfile(ROOT / 'docs/evidence/spt-full-support-witness-audit.json',
                            root / 'docs/evidence/spt-full-support-witness-audit.json')
            shutil.copytree(ROOT / 'submission', root / 'submission')
            self.assertEqual(check(root), [])
            spt_doc = json.loads((root / 'docs/evidence/spt-full-support-witness-audit.json').read_text())
            cand_tif = root / spt_doc['candidate_file']
            with zipfile.ZipFile(cand_tif.with_suffix('.zip'), 'w') as z:
                z.writestr(cand_tif.name, b'tampered')
            self.assertTrue(any('Quarantined submission ZIP payload differs' in err for err in check(root)))
            cand_tif.write_bytes(b'tampered')
            self.assertTrue(any('Quarantined submission TIFF SHA differs' in err for err in check(root)))


if __name__ == '__main__':
    unittest.main()
