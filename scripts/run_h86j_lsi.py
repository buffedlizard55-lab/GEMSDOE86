#!/usr/bin/env python3
"""Run the preregistered H86J-LSI lane (live-score inversion).

Preregistration (frozen before any lane field, commit 5259f66):
research/H86J_LSI_PREREGISTRATION.md (+ .json).

Stages
  fetch   restore (hash-verified) the registry rasters that carry an owner score
  e1      measurement set + operators, leakage canary, as-is instrument baselines
  e2      all-data fit + leave-one-site-out instrument validation
  e3      candidate field, emission, gates, fail-closed writer, run card
  all     e1 -> e3

Evidence labels: HOLDOUT-DTI (gems57-pooled-hide-v2), SGMC-PROXY-DTI (selection
instrument only), LSI-PROJECTION (a MODEL number, never a score),
OWNER-REPORTED (prior_scores.csv; no organizer receipt).  No weekly slot is
picked here.
"""
from __future__ import annotations

import argparse
import csv
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

from gems57 import evaluate_holdout as EH, grid, holdout  # noqa: E402
from gems57 import submission_writer, validate  # noqa: E402
from gems86_edti import features as EDTI_F, model as EDTI_M  # noqa: E402
from gems86_lsi import lsi  # noqa: E402
from scripts.protocol_preflight import require_like_for_like  # noqa: E402

SEED = 20
SAMPLE_SEED = 861025
SAMPLE_FRAC = 0.25
RIDGE = 1e-3
BUDGETS = (30_000, 37_654, 44_090, 55_000)
PREREG = (ROOT / "research/H86J_LSI_PREREGISTRATION.md",
          ROOT / "research/H86J_LSI_PREREGISTRATION.json")
FEATURE_TIF = ROOT / "data/bridge/training_features.tif"
EXT_DIR = ROOT / ".cache/external"
STACK_PATH = ROOT / ".cache/work_h86g/features.f32"     # shared H86G stack (68 bands)
NAMES_PATH = ROOT / ".cache/work_h86g/feature_names.json"
SGMC_TIF = EXT_DIR / "derived_sgmc_faults_100m_u8.tif"
SGMC_SHA = "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"
LIDAR_TIF = EXT_DIR / "lidar_scarp_features_u8.tif"
LIDAR_SHA = "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568"
import os
WORK = Path(os.environ.get("H86J_WORK", ROOT / "data/work/h86j"))
EV = ROOT / "docs/evidence"
OUT_DIR = ROOT / "docs/downloads"
REG_DIR = ROOT / "data/registry_ext"
INVENTORY = ROOT / "research/upstream/registry_inventory.json"
SCORES = ROOT / "registry/prior_scores.csv"
H33 = ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
H86G = OUT_DIR / "gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.tif"
H86G_SHA = "ba8b731fead02eb27ab30c1d2c2add78f3f703325a3b29316cdfdc3183489e8d"


def log(*a):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}]", *a, flush=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as s:
        for c in iter(lambda: s.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def read1(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        if (src.height, src.width) != (3730, 3292):
            raise ValueError(f"off-grid raster {path.name}: {src.height}x{src.width}")
        return src.read(1)


def get_grid_folds():
    g = grid.load_grid(ROOT / "data/bridge")
    folds, _ = holdout.buffered_component_draw(g, seed=SEED, hide_frac=0.20, buffer_px=3)
    return g, folds


def get_stack(g):
    if STACK_PATH.is_file() and NAMES_PATH.is_file():
        names = json.loads(NAMES_PATH.read_text())
        return EDTI_F.load_stack(STACK_PATH, len(names), g.shape), names
    log("building shared H86G feature stack (pinned layers only)")
    _, names = EDTI_F.build_stack(FEATURE_TIF, EXT_DIR, g.footprint, STACK_PATH)
    NAMES_PATH.write_text(json.dumps(names, indent=1))
    return EDTI_F.load_stack(STACK_PATH, len(names), g.shape), names


def lidar_valid(g) -> np.ndarray:
    if sha256(LIDAR_TIF) != LIDAR_SHA:
        raise RuntimeError("lidar raster hash drift")
    with rasterio.open(LIDAR_TIF) as ds:
        i = list(ds.descriptions).index("valid") + 1
        return ds.read(i).astype(np.float32) / 255.0


def sgmc_truth(g):
    if sha256(SGMC_TIF) != SGMC_SHA:
        raise RuntimeError("SGMC proxy raster hash drift")
    with rasterio.open(SGMC_TIF) as ds:
        sg = (ds.read(1) > 0) & g.footprint
    dcat = ndi.distance_transform_edt(~g.catalogue)
    return sg & (dcat > 3.0)


# ---------------------------------------------------------------- measurement set
def _norm(stem: str) -> str:
    return stem.split("__", 1)[1] if "__" in stem else stem


def candidate_files():
    """name-stem -> list of (path, provenance) over every restored raster."""
    out: dict[str, list] = {}
    for d in (ROOT / "data/scored_fleet", ROOT / "data/scored"):
        for p in sorted(d.glob("*.tif")):
            out.setdefault(_norm(p.stem), []).append((p, f"local:{p.relative_to(ROOT)}"))
    inv = json.loads(INVENTORY.read_text())["rasters"]
    for rec in inv:
        p = REG_DIR / f"{rec['sha256']}.tif"
        if not p.is_file():
            continue
        for src in rec["sources"]:
            stem = src.split(":", 1)[1].rsplit("/", 1)[-1].rsplit(".", 1)[0]
            out.setdefault(stem, []).append((p, f"registry:{src}"))
    return out


def _matches(sub: str, stem: str) -> bool:
    return sub in stem or (stem in sub and len(stem) >= 0.8 * len(sub))


def score_rows():
    rows = []
    for r in csv.DictReader(SCORES.open()):
        s = (r.get("score") or "").strip()
        sub = (r.get("submission") or "").strip()
        if not s or not sub:
            continue
        try:
            rows.append({"site": r["site"].strip(), "submission": sub, "score": float(s),
                         "evidence_class": "OWNER-REPORTED", "source_url": r.get("source_url", "")})
        except ValueError:
            continue
    return rows


def registry_records_for_scores():
    inv = json.loads(INVENTORY.read_text())
    recs = []
    for r in score_rows():
        for rec in inv["rasters"]:
            for src in rec["sources"]:
                stem = src.split(":", 1)[1].rsplit("/", 1)[-1].rsplit(".", 1)[0]
                if _matches(r["submission"], stem):
                    recs.append(rec)
                    break
    uniq = {rec["sha256"]: rec for rec in recs}
    return inv["owner"], list(uniq.values())


def stage_fetch():
    from scripts.restore_registry_inventory import fetch_one   # shared tool, not forked
    owner, recs = registry_records_for_scores()
    REG_DIR.mkdir(parents=True, exist_ok=True)
    ok, err = 0, []
    for rec in recs:
        try:
            fetch_one(rec, REG_DIR, owner)
            ok += 1
        except Exception as exc:   # visible, never silently skipped
            err.append({"sha256": rec["sha256"], "sources": rec["sources"], "error": repr(exc)[:200]})
    log(f"scored-registry fetch: {ok}/{len(recs)} verified, {len(err)} errors")
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "fetch_receipt.json").write_text(json.dumps(
        {"requested": len(recs), "verified": ok, "errors": err}, indent=1))


def build_measurements(g):
    fp, cat = g.footprint, g.catalogue
    files = candidate_files()
    groups: dict[str, dict] = {}      # decoded-hash -> merged measurement
    excluded = []
    for r in score_rows():
        hits = {}
        for stem, lst in files.items():
            if _matches(r["submission"], stem):
                for p, prov in lst:
                    hits.setdefault(str(p), (p, prov))
        if not hits:
            excluded.append({**r, "reason": "no restored raster matches the name"})
            continue
        decoded = {}
        for key, (p, prov) in hits.items():
            try:
                v, info = lsi.decode(read1(p), fp, cat)
            except ValueError as exc:
                excluded.append({**r, "reason": f"unreadable/off-grid: {exc}"})
                decoded = {}
                break
            dh = hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest()
            decoded.setdefault(dh, (p, info, []))[2].append(prov)
            del v
        if not decoded:
            continue
        if len(decoded) > 1:
            excluded.append({**r, "reason": f"ambiguous: {len(decoded)} distinct decoded arrays",
                             "provenance": sorted({x for d in decoded.values() for x in d[2]})})
            continue
        dh, (p0, info, prov) = next(iter(decoded.items()))
        m = groups.setdefault(dh, {"decoded_sha256": dh, "rows": [], "info": info,
                                   "provenance": sorted(set(prov)), "_path": p0})
        m["rows"].append(r)
    meas = []
    for dh, m in groups.items():
        scores = [x["score"] for x in m["rows"]]
        meas.append({"decoded_sha256": dh, "score": float(np.mean(scores)),
                     "score_spread": float(np.ptp(scores)),
                     "site": m["rows"][0]["site"],
                     "submissions": [x["submission"] for x in m["rows"]],
                     "provenance": m["provenance"], "info": m["info"], "_path": m["_path"]})
    meas.sort(key=lambda x: (x["site"], x["submissions"][0]))
    return meas, excluded


def features_at(stack, names, fp, lv, cat_in_force, idx):
    cols = []
    for name, plane in lsi.feature_planes(stack, names, fp, lv, cat_in_force):
        cols.append(plane.ravel()[idx].astype(np.float64))
    return np.stack(cols, axis=1)


def feature_full(stack, names, fp, lv, cat_in_force):
    for name, plane in lsi.feature_planes(stack, names, fp, lv, cat_in_force):
        yield name, plane


# ---------------------------------------------------------------- E1
def stage_e1(g, folds, stack, names):
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / "e1.json"
    if out.is_file() and (WORK / "e1_ops.npz").is_file():
        return json.loads(out.read_text())
    fp, cat = g.footprint, g.catalogue
    active = fp & ~cat
    lv = lidar_valid(g)
    meas, excluded = build_measurements(g)
    log(f"measurement set: {len(meas)} distinct scored rasters; {len(excluded)} rows excluded")
    sample = lsi.sample_pixels(active, SAMPLE_FRAC, SAMPLE_SEED)
    rows, n = [], []
    sg_off = sgmc_truth(g)
    sg_fold = dict(fold=0, name="SGMC_PROXY", region=fp, truth=sg_off, visible=cat,
                   masked_known=cat, hidden_all=sg_off)
    cache_path = WORK / "per_raster_instrument_cache.json"
    cache = json.loads(cache_path.read_text()) if cache_path.is_file() else {}
    for i, m in enumerate(meas):
        v = lsi.decode(read1(m["_path"]), fp, cat)[0]
        rows.append(lsi.raster_operator_rows(v, sample))
        n.append(float(v[active].sum(dtype=np.float64)))
        hit = cache.get(m["decoded_sha256"])
        if hit is None:
            res, _ = EH.evaluate(v, sg_fold, fp, block_side=200)
            tot = np.zeros(4)
            for f in folds:
                _, bt = EH.evaluate(v, f, fp, block_side=200)
                tot += bt.sum(axis=0)
            hit = {"sgmc_proxy_as_is": res["dti"],
                   "catalogue_hide_as_is": float(EH.from_terms(tot))}
            cache[m["decoded_sha256"]] = hit
            cache_path.write_text(json.dumps(cache, indent=1))
        m.update(hit)
        log(f"[{i+1}/{len(meas)}] {m['site']} {m['submissions'][0][:48]} live={m['score']:.4f} "
            f"sgmc={m['sgmc_proxy_as_is']:.4f} cathide={m['catalogue_hide_as_is']:.4f}")
    F = features_at(stack, names, fp, lv, cat, sample)
    # leakage canary: each feature alone, catalogue-hide folds, visible-catalogue shells
    region = np.zeros(fp.shape, bool)
    hidden = np.zeros(fp.shape, bool)
    known = np.zeros(fp.shape, bool)
    for f in folds:
        region |= np.asarray(f["region"], bool)
        hidden |= np.asarray(f["hidden_all"], bool)
        known |= np.asarray(f["masked_known"], bool)
    visible = np.asarray(folds[0]["visible"], bool)
    act_h = region & fp & ~known
    truth = act_h & hidden
    pos = np.flatnonzero(truth.ravel())
    neg_all = np.flatnonzero((act_h & ~truth).ravel())
    rng = np.random.default_rng(SAMPLE_SEED)
    neg = rng.choice(neg_all, size=min(300_000, neg_all.size), replace=False)
    y = np.r_[np.ones(pos.size), np.zeros(neg.size)]
    canaries = {}
    for name, plane in feature_full(stack, names, fp, lv, visible):
        s = np.r_[plane.ravel()[pos], plane.ravel()[neg]].astype(np.float64)
        auc = float(roc_auc_score(y, s)) if np.ptp(s) else 0.5
        canaries[name] = {"evidence_class": "LEAKAGE-CANARY", "auc": auc,
                          "discriminative_auc": max(auc, 1 - auc), "threshold": 0.90,
                          "leakage_flag": bool(max(auc, 1 - auc) > 0.90)}
        log(f"canary {name}: AUC={auc:.4f}")
    ops = lsi.assemble(rows, n, sample.size, sample.size / active.sum())
    np.savez(WORK / "e1_ops.npz", C_data=ops.C.data, C_ind=ops.C.indices, C_ptr=ops.C.indptr,
             S_data=ops.S.data, S_ind=ops.S.indices, S_ptr=ops.S.indptr, n=ops.n,
             frac=ops.frac, F=F, n_sample=sample.size)
    live = np.array([m["score"] for m in meas])
    doc = {
        "measurements": [{k: v for k, v in m.items() if k != "_path"} for m in meas],
        "excluded_rows": excluded,
        "n_measurements": len(meas),
        "sample": {"fraction": SAMPLE_FRAC, "seed": SAMPLE_SEED, "pixels": int(sample.size),
                   "active_pixels": int(active.sum())},
        "canaries": canaries,
        "withheld_positive_pixels": int(pos.size),
        "baseline_spearman_vs_live": {
            "sgmc_proxy_as_is": float(spearmanr([m["sgmc_proxy_as_is"] for m in meas], live).statistic),
            "catalogue_hide_as_is": float(spearmanr([m["catalogue_hide_as_is"] for m in meas], live).statistic),
        },
    }
    out.write_text(json.dumps(doc, indent=1))
    return doc


def load_ops():
    from scipy import sparse
    z = np.load(WORK / "e1_ops.npz")
    ns = int(z["n_sample"])
    C = sparse.csr_matrix((z["C_data"], z["C_ind"], z["C_ptr"]), shape=(len(z["n"]), ns))
    S = sparse.csr_matrix((z["S_data"], z["S_ind"], z["S_ptr"]), shape=(len(z["n"]), ns))
    return lsi.Operators(C=C, S=S, n=z["n"], frac=float(z["frac"])), z["F"]


# ---------------------------------------------------------------- E2
def stage_e2(e1):
    out = WORK / "e2.json"
    if out.is_file():
        return json.loads(out.read_text())
    ops, F = load_ops()
    st = lsi.Standardiser(F.mean(axis=0), F.std(axis=0) + 1e-9)
    X = lsi.design(st(F))
    meas = e1["measurements"]
    y = np.array([m["score"] for m in meas])
    w = np.ones_like(y)
    sites = np.array([m["site"] for m in meas])
    theta, info = lsi.fit(X, ops, y, w, ridge=RIDGE)
    pred_all, terms = lsi.predict_terms(theta, X, ops)
    th_c, info_c = lsi.fit_constant(X, ops, y, w)
    log(f"all-data fit: {info} in-sample rho={spearmanr(pred_all, y).statistic:.3f} "
        f"G={terms['G']:.0f}")
    loso, loso_c, thetas = np.zeros_like(y), np.zeros_like(y), {}
    for s in np.unique(sites):
        tr = np.flatnonzero(sites != s)
        te = np.flatnonzero(sites == s)
        th, _ = lsi.fit(X, ops, y, w, ridge=RIDGE, rows=tr, theta0=theta.copy())
        thetas[str(s)] = th.tolist()
        loso[te] = lsi.predict_terms(th, X, ops, rows=te)[0]
        thc, _ = lsi.fit(X[:, :1], ops, y, w, ridge=0.0, rows=tr, theta0=th_c.copy())
        loso_c[te] = lsi.predict_terms(thc, X[:, :1], ops, rows=te)[0]
    rho = float(spearmanr(loso, y).statistic)
    rho_c = float(spearmanr(loso_c, y).statistic)
    sg = np.array([m["sgmc_proxy_as_is"] for m in meas])
    rho_sg = float(spearmanr(sg, y).statistic)
    top = y >= 0.2
    doc = {
        "evidence_class": "LSI instrument validation (leave-one-site-out); predictions are MODEL numbers",
        "theta_all": theta.tolist(), "fit_info": info,
        "feature_names": ["intercept"] + list(lsi.FEATURE_NAMES),
        "standardiser": {"mu": st.mu.tolist(), "sd": st.sd.tolist()},
        "implied_hidden_truth_pixels_G": float(terms["G"]),
        "in_sample_spearman": float(spearmanr(pred_all, y).statistic),
        "in_sample_mae": float(np.mean(np.abs(pred_all - y))),
        "loso_spearman": rho, "loso_mae": float(np.mean(np.abs(loso - y))),
        "loso_spearman_constant_model": rho_c,
        "loso_mae_constant_model": float(np.mean(np.abs(loso_c - y))),
        "sgmc_proxy_spearman_same_set": rho_sg,
        "loso_spearman_top_cluster_ge_0p20": float(spearmanr(loso[top], y[top]).statistic) if top.sum() > 3 else None,
        "sgmc_spearman_top_cluster_ge_0p20": float(spearmanr(sg[top], y[top]).statistic) if top.sum() > 3 else None,
        "n_top_cluster": int(top.sum()),
        "per_raster": [{"site": m["site"], "submission": m["submissions"][0], "live": float(yy),
                        "loso_pred": float(p), "in_sample_pred": float(q), "sgmc": float(sv)}
                       for m, yy, p, q, sv in zip(meas, y, loso, pred_all, sg)],
        "loso_thetas": thetas,
        "gate_instrument": bool(rho >= 0.60 and rho > rho_c and rho >= rho_sg),
    }
    log(f"LOSO rho={rho:.3f} (const {rho_c:.3f}, sgmc {rho_sg:.3f}) gate={doc['gate_instrument']}")
    out.write_text(json.dumps(doc, indent=1))
    return doc


# ---------------------------------------------------------------- E3
def lam_field(theta, st, stack, names, fp, lv, cat_in_force):
    active = fp & ~cat_in_force
    eta = np.full(fp.shape, theta[0], np.float64)
    for j, (name, plane) in enumerate(feature_full(stack, names, fp, lv, cat_in_force)):
        eta += theta[j + 1] * (plane.astype(np.float64) - st.mu[j]) / st.sd[j]
    lam = np.exp(np.clip(eta, -50, 5)).astype(np.float32)
    lam[~active] = 0.0
    return lam


def uniqueness_report(surface, dots, fp, files, allowed=None):
    allowed = fp if allowed is None else allowed
    rng = np.random.default_rng(SAMPLE_SEED)
    fp_idx = np.flatnonzero(fp.ravel())
    sample = rng.choice(fp_idx, size=min(200_000, fp_idx.size), replace=False)
    my_s = surface.ravel()[sample].astype(np.float64)
    from gems57.uniqueness import representation_class
    dots_yx = np.nonzero(dots)
    rows = []
    for path in files:
        off_grid = None
        try:
            a = read1(path)
        except ValueError as exc:
            # Off-grid registry row (same shape, shifted transform): the portal scores
            # pixel arrays, so compare it index-wise and record that we did (never skip).
            with rasterio.open(path) as src:
                if (src.height, src.width) != fp.shape:
                    rows.append({"file": str(path.relative_to(ROOT)), "error": str(exc)})
                    continue
                a = src.read(1).astype(np.float32)
            off_grid = str(exc)
        theirs = np.isfinite(a) & (a > 0)
        their_s = np.where(np.isfinite(a), a, 0).ravel()[sample].astype(np.float64)
        rho = float(spearmanr(my_s, their_s).statistic) if np.ptp(their_s) else 0.0
        rho_d = float(spearmanr(dots.ravel()[sample].astype(np.float64), their_s).statistic) \
            if np.ptp(their_s) and dots.ravel()[sample].any() else 0.0
        fwd = within_3px_fraction(dots_yx, theirs) if (theirs.any() and len(dots_yx[0])) else 0.0
        rep = representation_class(int(theirs.sum()), int(fp.sum()))
        is_dot = rep["kind"] == "dot_field"
        # PA-86-02 (same rule as scripts/pa86_chance_overlap.py): a firing against a
        # raster whose own 3 px halo covers > 70 % of the allowed domain is expected for
        # ANY random dot set (space-filling) and falls back to the rank test.
        halo_cov = None
        if is_dot and fwd > 0.70:
            from gems57.uniqueness import _near
            halo_cov = float(_near(theirs & fp)[allowed].mean())
        rows.append({"file": str(path.relative_to(ROOT)), "sha256": sha256(path),
                     "their_positive": int(theirs.sum()), "representation": rep["kind"],
                     "spearman_surface_sample": rho, "spearman_dots_sample": rho_d,
                     "my_dots_within_3px_of_theirs": fwd,
                     "byte_identical_dots": bool(np.array_equal(theirs & fp, dots & fp)),
                     "rho_firing": bool(max(rho, rho_d) > 0.90),
                     "off_grid_compared_index_wise": off_grid,
                     "halo_coverage_allowed": halo_cov,
                     "space_filling_chance_level": bool(halo_cov is not None and halo_cov > 0.70),
                     "overlap_firing": bool(is_dot and fwd > 0.70
                                            and not (halo_cov is not None and halo_cov > 0.70)),
                     "literal_overlap_firing_incl_continuous": bool(fwd > 0.70)})
    ok = [r for r in rows if "error" not in r]
    return {
        "thresholds": {"rho_max": 0.90, "dot_overlap_3px_max": 0.70},
        "compared": len(ok), "errors": [r for r in rows if "error" in r],
        "max_spearman": max((max(r["spearman_surface_sample"], r["spearman_dots_sample"]) for r in ok), default=0.0),
        "max_forward_3px_overlap_dot_fields": max(
            (r["my_dots_within_3px_of_theirs"] for r in ok if r["representation"] == "dot_field"), default=0.0),
        "max_forward_3px_overlap_literal_incl_continuous": max(
            (r["my_dots_within_3px_of_theirs"] for r in ok), default=0.0),
        "rho_firings": int(sum(r["rho_firing"] for r in ok)),
        "overlap_firings": int(sum(r["overlap_firing"] for r in ok)),
        "literal_overlap_firings_incl_continuous": int(sum(r["literal_overlap_firing_incl_continuous"] for r in ok)),
        "any_byte_identical": bool(any(r["byte_identical_dots"] for r in ok)),
        "gate_pass": bool(ok) and not [r for r in rows if "error" in r] and not any(r["rho_firing"] or r["overlap_firing"] or r["byte_identical_dots"] for r in ok),
        "rows": rows,
    }


_OFF3 = [(j, i) for j in range(-3, 4) for i in range(-3, 4) if j * j + i * i <= 9]


def within_3px_fraction(dots_yx, theirs: np.ndarray) -> float:
    """Fraction of my dots with at least one of their positives at Euclidean
    distance <= 3 px (exact lattice neighbourhood; equals EDT(~theirs) <= 3)."""
    ys, xs = dots_yx
    H, W = theirs.shape
    hit = np.zeros(len(ys), bool)
    for j, i in _OFF3:
        yy, xx = ys + j, xs + i
        ok = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < W)
        hit[ok] |= theirs[yy[ok], xx[ok]]
    return float(hit.mean())


def registry_files(exclude: set[Path] = frozenset()):
    files = sorted(REG_DIR.glob("*.tif")) + sorted((ROOT / "data/scored_fleet").glob("*.tif")) \
        + sorted((ROOT / "data/scored").glob("*.tif")) + sorted(OUT_DIR.glob("*.tif")) \
        + sorted((ROOT / "submission").glob("*.tif"))
    seen, out = set(), []
    for p in files:
        if p in exclude:
            continue
        try:
            h = sha256(p)
        except OSError:
            continue
        if h not in seen:
            seen.add(h)
            out.append(p)
    return out


def stage_e3(g, folds, stack, names, e1, e2, preflight, started):
    fp, cat = g.footprint, g.catalogue
    active = fp & ~cat
    lv = lidar_valid(g)
    st = lsi.Standardiser(np.array(e2["standardiser"]["mu"]), np.array(e2["standardiser"]["sd"]))
    theta = np.array(e2["theta_all"])
    lam = lam_field(theta, st, stack, names, fp, lv, cat)
    log(f"lambda field: sum={lam.sum():.0f} max={lam.max():.4f}")
    ek = lsi.sum_credit(lam)
    dcat = ndi.distance_transform_edt(~cat)
    WORK.mkdir(parents=True, exist_ok=True)
    rpath = WORK / "ranked_full.npy"
    if rpath.is_file():
        ranked = np.load(rpath)
    else:
        ranked = EDTI_M.spacing_greedy_ranking(ek, fp & (dcat > 3.0), min_spacing_px=2.8)
        np.save(rpath, ranked)

    # surface-level uniqueness BEFORE placement (protocol item 1)
    reg = registry_files()
    log(f"surface uniqueness vs {len(reg)} registry rasters (pre-placement)")
    surf_uniq = uniqueness_report(ek, np.zeros(fp.shape, bool), fp, reg, fp & ~cat)
    (EV / "h86j-lsi-registry-surface.json").write_text(json.dumps(surf_uniq, indent=1))
    if surf_uniq["rho_firings"]:
        raise SystemExit("surface drifted into another lane (rho > 0.90): logged as duplicate, stop")

    # budget: argmax LSI-predicted DTI (all-data fit), exact full-field operators
    curve = {}
    for b in BUDGETS:
        dots_b = EDTI_M.prefix(ranked, b)
        curve[str(b)] = lsi.expected_dti_of(dots_b.astype(np.float32), lam, active)
        log(f"budget {b}: LSI-PROJECTION={curve[str(b)]['lsi_projection']:.4f}")
    budget = int(max(curve, key=lambda k: curve[k]["lsi_projection"]))
    dots = EDTI_M.prefix(ranked, budget)

    # LSI-PROJECTION robustness across LOSO refits (candidate vs H33 vs H86G)
    h33 = lsi.decode(read1(H33), fp, cat)[0]
    if sha256(H86G) != H86G_SHA:
        raise RuntimeError("H86G-EDTI raster hash drift")
    h86g = lsi.decode(read1(H86G), fp, cat)[0]
    wins_h33 = wins_h86g = 0
    loso_proj = {}
    for site, th in e2["loso_thetas"].items():
        lam_s = lam_field(np.array(th), st, stack, names, fp, lv, cat)
        pc = lsi.expected_dti_of(dots.astype(np.float32), lam_s, active)["lsi_projection"]
        p3 = lsi.expected_dti_of(h33, lam_s, active)["lsi_projection"]
        pg = lsi.expected_dti_of(h86g, lam_s, active)["lsi_projection"]
        loso_proj[site] = {"candidate": pc, "H33": p3, "H86G": pg}
        wins_h33 += pc > p3
        wins_h86g += pc > pg
    nrefit = len(loso_proj)
    proj_all = {"candidate": curve[str(budget)]["lsi_projection"],
                "H33": lsi.expected_dti_of(h33, lam, active)["lsi_projection"],
                "H86G": lsi.expected_dti_of(h86g, lam, active)["lsi_projection"]}
    log(f"LSI-PROJECTION all-data: {proj_all}; LOSO wins vs H33 {wins_h33}/{nrefit}, vs H86G {wins_h86g}/{nrefit}")

    # SGMC-PROXY-DTI paired vs H33 and H86G
    sg_off = sgmc_truth(g)
    sg_fold = dict(fold=0, name="SGMC_PROXY", region=fp, truth=sg_off, visible=cat,
                   masked_known=cat, hidden_all=sg_off)
    t_c = EH.evaluate(dots.astype(np.float32), sg_fold, fp, block_side=200)[1]
    t_3 = EH.evaluate(h33, sg_fold, fp, block_side=200)[1]
    t_g = EH.evaluate(h86g, sg_fold, fp, block_side=200)[1]
    pooled_sg = EH.pooled_summary({"CAND": t_c, "H33_as_is": t_3, "H86G_EDTI_as_is": t_g},
                                  draws=1000, seed=861025, candidate="CAND")
    pooled_sg = json.loads(json.dumps(pooled_sg).replace("HOLDOUT-DTI", "SGMC-PROXY-DTI"))

    # HOLDOUT-DTI (visible construction, OOF): same theta, visible-catalogue shells
    visible = np.asarray(folds[0]["visible"], bool)
    lam_v = lam_field(theta, st, stack, names, fp, lv, visible)
    dvis = ndi.distance_transform_edt(~visible)
    rv = WORK / "ranked_visible.npy"
    if rv.is_file():
        ranked_v = np.load(rv)
    else:
        ranked_v = EDTI_M.spacing_greedy_ranking(lsi.sum_credit(lam_v), fp & (dvis > 3.0),
                                                 min_spacing_px=2.8)
        np.save(rv, ranked_v)
    dots_v = EDTI_M.prefix(ranked_v, budget)

    def fold_terms(pred):
        return np.sum([EH.evaluate(np.asarray(pred, np.float32), f, fp, block_side=200)[1]
                       for f in folds], axis=0)
    from gems57 import emit
    ranked_h, _ = emit.emit_decimated(lsi.rank01((h33 > 0).astype(np.float32), fp),
                                      fp & (dvis > 3.0), tile_px=3)
    ctrl = emit.emit_prefix(ranked_h, budget)
    pooled_ch = EH.pooled_summary({"CAND": fold_terms(dots_v), "H33_visible_collar": fold_terms(ctrl)},
                                  draws=1000, seed=861025, candidate="CAND")

    # final-dot uniqueness BEFORE serialization
    log("final-dot uniqueness")
    uniq = uniqueness_report(ek, dots, fp, reg, fp & ~cat)
    (EV / "h86j-lsi-registry-dots.json").write_text(json.dumps(uniq, indent=1))

    canary_ok = not any(v["leakage_flag"] for v in e1["canaries"].values())
    sg_d3 = pooled_sg["paired_differences"]["H33_as_is"]
    sg_dg = pooled_sg["paired_differences"]["H86G_EDTI_as_is"]
    ch = pooled_ch["scores"]
    gates = {
        "canary_leakage": canary_ok,
        "instrument_validity_loso": bool(e2["gate_instrument"]),
        "sgmc_vs_H33_paired_ci_lower_gt_0": bool(sg_d3["ci95"][0] > 0),
        "sgmc_vs_H86G_paired_ci_upper_gt_0": bool(sg_dg["ci95"][1] > 0),
        "lsi_projection_beats_H33_and_H86G_ge_90pct_loso": bool(
            wins_h33 >= 0.9 * nrefit and wins_h86g >= 0.9 * nrefit),
        "holdout_floor_vs_H33_visible_collar": bool(ch["CAND"]["dti"] >= ch["H33_visible_collar"]["dti"]),
        "uniqueness_registry": bool(uniq["gate_pass"] and not surf_uniq["rho_firings"]),
    }
    gates_ok = all(gates.values())
    verdict = "promote" if gates_ok else "negative"
    # AGENTS rule 13: research `promote` is not upload authorization. Upload stays
    # DO NOT SUBMIT while the shared literal full-support witness gate blocks every
    # non-empty raster (PA-86-01) and no organizer receipt exists.
    decision = ("RESEARCH PROMOTE ONLY - DO NOT SUBMIT (repo literal witness gate / rule 13; "
                "owner decision needed)" if gates_ok else "DO NOT SUBMIT (negative)")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(dots).tobytes()).hexdigest()[:8]
    name = f"gems86-h86j-lsi-{int(dots.sum())}dots-{stamp}-{digest8}-zeros"
    if not gates_ok:
        name = name.replace("-zeros", "-DO-NOT-SUBMIT-zeros")
    note = ("H86J-LSI live-score inversion truth-density, E[k] spacing2.8 collar3; "
            f"gates {'pass' if gates_ok else 'FAIL'}; run card in repo")[:140]
    pred = np.where(dots & fp, 1.0, 0.0).astype(np.float32)
    path = OUT_DIR / f"{name}.tif"
    receipt = submission_writer.write_submission(
        path, pred, ROOT / "data/bridge/sample_submission.tif", fp,
        note=note, name=name, catalogue=cat,
        metadata={"lane": "H86J-LSI", "budget": budget, "collar_px": 3.0,
                  "preregistration": "research/H86J_LSI_PREREGISTRATION.md"})
    disk = validate.validate(path, fp, cat)
    if not disk["all_checks_passed"]:
        raise RuntimeError("independent on-disk validator failed")
    receipt["independent_disk_validation"] = disk
    receipt["gate_verdict"] = verdict
    receipt["decision"] = decision
    receipt["gates"] = gates
    path.with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n")

    card = {
        "schema": "gems86.h86j-lsi-run-card.v1",
        "lane": "H86J-LSI",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": {p.name: sha256(p) for p in PREREG} | {"frozen_commit": "5259f66"},
        "hypothesis": "The owner-scored fleet rasters are measurements of the hidden live truth: "
                      "a log-linear truth-density field fitted so the official DTI algebra "
                      "reproduces their reported scores locates unmapped faults better than any "
                      "proxy-selected surface.",
        "mechanism": "T=<lam,c_i>, M=<lam,s_i>/3, G=<lam,1>; DTI_i=T/(0.2T+0.2(n-M)+0.8G); "
                     "lam=exp(theta.f) over 9 pinned stack ranks + lidar coverage + 5 catalogue-"
                     "distance shells; ridge LSQ; dots by E[k]=lam*kernel, spacing>=2.8 px, collar>3 px.",
        "named_non_fault_process": "Lahontan shorelines, volcanic flow fronts and unfaulted contacts "
                                   "mimic the scarp/edge layers; lidar coverage is a mapping-effort "
                                   "proxy, not geology.",
        "evidence_classes": "HOLDOUT-DTI = gems57-pooled-hide-v2; SGMC-PROXY-DTI = selection instrument; "
                            "LSI-PROJECTION = model number, never a score; live scores OWNER-REPORTED.",
        "preflight_pa86_01": {"status": preflight.get("status"),
                              "literal_reading_blocked": preflight.get("literal_reading_blocked")},
        "measurement_set": {"n": e1["n_measurements"], "excluded_rows": len(e1["excluded_rows"])},
        "leakage_canaries": e1["canaries"],
        "instrument_validation": {k: e2[k] for k in (
            "loso_spearman", "loso_mae", "loso_spearman_constant_model", "loso_mae_constant_model",
            "sgmc_proxy_spearman_same_set", "in_sample_spearman", "implied_hidden_truth_pixels_G",
            "loso_spearman_top_cluster_ge_0p20", "sgmc_spearman_top_cluster_ge_0p20", "n_top_cluster")},
        "baseline_spearman_vs_live": e1["baseline_spearman_vs_live"],
        "theta_all": dict(zip(e2["feature_names"], e2["theta_all"])),
        "budget_curve_lsi_projection": curve, "chosen_budget": budget,
        "lsi_projection": {"all_data": proj_all, "loso": loso_proj,
                           "wins_vs_H33": int(wins_h33), "wins_vs_H86G": int(wins_h86g),
                           "refits": nrefit},
        "sgmc_proxy": {"evaluator": "shared gems57 term machinery, relabelled",
                       "positives": int(sg_off.sum()), "pooled": pooled_sg},
        "holdout_dti": {"evaluator_version": EH.VERSION,
                        "withheld_positive_pixels": int(ch["CAND"]["withheld_positive_pixels"]),
                        "pooled": pooled_ch},
        "uniqueness_surface": {k: v for k, v in surf_uniq.items() if k != "rows"},
        "uniqueness_dots": {k: v for k, v in uniq.items() if k != "rows"},
        "uniqueness_rows_files": ["docs/evidence/h86j-lsi-registry-surface.json",
                                  "docs/evidence/h86j-lsi-registry-dots.json"],
        "gates": gates,
        "raster_sha256": receipt["sha256"],
        "validator_output": disk,
        "submission_name": name, "submission_file": f"docs/downloads/{name}.tif",
        "zip_file": f"docs/downloads/{name}.zip",
        "note": note, "note_chars": len(note),
        "verdict": verdict, "decision": decision,
        "lane_gates_pass": gates_ok,
        "safe_to_submit": False, "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "runtime_seconds": time.time() - started,
    }
    (EV / "h86j-lsi-run-card.json").write_text(json.dumps(card, indent=1) + "\n")
    log(json.dumps({"verdict": verdict, "name": name, "gates": gates}, indent=1))
    return card


def main(argv=None) -> int:
    # Historical builder: the literal stop precedes all candidate work.
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("fetch", "e1", "e2", "e3", "all"))
    a = ap.parse_args(argv)
    started = time.time()
    preflight = require_like_for_like()
    log(f"PA-86-01 preflight: {preflight['status']}")
    if a.stage == "fetch":
        stage_fetch()
        return 0
    g, folds = get_grid_folds()
    stack, names = get_stack(g)
    e1 = stage_e1(g, folds, stack, names)
    if a.stage == "e1":
        return 0
    e2 = stage_e2(e1)
    if a.stage == "e2":
        return 0
    stage_e3(g, folds, stack, names, e1, e2, preflight, started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
