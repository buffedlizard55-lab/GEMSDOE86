#!/usr/bin/env python3
"""Generate the Pages dashboard from byte-checked evidence, never from prose scores.

No model fitting, placement, historical-raster copying, slot selection or portal
submission occurs here. Every download stays explicitly negative. --check is
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
        result.append(f'''<article class="card artifact"><div class="section-head"><h3>{e(a['lane'])}</h3><span class="badge bad">{e(a['status'])}</span></div>
<p class="filename">{e(Path(a['file']).name)}</p>
<p class="muted">FORMAT-VALIDATION · {a['bytes']:,} bytes · {v['emitted_dots']:,} positive cells · {passed}/{check_count} local checks pass</p>
<div class="actions"><a class="btn" href="{e(link(a['file']))}" download>Download TIFF — audit only</a>
<a class="btn secondary" href="{e(link(a['zip_file']))}" download>One-TIFF ZIP — audit only</a>
<a class="text-link" href="{e(link(a['receipt_file']))}">Writer receipt</a></div>
<details><summary>File identity, short note &amp; validation</summary>
<dl><dt>SHA-256</dt><dd><code id="{ident}-sha">{e(a['sha256'])}</code> <button data-copy-target="{ident}-sha" type="button">Copy hash</button></dd>
<dt>Submission name (identity only, not approval)</dt><dd><code id="{ident}-name">{e(a['submission_name'])}</code> <button data-copy-target="{ident}-name" type="button">Copy name</button></dd>
<dt>Note ({a['note_chars']} characters; limit from project protocol)</dt><dd><code id="{ident}-note">{e(a['note'])}</code> <button data-copy-target="{ident}-note" type="button">Copy note</button></dd></dl>
<p><a href="evidence.html#{ident}">Automated checks and scoped historical holdout</a></p></details></article>''')
    return "\n".join(result)


def home(report: dict, fleet: dict, registry: dict, review: dict, plan_count: int = 4) -> str:
    n = report["artifact_count"]
    return page("Download decision", "index.html", f'''
<section class="hero"><p class="eyebrow">DOE GEMS Prize · fault-discovery research</p>
<span class="badge bad">NOT SAFE TO SUBMIT · NO CANDIDATE AUTHORIZED</span>
<h1>Download the research.<br><span class="subtle">Do not spend a submission slot.</span></h1>
<p class="lede">The downloadable GeoTIFFs pass automated local format checks, but the mandatory uniqueness rule blocks every nonempty candidate. A new hash is not a unique scientific submission.</p>
<p><span class="badge ok">SAFE TO DOWNLOAD FOR AUDIT</span> <strong>DO NOT SUBMIT</strong> any current file.</p>
<p class="muted">Latest automated remeasurement: <time>{e(review['registry_measured_utc'])}</time>. <a href="evidence/latest-review-run-card.json">Current negative run card</a> · <a href="submit.html">PR #60 SPT revocation notice (IR-86-SPT-02)</a> · <a href="{REPO}/blob/main/research/SESSION_20261024_REVIEW.md">Safety review and next steps</a>. Historical model results below were not rerun.</p>
<div class="actions"><a class="btn" href="#downloads">Open TIFF downloads ↓</a><a class="btn secondary" href="executive-summary.html">Why blocked &amp; how submission works →</a></div></section>
<div class="kpi"><div><span>Local format &amp; integrity</span><strong>{report['locally_valid_artifacts']} / {n}</strong><small>All serialized files re-read; names, notes, masks, SHA and ZIP payloads checked.</small></div>
<div><span>Submission-approved files</span><strong>None</strong><small>Every candidate remains negative. No selector or portal operation was run.</small></div>
<div><span>New experiments / slots used</span><strong>{report['experiments_run']} / {report['submission_slots_used']}</strong><small>This audit stopped before modeling or placement, as required.</small></div></div>
<section class="callout"><h2>Why a new submission cannot be cleared</h2><p>A hash-pinned historical registry raster (<code>17GEMSDOE</code>, <code>ab0a0a62...</code>) is positive at <strong>every allowed pixel</strong>. Under the unchanged literal rule, any nonempty dot set has forward overlap {report['witness_positive_support_allowed_fraction']:.0%}, above the {report['overlap_limit']:.0%} stop; moreover, a discrete binary stride-5 lattice witness (<code>13GEMSDOE</code>, <code>b4570b40...</code>, <code>206,895</code> dots) covers <code>99.8724%</code> of allowed pixels within 3 px, forcing <code>&gt;= 82.70%</code> overlap on any <code>37,654</code>-dot raster by pigeonhole. This is a rule-satisfiability failure, not evidence that every geological idea is identical.</p>
<p>All {len(registry['artifacts'])} inherited final TIFFs were independently rechecked against this witness, and PR #60's <code>SPT</code> candidate remains quarantined outside <code>docs/</code> after also measuring 100% witness overlap and coin-flip canary AUC (<code>0.4947</code>). No dense-prior exemption was applied. <a href="evidence/all-artifacts-registry.json">Measured negative proof</a> · <a href="evidence/latest-review-run-card.json">Current negative run card</a> · <a href="evidence/spt-run-card.json">Revoked SPT card</a> · <a href="evidence/session-20261023-run-card.json">Archived 2026-10-23 card</a>.</p></section>
<section id="downloads"><p class="eyebrow">Immediate downloads · historical research artifacts</p><h2>TIFF + single-TIFF ZIP + identity receipt</h2>
<p>Files below were generated by earlier lanes, not this audit. They are preserved for reproducibility, not relabeled as new or submission-ready. No file is selected or ranked here.</p>
{downloads(report['artifacts'])}</section>
<section class="card"><h2>Why GEMSDOE32 (<code>0.2778</code> OWNER-REPORTED; not organizer-confirmed) led the fleet — and can we beat it?</h2><p>Pixel-exact forensic comparison of the pinned <code>GEMSDOE28</code> (<code>40,199</code> dots; <code>0.2708</code> OWNER-REPORTED) and <code>GEMSDOE32</code> <code>h33-h33-2-b2</code> (<code>37,654</code> dots; <code>0.2778</code> OWNER-REPORTED) rasters confirms <strong>0 differing cells across all 12,279,160 grid pixels</strong> after deleting the <code>2,545</code> dots in the <code>1.0 &lt; d_cat &lt;= 2.0</code> mapped-fault collar. <code>GEMSDOE36</code> (<code>0.2750</code> OWNER-REPORTED) contains <code>100%</code> of <code>R0</code> verbatim plus <code>1,200</code> extra dots (<code>97.40%</code> 3-px overlap); all owner-reported fleet entries above <code>0.2600</code> in the supplied inventory lie in this <code>H19-5/D2.8</code> lineage (<code>92.64%–100%</code> overlap). Under asymmetric 300 m Tversky (<code>alpha=0.2, beta=0.8</code>), <code>~2.8 px</code> disk spacing near the <code>3 px</code> kernel radius can reduce redundant prediction mass, but does not prevent kernel overlap; collar pruning may remove low-credit mass, though proximity to a mapped fault alone does not prove zero hidden-truth credit. Cross-project score comparisons (e.g., <code>GEMSDOE81</code> <code>44,090</code> unit dots and <code>0.0041</code> OWNER-REPORTED vs <code>GEMSDOE76</code> <code>0.2343</code> OWNER-REPORTED / <code>GEMSDOE70</code> <code>0.2478</code> OWNER-REPORTED) are descriptive associations, not controlled causal proofs. <strong>HOLDOUT-DTI</strong> (<code>gems57-pooled-hide-v2</code>, <code>22,893</code> withheld positives): <code>H86D-CTHB</code> = <code>0.1133</code>, 95% CI <code>[0.0965, 0.1297]</code>; <code>H33-2-B2</code> fold-fair control = <code>0.1056</code>, 95% CI <code>[0.0936, 0.1166]</code>; paired HOLDOUT-DTI delta = <code>+0.0076</code>, 95% CI <code>[-0.0101, +0.0241]</code>. The paired CI crosses zero. The prompt's conflicting <code>0.3195</code> and <code>0.4413</code> current-leaderboard values are OWNER-REPORTED and unverified here; exceeding any reported value is not established. <strong>Do not infer a leaderboard projection from holdout results.</strong> <a href="https://github.com/buffedlizard55-lab/GEMSDOE86/blob/main/research/H33_INTERPRETATION_REVIEW.md">Metric counterexamples and limits of the explanation</a>.</p>
<p>No validated improvement over that competition result is authorized for upload while the literal witness stop holds. Our ranked research queue prioritizes <strong>signed paired-throw basement–gravity concordance, cross-corridor magnetic marker translation, hydrothermal magnetite-destruction &amp; vent-alignment corridors, 3D MT conductance × heat flow, and 1-m 3DEP LiDAR watershed-crossing scarps</strong>. <a href="hypotheses.html">{plan_count} ranked, scoped hypotheses →</a> · <a href="{REPO}/blob/main/research/GEOTHERMAL_VENT_DISCOVERY_SYNTHESIS.md">Geothermal vent synthesis →</a></p></section>
<section class="card"><h2>An auditable, refreshable project feed</h2><p>{fleet['projects_snapshotted']} / {fleet['projects_requested']} named repositories snapshotted. Last GitHub inventory refresh: <time>{e(fleet['refreshed_utc'])}</time>. Final-artifact registry measurement: <time>{e(registry['measured_utc'])}</time>.</p>
<p><a href="fleet.html">Browse the full project list</a>. This is repository metadata and local artifact validation, <strong>not a live DrivenData score or remaining-quota feed</strong>. Failed requests and the age of observations remain visible.</p></section>''')


def executive(report: dict, sources: dict) -> str:
    audit_rows = "".join(f'<tr><th scope="row">{e(a["lane"])}</th><td><a href="{e(link(a["file"]))}" download>{e(Path(a["file"]).name)}</a><br><code>{e(a["sha256"])}</code></td><td>{a["bytes"]:,} bytes<br><strong>DO NOT SUBMIT</strong></td></tr>' for a in report["artifacts"])
    return page("Executive summary", "executive-summary.html", f'''
<p class="eyebrow">Executive summary</p><h1>Submission procedure,<br>with an automatic stop.</h1>
<div class="callout"><span class="badge bad">CURRENT DECISION: DO NOT SUBMIT</span><p>Technical validation is automatic; there is no human-inspection gate hiding a release decision. All current artifacts fail the required literal registry gate. This session generated no new TIFF, copied no historical raster into a new release, ran no experiment and spent no weekly slot.</p>
<a class="btn" href="index.html#downloads">Download research TIFFs — audit only</a><a class="btn secondary" href="evidence/release-readiness.json">Open complete validator output</a></div>
<h2>Current downloads — audit only, no submission authorized</h2>
<div class="table-wrap"><table><thead><tr><th>Historical lane</th><th>Direct TIFF / SHA-256</th><th>Decision</th></tr></thead><tbody>{audit_rows}</tbody></table></div>
<p><a href="download-status.html">Independent all-download format audit</a> · <a href="evidence/download-validation.json">Its machine-readable report</a>. These format checks and the literal registry decision are separate gates; neither invents an organizer receipt.</p>
<h2>What is checked without intervention?</h2><ul><li>Every published TIFF is decoded and checked by the pinned shared validator and template-format checker.</li>
<li>CRS, shape, affine transform, float32 band count, valid footprint, finite values in range, outside-footprint zeros and mapped-fault masking are measured from disk.</li>
<li>The SHA matches the inventory, writer receipt and applicable scientific card. ZIP bytes must contain exactly the corresponding TIFF; empty or mismatched ZIPs fail.</li>
<li>Names and notes are verified against the project length cap. Stored model evidence is not rewritten or upgraded by a format pass.</li>
<li>All final artifacts are bound to the negative registry measurement. Unknown/missing/stale evidence fails closed.</li></ul>
<h2>Future submission steps — only after scientific clearance</h2><ol class="steps"><li><strong>Resolve the protocol conflict first.</strong> A new lane must be authorized, the actual shared cached features and a complete accessible registry recovered, and the uniqueness rule made satisfiable through an explicit protocol revision. This project does not grant that revision itself.</li>
<li><strong>Validate a new method.</strong> Freeze whole-segment buffered folds, derive catalogue features only from visible faults, run each feature's leakage canary, and beat the strongest rerunnable matched control with a positive paired physical-block confidence interval. Use the shared evaluator and writer unchanged.</li>
<li><strong>Run all release checks.</strong> A format pass alone is insufficient: both pre-placement surface and final-dot uniqueness must pass the literal thresholds. Promotion is separate from slot selection.</li>
<li><strong>Use the separate selector.</strong> It must inspect the authenticated submission page's actual remaining weekly quota and bind its decision to the exact raster SHA. The public rules list {sources['weekly_limit_in_public_rules']} submissions per week; that is not our current account balance. No account credentials or automatic upload are implemented here.</li>
<li><strong>Download only the authorized TIFF or one-TIFF ZIP.</strong> Choose <em>New submission</em> on the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">official submission page</a>, select the file (not JSON, a sample or an audit-only artifact), and paste its short identity note.</li>
<li><strong>Retain the organizer receipt.</strong> Bind the result and submission ID to the exact SHA before classifying any score as ORGANIZER-CONFIRMED. Follow the rules for one final selection, reproducible assets, eligibility and generative-AI disclosure.</li></ol>
<h2>DrivenData “New submission” portal checklist (exact form mapping)</h2>
<div class="table-wrap"><table><thead><tr><th>DrivenData portal field</th><th>Required specification</th><th>Automated check in this repo</th></tr></thead><tbody>
<tr><th scope="row"><code>File to submit</code></th><td>Single-band <code>float32</code> GeoTIFF (<code>.tif</code>) or <code>.zip</code> containing a single <code>.tif</code>; <code>EPSG:32611</code>; shape <code>3730 × 3292</code>; <code>100 m</code> affine transform; values in <code>[0, 1]</code>.</td><td>Checked automatically by <code>vendor/template66/gems57/validate.py</code>, <code>gates.py</code>, and <code>scripts/audit_release.py</code> (<code>10/10</code> format-valid, <code>0</code> NaN, <code>0</code> Inf, <code>min=0.0</code>, <code>max=1.0</code> — still <strong>DO NOT SUBMIT</strong> under literal witness gate).</td></tr>
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
        card = f'<a href="{e(link(a["source_card"]))}">Historical scientific card</a>' if a["source_card"] else '<span>Historical control, not a new canonical candidate card</span>'
        rows.append(f'''<section class="card" id="artifact-{i}"><h2>{e(a['lane'])}</h2><p class="filename">{e(Path(a['file']).name)}</p><span class="badge bad">DO NOT SUBMIT</span>
{score}{measure}<p>{card} · <a href="{e(link(h['source']))}">Metric context</a></p>
<p>FORMAT-VALIDATION: min {v['min']:.1f}, max {v['max']:.1f}; NaN {v['n_nan']}, Inf {v['n_inf']}; outside-footprint positive cells {v['outside_footprint_positive']}; on-catalogue positive cells {v['on_catalogue_positive']}.</p>
<details><summary>Every automated format / identity / ZIP check</summary><div class="table-wrap"><table><thead><tr><th>Check</th><th>Result</th></tr></thead><tbody>{checks}</tbody></table></div></details></section>''')
    return page("Validation evidence", "evidence.html", '''<p class="eyebrow">Read-only audit · not a model experiment</p><h1>Every file. Every gate.<br>No automatic promotion.</h1>
<p>Different fold designs, seeds, buffered/cut segments, training contexts and confidence intervals are not one comparable leaderboard. Do not select the largest number across these cards. No current holdout best or improvement over the private test is certified here.</p>
<p><a href="evidence/release-readiness.json">Full machine-readable audit</a> · <a href="evidence/all-artifacts-registry.json">All-artifact witness measurements</a> · <a href="evidence/protocol-preflight.json">Saturation proof</a></p>''' + "\n".join(rows))


def hypotheses(plan: dict) -> str:
    sections = []
    for h in plan["hypotheses"]:
        sources = " · ".join(f'<a href="{e(url)}">Official basis</a>' for url in h["official_basis"])
        sections.append(f'''<article class="card"><p class="eyebrow">Priority {h['rank']} · {e(h['id'])} · {e(h['status'])}</p><h2>{e(h['name'])}</h2>
<dl><dt>Specific layers</dt><dd>{e('; '.join(h['layers']))}</dd><dt>Physical signature</dt><dd>{e(h['signature'])}</dd>
<dt>Why an unmapped fault?</dt><dd>{e(h['why_unmapped'])}</dd><dt>Different from this checkout</dt><dd>{e(h['difference_from_repo'])}</dd>
<dt>Named non-fault mimic</dt><dd>{e(h['non_fault_mimic'])}</dd><dt>Expected value / implementation cost</dt><dd>{e(h['expected_dti_gain'])} {e(h['implementation_cost'])}</dd>
<dt>Data / viability</dt><dd>{e(h['data_readiness'])} {e(h.get('obtainability', 'No new external product is proposed as acquired.'))}</dd></dl><p>{sources}</p></article>''')
    steps = "".join(f'<li>{e(step)}</li>' for step in plan["required_validation_after_blockers_are_resolved"])
    return page("Research queue", "hypotheses.html", f'''<p class="eyebrow">Declared before implementation · planning only</p><h1>Seek displacement,<br>not just another edge.</h1>
<div class="callout"><span class="badge bad">NO NEW SCIENTIFIC EXPERIMENT AUTHORIZED</span><p>{e(plan['scope'])} None of the following has a measured HOLDOUT-DTI or predicted score. The top candidate was <strong>not validated</strong> because the required pre-placement stop fires. No weekly slot was used.</p></div>
<p>{e(plan['ranking_basis'])} {e(plan['novelty_scope'])}</p><p>{e(plan['evidence_boundary'])}</p>{''.join(sections)}
<h2>Validation plan after blockers are resolved</h2><ol>{steps}</ol>
<p><a href="{REPO}/blob/main/registry/h86c_hypotheses.json">Machine-readable hypothesis register</a> · <a href="{REPO}/blob/main/research/SESSION_20261024_REVIEW.md">2026-10-24 scientific critique</a> · <a href="{REPO}/blob/main/research/GEOTHERMAL_VENT_DISCOVERY_SYNTHESIS.md">Geothermal vent synthesis</a> · <a href="research.html">Physical rationale and limitations</a></p>''')


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
<a href="evidence/fleet-feed.json">Full commit/tree/blob inventory JSON</a> · <a href="evidence/prompt-named-unscored-audit-20261024.json">Byte-level audit of prompt-named unscored GEMSDOE89 &amp; GEMSDOE90 artifacts</a></div>
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
<li>PR #60 (<code>IR-86-SPT-02</code>) ran <code>build_spt.py</code> / <code>build_xfleet.py</code> at module import without <code>protocol_preflight.require_feasible()</code>, leaked withheld test-fold fault locations through <code>dist_cat &gt; 2.0</code>, promoted a coin-flip surface (<code>AUC = 0.4947</code>) with <code>100%</code> pinned-witness overlap, misrepresented prose vs code, and placed unregistered binaries in <code>submission/</code> alongside a contradictory <code>docs/submit.html</code> banner; PR #63 (<code>IR-86-TIPRELAY-01</code>) placed unregistered binaries in <code>docs/downloads/</code> with an audit backdoor and <code>85.08%</code> 3-px overlap vs <code>GEMSDOE32</code>. PR #63's <code>docs/downloads/</code> binaries were removed, PR #60's <code>submission/</code> binaries remain quarantined outside <code>docs/</code> (excluded from GitHub Pages and SHA/ZIP-verified against <code>spt-full-support-witness-audit.json</code>), all 37 CLI builders and 8 imported orchestrators are gated behind <code>require_feasible()</code>, and <code>audit_release.py</code> + <code>check_site.py</code> fail closed on any other binary or byte modification in <code>submission/</code>.</li>
<li>Byte-level forensic review of the two newly prompt-named unscored fleet artifacts (<code>IR-86-FLEET-GEMS89-90-20261024</code>; <a href="evidence/prompt-named-unscored-audit-20261024.json">measured JSON receipt</a>) found that <code>GEMSDOE89</code> (<code>gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros</code>, SHA-256 <code>715c8b86...</code>) claimed <code>complete_registry_coverage=true</code> over a 91-raster subset that omitted both <code>17GEMSDOE</code> (<code>100.0%</code> forward 3-px overlap) and discrete binary <code>13GEMSDOE</code> (<code>99.92%</code> = <code>37,624/37,654</code> forward 3-px overlap), while <code>GEMSDOE90</code> (<code>gems90-cnc-35000dots-20261024T084324Z</code>, SHA-256 <code>e1e91be2...</code>) privately altered the uniqueness rule, exceeded <em>both</em> clauses of its altered rule (<code>max_overlap = 0.9833 &gt; 0.70</code> and <code>max_excess_over_chance = 0.4037 &gt; 0.30</code>; pinned-checker overlap <code>98.35%</code> vs binary <code>13GEMSDOE</code> and <code>100.0%</code> vs <code>17GEMSDOE</code>) yet still emitted <code>duplicate=false</code>, used external <code>qfault_sliprate_den</code> (<code>AUC = 0.7784</code>) on cut-segment folds, and recorded a <code>NEGATIVE</code> score-calibration verdict. Also fixed a mis-cited rule reference on the executive checklist from nonexistent <code>Official Rules §5–6</code> to verified <code>Official Rules §1.1 &amp; §3.4–3.6</code> (<code>IR-86-RULES-SECT-20261024</code>).</li></ul>
<p>The historical scientific cards and TIFF bytes are preserved. This audit does not retroactively certify earlier experiments, erase protocol overruns or change thresholds.</p>
<p><a href="evidence/latest-review-run-card.json">Current negative run card</a> · <a href="evidence/spt-run-card.json">Revoked SPT forensic card</a> · <a href="{REPO}/blob/main/research/SESSION_20261024_REVIEW.md">2026-10-24 three-pass review and next actions</a></p>''')


def scientific_context() -> str:
    return page("Scientific context", "hypotheses.html", '''<p class="eyebrow">Mechanism is not validation</p><h1>Why geometry matters,<br>and why it is not enough.</h1>
<p>The official distance-weighted Tversky metric uses maximum prediction-times-kernel credit at each truth pixel. More nearby prediction mass need not increase that maximum; it can still add false-positive cost. Sparse placement can therefore outperform redundant mass, but removing the only useful cover of a real fault can reduce the index.</p>
<p>With weighted recovered truth T, weighted false-positive mass F, fixed truth count N and the official coefficients, the index is T / (0.2T + 0.2F + 0.8N + epsilon). If pruning loses credit a and removes false-positive mass b, it helps exactly when T b &gt; a(F + 4N + 5 epsilon), for positive denominators. This identity is tested against the shared metric. It is not a leaderboard projection or evidence of why a particular private result occurred.</p>
<p>A density, magnetization, conductivity or relief contrast is not uniquely a fault. The new magnetic-marker idea instead asks whether pre-existing markers were displaced. Even that can be imitated by unrelated contacts, remanence or survey seams. A basement offset can also be old and buried rather than a present surface trace. The scientific reports on the sources page motivate and limit the hypotheses; none validates our untested detector.</p>
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
    summary.update(featured_research_artifact=None, current_comparable_holdout_best=None,
                   reason="No selector decision. Different historical holdout designs cannot be ranked by their maxima.",
                   release_readiness="../evidence/release-readiness.json")
    return {
        "docs/index.html": home(report, feed, registry, review, len(plan["hypotheses"])),
        "docs/executive-summary.html": executive(report, sources),
        "docs/submit.html": submit_gate(report, review),
        "docs/evidence.html": evidence(report),
        "docs/hypotheses.html": hypotheses(plan),
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
    print("Evidence-generated site: PASS; all research downloads remain DO NOT SUBMIT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
