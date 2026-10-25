#!/usr/bin/env python3
"""H86L-FMC: fleet minority-consensus lane. One experiment, fail-closed gates.

Shared template only (vendor/gems57 grid/holdout/evaluate_holdout/writer/validate).
Structural caveat: fleet rasters were built by their owners with the full
catalogue available, so this lane's HOLDOUT-DTI is labelled LEAKAGE-SUSPECT
and can never promote on its own; verdict logic below enforces that.
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
from gems57 import grid, holdout, evaluate_holdout as EH
from gems57.submission_writer import write_submission
from gems57.validate import validate

BUDGET, SPACING, COLLAR, SUP_LO, SUP_HI = 37654, 2.8, 3.0, 2, 8

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
    with rasterio.open(p) as s: return s.read(1)

def greedy(support, eligible, budget, spacing):
    ys, xs = np.nonzero(eligible)
    order = np.lexsort((xs, ys, -support[ys, xs].astype(int)))
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

def main():
    t0 = time.time(); stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    g = grid.load_grid(ROOT / "data/bridge"); fp, cat = g.footprint, g.catalogue
    fleet_files = sorted((ROOT / "data/scored_fleet").glob("*.tif"))
    fleet, support = {}, np.zeros(fp.shape, np.uint8)
    for p in fleet_files:
        m = (load(p) > 0) & fp; fleet[p.name] = m; support += m.astype(np.uint8)
    dcat = ndi.distance_transform_edt(~cat)
    eligible = fp & (dcat > COLLAR) & (support >= SUP_LO) & (support <= SUP_HI)
    dots = greedy(support, eligible, BUDGET, SPACING)
    print(f"fleet={len(fleet)} dots={int(dots.sum())} eligible={int(eligible.sum())}", flush=True)

    folds, _ = holdout.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    h33_name = [k for k in fleet if "h33-h33-2-b2" in k][0]
    # canary: support alone, withheld positives vs sampled active negatives
    region = np.zeros(fp.shape, bool); hidden = np.zeros(fp.shape, bool); known = np.zeros(fp.shape, bool)
    for f in folds:
        region |= f["region"]; hidden |= f["hidden_all"]; known |= f["masked_known"]
    active = region & fp & ~known; truth = active & hidden
    rng = np.random.default_rng(861186)
    p_idx = np.flatnonzero(truth.ravel()); n_all = np.flatnonzero((active & ~truth).ravel())
    n_idx = rng.choice(n_all, size=min(300_000, n_all.size), replace=False)
    vals = np.r_[support.ravel()[p_idx], support.ravel()[n_idx]].astype(float)
    y = np.r_[np.ones(p_idx.size), np.zeros(n_idx.size)]
    r = rankdata(vals); auc = float((r[y == 1].sum() - p_idx.size * (p_idx.size + 1) / 2) / (p_idx.size * n_idx.size))

    terms = {"H86L_FMC": [], "H33_control": []}
    for f in folds:
        for key, arr in (("H86L_FMC", dots), ("H33_control", fleet[h33_name])):
            _, bt = EH.evaluate(arr.astype(np.float32), f, fp, block_side=200)
            terms[key].append(bt)
    pooled = EH.pooled_summary({k: np.sum(v, axis=0) for k, v in terms.items()},
                               draws=1000, seed=861186, candidate="H86L_FMC")
    cand = pooled["scores"]["H86L_FMC"]; delta = pooled["paired_differences"]["H33_control"]

    # uniqueness vs fleet + prior downloads: Spearman on support + 3px dot overlap
    # Both fields binary => Spearman rho == phi coefficient (exact, fast).
    uni = {"max_spearman_rho": 0.0, "max_overlap3": 0.0, "worst_spearman": None, "worst_overlap": None,
           "method": "phi coefficient (= Spearman for binary fields); overlap = frac candidate dots <=3px of other dots"}
    others = [(k, v) for k, v in fleet.items()]
    for p in sorted((ROOT / "docs/downloads").glob("*.tif")):
        try: others.append((p.name, (load(p) > 0) & fp))
        except Exception: pass
    n_c = float(dots.sum()); N = float(dots.size)
    for name, m in others:
        n_o = float(m.sum()); both = float((dots & m).sum())
        den = np.sqrt(n_c * (N - n_c) * n_o * (N - n_o)) if n_o else 0.0
        rho = float((both * N - n_c * n_o) / den) if den else 0.0
        d = ndi.distance_transform_edt(~m) if m.any() else np.full(fp.shape, 99.0)
        ov = float((d[dots] <= 3.0).mean()) if dots.any() else 0.0
        if abs(rho) > abs(uni["max_spearman_rho"]): uni.update(max_spearman_rho=rho, worst_spearman=name)
        if ov > uni["max_overlap3"]: uni.update(max_overlap3=ov, worst_overlap=name)
    print(f"holdout={cand} delta={delta} auc={auc} uni={uni}", flush=True)

    gates = {
        "holdout_beats_h33_paired_ci_low_gt_0": bool(delta["ci95"][0] > 0),
        "canary_auc_le_0.90": bool(auc <= 0.90),
        "spearman_abs_lt_0.90": bool(abs(uni["max_spearman_rho"]) < 0.90),
        "overlap3_le_0.70": bool(uni["max_overlap3"] <= 0.70),
        "budget_exact": bool(int(dots.sum()) == BUDGET),
        "zero_dots_on_catalogue": bool(not (dots & cat).any()),
    }
    # Fleet ancestry = structural leakage: cannot be cured by a passing canary.
    verdict = "negative"; safe = False
    note = "H86L-FMC fleet minority-consensus 2-8/25, 37654 dots; leakage-suspect holdout; DO NOT SUBMIT"
    stem = f"gems86-h86l-fmc-minconsensus-37654dots-{stamp}"
    out = ROOT / "docs/downloads" / f"{stem}-zeros.tif"
    pred = np.zeros(fp.shape, np.float32); pred[dots] = 1.0; pred = np.where(fp, pred, 0.0)
    write_submission(out, pred, ROOT / "data/bridge/sample_submission.tif", fp,
                     note=note[:140], name=stem[:140], catalogue=cat,
                     metadata={"lane": "H86L-FMC", "verdict": verdict})
    val = validate(out, fp, cat)
    digest = sha(out)
    card = {
        "schema": "gems86.run-card.v1", "lane_id": "H86L-FMC",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "Minority fleet corroboration (support 2-8 of 25 independent scored rasters), >3px off-catalogue, marks unmapped faults the majority herd misses.",
        "mechanism": "Per-pixel fleet vote; greedy 2.8px Poisson-disc emission of 37,654 unit dots, support-descending.",
        "named_non_fault_mimic": "Shared fleet ancestry (H19-5/D28 lineage) manufacturing corroboration; common DEM artefacts.",
        "holdout": {"evidence_class": "HOLDOUT-DTI (LEAKAGE-SUSPECT: fleet built with full catalogue)",
                    "evaluator_version": EH.VERSION, "candidate": cand, "paired_vs_H33": delta,
                    "withheld_positive_pixels": cand["withheld_positive_pixels"]},
        "leakage_canary": {"feature": "fleet_support_count", "auc": auc, "gate_le_0.90": gates["canary_auc_le_0.90"],
                           "note": "Passing canary does not cure fleet-ancestry leakage; verdict stays negative."},
        "correlation_overlap_vs_registry": uni,
        "gates": gates, "raster_sha256": digest,
        "validator": val if isinstance(val, dict) else str(val),
        "submission_name": stem, "submission_note_le140": note,
        "verdict": verdict, "safe_to_submit": safe, "approved_for_weekly_slot": False,
        "submission_slots_used": 0, "dots": int(dots.sum()),
        "fleet_inputs_sha256": {p.name: sha(p) for p in fleet_files},
        "runtime_s": round(time.time() - t0, 1),
        "blockers": ["IR-86L-01: native feature stack (.cache/training_features.tif) absent in checkout; geological lanes BMR/GSST blocked.",
                     "Fleet-ancestry leakage: holdout is an upper bound, not hide-and-recover evidence."],
    }
    (ROOT / "docs/evidence/h86l-fmc-run-card.json").write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps({"file": out.name, "sha256": digest, "verdict": verdict, "validator": card["validator"]}, indent=2))

if __name__ == "__main__":
    main()
