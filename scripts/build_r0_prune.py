#!/usr/bin/env python3
"""Rebuild R0 exactly, then run the session's single PRUNE<=3/refill experiment.

No DrivenData endpoint is contacted. Every input is SHA-256 pinned. The parent
must reproduce byte-for-byte before a candidate can be written. Candidate TIFFs
are local-only because this is a public repository and the data-use terms have
not been cleared; receipts and code are safe to commit.

The refill ranking is the deterministic FIFO breadth-first visitation order of
the original H19-5 -> d2.8 recipe (GEMSDOE28 commit 94b027b, gems27.thinning).
It is a spatial/content-blind order, not a geological probability. The fixed
count is explicit in the session brief; the resulting loss of 2.8 px spacing is
reported as a confounder, never hidden.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from collections import deque
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
from gems57 import evaluate_holdout, metric  # noqa: E402
from gems57.grid import load_grid  # noqa: E402
from gems57.holdout import buffered_component_draw  # noqa: E402

SESSION_DATE = "20261023"
SEED = 20261023
PARENT = "h33-h33-2-b2"
AXIS = "PRUNE"
VALUE = "3"
PREDICTED_CHANGE = "-0.004 MODEL"
PREDICTED_DELTA = -0.004

PATHS = {
    "sample": ROOT / "data/bridge/sample_submission.tif",
    "catalogue": ROOT / "data/bridge/existing_faults.tif",
    "parent": ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "base": ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
    "h19": ROOT / "data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
    "d28": ROOT / "data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "sgmc": ROOT / "data/external/derived_sgmc_faults_100m_u8.tif",
}
PINS = {
    "sample": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "catalogue": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "parent": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "base": "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
    "h19": "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
    "d28": "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8",
    "sgmc": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
}
LEDGER_FIELDS = [
    "site", "name", "score", "encoding", "n_dots", "sha8", "parent", "receipt",
    "id", "axis", "value", "pct_changed", "sha256", "status", "predicted_change",
    "receipt_score", "date", "evidence_class", "source_url",
]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_inputs() -> dict:
    receipt = {}
    for name, path in PATHS.items():
        if not path.is_file():
            raise FileNotFoundError(f"pinned input {name} is missing: {path}")
        digest = sha256(path)
        if digest != PINS[name]:
            raise ValueError(f"pinned input {name} hash mismatch: {digest} != {PINS[name]}")
        receipt[name] = {
            "path": str(path.relative_to(ROOT)), "sha256": digest,
            "bytes": path.stat().st_size, "verified": True,
            "organizer_authenticated": False,
        }
    pin_path = ROOT / "research/template_pin.json"
    shared = json.loads(pin_path.read_text())
    for rel, expected in shared["files"].items():
        path = ROOT / rel
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"shared-tool pin mismatch: {rel}")
    return {"files": receipt, "shared_template_pins_verified": True,
            "pin_file": "research/template_pin.json"}


def read_array(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(1)


def read_binary(path: Path, footprint: np.ndarray) -> np.ndarray:
    arr = read_array(path)
    return footprint & np.isfinite(arr) & (arr > 0.5)


def reconstruct_r0(base: np.ndarray, catalogue: np.ndarray) -> np.ndarray:
    """Archived H33-2-B2: 40,199-dot solo-d2.8 base, strict d_cat>2."""
    return np.asarray(base, bool) & (ndi.distance_transform_edt(~catalogue) > 2.0)


def original_visit_rank(mask: np.ndarray) -> np.ndarray:
    """Recover the original dot_thin FIFO-BFS visitation order as integer ranks.

    This is the ranking reconstruction permitted by the brief. It mirrors only
    traversal, not the emission suppression rule. Source: GEMSDOE28 commit
    94b027bed628422b7b39b485cb918a3fc15e5364, src/gems27/thinning.py.
    """
    mask = np.asarray(mask, bool)
    height, width = mask.shape
    pad = 4  # ceil(2.8)+1 in the original d2.8 implementation
    padded_width, padded_height = width + 2 * pad, height + 2 * pad
    padded = np.zeros((padded_height, padded_width), bool)
    padded[pad:pad + height, pad:pad + width] = mask
    flat = bytearray(padded.tobytes())
    visited = bytearray(padded_height * padded_width)
    neighbours = (-padded_width - 1, -padded_width, -padded_width + 1, -1, 1,
                  padded_width - 1, padded_width, padded_width + 1)
    components, _ = ndi.label(padded, structure=np.ones((3, 3), int))
    component_flat = components.ravel()
    order = np.flatnonzero(component_flat)
    _, first = np.unique(component_flat[order], return_index=True)
    rank = np.full(padded_height * padded_width, -1, np.int32)
    visited_count = 0
    for seed in order[np.sort(first)].tolist():
        if visited[seed]:
            continue
        visited[seed] = 1
        queue = deque((seed,))
        while queue:
            current = queue.popleft()
            rank[current] = visited_count
            visited_count += 1
            for offset in neighbours:
                neighbour = current + offset
                if flat[neighbour] and not visited[neighbour]:
                    visited[neighbour] = 1
                    queue.append(neighbour)
    return rank.reshape(padded_height, padded_width)[pad:pad + height, pad:pad + width]


def build_prune_refill(r0: np.ndarray, h19: np.ndarray, catalogue: np.ndarray,
                       footprint: np.ndarray, buffer_px: float = 3.0) -> tuple[np.ndarray, dict]:
    """Remove d_cat<=buffer and refill to R0's count from the same H19-5 field."""
    r0 = np.asarray(r0, bool)
    h19 = np.asarray(h19, bool)
    distance = ndi.distance_transform_edt(~catalogue)
    retained = r0 & (distance > buffer_px)
    removed = r0 & ~retained
    n_refill = int(removed.sum())
    rank = original_visit_rank(h19)
    eligible = h19 & footprint & ~catalogue & (distance > buffer_px) & ~retained
    ey, ex = np.nonzero(eligible)
    if len(ey) < n_refill:
        raise ValueError(f"only {len(ey)} eligible H19-5 cells for {n_refill} refills")
    # Stable row-major tie break; ranks are unique on this connected-component traversal.
    order = np.argsort(rank[ey, ex], kind="stable")[:n_refill]
    added = np.zeros_like(r0)
    added[ey[order], ex[order]] = True
    candidate = retained | added
    if int(candidate.sum()) != int(r0.sum()):
        raise AssertionError("fixed-count refill failed")
    if (candidate & catalogue).any() or (candidate & (distance <= buffer_px)).any():
        raise AssertionError("catalogue/collar exclusion failed")
    changed = int((r0 & ~candidate).sum() + (candidate & ~r0).sum())
    stats = {
        "parent_dots": int(r0.sum()), "candidate_dots": int(candidate.sum()),
        "removed_dots": int((r0 & ~candidate).sum()),
        "added_dots": int((candidate & ~r0).sum()),
        "retained_dots": int((r0 & candidate).sum()),
        "changed_grid_cells": changed,
        "pct_parent_dots_removed": 100.0 * int((r0 & ~candidate).sum()) / int(r0.sum()),
        "pct_parent_dot_count_added": 100.0 * int((candidate & ~r0).sum()) / int(r0.sum()),
        "pct_changed_vs_parent_dots": 100.0 * changed / int(r0.sum()),
        "refill_rule": "lowest recovered FIFO-BFS visitation rank in pinned H19-5; d_cat>3; fixed count",
        "refill_is_geological_probability": False,
        "parent_min_catalogue_distance_px": float(distance[r0].min()),
        "candidate_min_catalogue_distance_px": float(distance[candidate].min()),
        "parent_dots_le_1px": int((r0 & (distance <= 1)).sum()),
        "parent_dots_le_2px": int((r0 & (distance <= 2)).sum()),
        "parent_dots_le_3px": int((r0 & (distance <= 3)).sum()),
        "candidate_dots_le_1px": int((candidate & (distance <= 1)).sum()),
        "candidate_dots_le_2px": int((candidate & (distance <= 2)).sum()),
        "candidate_dots_le_3px": int((candidate & (distance <= 3)).sum()),
    }
    return candidate, stats


def profile_from_catalogue() -> dict:
    with rasterio.open(PATHS["catalogue"]) as src:
        profile = src.profile.copy()
    profile.update(driver="GTiff", dtype="float32", count=1, compress="deflate",
                   predictor=3, zlevel=9, tiled=True, blockxsize=256, blockysize=256)
    return profile


def serialize(mask: np.ndarray, footprint: np.ndarray, path: Path, mode: str,
              profile: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out_profile = profile.copy()
    if mode == "nan":
        out_profile["nodata"] = np.nan
        arr = np.where(footprint, mask, np.nan).astype(np.float32)
    elif mode == "zeros":
        out_profile["nodata"] = None
        arr = np.where(footprint, mask, 0.0).astype(np.float32)
    else:
        raise ValueError(mode)
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(arr, 1)


def validate_raster(path: Path, expected_mask: np.ndarray, footprint: np.ndarray,
                    catalogue: np.ndarray, mode: str) -> dict:
    """Re-read delivered bytes and check every hard format/exclusion condition."""
    with rasterio.open(PATHS["sample"]) as sample, rasterio.open(path) as src:
        arr = src.read(1)
        checks = {
            "one_band": src.count == 1,
            "float32": src.dtypes == ("float32",),
            "shape_matches_sample": src.shape == sample.shape == expected_mask.shape,
            "crs_matches_sample": src.crs == sample.crs,
            "transform_matches_sample": src.transform == sample.transform,
            "bounds_match_sample": src.bounds == sample.bounds,
            "finite_inside_footprint": bool(np.isfinite(arr[footprint]).all()),
            "values_in_0_1_inside": bool(((arr[footprint] >= 0) & (arr[footprint] <= 1)).all()),
            "binary_unit_mass": bool(np.array_equal(arr[footprint] > 0.5, expected_mask[footprint])),
            "zero_catalogue_mass": int(((arr > 0) & catalogue).sum()) == 0,
            "no_positive_outside_footprint": int(((arr > 0) & ~footprint).sum()) == 0,
        }
        if mode == "nan":
            checks["nan_outside_footprint"] = bool(np.isnan(arr[~footprint]).all())
            checks["nodata_is_nan"] = src.nodata is not None and bool(np.isnan(src.nodata))
        else:
            checks["zero_outside_footprint"] = bool(np.all(arr[~footprint] == 0))
            checks["all_grid_values_in_0_1"] = bool(np.isfinite(arr).all() and ((arr >= 0) & (arr <= 1)).all())
        result = {
            "file": str(path.relative_to(ROOT)), "mode": mode, "sha256": sha256(path),
            "bytes": path.stat().st_size, "crs": str(src.crs), "shape": list(src.shape),
            "transform": list(src.transform)[:6], "dtype": src.dtypes[0],
            "n_dots": int((arr[footprint] > 0.5).sum()),
            "on_catalogue_dots": int(((arr > 0.5) & catalogue).sum()),
            "re_read_from_disk": True, "checks": checks, "all_checks_passed": all(checks.values()),
        }
    if not result["all_checks_passed"]:
        raise ValueError(f"raster validation failed for {path}: {[k for k, v in checks.items() if not v]}")
    return result


def nearest_neighbour_stats(mask: np.ndarray) -> dict:
    points = np.argwhere(mask)
    distances = cKDTree(points).query(points, k=2)[0][:, 1]
    return {"mean_px": float(distances.mean()), "median_px": float(np.median(distances)),
            "p10_px": float(np.percentile(distances, 10)),
            "fraction_below_2_8px": float((distances < 2.8).mean())}


def spacing_preserving_refill_count(r0: np.ndarray, h19: np.ndarray,
                                    catalogue: np.ndarray, buffer_px: float = 3.0,
                                    min_dist: float = 2.8) -> int:
    """Measure, rather than assume, how many refills preserve the parent's spacing."""
    distance = ndi.distance_transform_edt(~catalogue)
    retained = r0 & (distance > buffer_px)
    needed = int(r0.sum() - retained.sum())
    rank = original_visit_rank(h19)
    eligible = h19 & (distance > buffer_px) & ~retained
    ey, ex = np.nonzero(eligible)
    order = np.argsort(rank[ey, ex], kind="stable")
    ey, ex = ey[order], ex[order]
    blocked = ndi.distance_transform_edt(~retained) < min_dist
    radius = int(np.ceil(min_dist))
    dy, dx = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    offsets = np.argwhere((dy * dy + dx * dx) < min_dist * min_dist) - radius
    count = 0
    for row, col in zip(ey, ex):
        if blocked[row, col]:
            continue
        count += 1
        if count >= needed:
            break
        nr, nc = row + offsets[:, 0], col + offsets[:, 1]
        valid = (nr >= 0) & (nr < r0.shape[0]) & (nc >= 0) & (nc < r0.shape[1])
        blocked[nr[valid], nc[valid]] = True
    return count


def leakage_canaries(grid, folds, h19: np.ndarray) -> dict:
    rows = []
    for fold in folds:
        active = grid.footprint & fold["region"] & ~fold["masked_known"]
        truth = active & fold["truth"]
        distance_visible = ndi.distance_transform_edt(~fold["visible"])
        for feature, surface in (("h19_5_binary", h19),
                                 ("negative_distance_to_visible_catalogue", -distance_visible)):
            auc = float(roc_auc_score(truth[active], surface[active]))
            rows.append({"fold": fold["name"], "feature": feature, "auc": auc,
                         "withheld_positives": int(truth.sum())})
    maximum = max(row["auc"] for row in rows)
    return {"status": "PASS" if maximum <= 0.90 else "STOP_INVESTIGATE",
            "threshold": 0.90, "max_auc": maximum, "rows": rows,
            "note": "Single-feature diagnostics only; catalogue-derived distance is not an independent physical feature."}


def proxy_and_sgmc(candidate: np.ndarray, r0: np.ndarray, d28: np.ndarray, grid, folds,
                   h19: np.ndarray) -> tuple[dict, dict]:
    terms = {"r0": [], "prune3": []}
    fold_counts = []
    for fold in folds:
        # Every catalogue-derived collar is rebuilt from this fold's visible
        # catalogue only. Evaluating the final full-catalogue artifact directly
        # would trivially exclude the hidden truth and is not a recovery test.
        visible = fold["visible"]
        distance_visible = ndi.distance_transform_edt(~visible)
        r0_fold = d28 & (distance_visible > 2.0)
        candidate_fold, fold_diff = build_prune_refill(
            r0_fold, h19, visible, grid.footprint, 3.0)
        fold_counts.append({"fold": fold["name"], "r0_dots": int(r0_fold.sum()),
                            "candidate_dots": int(candidate_fold.sum()),
                            "removed": fold_diff["removed_dots"], "added": fold_diff["added_dots"]})
        for name, mask in (("r0", r0_fold), ("prune3", candidate_fold)):
            _, block_terms = evaluate_holdout.evaluate(
                mask.astype(np.float32), fold, grid.footprint, block_side=200,
                origin=(0, 0), global_shape=grid.shape)
            terms[name].append(block_terms)
    pooled = {name: np.sum(np.stack(parts), axis=0) for name, parts in terms.items()}
    proxy = evaluate_holdout.pooled_summary(pooled, draws=1000, seed=SEED, candidate="prune3")
    proxy["design"] = "fold-fair buffered whole-component catalogue hide-and-recover; seed 20; 3 px context buffer; collars rebuilt from visible faults only"
    proxy["fold_fair_counts"] = fold_counts
    proxy["evidence_class"] = "PROXY"
    proxy["caveat"] = "The historical H19-5 surface is fixed, but all catalogue-distance collars are fold-fair. This is a diagnostic, never a live-score gate."
    with rasterio.open(PATHS["sgmc"]) as src:
        sgmc = src.read(1) > 0
    off_truth = sgmc & grid.footprint & ~grid.catalogue & (ndi.distance_transform_edt(~grid.catalogue) > 3.0)
    scores = {}
    for name, mask in (("r0", r0), ("prune3", candidate)):
        result = metric.dti_binary(mask, off_truth, valid=grid.footprint, known=grid.catalogue)
        scores[name] = {key: result[key] for key in ("dti", "tp", "fp", "fn", "n_truth", "n_emitted")}
    scores["delta_prune3_minus_r0"] = scores["prune3"]["dti"] - scores["r0"]["dti"]
    control = {"evidence_class": "PROXY", "instrument": "official-kernel DTI vs SGMC off-catalogue control (Euclidean d_cat>3 px)",
               "scores": scores, "note": "SGMC is an independent-map control, not hidden competition truth."}
    return proxy, control


def encoding_for_name(name: str) -> str:
    low = name.lower()
    if "allfinite" in low:
        return "allfinite"
    if "nan" in low:
        return "nan"
    if "zero" in low:
        return "zeros"
    return "unknown"


def seed_or_read_ledger() -> tuple[list[dict], bool]:
    path = ROOT / "ledger/submissions.csv"
    if path.exists():
        with path.open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream)), False
    grouped = {}
    with (ROOT / "registry/prior_scores.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            name = row["submission"].strip()
            if not name:
                continue
            key = (name, row["score"])
            if key in grouped:
                grouped[key]["site"] += "|" + row["site"]
                continue
            grouped[key] = {field: "" for field in LEDGER_FIELDS} | {
                "site": row["site"], "name": name, "score": row["score"],
                "encoding": encoding_for_name(name), "receipt": "N",
                "status": "HISTORICAL", "evidence_class": "CLAIM",
                "source_url": row["source_url"],
            }
    rows = list(grouped.values())
    for row in rows:
        if row["name"].startswith("h33-h33-2-b2-"):
            row.update(n_dots="37654", sha8=PINS["parent"][:8], parent="h27-4-r1-solo-d2-8",
                       axis="PRUNE", value="2", sha256=PINS["parent"])
        elif row["name"].startswith("h27-4-r1-solo-d2-8-"):
            row.update(n_dots="40199", sha8=PINS["base"][:8], parent="dotted-h19-5-d2-8",
                       axis="PRUNE", value="1", sha256=PINS["base"])
    return rows, True


def update_ledger(candidate_id: str, primary_sha: str, diff: dict) -> None:
    rows, seeded = seed_or_read_ledger()
    duplicates = [row for row in rows if row.get("sha256") == primary_sha]
    if duplicates:
        raise ValueError(f"candidate SHA-256 already in ledger: {primary_sha}")
    repeat = [row for row in rows if row.get("parent") == PARENT and
              row.get("axis") == AXIS and row.get("value") == VALUE and row.get("id") != candidate_id]
    if repeat:
        raise ValueError("repeated (parent, axis, value) with a different artifact")
    rows = [row for row in rows if row.get("id") != candidate_id]
    rows.append({field: "" for field in LEDGER_FIELDS} | {
        "site": "GEMSDOE86", "name": candidate_id, "encoding": "nan",
        "n_dots": str(diff["candidate_dots"]), "sha8": primary_sha[:8], "parent": PARENT,
        "receipt": "N", "id": candidate_id, "axis": AXIS, "value": VALUE,
        "pct_changed": f"{diff['pct_changed_vs_parent_dots']:.6f}", "sha256": primary_sha,
        "status": "BUILT", "predicted_change": PREDICTED_CHANGE, "evidence_class": "MODEL",
    })
    path = ROOT / "ledger/submissions.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=LEDGER_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    if seeded:
        print("Seeded ledger/submissions.csv from registry/prior_scores.csv; raw_paste.txt was absent.")


def git_receipt() -> dict:
    def run(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    return {"git_sha": run("rev-parse", "HEAD"),
            "tracked_tree_clean_at_build_start": not bool(run("status", "--porcelain", "--untracked-files=no")),
            "branch": run("branch", "--show-current")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true", help="validate existing release files without rebuilding")
    args = parser.parse_args()
    code = git_receipt()
    if code["branch"] != "arena/06524e4a-gemsdoe86":
        raise ValueError(f"wrong working branch: {code['branch']}")
    if not code["tracked_tree_clean_at_build_start"] and not args.validate_only:
        raise ValueError("commit the builder before running so the logged Git SHA identifies the code")
    inputs = verify_inputs()
    grid = load_grid(ROOT / "data/bridge")
    footprint, catalogue = grid.footprint, grid.catalogue
    parent = read_binary(PATHS["parent"], footprint)
    base = read_binary(PATHS["base"], footprint)
    h19 = read_binary(PATHS["h19"], footprint) & ~catalogue
    d28 = read_binary(PATHS["d28"], footprint)
    rebuilt = reconstruct_r0(base, catalogue)
    if not np.array_equal(rebuilt, parent):
        raise ValueError("R0 pixel mask does not reproduce; STOP (parent approximation is forbidden)")
    profile = profile_from_catalogue()
    work = ROOT / ".cache/r0-prune"
    rebuilt_path = work / "r0-rebuilt-zeros.tif"
    serialize(rebuilt, footprint, rebuilt_path, "zeros", profile)
    if sha256(rebuilt_path) != PINS["parent"]:
        raise ValueError("R0 SHA-256 does not reproduce; STOP (parent approximation is forbidden)")
    # This also certifies the recorded parent recipe's 44,090-dot d2.8 starting set.
    if int(d28.sum()) != 44090 or int(base.sum()) != 40199 or int(parent.sum()) != 37654:
        raise ValueError("R0 lineage counts do not match the archived recipe")
    candidate, diff = build_prune_refill(parent, h19, catalogue, footprint, 3.0)
    diff["nearest_neighbour_parent"] = nearest_neighbour_stats(parent)
    diff["nearest_neighbour_candidate"] = nearest_neighbour_stats(candidate)
    diff["spacing_preserving_refills_available"] = spacing_preserving_refill_count(parent, h19, catalogue)
    diff["spacing_confounder"] = "Fixed-count refill admits cells below the old 2.8 px separation; reported, not used as a gate."
    folds, _ = buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3)
    canary = leakage_canaries(grid, folds, h19)
    if canary["status"] != "PASS":
        stop_path = ROOT / "evidence/r0-prune3-canary-stop.json"
        stop_path.write_text(json.dumps(canary, indent=2) + "\n")
        raise ValueError(f"leakage canary >0.90; STOP and investigate: {canary['max_auc']}")
    proxy, sgmc = proxy_and_sgmc(candidate, parent, d28, grid, folds, h19)
    candidate_id = None
    if args.validate_only:
        ledger_rows, _ = seed_or_read_ledger()
        matches = [r for r in ledger_rows if r.get("parent") == PARENT and r.get("axis") == AXIS and r.get("value") == VALUE]
        if len(matches) != 1:
            raise ValueError("validate-only requires exactly one PRUNE3 ledger row")
        candidate_id = matches[0]["id"]
        primary_sha = matches[0]["sha256"]
    else:
        releases = ROOT / "releases"
        releases.mkdir(exist_ok=True)
        tmp_nan, tmp_zeros = releases / ".build-nan.tif", releases / ".build-zeros.tif"
        serialize(candidate, footprint, tmp_nan, "nan", profile)
        serialize(candidate, footprint, tmp_zeros, "zeros", profile)
        primary_sha = sha256(tmp_nan)
        candidate_id = f"{PARENT}-prune{VALUE}-{SESSION_DATE}-{primary_sha[:8]}"
        nan_path, zeros_path = releases / f"{candidate_id}.tif", releases / f"{candidate_id}-zeros.tif"
        os.replace(tmp_nan, nan_path)
        os.replace(tmp_zeros, zeros_path)
    nan_path = ROOT / "releases" / f"{candidate_id}.tif"
    zeros_path = ROOT / "releases" / f"{candidate_id}-zeros.tif"
    validations = {
        "nan": validate_raster(nan_path, candidate, footprint, catalogue, "nan"),
        "zeros": validate_raster(zeros_path, candidate, footprint, catalogue, "zeros"),
    }
    if validations["nan"]["sha256"] != primary_sha:
        raise ValueError("primary SHA changed after naming")
    # Exact-hash dedupe also covers all pinned historical artifacts, not only the seeded ledger.
    known_hashes = {e["sha256"] for manifest in (ROOT / "registry/data_manifest.json", ROOT / "research/h86d_extended_manifest.json")
                    for key, entries in json.loads(manifest.read_text()).items()
                    if isinstance(entries, list) for e in entries if isinstance(e, dict) and "sha256" in e}
    if primary_sha in known_hashes or validations["zeros"]["sha256"] in known_hashes:
        raise ValueError("candidate hash duplicates a pinned historical artifact")
    if not args.validate_only:
        update_ledger(candidate_id, primary_sha, diff)
    note = "R0 h33-h33-2-b2; PRUNE<=3px + BFS-ranked H19-5 refill, 37654 dots; predicted delta -0.004 MODEL; no receipt"
    if len(note) > 140:
        raise AssertionError("form note too long")
    r0_rebuild = {"base_dots": int(base.sum()), "removed_le_2px": int((base & ~rebuilt).sum()),
                  "rebuilt_dots": int(rebuilt.sum()), "pixel_mask_matches_parent": True,
                  "rebuilt_sha256": sha256(rebuilt_path), "expected_sha256": PINS["parent"],
                  "sha256_match": True, "recipe": "solo-d2.8 (40,199) & d_cat>2",
                  "d28_starting_dots": int(d28.sum())}
    run_card = {
        "schema_version": 1, "session_date": SESSION_DATE, "seed": SEED, **code,
        "status": "BUILT", "submission_ready": False, "submission_slots_used": 0,
        "parent": PARENT, "axis": AXIS, "value": VALUE, "candidate_id": candidate_id,
        "inputs": inputs, "r0_rebuild": r0_rebuild, "parent_diff": diff,
        "outputs": validations, "predicted_live_change": {
            "value": PREDICTED_DELTA, "evidence_class": "MODEL",
            "interpretation": "A live change smaller than 0.01 in absolute value is no evidence."},
        "hypothesis": "At fixed mass, H19-5 cells beyond 300 m from the catalogue are more efficient than R0 cells in the 200-300 m annulus.",
        "mechanism": "Replace the complete <=3 px catalogue collar with the next cells in the parent's deterministic H19-5 order, preserving mass and excluding catalogue pixels.",
        "non_fault_mimic": "Roads, pipelines, alluvial channels and cartographic generalization can make non-fault lineaments beside mapped traces.",
        "falsifier": "A same-account public-chunk receipt at least +0.01 above R0 would falsify the predicted small-negative direction; |delta|<0.01 is inconclusive.",
        "catalogue_hide_recover_proxy": proxy, "leakage_canary": canary, "sgmc_control": sgmc,
        "form_note": note, "form_note_characters": len(note),
        "evidence_labels": {"R0_live_0_2778": "CLAIM (no receipt)", "predicted_live_change": "MODEL",
                            "catalogue_hide_recover": "PROXY", "sgmc_control": "PROXY"},
        "data_use": "Candidate TIFFs are local-only ignored artifacts in a public repository; organizer data-use terms unchecked.",
        "source_urls": {
            "r0_recipe": "https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/scripts/run_h33_validation.py",
            "parent_ranking_recipe": "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/94b027bed628422b7b39b485cb918a3fc15e5364/src/gems27/thinning.py",
            "catalogue_scoring_clarification": "https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516",
            "official_rules": "https://docs.nlr.gov/docs/fy26osti/96647.pdf",
        },
    }
    evidence = ROOT / "evidence/r0-prune3-run-card.json"
    evidence.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n")
    mechanism = f"""# Mechanism card — {candidate_id}\n\n- **Hypothesis:** At fixed mass, H19-5 cells beyond 300 m from the catalogue are more efficient than R0 cells in the 200–300 m annulus.\n- **Mechanism:** Remove all {diff['removed_dots']:,} R0 dots at catalogue distance ≤3 px ({diff['pct_parent_dots_removed']:.4f}% of R0) and refill the same number from the pinned H19-5 field at >3 px, using the [original deterministic FIFO-BFS order](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/94b027bed628422b7b39b485cb918a3fc15e5364/src/gems27/thinning.py). Count stays {diff['candidate_dots']:,}; the symmetric difference is {diff['pct_changed_vs_parent_dots']:.4f}% of R0's count.\n- **Non-fault mimic:** Roads, pipelines, alluvial channels and cartographic generalization can create fault-like responses beside mapped traces. The refill order is spatial/content-blind, not a new geological probability.\n- **Predicted live change:** **−0.004 DTI (MODEL)**. The prior 2 px prune was beneficial, but [new-fault truth may occur within 300 m of known traces](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) and a dense fixed-count refill can add redundant false-positive mass.\n- **Falsifier:** A comparable public-chunk receipt ≥+0.01 versus R0 falsifies the predicted direction. A change with absolute value <0.01 is no evidence.\n- **Confounder:** Only {diff['spacing_preserving_refills_available']} refills could preserve 2.8 px spacing; the required {diff['removed_dots']:,}-cell refill reduces nearest-neighbour spacing (parent mean {diff['nearest_neighbour_parent']['mean_px']:.3f}px, candidate mean {diff['nearest_neighbour_candidate']['mean_px']:.3f}px). PRUNE and spacing are therefore not perfectly separable at fixed count.\n- **Evidence:** Catalogue hide/recover and SGMC results in `evidence/r0-prune3-run-card.json` are **PROXY**, never scores or gates. R0's 0.2778 remains **CLAIM** until a receipt is supplied.\n"""
    (ROOT / "evidence/r0-prune3-mechanism.md").write_text(mechanism)
    submit = f"""# Manual submission card — no automatic submission\n\n**Status: BUILT; not slot-approved.** TOP_PUBLIC, remaining quota and R0's submission receipt were not supplied. The human alone submits from one registered entity.\n\n- Candidate ID: `{candidate_id}`\n- Primary (NaN outside): `releases/{candidate_id}.tif`\n- SHA-256: `{validations['nan']['sha256']}`\n- Fallback (zeros outside): `releases/{candidate_id}-zeros.tif`\n- Fallback SHA-256: `{validations['zeros']['sha256']}`\n- Upload **only one file per slot**.\n- Submission name: `{candidate_id}`\n- Form note ({len(note)} chars): `{note}`\n- Predicted change: **−0.004 (MODEL)**, not a score.\n- Format receipt: `evidence/r0-prune3-run-card.json`; both files re-read from disk, all hard checks passed, 37,654 dots, zero catalogue mass.\n- TIFFs are local-only and gitignored because this public repository has unchecked competition data-use terms. Record the actual receipt score/date in `ledger/submissions.csv` after any human submission.\n"""
    (ROOT / "docs/SUBMIT.md").write_text(submit)
    print(json.dumps({"candidate_id": candidate_id, "sha256": primary_sha,
                      "dots": diff["candidate_dots"], "pct_changed": diff["pct_changed_vs_parent_dots"],
                      "predicted_change": PREDICTED_CHANGE,
                      "proxy_delta": proxy["paired_differences"]["r0"]["delta"],
                      "sgmc_delta": sgmc["scores"]["delta_prune3_minus_r0"],
                      "format": "PASS", "submission_ready": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
