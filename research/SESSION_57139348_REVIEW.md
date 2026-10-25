# Repository review — 2026-10-25 — session 57139348

## Decision and work completed

**DO NOT SUBMIT.** No new raster, experiment, slot selection or upload. The requested new, unique, scientifically cleared TIFF is not delivered. An inherited TIFF is now downloadable through the audited dashboard, explicitly for research only. Reusing it with a new filename would not meet the request.

Read PROMPT.md and the full README before changes. No single method paragraph was supplied; this review stays in release-integrity work rather than silently assigning a parallel scientific lane. The standing owner request is preserved in PROMPT.md and README's embedded archives. Core values mean retaining falsifiable evidence, not claiming a win from an in-sample fit.

## Pass 1 — concrete release failure and repair

At entry `build_site.py --check` failed with `Unregistered or missing published TIFF`. `check_site.py` identified the H86M-LT TIFF and ZIP, an unauthorized “OK TO SUBMIT? YES” page and `safe_to_submit=true`. The new index registration preserves the raster SHA and bytes; nothing was clipped, copied, renamed or generated. The shared audit now recognizes `h86m_lt_unvalidated`, requires negative/no-authorization status and refuses invented holdout values. The original promotion claim is preserved in the card as superseded history.

## Pass 2 — scientific and statistical review

- H86M-LT fits aggregate **owner-reported** scores, not submission-page receipts. They are not ORGANIZER-CONFIRMED. Its fitted expected-DTI values are projections, not HOLDOUT-DTI. No buffered whole-segment hide-and-recover result, withheld-positive count or confidence interval is recorded for this candidate.
- Its single belief-map SGMC AUC is not the requested isolated-feature holdout canary. SGMC is an external proxy, not withheld competition labels.
- `research/H86M_LT_PREREGISTRATION.md` records amendments A, B and C after seeing placement results. The final coarse-belief delta is negative, and amendment C relaxes the original all-beliefs-win gate. This is exploration, not independent confirmation. LOO prediction error is not a paired confidence interval for a new candidate's improvement.
- `scripts/check_h86m_full_registry.py` computes Pearson for a continuous belief surface. Binary/binary Pearson equals tied-rank Spearman, but a continuous/binary comparison does not generally have that equivalence. Its historical surface number cannot establish the required rank gate. It also reconstructs inputs by executing an ignored `.cache/h86m/e2_tomography.py`; those source bytes are absent here. Do not claim reproducibility or a fresh full-registry uniqueness pass.
- No training data or shared cached feature stack is established by the fresh workspace inspection (`docs/evidence/session-57139348-inputs.json`). Restoring the proof witness is not restoring training features. GPU access is not the only blocker.

### Why H33 may have helped; can we beat the owner-reported 0.2778?

The repository's [H33 forensics](H33_ANALYSIS.md) and [LT review](H86M_LT_REVIEW.md) report that H33 pruned catalogue-collar dots from its parent, rather than discovering additional geological structures. In the shared DTI formulation, removing predictions that contribute more false-positive mass than recovered weighted truth can increase the ratio. That is a plausible mechanism, not organizer-confirmed causal attribution. Kernel overlap, mapped-fault masking and NaN handling matter; the historical names and a score alone cannot isolate them. No honest evidence in this review establishes a higher live score. The prompt also gives incompatible leaderboard-best claims; none is treated as current without a dated organizer receipt.

### Ranked proposals before implementation

These are *specific unexecuted variants*, not global novelty claims. Search of scripts/src found related families already executed; those are disclosed. Ranking is qualitative expected validation information per cost, **not a projected score**. All use native layers and require the shared cache to become available before viability; no new external source is assumed obtainable.

| Rank | Specific layers and signature | Why possibly catalogue-missing; non-fault mimic | Difference and cost |
|---|---|---|---|
| 1 | `iso_grav_anom`: explicit competing extended-step versus compact-body forward response fit across frozen widths, with blocked fitting | Buried density steps can lack a mapped scarp; elongated intrusive contacts mimic them | GSST was proposed, not executed as an explicit competing-source likelihood in this checkout. Unlike GZZD/tensor/saddle methods, compare physical response models. Medium cost; first test against matched raw-gradient control. |
| 2 | `cond_surf`, `geod_dilaterate`: threshold-persistent necks with **matched randomized-neck conditional nulls** | Concealed permeability pathways; saline paleochannels mimic them | CNT already ran and did not establish improvement; this is a specific conditional-null falsification extension, not a claim CNT is new. Medium cost, lower prior chance of improvement. |
| 3 | `iso_grav_anom`, `depth_to_base_surf`: **density-contrast stability intersection** of forward residual edges across frozen physical contrasts | Buried basement offset; sediment-density variability/model error mimic it | BMR already ran negatively. New element is requiring stability across density contrasts before ranking, rather than reusing the failed single fit. High cost, low prior confidence because basement depth is gravity-derived. |

Top-candidate validation is **blocked, not passed**: no authenticated shared feature cache, no assigned method paragraph. Freeze whole-segment buffered splits; derive all catalogue features from visible segments; run isolated-feature AUC canaries; use unchanged pooled evaluator; compare paired spatial-block CI against the best on exactly those folds. Stop at duplicate surface or dots. Never choose a submission using a maximum across different holdout designs.

## Pass 3 — end-to-end recheck

Registered LT in both indexes; restored the pinned dense witness and remeasured final-dot stops with the shared audit (not the complete fleet scan). The literal witness stop remains unchanged. Rebuilt the generated homepage and executive guide so LT appears with an audit-only download. Revalidated all published TIFFs/ZIPs and added regression tests against status or score laundering. See final PR for executed test results.

## Sources and access limits

- Official organizer reference implementation (GitHub repository metadata verified this session via `gh api`; source not freshly re-audited): https://github.com/drivendataorg/gems-prize-reference-solution — source for the reference task, not independent confirmation of local mirror provenance.
- Competition description (manual review link; not fetched): https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official rules PDF (manual review link; not fetched): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- USGS GeoDAWN source (manual review link; not fetched): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- Local executable evidence: `vendor/gems57/metric.py`, `scripts/audit_release.py`, `scripts/check_h86m_full_registry.py`; pinned witness: `research/registry_witness_pin.json`.

Network here permits GitHub and package registries, not USGS, Dropbox or the rules-PDF host. No live leaderboard, rules document or geological literature was freshly verified; no source is represented as read when it was not. DrivenData automated access is prohibited by repo instructions. No competition login, portal receipt or weekly quota is available. No claim of worldwide uniqueness, high-score guarantee, verified vents, or complete prompt fulfillment is warranted.

Next session: restore/provenance-pin the shared cache with fold-visible-mask identity; assign a method lane; validate GSST with frozen controls; replace the LT Pearson diagnostic with hash-bound Spearman before any uniqueness claim. Do not relax gates after seeing outcomes. A separate selector must verify available quota before any upload.

### Executed verification results

- Initial full suite: 1,028 passed, 24 skipped, one failed (stale README download count); 58 subtests passed. Fixed that count; affected review/archive regression rerun: **40 passed**. Full suite was not rerun after the one-line count correction; do not report an all-green full-suite rerun.
- `audit_release.py --measure-registry`, `build_site.py --check`, `check_site.py`, `audit_downloads.py`, `build_review_card.py --check`, and `git diff --check`: pass after repair. All **36** TIFF/ZIP downloads pass local format/integrity checks, not scientific promotion.
- Official GitHub repository metadata for the organizer reference solution was obtained with `gh api`. Non-allowlisted scientific/rules URLs remain review links, not freshly retrieved evidence.

## Later branch-integration verification (PR #162, after main `2c8d518`)

A subsequent branch reconciliation retained this review's negative findings and ranked proposals, changed the H86M-LT run card's operative verdict to `negative` while preserving the prior promotion claim as superseded history, and explicitly remeasured the pinned-witness overlap at 1.0 (>0.70). The latest full local suite on the integrated tree passes: **1029 passed, 24 skipped, 58 subtests passed**; 48 existing Rasterio deprecation warnings. Release and download integrity audits each cover 36 artifacts; site checks pass. These are local verification results, not scientific validation or organizer confirmation. No holdout, canary, experiment, slot selection, or submission occurred.
