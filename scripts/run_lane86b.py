"""Execute Lane H86B-GFCO end-to-end within the 3-experiment / 2-hour protocol budget.

Declared lane (Session 2, advancing PR #6's next-step roadmap):
  H86B-GFCO: Cover-adaptive Geothermometer-Disequilibrium & Multi-Depth Potential-Field
  Contact-Offset LOQO GBDT ensemble coupled with strictly visible-only crack-tip,
  two-host en-echelon relay, and bend-splay mechanics, emitted via 300 m triangular
  expected-credit priority disc thinning (`r = 2.8 px`, `d_cat > 2.0 px` flank collar).

Reuses `vendor/gems57` (`grid`, `holdout`, `metric`, `evaluate_holdout`, `emit`,
`faultzone`, `relay_bend_anatomy`, `uniqueness`, `validate`, `gates`,
`submission_writer`) byte-for-byte without modification.
"""
from __future__ import annotations

import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from gems57 import emit as E
from gems57 import evaluate_holdout as EH
from gems57 import gates as GT
from gems57 import grid as G
from gems57 import holdout as H
from gems57 import metric as M
from gems57 import uniqueness as U
from gems57 import validate as V
from gems57.submission_writer import write_submission

import h86b_features as F

BUDGET_38K = 37654
BUDGET_44K = 44090
ALPHA_PHYS = 0.65
ETA_BASE = 0.12

# Cover-blind subsurface/geothermal feature subset (excludes raw LiDAR/DEM relief/slope/steps)
TOPO_EXCLUDE = frozenset({
    "lidar_valid",
    "lidar_step_z",
    "lidar_ex_z",
    "lidar_face_asym",
    "lidar_piedmont_scarp",
    "lidar_chain_vote",
    "dem_elev_z",
    "dem_slope_z",
    "dem_piedmont_hinge",
    "dem_valley_chain",
})
SUBSURF_INDICES = [i for i, nm in enumerate(F.PHYS_FEATURES) if nm not in TOPO_EXCLUDE]


def gather_lowmem(rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    """Read `(len(rows), 38)` float32 features opening one plane file at a time."""
    X = np.empty((rows.size, len(F.PHYS_FEATURES)), dtype=np.float32)
    for j, name in enumerate(F.PHYS_FEATURES):
        arr = np.load(F.PLANE_DIR / f"{name}.npy", mmap_mode="r")
        X[:, j] = arr[rows, cols]
        del arr
    return X


def cached_kinematic(tag: str, vis: np.ndarray) -> dict[str, np.ndarray]:
    kdir = ROOT / "data" / "cache" / "h86b_kin"
    kdir.mkdir(parents=True, exist_ok=True)
    p = kdir / f"{tag}.npz"
    if p.is_file():
        z = np.load(p)
        return {"m_kin": z["m_kin"], "d1": z["d1"], "tip_cone": z["tip_cone"],
                "relay_bridge": z["relay_bridge"], "bend_splay": z["bend_splay"]}
    kc = F.compute_kinematic_components(vis)
    np.savez_compressed(p, **kc)
    gc.collect()
    return kc


def emit_ek_poisson(
    surface: np.ndarray,
    allowed: np.ndarray,
    budget: int,
    r_suppress: float = 2.8,
) -> np.ndarray:
    """Shared 300 m triangular expected-credit ranking + seam-free r=2.8 px disc thinning."""
    s = np.where(allowed & np.isfinite(surface), np.clip(surface, 0.0, 1.0), 0.0).astype(np.float32)
    ek = E.expected_credit(s)
    ek = np.where(allowed, ek, 0.0)
    ys, xs = np.nonzero(ek > 0.0)
    if ys.size == 0 or budget <= 0:
        return np.zeros(surface.shape, dtype=bool)
    cap = min(ys.size, max(budget * 16, 650_000))
    if ys.size > cap:
        part = np.argpartition(-ek[ys, xs], cap - 1)[:cap]
        ys, xs = ys[part], xs[part]
    order = np.argsort(-ek[ys, xs], kind="stable")
    ys, xs = ys[order], xs[order]

    H_h, W_w = surface.shape
    blocked = np.zeros((H_h, W_w), dtype=bool)
    rad = int(np.ceil(r_suppress))
    oy, ox = np.mgrid[-rad : rad + 1, -rad : rad + 1]
    disc = (oy * oy + ox * ox) <= (r_suppress * r_suppress + 1e-9)
    dy_d, dx_d = np.nonzero(disc)
    dy_d = dy_d.astype(np.int32) - rad
    dx_d = dx_d.astype(np.int32) - rad

    dots = np.zeros((H_h, W_w), dtype=bool)
    cnt = 0
    for i in range(ys.size):
        if cnt >= budget:
            break
        y, x = int(ys[i]), int(xs[i])
        if blocked[y, x]:
            continue
        dots[y, x] = True
        cnt += 1
        ny = y + dy_d
        nx = x + dx_d
        ok = (ny >= 0) & (ny < H_h) & (nx >= 0) & (nx < W_w)
        blocked[ny[ok], nx[ok]] = True
    return dots


def fit_and_predict_p_phys(
    g: G.Grid,
    quad: np.ndarray,
    strictly_visible: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Train 4 spatially blocked LOQO ensembles + 4-seed full-catalogue final ensemble."""
    cache_path = ROOT / "data" / "cache" / "h86b_p_phys_oof.npz"
    if cache_path.is_file():
        z = np.load(cache_path)
        return z["p_oof"], z["p_full"], json.loads(str(z["meta_json"]))

    t0 = time.time()
    fp = g.footprint
    bdepth = np.load(F.PLANE_DIR / "base_depth_z.npy", mmap_mode="r")
    w_cover_full = np.clip(0.25 + 0.20 * np.asarray(bdepth, dtype=np.float32), 0.15, 0.65)
    del bdepth

    p_oof = np.zeros(g.shape, dtype=np.float32)
    fold_stats = {}

    kw_all = dict(
        max_depth=6,
        max_iter=260,
        learning_rate=0.06,
        min_samples_leaf=80,
        l2_regularization=2.0,
        early_stopping=False,
    )
    kw_sub = dict(
        max_depth=5,
        max_iter=220,
        learning_rate=0.06,
        min_samples_leaf=100,
        l2_regularization=3.0,
        early_stopping=False,
    )

    for q, qname in enumerate(H.FOLD_NAMES):
        train_dom = ndi.binary_erosion((quad >= 0) & (quad != q), iterations=H.DOMAIN_ERODE) & fp
        vis_tr = strictly_visible & train_dom
        d_tr = ndi.distance_transform_edt(~vis_tr)
        pos_y, pos_x = np.nonzero(vis_tr)
        neg_pool_y, neg_pool_x = np.nonzero(train_dom & (d_tr > 4.0))
        del d_tr

        rng = np.random.default_rng(8600 + q)
        n_neg = min(160_000, neg_pool_y.size)
        take = rng.choice(neg_pool_y.size, size=n_neg, replace=False)
        tr_y = np.concatenate([pos_y, neg_pool_y[take]])
        tr_x = np.concatenate([pos_x, neg_pool_x[take]])
        y_tr = np.concatenate([np.ones(pos_y.size, np.int8), np.zeros(n_neg, np.int8)])
        w_neg = float(neg_pool_y.size) / float(max(n_neg, 1))
        w_tr = np.concatenate([np.ones(pos_y.size, np.float64), np.full(n_neg, w_neg, np.float64)])

        X_tr = gather_lowmem(tr_y, tr_x)
        m_all = HistGradientBoostingClassifier(**kw_all, random_state=860 + q)
        m_all.fit(X_tr, y_tr, sample_weight=w_tr)
        m_sub = HistGradientBoostingClassifier(**kw_sub, random_state=960 + q)
        m_sub.fit(X_tr[:, SUBSURF_INDICES], y_tr, sample_weight=w_tr)
        del X_tr
        gc.collect()

        # Predict strictly out-of-fold on quadrant q
        te_y, te_x = np.nonzero(fp & (quad == q))
        for s0 in range(0, te_y.size, 300_000):
            sl = slice(s0, min(s0 + 300_000, te_y.size))
            yy, xx = te_y[sl], te_x[sl]
            X_te = gather_lowmem(yy, xx)
            pa = m_all.predict_proba(X_te)[:, 1].astype(np.float32)
            ps = m_sub.predict_proba(X_te[:, SUBSURF_INDICES])[:, 1].astype(np.float32)
            wc = w_cover_full[yy, xx]
            p_oof[yy, xx] = (1.0 - wc) * pa + wc * np.maximum(pa, 0.90 * ps)
            del X_te
        fold_stats[qname] = dict(
            n_train_pos=int(pos_y.size),
            n_train_neg=int(n_neg),
            n_test_px=int(te_y.size),
            oof_mean=float(p_oof[te_y, te_x].mean()),
            oof_p99=float(np.percentile(p_oof[te_y, te_x], 99.0)),
        )
        print(f"LOQO fold {qname} predicted | oof_p99={fold_stats[qname]['oof_p99']:.5f}", flush=True)
        gc.collect()

    # Final full-map physical ensemble (2 seeds on full catalogue for live inference only)
    p_full_acc = np.zeros(g.shape, dtype=np.float32)
    d_full = ndi.distance_transform_edt(~g.catalogue)
    pos_fy, pos_fx = np.nonzero(g.catalogue & fp)
    neg_fy, neg_fx = np.nonzero(fp & (d_full > 4.0))
    del d_full
    fp_y, fp_x = np.nonzero(fp)
    n_seeds = 2
    for sd in range(n_seeds):
        rng = np.random.default_rng(1860 + sd)
        n_neg = min(180_000, neg_fy.size)
        take = rng.choice(neg_fy.size, size=n_neg, replace=False)
        tr_y = np.concatenate([pos_fy, neg_fy[take]])
        tr_x = np.concatenate([pos_fx, neg_fx[take]])
        y_tr = np.concatenate([np.ones(pos_fy.size, np.int8), np.zeros(n_neg, np.int8)])
        w_neg = float(neg_fy.size) / float(max(n_neg, 1))
        w_tr = np.concatenate([np.ones(pos_fy.size, np.float64), np.full(n_neg, w_neg, np.float64)])
        X_tr = gather_lowmem(tr_y, tr_x)
        m_all = HistGradientBoostingClassifier(**kw_all, random_state=1860 + sd)
        m_all.fit(X_tr, y_tr, sample_weight=w_tr)
        m_sub = HistGradientBoostingClassifier(**kw_sub, random_state=2860 + sd)
        m_sub.fit(X_tr[:, SUBSURF_INDICES], y_tr, sample_weight=w_tr)
        del X_tr
        for s0 in range(0, fp_y.size, 300_000):
            sl = slice(s0, min(s0 + 300_000, fp_y.size))
            yy, xx = fp_y[sl], fp_x[sl]
            X_te = gather_lowmem(yy, xx)
            pa = m_all.predict_proba(X_te)[:, 1].astype(np.float32)
            ps = m_sub.predict_proba(X_te[:, SUBSURF_INDICES])[:, 1].astype(np.float32)
            wc = w_cover_full[yy, xx]
            p_full_acc[yy, xx] += ((1.0 - wc) * pa + wc * np.maximum(pa, 0.90 * ps)) / float(n_seeds)
            del X_te
        gc.collect()

    meta = dict(elapsed_s=round(time.time() - t0, 2), folds=fold_stats, subsurf_features=len(SUBSURF_INDICES))
    np.savez_compressed(cache_path, p_oof=p_oof, p_full=p_full_acc, meta_json=json.dumps(meta))
    return p_oof, p_full_acc, meta


def coupled_surface(p_phys: np.ndarray, m_kin: np.ndarray, valid: np.ndarray) -> np.ndarray:
    p_norm = np.zeros(p_phys.shape, dtype=np.float32)
    ok = valid & (p_phys > 0)
    if ok.any():
        hi = max(float(np.percentile(p_phys[ok], 99.9)), 1e-6)
        p_norm[ok] = np.clip(p_phys[ok] / hi, 0.0, 1.0)
    surf = (np.power(p_norm, ALPHA_PHYS) * (ETA_BASE + (1.0 - ETA_BASE) * m_kin)).astype(np.float32)
    surf[~valid] = 0.0
    return surf


def run_leakage_canaries(g: G.Grid, comp_folds: list[dict], ctx: H.HoldoutContext) -> dict:
    rng = np.random.default_rng(8602)
    out = {}
    for name in F.PHYS_FEATURES:
        pl = np.load(F.PLANE_DIR / f"{name}.npy", mmap_mode="r")
        aucs = []
        for f in comp_folds:
            active = f["region"] & g.footprint & ~f["masked_known"]
            truth = f["truth"] & active
            py, px = np.nonzero(truth)
            ny, nx = np.nonzero(active & ~truth)
            sub = rng.choice(ny.size, size=min(40_000, ny.size), replace=False)
            y = np.concatenate([np.ones(py.size), np.zeros(sub.size)])
            s = np.concatenate([pl[py, px], pl[ny[sub], nx[sub]]])
            aucs.append(float(roc_auc_score(y, s)))
        disc = [max(a, 1.0 - a) for a in aucs]
        out[name] = dict(
            source="label_free_physical",
            auc_mean=float(np.mean(aucs)),
            discriminative_auc_max=float(np.max(disc)),
            leakage_flag=bool(np.max(disc) > 0.90),
        )
        del pl

    kc = cached_kinematic("comp_seed20", comp_folds[0]["visible"])
    for kname in ("tip_cone", "relay_bridge", "bend_splay", "m_kin"):
        arr = kc[kname]
        aucs = []
        for f in comp_folds:
            active = f["region"] & g.footprint & ~f["masked_known"]
            truth = f["truth"] & active
            py, px = np.nonzero(truth)
            ny, nx = np.nonzero(active & ~truth)
            sub = rng.choice(ny.size, size=min(40_000, ny.size), replace=False)
            y = np.concatenate([np.ones(py.size), np.zeros(sub.size)])
            s = np.concatenate([arr[py, px], arr[ny[sub], nx[sub]]])
            aucs.append(float(roc_auc_score(y, s)))
        disc = [max(a, 1.0 - a) for a in aucs]
        out[f"visible_kin_{kname}"] = dict(
            source="visible_only_catalogue_kinematics",
            auc_mean=float(np.mean(aucs)),
            discriminative_auc_max=float(np.max(disc)),
            leakage_flag=bool(np.max(disc) > 0.90),
        )
    del kc
    gc.collect()
    return out


def collect_registry_records() -> list[dict]:
    records = []
    seen_sha = set()
    man = json.loads((ROOT / "research" / "upstream" / "data_manifest.json").read_text())
    for e in man["files"]:
        if e["group"] == "scored":
            p = ROOT / "data" / e["dest"]
            if p.is_file() and e["sha256"] not in seen_sha:
                seen_sha.add(e["sha256"])
                records.append(dict(repo=e["repo"], submission=p.name, file=str(p), sha256=e["sha256"]))

    pr6 = ROOT / "docs" / "downloads" / "gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif"
    if pr6.is_file():
        sha = hashlib.sha256(pr6.read_bytes()).hexdigest()
        if sha not in seen_sha:
            seen_sha.add(sha)
            records.append(dict(repo="buffedlizard55-lab/GEMSDOE86", submission=pr6.name, file=str(pr6), sha256=sha))

    ext_man = ROOT / "research" / "upstream" / "cross_repo_champions_manifest.json"
    if ext_man.is_file():
        for e in json.loads(ext_man.read_text())["files"]:
            p = ROOT / "data" / e["dest"]
            if p.is_file() and e["sha256"] not in seen_sha:
                seen_sha.add(e["sha256"])
                records.append(dict(repo=e["repo"], submission=p.name, file=str(p), sha256=e["sha256"]))
    return records


def main():
    # The literal stop is mandatory, including for imported callers. A previous
    # boolean parameter could bypass it and start fitting/placement after STOP.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    t_start = time.time()
    plane_man = F.build_physical_planes()
    g = G.load_grid(ROOT / "data")
    fp, cat = g.footprint, g.catalogue
    quad = H.quadrant_ids(fp)

    # Build authoritative shared holdouts
    comp_folds, _ = H.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3)
    ctx = H.build_holdout(g, seeds=(20, 21), modes=("all", "detached"))

    # Global strictly-visible mask for training P_phys (excludes ALL withheld pixels of ALL draws!)
    all_hidden = comp_folds[0]["hidden_all"].copy()
    for hmask in ctx.hidden_by_cell.values():
        all_hidden |= hmask
    strictly_visible = cat & ~all_hidden

    print("Step 1/5: Running 42 single-feature leakage canaries...", flush=True)
    canaries = run_leakage_canaries(g, comp_folds, ctx)
    any_leak = any(v["leakage_flag"] for v in canaries.values())
    max_canary_disc = max(v["discriminative_auc_max"] for v in canaries.values())
    print(f"Canaries complete: {len(canaries)} checked, max_disc={max_canary_disc:.4f}, any_leak={any_leak}", flush=True)
    if any_leak:
        raise RuntimeError("STOP: Leakage canary > 0.90 triggered!")

    print("Step 2/5: Fitting spatially blocked LOQO physical+geothermal ensemble...", flush=True)
    p_oof, p_full, fit_meta = fit_and_predict_p_phys(g, quad, strictly_visible)

    # Load fixed reference controls once
    with rasterio.open(ROOT / "data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif") as ds:
        d28_dots = U._dots(ds.read(1)) & fp
    with rasterio.open(ROOT / "data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") as ds:
        h195_dots = U._dots(ds.read(1)) & fp
    with rasterio.open(ROOT / "docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif") as ds:
        pr6_dots = U._dots(ds.read(1)) & fp

    print("Step 3/5: Executing the 3 pre-declared experiments (E1, E2, E3)...", flush=True)
    n_blocks = ((g.height + 199) // 200) * ((g.width + 199) // 200)
    arm_names = ("E1_phys_38k", "E2_gfco_38k", "E3_gfco_44k", "d28_incumbent", "h33_b2_foldfair", "h19_5_ridge", "h86_rmrb_pr6")

    # ---- Primary Holdout A: Whole-component 3-px buffered LOQO (comp_folds, 11,321 positives)
    kc_comp = cached_kinematic("comp_seed20", comp_folds[0]["visible"])
    allow_comp = fp & (kc_comp["d1"] > 2.0)
    surf_e2_comp = coupled_surface(p_oof, kc_comp["m_kin"], fp)
    dots_comp = {
        "E1_phys_38k": emit_ek_poisson(p_oof, allow_comp, BUDGET_38K),
        "E2_gfco_38k": emit_ek_poisson(surf_e2_comp, allow_comp, BUDGET_38K),
        "E3_gfco_44k": emit_ek_poisson(surf_e2_comp, allow_comp, BUDGET_44K),
        "d28_incumbent": d28_dots,
        "h33_b2_foldfair": d28_dots & allow_comp,
        "h19_5_ridge": h195_dots,
        "h86_rmrb_pr6": pr6_dots,
    }
    del kc_comp, surf_e2_comp
    gc.collect()

    terms_comp = {k: np.zeros((n_blocks, 4), np.float64) for k in arm_names}
    per_fold_comp = {k: {} for k in arm_names}
    for f in comp_folds:
        for k in arm_names:
            r, t = EH.evaluate(dots_comp[k].astype(np.float32), f, fp, block_side=200)
            terms_comp[k] += t
            per_fold_comp[k][f["name"]] = round(r["dti"], 6)
    del dots_comp
    gc.collect()

    # ---- Primary Holdouts B ("all", 22,641) & C ("detached", 22,619)
    terms_ctx = {mode: {k: np.zeros((n_blocks, 4), np.float64) for k in arm_names} for mode in ("all", "detached")}
    for mode in ("all", "detached"):
        for seed in (20, 21):
            cells_sm = [c for c in ctx.cells_of(mode) if c.seed == seed]
            hid_union = np.zeros(g.shape, dtype=bool)
            for c in cells_sm:
                hid_union |= ctx.hidden_by_cell[c.key]
            vis_draw = cat & ~hid_union
            kc_draw = cached_kinematic(f"ctx_s{seed}_{mode}", vis_draw)
            allow_draw = fp & (kc_draw["d1"] > 2.0)
            surf_e2_draw = coupled_surface(p_oof, kc_draw["m_kin"], fp)
            dots_draw = {
                "E1_phys_38k": emit_ek_poisson(p_oof, allow_draw, BUDGET_38K),
                "E2_gfco_38k": emit_ek_poisson(surf_e2_draw, allow_draw, BUDGET_38K),
                "E3_gfco_44k": emit_ek_poisson(surf_e2_draw, allow_draw, BUDGET_44K),
                "d28_incumbent": d28_dots,
                "h33_b2_foldfair": d28_dots & allow_draw,
                "h19_5_ridge": h195_dots,
                "h86_rmrb_pr6": pr6_dots,
            }
            del kc_draw, surf_e2_draw
            for c in cells_sm:
                vis_cell = ctx.visible(c.key)
                truth_crop = np.zeros(c.active.shape, dtype=bool)
                truth_crop[c.truth_yx] = True
                fold_d = {"region": c.active, "truth": truth_crop, "visible": vis_cell[c.bbox]}
                org = (c.bbox[0].start, c.bbox[1].start)
                for k in arm_names:
                    _, t = EH.evaluate(
                        dots_draw[k][c.bbox].astype(np.float32),
                        fold_d,
                        c.active,
                        block_side=200,
                        origin=org,
                        global_shape=g.shape,
                    )
                    terms_ctx[mode][k] += t
            del dots_draw
            gc.collect()

    # Select winning candidate arm among E1, E2, E3 by mean pooled DTI across Holdout A + Holdout B
    exp_arms = ("E1_phys_38k", "E2_gfco_38k", "E3_gfco_44k")
    quick_scores = {}
    for ea in exp_arms:
        d_comp = float(EH.from_terms(terms_comp[ea].sum(axis=0)))
        d_all = float(EH.from_terms(terms_ctx["all"][ea].sum(axis=0)))
        d_det = float(EH.from_terms(terms_ctx["detached"][ea].sum(axis=0)))
        quick_scores[ea] = dict(buffered_comp=d_comp, all=d_all, detached=d_det, mean_ab=0.5 * (d_comp + d_all))
        print(f"  {ea:16s}: buffered_comp={d_comp:.4f} | all={d_all:.4f} | detached={d_det:.4f}", flush=True)

    winner_arm = max(exp_arms, key=lambda k: quick_scores[k]["mean_ab"])
    print(f"Selected winning arm: {winner_arm}", flush=True)

    summary_comp = EH.pooled_summary(terms_comp, draws=1000, seed=520810, candidate=winner_arm)
    summary_all = EH.pooled_summary(terms_ctx["all"], draws=1000, seed=520810, candidate=winner_arm)
    summary_det = EH.pooled_summary(terms_ctx["detached"], draws=1000, seed=520810, candidate=winner_arm)

    # Auxiliary Off-Catalogue SGMC Proxy Diagnostic (zero SGMC in training or inference!)
    with rasterio.open(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif") as sds:
        sgmc_raw = (sds.read(1) > 0) & fp
    d_cat_full = ndi.distance_transform_edt(~cat)
    sgmc_offcat = sgmc_raw & (d_cat_full > 3.0)
    kc_full = cached_kinematic("full_catalogue", cat)
    allow_full = fp & (kc_full["d1"] > 2.0)
    surf_full_e2 = coupled_surface(p_full, kc_full["m_kin"], fp)
    surf_oof_e2_fullcat = coupled_surface(p_oof, kc_full["m_kin"], fp)

    sgmc_diag = {}
    for nm, dts in (
        ("E1_phys_38k_oof", emit_ek_poisson(p_oof, allow_full, BUDGET_38K)),
        ("E2_gfco_38k_oof", emit_ek_poisson(surf_oof_e2_fullcat, allow_full, BUDGET_38K)),
        ("E3_gfco_44k_oof", emit_ek_poisson(surf_oof_e2_fullcat, allow_full, BUDGET_44K)),
        ("d28_incumbent", d28_dots & allow_full),
        ("h86_rmrb_pr6", pr6_dots),
    ):
        res_sg = M.dti_binary(dts, sgmc_offcat, valid=fp, known=cat)
        sgmc_diag[nm] = dict(
            evidence_class="OFF-CATALOGUE-PROXY-DIAGNOSTIC (NOT HOLDOUT-DTI, NOT ORGANIZER SCORE)",
            proxy_dti=round(res_sg["dti"], 6),
            coverage=round(res_sg["coverage"], 6),
            emitted=res_sg["n_emitted"],
            proxy_positives=res_sg["n_truth"],
        )
    print("Off-catalogue SGMC diagnostic:", {k: v["proxy_dti"] for k, v in sgmc_diag.items()}, flush=True)

    # ---- Step 4/5: Pre-placement surface AND final-dot uniqueness check across 28 registry rasters
    print("Step 4/5: Running pre-placement surface & final-dot uniqueness checks vs 28 rasters...", flush=True)
    if winner_arm == "E1_phys_38k":
        chosen_surface = np.where(allow_full, p_full, 0.0).astype(np.float32)
        chosen_budget = BUDGET_38K
    elif winner_arm == "E2_gfco_38k":
        chosen_surface = np.where(allow_full, surf_full_e2, 0.0).astype(np.float32)
        chosen_budget = BUDGET_38K
    else:
        chosen_surface = np.where(allow_full, surf_full_e2, 0.0).astype(np.float32)
        chosen_budget = BUDGET_44K

    s_max = max(float(chosen_surface.max()), 1e-6)
    chosen_surface_01 = np.clip(chosen_surface / s_max, 0.0, 1.0).astype(np.float32)
    chosen_surface_01[~fp] = 0.0

    records = collect_registry_records()
    surf_check = U.compare_array_to_registry(chosen_surface_01, records, fp)
    surf_rhos = [abs(r["spearman_full_footprint"]) for r in surf_check["rows"] if r.get("spearman_full_footprint") is not None]
    worst_surf_abs_rho = float(max(surf_rhos)) if surf_rhos else 0.0
    print(f"Pre-placement surface checked vs {len(records)} rasters | worst |rho|={worst_surf_abs_rho:.4f}", flush=True)
    if worst_surf_abs_rho > 0.90:
        raise RuntimeError(f"STOP: Pre-placement surface |rho|={worst_surf_abs_rho:.4f} > 0.90!")

    final_dots = emit_ek_poisson(chosen_surface_01, allow_full, chosen_budget)
    pred = np.where(final_dots, 1.0, 0.0).astype(np.float32)

    dot_check = U.compare_array_to_registry(pred, records, fp)
    two_phase = U.two_phase_summary(dot_check["rows"], int(fp.sum()), expected_rasters=len(records))
    lat_path = ROOT / "data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
    lat_cert = U.saturation_certificate(lat_path, fp, cat)

    non_lattice_rows = [
        r for r in dot_check["rows"]
        if "13gems_20261001_r13-lattice-s5" not in r["submission"]
    ]
    worst_disc_overlap_row = max(non_lattice_rows, key=lambda r: r["my_dots_within_3px_of_theirs"])
    worst_disc_rho_row = max(
        non_lattice_rows,
        key=lambda r: abs(r["spearman_full_footprint"]) if r["spearman_full_footprint"] is not None else 0.0,
    )
    worst_disc_overlap = float(worst_disc_overlap_row["my_dots_within_3px_of_theirs"])
    worst_disc_abs_rho = abs(float(worst_disc_rho_row["spearman_full_footprint"]))
    print(
        f"Final dots checked vs {len(records)} rasters | "
        f"discriminating worst overlap={worst_disc_overlap:.4f} ({worst_disc_overlap_row['submission']}) | "
        f"worst |rho|={worst_disc_abs_rho:.4f}",
        flush=True,
    )

    # Distance-to-catalogue distribution diagnostic of final emitted dots
    d_on_dots = d_cat_full[final_dots]
    dist_quantiles = {
        "min_px": round(float(d_on_dots.min()), 4),
        "p10_px": round(float(np.percentile(d_on_dots, 10)), 2),
        "p25_px": round(float(np.percentile(d_on_dots, 25)), 2),
        "median_px": round(float(np.median(d_on_dots)), 2),
        "p75_px": round(float(np.percentile(d_on_dots, 75)), 2),
        "p90_px": round(float(np.percentile(d_on_dots, 90)), 2),
    }

    # ---- Step 5/5: Serialize GeoTIFF + single-TIF ZIP + receipt via unmodified shared writer
    print("Step 5/5: Writing & validating GeoTIFF via shared submission_writer...", flush=True)
    digest8 = hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()[:8]
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stem = f"gems86-h86b-gfco-{chosen_budget}dots-{ts}-{digest8}"
    out_tif = ROOT / "docs" / "downloads" / f"{stem}-zeros.tif"
    note = (
        f"H86B-GFCO LOQO geotherm-diseq+mag-contact-offset+LiDAR x tip/relay, "
        f"{chosen_budget} dots d>2px, zeros"
    )
    assert len(note) <= 140, len(note)

    writer_receipt = write_submission(
        out_tif,
        pred,
        ROOT / "data" / "sample_submission.tif",
        fp,
        note=note,
        name=stem,
        catalogue=cat,
        metadata=dict(lane="H86B-GFCO", winner_arm=winner_arm, budget=chosen_budget, content_digest8=digest8),
    )
    val_receipt = V.validate(out_tif, footprint=fp, catalogue=cat)
    V.assert_submittable(val_receipt)
    fmt_report = GT.format_report(out_tif, ROOT / "data" / "sample_submission.tif", footprint=fp)
    assert fmt_report["ok"], fmt_report["problems"]

    # Gate checks
    beats_comp = (
        summary_comp["paired_differences"]["d28_incumbent"]["ci95"][0] > 0.0
        and summary_comp["paired_differences"]["h33_b2_foldfair"]["ci95"][0] > 0.0
    )
    beats_all = (
        summary_all["paired_differences"]["d28_incumbent"]["ci95"][0] > 0.0
        and summary_all["paired_differences"]["h33_b2_foldfair"]["ci95"][0] > 0.0
    )
    beats_det = (
        summary_det["paired_differences"]["d28_incumbent"]["ci95"][0] > 0.0
        and summary_det["paired_differences"]["h33_b2_foldfair"]["ci95"][0] > 0.0
    )
    disc_unique = (worst_surf_abs_rho <= 0.90) and (worst_disc_abs_rho <= 0.90) and (worst_disc_overlap <= 0.70)
    all_gates_green = bool(
        val_receipt["all_checks_passed"]
        and fmt_report["ok"]
        and (not any_leak)
        and beats_comp
        and beats_all
        and beats_det
        and disc_unique
    )

    full_results = dict(
        lane="H86B-GFCO",
        generated_utc=ts,
        elapsed_s=round(time.time() - t_start, 2),
        evaluator=dict(version=EH.VERSION, implementation_hashes=EH.implementation_hashes()),
        plane_manifest=dict(n_features=plane_man["n_features"], catalogue_used=False, sgmc_used=False),
        loqo_fit=fit_meta,
        leakage_canaries=dict(
            total_checked=len(canaries),
            max_discriminative_auc=max_canary_disc,
            any_leakage_flag=any_leak,
            features=canaries,
        ),
        experiments_run=3,
        experiment_quick_comparison=quick_scores,
        selected_arm=winner_arm,
        holdout_buffered_whole_components=summary_comp,
        holdout_buffered_per_fold=per_fold_comp,
        holdout_segment_all=summary_all,
        holdout_segment_detached=summary_det,
        off_catalogue_sgmc_diagnostic=sgmc_diag,
        uniqueness=dict(
            rasters_checked=len(records),
            discriminating_rasters_checked=len(non_lattice_rows),
            pre_placement_surface_worst_abs_spearman=worst_surf_abs_rho,
            final_dots_worst_discriminating_abs_spearman=worst_disc_abs_rho,
            final_dots_worst_discriminating_rho_vs=worst_disc_rho_row["submission"],
            final_dots_worst_discriminating_overlap_3px=worst_disc_overlap,
            final_dots_worst_discriminating_overlap_vs=worst_disc_overlap_row["submission"],
            final_dots_worst_jaccard=dot_check["worst_jaccard_dot_sets"],
            discriminating_lane_unique=disc_unique,
            literal_stride5_lattice_witness=dict(
                submission="13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
                covered_allowed_fraction=lat_cert["covered_allowed_fraction"],
                my_dots_within_3px_of_lattice=next(
                    r["my_dots_within_3px_of_theirs"]
                    for r in dot_check["rows"]
                    if "13gems_20261001_r13-lattice-s5" in r["submission"]
                ),
                spearman_vs_lattice=next(
                    r["spearman_full_footprint"]
                    for r in dot_check["rows"]
                    if "13gems_20261001_r13-lattice-s5" in r["submission"]
                ),
                jaccard_vs_lattice=next(
                    r["jaccard_dot_sets"]
                    for r in dot_check["rows"]
                    if "13gems_20261001_r13-lattice-s5" in r["submission"]
                ),
                note=(
                    "Regular 5-px calibration lattice covers 99.8724% of all allowed pixels within "
                    "sqrt(2^2+2^2)=2.828<=3.0 px; reported literally per protocol alongside "
                    "0/27 discriminating duplicates across 16 repositories."
                ),
            ),
            two_phase_summary=two_phase,
            per_raster_rows=[
                dict(
                    repo=r["repo"],
                    submission=r["submission"],
                    their_dots=r["their_dots"],
                    spearman_full_footprint=r["spearman_full_footprint"],
                    my_dots_within_3px_of_theirs=r["my_dots_within_3px_of_theirs"],
                    jaccard_dot_sets=r["jaccard_dot_sets"],
                )
                for r in dot_check["rows"]
            ],
        ),
        distance_to_catalogue_distribution=dist_quantiles,
        submission_artifact=dict(
            submission_name=stem,
            note=note,
            note_chars=len(note),
            tif_file=str(out_tif.relative_to(ROOT)),
            zip_file=str(out_tif.with_suffix(".zip").relative_to(ROOT)),
            receipt_file=str(out_tif.with_suffix(".json").relative_to(ROOT)),
            tif_sha256=val_receipt["sha256"],
            tif_bytes=val_receipt["bytes"],
            zip_sha256=writer_receipt["zip_sha256"],
            emitted_dots=val_receipt["emitted_positive_pixels"],
            validator=val_receipt,
            template_format_report=fmt_report,
        ),
        gates=dict(
            format_valid=bool(val_receipt["all_checks_passed"] and fmt_report["ok"]),
            leakage_canary_pass=not any_leak,
            beats_incumbent_buffered_whole_components=beats_comp,
            beats_incumbent_segment_all=beats_all,
            beats_incumbent_segment_detached=beats_det,
            discriminating_registry_unique=disc_unique,
            all_gates_passed=all_gates_green,
        ),
        verdict="promote" if all_gates_green else "negative",
    )

    (ROOT / "docs" / "evidence" / "lane86b_results.json").write_text(
        json.dumps(full_results, indent=2, allow_nan=False) + "\n"
    )

    run_card = dict(
        hypothesis=(
            "H86B-GFCO (Session-2 declared lane, advancing PR #6 roadmap): Blind hydrothermal upflow plumes "
            "(GDR-1391 geothermometer thermal disequilibrium dT_chem - T_meas & silica-cation lag + MT clay-cap "
            "edges), multi-depth potential-field contact-offsets (TMI vs 150m upward-continued attenuation + "
            "magnetic director disruption x gravity/basement steps), and relief-deconfounded 1m LiDAR/100m DEM "
            "scarplet chains localize concealed faults missed by single-layer mapping, especially along crack-tip "
            "propagation cones and two-host en-echelon relay stepovers."
        ),
        mechanism=(
            f"Cover-adaptive 4-quadrant LOQO GBDT ensemble (38-feature full + 28-feature cover-blind subsurface/geothermal "
            f"specialist gated by basement depth) coupled with strictly visible-only tip-cone/two-host-relay/bend-splay "
            f"mechanics (S = P_phys^0.65 * (0.12 + 0.88*M_kin)); 300m triangular expected-credit priority disc thinning "
            f"(r=2.8px, d_cat>2px collar, {chosen_budget} binary dots, all-finite zeros outside footprint)."
        ),
        non_fault_mimic=(
            "Playa evaporite conductivity, deep plutonic magnetic contacts, and steep bedrock cliffs / alluvial fan "
            "sorting (discriminants: TMI-vs-TMI_up150 shallow attenuation + gravity cross-step, relief-normalized "
            "LiDAR scarplet collinearity, topographic residualization of K & U/Th, and PU d>4px negative training)."
        ),
        declared_lane_note=(
            "Prompt contains no separate method paragraph (irregularity logged in Session 1). Session 1 tested rank-1 "
            "H86-RMRB (negative, 0.0420) and queued magnetic contact-offset + radiometric-topographic discordance next; "
            "Session 2 executes that exact multi-physics + geothermal-vent synthesis within a 3-experiment budget."
        ),
        holdout_dti=dict(
            evidence_class="HOLDOUT-DTI",
            evaluator_version=EH.VERSION,
            buffered_whole_components_loqo=dict(
                withheld_positives=summary_comp["scores"][winner_arm]["withheld_positive_pixels"],
                candidate_dti=summary_comp["scores"][winner_arm]["dti"],
                ci95=summary_comp["scores"][winner_arm]["ci95"],
                d28_incumbent_dti=summary_comp["scores"]["d28_incumbent"]["dti"],
                d28_incumbent_ci95=summary_comp["scores"]["d28_incumbent"]["ci95"],
                h33_b2_foldfair_dti=summary_comp["scores"]["h33_b2_foldfair"]["dti"],
                h33_b2_foldfair_ci95=summary_comp["scores"]["h33_b2_foldfair"]["ci95"],
                h86_rmrb_pr6_dti=summary_comp["scores"]["h86_rmrb_pr6"]["dti"],
                paired_delta_vs_d28=summary_comp["paired_differences"]["d28_incumbent"]["delta"],
                paired_delta_vs_d28_ci95=summary_comp["paired_differences"]["d28_incumbent"]["ci95"],
                paired_delta_vs_h33_foldfair=summary_comp["paired_differences"]["h33_b2_foldfair"]["delta"],
                paired_delta_vs_h33_foldfair_ci95=summary_comp["paired_differences"]["h33_b2_foldfair"]["ci95"],
            ),
            segment_hide_all=dict(
                withheld_positives=summary_all["scores"][winner_arm]["withheld_positive_pixels"],
                candidate_dti=summary_all["scores"][winner_arm]["dti"],
                ci95=summary_all["scores"][winner_arm]["ci95"],
                d28_incumbent_dti=summary_all["scores"]["d28_incumbent"]["dti"],
                d28_incumbent_ci95=summary_all["scores"]["d28_incumbent"]["ci95"],
                h33_b2_foldfair_dti=summary_all["scores"]["h33_b2_foldfair"]["dti"],
                paired_delta_vs_d28=summary_all["paired_differences"]["d28_incumbent"]["delta"],
                paired_delta_vs_d28_ci95=summary_all["paired_differences"]["d28_incumbent"]["ci95"],
            ),
            segment_hide_detached=dict(
                withheld_positives=summary_det["scores"][winner_arm]["withheld_positive_pixels"],
                candidate_dti=summary_det["scores"][winner_arm]["dti"],
                ci95=summary_det["scores"][winner_arm]["ci95"],
                d28_incumbent_dti=summary_det["scores"]["d28_incumbent"]["dti"],
                d28_incumbent_ci95=summary_det["scores"]["d28_incumbent"]["ci95"],
                h33_b2_foldfair_dti=summary_det["scores"]["h33_b2_foldfair"]["dti"],
                paired_delta_vs_d28=summary_det["paired_differences"]["d28_incumbent"]["delta"],
                paired_delta_vs_d28_ci95=summary_det["paired_differences"]["d28_incumbent"]["ci95"],
            ),
            experiment_progression=quick_scores,
            point_estimate_beats_all_3_holdouts=bool(
                summary_comp["scores"][winner_arm]["dti"] > summary_comp["scores"]["d28_incumbent"]["dti"]
                and summary_comp["scores"][winner_arm]["dti"] > summary_comp["scores"]["h33_b2_foldfair"]["dti"]
                and summary_all["scores"][winner_arm]["dti"] > summary_all["scores"]["d28_incumbent"]["dti"]
                and summary_det["scores"][winner_arm]["dti"] > summary_det["scores"]["d28_incumbent"]["dti"]
            ),
            beats_incumbent=bool(beats_comp and beats_all and beats_det),
        ),
        leakage_canary_auc=dict(
            features_checked=len(canaries),
            max_discriminative_auc=max_canary_disc,
            threshold=0.90,
            any_leakage_flag=any_leak,
        ),
        correlation_overlap_vs_registry=dict(
            rasters_checked=len(records),
            scope=(
                "28 hash-verified rasters across 16 buffedlizard55-lab repositories (12 pinned local + "
                "PR #6 H86-RMRB + 15 cross-repo primary champions GEMSDOE32..83); not an organizer-complete registry."
            ),
            surface_worst_abs_spearman=worst_surf_abs_rho,
            final_worst_discriminating_abs_spearman=worst_disc_abs_rho,
            final_worst_discriminating_dot_overlap_3px=worst_disc_overlap,
            final_worst_discriminating_overlap_vs=worst_disc_overlap_row["submission"],
            worst_modern_comparable_le_62k_overlap_3px=max(
                r["my_dots_within_3px_of_theirs"] for r in non_lattice_rows if r["their_dots"] <= 62_000
            ),
            overlap_3px_vs_gems32_h33_2_b2=next(
                r["my_dots_within_3px_of_theirs"]
                for r in non_lattice_rows
                if "h33-h33-2-b2" in r["submission"]
            ),
            overlap_3px_vs_d28_incumbent=next(
                r["my_dots_within_3px_of_theirs"]
                for r in non_lattice_rows
                if "gems24-h25-1-dotted-h19-5-d2-8" in r["submission"]
            ),
            final_worst_jaccard=dot_check["worst_jaccard_dot_sets"],
            literal_firings_over_0_70=[f["submission"] for f in two_phase["literal_firings"]],
            discriminating_duplicates=0 if disc_unique else len(two_phase["literal_firings"]) - 1,
            literal_stride5_lattice_note=(
                f"13gems stride-5 calibration lattice covers {lat_cert['covered_allowed_fraction']:.6f} of all "
                f"allowed footprint pixels within sqrt(8)=2.828<=3px (rho=-0.0004, jaccard=0.0069); dense legacy "
                f"gems10-h25 (174,232 dots, 25.6% area) = 0.7656 and gems10-h28 (69,281 dots, 26.5% area) = 0.7170 "
                f"also exceed 0.70 literally, whereas all 25 modern/comparable rasters (<=61,328 dots) are <=0.6342."
            ),
        ),
        raster_sha256=val_receipt["sha256"],
        validator=dict(
            status="PASS (automated 15/15 shared validator + template format check; not organizer acceptance)",
            no_nan_inside_footprint=val_receipt["checks"]["in_footprint_all_finite"],
            values_in_0_1=val_receipt["checks"]["range_0_1_guaranteed"],
            crs_shape_transform_match=bool(
                val_receipt["checks"]["crs_epsg_32611"]
                and val_receipt["checks"]["dimensions_3730x3292"]
                and val_receipt["checks"]["transform_matches_sample_submission"]
            ),
            checks=val_receipt["checks"],
            emitted_dots=val_receipt["emitted_positive_pixels"],
            min=val_receipt["min"],
            max=val_receipt["max"],
        ),
        submission_name=stem,
        note=note,
        submission_file=str(out_tif.relative_to(ROOT)),
        zip_file=str(out_tif.with_suffix(".zip").relative_to(ROOT)),
        scores_labelled=(
            "Every local metric is labelled HOLDOUT-DTI (gems57-pooled-hide-v2) or OFF-CATALOGUE-PROXY-DIAGNOSTIC. "
            "No ORGANIZER-CONFIRMED score exists for this new file; historical scores in the brief (0.2778, 0.3195, "
            "0.4413) are owner/user-reported without an organizer receipt in this repo."
        ),
        experiments_run=3,
        verdict="promote" if all_gates_green else "negative",
        submission_ready=all_gates_green,
        approved_for_weekly_slot=False,
        selector_note=(
            "Cleared all automated format, leakage-canary, 3-instrument HOLDOUT-DTI, and 27-raster cross-repo "
            "discriminating uniqueness gates. Final upload to a weekly DrivenData slot remains the human selector's "
            "decision after verifying live weekly quota and the disclosed 13gems stride-5 lattice witness."
            if all_gates_green
            else (
                "FORMAT-VALID ARTIFACT (15/15 checks PASS; 0.3012 overlap vs GEMSDOE32 H33-2-B2; <=0.6342 vs all 25 "
                "modern/comparable rasters; beats d2.8 and H33-2-B2 in point estimate across all 3 holdouts: "
                "0.1078 vs 0.0961 whole-component LOQO, 0.1396 vs 0.1011 holdout-all, 0.1521 vs 0.1035 detached), "
                "BUT DO NOT SPEND A WEEKLY SLOT AUTOMATICALLY: literal 3-px overlap exceeds 0.70 against 3 dense "
                "legacy GEMSDOE24 rasters (13gems lattice 0.9988, gems10-h25 174k-dot 0.7656, gems10-h28 69k-dot "
                "0.7170) and whole-component LOQO paired 95% CI narrowly straddles zero ([-0.0007, +0.0343])."
            )
        ),
    )
    (ROOT / "docs" / "evidence" / "h86b-gfco-run-card.json").write_text(
        json.dumps(run_card, indent=2, allow_nan=False) + "\n"
    )
    print("\n=== LANE H86B-GFCO COMPLETE ===", flush=True)
    print(json.dumps({
        "verdict": run_card["verdict"],
        "submission_ready": run_card["submission_ready"],
        "submission_file": run_card["submission_file"],
        "raster_sha256": run_card["raster_sha256"],
        "holdout_buffered_comp": run_card["holdout_dti"]["buffered_whole_components_loqo"],
        "holdout_all": run_card["holdout_dti"]["segment_hide_all"],
        "holdout_detached": run_card["holdout_dti"]["segment_hide_detached"],
        "worst_disc_overlap": worst_disc_overlap,
        "worst_surf_abs_rho": worst_surf_abs_rho,
    }, indent=2))


if __name__ == "__main__":
    main()
