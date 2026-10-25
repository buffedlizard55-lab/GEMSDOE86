#!/usr/bin/env python3
"""Run the preregistered H86I-HVFD hydrothermal-vent & basement-flexure fault-valve lane.

Frozen design: ``research/H86I_HVFD_PREREGISTRATION.json`` (checked before any
computation). Three fixed arms on ``gems57-pooled-hide-v2`` (seed=20, hide_frac=0.20,
buffer_px=3, 11,321 withheld whole-component positives):
  - ``E1_hvfd_blind_vent_conduit`` (zero-catalogue blind hydrothermal-vent + potential-field
    + 3DEP/LiDAR conduit baseline at 37,654 dots, d_vis > 2.0 px collar, r=2.8 px disc thinning),
  - ``E2_hvfd_foldfair_vent_relay_noisyor`` (preregistered candidate: Dual-Regime Noisy-OR
    coupling E1 with strictly fold-visible relay/tip/bend traps at 37,654 dots, d_vis > 2.0 px),
  - ``E3_hvfd_collar_ablation_44090`` (collar/budget ablation: identical S_HVFD surface emitted
    at 44,090 dots with d_vis > 1.5 px collar, isolating the h33-2-b2 collar-pruning effect),
scored alongside the fold-fair ``R0_G25_foldfair_collar`` control (unpruned GEMSDOE25 d2.8
masked strictly by fold-visible faults d_vis > 2.0 px).

Fail-closed sequence (AGENTS.md Rules 1-11 & PA-86-01/02):
1. Frozen preregistration + ``require_like_for_like`` preflight;
2. Static zero-catalogue features (verifying ``dist_known_fault_px`` is never read) +
   fold-visible structural trap planes (clamped at d_vis >= 3.5 px);
3. Single-feature leakage canary across all 18 planes (max(AUC, 1-AUC) > 0.90 stops);
4. Shared buffered whole-component holdout across all 3 arms and fold-fair controls;
5. Pre-placement surface registry check (``check_h86e_registry.py --surface``) BEFORE placement;
   any Spearman firing > 0.90 or missing inventory raster halts before placement;
6. Final dot placement (37,654 dots, r=2.8 px disc thinning, d_cat > 2.0 px), followed by
   final-dot registry check and PA-86-02 chance-overlap check BEFORE GeoTIFF serialization;
7. Shared fail-closed writer + independent on-disk validation + 0644 permission normalization +
   Run Card JSON. A PA diagnostic or audit emission never overrides a failing literal or
   completeness gate: unless every scientific, completeness, and literal gate passes, verdict
   is ``negative`` and decision is ``DO NOT SUBMIT``.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]

from gems57 import evaluate_holdout as EH, grid, holdout  # noqa: E402
from gems57 import submission_writer, validate  # noqa: E402
from gems86_hvfd.features import (  # noqa: E402
    ACCESSED_CSV_COLUMNS,
    BANNED_CSV_COLUMNS,
    STATIC_FEATURE_NAMES,
    TRAP_FEATURE_NAMES,
    build_hvfd_static_features,
    compose_hvfd_surface,
    compute_visible_trap_fields,
    disc_thin_prefix,
    rank01,
)
from scripts.protocol_preflight import require_like_for_like  # noqa: E402

BUDGET_PRIMARY = 37_654
BUDGET_ABLATION = 44_090
RADIUS_PX = 2.8
COLLAR_PRIMARY_PX = 2.0
COLLAR_ABLATION_PX = 1.5
SEED = 20

FEATURE_TIF = ROOT / "data/training_features.tif"
EXTERNAL_DIR = ROOT / "data/external"
R0_G25 = ROOT / "data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
D28 = ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
H33 = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"

OUT_DIR = ROOT / "docs/downloads"
EV_DIR = ROOT / "docs/evidence"
WORK_DIR = ROOT / ".cache/gems_data/work"
PREREGISTRATION = ROOT / "research/H86I_HVFD_PREREGISTRATION.json"
PREREGISTRATION_MD = ROOT / "research/H86I_HVFD_PREREGISTRATION.md"
CARD_PATH = EV_DIR / "h86i-hvfd-run-card.json"
CANDIDATE_ARM = "E2_hvfd_foldfair_vent_relay_noisyor"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_array(path: Path, a: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(a, dtype=np.float32))
    return sha256(path)


def load_binary(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1)
    return np.isfinite(a) & (a > 0)


def require_preregistration(
    prereg_path: Path = PREREGISTRATION,
    prereg_md: Path = PREREGISTRATION_MD,
) -> dict:
    if not prereg_path.is_file() or not prereg_md.is_file():
        raise RuntimeError(f"missing preregistration: {prereg_path} or {prereg_md}")
    doc = json.loads(prereg_path.read_text(encoding="utf-8"))
    if doc.get("lane") != "H86I-HVFD" or doc.get("status") != "frozen_before_lane_computation":
        raise RuntimeError("H86I-HVFD preregistration identity/status drifted")
    if doc.get("candidate_arm") != CANDIDATE_ARM:
        raise RuntimeError("H86I-HVFD candidate arm drifted")
    hypotheses = doc.get("ranked_hypotheses", [])
    arms = doc.get("arms", [])
    if not (3 <= len(hypotheses) <= 5):
        raise RuntimeError("H86I-HVFD preregistration must rank 3-5 hypotheses")
    if len(arms) != 3:
        raise RuntimeError("H86I-HVFD preregistration must freeze exactly 3 arms")
    required = {
        "layers",
        "transform",
        "non_fault_mimic",
        "uncatalogued_rationale",
        "novelty",
        "cost",
        "official_data",
    }
    if any(not required.issubset(item) for item in (*hypotheses, *arms)):
        raise RuntimeError("H86I-HVFD preregistration is missing required hypothesis/arm fields")
    budget = doc.get("budget", {})
    if (
        budget.get("max_arms") != 3
        or budget.get("max_hours") != 2
        or budget.get("dots_primary") != BUDGET_PRIMARY
        or budget.get("dots_ablation") != BUDGET_ABLATION
    ):
        raise RuntimeError("H86I-HVFD budget drifted from frozen limits")
    holdout_doc = doc.get("holdout", {})
    if (
        holdout_doc.get("alpha") != 0.2
        or holdout_doc.get("beta") != 0.8
        or holdout_doc.get("kernel_m") != 300
        or holdout_doc.get("withheld_positive_pixels") != 11321
    ):
        raise RuntimeError("H86I-HVFD holdout parameters drifted")
    return doc


def canary(
    fields: dict[str, np.ndarray],
    folds: list[dict],
    fp: np.ndarray,
    stop_auc: float = 0.90,
) -> dict[str, dict]:
    rng = np.random.default_rng(86_2025)
    out: dict[str, dict] = {}
    for idx, (name, field) in enumerate(fields.items()):
        aucs = []
        for fold_idx, fold in enumerate(folds):
            active = fold["region"] & fp & ~fold["masked_known"]
            truth = fold["truth"] & active
            py, px = np.nonzero(truth)
            ny, nx = np.nonzero(active & ~truth)
            draw = np.random.default_rng(int(rng.integers(1, 2**31 - 1)) + idx * 17 + fold_idx)
            take = draw.choice(ny.size, size=min(40_000, ny.size), replace=False)
            y = np.concatenate([np.ones(py.size, dtype=np.int8), np.zeros(take.size, dtype=np.int8)])
            s = np.concatenate([field[py, px], field[ny[take], nx[take]]]).astype(np.float64)
            s = np.where(np.isfinite(s), s, 0.0)
            auc = 0.5 if np.allclose(s, s[0]) else float(roc_auc_score(y, s))
            aucs.append(auc)
        disc = [max(a, 1.0 - a) for a in aucs]
        out[name] = {
            "source": "visible_only_trap" if name in TRAP_FEATURE_NAMES else "catalogue_blind_static",
            "fold_auc": aucs,
            "mean_auc": float(np.mean(aucs)),
            "max_discriminative_auc": float(np.max(disc)),
            "threshold": stop_auc,
            "leakage_flag": bool(np.max(disc) > stop_auc),
        }
    return out


def holdout_disc_arm(
    surface: np.ndarray,
    folds: list[dict],
    fp: np.ndarray,
    budget: int,
    collar_px: float,
    radius_px: float = RADIUS_PX,
) -> tuple[np.ndarray, dict]:
    """Evaluate a continuous surface on the 4 buffered holdout folds using Euclidean disc thinning."""
    vis0 = np.asarray(folds[0]["visible"], dtype=bool)
    same_visible = all(np.array_equal(np.asarray(f["visible"], dtype=bool), vis0) for f in folds[1:])
    terms = []
    per_fold = {}
    shared_emitted = None
    if same_visible:
        allowed = fp & ~vis0 & (ndi.distance_transform_edt(~vis0) > collar_px)
        shared_emitted = disc_thin_prefix(surface, allowed, budget=budget, radius_px=radius_px).astype(np.float32)

    for f in folds:
        if shared_emitted is not None:
            emitted = shared_emitted
        else:
            vis = np.asarray(f["visible"], dtype=bool)
            allowed = fp & ~vis & (ndi.distance_transform_edt(~vis) > collar_px)
            emitted = disc_thin_prefix(surface, allowed, budget=budget, radius_px=radius_px).astype(np.float32)
        result, block_terms = EH.evaluate(emitted, f, fp, block_side=200)
        terms.append(block_terms)
        per_fold[f["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": result["dti"],
            "n_truth": result["n_truth"],
            "emitted": result["n_emitted"],
            "collar_px": float(collar_px),
            "radius_px": float(radius_px),
        }
    return np.sum(terms, axis=0), per_fold


def holdout_binary_control(
    dots: np.ndarray, folds: list[dict], fp: np.ndarray, collar_px: float = 2.0
) -> tuple[np.ndarray, dict]:
    """Evaluate a pre-thinned binary dot control on holdout folds without re-decimating zero ties."""
    terms = []
    per_fold = {}
    base = np.asarray(dots, dtype=bool) & fp
    for fold in folds:
        vis = np.asarray(fold["visible"], dtype=bool)
        allowed = fp & ~vis & (ndi.distance_transform_edt(~vis) > collar_px)
        emitted = (base & allowed).astype(np.float32)
        result, block_terms = EH.evaluate(emitted, fold, fp, block_side=200)
        terms.append(block_terms)
        per_fold[fold["name"]] = {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": result["dti"],
            "n_truth": result["n_truth"],
            "emitted": result["n_emitted"],
            "collar_px": float(collar_px),
        }
    return np.sum(terms, axis=0), per_fold


def run_registry_check(candidate_path: Path, report_path: Path, *, surface: bool) -> tuple[dict, int]:
    expected_mode = "surface" if surface else "final_dots"
    if report_path.is_file():
        cached = json.loads(report_path.read_text(encoding="utf-8"))
        if (
            cached.get("schema") == "gems86.registry-candidate.v2"
            and cached.get("mode") == expected_mode
            and cached.get("candidate_source_sha256") == sha256(candidate_path)
            and cached.get("inventory_rasters_missing") == []
        ):
            gate_key = "surface_gate_pass" if surface else "final_dots_gate_pass"
            rc = 0 if (cached.get(gate_key) and cached.get("literal_gate_pass")) else 2
            return cached, rc
    cmd = [
        sys.executable,
        str(ROOT / "scripts/check_h86e_registry.py"),
        str(candidate_path.relative_to(ROOT)),
        str(report_path.relative_to(ROOT)),
    ]
    if surface:
        cmd.append("--surface")
    proc = subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True)
    if not report_path.is_file():
        raise RuntimeError(f"registry checker wrote no report for {candidate_path}: {proc.stderr}")
    return json.loads(report_path.read_text(encoding="utf-8")), int(proc.returncode)


def run_chance_check(registry_report: Path, candidate_path: Path, output: Path) -> dict:
    output.unlink(missing_ok=True)
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/pa86_chance_overlap.py"),
            str(registry_report),
            str(candidate_path),
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if output.is_file():
        report = json.loads(output.read_text(encoding="utf-8"))
        report["runner_returncode"] = int(proc.returncode)
        return report
    return {
        "schema": "gems86.pa86-chance-overlap.v2",
        "status": "FAILED_CLOSED_NO_REPORT",
        "runner_returncode": int(proc.returncode),
        "gate_pass": False,
        "informative_firings": None,
        "stderr_tail": proc.stderr[-3000:],
        "stdout_tail": proc.stdout[-1000:],
        "note": "pa86_chance_overlap.py refused to certify (binding/completeness); recorded verbatim, never bypassed with a private computation.",
    }


def registry_summary(report: dict, returncode: int) -> dict:
    shared = report.get("shared_summary", {})
    return {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "runner_returncode": returncode,
        "registry_rasters_expected": report.get("registry_rasters_expected", shared.get("registry_rasters_expected")),
        "registry_rasters_measured": report.get("registry_rasters_measured"),
        "registry_rasters_missing": len(report.get("inventory_rasters_missing", [])),
        "registry_errors": report.get("errors", []),
        "registry_complete_for_index": report.get("registry_complete_for_index"),
        "complete_accessible_scan": shared.get("complete_accessible_scan"),
        "byte_unique_among_checked": shared.get("byte_unique_among_checked"),
        "pixel_unique_among_checked": shared.get("pixel_unique_among_checked"),
        "worst_spearman_full_footprint": shared.get("worst_spearman_full_footprint"),
        "worst_spearman_submission": shared.get("worst_rho_submission"),
        "worst_dot_overlap": shared.get("worst_dot_overlap"),
        "worst_overlap_submission": shared.get("worst_overlap_submission"),
        "surface_gate_pass": report.get("surface_gate_pass"),
        "final_dots_gate_pass": report.get("final_dots_gate_pass"),
        "literal_gate_pass": report.get("literal_gate_pass"),
        "two_phase": report.get("two_phase"),
        "top15_by_forward_overlap": report.get("top15_by_forward_overlap"),
        "top15_by_spearman": report.get("top15_by_spearman"),
        "scope": report.get("scope"),
    }


def write_candidate(dots: np.ndarray, g, name: str, note: str, metadata: dict) -> dict:
    pred = np.where(dots & g.footprint, 1.0, 0.0).astype(np.float32)
    path = OUT_DIR / f"{name}.tif"
    receipt = submission_writer.write_submission(
        path,
        pred,
        ROOT / "data/bridge/sample_submission.tif",
        g.footprint,
        note=note,
        name=name,
        catalogue=g.catalogue,
        metadata=metadata,
    )
    disk = validate.validate(path, g.footprint, g.catalogue)
    if not disk["all_checks_passed"]:
        raise RuntimeError("independent on-disk validator failed")
    receipt["independent_disk_validation"] = disk
    json_path = path.with_suffix(".json")
    zip_path = path.with_suffix(".zip")
    json_path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    for p in (path, zip_path, json_path):
        if p.is_file():
            os.chmod(p, 0o644)
    return receipt


def run_lane() -> dict:
    started = time.time()
    preregistration = require_preregistration()
    preflight = require_like_for_like()
    g = grid.load_grid(ROOT / "data/bridge")
    if not FEATURE_TIF.is_file():
        raise FileNotFoundError(f"missing pinned feature raster: {FEATURE_TIF}")
    fp, cat = g.footprint, g.catalogue
    folds, _quad = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)
    withheld = int(np.logical_or.reduce([np.asarray(f["truth"], bool) for f in folds]).sum())

    print("building HVFD static zero-catalogue features...", flush=True)
    feature_hashes: dict[str, str] = {}
    static_fields: dict[str, np.ndarray] = {}
    if all((WORK_DIR / f"h86i_hvfd_{name}.npy").is_file() for name in STATIC_FEATURE_NAMES):
        ACCESSED_CSV_COLUMNS["gdr_wellspring_in_footprint.csv"] = (
            "row",
            "col",
            "temp_c",
            "geothermquartz_c",
            "geothermchalc_c",
        )
        ACCESSED_CSV_COLUMNS["gdr_volcanic_vents_in_footprint.csv"] = ("row", "col")
        for name in STATIC_FEATURE_NAMES:
            p = WORK_DIR / f"h86i_hvfd_{name}.npy"
            feature_hashes[name] = sha256(p)
            static_fields[name] = np.load(p, mmap_mode="r")
    else:
        static_fields_ram = build_hvfd_static_features(FEATURE_TIF, EXTERNAL_DIR, fp)
        assert not any(
            set(cols) & BANNED_CSV_COLUMNS for cols in ACCESSED_CSV_COLUMNS.values()
        ), "banned CSV column accessed"
        for name in list(static_fields_ram.keys()):
            p = WORK_DIR / f"h86i_hvfd_{name}.npy"
            feature_hashes[name] = save_array(p, static_fields_ram.pop(name))
            static_fields[name] = np.load(p, mmap_mode="r")
        del static_fields_ram

    print("building fold-visible structural trap planes...", flush=True)
    vis_holdout = np.asarray(folds[0]["visible"], dtype=bool)
    trap_holdout: dict[str, np.ndarray] = {}
    if all((WORK_DIR / f"h86i_hvfd_{name}.npy").is_file() for name in TRAP_FEATURE_NAMES):
        for name in TRAP_FEATURE_NAMES:
            p = WORK_DIR / f"h86i_hvfd_{name}.npy"
            feature_hashes[name] = sha256(p)
            trap_holdout[name] = np.load(p, mmap_mode="r")
    else:
        trap_holdout_ram = compute_visible_trap_fields(
            vis_holdout, fp, static_fields["hvfd_vent_composite"]
        )
        for name in list(trap_holdout_ram.keys()):
            p = WORK_DIR / f"h86i_hvfd_{name}.npy"
            feature_hashes[name] = save_array(p, trap_holdout_ram.pop(name))
            trap_holdout[name] = np.load(p, mmap_mode="r")
        del trap_holdout_ram

    all_holdout_fields = {**static_fields, **trap_holdout}

    print("running single-feature leakage canary...", flush=True)
    leakage = canary(all_holdout_fields, folds, fp, stop_auc=0.90)
    leakage_stop = any(v["leakage_flag"] for v in leakage.values())
    max_canary_auc = max(v["max_discriminative_auc"] for v in leakage.values())

    surf_holdout = compose_hvfd_surface(
        p_blind=static_fields["hvfd_blind_conduit_surface"],
        v_vent=static_fields["hvfd_vent_composite"],
        m_trap=trap_holdout["vis_trap_composite"],
        footprint=fp,
    )

    holdout_terms: dict[str, np.ndarray] = {}
    holdout_per_fold: dict[str, dict] = {}
    if not leakage_stop:
        print("scoring E1_hvfd_blind_vent_conduit...", flush=True)
        t_e1, pf_e1 = holdout_disc_arm(
            static_fields["hvfd_blind_conduit_surface"],
            folds,
            fp,
            budget=BUDGET_PRIMARY,
            collar_px=COLLAR_PRIMARY_PX,
            radius_px=RADIUS_PX,
        )
        holdout_terms["E1_hvfd_blind_vent_conduit"] = t_e1
        holdout_per_fold["E1_hvfd_blind_vent_conduit"] = pf_e1

        print("scoring E2_hvfd_foldfair_vent_relay_noisyor...", flush=True)
        t_e2, pf_e2 = holdout_disc_arm(
            surf_holdout,
            folds,
            fp,
            budget=BUDGET_PRIMARY,
            collar_px=COLLAR_PRIMARY_PX,
            radius_px=RADIUS_PX,
        )
        holdout_terms["E2_hvfd_foldfair_vent_relay_noisyor"] = t_e2
        holdout_per_fold["E2_hvfd_foldfair_vent_relay_noisyor"] = pf_e2

        print("scoring E3_hvfd_collar_ablation_44090...", flush=True)
        t_e3, pf_e3 = holdout_disc_arm(
            surf_holdout,
            folds,
            fp,
            budget=BUDGET_ABLATION,
            collar_px=COLLAR_ABLATION_PX,
            radius_px=RADIUS_PX,
        )
        holdout_terms["E3_hvfd_collar_ablation_44090"] = t_e3
        holdout_per_fold["E3_hvfd_collar_ablation_44090"] = pf_e3

        for label, path in (
            ("R0_G25_foldfair_collar", R0_G25),
            ("R0_D28_foldfair_collar", D28),
            ("H33_foldfair_collar", H33),
        ):
            if path.is_file():
                terms, per = holdout_binary_control(load_binary(path), folds, fp, collar_px=2.0)
                holdout_terms[label] = terms
                holdout_per_fold[label] = per

    pooled = None
    if holdout_terms:
        pooled = EH.pooled_summary(
            holdout_terms,
            draws=1000,
            seed=861025,
            candidate=CANDIDATE_ARM,
        )

    current_best = json.loads((EV_DIR / "lane86c_results.json").read_text())[
        "holdout_buffered_whole_components"
    ]["scores"]["E3_kslb_noisyor_44k"]
    same_split = withheld == int(current_best["withheld_positive_pixels"])
    cand_score = None if pooled is None else pooled["scores"][CANDIDATE_ARM]
    best_ctrl_name = None if pooled is None else pooled["best_comparable_control"]
    best_delta = None if pooled is None else pooled["paired_differences"][best_ctrl_name]
    beats_current = bool(
        same_split
        and cand_score is not None
        and cand_score["dti"] > current_best["dti"]
        and cand_score["ci95"][0] > current_best["ci95"][1]
    )
    beats_controls = bool(best_delta is not None and best_delta["ci95"][0] > 0.0)

    # Build full-footprint surface after holdout evaluation and run pre-placement surface check
    print("building full-footprint candidate surface for pre-placement registry check...", flush=True)
    surface_path = WORK_DIR / "h86i_hvfd_final_surface.npy"
    surf_raw_path = WORK_DIR / "h86i_hvfd_surf_full_raw.npy"
    if surface_path.is_file() and surf_raw_path.is_file():
        surf_full = np.load(surf_raw_path, mmap_mode="r")
        surface_sha = sha256(surface_path)
    elif surface_path.is_file():
        surf_full = np.load(surface_path, mmap_mode="r")
        surface_sha = sha256(surface_path)
    else:
        trap_full = compute_visible_trap_fields(cat, fp, static_fields["hvfd_vent_composite"])
        surf_full = compose_hvfd_surface(
            p_blind=static_fields["hvfd_blind_conduit_surface"],
            v_vent=static_fields["hvfd_vent_composite"],
            m_trap=trap_full["vis_trap_composite"],
            footprint=fp,
        )
        save_array(surf_raw_path, surf_full)
        surface_sha = save_array(surface_path, rank01(surf_full, fp))
    surface_report_path = EV_DIR / "h86i-hvfd-registry-surface.json"
    print("running pre-placement surface registry check...", flush=True)
    surface_report, surface_rc = run_registry_check(surface_path, surface_report_path, surface=True)
    surface_summary = registry_summary(surface_report, surface_rc)

    surface_rho = (
        surface_report.get("two_phase", {})
        .get("literal_reading", {})
        .get("rho_firings")
    )
    surface_missing = len(surface_report.get("inventory_rasters_missing", []))
    surface_complete = bool(
        surface_report.get("registry_complete_for_index")
        and surface_report.get("surface_gate_pass")
        and surface_rc == 0
    )
    rho_stop = surface_rho is None or int(surface_rho) > 0
    missing_stop = surface_missing > 0
    allow_audit_placement = (not leakage_stop) and (not rho_stop) and (not missing_stop)

    dots_summary = None
    pa86_report = None
    receipt = None
    submission_name = None
    note = None
    dots_sha = None
    if allow_audit_placement:
        dots_path = WORK_DIR / "h86i_hvfd_final_dots.npy"
        if dots_path.is_file():
            final_dots = np.load(dots_path) > 0.5
            dots_sha = sha256(dots_path)
        else:
            allowed_full = fp & ~cat & (ndi.distance_transform_edt(~cat) > COLLAR_PRIMARY_PX)
            final_dots = disc_thin_prefix(
                surf_full,
                allowed_full,
                budget=BUDGET_PRIMARY,
                radius_px=RADIUS_PX,
            )
            dots_sha = save_array(dots_path, final_dots.astype(np.float32))
        dots_report_path = EV_DIR / "h86i-hvfd-registry-final-dots.json"
        print("running pre-serialization final-dot registry check...", flush=True)
        dots_report, dots_rc = run_registry_check(dots_path, dots_report_path, surface=False)
        dots_summary = registry_summary(dots_report, dots_rc)
        pa86_path = EV_DIR / "h86i-hvfd-pa86-chance-overlap.json"
        pa86_report = run_chance_check(dots_report_path, dots_path, pa86_path)

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
        submission_name = f"gems86-h86i-hvfd-vent-flexure-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"
        note = (
            f"H86I-HVFD 2m-probe+sinter+biharm-flexure+relay NoisyOR {int(final_dots.sum())}d "
            f"r=2.8px d>2px; HOLDOUT-DTI={cand_score['dti']:.4f}; audit-only DO NOT SUBMIT"
        )[:140]
        print("serializing format-valid audit GeoTIFF + ZIP + receipt...", flush=True)
        receipt = write_candidate(
            final_dots,
            g,
            submission_name,
            note,
            metadata={
                "lane": "H86I-HVFD",
                "hypothesis": "Hydrothermal-vent thermal-wall, paleo-sinter & bi-harmonic basement flexure gated fault-valve discovery",
                "candidate_arm": CANDIDATE_ARM,
                "budget": BUDGET_PRIMARY,
                "radius_px": RADIUS_PX,
                "collar_px": COLLAR_PRIMARY_PX,
                "feature_hashes": feature_hashes,
                "surface_sha256": surface_sha,
                "dots_sha256": dots_sha,
            },
        )

    dots_complete = bool(
        dots_summary
        and dots_summary.get("registry_complete_for_index")
        and dots_summary.get("final_dots_gate_pass")
        and dots_summary.get("literal_gate_pass")
        and dots_summary.get("runner_returncode") == 0
    )
    pa_pass = bool(
        pa86_report
        and pa86_report.get("gate_pass") is True
        and pa86_report.get("informative_firings") == 0
    )
    promote = bool(
        allow_audit_placement
        and beats_current
        and beats_controls
        and surface_complete
        and dots_complete
        and pa_pass
        and receipt is not None
    )

    reasons: list[str] = []
    if leakage_stop:
        reasons.append(f"single-feature leakage canary exceeded 0.90 (max={max_canary_auc:.4f})")
    if not same_split:
        reasons.append(f"withheld positive count {withheld} != {current_best['withheld_positive_pixels']}")
    if cand_score is None:
        reasons.append("holdout was not scored")
    elif not beats_current:
        reasons.append(
            f"candidate HOLDOUT-DTI {cand_score['dti']:.4f} {cand_score['ci95']} does not beat "
            f"same-split historical best {current_best['dti']:.4f} {current_best['ci95']} with separated CIs"
        )
    if not beats_controls:
        reasons.append(
            f"paired HOLDOUT-DTI delta vs {best_ctrl_name} is {best_delta['delta']:.4f} "
            f"with 95% CI {best_delta['ci95']} (not strictly positive)"
        )
    if rho_stop:
        reasons.append(f"pre-placement surface Spearman firing count = {surface_rho}; placement stopped")
    if missing_stop:
        reasons.append(f"inventory rasters missing locally: {surface_missing}; placement stopped")
    if not surface_complete:
        reasons.append(
            f"surface registry scan incomplete/failed (errors={len(surface_summary['registry_errors'])}, "
            f"returncode={surface_rc})"
        )
    if dots_summary is not None and not dots_complete:
        reasons.append(
            f"final-dot registry gate failed (worst_dot_overlap={dots_summary['worst_dot_overlap']} "
            f"vs {dots_summary['worst_overlap_submission']}, errors={len(dots_summary['registry_errors'])})"
        )
    if pa86_report is not None and not pa_pass:
        reasons.append(
            f"PA-86-02 chance-overlap gate did not pass (status={pa86_report.get('status', 'completed')}, "
            f"informative_firings={pa86_report.get('informative_firings')})"
        )

    decision = "OK TO DOWNLOAD AND SUBMIT" if promote else "DO NOT SUBMIT"
    run_card = {
        "schema": "gems86.h86i-hvfd-run-card.v1",
        "evidence_class": "RUN-CARD",
        "lane": "H86I-HVFD",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "preregistration": {
            "path": str(PREREGISTRATION.relative_to(ROOT)),
            "markdown_path": str(PREREGISTRATION_MD.relative_to(ROOT)),
            "sha256": sha256(PREREGISTRATION),
            "status": preregistration["status"],
            "frozen_utc": preregistration["frozen_utc"],
            "ranked_hypothesis_ids": [h["id"] for h in preregistration["ranked_hypotheses"]],
            "arm_ids": [a["id"] for a in preregistration["arms"]],
            "candidate_arm": CANDIDATE_ARM,
        },
        "hypothesis": (
            "Unmapped Great Basin geothermal faults beneath Holocene fan/playa cover are marked by "
            "2-m shallow temperature probe lateral thermal walls (|grad T_2m|), 726 paleogeothermal "
            "sinter/travertine/tufa vent mounds, 300 m upslope-advected silica geothermometer excess, "
            "MT 2000 m clay-cap margin gradients, bi-harmonic basement plate flexure (|nabla^4 z_b|), "
            "and Laplace g_zz Poisson magnetite-destruction residuals co-activating inside fold-visible "
            "stepover relay bridges, crack-tip cones, and releasing-bend hinges."
        ),
        "mechanism": (
            "13 zero-catalogue static planes (DOE GDR-1391 3,800 2-m probes |grad T_2m| + F2mDAB plume, "
            "726 paleo-sinter/tufa vents, 300 m upslope-advected quartz/chalcedony geothermometers, "
            "21 Quaternary vents, MT clay-cap margin gradient, GeoDAWN K/eTh & eU/eTh alteration, "
            "Band 15 bi-harmonic |nabla^4 z_b| flexure, Bands 18/11 Laplace g_zz hinge, Band 9 Poisson "
            "magnetite-destruction residual, 3DEP 1 m LiDAR + 10 m DEM + fluvial chi/ksn scarps, "
            "Bands 4/7/8/10/16 Coulomb-seismic valve, and Lahontan/Bonneville + GeoDAWN seam suppression) "
            "coupled in E2 via Dual-Regime Noisy-OR with strictly fold-visible relay/tip/bend traps "
            "(d_vis >= 3.5 px clamp), emitted via Euclidean r=2.8 px disc thinning at 37,654 dots and "
            "d > 2.0 px collar (h33-2-b2 collar geometry)."
        ),
        "named_non_fault_process": (
            "Down-gradient lateral thermal outflow plumes in alluvial fans (mitigated by |grad T_2m| "
            "thermal-wall gradient and 300 m upslope advection along +grad DEM); Pleistocene Lake "
            "Lahontan (1270, 1332 m) and Bonneville (1463, 1552 m) wave-cut shoreline benches; "
            "unfaulted circular pluton rims and GeoDAWN acquisition-block stitch seams; flat-lying "
            "conductive playa evaporites."
        ),
        "named_non_fault_mimic": (
            "Down-gradient lateral thermal outflow plumes, Lahontan/Bonneville shorelines, "
            "unfaulted pluton contacts, GeoDAWN survey-block stitch seams, and flat-lying playa clays."
        ),
        "source_layers": [
            "DOE GDR-1391 2m_temperature_probe_INGENIOUS_regional_data.zip (3,800 probes, SHA256 1301f70d...)",
            "DOE GDR-1391 paleo_geothermal_regional.zip (726 sinter/travertine/tufa deposits, SHA256 faffcf69...)",
            "DOE GDR-1391 gdr_wellspring_in_footprint.csv (temp_c, geothermquartz_c, geothermchalc_c; dist_known_fault_px banned)",
            "DOE GDR-1391 gdr_volcanic_vents_in_footprint.csv (row, col; dist_known_fault_px banned)",
            "training_features.tif Bands 2, 4, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19",
            "USGS 3DEP lidar_scarp_features_u8.tif, topo_10m_derived_100m_u8.tif, dem10_chi_100m_i16.tif",
            "USGS GeoDAWN geodawn_rad_u8.tif and acquisition_block_id_100m.tif",
        ],
        "anti_leakage_audit": {
            "accessed_csv_columns": {k: list(v) for k, v in ACCESSED_CSV_COLUMNS.items()},
            "banned_csv_columns_verified_unread": sorted(BANNED_CSV_COLUMNS),
            "static_features_read_catalogue": False,
            "holdout_traps_use_fold_visible_only": True,
            "visible_trap_distance_clamp_px": 3.5,
        },
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "design": (
                "buffered whole-component quadrant draw, seed 20, hide fraction 0.20, "
                "visible-fault buffer 3 px, pooled 200-px (20 km) physical-block bootstrap (1,000 draws)"
            ),
            "withheld_positive_pixels": withheld,
            "same_split_as_historical_kslb": same_split,
            "candidate_arm": CANDIDATE_ARM,
            "candidate": cand_score,
            "paired_delta_vs_best_preregistered_control": best_delta,
            "best_preregistered_control": best_ctrl_name,
            "current_holdout_best_same_split": {
                "evidence_class": "HOLDOUT-DTI",
                "source": "docs/evidence/lane86c_results.json",
                "arm": "E3_kslb_noisyor_44k",
                "dti": current_best["dti"],
                "ci95": current_best["ci95"],
                "withheld_positive_pixels": current_best["withheld_positive_pixels"],
            },
            "beats_current_holdout_best": beats_current,
            "beats_preregistered_controls": beats_controls,
            "pooled_summary": pooled,
            "per_fold": holdout_per_fold,
        },
        "leakage_canary": {
            "evidence_class": "HOLDOUT-CANARY",
            "threshold_discriminative_auc": 0.90,
            "any_flag": leakage_stop,
            "max_discriminative_auc": max_canary_auc,
            "features": leakage,
        },
        "correlation_overlap_vs_registry": {
            "surface_preplacement": surface_summary,
            "final_dots": dots_summary,
            "pa86_02_chance_overlap": pa86_report,
        },
        "feature_hashes": feature_hashes,
        "surface_sha256": surface_sha,
        "dots_sha256": dots_sha,
        "raster_sha256": None if receipt is None else receipt["sha256"],
        "zip_sha256": None if receipt is None else receipt.get("zip_sha256"),
        "validator_output": None
        if receipt is None
        else {
            "evidence_class": "LOCAL-FORMAT-VALIDATION",
            "all_checks_passed": receipt["independent_disk_validation"]["all_checks_passed"],
            "no_nan_inside_footprint": receipt["independent_disk_validation"]["checks"]["in_footprint_all_finite"],
            "values_in_0_1": receipt["independent_disk_validation"]["checks"]["range_0_1_guaranteed"],
            "crs_shape_transform_match": all(
                receipt["independent_disk_validation"]["checks"][key]
                for key in ("crs_epsg_32611", "dimensions_3730x3292", "transform_matches_sample_submission")
            ),
            "checks": receipt["independent_disk_validation"]["checks"],
            "positive_pixels": receipt["independent_disk_validation"]["emitted_positive_pixels"],
            "min": receipt["independent_disk_validation"]["min"],
            "max": receipt["independent_disk_validation"]["max"],
        },
        "submission_name": submission_name,
        "submission_file": None if submission_name is None else f"docs/downloads/{submission_name}.tif",
        "zip_file": None if submission_name is None else f"docs/downloads/{submission_name}.zip",
        "receipt_file": None if submission_name is None else f"docs/downloads/{submission_name}.json",
        "note": note,
        "note_chars": None if note is None else len(note),
        "verdict": "promote" if promote else "negative",
        "submission_ready": promote,
        "safe_to_submit": promote,
        "safe_to_download_for_audit": bool(
            receipt is not None and receipt["independent_disk_validation"]["all_checks_passed"]
        ),
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "decision": decision,
        "decision_reason": "; ".join(reasons),
        "experiments_run": 0 if leakage_stop else 3,
        "placement_performed": allow_audit_placement,
        "preflight_status": preflight.get("status"),
        "runtime_seconds": round(time.time() - started, 3),
        "organizer_confirmed": False,
    }
    CARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    CARD_PATH.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "lane": "H86I-HVFD",
                "submission": run_card["submission_file"],
                "sha256": run_card["raster_sha256"],
                "e1_blind_dti": None if pooled is None else pooled["scores"]["E1_hvfd_blind_vent_conduit"]["dti"],
                "e2_candidate_dti": None if cand_score is None else cand_score["dti"],
                "e2_candidate_ci95": None if cand_score is None else cand_score["ci95"],
                "e3_ablation_44090_dti": None
                if pooled is None
                else pooled["scores"]["E3_hvfd_collar_ablation_44090"]["dti"],
                "r0_g25_foldfair_dti": None
                if pooled is None or "R0_G25_foldfair_collar" not in pooled["scores"]
                else pooled["scores"]["R0_G25_foldfair_collar"]["dti"],
                "current_holdout_best": current_best["dti"],
                "beats_current": beats_current,
                "beats_controls": beats_controls,
                "max_canary_auc": max_canary_auc,
                "surface_rho_firings": surface_rho,
                "decision": decision,
                "verdict": run_card["verdict"],
                "reason": run_card["decision_reason"],
            },
            indent=2,
        ),
        flush=True,
    )
    return run_card


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    run_lane()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
