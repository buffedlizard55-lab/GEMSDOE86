#!/usr/bin/env python3
"""CONCENTRATION dose ladder & block-scale replication on R0 (brief v2 session, 2026-10-23).

One axis, three builds, one matched control.

The parent is **R0 = `h33-h33-2-b2`** (GEMSDOE32, 37,654 unit-mass dots, claimed live 0.2778 =
CLAIM).  The rule under test is PR #47's `b5km-cvband-down4`: shave the lowest unique-kernel-credit
dot out of over-dense 1 km blocks and re-emit it on an unused pinned ancestor ridge cell
(`H19-5 | H19-4 | H16-1`) inside a sparse 1-2 dot block.  That arm is the only CONCENTRATION build
positive on both report-only instruments (SGMC MODEL +0.0015; fold-fair PROXY +0.0008).

This session changes ONE thing at a time across the three builds:

* ``cvband-down3``      — 1 km blocks, 3 % of R0 moved (brackets the CV-band peak from below);
* ``cvband-down5``      — 1 km blocks, 5 % of R0 moved (PR #47 dose + 1 %);
* ``cvband-down6``      — 1 km blocks, 6 % of R0 moved (1.5x the PR #47 dose; near the ceiling);
* ``CONTROL-cvband-down6-randcredit`` — same source blocks as ``down6`` with random dot choice and
  random destination order (measured, never promoted).

Two pre-registered arms are **infeasible on this parent** and are replaced by a lower dose
(``IR-86-CONC-12``): the 1 km sparse-ridge destination pool exhausts after 2,399 placements (8 % is
impossible) and the 2 km pool after 920 (4 % is impossible).  The ladder is therefore
3 % / 4 % (PR #47) / 5 % / 6 % on the same 1 km rule, and the two capacity ceilings are reported as
results rather than hidden.

Count is fixed at 37,654 on every arm, no arm emits mass on the catalogue, every newly emitted dot
is ``> 3.0 px`` from the catalogue and ``>= sqrt(8) px`` from its neighbours, and 100 % of new dots
sit on the pinned ancestor ridge union.

No truth raster, no portal, no login, no submission.  Predictions are pre-registered in
``evidence/concentration-dose-mechanism.md``; the SGMC surrogate and the catalogue
hide-and-recover instrument are REPORT-ONLY and are never called a score.

Usage
-----
    .venv/bin/python scripts/run_concentration_dose.py [--no-write] [--stamp 20261023]
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
from run_concentration_5km import (  # noqa: E402
    evaluate_surrogate,
    quadrant_masks,
    run_leakage_canary,
    sgmc_surrogate,
    verify_manifest_pins,
)
from gems57 import evaluate_holdout, grid as g57grid  # noqa: E402
from gems57.gates import format_report  # noqa: E402
from gems57.validate import validate  # noqa: E402
from gems86 import concentration_5km as C5, instrument as g86inst, mass_econ, prune as PRUNE  # noqa: E402

MANIFEST = ROOT / "registry" / "data_manifest.json"
FLEET = ROOT / "data" / "scored_fleet"
CACHE_SCORED = ROOT / ".cache" / "gems_data" / "scored"
CACHE_EXT = ROOT / ".cache" / "gems_data" / "external"
EVIDENCE_JSON = ROOT / "evidence" / "concentration_dose_20261023.json"
VARIANTS_JSON = ROOT / "ledger" / "variants_concentration_dose.json"

AXIS = "CONCENTRATION"
N_DOTS_R0 = 37654
MIN_PCT, MAX_PCT = 1.0, 50.0
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

SLUG = {
    "cvband-down5": "conc5dose",
    "cvband-down6": "conc6",
    "cvband-down3": "conc3",
    "CONTROL-cvband-down6-randcredit": "conc6rand",
}

#: Pre-registered predictions (evidence/concentration-dose-mechanism.md), written before the run.
PREREG = {
    # preregistered 2026-10-23 in evidence/concentration-dose-mechanism.md, before any build
    "cvband-down5": dict(predicted=0.0017, lo=-0.0023, hi=0.0057,
                         amended_from="cvband-down8 (infeasible: destination capacity 2,399 < 3,012)"),
    "cvband-down6": dict(predicted=0.0015, lo=-0.0025, hi=0.0055),
    "cvband-down3": dict(predicted=0.0016, lo=-0.0024, hi=0.0056,
                         amended_from="cvband-2km-down4 (infeasible: 2 km destination capacity 920 < 1,506)"),
    "CONTROL-cvband-down6-randcredit": dict(predicted=0.0, lo=-0.004, hi=0.004),
}
CONTROL_SEED = 20261023


def fold_fair_proxy(
    d28: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    ridge_union: np.ndarray,
    arms: dict[str, dict],
) -> dict:
    """Symmetric fold-fair hide-and-recover PROXY (REPORT ONLY).

    Both R0 and every arm are rebuilt from ``f.visible`` on each buffered whole-component fold, so
    no withheld catalogue pixel enters either the parent or the candidate geometry.
    """
    folds = g86inst.build(footprint, catalogue, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    keys = ["R0"] + list(arms)
    terms: dict[str, np.ndarray | None] = {k: None for k in keys}
    fold_details = []

    for f in folds:
        vis = f.visible & footprint
        edt_vis = ndi.distance_transform_edt(~vis)
        r0_f = d28 & footprint & (edt_vis > 2.0)
        u_cred_f, _ = mass_econ.marginal_credit(r0_f)
        rasters = {"R0": r0_f}
        for name, spec in arms.items():
            if name.startswith("CONTROL"):
                dots, _, _, _ = C5.relocate_cvband_down_shuffled(
                    r0_f, footprint, edt_vis, ridge_union,
                    n_move=int(round(spec["frac"] * int(r0_f.sum()))),
                    km_block_px=spec["block_px"], seed=CONTROL_SEED, unique_credit_dots=u_cred_f,
                )
            else:
                dots, _, _, _ = C5.relocate_cvband_down(
                    r0_f, footprint, edt_vis, ridge_union,
                    n_move=int(round(spec["frac"] * int(r0_f.sum()))),
                    km_block_px=spec["block_px"], unique_credit_dots=u_cred_f,
                )
            rasters[name] = dots
        f_scores = {}
        for name, arr in rasters.items():
            res, t_arr = evaluate_holdout.evaluate(
                arr.astype(np.float32), f.fold, f.fold["region"] & footprint,
                origin=(0, 0), global_shape=arr.shape,
            )
            terms[name] = t_arr if terms[name] is None else terms[name] + t_arr
            f_scores[name] = round(float(res["dti"]), 6)
        fold_details.append(
            dict(fold=f.name, n_truth_px=int(f.truth.sum()), n_r0_dots=int(r0_f.sum()), dti=f_scores)
        )

    base = evaluate_holdout.pooled_summary(
        {k: v for k, v in terms.items() if v is not None}, draws=1000, seed=520810, candidate="R0"
    )
    out = dict(
        protocol=(
            "buffered_component_draw(seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12); "
            "R0 and every arm rebuilt per fold from f.visible only"
        ),
        evidence_class="PROXY",
        contamination="NONE (per-fold geometry sees only f.visible)",
        n_withheld_positive_pixels=int(base["scores"]["R0"]["withheld_positive_pixels"]),
        R0=dict(
            dti=round(float(base["scores"]["R0"]["dti"]), 6),
            ci95=[round(float(x), 6) for x in base["scores"]["R0"]["ci95"]],
        ),
        folds=fold_details,
        arms={},
    )
    for name in arms:
        s = evaluate_holdout.pooled_summary(
            {"R0": terms["R0"], name: terms[name]}, draws=1000, seed=520810, candidate=name
        )
        row, diff = s["scores"][name], s["paired_differences"]["R0"]
        out["arms"][name] = dict(
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

    print("[1/7] verifying pins", flush=True)
    pins = verify_pins()
    manifest_pins = verify_manifest_pins(PINNED_INPUTS)

    print("[2/7] rebuilding R0 byte-exactly", flush=True)
    g = g57grid.load_grid(BRIDGE)
    foot, cat = np.asarray(g.footprint, bool), np.asarray(g.catalogue, bool)
    d28 = (read(PINNED_INPUTS["scored_d28_unscored"]) > 0.5) & foot
    rebuild = rebuild_parent(g, d28)
    if not (rebuild["content_identical"] and rebuild["byte_identical_sha"]):
        raise SystemExit(f"R0 rebuild gate FAILED: {rebuild}")
    parent = (read(PARENT_FILE) > 0) & foot
    if int(parent.sum()) != N_DOTS_R0 or sha256(PARENT_FILE) != PARENT_SHA:
        raise SystemExit(f"R0 verification mismatch: dots={int(parent.sum())}")
    edt_cat = ndi.distance_transform_edt(~cat)
    if not np.array_equal(d28 & (edt_cat > 2.0), parent):
        raise SystemExit("lineage verification failed: d28 & (edt_cat > 2.0) != R0")
    print(f"      R0 {int(parent.sum())} dots, byte-exact {rebuild['rebuilt_sha256'][:16]}...", flush=True)

    h19_5 = (read(PINNED_INPUTS["scored_h19_5"]) > 0.5) & foot
    h19_4 = (read(PINNED_INPUTS["scored_h19_4"]) > 0.5) & foot
    h16_1 = (read(PINNED_INPUTS["scored_h16_1"]) > 0.5) & foot
    ridge_union = (h19_5 | h19_4 | h16_1) & foot

    print("[3/7] building 3 dose/scale variants + ordering control", flush=True)
    u_cred, u_cred_info = mass_econ.marginal_credit(parent)
    specs = {
        "cvband-down5": dict(frac=0.05, block_px=10, ranked=True),
        "cvband-down6": dict(frac=0.06, block_px=10, ranked=True),
        "cvband-down3": dict(frac=0.03, block_px=10, ranked=True),
        "CONTROL-cvband-down6-randcredit": dict(frac=0.06, block_px=10, ranked=False),
    }
    built: dict[str, dict] = {}
    for name, spec in specs.items():
        n_move = int(round(spec["frac"] * N_DOTS_R0))
        if spec["ranked"]:
            dots, src, dst, st = C5.relocate_cvband_down(
                parent, foot, edt_cat, ridge_union,
                n_move=n_move, km_block_px=spec["block_px"], unique_credit_dots=u_cred,
            )
        else:
            dots, src, dst, st = C5.relocate_cvband_down_shuffled(
                parent, foot, edt_cat, ridge_union,
                n_move=n_move, km_block_px=spec["block_px"], seed=CONTROL_SEED,
                unique_credit_dots=u_cred,
            )
        if not st["count_fixed"] or st["n_dots"] != N_DOTS_R0:
            raise SystemExit(f"{name}: count not fixed at {N_DOTS_R0}")
        if not (MIN_PCT <= st["pct_changed"] <= MAX_PCT):
            raise SystemExit(f"{name}: pct_changed={st['pct_changed']} outside [1,50]")
        if np.any(dots & cat):
            raise SystemExit(f"{name}: positive mass on catalogue")
        if st["min_added_cat_clearance_px"] is None or st["min_added_cat_clearance_px"] <= 3.0:
            raise SystemExit(f"{name}: new mass violates >3.0 px clearance")
        if st["min_pair_distance_variant_px"] < st["min_pair_distance_parent_px"] - 1e-6:
            raise SystemExit(f"{name}: tightened R0's minimum spacing")
        if st["n_added"] != n_move or st["n_removed"] != n_move:
            raise SystemExit(f"{name}: relocation not symmetric ({st['n_removed']}/{st['n_added']})")
        built[name] = dict(spec=spec, dots=dots, stats=st, src=src, dst=dst, n_move=n_move)
        print(
            f"      {name:34s} moved={st['n_added']} ({st['pct_changed']:.2f}% chg) "
            f"1kmCV={st['cv_1km_variant']['density_cv_occupied']:.4f} "
            
            f"min_cat={st['min_added_cat_clearance_px']:.3f}",
            flush=True,
        )

    # dose ladder nesting: the ranked 1 km arms must be prefix-nested (same algorithm, more pops)
    s3, s5, s6 = (built["cvband-down3"]["src"], built["cvband-down5"]["src"],
                  built["cvband-down6"]["src"])
    nesting = dict(
        down3_sources_prefix_of_down5=bool(
            len(s3) <= len(s5) and np.array_equal(np.asarray(s3), np.asarray(s5)[: len(s3)])
        ),
        down5_sources_prefix_of_down6=bool(
            len(s5) <= len(s6) and np.array_equal(np.asarray(s5), np.asarray(s6)[: len(s5)])
        ),
    )
    print(f"      dose-ladder nesting: {nesting}", flush=True)

    print("[4/7] report-only instruments (canary + SGMC MODEL)", flush=True)
    surrogate, sgmc_info = sgmc_surrogate(cat, foot)
    quads = quadrant_masks(foot)
    credit_map = np.zeros(parent.shape, dtype=np.float32)
    ys_p, xs_p = np.nonzero(parent)
    credit_map[ys_p, xs_p] = (u_cred.astype(np.float32) / 9.3803)
    dens1 = C5.expand_blocks_to_pixels(
        C5._block_sum_padded(parent.astype(np.float32), 10)  # noqa: SLF001 - same-module helper
        / np.maximum(C5._block_sum_padded(foot.astype(np.float32), 10), 1.0),  # noqa: SLF001
        foot.shape, 10,
    ).astype(np.float32)
    canary_features = {
        "ridge_union_px": ridge_union.astype(np.float32),
        "unique_credit_parent": credit_map,
        "block_density_1km_parent": dens1,
    }
    canaries = run_leakage_canary(canary_features, foot, cat, surrogate, edt_cat)
    worst = max(v["max_auc"] for v in canaries.values())
    print(f"      leakage canary max single-feature AUC = {worst:.4f} (stop if > 0.90)", flush=True)
    if worst > 0.90:
        raise SystemExit(f"STOP: leakage canary AUC {worst:.4f} > 0.90")

    model = {k: evaluate_surrogate(parent, v["dots"], surrogate, foot, cat, quads) for k, v in built.items()}
    for k, m in model.items():
        print(
            f"      MODEL SGMC {k:34s} delta={m['all']['delta']:+.6f} "
            f"(quads +{m['sign_replication']['n_positive']}/4, jitter6px {m['jitter_6px_ensemble']['mean_delta']:+.6f})",
            flush=True,
        )

    print("[5/7] fold-fair catalogue hide-and-recover PROXY (report only)", flush=True)
    proxy = fold_fair_proxy(d28, foot, cat, ridge_union, specs)
    for k, pv in proxy["arms"].items():
        print(
            f"      PROXY {k:34s} delta={pv['delta_vs_R0']:+.6f} CI95={pv['delta_ci95']}",
            flush=True,
        )

    print("[6/7] MUST gates, twins on disk, receipts", flush=True)
    out_dir = ROOT / args.out_dir
    existing_shas: set[str] = set()
    ledger_csv = ROOT / "ledger" / "submissions.csv"
    own_values = set(SLUG)
    if ledger_csv.exists():
        with open(ledger_csv, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("sha256") and not (
                    row.get("axis", "").upper() == AXIS and row.get("value", "") in own_values and not row.get("receipt_score")
                ):
                    existing_shas.add(row["sha256"])
    existing_shas |= {sha256(p) for p in FLEET.glob("*.tif")}
    if (ROOT / "docs" / "downloads").is_dir():
        existing_shas |= {sha256(p) for p in (ROOT / "docs" / "downloads").glob("*.tif")}
    if out_dir.is_dir():
        existing_shas |= {sha256(p) for p in out_dir.glob("*.tif")}

    profile = serialization_profile(None)
    git_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()
    receipts, ledger_entries = [], []

    for name, card in built.items():
        dots, st = card["dots"], card["stats"]
        field_zeros = np.where(foot, dots.astype(np.float32), np.float32(0.0)).astype(np.float32)
        probe = Path(tempfile.mkdtemp()) / "probe.tif"
        with rasterio.open(probe, "w", **profile) as dst:
            dst.write(field_zeros, 1)
        sha8 = sha256(probe)[:8]
        shutil.rmtree(probe.parent, ignore_errors=True)
        role = "control" if name.startswith("CONTROL") else "candidate"
        cid = f"{PARENT_ID}-{SLUG[name]}-{args.stamp}-{sha8}"
        zeros_path = out_dir / f"{cid}-zeros.tif"
        nan_path = out_dir / f"{cid}.tif"

        m_all = model[name]["all"]
        m_sr = model[name]["sign_replication"]
        p_ff = proxy["arms"][name]
        cv1 = st["cv_1km_variant"]["density_cv_occupied"]
        cv2 = C5.block_density_stats(dots, foot, 20)["density_cv_occupied"]
        predicted = (
            f"{m_all['delta']:+.4f} MODEL (SGMC off-catalogue surrogate; quadrant range "
            f"{m_sr['quadrant_range'][0]:+.4f}..{m_sr['quadrant_range'][1]:+.4f}; "
            f"{m_sr['n_positive']}/4 quadrants positive; jitter6px mean "
            f"{model[name]['jitter_6px_ensemble']['mean_delta']:+.4f}); "
            f"fold-fair PROXY {p_ff['delta_vs_R0']:+.4f} "
            f"[{p_ff['delta_ci95'][0]:+.4f}, {p_ff['delta_ci95'][1]:+.4f}], n={p_ff['n_truth']}. "
            f"Not a score."
        )
        note = (
            f"R0 {PARENT_ID}; CONC {name}: {st['n_added']} ridge dots moved "
            f"({st['pct_changed']:.2f}% chg; 1km CV {cv1:.3f}); pred {m_all['delta']:+.4f} MODEL"
        )[:140]

        if args.no_write:
            receipts.append(dict(id=cid, note=note, predicted_change=predicted, dry_run=True))
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        nan_arr = np.where(foot, dots.astype(np.float32), np.float32(np.nan)).astype(np.float32)
        nan_sha = write_with_profile(nan_path, nan_arr, float("nan"))
        z_sha = write_with_profile(zeros_path, field_zeros, None)
        if z_sha[:8] != sha8:
            raise SystemExit(f"{name}: probed sha8 {sha8} != written {z_sha[:8]}")
        v_zero = validate(zeros_path, foot, cat)
        rep = format_report(zeros_path, BRIDGE / "sample_submission.tif", footprint=foot)
        v_nan = validate(nan_path, foot, cat)
        nan_fail = [k for k, ok in v_nan["checks"].items() if not ok and k not in NAN_POLICY_CHECKS]
        if not v_zero["all_checks_passed"] or not rep["ok"]:
            raise SystemExit(f"{name}: zeros twin failed MUST gates: {rep['problems']}")
        if nan_fail:
            raise SystemExit(f"{name}: NaN twin failed in-footprint gates: {nan_fail}")
        disk_z, disk_n = read(zeros_path), read(nan_path)
        if not np.array_equal(disk_z > 0.5, dots) or not np.array_equal(np.isfinite(disk_n) & (disk_n > 0.5), dots):
            raise SystemExit(f"{name}: on-disk re-read mismatch")
        if not np.all(np.isnan(disk_n[~foot])) or np.any(np.isnan(disk_n[foot])):
            raise SystemExit(f"{name}: NaN contract violated")
        if z_sha in existing_shas or nan_sha in existing_shas:
            raise SystemExit(f"{name}: exact sha256 collision with an existing file")
        existing_shas |= {z_sha, nan_sha}

        receipt = dict(
            id=cid,
            role=role,
            parent=PARENT_ID,
            axis=AXIS,
            value=name,
            n_dots=int(dots.sum()),
            pct_changed=st["pct_changed"],
            dot_digest=PRUNE.dot_digest(dots),
            preregistered=PREREG[name],
            concentration_stats=st,
            cv_2km_variant=C5.block_density_stats(dots, foot, 20),
            zeros=dict(file=zeros_path.name, sha256=z_sha, bytes=zeros_path.stat().st_size,
                       primary_for_upload=True, validator=v_zero, format_report_ok=rep["ok"]),
            nan=dict(file=nan_path.name, mode="nan", sha256=nan_sha, bytes=nan_path.stat().st_size,
                     in_footprint_checks_pass=not nan_fail, failed_checks=nan_fail,
                     policy_note="brief v2 §6/§7 spec form; -zeros is the portal fallback"),
            submission_name=cid[:140],
            note=note,
            predicted_live_change=predicted,
            model_delta_sgmc=m_all["delta"],
            proxy_fold_fair=p_ff,
            evidence_class="MODEL",
            approved_for_weekly_slot=False,
            submission_slots_used=0,
            provenance=dict(input_pins=pins, manifest_pins=manifest_pins, parent_rebuild=rebuild, git_sha=git_sha),
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        zeros_path.with_suffix(".json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        receipts.append(receipt)
        ledger_entries.append(dict(
            id=cid, site="GEMSDOE86", axis=AXIS, value=name,
            status="BUILT" if role == "candidate" else "CONTROL",
            n_dots=int(dots.sum()), pct_changed=st["pct_changed"], sha8=sha8, parent=PARENT_ID,
            encoding="zeros", sha256_zeros=z_sha, sha256_nan=nan_sha,
            predicted_change=predicted, source_url=f"releases/{zeros_path.name}",
            receipt_score="", receipt_date="", dot_digest=receipt["dot_digest"],
            files=[f"releases/{nan_path.name}", f"releases/{zeros_path.name}"], form_note=note,
            gate_all_pass=True,
            proxy=dict(value=p_ff["dti"], delta_vs_r0=p_ff["delta_vs_R0"], ci95=p_ff["delta_ci95"],
                       n_withheld_positive_pixels=p_ff["n_truth"], class_="PROXY",
                       note=proxy["contamination"]),
        ))
        print(f"      {cid}: gates PASS zeros={z_sha[:8]} nan={nan_sha[:8]} 1kmCV={cv1:.4f} 2kmCV={cv2:.4f}", flush=True)

    print("[7/7] writing evidence card + ledger JSON", flush=True)
    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        elapsed_seconds=round(time.time() - t0, 2),
        axis=AXIS,
        axis_assignment="SELF-ASSIGNED (brief v2 §1). Extends PR #47's only CONCENTRATION arm positive on both instruments.",
        parent=dict(id=PARENT_ID, n_dots=N_DOTS_R0, claimed_live_dti=0.2778, claimed_evidence_class="CLAIM",
                    rebuild=rebuild, d28_lineage_exact=True, unique_kernel_credit_summary=u_cred_info),
        preregistration=dict(file="evidence/concentration-dose-mechanism.md", predictions=PREREG,
                             note="written before any build in this session ran"),
        dose_ladder_nesting=nesting,
        variants=receipts,
        report_only_instruments=dict(
            note="brief v2 §6: report-only, never gates, never a score",
            leakage_canary=canaries,
            sgmc_surrogate_info=sgmc_info,
            sgmc_model=model,
            hide_and_recover_proxy_fold_fair=proxy,
            hide_and_recover_proxy_static={k: proxy_dti(parent.astype(np.float32), cat, foot) for k in ("R0",)},
        ),
        submission_slots_used=0,
    )
    if not args.no_write:
        EVIDENCE_JSON.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        VARIANTS_JSON.write_text(json.dumps(ledger_entries, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"      wrote {EVIDENCE_JSON.relative_to(ROOT)} and {VARIANTS_JSON.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
