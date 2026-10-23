"""Fail-closed audit & submission-gate verifier for Session-3 Lane H86C-KSLB.

Verifies:
  1. `vendor/gems57` byte-for-byte SHA-256 pin integrity (`research/template_pin.json`).
  2. AST zero-leakage check on `scripts/h86c_features.py` (`build_physical_planes` never
     touches `existing_faults.tif`, `labels.tif`, `gdr_qfaults_traces.csv`,
     `derived_sgmc_faults_100m_u8.tif`, or `dist_known_fault_px` as an active read).
  3. Strict JSON validity (no NaN/Infinity) of `docs/evidence/lane86c_results.json`,
     `docs/evidence/h86c-kslb-run-card.json`, and `docs/evidence/h86c_crosslane_uniqueness.json`.
  4. Shared validator (15/15 checks) + `format_report` + single-TIFF `.zip` byte identity
     against `data/bridge/{sample_submission,existing_faults}.tif`.
  5. Protocol gates: 52/52 leakage canaries <= 0.90, <= 3 experiments, positive paired 95% CIs
     across all 3 holdout views vs both `d2.8` and `H33-2-B2`, non-lattice `dot_field`
     uniqueness (`<= 0.70` 3-px overlap, `|rho| <= 0.90` across all 35 `dot_field` rasters),
     AND fail-closed `verdict == "negative"` / `approved_for_weekly_slot == False` under
     the literal saturated-witness rule.

Never mutates any prior run card (`docs/evidence/run-card.json`, `h86b-gfco-run-card.json`,
`rmrb86-run-card.json`, `evidence/run_card.json`).
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import gates as GT  # noqa: E402
from gems57 import validate as V  # noqa: E402

PINS = ROOT / "research" / "template_pin.json"
RESULTS = ROOT / "docs" / "evidence" / "lane86c_results.json"
RUNCARD = ROOT / "docs" / "evidence" / "h86c-kslb-run-card.json"
UNIQ = ROOT / "docs" / "evidence" / "h86c_crosslane_uniqueness.json"
FEATURES_SRC = ROOT / "scripts" / "h86c_features.py"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pin_mismatches() -> list[dict]:
    doc = json.loads(PINS.read_text())
    mismatches = []
    for rel_path, expected_sha in doc["files"].items():
        p = ROOT / rel_path
        if not p.is_file():
            mismatches.append(dict(path=rel_path, error="missing"))
            continue
        got = sha256(p)
        if got != expected_sha:
            mismatches.append(dict(path=rel_path, expected=expected_sha, got=got))
    return mismatches


def _strict_json_load(path: Path) -> dict:
    def _reject_const(val: str):
        raise ValueError(f"Non-finite JSON constant {val!r} in {path}")
    return json.loads(path.read_text(), parse_constant=_reject_const)


def ast_zero_leakage_check(src_path: Path = FEATURES_SRC) -> dict:
    tree = ast.parse(src_path.read_text())
    forbidden_files = {
        "existing_faults.tif",
        "labels.tif",
        "gdr_qfaults_traces.csv",
        "derived_sgmc_faults_100m_u8.tif",
    }
    build_fn = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "build_physical_planes":
            build_fn = node
            break
    if build_fn is None:
        return dict(ok=False, violations=["missing build_physical_planes"])
    violations = []
    for sub in ast.walk(build_fn):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            for bad in forbidden_files:
                if bad in sub.value:
                    violations.append(f"forbidden file string in build_physical_planes: {sub.value}")
        if isinstance(sub, ast.Subscript):
            sl = sub.slice
            if isinstance(sl, ast.Constant) and sl.value == "dist_known_fault_px":
                violations.append("forbidden subscript row['dist_known_fault_px']")
    return dict(ok=(len(violations) == 0), violations=violations)


def run(
    results_path: Path = RESULTS,
    run_card_path: Path = RUNCARD,
    uniq_path: Path = UNIQ,
) -> dict:
    mismatches = pin_mismatches()
    pins_clean = len(mismatches) == 0
    ast_check = ast_zero_leakage_check()

    res = _strict_json_load(results_path)
    card = _strict_json_load(run_card_path)
    uniq = _strict_json_load(uniq_path)

    art = res["submission_artifact"]
    tif_path = ROOT / art["tif_file"]
    zip_path = ROOT / art["zip_file"]
    rec_path = ROOT / art["receipt_file"]

    tif_ok = tif_path.is_file() and sha256(tif_path) == art["tif_sha256"] == card["raster_sha256"]
    zip_ok = False
    if zip_path.is_file() and sha256(zip_path) == art["zip_sha256"]:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            zip_ok = (
                names == [tif_path.name]
                and zf.testzip() is None
                and zf.read(tif_path.name) == tif_path.read_bytes()
            )
    rec_ok = rec_path.is_file() and _strict_json_load(rec_path)["sha256"] == card["raster_sha256"]

    bridge_dir = ROOT / "data" / "bridge"
    with rasterio.open(bridge_dir / "sample_submission.tif") as sds, rasterio.open(bridge_dir / "existing_faults.tif") as cds:
        fp = np.isfinite(sds.read(1))
        cat = cds.read(1) > 0

    val = V.validate(tif_path, footprint=fp, catalogue=cat)
    fmt = GT.format_report(tif_path, bridge_dir / "sample_submission.tif", footprint=fp)
    format_valid = bool(tif_ok and zip_ok and rec_ok and val["all_checks_passed"] and fmt["ok"] and len(card["note"]) <= 140)

    can = res["leakage_canaries"]
    leakage_pass = bool(
        can["total_checked"] == 52
        and (not can["any_leakage_flag"])
        and can["max_discriminative_auc"] <= 0.90
        and ast_check["ok"]
    )
    budget_pass = bool(res["experiments_run"] <= 3 and card["experiments_run"] <= 3)

    hc = res["holdout_buffered_whole_components"]
    ha = res["holdout_segment_all"]
    hd = res["holdout_segment_detached"]
    beats_all_3 = bool(
        hc["paired_differences"]["d28_incumbent"]["ci95"][0] > 0.0
        and hc["paired_differences"]["h33_b2_foldfair"]["ci95"][0] > 0.0
        and ha["paired_differences"]["d28_incumbent"]["ci95"][0] > 0.0
        and ha["paired_differences"]["h33_b2_foldfair"]["ci95"][0] > 0.0
        and hd["paired_differences"]["d28_incumbent"]["ci95"][0] > 0.0
        and hd["paired_differences"]["h33_b2_foldfair"]["ci95"][0] > 0.0
    )

    nonlattice_unique = bool(
        uniq["pre_placement_surface_worst_abs_spearman"] <= 0.90
        and uniq["final_dots_worst_all_abs_spearman"] <= 0.90
        and uniq["final_dots_worst_nonlattice_dot_overlap_3px"] <= 0.70
        and card["correlation_overlap_vs_registry"]["nonlattice_dot_field_duplicates"] == 0
    )
    literal_unique = bool(uniq["literal_protocol_unique"])

    fail_closed_consistent = bool(
        (not literal_unique)
        and card["verdict"] == "negative"
        and res["verdict"] == "negative"
        and card["submission_ready"] is False
        and card["approved_for_weekly_slot"] is False
    )

    all_audit_invariants = bool(
        pins_clean
        and format_valid
        and leakage_pass
        and budget_pass
        and beats_all_3
        and nonlattice_unique
        and fail_closed_consistent
    )

    return dict(
        lane="H86C-KSLB",
        pins_clean=pins_clean,
        pin_mismatches=mismatches,
        ast_zero_leakage=ast_check,
        format_valid=format_valid,
        leakage_canary_pass=leakage_pass,
        budget_within_3=budget_pass,
        beats_incumbents_all_3_holdouts_95ci=beats_all_3,
        nonlattice_dot_field_unique=nonlattice_unique,
        literal_protocol_unique=literal_unique,
        fail_closed_governance_consistent=fail_closed_consistent,
        all_audit_invariants_passed=all_audit_invariants,
        tif_sha256=val["sha256"],
        emitted_dots=val["emitted_positive_pixels"],
        verdict=card["verdict"],
        approved_for_weekly_slot=card["approved_for_weekly_slot"],
    )


if __name__ == "__main__":
    summary = run()
    print(json.dumps(summary, indent=2, allow_nan=False))
    if not summary["all_audit_invariants_passed"]:
        raise SystemExit(1)
