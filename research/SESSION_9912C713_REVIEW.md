# Repository review — `arena/9912c713-gemsdoe86` — 2026-10-25

## Decision

**DO NOT SUBMIT any file.** This review produced no new raster, ran no geological experiment, and spent no competition slot. The highest-priority unique-TIFF submission requirement remains unmet. The repository has historical TIFFs downloadable for audit, but no TIFF is currently upload-authorized.

This was an audit-and-safety repair, not an attempt to bypass the parallel-run protocol. `PROMPT.md` contains no assigned single-method paragraph, the required actual shared feature cache is absent, and the unchanged literal witness rule rejects every nonempty allowed raster. Those are blocking facts, not reasons to invent a lane, rebuild the shared cache privately, or relabel a historical file.

## Post-review integration on the current branch

After this review's first validation, `main` advanced through PR #169 and then additional parallel research PRs. The synced tree contains upstream H86N-EQL, H86N-GSST, H86M-PFTE, H86M-BMGS, and H86M-SLCQ artifacts; those experiments were performed on their respective branches, not by this review. Each is retained with its own recorded disposition and none is authorized for upload. The current proposal queue excludes executed BMR, CNT, EQL, GSST, PFTE, BMGS, and SLCQ, retaining three preregistered checkout-scoped proposals (MTCS, SPBT, CHTD) as unassigned and blocked. The integrated tree has **41/41** locally valid research TIFFs, while the release decision remains **DO NOT SUBMIT**; this review itself ran zero experiments and used zero slots. H86M-LT's historical `promote` card remains distinct from its current negative protocol disposition. The initial three-pass findings below retain their at-the-time 36-artifact counts. Final integrated verification: **1,077 passed, 24 skipped, 58 subtests**; focused LT/EQL/GSST/PFTE/BMGS/SLCQ/queue checks passed **64**.

## What I found and corrected

### 1. A misleading “OK TO SUBMIT” H86M-LT page

The repository's README led with H86M-LT “PROMOTE — OK TO SUBMIT,” and `docs/h86m-lt.html` said “IS THIS FILE OK TO SUBMIT? YES” and called its download “the submission file.” That was inconsistent with the standing current decision in `PROMPT.md`, the full-support witness, the lack of a comparable buffered whole-segment HOLDOUT-DTI for this tomography lane, and the old lane card's false `safe_to_submit`/slot distinction.

The page now says **DO NOT SUBMIT** at the top; its download is explicitly **audit only**. The old lane-level `verdict: promote` is preserved as history, while its current `safe_to_submit` field is false and a separate current disposition explains the stop. The old “expected DTI” figures remain projections in the historical source card; none is described as a score or organizer result.

### 2. H86M-LT was an unregistered published binary

The first all-artifact release-audit replay found **36** TIFFs in `docs/downloads/` but only **35** inventory entries. The missing entry was H86M-LT. This meant the all-artifact audit failed closed, while its standalone page was still offering a “submission file.” I registered the existing TIFF, ZIP, and receipt as an audit-only artifact; no raster bytes were changed or copied. The artifact mapping now names a dedicated negative current-disposition record, and the audit code rejects any attempt to attach a HOLDOUT-DTI to this lane when none exists.

After correction, `scripts/audit_release.py --measure-registry` reported **FORMAT-VALIDATION: 36/36 local artifacts valid**, but the decision remains **DO NOT SUBMIT**. For each nonempty final dot field, the fresh **REGISTRY-MEASUREMENT** against the pinned witness is 1.0 under the literal direct-support comparison; the witness covers all **5,106,385 allowed cells**. This is not a complete-registry uniqueness certification.

### 3. Evidence inputs were not in the locations expected by the protocol

The first `scripts/protocol_preflight.py` call failed because `data/sample_submission.tif` was absent. I ran the repository's hash-pinned `scripts/restore_protocol_data.py --include-registry`; this restored the sample grid, existing-fault mask, and historical witness to the expected locations. The restore receipt expressly says the owner-supplied mirrors are **not organizer-authenticated**. This operation did **not** restore `training_features.tif` or the actual template cache.

The subsequent live input inspection found:

- `training_features.tif`: **missing** from `data/` and `data/bridge/`;
- prepared native-band arrays: **missing**;
- actual shared template feature cache: **not established**;
- sample grid and existing-fault mask: hash-verified owner mirrors, not organizer-authenticated data.

Thus the mandated shared-stack holdout cannot be run from this workspace. A historical manifest or feature hash in a run card is not present bytes and does not establish a current cache.

## H33 `0.2778`: what the evidence supports

The prompt's `0.2778` for H33 and the cited `0.2708` parent score are **OWNER-REPORTED**, not organizer-confirmed; this checkout has no submission-page receipt for them. The prompt gives inconsistent “current high score” claims (`0.3195` and `0.4413`), also without receipts. No comparison to those claims is validated here.

The reproducible raster forensic result already recorded in the repository is that H33 is the GEMSDOE28 D28 raster with **2,545 dots removed and zero added**, at the narrow catalogue collar. These are **RASTER-MEASUREMENT** counts, not scores. The shared metric's kernel-based truth credit saturates by taking a maximum rather than summing all nearby prediction mass, while non-crediting predictions still contribute false-positive cost. Therefore collar pruning could improve DTI if the removed dots added little hidden-fault credit while saving enough false-positive mass. It is a plausible metric mechanism, not proof that the edit caused the reported `+0.0070`; only the competition's private scored labels/receipt could establish that causal leaderboard result.

The H86M-LT card's historical full-registry scan (655 files) used a different like-for-like dot-field comparison and reported max forward overlap 0.649. The current pinned continuous witness is a different, literal support comparison and gives 1.0 for every nonempty allowed candidate. These readings are not interchangeable and the former does not waive the latter. The new current disposition therefore does not claim the old local scan was numerically wrong; it records that it is not current authorization under the binding rule.

## Ranked research queue: only proposals that remain candidates

Ranking below is qualitative expected information gain per implementation cost, **not a score forecast**. The source-code scan was limited to this checkout; it does not prove fleet-wide novelty. No candidate is assigned to this session, and no experiment is authorized until an owner explicitly assigns one method paragraph and the protocol stops are resolved.

| Rank | Proposal and layers | Target signature and why it could reveal a catalogue-missing fault | Difference from executed local methods | Named non-fault mimic | Qualitative potential / cost / data |
|---|---|---|---|---|---|
| 1 | **Gravity step-versus-compact-source shape test (GSST)** — Band 13 `iso_grav_anom`, Band 5 `iso_grav_anom_slope`, Band 11 `iso_grav_anom_vg`, Band 18 `iso_grav_anom_hg`. | At frozen scales compare signed gradient-profile width and polarity to explicit extended-step versus compact-source responses. A covered basement step may be expressed as a coherent extended edge without a surface scarp; a compact anomaly maximum alone is less diagnostic. | No explicit competing step/compact forward-source likelihood was found in `src/` or `scripts/`. H86M-BMR tests a gravity/basement residual and H86F-GZZD/H86H-PSTD test derivative/tensor structure; neither is this specific shape-model comparison. Band 11 is a signed southward horizontal derivative, not vertical gravity. | Elongate intrusion, volcanic contact, or overlapping compact sources that form a linear edge. | **Low-to-medium qualitative potential; medium cost.** Uses existing competition bands; no new external data, but blocked because current feature raster/cache is absent. |
| 2 | **Microseismic density-lineation tensor (proposal only)** — Bands 10 `deq_n100a15` and 16 `ieq_n100a15`, with Band 7 `geod_shearrate` only as a predeclared corroboration/control. | Estimate local orientation coherence and anisotropic scale of seismic-density patterns, then test if persistent lineations align with independently measured shear. An unmapped active structure can host aligned microseismicity even where surface expression is weak. | Existing lanes use seismicity density/intensity in broader strain, conduit, or classifier fusions; an initial search found no standalone, orientation-coherence test as the candidate. This is **checkout-scoped novelty only**, not a claim it has never appeared in the 92-project fleet. Band semantics and smoothing scales require verification against actual source metadata before preregistration. | Induced geothermal seismic swarm, volcanic seismicity, or gridding/interpolation anisotropy. | **Low qualitative potential; medium-high cost.** Native layers only; no additional external source proposed. Still blocked by missing native stack and no assigned lane. |
| 3 | **Threshold-persistent conductivity necks versus continuous neck score** — Band 17 `cond_surf`, Band 8 `geod_dilaterate`, Band 7 `geod_shearrate`. | Track connectivity and neck-width persistence across frozen conductivity thresholds; require independent strain consistency. A covered fluid pathway could connect conductive areas without a surface scarp. | H86M-CNT already ran a continuous high-pass conductivity-neck score times positive dilatation and was negative; an explicit threshold-persistence/topological test is different but close enough that it must be treated as a risky refinement, not a wholly new concept. No exact threshold-filtration implementation was found in the scanned source. | Saline playa, clay-rich paleochannel, or interpolation bottleneck. | **Low potential; medium cost and high confounding risk.** Native layers only, but needs the missing native feature stack and a preregistered null test. Do not rerun the H86M-CNT score unchanged. |

The earlier ranked queue's **BMR** and **CNT** items are no longer “untried”: current tracked H86M run cards show both were executed. **HOLDOUT-DTI** (evaluator `gems57-pooled-hide-v2`, 11,321 withheld positives, 95% CIs as recorded in the cards) was 0.0220 [0.0086, 0.0384] for H86M-BMR and 0.0408 [0.0257, 0.0575] for H86M-CNT. Both were negative; do not rename or repeat them as new methods. Their cards are [`BMR`](../docs/evidence/h86m-bmr-run-card.json) and [`CNT`](../docs/evidence/h86m-cnt-run-card.json). These historical results are not recomputed in this review.

### External-data availability

The three proposals above use competition feature bands, so no new third-party layer is necessary. That does not make them runnable now. The official [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) is login-gated under the repository's recorded access limitation; automated portal access is disallowed by `AGENTS.md`. A mirrored native TIFF may be integrity-pinned, but the actual current file and shared cache are absent, and mirror integrity does not prove organizer provenance. No new external dataset is claimed obtained or validated.

## Pass log

### Pass 1 — understand requirements and the current branch

Read `PROMPT.md`, the complete `research/REQUEST_20261025.md`, `README.md`, `AGENTS.md`, current machine reports, and the H86M-LT, BMR, and CNT evidence. Reviewed repository status and the current source/code inventory. Found a live conflict: README/page called H86M-LT “OK TO SUBMIT” while the standing prompt says no artifact is authorized. Found the missing inventory mapping by comparing the published TIFF paths with the actual inventory.

### Pass 2 — reproduce the blocker and repair publication state

The initial workspace audit showed the feature TIFF/cache was absent. Initial preflight failed on the missing conventional sample-submission path; restored only the pinned protocol inputs and historical witness, recording their owner-mirror provenance. A fresh preflight then measured the full-support witness stop. Registered the pre-existing H86M-LT artifact with negative current status, kept its historical scientific card identifiable, added a fail-closed current-disposition parser branch and regression tests, and changed the H86M-LT page/README to make “audit only / DO NOT SUBMIT” unmistakable.

### Pass 3 — rerun checks and preserve remaining limitations

Refreshed the generated pages and download report from the audited inventory. Re-ran the all-artifact measurement; all 36 published TIFFs are format-valid locally, but all remain blocked by the literal witness policy and none is authorized. Focused regression/request/publication checks after the final documentation update: 35 passed. Final full suite before the documentation-only README correction: 1,026 passed, 24 skipped, 58 subtests passed. `audit_release.py --measure-registry` passed its integrity audit with 36/36 local format-valid artifacts and all still DO NOT SUBMIT; `audit_downloads.py`, `build_site.py --check`, and `check_site.py` passed. Skips are not evidence that unavailable-data experiments succeeded. No model, surface, placement, candidate TIFF, external layer, or slot was used.

## Limitations and next work

1. Obtain the actual competition feature raster and the **actual shared template feature cache** with input, preprocessing, and visible-mask provenance; do not reconstruct and mislabel a private cache.
2. Resolve the literal witness contradiction in the shared/upstream protocol, with an explicit documented policy change if authorized. No private threshold or support-rule change is acceptable.
3. Assign exactly one method paragraph. Then use the shared evaluator and writer, buffered whole-segment hide-and-recover, visible-only catalogue-derived features, pixel-exact visible-fault masking, pooled DTI (α=0.2, β=0.8, 300 m triangular kernel), and paired physical-block uncertainty intervals. Run isolated-feature leakage canaries first; AUC >0.90 is a stop pending proof.
4. Compare the candidate surface before placement and final dots after placement against a complete current registry. A single witness can reject but cannot clear uniqueness.
5. Keep slot selection separate. No current weekly cap or organizer receipt was available here; do not spend a slot on an unvalidated hypothesis.
6. After code/evidence update, rerun `scripts/audit_release.py --measure-registry`, `scripts/audit_downloads.py`, `scripts/build_site.py --check`, `scripts/check_site.py`, and the full test suite before publication.

## Source links for manual review

These sources are cited for manual verification. This review did not automate or scrape DrivenData.

- [DrivenData competition problem statement](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData competition data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login-gated)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [NLR/DOE GEMS Prize rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN official data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [DOI](https://doi.org/10.5066/P93LGLVQ)
- [DOE/NREL GDR INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391)
- [EPSG:32611](https://epsg.io/32611)

## Run card

```json
{
  "hypothesis": "No geological hypothesis lane was assigned or tested; this was a submission-readiness and publication-safety review.",
  "mechanism": "A pinned full-support historical witness covers all allowed cells, so the unchanged literal overlap gate rejects every nonempty allowed prediction.",
  "named_non_fault_process": "Not tested because no candidate surface or dots were constructed.",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "evaluator_version": "gems57-pooled-hide-v2",
    "withheld_positives": null,
    "value": null,
    "ci95": null,
    "status": "NOT_RUN_NO_LANE_ASSIGNED"
  },
  "correlation_overlap_vs_registry": {
    "evidence_class": "REGISTRY-MEASUREMENT",
    "candidate_surface": null,
    "candidate_final_dots": null,
    "witness_sha256": "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be",
    "allowed_pixels": 5106385,
    "uncovered_allowed_pixels": 0,
    "any_nonempty_allowed_candidate_forward_overlap": 1.0,
    "overlap_limit": 0.7,
    "scope": "One pinned witness; sufficient negative only; registry incomplete"
  },
  "raster_sha256": null,
  "validator_output": {
    "evidence_class": "FORMAT-VALIDATION",
    "published_artifacts_checked": 36,
    "local_format_passes": 36,
    "h86m_lt_no_nan_or_inf": true,
    "h86m_lt_values_in_0_1": true,
    "h86m_lt_crs": "EPSG:32611",
    "h86m_lt_shape": [3730, 3292],
    "h86m_lt_transform_matches_sample": true,
    "upload_authorized": false
  },
  "submission_name": null,
  "note": "Review only; no new TIFF, experiment, or weekly slot. Historical downloads are audit-only.",
  "verdict": "negative"
}
```
