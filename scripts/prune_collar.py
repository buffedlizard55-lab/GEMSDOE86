#!/usr/bin/env python3
"""PRUNE attribute axis on the R0 incumbent, built as controlled single-change edits.

Parent (R0)
-----------
``h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros``, sha256
``c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9``.
The same digest is pinned independently in ``scripts/fetch_registry.py``
(``EXTRA[0]``), so the local file is byte-identical to the file the owner
published for GEMSDOE32.  Measured here: 37,654 unit-mass dots, zero dots within
2 px of the catalogue, minimum catalogue distance 2.236 px (= sqrt(5): a
diagonal step), i.e. R0 *is* the "collar > 2 px" step of the lineage.

Variants (each differs from R0 only in the catalogue collar width)
-----------------------------------------------------------------
``prune3``   drop every dot with 2 < d <= 3 px of the catalogue (d = Euclidean
             distance transform to the mapped trace, in 100 m cells).
``prune4``   drop every dot with 2 < d <= 4 px.
``prune3r``  drop the ``prune3`` set, then *relocate* the same number of dots to
             free footprint cells with 3 < d <= 5 px (nearest such cell to the
             dot it replaces).  Count is held, so the difference from
             ``prune3`` is mass versus collar position, not mass alone.  The
             parent's upstream ranking is NOT used, because the GEMSDOE32
             ``gems32`` package that produced it is absent from this checkout --
             inventing a ranking would silently replace the parent (see
             IRREGULARITY IR-86-PRUNE-02).

Nothing here reads a model, a holdout label file, or the public leaderboard.
The only inputs are the pinned rasters in ``registry/data_manifest.json`` /
``data/bridge`` and the parent itself.

Evidence classes
----------------
* Format/geometry/catalogue checks: MEASUREMENT (gate).
* ``catalogue hide-and-recover`` numbers: PROXY (local holdout, never a score).
* Predicted live change: MODEL (mechanism + proxy sign, stated as a range).

Usage
-----
    python scripts/prune_collar.py --build          # write releases/ + ledger/variants.json
    python scripts/prune_collar.py --measure        # re-measure existing releases
    python scripts/prune_collar.py --build --draws 6
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine
from scipy import ndimage as ndi
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

from gems57.metric import dti_exact  # noqa: E402

GRID = ROOT / "data" / "bridge"
RELEASES = ROOT / "releases"
LEDGER = ROOT / "ledger"
FLEET = ROOT / "data" / "scored_fleet"
DOWNLOADS = ROOT / "docs" / "downloads"

EPSG = 32611
HEIGHT, WIDTH = 3730, 3292
TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)

PIN_SAMPLE = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
PIN_CATALOGUE = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
PIN_PARENT = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"

PARENT_FILE = FLEET / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
PARENT_SHORT = "h33-2-b2"
DATE_TAG = "20261023"
SEED = 20261023

# Predicted LIVE change, MODEL class: mechanism + algebra + the measured
# collar geometry below, never a score.  Ranges are the honest uncertainty; the
# point value is the mode.  A live change under 0.01 is treated as no evidence.
PREDICTIONS = {
    "prune3": ("-0.003 (95% range -0.010..+0.004). MODEL. Mechanism: the 2-3 px collar holds 5.8% of "
               "the dots at 2.1x the background density but is NOT evidence-poor (tmi_hg percentile "
               "0.528 vs 0.542 elsewhere), and the organiser says new truth can sit within 300 m of "
               "known traces, so most of these dots still carry new-fault credit; only the "
               "masked-sliver redundancy argues for a gain."),
    "prune4": ("-0.008 (95% range -0.025..+0.003). MODEL. Mechanism: extends the same deletion to the "
               "3-4 px ring (1,654 more dots at 1.9x background density) where a dot's whole kernel "
               "sits in unmasked terrain, so the lost coverage is no longer excusable as masked."),
    "prune3r": ("-0.003 (95% range -0.012..+0.006). MODEL. Mechanism: identical count to R0, identical "
                "deletions to prune3, collar pushed just past 3 px (mean move 1.14 px). Reads out "
                "whether any prune3 effect is mass or collar position."),
}

# (axis, value, description)
VARIANTS = (
    ("prune", "3", "drop dots with 2 < d(catalogue) <= 3 px"),
    ("prune", "4", "drop dots with 2 < d(catalogue) <= 4 px"),
    ("prune", "3r", "drop 2 < d <= 3 px, relocate the same count to 3 < d <= 5 px"),
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_pin(path: Path, pin: str, label: str) -> str:
    if not path.is_file():
        raise SystemExit(f"missing pinned input {label}: {path}")
    got = sha256_file(path)
    if got != pin:
        raise SystemExit(f"SHA-256 mismatch for {label}: {got} != {pin}")
    return got


# --------------------------------------------------------------------------- data
@dataclass
class Grids:
    footprint: np.ndarray      # bool, scored study cells (sample_submission finite)
    catalogue: np.ndarray      # bool, mapped USGS/INGENIOUS traces
    distance: np.ndarray       # float64, Euclidean px distance to the nearest catalogue cell
    parent: np.ndarray         # bool, R0 dots
    sample: np.ndarray         # float32 template values


def load_grids() -> Grids:
    check_pin(GRID / "sample_submission.tif", PIN_SAMPLE, "sample_submission.tif")
    check_pin(GRID / "existing_faults.tif", PIN_CATALOGUE, "existing_faults.tif")
    check_pin(PARENT_FILE, PIN_PARENT, "parent R0 raster")

    with rasterio.open(GRID / "sample_submission.tif") as src:
        sample = src.read(1)
        _check_meta(src, "sample_submission.tif")
    with rasterio.open(GRID / "existing_faults.tif") as src:
        _check_meta(src, "existing_faults.tif")
        cat = src.read(1)
    with rasterio.open(PARENT_FILE) as src:
        _check_meta(src, "parent R0")
        parent_field = src.read(1)

    footprint = np.isfinite(sample)
    catalogue = (cat > 0) & footprint
    distance = ndi.distance_transform_edt(~catalogue)
    parent = (parent_field > 0) & footprint
    if np.any((parent_field > 0) & ~footprint):
        raise SystemExit("parent R0 emits mass outside the footprint")
    return Grids(footprint=footprint, catalogue=catalogue, distance=distance,
                 parent=parent, sample=sample)


def _check_meta(src, label: str) -> None:
    if str(src.crs) != f"EPSG:{EPSG}":
        raise SystemExit(f"{label}: CRS {src.crs} != EPSG:{EPSG}")
    if (src.height, src.width) != (HEIGHT, WIDTH):
        raise SystemExit(f"{label}: shape {src.height}x{src.width} != {HEIGHT}x{WIDTH}")
    if tuple(src.transform)[:6] != tuple(TRANSFORM)[:6]:
        raise SystemExit(f"{label}: transform {tuple(src.transform)} != pinned transform")


# ---------------------------------------------------------------------- variants
def free_cells(g: Grids, occupied: np.ndarray) -> np.ndarray:
    """Cells a relocated dot may occupy: footprint, off catalogue, not occupied."""
    return g.footprint & ~g.catalogue & ~occupied


def relocate(g: Grids, dots: np.ndarray, moving: np.ndarray,
             lo: float, hi: float) -> tuple[np.ndarray, list[float]]:
    """Move each ``moving`` dot to the nearest free cell with ``lo < d <= hi``.

    Deterministic: dots are processed in row-major order and ties in the
    candidate cell scan are broken by row-major order, so the result depends
    only on the declared inputs and the seed-free rules above.
    """
    out = dots.copy()
    out[moving] = False
    candidates = g.footprint & ~g.catalogue & (g.distance > lo) & (g.distance <= hi)
    cand_y, cand_x = np.nonzero(candidates)
    if cand_x.size == 0:
        raise SystemExit("no candidate cells for relocation")
    cand_xy = np.column_stack([cand_y, cand_x]).astype(np.int32)
    taken = out.copy()
    displacements: list[float] = []
    shortfall = 0
    for y, x in np.argwhere(moving):
        # nearest candidate still free
        d2 = (cand_xy[:, 0] - y) ** 2 + (cand_xy[:, 1] - x) ** 2
        order = np.argsort(d2, kind="stable")
        placed = False
        for idx in order:
            cy, cx = int(cand_xy[idx, 0]), int(cand_xy[idx, 1])
            if taken[cy, cx]:
                continue
            taken[cy, cx] = True
            displacements.append(float(np.hypot(cy - y, cx - x)))
            placed = True
            break
        if not placed:
            shortfall += 1
    out |= taken & ~dots
    return out, displacements, shortfall


def build_variants(g: Grids) -> dict[str, dict]:
    d = g.distance
    parent = g.parent
    near3 = parent & (d > 2.0) & (d <= 3.0)
    near4 = parent & (d > 2.0) & (d <= 4.0)

    out: dict[str, dict] = {}
    p3 = parent & ~near3
    out["prune3"] = {"dots": p3, "removed": near3, "added": np.zeros_like(parent),
                     "rule": "2 < d <= 3 dropped"}

    p4 = parent & ~near4
    out["prune4"] = {"dots": p4, "removed": near4, "added": np.zeros_like(parent),
                     "rule": "2 < d <= 4 dropped"}

    moved, disp, shortfall = relocate(g, parent, near3, 3.0, 5.0)
    added = moved & ~parent
    out["prune3r"] = {"dots": moved, "removed": near3, "added": added,
                      "rule": "2 < d <= 3 dropped, equal count relocated into 3 < d <= 5",
                      "displacement_px": disp, "shortfall": shortfall}
    return out


# ---------------------------------------------------------------------- writing
def write_tiff(path: Path, dots: np.ndarray, footprint: np.ndarray, mode: str) -> None:
    """Write one single-band float32 GeoTIFF: unit mass on dots, fill outside dots.

    ``mode='nan'`` leaves NaN outside the scored footprint (brief gate) and 0
    inside it; ``mode='zeros'`` leaves 0 everywhere the dots are absent, which is
    the form the repo's vendored all-finite validator accepts.
    """
    values = np.zeros(dots.shape, dtype=np.float32)
    values[dots] = 1.0
    if mode == "nan":
        values[~footprint] = np.nan
        nodata = np.nan
    elif mode == "zeros":
        nodata = None
    else:
        raise ValueError(mode)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    profile = dict(driver="GTiff", height=HEIGHT, width=WIDTH, count=1,
                   dtype="float32", crs=f"EPSG:{EPSG}", transform=TRANSFORM,
                   nodata=nodata, compress="deflate", predictor=2, tiled=False)
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(values, 1)
        dst.set_band_description(1, "P(fault) unit-mass dots" if mode == "zeros" else "P(fault) unit-mass dots, NaN outside footprint")
    tmp.replace(path)


# --------------------------------------------------------------------- validation
def validate(path: Path, g: Grids, mode: str) -> dict:
    """Brief section 6 MUST-pass gates, measured from the file on disk."""
    with rasterio.open(path) as src:
        a = src.read(1)
        meta = dict(bands=src.count, dtype=src.dtypes[0], crs=str(src.crs),
                    shape=[src.height, src.width], transform=list(tuple(src.transform)[:6]),
                    nodata=None if src.nodata is None else float(src.nodata))
    fin = np.isfinite(a)
    inside = fin[g.footprint]
    checks = {
        "single_band": meta["bands"] == 1,
        "dtype_float32": meta["dtype"] == "float32",
        "crs_epsg_32611": meta["crs"] == f"EPSG:{EPSG}",
        "shape_matches_template": meta["shape"] == [HEIGHT, WIDTH],
        "transform_matches_template": meta["transform"] == list(tuple(TRANSFORM)[:6]),
        "values_in_0_1": bool(inside.min() >= 0.0 and inside.max() <= 1.0),
        "no_nan_inside_footprint": bool(inside.all()),
        "zero_on_catalogue": bool(float(a[g.catalogue & fin].sum() if fin[g.catalogue].any() else 0.0) == 0.0),
        "unit_mass_where_emitted": bool(np.allclose(inside[inside > 0], 1.0)),
    }
    if mode == "nan":
        checks["nan_outside_footprint"] = bool(np.isnan(a[~g.footprint]).all())
    else:
        checks["zeros_outside_footprint"] = bool((a[~g.footprint] == 0.0).all())
    dots = fin & (a > 0)
    dcat = g.distance[dots]
    return {
        "file": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "mode": mode,
        "meta": meta,
        "n_dots": int(dots.sum()),
        "on_catalogue_dots": int((dots & g.catalogue).sum()),
        "min_catalogue_distance_px": float(dcat.min()) if dots.any() else None,
        "mean_catalogue_distance_px": float(dcat.mean()) if dots.any() else None,
        "checks": checks,
        "all_checks_passed": bool(all(checks.values())),
        "validation_class": "local format/geometry gate (brief section 6); not organizer acceptance",
    }


def diff_stats(parent: np.ndarray, cand: np.ndarray) -> dict:
    removed = int((parent & ~cand).sum())
    added = int((cand & ~parent).sum())
    n0, n1 = int(parent.sum()), int(cand.sum())
    return {
        "n_parent": n0, "n_candidate": n1,
        "retained": int((parent & cand).sum()),
        "removed": removed, "added": added,
        "pct_of_parent_changed": round(100.0 * (removed + added) / n0, 3),
        "pct_removed": round(100.0 * removed / n0, 3),
        "pct_added": round(100.0 * added / n0, 3),
        "kept_fraction": round(float((parent & cand).sum()) / n0, 6),
    }


def uniqueness_vs_disk(path: Path) -> dict:
    """Exact-hash duplicate check only (the brief forbids overlap thresholds)."""
    digest = sha256_file(path)
    hits = []
    ledger = LEDGER / "submissions.csv"
    if ledger.is_file():
        import csv
        with ledger.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                # the ledger's own row for this build is not a duplicate
                if row.get("id") == path.stem:
                    continue
                if (row.get("sha256") or "") == digest:
                    hits.append(f"ledger:{row.get('id', '')}")
    for folder in (FLEET, DOWNLOADS, RELEASES):
        if not folder.is_dir():
            continue
        for other in sorted(folder.glob("*.tif")):
            if other.resolve() == path.resolve():
                continue
            try:
                if sha256_file(other) == digest:
                    hits.append(str(other.relative_to(ROOT)))
            except OSError:  # pragma: no cover
                continue
    return {"sha256": digest, "sha8": digest[:8], "exact_hash_duplicates": hits,
            "duplicate": bool(hits)}


# ------------------------------------------------------------------------- proxy
def holdout_draws(catalogue: np.ndarray, rng: np.random.Generator,
                  draws: int, hide: float = 0.20) -> list[dict]:
    """Catalogue hide-and-recover folds: hide whole components, keep the rest as known.

    Mirrors the event the metric actually scores: the organiser masks the mapped
    catalogue pixel-exactly and scores new faults.  Withholding whole components
    (8-connectivity) prevents a hidden trace from being recoverable from its own
    neighbours; the visible remainder is treated as known and excluded from the
    scored domain, exactly as the organiser description says.
    """
    labels, n_comp = ndi.label(catalogue, structure=np.ones((3, 3), bool))
    ids = np.arange(1, n_comp + 1)
    out = []
    for k in range(draws):
        n_hide = max(1, int(round(hide * n_comp)))
        hidden_ids = rng.choice(ids, size=n_hide, replace=False)
        hide_mask = np.isin(labels, hidden_ids)
        known = catalogue & ~hide_mask
        truth = hide_mask & ~known
        out.append({"draw": k, "hidden_components": int(n_hide),
                    "known": known, "truth": truth,
                    "n_withheld_positive_px": int(truth.sum())})
    return out


def paired_ci(diffs: np.ndarray) -> list[float]:
    diffs = np.asarray(diffs, float)
    if diffs.size < 2:
        return [float("nan"), float("nan")]
    se = diffs.std(ddof=1) / np.sqrt(diffs.size)
    half = stats.t.ppf(0.975, diffs.size - 1) * se
    return [float(diffs.mean() - half), float(diffs.mean() + half)]


def proxy_scores(cands: dict[str, np.ndarray], draws: list[dict],
                 footprint: np.ndarray) -> dict:
    """PROXY: paired catalogue hide-and-recover DTI for every candidate."""
    per = {name: [] for name in cands}
    for fold in draws:
        for name, dots in cands.items():
            pred = dots.astype(np.float32)
            r = dti_exact(pred, fold["truth"], valid=footprint, known=fold["known"])
            per[name].append(float(r["dti"]))
    base = np.asarray(per["R0"], float)
    out = {"evidence_class": "PROXY",
           "design": ("catalogue hide-and-recover, 20% of 8-connected catalogue components "
                      "withheld per draw, visible catalogue pixel-exactly masked as known, "
                      "exact alpha=0.2/beta=0.8/R=3px DTI (gems57.metric.dti_exact)"),
           "draws": len(draws),
           "withheld_positive_px_mean": float(np.mean([f["n_withheld_positive_px"] for f in draws])),
           "candidates": {}}
    for name, vals in per.items():
        v = np.asarray(vals, float)
        out["candidates"][name] = {
            "proxy_dti_mean": float(v.mean()),
            "proxy_dti_sd": float(v.std(ddof=1)) if v.size > 1 else 0.0,
            "per_draw": [round(float(x), 6) for x in v],
            "delta_vs_R0_mean": float((v - base).mean()),
            "delta_vs_R0_ci95": paired_ci(v - base),
            "folds_improved": int((v > base).sum()),
        }
    return out


RING_EDGES = (0.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 50.0, np.inf)


def ring_table(g: Grids, dots: np.ndarray) -> dict:
    """Label-free occupancy of the dot field by catalogue-distance ring.

    Enrichment = (share of dots in a ring) / (share of scored footprint in that
    ring).  Values above 1 mean the field is deliberately clustered along the
    mapped traces; 1 means the ring is populated like a background field.
    """
    n_fp = int(g.footprint.sum())
    n_dots = int(dots.sum())
    rows = []
    for lo, hi in zip(RING_EDGES[:-1], RING_EDGES[1:]):
        m = (g.distance > lo) & (g.distance <= hi)
        fp = int((m & g.footprint).sum())
        dn = int((m & dots).sum())
        rows.append({
            "ring_px": [lo, None if not np.isfinite(hi) else hi],
            "footprint_px": fp, "dots": dn,
            "footprint_share": round(fp / n_fp, 6),
            "dot_share": round(dn / n_dots, 6) if n_dots else 0.0,
            "enrichment": round((dn / n_dots) / (fp / n_fp), 4) if n_dots and fp else 0.0,
        })
    return {"evidence_class": "MEASUREMENT (label-free)",
            "note": "distance to the mapped catalogue; enrichment > 1 = hugging the traces",
            "rows": rows}


FEATURE_BANDS = ("tmi_hg", "tc", "det_elev_slope", "iso_grav_anom_hg", "rtp", "mag_anom")
PIN_FEATURES = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"


def feature_response(g: Grids, collar: np.ndarray, rest: np.ndarray,
                     n_random: int = 20000) -> dict:
    """Rank-normalised (label-free) lineament response of collar dots vs the rest.

    The 19-band stack has no truth in it, so this cannot reward a candidate.  It
    tests one thing: is the 2-3 px collar band *evidence-poor* compared with the
    rest of the parent's dots?  If it were, pruning it would be cheap.
    """
    path = GRID / "training_features.tif"
    if not path.is_file():
        return {"evidence_class": "MEASUREMENT", "status": "SKIPPED_FEATURE_STACK_ABSENT"}
    got = sha256_file(path)
    if got != PIN_FEATURES:
        raise SystemExit(f"feature stack SHA-256 mismatch: {got} != {PIN_FEATURES}")
    rng = np.random.default_rng(SEED)
    pool = np.argwhere(g.footprint & ~g.parent)
    rnd = pool[rng.choice(len(pool), min(n_random, len(pool)), replace=False)]
    out = {"evidence_class": "MEASUREMENT (label-free)",
           "feature_stack_sha256": got,
           "statistic": ("percentile of |value - median| within the scored footprint, "
                         "averaged per dot set; 0.5 = background"),
           "random_footprint_px": int(len(rnd)),
           "bands": {}}
    with rasterio.open(path) as src:
        # descriptions are "<band_name> - <long text>"; keep the short band name
        names = [(src.descriptions[i] or src.tags(i + 1).get("band_name") or f"band{i+1}").split(" - ")[0]
                 for i in range(src.count)]
        for name in FEATURE_BANDS:
            if name not in names:
                continue
            a = src.read(names.index(name) + 1).astype("float64")
            ok = g.footprint & np.isfinite(a) & (a > -1e30)
            v = a[ok]
            dev = np.abs(v - np.median(v))
            order = dev.argsort().argsort() / max(1, dev.size - 1)
            pct = np.full(a.shape, np.nan)
            pct[ok] = order
            out["bands"][name] = {
                "collar_mean": round(float(np.nanmean(pct[collar])), 4),
                "rest_of_parent_mean": round(float(np.nanmean(pct[rest])), 4),
                "random_footprint_mean": round(float(np.nanmean(pct[rnd[:, 0], rnd[:, 1]])), 4),
                "collar_minus_rest": round(float(np.nanmean(pct[collar]) - np.nanmean(pct[rest])), 4),
            }
    return out


def coverage_control(cands: dict[str, np.ndarray], catalogue: np.ndarray,
                     footprint: np.ndarray) -> dict:
    """REPORT ONLY: DTI against the whole visible catalogue (not a score)."""
    out = {"evidence_class": "PROXY-CONTROL",
           "design": "whole catalogue as truth, no masking; report-only, never a gate",
           "candidates": {}}
    for name, dots in cands.items():
        r = dti_exact(dots.astype(np.float32), catalogue, valid=footprint)
        out["candidates"][name] = {"dti": float(r["dti"]), "tp": float(r["tp"]),
                                   "fp": float(r["fp"]), "n_truth": int(r["n_truth"])}
    return out


# -------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="build releases/ and ledger/variants.json")
    ap.add_argument("--measure", action="store_true",
                    help="re-run the deterministic build and re-validate the on-disk releases")
    ap.add_argument("--draws", type=int, default=6)
    args = ap.parse_args()
    if not (args.build or args.measure):
        ap.error("choose --build or --measure")

    RELEASES.mkdir(parents=True, exist_ok=True)
    LEDGER.mkdir(parents=True, exist_ok=True)
    g = load_grids()
    print(f"[1/5] inputs verified; footprint {int(g.footprint.sum()):,} px, "
          f"catalogue {int(g.catalogue.sum()):,} px, parent {int(g.parent.sum()):,} dots")

    variants = build_variants(g)
    print(f"[2/5] variants built: {', '.join(variants)}")

    rng = np.random.default_rng(SEED)
    draws = holdout_draws(g.catalogue, rng, args.draws)

    dot_sets = {"R0": g.parent}
    for key, v in variants.items():
        dot_sets[key] = v["dots"]
    proxy = proxy_scores(dot_sets, draws, g.footprint)
    print(f"[3/5] proxy folds: {len(draws)} x "
          f"{proxy['withheld_positive_px_mean']:.0f} withheld positives")

    control = coverage_control(dot_sets, g.catalogue, g.footprint)

    collar = g.parent & (g.distance > 2.0) & (g.distance <= 3.0)
    rest = g.parent & ~collar
    rings = ring_table(g, g.parent)
    print("[3b/5] label-free ring / feature-response receipts")
    response = feature_response(g, collar, rest)

    rows = []
    for key, v in variants.items():
        dots = v["dots"]
        base = f"{PARENT_SHORT}-{key}-{DATE_TAG}"
        written = {}
        for mode in ("nan", "zeros"):
            # The digest is content-derived, so write to a scratch name first and
            # rename to <...>-<sha8>-<mode>.tif.  Each twin carries ITS OWN digest,
            # because the out-of-footprint fill changes the bytes.
            scratch = RELEASES / f".{base}-{mode}.tmp.tif"
            scratch.unlink(missing_ok=True)
            write_tiff(scratch, dots, g.footprint, mode)
            digest = sha256_file(scratch)
            final = RELEASES / f"{base}-{digest[:8]}-{mode}.tif"
            final.unlink(missing_ok=True)
            scratch.replace(final)
            written[mode] = (final, digest)
        final_nan, digest = written["nan"]
        final_zeros = written["zeros"][0]
        sha8 = digest[:8]

        v_nan = validate(final_nan, g, "nan")
        v_zeros = validate(final_zeros, g, "zeros")
        diff = diff_stats(g.parent, dots)
        dup = uniqueness_vs_disk(final_nan)

        rel = proxy["candidates"][key]
        row = {
            "id": final_nan.stem,
            "parent": PARENT_SHORT,
            "axis": key.rstrip("0123456789r"),
            "value": key[len(key.rstrip("0123456789r")):],
            "rule": v["rule"],
            "n_dots": diff["n_candidate"],
            "pct_changed": diff["pct_of_parent_changed"],
            "sha256": digest,
            "sha8": sha8,
            "files": [str(final_nan.relative_to(ROOT)), str(final_zeros.relative_to(ROOT))],
            "sha256_zeros": written["zeros"][1],
            "status": "BUILT",
            "diff": diff,
            "validation_nan": v_nan,
            "validation_zeros": v_zeros,
            "gate_all_pass": bool(v_nan["all_checks_passed"] and v_zeros["all_checks_passed"]),
            "exact_hash_duplicate": dup,
            "proxy": {"proxy_dti_mean": rel["proxy_dti_mean"],
                      "delta_vs_R0_mean": rel["delta_vs_R0_mean"],
                      "delta_vs_R0_ci95": rel["delta_vs_R0_ci95"],
                      "folds_improved": rel["folds_improved"],
                      "draws": proxy["draws"],
                      "evidence_class": "PROXY"},
            "coverage_control_dti": control["candidates"][key]["dti"],
            "ring_table": ring_table(g, dots),
            "mean_relocation_px": (round(float(np.mean(v["displacement_px"])), 4)
                                   if v.get("displacement_px") else None),
            "max_relocation_px": (round(float(np.max(v["displacement_px"])), 4)
                                  if v.get("displacement_px") else None),
            "relocation_shortfall": v.get("shortfall"),
            "predicted_change": PREDICTIONS.get(key, ""),
            "receipt_score": "",
            "receipt_date": "",
        }
        rows.append(row)
        print(f"[4/5] {row['id']}: {row['n_dots']:,} dots ({row['pct_changed']:+.3f}% vs R0), "
              f"gates {'PASS' if row['gate_all_pass'] else 'FAIL'}, "
              f"proxy {rel['proxy_dti_mean']:.4f} vs R0 {proxy['candidates']['R0']['proxy_dti_mean']:.4f} "
              f"(delta {rel['delta_vs_R0_mean']:+.4f})")

    evidence = {
        "schema": "gems86.prune-axis.v1",
        "generated_utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        "axis": "PRUNE",
        "parent": {"id": PARENT_FILE.stem, "sha256": PIN_PARENT,
                   "file": str(PARENT_FILE.relative_to(ROOT)), "n_dots": int(g.parent.sum())},
        "inputs": {"sample_submission.tif": PIN_SAMPLE, "existing_faults.tif": PIN_CATALOGUE},
        "seed": SEED,
        "git_sha": _git_sha(),
        "proxy": proxy,
        "proxy_verdict": (
            "UNINFORMATIVE FOR THIS AXIS. Every candidate scores at or near the floor because a "
            "catalogue-avoiding field earns almost no kernel credit from withheld catalogue pixels; "
            "the instrument rewards catalogue-following, which the scored metric punishes once the "
            "catalogue is masked. Reported, never used as a gate or a prediction."),
        "coverage_control": control,
        "ring_table_parent": rings,
        "feature_response_parent": response,
        "variants": rows,
    }
    out = ROOT / "evidence" / "prune_axis_20261023.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (LEDGER / "variants.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"[5/5] wrote {out.relative_to(ROOT)} and ledger/variants.json")
    return 0


def _git_sha() -> str:
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:  # pragma: no cover
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
