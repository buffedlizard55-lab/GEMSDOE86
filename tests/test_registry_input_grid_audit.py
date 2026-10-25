"""A complete byte download cannot silently discard invalid registry grids."""
import hashlib
from types import SimpleNamespace

import numpy as np
import pytest
import rasterio
from affine import Affine

from scripts.audit_registry_inputs import inspect_record


@pytest.mark.parametrize("defect", [None, "shape", "crs", "transform", "bands", "hash", "bytes", "missing"])
def test_grid_audit_preserves_incompatible_records(tmp_path, defect):
    path = tmp_path / "prior.tif"
    tr = Affine(100, 0, 243350, 0, -100, 4508550)
    crs = rasterio.crs.CRS.from_epsg(32611)
    reference = SimpleNamespace(shape=(6, 7), transform=tr, crs=crs)
    with rasterio.open(path, "w", driver="GTiff", height=5 if defect == "shape" else 6, width=7,
                       count=2 if defect == "bands" else 1, dtype="float32",
                       crs="EPSG:4326" if defect == "crs" else crs,
                       transform=tr @ Affine.translation(1, 0) if defect == "transform" else tr) as dst:
        dst.write(np.zeros((dst.count, dst.height, dst.width), np.float32))
    record = dict(cache_file=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  bytes=path.stat().st_size, sources=["test:prior.tif"], repo_first="test")
    if defect == "hash":
        record["sha256"] = "0" * 64
    elif defect == "bytes":
        record["bytes"] += 1
    elif defect == "missing":
        path.unlink()
    row = inspect_record(record, reference)
    assert row["sha256"] == record["sha256"] and row["sources"] == record["sources"]
    assert row["probability_values_checked"] is False
    assert row["grid_compatible"] is (defect is None)
    if defect in {"hash", "bytes", "missing"}:
        assert row["status"] == "INVALID_INPUT" and row["bytes_verified"] is False
    elif defect is not None:
        assert row["status"] == "GRID_INCOMPATIBLE_DO_NOT_EXCLUDE"
        assert row["bytes_verified"] is True
    else:
        assert row["status"] == "GRID_COMPATIBLE_VALUES_NOT_AUDITED"
