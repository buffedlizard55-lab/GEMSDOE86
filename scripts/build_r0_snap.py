#!/usr/bin/env python3
"""Second SNAP build on R0 (gain-gated): the ``r2g10`` variant + replication arms.

A concurrent session (PR #31, ``scripts/run_snap_axis.py``) merged its own SNAP
build -- unconditional ``r1p000`` / ``r2p000`` / ``r2p000-grav`` -- while this
script was being written, so the (SNAP, 1) and (SNAP, 2) pairs already exist on
main. This builder therefore *releases only* the one pair PR #31 did not build,
the gain-gated ``r2g10``; its own ``r1``/``r2`` are still computed (they are the
arms of the SGMC dose-response in the evidence file, an independent replication
with an absolute-gravity edge) but are recorded WITHDRAWN with no raster
written (IR-86-SNAP-09). Pure geometry lives in ``src/gems86/snap_gated.py``
(main's ``src/gems86/snap.py`` belongs to PR #31's build).

Parent R0 = ``h33-h33-2-b2`` (GEMSDOE32), 37,654 unit-mass dots, live 0.2778
**CLAIM** (no receipt in ``ledger/``). This script, in order:

1. verifies the sha256 of every input against ``registry/data_manifest.json``;
2. rebuilds R0 from the pinned 40,199-dot solo-d2.8 base (delete dots within
   2.0 px of the catalogue) and asserts pixel-identity AND byte-identity
   (219,065 B, sha256 c55bafc4...) with the published parent -- if either
   fails it stops, per the brief (never approximate the parent);
3. builds the edge surface from the two preregistered provided gradient
   bands: footprint-percentile of ``tmi_hg`` (a magnitude) averaged with the
   footprint-percentile of ``|iso_grav_anom_hg|`` (signed band -> absolute);
4. builds three SNAP variants that differ from R0 only in dot *position*:
   ``r1`` (Euclidean radius 1.0, unconditional), ``r2`` (radius 2.0,
   unconditional) and ``r2g10`` (radius 2.0, move only when the realised
   edge-percentile gain is >= 0.10). Count is preserved exactly (37,654);
   destinations keep the parent's exclusion (footprint, off catalogue,
   catalogue distance > 2.0 px, valid edge). See ``src/gems86/snap_gated.py``
   for the deterministic collision rule and IR-86-SNAP-08 for why the parent's
   ">2 px" exclusion is kept instead of a variant-wide ">=3 px" (that would
   confound SNAP with the already-spent PRUNE axis);
5. writes the released variant (r2g10) twice (NaN outside footprint, zeros twin
   for the portal/all-finite validator), re-reads both from disk, runs the
   brief section-6 gates plus the vendored ``gems57.validate`` on the zeros
   twins, and records parent-diff statistics and mean displacement;
6. reports -- never gates on -- the catalogue hide-and-recover PROXY (6
   draws, 95% CI), an SGMC off-catalogue control when its pinned raster is
   restored, and single-band catalogue AUCs (leakage canary, report only).

No DrivenData endpoint is contacted. No label probing: every variant covers
the whole footprint with the parent's dot set, only locally relocated.

Usage
-----
    .venv/bin/python scripts/restore_data.py          # pinned feature stack
    .venv/bin/python scripts/build_r0_snap.py --build
    .venv/bin/python scripts/build_r0_snap.py --measure   # rebuild + revalidate
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))

from gems57.metric import dti_binary  # noqa: E402
from gems57.validate import validate as vendored_validate  # noqa: E402
from scripts import prune_collar as PC  # noqa: E402  (shared gates/proxy harness)
from scripts.run_prune_ladder import write_with_profile  # noqa: E402  (R0 byte-exact writer)
from src.gems86.prune import dot_digest  # noqa: E402
from src.gems86.snap_gated import percentile_ranks, snap_diff_stats, snap_dots  # noqa: E402

AXIS = "SNAP"
PARENT_SHORT = "h33-h33-2-b2"
DATE_TAG = "20261023"
SEED = 20261023

GRID = ROOT / "data" / "bridge"
FLEET = ROOT / "data" / "scored_fleet"
RELEASES = ROOT / "releases"
PARENT_FILE = FLEET / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
BASE_FILE = FLEET / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
FEATURES_FILE = GRID / "training_features.tif"
SGMC_FILE = ROOT / "data" / "external" / "derived_sgmc_faults_100m_u8.tif"

# Pins cross-checked against registry/data_manifest.json at run time.
PINS = {
    "sample_submission": (GRID / "sample_submission.tif",
                          "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
    "existing_faults": (GRID / "existing_faults.tif",
                        "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    "training_features": (FEATURES_FILE,
                          "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"),
    "parent_R0": (PARENT_FILE,
                  "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "base_solo_d28": (BASE_FILE,
                      "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"),
}
PIN_SGMC = "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"

EDGE_BANDS = (("tmi_hg", False), ("iso_grav_anom_hg", True))  # (band, take |.|)

# Predicted LIVE change vs R0, MODEL class only -- never a score. Set from the
# measured dose plus the report-only local controls in
# evidence/snap_gated_axis_20261023.json (SGMC control is negative with
# a clean dose-response: r2g10 -0.0021, r1 -0.0032, r2 -0.0089 SGMC-DTI; the
# floored hide-and-recover PROXY is ~flat). Controls informed the MODEL; they
# gated nothing.
VARIANTS = {
    "snapr1": dict(
        radius=1.0, min_gain=0.0,
        predicted=("-0.002 (MODEL, band -0.008..+0.003). One-pixel hill-climb: 96.9% of dots "
                   "step 1 px for a median edge-percentile gain of only 0.025, and 28.4% of "
                   "dots end with a neighbour closer than the parent's 2.8 px floor. Mostly "
                   "swapping near-equal cells; the SGMC control moves the same way (-0.0032)."),
        note="R0 h33-h33-2-b2 SNAP r1: dots <=1px to strongest tmi/grav edge, 37654 dots; pred -0.002 MODEL"),
    "snapr2": dict(
        radius=2.0, min_gain=0.0,
        predicted=("-0.006 (MODEL, band -0.018..+0.006). Strongest dose: 98.4% of dots move "
                   "(mean 1.77 px, median gain 0.042), 40.1% acquire a sub-2.8 px neighbour, "
                   "and the SGMC control is worst here (-0.0089). Unconditional window-argmax "
                   "mostly chases gradient noise and clusters onto crests, redundant under "
                   "the max-kernel. A dose-escalation instrument, not a slot candidate."),
        note="R0 h33-h33-2-b2 SNAP r2: dots <=2px to strongest tmi/grav edge, 37654 dots; pred -0.006 MODEL"),
    "snapr2g10": dict(
        radius=2.0, min_gain=0.10,
        predicted=("-0.001 (MODEL, band -0.007..+0.008). Only the 17.5% of dots whose window "
                   "holds a decisively stronger edge (>=0.10 percentile, median realised "
                   "gain 0.142) move, mean 1.95 px; 82.5% of the parent is untouched. This is "
                   "the only SNAP form worth a live test if the crest hypothesis must be "
                   "settled, but the SGMC control is still slightly negative (-0.0021), so "
                   "the centre is ~zero, not positive."),
        note="R0 h33-h33-2-b2 SNAP r2g10: dots <=2px to edge if gain>=0.10, 37654 dots; pred -0.001 MODEL"),
}

# (SNAP, value) pairs PR #31 already built on main (ledger ids snap-r1p000 /
# snap-r2p000). Computed here only as replication arms; no raster is written,
# so the duplicate can never be uploaded (cf. the withdrawn PRUNE rung,
# IR-86-PRUNE-08). IR-86-SNAP-09.
WITHDRAWN = {
    "snapr1": "duplicate (SNAP,1) pair: PR #31's SNAP-r1p000 (0e09c2b7) is on main; "
              "near-identical independent build (36,483 vs 36,494 dots moved)",
    "snapr2": "duplicate (SNAP,2) pair: PR #31's SNAP-r2p000 (e7473403) is on main; "
              "near-identical independent build (37,055 vs 37,066 dots moved)",
}
PREDICTED_NUMERIC = {"snapr1": -0.002, "snapr2": -0.006, "snapr2g10": -0.001}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_pins() -> dict:
    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    manifest_hashes = {f["sha256"] for f in manifest["files"]}
    out = {}
    for name, (path, pin) in PINS.items():
        in_manifest = pin in manifest_hashes
        # The solo-d2.8 base is pinned in scripts/build_r0_prune.py (PINS) and in
        # ledger/submissions.csv's historical row, but has no data_manifest entry;
        # every other input used here must be manifest-pinned (brief section 4.2).
        if not in_manifest and name != "base_solo_d28":
            raise SystemExit(f"pin for {name} is not in registry/data_manifest.json")
        got = PC.check_pin(path, pin, name)
        out[name] = {"path": str(path.relative_to(ROOT)), "sha256": got,
                     "bytes": path.stat().st_size, "verified": True,
                     "in_data_manifest": in_manifest,
                     "pin_source": ("registry/data_manifest.json" if in_manifest
                                    else "scripts/build_r0_prune.py PINS + ledger row"),
                     "organizer_authenticated": False}
    return out


def read_binary(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1)
    return footprint & np.isfinite(a) & (a > 0.5)


def rebuild_r0(g: PC.Grids) -> dict:
    """Brief section 5 start gate: rebuild R0, match dot set AND file bytes."""
    base = read_binary(BASE_FILE, g.footprint)
    rebuilt = base & (g.distance > 2.0)
    if not np.array_equal(rebuilt, g.parent):
        raise SystemExit("R0 dot set does not reproduce from the pinned base; STOP")
    scratch = ROOT / ".cache" / "r0-rebuilt-check.tif"
    scratch.parent.mkdir(exist_ok=True)
    arr = np.where(g.footprint, rebuilt, 0.0).astype(np.float32)
    digest = write_with_profile(scratch, arr, None)
    size = scratch.stat().st_size
    scratch.unlink(missing_ok=True)
    expected = PINS["parent_R0"][1]
    if digest != expected:
        raise SystemExit(f"R0 byte rebuild mismatch: {digest} != {expected}; STOP")
    return {"base_dots": int(base.sum()), "rebuilt_dots": int(rebuilt.sum()),
            "differing_px": 0, "rebuilt_bytes": size, "rebuilt_sha256": digest,
            "byte_identical_to_published_parent": True,
            "recipe": "pinned solo-d2.8 base, delete dots with d(catalogue) <= 2.0 px; "
                      "catalogue-profile deflate/predictor=3/zlevel=9/tiled-256 writer"}


def build_edge(g: PC.Grids) -> tuple[np.ndarray, np.ndarray, dict]:
    """Mean footprint-percentile of tmi_hg and |iso_grav_anom_hg| (label-free)."""
    edge = None
    valid = None
    detail = {}
    with rasterio.open(FEATURES_FILE) as src:
        if (src.height, src.width) != (PC.HEIGHT, PC.WIDTH) or str(src.crs) != "EPSG:32611":
            raise SystemExit("feature stack grid mismatch")
        names = [(src.descriptions[i] or "").split(" - ")[0] for i in range(src.count)]
        for band, take_abs in EDGE_BANDS:
            a = src.read(names.index(band) + 1).astype(np.float64)
            ok = g.footprint & np.isfinite(a) & (a > -1e30)
            mag = np.abs(a) if take_abs else a
            pct = percentile_ranks(mag, ok)
            detail[band] = {"valid_in_footprint": int(ok.sum()),
                            "parent_dots_invalid": int((g.parent & ~ok).sum()),
                            "parent_mean_percentile": round(float(np.nanmean(pct[g.parent])), 4)}
            if edge is None:
                edge, valid = pct.astype(np.float64), ok
            else:
                both = ok & valid
                edge = np.where(both, (edge + pct) / 2.0, np.nan)
                valid = both
            del a, pct, mag
    detail["combined_parent_mean_percentile"] = round(float(np.nanmean(edge[g.parent])), 4)
    detail["parent_dots_edge_valid"] = int((g.parent & valid).sum())
    return edge, valid, detail


def nn_stats(dots: np.ndarray) -> dict:
    pts = np.argwhere(dots)
    d, _ = cKDTree(pts).query(pts, k=2)
    nn = d[:, 1]
    return {"mean_px": round(float(nn.mean()), 4), "median_px": round(float(np.median(nn)), 4),
            "min_px": round(float(nn.min()), 4), "frac_lt_2p8px": round(float((nn < 2.8).mean()), 4)}


def canary_aucs(g: PC.Grids, edge: np.ndarray) -> dict:
    """REPORT ONLY: single-band AUC vs the (training) catalogue. >0.90 = stop."""
    rng = np.random.default_rng(SEED)
    pos = np.argwhere(g.catalogue)
    neg_pool = np.argwhere(g.footprint & ~g.catalogue)
    neg = neg_pool[rng.choice(len(neg_pool), min(300_000, len(neg_pool)), replace=False)]
    idx = np.vstack([pos, neg])
    y = np.array([1] * len(pos) + [0] * len(neg))
    rows = {}
    with rasterio.open(FEATURES_FILE) as src:
        names = [(src.descriptions[i] or "").split(" - ")[0] for i in range(src.count)]
        for band, take_abs in EDGE_BANDS:
            a = src.read(names.index(band) + 1)
            v = a[idx[:, 0], idx[:, 1]].astype(np.float64)
            ok = np.isfinite(v) & (v > -1e30)
            rows[band] = round(float(roc_auc_score(y[ok], np.abs(v[ok]) if take_abs else v[ok])), 4)
    v = edge[idx[:, 0], idx[:, 1]]
    ok = np.isfinite(v)
    rows["combined_edge"] = round(float(roc_auc_score(y[ok], v[ok])), 4)
    mx = max(rows.values())
    return {"evidence_class": "REPORT-ONLY (leakage canary)",
            "design": "all 60,988 catalogue px vs 300,000 seeded non-catalogue footprint px",
            "auc": rows, "threshold": 0.90,
            "status": "PASS" if mx <= 0.90 else "STOP_INVESTIGATE"}


def sgmc_control(g: PC.Grids, cands: dict[str, np.ndarray]) -> dict:
    """REPORT ONLY: exact DTI vs SGMC faults off-catalogue and >3 px from it."""
    if not SGMC_FILE.is_file():
        return {"evidence_class": "PROXY", "status": "SKIPPED_SGMC_NOT_RESTORED",
                "note": "restore the pinned SGMC raster (registry/data_manifest.json) to run"}
    got = sha256_file(SGMC_FILE)
    if got != PIN_SGMC:
        raise SystemExit(f"SGMC SHA-256 mismatch: {got} != {PIN_SGMC}")
    with rasterio.open(SGMC_FILE) as src:
        sgmc = src.read(1) > 0
    truth = sgmc & g.footprint & ~g.catalogue & (g.distance > 3.0)
    rows = {}
    for name, dots in cands.items():
        r = dti_binary(dots, truth, valid=g.footprint, known=g.catalogue)
        rows[name] = {k: r[k] for k in ("dti", "tp", "fp", "fn", "n_truth", "n_emitted")}
    return {"evidence_class": "PROXY", "status": "MEASURED", "sgmc_sha256": got,
            "truth": "derived SGMC faults, off-catalogue, Euclidean d(catalogue) > 3 px",
            "n_truth_px": int(truth.sum()), "candidates": rows,
            "delta_vs_R0": {k: rows[k]["dti"] - rows["R0"]["dti"] for k in rows if k != "R0"},
            "note": "independent-map control, not hidden competition truth; never a gate"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--draws", type=int, default=6)
    args = ap.parse_args()
    if not (args.build or args.measure):
        ap.error("choose --build or --measure")
    t0 = time.time()

    pins = verify_pins()
    g = PC.load_grids()
    r0_check = rebuild_r0(g)
    print(f"[1/6] pins verified vs manifest; R0 rebuilt byte-identical "
          f"({r0_check['rebuilt_bytes']:,} B, {r0_check['rebuilt_dots']:,} dots)")

    edge, valid, edge_detail = build_edge(g)
    eligible = g.footprint & ~g.catalogue & (g.distance > 2.0) & valid
    print(f"[2/6] edge surface built; parent mean combined percentile "
          f"{edge_detail['combined_parent_mean_percentile']:.3f} "
          f"({edge_detail['parent_dots_edge_valid']:,}/{int(g.parent.sum()):,} dots valid)")

    built: dict[str, tuple[np.ndarray, dict]] = {}
    for key, cfg in VARIANTS.items():
        dots, st = snap_dots(g.parent, edge, eligible, cfg["radius"], cfg["min_gain"])
        built[key] = (dots, st)
        print(f"[3/6] {key}: moved {st['n_moved']:,}/{st['n_dots']:,} dots, "
              f"mean disp {st['mean_displacement_px']:.3f} px "
              f"(moved {st['mean_displacement_moved_px']:.3f}), "
              f"mean gain {st['mean_realised_gain']:.4f}")

    canary = canary_aucs(g, edge)
    if canary["status"] != "PASS":
        raise SystemExit(f"leakage canary STOP: {canary}")
    print(f"[4/6] leakage canary (report only): {canary['auc']} -> PASS")

    dot_sets = {"R0": g.parent} | {k: v[0] for k, v in built.items()}
    rng = np.random.default_rng(SEED)
    draws = PC.holdout_draws(g.catalogue, rng, args.draws)
    proxy = PC.proxy_scores(dot_sets, draws, g.footprint)
    sgmc = sgmc_control(g, dot_sets)
    coverage = PC.coverage_control(dot_sets, g.catalogue, g.footprint)
    parent_nn = nn_stats(g.parent)
    print(f"[5/6] proxy (report only): R0 {proxy['candidates']['R0']['proxy_dti_mean']:.5f}; "
          + ", ".join(f"{k} {proxy['candidates'][k]['delta_vs_R0_mean']:+.5f}" for k in built)
          + f"; SGMC status {sgmc['status']}")

    RELEASES.mkdir(parents=True, exist_ok=True)
    ledger_existing = set()
    led = ROOT / "ledger" / "submissions.csv"
    if led.is_file():
        import csv as _csv
        ledger_existing = {r.get("sha256") for r in _csv.DictReader(led.open()) if r.get("sha256")}
    # A rerun must not flag this builder's own previous outputs as duplicates.
    own = ROOT / "ledger" / "variants_snap_gated.json"
    if own.is_file():
        for v in json.loads(own.read_text()):
            ledger_existing.discard(v.get("sha256"))
            ledger_existing.discard(v.get("sha256_zeros"))
    rows = []
    for key, cfg in VARIANTS.items():
        dots, st = built[key]
        diff = snap_diff_stats(g.parent, dots)
        displaced = st["displacement_px"]
        gains = st["realised_gain"]
        snap_stats_common = {
            "n_moved": st["n_moved"], "n_stayed": st["n_stayed"],
            "mean_displacement_px": round(st["mean_displacement_px"], 4),
            "mean_displacement_moved_px": round(st["mean_displacement_moved_px"], 4),
            "median_displacement_moved_px": round(float(np.median(displaced[displaced > 0])), 4)
            if (displaced > 0).any() else 0.0,
            "max_displacement_px": st["max_displacement_px"],
            "mean_realised_gain": round(st["mean_realised_gain"], 4),
            "mean_realised_gain_moved": round(st["mean_realised_gain_moved"], 4),
            "median_realised_gain_moved": round(float(np.median(gains[gains > 0])), 4)
            if (gains > 0).any() else 0.0,
            "n_origin_edge_invalid_stayed": st["n_origin_edge_invalid"],
            "mean_edge_parent": round(float(np.nanmean(edge[g.parent])), 4),
            "mean_edge_candidate": round(float(np.nanmean(edge[dots])), 4),
        }
        rel = proxy["candidates"][key]
        proxy_row = {"proxy_dti_mean": rel["proxy_dti_mean"],
                     "delta_vs_R0_mean": rel["delta_vs_R0_mean"],
                     "delta_vs_R0_ci95": rel["delta_vs_R0_ci95"],
                     "folds_improved": rel["folds_improved"], "draws": proxy["draws"],
                     "evidence_class": "PROXY"}
        if key in WITHDRAWN:
            rows.append({
                "id": f"{PARENT_SHORT}-{key}-{DATE_TAG}-withdrawn", "parent": PARENT_SHORT,
                "axis": "snap", "value": key.removeprefix("snap"), "status": "WITHDRAWN",
                "withdrawn_because": WITHDRAWN[key],
                "rule": (f"each dot to max mean-percentile(tmi_hg,|iso_grav_anom_hg|) within "
                         f"Euclidean {cfg['radius']} px, min realised gain {cfg['min_gain']}"),
                "n_dots": diff["n_candidate"],
                # ledger pct_changed = % of parent dots moved (PR #31's SNAP
                # convention, IR-86-SNAP-03); the cell-level figure is kept too.
                "pct_changed": diff["pct_dots_moved"],
                "pct_cells_changed": diff["pct_of_parent_changed"],
                "pct_dots_moved": diff["pct_dots_moved"],
                "sha256": "", "sha256_zeros": "", "sha8": "", "files": [],
                "dot_digest": dot_digest(dots), "diff": diff, "gate_all_pass": None,
                "snap_stats": snap_stats_common, "nearest_neighbour": nn_stats(dots),
                "proxy": proxy_row,
                "coverage_control_dti": coverage["candidates"][key]["dti"],
                "sgmc_delta_vs_R0": (sgmc.get("delta_vs_R0") or {}).get(key),
                "ring_table": PC.ring_table(g, dots),
                "predicted_change": cfg["predicted"],
                "receipt_score": "", "receipt_date": "",
            })
            print(f"[6/6] {key}: WITHDRAWN (duplicate pair, measurement kept) — "
                  f"{WITHDRAWN[key][:80]}...")
            continue
        base = f"{PARENT_SHORT}-{key}-{DATE_TAG}"
        scratch = RELEASES / f".{base}-zeros.tmp.tif"
        scratch.unlink(missing_ok=True)
        zeros_arr = np.where(g.footprint, dots, 0.0).astype(np.float32)
        zeros_digest = write_with_profile(scratch, zeros_arr, None)
        sha8 = zeros_digest[:8]
        final_zeros = RELEASES / f"{base}-{sha8}-zeros.tif"
        final_nan = RELEASES / f"{base}-{sha8}.tif"
        final_zeros.unlink(missing_ok=True)
        scratch.replace(final_zeros)
        nan_arr = np.where(g.footprint, dots, np.nan).astype(np.float32)
        nan_digest = write_with_profile(final_nan, nan_arr, np.nan)
        # re-read from disk (brief section 6) and gate
        v_nan = PC.validate(final_nan, g, "nan")
        v_zeros = PC.validate(final_zeros, g, "zeros")
        vendored = vendored_validate(final_zeros, g.footprint, g.catalogue)
        dup = PC.uniqueness_vs_disk(final_nan)
        gate = bool(v_nan["all_checks_passed"] and v_zeros["all_checks_passed"]
                    and vendored["all_checks_passed"] and not dup["duplicate"]
                    and nan_digest not in ledger_existing and zeros_digest not in ledger_existing
                    and v_nan["min_catalogue_distance_px"] > 2.0)
        if not gate:
            raise SystemExit(f"{key}: MUST gate failed "
                             f"(nan={v_nan['all_checks_passed']}, zeros={v_zeros['all_checks_passed']}, "
                             f"vendored={vendored['all_checks_passed']}, dup={dup['duplicate']})")
        rel = proxy["candidates"][key]
        row = {
            "id": final_nan.stem, "parent": PARENT_SHORT, "axis": "snap",
            "value": key.removeprefix("snap"),
            "rule": (f"each dot to max mean-percentile(tmi_hg,|iso_grav_anom_hg|) within "
                     f"Euclidean {cfg['radius']} px, min realised gain {cfg['min_gain']}; "
                     f"destinations: footprint, off-catalogue, d(catalogue)>2 px, valid edge"),
            "n_dots": diff["n_candidate"], "pct_changed": diff["pct_dots_moved"],
            "pct_cells_changed": diff["pct_of_parent_changed"],
            "pct_dots_moved": diff["pct_dots_moved"],
            "sha256": nan_digest, "sha256_zeros": zeros_digest, "sha8": sha8,
            "files": [str(final_nan.relative_to(ROOT)), str(final_zeros.relative_to(ROOT))],
            "status": "BUILT-DUPLICATE", "diff": diff,  # axis already spent on main (PR #31/#34)
            "validation_nan": v_nan, "validation_zeros": v_zeros,
            "vendored_validate_zeros_pass": bool(vendored["all_checks_passed"]),
            "gate_all_pass": gate, "exact_hash_duplicate": dup,
            "snap_stats": snap_stats_common,
            "nearest_neighbour": nn_stats(dots),
            "proxy": proxy_row,
            "coverage_control_dti": coverage["candidates"][key]["dti"],
            "sgmc_delta_vs_R0": (sgmc.get("delta_vs_R0") or {}).get(key),
            "ring_table": PC.ring_table(g, dots),
            "predicted_change": cfg["predicted"],
            "form_note_140": cfg["note"][:140], "form_note_chars": len(cfg["note"][:140]),
            "receipt_score": "", "receipt_date": "",
        }
        receipt = {
            # axis/pct_changed/movement/predicted fields follow PR #31's SNAP
            # receipt contract (tests/test_prune_ladder.py per-axis branch).
            "id": final_nan.stem, "parent": PARENT_FILE.stem, "axis": "SNAP",
            "value": row["value"], "role": "candidate", "n_dots": diff["n_candidate"],
            "radius_px": cfg["radius"],
            "movement": {"pct_snapped": diff["pct_dots_moved"],
                         "max_displacement_px": st["max_displacement_px"]},
            "model": {"evidence_class": "MODEL"},
            "pct_changed": diff["pct_dots_moved"],
            "pct_cells_changed": diff["pct_of_parent_changed"],
            "pct_dots_moved": diff["pct_dots_moved"],
            "dot_digest": dot_digest(dots),
            "zeros": {"file": final_zeros.name, "sha256": zeros_digest,
                      "bytes": final_zeros.stat().st_size,
                      "validator": {k: v_zeros[k] for k in
                                    ("checks", "all_checks_passed", "on_catalogue_dots",
                                     "min_catalogue_distance_px")},
                      "vendored_gems57_validate_all_passed": bool(vendored["all_checks_passed"])},
            "nan": {"file": final_nan.name, "sha256": nan_digest,
                    "bytes": final_nan.stat().st_size,
                    "validator": {k: v_nan[k] for k in
                                  ("checks", "all_checks_passed", "on_catalogue_dots",
                                   "min_catalogue_distance_px")}},
            "submission_name": final_nan.stem, "note": row["form_note_140"],
            "predicted_live_change": PREDICTED_NUMERIC[key],
            "predicted_change_text": cfg["predicted"], "evidence_class": "MODEL",
            "approved_for_weekly_slot": False, "submission_slots_used": 0,
            "mean_displacement_px": row["snap_stats"]["mean_displacement_px"],
            "diff": diff, "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        final_zeros.with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n")
        rows.append(row)
        print(f"[6/6] {row['id']}: gates PASS, moved {diff['pct_dots_moved']:.2f}% of dots, "
              f"zeros sha {zeros_digest[:12]}..., nan sha {nan_digest[:12]}...")

    evidence = {
        "schema": "gems86.snap-gated-axis.v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 1),
        "axis": AXIS, "axis_assignment": "human left AXIS blank and skipped the assignment "
        "prompt; SNAP taken from SLOT_PLAN.md's preregistered slot-2 axis (PRUNE spent, "
        "MASS blocked by IR-86-PRUNE-02); a concurrent session (PR #31) built the same "
        "axis and merged first, so snapr1/snapr2 are WITHDRAWN duplicates here and only "
        "the novel gain-gated snapr2g10 is released (IR-86-SNAP-09)",
        "concurrent_build_on_main": "PR #31 scripts/run_snap_axis.py (SNAP r1p000/r2p000/r2p000-grav)",
        "parent": {"id": PARENT_SHORT, "file": str(PARENT_FILE.relative_to(ROOT)),
                   "sha256": PINS["parent_R0"][1], "n_dots": int(g.parent.sum()),
                   "live_score_0p2778": "CLAIM (no receipt in ledger/)",
                   "rebuild": r0_check, "dot_digest": dot_digest(g.parent),
                   "nearest_neighbour": parent_nn},
        "inputs_verified": pins, "seed": SEED,
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           text=True).strip(),
        "edge": {"bands": ["tmi_hg (magnitude)", "|iso_grav_anom_hg| (signed band)"],
                 "combination": "mean of footprint percentiles",
                 "detail": edge_detail, "leakage_canary_report_only": canary},
        "destination_rule": "footprint & off-catalogue & d(catalogue)>2.0 px (parent's own "
                            "exclusion; see IR-86-SNAP-08) & valid edge; gain-ordered greedy "
                            "with origin reservation (src/gems86/snap_gated.py)",
        "proxy": proxy,
        "proxy_verdict": "REPORT ONLY, structurally floored for a catalogue-avoiding parent "
                         "exactly as in IR-86-PRUNE-03: candidates (and R0) keep every dot "
                         ">2 px from the *full* catalogue, so withheld catalogue pixels earn "
                         "almost no credit. Never a gate. The MODEL prediction centres were "
                         "set from dose + the SGMC control's dose-response, not from this "
                         "floored instrument.",
        "sgmc_control": sgmc, "coverage_control": coverage, "variants": rows,
    }
    out = ROOT / "evidence" / "snap_gated_axis_20261023.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    (ROOT / "ledger" / "variants_snap_gated.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)} and ledger/variants_snap_gated.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
