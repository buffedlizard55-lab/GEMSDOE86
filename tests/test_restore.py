import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import restore_data


class RestoreTests(unittest.TestCase):
    def fixture(self, root, size=4):
        (root / 'research').mkdir()
        pin = dict(repo='owner/history', blob='immutable-test-blob', dest='registry/witness.tif',
                   sha256=hashlib.sha256(b'test').hexdigest(), bytes=size)
        (root / 'research/registry_witness_pin.json').write_text(json.dumps(pin))

    @staticmethod
    def download(*args, **kwargs):
        kwargs['stdout'].write(b'test')

    def test_publish_only_after_hash_and_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            with patch.object(restore_data, 'ROOT', root), patch.object(restore_data.subprocess, 'run', side_effect=self.download) as fetch:
                dest = restore_data.restore_registry_witness()
                self.assertEqual(dest.read_bytes(), b'test')
                self.assertFalse(dest.with_suffix('.partial').exists())
                restore_data.restore_registry_witness()
                self.assertEqual(fetch.call_count, 1)
                dest.write_bytes(b'evil')
                with self.assertRaises(ValueError):
                    restore_data.restore_registry_witness()
                self.assertEqual(fetch.call_count, 1)

    def test_wrong_size_cleans_staged_bytes_without_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root, size=9)
            with patch.object(restore_data, 'ROOT', root), patch.object(restore_data.subprocess, 'run', side_effect=self.download):
                with self.assertRaises(ValueError):
                    restore_data.restore_registry_witness()
            self.assertEqual(list((root / 'data/registry').iterdir()), [])

    def test_network_failure_cleans_staged_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            with patch.object(restore_data, 'ROOT', root), patch.object(restore_data.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'gh')):
                with self.assertRaises(subprocess.CalledProcessError):
                    restore_data.restore_registry_witness()
            self.assertEqual(list((root / 'data/registry').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
