"""H86G-EDTI lane guards: preregistration, emission invariants, shipped card."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_preregistration_amendments_and_hypotheses():
    doc = json.loads((ROOT / "research/H86G_EDTI_PREREGISTRATION.json").read_text())
    assert 3 <= len(doc["arms"]) <= 5
    assert doc["budget"]["max_experiments"] == 3 and doc["budget"]["max_hours"] == 2
    for key in ("amendment_A1", "amendment_A2", "amendment_A3", "amendment_A4"):
        assert key in doc
    md = (ROOT / "research/H86G_EDTI_PREREGISTRATION.md").read_text()
    assert "Amendment A4" in md and "post-hoc" in md


def test_spacing_greedy_enforces_min_spacing_on_synthetic():
    from gems86_edti.model import spacing_greedy_ranking

    rng = np.random.default_rng(7)
    ek = rng.random((60, 60), dtype=np.float32)
    allowed = np.ones((60, 60), bool)
    ranked = spacing_greedy_ranking(ek, allowed, min_spacing_px=2.8, candidate_cap=5000)
    ys, xs = np.nonzero(ranked > 0)
    assert len(ys) > 100
    # nested ranking: ranks are exactly 1..n
    assert sorted(ranked[ys, xs].tolist()) == list(range(1, len(ys) + 1))
    pts = np.column_stack([ys, xs]).astype(float)
    for i in range(0, len(pts), 37):  # sample pairwise checks (full check is O(n^2))
        d = np.hypot(*(pts - pts[i]) .T)
        d[i] = np.inf
        assert d.min() >= 2.8 - 1e-9


def test_shipped_candidate_card_receipt_consistency():
    card = json.loads((ROOT / "docs/evidence/h86g-edti-run-card.json").read_text())
    assert card["verdict"] == "promote"
    assert card["submission_slots_used"] == 0
    assert card["approved_for_weekly_slot"] is False
    assert card["safe_to_submit"] is False  # organizer acceptance unproven
    assert all(card["gates"].values())
    assert len(card["note"]) == card["note_chars"] <= 140
    tif = ROOT / card["submission_file"]
    assert tif.is_file()
    digest = hashlib.sha256(tif.read_bytes()).hexdigest()
    assert digest == card["raster_sha256"]
    receipt = json.loads(tif.with_suffix(".json").read_text())
    assert receipt["sha256"] == digest
    assert receipt["gate_verdict"] == "promote"
    assert card["sgmc_proxy"]["candidate"]["dti"] > card["sgmc_proxy"]["H33_as_is_dti"]
    assert card["sgmc_proxy"]["paired_delta_vs_H33_as_is"]["ci95"][0] > 0
    assert card["uniqueness"]["gate_pass"] is True
    assert card["uniqueness"]["max_spearman"] <= 0.90
    assert card["uniqueness"]["max_forward_3px_overlap_dot_fields"] <= 0.70


def test_shipped_raster_is_binary_grid_locked():
    rasterio = pytest.importorskip("rasterio")
    card = json.loads((ROOT / "docs/evidence/h86g-edti-run-card.json").read_text())
    with rasterio.open(ROOT / card["submission_file"]) as ds:
        a = ds.read(1)
        assert ds.count == 1 and str(ds.crs) == "EPSG:32611" and ds.shape == (3730, 3292)
    assert np.isfinite(a).all()
    assert set(np.unique(a).tolist()) == {0.0, 1.0}
    assert int((a > 0).sum()) == card["chosen_budget"]
