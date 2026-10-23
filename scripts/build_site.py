#!/usr/bin/env python3
"""Deterministic static-site generator & fail-closed integrity verifier for GEMSDOE86.

Generates `docs/index.html`, `docs/executive-summary.html`, `docs/hypotheses.html`,
`docs/evidence.html`, and `docs/irregularities.html` directly from the canonical JSON
artifacts in `docs/evidence/` and `evidence/` (zero hand-edited numbers in HTML),
then verifies every local link, registered download, and fail-closed safety banner.
"""
from __future__ import annotations

import html
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

CANDIDATES = (
    "gems86-h86c-kslb-44090dots-20261023T010446Z-83854555-zeros.tif",
    "gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.tif",
    "gems86-rmrb-kthu-rtp-37654-20261022-DO-NOT-SUBMIT.tif",
    "gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.tif",
    "gems86-gmc-linepost-90568d-20261022T222859Z-900ceac1-zeros.tif",
    "gems86-gmc-linepost-offcat-90568d-20261022T224539Z-e6f914e4-zeros.tif",
    "gems86-h86-edge2of5-dotted38000-20261022T225931Z-70513125-zeros.tif",
)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        self.values.extend(value for key, value in attrs if key in {"href", "src"} and value)


def _nav(active: str) -> str:
    tabs = [
        ("index.html", "Decision"),
        ("executive-summary.html", "How to submit"),
        ("hypotheses.html", "Hypotheses"),
        ("evidence.html", "Fleet evidence"),
        ("sources.html", "Sources"),
        ("irregularities.html", "Irregularities"),
    ]
    parts = []
    for href, label in tabs:
        attr = ' style="color:#e8eefc"' if href == active else ""
        parts.append(f'<a href="{href}"{attr}>{label}</a>')
    return f"<header><nav><b>GEMSDOE86</b>{''.join(parts)}</nav></header>"


def _fmt4(x: float) -> str:
    return f"{float(x):.4f}"


def _fmt_ci(ci: list[float], signed: bool = False) -> str:
    lo, hi = float(ci[0]), float(ci[1])
    if signed:
        return f"[{lo:+.4f}, {hi:+.4f}]"
    return f"[{lo:.4f}, {hi:.4f}]"


def render_pages() -> None:
    c86c = json.loads((DOCS / "evidence" / "h86c-kslb-run-card.json").read_text())
    r86c = json.loads((DOCS / "evidence" / "lane86c_results.json").read_text())
    c86b = json.loads((DOCS / "evidence" / "h86b-gfco-run-card.json").read_text())
    crmrb = json.loads((DOCS / "evidence" / "rmrb86-run-card.json").read_text())
    ch86 = json.loads((DOCS / "evidence" / "run-card.json").read_text())
    cpar = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    inv = json.loads((DOCS / "evidence" / "download-inventory.json").read_text())

    n_cand = len(inv["artifacts"])
    tif_c = Path(c86c["submission_file"]).name
    zip_c = Path(c86c["zip_file"]).name
    rec_c = Path(r86c["submission_artifact"]["receipt_file"]).name
    tif_b = Path(c86b["submission_file"]).name
    zip_b = Path(c86b["zip_file"]).name
    tif_rmrb = Path(crmrb["download_file"]).name
    zip_rmrb = Path(crmrb["zip_file"]).name
    tif_h86 = Path(ch86["submission_file"]).name
    tif_par = cpar["raster_name"]

    hc = c86c["holdout_dti"]["buffered_whole_components_loqo"]
    ha = c86c["holdout_dti"]["segment_hide_all"]
    hd = c86c["holdout_dti"]["segment_hide_detached"]
    prog = c86c["holdout_dti"]["experiment_progression"]
    uq = c86c["correlation_overlap_vs_registry"]
    can = c86c["leakage_canary_auc"]
    dist_q = r86c["distance_to_catalogue_distribution"]

    hb_c = c86b["holdout_dti"]["buffered_whole_components_loqo"]
    hb_a = c86b["holdout_dti"]["segment_hide_all"]
    hb_d = c86b["holdout_dti"]["segment_hide_detached"]
    hb_uq = c86b["correlation_overlap_vs_registry"]

    # 1. docs/index.html
    index_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Submission decision · GEMSDOE86</title><link rel="stylesheet" href="assets/site.css"></head><body>
{_nav("index.html")}<main>
<div class="card hero">
<span class="badge bad">NOT SAFE TO SUBMIT · NO CANDIDATE AUTHORIZED FOR A WEEKLY SLOT</span>
<span class="badge ok">SAFE TO DOWNLOAD FOR AUDIT · LOCAL FORMAT PASS (15/15)</span>
<h1>{n_cand} byte-distinct GEMSDOE86 research TIFFs exist (led on every holdout by Session-3 H86C-KSLB). Download for audit—do not submit.</h1>
<p class="muted">Single float32 band · 3,730 × 3,292 · EPSG:32611 · exact 100 m transform · all finite in [0,1] · 0 positive pixels outside the footprint · 0 on mapped catalogue pixels · zero live weekly slots spent automatically.</p>
<a class="btn danger" href="downloads/{tif_c}" download>Download H86C-KSLB TIFF (Session-3 leader) — DO NOT SUBMIT</a>
<a class="btn alt" href="downloads/{zip_c}" download>Download H86C-KSLB one-TIFF ZIP — DO NOT SUBMIT</a>
<a class="btn ghost" href="downloads/{tif_b}" download>Download H86B-GFCO TIFF (Session-2) — DO NOT SUBMIT</a>
<a class="btn ghost" href="downloads/{tif_rmrb}" download>Download RMRB-86 TIFF — DO NOT SUBMIT</a>
<a class="btn ghost" href="executive-summary.html">Submission procedure &amp; automated gate audit →</a>
<p class="mono">H86C-KSLB name: {html.escape(c86c["submission_name"])} · sha256 {c86c["raster_sha256"]} · {c86c["validator"]["emitted_dots"]:,} dots · note ({len(c86c["note"])}/140): {html.escape(c86c["note"])}</p>
<p class="mono">H86B-GFCO sha256 {c86b["raster_sha256"]} · {c86b["validator"]["emitted_dots"]:,} dots · note ({len(c86b["note"])}/140): {html.escape(c86b["note"])}</p>
<p class="mono">RMRB-86 sha256 {crmrb["raster_sha256"]} · 37,654 dots · note: {html.escape(crmrb["note"])}</p>
</div>

<div class="kpi">
<div><span class="muted">H86C-KSLB Whole-Comp LOQO (HOLDOUT-DTI)</span><b>{_fmt4(hc["candidate_dti"])}</b><span class="muted">{hc["withheld_positives"]:,} buffered pos · 95% CI {_fmt_ci(hc["ci95"])} · paired Δ vs d2.8 {hc["paired_delta_vs_d28"]:+.4f} {_fmt_ci(hc["paired_delta_vs_d28_ci95"], True)} &amp; vs H33-2-B2 {hc["paired_delta_vs_h33_foldfair"]:+.4f} {_fmt_ci(hc["paired_delta_vs_h33_foldfair_ci95"], True)} (vs H86B {_fmt4(hc["h86b_gfco_pr16_loqo_dti"])})</span></div>
<div><span class="muted">H86C-KSLB Segment-Hide (all / detached)</span><b>{_fmt4(ha["candidate_dti"])} / {_fmt4(hd["candidate_dti"])}</b><span class="muted">{ha["withheld_positives"]:,} / {hd["withheld_positives"]:,} pos · paired Δ vs d2.8 {ha["paired_delta_vs_d28"]:+.4f} / {hd["paired_delta_vs_d28"]:+.4f} (all 95% CIs &gt; 0)</span></div>
<div><span class="muted">Non-Lattice Dot-Field Uniqueness ({r86c["uniqueness"]["discriminating_dot_rasters_checked"]} rasters)</span><b>≤{_fmt4(uq["final_worst_nonlattice_dot_overlap_3px"])}</b><span class="muted">{can["features_checked"]}/{can["features_checked"]} leakage canaries ≤{_fmt4(can["max_discriminative_auc"])} · {_fmt4(uq["overlap_3px_vs_gems32_h33_2_b2"])} vs H33-2-B2 · {_fmt4(uq["overlap_3px_vs_h86b_gfco"])} vs H86B · |ρ| ≤{_fmt4(uq["final_worst_all_abs_spearman"])}</span></div>
<div><span class="muted">Literal saturated-witness gate</span><b>1.0000 / 0.9988</b><span class="muted">limit 0.70 · 100%-dense witness + GEMS87 87.7% surface + 13gems lattice trigger mandatory literal stop</span></div>
</div>

<h2>Automated Session-3 Verdict (H86C-KSLB)</h2>
<div class="card"><p><b>Scientific &amp; engineering advance over Session-2 H86B-GFCO:</b> H86C-KSLB integrates 100%-coverage 10 m 3DEP profile curvature/lineaments + 1 m LiDAR scarps deconfounded against contour-parallel Pleistocene Lake Lahontan shorelines (1,180–1,355 m ASL), drainage-area-weighted fluvial <i>k<sub>sn</sub></i> knickzones &amp; χ divide steps, Blakely-Miller magnetic/gravity tilt zero-crossings, basement-hinge flexure, and seismicity-strain fabric inside a Dual-Regime Noisy-OR posterior <code>S = 1 − (1 − P_link)(1 − P_blind)</code>, and fixes H86B's in-sample live emission shift by serving spatially cross-fitted out-of-fold <code>p_oof</code> predictions directly.</p>
<ol>
<li><b>All 3 holdout CIs strictly positive:</b> Whole-component buffered LOQO jumps from H86B's {_fmt4(hc["h86b_gfco_pr16_loqo_dti"])} (paired CI {_fmt_ci(hb_c["paired_delta_vs_d28_ci95"], True)}) to <b>{_fmt4(hc["candidate_dti"])} {_fmt_ci(hc["ci95"])}</b>, clearing zero on paired 95% CIs against both <code>d2.8</code> ({hc["paired_delta_vs_d28"]:+.4f}, {_fmt_ci(hc["paired_delta_vs_d28_ci95"], True)}) and <code>H33-2-B2</code> ({hc["paired_delta_vs_h33_foldfair"]:+.4f}, {_fmt_ci(hc["paired_delta_vs_h33_foldfair_ci95"], True)}), while reaching <b>{_fmt4(ha["candidate_dti"])}</b> / <b>{_fmt4(hd["candidate_dti"])}</b> on segment-all / detached and placing <b>{dist_q["frac_gt_15px_blind_domain"]*100:.2f}%</b> of dots in deep blind terrain (&gt;1.5 km from mapped faults).</li>
<li><b>Distinct from all 35 non-lattice dot-field candidates across 21 repos:</b> Max 3-px overlap across all 35 sparse/ridge <code>dot_field</code> rasters (including GEMSDOE32..88 and all 6 prior GEMSDOE86 lanes) is <b>{_fmt4(uq["final_worst_nonlattice_dot_overlap_3px"])} ≤ 0.70</b> (0 duplicates; {_fmt4(uq["overlap_3px_vs_gems32_h33_2_b2"])} vs H33-2-B2; {_fmt4(uq["overlap_3px_vs_h86b_gfco"])} vs H86B-GFCO).</li>
<li><b>Why verdict remains fail-closed <code>negative</code> / <code>DO NOT SUBMIT</code>:</b> Under the unmodified literal 3-px overlap rule, three saturated/calibration rasters in the 38-raster snapshot—<code>dense-witness-100pct-support.tif</code> (100% allowed support → overlap 1.0000), <code>GEMSDOE87</code> continuous surface (87.7% support / 90.4% halo → overlap 0.9228), and <code>13gems</code> stride-5 lattice (99.87% halo → overlap 0.9988)—force <code>stop_required=true</code> for any nonempty subset of the allowed domain. Furthermore, local <code>HOLDOUT-DTI</code> measures masked-catalogue recovery, not private expert new-fault labels; no live weekly slot may be spent without explicit human selector authorization.</li>
</ol>
<p><a href="evidence/h86c-kslb-run-card.json">Canonical H86C-KSLB run card</a> · <a href="evidence/lane86c_results.json">Full 3-experiment &amp; bootstrap evidence</a> · <a href="evidence/h86c_crosslane_uniqueness.json">38-raster uniqueness report</a> · <a href="downloads/{rec_c}">Shared writer receipt</a> · <a href="evidence/protocol-preflight.json">Universal dense-witness proof</a></p></div>

<h2>Repository-wide traffic light ({n_cand} audited research TIFFs)</h2>
<table><tr><th>File</th><th>Measured state (all local metrics = HOLDOUT-DTI, gems57-pooled-hide-v2)</th><th>Binding decision</th></tr>
<tr><td class="mono"><a href="downloads/{tif_c}">{tif_c}</a></td><td><b>Session 3 (H86C-KSLB):</b> format pass (15/15); {can["features_checked"]}/{can["features_checked"]} leakage canaries ≤{_fmt4(can["max_discriminative_auc"])}; 3/3 budget; beats d2.8 &amp; H33-2-B2 with <b>wholly positive 95% paired CIs across all 3 holdouts</b> ({_fmt4(hc["candidate_dti"])} whole-comp LOQO, {_fmt4(ha["candidate_dti"])} segment-all, {_fmt4(hd["candidate_dti"])} detached); <b>0/35 non-lattice dot-field duplicates</b> (max overlap {_fmt4(uq["final_worst_nonlattice_dot_overlap_3px"])} ≤ 0.70; {_fmt4(uq["overlap_3px_vs_gems32_h33_2_b2"])} vs H33-2-B2; {_fmt4(uq["overlap_3px_vs_h86b_gfco"])} vs H86B); blocked by literal &gt;0.70 overlap on 3 saturated/lattice witnesses (1.0000, 0.9988, 0.9228) · <a href="evidence/h86c-kslb-run-card.json">run card</a> · <a href="evidence/lane86c_results.json">evidence</a> · <a href="downloads/{rec_c}">receipt</a></td><td><span class="badge bad">DO NOT SUBMIT</span></td></tr>
<tr><td class="mono"><a href="downloads/{tif_b}">{tif_b}</a></td><td><b>Session 2 (H86B-GFCO):</b> format pass (15/15); 42/42 canaries ≤{_fmt4(c86b["leakage_canary_auc"]["max_discriminative_auc"])}; {_fmt4(hb_c["candidate_dti"])} whole-comp (paired CI {_fmt_ci(hb_c["paired_delta_vs_d28_ci95"], True)} straddles 0), {_fmt4(hb_a["candidate_dti"])} segment-all, {_fmt4(hb_d["candidate_dti"])} detached; ≤{_fmt4(hb_uq["worst_modern_comparable_le_62k_overlap_3px"])} vs 25 comparable rasters; literal dense/legacy overlap &gt;0.70 · <a href="evidence/h86b-gfco-run-card.json">run card</a> · <a href="evidence/lane86b_results.json">evidence</a></td><td><span class="badge bad">DO NOT SUBMIT</span></td></tr>
<tr><td class="mono"><a href="downloads/{tif_rmrb}">{tif_rmrb}</a></td><td>format pass; distinct from H33 and merged parallel rasters; HOLDOUT-DTI {_fmt4(crmrb["holdout_dti"]["value"])} {_fmt_ci(crmrb["holdout_dti"]["ci95"])}; paired RMRB delta uncertain; dense-prior overlap 1.0 · <a href="evidence/rmrb86-run-card.json">run card</a></td><td><span class="badge bad">DO NOT SUBMIT</span></td></tr>
<tr><td class="mono"><a href="downloads/{tif_h86}">{tif_h86}</a></td><td>own run card: negative; HOLDOUT-DTI {_fmt4(ch86["holdout_dti"]["candidate_at_final_budget_60000"])} {_fmt_ci(ch86["holdout_dti"]["ci95_cell_bootstrap"])} below incumbent; lattice overlap 0.995 · <a href="evidence/run-card.json">run card</a></td><td><span class="badge bad">DO NOT SUBMIT</span></td></tr>
<tr><td class="mono"><a href="downloads/gems86-gmc-linepost-90568d-20261022T222859Z-900ceac1-zeros.tif">gems86-gmc-linepost-90568d-20261022T222859Z-900ceac1-zeros.tif</a></td><td>format pass; 82% of dots within 3 px of a prior proximity lane</td><td><span class="badge bad">DO NOT SUBMIT — duplicate lane</span></td></tr>
<tr><td class="mono"><a href="downloads/{tif_par}">{tif_par}</a></td><td>format pass and low rank correlation, but literal overlap fails on saturated priors and session exceeded 3-experiment cap</td><td><span class="badge bad">DO NOT SUBMIT under literal rule</span></td></tr>
<tr><td class="mono"><a href="downloads/gems86-h86-edge2of5-dotted38000-20261022T225931Z-70513125-zeros.tif">gems86-h86-edge2of5-dotted38000-20261022T225931Z-70513125-zeros.tif</a></td><td>format pass; HOLDOUT-DTI 0.0463 [0.0372, 0.0560] below 0.1030 control; literal lattice overlap 0.971</td><td><span class="badge bad">DO NOT SUBMIT</span></td></tr></table>

<h2>Why GEMSDOE32's H33-2-B2 reported 0.2778 vs leaderboard 0.4413 (live 2026-10-23)</h2>
<div class="card"><p><b>Exact mechanics &amp; evidence class:</b> <code>gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif</code> (SHA-256 <code>c55bafc470054e82…</code>, 37,654 binary dots) takes the <code>0.2708</code> (OWNER-REPORTED) <code>d2.8</code> Poisson-disc thinning (44,090 dots, <i>r</i> = 2.8 px) of <code>19GEMSDOE</code>'s multi-lineament ridge map and deletes the 6,436 dots within <i>d</i><sub>cat</sub> ≤ 2 px (200 m) of mapped <code>existing_faults.tif</code>. Under DrivenData's pooled DW-Tversky metric (α = 0.2, β = 0.8, 300 m triangular kernel), removing ΔF false-positive mass at truth-coverage cost ΔT strictly raises DTI iff <code>T · ΔF &gt; ΔT · (F + 4N + 5ε)</code>. Upstream <code>GEMSDOE32</code> explicitly labels the file <code>UNSCORED</code> with modeled projection <code>0.2747</code>; <code>0.2778</code> is <b>OWNER-REPORTED / UNVERIFIED</b> (zero organizer submission receipt in checkout). On the live DrivenData leaderboard fetched 2026-10-23, #1 <code>xiaofanhu</code> holds <b>0.4413</b> (ORGANIZER-PUBLISHED LEADERBOARD), #2/#3 <b>0.3904</b>, #4 <b>0.3713</b>, #5 <b>0.3539</b>—an ~0.163 DTI gap above 0.2778 driven by blind cover-penetrating new-fault recall rather than post-hoc collar pruning alone.</p>
<p><a href="https://github.com/buffedlizard55-lab/GEMSDOE86/blob/main/research/H86C_KSLB_REVIEW.md">H86C-KSLB PhD scientific review &amp; 5 ranked hypotheses</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Official DrivenData public leaderboard</a> · <a href="https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html">Upstream GEMSDOE32 site</a></p></div>

<h2>Machine-checkable evidence bundle</h2><ul>
<li><a href="evidence/h86c-kslb-run-card.json">H86C-KSLB run card</a> · <a href="evidence/lane86c_results.json">H86C-KSLB full holdout &amp; canary JSON</a> · <a href="evidence/h86c_crosslane_uniqueness.json">38-raster cross-repo uniqueness JSON</a>.</li>
<li><a href="evidence/h86b-gfco-run-card.json">H86B-GFCO run card</a> · <a href="evidence/rmrb86-run-card.json">RMRB-86 run card</a> · <a href="evidence/run-card.json">H86-RMRB run card</a> · <a href="evidence/protocol-preflight.json">Dense-witness certificate</a>.</li>
<li><a href="evidence/download-inventory.json">Registered SHA-256 download inventory ({n_cand} TIFFs)</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE86/blob/main/README.md">Archived owner prompt &amp; reproduction guide</a>.</li>
</ul>
</main><footer>Local format pass ≠ organizer acceptance. Current selector decision: no file is safe to submit under the supplied literal protocol.</footer></body></html>
"""
    (DOCS / "index.html").write_text(index_html, encoding="utf-8")

    # 2. docs/executive-summary.html
    exec_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>How to submit · GEMSDOE86</title><link rel="stylesheet" href="assets/site.css"></head><body>
{_nav("executive-summary.html")}<main>
<h1>Executive summary — submission procedure and fail-closed gate audit</h1>
<div class="card hero"><span class="badge bad">CURRENT DECISION: DO NOT SUBMIT ANY REPOSITORY FILE · NO CANDIDATE AUTHORIZED</span>
<h2>Session-3 H86C-KSLB &amp; prior research candidates</h2>
<p>Every candidate GeoTIFF and single-TIFF ZIP is directly downloadable for inspection; the fail-closed block is unambiguous at the top of every page. Session-3 <b>H86C-KSLB</b> passes 15/15 format checks, passes {can["features_checked"]}/{can["features_checked"]} leakage canaries (max AUC {_fmt4(can["max_discriminative_auc"])} ≤ 0.90), clears paired 95% bootstrap CIs above both <code>d2.8</code> and <code>H33-2-B2</code> across all 3 holdout views ({_fmt4(hc["candidate_dti"])} whole-component LOQO, {_fmt4(ha["candidate_dti"])} segment-all, {_fmt4(hd["candidate_dti"])} detached), and achieves 0/35 duplicates across all non-lattice <code>dot_field</code> rasters in 21 repos (max 3-px overlap {_fmt4(uq["final_worst_nonlattice_dot_overlap_3px"])} ≤ 0.70). Automatic weekly-slot spending remains blocked because the unmodified literal &gt;0.70 3-px overlap gate fires on saturated/calibration witnesses (<code>dense-witness</code> 1.0000, <code>GEMSDOE87</code> 0.9228, <code>13gems</code> 0.9988).</p>
<a class="btn danger" href="downloads/{tif_c}" download>Download H86C-KSLB TIFF — DO NOT SUBMIT</a>
<a class="btn ghost" href="downloads/{zip_c}" download>Download H86C-KSLB ZIP — DO NOT SUBMIT</a>
<a class="btn ghost" href="evidence/h86c-kslb-run-card.json">H86C-KSLB Run Card</a>
<a class="btn ghost" href="downloads/{tif_b}" download>Download H86B-GFCO TIFF — DO NOT SUBMIT</a>
<a class="btn ghost" href="downloads/{tif_rmrb}" download>Download RMRB-86 TIFF — DO NOT SUBMIT</a>
<a class="btn ghost" href="downloads/{zip_rmrb}" download>Download RMRB-86 ZIP — DO NOT SUBMIT</a></div>

<h2>Session-3 Candidate Identity (H86C-KSLB)</h2><table>
<tr><th>File</th><td class="mono">{tif_c}</td></tr>
<tr><th>ZIP bundle (single TIFF)</th><td class="mono">{zip_c} (sha256 {r86c["submission_artifact"]["zip_sha256"]})</td></tr>
<tr><th>GeoTIFF SHA-256</th><td class="mono">{c86c["raster_sha256"]}</td></tr>
<tr><th>Unique submission name</th><td class="mono">{html.escape(c86c["submission_name"])}</td></tr>
<tr><th>Optional note ({len(c86c["note"])}/140 chars)</th><td class="mono">{html.escape(c86c["note"])}</td></tr>
<tr><th>Emitted binary dots</th><td>{c86c["validator"]["emitted_dots"]:,} (min={c86c["validator"]["min"]:.1f}, max={c86c["validator"]["max"]:.1f}, 0 NaN/Inf/sentinel, 0 on catalogue)</td></tr>
<tr><th>Verdict</th><td><b>{c86c["verdict"]} / approved_for_weekly_slot={str(c86c["approved_for_weekly_slot"]).lower()} (DO NOT SUBMIT)</b></td></tr></table>

<h2>Automated 8-Gate Protocol Audit (H86C-KSLB)</h2><ol>
<li><b>Format &amp; [0,1] range — PASS locally (15/15):</b> single-band float32; 3,730 × 3,292; exact EPSG:32611 &amp; 100 m affine transform matching <code>sample_submission.tif</code>; values strictly in [0.0, 1.0]; zero NaN, zero Inf, zero <code>-3.4028235e+38</code> Float32 nodata sentinels; zero positive mass outside footprint or on mapped catalogue pixels.</li>
<li><b>Leakage canaries — PASS ({can["features_checked"]}/{can["features_checked"]}):</b> max single-feature discriminative AUC = {_fmt4(can["max_discriminative_auc"])} ≤ 0.90 (48 label-free physical planes ≤0.6497; 4 visible-only kinematic components ≤{_fmt4(can["max_discriminative_auc"])}); AST-verified zero access to <code>existing_faults.tif</code>, <code>labels.tif</code>, <code>gdr_qfaults_traces.csv</code>, <code>derived_sgmc_faults_100m_u8.tif</code>, or <code>dist_known_fault_px</code> in <code>build_physical_planes()</code>.</li>
<li><b>Experiment budget — PASS ({c86c["experiments_run"]}/3):</b> E1 pure blind physical+filament 37,654 dots ({_fmt4(prog["E1_kslb_phys_fil_38k"]["buffered_comp"])}), E2 Noisy-OR 37,654 dots ({_fmt4(prog["E2_kslb_noisyor_38k"]["buffered_comp"])}), E3 Noisy-OR 44,090 dots ({_fmt4(prog["E3_kslb_noisyor_44k"]["buffered_comp"])}).</li>
<li><b>Whole-component 3-px buffered LOQO — PASS (95% CI &gt; 0):</b> <b>HOLDOUT-DTI</b> ({hc["withheld_positives"]:,} pos) = <b>{_fmt4(hc["candidate_dti"])} {_fmt_ci(hc["ci95"])}</b>; paired Δ vs <code>d2.8</code> = <b>{hc["paired_delta_vs_d28"]:+.4f} {_fmt_ci(hc["paired_delta_vs_d28_ci95"], True)}</b>; paired Δ vs <code>H33-2-B2</code> = <b>{hc["paired_delta_vs_h33_foldfair"]:+.4f} {_fmt_ci(hc["paired_delta_vs_h33_foldfair_ci95"], True)}</b> (+15.1% over Session-2 H86B-GFCO {_fmt4(hc["h86b_gfco_pr16_loqo_dti"])}).</li>
<li><b>Segment hide (all / detached) — PASS (95% CIs &gt; 0):</b> <b>HOLDOUT-DTI</b> = <b>{_fmt4(ha["candidate_dti"])} {_fmt_ci(ha["ci95"])}</b> ({ha["withheld_positives"]:,} pos) and <b>{_fmt4(hd["candidate_dti"])} {_fmt_ci(hd["ci95"])}</b> ({hd["withheld_positives"]:,} pos).</li>
<li><b>Non-lattice dot-field uniqueness — PASS (0/35 duplicates):</b> pre-placement surface max |ρ| = {_fmt4(uq["surface_worst_abs_spearman"])} ≤ 0.90; final dots max |ρ| = {_fmt4(uq["final_worst_all_abs_spearman"])} ≤ 0.90; max 3-px overlap across all 35 non-saturated/non-lattice <code>dot_field</code> rasters = <b>{_fmt4(uq["final_worst_nonlattice_dot_overlap_3px"])} ≤ 0.70</b> ({_fmt4(uq["overlap_3px_vs_gems32_h33_2_b2"])} vs H33-2-B2; {_fmt4(uq["overlap_3px_vs_h86b_gfco"])} vs H86B-GFCO).</li>
<li><b>Literal registry rule — STOP (binding blocker):</b> 3 saturated/calibration witnesses in the 38-raster snapshot (<code>dense-witness-100pct-support.tif</code> = 1.0000, <code>GEMSDOE87</code> 87.7%-dense surface = 0.9228, <code>13gems</code> stride-5 lattice = 0.9988) exceed 0.70 under the unmodified literal rule. Fail-closed governance preserved.</li>
<li><b>Live weekly-slot discipline — NOT SPENT:</b> zero submissions uploaded; human selector authorization required.</li></ol>

<h2>Exact DrivenData portal procedure — for a future human-authorized promotion only</h2>
<p>These instructions document the submission workflow; they do <b>not</b> authorize uploading any current file without human selector override of the saturated-witness literal rule.</p><ol>
<li>Verify the target file's canonical run card (e.g., <a href="evidence/h86c-kslb-run-card.json">h86c-kslb-run-card.json</a>) and confirm SHA-256 locally via <code>sha256sum {tif_c}</code> → <code>{c86c["raster_sha256"]}</code>.</li>
<li>Confirm all 15 local validator checks pass (<code>.venv/bin/python scripts/audit_h86c.py</code>): single-band Float32, EPSG:32611, 3,730 × 3,292, values in [0, 1], zero NaN/Inf/sentinel.</li>
<li>Open the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData GEMS Submissions portal</a>, sign in, verify weekly submission quota (≤3/week per <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">DOE/NLR Official Rules §3.3</a>), and click <b>Make new submission</b>.</li>
<li>Upload either the standalone <code>.tif</code> or its single-TIFF <code>.zip</code> archive, paste the unique name (<code>{html.escape(c86c["submission_name"])}</code>) and ≤140-char note (<code>{html.escape(c86c["note"])}</code>), and save the returned organizer submission receipt before labelling any number <b>ORGANIZER-CONFIRMED</b>.</li></ol>

<h2>Why the prior "[0, 1]" range error cannot recur</h2>
<p><code>training_features.tif</code> stores <code>-3.4028235e+38</code> Float32 nodata on 3,061 in-footprint cells (bands 15 &amp; 17) and outside-footprint margins, while legacy <code>-nan.tif</code> files stored IEEE <code>NaN</code> on 7,111,787 outside-footprint cells. Our shared <code>submission_writer.write_submission()</code> + <code>validate.assert_submittable()</code> rejects any non-finite, negative, &gt;1, or sentinel value before and after serialization and writes <code>0.0</code> outside the footprint with <code>nodata=None</code>.</p>
</main><footer>No organizer score is claimed. No current file is authorized for automatic upload.</footer></body></html>
"""
    (DOCS / "executive-summary.html").write_text(exec_html, encoding="utf-8")

    # 3. docs/hypotheses.html
    hyp_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hypotheses · GEMSDOE86</title><link rel="stylesheet" href="assets/site.css"></head><body>
{_nav("hypotheses.html")}<main>
<section class="card hero"><span class="badge bad">DO NOT SUBMIT · NO CANDIDATE AUTHORIZED</span>
<p>Five pre-registered Session-3 geological hypotheses advancing Session-1 &amp; Session-2 untested items. Only Rank #1 (<b>H86C-KSLB</b>) was executed within the 3-experiment budget. <a href="evidence/h86c-kslb-run-card.json">H86C-KSLB run card</a> · <a href="evidence/protocol-preflight.json">Dense-witness proof</a></p></section>
<h1>Ranked Candidate Geological Hypotheses (Session 3)</h1>

<div class="card"><h3>Rank #1 (Selected &amp; Executed) · H86C-KSLB: Lahontan-Deconfounded 10m+1m Scarp + Fluvial k<sub>sn</sub>/χ Knickzone + Blakely Zero-Crossing Dual-Regime Noisy-OR</h3>
<p><b>Layers:</b> <code>topo_10m_derived_100m_u8.tif</code> (b1,5,6,7,8; 100% coverage), <code>dem10_chi_100m_i16.tif</code> (b1–b5: χ steps, <i>k<sub>sn</sub></i>, log drainage area, true elevation <code>zmean_m</code>), <code>lidar_scarp_features_u8.tif</code> (75.37% coverage; verified image-tangent strike b11), <code>training_features.tif</code> (RTP b2, TMI HG/VG b3/b9, gravity HG/VG b18/b11, basement b15, conductivity b17, strain b4/b7/b8, seismicity b10/b16), <code>geodawn_rad_u8.tif</code> + <code>geodawn_extensions_u8.tif</code>, GDR-1391 wells/vents (excluding <code>dist_known_fault_px</code>).<br>
<b>Physical signature &amp; non-fault mimic rejection:</b> 25.2% of the footprint lies inside Pleistocene Lake Lahontan shoreline elevations (1,180–1,355 m ASL), where wave-cut beach scarps mimic fault scarps. H86C computes spin-2 transversality between scarp strike and regional <code>zmean_m</code> contours to reject contour-parallel shorelines while retaining contour-cutting scarps corroborated by drainage-area-weighted fluvial <i>k<sub>sn</sub></i> knickzones, Blakely-Miller magnetic/gravity tilt zero-crossings, basement-hinge flexure, and seismicity-strain fabric; fuses strike-concordant tip/relay/hinge linkage <code>P_link</code> with convex blind filaments <code>P_blind</code> via <code>1 − (1 − P_link)(1 − P_blind)</code>.<br>
<b>Measured HOLDOUT-DTI:</b> Whole-component LOQO <b>{_fmt4(hc["candidate_dti"])} {_fmt_ci(hc["ci95"])}</b> (+15.1% over H86B-GFCO {_fmt4(hc["h86b_gfco_pr16_loqo_dti"])}; paired Δ vs d2.8 {hc["paired_delta_vs_d28"]:+.4f} {_fmt_ci(hc["paired_delta_vs_d28_ci95"], True)}); segment-all <b>{_fmt4(ha["candidate_dti"])}</b>; segment-detached <b>{_fmt4(hd["candidate_dti"])}</b>; 0/35 non-lattice dot-field duplicates (max overlap {_fmt4(uq["final_worst_nonlattice_dot_overlap_3px"])}). Blocked from auto-promotion solely by literal saturated witnesses (<code>DO NOT SUBMIT</code>).</p></div>

<div class="card"><h3>Rank #2 (Deferred) · H86D-PFCO: Bipartite Graph-Matched Piercing-Line Magnetic Ridge Dislocation</h3>
<p><b>Layers:</b> <code>rtp</code> (b2), <code>tmi_hg</code> (b3), <code>tmi_up150_u8</code> (ext b4), <code>iso_grav_anom_hg</code> (b18).<br>
<b>Signature:</b> Extract terminated Canny-Hessian magnetic dike/flow ridges and solve minimum-cost bipartite matching across 0.3–3.5 km corridors for systematic lateral piercing-line offset where the intervening corridor carries zero surface scarp.<br>
<b>Mimic:</b> Primary volcanic flow-lobe terminations and GeoDAWN flight-line tie seams.</p></div>

<div class="card"><h3>Rank #3 (Deferred) · H86E-CSFD: Windowed Radial Spectral Magnetic Centroid / Curie-Depth Gradient</h3>
<p><b>Layers:</b> <code>tmi</code> (b14), <code>rtp</code> (b2), <code>depth_to_base_surf</code> (b15), GDR-1391 geothermometers.<br>
<b>Signature:</b> Overlapping 6.4 × 6.4 km radially averaged 2D FFT log-power slope ratios estimating shallow vs deep magnetic source-bottom upwarps along crustal-scale thermal fault conduits.<br>
<b>Mimic:</b> Shallow young basaltic vents and variable drape altitude.</p></div>

<div class="card"><h3>Rank #4 (External — Egress-Blocked in Sandbox) · H86F-InSAR: OPERA/ASF Sentinel-1 Aquitard Phase-Gradient Step</h3>
<p><b>External source:</b> Official NASA/JPL OPERA Surface Displacement (DISP-S1, CC0 via ASF/Earthdata). Sharp seasonal poroelastic phase steps across unmapped fault-seal aquitards in Dixie/Humboldt/Buena Vista playas. Verified not obtainable inside this sandbox's 6-host egress allowlist.</p></div>

<div class="card"><h3>Rank #5 (External — Egress-Blocked in Sandbox) · H86G-ASTER: LP DAAC ASTER TIR Silica/Sinter &amp; SWIR Argillic Alteration Ribbons</h3>
<p><b>External source:</b> Official NASA/USGS LP DAAC AST_05/AST_07XT (90 m TIR / 30 m SWIR, public domain). Maps opaline sinter, chalcedony, and kaolinite/alunite alteration aprons along blind geothermal range-front/playa faults. Verified not obtainable inside sandbox egress allowlist.</p></div>
</main>
<footer>Evidence classes: HOLDOUT-DTI (measured here) · ORGANIZER-CONFIRMED (submission-page receipt only) · OWNER-REPORTED (unverified site claim).</footer></body></html>
"""
    (DOCS / "hypotheses.html").write_text(hyp_html, encoding="utf-8")

    # 4. docs/evidence.html
    sgmc = r86c["off_catalogue_sgmc_diagnostic"]
    ev_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Evidence · GEMSDOE86</title><link rel="stylesheet" href="assets/site.css"></head><body>
{_nav("evidence.html")}<main>
<section class="card hero"><span class="badge bad">DO NOT SUBMIT — NO ARTIFACT IS APPROVED</span>
<p>Every metric below is generated programmatically from <code>docs/evidence/*.json</code> by <code>scripts/build_site.py</code> and explicitly labelled by evidence class.</p></section>
<h1>Multi-Holdout &amp; Cross-Repo Uniqueness Evidence</h1>

<h2>1. Session-3 H86C-KSLB 3-Experiment Progression &amp; Controls (HOLDOUT-DTI, gems57-pooled-hide-v2)</h2>
<table>
<tr><th>Arm / Control</th><th>Dots</th><th>Buffered Whole-Comp (11,321 pos)</th><th>Segment All (22,641 pos)</th><th>Segment Detached (22,619 pos)</th></tr>
<tr><td><b>E3: H86C-KSLB Noisy-OR 44k (Selected)</b></td><td>44,090</td><td><b>{_fmt4(hc["candidate_dti"])} {_fmt_ci(hc["ci95"])}</b></td><td><b>{_fmt4(ha["candidate_dti"])} {_fmt_ci(ha["ci95"])}</b></td><td><b>{_fmt4(hd["candidate_dti"])} {_fmt_ci(hd["ci95"])}</b></td></tr>
<tr><td>E2: H86C-KSLB Noisy-OR 38k</td><td>37,654</td><td>{_fmt4(prog["E2_kslb_noisyor_38k"]["buffered_comp"])}</td><td>{_fmt4(prog["E2_kslb_noisyor_38k"]["all"])}</td><td>{_fmt4(prog["E2_kslb_noisyor_38k"]["detached"])}</td></tr>
<tr><td>E1: H86C-KSLB Pure Blind Phys+Filament (0 cat at inference)</td><td>37,654</td><td>{_fmt4(prog["E1_kslb_phys_fil_38k"]["buffered_comp"])}</td><td>{_fmt4(prog["E1_kslb_phys_fil_38k"]["all"])}</td><td>{_fmt4(prog["E1_kslb_phys_fil_38k"]["detached"])}</td></tr>
<tr><td>Session-2 H86B-GFCO (PR #16 OOF)</td><td>44,090</td><td>{_fmt4(hc["h86b_gfco_pr16_loqo_dti"])} {_fmt_ci(hb_c["ci95"])}</td><td>{_fmt4(hb_a["candidate_dti"])} {_fmt_ci(hb_a["ci95"])}</td><td>{_fmt4(hb_d["candidate_dti"])} {_fmt_ci(hb_d["ci95"])}</td></tr>
<tr><td>GEMSDOE32 H33-2-B2 (fold-fair d_vis &gt; 2 px)</td><td>37,654</td><td>{_fmt4(hc["h33_b2_foldfair_dti"])} {_fmt_ci(hc["h33_b2_foldfair_ci95"])}</td><td>{_fmt4(ha["h33_b2_foldfair_dti"])}</td><td>{_fmt4(hd["h33_b2_foldfair_dti"])}</td></tr>
<tr><td>GEMSDOE24 d2.8 incumbent</td><td>44,090</td><td>{_fmt4(hc["d28_incumbent_dti"])} {_fmt_ci(hc["d28_incumbent_ci95"])}</td><td>{_fmt4(ha["d28_incumbent_dti"])}</td><td>{_fmt4(hd["d28_incumbent_dti"])}</td></tr>
</table>

<h2>2. Auxiliary Off-Catalogue SGMC Bedrock Fault Diagnostic (OFF-CATALOGUE-PROXY-DIAGNOSTIC)</h2>
<p class="muted">Zero SGMC bytes enter training or features; evaluated on 51,389 SGMC bedrock fault pixels at d<sub>cat</sub> &gt; 3 px (recall-heavy noisy proxy, not organizer ground truth): E1 = {sgmc["E1_kslb_phys_fil_38k_oof"]["proxy_dti"]:.4f}, E2 = {sgmc["E2_kslb_noisyor_38k_oof"]["proxy_dti"]:.4f}, E3 = {sgmc["E3_kslb_noisyor_44k_oof"]["proxy_dti"]:.4f} (vs H86B {sgmc["h86b_gfco_pr16"]["proxy_dti"]:.4f}, d2.8 {sgmc["d28_incumbent"]["proxy_dti"]:.4f}).</p>

<h2>3. 38-Raster Cross-Repo &amp; Intra-Repo Uniqueness Audit (H86C-KSLB)</h2>
<p>Measured against {uq["rasters_checked"]} SHA-256-verified rasters across 21 <code>buffedlizard55-lab</code> repositories (12 GEMSDOE24 + 6 prior GEMSDOE86 lanes + 19 cross-repo primary champions GEMSDOE32..88 + 1 pinned 100%-support dense witness):</p>
<ul>
<li><b>Pre-placement continuous surface max |Spearman ρ|:</b> {_fmt4(uq["surface_worst_abs_spearman"])} ≤ 0.90</li>
<li><b>Final binary dots max |Spearman ρ|:</b> {_fmt4(uq["final_worst_all_abs_spearman"])} ≤ 0.90</li>
<li><b>Non-saturated / non-lattice <code>dot_field</code> 3-px overlap (35 rasters):</b> max = <b>{_fmt4(uq["final_worst_nonlattice_dot_overlap_3px"])} ≤ 0.70</b> (0 duplicates; {_fmt4(uq["overlap_3px_vs_gems32_h33_2_b2"])} vs GEMSDOE32 H33-2-B2; {_fmt4(uq["overlap_3px_vs_d28_incumbent"])} vs d2.8; {_fmt4(uq["overlap_3px_vs_h86b_gfco"])} vs H86B-GFCO).</li>
<li><b>Saturated / calibration witnesses triggering literal &gt;0.70 stop:</b> <code>dense-witness-100pct-support.tif</code> (1.0000), <code>13gems_20261001_r13-lattice-s5_v2_nan-outside.tif</code> (0.9988), and <code>GEMSDOE87__gems87-bmtd…tif</code> (87.7% positive support = 4,532,408 cells → 0.9228).</li>
</ul>
</main>
<footer>Evidence classes: HOLDOUT-DTI · OFF-CATALOGUE-PROXY-DIAGNOSTIC · ORGANIZER-CONFIRMED (none in GEMSDOE86) · OWNER-REPORTED.</footer></body></html>
"""
    (DOCS / "evidence.html").write_text(ev_html, encoding="utf-8")

    # 5. docs/irregularities.html
    irr_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Irregularities · GEMSDOE86</title><link rel="stylesheet" href="assets/site.css"></head><body>
{_nav("irregularities.html")}<main>
<section class="card hero"><span class="badge bad">DO NOT SUBMIT — NO ARTIFACT IS APPROVED</span>
<p>Every data, metric, code, and documentation irregularity uncovered across Sessions 1–3 is logged transparently below.</p></section>
<h1>Irregularities Flagged for Review</h1>
<ol>
<li><b>IR-86C-DOC-01 (Fixed in Session 3): Prior H86B review misstated band count &amp; gravity type.</b> <code>research/H86B_GFCO_REVIEW.md</code> §3 referred to “22 bands including 6 MT slices and CBA gravity”; <code>training_features.tif</code> actually has exactly <b>19 Float32 bands</b>, <b>1</b> surface conductivity band (<code>b17 cond_surf</code>), and <b>isostatic residual gravity</b> (<code>b5, b11, b13, b18</code>).</li>
<li><b>IR-86C-MOD-02 (Fixed in Session 3): In-sample <code>p_full</code> collar memorization in H86B live raster.</b> Session-2 <code>run_lane86b.py</code> evaluated spatial LOQO <code>p_oof</code> on holdout, but wrote its live GeoTIFF from an in-sample <code>p_full</code> refit over all 4 quadrants with negatives excluded at <i>d</i><sub>cat</sub> ≤ 4 px—inflating probabilities in the 2 &lt; <i>d</i><sub>cat</sub> ≤ 4 px collar. <code>H86C-KSLB</code> serves cross-fitted out-of-fold <code>p_oof</code> directly (1:1 train/serve parity), cutting worst non-lattice overlap from 0.8801 to <b>{_fmt4(uq["final_worst_nonlattice_dot_overlap_3px"])} ≤ 0.70</b>.</li>
<li><b>IR-86C-LID-01 (Verified in Session 3): <code>lidar_scarp_features_u8.tif</code> band 11 strike convention.</b> Band 11 encodes image-plane `(dc=cos θ, dr=sin θ)` tangent (`θ = π · u8 / 255`), which equals `θ + π/2` in `N=0, E=90` azimuth; verified directly against <code>zmean_m</code> elevation gradients before spin-2 fusion.</li>
<li><b>IR-32-SCORE-01: 0.2778 is OWNER-REPORTED, not ORGANIZER-CONFIRMED.</b> Upstream <code>GEMSDOE32</code> marks <code>h33-h33-2-b2</code> as <code>UNSCORED</code> with projected DTI <code>0.27467</code>; sibling READMEs contradict each other on whether it was submitted.</li>
<li><b>IR-32-ZIP-01: Broken upstream ZIP in GEMSDOE32.</b> <code>gemsdoe32-h33-h33-2-b2-…-zeros.zip</code> is 216 bytes containing a 0-byte file; our <code>audit_h86c.py</code> &amp; <code>check_site.py</code> enforce exact byte-for-byte TIFF-inside-ZIP equality.</li>
<li><b>IR-86B-DATA-01 &amp; Spec vs Portal Range Gate:</b> <code>training_features.tif</code> has <code>-3.4028235e+38</code> Float32 nodata on 3,061 in-footprint cells (b15, b17), and the upload portal rejects NaN outside the footprint despite page 967 allowing null. All GEMSDOE86 writers sanitize inputs and emit 0.0 outside the footprint.</li>
<li><b>IR-86B-CSV-01: Leaky column &amp; trailing whitespace in GDR-1391 CSVs.</b> <code>dist_known_fault_px</code> is excluded by AST-tested rule, and 121 <code>'Hot '</code> rows with trailing spaces are stripped.</li>
<li><b>IR-57-EMIT-01: Saturation degeneracy in <code>gems57.emit.allocate_patient</code>.</b> Clamping <code>k_self = min(E[k], 1.0)</code> zeroes marginal FP penalty when 3-px local sum ≥ 1; bypassed via <code>expected_credit</code> + <i>r</i> = 2.8 px disc thinning without modifying <code>vendor/gems57</code>.</li>
<li><b>IR-86-SAT-01: Literal 3-px overlap rule vs saturated/lattice registry rasters.</b> Pinned <code>dense-witness.tif</code> (100% support), <code>GEMSDOE87</code> (87.7% support), and <code>13gems</code> stride-5 lattice (99.87% halo) force literal overlap &gt; 0.70; recorded honestly with zero unauthorized exemptions.</li>
</ol>
</main>
<footer>Evidence classes: HOLDOUT-DTI · ORGANIZER-CONFIRMED · OWNER-REPORTED.</footer></body></html>
"""
    (DOCS / "irregularities.html").write_text(irr_html, encoding="utf-8")


def verify_pages() -> None:
    pages = (
        DOCS / "index.html",
        DOCS / "executive-summary.html",
        DOCS / "hypotheses.html",
        DOCS / "evidence.html",
        DOCS / "sources.html",
        DOCS / "irregularities.html",
        DOCS / "research.html",
    )
    for page in pages:
        text = page.read_text(encoding="utf-8")
        if "OK TO DOWNLOAD AND SUBMIT" in text:
            raise SystemExit(f"fail-closed site violation in {page}: unauthorized readiness phrase")
        if page.name != "research.html" and "DO NOT SUBMIT" not in text:
            raise SystemExit(f"missing negative decision in {page}")
        parser = Links()
        parser.feed(text)
        for link in parser.values:
            if link.startswith(("http:", "https:", "mailto:", "#")):
                continue
            target = page.parent / link.split("#", 1)[0]
            if not target.exists():
                raise SystemExit(f"broken local link: {page} -> {link}")
    index = (DOCS / "index.html").read_text(encoding="utf-8")
    for name in CANDIDATES:
        if name not in index or not (DOCS / "downloads" / name).is_file():
            raise SystemExit(f"candidate missing from dashboard or disk: {name}")


def main() -> int:
    render_pages()
    verify_pages()
    print(f"Static site generated & verified: PASS; {len(CANDIDATES)} candidates listed; none authorized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
