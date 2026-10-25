"""Historical receipts cannot establish current training inputs or upload safety."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts import audit_workspace_inputs as audit
from src.gems86.io import BANDS


def write(root, name, payload=b'fixture'):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return dict(file=name, sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))


def prepared(root, *, features=True):
    names = ['_footprint.npy', '_labels.npy']
    if features:
        names += [f'{i:02d}_{name}.npy' for i, name in BANDS.items()]
    records = [write(root, f'.cache/gems_work/bands/{name}') for name in names]
    manifest = dict(counts=dict(has_features=features), prepared_arrays=records)
    write(root, 'data/prepared_manifest.json', json.dumps(manifest).encode())
    return manifest


def test_missing_inputs_are_explicit_not_a_readiness_pass(tmp_path):
    result = audit.inspect(tmp_path)
    assert not result['native_inputs_available']
    assert result['preparation']['status'] == 'MISSING_MANIFEST'
    assert result['shared_cache']['ready'] is False
    assert result['safe_to_submit'] is False
    assert result['new_candidate_generated'] is False
    assert result['experiments_run'] == result['submission_slots_used'] == 0


def test_live_bytes_override_historical_has_features_receipt(tmp_path):
    prepared(tmp_path)
    (tmp_path / '.cache/gems_work/bands/01_mag_anom.npy').unlink()
    result = audit.inspect(tmp_path)
    assert result['preparation']['status'] == 'STALE_OR_INCOMPLETE_RECEIPT'
    assert not result['preparation']['native_bands_available']


def test_complete_native_array_set_is_not_shared_cache(tmp_path):
    prepared(tmp_path)
    result = audit.inspect(tmp_path)
    assert result['preparation']['native_bands_available']
    assert not result['preparation']['shared_template_feature_stack']
    assert not result['shared_cache']['ready']
    assert not result['safe_to_submit']


@pytest.mark.parametrize('features', [False, True])
def test_incomplete_or_duplicate_schema_cannot_be_promoted(tmp_path, features):
    manifest = prepared(tmp_path, features=features)
    manifest['prepared_arrays'].append(manifest['prepared_arrays'][0])
    write(tmp_path, 'data/prepared_manifest.json', json.dumps(manifest).encode())
    assert audit.inspect(tmp_path)['preparation']['status'] == 'INVALID_MANIFEST'


def test_grid_only_arrays_are_not_training_bands(tmp_path):
    prepared(tmp_path, features=False)
    result = audit.inspect(tmp_path)
    assert result['preparation']['status'] == 'BYTES_VERIFIED_NOT_SHARED_CACHE'
    assert not result['preparation']['native_bands_available']


@pytest.mark.parametrize('path', ['../escape', '/etc/passwd', ''])
def test_untrusted_receipt_path_cannot_escape_workspace(tmp_path, path):
    result = audit.inspect_file(tmp_path, path, None)
    assert result['status'] == 'INVALID'
    assert result['sha256'] is None


def test_symlink_escape_is_invalid(tmp_path):
    (tmp_path / 'escape').symlink_to(tmp_path.parent)
    assert audit.inspect_file(tmp_path, 'escape/outside', None)['status'] == 'INVALID'


def test_hash_and_byte_pins_fail_closed(tmp_path):
    record = write(tmp_path, 'input')
    assert audit.inspect_file(tmp_path, 'input', record['sha256'], record['bytes'])['status'] == 'HASH_VERIFIED'
    assert audit.inspect_file(tmp_path, 'input', '0' * 64)['status'] == 'INVALID'
    assert audit.inspect_file(tmp_path, 'input', record['sha256'], True)['status'] == 'INVALID'
    assert audit.inspect_file(tmp_path, 'input', None)['status'] == 'PRESENT_UNAUTHENTICATED_NO_HASH_PIN'


def test_shadow_corruption_is_not_silently_ignored(tmp_path, monkeypatch):
    record = write(tmp_path, 'data/input.tif')
    write(tmp_path, 'data/bridge/input.tif', b'corrupt shadow')
    monkeypatch.setattr(audit, 'PINS', {'input.tif': record['sha256']})
    assert not audit.inspect(tmp_path)['native_inputs_available']


def test_size_only_lane_receipt_does_not_prove_shared_cache(tmp_path):
    record = write(tmp_path, '.cache/lane/mmap')
    receipt = dict(mmap_path=record['file'], bytes=record['bytes'])
    write(tmp_path, 'registry/feature_receipt.json', json.dumps(receipt).encode())
    result = audit.inspect(tmp_path)
    assert result['shared_cache']['recorded_lane_cache']['status'] == 'PRESENT_UNAUTHENTICATED_NO_HASH_PIN'
    assert result['shared_cache']['ready'] is False


@pytest.mark.parametrize('payload', ['null', '[]', '{', '{"prepared_arrays":[null]}'])
def test_malformed_manifest_is_an_explicit_blocker(tmp_path, payload):
    write(tmp_path, 'data/prepared_manifest.json', payload.encode())
    assert audit.inspect(tmp_path)['preparation']['status'] == 'INVALID_MANIFEST'


def test_cli_require_native_exits_nonzero_but_default_is_inspection_only(tmp_path, monkeypatch, capsys):
    actual_inspect = audit.inspect
    monkeypatch.setattr(audit, 'inspect', lambda: actual_inspect(tmp_path))
    assert audit.main([]) == 0
    assert audit.main(['--require-native']) == 1
    assert '"safe_to_submit": false' in capsys.readouterr().out


def test_write_report_is_atomic_and_does_not_imply_readiness(tmp_path):
    report = audit.inspect(tmp_path)
    target = tmp_path / 'docs/evidence/current-workspace-inputs.json'
    audit.persist_report(report, target)
    assert json.loads(target.read_text()) == report
    assert not target.with_name(target.name + '.partial').exists()
    assert report['safe_to_submit'] is False
    assert report['approved_for_weekly_slot'] is False


def test_symlink_cycle_is_reported_without_traceback(tmp_path):
    (tmp_path / 'cycle').symlink_to('cycle')
    result = audit.inspect_file(tmp_path, 'cycle', None)
    assert result['status'] == 'INVALID'
    assert result['sha256'] is None
