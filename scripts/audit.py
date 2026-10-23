"""Automated preflight & submission-artifact audit. Missing or invalid evidence is never a PASS."""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_pins(root: Path = ROOT) -> bool:
    pin_path = root / "research" / "template_pin.json"
    if not pin_path.is_file():
        return False
    pin = json.loads(pin_path.read_text())
    return all(
        (root / p).is_file() and sha256_file(root / p) == h
        for p, h in pin["files"].items()
    )


def _missing_evidence_card(checks: dict, details: dict) -> dict:
    return {
        "hypothesis": "No validated lane run card present",
        "mechanism": None,
        "non_fault_mimic": None,
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "status": "NOT_RUN",
            "evaluator_version": "gems57-pooled-hide-v2",
            "withheld_positives": None,
            "value": None,
            "ci95": None,
        },
        "correlation_overlap_vs_registry": {
            "status": "NOT_RUN",
            "surface": None,
            "final_dots": None,
            "complete": False,
        },
        "raster_sha256": None,
        "validator": {
            "status": "NOT_RUN_NO_CANDIDATE",
            "no_nan_inside_footprint": None,
            "values_in_0_1": None,
            "crs_shape_transform_match": None,
        },
        "submission_name": None,
        "note": "No candidate generated: missing docs/evidence/run-card.json.",
        "verdict": "negative",
        "submission_ready": False,
        "experiments_run": 0,
        "preflight_checks": checks,
        "input_grid": details,
    }


def run(root: Path = ROOT, write_audit_receipt: bool = True) -> dict:
    import numpy as np
    import rasterio
    from gems57 import gates, grid

    root = Path(root)
    checks: dict[str, bool] = {
        "shared_template_hashes_match": check_pins(root if (root / "research/template_pin.json").is_file() else ROOT),
    }
    details: dict = {}

    sample = root / "data" / "sample_submission.tif"
    faults = root / "data" / "existing_faults.tif"
    if sample.is_file() and faults.is_file():
        checks["sample_mirror_sha_matches"] = sha256_file(sample) == grid.SHA256_SAMPLE_SUBMISSION
        checks["fault_mirror_sha_matches"] = sha256_file(faults) == grid.SHA256_EXISTING_FAULTS
        with rasterio.open(sample) as s, rasterio.open(faults) as f:
            foot = np.isfinite(s.read(1)) & (s.read_masks(1) > 0)
            checks["input_grids_match"] = (
                s.count == f.count == 1
                and s.shape == f.shape == grid.SHAPE
                and s.crs == f.crs == rasterio.crs.CRS.from_epsg(grid.EPSG)
                and s.transform == f.transform == grid.TRANSFORM
            )
            details = {
                "shape": list(s.shape),
                "crs": str(s.crs),
                "transform": list(s.transform)[:6],
                "footprint_pixels": int(foot.sum()),
                "organizer_authenticated": False,
            }

    run_card_path = root / "docs" / "evidence" / "run-card.json"
    if not run_card_path.is_file():
        return _missing_evidence_card(checks, details)

    card = json.loads(run_card_path.read_text())
    sub = card.get("submission", {})
    tif_rel = sub.get("tif_path")
    zip_rel = sub.get("zip_path")
    tif_path = root / tif_rel if tif_rel else Path("/nonexistent")
    zip_path = root / zip_rel if zip_rel else Path("/nonexistent")

    checks["tif_exists"] = tif_path.is_file()
    checks["zip_exists"] = zip_path.is_file()
    if checks["tif_exists"]:
        checks["tif_sha256_matches_card"] = sha256_file(tif_path) == sub.get("raster_sha256")
        with rasterio.open(tif_path) as ds:
            arr = ds.read(1)
            finite = np.isfinite(arr)
            checks["single_band_float32"] = (ds.count == 1 and ds.dtypes[0] == "float32")
            checks["crs_epsg_32611"] = (ds.crs is not None and ds.crs.to_epsg() == grid.EPSG)
            checks["shape_3730x3292"] = (ds.shape == grid.SHAPE)
            checks["transform_matches_pinned"] = (tuple(ds.transform)[:6] == tuple(grid.TRANSFORM)[:6])
            checks["nodata_is_none"] = (ds.nodata is None)
            checks["all_pixels_finite"] = bool(finite.all())
            checks["strictly_in_0_1"] = bool(finite.all() and float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0)
            checks["emitted_dots_match_card"] = (int((arr > 0).sum()) == int(sub.get("emitted_dots", -1)))
            if sample.is_file():
                fmt = gates.format_report(tif_path, sample)
                checks["shared_format_report_ok"] = bool(fmt["ok"])
            if faults.is_file():
                with rasterio.open(faults) as fds:
                    cat = np.nan_to_num(fds.read(1), nan=0.0) > 0
                checks["zero_catalogue_overlap"] = (int((arr[cat] > 0).sum()) == 0)
    else:
        checks["tif_sha256_matches_card"] = False
        checks["strictly_in_0_1"] = False

    if checks["zip_exists"] and checks["tif_exists"]:
        checks["zip_sha256_matches_card"] = sha256_file(zip_path) == sub.get("zip_sha256")
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            checks["zip_contains_single_matching_tif"] = (
                names == [tif_path.name]
                and hashlib.sha256(zf.read(tif_path.name)).hexdigest() == sub.get("raster_sha256")
            )
    else:
        checks["zip_sha256_matches_card"] = False
        checks["zip_contains_single_matching_tif"] = False

    note = sub.get("submission_note", "")
    checks["note_le_140_chars"] = (0 < len(note) <= 140)

    lc = card.get("leakage_canary", {})
    checks["leakage_canary_pass"] = (
        bool(lc.get("passed"))
        and float(lc.get("max_single_feature_disc_auc", 1.0)) <= 0.90
        and lc.get("dist_known_fault_px_read") is False
    )

    uq = card.get("uniqueness_vs_registry", {})
    checks["uniqueness_gate_pass"] = (
        bool(uq.get("passed"))
        and int(uq.get("registry_rasters_checked", 0)) >= 38
        and float(uq.get("pre_placement_surface_max_abs_spearman_rho", 1.0)) <= 0.90
        and float(uq.get("final_dots_max_abs_spearman_rho", 1.0)) <= 0.90
        and float(uq.get("final_dots_max_3px_overlap_discriminating", 1.0)) <= 0.70
    )

    ho = card.get("holdout", {})
    checks["holdout_gate_pass"] = (
        ho.get("evidence_class") == "HOLDOUT-DTI"
        and ho.get("evaluator_version") == "gems57-pooled-hide-v2"
        and float(ho.get("paired_delta_vs_D28_all", {}).get("ci95", [-1, -1])[0]) > 0.0
        and float(ho.get("paired_delta_vs_H33_2_B2_foldfair_all", {}).get("ci95", [-1, -1])[0]) > 0.0
        and float(ho.get("paired_delta_vs_D28_detached", {}).get("ci95", [-1, -1])[0]) > 0.0
        and float(ho.get("paired_delta_vs_H33_2_B2_foldfair_detached", {}).get("ci95", [-1, -1])[0]) > 0.0
        and float(ho.get("buffered_component_300m_mode", {}).get("dti", 0.0)) > 0.10564
    )

    idx_html = root / "docs" / "index.html"
    exec_html = root / "docs" / "executive-summary.html"
    if idx_html.is_file() and exec_html.is_file() and checks["tif_exists"]:
        t_idx = idx_html.read_text()
        t_exec = exec_html.read_text()
        checks["docs_pages_synced_to_artifact"] = (
            tif_path.name in t_idx
            and tif_path.name in t_exec
            and sub["raster_sha256"] in t_idx
            and sub["raster_sha256"] in t_exec
            and note in t_idx
            and note in t_exec
        )

    all_ok = all(checks.values())
    report = {
        "ok": all_ok,
        "verdict": card.get("verdict") if all_ok else "negative",
        "submission_ready": bool(all_ok and card.get("verdict") == "promote" and card.get("safe_to_submit") is True),
        "raster_sha256": sub.get("raster_sha256"),
        "submission_name": sub.get("submission_name"),
        "note": note,
        "checks": checks,
        "input_grid": details,
    }
    if write_audit_receipt and (root / "docs" / "evidence").is_dir():
        (root / "docs" / "evidence" / "audit_report.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )
    return report


if __name__ == "__main__":
    rep = run()
    print(json.dumps(rep, indent=2))
    if not rep["ok"]:
        raise SystemExit(1)
