"""Grid loading and the two submission encodings (NaN-outside and zeros-outside).

The NaN-outside file is written by the shared template writer
(``vendor/template66/gems/submission_writer.py``) so the format-critical bytes stay the
bytes the whole project already validates.  The zeros-outside fallback twin is written
here with the identical CRS/transform/dtype and no nodata tag; the twins differ only in
how cells outside the footprint are encoded, which the ledger already shows scores
identically.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "data" / "bridge"
SAMPLE = BRIDGE / "sample_submission.tif"
CATALOGUE = BRIDGE / "existing_faults.tif"

#: measured on R0: the parent's own nearest-neighbour floor is 2*sqrt(2) px (d=2.8 thinning)
PARENT_MIN_SPACING_PX = 2.8284271247461903
#: R0's exclusion rule: no dot within 2 px of a catalogue pixel (measured floor 2.236 px)
PARENT_CAT_CLEARANCE_PX = 2.0


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_context(catalogue_path: str | Path = CATALOGUE, sample_path: str | Path = SAMPLE) -> dict:
    """Footprint, catalogue mask and the reference grid, read from the pinned bridge rasters."""
    import rasterio

    with rasterio.open(sample_path) as src:
        sample = src.read(1)
        grid = {"crs": src.crs, "transform": src.transform,
                "shape": (src.height, src.width), "dtype": str(src.dtypes[0])}
    with rasterio.open(catalogue_path) as src:
        cat = src.read(1)
    if cat.shape != sample.shape:
        raise ValueError(f"catalogue {cat.shape} != sample {sample.shape}")
    foot = np.isfinite(sample)
    return {"footprint": foot, "catalogue": cat == 1, "grid": grid,
            "sample_path": str(sample_path), "catalogue_path": str(catalogue_path)}


def dot8(mask: np.ndarray) -> str:
    """Deterministic identity token for a dot set.

    Independent of any filename or TIFF tag, so a release can carry its own token without
    the circularity of hashing a file whose tags contain the hash.  Reproducible from the
    mask alone.
    """
    import hashlib

    packed = np.packbits(np.asarray(mask, dtype=bool).astype(np.uint8).ravel())
    h = hashlib.sha256()
    h.update(np.array(np.asarray(mask).shape, dtype=np.int64).tobytes())
    h.update(packed.tobytes())
    return h.hexdigest()[:8]


def load_dots(path: str | Path, footprint: np.ndarray) -> np.ndarray:
    """Boolean dot mask from any scored encoding (NaN-outside or zeros-outside)."""
    import rasterio

    with rasterio.open(path) as src:
        arr = src.read(1)
    if arr.shape != footprint.shape:
        raise ValueError(f"{path} shape {arr.shape} != footprint {footprint.shape}")
    return (np.nan_to_num(arr, nan=0.0) > 0) & footprint


def write_pair(mask: np.ndarray, ctx: dict, out_dir: str | Path, stem: str,
               name: str, note: str, overwrite: bool = True) -> dict:
    """Write ``<stem>.tif`` (NaN outside) and ``<stem>-zeros.tif``; return both receipts."""
    import rasterio
    import sys

    sys.path.insert(0, str(ROOT / "vendor" / "template66"))
    from gems.submission_writer import write_submission  # noqa: PLC0415

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    foot = ctx["footprint"]
    pred = np.where(mask, 1.0, 0.0)

    nan_path = out_dir / f"{stem}.tif"
    nan_receipt = write_submission(nan_path, pred, foot, ctx["sample_path"],
                                   overwrite=overwrite, name=name, note=note)

    zeros_path = out_dir / f"{stem}-zeros.tif"
    with rasterio.open(ctx["sample_path"]) as ref:
        crs, transform = ref.crs, ref.transform
    out = np.zeros(ctx["grid"]["shape"], dtype=np.float32)
    out[foot] = pred[foot].astype(np.float32)
    with rasterio.open(zeros_path, "w", driver="GTiff", height=out.shape[0], width=out.shape[1],
                       count=1, dtype="float32", crs=crs, transform=transform, nodata=None,
                       compress="deflate") as dst:
        dst.write(out, 1)
        dst.update_tags(GEMS_NAME=name, GEMS_NOTE=note, GEMS_GENERATOR="gems86_axis.grid_io")
    zeros_receipt = {**{k: v for k, v in nan_receipt.items() if k not in
                        ("file", "sha256", "nan_outside_count")},
                     "file": zeros_path.name, "sha256": sha256_file(zeros_path),
                     "mode": "zeros", "nan_outside_count": 0}
    Path(str(zeros_path) + ".receipt.json").write_text(json.dumps(zeros_receipt, indent=2))
    nan_receipt["mode"] = "nan"
    return {"nan": {"path": str(nan_path), **nan_receipt},
            "zeros": {"path": str(zeros_path), **zeros_receipt}}
