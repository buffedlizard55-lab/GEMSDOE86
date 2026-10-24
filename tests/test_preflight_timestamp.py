"""Synthetic audit provenance tests; these are not geological experiments."""
from datetime import datetime, timezone
import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest
import rasterio
from affine import Affine

from scripts import audit_release, protocol_preflight


@pytest.fixture
def measurement_inputs(tmp_path, monkeypatch):
    data = tmp_path / 'data'
    data.mkdir()
    research = tmp_path / 'research'
    (research / 'upstream').mkdir(parents=True)
    footprint = np.ones((8, 8), dtype=bool)
    transform = Affine(100, 0, 0, 0, -100, 800)
    crs = rasterio.crs.CRS.from_epsg(32611)
    witness = data / 'witness.tif'
    with rasterio.open(witness, 'w', driver='GTiff', count=1, height=8, width=8,
                       dtype='float32', crs=crs, transform=transform) as dst:
        dst.write(np.full((8, 8), 0.01, dtype='float32'), 1)
    for name in ('sample_submission.tif', 'existing_faults.tif'):
        (data / name).write_bytes(b'pinned synthetic input')
    sha = protocol_preflight.digest(witness)
    inventory = research / 'upstream/registry_inventory.json'
    inventory.write_text(json.dumps({'rasters': [dict(
        sha256=sha, sources=['fixture:witness.tif'], blob='synthetic-blob')]}))
    pin = dict(repo='test/fixture', source_path='witness.tif', blob='synthetic-blob',
               dest='witness.tif', sha256=sha, bytes=witness.stat().st_size,
               registry_sha256=protocol_preflight.digest(inventory),
               registry_repository='test/registry', registry_commit='synthetic-commit',
               registry_path='inventory.json', verified_date_utc='2026-10-22')
    (research / 'registry_witness_pin.json').write_text(json.dumps(pin))
    monkeypatch.setattr(protocol_preflight, 'ROOT', tmp_path)
    monkeypatch.setattr(audit_release, 'verify_shared_pins', lambda root: {'synthetic': True})
    for name in ('SHA256_SAMPLE_SUBMISSION', 'SHA256_EXISTING_FAULTS'):
        monkeypatch.setattr(protocol_preflight.grid, name,
                            hashlib.sha256(b'pinned synthetic input').hexdigest())
    monkeypatch.setattr(protocol_preflight.grid, 'load_grid', lambda _: SimpleNamespace(
        shape=(8, 8), crs=crs, transform=transform, footprint=footprint,
        catalogue=np.zeros_like(footprint)))
    return data


@pytest.mark.parametrize('instant', ['2026-10-24T23:59:59+00:00', '2026-10-25T00:00:01+00:00'])
def test_measurement_uses_current_utc_not_witness_date(measurement_inputs, monkeypatch, instant):
    expected = datetime.fromisoformat(instant)

    class Clock:
        @staticmethod
        def now(tz):
            assert tz is timezone.utc
            return expected

    monkeypatch.setattr(protocol_preflight, 'datetime', Clock)
    result = protocol_preflight.measure(measurement_inputs)
    assert result['measured_utc'] == instant
    assert result['measured_date_utc'] == expected.date().isoformat()
    assert result['witness_verified_date_utc'] == '2026-10-22'
    assert result['universal_overlap_blocker'] is True
    assert result['candidate_generated'] is False


def test_corruption_cannot_produce_fresh_measurement(measurement_inputs, monkeypatch):
    class Clock:
        @staticmethod
        def now(tz):
            pytest.fail('Invalid inputs must stop before a completed measurement timestamp')

    monkeypatch.setattr(protocol_preflight, 'datetime', Clock)
    (measurement_inputs / 'witness.tif').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='Wrong byte length'):
        protocol_preflight.measure(measurement_inputs)


def test_pages_rebinds_receipts_after_proof_refresh():
    from pathlib import Path
    workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/pages.yml').read_text()
    assert workflow.index('python scripts/protocol_preflight.py') < workflow.index(
        'python scripts/audit_release.py --measure-registry') < workflow.index(
        'python scripts/build_site.py')
    assert '            docs/evidence/latest-review-run-card.json' in workflow
    assert '            docs/evidence/protocol-preflight.json' in workflow


def test_reproduction_ignores_only_validated_measurement_time():
    from scripts.check_preflight_reproduction import normalized
    original = dict(measured_utc='2026-10-24T23:59:59+00:00', measured_date_utc='2026-10-24',
                    witness_verified_date_utc='2026-10-22', universal_overlap_blocker=True)
    later = dict(original, measured_utc='2026-10-25T00:00:01+00:00', measured_date_utc='2026-10-25')
    assert normalized(original) == normalized(later)
    assert normalized(original) != normalized(dict(later, universal_overlap_blocker=False))
    assert normalized(original) != normalized(dict(later, witness_verified_date_utc='2026-10-23'))
    for invalid in (dict(later, measured_date_utc='2026-10-24'),
                    dict(later, measured_utc='2026-10-25T00:00:01'),
                    dict(later, measured_utc='2026-10-25T00:00:01+02:00')):
        with pytest.raises(ValueError):
            normalized(invalid)
    nested = {'correlation_overlap_vs_registry': {'universal_witness': original}}
    path = ('correlation_overlap_vs_registry', 'universal_witness')
    assert normalized(nested, path)['correlation_overlap_vs_registry']['universal_witness'] == normalized(original)
