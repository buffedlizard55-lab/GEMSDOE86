import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor")]
from gems86_rmrb import features, model


class ResearchTests(unittest.TestCase):
    def test_feature_cache_receipt_pins_current_builder(self):
        receipt = json.loads((ROOT / "docs/evidence/feature-cache.json").read_text())
        digest = hashlib.sha256((ROOT / "src/gems86_rmrb/features.py").read_bytes()).hexdigest()
        self.assertEqual(receipt["source"]["builder_sha256"], digest)
        self.assertEqual(receipt["names"], list(features.NAMES))
        self.assertTrue(receipt["catalogue_free"])

    def test_run_card_is_consistent_with_evidence_and_writer_receipt(self):
        card = json.loads((ROOT / "docs/evidence/rmrb86-run-card.json").read_text())
        holdout = json.loads((ROOT / "docs/evidence/holdout.json").read_text())
        receipt = json.loads((ROOT / "docs/downloads/gems86-rmrb-kthu-rtp-37654-20261022-DO-NOT-SUBMIT.json").read_text())
        score = holdout["scores"]["rmrb_candidate"]
        self.assertEqual(card["raster_sha256"], receipt["sha256"])
        self.assertEqual(card["holdout_dti"]["value"], score["dti"])
        self.assertEqual(card["holdout_dti"]["ci95"], score["ci95"])
        self.assertEqual(card["holdout_dti"]["withheld_positives"], score["withheld_positive_pixels"])
        self.assertFalse(card["safe_to_submit"])
        self.assertIn("DO-NOT-SUBMIT", receipt["file"])

    def test_spaced_emitter_budget_and_separation(self):
        yy, xx = np.mgrid[:20, :20]
        surface = (yy * 20 + xx).astype(np.float32) / 400
        eligible = np.ones((20, 20), bool)
        dots, info = model.spaced_dots(surface, eligible, budget=12, radius=2, tie=surface)
        self.assertEqual(info["emitted"], 12)
        coords = np.argwhere(dots)
        for i in range(len(coords)):
            distance = np.sqrt(((coords[i + 1:] - coords[i]) ** 2).sum(axis=1))
            self.assertTrue((distance > 2).all())

    def test_radiometric_nodata_is_reported_and_filled(self):
        array = np.array([[1.0, np.nan], [3.0, 5.0]], np.float32)
        footprint = np.ones((2, 2), bool)
        clean, stats = features.clean_scale(array, footprint)
        self.assertEqual(stats["missing_inside_footprint"], 1)
        self.assertTrue(np.isfinite(clean).all())
        self.assertTrue(((clean >= 0) & (clean <= 1)).all())

    def test_site_leads_with_unambiguous_decision_and_download(self):
        html = (ROOT / "docs/index.html").read_text()
        self.assertIn("NO FILE IS CLEARED TO SUBMIT", html)
        self.assertIn("Do not upload any file linked from this page", html)
        self.assertIn("HISTORICAL PROMOTE — NOT CLEARED TO SUBMIT", html)
        self.assertIn("byte-distinct research GeoTIFFs", html)
        self.assertIn("DO-NOT-SUBMIT.tif", html)


if __name__ == "__main__":
    unittest.main()
