#!/usr/bin/env python3
"""Build the novel R0 PRUNE <=3.75 px rung with a fixed-count H19-5 refill.

The exact parent gate, existing FIFO-BFS H19-5 ranking recipe, serializer, and
shared format validator are reused. Inputs are limited to files pinned by
registry/data_manifest.json plus the recipe-pinned d2.8 base in
scripts/run_prune_ladder.py. No truth raster or competition endpoint is read.
The output TIFFs are ignored/local-only until data-use terms are cleared.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57 import metric
from gems57.grid import load_grid
from gems57.holdout import buffered_component_draw
from gems57.gates import format_report
from gems57.validate import validate
from run_prune_ladder import (BASE_FILE, BASE_SHA_MEASURED, BRIDGE, PARENT_FILE,
                              PARENT_ID, PARENT_SHA, proxy_dti, read,
                              rebuild_parent, sha256, write_with_profile)
from scripts.build_r0_prune import (PATHS as PRUNE_PATHS, build_prune_refill,
                                    leakage_canaries, profile_from_catalogue,
                                    serialize, validate_raster)

SESSION_DATE = "20261023"
AXIS = "PRUNE"
PARENT_LABEL = "h33-h33-2-b2"
VALUE = "3.75px"
BUFFER_PX = 3.75
PREDICTED_DELTA = -0.002
PREDICTED_BAND = [-0.010, 0.006]
NAN_POLICY_CHECKS = {"no_nan_anywhere", "outside_footprint_zero"}
H19_PATH = ROOT / "data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif"
SGMC_PATH = ROOT / "data/external/derived_sgmc_faults_100m_u8.tif"
MANIFEST_PATH = ROOT / "registry/data_manifest.json"
LEDGER_PATH = ROOT / "ledger/submissions.csv"


def digest(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def verify_manifest_inputs() -> dict:
    manifest = {e["id"]: e for e in json.loads(MANIFEST_PATH.read_text())["files"]}
    paths = {
        "sample_submission": BRIDGE / "sample_submission.tif",
        "existing_faults": BRIDGE / "existing_faults.tif",
        "scored_h33_2_b2_zeros": PARENT_FILE,
        "scored_h19_5": H19_PATH,
        "ext_derived_sgmc_faults_100m_u8": SGMC_PATH,
    }
    receipt = {}
    for key, path in paths.items():
        entry = manifest[key]
        actual = digest(path)
        if actual != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise ValueError(f"manifest pin mismatch for {key}: {actual} != {entry['sha256']}")
        receipt[key] = {"path": str(path.relative_to(ROOT)), "sha256": actual,
                        "bytes": path.stat().st_size, "manifest_id": key}
    actual_base = digest(BASE_FILE)
    if actual_base != BASE_SHA_MEASURED:
        raise ValueError(f"R0 source base hash mismatch: {actual_base} != {BASE_SHA_MEASURED}")
    receipt["solo_d2_8_base"] = {
        "path": str(BASE_FILE.relative_to(ROOT)), "sha256": actual_base,
        "bytes": BASE_FILE.stat().st_size,
        "pin_source": "scripts/run_prune_ladder.py BASE_SHA_MEASURED (recipe-local pin)",
    }
    return receipt


def read_binary(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        arr = src.read(1)
    return footprint & np.isfinite(arr) & (arr > 0.5)


def main() -> int:
    pins = verify_manifest_inputs()
    grid = load_grid(BRIDGE)
    footprint = np.asarray(grid.footprint, bool)
    catalogue = np.asarray(grid.catalogue, bool)
    base = read(BASE_FILE) > 0
    rebuilt = rebuild_parent(grid, base)
    if not rebuilt["content_identical"] or not rebuilt["byte_identical_sha"]:
        raise ValueError(f"R0 did not reproduce byte-for-byte; stop: {rebuilt}")
    parent = read_binary(PARENT_FILE, footprint)
    if int(parent.sum()) != 37654 or digest(PARENT_FILE) != PARENT_SHA:
        raise ValueError("R0 count or published hash mismatch")

    h19 = read_binary(H19_PATH, footprint) & ~catalogue
    candidate, diff = build_prune_refill(parent, h19, catalogue, footprint, BUFFER_PX)
    dcat = ndi.distance_transform_edt(~catalogue)
    if (candidate & (dcat <= BUFFER_PX)).any():
        raise AssertionError("candidate violates the PRUNE 3.75 px collar")
    if (candidate & catalogue).any() or int(candidate.sum()) != int(parent.sum()):
        raise AssertionError("candidate violates catalogue exclusion or fixed mass")
    if not 1.0 <= diff["pct_changed_vs_parent_dots"] <= 50.0:
        raise ValueError(f"parent-change fraction outside 1-50%: {diff['pct_changed_vs_parent_dots']}")

    # REPORT-ONLY instruments. The leakage canary's >0.90 outcome is the brief's
    # explicit stop condition; it is evaluated before any candidate is written.
    folds, _ = buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    canary = leakage_canaries(grid, folds, h19)
    if canary["status"] != "PASS":
        raise RuntimeError(f"leakage canary >0.90; stop and investigate: {canary['max_auc']}")
    proxy = proxy_dti(candidate.astype(np.float32), catalogue, footprint)
    proxy["baseline_r0"] = proxy_dti(parent.astype(np.float32), catalogue, footprint)
    with rasterio.open(SGMC_PATH) as src:
        sgmc = src.read(1) > 0
    sgmc_truth = sgmc & footprint & ~catalogue & (dcat > 3.0)
    sgmc_r0 = metric.dti_binary(parent, sgmc_truth, valid=footprint, known=catalogue)
    sgmc_candidate = metric.dti_binary(candidate, sgmc_truth, valid=footprint, known=catalogue)
    sgmc_report = {
        "evidence_class": "MODEL",
        "instrument": "report-only official-kernel DTI against pinned USGS SGMC faults, off-catalogue and >3 px",
        "baseline_r0_dti": sgmc_r0["dti"], "candidate_dti": sgmc_candidate["dti"],
        "delta_candidate_minus_r0": sgmc_candidate["dti"] - sgmc_r0["dti"],
        "n_truth": sgmc_candidate["n_truth"],
        "warning": "SGMC is a surrogate map, not hidden competition truth and not a live score.",
    }

    # The output basename contains the primary (NaN-outside) file's SHA-256 prefix.
    out_dir = ROOT / "releases"
    work = ROOT / ".cache/prune35"
    work.mkdir(parents=True, exist_ok=True)
    probe = work / "probe-nan.tif"
    serialize(candidate, footprint, probe, "nan", profile_from_catalogue())
    primary_sha = digest(probe)
    candidate_id = f"{PARENT_LABEL}-PRUNE3p75-{SESSION_DATE}-{primary_sha[:8]}"
    nan_path = out_dir / f"{candidate_id}.tif"
    zeros_path = out_dir / f"{candidate_id}-zeros.tif"
    serialize(candidate, footprint, nan_path, "nan", profile_from_catalogue())
    serialize(candidate, footprint, zeros_path, "zeros", profile_from_catalogue())

    nan_report = validate_raster(nan_path, candidate, footprint, catalogue, "nan")
    zeros_report = validate_raster(zeros_path, candidate, footprint, catalogue, "zeros")
    zeros_format = format_report(zeros_path, BRIDGE / "sample_submission.tif", footprint=footprint)
    if not zeros_format["ok"]:
        raise ValueError(f"sample-submission format check failed: {zeros_format}")
    for key, report in (("nan", nan_report), ("zeros", zeros_report)):
        if not report["all_checks_passed"]:
            raise ValueError(f"{key} raster failed checks")
    if digest(nan_path) != primary_sha:
        raise ValueError("primary hash changed after filename construction")
    read_back = read_binary(zeros_path, footprint)
    if not np.array_equal(read_back, candidate):
        raise ValueError("on-disk zeros twin does not reproduce candidate dot set")

    rows = list(csv.DictReader(LEDGER_PATH.open(newline="", encoding="utf-8")))
    candidate_zeros_sha = digest(zeros_path)
    prior = [r for r in rows if r.get("axis") == AXIS and r.get("value") == VALUE]
    existing_same = [r for r in prior if r.get("id") == candidate_id and
                     r.get("sha256") in {primary_sha, candidate_zeros_sha}]
    if prior and not existing_same:
        raise ValueError("(AXIS, value) already exists in ledger; do not repeat")
    duplicate_rows = [r for r in rows if r.get("sha256") in {primary_sha, candidate_zeros_sha}]
    if duplicate_rows and not all(r.get("id") == candidate_id for r in duplicate_rows):
        raise ValueError("exact TIFF hash already exists in ledger")
    known_hashes = {digest(p) for p in (ROOT / "data/scored_fleet").glob("*.tif")}
    if primary_sha in known_hashes or candidate_zeros_sha in known_hashes:
        raise ValueError("candidate hash duplicates a fleet raster")

    note = ("R0 h33-h33-2-b2; PRUNE <=3.75px, FIFO-BFS H19-5 refill; count fixed; pred -0.002 MODEL")
    if len(note) > 140:
        raise AssertionError("submission note exceeds 140 characters")
    source_removed = int((parent & ~candidate).sum())
    source_added = int((candidate & ~parent).sum())
    card = {
        "schema_version": 1, "status": "BUILT", "axis": AXIS, "value": VALUE,
        "parent": {"id": PARENT_ID, "sha256": PARENT_SHA, "n_dots": int(parent.sum()),
                   "rebuild": rebuilt},
        "candidate_id": candidate_id, "n_dots": int(candidate.sum()),
        "pct_changed": diff["pct_changed_vs_parent_dots"],
        "parent_diff": {"removed": source_removed, "added": source_added,
                        "symmetric_difference_cells": diff["changed_grid_cells"],
                        "removed_pct_parent": diff["pct_parent_dots_removed"],
                        "added_pct_parent": diff["pct_parent_dot_count_added"]},
        "catalogue_clearance_px": {"threshold": BUFFER_PX,
                                    "minimum_candidate_distance": float(dcat[candidate].min())},
        "inputs": pins, "outputs": {"nan": nan_report, "zeros": zeros_report,
                                    "sample_format_report_zeros": zeros_format,
                                    "disk_reread_dot_mask_matches": True},
        "report_only": {"catalogue_hide_recover_proxy": proxy,
                         "leakage_canary": canary, "sgmc_control": sgmc_report},
        "predicted_live_change": {"delta": PREDICTED_DELTA, "band": PREDICTED_BAND,
                                  "evidence_class": "MODEL",
                                  "interpretation": "A live change with |delta| < 0.01 is no evidence."},
        "mechanism_card": {
            "source_urls": {
                "fifo_bfs_recipe": "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/94b027bed628422b7b39b485cb918a3fc15e5364/src/gems27/thinning.py",
                "new_fault_near_catalogue_clarification": "https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516",
                "official_rules": "https://docs.nlr.gov/docs/fy26osti/96647.pdf",
            },
            "hypothesis": "At fixed unit mass, removing R0 dots within 375 m of mapped traces and refilling with the recorded H19-5 traversal order modestly reduces near-trace false-positive mass.",
            "mechanism": f"Remove {source_removed:,} R0 dots at catalogue distance <=3.75 px and replace them with the first eligible FIFO-BFS-ranked H19-5 cells beyond 3.75 px; count remains 37,654.",
            "non_fault_mimic": "New fault truth can lie within 300 m of known traces; roads, pipelines, alluvial channels, and mapped linework can also create near-trace responses.",
            "predicted_sign_size": "-0.002 DTI (MODEL; pre-registered band -0.010..+0.006); the 0.2778 R0 value remains CLAIM, not a receipt.",
            "falsifier": "A same-entity public-chunk receipt >=+0.010 versus R0 falsifies the predicted small-negative direction; |delta|<0.010 is no evidence.",
        },
        "submission": {"name": candidate_id, "note": note,
                       "primary_nan": nan_path.name, "primary_sha256": nan_report["sha256"],
                       "fallback_zeros": zeros_path.name, "fallback_sha256": zeros_report["sha256"],
                       "upload_only_one": True, "slot_authorized": False},
        "git": {"branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
                "head_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        "data_use": "Candidate TIFFs are local-only and gitignored; challenge data-use terms remain unchecked.",
    }
    receipt_path = out_dir / f"{candidate_id}-zeros.json"
    receipt_path.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")

    # Keep the ledger generator canonical; it folds this variant manifest into CSV.
    variant_path = ROOT / "ledger/variants_prune375.json"
    variant = {
        "id": candidate_id, "site": "GEMSDOE86", "axis": AXIS, "value": VALUE,
        "status": "BUILT", "n_dots": int(candidate.sum()),
        "pct_changed": round(float(diff["pct_changed_vs_parent_dots"]), 4),
        "sha8": primary_sha[:8], "parent": PARENT_LABEL, "encoding": "nan",
        "sha256": primary_sha, "sha256_nan": primary_sha,
        "sha256_zeros": candidate_zeros_sha,
        "predicted_change": "-0.002 MODEL", "source_url": nan_path.relative_to(ROOT).as_posix(),
        "receipt_score": "", "receipt_date": "",
        "dot_digest": hashlib.sha256(np.flatnonzero(candidate.ravel()).astype("<u4").tobytes()).hexdigest(),
        "files": [nan_path.relative_to(ROOT).as_posix(), zeros_path.relative_to(ROOT).as_posix()],
        "form_note": note, "gate_all_pass": True,
    }
    if variant_path.exists():
        prior_variants = json.loads(variant_path.read_text(encoding="utf-8"))
        if not any(v.get("id") == candidate_id and v.get("sha256") == primary_sha for v in prior_variants):
            raise ValueError("ledger/variants_prune375.json already has a different artifact")
    else:
        variant_path.write_text(json.dumps([variant], indent=2) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts/build_ledger.py")], cwd=ROOT, check=True)

    mechanism = """# Mechanism card — PRUNE <=3.75 px, R0 parent\n\n- **Hypothesis:** At fixed unit mass, removing R0 dots within 375 m of mapped traces and refilling with the recorded H19-5 traversal order modestly reduces near-trace false-positive mass.\n- **Mechanism:** Remove the measured <=3.75 px catalogue collar, then replace those dots with the first eligible cells in the original deterministic FIFO-BFS H19-5 order, all farther than 3.75 px from the catalogue. The count remains 37,654 and no other ranking or physical layer changes.\n- **Non-fault mimic / confounder:** New-fault truth may occur within 300 m of known traces; roads, pipelines, alluvial channels, and map generalization can mimic near-trace responses. The H19-5 traversal is spatially/content-blind and refilling may disrupt spacing.\n- **Predicted live change:** -0.002 DTI (**MODEL**, pre-registered band -0.010..+0.006). Treat |delta| <0.01 as no evidence; 0.2778 for R0 is a **CLAIM**, not a receipt.\n- **Falsifier:** A same-entity public-chunk receipt >= +0.010 versus R0 falsifies the predicted small-negative direction.\n- **Report only:** catalogue hide/recover is **PROXY**; leakage canary and SGMC control are diagnostics, never gates or scores.\n- **Sources:** [FIFO-BFS ranking recipe](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/94b027bed628422b7b39b485cb918a3fc15e5364/src/gems27/thinning.py); [organizer note on new faults near known traces](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516); [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf).\n"""
    (ROOT / "evidence/prune375-mechanism.md").write_text(mechanism)
    summary = {k: card[k] for k in ("status", "axis", "value", "parent", "candidate_id", "n_dots",
                                    "pct_changed", "parent_diff", "catalogue_clearance_px", "inputs",
                                    "outputs", "report_only", "predicted_live_change", "submission", "git")}
    (ROOT / "evidence/prune375-run-card.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"candidate_id": candidate_id, "nan_sha256": nan_report["sha256"],
                      "zeros_sha256": zeros_report["sha256"], "n_dots": int(candidate.sum()),
                      "pct_changed": diff["pct_changed_vs_parent_dots"],
                      "sgmc_delta_model": sgmc_report["delta_candidate_minus_r0"],
                      "proxy_mean": proxy.get("mean"), "leakage_auc_max": canary["max_auc"],
                      "all_format_gates_pass": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
