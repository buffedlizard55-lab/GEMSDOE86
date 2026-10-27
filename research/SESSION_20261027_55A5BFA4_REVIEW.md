# Independent review — session 55a5bfa4, 2026-10-27

## Executive decision: no file approved for competition upload

This session generated **no new TIFF**, ran **zero model experiments**, and used
**zero weekly slots**. The unique, high-scoring, approved TIFF requested by the
owner has **not** been achieved. Existing research downloads are not recommendations.
The full owner request remains linked from README through `research/REQUEST_20261027.md`;
its additional peer sites and unscored entries do not establish verified results.

### What was actually checked

- Reinstalled CPU dependencies in an ignored `.venv` (system Python disallows pip
  installation). Dependency installation succeeded with `requirements.txt`.
- Inspected current inputs, not historical restoration receipts:
  `docs/evidence/session-55a5bfa4-inputs.json`. Native feature TIFF, prepared arrays,
  and verified shared feature cache are absent. Sample and fault-label TIFFs match pins.
- Restored the pinned historical full-support registry witness using
  `scripts/restore_protocol_data.py --include-registry` (owner mirror, not official data).
- Re-measured all **49/49** registered TIFFs with `audit_release.py --measure-registry`:
  format/integrity pass, literal uniqueness fail. See `release-readiness.json`,
  `all-artifacts-registry.json`, and `latest-review-run-card.json` in `docs/evidence/`.
- Fixed the Focus-9 table's evidence join: the highest ledger entry must match
  both the registered method and the exact measured filename suffix. A changed
  champion now fails closed instead of inheriting a different raster's overlap.
- Added explicit per-site estimate and download-authorization columns. Missing
  organizer-calibrated estimates are displayed as unavailable, not invented.
  Historical source links are provided, not misleading upload/download buttons.

## Why H33 reportedly leads — evidence limits

The highest Focus-9 **OWNER-REPORTED** result is GEMSDOE32 H33, **0.2778**;
GEMSDOE36 is **0.2750**, GEMSDOE28 **0.2710**, GEMSDOE31 **0.2708**,
GEMSDOE33 **0.2632**, GEMSDOE25 and GEMSDOE30 **0.2600**, GEMSDOE24
**0.2477**, GEMSDOE27 **0.2449**. These are historical user claims from
`registry/prior_scores.csv`, **not ORGANIZER-CONFIRMED** results or predictions.
The generated executive summary contains each full submission identity and the
measured overlap source. No independent organizer receipt was obtained.

`focus9-forensics-20261026-rev2.json` measures champion overlap against H33
between **0.8672 and 1.0**: all fail the user's **0.70** stop. Different file
hashes do not make these scientifically distinct submissions under that rule.
The existing lineage analysis attributes H33 to pruning 2,545 catalogue-collar
dots from H27-4. Reducing redundant placement while preserving far-field
coverage is a plausible DTI tradeoff, not a demonstrated cause of its live result.
We cannot infer a score above 0.2778, 0.3195, or 0.4413 from that observation.
The latter two inconsistent leaderboard claims remain unverified.

## New scientific irregularity: H86T physical-band attribution

The latest lane's narrative and code need a fresh scientific audit before reuse.
`src/gems86/io.py:BANDS` maps **12 to det_elev**, **5 to iso_grav_anom_slope**,
**16 to ieq_n100a15**; its physical-override evidence describes **18 as a signed
eastward gravity derivative**, not scalar horizontal gradient. In contrast,
`src/gems86_knds/features.py:build_static_planes` names band 5 `elev_relief`,
band 16 `mt_2km_edge`, and computes the purported Bouguer sill veto from band 12.
This is a concrete attribution mismatch, not proof that the archived measured
DTI numbers are fabricated. The interpretation is not physically established by
those numbers. The H86T result remains negative; **do not repair its labels and
pretend its existing experiment validates a different physical mechanism**.
A corrected band contract requires a fresh preregistration, feature canaries,
fold-safe rerun, ablations, paired CI, and registry checks.

## Research queue and next session

The four existing ranked H86T proposals are in
`registry/h86t_hypotheses_20261027.json`. They are **not four new hypotheses from
this review**. Their assertions that all data are local are not true of this
fresh checkout. None is executable under the present shared-cache and literal
uniqueness constraints. This session therefore does not claim to satisfy the
request for 3–5 new viable, externally verified geological hypotheses.

Priority order:
1. Correct the scientific layer-identity contract across proposal, code, and
   feature receipts; do not privately change shared evaluator/writer bytes.
2. Restore the actual shared feature cache with implementation, source hashes,
   and visible-fault-mask provenance. Native TIFF restoration alone is insufficient.
3. Assign a single method lane. Reconcile the literal full-support-witness rule
   through an explicit owner protocol decision, not a hidden threshold change.
4. Only then preregister a distinct geological hypothesis and run at most three
   experiments, with per-feature canaries and a like-for-like paired holdout best.
5. Keep full-registry coverage and weekly selector authorization separate from
   local format success. No automated portal upload or quota assumption.

## Official-source and access boundary

Read the official organizer reference README at pinned commit
[aebe92f7c8a990f0e3443451b7a825d9afd6336b](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md)
through GitHub API this session. It describes both CPU and GPU environments;
GPU acceleration is useful, **not an absolute prerequisite for training**.
It does not authenticate our mirrored TIFFs or validate a scientific hypothesis.

Network access in this session is restricted to GitHub and package registries.
USGS, GDR, NLR PDF, Dropbox, and DrivenData sources could not be independently
retrieved here. Their links in the request remain review pointers, not freshly
verified sources. Per repository policy DrivenData must not be scraped.
No credentials were requested and no submission slot was spent.

## Three passes

1. Baseline: inspected instructions, request archive, input bytes, shared pins,
   all published TIFFs, witness, official reference README, and executive renderer.
2. Repair: exact identity binding and explicit unavailable estimates/download
   authorization; regression tests cover a new champion and a changed hash token.
3. Recheck: regenerated evidence-backed Pages, audited artifacts and site checks,
   and ran regression/full-suite tests (results recorded in PR). This is a
   reporting/integrity improvement, not a newly successful model experiment.

### Verification results

- `audit_release.py --measure-registry`: PASS, 49/49 locally valid artifacts;
  literal registry result remains DO NOT SUBMIT.
- `build_site.py --check` and `check_site.py`: PASS after final regeneration.
- Focus-9 plus site regressions: **8 passed**.
- Full suite: **1,136 passed, 24 skipped, 2 failed**, 58 subtests passed.
  The two failures were generated-HTML freshness checks while this session was
  actively modifying/regenerating the executive summary, not model assertions.
  After edits and regeneration, **both exact failing tests passed** (2/2).
  The full suite was not rerun in its entirety after that regeneration; do not
  advertise this as an uninterrupted all-green full-suite run.
- `git diff --check`: PASS. No shared-tool bytes or submission artifacts changed.
