"""Immutable owner-file references never imply a new score or submit approval."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import focus9_provenance as p
from scripts.audit_release import sha256

ROOT = Path(__file__).resolve().parents[1]


def fixtures():
    audit = {'files': []}
    feed = {'projects': [], 'refreshed_utc': '2026-10-29T00:00:00Z'}
    payloads = {}
    for i, site in enumerate(p.SITES):
        blob = f'historical {site}'.encode()
        path = f'docs/downloads/file-{i}.tif'
        git_sha = hashlib.sha1(b'blob ' + str(len(blob)).encode() + b'\0' + blob).hexdigest()
        audit['files'].append({'site': site, 'file': f'{site}-main/{path}',
                               'sha256': hashlib.sha256(blob).hexdigest(), 'bytes': len(blob)})
        feed['projects'].append({'repository': f'buffedlizard55-lab/{site}', 'status': 'SNAPSHOT_OK',
                                 'tree_truncated': False, 'commit_sha': 'a' * 40,
                                 'tif_git_objects': [{'path': path, 'git_blob_sha1': git_sha,
                                                      'git_blob_bytes': len(blob)}]})
        payloads[git_sha] = blob
    return audit, feed, payloads


def test_acquisition_binds_sha256_git_object_commit_and_bytes():
    audit, feed, payloads = fixtures()
    calls = []
    def fetch(repo, git_sha, out):
        calls.append((repo, git_sha))
        out.write(payloads[git_sha])
    report = p.acquire(audit, feed, 'b' * 64, fetch=fetch)
    assert len(calls) == len(report['files']) == 9
    records = p.validate_receipt(audit, report, 'b' * 64)
    first = records[p.SITES[0]]
    assert '/raw/' + 'a' * 40 + '/docs/downloads/' in p.immutable_download_url(first)
    assert p.current_tree_status(first, p._projects(feed)).startswith('MATCH')
    assert report['safe_to_submit'] is False and report['approved_for_weekly_slot'] is False
    assert report['experiments_run'] == report['submission_slots_used'] == 0


def test_wrong_bytes_or_missing_tree_never_publish_a_receipt():
    audit, feed, payloads = fixtures()
    def corrupt(repo, git_sha, out):
        out.write(payloads[git_sha] + b'x')
    with pytest.raises(ValueError, match='identity mismatch'):
        p.acquire(audit, feed, 'b' * 64, fetch=corrupt)
    feed['projects'][0]['tree_truncated'] = True
    with pytest.raises(ValueError, match='No complete immutable Git tree'):
        p.acquire(audit, feed, 'b' * 64, fetch=lambda *_: None)


def test_receipt_rejects_tampered_sha_path_size_or_authorization():
    audit, feed, payloads = fixtures()
    report = p.acquire(audit, feed, 'b' * 64, fetch=lambda repo, sha, out: out.write(payloads[sha]))
    for key, value in [('sha256', '0' * 64), ('path', 'docs/downloads/../other.tif'),
                       ('commit_sha', 'main'), ('bytes', 1)]:
        bad = copy.deepcopy(report)
        bad['files'][0][key] = value
        with pytest.raises(ValueError):
            p.validate_receipt(audit, bad, 'b' * 64)
    bad = copy.deepcopy(report)
    bad['safe_to_submit'] = True
    with pytest.raises(ValueError):
        p.validate_receipt(audit, bad, 'b' * 64)
    with pytest.raises(ValueError):
        p.validate_receipt(audit, report, 'c' * 64)


def test_live_tree_status_distinguishes_match_change_missing_and_unknown():
    audit, feed, payloads = fixtures()
    report = p.acquire(audit, feed, 'b' * 64, fetch=lambda repo, sha, out: out.write(payloads[sha]))
    first = report['files'][0]
    projects = p._projects(feed)
    assert p.current_tree_status(first, projects).startswith('MATCH')
    changed = copy.deepcopy(projects)
    changed[first['repository']]['tif_git_objects'][0]['git_blob_sha1'] = '0' * 40
    assert p.current_tree_status(first, changed).startswith('CHANGED')
    changed[first['repository']]['tif_git_objects'] = []
    assert p.current_tree_status(first, changed).startswith('CHANGED OR MISSING')
    changed[first['repository']]['status'] = 'FORBIDDEN_OR_RATE_LIMITED'
    assert p.current_tree_status(first, changed).startswith('UNKNOWN')


def test_committed_receipt_matches_the_dated_audit():
    audit_path = ROOT / p.AUDIT
    audit = json.loads(audit_path.read_text())
    receipt = json.loads((ROOT / p.RECEIPT).read_text())
    records = p.validate_receipt(audit, receipt, sha256(audit_path))
    assert set(records) == set(p.SITES)
    assert receipt['historical_files_only'] is True
    assert receipt['safe_to_submit'] is receipt['approved_for_weekly_slot'] is False
