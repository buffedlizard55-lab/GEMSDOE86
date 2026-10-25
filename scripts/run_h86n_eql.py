#!/usr/bin/env python3
"""H86N-EQL: earthquake-lineation anisotropy lane (bands 10/16 primary).

Preregistration: research/H86N_EQA_PREREGISTRATION.md (frozen before scoring).
Shared template only: vendor/gems57 grid/holdout/evaluate_holdout/writer/validate.
Surfaces use ONLY native seismicity bands 10 (deq_n100a15) and 16 (ieq_n100a15)
plus, for the C1 control, band 2 (rtp). No catalogue-derived feature exists in
any surface, so surfaces are fold-safe by construction; the catalogue is used
only for (a) holdout truth/masking via the shared evaluator and (b) the
protocol-standard >3px emission collar (visible-only inside holdout folds).
"""
from __future__ import annotations
import hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))
from gems57 import grid, holdout, evaluate_holdout as EH
from gems57.submission_writer import write_submission
from gems57.validate import validate
from scripts.protocol_preflight import require_like_for_like

BUDGET, SPACING, COLLAR = 37654, 2.8, 3.0
SIG_DERIV, SIG_TENSOR = 1.5, 6.0

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
    with rasterio.open(p) as s: return s.read(1)

def greedy(support, eligible, budget, spacing):
    ys, xs = np.nonzero(eligible)
    order = np.lexsort((xs, ys, -support[ys, xs]))
    ys, xs = ys[order], xs[order]
    cell = int(np.ceil(spacing)); chosen = {}; oy, ox = [], []
    r2 = spacing * spacing
    for y, x in zip(ys.tolist(), xs.tolist()):
        cy, cx = y // cell, x // cell; ok = True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for yy, xx in chosen.get((cy + dy, cx + dx), ()):
                    if (yy - y) ** 2 + (xx - x) ** 2 < r2: ok = False; break
                if not ok: break
            if not ok: break
        if ok:
            chosen.setdefault((cy, cx), []).append((y, x)); oy.append(y); ox.append(x)
            if len(oy) >= budget: break
    dots = np.zeros(support.shape, bool); dots[oy, ox] = True; return dots

def rankpct(a, fp):
    out = np.zeros(a.shape, np.float32)
    v = a[fp]; r = rankdata(v) / max(len(v), 1)
    out[fp] = r.astype(np.float32); return out

def clean(a, fp):
    a = a.astype(np.float64)
    med = np.nanmedian(a[fp])
    a = np.where(np.isfinite(a), a, med)
    a[~fp] = med
    return a

def main():
    t0 = time.time()
    cert = require_like_for_like()
    print(f"preflight: {cert['status']} witness_rep={cert['witness_representation']}", flush=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    g = grid.load_grid(ROOT / "data/bridge"); fp, cat = g.footprint, g.catalogue
    tf = ROOT / "data/bridge/training_features.tif"
    with rasterio.open(tf) as s:
        b10 = clean(s.read(10), fp); b16 = clean(s.read(16), fp); rtp = clean(s.read(2), fp)
    # Seismicity density (rank/ log only: invariant to unverified band units).
    d = 0.5 * (rankpct(np.log1p(np.maximum(b10, 0.0)), fp) + rankpct(np.log1p(np.maximum(b16, 0.0)), fp))
    # Structure tensor coherence of the density field.
    sm = ndi.gaussian_filter(d.astype(np.float64), SIG_DERIV)
    gy, gx = np.gradient(sm)
    jxx = ndi.gaussian_filter(gx * gx, SIG_TENSOR)
    jyy = ndi.gaussian_filter(gy * gy, SIG_TENSOR)
    jxy = ndi.gaussian_filter(gx * gy, SIG_TENSOR)
    tr = jxx + jyy
    disc = np.sqrt(np.maximum((jxx - jyy) ** 2 + 4.0 * jxy ** 2, 0.0))
    coherence = disc / (tr + 1e-18)
    energy = np.sqrt(np.maximum(tr, 0.0))
    cand_raw = coherence * energy * (0.25 + 0.75 * d)
    surface = rankpct(cand_raw, fp)
    feats = {
        "eql_log_b10": np.log1p(np.maximum(b10, 0.0)), "eql_log_b16": np.log1p(np.maximum(b16, 0.0)),
        "eql_density": d.astype(np.float64), "eql_coherence": coherence,
        "eql_energy": energy, "eql_cand_raw": cand_raw,
        "ctrl_rtp_grad": np.hypot(*np.gradient(rtp)),
    }
    surfaces = {"H86N_EQL": surface,
                "C0_iso_density": d.astype(np.float32),
                "C1_rtp_grad": rankpct(feats["ctrl_rtp_grad"], fp)}
    dcat = ndi.distance_transform_edt(~cat)
    eligible = fp & (dcat > COLLAR)
    dots = {k: greedy(s, eligible, BUDGET, SPACING) for k, s in surfaces.items()}
    for k, dd in dots.items(): print(f"{k}: dots={int(dd.sum())}", flush=True)

    folds, _ = holdout.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    region = np.zeros(fp.shape, bool); hidden = np.zeros(fp.shape, bool); known = np.zeros(fp.shape, bool)
    for f in folds:
        region |= f["region"]; hidden |= f["hidden_all"]; known |= f["masked_known"]
    active = region & fp & ~known; truth = active & hidden
    rng = np.random.default_rng(861438)
    p_idx = np.flatnonzero(truth.ravel()); n_all = np.flatnonzero((active & ~truth).ravel())
    n_idx = rng.choice(n_all, size=min(300_000, n_all.size), replace=False)
    canary = {}
    for name, arr in feats.items():
        vals = np.r_[arr.ravel()[p_idx], arr.ravel()[n_idx]].astype(float)
        y = np.r_[np.ones(p_idx.size), np.zeros(n_idx.size)]
        r = rankdata(vals); auc = float((r[y == 1].sum() - p_idx.size * (p_idx.size + 1) / 2) / (p_idx.size * n_idx.size))
        canary[name] = round(auc, 4)
    print(f"canary={canary} withheld={int(truth.sum())}", flush=True)

    terms = {k: [] for k in dots}
    for f in folds:
        visible = cat & ~f["hidden_all"]
        elig_vis = fp & (ndi.distance_transform_edt(~visible) > COLLAR)
        for k, s in surfaces.items():
            fd = greedy(s, elig_vis, BUDGET, SPACING)
            _, bt = EH.evaluate(fd.astype(np.float32), f, fp, block_side=200); terms[k].append(bt)
    pooled = EH.pooled_summary({k: np.sum(v, axis=0) for k, v in terms.items()},
                               draws=1000, seed=861438, candidate="H86N_EQL")
    cand = pooled["scores"]["H86N_EQL"]; deltas = pooled["paired_differences"]
    print(f"holdout={cand} deltas={deltas}", flush=True)

    others = []
    for p in sorted((ROOT / "data/scored_fleet").glob("*.tif")):
        others.append((p.name, (load(p) > 0) & fp))
    for p in sorted((ROOT / "docs/downloads").glob("*.tif")):
        try: others.append((p.name, (load(p) > 0) & fp))
        except Exception: pass
    fy, fx = np.nonzero(fp); sidx = rng.choice(len(fy), size=min(300_000, len(fy)), replace=False)
    sy, sx = fy[sidx], fx[sidx]; cand_s = rankdata(surface[sy, sx])
    uni = {"max_surface_spearman_abs": 0.0, "worst_surface": None, "max_dot_spearman_abs": 0.0,
           "worst_dot": None, "max_overlap3": 0.0, "worst_overlap": None, "n_registry_measured": len(others),
           "method": "surface Spearman on shared 300k footprint sample vs every raster; dot phi (=Spearman, binary); overlap=frac candidate dots <=3px of other dots, dot-fields only (support<=20% footprint, PA-86-01)",
           "registry_scope": "Locally measured rasters only (data/scored_fleet + docs/downloads at run time); complete 92-site registry NOT restored this session, so no complete-uniqueness claim is made."}
    d = dots["H86N_EQL"]; n_c = float(d.sum()); N = float(d.size)
    for name, m in others:
        mv = m[sy, sx].astype(float)
        if mv.std() > 0:
            rho_s = float(np.corrcoef(cand_s, rankdata(mv))[0, 1])
            if abs(rho_s) > uni["max_surface_spearman_abs"]: uni.update(max_surface_spearman_abs=rho_s, worst_surface=name)
        n_o = float(m.sum()); both = float((d & m).sum())
        den = np.sqrt(n_c * (N - n_c) * n_o * (N - n_o)) if n_o else 0.0
        rho = float((both * N - n_c * n_o) / den) if den else 0.0
        if abs(rho) > uni["max_dot_spearman_abs"]: uni.update(max_dot_spearman_abs=rho, worst_dot=name)
        from gems57.uniqueness import representation_class
        if m.any() and representation_class(int(m.sum()), int(fp.sum()))["kind"] == "dot_field":
            dd = ndi.distance_transform_edt(~m); ov = float((dd[d] <= 3.0).mean())
            if ov > uni["max_overlap3"]: uni.update(max_overlap3=ov, worst_overlap=name)
    print(f"uni={uni}", flush=True)

    sym_auc_ok = all(min(v, 1 - v) >= 0.10 for v in canary.values())  # symmetric AUC <= 0.90
    gates = {
        "paired_ci_low_gt_0_vs_C0": bool(deltas["C0_iso_density"]["ci95"][0] > 0),
        "paired_ci_low_gt_0_vs_C1": bool(deltas["C1_rtp_grad"]["ci95"][0] > 0),
        "canary_all_symmetric_auc_le_0.90": bool(sym_auc_ok),
        "surface_spearman_abs_le_0.90": bool(abs(uni["max_surface_spearman_abs"]) <= 0.90),
        "dot_spearman_abs_le_0.90": bool(abs(uni["max_dot_spearman_abs"]) <= 0.90),
        "overlap3_le_0.70": bool(uni["max_overlap3"] <= 0.70),
        "budget_exact": bool(int(d.sum()) == BUDGET),
        "zero_dots_on_catalogue": bool(not (d & cat).any()),
    }
    promote = all(gates.values())
    verdict = "promote" if promote else "negative"
    stem = f"gems86-h86n-eql-seislineation-37654dots-{stamp}"
    note = ("H86N-EQL seismicity lineation anisotropy dotted 37654; HOLDOUT-DTI in run card; "
            + ("gates pass" if promote else "DO NOT SUBMIT"))[:140]
    out = ROOT / "docs/downloads" / f"{stem}-zeros.tif"
    pred = np.where(fp, d.astype(np.float32), np.float32(0.0))
    write_submission(out, pred, ROOT / "data/bridge/sample_submission.tif", fp,
                     note=note, name=stem[:140], catalogue=cat,
                     metadata={"lane": "H86N-EQL", "verdict": verdict})
    val = validate(out, fp, cat)
    if not val["all_checks_passed"]:
        raise RuntimeError(f"validator failed after write: {val['checks']}")
    card = {
        "schema": "gems86.run-card.v1", "lane_id": "H86N-EQL",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": "research/H86N_EQA_PREREGISTRATION.md",
        "hypothesis": "Line-like (anisotropic) organization of the seismicity fields (bands 10/16) at ~600 m scale traces active fault segments, including catalogue-missing ones under fill/volcanics; isotropic seismicity clouds do not.",
        "mechanism": "Density d=mean(rank log1p B10, rank log1p B16); structure-tensor coherence c of d (deriv sigma 1.5px, tensor sigma 6px); surface=rank(c*sqrt(E)*(0.25+0.75d)); greedy 2.8px emission, 37654 dots, >3px off catalogue.",
        "named_non_fault_mimic": "Geothermal induced-seismicity clusters (radial), quarry/blast and network-geometry location artifacts, bridged isotropic clusters.",
        "holdout": {"evidence_class": "HOLDOUT-DTI", "evaluator_version": EH.VERSION,
                    "candidate": {**cand, "withheld_positive_pixels": int(truth.sum())},
                    "controls": {k: pooled["scores"][k] for k in ("C0_iso_density", "C1_rtp_grad")},
                    "paired_differences_vs_candidate": deltas},
        "leakage_canary": {"single_feature_auc": canary, "gate_symmetric_le_0.90": gates["canary_all_symmetric_auc_le_0.90"]},
        "correlation_overlap_vs_registry": uni,
        "preflight_PA-86-01": {"status": cert["status"], "literal_reading_blocked": cert["literal_reading_blocked"],
                               "witness_representation": cert["witness_representation"]},
        "gates": gates, "raster_sha256": sha(out),
        "validator": val if isinstance(val, dict) else str(val),
        "submission_name": stem, "submission_note_le140": note, "note_chars": len(note),
        "verdict": verdict, "safe_to_submit": False, "approved_for_weekly_slot": False,
        "submission_slots_used": 0, "dots": int(d.sum()),
        "input_sha256": {"training_features.tif": sha(tf)},
        "runtime_s": round(time.time() - t0, 1),
    }
    (ROOT / "docs/evidence/h86n-eql-run-card.json").write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps({"file": out.name, "sha256": card["raster_sha256"], "verdict": verdict, "gates": gates}, indent=2))

if __name__ == "__main__":
    main()
