#!/usr/bin/env python3
"""Run the preregistered H86J-LLP lane (research/H86J_LLP_PREREGISTRATION.md).

Stages (each caches its outputs under data/work/h86j and .cache/work_h86j):
  fleet  -- join OWNER-REPORTED scores to verified bytes; max-kernel coverage on S
  e1     -- leakage canary (protocol holdout) + LLP fit with leave-one-site-out CV
  e2     -- like-for-like protocol holdout (candidate, ablation, comparators, null)
  e3     -- final build, budget rule, uniqueness, shared writer/validator, run card

Labels: HOLDOUT-DTI (gems57-pooled-hide-v2, withheld count, 95% CI),
SGMC-PROXY-DTI (selection evidence only), OWNER-REPORTED (fleet inputs),
LLP-EMULATOR (model fit statistic or MODEL projection -- never a score).
No weekly slot is picked here.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "vendor")]

from gems57 import emit, evaluate_holdout as EH, grid, holdout  # noqa: E402
from gems86_llp import fleet as FL  # noqa: E402

WORK = ROOT / "data/work/h86j"
CACHE = ROOT / ".cache/work_h86j"
EV = ROOT / "docs/evidence"
SEED = 20
T0 = time.time()


def log(*a):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')} +{time.time()-T0:6.0f}s]", *a, flush=True)


def get_grid():
    return grid.load_grid(ROOT / "data/bridge")


# ------------------------------------------------------------------ fleet
def stage_fleet(g):
    out_json = EV / "h86j-llp-e0-fleet.json"
    npz = CACHE / "fleet_cov.npz"
    if out_json.is_file() and npz.is_file():
        return json.loads(out_json.read_text()), np.load(npz)
    CACHE.mkdir(parents=True, exist_ok=True)
    fp, cat = g.footprint, g.catalogue
    domain = fp & ~cat
    S = FL.subsample(domain)
    dcat = ndi.distance_transform_edt(~cat).astype(np.float32)
    cands = FL.scored_candidates(ROOT)
    rows, dropped, by_content = [], [], {}
    keys = []
    from scipy import sparse
    c_rows, c_cols, c_vals, p_rows, p_cols, p_vals = [], [], [], [], [], []
    for c in cands:
        if not c["files"]:
            dropped.append(dict(submission=c["submission"], site=c["site"], reason="no verified local bytes"))
            continue
        arrs, infos = [], []
        for f in c["files"]:
            a, info = FL.load_prediction(Path(f), fp, cat)
            arrs.append(a)
            infos.append(info)
        ks = {FL.content_key(a) for a in arrs}
        if len(ks) != 1:
            dropped.append(dict(submission=c["submission"], site=c["site"],
                                reason=f"ambiguous: {len(ks)} distinct in-domain contents", files=c["files"]))
            continue
        k = ks.pop()
        a, info = arrs[0], infos[0]
        if info["mass"] <= 0:
            dropped.append(dict(submission=c["submission"], site=c["site"], reason="empty in scored domain"))
            continue
        if k in by_content:
            prev = rows[by_content[k]]
            prev["aliases"].append(dict(site=c["site"], submission=c["submission"], score=c["score"]))
            continue
        cov = FL.coverage(a)
        pos = a > 0
        d = dcat[pos]
        row = dict(site=c["site"], submission=c["submission"], score=c["score"],
                   evidence_class="OWNER-REPORTED", files=[str(Path(f).relative_to(ROOT)) for f in c["files"]],
                   content_sha256=k, positive=info["positive"], mass=info["mass"], binary=info["binary"],
                   clipped_cells=info["clipped_cells"],
                   dcat_median=float(np.median(d)), dcat_le3=float((d <= 3).mean()),
                   dcat_3_8=float(((d > 3) & (d <= 8)).mean()), dcat_gt20=float((d > 20).mean()),
                   aliases=[])
        by_content[k] = len(rows)
        rows.append(row)
        cs = cov.ravel()[S]
        nz = np.flatnonzero(cs)
        c_rows.append(np.full(nz.size, len(rows) - 1, np.int32)); c_cols.append(nz.astype(np.int32))
        c_vals.append(cs[nz].astype(np.float32))
        ps = a.ravel()[S]
        nz = np.flatnonzero(ps)
        p_rows.append(np.full(nz.size, len(rows) - 1, np.int32)); p_cols.append(nz.astype(np.int32))
        p_vals.append(ps[nz].astype(np.float32))
        keys.append(k)
        log(f"fleet {len(rows):3d} {c['site']:10s} {c['score']:.4f} n={info['positive']:7d} {c['submission'][:60]}")
    # alias score consistency: identical content with different reported scores
    for r in rows:
        sc = [r["score"]] + [a["score"] for a in r["aliases"]]
        r["alias_scores"] = sc
        r["score_used"] = float(np.mean(sc))
        r["alias_score_conflict"] = bool(max(sc) - min(sc) > 1e-4)
    R_, nS = len(rows), int(S.size)
    C = sparse.csr_matrix((np.concatenate(c_vals), (np.concatenate(c_rows), np.concatenate(c_cols))), shape=(R_, nS))
    Pv = sparse.csr_matrix((np.concatenate(p_vals), (np.concatenate(p_rows), np.concatenate(p_cols))), shape=(R_, nS))
    sparse.save_npz(CACHE / "fleet_C.npz", C)
    sparse.save_npz(CACHE / "fleet_P.npz", Pv)
    np.savez(npz, S=S, keys=np.array(keys))
    doc = dict(evidence_class="FLEET-ASSEMBLY (inputs are OWNER-REPORTED scores; bytes hash-verified)",
               generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               subsample=dict(fraction=FL.SUBSAMPLE_FRACTION, seed=FL.SUBSAMPLE_SEED, n=int(S.size),
                              domain_cells=int(domain.sum())),
               n_scored_names=len(cands), n_rasters=len(rows), dropped=dropped, rasters=rows)
    out_json.write_text(json.dumps(doc, indent=1) + "\n")
    return doc, np.load(npz)


# ------------------------------------------------------------------ features
H86G_WORK = ROOT / "data/work/h86g"


def get_folds(g):
    folds, _ = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)
    return folds


def shared_features(g):
    """16 shared rank01 planes (14 pinned stack features + H86G-L + top-hat L)."""
    from gems86_llp import llp as LL
    path, npath = CACHE / "shared_f16.dat", CACHE / "shared_names.json"
    names = list(LL.STACK_FEATURES) + ["h86g_L_corroboration", "tophat_L_5x5"]
    shape = (len(names),) + g.shape
    if path.is_file() and npath.is_file():
        return np.memmap(path, np.float16, "r", shape=shape), names
    import scripts.run_h86g_edti as R
    stack, snames = R.get_stack(g)
    idx = {n: i for i, n in enumerate(snames)}
    mm = np.memmap(path, np.float16, "w+", shape=shape)
    fp = g.footprint
    for k, nm in enumerate(LL.STACK_FEATURES):
        mm[k] = LL.rank01(np.asarray(stack[idx[nm]]), fp)
    L = R.surface_L(stack, snames, fp)
    mm[len(LL.STACK_FEATURES)] = LL.rank01(L, fp)
    mm[len(LL.STACK_FEATURES) + 1] = LL.rank01(LL.tophat(L), fp)
    mm.flush()
    npath.write_text(json.dumps(names))
    return np.memmap(path, np.float16, "r", shape=shape), names


def hgb_rank(g, variant):
    """rank01 of the H86G-H HGB posterior (68 pinned features, zero catalogue-
    derived features); 'visible' = holdout labels, 'full' = full catalogue."""
    from gems86_llp import llp as LL
    tag = {"visible": "holdout_visible", "full": "full_catalogue"}[variant]
    p = np.load(H86G_WORK / f"posterior_{tag}.npy")
    return LL.rank01(p, g.footprint), p


def design(flat_idx, shared, hgbr, catf):
    from gems86_llp import llp as LL
    cols = [np.asarray(shared[k]).ravel()[flat_idx].astype(np.float32) for k in range(shared.shape[0])]
    cols.append(hgbr.ravel()[flat_idx].astype(np.float32))
    cols += [catf[nm].ravel()[flat_idx] for nm in LL.CAT_FEATURES]
    return np.stack(cols, axis=1)


# ------------------------------------------------------------------ E1
def stage_e1(g):
    from scipy import sparse
    from scipy.stats import spearmanr
    from sklearn.metrics import roc_auc_score
    from gems86_llp import llp as LL
    out = EV / "h86j-llp-e1.json"
    if out.is_file() and (WORK / "theta.json").is_file():
        return json.loads(out.read_text())
    WORK.mkdir(parents=True, exist_ok=True)
    fleet_doc, z = stage_fleet(g)
    shared, snames = shared_features(g)
    names = snames + ["hgb_catalogue_signature_posterior"] + list(LL.CAT_FEATURES)
    assert tuple(names) == LL.ALL_FEATURES, names
    fp, cat = g.footprint, g.catalogue

    # ---- leakage canary on the protocol holdout (visible-only catalogue features)
    folds = get_folds(g)
    vis = np.asarray(folds[0]["visible"], bool)
    hidden = np.asarray(folds[0]["hidden_all"], bool)
    region = np.zeros(g.shape, bool)
    for f in folds:
        region |= np.asarray(f["region"], bool)
    masked = np.asarray(folds[0]["masked_known"], bool)
    hv, _ = hgb_rank(g, "visible")
    catv = LL.catalogue_features(vis)
    pos = np.flatnonzero((hidden & region & fp).ravel())
    bg = np.flatnonzero((region & fp & ~masked & ~hidden).ravel())
    rng = np.random.default_rng(861101)
    neg = bg[rng.choice(bg.size, size=min(300_000, bg.size), replace=False)]
    Xc = design(np.r_[pos, neg], shared, hv, catv)
    y = np.r_[np.ones(pos.size), np.zeros(neg.size)]
    canary = {}
    for j, nm in enumerate(names):
        auc = float(roc_auc_score(y, Xc[:, j])) if np.ptp(Xc[:, j]) > 0 else 0.5
        canary[nm] = dict(auc=auc, discriminative_auc=max(auc, 1 - auc))
    max_feat = max(canary, key=lambda k: canary[k]["discriminative_auc"])
    canary_doc = dict(evidence_class="HOLDOUT-CANARY (single-feature AUC, visible-only catalogue features)",
                      split="buffered-whole-components-loqo-v2 seed 20 hide 0.20 buffer 3",
                      withheld_positive_pixels=int(pos.size), background_sample=int(neg.size),
                      threshold=0.90, max_feature=max_feat,
                      max_discriminative_auc=canary[max_feat]["discriminative_auc"],
                      leakage_flags=[k for k, v in canary.items() if v["discriminative_auc"] > 0.90],
                      per_feature=canary)
    log(f"canary: max {max_feat} {canary[max_feat]['discriminative_auc']:.4f}")
    del Xc, catv
    keep = [nm for nm in names if canary[nm]["discriminative_auc"] <= 0.90]

    # ---- LLP fit on live scores (full-catalogue features)
    S = z["S"]
    C = sparse.load_npz(CACHE / "fleet_C.npz").tocsc()
    Pv = sparse.load_npz(CACHE / "fleet_P.npz").tocsc()
    rows = fleet_doc["rasters"]
    scores = np.array([r["score_used"] for r in rows])
    mass = np.array([r["mass"] for r in rows])
    sites = np.array([r["site"] for r in rows])
    hf, _ = hgb_rank(g, "full")
    catf = LL.catalogue_features(cat)
    domain_cells = int((fp & ~cat).sum())
    X = design(S, shared, hf, catf)
    jkeep = [names.index(nm) for nm in keep]
    jdist = [names.index(nm) for nm in LL.DIST_ONLY if nm in keep]
    thin = np.arange(0, S.size, 5)
    def model_for(cols, sub):
        return LL.LLPModel(X[sub][:, cols], C[:, sub].tocsr(), Pv[:, sub].tocsr(), mass, scores,
                           domain_cells / sub.size, [names[j] for j in cols])
    results = {}
    for label, cols in (("full", jkeep), ("dist_only", jdist)):
        m5 = model_for(cols, thin)
        per_rho = {}
        for rho in (0.3, 1.0, 3.0, 10.0):
            w_all, res = m5.fit(rho=rho)
            pred = np.zeros(len(rows))
            for site in np.unique(sites):
                test = np.flatnonzero(sites == site)
                train = np.flatnonzero(sites != site)
                w, _ = m5.fit(rows=train, rho=rho, w0=w_all, maxiter=200)
                pred[test] = m5.predict(w, rows=test)[0]
            rs = float(spearmanr(pred, scores).statistic)
            rmse = float(np.sqrt(np.mean((pred - scores) ** 2)))
            per_rho[str(rho)] = dict(loso_spearman=rs, loso_rmse=rmse, train_converged=bool(res.success))
            log(f"LLP {label} rho={rho}: LOSO spearman={rs:.3f} rmse={rmse:.4f}")
            results.setdefault(label, {})[str(rho)] = dict(per_rho[str(rho)], loso_pred=pred.tolist())
        best_rho = max(per_rho, key=lambda k: per_rho[k]["loso_spearman"])
        results[label]["best_rho"] = float(best_rho)
    rho = results["full"]["best_rho"]
    mfull = model_for(jkeep, np.arange(S.size))
    w, res = mfull.fit(rho=rho)
    fit_pred, parts = mfull.predict(w)
    theta = dict(names=[names[j] for j in jkeep], mu=mfull.mu.tolist(), b=float(w[0]), theta=w[1:].tolist(),
                 rho=rho, implied_G_full_footprint=float(parts["G"]),
                 converged=bool(res.success), message=str(res.message))
    (WORK / "theta.json").write_text(json.dumps(theta, indent=1))
    md = model_for(jdist, np.arange(S.size))
    wd, resd = md.fit(rho=results["dist_only"]["best_rho"])
    (WORK / "theta_dist.json").write_text(json.dumps(dict(
        names=[names[j] for j in jdist], mu=md.mu.tolist(), b=float(wd[0]), theta=wd[1:].tolist(),
        rho=results["dist_only"]["best_rho"], converged=bool(resd.success)), indent=1))
    # distance profile: intensity multiplier per band relative to >64 px
    prof = {nm: float(np.exp(w[1 + theta["names"].index(nm)])) for nm in LL.CAT_FEATURES[:-1] if nm in theta["names"]}
    acc_full = results["full"][str(rho)]["loso_spearman"]
    acc_dist = results["dist_only"][str(results["dist_only"]["best_rho"])]["loso_spearman"]
    accepted = bool(acc_full >= 0.50 and acc_full > acc_dist)
    table = [dict(site=r["site"], submission=r["submission"], owner_reported=r["score_used"],
                  llp_in_sample_fit=float(fit_pred[i]),
                  llp_loso=float(results["full"][str(rho)]["loso_pred"][i]))
             for i, r in enumerate(rows)]
    doc = dict(
        evidence_class="LLP-EMULATOR fit statistics (inputs OWNER-REPORTED; outputs are model fits, never scores)",
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        n_rasters=len(rows), n_sites=int(np.unique(sites).size), canary=canary_doc,
        features_used=theta["names"], features_dropped_by_canary=[n for n in names if n not in keep],
        cv=dict(scheme="leave-one-site-out, warm-started, 1-in-5 thinned S (Amendment A3)",
                full={k: (v if k == "best_rho" else {kk: vv for kk, vv in v.items() if kk != "loso_pred"})
                      for k, v in results["full"].items()},
                dist_only={k: (v if k == "best_rho" else {kk: vv for kk, vv in v.items() if kk != "loso_pred"})
                           for k, v in results["dist_only"].items()}),
        acceptance=dict(rule="LOSO Spearman >= 0.50 and > distance-only model", full=acc_full,
                        dist_only=acc_dist, accepted=accepted),
        theta=theta, distance_band_multipliers_vs_gt64px=prof, per_raster=table)
    out.write_text(json.dumps(doc, indent=1) + "\n")
    return doc


# ------------------------------------------------------------------ surfaces / emission
def llp_lambda(theta, shared, snames, hgbr, catf, fp, block_rows=373):
    """lambda(x) on the full grid for a fitted theta (0 outside footprint)."""
    names, mu, th = theta["names"], np.array(theta["mu"]), np.array(theta["theta"])
    H, W = fp.shape
    out = np.zeros((H, W), np.float32)

    def plane(nm, sl):
        if nm in snames:
            return np.asarray(shared[snames.index(nm)][sl], np.float32)
        if nm == "hgb_catalogue_signature_posterior":
            return hgbr[sl]
        return catf[nm][sl]

    for r0 in range(0, H, block_rows):
        sl = slice(r0, min(H, r0 + block_rows))
        acc = np.full((sl.stop - sl.start, W), theta["b"], np.float32)
        for j, nm in enumerate(names):
            acc += np.float32(th[j]) * (plane(nm, sl) - np.float32(mu[j]))
        out[sl] = np.exp(np.clip(acc, -30, 5)) * fp[sl]
    return out


def ranking(surface, allowed, tag, *, smooth=True):
    from gems86_edti import model as M
    path = CACHE / f"ranked_{tag}.npy"
    if path.is_file():
        return np.load(path)
    ek = emit.expected_credit(surface) if smooth else np.asarray(surface, np.float32)
    ek = np.where(allowed, ek, 0).astype(np.float32)
    r = M.spacing_greedy_ranking(ek, allowed, min_spacing_px=2.8)
    np.save(path, r)
    return r


def dots_at(r, budget):
    return (r > 0) & (r <= int(budget))


def fold_terms(pred, folds, fp):
    terms, per = [], {}
    for f in folds:
        res, bt = EH.evaluate(np.asarray(pred, np.float32), f, fp, block_side=200)
        terms.append(bt)
        per[f["name"]] = dict(dti=res["dti"], n_truth=res["n_truth"], emitted=res["n_emitted"])
    return np.sum(terms, axis=0), per


# ------------------------------------------------------------------ E2
BUDGET_E2 = 37_654


def stage_e2(g):
    from gems86_llp import llp as LL
    import rasterio
    out = EV / "h86j-llp-e2.json"
    if out.is_file():
        return json.loads(out.read_text())
    e1 = stage_e1(g)
    theta = json.loads((WORK / "theta.json").read_text())
    theta_d = json.loads((WORK / "theta_dist.json").read_text())
    fp = g.footprint
    folds = get_folds(g)
    vis = np.asarray(folds[0]["visible"], bool)
    catv = LL.catalogue_features(vis)
    allowed = fp & (catv["_dcat"] > 2.0)
    allowed3 = fp & (catv["_dcat"] > 3.0)
    shared, snames = shared_features(g)
    hv, p_vis = hgb_rank(g, "visible")
    arms, notes = {}, {}
    lam = llp_lambda(theta, shared, snames, hv, catv, fp)
    arms["LLP"] = dots_at(ranking(lam, allowed, "e2_llp_vis_c2"), BUDGET_E2)
    lam_d = llp_lambda(theta_d, shared, snames, hv, catv, fp)
    arms["LLP-dist"] = dots_at(ranking(lam_d, allowed, "e2_llpdist_vis_c2"), BUDGET_E2)
    L = np.asarray(shared[snames.index("h86g_L_corroboration")], np.float32)
    arms["H86G-L"] = dots_at(ranking(L, allowed, "e2_L_vis_c2"), BUDGET_E2)
    arms["H86G-H"] = dots_at(ranking(p_vis, allowed, "e2_H_vis_c2"), BUDGET_E2)
    rnd = np.random.default_rng(862020).random(fp.shape).astype(np.float32)
    arms["random"] = dots_at(ranking(rnd, allowed, "e2_random_vis_c2", smooth=False), BUDGET_E2)
    # reproduction check of the H86G same-design number (collar 3, as published)
    arms["H86G-H-collar3-repro"] = dots_at(ranking(p_vis, allowed3, "e2_H_vis_c3"), BUDGET_E2)
    # H33 recipe rebuilt on visible faults: D2.8 parent minus its visible 2-px collar (natural count)
    d28p = ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
    with rasterio.open(d28p) as ds:
        d28 = np.nan_to_num(ds.read(1)) > 0
    arms["H33-recipe-visible"] = d28 & fp & (catv["_dcat"] > 2.0)
    notes["H33-recipe-visible"] = f"D2.8 parent minus visible 2-px collar; natural count {int(arms['H33-recipe-visible'].sum())} (not budget-matched)"
    terms, per = {}, {}
    for name, d in arms.items():
        t, pf = fold_terms(d.astype(np.float32), folds, fp)
        terms[name] = t
        per[name] = dict(per_fold=pf, dots=int(d.sum()))
        log(f"E2 {name}: dots={int(d.sum())} pooled={float(EH.from_terms(t.sum(axis=0))):.4f}")
    comparators = ["LLP-dist", "H86G-L", "H86G-H", "random"]
    summ = EH.pooled_summary({k: terms[k] for k in ["LLP"] + comparators}, draws=1000, seed=520810,
                             candidate="LLP")
    best = summ["best_comparable_control"]
    diff = summ["paired_differences"][best]
    se = (diff["ci95"][1] - diff["ci95"][0]) / 3.92
    EWCS_RECORD = 0.17232456905148233   # docs/evidence/h86f-ewcs-run-card.json (Amendment A4)
    rule_i = bool(diff["delta"] > 0 and diff["ci95"][0] > 0)
    rule_ii = bool(summ["scores"]["LLP"]["dti"] > EWCS_RECORD)
    promote = bool(rule_i and rule_ii)
    side = {k: dict(dti=float(EH.from_terms(terms[k].sum(axis=0))), dots=per[k]["dots"], note=notes.get(k, ""))
            for k in ("H86G-H-collar3-repro", "H33-recipe-visible")}
    doc = dict(evidence_class="HOLDOUT-DTI", evaluator_version=EH.VERSION,
               split=folds[0]["receipt"]["split_version"], seed=SEED,
               withheld_positive_pixels=int(sum(int(np.asarray(f["truth"]).sum()) for f in folds)),
               budget=BUDGET_E2, emission="E[k] spacing-greedy >= 2.8 px; allowed = footprint & d_visible > 2 px",
               construction="every arm built from visible faults only (OOF); LLP theta fit on live scores only",
               summary=summ, current_holdout_best=dict(arm=best, dti=summ["scores"][best]["dti"]),
               candidate=dict(arm="LLP", **summ["scores"]["LLP"]),
               candidate_minus_best=dict(diff, se_from_ci=se, z=float(diff["delta"] / se) if se > 0 else None),
               promote_rule=("(i) candidate - best in-run comparator > 0 with paired 95% CI lower bound > 0 AND "
                             "(ii) candidate > 0.1723 published same-split record (H86F-EWCS; Amendment A4)"),
               rule_i_beats_in_run_best=rule_i, rule_ii_beats_published_record=rule_ii,
               published_same_split_record=dict(lane="H86F-EWCS", dti=EWCS_RECORD, ci95=[0.15295644923310786, 0.18979291320276231],
                                                note="same split/evaluator/withheld count; collar 3 px and its own budget (not like-for-like)"),
               promote=promote, side_measurements=side, per_arm=per)
    out.write_text(json.dumps(doc, indent=1) + "\n")
    return doc


# ------------------------------------------------------------------ E3
BUDGET_GRID = (20_000, 25_000, 30_000, 37_654, 44_090, 55_000)
DL = ROOT / "docs/downloads"


def expected_dti(dots, lam, domain):
    """MODEL projection of DTI under lambda (never a score)."""
    from gems86_llp import fleet as FL
    c = FL.coverage(dots.astype(np.float32))
    T = float((lam * c)[domain].sum(dtype=np.float64))
    M = float(np.minimum(1.0, 3.0 * lam[dots]).sum(dtype=np.float64))
    G = float(lam[domain].sum(dtype=np.float64))
    n = float(dots.sum())
    return T / (0.2 * T + 0.2 * (n - M) + 0.8 * G), dict(T=T, M=M, G=G, n=n)


def run(cmd):
    import subprocess
    log("$ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    log((r.stdout or "")[-1500:] + (r.stderr or "")[-1500:])
    return r.returncode


def stage_e3(g):
    from gems86_llp import llp as LL
    from gems57 import submission_writer, validate as V
    import rasterio
    e1 = stage_e1(g)
    e2 = json.loads((EV / "h86j-llp-e2.json").read_text())
    theta = json.loads((WORK / "theta.json").read_text())
    fp, cat = g.footprint, g.catalogue
    domain = fp & ~cat
    catf = LL.catalogue_features(cat)
    shared, snames = shared_features(g)
    hf, _ = hgb_rank(g, "full")
    lam = llp_lambda(theta, shared, snames, hf, catf, fp)
    lam[cat] = 0.0
    allowed = fp & ~cat & (catf["_dcat"] > 2.0)
    r = ranking(lam, allowed, "e3_llp_full_c2")
    curve = {}
    for b in BUDGET_GRID:
        d = dots_at(r, b)
        val, parts = expected_dti(d, lam, domain)
        curve[str(b)] = dict(model_expected_dti=val, **parts)
        log(f"E3 budget {b}: MODEL expected DTI {val:.4f}")
    chosen = int(max(curve, key=lambda k: curve[k]["model_expected_dti"]))
    dots = dots_at(r, chosen)
    pred = dots.astype(np.float32)
    pred[~fp] = 0.0
    surf = (lam / float(lam.max())).astype(np.float32)
    surf[~fp] = 0.0
    surf_npy, dots_npy = WORK / "h86j_surface.npy", WORK / "h86j_final_dots.npy"
    np.save(surf_npy, surf)
    np.save(dots_npy, pred)
    # uniqueness: surface + final dots + PA-86-02, BEFORE the TIFF joins docs/downloads
    rs = EV / "h86j-llp-registry-surface.json"
    rd = EV / "h86j-llp-registry-final-dots.json"
    rc = EV / "h86j-llp-pa86-chance-overlap.json"
    py = str(ROOT / ".venv/bin/python")
    run([py, "scripts/check_h86e_registry.py", str(surf_npy), str(rs), "--surface"])
    run([py, "scripts/check_h86e_registry.py", str(dots_npy), str(rd)])
    run([py, "scripts/pa86_chance_overlap.py", str(rd), str(dots_npy), str(rc)])
    # SGMC proxy (selection evidence only; never a score)
    import scripts.run_h86g_edti as R
    sg_off = R.sgmc_truth(g)
    _, sg_c = R.sgmc_terms(pred, g, sg_off)
    h33p = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    with rasterio.open(h33p) as ds:
        h33 = (np.nan_to_num(ds.read(1)) > 0).astype(np.float32)
    _, sg_h = R.sgmc_terms(h33, g, sg_off)
    # LLP-EMULATOR projections for reference rasters (MODEL, never scores; Amendment A5 / gate S4)
    refs = {"GEMSDOE32 H33 (0.2778 OWNER-REPORTED)": h33p,
            "H86G-EDTI (promoted 2026-10-25)": DL / "gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.tif",
            "H86F-EWCS (holdout record 0.1723)": DL / "gems86-h86f-ewcs-elastic-wing-37654dots-20261025T020534Z-47f1ed21-zeros.tif",
            "13GEMSDOE lattice s5 (0.0904 OWNER-REPORTED)": None}
    fleet_doc = json.loads((EV / "h86j-llp-e0-fleet.json").read_text())
    for row in fleet_doc["rasters"]:
        if row["site"] == "13GEMSDOE":
            refs["13GEMSDOE lattice s5 (0.0904 OWNER-REPORTED)"] = ROOT / row["files"][0]
    emulator = {}
    for label, pth in refs.items():
        if pth is None or not Path(pth).is_file():
            emulator[label] = None
            continue
        with rasterio.open(pth) as ds:
            ref = (np.nan_to_num(ds.read(1)) > 0) & fp & ~cat
        emulator[label] = expected_dti(ref, lam, domain)[0]
    emulator["H86J-LLP candidate"] = curve[str(chosen)]["model_expected_dti"]
    s4_pass = bool(emulator["H86J-LLP candidate"] > emulator["GEMSDOE32 H33 (0.2778 OWNER-REPORTED)"])
    log(f"E3 emulator projections: {emulator}")
    # write with the shared writer
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    import hashlib
    tag = hashlib.sha256(pred.tobytes()).hexdigest()[:8]
    name = f"gems86-h86j-llp-{chosen}dots-{stamp}-{tag}-zeros"
    note = (f"H86J-LLP: fault intensity fit to {e1['n_rasters']} fleet live scores; E[k] spacing-greedy "
            f"2.8px collar2; gate+holdout in run card")[:140]
    out_tif = DL / f"{name}.tif"
    receipt = submission_writer.write_submission(out_tif, pred, ROOT / "data/bridge/sample_submission.tif", fp,
                                                 note=note, name=name, catalogue=cat,
                                                 metadata=dict(lane="H86J-LLP", budget=chosen))
    vrec = V.validate(out_tif, fp, cat)
    dcat = catf["_dcat"][dots]
    from scipy.spatial import cKDTree
    yx = np.argwhere(dots)
    nn = cKDTree(yx).query(yx, k=2)[0][:, 1]
    rsj, rdj, rcj = (json.loads(p.read_text()) if p.is_file() else {} for p in (rs, rd, rc))
    def two(rep, key):
        return rep.get("two_phase", {}).get(key, {})
    card = dict(
        schema="gems86.h86j-llp-run-card.v1", lane="H86J-LLP",
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        preregistration=dict(document="research/H86J_LLP_PREREGISTRATION.md",
                             machine_readable="research/H86J_LLP_PREREGISTRATION.json",
                             sha256=FL_sha(ROOT / "research/H86J_LLP_PREREGISTRATION.md")),
        hypothesis=("The organiser's hidden new-fault truth can be localised by a log-linear intensity over pinned "
                    "raw-data features whose expected DTI reproduces the fleet's live scores (learning from label "
                    "proportions), rather than by fitting the catalogue."),
        mechanism=(f"lambda = exp(b + theta.phi) over {len(theta['names'])} rank features (edges, LiDAR steps, "
                   "HGB catalogue-signature posterior, H86G-L corroboration, catalogue-distance bands/density); "
                   "theta fit by ridge logit least squares so E[DTI_r] matches OWNER-REPORTED live scores of "
                   f"{e1['n_rasters']} fleet rasters; dots by E[k]=lambda*kernel spacing-greedy >=2.8 px, collar >2 px."),
        named_non_fault_process=("Pleistocene Lake Lahontan wave-cut shorelines/beach ridges and alluvial-fan terrace "
                                 "risers produce linear LiDAR steps that mimic young fault scarps."),
        evidence_files=dict(fleet="docs/evidence/h86j-llp-e0-fleet.json", e1="docs/evidence/h86j-llp-e1.json",
                            e2="docs/evidence/h86j-llp-e2.json"),
        leakage_canary=dict(max_feature=e1["canary"]["max_feature"],
                            max_discriminative_auc=e1["canary"]["max_discriminative_auc"],
                            threshold=0.90, flags=e1["canary"]["leakage_flags"]),
        llp_emulator=dict(evidence_class="LLP-EMULATOR (fit statistic; not a score)", acceptance=e1["acceptance"],
                          distance_band_multipliers_vs_gt64px=e1["distance_band_multipliers_vs_gt64px"],
                          implied_truth_px_full_footprint=e1["theta"]["implied_G_full_footprint"]),
        holdout_dti=dict(evidence_class="HOLDOUT-DTI", evaluator_version=e2["evaluator_version"],
                         withheld_positive_pixels=e2["withheld_positive_pixels"], budget=e2["budget"],
                         candidate=e2["candidate"], current_holdout_best_in_run=e2["current_holdout_best"],
                         candidate_minus_best=e2["candidate_minus_best"],
                         published_same_split_record=e2["published_same_split_record"],
                         all_arms={k: dict(dti=v["dti"], ci95=v["ci95"]) for k, v in e2["summary"]["scores"].items()},
                         side_measurements=e2["side_measurements"], promote=e2["promote"],
                         promote_rule=e2["promote_rule"]),
        budget_rule=dict(evidence_class="MODEL projection under fitted lambda (never a score)", curve=curve,
                         chosen=chosen),
        llp_emulator_projections=dict(evidence_class="LLP-EMULATOR MODEL projection (never a score)",
                                      values=emulator, s4_candidate_above_h33=s4_pass,
                                      caveat="in-sample fit compresses the top: H33 fits 0.163 vs 0.2778 reported; "
                                             "a lambda-optimised candidate flatters itself, so S4 can only veto"),
        sgmc_proxy=dict(evidence_class="SGMC-PROXY-DTI (selection evidence only; never a score)",
                        candidate=sg_c["dti"], h33_as_is=sg_h["dti"]),
        uniqueness=dict(
            surface=dict(report=str(rs.relative_to(ROOT)), gate_pass=rsj.get("surface_gate_pass"),
                         worst_spearman=two(rsj, "literal_reading").get("worst_spearman_full_footprint"),
                         worst_spearman_submission=two(rsj, "literal_reading").get("worst_spearman_submission"),
                         rasters=rsj.get("registry_rasters_measured")),
            final_dots=dict(report=str(rd.relative_to(ROOT)), like_for_like_pass=rdj.get("final_dots_gate_pass"),
                            literal_pass=rdj.get("literal_gate_pass"),
                            worst_spearman=two(rdj, "literal_reading").get("worst_spearman_full_footprint"),
                            worst_forward_overlap_dot_fields=two(rdj, "like_for_like_reading").get("worst_forward_overlap_dot_fields"),
                            worst_forward_overlap_dot_field_submission=two(rdj, "like_for_like_reading").get("worst_forward_overlap_dot_field_submission"),
                            literal_worst_forward_overlap=two(rdj, "literal_reading").get("worst_forward_overlap"),
                            literal_worst_submission=two(rdj, "literal_reading").get("worst_overlap_submission"),
                            rasters=rdj.get("registry_rasters_measured")),
            chance_overlap=dict(report=str(rc.relative_to(ROOT)), gate_pass=rcj.get("gate_pass"),
                                informative_firings=rcj.get("informative_firings"))),
        raster_path=str(out_tif.relative_to(ROOT)), zip_path=str(out_tif.with_suffix(".zip").relative_to(ROOT)),
        writer_receipt=str(out_tif.with_suffix(".json").relative_to(ROOT)),
        raster_sha256=receipt["sha256"], dots=int(dots.sum()),
        dots_npy=str(dots_npy.relative_to(ROOT)), surface_npy=str(surf_npy.relative_to(ROOT)),
        geometry=dict(min_spacing_px=float(nn.min()), median_spacing_px=float(np.median(nn)),
                      min_catalogue_distance_px=float(dcat.min()), median_catalogue_distance_px=float(np.median(dcat)),
                      dots_on_catalogue=int((pred[cat] > 0).sum())),
        validator_output=dict(all_checks_passed=vrec["all_checks_passed"], checks=vrec["checks"],
                              n_nan=vrec["n_nan"], n_infinite=vrec["n_infinite"], min=vrec["min"], max=vrec["max"],
                              crs=vrec["meta"]["crs"], shape=vrec["meta"]["shape"], transform=vrec["meta"]["transform"]),
        submission_name=name, submission_note=note, note_chars=len(note),
        science=dict(canary_max_auc=e1["canary"]["max_discriminative_auc"], canary_max_feature=e1["canary"]["max_feature"],
                     model_accepted=e1["acceptance"]["accepted"], model_acceptance_rule=e1["acceptance"]["rule"],
                     model_acceptance_value=e1["acceptance"]["full"],
                     holdout_promote=e2["promote"], holdout_candidate=e2["candidate"]["dti"],
                     holdout_current_best=dict(in_run=e2["current_holdout_best"],
                                               published_record=e2["published_same_split_record"]["dti"]),
                     holdout_paired_delta=e2["candidate_minus_best"], holdout_rule=e2["promote_rule"],
                     emulator_candidate=emulator["H86J-LLP candidate"],
                     emulator_h33=emulator["GEMSDOE32 H33 (0.2778 OWNER-REPORTED)"], emulator_s4_pass=s4_pass),
        verdict="promote" if (e1["acceptance"]["accepted"] and e2["promote"]) else "negative",
        safe_to_submit_decided_by="scripts/submission_gate.py (docs/evidence/submission-gate.json)",
        submission_slots_used=0)
    cp = EV / "h86j-llp-run-card.json"
    cp.write_text(json.dumps(card, indent=1) + "\n")
    run([py, "scripts/submission_gate.py", str(cp)])
    return card


def FL_sha(p):
    from gems86_llp import fleet as FL
    return FL.sha256(p)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stages", nargs="+", choices=("fleet", "e1", "e2", "e3"))
    a = ap.parse_args(argv)
    g = get_grid()
    for st in a.stages:
        if st == "fleet":
            doc, _ = stage_fleet(g)
            log(f"fleet: {doc['n_rasters']} rasters, {len(doc['dropped'])} dropped")
        elif st == "e1":
            doc = stage_e1(g)
            log(f"e1: accepted={doc['acceptance']} canary_max={doc['canary']['max_discriminative_auc']:.4f}")
        elif st == "e2":
            doc = stage_e2(g)
            log(f"e2: best={doc['current_holdout_best']} cand={doc['candidate']['dti']:.4f} promote={doc['promote']}")
        elif st == "e3":
            card = stage_e3(g)
            log(f"e3: {card['submission_name']} verdict={card['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
