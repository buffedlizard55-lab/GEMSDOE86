import hashlib
import base64
from types import SimpleNamespace
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import restore_protocol_data as restore_data


class RestoreTests(unittest.TestCase):
    def fixture(self, root, size=4):
        (root / 'research').mkdir()
        pin = dict(repo='owner/history', blob=hashlib.sha1(b'blob 4\0test').hexdigest(), dest='registry/witness.tif',
                   sha256=hashlib.sha256(b'test').hexdigest(), bytes=size)
        (root / 'research/registry_witness_pin.json').write_text(json.dumps(pin))

    @staticmethod
    def download(*args, **kwargs):
        return SimpleNamespace(stdout=json.dumps(dict(encoding='base64', sha=hashlib.sha1(b'blob 4\0test').hexdigest(), size=4, content=base64.b64encode(b'test').decode())).encode())

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

    def test_blob_json_must_match_git_object_identity(self):
        blob = hashlib.sha1(b'blob 4\0test').hexdigest()
        response = SimpleNamespace(stdout=json.dumps(dict(encoding='base64', sha=blob,
            size=4, content=base64.b64encode(b'evil').decode())).encode())
        stream = io.BytesIO()
        with patch.object(restore_data.subprocess, 'run', return_value=response):
            with self.assertRaises(ValueError):
                restore_data.write_blob('test/repo', blob, stream)
        self.assertEqual(stream.getvalue(), b'')

    def test_network_failure_cleans_staged_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            with patch.object(restore_data, 'ROOT', root), patch.object(restore_data.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'gh')):
                with self.assertRaises(subprocess.CalledProcessError):
                    restore_data.restore_registry_witness()
            self.assertEqual(list((root / 'data/registry').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
