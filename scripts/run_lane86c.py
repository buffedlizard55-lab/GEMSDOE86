"""Execute Lane H86C-KSLB end-to-end within the strict 3-experiment / 2-hour budget.

Declared lane (Session 3, advancing Session-2 H86B-GFCO next steps & README §9):
  H86C-KSLB: Lahontan-Shoreline-Deconfounded Seamless 1m-LiDAR + 10m-3DEP Tectonic Scarp,
  Fluvial ksn/chi Knickzone & Blakely-Miller Zero-Crossing Blind-Filament LOQO Ensemble
  coupled via Dual-Regime Noisy-OR Discovery Posterior:
    S_KSLB(x) = 1 - (1 - P_link(x)) * (1 - P_blind(x))
  where P_link restricts kinematic stress transfer to crack-tip cones, two-host relays,
  and strike-concordant / true bend-hinge splays (eliminating H86B's isotropic straight-fault
  sausage), and P_blind enables unchoked whole-component discovery along convex
  filament-coherent multi-family physical corridors.

Reuses `vendor/gems57` byte-for-byte without modification.
`main()` calls `protocol_preflight.require_feasible()` unconditionally before argument parsing,
feature construction, fitting, or placement under the literal 100%-dense witness stop; no CLI or
boolean bypass exists.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import resource
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

import h86c_features as F

BUDGET_38K = 37654
BUDGET_44K = 44090

# Cover-blind subsurface/hydrothermal/seismic specialist subset (all surface DEM/LiDAR/fluvial-topo planes excluded)
SURFACE_TOPO_EXCLUDE = frozenset({
    "topo10_curv_prof_z",
    "topo10_hs_lineament_z",
    "topo10_aspect_coh_z",
    "topo10_piedmont_scarp",
    "topo10_scarp_chain",
    "lahontan_zone_weight",
    "lahontan_shoreline_mimic",
    "tectonic_scarp_deconf",
    "tectonic_scarp_chain",
    "lidar_valid",
    "lidar_step_z",
    "lidar_face_asym",
    "dem_piedmont_hinge",
    "dem_valley_chain",
    "fluv_ksn_knick_s2",
    "fluv_ksn_chain_s5",
    "fluv_chi_step_s3",
    "fluv_scarp_knick_couple",
    "zmean_elev_z",
    "topo10_slope_p90_z",
})
SUBSURF_INDICES = [i for i, nm in enumerate(F.PHYS_FEATURES) if nm not in SURFACE_TOPO_EXCLUDE]


def gather_lowmem(pdir: Path, rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    """Read `(len(rows), 48)` float32 features opening one plane file at a time."""
    X = np.empty((rows.size, len(F.PHYS_FEATURES)), dtype=np.float32)
    for j, name in enumerate(F.PHYS_FEATURES):
        arr = np.load(pdir / f"{name}.npy", mmap_mode="r")
        X[:, j] = arr[rows, cols]
        del arr
    return X


def cached_kinematic(
    data_dir: Path,
    tag: str,
    vis: np.ndarray,
    adir: Path,
) -> dict[str, np.ndarray]:
    kdir = data_dir / "cache" / "h86c_kin"
    kdir.mkdir(parents=True, exist_ok=True)
    p = kdir / f"{tag}.npz"
    if p.is_file():
        z = np.load(p)
        return {
            "m_kin": z["m_kin"],
            "d1": z["d1"],
            "tip_cone": z["tip_cone"],
            "relay_bridge": z["relay_bridge"],
            "hinge_concord_splay": z["hinge_concord_splay"],
        }
    pc2 = np.load(adir / "phys_cos2.npy", mmap_mode="r")
    ps2 = np.load(adir / "phys_sin2.npy", mmap_mode="r")
    pcoh = np.load(adir / "phys_coh.npy", mmap_mode="r")
    kc = F.compute_kslb_kinematics(vis, pc2, ps2, pcoh)
    del pc2, ps2, pcoh
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
    data_dir: Path,
    g: G.Grid,
    quad: np.ndarray,
    strictly_visible: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Train 4 spatially blocked LOQO ensembles + 2-seed full-catalogue ensemble."""
    # Direct imported calls must stop before model or candidate work.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    cache_path = data_dir / "cache" / "h86c_p_phys_oof.npz"
    if cache_path.is_file():
        z = np.load(cache_path)
        return z["p_oof"], z["p_full"], json.loads(str(z["meta_json"]))

    t0 = time.time()
    pdir = F.plane_dir_for(data_dir)
    fp = g.footprint
    bdepth = np.load(pdir / "base_depth_z.npy", mmap_mode="r")
    w_cover_full = np.clip(0.25 + 0.22 * np.asarray(bdepth, dtype=np.float32), 0.15, 0.70)
    del bdepth

    p_oof = np.zeros(g.shape, dtype=np.float32)
    fold_stats = {}

    kw_all = dict(
        max_depth=6,
        max_iter=280,
        learning_rate=0.055,
        min_samples_leaf=80,
        l2_regularization=2.5,
        early_stopping=False,
    )
    kw_sub = dict(
        max_depth=5,
        max_iter=230,
        learning_rate=0.055,
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

        rng = np.random.default_rng(8630 + q)
        n_neg = min(170_000, neg_pool_y.size)
        take = rng.choice(neg_pool_y.size, size=n_neg, replace=False)
        tr_y = np.concatenate([pos_y, neg_pool_y[take]])
        tr_x = np.concatenate([pos_x, neg_pool_x[take]])
        y_tr = np.concatenate([np.ones(pos_y.size, np.int8), np.zeros(n_neg, np.int8)])
        w_neg = float(neg_pool_y.size) / float(max(n_neg, 1))
        w_tr = np.concatenate([np.ones(pos_y.size, np.float64), np.full(n_neg, w_neg, np.float64)])

        X_tr = gather_lowmem(pdir, tr_y, tr_x)
        m_all = HistGradientBoostingClassifier(**kw_all, random_state=863 + q)
        m_all.fit(X_tr, y_tr, sample_weight=w_tr)
        m_sub = HistGradientBoostingClassifier(**kw_sub, random_state=963 + q)
        m_sub.fit(X_tr[:, SUBSURF_INDICES], y_tr, sample_weight=w_tr)
        del X_tr
        gc.collect()

        te_y, te_x = np.nonzero(fp & (quad == q))
        for s0 in range(0, te_y.size, 300_000):
            sl = slice(s0, min(s0 + 300_000, te_y.size))
            yy, xx = te_y[sl], te_x[sl]
            X_te = gather_lowmem(pdir, yy, xx)
            pa = m_all.predict_proba(X_te)[:, 1].astype(np.float32)
            ps = m_sub.predict_proba(X_te[:, SUBSURF_INDICES])[:, 1].astype(np.float32)
            wc = w_cover_full[yy, xx]
            p_oof[yy, xx] = (1.0 - wc) * pa + wc * np.maximum(pa, 0.92 * ps)
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

    # Final full-map physical ensemble (2 seeds on full catalogue for live artifact only)
    p_full_acc = np.zeros(g.shape, dtype=np.float32)
    d_full = ndi.distance_transform_edt(~g.catalogue)
    pos_fy, pos_fx = np.nonzero(g.catalogue & fp)
    neg_fy, neg_fx = np.nonzero(fp & (d_full > 4.0))
    del d_full
    fp_y, fp_x = np.nonzero(fp)
    n_seeds = 2
    for sd in range(n_seeds):
        rng = np.random.default_rng(1863 + sd)
        n_neg = min(180_000, neg_fy.size)
        take = rng.choice(neg_fy.size, size=n_neg, replace=False)
        tr_y = np.concatenate([pos_fy, neg_fy[take]])
        tr_x = np.concatenate([pos_fx, neg_fx[take]])
        y_tr = np.concatenate([np.ones(pos_fy.size, np.int8), np.zeros(n_neg, np.int8)])
        w_neg = float(neg_fy.size) / float(max(n_neg, 1))
        w_tr = np.concatenate([np.ones(pos_fy.size, np.float64), np.full(n_neg, w_neg, np.float64)])
        X_tr = gather_lowmem(pdir, tr_y, tr_x)
        m_all = HistGradientBoostingClassifier(**kw_all, random_state=1863 + sd)
        m_all.fit(X_tr, y_tr, sample_weight=w_tr)
        m_sub = HistGradientBoostingClassifier(**kw_sub, random_state=2863 + sd)
        m_sub.fit(X_tr[:, SUBSURF_INDICES], y_tr, sample_weight=w_tr)
        del X_tr
        for s0 in range(0, fp_y.size, 300_000):
            sl = slice(s0, min(s0 + 300_000, fp_y.size))
            yy, xx = fp_y[sl], fp_x[sl]
            X_te = gather_lowmem(pdir, yy, xx)
            pa = m_all.predict_proba(X_te)[:, 1].astype(np.float32)
            ps = m_sub.predict_proba(X_te[:, SUBSURF_INDICES])[:, 1].astype(np.float32)
            wc = w_cover_full[yy, xx]
            p_full_acc[yy, xx] += ((1.0 - wc) * pa + wc * np.maximum(pa, 0.92 * ps)) / float(n_seeds)
            del X_te
        gc.collect()

    meta = dict(
        elapsed_s=round(time.time() - t0, 2),
        n_total_features=len(F.PHYS_FEATURES),
        n_subsurf_features=len(SUBSURF_INDICES),
        folds=fold_stats,
    )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache_path, p_oof=p_oof, p_full=p_full_acc, meta_json=json.dumps(meta))
    return p_oof, p_full_acc, meta


def build_filament_fields(p_phys: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Normalize `p_phys` onto `[0, 1]` and compute 8-azimuth filament response `r_fil` & `p_fil`."""
    p_norm = np.zeros(p_phys.shape, dtype=np.float32)
    ok = valid & (p_phys > 0) & np.isfinite(p_phys)
    if ok.any():
        hi = max(float(np.percentile(p_phys[ok], 99.85)), 1e-6)
        p_norm[ok] = np.clip(p_phys[ok] / hi, 0.0, 1.0)
    r_fil = F.filament_enhance(p_norm, valid, sig_par=3.8, sig_perp=1.0, n_angles=8)
    p_fil = np.where(valid, np.clip(0.52 * p_norm + 0.48 * r_fil, 0.0, 1.0), 0.0).astype(np.float32)
    return p_fil, r_fil


def noisyor_discovery_surface(
    p_fil: np.ndarray,
    r_fil: np.ndarray,
    m_kin: np.ndarray,
    c_multi: np.ndarray,
    valid: np.ndarray,
) -> np.ndarray:
    """Dual-Regime Noisy-OR Discovery Posterior:
      P_link  = p_fil^0.62 * m_kin
      P_blind = 0.58 * p_fil^1.65 * (0.30 + 0.70*r_fil) * (0.35 + 0.65*c_multi)
      S_KSLB  = 1 - (1 - P_link) * (1 - P_blind)
    """
    pf = np.where(valid & np.isfinite(p_fil), np.clip(p_fil, 0.0, 1.0), 0.0)
    rf = np.where(valid & np.isfinite(r_fil), np.clip(r_fil, 0.0, 1.0), 0.0)
    mk = np.where(valid & np.isfinite(m_kin), np.clip(m_kin, 0.0, 1.0), 0.0)
    cm = np.where(valid & np.isfinite(c_multi), np.clip(c_multi, 0.0, 1.0), 0.0)

    p_link = np.clip(np.power(pf, 0.62) * mk, 0.0, 1.0)
    p_blind = np.clip(
        0.58 * np.power(pf, 1.65) * (0.30 + 0.70 * rf) * (0.35 + 0.65 * cm),
        0.0,
        1.0,
    )
    surf = (1.0 - (1.0 - p_link) * (1.0 - p_blind)).astype(np.float32)
    surf[~valid] = 0.0
    return surf


def run_leakage_canaries(data_dir: Path, g: G.Grid, comp_folds: list[dict]) -> dict:
    rng = np.random.default_rng(8603)
    pdir = F.plane_dir_for(data_dir)
    adir = F.aux_dir_for(data_dir)
    out = {}
    for name in F.PHYS_FEATURES:
        pl = np.load(pdir / f"{name}.npy", mmap_mode="r")
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

    kc = cached_kinematic(data_dir, "comp_seed20", comp_folds[0]["visible"], adir)
    for kname in ("tip_cone", "relay_bridge", "hinge_concord_splay", "m_kin"):
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


def collect_registry_records(data_dir: Path) -> list[dict]:
    records = []
    seen_sha = set()

    man = json.loads((ROOT / "research" / "upstream" / "data_manifest.json").read_text())
    for e in man["files"]:
        if e["group"] == "scored":
            p = data_dir / e["dest"]
            if p.is_file() and e["sha256"] not in seen_sha:
                seen_sha.add(e["sha256"])
                records.append(dict(repo=e["repo"], submission=p.name, file=str(p), sha256=e["sha256"]))

    # All prior GEMSDOE86 candidate TIFFs in docs/downloads/ (excluding H86C-KSLB's own output)
    inv_path = ROOT / "docs" / "evidence" / "download-inventory.json"
    if inv_path.is_file():
        for e in json.loads(inv_path.read_text())["artifacts"]:
            p = ROOT / e["file"]
            if p.is_file() and not p.name.startswith("gems86-h86c-kslb-") and e["sha256"] not in seen_sha:
                seen_sha.add(e["sha256"])
                records.append(dict(repo="buffedlizard55-lab/GEMSDOE86", submission=p.name, file=str(p), sha256=e["sha256"]))

    for mfile in (
        ROOT / "research" / "upstream" / "cross_repo_champions_manifest.json",
        ROOT / "research" / "upstream" / "cross_repo_champions_ext88_manifest.json",
    ):
        if mfile.is_file():
            for e in json.loads(mfile.read_text())["files"]:
                p = data_dir / e["dest"]
                if p.is_file() and e["sha256"] not in seen_sha:
                    seen_sha.add(e["sha256"])
                    records.append(dict(repo=e["repo"], submission=p.name, file=str(p), sha256=e["sha256"]))

    wit_pin = ROOT / "research" / "registry_witness_pin.json"
    if wit_pin.is_file():
        wp = json.loads(wit_pin.read_text())
        p = data_dir / wp["dest"]
        if p.is_file() and wp["sha256"] not in seen_sha:
            seen_sha.add(wp["sha256"])
            records.append(dict(repo=wp["repo"], submission="dense-witness-100pct-support.tif", file=str(p), sha256=wp["sha256"]))

    return records


def main(data_dir: Path | None = None):
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    if data_dir is None:
        ap = argparse.ArgumentParser(description=__doc__)
        ap.add_argument("--data-dir", type=Path, default=F.DEFAULT_DATA_DIR)
        data_dir = ap.parse_args().data_dir

    d = Path(data_dir)
    t_start = time.time()
    plane_man = F.build_physical_planes(d)
    adir = F.aux_dir_for(d)
    g = G.load_grid(d)
    fp, cat = g.footprint, g.catalogue
    quad = H.quadrant_ids(fp)

    comp_folds, _ = H.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3)
    ctx = H.build_holdout(g, seeds=(20, 21), modes=("all", "detached"))

    all_hidden = comp_folds[0]["hidden_all"].copy()
    for hmask in ctx.hidden_by_cell.values():
        all_hidden |= hmask
    strictly_visible = cat & ~all_hidden

    print("Step 1/5: Running 52 single-feature leakage canaries...", flush=True)
    canaries = run_leakage_canaries(d, g, comp_folds)
    any_leak = any(v["leakage_flag"] for v in canaries.values())
    max_canary_disc = max(v["discriminative_auc_max"] for v in canaries.values())
    print(f"Canaries complete: {len(canaries)} checked, max_disc={max_canary_disc:.4f}, any_leak={any_leak}", flush=True)
    if any_leak:
        raise RuntimeError("STOP: Leakage canary > 0.90 triggered!")

    print("Step 2/5: Fitting spatially blocked LOQO KSLB ensemble...", flush=True)
    p_oof, p_full, fit_meta = fit_and_predict_p_phys(d, g, quad, strictly_visible)
    p_fil_oof, r_fil_oof = build_filament_fields(p_oof, fp)
    c_multi = np.asarray(np.load(adir / "c_multi.npy", mmap_mode="r"), dtype=np.float32)

    # Load fixed reference controls once
    with rasterio.open(d / "scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif") as ds:
        d28_dots = U._dots(ds.read(1)) & fp
    with rasterio.open(d / "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") as ds:
        h195_dots = U._dots(ds.read(1)) & fp
    with rasterio.open(ROOT / "docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif") as ds:
        pr6_dots = U._dots(ds.read(1)) & fp

    print("Step 3/5: Executing the 3 pre-declared experiments (E1, E2, E3)...", flush=True)
    n_blocks = ((g.height + 199) // 200) * ((g.width + 199) // 200)
    arm_names = (
        "E1_kslb_phys_fil_38k",
        "E2_kslb_noisyor_38k",
        "E3_kslb_noisyor_44k",
        "d28_incumbent",
        "h33_b2_foldfair",
        "h19_5_ridge",
        "h86_rmrb_pr6",
    )

    # ---- Primary Holdout A: Whole-component 3-px buffered LOQO (11,321 withheld positives)
    kc_comp = cached_kinematic(d, "comp_seed20", comp_folds[0]["visible"], adir)
    allow_comp = fp & (kc_comp["d1"] > 2.0)
    surf_noisyor_comp = noisyor_discovery_surface(p_fil_oof, r_fil_oof, kc_comp["m_kin"], c_multi, fp)
    dots_comp = {
        "E1_kslb_phys_fil_38k": emit_ek_poisson(p_fil_oof, allow_comp, BUDGET_38K),
        "E2_kslb_noisyor_38k": emit_ek_poisson(surf_noisyor_comp, allow_comp, BUDGET_38K),
        "E3_kslb_noisyor_44k": emit_ek_poisson(surf_noisyor_comp, allow_comp, BUDGET_44K),
        "d28_incumbent": d28_dots,
        "h33_b2_foldfair": d28_dots & allow_comp,
        "h19_5_ridge": h195_dots,
        "h86_rmrb_pr6": pr6_dots,
    }
    del kc_comp, surf_noisyor_comp
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
            kc_draw = cached_kinematic(d, f"ctx_s{seed}_{mode}", vis_draw, adir)
            allow_draw = fp & (kc_draw["d1"] > 2.0)
            surf_draw = noisyor_discovery_surface(p_fil_oof, r_fil_oof, kc_draw["m_kin"], c_multi, fp)
            dots_draw = {
                "E1_kslb_phys_fil_38k": emit_ek_poisson(p_fil_oof, allow_draw, BUDGET_38K),
                "E2_kslb_noisyor_38k": emit_ek_poisson(surf_draw, allow_draw, BUDGET_38K),
                "E3_kslb_noisyor_44k": emit_ek_poisson(surf_draw, allow_draw, BUDGET_44K),
                "d28_incumbent": d28_dots,
                "h33_b2_foldfair": d28_dots & allow_draw,
                "h19_5_ridge": h195_dots,
                "h86_rmrb_pr6": pr6_dots,
            }
            del kc_draw, surf_draw
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

    exp_arms = ("E1_kslb_phys_fil_38k", "E2_kslb_noisyor_38k", "E3_kslb_noisyor_44k")
    quick_scores = {}
    for ea in exp_arms:
        d_comp = float(EH.from_terms(terms_comp[ea].sum(axis=0)))
        d_all = float(EH.from_terms(terms_ctx["all"][ea].sum(axis=0)))
        d_det = float(EH.from_terms(terms_ctx["detached"][ea].sum(axis=0)))
        quick_scores[ea] = dict(buffered_comp=d_comp, all=d_all, detached=d_det, mean_ab=0.5 * (d_comp + d_all))
        print(f"  {ea:22s}: buffered_comp={d_comp:.4f} | all={d_all:.4f} | detached={d_det:.4f}", flush=True)

    winner_arm = max(exp_arms, key=lambda k: quick_scores[k]["mean_ab"])
    print(f"Selected winning arm: {winner_arm}", flush=True)

    summary_comp = EH.pooled_summary(terms_comp, draws=1000, seed=520810, candidate=winner_arm)
    summary_all = EH.pooled_summary(terms_ctx["all"], draws=1000, seed=520810, candidate=winner_arm)
    summary_det = EH.pooled_summary(terms_ctx["detached"], draws=1000, seed=520810, candidate=winner_arm)

    # Auxiliary Off-Catalogue SGMC Proxy Diagnostic (zero SGMC bytes in training/features)
    with rasterio.open(d / "external/derived_sgmc_faults_100m_u8.tif") as sds:
        sgmc_raw = (sds.read(1) > 0) & fp
    d_cat_full = ndi.distance_transform_edt(~cat)
    sgmc_offcat = sgmc_raw & (d_cat_full > 3.0)
    kc_full = cached_kinematic(d, "full_catalogue", cat, adir)
    allow_full = fp & (kc_full["d1"] > 2.0)

    p_fil_full, r_fil_full = build_filament_fields(p_oof, fp)
    surf_full_noisyor = noisyor_discovery_surface(p_fil_full, r_fil_full, kc_full["m_kin"], c_multi, fp)
    surf_oof_noisyor_fullcat = surf_full_noisyor

    with rasterio.open(ROOT / "docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.tif") as bds:
        h86b_dots = U._dots(bds.read(1)) & fp

    sgmc_diag = {}
    for nm, dts in (
        ("E1_kslb_phys_fil_38k_oof", emit_ek_poisson(p_fil_oof, allow_full, BUDGET_38K)),
        ("E2_kslb_noisyor_38k_oof", emit_ek_poisson(surf_oof_noisyor_fullcat, allow_full, BUDGET_38K)),
        ("E3_kslb_noisyor_44k_oof", emit_ek_poisson(surf_oof_noisyor_fullcat, allow_full, BUDGET_44K)),
        ("h86b_gfco_pr16", h86b_dots),
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

    # ---- Step 4/5: Pre-placement surface AND final-dot uniqueness check across 38 rasters
    print("Step 4/5: Running pre-placement surface & final-dot uniqueness checks...", flush=True)
    if winner_arm == "E1_kslb_phys_fil_38k":
        chosen_surface = np.where(allow_full, p_fil_full, 0.0).astype(np.float32)
        chosen_budget = BUDGET_38K
    elif winner_arm == "E2_kslb_noisyor_38k":
        chosen_surface = np.where(allow_full, surf_full_noisyor, 0.0).astype(np.float32)
        chosen_budget = BUDGET_38K
    else:
        chosen_surface = np.where(allow_full, surf_full_noisyor, 0.0).astype(np.float32)
        chosen_budget = BUDGET_44K

    s_max = max(float(chosen_surface.max()), 1e-6)
    chosen_surface_01 = np.clip(chosen_surface / s_max, 0.0, 1.0).astype(np.float32)
    chosen_surface_01[~fp] = 0.0

    records = collect_registry_records(d)
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

    lat_path = d / "scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
    lat_cert = U.saturation_certificate(lat_path, fp, cat)
    wit_path = d / "registry/dense-witness.tif"
    wit_cert = U.saturation_certificate(wit_path, fp, cat)

    # Separate saturated witnesses (100% dense surface, GEMS87 90.4% continuous surface, 13gems 99.87% stride-5 lattice)
    # from informative dot-field candidates (< 20% support and not stride-5 calibration lattice)
    disc_dot_rows = [
        r for r in dot_check["rows"]
        if "error" not in r
        and r["their_dots"] <= int(0.20 * fp.sum())
        and "13gems_20261001_r13-lattice-s5" not in r["submission"]
    ]
    modern_rows = [
        r for r in disc_dot_rows
        if r["their_dots"] <= 95_000
        and not r["submission"].startswith("gems10-")
    ]
    gems86_sibling_rows = [r for r in dot_check["rows"] if r.get("repo") == "buffedlizard55-lab/GEMSDOE86"]

    worst_disc_overlap_row = max(disc_dot_rows, key=lambda r: r["my_dots_within_3px_of_theirs"])
    worst_disc_rho_row = max(
        dot_check["rows"],
        key=lambda r: abs(r["spearman_full_footprint"]) if r.get("spearman_full_footprint") is not None else 0.0,
    )
    worst_modern_row = max(modern_rows, key=lambda r: r["my_dots_within_3px_of_theirs"])
    worst_gems86_row = max(gems86_sibling_rows, key=lambda r: r["my_dots_within_3px_of_theirs"])

    worst_disc_overlap = float(worst_disc_overlap_row["my_dots_within_3px_of_theirs"])
    worst_all_abs_rho = abs(float(worst_disc_rho_row["spearman_full_footprint"]))
    worst_modern_overlap = float(worst_modern_row["my_dots_within_3px_of_theirs"])
    worst_gems86_overlap = float(worst_gems86_row["my_dots_within_3px_of_theirs"])

    print(
        f"Final dots checked vs {len(records)} rasters | "
        f"non-lattice dot-field worst overlap={worst_disc_overlap:.4f} ({worst_disc_overlap_row['submission']}) | "
        f"modern <=95k worst={worst_modern_overlap:.4f} ({worst_modern_row['submission']}) | "
        f"GEMSDOE86 6-lane worst={worst_gems86_overlap:.4f} ({worst_gems86_row['submission']}) | "
        f"worst |rho|={worst_all_abs_rho:.4f}",
        flush=True,
    )

    d_on_dots = d_cat_full[final_dots]
    dist_quantiles = {
        "min_px": round(float(d_on_dots.min()), 4),
        "p10_px": round(float(np.percentile(d_on_dots, 10)), 2),
        "p25_px": round(float(np.percentile(d_on_dots, 25)), 2),
        "median_px": round(float(np.median(d_on_dots)), 2),
        "p75_px": round(float(np.percentile(d_on_dots, 75)), 2),
        "p90_px": round(float(np.percentile(d_on_dots, 90)), 2),
        "frac_gt_15px_blind_domain": round(float((d_on_dots > 15.0).mean()), 4),
    }

    # ---- Step 5/5: Serialize GeoTIFF + single-TIF ZIP + receipt via unmodified shared writer
    print("Step 5/5: Writing & validating GeoTIFF via shared submission_writer...", flush=True)
    digest8 = hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()[:8]
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stem = f"gems86-h86c-kslb-{chosen_budget}dots-{ts}-{digest8}"
    out_tif = ROOT / "docs" / "downloads" / f"{stem}-zeros.tif"
    note = (
        f"H86C-KSLB Lahontan-deconf 10m+LiDAR+ksn+Blakely NoisyOR LOQO, "
        f"{chosen_budget} dots d>2px, zeros"
    )
    assert len(note) <= 140, len(note)

    writer_receipt = write_submission(
        out_tif,
        pred,
        d / "sample_submission.tif",
        fp,
        note=note,
        name=stem,
        catalogue=cat,
        metadata=dict(lane="H86C-KSLB", winner_arm=winner_arm, budget=chosen_budget, content_digest8=digest8),
    )
    val_receipt = V.validate(out_tif, footprint=fp, catalogue=cat)
    V.assert_submittable(val_receipt)
    fmt_report = GT.format_report(out_tif, d / "sample_submission.tif", footprint=fp)
    assert fmt_report["ok"], fmt_report["problems"]

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
    disc_unique = (worst_surf_abs_rho <= 0.90) and (worst_all_abs_rho <= 0.90) and (worst_disc_overlap <= 0.70)
    # Fail-closed literal rule: dense_witness (100% allowed support) forces literal stop_required=True
    literal_unique = bool(dot_check["unique"] and not dot_check["stop_required"])
    all_gates_green = bool(
        val_receipt["all_checks_passed"]
        and fmt_report["ok"]
        and (not any_leak)
        and beats_comp
        and beats_all
        and beats_det
        and disc_unique
        and literal_unique
    )

    rss_mb = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)
    h33_ov = next(
        r["my_dots_within_3px_of_theirs"]
        for r in dot_check["rows"]
        if "gemsdoe32-h33-h33-2-b2" in r["submission"]
    )
    d28_ov = next(
        r["my_dots_within_3px_of_theirs"]
        for r in dot_check["rows"]
        if "gems24-h25-1-dotted-h19-5-d2-8" in r["submission"]
    )
    h86b_ov = next(
        r["my_dots_within_3px_of_theirs"]
        for r in dot_check["rows"]
        if "gems86-h86b-gfco" in r["submission"]
    )

    full_results = dict(
        lane="H86C-KSLB",
        generated_utc=ts,
        elapsed_s=round(time.time() - t_start, 2),
        peak_rss_mb=rss_mb,
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
            discriminating_dot_rasters_checked=len(disc_dot_rows),
            pre_placement_surface_worst_abs_spearman=worst_surf_abs_rho,
            final_dots_worst_all_abs_spearman=worst_all_abs_rho,
            final_dots_worst_rho_vs=worst_disc_rho_row["submission"],
            final_dots_worst_nonlattice_dot_overlap_3px=worst_disc_overlap,
            final_dots_worst_nonlattice_dot_overlap_vs=worst_disc_overlap_row["submission"],
            final_dots_worst_modern_comparable_overlap_3px=worst_modern_overlap,
            final_dots_worst_modern_comparable_vs=worst_modern_row["submission"],
            final_dots_worst_gems86_intralane_overlap_3px=worst_gems86_overlap,
            final_dots_worst_gems86_intralane_vs=worst_gems86_row["submission"],
            overlap_3px_vs_gems32_h33_2_b2=h33_ov,
            overlap_3px_vs_d28_incumbent=d28_ov,
            overlap_3px_vs_h86b_gfco=h86b_ov,
            final_dots_worst_jaccard=dot_check["worst_jaccard_dot_sets"],
            discriminating_nonlattice_unique=disc_unique,
            literal_protocol_unique=literal_unique,
            saturation_witnesses=dict(
                dense_100pct_witness=wit_cert,
                stride5_lattice_witness=lat_cert,
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
            discriminating_nonlattice_unique=disc_unique,
            literal_protocol_unique=literal_unique,
            all_gates_passed=all_gates_green,
        ),
        verdict="promote" if all_gates_green else "negative",
    )

    (ROOT / "docs" / "evidence" / "lane86c_results.json").write_text(
        json.dumps(full_results, indent=2, allow_nan=False) + "\n"
    )
    (ROOT / "docs" / "evidence" / "h86c_crosslane_uniqueness.json").write_text(
        json.dumps(full_results["uniqueness"], indent=2, allow_nan=False) + "\n"
    )

    run_card = dict(
        hypothesis=(
            "H86C-KSLB (Session-3 declared lane, advancing H86B-GFCO & README §9 next steps): "
            "Seamless 10m-3DEP + 1m-LiDAR tectonic scarps deconfounded against contour-parallel "
            "Pleistocene Lake Lahontan shorelines (1180-1355m ASL), drainage-area-weighted fluvial "
            "ksn knickzone chains & chi divide steps, Blakely-Miller magnetic/gravity tilt zero-crossings, "
            "basement-hinge flexure, GDR-1391 geothermometer disequilibrium, and seismicity-strain fabric "
            "recover both strike-concordant linkage strands and detached whole-component blind faults."
        ),
        mechanism=(
            f"Cover-adaptive 4-quadrant LOQO GBDT ensemble (48-feature full + 28-feature cover-blind "
            f"subsurface specialist) + 8-azimuth DoG filament sharpening, fused via Dual-Regime Noisy-OR "
            f"Discovery Posterior S = 1 - (1 - P_link)*(1 - P_blind) (strike-concordant tip/relay/hinge "
            f"linkage + convex multi-family blind filaments); 300m expected-credit r=2.8px disc thinning, "
            f"d_cat>2px collar, {chosen_budget} binary dots, all-finite zeros outside footprint."
        ),
        non_fault_mimic=(
            "Pleistocene Lake Lahontan wave-cut shorelines (1180-1355m equipotential contour-parallel benches), "
            "incised dendritic canyon walls, passive pluton edges, and playa evaporite conductivity "
            "(discriminants: regional contour-strike transversality rejection, drainage-area-weighted ksn "
            "knickzone co-activation, Blakely tilt zero-crossing x basement flexure, and PU d>4px training)."
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
                h86b_gfco_pr16_loqo_dti=0.10775922634537677,
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
                h33_b2_foldfair_dti=summary_all["scores"]["h33_b2_foldfair"]["dti"],
                paired_delta_vs_d28=summary_all["paired_differences"]["d28_incumbent"]["delta"],
                paired_delta_vs_d28_ci95=summary_all["paired_differences"]["d28_incumbent"]["ci95"],
            ),
            segment_hide_detached=dict(
                withheld_positives=summary_det["scores"][winner_arm]["withheld_positive_pixels"],
                candidate_dti=summary_det["scores"][winner_arm]["dti"],
                ci95=summary_det["scores"][winner_arm]["ci95"],
                d28_incumbent_dti=summary_det["scores"]["d28_incumbent"]["dti"],
                h33_b2_foldfair_dti=summary_det["scores"]["h33_b2_foldfair"]["dti"],
                paired_delta_vs_d28=summary_det["paired_differences"]["d28_incumbent"]["delta"],
                paired_delta_vs_d28_ci95=summary_det["paired_differences"]["d28_incumbent"]["ci95"],
            ),
            experiment_progression=quick_scores,
            beats_incumbent_all_3_holdouts_95ci=bool(beats_comp and beats_all and beats_det),
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
                "38 hash-verified rasters across 20+ buffedlizard55-lab repositories "
                "(12 GEMSDOE24 + 6 prior GEMSDOE86 lanes + 19 cross-repo primary champions GEMSDOE32..88 + "
                "1 pinned 100%-support dense witness); not an organizer-complete registry."
            ),
            surface_worst_abs_spearman=worst_surf_abs_rho,
            final_worst_all_abs_spearman=worst_all_abs_rho,
            final_worst_nonlattice_dot_overlap_3px=worst_disc_overlap,
            final_worst_nonlattice_dot_overlap_vs=worst_disc_overlap_row["submission"],
            final_worst_modern_comparable_overlap_3px=worst_modern_overlap,
            final_worst_gems86_intralane_overlap_3px=worst_gems86_overlap,
            overlap_3px_vs_gems32_h33_2_b2=h33_ov,
            overlap_3px_vs_d28_incumbent=d28_ov,
            overlap_3px_vs_h86b_gfco=h86b_ov,
            final_worst_jaccard=dot_check["worst_jaccard_dot_sets"],
            nonlattice_dot_field_duplicates=sum(1 for r in disc_dot_rows if r["my_dots_within_3px_of_theirs"] > 0.70),
            literal_firings_over_0_70=[f["submission"] for f in two_phase["literal_firings"]],
            discriminating_nonlattice_unique=disc_unique,
            literal_protocol_unique=literal_unique,
        ),
        raster_sha256=val_receipt["sha256"],
        validator=dict(
            status="PASS (automated 15/15 shared validator + template format check; not organizer acceptance)",
            no_nan_inside_footprint=bool(val_receipt["n_nan"] == 0),
            values_in_0_1=bool(val_receipt["min"] >= 0.0 and val_receipt["max"] <= 1.0),
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
            "Every local metric is labelled HOLDOUT-DTI (gems57-pooled-hide-v2) or "
            "OFF-CATALOGUE-PROXY-DIAGNOSTIC. Zero ORGANIZER-CONFIRMED scores exist in GEMSDOE86; "
            "historical figures in the brief (0.2778, 0.3195, 0.4413) are owner/public reports without "
            "an organizer submission receipt for this repository."
        ),
        experiments_run=3,
        verdict="promote" if all_gates_green else "negative",
        submission_ready=bool(all_gates_green),
        approved_for_weekly_slot=bool(all_gates_green),
        selector_note=(
            "FORMAT-VALID RESEARCH ARTIFACT (15/15 checks PASS; 52/52 leakage canaries PASS) — "
            "DO NOT SPEND A WEEKLY SLOT AUTOMATICALLY: literal >0.70 3-px overlap fires on "
            "saturated registry witnesses (pinned 100%-support dense surface = 1.0000, GEMS87 90.4%-halo "
            "continuous surface, and 13gems 99.87%-halo stride-5 calibration lattice) under the unmodified "
            "literal protocol rule; promotion to a live slot requires explicit selector/schema authorization."
        ),
    )

    (ROOT / "docs" / "evidence" / "h86c-kslb-run-card.json").write_text(
        json.dumps(run_card, indent=2, allow_nan=False) + "\n"
    )
    print(f"Completed Lane H86C-KSLB in {full_results['elapsed_s']}s | peak RSS {rss_mb} MB | SHA256={val_receipt['sha256']}", flush=True)
    return full_results


if __name__ == "__main__":
    main()
