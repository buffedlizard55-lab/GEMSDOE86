#!/usr/bin/env python3
"""GEMSDOE86 lane: Blind Geothermal Conduit (BGC) emission — NEW lane.

Method (single lane paragraph):
  Dots are emitted off the mapped catalogue (nothing on a traced fault) from a
  hybrid surface: rank-normalized catalogue-proximity credit (triangular 300 m
  kernel over catalogue distance, 1-7 px annulus) blended with a rank-normalized
  geothermal-anomaly surface (GeoDAWN radiometric total count Band 6 tc, weight
  0.5; near-surface conductivity Band 17 cond_surf, 0.3; unsigned horizontal
  gravity-gradient magnitude Band 5, 0.2), blend weight swept on the holdout.
  One candidate per 3 x 3 tile, top-N by hybrid credit with 3-px mutual
  exclusion, N swept on the holdout.  Visible faults are masked pixel-exactly
  out of scoring (known); every catalogue-derived quantity is built from
  visible faults only; withheld segments never enter a feature.  Scored by
  pooled hide-and-recover DTI (alpha = 0.2, beta = 0.8, 300 m triangular
  kernel) over four spatial quadrants with paired spatial-block 95% CI;
  per-feature leakage canary (feature-alone AUC vs withheld truth);
  uniqueness vs the full 655-raster public registry (Spearman rho <= 0.90 on
  the surface vs every raster; forward 3-px dot overlap <= 0.70 vs every
  dot-field raster).  Packaged by the fail-closed shared writer as a
  single-band float32 EPSG:32611 3730 x 3292 pinned-transform GeoTIFF, finite
  values in [0, 1], zeros outside the footprint and on the catalogue.

Distinct from GEMSDOE32 H33 (binary dotted-ridge field minus its 1-2 px
catalogue collar), GEMSDOE28 H87 (bands 3-5 px dots on visible traces) and
Poisson off-catalogue dot fields: this is a geothermally gated, off-catalogue
dotted annulus, not a structure-thinned copy of any site-best raster.

It enters through protocol_preflight.require_like_for_like() (PA-86-01/PA-86-02),
NOT require_feasible(), and must then pass scripts/check_h86e_registry.py on the
surface and the final dots plus scripts/pa86_chance_overlap.py.  Local format
validity is not organizer acceptance; safe_to_submit and
approved_for_weekly_slot stay false until an organizer receipt is logged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import grid as grid_mod, emit as emit_mod, metric, holdout as holdout_mod  # noqa: E402
from gems57.submission_writer import write_submission  # noqa: E402
from src.gems86.io import read_band  # noqa: E402

from scripts.protocol_preflight import require_like_for_like  # noqa: E402

BRIDGE = ROOT / "data" / "bridge"
FEATURES = BRIDGE / "training_features.tif"
DOWNLOADS = ROOT / "docs" / "downloads"
EVIDENCE = ROOT / "evidence"
SAMPLE = BRIDGE / "sample_submission.tif"

TC_BAND, COND_BAND, GRAV_BAND = 6, 17, 5  # tc, cond_surf, iso_grav_anom_slope (= |grad g|)
W_TC, W_COND, W_GRAV = 0.5, 0.3, 0.2
TILE_PX = 3
DCAT_MIN = 1.0          # writer-safe: never on a mapped trace
DCAT_MAX = 7.0          # off-catalogue annulus outer edge (px)
ANCHOR_MAX_FRAC = 0.0   # proximity credit already anchors near traces
BOOTSTRAP_DRAWS = 2000
BOOTSTRAP_SEED = 9172026
CANDIDATE_CAP = 400_000

EVIDENCE.mkdir(parents=True, exist_ok=True)
DOWNLOADS.mkdir(parents=True, exist_ok=True)


def sha_bytes(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def rank_normalize(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    out = np.zeros(a.shape, np.float64)
    m = np.isfinite(a) & valid
    if int(m.sum()) < 2:
        return out
    vals = a[m]
    order = np.argsort(vals, kind="stable")
    ranks = np.empty(vals.size, np.float64)
    ranks[order] = np.arange(vals.size, dtype=np.float64)
    uniq, inv, cnt = np.unique(vals[order], return_inverse=True, return_counts=True)
    if (cnt > 1).any():
        means = np.bincount(inv, weights=ranks[order]) / cnt
        ranks[order] = means[inv]
    out[m] = ranks / max(vals.size - 1, 1)
    return out


def build_surface(g, bands, w_geo):
    tc = rank_normalize(bands["tc"], g.footprint)
    cond = rank_normalize(bands["cond"], g.footprint)
    grav = rank_normalize(bands["grav"], g.footprint)
    geo = W_TC * tc + W_COND * cond + W_GRAV * grav
    geo = geo / geo.max() if geo.max() > 0 else geo
    dcat = ndi.distance_transform_edt(~g.catalogue).astype(np.float32)
    # Catalogue-proximity credit: triangular kernel over distance to mapped trace,
    # zero on the trace itself (dots must stay off mapped faults) and zero at
    # DCAT_MAX; this is the holdout-recovery signal.
    prox = metric.kernel(np.minimum(dcat, DCAT_MAX))   # k(d), peaks at d=0 -> 0 on traces
    prox = np.where(g.footprint & (dcat >= DCAT_MIN), prox, 0.0)
    prox = rank_normalize(prox, g.footprint & (dcat >= DCAT_MIN))
    surface = (1.0 - w_geo) * prox + w_geo * geo
    surface = np.where(g.footprint, np.clip(surface, 0.0, 1.0), 0.0).astype(np.float32)
    return surface, dcat, prox


def emit_dots(surface, allowed, n_dots):
    """Top-N dots by hybrid credit with 3-px mutual exclusion."""
    ek = emit_mod.expected_credit(surface)  # surface used as proxy truth field
    cand = allowed & (ek > 0)
    ys, xs = np.nonzero(cand)
    if ys.size == 0:
        return np.zeros(surface.shape, bool)
    order = np.argsort(-ek[ys, xs], kind="stable")[:CANDIDATE_CAP]
    ys, xs = ys[order], xs[order]
    blocked = np.zeros(surface.shape, bool)
    selected_y, selected_x = [], []
    for i in range(ys.size):
        if len(selected_y) >= n_dots:
            break
        if blocked[ys[i], xs[i]]:
            continue
        selected_y.append(int(ys[i]))
        selected_x.append(int(xs[i]))
        blocked[max(0, ys[i] - TILE_PX):ys[i] + TILE_PX + 1,
                max(0, xs[i] - TILE_PX):xs[i] + TILE_PX + 1] = True
    dots = np.zeros(surface.shape, bool)
    dots[selected_y, selected_x] = True
    return dots


def build_holdout(g):
    return holdout_mod.build_holdout(g, hide_frac=0.20, seeds=(20, 21), modes=("all",))


def score_dots(dots, ctx):
    return holdout_mod.evaluate(dots, ctx)


def pooled_with_ci(terms_list, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    """Resample whole spatial-block cells for a paired spatial-block CI."""
    arr = np.array([[t["tp"], t["fp"], t["fn"], t["n_truth"]] for t in terms_list], float)
    base = metric.dti_from_components(arr[:, 0].sum(), arr[:, 1].sum(), arr[:, 2].sum())
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, arr.shape[0], size=(draws, arr.shape[0]))
    boot = np.array([metric.dti_from_components(*arr[p].sum(axis=0)[:3]) for p in picks])
    return float(base), (float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))), boot


def canary_aucs(ctx, bands, g):
    """Feature-alone AUC vs pooled withheld truth.  AUC > 0.90 = leakage flag."""
    from sklearn.metrics import roc_auc_score

    truth_index = np.zeros(g.shape, bool)
    pos_feats = []
    for cell in ctx.cells:
        ty, tx = cell.truth_yx
        fy, fx = cell.bbox[0].start + ty, cell.bbox[1].start + tx
        truth_index[fy, fx] = True
        pos_feats.append(np.stack([bands[name][fy, fx] for name in bands], axis=1))
    P = np.concatenate(pos_feats, axis=0)
    rng = np.random.default_rng(314159)
    neg_mask = (g.footprint & ~g.catalogue) & ~truth_index
    ny, nx = np.nonzero(neg_mask)
    take = min(ny.size, 300_000)
    sel = rng.choice(ny.size, size=take, replace=False)
    N = np.stack([bands[name][ny[sel], nx[sel]] for name in bands], axis=1)
    X = np.vstack([P, N])
    y = np.concatenate([np.ones(len(P)), np.zeros(len(N))])
    return {name: float(roc_auc_score(y, X[:, j])) for j, name in enumerate(bands)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(DOWNLOADS))
    ap.add_argument("--name", default=None)
    ap.add_argument("--note", default=None)
    ap.add_argument("--skip-holdout", action="store_true")
    ap.add_argument("--skip-registry", action="store_true")
    a = ap.parse_args()
    out_dir = Path(a.out_dir)

    # PA-86-01/PA-86-02: like-for-like pre-placement gate for this NEW lane only.
    cert = require_like_for_like()
    print("preflight:", cert["status"], "| witness:", cert["witness_representation"]["kind"],
          flush=True)

    g = grid_mod.load_grid(BRIDGE)
    bands = {name: read_band(FEATURES, idx) for name, idx in
             (("tc", TC_BAND), ("cond", COND_BAND), ("grav", GRAV_BAND))}
    print(f"grid {g.shape} footprint {int(g.footprint.sum())} catalogue {int(g.catalogue.sum())}",
          flush=True)

    ctx = None if a.skip_holdout else build_holdout(g)
    withheld_total = sum(c.n_truth for c in ctx.cells) if ctx else 0
    print(f"withheld positives {withheld_total}", flush=True)

    # --- holdout sweep (Experiment 1) --------------------------------------
    best = None
    results = []
    if ctx is not None:
        for n_dots in (20_000, 40_000):
            for w_geo in (0.0, 0.3, 0.6):
                surface, dcat, prox = build_surface(g, bands, w_geo)
                allowed = g.footprint & ~g.catalogue & (dcat >= DCAT_MIN)
                dots = emit_dots(surface, allowed, n_dots)
                res = score_dots(dots, ctx)
                base, ci, _boot = pooled_with_ci([c for c in res["folds"].values()])
                results.append(dict(n_dots=n_dots, w_geo=w_geo, dots=int(dots.sum()),
                                    pooled_dti=res["pooled_dti"], ci=ci,
                                    coverage=res["pooled_coverage"],
                                    on_cat=int(res["on_visible_catalogue"])))
                print(f"  N={n_dots} w_geo={w_geo} dots={int(dots.sum())} "
                      f"DTI={res['pooled_dti']:.5f} CI=[{ci[0]:.5f},{ci[1]:.5f}]",
                      flush=True)
                if best is None or res["pooled_dti"] > best["pooled_dti"]:
                    best = dict(results[-1])
        # control: uniform off-catalogue dots
        rng = np.random.default_rng(7)
        allowed = g.footprint & ~g.catalogue
        ny, nx = np.nonzero(allowed)
        sel = rng.choice(ny.size, size=min(ny.size, 40_000), replace=False)
        uni = np.zeros(g.shape, bool); uni[ny[sel], nx[sel]] = True
        ures = score_dots(uni, ctx)
        ubase, uci, _ = pooled_with_ci([c for c in ures["folds"].values()])
        results.append(dict(n_dots=40_000, w_geo="uniform", dots=int(uni.sum()),
                            pooled_dti=ures["pooled_dti"], ci=uci,
                            coverage=ures["pooled_coverage"], on_cat=int(ures["on_visible_catalogue"])))
        print(f"  UNIFORM control dots={int(uni.sum())} DTI={ures['pooled_dti']:.5f} "
              f"CI=[{uci[0]:.5f},{uci[1]:.5f}]", flush=True)
        geo_cfgs = [r for r in results if isinstance(r["w_geo"], float) and r["w_geo"] > 0]
        pick = max(geo_cfgs, key=lambda r: r["pooled_dti"]) if geo_cfgs else best
        best = pick
        print(f"BEST holdout config (geothermal-gated): N={best['n_dots']} w_geo={best['w_geo']} "
              f"DTI={best['pooled_dti']:.5f} CI=[{best['ci'][0]:.5f},{best['ci'][1]:.5f}]",
              flush=True)

    # --- leakage canary ----------------------------------------------------
    canary = canary_aucs(ctx, bands, g) if ctx is not None else {}
    print("canary AUC:", {k: round(v, 4) for k, v in canary.items()}, flush=True)
    leakage_flag = any(v > 0.90 for v in canary.values())

    # --- live build on the FULL catalogue (Experiment 2) -------------------
    n_dots = int(best["n_dots"]) if best else 30_000
    w_geo = float(best["w_geo"]) if best else 0.3
    surface, dcat, prox = build_surface(g, bands, w_geo)
    full_allowed = g.footprint & ~g.catalogue & (dcat >= DCAT_MIN)
    dots = emit_dots(surface, full_allowed, n_dots)
    pred = dots.astype(np.float32)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = sha_bytes(pred)[:8]
    name = a.name or f"gems86-bgc-conduit-{int(dots.sum())}d-{stamp}-{digest}-zeros"
    holdout_note = (f"holdout DTI {best['pooled_dti']:.4f} [{best['ci'][0]:.4f},{best['ci'][1]:.4f}]"
                    if best else "holdout DTI NR")
    note = a.note or (f"BGC dots off faults; prox+TC/cond/gravity surface; {int(dots.sum())} dots; "
                      f"{holdout_note}; values [0,1]; not organizer-approved")
    assert len(name) <= 140, len(name)
    assert len(note) <= 140, len(note)
    if (out_dir / f"{name}.tif").exists():
        raise FileExistsError(f"refusing to overwrite: {out_dir / f'{name}.tif'}")
    receipt = write_submission(out_dir / f"{name}.tif", pred, SAMPLE, g.footprint,
                               note=note, name=name, catalogue=g.catalogue,
                               metadata=dict(lane="gems86-bgc",
                                             method="blind geothermal conduit emission; off-catalogue dots only",
                                             bands={"tc": 6, "cond": 17, "grav": 5},
                                             weights=[W_TC, W_COND, W_GRAV], w_geo=w_geo,
                                             dcat_min=DCAT_MIN, dcat_max=DCAT_MAX,
                                             dots=int(dots.sum()), n_dots=n_dots,
                                             withheld_positives=withheld_total,
                                             canary_aucs=canary, leakage_flag=leakage_flag,
                                             verdict="format-valid; registry/holdout measured below"))
    print("WRITTEN", receipt["file"], receipt["sha256"], flush=True)
    print("validation:", receipt["validator"]["all_checks_passed"], receipt["validator"]["checks"],
          flush=True)

    # --- uniqueness (Experiment 3): surface + final dots vs full registry ----
    surface_path = out_dir / f"{name}.surface.npy"
    dots_path = out_dir / f"{name}.dots.npy"
    np.save(surface_path, surface)
    np.save(dots_path, pred)

    reg_reports = {}
    if not a.skip_registry:
        for mode, arr_path in (("surface", surface_path), ("final_dots", dots_path)):
            out_json = out_dir / f"{name}.{mode}.registry.json"
            cmd = [sys.executable, "scripts/check_h86e_registry.py", str(arr_path), str(out_json)]
            if mode == "surface":
                cmd.append("--surface")
            cp = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            reg_reports[mode] = dict(exit=cp.returncode, out=str(out_json),
                                     stdout=cp.stdout[-2000:], stderr=cp.stderr[-2000:])
            print(f"registry {mode}: exit {cp.returncode}", flush=True)
            if cp.returncode == 0:
                rep = json.loads(open(out_json).read())
                print(json.dumps({k: rep[k] for k in ("surface_gate_pass", "final_dots_gate_pass",
                                                      "literal_gate_pass",
                                                      "registry_complete_for_index")}, indent=2),
                      flush=True)

    card = dict(
        schema="gems86.run-card.v1",
        lane="gems86-bgc-blind-geothermal-conduit",
        hypothesis="Off-catalogue dots gated by a geothermal-anomaly surface (radiometric TC, "
                   "conductivity, gravity gradient) recover withheld fault segments and target blind "
                   "geothermal conduits missing from the USGS/INGENIOUS catalogue.",
        mechanism="Rank-normalized catalogue-proximity credit (triangular 300 m kernel, 1-7 px "
                  "off-catalogue annulus) blended with rank-normalized Band 6 tc / Band 17 cond_surf / "
                  "Band 5 gravity-gradient surface; tile-maximized sparse dots; visible faults masked "
                  "pixel-exactly from scoring.",
        named_non_fault_mimic="Radiometric/conductivity anomalies from alteration, lithology or cover "
                              "unrelated to faults; gravity gradients from density contacts without "
                              "displacement.",
        evaluator_version='gems57-pooled-hide-v2',
        holdout_dti=(best["pooled_dti"] if best else None),
        holdout_ci95=(best["ci"] if best else None),
        withheld_positives=withheld_total,
        alpha=metric.ALPHA, beta=metric.BETA, triangular_radius_m=metric.R_M,
        leakage_canary=canary, leakage_flag=leakage_flag,
        surface_sha256=sha_bytes(surface), dots_sha256=sha_bytes(pred), raster_sha256=receipt["sha256"],
        n_dots=int(dots.sum()),
        registry=reg_reports,
        validator=receipt["validator"],
        template_report=receipt["template_report"],
        submission_name=name, note=note, note_chars=len(note),
        safe_to_submit=False, approved_for_weekly_slot=False,
        submission_slots_used=0,
        generated_utc=datetime.now(timezone.utc).isoformat(),
    )
    card_path = EVIDENCE / f"{name}-run-card.json"
    card_path.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print("RUN CARD", card_path, flush=True)
    verdict = "NEGATIVE / DO NOT SUBMIT"
    if (not leakage_flag and best and best["ci"][0] > 0
            and all(r.get("exit") == 0 for r in reg_reports.values())):
        verdict = "PROMOTE-TO-SELECTOR (organizer receipt + slot still required)"
    print("VERDICT:", verdict, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
