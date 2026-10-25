# Repository review — session fb9725b9 — 2026-10-25

## Decision

**DO NOT SUBMIT. No new TIFF generated; the requested unique-submission deliverable remains unmet.** Existing downloadable TIFFs remain available for research/selector review. A local format pass is not scientific clearance or weekly-slot authorization. No model experiment or submission slot was used.

Read the standing [prompt](../PROMPT.md), [agent instructions](../AGENTS.md), README safety decision, [complete request archive](REQUEST_20261025.md), prior handoffs and [queued hypotheses](../registry/h86g_hypotheses.json). The prompt is already preserved through README and the request archive; no duplicate historical request or old raster was rebranded as new work.

## Pass 1 — actual repair

`session_preflight.check_pins()` checked only `vendor/gems57`, although the release audit checks both that path and `vendor/template66`. Consequently its `shared_template_hashes_match` boolean could incorrectly pass when the second import path drifted (downstream protocol measurement has its own stronger guard, so this is not evidence that any historical model actually used drifted tools).

The preflight now reuses `audit_release.verify_shared_pins()` rather than maintaining a weaker private implementation. Missing files, malformed pins and changed bytes fail closed. Neither shared evaluator/writer implementation nor a scientific threshold was changed.

## Pass 2 — regression and edge cases

Added `tests/test_session_preflight_pins.py`: intact copies pass; changed or missing evaluator/writer files in either import path fail; malformed manifests fail. These tests use temporary copies, not mutations to real shared files. All eleven targeted tests passed (SOFTWARE-TEST, not HOLDOUT-DTI).

The base Python environment lacked NumPy and is externally managed. Created an ignored `.venv` and installed the numerical/test dependencies there. This is not a claim of exact lockfile reproduction: installed certifi is 2026.10.23 rather than the lockfile's 2026.10.19. No lockfile was rewritten to disguise that difference.

## H33 — supported explanation, not a causal leaderboard claim

Freshly retrieved [the pinned GEMSDOE32 recipe](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/scripts/run_h33_validation.py) through GitHub API. Its H33-2 flank sweep removes base dots at catalogue distances at or below the specified buffer. The repository's existing byte-forensic evidence identifies H33 as the parent minus the two-pixel collar, not a newly discovered geological corridor: [prior independent review](SESSION_4A5A945D_REVIEW.md), [forensic evidence](../docs/evidence/h86f-h33-forensics.json).

Why this could help: under a spatially tolerant metric, redundant dots can increase false-positive mass without increasing recovered truth credit. Pruning those dots can improve the ratio. Why it might hurt: dots near mapped traces can also recover withheld segments. Without hidden truth or an organizer receipt, the public artifact does not establish which mechanism caused the claimed improvement. The owner's H33 0.2778 and inconsistent leaderboard maxima 0.3195/0.4413 remain **OWNER-REPORTED**, not ORGANIZER-CONFIRMED or HOLDOUT-DTI. No claim that we beat them is justified.

Fault-trace prediction is not direct geothermal-vent identification. Conductivity, strain and potential-field contacts are ambiguous physical evidence, not vent labels.

## Ranked untested hypotheses — no implementation authorized

This carries forward four unimplemented proposals rather than falsely claiming they were newly invented. Ranking is qualitative expected information gain per cost, **not a numerical DTI forecast**. Exact layer identities, novelty scope, confounders and falsifiers are in [the machine-readable queue](../registry/h86g_hypotheses.json).

| Priority | Native layers and physical signature | Why potentially missing from catalogue / distinction | Mimic and cost |
|---|---|---|---|
| First | RTP magnetic band 2 and gravity band 13; local cross-spectral admittance breaks | Covered juxtaposition without a scarp; joint frequency-domain relation rather than existing curvature or signed-gradient concordance | Lithologic boundaries, remanence, source-depth variation; medium |
| Second | Bands 2/13; monogenic log-Gabor/Riesz phase congruency | Weak covered markers may retain phase agreement; different from amplitude-ranked ridges | Lava margins, dikes, survey seams; medium |
| Third | Bands 2/13/15; persistent saddle-to-extremum connections | Buried connectors missed by peak-only detection; topology rather than local Hessian ridges | Intrusive contacts, superposed sources; medium-high |
| Fourth | Conductivity band 17 and strain bands 7/8; persistent conductive necks with dilatation | Covered pathways; connectivity rather than broad conductive halos | Saline paleochannels, clay, interpolation bottlenecks; medium |

These require no proposed new external product, but the actual shared cached feature stack is still missing in this checkout. Native-layer restoration is not cache restoration. No new third-party data is claimed obtainable. None of these proposals passed a canary, holdout or uniqueness gate in this session.

## Pass 3 — release checks and remaining limitations

`audit_release.py` remeasured all 21 inherited artifacts and passed integrity with decision **DO NOT SUBMIT**. This is a current local SOFTWARE/FORMAT measurement, not a new HOLDOUT-DTI or proof of unique predictions. The earlier handoff's 18-artifact count is historical; do not silently present it as today's inventory. `build_site.py --check` and `check_site.py` passed, preserving the prominent download/authorization distinction and executive submission instructions. No generated HTML numbers were hand-edited.

The full test outcome is recorded in the session JSON card. Skips are not passes of scientific gates. No historical proof timestamp or model score was refreshed to manufacture new evidence.

Fresh official-source verification: the [reference README at aebe92f7](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md) explicitly supports CPU-only setup. Therefore GPU is not a universal training prerequisite. It does not establish our bands' physics or validate the leaderboard.

Official links for manual review, **not freshly fetched here**: [problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [GDR 1391](https://gdr.openei.org/submissions/1391), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). Egress permits GitHub/package hosts only. No DrivenData scraping, organizer login, submission receipt or quota receipt was used.

### Next work in dependency order

1. Explicitly assign a single method lane; resolve literal full-support registry overlap and grid-incompatible entries without privately changing thresholds or dropping records.
2. Restore and hash-bind the actual shared feature cache, preprocessing and visible-fault identities.
3. Freeze a rerunnable same-split comparator, then feature-alone canaries and buffered whole-segment hide-and-recover with the shared evaluator and paired spatial confidence interval. Respect the three-experiment/two-hour ceiling.
4. Require surface-before-placement and final-dot uniqueness gates before calling the shared writer. Reopen serialized bytes and validate finite footprint, range, grid and digest.
5. Only a separate selector may authorize a real slot under current quota evidence. A local validation pass alone must not enable an upload button.

Run card: [session-fb9725b9-run-card.json](session-fb9725b9-run-card.json). PR/merge outcome is reported separately in the session response.
