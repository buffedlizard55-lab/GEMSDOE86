"""Unit and integration tests for Session-3 Lane H86C-KSLB."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from gems57.network import local_strike  # noqa: E402
import audit_h86c  # noqa: E402
import build_site  # noqa: E402
import h86c_features as F  # noqa: E402
import run_lane86c as R  # noqa: E402


class H86CKslbTests(unittest.TestCase):
    def test_ast_zero_leakage_in_physical_planes(self):
        chk = audit_h86c.ast_zero_leakage_check()
        self.assertTrue(chk["ok"], chk["violations"])
        self.assertEqual(len(F.PHYS_FEATURES), 48)
        self.assertEqual(len(set(F.PHYS_FEATURES)), 48)

    def test_spin2_edge_director_matches_network_local_strike_all_axes(self):
        """Verify algebraic coordinate equivalence on N-S, E-W, and NE-SW ridges."""
        H, W = 64, 64
        yy, xx = np.mgrid[:H, :W].astype(np.float32)

        # Case 1: N-S trace (col=32), step across x -> strike = 0 deg -> cos(2s)=+1, sin(2s)=0
        vis_ns = np.zeros((H, W), dtype=bool)
        vis_ns[8:56, 32] = True
        s_ns, _ = local_strike(vis_ns, smooth_px=3.0)
        f_ns = np.tanh((xx - 32.0) / 2.0).astype(np.float32)
        c2, s2, coh = F._spin2_edge_director(f_ns, 1.0, 2.0)
        self.assertGreater(float(coh[32, 32]), 0.90)
        self.assertAlmostEqual(float(c2[32, 32]), float(np.cos(np.radians(2.0 * s_ns[32, 32]))), places=2)
        self.assertAlmostEqual(float(s2[32, 32]), float(np.sin(np.radians(2.0 * s_ns[32, 32]))), places=2)

        # Case 2: E-W trace (row=32), step across y -> strike = 90 deg -> cos(2s)=-1, sin(2s)=0
        vis_ew = np.zeros((H, W), dtype=bool)
        vis_ew[32, 8:56] = True
        s_ew, _ = local_strike(vis_ew, smooth_px=3.0)
        f_ew = np.tanh((yy - 32.0) / 2.0).astype(np.float32)
        c2e, s2e, _ = F._spin2_edge_director(f_ew, 1.0, 2.0)
        self.assertAlmostEqual(float(c2e[32, 32]), float(np.cos(np.radians(2.0 * s_ew[32, 32]))), places=2)
        self.assertAlmostEqual(float(s2e[32, 32]), 0.0, places=2)

        # Case 3: NE-SW trace (row + col = 64), step across (row + col) -> strike = 45 deg -> cos(2s)=0, sin(2s)=+1
        vis_ne = np.zeros((H, W), dtype=bool)
        for k in range(12, 52):
            vis_ne[64 - k, k] = True
        s_ne, _ = local_strike(vis_ne, smooth_px=3.0)
        f_ne = np.tanh((yy + xx - 64.0) / 2.5).astype(np.float32)
        c2d, s2d, _ = F._spin2_edge_director(f_ne, 1.0, 2.0)
        dot_align = c2d[32, 32] * np.cos(np.radians(2.0 * s_ne[32, 32])) + s2d[32, 32] * np.sin(np.radians(2.0 * s_ne[32, 32]))
        self.assertGreater(float(dot_align), 0.95)

    def test_filament_enhance_sharpens_line_and_suppresses_isolated_speckle(self):
        H, W = 64, 64
        valid = np.ones((H, W), dtype=bool)
        line_img = np.zeros((H, W), dtype=np.float32)
        line_img[12:52, 32] = 0.80
        blob_img = np.zeros((H, W), dtype=np.float32)
        blob_img[32, 32] = 0.80

        resp_line = F.filament_enhance(line_img, valid)
        resp_blob = F.filament_enhance(blob_img, valid)
        self.assertGreater(float(resp_line[32, 32]), 0.65)
        self.assertLess(float(resp_blob[32, 32]), 0.25)

    def test_kslb_kinematics_eliminates_isotropic_straight_flank_sausage(self):
        """Straight uncorroborated fault flank must have ~0 hinge_concord_splay,
        whereas strike-concordant physical corridor activates cleanly."""
        H, W = 80, 80
        vis = np.zeros((H, W), dtype=bool)
        vis[15:65, 40] = True  # Straight N-S fault (zero bend curvature)

        # Orthogonal physical director (E-W: cos2=-1, sin2=0) -> zero concordance
        pc2_orth = np.full((H, W), -1.0, dtype=np.float32)
        ps2_orth = np.zeros((H, W), dtype=np.float32)
        pcoh = np.ones((H, W), dtype=np.float32)
        kc_orth = F.compute_kslb_kinematics(vis, pc2_orth, ps2_orth, pcoh)

        # Parallel physical director (N-S: cos2=+1, sin2=0) -> strong concordance
        pc2_par = np.full((H, W), 1.0, dtype=np.float32)
        ps2_par = np.zeros((H, W), dtype=np.float32)
        kc_par = F.compute_kslb_kinematics(vis, pc2_par, ps2_par, pcoh)

        self.assertLess(float(kc_orth["hinge_concord_splay"][40, 46]), 0.05)
        self.assertGreater(float(kc_par["hinge_concord_splay"][40, 46]), 0.30)
        # Crack-tip cone ahead of fault tip at (64, 40) fires strongly
        self.assertGreater(float(kc_orth["tip_cone"][70, 40]), 0.40)

        # Two-component stepover relay test + empty visible mask edge case
        vis2 = vis.copy()
        vis2[25:70, 50] = True
        kc_relay = F.compute_kslb_kinematics(vis2, pc2_par, ps2_par, pcoh)
        self.assertGreater(float(kc_relay["relay_bridge"][45, 45]), 0.15)

        kc_empty = F.compute_kslb_kinematics(np.zeros((24, 24), dtype=bool), pc2_par[:24, :24], ps2_par[:24, :24], pcoh[:24, :24])
        self.assertEqual(float(kc_empty["m_kin"].max()), 0.0)
        self.assertTrue(np.isinf(kc_empty["d1"]).all())

    def test_noisyor_posterior_recovers_blind_filament_when_mkin_is_zero(self):
        valid = np.ones((10, 10), dtype=bool)
        p_fil = np.full((10, 10), 0.90, dtype=np.float32)
        r_fil = np.full((10, 10), 0.85, dtype=np.float32)
        c_multi = np.full((10, 10), 0.80, dtype=np.float32)
        m_kin_zero = np.zeros((10, 10), dtype=np.float32)

        s_blind = R.noisyor_discovery_surface(p_fil, r_fil, m_kin_zero, c_multi, valid)
        self.assertGreater(float(s_blind[5, 5]), 0.35)

        # Mediocre desert background stays near zero
        s_bg = R.noisyor_discovery_surface(
            np.full((10, 10), 0.25, np.float32),
            np.full((10, 10), 0.10, np.float32),
            m_kin_zero,
            np.full((10, 10), 0.15, np.float32),
            valid,
        )
        self.assertLess(float(s_bg[5, 5]), 0.03)

    def test_run_lane86c_and_features_have_no_preflight_bypass(self):
        with self.assertRaises(TypeError):
            R.main(skip_literal_preflight=True)  # type: ignore[call-arg]
        with mock.patch("scripts.protocol_preflight.measure", return_value={"universal_overlap_blocker": True}):
            with self.assertRaisesRegex(RuntimeError, "STOP_LITERAL_OVERLAP_UNSATISFIABLE"):
                R.main()
            with self.assertRaisesRegex(RuntimeError, "STOP_LITERAL_OVERLAP_UNSATISFIABLE"):
                F.main()

    def test_audit_h86c_passes_without_mutating_any_prior_cards(self):
        watched = [
            ROOT / "docs/evidence/run-card.json",
            ROOT / "docs/evidence/h86b-gfco-run-card.json",
            ROOT / "docs/evidence/rmrb86-run-card.json",
            ROOT / "evidence/run_card.json",
        ]
        before = {p: p.read_bytes() for p in watched}
        summary = audit_h86c.run()
        self.assertTrue(summary["all_audit_invariants_passed"], summary)
        self.assertEqual(summary["emitted_dots"], 44090)
        self.assertEqual(summary["verdict"], "negative")
        self.assertFalse(summary["approved_for_weekly_slot"])
        for p, raw in before.items():
            self.assertEqual(p.read_bytes(), raw, f"Mutated {p}")

    def test_build_site_is_idempotent_and_preserves_owner_prompt_archive(self):
        rc_check = build_site.main(["--check"])
        self.assertEqual(rc_check, 0)
        html_paths = sorted((ROOT / "docs").glob("*.html"))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in html_paths}
        rc = build_site.main([])
        self.assertEqual(rc, 0)
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in html_paths}
        self.assertEqual(before, after, "scripts/build_site.py must be byte-for-byte deterministic")

        readme = (ROOT / "README.md").read_text()
        owner = (ROOT / "research/OWNER_PROMPT.md").read_text().strip()
        start_tag = "<!-- OWNER_PROMPT_ARCHIVE_START -->"
        end_tag = "<!-- OWNER_PROMPT_ARCHIVE_END -->"
        self.assertIn(start_tag, readme)
        self.assertIn(end_tag, readme)
        archived = readme.split(start_tag, 1)[1].split(end_tag, 1)[0].strip()
        self.assertEqual(archived, owner)
        tif_bytes = (ROOT / "docs/downloads/gems86-h86c-kslb-44090dots-20261023T010446Z-83854555-zeros.tif").stat().st_size
        self.assertIn(f"| {tif_bytes:,} | 85 |", readme)


if __name__ == "__main__":
    unittest.main()
