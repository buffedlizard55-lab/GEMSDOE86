#!/usr/bin/env python3
"""Build, gate and card the three SNAP variants of parent R0 (GEMSDOE32 h33-h33-2-b2).

Axis assigned by the human for this session: SNAP, response family "magnetic edges
(tmi_hg / tc)".  Rule, gate and constants below were fixed **before** any variant was
scored; the pre-registration is ``registry/preregistration_snap.json``.

Parent R0
---------
``GEMSDOE32 docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif``
sha256 ``c55bafc4...``, 37,654 unit-mass dots, 0 on the catalogue, min catalogue
distance 2.24 px, own nearest-neighbour floor 2.828 px (the d2.8 rung).
Its dot set is reproduced exactly here from the recorded recipe
(dot the 0.2708 base at rung 2.8, then delete every dot at d(catalogue) <= 2 px);
symdiff must be 0 or this script aborts.

Shared SNAP rule (identical for all three variants; only the response FIELD changes)
------------------------------------------------------------------------------------
For variant ``v`` with response field ``R_v`` (z-scored over the footprint):

1. ``R_v`` is a Gaussian-smoothed (sigma = 1 px = 100 m) magnetic-edge measure.
   Smoothing at one cell is declared *a priori*: the raw 100 m bands carry
   interpolation noise between the 400 m GeoDAWN flight lines, and a diagnostic run
   before this file existed showed raw-field snapping moves 99 % of dots with a
   per-dot gain barely above a random-offset null.
2. Window: the 25 cells with max(|dy|, |dx|) <= 2 (the brief's "<= 2 px").
3. Valid destinations: inside the footprint, NOT on the catalogue, finite ``R_v``,
   and not another dot's source pixel (sources stay reserved, which is what makes
   the dot count exact by construction).
4. A dot moves only if the best valid gain ``R_v(dest) - R_v(source) >= GAIN_GATE``
   (0.25 field standard deviations).  Otherwise it stays where it is.
5. Dots are placed greedily in descending best-gain order; each takes the
   highest-``R_v`` candidate that is unclaimed and at Euclidean distance
   >= ``SPACING_FLOOR_PX`` (R0's own 2.828 px) from every claimed cell, so SNAP
   cannot manufacture the clustering the 3 px kernel punishes.
6. Ties break to the smaller displacement, then to (row, col).  No randomness, so
   the build is deterministic and the seed is irrelevant (recorded as seed 0).

Variant fields (the axis values)
--------------------------------
``hg2``    z(smooth(tmi_hg))                       -- horizontal-gradient magnitude peak
``vg2``    z(smooth(|tmi_vg|))                     -- vertical-gradient flank peak (sharper)
``cons2``  z(smooth(tmi_hg)) + z(smooth(|tmi_vg|)) -- consensus of both magnetic derivatives

Nothing here contacts drivendata.org, dropbox.com or any leaderboard; no label probing:
no region-isolated or patterned file is built.  Inputs are only the hash-pinned files in
``registry/data_manifest.json`` (verified below) plus the parent raster.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))

VERSION = "gems86-snap-v1"
PARENT_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
PARENT_REL = ("data/scored_fleet/"
              "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
BASE_REL = ("data/scored_fleet/"
            "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif")
BASE_SHA = "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"
BRIDGE = ROOT / "data" / "bridge"
FEATURES = ROOT / ".cache" / "bridge" / "training_features.tif"
H19_5 = ROOT / ".cache" / "scored" / "h19_5.tif"
FEATURES_SHA = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
H19_5_SHA = "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d"
CAT_SHA = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
SAMPLE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"

NODATA = -3.4028234663852886e+38
SMOOTH_SIGMA_PX = 1.0
CAP_PX = 2
GAIN_GATE = 0.25            # field standard deviations
SPACING_FLOOR_PX = 2.828    # R0's own nearest-neighbour floor (d2.8 rung)
SEED = 0                    # unused: the rule is deterministic
DATE_TAG = "20261023"

VARIANTS = {
    "hg2": {"field": "hg", "label": "tmi_hg horizontal-gradient peak"},
    "vg2": {"field": "vg", "label": "|tmi_vg| vertical-gradient flank peak"},
    "cons2": {"field": "cons", "label": "tmi_hg + |tmi_vg| consensus"},
}

MECHANISM = {
    "hg2": dict(
        hypothesis="A dot's 100 m position is uncertain by about the kernel radius, so moving it "
                   "up to 2 px onto the local maximum of the horizontal magnetic gradient "
                   "recovers true-trace credit the kernel currently only half-credits.",
        mechanism="Faults and their damage zones truncate or offset magnetised units, so the "
                  "horizontal gradient of TMI peaks along the structure. The grader gives a "
                  "triangular credit max(1-d/3px,0), so a dot displaced 2 px from truth keeps "
                  "only 0.33 of its unit credit; the same dot re-centred earns ~1.0.",
        confounder="Magnetic contacts with no Quaternary slip (intrusive contacts, remanence "
                   "boundaries, survey seams between flight-line blocks) produce the same "
                   "gradient peak; so do shallow alluvial magnetic contrasts.",
        predicted="MODEL: live change in [-0.005, +0.015], central +0.004. Below the 0.01 "
                  "evidence floor this is a mechanism probe, not a score play.",
        falsifier="Live change <= -0.02 kills the positional-correction reading (the dots were "
                  "already on true traces and the gradient peak is a mimicking contact); "
                  "|change| < 0.01 is no evidence in either direction.",
    ),
    "vg2": dict(
        hypothesis="If sharpness is what the kernel rewards, the vertical gradient should snap "
                   "better than the horizontal one, because it localises a contact more tightly.",
        mechanism="The vertical derivative of a potential field is a shorter-wavelength "
                  "enhancement of the same source edge; at a given flight-line spacing it "
                  "discriminates neighbouring contacts that the horizontal gradient smears "
                  "into one 2 px-wide maximum.",
        confounder="Short-wavelength enhancement amplifies interpolation noise between the "
                   "400 m GeoDAWN lines, so the 'peak' can be an artifact of the survey "
                   "geometry rather than the geology.",
        predicted="MODEL: live change in [-0.008, +0.015], central +0.003.",
        falsifier="vg2 weaker than hg2 by more than 0.01 argues that the extra sharpening is "
                  "noise; vg2 beating hg2 by >= 0.01 would say kernel-scale sharpness, not "
                  "edge existence, is the binding constraint.",
    ),
    "cons2": dict(
        hypothesis="The two magnetic derivatives disagree where one of them is artefact-"
                   "dominated, so their consensus peak should be the more reliable positional "
                   "estimate even though it is broader.",
        mechanism="Averaging two edge measures that are sensitive to the same source but to "
                  "different noise keeps the shared (geological) peak and suppresses the "
                  "band-specific seam and interpolation artefacts.",
        confounder="Where both bands share one artefact (a flight-line seam distorts every "
                   "derivative at once) consensus adds no robustness at all.",
        predicted="MODEL: live change in [-0.005, +0.015], central +0.005; expected to be the "
                  "most stable of the three if any of them works.",
        falsifier="cons2 outside the hg2/vg2 spread, i.e. worse than both, would mean the "
                  "consensus peak lands on a compromise neither band supports.",
    ),
}


# --------------------------------------------------------------------------- inputs
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_inputs() -> dict:
    pins = {BRIDGE / "existing_faults.tif": CAT_SHA,
            BRIDGE / "sample_submission.tif": SAMPLE_SHA,
            ROOT / PARENT_REL: PARENT_SHA,
            ROOT / BASE_REL: BASE_SHA,
            FEATURES: FEATURES_SHA,
            H19_5: H19_5_SHA}
    receipt = {}
    for path, pin in pins.items():
        if not path.is_file():
            raise SystemExit(f"missing pinned input {path} (run scripts/restore_data.py; "
                             f"h19_5 comes from the manifest entry 'scored_h19_5')")
        got = sha256(path)
        if got != pin:
            raise SystemExit(f"SHA-256 mismatch for {path}: {got} != {pin}")
        receipt[str(path.relative_to(ROOT))] = {"sha256": got, "verified": True}
    # the parent's own documented recipe, re-derived here rather than trusted
    with rasterio.open(BRIDGE / "existing_faults.tif") as ds:
        catalogue = ds.read(1) == 1
    with rasterio.open(ROOT / PARENT_REL) as ds:
        parent = ds.read(1) > 0
        parent_profile = ds.profile.copy()
    with rasterio.open(ROOT / BASE_REL) as ds:
        base = ds.read(1) > 0
    from scipy.ndimage import distance_transform_edt
    rebuilt = base & (distance_transform_edt(~catalogue) > 2)
    if not np.array_equal(rebuilt, parent):
        raise SystemExit(f"parent dot-set not reproduced from its recipe: "
                         f"symdiff {int((rebuilt ^ parent).sum())} px")
    receipt["parent_recipe_reproduction"] = {"symdiff_px": 0, "dots": int(parent.sum())}
    return {"pins": receipt, "catalogue": catalogue, "parent": parent,
            "parent_profile": parent_profile}


# ------------------------------------------------------------------------ responses
def _z(a: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    v = a[footprint]
    return (a - float(np.median(v))) / float(np.std(v))


def response_fields(footprint: np.ndarray) -> dict[str, np.ndarray]:
    with rasterio.open(FEATURES) as ds:
        idx = {ds.descriptions[i].split(" - ")[0]: i + 1 for i in range(ds.count)}
        hg = ds.read(idx["tmi_hg"]).astype(np.float64)
        vg = ds.read(idx["tmi_vg"]).astype(np.float64)
    for a in (hg, vg):
        a[a == NODATA] = np.nan
    def smooth(a):
        filled = np.where(np.isfinite(a), a, np.nanmedian(a[footprint]))
        return gaussian_filter(filled, SMOOTH_SIGMA_PX, mode="nearest")
    zhg = _z(smooth(hg), footprint)
    zvg = _z(smooth(np.abs(vg)), footprint)
    return {"hg": zhg, "vg": zvg, "cons": zhg + zvg}


# ---------------------------------------------------------------------------- snap
def snap(parent: np.ndarray, R: np.ndarray, footprint: np.ndarray,
         catalogue: np.ndarray) -> tuple[np.ndarray, dict]:
    """Move each dot <= CAP_PX onto the strongest valid edge response; count preserved.

    Invariants enforced (not hoped for): the dot count is unchanged, no dot lands on the
    catalogue or outside the footprint, and no two dots end up closer than
    ``SPACING_FLOOR_PX`` -- a destination may not come within that floor of another dot's
    *source* either, so a dot blocked later cannot retro-actively create a cluster.
    """
    H, W = parent.shape
    wy, wx = np.nonzero(parent)
    n = len(wy)
    offs = [(dy, dx) for dy in range(-CAP_PX, CAP_PX + 1)
            for dx in range(-CAP_PX, CAP_PX + 1)]
    dist = np.array([float(np.hypot(dy, dx)) for dy, dx in offs], float)

    valid = np.isfinite(R) & footprint & ~catalogue
    src = (wy * W + wx)
    src_val = R[wy, wx]

    vals, dys, ys, xs, cells, oks = [], [], [], [], [], []
    for j, (dy, dx) in enumerate(offs):
        y = np.clip(wy + dy, 0, H - 1)
        x = np.clip(wx + dx, 0, W - 1)
        vals.append(R[y, x]); dys.append(np.full(n, dist[j]))
        ys.append(y); xs.append(x); cells.append(y * W + x); oks.append(valid[y, x])
    vals, dys, ys, xs = (np.stack(v, 1) for v in (vals, dys, ys, xs))
    cells, ok = np.stack(cells, 1), np.stack(oks, 1)
    gain = np.where(ok, vals - src_val[:, None], -np.inf)

    src_mask = parent.copy()
    rad = int(np.ceil(SPACING_FLOOR_PX))
    floor_sq = (SPACING_FLOOR_PX - 1e-9) ** 2

    def sources_near(y2, x2, own_y, own_x):
        """Is a source cell within the floor of (y2,x2), other than this dot's own?"""
        y0, y1 = max(0, y2 - rad), min(H - 1, y2 + rad)
        x0, x1 = max(0, x2 - rad), min(W - 1, x2 + rad)
        sub = src_mask[y0:y1 + 1, x0:x1 + 1].copy()
        if y0 <= own_y <= y1 and x0 <= own_x <= x1:
            sub[own_y - y0, own_x - x0] = False
        if not sub.any():
            return False
        yy, xx = np.nonzero(sub)
        return bool(((yy + y0 - y2) ** 2 + (xx + x0 - x2) ** 2).min() < floor_sq)

    # a dot moves only if its best valid gain clears the gate
    best_j = np.argmax(gain, axis=1)
    best_gain = gain[np.arange(n), best_j]
    move = np.isfinite(best_gain) & (best_gain >= GAIN_GATE)
    order = np.argsort(-np.where(move, best_gain, -np.inf), kind="stable")

    claimed = np.zeros(H * W, bool)

    def spacing_ok(y2, x2, own_y, own_x):
        y0, y1 = max(0, y2 - rad), min(H - 1, y2 + rad)
        x0, x1 = max(0, x2 - rad), min(W - 1, x2 + rad)
        sub = claimed.reshape(H, W)[y0:y1 + 1, x0:x1 + 1]
        if not sub.any():
            return True
        yy, xx = np.nonzero(sub)
        return bool(((yy + y0 - y2) ** 2 + (xx + x0 - x2) ** 2).min() >= floor_sq)

    owner = np.full(n, -1, np.int64)
    forced = 0
    n_blocked = 0

    # stayers claim their sources first, so movers are tested against them
    for i in np.flatnonzero(~move):
        owner[i] = int(src[i]); claimed[src[i]] = True

    for i in [k for k in order if move[k]]:   # gain-descending, movers only
        rank = np.lexsort((cells[i], dys[i], -np.where(ok[i], vals[i], -np.inf)))
        for j in rank:
            if not ok[i, j]:
                break
            c = int(cells[i, j])
            if claimed[c]:
                continue
            y2, x2 = int(ys[i, j]), int(xs[i, j])
            if sources_near(y2, x2, int(wy[i]), int(wx[i])):
                continue
            if not spacing_ok(y2, x2, int(wy[i]), int(wx[i])):
                continue
            claimed[c] = True; owner[i] = c
            break
        else:
            n_blocked += 1
        if owner[i] < 0:                       # blocked mover keeps its source
            if spacing_ok(int(wy[i]), int(wx[i]), int(wy[i]), int(wx[i])):
                owner[i] = int(src[i]); claimed[src[i]] = True
            else:
                forced += 1
                owner[i] = int(src[i]); claimed[src[i]] = True

    if (owner < 0).any():
        raise RuntimeError(f"internal: {int((owner < 0).sum())} dots unplaced")
    out = np.zeros((H, W), bool)
    oy, ox = owner // W, owner % W
    out[oy, ox] = True
    if int(out.sum()) != n:
        raise RuntimeError(f"dot count changed {int(out.sum())} != {n}")
    if np.any(out & catalogue):
        raise RuntimeError("catalogue mass emitted")

    moved = (oy != wy) | (ox != wx)
    disp = np.hypot(oy - wy, ox - wx)
    stats = {
        "n_dots": int(n),
        "n_moved": int(moved.sum()),
        "pct_changed": round(100.0 * float(moved.mean()), 2),
        "mean_displacement_px_all": round(float(disp.mean()), 3),
        "mean_displacement_px_moved": round(float(disp[moved].mean()), 3) if moved.any() else 0.0,
        "median_displacement_px_moved": round(float(np.median(disp[moved])), 3) if moved.any() else 0.0,
        "max_displacement_px": round(float(disp.max()), 3),
        "n_movers_blocked_kept_source": int(n_blocked),
        "n_forced_floor_violations": int(forced),
        "mean_gain_z_moved": round(float(best_gain[moved].mean()), 3) if moved.any() else 0.0,
        "min_spacing_px_after": round(float(_min_spacing(oy, ox)), 3),
        "min_spacing_px_before": round(float(_min_spacing(wy, wx)), 3),
        "seed": SEED,
    }
    return out, stats


def _min_spacing(y: np.ndarray, x: np.ndarray) -> float:
    d, _ = cKDTree(np.c_[y, x]).query(np.c_[y, x], k=2)
    return float(d[:, 1].min())


# ---------------------------------------------------------------------------- gates
def gate(path: Path, footprint: np.ndarray, catalogue: np.ndarray,
         expect_dots: int, nan_outside: bool) -> dict:
    """MUST-pass checks from the brief, run on the file re-read from disk."""
    with rasterio.open(BRIDGE / "sample_submission.tif") as ref:
        ref_crs, ref_shape, ref_transform, ref_dtype = ref.crs, ref.shape, ref.transform, ref.dtypes[0]
    with rasterio.open(path) as ds:
        a = ds.read(1)
        meta = dict(crs=str(ds.crs), shape=[ds.height, ds.width], dtype=ds.dtypes[0],
                    count=ds.count, transform=list(tuple(ds.transform)[:6]),
                    nodata=(None if ds.nodata is None else
                            (float(ds.nodata) if np.isfinite(ds.nodata) else str(ds.nodata))))
    finite = np.isfinite(a)
    checks = {
        "crs_matches_sample": meta["crs"] == str(ref_crs),
        "shape_matches_sample": tuple(meta["shape"]) == tuple(ref_shape),
        "transform_matches_sample": tuple(meta["transform"]) == tuple(tuple(ref_transform)[:6]),
        "dtype_float32": meta["dtype"] == "float32" == ref_dtype,
        "single_band": meta["count"] == 1,
        "values_in_0_1": bool(finite.any() and a[finite].min() >= 0.0 and a[finite].max() <= 1.0),
        "no_nan_inside_footprint": bool(np.isfinite(a[footprint]).all()),
        "zero_mass_on_catalogue": int((a[catalogue] > 0).sum()) == 0,
        "dot_count_matches_parent": int((a > 0).sum()) == expect_dots,
        "no_positive_mass_outside_footprint": int(((a > 0) & ~footprint).sum()) == 0,
    }
    if nan_outside:
        checks["nan_outside_footprint"] = bool((~np.isfinite(a[~footprint])).all())
    else:
        checks["zeros_outside_footprint"] = bool((a[~footprint] == 0.0).all())
    return {"file": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "sha256": sha256(path), "meta": meta, "checks": checks,
            "all_checks_passed": bool(all(checks.values())),
            "on_catalogue_positive_pixels": int((a[catalogue] > 0).sum()),
            "emitted_positive_pixels": int((a > 0).sum())}


def write_pair(stem: str, mask: np.ndarray, profile: dict, footprint: np.ndarray) -> list[Path]:
    out_dir = ROOT / "releases"
    out_dir.mkdir(exist_ok=True)
    written = []
    for suffix, mode in (("", "nan"), ("-zeros", "zeros")):
        p = out_dir / f"{stem}{suffix}.tif"
        arr = np.where(footprint, mask.astype(np.float32), np.nan if mode == "nan" else 0.0)
        prof = profile.copy()
        prof.update(dtype="float32", count=1, compress="deflate", predictor=2,
                    tiled=True, blockxsize=256, blockysize=256)
        if mode == "nan":
            prof["nodata"] = float("nan")
        else:
            prof["nodata"] = None
        with rasterio.open(p, "w", **prof) as dst:
            dst.write(arr.astype(np.float32), 1)
        written.append(p)
    return written


# ---------------------------------------------------------------------- proxy / report
def proxy_report(masks: dict[str, np.ndarray], footprint: np.ndarray,
                 catalogue: np.ndarray) -> dict:
    """Catalogue hide-and-recover PROXY + leakage canary.  NEVER a gate, NEVER a score."""
    from gems57 import grid as g57grid, holdout as g57
    g = g57grid.Grid(footprint=footprint, catalogue=catalogue, crs=None, transform=None,
                     height=footprint.shape[0], width=footprint.shape[1])
    ctx = g57.build_holdout(g)
    out = {}
    for name, mask in masks.items():
        ev = g57.evaluate(mask, ctx)
        per = list(ev["per_fold_dti"].values())
        out[name] = {
            "evidence_class": "PROXY (catalogue hide-and-recover, not a leaderboard score)",
            "n_withheld_positive_px": int(ev["pooled_n_truth"]),
            "pooled_dti": round(float(ev["pooled_dti"]), 4),
            "pooled_coverage": round(float(ev["pooled_coverage"]), 4),
            "coverage_wilson95": [round(v, 4) for v in
                                  g57.wilson_ci(ev["pooled_tp"], ev["pooled_n_truth"])],
            "mean_fold_dti": round(float(ev["mean_fold_dti"]), 4),
            "fold_dti_spread_95": [round(v, 4) for v in
                                   (np.percentile(per, 2.5), np.percentile(per, 97.5))],
            "per_quadrant_dti": {k: round(float(v), 4) for k, v in ev["per_quadrant_dti"].items()},
            "per_draw_dti": {k: round(float(v), 4) for k, v in ev["per_draw_dti"].items()},
            "folds": len(per),
        }
    return out


def canary_auc(fields: dict[str, np.ndarray], catalogue: np.ndarray,
               footprint: np.ndarray) -> dict:
    """Leakage canary: AUC of a single feature alone.  > 0.90 means stop and investigate."""
    from sklearn.metrics import roc_auc_score
    out = {}
    for name, R in fields.items():
        sel = footprint & np.isfinite(R)
        y = catalogue[sel]
        if y.sum() == 0:
            continue
        out[name] = round(float(roc_auc_score(y, R[sel])), 4)
    return {"catalogue_auc": out,
            "leakage_stop_threshold": 0.90,
            "verdict": "STOP: investigate" if any(v > 0.90 for v in out.values()) else "clear",
            "note": "report-only; catalogue AUC is not a prediction of new-fault performance"}


def h19_rank_readout(masks: dict[str, np.ndarray], footprint: np.ndarray) -> dict:
    """Does snapping move dots up or down the parent lineage's own ranking field?"""
    with rasterio.open(H19_5) as ds:
        h = ds.read(1).astype(np.float64)
    h[~np.isfinite(h)] = np.nan
    v = h[footprint & np.isfinite(h)]
    order = np.argsort(np.argsort(v))
    ranks = np.full(footprint.shape, np.nan)
    idx = np.flatnonzero((footprint & np.isfinite(h)).ravel())
    ranks.ravel()[idx] = order / max(len(order) - 1, 1)
    parent = masks["parent"]
    base = float(np.nanmean(ranks[parent]))
    out = {"parent_mean_rank_pct": round(base, 4)}
    for name, m in masks.items():
        if name == "parent":
            continue
        out[name] = round(float(np.nanmean(ranks[m])), 4)
        out[name + "_delta_pct_points"] = round(100 * (out[name] - base), 3)
    out["evidence_class"] = "PROXY readout on the parent lineage's ranking field (H19-5)"
    return out


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-proxy", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated variant keys")
    args = ap.parse_args()

    inputs = verify_inputs()
    catalogue, parent = inputs["catalogue"], inputs["parent"]
    with rasterio.open(BRIDGE / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    fields = response_fields(footprint)
    keys = [k.strip() for k in args.only.split(",") if k.strip()] or list(VARIANTS)

    mask_receipts = {}
    masks = {"parent": parent}
    for key in keys:
        spec = VARIANTS[key]
        mask, stats = snap(parent, fields[spec["field"]], footprint, catalogue)
        masks[key] = mask
        stem = f"h33-h33-2-b2-snap-{key}-{DATE_TAG}"
        provisional = write_pair(stem, mask, inputs["parent_profile"], footprint)
        # the released name carries the sha8 of the primary (NaN-outside) file
        primary_sha = sha256(provisional[0])[:8]
        stem_final = f"{stem}-{primary_sha}"
        files = write_pair(stem_final, mask, inputs["parent_profile"], footprint)
        for p in provisional:                               # drop the provisional copies
            if p.exists() and p.name not in {f.name for f in files}:
                p.unlink()
        gates = {}
        for p in files:
            nan_outside = not p.stem.endswith("-zeros")
            gates[p.name] = gate(p, footprint, catalogue, int(parent.sum()), nan_outside)
        mask_receipts[key] = {
            "id": stem_final, "parent": "h33-h33-2-b2",
            "axis": "SNAP", "value": key,
            "field_label": spec["label"],
            "files": {"nan_outside": files[0].name, "zeros_outside": files[1].name},
            "parent_diff": stats,
            "gates": gates,
            "mechanism_card": MECHANISM[key],
            "rule": {"smooth_sigma_px": SMOOTH_SIGMA_PX, "cap_px": CAP_PX,
                     "gain_gate_z": GAIN_GATE, "spacing_floor_px": SPACING_FLOOR_PX,
                     "window": "25 cells, max(|dy|,|dx|) <= 2"},
        }

    report = {"schema": "gems86.snap-variants.v1", "version": VERSION,
              "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "git_sha": _git_sha(), "inputs": inputs["pins"],
              "variants": mask_receipts,
              "rule_constants": {"smooth_sigma_px": SMOOTH_SIGMA_PX, "cap_px": CAP_PX,
                                 "gain_gate_z": GAIN_GATE,
                                 "spacing_floor_px": SPACING_FLOOR_PX, "seed": SEED}}
    if not args.skip_proxy:
        report["leakage_canary"] = canary_auc(fields, catalogue, footprint)
        report["holdout_proxy"] = proxy_report(masks, footprint, catalogue)
        report["h19_rank_readout"] = h19_rank_readout(masks, footprint)

    out = ROOT / "evidence" / "snap_variants.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(_clean(report), indent=2, allow_nan=False) + "\n")
    bad = [k for k, v in mask_receipts.items()
           if not all(g["all_checks_passed"] for g in v["gates"].values())]
    print(json.dumps({"variants": list(mask_receipts), "gate_failures": bad,
                      "report": str(out.relative_to(ROOT))}, indent=2))
    return 1 if bad else 0


def _clean(obj):
    """Recursively replace non-finite floats so the card is strict JSON."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (float, np.floating)):
        v = float(obj)
        return v if np.isfinite(v) else None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def _git_sha() -> str:
    try:
        import subprocess
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                       text=True).strip()
    except Exception:                                    # pragma: no cover
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
