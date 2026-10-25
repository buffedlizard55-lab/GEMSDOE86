"""No raster construction: guard the archived prototype's scientific identity."""
import pytest
from scripts import build_unique_submission as legacy
from src.gems86.io import BANDS


def test_all_feature_identities_match_central_band_map():
    assert all(BANDS[index] == name for name, index in legacy.BANDS.items())
    assert legacy.BANDS['ieq_n100a15'] == 16
    assert 17 not in legacy.BANDS.values()  # conductivity is not seismicity
    assert set(legacy.BANDS) == set(legacy.WEIGHTS)
    assert sum(legacy.WEIGHTS.values()) == pytest.approx(1)


def test_legacy_builder_cannot_write_even_if_literal_stop_is_resolved(monkeypatch):
    from scripts import protocol_preflight
    monkeypatch.setattr(protocol_preflight, 'require_feasible', lambda: {})

    def forbidden(*args, **kwargs):
        pytest.fail('Archived pipeline reached construction or serialization')

    monkeypatch.setattr(legacy, 'build_surface', forbidden)
    monkeypatch.setattr(legacy, 'write_submission', forbidden)
    with pytest.raises(RuntimeError, match='ARCHIVED_UNSAFE_PIPELINE'):
        legacy.main()


def test_literal_stop_still_precedes_archive_guard(monkeypatch):
    from scripts import protocol_preflight

    def stop():
        raise RuntimeError('STOP_LITERAL_OVERLAP_UNSATISFIABLE')

    monkeypatch.setattr(protocol_preflight, 'require_feasible', stop)
    with pytest.raises(RuntimeError, match='STOP_LITERAL_OVERLAP_UNSATISFIABLE'):
        legacy.main()
