import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_site import check


class SiteTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'docs/evidence').mkdir(parents=True)
        (root / 'index.html').write_text('<a href="docs/index.html">Site</a>')
        (root / 'docs/index.html').write_text('<h1>NOT READY</h1>')
        (root / 'docs/evidence/run-card.json').write_text(json.dumps({
            'submission_ready': False, 'verdict': 'negative'}))

    def test_real_site(self):
        self.assertEqual(check(), [])

    def test_missing_link_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            (root / 'docs/index.html').write_text('<a href="missing.tif">Download</a>')
            self.assertTrue(check(root))

    def test_docs_must_not_link_unpublished_repository_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            (root / 'PROMPT.md').write_text('Exists in Git, not in the Pages artifact')
            (root / 'docs/index.html').write_text('<a href="../PROMPT.md">Brief</a>')
            self.assertTrue(check(root))

    def test_unlinked_tif_and_zip_fail_in_negative_state(self):
        for suffix in ('.tif', '.tiff', '.zip'):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.fixture(root)
                (root / ('docs/hidden' + suffix)).write_bytes(b'not approved')
                self.assertTrue(check(root))

    def test_inventory_cannot_escape_downloads_even_without_docs_html(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            (root / 'docs/index.html').unlink()
            (root / 'index.html').write_text('<h1>Audit</h1>')
            artifact = root / 'outside.tif'
            artifact.write_bytes(b'not a public download')
            (root / 'docs/evidence/download-inventory.json').write_text(json.dumps({
                'artifacts': [{'file': 'outside.tif',
                    'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    'status': 'DO NOT SUBMIT', 'approved_for_weekly_slot': False}]}))
            self.assertTrue(check(root))

    def test_unsupported_ready_claim_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            (root / 'docs/evidence/run-card.json').write_text(json.dumps({
                'submission_ready': True, 'verdict': 'promote', 'raster_sha256': None}))
            self.assertTrue(check(root))


if __name__ == '__main__':
    unittest.main()
