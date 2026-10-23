"""Fail-closed helpers for the literal, two-phase parallel-run uniqueness rule.

The shared ``gems57.uniqueness.compare_array_to_registry`` remains the source
of the measured Spearman and forward 3-pixel-overlap fields.  This module only
applies the user's literal thresholds to those rows; it never reclassifies a
continuous raster as exempt and never substitutes Jaccard or a like-for-like
subset for the specified gates.
"""
from __future__ import annotations

import math
from typing import Iterable

RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70


def _finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def literal_blockers(rows: Iterable[dict]) -> list[dict]:
    """Return every row that blocks under the literal protocol.

    A row with a missing/invalid comparison is also a blocker for clearance.
    Rank correlation is tested as ``rho > 0.90`` (the prompt's stated upper
    threshold); forward overlap is tested as ``> 0.70``.  Equality at either
    threshold is not a firing.  Byte or decoded-pixel identity is reported as
    a duplicate independently of these numeric thresholds.
    """
    blockers: list[dict] = []
    for row in rows:
        reasons: list[str] = []
        if row.get("error"):
            reasons.append("registry comparison invalid")
        rho = _finite_number(row.get("spearman_full_footprint"))
        overlap = _finite_number(row.get("my_dots_within_3px_of_theirs"))
        if rho is None:
            reasons.append("rank correlation missing or non-finite")
        elif rho > RHO_LIMIT:
            reasons.append(f"rank correlation {rho:.12g} > {RHO_LIMIT}")
        if overlap is None:
            reasons.append("forward 3-px overlap missing or non-finite")
        elif overlap > OVERLAP_LIMIT:
            reasons.append(f"forward 3-px overlap {overlap:.12g} > {OVERLAP_LIMIT}")
        if row.get("identical_bytes"):
            reasons.append("byte-identical raster")
        if row.get("identical_decoded_predictions"):
            reasons.append("pixel-identical raster")
        if reasons:
            blockers.append({
                "submission": row.get("submission"),
                "repo": row.get("repo"),
                "reasons": reasons,
                "spearman_full_footprint": rho,
                "my_dots_within_3px_of_theirs": overlap,
            })
    return blockers


def phase_status(report: dict) -> dict:
    """Summarize one pre-placement or final-dot comparison without exemptions."""
    rows = report.get("rows") if isinstance(report, dict) else None
    rows = list(rows) if rows is not None else []
    blockers = literal_blockers(rows)
    expected = report.get("registry_rasters_expected") if isinstance(report, dict) else None
    reported_checked = report.get("registry_rasters_checked") if isinstance(report, dict) else None
    missing_or_invalid = report.get("missing_or_invalid") if isinstance(report, dict) else None
    source_errors = report.get("source_errors") if isinstance(report, dict) else None
    complete = bool(
        isinstance(report, dict)
        and report.get("complete_accessible_scan") is True
        and isinstance(expected, int) and not isinstance(expected, bool)
        and expected == len(rows)
        and isinstance(reported_checked, int) and not isinstance(reported_checked, bool)
        and reported_checked == len(rows)
        and type(missing_or_invalid) is int and missing_or_invalid == 0
        and isinstance(source_errors, (list, tuple)) and not source_errors
    )
    errors = [row for row in rows if row.get("error")]
    clear = bool(rows) and complete and not blockers and not errors
    return {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "rows_checked": len(rows),
        "registry_rasters_expected": expected,
        "reported_rasters_checked": reported_checked,
        "missing_or_invalid": missing_or_invalid,
        "source_errors": source_errors,
        "complete_accessible_scan": complete,
        "blockers": blockers,
        "clear_under_literal_rule": clear,
        "scope_note": (
            "A partial scan can establish a collision when one is found, but cannot clear uniqueness."
        ),
    }


def two_phase_status(surface_report: dict, final_dot_report: dict) -> dict:
    """Require both pre-placement surface and final dots to clear literally."""
    surface = phase_status(surface_report)
    final_dots = phase_status(final_dot_report)
    return {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "pre_placement_surface": surface,
        "final_dots": final_dots,
        "clear_under_literal_rule": (
            surface["clear_under_literal_rule"] and final_dots["clear_under_literal_rule"]
        ),
    }
