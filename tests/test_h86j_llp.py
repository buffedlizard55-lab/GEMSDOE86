"""H86J-LLP lane guards: LLP math, coverage, automated gate and run-card binding."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "src", ROOT / "vendor"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

CARD = ROOT / "docs/evidence/h86j-llp-run-card.json"
GATE = ROOT / "docs/evidence/submission-gate.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_llp_gradient_matches_finite_differences():
    from scipy import sparse
    from gems86_llp.llp import LLPModel

    rng = np.random.default_rng(0)
    n, F, R = 4000, 4, 10
    X = rng.random((n, F)).astype(np.float32)
    C = sparse.random(R, n, density=0.05, random_state=1, format="csr")
    C.data = np.clip(C.data, 0, 1)
    P = sparse.random(R, n, density=0.01, random_state=2, format="csr")
    P.data[:] = 1.0
    mass = np.asarray(P.sum(1)).ravel() * 20
    s = rng.uniform(0.02, 0.3, R)
    m = LLPModel(X, C, P, mass, s, 20.0, list("abcd"))
    w = np.r_[np.log(0.02), rng.normal(0, 0.5, F)]
    for rows in (np.arange(R), np.arange(1, R)):
        _, g = m.loss_grad(w, rows, 0.7)
        num = np.array([(m.loss_grad(w + e, rows, 0.7)[0] - m.loss_grad(w - e, rows, 0.7)[0]) / 2e-6
                        for e in np.eye(len(w)) * 1e-6])
        assert np.max(np.abs(g - num) / (np.abs(num) + 1e-9)) < 1e-5


def test_predicted_dti_is_a_valid_ratio():
    from scipy import sparse
    from gems86_llp.llp import LLPModel

    rng = np.random.default_rng(3)
    X = rng.random((2000, 3)).astype(np.float32)
    C = sparse.random(6, 2000, density=0.1, random_state=4, format="csr")
    C.data = np.clip(C.data, 0, 1)
    P = sparse.random(6, 2000, density=0.02, random_state=5, format="csr")
    P.data[:] = 1.0
    m = LLPModel(X, C, P, np.asarray(P.sum(1)).ravel() * 10, np.full(6, 0.1), 10.0, list("abc"))
    pred, parts = m.predict(np.r_[np.log(0.01), 0.3, -0.2, 0.1])
    assert np.all((pred >= 0) & (pred <= 1))
    assert np.all(parts["T"] <= parts["G"] + 1e-9)


def test_coverage_equals_shared_max_cover_credit():
    from gems57.metric import max_cover
    from gems86_llp.fleet import coverage

    rng = np.random.default_rng(11)
    p = (rng.random((40, 50)) > 0.97).astype(np.float32)
    truth = rng.random((40, 50)) > 0.9
    credit, _, _ = max_cover(p, truth)
    cov = coverage(p)
    assert np.allclose(cov[truth], credit, atol=1e-6)


def test_preregistration_frozen_before_run_and_amendments_recorded():
    doc = json.loads((ROOT / "research/H86J_LLP_PREREGISTRATION.json").read_text())
    md = (ROOT / "research/H86J_LLP_PREREGISTRATION.md").read_text()
    assert len(doc["hypotheses_ranked"]) == 5
    assert [a["id"] for a in doc["amendments"]] == ["A1", "A2", "A3", "A4"]
    for tag in ("**A1", "**A2", "**A3", "**A4", "**A5"):
        assert tag in md
    card = json.loads(CARD.read_text())
    assert doc["frozen_utc"] < card["generated_utc"]


def test_run_card_has_every_protocol_field_and_is_negative():
    card = json.loads(CARD.read_text())
    for key in ("hypothesis", "mechanism", "named_non_fault_process", "holdout_dti", "uniqueness",
                "raster_sha256", "validator_output", "submission_name", "submission_note", "verdict"):
        assert card.get(key), key
    assert len(card["submission_name"]) <= 140 and len(card["submission_note"]) <= 140
    h = card["holdout_dti"]
    assert h["evidence_class"] == "HOLDOUT-DTI" and h["evaluator_version"] == "gems57-pooled-hide-v2"
    assert h["withheld_positive_pixels"] == 11321 and len(h["candidate"]["ci95"]) == 2
    assert card["verdict"] == "negative" and card["decision"] == "DO NOT SUBMIT"
    assert card["safe_to_submit"] is False and card["approved_for_weekly_slot"] is False
    assert card["submission_slots_used"] == 0
    v = card["validator_output"]
    assert v["all_checks_passed"] and v["n_nan"] == 0 and v["min"] >= 0 and v["max"] <= 1
    assert v["crs"] == "EPSG:32611" and v["shape"] == [3730, 3292]


def test_published_tif_zip_and_gate_are_bound_and_say_do_not_submit():
    card = json.loads(CARD.read_text())
    gate = json.loads(GATE.read_text())
    tif = ROOT / card["raster_path"]
    assert tif.is_file() and _sha(tif) == card["raster_sha256"] == gate["sha256"]
    assert gate["verdict"] == "DO NOT SUBMIT" and gate["ok_to_submit"] is False
    assert set(gate["failed_checks"]) == {"U3_pa86_chance_overlap", "S3_holdout_beats_current_best"}
    assert gate["checks"]["F2_shared_validator"]["passed"]
    import zipfile
    with zipfile.ZipFile(ROOT / card["zip_path"]) as z:
        assert z.namelist() == [tif.name] and z.read(tif.name) == tif.read_bytes()


def test_gate_fails_closed_on_tampered_sha_and_missing_evidence():
    from scripts.submission_gate import evaluate

    card = json.loads(CARD.read_text())
    bad = dict(card, raster_sha256="0" * 64)
    out = evaluate(bad)
    assert out["verdict"] == "DO NOT SUBMIT" and "F1_sha256_bound" in out["failed_checks"]
    missing = dict(card)
    missing.pop("uniqueness")
    out = evaluate(missing)
    assert {"U1_registry_final_dots_bound_complete_rho", "U2_registry_surface_rho",
            "U3_pa86_chance_overlap"} <= set(out["failed_checks"])


def test_site_and_readme_lead_with_the_gate_verdict():
    gate = json.loads(GATE.read_text())
    html = (ROOT / "docs/index.html").read_text()
    main = html.split('<main id="main">', 1)[1]
    assert main.lstrip().startswith('<section class="gate no" id="gate">')
    assert '<p class="verdict">DO NOT SUBMIT</p>' in main[:400]
    assert gate["sha256"] in html
    exe = (ROOT / "docs/executive-summary.html").read_text()
    assert 'id="exact-steps"' in exe and "Predicted values must be in range [0, 1]" in exe
    readme = (ROOT / "README.md").read_text()
    head = readme.split("<!-- GATE:END -->", 1)[0]
    assert "## Is the newest TIFF OK to submit? **DO NOT SUBMIT**" in head
    assert gate["submission_name"] in head


@pytest.mark.skipif(not (ROOT / "data/registry_ext").is_dir(), reason="registry not restored")
def test_offgrid_inventory_rows_get_pixel_grid_derivatives():
    from scripts.check_h86e_registry import build_index

    index, missing = build_index()
    assert not missing
    derived = [r for r in index["rasters"] if r.get("derived_from_sha256")]
    assert len(derived) == 4
    assert all("PA-86-03" in r["sources"][0] for r in derived)
