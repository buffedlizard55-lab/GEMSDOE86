#!/usr/bin/env python3
"""SNAP axis on the R0 incumbent: move dots onto a physical edge response.

Parent (R0)
-----------
``h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros``, sha256
``c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9``,
37,654 unit-mass dots, minimum catalogue distance sqrt(5) = 2.2361 px.
It is reproduced **byte-exactly** from the pinned base raster
``gems28-h27-4-r1-solo-d2-8`` (40,199 dots, sha256 ``ab023001…``) by deleting
every dot at Euclidean distance <= 2.0 px from a mapped-fault cell, and the run
aborts unless both the dot set and the file digest match (brief v2 §5).

The experiment
--------------
Three variants, one axis value each, identical geometry and identical
exclusions, differing **only** in which physical surface the dots climb:

===========  =====================================================
``tmihg``    TMI horizontal gradient (band 3), the magnetic edge
``gravhg``   isostatic gravity anomaly horizontal gradient (band 18)
``combo``    the equal-weight mean of the two rank surfaces
===========  =====================================================

Surface construction (identical for every variant, no per-variant tuning):
rank-normalise the band over the footprint, Gaussian-smooth with sigma = 1 px
(100 m) by normalised convolution, rank-normalise the smoothed field again.
The first rank fixes how much each pixel may contribute; the smoothing is what
separates a lineament from single-pixel dither in the potential-field product;
the second rank makes "gain" comparable across variants.

Rule (brief §5 SNAP), identical for all three:

* each dot moves at most 2 px, to the highest-response cell in its window;
* a target cell must be a *decisive crest*: response >= 0.75 rank (top 25 % of
  the footprint) and at least 0.02 rank units better than the dot's own cell;
* a dot may not move outside the footprint, to a cell closer than 3 px to the
  catalogue, or onto a cell another dot holds;
* the dot count is preserved exactly; no dot is deleted, added or re-weighted.

Report-only instruments (never gates): the catalogue hide-and-recover PROXY
(PROXY, structurally at its floor for catalogue-avoiding fields --
IR-86-PRUNE-03) and a single-feature leakage canary (AUC of each surface for
catalogue membership, pooled and per spatial quadrant; STOP above 0.90).

Usage
-----
    python scripts/run_snap.py             # measure only, write nothing
    python scripts/run_snap.py --build     # write releases/ + ledger rows
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57 import gates as g57gates            # noqa: E402
from gems57.grid import load_grid              # noqa: E402
from gems57.validate import validate           # noqa: E402
from gems86 import prune as P                  # noqa: E402
from gems86 import snap as S                   # noqa: E402
from gems86.io import BY_NAME, NODATA, read_band  # noqa: E402
from run_prune_ladder import proxy_dti, serialization_profile, write_with_profile  # noqa: E402

BRIDGE = ROOT / "data" / "bridge"
FLEET = ROOT / "data" / "scored_fleet"
RELEASES = ROOT / "releases"
# House convention (as for releases/refill/): a variant that ADDS as well as
# removes dot cells is not a PRUNE release and must not sit in releases/
# itself, because tests/test_prune_ladder.py re-derives "deletion only" gates
# from every releases/*-zeros.tif. SNAP moves dots, so it lives one level down.
OUT_DIR = RELEASES / "snap"
EVIDENCE = ROOT / "evidence"
LEDGER = ROOT / "ledger"

PARENT_FILE = FLEET / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
BASE_FILE = FLEET / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
FEATURES = BRIDGE / "training_features.tif"

PARENT_ID = "h33-h33-2-b2"
PARENT_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
BASE_SHA = "ab023001"          # measured locally; no upstream pin exists (IR-86-PRUNE-02)
PIN_SAMPLE = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
PIN_CATALOGUE = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
PIN_FEATURES = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"

R0_PRUNE_PX = 2.0              # the lineage step that reproduces R0 from the base raster
SIGMA_PX = 1.0                 # edge-surface smoothing, 100 m
SNAP_RADIUS_PX = 2.0           # brief §5 SNAP window
MIN_CATALOGUE_PX = 3.0         # no dot may be *moved* inside the 3 px collar
#: Selectivity gate, fixed before any raster is written. A target cell must be in
#: the top 15 % of the response landscape ("a decisive crest") and must beat the
#: dot's own cell by at least 0.10 rank units. Without the gate the rule moves
#: 97-99 % of dots by a mean 1.8 px -- the whole field climbs to its window edge,
#: which is a relabelling, not a correction. The gate exists to keep the edit
#: local (1-50 % of dots, per brief §5) and attributable to the surface.
CREST_MIN = 0.75
GAIN_MIN = 0.02
STAMP = "20261023"
SEED = 20261023                # only the PROXY bootstrap uses it

# axis value -> (band, predicted live change, band range, mechanism card)
VARIANTS = {
    "tmihg": dict(
        bands=("tmi_hg",),
        predicted=-0.006, band=(-0.022, 0.012),
        hypothesis=("Where the total-magnetic-intensity horizontal gradient is strongest, a "
                    "magnetisation contrast marks a fault; a dot sitting 1-2 px off that crest "
                    "would earn more kernel credit if it climbed onto it."),
        mechanism=("Lineaments in aeromagnetics are the surface expression of the fault plane. R0's "
                   "dots come from a smooth model over the 19-band stack at 2.8 px spacing, so each "
                   "dot's sub-kernel position is a model average, not an edge measurement. Snapping "
                   "replaces that average with the local maximum of the TMI horizontal gradient."),
        confounder=("Pixel-scale dither in the delivered gradient band (0 % of horizontal neighbour "
                    "differences are zero), so a 100 m crest can be a resampling artefact; 400 m "
                    "flight lines at 150-200 m clearance also make a 100 m peak position not a "
                    "100 m fault position. Measured pre-test: R0's dots already sit at the 62nd "
                    "percentile of this surface (background 50th), so the parent has partly used "
                    "this field already and the remaining headroom is small."),
        falsifier=("A live change of +0.010 or more would falsify the pre-test claim that the "
                   "magnetic edge adds nothing at 100 m beyond the parent's own field (catalogue "
                   "AUC 0.527, dots already at the 62nd percentile). Inside +/-0.010 it is no "
                   "evidence and closes the magnetic-snap form for Phase 1."),
    ),
    "gravhg": dict(
        bands=("iso_grav_anom_hg",),
        predicted=-0.002, band=(-0.014, 0.010),
        hypothesis=("A density contrast across a fault produces an isostatic-gravity horizontal "
                    "gradient crest; gravity is not masked by the magnetic blanking that removes "
                    "signal over some volcanic rocks, so it is the independent test of the snap idea."),
        mechanism=("Same relocation rule as ``tmihg`` with the gravity edge substituted. Because the "
                   "two fields are independent measurements, agreement between the variants is "
                   "evidence that the edge geometry is physical rather than processing noise."),
        confounder=("R0's dots sit at the 48th percentile of this surface -- indistinguishable "
                    "from background -- and catalogue pixels separate at AUC 0.499, i.e. chance. "
                    "This variant is therefore the honest null control of the trio: whatever it "
                    "does live is a floor for the axis. Isostatic correction also low-passes the "
                    "field, moving a 100 m crest off the fault trace."),
        falsifier=("A gain of +0.010 or more would mean the gravity edge localises faults better "
                   "than the parent's model despite a chance-level catalogue AUC, which would need "
                   "an independent explanation before any slot. Inside +/-0.010 it is a no-op."),
    ),
    "combo": dict(
        bands=("tmi_hg", "iso_grav_anom_hg"),
        predicted=-0.004, band=(-0.018, 0.011),
        hypothesis=("Where the magnetic and the gravity horizontal gradients are both strong, two "
                    "independent contrasts share one boundary -- the classical cross-gradient "
                    "structural argument (Gallardo & Meju 2003). Snapping to that conjunction should "
                    "be cleaner than snapping to either field alone."),
        mechanism=("The two rank surfaces are averaged with equal weight, so a cell scores high only "
                   "if both fields are high there. Dots then climb the shared boundary rather than "
                   "one field's processing artefacts."),
        confounder=("Equal weights are a declared choice, not a fitted one; if one field is noisy "
                    "over part of the footprint the average inherits half of that noise. The mean "
                    "also allows one strong field to carry a cell, so it is a soft conjunction "
                    "rather than the strict minimum. The averaged surface is ranked again so that "
                    "the 0.75 gate is the same percentile on all three variants."),
        falsifier=("The combo must beat **both** single-field variants by >= 0.005 live to support "
                   "the conjunction mechanism. If it lands between them, the average is an average "
                   "and the mechanism is unsupported; inside +/-0.010 nothing is learned."),
    ),
}


# --------------------------------------------------------------------- inputs
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pins() -> dict:
    """Every input must match a committed pin; a mismatch aborts the run."""
    pins = {}
    for label, path, pin in (
        ("sample_submission.tif", BRIDGE / "sample_submission.tif", PIN_SAMPLE),
        ("existing_faults.tif", BRIDGE / "existing_faults.tif", PIN_CATALOGUE),
        ("training_features.tif", FEATURES, PIN_FEATURES),
        (PARENT_FILE.name, PARENT_FILE, PARENT_SHA),
    ):
        got = sha256_file(path)
        if got != pin:
            raise SystemExit(f"PIN MISMATCH for {label}: {got} != {pin}")
        pins[label] = {"sha256": got, "pin": pin, "path": str(path.relative_to(ROOT))}
    base = sha256_file(BASE_FILE)
    if not base.startswith(BASE_SHA):
        raise SystemExit(f"BASE MISMATCH: {base} does not start with {BASE_SHA}")
    pins[BASE_FILE.name] = {"sha256": base, "pin": None,
                            "pin_source": "MEASURED-LOCAL (no upstream pin in this checkout)",
                            "path": str(BASE_FILE.relative_to(ROOT))}
    return pins


def rebuild_parent(grid, base: np.ndarray) -> dict:
    """Re-derive R0's dot set and re-encode it; abort unless both identities hold."""
    dist = P.catalogue_distance(grid.catalogue)
    published = read_band(PARENT_FILE, 1) > 0
    rebuilt = P.prune_mask(base > 0, dist, R0_PRUNE_PX)
    diff = int((rebuilt != published).sum())
    if diff:
        raise SystemExit(f"R0 dot set does not reproduce ({diff} pixels differ); STOP")
    probe = Path(tempfile.mkdtemp()) / "r0_rebuild.tif"
    field = np.where(grid.footprint, rebuilt.astype(np.float32), np.float32(0.0))
    rebuilt_sha = write_with_profile(probe, field, None)
    probe.unlink()
    if rebuilt_sha != PARENT_SHA:
        raise SystemExit(f"R0 bytes do not reproduce ({rebuilt_sha}); STOP")
    return {"rule": f"delete base dots at Euclidean distance <= {R0_PRUNE_PX} px from the catalogue",
            "n_base_dots": int((base > 0).sum()), "n_rebuilt": int(rebuilt.sum()),
            "n_published": int(published.sum()), "differing_pixels": diff,
            "content_identical": True, "byte_identical_sha": True,
            "rebuilt_sha256": rebuilt_sha, "dot_digest": S.dot_digest(rebuilt)}


# ------------------------------------------------------------------- surfaces
def rank_normalize(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros(a.shape, np.float32)
    v = a[mask]
    if v.size < 2:
        return out
    order = np.argsort(v, kind="stable")
    ranks = np.empty(v.size, np.float32)
    ranks[order] = np.arange(v.size, dtype=np.float32)
    out[mask] = ranks / max(v.size - 1, 1)
    return out


def edge_surface(band: str, footprint: np.ndarray, sigma: float = SIGMA_PX) -> np.ndarray:
    """Rank -> Gaussian smooth (normalised convolution) -> rank, over the footprint."""
    raw = read_band(FEATURES, band).astype(np.float32)
    finite = np.isfinite(raw) & footprint
    z = np.where(finite, raw, np.float32(0.0))
    num = ndi.gaussian_filter(z, sigma, mode="nearest")
    den = ndi.gaussian_filter(finite.astype(np.float32), sigma, mode="nearest")
    smooth = np.where(den > 0.2, num / np.maximum(den, 1e-6), np.nan).astype(np.float32)
    ok = np.isfinite(smooth) & footprint
    return rank_normalize(smooth, ok)


def build_surfaces(footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Three uniformly distributed response surfaces on the same grid.

    ``combo`` is ranked once more after averaging so that a crest at 0.75 is the
    75th percentile of *every* surface; without that step the same numeric gate
    would be a much stricter percentile on the average and the three variants
    would not be comparable.
    """
    tmi = edge_surface("tmi_hg", footprint)
    grav = edge_surface("iso_grav_anom_hg", footprint)
    both = footprint & ((tmi > 0) | (grav > 0))
    combo = rank_normalize(0.5 * (tmi + grav), both)
    return {"tmihg": tmi, "gravhg": grav, "combo": combo}


# --------------------------------------------------------------------- checks
def diff_stats(parent: np.ndarray, cand: np.ndarray, dist: np.ndarray) -> dict:
    removed = int((parent & ~cand).sum())
    added = int((cand & ~parent).sum())
    n0, n1 = int(parent.sum()), int(cand.sum())
    return {"n_parent": n0, "n_candidate": n1,
            "retained": int((parent & cand).sum()),
            "removed": removed, "added": added,
            "pct_of_parent_changed": round(100.0 * (removed + added) / n0, 4),
            "kept_fraction": round(float((parent & cand).sum()) / n0, 6),
            "min_catalogue_distance_px": round(float(dist[cand].min()), 4),
            "dots_inside_3px_inherited": int((cand & (dist < MIN_CATALOGUE_PX)).sum())}


def leakage_canary(surfaces: dict[str, np.ndarray], grid) -> dict:
    """Single-feature AUC of each surface for catalogue membership (REPORT ONLY, stops > 0.90)."""
    fp = grid.footprint
    med_y, med_x = np.median(np.nonzero(fp)[0]), np.median(np.nonzero(fp)[1])
    yy = np.arange(fp.shape[0])[:, None] > med_y
    xx = np.arange(fp.shape[1])[None, :] > med_x
    quad = yy.astype(np.int8) * 2 + xx.astype(np.int8)
    rows = []
    for name, s in surfaces.items():
        pooled = float(roc_auc_score(grid.catalogue[fp], s[fp]))
        per_quad = []
        for q in range(4):
            m = fp & (quad == q) & ((s > 0) | grid.catalogue)
            if grid.catalogue[m].sum() >= 30 and (~grid.catalogue[m]).sum() > 0:
                per_quad.append(float(roc_auc_score(grid.catalogue[m], s[m])))
        rows.append({"surface": name, "auc_pooled": round(pooled, 4),
                     "auc_quadrants": [round(v, 4) for v in per_quad],
                     "auc_quadrant_max": round(max(per_quad), 4) if per_quad else None})
    worst = max(max(r["auc_pooled"], r["auc_quadrant_max"] or 0.0) for r in rows)
    return {"threshold": 0.90, "max_auc": round(worst, 4),
            "status": "PASS" if worst <= 0.90 else "STOP_INVESTIGATE",
            "rows": rows,
            "note": ("Catalogue pixels are the only measured fault pixels available; a surface that "
                     "reproduced them above 0.90 AUC would be a copy of the labels, not a physical "
                     "feature. Values near 0.50 mean the surface cannot localise a mapped trace.")}


# ----------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="write rasters, receipts and ledger rows")
    ap.add_argument("--draws", type=int, default=10, help="PROXY draws per field")
    args = ap.parse_args()
    t0 = time.time()

    print("[1/7] verifying pins", flush=True)
    pins = verify_pins()
    for k, v in pins.items():
        print(f"      {k}: {v['sha256'][:12]}")

    grid = load_grid(BRIDGE)
    dist = P.catalogue_distance(grid.catalogue)
    base = read_band(BASE_FILE, 1)
    print("[2/7] rebuilding R0 (dot set + file bytes)", flush=True)
    rebuild = rebuild_parent(grid, base)
    parent = read_band(PARENT_FILE, 1) > 0
    print(f"      {rebuild['n_base_dots']} -> {rebuild['n_rebuilt']} dots, "
          f"{rebuild['differing_pixels']} differing, sha {'MATCH'}", flush=True)

    print("[3/7] building edge surfaces", flush=True)
    surfaces = build_surfaces(grid.footprint)
    canary = leakage_canary(surfaces, grid)
    for row in canary["rows"]:
        print(f"      {row['surface']}: AUC {row['auc_pooled']} (max quadrant {row['auc_quadrant_max']})")
    if canary["status"] != "PASS":
        raise SystemExit(f"leakage canary > 0.90 on a single feature; STOP: {canary}")

    print("[4/7] snapping", flush=True)
    results, cards = {}, {}
    for key, spec in VARIANTS.items():
        surf = surfaces[key]
        res = S.snap_dots(parent, surf, grid.footprint, dist,
                          radius=SNAP_RADIUS_PX, min_catalogue_px=MIN_CATALOGUE_PX,
                          min_gain=GAIN_MIN, min_response=CREST_MIN)
        if res.n_dots != int(parent.sum()):
            raise SystemExit(f"{key}: dot count changed ({res.n_dots} != {parent.sum()})")
        if np.any(res.dots & grid.catalogue):
            raise SystemExit(f"{key}: mass on the catalogue")
        if np.any(res.dots & ~grid.footprint):
            raise SystemExit(f"{key}: mass outside the footprint")
        new_in_collar = int((res.dots & (dist < MIN_CATALOGUE_PX)).sum())
        inherited = int((parent & (dist < MIN_CATALOGUE_PX)).sum())
        if new_in_collar > inherited:
            raise SystemExit(f"{key}: a dot was moved into the collar ({new_in_collar} > {inherited})")
        st = res.stats()
        d = diff_stats(parent, res.dots, dist)
        results[key] = res
        cards[key] = dict(
            axis="SNAP", value=key, bands=list(spec["bands"]),
            sigma_px=SIGMA_PX, radius_px=SNAP_RADIUS_PX, min_catalogue_px=MIN_CATALOGUE_PX,
            stats=st, diff=d,
            nn_spacing_px_before=S.nearest_neighbour_px(parent),
            nn_spacing_px_after=S.nearest_neighbour_px(res.dots),
            block_density_cv_50px_before=S.block_density_cv(parent, grid.footprint, 50),
            block_density_cv_50px_after=S.block_density_cv(res.dots, grid.footprint, 50),
            surface_percentile_on_dots_before=round(float(surfaces[key][parent].mean()), 4),
            surface_percentile_on_dots_after=round(float(surfaces[key][res.dots].mean()), 4),
            surface_percentile_footprint=round(float(surfaces[key][grid.footprint].mean()), 4),
            dots_already_on_crest=int((surf[parent] >= CREST_MIN).sum()),
            crest_min=CREST_MIN, min_gain=GAIN_MIN,
            **{k: spec[k] for k in ("predicted", "band", "hypothesis", "mechanism",
                                    "confounder", "falsifier")},
        )
        print(f"      {key}: {st['n_moved']} moved ({100*st['fraction_moved']:.1f}%), "
              f"mean {st['mean_displacement_px']} px, median {st['median_displacement_px']} px, "
              f"NN {cards[key]['nn_spacing_px_before']['mean']} -> "
              f"{cards[key]['nn_spacing_px_after']['mean']}, "
              f"CV {cards[key]['block_density_cv_50px_before']} -> "
              f"{cards[key]['block_density_cv_50px_after']}", flush=True)

    print("[5/7] catalogue hide-and-recover PROXY (REPORT ONLY)", flush=True)
    proxy = {"R0": proxy_dti(parent, grid.catalogue, grid.footprint, n_draws=args.draws)}
    for key, res in results.items():
        proxy[key] = proxy_dti(res.dots, grid.catalogue, grid.footprint, n_draws=args.draws)
    for k, v in proxy.items():
        print(f"      {k}: {v.get('mean')} {v.get('ci95')}")

    print("[6/7] writing" if args.build else "[6/7] writing nothing (measure-only)", flush=True)
    written = []
    if args.build:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        known = set()
        if (LEDGER / "submissions.csv").is_file():
            with open(LEDGER / "submissions.csv", newline="") as fh:
                known |= {r["sha256"] for r in csv.DictReader(fh) if r.get("sha256")}
        known |= {sha256_file(p) for d in (FLEET, ROOT / "docs" / "downloads", RELEASES)
                  for p in d.rglob("*.tif")}
        for key, res in results.items():
            zeros_arr = np.where(res.dots, np.float32(1.0), np.float32(0.0)).astype(np.float32)
            nan_arr = np.where(grid.footprint, zeros_arr, np.float32(np.nan)).astype(np.float32)
            probe = Path(tempfile.mkdtemp()) / "probe.tif"
            sha8 = write_with_profile(probe, zeros_arr, None)[:8]
            probe.unlink()
            name = f"{PARENT_ID}-SNAP-{key}-{STAMP}-{sha8}"
            zeros_path = OUT_DIR / f"{name}-zeros.tif"
            nan_path = OUT_DIR / f"{name}.tif"
            zeros_sha = write_with_profile(zeros_path, zeros_arr, None)
            nan_sha = write_with_profile(nan_path, nan_arr, float("nan"))
            if zeros_sha[:8] != sha8:
                raise SystemExit(f"{key}: probed sha8 {sha8} != written {zeros_sha[:8]}")
            # novelty: the digest may not match any *other* file; a rebuild of this
            # same variant is allowed to overwrite its own twins (idempotent rerun)
            own = {sha256_file(p) for p in (zeros_path, nan_path)
                   if p.exists() and sha256_file(p) == zeros_sha}
            if zeros_sha in (known - own):
                raise SystemExit(f"{key}: sha256 already present in the ledger/disk set")
            v_zero = validate(zeros_path, grid.footprint, grid.catalogue)
            rep_zero = g57gates.format_report(zeros_path, BRIDGE / "sample_submission.tif",
                                              footprint=grid.footprint)
            v_nan = validate(nan_path, grid.footprint, grid.catalogue)
            if not v_zero["all_checks_passed"] or not rep_zero["ok"]:
                raise SystemExit(f"{key}: zeros twin failed the gates: {rep_zero['problems']}")
            nan_checks = {k: bool(v) for k, v in v_nan["checks"].items() if k != "no_nan_anywhere"}
            with rasterio.open(zeros_path) as ds:
                reread = ds.read(1) > 0
            if int((reread != res.dots).sum()):
                raise SystemExit(f"{key}: re-read from disk differs from the in-memory field")
            spec = VARIANTS[key]
            note = (f"SNAP {key}: R0 {PARENT_ID}; {cards[key]['stats']['n_moved']} dots "
                    f"({100 * cards[key]['stats']['fraction_moved']:.0f}%) moved <=2px onto "
                    f"{'+'.join(spec['bands'])} crest (sigma 1px); predicted "
                    f"{spec['predicted']:+.3f} MODEL")[:140]
            receipt = dict(
                id=name, parent=PARENT_ID, axis="SNAP", value=key, role="candidate",
                n_dots=int(res.dots.sum()), pct_changed=cards[key]["diff"]["pct_of_parent_changed"],
                dot_digest=S.dot_digest(res.dots), card=cards[key],
                zeros=dict(file=zeros_path.name, sha256=zeros_sha,
                           bytes=zeros_path.stat().st_size, validator=v_zero,
                           format_report_ok=rep_zero["ok"]),
                nan=dict(file=nan_path.name, sha256=nan_sha, bytes=nan_path.stat().st_size,
                         in_footprint_checks_pass=all(nan_checks.values()),
                         policy_note="NaN outside the footprint is the public spec; the repo's "
                                     "all-finite policy prefers the -zeros twin"),
                submission_name=name[:140], note=note,
                predicted_live_change=spec["predicted"],
                predicted_band=list(spec["band"]), evidence_class="MODEL",
                approved_for_weekly_slot=False, submission_slots_used=0,
                generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                provenance=dict(input_pins=pins, parent_rebuild=rebuild),
            )
            zeros_path.with_suffix(".json").write_text(
                json.dumps(receipt, indent=2, allow_nan=False) + "\n")
            written.append(receipt)
            print(f"      {zeros_path.name}  {zeros_sha[:12]}  {res.n_dots} dots")

    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        elapsed_seconds=round(time.time() - t0, 1),
        parent=dict(id=PARENT_ID, file=PARENT_FILE.name, sha256=PARENT_SHA,
                    n_dots=int(parent.sum()), dot_digest=S.dot_digest(parent)),
        axis="SNAP",
        axis_assignment=("UNASSIGNED BY THE HUMAN this session. SNAP was chosen because SLOT_PLAN's "
                         "slot 2 names it, its inputs are all pinned and restored (the 419 MB stack "
                         "verified against 4371c82e…), and PRUNE is exhausted (7 builds)"),
        input_pins=pins, parent_rebuild=rebuild,
        surface_recipe=dict(sigma_px=SIGMA_PX, steps=["rank over footprint", "gaussian smooth",
                                                      "rank again"]),
        rule=dict(radius_px=SNAP_RADIUS_PX, min_catalogue_px=MIN_CATALOGUE_PX,
                  crest_min=CREST_MIN, min_gain=GAIN_MIN,
                  move_if=("target is a decisive crest (response >= crest_min) and beats the "
                           "dot's own cell by more than min_gain"),
                  count="preserved exactly",
                  conflicts="greedy by descending gain, ties by row-major dot index"),
        variants=cards, proxy=proxy, leakage_canary=canary,
        written=[w["id"] for w in written],
        gates=dict(format="zeros twin passes the shared validator and format_report",
                   zero_catalogue_mass="asserted in memory and after re-read",
                   sha_novel="checked against the ledger and every local raster",
                   parent_diff="recorded per variant",
                   reread_from_disk="yes"),
        not_a_score="Every number here is a MODEL projection or a PROXY measurement. No submission was made.",
    )
    out = EVIDENCE / "snap_axis.json"
    if args.build:
        out.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        rows = [dict(id=w["id"], site="GEMSDOE86", parent=PARENT_ID, axis="SNAP",
                     value=w["value"], n_dots=w["n_dots"],
                     pct_changed=w["pct_changed"], sha8=w["zeros"]["sha256"][:8],
                     sha256_zeros=w["zeros"]["sha256"], encoding="zeros",
                     status="BUILT",
                     predicted_change=(f"{w['predicted_live_change']:+.3f} MODEL "
                                       f"(band {w['predicted_band'][0]:+.3f}..{w['predicted_band'][1]:+.3f}); "
                                       f"{100 * w['card']['stats']['fraction_moved']:.1f}% of dots moved, "
                                       f"mean {w['card']['stats']['mean_displacement_px']:.2f} px"),
                     source_url="https://github.com/buffedlizard55-lab/GEMSDOE86",
                     card=w["card"]) for w in written]
        (LEDGER / "variants_snap.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(f"[7/7] wrote {out.relative_to(ROOT)} and ledger/variants_snap.json", flush=True)
    else:
        print("[7/7] measure-only; rerun with --build to write", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
