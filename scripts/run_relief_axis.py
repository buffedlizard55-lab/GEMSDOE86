#!/usr/bin/env python3
"""RELIEF axis on R0 (GEMSDOE32 h33-h33-2-b2): three doses of one signed edit.

What this script does, in order
------------------------------
1. verifies the sha256 of every input against a committed pin before reading it
   (``registry/data_manifest.json`` for the 19-band stack and the SGMC control,
   ``data/restore_receipt.json`` for the parent), and aborts on any mismatch;
2. re-derives R0's dot set from its pinned parent field and the catalogue and
   asserts byte-for-byte equality with the published file -- the brief's parent
   gate, run again here and never approximated;
3. classifies the scored footprint into basin / piedmont / range-front /
   range-interior from the two detrended-elevation bands (``src.gems86.relief``),
   then builds three count-fixed RELIEF variants -- ``front+10pct``,
   ``front+5pct`` (a strict prefix of the first) and ``front-5pct`` (the sign
   flip) -- plus a displacement-matched in-regime control that is measured, never
   written, because it is not a slot candidate;
4. writes each candidate twice (``-zeros`` twin, which is the primary form for this
   session, and the spec ``.tif`` with NaN outside the footprint), re-reads both
   from disk and runs the shared validator and format report on the bytes;
5. scores two report-only instruments: a USGS SGMC hide-and-recover *surrogate*
   that produces the predicted live change (MODEL) with a four-quadrant sign
   replication, and the catalogue hide-and-recover PROXY; plus a leakage canary
   panel. No gate depends on any of them (brief §6).

No truth raster is read (there is none: the private test labels are not published).
No network call, no portal, no submission, no login, no credential.

Usage
-----
    .venv/bin/python scripts/run_relief_axis.py [--no-write] [--stamp 20261023]
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

# Reuse, don't rebuild: the parent gate, the encoder profile that reproduces R0's
# bytes, the shared validator/format report and the PROXY instrument all come from
# the PR #29 ladder script and the vendored template, unchanged.
from run_prune_ladder import (BRIDGE, PARENT_FILE, PARENT_ID, PARENT_SHA,   # noqa: E402
                             proxy_dti, read, rebuild_parent, sha256,
                             serialization_profile, verify_pins, write_with_profile)
from gems57 import metric as g57metric                       # noqa: E402
from gems57 import grid as g57grid                           # noqa: E402
from gems57.gates import format_report                       # noqa: E402
from gems57.validate import validate                         # noqa: E402
from src.gems86 import io as g86io
from src.gems86 import prune as PRUNE          # identity digest only        # noqa: E402
from src.gems86 import relief as RL                                           # noqa: E402

MANIFEST = ROOT / "registry" / "data_manifest.json"
FLEET = ROOT / "data" / "scored_fleet"
EXTERNAL = ROOT / ".cache" / "external"
STACK = BRIDGE / "training_features.tif"
SGMC = ROOT / "data" / "external" / "derived_sgmc_faults_100m_u8.tif"
EVIDENCE = ROOT / "evidence" / "relief_axis_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants.json"

#: Axis assignment recorded, per brief §1: the human assigned this axis in-session
#: on 2026-10-23 (Arena message "RELIEF", plus "-zeros" as the primary upload form).
AXIS = "RELIEF"
AXIS_ASSIGNMENT = ("HUMAN-ASSIGNED this session (brief v2 §1). PRUNE is deliberately not "
                   "touched: it is already spent on this parent by three earlier sessions "
                   "(IR-86-PRUNE-08).")
N_DOTS_R0 = 37654
#: dose = fraction of the parent's dots relocated (count and unit mass fixed).
#: dose = fraction of the parent's dots relocated (count and unit mass fixed).
#: 10-15% is the range brief v2 §5 allows for RELIEF; +10pct is a strict prefix of
#: +15pct, and -10pct is the same size in the opposite direction.
DOSES = {
    "frontp15": dict(value="front+15pct", frac=0.15, source=1, destination=2,
                     hypothesis="more mass on the basin-margin range front"),
    "frontp10": dict(value="front+10pct", frac=0.10, source=1, destination=2,
                     hypothesis="lower dose of the same direction (nested inside +15)"),
    "frontm10": dict(value="front-10pct", frac=0.10, source=2, destination=1,
                     hypothesis="sign flip: mass off the front into the middle tercile"),
}
SELECTION = "deepest"
MIN_PCT_CHANGED, MAX_PCT_CHANGED = 1.0, 50.0
#: checks the vendored validator runs only to enforce this repo's all-finite policy;
#: the spec-form file is allowed to fail exactly these (brief v2 §6 wants NaN outside).
NAN_POLICY_CHECKS = {"no_nan_anywhere", "outside_footprint_zero"}


# --------------------------------------------------------------------- inputs
def verify_manifest_pins(ids: dict[str, Path]) -> dict:
    """Every file this script reads from the manifest must match its pinned digest."""
    files = {f["id"]: f for f in json.loads(MANIFEST.read_text())["files"]}
    out = {}
    for eid, path in ids.items():
        entry = files[eid]
        if not path.is_file():
            raise SystemExit(f"pinned input {eid} is absent: {path} (run scripts/restore_data.py "
                             f"--with-external, and for {SGMC.name} the ext pin in the manifest)")
        got = sha256(path)
        if got != entry["sha256"]:
            raise SystemExit(f"PIN MISMATCH {eid}: {got} != {entry['sha256']}")
        if path.stat().st_size != entry["bytes"]:
            raise SystemExit(f"SIZE MISMATCH {eid}: {path.stat().st_size} != {entry['bytes']}")
        out[eid] = dict(path=str(path.relative_to(ROOT)), sha256=got, bytes=entry["bytes"],
                        verified=True, organizer_authenticated=False,
                        provenance=entry["provenance"])
    return out


def band(path: Path, index: int) -> np.ndarray:
    """One band of the pinned stack, scrubbed through the repo's own reader.

    ``src.gems86.io.read_band`` is the only sanctioned way in: it clears both the
    non-finite values and the ``-3.4028234663852886e+38`` nodata sentinel that the
    stack stores *inside* the footprint (3,061 cells). Reading the raw band and
    scrubbing only non-finite values leaves those spikes in, and they dominate the
    standardisation -- a first pass here classified 100% of the parent's dots as
    "basin" for exactly that reason. Fixed, and recorded in IRREGULARITIES.md.
    """
    return g86io.read_band(Path(path), int(index)).astype(np.float64)


# ------------------------------------------------------------------ surrogate
def sgmc_surrogate(catalogue: np.ndarray) -> tuple[np.ndarray, dict]:
    """USGS SGMC fault pixels that are NOT in the training catalogue.

    This is an *independent public-domain fault inventory* (DOI 10.5066/..., see the
    manifest provenance line), not the test truth. It is used to project the sign and
    size of a relocation, never as a gate, and it is never used to build a raster.
    """
    with rasterio.open(SGMC) as src:
        a = src.read(1)
    sg = np.isfinite(a) & (a > 0)
    extra = sg & ~catalogue
    return extra, dict(sgmc_pixels=int(sg.sum()), catalogue_pixels=int(catalogue.sum()),
                       sgmc_pixels_not_in_catalogue=int(extra.sum()),
                       overlap_fraction=round(float((sg & catalogue).sum() / max(int(sg.sum()), 1)), 4),
                       note=("surrogate for 'new-fault' truth only in the weak sense that both are "
                             "mappings of faults the training catalogue lacks; its density is itself "
                             "relief-dependent, which is the confounder named on the mechanism cards"))


def surrogate_delta(pred_parent: np.ndarray, pred_child: np.ndarray, truth: np.ndarray,
                    footprint: np.ndarray, catalogue: np.ndarray,
                    quadrants: list[np.ndarray] | None = None) -> dict:
    """Exact DTI difference (child - parent) against the surrogate truth, masked pixel-exactly."""
    regions = {"all": footprint}
    if quadrants:
        regions.update({f"q{i}": q for i, q in enumerate(quadrants, start=1)})
    out = {}
    for name, valid in regions.items():
        a = g57metric.dti_binary(pred_parent, truth, valid=valid, known=catalogue)
        b = g57metric.dti_binary(pred_child, truth, valid=valid, known=catalogue)
        out[name] = dict(dti_parent=round(a["dti"], 6), dti_child=round(b["dti"], 6),
                         delta=round(b["dti"] - a["dti"], 6),
                         n_truth=int(a["n_truth"]), n_truth_child=int(b["n_truth"]),
                         coverage_parent=round(a["coverage"], 6), coverage_child=round(b["coverage"], 6))
    deltas = [out[k]["delta"] for k in out if k != "all"]
    out["sign_replication"] = dict(n_quadrants=len(deltas),
                                   n_positive=int(sum(d > 0 for d in deltas)),
                                   quadrant_range=[round(min(deltas), 6), round(max(deltas), 6)]
                                   if deltas else None)
    return out


def quadrant_masks(footprint: np.ndarray, n: int = 2) -> list[np.ndarray]:
    h, w = footprint.shape
    out = []
    for iy in range(n):
        for ix in range(n):
            m = np.zeros(footprint.shape, bool)
            m[slice(iy * h // n, (iy + 1) * h // n), slice(ix * w // n, (ix + 1) * w // n)] = True
            out.append(footprint & m)
    return out


def canary_panel(index: np.ndarray, footprint: np.ndarray, catalogue: np.ndarray,
                 surrogate: np.ndarray, bands: dict[str, np.ndarray], *, n: int = 400_000,
                 seed: int = 306) -> dict:
    """Single-feature AUCs on a random cell sample. AUC > 0.90 => stop and investigate."""
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(seed)
    flat = np.flatnonzero(footprint.ravel())
    take = rng.choice(flat, size=min(n, flat.size), replace=False)
    feats = {"relief_index": index}
    feats.update(bands)
    out = {}
    for target_name, target in (("catalogue", catalogue), ("sgmc_extra", surrogate)):
        y = np.asarray(target).ravel()[take].astype(int)
        per_feature = {}
        for name, arr in feats.items():
            x = np.asarray(arr).ravel()[take]
            if np.unique(x).size < 2:
                per_feature[name] = None
                continue
            per_feature[name] = round(float(roc_auc_score(y, x)), 4)
        out[target_name] = dict(n_sampled_cells=int(take.size), n_positive=int(y.sum()),
                                auc_per_feature=per_feature,
                                max_auc=max(v for v in per_feature.values() if v is not None),
                                threshold=0.90)
    return out


# ----------------------------------------------------------------------- main
def main() -> int:
    # Historical variant builders obey the same literal pre-placement stop.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="releases")
    ap.add_argument("--no-write", action="store_true", help="measure only; write no raster")
    ap.add_argument("--stamp", default=time.strftime("%Y%m%d"))
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
    base = read(PARENT_FILE.parent / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif")
    rebuild = rebuild_parent(g, base)
    if not (rebuild["content_identical"] and rebuild["byte_identical_sha"]):
        raise SystemExit(f"parent gate FAILED: {rebuild}")
    parent = read(PARENT_FILE) > 0
    if int(parent.sum()) != N_DOTS_R0 or sha256(PARENT_FILE) != PARENT_SHA:
        raise SystemExit("the parent on disk is not the parent this session was told to use")
    print(f"      R0 {int(parent.sum())} dots, rebuilt sha256 == published "
          f"({rebuild['rebuilt_sha256'][:8]})", flush=True)

    print("[3/8] relief regimes from the pinned detrended-elevation bands", flush=True)
    bands = {"det_elev": band(STACK, 12), "det_elev_slope": band(STACK, 19)}
    for name, arr in bands.items():          # sentinel scrub is load-bearing: assert it
        if float(np.abs(arr).max()) > 1e6:
            raise SystemExit(f"{name}: nodata sentinel survived the reader")
    support_band = band(STACK, 3)                      # tmi_hg, for reporting only
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
        census[name] = dict(area_px=int(m.sum()), area_share_of_footprint=round(float(m.sum()) / foot.sum(), 6),
                            dots=nd, dot_share_pct=round(100.0 * nd / int(parent.sum()), 4),
                            dots_per_Mpx=round(nd / max(m.sum(), 1) * 1e6, 1),
                            eligible_free_cells=int((eligible & m).sum()),
                            median_dot_catalogue_px=round(float(np.median(d_cat[parent & m])), 3) if nd else None)
    print("      " + json.dumps({k: v["dot_share_pct"] for k, v in census.items()}), flush=True)

    print("[4/8] building the dose ladder", flush=True)
    # percentile of the magnetic-gradient support band on the footprint, flattened so
    # it can be looked up by the flat cell indices the matcher returns. Reporting only:
    # it shows whether a variant quietly changed the evidence quality of the mass it moved.
    pct_flat = (np.searchsorted(np.sort(support_band[foot]), support_band)
                / float(int(foot.sum()))).ravel()
    built: dict[str, dict] = {}
    order: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for key, spec in DOSES.items():
        n_move = int(int(parent.sum()) * spec["frac"])
        src, dst, stats = RL.plan_moves(parent, lab, eligible, source=spec["source"],
                                       destination=spec["destination"], n_move=n_move,
                                       select=SELECTION)
        order[key] = (src, dst)
        dots = RL.apply_moves(parent, src, dst)
        diff = RL.relief_diff(parent, dots, lab, cat, n_move=n_move)
        if not diff["count_fixed"] or int(dots.sum()) != int(parent.sum()):
            raise SystemExit(f"{key}: count not fixed -- not a valid RELIEF variant")
        if diff["pct_changed"] < MIN_PCT_CHANGED or diff["pct_changed"] > MAX_PCT_CHANGED:
            raise SystemExit(f"{key}: {diff['pct_changed']}% changed is outside the 1-50% contract")
        if np.any(dots & cat):
            raise SystemExit(f"{key}: positive mass on the catalogue")
        if not diff["removed_from_regime"][RL.REGIMES[spec["source"]]] == n_move:
            raise SystemExit(f"{key}: deletions are not confined to the source regime")
        if not diff["added_in_regime"][RL.REGIMES[spec["destination"]]] == n_move:
            raise SystemExit(f"{key}: insertions are not confined to the destination regime")
        built[key] = dict(spec=spec, dots=dots, stats=stats, diff=diff,
                          support_pct=dict(removed=round(float(pct_flat[src].mean()), 4),
                                           added=round(float(pct_flat[dst].mean()), 4)))
        print(f"      {key}: {n_move} dots ({diff['pct_changed']}% of mass), "
              f"mean displacement {stats['displacement_px']['mean']} px", flush=True)

    # nesting proof for the two same-direction doses -- a ladder is only
    # interpretable if the small rung is a strict prefix of the big one
    s10, d10 = order["frontp10"]
    s15, d15 = order["frontp15"]
    nested = set(zip(s10.tolist(), d10.tolist())) <= set(zip(s15.tolist(), d15.tolist()))
    if not nested:
        raise SystemExit("front+10pct is not a prefix of front+15pct: the ladder is broken")

    print("[5/8] displacement-matched in-regime control (measured, never written)", flush=True)
    n_ctl = int(int(parent.sum()) * DOSES["frontp15"]["frac"])
    ctl_src, ctl_dst, ctl_stats = RL.plan_moves(parent, lab, eligible, source=1, destination=1,
                                                n_move=n_ctl, select="nearest-boundary")
    ctl_dots = RL.apply_moves(parent, ctl_src, ctl_dst)

    print("[6/8] report-only instruments (MODEL surrogate, PROXY, canaries)", flush=True)
    surrogate, sgmc_info = sgmc_surrogate(cat)
    quads = quadrant_masks(foot, 2)
    pred_parent = parent
    preds = {k: v["dots"] for k, v in built.items()}
    preds["CONTROL-inregime"] = ctl_dots
    model = {k: surrogate_delta(pred_parent, p, surrogate, foot, cat, quads) for k, p in preds.items()}
    proxy = {"R0": proxy_dti(parent.astype(np.float32), cat, foot)}
    proxy.update({k: proxy_dti(v["dots"].astype(np.float32), cat, foot) for k, v in built.items()})
    canaries = canary_panel(index, foot, cat, surrogate,
                            {"det_elev": bands["det_elev"], "det_elev_slope": bands["det_elev_slope"],
                             "tmi_hg": support_band})
    worst = max(canaries[t]["max_auc"] for t in canaries)
    if worst > 0.90:
        raise SystemExit(f"leakage canary: a single feature reaches AUC {worst} -- STOP and investigate")
    print(f"      surrogate delta: " + json.dumps({k: v["all"]["delta"] for k, v in model.items()}), flush=True)
    print(f"      proxy mean: " + json.dumps({k: v.get("mean") for k, v in proxy.items()}), flush=True)

    print("[7/8] gates and release artifacts", flush=True)
    out_dir = ROOT / args.out_dir
    existing_shas: set[str] = set()
    if (ROOT / "ledger/submissions.csv").exists():
        with open(ROOT / "ledger/submissions.csv", newline="") as fh:
            existing_shas |= {r["sha256"] for r in csv.DictReader(fh) if r.get("sha256")}
    existing_shas |= {sha256(p) for p in FLEET.glob("*.tif")}
    existing_shas |= {sha256(p) for p in (ROOT / "docs" / "downloads").glob("*.tif")}
    written, ledger_rows = [], []
    profile = serialization_profile(None)
    for key, card in built.items():
        dots = card["dots"]
        field = np.where(foot, dots.astype(np.float32), np.float32(0.0)).astype(np.float32)
        # the release name carries the file's own sha8, so probe the (filename
        # independent) bytes first, in a scratch dir -- never inside releases/
        import shutil as _sh
        import tempfile as _tf
        probe_dir = Path(_tf.mkdtemp())
        probe = probe_dir / "probe.tif"
        with rasterio.open(probe, "w", **profile) as dst_:
            dst_.write(field, 1)
        sha8 = sha256(probe)[:8]
        _sh.rmtree(probe_dir, ignore_errors=True)
        name = f"{PARENT_ID}-{AXIS}-{key}-{args.stamp}-{sha8}"
        zeros_path = out_dir / f"{name}-zeros.tif"
        nan_path = out_dir / f"{name}.tif"
        pred = model[key]["all"]
        rng = model[key]["sign_replication"]["quadrant_range"]
        predicted = (f"{pred['delta']:+.4f} (quadrant range {rng[0]:+.4f}..{rng[1]:+.4f}; "
                     f"{model[key]['sign_replication']['n_positive']}/{model[key]['sign_replication']['n_quadrants']} "
                     f"quadrants agree). MODEL: SGMC-extra surrogate, not a score.")
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
        # the two NaN-policy checks are the documented, accepted difference between the
        # twins (IR-86-PRUNE-07); every in-footprint check must still pass on the spec form
        nan_fail = [k2 for k2, ok in v_nan["checks"].items()
                    if not ok and k2 not in NAN_POLICY_CHECKS]
        if not v_zero["all_checks_passed"] or not rep_zero["ok"]:
            raise SystemExit(f"{key}: zeros twin failed the shared gates: {rep_zero['problems']} / "
                             f"{v_zero['failed_checks'] if 'failed_checks' in v_zero else ''}")
        if nan_fail:
            raise SystemExit(f"{key}: spec twin failed in-footprint checks: {nan_fail}")
        # re-read from disk: the dot set in the bytes must equal the in-memory one
        on_disk = read(zeros_path) > 0.5
        if int(on_disk.sum()) != int(dots.sum()) or bool((on_disk != dots).any()):
            raise SystemExit(f"{key}: re-read raster does not match the in-memory dot set")
        if z_sha in existing_shas or nan_sha in existing_shas:
            raise SystemExit(f"{key}: sha256 already present in the ledger/fleet (exact-hash dedupe)")
        existing_shas |= {z_sha, nan_sha}
        receipt = dict(
            id=name, parent=PARENT_ID, axis=AXIS, value=card["spec"]["value"], role="candidate",
            n_dots=int(dots.sum()), pct_changed=card["diff"]["pct_changed"],
            dot_digest=PRUNE.dot_digest(dots),
            regime_census=census, regime_cuts=cuts, relief_stats=card["stats"],
            diff=card["diff"], support_percentile=card["support_pct"],
            zeros=dict(file=zeros_path.name, sha256=z_sha, bytes=zeros_path.stat().st_size,
                       primary_for_upload=True, validator=v_zero, format_report_ok=rep_zero["ok"]),
            nan=dict(file=nan_path.name, mode="nan", sha256=nan_sha, bytes=nan_path.stat().st_size,
                     in_footprint_checks_pass=not nan_fail, failed_checks=nan_fail,
                     policy_checks_excluded=sorted(NAN_POLICY_CHECKS & {k for k, v in v_nan["checks"].items() if not v}),
                     policy_note="brief v2 §6 form; repo policy prefers -zeros (IR-86-PRUNE-07)"),
            submission_name=name[:140], note=note,
            predicted_live_change=predicted, evidence_class="MODEL",
            approved_for_weekly_slot=False, submission_slots_used=0,
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
            predicted_change=predicted, source_url="", receipt_score="", receipt_date="",
            dot_digest=receipt["dot_digest"], files=[zeros_path.name, nan_path.name],
            gate_all_pass=True,
            proxy=dict(value=proxy[key].get("mean"), ci95=proxy[key].get("ci95"),
                       class_="PROXY", note=proxy[key].get("contamination")),
        ))
        print(f"      {name}: gates pass, {z_sha[:8]} (zeros) / {nan_sha[:8]} (nan)", flush=True)

    print("[8/8] evidence, run card, ledger", flush=True)
    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        elapsed_seconds=round(time.time() - t0, 1),
        axis=AXIS, axis_assignment=AXIS_ASSIGNMENT,
        parent=dict(id=PARENT_ID, file=PARENT_FILE.name, sha256=PARENT_SHA,
                    n_dots=int(parent.sum()), dot_digest=PRUNE.dot_digest(parent)),
        parent_rebuild=rebuild, input_pins=pins, manifest_pins=manifest_pins,
        regime_cuts=cuts, regime_census=census, sgmc_info=sgmc_info,
        variants={k: dict(value=v["spec"]["value"], hypothesis=v["spec"]["hypothesis"],
                          relief_stats=v["stats"], diff=v["diff"],
                          support_percentile=v["support_pct"],
                          predicted_live_change=model[k], proxy=proxy[k]) for k, v in built.items()},
        ladder_nesting=dict(front5_is_prefix_of_front10=bool(nested)),
        control=dict(role="displacement-matched, same regime, never written as a raster",
                     relief_stats=ctl_stats, diff=RL.relief_diff(parent, ctl_dots, lab, cat, n_move=n_ctl),
                     predicted_live_change=model["CONTROL-inregime"]["all"]),
        instruments=dict(surrogate_class="MODEL", proxy_class="PROXY", canaries=canaries,
                         worst_single_feature_auc=round(worst, 4),
                         note=("both instruments are REPORT ONLY (brief §6); the proxy is at its floor "
                               "for catalogue-avoiding fields (IR-86-PRUNE-03)")),
        gates=dict(format="shared validator + shared format_report on the written bytes, both twins",
                   zero_catalogue_mass="asserted in memory and after re-read",
                   count_fixed="asserted for every variant",
                   pct_changed_contract=f"{MIN_PCT_CHANGED}-{MAX_PCT_CHANGED}% enforced",
                   sha_novel="checked against every sha256 in ledger/submissions.csv, data/scored_fleet and docs/downloads",
                   parent_diff="recorded per variant", reread_from_disk="yes",
                   uniqueness_thresholds="NOT applied, by brief v2 §6 (IR-86-PRUNE-01)"),
        written=[w["id"] for w in written], no_slot_authorized=True,
        not_a_score="Every number here is a MODEL projection or a PROXY measurement. No submission was made.",
    )
    if not args.no_write:
        EVIDENCE.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        VARIANTS_JSON.write_text(json.dumps(_merge_variants(
            [dict(r, gate_all_pass=True) for r in ledger_rows]), indent=2) + "\n")
        subprocess.run([sys.executable, str(ROOT / "scripts/build_ledger.py")], check=True, cwd=ROOT)
        print(f"      wrote {EVIDENCE.relative_to(ROOT)} and {len(ledger_rows)} ledger rows", flush=True)
    else:
        print(json.dumps({k: v["predicted_live_change"]["all"] for k, v in built.items()}, indent=2))
    return 0


def _merge_variants(rows: list[dict]) -> list[dict]:
    """Append this session's rows to ``ledger/variants.json``, replacing same-id rows."""
    entries = json.loads(VARIANTS_JSON.read_text()) if VARIANTS_JSON.is_file() else []
    by_id = {e.get("id"): i for i, e in enumerate(entries)}
    for r in rows:
        if r["id"] in by_id:
            entries[by_id[r["id"]]] = r
        else:
            entries.append(r)
    return entries


if __name__ == "__main__":
    raise SystemExit(main())
