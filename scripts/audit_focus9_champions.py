#!/usr/bin/env python3
"""Byte-verify archived nine-site historical winners, for audit/education only.

Requires the metadata feed from refresh_fleet.py and its own GitHub read access.
Downloads only historical raster blobs to ignored .cache, hashes them, and
compares them with the archived 2026-10-26 forensic records. No candidate,
model, holdout, selector, competition request, or slot is created or used.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_release import sha256, strict_json, write_json  # noqa: E402
from scripts.focus9 import SITES, best_claims, forensic_match, read_ledger, snapshot_match  # noqa: E402
from scripts.restore_protocol_data import write_blob  # noqa: E402


def git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()


def measure(root: Path = ROOT) -> dict:
    ledger_path = root / 'registry/prior_scores.csv'
    forensic_path = root / 'docs/evidence/focus9-forensics-20261026-rev2.json'
    feed_path = root / 'docs/evidence/fleet-feed.json'
    claims = best_claims(read_ledger(ledger_path))
    forensic, feed = strict_json(forensic_path), strict_json(feed_path)
    if forensic.get('evidence_class') != 'REGISTRY-MEASUREMENT':
        raise ValueError('Historical forensic evidence class is missing or invalid')
    cache = root / '.cache/focus9-historical-audit'
    cache.mkdir(parents=True, exist_ok=True)
    winners = []
    for site in SITES:
        for claim in claims[site]:
            archived = forensic_match(site, claim['submission'], forensic)
            if not archived:
                raise ValueError(f'{site}: exact historical forensic entry missing or ambiguous')
            filename = archived['file'].split('__', 1)[1]
            found = snapshot_match(site, filename, feed)
            if not found:
                raise ValueError(f'{site}: exact current tree object is missing or ambiguous')
            project, blob = found
            path = cache / (site + '__' + filename)
            # A local historical file is usable only if BOTH cryptographic identities
            # match. A bad cached file triggers a fresh fetch, not a false pass.
            local = root / 'data/scored_fleet' / (site + '__' + filename)
            payload = local.read_bytes() if local.is_file() else None
            if payload is None or git_blob_sha1(payload) != blob['git_blob_sha1']:
                with path.open('wb') as stream:
                    write_blob(project['repository'], blob['git_blob_sha1'], stream)
                payload = path.read_bytes()
            git_ok = git_blob_sha1(payload) == blob['git_blob_sha1']
            digest = hashlib.sha256(payload).hexdigest()
            archived_ok = digest == archived['sha256']
            if not git_ok or not archived_ok or len(payload) != blob['git_blob_bytes']:
                raise ValueError(f'{site}: Git object, size or archived SHA-256 mismatch')
            winners.append(dict(site=site, submission=claim['submission'],
                                owner_reported_result=claim['score'], evidence_class=claim['evidence_class'],
                                source_repository=project['repository'], source_commit=project['commit_sha'],
                                source_path=blob['path'], git_blob_sha1=blob['git_blob_sha1'],
                                sha256=digest, bytes=len(payload), forensic_file=archived['file'],
                                git_object_matches=git_ok, archived_sha256_matches=archived_ok))
    return dict(schema='gems86.focus9-champion-byte-audit.v1',
                measured_utc=datetime.now(timezone.utc).isoformat(),
                forensic_measured_utc=forensic['measured_utc'],
                ledger_sha256=sha256(ledger_path), forensic_sha256=sha256(forensic_path),
                github_feed_sha256=sha256(feed_path), winners=winners,
                organizer_receipts_obtained=0, new_rasters_generated=0, submission_slots_used=0,
                scope=('Historical owner-reported winners; byte identity only. Archived spatial overlap is not '
                       'recomputed, no organizer score is verified, and no file is a unique submission.'))


def main() -> None:
    report = measure()
    write_json(ROOT / 'docs/evidence/focus9-champions-20261027.json', report)
    print(json.dumps({'winners_verified': len(report['winners']),
                      'organizer_receipts_obtained': report['organizer_receipts_obtained'],
                      'new_rasters_generated': report['new_rasters_generated'],
                      'submission_slots_used': report['submission_slots_used']}, indent=2))


if __name__ == '__main__':
    main()
