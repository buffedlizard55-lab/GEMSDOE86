#!/usr/bin/env python3
"""Run the preregistered H86J-MPC lane (research/H86J_MPC_PREREGISTRATION.md).

Reuse, don't rebuild: fold construction, SGMC-proxy machinery, fold scoring,
rank01, registry scan and binary loaders are imported from the H86G-EDTI
runner; emission ranking is ``gems57.emit.expected_credit`` +
``gems86_edti.model.spacing_greedy_ranking``; serialization is the vendor
fail-closed ``submission_writer``; validation is vendor ``validate``.
The only new physics is ``gems86_mpc.features.monogenic_pc``.

Stages: features -> e1 (canaries+controls+H33 re-forensics) -> e2 (3 arms;
surface registry check BEFORE any placement) -> e3 (amplitude/line falsifiers)
-> final (gates, TIFF, run card).  Budget 44,090 and collar 3 px are frozen in
the preregistration; budget curves are reported points only.
No weekly slot is picked here.
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
from scipy.spatial import cKDTree
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]

from gems57 import emit, evaluate_holdout as EH, submission_writer, validate  # noqa: E402
from gems86_edti import features as EF, model as M  # noqa: E402
from gems86_mpc import features as MF  # noqa: E402
from scripts import run_h86g_edti as G  # noqa: E402
from scripts.protocol_preflight import require_like_for_like  # noqa: E402

WORK = ROOT / "data/work/h86j"
CACHE = ROOT / ".cache/work_h86j"
EV = ROOT / "docs/evidence"
OUT_DIR = ROOT / "docs/downloads"
FEATURE_TIF = ROOT / "data/bridge/training_features.tif"
BUDGET = 44_090
CURVE = (37_654, 44_090, 55_000)
FIELDS = {"mag": (2, MF.WAVELENGTHS_FINE), "grav": (13, MF.WAVELENGTHS_COARSE),
          "dem": (12, MF.WAVELENGTHS_FINE)}
EDTI_TIF = OUT_DIR / "gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.tif"
ARMS = ("MPC-MAG", "MPC-DUAL", "MPC-TRI")
NOTE = ("H86J-MPC monogenic phase-congruency step (RTP+grav+DEM) E[k] spacing collar3 "
        "44090d; SGMC-proxy selected; no slot pre-picked")[:140]


def log(*a):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}][h86j]", *a, flush=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as s:
        for c in iter(lambda: s.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# ---------------------------------------------------------------- features
def get_products(g):
    """MPC products per field + matched gradmag amplitude controls (cached)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    mpc, grad = {}, {}
    with rasterio.open(FEATURE_TIF) as ds:
        raw = {name: ds.read(band) for name, (band, _) in FIELDS.items()}
    for name, (_, wavelengths) in FIELDS.items():
        tag = CACHE / f"mpc_{name}.npz"
        if tag.is_file():
            mpc[name] = {k: v for k, v in np.load(tag).items()}
        else:
            log(f"monogenic PC: {name} (wavelengths {wavelengths})")
            mpc[name] = MF.monogenic_pc(raw[name], g.footprint, wavelengths)
            np.savez(tag, **mpc[name])
        gpath = CACHE / f"gradmag_{name}_s1p5.npy"
        if gpath.is_file():
            grad[name] = np.load(gpath)
        else:
            # Identical construction to EDTI stack gradmag_{rtp,grav,dem}_s1p5.
            grad[name] = EF._gradmag(EF._clean(raw[name], g.footprint), 1.5)
            grad[name][~g.footprint] = 0.0
            np.save(gpath, grad[name])
    del raw
    return mpc, grad


def surfaces(mpc, grad, fp):
    r = {f: G.rank01(mpc[f]["pc_step"], fp) for f in FIELDS}
    rl = {f: G.rank01(mpc[f]["pc_line"], fp) for f in FIELDS}
    rg = {f: G.rank01(grad[f], fp) for f in FIELDS}
    return {
        "MPC-MAG": r["mag"].astype(np.float32),
        "MPC-DUAL": MF.corroborate([r["mag"], r["grav"]], fp),
        "MPC-TRI": MF.corroborate([r["mag"], r["grav"], r["dem"]], fp),
        "AMP-GRADMAG": MF.corroborate([rg["mag"], rg["grav"], rg["dem"]], fp),
        "MPC-LINE": MF.corroborate([rl["mag"], rl["grav"], rl["dem"]], fp),
    }


def ranked(surf, allowed, tag):
    p = WORK / f"ranked_{tag}.npy"
    if p.is_file():
        return np.load(p)
    log(f"spacing-greedy ranking ({tag})")
    r = M.spacing_greedy_ranking(emit.expected_credit(surf), allowed,
                                 min_spacing_px=2.8)
    WORK.mkdir(parents=True, exist_ok=True)
    np.save(p, r)
    return r


# ---------------------------------------------------------------- E1
def h33_forensics(g):
    h33 = G.load_binary(G.H33)
    parent = G.load_binary(G.D28)
    dcat = ndi.distance_transform_edt(~g.catalogue)
    removed = parent & ~h33
    pts = np.column_stack(np.nonzero(h33)).astype(float)
    nn, _ = cKDTree(pts).query(pts, k=2)
    return {
        "evidence_class": "MEASUREMENT (pinned bytes in this checkout)",
        "h33_sha256": sha256(G.H33), "parent_sha256": sha256(G.D28),
        "h33_dots": int(h33.sum()), "parent_dots": int(parent.sum()),
        "h33_is_exact_subset_of_parent": bool(not (h33 & ~parent).any()),
        "added_dots": int((h33 & ~parent).sum()),
        "removed_dots": int(removed.sum()),
        "removed_dcat_values_px": sorted({float(v) for v in np.unique(dcat[removed])}),
        "h33_nn_spacing_px_min": float(nn[:, 1].min()),
        "h33_dots_on_catalogue": int((h33 & g.catalogue).sum()),
        "h33_dots_outside_footprint": int((h33 & ~g.footprint).sum()),
        "owner_reported_scores": {"parent_d28": 0.2708, "h33": 0.2778,
                                  "evidence_class": "OWNER-REPORTED (no organizer receipt)"},
        "interpretation": "Re-measured in H86J E1: the 0.2708->0.2778 step deletes collar "
                          "dots and changes nothing else; coverage-efficient emission under "
                          "the 300 m triangular-kernel DTI, not a new geological layer.",
    }


def stage_e1(g, folds, mpc, grad):
    WORK.mkdir(parents=True, exist_ok=True)
    out, terms_path = WORK / "e1.json", WORK / "e1_control_terms.npz"
    if out.is_file() and terms_path.is_file():
        return json.loads(out.read_text())
    fp = g.footprint
    region = np.zeros(fp.shape, bool); hidden = np.zeros(fp.shape, bool); known = np.zeros(fp.shape, bool)
    for f in folds:
        region |= np.asarray(f["region"], bool); hidden |= np.asarray(f["hidden_all"], bool)
        known |= np.asarray(f["masked_known"], bool)
    active = region & fp & ~known
    truth = active & hidden
    pos = np.flatnonzero(truth.ravel()); neg_all = np.flatnonzero((active & ~truth).ravel())
    rng = np.random.default_rng(861025)
    neg = rng.choice(neg_all, size=min(300_000, neg_all.size), replace=False)
    y = np.r_[np.ones(pos.size), np.zeros(neg.size)]
    feats = {}
    for f in FIELDS:
        for prod in ("pc_step", "pc", "stepness", "pc_line", "log_amp"):
            feats[f"{f}_{prod}"] = mpc[f][prod]
        feats[f"{f}_gradmag_s1p5"] = grad[f]
    canaries = {}
    for name, arr in feats.items():
        v = np.asarray(arr).ravel()
        s = np.r_[v[pos], v[neg]].astype(np.float64)
        auc = float(roc_auc_score(y, s)) if np.ptp(s) else 0.5
        canaries[name] = {"evidence_class": "LEAKAGE-CANARY", "auc": auc,
                          "discriminative_auc": max(auc, 1 - auc), "threshold": 0.90,
                          "leakage_flag": bool(max(auc, 1 - auc) > 0.90),
                          "n_positive": int(pos.size), "n_negative_sampled": int(neg.size)}
        log(f"canary {name}: AUC={auc:.4f}")
    sg_off = G.sgmc_truth(g)
    controls, saved = {}, {}
    for label, path in (("H33_as_is", G.H33), ("D28_parent_as_is", G.D28),
                        ("EDTI_as_is", EDTI_TIF)):
        dots = G.load_binary(path)
        t, per = G.fold_terms(dots.astype(np.float32), folds, fp)
        bt, sres = G.sgmc_terms(dots.astype(np.float32), g, sg_off)
        controls[label] = {"catalogue_hide_point_as_is": G.pooled_point(t), "per_fold": per,
                           "sgmc_proxy_point": sres["dti"], "sgmc_coverage": sres["coverage"],
                           "dots_total": int(dots.sum())}
        saved[label], saved[f"{label}__sgmc"] = t, bt
        log(f"control {label}: sgmc={sres['dti']:.4f} cat-hide-as-is={G.pooled_point(t):.4f}")
    np.savez(terms_path, **saved)
    doc = {"canaries": canaries, "controls_point": controls,
           "withheld_positive_pixels": int(pos.size),
           "sgmc_proxy_positives": int(sg_off.sum()),
           "h33_forensics": h33_forensics(g)}
    out.write_text(json.dumps(doc, indent=1))
    log(f"E1 done; H33 subset={doc['h33_forensics']['h33_is_exact_subset_of_parent']}")
    return doc


# ---------------------------------------------------------------- E2 / E3
def score_arm(g, folds, surf, tag, budgets, sg_off):
    fp, cat = g.footprint, g.catalogue
    visible = np.asarray(folds[0]["visible"], bool)
    dcat = ndi.distance_transform_edt(~cat); dvis = ndi.distance_transform_edt(~visible)
    rf = ranked(surf, fp & (dcat > 3.0), f"{tag}_full_c3")
    ro = ranked(surf, fp & (dvis > 3.0), f"{tag}_oof_c3")
    doc = {"ranking_dots_available": int((rf > 0).sum()),
           "ranking_dots_available_oof": int((ro > 0).sum()), "budgets": {}}
    saved = {}
    for b in budgets:
        bt, sres = G.sgmc_terms(M.prefix(rf, b).astype(np.float32), g, sg_off)
        t, per = G.fold_terms(M.prefix(ro, b).astype(np.float32), folds, fp)
        doc["budgets"][str(b)] = {
            "evidence_class_sgmc": "SGMC-PROXY-DTI (point, selection only)",
            "sgmc_proxy_dti": sres["dti"], "sgmc_coverage": sres["coverage"],
            "evidence_class_holdout": "HOLDOUT-DTI (point, pooled terms, OOF visible construction)",
            "catalogue_hide_dti_oof": G.pooled_point(t), "per_fold": per}
        saved[f"{tag}_b{b}__sgmc"], saved[f"{tag}_b{b}__cathide"] = bt, t
        log(f"{tag} b={b}: sgmc={sres['dti']:.4f} cat-hide-oof={G.pooled_point(t):.4f}")
    return doc, saved


def surface_registry_check(surfs, fp):
    """Surface Spearman vs every local registry raster (BEFORE placement)."""
    out = EV / "h86j-mpc-registry-surface.json"
    empty = np.zeros(fp.shape, bool)
    doc = {}
    for arm in ARMS:
        doc[arm] = G.uniqueness_report(surfs[arm], empty, fp)
        log(f"surface rho {arm}: max={doc[arm]['max_spearman']:.4f}")
    EV.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"evidence_class": "REGISTRY-MEASUREMENT",
                               "scope": "surface Spearman before placement; local registry scan (EDTI function reused)",
                               "arms": doc}, indent=1))
    return doc


def stage_e2(g, folds, surfs):
    out = WORK / "e2.json"
    if out.is_file():
        return json.loads(out.read_text())
    surf_check = surface_registry_check(surfs, g.footprint)
    sg_off = G.sgmc_truth(g)
    doc, saved = {}, {}
    for arm in ARMS:
        doc[arm], s = score_arm(g, folds, surfs[arm], arm, CURVE, sg_off)
        doc[arm]["surface_max_spearman"] = surf_check[arm]["max_spearman"]
        doc[arm]["surface_rho_ok"] = bool(surf_check[arm]["max_spearman"] <= 0.90)
        saved.update(s)
    eligible = [a for a in ARMS if doc[a]["surface_rho_ok"]]
    best = max(eligible, key=lambda a: doc[a]["budgets"][str(BUDGET)]["sgmc_proxy_dti"]) if eligible else None
    doc["_selection"] = {"best_arm": best, "budget_frozen": BUDGET,
                         "selector": "SGMC-PROXY-DTI point at frozen 44090 among surface-rho-eligible arms (preregistration)",
                         "eligible_arms": eligible}
    np.savez(WORK / "e2_terms.npz", **saved)
    out.write_text(json.dumps(doc, indent=1))
    log(f"E2 selection: {best} @ {BUDGET}")
    return doc


def stage_e3(g, folds, surfs):
    out = WORK / "e3.json"
    if out.is_file():
        return json.loads(out.read_text())
    sg_off = G.sgmc_truth(g)
    doc, saved = {}, {}
    for arm in ("AMP-GRADMAG", "MPC-LINE"):
        doc[arm], s = score_arm(g, folds, surfs[arm], arm, (BUDGET,), sg_off)
        saved.update(s)
    np.savez(WORK / "e3_terms.npz", **saved)
    out.write_text(json.dumps(doc, indent=1))
    return doc


# ---------------------------------------------------------------- final
def stage_final(g, folds, surfs, e1, e2, e3, preflight, started):
    fp, cat = g.footprint, g.catalogue
    arm = e2["_selection"]["best_arm"]
    if arm is None:
        raise RuntimeError("no surface-eligible arm; verdict negative, no TIFF placement")
    e1t = dict(np.load(WORK / "e1_control_terms.npz"))
    e2t = dict(np.load(WORK / "e2_terms.npz"))
    CAND = "E2_candidate_chosen"
    pooled_sgmc = G.relabel(EH.pooled_summary(
        {CAND: e2t[f"{arm}_b{BUDGET}__sgmc"], "H33_as_is": e1t["H33_as_is__sgmc"],
         "D28_parent_as_is": e1t["D28_parent_as_is__sgmc"], "EDTI_as_is": e1t["EDTI_as_is__sgmc"]},
        draws=1000, seed=861025, candidate=CAND))
    visible0 = np.asarray(folds[0]["visible"], bool)
    dvis0 = ndi.distance_transform_edt(~visible0)
    ctrl_ch = {}
    for label, path in (("H33_visible_collar", G.H33), ("D28_visible_collar", G.D28)):
        ranked_c, _ = emit.emit_decimated(G.rank01(G.load_binary(path).astype(np.float32), fp),
                                          fp & (dvis0 > 3.0), tile_px=3)
        ctrl_ch[label], _ = G.fold_terms(emit.emit_prefix(ranked_c, BUDGET).astype(np.float32), folds, fp)
    pooled_ch = EH.pooled_summary({CAND: e2t[f"{arm}_b{BUDGET}__cathide"], **ctrl_ch},
                                  draws=1000, seed=861025, candidate=CAND)
    sg = pooled_sgmc["scores"][CAND]
    sg_delta = pooled_sgmc["paired_differences"]["H33_as_is"]
    sg_delta_edti = pooled_sgmc["paired_differences"]["EDTI_as_is"]
    ch = pooled_ch["scores"][CAND]
    h33_sg = pooled_sgmc["scores"]["H33_as_is"]["dti"]
    h33_ch = pooled_ch["scores"]["H33_visible_collar"]["dti"]
    canary_ok = not any(v["leakage_flag"] for v in e1["canaries"].values())
    falsifiers_ok = bool(
        sg["dti"] > e3["AMP-GRADMAG"]["budgets"][str(BUDGET)]["sgmc_proxy_dti"]
        and sg["dti"] > e3["MPC-LINE"]["budgets"][str(BUDGET)]["sgmc_proxy_dti"])
    gate_sgmc = bool(sg["dti"] > h33_sg and sg_delta["ci95"][0] > 0)
    gate_floor = bool(ch["dti"] >= h33_ch)

    surf = surfs[arm]
    dcat = ndi.distance_transform_edt(~cat)
    dots = M.prefix(ranked(surf, fp & (dcat > 3.0), f"{arm}_full_c3"), BUDGET)
    log(f"final dots: {int(dots.sum())} (arm {arm} @ {BUDGET})")
    np.save(WORK / "final_dots.npy", dots.astype(np.float32))
    np.save(WORK / "final_surface.npy", np.clip(surf, 0, 1).astype(np.float32))
    uniq = G.uniqueness_report(surf, dots, fp)
    EV.mkdir(parents=True, exist_ok=True)
    (EV / "h86j-mpc-registry.json").write_text(json.dumps(uniq, indent=1))

    gates = {"canary_leakage": bool(canary_ok),
             "sgmc_proxy_beats_H33_paired_ci": gate_sgmc,
             "catalogue_hide_floor_vs_H33": gate_floor,
             "falsifiers_amplitude_and_line": falsifiers_ok,
             "uniqueness_local_registry": bool(uniq["gate_pass"])}
    gates_ok = all(gates.values())
    verdict = "promote" if gates_ok else "negative"
    decision = ("OK TO SUBMIT after separate selector step (all registered gates pass; no slot picked here)"
                if gates_ok else "DO NOT SUBMIT")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(dots).tobytes()).hexdigest()[:8]
    arm_slug = arm.lower().replace("-", "")
    name = f"gems86-h86j-{arm_slug}-mpcstep-{int(dots.sum())}dots-{stamp}-{digest8}-zeros"
    pred = np.where(dots & fp, 1.0, 0.0).astype(np.float32)
    path = OUT_DIR / f"{name}.tif"
    receipt = submission_writer.write_submission(
        path, pred, ROOT / "data/bridge/sample_submission.tif", fp,
        note=NOTE, name=name, catalogue=cat,
        metadata={"lane": "H86J-MPC", "arm": arm, "budget": BUDGET, "collar_px": 3.0,
                  "preregistration": "research/H86J_MPC_PREREGISTRATION.md"})
    disk = validate.validate(path, fp, cat)
    if not disk["all_checks_passed"]:
        raise RuntimeError("independent on-disk validator failed")
    receipt["independent_disk_validation"] = disk
    receipt["gate_verdict"] = verdict
    receipt["decision"] = decision
    receipt["gates"] = gates
    path.with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n")

    card = {
        "schema": "gems86.h86j-mpc-run-card.v1",
        "lane": "H86J-MPC",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {"document": "research/H86J_MPC_PREREGISTRATION.md",
                            "machine_readable": "research/H86J_MPC_PREREGISTRATION.json",
                            "document_sha256": sha256(ROOT / "research/H86J_MPC_PREREGISTRATION.md"),
                            "json_sha256": sha256(ROOT / "research/H86J_MPC_PREREGISTRATION.json")},
        "hypothesis": "Catalogue-missing faults offset weak magnetic/gravity/DEM markers whose "
                      "cross-scale Fourier phase remains congruent while gradient amplitude "
                      "ranks them below shallow noise; a monogenic log-Gabor phase-congruency "
                      "STEP response (odd symmetry) recovers that buried trace DTI-efficiently "
                      "where amplitude multiline detectors (H19-5 lineage, EDTI-L) miss it.",
        "mechanism": "Per field (B2 rtp, B13 iso_grav, B12 det_elev): log-Gabor scales "
                     "4/8/16/32 px (grav 8/16/32/64), sigmaonf 0.55; even sum E and Riesz odd "
                     "vector sum O give PC=sqrt(E^2+|O|^2)/(sum A_s+eps), stepness=|O|/energy; "
                     "surface = EDTI-form corroboration of footprint ranks of PC_step. Dots: "
                     "E[k]=surface (*) triangular 300 m ranking, spacing >=2.8 px, collar >3 px, "
                     "frozen 44,090 dots (vendor/EDTI emission reused, no fork).",
        "named_non_fault_process": "Unfaulted lithologic step contacts and lava-flow fronts "
                                   "(true potential-field/DEM steps), and GeoDAWN flight-line "
                                   "seams / interpolation ringing (phase-congruent non-geology).",
        "non_fault_mimic": "Unfaulted lithologic step contacts, lava-flow fronts, survey seams.",
        "chosen_arm": arm, "chosen_budget": BUDGET, "chosen_config": "collar3_spacing_frozen",
        "evidence_classes": "HOLDOUT-DTI = gems57-pooled-hide-v2 (alpha 0.2, beta 0.8, 300 m "
                            "triangular) OOF visible construction. SGMC-PROXY-DTI = same formula vs "
                            "pinned USGS SGMC faults >3 px off catalogue; SELECTION ONLY, never a "
                            "leaderboard projection. 0.2778/0.3195/0.4413 are OWNER-REPORTED "
                            "without organizer receipts; this lane has no ORGANIZER-CONFIRMED number.",
        "preflight_pa86_01": {"status": preflight.get("status"),
                              "literal_reading_blocked": preflight.get("literal_reading_blocked")},
        "h33_forensics": e1["h33_forensics"],
        "leakage_canaries": e1["canaries"],
        "controls_point": e1["controls_point"],
        "budget_curves": {k: v for k, v in e2.items() if not k.startswith("_")},
        "ablations": e3,
        "sgmc_proxy": {"evaluator": "shared gems57 term machinery, relabelled",
                       "positives": int(sg["withheld_positive_pixels"]),
                       "candidate": sg, "paired_delta_vs_H33_as_is": sg_delta,
                       "paired_delta_vs_EDTI_as_is_55000_budget_caveat": sg_delta_edti,
                       "H33_as_is_dti": h33_sg, "pooled": pooled_sgmc},
        "holdout_dti": {"evaluator_version": EH.VERSION,
                        "withheld_positive_pixels": int(ch["withheld_positive_pixels"]),
                        "candidate": ch, "H33_visible_collar_dti": h33_ch, "pooled": pooled_ch},
        "uniqueness": {k: v for k, v in uniq.items() if k != "rows"},
        "uniqueness_rows_file": "docs/evidence/h86j-mpc-registry.json",
        "surface_registry_file": "docs/evidence/h86j-mpc-registry-surface.json",
        "gates": gates,
        "raster_sha256": receipt["sha256"],
        "validator_output": disk,
        "submission_name": name,
        "submission_file": f"docs/downloads/{name}.tif",
        "zip_file": f"docs/downloads/{name}.zip",
        "note": NOTE, "note_chars": len(NOTE),
        "verdict": verdict, "decision": decision,
        "submission_slots_used": 0,
        "runtime_seconds": time.time() - started,
        "submission_ready": bool(gates_ok),
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "experiments_run": 3,
        "duplicate": bool(not uniq["gate_pass"]),
        "organizer_confirmed": None,
        "holdout_dti_normalized": {
            "evidence_class": "HOLDOUT-DTI", "evaluator_version": EH.VERSION,
            "dti": ch["dti"], "ci95": ch["ci95"], "n_truth": int(ch["withheld_positive_pixels"]),
            "design": "OOF visible construction (EDTI Amendment A2 form); primary selector SGMC-PROXY-DTI in sgmc_proxy block"},
        "correlation_overlap_vs_registry": {
            "max_spearman_surface": uniq.get("max_spearman"),
            "max_forward_3px_overlap_dot_fields": uniq.get("max_forward_3px_overlap_dot_fields"),
            "gate_pass": bool(uniq["gate_pass"]),
            "rows_file": "docs/evidence/h86j-mpc-registry.json"},
    }
    (EV / "h86j-mpc-run-card.json").write_text(json.dumps(card, indent=1) + "\n")
    log(json.dumps({"verdict": verdict, "decision": decision, "name": name,
                    "sgmc_proxy": sg["dti"], "sgmc_delta_vs_H33_ci95": sg_delta["ci95"],
                    "sgmc_delta_vs_EDTI_ci95": sg_delta_edti["ci95"],
                    "catalogue_hide_dti_oof": ch["dti"], "gates": gates}, indent=1))
    return card


def main(argv=None) -> int:
    # Historical builder: the literal stop precedes all candidate work.
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("features", "e1", "e2", "e3", "final", "all"))
    a = ap.parse_args(argv)
    started = time.time()
    preflight = require_like_for_like()
    log(f"PA-86-01 preflight: {preflight['status']}")
    # Registry-repo links for registry metadata restored externally (mirrors of
    # official sources for manual review):
    # https://github.com/drivendataorg/gems-prize-reference-solution
    # https://peterkovesi.github.io/ImagePhaseCongruency.jl/dev/
    g, folds = G.get_grid_folds()
    mpc, grad = get_products(g)
    if a.stage == "features":
        log("MPC products ready")
        return 0
    surfs = surfaces(mpc, grad, g.footprint)
    e1 = stage_e1(g, folds, mpc, grad)
    if a.stage == "e1":
        return 0
    e2 = stage_e2(g, folds, surfs)
    if a.stage == "e2":
        return 0
    e3 = stage_e3(g, folds, surfs)
    if a.stage == "e3":
        return 0
    stage_final(g, folds, surfs, e1, e2, e3, preflight, started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
