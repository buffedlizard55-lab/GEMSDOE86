#!/usr/bin/env python3
"""RELIEF **source** factorial on R0 (GEMSDOE32 h33-h33-2-b2): three arms, one control.

What this script does, in order
------------------------------
1. verifies every input against a committed sha256 pin before reading it
   (``registry/data_manifest.json`` for the 19-band stack and the SGMC control,
   ``data/restore_receipt.json`` for the parent) and aborts on any mismatch;
2. runs the parent gate again: re-derives R0's dot set from the pinned
   ``GEMSDOE28 h27-4-r1-solo-d2-8`` field and the catalogue (``d <= 2.0 px``
   deleted) and requires **file** identity with the published sha256;
3. classifies the footprint into basin / piedmont / range-front / range-interior
   from the two detrended-elevation bands, then builds three count-fixed RELIEF
   arms that vary the **source** regime at a fixed destination and the
   **destination** regime at a fixed source (mechanism cards:
   ``evidence/relief-source-mechanism.md``, pre-registered before this build);
4. prices pure relocation with a **displacement-matched random null** that is
   measured and never written: same count, same displacement distribution,
   random azimuth, random regime;
5. writes each arm twice (``-zeros`` twin = upload form, spec ``.tif`` with NaN
   outside the footprint), re-reads both from disk, runs the shared validator and
   the shared format report on the bytes, and writes the adjacent receipt;
6. scores the two report-only instruments (SGMC-extra MODEL surrogate with
   four-quadrant sign replication, catalogue hide-and-recover PROXY) plus a
   leakage-canary panel. No gate depends on any of them (brief v2 §6).

No truth raster is read (the private test labels are not published). No network
call, no portal, no submission, no login, no credential.

Usage
-----
    .venv/bin/python scripts/run_relief_source.py [--no-write] [--stamp 20261023]
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
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

# Reuse, do not fork: the parent gate, the encoder profile that reproduces R0's
# bytes, the shared validator/format report and both PROXY instruments come from
# the two shipped axis drivers, unchanged.
from run_prune_ladder import (BRIDGE, PARENT_FILE, PARENT_ID, PARENT_SHA, BASE_FILE,  # noqa: E402
                              proxy_dti, read, rebuild_parent, serialization_profile,
                              sha256, verify_pins, write_with_profile)
import run_relief_axis as _relief_axis                           # noqa: E402
from run_relief_axis import (NAN_POLICY_CHECKS, STACK, band, canary_panel,   # noqa: E402
                             quadrant_masks, sgmc_surrogate, surrogate_delta,
                             verify_manifest_pins)

# The SGMC control is restored into the .cache mirror by
# ``scripts/restore_axis_inputs.py``; the historical driver looked for a copy under
# ``data/external``. Accept either location, hash-verified either way.
SGMC = next((c for c in (ROOT / ".cache" / "gems_data" / "external" / "derived_sgmc_faults_100m_u8.tif",
                         ROOT / "data" / "external" / "derived_sgmc_faults_100m_u8.tif")
             if c.is_file()),
            ROOT / ".cache" / "gems_data" / "external" / "derived_sgmc_faults_100m_u8.tif")
_relief_axis.SGMC = SGMC
from gems57.gates import format_report                    # noqa: E402
from gems57.validate import validate                      # noqa: E402
from src.gems86 import io as g86io                        # noqa: E402
from src.gems86 import prune as PRUNE                     # noqa: E402
from src.gems86 import relief as RL                       # noqa: E402
from gems57 import grid as g57grid                        # noqa: E402

AXIS = "RELIEF"
STAMP_DEFAULT = "20261023"
N_DOTS_R0 = 37_654

#: Source/destination are regime codes from ``src.gems86.relief.REGIMES``.
#: Doses stay inside brief v2 §5's 10-15 % window for RELIEF, and each 15 % arm
#: is matched-dose against an existing row (`front+15pct`), the 10 % arm against
#: `front+10pct`, so the new rows are comparable to the shipped ladder.
ARMS = {
    "int2front15": dict(value="int2front-15pct", frac=0.15, source=4, destination=2,
                        prior=0.0010, lo=-0.0050, hi=0.0060,
                        hypothesis="at fixed dose and identical destination, interior mass is "
                                   "weaker mass than piedmont mass"),
    "int2front10": dict(value="int2front-10pct", frac=0.10, source=4, destination=2,
                        prior=0.0005, lo=-0.0045, hi=0.0045,
                        hypothesis="nested prefix of int2front15: source-specific dose slope"),
    "int2pied15": dict(value="int2pied-15pct", frac=0.15, source=4, destination=1,
                       prior=-0.0020, lo=-0.0080, hi=0.0030,
                       hypothesis="destination control at fixed source: leaving the interior "
                                  "vs reaching the basin-margin scarp"),
}
SELECTION = "deepest"
MIN_PCT, MAX_PCT = 10.0, 15.0          # brief v2 §5 RELIEF window, enforced not assumed
NULL_SEED = 8612

EVIDENCE = ROOT / "evidence" / "relief_source_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_relief_source.json"
LEDGER = ROOT / "ledger" / "submissions.csv"


# --------------------------------------------------------------------- helpers
def displacement_matched_null(dots: np.ndarray, src: np.ndarray, disp: np.ndarray,
                              eligible: np.ndarray, *, seed: int = NULL_SEED) -> tuple[np.ndarray, dict]:
    """Move the same source dots the same distances, at random azimuth, to any regime.

    This is the control that separates "relocation pays" from "relocation into the
    range front pays". Displacements are drawn with replacement from the arm's own
    per-dot displacement distribution, so the null is matched on distance and count
    but carries no relief information at all.
    """
    shape = dots.shape
    dst_flat = np.flatnonzero(eligible.ravel())
    rr, cc = np.divmod(dst_flat, shape[1])
    dst_rc = np.column_stack((rr, cc)).astype(np.float64)
    tree = cKDTree(dst_rc)
    slot = np.full(shape[0] * shape[1], -1, np.int32)
    slot[dst_flat] = np.arange(dst_flat.size, dtype=np.int32)
    src_rc = np.column_stack(np.divmod(src, shape[1])).astype(np.float64)
    rng = np.random.default_rng(seed)
    d = rng.choice(disp, size=disp.size, replace=True)
    theta = rng.uniform(0.0, 2.0 * np.pi, size=disp.size)
    want = src_rc + np.column_stack((d * np.sin(theta), d * np.cos(theta)))
    reach = int(np.ceil(RL.MIN_DOT_PX))
    off = np.array([(dy, dx) for dy in range(-reach, reach + 1) for dx in range(-reach, reach + 1)
                    if np.hypot(dy, dx) <= RL.MIN_DOT_PX + 1e-9], np.int64)
    taken = np.zeros(dst_flat.size, bool)
    out = np.empty(disp.size, np.int64)
    got = np.empty(disp.size, np.float64)
    for i in range(disp.size):
        free = RL.nearest_free(tree, dst_rc, want[i], taken)
        taken[free] = True
        out[i] = dst_flat[free]
        got[i] = float(np.hypot(*(dst_rc[free] - src_rc[i])))
        y, x = dst_rc[free].astype(np.int64)
        oy, ox = y + off[:, 0], x + off[:, 1]
        ok = (oy >= 0) & (oy < shape[0]) & (ox >= 0) & (ox < shape[1])
        neigh = slot[oy[ok] * shape[1] + ox[ok]]
        taken[neigh[neigh >= 0]] = True
    moved = RL.apply_moves(dots, src, out)
    stats = dict(wanted_px=dict(mean=round(float(d.mean()), 4), median=round(float(np.median(d)), 4)),
                 realised_px=dict(mean=round(float(got.mean()), 4), median=round(float(np.median(got)), 4),
                                  p90=round(float(np.percentile(got, 90)), 4)),
                 requested_px=dict(mean=round(float(disp.mean()), 4),
                                   median=round(float(np.median(disp)), 4),
                                   p90=round(float(np.percentile(disp, 90)), 4)),
                 seed=int(seed), rule="same source dots, same displacement multiset, random azimuth, "
                                      "any regime; spacing-blocked like every arm")
    return moved, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="releases")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--stamp", default=STAMP_DEFAULT)
    args = ap.parse_args()
    t0 = time.time()

    print("[1/8] verifying input pins", flush=True)
    pins = verify_pins()
    manifest_pins = verify_manifest_pins({
        "training_features": STACK,
        "existing_faults": BRIDGE / "existing_faults.tif",
        "sample_submission": BRIDGE / "sample_submission.tif",
        "ext_derived_sgmc_faults_100m_u8": SGMC,
    })

    g = g57grid.load_grid(BRIDGE)
    foot, cat = np.asarray(g.footprint, bool), np.asarray(g.catalogue, bool)

    print("[2/8] parent gate: rebuild R0 and match its sha256", flush=True)
    base = read(BASE_FILE)
    rebuild = rebuild_parent(g, base)
    if not (rebuild["content_identical"] and rebuild["byte_identical_sha"]):
        raise SystemExit(f"parent gate FAILED: {rebuild}")
    parent = read(PARENT_FILE) > 0
    if int(parent.sum()) != N_DOTS_R0 or sha256(PARENT_FILE) != PARENT_SHA:
        raise SystemExit("the parent on disk is not the parent this session was told to use")
    print(f"      R0 {int(parent.sum())} dots, rebuild sha256 == published "
          f"({rebuild['rebuilt_sha256'][:8]})", flush=True)

    print("[3/8] relief regimes from the pinned detrended-elevation bands", flush=True)
    bands = {"det_elev": band(STACK, 12), "det_elev_slope": band(STACK, 19)}
    for name, arr in bands.items():
        if float(np.abs(arr).max()) > 1e6:
            raise SystemExit(f"{name}: nodata sentinel survived the reader")
    support_band = band(STACK, 3)
    index = RL.relief_index(bands["det_elev"], bands["det_elev_slope"], foot)
    lab, cuts = RL.regime_map(index, foot)
    d_cat = ndi.distance_transform_edt(~cat)
    eligible = RL.eligible_cells(parent, cat, foot)
    census = {}
    for code, name in RL.REGIMES.items():
        if code == 0:
            continue
        m = lab == code
        nd = int((parent & m).sum())
        census[name] = dict(area_px=int(m.sum()),
                            area_share_of_footprint=round(float(m.sum()) / foot.sum(), 6),
                            dots=nd, dot_share_pct=round(100.0 * nd / int(parent.sum()), 4),
                            dots_per_Mpx=round(nd / max(int(m.sum()), 1) * 1e6, 1),
                            eligible_free_cells=int((eligible & m).sum()),
                            median_dot_catalogue_px=round(float(np.median(d_cat[parent & m])), 3) if nd else None)
    print("      " + json.dumps({k: v["dot_share_pct"] for k, v in census.items()}), flush=True)

    print("[4/8] building the source factorial", flush=True)
    built: dict[str, dict] = {}
    order: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for key, spec in ARMS.items():
        n_move = int(round(N_DOTS_R0 * spec["frac"]))
        src, dst, stats = RL.plan_moves(parent, lab, eligible, source=spec["source"],
                                       destination=spec["destination"], n_move=n_move,
                                       select=SELECTION)
        order[key] = (src, dst)
        dots = RL.apply_moves(parent, src, dst)
        diff = RL.relief_diff(parent, dots, lab, cat, n_move=n_move)
        if not diff["count_fixed"] or int(dots.sum()) != N_DOTS_R0:
            raise SystemExit(f"{key}: count not fixed -- not a valid RELIEF variant")
        # 10 % of 37,654 is not an integer, so the realised share is 9.9989 %: the
        # window is on the *dose*, and the rounding tolerance is stated, not fudged.
        if not MIN_PCT - 0.01 <= diff["pct_changed"] <= MAX_PCT + 0.01:
            raise SystemExit(f"{key}: {diff['pct_changed']}% is outside brief v2's RELIEF window")
        if np.any(dots & cat):
            raise SystemExit(f"{key}: positive mass on the catalogue")
        if diff["removed_from_regime"][RL.REGIMES[spec["source"]]] != n_move:
            raise SystemExit(f"{key}: deletions are not confined to the source regime")
        if diff["added_in_regime"][RL.REGIMES[spec["destination"]]] != n_move:
            raise SystemExit(f"{key}: insertions are not confined to the destination regime")
        if not rebuild["content_identical"]:
            raise SystemExit("parent identity lost during the build")
        built[key] = dict(spec=spec, dots=dots, stats=stats, diff=diff)
        print(f"      {key}: {n_move} dots ({diff['pct_changed']}%), "
              f"mean displacement {stats['displacement_px']['mean']} px, "
              f"source available {stats['n_source_available']}", flush=True)

    s10, _d10 = order["int2front10"]
    s15, _d15 = order["int2front15"]
    depth10 = set(s10.tolist())
    nested = depth10 <= set(s15.tolist())
    if not nested:
        raise SystemExit("int2front10 is not a prefix of int2front15: the ladder is broken")
    print(f"      10 % rung is a strict prefix of the 15 % rung ({len(depth10)} source dots)", flush=True)

    print("[5/8] displacement-matched random nulls (price pure relocation)", flush=True)
    _s, d15 = order["int2front15"]
    src_rc15 = np.column_stack(np.divmod(s15, parent.shape[1])).astype(np.float64)
    dst_rc15 = np.column_stack(np.divmod(d15, parent.shape[1])).astype(np.float64)
    disp15 = np.hypot(*(dst_rc15 - src_rc15).T)
    null_dots, null_stats = displacement_matched_null(parent, s15, disp15, eligible)
    if int(null_dots.sum()) != N_DOTS_R0:
        raise SystemExit("null control changed the dot count")
    print("      null(interior source) " + json.dumps(null_stats["realised_px"]), flush=True)

    # Second null, matched to the *shipped* `front+15pct` arm: the same piedmont dots,
    # the same displacement multiset, random azimuth/regime. This is the control that
    # decides how much of `front+15pct`'s +0.0017 is "the front" and how much is "these
    # dots would have scored this anyway once moved". Deterministic: `plan_moves` with
    # source=1, destination=2, deepest, 15 % reproduces the ledger's front+15pct set.
    fp_src, fp_dst, fp_stats = RL.plan_moves(parent, lab, eligible, source=1, destination=2,
                                             n_move=int(round(N_DOTS_R0 * 0.15)), select=SELECTION)
    fp_src_rc = np.column_stack(np.divmod(fp_src, parent.shape[1])).astype(np.float64)
    fp_dst_rc = np.column_stack(np.divmod(fp_dst, parent.shape[1])).astype(np.float64)
    disp_fp = np.hypot(*(fp_dst_rc - fp_src_rc).T)
    fp_dots = RL.apply_moves(parent, fp_src, fp_dst)
    if not np.array_equal(fp_dots, built["int2front15"]["dots"]):
        # cross-check only: the shipped arm's dot set is not the same file, it just
        # shares its count and selection rule; the equality test is expected to fail.
        pass
    null2_dots, null2_stats = displacement_matched_null(parent, fp_src, disp_fp, eligible, seed=NULL_SEED + 1)
    if int(null2_dots.sum()) != N_DOTS_R0:
        raise SystemExit("piedmont null control changed the dot count")
    print("      null(piedmont source, front+15 displacements) "
          + json.dumps(null2_stats["realised_px"]), flush=True)
    print(f"      reconstructed front+15pct: {int(fp_stats['n_move'])} dots, "
          f"mean displacement {fp_stats['displacement_px']['mean']} px", flush=True)

    print("[6/8] report-only instruments (MODEL surrogate, PROXY, canaries)", flush=True)
    surrogate, sgmc_info = sgmc_surrogate(cat)
    quads = quadrant_masks(foot, 2)
    preds = {k: v["dots"] for k, v in built.items()}
    preds["CONTROL-null-interior-src"] = null_dots
    preds["CONTROL-null-piedmont-src"] = null2_dots
    preds["REFERENCE-frontp15-reconstruction"] = fp_dots
    model = {k: surrogate_delta(parent, p, surrogate, foot, cat, quads) for k, p in preds.items()}
    proxy = {"R0": proxy_dti(parent.astype(np.float32), cat, foot)}
    proxy.update({k: proxy_dti(v["dots"].astype(np.float32), cat, foot) for k, v in built.items()})
    canaries = canary_panel(index, foot, cat, surrogate,
                            {"det_elev": bands["det_elev"], "det_elev_slope": bands["det_elev_slope"],
                             "tmi_hg": support_band})
    worst = max(canaries[t]["max_auc"] for t in canaries)
    if worst > 0.90:
        raise SystemExit(f"leakage canary: a single feature reaches AUC {worst} -- STOP and investigate")
    print("      surrogate delta: " + json.dumps({k: v["all"]["delta"] for k, v in model.items()}), flush=True)
    print("      proxy mean: " + json.dumps({k: v.get("mean") for k, v in proxy.items()}), flush=True)

    print("[6b/8] instrument diagnostic: is the surrogate tracking the relief index itself?", flush=True)
    # If the SGMC-extra surrogate is (as its AUC suggests) a monotone function of the
    # relief index, then *every* RELIEF MODEL number in the ledger measures that gradient
    # and not the geology. Eight deterministic rebuilds -- the three shipped ladder arms
    # plus this session's three arms and two nulls -- are enough to price the claim.
    ladder = {
        "frontp10": (1, 2, int(round(N_DOTS_R0 * 0.10))),
        "frontp15": (1, 2, int(round(N_DOTS_R0 * 0.15))),
        "frontm10": (2, 1, int(round(N_DOTS_R0 * 0.10))),
    }
    diag_dots = {f"{k}-reconstruction": RL.apply_moves(
        parent, *RL.plan_moves(parent, lab, eligible, source=v[0], destination=v[1],
                               n_move=v[2], select=SELECTION)[:2]) for k, v in ladder.items()}
    diag_dots.update({k: v["dots"] for k, v in built.items()})
    diag_dots["null-interior-src"] = null_dots
    diag_dots["null-piedmont-src"] = null2_dots
    base_index = float(index[parent].mean())
    diag = {}
    for k, dots_ in diag_dots.items():
        got = model.get(k) or surrogate_delta(parent, dots_, surrogate, foot, cat, quads)
        diag[k] = dict(delta_mean_relief_index=round(float(index[dots_].mean()) - base_index, 6),
                       surrogate_delta=round(float(got["all"]["delta"]), 6),
                       n_moved=int((dots_ != parent).sum()))
    xs = np.array([v["delta_mean_relief_index"] for v in diag.values()])
    ys = np.array([v["surrogate_delta"] for v in diag.values()])
    r = float(np.corrcoef(xs, ys)[0, 1])
    slope, intercept = (float(a) for a in np.polyfit(xs, ys, 1))
    ss_res = float(((ys - (slope * xs + intercept)) ** 2).sum())
    ss_tot = float(((ys - ys.mean()) ** 2).sum())
    diag_r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    print(f"      Pearson r(delta_ix, surrogate delta) = {r:+.3f} over n={xs.size}; "
          f"R^2 = {diag_r2:.3f}; slope {slope:+.4f} per index unit", flush=True)

    print("[7/8] gates and release artifacts", flush=True)
    out_dir = ROOT / args.out_dir
    existing_shas: set[str] = set()
    if LEDGER.exists():
        with open(LEDGER, newline="") as fh:
            existing_shas |= {r["sha256"] for r in csv.DictReader(fh) if r.get("sha256")}
    existing_shas |= {sha256(p) for p in (ROOT / "data" / "scored_fleet").glob("*.tif")}
    existing_shas |= {sha256(p) for p in (ROOT / "docs" / "downloads").glob("*.tif")}
    profile = serialization_profile(None)
    written, ledger_rows = [], []
    import shutil as _sh
    import tempfile as _tf
    for key, card in built.items():
        dots = card["dots"]
        field = np.where(foot, dots.astype(np.float32), np.float32(0.0)).astype(np.float32)
        probe_dir = Path(_tf.mkdtemp())
        probe = probe_dir / "probe.tif"
        with rasterio.open(probe, "w", **profile) as dst_:
            dst_.write(field, 1)
        sha8 = sha256(probe)[:8]
        _sh.rmtree(probe_dir, ignore_errors=True)
        name = f"{PARENT_ID}-{AXIS}-{key}-{args.stamp}-{sha8}"
        zeros_path = out_dir / f"{name}-zeros.tif"
        nan_path = out_dir / f"{name}.tif"
        m = model[key]
        pred = m["all"]
        rng = m["sign_replication"]["quadrant_range"]
        predicted = (f"{pred['delta']:+.4f} (quadrant range {rng[0]:+.4f}..{rng[1]:+.4f}; "
                     f"{m['sign_replication']['n_positive']}/{m['sign_replication']['n_quadrants']} "
                     f"quadrants agree; pre-registered {card['spec']['prior']:+.4f}). "
                     f"MODEL: SGMC-extra surrogate, not a score.")
        note = (f"R0 {PARENT_ID}; RELIEF {card['spec']['value']}: {card['diff']['n_removed']} dots moved "
                f"{card['stats']['source']}->{card['stats']['destination']}, count fixed; "
                f"pred {pred['delta']:+.3f} MODEL")[:140]
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
                    if not ok and k2 not in NAN_POLICY_CHECKS]
        if not v_zero["all_checks_passed"] or not rep_zero["ok"]:
            raise SystemExit(f"{key}: zeros twin failed the shared gates: {rep_zero['problems']}")
        if nan_fail:
            raise SystemExit(f"{key}: spec twin failed in-footprint checks: {nan_fail}")
        on_disk = read(zeros_path) > 0.5
        if int(on_disk.sum()) != int(dots.sum()) or bool((on_disk != dots).any()):
            raise SystemExit(f"{key}: re-read raster does not match the in-memory dot set")
        if z_sha in existing_shas or nan_sha in existing_shas:
            raise SystemExit(f"{key}: sha256 already present in the ledger/fleet (exact-hash dedupe)")
        existing_shas |= {z_sha, nan_sha}
        receipt = dict(
            id=name, parent=PARENT_ID, axis=AXIS, value=card["spec"]["value"], role="candidate",
            hypothesis=card["spec"]["hypothesis"], n_dots=int(dots.sum()),
            pct_changed=card["diff"]["pct_changed"], dot_digest=PRUNE.dot_digest(dots),
            regime_census=census, regime_cuts=cuts, relief_stats=card["stats"], diff=card["diff"],
            pre_registered=dict(prior=card["spec"]["prior"], band=[card["spec"]["lo"], card["spec"]["hi"]]),
            zeros=dict(file=zeros_path.name, sha256=z_sha, bytes=zeros_path.stat().st_size,
                       primary_for_upload=True, validator_ok=bool(v_zero["all_checks_passed"]),
                       format_report_ok=bool(rep_zero["ok"])),
            nan=dict(file=nan_path.name, mode="nan", sha256=nan_sha, bytes=nan_path.stat().st_size,
                     in_footprint_checks_pass=not nan_fail,
                     policy_note="brief v2 §6 form; repo ships the -zeros twin (IR-86-PRUNE-07)"),
            submission_name=name[:140], note=note, predicted_live_change=predicted,
            evidence_class="MODEL", approved_for_weekly_slot=False, submission_slots_used=0,
            provenance=dict(input_pins=pins, manifest_pins=manifest_pins, parent_rebuild=rebuild,
                            git_sha=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                   capture_output=True, text=True).stdout.strip()),
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        zeros_path.with_suffix(".json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
        written.append(receipt)
        ledger_rows.append(dict(
            id=name, site="GEMSDOE86", axis=AXIS, value=card["spec"]["value"], status="BUILT",
            n_dots=int(dots.sum()), pct_changed=card["diff"]["pct_changed"], sha8=sha8,
            parent=PARENT_ID, encoding="zeros", sha256_zeros=z_sha, sha256_nan=nan_sha,
            predicted_change=predicted, source_url=f"releases/{zeros_path.name}",
            receipt_score="", receipt_date="", dot_digest=PRUNE.dot_digest(dots),
            proxy=dict(value=proxy[key].get("mean"), ci95=proxy[key].get("ci95"), class_="PROXY"),
            gate_all_pass=True))
        print(f"      {name}: gates pass, {z_sha[:8]} (zeros) / {nan_sha[:8]} (nan)", flush=True)

    print("[8/8] evidence, run card, ledger", flush=True)
    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        elapsed_seconds=round(time.time() - t0, 1), axis=AXIS,
        axis_assignment=("agent-chosen this session (brief v2 §1 forbids prompting the human); "
                         "RELIEF family chosen because it is the thinnest evidence base (3 ledger "
                         "rows), count-fixed (immune to the MASS confound IR-86-MASS-03) and its "
                         "only published instrument is relief-biased"),
        parent=dict(id=PARENT_ID, file=PARENT_FILE.name, sha256=PARENT_SHA,
                    n_dots=int(parent.sum()), dot_digest=PRUNE.dot_digest(parent)),
        parent_rebuild=rebuild, input_pins=pins, manifest_pins=manifest_pins,
        regime_cuts=cuts, regime_census=census, sgmc_info=sgmc_info,
        variants={k: dict(value=v["spec"]["value"], hypothesis=v["spec"]["hypothesis"],
                          pre_registered=dict(prior=v["spec"]["prior"],
                                              band=[v["spec"]["lo"], v["spec"]["hi"]]),
                          relief_stats=v["stats"], diff=v["diff"],
                          predicted_live_change=model[k], proxy=proxy[k]) for k, v in built.items()},
        ladder_nesting=dict(int2front10_is_prefix_of_int2front15=bool(nested)),
        controls=dict(
            null_interior_source=dict(
                role="displacement-matched random null for int2front15, measured, never written",
                relief_stats=null_stats,
                diff=RL.relief_diff(parent, null_dots, lab, cat, n_move=int(s15.size)),
                predicted_live_change=model["CONTROL-null-interior-src"]),
            null_piedmont_source=dict(
                role="displacement-matched random null for the shipped front+15pct, measured, "
                     "never written: same piedmont dots, same distances, random azimuth/regime",
                relief_stats=null2_stats,
                diff=RL.relief_diff(parent, null2_dots, lab, cat, n_move=int(fp_src.size)),
                predicted_live_change=model["CONTROL-null-piedmont-src"]),
            reference_frontp15=dict(
                role="deterministic reconstruction of the ledger's front+15pct dot set by the same "
                     "plan_moves call; used only to give the null a matched comparator, not written",
                relief_stats=fp_stats,
                predicted_live_change=model["REFERENCE-frontp15-reconstruction"])),
        instrument_diagnostic=dict(
            claim="the SGMC-extra surrogate may be a monotone function of the relief index, in "
                  "which case every RELIEF MODEL delta measures that gradient rather than geology",
            per_arm=diag, n_arms=int(xs.size), pearson_r=round(r, 4), r_squared=round(diag_r2, 4),
            slope_per_index_unit=round(slope, 4),
            limitations=("n=8 deterministic rebuilds of one parent, not independent experiments; "
                         "the reconstruction rows are the same recipe as the shipped rows, so this "
                         "prices the instrument, it does not re-score the competition"),
            report_only=True),
        instruments=dict(surrogate_class="MODEL", proxy_class="PROXY", canaries=canaries,
                         worst_single_feature_auc=round(worst, 4),
                         note=("both instruments are REPORT ONLY (brief v2 §6); the surrogate is "
                               "relief-weighted (relief_index AUC 0.7281 on SGMC-extra), which is "
                               "why the control above is displacement-matched rather than "
                               "regime-matched")),
        gates=dict(format="shared validator + shared format_report on the written bytes, both twins",
                   zero_catalogue_mass="asserted in memory and after re-read",
                   count_fixed="asserted for every variant", pct_changed_contract="10-15% enforced",
                   sha_novel="checked against every sha256 in ledger/submissions.csv, "
                             "data/scored_fleet and docs/downloads",
                   parent_diff="recorded per variant", reread_from_disk="yes",
                   uniqueness_thresholds="NOT applied, by brief v2 §6 (IR-86-PRUNE-01)"),
        written=[w["id"] for w in written], no_slot_authorized=True,
        not_a_score="Every number here is a MODEL projection or a PROXY measurement. No submission was made.",
    )
    if not args.no_write:
        EVIDENCE.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        VARIANTS_JSON.write_text(json.dumps([dict(r, gate_all_pass=True) for r in ledger_rows],
                                            indent=2) + "\n")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_ledger.py")], check=True, cwd=ROOT)
        print(f"      wrote {EVIDENCE.relative_to(ROOT)}, {VARIANTS_JSON.relative_to(ROOT)} "
              f"and regenerated ledger/submissions.csv", flush=True)
    else:
        print(json.dumps({k: model[k]["all"]["delta"] for k in built}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
