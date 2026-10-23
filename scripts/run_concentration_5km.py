#!/usr/bin/env python3
"""Deconfounded 5 km CONCENTRATION axis on R0 (GEMSDOE32 h33-h33-2-b2).

Why CONCENTRATION was chosen after ``git fetch origin main``
------------------------------------------------------------
At session start ``TRACKB`` was unoccupied; while verifying R0 and external bands,
concurrent PRs #39 (``MASS`` kernel-budget) and #41 (``TRACKB`` 3-arm corridor
build) merged to ``main``.  Re-checking ``ledger/submissions.csv`` at ``a482851``
showed ``CONCENTRATION`` was the *only* brief-v2 §5 axis with a single row
(``b1km-move15`` from PR #37), and forensic inspection uncovered four unaddressed
defects in that single row (logged as ``IR-86-CONC-05``):

  1. Its ``+0.006 MODEL`` figure in ``SLOT_PLAN.md`` was a hard-coded Python
     constant (``PREDICTIONS["CONCENTRATION"] = 0.006``), never measured on SGMC;
  2. It placed newly emitted dots down to ``2.2361 px`` from mapped catalogue
     faults, violating brief v2 §4.4 (``>= 3 px`` clearance on new mass);
  3. It abandoned R0's lineament evidence surface onto empty off-ridge pixels;
  4. It left ``SLOT_PLAN.md``'s two explicit proposals unbuilt: the **5 km**
     Faulds fault-interaction block scale and the **spread-to-0.51..0.59-CV-band**
     sign flip.

This script builds three controlled, count-fixed (``37,654``), ``> 3.0 px``
catalogue-clear, ``>= sqrt(8)``-spaced, 100% ancestor-ridge-supported variants on
``AXIS = CONCENTRATION``, measures a matched random-block control, and runs the
first actual SGMC ``MODEL`` + fold-fair ``d28`` hide-and-recover ``PROXY`` audit
on both the three new variants and PR #37's ``b1km-move15``.

Usage
-----
    .venv/bin/python scripts/run_concentration_5km.py [--no-write] [--stamp 20261023]
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
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from run_prune_ladder import (  # noqa: E402
    BRIDGE,
    PARENT_FILE,
    PARENT_ID,
    PARENT_SHA,
    proxy_dti,
    read,
    rebuild_parent,
    serialization_profile,
    sha256,
    verify_pins,
    write_with_profile,
)
from gems57 import evaluate_holdout, grid as g57grid, metric as g57metric  # noqa: E402
from gems57.gates import format_report  # noqa: E402
from gems57.validate import validate  # noqa: E402
from gems86 import concentration_5km as C5, instrument as g86inst, mass_econ, prune as PRUNE  # noqa: E402
from gems86_axis import bands as ax_bands, grid_io as ax_gio, variants as ax_var  # noqa: E402

MANIFEST = ROOT / "registry" / "data_manifest.json"
FLEET = ROOT / "data" / "scored_fleet"
CACHE_SCORED = ROOT / ".cache" / "gems_data" / "scored"
CACHE_EXT = ROOT / ".cache" / "gems_data" / "external"
EVIDENCE_JSON = ROOT / "evidence" / "concentration_5km_axis_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_concentration_5km.json"

AXIS = "CONCENTRATION"
AXIS_ASSIGNMENT = (
    "SELF-ASSIGNED this session (brief v2 §1: pick axis without prompting). After "
    "merging concurrent origin/main (PR #39 MASS-econ, PR #41 TRACKB), CONCENTRATION "
    "was the sole brief-§5 axis with only 1 ledger row (b1km-move15), whose +0.006 "
    "prediction was unmeasured and whose 2.236 px clearance breached §4.4."
)
N_DOTS_R0 = 37654
MIN_PCT_CHANGED, MAX_PCT_CHANGED = 1.0, 50.0
NAN_POLICY_CHECKS = {"no_nan_anywhere", "outside_footprint_zero"}

PINNED_INPUTS: dict[str, Path] = {
    "scored_h19_5": CACHE_SCORED / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
    "scored_h19_4": CACHE_SCORED / "gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif",
    "scored_h16_1": CACHE_SCORED / "gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif",
    "scored_d28_unscored": CACHE_SCORED / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "ext_derived_sgmc_faults_100m_u8": CACHE_EXT / "derived_sgmc_faults_100m_u8.tif",
    "ext_geodawn_extensions_u8": CACHE_EXT / "geodawn_extensions_u8.tif",
    "ext_geodawn_extensions_json": CACHE_EXT / "geodawn_extensions.json",
    "ext_topo_10m_derived_100m_u8": CACHE_EXT / "topo_10m_derived_100m_u8.tif",
    "ext_dem10_chi_100m_i16": CACHE_EXT / "dem10_chi_100m_i16.tif",
}

SPECS = {
    "b5km-ridge-up8": dict(
        value="b5km-ridge-up8",
        n_move=3012,
        direction="up_toward_faulds_5km_prior",
        hypothesis=(
            "Reallocating 8% of R0 (3,012 dots, 16.00% changed) out of the lowest-scoring "
            "5 km Faulds fault-interaction blocks onto unused pinned ancestor ridge cells "
            "(H19-5|H19-4|H16-1, >300 m off catalogue, >=283 m spacing) inside the top-35% "
            "fault-interaction 5 km blocks increases unmapped-fault coverage in structural "
            "step-overs, splays, and terminations without leaving the lineament surface."
        ),
    ),
    "b5km-ridge-up4": dict(
        value="b5km-ridge-up4",
        n_move=1506,
        direction="up_toward_faulds_5km_prior_half_dose",
        hypothesis=(
            "Strict nested half-dose prefix (4% = 1,506 dots moved, 8.00% changed) of "
            "b5km-ridge-up8; measures the dose-response slope (0% -> 4% -> 8%) and guards "
            "against ridge-pool saturation inside top-35% 5 km blocks."
        ),
    ),
    "b5km-cvband-down4": dict(
        value="b5km-cvband-down4",
        n_move=1506,
        direction="down_spread_into_0p51_0p59_cv_band",
        hypothesis=(
            "Exact-dose sign flip (4% = 1,506 dots moved, 8.00% changed): shaves redundant "
            "low-unique-credit dots off >=3-dot 1 km clusters onto unused ancestor ridges "
            "in sparse 1-2 dot blocks, bringing occupied 1 km block-density CV from R0's "
            "0.6235 down into the 0.51-0.59 band of top-scoring historical submissions."
        ),
    ),
}


def verify_manifest_pins(ids: dict[str, Path]) -> dict[str, dict]:
    files = {f["id"]: f for f in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]}
    out: dict[str, dict] = {}
    for eid, path in ids.items():
        entry = files[eid]
        if not path.is_file():
            raise SystemExit(
                f"pinned input {eid} missing at {path}; run scripts/restore_axis_inputs.py first"
            )
        got = sha256(path)
        if got != entry["sha256"]:
            raise SystemExit(f"SHA256 MISMATCH for {eid}: {got} != {entry['sha256']}")
        if path.stat().st_size != entry["bytes"]:
            raise SystemExit(f"BYTE SIZE MISMATCH for {eid}: {path.stat().st_size} != {entry['bytes']}")
        out[eid] = dict(
            path=str(path.relative_to(ROOT)),
            sha256=got,
            bytes=entry["bytes"],
            verified=True,
            provenance=entry.get("provenance", ""),
        )
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
        overlap_fraction=round(float((sg & catalogue).sum() / max(int(sg.sum()), 1)), 4),
        provenance="USGS State Geologic Map Compilation (SGMC, DOI 10.3133/ds1052), off-catalogue fault pixels",
        evidence_class="MODEL",
        note="Count-fixed across all CONCENTRATION arms (n=37,654), so IR-86-MASS-03 mass monotonicity cancels identically.",
    )


def quadrant_masks(footprint: np.ndarray) -> list[np.ndarray]:
    h, w = footprint.shape
    return [
        footprint & (np.arange(h)[:, None] < h // 2) & (np.arange(w)[None, :] < w // 2),
        footprint & (np.arange(h)[:, None] < h // 2) & (np.arange(w)[None, :] >= w // 2),
        footprint & (np.arange(h)[:, None] >= h // 2) & (np.arange(w)[None, :] < w // 2),
        footprint & (np.arange(h)[:, None] >= h // 2) & (np.arange(w)[None, :] >= w // 2),
    ]


def _shift_bool(mask: np.ndarray, dy: int, dx: int) -> np.ndarray:
    if dy == 0 and dx == 0:
        return mask
    h, w = mask.shape
    out = np.zeros_like(mask, dtype=bool)
    sy0, sy1 = max(0, -dy), min(h, h - dy)
    sx0, sx1 = max(0, -dx), min(w, w - dx)
    out[sy0 + dy : sy1 + dy, sx0 + dx : sx1 + dx] = mask[sy0:sy1, sx0:sx1]
    return out


def evaluate_surrogate(
    pred_parent: np.ndarray,
    pred_child: np.ndarray,
    surrogate: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    quads: list[np.ndarray],
) -> dict:
    regions = {"all": footprint}
    regions.update({f"q{i}": q for i, q in enumerate(quads, start=1)})
    out: dict = {}
    for name, valid in regions.items():
        a = g57metric.dti_binary(pred_parent, surrogate, valid=valid, known=catalogue)
        b = g57metric.dti_binary(pred_child, surrogate, valid=valid, known=catalogue)
        out[name] = dict(
            dti_parent=round(a["dti"], 6),
            dti_child=round(b["dti"], 6),
            delta=round(b["dti"] - a["dti"], 6),
            n_truth=int(a["n_truth"]),
            coverage_parent=round(a["coverage"], 6),
            coverage_child=round(b["coverage"], 6),
            tp_parent=round(a["tp"], 3),
            tp_child=round(b["tp"], 3),
            fp_parent=round(a["fp"], 3),
            fp_child=round(b["fp"], 3),
        )
    q_deltas = [out[f"q{i}"]["delta"] for i in range(1, 5)]
    out["sign_replication"] = dict(
        n_quadrants=4,
        n_positive=int(sum(d > 0 for d in q_deltas)),
        n_negative=int(sum(d < 0 for d in q_deltas)),
        quadrant_range=[round(min(q_deltas), 6), round(max(q_deltas), 6)],
    )
    jitter_deltas = []
    for dy, dx in ((0, 0), (-6, 0), (6, 0), (0, -6), (0, 6)):
        sg_j = _shift_bool(surrogate, dy, dx) & footprint & ~catalogue
        aj = g57metric.dti_binary(pred_parent, sg_j, valid=footprint, known=catalogue)
        bj = g57metric.dti_binary(pred_child, sg_j, valid=footprint, known=catalogue)
        jitter_deltas.append(round(bj["dti"] - aj["dti"], 6))
    out["jitter_6px_ensemble"] = dict(
        shifts_px=[[0, 0], [-6, 0], [6, 0], [0, -6], [0, 6]],
        deltas=jitter_deltas,
        mean_delta=round(float(np.mean(jitter_deltas)), 6),
        min_delta=round(min(jitter_deltas), 6),
        max_delta=round(max(jitter_deltas), 6),
    )
    return out


def run_leakage_canary(
    features: dict[str, np.ndarray],
    footprint: np.ndarray,
    catalogue: np.ndarray,
    surrogate: np.ndarray,
    edt_cat: np.ndarray,
) -> dict:
    targets = {
        "catalogue_in_footprint": (footprint, catalogue & footprint),
        "sgmc_beyond_3px_collar": (footprint & (edt_cat > 3.0), surrogate & (edt_cat > 3.0)),
    }
    report: dict = {}
    for tname, (dom, pos) in targets.items():
        y_all = pos[dom].astype(np.int8)
        per_feat: dict[str, float] = {}
        for fname, arr in features.items():
            x = np.asarray(arr, dtype=np.float64)[dom]
            fin = np.isfinite(x)
            if int(fin.sum()) < 100 or y_all[fin].min() == y_all[fin].max():
                continue
            auc_raw = float(roc_auc_score(y_all[fin], x[fin]))
            per_feat[fname] = round(max(auc_raw, 1.0 - auc_raw), 4)
        worst_name = max(per_feat, key=per_feat.get) if per_feat else "none"
        report[tname] = dict(
            n_domain=int(dom.sum()),
            n_positives=int(y_all.sum()),
            max_auc=per_feat.get(worst_name, 0.0),
            worst_feature=worst_name,
            aucs=per_feat,
        )
    return report


def run_fold_fair_proxy(
    d28_unmasked: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    *,
    ridge_union: np.ndarray,
    tmi_up150: np.ndarray,
    pr37_bands: dict,
) -> dict:
    """True fold-fair hide-and-recover PROXY resolving ``IR-86-SPACING-05``.

    On every buffered whole-component fold ``f``, BOTH the parent R0
    (``d28 & (edt(f.visible) > 2.0)``) AND every CONCENTRATION arm's block prior
    and ``> 3.0 px`` collar are built strictly from ``f.visible``.  Zero withheld
    fault pixels leak into either R0 or any candidate arm.
    """
    folds = g86inst.build(footprint, catalogue, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    arm_keys = ("R0", "b5km-ridge-up8", "b5km-ridge-up4", "b5km-cvband-down4", "AUDIT-b1km-move15-PR37")
    terms_by_arm: dict[str, np.ndarray | None] = {k: None for k in arm_keys}
    fold_details = []
    rdg_topo_cached = C5.skeleton_tips_and_junctions(ridge_union & footprint)
    tmi_ga_cached = C5.local_agc_gradient(tmi_up150, footprint, window_px=101)

    for f in folds:
        vis = f.visible & footprint
        edt_vis = ndi.distance_transform_edt(~vis)
        r0_f = d28_unmasked & footprint & (edt_vis > 2.0)
        u_cred_f, _ = mass_econ.marginal_credit(r0_f)

        p5_f = C5.faulds_5km_block_prior(
            footprint, vis, ridge_union, tmi_up150, block_px=50,
            precomputed_ridge_topo=rdg_topo_cached,
            precomputed_tmi_grad_agc=tmi_ga_cached,
        )
        n_up8 = int(round(0.08 * int(r0_f.sum())))
        n_up4 = int(round(0.04 * int(r0_f.sum())))
        up8_f, _, _, _ = C5.relocate_5km_ridge_up(
            r0_f, footprint, edt_vis, ridge_union, p5_f["prior_blocks"],
            n_move=n_up8, unique_credit_dots=u_cred_f,
        )
        up4_f, _, _, _ = C5.relocate_5km_ridge_up(
            r0_f, footprint, edt_vis, ridge_union, p5_f["prior_blocks"],
            n_move=n_up4, unique_credit_dots=u_cred_f,
        )
        down4_f, _, _, _ = C5.relocate_cvband_down(
            r0_f, footprint, edt_vis, ridge_union,
            n_move=n_up4, unique_credit_dots=u_cred_f,
        )

        # Also rebuild PR #37's 1 km move-15% rule fold-fairly on f.visible
        ctx_f = {"footprint": footprint, "catalogue": vis}
        p1_f = ax_var.block_prior(ctx_f, pr37_bands, vis, block_px=10)
        pr37_f, _ = ax_var.concentration(
            r0_f, ctx_f, pr37_bands, p1_f["prior"], 0.15,
            ax_gio.PARENT_CAT_CLEARANCE_PX, ax_gio.PARENT_MIN_SPACING_PX,
        )

        rasters = {
            "R0": r0_f,
            "b5km-ridge-up8": up8_f,
            "b5km-ridge-up4": up4_f,
            "b5km-cvband-down4": down4_f,
            "AUDIT-b1km-move15-PR37": pr37_f,
        }
        f_scores = {}
        for aname, arr in rasters.items():
            res, t_arr = evaluate_holdout.evaluate(
                arr.astype(np.float32),
                f.fold,
                f.fold["region"] & footprint,
                origin=(0, 0),
                global_shape=arr.shape,
            )
            terms_by_arm[aname] = t_arr if terms_by_arm[aname] is None else terms_by_arm[aname] + t_arr
            f_scores[aname] = round(float(res["dti"]), 6)
        fold_details.append(
            dict(fold=f.name, n_truth_px=int(f.truth.sum()), n_r0_dots=int(r0_f.sum()), dti=f_scores)
        )

    base = evaluate_holdout.pooled_summary(
        {k: v for k, v in terms_by_arm.items() if v is not None},
        draws=1000,
        seed=520810,
        candidate="R0",
    )
    out: dict = {
        "protocol": (
            "buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12) + "
            "symmetric fold-fair d28 rebuild for BOTH R0 and every candidate arm (resolves IR-86-SPACING-05)"
        ),
        "evidence_class": "PROXY",
        "contamination": "NONE (both R0 and all candidate priors/collars see only f.visible per fold)",
        "n_withheld_positive_pixels": int(base["scores"]["R0"]["withheld_positive_pixels"]),
        "n_bootstrap_clusters_20km": int(base["bootstrap"]["clusters"]),
        "R0": dict(
            dti=round(float(base["scores"]["R0"]["dti"]), 6),
            ci95=[round(float(x), 6) for x in base["scores"]["R0"]["ci95"]],
            n_truth=int(base["scores"]["R0"]["withheld_positive_pixels"]),
        ),
        "folds": fold_details,
        "arms": {},
    }
    for key in arm_keys[1:]:
        s = evaluate_holdout.pooled_summary(
            {"R0": terms_by_arm["R0"], key: terms_by_arm[key]},
            draws=1000,
            seed=520810,
            candidate=key,
        )
        row = s["scores"][key]
        diff = s["paired_differences"]["R0"]
        out["arms"][key] = dict(
            dti=round(float(row["dti"]), 6),
            ci95=[round(float(x), 6) for x in row["ci95"]],
            delta_vs_R0=round(float(diff["delta"]), 6),
            delta_ci95=[round(float(x), 6) for x in diff["ci95"]],
            n_truth=int(row["withheld_positive_pixels"]),
            evidence_class="PROXY",
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default="releases")
    ap.add_argument("--stamp", default="20261023")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    print("[1/7] Verifying bridge, parent, and manifest SHA-256 pins...", flush=True)
    pins = verify_pins()
    manifest_pins = verify_manifest_pins(PINNED_INPUTS)

    print("[2/7] Rebuilding R0 byte-for-byte + verifying unmasked d28 lineage...", flush=True)
    g = g57grid.load_grid(BRIDGE)
    foot, cat = np.asarray(g.footprint, bool), np.asarray(g.catalogue, bool)
    base_d28_solo = read(
        PARENT_FILE.parent / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
    )
    rebuild = rebuild_parent(g, base_d28_solo)
    if not (rebuild["content_identical"] and rebuild["byte_identical_sha"]):
        raise SystemExit(f"Parent byte-exact rebuild gate FAILED: {rebuild}")
    parent = (read(PARENT_FILE) > 0) & foot
    if int(parent.sum()) != N_DOTS_R0 or sha256(PARENT_FILE) != PARENT_SHA:
        raise SystemExit(f"R0 verification mismatch: dots={int(parent.sum())}")
    print(
        f"      R0 verified: {int(parent.sum())} dots, byte-exact sha256={rebuild['rebuilt_sha256'][:16]}...",
        flush=True,
    )
    edt_cat = ndi.distance_transform_edt(~cat)

    d28 = (read(PINNED_INPUTS["scored_d28_unscored"]) > 0.5) & foot
    if not np.array_equal(d28 & (edt_cat > 2.0), parent):
        raise SystemExit("Lineage verification failed: d28 & (edt_cat > 2.0) != R0")

    h19_5 = (read(PINNED_INPUTS["scored_h19_5"]) > 0.5) & foot
    h19_4 = (read(PINNED_INPUTS["scored_h19_4"]) > 0.5) & foot
    h16_1 = (read(PINNED_INPUTS["scored_h16_1"]) > 0.5) & foot
    ridge_union = (h19_5 | h19_4 | h16_1) & foot

    print("[3/7] Computing Faulds 5 km fault-interaction prior & auditing PR #37 b1km-move15...", flush=True)
    bd = ax_bands.load_bands()
    bd["tmi_grad"] = ax_bands.gradient_magnitude(bd["tmi_up150"], fill_value=0.0)
    tmi_u8_masked = np.where((bd["tmi_up150"] > 0) & foot, bd["tmi_up150"], np.nan)

    prior_5km = C5.faulds_5km_block_prior(foot, cat, ridge_union, tmi_u8_masked, block_px=50)
    print("      5 km block counts:", json.dumps(prior_5km["counts"]), flush=True)
    print("      5 km quadrant balance:", json.dumps(prior_5km["quadrant_balance"]), flush=True)

    # Reconstruct PR #37's b1km-move15 deterministically to measure its real SGMC MODEL & PROXY
    ctx_full = {"footprint": foot, "catalogue": cat}
    pr37_p1 = ax_var.block_prior(ctx_full, bd, cat, block_px=10)
    pr37_dots, pr37_stats = ax_var.concentration(
        parent, ctx_full, bd, pr37_p1["prior"], 0.15,
        ax_gio.PARENT_CAT_CLEARANCE_PX, ax_gio.PARENT_MIN_SPACING_PX,
    )
    pr37_added = pr37_dots & ~parent
    pr37_audit_geom = dict(
        n_dots=int(pr37_dots.sum()),
        n_moved=int(pr37_added.sum()),
        min_added_cat_clearance_px=round(float(edt_cat[pr37_added].min()), 4),
        violates_brief_sec4_3px_clearance=bool(float(edt_cat[pr37_added].min()) < 3.0),
        added_within_3px_of_catalogue=int((edt_cat[pr37_added] <= 3.0).sum()),
        added_on_h19_5_fraction=round(float((pr37_added & h19_5).sum()) / int(pr37_added.sum()), 4),
        added_on_ancestor_ridge_union_fraction=round(
            float((pr37_added & ridge_union).sum()) / int(pr37_added.sum()), 4
        ),
        cv_1km=pr37_stats["block_density_variant"]["density_cv_occupied"],
    )
    print("      PR #37 b1km-move15 forensic geometry:", json.dumps(pr37_audit_geom), flush=True)

    print("[4/7] Building 3 controlled CONCENTRATION variants + matched 5 km random control...", flush=True)
    u_cred_r0, u_cred_info = mass_econ.marginal_credit(parent)
    up8_dots, src8, dst8, up8_stats = C5.relocate_5km_ridge_up(
        parent, foot, edt_cat, ridge_union, prior_5km["prior_blocks"],
        n_move=SPECS["b5km-ridge-up8"]["n_move"], unique_credit_dots=u_cred_r0,
    )
    up4_dots, src4, dst4, up4_stats = C5.relocate_5km_ridge_up(
        parent, foot, edt_cat, ridge_union, prior_5km["prior_blocks"],
        n_move=SPECS["b5km-ridge-up4"]["n_move"], unique_credit_dots=u_cred_r0,
    )
    down4_dots, src_d4, dst_d4, down4_stats = C5.relocate_cvband_down(
        parent, foot, edt_cat, ridge_union,
        n_move=SPECS["b5km-cvband-down4"]["n_move"], unique_credit_dots=u_cred_r0,
    )
    ctl_rand8_dots, ctl_rand8_stats = C5.relocate_5km_random_control(
        parent, foot, edt_cat, ridge_union, prior_5km["valid_blocks"],
        n_move=SPECS["b5km-ridge-up8"]["n_move"], unique_credit_dots=u_cred_r0,
    )

    # Assert strict prefix nesting of b5km-ridge-up4 inside b5km-ridge-up8
    if not np.array_equal(src4, src8[: len(src4)]) or not np.array_equal(dst4, dst8[: len(dst4)]):
        raise SystemExit("Nesting invariant broken: b5km-ridge-up4 is not an exact prefix of b5km-ridge-up8")
    # Assert CV-band target on b5km-cvband-down4
    cv_down = down4_stats["cv_1km_variant"]["density_cv_occupied"]
    if not (0.51 <= cv_down <= 0.59):
        raise SystemExit(f"b5km-cvband-down4 1 km CV {cv_down} did not land inside [0.51, 0.59]")

    built = {
        "b5km-ridge-up8": dict(spec=SPECS["b5km-ridge-up8"], dots=up8_dots, stats=up8_stats),
        "b5km-ridge-up4": dict(spec=SPECS["b5km-ridge-up4"], dots=up4_dots, stats=up4_stats),
        "b5km-cvband-down4": dict(spec=SPECS["b5km-cvband-down4"], dots=down4_dots, stats=down4_stats),
    }
    for key, card in built.items():
        st = card["stats"]
        if not st["count_fixed"] or st["n_dots"] != N_DOTS_R0:
            raise SystemExit(f"{key}: count not fixed at {N_DOTS_R0}")
        if not (MIN_PCT_CHANGED <= st["pct_changed"] <= MAX_PCT_CHANGED):
            raise SystemExit(f"{key}: pct_changed={st['pct_changed']}% outside [1%, 50%]")
        if np.any(card["dots"] & cat):
            raise SystemExit(f"{key}: positive mass on catalogue")
        if st["min_added_cat_clearance_px"] is None or st["min_added_cat_clearance_px"] <= 3.0:
            raise SystemExit(f"{key}: newly emitted pixels violate >3.0 px clearance")
        if st["min_pair_distance_variant_px"] < st["min_pair_distance_parent_px"] - 1e-6:
            raise SystemExit(f"{key}: tightened parent's minimum dot spacing")
        print(
            f"      {key:20s}: moved={st['n_added']} ({st['pct_changed']}% changed), "
            f"1km_CV={st['cv_1km_variant']['density_cv_occupied']:.4f}, "
            f"5km_CV={st['cv_5km_variant']['density_cv_occupied']:.4f}, "
            f"ridge_frac={st['added_on_ancestor_ridge_fraction']:.3f}, "
            f"min_cat_px={st['min_added_cat_clearance_px']:.3f}",
            flush=True,
        )

    print("[5/7] Running report-only instruments (canary, SGMC MODEL, symmetric fold-fair PROXY)...", flush=True)
    surrogate, sgmc_info = sgmc_surrogate(cat, foot)
    canary_features = {
        "prior_5km_px": prior_5km["prior_px"],
        "cat_tips_junc_15km": prior_5km["cat_loci_map"],
        "ridge_tips_junc_5km": prior_5km["rdg_loci_map"],
        "tmi_agc": prior_5km["tmi_agc"],
        "tmi_grad": prior_5km["tmi_grad"],
    }
    canaries = run_leakage_canary(canary_features, foot, cat, surrogate, edt_cat)
    worst_auc = max(v["max_auc"] for v in canaries.values())
    print(f"      Leakage canary max single-feature AUC = {worst_auc:.4f} (threshold <= 0.90)", flush=True)
    if worst_auc > 0.90:
        raise SystemExit(f"STOP: single-feature leakage canary reached AUC {worst_auc:.4f} > 0.90")

    quads = quadrant_masks(foot)
    eval_arms = {k: v["dots"] for k, v in built.items()}
    eval_arms["CONTROL-b5km-rand8"] = ctl_rand8_dots
    eval_arms["AUDIT-b1km-move15-PR37"] = pr37_dots
    model = {
        k: evaluate_surrogate(parent, arr, surrogate, foot, cat, quads)
        for k, arr in eval_arms.items()
    }
    for k, m in model.items():
        print(
            f"      MODEL SGMC {k:24s}: delta={m['all']['delta']:+.6f} "
            f"(quads +:{m['sign_replication']['n_positive']}/4 "
            f"[{m['sign_replication']['quadrant_range'][0]:+.5f}..{m['sign_replication']['quadrant_range'][1]:+.5f}], "
            f"jitter6px mean={m['jitter_6px_ensemble']['mean_delta']:+.6f})",
            flush=True,
        )

    proxy_fold_fair = run_fold_fair_proxy(
        d28, foot, cat, ridge_union=ridge_union, tmi_up150=tmi_u8_masked, pr37_bands=bd
    )
    for k, pv in proxy_fold_fair["arms"].items():
        print(
            f"      PROXY fold-fair {k:24s}: DTI={pv['dti']:.6f}, "
            f"delta_vs_R0={pv['delta_vs_R0']:+.6f}, CI95={pv['delta_ci95']}, n_truth={pv['n_truth']}",
            flush=True,
        )
    proxy_static = {"R0": proxy_dti(parent.astype(np.float32), cat, foot)}
    for k, card in built.items():
        proxy_static[k] = proxy_dti(card["dots"].astype(np.float32), cat, foot)

    print("[6/7] Enforcing MUST gates & writing GeoTIFF twins + receipts...", flush=True)
    out_dir = ROOT / args.out_dir
    own_values = {v["value"] for v in SPECS.values()}
    existing_shas: set[str] = set()
    if (ROOT / "ledger/submissions.csv").exists():
        with open(ROOT / "ledger/submissions.csv", newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (
                    row.get("sha256")
                    and not (
                        row.get("axis", "").upper() == AXIS
                        and row.get("value", "") in own_values
                        and not row.get("receipt_score")
                    )
                ):
                    existing_shas.add(row["sha256"])
    existing_shas |= {sha256(p) for p in FLEET.glob("*.tif")}
    if (ROOT / "docs" / "downloads").is_dir():
        existing_shas |= {sha256(p) for p in (ROOT / "docs" / "downloads").glob("*.tif")}

    profile = serialization_profile(None)
    git_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()
    written_receipts = []
    ledger_entries = []

    slug_map = {
        "b5km-ridge-up8": "b5kmup8",
        "b5km-ridge-up4": "b5kmup4",
        "b5km-cvband-down4": "b5kmdown4",
    }
    for key, card in built.items():
        dots = card["dots"]
        st = card["stats"]
        field_zeros = np.where(foot, dots.astype(np.float32), np.float32(0.0)).astype(np.float32)

        probe_dir = Path(tempfile.mkdtemp())
        probe = probe_dir / "probe.tif"
        with rasterio.open(probe, "w", **profile) as dst:
            dst.write(field_zeros, 1)
        sha8 = sha256(probe)[:8]
        shutil.rmtree(probe_dir, ignore_errors=True)

        # Brief v2 §7 literal template: <parent>-<axis><value>-<yyyymmdd>-<sha8>
        cid = f"{PARENT_ID}-conc{slug_map[key]}-{args.stamp}-{sha8}"
        zeros_path = out_dir / f"{cid}-zeros.tif"
        nan_path = out_dir / f"{cid}.tif"

        m_all = model[key]["all"]
        m_sr = model[key]["sign_replication"]
        p_ff = proxy_fold_fair["arms"][key]
        predicted = (
            f"{m_all['delta']:+.4f} (quadrant range {m_sr['quadrant_range'][0]:+.4f}.."
            f"{m_sr['quadrant_range'][1]:+.4f}; {m_sr['n_positive']}/4 quadrants positive; "
            f"fold-fair PROXY {p_ff['delta_vs_R0']:+.4f}, CI95 [{p_ff['delta_ci95'][0]:+.4f},"
            f"{p_ff['delta_ci95'][1]:+.4f}], n={p_ff['n_truth']}). MODEL: SGMC-extra surrogate, not a score."
        )
        note = (
            f"R0 {PARENT_ID}; CONC {key}: {st['n_added']} ridge dots moved "
            f"({st['pct_changed']:.2f}% chg, 1km CV {st['cv_1km_variant']['density_cv_occupied']:.3f}); "
            f"pred {m_all['delta']:+.4f} MODEL"
        )[:140]

        if args.no_write:
            written_receipts.append(dict(id=cid, note=note, predicted_change=predicted, dry_run=True))
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
        nan_fail = [k2 for k2, ok in v_nan["checks"].items() if not ok and k2 not in NAN_POLICY_CHECKS]
        if not v_zero["all_checks_passed"] or not rep_zero["ok"]:
            raise SystemExit(f"{key}: zeros twin failed MUST gates: {rep_zero['problems']}")
        if nan_fail:
            raise SystemExit(f"{key}: NaN twin failed in-footprint gates: {nan_fail}")

        disk_z = read(zeros_path)
        disk_n = read(nan_path)
        if not np.array_equal(disk_z > 0.5, dots) or not np.array_equal(np.isfinite(disk_n) & (disk_n > 0.5), dots):
            raise SystemExit(f"{key}: on-disk re-read mismatch against in-memory dot set")
        if not np.all(np.isnan(disk_n[~foot])) or np.any(np.isnan(disk_n[foot])):
            raise SystemExit(f"{key}: NaN twin outside/inside footprint contract violated")
        if z_sha in existing_shas or nan_sha in existing_shas:
            raise SystemExit(f"{key}: exact sha256 collision with existing ledger/fleet file")
        existing_shas |= {z_sha, nan_sha}

        receipt = dict(
            id=cid,
            parent=PARENT_ID,
            axis=AXIS,
            value=card["spec"]["value"],
            role="candidate",
            n_dots=int(dots.sum()),
            pct_changed=st["pct_changed"],
            dot_digest=PRUNE.dot_digest(dots),
            concentration_stats=st,
            zeros=dict(
                file=zeros_path.name,
                sha256=z_sha,
                bytes=zeros_path.stat().st_size,
                primary_for_upload=True,
                validator=v_zero,
                format_report_ok=rep_zero["ok"],
            ),
            nan=dict(
                file=nan_path.name,
                mode="nan",
                sha256=nan_sha,
                bytes=nan_path.stat().st_size,
                in_footprint_checks_pass=not nan_fail,
                failed_checks=nan_fail,
                policy_note="brief v2 §6/§7 spec form (NaN outside footprint); -zeros is portal fallback",
            ),
            submission_name=cid[:140],
            note=note,
            predicted_live_change=predicted,
            model_delta_sgmc=m_all["delta"],
            proxy_fold_fair=p_ff,
            evidence_class="MODEL",
            approved_for_weekly_slot=False,
            submission_slots_used=0,
            provenance=dict(
                input_pins=pins,
                manifest_pins=manifest_pins,
                parent_rebuild=rebuild,
                git_sha=git_sha,
            ),
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        zeros_path.with_suffix(".json").write_text(
            json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        written_receipts.append(receipt)

        ledger_entries.append(
            dict(
                id=cid,
                site="GEMSDOE86",
                axis=AXIS,
                value=card["spec"]["value"],
                status="BUILT",
                n_dots=int(dots.sum()),
                pct_changed=st["pct_changed"],
                sha8=sha8,
                parent=PARENT_ID,
                encoding="zeros",
                sha256_zeros=z_sha,
                sha256_nan=nan_sha,
                predicted_change=predicted,
                source_url=f"releases/{zeros_path.name}",
                receipt_score="",
                receipt_date="",
                dot_digest=receipt["dot_digest"],
                files=[f"releases/{nan_path.name}", f"releases/{zeros_path.name}"],
                form_note=note,
                gate_all_pass=True,
                proxy=dict(
                    value=p_ff["dti"],
                    delta_vs_r0=p_ff["delta_vs_R0"],
                    ci95=p_ff["delta_ci95"],
                    n_withheld_positive_pixels=p_ff["n_truth"],
                    class_="PROXY",
                    note=proxy_fold_fair["contamination"],
                ),
            )
        )
        print(f"      {cid}: MUST gates PASS | zeros={z_sha[:8]} | nan={nan_sha[:8]}", flush=True)

    print("[7/7] Writing master evidence card and ledger/variants_concentration_5km.json...", flush=True)
    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        elapsed_seconds=round(time.time() - t0, 2),
        axis=AXIS,
        axis_assignment=AXIS_ASSIGNMENT,
        parent=dict(
            id=PARENT_ID,
            n_dots=N_DOTS_R0,
            claimed_live_dti=0.2778,
            claimed_evidence_class="CLAIM",
            rebuild=rebuild,
            d28_lineage_exact=True,
            unique_kernel_credit_summary=u_cred_info,
        ),
        prior_5km_summary=dict(
            counts=prior_5km["counts"],
            quadrant_balance=prior_5km["quadrant_balance"],
            nesting_verified_up4_in_up8=True,
        ),
        pr37_b1km_move15_forensic_audit=dict(
            id="gems86-h33-2b2-conc15-20261023-2b883f2d",
            published_hardcoded_prediction="+0.006 MODEL (unmeasured constant in scripts/build_axis_variants.py:57)",
            geometry=pr37_audit_geom,
            measured_sgmc_model=model["AUDIT-b1km-move15-PR37"],
            measured_fold_fair_proxy=proxy_fold_fair["arms"]["AUDIT-b1km-move15-PR37"],
        ),
        variants=written_receipts,
        null_control_not_promoted={
            "CONTROL-b5km-rand8": dict(
                description="Randomly permuted 5 km block prior on the same ancestor ridge pool (3,012 dots moved)",
                stats=ctl_rand8_stats,
                model_sgmc=model["CONTROL-b5km-rand8"],
            )
        },
        report_only_instruments=dict(
            note="Brief v2 §6: report-only instruments; no candidate was gated or tuned on them.",
            leakage_canary=canaries,
            sgmc_surrogate_info=sgmc_info,
            sgmc_model=model,
            hide_and_recover_proxy_fold_fair=proxy_fold_fair,
            hide_and_recover_proxy_static=proxy_static,
        ),
        submission_slots_used=0,
    )
    if not args.no_write:
        EVIDENCE_JSON.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        VARIANTS_JSON.write_text(json.dumps(ledger_entries, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"      Wrote {EVIDENCE_JSON.relative_to(ROOT)} and {VARIANTS_JSON.relative_to(ROOT)}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
