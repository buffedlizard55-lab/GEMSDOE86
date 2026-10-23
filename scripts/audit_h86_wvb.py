"""Reproducible preflight and post-run evidence verifier.

- Missing evidence is ALWAYS a fail-closed negative result, never a PASS.
- Never silently clobbers `docs/evidence/run-card.json` unless `write_out` is
  explicitly passed by the caller.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

DEFAULT_RUN_CARD = ROOT / "docs" / "evidence" / "h86-wvb-run-card.json"


def check_pins() -> bool:
    pin = json.loads((ROOT / "research" / "template_pin.json").read_text())
    return all(
        (ROOT / p).is_file() and hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
        for p, h in pin["files"].items()
    )


def _preflight_grid_checks() -> tuple[dict, dict]:
    import numpy as np
    import rasterio
    from gems57 import grid

    checks = {"shared_template_hashes_match": check_pins()}
    details: dict = {}
    sample = ROOT / "data" / "sample_submission.tif"
    faults = ROOT / "data" / "existing_faults.tif"
    checks["grid_inputs_present"] = sample.is_file() and faults.is_file()
    if checks["grid_inputs_present"]:
        with sample.open("rb") as stream:
            checks["sample_mirror_sha_matches"] = (
                hashlib.file_digest(stream, "sha256").hexdigest() == grid.SHA256_SAMPLE_SUBMISSION
            )
        with faults.open("rb") as stream:
            checks["fault_mirror_sha_matches"] = (
                hashlib.file_digest(stream, "sha256").hexdigest() == grid.SHA256_EXISTING_FAULTS
            )
        with rasterio.open(sample) as s, rasterio.open(faults) as f:
            foot = np.isfinite(s.read(1)) & (s.read_masks(1) > 0)
            checks["input_grids_match"] = (
                s.count == f.count == 1
                and s.shape == f.shape == grid.SHAPE
                and s.crs == f.crs == rasterio.crs.CRS.from_epsg(grid.EPSG)
                and s.transform == f.transform == grid.TRANSFORM
            )
            details = dict(
                shape=list(s.shape),
                crs=str(s.crs),
                transform=list(s.transform)[:6],
                footprint_pixels=int(foot.sum()),
                organizer_authenticated=False,
            )
    return checks, details


def run(
    evidence_path: Path | str | None = DEFAULT_RUN_CARD,
    write_out: Path | str | None = None,
) -> dict:
    """Verify existing run-card & GeoTIFF artifact, or return fail-closed NOT_RUN card."""
    from gems57 import validate as VAL

    checks, details = _preflight_grid_checks()
    ev_path = Path(evidence_path) if evidence_path is not None else None

    if ev_path is None or not ev_path.is_file():
        blockers = [
            "No single method paragraph/lane was specified in the supplied prompt.",
            "Run-card evidence file is absent; missing evidence fails closed.",
            "No verified candidate raster or holdout receipt loaded.",
        ]
        card = dict(
            hypothesis="H86 provisional: missing run-card evidence (fail-closed)",
            mechanism="N/A — evidence file missing.",
            non_fault_mimic="Lithologic contacts and shoreline benches",
            holdout_dti=dict(
                evidence_class="HOLDOUT-DTI",
                status="NOT_RUN",
                evaluator_version="gems57-pooled-hide-v2",
                withheld_positives=None,
                value=None,
                ci95=None,
            ),
            correlation_overlap_vs_registry=dict(status="NOT_RUN", surface=None, final_dots=None, complete=False),
            raster_sha256=None,
            validator=dict(
                status="NOT_RUN_NO_CANDIDATE",
                no_nan_inside_footprint=None,
                values_in_0_1=None,
                crs_shape_transform_match=None,
            ),
            submission_name=None,
            note="No candidate verified: run-card evidence is absent; fail-closed negative verdict.",
            verdict="negative",
            submission_ready=False,
            experiments_run=0,
            preflight_checks=checks,
            input_grid=details,
            blockers=blockers,
        )
        if write_out is not None:
            Path(write_out).write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
        return card

    card = json.loads(ev_path.read_text())
    tif_rel = (card.get("artifact_paths") or {}).get("tif")
    zip_rel = (card.get("artifact_paths") or {}).get("zip")
    tif_ok = False
    zip_ok = False
    if tif_rel and (ROOT / tif_rel).is_file():
        tif_path = ROOT / tif_rel
        v_rec = VAL.validate(tif_path)
        tif_ok = bool(
            v_rec["all_checks_passed"]
            and v_rec["sha256"] == card.get("raster_sha256")
            and v_rec["n_nan"] == 0
            and v_rec["n_infinite"] == 0
            and v_rec["min"] >= 0.0
            and v_rec["max"] <= 1.0
        )
        if zip_rel and (ROOT / zip_rel).is_file():
            z_path = ROOT / zip_rel
            z_sha = hashlib.sha256(z_path.read_bytes()).hexdigest()
            with zipfile.ZipFile(z_path, "r") as zf:
                names = zf.namelist()
                zip_ok = (z_sha == card.get("zip_sha256")) and (names == [tif_path.name])

    checks["artifact_tif_verified"] = tif_ok
    checks["artifact_zip_verified"] = zip_ok
    checks["note_len_le_140"] = len(card.get("submission_note", "")) <= 140
    card["preflight_checks"] = checks
    card["submission_ready"] = bool(
        checks["shared_template_hashes_match"]
        and tif_ok
        and zip_ok
        and checks["note_len_le_140"]
        and card.get("verdict") == "promote"
    )
    if write_out is not None:
        Path(write_out).write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    return card


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
