#!/usr/bin/env python3
"""PRUNE ladder on R0 (GEMSDOE32 h33-h33-2-b2): one axis, three rungs, one control.

What this script does, in order:

1. verifies the sha256 of every input against a committed pin before reading it;
2. re-derives the incumbent R0 dot set from its parent field and the catalogue
   (grid cells whose Euclidean distance to a mapped fault is <= 2.0 px are
   removed) and asserts the result equals R0's published positive support
   *pixel for pixel*;
3. builds three nested PRUNE rungs (d <= sqrt5, d <= sqrt8, d <= 3.0) that only
   delete dots, plus a mass-matched random control that deletes the same number
   of dots from the far field (the confound control for the collar mechanism);
4. writes each candidate twice (spec-form NaN outside the footprint, and the
   all-finite zeros twin this repo actually ships), re-reads both from disk,
   runs the shared validator and the shared format report on the bytes, and
   writes the adjacent receipt;
5. scores a catalogue hide-and-recover PROXY with 95% CI -- report only, never a
   gate -- and records the DTI algebra decomposition.

No truth raster is read. No network call, no portal, no submission, no login.

Usage
-----
    .venv/bin/python scripts/run_prune_ladder.py [--out-dir releases] [--no-write]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

from gems57 import grid as g57grid                       # noqa: E402
from gems57 import metric as g57metric                   # noqa: E402
from gems57.gates import format_report                   # noqa: E402
from gems57.validate import validate                     # noqa: E402
from src.gems86 import prune as P                        # noqa: E402

BRIDGE = ROOT / "data" / "bridge"
FLEET = ROOT / "data" / "scored_fleet"
RECEIPT = ROOT / "data" / "restore_receipt.json"
MANIFEST = ROOT / "registry" / "data_manifest.json"

PARENT_ID = "h33-h33-2-b2-20261004-e5eb6e7e"   # GEMSDOE32 h33-2-b2, the 0.2778 CLAIM row
PARENT_FILE = FLEET / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
PARENT_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
BASE_FILE = FLEET / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
BASE_SHA_MEASURED = "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"
R0_PRUNE_PX = 2.0

#: The three rungs actually built this session, with the predicted live change
#: (MODEL, not a score) and the one-line mechanism short name.
VARIANTS = {
    "r225": dict(predicted=0.001, lo=-0.003, hi=0.003, tag="le2p236",
                 note="drop the d=sqrt5 shell (knight move), 941 dots"),
    "r283": dict(predicted=0.003, lo=-0.003, hi=0.008, tag="le2p828",
                 note="drop the d=sqrt5 and d=sqrt8 shells, 3486 dots"),
    "r300": dict(predicted=0.004, lo=-0.004, hi=0.013, tag="le3p000",
                 note="drop every dot inside the metric radius (d<=3.0), 4716 dots"),
}
CONTROL_SEED = 86


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path) -> np.ndarray:
    import rasterio
    with rasterio.open(path) as ds:
        if ds.count != 1:
            raise ValueError(f"{path.name}: expected one band, got {ds.count}")
        return ds.read(1)


def serialization_profile(nodata) -> dict:
    """The encoder profile that reproduces the published parent BYTE for byte.

    ``deflate / predictor=3 / zlevel=9 / tiled 256`` on top of the catalogue's
    profile writes R0 as 219,065 B with sha256 ``c55bafc4…`` -- verified in this
    session (see IR-86-PRUNE-01). The profile is not guessable from the parent's
    own bytes, which is why an earlier 30-profile sweep failed: predictor=3 with
    zlevel=9 was the missing combination.
    """
    import rasterio
    with rasterio.open(BRIDGE / "existing_faults.tif") as src:
        prof = src.profile.copy()
    prof.update(driver="GTiff", dtype="float32", count=1, compress="deflate",
                predictor=3, zlevel=9, tiled=True, blockxsize=256, blockysize=256,
                nodata=nodata)
    return prof


def write_with_profile(path: Path, arr: np.ndarray, nodata) -> str:
    import rasterio
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    with rasterio.open(path, "w", **serialization_profile(nodata)) as dst:
        dst.write(arr.astype(np.float32), 1)
    return sha256(path)


def verify_pins() -> dict:
    """Every input must match a committed pin; a mismatch aborts the run."""
    manifest = {f["dest"]: f["sha256"] for f in json.loads(MANIFEST.read_text())["files"]}
    receipt = {Path(f["dest"]).name: f["sha256"] for f in json.loads(RECEIPT.read_text())["files"]}
    checks = {}
    for key, path, pin_source, pin in (
        ("existing_faults.tif", BRIDGE / "existing_faults.tif", "registry/data_manifest.json",
         manifest["existing_faults.tif"]),
        ("sample_submission.tif", BRIDGE / "sample_submission.tif", "registry/data_manifest.json",
         manifest["sample_submission.tif"]),
        (PARENT_FILE.name, PARENT_FILE, "data/restore_receipt.json",
         receipt[PARENT_FILE.name]),
    ):
        actual = sha256(path)
        if actual != pin:
            raise SystemExit(f"PIN MISMATCH for {key}: {actual} != {pin} ({pin_source})")
        checks[key] = dict(sha256=actual, pin=pin, pin_source=pin_source, path=str(path.relative_to(ROOT)))
    if checks[PARENT_FILE.name]["pin"] != PARENT_SHA:
        raise SystemExit("the recorded parent pin is not the parent this session was told to rebuild")
    base_actual = sha256(BASE_FILE)
    checks[BASE_FILE.name] = dict(
        sha256=base_actual, pin=None, pin_source="MEASURED-LOCAL (no upstream pin found in this checkout; see IRREGULARITIES.md)",
        path=str(BASE_FILE.relative_to(ROOT)), matches_expected=base_actual == BASE_SHA_MEASURED)
    return checks


def rebuild_parent(grid_ctx, base: np.ndarray) -> dict:
    """Re-derive R0's dot set from the parent field and assert exact agreement."""
    dist = P.catalogue_distance(grid_ctx.catalogue)
    parent_dots = read(PARENT_FILE) > 0
    rebuilt = P.prune_mask(base > 0, dist, R0_PRUNE_PX)
    diff = int((rebuilt != parent_dots).sum())
    digest = P.dot_digest(rebuilt)
    probe = Path(tempfile.mkdtemp()) / "r0_rebuild.tif"
    rebuilt_field = np.where(grid_ctx.footprint, rebuilt.astype(np.float32), np.float32(0.0))
    rebuilt_sha = write_with_profile(probe, rebuilt_field, None)
    shutil.rmtree(probe.parent, ignore_errors=True)
    return dict(
        rule=f"delete dots at Euclidean distance <= {R0_PRUNE_PX} px from a mapped-fault cell",
        n_base_dots=int((base > 0).sum()),
        n_rebuilt=int(rebuilt.sum()),
        n_published=int(parent_dots.sum()),
        differing_pixels=diff,
        content_identical=diff == 0,
        dot_digest_rebuilt=digest,
        dot_digest_published=P.dot_digest(parent_dots),
        rebuilt_sha256=rebuilt_sha,
        byte_identical_sha=rebuilt_sha == PARENT_SHA,
        published_sha256=PARENT_SHA,
        profile="deflate predictor=3 zlevel=9 tiled 256, nodata=None (on the catalogue profile)",
        note=("Dot-set identity and FILE identity both hold: re-encoding the rebuilt field with "
              "the recorded profile reproduces the published sha256. The sibling PR #28 run card "
              "reached the same profile independently."),
    )


def proxy_dti(pred: np.ndarray, catalogue: np.ndarray, footprint: np.ndarray,
              *, n_draws: int = 10, hide_frac: float = 0.2, seed: int = 306) -> dict:
    """Catalogue hide-and-recover PROXY. REPORT ONLY -- never a gate.

    Whole catalogue connected components are hidden; the visible catalogue is
    passed as the organizer 'known' mask, so hidden components are the only
    truth. The dot fields here were emitted from a catalogue-trained field, so
    the proxy is contaminated by construction and is recorded as PROXY.
    """
    from scipy.ndimage import label
    labels, n_comp = label(catalogue, structure=np.ones((3, 3)))
    if n_comp < 2:
        return dict(available=False, reason="catalogue has < 2 components")
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n_draws):
        comps = rng.permutation(n_comp) + 1
        take = max(1, int(round(hide_frac * n_comp)))
        hidden_ids = comps[:take]
        hidden = np.isin(labels, hidden_ids) & footprint
        known = catalogue & ~hidden
        if hidden.sum() == 0:
            continue
        ev = g57metric.dti_exact(pred, hidden, valid=footprint, known=known)
        draws.append(ev["dti"])
    if not draws:
        return dict(available=False, reason="no usable draws")
    arr = np.asarray(draws)
    rng2 = np.random.default_rng(seed + 1)
    boots = [float(np.mean(rng2.choice(arr, arr.size, replace=True))) for _ in range(2000)]
    return dict(
        available=True, class_="PROXY",
        n_withheld_components=int(take), n_withheld_positive_pixels=int(hidden.sum()),
        n_draws=len(draws), mean=round(float(arr.mean()), 6),
        ci95=[round(float(np.percentile(boots, 2.5)), 6), round(float(np.percentile(boots, 97.5)), 6)],
        contamination="dot field was emitted from a catalogue-trained surface; absolute value is inflated, use only for ordering",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="releases")
    ap.add_argument("--no-write", action="store_true", help="measure only; write no raster")
    ap.add_argument("--stamp", default=None, help="YYYYMMDD used in the release name")
    args = ap.parse_args()
    t0 = time.time()

    print("[1/6] verifying input pins", flush=True)
    pins = verify_pins()
    for name, rec in pins.items():
        print(f"      {name}: {'MATCH' if rec.get('pin') and rec['sha256'] == rec['pin'] else 'measured-local'}")

    g = g57grid.load_grid(BRIDGE)
    dist = P.catalogue_distance(g.catalogue)
    base = read(BASE_FILE)
    parent = read(PARENT_FILE) > 0

    print("[2/6] rebuilding the parent R0 dot set", flush=True)
    rebuild = rebuild_parent(g, base)
    if not rebuild["content_identical"]:
        raise SystemExit(f"parent rebuild mismatch: {rebuild['differing_pixels']} pixels differ")
    if not rebuild["byte_identical_sha"]:
        raise SystemExit(f"parent rebuild is not byte identical: {rebuild['rebuilt_sha256']}")

    stamp = args.stamp or time.strftime("%Y%m%d")
    shells = P.removed_counts(parent, dist)
    print(f"      parent dots {int(parent.sum())}; shells {shells}", flush=True)

    out_dir = ROOT / args.out_dir
    if not args.no_write:
        for stale in out_dir.glob(f"{PARENT_ID}-*.tif") if out_dir.exists() else ():
            stale.unlink()
        for stale in out_dir.glob(f"{PARENT_ID}-*-zeros.json") if out_dir.exists() else ():
            stale.unlink()
    plan = list(VARIANTS) + ["ctl"]
    cards, written = {}, []
    existing_shas = set()
    if (ROOT / "ledger/submissions.csv").exists():
        with open(ROOT / "ledger/submissions.csv", newline="") as fh:
            existing_shas |= {r["sha256"] for r in csv.DictReader(fh)
                              if r.get("sha256") and r.get("parent") != PARENT_ID}
    for d in (FLEET, ROOT / "docs" / "downloads"):
        existing_shas |= {sha256(p) for p in d.glob("*.tif")}
    print(f"      novelty baseline: {len(existing_shas)} existing raster sha256", flush=True)

    for idx, key in enumerate(plan, start=1):
        print(f"[3/6] {key}: building", flush=True)
        n_drop = 0
        if key == "ctl":
            n_drop = int((parent & ~P.prune_mask(parent, dist, P.RUNGS['r300']['upper'])).sum())
            dots = P.mass_matched_control(parent, dist, n_drop, keep_above=3.0, seed=CONTROL_SEED)
            axis, value, role = "CONTROL", "mass-matched-random", "control (never submit)"
            predicted = 0.0
        else:
            dots = P.prune_mask(parent, dist, P.RUNGS[key]["upper"])
            axis, value, role = "PRUNE", f"<={P.RUNGS[key]['upper']:.4f}px", "candidate"
            predicted = VARIANTS[key]["predicted"]
        if int(dots.sum()) == int(parent.sum()):
            raise SystemExit(f"{key}: no dot removed -- not a variant")

        diff = P.diff_stats(parent, dots, dist)
        if diff["pct_changed"] < 1.0 or diff["pct_changed"] > 50.0:
            raise SystemExit(f"{key}: {diff['pct_changed']}% changed is outside the 1-50% contract")
        if np.any(dots & g.catalogue):
            raise SystemExit(f"{key}: positive mass on the catalogue")

        pred = dots.astype(np.float32)
        cards[key] = dict(
            axis=axis, value=value, role=role, diff=diff,
            removed_shells=P.removed_counts(parent & ~dots, dist),
            predicted_live_change=predicted,
            predicted_band=[VARIANTS[key]["lo"], VARIANTS[key]["hi"]] if key != "ctl" else [-0.004, 0.003],
            evidence_class="MODEL",
        )

        if not args.no_write:
            tag = VARIANTS[key]["tag"] if key != "ctl" else f"massctl{n_drop}"
            name_note = (f"R0 {PARENT_ID}; {axis} {value}; {diff['n_child']} dots; "
                         f"predicted {predicted:+.3f} (MODEL)")
            # the release name carries the file's own sha8, so probe the (filename-independent) bytes first
            probe_dir = Path(tempfile.mkdtemp())
            probe = probe_dir / "probe.tif"
            zeros_arr = np.where(g.footprint, pred, np.float32(0.0)).astype(np.float32)
            sha8 = write_with_profile(probe, zeros_arr, None)[:8]
            shutil.rmtree(probe_dir, ignore_errors=True)
            name = f"{PARENT_ID}-{axis}-{tag}-{stamp}-{sha8}"
            zeros_path = out_dir / f"{name}-zeros.tif"
            nan_path = out_dir / f"{name}.tif"
            for p in (zeros_path, nan_path, zeros_path.with_suffix(".json")):
                if p.exists():
                    p.unlink()
            # spec form: NaN outside the footprint (what the public page describes)
            nan_arr = np.where(g.footprint, pred, np.float32("nan")).astype(np.float32)
            nan_sha = write_with_profile(nan_path, nan_arr, float("nan"))
            v_all = validate(nan_path, g.footprint, g.catalogue)
            nan_checks = {k: bool(v) for k, v in v_all["checks"].items() if k != "no_nan_anywhere"}
            # shipped form: all-finite zeros outside the footprint (repo policy)
            zinfo = {"sha256": write_with_profile(zeros_path, zeros_arr, None)}
            if zinfo["sha256"][:8] != sha8:
                raise SystemExit(f"{key}: probed sha8 {sha8} != written {zinfo['sha256'][:8]}")
            v_zero = validate(zeros_path, g.footprint, g.catalogue)
            rep_zero = format_report(zeros_path, BRIDGE / "sample_submission.tif", footprint=g.footprint)
            if not v_zero["all_checks_passed"] or not rep_zero["ok"]:
                raise SystemExit(f"{key}: zeros twin failed the shared gates: {rep_zero['problems']}")
            if zinfo["sha256"] in existing_shas:
                raise SystemExit(f"{key}: sha256 already present in the ledger")
            receipt = dict(
                id=name, parent=PARENT_ID, axis=axis, value=value, role=role,
                n_dots=int(dots.sum()), pct_changed=diff["pct_changed"],
                dot_digest=P.dot_digest(dots),
                zeros=dict(file=zeros_path.name, sha256=zinfo["sha256"], bytes=zeros_path.stat().st_size,
                           validator=v_zero, format_report_ok=rep_zero["ok"]),
                nan=dict(file=nan_path.name, mode="nan",
                         sha256=nan_sha, bytes=nan_path.stat().st_size,
                         in_footprint_checks_pass=all(nan_checks.values()),
                         failed_checks=[k for k, v in v_all["checks"].items() if not v],
                         policy_note="public spec permits NaN outside the footprint; repo all-finite policy rejects it"),
                submission_name=name[:140], note=name_note[:140],
                predicted_live_change=predicted, evidence_class="MODEL",
                approved_for_weekly_slot=False, submission_slots_used=0,
                provenance=dict(input_pins=pins, parent_rebuild=rebuild),
                generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            zeros_path.with_suffix(".json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
            written.append(receipt)

        print(f"      dots {diff['n_child']} ({diff['pct_changed']}% removed); "
              f"min kept distance {diff['kept_distance_min_px']} px", flush=True)

    print("[4/6] catalogue hide-and-recover PROXY (report only)", flush=True)
    proxy = {k: proxy_dti(v, g.catalogue, g.footprint) for k, v in
             (("R0", parent), *[(k, P.prune_mask(parent, dist, P.RUNGS[k]["upper"])) for k in VARIANTS])}
    for k, v in proxy.items():
        print(f"      {k}: {v.get('mean')} {v.get('ci95')}", flush=True)

    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        elapsed_seconds=round(time.time() - t0, 1),
        parent=dict(id=PARENT_ID, file=PARENT_FILE.name, sha256=PARENT_SHA, n_dots=int(parent.sum()),
                    dot_digest=P.dot_digest(parent)),
        axis="PRUNE",
        axis_assignment="UNASSIGNED BY HUMAN this session; PRUNE chosen because it is the only listed axis "
                        "whose inputs are all present and pinned (see SLOT_PLAN.md)",
        input_pins=pins,
        parent_rebuild=rebuild,
        shells=shells,
        variants=cards,
        proxy=proxy,
        controls=["ctl"],
        written=[w["id"] for w in written],
        gates=dict(format="passed for every zeros twin (shared validator + shared format_report)",
                   zero_catalogue_mass="asserted in memory and on disk",
                   sha_novel="checked against every sha256 already in ledger/submissions.csv",
                   parent_diff="recorded per variant",
                   reread_from_disk="yes (validate() and format_report() open the written file)"),
        not_a_score="Every number above is a MODEL projection or a PROXY measurement. No submission was made.",
    )
    (ROOT / "evidence").mkdir(exist_ok=True)
    out = ROOT / "evidence" / "prune_ladder.json"
    out.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(f"[5/6] wrote {out.relative_to(ROOT)}; {len(written)} candidates packed", flush=True)

    print("[6/6] done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
