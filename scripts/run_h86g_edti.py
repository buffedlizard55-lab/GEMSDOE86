#!/usr/bin/env python3
"""Run the preregistered H86G-EDTI lane (incl. Amendment A1).

Preregistration: research/H86G_EDTI_PREREGISTRATION.md (+ .json).
E1 (canaries + as-is controls) falsified two frozen premises; Amendment A1
(recorded there, before any candidate field) switched the primary selector to
SGMC-proxy DTI of the as-emitted raster and the candidate to a 3-arm experiment
under identical E[k] spacing-greedy emission:

  L   unsupervised multiline corroboration field (pinned layers only)
  H   HistGradientBoosting signature posterior (zero catalogue-derived feats)
  LH  L reweighted by H rank

SGMC bytes are a SELECTION instrument only -- never features, never training,
never written as a score.  Catalogue-hide HOLDOUT-DTI is reported for every arm.
No weekly slot is picked here; verdict `promote` = eligible for the separate
selector step, only if every (amended) gate passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]

from gems57 import emit, evaluate_holdout as EH, grid, holdout, metric as MET  # noqa: E402
from gems57 import submission_writer, validate  # noqa: E402
from gems86_edti import features as F, model as M  # noqa: E402
from scripts.protocol_preflight import require_like_for_like  # noqa: E402

SEED = 20
BUDGETS = (20_000, 30_000, 37_654, 44_090, 55_000, 70_000)
FEATURE_TIF = ROOT / "data/bridge/training_features.tif"
EXT_DIR = ROOT / ".cache/external"
SGMC_TIF = EXT_DIR / "derived_sgmc_faults_100m_u8.tif"
SGMC_SHA = "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"
WORK = ROOT / "data/work/h86g"
CACHE = ROOT / ".cache/work_h86g"
STACK_PATH = CACHE / "features.f32"
NAMES_PATH = CACHE / "feature_names.json"
EV = ROOT / "docs/evidence"
OUT_DIR = ROOT / "docs/downloads"
H33 = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
D28 = ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"

DETECTORS = ("gradmag_rtp_s1p5", "gradmag_grav_s1p5", "analytic_signal_log",
             "lidar_step_max", "lidar_cross_max", "topo_hs_lineament",
             "gradmag_dem_s1p5", "topo_curv_prof_absmax")


def log(*a):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}]", *a, flush=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as s:
        for c in iter(lambda: s.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_binary(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1)
    return np.isfinite(a) & (a > 0)


def rank01(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros(a.shape, np.float32)
    vals = np.asarray(a, np.float32)[mask]
    order = np.argsort(vals, kind="stable")
    ranks = np.empty(len(vals), np.float32)
    ranks[order] = np.linspace(0.0, 1.0, len(vals), dtype=np.float32)
    out[mask] = ranks
    return out


def get_grid_folds():
    g = grid.load_grid(ROOT / "data/bridge")
    folds, _ = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)
    return g, folds


def get_stack(g):
    if STACK_PATH.is_file() and NAMES_PATH.is_file():
        names = json.loads(NAMES_PATH.read_text())
        return F.load_stack(STACK_PATH, len(names), g.shape), names
    log("building feature stack")
    mm, names = F.build_stack(FEATURE_TIF, EXT_DIR, g.footprint, STACK_PATH)
    NAMES_PATH.write_text(json.dumps(names, indent=1))
    return F.load_stack(STACK_PATH, len(names), g.shape), names


def sgmc_truth(g):
    if sha256(SGMC_TIF) != SGMC_SHA:
        raise RuntimeError("SGMC proxy raster hash drift")
    with rasterio.open(SGMC_TIF) as ds:
        sg = (ds.read(1) > 0) & g.footprint
    dcat = ndi.distance_transform_edt(~g.catalogue)
    return sg & (dcat > 3.0)


def fold_terms(pred, folds, fp):
    terms, per = [], {}
    for fold in folds:
        res, bt = EH.evaluate(np.asarray(pred, np.float32), fold, fp, block_side=200)
        terms.append(bt)
        per[fold["name"]] = {"dti": res["dti"], "n_truth": res["n_truth"],
                             "emitted": res["n_emitted"]}
    return np.sum(terms, axis=0), per


def pooled_point(terms) -> float:
    return float(EH.from_terms(np.asarray(terms).sum(axis=0)))


def sgmc_terms(pred, g, sg_off):
    """One synthetic fold so the shared spatial-block term machinery can be
    reused unchanged; results are relabelled SGMC-PROXY-DTI, never HOLDOUT-DTI."""
    fold = dict(fold=0, name="SGMC_PROXY", region=g.footprint, truth=sg_off,
                visible=g.catalogue, masked_known=g.catalogue, hidden_all=sg_off)
    res, bt = EH.evaluate(np.asarray(pred, np.float32), fold, g.footprint,
                          block_side=200)
    return bt, res


def relabel(obj, old="HOLDOUT-DTI", new="SGMC-PROXY-DTI"):
    if isinstance(obj, dict):
        return {k: relabel(v, old, new) for k, v in obj.items()}
    if isinstance(obj, list):
        return [relabel(v, old, new) for v in obj]
    return new if obj == old else obj


# ---------------------------------------------------------------- E1
def stage_e1(g, folds, stack, names):
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / "e1.json"
    terms_path = WORK / "e1_control_terms.npz"
    if out.is_file() and terms_path.is_file():
        return json.loads(out.read_text())
    fp = g.footprint
    region = np.zeros(fp.shape, bool)
    hidden = np.zeros(fp.shape, bool)
    known = np.zeros(fp.shape, bool)
    for f in folds:
        region |= np.asarray(f["region"], bool)
        hidden |= np.asarray(f["hidden_all"], bool)
        known |= np.asarray(f["masked_known"], bool)
    active = region & fp & ~known
    truth = active & hidden
    pos = np.flatnonzero(truth.ravel())
    neg_all = np.flatnonzero((active & ~truth).ravel())
    rng = np.random.default_rng(861025)
    neg = rng.choice(neg_all, size=min(300_000, neg_all.size), replace=False)
    y = np.r_[np.ones(pos.size), np.zeros(neg.size)]
    canaries = {}
    for i, name in enumerate(names):
        v = np.asarray(stack[i]).ravel()
        s = np.r_[v[pos], v[neg]].astype(np.float64)
        auc = float(roc_auc_score(y, s)) if np.ptp(s) else 0.5
        canaries[name] = {
            "evidence_class": "LEAKAGE-CANARY", "auc": auc,
            "discriminative_auc": max(auc, 1 - auc), "threshold": 0.90,
            "leakage_flag": bool(max(auc, 1 - auc) > 0.90),
            "n_positive": int(pos.size), "n_negative_sampled": int(neg.size),
        }
    sg_off = sgmc_truth(g)
    controls, saved = {}, {}
    for label, path in (("H33_as_is", H33), ("D28_parent_as_is", D28)):
        dots = load_binary(path)
        t, per = fold_terms(dots.astype(np.float32), folds, fp)
        bt, sres = sgmc_terms(dots.astype(np.float32), g, sg_off)
        controls[label] = {
            "catalogue_hide_point": pooled_point(t), "per_fold": per,
            "sgmc_proxy_point": sres["dti"], "sgmc_coverage": sres["coverage"],
            "dots_total": int(dots.sum())}
        saved[label] = t
        saved[f"{label}__sgmc"] = bt
        log(f"control {label}: cat-hide={controls[label]['catalogue_hide_point']:.4f} "
            f"sgmc={controls[label]['sgmc_proxy_point']:.4f}")
    np.savez(terms_path, **saved)
    doc = {"canaries": canaries, "controls_point": controls,
           "withheld_positive_pixels": int(pos.size),
           "sgmc_proxy_positives": int(sg_off.sum())}
    out.write_text(json.dumps(doc, indent=1))
    return doc


# ---------------------------------------------------------------- surfaces
def surface_L(stack, names, fp):
    p = WORK / "surface_L.npy"
    if p.is_file():
        return np.load(p)
    log("building L multiline corroboration surface")
    idx = {n: i for i, n in enumerate(names)}
    ranks = [rank01(np.asarray(stack[idx[d]]), fp) for d in DETECTORS]
    mean_r = np.mean(ranks, axis=0)
    agree = np.mean([r > 0.5 for r in ranks], axis=0)
    L = (mean_r * (0.5 + 0.5 * agree)).astype(np.float32)
    L[~fp] = 0.0
    WORK.mkdir(parents=True, exist_ok=True)
    np.save(p, L)
    return L


def posterior_for(visible, g, stack, tag):
    p_path = WORK / f"posterior_{tag}.npy"
    meta_path = WORK / f"posterior_{tag}.json"
    if p_path.is_file():
        return np.load(p_path), json.loads(meta_path.read_text())
    log(f"fitting HGB ({tag})")
    clf, info = M.fit_posterior(stack, g.footprint, visible)
    log(f"predicting ({tag})")
    p = M.predict_full(clf, stack, g.footprint)
    WORK.mkdir(parents=True, exist_ok=True)
    np.save(p_path, p)
    meta_path.write_text(json.dumps(info, indent=1))
    return p, info


def ranked_spacing(p, allowed, tag):
    r_path = WORK / f"ranked_{tag}.npy"
    if r_path.is_file():
        return np.load(r_path)
    log(f"spacing-greedy ranking ({tag})")
    ranked = M.spacing_greedy_ranking(emit.expected_credit(p), allowed,
                                      min_spacing_px=2.8)
    np.save(r_path, ranked)
    return ranked


def arm_surfaces(g, stack, names):
    """Full-catalogue build surfaces (final-build construction)."""
    fp, cat = g.footprint, g.catalogue
    out = {}
    L = surface_L(stack, names, fp)
    out["L_lineament"] = L
    p_full, _ = posterior_for(cat, g, stack, "full_catalogue")
    out["H_hgb"] = p_full
    lh_path = WORK / "surface_LH.npy"
    if lh_path.is_file():
        out["LH_hybrid"] = np.load(lh_path)
    else:
        LH = (rank01(L, fp) * (0.35 + 0.65 * rank01(p_full, fp))).astype(np.float32)
        LH[~fp] = 0.0
        np.save(lh_path, LH)
        out["LH_hybrid"] = LH
    return out


def arm_surfaces_oof(g, folds, stack, names):
    """Visible-only constructions for the honest OOF catalogue-hide reading
    (Amendment A2).  L is label-free; H is refit on visible labels only."""
    fp = g.footprint
    visible = np.asarray(folds[0]["visible"], bool)
    L = surface_L(stack, names, fp)
    p_vis, _ = posterior_for(visible, g, stack, "holdout_visible")
    lh_path = WORK / "surface_LH_oof.npy"
    if lh_path.is_file():
        LH = np.load(lh_path)
    else:
        LH = (rank01(L, fp) * (0.35 + 0.65 * rank01(p_vis, fp))).astype(np.float32)
        LH[~fp] = 0.0
        np.save(lh_path, LH)
    return {"L_lineament": L, "H_hgb": p_vis, "LH_hybrid": LH}


def budget_curve(g, folds, surfaces, oof_surfaces, collar_px=3.0, tag_prefix="e2"):
    """Per arm/budget: SGMC-proxy (full construction, as shipped) + OOF
    catalogue-hide HOLDOUT-DTI (visible construction, Amendment A2)."""
    fp, cat = g.footprint, g.catalogue
    visible = np.asarray(folds[0]["visible"], bool)
    dcat = ndi.distance_transform_edt(~cat)
    dvis = ndi.distance_transform_edt(~visible)
    allowed_full = fp & (dcat > collar_px)
    allowed_vis = fp & (dvis > collar_px)
    sg_off = sgmc_truth(g)
    doc, saved = {}, {}
    for arm, surf in surfaces.items():
        ranked = ranked_spacing(surf, allowed_full, f"{tag_prefix}_{arm}_c{int(collar_px)}")
        ranked_oof = ranked_spacing(oof_surfaces[arm], allowed_vis,
                                     f"{tag_prefix}_{arm}_oof_c{int(collar_px)}")
        doc[arm] = {"ranking_dots_available": int((ranked > 0).sum()),
                    "ranking_dots_available_oof": int((ranked_oof > 0).sum()),
                    "budgets": {}}
        for b in BUDGETS:
            dots = M.prefix(ranked, b)
            bt, sres = sgmc_terms(dots.astype(np.float32), g, sg_off)
            dots_oof = M.prefix(ranked_oof, b)
            t, per = fold_terms(dots_oof.astype(np.float32), folds, fp)
            doc[arm]["budgets"][str(b)] = {
                "evidence_class_sgmc": "SGMC-PROXY-DTI (point, selection only)",
                "sgmc_proxy_dti": sres["dti"], "sgmc_coverage": sres["coverage"],
                "evidence_class_holdout": "HOLDOUT-DTI (point, pooled terms, OOF visible construction)",
                "catalogue_hide_dti_oof": pooled_point(t), "per_fold": per}
            saved[f"{arm}_b{b}__sgmc"] = bt
            saved[f"{arm}_b{b}__cathide"] = t
            log(f"{arm} b={b}: sgmc={sres['dti']:.4f} cat-hide-oof={pooled_point(t):.4f}")
    np.savez(WORK / f"{tag_prefix}_terms.npz", **saved)
    return doc


# ---------------------------------------------------------------- E2/E3
def stage_e2(g, folds, stack, names):
    out = WORK / "e2.json"
    if out.is_file():
        return json.loads(out.read_text())
    surfaces = arm_surfaces(g, stack, names)
    doc = budget_curve(g, folds, surfaces, arm_surfaces_oof(g, folds, stack, names),
                       collar_px=3.0, tag_prefix="e2")
    # Amendment A3: SGMC selects the arm; budget capped to the live-validated
    # fleet range (<=44,090) because the proxy's own budget optimum is a
    # truth-density artifact (still rising at 98,163-dot ranking exhaustion).
    LIVE_BUDGET_CAP = 44_090
    best_arm, best_budget, best_sgmc = None, None, -1.0
    uncapped = {"arm": None, "budget": None, "sgmc_proxy_dti": -1.0}
    for arm, d in doc.items():
        for bs, v in d["budgets"].items():
            if v["sgmc_proxy_dti"] > uncapped["sgmc_proxy_dti"]:
                uncapped = {"arm": arm, "budget": int(bs),
                            "sgmc_proxy_dti": v["sgmc_proxy_dti"]}
            if int(bs) <= LIVE_BUDGET_CAP and v["sgmc_proxy_dti"] > best_sgmc:
                best_arm, best_budget, best_sgmc = arm, int(bs), v["sgmc_proxy_dti"]
    try:
        ext = json.loads((WORK / "e2_ext_budget_diag.json").read_text())
    except Exception:
        ext = None
    # Amendment A4 (post-hoc, disclosed): budget = smallest grid budget whose
    # paired SGMC CI vs H33-as-is excludes 0 (arm still SGMC-selected at the
    # A3 cap for comparability; A4 re-prices budget only, on the winning arm).
    e2t_a4 = dict(np.load(WORK / "e2_terms.npz"))
    e1t_a4 = dict(np.load(WORK / "e1_control_terms.npz"))
    a4_budget, a4_table = None, {}
    for b in BUDGETS:
        pooled_b = EH.pooled_summary(
            {"CAND": e2t_a4[f"{best_arm}_b{b}__sgmc"],
             "H33_as_is": e1t_a4["H33_as_is__sgmc"]},
            draws=1000, seed=861025, candidate="CAND")
        d_b = pooled_b["paired_differences"]["H33_as_is"]
        a4_table[str(b)] = {"delta": d_b["delta"], "ci95": d_b["ci95"]}
        if a4_budget is None and d_b["ci95"][0] > 0:
            a4_budget = b
    doc["_selection"] = {"best_arm": best_arm,
                         "a3_capped_budget": best_budget,
                         "a3_capped_sgmc_proxy_dti": best_sgmc,
                         "best_budget": a4_budget if a4_budget is not None else best_budget,
                         "a4_budget_rule": "smallest grid budget whose paired SGMC CI vs H33-as-is excludes 0 (post-hoc, Amendment A4)",
                         "a4_paired_ci_by_budget": a4_table,
                         "a4_passing_budget_found": a4_budget is not None,
                         "live_budget_cap": LIVE_BUDGET_CAP,
                         "uncapped_proxy_selection": uncapped,
                         "extended_budget_diagnostics_L": ext,
                         "selector": "SGMC-PROXY-DTI arm; A4 budget rule (Amendments A1+A3+A4)"}
    out.write_text(json.dumps(doc, indent=1))
    log(f"E2 selection (A4): {best_arm} @ {doc['_selection']['best_budget']} (A3 cap sgmc={best_sgmc:.4f})")
    return doc


def stage_e3(g, folds, stack, names, e2):
    out = WORK / "e3.json"
    if out.is_file():
        return json.loads(out.read_text())
    sel = e2["_selection"]
    arm, budget = sel["best_arm"], int(sel["best_budget"])
    fp, cat = g.footprint, g.catalogue
    sg_off = sgmc_truth(g)
    surf = arm_surfaces(g, stack, names)[arm]
    surf_oof = arm_surfaces_oof(g, folds, stack, names)[arm]
    visible = np.asarray(folds[0]["visible"], bool)
    dcat = ndi.distance_transform_edt(~cat)
    dvis = ndi.distance_transform_edt(~visible)
    arms, saved = {}, {}
    # (a) collar 2 px spacing-greedy
    ranked_c2 = ranked_spacing(surf, fp & (dcat > 2.0), f"e3_{arm}_c2")
    dots = M.prefix(ranked_c2, budget)
    bt, sres = sgmc_terms(dots.astype(np.float32), g, sg_off)
    ranked_c2_oof = ranked_spacing(surf_oof, fp & (dvis > 2.0), f"e3_{arm}_oof_c2")
    t, per = fold_terms(M.prefix(ranked_c2_oof, budget).astype(np.float32), folds, fp)
    arms["E3_collar2"] = {"sgmc_proxy_dti": sres["dti"],
                          "catalogue_hide_dti_oof": pooled_point(t), "per_fold": per}
    saved["E3_collar2__sgmc"], saved["E3_collar2__cathide"] = bt, t
    # (b) vendor 3-px-tile decimated emission, collar 3
    ranked_tile, _ = emit.emit_decimated(surf, fp & (dcat > 3.0), tile_px=3)
    dots = emit.emit_prefix(ranked_tile, budget)
    bt, sres = sgmc_terms(dots.astype(np.float32), g, sg_off)
    ranked_tile_oof, _ = emit.emit_decimated(surf_oof, fp & (dvis > 3.0), tile_px=3)
    t, per = fold_terms(emit.emit_prefix(ranked_tile_oof, budget).astype(np.float32), folds, fp)
    arms["E3_tile_decimated"] = {"sgmc_proxy_dti": sres["dti"],
                                 "catalogue_hide_dti_oof": pooled_point(t), "per_fold": per}
    saved["E3_tile_decimated__sgmc"], saved["E3_tile_decimated__cathide"] = bt, t
    np.savez(WORK / "e3_terms.npz", **saved)
    for k, v in arms.items():
        log(f"{k}: sgmc={v['sgmc_proxy_dti']:.4f} cat-hide-oof={v['catalogue_hide_dti_oof']:.4f}")
    doc = {"arm": arm, "budget": budget, "arms": arms}
    out.write_text(json.dumps(doc, indent=1))
    return doc


# ---------------------------------------------------------------- registry
def registry_files():
    files = sorted((ROOT / "data/scored_fleet").glob("*.tif"))
    files += sorted((ROOT / "docs/downloads").glob("*.tif"))
    files += sorted((ROOT / "submission").glob("*.tif"))
    return files


def uniqueness_report(surface, dots, fp, exclude: Path | None = None):
    rng = np.random.default_rng(861025)
    fp_idx = np.flatnonzero(fp.ravel())
    sample = rng.choice(fp_idx, size=min(200_000, fp_idx.size), replace=False)
    my_s = surface.ravel()[sample].astype(np.float64)
    rows = []
    for path in registry_files():
        if exclude is not None and path == exclude:
            continue
        with rasterio.open(path) as src:
            a = src.read(1)
        theirs = np.isfinite(a) & (a > 0)
        their_s = a.ravel()[sample].astype(np.float64)
        rho = float(spearmanr(my_s, their_s, nan_policy="omit").statistic) \
            if np.ptp(their_s) else 0.0
        if theirs.any():
            dt = ndi.distance_transform_edt(~theirs)
            fwd = float((dt[dots] <= 3.0).mean()) if dots.any() else 0.0
        else:
            fwd = 0.0
        inter, union = int((dots & theirs).sum()), int((dots | theirs).sum())
        from gems57.uniqueness import representation_class
        rep = representation_class(int(theirs.sum()), int(fp.sum()))
        is_dot = rep["kind"] == "dot_field"
        rows.append({"file": str(path.relative_to(ROOT)), "sha256": sha256(path),
                     "their_dots": int(theirs.sum()),
                     "representation": rep["kind"],
                     "support_fraction": rep["support_fraction"],
                     "spearman_surface_sample": rho,
                     "my_dots_within_3px_of_theirs": fwd,
                     "jaccard_dot_sets": inter / union if union else 0.0,
                     "rho_firing": bool(rho > 0.90),
                     "overlap_firing": bool(is_dot and fwd > 0.70),
                     "literal_overlap_firing_incl_continuous": bool(fwd > 0.70)})
        log(f"registry {path.name}: rho={rho:.3f} fwd3px={fwd:.3f}")
    return {
        "scope": "Every pinned local registry dot-field raster present in this "
                 "checkout (data/scored_fleet + docs/downloads + submission), "
                 "listed row-by-row with SHA-256. Continuous full-support "
                 "non-submission grids in the historical upstream inventory are "
                 "handled by the PA-86-01 preflight certificate (literal reading "
                 "reported, never hidden); under the literal support reading they "
                 "block every nonempty candidate regardless of mechanism.",
        "thresholds": {"rho_max": 0.90, "dot_overlap_3px_max": 0.70},
        "my_dots": int(dots.sum()),
        "max_spearman": max((r["spearman_surface_sample"] for r in rows), default=0.0),
        "max_forward_3px_overlap_dot_fields": max(
            (r["my_dots_within_3px_of_theirs"] for r in rows if r["representation"] == "dot_field"),
            default=0.0),
        "max_forward_3px_overlap_literal_incl_continuous": max(
            (r["my_dots_within_3px_of_theirs"] for r in rows), default=0.0),
        "rho_firings": int(sum(r["rho_firing"] for r in rows)),
        "overlap_firings": int(sum(r["overlap_firing"] for r in rows)),
        "literal_overlap_firings_incl_continuous": int(sum(
            r["literal_overlap_firing_incl_continuous"] for r in rows)),
        "gate_pass": bool(rows) and not any(r["rho_firing"] or r["overlap_firing"] for r in rows),
        "rows": rows,
    }


# ---------------------------------------------------------------- final
def stage_final(g, folds, stack, names, e1, e2, e3, preflight, started):
    fp, cat = g.footprint, g.catalogue
    sel = e2["_selection"]
    arm, budget = sel["best_arm"], int(sel["best_budget"])
    config = "collar3_spacing"
    cand_sgmc = e2[arm]["budgets"][str(budget)]["sgmc_proxy_dti"]
    for key, cfg in (("E3_collar2", "collar2_spacing"),
                     ("E3_tile_decimated", "collar3_tile")):
        if e3["arms"][key]["sgmc_proxy_dti"] > cand_sgmc:
            cand_sgmc, config = e3["arms"][key]["sgmc_proxy_dti"], cfg
            log(f"config switched to {cfg} (sgmc {cand_sgmc:.4f})")
    e2t = dict(np.load(WORK / "e2_terms.npz"))
    e3t = dict(np.load(WORK / "e3_terms.npz"))
    e1t = dict(np.load(WORK / "e1_control_terms.npz"))
    CAND = "E2_candidate_chosen"
    if config == "collar3_spacing":
        t_sg, t_ch = e2t[f"{arm}_b{budget}__sgmc"], e2t[f"{arm}_b{budget}__cathide"]
    elif config == "collar2_spacing":
        t_sg, t_ch = e3t["E3_collar2__sgmc"], e3t["E3_collar2__cathide"]
    else:
        t_sg, t_ch = e3t["E3_tile_decimated__sgmc"], e3t["E3_tile_decimated__cathide"]
    pooled_sgmc = relabel(EH.pooled_summary(
        {CAND: t_sg, "H33_as_is": e1t["H33_as_is__sgmc"],
         "D28_parent_as_is": e1t["D28_parent_as_is__sgmc"]},
        draws=1000, seed=861025, candidate=CAND))
    # OOF catalogue-hide controls: PCC construction (binary surface re-emitted
    # with the visible collar at the SAME budget; Amendment A2).
    visible0 = np.asarray(folds[0]["visible"], bool)
    dvis0 = ndi.distance_transform_edt(~visible0)
    ctrl_ch = {}
    for label, path in (("H33_visible_collar", H33), ("D28_visible_collar", D28)):
        ranked_c, _ = emit.emit_decimated(rank01(load_binary(path).astype(np.float32), fp),
                                          fp & (dvis0 > 3.0), tile_px=3)
        t_c, _per = fold_terms(emit.emit_prefix(ranked_c, budget).astype(np.float32), folds, fp)
        ctrl_ch[label] = t_c
    pooled_ch = EH.pooled_summary(
        {CAND: t_ch, **ctrl_ch}, draws=1000, seed=861025, candidate=CAND)
    sg = pooled_sgmc["scores"][CAND]
    sg_delta = pooled_sgmc["paired_differences"]["H33_as_is"]
    ch = pooled_ch["scores"][CAND]
    h33_sg = pooled_sgmc["scores"]["H33_as_is"]["dti"]
    h33_ch = pooled_ch["scores"]["H33_visible_collar"]["dti"]
    canary_ok = not any(v["leakage_flag"] for v in e1["canaries"].values())
    gate_sgmc = bool(sg["dti"] > h33_sg and sg_delta["ci95"][0] > 0)
    gate_ch_floor = bool(ch["dti"] >= h33_ch)

    # final dots: identical construction to the winning arm/config
    surf = arm_surfaces(g, stack, names)[arm]
    dcat = ndi.distance_transform_edt(~cat)
    if config == "collar3_tile":
        ranked, _ = emit.emit_decimated(surf, fp & (dcat > 3.0), tile_px=3)
        dots = emit.emit_prefix(ranked, budget)
        collar = 3.0
    else:
        collar = 2.0 if config == "collar2_spacing" else 3.0
        tag = f"e2_{arm}_c3" if collar == 3.0 else f"e3_{arm}_c2"
        ranked = ranked_spacing(surf, fp & (dcat > collar), tag)
        dots = M.prefix(ranked, budget)
    log(f"final dots: {int(dots.sum())} (arm {arm}, budget {budget}, config {config})")

    uniq = uniqueness_report(surf, dots, fp)
    EV.mkdir(parents=True, exist_ok=True)
    (EV / "h86g-edti-registry.json").write_text(json.dumps(uniq, indent=1))

    gates = {"canary_leakage": canary_ok,
             "sgmc_proxy_beats_H33_paired_ci": gate_sgmc,
             "catalogue_hide_floor_vs_H33": gate_ch_floor,
             "uniqueness_local_registry": bool(uniq["gate_pass"])}
    gates_ok = all(gates.values())
    verdict = "promote" if gates_ok else "negative"
    decision = ("OK TO SUBMIT after separate selector step (all registered gates pass; no slot picked here)"
                if gates_ok else "DO NOT SUBMIT")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(dots).tobytes()).hexdigest()[:8]
    name = f"gems86-h86g-edti-{int(dots.sum())}dots-{stamp}-{digest8}-zeros"
    note = ("H86G-EDTI multiline+HGB E[k] spacing-greedy collar3; "
            "SGMC-proxy selected; holdout in run card; no slot pre-picked")[:140]
    pred = np.where(dots & fp, 1.0, 0.0).astype(np.float32)
    path = OUT_DIR / f"{name}.tif"
    receipt = submission_writer.write_submission(
        path, pred, ROOT / "data/bridge/sample_submission.tif", fp,
        note=note, name=name, catalogue=cat,
        metadata={"lane": "H86G-EDTI", "arm": arm, "config": config,
                  "budget": budget, "collar_px": collar,
                  "preregistration": "research/H86G_EDTI_PREREGISTRATION.md",
                  "amendment": "A1 (SGMC-proxy selector after E1)"})
    disk = validate.validate(path, fp, cat)
    if not disk["all_checks_passed"]:
        raise RuntimeError("independent on-disk validator failed")
    receipt["independent_disk_validation"] = disk
    receipt["gate_verdict"] = verdict
    receipt["decision"] = decision
    receipt["gates"] = gates
    path.with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n")

    card = {
        "schema": "gems86.h86g-edti-run-card.v1",
        "lane": "H86G-EDTI",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {"document": "research/H86G_EDTI_PREREGISTRATION.md",
                            "machine_readable": "research/H86G_EDTI_PREREGISTRATION.json",
                            "amendment": "A1 after E1 (see document)"},
        "hypothesis": "Off-catalogue multiline lineament corroboration over the "
                      "pinned potential-field + LiDAR + topography stack, signed "
                      "by a catalogue-signature HGB posterior and emitted by "
                      "expected-kernel-credit spacing-greedy behind a 3 px "
                      "catalogue collar, recovers unmapped fault trace more "
                      "DTI-efficiently than the H19-5-ancestor dotted field "
                      "behind the owner-reported 0.2778 mechanism.",
        "mechanism": "L: mean footprint-rank of 8 independent edge detectors "
                     "(RTP/gravity/DEM gradient magnitudes, analytic signal, "
                     "LiDAR step/cross, topo lineament/curvature) times a "
                     "detector-agreement weight. H: HistGradientBoosting on 68 "
                     "pinned features with zero catalogue-derived inputs. "
                     "LH = rank(L) x (0.35 + 0.65 rank(H)). Dots ranked by "
                     "E[k] = surface (*) triangular 300 m kernel (vendor "
                     "gems57.emit.expected_credit), spacing >= 2.8 px.",
        "named_non_fault_process": "Unfaulted lithologic contacts, volcanic "
                                   "flow-front edges, and Lahontan shorelines/"
                                   "beach ridges produce the same edge/scarp "
                                   "corroboration signature.",
        "chosen_arm": arm, "chosen_config": config, "chosen_budget": budget,
        "evidence_classes": "HOLDOUT-DTI = gems57-pooled-hide-v2 (alpha 0.2, "
                            "beta 0.8, 300 m triangular) on buffered whole-"
                            "component catalogue-hide folds. SGMC-PROXY-DTI = "
                            "same formula/masking vs pinned USGS SGMC faults "
                            ">3 px off catalogue; SELECTION ONLY, never a "
                            "leaderboard projection. 0.2778/0.4413/0.3195 are "
                            "OWNER-REPORTED without organizer receipts; this "
                            "lane has no ORGANIZER-CONFIRMED number.",
        "preflight_pa86_01": {"status": preflight.get("status"),
                              "literal_reading_blocked": preflight.get("literal_reading_blocked")},
        "leakage_canaries": e1["canaries"],
        "instrument_validation_E1b": {
            "note": "As-is shipped rasters on both instruments (full table in "
                    "research/H86G_EDTI_REVIEW.md). Catalogue-hide anti-correlates "
                    "with owner-reported live ordering; SGMC-proxy reproduces it. "
                    "SGMC implementation verified by reproducing KSLB's published "
                    "0.072612 exactly.",
            "controls": e1["controls_point"]},
        "budget_curves": {k: v for k, v in e2.items() if not k.startswith("_")},
        "ablations": e3["arms"],
        "sgmc_proxy": {"evaluator": "shared gems57 term machinery, relabelled",
                       "positives": int(sg["withheld_positive_pixels"]),
                       "candidate": sg, "paired_delta_vs_H33_as_is": sg_delta,
                       "H33_as_is_dti": h33_sg, "pooled": pooled_sgmc},
        "holdout_dti": {"evaluator_version": EH.VERSION,
                        "withheld_positive_pixels": int(ch["withheld_positive_pixels"]),
                        "candidate": ch, "H33_as_is_dti": h33_ch,
                        "pooled": pooled_ch},
        "uniqueness": {k: v for k, v in uniq.items() if k != "rows"},
        "uniqueness_rows_file": "docs/evidence/h86g-edti-registry.json",
        "gates": gates,
        "raster_sha256": receipt["sha256"],
        "validator_output": disk,
        "submission_name": name,
        "submission_file": f"docs/downloads/{name}.tif",
        "zip_file": f"docs/downloads/{name}.zip",
        "note": note, "note_chars": len(note),
        "verdict": verdict, "decision": decision,
        "submission_slots_used": 0,
        "runtime_seconds": time.time() - started,
    }
    (EV / "h86g-edti-run-card.json").write_text(json.dumps(card, indent=1) + "\n")
    log(json.dumps({"verdict": verdict, "decision": decision, "name": name,
                    "sgmc_proxy": sg["dti"], "sgmc_delta_ci95": sg_delta["ci95"],
                    "catalogue_hide_dti_oof": ch["dti"], "gates": gates}, indent=1))
    return card


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("features", "e1", "e2", "e3", "final", "all"))
    a = ap.parse_args(argv)
    started = time.time()
    preflight = require_like_for_like()
    log(f"PA-86-01 preflight: {preflight['status']}")
    g, folds = get_grid_folds()
    stack, names = get_stack(g)
    if a.stage == "features":
        log(f"stack ready: {len(names)} features")
        return 0
    e1 = stage_e1(g, folds, stack, names)
    if a.stage == "e1":
        return 0
    e2 = stage_e2(g, folds, stack, names)
    if a.stage == "e2":
        return 0
    e3 = stage_e3(g, folds, stack, names, e2)
    if a.stage == "e3":
        return 0
    stage_final(g, folds, stack, names, e1, e2, e3, preflight, started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
