#!/usr/bin/env python3
"""Execute preregistered lane H86P-PFA (paired-flank multi-physics asymmetry).

Frozen in research/H86P_PFA_PREREGISTRATION.md / .json before implementation.
main() calls the literal protocol stop first (historical-builder guard); the
recorded 2026-10-26 execution calls run_pa86_lane() under PA-86-01/02
(AGENTS.md rule 10) and therefore runs require_like_for_like plus the full
surface + final-dot registry checks. That recorded execution is a historical
receipt, not a protocol exemption for reruns.
"""
from __future__ import annotations

from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
VENDOR = ROOT / "vendor"
for _p in (str(ROOT), str(SRC), str(VENDOR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gems57 import evaluate_holdout as EH, grid, holdout, submission_writer, validate  # noqa: E402
from gems86_ewcs.features import compute_elastic_fields  # noqa: E402
from gems86_pfa.features import BASELINE_NAMES, PFA_NAMES, STATIC_NAMES, build_static_stack  # noqa: E402
from gems86_slcq.model import calibrate_footprint_quadrant_posterior  # noqa: E402
from gems86_stdp.dinkelbach_celf import dinkelbach_celf_allocate_dots  # noqa: E402
from gems86_stdp.model import rank01_on_mask  # noqa: E402
from gems57.holdout import DOMAIN_ERODE, quadrant_ids  # noqa: E402
from scripts.protocol_preflight import require_like_for_like  # noqa: E402
from scripts.run_h86k_stdp import (  # noqa: E402
    BUDGET, COLLAR_PX, H33_TIF, SPACING_PX,
    audit_informative_dot_field_firings, evaluate_sgmc_proxy, load_binary_tif,
    prepare_canary_indices, registry_summary, run_chance_check, run_registry_check,
    score_canary_array, sha256, write_candidate,
)

CACHE_DIR = ROOT / ".cache/h86p_pfa"
EV_DIR = ROOT / "docs/evidence"
FEATURE_TIF = ROOT / "data/bridge/training_features.tif"
PREREG_JSON = ROOT / "research/H86P_PFA_PREREGISTRATION.json"
ELASTIC_NAMES = ("wing_crack_lobe", "collinear_tip_cone", "stepover_bridge",
                 "broadside_stress_shadow", "iso_tip_halo")
SEED = 865620
N_NEG = 160_000
N_POS_CAP = 60_000
ARM_E1 = "E1_pfa_candidate"
ARM_E2 = "E2_pfa_blind"
ARM_E3 = "E3_baseline_ablation"


def _rows(X, static_idx, elast, elast_names, flat):
    H, W = X.shape[1], X.shape[2]
    ys, xs = np.divmod(flat, W)
    cols = [X[i][ys, xs].astype(np.float32) for i in static_idx]
    if elast is not None:
        cols += [elast[k][ys, xs].astype(np.float32) for k in elast_names]
    return np.column_stack(cols) if cols else np.empty((flat.size, 0), np.float32)


def fit_predict_loqo(X, static_idx, elast, elast_names, vis, fp, seed_offset=0):
    """Strict LOQO HGB PU surface: quadrant q predicted by a model trained only
    on the 12-px-eroded complement of q, labels = vis catalogue only."""
    quad = quadrant_ids(fp)
    d_vis = ndi.distance_transform_edt(~vis)
    out = np.zeros(fp.shape, dtype=np.float32)
    for q in range(4):
        train_dom = ndi.binary_erosion((quad >= 0) & (quad != q), iterations=DOMAIN_ERODE) & fp
        rng = np.random.default_rng(SEED + seed_offset + q)
        pos = np.flatnonzero((vis & train_dom).ravel())
        if pos.size > N_POS_CAP:
            pos = rng.choice(pos, N_POS_CAP, replace=False)
        neg_pool = np.flatnonzero((train_dom & (d_vis > 8.0)).ravel())
        neg = rng.choice(neg_pool, min(N_NEG, neg_pool.size), replace=False)
        flat = np.r_[pos, neg]
        y = np.r_[np.ones(pos.size, np.int8), np.zeros(neg.size, np.int8)]
        Xtr = _rows(X, static_idx, elast, elast_names, flat)
        clf = HistGradientBoostingClassifier(
            max_iter=250, learning_rate=0.06, max_leaf_nodes=31,
            min_samples_leaf=40, l2_regularization=0.1,
            early_stopping=False, random_state=SEED + seed_offset + q)
        clf.fit(Xtr, y)
        del Xtr
        # predict quadrant q in row chunks
        qmask = fp & (quad == q)
        for r0 in range(0, fp.shape[0], 256):
            r1 = min(fp.shape[0], r0 + 256)
            m = qmask[r0:r1]
            if not m.any():
                continue
            ys, xs = np.nonzero(m)
            cols = [X[i][r0 + ys, xs].astype(np.float32) for i in static_idx]
            if elast is not None:
                cols += [elast[k][r0 + ys, xs].astype(np.float32) for k in elast_names]
            out[r0 + ys, xs] = clf.predict_proba(np.column_stack(cols))[:, 1].astype(np.float32)
        print(f"    LOQO q{q}: pos={pos.size} neg={neg.size} pred={int(qmask.sum())}", flush=True)
        del clf
        gc.collect()
    return calibrate_footprint_quadrant_posterior(out, fp, quad)


def allocate(surface, allowed, known, fp):
    return dinkelbach_celf_allocate_dots(
        surface, allowed, known_faults=known, valid=fp,
        budget=BUDGET, min_spacing_px=SPACING_PX, outer_iterations=2)


def run_pa86_lane() -> int:
    t0 = time.time()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)
    print("[1/7] PA-86 preflight + preregistration + input hashes...", flush=True)
    preflight = require_like_for_like()
    prereg = json.loads(PREREG_JSON.read_text())
    input_hashes = {
        "training_features.tif": sha256(FEATURE_TIF),
        "existing_faults.tif": sha256(ROOT / "data/bridge/existing_faults.tif"),
        "sample_submission.tif": sha256(ROOT / "data/bridge/sample_submission.tif"),
        "preregistration_json_sha256": sha256(PREREG_JSON),
        "preregistration_md_sha256": sha256(ROOT / "research/H86P_PFA_PREREGISTRATION.md"),
        "hypotheses_sha256": sha256(ROOT / "registry/h86p_pfa_hypotheses.json"),
    }
    expect = {"training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
              "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
              "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"}
    for k, v in expect.items():
        if input_hashes[k] != v:
            raise ValueError(f"SHA mismatch {k}")
    g = grid.load_grid(ROOT / "data/bridge")
    fp = np.asarray(g.footprint, bool)
    cat = np.asarray(g.catalogue, bool)

    print("[2/7] Static stack (12 baseline + 8 PFA)...", flush=True)
    stack_path = CACHE_DIR / "h86p_static20.npy"
    if stack_path.is_file():
        X = np.load(stack_path, mmap_mode="r")
    else:
        X = build_static_stack(FEATURE_TIF, fp, stack_path)
    static_sha = sha256(stack_path)
    idx = {n: i for i, n in enumerate(STATIC_NAMES)}
    base_idx = tuple(idx[n] for n in BASELINE_NAMES)
    pfa_idx = tuple(idx[n] for n in PFA_NAMES)

    print("[3/7] Canary + holdout arms (gems57-pooled-hide-v2, seed20, buffered whole components)...", flush=True)
    folds, _ = holdout.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    vis_ho = np.asarray(folds[0]["visible"], bool) & fp
    for f in folds[1:]:
        if not np.array_equal(np.asarray(f["visible"], bool) & fp, vis_ho):
            raise AssertionError("visible mask differs across folds")
    elast_ho = compute_elastic_fields(vis_ho, fp)
    p_idx, n_idx, y = prepare_canary_indices(folds, fp)
    canary = {}
    for i, name in enumerate(STATIC_NAMES):
        pl = np.asarray(X[i]).ravel()
        canary[name] = score_canary_array(np.r_[pl[p_idx], pl[n_idx]].astype(np.float64), y)
    for k in ELASTIC_NAMES:
        pl = np.asarray(elast_ho[k]).ravel()
        canary[f"fold_visible_{k}"] = score_canary_array(np.r_[pl[p_idx], pl[n_idx]].astype(np.float64), y)
    flagged = [k for k, v in canary.items() if v["leakage_flag"]]
    if flagged:
        raise RuntimeError(f"STOP leakage canary >0.90: {flagged}")
    wname, wv = max(canary.items(), key=lambda kv: kv[1]["discriminative_auc"])
    print(f"  canary PASS n={len(canary)} worst={wname} {wv['discriminative_auc']:.4f}", flush=True)

    d_vis = ndi.distance_transform_edt(~vis_ho)
    allowed_ho = fp & (d_vis > COLLAR_PX)
    del d_vis
    surfaces, dots_by_arm = {}, {}
    for arm, sidx, elast in ((ARM_E1, base_idx + pfa_idx, elast_ho),
                             (ARM_E2, base_idx + pfa_idx, None),
                             (ARM_E3, base_idx, elast_ho)):
        print(f"  arm {arm}: LOQO fit...", flush=True)
        surf = fit_predict_loqo(X, sidx, elast, ELASTIC_NAMES if elast is not None else (),
                                vis_ho, fp, seed_offset={ARM_E1: 0, ARM_E2: 100, ARM_E3: 200}[arm])
        surfaces[arm] = surf
        alloc = allocate(surf, allowed_ho, vis_ho, fp)
        dots_by_arm[arm] = alloc.dots
        print(f"  arm {arm}: dots={alloc.n_dots} lambda={alloc.final_lambda:.4f} ({time.time()-t0:.0f}s)", flush=True)
        del surf, alloc
        gc.collect()
    h33_mask = load_binary_tif(H33_TIF) & fp
    dots_by_arm["H33_visible_collar"] = h33_mask & allowed_ho
    terms, per_fold = {}, {}
    for arm, dots in dots_by_arm.items():
        tot, pf = None, {}
        for f in folds:
            res, bt = EH.evaluate(dots.astype(np.float32), f, fp, block_side=200)
            tot = bt if tot is None else tot + bt
            pf[f["name"]] = {"evidence_class": "HOLDOUT-DTI", "evaluator_version": EH.VERSION,
                             "dti": res["dti"], "n_truth": res["n_truth"], "emitted": res["n_emitted"]}
        terms[arm] = tot
        per_fold[arm] = pf
    pooled = EH.pooled_summary(terms, draws=1000, seed=SEED, candidate=ARM_E1)
    e1s = pooled["scores"][ARM_E1]
    delta_e3 = pooled["paired_differences"][ARM_E3]
    print(f"  HOLDOUT-DTI E1={e1s['dti']:.4f} {e1s['ci95']} E2={pooled['scores'][ARM_E2]['dti']:.4f} "
          f"E3={pooled['scores'][ARM_E3]['dti']:.4f} dE3={delta_e3['delta']:+.4f} {delta_e3['ci95']} "
          f"H33vc={pooled['scores']['H33_visible_collar']['dti']:.4f}", flush=True)
    del surfaces, dots_by_arm, elast_ho
    gc.collect()

    print("[4/7] Full-catalogue LOQO surface (E1) + pre-placement surface registry scan...", flush=True)
    elast_full = compute_elastic_fields(cat & fp, fp)
    surf_full = fit_predict_loqo(X, base_idx + pfa_idx, elast_full, ELASTIC_NAMES, cat & fp, fp, seed_offset=2000)
    del elast_full
    gc.collect()
    bounded = rank01_on_mask(surf_full, fp)
    surface_npy = CACHE_DIR / "h86p_surface.npy"
    np.save(surface_npy, bounded)
    surface_sha = sha256(surface_npy)
    surface_report_path = EV_DIR / "h86p-pfa-registry-surface.json"
    surface_report, surface_rc = run_registry_check(surface_npy, surface_report_path, surface=True)
    rho_firings = int(surface_report.get("two_phase", {}).get("literal_reading", {}).get("rho_firings", 999))
    worst_rho = surface_report.get("shared_summary", {}).get("worst_spearman_full_footprint")
    print(f"  surface scan measured={surface_report.get('registry_rasters_measured')} worst_rho={worst_rho} firings={rho_firings}", flush=True)
    if rho_firings != 0:
        card = _stop_card(t0, prereg, input_hashes, preflight, canary, pooled, per_fold,
                          static_sha, surface_sha, surface_report, surface_report_path,
                          reason=f"STOP BEFORE PLACEMENT: surface Spearman rho>0.90 fired {rho_firings}x")
        _write_card(card)
        print(json.dumps({"verdict": "negative", "stop": card["decision_reason"]}, indent=2), flush=True)
        return 2

    print("[5/7] Final dot placement + final-dot registry + PA-86-02 + SGMC diagnostic...", flush=True)
    dcat = ndi.distance_transform_edt(~(cat & fp))
    allowed_full = fp & (dcat > COLLAR_PX)
    frac_gt1km = float((dcat[allowed_full] > 10).mean())
    del dcat
    alloc_full = allocate(surf_full, allowed_full, cat & fp, fp)
    final_dots = alloc_full.dots
    dcat2 = ndi.distance_transform_edt(~(cat & fp))
    far_frac = float((dcat2[final_dots] > 10).mean()) if final_dots.any() else None
    del dcat2
    dots_npy = CACHE_DIR / "h86p_final_dots.npy"
    np.save(dots_npy, final_dots.astype(np.float32))
    dots_sha = sha256(dots_npy)
    dots_report_path = EV_DIR / "h86p-pfa-registry-final-dots.json"
    dots_report, dots_rc = run_registry_check(dots_npy, dots_report_path, surface=False)
    chance_path = EV_DIR / "h86p-pfa-pa86-chance-overlap.json"
    chance = run_chance_check(dots_report_path, dots_npy, chance_path)
    informative = audit_informative_dot_field_firings(dots_report, fp, cat)
    shared = dots_report.get("shared_summary", {})
    print(f"  final scan measured={dots_report.get('registry_rasters_measured')} "
          f"informative={informative['informative_dot_field_firings_count']} "
          f"le90k_firings={informative['discrete_le_90k_firings_over_0p70']} "
          f"worst_le90k={informative['worst_discrete_le_90k_overlap_3px']}", flush=True)
    identical = not (shared.get("byte_unique_among_checked") is True and shared.get("pixel_unique_among_checked") is True)
    duplicate_stop = bool(identical or informative["discrete_le_90k_firings_over_0p70"] > 0)
    sgmc = evaluate_sgmc_proxy({ARM_E1: final_dots, "H33_GEMSDOE32_as_is": h33_mask}, fp, cat, candidate_key=ARM_E1)
    if duplicate_stop:
        card = _stop_card(t0, prereg, input_hashes, preflight, canary, pooled, per_fold,
                          static_sha, surface_sha, surface_report, surface_report_path,
                          reason=("STOP BEFORE SERIALISATION: final dots are identical to a registry raster"
                                  if identical else
                                  f"STOP BEFORE SERIALISATION: {informative['discrete_le_90k_firings_over_0p70']} discrete <=90k-dot registry firings >0.70 (worst {informative['worst_discrete_le_90k_overlap_3px']:.4f} vs {informative['worst_discrete_le_90k_submission']})"),
                          dots_report=dots_report, dots_report_path=dots_report_path, chance=chance,
                          chance_path=chance_path, informative=informative, sgmc=sgmc, dots_sha=dots_sha)
        _write_card(card)
        print(json.dumps({"verdict": "negative", "stop": card["decision_reason"]}, indent=2), flush=True)
        return 2

    print("[6/7] Fail-closed writer (values {0,1}, zeros outside footprint)...", flush=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
    name = f"gems86-h86p-pfa-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"
    note = (f"H86P-PFA paired-flank step LOQO CELF {int(final_dots.sum())}d "
            f"(HOLDOUT {e1s['dti']:.4f} vs E3 {pooled['scores'][ARM_E3]['dti']:.4f}); DO NOT SUBMIT")[:140]
    receipt = write_candidate(final_dots, g, name, note, metadata={
        "lane": "H86P-PFA", "budget": BUDGET, "spacing_px": SPACING_PX, "collar_px": COLLAR_PX,
        "static_feature_sha256": static_sha, "surface_sha256": surface_sha, "dots_sha256": dots_sha,
        "dinkelbach_final_lambda": alloc_full.final_lambda,
        "far_field_frac_gt_1km_from_catalogue": far_frac,
    })
    disk = receipt["independent_disk_validation"]

    print("[7/7] Run card...", flush=True)
    best = prereg["comparable_holdout_best"]["value"]
    beats_e3 = bool(delta_e3["ci95"][0] > 0)
    beats_best = bool(e1s["dti"] > best)
    surface_pass = bool(surface_rc == 0 and surface_report.get("surface_gate_pass") is True)
    dots_pass = bool(dots_rc == 0 and dots_report.get("final_dots_gate_pass") is True)
    scientific_promote = bool(beats_e3 and beats_best and rho_firings == 0
                              and informative["informative_dot_field_firings_count"] == 0
                              and chance.get("gate_pass") is True)
    reasons = []
    if not beats_e3:
        reasons.append(f"E1-E3 paired HOLDOUT-DTI delta {delta_e3['delta']:+.4f} CI {delta_e3['ci95']} not strictly positive")
    if not beats_best:
        reasons.append(f"E1 HOLDOUT-DTI {e1s['dti']:.4f} did not beat comparable strict-LOQO best {best:.4f} (H86I-KSAD)")
    if informative["informative_dot_field_firings_count"]:
        reasons.append(f"{informative['informative_dot_field_firings_count']} informative dot-field firings in full audit")
    if not surface_pass:
        reasons.append("surface v2/literal registry gate failed closed (see surface report)")
    if not dots_pass:
        reasons.append("final-dot v2/literal registry gate failed closed (see final-dots report)")
    if chance.get("gate_pass") is not True:
        reasons.append("PA-86-02 chance-overlap gate failed closed")
    reasons.append("literal full-support witness (17GEMSDOE, covered_allowed_fraction=1.0) blocks every nonempty candidate under the literal reading; selector step separate (protocol rule 6)")
    card = {
        "schema": "gems86.lane_run_card.v1", "lane_id": "H86P-PFA",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_branch": "arena/5620a35f-gemsdoe86",
        "preregistration": {"path": "research/H86P_PFA_PREREGISTRATION.json",
                            "markdown": "research/H86P_PFA_PREREGISTRATION.md",
                            "hypotheses_registry": "registry/h86p_pfa_hypotheses.json",
                            "sha256": input_hashes["preregistration_json_sha256"],
                            "markdown_sha256": input_hashes["preregistration_md_sha256"]},
        "hypothesis": "Paired-flank multi-physics cross-strike step asymmetry (TC/conductivity/basement-depth/gravity/RTP) catches sediment-blanketed piedmont faults missing from the trace catalogue, beyond side-blind gradient magnitude.",
        "mechanism": {"static_features": list(STATIC_NAMES), "baseline_features": list(BASELINE_NAMES),
                      "pfa_features": list(PFA_NAMES), "fold_visible_elastic_features": list(ELASTIC_NAMES),
                      "arms": {ARM_E1: "baseline+PFA+elastic", ARM_E2: "baseline+PFA (catalogue-blind)",
                               ARM_E3: "baseline+elastic (no PFA ablation)"},
                      "allocator": "shared STDP Dinkelbach-CELF, 37654 dots, 2.8px spacing, >3px collar",
                      "training": "strict 4-fold LOQO HGB PU, visible-only labels/features"},
        "named_non_fault_mimic": "Alluvial fan-toe progradation fronts, Lake Lahontan shoreline benches against conductive playas, buried paleochannel/fanglomerate facies changes, Miocene basaltic-andesite flow margins and lithologic contacts.",
        "input_sha256": input_hashes, "preflight": preflight,
        "experiments_run": 3,
        "leakage_canary": canary,
        "leakage_canary_summary": {"n_features": len(canary), "worst_feature": wname,
                                   "worst_discriminative_auc": wv["discriminative_auc"], "threshold": 0.90, "pass": True},
        "holdout_dti": {"evidence_class": "HOLDOUT-DTI", "evaluator_version": EH.VERSION,
                        "evaluator_hashes": EH.implementation_hashes(),
                        "design": "gems57-pooled-hide-v2: buffered whole components (seed20, hide20%, buffer3px, boundary12px), strict LOQO OOF surfaces, pooled 200px blocks, 1000 paired draws",
                        "withheld_positive_pixels": e1s["withheld_positive_pixels"],
                        "candidate": e1s, "all_arms": pooled["scores"],
                        "paired_differences": pooled["paired_differences"],
                        "best_preregistered_control": ARM_E3,
                        "paired_delta_vs_best_preregistered_control": delta_e3,
                        "per_fold": per_fold,
                        "comparable_strict_loqo_best_before_this_lane": prereg["comparable_holdout_best"],
                        "beats_e3_paired_ci_positive": beats_e3, "beats_comparable_best_point": beats_best},
        "sgmc_off_catalogue_diagnostic": sgmc,
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "surface": registry_summary(surface_report, surface_report_path, surface_rc),
            "surface_gate_pass_v2_literal": surface_pass,
            "final_dots": registry_summary(dots_report, dots_report_path, dots_rc),
            "final_dots_gate_pass_v2_literal": dots_pass,
            "pa86_chance_overlap": chance,
            "informative_dot_field_audit": informative,
            "far_field_frac_gt_1km_from_catalogue": far_frac,
            "allowed_domain_frac_gt_1km": frac_gt1km},
        "raster_sha256": receipt["sha256"], "zip_sha256": receipt["zip_sha256"],
        "validator_output": {"evidence_class": "FORMAT-VALIDATION",
                             "no_nan_inside_footprint": bool(disk["checks"].get("in_footprint_all_finite")) and disk.get("n_nan", 0) == 0,
                             "values_in_0_1": disk["checks"].get("range_0_1_guaranteed"),
                             "crs_shape_transform_match": all(disk["checks"].get(k, False) for k in
                                 ("crs_epsg_32611", "dimensions_3730x3292", "transform_matches_sample_submission")),
                             "checks": disk["checks"], "positive_pixels": disk["emitted_positive_pixels"],
                             "min": disk["min"], "max": disk["max"], "writer_receipt": receipt},
        "submission_name": name, "submission_file": f"docs/downloads/{name}.tif",
        "submission_zip": f"docs/downloads/{name}.zip", "note": note, "note_chars": len(note),
        "scientific_promote_like_for_like": scientific_promote,
        "verdict": "negative", "decision": "DO NOT SUBMIT",
        "decision_reason": "; ".join(reasons),
        "submission_ready": False, "safe_to_submit": False, "approved_for_weekly_slot": False,
        "submission_slots_used": 0, "new_candidate_generated": True, "duplicate": False,
        "runtime_seconds": round(time.time() - t0, 2),
    }
    _write_card(card)
    print(json.dumps({"lane": "H86P-PFA", "file": card["submission_file"], "sha256": card["raster_sha256"],
                      "holdout_dti": e1s, "delta_e3": delta_e3, "verdict": "negative",
                      "decision": "DO NOT SUBMIT", "runtime_seconds": card["runtime_seconds"]}, indent=2), flush=True)
    return 0


def _stop_card(t0, prereg, input_hashes, preflight, canary, pooled, per_fold, static_sha,
               surface_sha, surface_report, surface_report_path, reason, **kw):
    e1s = pooled["scores"][ARM_E1]
    card = {
        "schema": "gems86.lane_run_card.v1", "lane_id": "H86P-PFA",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_branch": "arena/5620a35f-gemsdoe86",
        "preregistration": {"path": "research/H86P_PFA_PREREGISTRATION.json", "sha256": input_hashes["preregistration_json_sha256"]},
        "hypothesis": "Paired-flank multi-physics cross-strike step asymmetry for sediment-blanketed piedmont faults.",
        "mechanism": {"static_features": list(STATIC_NAMES)},
        "named_non_fault_mimic": "Fan-toe fronts, Lahontan shorelines, paleochannel facies changes, volcanic flow margins, lithologic contacts.",
        "input_sha256": input_hashes, "preflight": preflight, "experiments_run": 3,
        "leakage_canary": canary,
        "holdout_dti": {"evidence_class": "HOLDOUT-DTI", "evaluator_version": EH.VERSION,
                        "withheld_positive_pixels": e1s["withheld_positive_pixels"],
                        "candidate": e1s, "all_arms": pooled["scores"],
                        "paired_differences": pooled["paired_differences"], "per_fold": per_fold},
        "sgmc_off_catalogue_diagnostic": kw.get("sgmc"),
        "correlation_overlap_vs_registry": {"evidence_class": "REGISTRY-MEASUREMENT",
            "surface": registry_summary(surface_report, surface_report_path, 0 if surface_report.get("surface_gate_pass") else 2),
            **({"final_dots": registry_summary(kw["dots_report"], kw["dots_report_path"], 2),
                "pa86_chance_overlap": kw.get("chance"), "informative_dot_field_audit": kw.get("informative")} if "dots_report" in kw else {})},
        "raster_sha256": None, "zip_sha256": None,
        "validator_output": {"evidence_class": "FORMAT-VALIDATION", "status": "NOT_SERIALISED_REGISTRY_STOP",
                             "no_nan_inside_footprint": None, "values_in_0_1": None, "crs_shape_transform_match": None},
        "submission_name": None, "submission_file": None, "note": "H86P-PFA stopped before serialisation; DO NOT SUBMIT",
        "note_chars": len("H86P-PFA stopped before serialisation; DO NOT SUBMIT"), "verdict": "negative", "decision": "DO NOT SUBMIT", "decision_reason": reason,
        "submission_ready": False, "safe_to_submit": False, "approved_for_weekly_slot": False,
        "submission_slots_used": 0, "new_candidate_generated": False, "duplicate": True,
        "runtime_seconds": round(time.time() - t0, 2),
        "static_feature_sha256": static_sha, "surface_sha256": surface_sha, "dots_sha256": kw.get("dots_sha"),
    }
    return card


def _write_card(card):
    p = EV_DIR / "h86p-pfa-run-card.json"
    p.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"wrote {p}", flush=True)


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    return run_pa86_lane()


if __name__ == "__main__":
    raise SystemExit(main())
