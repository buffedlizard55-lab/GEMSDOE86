"""Independent, read-only validation of the published candidate + run card.

Does NOT need data/ (checks the serialized TIF against the pinned grid
constants in vendor/gems57/grid.py) and NEVER writes or overwrites
docs/evidence/run-card.json. Exit 0 only if every format/consistency
check passes; the scientific verdict is reported, not altered.
"""
from __future__ import annotations
import hashlib, json, sys, zipfile
from pathlib import Path
import numpy as np, rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
from gems57 import grid as G  # pinned constants only; no data files read


def validate() -> dict:
    card = json.loads((ROOT / "docs/evidence/run-card.json").read_text())
    tif = ROOT / card["submission_file"]
    sha = hashlib.sha256(tif.read_bytes()).hexdigest()
    checks: dict[str, bool] = {}
    checks["sha256_matches_run_card"] = sha == card["raster_sha256"]
    checks["note_le_140_chars"] = len(card["note"]) <= 140
    checks["experiments_within_budget_3"] = card.get("experiments_run", 99) <= 3
    # Shared uniqueness checker verdict must be reported verbatim, never paraphrased.
    lane = json.loads((ROOT / "docs/evidence/lane86_results.json").read_text())
    uniq = lane["final_uniqueness"]
    recorded = card['correlation_overlap_vs_registry']
    checks['uniqueness_checker_verbatim'] = bool(
        recorded['rasters_checked'] == uniq['registry_rasters_checked']
        and recorded['final_worst_dot_overlap_literal'] == uniq['worst_dot_overlap']
        and recorded['final_worst_spearman'] == uniq['worst_spearman_full_footprint'])
    checks['readiness_respects_shared_stop'] = bool(not uniq['stop_required'] or (
        card['verdict'] == 'negative' and not card['submission_ready'] and not card['approved_for_weekly_slot']))
    # A missing/incomplete scan is not clearance, even if stop_required is false.
    # This is necessary evidence only: a complete unique scan cannot by itself
    # establish a holdout improvement or authorize the separate slot selector.
    claims_promotion = (card['verdict'] == 'promote' or card['submission_ready']
                        or card['approved_for_weekly_slot'])
    checks['readiness_requires_complete_unique_scan'] = bool(not claims_promotion or (
        uniq.get('unique') is True
        and uniq.get('complete_accessible_scan') is True
        and uniq.get('stop_required') is False))
    with rasterio.open(tif) as ds:
        a = ds.read(1)
        checks["single_band_float32"] = ds.count == 1 and ds.dtypes == ("float32",)
        checks["crs_epsg_32611"] = str(ds.crs) == "EPSG:32611"
        checks["shape_3730x3292"] = ds.shape == G.SHAPE
        checks["transform_matches_pinned_grid"] = tuple(ds.transform)[:6] == tuple(G.TRANSFORM)[:6]
    checks["all_finite"] = bool(np.isfinite(a).all())
    checks["values_in_0_1"] = bool(a.min() >= 0.0 and a.max() <= 1.0)
    checks["no_sentinels"] = bool(not ((a < -1e30) | (a == -9999)).any())
    checks["dots_match_run_card"] = int((a > 0).sum()) == int(card["validator"]["dots"])
    zpath = tif.with_suffix(".zip")
    with zipfile.ZipFile(zpath) as z:
        checks["zip_contains_only_this_tif"] = z.namelist() == [tif.name]
        checks['zip_tif_bytes_equal_registered_tif'] = bool(
            checks['zip_contains_only_this_tif'] and z.read(tif.name) == tif.read_bytes())
    return {
        "file": str(tif.relative_to(ROOT)), "sha256": sha,
        "checks": checks, "all_format_checks_passed": all(checks.values()),
        "dots": int((a > 0).sum()), "min": float(a.min()), "max": float(a.max()),
        "uniqueness_checker": {"unique": uniq["unique"], "duplicate_count": uniq["duplicate_count"],
                                "stop_required": uniq["stop_required"],
                                "worst_spearman": uniq["worst_spearman_full_footprint"],
                                "worst_dot_overlap_within_3px": uniq["worst_dot_overlap"],
                                "worst_overlap_submission": uniq["worst_overlap_submission"],
                                "registry_rasters_checked": uniq["registry_rasters_checked"]},
        "holdout_dti_labelled": card["holdout_dti"],
        "verdict": card["verdict"], "submission_ready": card["submission_ready"],
        "approved_for_weekly_slot": card["approved_for_weekly_slot"],
        "download_status": card["download_status"],
        "validation_class": "independent local format/consistency preflight; NOT organizer acceptance",
    }


if __name__ == "__main__":
    out = validate()
    (ROOT / "docs/evidence/independent_validation.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    sys.exit(0 if out["all_format_checks_passed"] else 1)
