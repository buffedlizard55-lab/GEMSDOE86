"""Test scripts/prepare_data.py under normal and edge conditions."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import rasterio
from rasterio.transform import Affine

ROOT = Path(__file__).resolve().parents[1]
from scripts import prepare_data


class PrepareDataTests(unittest.TestCase):
    def test_prepare_data_on_restored_inputs(self):
        """When bridge files exist, prepare_data should succeed and write manifest cleanly."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            out_manifest = tmp_path / "prepared_manifest.json"
            manifest = prepare_data.prepare(work_dir=tmp_path / "work", manifest_path=out_manifest)
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["grid"]["epsg"], 32611)
            self.assertEqual(manifest["grid"]["height"], 3730)
            self.assertEqual(manifest["grid"]["width"], 3292)
            self.assertEqual(manifest["grid"]["transform"], [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0])
            self.assertEqual(manifest["counts"]["footprint_valid_pixels"], 5167373)
            self.assertEqual(manifest["counts"]["positive_catalogue_label_pixels"], 60988)
            pins = manifest["pins_verified"]
            self.assertTrue(pins["sample_submission"])
            self.assertTrue(pins["existing_faults"])
            self.assertNotIn(False, pins.values())
            if manifest["counts"]["has_features"]:
                self.assertTrue(pins["training_features"])

            self.assertTrue(out_manifest.is_file())
            saved = json.loads(out_manifest.read_text())
            self.assertEqual(saved["counts"]["footprint_valid_pixels"], 5167373)
        tracked_manifest = ROOT / "data" / "prepared_manifest.json"
        self.assertTrue(tracked_manifest.is_file())
        self.assertEqual(json.loads(tracked_manifest.read_text())["grid"]["transform"],
                         [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0])

    def test_missing_files_raises_filenotfound(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            with self.assertRaises(FileNotFoundError):
                prepare_data.prepare(data_dir=Path(empty_dir))

    def test_relative_and_external_data_dir_resolution(self):
        """Relative --data-dir and external paths outside ROOT must not fail relative_to(ROOT)."""
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rel_manifest = tmp_path / "rel_manifest.json"
            rel = prepare_data.prepare(
                data_dir=Path("data/bridge"),
                work_dir=tmp_path / "rel_work",
                manifest_path=rel_manifest,
            )
            self.assertEqual(rel["source_paths"]["sample_submission"], "data/bridge/sample_submission.tif")
            ext_dir = tmp_path / "ext_data"
            ext_dir.mkdir()
            shutil.copyfile(ROOT / "data/bridge/sample_submission.tif", ext_dir / "sample_submission.tif")
            shutil.copyfile(ROOT / "data/bridge/existing_faults.tif", ext_dir / "existing_faults.tif")
            ext_manifest = tmp_path / "ext_manifest.json"
            ext = prepare_data.prepare(
                data_dir=ext_dir,
                work_dir=tmp_path / "ext_work",
                manifest_path=ext_manifest,
            )
            self.assertTrue(ext["source_paths"]["sample_submission"].endswith("sample_submission.tif"))


if __name__ == "__main__":
    unittest.main()
