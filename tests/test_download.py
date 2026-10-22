"""Read-only regression checks for the inherited negative artifact."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import validate_download


class DownloadTests(unittest.TestCase):
    def fixture(self, root):
        card = json.loads((ROOT / 'docs/evidence/run-card.json').read_text())
        (root / 'docs/evidence').mkdir(parents=True)
        for name in ('run-card.json', 'lane86_results.json'):
            shutil.copyfile(ROOT / 'docs/evidence' / name, root / 'docs/evidence' / name)
        tif = root / card['submission_file']; tif.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / card['submission_file'], tif)
        shutil.copyfile((ROOT / card['submission_file']).with_suffix('.zip'), tif.with_suffix('.zip'))
        return card, tif

    def test_actual_download_format_and_readonly_behavior(self):
        path = ROOT / 'docs/evidence/run-card.json'
        before = path.read_bytes()
        result = validate_download.validate()
        self.assertTrue(result['all_format_checks_passed'])
        self.assertTrue(result['checks']['zip_tif_bytes_equal_registered_tif'])
        self.assertFalse(result['submission_ready'])
        self.assertFalse(result['uniqueness_checker']['unique'])
        self.assertEqual(before, path.read_bytes())

    def test_named_zip_member_with_wrong_bytes_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); _, tif = self.fixture(root)
            with zipfile.ZipFile(tif.with_suffix('.zip'), 'w') as z:
                z.writestr(tif.name, b'wrong TIFF bytes')
            with patch.object(validate_download, 'ROOT', root):
                result = validate_download.validate()
            self.assertTrue(result['checks']['zip_contains_only_this_tif'])
            self.assertFalse(result['checks']['zip_tif_bytes_equal_registered_tif'])
            self.assertFalse(result['all_format_checks_passed'])

    def test_uniqueness_consistency_is_computed_not_hardcoded_true(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); card, _ = self.fixture(root)
            card['correlation_overlap_vs_registry']['final_worst_dot_overlap_literal'] = 0
            (root / 'docs/evidence/run-card.json').write_text(json.dumps(card))
            with patch.object(validate_download, 'ROOT', root):
                result = validate_download.validate()
            self.assertFalse(result['checks']['uniqueness_checker_verbatim'])
            self.assertFalse(result['all_format_checks_passed'])


if __name__ == '__main__':
    unittest.main()
