#!/usr/bin/env python3
"""CONCENTRATION surface-extension arms on the byte-exact R0 parent (2026-10-23).

The session's single axis is ``CONCENTRATION``.  Nothing else about R0 changes:
count stays 37,654, every retained dot keeps its geometry, newly emitted mass
must be strictly ``> 3.0 px`` from the visible catalogue, and the parent's
``>= sqrt(8) px`` inter-dot spacing floor is never tightened.

Three files, one change each:

* ``b5km-surfext-down10``  -- moves 3,765 dots (10.0%, 20.00% changed) out of the
  densest occupied 1 km blocks, lowest unique-kernel-credit dot first, onto legal
  cells of ``H19-4 | H16-1`` that are not on ``H19-5``;
* ``b5km-surfext-down15``  -- the nested 2x dose, 5,648 dots (15.0%, 30.00% changed);
* ``b5km-surfext-down10-randdst`` -- matched null control: identical sources and
  dose, destinations drawn uniformly from legal cells that are *off* the ancestor
  union inside the same 1 km blocks.  Measured, never promoted.

Order of operations: verify every pin (bridge, parent, five manifest inputs);
reproduce R0's mask *and file SHA-256*; reproduce the merged
``b5km-cvband-down4`` file SHA-256 as an input-integrity check; build; run the
leakage canary and the report-only SGMC quadrant / fold-fair PROXY instruments;
write both encodings; re-read them and run every MUST gate; emit receipts and
canonical ledger-source rows.

No truth raster is read, no network call is made, nothing is submitted.

Usage::

    .venv/bin/python scripts/run_concentration_surfext.py [--no-write] [--stamp 20261023]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
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
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "scripts", ROOT / "vendor", ROOT / "vendor" / "template66"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gems57 import evaluate_holdout, grid as g57grid, metric as g57metric  # noqa: E402
from gems57.gates import format_report  # noqa: E402
from gems57.validate import validate  # noqa: E402
from gems86 import concentration_5km as C5  # noqa: E402
from gems86 import concentration_surfext as SE  # noqa: E402
from gems86 import instrument as g86inst  # noqa: E402
from gems86 import mass_econ, prune as P  # noqa: E402
from run_prune_ladder import (  # noqa: E402
    BASE_FILE,
    PARENT_FILE,
    PARENT_SHA,
    read,
    rebuild_parent,
    serialization_profile,
    sha256,
    write_with_profile,
)

SESSION = "concentration_surfext"
DATE_TAG = "20261023"
AXIS = "CONCENTRATION"
PARENT_ID = "h33-h33-2-b2-20261004-e5eb6e7e"
N_DOTS_R0 = 37654
MERGED_DOWN4_SHA = "8aab97b65f70ba6c5dc4e3f0e73d95cbcb602da0d110c46dd0cf6a3a2e55d863"
MERGED_DOWN4_ID = "h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown4-20261023-8aab97b6"
SEED = 20261023
BRIDGE = ROOT / "data" / "bridge"
FLEET = ROOT / "data" / "scored_fleet"
CACHE_SCORED = ROOT / ".cache" / "gems_data" / "scored"
CACHE_EXT = ROOT / ".cache" / "gems_data" / "external"
EVIDENCE_JSON = ROOT / "evidence" / f"{SESSION}_axis_{DATE_TAG}.json"
VARIANTS_JSON = ROOT / "ledger" / f"variants_{SESSION}.json"
MIN_PCT_CHANGED, MAX_PCT_CHANGED = 1.0, 50.0
NAN_POLICY_CHECKS = {"no_nan_anywhere", "outside_footprint_zero"}

PINNED_INPUTS: dict[str, Path] = {
    "scored_h19_5": CACHE_SCORED / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
    "scored_h19_4": CACHE_SCORED / "gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif",
    "scored_h16_1": CACHE_SCORED / "gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif",
    "scored_d28_unscored": CACHE_SCORED / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "ext_derived_sgmc_faults_100m_u8": CACHE_EXT / "derived_sgmc_faults_100m_u8.tif",
}

SPECS = {
    "b5km-surfext-down10": dict(value="b5km-surfext-down10", n_move=3765, role="candidate",
                                slug="surfext10", seed=None),
    "b5km-surfext-down15": dict(value="b5km-surfext-down15", n_move=5648, role="candidate",
                                slug="surfext15", seed=None),
    "b5km-surfext-down10-randdst": dict(value="b5km-surfext-down10-randdst", n_move=3765,
                                        role="control", slug="surfext10ctl", seed=86),
}


def git_sha() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                          text=True, check=False).stdout.strip()


def verify_pins() -> dict:
    files = json.loads((ROOT / "registry/data_manifest.json").read_text())["files"]
    manifest = {f["dest"]: f for f in files}
    by_id = {f["id"]: f for f in files}
    out = {}
    for key, path, entry in (
        ("existing_faults.tif", BRIDGE / "existing_faults.tif", manifest["existing_faults.tif"]),
        ("sample_submission.tif", BRIDGE / "sample_submission.tif", manifest["sample_submission.tif"]),
        ("parent", PARENT_FILE, by_id["scored_h33_2_b2_zeros"]),
    ):
        got = sha256(path)
        if got != entry["sha256"]:
            raise SystemExit(f"PIN MISMATCH {key}: {got} != {entry['sha256']}")
        out[key] = dict(path=str(path.relative_to(ROOT)), sha256=got, pin_source="registry/data_manifest.json")
    if out["parent"]["sha256"] != PARENT_SHA:
        raise SystemExit("parent pin is not the R0 this session must rebuild")
    out["base"] = dict(path=str(BASE_FILE.relative_to(ROOT)), sha256=sha256(BASE_FILE),
                       pin_source="MEASURED-LOCAL (see IRREGULARITIES.md)")
    for ident, path in PINNED_INPUTS.items():
        entry = by_id[ident]
        if not path.is_file():
            raise SystemExit(f"missing pinned input {ident} at {path}; run scripts/restore_axis_inputs.py")
        got = sha256(path)
        if got != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise SystemExit(f"PIN MISMATCH {ident}: {got} != {entry['sha256']}")
        out[ident] = dict(path=str(path.relative_to(ROOT)), sha256=got, bytes=entry["bytes"],
                          pin_source="registry/data_manifest.json",
                          provenance=entry.get("provenance", ""))
    return out


def sgmc_surrogate(catalogue: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, dict]:
    with rasterio.open(PINNED_INPUTS["ext_derived_sgmc_faults_100m_u8"]) as src:
        a = src.read(1)
    sg = np.isfinite(a) & (a > 0) & footprint
    extra = sg & ~catalogue
    return extra, dict(
        sgmc_pixels_in_footprint=int(sg.sum()),
        catalogue_pixels_in_footprint=int((catalogue & footprint).sum()),
        sgmc_pixels_not_in_catalogue=int(extra.sum()),
        provenance="USGS State Geologic Map Compilation (DOI 10.3133/ds1052), off-catalogue fault pixels",
        evidence_class="MODEL",
        note="Count fixed across every arm (n=37,654), so IR-86-MASS-03 mass monotonicity cancels.",
    )


def clearance_confound(parent, child, edt_cat, edt_sgmc, union, edt_union) -> dict:
    """Is an arm's MODEL gain just 'mass farther from the catalogue'?

    The SGMC surrogate's truth is ``SGMC minus catalogue``: pixels on the mapped
    catalogue and its 2-3 px collar can never be SGMC truth, while the organiser
    says new truth *can* lie within 300 m of a known trace.  Any arm that moves
    mass outward therefore gains on this instrument for a reason that has nothing
    to do with fault-lineament knowledge.  This function prices that: the added
    mass's mean distance to SGMC-extra truth and to the catalogue, against the
    removed mass's, with a matched random-destination null.
    """
    added, removed = child & ~parent, parent & ~child
    out = {"added": {}, "removed": {}}
    for name, mask in (("added", added), ("removed", removed)):
        if not mask.any():
            continue
        out[name] = dict(
            n=int(mask.sum()),
            mean_dist_to_catalogue_px=round(float(edt_cat[mask].mean()), 3),
            median_dist_to_catalogue_px=round(float(np.median(edt_cat[mask])), 3),
            mean_dist_to_sgmc_extra_px=round(float(edt_sgmc[mask].mean()), 3),
            median_dist_to_sgmc_extra_px=round(float(np.median(edt_sgmc[mask])), 3),
            mean_dist_to_ancestor_union_px=round(float(edt_union[mask].mean()), 3),
        )
    out["reading"] = ("A CONCENTRATION arm that moves mass outward raises every 'distance to "
                      "catalogue' column and lowers nothing; compare an arm with its matched "
                      "random-destination control before attributing any MODEL delta to lineaments.")
    return out


def live_credit_budget(n_dots: int, claimed_dti: float = 0.2778, truth_px: int = 40000,
                       mean_self_credit: float = 0.30, alpha: float = 0.2,
                       beta: float = 0.8) -> dict:
    """How much new truth credit +0.01 of live DTI would require (MODEL projection).

    Uses the official algebra ``DTI = T / (alpha*T + alpha*(n - M) + beta*|G|)``
    with ``M = n * k`` for the binary-dot case.  ``truth_px`` is the one free
    parameter and is *assumed*, not measured (the organiser does not disclose
    ``|G|``); the sensitivity band is reported.
    """
    rows = {}
    for g_px in (truth_px // 2, truth_px, truth_px * 2):
        M = n_dots * mean_self_credit
        fp = alpha * (n_dots - M)
        T = claimed_dti * (beta * g_px + fp) / (1.0 - alpha * claimed_dti)
        D = alpha * T + fp + beta * g_px
        dT_per_001 = 0.01 * D * D / max(D - alpha * T, 1e-9)
        rows[str(g_px)] = dict(
            implied_truth_px=g_px, implied_T=round(T, 1), denominator=round(D, 1),
            mean_credit_per_truth_px=round(T / g_px, 4),
            credit_units_needed_for_plus_0p01=round(dT_per_001, 1),
            km_of_new_fault_trace_hit_squarely=round(dT_per_001 / 10.0, 1),
        )
    return dict(
        model="DTI = T/(alpha*T + alpha*(n-M) + beta*|G|), binary unit dots",
        evidence_class="MODEL", assumed_mean_self_credit=mean_self_credit,
        note=("The rearrangement axes move which ~1-4k dots exist, not how much new fault "
              "line the field touches; the credit they can buy is bounded by the kernel "
              "overlap they change. Read this against the measured |delta| <= 0.008."),
        rows=rows,
    )


def quadrant_masks(footprint: np.ndarray) -> list[np.ndarray]:
    h, w = footprint.shape
    ys = np.arange(h)[:, None]
    xs = np.arange(w)[None, :]
    return [
        footprint & (ys < h // 2) & (xs < w // 2),
        footprint & (ys < h // 2) & (xs >= w // 2),
        footprint & (ys >= h // 2) & (xs < w // 2),
        footprint & (ys >= h // 2) & (xs >= w // 2),
    ]


def shift_bool(mask: np.ndarray, dy: int, dx: int) -> np.ndarray:
    if dy == 0 and dx == 0:
        return mask
    h, w = mask.shape
    out = np.zeros_like(mask, dtype=bool)
    sy0, sy1 = max(0, -dy), min(h, h - dy)
    sx0, sx1 = max(0, -dx), min(w, w - dx)
    out[sy0 + dy:sy1 + dy, sx0 + dx:sx1 + dx] = mask[sy0:sy1, sx0:sx1]
    return out


def evaluate_surrogate(parent, child, surrogate, footprint, catalogue, quads) -> dict:
    regions = {"all": footprint}
    regions.update({f"q{i}": q for i, q in enumerate(quads, start=1)})
    out: dict = {}
    for name, valid in regions.items():
        a = g57metric.dti_binary(parent, surrogate, valid=valid, known=catalogue)
        b = g57metric.dti_binary(child, surrogate, valid=valid, known=catalogue)
        out[name] = dict(dti_parent=round(a["dti"], 6), dti_child=round(b["dti"], 6),
                         delta=round(b["dti"] - a["dti"], 6), n_truth=int(a["n_truth"]),
                         coverage_parent=round(a["coverage"], 6), coverage_child=round(b["coverage"], 6),
                         tp_child=round(b["tp"], 3), fp_child=round(b["fp"], 3))
    q = [out[f"q{i}"]["delta"] for i in range(1, 5)]
    out["sign_replication"] = dict(n_quadrants=4, n_positive=int(sum(d > 0 for d in q)),
                                   n_negative=int(sum(d < 0 for d in q)),
                                   quadrant_range=[round(min(q), 6), round(max(q), 6)])
    jit = []
    for dy, dx in ((0, 0), (-6, 0), (6, 0), (0, -6), (0, 6)):
        sg = shift_bool(surrogate, dy, dx) & footprint & ~catalogue
        aj = g57metric.dti_binary(parent, sg, valid=footprint, known=catalogue)
        bj = g57metric.dti_binary(child, sg, valid=footprint, known=catalogue)
        jit.append(round(bj["dti"] - aj["dti"], 6))
    out["jitter_6px_ensemble"] = dict(shifts_px=[[0, 0], [-6, 0], [6, 0], [0, -6], [0, 6]], deltas=jit,
                                      mean_delta=round(float(np.mean(jit)), 6),
                                      min_delta=round(min(jit), 6), max_delta=round(max(jit), 6))
    return out


def leakage_canary(features: dict[str, np.ndarray], footprint: np.ndarray, catalogue: np.ndarray,
                   surrogate: np.ndarray, edt_cat: np.ndarray) -> dict:
    """Single-feature AUC canary; > 0.90 means stop and investigate."""
    targets = {
        "catalogue_in_footprint": (footprint, catalogue & footprint),
        "sgmc_beyond_3px_collar": (footprint & (edt_cat > 3.0), surrogate & (edt_cat > 3.0)),
    }
    report: dict = {}
    for tname, (dom, pos) in targets.items():
        y = pos[dom].astype(np.int8)
        per_feat = {}
        for fname, arr in features.items():
            x = np.asarray(arr, dtype=np.float64)[dom]
            fin = np.isfinite(x)
            if int(fin.sum()) < 100 or y[fin].min() == y[fin].max():
                continue
            auc = float(roc_auc_score(y[fin], x[fin]))
            per_feat[fname] = round(max(auc, 1.0 - auc), 4)
        worst = max(per_feat, key=per_feat.get) if per_feat else "none"
        report[tname] = dict(n_domain=int(dom.sum()), n_positives=int(y.sum()),
                             max_auc=per_feat.get(worst, 0.0), worst_feature=worst, aucs=per_feat)
    return report


def control_destination_surface(dst_rc: np.ndarray, footprint: np.ndarray, union: np.ndarray,
                                km_block_px: int = 10) -> np.ndarray:
    """Off-ancestor-union cells lying in the same 1 km blocks the treatment used."""
    h, w = footprint.shape
    nb, mb = h // km_block_px, w // km_block_px
    bb = np.zeros((nb, mb), dtype=bool)
    for r, c in dst_rc:
        bi, bj = int(r) // km_block_px, int(c) // km_block_px
        if bi < nb and bj < mb:
            bb[bi, bj] = True
    blocks = np.zeros((h, w), dtype=bool)
    blocks[: nb * km_block_px, : mb * km_block_px] = np.repeat(np.repeat(bb, km_block_px, axis=0),
                                                               km_block_px, axis=1)
    return blocks & footprint & ~union


def fold_fair_proxy(d28_unmasked, footprint, catalogue, union, h19_5, *, km_block_px=10) -> dict:
    """Symmetric hide-and-recover PROXY: R0 *and* every arm rebuilt from ``f.visible`` only."""
    folds = g86inst.build(footprint, catalogue, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    arms = ("R0", "b5km-surfext-down10", "b5km-surfext-down15", "b5km-surfext-down10-randdst")
    terms = {k: None for k in arms}
    details = []
    for f in folds:
        vis = f.visible & footprint
        edt_vis = ndi.distance_transform_edt(~vis)
        r0_f = d28_unmasked & footprint & (edt_vis > 2.0)
        u_cred_f, _ = mass_econ.marginal_credit(r0_f)
        off5_f = union & ~h19_5
        a10, _, dst10, _ = SE.relocate_surface_extension(
            r0_f, footprint, edt_vis, off5_f, n_move=SPECS["b5km-surfext-down10"]["n_move"],
            unique_credit_dots=u_cred_f)
        a15, _, _, _ = SE.relocate_surface_extension(
            r0_f, footprint, edt_vis, off5_f, n_move=SPECS["b5km-surfext-down15"]["n_move"],
            unique_credit_dots=u_cred_f)
        ctl_dest = control_destination_surface(dst10, footprint, union, km_block_px)
        actl, _, _, _ = SE.relocate_surface_extension(
            r0_f, footprint, edt_vis, ctl_dest, n_move=SPECS["b5km-surfext-down10-randdst"]["n_move"],
            unique_credit_dots=u_cred_f, order_seed=SPECS["b5km-surfext-down10-randdst"]["seed"])
        rasters = {"R0": r0_f, "b5km-surfext-down10": a10, "b5km-surfext-down15": a15,
                   "b5km-surfext-down10-randdst": actl}
        scores = {}
        for name, arr in rasters.items():
            res, t = evaluate_holdout.evaluate(arr.astype(np.float32), f.fold,
                                               f.fold["region"] & footprint,
                                               origin=(0, 0), global_shape=arr.shape)
            terms[name] = t if terms[name] is None else terms[name] + t
            scores[name] = round(float(res["dti"]), 6)
        details.append(dict(fold=f.name, n_truth_px=int(f.truth.sum()), n_r0_dots=int(r0_f.sum()), dti=scores))
    base = evaluate_holdout.pooled_summary(terms, draws=1000, seed=520810, candidate="R0")
    out = dict(protocol="buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12) + "
                        "symmetric fold-fair rebuild of R0 and every arm from f.visible only",
               evidence_class="PROXY",
               contamination=("R0 is rebuilt fold-fair from f.visible; the destination surface is a fixed "
                              "ancestor field (catalogue-trained) exactly as in the merged b5km-cvband-down4 arm"),
               n_withheld_positive_pixels=int(base["scores"]["R0"]["withheld_positive_pixels"]),
               n_bootstrap_clusters_20km=int(base["bootstrap"]["clusters"]),
               R0=dict(dti=round(float(base["scores"]["R0"]["dti"]), 6),
                       ci95=[round(float(x), 6) for x in base["scores"]["R0"]["ci95"]]),
               folds=details, arms={})
    for key in arms[1:]:
        s = evaluate_holdout.pooled_summary({"R0": terms["R0"], key: terms[key]}, draws=1000,
                                            seed=520810, candidate=key)
        row = s["scores"][key]
        diff = s["paired_differences"]["R0"]
        out["arms"][key] = dict(dti=round(float(row["dti"]), 6),
                                ci95=[round(float(x), 6) for x in row["ci95"]],
                                delta_vs_R0=round(float(diff["delta"]), 6),
                                delta_ci95=[round(float(x), 6) for x in diff["ci95"]],
                                n_truth=int(row["withheld_positive_pixels"]), evidence_class="PROXY")
    return out


def main() -> int:
    # Historical variant builders obey the same literal pre-placement stop.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default="releases")
    ap.add_argument("--stamp", default=DATE_TAG)
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    t0 = time.time()

    print("[1/7] verifying pins", flush=True)
    pins = verify_pins()
    for k, v in pins.items():
        print(f"      {k:34s} {v['sha256'][:16]}…  {v['pin_source']}")

    print("[2/7] rebuilding R0 byte-for-byte and checking the d28 lineage", flush=True)
    g = g57grid.load_grid(BRIDGE)
    foot = np.asarray(g.footprint, bool)
    cat = np.asarray(g.catalogue, bool)
    rebuild = rebuild_parent(g, read(BASE_FILE))
    if not (rebuild["content_identical"] and rebuild["byte_identical_sha"]):
        raise SystemExit(f"parent rebuild gate FAILED: {rebuild}")
    parent = (read(PARENT_FILE) > 0) & foot
    if int(parent.sum()) != N_DOTS_R0 or sha256(PARENT_FILE) != PARENT_SHA:
        raise SystemExit("R0 verification mismatch")
    edt_cat = ndi.distance_transform_edt(~cat)
    d28 = (read(PINNED_INPUTS["scored_d28_unscored"]) > 0.5) & foot
    if not np.array_equal(d28 & (edt_cat > 2.0), parent):
        raise SystemExit("lineage check failed: d28 & (edt_cat > 2.0) != R0")
    print(f"      R0 verified: 37,654 dots, sha256 {rebuild['rebuilt_sha256'][:16]}…", flush=True)

    print("[3/7] ancestor surfaces + merged-arm reproduction", flush=True)
    h19_5 = (read(PINNED_INPUTS["scored_h19_5"]) > 0.5) & foot
    h19_4 = (read(PINNED_INPUTS["scored_h19_4"]) > 0.5) & foot
    h16_1 = (read(PINNED_INPUTS["scored_h16_1"]) > 0.5) & foot
    union = (h19_5 | h19_4 | h16_1) & foot
    off5 = union & ~h19_5
    u_cred, u_cred_info = mass_econ.marginal_credit(parent)
    edt_parent = ndi.distance_transform_edt(~parent)
    free_h5 = int((h19_5 & ~parent & (edt_cat > 3.0) & (edt_parent >= SE.MIN_SPACING_PX)).sum())
    free_off5 = int((off5 & ~parent & (edt_cat > 3.0) & (edt_parent >= SE.MIN_SPACING_PX)).sum())
    surface_audit = dict(
        h19_5_px=int(h19_5.sum()), h19_4_px=int(h19_4.sum()), h16_1_px=int(h16_1.sum()),
        union_px=int(union.sum()), off_h19_5_px=int(off5.sum()),
        parent_dots_on_h19_5=int((parent & h19_5).sum()),
        parent_dots_on_off5=int((parent & off5).sum()),
        free_slots_on_h19_5=free_h5, free_slots_on_off5=free_off5,
        constraint=f">{SE.MIN_CLEARANCE_PX} px from the catalogue and >={SE.MIN_SPACING_PX:.4f} px from every R0 dot",
        reading=("R0 is the H19-5 surface dotted at 2.8 px and is saturated there "
                 f"({free_h5} free slots); {free_off5} legal slots exist on H19-4|H16-1 ground "
                 "that carries zero parent mass."),
    )
    print(f"      {surface_audit['reading']}", flush=True)

    merged, _, _, _ = C5.relocate_cvband_down(parent, foot, edt_cat, union,
                                              n_move=1506, unique_credit_dots=u_cred)
    probe_dir = Path(tempfile.mkdtemp())
    probe = probe_dir / "merged.tif"
    write_with_profile(probe, np.where(foot, merged.astype(np.float32), np.float32(0.0)), None)
    merged_sha = sha256(probe)
    shutil.rmtree(probe_dir, ignore_errors=True)
    if merged_sha != MERGED_DOWN4_SHA:
        raise SystemExit(f"merged b5km-cvband-down4 reproduction FAILED: {merged_sha} != {MERGED_DOWN4_SHA}")
    print(f"      merged {MERGED_DOWN4_ID} reproduced byte-exactly (sha256 {merged_sha[:16]}…)", flush=True)

    print("[4/7] building the three arms", flush=True)
    built: dict = {}
    for key, spec in SPECS.items():
        if spec["role"] == "candidate":
            dest = off5
        else:
            ref, _, dst10, _ = SE.relocate_surface_extension(
                parent, foot, edt_cat, off5, n_move=SPECS["b5km-surfext-down10"]["n_move"],
                unique_credit_dots=u_cred)
            dest = control_destination_surface(dst10, foot, union)
        dots, src, dst, st = SE.relocate_surface_extension(
            parent, foot, edt_cat, dest, n_move=spec["n_move"],
            unique_credit_dots=u_cred, order_seed=spec["seed"])
        cv1p = C5.block_density_stats(parent, foot, 10)
        cv1c = C5.block_density_stats(dots, foot, 10)
        cv5p = C5.block_density_stats(parent, foot, 50)
        cv5c = C5.block_density_stats(dots, foot, 50)
        st["cv_1km"] = dict(parent=cv1p, variant=cv1c)
        st["cv_5km"] = dict(parent=cv5p, variant=cv5c)
        if not st["count_fixed"] or st["n_dots"] != N_DOTS_R0:
            raise SystemExit(f"{key}: count not fixed")
        if not (MIN_PCT_CHANGED <= st["pct_changed"] <= MAX_PCT_CHANGED):
            raise SystemExit(f"{key}: pct_changed {st['pct_changed']} outside [1,50]")
        if np.any(dots & cat):
            raise SystemExit(f"{key}: positive mass on the catalogue")
        if st["min_added_cat_clearance_px"] is None or st["min_added_cat_clearance_px"] <= 3.0:
            raise SystemExit(f"{key}: newly emitted mass violates the >3.0 px clearance")
        if st["min_pair_distance_variant_px"] < st["min_pair_distance_parent_px"] - 1e-6:
            raise SystemExit(f"{key}: tightened the parent spacing floor")
        if int((dots & ~foot).sum()):
            raise SystemExit(f"{key}: mass outside the footprint")
        built[key] = dict(spec=spec, dots=dots, src=src, dst=dst, stats=st)
        print(f"      {key:30s} moved={st['n_added']:5d} ({st['pct_changed']:6.2f}% chg) "
              f"1km_CV {cv1p['density_cv_occupied']:.4f}->{cv1c['density_cv_occupied']:.4f} "
              f"dest_frac={st['added_on_destination_surface_fraction']:.3f} "
              f"min_cat={st['min_added_cat_clearance_px']:.3f}px", flush=True)

    print("[5/7] report-only instruments", flush=True)
    surrogate, sgmc_info = sgmc_surrogate(cat, foot)
    canary_features = {
        "h19_5": h19_5.astype(np.float32), "h19_4": h19_4.astype(np.float32),
        "h16_1": h16_1.astype(np.float32), "union": union.astype(np.float32),
        "off_h19_5": off5.astype(np.float32),
        "unique_credit_px": _credit_field(parent, u_cred),
        "d28_lineage": d28.astype(np.float32),
    }
    edt_sgmc = ndi.distance_transform_edt(~surrogate)
    edt_union = ndi.distance_transform_edt(~union)
    confound = {k: clearance_confound(parent, v["dots"], edt_cat, edt_sgmc, union, edt_union)
                for k, v in built.items()}
    budget = live_credit_budget(N_DOTS_R0)
    canaries = leakage_canary(canary_features, foot, cat, surrogate, edt_cat)
    worst_auc = max(v["max_auc"] for v in canaries.values())
    print(f"      leakage canary max single-feature AUC = {worst_auc:.4f} (stop threshold 0.90)", flush=True)
    if worst_auc > 0.90:
        raise SystemExit(f"STOP: canary AUC {worst_auc:.4f} > 0.90")

    quads = quadrant_masks(foot)
    model = {k: evaluate_surrogate(parent, v["dots"], surrogate, foot, cat, quads)
             for k, v in built.items()}
    for k, m in model.items():
        print(f"      MODEL SGMC {k:30s} delta={m['all']['delta']:+.6f} "
              f"(+{m['sign_replication']['n_positive']}/4 quads, jitter6 mean "
              f"{m['jitter_6px_ensemble']['mean_delta']:+.6f})", flush=True)
    proxy = fold_fair_proxy(d28, foot, cat, union, h19_5)
    for k, v in proxy["arms"].items():
        print(f"      PROXY fold-fair {k:30s} d={v['delta_vs_R0']:+.6f} "
              f"CI95 {v['delta_ci95']} n={v['n_truth']}", flush=True)

    print("[6/7] MUST gates + writing twins", flush=True)
    out_dir = ROOT / args.out_dir
    existing_shas: set[str] = set()
    with open(ROOT / "ledger/submissions.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("sha256"):
                existing_shas.add(row["sha256"])
    existing_shas |= {sha256(p) for p in FLEET.glob("*.tif")}
    dl = ROOT / "docs" / "downloads"
    if dl.is_dir():
        existing_shas |= {sha256(p) for p in dl.glob("*.tif")}
    profile = serialization_profile(None)
    gsha = git_sha()
    receipts, ledger_rows = [], []

    for key, card in built.items():
        spec, dots, st = card["spec"], card["dots"], card["stats"]
        field_zeros = np.where(foot, dots.astype(np.float32), np.float32(0.0)).astype(np.float32)
        td = Path(tempfile.mkdtemp())
        pr = td / "probe.tif"
        with rasterio.open(pr, "w", **profile) as dst:
            dst.write(field_zeros, 1)
        sha8 = sha256(pr)[:8]
        shutil.rmtree(td, ignore_errors=True)
        cid = f"{PARENT_ID}-CONC-{spec['slug']}-{args.stamp}-{sha8}"
        zeros_path = out_dir / f"{cid}-zeros.tif"
        nan_path = out_dir / f"{cid}.tif"

        m_all = model[key]["all"]
        m_sr = model[key]["sign_replication"]
        p_ff = proxy["arms"][key]
        predicted = (
            f"{m_all['delta']:+.4f} (quadrant range {m_sr['quadrant_range'][0]:+.4f}.."
            f"{m_sr['quadrant_range'][1]:+.4f}; {m_sr['n_positive']}/4 quadrants positive; "
            f"fold-fair PROXY {p_ff['delta_vs_R0']:+.4f}, CI95 [{p_ff['delta_ci95'][0]:+.4f},"
            f"{p_ff['delta_ci95'][1]:+.4f}], n={p_ff['n_truth']}). MODEL: SGMC-extra surrogate, not a score."
        )
        target = "H19-4|H16-1" if spec["role"] == "candidate" else "off-union same-block (CONTROL)"
        note = (f"R0 {PARENT_ID}; CONC surface-ext to {target}: {st['n_added']} dots moved "
                f"({st['pct_changed']:.1f}% chg); pred {m_all['delta']:+.4f} MODEL")[:140]
        if args.no_write:
            receipts.append(dict(id=cid, note=note, predicted_change=predicted, dry_run=True))
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        nan_arr = np.where(foot, dots.astype(np.float32), np.float32(np.nan)).astype(np.float32)
        nan_sha = write_with_profile(nan_path, nan_arr, float("nan"))
        z_sha = write_with_profile(zeros_path, field_zeros, None)
        if z_sha[:8] != sha8:
            raise SystemExit(f"{key}: probed sha8 {sha8} != written {z_sha[:8]}")

        v_zero = validate(zeros_path, foot, cat)
        rep_zero = format_report(zeros_path, BRIDGE / "sample_submission.tif", footprint=foot)
        v_nan = validate(nan_path, foot, cat)
        nan_fail = [k for k, ok in v_nan["checks"].items() if not ok and k not in NAN_POLICY_CHECKS]
        if not v_zero["all_checks_passed"] or not rep_zero["ok"]:
            raise SystemExit(f"{key}: zeros twin failed MUST gates: {rep_zero.get('problems')}")
        if nan_fail:
            raise SystemExit(f"{key}: NaN twin failed in-footprint gates: {nan_fail}")

        disk_z = read(zeros_path)
        disk_n = read(nan_path)
        if not np.array_equal(disk_z > 0.5, dots) or not np.array_equal(np.isfinite(disk_n) & (disk_n > 0.5), dots):
            raise SystemExit(f"{key}: on-disk re-read mismatch")
        if not np.all(np.isnan(disk_n[~foot])) or np.any(np.isnan(disk_n[foot])):
            raise SystemExit(f"{key}: NaN contract violated")
        if z_sha in existing_shas or nan_sha in existing_shas:
            raise SystemExit(f"{key}: exact sha256 collision with an existing file")
        existing_shas |= {z_sha, nan_sha}

        receipt = dict(
            id=cid, parent=PARENT_ID, axis=AXIS, value=spec["value"], role=spec["role"],
            n_dots=int(dots.sum()), pct_changed=st["pct_changed"],
            dot_digest=P.dot_digest(dots), surface_extension_stats=st,
            zeros=dict(file=zeros_path.name, sha256=z_sha, bytes=zeros_path.stat().st_size,
                       primary_for_upload=spec["role"] == "candidate", validator=v_zero,
                       format_report_ok=rep_zero["ok"]),
            nan=dict(file=nan_path.name, mode="nan", sha256=nan_sha, bytes=nan_path.stat().st_size,
                     in_footprint_checks_pass=not nan_fail, failed_checks=nan_fail,
                     policy_note="brief v2 spec form (NaN outside footprint); -zeros is the portal fallback"),
            submission_name=cid[:140], note=note, predicted_live_change=predicted,
            model_delta_sgmc=m_all["delta"], proxy_fold_fair=p_ff, evidence_class="MODEL",
            approved_for_weekly_slot=False, submission_slots_used=0,
            provenance=dict(input_pins=pins, parent_rebuild=rebuild,
                            merged_arm_reproduction=dict(id=MERGED_DOWN4_ID, sha256=merged_sha, matched=True),
                            surface_audit=surface_audit, git_sha=gsha),
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        zeros_path.with_suffix(".json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n",
                                                   encoding="utf-8")
        receipts.append(receipt)
        ledger_rows.append(dict(id=cid, site="GEMSDOE86", axis=AXIS, value=spec["value"],
                                status="BUILT" if spec["role"] == "candidate" else "CONTROL",
                                n_dots=int(dots.sum()), pct_changed=st["pct_changed"], sha8=sha8,
                                parent=PARENT_ID, encoding="zeros", sha256_zeros=z_sha,
                                sha256_nan=nan_sha, predicted_change=predicted,
                                source_url=f"releases/{zeros_path.name}", receipt_score="",
                                receipt_date="", dot_digest=receipt["dot_digest"],
                                form_note=note))
        print(f"      {cid}: gates PASS | zeros={z_sha[:8]} nan={nan_sha[:8]}", flush=True)

    print("[7/7] writing evidence card", flush=True)
    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        elapsed_seconds=round(time.time() - t0, 2), axis=AXIS, session=SESSION,
        axis_choice_reason=("Only merged CONCENTRATION arm positive on both report-only instruments "
                            "(b5km-cvband-down4: +0.0015 MODEL in 4/4 quadrants, +0.0008 PROXY); a "
                            "pre-build capacity audit shows its within-surface destination pool "
                            "saturates at ~2.4k dots, so the headroom is the unoccupied part of the "
                            "ancestor union, not more within-surface shaving."),
        parent=dict(id=PARENT_ID, n_dots=N_DOTS_R0, claimed_live_dti=0.2778,
                    claimed_evidence_class="CLAIM", rebuild=rebuild, d28_lineage_exact=True,
                    unique_credit_summary=u_cred_info),
        surface_capacity_audit=surface_audit,
        merged_arm_reproduction=dict(id=MERGED_DOWN4_ID, sha256=merged_sha,
                                     expected=MERGED_DOWN4_SHA, matched=True,
                                     meaning="restored input bytes are those the merged arm used"),
        variants=receipts,
        instrument_confound=dict(
            note=("The SGMC-extra surrogate cannot pay a dot that sits in the 0-3 px collar of a "
                  "mapped fault, because its truth is SGMC minus the catalogue. R0 is built almost "
                  "entirely of such dots, so outward-moving CONCENTRATION arms gain on this "
                  "instrument partly by construction; each arm is therefore read against its "
                  "matched random-destination control, not against zero."),
            per_arm=confound,
        ),
        live_credit_budget_projection=budget,
        report_only_instruments=dict(note="Brief v2 section 6: report-only; no arm was gated or tuned on these.",
                                     leakage_canary=canaries, sgmc_surrogate_info=sgmc_info,
                                     sgmc_model=model, hide_and_recover_proxy=proxy),
        submission_slots_used=0,
    )
    if not args.no_write:
        EVIDENCE_JSON.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        VARIANTS_JSON.write_text(json.dumps(ledger_rows, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"      wrote {EVIDENCE_JSON.relative_to(ROOT)} and {VARIANTS_JSON.relative_to(ROOT)}", flush=True)
    return 0


def _credit_field(parent: np.ndarray, u_cred: np.ndarray) -> np.ndarray:
    out = np.zeros(parent.shape, dtype=np.float32)
    ys, xs = np.nonzero(parent)
    out[ys, xs] = u_cred.astype(np.float32)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
