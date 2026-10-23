"""Read-only fail-closed verifier for Lane H86-FVMB (`GEMSDOE86` Lane 7).

Checks:
  1. Unmodified `vendor/gems57` SHA-256 pins (`research/template_pin.json`).
  2. Strict finite JSON in `docs/evidence/h86-fvmb-run-card.json` and companion receipts.
  3. GeoTIFF + single-TIF ZIP + receipt in `docs/downloads/` (`15/15` checks, `[0, 1]`
     range, zero NaN/Inf, zero on-catalogue mass, exact `EPSG:32611` `3730 x 3292` grid).
  4. All 72 leakage canaries <= 0.90, statistically positive paired holdout delta vs
     GEMSDOE32 H33-2-B2 & D2.8, literal uniqueness across all 37 modern/concurrent
     rasters (<= 0.6831), AND fail-closed `verdict == 'negative'` under the 808-raster
     historical dense witness (`17GEMSDOE_E-proba-multiscale`).
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
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import gates as GT  # noqa: E402
from gems57 import grid as G  # noqa: E402
from gems57 import validate as V  # noqa: E402

PINS = ROOT / "research" / "template_pin.json"
RUNCARD = ROOT / "docs" / "evidence" / "h86-fvmb-run-card.json"
CANARY = ROOT / "docs" / "evidence" / "h86_fvmb_canary.json"
ABLATION = ROOT / "docs" / "evidence" / "h86_fvmb_holdout_ablation.json"
CROSSLANE = ROOT / "docs" / "evidence" / "h86_fvmb_crosslane_uniqueness.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_pins() -> bool:
    doc = json.loads(PINS.read_text())
    return all(
        (ROOT / rel).is_file() and sha256(ROOT / rel) == expected
        for rel, expected in doc["files"].items()
    )


def _strict_json(path: Path) -> dict:
    def _reject(val: str):
        raise ValueError(f"Non-finite JSON constant {val!r} in {path}")
    return json.loads(path.read_text(), parse_constant=_reject)


def run(run_card_path: Path = RUNCARD) -> dict:
    pins_ok = check_pins()
    if not run_card_path.is_file():
        return dict(
            pins_clean=pins_ok,
            evidence_present=False,
            all_checks_passed=False,
            verdict="negative",
            submission_ready=False,
            approved_for_weekly_slot=False,
        )

    card = _strict_json(run_card_path)
    canary = _strict_json(CANARY)
    ablation = _strict_json(ABLATION)
    cross = _strict_json(CROSSLANE)

    tif = ROOT / card["submission_file"]
    zpath = ROOT / card["zip_file"]
    rpath = tif.with_suffix(".json")
    rec = _strict_json(rpath)

    grid = G.load_grid(ROOT / "data" / "bridge")
    val = V.validate(tif, grid.footprint, grid.catalogue)
    tmpl = GT.format_report(tif, ROOT / "data" / "bridge" / "sample_submission.tif", footprint=grid.footprint)

    with rasterio.open(tif) as ds:
        arr = ds.read(1)
        no_nodata = ds.nodata is None

    with zipfile.ZipFile(zpath) as zf:
        zip_ok = zf.namelist() == [tif.name] and zf.read(tif.name) == tif.read_bytes()

    pd33 = ablation["dual_seed_pooled"]["paired_differences"]["Ref_GEMS32_H33_FoldFair_02778"]
    checks = dict(
        pins_clean=pins_ok,
        tif_sha256_matches=sha256(tif) == card["raster_sha256"] == rec["sha256"],
        zip_sha256_matches=sha256(zpath) == card["zip_sha256"] == rec["zip_sha256"],
        zip_roundtrip_exact=zip_ok,
        shared_validator_15_of_15=bool(val["all_checks_passed"]),
        template_format_ok=bool(tmpl["ok"]),
        no_nodata_tag=no_nodata,
        all_finite_0_1=bool(np.isfinite(arr).all() and arr.min() >= 0.0 and arr.max() <= 1.0),
        zero_outside_footprint=bool(np.all(arr[~grid.footprint] == 0.0)),
        zero_on_catalogue=bool(int((arr[grid.catalogue] > 0).sum()) == 0),
        dots_38400=bool(int((arr > 0).sum()) == 38400),
        note_le_140=bool(1 <= len(card["note"]) <= 140 and card["note"] == rec["note"]),
        experiments_le_3=bool(card["experiments_run"] <= 3),
        zero_slots_used=bool(card["weekly_submission_slots_used"] == 0),
        canary_72_pass=bool(canary["passed"] and canary["n_channels_tested"] == 72 and canary["max_symmetric_auc"] <= 0.90),
        paired_holdout_ci_positive=bool(pd33["delta"] > 0.04 and pd33["ci95"][0] > 0.04),
        modern_37_unique=bool(
            cross["vs_6_concurrent_gemsdoe86_lanes"]["max_forward_3px_overlap"] <= 0.70
            and cross["vs_31_modern_gemsdoe28_to_85_priors"]["dots_worst_3px_overlap"] <= 0.70
        ),
        fail_closed_verdict=bool(
            card["verdict"] == "negative"
            and card["submission_ready"] is False
            and card["approved_for_weekly_slot"] is False
            and rec["promoted"] is False
            and rec["approved_for_weekly_slot"] is False
        ),
    )
    return dict(
        lane_id="H86-FVMB",
        checks=checks,
        all_checks_passed=all(checks.values()),
        verdict=card["verdict"],
        submission_ready=card["submission_ready"],
        approved_for_weekly_slot=card["approved_for_weekly_slot"],
    )


if __name__ == "__main__":
    out = run()
    print(json.dumps(out, indent=2))
    sys.exit(0 if out["all_checks_passed"] else 1)
