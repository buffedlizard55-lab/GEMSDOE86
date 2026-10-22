#!/usr/bin/env python3
"""Fail-closed prerequisite inventory for the GEMS workflow.

This script does not load/modify rasters, run a holdout, clear uniqueness, or write a
submission. A "READY" result means only that the named inputs/tools were found; the
shared evaluator, registry gate, and shared submission writer still have to pass.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DATA = (
    "training_features.tif",
    "labels.tif",
    "existing_faults.tif",
    "sample_submission.tif",
)
SHARED_FILES = (
    "vendor/gems57/evaluate_holdout.py",
    "vendor/gems57/submission_writer.py",
    "vendor/gems57/holdout.py",
    "vendor/gems57/metric.py",
    "vendor/gems57/uniqueness.py",
    "vendor/gems57/gates.py",
)


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return str(path)


def _file_record(path: Path | None) -> dict:
    if path is None:
        return {"path": None, "exists": False, "bytes": None}
    display = _display_path(path)
    try:
        stat = path.stat()
    except (FileNotFoundError, NotADirectoryError, OSError):
        return {"path": display, "exists": False, "bytes": None}
    return {
        "path": display,
        "exists": path.is_file(),
        "bytes": stat.st_size if path.is_file() else None,
    }


def inspect_environment(env: dict[str, str] | None = None) -> dict:
    env = os.environ if env is None else env
    data_value = env.get("GEMS_DATA_DIR", "").strip()
    data_dir = Path(data_value).expanduser() if data_value else ROOT / "data" / "raw"
    stack_value = env.get("GEMS_FEATURE_STACK", "").strip()
    template_value = env.get("GEMS_SHARED_TEMPLATE", "").strip()
    registry_value = env.get("GEMS_REGISTRY_INDEX", "").strip()

    data_files = {name: _file_record(data_dir / name) for name in REQUIRED_DATA}
    feature_stack = _file_record(Path(stack_value).expanduser() if stack_value else None)

    shared_root = Path(template_value).expanduser() if template_value else None
    shared_files = {
        rel: _file_record(shared_root / rel if shared_root else None)
        for rel in SHARED_FILES
    }
    registry_index = _file_record(Path(registry_value).expanduser() if registry_value else None)

    blockers: list[str] = []
    missing_data = [name for name, rec in data_files.items() if not rec["exists"]]
    if missing_data:
        blockers.append("Missing required competition inputs: " + ", ".join(missing_data))
    if not feature_stack["exists"]:
        blockers.append("GEMS_FEATURE_STACK is unset or its cached feature file is missing")
    missing_tools = [rel for rel, rec in shared_files.items() if not rec["exists"]]
    if missing_tools:
        blockers.append(
            "GEMS_SHARED_TEMPLATE is unset or required shared tools are missing: "
            + ", ".join(missing_tools)
        )
    if not registry_index["exists"]:
        blockers.append("GEMS_REGISTRY_INDEX is unset or the registry index is missing")

    ready_for_shared_run = not blockers
    return {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "PREREQUISITES_PRESENT_NOT_VALIDATED" if ready_for_shared_run else "BLOCKED",
        "ready_for_shared_run": ready_for_shared_run,
        "submission_status": "NO_TIF_GENERATED",
        "data_dir": _display_path(data_dir),
        "competition_data_access": "not_assessed_by_file_presence_check; session observation is recorded in docs/sources.md",
        "input_provenance_status": "NOT_AUTHENTICATED_BY_FILE_PRESENCE",
        "data_files": data_files,
        "cached_feature_stack": feature_stack,
        "shared_tools": shared_files,
        "registry_index": registry_index,
        "blockers": blockers,
        "limitations": [
            "This inventory checks file existence only; it does not authenticate provenance or inspect raster metadata.",
            "It does not run the shared hide-and-recover evaluator, per-feature leakage tests, or uniqueness gate.",
            "It does not call the submission writer and cannot authorize a download or submission.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "data" / "preflight.json",
        help="write the prerequisite report as JSON (default: docs/data/preflight.json)",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="return exit code 2 when prerequisites are blocked; never implies validation",
    )
    args = parser.parse_args(argv)

    report = inspect_environment()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 2 if args.require_ready and not report["ready_for_shared_run"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
