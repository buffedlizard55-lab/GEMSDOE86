#!/usr/bin/env python3
"""H86N-GSST: gravity step-versus-compact-source shape test lane.

Preregistration: research/H86N_GSST_PREREGISTRATION.md (frozen before scoring).
Shared template only: vendor/gems57 grid/holdout/evaluate_holdout/writer/validate.
Features use ONLY native bands 13 (iso_grav_anom), 5 (iso_grav_anom_slope),
11 (iso_grav_anom_vg = +dg/drow_south), and 18 (iso_grav_anom_hg = +dg/dx_east);
no catalogue-derived feature exists in this lane, so the surface is fold-safe
by construction. Catalogue is used only for (a) holdout truth/masking via the
shared evaluator and (b) the protocol-standard >3px emission collar.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))
from gems57 import evaluate_holdout as EH, grid, holdout
from gems57.submission_writer import write_submission
from gems57.validate import validate
from scripts.protocol_preflight import require_like_for_like
from src.gems86_gsst.features import compute_gsst_features

BUDGET, SPACING, COLLAR = 37654, 2.8, 3.0
EXPECTED_TF_SHA = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)


def find_training_features() -> Path:
    for rel in ("data/bridge/training_features.tif", "data/training_features.tif", ".cache/training_features.tif"):
        p = ROOT / rel
        if p.is_file():
            digest = sha(p)
            if digest != EXPECTED_TF_SHA:
                raise ValueError(f"training_features.tif SHA mismatch at {rel}: {digest}")
            return p
    raise FileNotFoundError("training_features.tif not found in data/bridge, data, or .cache")


def greedy(support: np.ndarray, eligible: np.ndarray, budget: int, spacing: float) -> np.ndarray:
    ys, xs = np.nonzero(eligible)
    order = np.lexsort((xs, ys, -support[ys, xs]))
    ys, xs = ys[order], xs[order]
    cell = int(np.ceil(spacing))
    chosen: dict[tuple[int, int], list[tuple[int, int]]] = {}
    oy, ox = [], []
    r2 = spacing * spacing
    for y, x in zip(ys.tolist(), xs.tolist()):
        cy, cx = y // cell, x // cell
        ok = True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for yy, xx in chosen.get((cy + dy, cx + dx), ()):
                    if (yy - y) ** 2 + (xx - x) ** 2 < r2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            chosen.setdefault((cy, cx), []).append((y, x))
            oy.append(y)
            ox.append(x)
            if len(oy) >= budget:
                break
    dots = np.zeros(support.shape, bool)
    dots[oy, ox] = True
    return dots


def main() -> None:
    t0 = time.time()
    cert = require_like_for_like()
    print(f"preflight: {cert['status']} witness_rep={cert['witness_representation']}", flush=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    g = grid.load_grid(ROOT / "data/bridge")
    fp, cat = g.footprint, g.catalogue
    tf = find_training_features()
    with rasterio.open(tf) as s:
        slope = s.read(5).astype(np.float64)
        gy_south = s.read(11).astype(np.float64)
        grav = s.read(13).astype(np.float64)
        gx_east = s.read(18).astype(np.float64)

    out_bundle = compute_gsst_features(grav, slope, gy_south, gx_east, fp)
    feats = out_bundle["features"]
    surfaces = out_bundle["surfaces"]
    surface = surfaces["H86N_GSST"]

    dcat = ndi.distance_transform_edt(~cat)
    eligible = fp & (dcat > COLLAR)
    dots = {k: greedy(s, eligible, BUDGET, SPACING) for k, s in surfaces.items()}
    for k, d in dots.items():
        print(f"{k}: dots={int(d.sum())}", flush=True)

    folds, _ = holdout.buffered_component_draw(g, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    region = np.zeros(fp.shape, bool)
    hidden = np.zeros(fp.shape, bool)
    known = np.zeros(fp.shape, bool)
    for f in folds:
        region |= f["region"]
        hidden |= f["hidden_all"]
        known |= f["masked_known"]
    active = region & fp & ~known
    truth = active & hidden
    rng = np.random.default_rng(861486)
    p_idx = np.flatnonzero(truth.ravel())
    n_all = np.flatnonzero((active & ~truth).ravel())
    n_idx = rng.choice(n_all, size=min(300_000, n_all.size), replace=False)
    canary = {}
    for name, arr in feats.items():
        vals = np.r_[arr.ravel()[p_idx], arr.ravel()[n_idx]].astype(float)
        y = np.r_[np.ones(p_idx.size), np.zeros(n_idx.size)]
        r = rankdata(vals)
        auc = float((r[y == 1].sum() - p_idx.size * (p_idx.size + 1) / 2) / (p_idx.size * n_idx.size))
        canary[name] = round(auc, 4)
    print(f"canary={canary} withheld={int(truth.sum())}", flush=True)

    terms = {k: [] for k in dots}
    for f in folds:
        visible = cat & ~f["hidden_all"]
        elig_vis = fp & (ndi.distance_transform_edt(~visible) > COLLAR)
        for k, s in surfaces.items():
            fd = greedy(s, elig_vis, BUDGET, SPACING)
            _, bt = EH.evaluate(fd.astype(np.float32), f, fp, block_side=200)
            terms[k].append(bt)
    pooled = EH.pooled_summary(
        {k: np.sum(v, axis=0) for k, v in terms.items()},
        draws=1000,
        seed=861486,
        candidate="H86N_GSST",
    )
    cand = pooled["scores"]["H86N_GSST"]
    deltas = pooled["paired_differences"]
    print(f"holdout={cand} deltas={deltas}", flush=True)

    # Uniqueness: surface Spearman (300k footprint sample) + final-dot phi/overlap vs fleet+downloads.
    others = []
    for p in sorted((ROOT / "data/scored_fleet").glob("*.tif")):
        others.append((p.name, (load(p) > 0) & fp))
    for p in sorted((ROOT / "docs/downloads").glob("*.tif")):
        try:
            others.append((p.name, (load(p) > 0) & fp))
        except Exception:
            pass
    fy, fx = np.nonzero(fp)
    sidx = rng.choice(len(fy), size=min(300_000, len(fy)), replace=False)
    sy, sx = fy[sidx], fx[sidx]
    cand_s = rankdata(surface[sy, sx])
    uni = {
        "max_surface_spearman_abs": 0.0,
        "worst_surface": None,
        "max_dot_spearman_abs": 0.0,
        "worst_dot": None,
        "max_overlap3": 0.0,
        "worst_overlap": None,
        "n_registry_measured": len(others),
        "method": (
            "surface Spearman on shared 300k footprint sample vs every raster; "
            "dot phi (=Spearman, binary); overlap=frac candidate dots <=3px of "
            "other dots, dot-fields only (support<=20% footprint, PA-86-01)"
        ),
    }
    d = dots["H86N_GSST"]
    n_c = float(d.sum())
    N = float(d.size)
    from gems57.uniqueness import representation_class

    for name, m in others:
        mv = m[sy, sx].astype(float)
        if mv.std() > 0:
            rho_s = float(np.corrcoef(cand_s, rankdata(mv))[0, 1])
            if abs(rho_s) > abs(uni["max_surface_spearman_abs"]):
                uni.update(max_surface_spearman_abs=rho_s, worst_surface=name)
        n_o = float(m.sum())
        both = float((d & m).sum())
        den = np.sqrt(n_c * (N - n_c) * n_o * (N - n_o)) if n_o else 0.0
        rho = float((both * N - n_c * n_o) / den) if den else 0.0
        if abs(rho) > abs(uni["max_dot_spearman_abs"]):
            uni.update(max_dot_spearman_abs=rho, worst_dot=name)
        if m.any() and representation_class(int(m.sum()), int(fp.sum()))["kind"] == "dot_field":
            dd = ndi.distance_transform_edt(~m)
            ov = float((dd[d] <= 3.0).mean())
            if ov > uni["max_overlap3"]:
                uni.update(max_overlap3=ov, worst_overlap=name)
    print(f"uni={uni}", flush=True)

    gates = {
        "paired_ci_low_gt_0_vs_E0": bool(deltas["E0_raw_grav_slope"]["ci95"][0] > 0),
        "paired_ci_low_gt_0_vs_E2": bool(deltas["E2_compact_curv"]["ci95"][0] > 0),
        "beats_same_split_holdout_best_0.1599": bool(cand["dti"] > 0.1599),
        "canary_all_auc_le_0.90": bool(all(v <= 0.90 for v in canary.values())),
        "surface_spearman_abs_le_0.90": bool(abs(uni["max_surface_spearman_abs"]) <= 0.90),
        "dot_spearman_abs_le_0.90": bool(abs(uni["max_dot_spearman_abs"]) <= 0.90),
        "overlap3_le_0.70": bool(uni["max_overlap3"] <= 0.70),
        "budget_exact": bool(int(d.sum()) == BUDGET),
        "zero_dots_on_catalogue": bool(not (d & cat).any()),
    }
    promote = all(gates.values())
    verdict = "promote" if promote else "negative"
    stem = f"gems86-h86n-gsst-stepshape-37654dots-{stamp}"
    note = (
        "H86N-GSST gravity step-vs-compact shape dotted 37654; HOLDOUT-DTI in run card; "
        + ("gates pass" if promote else "DO NOT SUBMIT")
    )[:140]
    out = ROOT / "docs/downloads" / f"{stem}-zeros.tif"
    pred = np.where(fp, d.astype(np.float32), np.float32(0.0))
    write_submission(
        out,
        pred,
        ROOT / "data/bridge/sample_submission.tif",
        fp,
        note=note,
        name=stem[:140],
        catalogue=cat,
        metadata={"lane": "H86N-GSST", "verdict": verdict},
    )
    val = validate(out, fp, cat)
    card = {
        "schema": "gems86.run-card.v1",
        "lane_id": "H86N-GSST",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": (
            "An extended buried basement fault step maintains one-sided cross-strike "
            "horizontal gravity gradient flanks and low radial unit-normal divergence "
            "(Bands 13, 5, 11, 18), whereas compact 3-D intrusive plugs and symmetric "
            "dike bumps reverse flank gradient sign or exhibit high radial curvature."
        ),
        "mechanism": (
            "Multi-scale (sigma=3,6 px) flank-gradient sign persistence x potential step "
            "drop x along-strike coherence x (1 - 0.5*compact radial divergence) on "
            "verified signed gravity gradient vector (+Band 18 east, +Band 11 south); "
            "greedy 2.8px Poisson-disc emission, 37,654 dots, >3px off catalogue "
            "(visible-only collar in holdout folds)."
        ),
        "named_non_fault_mimic": (
            "Elongated lithologic or intrusive contacts and basin-margin alluvial-fan "
            "density boundaries producing a one-sided density step without brittle fault offset."
        ),
        "holdout": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "withheld_positive_pixels": int(truth.sum()),
            "candidate": cand,
            "controls": {
                "E0_raw_grav_slope": pooled["scores"]["E0_raw_grav_slope"],
                "E2_compact_curv": pooled["scores"]["E2_compact_curv"],
            },
            "paired_differences_vs_candidate": deltas,
        },
        "leakage_canary": {
            "single_feature_auc": canary,
            "gate_le_0.90": gates["canary_all_auc_le_0.90"],
        },
        "correlation_overlap_vs_registry": uni,
        "preflight_PA-86-01": {
            "status": cert["status"],
            "literal_reading_blocked": cert["literal_reading_blocked"],
            "witness_representation": cert["witness_representation"],
        },
        "gates": gates,
        "raster_sha256": sha(out),
        "validator": val if isinstance(val, dict) else str(val),
        "submission_name": stem,
        "submission_note_le140": note,
        "note_chars": len(note),
        "verdict": verdict,
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "dots": int(d.sum()),
        "input_sha256": {"training_features.tif": sha(tf)},
        "runtime_s": round(time.time() - t0, 1),
    }
    (ROOT / "docs/evidence/h86n-gsst-run-card.json").write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps({"file": out.name, "sha256": card["raster_sha256"], "verdict": verdict, "gates": gates}, indent=2))


if __name__ == "__main__":
    main()
