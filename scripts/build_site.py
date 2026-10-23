#!/usr/bin/env python3
"""Build the static Pages dashboard from canonical evidence and the score ledger.

The page is a read-only report. This script does not train a model, create a
raster, choose a competition submission, or authorize a weekly slot. Metrics
come from lane evidence JSON; historical leaderboard claims come from the
owner/user-supplied CSV and remain explicitly unverified.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _strict_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"Non-finite JSON value {value!r} in {path}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _web_path(path: str) -> str:
    value = str(path).replace("\\", "/")
    if value.startswith("docs/"):
        return value[len("docs/"):]
    if value.startswith("/") or ".." in Path(value).parts:
        raise ValueError(f"Unsafe Pages path: {path}")
    return value


def _load_score(score: dict) -> dict:
    return {
        "evidence_class": score["evidence_class"],
        "evaluator_version": score["evaluator_version"],
        "withheld_positive_pixels": int(score["withheld_positive_pixels"]),
        "dti": float(score["dti"]),
        "ci95": [float(x) for x in score["ci95"]],
    }


def build_summary(root: Path = ROOT) -> dict:
    """Construct the machine-readable current status using evidence files only."""
    root = Path(root).resolve()
    evidence = root / "docs/evidence"
    card = _strict_json(evidence / "h86b-gfco-run-card.json")
    results = _strict_json(evidence / "lane86b_results.json")
    protocol = _strict_json(evidence / "protocol-run-card.json")
    review_card = _strict_json(evidence / "session-review-run-card.json")
    preflight = _strict_json(evidence / "protocol-preflight.json")
    inventory = _strict_json(evidence / "download-inventory.json")

    if (review_card.get("verdict") != "negative"
            or review_card.get("submission_status") != "DO NOT SUBMIT"
            or review_card.get("weekly_slot_authorized") is not False
            or review_card.get("new_tif_generated") is not False
            or review_card.get("raster_sha256") != card.get("raster_sha256")
            or review_card.get("submission_name") != card.get("submission_name")
            or review_card.get("note") != card.get("note")):
        raise ValueError("Session review card contradicts the canonical H86B release state")

    artifact_path = root / card["submission_file"]
    if not artifact_path.is_file() or _sha256(artifact_path) != card["raster_sha256"]:
        raise ValueError("H86B raster is missing or differs from its canonical run-card SHA-256")
    if len(card["note"]) > 140:
        raise ValueError("H86B submission note exceeds the competition's stated limit")
    if card["verdict"] != "negative" or card["submission_ready"] is not False:
        raise ValueError("This dashboard builder is fail-closed; review the release selector before publishing")
    if card.get("approved_for_weekly_slot") is not False:
        raise ValueError("A negative run card cannot be authorized for a weekly slot")
    if any(item.get("approved_for_weekly_slot") is not False for item in inventory["artifacts"]):
        raise ValueError("A download inventory row is missing its explicit negative authorization state")

    selected = results["selected_arm"]
    holdouts = []
    split_specs = (
        ("buffered whole components", "holdout_buffered_whole_components"),
        ("segment hide — all components", "holdout_segment_all"),
        ("segment hide — detached components", "holdout_segment_detached"),
    )
    for label, split_key in split_specs:
        split = results[split_key]
        scores = split["scores"]
        deltas = split["paired_differences"]
        holdouts.append({
            "split": label,
            "candidate": _load_score(scores[selected]),
            "d2_8_control": _load_score(scores["d28_incumbent"]),
            "h33_b2_foldfair_control": _load_score(scores["h33_b2_foldfair"]),
            "paired_delta_vs_d2_8": {
                "evidence_class": deltas["d28_incumbent"]["evidence_class"],
                "evaluator_version": deltas["d28_incumbent"]["evaluator_version"],
                "withheld_positive_pixels": int(deltas["d28_incumbent"]["withheld_positive_pixels"]),
                "delta": float(deltas["d28_incumbent"]["delta"]),
                "ci95": [float(x) for x in deltas["d28_incumbent"]["ci95"]],
            },
            "paired_delta_vs_h33_b2": {
                "evidence_class": deltas["h33_b2_foldfair"]["evidence_class"],
                "evaluator_version": deltas["h33_b2_foldfair"]["evaluator_version"],
                "withheld_positive_pixels": int(deltas["h33_b2_foldfair"]["withheld_positive_pixels"]),
                "delta": float(deltas["h33_b2_foldfair"]["delta"]),
                "ci95": [float(x) for x in deltas["h33_b2_foldfair"]["ci95"]],
            },
        })

    validator = dict(card["validator"]["checks"])
    check_total = len(validator)
    check_passed = sum(value is True for value in validator.values())
    if check_total != 15 or check_passed != 15:
        raise ValueError("H86B serialized format validator is not a complete 15/15 local pass")

    artifacts = []
    for item in inventory["artifacts"]:
        path = root / item["file"]
        if not path.is_file() or _sha256(path) != item["sha256"]:
            raise ValueError(f"Download inventory hash mismatch: {item['file']}")
        artifacts.append({
            "file": _web_path(item["file"]),
            "sha256": item["sha256"],
            "status": item["status"],
            "approved_for_weekly_slot": item["approved_for_weekly_slot"],
            "zip": _web_path(str(Path(item["file"]).with_suffix(".zip")))
            if (root / str(Path(item["file"]).with_suffix(".zip"))).is_file() else None,
        })

    leakage = results["leakage_canaries"]
    uniqueness = card["correlation_overlap_vs_registry"]
    current_lane = {
        "id": "H86B-GFCO",
        "submission_name": card["submission_name"],
        "note": card["note"],
        "file": _web_path(card["submission_file"]),
        "zip": _web_path(card["zip_file"]),
        "sha256": card["raster_sha256"],
        "verdict": card["verdict"],
        "submission_ready": card["submission_ready"],
        "approved_for_weekly_slot": card["approved_for_weekly_slot"],
        "holdouts": holdouts,
        "leakage_canaries": {
            "evidence_class": "HOLDOUT-FEATURE-CANARY",
            "features_checked": int(leakage["total_checked"]),
            "max_discriminative_auc": float(leakage["max_discriminative_auc"]),
            "stop_threshold": 0.90,
            "any_leakage_flag": bool(leakage["any_leakage_flag"]),
        },
        "uniqueness": {
            "evidence_class": "REGISTRY-MEASUREMENT",
            "rasters_checked": int(uniqueness["rasters_checked"]),
            "scope": uniqueness["scope"],
            "surface_worst_abs_spearman": float(uniqueness["surface_worst_abs_spearman"]),
            "final_worst_discriminating_abs_spearman": float(uniqueness["final_worst_discriminating_abs_spearman"]),
            "worst_discriminating_dot_overlap_3px": float(uniqueness["final_worst_discriminating_dot_overlap_3px"]),
            "worst_discriminating_overlap_against": uniqueness["final_worst_discriminating_overlap_vs"],
            "worst_modern_comparable_overlap_3px": float(uniqueness["worst_modern_comparable_le_62k_overlap_3px"]),
            "overlap_vs_gemsdoe32_h33_b2": float(uniqueness["overlap_3px_vs_gems32_h33_2_b2"]),
            "literal_firings_over_0_70": list(uniqueness["literal_firings_over_0_70"]),
            "discriminating_duplicates": int(uniqueness["discriminating_duplicates"]),
            "registry_complete": False,
        },
        "validator": {
            "evidence_class": "LOCAL-FORMAT-MEASUREMENT",
            "status": card["validator"]["status"],
            "checks_passed": check_passed,
            "checks_total": check_total,
            "no_nan_inside_footprint": bool(card["validator"]["no_nan_inside_footprint"]),
            "values_in_0_1": bool(card["validator"]["values_in_0_1"]),
            "crs_shape_transform_match": bool(card["validator"]["crs_shape_transform_match"]),
            "checks": validator,
            "dots": int(card["validator"]["emitted_dots"]),
            "min": float(card["validator"]["min"]),
            "max": float(card["validator"]["max"]),
        },
    }

    return {
        "schema": "gems86.current-status.v1",
        "decision": "DO NOT SUBMIT",
        "decision_reason": "The selected H86B-GFCO research artifact is format-valid but fails the preregistered uniqueness gate, and the paired 95% interval for the primary buffered whole-component holdout includes zero. No artifact is approved for a weekly slot.",
        "latest_evaluated_lane": current_lane,
        "current_review": {
            "new_experiments_run": int(protocol["experiments_run"]),
            "new_candidate_generated": bool(preflight["candidate_generated"]),
            "submission_slots_used": int(protocol.get("submission_slots_used", 0)),
            "lane_assignment_present": False,
            "cached_feature_stack_present": False,
            "preflight_status": preflight["status"],
            "review_run_card": "evidence/session-review-run-card.json",
            "literal_support_witness": {
                "evidence_class": "REGISTRY-MEASUREMENT",
                "sha256": preflight["witness_sha256"],
                "positive_pixels": int(preflight["positive_pixels"]),
                "allowed_pixels": int(preflight["allowed_pixels"]),
                "uncovered_allowed_pixels": int(preflight["uncovered_allowed_pixels"]),
                "covered_allowed_fraction": float(preflight["covered_allowed_fraction"]),
                "universal_literal_support_blocker": bool(preflight["universal_overlap_blocker"]),
                "registry_complete": bool(preflight["registry_complete"]),
                "interpretation": "This is a literal positive-support measurement of one historical raster, not evidence of identical geological arrangement. Under the repository's current literal support rule it blocks any nonempty prediction; no exemption was used.",
            },
            "blockers": list(protocol["blockers"]),
        },
        "artifacts": artifacts,
        "organizer_confirmed_score": None,
        "organizer_receipt_present": False,
        "sources": {
            "competition_problem": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
            "competition_data": "https://www.drivendata.org/competitions/306/competition-doe-gems/data/",
            "reference_solution": "https://github.com/drivendataorg/gems-prize-reference-solution",
            "usgs_geodawn": "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and",
            "usgs_3dep": "https://www.usgs.gov/3d-elevation-program",
            "usgs_comcat": "https://earthquake.usgs.gov/fdsnws/event/1/",
            "gdr_ingenious": "https://gdr.openei.org/submissions/1391",
        },
        "provenance": {
            "run_card": "docs/evidence/h86b-gfco-run-card.json",
            "lane_evidence": "docs/evidence/lane86b_results.json",
            "protocol_run_card": "docs/evidence/protocol-run-card.json",
            "session_review_run_card": "docs/evidence/session-review-run-card.json",
            "registry_measurement": "docs/evidence/protocol-preflight.json",
            "download_inventory": "docs/evidence/download-inventory.json",
            "score_ledger": "registry/prior_scores.csv",
            "scores_label": "No organizer-confirmed score is recorded; local model metrics are HOLDOUT-DTI and peer-site values are OWNER/USER-REPORTED or explicitly missing.",
        },
    }


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _fmt(value: float, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def _ci(values: list[float]) -> str:
    return f"[{_fmt(values[0])}, {_fmt(values[1])}]"


def _nav(active: str) -> str:
    links = [
        ("index.html", "Decision"),
        ("executive-summary.html", "How to submit"),
        ("hypotheses.html", "Hypotheses"),
        ("evidence.html", "Evidence"),
        ("sources.html", "Sources"),
        ("irregularities.html", "Irregularities"),
    ]
    body = "".join(
        f'<a href="{href}"' + (' style="color:#e8eefc"' if active == href else "") + f'>{label}</a>'
        for href, label in links
    )
    return f'<header><nav><b>GEMSDOE86</b>{body}</nav></header>'


def _page(title: str, active: str, content: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{_e(title)} · GEMSDOE86</title><link rel="stylesheet" href="assets/site.css"></head><body>\n'
        + _nav(active) + f'<main>{content}</main>\n'
        '<footer>Local format validation is not organizer acceptance. No current file is authorized for submission.</footer></body></html>\n'
    )


def render_index(summary: dict) -> str:
    lane = summary["latest_evaluated_lane"]
    primary = lane["holdouts"][0]
    result = primary["candidate"]
    delta = primary["paired_delta_vs_d2_8"]
    h33_delta = primary["paired_delta_vs_h33_b2"]
    val = lane["validator"]
    content = f'''<section class="card hero">
<span class="badge bad">DO NOT SUBMIT · NO CANDIDATE IS AUTHORIZED</span>
<span class="badge ok">SAFE TO DOWNLOAD FOR AUDIT · LOCAL FORMAT PASS ({val['checks_passed']}/{val['checks_total']})</span>
<h1>Competition submission status</h1>
<p><b>{_e(lane['id'])}</b> is the latest evaluated research lane. This review generated no new raster. Its TIFF is linked for reproducibility and audit only; it is <b>not safe to submit</b>.</p>
<a class="btn danger" href="{_e(lane['file'])}" download>Download the research TIFF — DO NOT SUBMIT</a>
<a class="btn alt" href="{_e(lane['zip'])}" download>Download the one-TIFF ZIP — DO NOT SUBMIT</a>
<p><b>Submission name:</b> <code>{_e(lane['submission_name'])}</code></p>
<p><b>Note (≤140 characters):</b> <code>{_e(lane['note'])}</code></p>
<p class="mono"><b>Raster SHA-256:</b> {_e(lane['sha256'])}</p>
<p><b>Why not submit?</b> The primary buffered whole-component paired HOLDOUT-DTI interval includes zero; the final dots also exceed the prescribed overlap threshold against registry dot fields. The strict run card is negative.</p>
<p><a href="evidence/h86b-gfco-run-card.json">Canonical H86B-GFCO run card</a> · <a href="evidence/session-review-run-card.json">Current-review JSON run card</a> · <a href="data/summary.json">Machine-readable status feed</a></p>
</section>
<section class="card"><h2>Primary evidence (not a leaderboard score)</h2>
<p><b>HOLDOUT-DTI</b> · evaluator {_e(result['evaluator_version'])} · {_e(result['withheld_positive_pixels'])} withheld positives · 95% CI {_e(_ci(result['ci95']))}: {_e(_fmt(result['dti']))}.</p>
<p><b>Paired HOLDOUT-DTI delta vs d2.8 control</b> · same evaluator and withheld positives · 95% CI {_e(_ci(delta['ci95']))}: {_e(_fmt(delta['delta'], 4,))}. The interval crosses zero; no scientific promotion.</p>
<p><b>Paired HOLDOUT-DTI delta vs H33-2-B2 fold-fair control</b> · same evaluator and withheld positives · 95% CI {_e(_ci(h33_delta['ci95']))}: {_e(_fmt(h33_delta['delta']))}.</p>
</section>
<section class="card"><h2>Download / submission decision</h2>
<p>Download is for audit only. The file passed local serialization checks for a single float32 band, finite values in [0,1], and matching CRS, shape, and transform. That does not establish uniqueness or organizer acceptance.</p>
<p>There is no ORGANIZER-CONFIRMED score or submission-page receipt for this artifact, and no current weekly slot has been authorized.</p>
<a class="btn ghost" href="executive-summary.html">Read the future submission procedure</a>
<a class="btn ghost" href="hypotheses.html">Review next research hypotheses</a>
</section>'''
    return _page("Submission decision", "index.html", content)


def render_evidence(summary: dict) -> str:
    lane = summary["latest_evaluated_lane"]
    holdout_rows = []
    for item in lane["holdouts"]:
        candidate = item["candidate"]
        control = item["d2_8_control"]
        delta = item["paired_delta_vs_d2_8"]
        holdout_rows.append(
            f'<tr><td>{_e(item["split"])}</td>'
            f'<td><b>HOLDOUT-DTI</b> ({_e(candidate["evaluator_version"])}; '
            f'{_e(candidate["withheld_positive_pixels"])} withheld positives; 95% CI {_e(_ci(candidate["ci95"]))}) '
            f'{_e(_fmt(candidate["dti"]))}</td>'
            f'<td><b>HOLDOUT-DTI</b> ({_e(control["evaluator_version"])}; '
            f'{_e(control["withheld_positive_pixels"])} withheld positives; 95% CI {_e(_ci(control["ci95"]))}) '
            f'{_e(_fmt(control["dti"]))}</td>'
            f'<td><b>Paired HOLDOUT-DTI delta</b> ({_e(delta["evaluator_version"])}; '
            f'{_e(delta["withheld_positive_pixels"])} withheld positives; 95% CI {_e(_ci(delta["ci95"]))}) '
            f'{_e(_fmt(delta["delta"]))}</td></tr>'
        )
    leakage = lane["leakage_canaries"]
    uniqueness = lane["uniqueness"]
    witness = summary["current_review"]["literal_support_witness"]
    artifact_rows = []
    for artifact in summary["artifacts"]:
        artifact_rows.append(
            f'<tr><td><a class="mono" href="{_e(artifact["file"])}">{_e(Path(artifact["file"]).name)}</a></td>'
            f'<td class="mono">{_e(artifact["sha256"])}</td>'
            f'<td><a href="{_e(artifact["zip"])}">single-TIFF ZIP</a></td>'
            f'<td><span class="badge bad">{_e(artifact["status"])}</span></td></tr>'
        )
    content = f'''<section class="card hero"><span class="badge bad">DO NOT SUBMIT — NO ARTIFACT IS APPROVED</span>
<p>The values on this page are classified as HOLDOUT-DTI, HOLDOUT-FEATURE-CANARY, REGISTRY-MEASUREMENT, or LOCAL-FORMAT-MEASUREMENT. No organizer receipt exists.</p></section>
<h1>Evidence ledger</h1>
<h2>Spatial holdout (the existing H86B-GFCO run)</h2>
<p>The model lane's three preregistered experiments were already run in the inherited evidence. This review ran no new model experiment. The evaluator pooled DTI terms after buffered whole-component/segment hide-and-recover splits, with visible catalogue masking; the evidence files carry fold details and evaluator hashes.</p>
<table><thead><tr><th>Split</th><th>H86B-GFCO</th><th>d2.8 control</th><th>Paired delta vs d2.8</th></tr></thead><tbody>{''.join(holdout_rows)}</tbody></table>
<p>The primary buffered whole-component paired confidence interval includes zero, so the best point estimate does not clear the preregistered promotion test. Segment-split results are descriptive HOLDOUT-DTI, not organizer scores.</p>
<h2>Leakage canaries</h2>
<p><b>HOLDOUT-FEATURE-CANARY</b> · {_e(leakage['features_checked'])} single-feature channels checked; maximum discriminative AUC {_e(_fmt(leakage['max_discriminative_auc']))}; stop threshold {_e(_fmt(leakage['stop_threshold'], 2))}; any flag: {_e(leakage['any_leakage_flag'])}. This diagnostic is not DTI and does not prove geological validity.</p>
<h2>Registry comparisons</h2>
<p><b>REGISTRY-MEASUREMENT</b> · {_e(uniqueness['rasters_checked'])} hash-verified rasters in the lane's stated partial scope; registry completeness is false. Pre-placement surface worst absolute Spearman {_e(_fmt(uniqueness['surface_worst_abs_spearman']))}; final-dot worst discriminating absolute Spearman {_e(_fmt(uniqueness['final_worst_discriminating_abs_spearman']))}; worst forward 3-px overlap among discriminating comparisons {_e(_fmt(uniqueness['worst_discriminating_dot_overlap_3px']))} against {_e(uniqueness['worst_discriminating_overlap_against'])}. Limit: 0.70. The candidate also exceeds the literal overlap limit on the listed dense/legacy dot fields in the run card.</p>
<p><b>REGISTRY-MEASUREMENT</b> · overlap against GEMSDOE32 H33-2-B2 {_e(_fmt(uniqueness['overlap_vs_gemsdoe32_h33_b2']))}; worst overlap against the stated modern/comparable subset {_e(_fmt(uniqueness['worst_modern_comparable_overlap_3px']))}. These are scoped comparisons, not global uniqueness clearance.</p>
<p><b>REGISTRY-MEASUREMENT</b> · the separately pinned historical positive-support witness has {_e(witness['uncovered_allowed_pixels'])} uncovered allowed cells, SHA-256 <code>{_e(witness['sha256'])}</code>, and is positive on the complete allowed domain under the repository's literal support definition. This is a support/overlap blocker, not proof of identical geological arrangement; the evidence inventory is explicitly incomplete. No density exemption was applied.</p>
<h2>Local file validator</h2>
<p><b>LOCAL-FORMAT-MEASUREMENT</b> · {_e(lane['validator']['checks_passed'])}/{_e(lane['validator']['checks_total'])} checks pass: no NaN inside the footprint; all values in [0,1]; single-band float32; CRS, shape, and transform match the sample grid. This is not organizer acceptance.</p>
<h2>Download inventory — all negative</h2>
<table><thead><tr><th>Research TIFF</th><th>SHA-256</th><th>Bundle</th><th>Decision</th></tr></thead><tbody>{''.join(artifact_rows)}</tbody></table>
<p><a href="evidence/h86b-gfco-run-card.json">H86B-GFCO run card</a> · <a href="evidence/lane86b_results.json">Full lane results</a> · <a href="evidence/protocol-preflight.json">Literal support witness</a> · <a href="evidence/download-inventory.json">Exact download inventory</a></p>'''
    return _page("Evidence", "evidence.html", content)


def render_executive_summary(summary: dict) -> str:
    lane = summary["latest_evaluated_lane"]
    content = f'''<section class="card hero"><span class="badge bad">CURRENT DECISION: DO NOT SUBMIT ANY REPOSITORY FILE</span>
<h1>Executive summary — submission procedure and current stop</h1>
<p>The latest evaluated candidate is {_e(lane['id'])}. Its local file checks pass, but its research verdict is negative and it is not authorized for a weekly slot. Download it only for audit or reproducibility.</p>
<a class="btn danger" href="{_e(lane['file'])}" download>Download research TIFF — DO NOT SUBMIT</a>
<a class="btn alt" href="{_e(lane['zip'])}" download>Download one-TIFF ZIP — DO NOT SUBMIT</a>
<p><b>Submission name:</b> <code>{_e(lane['submission_name'])}</code></p>
<p><b>Note (≤140 characters):</b> <code>{_e(lane['note'])}</code></p>
<p class="mono"><b>SHA-256:</b> {_e(lane['sha256'])}</p>
<p>The current review created no new raster and used no competition slot. See the <a href="evidence.html">evidence page</a> for labelled holdout and validator results.</p></section>
<h2>Exact portal procedure — only for a future promoted file</h2>
<p>These steps do not authorize any current file. Continue only after a new, canonical run card says <code>verdict: promote</code>, the serialized raster validator passes, the prescribed holdout and registry gates pass, and a separate selector verifies the live weekly allowance.</p>
<ol>
<li>Open the future candidate's canonical run card and confirm its promotion decision, raster SHA-256, and note length.</li>
<li>Download the exact <code>.tif</code> or a <code>.zip</code> containing exactly one GeoTIFF. Compute its SHA-256 and compare it with the run card.</li>
<li>Open the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">official DrivenData submission page</a>, sign in through the competition site, review the current rules and remaining quota, and choose <b>New submission</b>.</li>
<li>Select the promoted TIFF (not JSON evidence, a sample raster, or any file labelled <code>DO-NOT-SUBMIT</code>).</li>
<li>Paste the run-card note, verify it matches the exact raster, and submit only after the independent selector authorizes a slot.</li>
<li>Retain the submission-page receipt and exact SHA-256. Only the receipt may support an <b>ORGANIZER-CONFIRMED</b> score.</li>
</ol>
<h2>About the earlier range error</h2>
<p>The rejected bytes were not provided, so the original cause is unknown. The latest research TIFF passes this repository's local format checks for finite [0,1] values and matching grid metadata. A local pass cannot guarantee organizer acceptance and does not override its negative scientific and uniqueness decision.</p>
<h2>Current status</h2><p><a href="index.html">Return to the prominent download/decision page</a> · <a href="evidence/session-review-run-card.json">Current review JSON run card</a> · <a href="evidence/h86b-gfco-run-card.json">Latest evaluated lane card</a></p>'''
    return _page("How to submit", "executive-summary.html", content)


def render_hypotheses(root: Path = ROOT) -> str:
    proposal = _strict_json(root / "research/next_hypotheses.json")
    cards = []
    for item in proposal["hypotheses"]:
        layers = "".join(f"<li>{_e(layer)}</li>" for layer in item["layers"])
        sources = " · ".join(
            f'<a href="{_e(source["url"])}" rel="noreferrer">{_e(source["name"])}</a>'
            for source in item["official_sources"]
        )
        cards.append(f'''<article class="card"><h2>Rank {_e(item['rank'])} — {_e(item['id'])}: {_e(item['name'])}</h2>
<p><b>Layers:</b></p><ul>{layers}</ul>
<p><b>Physical signature:</b> {_e(item['physical_signature'])}</p>
<p><b>Why it may reveal a catalogue-missing fault:</b> {_e(item['missing_fault_mechanism'])}</p>
<p><b>Named non-fault mimic:</b> {_e(item['non_fault_mimic'])}</p>
<p><b>Difference from existing code:</b> {_e(item['difference_from_repo'])}</p>
<p><b>Repository-level novelty / overlap:</b> {_e(item['repository_novelty'])}</p>
<p><b>Qualitative expected DTI potential:</b> {_e(item['expected_dti_potential'])}</p>
<p><b>Implementation cost:</b> {_e(item['implementation_cost'])}</p>
<p><b>Data availability / viability:</b> {_e(item['data_availability'])}</p>
<p><b>Official sources for review:</b> {sources}</p></article>''')
    content = f'''<section class="card hero"><span class="badge bad">NO EXPERIMENT AUTHORIZED IN THIS REVIEW</span>
<h1>Next geological hypotheses</h1>
<p>{_e(proposal['ranking_basis'])}</p>
<p><b>Top proposed candidate:</b> {_e(proposal['top_candidate'])}. {_e(proposal['validation_status'])}</p>
<p>Do not interpret the qualitative ranking as a numerical DTI projection or an organizer score. Exact cross-repository novelty is not established by the incomplete registry.</p></section>
{''.join(cards)}
<p><a href="research.html">Full scientific review</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE86/blob/main/research/next_hypotheses.json">Structured hypothesis record</a></p>'''
    return _page("Hypotheses", "hypotheses.html", content)


def render_sources(root: Path = ROOT) -> str:
    ledger_path = root / "registry/prior_scores.csv"
    with ledger_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    required = {"site", "submission", "score", "evidence_class", "source_url"}
    if rows and not required.issubset(rows[0]):
        raise ValueError("Prior-score ledger schema is incomplete")
    table_rows = []
    for row in rows:
        submission = row["submission"] or "No submission name provided"
        score = row["score"].strip() or "Not supplied"
        table_rows.append(
            f'<tr><td>{_e(row["site"])}</td><td class="mono">{_e(submission)}</td>'
            f'<td>{_e(score)}</td><td>{_e(row["evidence_class"])}</td>'
            f'<td><a href="{_e(row["source_url"])}" rel="noreferrer">source page</a></td></tr>'
        )
    # Copy the canonical ledger into Pages as a direct, downloadable audit file.
    mirror = root / "docs/data/prior_scores.csv"
    mirror.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ledger_path, mirror)
    official = [
        ("DrivenData problem and format", "Official competition task and submission requirements", "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"),
        ("DrivenData data page", "Official data access; login may be required", "https://www.drivendata.org/competitions/306/competition-doe-gems/data/"),
        ("Official reference solution", "Organizer's baseline repository", "https://github.com/drivendataorg/gems-prize-reference-solution"),
        ("USGS GeoDAWN", "Official airborne magnetic/radiometric release and DOI 10.5066/P93LGLVQ", "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and"),
        ("USGS 3DEP", "Official elevation program source; owner-derived local product has not been independently authenticated here", "https://www.usgs.gov/3d-elevation-program"),
        ("USGS ComCat FDSN", "Official event service; not accessible from this sandbox's outbound allowlist", "https://earthquake.usgs.gov/fdsnws/event/1/"),
        ("DOE Geothermal Data Repository / INGENIOUS", "Official project-data landing page for manual review", "https://gdr.openei.org/submissions/1391"),
        ("NLR report 96647", "Competition rules document supplied by the owner", "https://docs.nlr.gov/docs/fy26osti/96647.pdf"),
    ]
    source_rows = "".join(
        f'<tr><td>{_e(name)}</td><td>{_e(scope)}</td><td><a href="{_e(url)}" rel="noreferrer">open source</a></td></tr>'
        for name, scope, url in official
    )
    content = f'''<section class="card hero"><span class="badge bad">NO ARTIFACT IS APPROVED FOR SUBMISSION</span>
<h1>Official links and prior-score ledger</h1>
<p>Official-source links are provided for manual review. The DrivenData and USGS sites were not freshly fetched in this review because they are outside the sandbox's permitted outbound hosts; this page does not claim a current external leaderboard read or a newly authenticated download.</p></section>
<h2>Official and primary sources</h2>
<table><thead><tr><th>Source</th><th>Scope / limitation</th><th>Link</th></tr></thead><tbody>{source_rows}</tbody></table>
<h2>Prior-site ledger</h2>
<p>The ledger below transcribes the owner's prompt and is not an organizer receipt. Numeric entries are OWNER/USER-REPORTED unless the evidence-class column says otherwise. A blank score means none was supplied; it does not prove no score exists. No row is ORGANIZER-CONFIRMED in this checkout.</p>
<p><a class="btn ghost" href="data/prior_scores.csv" download>Download the canonical CSV ledger</a></p>
<div class="table-wrap"><table><thead><tr><th>Site</th><th>Submission name as reported</th><th>Reported value</th><th>Evidence class</th><th>Source</th></tr></thead><tbody>{''.join(table_rows)}</tbody></table></div>
<p>Canonical source: <a href="https://github.com/buffedlizard55-lab/GEMSDOE86/blob/main/registry/prior_scores.csv">registry/prior_scores.csv</a>. The values 0.2778, 0.3195, and 0.4413 are conflicting OWNER/USER-REPORTED figures without a submission-page receipt; do not treat them as verified scores.</p>'''
    return _page("Sources", "sources.html", content)


def render_irregularities(summary: dict) -> str:
    review = summary["current_review"]
    issues = [
        "The supplied request refers to a single assigned method paragraph, but none is present in the prompt received for this review; the lane was not invented.",
        "The shared cached feature stack is absent from the checkout. The prior feature-cache receipt references a cache file that is not present; no private replacement was built.",
        "The inherited H86B-GFCO model lane already used its preregistered experiment budget. This review did not run a model experiment or generate a new TIFF.",
        "The H86B-GFCO candidate remains negative: its primary paired whole-component HOLDOUT-DTI interval includes zero, and its registry dot-overlap audit exceeds the prescribed limit against dot-field priors.",
        "The historical registry support witness covers the full allowed domain under the literal positive-support definition. Its overlap is a protocol blocker, not proof of identical geological arrangement; the registry inventory is incomplete.",
        "Owner-mirrored competition and USGS-derived data are hash-pinned for integrity but are not authenticated against original organizer or agency downloads in this checkout.",
        "No submission-page receipt, current weekly quota, or ORGANIZER-CONFIRMED score is available. Public leaderboard values quoted in the prompt remain unverified owner/user claims.",
    ]
    content = '<section class="card hero"><span class="badge bad">DO NOT SUBMIT</span><h1>Irregularities and limitations</h1><p>These issues are evidence boundaries, not assumptions to paper over.</p></section><ol>'
    content += "".join(f"<li>{_e(issue)}</li>" for issue in issues)
    content += f'''</ol><h2>Current protocol record</h2>
<p>New experiments run in this review: {_e(review['new_experiments_run'])}. New candidate generated: {_e(review['new_candidate_generated'])}. Submission slots used: {_e(review['submission_slots_used'])}.</p>
<p><a href="evidence/session-review-run-card.json">Current review JSON run card</a> · <a href="evidence/protocol-run-card.json">Protocol preflight record</a> · <a href="evidence/protocol-preflight.json">Registry witness measurement</a> · <a href="research.html">Historical scientific review and sources</a></p>'''
    return _page("Irregularities", "irregularities.html", content)


def build(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    summary = build_summary(root)
    data_dir = docs / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (docs / "index.html").write_text(render_index(summary), encoding="utf-8")
    (docs / "evidence.html").write_text(render_evidence(summary), encoding="utf-8")
    (docs / "executive-summary.html").write_text(render_executive_summary(summary), encoding="utf-8")
    (docs / "hypotheses.html").write_text(render_hypotheses(root), encoding="utf-8")
    (docs / "sources.html").write_text(render_sources(root), encoding="utf-8")
    (docs / "irregularities.html").write_text(render_irregularities(summary), encoding="utf-8")
    return summary


def main() -> int:
    summary = build()
    # Perform the existing strict download/HTML-link safety audit after rendering.
    sys.path.insert(0, str(ROOT))
    from scripts.check_site import check

    errors = check(ROOT)
    if errors:
        raise SystemExit("Site build failed integrity checks:\n" + "\n".join(errors))
    print(json.dumps({
        "status": "PASS",
        "decision": summary["decision"],
        "lane": summary["latest_evaluated_lane"]["id"],
        "tif": summary["latest_evaluated_lane"]["file"],
        "sha256": summary["latest_evaluated_lane"]["sha256"],
        "artifacts": len(summary["artifacts"]),
        "safe_to_submit": summary["latest_evaluated_lane"]["submission_ready"],
        "current_review_generated_new_tif": summary["current_review"]["new_candidate_generated"],
        "organizer_receipt_present": summary["organizer_receipt_present"],
    }, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
