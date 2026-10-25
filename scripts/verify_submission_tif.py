#!/usr/bin/env python3
"""Independent, no-human-intervention re-verification of the promoted submission TIFF.

Checks, from disk bytes only:
  * TIFF SHA-256 matches the writer receipt sidecar
  * the one-TIFF ZIP contains exactly that TIFF and matches its sidecar SHA
  * single-band float32 GeoTIFF, EPSG:32611, 3730x3292, sample-submission transform
  * finite values in [0, 1], exactly {0, 1}, 55,000 positive pixels, 0 NaN/Inf

Exits non-zero on any failure. Intended for CI / pre-submit gating, not as a
substitute for the organizer's submission-page acceptance.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
TIFF = ROOT / "docs/downloads/gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.tif"
ZIP = ROOT / "docs/downloads/gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.zip"
RECEIPT = ROOT / "docs/downloads/gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.json"

EXPECTED_TIF_SHA = "ba8b731fead02eb27ab30c1d2c2add78f3f703325a3b29316cdfdc3183489e8d"
EXPECTED_ZIP_SHA = "51fcf074ec42c5db1720fe5d6ae2b743cda2dda853e91b9797ced25073c6a3e9"
EXPECTED_SHAPE = (3730, 3292)
EXPECTED_CRS = "EPSG:32611"
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
EXPECTED_POSITIVES = 55000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    failures: list[str] = []
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    # 1. Sidecar names the promoted file and declares the gate verdict.
    if receipt.get("gate_verdict") != "promote":
        failures.append(f"gate_verdict={receipt.get('gate_verdict')} != promote")
    if receipt.get("submission_name") != "gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros":
        failures.append("submission_name mismatch in receipt")
    if len(receipt.get("note", "")) > 140:
        failures.append("note exceeds 140 characters")

    # 2. TIFF bytes match the pinned digest (guards against silent bit rot /
    #    re-labeling of an old raster as a new submission).
    tif_sha = sha256(TIFF)
    print(f"TIFF sha256: {tif_sha}")
    if tif_sha != EXPECTED_TIF_SHA:
        failures.append(f"TIFF sha256 mismatch: {tif_sha}")
    if receipt.get("sha256") != tif_sha:
        failures.append("receipt sha256 != on-disk TIFF sha256")

    # 3. ZIP is a one-TIFF container whose inner TIFF is byte-identical.
    zip_sha = sha256(ZIP)
    print(f"ZIP sha256: {zip_sha}")
    if zip_sha != EXPECTED_ZIP_SHA:
        failures.append(f"ZIP sha256 mismatch: {zip_sha}")
    if receipt.get("zip_sha256") != zip_sha:
        failures.append("receipt zip_sha256 != on-disk ZIP sha256")
    with zipfile.ZipFile(ZIP) as archive:
        names = archive.namelist()
        print(f"ZIP entries: {names}")
        if names != [TIFF.name]:
            failures.append(f"ZIP must contain exactly one TIFF ({TIFF.name}); got {names}")
        with archive.open(TIFF.name) as inner:
            inner_sha = hashlib.file_digest(inner, "sha256").hexdigest()
        if inner_sha != EXPECTED_TIF_SHA:
            failures.append(f"ZIP-internal TIFF sha256 mismatch: {inner_sha}")

    # 4. On-disk raster decode (the "Predicted values must be in range [0, 1]"
    #    portal error class is excluded by construction).
    with rasterio.open(TIFF) as src:
        profile_ok = (
            src.count == 1
            and src.dtypes[0] == "float32"
            and (src.width, src.height) == (EXPECTED_SHAPE[1], EXPECTED_SHAPE[0])
            and str(src.crs) == EXPECTED_CRS
            and (src.transform.a, src.transform.b, src.transform.c,
                 src.transform.d, src.transform.e, src.transform.f) == EXPECTED_TRANSFORM
        )
        print(f"profile: count={src.count} dtype={src.dtypes[0]} "
              f"shape={src.height}x{src.width} crs={src.crs} "
              f"transform=({src.transform.a},{src.transform.b},{src.transform.c},"
              f"{src.transform.d},{src.transform.e},{src.transform.f})")
        if not profile_ok:
            failures.append("CRS/shape/dtype/band-count/transform mismatch")
        arr = src.read(1)
        finite = np.isfinite(arr)
        n_nan = int(np.isnan(arr).sum())
        n_inf = int(np.isinf(arr).sum())
        vmin = float(np.nanmin(arr))
        vmax = float(np.nanmax(arr))
        uniq = np.unique(arr)
        n_pos = int((arr == 1.0).sum())
        print(f"finite={bool(finite.all())} n_nan={n_nan} n_inf={n_inf} "
              f"min={vmin} max={vmax} unique={uniq.tolist()} positives={n_pos}")
        if not finite.all():
            failures.append("non-finite pixels present")
        if vmin < 0.0 or vmax > 1.0:
            failures.append(f"values outside [0, 1]: [{vmin}, {vmax}]")
        if not np.array_equal(uniq, np.array([0.0, 1.0], dtype=np.float32)):
            failures.append(f"unique values not exactly {{0,1}}: {uniq.tolist()}")
        if n_pos != EXPECTED_POSITIVES:
            failures.append(f"positive pixels {n_pos} != {EXPECTED_POSITIVES}")

    # 5. Receipt cross-checks.
    val = receipt.get("validator", {})
    if val.get("all_checks_passed") is not True:
        failures.append("receipt validator.all_checks_passed is not True")

    if failures:
        print("\nVERIFY FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nVERIFY PASSED: promoted submission TIFF is format-valid, unique by pinned digest, "
          "values exactly {0,1} with 0 NaN/Inf, CRS/shape/transform match the sample submission.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
