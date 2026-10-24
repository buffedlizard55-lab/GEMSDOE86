#!/usr/bin/env python3
"""CONCENTRATION dose-response rungs on R0 (down2 / down6 / down-max ceiling).

Post-merge note (PR #55 reconciliation): the concurrent PR #50 session independently
built the same down-mechanism ladder (cvband-down3/5/6) and merged first; its cvband-down6
is BYTE-IDENTICAL to this script's down6 (zeros sha256 1ed78e0f...), carried as
BUILT-DUPLICATE in ledger/variants_concentration_dose_rungs.json. This script's unique
contributions are the down2 (753-move) low rung and the downmax 2,381-move ceiling
(binary-searched), which confirm PR #50's capacity cap (IR-86-CONC-12) with the exact
ceiling number and show the marginal 122 moves past down6 cost more than they bought
(+0.0020 vs +0.0022 MODEL).

Why CONCENTRATION again, and why only the ``down`` direction
------------------------------------------------------------
Across all 10 CONCENTRATION rows in ``ledger/submissions.csv`` exactly one arm is
positive on **both** instruments: ``b5km-cvband-down4`` (SGMC ``MODEL`` ``+0.0015``
with 4/4 quadrants positive; symmetric fold-fair ``d28`` ``PROXY`` ``+0.0008``,
CI95 ``[-0.0004, +0.0018]``, ``n = 11,321``).  The up direction toward the Faulds
5 km prior is measured flat-to-negative (``up4 = -0.0005``, ``up8 = -0.0007``),
``MASS`` is closed (``IR-86-MASS-03``), ``SNAP`` is negative in three sessions
(``IR-86-SNAP-02``), and the PRUNE/RELIEF/SPACING ladders are built.  The ``down``
curve has exactly one point, so this session completes it:

* ``b5km-cvband-down2``   — 753 dots moved (2.00 % of dots, 4.00 % changed),
  1 km CV ``0.6235 -> ~0.56``: the *band-interior* rung.
* ``b5km-cvband-down6``   — 2,259 dots moved (6.00 % of dots, 12.00 % changed),
  1 km CV ``~0.48``: the first *below-the-band* rung.
* ``b5km-cvband-downmax`` — capacity-limited ceiling of the exact mechanism
  (binary-searched max feasible ``n_move`` under the same destination rule),
  CV ``~0.478``: the *pool-ceiling* rung.  The ceiling itself is a recorded
  structural fact the Week 4-5 composite needs.

Every rung shaves the lowest-unique-credit dot from the densest ``>= 3``-dot
1 km block (sources are exact prefixes across doses) and re-plants it on an
unused ``H19-5 | H19-4 | H16-1`` ancestor-ridge cell in a 1-2-dot block at
``> 3.0 px`` catalogue clearance and ``>= sqrt(8)`` spacing, count fixed at
37,654.  The released ``down4`` file is rebuilt in-run and asserted byte-identical
(``8aab97b6...``) as a regression anchor before anything new is written.

No truth raster is read. No network call, no portal, no submission, no login.

Usage
-----
    .venv/bin/python scripts/run_concentration_dose.py [--out-dir releases] [--stamp 20261023] [--no-write]
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from run_concentration_5km import (  # noqa: E402
    PINNED_INPUTS,
    evaluate_surrogate,
    quadrant_masks,
    run_leakage_canary,
    sgmc_surrogate,
    verify_manifest_pins,
)
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
from gems86 import concentration_5km as C5, instrument as g86inst, mass_econ  # noqa: E402
from gems86_axis import bands as ax_bands  # noqa: E402

MANIFEST = ROOT / "registry" / "data_manifest.json"
FLEET = ROOT / "data" / "scored_fleet"
EVIDENCE_JSON = ROOT / "evidence" / "concentration_dose_axis_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_concentration_dose_rungs.json"

AXIS = "CONCENTRATION"
AXIS_ASSIGNMENT = (
    "SELF-ASSIGNED this session (brief v2 section 1: pick axis without prompting). "
    "CONCENTRATION is the only axis whose single both-instruments-positive arm "
    "(b5km-cvband-down4) has a one-point dose curve; MASS/SNAP are closed negative, "
    "PRUNE/RELIEF/SPACING ladders are built, TRACKB is Phase-2 only."
)
N_DOTS_R0 = 37654
MIN_PCT_CHANGED, MAX_PCT_CHANGED = 1.0, 50.0
NAN_POLICY_CHECKS = {"no_nan_anywhere", "outside_footprint_zero"}

# Released down4 anchor (ledger/submissions.csv, GEMSDOE86 row of 2026-10-23).
ANCHOR_ID = "h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown4-20261023-8aab97b6"
ANCHOR_ZEROS_SHA = "8aab97b65f70ba6c5dc4e3f0e73d95cbcb602da0d110c46dd0cf6a3a2e55d863"
ANCHOR_CV = 0.5162

DOWNMAX_FRACTION_LADDER = (0.0632, 0.06, 0.055, 0.05, 0.045, 0.04, 0.03, 0.02)


def ridge_union_from_pins(foot: np.ndarray) -> np.ndarray:
    ridge = np.zeros_like(foot, dtype=bool)
    for key in ("scored_h19_5", "scored_h19_4", "scored_h16_1"):
        ridge |= (read(PINNED_INPUTS[key]) > 0.5) & foot
    return ridge


def max_feasible_downmax(
    parent: np.ndarray,
    foot: np.ndarray,
    edt_cat: np.ndarray,
    ridge: np.ndarray,
    u_cred: np.ndarray,
    lo: int = 1506,
    hi: int = 3012,
) -> tuple[int, dict]:
    """Largest n_move the 1-2-dot sparse-ridge destination pool can absorb."""
    best_stats: dict | None = None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        try:
            _, _, _, st = C5.relocate_cvband_down(
                parent, foot, edt_cat, ridge, n_move=mid, unique_credit_dots=u_cred
            )
            lo = mid
            best_stats = st
        except ValueError:
            hi = mid
    return lo, best_stats or {}


def run_fold_fair_proxy_dose(
    d28_unmasked: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    *,
    ridge_union: np.ndarray,
    tmi_up150: np.ndarray,
    dose_fractions: dict[str, float],
) -> dict:
    """Fold-fair hide-and-recover PROXY restricted to the down-dose arms.

    Same protocol as the 5 km session (buffered component draw seed=20,
    hide_frac=0.20, buffer_px=3, boundary_px=12; both R0 and every arm's block
    prior and >3 px collar are rebuilt from f.visible only).  ``downmax`` falls
    back down its fraction ladder inside a fold whose sparse-ridge pool cannot
    absorb the full-grid ceiling dose; the chosen fraction is recorded per fold.
    """
    folds = g86inst.build(footprint, catalogue, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    arm_keys = ("R0", "b5km-cvband-down4", "b5km-cvband-down2", "b5km-cvband-down6", "b5km-cvband-downmax")
    terms_by_arm: dict[str, np.ndarray | None] = {k: None for k in arm_keys}
    fold_details = []
    rdg_topo_cached = C5.skeleton_tips_and_junctions(ridge_union & footprint)
    tmi_ga_cached = C5.local_agc_gradient(tmi_up150, footprint, window_px=101)

    for f in folds:
        vis = f.visible & footprint
        edt_vis = ndi.distance_transform_edt(~vis)
        r0_f = d28_unmasked & footprint & (edt_vis > 2.0)
        u_cred_f, _ = mass_econ.marginal_credit(r0_f)
        n_r0 = int(r0_f.sum())

        p5_f = C5.faulds_5km_block_prior(
            footprint, vis, ridge_union, tmi_up150, block_px=50,
            precomputed_ridge_topo=rdg_topo_cached,
            precomputed_tmi_grad_agc=tmi_ga_cached,
        )
        n_down4 = int(round(dose_fractions["b5km-cvband-down4"] * n_r0))
        down4_f, _, _, _ = C5.relocate_cvband_down(
            r0_f, footprint, edt_vis, ridge_union, n_move=n_down4, unique_credit_dots=u_cred_f,
        )
        arms_f = {"b5km-cvband-down4": down4_f}
        per_fold_dose = {"b5km-cvband-down4": n_down4}
        for key in ("b5km-cvband-down2", "b5km-cvband-down6"):
            n_k = int(round(dose_fractions[key] * n_r0))
            out_k, _, _, _ = C5.relocate_cvband_down(
                r0_f, footprint, edt_vis, ridge_union, n_move=n_k, unique_credit_dots=u_cred_f,
            )
            arms_f[key] = out_k
            per_fold_dose[key] = n_k
        for frac in DOWNMAX_FRACTION_LADDER:
            n_max = int(round(frac * n_r0))
            try:
                out_m, _, _, _ = C5.relocate_cvband_down(
                    r0_f, footprint, edt_vis, ridge_union, n_move=n_max, unique_credit_dots=u_cred_f,
                )
                arms_f["b5km-cvband-downmax"] = out_m
                per_fold_dose["b5km-cvband-downmax"] = n_max
                break
            except ValueError:
                continue
        if "b5km-cvband-downmax" not in arms_f:
            arms_f["b5km-cvband-downmax"] = r0_f.copy()
            per_fold_dose["b5km-cvband-downmax"] = 0

        rasters = {"R0": r0_f, **arms_f}
        for aname, arr in rasters.items():
            res, t_arr = evaluate_holdout.evaluate(
                arr.astype(np.float32),
                f.fold,
                f.fold["region"] & footprint,
                origin=(0, 0),
                global_shape=arr.shape,
            )
            terms_by_arm[aname] = t_arr if terms_by_arm[aname] is None else terms_by_arm[aname] + t_arr
        fold_details.append(
            dict(fold=f.name, n_truth_px=int(f.truth.sum()), n_r0_dots=n_r0,
                 per_fold_dose=per_fold_dose)
        )

    base = evaluate_holdout.pooled_summary(
        {k: v for k, v in terms_by_arm.items() if v is not None},
        draws=1000, seed=520810, candidate="R0",
    )
    out: dict = {
        "protocol": (
            "buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12) + "
            "symmetric fold-fair d28 rebuild for BOTH R0 and every down-dose arm"
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
            draws=1000, seed=520810, candidate=key,
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
    print("[1/8] Verifying bridge, parent, and manifest SHA-256 pins...", flush=True)
    pins = verify_pins()
    manifest_pins = verify_manifest_pins(PINNED_INPUTS)

    print("[2/8] Rebuilding R0 byte-for-byte + verifying unmasked d28 lineage...", flush=True)
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
    print(f"      R0 verified: {int(parent.sum())} dots, byte-exact sha256={rebuild['rebuilt_sha256'][:16]}...", flush=True)
    edt_cat = ndi.distance_transform_edt(~cat)
    d28 = (read(PINNED_INPUTS["scored_d28_unscored"]) > 0.5) & foot
    if not np.array_equal(d28 & (edt_cat > 2.0), parent):
        raise SystemExit("Lineage verification failed: d28 & (edt_cat > 2.0) != R0")
    ridge = ridge_union_from_pins(foot)

    print("[3/8] Unique-credit surface + down4 byte-exact regression anchor...", flush=True)
    u_cred_r0, u_cred_info = mass_econ.marginal_credit(parent)
    anchor_dots, a_src, _, a_stats = C5.relocate_cvband_down(
        parent, foot, edt_cat, ridge, n_move=1506, unique_credit_dots=u_cred_r0,
    )
    a_cv = a_stats["cv_1km_variant"]["density_cv_occupied"]
    if not (0.51 <= a_cv <= 0.59):
        raise SystemExit(f"anchor down4 CV {a_cv} left the [0.51, 0.59] band")
    profile = serialization_profile(None)
    probe_dir = Path(tempfile.mkdtemp())
    anchor_probe = probe_dir / "anchor.tif"
    with rasterio.open(anchor_probe, "w", **profile) as dst:
        dst.write(np.where(foot, anchor_dots.astype(np.float32), np.float32(0.0)).astype(np.float32), 1)
    anchor_sha = sha256(anchor_probe)
    shutil.rmtree(probe_dir, ignore_errors=True)
    if anchor_sha != ANCHOR_ZEROS_SHA:
        raise SystemExit(
            f"REGRESSION ANCHOR FAILED: rebuilt down4 zeros sha256 {anchor_sha} != released {ANCHOR_ZEROS_SHA}; "
            "the rebuild path diverges from the released artifact - STOP, do not approximate."
        )
    print(f"      down4 anchor byte-exact: {anchor_sha[:16]}... (CV {a_cv:.4f})", flush=True)

    print("[4/8] Building down2 / down6 rungs + binary-searching the downmax ceiling...", flush=True)
    specs = {
        "b5km-cvband-down2": dict(n_move=753, pct_of_dots=2.00),
        "b5km-cvband-down6": dict(n_move=2259, pct_of_dots=6.00),
    }
    built: dict[str, dict] = {}
    src_sets: dict[str, np.ndarray] = {}
    for key, spec in specs.items():
        dots, src, dst, st = C5.relocate_cvband_down(
            parent, foot, edt_cat, ridge, n_move=spec["n_move"], unique_credit_dots=u_cred_r0,
        )
        built[key] = dict(spec=spec, dots=dots, stats=st)
        src_sets[key] = src
    n_max, max_stats = max_feasible_downmax(parent, foot, edt_cat, ridge, u_cred_r0)
    dots_m, src_m, dst_m, st_m = C5.relocate_cvband_down(
        parent, foot, edt_cat, ridge, n_move=n_max, unique_credit_dots=u_cred_r0,
    )
    built["b5km-cvband-downmax"] = dict(
        spec=dict(n_move=n_max, pct_of_dots=round(100.0 * n_max / N_DOTS_R0, 2),
                  ceiling_search=dict(max_feasible_n_move=n_max,
                                      capacity_note="1-2-dot sparse-ridge destination pool ceiling "
                                                    "under >= sqrt(8) spacing; binary-searched"),
                  stats_at_ceiling_cv=max_stats["cv_1km_variant"]["density_cv_occupied"] if max_stats else None),
        dots=dots_m, stats=st_m,
    )
    src_sets["b5km-cvband-downmax"] = src_m

    order = ["b5km-cvband-down2", "b5km-cvband-down6", "b5km-cvband-downmax"]
    # All five source sets (down2 < down4-anchor < down6 < downmax) must lie on ONE
    # common deterministic removal sequence: the master sequence is downmax's.
    master_src = src_sets["b5km-cvband-downmax"]
    nesting = {}
    chain = {"b5km-cvband-down2": (src_sets["b5km-cvband-down2"], None),
             "b5km-cvband-down4(anchor)": (a_src, None),
             "b5km-cvband-down6": (src_sets["b5km-cvband-down6"], None)}
    for key, (s, _) in chain.items():
        m = len(s)
        ok = m <= len(master_src) and np.array_equal(master_src[:m], s)
        nesting[key] = dict(n_removed=m, exact_prefix_of_downmax_master_sequence=bool(ok))
        if not ok:
            raise SystemExit(f"NESTING BROKEN for {key}: source set is not a prefix of the downmax removal sequence")
    print("      source-prefix nesting verified: down2 < down4(anchor) < down6 < downmax", flush=True)

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
        if st["added_on_ancestor_ridge_fraction"] < 1.0:
            raise SystemExit(f"{key}: added dots left the ancestor ridge union")
        print(
            f"      {key:22s}: moved={st['n_added']} ({st['pct_changed']:.2f}% changed), "
            f"1km_CV={st['cv_1km_variant']['density_cv_occupied']:.4f}, "
            f"ridge_frac={st['added_on_ancestor_ridge_fraction']:.3f}, "
            f"min_cat_px={st['min_added_cat_clearance_px']:.3f}",
            flush=True,
        )

    print("[5/8] Running report-only instruments (canary, SGMC MODEL, fold-fair PROXY)...", flush=True)
    bd = ax_bands.load_bands()
    bd["tmi_grad"] = ax_bands.gradient_magnitude(bd["tmi_up150"], fill_value=0.0)
    tmi_u8_masked = np.where((bd["tmi_up150"] > 0) & foot, bd["tmi_up150"], np.nan)
    prior_5km = C5.faulds_5km_block_prior(foot, cat, ridge, tmi_u8_masked, block_px=50)

    surrogate, sgmc_info = sgmc_surrogate(cat, foot)
    canary_features = {
        "prior_5km_px": prior_5km["prior_px"],
        "cat_tips_junc_15km": prior_5km["cat_loci_map"],
        "ridge_tips_junc_5km": prior_5km["rdg_loci_map"],
        "tmi_agc": prior_5km["tmi_agc"],
        "tmi_grad": bd["tmi_grad"],
    }
    canaries = run_leakage_canary(canary_features, foot, cat, surrogate, edt_cat)
    worst_auc = max(v["max_auc"] for v in canaries.values())
    print(f"      Leakage canary max single-feature AUC = {worst_auc:.4f} (threshold <= 0.90)", flush=True)
    if worst_auc > 0.90:
        raise SystemExit(f"STOP: single-feature leakage canary reached AUC {worst_auc:.4f} > 0.90")

    quads = quadrant_masks(foot)
    model = {
        key: evaluate_surrogate(parent, card["dots"], surrogate, foot, cat, quads)
        for key, card in built.items()
    }
    for key, m in model.items():
        print(
            f"      MODEL SGMC {key:22s}: delta={m['all']['delta']:+.6f} "
            f"(quads +:{m['sign_replication']['n_positive']}/4 "
            f"[{m['sign_replication']['quadrant_range'][0]:+.5f}..{m['sign_replication']['quadrant_range'][1]:+.5f}], "
            f"jitter6px mean={m['jitter_6px_ensemble']['mean_delta']:+.6f})",
            flush=True,
        )

    proxy_fold_fair = run_fold_fair_proxy_dose(
        d28, foot, cat, ridge_union=ridge, tmi_up150=tmi_u8_masked,
        dose_fractions={
            "b5km-cvband-down4": 1506 / N_DOTS_R0,
            "b5km-cvband-down2": 753 / N_DOTS_R0,
            "b5km-cvband-down6": 2259 / N_DOTS_R0,
        },
    )
    for k, pv in proxy_fold_fair["arms"].items():
        print(
            f"      PROXY fold-fair {k:22s}: DTI={pv['dti']:.6f}, "
            f"delta_vs_R0={pv['delta_vs_R0']:+.6f}, CI95={pv['delta_ci95']}, n_truth={pv['n_truth']}",
            flush=True,
        )
    proxy_static = {"R0": proxy_dti(parent.astype(np.float32), cat, foot)}
    for key, card in built.items():
        proxy_static[key] = proxy_dti(card["dots"].astype(np.float32), cat, foot)

    print("[6/8] Enforcing MUST gates & writing GeoTIFF twins + receipts...", flush=True)
    out_dir = ROOT / args.out_dir
    own_values = set(built.keys()) | {"b5km-cvband-down4"}
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

    git_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()
    slug_map = {
        "b5km-cvband-down2": "b5kmdown2",
        "b5km-cvband-down6": "b5kmdown6",
        "b5km-cvband-downmax": "b5kmdownmax",
    }
    written_receipts = []
    ledger_entries = []
    for key in order:
        card = built[key]
        dots, st = card["dots"], card["stats"]
        field_zeros = np.where(foot, dots.astype(np.float32), np.float32(0.0)).astype(np.float32)

        probe_dir = Path(tempfile.mkdtemp())
        probe = probe_dir / "probe.tif"
        with rasterio.open(probe, "w", **profile) as dst:
            dst.write(field_zeros, 1)
        sha8 = sha256(probe)[:8]
        shutil.rmtree(probe_dir, ignore_errors=True)

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
            value=card["spec"].get("value", key),
            role="candidate",
            n_dots=int(dots.sum()),
            pct_changed=st["pct_changed"],
            dot_digest=__import__("src.gems86.prune", fromlist=["prune"]).dot_digest(dots)
            if False else C5_DOT_DIGEST(dots),
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
                policy_note="brief v2 sections 6/7 spec form (NaN outside footprint); -zeros is portal fallback",
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
                down4_regression_anchor=dict(id=ANCHOR_ID, zeros_sha256=anchor_sha, matched=True),
                git_sha=git_sha,
            ),
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        zeros_path.with_suffix(".json").write_text(
            json.dumps(receipt, indent=2, allow_nan=False, default=_json_default) + "\n", encoding="utf-8"
        )
        written_receipts.append(receipt)

        ledger_entries.append(
            dict(
                id=cid,
                site="GEMSDOE86",
                axis=AXIS,
                value=key,
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

    print("[7/8] Writing master evidence card and ledger/variants_concentration_dose.json...", flush=True)
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
        down4_regression_anchor=dict(
            id=ANCHOR_ID, zeros_sha256=ANCHOR_ZEROS_SHA, rebuilt_zeros_sha256=anchor_sha,
            byte_identical=anchor_sha == ANCHOR_ZEROS_SHA, cv_1km=a_cv,
        ),
        dose_ladder=dict(
            block_px=10,
            cv_1km={"R0": a_stats["cv_1km_parent"]["density_cv_occupied"],
                    **{k: built[k]["stats"]["cv_1km_variant"]["density_cv_occupied"] for k in order},
                    "b5km-cvband-down4(anchor)": a_cv},
            source_prefix_nesting=nesting,
            downmax_ceiling=built["b5km-cvband-downmax"]["spec"]["ceiling_search"],
        ),
        variants=written_receipts,
        report_only_instruments=dict(
            note="Brief v2 section 6: report-only instruments; no candidate was gated or tuned on them.",
            leakage_canary=canaries,
            sgmc_surrogate_info=sgmc_info,
            sgmc_model=model,
            hide_and_recover_proxy_fold_fair=proxy_fold_fair,
            hide_and_recover_proxy_static=proxy_static,
        ),
        submission_slots_used=0,
    )
    if not args.no_write:
        EVIDENCE_JSON.write_text(json.dumps(summary, indent=2, allow_nan=False, default=_json_default) + "\n", encoding="utf-8")
        VARIANTS_JSON.write_text(json.dumps(ledger_entries, indent=2, allow_nan=False, default=_json_default) + "\n", encoding="utf-8")
        print(f"      Wrote {EVIDENCE_JSON.relative_to(ROOT)} and {VARIANTS_JSON.relative_to(ROOT)}", flush=True)

    print(f"[8/8] DONE in {time.time() - t0:.0f}s", flush=True)
    return 0


def C5_DOT_DIGEST(dots: np.ndarray) -> str:
    from gems86 import prune as PRUNE

    return PRUNE.dot_digest(dots)


def _json_default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serializable: {type(o)}")


if __name__ == "__main__":
    raise SystemExit(main())
