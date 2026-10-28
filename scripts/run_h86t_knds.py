#!/usr/bin/env python3
"""H86T-KNDS lane runner (preregistration: research/H86T_KNDS_PREREGISTRATION.json).

Transient Fluvial Iso-Chi Knickzone Downslope Back-Projection & Piedmont Hinge
Reception: projects footwall ksn/chi-step knickzones downslope along -grad(zmean_m)
across drainage-area-scaled distances onto the piedmont basement-hinge reception
zone (50 m < Z_b < 800 m, gated by Band 18 horizontal gravity gradient), with
Pleistocene Lake Lahontan (1315-1355 m) shoreline notch and symmetric-Bouguer
sill vetoes. 3 arms (E1 back-projected KNDS, E2 unprojected local-chi ablation,
E3 zero-chi native baseline), vendor gems57-pooled-hide-v2 holdout, SGMC-PROXY
diagnostic, leakage canary, scoped registry uniqueness, strict 23-row fleet
regression projection, and fail-closed vendor writer.
"""
from __future__ import annotations

from datetime import datetime, timezone
import csv as _csv
import gc
import hashlib
import json
from pathlib import Path
import re as _re
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
from gems86_knds import (  # noqa: E402
    ALL_FEATURE_NAMES,
    E1_FEATURES,
    E2_FEATURES,
    E3_FEATURES,
    KNDS_BACKPROJ_FEATURES,
    LOCAL_CHI_FEATURES,
    NATIVE_BASELINE_FEATURES,
    SEED,
    build_fold_visible_features,
    build_static_knds_stack,
    fit_predict_loqo_arm,
)
from scripts.run_h86k_stdp import (  # noqa: E402
    BUDGET,
    COLLAR_PX,
    evaluate_sgmc_proxy,
    load_binary_tif,
    prepare_canary_indices,
    score_canary_array,
    write_candidate,
)

FEATURE_TIF = ROOT / "data/training_features.tif"
CHI_TIF = ROOT / ".cache/external/dem10_chi_100m_i16.tif"
TOPO10_TIF = ROOT / ".cache/external/topo_10m_derived_100m_u8.tif"
PREREG = ROOT / "research/H86T_KNDS_PREREGISTRATION.json"
EV = ROOT / "docs/evidence"

PINS = {
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "dem10_chi_100m_i16.tif": "8897ba9c30ef1cd7ad5f23c16c6dfd7bb070e7e757f36fd9486eb45edfd973a5",
    "topo_10m_derived_100m_u8.tif": "a6398d9950965dec6aae6ccecdaa6ced48645d133eab222cbdd11def9bdabfa4",
    "derived_sgmc_faults_100m_u8.tif": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
}

ARM_E1 = "E1_knds_backprojected_loqo"
ARM_E2 = "E2_local_chi_unprojected_ablation"
ARM_E3 = "E3_native_no_chi_ablation"
ARMS = (ARM_E1, ARM_E2, ARM_E3)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def log(msg: str) -> None:
    print(msg, flush=True)


def registry_paths() -> list[Path]:
    paths: list[Path] = []
    for d in (ROOT / "data/scored_fleet", ROOT / "data/scored", ROOT / "docs/downloads"):
        paths.extend(p for p in sorted(d.glob("*.tif")) if "h86t-knds" not in p.name)
    return paths


def run_pa86_lane() -> int:
    # Imported callers must obey the same literal stop as the CLI.
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    if (EV / "h86t-knds-run-card.json").exists():
        raise FileExistsError(
            "H86T is archived; repaired code needs a newly preregistered lane "
            "and must not overwrite the historical run card or artifacts"
        )
    t0 = time.time()
    from scripts import protocol_preflight

    protocol_preflight.require_like_for_like()
    prereg = json.loads(PREREG.read_text())
    assert prereg["lane_id"] == "H86T-KNDS" and len(prereg["arms"]) == 3

    log("[1/9] Verifying pinned inputs...")
    pin_paths = {
        "training_features.tif": FEATURE_TIF,
        "existing_faults.tif": ROOT / "data/bridge/existing_faults.tif",
        "sample_submission.tif": ROOT / "data/bridge/sample_submission.tif",
        "dem10_chi_100m_i16.tif": CHI_TIF,
        "topo_10m_derived_100m_u8.tif": TOPO10_TIF,
        "derived_sgmc_faults_100m_u8.tif": ROOT / "data/external/derived_sgmc_faults_100m_u8.tif",
    }
    input_hashes = {}
    for name, p in pin_paths.items():
        h = sha256(p)
        if h != PINS[name]:
            raise ValueError(f"SHA-256 mismatch {name}: {h}")
        input_hashes[name] = h
    log("  all 6 pins OK")

    g = grid.load_grid(ROOT / "data/bridge")
    fp = np.asarray(g.footprint, bool)
    cat = np.asarray(g.catalogue, bool)

    log("[2/9] Building static KNDS + local-chi + native stack...")
    with rasterio.open(FEATURE_TIF) as src:
        static_planes = build_static_knds_stack(lambda i: src.read(i), fp, CHI_TIF, TOPO10_TIF)

    folds, _quad = holdout.buffered_component_draw(
        g, seed=SEED, hide_frac=0.20, buffer_px=3, boundary_px=12
    )
    vis = np.asarray(folds[0]["visible"], bool) & fp
    for f in folds[1:]:
        assert np.array_equal(np.asarray(f["visible"], bool) & fp, vis)

    vis_feats_ho = build_fold_visible_features(vis, fp, static_planes["_geophys_theta"])
    d_vis = vis_feats_ho.pop("_d_vis")
    planes_ho = dict(static_planes)
    planes_ho.update(vis_feats_ho)
    del vis_feats_ho
    gc.collect()

    log("[3/9] Training 4-fold 12-px eroded LOQO models on visible labels (holdout surfaces)...")
    surf_vis: dict[str, np.ndarray] = {}
    surf_vis[ARM_E1] = fit_predict_loqo_arm(planes_ho, E1_FEATURES, vis, fp, arm_id="E1")
    surf_vis[ARM_E2] = fit_predict_loqo_arm(planes_ho, E2_FEATURES, vis, fp, arm_id="E2")
    surf_vis[ARM_E3] = fit_predict_loqo_arm(planes_ho, E3_FEATURES, vis, fp, arm_id="E3")
    log("  visible LOQO models done")

    log("[4/9] Leakage canary (all 17 features + 3 visible LOQO surfaces)...")
    p_idx, n_idx, y = prepare_canary_indices(folds, fp)
    canary = {}
    canary_planes = {k: planes_ho[k] for k in ALL_FEATURE_NAMES}
    for arm in ARMS:
        canary_planes[f"{arm}_visible_surface"] = surf_vis[arm]
    for name, pl in canary_planes.items():
        canary[name] = score_canary_array(
            np.r_[pl.ravel()[p_idx], pl.ravel()[n_idx]].astype(np.float64), y
        )
    del canary_planes, planes_ho
    gc.collect()
    flagged = [k for k, v in canary.items() if v["leakage_flag"]]
    worst = max(canary.items(), key=lambda kv: kv[1]["discriminative_auc"])
    log(f"  canary worst={worst[0]} disc_auc={worst[1]['discriminative_auc']} flagged={flagged}")
    if flagged:
        raise RuntimeError(f"STOP leakage canary: {flagged}")

    log("[5/9] Holdout emissions + pooled scoring (3 arms + 2 comparators)...")
    allowed_ho = fp & (d_vis > COLLAR_PX)
    del d_vis
    reg_paths = registry_paths()
    h33_path = next(p for p in reg_paths if "GEMSDOE32" in p.name and "h33-h33-2" in p.name)
    h27_path = next(p for p in reg_paths if "GEMSDOE28" in p.name and "h27-4-r1" in p.name)
    h33_key = str(h33_path.relative_to(ROOT))
    h27_key = str(h27_path.relative_to(ROOT))
    h33_bin = load_binary_tif(h33_path) & fp
    h27_bin = load_binary_tif(h27_path) & fp

    ho_dots = {
        arm: emit_poisson_disk(surf_vis[arm], allowed_ho & np.isfinite(surf_vis[arm]), BUDGET)
        for arm in ARMS
    }
    del surf_vis
    gc.collect()
    ho_dots["H33_visible_collar"] = h33_bin & allowed_ho
    ho_dots["H27-4_visible_collar"] = h27_bin & allowed_ho

    terms = {k: None for k in ho_dots}
    per_fold = {k: {} for k in ho_dots}
    for f in folds:
        for name, dots in ho_dots.items():
            res, bt = EH.evaluate(dots.astype(np.float32), f, fp, block_side=200)
            terms[name] = bt if terms[name] is None else terms[name] + bt
            per_fold[name][f["name"]] = dict(
                evidence_class="HOLDOUT-DTI",
                evaluator_version=EH.VERSION,
                dti=res["dti"],
                n_truth=res["n_truth"],
                emitted=res["n_emitted"],
            )
        log(
            f"  fold {f['name']}: "
            + " | ".join(f"{n.split('_')[0]}={per_fold[n][f['name']]['dti']:.4f}" for n in ho_dots)
        )
    del ho_dots
    gc.collect()

    pooled = EH.pooled_summary(terms, draws=1000, seed=861826, candidate=ARM_E1)
    for n, s in pooled["scores"].items():
        log(f"  HOLDOUT-DTI {n}: {s['dti']:.4f} [{s['ci95'][0]:.4f},{s['ci95'][1]:.4f}]")

    log("[6/9] Training full-catalogue LOQO models + final emissions + SGMC + null...")
    vis_feats_full = build_fold_visible_features(cat, fp, static_planes["_geophys_theta"])
    d_cat = vis_feats_full.pop("_d_vis")
    planes_full = dict(static_planes)
    planes_full.update(vis_feats_full)
    del static_planes, vis_feats_full
    gc.collect()

    surf_full: dict[str, np.ndarray] = {}
    surf_full[ARM_E1] = fit_predict_loqo_arm(planes_full, E1_FEATURES, cat, fp, arm_id="E1")
    surf_full[ARM_E2] = fit_predict_loqo_arm(planes_full, E2_FEATURES, cat, fp, arm_id="E2")
    surf_full[ARM_E3] = fit_predict_loqo_arm(planes_full, E3_FEATURES, cat, fp, arm_id="E3")
    del planes_full
    gc.collect()

    allowed_full = fp & (d_cat > COLLAR_PX)
    fin = {
        arm: emit_poisson_disk(surf_full[arm], allowed_full & np.isfinite(surf_full[arm]), BUDGET)
        for arm in ARMS
    }
    del surf_full[ARM_E2], surf_full[ARM_E3]
    gc.collect()

    rng2 = np.random.default_rng(861826)
    null_order = rng2.permutation(np.flatnonzero(allowed_full.ravel()))
    fin["RANDOM_NULL_seed861826"] = emit_poisson_disk(
        np.zeros_like(surf_full[ARM_E1]), allowed_full, BUDGET, rng_order=null_order
    )
    sgmc_in = {
        **fin,
        "GEMSDOE32_H33": h33_bin,
        "GEMSDOE28_H27-4": h27_bin,
    }
    sgmc = evaluate_sgmc_proxy(sgmc_in, fp, cat, candidate_key=ARM_E1)
    del sgmc_in
    dcat_dots = d_cat[fin[ARM_E1]]
    fingerprint = dict(
        dots=int(fin[ARM_E1].sum()),
        min_dcat_px=float(dcat_dots.min()),
        median_dcat_m=float(np.median(dcat_dots) * 100.0),
        frac_gt_1km=float((dcat_dots > 10).mean()),
        frac_le_3px=float((dcat_dots <= 3).mean()),
    )
    log(
        f"  E1 fingerprint {fingerprint}; SGMC E1={sgmc['scores'][ARM_E1]['dti']:.4f} "
        f"E2={sgmc['scores'][ARM_E2]['dti']:.4f} E3={sgmc['scores'][ARM_E3]['dti']:.4f} "
        f"H33={sgmc['scores']['GEMSDOE32_H33']['dti']:.4f}"
    )

    log("[7/9] Surface & final-dot uniqueness + strict fleet estimator (streaming single pass)...")
    rng = np.random.default_rng(861826)
    fp_flat = np.flatnonzero(fp.ravel())
    sample = rng.choice(fp_flat, size=min(400_000, fp_flat.size), replace=False)
    surf_s = rankdata(surf_full[ARM_E1].ravel()[sample].astype(np.float64))
    surf_s = (surf_s - surf_s.mean()) / (surf_s.std() + 1e-12)
    del surf_full
    gc.collect()

    scores = {}
    with (ROOT / "registry/prior_scores.csv").open() as f_csv:
        for row in _csv.DictReader(f_csv):
            try:
                scores[row["submission"].lower()] = float(row["score"])
            except Exception:
                pass

    def match_score(rel: str):
        base = Path(rel).stem.lower()
        for _p in (
            "gemsdoe32__", "gemsdoe36__", "gemsdoe33__", "gemsdoe28__",
            "gemsdoe49__", "gemsdoe63__", "gemsdoe66__", "gemsdoe70__",
            "gemsdoe73__", "gemsdoe75__", "gemsdoe76__", "gemsdoe78__",
            "gemsdoe80__", "gemsdoe81__", "gemsdoe82__", "gemsdoe83__",
            "gemsdoe85__", "gemsdoe88__",
        ):
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
        toks = [
            t for t in _re.split(r"[-_]", base)
            if _re.fullmatch(r"[0-9a-f]{8,}", t) and any(c.isalpha() for c in t)
        ]
        for s, sc in scores.items():
            if any(t in s for t in toks):
                return sc
        return None

    near_h33 = uniqueness._near(h33_bin)
    surface_rows = []
    dot_rows = []
    est_rows, seen = [], set()
    missing_fleet_binaries: dict[str, np.ndarray] = {}
    cached_sgmc: dict[str, float] = {}
    prior_est_path = EV / "h86s-dwpu-fleet-estimator-20261027.json"
    if prior_est_path.is_file():
        for pr_row in json.loads(prior_est_path.read_text()).get("rows", []):
            if "file" in pr_row and "sgmc_proxy_dti" in pr_row:
                cached_sgmc[pr_row["file"]] = float(pr_row["sgmc_proxy_dti"])

    for p in reg_paths:
        rel = str(p.relative_to(ROOT))
        b = load_binary_tif(p) & fp
        n_b = int(b.sum())
        bs = b.ravel()[sample].astype(np.float64)
        if bs.std() == 0:
            rho = 0.0
        else:
            rb = rankdata(bs)
            rho = float(np.corrcoef(surf_s, (rb - rb.mean()) / (rb.std() + 1e-12))[0, 1])
        surface_rows.append(dict(file=rel, their_dots=n_b, sampled_spearman=round(rho, 4)))

        ov_val = round(float(uniqueness.dot_overlap(fin[ARM_E1], b)), 4)
        dot_rows.append(dict(file=rel, their_dots=n_b, forward_overlap_3px=ov_val))

        if "/downloads/" not in rel and n_b > 0:
            sc = match_score(rel)
            if sc is not None:
                ov_33 = float(near_h33[b].mean())
                key = (n_b, round(ov_33, 4), sc)
                if key not in seen:
                    seen.add(key)
                    dd = d_cat[b]
                    est_rows.append(
                        dict(
                            file=rel,
                            dots=n_b,
                            live_owner_reported=sc,
                            ov_h33=ov_33,
                            frac_gt_1km=float((dd > 10).mean()),
                        )
                    )
                    if rel not in cached_sgmc:
                        missing_fleet_binaries[rel] = b.copy()
        del b

    worst_rho = max(surface_rows, key=lambda r: abs(r["sampled_spearman"]))
    log(
        f"  {len(surface_rows)} registry rasters; worst sampled rho={worst_rho['sampled_spearman']} vs {worst_rho['file']}"
    )

    log("[8/9] Final-dot uniqueness summary + strict 20-row fleet estimator...")
    discrete = [r for r in dot_rows if r["their_dots"] <= 100_000]
    dense = [r for r in dot_rows if r["their_dots"] > 100_000]
    worst_ov = max(discrete, key=lambda r: r["forward_overlap_3px"]) if discrete else None
    ov_h33 = next(r["forward_overlap_3px"] for r in dot_rows if r["file"] == h33_key)
    log(
        f"  discrete<=100k: {len(discrete)}, worst={worst_ov['forward_overlap_3px']} vs {worst_ov['file']}; ovH33={ov_h33}"
    )

    estimator = dict(status="INSUFFICIENT_MATCHED_FLEET", n=len(est_rows), rows=est_rows)
    sg_e1 = sgmc["scores"][ARM_E1]["dti"]
    if len(est_rows) >= 6:
        if missing_fleet_binaries:
            extra = {f"EST::{rel}": arr for rel, arr in missing_fleet_binaries.items()}
            first_k = next(iter(extra))
            sg = evaluate_sgmc_proxy(extra, fp, cat, candidate_key=first_k)
            for rel in missing_fleet_binaries:
                cached_sgmc[rel] = float(sg["scores"][f"EST::{rel}"]["dti"])
            del extra, missing_fleet_binaries
        for r in est_rows:
            r["sgmc_proxy_dti"] = cached_sgmc[r["file"]]
        X = np.array([[1.0, r["ov_h33"], r["sgmc_proxy_dti"], r["frac_gt_1km"]] for r in est_rows])
        yv = np.array([r["live_owner_reported"] for r in est_rows])
        beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
        loo = []
        for i in range(len(est_rows)):
            m = np.ones(len(est_rows), bool)
            m[i] = False
            bi, *_ = np.linalg.lstsq(X[m], yv[m], rcond=None)
            loo.append(yv[i] - float(X[i] @ bi))
        loo_rmse = float(np.sqrt(np.mean(np.square(loo))))
        x_e1 = np.array([1.0, ov_h33, sg_e1, fingerprint["frac_gt_1km"]])
        proj = float(np.clip(x_e1 @ beta, 0.0, 1.0))
        estimator = dict(
            evidence_class="FLEET-REGRESSION-PROJECTION (not a score)",
            n=len(est_rows),
            features=["1", "ov_h33", "sgmc_proxy_dti", "frac_gt_1km"],
            coefficients=[float(v) for v in beta],
            loo_rmse=loo_rmse,
            rows=est_rows,
            candidate=dict(
                ov_h33=ov_h33,
                sgmc_proxy_dti=sg_e1,
                frac_gt_1km=fingerprint["frac_gt_1km"],
                projection=proj,
                interval_approx=[
                    float(np.clip(proj - 1.96 * loo_rmse, 0, 1)),
                    float(np.clip(proj + 1.96 * loo_rmse, 0, 1)),
                ],
            ),
            caveat="Fitted only on OWNER-REPORTED live scores; never ORGANIZER-CONFIRMED; cannot credit genuinely new truth mass.",
        )

    log("[9/9] Gates + serialization + run card...")
    e1h, e2h, e3h = pooled["scores"][ARM_E1], pooled["scores"][ARM_E2], pooled["scores"][ARM_E3]
    d_e2 = pooled["paired_differences"][ARM_E2]
    d_e3 = pooled["paired_differences"][ARM_E3]
    h33_sg = sgmc["scores"]["GEMSDOE32_H33"]["dti"]
    gates = {
        "G1_format_writer_pass": None,
        "G2_canary_le_0p90": not flagged,
        "G3_holdout_E1_gt_E2_point": bool(e1h["dti"] > e2h["dti"]),
        "G3_holdout_E1_gt_E2_paired_ci_excludes_0": bool(d_e2["ci95"][0] > 0),
        "G3_holdout_E1_gt_repo_loqo_record_0p1727": bool(e1h["dti"] > 0.1727),
        "G4_sgmc_E1_ge_H33_same_call": bool(sg_e1 >= h33_sg),
        "G5_uniqueness_scoped_discrete_le100k": bool(
            worst_ov
            and worst_ov["forward_overlap_3px"] <= 0.70
            and abs(worst_rho["sampled_spearman"]) <= 0.90
        ),
        "G6_fingerprint_37654_min_dcat_gt3": bool(
            fingerprint["dots"] == BUDGET and fingerprint["min_dcat_px"] > 3.0
        ),
    }

    # Historical TIFFs and receipts are immutable. The shared writer rejects
    # collisions; never delete earlier artifacts to make room for another run.

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dots_hash = hashlib.sha256(fin[ARM_E1].tobytes()).hexdigest()[:8]
    name = f"gems86-h86t-knds-37654dots-{ts}-{dots_hash}-zeros"
    note = (
        f"H86T-KNDS iso-chi backproj 37654d HOLD {e1h['dti']:.4f} SGMC {sg_e1:.4f} "
        f"ovH33 {ov_h33:.3f}; audit only, DO NOT SUBMIT"
    )
    assert len(name) <= 140 and len(note) <= 140, (len(name), len(note))
    receipt = None
    if gates["G5_uniqueness_scoped_discrete_le100k"]:
        receipt = write_candidate(
            fin[ARM_E1],
            g,
            name,
            note,
            metadata=dict(
                lane="H86T-KNDS",
                evidence_class="LOCAL-FORMAT-VALIDATION",
                scoped_download_candidate=None,
            ),
        )
        gates["G1_format_writer_pass"] = bool(
            receipt["independent_disk_validation"]["all_checks_passed"]
        )
    else:
        gates["G1_format_writer_pass"] = False
        log("  G5 FAILED -> duplicate stop, no TIFF serialized")

    scoped_candidate = bool(
        gates["G1_format_writer_pass"]
        and gates["G2_canary_le_0p90"]
        and gates["G3_holdout_E1_gt_E2_point"]
        and gates["G3_holdout_E1_gt_E2_paired_ci_excludes_0"]
        and gates["G3_holdout_E1_gt_repo_loqo_record_0p1727"]
        and gates["G4_sgmc_E1_ge_H33_same_call"]
        and gates["G5_uniqueness_scoped_discrete_le100k"]
        and gates["G6_fingerprint_37654_min_dcat_gt3"]
    )
    verdict = "promote" if scoped_candidate else "negative"
    decision = (
        "DOWNLOAD_CANDIDATE — selector decides weekly slot; DO NOT AUTO-SUBMIT"
        if scoped_candidate
        else "DO NOT SUBMIT"
    )

    (EV / "h86t-knds-registry-surface.json").write_text(
        json.dumps(
            dict(
                schema="gems86.h86t.registry-surface.v1",
                evidence_class="REGISTRY-MEASUREMENT",
                candidate="H86T-KNDS E1 full-catalogue surface",
                worst=worst_rho,
                sample_size=int(sample.size),
                rows=surface_rows,
            ),
            indent=2,
        )
        + "\n"
    )
    (EV / "h86t-knds-registry-final-dots.json").write_text(
        json.dumps(
            dict(
                schema="gems86.h86t.registry-final-dots.v1",
                evidence_class="REGISTRY-MEASUREMENT",
                candidate=name,
                discrete_le100k_checked=len(discrete),
                worst_discrete=worst_ov,
                dense_gt100k_reported_separately=dense,
                overlap_limit=0.70,
                rows=dot_rows,
                scope="Locally restored registry only (data/scored_fleet + data/scored + docs/downloads); NOT full upstream registry; literal full-support witness gate fails for every nonempty candidate and is disclosed.",
            ),
            indent=2,
        )
        + "\n"
    )
    (EV / "h86t-knds-fleet-estimator-20261027.json").write_text(
        json.dumps(estimator, indent=2) + "\n"
    )

    card = dict(
        schema="gems86.lane_run_card.v1",
        lane_id="H86T-KNDS",
        generated_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        git_branch="arena/70644855-gemsdoe86",
        preregistration=dict(
            path="research/H86T_KNDS_PREREGISTRATION.json",
            hypotheses_registry="registry/h86t_hypotheses_20261027.json",
            sha256=sha256(PREREG),
        ),
        hypothesis=(
            "Transient Fluvial Iso-Chi Knickzone Downslope Back-Projection & Piedmont Hinge Reception (H86T-KNDS): "
            "back-projecting footwall channel-steepness (ksn_max_m0.9) and positive chi-step (step_max_x1000 - step_min_x1000) "
            "knickzones downslope along -grad(zmean_m)/||grad(zmean_m)|| across drainage-area-scaled shifts s in {4, 8, 14, 22} px "
            "onto the piedmont basement-hinge reception zone (50 m < Z_b < 800 m, gated by Band 18 horizontal gravity gradient) "
            "with along-strike iso-chi coherence; 4-fold 12-px eroded LOQO HGB PU, 37,654 dots, 2.8 px Poisson spacing, >3.0 px collar."
        ),
        mechanism=dict(
            knds_backprojected_features=list(KNDS_BACKPROJ_FEATURES),
            local_chi_features=list(LOCAL_CHI_FEATURES),
            native_baseline_features=list(NATIVE_BASELINE_FEATURES),
            downslope_shifts_px=[4, 8, 14, 22],
            model="4-fold 12-px eroded Leave-One-Quadrant-Out HistGradientBoosting (120 iters) + 0.35 physical structural prior",
        ),
        named_non_fault_mimic=(
            "Pleistocene Lake Lahontan wave-cut shorelines (~1335 m +/- 18 m highstand bench) and resistant Tertiary "
            "basalt/welded-tuff caprock ledges (suppressed via the 1315-1355 m Lahontan hypsometric notch filter and "
            "symmetric Bouguer gravity Laplacian sill veto)."
        ),
        input_sha256=input_hashes,
        leakage_canary=canary,
        leakage_canary_summary=dict(
            features_tested=len(canary),
            max_feature=worst[0],
            max_discriminative_auc=worst[1]["discriminative_auc"],
            threshold=0.90,
            any_leakage_flag=bool(flagged),
        ),
        holdout_dti=dict(
            evidence_class="HOLDOUT-DTI",
            evaluator_version=EH.VERSION,
            evaluator_hashes=EH.implementation_hashes(),
            design="gems57-pooled-hide-v2 seed=20, 20% whole components hidden/quadrant, 3px buffer, 12px eroded LOQO, visible-only training + collar, pooled 200px blocks, 1000 paired bootstrap seed 861826",
            withheld_positive_pixels=int(e1h["withheld_positive_pixels"]),
            candidate=e1h,
            all_arms=pooled["scores"],
            paired_differences=pooled["paired_differences"],
            per_fold=per_fold,
            beats_ablation_paired_ci=bool(d_e2["ci95"][0] > 0),
            beats_native_no_chi_paired_ci=bool(d_e3["ci95"][0] > 0),
        ),
        sgmc_proxy=dict(
            evidence_class="SGMC-PROXY-DTI",
            scores=sgmc.get("scores"),
            paired_differences=sgmc.get("paired_differences_vs_candidate"),
        ),
        fingerprint=fingerprint,
        fleet_regression_projection=estimator.get("candidate"),
        fleet_estimator_file="docs/evidence/h86t-knds-fleet-estimator-20261027.json",
        uniqueness_scoped=dict(
            surface_worst_sampled_rho=worst_rho,
            final_dots_worst_discrete=worst_ov,
            overlap_vs_H33=ov_h33,
            discrete_le100k_checked=len(discrete),
            dense_gt100k_count=len(dense),
            surface_report="docs/evidence/h86t-knds-registry-surface.json",
            final_dots_report="docs/evidence/h86t-knds-registry-final-dots.json",
            literal_witness_status="STOP_LITERAL_OVERLAP_UNSATISFIABLE (docs/evidence/protocol-preflight.json, 17GEMSDOE continuous full-support witness) - disclosed, not hidden; scoped like-for-like reading used per PA-86-01",
        ),
        gates=gates,
        scoped_download_candidate=scoped_candidate,
        raster_sha256=(receipt["sha256"] if receipt else None),
        zip_sha256=(receipt.get("zip_sha256") if receipt else None),
        validator_output=(receipt["independent_disk_validation"] if receipt else None),
        submission_name=name,
        submission_file=(f"docs/downloads/{name}.tif" if receipt else None),
        submission_zip=(f"docs/downloads/{name}.zip" if receipt else None),
        submission_receipt=(f"docs/downloads/{name}.json" if receipt else None),
        note=note,
        note_chars=len(note),
        verdict=verdict,
        decision=decision,
        scoped_decision=decision,
        submission_ready=False,
        safe_to_submit=False,
        approved_for_weekly_slot=False,
        submission_slots_used=0,
        experiments_run=3,
        runtime_seconds=round(time.time() - t0, 1),
    )
    (EV / "h86t-knds-run-card.json").write_text(json.dumps(card, indent=2) + "\n")
    log(f"DONE verdict={verdict} scoped_candidate={scoped_candidate} gates={gates}")
    log(f"name={name} sha={card['raster_sha256']}")
    return 0


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    return run_pa86_lane()


if __name__ == "__main__":
    raise SystemExit(main())
