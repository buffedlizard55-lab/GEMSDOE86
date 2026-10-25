# Review and autonomous verification — 2026-10-25

## Executive decision

**DO NOT SUBMIT. The requested new unique submission TIFF remains unfulfilled.** No new raster was copied, re-encoded, generated, or uploaded; no weekly slot was consumed. The existing download and executive-summary pages correctly distinguish review downloads from upload authorization.

This session adds an executable improvement, not another model: `scripts/review_repository.py` runs the existing release audit, tests, frozen-evidence verification, generated-site comparison, link checks, and download audit in three passes. It continues collecting diagnostics after failures, returns nonzero on failure, records output hashes and diagnostic tails, and writes a local JSON negative run card. Even a completely passing software audit never grants upload authorization. It neither replaces the shared evaluator/writer nor changes registry thresholds. It does not download data or remeasure the registry; inherited registry evidence remains historical.

## Reproduce without manual inspection

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/python scripts/review_repository.py
```

Report: `.cache/repository-review.json` (ignored, local). Per-command timeout defaults to 600 seconds. Reports cannot overwrite tracked source or published evidence through `--output`. Missing dependencies, failed commands and timeouts are explicit failures, not successes. The existing release auditor may refresh live audit JSON; frozen research evidence is not rewritten by this command.

## Three passes actually performed

1. Read the standing prompt, README and agent rules, inspected prior hypotheses, release gates, workflows, and restoration scripts. Initially checks failed because dependencies were absent. Installed the pinned lockfile in the ignored virtual environment rather than altering system Python.
2. Executed the new review command end to end. Release audit: PASS, decision **DO NOT SUBMIT**; 21 inherited TIFFs locally format-valid. Tests: **847 passed, 24 skipped, 42 warnings, 41 subtests passed**. These are software/format counts, not competition scores. Added eight tests covering continued execution after failures, timeout/error handling, output protection, and refusal to equate software success with submission authorization.
3. Frozen review, generated-site comparison, site links and download checks all passed. The site reports one historical promoted-for-selector-review download and no file authorized for upload. Reviewed the implementation against the request: no new scientific validation or claim of full uniqueness was introduced.

## H33: what the evidence can and cannot explain

The pinned-raster forensic analysis in [the prior review](SESSION_20261025_REVIEW.md) and `docs/evidence/h86f-h33-forensics.json` reports that H33 removes near-catalogue dots from its parent without adding cells. Under an asymmetric distance-tolerant objective, pruning redundant prediction mass can plausibly reduce false-positive cost while retaining nearby-truth coverage. This is a mechanism, not a causal attribution of the reported leaderboard increase.

The prompt's H33 value 0.2778 and mutually inconsistent current-best claims 0.3195 and 0.4413 are **OWNER-REPORTED**, not organizer-confirmed receipts. No live leaderboard or quota is established here. A better score is possible in principle, but this review supplies no defensible numeric prediction. Fault-trace prediction is not confirmation of geothermal vents.

## Ranked unimplemented hypotheses, before any implementation

Carry forward [the existing explicit four-hypothesis queue](../registry/h86g_hypotheses.json), rather than pretending these are newly invented or unique across every remote project. Novelty is scoped to the inspected repository; each entry includes a falsifier and non-fault mimic. No numeric DTI improvement is projected.

| Priority / cost | Layers and signature | Missing-fault rationale / distinction / mimic |
|---|---|---|
| First / medium | RTP band 2 + isostatic gravity band 13; windowed cross-spectral admittance breaks | Buried juxtaposition could alter the joint relationship without a scarp. Differs from local curvature and signed-gradient alignment. Mimics: lithology, source depth, remanence. |
| Second / medium | RTP band 2, gravity band 13; normalized multiscale monogenic phase agreement | Weak but spatially coherent buried markers might survive contrast changes. Differs from amplitude ridges. Mimics: dikes, lava boundaries, survey seams. |
| Third / medium–high | Bands 2, 13, 15 (basement depth); persistent saddle connections | Connecting buried structures could escape peak-only detection. Differs from local Hessian ridges. Mimics: intrusive contacts, erosional basement. Gravity-derived depth is not independent confirmation. |
| Fourth / medium | Conductivity band 17, shear band 7, dilatation band 8; persistent conductive necks | Tests narrow subsurface connectivity without requiring a mapped scarp. Differs from conductive halos/margins. Mimics: saline playa sediments and paleochannels. |

These require no proposed new external product, but the shared feature cache is absent; an obtainable raw owner mirror is not that cache. None is executable as a protocol-compliant new lane in this review. The prompt's promised single assigned method paragraph is absent. A complete valid registry and a frozen comparable holdout control remain prerequisites. The literal full-support overlap stop remains binding; no private waiver is added. Top-candidate HOLDOUT-DTI is **NOT RUN**: evaluator `gems57-pooled-hide-v2`, withheld positives/value/95% CI all null. Experiment budget used: zero.

## Sources and irregularities

Freshly retrieved through GitHub API: [official reference solution README at verified commit aebe92f](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md). It explicitly offers CPU training; the prompt's statement that a GPU is required is too strong. A GPU accelerates training but is not a universal prerequisite. That README directs users to acquire competition data separately; it does not supply the private data or prove mirror authenticity.

Manual-review pointers, **not freshly fetched or independently verified here**: [competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [H33 project](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html), [GDR 1391](https://gdr.openei.org/submissions/1391). No automated DrivenData access was attempted. Network access is restricted to GitHub and package registries; no claim of exhaustive literature research or all-site current verification is made.

## Next session

Resolve the lane and literal-overlap protocol inconsistency explicitly, restore and bind the genuine shared cache, reconcile invalid/incomplete registry rows, freeze matched spatial controls, then run feature-alone canaries and the top authorized hypothesis with the shared hide-and-recover evaluator. Placement follows surface uniqueness; serialization follows final-dot uniqueness. Promote only with a comparable paired holdout improvement; reserve actual weekly-slot selection as a separate step. Do not use the new software-review command as scientific clearance.
