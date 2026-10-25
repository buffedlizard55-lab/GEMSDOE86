#!/usr/bin/env python3
"""Run the existing three-pass repository review; never authorize an upload.

No network, model training, candidate generation, or weekly submission is performed.
Evidence is written outside the published site by default so this review does not
manufacture a fresh scientific result or modify archived run cards.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def plan(python: str) -> list[tuple[str, list[str]]]:
    return [
        ("pass1-release", [python, "scripts/audit_release.py"]),
        ("pass2-tests", [python, "-m", "pytest", "-q"]),
        ("pass3-frozen-evidence", [python, "scripts/build_review_card.py", "--check"]),
        ("pass3-generated-site", [python, "scripts/build_site.py", "--check"]),
        ("pass3-site-links", [python, "scripts/check_site.py"]),
        ("pass3-downloads", [python, "scripts/audit_downloads.py"]),
        ("pass3-live-inputs", [python, "scripts/audit_workspace_inputs.py"]),
    ]


def run_check(name: str, command: list[str], root: Path, timeout: int) -> dict:
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, timeout=timeout)
        stdout, stderr = result.stdout, result.stderr
        code, status = result.returncode, "PASS" if result.returncode == 0 else "FAIL"
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        code, status = None, "TIMEOUT"
    except OSError as exc:
        stdout, stderr = b"", str(exc).encode()
        code, status = None, "ERROR"
    return dict(name=name, command=command, status=status, returncode=code,
                stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                stderr_sha256=hashlib.sha256(stderr).hexdigest(),
                stdout_tail=stdout[-16000:].decode(errors="replace"),
                stderr_tail=stderr[-16000:].decode(errors="replace"))


def review(root: Path = ROOT, timeout: int = 600) -> dict:
    # Continue after failures: each pass contributes diagnostics, none repairs or
    # overrides a scientific gate. The audit itself may refresh live audit JSON.
    checks = [run_check(name, command, root, timeout) for name, command in plan(sys.executable)]
    evidence = {}
    for relative in ("PROMPT.md", "AGENTS.md", "research/REQUEST_20261025.md",
                     "docs/evidence/release-readiness.json", "data/prepared_manifest.json",
                     "registry/feature_receipt.json"):
        path = root / relative
        evidence[relative] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return dict(schema="gems86.three-pass-review.v1",
                measured_utc=datetime.now(timezone.utc).isoformat(),
                checks=checks, software_review_passed=all(c["status"] == "PASS" for c in checks),
                evidence_sha256=evidence,
                training_readiness_established=False,
                readiness_scope="Software checks and live input inspection only; neither can authorize training or submission.",
                hypothesis="No lane assigned; repository verification only",
                mechanism="No candidate constructed", named_non_fault_process="Not tested",
                holdout_dti=dict(evidence_class="HOLDOUT-DTI", status="NOT_RUN",
                                 evaluator_version="gems57-pooled-hide-v2",
                                 withheld_positives=None, value=None, ci95=None),
                correlation_overlap_vs_registry=dict(status="NOT_RUN_NO_NEW_CANDIDATE", complete=False),
                raster_sha256=None,
                validator=dict(status="NOT_RUN_NO_NEW_CANDIDATE", no_nan_inside_footprint=None,
                               values_in_0_1=None, crs_shape_transform_match=None),
                submission_name=None, note="Three-pass software audit only; no new TIFF, scientific validation or weekly-slot authorization.",
                experiments_run=0, submission_slots_used=0, safe_to_submit=False,
                approved_for_weekly_slot=False, verdict="negative")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cache/repository-review.json")
    parser.add_argument("--timeout", type=int, default=600, help="Maximum seconds per check")
    args = parser.parse_args(argv)
    if args.timeout < 1:
        parser.error("--timeout must be positive")
    output = args.output.resolve()
    # Do not allow a convenience command to overwrite source, published or
    # archived evidence. Reports belong only in the ignored local cache.
    if not output.is_relative_to((ROOT / ".cache").resolve()):
        parser.error("--output must be inside the repository .cache directory")
    card = review(timeout=args.timeout)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    try:
        temporary.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps(card, indent=2, allow_nan=False))
    return 0 if card["software_review_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
