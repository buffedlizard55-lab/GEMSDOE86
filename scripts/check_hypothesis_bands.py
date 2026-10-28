#!/usr/bin/env python3
"""Fail closed when current research proposals mismatch native-band identities.

The TIFF's short names are identifiers, not proof of physics. The four physical
labels below encode prior pixel-level overrides. Historical prose and cards are
archives; this validator applies only to the explicitly reviewed current queue.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.gems86.io import BANDS  # noqa: E402

QUEUE = ROOT / "registry/review_hypotheses_20261027_0a171468.json"
PHYSICAL_OVERRIDES = {
    5: "gravity_gradient_magnitude_proxy",
    6: "radiometric_total_count",
    11: "southward_gravity_derivative",
    18: "eastward_gravity_derivative",
}
REQUIRED_TEXT = ("id", "title", "external_layers", "mechanism", "off_catalogue_rationale",
                 "named_non_fault_mimic", "falsifier_and_novelty", "expected_improvement_rank",
                 "implementation_cost", "availability")


def validate(document: dict) -> dict:
    if document.get("schema") != "gems86.review-hypotheses.v1":
        raise ValueError("Unexpected hypothesis queue schema")
    if document.get("status") != "NOT_RUN_NO_LANE_OR_PROTOCOL_CLEARANCE":
        raise ValueError("Review queue must remain unexecuted and unauthorized")
    rows = document.get("hypotheses")
    if not isinstance(rows, list) or not 3 <= len(rows) <= 5:
        raise ValueError("Review queue must contain three to five hypotheses")
    if [r.get("rank") for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("Hypothesis ranks must be unique and consecutive")
    ids = []
    for row in rows:
        for key in REQUIRED_TEXT:
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Missing hypothesis field: {key}")
        ids.append(row["id"])
        claims = row.get("native_bands")
        if not isinstance(claims, list) or not claims:
            raise ValueError("Each hypothesis needs explicit native band identities")
        indexes = []
        for claim in claims:
            index = claim.get("index")
            if type(index) is not int or index not in BANDS:
                raise ValueError(f"Unknown native band: {index!r}")
            if claim.get("name") != BANDS[index]:
                raise ValueError(f"Band {index} must be named {BANDS[index]}")
            expected = PHYSICAL_OVERRIDES.get(index, BANDS[index])
            if claim.get("physical_label") != expected:
                raise ValueError(f"Band {index} physical label must be {expected}")
            indexes.append(index)
        if len(indexes) != len(set(indexes)):
            raise ValueError("Duplicate native band in hypothesis")
        sources = row.get("sources")
        if not isinstance(sources, list) or not sources or any(
                not isinstance(url, str) or not url.startswith("https://") for url in sources):
            raise ValueError("Each hypothesis needs HTTPS source links")
    if len(ids) != len(set(ids)):
        raise ValueError("Hypothesis IDs must be unique")
    return document


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=QUEUE)
    args = parser.parse_args(argv)
    document = validate(json.loads(args.path.read_text(encoding="utf-8")))
    print(f"Validated {len(document['hypotheses'])} unrun hypotheses; not a protocol clearance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
