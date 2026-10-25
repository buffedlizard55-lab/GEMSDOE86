"""Unit and artifact-integrity tests for H86I-SACD (Session 95a42d60)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gems86.io import BANDS, BAND_PHYSICS_VERIFIED  # noqa: E402
from gems86_sacd.features import (  # noqa: E402
    DIRECTOR_NAMES,
    DYNAMIC_FEATURE_NAMES,
    compute_sacd_dynamic_fields,
)
from gems86_sacd.submodular import submodular_kernel_allocate  # noqa: E402


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_submodular_kernel_allocate_respects_budget_and_allowed_mask() -> None:
    rng = np.random.default_rng(95)
    prob = rng.uniform(0.0, 0.2, size=(64, 64)).astype(np.float32)
    # Plant a sharp N-S ridge at col 32
    prob[10:54, 32] = 0.95
    allowed = np.ones((64, 64), dtype=bool)
    allowed[:6, :] = False
    allowed[:, :6] = False

    dots = submodular_kernel_allocate(prob, allowed, budget=12, gamma=1.30)
    assert dots.shape == (64, 64)
    assert dots.dtype == np.float32
    assert int((dots > 0).sum()) == 12
    assert float(dots.min()) == 0.0
    assert float(dots.max()) == 1.0
    assert int((dots[~allowed] > 0).sum()) == 0
    # Majority of allocated dots must concentrate along the high-posterior ridge
    assert int((dots[10:54, 31:34] > 0).sum()) >= 8


def test_spin2_dynamic_fields_zero_on_empty_and_pi_periodic() -> None:
    h, w = 80, 80
    fp = np.ones((h, w), dtype=bool)
    n_fp = int(fp.sum())
    directors = np.zeros((len(DIRECTOR_NAMES), n_fp), dtype=np.float16)

    empty_vis = np.zeros((h, w), dtype=bool)
    d0 = compute_sacd_dynamic_fields(empty_vis, fp, directors)
    assert d0.shape == (len(DYNAMIC_FEATURE_NAMES), n_fp)
    assert np.all(d0 == 0)

    vis = np.zeros((h, w), dtype=bool)
    vis[20:42, 40] = True  # N-S fault segment -> outward tip along +/- row_south (ux=0, ur=+/-1 -> c2=-1, s2=0)
    # Set scarp director along N-S (theta = pi/2 -> c2 = -1, s2 = 0) vs E-W (theta = 0 -> c2 = +1, s2 = 0)
    directors_aligned = directors.copy()
    directors_aligned[0, :] = -1.0
    d_align = compute_sacd_dynamic_fields(vis, fp, directors_aligned)

    directors_orth = directors.copy()
    directors_orth[0, :] = +1.0
    d_orth = compute_sacd_dynamic_fields(vis, fp, directors_orth)

    assert np.isfinite(d_align).all()
    assert np.isfinite(d_orth).all()
    # Ahead of southern tip (rows 44..52, col 40), aligned scarp must exceed orthogonal scarp
    ahead_idx = np.ravel_multi_index(
        np.meshgrid(np.arange(44, 52), np.array([40]), indexing="ij"), (h, w)
    ).ravel()
    assert float(d_align[4, ahead_idx].mean()) > float(d_orth[4, ahead_idx].mean())


def test_h86i_preregistration_and_run_card_integrity() -> None:
    hyp = json.loads((ROOT / "registry/h86i_hypotheses.json").read_text(encoding="utf-8"))
    prereg = json.loads((ROOT / "research/H86I_SACD_PREREGISTRATION.json").read_text(encoding="utf-8"))
    card = json.loads((ROOT / "docs/evidence/h86i-sacd-run-card.json").read_text(encoding="utf-8"))

    assert hyp["declared_before_implementation"] is True
    assert len(hyp["hypotheses"]) == 4
    assert hyp["hypotheses"][0]["id"] == "H86I-SACD"
    assert "NOT_VIABLE_YET" in hyp["hypotheses"][3]["external_data_status"]
    assert BANDS[6] == "tc" and "Radiometric Total Count" in BAND_PHYSICS_VERIFIED[6]

    assert card["preregistration"]["preregistration_sha256"] == _sha256(
        ROOT / "research/H86I_SACD_PREREGISTRATION.json"
    )
    assert card["preregistration"]["hypothesis_queue_sha256"] == _sha256(
        ROOT / "registry/h86i_hypotheses.json"
    )
    assert len(prereg["preregistered_experiments"]) == 3
    assert card["experiments_run"] == 3
    assert card["verdict"] == "negative"
    assert card["decision"] == "DO NOT SUBMIT"
    assert card["safe_to_submit"] is False
    assert card["submission_ready"] is False
    assert card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    assert 1 <= card["note_chars"] <= 140
    assert card["note_chars"] == len(card["note"])

    tif = ROOT / card["submission_file"]
    assert tif.is_file()
    assert _sha256(tif) == card["raster_sha256"]
    assert card["validator_output"]["all_checks_passed"] is True
    assert card["validator_output"]["values_in_0_1"] is True
    assert card["validator_output"]["no_nan_inside_footprint"] is True
    assert card["validator_output"]["crs_shape_transform_match"] is True
    assert card["holdout_dti"]["leakage_canary_summary"]["any_leakage_flag"] is False
    assert card["holdout_dti"]["leakage_canary_summary"]["max_discriminative_auc"] <= 0.90

    reg = card["correlation_overlap_vs_registry"]
    surf_rep = json.loads((ROOT / reg["surface_preplacement"]["report"]).read_text(encoding="utf-8"))
    dots_rep = json.loads((ROOT / reg["final_dots"]["report"]).read_text(encoding="utf-8"))
    assert surf_rep["schema"] == "gems86.registry-candidate.v2"
    assert dots_rep["schema"] == "gems86.registry-candidate.v2"
    assert surf_rep["surface_gate_pass"] is False
    assert dots_rep["final_dots_gate_pass"] is False
    assert reg["pa86_02"]["gate_pass"] is False
