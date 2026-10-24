#!/usr/bin/env python3
"""Pediment-window CONCENTRATION on R0 (pre-registered unbuilt proposal #2).

Why this session exists
-----------------------
SLOT_PLAN.md (2026-10-23) closes every brief-v2 axis except two pre-registered
unbuilt proposals.  Proposal 2 (``IR-86-TRACKB-08`` ->
``evidence/concentration-5km-mechanism.md``) asks for the *pediment refinement* of
the session's best both-instruments arm ``concb5kmdown4``: weight the sparse-block
ridge additions toward thin-alluvium pediment windows (``relief_local`` 10-40 m,
> 1 km from a range front), where concealed Quaternary faults are under-represented
in the mapped catalogue, and attribute the gain by splitting the destination pool.

The three arms below are identical to ``concb5kmdown4`` in EVERY respect except
where the vacated dots land (same source shave, count fix, clearance, spacing,
ancestor-ridge support):

1. ``b5km-ped-down2p5``      941 dots (5.00 % changed), destinations strictly inside the
                             pediment window (its capacity caps at 1,045 moved);
2. ``b5km-nonped-down2p5``   941 dots, destinations strictly in the complement
                             (dose-matched attribution control for the pediment prior);
3. ``b5km-ped-down5``        1,882 dots (10.00 % changed), destinations pediment-first
                             with spillover (dose-response of rule 1).

The pediment mask is built ONLY from truth-free evidence bands (USGS 3DEP-derived
local relief + the RELIEF axis's detrended-elevation regime map), so it is fold-fair
by construction.  No catalogue byte, SGMC byte, or scored-truth byte enters the mask.

All MUST gates (brief v2 §6) are enforced; SGMC MODEL and the symmetric fold-fair
d28 PROXY stay REPORT-ONLY instruments.  Nothing is auto-approved for a slot.

Usage
-----
    .venv/bin/python scripts/run_concentration_pediment.py [--no-write] [--stamp 20261023]
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
from gems57 import grid as g57grid, metric as g57metric  # noqa: E402
from gems57.gates import format_report  # noqa: E402
from gems57.validate import validate  # noqa: E402
from gems57 import evaluate_holdout  # noqa: E402
from gems86 import concentration_5km as C5, instrument as g86inst, mass_econ, prune as PRUNE, relief as REL  # noqa: E402
from gems86 import io as g86io  # noqa: E402
from gems86 import concentration_pediment as CP  # noqa: E402
from run_concentration_5km import (  # noqa: E402
    PINNED_INPUTS,
    evaluate_surrogate,
    quadrant_masks,
    run_leakage_canary,
    sgmc_surrogate,
    verify_manifest_pins,
)

EVIDENCE_JSON = ROOT / "evidence" / "concentration_pediment_axis_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_concentration_pediment.json"
MECHANISM_MD = ROOT / "evidence" / "concentration-pediment-mechanism.md"

AXIS = "CONCENTRATION"
AXIS_ASSIGNMENT = (
    "SELF-ASSIGNED this session (brief v2 §1). All 7 axes are reconciled in SLOT_PLAN.md; "
    "the only pre-registered UNBUILT Phase-1 experiment left is proposal 2: the pediment-window "
    "refinement/attribution of concb5kmdown4, the sole arm positive on both instruments with "
    "4/4 quadrant agreement. This session builds exactly that experiment."
)
N_DOTS_R0 = 37654
MIN_PCT_CHANGED, MAX_PCT_CHANGED = 1.0, 50.0
NAN_POLICY_CHECKS = {"no_nan_anywhere", "outside_footprint_zero"}
STACK = ROOT / "data" / "training_features.tif"  # manifest pin id training_features

SPECS = {
    "b5km-ped-down2p5": dict(
        value="b5km-ped-down2p5",
        n_move=941,  # 2.5% of R0 = 5.00% of dots changed; max pediment-feasible dose is 1,045
        mode="ped",
        slug="b5kmpeddown2p5",
        hypothesis=(
            "Same shave rule as the slot-2 arm concb5kmdown4, dose-matched at 941 dots, but every "
            "relocated dot lands on an ancestor-ridge sparse-block cell inside thin-alluvium "
            "pediment windows (relief_local 10-40 m, >1 km from a RELIEF-regime range front), "
            "where concealed Quaternary faults are under-represented in the mapped catalogue, so "
            "each dot is more likely to pay against new-fault truth."
        ),
    ),
    "b5km-nonped-down2p5": dict(
        value="b5km-nonped-down2p5",
        n_move=941,
        mode="nonped",
        slug="b5kmnonpeddown2p5",
        hypothesis=(
            "Attribution complement at the identical 941-dot dose: destinations strictly OUTSIDE "
            "the pediment window. If this matches or beats b5km-ped-down2p5 on the SGMC MODEL "
            "surrogate, the slot-2 arm's gain is generic sparse-ridge coverage and the pediment "
            "prior is falsified (its pre-registered falsifier)."
        ),
    ),
    "b5km-ped-down5": dict(
        value="b5km-ped-down5",
        n_move=1882,  # 5% of R0 = 10.00% of dots changed; pediment fills first, then spills
        mode="ped_first",
        slug="b5kmpeddown5",
        hypothesis=(
            "Double dose of the pediment-prioritised rule (pediment destinations first — the "
            "window saturates near 1,045 cells — then spillover to the rest of the sparse-ridge "
            "pool). Linear dose-response predicts roughly twice the b5km-ped-down2p5 surrogate "
            "delta; a plateau says the pediment window saturates and the slot-2 upgrade path "
            "caps at the small dose."
        ),
    ),
}


def dequant_band(path: Path, band_name: str) -> np.ndarray:
    """Dequantise one u8 band exactly per its own q_lo/q_hi/`q=0 nodata` tags."""
    with rasterio.open(path) as src:
        names = list(src.descriptions)
        i = names.index(band_name)
        band = src.read(i + 1)
        tags = src.tags(i + 1)
    out = np.full(band.shape, np.nan, np.float32)
    live = band > 0
    out[live] = float(tags["q_lo"]) + (band[live].astype(np.float64) - 1.0) / 254.0 * (
        float(tags["q_hi"]) - float(tags["q_lo"])
    )
    return out


def build_fold_fair_proxy(
    d28_unmasked: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    *,
    ridge_union: np.ndarray,
    tmi_up150: np.ndarray,
    pediment: np.ndarray,
    arms_order: tuple[str, ...],
) -> dict:
    """Symmetric fold-fair hide-and-recover PROXY for the three pediment arms.

    Mirrors ``run_concentration_5km.run_fold_fair_proxy``: on every buffered
    whole-component fold BOTH R0 (``d28 & (edt(f.visible) > 2.0)``) and every arm
    are rebuilt from ``f.visible`` only.  The pediment window is truth-free, so the
    same mask is legitimately reused inside every fold (no withheld byte can enter).
    """
    folds = g86inst.build(footprint, catalogue, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    terms_by_arm: dict[str, np.ndarray | None] = {"R0": None, **{k: None for k in arms_order}}
    fold_details = []
    fallbacks: list[dict] = []

    for f in folds:
        vis = f.visible & footprint
        edt_vis = ndi.distance_transform_edt(~vis)
        r0_f = d28_unmasked & footprint & (edt_vis > 2.0)
        u_cred_f, _ = mass_econ.marginal_credit(r0_f)
        n4 = int(round(0.025 * int(r0_f.sum())))
        n8 = int(round(0.05 * int(r0_f.sum())))

        def _build(mode: str, n: int, key: str):
            try:
                return CP.build_ped_down(
                    r0_f, footprint, edt_vis, ridge_union, pediment,
                    n_move=n, mode=mode, unique_credit_dots=u_cred_f,
                )[0]
            except ValueError:
                fallback = "ped_first" if mode == "ped" else None
                fallbacks.append(dict(fold=f.name, arm=key, mode=mode, n=n,
                                      fallback=fallback or "legacy-order"))
                if fallback is None:
                    return C5.relocate_cvband_down(
                        r0_f, footprint, edt_vis, ridge_union,
                        n_move=n, unique_credit_dots=u_cred_f,
                    )[0]
                return CP.build_ped_down(
                    r0_f, footprint, edt_vis, ridge_union, pediment,
                    n_move=n, mode=fallback, unique_credit_dots=u_cred_f,
                )[0]

        rasters = {
            "R0": r0_f,
            "b5km-ped-down2p5": _build("ped", n4, "b5km-ped-down2p5"),
            "b5km-nonped-down2p5": _build("nonped", n4, "b5km-nonped-down2p5"),
            "b5km-ped-down5": _build("ped_first", n8, "b5km-ped-down5"),
        }
        fold_terms = {}
        for aname, arr in rasters.items():
            res, t_arr = evaluate_holdout.evaluate(
                arr.astype(np.float32),
                f.fold,
                f.fold["region"] & footprint,
                origin=(0, 0),
                global_shape=arr.shape,
            )
            terms_by_arm[aname] = t_arr if terms_by_arm[aname] is None else terms_by_arm[aname] + t_arr
            fold_terms[aname] = round(float(res["dti"]), 6)
        fold_details.append(
            dict(fold=f.name, n_truth_px=int(f.truth.sum()), n_r0_dots=int(r0_f.sum()), dti=fold_terms)
        )

    base = evaluate_holdout.pooled_summary(
        {k: v for k, v in terms_by_arm.items() if v is not None},
        draws=1000, seed=520810, candidate="R0",
    )
    out: dict = {
        "protocol": (
            "buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12) + "
            "symmetric fold-fair d28 rebuild for BOTH R0 and every candidate arm; pediment mask "
            "is truth-free and therefore fold-invariant"
        ),
        "evidence_class": "PROXY",
        "contamination": "NONE (R0 and all candidate arms see only f.visible per fold)",
        "fold_fallbacks": fallbacks,
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
    for key in arms_order:
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
    pinned = dict(PINNED_INPUTS)
    pinned["training_features"] = STACK
    manifest_pins = verify_manifest_pins(pinned)

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

    h19_5 = (read(PINNED_INPUTS["scored_h19_5"]) > 0.5) & foot
    h19_4 = (read(PINNED_INPUTS["scored_h19_4"]) > 0.5) & foot
    h16_1 = (read(PINNED_INPUTS["scored_h16_1"]) > 0.5) & foot
    ridge_union = (h19_5 | h19_4 | h16_1) & foot

    print("[3/8] Building the truth-free pediment window (relief bands only)...", flush=True)
    det_elev = g86io.read_band(STACK, "det_elev").astype(np.float64)
    det_elev_slope = g86io.read_band(STACK, "det_elev_slope").astype(np.float64)
    for nm, arr in (("det_elev", det_elev), ("det_elev_slope", det_elev_slope)):
        if not np.all(np.isfinite(arr[foot])):
            raise SystemExit(f"{nm}: nodata sentinel survived the reader (IR repeat)")
    idx = REL.relief_index(det_elev, det_elev_slope, foot)
    regimes, regime_cuts = REL.regime_map(idx, foot)
    range_front = regimes == 2
    relief_local = dequant_band(
        PINNED_INPUTS["ext_topo_10m_derived_100m_u8"], "relief_local"
    ).astype(np.float64)
    ped, ped_info = CP.pediment_window(relief_local, range_front, foot)
    print(f"      regimes: {json.dumps(regime_cuts['area_px'])}", flush=True)
    print(f"      pediment window: {ped_info['n_window_px']} px ({100*ped_info['pct_footprint']:.1f}% of footprint)", flush=True)
    print(f"      R0 dots inside window: {int((parent & ped).sum())}", flush=True)

    print("[4/8] Building 3 controlled CONCENTRATION arms + parent-arm attribution...", flush=True)
    u_cred_r0, u_cred_info = mass_econ.marginal_credit(parent)
    built: dict[str, dict] = {}
    for key, spec in SPECS.items():
        dots, src_rc, dst_rc, st = CP.build_ped_down(
            parent, foot, edt_cat, ridge_union, ped,
            n_move=spec["n_move"], mode=spec["mode"], unique_credit_dots=u_cred_r0,
        )
        built[key] = dict(spec=spec, dots=dots, src_rc=src_rc, dst_rc=dst_rc, stats=st)

    # Parent-arm attribution: where did concb5kmdown4 itself put its 1,506 dots?
    down4_dots, down4_src, down4_dst, down4_stats = C5.relocate_cvband_down(
        parent, foot, edt_cat, ridge_union, n_move=1506, unique_credit_dots=u_cred_r0,
    )
    down4_shares = CP.destination_regime_shares(down4_dst, ped, ridge_union)

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
            f"      {key:18s}: moved={st['n_added']} ({st['pct_changed']}% changed), "
            f"1km_CV={st['cv_1km_variant']['density_cv_occupied']:.4f}, "
            f"ridge_frac={st['added_on_ancestor_ridge_fraction']:.3f}, "
            f"min_cat_px={st['min_added_cat_clearance_px']:.3f}",
            flush=True,
        )
    # Regime-share design gates
    sh_ped = CP.destination_regime_shares(built["b5km-ped-down2p5"]["dst_rc"], ped, ridge_union)
    sh_non = CP.destination_regime_shares(built["b5km-nonped-down2p5"]["dst_rc"], ped, ridge_union)
    sh_d8 = CP.destination_regime_shares(built["b5km-ped-down5"]["dst_rc"], ped, ridge_union)
    sh_legacy = CP.destination_regime_shares(down4_dst, ped, ridge_union)
    if sh_ped["ped_fraction"] != 1.0:
        raise SystemExit(f"b5km-ped-down2p5 destinations not 100% inside the window: {sh_ped}")
    if sh_non["ped_fraction"] != 0.0:
        raise SystemExit(f"b5km-nonped-down2p5 destinations not 100% outside the window: {sh_non}")
    if sh_d8["ped_fraction"] <= sh_legacy["ped_fraction"]:
        raise SystemExit(
            f"b5km-ped-down5 pediment share {sh_d8['ped_fraction']} does not exceed the "
            f"parent arm's {sh_legacy['ped_fraction']}: dest_prefer ordering failed"
        )
    print(f"      dest shares: ped={json.dumps(sh_ped)}", flush=True)
    print(f"      dest shares: nonped={json.dumps(sh_non)}", flush=True)
    print(f"      dest shares: ped8={json.dumps(sh_d8)}", flush=True)
    print(f"      parent down4 dest shares: {json.dumps(down4_shares)}", flush=True)

    print("[5/8] Running report-only instruments (canary, SGMC MODEL, fold-fair PROXY)...", flush=True)
    surrogate, sgmc_info = sgmc_surrogate(cat, foot)
    with rasterio.open(PINNED_INPUTS["ext_geodawn_extensions_u8"]) as src:
        i_tmi = list(src.descriptions).index("TMI_up150")
        tmi_raw = src.read(i_tmi + 1)
    tmi_up150 = np.where((tmi_raw > 0) & foot, tmi_raw, np.nan).astype(np.float32)

    dist_front = ndi.distance_transform_edt(~range_front)
    canary_features = {
        "relief_local_m": np.where(foot, relief_local, 0.0),
        "pediment_window": ped.astype(np.float32),
        "dist_to_range_front_px": np.where(foot, dist_front, 0.0),
        "relief_regime_idx": np.where(foot, regimes.astype(np.float32), 0.0),
    }
    canaries = run_leakage_canary(canary_features, foot, cat, surrogate, edt_cat)
    worst_auc = max(v["max_auc"] for v in canaries.values())
    print(f"      Leakage canary max single-feature AUC = {worst_auc:.4f} (threshold <= 0.90)", flush=True)
    if worst_auc > 0.90:
        raise SystemExit(f"STOP: single-feature leakage canary reached AUC {worst_auc:.4f} > 0.90")

    quads = quadrant_masks(foot)
    eval_arms = {k: v["dots"] for k, v in built.items()}
    eval_arms["REF-concb5kmdown4"] = down4_dots
    model = {k: evaluate_surrogate(parent, arr, surrogate, foot, cat, quads) for k, arr in eval_arms.items()}
    for k, m in model.items():
        print(
            f"      MODEL SGMC {k:18s}: delta={m['all']['delta']:+.6f} "
            f"(quads +:{m['sign_replication']['n_positive']}/4 "
            f"[{m['sign_replication']['quadrant_range'][0]:+.5f}..{m['sign_replication']['quadrant_range'][1]:+.5f}], "
            f"jitter6px mean={m['jitter_6px_ensemble']['mean_delta']:+.6f})",
            flush=True,
        )

    arms_order = tuple(SPECS.keys())
    proxy_fold_fair = build_fold_fair_proxy(
        d28, foot, cat, ridge_union=ridge_union, tmi_up150=tmi_up150,
        pediment=ped, arms_order=arms_order,
    )
    for k, pv in proxy_fold_fair["arms"].items():
        print(
            f"      PROXY fold-fair {k:18s}: DTI={pv['dti']:.6f}, "
            f"delta_vs_R0={pv['delta_vs_R0']:+.6f}, CI95={pv['delta_ci95']}, n_truth={pv['n_truth']}",
            flush=True,
        )
    if proxy_fold_fair["fold_fallbacks"]:
        print(f"      NOTE fold fallbacks: {proxy_fold_fair['fold_fallbacks']}", flush=True)
    proxy_static = {"R0": proxy_dti(parent.astype(np.float32), cat, foot)}
    for key, card in built.items():
        proxy_static[key] = proxy_dti(card["dots"].astype(np.float32), cat, foot)

    cv_table = CP.cv_report(parent, {k: v["dots"] for k, v in built.items()} | {"REF-concb5kmdown4": down4_dots}, foot)
    print(f"      CV table (1km/5km/10km): {json.dumps(cv_table)}", flush=True)

    print("[6/8] Enforcing MUST gates & writing GeoTIFF twins + receipts...", flush=True)
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
    fleet = ROOT / "data" / "scored_fleet"
    existing_shas |= {sha256(p) for p in fleet.glob("*.tif")}
    if (ROOT / "docs" / "downloads").is_dir():
        existing_shas |= {sha256(p) for p in (ROOT / "docs" / "downloads").glob("*.tif")}

    git_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()
    written_receipts = []
    ledger_entries = []

    for key, card in built.items():
        dots = card["dots"]
        st = card["stats"]
        field_zeros = np.where(foot, dots.astype(np.float32), np.float32(0.0)).astype(np.float32)

        probe_dir = Path(tempfile.mkdtemp())
        probe = probe_dir / "probe.tif"
        with rasterio.open(probe, "w", **serialization_profile(None)) as dst:
            dst.write(field_zeros, 1)
        sha8 = sha256(probe)[:8]
        shutil.rmtree(probe_dir, ignore_errors=True)

        cid = f"{PARENT_ID}-conc{card['spec']['slug']}-{args.stamp}-{sha8}"
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
            f"({st['pct_changed']:.2f}% chg); pred {m_all['delta']:+.4f} MODEL"
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
            destination_regime_shares=CP.destination_regime_shares(card["dst_rc"], ped, ridge_union),
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

    print("[7/8] Writing master evidence card and ledger/variants_concentration_pediment.json...", flush=True)
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
        pediment_window=ped_info,
        relief_regimes=regime_cuts,
        parent_arm_attribution=dict(
            reference="REF-concb5kmdown4 (session slot-2 arm rebuilt with identical inputs)",
            destination_regime_shares=down4_shares,
            model_sgmc=model["REF-concb5kmdown4"]["all"],
            stats=down4_stats,
        ),
        variants=written_receipts,
        report_only_instruments=dict(
            note="Brief v2 §6: report-only instruments; no candidate was gated or tuned on them.",
            leakage_canary=canaries,
            sgmc_surrogate_info=sgmc_info,
            sgmc_model=model,
            hide_and_recover_proxy_fold_fair=proxy_fold_fair,
            hide_and_recover_proxy_static=proxy_static,
            block_density_cv=cv_table,
        ),
        submission_slots_used=0,
    )
    if not args.no_write:
        EVIDENCE_JSON.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        VARIANTS_JSON.write_text(json.dumps(ledger_entries, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"      Wrote {EVIDENCE_JSON.relative_to(ROOT)} and {VARIANTS_JSON.relative_to(ROOT)}", flush=True)

    print("[8/8] Done.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
