#!/usr/bin/env python3
"""H86R-SFG lane runner (preregistration: research/H86R_SFG_PREREGISTRATION.json).

Executes queued H86J-SCO at full-footprint scale: 5 native-band edge planes ->
multiline-corroborated fusion E -> catalogue strike-field gate (0.35+0.65*A) ->
score-ordered 2.8 px Poisson-disk emission of exactly 37,654 dots outside a
3.0 px catalogue collar. Three preregistered arms (E1 gated fusion, E2 ungated
ablation, E3 gated gravity-only), vendor gems57-pooled-hide-v2 holdout, repo
SGMC-PROXY diagnostic, leakage canary, scoped registry uniqueness, fleet
regression projection, frozen gate table, fail-closed vendor writer.
No slot is picked: verdict/safe_to_submit governance stays negative/false.
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

from gems57 import evaluate_holdout as EH, grid, holdout, uniqueness, validate  # noqa: E402
from gems86_sfg.features import (  # noqa: E402
    alignment_A, catalogue_strike_field, clean, edge_ranks, emit_poisson_disk,
    fuse_E, gated,
)
from scripts.run_h86k_stdp import (  # noqa: E402
    BUDGET, COLLAR_PX, evaluate_sgmc_proxy, load_binary_tif,
    prepare_canary_indices, score_canary_array, write_candidate,
)

FEATURE_TIF = ROOT / "data/bridge/training_features.tif"
PREREG = ROOT / "research/H86R_SFG_PREREGISTRATION.json"
EV = ROOT / "docs/evidence"
OUT = ROOT / "docs/downloads"
PINS = {
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "derived_sgmc_faults_100m_u8.tif": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
}
ARM_E1, ARM_E2, ARM_E3 = "E1_sfg_gated_edge_fusion", "E2_edge_fusion_ungated_ablation", "E3_sfg_gated_gravity_only"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def log(msg: str):
    print(msg, flush=True)


def registry_paths() -> list[Path]:
    paths = []
    for d in (ROOT / "data/scored_fleet", ROOT / "data/scored", ROOT / "docs/downloads"):
        paths.extend(sorted(d.glob("*.tif")))
    return paths


def run_pa86_lane() -> int:
    # Imported callers must obey the same literal stop as the CLI.
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    t0 = time.time()
    if not PREREG.is_file():
        raise RuntimeError("missing frozen preregistration")
    prereg = json.loads(PREREG.read_text())
    assert prereg["lane_id"] == "H86R-SFG" and len(prereg["arms"]) == 3

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

    log("[2/9] Building 5 edge planes + fusion E (native bands 5,3,2,15,19)...")
    with rasterio.open(FEATURE_TIF) as src:
        read = lambda i: src.read(i)  # noqa: E731
        planes = edge_ranks(read, fp)
        b11 = src.read(11).astype(np.float32)
        b18 = src.read(18).astype(np.float32)
    E = fuse_E(planes)
    planes["sfg_edge_fusion_E"] = E

    log("[3/9] Catalogue strike fields (full + holdout-visible) + alignment gates...")
    folds, _quad = holdout.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    vis = np.asarray(folds[0]["visible"], bool) & fp
    for f in folds[1:]:
        assert np.array_equal(np.asarray(f["visible"], bool) & fp, vis)
    cosC, sinC = catalogue_strike_field(cat, fp)
    A_full = alignment_A(b11, b18, fp, cosC, sinC)
    del cosC, sinC
    cosV, sinV = catalogue_strike_field(vis, fp)
    A_vis = alignment_A(b11, b18, fp, cosV, sinV)
    del cosV, sinV, b11, b18
    grav = planes["sfg_grav_edge_b5_rank"]
    S = {
        (ARM_E1, "full"): gated(E, A_full), (ARM_E1, "vis"): gated(E, A_vis),
        (ARM_E2, "full"): E, (ARM_E2, "vis"): E,
        (ARM_E3, "full"): gated(grav, A_full), (ARM_E3, "vis"): gated(grav, A_vis),
    }

    log("[4/9] Leakage canary (every plane, discriminative AUC <= 0.90)...")
    p_idx, n_idx, y = prepare_canary_indices(folds, fp)
    canary = {}
    canary_planes = {**{k: planes[k] for k in list(planes)},
                     "sfg_alignment_A_visible": A_vis, "sfg_surface_E1_visible": S[(ARM_E1, "vis")],
                     "sfg_surface_E3_visible": S[(ARM_E3, "vis")]}
    for name, pl in canary_planes.items():
        canary[name] = score_canary_array(np.r_[pl.ravel()[p_idx], pl.ravel()[n_idx]].astype(np.float64), y)
    flagged = [k for k, v in canary.items() if v["leakage_flag"]]
    worst = max(canary.items(), key=lambda kv: kv[1]["discriminative_auc"])
    log(f"  canary worst={worst[0]} disc_auc={worst[1]['discriminative_auc']} flagged={flagged}")
    if flagged:
        raise RuntimeError(f"STOP leakage canary: {flagged}")

    log("[5/9] Surface uniqueness (pre-placement, sampled Spearman n=400k, seed 861726)...")
    reg = registry_paths()
    rng = np.random.default_rng(861726)
    fp_flat = np.flatnonzero(fp.ravel())
    sample = rng.choice(fp_flat, size=min(400_000, fp_flat.size), replace=False)
    surf_s = rankdata(S[(ARM_E1, "full")].ravel()[sample].astype(np.float64))
    surf_s = (surf_s - surf_s.mean()) / (surf_s.std() + 1e-12)
    reg_binaries: dict[str, np.ndarray] = {}
    surface_rows = []
    for p in reg:
        b = load_binary_tif(p) & fp
        reg_binaries[str(p.relative_to(ROOT))] = b
        bs = b.ravel()[sample].astype(np.float64)
        rho = float(np.corrcoef(surf_s, (rankdata(bs) - rankdata(bs).mean()) / (rankdata(bs).std() + 1e-12))[0, 1]) if bs.std() > 0 else 0.0
        surface_rows.append(dict(file=str(p.relative_to(ROOT)), their_dots=int(b.sum()),
                                 sampled_spearman=round(rho, 4)))
    worst_rho = max(surface_rows, key=lambda r: r["sampled_spearman"])
    log(f"  {len(reg)} registry rasters; worst sampled rho={worst_rho['sampled_spearman']} vs {worst_rho['file']}")
    gc.collect()

    log("[6/9] Holdout emissions + gems57-pooled-hide-v2 scoring (3 arms + 3 comparators)...")
    d_vis = ndi.distance_transform_edt(~vis)
    allowed_ho = fp & (d_vis > COLLAR_PX)
    del d_vis
    h33 = reg_binaries["data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"]
    h27 = reg_binaries["data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"]
    bfra_name = next(k for k in reg_binaries if "h86q-bfra" in k)
    ho_dots = {}
    for arm in (ARM_E1, ARM_E2, ARM_E3):
        ho_dots[arm] = emit_poisson_disk(S[(arm, "vis")], allowed_ho & np.isfinite(S[(arm, "vis")]), BUDGET)
    ho_dots["H33_visible_collar"] = h33 & allowed_ho
    ho_dots["H27-4_visible_collar"] = h27 & allowed_ho
    ho_dots["H86Q_BFRA_as_shipped"] = reg_binaries[bfra_name] & allowed_ho
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
        log(f"  HOLDOUT-DTI {n}: {s['dti']:.4f} [{s['ci95'][0]:.4f},{s['ci95'][1]:.4f}] n={s['withheld_positive_pixels']}")

    log("[7/9] Final emissions (full catalogue) + random null + SGMC-PROXY + fingerprint...")
    d_cat = ndi.distance_transform_edt(~cat)
    allowed_full = fp & (d_cat > COLLAR_PX)
    fin = {}
    for arm in (ARM_E1, ARM_E2, ARM_E3):
        fin[arm] = emit_poisson_disk(S[(arm, "full")], allowed_full & np.isfinite(S[(arm, "full")]), BUDGET)
    rng2 = np.random.default_rng(861726)
    null_order = rng2.permutation(np.flatnonzero(allowed_full.ravel()))
    fin["RANDOM_NULL_seed861726"] = emit_poisson_disk(np.zeros_like(E), allowed_full, BUDGET, rng_order=null_order)
    sgmc_in = {**fin, "GEMSDOE32_H33": h33, "GEMSDOE28_H27-4": h27, "H86Q_BFRA": reg_binaries[bfra_name]}
    sgmc = evaluate_sgmc_proxy(sgmc_in, fp, cat, candidate_key=ARM_E1)
    dcat_dots = d_cat[fin[ARM_E1]]
    fingerprint = dict(dots=int(fin[ARM_E1].sum()), min_dcat_px=float(dcat_dots.min()),
                       median_dcat_m=float(np.median(dcat_dots) * 100.0),
                       frac_gt_1km=float((dcat_dots > 10).mean()), frac_le_3px=float((dcat_dots <= 3).mean()))
    log(f"  E1 fingerprint {fingerprint}")

    log("[8/9] Final-dot uniqueness vs local registry + fleet regression estimator...")
    dot_rows = []
    for rel, b in reg_binaries.items():
        dot_rows.append(dict(file=rel, their_dots=int(b.sum()),
                             forward_overlap_3px=round(float(uniqueness.dot_overlap(fin[ARM_E1], b)), 4)))
    discrete = [r for r in dot_rows if r["their_dots"] <= 100_000]
    dense = [r for r in dot_rows if r["their_dots"] > 100_000]
    worst_ov = max(discrete, key=lambda r: r["forward_overlap_3px"]) if discrete else None
    ov_h33 = next(r["forward_overlap_3px"] for r in dot_rows if "GEMSDOE32" in r["file"] and "h33-h33-2" in r["file"])
    log(f"  discrete<=100k: {len(discrete)} rasters, worst overlap={worst_ov['forward_overlap_3px']} vs {worst_ov['file']}; ovH33={ov_h33}")

    import csv as _csv, re as _re
    scores = {}
    for row in _csv.DictReader(open(ROOT / "registry/prior_scores.csv")):
        try:
            scores[row["submission"].lower()] = float(row["score"])
        except Exception:
            pass

    def match_score(rel: str):
        # STRICT matching only (IR-86R-ESTIMATOR-MISMATCH-20261026): normalized
        # stem containment, or a shared hex hash token (>=8 hex chars incl. a
        # letter). Pure-digit/date/dot-count tokens must never match: the v1
        # loose tokenizer false-labelled 5/28 rows incl. a DO-NOT-SUBMIT file.
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

    near_h33 = uniqueness._near(h33)
    est_rows, seen = [], set()
    for rel, b in reg_binaries.items():
        if "/downloads/" in rel:
            continue  # gems86 lanes have no live scores
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
        sg_e1 = sgmc["scores"][ARM_E1]["dti"]
        x_e1 = np.array([1.0, ov_h33, sg_e1, fingerprint["frac_gt_1km"]])
        proj = float(np.clip(x_e1 @ beta, 0.0, 1.0))
        estimator = dict(evidence_class="FLEET-REGRESSION-PROJECTION (not a score)",
                         n=len(est_rows), features=["1", "ov_h33", "sgmc_proxy_dti", "frac_gt_1km"],
                         coefficients=[float(v) for v in beta], loo_rmse=loo_rmse,
                         rows=est_rows,
                         candidate=dict(ov_h33=ov_h33, sgmc_proxy_dti=sg_e1,
                                        frac_gt_1km=fingerprint["frac_gt_1km"],
                                        projection=proj,
                                        interval_approx=[float(np.clip(proj - 1.96 * loo_rmse, 0, 1)),
                                                         float(np.clip(proj + 1.96 * loo_rmse, 0, 1))]),
                         caveat="Fitted only on OWNER-REPORTED live scores of locally measured fleet rasters; history says deviations from H33 lost score, so this projection cannot credit genuinely new truth mass. Never an ORGANIZER-CONFIRMED score.")
    else:
        estimator = dict(status="INSUFFICIENT_MATCHED_FLEET", n=len(est_rows), rows=est_rows)
        sg_e1 = sgmc["scores"][ARM_E1]["dti"]
    log(f"  estimator n={estimator.get('n')} projection={estimator.get('candidate', {}).get('projection')}")

    log("[9/9] Gates + serialization (fail-closed) + run card...")
    e1h, e2h = pooled["scores"][ARM_E1], pooled["scores"][ARM_E2]
    d_e2 = pooled["paired_differences"][ARM_E2]
    h33_sg = sgmc["scores"]["GEMSDOE32_H33"]["dti"]
    gates = {
        "G1_format_writer_pass": None,  # set after attempted write below
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
    name = f"gems86-h86r-sfg-strikegate-37654dots-{ts}-{dots_hash}-zeros"
    note = (f"H86R-SFG strike-gated edge fusion 37654d HOLD {e1h['dti']:.4f} SGMC {sg_e1:.4f} "
            f"ovH33 {ov_h33:.3f}; audit download, selector decides slot")
    assert len(name) <= 140 and len(note) <= 140, (len(name), len(note), note)
    receipt = None
    if gates["G5_uniqueness_scoped_discrete_le100k"]:
        receipt = write_candidate(fin[ARM_E1], g, name, note, metadata=dict(
            lane="H86R-SFG", evidence_class="LOCAL-FORMAT-VALIDATION",
            scoped_download_candidate=None))
        gates["G1_format_writer_pass"] = bool(
            receipt["independent_disk_validation"]["all_checks_passed"])
    else:
        gates["G1_format_writer_pass"] = False
        log("  G5 FAILED -> duplicate stop, no TIFF serialized")

    scoped_candidate = bool(gates["G1_format_writer_pass"] and gates["G2_canary_le_0p90"]
                            and gates["G3_holdout_E1_gt_E2_point"] and gates["G4_sgmc_E1_ge_H33_same_call"]
                            and gates["G5_uniqueness_scoped_discrete_le100k"])
    decision = "DOWNLOAD_CANDIDATE — owner/selector decides the weekly slot" if scoped_candidate else "DO NOT SUBMIT"

    evidence = dict(sample_size=int(sample.size), rows=surface_rows)
    (EV / "h86r-sfg-registry-surface.json").write_text(json.dumps(
        dict(schema="gems86.h86r.registry-surface.v1", evidence_class="REGISTRY-MEASUREMENT",
             candidate="H86R-SFG E1 full-catalogue surface (pre-placement)",
             worst=worst_rho, **evidence), indent=2) + "\n")
    (EV / "h86r-sfg-registry-final-dots.json").write_text(json.dumps(
        dict(schema="gems86.h86r.registry-final-dots.v1", evidence_class="REGISTRY-MEASUREMENT",
             candidate=name, discrete_le100k_checked=len(discrete), worst_discrete=worst_ov,
             dense_gt100k_reported_separately=dense, overlap_limit=0.70, rows=dot_rows,
             scope="Locally restored registry only (data/scored_fleet + data/scored + docs/downloads); NOT the full 713-raster upstream registry; full-support continuous rasters (e.g. 17GEMSDOE) make the literal gate fail for every nonempty candidate and are disclosed, not hidden."), indent=2) + "\n")
    (EV / "h86r-fleet-estimator-20261026.json").write_text(json.dumps(estimator, indent=2) + "\n")

    card = dict(
        schema="gems86.lane_run_card.v1", lane_id="H86R-SFG",
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        git_branch="arena/9c9712ca-gemsdoe86",
        preregistration=dict(path="research/H86R_SFG_PREREGISTRATION.json",
                             hypotheses_registry="registry/h86r_hypotheses_20261026.json",
                             sha256=sha256(PREREG)),
        hypothesis="Catalogue Strike-Field Gated Blind Potential-Field Edge Fusion: 5 native-band edge ranks fused multiline-corroborated (E=0.5*mean+0.5*2nd-highest), gated by spin-2 alignment A=cos^2(theta_E-theta_C) between verified gravity-gradient edge strike (B18,B11) and a 5 km-smoothed double-angle catalogue strike field (visible-only in folds): S=E*(0.35+0.65*A); 37,654 dots, 2.8 px Poisson-disk spacing, >3.0 px catalogue collar. Executes queued H86J-SCO.",
        mechanism=dict(static_features=list(planes.keys()),
                       fold_visible_features=["sfg_alignment_A_visible", "sfg_surface_E1_visible", "sfg_surface_E3_visible"],
                       note="Strike field smoothed on a 10-px block grid (sigma=5 blocks=50 px) then bilinearly upsampled; mathematically the frozen 5 km design, implemented coarsely for the 3 GB sandbox."),
        named_non_fault_mimic="Strike-parallel unfaulted lithologic contacts / depositional strike valleys along range fronts pass the gate; genuine perpendicular accommodation/transfer faults are down-weighted to the 0.35 floor.",
        input_sha256=input_hashes,
        leakage_canary=canary,
        leakage_canary_summary=dict(features_tested=len(canary), max_feature=worst[0],
                                    max_discriminative_auc=worst[1]["discriminative_auc"],
                                    threshold=0.90, any_leakage_flag=False),
        holdout_dti=dict(
            evidence_class="HOLDOUT-DTI", evaluator_version=EH.VERSION,
            evaluator_hashes=EH.implementation_hashes(),
            design="gems57-pooled-hide-v2: buffered_component_draw seed=20, 20% whole 8-connected components hidden per footprint-median quadrant, 3 px feature buffer, 12 px eroded domains, visible-only strike field + visible-only 3.0 px collar, pooled 200-px physical blocks, 1,000 paired bootstrap draws",
            withheld_positive_pixels=int(e1h["withheld_positive_pixels"]),
            candidate=e1h, all_arms=pooled["scores"], paired_differences=pooled["paired_differences"],
            per_fold=per_fold,
            beats_ablation_paired_ci=bool(d_e2["ci95"][0] > 0)),
        sgmc_proxy=dict(evidence_class="SGMC-PROXY-DTI", scores=sgmc.get("scores"),
                        paired_differences=sgmc.get("paired_differences_vs_candidate")),
        fingerprint=fingerprint,
        fleet_regression_projection=estimator.get("candidate"),
        fleet_estimator_file="docs/evidence/h86r-fleet-estimator-20261026.json",
        uniqueness_scoped=dict(surface_worst_sampled_rho=worst_rho, final_dots_worst_discrete=worst_ov,
                               overlap_vs_H33=ov_h33, discrete_le100k_checked=len(discrete),
                               dense_gt100k_count=len(dense),
                               surface_report="docs/evidence/h86r-sfg-registry-surface.json",
                               final_dots_report="docs/evidence/h86r-sfg-registry-final-dots.json"),
        gates=gates,
        scoped_download_candidate=scoped_candidate,
        raster_sha256=(receipt["sha256"] if receipt else None),
        zip_sha256=(receipt.get("zip_sha256") if receipt else None),
        validator_output=(receipt["independent_disk_validation"] if receipt else None),
        submission_name=name, submission_file=(f"docs/downloads/{name}.tif" if receipt else None),
        submission_zip=(f"docs/downloads/{name}.zip" if receipt else None),
        submission_receipt=(f"docs/downloads/{name}.json" if receipt else None),
        note=note, note_chars=len(note),
        verdict="negative",  # repo governance: no organizer receipt exists; see decision/scoped fields
        decision=("OK TO DOWNLOAD (scoped automated candidate) — DO NOT AUTO-SUBMIT; owner/selector spends the slot"
                  if scoped_candidate else "DO NOT SUBMIT"),
        scoped_decision=decision,
        submission_ready=False, safe_to_submit=False, approved_for_weekly_slot=False,
        submission_slots_used=0, experiments_run=3,
        runtime_seconds=round(time.time() - t0, 1),
    )
    (EV / "h86r-sfg-run-card.json").write_text(json.dumps(card, indent=2) + "\n")
    log(f"DONE scoped_candidate={scoped_candidate} gates={gates}")
    log(f"name={name} sha={card['raster_sha256']}")
    return 0


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    return run_pa86_lane()


if __name__ == "__main__":
    raise SystemExit(main())
