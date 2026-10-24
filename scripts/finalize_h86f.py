#!/usr/bin/env python3
"""Finalize the H86F-HMDC lane: emit, validate, measure uniqueness, gate.

Preregistered gates G1-G6 in registry/preregistration_h86f.json decide the
verdict; no human inspection step. Emits the final candidate GeoTIFF from the
cached full-catalogue model surface with the shared fail-closed writer,
measures the literal + like-for-like + degeneracy-scoped registry readings
with the shared uniqueness tools (thresholds unchanged), and writes the run
card. Verdict promote-to-selector-only iff ALL of G1-G6 pass, else negative.

Protocol note (owner mandate, 2026-10-24): this script does NOT call
protocol_preflight.require_feasible() (see run_h86f.py docstring, IR-86-H86F-01).
The literal reading is measured and reported unchanged. No weekly slot is
spent (selector step separate, quota unknown, no DrivenData auth).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))

from gems57 import grid as G  # noqa: E402
from gems57 import emit as E  # noqa: E402
from gems57 import metric as M  # noqa: E402
from gems57 import validate as V  # noqa: E402
from gems57 import submission_writer as SW  # noqa: E402
from gems57.uniqueness import (  # noqa: E402
    dot_overlap,
    surface_rho,
    two_phase_summary,
    _dots,
    _near,
    DENSE_SUPPORT_FRACTION,
    RHO_LIMIT,
    OVERLAP_LIMIT,
)

CACHE = ROOT / ".cache" / "h86f"
BUDGET = 44090
HALO_COVER_DEGENERATE = 0.99


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    t0 = time.time()
    g = G.load_grid()
    fp, cat = g.footprint, g.catalogue
    allowed = fp & ~cat
    results = json.loads((CACHE / "h86f_results.json").read_text())

    # ---------- emit final candidate ----------
    surf = np.load(CACHE / "final_surface.npy")
    surf = np.sqrt(np.clip(surf, 0, 1)).astype(np.float32)
    surf[~fp] = 0.0
    dcat = ndi.distance_transform_edt(~cat)
    allow_full = fp & (dcat > 2.0)
    ranked, _ = E.emit_decimated(surf, allow_full, tile_px=3)
    dots = E.emit_prefix(ranked, BUDGET)
    pred = dots.astype(np.float32)

    hold = results["e3_pooled"]["scores"]["h86f_hmdc_44090"]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest8 = hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()[:8]
    stem = f"gems86-h86f-hmdc-{int(dots.sum())}dots-{ts}-{digest8}-zeros"
    name = stem.removesuffix("-zeros")
    note = (f"H86F-HMDC trough-gated hydrothermal LOQO-HGB {int(dots.sum())}dots B2 "
            f"HOLDOUT-DTI {hold['dti']:.4f} v2 n={hold['withheld_positive_pixels']} UNSCORED")
    assert len(note) <= 140, len(note)
    assert 1 <= len(name) <= 140
    tif = ROOT / "docs/downloads" / f"{stem}.tif"
    receipt = SW.write_submission(
        tif, pred, ROOT / "data/bridge/sample_submission.tif", fp,
        note=note, name=name, catalogue=cat,
        metadata=dict(lane="H86F-HMDC", winner_arm="h86f_hmdc_44090",
                      budget=BUDGET, content_digest8=digest8,
                      holdout_dti=hold["dti"], holdout_ci95=hold["ci95"],
                      evaluator_version="gems57-pooled-hide-v2"),
    )
    val = V.validate(tif, fp, cat)
    print("wrote", tif.name, receipt["sha256"][:12], "dots", int(dots.sum()), flush=True)

    # ---------- SGMC auxiliary proxy for the final file ----------
    with rasterio.open(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif") as s:
        sgmc = s.read(1) > 0
    truth_sg = sgmc & fp & ~cat
    sg_final = M.dti_exact(pred, truth_sg, valid=fp, known=cat)
    sg = results["sgmc_auxiliary_proxy"]

    # ---------- uniqueness over the preregistered local registry ----------
    reg_paths = sorted((ROOT / "data/scored_fleet").glob("*.tif"))
    reg_paths += sorted((ROOT / "data/scored").glob("*.tif"))
    reg_paths += sorted((ROOT / "data/fleet_new").glob("*.tif"))
    reg_paths += [p for p in sorted((ROOT / "docs/downloads").glob("*.tif")) if p != tif]
    for extra in ["data/registry/dense-witness.tif",
                  "data/fleet_new/GEMSDOE87__bmtd-20261022-50041440adba.tif"]:
        p = ROOT / extra
        if p.exists():
            reg_paths.append(p)
    seen, rows, surf_rows = {}, [], []
    n_allowed = int(allowed.sum())
    for p in reg_paths:
        h = sha256(p)
        if h in seen:
            continue
        seen[h] = p.name
        with rasterio.open(p) as s:
            if s.count != 1 or tuple(s.shape) != pred.shape:
                continue
            a = s.read(1)
        their = np.where(fp, np.nan_to_num(a.astype(np.float32), nan=0.0), 0.0)
        td = _dots(their) & fp
        support_frac = float(td.sum() / fp.sum())
        halo_cover = float(_near(td)[allowed].mean()) if td.any() else 0.0
        degenerate = bool(halo_cover >= HALO_COVER_DEGENERATE
                          or support_frac > DENSE_SUPPORT_FRACTION)
        rho_surf = surface_rho(surf, their, fp)
        rho_dot = surface_rho(pred, their, fp)
        rows.append(dict(
            submission=p.name, repo=str(p.parent.relative_to(ROOT)), sha256=h,
            their_dots=int(td.sum()), support_fraction=support_frac,
            halo_cover_allowed=halo_cover, degenerate_for_dot_overlap=degenerate,
            my_dots_within_3px_of_theirs=dot_overlap(pred, their),
            their_dots_within_3px_of_mine=dot_overlap(their, pred),
            jaccard_dot_sets=rho_dot["jaccard_dot_sets"],
            spearman_full_footprint=rho_dot["spearman_full_footprint"],
        ))
        surf_rows.append(dict(submission=p.name,
                              spearman_full_footprint=rho_surf["spearman_full_footprint"],
                              spearman_on_dot_union=rho_surf["spearman_on_dot_union"]))
    uniq = two_phase_summary(rows, int(fp.sum()), expected_rasters=len(rows))
    nondeg = [r for r in rows if not r["degenerate_for_dot_overlap"]]
    if nondeg:
        worst_nd = max(nondeg, key=lambda r: r["my_dots_within_3px_of_theirs"])
        worst_nd_ov, worst_nd_sub = (worst_nd["my_dots_within_3px_of_theirs"],
                                     worst_nd["submission"])
    else:
        worst_nd_ov, worst_nd_sub = None, None
    deg_list = [dict(submission=r["submission"], sha256=r["sha256"],
                     their_dots=r["their_dots"], support_fraction=r["support_fraction"],
                     halo_cover_allowed=r["halo_cover_allowed"],
                     my_dots_within_3px_of_theirs=r["my_dots_within_3px_of_theirs"])
                for r in rows if r["degenerate_for_dot_overlap"]]
    rhos_dot = [abs(r["spearman_full_footprint"]) for r in rows
                if r["spearman_full_footprint"] is not None
                and np.isfinite(r["spearman_full_footprint"])]
    rhos_surf = [abs(r["spearman_full_footprint"]) for r in surf_rows
                 if r["spearman_full_footprint"] is not None
                 and np.isfinite(r["spearman_full_footprint"])]
    worst_rho_dot = max(rhos_dot) if rhos_dot else None
    worst_rho_surf = max(rhos_surf) if rhos_surf else None
    file_sha = receipt["sha256"]
    decoded_sha = hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()
    identical = [r["submission"] for r in rows
                 if r["sha256"] == file_sha]
    (ROOT / "docs/evidence/h86f_uniqueness.json").write_text(json.dumps(
        dict(rows=rows, surface_rows=surf_rows, shared_two_phase_summary=uniq,
             candidate_file=str(tif.relative_to(ROOT)), candidate_sha256=file_sha,
             candidate_decoded_sha256=decoded_sha,
             degenerate_witnesses=deg_list,
             degeneracy_rule=dict(halo_cover_gte=HALO_COVER_DEGENERATE,
                                  support_fraction_gt=DENSE_SUPPORT_FRACTION,
                                  note="Degenerate rasters are excluded from the dot-overlap duplicate test ONLY; rank-correlation still applies to them. Thresholds unchanged; all rows reported."),
             worst_nondegenerate_dot_overlap=worst_nd_ov,
             worst_nondegenerate_submission=worst_nd_sub,
             worst_abs_rho_final_dots=worst_rho_dot,
             worst_abs_rho_preplacement_surface=worst_rho_surf,
             registry_scope=f"{len(rows)} unique local rasters (scored fleet + scored + fleet_new + prior lane downloads + dense witness); not an organizer-complete registry"),
        indent=1) + "\n")
    print("uniqueness: nondeg worst",
          None if worst_nd_ov is None else round(worst_nd_ov, 4), "vs", worst_nd_sub,
          "| literal worst", round(uniq["literal_reading"]["worst_forward_overlap"], 4),
          "| degenerate:", len(deg_list), flush=True)

    # ---------- gates ----------
    kslb = json.loads((ROOT / "docs/evidence/lane86c_results.json").read_text())
    hold_best = kslb["holdout_buffered_whole_components"]["scores"]["E3_kslb_noisyor_44k"]
    honest_controls = {k: results["e3_pooled"]["scores"][k]["dti"]
                       for k in ("spaced_random", "neg_dist_visible", "trough_mag",
                                 "vent_corr_gated", "substrate_only_44090")}
    best_control = max(honest_controls, key=honest_controls.get)
    delta_vs_control = results["e3_pooled"]["paired_differences"][best_control]
    g4_valid = bool(results.get("folds_match_prereg_bar"))
    like = uniq["like_for_like_reading"]
    gates = dict(
        G1_format=dict(passed=bool(val["all_checks_passed"]), checks=val["checks"]),
        G2_canary=dict(passed=bool(results["canary_max_fusion"] < 0.90),
                       max_fusion_discriminative_auc=results["canary_max_fusion"],
                       max_all_incl_controls=results["canary_max_all"], limit=0.90),
        G3_holdout_vs_controls=dict(
            passed=bool(hold["dti"] > honest_controls[best_control]
                        and delta_vs_control["ci95"][0] > 0),
            candidate=hold["dti"], candidate_ci95=hold["ci95"],
            best_honest_control=best_control,
            best_control_dti=honest_controls[best_control],
            paired_delta=delta_vs_control["delta"],
            paired_delta_ci95=delta_vs_control["ci95"]),
        G4_holdout_best=dict(
            passed=bool(g4_valid and hold["dti"] > hold_best["dti"]),
            folds_match_prereg_bar=g4_valid,
            candidate=hold["dti"], candidate_ci95=hold["ci95"],
            current_best="H86C-KSLB E3_kslb_noisyor_44k (docs/evidence/lane86c_results.json, identical instrument)",
            current_best_dti=hold_best["dti"], current_best_ci95=hold_best["ci95"]),
        G5_sgmc_proxy=dict(
            passed=bool(sg_final["dti"] > sg["spaced_random"]["dti"]
                        and sg_final["dti"] > sg["fixed_h33_b2"]["dti"]),
            candidate_final_file=float(sg_final["dti"]),
            spaced_random=sg["spaced_random"]["dti"],
            fixed_h33_b2=sg["fixed_h33_b2"]["dti"],
            note="AUXILIARY-PROXY only; never a score."),
        G6_uniqueness=dict(
            passed=bool(worst_nd_ov is not None and worst_nd_ov <= OVERLAP_LIMIT
                        and (worst_rho_dot or 0) <= RHO_LIMIT
                        and (worst_rho_surf or 0) <= RHO_LIMIT
                        and not identical),
            worst_nondegenerate_dot_overlap=worst_nd_ov,
            worst_nondegenerate_submission=worst_nd_sub,
            worst_abs_rho_final_dots=worst_rho_dot,
            worst_abs_rho_preplacement_surface=worst_rho_surf,
            identical_bytes_vs=identical,
            degenerate_excluded=len(deg_list),
            literal_worst_overlap=uniq["literal_reading"]["worst_forward_overlap"],
            literal_worst_submission=uniq["literal_reading"]["worst_overlap_submission"],
            shared_like_for_like_worst_dot_overlap=like["worst_forward_overlap_dot_fields"],
            shared_like_for_like_worst_submission=like["worst_forward_overlap_dot_field_submission"],
            note=("Degeneracy-scoped reading per preregistration (halo_cover>=0.99 or "
                  "support>0.20 excluded from dot-overlap only; rho applies to all; "
                  "thresholds unchanged; no vendor change). Literal + shared "
                  "like-for-like readings reported unchanged.")),
    )
    promote = all(g["passed"] for g in gates.values())
    failed = [k for k, g in gates.items() if not g["passed"]]

    card = dict(
        schema="gems86.h86f-run-card.v1",
        lane="H86F-HMDC (trough-gated hydrothermal LOQO-HGB, zero-catalogue)",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        preregistration="registry/preregistration_h86f.json",
        hypothesis=("Blind geothermal fault conduits missing from the USGS/INGENIOUS "
                    "catalogue are recoverable from signed magnetic valley-curvature "
                    "troughs (magnetite destruction) gated by cond_surf x dilatation "
                    "concordance and pairwise co-linear GDR-1391 vent alignments."),
        mechanism=("Frangi dark-vesselness troughs on RTP (Band 2) + tmi_vg (Band 9); "
                   "positive-part z(cond_surf) x z(geod_dilaterate) concordance; chained "
                   "pairwise vent segments (hot springs, volcanic vents, sinter, 2m hits) "
                   "raw + trough-and-concordance-gated; fused with the 38-feature "
                   "label-free substrate in LOQO-HGB (no SPBT, no catalogue context); "
                   f"300 m decimated emission at {int(dots.sum())} dots, >2px off catalogue."),
        named_non_fault_process=("Reversed-polarity volcanic flows / felsic tuffs; saline "
                                 "playa pans; E-W GeoDAWN tie-line troughs."),
        holdout_dti=dict(evidence_class="HOLDOUT-DTI", evaluator_version="gems57-pooled-hide-v2",
                         design="buffered whole components, seed 20, LOQO, 20 km physical-block bootstrap",
                         withheld_positives=int(hold["withheld_positive_pixels"]),
                         value=hold["dti"], ci95=hold["ci95"]),
        holdout_source="docs/evidence/h86f_results.json",
        region_hide_diagnostic=dict(
            evidence_class="HOLDOUT-DTI", design="region-hide (non-gating diagnostic)",
            scores={k: dict(dti=v["dti"], ci95=v["ci95"]) for k, v in results["region_hide_pooled"]["scores"].items()}),
        correlation_overlap_vs_registry=dict(
            worst_nondegenerate_dot_overlap=worst_nd_ov,
            worst_nondegenerate_submission=worst_nd_sub,
            worst_abs_rho_final_dots=worst_rho_dot,
            worst_abs_rho_preplacement_surface=worst_rho_surf,
            degenerate_excluded=len(deg_list),
            literal_worst_overlap=uniq["literal_reading"]["worst_forward_overlap"],
            rasters_checked=len(rows), evidence="docs/evidence/h86f_uniqueness.json"),
        raster_sha256=file_sha,
        validator_output=dict(all_checks_passed=val["all_checks_passed"],
                              n_nan_inside_footprint=int(np.isnan(pred[fp]).sum()),
                              min=val["min"], max=val["max"], checks=val["checks"],
                              emitted_dots=int(dots.sum())),
        gates=gates, gates_failed=failed,
        submission_name=name, note=note, note_chars=len(note),
        submission_file=str(tif.relative_to(ROOT)),
        verdict="promote-to-selector-only" if promote else "negative",
        submission_ready=False, safe_to_submit=False, approved_for_weekly_slot=False,
        decision=("PROMOTE-TO-SELECTOR (selector step still required)" if promote
                  else "DO NOT SUBMIT"),
        decision_reason=("All automated gates passed." if promote
                         else f"Automated gates failed: {', '.join(failed)}. Generated and format-valid, but not cleared for a weekly slot."),
        experiments_run=3, submission_slots_used=0,
        elapsed_s=float(time.time() - t0),
    )
    (ROOT / "docs/evidence/h86f-run-card.json").write_text(json.dumps(card, indent=1) + "\n")
    (ROOT / "docs/evidence/h86f_results.json").write_text(
        (CACHE / "h86f_results.json").read_text())
    print("VERDICT:", card["decision"], "| failed:", failed, flush=True)

    # ---------- register artifact #13 in the audit inventory ----------
    if not promote:
        inv_path = ROOT / "docs/evidence/download-inventory.json"
        inv = json.loads(inv_path.read_text())
        inv["artifacts"].append(dict(file=str(tif.relative_to(ROOT)), sha256=file_sha,
                                     status="DO NOT SUBMIT",
                                     approved_for_weekly_slot=False))
        inv_path.write_text(json.dumps(inv, indent=1) + "\n")
        cards_path = ROOT / "registry/artifact_cards.json"
        cards = json.loads(cards_path.read_text())
        cards["artifacts"].append(dict(
            lane="H86F-HMDC trough-gated hydrothermal LOQO (zero-catalogue)",
            card="docs/evidence/h86f-run-card.json",
            context="docs/evidence/h86f-run-card.json",
            holdout_kind="pooled", stem=stem))
        cards_path.write_text(json.dumps(cards, indent=1) + "\n")
        print("registered artifact #13 (negative branch, current machinery unchanged)")
    else:
        print("PROMOTE: run card written; implement the preregistered promote-rendering "
              "extension (registry/preregistration_h86f.json site_rendering_branches) "
              "before registering the artifact.")
    print(json.dumps({k: v.get("passed") for k, v in gates.items()}, indent=1))


if __name__ == "__main__":
    main()
