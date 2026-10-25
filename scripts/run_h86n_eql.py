#!/usr/bin/env python3
"""Fail-closed entrypoint for the preregistered H86N-EQL lane.

H86N-EQL is a pure multi-scale earthquake-lineation anisotropy hypothesis.
This entrypoint deliberately refuses to construct features until both the
repository preflight and a real hash-pinned shared cache are available. The
native prepared arrays are not accepted as a cache substitute, and the current
cache receipt does not prove visible-catalogue recomputation for a holdout.

When the gates become available, the implementation must continue to use the
unchanged gems57 holdout/evaluator/emit/submission_writer tools. This script
currently records the blocker and exits before model work; it does not create a
candidate TIFF or claim a holdout score.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]

from scripts.protocol_preflight import measure  # noqa: E402

CACHE_RECEIPT = ROOT / "docs/evidence/feature-cache.json"
RUN_CARD = ROOT / "docs/evidence/h86n-eql-run-card.json"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def shared_cache_status() -> dict:
    """Return a diagnostic; never treat prepared native arrays as the cache."""
    if not CACHE_RECEIPT.is_file():
        return {"available": False, "reason": "missing feature-cache.json receipt"}
    doc = json.loads(CACHE_RECEIPT.read_text(encoding="utf-8"))
    raw = doc.get("cache_file")
    if not isinstance(raw, str):
        return {"available": False, "reason": "cache receipt has no cache_file"}
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    try:
        candidate = candidate.resolve()
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return {"available": False, "reason": "cache path escapes this checkout"}
    if not candidate.is_file():
        return {
            "available": False,
            "reason": "hash-pinned shared cache bytes are missing",
            "cache_file": str(candidate.relative_to(ROOT)),
            "expected_bytes": doc.get("cache_bytes"),
            "expected_sha256": doc.get("cache_sha256"),
        }
    actual_bytes = candidate.stat().st_size
    actual_sha = sha256(candidate)
    if actual_bytes != doc.get("cache_bytes") or actual_sha != doc.get("cache_sha256"):
        return {"available": False, "reason": "shared cache bytes/hash do not match receipt",
                "cache_file": str(candidate.relative_to(ROOT)), "actual_bytes": actual_bytes,
                "actual_sha256": actual_sha}
    names = set(doc.get("names", []))
    required = {"ieq_n100a15", "deq_n100a15"}
    if not required.issubset(names):
        return {"available": False, "reason": "shared cache lacks the preregistered seismic channels",
                "missing_names": sorted(required - names)}
    if doc.get("catalogue_recomputed_per_fold") is not True:
        return {"available": False,
                "reason": "cache receipt does not certify visible-catalogue recomputation per fold"}
    return {"available": True, "cache_file": str(candidate.relative_to(ROOT)),
            "cache_bytes": actual_bytes, "cache_sha256": actual_sha,
            "names": sorted(names)}


def write_blocked_card(preflight: dict, cache: dict) -> dict:
    card = {
        "schema": "gems86.h86n-eql-run-card.v1",
        "lane": "H86N-EQL",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "A pure multi-scale earthquake-intensity lineation is a catalogue-missing active-fault proxy, while compact induced or volcanic swarms are the named non-fault mimic.",
        "mechanism": "Band 16 log-intensity Hessian ridge anisotropy at 2 px and 4 px with a separate Band 10 distance control; exact formula is frozen in research/H86N_EQL_PREREGISTRATION.md.",
        "named_non_fault_process": "Induced geothermal injection swarm or volcanic dike swarm with an elongated event cloud.",
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": "gems57-pooled-hide-v2",
            "status": "NOT_RUN_SHARED_CACHE_OR_PREFLIGHT_BLOCKER",
            "withheld_positive_pixels": None,
            "dti": None,
            "ci95": None,
            "caveat": "No feature construction or evaluator call occurred. A projection is not a score."
        },
        "leakage_canary": {
            "evidence_class": "LEAKAGE-CANARY",
            "status": "NOT_RUN_SHARED_CACHE_OR_PREFLIGHT_BLOCKER",
            "threshold": 0.90,
            "max_discriminative_auc": None,
            "any_leakage_flag": None
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "status": "NOT_RUN_NO_CANDIDATE_SURFACE",
            "surface": None,
            "final_dots": None,
            "thresholds": {"spearman_max": 0.90, "forward_overlap_3px_max": 0.70}
        },
        "raster_sha256": None,
        "validator_output": {
            "evidence_class": "LOCAL-FORMAT-VALIDATION",
            "status": "NOT_WRITTEN_NO_CANDIDATE",
            "all_checks_passed": False,
            "no_nan_inside_footprint": None,
            "values_in_0_1": None,
            "crs_shape_transform_match": None
        },
        "submission_name": None,
        "submission_note": None,
        "note_chars": None,
        "verdict": "negative",
        "decision": "DO NOT SUBMIT",
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "experiments_run": 0,
        "new_candidate_generated": False,
        "preflight": {
            "universal_overlap_blocker": preflight.get("universal_overlap_blocker"),
            "status": preflight.get("status"),
            "witness_sha256": preflight.get("witness_sha256")
        },
        "shared_cache": cache,
        "decision_reason": "No H86N experiment is authorized until the actual hash-pinned shared cache, visible-catalogue fold provenance, and registry/preflight gates are available.",
    }
    RUN_CARD.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return card


def main() -> int:
    # The protocol witness is measured before any lane-specific feature work.
    preflight = measure()
    cache = shared_cache_status()
    card = write_blocked_card(preflight, cache)
    print(json.dumps({
        "verdict": card["verdict"],
        "decision": card["decision"],
        "experiments_run": card["experiments_run"],
        "shared_cache_available": cache["available"],
        "preflight_universal_overlap_blocker": preflight.get("universal_overlap_blocker"),
        "run_card": str(RUN_CARD.relative_to(ROOT)),
    }, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
