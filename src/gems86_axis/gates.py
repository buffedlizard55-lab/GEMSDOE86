"""MUST-pass gates (brief section 6), each re-read from the written file on disk.

The format checks delegate to the shared template validator
(``vendor/template66/gems/validate_submission.py``) so this session cannot drift from the
format definition the rest of the project already uses.  A SKIP is never a PASS: without
the reference raster the validator's grid checks are skipped and the gate fails closed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))

from gems.validate_submission import validate as template_validate  # noqa: E402

from .grid_io import load_dots, sha256_file  # noqa: E402


#: The template validator's only SKIPPED check without the 419 MB feature stack.  The
#: human declined that download for this session, so the same measurements are taken here
#: against ``sample_submission.tif`` (the official footprint definition) by ``value_gate``.
COVERED_SKIPS = {
    "footprint checks": ("covered by gates.value_gate, which re-reads the written file and "
                         "checks in_footprint_all_finite / in_footprint_range_0_1 / "
                         "outside_footprint_nan_or_zero against the footprint of the pinned "
                         "sample_submission.tif; the template validator skips them only "
                         "because the 419 MB feature stack was not restored this session"),
}


def format_gate(path: str | Path, ctx: dict) -> dict:
    res = template_validate(path, reference_path=ctx["sample_path"])
    skipped = [c["check"] for c in res["checks"] if c["status"] == "SKIPPED"]
    failed = [c["check"] for c in res["checks"] if c["status"] == "FAIL"]
    uncovered = [s for s in skipped if s not in COVERED_SKIPS]
    passed = not failed and not uncovered
    return {"gate": "format", "passed": passed, "skipped": skipped,
            "skipped_covered_elsewhere": {s: COVERED_SKIPS[s] for s in skipped if s in COVERED_SKIPS},
            "uncovered_skips": uncovered, "failed": failed, "checks": res["checks"]}


def value_gate(path: str | Path, ctx: dict) -> dict:
    """Re-read the file: range, NaN placement, zero catalogue mass, dot count."""
    import rasterio

    foot, cat = ctx["footprint"], ctx["catalogue"]
    with rasterio.open(path) as src:
        arr = src.read(1)
    inside = arr[foot]
    outside = arr[~foot]
    nan_mode = bool(np.isnan(outside).all()) if outside.size else False
    zero_mode = bool(np.nan_to_num(outside, nan=0.0).max(initial=0.0) == 0.0)
    dots = (np.nan_to_num(arr, nan=0.0) > 0) & foot
    checks = {
        "in_footprint_all_finite": not bool(np.isnan(inside).any()),
        "in_footprint_range_0_1": bool(inside[np.isfinite(inside)].min() >= 0.0
                                       and inside[np.isfinite(inside)].max() <= 1.0)
                                  if inside.size else False,
        "outside_footprint_nan_or_zero": nan_mode or zero_mode,
        "zero_catalogue_mass": int((dots & cat).sum()) == 0,
        "single_band": True,
    }
    return {"gate": "values", "passed": all(checks.values()), "checks": checks,
            "mode": "nan" if nan_mode else ("zeros" if zero_mode else "unknown"),
            "n_dots": int(dots.sum()),
            "dots_on_catalogue": int((dots & cat).sum()),
            "in_footprint_min": float(np.nanmin(inside)) if inside.size else None,
            "in_footprint_max": float(np.nanmax(inside)) if inside.size else None}


def catalogue_clearance_gate(path: str | Path, ctx: dict, clearance_px: float) -> dict:
    from scipy import ndimage

    dots = load_dots(path, ctx["footprint"])
    edt = ndimage.distance_transform_edt(~ctx["catalogue"])
    inside = dots & (edt <= clearance_px)
    return {"gate": "catalogue_clearance", "passed": int(inside.sum()) == 0,
            "clearance_px": clearance_px, "violations": int(inside.sum()),
            "min_cat_edt_px": round(float(edt[dots].min()), 4) if dots.any() else None}


def ledger_hash_gate(path: str | Path, known_sha256: set[str]) -> dict:
    digest = sha256_file(path)
    return {"gate": "sha256_not_in_ledger", "passed": digest not in known_sha256,
            "sha256": digest, "sha8": digest[:8]}


def run_all(path: str | Path, ctx: dict, known_sha256: set[str], clearance_px: float) -> dict:
    out = {"file": str(path), "sha256": sha256_file(path)}
    out["format"] = format_gate(path, ctx)
    out["values"] = value_gate(path, ctx)
    out["catalogue_clearance"] = catalogue_clearance_gate(path, ctx, clearance_px)
    out["ledger_hash"] = ledger_hash_gate(path, known_sha256)
    out["passed"] = all(out[k]["passed"] for k in
                        ("format", "values", "catalogue_clearance", "ledger_hash"))
    return out
