"""Fail-closed orchestration gates for the shared registry checker.

The numerical comparisons remain in ``vendor/gems57/uniqueness.py``. This
module only interprets their receipts according to the session protocol; it is
not a replacement implementation of the shared metric or registry tools.
"""
from __future__ import annotations

import math
from typing import Any

from gems57.uniqueness import OVERLAP_LIMIT, RHO_LIMIT


def classify_registry_result(result: dict[str, Any], *, stage: str,
                             check_rho: bool = True,
                             check_overlap: bool = True,
                             require_complete: bool = True) -> dict[str, Any]:
    """Apply the literal lane stop thresholds to a shared-tool result.

    A reported Jaccard value or byte/pixel inequality cannot override the
    protocol's ``rho > 0.90`` OR ``forward 3-pixel overlap > 0.70`` rule.
    Incomplete inventories and unreadable/mismatched rasters also block
    *clearance*, but are reported separately from an actual threshold hit.
    """
    rows = list(result.get("rows", []))
    violations: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if not rows:
        errors.append({"submission": None, "error": "registry comparison has no rows"})
    reported_count = result.get("registry_rasters_checked", len(rows))
    try:
        if int(reported_count) != len(rows):
            errors.append({"submission": None, "error": "reported registry count does not match comparison rows"})
    except (TypeError, ValueError):
        errors.append({"submission": None, "error": "invalid reported registry count"})

    for row in rows:
        if "error" in row:
            errors.append({"submission": row.get("submission"), "error": row["error"]})
            continue
        checks = []
        invalid_metrics = []
        for enabled, key, threshold in (
            (check_rho, "spearman_full_footprint", RHO_LIMIT),
            (check_overlap, "my_dots_within_3px_of_theirs", OVERLAP_LIMIT),
        ):
            if not enabled:
                continue
            raw = row.get(key)
            try:
                value = float(raw)
            except (TypeError, ValueError):
                invalid_metrics.append(f"{key} is missing or not numeric")
                continue
            if not math.isfinite(value):
                invalid_metrics.append(f"{key} is not finite")
                continue
            if key == "my_dots_within_3px_of_theirs" and not 0.0 <= value <= 1.0:
                invalid_metrics.append(f"{key} is outside [0, 1]")
                continue
            if key == "spearman_full_footprint" and not -1.0 <= value <= 1.0:
                invalid_metrics.append(f"{key} is outside [-1, 1]")
                continue
            if value > threshold:
                checks.append({"metric": key, "value": value, "threshold": threshold})
        if invalid_metrics:
            errors.append({"submission": row.get("submission"), "error": "; ".join(invalid_metrics)})
        if row.get("identical_bytes") or row.get("identical_decoded_predictions"):
            checks.append({
                "metric": "identity",
                "value": "byte-identical" if row.get("identical_bytes") else "decoded-pixel-identical",
                "threshold": "must differ",
            })
        if checks:
            violations.append({"submission": row.get("submission"), "checks": checks})

    complete = bool(result.get("complete_accessible_scan", False))
    if violations:
        status = "STOP_DUPLICATE_THRESHOLD"
        reason = "At least one literal lane-duplicate threshold was exceeded."
    elif errors:
        status = "STOP_UNVERIFIED_REGISTRY_ROWS"
        reason = "One or more registry rasters could not be verified."
    elif require_complete and not complete:
        status = "STOP_INCOMPLETE_REGISTRY"
        reason = "The accessible registry is not certified complete; uniqueness cannot be cleared."
    else:
        status = "PASS_LOCAL_SCOPE_ONLY" if complete else "DIAGNOSTIC_ONLY_INCOMPLETE_SCOPE"
        reason = "No checked row crossed the requested threshold; scope still limits any uniqueness claim."

    return {
        "stage": stage,
        "status": status,
        "passed": status == "PASS_LOCAL_SCOPE_ONLY",
        "reason": reason,
        "rho_limit": RHO_LIMIT,
        "overlap_limit": OVERLAP_LIMIT,
        "check_rho": check_rho,
        "check_overlap": check_overlap,
        "require_complete": require_complete,
        "registry_complete": complete,
        "registry_rasters_checked": result.get("registry_rasters_checked", len(rows)),
        "violations": violations,
        "errors": errors,
        "worst_spearman_full_footprint": result.get("worst_spearman_full_footprint"),
        "worst_dot_overlap": result.get("worst_dot_overlap"),
        "scope": result.get("scope"),
    }


def assert_experiment_budget_open(experiments_run: int, limit: int = 3) -> None:
    """Stop before any new experiment once the preregistered cap is consumed."""
    if limit < 1 or experiments_run < 0:
        raise ValueError("experiment count and limit must be non-negative/positive")
    if experiments_run >= limit:
        raise RuntimeError(
            f"Experiment budget exhausted ({experiments_run}/{limit}); do not run another experiment."
        )
