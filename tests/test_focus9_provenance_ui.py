"""Fail-closed presentation of historical downloads under feed drift."""
import hashlib
import json
from pathlib import Path
import shutil

import pytest
from scripts import build_site

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    for path in ('registry/prior_scores.csv', 'registry/focus9_novel_hypotheses_20261028.json',
                 'docs/evidence/focus9-and-siblings-forensics-20261027.json',
                 'docs/evidence/nine-site-audit-20261027.json',
                 'docs/evidence/protocol-preflight.json',
                 'docs/evidence/protocol-preflight-20261030.json',
                 'docs/evidence/session-57a46ea2-inputs-20261030.json',
                 'docs/evidence/registry-input-grid-review-20261028.json',
                 'docs/evidence/focus9-immutable-files-20261029.json', 'docs/evidence/fleet-feed-current.json',
                 'docs/evidence/focus9-feed-delta-20261030.json',
                 'docs/evidence/focus9-score-source-audit-20261029.json',
                 'docs/evidence/session-9b7ca9b8-inputs-20261030.json'):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    monkeypatch.setattr(build_site, 'ROOT', tmp_path)
    return tmp_path


def row(html, site):
    return html.split(f'<tr><th scope="row"><a href="https://buffedlizard55-lab.github.io/{site}/">', 1)[1].split('</tr>', 1)[0]


def sync_feed_delta(inputs):
    feed_path = inputs / 'docs/evidence/fleet-feed-current.json'
    delta_path = inputs / 'docs/evidence/focus9-feed-delta-20261030.json'
    delta = json.loads(delta_path.read_text())
    delta['current_feed_sha256'] = hashlib.sha256(feed_path.read_bytes()).hexdigest()
    delta_path.write_text(json.dumps(delta))


def test_truncated_or_failed_feed_explicitly_unknown_without_erasing_historical_link(inputs):
    path = inputs / 'docs/evidence/fleet-feed-current.json'
    feed = json.loads(path.read_text())
    project = next(x for x in feed['projects'] if x['repository'].endswith('/GEMSDOE32'))
    project['status'] = 'FORBIDDEN_OR_RATE_LIMITED'
    project['tree_truncated'] = True
    feed['refresh_complete'] = False
    path.write_text(json.dumps(feed))
    sync_feed_delta(inputs)
    html = build_site.focus9_summary()
    r = row(html, 'GEMSDOE32')
    assert 'UNKNOWN' in r and 'SUBMIT: NO' in r
    assert '/raw/22d1d9efbebc0c0f2cf29d76cfd765edf61a19ea/' in r


def test_changed_blob_is_not_confused_with_historical_audited_bytes(inputs):
    path = inputs / 'docs/evidence/fleet-feed-current.json'
    feed = json.loads(path.read_text())
    project = next(x for x in feed['projects'] if x['repository'].endswith('/GEMSDOE32'))
    receipt = json.loads((inputs / 'docs/evidence/focus9-immutable-files-20261029.json').read_text())
    audited_path = next(x['path'] for x in receipt['files'] if x['site'] == 'GEMSDOE32')
    item = next(x for x in project['tif_git_objects'] if x['path'] == audited_path)
    item['git_blob_sha1'] = '0' * 40
    path.write_text(json.dumps(feed))
    sync_feed_delta(inputs)
    assert 'CHANGED' in row(build_site.focus9_summary(), 'GEMSDOE32')


def test_historical_audit_drift_invalidates_binding_instead_of_misattributing(inputs):
    path = inputs / 'docs/evidence/nine-site-audit-20261027.json'
    audit = json.loads(path.read_text())
    audit['files'][0]['sha256'] = '0' * 64
    path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match='unbound forensic-file receipt'):
        build_site.focus9_summary()


def test_replacing_pair_with_self_pair_is_not_a_complete_matrix(inputs):
    path = inputs / 'docs/evidence/nine-site-audit-20261027.json'
    audit = json.loads(path.read_text())
    value = audit['pairwise_overlap'].pop('GEMSDOE24->GEMSDOE25')
    audit['pairwise_overlap']['GEMSDOE24->GEMSDOE24'] = value
    path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match='overlap audit is incomplete'):
        build_site.focus9_summary()
