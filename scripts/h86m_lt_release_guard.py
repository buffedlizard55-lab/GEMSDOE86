"""Validate the fail-closed release overlay for the H86M-LT upstream lane.

The original scientific run card is immutable upstream evidence and says
``safe_to_submit=true`` under lane-local PA-86 gates.  This wrapper does not
rewrite that card; it binds its exact hash and the candidate TIFF to an explicit
repo-wide DO NOT SUBMIT decision.  Only this fixed lane card is accepted here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

CARD_REL = "docs/evidence/h86m-lt-run-card.json"
OVERLAY_REL = "docs/evidence/h86m-lt-release-overlay.json"
CANDIDATE_REL = (
    "docs/downloads/gems86-h86m-lt-tomography-37654dots-"
    "20261025T174610Z-7b4ebdf5-zeros.tif"
)
CARD_SHA256 = "3dd9aca2fff500cb6cf0d1bd9047418e90e76c773ffd40aee0fcb95979d9fa4c"
CANDIDATE_SHA256 = "4067382cab05de80e85c22e717a8ea98e569f85933eedd9690651a7755eaebee"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def valid_h86m_lt_release_overlay(root: Path) -> bool:
    """Return true only for the pinned lane card with a complete negative overlay."""
    root = Path(root).resolve()
    card_path = root / CARD_REL
    overlay_path = root / OVERLAY_REL
    candidate_path = root / CANDIDATE_REL
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        if _sha256(card_path) != CARD_SHA256 or _sha256(candidate_path) != CANDIDATE_SHA256:
            return False
    except (OSError, ValueError, TypeError):
        return False

    full_registry = card.get("full_registry_uniqueness", {})
    return all((
        overlay.get("schema") == "gems86.h86m-lt-release-overlay.v1",
        overlay.get("source_run_card") == CARD_REL,
        overlay.get("source_run_card_sha256") == CARD_SHA256,
        overlay.get("candidate_file") == CANDIDATE_REL,
        overlay.get("candidate_sha256") == CANDIDATE_SHA256,
        overlay.get("lane_verdict") == "promote",
        overlay.get("lane_safe_to_submit") is True,
        overlay.get("lane_slot_approval") is False,
        overlay.get("lane_submission_slots_used") == 0,
        overlay.get("holdout_dti_status") == "NOT_RUN_ALTERNATE_EVIDENCE_DESIGN",
        overlay.get("global_release_decision") == "DO NOT SUBMIT",
        overlay.get("global_safe_to_submit") is False,
        overlay.get("global_approved_for_weekly_slot") is False,
        overlay.get("submission_slots_used") == 0,
        card.get("lane", "").startswith("H86M-LT "),
        card.get("verdict") == "promote",
        card.get("safe_to_submit") is True,
        card.get("approved_for_weekly_slot") is False,
        card.get("submission_slots_used") == 0,
        card.get("raster_sha256") == CANDIDATE_SHA256,
        "Catalogue hide-and-recover not used for promotion" in card.get("evidence_class_note", ""),
        full_registry.get("pass") is True,
        full_registry.get("registry_files") == 655,
        full_registry.get("measured") == 655,
        full_registry.get("dotfields") == 414,
        full_registry.get("max_forward_overlap_3px", 1.0) <= 0.70,
        full_registry.get("firings_forward_gt_070") == 0,
        isinstance(overlay.get("reasons"), list) and len(overlay["reasons"]) >= 3,
    ))
