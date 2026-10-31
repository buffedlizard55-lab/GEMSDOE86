#!/usr/bin/env python3
"""Bind the nine audited historical TIFFs to immutable GitHub commits.

This read-only, byte-level forensic acquisition is NOT a new candidate, score,
registry clearance, or approval to upload. It fetches only the nine existing
owner files for comparison with the earlier nine-site audit. GitHub blob SHA-1,
SHA-256 and size must all agree before a receipt is published. The receipt can
then be used offline to construct commit-pinned audit-only download links.
"""
from __future__ import annotations

import hashlib
import io
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_release import sha256, strict_json, write_json  # noqa: E402
from scripts.restore_protocol_data import write_blob  # noqa: E402

AUDIT = 'docs/evidence/nine-site-audit-20261027.json'
FEED = 'docs/evidence/fleet-feed-current.json'
RECEIPT = 'docs/evidence/focus9-immutable-files-20261029.json'
SITES = ('GEMSDOE24', 'GEMSDOE25', 'GEMSDOE27', 'GEMSDOE28', 'GEMSDOE30',
         'GEMSDOE31', 'GEMSDOE32', 'GEMSDOE33', 'GEMSDOE36')


def _hex(value: object, length: int) -> bool:
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{%d}' % length, value) is not None


def _audited_files(audit: dict) -> dict:
    rows = audit.get('files', [])
    if not isinstance(rows, list) or len(rows) != len(SITES):
        raise ValueError('Expected precisely nine audited source files')
    result = {}
    for row in rows:
        site = row.get('site')
        if site not in SITES or site in result:
            raise ValueError('Unknown or duplicate Focus-9 site')
        name = row.get('file', '')
        prefix = f'{site}-main/'
        if not isinstance(name, str) or not name.startswith(prefix):
            raise ValueError(f'Unexpected owner source path for {site}')
        path = name[len(prefix):]
        parts = PurePosixPath(path).parts
        if (not path.startswith('docs/downloads/') or '..' in parts
                or PurePosixPath(path).as_posix() != path
                or not path.lower().endswith(('.tif', '.tiff'))):
            raise ValueError(f'Unsafe or unexpected audited TIFF path for {site}')
        if not _hex(row.get('sha256'), 64) or type(row.get('bytes')) is not int or row['bytes'] <= 0:
            raise ValueError(f'Invalid file identity for {site}')
        result[site] = (row, path)
    if set(result) != set(SITES):
        raise ValueError('Missing Focus-9 sites')
    return result


def _projects(feed: dict) -> dict:
    rows = feed.get('projects')
    if not isinstance(rows, list):
        raise ValueError('Invalid feed projects')
    result = {}
    for row in rows:
        repo = row.get('repository')
        if repo in result:
            raise ValueError('Duplicate project in feed')
        result[repo] = row
    return result


def _live_entry(project: dict | None, path: str) -> dict | None:
    if not project or project.get('status') != 'SNAPSHOT_OK' or project.get('tree_truncated') is not False:
        return None
    entries = [item for item in project.get('tif_git_objects', []) if item.get('path') == path]
    return entries[0] if len(entries) == 1 else None


def acquire(audit: dict, feed: dict, audit_sha256: str, fetch=write_blob) -> dict:
    """Fetch exact Git objects and verify them against the old pixel audit."""
    if not _hex(audit_sha256, 64):
        raise ValueError('Invalid audited-source hash')
    files, projects = _audited_files(audit), _projects(feed)
    records = []
    for site in SITES:
        historical, path = files[site]
        repo = f'buffedlizard55-lab/{site}'
        project = projects.get(repo)
        entry = _live_entry(project, path)
        if not entry or not _hex(project.get('commit_sha'), 40) or not _hex(entry.get('git_blob_sha1'), 40):
            raise ValueError(f'No complete immutable Git tree entry for {site}')
        if type(entry.get('git_blob_bytes')) is not int or entry['git_blob_bytes'] != historical['bytes']:
            raise ValueError(f'Git tree size differs from prior pixel audit for {site}')
        buf = io.BytesIO()
        fetch(repo, entry['git_blob_sha1'], buf)
        payload = buf.getvalue()
        git_sha = hashlib.sha1(b'blob ' + str(len(payload)).encode('ascii') + b'\0' + payload).hexdigest()
        content_sha = hashlib.sha256(payload).hexdigest()
        if (len(payload) != historical['bytes'] or git_sha != entry['git_blob_sha1']
                or content_sha != historical['sha256']):
            raise ValueError(f'Git object or pixel-audit content identity mismatch for {site}')
        records.append(dict(site=site, repository=repo, path=path,
                            commit_sha=project['commit_sha'], git_blob_sha1=git_sha,
                            sha256=content_sha, bytes=len(payload)))
    return dict(schema='gems86.focus9-immutable-files.v1', evidence_class='FILE-IDENTITY-MEASUREMENT',
                measured_utc=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                nine_site_audit=AUDIT, nine_site_audit_sha256=audit_sha256,
                feed_observed_utc=feed.get('refreshed_utc'),
                method='Fetched Git blob bytes; independently recomputed Git SHA-1, SHA-256 and size; matched the earlier nine-site pixel-audit identity.',
                scope='Owner files for forensic use only. This is not an organizer receipt, leaderboard score, new prediction, or full-registry uniqueness clearance.',
                historical_files_only=True, safe_to_submit=False, approved_for_weekly_slot=False,
                new_candidate_generated=False, experiments_run=0, submission_slots_used=0, files=records)


def validate_receipt(audit: dict, receipt: dict, audit_sha256: str) -> dict:
    """Offline integrity/identity checks; the receipt is a dated measurement."""
    if (receipt.get('schema') != 'gems86.focus9-immutable-files.v1'
            or receipt.get('nine_site_audit') != AUDIT
            or receipt.get('nine_site_audit_sha256') != audit_sha256
            or receipt.get('historical_files_only') is not True
            or receipt.get('safe_to_submit') is not False
            or receipt.get('approved_for_weekly_slot') is not False
            or receipt.get('new_candidate_generated') is not False
            or receipt.get('experiments_run') != 0 or receipt.get('submission_slots_used') != 0):
        raise ValueError('Invalid or unbound forensic-file receipt')
    audited = _audited_files(audit)
    rows = receipt.get('files')
    if not isinstance(rows, list) or len(rows) != len(SITES):
        raise ValueError('Forensic receipt must contain exactly nine files')
    result = {}
    for row in rows:
        site = row.get('site')
        if site not in audited or site in result:
            raise ValueError('Unknown or duplicate forensic receipt site')
        old, path = audited[site]
        if (row.get('repository') != f'buffedlizard55-lab/{site}' or row.get('path') != path
                or row.get('sha256') != old['sha256'] or row.get('bytes') != old['bytes']
                or not _hex(row.get('commit_sha'), 40) or not _hex(row.get('git_blob_sha1'), 40)):
            raise ValueError(f'Forensic receipt disagrees with audited file identity for {site}')
        result[site] = row
    if set(result) != set(SITES):
        raise ValueError('Forensic receipt missing a Focus-9 site')
    return result


def current_tree_status(record: dict, projects: dict) -> str:
    """Only Git metadata at feed time, never a byte remeasurement or score."""
    project = projects.get(record['repository'])
    if not project or project.get('status') != 'SNAPSHOT_OK' or project.get('tree_truncated') is not False:
        return 'UNKNOWN — incomplete Git metadata feed'
    matches = [item for item in project.get('tif_git_objects', []) if item.get('path') == record['path']]
    if len(matches) != 1:
        return 'CHANGED OR MISSING — current tree does not uniquely contain this path'
    entry = matches[0]
    if entry.get('git_blob_sha1') != record['git_blob_sha1'] or entry.get('git_blob_bytes') != record['bytes']:
        return 'CHANGED — current tree object differs from audited bytes'
    return 'MATCH — current tree object matches audited bytes'


def immutable_download_url(record: dict) -> str:
    # All components have already passed validate_receipt; quote path segments.
    return f"https://github.com/{record['repository']}/raw/{record['commit_sha']}/{quote(record['path'], safe='/')}?download=1"


def main() -> int:
    audit_path = ROOT / AUDIT
    report = acquire(strict_json(audit_path), strict_json(ROOT / FEED), sha256(audit_path))
    validate_receipt(strict_json(audit_path), report, sha256(audit_path))
    write_json(ROOT / RECEIPT, report)
    print(f"Verified {len(report['files'])} immutable historical owner files; audit-only; DO NOT SUBMIT")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
