"""Synthetic provenance regression; not a model experiment or holdout score."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from scripts import protocol_preflight


@pytest.mark.parametrize('instant', [
    datetime(2026, 10, 24, 23, 59, 59, tzinfo=timezone.utc),
    datetime(2026, 10, 25, 0, 0, 0, tzinfo=timezone.utc),
])
def test_measurement_uses_current_utc_not_historical_snapshot(instant):
    footprint = np.ones((2, 2), dtype=bool)
    grid = SimpleNamespace(shape=(2, 2), crs='synthetic-crs',
                           transform='synthetic-transform', footprint=footprint,
                           catalogue=np.zeros_like(footprint))
    source = MagicMock()
    source.shape, source.crs, source.transform, source.count = (
        grid.shape, grid.crs, grid.transform, 1)
    source.read_masks.return_value = footprint.astype('uint8') * 255
    source.read.return_value = footprint.astype('float32') * .5
    source.__enter__.return_value = source
    with (patch('scripts.audit_release.verify_shared_pins', return_value={'synthetic': True}),
          patch.object(protocol_preflight, 'verify_file') as verify,
          patch.object(protocol_preflight.grid, 'load_grid', return_value=grid),
          patch.object(protocol_preflight.rasterio, 'open', return_value=source),
          patch.object(protocol_preflight, 'saturation_certificate',
                       return_value={'universal_overlap_blocker': True}),
          patch.object(protocol_preflight, 'datetime') as clock):
        clock.now.return_value = instant
        result = protocol_preflight.measure()
    clock.now.assert_called_once_with(timezone.utc)
    # Competition grid and witness are mirrored under data/bridge; a canonical
    # historical-witness archive is retained separately under data/registry.
    assert verify.call_args_list[1].args[0] == protocol_preflight.ROOT / 'data/bridge/sample_submission.tif'
    assert verify.call_args_list[3].args[0] == protocol_preflight.ROOT / 'data/bridge/registry/dense-witness.tif'
    assert result['measured_utc'] == instant.isoformat()
    assert result['measured_date_utc'] == instant.date().isoformat()
    assert result['status'] == 'STOP_LITERAL_OVERLAP_UNSATISFIABLE'
    assert result['candidate_generated'] is False
    assert result['registry_complete'] is False
    assert result['direct_support_uncovered_allowed_pixels'] == 0


def test_reproduction_ignores_only_valid_measurement_time():
    from scripts.check_preflight_reproduction import content
    base = {'measured_date_utc': '2026-10-22', 'universal_overlap_blocker': True}
    current = {**base, 'measured_date_utc': '2026-10-25',
               'measured_utc': '2026-10-25T00:00:00+00:00'}
    assert content(base) == content(current)
    assert content(base) != content({**current, 'universal_overlap_blocker': False})
    for invalid in ('2026-10-24T23:59:59+00:00', '2026-10-25T00:00:00',
                    '2026-10-25T00:00:00+01:00'):
        with pytest.raises(ValueError):
            content({**current, 'measured_utc': invalid})
