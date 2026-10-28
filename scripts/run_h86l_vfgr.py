#!/usr/bin/env python3
"""H86L-VFGR: fold-safe visible-fault edge residual, three frozen arms.

Uses the shared evaluator and writer. Does not fork the metric. Does not pick
a weekly slot. A format-valid TIFF is an audit file unless every frozen gate
passes; safe_to_submit stays false either way.
"""
from __future__ import annotations

import hashlib
import json
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

from gems57 import evaluate_holdout as EH  # noqa: E402
from gems57 import grid as G  # noqa: E402
from gems57 import holdout  # noqa: E402
from gems57 import submission_writer  # noqa: E402
from gems57.uniqueness import (  # noqa: E402
    OVERLAP_LIMIT,
    RHO_LIMIT,
    _near,
    compare_array_to_registry,
    two_phase_summary,
)
from gems86.io import read_band  # noqa: E402
from gems86_mcsp.celf import static_ek_spacing_allocate  # noqa: E402
from gems86_vfgr.features import (  # noqa: E402
    basement_mass_balance_surface,
    corroborated_residual_surface,
)
from scripts.protocol_preflight import require_like_for_like  # noqa: E402

BUDGET = 37654
SPACING = 2.8
COLLAR = 2.0
CANDIDATE = "E1_vfgr"
ARMS = ("E1_vfgr", "E2_raw_edge", "E3_bmr")
H33_ARM = "H33_as_is"
H33_PATH = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    if isinstance(value, np.floating):
        number = float(value)
        if not np.isfinite(number):
            raise ValueError("non-finite number in run card")
        return number
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def local_registry_index() -> tuple[dict, list[str]]:
    """Measured files only. Missing inventory rows stay missing; never repaired."""
    records = []
    seen = set()
    missing = []
    inventory = json.loads((ROOT / "research/upstream/registry_inventory.json").read_text())
    for record in inventory["rasters"]:
        path = ROOT / "data/registry_ext" / f"{record['sha256']}.tif"
        if not path.is_file():
            missing.append(record["sha256"])
            continue
        records.append(dict(record, cache_file=str(path)))
        seen.add(record["sha256"])
    extras = list((ROOT / "docs/downloads").glob("*.tif")) + list((ROOT / "data/scored_fleet").glob("*.tif"))
    witness = ROOT / "data/registry/dense-witness.tif"
    if witness.is_file():
        extras.append(witness)
    for path in extras:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        records.append({
            "sha256": digest,
            "bytes": path.stat().st_size,
            "blob": None,
            "cache_file": str(path),
            "sources": [f"GEMSDOE86-local:{path.relative_to(ROOT)}"],
            "repo_first": "GEMSDOE86-local",
        })
    return {"rasters": records, "complete_accessible_scan": not missing, "errors": []}, missing


def registry_measurement(array: np.ndarray, footprint: np.ndarray, *, dots: bool) -> dict:
    index, missing = local_registry_index()
    if not index["rasters"]:
        raise RuntimeError("no registry rasters available to measure")
    result = compare_array_to_registry(
        array.astype(np.float32), index, footprint,
        expected_grid=None,
    )
    rows = result.pop("rows")
    checked = [r for r in rows if "error" not in r]
    phase = two_phase_summary(rows, int(footprint.sum()), expected_rasters=len(index["rasters"]) + len(missing))
    rho_hits = [r for r in checked if r.get("spearman_full_footprint") is not None and r["spearman_full_footprint"] > RHO_LIMIT]
    informative = []
    allowed = footprint  # halo coverage is reported on the footprint; catalogue cells are not emission sites
    for row in checked:
        if row.get("representation") != "dot_field":
            continue
        if row["my_dots_within_3px_of_theirs"] <= OVERLAP_LIMIT:
            continue
        path = Path(row["file"])
        with rasterio.open(path) as src:
            support = np.nan_to_num(src.read(1).astype(np.float32)) > 0
        coverage = float(_near(support & footprint)[footprint].mean())
        row_info = {
            "submission": row.get("submission"),
            "repo": row.get("repo"),
            "overlap": row["my_dots_within_3px_of_theirs"],
            "halo_coverage": coverage,
            "their_dots": row.get("their_dots"),
            "informative": coverage <= OVERLAP_LIMIT,
        }
        if row_info["informative"]:
            informative.append(row_info)
    worst_rho = max((r["spearman_full_footprint"] for r in checked if r.get("spearman_full_footprint") is not None), default=None)
    dot_rows = [r for r in checked if r.get("representation") == "dot_field"]
    worst_dot = max((r["my_dots_within_3px_of_theirs"] for r in dot_rows), default=None)
    # A soft surface is positive on too many cells for a dot-overlap test.
    # Rank correlation is the surface gate. Overlap is a final-dot gate only.
    duplicate = bool(rho_hits or (dots and informative))
    return {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "mode": "final_dots" if dots else "surface",
        "rasters_measured": len(checked),
        "rasters_missing_from_pinned_inventory": len(missing),
        "registry_complete": not missing and int(result.get("missing_or_invalid", 1)) == 0,
        "worst_spearman_rho": worst_rho,
        "rho_firings_above_0.90": len(rho_hits),
        "worst_dot_field_overlap_3px": worst_dot,
        "informative_overlap_firings": informative if dots else [],
        "literal_reading": phase["literal_reading"],
        "like_for_like_reading": phase["like_for_like_reading"],
        "duplicate_stop": duplicate,
        "scope": "Pinned inventory files present in data/registry_ext plus local downloads, scored fleet, and the witness. Missing inventory rows are not a pass. Surface gate is Spearman only.",
    }


def emit(surface: np.ndarray, allowed: np.ndarray, known: np.ndarray, valid: np.ndarray, budget: int) -> np.ndarray:
    return static_ek_spacing_allocate(
        surface, allowed, known_faults=known, valid=valid,
        budget=budget, min_spacing_px=SPACING, candidate_cap=450_000,
    )


def main() -> None:
    # Imported and command-line entry points obey the literal stop before work.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    started = time.time()
    certificate = require_like_for_like()
    print("preflight", certificate["status"], flush=True)
    grid = G.load_grid(ROOT / "data/bridge")
    footprint = grid.footprint
    catalogue = grid.catalogue
    features = ROOT / "data/bridge/training_features.tif"
    pinned = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
    digest = hashlib.sha256(features.read_bytes()).hexdigest()
    if digest != pinned:
        raise SystemExit(f"training_features.tif hash mismatch: {digest}")
    mag = read_band(features, "tmi_hg")
    grav_slope = read_band(features, "iso_grav_anom_slope")
    gravity = read_band(features, "iso_grav_anom")
    depth = read_band(features, "depth_to_base_surf")
    print("bands", {name: [float(np.nanmin(a[footprint])), float(np.nanmax(a[footprint]))]
                    for name, a in {"tmi_hg": mag, "grav_slope": grav_slope, "grav": gravity, "depth": depth}.items()},
          flush=True)

    folds, quad = holdout.buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    hidden = folds[0]["hidden_all"]
    visible_for_canary = catalogue & ~hidden
    active = footprint & ~visible_for_canary
    rng = np.random.default_rng(86)
    sample_index = rng.choice(np.flatnonzero(active), size=min(400_000, int(active.sum())), replace=False)
    y = hidden.ravel()[sample_index]
    if y.sum() == 0 or y.sum() == y.size:
        raise RuntimeError("canary sample has one class")

    # Canary uses one globally hidden draw so a withheld strand is not visible.
    dist_hidden = ndi.distance_transform_edt(~visible_for_canary)
    train_canary = footprint & ~hidden
    canary_surfaces = {}
    canary_surfaces["E1_vfgr"], _ = corroborated_residual_surface(mag, grav_slope, dist_hidden, train_canary, footprint, subtract=True)
    canary_surfaces["E2_raw_edge"], _ = corroborated_residual_surface(mag, grav_slope, dist_hidden, train_canary, footprint, subtract=False)
    canary_surfaces["E3_bmr"], bmr_canary = basement_mass_balance_surface(gravity, depth, train_canary, footprint)
    canary = {}
    for name, surface in canary_surfaces.items():
        score = float(roc_auc_score(y, surface.ravel()[sample_index]))
        canary[name] = score
    print("canary", canary, "bmr_r2", bmr_canary["training_r2"], flush=True)
    if max(canary.values()) > 0.90:
        raise SystemExit(f"LEAKAGE CANARY FAIL {canary}")

    terms = {name: [] for name in (*ARMS, H33_ARM)}
    fit_receipts = []
    total_fp = int(footprint.sum())
    for fold in folds:
        region = fold["region"]
        visible = fold["visible"]
        train = footprint & (quad != fold["fold"])
        dist_vis = ndi.distance_transform_edt(~visible)
        allowed = region & footprint & (dist_vis > COLLAR) & ~visible
        budget = int(round(BUDGET * int((region & footprint).sum()) / total_fp))
        surfaces = {}
        surfaces["E1_vfgr"], e1_fit = corroborated_residual_surface(mag, grav_slope, dist_vis, train, footprint, subtract=True)
        surfaces["E2_raw_edge"], e2_fit = corroborated_residual_surface(mag, grav_slope, dist_vis, train, footprint, subtract=False)
        surfaces["E3_bmr"], e3_fit = basement_mass_balance_surface(gravity, depth, train, footprint)
        fit_receipts.append({"fold": fold["name"], "budget": budget, "E1": e1_fit, "E2": e2_fit, "E3": e3_fit})
        for arm in ARMS:
            dots = emit(surfaces[arm], allowed, visible, footprint, budget)
            result, block_terms = EH.evaluate(dots.astype(np.float32), fold, footprint)
            terms[arm].append(block_terms)
            print(fold["name"], arm, round(result["dti"], 4), result["n_emitted"], flush=True)
        if not H33_PATH.is_file():
            raise FileNotFoundError(H33_PATH)
        with rasterio.open(H33_PATH) as src:
            if (src.shape, src.crs, src.transform) != (grid.shape, grid.crs, grid.transform):
                raise ValueError("H33 raster grid does not match the sample grid")
            h33 = src.read(1).astype(np.float32)
        h33 = np.where(np.isfinite(h33), h33, 0.0)
        h33 = np.clip(h33, 0.0, 1.0)
        result, block_terms = EH.evaluate(h33, fold, footprint)
        terms[H33_ARM].append(block_terms)
        print(fold["name"], H33_ARM, round(result["dti"], 4), result["n_emitted"], flush=True)

    pooled = {name: np.sum(np.stack(parts), axis=0) for name, parts in terms.items()}
    summary = EH.pooled_summary(pooled, draws=1000, seed=520810, candidate=CANDIDATE)
    print(json.dumps(_jsonable(summary["scores"])), flush=True)

    # Deployment surface: full-footprint fit. This is not the fold-safe score.
    dist_full = ndi.distance_transform_edt(~catalogue)
    final_surfaces = {}
    final_surfaces["E1_vfgr"], final_e1 = corroborated_residual_surface(
        mag, grav_slope, dist_full, footprint, footprint, subtract=True)
    surface_check = registry_measurement(final_surfaces["E1_vfgr"], footprint, dots=False)
    print("surface", surface_check["worst_spearman_rho"], surface_check["rho_firings_above_0.90"],
          "complete", surface_check["registry_complete"], flush=True)
    if surface_check["duplicate_stop"]:
        card = _card(started, certificate, canary, summary, fit_receipts, final_e1, surface_check,
                     None, None, None, "negative", "duplicate surface; TIFF not written")
        _write_card(card)
        raise SystemExit("DUPLICATE SURFACE STOP")

    allowed_final = footprint & (dist_full > COLLAR) & ~catalogue
    dots = emit(final_surfaces["E1_vfgr"], allowed_final, catalogue, footprint, BUDGET)
    prediction = np.where(dots, np.float32(1.0), np.float32(0.0))
    if not np.isfinite(prediction).all() or prediction.min() < 0 or prediction.max() > 1:
        raise RuntimeError("prediction left [0, 1]")
    if ((prediction > 0) & (~footprint | catalogue)).any():
        raise RuntimeError("prediction lands outside the footprint or on the catalogue")
    dot_check = registry_measurement(prediction, footprint, dots=True)
    print("dots", int(dots.sum()), "overlap", dot_check["worst_dot_field_overlap_3px"],
          "informative", len(dot_check["informative_overlap_firings"]), flush=True)
    if dot_check["duplicate_stop"]:
        card = _card(started, certificate, canary, summary, fit_receipts, final_e1, surface_check,
                     dot_check, None, None, "negative", "duplicate final dots; TIFF not written")
        _write_card(card)
        raise SystemExit("DUPLICATE DOT STOP")

    e1 = summary["scores"][CANDIDATE]
    paired = summary["paired_differences"]
    beats = all(paired[name]["ci95"][0] > 0 for name in ("E2_raw_edge", "E3_bmr", H33_ARM))
    unique_measured = not surface_check["duplicate_stop"] and not dot_check["duplicate_stop"]
    complete = surface_check["registry_complete"] and dot_check["registry_complete"]
    scientific_promote = bool(beats and max(canary.values()) <= 0.90 and unique_measured and complete)
    verdict = "promote" if scientific_promote else "negative"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short = hashlib.sha256(np.ascontiguousarray(prediction).tobytes()).hexdigest()[:8]
    name = f"gems86-h86l-vfgr-{int(dots.sum())}dots-{stamp}-{short}-zeros"
    note = (
        f"H86L-VFGR visible-edge residual {int(dots.sum())}d; "
        f"HOLDOUT-DTI {e1['dti']:.4f}; {verdict}; DO NOT SUBMIT"
    )[:140]
    out = ROOT / "docs/downloads" / f"{name}.tif"
    receipt = submission_writer.write_submission(
        out, prediction, ROOT / "data/bridge/sample_submission.tif", footprint,
        note=note, name=name[:140], catalogue=catalogue,
        metadata={"lane": "H86L-VFGR", "verdict": verdict, "safe_to_submit": False},
    )
    card = _card(started, certificate, canary, summary, fit_receipts, final_e1, surface_check,
                 dot_check, receipt, out, verdict, note)
    _write_card(card)
    print(json.dumps({k: card[k] for k in ("verdict", "submission_name", "note", "raster_sha256", "safe_to_submit")}))


def _card(started, certificate, canary, summary, fits, final_fit, surface_check, dot_check,
          receipt, out, verdict, note) -> dict:
    e1 = summary["scores"][CANDIDATE]
    return {
        "schema": "gems86.lane_run_card.v1",
        "lane_id": "H86L-VFGR",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "A fault missing from the visible catalogue keeps a magnetic and gravity edge after the expected edge of the visible faults is subtracted.",
        "mechanism": "Training-only Gaussian expected-edge subtraction (sigma 2 px) on tmi_hg and iso_grav_anom_slope, geometric-mean residual, structure-tensor coherence, 2.8 px spacing, 37654 dots, 2 px collar.",
        "named_non_fault_mimic": "Lithologic contact or flight-line residual that is linear and off the mapped catalogue.",
        "preregistration": "research/H86L_VFGR_PREREGISTRATION.md",
        "shared_feature_cache_used": False,
        "native_feature_sha256": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
        "cache_note": "Template cached feature stack is absent. Native hash-pinned bands were read. This is not a restored shared cache.",
        "preflight_status": certificate["status"],
        "literal_overlap_blocker": bool(certificate["universal_overlap_blocker"]),
        "leakage_canary_auc": canary,
        "canary_pass": bool(max(canary.values()) <= 0.90),
        "fold_fits": fits,
        "deployment_fit": final_fit,
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "design": "buffered whole components; one seed; LOQO quadrant complement fit; physical-block interval",
            "withheld_positive_pixels": e1["withheld_positive_pixels"],
            "candidate": {"dti": e1["dti"], "ci95": e1["ci95"], "arm": CANDIDATE},
            "scores": summary["scores"],
            "paired_differences": summary["paired_differences"],
            "bootstrap": summary["bootstrap"],
        },
        "holdout_dti_normalized": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "dti": e1["dti"],
            "ci95": e1["ci95"],
            "n_truth": e1["withheld_positive_pixels"],
            "design": "buffered whole components; seed 20; hide_frac 0.20; buffer 3 px",
        },
        "correlation_overlap_vs_registry": {"surface": surface_check, "final_dots": dot_check},
        "raster_sha256": None if receipt is None else receipt["sha256"],
        "submission_file": None if out is None else str(out.relative_to(ROOT)),
        "validator_output": None if receipt is None else receipt["validator"],
        "submission_name": None if out is None else out.stem,
        "note": note,
        "note_chars": len(note),
        "verdict": verdict,
        "decision": "DO NOT SUBMIT",
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "experiments_run": 3,
        "organizer_confirmed_score": None,
        "ok_to_download_for_audit": receipt is not None and bool(receipt["validator"]["all_checks_passed"]),
        "ok_to_submit_to_portal": False,
        "runtime_s": time.time() - started,
    }


def _write_card(card: dict) -> None:
    path = ROOT / "docs/evidence/h86l-vfgr-run-card.json"
    path.write_text(json.dumps(_jsonable(card), indent=2) + "\n")
    print("wrote", path, flush=True)


if __name__ == "__main__":
    main()
