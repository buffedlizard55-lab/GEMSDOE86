#!/usr/bin/env python3
"""Run the preregistered RMRB-86 experiment and package one research candidate.

The script never uploads to DrivenData. It uses the unmodified shared evaluator
and writer. A binding duplicate or scientific gate produces a negative run card
and a conspicuously DO-NOT-SUBMIT filename; the locally valid artifact is still
retained because this project's highest-priority deliverable is a unique TIFF
whose submit/no-submit state is machine-readable and obvious.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor"), str(ROOT / "src")]
from gems57 import evaluate_holdout, grid, holdout, submission_writer, uniqueness  # noqa: E402
from gems86_rmrb import features, model  # noqa: E402

DATA = ROOT / "data"
EVIDENCE = ROOT / "docs" / "evidence"
DOWNLOADS = ROOT / "docs" / "downloads"
REGISTRY = ROOT / "registry"
BUDGET = 37_654
SEEDS = (20, 21)
ARTIFACT_STEM = "gems86-rmrb-kthu-rtp-37654-20261022-DO-NOT-SUBMIT"
SUBMISSION_NAME = "RMRB-86 K-Th-U residual boundary + RTP persistence; 37,654 dots"
NOTE = "RMRB-86: K~Th+U residual boundaries gated by persistent RTP edges; HGB, 37,654 dots, 2 px catalogue collar."
PUBLISHED_SHARED_V2_BEST = {
    "value": 0.04436352673339927,
    "source": "GEMSDOE84 evidence/run-card.json step_control",
    "source_commit": "e80df44eb4a915ee7d22eece33030eff76ee88eb",
    "local_snapshot": "research/upstream/gems84-run-card.json",
    "snapshot_sha256": "9092b6f017c93a36ab8120e35f3fdf27d2c9e8daee0e88926bc9e3435c5517fa",
    "comparable": False,
    "reason": "same evaluator formula/version but a different fold draw; matched controls below are binding",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False, sort_keys=True) + "\n")


def bbox(region, pad=4):
    rows, cols = np.nonzero(region)
    if not len(rows):
        raise ValueError("empty holdout region")
    return (slice(max(0, int(rows.min()) - pad), min(region.shape[0], int(rows.max()) + pad + 1)),
            slice(max(0, int(cols.min()) - pad), min(region.shape[1], int(cols.max()) + pad + 1)))


def checked_inputs():
    pins = {
        "training_features": (DATA / "training_features.tif", "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"),
        "sample_submission": (DATA / "sample_submission.tif", grid.SHA256_SAMPLE_SUBMISSION),
        "existing_faults": (DATA / "existing_faults.tif", grid.SHA256_EXISTING_FAULTS),
        "radiometrics": (DATA / "external/geodawn_rad_u8.tif", "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682"),
        "dense_registry_witness": (DATA / "registry/dense_17gemdoe.tif", "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be"),
        "h33_education": (DATA / "registry/h33_education.tif", "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    }
    result = {}
    for name, (path, expected) in pins.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = digest(path)
        if actual != expected:
            raise ValueError(f"{name} hash mismatch: {actual} != {expected}")
        result[name] = {"path": str(path.relative_to(ROOT)), "sha256": actual,
                        "bytes": path.stat().st_size, "organizer_authenticated": False}
    return result


def read_registry(path: Path, footprint):
    with rasterio.open(path) as src:
        if src.shape != footprint.shape or src.count != 1 or src.crs.to_epsg() != grid.EPSG or src.transform != grid.TRANSFORM:
            raise ValueError(f"registry grid mismatch: {path}")
        a = src.read(1).astype(np.float32)
    a = np.where(np.isfinite(a), a, 0.0).astype(np.float32)
    a[~footprint] = 0.0
    return a


def compare_representation(candidate, footprint, registry_arrays, phase):
    rows = []
    for name, (path, prior) in registry_arrays.items():
        rho = uniqueness.surface_rho(candidate, prior, footprint)
        overlap = uniqueness.dot_overlap(candidate, prior)
        decoded_equal = bool(np.array_equal(candidate, prior))
        rows.append({
            "phase": phase,
            "registry_name": name,
            "path": str(path.relative_to(ROOT)),
            "sha256": digest(path),
            "spearman_full_footprint": (None if not np.isfinite(rho["spearman_full_footprint"]) else rho["spearman_full_footprint"]),
            "spearman_on_dot_union": (None if not np.isfinite(rho["spearman_on_dot_union"]) else rho["spearman_on_dot_union"]),
            "candidate_dots_within_3px": overlap,
            "duplicate_by_rho": bool(np.isfinite(rho["spearman_full_footprint"]) and rho["spearman_full_footprint"] > 0.90),
            "duplicate_by_overlap": bool(overlap > 0.70),
            "decoded_equal": decoded_equal,
            "stop_required": bool((np.isfinite(rho["spearman_full_footprint"]) and rho["spearman_full_footprint"] > 0.90) or overlap > 0.70 or decoded_equal),
        })
    return rows


def run():
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    started = time.monotonic()
    prereg = json.loads((REGISTRY / "preregistration.json").read_text())
    inputs = checked_inputs()
    g = grid.load_grid(DATA)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)

    cache_path = DATA / "cache/rmrb86-20channel.f32"
    feature_receipt = features.build_cache(
        DATA / "training_features.tif",
        DATA / "external/geodawn_rad_u8.tif",
        g.footprint,
        cache_path,
        EVIDENCE / "feature-cache.json",
    )
    x = features.open_cache(cache_path, g.shape)

    folds, quads = [], {}
    for seed in SEEDS:
        draw, quad = holdout.buffered_component_draw(
            g, seed=seed, hide_frac=0.20, buffer_px=3, boundary_px=12
        )
        folds.extend(draw)
        quads[seed] = quad
    split = {
        "schema": "gems86.holdout-split.v1",
        "split_version": "buffered-whole-components-loqo-v2",
        "seeds": list(SEEDS),
        "folds": [f["receipt"] for f in folds],
        "evaluator_version": evaluate_holdout.VERSION,
        "evaluator_sha256": evaluate_holdout.implementation_hashes(),
    }
    dump(EVIDENCE / "holdout-split.json", split)

    canary_rows = model.leakage_canaries(x, features.NAMES, folds, g.footprint)
    max_canary = max(row["symmetric_auc"] for row in canary_rows)
    canaries = {
        "evidence_class": "HOLDOUT-FEATURE-CANARY",
        "threshold": 0.90,
        "max_symmetric_auc": max_canary,
        "passed": max_canary <= 0.90,
        "features": canary_rows,
        "caveat": "Feature-alone AUC is a leakage diagnostic, not DTI or an organizer score.",
    }
    dump(EVIDENCE / "leakage-canaries.json", canaries)
    if not canaries["passed"]:
        raise RuntimeError("leakage canary exceeded 0.90; stop")

    arms = {
        "core_control": features.BASE_COLUMNS,
        "raw_radiometric": features.RAW_RAD_COLUMNS,
        "rmrb_candidate": features.JOINT_COLUMNS,
    }
    terms = {name: None for name in arms}
    fold_records = []
    joint_col = features.NAMES.index("rmrb_joint")
    for fold in folds:
        seed = int(fold["receipt"]["seed"])
        fold_id = int(fold["fold"])
        train_domain = g.footprint & (quads[seed] != fold_id)
        sl = bbox(fold["region"])
        region = fold["region"][sl]
        pvalid = g.footprint[sl]
        visible_crop = fold["visible"][sl]
        allowed = model.catalogue_collar_allowed(pvalid, visible_crop, radius_px=2) & region
        local_index = np.flatnonzero(allowed.ravel())
        width = sl[1].stop - sl[1].start
        rr, cc = np.divmod(local_index, width)
        global_index = ((sl[0].start + rr) * g.width + (sl[1].start + cc)).astype(np.int64)
        tie = np.zeros(allowed.shape, np.float32)
        tie.ravel()[local_index] = np.asarray(x[joint_col, global_index])
        budget = max(1, round(BUDGET * int(region.sum()) / int(g.footprint.sum())))
        fold_record = {
            "seed": seed,
            "quadrant": fold["name"],
            "budget": int(budget),
            "withheld_positive_pixels": int(fold["truth"].sum()),
            "feature_context_buffer_px": 3,
            "boundary_buffer_px": 12,
            "catalogue_collar_px": 2,
            "arms": {},
        }
        fold_dict = {key: fold[key][sl] for key in ("region", "visible", "masked_known", "truth")}
        for arm_no, (arm, columns) in enumerate(arms.items()):
            estimator, fit_info = model.fit(
                x, g.footprint, fold["visible"], train_domain, columns,
                seed=model.SEED + seed * 20 + fold_id * 3 + arm_no,
            )
            probability = np.zeros(allowed.shape, np.float32)
            probability.ravel()[local_index] = model.probability(estimator, x, global_index, columns)
            dots, emission = model.spaced_dots(probability, allowed, budget, radius=2, tie=tie)
            score, by_block = evaluate_holdout.evaluate(
                dots.astype(np.float32), fold_dict, pvalid,
                origin=(sl[0].start, sl[1].start), global_shape=g.shape,
                block_side=200,
            )
            terms[arm] = by_block if terms[arm] is None else terms[arm] + by_block
            fold_record["arms"][arm] = {
                "training": fit_info,
                "emission": emission,
                "tpw": score["tpw"], "fpw": score["fpw"], "fnw": score["fnw"],
                "fold_dti_diagnostic": score["dti"],
            }
        fold_records.append(fold_record)

    holdout_result = evaluate_holdout.pooled_summary(
        terms, draws=1200, seed=86022, candidate="rmrb_candidate"
    )
    holdout_result.update({
        "split_version": split["split_version"],
        "folds": fold_records,
        "experiments_run": 2,
        "experiment_definition": {
            "experiment_1": "add raw K, Th and U to the ten-layer core control",
            "experiment_2": "add the preregistered K~Th+U residual/RTP boundary transforms",
        },
        "published_shared_v2_best_context": PUBLISHED_SHARED_V2_BEST,
    })
    dump(EVIDENCE / "holdout.json", holdout_result)

    score = holdout_result["scores"]["rmrb_candidate"]
    controls = ["core_control", "raw_radiometric"]
    matched_best = max(controls, key=lambda key: holdout_result["scores"][key]["dti"])
    matched_delta = holdout_result["paired_differences"][matched_best]
    scientific_pass = bool(
        score["dti"] > holdout_result["scores"][matched_best]["dti"]
        and matched_delta["ci95"][0] > 0
        and score["dti"] > PUBLISHED_SHARED_V2_BEST["value"]
    )

    # Train the unique production candidate using the full public catalogue.
    production_model, production_fit = model.fit(
        x, g.footprint, g.catalogue, g.footprint, features.JOINT_COLUMNS,
        seed=model.SEED + 1000,
    )
    allowed_full = model.catalogue_collar_allowed(g.footprint, g.catalogue, radius_px=2)
    production_index = np.flatnonzero(allowed_full.ravel())
    surface = np.zeros(g.shape, np.float32)
    surface.ravel()[production_index] = model.probability(
        production_model, x, production_index, features.JOINT_COLUMNS
    )
    surface[~allowed_full] = 0.0
    if not np.isfinite(surface).all() or (surface < 0).any() or (surface > 1).any():
        raise ValueError("production surface is invalid")

    registry_arrays = {
        "17GEMSDOE dense continuous witness": (
            DATA / "registry/dense_17gemdoe.tif",
            read_registry(DATA / "registry/dense_17gemdoe.tif", g.footprint),
        ),
        "GEMSDOE32 H33-2-B2": (
            DATA / "registry/h33_education.tif",
            read_registry(DATA / "registry/h33_education.tif", g.footprint),
        ),
    }
    surface_rows = compare_representation(surface, g.footprint, registry_arrays, "surface_before_placement")
    surface_stop = any(row["stop_required"] for row in surface_rows)

    # The duplicate stop is binding for promotion/slot use. Packaging continues
    # only to satisfy the requested auditable unique-TIFF deliverable; the name,
    # page and machine receipt all say DO NOT SUBMIT.
    tie_full = np.asarray(x[joint_col]).reshape(g.shape)
    dots, production_emission = model.spaced_dots(
        surface, allowed_full, BUDGET, radius=2, tie=tie_full
    )
    prediction = dots.astype(np.float32)
    final_rows = compare_representation(prediction, g.footprint, registry_arrays, "final_dots")
    duplicate_stop = surface_stop or any(row["stop_required"] for row in final_rows)
    uniqueness_receipt = {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "thresholds": {"spearman_rank_correlation": 0.90, "forward_dot_overlap_3px": 0.70},
        "surface_before_placement": surface_rows,
        "final_dots": final_rows,
        "stop_required": duplicate_stop,
        "literal_dense_witness_is_binding": True,
        "scope": "Two hash-pinned stopping witnesses checked. The inherited protocol stops at the first duplicate; full 1,143-raster decode was not continued.",
        "indexed_public_hashes": 1143,
        "complete_spatial_scan": False,
        "packaging_after_stop_reason": "Required research TIFF deliverable only; never approval for a slot.",
    }
    dump(EVIDENCE / "uniqueness.json", uniqueness_receipt)

    out = DOWNLOADS / f"{ARTIFACT_STEM}.tif"
    writer_receipt = submission_writer.write_submission(
        out, prediction, DATA / "sample_submission.tif", g.footprint,
        catalogue=g.catalogue, name=SUBMISSION_NAME, note=NOTE,
        metadata={
            "hypothesis": prereg["hypothesis"],
            "production_fit": production_fit,
            "production_emission": production_emission,
            "scientific_pass": scientific_pass,
            "duplicate_stop": duplicate_stop,
            "submission_authorized": False,
        },
    )
    indexed = json.loads((REGISTRY / "upstream_registry_index.json").read_text())
    indexed_hashes = {row["sha256"] for row in indexed["rasters"]}
    byte_unique = writer_receipt["sha256"] not in indexed_hashes
    decoded_unique_witnesses = not any(row["decoded_equal"] for row in final_rows)

    blockers = []
    if not scientific_pass:
        blockers.append("RMRB candidate did not clear every preregistered holdout promotion condition.")
    if duplicate_stop:
        blockers.append("Binding registry rule fired: >70% 3-pixel overlap with a hash-pinned dense prior.")
    if not byte_unique:
        blockers.append("Candidate file hash already exists in the indexed public raster inventory.")
    if not decoded_unique_witnesses:
        blockers.append("Candidate decoded pixels equal a stopping witness.")
    blockers.extend([
        "No authenticated organizer submission receipt or current weekly quota was available.",
        "Input hashes establish owner-mirror integrity, not independent organizer authentication.",
    ])
    promoted = bool(scientific_pass and not duplicate_stop and byte_unique and decoded_unique_witnesses)
    validator = writer_receipt["validator"]
    validation_checks = validator["checks"]
    run_card = {
        "hypothesis": prereg["hypothesis"],
        "mechanism": prereg["mechanism"],
        "non_fault_mimic": prereg["non_fault_mimic"],
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": evaluate_holdout.VERSION,
            "withheld_positives": score["withheld_positive_pixels"],
            "value": score["dti"],
            "ci95": score["ci95"],
            "matched_best_control": matched_best,
            "matched_control_value": holdout_result["scores"][matched_best]["dti"],
            "paired_delta": matched_delta,
            "scientific_promotion_gate_passed": scientific_pass,
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "surface": surface_rows,
            "final_dots": final_rows,
            "stop_required": duplicate_stop,
            "complete": False,
        },
        "raster_sha256": writer_receipt["sha256"],
        "validator_output": {
            "status": "PASS_LOCAL_FORMAT_ONLY" if validator["all_checks_passed"] else "FAIL",
            "no_nan_inside_footprint": validation_checks["in_footprint_all_finite"],
            "values_in_0_1": validation_checks["in_footprint_range_0_1"],
            "crs_shape_transform_match": bool(
                validation_checks[f"dimensions_{grid.HEIGHT}x{grid.WIDTH}"]
                and validation_checks[f"crs_epsg_{grid.EPSG}"]
                and validation_checks["transform_matches_sample_submission"]
            ),
            "single_band_float32": validation_checks["single_band"] and validation_checks["dtype_float32"],
            "positive_outside_footprint": 0 if validation_checks["outside_footprint_zero"] else None,
            "positive_on_catalogue": validator["on_catalogue_positive_pixels"],
            "all_checks_passed": validator["all_checks_passed"],
            "local_validation_is_not_organizer_acceptance": True,
        },
        "submission_name": SUBMISSION_NAME,
        "note": NOTE,
        "verdict": "promote" if promoted else "negative",
        "submission_ready": promoted,
        "safe_to_download": True,
        "safe_to_submit": promoted,
        "download_file": f"downloads/{out.name}",
        "zip_file": f"downloads/{out.with_suffix('.zip').name}",
        "byte_unique_among_1143_indexed_public_rasters": byte_unique,
        "decoded_unique_vs_stopping_witnesses": decoded_unique_witnesses,
        "experiments_run": 2,
        "runtime_seconds": time.monotonic() - started,
        "submission_slots_used": 0,
        "validator_scope": "automated local bytes/grid/range checks; not organizer acceptance",
        "blockers": blockers,
        "input_receipts": inputs,
    }
    dump(EVIDENCE / "rmrb86-run-card.json", run_card)
    dump(EVIDENCE / "experiment-summary.json", {
        "preregistration": prereg,
        "holdout": holdout_result,
        "canaries": canaries,
        "uniqueness": uniqueness_receipt,
        "writer_receipt": writer_receipt,
        "run_card": run_card,
    })
    return run_card


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, allow_nan=False))
