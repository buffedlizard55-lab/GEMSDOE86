# Current publication and H86N review — 2026-10-25 UTC

## Executive decision

**DO NOT SUBMIT.** No authorized candidate exists in this checkout. H86M-LT remains a downloadable historical GeoTIFF, but it is now reconciled as `verdict=negative`, `safe_to_submit=false`, `approved_for_weekly_slot=false`, and `submission_slots_used=0`. No organizer receipt exists, so no leaderboard score is claimed.

The repository now registers H86M-LT's TIFF/ZIP/receipt/card in the download and artifact joins, repairs the stale release branch, and exposes the lane as **audit-only**. Registration is an integrity repair; it is not scientific validation or upload authorization.

## What was verified

- H86M-LT TIFF SHA-256: `4067382cab05de80e85c22e717a8ea98e569f85933eedd9690651a7755eaebee`.
- H86M-LT local format and ZIP checks pass through the shared validators. The local scan has a separately recorded 655-raster scope, but it is not organizer clearance.
- H86M-LT has no shared hide-and-recover `HOLDOUT-DTI` with evaluator version, withheld-positive count and 95% CI. Its expected-DTI and SGMC-PROXY values remain projections/diagnostics, not scores.
- The restored native 19-band feature TIFF is SHA-pinned (`4371c82e…`), but `docs/evidence/feature-cache.json` points to a missing 982,332,800-byte shared cache. Prepared native arrays are not accepted as a shared-cache receipt.
- `scripts/run_h86n_eql.py` was invoked. It recorded a negative no-run card with `experiments_run=0`, because the literal registry preflight blocker and missing shared cache are both still active. No current H86N feature surface was constructed and no current slot was used.
- A parallel main-line history already contains an inherited H86N native-stack TIFF and an H86M-PFTE TIFF. Both are registered as negative audit-only artifacts. The H86N experiment reports `HOLDOUT-DTI` `0.030634 [0.017499, 0.045497]` with `gems57-pooled-hide-v2` and `11,321` withheld positives, but its paired controls cross zero and it does not prove use of the required shared cache; the current blocked no-run card remains authoritative for this review. No organizer score is claimed.
- Fresh official/trusted source checks are stored in [`official-source-verification-20261025.json`](official-source-verification-20261025.json), including the working USGS GeoDAWN page, the stale USGS 404 irregularity, DrivenData problem text, NLR rules, GBCGE INGENIOUS, GDR 1391, EPSG:32611, and the DrivenData reference repository.

## Ranked research queue

The full five-item register is [`registry/h86n_hypotheses.json`](../registry/h86n_hypotheses.json). “New” means no executed run card matching the method was found in this checkout on this date; it is not a global literature or fleet-wide novelty claim.

| Rank | Hypothesis | Layers / signature | Catalogue-missing rationale | Repo distinction | Qualitative expected DTI benefit | Cost / availability |
|---:|---|---|---|---|---|---|
| 1 | H86N-EQL pure earthquake-lineation anisotropy | Bands 16/10; 2- and 4-pixel Hessian ridge anisotropy and persistence | Blind active fault lineation versus compact/radial induced or volcanic swarm | Pure seismic primary surface, unlike prior multi-physics/supervised stacks | Highest qualitative priority; no numeric projection | Low–medium; native bytes exist, shared cache and visible-fold provenance missing |
| 2 | H86N-MTPS conductance–seismicity phase offset | Bands 17, 10, 16, 15, 8; signed cross-strike offset | Dipping conduit can offset deep seismicity from shallow clay cap | Directed phase geometry, not H86M-CNT raw topology | Medium qualitative potential | Medium; native bands present, cache blocker |
| 3 | H86N-PSCS potential-field source shape | Bands 13, 2, 5, 11, 18, 14; odd step versus even compact response | Reject dike/pluton compact ridges in favor of buried fault steps | Explicit response-shape likelihood, not generic gradient/phase rank | Medium-low qualitative potential | Medium; native bands present, cache blocker |
| 4 | H86N-BWPP broad low-relief warp persistence | Bands 12/19; sign-stable 300–1200 m warp | Degraded/buried broad fault warp after sharp scarp erosion | Broad-warp persistence, not sharp scarp or vent-flexure detector | Low–medium qualitative potential | Low–medium; native bands present, cache blocker |
| 5 | H86N-SWIR independent alteration boundary | Official external SWIR mineral-index layer plus Bands 2/13/17 | Blind vapor-zone alteration without scarp | No prior SWIR mineral absorption lane | Unknown until pinned and blind-tested | High; external bytes unavailable here, explicitly deferred |

No number in this table is a score. The top candidate's preregistration is [`H86N_EQL_PREREGISTRATION.md`](H86N_EQL_PREREGISTRATION.md).

## Three-pass verification

### Pass 1 — implementation

1. Read `PROMPT.md` and the complete request archive.
2. Reconciled the H86M-LT artifact into `docs/evidence/download-inventory.json` and `registry/artifact_cards.json`.
3. Added an `h86m_lt_unvalidated` branch to `scripts/audit_release.py`; it rejects projections as inherited HOLDOUT-DTI and requires the card's negative/no-slot state.
4. Rewrote the H86M-LT page and top README/site language so “safe to download” and “safe to submit” cannot be confused.
5. Added five hypotheses, a frozen H86N-EQL preregistration, source verification, a pure seismic feature module, and a fail-closed runner/run card.
6. Re-ran the full local artifact release measurement: 38 registered TIFFs and ZIPs, 38 local format/integrity passes, current decision DO NOT SUBMIT, 0 release-audit experiments and 0 slots.

### Pass 2 — bug and edge-case review

- Checked that H86M-LT receipt, TIFF, ZIP, inventory SHA and card SHA join exactly.
- Checked that H86M-LT card's historical `promote` label cannot satisfy the current `verdict`, `safe_to_submit`, or slot flags.
- Checked that an absent cache, a cache hash mismatch, a cache missing seismic channels, or a cache without per-fold visible-catalogue provenance all stop H86N before feature construction.
- Checked that the current H86N blocked card's planned numeric fields are null, while the separately preserved inherited native-stack card labels its measured HOLDOUT-DTI with evaluator, withheld-positive count and CI; neither is an organizer receipt.
- Checked official-source irregularities: the user-supplied old USGS GeoDAWN URL is a 404; the current USGS page/DOI is used. GDR/INGENIOUS pages describe data resources but do not prove local bytes, co-registration, or competition eligibility.

### Pass 3 — final requirement re-check

| Requirement | Result |
|---|---|
| Study prior results and official sources | Met for this review; source observations and irregularities are recorded, and owner-reported scores remain labeled as unverified. |
| Propose 3–5 new hypotheses with layers, signature, missing rationale, distinction, benefit, cost, data | Met: five proposals in the H86N register; benefit is qualitative, not a fabricated score. |
| Validate top candidate using shared cache/evaluator before slot | Correctly not met because the actual shared cache and fold-visible provenance are unavailable; the runner stops before experiment. |
| Generate a unique single-band GeoTIFF only after all gates | The current runner generated no TIFF; two inherited main-line negative TIFFs (H86N native-stack and H86M-PFTE) are retained for audit only and are not relabeled as current shared-cache clearance. |
| Obvious download/submit status, guide, name/note, run card, sources, limitations | Met for H86M-LT, inherited H86N/PFTE audit status, and the current H86N blocked card. No name/note is presented as an authorized upload. |
| Three passes | Met and documented here. |
| Organizer-confirmed score | None claimed; no organizer receipt exists. |
| PR and merge | A PR should be opened from the fixed Arena branch after final checks. The branch must not be switched or renamed; merge is a GitHub operation outside the scientific decision. |

## Remaining blockers / next actions

1. Obtain the actual hash-pinned shared template cache, including the H86N seismic channels and an explicit receipt that fold-visible catalogue transforms are rebuilt from visible faults only.
2. Resolve the literal full-support witness policy through the unchanged shared comparator/owner protocol; do not privately relax `0.90`/`0.70` thresholds.
3. If gates become available, execute only the preregistered H86N lane, run the canary and same-split baseline, then run surface and final-dot uniqueness before any writer output.
4. If and only if every gate passes, create a new writer TIFF/ZIP and register its exact SHA/name/note. Keep selector/weekly-slot choice separate.
5. If the lane is negative, preserve the card and any local audit artifact as a negative deliverable; do not claim it beats an organizer score.
