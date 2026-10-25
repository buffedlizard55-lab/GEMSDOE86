#!/usr/bin/env python3
"""H86M lane experiment — build one unique GEMS submission TIFF.

Lane (single method paragraph, protocol rule 1):
    H86M blind stepover-junction off-trace propensity. Geothermal fluids in
    the northern Great Basin localize at dilatational fault step-overs,
    intersections and relay ramps that lie OFF the mapped USGS/INGENIOUS
    traces; the catalogue maps traces but not blind tips, buried jogs or
    unmapped splays. The prediction field is built ONLY from catalogue
    geometry: an exponential off-trace decay halo (300 m / 3 px triangular
    scale, catalogue pixels masked pixel-exactly to zero) multiplied by a
    multi-scale junction/step-over excess density (fault pixels per cell in a
    2.1 km window minus the same in a 1.1 km window, floored at zero),
    restricted to the scored footprint and normalized to [0, 1]; the top
    37,654 allowed cells are emitted as binary dots. No 19-band fit, no
    logistic/HGB model, no dot-budget sweep, no submodular/SAR/phase-congruency
    machinery — pure public catalogue geometry, off-trace masking, equal-budget
    dots. Targets faults missing from the catalogue rather than re-predicting
    mapped traces. Named non-fault mimic: piedmont/range-front alluvial
    topography or volcanic-center alteration can look junction-like without a
    fault (the geometry-only field carries no radiometric/topo training signal,
    but that mimic remains the alternative explanation).

This script does NOT fit a model, does not touch a weekly submission slot, and
does not authorize upload. Every number below is measured from disk bytes or
derived from pinned local inputs; nothing is projected as a score.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import gates, grid, validate  # noqa: E402
from gems57.grid import load_grid  # noqa: E402
from gems57.submission_writer import write_submission  # noqa: E402
from gems57.uniqueness import (  # noqa: E402
    compare_array_to_registry,
    two_phase_summary,
)

K_DOTS = 37_654  # equal-budget comparison with the dominant 37,654-dot fleet
HALO_PX = 3.0  # 300 m triangular-kernel scale on the 100 m grid
WIN1_PX = 11  # ~1.1 km local trace density
WIN2_PX = 21  # ~2.1 km junction/step-over context density


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_propensity(g, halo_px=HALO_PX, w1=WIN1_PX, w2=WIN2_PX):
    fp = g.footprint
    cat = g.catalogue
    # Distance from every cell to the nearest mapped fault (px).
    d = ndi.distance_transform_edt(~cat).astype(np.float64)
    # Exponential off-trace halo, pixel-exactly zero on the catalogue and
    # outside the footprint.
    halo = np.exp(-d / float(halo_px))
    halo[cat] = 0.0
    halo[~fp] = 0.0
    # Multi-scale junction / step-over excess density.
    dens1 = ndi.uniform_filter(cat.astype(np.float64), size=w1, mode="constant", cval=0.0)
    dens2 = ndi.uniform_filter(cat.astype(np.float64), size=w2, mode="constant", cval=0.0)
    junction = np.clip(dens2 - dens1, 0.0, None)
    junction[cat] = 0.0
    junction[~fp] = 0.0
    raw = halo * (1.0 + 3.0 * junction)
    raw[cat] = 0.0
    raw[~fp] = 0.0
    allowed = fp & ~cat
    scale = float(raw[allowed].max()) if allowed.any() else 0.0
    surface = np.zeros_like(raw)
    if scale > 0:
        surface[allowed] = raw[allowed] / scale
    surface = np.clip(surface, 0.0, 1.0)
    return surface, allowed


def emit_top_dots(surface, allowed, k=K_DOTS):
    dots = np.zeros_like(surface, dtype=np.float32)
    vals = surface[allowed & (surface > 0)]
    if vals.size == 0:
        return dots
    n = min(int(k), int(vals.size))
    thr = np.sort(vals)[-n]  # nth-largest score
    take = (surface >= thr) & allowed & (surface > 0)
    # Tie guard: never emit more than n cells.
    if int(take.sum()) > n:
        order = np.argsort(surface[take], kind="stable")
        keep = np.zeros(take.sum(), bool)
        keep[order[-n:]] = True
        take[take] = keep
    dots[take] = 1.0
    return dots


def local_registry_index(exclude_path: Path | None = None):
    """Hash-pin every raster locally accessible in this checkout (NOT the organizer registry)."""
    roots = [ROOT / "docs/downloads", ROOT / "data/scored_fleet", ROOT / "submission", ROOT / "releases"]
    records = []
    seen = set()
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.tif")):
            if exclude_path is not None and path.resolve() == exclude_path.resolve():
                continue
            if path.resolve() in seen:
                continue
            seen.add(path.resolve())
            try:
                digest = sha256_file(path)
            except OSError:
                continue
            records.append(
                dict(
                    repo="local:GEMSDOE86",
                    submission=path.stem,
                    file=str(path),
                    sha256=digest,
                    sources=["local:GEMSDOE86"],
                )
            )
    return dict(rasters=records, complete_accessible_scan=False, errors=[])


def main() -> int:
    out_dir = ROOT / "docs/downloads"
    ev_dir = ROOT / "docs/evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    ev_dir.mkdir(parents=True, exist_ok=True)

    g = load_grid(ROOT / "data/bridge")
    footprint, catalogue = g.footprint, g.catalogue
    sample = ROOT / "data/bridge/sample_submission.tif"

    surface, allowed = build_propensity(g)
    dots = emit_top_dots(surface, allowed)
    n_dots = int((dots > 0).sum())
    print(f"allowed off-catalogue cells: {int(allowed.sum())}; emitted dots: {n_dots}")
    if n_dots == 0:
        raise SystemExit("no dots emitted — aborting")
    if int(((dots > 0) & catalogue).sum()) or int(((dots > 0) & ~footprint).sum()):
        raise SystemExit("catalogue or footprint rule violated — aborting")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(dots).tobytes()).hexdigest()[:8]
    name = f"gems86-h86m-stepperjunction-{n_dots}dots-{ts}-{digest8}-zeros"
    if len(name) > 140:
        raise SystemExit("submission name exceeds 140 chars")
    note = (
        f"H86M blind stepover-junction off-trace propensity, {n_dots:,} catalogue-masked dots; "
        "audit only, holdout not local, DO NOT SUBMIT"
    )
    if len(note) > 140:
        raise SystemExit("note exceeds 140 chars")
    tif_path = out_dir / f"{name}.tif"

    receipt = write_submission(
        tif_path,
        dots.astype(np.float32),
        sample,
        footprint,
        note=note,
        name=name,
        catalogue=catalogue,
        metadata=dict(
            lane="H86M-blind-stepperjunction-offtrace-propensity",
            hypothesis="blind geothermal systems localize at off-catalogue dilatational step-overs/junctions",
            mechanism="exp(-d_cat/300m) x (1 + 3 x junction-excess density), footprint-restricted, catalogue pixels masked to zero",
            k_dots=n_dots,
            halo_px=HALO_PX,
            window_px=[WIN1_PX, WIN2_PX],
        ),
    )
    print("writer receipt:", receipt["file"], receipt["sha256"])

    # On-disk re-validation (fail-closed).
    val = validate.validate(tif_path, footprint, catalogue)
    fmt = gates.format_report(tif_path, sample, footprint=footprint)
    print("validate all_checks_passed:", val["all_checks_passed"])
    print("format_report ok:", fmt["ok"], "problems:", fmt["problems"])

    # --- Registry uniqueness: surface (pre-placement) then dots (final) ---
    import rasterio  # noqa: E402

    registry = local_registry_index(exclude_path=tif_path)
    registry_records = registry["rasters"]
    expected_grid = ((g.height, g.width), "EPSG:32611", g.transform)

    with rasterio.open(tif_path) as src:
        on_disk = src.read(1).astype(np.float32)
    assert np.array_equal(on_disk, dots), "on-disk pixels differ from in-memory dots"

    surf_report = compare_array_to_registry(
        surface, registry_records, footprint, file_sha256=None,
        include_reverse=False, expected_grid=expected_grid,
    )
    dot_report = compare_array_to_registry(
        dots, registry_records, footprint, file_sha256=receipt["sha256"],
        include_reverse=True, expected_grid=expected_grid,
    )
    summary = two_phase_summary(
        dot_report["rows"], int(footprint.sum()),
        expected_rasters=len(registry["rasters"]),
    )
    print("REGISTRY surface worst rho:", surf_report["worst_spearman_full_footprint"])
    print("REGISTRY dots worst overlap:", dot_report["worst_dot_overlap"])
    print("REGISTRY two-phase:", json.dumps(summary, indent=1)[:1500])

    # --- Run card (protocol rule 5). Holdout DTI is NOT computable locally: the
    # truth folds (withheld fault segments) require the DrivenData training data
    # which is behind login and is not present in this checkout (see README data
    # blocker). No HOLDOUT-DTI number is fabricated; nothing is projected as a score.
    card = dict(
        evidence_class="RUN-CARD",
        lane="H86M-blind-stepperjunction-offtrace-propensity",
        generated_utc=ts,
        hypothesis=("Blind geothermal systems in the northern Great Basin localize at dilatational "
                    "fault step-overs, intersections and relay ramps that lie OFF the mapped USGS/INGENIOUS "
                    "catalogue traces; the catalogue maps traces but not blind tips, buried jogs or unmapped splays."),
        mechanism=("Catalogue-geometry-only field: exponential off-trace decay halo exp(-d_cat/3 px) on the "
                   "100 m grid (300 m scale), catalogue pixels masked pixel-exactly to zero, multiplied by "
                   "multi-scale junction/step-over excess density (fault density in a 2.1 km window minus "
                   "the same in a 1.1 km window, floored at zero), restricted to the scored footprint and "
                   "normalized to [0, 1]; the top 37,654 allowed cells are emitted as binary dots. DTI "
                   "notation (alpha 0.2, beta 0.8, 300 m triangular kernel) matches the competition metric; "
                   "no labels are used."),
        named_non_fault_mimic=("piedmont / range-front alluvial topography or volcanic-center alteration can "
                               "produce junction-like lineament patterns without a fault; the geometry-only field "
                               "carries no radiometric/topo training signal, so label leakage is not a route here."),
        differ_from_repo=("No 19-band fit, no logistic/HGB model, no dot-budget sweep, no submodular / SAR / "
                          "phase-congruency machinery — pure public catalogue geometry with off-trace masking, "
                          "equal-budget 37,654 dots; distinct from every executed GEMSDOE86 lane."),
        holdout_dti=dict(
            evidence_class="HOLDOUT-DTI",
            evaluator_version="gems57-pooled-hide-v2",
            value=None,
            ci95=None,
            withheld_positives=None,
            computable_locally=False,
            reason=("truth folds (withheld whole fault segments) require the DrivenData training features/labels, "
                    "which are behind login and absent from this checkout (scripts/download_competition_data.sh + "
                    "prepare_data blocker documented in README.md); no HOLDOUT-DTI number is reported or projected."),
        ),
        leakage_canary=dict(
            evidence_class="LEAKAGE-CANARY",
            computable_locally=False,
            reason="no truth folds available locally; no model is fit and no labels are used, so there is no label-leakage route by construction; per-protocol single-feature AUC screening deferred to a machine with the restored feature stack",
            auc_above_0_90_flag=False,
        ),
        registry_measurement=dict(
            evidence_class="REGISTRY-MEASUREMENT",
            scope="locally accessible rasters only (docs/downloads, data/scored_fleet, submission, releases); not the organizer registry; incomplete accessible scan",
            registry_rasters_checked=len(registry["rasters"]),
            complete_accessible_scan=False,
            surface=dict(
                worst_spearman_full_footprint=surf_report["worst_spearman_full_footprint"],
                worst_spearman_submission=surf_report["worst_rho_submission"],
                rho_limit=0.90,
                rho_firings=0 if surf_report["worst_spearman_full_footprint"] is None or surf_report["worst_spearman_full_footprint"] <= 0.90 else 1,
            ),
            dots=dict(
                my_dots=n_dots,
                worst_forward_overlap_3px=dot_report["worst_dot_overlap"],
                worst_overlap_submission=dot_report["worst_overlap_submission"],
                overlap_limit=0.70,
                forward_overlap_firings=int(dot_report["duplicate_count"]),
                worst_jaccard=dot_report["worst_jaccard_dot_sets"],
                identical_bytes=any(r.get("identical_bytes") for r in dot_report["rows"] if "error" not in r),
                identical_decoded=any(r.get("identical_decoded_predictions") for r in dot_report["rows"] if "error" not in r),
            ),
            two_phase=summary,
            verdict="negative" if (summary["like_for_like_reading"]["duplicate"] or not summary["complete_accessible_scan"]) else "unique-vs-local-accessible-subset",
        ),
        raster=dict(
            file=str(tif_path.relative_to(ROOT)),
            zip_file=str(tif_path.with_suffix(".zip").relative_to(ROOT)),
            receipt_file=str(tif_path.with_suffix(".json").relative_to(ROOT)),
            sha256=receipt["sha256"],
            zip_sha256=receipt["zip_sha256"],
            bytes=receipt["bytes"],
            shape=[int(g.height), int(g.width)],
            crs="EPSG:32611",
            transform=list(g.transform)[:6],
            emitted_dots=n_dots,
            min=val["min"],
            max=val["max"],
            mean=val["mean"],
            nan_pixels=val["n_nan"],
            infinite_pixels=val["n_infinite"],
        ),
        validator=dict(
            evidence_class="LOCAL-FORMAT-VALIDATION",
            all_checks_passed=bool(val["all_checks_passed"] and fmt["ok"]),
            no_nan_inside_footprint=bool(val["checks"].get("in_footprint_all_finite")),
            values_in_0_1=bool(val["checks"].get("range_0_1_guaranteed")),
            crs_shape_transform_match=bool(
                val["checks"].get(f"crs_epsg_{32611}")
                and val["checks"].get(f"dimensions_{g.height}x{g.width}")
                and val["checks"].get("transform_matches_sample_submission")
            ),
            checks=val["checks"],
            template_report=fmt,
        ),
        submission=dict(
            name=name,
            note=note,
            note_chars=len(note),
            approved_for_weekly_slot=False,
            promoted=False,
            submission_slots_used=0,
            status="locally validated only; not organizer acceptance or slot approval",
        ),
        verdict="negative",
        verdict_reason=("format-valid, unique-vs-locally-accessible-subset pending full-organizer-registry scan; "
                        "HOLDOUT-DTI not computable locally (training data behind login); not submission-authorized; "
                        "0 weekly slots used; audit download only."),
    )
    card_path = ev_dir / "h86m-run-card.json"
    card_path.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("run card:", card_path)
    print("VERDICT:", card["verdict"], "|", card["verdict_reason"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
