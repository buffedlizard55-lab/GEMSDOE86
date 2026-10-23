"""Unit and artifact tests for the TRACKB (Phase 2) axis on R0 (``h33-h33-2-b2``).

Runs under both ``pytest`` and ``python -m unittest discover -s tests -v``.
"""
from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from gems86 import trackb_hybrid as tb  # noqa: E402
from gems86_axis import grid_io  # noqa: E402


class TestTrackBDTIAlgebra(unittest.TestCase):
    """Verify the closed-form DTI algebra and marginal inclusion bar from brief section 2."""

    def test_closed_form_matches_gems57_metric(self) -> None:
        rng = np.random.default_rng(20261023)
        for seed_idx in range(6):
            valid = np.ones((28, 30), dtype=bool)
            valid[:2, :] = False
            known = np.zeros_like(valid)
            known[5:12, 4] = True
            truth = (rng.random(valid.shape) < 0.06) & valid & ~known
            truth[14, 8:22] = True  # >= 1 km trace
            pred = ((rng.random(valid.shape) < 0.08) & valid & ~known).astype(np.float32)

            terms = tb.dti_algebra_terms(pred, truth, valid=valid, known=known)
            self.assertAlmostEqual(terms["dti_closed"], terms["dti_metric"], places=9, msg=f"draw {seed_idx}")

    def test_bridging_internal_gap_beats_subkernel_overlap_along_line_truth(self) -> None:
        h, w = 32, 40
        valid = np.ones((h, w), dtype=bool)
        truth = np.zeros((h, w), dtype=bool)
        truth[16, 6:30] = True  # continuous 2.4 km fault trace

        # Two R0-like dots 7 px apart leave a >3 px uncovered blind spot at col 13..14
        pred = np.zeros((h, w), dtype=np.float32)
        pred[16, 10] = 1.0
        pred[16, 17] = 1.0

        bridge_gain = tb.exact_marginal_dti_gain(pred, truth, (16, 13), valid=valid)
        overlap_gain = tb.exact_marginal_dti_gain(pred, truth, (16, 11), valid=valid)
        off_fault_loss = tb.exact_marginal_dti_gain(pred, truth, (3, 3), valid=valid)

        self.assertGreater(bridge_gain["delta_dti"], 0.0)
        self.assertGreater(bridge_gain["delta_dti"], overlap_gain["delta_dti"])
        self.assertLess(off_fault_loss["delta_dti"], 0.0)


class TestTrackBSyntheticExtractionAndVariants(unittest.TestCase):
    """Synthetic geometry tests for trace extraction and the 3 controlled R0 variants."""

    def _make_synthetic_scene(self) -> dict[str, np.ndarray]:
        h, w = 64, 64
        foot = np.ones((h, w), dtype=bool)
        cat = np.zeros((h, w), dtype=bool)
        cat[4:60, 4] = True  # mapped fault on left margin

        parent = np.zeros((h, w), dtype=bool)
        support = np.zeros((h, w), dtype=bool)
        ev = np.zeros((h, w), dtype=np.float32)

        # Trace 1: 1.8 km straight N-S chain at col 24 with one 6-px internal gap (rows 10,13,16,22,25,28)
        for r in (10, 13, 16, 22, 25, 28):
            parent[r, 24] = True
        support[8:36, 24] = True
        ev[8:36, 24] = 3.0

        # Trace 2: 1.5 km straight E-W chain at row 46 (cols 16, 19, 22, 25, 28, 31)
        for c in (16, 19, 22, 25, 28, 31):
            parent[46, c] = True
        support[46, 14:38] = True
        ev[46, 14:38] = 2.2

        # Short 2-dot pair (< 1 km): must NOT be extracted as >= 1 km trace, MUST survive cull1dot
        parent[14, 44] = True
        parent[17, 44] = True
        support[14:18, 44] = True

        # 6 isolated 1-dot singletons (> 5.5 px from every other dot)
        singletons = [(8, 54), (18, 56), (28, 54), (38, 56), (52, 54), (58, 42)]
        for idx, (sr, sc) in enumerate(singletons):
            parent[sr, sc] = True
            ev[sr, sc] = -1.0 + 0.1 * idx

        return {"foot": foot, "cat": cat, "parent": parent, "support": support, "ev": ev}

    def test_bresenham_is_8_connected_and_exact_endpoints(self) -> None:
        for coords in ((5, 7, 19, 12), (20, 30, 8, 11), (10, 10, 10, 10)):
            rs, cs = tb.bresenham_line(*coords)
            self.assertEqual((int(rs[0]), int(cs[0])), (coords[0], coords[1]))
            self.assertEqual((int(rs[-1]), int(cs[-1])), (coords[2], coords[3]))
            if len(rs) > 1:
                step_cheb = np.maximum(np.abs(np.diff(rs)), np.abs(np.diff(cs)))
                self.assertTrue(bool((step_cheb == 1).all()))

    def test_extract_strike_traces_enforces_1km_and_catalogue_buffer(self) -> None:
        sc = self._make_synthetic_scene()
        t1, stats1 = tb.extract_strike_traces(
            sc["parent"], sc["foot"], sc["cat"],
            support_mask=sc["support"], evidence_field=sc["ev"],
        )
        t2, _ = tb.extract_strike_traces(
            sc["parent"], sc["foot"], sc["cat"],
            support_mask=sc["support"], evidence_field=sc["ev"],
        )
        self.assertEqual(stats1["n_traces"], 2)
        self.assertEqual([t["arc_length_km"] for t in t1], [t["arc_length_km"] for t in t2])
        for tr in t1:
            self.assertGreaterEqual(tr["arc_length_km"], 1.0)
            self.assertGreater(tr["min_cat_edt_px"], 3.0)

        # Place a catalogue pixel 2 px away from Trace 2's middle segment: must block Trace 2
        cat_block = sc["cat"].copy()
        cat_block[44, 23] = True
        t_blocked, _ = tb.extract_strike_traces(
            sc["parent"], sc["foot"], cat_block,
            support_mask=sc["support"], evidence_field=sc["ev"],
        )
        self.assertEqual(len(t_blocked), 1)

    def test_three_variants_satisfy_structural_invariants(self) -> None:
        sc = self._make_synthetic_scene()
        traces, _ = tb.extract_strike_traces(
            sc["parent"], sc["foot"], sc["cat"],
            support_mask=sc["support"], evidence_field=sc["ev"],
        )
        edt_cat = ndi.distance_transform_edt(~sc["cat"])

        # 1. cull1dot: deletes only the 6 singletons, keeps the 2-dot pair and both >= 1 km traces
        cull, st_cull = tb.build_cull_singletons(sc["parent"], sc["foot"], sc["cat"])
        self.assertEqual(st_cull["removed"], 6)
        self.assertEqual(st_cull["added"], 0)
        self.assertTrue(cull[14, 44] and cull[17, 44])
        for tr in traces:
            v = tr["vertices_rc"]
            self.assertTrue(bool(cull[v[:, 0], v[:, 1]].all()))

        # 2. bridge1km: exact count preservation, spacing >= 2.8284 px, new mass > 3 px off catalogue
        bridge, st_bridge = tb.build_bridge_traces(
            sc["parent"], sc["foot"], sc["cat"], traces, sc["ev"], support_mask=sc["support"],
        )
        self.assertEqual(int(bridge.sum()), int(sc["parent"].sum()))
        new_b = bridge & ~sc["parent"]
        self.assertGreater(int(new_b.sum()), 0)
        self.assertTrue(bool((edt_cat[new_b] > 3.0).all()))
        self.assertGreaterEqual(st_bridge["nn_min_px_before_after"][1], tb.PARENT_MIN_SPACING_PX - 1e-4)
        # Verify the 6-px internal gap on Trace 1 (around row 19, col 24) received a bridge dot
        self.assertTrue(bool(bridge[18:21, 24].any()))

        # 3. rendertop120 (top_k=1 on synthetic scene so connectors <= removable pool):
        render, st_render = tb.build_render_top_traces(
            sc["parent"], sc["foot"], sc["cat"], traces, sc["ev"], top_k=1,
        )
        self.assertEqual(int(render.sum()), int(sc["parent"].sum()))
        new_r = render & ~sc["parent"]
        self.assertTrue(bool((edt_cat[new_r] > 3.0).all()))
        self.assertGreater(st_render["added"], 0)


class TestTrackBShippedArtifacts(unittest.TestCase):
    """Verify geologist dossier, evidence card, ledger rows, and local GeoJSON/rasters."""

    def test_geojson_and_geologist_dossier_are_valid_and_synced(self) -> None:
        card = json.loads((ROOT / "evidence" / "trackb_hybrid_20261023.json").read_text(encoding="utf-8"))
        md_path = ROOT / "evidence" / "trackb-geologist-dossier.md"
        self.assertTrue(md_path.is_file(), "missing geologist dossier markdown")
        md_text = md_path.read_text(encoding="utf-8")
        for idx in range(1, 121):
            self.assertIn(f"`TB-{idx:04d}`", md_text)

        gj_path = ROOT / card["trace_inventory"]["geojson_path"]
        if not gj_path.is_file():
            # Local candidate GeoJSON is gitignored under /releases/trackb/*.geojson (IR-86-TRACKB-04)
            return

        import hashlib
        self.assertEqual(hashlib.sha256(gj_path.read_bytes()).hexdigest(), card["trace_inventory"]["geojson_sha256"])
        fc = json.loads(gj_path.read_text(encoding="utf-8"))
        self.assertEqual(fc["type"], "FeatureCollection")
        features = fc["features"]
        self.assertEqual(len(features), 120)

        quads = set()
        for idx, feat in enumerate(features, start=1):
            self.assertEqual(feat["type"], "Feature")
            self.assertEqual(feat["geometry"]["type"], "LineString")
            coords = feat["geometry"]["coordinates"]
            self.assertGreaterEqual(len(coords), 2)
            for lon, lat in coords:
                self.assertGreaterEqual(lon, -121.0)
                self.assertLessEqual(lon, -115.0)
                self.assertGreaterEqual(lat, 36.5)
                self.assertLessEqual(lat, 42.0)
            props = feat["properties"]
            self.assertEqual(props["rank"], idx)
            self.assertGreaterEqual(props["arc_length_km"], 1.0)
            self.assertGreater(props["min_catalogue_clearance_m"], 300.0)
            para = props["evidence_paragraph"]
            self.assertGreaterEqual(len(para), 300)
            self.assertIn(props["trace_id"], md_text)
            quads.add(props["quadrant"])

        # Susceptibility-normalised ranking must span all 4 quadrants of the footprint
        self.assertEqual(quads, {"NW", "NE", "SW", "SE"})

    def test_ledger_and_evidence_card_invariants(self) -> None:
        card = json.loads((ROOT / "evidence" / "trackb_hybrid_20261023.json").read_text(encoding="utf-8"))
        self.assertEqual(card["axis"], "TRACKB")
        self.assertTrue(card["r0_rebuild"]["byte_exact_match"])
        self.assertEqual(
            card["r0_rebuild"]["rebuilt_sha256"],
            "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
        )
        canary = card["report_only_instruments"]["leakage_canary"]
        self.assertFalse(canary["stop"])
        self.assertLessEqual(canary["max_symmetric_auc_vs_catalogue"], 0.90)
        self.assertLessEqual(canary["max_symmetric_auc_vs_sgmc_off_catalogue"], 0.90)

        with (ROOT / "ledger" / "submissions.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        our_values = {"cull1dot", "bridge1km", "rendertop120"}
        trackb_rows = [r for r in rows if r["axis"] == "TRACKB" and r["value"] in our_values]
        self.assertEqual([r["value"] for r in trackb_rows], ["cull1dot", "bridge1km", "rendertop120"])
        for r in trackb_rows:
            pct = float(r["pct_changed"])
            self.assertGreaterEqual(pct, 1.0)
            self.assertLessEqual(pct, 50.0)
            self.assertEqual(r["status"], "BUILT")
            self.assertEqual(r["receipt"], "N")
            self.assertEqual(r["receipt_score"], "")
            self.assertEqual(r["score"], "")
            self.assertEqual(r["evidence_class"], "MODEL")

        # Global (parent, axis, value) uniqueness across non-duplicate BUILT session rows
        built_keys = [
            (r["parent"], r["axis"], r["value"])
            for r in rows
            if r["status"] == "BUILT" and r["axis"]
        ]
        self.assertEqual(len(built_keys), len(set(built_keys)), "duplicate BUILT (parent, axis, value) in ledger")

    def test_disk_releases_match_geojson_traces_when_present(self) -> None:
        card = json.loads((ROOT / "evidence" / "trackb_hybrid_20261023.json").read_text(encoding="utf-8"))
        render_rec = card["variants"]["rendertop120"]
        render_path = ROOT / render_rec["zeros_path"]
        gj_path = ROOT / card["trace_inventory"]["geojson_path"]
        if not render_path.is_file() or not gj_path.is_file():
            self.skipTest("local gitignored TRACKB GeoTIFFs/GeoJSON are not present in this checkout")

        ctx = grid_io.load_context()
        foot = ctx["footprint"]
        cat = ctx["catalogue"]
        edt_cat = ndi.distance_transform_edt(~cat)
        r0 = grid_io.load_dots(
            ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
            foot,
        )
        render_dots = grid_io.load_dots(render_path, foot)
        self.assertEqual(int(render_dots.sum()), 37_654)
        self.assertTrue(bool((edt_cat[render_dots & ~r0] > 3.0).all()))

        # Every GeoJSON trace vertex & Bresenham segment pixel must be emitted in rendertop120
        fc = json.loads(gj_path.read_text(encoding="utf-8"))
        from rasterio.warp import transform as warp_transform
        tr = ctx["grid"]["transform"]
        for feat in fc["features"]:
            coords = feat["geometry"]["coordinates"]
            lons = [pt[0] for pt in coords]
            lats = [pt[1] for pt in coords]
            xs, ys = warp_transform("EPSG:4326", "EPSG:32611", lons, lats)
            v_cols = np.floor((np.asarray(xs) - float(tr.c)) / float(tr.a) + 1e-6).astype(int)
            v_rows = np.floor((np.asarray(ys) - float(tr.f)) / float(tr.e) + 1e-6).astype(int)
            for idx in range(len(v_rows) - 1):
                rs, cs = tb.bresenham_line(int(v_rows[idx]), int(v_cols[idx]),
                                           int(v_rows[idx + 1]), int(v_cols[idx + 1]))
                self.assertTrue(
                    bool(render_dots[rs, cs].all()),
                    f"GeoJSON trace {feat['id']} missing pixels in {render_path.name}",
                )


if __name__ == "__main__":
    unittest.main()
