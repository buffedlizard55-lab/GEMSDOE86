"""Audit a candidate with the unchanged shared registry comparator.

Usage: python scripts/check_h86e_registry.py CANDIDATE.npy OUT.json [--surface]

PA-86-01 diagnostics are NOT submission authorization. Missing/invalid registry
rows, invalid candidate values, empty/constant predictions and duplicates fail
closed. Both literal and representation-aware readings remain visible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import grid  # noqa: E402
from gems57.uniqueness import compare_array_to_registry, two_phase_summary  # noqa: E402

SCHEMA = "gems86.registry-candidate.v2"


def sha(p: Path) -> str:
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def build_index():
    inv = json.loads((ROOT / "research/upstream/registry_inventory.json").read_text())
    rasters, seen, missing = [], set(), []
    for r in inv["rasters"]:
        f = ROOT / "data/registry_ext" / f"{r['sha256']}.tif"
        if not f.exists():
            missing.append(r["sha256"])
            continue
        rasters.append(dict(r, cache_file=str(f)))
        seen.add(r["sha256"])
    extra = sorted((ROOT / "docs/downloads").glob("*.tif")) + sorted((ROOT / "data/scored_fleet").glob("*.tif"))
    for f in extra:
        d = sha(f)
        if d in seen:
            continue
        seen.add(d)
        rasters.append(dict(sha256=d, bytes=f.stat().st_size, blob=None, cache_file=str(f),
                            sources=[f"GEMSDOE86-local:{f.relative_to(ROOT)}"], repo_first="GEMSDOE86-local"))
    return dict(rasters=rasters, complete_accessible_scan=not missing, errors=[]), missing


def load_candidate(path, footprint, *, surface):
    """Reject, never repair, invalid bytes before comparing rank or support."""
    raw = np.load(path, allow_pickle=False)
    if raw.shape != footprint.shape or raw.dtype.kind not in "buif":
        raise ValueError("candidate shape/type mismatch")
    # Validate BEFORE float32 conversion: e.g. 1 + 1e-9 must not round into range.
    if not np.isfinite(raw).all() or (raw < 0).any() or (raw > 1).any():
        raise ValueError("candidate must already be finite in [0,1]")
    if (raw[~footprint] != 0).any():
        raise ValueError("candidate has nonzero values outside footprint")
    if not surface and not ((raw == 0) | (raw == 1)).all():
        raise ValueError("final dots must already be binary; no implicit thresholding")
    return raw.astype(np.float32)


def index_identity(index):
    """Bind the exact indexed content AND its labels, not local cache filenames."""
    records = sorted((r["sha256"], r["repo_first"], sorted(r["sources"]))
                     for r in index["rasters"])
    return hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()


def evaluate_candidate(arr, index, missing, g):
    """Pure orchestration; metric, rank, overlap and thresholds stay shared."""
    res = compare_array_to_registry(arr, index, g.footprint,
                                    expected_grid=(g.shape, g.crs, g.transform))
    rows = res.pop("rows")
    checked = [r for r in rows if "error" not in r]
    expected = len(index["rasters"]) + len(missing)
    phase = (two_phase_summary(rows, int(g.footprint.sum()), expected_rasters=expected)
             if checked else None)
    complete = bool(not missing and res["complete_accessible_scan"]
                    and len(checked) == expected and expected > 0)
    candidate_valid = bool(res["my_dots"] > 0 and res["candidate_rank_variation"])
    identity_clear = bool(res["byte_unique_among_checked"] and res["pixel_unique_among_checked"])
    keep = ("repo", "submission", "sha256", "their_dots", "my_dots_within_3px_of_theirs",
            "their_dots_within_3px_of_mine", "spearman_full_footprint", "jaccard_dot_sets")

    def compact(items):
        return [{k: r.get(k) for k in keep} | {"representation": r.get("representation")} for r in items[:15]]

    top = sorted(checked, key=lambda r: -r["my_dots_within_3px_of_theirs"])
    top_rho = sorted([r for r in checked if r.get("spearman_full_footprint") is not None],
                     key=lambda r: -r["spearman_full_footprint"])
    ready = complete and candidate_valid and identity_clear and phase is not None
    return dict(
        schema=SCHEMA, registry_index_sha256=index_identity(index),
        inventory_rasters_missing=missing, registry_rasters_expected=expected,
        registry_rasters_measured=len(checked), registry_complete_for_index=complete,
        scope="Pinned inventory plus local extras only; not all current projects or organizer submissions.",
        errors=[r for r in rows if "error" in r], shared_summary=res, two_phase=phase,
        comparison_rows=rows,
        top15_by_forward_overlap=compact(top), top15_by_spearman=compact(top_rho),
        surface_gate_pass=bool(ready and phase["literal_reading"]["rho_firings"] == 0),
        final_dots_gate_pass=bool(ready and not phase["like_for_like_reading"]["duplicate"]),
        literal_gate_pass=bool(ready and res["unique"]),
        submission_authorized=False,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--surface", action="store_true")
    args = parser.parse_args(argv)
    from scripts.audit_release import verify_shared_pins, write_json
    if not all(verify_shared_pins(ROOT).values()):
        raise ValueError("Shared tool SHA drift")
    g = grid.load_grid(ROOT / "data")
    source_sha = sha(args.candidate)
    arr = load_candidate(args.candidate, g.footprint, surface=args.surface)
    if sha(args.candidate) != source_sha:
        raise ValueError("Candidate changed while loading")
    index, missing = build_index()
    report = evaluate_candidate(arr, index, missing, g)
    report.update(candidate=str(args.candidate), candidate_source_sha256=source_sha,
                  mode="surface" if args.surface else "final_dots")
    # A surface pass must never be mistaken for completed final-dot clearance.
    report.pop("final_dots_gate_pass" if args.surface else "surface_gate_pass")
    write_json(args.output, report)
    gate = "surface_gate_pass" if args.surface else "final_dots_gate_pass"
    print(json.dumps({k: report[k] for k in (gate, "literal_gate_pass", "registry_complete_for_index")}, indent=2))
    return 0 if report[gate] else 1


if __name__ == "__main__":
    raise SystemExit(main())
