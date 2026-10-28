"""Synthetic gate integrity checks; these are NOT geological experiments/scores."""
from types import SimpleNamespace
from pathlib import Path
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from scripts import check_h86e_registry as check
from scripts.pa86_chance_overlap import validate_report_binding


@pytest.fixture
def audit(tmp_path):
    fp = np.ones((30, 30), bool)
    g = SimpleNamespace(footprint=fp, shape=fp.shape,
                        crs=rasterio.crs.CRS.from_epsg(32611),
                        transform=from_origin(0, 3000, 100, 100))
    theirs = np.zeros(g.shape, np.float32)
    theirs[2, 2] = 1
    tif = tmp_path / "prior.tif"
    with rasterio.open(tif, "w", driver="GTiff", height=30, width=30, count=1,
                       dtype="float32", crs=g.crs, transform=g.transform) as dst:
        dst.write(theirs, 1)
    index = dict(rasters=[dict(sha256=check.sha(tif), repo_first="synthetic",
                              sources=["synthetic:prior"], cache_file=str(tif))],
                 complete_accessible_scan=True, errors=[])
    mine = np.zeros(g.shape, np.float32)
    mine[25, 25] = 1
    source = tmp_path / "candidate.npy"
    np.save(source, mine)
    report = check.evaluate_candidate(mine, index, [], g)
    report.update(mode="final_dots", candidate_source_sha256=check.sha(source))
    return g, index, mine, source, report


def test_complete_distinct_registry_is_only_scoped_clearance(audit):
    g, index, _, source, report = audit
    assert report["surface_gate_pass"] and report["final_dots_gate_pass"]
    assert report["literal_gate_pass"]
    assert report["registry_rasters_measured"] == 1
    assert report["submission_authorized"] is False
    assert validate_report_binding(report, source, g, index, [])["rasters_checked"] == 1


@pytest.mark.parametrize("failure", ["missing", "source_error", "hash_drift", "no_records", "all_bad"])
def test_incomplete_or_invalid_registry_never_passes(audit, failure):
    g, index, mine, _, _ = audit
    missing = []
    if failure == "missing":
        missing = ["missing-sha"]
        index["complete_accessible_scan"] = False
    elif failure == "source_error":
        index["errors"] = ["fetch failed"]
    elif failure == "hash_drift":
        index["rasters"][0]["sha256"] = "0" * 64
    elif failure == "no_records":
        index["rasters"] = []
    elif failure == "all_bad":
        Path(index["rasters"][0]["cache_file"]).unlink()
    report = check.evaluate_candidate(mine, index, missing, g)
    assert not report["registry_complete_for_index"]
    assert not report["surface_gate_pass"]
    assert not report["final_dots_gate_pass"]
    assert not report["literal_gate_pass"]
    assert report["registry_rasters_expected"] == len(index["rasters"]) + len(missing)


@pytest.mark.parametrize("value", [0, 1])
def test_empty_and_constant_candidates_cannot_pass(audit, value):
    g, index, mine, _, _ = audit
    mine[:] = value
    report = check.evaluate_candidate(mine, index, [], g)
    assert not report["surface_gate_pass"]
    assert not report["final_dots_gate_pass"]


def test_pixel_identical_candidate_fails_without_a_candidate_file_hash(audit):
    g, index, mine, _, _ = audit
    mine[:] = 0
    mine[2, 2] = 1
    report = check.evaluate_candidate(mine, index, [], g)
    assert not report["final_dots_gate_pass"]
    assert report["shared_summary"]["pixel_unique_among_checked"] is False


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf, -0.01, 1.01, 1 + 1e-9])
@pytest.mark.parametrize("surface", [False, True])
def test_candidate_invalid_values_rejected_before_cast_or_threshold(audit, bad, surface):
    g, _, mine, source, _ = audit
    raw = mine.astype(np.float64)
    raw[2, 2] = bad
    np.save(source, raw)
    with pytest.raises(ValueError, match="finite in"):
        check.load_candidate(source, g.footprint, surface=surface)


def test_candidate_outside_support_not_silently_masked(audit):
    g, _, mine, source, _ = audit
    g.footprint[25, 25] = False
    np.save(source, mine)
    with pytest.raises(ValueError, match="outside footprint"):
        check.load_candidate(source, g.footprint, surface=True)


def test_soft_surface_cannot_be_implicitly_converted_to_dots(audit):
    g, _, mine, source, _ = audit
    mine[25, 25] = 0.3
    np.save(source, mine)
    with pytest.raises(ValueError, match="already be binary"):
        check.load_candidate(source, g.footprint, surface=False)
    assert check.load_candidate(source, g.footprint, surface=True)[25, 25] == mine[25, 25]


@pytest.mark.parametrize("failure", ["legacy", "surface", "incomplete", "error", "index", "source",
                                     "decoded", "rows", "count", "prior_changed", "fake_self"])
def test_chance_audit_rejects_unbound_or_stale_evidence(audit, failure):
    g, index, mine, source, report = audit
    if failure == "legacy":
        report.pop("schema")
    elif failure == "surface":
        report["mode"] = "surface"
    elif failure == "incomplete":
        report["registry_complete_for_index"] = False
    elif failure == "error":
        report["errors"] = ["unreadable raster"]
    elif failure == "index":
        report["registry_index_sha256"] = "0" * 64
    elif failure == "source":
        mine[20, 20] = 1
        np.save(source, mine)
    elif failure == "decoded":
        report["shared_summary"]["candidate_decoded_sha256"] = "0" * 64
    elif failure == "rows":
        report["comparison_rows"] = []
    elif failure == "count":
        report["registry_rasters_measured"] = 655
    elif failure == "prior_changed":
        Path(index["rasters"][0]["cache_file"]).write_bytes(b"changed")
    exclude = "synthetic:prior" if failure == "fake_self" else None
    with pytest.raises(ValueError):
        validate_report_binding(report, source, g, index, [], exclude=exclude)


def test_missing_index_entries_reject_chance_audit(audit):
    g, index, _, source, report = audit
    with pytest.raises(ValueError, match="Incomplete registry"):
        validate_report_binding(report, source, g, index, ["missing"])


def test_self_exclusion_needs_exact_pixels_and_another_prior(audit):
    g, index, _, source, report = audit
    arr = np.load(source)
    original = Path(index["rasters"][0]["cache_file"])
    second = original.with_name("self.tif")
    with rasterio.open(second, "w", driver="GTiff", height=30, width=30, count=1,
                       dtype="float32", crs=g.crs, transform=g.transform) as dst:
        dst.write(arr, 1)
    index["rasters"].append(dict(sha256=check.sha(second), repo_first="synthetic",
                                 sources=["synthetic:self"], cache_file=str(second)))
    report = check.evaluate_candidate(arr, index, [], g)
    report.update(mode="final_dots", candidate_source_sha256=check.sha(source))
    phase = validate_report_binding(report, source, g, index, [], exclude="synthetic:self")
    assert phase["rasters_checked"] == 1
    assert phase["literal_reading"]["rho_firings"] == 0


def test_cli_failure_writes_negative_report_and_nonzero_exit(audit, tmp_path, monkeypatch):
    g, index, _, source, _ = audit
    monkeypatch.setattr(check.grid, "load_grid", lambda _: g)
    monkeypatch.setattr(check, "build_index", lambda: (index, ["absent"]))
    out = tmp_path / "report.json"
    assert check.main([str(source), str(out), "--surface"]) == 1
    import json
    report = json.loads(out.read_text())
    assert report["surface_gate_pass"] is False
    assert "final_dots_gate_pass" not in report
    assert report["candidate_source_sha256"] == check.sha(source)


def test_builder_stops_before_placement_on_failed_surface(audit, tmp_path, monkeypatch):
    from scripts import build_h86e_final as builder
    g, _, mine, _, _ = audit
    g.catalogue = np.zeros(g.shape, bool)
    (tmp_path / "data/work").mkdir(parents=True)
    (tmp_path / "docs/evidence").mkdir(parents=True)
    np.save(tmp_path / "data/work/h86e_features.npy", np.zeros((1, 30, 30)))
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    # Synthetic unit test simulates an already-satisfied literal preflight;
    # production must not bypass it even when this diagnostic is mocked.
    from scripts import protocol_preflight
    monkeypatch.setattr(protocol_preflight, "require_feasible", lambda: {})
    monkeypatch.setattr(builder, "require_like_for_like", lambda: {})
    monkeypatch.setattr(builder.grid, "load_grid", lambda _: g)
    monkeypatch.setattr(builder.P, "sample_training", lambda *a, **kw: (None, np.array([0, 1])))
    monkeypatch.setattr(builder.P, "fit", lambda *a, **kw: None)
    monkeypatch.setattr(builder.P, "predict", lambda *a: mine)
    def failed_check(args):
        Path(args[1]).write_text('{"literal_gate_pass": false}')
        return 1
    monkeypatch.setattr(builder.registry_check, "main", failed_check)
    def forbidden(*args, **kwargs):
        pytest.fail("dot placement must not follow a failed surface gate")
    monkeypatch.setattr(builder.P, "disc_thin", forbidden)
    with pytest.raises(RuntimeError, match="no dot placement"):
        builder.main()
    assert not (tmp_path / "data/work/h86e_final_dots.npy").exists()


def test_writer_stops_before_data_loading_or_serialization(monkeypatch):
    # Import itself must have no IO/writing side effects.
    from scripts import write_h86e_tif as writer
    from scripts import protocol_preflight
    def blocked():
        raise RuntimeError("STOP_LITERAL_OVERLAP_UNSATISFIABLE")
    monkeypatch.setattr(protocol_preflight, "require_feasible", blocked)
    monkeypatch.setattr(writer.grid, "load_grid", lambda _: pytest.fail("read after stop"))
    with pytest.raises(RuntimeError, match="STOP_LITERAL"):
        writer.main()
