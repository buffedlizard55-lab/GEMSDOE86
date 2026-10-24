#!/usr/bin/env python3
"""10 km fault-system-scale CONCENTRATION axis on R0 (GEMSDOE32 h33-h33-2-b2).

Why CONCENTRATION at 10 km, and why now
---------------------------------------
At session start (main ``d0e53b8``) every brief-v2 §5 axis already carried
BUILT rows (37 total, 0 RECEIPT).  The one scale the repo's own evidence
pointed at but nobody had built is the 10 km (100 px) fault-system block:
``IR-86-TRACKB-08`` reports that top-scoring historical files cluster in a
narrow occupied-block-density CV band at 10 km while the 0.1152 lidar file
sits far outside it, and ``SLOT_PLAN.md`` logged ``CONCENTRATION-10km`` as an
unbuilt proposal.  All three ``(CONCENTRATION, b10km-*)`` keys here are new.

One correction measured before building (``IR-86-CONC-19``): with this repo's
canonical ``block_density_stats`` (occupied blocks, density = dots/footprint
cells), R0's 10 km CV is **0.736**, not 0.570 — above the 0.51-0.59 band under
either complete-block or padded-block accounting.  The dispersal (down)
direction is therefore the CV-band direction at 10 km too, exactly as at 1 km.

Arms (pre-registered in ``registry/preregistration_conc10.json`` before any
instrument ran; all count-fixed at 37,654, 100% of new dots on the pinned
ancestor ridge union ``H19-5|H19-4|H16-1``, ``> 3.0 px`` off catalogue,
``>= sqrt(8) px`` spacing — the audited 5 km machinery, block_px=100):

1. ``b10km-down8`` / ``b10km-down4`` — disperse 3,012 / 1,506 lowest-unique-
   credit dots out of the densest occupied 10 km blocks onto unused ridges in
   the sparsest occupied 10 km blocks (down4 is a strict prefix of down8).
2. ``b10km-ridge-up8`` — sign control: concentrate 3,012 dots toward the
   top-35% Faulds fault-interaction blocks, prior recomputed at 100 px.

Plus ``CONTROL-b10km-rand8`` (random 10 km block prior, measured only).
Report-only instruments: SGMC off-catalogue MODEL with quadrant + jitter
replication, symmetric fold-fair d28 PROXY, leakage canary.  No gate depends
on any of them (brief §6).  No network, no portal, no submission.

Usage
-----
    .venv/bin/python scripts/restore_axis_inputs.py --ids scored_h19_5 scored_h19_4 scored_h16_1 scored_d28_unscored ext_derived_sgmc_faults_100m_u8 ext_geodawn_extensions_u8 ext_geodawn_extensions_json ext_topo_10m_derived_100m_u8 ext_dem10_chi_100m_i16
    .venv/bin/python scripts/run_concentration_10km.py [--no-write] [--stamp 20261023]
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
    BRIDGE, PARENT_FILE, PARENT_ID, PARENT_SHA,
    proxy_dti, read, rebuild_parent, serialization_profile, sha256,
    verify_pins, write_with_profile,
)
from run_concentration_5km import (  # noqa: E402  ( audited helpers, reused unchanged )
    PINNED_INPUTS, evaluate_surrogate, quadrant_masks, run_leakage_canary,
    sgmc_surrogate, verify_manifest_pins,
)
from gems57 import evaluate_holdout, grid as g57grid  # noqa: E402
from gems57.gates import format_report  # noqa: E402
from gems57.validate import validate  # noqa: E402
from gems86 import concentration_5km as C5, concentration_10km as C10  # noqa: E402
from gems86 import instrument as g86inst, mass_econ, prune as PRUNE  # noqa: E402
from gems86_axis import bands as ax_bands  # noqa: E402

EVIDENCE_JSON = ROOT / "evidence" / "concentration_10km_axis_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_concentration_10km.json"
PREREG_JSON = ROOT / "registry" / "preregistration_conc10.json"
FLEET = ROOT / "data" / "scored_fleet"

AXIS = "CONCENTRATION"
AXIS_ASSIGNMENT = (
    "SELF-ASSIGNED this session (brief v2: do not prompt over axis choice). All 7 axes "
    "already carry BUILT rows; the 10 km fault-system block is the one unbuilt "
    "CONCENTRATION scale named by IR-86-TRACKB-08 and SLOT_PLAN.md proposal 2. "
    "Every (CONCENTRATION, b10km-*) key below is absent from ledger/submissions.csv."
)
BLOCK_PX = 100
N_DOTS_R0 = 37654
MIN_PCT_CHANGED, MAX_PCT_CHANGED = 1.0, 50.0
NAN_POLICY_CHECKS = {"no_nan_anywhere", "outside_footprint_zero"}
DOWN_FRAC_LADDER = (0.50, 0.65, 0.75, 0.85)
UP_FRAC_LADDER = (0.35, 0.45, 0.55)

SPECS = {
    "b10km-down8": dict(
        value="b10km-down8", n_move=3012, direction="down_disperse_10km_density",
        hypothesis=(
            "Dispersing 8% of R0 (3,012 dots, 16.00% changed) — the lowest-unique-credit "
            "dots of the densest occupied 10 km blocks — onto unused pinned ancestor "
            "ridge cells in the sparsest occupied 10 km blocks lowers the occupied "
            "10 km block-density CV from R0's 0.736 toward the 0.51-0.59 band and adds "
            "new-fault coverage in under-sampled fault systems without leaving the "
            "lineament surface."
        ),
    ),
    "b10km-down4": dict(
        value="b10km-down4", n_move=1506, direction="down_disperse_10km_density_half_dose",
        hypothesis=(
            "Strict nested half-dose prefix (4% = 1,506 dots moved, 8.00% changed) of "
            "b10km-down8; measures the 10 km dispersal dose-response slope (0% -> 4% -> 8%) "
            "and guards against sparse-block ridge-pool saturation."
        ),
    ),
    "b10km-ridge-up8": dict(
        value="b10km-ridge-up8", n_move=3012, direction="up_toward_faulds_10km_prior",
        hypothesis=(
            "Sign control at matched dose: concentrate 3,012 dots toward the top-35% "
            "Faulds fault-interaction blocks with the prior recomputed at 100 px "
            "(30 km catalogue / 10 km ridge tip-junction halos). Upward concentration "
            "lost at 1 km and 5 km; this tests whether fault-system-scale interaction "
            "zoning reverses that."
        ),
    ),
}


def _try_down(parent, foot, edt_cat, ridge_union, density, *, n_move, u_cred, fracs):
    """First destination fraction in ``fracs`` that places ``n_move`` dots."""
    last = None
    for frac in fracs:
        try:
            out = C10.relocate_b10km_down(
                parent, foot, edt_cat, ridge_union, density,
                n_move=n_move, dest_block_frac=frac, unique_credit_dots=u_cred)
            return frac, out
        except ValueError as exc:  # capacity or donor/dest overlap at this fraction
            last = exc
    raise SystemExit(f"b10km-down could not place {n_move} dots at any fraction {fracs}: {last}")


def _try_up(parent, foot, edt_cat, ridge_union, prior_blocks, *, n_move, u_cred, fracs):
    last = None
    for frac in fracs:
        try:
            out = C5.relocate_5km_ridge_up(
                parent, foot, edt_cat, ridge_union, prior_blocks,
                n_move=n_move, block_px=BLOCK_PX, dest_block_frac=frac,
                unique_credit_dots=u_cred)
            return frac, out
        except ValueError as exc:
            last = exc
    raise SystemExit(f"b10km-ridge-up could not place {n_move} dots at any fraction {fracs}: {last}")


def run_fold_fair_proxy(d28_unmasked, footprint, catalogue, *, ridge_union, tmi_up150,
                        down_frac: float) -> dict:
    """Symmetric fold-fair PROXY for the b10km arms (resolves IR-86-SPACING-05).

    Per buffered whole-component fold, R0 AND every arm are rebuilt strictly
    from ``f.visible``: the density prior comes from the fold-fair R0 itself,
    the Faulds prior and the ``> 3.0 px`` collar from ``f.visible`` only.
    """
    folds = g86inst.build(footprint, catalogue, seed=20, hide_frac=0.20,
                          buffer_px=3, boundary_px=12)
    arm_keys = ("R0", "b10km-down8", "b10km-down4", "b10km-ridge-up8")
    terms_by_arm: dict[str, np.ndarray | None] = {k: None for k in arm_keys}
    fold_details = []
    rdg_topo_cached = C5.skeleton_tips_and_junctions(ridge_union & footprint)
    tmi_ga_cached = C5.local_agc_gradient(tmi_up150, footprint, window_px=101)

    for f in folds:
        vis = f.visible & footprint
        edt_vis = ndi.distance_transform_edt(~vis)
        r0_f = d28_unmasked & footprint & (edt_vis > 2.0)
        u_cred_f, _ = mass_econ.marginal_credit(r0_f)
        n8 = int(round(0.08 * int(r0_f.sum())))
        n4 = int(round(0.04 * int(r0_f.sum())))

        dens_f = C10.occupied_density_blocks(r0_f, footprint, block_px=BLOCK_PX)
        frac_f, (_, _, _, _) = down_frac, (None, None, None, None)
        got8 = None
        for frac in (down_frac,) + tuple(x for x in DOWN_FRAC_LADDER if x != down_frac):
            try:
                got8 = C10.relocate_b10km_down(
                    r0_f, footprint, edt_vis, ridge_union, dens_f,
                    n_move=n8, dest_block_frac=frac, unique_credit_dots=u_cred_f)
                frac_f = frac
                break
            except ValueError:
                continue
        if got8 is None:
            raise SystemExit(f"fold {f.name}: b10km-down8 capacity exhausted at all fractions")
        down8_f = got8[0]
        down4_f, _, _, _ = C10.relocate_b10km_down(
            r0_f, footprint, edt_vis, ridge_union, dens_f,
            n_move=n4, dest_block_frac=frac_f, unique_credit_dots=u_cred_f)

        p10_f = C5.faulds_5km_block_prior(
            footprint, vis, ridge_union, tmi_up150, block_px=BLOCK_PX,
            precomputed_ridge_topo=rdg_topo_cached,
            precomputed_tmi_grad_agc=tmi_ga_cached)
        _, (up8_f, _, _, _) = _try_up(
            r0_f, footprint, edt_vis, ridge_union, p10_f["prior_blocks"],
            n_move=n8, u_cred=u_cred_f, fracs=UP_FRAC_LADDER)

        rasters = {"R0": r0_f, "b10km-down8": down8_f,
                   "b10km-down4": down4_f, "b10km-ridge-up8": up8_f}
        f_scores = {}
        for aname, arr in rasters.items():
            res, t_arr = evaluate_holdout.evaluate(
                arr.astype(np.float32), f.fold, f.fold["region"] & footprint,
                origin=(0, 0), global_shape=arr.shape)
            terms_by_arm[aname] = t_arr if terms_by_arm[aname] is None else terms_by_arm[aname] + t_arr
            f_scores[aname] = round(float(res["dti"]), 6)
        fold_details.append(dict(fold=f.name, n_truth_px=int(f.truth.sum()),
                                 n_r0_dots=int(r0_f.sum()), down_dest_frac=frac_f,
                                 dti=f_scores))

    base = evaluate_holdout.pooled_summary(
        {k: v for k, v in terms_by_arm.items() if v is not None},
        draws=1000, seed=520810, candidate="R0")
    out: dict = {
        "protocol": (
            "buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12) + "
            "symmetric fold-fair d28 rebuild for BOTH R0 and every b10km arm"),
        "evidence_class": "PROXY",
        "contamination": "NONE (R0, density prior, Faulds prior and collars see only f.visible per fold)",
        "n_withheld_positive_pixels": int(base["scores"]["R0"]["withheld_positive_pixels"]),
        "n_bootstrap_clusters_20km": int(base["bootstrap"]["clusters"]),
        "R0": dict(dti=round(float(base["scores"]["R0"]["dti"]), 6),
                   ci95=[round(float(x), 6) for x in base["scores"]["R0"]["ci95"]],
                   n_truth=int(base["scores"]["R0"]["withheld_positive_pixels"])),
        "folds": fold_details,
        "arms": {},
    }
    for key in arm_keys[1:]:
        s = evaluate_holdout.pooled_summary(
            {"R0": terms_by_arm["R0"], key: terms_by_arm[key]},
            draws=1000, seed=520810, candidate=key)
        row, diff = s["scores"][key], s["paired_differences"]["R0"]
        out["arms"][key] = dict(
            dti=round(float(row["dti"]), 6),
            ci95=[round(float(x), 6) for x in row["ci95"]],
            delta_vs_R0=round(float(diff["delta"]), 6),
            delta_ci95=[round(float(x), 6) for x in diff["ci95"]],
            n_truth=int(row["withheld_positive_pixels"]),
            evidence_class="PROXY")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default="releases")
    ap.add_argument("--stamp", default="20261023")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    if not PREREG_JSON.is_file():
        raise SystemExit("pre-registration missing: registry/preregistration_conc10.json must exist before building")
    prereg = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    if {a["value"] for a in prereg["arms"]} != {v["value"] for v in SPECS.values()}:
        raise SystemExit("SPECS do not match the pre-registered arms; stop")

    print("[1/7] Verifying bridge, parent, and manifest SHA-256 pins...", flush=True)
    pins = verify_pins()
    manifest_pins = verify_manifest_pins(PINNED_INPUTS)

    print("[2/7] Rebuilding R0 byte-for-byte + verifying unmasked d28 lineage...", flush=True)
    g = g57grid.load_grid(BRIDGE)
    foot, cat = np.asarray(g.footprint, bool), np.asarray(g.catalogue, bool)
    base_d28_solo = read(PARENT_FILE.parent / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif")
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

    print("[3/7] Computing 10 km density + Faulds priors; measuring R0 block CVs...", flush=True)
    bd = ax_bands.load_bands()
    tmi_u8_masked = np.where((bd["tmi_up150"] > 0) & foot, bd["tmi_up150"], np.nan)
    density10 = C10.occupied_density_blocks(parent, foot, block_px=BLOCK_PX)
    prior_10km = C5.faulds_5km_block_prior(foot, cat, ridge_union, tmi_u8_masked, block_px=BLOCK_PX)
    cv_parent = {f"cv_{km}km": C5.block_density_stats(parent, foot, px)
                 for km, px in ((1, 10), (5, 50), (10, 100))}
    print("      R0 occupied density CVs:", {k: v["density_cv_occupied"] for k, v in cv_parent.items()}, flush=True)
    print(f"      occupied 10 km blocks (valid): {density10['n_valid_blocks']}", flush=True)

    print("[4/7] Building 3 controlled b10km variants + matched random control...", flush=True)
    u_cred_r0, u_cred_info = mass_econ.marginal_credit(parent)
    down_frac, (down8_dots, src8, dst8, down8_stats) = _try_down(
        parent, foot, edt_cat, ridge_union, density10,
        n_move=SPECS["b10km-down8"]["n_move"], u_cred=u_cred_r0, fracs=DOWN_FRAC_LADDER)
    down4_dots, src4, dst4, down4_stats = C10.relocate_b10km_down(
        parent, foot, edt_cat, ridge_union, density10,
        n_move=SPECS["b10km-down4"]["n_move"], dest_block_frac=down_frac,
        unique_credit_dots=u_cred_r0)
    up_frac, (up8_dots, src_u8, dst_u8, up8_stats) = _try_up(
        parent, foot, edt_cat, ridge_union, prior_10km["prior_blocks"],
        n_move=SPECS["b10km-ridge-up8"]["n_move"], u_cred=u_cred_r0, fracs=UP_FRAC_LADDER)
    up8_stats["dest_block_frac"] = float(up_frac)
    up8_stats["block_px"] = BLOCK_PX
    ctl_dots, ctl_stats = C5.relocate_5km_random_control(
        parent, foot, edt_cat, ridge_union, prior_10km["valid_blocks"],
        n_move=SPECS["b10km-down8"]["n_move"], block_px=BLOCK_PX,
        unique_credit_dots=u_cred_r0)

    if not np.array_equal(src4, src8[:len(src4)]) or not np.array_equal(dst4, dst8[:len(dst4)]):
        raise SystemExit("Nesting invariant broken: b10km-down4 is not an exact prefix of b10km-down8")

    built = {
        "b10km-down8": dict(spec=SPECS["b10km-down8"], dots=down8_dots, stats=down8_stats),
        "b10km-down4": dict(spec=SPECS["b10km-down4"], dots=down4_dots, stats=down4_stats),
        "b10km-ridge-up8": dict(spec=SPECS["b10km-ridge-up8"], dots=up8_dots, stats=up8_stats),
    }
    for key, card in built.items():
        st = card["stats"]
        st["cv_10km_parent"] = cv_parent["cv_10km"]
        st["cv_10km_variant"] = C5.block_density_stats(card["dots"], foot, BLOCK_PX)
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
        print(f"      {key:18s}: moved={st['n_added']} ({st['pct_changed']}% changed), "
              f"10km_CV={st['cv_10km_variant']['density_cv_occupied']:.4f}, "
              f"5km_CV={st['cv_5km_variant']['density_cv_occupied']:.4f}, "
              f"1km_CV={st['cv_1km_variant']['density_cv_occupied']:.4f}, "
              f"ridge_frac={st['added_on_ancestor_ridge_fraction']:.3f}, "
              f"min_cat_px={st['min_added_cat_clearance_px']:.3f}", flush=True)

    print("[5/7] Running report-only instruments (canary, SGMC MODEL, fold-fair PROXY)...", flush=True)
    surrogate, sgmc_info = sgmc_surrogate(cat, foot)
    dens_px = C5.expand_blocks_to_pixels(
        np.where(density10["valid_blocks"], density10["density_blocks"], 0.0), foot.shape, BLOCK_PX)
    canary_features = {
        "prior_10km_px": prior_10km["prior_px"],
        "density_10km_px": dens_px,
        "cat_tips_junc_30km": prior_10km["cat_loci_map"],
        "ridge_tips_junc_10km": prior_10km["rdg_loci_map"],
        "tmi_agc": prior_10km["tmi_agc"],
        "tmi_grad": prior_10km["tmi_grad"],
    }
    canaries = run_leakage_canary(canary_features, foot, cat, surrogate, edt_cat)
    worst_auc = max(v["max_auc"] for v in canaries.values())
    print(f"      Leakage canary max single-feature AUC = {worst_auc:.4f} (threshold <= 0.90)", flush=True)
    if worst_auc > 0.90:
        raise SystemExit(f"STOP: single-feature leakage canary reached AUC {worst_auc:.4f} > 0.90")

    quads = quadrant_masks(foot)
    eval_arms = {k: v["dots"] for k, v in built.items()}
    eval_arms["CONTROL-b10km-rand8"] = ctl_dots
    model = {k: evaluate_surrogate(parent, arr, surrogate, foot, cat, quads)
             for k, arr in eval_arms.items()}
    for k, m in model.items():
        print(f"      MODEL SGMC {k:24s}: delta={m['all']['delta']:+.6f} "
              f"(quads +:{m['sign_replication']['n_positive']}/4 "
              f"[{m['sign_replication']['quadrant_range'][0]:+.5f}..{m['sign_replication']['quadrant_range'][1]:+.5f}], "
              f"jitter6px mean={m['jitter_6px_ensemble']['mean_delta']:+.6f})", flush=True)

    proxy_fold_fair = run_fold_fair_proxy(
        d28, foot, cat, ridge_union=ridge_union, tmi_up150=tmi_u8_masked, down_frac=down_frac)
    for k, pv in proxy_fold_fair["arms"].items():
        print(f"      PROXY fold-fair {k:24s}: DTI={pv['dti']:.6f}, "
              f"delta_vs_R0={pv['delta_vs_R0']:+.6f}, CI95={pv['delta_ci95']}, n_truth={pv['n_truth']}", flush=True)
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
                if (row.get("sha256") and not (
                        row.get("axis", "").upper() == AXIS
                        and row.get("value", "") in own_values
                        and not row.get("receipt_score"))):
                    existing_shas.add(row["sha256"])
    existing_shas |= {sha256(p) for p in FLEET.glob("*.tif")}
    if (ROOT / "docs" / "downloads").is_dir():
        existing_shas |= {sha256(p) for p in (ROOT / "docs" / "downloads").glob("*.tif")}

    profile = serialization_profile(None)
    git_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, check=False).stdout.strip()
    written_receipts, ledger_entries = [], []
    slug_map = {"b10km-down8": "b10kmdown8", "b10km-down4": "b10kmdown4",
                "b10km-ridge-up8": "b10kmup8"}

    for key, card in built.items():
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

        m_all, m_sr = model[key]["all"], model[key]["sign_replication"]
        p_ff = proxy_fold_fair["arms"][key]
        predicted = (
            f"{m_all['delta']:+.4f} (quadrant range {m_sr['quadrant_range'][0]:+.4f}.."
            f"{m_sr['quadrant_range'][1]:+.4f}; {m_sr['n_positive']}/4 quadrants positive; "
            f"fold-fair PROXY {p_ff['delta_vs_R0']:+.4f}, CI95 [{p_ff['delta_ci95'][0]:+.4f},"
            f"{p_ff['delta_ci95'][1]:+.4f}], n={p_ff['n_truth']}). MODEL: SGMC-extra surrogate, not a score.")
        note = (
            f"R0 {PARENT_ID}; CONC {key}: {st['n_added']} ridge dots moved "
            f"({st['pct_changed']:.2f}% chg, 10km CV {st['cv_10km_variant']['density_cv_occupied']:.3f}); "
            f"pred {m_all['delta']:+.4f} MODEL")[:140]

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

        disk_z, disk_n = read(zeros_path), read(nan_path)
        if not np.array_equal(disk_z > 0.5, dots) or not np.array_equal(np.isfinite(disk_n) & (disk_n > 0.5), dots):
            raise SystemExit(f"{key}: on-disk re-read mismatch against in-memory dot set")
        if not np.all(np.isnan(disk_n[~foot])) or np.any(np.isnan(disk_n[foot])):
            raise SystemExit(f"{key}: NaN twin outside/inside footprint contract violated")
        if z_sha in existing_shas or nan_sha in existing_shas:
            raise SystemExit(f"{key}: exact sha256 collision with existing ledger/fleet file")
        existing_shas |= {z_sha, nan_sha}

        receipt = dict(
            id=cid, parent=PARENT_ID, axis=AXIS, value=card["spec"]["value"],
            role="candidate", n_dots=int(dots.sum()), pct_changed=st["pct_changed"],
            dot_digest=PRUNE.dot_digest(dots), concentration_stats=st,
            zeros=dict(file=zeros_path.name, sha256=z_sha, bytes=zeros_path.stat().st_size,
                       primary_for_upload=True, validator=v_zero,
                       format_report_ok=rep_zero["ok"]),
            nan=dict(file=nan_path.name, mode="nan", sha256=nan_sha,
                     bytes=nan_path.stat().st_size,
                     in_footprint_checks_pass=not nan_fail, failed_checks=nan_fail,
                     policy_note="brief v2 spec form (NaN outside footprint); -zeros is portal fallback"),
            submission_name=cid[:140], note=note, predicted_live_change=predicted,
            model_delta_sgmc=m_all["delta"], proxy_fold_fair=p_ff,
            evidence_class="MODEL", approved_for_weekly_slot=False, submission_slots_used=0,
            provenance=dict(input_pins=pins, manifest_pins=manifest_pins,
                            parent_rebuild=rebuild, git_sha=git_sha,
                            preregistration="registry/preregistration_conc10.json"),
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        zeros_path.with_suffix(".json").write_text(
            json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        written_receipts.append(receipt)

        ledger_entries.append(dict(
            id=cid, site="GEMSDOE86", axis=AXIS, value=card["spec"]["value"],
            status="BUILT", n_dots=int(dots.sum()), pct_changed=st["pct_changed"],
            sha8=sha8, parent=PARENT_ID, encoding="zeros",
            sha256_zeros=z_sha, sha256_nan=nan_sha, predicted_change=predicted,
            source_url=f"releases/{zeros_path.name}", receipt_score="", receipt_date="",
            dot_digest=receipt["dot_digest"],
            files=[f"releases/{nan_path.name}", f"releases/{zeros_path.name}"],
            form_note=note, gate_all_pass=True,
            proxy=dict(value=p_ff["dti"], delta_vs_r0=p_ff["delta_vs_R0"],
                       ci95=p_ff["delta_ci95"],
                       n_withheld_positive_pixels=p_ff["n_truth"], class_="PROXY",
                       note=proxy_fold_fair["contamination"])))
        print(f"      {cid}: MUST gates PASS | zeros={z_sha[:8]} | nan={nan_sha[:8]}", flush=True)

    print("[7/7] Writing master evidence card and ledger/variants_concentration_10km.json...", flush=True)
    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        elapsed_seconds=round(time.time() - t0, 2),
        axis=AXIS, axis_assignment=AXIS_ASSIGNMENT, block_px=BLOCK_PX,
        preregistration=prereg,
        parent=dict(id=PARENT_ID, n_dots=N_DOTS_R0, claimed_live_dti=0.2778,
                    claimed_evidence_class="CLAIM", rebuild=rebuild,
                    d28_lineage_exact=True, unique_kernel_credit_summary=u_cred_info,
                    block_density_cv_parent=cv_parent),
        design_notes=dict(
            down_dest_block_frac=down_frac, up_dest_block_frac=up_frac,
            down_frac_ladder=list(DOWN_FRAC_LADDER), up_frac_ladder=list(UP_FRAC_LADDER),
            nesting_verified_down4_in_down8=True,
            density_valid_occupied_10km_blocks=density10["n_valid_blocks"],
            faulds_10km_counts=prior_10km["counts"],
            faulds_10km_quadrant_balance=prior_10km["quadrant_balance"],
            ir86_trackb08_cv_note=(
                "IR-86-TRACKB-08 reports R0 10 km CV = 0.570; canonical "
                "block_density_stats (occupied blocks, density per footprint cell) "
                "measures 0.736 complete-block / 0.733 padded-block this session. "
                "See IR-86-CONC-19.")),
        variants=written_receipts,
        null_control_not_promoted={
            "CONTROL-b10km-rand8": dict(
                description="Random 10 km block prior on the same ancestor ridge pool (3,012 dots moved, seed 20261023)",
                stats=ctl_stats, model_sgmc=model["CONTROL-b10km-rand8"])},
        report_only_instruments=dict(
            note="Brief v2 sec 6: report-only instruments; no candidate was gated or tuned on them.",
            leakage_canary=canaries, sgmc_surrogate_info=sgmc_info, sgmc_model=model,
            hide_and_recover_proxy_fold_fair=proxy_fold_fair,
            hide_and_recover_proxy_static=proxy_static),
        submission_slots_used=0)
    if not args.no_write:
        EVIDENCE_JSON.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        VARIANTS_JSON.write_text(json.dumps(ledger_entries, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"      Wrote {EVIDENCE_JSON.relative_to(ROOT)} and {VARIANTS_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
