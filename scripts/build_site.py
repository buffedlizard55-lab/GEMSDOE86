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
from scripts.audit_legacy_spt import check_snapshot as check_legacy_spt  # noqa: E402

REPO = "https://github.com/buffedlizard55-lab/GEMSDOE86"


def e(value) -> str:
    return escape(str(value), quote=True)


def link(path: str) -> str:
    return path.removeprefix("docs/") if path.startswith("docs/") else REPO + "/blob/main/" + path


def page(title: str, active: str, body: str) -> str:
    nav = (("index.html", "Downloads"), ("executive-summary.html", "How to submit"),
           ("evidence.html", "Validation"), ("hypotheses.html", "Research queue"),
           ("fleet.html", "Project feed"), ("sources.html", "Sources"))
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


def legacy_notice(legacy: dict) -> str:
    """Replace the previously optimistic direct-URL upload guide with a stop."""
    return page("Legacy SPT correction", "executive-summary.html", f'''
<p class="eyebrow">Correction of a historical release claim</p>
<h1>SPT file: <strong>DO NOT SUBMIT</strong>.</h1>
<div class="callout"><span class="badge bad">NOT CLEARED · NO COMPETITION UPLOAD</span>
<p>A former page described this TIFF as ready to submit. That claim was wrong. This page is generated from a byte-checked negative review, not a human-inspection placeholder. No upload link or recommendation is offered.</p>
<p><strong>Existing research file (not generated in this review):</strong> <code>{e(Path(legacy['file']).name)}</code><br>SHA-256: <code>{e(legacy['sha256'])}</code>.</p>
<p>The original TIFF and ZIP pass local numerical and grid checks, including finite values in [0,1], but their dots have <strong>{legacy['registry']['final_dots_forward_overlap_3px']:.0%} forward 3-pixel overlap</strong> with one pinned registry prior, above the {legacy['registry']['overlap_limit']:.0%} stop. A 25-file subset check cannot clear a file against the full registry.</p>
<p>The archived 0.00526 / 0.00479 figures used the full catalogue to place dots before evaluating held faults; they are <strong>not a valid visible-only HOLDOUT-DTI or an organizer score</strong>. No paired physical-block 95% confidence interval or pre-placement surface check is available. The builder used a private writer rather than the shared submission writer and has been retired.</p>
<p><a href="evidence/spt-legacy-audit.json">Automated TIFF/ZIP/registry audit</a> · <a href="evidence/spt-run-card.json">Corrected negative run card</a> · <a href="executive-summary.html">Actual submission procedure and gating</a></p></div>''')


def home(report: dict, fleet: dict, registry: dict, review: dict) -> str:
    n = report["artifact_count"]
    return page("Download decision", "index.html", f'''
<section class="hero"><p class="eyebrow">DOE GEMS Prize · fault-discovery research</p>
<span class="badge bad">NOT SAFE TO SUBMIT · NO CANDIDATE AUTHORIZED</span>
<h1>Download the research.<br><span class="subtle">Do not spend a submission slot.</span></h1>
<p class="lede">The downloadable GeoTIFFs pass automated local format checks, but the mandatory uniqueness rule blocks every nonempty candidate. A new hash is not a unique scientific submission.</p>
<p><span class="badge ok">SAFE TO DOWNLOAD FOR AUDIT</span> <strong>DO NOT SUBMIT</strong> any current file.</p>
<p class="muted">Latest automated remeasurement: <time>{e(review['registry_measured_utc'])}</time>. <a href="evidence/latest-review-run-card.json">Current negative run card</a> · <a href="{REPO}/blob/main/research/SESSION_20261024_REVIEW.md">Safety review and next steps</a>. Historical model results below were not rerun.</p>
<div class="actions"><a class="btn" href="#downloads">Open TIFF downloads ↓</a><a class="btn secondary" href="executive-summary.html">Why blocked &amp; how submission works →</a></div></section>
<section class="callout"><span class="badge bad">IMPORTANT: LEGACY SPT PAGE CORRECTED</span><p>A separate earlier SPT page described an off-dashboard TIFF as ready. Its TIFF passes local format checks but fails the literal registry-overlap rule; its in-sample diagnostic is not a valid holdout. <a href="submit.html">Read the corrected DO NOT SUBMIT notice</a>.</p></section>
<div class="kpi"><div><span>Local format &amp; integrity</span><strong>{report['locally_valid_artifacts']} / {n}</strong><small>All serialized files re-read; names, notes, masks, SHA and ZIP payloads checked.</small></div>
<div><span>Submission-approved files</span><strong>None</strong><small>Every candidate remains negative. No selector or portal operation was run.</small></div>
<div><span>New experiments / slots used</span><strong>{report['experiments_run']} / {report['submission_slots_used']}</strong><small>This audit stopped before modeling or placement, as required.</small></div></div>
<section class="callout"><h2>Why a new submission cannot be cleared</h2><p>A hash-pinned historical registry raster is positive at <strong>every allowed pixel</strong>. Under the unchanged literal rule, any nonempty dot set has forward overlap {report['witness_positive_support_allowed_fraction']:.0%}, above the {report['overlap_limit']:.0%} stop. This is a rule-satisfiability failure, not evidence that every geological idea is identical.</p>
<p>All {len(registry['artifacts'])} inherited final TIFFs were independently rechecked against this witness. No dense-prior exemption was applied. <a href="evidence/all-artifacts-registry.json">Measured negative proof</a> · <a href="evidence/session-20261023-run-card.json">This session's run card</a>.</p></section>
<section id="downloads"><p class="eyebrow">Immediate downloads · historical research artifacts</p><h2>TIFF + single-TIFF ZIP + identity receipt</h2>
<p>Files below were generated by earlier lanes, not this audit. They are preserved for reproducibility, not relabeled as new or submission-ready. No file is selected or ranked here.</p>
{downloads(report['artifacts'])}</section>
<section class="card"><h2>Can we beat the owner's reported H33 result?</h2><p>The available H33 page describes kernel-scale thinning and mapped-fault-collar pruning. Those operations can reduce redundant false-positive cost, but can also remove true coverage. They do not establish a new fault or a causal explanation of a private score. The reported result lacks a submission-page receipt here; its archived projection remains a projection.</p>
<p>No validated improvement over that competition result is demonstrated. The next research direction is <strong>displaced magnetic markers rather than another unsigned edge detector</strong>, with explicit non-fault controls and buffered whole-component validation. It remains untested under the mandatory stop. <a href="hypotheses.html">Three ranked, scoped hypotheses →</a></p></section>
<section class="card"><h2>An auditable, refreshable project feed</h2><p>{fleet['projects_snapshotted']} / {fleet['projects_requested']} named repositories snapshotted. Last GitHub inventory refresh: <time>{e(fleet['refreshed_utc'])}</time>. Final-artifact registry measurement: <time>{e(registry['measured_utc'])}</time>.</p>
<p><a href="fleet.html">Browse the full project list</a>. This is repository metadata and local artifact validation, <strong>not a live DrivenData score or remaining-quota feed</strong>. Failed requests and the age of observations remain visible.</p></section>''')


def executive(report: dict, sources: dict) -> str:
    audit_rows = "".join(f'<tr><th scope="row">{e(a["lane"])}</th><td><a href="{e(link(a["file"]))}" download>{e(Path(a["file"]).name)}</a><br><code>{e(a["sha256"])}</code></td><td>{a["bytes"]:,} bytes<br><strong>DO NOT SUBMIT</strong></td></tr>' for a in report["artifacts"])
    return page("Executive summary", "executive-summary.html", f'''
<p class="eyebrow">Executive summary</p><h1>Submission procedure,<br>with an automatic stop.</h1>
<div class="callout"><span class="badge bad">CURRENT DECISION: DO NOT SUBMIT</span><p>Technical validation is automatic; there is no human-inspection gate hiding a release decision. All current artifacts fail the required literal registry gate. This session generated no new TIFF, copied no historical raster into a new release, ran no experiment and spent no weekly slot.</p>
<a class="btn" href="index.html#downloads">Download research TIFFs — audit only</a><a class="btn secondary" href="evidence/release-readiness.json">Open complete validator output</a></div>
<p><strong>Correction:</strong> a separate historical SPT upload guide was unsafe. Its 11th, off-dashboard raster is <a href="submit.html">DO NOT SUBMIT</a>, despite passing local [0,1] checks. It is reviewed separately in <a href="evidence/spt-legacy-audit.json">the automatic legacy audit</a>, not silently counted among the ten downloads below.</p>
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
<h2>The reported “[0,1]” rejection</h2><p>The rejected file was not supplied, so the cause is unknown. The shared writer rejects nonfinite and out-of-range predictions instead of silently clipping them, then validates the serialized output and ZIP. The current audit rechecks those bytes. This prevents us publishing that class of invalid numerical output, but it does not prove portal acceptance.</p>
<p>The public specification describes null/NaN outside bounds. The project's all-finite, zero-outside policy is a conservative local choice. It must not be described as organizer-confirmed acceptance or a complete diagnosis of the earlier error.</p>
<h2>Reproduce the checks</h2><pre><code>python scripts/restore_protocol_data.py --include-registry
python scripts/audit_release.py --measure-registry
python scripts/refresh_fleet.py
python scripts/build_site.py
python -m pytest -q</code></pre>
<p>The first command restores pinned small mirror inputs and one historical witness for comparison, not a new submission. Shared cached features are not regenerated. No GPU is needed for these audits; the official reference also has CPU-only training options.</p>
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
    return page("Research queue", "hypotheses.html", f'''<p class="eyebrow">Untried hypotheses · planning only</p><h1>Seek displacement,<br>not just another edge.</h1>
<div class="callout"><span class="badge bad">NO NEW SCIENTIFIC EXPERIMENT AUTHORIZED</span><p>{e(plan['scope'])} None of the following has a measured HOLDOUT-DTI or predicted score. The top candidate was <strong>not validated</strong> because the required pre-placement stop fires. No weekly slot was used.</p><p>The older plan included SPT as untried; <a href="submit.html">SPT was subsequently tried and its optimistic release status has been withdrawn</a>.</p></div>
<p>{e(plan['ranking_basis'])} {e(plan['novelty_scope'])}</p>{''.join(sections)}
<h2>Validation plan after blockers are resolved</h2><ol>{steps}</ol>
<p><a href="{REPO}/blob/main/registry/hypotheses_20261024.json">Current machine-readable hypothesis register</a> · <a href="{REPO}/blob/main/registry/h86c_hypotheses.json">Archived earlier plan</a> · <a href="research.html">Physical rationale and limitations</a></p>''')


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
<a href="evidence/fleet-feed.json">Full commit/tree/blob inventory JSON</a></div>
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
<p><a href="evidence/source-review-20261023.json">Exact observation register</a> · <a href="fleet.html">All owner-reported project results</a></p>
<p>Official observations are dated research records, not an automatically authenticated live leaderboard. The daily feed refreshes repository metadata and local file checks, not the meaning of external publications or the remaining account quota.</p>''')


def irregularities(report: dict) -> str:
    items = "".join(f'<li>{e(item)}</li>' for item in report["limitations"])
    return page("Limitations and irregularities", "irregularities.html", f'''<p class="eyebrow">Explicitly unresolved</p><h1>No silent exceptions.<br>No invented score.</h1><ol>{items}</ol>
<h2>Defects found in the reviews</h2><ul><li>The inherited PR #60 <a href="submit.html">SPT upload page</a> incorrectly said READY and its card called an in-sample diagnostic HOLDOUT-DTI. Both are withdrawn; <a href="evidence/spt-legacy-audit.json">the separate byte/registry audit</a> proves the file passes format but fails literal uniqueness.</li>
<li>An imported model caller could bypass the mandatory preflight with a boolean parameter. That escape hatch was removed; regression tests require a stop before feature building.</li>
<li>The inherited site compared nonidentical holdout instruments as a repository-wide “highest holdout.” That wording was removed. The automated view labels each design and confidence interval separately.</li>
<li>The inherited headline byte and note-character counts disagreed with the serialized GFCO receipt. Counts now come directly from every actual file and receipt on each build.</li>
<li>The old source ledger conflated the owner's H33 reported result with a different historical projection. The supplied result is retained as OWNER-REPORTED, not mislabeled as either confirmed or fabricated.</li>
<li>A static-site inventory path check accidentally depended on the last traversed HTML path. It now checks the publication root directly, including when there is no HTML input.</li></ul>
<p>The historical scientific cards and TIFF bytes are preserved. This audit does not retroactively certify earlier experiments, erase protocol overruns or change thresholds.</p>
<p><a href="evidence/session-20261024-spt-correction-run-card.json">Current negative run card</a> · <a href="{REPO}/blob/main/research/SESSION_20261024_SPT_CORRECTION.md">Current three-pass correction</a> · <a href="evidence/session-20261023-run-card.json">Prior run card</a></p>''')


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
    review = strict_json(root / "docs/evidence/latest-review-run-card.json")
    if (review["release_report_sha256"] != sha256(root / "docs/evidence/release-readiness.json")
            or review["registry_measurement_sha256"] != sha256(root / "docs/evidence/all-artifacts-registry.json")
            or review["registry_measured_utc"] != registry["measured_utc"]
            or review["verdict"] != "negative" or review["submission_ready"] is not False
            or review["new_candidate_generated"] is not False):
        raise ValueError("Current review is stale or contradicts the negative release audit; remeasure registry")
    legacy = check_legacy_spt(root)  # verifies off-dashboard TIFF and withdrawn card, fail closed
    sources = strict_json(root / "docs/evidence/source-review-20261023.json")
    plan = strict_json(root / "registry/hypotheses_20261024.json")
    with (root / "registry/prior_scores.csv").open(newline="", encoding="utf-8") as stream:
        ledger = list(csv.DictReader(stream))
    summary = {k: report[k] for k in ("schema", "audit_ok", "decision", "submission_ready", "safe_to_submit", "artifact_count", "locally_valid_artifacts", "new_candidate_generated", "experiments_run", "submission_slots_used")}
    summary.update(featured_research_artifact=None, current_comparable_holdout_best=None,
                   reason="No selector decision. Different historical holdout designs cannot be ranked by their maxima.",
                   release_readiness="../evidence/release-readiness.json")
    return {
        "docs/index.html": home(report, feed, registry, review),
        "docs/submit.html": legacy_notice(legacy),
        "docs/executive-summary.html": executive(report, sources),
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
