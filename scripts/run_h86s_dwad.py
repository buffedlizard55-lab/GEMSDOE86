#!/usr/bin/env python3
"""Execute Preregistered Lane H86S-DWAD (<= 3 Arms, Strict 12-px-Eroded 4-Fold LOQO).

Method lane (frozen in research/H86S_DWAD_PREREGISTRATION.json):
  Detectability-Weighted Exposure-Deconfounded PU (w_neg = O(x)^1.25) +
  Downslope Canyon-Mouth Fluvial Knickzone Back-Projection (KNDS) +
  Sub-Clay-Cap Hydrothermal Feeder-Margin Disjunction +
  Prior-Weighted Dual-Regime Stepover-Preserving 6-Ring Dinkelbach-CELF.

Following repository-wide builder gating, ``main()`` calls
``protocol_preflight.require_feasible()`` before any work.
"""

from __future__ import annotations

from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
VENDOR = ROOT / "vendor"
for _p in (str(ROOT), str(SRC), str(VENDOR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gems57 import grid, holdout
from gems86_dwad import (
    DWADConfig,
    DWAD_ABLATION_NAMES,
    DWAD_CONT_NAMES,
    DWAD_STATIC_NAMES,
    build_dwad_static_stack,
    compute_dwad_continuation_fields,
    fit_predict_loqo_dwad_surfaces,
    verify_dwad_input_contract,
)
from gems86_stdp.dinkelbach_celf import (
    dinkelbach_celf_allocate_dots,
    static_ek_spacing_allocate,
)
from gems86_stdp.model import rank01_on_mask
from scripts.protocol_preflight import require_like_for_like
from scripts.run_h86k_stdp import (
    BUDGET,
    COLLAR_PX,
    D28_TIF,
    EH,
    EV_DIR,
    EXT_DIR,
    FEATURE_TIF,
    H33_TIF,
    SPACING_PX,
    audit_informative_dot_field_firings,
    evaluate_sgmc_proxy,
    load_binary_tif,
    prepare_canary_indices,
    registry_summary,
    run_chance_check,
    run_registry_check,
    score_canary_array,
    sha256,
    verify_all_inputs,
    write_candidate,
)

CACHE_DIR = ROOT / ".cache/h86s_dwad"
LIVE_PEER_CACHE = ROOT / ".cache/focus9_and_siblings_20261027"
PREREG_PATH = ROOT / "research/H86S_DWAD_PREREGISTRATION.json"
LOG_PATH = CACHE_DIR / "run_h86s_dwad.log"


def _log(msg: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%SZ')}] {msg}"
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    try:
        print(line, flush=True)
    except BrokenPipeError:
        pass


def _quadrant_regions(
    fp: np.ndarray, vis_mask: np.ndarray
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    q_grid = holdout.quadrant_ids(fp)
    names = ("NW", "NE", "SW", "SE")
    return [(names[q], fp & (q_grid == q), vis_mask) for q in range(4)]


def _check_live_peers_surface(
    bounded_surface: np.ndarray, fp: np.ndarray
) -> dict[str, object]:
    """Check sampled continuous Spearman rho against all cached live Focus-9 & sibling org rasters."""
    rng = np.random.default_rng(20261027)
    fp_idx = np.flatnonzero(fp)
    sample_idx = rng.choice(fp_idx, size=min(120_000, fp_idx.size), replace=False)
    s_vec = bounded_surface.ravel()[sample_idx]
    worst_rho = 0.0
    worst_name = ""
    checked = 0
    firings = 0
    if LIVE_PEER_CACHE.is_dir():
        for p in sorted(LIVE_PEER_CACHE.glob("*.tif")):
            try:
                with rasterio.open(p) as ds:
                    if ds.count != 1 or ds.shape != fp.shape:
                        continue
                    arr = ds.read(1)
            except Exception:
                continue
            v = np.nan_to_num(arr.ravel()[sample_idx].astype(np.float32), nan=0.0)
            if float(np.std(v)) < 1e-12:
                continue
            rho = abs(float(spearmanr(s_vec, v).statistic))
            checked += 1
            if rho > worst_rho:
                worst_rho = rho
                worst_name = p.name
            if rho > 0.90:
                firings += 1
    return {
        "live_peer_rasters_checked": checked,
        "worst_abs_spearman": round(worst_rho, 6),
        "worst_peer": worst_name,
        "firings_over_0p90": firings,
    }


def _check_live_peers_dots(
    final_dots: np.ndarray, fp: np.ndarray
) -> dict[str, object]:
    """Check 3-px forward dot overlap against all <=90k discrete live Focus-9 & sibling org rasters."""
    mine_pts = np.column_stack(np.nonzero(final_dots & fp))
    rows: list[tuple[float, int, str]] = []
    if LIVE_PEER_CACHE.is_dir():
        for p in sorted(LIVE_PEER_CACHE.glob("*.tif")):
            try:
                with rasterio.open(p) as ds:
                    if ds.count != 1 or ds.shape != fp.shape:
                        continue
                    arr = ds.read(1)
            except Exception:
                continue
            supp = np.isfinite(arr) & (arr >= 0.5) & fp
            nd = int(supp.sum())
            if nd == 0 or nd > 90_000:
                continue
            tree = cKDTree(np.column_stack(np.nonzero(supp)))
            dists, _ = tree.query(mine_pts, distance_upper_bound=3.0 + 1e-9, workers=-1)
            ov3 = float((dists <= 3.0).mean())
            rows.append((ov3, nd, p.name))
    rows.sort(reverse=True)
    firings = sum(1 for ov3, _, _ in rows if ov3 > 0.70)
    top5 = [
        {"overlap_3px": round(ov3, 6), "n_dots": nd, "peer_file": nm}
        for ov3, nd, nm in rows[:5]
    ]
    return {
        "discrete_le_90k_live_peers_checked": len(rows),
        "firings_over_0p70": firings,
        "worst_overlap_3px": round(rows[0][0], 6) if rows else 0.0,
        "worst_peer_file": rows[0][2] if rows else None,
        "top_5_overlaps": top5,
    }


def run_pa86_lane() -> int:
    # Imported callers must obey the same literal stop as the CLI.
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    t0 = time.time()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EV_DIR.mkdir(parents=True, exist_ok=True)
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    _log("[1/6] Verifying preregistration, SHA-256 inputs, and like-for-like preflight...")
    if not PREREG_PATH.is_file():
        raise RuntimeError(f"Missing frozen preregistration: {PREREG_PATH}")
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    if prereg.get("lane_id") != "H86S-DWAD" or len(prereg["experiment_budget"]["planned_arms"]) != 3:
        raise RuntimeError("Invalid H86S-DWAD preregistration")

    preflight = require_like_for_like()
    input_hashes = verify_all_inputs()
    qc_contract = verify_dwad_input_contract(EXT_DIR)

    g = grid.load_grid(ROOT / "data/bridge")
    fp = np.asarray(g.footprint, dtype=bool)
    cat = np.asarray(g.catalogue, dtype=bool)

    _log("[2/6] Building 24 DWAD static planes + 6 local ablation planes + survey observability...")
    dwad_mm_path = CACHE_DIR / "dwad_static24.npy"
    abl_mm_path = CACHE_DIR / "dwad_abl6.npy"
    extras_npz = CACHE_DIR / "dwad_extras.npz"
    if dwad_mm_path.is_file() and abl_mm_path.is_file() and extras_npz.is_file():
        ex = np.load(extras_npz)
        stack = {
            "X_dwad": np.load(dwad_mm_path, mmap_mode="r"),
            "X_abl": np.load(abl_mm_path, mmap_mode="r"),
            "observability": ex["observability"],
            "dilaterate_b8": ex["dilaterate_b8"],
            "L_dwad": ex["L_dwad"],
            "valid": fp,
            "accessed_columns": json.loads(str(ex["accessed_columns_json"])),
        }
    else:
        stack = build_dwad_static_stack(
            FEATURE_TIF,
            EXT_DIR,
            out_dwad_path=dwad_mm_path,
            out_ablation_path=abl_mm_path,
            footprint=fp,
        )
        np.savez(
            extras_npz,
            observability=stack["observability"],
            dilaterate_b8=stack["dilaterate_b8"],
            L_dwad=stack["L_dwad"],
            accessed_columns_json=json.dumps(stack["accessed_columns"]),
        )
    static_sha256 = sha256(dwad_mm_path)
    _log(f"  Static stack ready ({time.time() - t0:.1f}s) | sha256={static_sha256[:16]}")

    _log("[3/6] Running symmetric single-feature leakage canary & 3 preregistered arms on gems57-pooled-hide-v2...")
    folds, _ = holdout.buffered_component_draw(
        g, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12
    )
    p_idx, n_idx, y_canary = prepare_canary_indices(folds, fp)
    canary: dict[str, dict] = {}
    X_dwad = stack["X_dwad"]
    X_abl = stack["X_abl"]

    for i, fname in enumerate(DWAD_STATIC_NAMES):
        pl = X_dwad[i].ravel()
        canary[fname] = score_canary_array(
            np.r_[pl[p_idx], pl[n_idx]].astype(np.float64), y_canary
        )
    for extra_name, extra_arr in (
        ("survey_observability_O_x", stack["observability"]),
        ("L_dwad_corroboration_prior", stack["L_dwad"]),
    ):
        pl = extra_arr.ravel()
        canary[extra_name] = score_canary_array(
            np.r_[pl[p_idx], pl[n_idx]].astype(np.float64), y_canary
        )
    for i, fname in enumerate(DWAD_ABLATION_NAMES):
        pl = X_abl[i].ravel()
        canary[fname] = score_canary_array(
            np.r_[pl[p_idx], pl[n_idx]].astype(np.float64), y_canary
        )

    vis_holdout = np.asarray(folds[0]["visible"], dtype=bool) & fp
    for f in folds[1:]:
        if not np.array_equal(np.asarray(f["visible"], dtype=bool) & fp, vis_holdout):
            raise AssertionError("Expected shared global visible mask across buffered folds")

    cont_ho, d_vis_ho = compute_dwad_continuation_fields(vis_holdout, fp)
    for k, cname in enumerate(DWAD_CONT_NAMES):
        pl = cont_ho[k].ravel()
        canary[f"fold_visible_{cname}"] = score_canary_array(
            np.r_[pl[p_idx], pl[n_idx]].astype(np.float64), y_canary
        )
    iso_ho = np.exp(-d_vis_ho / 11.0).ravel()
    canary["fold_visible_abl_isotropic_tip_decay"] = score_canary_array(
        np.r_[iso_ho[p_idx], iso_ho[n_idx]].astype(np.float64), y_canary
    )
    del cont_ho, iso_ho
    gc.collect()

    flagged = [k for k, v in canary.items() if v["leakage_flag"]]
    if flagged:
        raise RuntimeError(f"STOP: Leakage canary > 0.90 fired on: {flagged}")
    max_canary_name, max_canary = max(
        canary.items(), key=lambda kv: kv[1]["discriminative_auc"]
    )
    _log(
        f"  Canary PASS ({len(canary)} planes): worst={max_canary_name} "
        f"(disc_auc={max_canary['discriminative_auc']:.4f} <= 0.90)"
    )

    fp_cfg = prereg["frozen_parameters"]
    cfg = DWADConfig(
        collar_px=float(fp_cfg["catalogue_collar_px"]),
        erode_train_px=int(fp_cfg["spatial_cv_erosion_px"]),
        observability_gamma=float(fp_cfg["observability_gamma"]),
        hgb_max_depth=int(fp_cfg["hgb_max_depth"]),
        hgb_max_iter=int(fp_cfg["hgb_max_iter"]),
        hgb_learning_rate=float(fp_cfg["hgb_learning_rate"]),
        hgb_min_samples_leaf=int(fp_cfg["hgb_min_samples_leaf"]),
        hgb_l2_regularization=float(fp_cfg["hgb_l2_regularization"]),
        dual_regime_blind_floor_weight=float(fp_cfg["dual_regime_blind_floor_weight"]),
        quadrant_pooled_blend_alpha=float(fp_cfg["quadrant_pooled_blend_alpha"]),
    )

    arm_e1 = "E1_dwad_deconfounded_dualregime_dcelf"
    arm_e2 = "E2_dwad_zero_catalogue_blind_dcelf"
    arm_e3 = "E3_unweighted_unadvected_local_ablation"
    arm_names = (arm_e1, arm_e2, arm_e3)

    oof_ho_cache = CACHE_DIR / "oof_holdout.npz"
    if oof_ho_cache.is_file():
        z_ho = np.load(oof_ho_cache)
        oof_ho = {k: z_ho[k] for k in ("E1_surface", "E2_surface", "E3_surface")}
    else:
        ho_regions = _quadrant_regions(fp, vis_holdout)
        oof_ho = fit_predict_loqo_dwad_surfaces(
            X_dwad,
            X_abl,
            stack["L_dwad"],
            stack["observability"],
            stack["dilaterate_b8"],
            ho_regions,
            fp,
            cfg,
        )
        np.savez(
            oof_ho_cache,
            E1_surface=oof_ho["E1_surface"],
            E2_surface=oof_ho["E2_surface"],
            E3_surface=oof_ho["E3_surface"],
        )

    allowed_ho = fp & (d_vis_ho > COLLAR_PX)
    del d_vis_ho

    dink_iters = int(fp_cfg["dinkelbach_outer_iters"])
    dc_e1_ho = dinkelbach_celf_allocate_dots(
        oof_ho["E1_surface"],
        allowed_ho,
        known_faults=vis_holdout,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
        outer_iterations=dink_iters,
    )
    dc_e2_ho = dinkelbach_celf_allocate_dots(
        oof_ho["E2_surface"],
        allowed_ho,
        known_faults=vis_holdout,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
        outer_iterations=dink_iters,
    )
    dots_e3_ho = static_ek_spacing_allocate(
        oof_ho["E3_surface"],
        allowed_ho,
        known_faults=vis_holdout,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
    )

    d28_mask = load_binary_tif(D28_TIF) & fp
    h33_mask = load_binary_tif(H33_TIF) & fp
    dots_d28_ho = d28_mask & allowed_ho
    dots_h33_ho = h33_mask & allowed_ho

    arm_fold_terms: dict[str, list[np.ndarray]] = {
        a: [] for a in (*arm_names, "R0_D28_visible_collar", "H33_visible_collar")
    }
    holdout_per_fold: dict[str, dict] = {
        a: {} for a in (*arm_names, "R0_D28_visible_collar", "H33_visible_collar")
    }

    for f in folds:
        qname = f["name"]
        for key, pred_dots in (
            (arm_e1, dc_e1_ho.dots),
            (arm_e2, dc_e2_ho.dots),
            (arm_e3, dots_e3_ho),
            ("R0_D28_visible_collar", dots_d28_ho),
            ("H33_visible_collar", dots_h33_ho),
        ):
            res_k, b_k = EH.evaluate(pred_dots.astype(np.float32), f, fp, block_side=200)
            arm_fold_terms[key].append(b_k)
            holdout_per_fold[key][qname] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": EH.VERSION,
                "dti": res_k["dti"],
                "n_truth": res_k["n_truth"],
                "emitted": res_k["n_emitted"],
            }
        _log(
            f"  Fold {qname}: E1={holdout_per_fold[arm_e1][qname]['dti']:.4f} | "
            f"E2={holdout_per_fold[arm_e2][qname]['dti']:.4f} | "
            f"E3={holdout_per_fold[arm_e3][qname]['dti']:.4f} | "
            f"D28={holdout_per_fold['R0_D28_visible_collar'][qname]['dti']:.4f} | "
            f"H33={holdout_per_fold['H33_visible_collar'][qname]['dti']:.4f}"
        )

    del oof_ho, dc_e1_ho, dc_e2_ho, dots_e3_ho
    gc.collect()

    terms_by_arm = {k: np.sum(v, axis=0) for k, v in arm_fold_terms.items()}
    pooled = EH.pooled_summary(
        terms_by_arm,
        draws=1000,
        seed=862027,
        candidate=arm_e1,
    )
    e1_score = pooled["scores"][arm_e1]
    e2_score = pooled["scores"][arm_e2]
    e3_score = pooled["scores"][arm_e3]
    delta_vs_e3 = pooled["paired_differences"][arm_e3]
    beats_e3_ci = bool(delta_vs_e3["ci95"][0] > 0.0)
    _log(
        f"  POOLED HOLDOUT-DTI: E1={e1_score['dti']:.4f} {e1_score['ci95']} | "
        f"E2={e2_score['dti']:.4f} {e2_score['ci95']} | "
        f"E3={e3_score['dti']:.4f} {e3_score['ci95']} | "
        f"E1-E3={delta_vs_e3['delta']:+.4f} {delta_vs_e3['ci95']} (beats_E3_CI={beats_e3_ci})"
    )

    _log("[4/6] Fitting deployment 4-fold OOF surfaces & checking pre-placement Spearman rho vs full registry + live peers...")
    full_cfg = DWADConfig(
        collar_px=cfg.collar_px,
        erode_train_px=cfg.erode_train_px,
        observability_gamma=cfg.observability_gamma,
        hgb_max_depth=cfg.hgb_max_depth,
        hgb_max_iter=cfg.hgb_max_iter,
        hgb_learning_rate=cfg.hgb_learning_rate,
        hgb_min_samples_leaf=cfg.hgb_min_samples_leaf,
        hgb_l2_regularization=cfg.hgb_l2_regularization,
        dual_regime_blind_floor_weight=cfg.dual_regime_blind_floor_weight,
        quadrant_pooled_blend_alpha=cfg.quadrant_pooled_blend_alpha,
        seed=cfg.seed + 2000,
    )
    oof_full_cache = CACHE_DIR / "oof_full.npz"
    if oof_full_cache.is_file():
        z_fu = np.load(oof_full_cache)
        oof_full = {k: z_fu[k] for k in ("E1_surface", "E2_surface", "E3_surface")}
    else:
        full_regions = _quadrant_regions(fp, cat & fp)
        oof_full = fit_predict_loqo_dwad_surfaces(
            X_dwad,
            X_abl,
            stack["L_dwad"],
            stack["observability"],
            stack["dilaterate_b8"],
            full_regions,
            fp,
            full_cfg,
        )
        np.savez(
            oof_full_cache,
            E1_surface=oof_full["E1_surface"],
            E2_surface=oof_full["E2_surface"],
            E3_surface=oof_full["E3_surface"],
        )
    surf_e1_full = oof_full["E1_surface"]
    surf_e2_full = oof_full["E2_surface"]
    surf_e3_full = oof_full["E3_surface"]
    del oof_full, stack
    gc.collect()

    bounded_e1 = rank01_on_mask(surf_e1_full, fp)
    e1_surf_npy = CACHE_DIR / "h86s_dwad_e1_surface.npy"
    np.save(e1_surf_npy, bounded_e1)
    e1_surf_sha = sha256(e1_surf_npy)
    surface_report_path = EV_DIR / "h86s-dwad-registry-surface.json"
    if (
        surface_report_path.is_file()
        and json.loads(surface_report_path.read_text(encoding="utf-8")).get(
            "candidate_source_sha256"
        )
        == e1_surf_sha
    ):
        surface_report = json.loads(surface_report_path.read_text(encoding="utf-8"))
        surface_rc = 0 if surface_report.get("surface_gate_pass") is True else 2
    else:
        surface_report, surface_rc = run_registry_check(
            e1_surf_npy, surface_report_path, surface=True
        )
    rho_firings = int(
        surface_report.get("two_phase", {}).get("literal_reading", {}).get("rho_firings", 999)
    )
    live_peer_surf = _check_live_peers_surface(bounded_e1, fp)
    _log(
        f"  E1 pre-placement surface scan: registry_measured={surface_report.get('registry_rasters_measured')}, "
        f"worst_spearman={surface_report['shared_summary']['worst_spearman_full_footprint']:.4f} "
        f"(rho_firings={rho_firings}), live_peer_worst_rho={live_peer_surf['worst_abs_spearman']:.4f} "
        f"({live_peer_surf['live_peer_rasters_checked']} live peer TIFFs)"
    )
    if rho_firings != 0 or int(live_peer_surf["firings_over_0p90"]) != 0:
        raise RuntimeError("STOP BEFORE PLACEMENT: Surface Spearman rho > 0.90 fired")

    _log("[5/6] Placing 37,654 Dinkelbach-CELF dots & checking full registry + live Focus-9/sibling 3-px overlap + SGMC-PROXY-DTI...")
    dcat = ndi.distance_transform_edt(~(cat & fp))
    allowed_full = fp & (dcat > COLLAR_PX)
    q_grid = holdout.quadrant_ids(fp)

    dc_e1_full = dinkelbach_celf_allocate_dots(
        surf_e1_full,
        allowed_full,
        known_faults=cat & fp,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
        outer_iterations=dink_iters,
    )
    dc_e2_full = dinkelbach_celf_allocate_dots(
        surf_e2_full,
        allowed_full,
        known_faults=cat & fp,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
        outer_iterations=dink_iters,
    )
    dots_e3_full = static_ek_spacing_allocate(
        surf_e3_full,
        allowed_full,
        known_faults=cat & fp,
        valid=fp,
        budget=BUDGET,
        min_spacing_px=SPACING_PX,
    )

    def _radial_and_quad_profile(dots_bool: np.ndarray) -> dict[str, object]:
        m_d = dots_bool & fp
        dc_vals = dcat[m_d]
        q_shares = {
            nm: round(float((m_d & (q_grid == qi)).sum() / max(int(m_d.sum()), 1)), 4)
            for qi, nm in enumerate(("NW", "NE", "SW", "SE"))
        }
        return {
            "n_dots": int(m_d.sum()),
            "min_dcat_px": round(float(dc_vals.min()), 4),
            "median_dcat_m": round(float(np.median(dc_vals) * 100.0), 2),
            "frac_3_to_10px_near_halo": round(float((dc_vals <= 10.0).mean()), 4),
            "frac_gt_10px_far_field_gt_1km": round(float((dc_vals > 10.0).mean()), 4),
            "quadrant_dot_shares": q_shares,
        }

    e1_profile = _radial_and_quad_profile(dc_e1_full.dots)
    e2_profile = _radial_and_quad_profile(dc_e2_full.dots)
    _log(f"  E1 profile: {e1_profile}")
    _log(f"  E2 profile: {e2_profile}")

    e1_dots_npy = CACHE_DIR / "h86s_dwad_e1_dots.npy"
    np.save(e1_dots_npy, dc_e1_full.dots.astype(np.float32))
    e1_dots_sha = sha256(e1_dots_npy)
    dots_report_path = EV_DIR / "h86s-dwad-registry-final-dots.json"
    if (
        dots_report_path.is_file()
        and json.loads(dots_report_path.read_text(encoding="utf-8")).get(
            "candidate_source_sha256"
        )
        == e1_dots_sha
    ):
        dots_report = json.loads(dots_report_path.read_text(encoding="utf-8"))
        dots_rc = 0 if dots_report.get("final_dots_gate_pass") is True else 2
    else:
        dots_report, dots_rc = run_registry_check(e1_dots_npy, dots_report_path, surface=False)
    informative_audit = audit_informative_dot_field_firings(dots_report, fp, cat)
    live_peer_dots = _check_live_peers_dots(dc_e1_full.dots, fp)
    _log(
        f"  E1 final-dot scan: registry_measured={dots_report.get('registry_rasters_measured')}, "
        f"discrete_le_90k_firings={informative_audit['discrete_le_90k_firings_over_0p70']}, "
        f"worst_le_90k_overlap={informative_audit['worst_discrete_le_90k_overlap_3px']:.4f}, "
        f"live_peer_firings={live_peer_dots['firings_over_0p70']} "
        f"(worst_live={live_peer_dots['worst_overlap_3px']:.4f} vs {live_peer_dots['worst_peer_file']})"
    )

    e1_rule1_duplicate_stop: dict | None = None
    if (
        int(informative_audit["discrete_le_90k_firings_over_0p70"]) > 0
        or int(live_peer_dots["firings_over_0p70"]) > 0
    ):
        e1_rule1_duplicate_stop = {
            "arm_halted": arm_e1,
            "tif_serialized_for_e1": False,
            "discrete_le_90k_firings_over_0p70": int(
                informative_audit["discrete_le_90k_firings_over_0p70"]
            ),
            "worst_discrete_le_90k_overlap_3px": informative_audit[
                "worst_discrete_le_90k_overlap_3px"
            ],
            "worst_discrete_le_90k_submission": informative_audit.get(
                "worst_discrete_le_90k_submission"
            ),
            "live_peer_firings_over_0p70": int(live_peer_dots["firings_over_0p70"]),
            "worst_live_peer_overlap_3px": live_peer_dots["worst_overlap_3px"],
        }
        _log("  Rule-1 stop triggered on E1 -> pivoting cleanly to preregistered blind E2 (0 extra experiments)...")
        serialized_arm_key = arm_e2
        final_dots = dc_e2_full.dots
        active_profile = e2_profile

        bounded_e2 = rank01_on_mask(surf_e2_full, fp)
        e2_surf_npy = CACHE_DIR / "h86s_dwad_e2_surface.npy"
        np.save(e2_surf_npy, bounded_e2)
        surface_report_path = EV_DIR / "h86s-dwad-e2-registry-surface.json"
        surface_report, surface_rc = run_registry_check(e2_surf_npy, surface_report_path, surface=True)
        live_peer_surf = _check_live_peers_surface(bounded_e2, fp)
        if (
            int(surface_report.get("two_phase", {}).get("literal_reading", {}).get("rho_firings", 999)) != 0
            or int(live_peer_surf["firings_over_0p90"]) != 0
        ):
            raise RuntimeError("STOP BEFORE PLACEMENT: E2 surface Spearman rho > 0.90 fired")

        e2_dots_npy = CACHE_DIR / "h86s_dwad_e2_dots.npy"
        np.save(e2_dots_npy, final_dots.astype(np.float32))
        dots_report_path = EV_DIR / "h86s-dwad-e2-registry-final-dots.json"
        dots_report, dots_rc = run_registry_check(e2_dots_npy, dots_report_path, surface=False)
        informative_audit = audit_informative_dot_field_firings(dots_report, fp, cat)
        live_peer_dots = _check_live_peers_dots(final_dots, fp)
        active_dots_npy = e2_dots_npy
    else:
        serialized_arm_key = arm_e1
        final_dots = dc_e1_full.dots
        active_profile = e1_profile
        active_dots_npy = e1_dots_npy

    if (
        int(informative_audit["discrete_le_90k_firings_over_0p70"]) > 0
        or int(live_peer_dots["firings_over_0p70"]) > 0
    ):
        raise RuntimeError("STOP BEFORE SERIALIZATION: Discrete <=90k 3-px overlap > 0.70 fired")

    shared_dots = dots_report.get("shared_summary", {})
    if not (
        shared_dots.get("byte_unique_among_checked") is True
        and shared_dots.get("pixel_unique_among_checked") is True
    ):
        raise RuntimeError("STOP: Candidate is byte- or pixel-identical to an existing raster")

    chance_path = EV_DIR / "h86s-dwad-pa86-chance-overlap.json"
    chance = run_chance_check(dots_report_path, active_dots_npy, chance_path)

    sgmc_preds: dict[str, np.ndarray] = {
        arm_e1: dc_e1_full.dots,
        arm_e2: dc_e2_full.dots,
        arm_e3: dots_e3_full,
        "H33_GEMSDOE32_as_is": h33_mask,
        "D28_GEMSDOE28_as_is": d28_mask,
    }
    for label_glob, label_key in (
        ("gems86-h86p-tcwb-*.tif", "H86P_TCWB_37654_as_is"),
        ("gems86-h86q-bfra-*.tif", "H86Q_BFRA_37654_as_is"),
        ("gems86-h86r-sfg-*.tif", "H86R_SFG_37654_as_is"),
    ):
        m_tifs = sorted((ROOT / "docs/downloads").glob(label_glob))
        if m_tifs:
            sgmc_preds[label_key] = load_binary_tif(m_tifs[-1]) & fp
    if LIVE_PEER_CACHE.is_dir():
        g27_h31 = sorted(LIVE_PEER_CACHE.glob("*GEMSDOE27*h31-drcg*.tif"))
        if g27_h31:
            sgmc_preds["GEMSDOE27_H31_0p2250_as_is"] = load_binary_tif(g27_h31[0]) & fp

    sgmc_diag = evaluate_sgmc_proxy(sgmc_preds, fp, cat, candidate_key=serialized_arm_key)
    _log(
        "  SGMC-PROXY-DTI: "
        + json.dumps({k: round(v["dti"], 4) for k, v in sgmc_diag["scores"].items()})
    )

    _log("[6/6] Serializing validated [0, 1] -zeros GeoTIFF + single-TIFF ZIP + receipt + run card...")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
    arm_slug = "dcelf" if serialized_arm_key == arm_e1 else "blind-dcelf"
    name = f"gems86-h86s-dwad-{arm_slug}-{int(final_dots.sum())}dots-{stamp}-{digest8}-zeros"

    ser_hold = pooled["scores"][serialized_arm_key]
    ser_sgmc = sgmc_diag["scores"][serialized_arm_key]
    note = (
        f"H86S-DWAD {arm_slug.upper()} ObsPU+KNDS+ClayFeeder LOQO "
        f"(HOLD {ser_hold['dti']:.4f}, SGMC {ser_sgmc['dti']:.4f}); "
        f"witness stop; DO NOT SUBMIT"
    )[:140]

    receipt = write_candidate(
        final_dots,
        g,
        name,
        note,
        metadata={
            "lane_id": "H86S-DWAD",
            "serialized_arm": serialized_arm_key,
            "preregistration": "research/H86S_DWAD_PREREGISTRATION.json",
            "holdout_dti": ser_hold["dti"],
            "sgmc_proxy_dti": ser_sgmc["dti"],
        },
    )

    val_out = receipt["independent_disk_validation"]
    literal_witness_pass = bool(
        dots_rc == 0
        and dots_report.get("final_dots_gate_pass") is True
        and dots_report.get("literal_gate_pass") is True
    )
    gates = {
        "format_15_of_15_and_unit_interval": bool(
            val_out.get("valid") is True
            and val_out.get("nan_count") == 0
            and val_out.get("inf_count") == 0
            and val_out.get("min_val", -1.0) >= 0.0
            and val_out.get("max_val", 2.0) <= 1.0
        ),
        "leakage_canary_max_sym_auc_le_0p90": bool(not flagged),
        "surface_spearman_vs_registry_and_live_peers_le_0p90": True,
        "discrete_le_90k_3px_overlap_vs_registry_and_live_peers_le_0p70": True,
        "e1_beats_e3_ablation_paired_ci95_low_gt_0": beats_e3_ci,
        "sgmc_proxy_beats_random_null_0p0754": bool(ser_sgmc["dti"] > 0.0754),
        "sgmc_proxy_beats_gemsdoe32_h33_0p0937": bool(
            ser_sgmc["dti"] > sgmc_diag["scores"]["H33_GEMSDOE32_as_is"]["dti"]
        ),
        "full_655_registry_restored_and_measured": bool(
            dots_report.get("registry_complete_for_index") is True
            and dots_report.get("inventory_rasters_missing") == []
        ),
        "literal_full_support_witness_17gemsdoe_le_0p70": literal_witness_pass,
    }

    run_card = {
        "schema": "gems86.lane_run_card.v1",
        "lane_id": "H86S-DWAD",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_branch": "arena/8074001e-gemsdoe86",
        "preregistration": {
            "path": "research/H86S_DWAD_PREREGISTRATION.json",
            "markdown": "research/H86S_DWAD_PREREGISTRATION.md",
            "hypotheses_registry": "registry/h86s_dwad_hypotheses_20261027.json",
            "sha256": sha256(PREREG_PATH),
        },
        "hypothesis": (
            "Detectability-Weighted Exposure-Deconfounded PU (w_neg = O(x)^1.25) + "
            "Downslope Canyon-Mouth Fluvial Knickzone Back-Projection (KNDS, 800-1,500 m "
            "downslope onto Band 15 alluvial-apex steps) + Sub-Clay-Cap Hydrothermal "
            "Feeder-Margin Disjunction (lateral gradient margin of Band 17 cond_surf x "
            "magnetite-oxidation Band 2 RTP trough x Band 5 gravity step x up-head GDR #1391 "
            "2-m probe/sinter/geothermometer plumes) + Prior-Weighted Dual-Regime "
            "Stepover-Preserving 6-Ring Bernoulli Dinkelbach-CELF at 37,654 dots."
        ),
        "mechanism": {
            "static_features": list(DWAD_STATIC_NAMES),
            "fold_visible_continuation_features": list(DWAD_CONT_NAMES),
            "ablation_control_features": list(DWAD_ABLATION_NAMES),
            "static_stack_sha256": static_sha256,
            "gdr_accessed_columns": qc_contract.get("verified_native_bands"),
            "serialized_arm": serialized_arm_key,
            "e1_profile": e1_profile,
            "e2_profile": e2_profile,
            "active_serialized_profile": active_profile,
        },
        "named_non_fault_mimic": (
            "(1) Unfaulted erosional bedrock-pediment canyon mouths and resistant welded-tuff "
            "ledges -> suppressed by requiring positive downslope Band 15 basin-fill thickening "
            "and cross-canyon strike persistence; (2) Flat conductive saline playa evaporite pans "
            "and Pleistocene Lake Lahontan (~1,330 m / ~1,205 m) shorelines -> suppressed by "
            "targeting lateral conductance margins corroborated by potential-field steps plus "
            "explicit Lahontan contour and GeoDAWN block-seam vetoes."
        ),
        "preflight_receipt": preflight,
        "input_sha256": input_hashes,
        "leakage_canary": canary,
        "leakage_canary_summary": {
            "features_tested": len(canary),
            "max_discriminative_auc_feature": max_canary_name,
            "max_discriminative_auc": max_canary["discriminative_auc"],
            "threshold": 0.90,
            "any_leakage_flag": False,
            "dist_known_fault_px_read": False,
        },
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "evaluator_hashes": EH.implementation_hashes(),
            "design": (
                "gems57-pooled-hide-v2: buffered_component_draw seed=20, 20% whole 8-connected "
                "components hidden per footprint-median quadrant (ym=936, xm=1504), 3 px feature "
                "buffer, strict 12-px-eroded out-of-fold LOQO training domain, nested component-split "
                "continuation features, visible-only 3.0 px collar, pooled 200-px physical blocks, "
                "1,000 paired bootstrap draws"
            ),
            "withheld_positive_pixels": int(ser_hold["withheld_positive_pixels"]),
            "candidate": e1_score,
            "serialized_arm_score": ser_hold,
            "all_arms": pooled["scores"],
            "paired_differences": pooled["paired_differences"],
            "per_fold": holdout_per_fold,
            "beats_ablation_e3_paired_ci95": beats_e3_ci,
        },
        "sgmc_off_catalogue_diagnostic": sgmc_diag,
        "correlation_overlap_vs_registry": {
            "e1_rule1_duplicate_stop": e1_rule1_duplicate_stop,
            "surface_preplacement": registry_summary(
                surface_report, surface_report_path, surface_rc
            ),
            "final_dots": registry_summary(dots_report, dots_report_path, dots_rc),
            "full_registry_informative_dot_field_audit": informative_audit,
            "live_focus9_and_sibling_orgs_surface": live_peer_surf,
            "live_focus9_and_sibling_orgs_final_dots": live_peer_dots,
            "pa86_chance_calibrated_overlap": {
                "evidence_file": str(chance_path.relative_to(ROOT)),
                "gate_pass": chance.get("gate_pass"),
                "informative_firings": chance.get("informative_firings"),
                "worst_informative_excess": chance.get("worst_informative_excess"),
            },
        },
        "gates": gates,
        "raster_sha256": receipt["sha256"],
        "zip_sha256": receipt.get("zip_sha256"),
        "validator_output": val_out,
        "submission_name": name,
        "submission_file": f"docs/downloads/{name}.tif",
        "submission_zip": f"docs/downloads/{name}.zip",
        "submission_receipt": f"docs/downloads/{name}.json",
        "note": note,
        "note_chars": len(note),
        "verdict": "negative",
        "decision": "DO NOT SUBMIT",
        "decision_rationale": (
            "Format-valid (15/15 checks, float32 in [0, 1], 0 NaN/Inf), leakage-clean "
            f"(max symmetric AUC {max_canary['discriminative_auc']:.4f} <= 0.90), and unique "
            f"across all {informative_audit['discrete_le_90k_rasters_checked']} discrete <=90k "
            f"restored-registry rasters (worst {informative_audit['worst_discrete_le_90k_overlap_3px']:.4f} <= 0.70) "
            f"plus all {live_peer_dots['discrete_le_90k_live_peers_checked']} live Focus-9 & "
            f"sibling-org rasters (worst {live_peer_dots['worst_overlap_3px']:.4f} <= 0.70). "
            "Marked verdict='negative' / DO NOT SUBMIT under repository governance because "
            "literal full-support continuous witness 17GEMSDOE (1.0000 3-px overlap) remains "
            "an active fail-closed repo-wide gate and weekly slot selection requires human authorization."
        ),
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "experiments_run": 3,
        "runtime_seconds": round(time.time() - t0, 2),
    }

    card_path = EV_DIR / "h86s-dwad-run-card.json"
    card_path.write_text(
        json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    _log(f"DONE -> {card_path} | tif={run_card['submission_file']} | sha256={receipt['sha256'][:16]}")
    return 0


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible

    require_feasible()
    return run_pa86_lane()


if __name__ == "__main__":
    raise SystemExit(main())
