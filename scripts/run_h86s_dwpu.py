#!/usr/bin/env python3
"""H86S-DWPU lane runner (preregistration: research/H86S_DWPU_PREREGISTRATION.json).

Detectability-weighted PU: HGB positives=catalogue, negatives sampled with
weight 0.05+0.95*c(x), c from B15/B19 completeness ranks. 3 arms (E1 weighted,
E2 unweighted ablation, E3 weighted without B15/B19 features), vendor
gems57-pooled-hide-v2 holdout, SGMC-PROXY diagnostic, leakage canary, scoped
registry uniqueness, strict fleet-regression projection, frozen gates,
fail-closed vendor writer. No slot picked: governance stays negative/false.
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
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gems57 import evaluate_holdout as EH, grid, holdout, uniqueness  # noqa: E402
from gems86_sfg.features import emit_poisson_disk  # noqa: E402
from gems86_dwpu.features import (  # noqa: E402
    COVER_FEATURES, FEATURE_NAMES, build_stack, completeness, train_predict,
)
from scripts.run_h86k_stdp import (  # noqa: E402
    BUDGET, COLLAR_PX, evaluate_sgmc_proxy, load_binary_tif,
    prepare_canary_indices, score_canary_array, write_candidate,
)

FEATURE_TIF = ROOT / "data/training_features.tif"
PREREG = ROOT / "research/H86S_DWPU_PREREGISTRATION.json"
EV = ROOT / "docs/evidence"
PINS = {
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "derived_sgmc_faults_100m_u8.tif": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
}
ARM_E1, ARM_E2, ARM_E3 = "E1_dwpu_weighted", "E2_pu_unweighted_ablation", "E3_dwpu_nocover_features"
ARMS = (ARM_E1, ARM_E2, ARM_E3)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def log(msg: str):
    print(msg, flush=True)


def registry_paths() -> list[Path]:
    paths = []
    for d in (ROOT / "data/scored_fleet", ROOT / "data/scored", ROOT / "docs/downloads"):
        paths.extend(sorted(d.glob("*.tif")))
    return paths


def main() -> int:
    t0 = time.time()
    prereg = json.loads(PREREG.read_text())
    assert prereg["lane_id"] == "H86S-DWPU" and len(prereg["arms"]) == 3

    log("[1/9] Verifying pinned inputs...")
    pin_paths = {
        "training_features.tif": FEATURE_TIF,
        "existing_faults.tif": ROOT / "data/bridge/existing_faults.tif",
        "sample_submission.tif": ROOT / "data/bridge/sample_submission.tif",
        "derived_sgmc_faults_100m_u8.tif": ROOT / "data/external/derived_sgmc_faults_100m_u8.tif",
    }
    input_hashes = {}
    for name, p in pin_paths.items():
        h = sha256(p)
        if h != PINS[name]:
            raise ValueError(f"SHA-256 mismatch {name}: {h}")
        input_hashes[name] = h
    log("  all 4 pins OK")

    g = grid.load_grid(ROOT / "data/bridge")
    fp = np.asarray(g.footprint, bool)
    cat = np.asarray(g.catalogue, bool)

    log("[2/9] Building 11-plane DWPU stack + completeness...")
    with rasterio.open(FEATURE_TIF) as src:
        planes = build_stack(lambda i: src.read(i), fp)
    comp = completeness(planes, fp)
    planes["dwpu_completeness_c"] = comp

    folds, _quad = holdout.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    vis = np.asarray(folds[0]["visible"], bool) & fp
    for f in folds[1:]:
        assert np.array_equal(np.asarray(f["visible"], bool) & fp, vis)

    log("[3/9] Training visible-label models (holdout surfaces)...")
    nocover = tuple(n for n in FEATURE_NAMES if n not in COVER_FEATURES)
    surf_vis, surf_full = {}, {}
    surf_vis[ARM_E1] = train_predict(planes, FEATURE_NAMES, vis, fp, comp, weighted=True)
    surf_vis[ARM_E2] = train_predict(planes, FEATURE_NAMES, vis, fp, comp, weighted=False)
    surf_vis[ARM_E3] = train_predict(planes, nocover, vis, fp, comp, weighted=True)
    log("  visible models done")

    log("[4/9] Leakage canary (every plane + visible surfaces)...")
    p_idx, n_idx, y = prepare_canary_indices(folds, fp)
    canary = {}
    canary_planes = {k: planes[k] for k in FEATURE_NAMES}
    canary_planes["dwpu_completeness_c"] = comp
    for arm in ARMS:
        canary_planes[f"{arm}_visible_surface"] = surf_vis[arm]
    for name, pl in canary_planes.items():
        canary[name] = score_canary_array(np.r_[pl.ravel()[p_idx], pl.ravel()[n_idx]].astype(np.float64), y)
    flagged = [k for k, v in canary.items() if v["leakage_flag"]]
    worst = max(canary.items(), key=lambda kv: kv[1]["discriminative_auc"])
    log(f"  canary worst={worst[0]} disc_auc={worst[1]['discriminative_auc']} flagged={flagged}")
    if flagged:
        raise RuntimeError(f"STOP leakage canary: {flagged}")

    log("[5/9] Holdout emissions + pooled scoring (3 arms + 2 comparators)...")
    d_vis = ndi.distance_transform_edt(~vis)
    allowed_ho = fp & (d_vis > COLLAR_PX)
    del d_vis
    reg_paths = registry_paths()
    reg_binaries: dict[str, np.ndarray] = {}
    for p in reg_paths:
        reg_binaries[str(p.relative_to(ROOT))] = load_binary_tif(p) & fp
    h33_key = next(k for k in reg_binaries if "GEMSDOE32" in k and "h33-h33-2" in k)
    h27_key = next(k for k in reg_binaries if "GEMSDOE28" in k and "h27-4-r1" in k)
    ho_dots = {arm: emit_poisson_disk(surf_vis[arm], allowed_ho & np.isfinite(surf_vis[arm]), BUDGET) for arm in ARMS}
    ho_dots["H33_visible_collar"] = reg_binaries[h33_key] & allowed_ho
    ho_dots["H27-4_visible_collar"] = reg_binaries[h27_key] & allowed_ho
    terms = {k: None for k in ho_dots}
    per_fold = {k: {} for k in ho_dots}
    for f in folds:
        for name, dots in ho_dots.items():
            res, bt = EH.evaluate(dots.astype(np.float32), f, fp, block_side=200)
            terms[name] = bt if terms[name] is None else terms[name] + bt
            per_fold[name][f["name"]] = dict(evidence_class="HOLDOUT-DTI", evaluator_version=EH.VERSION,
                                             dti=res["dti"], n_truth=res["n_truth"], emitted=res["n_emitted"])
        log(f"  fold {f['name']}: " + " | ".join(f"{n.split('_')[0]}={per_fold[n][f['name']]['dti']:.4f}" for n in ho_dots))
    pooled = EH.pooled_summary(terms, draws=1000, seed=861726, candidate=ARM_E1)
    for n, s in pooled["scores"].items():
        log(f"  HOLDOUT-DTI {n}: {s['dti']:.4f} [{s['ci95'][0]:.4f},{s['ci95'][1]:.4f}]")

    log("[6/9] Training full-catalogue models + final emissions + SGMC + null...")
    surf_full[ARM_E1] = train_predict(planes, FEATURE_NAMES, cat, fp, comp, weighted=True)
    surf_full[ARM_E2] = train_predict(planes, FEATURE_NAMES, cat, fp, comp, weighted=False)
    surf_full[ARM_E3] = train_predict(planes, nocover, cat, fp, comp, weighted=True)
    d_cat = ndi.distance_transform_edt(~cat)
    allowed_full = fp & (d_cat > COLLAR_PX)
    fin = {arm: emit_poisson_disk(surf_full[arm], allowed_full & np.isfinite(surf_full[arm]), BUDGET) for arm in ARMS}
    rng2 = np.random.default_rng(861726)
    null_order = rng2.permutation(np.flatnonzero(allowed_full.ravel()))
    from gems86_sfg.features import emit_poisson_disk as _emit
    fin["RANDOM_NULL_seed861726"] = _emit(np.zeros_like(surf_full[ARM_E1]), allowed_full, BUDGET, rng_order=null_order)
    sgmc_in = {**fin, "GEMSDOE32_H33": reg_binaries[h33_key], "GEMSDOE28_H27-4": reg_binaries[h27_key]}
    sgmc = evaluate_sgmc_proxy(sgmc_in, fp, cat, candidate_key=ARM_E1)
    dcat_dots = d_cat[fin[ARM_E1]]
    fingerprint = dict(dots=int(fin[ARM_E1].sum()), min_dcat_px=float(dcat_dots.min()),
                       median_dcat_m=float(np.median(dcat_dots) * 100.0),
                       frac_gt_1km=float((dcat_dots > 10).mean()), frac_le_3px=float((dcat_dots <= 3).mean()))
    log(f"  E1 fingerprint {fingerprint}; SGMC E1={sgmc['scores'][ARM_E1]['dti']:.4f} H33={sgmc['scores']['GEMSDOE32_H33']['dti']:.4f}")

    log("[7/9] Surface uniqueness (pre-placement would be ideal; here full surface, sampled Spearman)...")
    rng = np.random.default_rng(861726)
    fp_flat = np.flatnonzero(fp.ravel())
    sample = rng.choice(fp_flat, size=min(400_000, fp_flat.size), replace=False)
    surf_s = rankdata(surf_full[ARM_E1].ravel()[sample].astype(np.float64))
    surf_s = (surf_s - surf_s.mean()) / (surf_s.std() + 1e-12)
    surface_rows = []
    for rel, b in reg_binaries.items():
        bs = b.ravel()[sample].astype(np.float64)
        if bs.std() == 0:
            rho = 0.0
        else:
            rb = rankdata(bs)
            rho = float(np.corrcoef(surf_s, (rb - rb.mean()) / (rb.std() + 1e-12))[0, 1])
        surface_rows.append(dict(file=rel, their_dots=int(b.sum()), sampled_spearman=round(rho, 4)))
    worst_rho = max(surface_rows, key=lambda r: r["sampled_spearman"])
    log(f"  {len(reg_binaries)} registry rasters; worst sampled rho={worst_rho['sampled_spearman']} vs {worst_rho['file']}")

    log("[8/9] Final-dot uniqueness + strict fleet estimator...")
    dot_rows = []
    for rel, b in reg_binaries.items():
        dot_rows.append(dict(file=rel, their_dots=int(b.sum()),
                             forward_overlap_3px=round(float(uniqueness.dot_overlap(fin[ARM_E1], b)), 4)))
    discrete = [r for r in dot_rows if r["their_dots"] <= 100_000]
    dense = [r for r in dot_rows if r["their_dots"] > 100_000]
    worst_ov = max(discrete, key=lambda r: r["forward_overlap_3px"]) if discrete else None
    ov_h33 = next(r["forward_overlap_3px"] for r in dot_rows if r["file"] == h33_key)
    log(f"  discrete<=100k: {len(discrete)}, worst={worst_ov['forward_overlap_3px']} vs {worst_ov['file']}; ovH33={ov_h33}")

    # Strict fleet estimator (same frozen method as H86R v2)
    import csv as _csv, re as _re
    scores = {}
    for row in _csv.DictReader(open(ROOT / "registry/prior_scores.csv")):
        try:
            scores[row["submission"].lower()] = float(row["score"])
        except Exception:
            pass

    def match_score(rel: str):
        base = Path(rel).stem.lower()
        for _p in ("gemsdoe32__", "gemsdoe36__", "gemsdoe33__", "gemsdoe28__",
                   "gemsdoe49__", "gemsdoe63__", "gemsdoe66__", "gemsdoe70__",
                   "gemsdoe73__", "gemsdoe75__", "gemsdoe76__", "gemsdoe78__",
                   "gemsdoe80__", "gemsdoe81__", "gemsdoe82__", "gemsdoe83__",
                   "gemsdoe85__", "gemsdoe88__"):
            base = base.replace(_p, "")
        for _p in ("gemsdoe32-", "gemsdoe36-", "gemsdoe33-", "gems28-", "gems-", "gems"):
            if base.startswith(_p):
                base = base[len(_p):]
        for suf in ("-allfinite", "-zeros", "-nan", "-zero"):
            base = base.replace(suf, "")
        for s, sc in scores.items():
            ss = s
            for suf in ("-allfinite", "-zeros", "-nan", "-zero"):
                ss = ss.replace(suf, "")
            if ss and (ss in base or base in ss):
                return sc
        toks = [t for t in _re.split(r"[-_]", base)
                if _re.fullmatch(r"[0-9a-f]{8,}", t) and any(c.isalpha() for c in t)]
        for s, sc in scores.items():
            if any(t in s for t in toks):
                return sc
        return None

    near_h33 = uniqueness._near(reg_binaries[h33_key])
    est_rows, seen = [], set()
    for rel, b in reg_binaries.items():
        if "/downloads/" in rel:
            continue
        sc = match_score(rel)
        if sc is None or int(b.sum()) == 0:
            continue
        key = (int(b.sum()), round(float(near_h33[b].mean()), 4), sc)
        if key in seen:
            continue
        seen.add(key)
        dd = d_cat[b]
        est_rows.append(dict(file=rel, dots=int(b.sum()), live_owner_reported=sc,
                             ov_h33=float(near_h33[b].mean()), frac_gt_1km=float((dd > 10).mean())))
    estimator = dict(status="INSUFFICIENT_MATCHED_FLEET", n=len(est_rows), rows=est_rows)
    sg_e1 = sgmc["scores"][ARM_E1]["dti"]
    if len(est_rows) >= 6:
        extra = {f"EST::{i}": reg_binaries[r["file"]] for i, r in enumerate(est_rows)}
        sg = evaluate_sgmc_proxy(extra, fp, cat, candidate_key="EST::0")
        for i, r in enumerate(est_rows):
            r["sgmc_proxy_dti"] = sg["scores"][f"EST::{i}"]["dti"]
        X = np.array([[1.0, r["ov_h33"], r["sgmc_proxy_dti"], r["frac_gt_1km"]] for r in est_rows])
        yv = np.array([r["live_owner_reported"] for r in est_rows])
        beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
        loo = []
        for i in range(len(est_rows)):
            m = np.ones(len(est_rows), bool); m[i] = False
            bi, *_ = np.linalg.lstsq(X[m], yv[m], rcond=None)
            loo.append(yv[i] - float(X[i] @ bi))
        loo_rmse = float(np.sqrt(np.mean(np.square(loo))))
        x_e1 = np.array([1.0, ov_h33, sg_e1, fingerprint["frac_gt_1km"]])
        proj = float(np.clip(x_e1 @ beta, 0.0, 1.0))
        estimator = dict(evidence_class="FLEET-REGRESSION-PROJECTION (not a score)",
                         n=len(est_rows), features=["1", "ov_h33", "sgmc_proxy_dti", "frac_gt_1km"],
                         coefficients=[float(v) for v in beta], loo_rmse=loo_rmse, rows=est_rows,
                         candidate=dict(ov_h33=ov_h33, sgmc_proxy_dti=sg_e1,
                                        frac_gt_1km=fingerprint["frac_gt_1km"], projection=proj,
                                        interval_approx=[float(np.clip(proj - 1.96 * loo_rmse, 0, 1)),
                                                         float(np.clip(proj + 1.96 * loo_rmse, 0, 1))]),
                         caveat="Fitted only on OWNER-REPORTED live scores; never ORGANIZER-CONFIRMED; cannot credit genuinely new truth mass.")

    log("[9/9] Gates + serialization + run card...")
    e1h, e2h = pooled["scores"][ARM_E1], pooled["scores"][ARM_E2]
    d_e2 = pooled["paired_differences"][ARM_E2]
    h33_sg = sgmc["scores"]["GEMSDOE32_H33"]["dti"]
    gates = {
        "G1_format_writer_pass": None,
        "G2_canary_le_0p90": not flagged,
        "G3_holdout_E1_gt_E2_point": bool(e1h["dti"] > e2h["dti"]),
        "G3_holdout_E1_gt_E2_paired_ci_excludes_0": bool(d_e2["ci95"][0] > 0),
        "G4_sgmc_E1_ge_H33_same_call": bool(sg_e1 >= h33_sg),
        "G5_uniqueness_scoped_discrete_le100k": bool(worst_ov and worst_ov["forward_overlap_3px"] <= 0.70
                                                     and worst_rho["sampled_spearman"] <= 0.90),
        "G6_fingerprint_37654_min_dcat_gt3": bool(fingerprint["dots"] == BUDGET and fingerprint["min_dcat_px"] > 3.0),
    }
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dots_hash = hashlib.sha256(fin[ARM_E1].tobytes()).hexdigest()[:8]
    name = f"gems86-h86s-dwpu-37654dots-{ts}-{dots_hash}-zeros"
    note = f"H86S-DWPU detect-weighted PU 37654d HOLD {e1h['dti']:.4f} SGMC {sg_e1:.4f} ovH33 {ov_h33:.3f}; audit, selector decides"
    assert len(name) <= 140 and len(note) <= 140, (len(name), len(note))
    receipt = None
    if gates["G5_uniqueness_scoped_discrete_le100k"]:
        receipt = write_candidate(fin[ARM_E1], g, name, note, metadata=dict(
            lane="H86S-DWPU", evidence_class="LOCAL-FORMAT-VALIDATION", scoped_download_candidate=None))
        gates["G1_format_writer_pass"] = bool(receipt["independent_disk_validation"]["all_checks_passed"])
    else:
        gates["G1_format_writer_pass"] = False
        log("  G5 FAILED -> duplicate stop, no TIFF serialized")

    scoped_candidate = bool(gates["G1_format_writer_pass"] and gates["G2_canary_le_0p90"]
                            and gates["G3_holdout_E1_gt_E2_point"]
                            and gates["G3_holdout_E1_gt_E2_paired_ci_excludes_0"]
                            and gates["G4_sgmc_E1_ge_H33_same_call"]
                            and gates["G5_uniqueness_scoped_discrete_le100k"]
                            and gates["G6_fingerprint_37654_min_dcat_gt3"])
    verdict = "promote" if scoped_candidate else "negative"
    decision = ("DOWNLOAD_CANDIDATE — selector decides weekly slot; DO NOT AUTO-SUBMIT" if scoped_candidate else "DO NOT SUBMIT")

    (EV / "h86s-dwpu-registry-surface.json").write_text(json.dumps(
        dict(schema="gems86.h86s.registry-surface.v1", evidence_class="REGISTRY-MEASUREMENT",
             candidate="H86S-DWPU E1 full-catalogue surface", worst=worst_rho,
             sample_size=int(sample.size), rows=surface_rows), indent=2) + "\n")
    (EV / "h86s-dwpu-registry-final-dots.json").write_text(json.dumps(
        dict(schema="gems86.h86s.registry-final-dots.v1", evidence_class="REGISTRY-MEASUREMENT",
             candidate=name, discrete_le100k_checked=len(discrete), worst_discrete=worst_ov,
             dense_gt100k_reported_separately=dense, overlap_limit=0.70, rows=dot_rows,
             scope="Locally restored registry only (data/scored_fleet + data/scored + docs/downloads); NOT full upstream registry; literal full-support witness gate fails for every nonempty candidate and is disclosed."), indent=2) + "\n")
    (EV / "h86s-dwpu-fleet-estimator-20261027.json").write_text(json.dumps(estimator, indent=2) + "\n")

    card = dict(
        schema="gems86.lane_run_card.v1", lane_id="H86S-DWPU",
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        git_branch="arena/df922739-gemsdoe86",
        preregistration=dict(path="research/H86S_DWPU_PREREGISTRATION.json",
                             hypotheses_registry="registry/h86s_hypotheses_20261027.json",
                             sha256=sha256(PREREG)),
        hypothesis="Detectability-Weighted PU Learning: HGB positives=catalogue pixels, negatives sampled background weighted 0.05+0.95*c(x) with completeness c from B15 basement-depth + B19 slope ranks; 11 catalogue-free native geophysics features; 37,654 dots, 2.8px Poisson spacing, >3.0px collar.",
        mechanism=dict(features=list(FEATURE_NAMES), completeness="c=clip(0.6*(1-rank01(B15))+0.4*rank01(B19),0,1)",
                       negative_weight="0.05+0.95*c", model="HistGradientBoosting 200 iters, sample-weighted"),
        named_non_fault_mimic="Unfaulted deep playa basins (genuinely fault-free) are up-weighted once negative evidence is discounted; saline playa response mimics hydrothermal alteration in TC/radiometrics.",
        input_sha256=input_hashes,
        leakage_canary=canary,
        leakage_canary_summary=dict(features_tested=len(canary), max_feature=worst[0],
                                    max_discriminative_auc=worst[1]["discriminative_auc"], threshold=0.90,
                                    any_leakage_flag=bool(flagged)),
        holdout_dti=dict(evidence_class="HOLDOUT-DTI", evaluator_version=EH.VERSION,
                         evaluator_hashes=EH.implementation_hashes(),
                         design="gems57-pooled-hide-v2 seed=20, 20% whole components hidden/quadrant, 3px buffer, 12px eroded, visible-only training + collar, pooled 200px blocks, 1000 paired bootstrap seed 861726",
                         withheld_positive_pixels=int(e1h["withheld_positive_pixels"]),
                         candidate=e1h, all_arms=pooled["scores"], paired_differences=pooled["paired_differences"],
                         per_fold=per_fold, beats_ablation_paired_ci=bool(d_e2["ci95"][0] > 0)),
        sgmc_proxy=dict(evidence_class="SGMC-PROXY-DTI", scores=sgmc.get("scores"),
                        paired_differences=sgmc.get("paired_differences_vs_candidate")),
        fingerprint=fingerprint,
        fleet_regression_projection=estimator.get("candidate"),
        fleet_estimator_file="docs/evidence/h86s-dwpu-fleet-estimator-20261027.json",
        uniqueness_scoped=dict(surface_worst_sampled_rho=worst_rho, final_dots_worst_discrete=worst_ov,
                               overlap_vs_H33=ov_h33, discrete_le100k_checked=len(discrete),
                               dense_gt100k_count=len(dense),
                               surface_report="docs/evidence/h86s-dwpu-registry-surface.json",
                               final_dots_report="docs/evidence/h86s-dwpu-registry-final-dots.json",
                               literal_witness_status="STOP_LITERAL_OVERLAP_UNSATISFIABLE (docs/evidence/protocol-preflight.json, 17GEMSDOE continuous full-support witness) - disclosed, not hidden; scoped like-for-like reading used per PA-86-01"),
        gates=gates, scoped_download_candidate=scoped_candidate,
        raster_sha256=(receipt["sha256"] if receipt else None),
        zip_sha256=(receipt.get("zip_sha256") if receipt else None),
        validator_output=(receipt["independent_disk_validation"] if receipt else None),
        submission_name=name, submission_file=(f"docs/downloads/{name}.tif" if receipt else None),
        submission_zip=(f"docs/downloads/{name}.zip" if receipt else None),
        submission_receipt=(f"docs/downloads/{name}.json" if receipt else None),
        note=note, note_chars=len(note), verdict=verdict, decision=decision, scoped_decision=decision,
        submission_ready=False, safe_to_submit=False, approved_for_weekly_slot=False,
        submission_slots_used=0, experiments_run=3, runtime_seconds=round(time.time() - t0, 1),
    )
    (EV / "h86s-dwpu-run-card.json").write_text(json.dumps(card, indent=2) + "\n")
    log(f"DONE verdict={verdict} scoped_candidate={scoped_candidate} gates={gates}")
    log(f"name={name} sha={card['raster_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
