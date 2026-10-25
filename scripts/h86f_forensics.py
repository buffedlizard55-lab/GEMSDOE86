#!/usr/bin/env python3
"""Read-only H86F pre-freeze forensics: H33 anatomy, fleet strata, band QC.

This audit fits nothing, builds no candidate surface and places no dots. It
re-derives, from pinned bytes in this checkout, the three facts the H86F-GZZD
preregistration relies on:

1. GEMSDOE32 ``h33-h33-2-b2`` (OWNER-REPORTED 0.2778) is pixel-exactly its
   GEMSDOE28 ``r1-solo-d2-8`` parent minus the dots at catalogue distance in
   {sqrt(2), 2} px, with minimum dot spacing 2*sqrt(2) px (kernel-scale
   dotting). Emission geometry, not a new layer.
2. Descriptive fleet strata (far-from-catalogue and low-slope fractions) for
   every raster in ``data/scored_fleet``, joined to OWNER-REPORTED scores in
   ``registry/prior_scores.csv`` where an exact stem match exists. Owner
   scores are unverified claims; strata are measurements. No causality.
3. The signed-gravity-vector Laplace identity actually used by H86F-GZZD:
   corr(-(dx Band18 + drow Band11), -Laplacian Band13) at sigma=5 px on the
   30-px-eroded footprint interior, plus the Band15/Band13 shared-ancestry
   correlation. Recomputed here so the lane never relies on prose alone.

Output: ``docs/evidence/h86f-h33-forensics.json`` (evidence classes labelled).
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]

from gems57 import grid as grid_mod  # noqa: E402

NODATA = -3.4028234663852886e38
H33 = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
PARENT = ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
FEATURES = ROOT / "data/training_features.tif"
OUT = ROOT / "docs/evidence/h86f-h33-forensics.json"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dots(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        if src.count != 1 or src.shape != (grid_mod.HEIGHT, grid_mod.WIDTH):
            raise ValueError(f"unexpected grid for {path.name}")
        a = src.read(1)
    return np.isfinite(a) & (a > 0)


def read_band(index: int, footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(FEATURES) as src:
        a = src.read(index).astype(np.float32)
    ok = footprint & np.isfinite(a) & (a > NODATA * 0.5)
    filled = np.where(ok, a, float(np.median(a[ok]))).astype(np.float32)
    return filled, ok


def corr(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> float:
    return float(np.corrcoef(a[mask].astype(np.float64), b[mask].astype(np.float64))[0, 1])


def owner_scores() -> dict[str, float]:
    scores: dict[str, float] = {}
    with (ROOT / "registry/prior_scores.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                scores[row["submission"]] = float(row["score"])
            except (KeyError, TypeError, ValueError):
                continue
    return scores


def match_owner_score(filename: str, scores: dict[str, float]) -> float | None:
    stem = filename.removesuffix(".tif")
    for submission, value in scores.items():
        if submission in stem:
            return value
    return None


def main() -> int:
    g = grid_mod.load_grid(ROOT / "data/bridge")
    fp, cat = g.footprint, g.catalogue
    dcat = ndi.distance_transform_edt(~cat)

    h33 = dots(H33)
    parent = dots(PARENT)
    removed = parent & ~h33
    added = h33 & ~parent
    removed_distances = sorted({round(float(v), 6) for v in np.unique(dcat[removed])})

    ys, xs = np.nonzero(h33)
    tree = cKDTree(np.c_[ys, xs].astype(np.float64))
    nn, _ = tree.query(np.c_[ys, xs].astype(np.float64), k=2)
    nn = nn[:, 1]

    def strata(mask: np.ndarray, slope: np.ndarray, slope_ok: np.ndarray, q25: float) -> dict:
        inside = mask & fp
        d = dcat[inside]
        s = slope[inside & slope_ok]
        return {
            "dots": int(mask.sum()),
            "dots_on_catalogue": int((mask & cat).sum()),
            "dots_outside_footprint": int((mask & ~fp).sum()),
            "frac_dcat_le_2px": float((d <= 2).mean()),
            "frac_dcat_ge_32px": float((d >= 32).mean()),
            "median_dcat_px": float(np.median(d)),
            "frac_slope_le_footprint_q25": float((s <= q25).mean()) if s.size else None,
        }

    slope, slope_ok = read_band(19, fp)
    q25 = float(np.percentile(slope[fp & slope_ok], 25))
    scores = owner_scores()
    fleet = []
    for path in sorted((ROOT / "data/scored_fleet").glob("*.tif")):
        mask = dots(path)
        fleet.append({
            "file": path.name,
            "sha256": sha256(path),
            "owner_reported_score": match_owner_score(path.name, scores),
            "evidence_class_score": "OWNER-REPORTED (no organizer receipt)",
            **strata(mask, slope, slope_ok, q25),
        })

    interior = ndi.binary_erosion(fp, iterations=30)
    b11, _ = read_band(11, fp)
    b13, _ = read_band(13, fp)
    b15, _ = read_band(15, fp)
    b18, _ = read_band(18, fp)
    sigma = 5.0
    gzz = -(ndi.gaussian_filter(b18, sigma, order=(0, 1), mode="nearest")
            + ndi.gaussian_filter(b11, sigma, order=(1, 0), mode="nearest"))
    gzz_wrong_sign = -(ndi.gaussian_filter(b18, sigma, order=(0, 1), mode="nearest")
                       - ndi.gaussian_filter(b11, sigma, order=(1, 0), mode="nearest"))
    neg_laplacian = -(ndi.gaussian_filter(b13, sigma, order=(0, 2), mode="nearest")
                       + ndi.gaussian_filter(b13, sigma, order=(2, 0), mode="nearest"))

    report = {
        "schema": "gems86.h86f-forensics.v1",
        "evidence_class": "MEASUREMENT (pinned bytes in this checkout; owner scores labelled separately)",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "grid": {
            "shape": [grid_mod.HEIGHT, grid_mod.WIDTH],
            "crs": "EPSG:32611",
            "footprint_pixels": int(fp.sum()),
            "catalogue_pixels": int(cat.sum()),
            "training_features_sha256": sha256(FEATURES),
        },
        "h33_anatomy": {
            "h33_file": H33.name,
            "h33_sha256": sha256(H33),
            "parent_file": PARENT.name,
            "parent_sha256": sha256(PARENT),
            "h33_dots": int(h33.sum()),
            "parent_dots": int(parent.sum()),
            "h33_is_exact_subset_of_parent": bool(added.sum() == 0),
            "removed_dots": int(removed.sum()),
            "added_dots": int(added.sum()),
            "removed_dcat_values_px": removed_distances,
            "h33_nn_spacing_px": {
                "min": float(nn.min()),
                "median": float(np.median(nn)),
                "frac_below_2p8": float((nn < 2.8).mean()),
            },
            "h33_strata": strata(h33, slope, slope_ok, q25),
            "parent_strata": strata(parent, slope, slope_ok, q25),
            "interpretation": (
                "OWNER-REPORTED 0.2708 -> 0.2778 was obtained by deleting 2,545 collar dots and "
                "changing nothing else. Together with the >=2.828 px spacing, H33's lead within its "
                "lineage is explained by coverage-efficient dotted emission under the 300 m "
                "triangular-kernel DTI (alpha=0.2: redundant/collar mass costs FP weight without "
                "adding max-kernel truth credit), not by a new geological layer. This is a "
                "mechanistic explanation of an unverified owner claim, not an organizer score."
            ),
        },
        "fleet_strata": {
            "slope_q25_band19": q25,
            "rows": fleet,
            "caveat": (
                "Descriptive only. High OWNER-REPORTED lineage files put ~0.32-0.34 of dots "
                ">=32 px from the catalogue and ~0.001 on lowest-quartile slope, while the lowest "
                "scored present file puts 0.000 far; counterexamples exist in the same table, so "
                "no monotone causal rule is claimed."
            ),
        },
        "gzzd_band_qc": {
            "formula_image_coordinates": "gzz = -(d_x Band18 + d_row Band11); vector (dg/dx_east, dg/dy_north) = (+Band18, -Band11)",
            "sigma_px": sigma,
            "interior_pixels": int(interior.sum()),
            "corr_gzz_vs_neg_laplacian_band13": corr(gzz, neg_laplacian, interior),
            "corr_wrong_sign_row_variant": corr(gzz_wrong_sign, neg_laplacian, interior),
            "corr_band15_vs_band13_shared_ancestry": corr(b15, b13, interior),
            "runner_fail_closed_below": 0.80,
        },
        "limitations": [
            "Owner-mirrored competition bytes are hash-pinned, not organizer-authenticated.",
            "OWNER-REPORTED scores have no submission-page receipts; conflicting prompt leaderboard claims (0.3195 / 0.4413) are unverified and unused.",
            "Fleet strata join by exact submission-stem substring; unmatched files report null rather than a guessed score.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "h33_subset": report["h33_anatomy"]["h33_is_exact_subset_of_parent"],
        "removed": report["h33_anatomy"]["removed_dots"],
        "removed_dcat": removed_distances,
        "nn_min": report["h33_anatomy"]["h33_nn_spacing_px"]["min"],
        "gzz_corr_sigma5": report["gzzd_band_qc"]["corr_gzz_vs_neg_laplacian_band13"],
        "fleet_rows": len(fleet),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
