"""ARTIFACT-FORENSIC-IDENTITY checks only; never a score explanation or HOLDOUT-DTI."""
from hashlib import sha256
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
H33 = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
H36 = ROOT / "data/scored_fleet/GEMSDOE36__gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif"
CATALOGUE = ROOT / "data/bridge/existing_faults.tif"
EXPECTED_SHA256 = {
    PARENT: "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
    H33: "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    H36: "e15891020b9c57056ac7fa874a5e506fbd6ed9314a4ea8e73af0753887a3708a",
    CATALOGUE: "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
}


def _read_positive(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as dataset:
        return dataset.read(1) > 0, {
            "crs": dataset.crs,
            "transform": dataset.transform,
            "shape": dataset.shape,
            "count": dataset.count,
        }


def test_h33_is_exactly_parent_after_two_pixel_catalogue_collar_pruning():
    """Confirms raster ancestry only; the supplied 0.2778 remains OWNER-REPORTED."""
    for path, expected in EXPECTED_SHA256.items():
        assert sha256(path.read_bytes()).hexdigest() == expected

    with rasterio.open(PARENT) as dataset:
        parent_values = dataset.read(1)
        parent_profile = (dataset.crs, dataset.transform, dataset.shape, dataset.count)
    parent = np.isfinite(parent_values) & (parent_values > 0)

    with rasterio.open(CATALOGUE) as dataset:
        catalogue = dataset.read(1) > 0
        catalogue_profile = (dataset.crs, dataset.transform, dataset.shape, dataset.count)
    with rasterio.open(H33) as dataset:
        h33 = dataset.read(1) > 0
        h33_profile = (dataset.crs, dataset.transform, dataset.shape, dataset.count)

    assert parent_profile == h33_profile == catalogue_profile
    assert parent_profile[0].to_epsg() == 32611
    assert parent_profile[2] == (3730, 3292)
    assert parent_profile[3] == 1

    catalogue_distance_px = distance_transform_edt(~catalogue)
    expected_h33 = parent & (catalogue_distance_px > 2.0)
    assert np.array_equal(h33, expected_h33)
    assert not np.any(h33 & ~parent)
    assert int(parent.sum()) == 40199
    assert int(h33.sum()) == 37654
    assert int((parent & ~h33).sum()) == 2545
    assert int((parent & ~h33 & (catalogue_distance_px <= 2.0)).sum()) == 2545


def test_gemsdoe36_contains_h33_plus_1200_pixels_without_scoring_inference():
    h33, h33_profile = _read_positive(H33)
    h36, h36_profile = _read_positive(H36)
    assert h36_profile == h33_profile
    assert int(h36.sum()) == 38854
    assert np.all(h36[h33])
    assert int((h36 & ~h33).sum()) == 1200
