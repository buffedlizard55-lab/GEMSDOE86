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
        (root / 'research').mkdir()
        shutil.copyfile(ROOT / 'research/template_pin.json', root / 'research/template_pin.json')
        shutil.copytree(ROOT / 'vendor', root / 'vendor', ignore=shutil.ignore_patterns('__pycache__'))
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

    def test_optimistic_card_requires_complete_unique_scan_even_without_stop(self):
        # Tamper only with authorization fields; byte integrity alone must not
        # make an incomplete or duplicate registry report submission-ready.
        for complete, unique in ((False, True), (True, False), (None, True)):
            for field, value in (('verdict', 'promote'), ('submission_ready', True),
                                 ('approved_for_weekly_slot', True)):
                with self.subTest(complete=complete, unique=unique, field=field):
                    with tempfile.TemporaryDirectory() as d:
                        root = Path(d); card, _ = self.fixture(root)
                        card[field] = value
                        (root / 'docs/evidence/run-card.json').write_text(json.dumps(card))
                        path = root / 'docs/evidence/lane86_results.json'
                        lane = json.loads(path.read_text())
                        lane['final_uniqueness'].update(
                            stop_required=False, unique=unique,
                            complete_accessible_scan=complete)
                        path.write_text(json.dumps(lane))
                        with patch.object(validate_download, 'ROOT', root):
                            result = validate_download.validate()
                        self.assertTrue(result['checks']['readiness_respects_shared_stop'])
                        self.assertFalse(result['checks']['readiness_requires_complete_unique_scan'])
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

    def test_untrusted_json_is_rejected_before_raster_open(self):
        for name in ('run-card.json', 'lane86_results.json'):
            for payload in ('{"duplicate": 1, "duplicate": 2}', '{"value": NaN}', '{"value": Infinity}'):
                with self.subTest(name=name, payload=payload), tempfile.TemporaryDirectory() as d:
                    root = Path(d); self.fixture(root)
                    (root / 'docs/evidence' / name).write_text(payload)
                    with patch.object(validate_download, 'ROOT', root), patch.object(validate_download.rasterio, 'open') as opened:
                        with self.assertRaises(ValueError):
                            validate_download.validate()
                        opened.assert_not_called()

    def test_candidate_path_must_be_a_published_tiff(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); card, tif = self.fixture(root)
            private = root / 'private.tif'; shutil.copyfile(tif, private)
            external = root.parent / (root.name + '-external.tif')
            try:
                shutil.copyfile(tif, external)
                symlink = tif.parent / 'escape.tif'; symlink.symlink_to(external)
                for path in (str(external), '../' + external.name, 'private.tif',
                             str(symlink.relative_to(root)), 'docs/evidence/run-card.json'):
                    with self.subTest(path=path):
                        card['submission_file'] = path
                        (root / 'docs/evidence/run-card.json').write_text(json.dumps(card))
                        with patch.object(validate_download, 'ROOT', root), patch.object(validate_download.rasterio, 'open') as opened:
                            with self.assertRaises(ValueError):
                                validate_download.validate()
                            opened.assert_not_called()
            finally:
                external.unlink(missing_ok=True)

    def test_zip_symlink_cannot_escape_download_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); _, tif = self.fixture(root)
            zpath = tif.with_suffix('.zip')
            private = root / 'private.zip'; zpath.rename(private); zpath.symlink_to(private)
            with patch.object(validate_download, 'ROOT', root), patch.object(validate_download.rasterio, 'open') as opened:
                with self.assertRaises(ValueError):
                    validate_download.validate()
                opened.assert_not_called()

    def test_either_vendored_tree_drifting_stops_before_artifact_access(self):
        for relative in ('vendor/gems57/grid.py', 'vendor/template66/gems57/grid.py'):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as d:
                root = Path(d); self.fixture(root)
                with (root / relative).open('a') as stream:
                    stream.write('\n# drift\n')
                with patch.object(validate_download, 'ROOT', root), patch.object(validate_download.rasterio, 'open') as opened:
                    with self.assertRaisesRegex(ValueError, 'Shared tool SHA drift'):
                        validate_download.validate()
                    opened.assert_not_called()

    def test_imported_grid_bytes_are_verified_not_only_local_copies(self):
        with tempfile.TemporaryDirectory() as d:
            fake = Path(d) / 'grid.py'; fake.write_text('# wrong imported module')
            with patch.object(validate_download.G, '__file__', str(fake)):
                with self.assertRaisesRegex(ValueError, 'Shared tool SHA drift'):
                    validate_download.require_shared_tools(ROOT)


if __name__ == '__main__':
    unittest.main()
