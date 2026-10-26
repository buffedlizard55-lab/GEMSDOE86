#!/usr/bin/env python3
"""Inspect CURRENT input bytes, not historical preparation receipts.

Read-only: no downloads, cache rebuilding, model, TIFF, or upload. The default
exit code describes successful inspection, NOT training/submission readiness.
Use --require-native to make missing/invalid native inputs a nonzero exit.
Even that flag cannot establish the required shared-cache or scientific gates.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.restore_data import PINS  # noqa: E402


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def local_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('Expected a nonempty repository-relative path')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Input path escapes repository')
    return path


def inspect_file(root: Path, relative: str, expected_sha: str | None,
                 expected_bytes: int | None = None) -> dict:
    row = dict(file=relative, status='INVALID', sha256=None, bytes=None)
    try:
        path = local_path(root, relative)
        if not path.exists():
            return {**row, 'status': 'MISSING'}
        if not path.is_file():
            raise ValueError('Not a regular file')
        if expected_bytes is not None and (type(expected_bytes) is not int or expected_bytes < 0):
            raise ValueError('Invalid byte-length pin')
        if expected_sha is not None and not re.fullmatch('[0-9a-f]{64}', expected_sha):
            raise ValueError('Invalid SHA-256 pin')
        before = path.stat()
        measured_sha = digest(path)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError('Input mutated during inspection')
        row.update(sha256=measured_sha, bytes=after.st_size)
        if expected_bytes is not None and after.st_size != expected_bytes:
            raise ValueError('Byte-length pin mismatch')
        if expected_sha is None:
            row['status'] = 'PRESENT_UNAUTHENTICATED_NO_HASH_PIN'
        elif measured_sha != expected_sha:
            raise ValueError('SHA-256 pin mismatch')
        else:
            row['status'] = 'HASH_VERIFIED'
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        row.update(status='INVALID', error=str(exc))
    return row


def inspect(root: Path = ROOT) -> dict:
    root = root.resolve()
    native = []
    for name, expected in PINS.items():
        # Audit BOTH locations. A corrupt shadow must not be silently ignored
        # merely because the other copy matches the pin.
        copies = [inspect_file(root, f'{directory}/{name}', expected)
                  for directory in ('data', 'data/bridge')]
        valid = any(row['status'] == 'HASH_VERIFIED' for row in copies)
        invalid = any(row['status'] == 'INVALID' for row in copies)
        native.append(dict(name=name, copies=copies, usable=valid and not invalid))

    # `data/prepared_manifest.json` is a frozen historical receipt pinned by
    # the generated site. Prefer the current ignored cache manifest when one
    # exists; never fall back to the historical receipt if that live receipt is
    # malformed, because doing so could hide a failed current preparation.
    live_manifest_rel = '.cache/gems_work/prepared_manifest.json'
    historical_manifest_rel = 'data/prepared_manifest.json'
    live_manifest_candidate = root / live_manifest_rel
    manifest_rel = live_manifest_rel if live_manifest_candidate.exists() else historical_manifest_rel
    prepared = dict(status='MISSING_MANIFEST', arrays=[], native_bands_available=False,
                    shared_template_feature_stack=False, manifest_file=None)
    try:
        manifest_path = local_path(root, manifest_rel)
        if manifest_path.is_file():
            prepared['manifest_file'] = manifest_rel
            manifest = json.loads(manifest_path.read_text())
            records = manifest.get('prepared_arrays')
            if not isinstance(records, list) or not records:
                raise ValueError('Preparation manifest has no array records')
            paths = [record['file'] for record in records]
            if len(set(paths)) != len(paths):
                raise ValueError('Duplicate preparation array records')
            from src.gems86.io import BANDS
            expected_names = {'_footprint.npy', '_labels.npy'}
            if manifest.get('counts', {}).get('has_features') is True:
                expected_names.update(f'{i:02d}_{name}.npy' for i, name in BANDS.items())
            names = [Path(path).name for path in paths]
            if len(set(names)) != len(names) or set(names) != expected_names:
                raise ValueError('Preparation array set does not match native band schema')
            rows = [inspect_file(root, record['file'], record['sha256'], record['bytes']) for record in records]
            complete = all(row['status'] == 'HASH_VERIFIED' for row in rows)
            prepared.update(status='BYTES_VERIFIED_NOT_SHARED_CACHE' if complete else 'STALE_OR_INCOMPLETE_RECEIPT',
                            arrays=rows, native_bands_available=complete and manifest.get('counts', {}).get('has_features') is True)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        prepared.update(status='INVALID_MANIFEST', error=str(exc))

    # This receipt names an earlier lane's mmap; it is not a shared cache pin.
    # Byte presence or a size match alone must NEVER establish shared-cache reuse.
    receipt_path = root / 'registry/feature_receipt.json'
    shared = dict(status='NO_VERIFIABLE_SHARED_CACHE_RECEIPT', ready=False)
    try:
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text())
            row = inspect_file(root, receipt['mmap_path'], receipt.get('sha256'), receipt['bytes'])
            shared.update(recorded_lane_cache=row, status='SHARED_CACHE_NOT_ESTABLISHED',
                          reason='Lane receipt lacks a verified shared-template feature/implementation/visible-mask identity contract.')
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        shared.update(error=str(exc))

    native_ready = all(row['usable'] for row in native)
    blockers = []
    if not native_ready:
        blockers.append('NATIVE_INPUTS_MISSING_OR_INVALID')
    if not prepared['native_bands_available']:
        blockers.append('NATIVE_PREPARATION_NOT_AVAILABLE')
    blockers.append('SHARED_FEATURE_CACHE_NOT_ESTABLISHED')
    return dict(schema='gems86.live-workspace-inputs.v1', measured_utc=datetime.now(timezone.utc).isoformat(),
                evidence_class='INPUT-INTEGRITY-MEASUREMENT', native_inputs=native,
                native_inputs_available=native_ready, preparation=prepared, shared_cache=shared,
                blockers=blockers, inspection_completed=True,
                scope='Current local bytes only. Integrity pins authenticate mirror identity, not organizer origin. No scientific or registry gate was evaluated.',
                safe_to_submit=False, approved_for_weekly_slot=False, new_candidate_generated=False,
                experiments_run=0, submission_slots_used=0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-native', action='store_true')
    args = parser.parse_args(argv)
    report = inspect()
    print(json.dumps(report, indent=2, allow_nan=False))
    return 1 if args.require_native and not report['native_inputs_available'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
