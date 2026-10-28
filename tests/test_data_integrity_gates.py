"""No fitting: fail closed on misaligned inputs and incomplete/corrupt archives."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import subprocess
import tarfile

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

from scripts import prepare_data as prepare
from scripts import restore_data as restore


TRANSFORM = Affine(100, 0, 243350, 0, -100, 4508550)


def write_tif(path, values, *, crs="EPSG:32611", transform=TRANSFORM):
    values = np.asarray(values, dtype="float32")
    if values.ndim == 2:
        values = values[None]
    with rasterio.open(path, "w", driver="GTiff", height=values.shape[1], width=values.shape[2],
                       count=len(values), dtype="float32", crs=crs, transform=transform) as dst:
        dst.write(values)
        if path.name == "training_features.tif" and len(values) == len(prepare.BANDS):
            for index, band_name in prepare.BANDS.items():
                dst.set_band_description(index, f"{band_name} - synthetic fixture")


@pytest.fixture
def tiny_data(tmp_path, monkeypatch):
    data = tmp_path / "inputs"
    data.mkdir()
    shape = (6, 7)
    labels = np.zeros(shape, np.float32)
    labels[2, 3] = 1
    write_tif(data / "sample_submission.tif", np.ones(shape, np.float32))
    write_tif(data / "existing_faults.tif", labels)
    write_tif(data / "training_features.tif", np.ones((19, *shape), np.float32))
    monkeypatch.setattr(prepare, "EXPECTED_SHAPE", shape)
    monkeypatch.setattr(prepare, "EXPECTED_FOOTPRINT_PIXELS", int(np.prod(shape)))
    monkeypatch.setattr(prepare, "EXPECTED_CATALOGUE_PIXELS", 1)
    monkeypatch.setattr(prepare, "PINS", {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in data.glob("*.tif")
    })
    return data, tmp_path / "work", tmp_path / "manifest.json"


def run_prepare(paths):
    data, work, manifest = paths
    return prepare.prepare(data_dir=data, work_dir=work, manifest_path=manifest)


@pytest.mark.parametrize("name", ["sample_submission", "existing_faults", "training_features"])
@pytest.mark.parametrize("defect", ["crs", "transform", "count", "shape"])
def test_all_input_grids_are_checked_before_any_cache_output(tiny_data, name, defect):
    data, work, manifest = tiny_data
    path = data / f"{name}.tif"
    with rasterio.open(path) as src:
        values = src.read()
    kwargs = {}
    if defect == "crs":
        kwargs["crs"] = "EPSG:4326"
    elif defect == "transform":
        kwargs["transform"] = TRANSFORM @ Affine.translation(1, 0)
    elif defect == "count":
        values = values[:1] if name == "training_features" else np.repeat(values, 2, axis=0)
    else:
        values = values[:, :-1]
    write_tif(path, values, **kwargs)
    with pytest.raises(ValueError):
        run_prepare(tiny_data)
    assert not work.exists()
    assert not manifest.exists()


@pytest.mark.parametrize("descriptions", ["swapped", "missing", "mislabeled"])
def test_band_names_must_match_native_schema_before_preparation(tiny_data, monkeypatch, descriptions):
    data, work, manifest = tiny_data
    path = data / "training_features.tif"
    with rasterio.open(path, "r+") as dst:
        if descriptions == "swapped":
            fifth, twelfth = dst.descriptions[4], dst.descriptions[11]
            dst.set_band_description(5, twelfth)
            dst.set_band_description(12, fifth)
        elif descriptions == "missing":
            dst.set_band_description(16, "")
        else:
            dst.set_band_description(16, "mt_resistivity_2km - misleading label")
    # Repin the synthetic fixture so this specifically tests the schema gate.
    monkeypatch.setitem(prepare.PINS, "training_features.tif", hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="band identifiers"):
        run_prepare(tiny_data)
    assert not work.exists() and not manifest.exists()


def test_pin_mismatch_is_not_a_successful_manifest_with_a_false_flag(tiny_data):
    data, work, manifest = tiny_data
    path = data / "training_features.tif"
    with rasterio.open(path, "r+") as dst:
        values = dst.read(1)
        values[0, 0] = 100
        dst.write(values, 1)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        run_prepare(tiny_data)
    assert not work.exists() and not manifest.exists()


def test_valid_preparation_records_each_grid_and_does_not_claim_shared_cache(tiny_data):
    result = run_prepare(tiny_data)
    assert result["counts"]["has_features"]
    assert result["pins_verified"] == dict(sample_submission=True, existing_faults=True, training_features=True)
    assert len(result["bands"]) == 19
    assert result["shared_template_feature_stack"] is False
    assert set(result["input_grid_checks"]) == {"sample_submission", "existing_faults", "training_features"}
    assert all(row["crs_shape_transform_match"] is True for row in result["input_grid_checks"].values())
    assert not tiny_data[2].with_suffix(".json.partial").exists()


def test_binary_labels_and_validity_masks_are_not_silently_repaired(tiny_data):
    data, work, manifest = tiny_data
    with rasterio.open(data / "existing_faults.tif", "r+") as dst:
        values = dst.read(1)
        values[0, 0] = 0.5
        dst.write(values, 1)
    with pytest.raises(ValueError, match="already be binary"):
        run_prepare(tiny_data)
    assert not work.exists() and not manifest.exists()


def test_fetch_uses_requested_destination_and_propagates_failure(tmp_path, monkeypatch):
    commands = []

    def failed(command, **kwargs):
        commands.append((command, kwargs))
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(prepare.subprocess, "run", failed)
    data = tmp_path / "elsewhere"
    with pytest.raises(subprocess.CalledProcessError):
        prepare.prepare(data_dir=data, work_dir=tmp_path / "work", fetch_if_missing=True)
    command, kwargs = commands[0]
    assert command[-2:] == ["--dest", str(data.resolve())]
    assert kwargs["check"] is True
    assert not (tmp_path / "work").exists()


def archive(members):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w:gz") as bundle:
        for name, payload in members:
            member = tarfile.TarInfo("repo/" + name)
            member.size = len(payload)
            bundle.addfile(member, io.BytesIO(payload))
    return raw.getvalue()


def mock_archive(monkeypatch, members):
    raw = archive(members)
    monkeypatch.setattr(restore.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(raw))


@pytest.mark.parametrize("defect", ["bad_hash", "missing", "duplicate"])
def test_archive_failure_leaves_all_existing_targets_untouched(tmp_path, monkeypatch, defect):
    members = [("data/a.tif", b"new-a"), ("data/b.tif", b"new-b")]
    if defect == "bad_hash":
        members[1] = ("data/b.tif", b"tampered")
    elif defect == "missing":
        members.pop()
    else:
        members.append(members[0])
    mock_archive(monkeypatch, members)
    wanted = {f"data/{name}.tif": tmp_path / f"{name}.tif" for name in ("a", "b")}
    for path in wanted.values():
        path.write_bytes(b"pre-existing")
    pins = {f"data/{name}.tif": hashlib.sha256(f"new-{name}".encode()).hexdigest() for name in ("a", "b")}
    with pytest.raises(ValueError):
        restore.stream_extract("https://codeload.github.com/test", wanted, expected_sha256=pins)
    assert all(path.read_bytes() == b"pre-existing" for path in wanted.values())
    assert not list(tmp_path.glob("*.partial"))


def test_archive_publication_requires_complete_hash_mapping_and_unique_destinations(tmp_path, monkeypatch):
    path = tmp_path / "a.tif"
    mock_archive(monkeypatch, [("data/a.tif", b"new-a")])
    with pytest.raises(ValueError, match="exactly"):
        restore.stream_extract("https://codeload.github.com/test", {"data/a.tif": path}, expected_sha256={})
    with pytest.raises(ValueError, match="distinct"):
        restore.stream_extract("https://codeload.github.com/test", {"data/a.tif": path, "data/b.tif": path})
    assert not path.exists()


def test_archive_success_publishes_verified_bytes_and_ignores_unrequested_paths(tmp_path, monkeypatch):
    mock_archive(monkeypatch, [("../../escape", b"ignored"), ("data/a.tif", b"new-a")])
    path = tmp_path / "a.tif"
    restore.stream_extract("https://codeload.github.com/test", {"data/a.tif": path},
                           expected_sha256={"data/a.tif": hashlib.sha256(b"new-a").hexdigest()})
    assert path.read_bytes() == b"new-a"
    assert list(tmp_path.iterdir()) == [path]


def test_native_cache_receipt_binds_the_complete_array_set(tiny_data):
    result = run_prepare(tiny_data)
    assert len(result["prepared_arrays"]) == 21
    for record in result["prepared_arrays"]:
        path = Path(record["file"])
        if not path.is_absolute():
            path = prepare.ROOT / path
        assert path.stat().st_size == record["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    assert result["publication"]["complete_array_set_staged"] is True
    assert result["publication"]["rollback_on_exception"] is True
    assert result["publication"]["crash_atomic_across_cache_and_manifest"] is False


@pytest.mark.parametrize("old_cache", [False, True])
@pytest.mark.parametrize("failure", ["array_write", "source_mutation", "cache_replace", "manifest_replace"])
def test_preparation_failure_never_publishes_a_partial_or_mixed_generation(tiny_data, monkeypatch, old_cache, failure):
    data, work, manifest = tiny_data
    if old_cache:
        run_prepare(tiny_data)
    before = {p.name: p.read_bytes() for p in (work / "bands").glob("*")}
    before_manifest = manifest.read_bytes() if manifest.exists() else None
    original_save = prepare.np.save
    original_replace = prepare.os.replace
    failed = False

    def save(path, values):
        nonlocal failed
        if not failed and failure == "array_write":
            failed = True
            raise OSError("injected array write failure")
        original_save(path, values)
        if not failed and failure == "source_mutation":
            failed = True
            source = data / "training_features.tif"
            source.write_bytes(source.read_bytes() + b"changed while preparing")

    def replace(src, dst):
        nonlocal failed
        if not failed and ((failure == "manifest_replace" and Path(dst) == manifest) or
                           (failure == "cache_replace" and Path(dst) == work / "bands")):
            failed = True
            raise OSError("injected publication failure")
        return original_replace(src, dst)

    monkeypatch.setattr(prepare.np, "save", save)
    monkeypatch.setattr(prepare.os, "replace", replace)
    with pytest.raises((OSError, ValueError)):
        run_prepare(tiny_data)
    assert failed
    assert {p.name: p.read_bytes() for p in (work / "bands").glob("*")} == before
    assert (manifest.read_bytes() if manifest.exists() else None) == before_manifest
    assert not list(work.glob(".native-bands-*"))
    assert not list(manifest.parent.glob("*.partial"))


def test_later_grid_only_preparation_does_not_leave_stale_native_feature_arrays(tiny_data):
    run_prepare(tiny_data)
    (tiny_data[0] / "training_features.tif").unlink()
    result = run_prepare(tiny_data)
    assert result["counts"]["has_features"] is False
    assert result["bands"] == []
    assert {p.name for p in (tiny_data[1] / "bands").iterdir()} == {"_labels.npy", "_footprint.npy"}
    assert len(result["prepared_arrays"]) == 2


@pytest.mark.parametrize("failure", ["bad_serialization", "staging_mutation", "publication_mutation"])
def test_prepared_array_content_or_pin_mismatch_rolls_back(tiny_data, monkeypatch, failure):
    data, work, manifest = tiny_data
    run_prepare(tiny_data)
    before = {p.name: p.read_bytes() for p in (work / "bands").glob("*")}
    before_manifest = manifest.read_bytes()
    original_save = prepare.np.save
    original_replace = prepare.os.replace
    injected = False

    def save(path, values):
        nonlocal injected
        if not injected and failure == "bad_serialization" and Path(path).name == "01_mag_anom.npy":
            bad = np.array(values, copy=True)
            bad[0, 0] += 1
            original_save(path, bad)
            injected = True
        else:
            original_save(path, values)
            if not injected and failure == "staging_mutation" and Path(path).name == "02_rtp.npy":
                prior = Path(path).parent / "01_mag_anom.npy"
                array = np.load(prior, mmap_mode="r+")
                array[0, 0] += 1
                array.flush()
                del array
                injected = True

    def replace(src, dst):
        nonlocal injected
        result = original_replace(src, dst)
        if not injected and failure == "publication_mutation" and Path(dst) == work / "bands":
            array = np.load(Path(dst) / "01_mag_anom.npy", mmap_mode="r+")
            array[0, 0] += 1
            array.flush()
            del array
            injected = True
        return result

    monkeypatch.setattr(prepare.np, "save", save)
    monkeypatch.setattr(prepare.os, "replace", replace)
    with pytest.raises(ValueError, match="readback mismatch|changed during staging|changed during publication"):
        run_prepare(tiny_data)
    assert injected
    assert {p.name: p.read_bytes() for p in (work / "bands").glob("*")} == before
    assert manifest.read_bytes() == before_manifest
