#!/usr/bin/env python3
"""TRACKB axis on R0 (GEMSDOE32 h33-h33-2-b2): strike-consistent traces + a
count-fixed trace-consistent variant, exported as GeoJSON and as a raster.

Axis choice (this session's own, brief v2 §1: the analyst picks the axis)
-------------------------------------------------------------------------
TRACKB is the one AXIS in brief v2 §5 that nothing in this repository had built,
and it is the only axis whose case is *not* a local metric perturbation: Phase 2
of the prize rescores submissions against labels that experts expand **after
reviewing the submitted faults** (problem page, quoted in PROMPT.md). A field of
geologically legible, strike-continuous strands is therefore the one edit whose
plausible upside lives outside the Phase-1 DTI proxy. That is the argument this
session tests, and the reason it is worth building even though every other axis
has come back inside +/-0.01.

What this script does, in order
------------------------------
1. verifies the sha256 of every input against a committed pin before reading it;
2. re-derives R0 from the pinned d2.8 parent field and the catalogue and asserts
   byte-for-byte equality with the published file (brief §5 parent gate);
3. runs the TRACKB detector (`src/gems86/trackb.py`) on R0 at three corridor
   widths -- the one parameter that varies across the three variants -- and
   records the trace set, per-dot trace support, and a uniform-point NULL field
   of the same count on the same footprint (the falsifier: if R0's trace
   statistics are no better than the null, there is nothing to export);
4. builds one count-fixed variant per corridor: the least trace-supported dots
   are donated and the same number are emitted as along-strike continuations of
   the strongest traces (every new cell off-catalogue, > 3 px from it, and >= the
   parent's own 2.828 px dot separation from every parent dot);
5. measures a displacement-matched random-azimuth relocation control (same
   donors, same step lengths, random directions) -- measured, never written;
6. scores the report-only instruments: the USGS SGMC off-catalogue surrogate
   (MODEL, with a four-quadrant sign replication) and the catalogue
   hide-and-recover PROXY, plus a single-feature leakage canary panel;
7. applies every hard gate to the written bytes, re-reads both twins from disk,
   writes the GeoJSON trace set and one evidence paragraph per trace, and appends
   the ledger rows through the repository's single generator.

No truth raster is read. No network call, no portal, no submission, no login.

Usage
-----
    .venv/bin/python scripts/run_trackb_axis.py [--no-write] [--stamp 20261023]
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

from gems57 import grid as g57grid                            # noqa: E402
from gems57 import metric as g57metric                        # noqa: E402
from gems57.gates import format_report                        # noqa: E402
from gems57.validate import validate                          # noqa: E402
from run_prune_ladder import (BRIDGE, PARENT_FILE, PARENT_SHA,  # noqa: E402
                              proxy_dti, read, rebuild_parent, sha256,
                              write_with_profile)
from src.gems86 import prune as PRUNE                          # noqa: E402
from src.gems86 import trackb as TB                            # noqa: E402

AXIS = "TRACKB"
SESSION_DATE = "20261023"
SEED = 20261023
PARENT_ID = "h33-h33-2-b2-20261004-e5eb6e7e"
N_DOTS_R0 = 37654
BASE_FILE = ROOT / "data/scored_fleet" / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
BASE_SHA = "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"
MANIFEST = ROOT / "registry" / "data_manifest.json"
DATA_ROOT = ROOT / ".cache" / "gems_data"
SGMC_ID = "ext_derived_sgmc_faults_100m_u8"
MIN_PCT_CHANGED, MAX_PCT_CHANGED = 1.0, 50.0

#: The axis value that varies across the three variants: the across-strike
#: corridor width of the detector, in pixels. Everything else (minimum trace
#: length 1.0 km, dot count, catalogue rules, spacing floor) is held fixed.
VARIANTS = {
    "c10len1km": dict(corridor_px=1.0,
                      hypothesis=("Only strictly collinear dots are traces. Fewest, "
                                  "cleanest strands; smallest relocation budget.")),
    "c15len1km": dict(corridor_px=1.5,
                      hypothesis=("A trace may wander +/-0.75 px across strike, which is "
                                  "the flight-line positional uncertainty of the parent "
                                  "survey. The planned default.")),
    "c25len1km": dict(corridor_px=2.5,
                      hypothesis=("A loose corridor captures relays and gentle arcs but "
                                  "also captures crossing strands; the largest relocation "
                                  "budget and the largest chance-alignment risk.")),
}
MIN_TRACE_LEN_PX = 10.0          # 1 km at the 100 m grid, per brief §5
DOSE_FRAC = 0.10                 # requested donation budget (capacity usually binds)
NOTE_NAN_POLICY_CHECKS = {"no_nan_anywhere", "outside_footprint_zero"}


def pin_table() -> dict:
    """Verify every input that is read here against a committed pin."""
    manifest = {f["id"]: f for f in json.loads(MANIFEST.read_text())["files"]}
    receipt = {Path(f["dest"]).name: f["sha256"]
               for f in json.loads((ROOT / "data" / "restore_receipt.json").read_text())["files"]}
    checks = {}
    for key, path, pin_source, pin in (
        ("existing_faults.tif", BRIDGE / "existing_faults.tif", "registry/data_manifest.json",
         manifest["existing_faults"]["sha256"]),
        ("sample_submission.tif", BRIDGE / "sample_submission.tif", "registry/data_manifest.json",
         manifest["sample_submission"]["sha256"]),
        (PARENT_FILE.name, PARENT_FILE, "data/restore_receipt.json", receipt[PARENT_FILE.name]),
        (BASE_FILE.name, BASE_FILE, "HISTORICAL constant (measured, see IRREGULARITIES.md)", BASE_SHA),
    ):
        if not path.is_file():
            raise SystemExit(f"pinned input absent: {path}")
        got = sha256(path)
        if got != pin:
            raise SystemExit(f"PIN MISMATCH {key}: {got} != {pin} ({pin_source})")
        checks[key] = dict(path=str(path.relative_to(ROOT)), sha256=got, pin_source=pin_source)
    entry = manifest[SGMC_ID]
    sgmc_path = DATA_ROOT / entry["dest"]
    if not sgmc_path.is_file() or sha256(sgmc_path) != entry["sha256"]:
        raise SystemExit(f"pinned SGMC surrogate absent or changed: {sgmc_path} "
                         "(run scripts/restore_axis_inputs.py --ids ext_derived_sgmc_faults_100m_u8)")
    checks[SGMC_ID] = dict(path=str(sgmc_path), sha256=entry["sha256"],
                           pin_source="registry/data_manifest.json")
    return checks


def uniform_null(dots: np.ndarray, footprint: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Same dot count, uniform over the footprint: the trace detector's null."""
    flat = np.flatnonzero(np.asarray(footprint).ravel())
    take = rng.choice(flat, size=int(np.count_nonzero(dots)), replace=False)
    out = np.zeros(dots.shape, bool)
    out.ravel()[take] = True
    return out


def displacement_matched_control(donors: np.ndarray, add: np.ndarray, parent: np.ndarray,
                                 footprint: np.ndarray, distance_to_catalogue: np.ndarray,
                                 rng: np.random.Generator,
                                 clearance_px: float = TB.CLEARANCE_PX) -> tuple[np.ndarray, dict]:
    """Move each donor the same distance as the trace edit, but in a random direction.

    This is the control the SPACING session showed is essential: the *act* of
    moving is separate from the *law* used to choose where to move.
    """
    src = np.argwhere(donors)
    dst = np.argwhere(add)
    if src.shape[0] != dst.shape[0]:
        raise ValueError("control needs one destination per donor")
    order = np.argsort(src[:, 0] * 10 ** 6 + src[:, 1])
    src, dst = src[order], dst[order]
    delta = dst - src
    radius = np.hypot(delta[:, 0], delta[:, 1])
    occupied = (parent & ~donors).copy()
    out = np.zeros(parent.shape, bool)
    height, width = parent.shape
    offs = TB.OCCUPIED_OFFSETS
    placed = 0
    angles = rng.uniform(0.0, 2.0 * np.pi, size=radius.size)
    for i in range(radius.size):
        r = float(radius[i])
        for attempt in range(12):
            a = angles[i] + (np.pi / 6.0) * attempt
            rr = int(round(src[i, 0] + r * np.sin(a)))
            cc = int(round(src[i, 1] + r * np.cos(a)))
            if not (0 <= rr < height and 0 <= cc < width):
                continue
            if not footprint[rr, cc] or distance_to_catalogue[rr, cc] <= clearance_px:
                continue
            if occupied[rr, cc]:
                continue
            if any(0 <= rr + o[0] < height and 0 <= cc + o[1] < width
                   and occupied[rr + o[0], cc + o[1]] for o in offs):
                continue
            out[rr, cc] = True
            occupied[rr, cc] = True
            placed += 1
            break
    stats = dict(requested=int(radius.size), placed=placed,
                 shortfall=int(radius.size) - placed,
                 radius_px=dict(min=round(float(radius.min()), 3),
                                median=round(float(np.median(radius)), 3),
                                max=round(float(radius.max()), 3)),
                 rule="same step length as the trace edit, random azimuth, same catalogue and spacing rules")
    return out, stats


def nearest_neighbour(mask: np.ndarray) -> dict:
    pts = np.argwhere(mask)
    d = cKDTree(pts).query(pts, k=2)[0][:, 1]
    return dict(mean_px=round(float(d.mean()), 3), median_px=round(float(np.median(d)), 3),
                min_px=round(float(d.min()), 3),
                fraction_below_2_8px=round(float((d < 2.8).mean()), 4))


def quadrant_masks(footprint: np.ndarray, n: int = 2) -> list[np.ndarray]:
    h, w = footprint.shape
    out = []
    for iy in range(n):
        for ix in range(n):
            m = np.zeros(footprint.shape, bool)
            m[iy * h // n:(iy + 1) * h // n, ix * w // n:(ix + 1) * w // n] = True
            out.append(footprint & m)
    return out


def surrogate_delta(parent: np.ndarray, child: np.ndarray, truth: np.ndarray,
                    footprint: np.ndarray, catalogue: np.ndarray,
                    quadrants: list[np.ndarray]) -> dict:
    regions = {"all": footprint}
    regions.update({f"q{i}": q for i, q in enumerate(quadrants, start=1)})
    out = {}
    for name, valid in regions.items():
        a = g57metric.dti_binary(parent, truth, valid=valid, known=catalogue)
        b = g57metric.dti_binary(child, truth, valid=valid, known=catalogue)
        out[name] = dict(dti_parent=round(a["dti"], 6), dti_child=round(b["dti"], 6),
                         delta=round(b["dti"] - a["dti"], 6),
                         n_truth=int(a["n_truth"]), coverage_parent=round(a["coverage"], 6),
                         coverage_child=round(b["coverage"], 6))
    deltas = [out[k]["delta"] for k in out if k != "all"]
    out["sign_replication"] = dict(
        n_quadrants=len(deltas), n_positive=int(sum(d > 0 for d in deltas)),
        quadrant_range=[round(min(deltas), 6), round(max(deltas), 6)])
    return out


def canary_panel(parent: np.ndarray, footprint: np.ndarray, catalogue: np.ndarray,
                 surrogate: np.ndarray, support: np.ndarray, distance_to_catalogue: np.ndarray,
                 *, n: int = 400_000, seed: int = SEED) -> dict:
    """Single-feature AUCs on a random cell sample; AUC > 0.90 => stop."""
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(seed)
    flat = np.flatnonzero(footprint.ravel())
    take = rng.choice(flat, size=min(n, flat.size), replace=False)
    density = ndi.uniform_filter(parent.astype(np.float32), size=9, mode="constant")
    feats = {"trace_support_px": support, "dot_density_9px": density,
             "catalogue_distance_px": distance_to_catalogue}
    out = {}
    for target_name, target in (("catalogue", catalogue), ("sgmc_extra", surrogate)):
        y = np.asarray(target).ravel()[take].astype(int)
        per = {}
        for name, arr in feats.items():
            x = np.asarray(arr).ravel()[take]
            if np.unique(x).size < 2:
                per[name] = None
                continue
            per[name] = round(float(roc_auc_score(y, x)), 4)
        out[target_name] = dict(n_sampled_cells=int(take.size), n_positive=int(y.sum()),
                                auc_per_feature=per, threshold=0.90,
                                max_auc=max(v for v in per.values() if v is not None))
    out["note"] = ("catalogue_distance_px is a label-derived feature by construction and is "
                   "reported only against the independent SGMC target, as the RELIEF session did.")
    return out


def trace_record(trace: dict, catalogue_distance: np.ndarray, width: int) -> dict:
    rows = trace["dot_flat"] // width
    cols = trace["dot_flat"] % width
    d = catalogue_distance[rows, cols]
    return dict(rank=int(trace["rank"]), length_km=round(trace["length_px"] / 10.0, 2),
                strike_azimuth_deg=round(TB.strike_azimuth(trace["theta_deg"]), 1),
                n_dots=int(trace["n_dots"]), n_new_dots=int(trace["n_new_dots"]),
                corridor_px=None,
                min_catalogue_distance_px=round(float(d.min()), 3),
                median_catalogue_distance_px=round(float(np.median(d)), 3),
                dot_density_per_km=round(float(trace["n_dots"]) / max(trace["length_px"] / 10.0, 0.1), 3),
                start_px=[int(rows[np.argmin(trace["t"])]), int(cols[np.argmin(trace["t"])])],
                end_px=[int(rows[np.argmax(trace["t"])]), int(cols[np.argmax(trace["t"])])])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="releases")
    ap.add_argument("--geo-dir", default="releases/trackb")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--stamp", default=time.strftime("%Y%m%d"))
    args = ap.parse_args()
    t0 = time.time()

    print("[1/9] pins", flush=True)
    pins = pin_table()

    print("[2/9] parent gate", flush=True)
    g = g57grid.load_grid(BRIDGE)
    foot, cat = np.asarray(g.footprint, bool), np.asarray(g.catalogue, bool)
    base = read(BASE_FILE)
    rebuild = rebuild_parent(g, base)
    if not (rebuild["content_identical"] and rebuild["byte_identical_sha"]):
        raise SystemExit(f"parent gate FAILED: {rebuild}")
    parent = read(PARENT_FILE) > 0
    if int(parent.sum()) != N_DOTS_R0 or sha256(PARENT_FILE) != PARENT_SHA:
        raise SystemExit("the parent on disk is not the parent this session must rebuild from")
    d_cat = PRUNE.catalogue_distance(cat)
    print(f"      R0 {int(parent.sum())} dots; rebuilt sha256 == published ({rebuild['rebuilt_sha256'][:8]})",
          flush=True)

    print("[3/9] SGMC off-catalogue surrogate", flush=True)
    with rasterio.open(DATA_ROOT / "external" / "derived_sgmc_faults_100m_u8.tif") as src:
        sg = src.read(1)
    sgmc = np.isfinite(sg) & (sg > 0)
    surrogate = sgmc & ~cat
    print(f"      SGMC {int(sgmc.sum())} px, off-catalogue {int(surrogate.sum())} px", flush=True)

    print("[4/9] trace detection at three corridors + uniform null", flush=True)
    rng = np.random.default_rng(SEED)
    null_dots = uniform_null(parent, foot, rng)
    detector = {}
    for key, spec in VARIANTS.items():
        corridor = spec["corridor_px"]
        runs = TB.trace_runs(parent, corridor_px=corridor)
        traces = TB.trace_table(parent, runs, MIN_TRACE_LEN_PX)
        support = TB.dot_support(parent, runs)
        null_runs = TB.trace_runs(null_dots, corridor_px=corridor)
        null_traces = TB.trace_table(null_dots, null_runs, MIN_TRACE_LEN_PX)
        null_support = TB.dot_support(null_dots, null_runs)
        lengths = np.array([t["length_px"] for t in traces], float)
        null_lengths = np.array([t["length_px"] for t in null_traces], float)
        detector[key] = dict(
            corridor_px=corridor,
            r0=dict(runs_total=len(runs), traces=len(traces),
                    dots_on_traces=int(sum(t["n_dots"] for t in traces)),
                    dot_share_on_traces=round(float(sum(t["n_dots"] for t in traces)) / N_DOTS_R0, 4),
                    dots_with_any_run=int((support[parent] > 0).sum()),
                    length=TB.trace_length_summary(lengths)),
            null=dict(traces=len(null_traces),
                      dots_on_traces=int(sum(t["n_dots"] for t in null_traces)),
                      dots_with_any_run=int((null_support[null_dots] > 0).sum()),
                      length=TB.trace_length_summary(null_lengths)),
            support_percentiles={p: round(float(np.percentile(support[parent], p)), 2)
                                 for p in (50, 75, 90, 95, 99)},
        )
        spec["runs"] = runs
        spec["traces"] = traces
        spec["support"] = support
        print(f"      {key}: {len(traces)} traces >=1 km, "
              f"{int(sum(t['n_dots'] for t in traces))} dots on them; null {len(null_traces)} traces",
              flush=True)

    print("[5/9] count-fixed variants", flush=True)
    built: dict[str, dict] = {}
    for key, spec in VARIANTS.items():
        target = int(DOSE_FRAC * N_DOTS_R0)
        add, placement = TB.plan_extension(parent, spec["traces"], foot, d_cat, target)
        k = int(add.sum())
        if k == 0:
            raise SystemExit(f"{key}: no eligible along-strike continuation exists")
        donors = TB.select_donors(parent, spec["support"], k)
        dots = TB.apply_swap(parent, donors, add)
        diff = TB.diff_stats(parent, dots)
        if not diff["count_fixed"]:
            raise SystemExit(f"{key}: count not fixed")
        if not (MIN_PCT_CHANGED <= diff["pct_changed"] <= MAX_PCT_CHANGED):
            raise SystemExit(f"{key}: {diff['pct_changed']}% changed violates the 1-50% contract")
        if np.any(dots & cat):
            raise SystemExit(f"{key}: positive mass on the catalogue")
        if float(d_cat[add].min()) <= TB.CLEARANCE_PX:
            raise SystemExit(f"{key}: new mass inside the 3 px catalogue collar")
        if np.any(donors & spec["support"].astype(bool) & (spec["support"] > MIN_TRACE_LEN_PX)):
            raise SystemExit(f"{key}: a donor came from a >=1 km trace")
        diff["nearest_neighbour"] = nearest_neighbour(dots)
        diff["min_catalogue_distance_px"] = round(float(d_cat[dots].min()), 3)
        built[key] = dict(spec=spec, dots=dots, donors=donors, add=add, placement=placement,
                          diff=diff, broken=TB.broken_traces(spec["traces"], dots))
        print(f"      {key}: {k} dots relocated ({diff['pct_changed']}% of the field, "
              f"capacity-limited from {target}); NN {diff['nearest_neighbour']['mean_px']} px",
              flush=True)

    print("[6/9] displacement-matched control (measured, never written)", flush=True)
    key0 = "c15len1km"
    ctl_add, ctl_stats = displacement_matched_control(built[key0]["donors"], built[key0]["add"],
                                                      parent, foot, d_cat,
                                                      np.random.default_rng(SEED + 1))
    ctl_dots = (parent & ~built[key0]["donors"]) | ctl_add

    print("[7/9] report-only instruments", flush=True)
    quads = quadrant_masks(foot, 2)
    preds = {k: v["dots"] for k, v in built.items()}
    preds["CONTROL-randomaz"] = ctl_dots
    model = {k: surrogate_delta(parent, p, surrogate, foot, cat, quads) for k, p in preds.items()}
    proxy = {"R0": proxy_dti(parent.astype(np.float32), cat, foot)}
    proxy.update({k: proxy_dti(v["dots"].astype(np.float32), cat, foot) for k, v in built.items()})
    proxy["CONTROL-randomaz"] = proxy_dti(ctl_dots.astype(np.float32), cat, foot)
    canaries = canary_panel(parent, foot, cat, surrogate, built[key0]["spec"]["support"], d_cat)
    worst = max(canaries[t]["max_auc"] for t in ("catalogue", "sgmc_extra"))
    if worst > 0.90:
        raise SystemExit(f"leakage canary: a single feature reaches AUC {worst} -- STOP and investigate")
    print("      surrogate delta: " + json.dumps({k: v["all"]["delta"] for k, v in model.items()}),
          flush=True)

    print("[8/9] gates and release artifacts", flush=True)
    out_dir, geo_dir = ROOT / args.out_dir, ROOT / args.geo_dir
    existing: set[str] = set()
    if (ROOT / "ledger/submissions.csv").exists():
        with open(ROOT / "ledger/submissions.csv", newline="") as fh:
            existing |= {r["sha256"] for r in csv.DictReader(fh) if r.get("sha256")}
    existing |= {sha256(p) for p in (ROOT / "data/scored_fleet").glob("*.tif")}
    existing |= {sha256(p) for p in (ROOT / "docs/downloads").glob("*.tif")}
    # Idempotent re-run: an artifact whose id and bytes are already in the ledger is
    # this same build, not a collision. Re-validating it is the useful action; writing
    # it again would trip the exact-hash dedupe (which exists to catch duplicates).
    ledger_ids: dict[str, str] = {}
    if (ROOT / "ledger/submissions.csv").exists():
        with open(ROOT / "ledger/submissions.csv", newline="") as fh:
            ledger_ids = {r["id"]: r["sha256"] for r in csv.DictReader(fh) if r.get("id")}
    with rasterio.open(BRIDGE / "sample_submission.tif") as sample:
        crs_wkt = sample.crs.to_wkt()
        epsg = sample.crs.to_epsg()
    written, ledger_rows = [], []
    for key, card in built.items():
        dots = card["dots"]
        field = np.where(foot, dots.astype(np.float32), np.float32(0.0)).astype(np.float32)
        probe_dir = Path(tempfile.mkdtemp())
        probe = probe_dir / "probe.tif"
        probe_sha = write_with_profile(probe, field, None)
        sha8 = probe_sha[:8]
        shutil.rmtree(probe_dir, ignore_errors=True)
        name = f"{PARENT_ID}-{AXIS}-{key}-{args.stamp}-{sha8}"
        zeros_path = out_dir / f"{name}-zeros.tif"
        nan_path = out_dir / f"{name}.tif"
        pred = model[key]
        rng_ = pred["sign_replication"]["quadrant_range"]
        predicted = (f"{pred['all']['delta']:+.4f} (quadrant range {rng_[0]:+.4f}..{rng_[1]:+.4f}; "
                     f"{pred['sign_replication']['n_positive']}/4 quadrants agree). MODEL: SGMC-extra "
                     f"surrogate, not a score; below the 0.01 evidence floor.")
        note = (f"R0 {PARENT_ID}; TRACKB corridor {card['spec']['corridor_px']} px, traces >=1 km, "
                f"{int(card['add'].sum())} dots extended along strike; pred {pred['all']['delta']:+.3f} MODEL")
        if len(note) > 140:
            raise AssertionError(f"form note too long: {len(note)}")
        if args.no_write:
            written.append(dict(id=name, note=note, predicted_change=predicted, dry_run=True,
                                dot_digest=PRUNE.dot_digest(dots)))
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        nan_arr = np.where(foot, dots.astype(np.float32), np.float32(np.nan)).astype(np.float32)
        nan_sha = write_with_profile(nan_path, nan_arr, float("nan"))
        z_sha = write_with_profile(zeros_path, field, None)
        if z_sha[:8] != sha8:
            raise SystemExit(f"{key}: probed sha8 {sha8} != written {z_sha[:8]}")
        v_zero = validate(zeros_path, foot, cat)
        rep_zero = format_report(zeros_path, BRIDGE / "sample_submission.tif", footprint=foot)
        v_nan = validate(nan_path, foot, cat)
        nan_fail = [k2 for k2, ok in v_nan["checks"].items()
                    if not ok and k2 not in NOTE_NAN_POLICY_CHECKS]
        if not v_zero["all_checks_passed"] or not rep_zero["ok"]:
            raise SystemExit(f"{key}: zeros twin failed the shared gates: "
                             f"{getattr(v_zero, 'failed_checks', '')} / {rep_zero['problems']}")
        if nan_fail:
            raise SystemExit(f"{key}: spec twin failed in-footprint checks: {nan_fail}")
        on_disk = read(zeros_path) > 0.5
        if int(on_disk.sum()) != int(dots.sum()) or bool((on_disk != dots).any()):
            raise SystemExit(f"{key}: re-read raster does not match the in-memory dot set")
        already = ledger_ids.get(name) in {z_sha, nan_sha}
        if (z_sha in existing or nan_sha in existing) and not already:
            raise SystemExit(f"{key}: sha256 already present in the ledger/fleet (exact-hash dedupe)")
        existing |= {z_sha, nan_sha}
        if already:
            print(f"      {key}: already built with these bytes; validated, not re-recorded", flush=True)
        geo_dir.mkdir(parents=True, exist_ok=True)
        geo = TB.traces_to_geojson(card["spec"]["traces"],
                                   card["placement"]["dots_placed_per_trace"] and
                                   {int(k2): int(v2) for k2, v2 in
                                    card["placement"]["dots_placed_per_trace"].items()},
                                   g.transform, crs_wkt, d_cat)
        geo_path = geo_dir / f"{name}-traces.geojson"
        geo_path.write_text(json.dumps(geo, indent=1) + "\n")
        receipt = dict(
            id=name, parent=PARENT_ID, axis=AXIS, value=key, role="candidate",
            n_dots=int(dots.sum()), pct_changed=card["diff"]["pct_changed"],
            dot_digest=PRUNE.dot_digest(dots), trace_set=dict(
                corridor_px=card["spec"]["corridor_px"], min_length_km=MIN_TRACE_LEN_PX / 10.0,
                n_traces=len(card["spec"]["traces"]),
                dots_on_traces=int(sum(t["n_dots"] for t in card["spec"]["traces"])),
                geojson=str(geo_path.relative_to(ROOT)),
                null=detector[key]["null"], first_traces=[
                    trace_record(t, d_cat, foot.shape[1])
                    for t in card["spec"]["traces"][:12]],
            ),
            diff=card["diff"], broken_traces=card["broken"], placement=card["placement"],
            zeros=dict(file=zeros_path.name, sha256=z_sha, bytes=zeros_path.stat().st_size,
                       primary_for_upload=True, validator=v_zero, format_report_ok=rep_zero["ok"],
                       epsg=epsg),
            nan=dict(file=nan_path.name, mode="nan", sha256=nan_sha,
                     bytes=nan_path.stat().st_size, in_footprint_checks_pass=not nan_fail,
                     policy_note="brief v2 §6 form; repo policy prefers -zeros (IR-86-PRUNE-07)"),
            submission_name=name[:140], note=note, predicted_live_change=predicted,
            evidence_class="MODEL", approved_for_weekly_slot=False, submission_slots_used=0,
            provenance=dict(pins=pins, parent_rebuild=rebuild,
                            git_sha=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                   capture_output=True, text=True).stdout.strip(),
                            branch=subprocess.run(["git", "branch", "--show-current"], cwd=ROOT,
                                                  capture_output=True, text=True).stdout.strip()),
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        zeros_path.with_suffix(".json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
        written.append(receipt)
        ledger_rows.append(dict(
            id=name, site="GEMSDOE86", axis=AXIS, value=key, status="BUILT",
            n_dots=int(dots.sum()), pct_changed=card["diff"]["pct_changed"], sha8=sha8,
            parent=PARENT_ID, encoding="zeros", sha256_zeros=z_sha, sha256_nan=nan_sha,
            predicted_change=predicted, evidence_class="MODEL"))
        print(f"      {name}: gates pass ({z_sha[:8]} zeros / {nan_sha[:8]} nan), "
              f"{len(geo['features'])} traces exported", flush=True)

    print("[9/9] evidence, ledger", flush=True)
    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        elapsed_seconds=round(time.time() - t0, 1), axis=AXIS,
        axis_assignment="self-assigned (brief v2 §1 forbids prompting for an axis); TRACKB is the "
                        "only brief-listed axis with no build in this repository",
        parent=dict(id=PARENT_ID, file=PARENT_FILE.name, sha256=PARENT_SHA,
                    n_dots=int(parent.sum()), dot_digest=PRUNE.dot_digest(parent)),
        parent_rebuild=rebuild, pins=pins,
        detector=detector,
        null_interpretation=("The detector finds no 1 km collinear run in a uniform field of the same "
                             "47-dot-per-10 km2 density, so R0's traces are structure in the parent "
                             "field, not a property of the operator."),
        variants={k: dict(value=k, hypothesis=v["spec"]["hypothesis"],
                          corridor_px=v["spec"]["corridor_px"],
                          n_traces=len(v["spec"]["traces"]),
                          diff=v["diff"], broken=v["broken"], placement=v["placement"],
                          predicted_live_change=model[k], proxy=proxy[k]) for k, v in built.items()},
        proxy_parent=proxy["R0"],
        control=dict(role="same donors, same step lengths, random azimuth; measured, never written",
                     stats=ctl_stats, diff=TB.diff_stats(parent, ctl_dots),
                     predicted_live_change=model["CONTROL-randomaz"]["all"],
                     proxy=proxy["CONTROL-randomaz"]),
        instruments=dict(model_class="MODEL (USGS SGMC off-catalogue exact DTI)",
                         proxy_class="PROXY (catalogue hide-and-recover, report only)",
                         canaries=canaries, worst_single_feature_auc=round(worst, 4),
                         note="both are REPORT ONLY per brief v2 §6; neither is a score"),
        gates=dict(format="shared validator + shared format_report on both twins, re-read from disk",
                   zero_catalogue_mass="asserted in memory and after re-read",
                   collar_3px="asserted for every newly emitted cell",
                   spacing_floor="every new cell >= sqrt(8) px from every parent dot",
                   count_fixed="asserted for every variant",
                   pct_changed_contract=f"{MIN_PCT_CHANGED}-{MAX_PCT_CHANGED}% enforced",
                   sha_novel="checked against ledger, data/scored_fleet and docs/downloads",
                   parent_diff="recorded per variant", uniqueness_thresholds="NOT applied"),
        written=[w["id"] for w in written], no_slot_authorized=True,
        not_a_score="Every number here is a MODEL projection or a PROXY measurement.",
    )
    if not args.no_write:
        (ROOT / "evidence" / "trackb_axis_20261023.json").write_text(
            json.dumps(summary, indent=2, allow_nan=False) + "\n")
        variants_path = ROOT / "ledger" / "variants_trackb.json"
        entries = json.loads(variants_path.read_text()) if variants_path.is_file() else []
        by_id = {e.get("id"): i for i, e in enumerate(entries)}
        for row in ledger_rows:
            entry = dict(row, gate_all_pass=True)
            if row["id"] in by_id:
                entries[by_id[row["id"]]] = entry
            else:
                entries.append(entry)
        variants_path.write_text(json.dumps(entries, indent=2) + "\n")
        subprocess.run([sys.executable, str(ROOT / "scripts/build_ledger.py")], check=True, cwd=ROOT)
        print(f"      wrote evidence/trackb_axis_20261023.json and {len(ledger_rows)} ledger rows",
              flush=True)
    else:
        print(json.dumps({k: v["all"]["delta"] for k, v in model.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
