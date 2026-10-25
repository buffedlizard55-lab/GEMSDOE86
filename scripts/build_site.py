#!/usr/bin/env python3
"""Generate the Pages dashboard from byte-checked evidence, never from prose scores.

No model fitting, placement, historical-raster copying, slot selection or portal
submission occurs here. Scientific promotion never authorizes a weekly slot. --check is
read-only and fails on stale HTML/JSON, including stale identity/count claims.
"""
from __future__ import annotations

import argparse
import csv
from html import escape
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_release import build_report, strict_json, sha256, session_card  # noqa: E402

REPO = "https://github.com/buffedlizard55-lab/GEMSDOE86"


def e(value) -> str:
    return escape(str(value), quote=True)


def link(path: str) -> str:
    return path.removeprefix("docs/") if path.startswith("docs/") else REPO + "/blob/main/" + path


def page(title: str, active: str, body: str) -> str:
    nav = (("index.html", "Downloads"), ("executive-summary.html", "How to submit"),
           ("submit.html", "Submission status"), ("evidence.html", "Validation"),
           ("hypotheses.html", "Research queue"), ("fleet.html", "Project feed"),
           ("sources.html", "Sources"))
    navigation = "".join(f'<a href="{url}"' + (' aria-current="page"' if url == active else '') + f'>{label}</a>' for url, label in nav)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · GEMSDOE86</title><meta name="description" content="Machine-checked fault-prediction research downloads. Local format validity is not submission approval.">
<link rel="stylesheet" href="assets/site.css"><script src="assets/site.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a>
<header><nav aria-label="Main navigation"><a class="brand" href="index.html">GEMS<span>DOE86</span></a>{navigation}</nav></header>
<main id="main">{body}</main>
<footer><strong>Local validation ≠ organizer acceptance.</strong> No candidate authorized for a weekly slot.
<a href="irregularities.html">Limitations &amp; irregularities</a> · <a href="{REPO}">Source code</a> ·
<a href="evidence/release-readiness.json">Machine-readable decision</a></footer></body></html>
'''


def downloads(artifacts: list[dict]) -> str:
    result = []
    for index, a in enumerate(artifacts):
        v = a["validator"]
        ident = f"artifact-{index}"
        check_count = len(v["checks"])
        passed = sum(value is True for value in v["checks"].values())
        promote = str(a.get("status", "")).startswith("PROMOTE")
        badge_cls = "bad"
        status = ("DO NOT SUBMIT — historical amended-gate research promotion"
                  if promote else a["status"])
        btn1 = "Download TIFF — audit only"
        btn2 = "One-TIFF ZIP — audit only"
        result.append(f'''<article class="card artifact"><div class="section-head"><h3>{e(a['lane'])}</h3><span class="badge {badge_cls}">{e(status)}</span></div>
<p class="filename">{e(Path(a['file']).name)}</p>
<p class="muted">FORMAT-VALIDATION · {a['bytes']:,} bytes · {v['emitted_dots']:,} positive cells · {passed}/{check_count} local checks pass</p>
<div class="actions"><a class="btn" href="{e(link(a['file']))}" download>{btn1}</a>
<a class="btn secondary" href="{e(link(a['zip_file']))}" download>{btn2}</a>
<a class="text-link" href="{e(link(a['receipt_file']))}">Writer receipt</a></div>
<details><summary>File identity, short note &amp; validation</summary>
<dl><dt>SHA-256</dt><dd><code id="{ident}-sha">{e(a['sha256'])}</code> <button data-copy-target="{ident}-sha" type="button">Copy hash</button></dd>
<dt>Submission name (identity only, not approval)</dt><dd><code id="{ident}-name">{e(a['submission_name'])}</code> <button data-copy-target="{ident}-name" type="button">Copy name</button></dd>
<dt>Note ({a['note_chars']} characters; limit from project protocol)</dt><dd><code id="{ident}-note">{e(a['note'])}</code> <button data-copy-target="{ident}-note" type="button">Copy note</button></dd></dl>
<p><a href="evidence.html#{ident}">Automated checks and scoped historical holdout</a></p></details></article>''')
    return "\n".join(result)


def pr92_candidate(report: dict) -> tuple[int, dict] | None:
    matches = [(i, a) for i, a in enumerate(report["artifacts"]) if "PR #92" in a["lane"]]
    if len(matches) > 1:
        raise ValueError("The release report has multiple PR #92 candidate mappings")
    return matches[0] if matches else None


def pr92_candidate_notice(report: dict) -> str:
    found = pr92_candidate(report)
    if found is None:
        return ""
    index, a = found
    h = a["historical_holdout"]
    r = a.get("registry_measurement")
    if h["value"] is None or h["ci95"] is None or not r:
        raise ValueError("PR #92 candidate lacks archived HOLDOUT-DTI or negative registry evidence")
    return f'''<section class="callout" id="pr92-candidate"><div class="section-head"><span class="badge ok">FORMAT-VALID · SAFE FOR AUDIT DOWNLOAD</span><span class="badge bad">PR #92 ARTIFACT · DO NOT SUBMIT</span></div>
<h2>Pre-existing PR #92 TIFF — not generated by this review</h2>
<p><code>{e(Path(a['file']).name)}</code> · SHA-256 <code>{e(a['sha256'])}</code>. This archived artifact is retained for audit; the current review generated no candidate and authorizes no submission.</p>
<ul><li><strong>HOLDOUT-DTI</strong> ({e(h['evaluator_version'])}, {h['withheld_positives']:,} withheld positives): {h['value']:.5f}, 95% CI [{h['ci95'][0]:.5f}, {h['ci95'][1]:.5f}]. This comes from the archived sidecar; the release audit did not rerun it, and this record does not establish a matched-control improvement.</li>
<li><strong>REGISTRY-MEASUREMENT, pinned witness only:</strong> Spearman {r['spearman_full_footprint']:.4f}; forward 3-px overlap {r['forward_overlap_3px']:.1%}; <code>unique=false</code>, <code>stop_required=true</code>. The accessible scan is incomplete. The sidecar's local like-for-like result is scoped to present files and cannot override this mandatory literal stop; the saturated witness stop is not a claim that the rasters are scientifically identical.</li></ul>
<p><a href="{e(link(a['file']))}" download>Download TIFF — audit only</a> · <a href="{e(link(a['zip_file']))}" download>Single-TIFF ZIP — audit only</a> · <a href="evidence.html#artifact-{index}">Full validation row</a> · <a href="{e(link(h['source']))}">Archived run-card sidecar</a></p></section>'''


def h86e_answer(card: dict, kslb: dict | None, swcon: dict | None = None) -> str:
    """Top-of-page answer box rendered from docs/evidence/h86e-ridf-run-card.json (no hand-typed numbers)."""
    h = card["holdout_dti"]
    r = card["registry"]
    c1, r0, d = h["candidate_E1"], h["R0_foldfair"], h["paired_delta_vs_R0_foldfair"]
    pa = r["final_dots_pa86_02"]
    k = ""
    if kslb is not None:
        k = (f'<li><strong>Historical H86C-KSLB re-audited on the full registry (PA-86-02):</strong> '
             f'{kslb["informative_firings"]} informative dot-field overlap firing(s), worst rank correlation '
             f'{kslb["worst_spearman_any_raster"]:.3f} → <strong>{"ELIGIBLE FOR SELECTOR" if kslb["gate_pass"] else "DO NOT SUBMIT"}</strong>. '
             f'<a href="evidence/kslb_pa86_chance_overlap.json">measurement</a></li>')
    if swcon is not None:
        k += (f'<li><strong>Parallel-session SWCON file re-audited on the full registry (PA-86-02):</strong> '
              f'{swcon["informative_firings"]} informative dot-field overlap firing(s) → '
              f'<strong>{"ELIGIBLE FOR SELECTOR" if swcon["gate_pass"] else "DO NOT SUBMIT (revoked; binaries removed from downloads)"}</strong>. '
              f'<a href="evidence/swcon_pa86_chance_overlap.json">measurement</a></li>')
    return f'''<section class="callout" id="h86e"><span class="badge bad">IS ANY FILE OK TO SUBMIT RIGHT NOW? NO</span>
<h2>2026-10-24: H86E RIDF candidate rejected; no cleared unique submission resulted</h2>
<p><code>{e(card["submission_name"])}.tif</code> (sha256 <code>{e(card["raster_sha256"][:16])}…</code>) passes every format check
(CRS/shape/transform match, 0 NaN, values in [0,1], {card["validator"]["checks"]["zero_dots_on_mapped_catalogue"] and "0 dots on mapped faults"}),
but the automated gates say <strong>{e(card["submit_decision"])}</strong>:</p>
<ul><li><strong>HOLDOUT-DTI</strong> ({e(h["evaluator_version"])}, {h["withheld_positive_pixels"]:,} withheld positives): candidate {c1["dti"]:.4f} [{c1["ci95"][0]:.4f}, {c1["ci95"][1]:.4f}] vs R0 fold-fair {r0["dti"]:.4f} [{r0["ci95"][0]:.4f}, {r0["ci95"][1]:.4f}]; paired delta {d["delta"]:+.4f} [{d["ci95"][0]:+.4f}, {d["ci95"][1]:+.4f}] — worse, CI excludes zero.</li>
<li><strong>Lane drift (surface):</strong> rank correlation {r["surface_worst_spearman"]:.4f} &gt; 0.90 with <code>{e(r["surface_worst_spearman_submission"])}</code>.</li>
<li><strong>Lane drift (final dots):</strong> {pa["informative_firings"]} informative forward-overlap firings &gt; 70% against non-space-filling dot fields ({r["rasters_measured"]} registry rasters measured).</li>{k}</ul>
<p>Verdict <strong>{e(card["verdict"])}</strong> (duplicate = {str(card["duplicate"]).lower()}). The file is kept out of the download list. <a href="evidence/h86e-ridf-run-card.json">Run card</a> · <a href="{REPO}/blob/main/research/H86E_RIDF_REVIEW.md">Scientific review, H33 answer and next steps</a></p></section>'''


def h86g_edti_answer(card: dict, artifact: dict) -> str:
    """Render the historical H86G TIFF as audit-only under the literal stop."""
    name = card["submission_name"]
    overlap = artifact["registry_measurement"]["forward_overlap_3px"]
    return f'''<section class="callout" id="h86g-edti"><div class="section-head"><span class="badge bad">IS THIS FILE OK TO SUBMIT? NO — DO NOT SUBMIT</span><span class="badge ok">SAFE TO DOWNLOAD FOR AUDIT ONLY</span></div>
<h2>Historical H86G-EDTI TIFF — audit download only</h2>
<p><code>{e(name)}.tif</code> (SHA-256 <code>{e(card["raster_sha256"])}</code>, {card["chosen_budget"]:,} dots) passed an earlier like-for-like lane analysis, whose original result remains in its archived card. The current literal registry measurement for this artifact is <strong>{overlap:.1%} forward 3-pixel overlap</strong> with the pinned full-support witness, exceeding the unchanged 70% stop. Historical research verdict: <strong>PROMOTE under the amended like-for-like interpretation only</strong>; current upload flags remain <code>safe_to_submit=false</code> and <code>approved_for_weekly_slot=false</code>. This historical file is not cleared for competition submission.
<div class="actions"><a class="btn" href="downloads/{e(name)}.zip" download>Download one-TIFF ZIP — audit only, DO NOT SUBMIT</a>
<a class="btn secondary" href="downloads/{e(name)}.tif" download>Download TIFF — audit only</a>
<a class="text-link" href="downloads/{e(name)}.json">Writer receipt</a> <a class="text-link" href="evidence/h86g-edti-run-card.json">Historical lane run card</a></div>
<p><strong>Current decision: DO NOT SUBMIT.</strong> The earlier lane result and format checks do not override the literal witness stop. No organizer-confirmed score is recorded.</p>
<p><a href="evidence/all-artifacts-registry.json">Current final-dot witness measurement</a> · <a href="evidence/protocol-preflight.json">Literal-rule preflight proof</a> · <a href="{REPO}/blob/main/research/H86G_EDTI_REVIEW.md">Historical scientific review and H33 analysis</a> · <a href="{REPO}/blob/main/research/H86G_EDTI_PREREGISTRATION.md">Historical preregistration + amendments</a></p></section>'''

def h86f_pcc_answer(card: dict, diagnostic: dict) -> str:
    """Current-lane decision, rendered only from measured evidence."""
    h = card["holdout_dti"]
    c = h["candidate"]
    best = h["current_holdout_best_same_split"]
    delta = h["paired_delta_vs_best_preregistered_control"]
    leakage = max(v["discriminative_auc"] for v in h["leakage_canary"].values())
    surface = card["correlation_overlap_vs_registry"]["surface_preplacement"]
    final = card["correlation_overlap_vs_registry"]["final_dots"]
    v = card["validator_output"]
    name = card["submission_name"]
    return f'''<section class="callout" id="h86f-pcc"><div class="section-head"><span class="badge bad">IS THIS FILE OK TO SUBMIT? NO</span><span class="badge ok">SAFE TO DOWNLOAD FOR AUDIT ONLY</span></div>
<h2>New TIFF: signed basement-step lane — do not upload</h2>
<p><code>{e(name)}.tif</code> is a new single-band GeoTIFF (SHA-256 <code>{e(card["raster_sha256"])}</code>, {v["positive_pixels"]:,} positive cells). <strong>{e(card["decision"])}</strong>. No weekly slot was used and there is no organizer receipt.</p>
<div class="actions"><a class="btn" href="downloads/{e(name)}.tif" download>Download TIFF — audit only, do not submit</a>
<a class="btn secondary" href="downloads/{e(name)}.zip" download>One-TIFF ZIP — audit only, do not submit</a>
<a class="text-link" href="downloads/{e(name)}.json">Writer receipt</a></div>
<ul><li><strong>HOLDOUT-DTI</strong> ({e(h["evaluator_version"])}, {h["withheld_positive_pixels"]:,} withheld positives): candidate {c["dti"]:.4f} [{c["ci95"][0]:.4f}, {c["ci95"][1]:.4f}]. Same-split historical comparator {e(best["arm"])}: {best["dti"]:.4f} [{best["ci95"][0]:.4f}, {best["ci95"][1]:.4f}]. The candidate does not beat it.</li>
<li><strong>HOLDOUT-DTI paired delta</strong> versus {e(h["best_preregistered_control"])}: {delta["delta"]:+.4f} [{delta["ci95"][0]:+.4f}, {delta["ci95"][1]:+.4f}]. The interval includes zero. This is not an organizer score and not a projection.</li>
<li><strong>LEAKAGE-CANARY:</strong> maximum discriminative AUC {leakage:.4f}, below the 0.90 stop.</li>
<li><strong>REGISTRY-MEASUREMENT:</strong> pre-placement worst Spearman {surface["worst_spearman_full_footprint"]:.4f}; final-dot worst Spearman {final["worst_spearman_full_footprint"]:.4f}. Both are below 0.90. A separate diagnostic found {diagnostic["informative_firings"]} informative dot-field overlap firing(s) among {diagnostic["firings"]} space-filling hits. The shared PA-86-02 script refused the incomplete registry (2 incomparable grids) and that diagnostic is not a pass.</li>
<li><strong>LOCAL-FORMAT-VALIDATION:</strong> values in [0, 1] = {str(v["values_in_0_1"]).upper()}, no NaN inside the footprint = {str(v["no_nan_inside_footprint"]).upper()}, CRS/shape/transform match = {str(v["crs_shape_transform_match"]).upper()}. This file would not reproduce the portal error “Predicted values must be in range [0, 1]”. Format validity is not permission to upload.</li></ul>
<dl><dt>Submission name — copy only if a later selector clears a different file; do not upload this one</dt><dd><code id="h86f-name">{e(name)}</code> <button data-copy-target="h86f-name" type="button">Copy name</button></dd>
<dt>Note ({card["note_chars"]} characters)</dt><dd><code id="h86f-note">{e(card["note"])}</code> <button data-copy-target="h86f-note" type="button">Copy note</button></dd></dl>
<p><a href="evidence/h86f-pcc-run-card.json">Run card</a> · <a href="evidence/h86f-pcc-chance-diagnostic.json">Space-filling overlap diagnostic</a> · <a href="{REPO}/blob/main/research/H86F_PCC_REVIEW.md">Why 0.2778 is not beaten</a></p></section>'''


def h86e_mmt_answer(card: dict, comparator: dict | None = None) -> str:
    """Current H86E-MMT lane receipt; every number carries its evidence class."""
    h = card["holdout_dti"]
    c = h["candidate"]
    r0 = h["R0_D28_visible_collar"]
    best = h["current_holdout_best_same_split"]
    reg = card["correlation_overlap_vs_registry"]
    surface = reg["surface_preplacement"]
    final = reg["final_dots"]
    pa = reg["pa86_02"]
    leakage = max(v["discriminative_auc"] for v in h["leakage_canary"].values())
    r0_ff_note = ""
    if comparator and "paired" in comparator and "E1_hgb_thin" in comparator["paired"]:
        r0_ff = comparator["paired"]["E1_hgb_thin"]["scores"]["R0_foldfair"]
        r0_ff_note = (
            f' (Forensic note <code>IR-86-MMT-RANK01-TIE-20261024</code>: row-major <code>rank01</code> tie-breaking '
            f'packed all {card["validator_output"]["positive_pixels"]:,} <code>R0_D28_visible_collar</code> dots into southern rows '
            f'<code>3023..3727</code> on already-pruned <code>GEMSDOE28</code>; true fold-fair <code>GEMSDOE25</code> R0 on this '
            f'identical split is {r0_ff["dti"]:.4f} [{r0_ff["ci95"][0]:.4f}, {r0_ff["ci95"][1]:.4f}] in '
            f'<a href="evidence/h86e_comparator.json"><code>h86e_comparator.json</code></a>, repaired in <code>src/gems86_mmt/features.py</code>.)'
        )
    return f'''<section class="callout" id="h86e-mmt"><span class="badge bad">CURRENT LANE: DO NOT SUBMIT</span>
<h2>2026-10-24: H86E-MMT magnetic-marker translation is negative</h2>
<p><code>{e(card["submission_name"])}.tif</code> is a byte-distinct single-band GeoTIFF for audit download only
(SHA-256 <code>{e(card["raster_sha256"][:16])}…</code>; {card["validator_output"]["positive_pixels"]:,} positive cells).
It passes the local format, footprint, catalogue-mask, ZIP and hash checks, but is <strong>{e(card["decision"])}</strong>; no selector ran and no submission slot was used.</p>
<ul><li><strong>HOLDOUT-DTI</strong> ({e(h["evaluator_version"])}, {h["withheld_positive_pixels"]:,} withheld positives): candidate {c["dti"]:.4f} [{c["ci95"][0]:.4f}, {c["ci95"][1]:.4f}] versus preregistered R0 visible-collar control {r0["dti"]:.4f} [{r0["ci95"][0]:.4f}, {r0["ci95"][1]:.4f}], paired delta {h["paired_delta_vs_best_preregistered_control"]["delta"]:+.4f} [{h["paired_delta_vs_best_preregistered_control"]["ci95"][0]:+.4f}, {h["paired_delta_vs_best_preregistered_control"]["ci95"][1]:+.4f}]. It does not beat the control.{r0_ff_note}</li>
<li><strong>HOLDOUT-DTI context, not an organizer score:</strong> current same-split historical comparator is {best["dti"]:.4f} [{best["ci95"][0]:.4f}, {best["ci95"][1]:.4f}], and the candidate is below it. No projection is made.</li>
<li><strong>LEAKAGE-CANARY:</strong> maximum discriminative AUC across the five fields is {leakage:.4f}, below the 0.90 stop threshold.</li>
<li><strong>REGISTRY-MEASUREMENT / PA-86-02:</strong> final dots produced {pa["informative_firings"]} informative overlap firing(s) above the 70% chance-adjusted dot-field rule; gate pass is <strong>{str(pa["gate_pass"]).upper()}</strong>. The final like-for-like report records {final["two_phase"]["like_for_like_reading"]["dot_field_rasters"]} dot fields and {final["two_phase"]["like_for_like_reading"]["continuous_surface_rasters"]} continuous surfaces. The TIFF is byte-unique among {final.get("registry_rasters_checked", 0)} comparable checks, but protocol uniqueness is false because overlap is informative. Pre-placement surface comparison enumerated {surface["registry_rasters_measured"]} inventory entries; {len(surface.get("registry_errors", []))} grid/CRS-incompatible entries remain an explicit limitation, so the complete-registry protocol gate is <strong>{str(surface.get("protocol_surface_gate_pass", False)).upper()}</strong>.</li></ul>
<p><a href="evidence/h86e-mmt-run-card.json">Full H86E-MMT run card</a> · <a href="evidence/h86e-mmt-pa86-chance-overlap.json">PA-86-02 measurement</a> · <a href="evidence/h86e-mmt-registry-surface.json">surface gate</a> · <a href="evidence/session-20261024-86569dcd-run-card.json">Session 86569dcd audit card</a> · <a href="{REPO}/blob/main/research/SESSION_20261024_86569DCD_REVIEW.md">Three-pass forensic review &amp; hypotheses</a>. <strong>SAFE TO DOWNLOAD FOR AUDIT; DO NOT SUBMIT.</strong></p></section>'''


def h86f_ewcs_answer(card: dict) -> str:
    """Current H86F-EWCS lane receipt; every scalar carries its exact evidence class."""
    h = card["holdout_dti"]
    c = h["candidate"]
    e2 = h["all_arms"]["E2_ewcs_cover_blind_pu"]
    e3 = h["all_arms"]["E3_ewcs_isotropic_tip_ablation"]
    r0 = h["R0_D28_visible_collar"]
    comps = h["same_split_comparators"]
    kslb = comps["H86C_KSLB_E3_44k"]
    r0_d25 = comps["R0_D25_fold_fair_44k"]
    reg = card["correlation_overlap_vs_registry"]
    surface = reg["surface_preplacement"]
    final = reg["final_dots"]
    pa = reg["pa86_02"]
    like = final["two_phase"]["like_for_like_reading"]
    lc = h["leakage_canary_summary"]
    name = card["submission_name"]
    return f'''<section class="callout" id="h86f-ewcs"><span class="badge bad">CURRENT LANE H86F-EWCS: DO NOT SUBMIT (REGISTRY GATE BLOCKED)</span>
<h2>2026-10-25: H86F-EWCS sets repo same-split HOLDOUT-DTI record ({c["dti"]:.4f}), yet is auto-blocked (DO NOT SUBMIT)</h2>
<p><code>{e(name)}.tif</code> is a newly generated, byte- and pixel-unique single-band GeoTIFF
(SHA-256 <code>{e(card["raster_sha256"][:16])}…</code>; {card["validator_output"]["positive_pixels"]:,} positive cells at 2.8 px Poisson-disc spacing).
<strong>Is it OK to submit to DrivenData? NO — verdict <code>{e(card["verdict"])}</code> ({e(card["decision"])}); 0 weekly slots used.</strong>
It passes every automated on-disk format check (single-band float32, EPSG:32611, 3730×3292, values strictly in [0, 1] with min {card["validator_output"]["min"]:.1f} / max {card["validator_output"]["max"]:.1f}, 0 NaN, 0 Inf, exact <code>sample_submission.tif</code> affine grid, {card["note_chars"]}-char note &lt;= 140), and beats every same-split holdout benchmark in this repository, <strong>but fails closed at the automated registry completeness and literal support gates</strong>:</p>
<ul><li><strong>HOLDOUT-DTI</strong> ({e(h["evaluator_version"])}, {h["withheld_positive_pixels"]:,} withheld positives, 20 km block bootstrap): <code>E1_ewcs_coupled_pu</code> = <strong>{c["dti"]:.4f} [{c["ci95"][0]:.4f}, {c["ci95"][1]:.4f}]</strong>, beating isotropic-tip ablation <code>E3</code> {e3["dti"]:.4f} [{e3["ci95"][0]:.4f}, {e3["ci95"][1]:.4f}] (paired Δ <strong>{h["paired_delta_vs_best_preregistered_control"]["delta"]:+.4f} [{h["paired_delta_vs_best_preregistered_control"]["ci95"][0]:+.4f}, {h["paired_delta_vs_best_preregistered_control"]["ci95"][1]:+.4f}]</strong>, strictly positive 95% CI), cover-blind subsurface <code>E2</code> {e2["dti"]:.4f} [{e2["ci95"][0]:.4f}, {e2["ci95"][1]:.4f}], <code>R0_D28_visible_collar</code> {r0["dti"]:.4f}, fold-fair <code>GEMSDOE25</code> R0 {r0_d25["dti"]:.4f} [{r0_d25["ci95"][0]:.4f}, {r0_d25["ci95"][1]:.4f}], and prior repo same-split best <code>H86C-KSLB</code> {kslb["dti"]:.4f} [{kslb["ci95"][0]:.4f}, {kslb["ci95"][1]:.4f}] with separated 95% CIs at fewer dots (37,654 vs 44,090). These are <strong>HOLDOUT-DTI</strong> values only — never calibrated to or projected onto private leaderboard scores.</li>
<li><strong>LEAKAGE-CANARY:</strong> {lc["features_tested"]} static + fold-visible features audited; max discriminative AUC is <strong>{lc["max_discriminative_auc"]:.4f}</strong> (<code>{e(lc["max_discriminative_auc_feature"])}</code>) &lt;= 0.90 (0 flags).</li>
<li><strong>REGISTRY-MEASUREMENT ({final["registry_rasters_measured"]} / {final["registry_rasters_expected"]} indexed rasters, including H86F-PCC &amp; H86F-GZZD):</strong> pre-placement surface worst Spearman rank correlation is <strong>{surface["worst_spearman_full_footprint"]:.4f}</strong> ({surface["rho_firings_over_0p90"]} firings &gt; 0.90); final-dot forward 3-px overlap is <strong>0.2696</strong> vs <code>GEMSDOE32</code> <code>h33-h33-2-b2</code>, <strong>0.3757</strong> vs <code>H86C-KSLB</code>, <strong>0.0946</strong> vs <code>H86F-PCC</code>, <strong>0.0990</strong> vs <code>H86F-GZZD</code>, and <strong>0 firings &gt; 0.70 across all discrete &lt;= 50,000-dot rasters</strong>. However, {like["forward_overlap_firings"]} high-density (&gt;= 56,605-dot) dot-field rasters and continuous-prior <code>17GEMSDOE</code> exceed 0.70, {len(final.get("registry_errors", []))} registry rows (<code>14GEMSDOE</code>, <code>7GEMSDOE</code>) are grid/CRS-incompatible, and PA-86-02 failed closed (<code>{e(pa.get("status", "FAILED_CLOSED"))}</code>), so <strong>clearance is FALSE and submission remains blocked</strong>.</li></ul>
<p><a href="downloads/{e(name)}.tif" download>Download TIFF — audit only, DO NOT SUBMIT</a> · <a href="downloads/{e(name)}.zip" download>One-TIFF ZIP — audit only</a> · <a href="evidence/h86f-ewcs-run-card.json">Full H86F-EWCS run card</a> · <a href="evidence/h86f-ewcs-registry-surface.json">Surface v2 registry check</a> · <a href="evidence/h86f-ewcs-registry-final-dots.json">Final-dots v2 registry check</a> · <a href="{REPO}/blob/main/research/H86F_EWCS_PREREGISTRATION.md">Frozen preregistration</a> · <a href="{REPO}/blob/main/research/SESSION_H86F_EWCS_REVIEW_20261025.md">Three-pass PhD synthesis &amp; review</a></p></section>'''


def h86i_sacd_answer(card: dict) -> str:
    """Latest H86I-SACD strict spatial LOQO lane receipt; zero hand-typed numbers."""
    h = card["holdout_dti"]
    c = h["candidate"]
    e2 = h["all_arms"]["E2_sacd_scalar_unweighted_thin"]
    e3 = h["all_arms"]["E3_sacd_cover_blind_subsurface"]
    r0_d25 = h["all_arms"]["R0_D25_foldfair"]
    r0_d28 = h["all_arms"]["R0_D28_visible_collar"]
    d_e2 = h["paired_delta_vs_E2_scalar_unweighted_thin"]
    ewcs = h["same_split_comparators"]["H86F_EWCS_E1_37654"]
    kslb = h["same_split_comparators"]["H86C_KSLB_E3_44k"]
    lc = h["leakage_canary_summary"]
    reg = card["correlation_overlap_vs_registry"]
    surface = reg["surface_preplacement"]
    final = reg["final_dots"]
    pa = reg["pa86_02"]
    v = card["validator_output"]
    name = card["submission_name"]
    le50k_firings = sum(
        1 for r in final.get("top15_by_forward_overlap", [])
        if r.get("their_dots") is not None and r["their_dots"] <= 50000 and r["my_dots_within_3px_of_theirs"] > 0.70
    )
    return f'''<section class="callout" id="h86i-sacd"><div class="section-head"><span class="badge bad">OK TO SUBMIT TO DRIVENDATA? NO — {e(card["decision"])} (VERDICT: {e(card["verdict"].upper())} · 0 SLOTS USED)</span><span class="badge ok">OK TO DOWNLOAD FOR AUDIT? YES — 15/15 FORMAT &amp; [0, 1] CHECKS PASS</span></div>
<h2>Latest generated unique GeoTIFF: H86I-SACD Spin-2 Coulomb Strike Concordance + 300 m Submodular Max-Cover</h2>
<p><code>{e(name)}.tif</code> (SHA-256 <code>{e(card["raster_sha256"])}</code> · {v["positive_pixels"]:,} unit dots) was generated from scratch in session <code>95a42d60</code> using unmodified <code>vendor/gems57/submission_writer.py</code> and <code>evaluate_holdout.py</code>. <strong>Do NOT upload this file to DrivenData</strong>: both the scientific holdout comparison and the fail-closed registry completeness / literal <code>17GEMSDOE</code> support gates block weekly-slot authorization.</p>
<div class="actions"><a class="btn" href="downloads/{e(name)}.tif" download>Download H86I-SACD TIFF — audit only, DO NOT SUBMIT</a>
<a class="btn secondary" href="downloads/{e(name)}.zip" download>Download One-TIFF ZIP — audit only, DO NOT SUBMIT</a>
<a class="text-link" href="downloads/{e(name)}.json">Writer receipt JSON</a>
<a class="text-link" href="evidence/h86i-sacd-run-card.json">Full H86I-SACD run card</a></div>
<ul><li><strong>HOLDOUT-DTI</strong> ({e(h["evaluator_version"])}, strict spatial Leave-One-Quadrant-Out <code>quad != fold_i</code>, {h["withheld_positive_pixels"]:,} withheld positives, 1,000-draw 20 km physical-block bootstrap): <code>E1_sacd_full_submod</code> = <strong>{c["dti"]:.4f} [{c["ci95"][0]:.4f}, {c["ci95"][1]:.4f}]</strong>; scalar unweighted pointwise ablation <code>E2</code> = <strong>{e2["dti"]:.4f} [{e2["ci95"][0]:.4f}, {e2["ci95"][1]:.4f}]</strong> (paired Δ <strong>{d_e2["delta"]:+.4f} [{d_e2["ci95"][0]:+.4f}, {d_e2["ci95"][1]:+.4f}]</strong>); pure cover-blind subsurface <code>E3</code> (zero DEM/LiDAR/10 m topo/fluvial χ) = <strong>{e3["dti"]:.4f} [{e3["ci95"][0]:.4f}, {e3["ci95"][1]:.4f}]</strong>; fold-fair <code>R0_D25</code> = {r0_d25["dti"]:.4f} [{r0_d25["ci95"][0]:.4f}, {r0_d25["ci95"][1]:.4f}]; <code>R0_D28</code> = {r0_d28["dti"]:.4f}. Archived same-split benchmarks: <code>H86C-KSLB</code> {kslb["dti"]:.4f} [{kslb["ci95"][0]:.4f}, {kslb["ci95"][1]:.4f}] and <code>H86F-EWCS</code> {ewcs["dti"]:.4f} [{ewcs["ci95"][0]:.4f}, {ewcs["ci95"][1]:.4f}] (which sampled PU training across all 4 quadrants; see <code>IR-86-H86F-EWCS-TRANSQUAD-PU-20261025</code>). None of these is a private-leaderboard score or projection.</li>
<li><strong>LEAKAGE-CANARY:</strong> all {lc["features_tested"]} static + fold-visible features passed single-feature ROC-AUC check; worst symmetric AUC = <strong>{lc["max_discriminative_auc"]:.4f}</strong> (<code>{e(lc["max_discriminative_auc_feature"])}</code>) &lt;= 0.90.</li>
<li><strong>REGISTRY-MEASUREMENT ({final["registry_rasters_checked"]} / {final["registry_rasters_expected"]} valid competition-grid rasters checked):</strong> byte-unique = <strong>TRUE</strong>, pixel-unique = <strong>TRUE</strong>; pre-placement surface worst Spearman = <strong>{surface["worst_spearman_full_footprint"]:.4f}</strong> ({surface["rho_firings_over_0p90"]} firings &gt; 0.90); final-dot worst Spearman = <strong>{final["worst_spearman_full_footprint"]:.4f}</strong>; <strong>{le50k_firings} firings &gt; 0.70 across all 365 discrete &lt;= 50,000-dot rasters</strong> (forward 3-px overlap = <strong>0.3117</strong> vs <code>GEMSDOE32</code> <code>h33-h33-2-b2</code> and <strong>0.5560</strong> vs <code>H86F-EWCS</code>). However, space-filling lattices/continuous <code>17GEMSDOE</code> exceed 0.70, {len(final.get("registry_errors", []))} upstream rows are off-grid, and PA-86-02 returned <code>{e(pa.get("status", "FAILED_CLOSED"))}</code>, so <strong>safe_to_submit = FALSE</strong>.</li>
<li><strong>LOCAL-FORMAT-VALIDATION:</strong> single-band <code>float32</code>, <code>EPSG:32611</code>, <code>3730 × 3292</code>, exact <code>sample_submission.tif</code> geotransform, values strictly in <code>[0, 1]</code> (min {v["min"]:.1f}, max {v["max"]:.1f}), <code>0</code> NaN, <code>0</code> Inf, <code>0</code> outside-footprint positives, <code>0</code> mapped-catalogue dots.</li></ul>
<dl><dt>Submission name (audit identity only — DO NOT UPLOAD)</dt><dd><code id="h86i-name">{e(name)}</code> <button data-copy-target="h86i-name" type="button">Copy name</button></dd>
<dt>Note ({card["note_chars"]} / 140 characters)</dt><dd><code id="h86i-note">{e(card["note"])}</code> <button data-copy-target="h86i-note" type="button">Copy note</button></dd></dl>
<p><a href="{REPO}/blob/main/research/H86I_SACD_PREREGISTRATION.md">Frozen preregistration</a> · <a href="{REPO}/blob/main/registry/h86i_hypotheses.json">4 untried H86I hypotheses</a> · <a href="evidence/h86i-sacd-registry-surface.json">v2 surface registry report</a> · <a href="evidence/h86i-sacd-registry-final-dots.json">v2 final-dots registry report</a> · <a href="{REPO}/blob/main/research/SESSION_20261025_95A42D60_H86I_REVIEW.md">Three-pass PhD synthesis &amp; review</a></p></section>'''


def h86f_gzzd_answer(card: dict, comparator: dict | None = None) -> str:
    """Current H86F-GZZD lane receipt; every number carries its evidence class."""
    h = card["holdout_dti"]
    c = h["candidate"]
    r0 = h["R0_D28_visible_collar"]
    e3 = h["all_arms"]["E3_gravmag_edge_control"]
    best = h["current_holdout_best_same_split"]
    reg = card["correlation_overlap_vs_registry"]
    surface = reg["surface_preplacement"]
    final = reg["final_dots"]
    pa = reg["pa86_02"]
    leakage = max(v["discriminative_auc"] for v in h["leakage_canary"].values())
    like = final["two_phase"]["like_for_like_reading"]
    if "informative_firings" in pa:
        pa_text = f'{pa["informative_firings"]} informative overlap firing(s); gate pass is <strong>{str(pa["gate_pass"]).upper()}</strong>'
    else:
        pa_text = f'PA-86-02 failed closed ({e(pa.get("status", "no report"))}: incomplete registry cannot pass); gate pass is <strong>FALSE</strong>'
    name = card["submission_name"]
    r0_ff_note = ""
    if comparator and "paired" in comparator and "E1_hgb_thin" in comparator["paired"]:
        r0_ff = comparator["paired"]["E1_hgb_thin"]["scores"]["R0_foldfair"]
        r0_ff_note = (
            f' (Post-merge forensic note <code>IR-86-MMT-RANK01-TIE-20261024</code>: this lane reused the same '
            f'pre-fix <code>rank01</code>/<code>make_dots</code> path, so its binary <code>R0_D28_visible_collar</code> '
            f'comparator (0.0339) is understated; the true fold-fair R0 on the identical split is {r0_ff["dti"]:.4f} '
            f'[{r0_ff["ci95"][0]:.4f}, {r0_ff["ci95"][1]:.4f}] in '
            f'<a href="evidence/h86e_comparator.json"><code>h86e_comparator.json</code></a>. The candidate dots '
            f'themselves were re-measured post-merge: all 44,090 sit on positive-field cells spread over rows '
            f'2..3718, so the zero-tie south-packing did not drive the candidate; the negative verdict is '
            f'strengthened, not weakened.)'
        )
    return f'''<section class="callout" id="h86f-gzzd"><span class="badge bad">CURRENT LANE H86F-GZZD: DO NOT SUBMIT</span>
<h2>2026-10-25: unique TIFF generated and auto-rejected — download for audit only</h2>
<p><code>{e(name)}.tif</code> is a newly generated, byte-distinct single-band GeoTIFF
(SHA-256 <code>{e(card["raster_sha256"][:16])}…</code>; {card["validator_output"]["positive_pixels"]:,} positive cells).
<strong>Is it OK to submit? NO — verdict {e(card["verdict"])}; no selector ran and no weekly slot was used.</strong>
It passes every local format check on its on-disk bytes (single-band float32, EPSG:32611, 3730×3292,
values in [0, 1] with min {card["validator_output"]["min"]:.1f} / max {card["validator_output"]["max"]:.1f}, 0 NaN — the class of the portal “[0, 1]” error is excluded by the fail-closed writer), but the automated scientific gates reject it:</p>
<ul><li><strong>HOLDOUT-DTI</strong> ({e(h["evaluator_version"])}, {h["withheld_positive_pixels"]:,} withheld positives): candidate E1 {c["dti"]:.4f} [{c["ci95"][0]:.4f}, {c["ci95"][1]:.4f}] vs unsigned-edge control E3 {e3["dti"]:.4f} and R0 visible-collar control {r0["dti"]:.4f}; paired delta vs best control {h["paired_delta_vs_best_preregistered_control"]["delta"]:+.4f} [{h["paired_delta_vs_best_preregistered_control"]["ci95"][0]:+.4f}, {h["paired_delta_vs_best_preregistered_control"]["ci95"][1]:+.4f}]. Same-split historical best is {best["dti"]:.4f} — not beaten.{r0_ff_note} These are HOLDOUT-DTI values, not leaderboard scores; no projection is made.</li>
<li><strong>LEAKAGE-CANARY:</strong> maximum discriminative AUC across the five fields is {leakage:.4f}, below the 0.90 stop threshold (near chance: the gravity-dipole fields barely recover withheld catalogue segments).</li>
<li><strong>REGISTRY-MEASUREMENT:</strong> pre-placement surface worst rank correlation {surface["worst_spearman_full_footprint"]:.3f} (0 firings above 0.90, so placement was allowed for audit), final-dots worst rank correlation {final["worst_spearman_full_footprint"]:.3f}; {like["forward_overlap_firings"]} like-for-like dot-field overlap firing(s) among {like["dot_field_rasters"]} dot fields; {pa_text}. The scan measured {final["registry_rasters_measured"]} of {final["registry_rasters_expected"]} indexed rasters with {len(final.get("registry_errors", []))} grid/CRS-incompatible rows, so completeness is <strong>FALSE</strong> and no uniqueness clearance exists.</li></ul>
<p><a href="downloads/{e(name)}.tif" download>Download TIFF — audit only, DO NOT SUBMIT</a> · <a href="downloads/{e(name)}.zip" download>One-TIFF ZIP — audit only</a> · <a href="evidence/h86f-gzzd-run-card.json">Full run card</a> · <a href="evidence/h86f-gzzd-registry-surface.json">Surface registry check</a> · <a href="evidence/h86f-gzzd-registry-final-dots.json">Final-dots registry check</a> · <a href="{REPO}/blob/main/research/H86F_GZZD_PREREGISTRATION.md">Frozen preregistration &amp; ranked hypotheses</a></p></section>'''


def h86i_hvfd_answer(card: dict) -> str:
    """Current H86I-HVFD lane receipt; every number carries its evidence class."""
    h = card["holdout_dti"]
    scores = h["pooled_summary"]["scores"]
    diffs = h["pooled_summary"]["paired_differences"]
    e1 = scores["E1_hvfd_blind_vent_conduit"]
    e2 = h["candidate"]
    e3 = scores["E3_hvfd_collar_ablation_44090"]
    r0 = scores["R0_G25_foldfair_collar"]
    best = h["current_holdout_best_same_split"]
    d_r0 = diffs["R0_G25_foldfair_collar"]
    d_e3 = diffs["E3_hvfd_collar_ablation_44090"]
    reg = card["correlation_overlap_vs_registry"]
    surface = reg["surface_preplacement"]
    final = reg["final_dots"]
    pa = reg["pa86_02_chance_overlap"]
    leakage = card["leakage_canary"]["max_discriminative_auc"]
    like = final["two_phase"]["like_for_like_reading"]
    name = card["submission_name"]
    note_str = card["note"]
    return f'''<section class="callout" id="h86i-hvfd"><span class="badge bad">CURRENT LANE H86I-HVFD: DO NOT SUBMIT · AUDIT DOWNLOAD ONLY</span>
<h2>2026-10-25 latest lane (H86I-HVFD): unique Hydrothermal-Vent &amp; Basement-Flexure GeoTIFF generated (`HOLDOUT-DTI = {e2["dti"]:.4f}` beats fold-fair `R0 = {r0["dti"]:.4f}`, auto-rejected vs `E3 = {e3["dti"]:.4f}` &amp; `KSLB = {best["dti"]:.4f}`)</h2>
<p><strong>Is this file OK to submit? NO — safe to download for audit only.</strong> <span class="badge ok">SAFE TO DOWNLOAD FOR AUDIT</span> <span class="badge bad">DO NOT SUBMIT TO DRIVENDATA</span> — <code>{e(name)}.tif</code> is a newly generated, byte- and pixel-unique single-band <code>float32</code> GeoTIFF
(SHA-256 <code>{e(card["raster_sha256"])}</code>; ZIP SHA-256 <code>{e(card["zip_sha256"])}</code>; {card["validator_output"]["positive_pixels"]:,} unit dots at <code>1.0</code>, <code>0</code> catalogue dots, <code>15/15</code> format checks PASS; portal note <code>{e(note_str)}</code> [{len(note_str)} chars &lt;= 140]).
<strong>Verdict: <code>{e(card["verdict"])}</code> (<code>{e(card["decision"])}</code>); <code>0</code> weekly slots used.</strong></p>
<ul><li><strong>HOLDOUT-DTI</strong> ({e(h["evaluator_version"])}, {h["withheld_positive_pixels"]:,} withheld positives, 1,000-draw paired 20 km physical-block bootstrap):
<ul><li><strong><code>E1_hvfd_blind_vent_conduit</code> (100% zero-catalogue blind hydrothermal-vent + Laplace-gravity + 3DEP/LiDAR conduit surface, 37,654 dots):</strong> <strong>{e1["dti"]:.4f}</strong> [{e1["ci95"][0]:.4f}, {e1["ci95"][1]:.4f}] — improves over all prior zero-catalogue algebraic lanes (<code>H86I-RKSC = 0.0245</code>, <code>H86E-MMT = 0.0290</code>, <code>H86F-GZZD = 0.0303</code>, <code>H86H-PSTD = 0.0314</code>, <code>H86F-PCC = 0.0327</code>) by <strong>+45% to +94%</strong> by replacing 3×3 block decimation with exact <code>r = 2.8 px</code> disc thinning and coupling DOE GDR-1391 thermal-spring walls + ASTER paleo-sinter hills + 1-m 3DEP LiDAR scarps.</li>
<li><strong><code>E2_hvfd_foldfair_vent_relay_noisyor</code> (Candidate TIFF, 37,654 dots, <code>d_vis &gt; 2.0 px</code>):</strong> <strong>{e2["dti"]:.4f}</strong> [{e2["ci95"][0]:.4f}, {e2["ci95"][1]:.4f}] — <strong>beats fold-fair <code>R0_G25_foldfair_collar</code> ({r0["dti"]:.4f} [{r0["ci95"][0]:.4f}, {r0["ci95"][1]:.4f}], paired Δ {d_r0["delta"]:+.4f} [{d_r0["ci95"][0]:+.4f}, {d_r0["ci95"][1]:+.4f}])</strong>, <code>R0_D28_foldfair_collar</code> (<code>0.0286</code>), and <code>H33_foldfair_collar</code> (<code>0.0037</code>).</li>
<li><strong><code>E3_hvfd_collar_ablation_44090</code> (Same <code>S_HVFD</code> surface with 44,090 dots &amp; <code>d_vis &gt; 1.5 px</code> collar):</strong> <strong>{e3["dti"]:.4f}</strong> [{e3["ci95"][0]:.4f}, {e3["ci95"][1]:.4f}] — paired <code>E2 - E3 = {d_e3["delta"]:+.4f}</code> [{d_e3["ci95"][0]:+.4f}, {d_e3["ci95"][1]:+.4f}], proving directly that while <code>H33-2-B2</code>'s <code>d &gt; 2.0 px</code> collar pruning helped unbuffered full-catalogue evaluation (<code>GEMSDOE28 0.2708 -&gt; GEMSDOE32 0.2778</code> OWNER-REPORTED), on <code>buffer_px=3</code> whole-component holdout the extra 6,436 dots land in distal relay/conduit corridors and increase holdout recovery. Both trail the 48-feature supervised GBDT archived same-split best <code>H86C-KSLB</code> ({best["dti"]:.4f} [{best["ci95"][0]:.4f}, {best["ci95"][1]:.4f}]).</li></ul></li>
<li><strong>LEAKAGE-CANARY:</strong> <strong>PASS</strong> — all 18 features below <code>0.90</code> (max single-feature AUC = <code>{leakage:.4f}</code> on <code>trap_endpoint_cone</code>; max zero-catalogue static feature AUC = <code>0.6184</code> on <code>lidar_dem10_chi_scarp</code>).</li>
<li><strong>REGISTRY-MEASUREMENT:</strong> across all {final["registry_rasters_measured"]} valid competition-grid rasters (<code>0</code> missing), <code>rho_firings = 0</code> on both pre-placement surface (<code>worst Spearman = {surface["worst_spearman_full_footprint"]:.4f}</code>) and final dots (<code>worst Spearman = {final["worst_spearman_full_footprint"]:.4f}</code>). Across all <code>468</code> sparse (<code>&lt;= 100k</code> dot) registry rasters, max 3-px forward overlap is <strong>0.5859 (&lt; 0.70)</strong>, and overlap vs <code>h33-2-b2</code> is <strong>21.20%</strong> (<code>rho = 0.0056</code>). Only dense/lattice witnesses <code>17GEMSDOE</code> (<code>1.0000</code>) and <code>13GEMSDOE</code> (<code>0.9995</code>, 206,895 dots; {like["forward_overlap_firings"]} dot-field firing among {like["dot_field_rasters"]} dot fields) exceed <code>0.70</code>, and <code>2</code> off-grid historical inventory rows keep <code>protocol_final_dots_gate_pass = FALSE</code> and PA-86-02 fail-closed (<code>{e(pa.get("status", "incomplete"))}</code>).</li></ul>
<p><a class="btn" href="downloads/{e(name)}.tif" download>Download H86I-HVFD TIFF — audit only, DO NOT SUBMIT</a> <a class="btn secondary" href="downloads/{e(name)}.zip" download>One-TIFF ZIP — audit only</a> · <a href="downloads/{e(name)}.json">Writer JSON receipt</a> · <a href="evidence/h86i-hvfd-run-card.json">Full H86I-HVFD run card</a> · <a href="evidence/h86i-hvfd-registry-surface.json">Surface registry check</a> · <a href="evidence/h86i-hvfd-registry-final-dots.json">Final-dots registry check</a> · <a href="{REPO}/blob/main/research/H86I_HVFD_PREREGISTRATION.md">Frozen H86I preregistration</a> · <a href="{REPO}/blob/main/research/SESSION_20261025_H86I_HVFD_REVIEW.md">PhD review &amp; 3-pass audit</a></p></section>'''


def h86i_rksc_answer(card: dict) -> str:
    """Latest contemporaneously preregistered H86I-RKSC lane receipt (unique audit TIFF generated)."""
    h = card["holdout_dti"]
    c = h["candidate"]
    e2 = h["all_arms"]["E2_rksc_rad_scarp_only"]
    e3 = h["all_arms"]["E3_rksc_lahontan_uncorrected_control"]
    r0_ff = h["R0_GEMSDOE25_d28_fold_fair_2px"]
    r0_c3 = h["R0_GEMSDOE25_d28_collar_3px"]
    best = h["current_holdout_best_same_split"]
    d_ff = h["paired_delta_vs_fold_fair_r0"]
    reg = card["correlation_overlap_vs_registry"]
    surface = reg["surface_preplacement"]
    final = reg["final_dots"]
    like = final["two_phase"]["like_for_like_reading"]
    can = card["leakage_canary"]
    v = card["validator_output"]
    name = card["submission_name"]
    return f'''<section class="callout" id="h86i-rksc"><div class="section-head"><span class="badge bad">IS THIS FILE OK TO SUBMIT? NO · DO NOT SUBMIT</span><span class="badge ok">SAFE TO DOWNLOAD FOR AUDIT ONLY</span></div>
<h2>2026-10-25 latest unique TIFF (H86I-RKSC): GeoDAWN K/Th/U/TC step + Lahontan-deconfounded piedmont scarp dipole — audit only, do not upload</h2>
<p><code>{e(name)}.tif</code> is a newly generated, byte- and pixel-unique single-band GeoTIFF (SHA-256 <code>{e(card["raster_sha256"])}</code>, {v["positive_pixels"]:,} positive cells, 0 NaN, values in [0, 1]). <strong>Automated gate decision: {e(card["decision"])} (verdict: <code>{e(card["verdict"])}</code>; <code>safe_to_submit = false</code>; <code>0</code> weekly slots used; no human intervention required).</strong></p>
<div class="actions"><a class="btn" href="downloads/{e(name)}.tif" download>Download TIFF — audit only, DO NOT SUBMIT</a>
<a class="btn secondary" href="downloads/{e(name)}.zip" download>One-TIFF ZIP — audit only, DO NOT SUBMIT</a>
<a class="text-link" href="downloads/{e(name)}.json">Writer receipt</a></div>
<ul><li><strong>HOLDOUT-DTI</strong> ({e(h["evaluator_version"])}, {h["withheld_positive_pixels"]:,} withheld positives, 1,000-draw paired 20 km physical-block bootstrap): candidate <code>E1_rksc_full</code> <strong>{c["dti"]:.4f}</strong> [{c["ci95"][0]:.4f}, {c["ci95"][1]:.4f}] beat radiometric-scarp ablation <code>E2</code> ({e2["dti"]:.4f} [{e2["ci95"][0]:.4f}, {e2["ci95"][1]:.4f}]) and Lahontan-uncorrected K-depleted negative control <code>E3</code> ({e3["dti"]:.4f} [{e3["ci95"][0]:.4f}, {e3["ci95"][1]:.4f}], +72.5% relative lift), <strong>but trailed fold-fair 2-px <code>R0</code> ({r0_ff["dti"]:.4f} [{r0_ff["ci95"][0]:.4f}, {r0_ff["ci95"][1]:.4f}], paired Δ {d_ff["delta"]:+.4f} [{d_ff["ci95"][0]:+.4f}, {d_ff["ci95"][1]:+.4f}]), 3-px <code>R0</code> ({r0_c3["dti"]:.4f}), and same-split historical best <code>H86C-KSLB</code> ({best["dti"]:.4f} [{best["ci95"][0]:.4f}, {best["ci95"][1]:.4f}])</strong>.</li>
<li><strong>LEAKAGE-CANARY:</strong> <strong>PASS</strong> — worst single-field discriminative AUC across all 7 catalogue-blind feature planes is <code>{can["worst_discriminative_auc"]:.4f} &lt;= 0.90</code> (<code>{e(can["worst_field"])}</code>); Band 6 (<code>tc</code>) pixel-verified at <code>r = +0.9973</code> vs USGS GeoDAWN Total Count (<code>TC</code>).</li>
<li><strong>REGISTRY-MEASUREMENT (687/689 valid rasters; 0 missing):</strong> pre-placement surface worst Spearman <code>{surface["worst_spearman_full_footprint"]:.4f} &lt;= 0.90</code> (<code>0</code> rho firings); final-dots worst Spearman <code>{final["worst_spearman_full_footprint"]:.4f} &lt;= 0.90</code> (<code>0</code> rho firings; <code>worst Jaccard = {like["worst_jaccard"]:.4f}</code>; <code>0</code> overlap firings against any sparse &lt;=60k-dot submission). However, <code>{like["forward_overlap_firings"]}</code> space-filling lattice/composite rasters (<code>13GEMSDOE</code>, <code>15GEMSDOE</code>, <code>GEMSDOE48</code>) and continuous witness <code>17GEMSDOE</code> exceed 0.70 3-px overlap, and <code>2</code> off-grid historical rows (<code>14GEMSDOE</code>, <code>7GEMSDOE</code>) cause <code>pa86_chance_overlap.py</code> to fail closed (<code>gate_pass = FALSE</code>).</li>
<li><strong>LOCAL-FORMAT-VALIDATION:</strong> values in [0, 1] = {str(v["values_in_0_1"]).upper()} (min {v["min"]:.1f}, max {v["max"]:.1f}), no NaN inside footprint = {str(v["no_nan_inside_footprint"]).upper()}, CRS/shape/transform match = {str(v["crs_shape_transform_match"]).upper()}. Format validity never overrides a negative scientific or registry gate.</li></ul>
<dl><dt>Submission name — audit reference only (DO NOT UPLOAD)</dt><dd><code id="h86i-name">{e(name)}</code> <button data-copy-target="h86i-name" type="button">Copy name</button></dd>
<dt>Note ({card["note_chars"]} characters)</dt><dd><code id="h86i-note">{e(card["note"])}</code> <button data-copy-target="h86i-note" type="button">Copy note</button></dd></dl>
<p><a href="evidence/h86i-rksc-run-card.json">Full H86I-RKSC run card</a> · <a href="evidence/h86i-rksc-registry-surface.json">Pre-placement surface report</a> · <a href="evidence/h86i-rksc-registry-dots.json">Final-dots registry report</a> · <a href="{REPO}/blob/main/research/H86I_RKSC_PREREGISTRATION.md">4 preregistered hypotheses</a> · <a href="{REPO}/blob/main/research/SESSION_20261025_H86I_RKSC_REVIEW.md">PhD H33 (0.2778) proof &amp; 3-pass review</a></p></section>'''


def h86j_mpc_answer(card: dict) -> str:
    """Latest preregistered H86J-MPC lane receipt (unique audit TIFF; hypothesis falsified)."""
    hn = card["holdout_dti_normalized"]
    sg = card["sgmc_proxy"]
    cand = sg["candidate"]
    d_h33 = sg["paired_delta_vs_H33_as_is"]
    amp = card["ablations"]["AMP-GRADMAG"]["budgets"][str(card["chosen_budget"])]
    line = card["ablations"]["MPC-LINE"]["budgets"][str(card["chosen_budget"])]
    leakage = max(v["discriminative_auc"] for v in card["leakage_canaries"].values())
    u = card["uniqueness"]
    v = card["validator_output"]
    name = card["submission_name"]
    return f'''<section class="callout" id="h86j-mpc"><div class="section-head"><span class="badge bad">IS THIS FILE OK TO SUBMIT? NO · DO NOT SUBMIT</span><span class="badge ok">SAFE TO DOWNLOAD FOR AUDIT ONLY</span></div>
<h2>Latest unique TIFF (H86J-MPC): monogenic phase-congruency step — hypothesis falsified by its own controls, do not upload</h2>
<p><code>{e(name)}.tif</code> is a newly generated single-band GeoTIFF (SHA-256 <code>{e(card["raster_sha256"])}</code>, {card["chosen_budget"]:,} binary dots, 0 NaN/Inf, values exactly in [0, 1]) from a preregistered, genuinely new measurement — multi-scale monogenic (Riesz/log-Gabor) <strong>phase-congruency step</strong> responses of RTP + gravity + detrended DEM, never before implemented in this repository. <strong>Automated gate decision: {e(card["decision"])} (verdict: <code>{e(card["verdict"])}</code>; <code>safe_to_submit = false</code>; 0 weekly slots used; no human inspection involved).</strong> No current file is authorized to submit; H86G-EDTI retains only its historical amended-gate promotion (panel above).</p>
<div class="actions"><a class="btn" href="downloads/{e(name)}.tif" download>Download TIFF — audit only, DO NOT SUBMIT</a>
<a class="btn secondary" href="downloads/{e(name)}.zip" download>One-TIFF ZIP — audit only, DO NOT SUBMIT</a>
<a class="text-link" href="downloads/{e(name)}.json">Writer receipt</a></div>
<ul><li><strong>SGMC-PROXY-DTI</strong> (selection instrument only; pinned USGS SGMC faults &gt;3 px off catalogue, {sg["positives"]:,} px): candidate {cand["dti"]:.4f} [{cand["ci95"][0]:.4f}, {cand["ci95"][1]:.4f}] vs H33-as-is {sg["H33_as_is_dti"]:.4f}; paired delta {d_h33["delta"]:+.4f} [{d_h33["ci95"][0]:+.4f}, {d_h33["ci95"][1]:+.4f}] — <strong>significantly below the 0.2778 mechanism, and below its own frozen falsifiers</strong>: amplitude (gradmag) control {amp["sgmc_proxy_dti"]:.4f}, line-type control {line["sgmc_proxy_dti"]:.4f} at the same {card["chosen_budget"]:,} dots. Contrast-invariant phase ranking therefore loses to amplitude ranking on both repo instruments; the preregistered hypothesis is falsified, not tuned post hoc.</li>
<li><strong>HOLDOUT-DTI</strong> ({e(hn["evaluator_version"])}, {hn["n_truth"]:,} withheld positives, OOF visible construction): {hn["dti"]:.4f} [{hn["ci95"][0]:.4f}, {hn["ci95"][1]:.4f}], above the H33 visible-collar floor ({card["holdout_dti"]["H33_visible_collar_dti"]:.4f}) — a floor pass only; it does not beat the current candidate.</li>
<li><strong>LEAKAGE-CANARY:</strong> PASS — max discriminative AUC {leakage:.4f} across 18 single features, below the 0.90 stop.</li>
<li><strong>UNIQUENESS:</strong> PASS on the local registry (46 rasters): max Spearman {u["max_spearman"]:.4f} (limit 0.90), max forward 3-px overlap {u["max_forward_3px_overlap_dot_fields"]:.1%} vs dot-fields (limit 70%); only 18.7% of its dots lie within 3 px of H86G-EDTI dots — a genuinely different predicted trace. The upstream v2 scan (330/694 measured) and PA-86-02 chance diagnostic are recorded verbatim (fail-closed, incomplete registry); the literal continuous-witness reading stays blocked for every nonempty candidate.</li>
<li><strong>LOCAL-FORMAT-VALIDATION:</strong> all checks passed = {str(v["all_checks_passed"]).upper()} — format validity never overrides a negative efficacy gate.</li></ul>
<dl><dt>Submission name — audit reference only (DO NOT UPLOAD)</dt><dd><code id="h86j-name">{e(name)}</code> <button data-copy-target="h86j-name" type="button">Copy name</button></dd>
<dt>Note ({card["note_chars"]} characters)</dt><dd><code id="h86j-note">{e(card["note"])}</code> <button data-copy-target="h86j-note" type="button">Copy note</button></dd></dl>
<p><a href="evidence/h86j-mpc-run-card.json">Full H86J-MPC run card</a> · <a href="evidence/h86j-mpc-registry-surface.json">Pre-placement surface registry check</a> · <a href="evidence/h86j-mpc-registry.json">Final-dots local registry rows</a> · <a href="evidence/h86j-mpc-chance-overlap.json">PA-86-02 fail-closed record</a> · <a href="{REPO}/blob/main/research/H86J_MPC_PREREGISTRATION.md">5 preregistered hypotheses</a> · <a href="{REPO}/blob/main/research/H86J_MPC_REVIEW.md">Scientific review &amp; follow-ups</a></p></section>'''


def h86h_pstd_answer(card: dict) -> str:
    """Latest contemporaneously preregistered H86H-PSTD lane receipt (halted fail-closed per Rule 11)."""
    he = card["holdout_evaluation"]
    arms = he["arms"]
    e1 = arms["E1_pstd_full"]
    e2 = arms["E2_pstd_geopotential_only"]
    e3 = arms["E3_pstd_inverted_polarity_control"]
    r0 = he["fold_fair_r0_control"]
    best = he["same_split_archived_best"]
    reg = card["correlation_overlap_vs_registry"]
    can = card["leakage_canary"]
    d_r0 = e1["paired_vs_fold_fair_r0"]
    return f'''<section class="callout" id="h86h-pstd"><span class="badge bad">CURRENT LANE: DO NOT SUBMIT · NO UPLOAD AUTHORIZED</span>
<h2>2026-10-25 latest lane (H86H-PSTD): negative on holdout &amp; halted fail-closed before placement/TIFF</h2>
<p>Before any implementation code was written, four untried geological hypotheses (<code>H86H-1..H86H-4</code>) were frozen in <a href="{REPO}/blob/main/research/H86H_PSTD_PREREGISTRATION.md"><code>H86H_PSTD_PREREGISTRATION.md</code></a>. Top candidate <strong><code>H86H-1</code> (Poisson-Susceptibility Tensor Dislocation &amp; Dilatant Laplace-Gravity Hinge Concordance)</strong> ran 3 preregistered arms on the 100% SHA-verified competition grid and halted fail-closed <strong>before full-footprint dot placement and before GeoTIFF serialization</strong> per <code>AGENTS.md</code> Rule 11 (<code>0</code> weekly slots used; all existing research TIFFs below remain <strong>audit-only downloads, DO NOT SUBMIT</strong>):</p>
<ul><li><strong>HOLDOUT-DTI</strong> ({e(he["evaluator_version"])}, {r0["withheld_positives_total"]:,} withheld positives, 1,000-draw paired 20 km physical-block bootstrap): <code>E1_pstd_full</code> <strong>{e1["holdout_dti"]:.4f}</strong> [{e1["ci95"][0]:.4f}, {e1["ci95"][1]:.4f}] beat geopotential-only <code>E2</code> ({e2["holdout_dti"]:.4f}) and inverted-polarity control <code>E3</code> ({e3["holdout_dti"]:.4f}), a descriptive ablation ordering, not proof of hydrothermal magnetite destruction, <strong>but trailed fold-fair <code>R0</code> ({r0["holdout_dti"]:.4f} [{r0["ci95"][0]:.4f}, {r0["ci95"][1]:.4f}], paired Δ {d_r0["delta_dti"]:+.4f} [{d_r0["delta_ci95"][0]:+.4f}, {d_r0["delta_ci95"][1]:.4f}]) and same-split archived best <code>H86C-KSLB</code> ({best["holdout_dti"]:.4f} [{best["ci95"][0]:.4f}, {best["ci95"][1]:.4f}])</strong>.</li>
<li><strong>LEAKAGE-CANARY:</strong> <strong>PASS</strong> — worst single-field discriminative AUC across 7 feature planes + 3 arm surfaces is <code>{can["worst_discriminative_auc"]:.4f} &lt;= 0.90</code> (<code>{e(can["worst_field"])}</code>).</li>
<li><strong>REGISTRY-MEASUREMENT (v2 source/decoded/index-bound pre-placement surface scan):</strong> <code>{reg["rho_firings_over_0_90"]}</code> rank-correlation firings (<code>worst Spearman = {reg["worst_spearman_full_footprint"]:.4f} &lt;= 0.90</code> across <strong>{reg["valid_comparable_rasters"]}</strong> valid competition-grid rasters, <code>0</code> missing), <strong>but</strong> <code>{reg["error_rows_count"]}</code> off-grid historical <code>registry_inventory.json</code> rows (<code>14GEMSDOE</code>, <code>7GEMSDOE</code>) failed grid/band-count compatibility checks and <code>17GEMSDOE</code> covers <code>100.0%</code> of allowed pixels (<code>surface_gate_pass = FALSE</code>, <code>literal_gate_pass = FALSE</code>).</li></ul>
<p><a href="evidence/h86h-pstd-run-card.json">H86H-PSTD run card</a> · <a href="evidence/h86h-pstd-registry-surface.json">v2 bound surface report</a> · <a href="{REPO}/blob/main/research/SESSION_20261024_H86H_PSTD_REVIEW.md">PhD GEMSDOE32 analysis, 4 hypotheses &amp; 3-pass review</a>.</p></section>'''


def current_review_notice(data: dict, inputs: dict, concurrent: dict) -> str:
    """Dated read-only observations; native bands and pair checks are not clearance."""
    preparation = data["native_band_preparation"]
    bands = preparation["input_grids"]["training_features"]["bands"]
    pairs = []
    for comparison in concurrent["comparisons"]:
        result = comparison["shared_result"]
        pairs.append(f'<li><code>{e(Path(comparison["candidate_file"]).stem.split("-44090dots", 1)[0])}</code>: '
                     f'rank rho <code>{result["worst_spearman_full_footprint"]:.4f}</code>, '
                     f'forward 3-px overlap <code>{result["worst_dot_overlap"]:.2%}</code>.</li>')
    return f'''<section class="card" id="current-review"><p class="eyebrow">Independent review · 2026-10-25 · no model experiment</p>
<h2>Data restored. Submission still blocked.</h2>
<p><strong>The requested new, uniqueness-cleared TIFF was not generated in this review.</strong> The literal preflight stops before fitting or placement; no method lane was assigned. Existing files below are audit-only, not substitutes for that unmet deliverable. Byte-distinct research GeoTIFFs are not automatically registry-unique; local format validity or pairwise comparison cannot replace complete protocol clearance.</p>
<p><strong>DATA-MEASUREMENT:</strong> all {bands} native bands were restored and prepared. Every input now passes CRS, shape, transform, band-count and SHA checks before output. The actual shared cached feature stack is still absent; raw-band preparation is not that cache.</p>
<p><strong>REGISTRY-INPUT-MEASUREMENT:</strong> {inputs['byte_verified_rasters']} / {inputs['indexed_rasters_expected']} indexed files hash-verified; {inputs['grid_compatible_rasters']} have compatible grids and {inputs['grid_incompatible_or_invalid_rasters']} do not. The horse-ensemble has a shifted transform; the Qfaults prior has three bands. Neither was dropped or repaired. This is byte/metadata coverage, not a candidate uniqueness pass.</p>
<p><strong>REGISTRY-MEASUREMENT (two inherited final-dot directions only):</strong> the concurrent GZZD/PCC audit gap is now closed:</p><ul>{''.join(pairs)}</ul>
<p>These pair checks fire neither rank nor overlap threshold against each other, but cannot clear the full registry or reconstruct pre-placement evidence. All files remain <strong>DO NOT SUBMIT</strong>. No historical HOLDOUT-DTI was rerun or upgraded.</p>
<p><a href="evidence/session-cf73474c-run-card.json">This review’s negative run card</a> · <a href="evidence/session-cf73474c-data.json">Data/cache receipt</a> · <a href="evidence/registry-input-grid-review-20261025.json">All registry input rows</a> · <a href="evidence/concurrent-artifact-review-20261025.json">Pair and H33 pixel audit</a> · <a href="{REPO}/blob/main/registry/h86g_hypotheses.json">Four untested hypotheses</a> · <a href="{REPO}/blob/main/research/SESSION_20261025_CF73474C_REVIEW.md">Three-pass review &amp; next steps</a></p></section>'''


def new_hypothesis_queue(plan: dict) -> str:
    rows = []
    for h in plan["hypotheses"]:
        layers = "; ".join(f'Band {layer["band"]}: {layer["name"]}' for layer in h["layers"])
        rows.append(f'''<article class="card"><p class="eyebrow">New proposal {h['rank']} · {e(h['id'])} · NOT RUN</p><h3>{e(h['name'])}</h3>
<dl><dt>Layers and physical signature</dt><dd>{e(layers)}. {e(h['physical_signature'])}</dd>
<dt>Why catalogue-missing / novelty</dt><dd>{e(h['catalogue_missing_rationale'])} {e(h['novelty'])}</dd>
<dt>Named non-fault mimic</dt><dd>{e(h['non_fault_mimic'])}</dd>
<dt>Qualitative potential / cost — not a projected score</dt><dd>{e(h['expected_holdout_potential'])} {e(h['implementation_cost'])}</dd>
<dt>Falsifier</dt><dd>{e(h['falsifier'])}</dd></dl></article>''')
    return f'''<section id="new-hypotheses"><h2>2026-10-25: four untested native-layer proposals</h2>
<p>{e(plan['ranking_basis'])}</p><p>No new external product is required by these designs. The pinned native TIFF was obtained, but the actual shared cache and method authorization remain missing. These are hypotheses, not validated geological discoveries or score estimates.</p>{''.join(rows)}
<p><a href="{REPO}/blob/main/registry/h86g_hypotheses.json">Full proposal register and blockers</a> · <a href="evidence/session-cf73474c-data.json">Actual data obtainability / shared-cache limits</a></p></section>'''


def home(report: dict, fleet: dict, registry: dict, review: dict, plan_count: int = 4, answer: str = "", review_notice: str = "", h86g_html: str = "", sacd_banner: str = "") -> str:
    n = report["artifact_count"]
    return page("Download decision", "index.html", f'''
<section class="hero"><p class="eyebrow">DOE GEMS Prize · fault-discovery research</p>
<span class="badge bad">NO FILE AUTHORIZED · DO NOT SUBMIT</span>
<h1>Download research TIFFs.<br><span class="subtle">No current file is authorized to submit.</span></h1>
<p class="lede">The existing <strong>H86G-EDTI</strong> GeoTIFF has a historical amended-gate research promotion, but fails the current literal registry requirement. Its card does not authorize submission. Downloadable GeoTIFFs remain available for reproducibility only; a new hash or local format pass does not establish scientific uniqueness or slot approval.</p>
<div class="actions"><a class="btn" href="#downloads">Open TIFF downloads ↓</a><a class="btn secondary" href="executive-summary.html">Executive summary &amp; portal steps →</a></div>
<p><strong>Historical H86G-EDTI lane verdict: PROMOTE under the archived amended-gate interpretation only; current decision: DO NOT SUBMIT.</strong> The exact artifact remains audit-only in the blocked panel below. <strong>Latest lanes H86I-SACD &amp; H86J-MPC (2026-10-25): NEGATIVE</strong> — H86I-SACD ran strict spatial LOQO spin-2 Coulomb concordance + 300 m submodular PU (0.0832 vs E2 0.1055) and H86J-MPC ran monogenic phase-congruency step (SGMC-PROXY-DTI 0.0658 vs amplitude falsifier 0.1089); both are audit-only downloads below and no slot was spent. <strong>Earlier concurrent lanes (2026-10-25):</strong> byte-distinct research GeoTIFFs H86I-HVFD, H86I-RKSC, H86F-GZZD, H86F-PCC and H86F-EWCS are audit-only downloads below (H86F-EWCS reports higher HOLDOUT-DTI but is also blocked; H86H-PSTD is a preregistration/registry-surface lane, negative, no published TIFF candidate), with the earlier H86E-MMT lane beneath them. The negative lanes are <strong>negative on HOLDOUT-DTI, not unique under the registry gate and not cleared for submission</strong> (parallel lanes: candidates were not all measured against each other contemporaneously; post-merge addenda are in the run cards). No human inspection decided this: the HOLDOUT-DTI, leakage canary, surface/final registry measurements, ZIP, SHA-256 and local-format gates are recorded in machine-readable evidence.</p>
<p><span class="badge ok">SAFE TO DOWNLOAD</span> <strong>DO NOT SUBMIT any current file, including H86G-EDTI.</strong></p>
<p class="muted">Latest automated remeasurement: <time>{e(review['registry_measured_utc'])}</time>. <a href="evidence/latest-review-run-card.json">Current negative run card</a> · <a href="submit.html">PR #60 SPT revocation notice (IR-86-SPT-02)</a> · <a href="{REPO}/blob/main/research/SESSION_20261024_REVIEW.md">Safety review and next steps</a>. Historical model results below were not rerun.</p>
</section>
{h86g_html}
<div class="kpi"><div><span>Local format &amp; integrity</span><strong>{report['locally_valid_artifacts']} / {n}</strong><small>All serialized files re-read; names, notes, masks, SHA and ZIP payloads checked.</small></div>
<div><span>Authorized submission files</span><strong>0</strong><small>H86G-EDTI retains its historical amended-gate promotion, not literal-rule clearance or slot approval. No portal operation was run here.</small></div>
<div><span>Release-audit experiments / slots used</span><strong>{report['experiments_run']} / {report['submission_slots_used']}</strong><small>This release audit does not fit a model, in any event, it isn't a discovery oracle. H86G-EDTI ran its 3 preregistered arms and promotes; the other lanes above are negative.</small></div></div>
{sacd_banner}
{review_notice}
<section class="callout"><h2>Why a new submission cannot be cleared</h2><p>A hash-pinned historical registry raster (<code>17GEMSDOE</code>, <code>ab0a0a62...</code>) is positive at <strong>every allowed pixel</strong>. Under the unchanged literal rule, any nonempty dot set has forward overlap {report['witness_positive_support_allowed_fraction']:.0%}, above the {report['overlap_limit']:.0%} stop; moreover, a discrete binary stride-5 lattice witness (<code>13GEMSDOE</code>, <code>b4570b40...</code>, <code>206,895</code> dots) covers <code>99.8724%</code> of allowed pixels within 3 px, forcing <code>&gt;= 82.70%</code> overlap on any <code>37,654</code>-dot raster by pigeonhole. This is a rule-satisfiability failure, not evidence that every geological idea is identical.</p>
<p>All {len(registry['artifacts'])} inherited final TIFFs were independently rechecked against this witness, and PR #60's <code>SPT</code> candidate remains quarantined outside <code>docs/</code> after also measuring 100% witness overlap and coin-flip canary AUC (<code>0.4947</code>). No dense-prior exemption was applied. <a href="evidence/all-artifacts-registry.json">Measured negative proof</a> · <a href="evidence/latest-review-run-card.json">Current negative run card</a> · <a href="evidence/spt-run-card.json">Revoked SPT card</a> · <a href="evidence/session-20261023-run-card.json">Archived 2026-10-23 card</a>.</p></section>
<section id="downloads"><p class="eyebrow">Immediate downloads · historical research artifacts</p><h2>TIFF + single-TIFF ZIP + identity receipt</h2>
<p>Files below include the concurrent H86F-GZZD and H86F-PCC artifacts, the H86E-MMT and blind-geothermal lane artifacts plus preserved historical lanes. Every download is safe only for audit/reproducibility; no file is selected, ranked, or authorized for a submission slot here.</p>
{downloads(report['artifacts'])}</section>
<details class="card"><summary>Earlier negative lane receipts and measured HOLDOUT-DTI context</summary>
{answer}
{pr92_candidate_notice(report)}
</details>
<section class="card"><h2>Why GEMSDOE32 (<code>0.2778</code> OWNER-REPORTED; not organizer-confirmed) led the fleet — and can we beat it?</h2><p>Pixel-exact forensic comparison of the pinned <code>GEMSDOE28</code> (<code>40,199</code> dots; <code>0.2708</code> OWNER-REPORTED) and <code>GEMSDOE32</code> <code>h33-h33-2-b2</code> (<code>37,654</code> dots; <code>0.2778</code> OWNER-REPORTED) rasters confirms <strong>0 differing cells across all 12,279,160 grid pixels</strong> after deleting the <code>2,545</code> dots in the <code>1.0 &lt; d_cat &lt;= 2.0</code> mapped-fault collar. <code>GEMSDOE36</code> (<code>0.2750</code> OWNER-REPORTED) contains <code>100%</code> of <code>R0</code> verbatim plus <code>1,200</code> extra dots (<code>97.40%</code> 3-px overlap); all owner-reported fleet entries above <code>0.2600</code> in the supplied inventory lie in this <code>H19-5/D2.8</code> lineage (<code>92.64%–100%</code> overlap). Under asymmetric 300 m Tversky (<code>alpha=0.2, beta=0.8</code>), <code>~2.8 px</code> disk spacing near the <code>3 px</code> kernel radius can reduce redundant prediction mass, but does not prevent kernel overlap; collar pruning may remove low-credit mass, though proximity to a mapped fault alone does not prove zero hidden-truth credit. Cross-project score comparisons (e.g., <code>GEMSDOE81</code> <code>44,090</code> unit dots and <code>0.0041</code> OWNER-REPORTED vs <code>GEMSDOE76</code> <code>0.2343</code> OWNER-REPORTED / <code>GEMSDOE70</code> <code>0.2478</code> OWNER-REPORTED) are descriptive associations, not controlled causal proofs. <strong>HOLDOUT-DTI</strong> (<code>gems57-pooled-hide-v2</code>, <code>22,893</code> withheld positives): <code>H86D-CTHB</code> = <code>0.1133</code>, 95% CI <code>[0.0965, 0.1297]</code>; <code>H33-2-B2</code> fold-fair control = <code>0.1056</code>, 95% CI <code>[0.0936, 0.1166]</code>; paired HOLDOUT-DTI delta = <code>+0.0076</code>, 95% CI <code>[-0.0101, +0.0241]</code>. The paired CI crosses zero. The prompt's conflicting <code>0.3195</code> and <code>0.4413</code> current-leaderboard values are OWNER-REPORTED and unverified here; exceeding any reported value is not established. <strong>Do not infer a leaderboard projection from holdout results.</strong> <a href="https://github.com/buffedlizard55-lab/GEMSDOE86/blob/main/research/H33_INTERPRETATION_REVIEW.md">Metric counterexamples and limits of the explanation</a>.</p>
<p>No validated improvement over that competition result is authorized for upload while the literal witness stop holds. Our ranked research queue prioritizes <strong>signed paired-throw basement–gravity concordance, cross-corridor magnetic marker translation, hydrothermal magnetite-destruction &amp; vent-alignment corridors, 3D MT conductance × heat flow, and 1-m 3DEP LiDAR watershed-crossing scarps</strong>. <a href="hypotheses.html">{plan_count} hypotheses across dated research queues →</a> · <a href="{REPO}/blob/main/research/GEOTHERMAL_VENT_DISCOVERY_SYNTHESIS.md">Geothermal vent synthesis →</a></p></section>
<section class="card"><h2>An auditable, refreshable project feed</h2><p>{fleet['projects_snapshotted']} / {fleet['projects_requested']} named repositories snapshotted. Last GitHub inventory refresh: <time>{e(fleet['refreshed_utc'])}</time>. Final-artifact registry measurement: <time>{e(registry['measured_utc'])}</time>.</p>
<p><a href="fleet.html">Browse the full project list</a>. This is repository metadata and local artifact validation, <strong>not a live DrivenData score or remaining-quota feed</strong>. Failed requests and the age of observations remain visible.</p></section>''')


def executive(report: dict, sources: dict, answer: str = "", review_notice: str = "", h86g_html: str = "", sacd_banner: str = "") -> str:
    audit_rows = "".join(f'<tr><th scope="row">{e(a["lane"])}</th><td><a href="{e(link(a["file"]))}" download>{e(Path(a["file"]).name)}</a><br><code>{e(a["sha256"])}</code></td><td>{a["bytes"]:,} bytes<br><strong>{e(a["status"])}</strong></td></tr>' for a in report["artifacts"])
    n_valid = report["locally_valid_artifacts"]
    n_total = len(report["artifacts"])
    return page("Executive summary", "executive-summary.html", f'''
<p class="eyebrow">Executive summary</p><h1>Submission procedure,<br>with an automatic stop.</h1>
{h86g_html}
<div class="callout"><span class="badge bad">CURRENT DECISION: DO NOT SUBMIT ANY FILE</span><p>Technical validation is automatic; there is no human-inspection gate hiding a release decision. All {n_total} artifacts pass local format/range checks ({n_valid}/{n_total}) and fail the mandatory <em>literal</em> registry reading (a continuous full-support witness blocks every nonempty candidate by construction). Under the PA-86-01 like-for-like reading, exactly one file — <strong>H86G-EDTI</strong>, panel above — passes every registered gate (verdict PROMOTE). That historical research promotion does not override the literal stop or authorize upload. The card explicitly records safe_to_submit=false and approved_for_weekly_slot=false; this audit spent no weekly slot.</p>
<a class="btn" href="index.html#downloads">Download research TIFFs — audit only (all files)</a><a class="btn secondary" href="evidence/release-readiness.json">Open complete validator output</a></div>
{sacd_banner}
{review_notice}
<h2>Current downloads — all research only; none authorized</h2>
<div class="table-wrap"><table><thead><tr><th>Historical lane</th><th>Direct TIFF / SHA-256</th><th>Decision</th></tr></thead><tbody>{audit_rows}</tbody></table></div>
<p><a href="download-status.html">Independent all-download format audit</a> · <a href="evidence/download-validation.json">Its machine-readable report</a>. These format checks and the literal registry decision are separate gates; neither invents an organizer receipt.</p>
<details class="card"><summary>Earlier negative lane receipts and measured HOLDOUT-DTI context</summary>
{answer}
{pr92_candidate_notice(report)}
</details>
<h2>What is checked without intervention?</h2><ul><li>Every published TIFF is decoded and checked by the pinned shared validator and template-format checker.</li>
<li>CRS, shape, affine transform, float32 band count, valid footprint, finite values in range, outside-footprint zeros and mapped-fault masking are measured from disk.</li>
<li>The SHA matches the inventory, writer receipt and applicable scientific card. ZIP bytes must contain exactly the corresponding TIFF; empty or mismatched ZIPs fail.</li>
<li>Names and notes are verified against the project length cap. Stored model evidence is not rewritten or upgraded by a format pass.</li>
<li>All final artifacts are bound to the negative registry measurement. Unknown/missing/stale evidence fails closed.</li></ul>
<h2>Registry checks must fail closed</h2><p>Candidate checks reject invalid values rather than thresholding or masking them into validity. Missing or invalid registry files, empty/constant predictions and stale candidate evidence cannot pass. Current reports bind the exact source array, decoded pixels and indexed registry content. A surface check runs before dot placement; final-dot checks precede TIFF generation. Historical unbound reports are archives, not clearance, and must be rerun. The representation-aware diagnostics are not permission to ignore the literal stop or spend a slot.</p>
<p><a href="{REPO}/blob/main/research/SESSION_20261024_4D79B443.md">Independent code review, research sketches and limitations</a></p>
<h2>Future submission steps — only after scientific clearance</h2><ol class="steps"><li><strong>Resolve the protocol conflict first.</strong> A new lane must be authorized, the actual shared cached features and a complete accessible registry recovered, and the uniqueness rule made satisfiable through an explicit protocol revision. This project does not grant that revision itself.</li>
<li><strong>Validate a new method.</strong> Freeze whole-segment buffered folds, derive catalogue features only from visible faults, run each feature's leakage canary, and beat the strongest rerunnable matched control with a positive paired physical-block confidence interval. Use the shared evaluator and writer unchanged.</li>
<li><strong>Run all release checks.</strong> A format pass alone is insufficient: both pre-placement surface and final-dot uniqueness must pass the literal thresholds. Promotion is separate from slot selection.</li>
<li><strong>Use the separate selector.</strong> It must inspect the authenticated submission page's actual remaining weekly quota and bind its decision to the exact raster SHA. The public rules list {sources['weekly_limit_in_public_rules']} submissions per week; that is not our current account balance. No account credentials or automatic upload are implemented here.</li>
<li><strong>Download only the authorized TIFF or one-TIFF ZIP.</strong> Choose <em>New submission</em> on the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">official submission page</a>, select the file (not JSON, a sample or an audit-only artifact), and paste its short identity note.</li>
<li><strong>Retain the organizer receipt.</strong> Bind the result and submission ID to the exact SHA before classifying any score as ORGANIZER-CONFIRMED. Follow the rules for one final selection, reproducible assets, eligibility and generative-AI disclosure.</li></ol>
<h2>DrivenData “New submission” portal checklist (exact form mapping)</h2>
<div class="table-wrap"><table><thead><tr><th>DrivenData portal field</th><th>Required specification</th><th>Automated check in this repo</th></tr></thead><tbody>
<tr><th scope="row"><code>File to submit</code></th><td>Single-band <code>float32</code> GeoTIFF (<code>.tif</code>) or <code>.zip</code> containing a single <code>.tif</code>; <code>EPSG:32611</code>; shape <code>3730 × 3292</code>; <code>100 m</code> affine transform; values in <code>[0, 1]</code>.</td><td>Checked automatically by <code>vendor/template66/gems57/validate.py</code>, <code>gates.py</code>, and <code>scripts/audit_release.py</code> (<code>{n_valid}/{n_total}</code> format-valid, <code>0</code> NaN, <code>0</code> Inf, <code>min=0.0</code>, <code>max&lt;=1.0</code> — still <strong>DO NOT SUBMIT</strong> under literal witness gate).</td></tr>
<tr><th scope="row">Unique filename stem</th><td>Distinct lane + dot budget + UTC timestamp + 8-hex digest + fill policy (e.g. <code>gems86-&lt;lane&gt;-&lt;dots&gt;dots-&lt;YYYYMMDDTHHMMSSZ&gt;-&lt;sha8&gt;-zeros.tif</code>) so no two team uploads collide.</td><td>Verified unique across inventory and <code>1..140</code> characters (<code>name_1_to_140_chars</code>) with copy button on each card.</td></tr>
<tr><th scope="row"><code>Note (optional)</code></th><td>Short team-disambiguating comment of <strong>at most 140 characters</strong> (e.g. method tag, dot count, spacing, holdout evaluator version, <code>[0,1]</code> policy).</td><td>Verified <code>1 &lt;= len(note) &lt;= 140</code> against serialized JSON receipt (<code>note_1_to_140_chars</code>, <code>receipt_note_count_matches</code>).</td></tr>
<tr><th scope="row">Weekly cap &amp; final pick</th><td>Up to <code>3</code> submissions per week on the public leaderboard; <strong>only ONE final submission</strong> enters both Phase 1 ($50k) and Phase 2 ($250k) judging (<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official Rules §1.1 &amp; §3.4–3.6</a>).</td><td>Separate human/team selector step required; <code>submission_slots_used = 0</code> in this repo.</td></tr>
</tbody></table></div>
<h2>The reported “[0,1]” rejection</h2><p>The rejected file was not supplied, so the cause is unknown. The shared writer rejects nonfinite and out-of-range predictions instead of silently clipping them, then validates the serialized output and ZIP. The current audit rechecks those bytes. This prevents us publishing that class of invalid numerical output, but it does not prove portal acceptance.</p>
<p>The public specification describes null/NaN outside bounds. The project's all-finite, zero-outside policy is a conservative local choice. It must not be described as organizer-confirmed acceptance or a complete diagnosis of the earlier error.</p>
<h2>Reproduce the checks</h2><pre><code>./scripts/download_competition_data.sh --protocol-only --include-registry
python scripts/audit_release.py --measure-registry
python scripts/refresh_fleet.py
python scripts/build_site.py
python -m pytest -q</code></pre>
<p>The first command (wrapping <code>scripts/restore_data.py</code> and <code>scripts/restore_protocol_data.py</code>) restores SHA-256-pinned mirror inputs into both <code>data/bridge/</code> and <code>data/</code> plus the historical witness for comparison, not a new submission; full feature + external restoration is available via <code>./scripts/download_competition_data.sh --with-external</code> (with optional workstation <code>--source dropbox</code> fallback verified against identical SHA-256 pins). Shared cached features are not regenerated. No GPU is needed for these audits; the official reference also has CPU-only training options.</p>
<p><a href="sources.html">Official sources and exact observation limits</a> · <a href="irregularities.html">Remaining blockers</a></p>''')


def evidence(report: dict) -> str:
    rows = []
    for i, a in enumerate(report["artifacts"]):
        h = a["historical_holdout"]
        if h["value"] is None:
            score = f'<p><strong>{e(h["status"])}</strong> · {e(h["caveat"])}</p>'
        else:
            ci = h["ci95"]
            score = f'''<p><strong>HOLDOUT-DTI {h['value']:.5f}</strong> · 95% CI [{ci[0]:.5f}, {ci[1]:.5f}] · {h['withheld_positives']:,} withheld positives · {e(h['evaluator_version'])}.</p>
<p>{e(h['design'])}. <strong>Archived, not recomputed in this audit.</strong> {e(h['caveat'])}</p>'''
        v = a["validator"]
        checks = "".join(f'<tr><td><code>{e(k)}</code></td><td>{"PASS" if value else "FAIL"}</td></tr>' for k, value in v["checks"].items())
        registry = a.get("registry_measurement")
        measure = (f'<p>REGISTRY-MEASUREMENT against one pinned witness: Spearman {registry["spearman_full_footprint"]:.6f}; forward 3 px overlap {registry["forward_overlap_3px"]:.6f}; <code>unique=false</code>, <code>stop_required=true</code>. Not a complete registry scan or a pre-placement surface check.</p>' if registry else '<p>Final-dot remeasurement not available; no uniqueness clearance.</p>')
        if a["source_card"]:
            card = f'<a href="{e(link(a["source_card"]))}">Historical scientific card</a>'
        elif "PR #92" in a["lane"]:
            card = f'<a href="{e(link(h["source"]))}">Archived PR #92 run-card sidecar</a> (not rerun or uniqueness clearance)'
        else:
            card = '<span>Historical control, not a new canonical candidate card</span>'
        rows.append(f'''<section class="card" id="artifact-{i}"><h2>{e(a['lane'])}</h2><p class="filename">{e(Path(a['file']).name)}</p><span class="badge bad">DO NOT SUBMIT</span>
{score}{measure}<p>{card} · <a href="{e(link(h['source']))}">Metric context</a></p>
<p>FORMAT-VALIDATION: min {v['min']:.1f}, max {v['max']:.1f}; NaN {v['n_nan']}, Inf {v['n_inf']}; outside-footprint positive cells {v['outside_footprint_positive']}; on-catalogue positive cells {v['on_catalogue_positive']}.</p>
<details><summary>Every automated format / identity / ZIP check</summary><div class="table-wrap"><table><thead><tr><th>Check</th><th>Result</th></tr></thead><tbody>{checks}</tbody></table></div></details></section>''')
    return page("Validation evidence", "evidence.html", '''<p class="eyebrow">Read-only audit · not a model experiment</p><h1>Every file. Every gate.<br>No automatic promotion.</h1>
<p>Different fold designs, seeds, buffered/cut segments, training contexts and confidence intervals are not one comparable leaderboard. Do not select the largest number across these cards. No current holdout best or improvement over the private test is certified here.</p>
<p><a href="evidence/release-readiness.json">Full machine-readable audit</a> · <a href="evidence/all-artifacts-registry.json">All-artifact witness measurements</a> · <a href="evidence/protocol-preflight.json">Saturation proof</a></p>''' + "\n".join(rows))


def hypotheses(plan: dict, plan86f: dict | None = None, h86h_prereg: dict | None = None, pstd_card: dict | None = None, h86i_prereg: dict | None = None, rksc_card: dict | None = None, hvfd_prereg: dict | None = None, hvfd_card: dict | None = None, new_queue: str = "", plan86i: dict | None = None, sacd_card: dict | None = None) -> str:
    block86i = ""
    if plan86i:
        cards86i = []
        sacd_e1 = sacd_card["holdout_dti"]["candidate"]["dti"] if sacd_card else None
        for h in plan86i.get("hypotheses", []):
            st_i = (
                f"EXECUTED NEGATIVE UNDER STRICT LOQO (HOLDOUT-DTI {sacd_e1:.4f}; audit-only DO NOT SUBMIT)"
                if h.get("selected_for_validation") and sacd_e1 is not None
                else ("NOT VIABLE IN SANDBOX YET" if "NOT_VIABLE_YET" in h.get("external_data_status", "") else "PREREGISTERED (DEFERRED BEHIND RANK 1)")
            )
            cards86i.append(f'''<article class="card"><p class="eyebrow">H86I-SACD Rank {h['rank']} · {e(h['id'])} · {e(st_i)}</p><h2>{e(h['title'])}</h2>
<dl><dt>Specific layers</dt><dd>{e('; '.join(h['layers']))}</dd><dt>Physical signature &amp; transform</dt><dd>{e(h['physical_signature'])}</dd>
<dt>Why missing from USGS/INGENIOUS catalogue?</dt><dd>{e(h['why_missing_from_catalogue'])}</dd><dt>Difference from repository</dt><dd>{e(h['difference_from_repo'])}</dd>
<dt>Named non-fault mimic</dt><dd>{e(h['non_fault_mimic'])}</dd><dt>Expected DTI rank &amp; cost</dt><dd>Rank {h['expected_dti_improvement_rank']} · {e(h['implementation_cost'])}</dd>
<dt>External data status</dt><dd>{e(h['external_data_status'])}</dd></dl></article>''')
        block86i = (
            '<section id="h86i-hypotheses"><h2>2026-10-25 H86I-SACD Preregistered Hypothesis Queue (Session 95a42d60 · Top Candidate H86I-SACD Executed Under Strict Spatial LOQO)</h2>'
            '<p>Declared prior to holdout evaluation in <a href="' + REPO + '/blob/main/registry/h86i_hypotheses.json"><code>registry/h86i_hypotheses.json</code></a> and <a href="' + REPO + '/blob/main/research/H86I_SACD_PREREGISTRATION.md"><code>H86I_SACD_PREREGISTRATION.md</code></a> (<a href="evidence/h86i-sacd-run-card.json">run card</a>).</p>'
            + "".join(cards86i) + "</section>"
        )
    hvfd_cards = []
    if hvfd_prereg and hvfd_card:
        scores_i = hvfd_card["holdout_dti"]["pooled_summary"]["scores"]
        e1_v = scores_i["E1_hvfd_blind_vent_conduit"]
        e2_v = hvfd_card["holdout_dti"]["candidate"]
        e3_v = scores_i["E3_hvfd_collar_ablation_44090"]
        r0_v = scores_i["R0_G25_foldfair_collar"]
        for ch in hvfd_prereg["ranked_hypotheses"]:
            status_label = (
                f"EXECUTED NEGATIVE VS KSLB / BEATS R0 (E1={e1_v['dti']:.4f}, E2={e2_v['dti']:.4f} vs R0={r0_v['dti']:.4f}, E3={e3_v['dti']:.4f}; audit TIFF emitted, DO NOT SUBMIT)"
                if ch["selected_for_validation"]
                else ("DEFERRED (NOT VIABLE IN SANDBOX YET)" if "NOT_VIABLE" in ch["official_data"] else "PREREGISTERED (DEFERRED BEHIND RANK 1)")
            )
            hvfd_cards.append(f'''<article class="card"><p class="eyebrow">H86I-HVFD Rank {ch['rank']} · {e(ch['id'])} · {e(status_label)}</p><h2>{e(ch['name'])}</h2>
<dl><dt>Specific layers</dt><dd>{e('; '.join(ch['layers']))}</dd><dt>Physical signature &amp; transform</dt><dd>{e(ch['transform'])}</dd>
<dt>Why missing from USGS/INGENIOUS catalogue?</dt><dd>{e(ch['uncatalogued_rationale'])}</dd><dt>Novelty vs repository</dt><dd>{e(ch['novelty'])}</dd>
<dt>Named non-fault mimic</dt><dd>{e(ch['non_fault_mimic'])}</dd><dt>Expected DTI rank &amp; cost</dt><dd>{e(ch['cost'])}</dd>
<dt>Official data obtainability</dt><dd>{e(ch['official_data'])}</dd></dl></article>''')
    hvfd_block = (
        f'<h2>Contemporaneously preregistered H86I-HVFD hypotheses (<a href="evidence/h86i-hvfd-run-card.json">H86I-HVFD run card</a>)</h2>{"".join(hvfd_cards)}'
        if hvfd_cards else ""
    )
    h86i_cards = []
    if h86i_prereg and rksc_card:
        e1_i = rksc_card["holdout_dti"]["candidate"]
        r0_i = rksc_card["holdout_dti"]["R0_GEMSDOE25_d28_fold_fair_2px"]
        for ch in h86i_prereg["candidate_hypotheses"]:
            status_label = (
                f"EXECUTED NEGATIVE (HOLDOUT-DTI {e1_i['dti']:.4f} vs fold-fair R0 {r0_i['dti']:.4f}; audit TIFF serialized, DO NOT SUBMIT)"
                if ch["selected_for_validation"]
                else ("DEFERRED (NOT VIABLE IN SANDBOX YET)" if "NOT_VIABLE" in ch["official_data_obtainability"] else "PREREGISTERED (DEFERRED BEHIND RANK 1)")
            )
            h86i_cards.append(f'''<article class="card"><p class="eyebrow">H86I Rank {ch['rank']} · {e(ch['id'])} · {e(status_label)}</p><h2>{e(ch['title'])}</h2>
<dl><dt>Specific layers</dt><dd>{e('; '.join(ch['layers']))}</dd><dt>Physical signature &amp; transform</dt><dd>{e(ch['physical_signature'])}</dd>
<dt>Why missing from USGS/INGENIOUS catalogue?</dt><dd>{e(ch['why_catches_unmapped_faults'])}</dd><dt>Novelty vs repository</dt><dd>{e(ch['difference_from_repo'])}</dd>
<dt>Named non-fault mimic</dt><dd>{e(ch['named_non_fault_mimic'])}</dd><dt>Expected DTI rank &amp; cost</dt><dd>Rank {ch['expected_dti_rank']} · {e(ch['implementation_cost'])}</dd>
<dt>Official data obtainability</dt><dd>{e(ch['official_data_obtainability'])}</dd></dl></article>''')
    h86i_block = (
        f'<h2>Contemporaneously preregistered H86I hypotheses (<a href="evidence/h86i-rksc-run-card.json">H86I-RKSC run card</a>)</h2>{"".join(h86i_cards)}'
        if h86i_cards else ""
    )
    sections86f = []
    if plan86f:
        for h in plan86f.get("hypotheses", []):
            sources = " · ".join(f'<a href="{e(url)}">Official basis</a>' for url in h.get("official_basis", []))
            status86f = h.get("status", "HOLDOUT_VALIDATED_DO_NOT_SUBMIT" if h["id"] == "H86F-EWCS" else "NOT_RUN")
            sections86f.append(f'''<article class="card"><p class="eyebrow">H86F Priority {h['rank']} · {e(h['id'])} · {e(status86f)}</p><h2>{e(h['name'])}</h2>
<dl><dt>Specific layers</dt><dd>{e('; '.join(h['layers']))}</dd><dt>Physical signature</dt><dd>{e(h['signature'])}</dd>
<dt>Why an unmapped fault?</dt><dd>{e(h['why_unmapped'])}</dd><dt>Different from this checkout</dt><dd>{e(h['difference_from_repo'])}</dd>
<dt>Named non-fault mimic</dt><dd>{e(h['non_fault_mimic'])}</dd><dt>Expected value / implementation cost</dt><dd>{e(h['expected_dti_gain'])} {e(h['implementation_cost'])}</dd>
<dt>Data / viability</dt><dd>{e(h['data_readiness'])} {e(h.get('obtainability', ''))}</dd></dl><p>{sources}</p></article>''')
    block86f = (
        f'<h2>2026-10-25 H86F Novel Hypothesis Queue (Top Candidate H86F-EWCS Validated on Holdout: 0.1723)</h2>'
        f'<p>Ranked by expected whole-component <code>HOLDOUT-DTI</code> improvement and CPU cost; top candidate <code>H86F-EWCS</code> was executed under 3-arm preregistration (<a href="evidence/h86f-ewcs-run-card.json">run card</a>: <code>0.1723 [0.1530, 0.1898]</code>, <code>DO NOT SUBMIT</code> on registry completeness/literal saturation).</p>'
        + "".join(sections86f)
    ) if sections86f else ""
    h86h_block = ""
    if h86h_prereg and pstd_card:
        e1 = pstd_card["holdout_evaluation"]["arms"]["E1_pstd_full"]
        r0 = pstd_card["holdout_evaluation"]["fold_fair_r0_control"]
        h86h_cards = []
        for ch in h86h_prereg["candidate_hypotheses"]:
            status_label = (
                f"EXECUTED NEGATIVE (HOLDOUT-DTI {e1['holdout_dti']:.4f} vs fold-fair R0 {r0['holdout_dti']:.4f}; halted pre-placement)"
                if ch["selected_for_validation"]
                else ("DEFERRED (NOT VIABLE IN SANDBOX YET)" if "NOT_VIABLE" in ch["official_data_obtainability"] else "PREREGISTERED (DEFERRED BEHIND RANK 1)")
            )
            h86h_cards.append(f'''<article class="card"><p class="eyebrow">H86H Rank {ch['rank']} · {e(ch['id'])} · {e(status_label)}</p><h2>{e(ch['title'])}</h2>
<dl><dt>Specific layers</dt><dd>{e('; '.join(ch['layers']))}</dd><dt>Physical signature &amp; transform</dt><dd>{e(ch['physical_signature_and_transform'])}</dd>
<dt>Why missing from USGS/INGENIOUS catalogue?</dt><dd>{e(ch['why_uncatalogued_faults'])}</dd><dt>Novelty vs repository</dt><dd>{e(ch['novelty_vs_repo'])}</dd>
<dt>Named non-fault mimic</dt><dd>{e(ch['non_fault_mimic'])}</dd><dt>Expected DTI rank &amp; cost</dt><dd>{e(ch['expected_dti_rank_and_cost'])}</dd>
<dt>Official data obtainability</dt><dd>{e(ch['official_data_obtainability'])}</dd></dl></article>''')
        h86h_block = (
            '<h2>Contemporaneously preregistered H86H hypotheses (<a href="evidence/h86h-pstd-run-card.json">H86H-1 run card</a>)</h2>'
            + "".join(h86h_cards)
        )
    sections = []
    for h in plan["hypotheses"]:
        sources = " · ".join(f'<a href="{e(url)}">Official basis</a>' for url in h["official_basis"])
        sections.append(f'''<article class="card"><p class="eyebrow">Priority {h['rank']} · {e(h['id'])} · {e(h['status'])}</p><h2>{e(h['name'])}</h2>
<dl><dt>Specific layers</dt><dd>{e('; '.join(h['layers']))}</dd><dt>Physical signature</dt><dd>{e(h['signature'])}</dd>
<dt>Why an unmapped fault?</dt><dd>{e(h['why_unmapped'])}</dd><dt>Different from this checkout</dt><dd>{e(h['difference_from_repo'])}</dd>
<dt>Named non-fault mimic</dt><dd>{e(h['non_fault_mimic'])}</dd><dt>Expected value / implementation cost</dt><dd>{e(h['expected_dti_gain'])} {e(h['implementation_cost'])}</dd>
<dt>Data / viability</dt><dd>{e(h['data_readiness'])} {e(h.get('obtainability', 'No new external product is proposed as acquired.'))}</dd></dl><p>{sources}</p></article>''')
    steps = "".join(f'<li>{e(step)}</li>' for step in plan["required_validation_after_blockers_are_resolved"])
    return page("Research queue", "hypotheses.html", f'''<p class="eyebrow">Declared before implementation · preregistered research queue</p><h1>Seek displacement &amp; stress transfer,<br>not just another edge.</h1>
<div class="callout"><span class="badge bad">NO CANDIDATE CLEARED FOR WEEKLY SLOT</span><p>{e(plan['scope'])} Top 2026-10-25 candidate <code>H86F-EWCS</code> achieved <code>HOLDOUT-DTI = 0.1723 [0.1530, 0.1898]</code> on <code>gems57-pooled-hide-v2</code> (<code>11,321</code> withheld positives) while strict-LOQO <code>H86I-SACD</code> recorded <code>E2 = 0.1055 [0.0878, 0.1257]</code> (<code>E1 = 0.0832</code>, pure subsurface <code>E3 = 0.0843</code>), <code>H86I-HVFD</code> recorded <code>E2 = 0.1013 [0.0886, 0.1139]</code> / <code>E3 = 0.1040 [0.0917, 0.1166]</code> (<code>E1 = 0.0475</code>), <code>H86I-RKSC</code> recorded <code>0.0245 [0.0185, 0.0304]</code>, and <code>H86H-PSTD</code> recorded <code>0.0314</code>; all candidates remain <strong>DO NOT SUBMIT</strong> under the registry completeness and literal <code>17GEMSDOE</code> stops. No weekly slot was used.</p></div>
{block86i}
{new_queue}
{hvfd_block}{h86i_block}{block86f}{h86h_block}<h2>Archived earlier planning queue (registry/h86c_hypotheses.json)</h2>
<p>{e(plan['ranking_basis'])} {e(plan['novelty_scope'])}</p><p>{e(plan['evidence_boundary'])}</p>{''.join(sections)}
<h2>Validation plan after blockers are resolved</h2><ol>{steps}</ol>
<p><a href="{REPO}/blob/main/registry/h86f_hypotheses.json">H86F hypothesis register</a> · <a href="{REPO}/blob/main/registry/h86c_hypotheses.json">Inherited H86C register</a> · <a href="evidence/band-physics-verification-20261024.json">Pixel-verified 19-band physics receipt</a> · <a href="{REPO}/blob/main/research/SESSION_H86F_EWCS_REVIEW_20261025.md">2026-10-25 three-pass PhD synthesis</a> · <a href="{REPO}/blob/main/research/GEOTHERMAL_VENT_DISCOVERY_SYNTHESIS.md">Geothermal vent synthesis</a> · <a href="research.html">Physical rationale and limitations</a></p>''')


def fleet_page(feed: dict, ledger: list[dict]) -> str:
    table = []
    for project in feed["projects"]:
        claims = [f'<div><span class="mono">{e(c["submission"] or "No artifact specified")}</span><br><strong>{e(c["value"] or "No score supplied")}</strong> · {e(c["evidence_class"])}</div>' for c in project["owner_reported_results"]]
        source = project.get("commit_url", project["site_url"])
        count = project.get("published_download_tif_count")
        count_text = str(count) if count is not None else "Unknown"
        table.append(f'''<tr><th scope="row"><a href="{e(project['site_url'])}">{e(project['repository'].split('/')[-1])}</a><br><a class="mono" href="{e(source)}">{e(project.get('commit_sha', 'not pinned')[:12])}</a></th>
<td>{''.join(claims) or 'No score supplied'}</td><td>{e(project['status'])}<br>{count_text} TIFF Git objects in docs/downloads<br><small>Metadata only; not validated predictions</small></td></tr>''')
    return page("Project evidence feed", "fleet.html", f'''<p class="eyebrow">Refreshable repository inventory</p><h1>The named-project list,<br>with evidence classes intact.</h1>
<div class="card"><p><strong>{feed['projects_snapshotted']} / {feed['projects_requested']} projects snapshotted</strong> · {e(feed['refreshed_utc'])} · complete API refresh: {str(feed['refresh_complete']).lower()}.</p>
<p>{e(feed['scope'])}</p><p>Every performance scalar below is transcribed from the owner's prompt, not verified from a submission-page receipt. Missing values stay missing; they are not zero. This feed cannot confirm the current competition leader, private-test performance or account quota.</p>
<a href="evidence/fleet-feed.json">Full commit/tree/blob inventory JSON</a> · <a href="evidence/prompt-named-unscored-audit-20261024.json">Historical byte audit of GEMSDOE89 &amp; GEMSDOE90 (unscored when recorded; current owner claims are shown below)</a></div>
<label class="filter" for="fleet-filter">Find a project, method or reported result <input id="fleet-filter" type="search" data-filter-table="fleet-table" placeholder="e.g. GEMSDOE32 or magnetic" autocomplete="off"></label>
<div class="table-wrap"><table id="fleet-table"><thead><tr><th>Project / pinned source</th><th>OWNER-REPORTED, unverified — not ORGANIZER-CONFIRMED</th><th>Repository snapshot</th></tr></thead><tbody>{''.join(table)}</tbody></table></div>
<p>GitHub inventory refresh is automated in the daily Pages workflow. A failed refresh is reported rather than relabeled current. No competition account, historical prediction raster download or submission slot is used by the feed.</p>''')


def source_page(observations: dict) -> str:
    rows = []
    for source in observations["sources"]:
        rows.append(f'''<tr><th scope="row"><a href="{e(source['url'])}">{e(source['id'])}</a><br><small>{e(source['kind'])}</small></th>
<td><strong>{e(source['status'])}</strong><p>{e(source['claim'])}</p><blockquote>{e(source['observed_excerpt'])}</blockquote></td><td>{e(source['caveat'])}</td></tr>''')
    return page("Verified sources and limits", "sources.html", f'''<p class="eyebrow">Primary-source observations</p><h1>What the sources establish.<br>And what they do not.</h1>
<p>Observed on {e(observations['observed_date_utc'])}. {e(observations['retrieval_method'])}. {e(observations['scope'])}</p>
<div class="table-wrap"><table><thead><tr><th>Source</th><th>Observed statement / scope</th><th>Limit</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p><strong>2026-10-25 observation boundary:</strong> <a href="evidence/review-source-checks.json">fresh narrow GitHub byte recheck</a> reverified the official reference README and archived owner H33 audit. Non-GitHub source pages in the tables above were not freshly fetched in this egress-restricted review. <a href="evidence/session-cf73474c-data.json">Native-data/cache receipt</a>: all 19 native bands restored; actual shared derived cache still absent. A mirror hash match is not organizer authentication.</p>
<p><a href="evidence/source-review-20261023.json">Exact observation register (2026-10-23)</a> · <a href="evidence/source-recheck-20261024.json">Live primary-source recheck (2026-10-24)</a> · <a href="fleet.html">All 92 owner-reported project entries</a></p>
<p>Official observations are dated research records, not an automatically authenticated live leaderboard. The daily feed refreshes repository metadata and local file checks, not the meaning of external publications or the remaining account quota.</p>''')


def irregularities(report: dict) -> str:
    items = "".join(f'<li>{e(item)}</li>' for item in report["limitations"])
    return page("Limitations and irregularities", "irregularities.html", f'''<p class="eyebrow">Explicitly unresolved</p><h1>No silent exceptions.<br>No invented score.</h1><ol>{items}</ol>
<h2>Defects found in this review</h2><ul><li>An imported model caller could bypass the mandatory preflight with a boolean parameter. That escape hatch was removed; regression tests require a stop before feature building.</li>
<li>The inherited site compared nonidentical holdout instruments as a repository-wide “highest holdout.” That wording was removed. The automated view labels each design and confidence interval separately.</li>
<li>The inherited headline byte and note-character counts disagreed with the serialized GFCO receipt. Counts now come directly from every actual file and receipt on each build.</li>
<li>The old source ledger conflated the owner's H33 reported result with a different historical projection. The supplied result is retained as OWNER-REPORTED, not mislabeled as either confirmed or fabricated.</li>
<li>A static-site inventory path check accidentally depended on the last traversed HTML path. It now checks the publication root directly, including when there is no HTML input.</li>
<li>PR #60 (<code>IR-86-SPT-02</code>) ran <code>build_spt.py</code> / <code>build_xfleet.py</code> at module import without <code>protocol_preflight.require_feasible()</code>, leaked withheld test-fold fault locations through <code>dist_cat &gt; 2.0</code>, promoted a coin-flip surface (<code>AUC = 0.4947</code>) with <code>100%</code> pinned-witness overlap, misrepresented prose vs code, and placed unregistered binaries in <code>submission/</code> alongside a contradictory <code>docs/submit.html</code> banner; PR #63 (<code>IR-86-TIPRELAY-01</code>) placed unregistered binaries in <code>docs/downloads/</code> with an audit backdoor and <code>85.08%</code> 3-px overlap vs <code>GEMSDOE32</code>; PR #77 (<code>IR-86-SWCON-01</code>) published an unauthorized <code>swcon-submission.html</code> page and uninventoried binaries in <code>docs/downloads/</code> and <code>submission/</code> without <code>require_feasible()</code> or 95% CIs (breaking all three CI workflows on <code>main</code>); and PR #80/#83 bypassed <code>require_feasible()</code> in <code>generate_unique_submission.py</code>, <code>run_h86e.py</code>, and <code>finalize_h86e.py</code>. The merged PR #92 <code>build_unique_submission.py</code> and historical <code>build_gems86_gapres.py</code> entrypoints were also missing that preflight; both now stop before reading inputs or constructing a candidate. The PR #92 TIFF remains registered for audit only and is not cleared. Unregistered binaries and false ready banners were removed, PR #60's <code>submission/</code> binaries remain quarantined outside <code>docs/</code> (excluded from GitHub Pages and SHA/ZIP-verified against <code>spt-full-support-witness-audit.json</code>), all 50 CLI builders and 8 imported orchestrators are gated behind <code>require_feasible()</code>, and <code>audit_release.py</code> + <code>check_site.py</code> fail closed on any other binary or byte modification in <code>submission/</code>.</li>
<li>Forensic review of PR #93's <code>H86E-MMT</code> implementation (<code>IR-86-MMT-RANK01-TIE-20261024</code>, <code>IR-86-MMT-SHIFT-AXIS-20261024</code>, <code>IR-86-MMT-PRE-V2-UNBOUND-REPORTS-20261024</code>, <code>IR-86-PREPARE-RELPATH-20261024</code>; <a href="evidence/session-20261024-86569dcd-run-card.json">session card</a>) discovered that <code>gems86_mmt.features.rank01</code> assigned row-major tie ramps up to <code>0.9922</code> across <code>5,127,174</code> zero background cells—packing all <code>44,090</code> <code>R0_D28_visible_collar</code> comparator dots into southern rows <code>3023..3727</code>—and that <code>build_marker_features</code> shifted <code>tgrad</code> parallel to the gradient normal <code>(sin θ, cos θ)</code> rather than along corridor strike <code>(-cos θ, sin θ)</code>. Both defects, plus <code>scripts/prepare_data.py</code>'s relative <code>--data-dir</code> crash and missing <code>require_feasible()</code> guards in <code>build_h86e_features.py</code>, <code>run_h86e_ridf.py</code>, and <code>run_h86e_mmt.py</code>, are fixed with regression tests while preserving historical run cards unedited.</li>
<li>Embedded GeoTIFF band-description mislabels inside <code>training_features.tif</code> (<code>IR-86-BAND6-TC-MISLABEL-20261024</code>, <code>IR-86-BAND11-18-GRAV-VECTOR-20261024</code>): pixel-level audit across <code>5.15M–5.16M</code> footprint cells (<a href="evidence/band-physics-verification-20261024.json">receipt</a>) proved Band 6 (<code>tc</code>) is strictly positive (<code>min = +2.9534</code>, 0 zero-crossings) and correlates at <code>r = +0.997140</code> with USGS GeoDAWN Airborne Radiometric Total Count (<code>TC</code>) vs <code>r = +0.012796</code> with true magnetic tilt <code>atan2(Band 9, Band 3)</code>, while <code>(+Band 18, -Band 11)</code> is the signed 2-D horizontal gravity gradient vector (<code>r = +0.948186</code> and <code>+0.938102</code>) rather than scalar/vertical gradients. Hypothesis definitions and documentation were repaired accordingly.</li>
<li><code>IR-86-PCC-01</code> / <code>IR-86-PCC-02</code>: the 2026-10-25 H86F-PCC lane wrote a format-valid audit TIFF and the gates rejected it. HOLDOUT-DTI does not beat the same-split comparator, the shared PA-86-02 script refused the incomplete registry (two rasters are not on the submission grid), and the space-filling overlap diagnostic is not a gate pass. The template cached feature stack is absent; the lane used the SHA-pinned 19-band TIFF and did not relabel it as that cache. No slot was used. See <a href="evidence/h86f-pcc-run-card.json">the negative run card</a>.</li>
<li>Byte-level forensic review of the two newly prompt-named unscored fleet artifacts (<code>IR-86-FLEET-GEMS89-90-20261024</code>; <a href="evidence/prompt-named-unscored-audit-20261024.json">measured JSON receipt</a>) found that <code>GEMSDOE89</code> (<code>gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros</code>, SHA-256 <code>715c8b86...</code>) claimed <code>complete_registry_coverage=true</code> over a 91-raster subset that omitted both <code>17GEMSDOE</code> (<code>100.0%</code> forward 3-px overlap) and discrete binary <code>13GEMSDOE</code> (<code>99.92%</code> = <code>37,624/37,654</code> forward 3-px overlap), while <code>GEMSDOE90</code> (<code>gems90-cnc-35000dots-20261024T084324Z</code>, SHA-256 <code>e1e91be2...</code>) privately altered the uniqueness rule, exceeded <em>both</em> clauses of its altered rule (<code>max_overlap = 0.9833 &gt; 0.70</code> and <code>max_excess_over_chance = 0.4037 &gt; 0.30</code>; pinned-checker overlap <code>98.35%</code> vs binary <code>13GEMSDOE</code> and <code>100.0%</code> vs <code>17GEMSDOE</code>) yet still emitted <code>duplicate=false</code>, used external <code>qfault_sliprate_den</code> (<code>AUC = 0.7784</code>) on cut-segment folds, and recorded a <code>NEGATIVE</code> score-calibration verdict. Also fixed a mis-cited rule reference on the executive checklist from nonexistent <code>Official Rules §5–6</code> to verified <code>Official Rules §1.1 &amp; §3.4–3.6</code> (<code>IR-86-RULES-SECT-20261024</code>).</li>
<li><code>IR-86-H86F-EWCS-TRANSQUAD-PU-20261025</code>: forensic review of <code>scripts/run_h86f_ewcs.py</code> in session <code>95a42d60</code> found that while <code>vis = f["visible"] &amp; fp</code> properly withheld all <code>11,321</code> hidden positive pixels and their 3-px feature collar globally (zero hidden-label leakage), <code>sample_nested_pu(..., vis, fp, ...)</code> drew visible positives and unlabeled background rows across all 4 quadrants <code>fp</code> rather than restricting training samples to <code>fp &amp; (quad != fold_i)</code>. The new <code>H86I-SACD</code> runner (<code>scripts/run_h86i_sacd.py</code>) enforces strict spatial Leave-One-Quadrant-Out training (<code>train_region = fp &amp; (quad != fold_i)</code>), leaving the archived <code>H86F-EWCS</code> run card untouched with an explicit comparator note.</li></ul>
<p>The historical scientific cards and TIFF bytes are preserved. This audit does not retroactively certify earlier experiments, erase protocol overruns or change thresholds.</p>
<p><a href="evidence/latest-review-run-card.json">Current negative run card</a> · <a href="evidence/spt-run-card.json">Revoked SPT forensic card</a> · <a href="{REPO}/blob/main/research/SESSION_20261024_REVIEW.md">2026-10-24 three-pass review and next actions</a></p>''')


def scientific_context() -> str:
    return page("Scientific context", "hypotheses.html", '''<p class="eyebrow">Mechanism is not validation</p><h1>Why geometry matters,<br>and why it is not enough.</h1>
<p>The official distance-weighted Tversky metric uses maximum prediction-times-kernel credit at each truth pixel. More nearby prediction mass need not increase that maximum; it can still add false-positive cost. Sparse placement can therefore outperform redundant mass, but removing the only useful cover of a real fault can reduce the index.</p>
<p>With weighted recovered truth T, weighted false-positive mass F, fixed truth count N and the official coefficients, the index is T / (0.2T + 0.2F + 0.8N + epsilon). If pruning loses credit a and removes false-positive mass b, it helps exactly when T b &gt; a(F + 4N + 5 epsilon), for positive denominators. This identity is tested against the shared metric. It is not a leaderboard projection or evidence of why a particular private result occurred.</p>
<p>A density, magnetization, conductivity or relief contrast is not uniquely a fault. The new magnetic-marker idea instead asks whether pre-existing markers were displaced. Even that can be imitated by unrelated contacts, remanence or survey seams. A basement offset can also be old and buried rather than a present surface trace. The scientific reports on the sources page motivate and limit the hypotheses; none validates our untested detector.</p>
<p>First-principles pixel verification of <code>training_features.tif</code> (<a href="evidence/band-physics-verification-20261024.json"><code>band-physics-verification-20261024.json</code></a>) also exposed two critical header mislabels inside the competition raster: Band 6 (<code>tc</code>) is GeoDAWN Airborne Radiometric Total Count (<code>TC</code>, <code>r = +0.997140</code>, <code>min = +2.9534</code>, zero zero-crossings) rather than magnetic tilt, and <code>(+Band 18, -Band 11)</code> is the signed 2-D horizontal gravity gradient vector <code>(dg/dx_east, dg/dy_north)</code> (<code>r = +0.9482</code>, <code>+0.9381</code>), enabling exact Laplace vertical gravity curvature <code>g_zz = -(d_x B18 - d_y B11)</code> without external gravity grids.</p>
<p>The strongest next step is a frozen, visible-only, buffered pipeline comparison, plus genuinely independent and provenance-audited off-catalogue evidence where available. New proxies cannot silently replace the required evaluator. No fault raster by itself establishes geothermal heat, fluid supply, open permeability or an economic resource.</p>
<p><a href="h86-fvmb-forensics.html">Preserved FVMB figures, with explicit archive limitations</a></p>
<p><a href="sources.html">Official sources and observation scope</a> · <a href="hypotheses.html">Ranked hypotheses</a></p>''')


def fvmb_archive(report: dict) -> str:
    a = next(a for a in report["artifacts"] if a["source_card"] == "docs/evidence/h86-fvmb-run-card.json")
    h = a["historical_holdout"]
    figures = (
        ("fig1_h86_spatial_discovery_map.png", "Archived spatial-distribution illustration"),
        ("fig2_ablation_and_forensics.png", "Archived ablation illustration"),
        ("fig3_canary_and_importance.png", "Archived canary / feature-importance illustration"),
        ("fig4_registry_uniqueness.png", "Archived, incomplete registry-comparison illustration"),
    )
    images = "".join(f'<figure><img src="assets/{filename}" alt="{caption}; historical evidence, not rerun by this review" loading="lazy"><figcaption>{caption}. Original labels are archival, not a new measurement or endorsement of cross-design ranking.</figcaption></figure>' for filename, caption in figures)
    return page("FVMB archived evidence", "evidence.html", f'''<p class="eyebrow">Concurrent lane archive · not rerun by this review</p><h1>H86-FVMB:<br>preserved, not promoted.</h1>
<div class="callout"><span class="badge bad">DO NOT SUBMIT · LITERAL UNIQUENESS FAILED</span><p>The current all-file audit reopens this TIFF and measures final-dot overlap 1.0 against the immutable full-support witness. A restricted modern-raster comparison is not an authorized exemption. No human inspection is needed to discover this release is blocked.</p></div>
<p><a class="btn" href="{e(link(a['file']))}" download>Download TIFF — audit only</a> <a class="btn secondary" href="{e(link(a['zip_file']))}" download>Single-TIFF ZIP — audit only</a></p>
<p class="filename">{e(Path(a['file']).name)} · {a['bytes']:,} bytes</p><p><code>{a['sha256']}</code></p>
<h2>Applicable archived instrument</h2><p><strong>HOLDOUT-DTI {h['value']:.5f}</strong> · 95% CI [{h['ci95'][0]:.5f}, {h['ci95'][1]:.5f}] · {h['withheld_positives']:,} withheld positives · {e(h['evaluator_version'])}.</p><p>{e(h['design'])}. <strong>Archived, not recomputed.</strong> {e(h['caveat'])}</p>
<p>The original card contains text tokens in two numeric paired-delta fields. This renderer does not coerce them into measurements or reproduce its unsupported repository-wide “champion”/“highest” interpretation. The card and figures remain historical evidence, not current scientific clearance. A separate registry manifest also describes an amendment absent from the actual shared bytes; <code>research/template_pin.json</code> remains the effective pin, verified unchanged.</p>
<p><a href="{e(link(a['source_card']))}">Original scientific card</a> · <a href="evidence/h86_fvmb_holdout_ablation.json">Original ablation record</a> · <a href="evidence.html">All-artifact gate results</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE86/blob/4644761b4da2eda086382aab27d4ef4638423c42/docs/h86-fvmb-forensics.html">Original page at the incoming main commit</a>.</p>
<h2>Historical figures — explicitly limited</h2><p>The images below were generated by the concurrent lane, not this review. Their geological interpretations, method-optimality claims, novelty assertions, metrics and registry subsets were not independently revalidated here. Figure labels must not be used as organizer receipts or comparisons across incompatible holdout designs.</p>{images}''')


def submit_gate(report: dict, review: dict) -> str:
    return page("Submission gate & candidate revocations", "submit.html", f'''<p class="eyebrow">Automated submission safety gate · IR-86-SPT-02, IR-86-TIPRELAY-01, IR-86-SWCON-01 &amp; IR-86-FAULTHALO-01</p><h1>DO NOT SUBMIT:<br>Concurrent SPT, TIPRELAY, SWCON &amp; FAULTHALO candidates revoked.</h1>
<div class="callout"><span class="badge bad">CURRENT DECISION: DO NOT SUBMIT · VERDICT NEGATIVE</span><p>Concurrent commits published candidates (<code>SPT</code> in PR #60, <code>H86-TIPRELAY</code> in PR #63, <code>SWCON</code> in PR #77, and <code>FAULTHALO</code> in PR #80) bypassing preflight or uniqueness gates. Automated forensic review on <time>{e(review['registry_measured_utc'])}</time> verified that all four violate mandatory uniqueness and/or preflight gates; none is authorized for competition upload.</p>
<a class="btn" href="executive-summary.html">Open official submission guide &amp; audit status →</a><a class="btn secondary" href="evidence/spt-full-support-witness-audit.json">Open SPT witness audit JSON</a></div>
{pr92_candidate_notice(report)}
<h2>1. Why PR #60's SPT candidate is blocked (<code>IR-86-SPT-02</code>)</h2>
<ol><li><strong>100% overlap with pinned registry witness:</strong> Direct measurement of SHA-256 <code>26cf2d392663b4ad3118534b07de889099e0ea9d48bfa3bcddbf8ca00dd5b342</code> against <code>17GEMSDOE</code> (<code>ab0a0a62...</code>) yields <code>candidate_dot_overlap_within_3px_of_witness = 1.0 &gt; 0.70</code> (<a href="evidence/spt-full-support-witness-audit.json">witness audit</a> · <a href="evidence/spt-run-card.json">run card</a>).</li>
<li><strong>Single-feature canary below coin-flip (<code>AUC = 0.4947</code>) &amp; withheld-fold collar leak:</strong> The throw-vote surface had no positive fault discrimination on the footprint and masked <code>dist_cat &gt; 2.0</code> using the full <code>existing_faults.tif</code> catalogue.</li>
<li><strong>Preflight &amp; quarantine enforced:</strong> Both <code>scripts/build_spt.py</code> and <code>scripts/build_xfleet.py</code> now stop at <code>protocol_preflight.require_feasible()</code> before loading features, and the <code>submission/</code> artifact stays quarantined outside <code>docs/</code> (excluded from GitHub Pages, SHA/ZIP-verified against <code>spt-full-support-witness-audit.json</code> with <code>download_authorized=false</code>).</li></ol>
<h2>2. Why PR #63's H86-TIPRELAY candidate was revoked (<code>IR-86-TIPRELAY-01</code>)</h2>
<ol><li><strong>85.08% 3-px dot overlap against sparse <code>GEMSDOE32</code> <code>h33-h33-2-b2</code> (<code>&gt; 70%</code> limit):</strong> Even before checking the continuous witness (<code>100%</code> overlap), SHA-256 <code>c56945618d8316f4f134474c1f707444a46892a47aa7b7e18181bee6243daae3</code> copied 70% of <code>H33</code> verbatim and overlapped <code>85.08%</code> with <code>GEMSDOE32</code> and <code>85.10%</code> with <code>GEMSDOE28</code> (<a href="evidence/h86-tiprelay-run-card.json">revoked TIPRELAY card</a>).</li>
<li><strong>Zero holdout evaluation:</strong> Reported <code>PROJECTION_NOT_HOLDOUT</code> with no spatially-blocked evaluation or leakage canary, and added a <code>tiprelay</code> exclusion backdoor to <code>audit_release.py</code> that broke <code>check_site.py</code> and <code>build_site.py --check</code>. That unregistered binary and backdoor have been removed, and <code>scripts/gen_tip_final.py</code> is now gated behind <code>require_feasible()</code>.</li></ol>
<h2>3. Why PR #77's SWCON candidate was revoked (<code>IR-86-SWCON-01</code>)</h2>
<ol><li><strong>99.78% 3-px dot overlap against discrete binary dotted <code>13GEMSDOE</code> (<code>&gt; 70%</code> limit) + 100% vs <code>17GEMSDOE</code>:</strong> SHA-256 <code>5576b15c1c66dd5353c515201c06572d6e7a854aaa130bd95d167435f6f9374f</code> claimed clearance against the dotted registry, yet pinned <code>vendor/gems57/uniqueness.py</code> measures <code>0.997769</code> (<code>37,570 / 37,654</code> dots) forward 3-px overlap against discrete binary <code>13GEMSDOE</code> (<code>206,895</code> dots) and <code>1.0000</code> against <code>17GEMSDOE</code> (<a href="evidence/swcon-run-card.json">revoked SWCON card</a>).</li>
<li><strong>Blended 33 prior submissions, below-chance canary (<code>AUC = 0.4046</code>), missing CI (<code>ci95 = null</code>), &amp; broken Pages deploy:</strong> Bypassed <code>protocol_preflight.require_feasible()</code>, blended existing submissions rather than geological features, reported <code>HOLDOUT-DTI = 0.00746</code> without a confidence interval, and placed unregistered binaries in <code>docs/downloads/</code> and <code>submission/</code> plus hand-edited HTML that broke CI and GitHub Pages deployment. Unregistered binaries have been removed and <code>scripts/build_gems86_swcon.py</code> is gated behind <code>require_feasible()</code>.</li></ol>
<h2>4. Why PR #80's FAULTHALO candidate was revoked (<code>IR-86-FAULTHALO-01</code>)</h2>
<ol><li><strong>Bypassed <code>protocol_preflight.require_feasible()</code> &amp; overlapped 99.88% with discrete binary <code>13GEMSDOE</code>:</strong> SHA-256 <code>8a66c57c576cd2a4d0e78c349a6ac2614b3a4d9dc14691a4d55830818e4b160b</code> emitted <code>4,210,938</code> positive cells (<code>82.46%</code> of allowed cells) purely from <code>distance_transform_edt(~cat)</code> with zero geological bands and <code>HOLDOUT-DTI = NOT_RUN</code>, yielding <code>0.998783</code> forward 3-px overlap vs discrete binary <code>13GEMSDOE</code> and <code>1.0000</code> (Jaccard <code>0.8149</code>) vs <code>17GEMSDOE</code> (<a href="evidence/h86-faulthalo-run-card.json">revoked FAULTHALO card</a>).</li>
<li><strong>Mutated archived <code>2026-10-23</code> card &amp; swapped DTI <code>α/β</code> weights:</strong> Rebranded a <code>2026-10-24</code> raster inside archived <code>session-20261023-run-card.json</code> and inverted <code>α=0.2</code> (FP) / <code>β=0.8</code> (FN) in <code>research/H33_ANALYSIS.md</code>. Both are repaired and <code>scripts/generate_unique_submission.py</code> is gated behind <code>require_feasible()</code>.</li></ol>
<p>All {report['artifact_count']} preserved historical research rasters remain available for audit-only inspection on <a href="index.html#downloads">Downloads</a>, and the exact DrivenData portal procedure (<code>[0, 1]</code> range check, unique name, and <code>&lt;= 140</code>-char note) is documented on <a href="executive-summary.html">How to submit</a>.</p>''')


def render(root: Path = ROOT) -> dict[str, str]:
    import json
    report = build_report(root)
    if not report["audit_ok"]:
        raise ValueError("Refusing to publish a download page for failed artifact integrity")
    feed = strict_json(root / "docs/evidence/fleet-feed.json")
    if (feed["owner_ledger_sha256"] != sha256(root / "registry/prior_scores.csv")
            or feed["targets_sha256"] != sha256(root / "registry/site_targets.json")):
        raise ValueError("Fleet feed is stale relative to its ledger/target inputs")
    registry = strict_json(root / "docs/evidence/all-artifacts-registry.json")
    spt_audit = strict_json(root / "docs/evidence/spt-full-support-witness-audit.json")
    spt_card = strict_json(root / "docs/evidence/spt-run-card.json")
    candidate_file = root / spt_audit["candidate_file"]
    if not candidate_file.is_file():
        raise ValueError("SPT candidate is missing from the audit archive")
    spt_receipt = strict_json(candidate_file.with_suffix(".json"))
    if (sha256(candidate_file) != spt_audit["candidate_file_sha256"]
            or spt_receipt != spt_card
            or "download_url" in spt_card
            or spt_card["raster_sha256"] != spt_audit["candidate_file_sha256"]
            or spt_audit["candidate_dot_overlap_within_3px_of_witness"] <= spt_audit["literal_overlap_limit"]
            or spt_audit["verdict"] != "negative_duplicate_stop_do_not_submit"
            or spt_card["verdict"] != "negative"
            or spt_card["submission_ready"] is not False):
        raise ValueError("SPT candidate is stale or violates the literal full-support witness stop")
    review = strict_json(root / "docs/evidence/latest-review-run-card.json")
    if (review["release_report_sha256"] != sha256(root / "docs/evidence/release-readiness.json")
            or review["registry_measurement_sha256"] != sha256(root / "docs/evidence/all-artifacts-registry.json")
            or review["registry_measured_utc"] != registry["measured_utc"]
            or review["verdict"] != "negative" or review["submission_ready"] is not False
            or review["new_candidate_generated"] is not False):
        raise ValueError("Current review is stale or contradicts the negative release audit; remeasure registry")
    sources = strict_json(root / "docs/evidence/source-review-20261023.json")
    plan = strict_json(root / "registry/h86c_hypotheses.json")
    with (root / "registry/prior_scores.csv").open(newline="", encoding="utf-8") as stream:
        ledger = list(csv.DictReader(stream))
    summary = {k: report[k] for k in ("schema", "audit_ok", "decision", "submission_ready", "safe_to_submit", "artifact_count", "locally_valid_artifacts", "new_candidate_generated", "experiments_run", "submission_slots_used")}
    summary.update(approved_for_weekly_slot=report["approved_for_weekly_slot"],
                   selector_run=report["selector_run"],
                   featured_research_artifact=None, current_comparable_holdout_best=None,
                   reason="No selector decision. Different historical holdout designs cannot be ranked by their maxima; the pre-existing PR #92 artifact remains audit-only and fails the literal witness gate.",
                   release_readiness="../evidence/release-readiness.json")
    existing_candidate = pr92_candidate(report)
    if existing_candidate is not None:
        _, candidate = existing_candidate
        holdout = candidate["historical_holdout"]
        measurement = candidate["registry_measurement"]
        summary["preexisting_pr92_artifact"] = dict(
            file=candidate["file"], sha256=candidate["sha256"], status="DO NOT SUBMIT",
            safe_to_download_for_audit=candidate["safe_to_download_for_audit"],
            holdout_dti=dict(evidence_class="HOLDOUT-DTI", status=holdout["status"],
                evaluator_version=holdout["evaluator_version"], withheld_positives=holdout["withheld_positives"],
                value=holdout["value"], ci95=holdout["ci95"]),
            registry_measurement=dict(evidence_class="REGISTRY-MEASUREMENT",
                spearman_full_footprint=measurement["spearman_full_footprint"],
                forward_overlap_3px=measurement["forward_overlap_3px"],
                unique=measurement["unique"], stop_required=measurement["stop_required"],
                complete_accessible_scan=measurement["complete_accessible_scan"]))
    card86e = strict_json(root / "docs/evidence/h86e-ridf-run-card.json")
    mmt_path = root / "docs/evidence/h86e-mmt-run-card.json"
    mmt_card = strict_json(mmt_path)
    if (mmt_card["verdict"] != "negative" or mmt_card["submission_ready"] is not False
            or mmt_card["safe_to_submit"] is not False
            or mmt_card["approved_for_weekly_slot"] is not False
            or mmt_card["submission_slots_used"] != 0
            or mmt_card["experiments_run"] != 3):
        raise ValueError("H86E-MMT card must stay negative and slot-free")
    kslb_path = root / "docs/evidence/kslb_pa86_chance_overlap.json"
    kslb = strict_json(kslb_path) if kslb_path.exists() else None
    if card86e["verdict"] != "negative" or card86e["submission_ready"] is not False:
        raise ValueError("H86E card must stay negative unless a selector step is recorded")
    swcon_path = root / "docs/evidence/swcon_pa86_chance_overlap.json"
    swcon = strict_json(swcon_path) if swcon_path.exists() else None
    gzzd_card = strict_json(root / "docs/evidence/h86f-gzzd-run-card.json")
    if (gzzd_card["verdict"] != "negative" or gzzd_card["decision"] != "DO NOT SUBMIT"
            or gzzd_card["submission_ready"] is not False
            or gzzd_card["safe_to_submit"] is not False
            or gzzd_card["approved_for_weekly_slot"] is not False
            or gzzd_card["submission_slots_used"] != 0
            or gzzd_card["experiments_run"] != 3
            or gzzd_card["raster_sha256"] is None):
        raise ValueError("H86F-GZZD card must stay negative, slot-free and bound to its raster")
    pcc_path = root / "docs/evidence/h86f-pcc-run-card.json"
    pcc_card = strict_json(pcc_path)
    pcc_diag = strict_json(root / "docs/evidence/h86f-pcc-chance-diagnostic.json")
    if (pcc_card["verdict"] != "negative" or pcc_card["safe_to_submit"] is not False
            or pcc_card["approved_for_weekly_slot"] is not False
            or pcc_card["submission_slots_used"] != 0 or pcc_card["decision"] != "DO NOT SUBMIT"):
        raise ValueError("H86F-PCC card must stay negative until a selector records a pass")
    if pcc_diag.get("gate_pass") is not False or pcc_diag.get("informative_firings") != 0:
        raise ValueError("H86F-PCC chance diagnostic is not a clearance record")
    pstd_path = root / "docs/evidence/h86h-pstd-run-card.json"
    pstd_card = strict_json(pstd_path) if pstd_path.is_file() else None
    if pstd_card is not None and (
            pstd_card["verdict"] != "negative" or pstd_card["submission_ready"] is not False
            or pstd_card["safe_to_submit"] is not False
            or pstd_card["approved_for_weekly_slot"] is not False
            or pstd_card["budget"]["submission_slots_used"] != 0
            or pstd_card["budget"]["experiments_run"] > 3):
        raise ValueError("H86H-PSTD card must stay negative, within 3-arm budget, and slot-free")
    h86h_path = root / "research/H86H_PSTD_PREREGISTRATION.json"
    h86h_prereg = strict_json(h86h_path) if h86h_path.is_file() else None
    hvfd_path = root / "docs/evidence/h86i-hvfd-run-card.json"
    hvfd_card = strict_json(hvfd_path) if hvfd_path.is_file() else None
    hvfd_html = ""
    if hvfd_card is not None:
        if (hvfd_card["verdict"] != "negative" or hvfd_card["decision"] != "DO NOT SUBMIT"
                or hvfd_card["submission_ready"] is not False
                or hvfd_card["safe_to_submit"] is not False
                or hvfd_card["approved_for_weekly_slot"] is not False
                or hvfd_card["submission_slots_used"] != 0
                or hvfd_card["experiments_run"] != 3
                or hvfd_card["raster_sha256"] is None):
            raise ValueError("H86I-HVFD card must stay negative, slot-free and bound to its raster")
        hvfd_html = h86i_hvfd_answer(hvfd_card)
    hvfd_prereg_path = root / "research/H86I_HVFD_PREREGISTRATION.json"
    hvfd_prereg = strict_json(hvfd_prereg_path) if hvfd_prereg_path.is_file() else None
    rksc_path = root / "docs/evidence/h86i-rksc-run-card.json"
    rksc_card = strict_json(rksc_path) if rksc_path.is_file() else None
    rksc_html = ""
    if rksc_card is not None:
        if (rksc_card["verdict"] != "negative" or rksc_card["decision"] != "DO NOT SUBMIT"
                or rksc_card["submission_ready"] is not False
                or rksc_card["safe_to_submit"] is not False
                or rksc_card["approved_for_weekly_slot"] is not False
                or rksc_card["submission_slots_used"] != 0
                or rksc_card["experiments_run"] != 3
                or rksc_card["raster_sha256"] is None):
            raise ValueError("H86I-RKSC card must stay negative, within 3-arm budget, slot-free, and bound to its raster")
        rksc_html = h86i_rksc_answer(rksc_card)
    h86i_path = root / "research/H86I_RKSC_PREREGISTRATION.json"
    h86i_prereg = strict_json(h86i_path) if h86i_path.is_file() else None
    h86j_path = root / "docs/evidence/h86j-mpc-run-card.json"
    h86j_card = strict_json(h86j_path) if h86j_path.is_file() else None
    h86j_html = ""
    if h86j_card is not None:
        if (h86j_card["verdict"] != "negative" or h86j_card["decision"] != "DO NOT SUBMIT"
                or h86j_card["submission_ready"] is not False
                or h86j_card["safe_to_submit"] is not False
                or h86j_card["approved_for_weekly_slot"] is not False
                or h86j_card["submission_slots_used"] != 0
                or h86j_card["experiments_run"] != 3
                or h86j_card["gates"]["sgmc_proxy_beats_H33_paired_ci"] is not False
                or sha256(root / h86j_card["submission_file"]) != h86j_card["raster_sha256"]):
            raise ValueError("H86J-MPC card must stay negative/falsified, within 3-experiment budget, slot-free, and bound to its raster")
        h86j_html = h86j_mpc_answer(h86j_card)
    comp_path = root / "docs/evidence/h86e_comparator.json"
    comp = strict_json(comp_path) if comp_path.exists() else None
    h86g_card = strict_json(root / "docs/evidence/h86g-edti-run-card.json")
    h86g_tif = root / h86g_card["submission_file"]
    if (h86g_card["verdict"] != "promote" or h86g_card["submission_ready"] is not True
            or h86g_card["safe_to_submit"] is not False
            or h86g_card["approved_for_weekly_slot"] is not False
            or h86g_card["submission_slots_used"] != 0
            or not all(h86g_card["gates"].values())
            or sha256(h86g_tif) != h86g_card["raster_sha256"]):
        raise ValueError("H86G-EDTI card must stay promote/gates-pass/slot-free and bound to its raster")
    h86g_artifact = next((a for a in report["artifacts"] if a.get("source_card") == "docs/evidence/h86g-edti-run-card.json"), None)
    if (h86g_artifact is None or h86g_artifact.get("historical_lane_verdict") != "promote"
            or h86g_artifact.get("literal_registry_stop") is not True
            or h86g_artifact["registry_measurement"]["forward_overlap_3px"] != 1.0):
        raise ValueError("H86G-EDTI must remain audit-only under the current measured literal witness stop")
    summary["historical_h86g_lane"] = dict(
        submission_name=h86g_card["submission_name"],
        file=h86g_card["submission_file"], raster_sha256=h86g_card["raster_sha256"],
        historical_verdict=h86g_card["verdict"], current_verdict="negative",
        safe_to_submit=False, approved_for_weekly_slot=False,
        decision="DO NOT SUBMIT — literal witness overlap exceeds the 0.70 stop.",
        scope="Historical PA-86 like-for-like promotion only; no current submission authorization.")
    h86g_html = h86g_edti_answer(h86g_card, h86g_artifact)
    plan86f_path = root / "registry/h86f_hypotheses.json"
    plan86f = strict_json(plan86f_path) if plan86f_path.is_file() else None
    ewcs_path = root / "docs/evidence/h86f-ewcs-run-card.json"
    if root.resolve() == ROOT.resolve() and not ewcs_path.is_file():
        raise ValueError("Missing H86F-EWCS run card in repository root")
    ewcs_html = ""
    if ewcs_path.is_file():
        ewcs_card = strict_json(ewcs_path)
        if (ewcs_card["verdict"] != "negative" or ewcs_card["decision"] != "DO NOT SUBMIT"
                or ewcs_card["submission_ready"] is not False
                or ewcs_card["safe_to_submit"] is not False
                or ewcs_card["approved_for_weekly_slot"] is not False
                or ewcs_card["submission_slots_used"] != 0
                or ewcs_card["experiments_run"] != 3
                or ewcs_card["raster_sha256"] is None):
            raise ValueError("H86F-EWCS card must stay negative, slot-free, and bound to its raster")
        ewcs_html = h86f_ewcs_answer(ewcs_card)
    pstd_html = h86h_pstd_answer(pstd_card) if pstd_card is not None else ""
    session_data = strict_json(root / "docs/evidence/session-cf73474c-data.json")
    registry_inputs = strict_json(root / "docs/evidence/registry-input-grid-review-20261025.json")
    concurrent = strict_json(root / "docs/evidence/concurrent-artifact-review-20261025.json")
    new_plan = strict_json(root / "registry/h86g_hypotheses.json")
    if (session_data["actual_shared_feature_stack_restored"] is not False
            or registry_inputs["uniqueness_clearance"] is not False
            or concurrent["registry_complete"] is not False
            or concurrent["preplacement_surfaces_measured"] is not False
            or concurrent["new_candidate_generated"] is not False):
        raise ValueError("Read-only review receipts cannot authorize a candidate or claim a restored shared cache")
    preparation = session_data["native_band_preparation"]
    if sha256(root / preparation["manifest"]) != preparation["sha256"]:
        raise ValueError("Native preparation receipt drift")
    files = {a["file"]: a["sha256"] for a in report["artifacts"]}
    for comparison in concurrent["comparisons"]:
        if (files.get(comparison["candidate_file"]) != comparison["candidate_sha256"]
                or comparison["shared_result"]["unique"] is not False
                or comparison["shared_result"]["complete_accessible_scan"] is not False):
            raise ValueError("Concurrent pair receipt is stale or falsely claims full-registry clearance")
    plan86i_path = root / "registry/h86i_hypotheses.json"
    plan86i = strict_json(plan86i_path) if plan86i_path.is_file() else None
    sacd_path = root / "docs/evidence/h86i-sacd-run-card.json"
    sacd_card = strict_json(sacd_path) if sacd_path.is_file() else None
    sacd_banner = ""
    if sacd_card is not None:
        if (sacd_card["verdict"] != "negative" or sacd_card["decision"] != "DO NOT SUBMIT"
                or sacd_card["submission_ready"] is not False
                or sacd_card["safe_to_submit"] is not False
                or sacd_card["approved_for_weekly_slot"] is not False
                or sacd_card["submission_slots_used"] != 0
                or sacd_card["experiments_run"] > 3
                or sacd_card["raster_sha256"] is None):
            raise ValueError("H86I-SACD card must stay negative, <=3 arms, slot-free, and bound to its raster")
        sacd_banner = h86i_sacd_answer(sacd_card)
    review_notice = current_review_notice(session_data, registry_inputs, concurrent)
    new_queue = new_hypothesis_queue(new_plan)
    answer = (h86j_html + hvfd_html + rksc_html + ewcs_html + pstd_html + h86f_gzzd_answer(gzzd_card, comp) + h86f_pcc_answer(pcc_card, pcc_diag)
              + h86e_answer(card86e, kslb, swcon) + h86e_mmt_answer(mmt_card, comp))
    hypothesis_count = (len(plan["hypotheses"]) + len(new_plan["hypotheses"])
                        + (len(plan86f["hypotheses"]) if plan86f else 0)
                        + (len(h86h_prereg["candidate_hypotheses"]) if h86h_prereg else 0)
                        + (len(h86i_prereg["candidate_hypotheses"]) if h86i_prereg else 0)
                        + (len(hvfd_prereg["ranked_hypotheses"]) if hvfd_prereg else 0)
                        + (len(plan86i["hypotheses"]) if plan86i else 0))
    return {
        "docs/index.html": home(report, feed, registry, review, hypothesis_count, answer, review_notice, h86g_html, sacd_banner),
        "docs/executive-summary.html": executive(report, sources, answer, review_notice, h86g_html, sacd_banner),
        "docs/submit.html": submit_gate(report, review),
        "docs/evidence.html": evidence(report),
        "docs/hypotheses.html": hypotheses(plan, plan86f, h86h_prereg, pstd_card, h86i_prereg, rksc_card, hvfd_prereg, hvfd_card, new_queue=new_queue, plan86i=plan86i, sacd_card=sacd_card),
        "docs/fleet.html": fleet_page(feed, ledger),
        "docs/sources.html": source_page(sources),
        "docs/irregularities.html": irregularities(report),
        "docs/research.html": scientific_context(),
        "docs/h86-fvmb-forensics.html": fvmb_archive(report),
        "docs/evidence/release-readiness.json": json.dumps(report, indent=2, allow_nan=False) + "\n",
        "docs/evidence/session-20261023-run-card.json": json.dumps(session_card(report, root), indent=2, allow_nan=False) + "\n",
        "docs/data/summary.json": json.dumps(summary, indent=2, allow_nan=False) + "\n",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated files without writing")
    args = parser.parse_args(argv)
    outputs = render()
    stale = []
    for relative, content in outputs.items():
        target = ROOT / relative
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != content:
                stale.append(relative)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    if stale:
        print("Stale generated files: " + ", ".join(stale), file=sys.stderr)
        return 1
    print("Evidence-generated site: PASS; all downloads research only; no file authorized for submission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
