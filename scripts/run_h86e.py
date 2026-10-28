#!/usr/bin/env python3
"""H86E lane: SPBT canary/holdout (E1-E2, negative) + catalogue-context LOQO (E3).

E1/E2 (pure signed paired-throw, H86E-SPBT) are implemented in build_spbt_surface()
and were run first; they falsified the pure polarity-concordance surface
(HOLDOUT-DTI below spaced random, SGMC proxy far below random).  E3 tests the
orthogonal signal that the earlier GFCO/KSLB lanes deliberately excluded
(plane_manifest catalogue_used=false): features derived from the *visible*
catalogue only (distance, tip distance, multi-scale fault-length density),
combined with label-free geophysics/topography and the SPBT channel, in a
leave-one-quadrant-out HistGradientBoosting model.  Every catalogue-derived
feature is recomputed from the visible mask of the buffered whole-component
draw, so withheld components cannot leak into training or features.

Shared tools are used unchanged: gems57.holdout.buffered_component_draw,
gems57.evaluate_holdout (gems57-pooled-hide-v2), gems57.emit.emit_decimated,
gems57.grid.write_submission / validate via gems57.validate.

Protocol note (SUPERSEDED — read this before citing IR-86-H86E-01): an earlier
revision of this script skipped protocol_preflight.require_feasible() on the
grounds that the owner's 2026-10-24 mandate ordered generation of a unique TIF
with fully automated validation, which the literal full-support stop makes
impossible for any nonempty candidate.  That bypass has been REVOKED.
``main()`` now calls ``require_feasible()`` as its first action, before argparse,
any grid load, feature construction, fitting or placement, and
``tests/test_builder_preflight.py`` pins that guard (an owner mandate to produce
a file is not a protocol exemption; AGENTS.md item 8).  Under the current
literal rule the call raises STOP_LITERAL_OVERLAP_UNSATISFIABLE, so this script
emits nothing.

The E1-E3 measurements and the H86E artifact already published were produced by
the earlier ungated revision and are preserved as a DO NOT SUBMIT audit record
(``docs/evidence/h86e-run-card.json``, G4/G5/G6 fail).  Uniqueness is reported
with the shared ``gems57.uniqueness.two_phase_summary`` -- BOTH the literal
reading (worst forward overlap ``1.0`` vs the pinned dense witness; ``0.9988``
vs the stride-5 lattice) and the like-for-like dot-field reading -- with
thresholds unchanged (``rho 0.90``, overlap ``0.70``).  No shared tool was forked
or edited and no weekly slot is authorized.  Recorded as IR-86-H86E-01 in
IRREGULARITIES.md (now marked SUPERSEDED, with this revocation stated) and
IR-86-PROSE-CODE-01 (the stale docstring that contradicted this guard).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))

from gems57 import grid as G  # noqa: E402
from gems57 import holdout as H  # noqa: E402
from gems57 import emit as E  # noqa: E402
from gems57 import evaluate_holdout as EH  # noqa: E402
from gems57 import metric as M  # noqa: E402

CACHE = ROOT / ".cache" / "h86e"
BUDGETS = (37654, 44090)
SEED = 20


# --------------------------------------------------------------------------- #
# SPBT surface (E1/E2)
# --------------------------------------------------------------------------- #
def _band(idx: int) -> np.ndarray:
    with rasterio.open(ROOT / "data/bridge/training_features.tif") as s:
        a = s.read(idx).astype(np.float32)
    a[a <= -1e38] = np.nan
    return a


def _zrobust(a: np.ndarray, fp: np.ndarray) -> np.ndarray:
    v = a[fp & np.isfinite(a)]
    lo, hi = np.percentile(v, [1, 99])
    med = float(np.median(v))
    iqr = float(np.percentile(v, 75) - np.percentile(v, 25)) + 1e-9
    a = np.clip(a, lo, hi)
    a[~np.isfinite(a)] = med
    return ((a - med) / iqr).astype(np.float32)


def build_spbt_surface(fp: np.ndarray) -> dict[str, np.ndarray]:
    """Signed paired-throw concordance: depth-to-basement step and isostatic
    gravity step across +/-200-400 m flanks must have opposite signs (deeper
    basement on the downthrown side is a gravity low), with >=900 m strike
    continuity (9 px strike smoothing), max over 8 strike azimuths.
    The anti-concordant product is the polarity-scrambled control."""
    depth = ndi.gaussian_filter(_zrobust(_band(15), fp), 1.2)
    grav = ndi.gaussian_filter(_zrobust(_band(13), fp), 1.2)
    slope = _band(19)

    def shift(a, dy, dx):
        return ndi.shift(a, (dy, dx), order=1, mode="nearest")

    def flank(a, py, px):
        pos = sum(shift(a, t * py, t * px) for t in (2.0, 3.0, 4.0)) / 3.0
        neg = sum(shift(a, -t * py, -t * px) for t in (2.0, 3.0, 4.0)) / 3.0
        return (pos - neg).astype(np.float32)

    def strike_smooth(a, sy, sx):
        return (sum(shift(a, t * sy, t * sx) for t in range(-4, 5)) / 9.0).astype(np.float32)

    conc = np.zeros(fp.shape, np.float32)
    anti = np.zeros(fp.shape, np.float32)
    for k in range(8):
        th = np.radians(k * 22.5)
        sx, sy = np.cos(th), -np.sin(th)
        px, py = np.sin(th), np.cos(th)
        ds, gs = flank(depth, py, px), flank(grav, py, px)
        conc = np.maximum(conc, strike_smooth(np.sqrt(np.clip(ds * -gs, 0, None)).astype(np.float32), sy, sx))
        anti = np.maximum(anti, strike_smooth(np.sqrt(np.clip(ds * gs, 0, None)).astype(np.float32), sy, sx))
    # muted-relief weight (rank of detrended-elevation slope inside footprint)
    sr = np.zeros(fp.shape, np.float32)
    vals = np.where(np.isfinite(slope), slope, np.nanmedian(slope[fp & np.isfinite(slope)]))[fp]
    order = np.argsort(vals, kind="stable")
    ranks = np.empty(order.size, np.float32)
    ranks[order] = np.linspace(0, 1, order.size, dtype=np.float32)
    sr[fp] = ranks
    spbt = (conc * (1.25 - 0.5 * sr)).astype(np.float32)
    for a in (conc, anti, spbt):
        a[~fp] = 0.0
    return dict(conc=conc, anti=anti, spbt=spbt)


# --------------------------------------------------------------------------- #
# E3 feature stack
# --------------------------------------------------------------------------- #
def _other_group_distance(mask: np.ndarray, comp: np.ndarray, group: np.ndarray) -> np.ndarray:
    """Distance to the nearest mask pixel belonging to a *different* component
    group.  Components are randomly split into two groups; for a pixel inside
    group A the distance to group B is an honest other-component distance
    (an upper bound on the true other-component distance), and for pixels
    outside the mask min(dA, dB) is the ordinary distance.  This removes the
    degenerate self-identity leak of the plain distance transform, whose
    value 0 exactly encodes the training label (positives *are* mask pixels):
    the first E3 run degenerated to p=1 on the catalogue and p~1e-6 elsewhere
    because HistGradientBoosting split on logdist==0."""
    d = np.full(mask.shape, 999.0, np.float32)
    dists = []
    for gv in (0, 1):
        m = mask & (group[comp] == gv)
        dists.append(ndi.distance_transform_edt(~m) if m.any() else np.full(mask.shape, 999.0))
    dA, dB = dists
    d = np.minimum(dA, dB).astype(np.float32)
    inside = mask
    gv_here = group[comp[inside]]
    d[inside] = np.where(gv_here == 0, dB[inside], dA[inside]).astype(np.float32)
    return d


def catalogue_context(catmask: np.ndarray, seed: int = 12345) -> list[np.ndarray]:
    """[log other-component dist, log other-group tip dist, self-corrected
    fault-length densities s10/s25/s50] from a catalogue mask.
    For holdout this is the *visible* mask only.  Densities subtract the
    analytic self-weight (1/(2*pi*sigma^2)) at catalogue pixels so a positive
    pixel does not count itself."""
    comp, ncomp = ndi.label(catmask, structure=np.ones((3, 3), int))
    rng = np.random.default_rng(seed)
    group = rng.integers(0, 2, size=ncomp + 1)
    group[0] = -1
    dist = _other_group_distance(catmask, comp, group)
    nbr = ndi.convolve(catmask.astype(np.int32), np.ones((3, 3), np.int32), mode="constant") - catmask
    tips = catmask & (nbr <= 1)
    tdist = _other_group_distance(tips, comp, group) if tips.any() else np.full(catmask.shape, 999.0, np.float32)
    cf = catmask.astype(np.float32)
    dens = []
    for s in (10, 25, 50):
        d = ndi.gaussian_filter(cf, s)
        d = d - cf * (1.0 / (2.0 * np.pi * s * s))
        dens.append(np.clip(d, 0, None).astype(np.float32))
    return [np.log1p(dist).astype(np.float32), np.log1p(tdist).astype(np.float32), *dens]


CTX_NAMES = ["ctx_logdist_other", "ctx_logtipdist_other", "ctx_dens10", "ctx_dens25", "ctx_dens50"]


def _fill(a: np.ndarray, fp: np.ndarray, nodata_vals=()) -> np.ndarray:
    a = a.astype(np.float32)
    bad = ~np.isfinite(a)
    for v in nodata_vals:
        bad |= a == v
    bad |= a <= -1e38
    med = float(np.median(a[fp & ~bad])) if (fp & ~bad).any() else 0.0
    a[bad] = med
    return a


def build_static_stack(g, spbt_conc: np.ndarray) -> tuple[np.memmap, list[str], np.ndarray]:
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = g.footprint
    flat_idx = np.flatnonzero(fp.ravel())
    names: list[str] = []
    feats: list[np.ndarray] = []

    def add(name, arr):
        names.append(name)
        feats.append(arr)

    grad_bands = {2: "rtp", 12: "det_elev", 13: "iso_grav", 14: "tmi", 15: "depth_base", 17: "cond"}
    from src.gems86.io import BANDS

    raw = {}
    for i in range(1, 20):
        a = _fill(_band(i), fp)
        raw[i] = a
        add(f"b{i}_{BANDS[i]}", a)
    for i, nm in grad_bands.items():
        gx = ndi.gaussian_filter1d(raw[i], 1.5, axis=1, order=1)
        gy = ndi.gaussian_filter1d(raw[i], 1.5, axis=0, order=1)
        add(f"grad_{nm}", np.hypot(gx, gy).astype(np.float32))

    ext_specs = [
        (".cache/external/lidar_scarp_features_u8.tif", [1, 3, 9, 10, 12], ["lid_ex_max", "lid_step_max", "lid_relief", "lid_coh100", "lid_valid"]),
        (".cache/external/topo_10m_derived_100m_u8.tif", [1, 5, 6, 8], ["topo_slope_p90", "topo_relief", "topo_curv", "topo_hs_lineament"]),
        (".cache/external/geodawn_rad_u8.tif", [1, 2, 3, 4], ["rad_K", "rad_Th", "rad_U", "rad_TC"]),
        (".cache/external/geodawn_extensions_u8.tif", [1, 2, 3, 4], ["rad_ThK", "rad_UK", "rad_UTh", "tmi_up150"]),
        (".cache/external/dem10_chi_100m_i16.tif", [1], ["chi_step_max"]),
    ]
    for path, bands, nms in ext_specs:
        with rasterio.open(ROOT / path) as s:
            for b, nm in zip(bands, nms):
                add(nm, _fill(s.read(b), fp, nodata_vals=(-32768,) if "chi" in nm else ()))
    add("spbt_conc", spbt_conc)

    n = len(feats)
    mm_path = CACHE / f"static_{n}.dat"
    mm = np.memmap(mm_path, dtype=np.float32, mode="w+", shape=(flat_idx.size, n))
    for j, a in enumerate(feats):
        mm[:, j] = a.ravel()[flat_idx]
    mm.flush()
    (CACHE / "static_names.json").write_text(json.dumps(names))
    return mm, names, flat_idx


def load_static_stack(g):
    """Reuse the cached static memmap when present (identical construction)."""
    names = json.loads((CACHE / "static_names.json").read_text())
    flat_idx = np.flatnonzero(g.footprint.ravel())
    mm = np.memmap(CACHE / f"static_{len(names)}.dat", dtype=np.float32,
                   mode="r", shape=(flat_idx.size, len(names)))
    return mm, names, flat_idx


# --------------------------------------------------------------------------- #
# E3 LOQO training + evaluation
# --------------------------------------------------------------------------- #
def _assemble(static_mm, ctx_arrays, flat_idx, rows):
    """rows = indices into footprint-row space."""
    cols = [np.asarray(static_mm[rows])]
    flat = flat_idx[rows]
    for a in ctx_arrays:
        cols.append(a.ravel()[flat][:, None].astype(np.float32))
    return np.hstack(cols).astype(np.float32)


def train_predict(static_mm, ctx_arrays, flat_idx, train_rows_pos, train_rows_neg,
                  predict_rows, seed=0):
    # Direct imported calls must stop before model or candidate work.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    from sklearn.ensemble import HistGradientBoostingClassifier

    X = np.vstack([
        _assemble(static_mm, ctx_arrays, flat_idx, train_rows_pos),
        _assemble(static_mm, ctx_arrays, flat_idx, train_rows_neg),
    ])
    y = np.r_[np.ones(len(train_rows_pos), np.int8), np.zeros(len(train_rows_neg), np.int8)]
    clf = HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.06, max_leaf_nodes=63,
        min_samples_leaf=40, l2_regularization=1.0, random_state=seed)
    clf.fit(X, y)
    out = np.empty(len(predict_rows), np.float32)
    for s in range(0, len(predict_rows), 200_000):
        r = predict_rows[s:s + 200_000]
        out[s:s + len(r)] = clf.predict_proba(_assemble(static_mm, ctx_arrays, flat_idx, r))[:, 1]
    return out, clf


def rankpct(a, fp):
    out = np.zeros(a.shape, np.float32)
    v = a[fp]
    o = np.argsort(v, kind="stable")
    r = np.empty(o.size, np.float32)
    r[o] = np.linspace(0, 1, o.size, dtype=np.float32)
    out[fp] = r
    return out


def emit_from(surface, allowed, budget):
    ranked, _ = E.emit_decimated(surface.astype(np.float32), allowed, tile_px=3)
    return E.emit_prefix(ranked, budget), ranked


def holdout_eval(arms_masks: dict, folds, fp, candidate: str):
    terms, per = {}, {}
    for name, mask in arms_masks.items():
        pred = mask.astype(np.float32)
        tt, rr = [], []
        for f in folds:
            res, tf = EH.evaluate(pred, f, fp, block_side=200)
            tt.append(tf)
            rr.append({k: float(res[k]) for k in ("dti", "tp", "fp", "fn", "n_truth", "n_emitted", "coverage")})
        terms[name] = np.sum(tt, axis=0)
        per[name] = rr
    pooled = EH.pooled_summary(terms, draws=1000, seed=1, candidate=candidate)
    return pooled, per


def main():
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    t0 = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    g = G.load_grid()
    fp, cat = g.footprint, g.catalogue
    folds, quad = H.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)
    visible = folds[0]["visible"]
    hidden = folds[0]["hidden_all"]
    masked_known = folds[0]["masked_known"]
    print(f"hidden={int(hidden.sum())} visible={int(visible.sum())}", flush=True)

    # ---- E1/E2 SPBT ----
    sp = build_spbt_surface(fp)
    np.save(CACHE / "conc.npy", sp["conc"])
    dvis = ndi.distance_transform_edt(~visible)
    allowed_vis = fp & (dvis > 2.0)
    rng = np.random.default_rng(7)
    rand_surf = rng.random(fp.shape, dtype=np.float32)
    rand_surf[~fp] = 0
    arms = {}
    for name, surf in [("spbt_weighted", sp["spbt"]), ("conc_unweighted", sp["conc"]),
                       ("anti_control", sp["anti"]), ("spaced_random", rand_surf),
                       ("neg_dist_visible", rankpct((-dvis).astype(np.float32), fp))]:
        arms[name], _ = emit_from(surf if name in ("spaced_random", "neg_dist_visible") else rankpct(surf, fp),
                                  allowed_vis, BUDGETS[0])

    def loadmask(p):
        with rasterio.open(p) as s:
            a = s.read(1)
        return np.isfinite(a) & (a > 0)

    arms["fixed_d28_leaked_ref"] = loadmask(ROOT / "data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
    pooled_e2, per_e2 = holdout_eval(arms, folds, fp, "conc_unweighted")
    print("E2 pooled:", {k: round(v["dti"], 4) for k, v in pooled_e2["scores"].items()}, flush=True)

    # ---- canaries (all E3 features, seed-20 hidden vs sampled negatives) ----
    if (CACHE / "static_names.json").exists():
        static_mm, static_names, flat_idx = load_static_stack(g)
        print("reused cached static stack", flush=True)
    else:
        static_mm, static_names, flat_idx = build_static_stack(g, sp["conc"])
    ctx_vis = catalogue_context(visible)
    ctx_full = catalogue_context(cat)
    for j, a in enumerate(ctx_vis):
        np.save(CACHE / f"ctx_vis_{j}.npy", a)
    for j, a in enumerate(ctx_full):
        np.save(CACHE / f"ctx_full_{j}.npy", a)
    feat_names = static_names + CTX_NAMES

    row_of_flat = -np.ones(fp.size, np.int64)
    row_of_flat[flat_idx] = np.arange(flat_idx.size)
    region = np.any(np.stack([f["region"] for f in folds]), axis=0)
    pos_flat = np.flatnonzero((hidden & region).ravel())
    neg_flat_all = np.flatnonzero((region & ~masked_known & ~hidden & fp).ravel())
    neg_flat = rng.choice(neg_flat_all, size=300_000, replace=False)
    pos_rows, neg_rows = row_of_flat[pos_flat], row_of_flat[neg_flat]
    from sklearn.metrics import roc_auc_score

    Xc = _assemble(static_mm, ctx_vis, flat_idx, np.r_[pos_rows, neg_rows])
    yc = np.r_[np.ones(len(pos_rows)), np.zeros(len(neg_rows))]
    canary = {}
    for j, nm in enumerate(feat_names):
        s = Xc[:, j].astype(float)
        s[~np.isfinite(s)] = np.nanmedian(s[np.isfinite(s)])
        canary[nm] = float(roc_auc_score(yc, s)) if np.ptp(s) > 0 else 0.5
    max_canary = max(max(v, 1 - v) for v in canary.values())
    print(f"canary max discriminative AUC={max_canary:.4f}", flush=True)

    # ---- E3 LOQO ----
    quad_row = quad.ravel()[flat_idx]
    cat_row = cat.ravel()[flat_idx]
    vis_row = visible.ravel()[flat_idx]
    dcat_full = ndi.distance_transform_edt(~cat)
    neg_ok_row = (dcat_full.ravel()[flat_idx] > 1.0)
    oof = np.zeros(flat_idx.size, np.float32)
    fold_info = {}
    for q in range(4):
        tr_pos = np.flatnonzero(vis_row & (quad_row != q) & (quad_row >= 0))
        tr_neg_pool = np.flatnonzero(~cat_row & neg_ok_row & (quad_row != q) & (quad_row >= 0))
        tr_neg = rng.choice(tr_neg_pool, size=160_000, replace=False)
        te = np.flatnonzero(quad_row == q)
        pred, _ = train_predict(static_mm, ctx_vis, flat_idx, tr_pos, tr_neg, te, seed=q)
        oof[te] = pred
        fold_info[str(q)] = dict(n_pos=int(len(tr_pos)), n_neg=int(len(tr_neg)), n_test=int(len(te)))
        print(f"LOQO fold {q} done t={time.time()-t0:.0f}s", flush=True)
    # rows outside any quadrant (should be none inside footprint) stay 0
    oof_grid = np.zeros(fp.shape, np.float32)
    oof_grid.ravel()[flat_idx] = oof
    np.save(CACHE / "oof.npy", oof_grid)

    arms3 = {"spaced_random": arms["spaced_random"], "neg_dist_visible": arms["neg_dist_visible"],
             "conc_unweighted": arms["conc_unweighted"], "fixed_d28_leaked_ref": arms["fixed_d28_leaked_ref"]}
    for b in BUDGETS:
        # model probabilities are used directly (not rank-transformed): the
        # shared emitter's expected-credit convolution expects a probability.
        arms3[f"cctv_oof_{b}"], _ = emit_from(np.sqrt(np.clip(oof_grid, 0, 1)), allowed_vis, b)
    pooled_e3, per_e3 = holdout_eval(arms3, folds, fp, f"cctv_oof_{BUDGETS[1]}")
    print("E3 pooled:", {k: round(v["dti"], 4) for k, v in pooled_e3["scores"].items()}, flush=True)

    # ---- SGMC auxiliary proxy (never a score) ----
    with rasterio.open(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif") as s:
        sgmc = s.read(1) > 0
    truth_sg = sgmc & fp & ~cat
    sg = {}
    for name in ["cctv_oof_37654", "cctv_oof_44090", "spaced_random", "conc_unweighted"]:
        # re-emit pipeline arms against full-catalogue B2 for a final-style proxy reading
        allow_full = fp & (dcat_full > 2.0)
        surf = {"cctv_oof_37654": np.sqrt(np.clip(oof_grid, 0, 1)), "cctv_oof_44090": np.sqrt(np.clip(oof_grid, 0, 1)),
                "spaced_random": rand_surf, "conc_unweighted": rankpct(sp["conc"], fp)}[name]
        b = 44090 if name.endswith("44090") else 37654
        m, _ = emit_from(surf, allow_full, b)
        sg[name] = {k: float(v) for k, v in M.dti_exact(m.astype(np.float32), truth_sg, valid=fp, known=cat).items()}
    for name, p in [("fixed_h33_b2", ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")]:
        sg[name] = {k: float(v) for k, v in M.dti_exact(loadmask(p).astype(np.float32), truth_sg, valid=fp, known=cat).items()}
    print("SGMC:", {k: round(v["dti"], 4) for k, v in sg.items()}, flush=True)

    # ---- final full-catalogue model ----
    all_pos = np.flatnonzero(cat_row)
    all_neg_pool = np.flatnonzero(~cat_row & neg_ok_row)
    all_neg = rng.choice(all_neg_pool, size=250_000, replace=False)
    all_rows = np.arange(flat_idx.size)
    final_pred, _ = train_predict(static_mm, ctx_full, flat_idx, all_pos, all_neg, all_rows, seed=99)
    final_grid = np.zeros(fp.shape, np.float32)
    final_grid.ravel()[flat_idx] = final_pred
    np.save(CACHE / "final_surface.npy", final_grid)
    print(f"final model done t={time.time()-t0:.0f}s", flush=True)

    out = dict(
        evaluator_version=EH.VERSION, seed=SEED,
        withheld_positive_pixels=int(hidden.sum()),
        fold_receipts=[f["receipt"] for f in folds],
        canary_auc=canary, canary_max_discriminative=float(max_canary),
        e2_pooled=pooled_e2, e2_per_fold=per_e2,
        e3_pooled=pooled_e3, e3_per_fold=per_e3,
        e3_loqo_folds=fold_info, feature_names=feat_names,
        sgmc_auxiliary_proxy=sg,
        sgmc_truth_pixels=int(truth_sg.sum()),
        elapsed_s=float(time.time() - t0),
    )
    (CACHE / "h86e_results.json").write_text(json.dumps(out, indent=1, default=str))
    print("WROTE", CACHE / "h86e_results.json")


if __name__ == "__main__":
    main()
