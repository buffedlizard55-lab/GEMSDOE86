"""Synthetic pin-integrity tests; no model or submission evidence."""
from pathlib import Path
import shutil

import pytest

from scripts import session_preflight

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def pinned_tree(tmp_path, monkeypatch):
    for relative in ('research/template_pin.json', 'vendor/gems57', 'vendor/template66'):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__'))
        else:
            shutil.copy2(source, target)
    monkeypatch.setattr(session_preflight, 'ROOT', tmp_path)
    return tmp_path


def test_intact_both_import_paths_pass(pinned_tree):
    assert session_preflight.check_pins() is True


@pytest.mark.parametrize('relative', [
    'vendor/gems57/evaluate_holdout.py',
    'vendor/gems57/submission_writer.py',
    'vendor/template66/gems57/evaluate_holdout.py',
    'vendor/template66/gems57/submission_writer.py',
])
@pytest.mark.parametrize('damage', ['changed', 'missing'])
def test_either_import_path_drift_stops(pinned_tree, relative, damage):
    target = pinned_tree / relative
    if damage == 'missing':
        target.unlink()
    else:
        target.write_text(target.read_text() + '\n# synthetic drift\n')
    assert session_preflight.check_pins() is False


@pytest.mark.parametrize('relative', [
    'research/template_pin.json', 'vendor/template66/TEMPLATE_SHA256.txt',
])
def test_malformed_pin_stops(pinned_tree, relative):
    (pinned_tree / relative).write_text('not a pin\n')
    assert session_preflight.check_pins() is False
