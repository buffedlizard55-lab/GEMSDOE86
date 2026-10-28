#!/usr/bin/env python3
"""Build the H87-FCB candidate raster (band selected by the pre-registered holdout rule).

Preregistration: research/H87_FAIR_CATALOGUE_BAND_PREREGISTRATION.json.
Experiment results: docs/evidence/h87-fcb-experiment1-20261027.json and
docs/evidence/h87-fcb-experiment2-20261027.json (HOLDOUT-DTI, gems57-pooled-hide-v2).

The band is chosen by the holdout rule (argmax pooled HOLDOUT-DTI among B1/B2/B3 whose paired
delta vs the uniform null excludes 0), read from the experiment JSON rather than typed in.
The candidate is written with the repo's own writer (vendor/gems57/grid.write_submission,
all-finite zeros-outside form) and checked with the repo's own validator
(vendor/gems57/validate.validate). Uniqueness is measured against every locally available
reference raster; this is NOT a full-registry clearance.

Usage: python scripts/h87_build_candidate.py --fleet /tmp/fleet/extract
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems57 import grid as G, validate as V, uniqueness as U  # noqa: E402
from run_h87_fcb import thin_nearest_first, BANDS, BUDGET_RATIO, SPACING_PX  # noqa: E402


def _finite(o):
    """Replace NaN/Inf with null so the JSON is strict (the repo loader rejects non-finite tokens)."""
    if isinstance(o, float) and not math.isfinite(o):
        return None
    if isinstance(o, dict):
        return {k: _finite(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_finite(v) for v in o]
    return o

BUDGET = 37654
EXP1 = ROOT / "docs/evidence/h87-fcb-experiment1-20261027.json"
EXP2 = ROOT / "docs/evidence/h87-fcb-experiment2-20261027.json"
OUT_DIR = ROOT / "releases"  # git-ignored (releases/*.tif) pending data-use check; NOT published on Pages
EVID = ROOT / "docs/evidence/h87-fcb-candidate-receipt-20261027.json"
NOTE_MAX = 140
NAME_MAX = 64


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def choose_band() -> tuple[str, dict]:
    arms = {}
    for path in (EXP1, EXP2):
        arms.update(json.loads(path.read_text())["arms"])
    eligible = {}
    for name in ("B1", "B2", "B3"):
        a = arms[name]
        lo, hi = a["vs_N0"]["paired_delta_ci95"]
        if lo > 0:
            eligible[name] = a["pooled"]["dti"]
    if not eligible:
        raise SystemExit("no band passes the pre-registered selection rule: lane NEGATIVE")
    best = max(eligible, key=eligible.get)
    return best, {k: arms[k]["pooled"]["dti"] for k in eligible}


def union_rho(mine: np.ndarray, theirs: np.ndarray) -> float:
    """Spearman on the union of the two dot sets (same definition as uniqueness.surface_rho)."""
    from scipy.stats import spearmanr
    union = mine | theirs
    if union.sum() <= 10 or not (mine[union].any() and theirs[union].any()) or (mine[union].all() or theirs[union].all()):
        return float("nan")
    return float(spearmanr(mine[union].astype(np.float32), theirs[union].astype(np.float32)).statistic)


def dot_ref_paths(fleet: Path) -> dict[str, Path]:
    """Every locally available GeoTIFF reference, keyed by its repo-relative or fleet-relative name."""
    refs: dict[str, Path] = {}
    for p in sorted((ROOT / "docs/downloads").glob("*.tif")):
        refs[f"docs/downloads/{p.name}"] = p
    for p in sorted((ROOT / "data/scored_fleet").glob("*.tif")):
        refs[f"data/scored_fleet/{p.name}"] = p
    if fleet.is_dir():
        for p in sorted(fleet.rglob("*.tif")):
            refs[f"fleet/{p.relative_to(fleet)}"] = p
    return refs


def load_dots(path: Path, shape: tuple[int, int]) -> np.ndarray | None:
    """Stream one reference as a boolean dot field (None if its grid differs)."""
    with rasterio.open(path) as ds:
        if ds.shape != shape:
            return None
        a = ds.read(1)
    return np.isfinite(a) & (a > 0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fleet", default="/tmp/fleet/extract")
    args = ap.parse_args()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")

    band, eligible = choose_band()
    lo, hi = BANDS[band]
    g = G.load_grid(ROOT / "data/bridge")
    fp = g.footprint
    cat = g.catalogue
    d = ndi.distance_transform_edt(~cat)
    cand = fp & (d > lo) & (d <= hi)
    dots = thin_nearest_first(cand, d, BUDGET)
    n = int(dots.sum())

    name = f"gems86-h87-fcb-{band.lower()}-{int(lo)}to{int(hi)}px-{n}dots-20261027-zeros-out"  # not *-zeros.tif: releases/ globs reserve that suffix
    assert len(name) + len(".tif") <= NAME_MAX, name
    out = OUT_DIR / f"{name}.tif"
    G.write_submission(out, dots.astype(np.float32), mode="zeros")

    rec = V.validate(out, footprint=fp, catalogue=cat)
    with rasterio.open(out) as ds:
        arr = ds.read(1)
        tf = tuple(float(v) for v in ds.transform)[:6]
        crs = ds.crs.to_epsg()
    checks = dict(
        crs_epsg_32611=crs == 32611,
        shape_3730x3292=arr.shape == (3730, 3292),
        transform_pinned=tf == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
        no_nan_or_inf=bool(np.isfinite(arr).all()),
        in_0_1=bool(arr.min() >= 0.0 and arr.max() <= 1.0),
        outside_footprint_zero=bool(np.all(arr[~fp] == 0.0)),
        zero_dots_on_catalogue=int((arr[cat] > 0).sum()) == 0,
    )
    checks["validator_all_checks_passed"] = bool(rec["all_checks_passed"])

    # minimum pairwise spacing of accepted dots (must be >= SPACING_PX)
    ys, xs = np.nonzero(dots)
    pts = np.stack([ys, xs], 1)
    from scipy.spatial import cKDTree
    dd, _ = cKDTree(pts).query(pts, k=2)
    min_pair = float(dd[:, 1].min())
    checks["min_pair_spacing_px_ge_parent_floor"] = min_pair >= SPACING_PX - 1e-9

    # uniqueness: dot-field overlap against every locally available reference
    ref_paths = dot_ref_paths(Path(args.fleet))
    rows = []
    skipped_shape = 0
    self_key = str(out.relative_to(ROOT))
    for key, path in ref_paths.items():
        if key == self_key:
            continue
        rdots = load_dots(path, fp.shape)
        if rdots is None:
            skipped_shape += 1
            continue
        if not rdots.any():
            del rdots
            continue
        fwd = U.dot_overlap(dots, rdots)
        rev = U.dot_overlap(rdots, dots)
        cover = float(U._near(rdots, 3.0)[fp].mean())
        rows.append(dict(reference=key, reference_dots=int(rdots.sum()),
                         overlap_mine_in_ref=round(fwd, 6), overlap_ref_in_mine=round(rev, 6),
                         chance_halo_fraction=round(cover, 6),
                         excess_over_chance=round(fwd - cover, 6),
                         surface_rho_dot_union=union_rho(dots, rdots)))
        del rdots
    rows.sort(key=lambda r: -r["overlap_mine_in_ref"])
    max_fwd = rows[0] if rows else None
    dense_saturated = [r["reference"] for r in rows if r["chance_halo_fraction"] > 0.5]
    uniq = dict(
        references_compared=len(rows),
        references_excluded_for_shape=skipped_shape,
        max_overlap=max_fwd,
        count_over_0_70=sum(1 for r in rows if r["overlap_mine_in_ref"] > 0.70),
        count_excess_over_chance_over_0_30=sum(1 for r in rows if r["excess_over_chance"] > 0.30),
        max_surface_rho=max((r["surface_rho_dot_union"] for r in rows
                             if r["surface_rho_dot_union"] == r["surface_rho_dot_union"]), default=None),
        references_with_chance_halo_over_50pct=dense_saturated,
        top10=rows[:10],
    )

    # literal full-support witness: not present locally. Recorded as NOT MEASURED here.
    witness = dict(name="17GEMSDOE", status="NOT_MEASURED_LOCALLY",
                   repo_record="IRREGULARITIES.md: continuous full-support witness, 5,106,385/5,106,385 = 100.0% allowed coverage; literal overlap 1.0000 for every dot field")

    passed_format = all(checks.values())
    like_for_like_local = uniq["count_over_0_70"] == 0 and uniq["count_excess_over_chance_over_0_30"] == 0
    literal_gate = "FAIL (repo record: 17GEMSDOE literal overlap 1.0000; PA-86-01 keeps the literal gate binding for upload)"
    note = (f"H87-FCB band {int(lo)}-{int(hi)}px from visible traces; holdout 0.2197 [0.2105,0.2277]; "
            "NOT cleared: literal witness gate")
    assert len(note) <= NOTE_MAX, len(note)

    receipt = dict(
        schema="gems86.h87-fcb-candidate.v1",
        session="fb68389e",
        started_utc=started,
        finished_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        hypothesis="A dot field in the band (3,5] px from VISIBLE traces, built only from visible traces, beats an equal-count uniform null on the hide-and-recover holdout.",
        mechanism="Withheld fault traces lie a few pixels from visible mapped traces; the band captures near-parallel strands beyond the 3 px kernel.",
        non_fault_mimic="Mapping density: traces are mapped where survey coverage is dense, so distance-to-trace can proxy for where surveyors looked.",
        band_selected_by_rule=band,
        band_px=[lo, hi],
        eligible_band_holdout_dti=eligible,
        file=str(out.relative_to(ROOT)),
        name=name,
        name_chars=len(name),
        note=note,
        note_chars=len(note),
        sha256=sha256(out),
        bytes=out.stat().st_size,
        dots=n,
        budget=BUDGET,
        budget_ratio_reference=BUDGET_RATIO,
        spacing_px=SPACING_PX,
        min_pair_spacing_px=min_pair,
        validator_checks=checks,
        validator_receipt_class=rec.get("validation_class"),
        format_gate_passed=passed_format,
        uniqueness_local=uniq,
        witness_literal=witness,
        like_for_like_local_pass=like_for_like_local,
        holdout={
            "evaluator": "gems57-pooled-hide-v2",
            "label": "HOLDOUT-DTI (gems57-pooled-hide-v2, 45,260 withheld positives, cell-bootstrap 95% CI)",
            "source": "docs/evidence/h87-fcb-experiment2-20261027.json (B3 arm; candidate is built from the full catalogue, the arm from visible traces only)",
        },
        leaderboard_score="NONE: no live score is claimed. OWNER-REPORTED / ORGANIZER-CONFIRMED scores for this file: none.",
        literal_submission_gate=literal_gate,
        verdict="negative-for-upload",
        safe_to_submit=False,
        approved_for_weekly_slot=False,
        submission_slots_used=0,
        decision=("DO NOT SUBMIT: unique-by-local-check and format-valid, but the literal full-support witness gate "
                  "is failed by the repo's binding rule. Upload needs an owner decision on that gate plus an "
                  "organizer receipt."),
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    EVID.parent.mkdir(parents=True, exist_ok=True)
    EVID.write_text(json.dumps(_finite(receipt), indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: receipt[k] for k in ("name", "sha256", "dots", "band_selected_by_rule",
                                                "format_gate_passed", "like_for_like_local_pass",
                                                "decision")}, indent=2))
    print("max overlap:", json.dumps(uniq["max_overlap"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
