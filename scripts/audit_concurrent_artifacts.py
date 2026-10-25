#!/usr/bin/env python3
"""Close the two concurrent H86F lanes' mutual final-dot audit gap.

This re-reads inherited TIFFs and delegates ALL rank/overlap arithmetic to the
unchanged shared comparator. It creates no predictions, .npy candidate, TIFF or
ZIP. Pairwise measurements are not full-registry or pre-placement clearance.
Also rechecks the H33 collar-pruning identity, without inferring a private score.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import grid  # noqa: E402
from gems57.uniqueness import compare_array_to_registry  # noqa: E402
from scripts.audit_release import inside, sha256, strict_json, verify_shared_pins, write_json  # noqa: E402


SUFFIXES = ("-gzzd-run-card.json", "-pcc-run-card.json")


def read_pinned(path: Path, expected_sha: str, reference) -> np.ndarray:
    if sha256(path) != expected_sha:
        raise ValueError(f"Input SHA drift: {path.name}")
    with rasterio.open(path) as src:
        if (src.count, src.shape, src.crs, src.transform) != (1, reference.shape, reference.crs, reference.transform):
            raise ValueError(f"Input grid drift: {path.name}")
        values = src.read(1)
    return values


def measure() -> dict:
    if not all(verify_shared_pins(ROOT).values()):
        raise ValueError("Shared tool SHA drift")
    reference = grid.load_grid(ROOT / "data/bridge")
    mapping = strict_json(ROOT / "registry/artifact_cards.json")["artifacts"]
    inventory = strict_json(ROOT / "docs/evidence/download-inventory.json")["artifacts"]
    by_stem = {Path(row["file"]).stem: row for row in inventory}
    selected = [row for row in mapping if row.get("card") and row["card"].endswith(SUFFIXES)]
    if len(selected) != 2:
        raise ValueError("Expected exactly the two archived H86F lanes")
    entries = [by_stem[row["stem"]] for row in selected]
    rows = []
    for own, other in ((entries[0], entries[1]), (entries[1], entries[0])):
        path = inside(ROOT, own["file"], directory="docs/downloads")
        prediction = read_pinned(path, own["sha256"], reference)
        prior = inside(ROOT, other["file"], directory="docs/downloads")
        # A list explicitly has NO complete-inventory certificate in the common
        # comparator. Its source_errors/negative clearance must stay visible.
        shared = compare_array_to_registry(prediction,
            [dict(repo="GEMSDOE86", submission=other["file"], file=str(prior), sha256=other["sha256"])],
            reference.footprint, file_sha256=own["sha256"],
            expected_grid=(reference.shape, reference.crs, reference.transform))
        rows.append(dict(candidate_file=own["file"], candidate_sha256=own["sha256"], shared_result=shared))

    forensic = strict_json(ROOT / "docs/evidence/h86f-h33-forensics.json")["h33_anatomy"]
    parent_path = ROOT / "data/scored_fleet" / forensic["parent_file"]
    h33_path = ROOT / "data/scored_fleet" / forensic["h33_file"]
    parent = (read_pinned(parent_path, forensic["parent_sha256"], reference) > 0) & reference.footprint
    h33 = (read_pinned(h33_path, forensic["h33_sha256"], reference) > 0) & reference.footprint
    distance = ndi.distance_transform_edt(~reference.catalogue)
    removed = parent & ~h33
    added = h33 & ~parent
    # This is an equality check of the stored operation, not a new prediction.
    exact = bool(np.array_equal(h33, parent & (distance > 2.0)))
    return dict(
        schema="gems86.concurrent-artifact-review.v1", evidence_class="REGISTRY-MEASUREMENT",
        measured_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), comparisons=rows,
        h33_lineage=dict(parent_sha256=forensic["parent_sha256"], h33_sha256=forensic["h33_sha256"],
            parent_dots=int(parent.sum()), h33_dots=int(h33.sum()), removed_dots=int(removed.sum()),
            added_dots=int(added.sum()), exact_parent_minus_2px_catalogue_collar=exact,
            removed_catalogue_distances_px=np.unique(distance[removed]).tolist(),
            owner_reported_parent="0.2708", owner_reported_h33="0.2778", organizer_confirmed=False,
            interpretation="Verified pixel operation only. Coverage-efficient pruning is a plausible mechanism, not a causal explanation of private leaderboard truth or a projected improvement."),
        registry_complete=False, preplacement_surfaces_measured=False,
        new_candidate_generated=False, experiments_run=0, submission_slots_used=0,
        submission_authorized=False, verdict="negative",
        scope="Two inherited final-dot directions plus a pinned H33 pixel-identity audit only. No full-registry clearance, no reconstructed pre-placement surfaces, no re-evaluated HOLDOUT-DTI and no new submission.",
    )


def main() -> int:
    result = measure()
    write_json(ROOT / "docs/evidence/concurrent-artifact-review-20261025.json", result)
    for row in result["comparisons"]:
        shared = row["shared_result"]
        print(row["candidate_file"], {key: shared[key] for key in (
            "worst_spearman_full_footprint", "worst_dot_overlap", "complete_accessible_scan", "unique")})
    print(result["h33_lineage"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
