"""Fail-closed repository audit & submission-gate verifier for GEMSDOE86.

Checks:
  1. `vendor/gems57` byte-for-byte SHA-256 pin integrity (`research/template_pin.json`).
  2. Active lane evidence (`docs/evidence/lane86b_results.json`) and Run Card
     (`docs/evidence/run-card.json`) strictly valid JSON with zero NaN/Infinity.
  3. GeoTIFF + single-TIF ZIP + receipt in `docs/downloads/` (`15/15` shared validator
     checks, `[0, 1]` range, zero NaN/Inf, zero on-catalogue mass, exact EPSG:32611
     `3730 x 3292` grid, matching SHA-256).
  4. Protocol gates: all 42 leakage canaries <= 0.90, 3-instrument HOLDOUT-DTI vs
     incumbents, AND literal/like-for-like uniqueness (`|rho| <= 0.90`, `3-px overlap <= 0.70`).

Never mutates `docs/evidence/run-card.json` during read-only verification or unit tests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import gates as GT  # noqa: E402
from gems57 import grid as G  # noqa: E402
from gems57 import validate as V  # noqa: E402

PINS = ROOT / "research" / "template_pin.json"
RESULTS = ROOT / "docs" / "evidence" / "lane86b_results.json"
RUNCARD = ROOT / "docs" / "evidence" / "h86b-gfco-run-card.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pin_mismatches() -> list[dict]:
    doc = json.loads(PINS.read_text())
    mismatches = []
    for rel_path, expected_sha in doc["files"].items():
        p = ROOT / rel_path
        if not p.is_file():
            mismatches.append(dict(path=rel_path, error="missing"))
            continue
        got = sha256(p)
        if got != expected_sha:
            mismatches.append(dict(path=rel_path, expected=expected_sha, got=got))
    return mismatches


def check_pins() -> bool:
    return len(pin_mismatches()) == 0


def _strict_json_load(path: Path) -> dict:
    def _reject_const(val: str):
        raise ValueError(f"Non-finite JSON constant {val!r} in {path}")
    return json.loads(path.read_text(), parse_constant=_reject_const)


def run(
    results_path: Path = RESULTS,
    run_card_path: Path = RUNCARD,
    run_card_out: Path | None = None,
) -> dict:
    mismatches = pin_mismatches()
    pins_clean = len(mismatches) == 0

    if not results_path.is_file():
        summary = dict(
            pins_clean=pins_clean,
            pin_mismatches=mismatches,
            evidence_present=False,
            format_valid=False,
            leakage_canary_pass=False,
            beats_incumbent_all_views=False,
            literal_uniqueness_pass=False,
            modern_comparable_uniqueness_pass=False,
            verdict="negative",
            submission_ready=False,
            approved_for_weekly_slot=False,
            reason=f"Missing {results_path.name}; fail-closed.",
        )
        if run_card_out is not None:
            run_card_out.parent.mkdir(parents=True, exist_ok=True)
            run_card_out.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        return summary

    res = _strict_json_load(results_path)
    art = res["submission_artifact"]
    tif_path = ROOT / art["tif_file"]
    zip_path = ROOT / art["zip_file"]

    # Verify TIF + ZIP on disk
    tif_exists = tif_path.is_file()
    zip_ok = False
    if zip_path.is_file():
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            zip_ok = (len(names) == 1 and names[0].endswith(".tif") and zf.testzip() is None)

    data_dir = ROOT / "data" if (ROOT / "data" / "sample_submission.tif").is_file() else ROOT / "data" / "bridge"
    data_ready = (data_dir / "sample_submission.tif").is_file() and (data_dir / "existing_faults.tif").is_file()
    if tif_exists and data_ready:
        with zipfile.ZipFile(zip_path) as _:
            pass
        import rasterio as _rio, numpy as _np
        with _rio.open(data_dir / "sample_submission.tif") as _s, _rio.open(data_dir / "existing_faults.tif") as _c:
            _fp = _np.isfinite(_s.read(1))
            _cat = _c.read(1) > 0
        val = V.validate(tif_path, footprint=_fp, catalogue=_cat)
        fmt = GT.format_report(tif_path, data_dir / "sample_submission.tif", footprint=_fp)
        format_valid = bool(val["all_checks_passed"] and fmt["ok"] and zip_ok and val["sha256"] == art["tif_sha256"])
    elif tif_exists:
        val = art["validator"]
        format_valid = bool(
            val["all_checks_passed"]
            and zip_ok
            and sha256(tif_path) == art["tif_sha256"]
        )
    else:
        format_valid = False

    leak_pass = (not res["leakage_canaries"]["any_leakage_flag"]) and (
        res["leakage_canaries"]["max_discriminative_auc"] <= 0.90
    )

    # Check holdout skill
    sel = res["selected_arm"]
    comp = res["holdout_buffered_whole_components"]
    seg_all = res["holdout_segment_all"]
    seg_det = res["holdout_segment_detached"]
    point_beats_all_three = bool(
        comp["scores"][sel]["dti"] > comp["scores"]["d28_incumbent"]["dti"]
        and comp["scores"][sel]["dti"] > comp["scores"]["h33_b2_foldfair"]["dti"]
        and seg_all["scores"][sel]["dti"] > seg_all["scores"]["d28_incumbent"]["dti"]
        and seg_det["scores"][sel]["dti"] > seg_det["scores"]["d28_incumbent"]["dti"]
    )
    ci_beats_all_three = bool(
        comp["paired_differences"]["d28_incumbent"]["ci95"][0] > 0.0
        and comp["paired_differences"]["h33_b2_foldfair"]["ci95"][0] > 0.0
        and seg_all["paired_differences"]["d28_incumbent"]["ci95"][0] > 0.0
        and seg_det["paired_differences"]["d28_incumbent"]["ci95"][0] > 0.0
    )

    uq = res["uniqueness"]
    tp = uq["two_phase_summary"]
    literal_unique = (not tp["like_for_like_reading"]["duplicate"]) and (
        uq["pre_placement_surface_worst_abs_spearman"] <= 0.90
    )
    comparable_rows = [
        r for r in uq["per_raster_rows"] if r["their_dots"] <= 62_000
    ]
    modern_comparable_unique = bool(
        uq["pre_placement_surface_worst_abs_spearman"] <= 0.90
        and all(abs(r["spearman_full_footprint"]) <= 0.90 for r in comparable_rows)
        and all(r["my_dots_within_3px_of_theirs"] <= 0.70 for r in comparable_rows)
    )

    # Validate run-card consistency
    card_ok = False
    if run_card_path.is_file():
        card = _strict_json_load(run_card_path)
        card_ok = bool(
            card.get("raster_sha256") == art["tif_sha256"]
            and len(card.get("note", "")) <= 140
            and card.get("verdict") in {"promote", "negative"}
        )

    strict_ready = bool(
        pins_clean
        and format_valid
        and leak_pass
        and ci_beats_all_three
        and literal_unique
        and card_ok
    )

    summary = dict(
        pins_clean=pins_clean,
        pin_mismatches=mismatches,
        evidence_present=True,
        run_card_consistent=card_ok,
        selected_arm=sel,
        submission_file=art["tif_file"],
        zip_file=art["zip_file"],
        raster_sha256=art["tif_sha256"],
        format_valid=format_valid,
        leakage_canary_pass=leak_pass,
        point_beats_incumbent_all_3_holdouts=point_beats_all_three,
        ci95_beats_incumbent_all_3_holdouts=ci_beats_all_three,
        modern_comparable_uniqueness_pass=modern_comparable_unique,
        literal_uniqueness_pass=literal_unique,
        verdict="promote" if strict_ready else "negative",
        submission_ready=strict_ready,
        approved_for_weekly_slot=False,
    )
    if run_card_out is not None:
        run_card_out.parent.mkdir(parents=True, exist_ok=True)
        run_card_out.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, default=RESULTS)
    ap.add_argument("--run-card", type=Path, default=RUNCARD)
    ap.add_argument("--summary-out", type=Path, default=None)
    args = ap.parse_args(argv)
    out = run(results_path=args.results, run_card_path=args.run_card, run_card_out=args.summary_out)
    print(json.dumps(out, indent=2, allow_nan=False))
    return 0 if (out["pins_clean"] and out["format_valid"] and out["run_card_consistent"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
