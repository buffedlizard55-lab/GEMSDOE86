#!/usr/bin/env python3
"""Execute Lane H86I-RKSC within the strict 3-experiment / 2-hour budget.

H86I-RKSC: Lahontan-Deconfounded Piedmont Scarp Profile-Curvature Dipole coupled
with GeoDAWN Radiometric K/Th/U/TC Provenance-Metasomatism Step and
Seismic-Conductance Conduit.

Protocol sequence:
1. Verify frozen preregistration (`research/H86I_RKSC_PREREGISTRATION.json` & `.md`).
2. Run representation-aware preflight (`scripts/protocol_preflight.py::require_like_for_like`).
3. Verify band physics (`Band 6 tc` vs `data/external/geodawn_rad_u8.tif` band 4 `TC`).
4. Compute the 7 catalogue-blind feature planes and 3 preregistered arm surfaces (`E1`, `E2`, `E3`).
5. Run single-feature Leakage Canary (`max(AUC, 1-AUC) <= 0.90`) across all 4 `gems57-pooled-hide-v2` folds.
6. Evaluate all 3 arms + fold-fair `R0` controls on `gems57-pooled-hide-v2` (`seed=20`, `11,321` withheld positives).
7. Run pre-placement surface registry scan (`scripts/check_h86e_registry.py --surface`) BEFORE dot placement.
8. Emit final dot field (`44,090` dots, `tile_px=3`, `>3 px` off catalogue) and run final-dot registry scan
   (`scripts/check_h86e_registry.py`) + PA-86-02 chance-overlap check (`scripts/pa86_chance_overlap.py`)
   BEFORE GeoTIFF serialization.
No weekly slot is selected or used in any outcome.

Following the repository-wide builder gating merged in PR #98, ``main()`` now
calls ``protocol_preflight.require_feasible()`` before any work, so this
runner now stops at the literal protocol stop like every other historical
builder. The recorded 2026-10-25 execution ran under the frozen PA-86
owner-mandate interpretation; its run card and artifacts are unchanged
historical receipts, not a protocol exemption.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import evaluate_holdout as EH  # noqa: E402
from gems57 import grid as G  # noqa: E402
from gems57 import holdout as H  # noqa: E402

from gems86_mmt.features import rank01  # noqa: E402
from gems86_rksc.features import (  # noqa: E402
    ARM_NAMES,
    FEATURE_NAMES,
    REQUIRED_BANDS,
    compute_rksc_from_tif,
    verify_band_contract,
)
from scripts import protocol_preflight  # noqa: E402
from scripts.run_h86e_mmt import (  # noqa: E402
    holdout_arm,
    holdout_binary_control,
    load_binary,
    make_dots,
    save_array,
    sha256,
    write_candidate,
)

PREREG_JSON = ROOT / "research/H86I_RKSC_PREREGISTRATION.json"
PREREG_MD = ROOT / "research/H86I_RKSC_PREREGISTRATION.md"
SURFACE_REPORT_JSON = ROOT / "docs/evidence/h86i-rksc-registry-surface.json"
DOTS_REPORT_JSON = ROOT / "docs/evidence/h86i-rksc-registry-dots.json"
CHANCE_OVERLAP_JSON = ROOT / "docs/evidence/h86i-rksc-chance-overlap.json"
RUN_CARD_JSON = ROOT / "docs/evidence/h86i-rksc-run-card.json"
WORK_DIR = ROOT / "data/work"

HOLDOUT_SEED = 20
HOLDOUT_HIDE_FRAC = 0.20
HOLDOUT_BUFFER_PX = 3
FULL_BUDGET_DOTS = 44090
VISIBLE_COLLAR_PX = 3.0
TILE_PX = 3

R0_UNPRUNED_SHA256 = "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"


def locate_unpruned_r0() -> Path:
    candidates = [
        ROOT / "data/registry_ext" / f"{R0_UNPRUNED_SHA256}.tif",
        ROOT / "data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    ]
    for p in candidates:
        if p.is_file() and sha256(p) == R0_UNPRUNED_SHA256:
            return p
    raise RuntimeError("Missing or hash-mismatched unpruned R0 control raster")


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def require_preregistration(
    json_path: Path = PREREG_JSON,
    md_path: Path = PREREG_MD,
) -> dict:
    if not json_path.is_file() or not md_path.is_file():
        raise FileNotFoundError("H86I-RKSC preregistration files must exist before execution")
    doc = json.loads(json_path.read_text())
    if doc.get("status") != "frozen_before_implementation":
        raise ValueError("H86I-RKSC preregistration must have status == 'frozen_before_implementation'")
    if int(doc.get("candidate_hypotheses_count", 0)) < 3:
        raise ValueError("Preregistration must declare at least 3 untried candidate hypotheses")
    if len(doc.get("experiment_arms", [])) > 3:
        raise ValueError("Preregistration exceeds 3-experiment budget cap")
    return {
        "schema": doc["schema"],
        "status": doc["status"],
        "frozen_utc": doc["frozen_utc"],
        "json_path": _rel(json_path),
        "json_sha256": sha256(json_path),
        "md_path": _rel(md_path),
        "md_sha256": sha256(md_path),
        "candidate_hypotheses_count": int(doc["candidate_hypotheses_count"]),
        "ranked_hypothesis_ids": [h["id"] for h in doc["candidate_hypotheses"]],
        "experiment_arms": [a["arm_id"] for a in doc["experiment_arms"]],
    }


def verify_rad_tc_band_physics(
    features_tif: Path,
    geodawn_tif: Path,
    footprint: np.ndarray,
) -> dict:
    """Verify Band 6 (`tc`) against external GeoDAWN Total Count (`geodawn_rad_u8.tif` band 4 `TC`)."""
    verify_band_contract()
    core = ndi.binary_erosion(np.asarray(footprint, dtype=bool), iterations=20)
    with rasterio.open(features_tif) as src_f:
        b6 = src_f.read(6).astype(np.float64)
    with rasterio.open(geodawn_tif) as src_g:
        gk = src_g.read(1).astype(np.float64)
        gth = src_g.read(2).astype(np.float64)
        gu = src_g.read(3).astype(np.float64)
        gtc = src_g.read(4).astype(np.float64)

    ok = core & np.isfinite(b6) & (np.abs(b6) < 1e20) & (gtc > 0) & (gk > 0) & (gth > 0)
    corr_geodawn_tc = float(np.corrcoef(b6[ok], gtc[ok])[0, 1])
    if corr_geodawn_tc < 0.98:
        raise RuntimeError(
            f"Band 6 tc correlation with geodawn_rad_u8.tif Band 4 TC too low: {corr_geodawn_tc:.6f}"
        )
    corr_b6_k = float(np.corrcoef(b6[ok], gk[ok])[0, 1])
    corr_b6_th = float(np.corrcoef(b6[ok], gth[ok])[0, 1])
    corr_b6_u = float(np.corrcoef(b6[ok], gu[ok])[0, 1])
    return {
        "evidence_class": "BAND-PHYSICS-QC",
        "verified_bands": REQUIRED_BANDS,
        "geodawn_bands": {1: "K", 2: "Th", 3: "U", 4: "TC"},
        "interior_erosion_px": 20,
        "interior_pixels": int(ok.sum()),
        "corr_band6_tc_vs_geodawn_b4_TC": round(corr_geodawn_tc, 6),
        "corr_band6_tc_vs_geodawn_b1_K": round(corr_b6_k, 6),
        "corr_band6_tc_vs_geodawn_b2_Th": round(corr_b6_th, 6),
        "corr_band6_tc_vs_geodawn_b3_U": round(corr_b6_u, 6),
        "fail_closed_min_corr_geodawn_tc": 0.98,
    }


def run_leakage_canary(
    planes: dict[str, np.ndarray],
    folds: list[dict],
    footprint: np.ndarray,
) -> dict:
    """Single-feature ROC AUC canary on all 4 buffered whole-component holdout folds."""
    rng = np.random.default_rng(HOLDOUT_SEED + 869)
    fp = np.asarray(footprint, dtype=bool)
    fields_out: dict[str, dict] = {}
    worst_field = ""
    worst_disc = 0.0
    all_pass = True

    for name in FEATURE_NAMES:
        arr = planes[name]
        fold_aucs: list[float] = []
        for f in folds:
            region = np.asarray(f["region"], dtype=bool)
            known = np.asarray(f.get("masked_known", f["visible"]), dtype=bool)
            truth = np.asarray(f["truth"], dtype=bool)
            active = fp & region & (~known)
            pos = truth & active
            neg = active & (~pos)
            pos_vals = arr[pos]
            neg_idx = np.flatnonzero(neg)
            take = min(neg_idx.size, max(60_000, pos_vals.size * 12))
            sampled_neg = arr.ravel()[rng.choice(neg_idx, size=take, replace=False)]
            y_true = np.concatenate(
                [np.ones(pos_vals.size, dtype=np.int8), np.zeros(sampled_neg.size, dtype=np.int8)]
            )
            y_score = np.concatenate([pos_vals.astype(np.float64), sampled_neg.astype(np.float64)])
            auc = float(roc_auc_score(y_true, y_score))
            fold_aucs.append(round(auc, 6))
        mean_auc = float(np.mean(fold_aucs))
        max_disc = float(max(max(a, 1.0 - a) for a in fold_aucs))
        passed = bool(max_disc <= 0.90)
        if not passed:
            all_pass = False
        if max_disc > worst_disc:
            worst_disc = max_disc
            worst_field = name
        fields_out[name] = {
            "evidence_class": "LEAKAGE-CANARY",
            "mean_auc": round(mean_auc, 6),
            "fold_aucs": fold_aucs,
            "max_discriminative_auc": round(max_disc, 6),
            "threshold": 0.90,
            "pass": passed,
        }

    if not all_pass:
        raise RuntimeError(
            f"Leakage canary failed on {worst_field}: discriminative AUC {worst_disc:.4f} > 0.90"
        )
    return {
        "threshold_discriminative_auc": 0.90,
        "all_pass": all_pass,
        "worst_field": worst_field,
        "worst_discriminative_auc": round(worst_disc, 6),
        "fields": fields_out,
    }


def run_registry_check(array_path: Path, output: Path, *, surface: bool) -> tuple[dict, int]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts/check_h86e_registry.py"),
        str(array_path.relative_to(ROOT)),
        str(output),
    ]
    if surface:
        cmd.append("--surface")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if not output.is_file():
        raise RuntimeError(
            f"registry check produced no report (rc={proc.returncode}): {proc.stderr[-2000:]}"
        )
    return json.loads(output.read_text()), proc.returncode


def run_chance_check(registry_report: Path, candidate_path: Path, output: Path) -> dict:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/pa86_chance_overlap.py"),
            str(registry_report),
            str(candidate_path.relative_to(ROOT)),
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if output.is_file():
        report = json.loads(output.read_text())
        report["runner_returncode"] = proc.returncode
        return report
    return {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "amendment": "PA-86-02",
        "status": "FAILED_CLOSED_NO_REPORT",
        "gate_pass": False,
        "runner_returncode": proc.returncode,
        "stderr_tail": proc.stderr[-3000:],
        "stdout_tail": proc.stdout[-1000:],
        "note": (
            "pa86_chance_overlap.py refused to certify (binding/completeness due to 2 off-grid "
            "historical registry rasters); recorded verbatim as gate_pass=False."
        ),
    }


def registry_summary(report: dict, returncode: int) -> dict:
    shared = report.get("shared_summary", {})
    return {
        "evidence_class": "REGISTRY-MEASUREMENT",
        "runner_returncode": returncode,
        "registry_rasters_expected": report.get(
            "registry_rasters_expected", shared.get("registry_rasters_expected")
        ),
        "registry_rasters_measured": report.get("registry_rasters_measured"),
        "registry_rasters_missing": len(report.get("inventory_rasters_missing", [])),
        "registry_errors": report.get("errors", []),
        "registry_complete_for_index": report.get("registry_complete_for_index"),
        "complete_accessible_scan": shared.get("complete_accessible_scan"),
        "byte_unique_among_checked": shared.get("byte_unique_among_checked"),
        "pixel_unique_among_checked": shared.get("pixel_unique_among_checked"),
        "worst_spearman_full_footprint": shared.get("worst_spearman_full_footprint"),
        "worst_spearman_submission": shared.get("worst_rho_submission"),
        "worst_dot_overlap": shared.get("worst_dot_overlap"),
        "worst_overlap_submission": shared.get("worst_overlap_submission"),
        "literal_gate_pass": report.get("literal_gate_pass"),
        "two_phase": report.get("two_phase"),
        "top15_by_forward_overlap": report.get("top15_by_forward_overlap"),
        "top15_by_spearman": report.get("top15_by_spearman"),
        "scope": report.get("scope"),
    }


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Verify preregistration only.")
    args = parser.parse_args()

    t0 = time.time()
    prereg_info = require_preregistration()
    if args.dry_run:
        print(json.dumps({"status": "PREREGISTRATION_OK", "preregistration": prereg_info}, indent=2))
        return 0

    # Step 1: PA-86-01 representation-aware preflight
    preflight_report = protocol_preflight.require_like_for_like()

    # Step 2: Load canonical grid and verify input hashes
    grid = G.load_grid(ROOT / "data/bridge")
    features_tif = ROOT / "data/training_features.tif"
    faults_tif = ROOT / "data/existing_faults.tif"
    sample_tif = ROOT / "data/sample_submission.tif"
    geodawn_tif = ROOT / "data/external/geodawn_rad_u8.tif"
    topo10_tif = ROOT / "data/external/topo_10m_derived_100m_u8.tif"

    input_hashes = {
        "training_features.tif": sha256(features_tif),
        "existing_faults.tif": sha256(faults_tif),
        "sample_submission.tif": sha256(sample_tif),
        "geodawn_rad_u8.tif": sha256(geodawn_tif),
        "topo_10m_derived_100m_u8.tif": sha256(topo10_tif),
    }

    # Step 3: Band physics QC
    band_qc = verify_rad_tc_band_physics(features_tif, geodawn_tif, grid.footprint)

    # Step 4: Build shared buffered whole-component holdout folds (`seed=20`, `11,321` withheld positives)
    folds, _quad_meta = H.buffered_component_draw(
        grid,
        seed=HOLDOUT_SEED,
        hide_frac=HOLDOUT_HIDE_FRAC,
        buffer_px=HOLDOUT_BUFFER_PX,
    )

    # Step 5: Compute catalogue-blind feature planes and 3 preregistered arms
    planes, arms = compute_rksc_from_tif(features_tif, geodawn_tif, topo10_tif, grid.footprint)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    feature_hashes = {
        name: save_array(WORK_DIR / f"h86i_{name}.npy", planes[name]) for name in FEATURE_NAMES
    }

    # Step 6: Run single-feature Leakage Canary
    canary_report = run_leakage_canary(planes, folds, grid.footprint)
    del planes
    gc.collect()

    # Step 7: Evaluate all 3 preregistered arms + fold-fair R0 controls on `gems57-pooled-hide-v2`
    holdout_terms: dict[str, np.ndarray] = {}
    holdout_per_fold: dict[str, dict] = {}
    for arm_name in ARM_NAMES:
        terms, per_fold, _example = holdout_arm(
            arms[arm_name], folds, grid.footprint, FULL_BUDGET_DOTS
        )
        holdout_terms[arm_name] = terms
        holdout_per_fold[arm_name] = per_fold

    r0_path = locate_unpruned_r0()
    r0_dots = load_binary(r0_path) & grid.footprint
    r0_ff_terms, r0_ff_per_fold, _ = holdout_binary_control(
        r0_dots, folds, grid.footprint, collar_px=2.0
    )
    r0_c3_terms, r0_c3_per_fold, _ = holdout_binary_control(
        r0_dots, folds, grid.footprint, collar_px=3.0
    )
    del r0_dots
    gc.collect()

    holdout_terms["R0_GEMSDOE25_d28_fold_fair_2px"] = r0_ff_terms
    holdout_per_fold["R0_GEMSDOE25_d28_fold_fair_2px"] = r0_ff_per_fold
    holdout_terms["R0_GEMSDOE25_d28_collar_3px"] = r0_c3_terms
    holdout_per_fold["R0_GEMSDOE25_d28_collar_3px"] = r0_c3_per_fold

    pooled = EH.pooled_summary(
        holdout_terms,
        draws=1000,
        seed=86_1025,
        candidate="E1_rksc_full",
    )
    current_best = json.loads((ROOT / "docs/evidence/lane86c_results.json").read_text())[
        "holdout_buffered_whole_components"
    ]["scores"]["E3_kslb_noisyor_44k"]
    e1_metrics = pooled["scores"]["E1_rksc_full"]
    e2_metrics = pooled["scores"]["E2_rksc_rad_scarp_only"]
    e3_metrics = pooled["scores"]["E3_rksc_lahontan_uncorrected_control"]
    r0_ff_metrics = pooled["scores"]["R0_GEMSDOE25_d28_fold_fair_2px"]
    r0_c3_metrics = pooled["scores"]["R0_GEMSDOE25_d28_collar_3px"]
    diff_vs_r0_ff = pooled["paired_differences"]["R0_GEMSDOE25_d28_fold_fair_2px"]
    diff_vs_r0_c3 = pooled["paired_differences"]["R0_GEMSDOE25_d28_collar_3px"]

    beats_current = bool(
        e1_metrics["dti"] > current_best["dti"]
        and e1_metrics["ci95"][0] > current_best["ci95"][1]
    )
    beats_controls = bool(diff_vs_r0_ff["ci95"][0] > 0.0)

    # Step 8: Pre-placement surface registry check (`scripts/check_h86e_registry.py --surface`)
    final_surface = arms["E1_rksc_full"].copy()
    del arms, folds, holdout_terms
    gc.collect()

    surface_path = WORK_DIR / "h86i_rksc_final_surface.npy"
    save_array(surface_path, rank01(final_surface, grid.footprint))
    surface_report, surface_rc = run_registry_check(
        surface_path, SURFACE_REPORT_JSON, surface=True
    )
    surface_gate = bool(surface_report.get("surface_gate_pass"))
    rho_firings = int(
        surface_report.get("two_phase", {})
        .get("literal_reading", {})
        .get("rho_firings", -1)
    )
    if rho_firings != 0:
        raise RuntimeError(
            f"STOP: Pre-placement surface rank correlation firing (rho_firings={rho_firings})"
        )

    # Step 9: Place final dots (`44,090` dots, `tile_px=3`, `d_cat > 3.0 px`) and run
    # final-dot registry scan + PA-86-02 chance-overlap check BEFORE GeoTIFF serialization
    dcat = ndi.distance_transform_edt(~grid.catalogue)
    allowed = grid.footprint & (dcat > VISIBLE_COLLAR_PX)
    del dcat
    final_dots = make_dots(final_surface, allowed, FULL_BUDGET_DOTS)
    del final_surface, allowed
    gc.collect()

    dots_path = WORK_DIR / "h86i_rksc_final_dots.npy"
    save_array(dots_path, final_dots.astype(np.float32))
    dots_report, dots_rc = run_registry_check(dots_path, DOTS_REPORT_JSON, surface=False)
    chance_report = run_chance_check(DOTS_REPORT_JSON, dots_path, CHANCE_OVERLAP_JSON)
    CHANCE_OVERLAP_JSON.write_text(json.dumps(chance_report, indent=2) + "\n")

    final_gate = bool(dots_report.get("final_dots_gate_pass"))
    registry_gate = bool(
        surface_gate and final_gate and chance_report.get("gate_pass") is True
    )

    # Step 10: Serialize unique audit-only GeoTIFF + single-TIFF `.zip` + writer receipt `.json`
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(final_dots).tobytes()).hexdigest()[:8]
    n_final_dots = int(final_dots.sum())
    name = f"gems86-h86i-rksc-rad-scarp-{n_final_dots}dots-{stamp}-{digest8}-zeros"
    note = (
        "H86I-RKSC GeoDAWN K/Th/U/TC step + Lahontan-deconf piedmont scarp dipole; "
        "see run card gates; no slot used"
    )[:140]
    receipt = write_candidate(
        final_dots,
        grid,
        name,
        note,
        metadata={
            "lane": "H86I-RKSC",
            "hypothesis": (
                "Lahontan-deconfounded piedmont scarp profile-curvature dipole + "
                "GeoDAWN K/Th/U/TC provenance-metasomatism step + seismic-conductance conduit"
            ),
            "budget": FULL_BUDGET_DOTS,
            "feature_hashes": feature_hashes,
            "band_physics_qc": band_qc,
            "surface_sha256": sha256(surface_path),
            "dots_sha256": sha256(dots_path),
            "registry_surface_evidence": _rel(SURFACE_REPORT_JSON),
            "registry_final_evidence": _rel(DOTS_REPORT_JSON),
            "chance_overlap_evidence": _rel(CHANCE_OVERLAP_JSON),
        },
    )

    verdict = "promote" if (beats_current and beats_controls and registry_gate) else "negative"
    reasons = []
    if not beats_current:
        reasons.append(
            "candidate does not beat current same-split HOLDOUT-DTI best (H86C-KSLB 0.1241) with separated CIs"
        )
    if not beats_controls:
        reasons.append(
            "paired HOLDOUT-DTI delta versus fold-fair R0 control (0.0961) is not strictly positive"
        )
    if not surface_gate:
        reasons.append(
            "pre-placement surface registry gate did not pass (completeness/validity on 2 off-grid historical rows; 0 rho firings)"
        )
    if not final_gate:
        reasons.append("final-dot like-for-like / literal registry gate failed")
    if chance_report.get("gate_pass") is not True:
        reasons.append("PA-86-02 chance-overlap gate failed closed on 2 off-grid registry rows")

    elapsed_s = round(time.time() - t0, 2)

    surf_summary = registry_summary(surface_report, surface_rc)
    dots_summary = registry_summary(dots_report, dots_rc)

    run_card = {
        "schema": "gems86.h86i-rksc-run-card.v1",
        "lane": "H86I-RKSC",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": prereg_info,
        "hypothesis": (
            "H86I-1 (H86I-RKSC): Late-Quaternary piedmont and intrabasin faults diffused below "
            "~1-2 m relief are missed by aerial-photo compilation in USGS/INGENIOUS, yet produce "
            "co-located (1) asymmetric slope-normal profile-curvature inflections in detrended "
            "elevation (Band 12) + 10m 3DEP profile curvature within the piedmont slope window "
            "(Band 19) deconfounded against Pleistocene Lake Lahontan strandlines (topo_10m dem_mean), "
            "(2) strike-concordant radiometric steps in immobile-normalized potassium metasomatism "
            "R_K_Th = z(geodawn K) - 0.85*z(geodawn Th) and GeoDAWN Total Count (Band 6 tc), and "
            "(3) seismic-geodetic-argillic conduit favorability (Bands 4, 7, 8, 10, 16, 17)."
        ),
        "mechanism": (
            "Footprint-normalized sigma=300 m slope-normal profile curvature -div(grad(B12)/||grad(B12)||) "
            "+ 10m 3DEP curv_prof_absmax gated by piedmont slope window (B19) and suppressed along "
            "Lake Lahontan contour-parallel strandlines (topo_10m Band 9 dem_mean), coupled via spin-2 "
            "structure-tensor concordance with spatial gradients of R_K_Th and B6 (tc), and modulated "
            "by microseismic swarm proximity/intensity (B10, B16), shallow conductance gradients (B17), "
            "and geodetic transtension (B4, B7, B8). Emitted via shared 3-px decimated emitter at "
            "44,090 dots with >3 px Euclidean catalogue collar."
        ),
        "named_non_fault_process": (
            "Pleistocene Lake Lahontan wave-cut constructional strandlines and non-tectonic "
            "lithologic contact aprons between potassic ash-flow tuff ranges and intermediate "
            "volcanic piedmonts."
        ),
        "non_fault_mimic": (
            "Pleistocene Lake Lahontan wave-cut constructional strandlines and non-tectonic "
            "lithologic contact aprons between potassic ash-flow tuff ranges and intermediate "
            "volcanic piedmonts."
        ),
        "source_layers": [
            "training_features.tif Band 4 geod_2ndinv",
            "training_features.tif Band 6 tc (pixel-verified GeoDAWN Total Count TC)",
            "training_features.tif Band 7 geod_shearrate",
            "training_features.tif Band 8 geod_dilaterate",
            "training_features.tif Band 10 deq_n100a15",
            "training_features.tif Band 12 det_elev",
            "training_features.tif Band 16 ieq_n100a15",
            "training_features.tif Band 17 cond_surf",
            "training_features.tif Band 19 det_elev_slope",
            "data/external/geodawn_rad_u8.tif Bands 1-4 (K, Th, U, TC)",
            "data/external/topo_10m_derived_100m_u8.tif Bands 6, 9 (curv_prof_absmax, dem_mean)",
        ],
        "preflight": preflight_report,
        "verified_input_sha256": input_hashes,
        "band_physics_qc": band_qc,
        "leakage_canary": canary_report,
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EH.VERSION,
            "design": (
                "buffered whole-component quadrant draw, seed 20, hide fraction 0.20, "
                "visible-fault collar 3 px, pooled 200-px physical blocks"
            ),
            "withheld_positive_pixels": int(e1_metrics["withheld_positive_pixels"]),
            "candidate": e1_metrics,
            "paired_delta_vs_fold_fair_r0": diff_vs_r0_ff,
            "paired_delta_vs_same_collar_r0": diff_vs_r0_c3,
            "R0_GEMSDOE25_d28_fold_fair_2px": r0_ff_metrics,
            "R0_GEMSDOE25_d28_collar_3px": r0_c3_metrics,
            "current_holdout_best_same_split": {
                "evidence_class": "HOLDOUT-DTI",
                "source": "docs/evidence/lane86c_results.json",
                "arm": "E3_kslb_noisyor_44k",
                "dti": current_best["dti"],
                "ci95": current_best["ci95"],
                "note": "historical same-split comparator; not re-run by this lane",
            },
            "beats_current_with_separated_ci": beats_current,
            "paired_delta_beats_control": beats_controls,
            "all_arms": pooled["scores"],
            "paired_differences": pooled["paired_differences"],
            "per_fold": holdout_per_fold,
            "leakage_canary": canary_report,
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "surface_preplacement": {
                "report": _rel(SURFACE_REPORT_JSON),
                **surf_summary,
                "surface_gate_pass": surface_gate,
                "rho_firings": rho_firings,
            },
            "final_dots": {
                "report": _rel(DOTS_REPORT_JSON),
                **dots_summary,
                "final_dots_gate_pass": final_gate,
            },
            "pa86_02": chance_report,
            "literal_dense_surface_note": (
                "The literal support reading is reported unchanged in both registry reports; a "
                "full-support continuous prior gives literal forward overlap 1.0 for every nonempty "
                "dot set. PA-86-01/02 keeps that firing visible and decides on rank correlation "
                "(every raster) plus dot-field overlap; thresholds are unchanged."
            ),
        },
        "raster_sha256": receipt["sha256"],
        "validator_output": {
            "evidence_class": "LOCAL-FORMAT-VALIDATION",
            "all_checks_passed": receipt["independent_disk_validation"]["all_checks_passed"],
            "no_nan_inside_footprint": receipt["independent_disk_validation"]["checks"][
                "in_footprint_all_finite"
            ],
            "values_in_0_1": receipt["independent_disk_validation"]["checks"][
                "range_0_1_guaranteed"
            ],
            "crs_shape_transform_match": all(
                receipt["independent_disk_validation"]["checks"][key]
                for key in (
                    "crs_epsg_32611",
                    "dimensions_3730x3292",
                    "transform_matches_sample_submission",
                )
            ),
            "checks": receipt["independent_disk_validation"]["checks"],
            "positive_pixels": receipt["independent_disk_validation"]["emitted_positive_pixels"],
            "min": receipt["independent_disk_validation"]["min"],
            "max": receipt["independent_disk_validation"]["max"],
        },
        "submission_name": name,
        "submission_file": f"docs/downloads/{name}.tif",
        "submission_zip": f"docs/downloads/{name}.zip",
        "submission_receipt": f"docs/downloads/{name}.json",
        "note": note,
        "submission_note": note,
        "note_chars": len(note),
        "verdict": verdict,
        "duplicate": bool(not registry_gate),
        "decision": "SELECTOR STEP REQUIRED" if verdict == "promote" else "DO NOT SUBMIT",
        "decision_reason": "; ".join(reasons),
        "experiments_run": 3,
        "submission_ready": False,
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "budget": {
            "experiments_run": 3,
            "max_experiments": 3,
            "runtime_seconds": elapsed_s,
            "max_hours": 2.0,
            "submission_slots_used": 0,
        },
        "runtime_seconds": elapsed_s,
    }
    RUN_CARD_JSON.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "lane": "H86I-RKSC",
                "verdict": verdict,
                "decision": run_card["decision"],
                "submission_name": name,
                "raster_sha256": receipt["sha256"],
                "e1_dti": e1_metrics["dti"],
                "e1_ci95": e1_metrics["ci95"],
                "e2_dti": e2_metrics["dti"],
                "e3_dti": e3_metrics["dti"],
                "r0_fold_fair_2px_dti": r0_ff_metrics["dti"],
                "r0_collar_3px_dti": r0_c3_metrics["dti"],
                "surface_worst_rho": surf_summary["worst_spearman_full_footprint"],
                "surface_rho_firings": rho_firings,
                "dots_worst_rho": dots_summary["worst_spearman_full_footprint"],
                "dots_worst_dot_overlap": dots_summary["worst_dot_overlap"],
                "elapsed_s": elapsed_s,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
