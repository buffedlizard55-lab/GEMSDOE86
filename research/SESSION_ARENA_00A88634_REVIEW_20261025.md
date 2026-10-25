# Repository review — session `00a88634` (2026-10-25 UTC)

> **Post-merge addendum (2026-10-25):** This branch later merged `origin/main` at `6a859ed` (PR #157). The upstream merge added H86M-BMR, H86M-CNT, H86M-DAMAGERING and H86L-VFGR records/artifacts from separate sessions. They are not experiments performed by session `00a88634`. Their cards report: H86M-BMR HOLDOUT-DTI **0.0220 [0.0086, 0.0384]** (gems57-pooled-hide-v2; 11,321 withheld positives), paired delta vs raw gravity **−0.0144 [−0.0257, −0.0025]**; H86M-CNT HOLDOUT-DTI **0.0408 [0.0257, 0.0575]** with paired CIs vs both controls crossing zero; H86M-DAMAGERING HOLDOUT-DTI **NOT RUN**; and H86L-VFGR HOLDOUT-DTI **0.0313 [0.0230, 0.0395]** (same evaluator/withheld count), paired delta vs raw-edge **−0.0054 [−0.0082, −0.0026]**. H86L-VFGR records `shared_feature_cache_used=false` and its final dots overlap 70.13% within 3 px of GEMSDOE46, exceeding the 0.70 gate. All are negative/not submission-authorized as recorded upstream; none is an organizer-confirmed score. A fresh audit of this merged workspace still finds native training features, prepared arrays, labels, and the required shared cache missing; the upstream restoration statement describes its earlier environment only. The live release inventory now lists 35 inherited artifacts, not the 32 in the original pass-3 snapshot. The untried queue was refreshed: BMR/CNT are excluded as already executed; GSST, H86K-CWQA and H86K-BFAH remain proposals, with no new experiment authorized or run.


## Decision first

**DO NOT SUBMIT any repository TIFF. No new candidate was generated, no geological experiment was run, and no weekly slot was selected.** The visible TIFFs are downloadable only for audit/reproducibility. Their local format checks are not organizer acceptance or upload authorization. The requested new-lane work is blocked, not silently replaced with a previous submission.

This session had no single method paragraph assigned. The exact required shared-template feature cache is absent. In addition, the unchanged literal 70% overlap gate is unsatisfiable for nonempty predictions under the pinned witness measured below. These are stop conditions; I did not weaken thresholds, create a private feature cache, or treat a format-valid historical raster as this session's unique candidate.

## Three-pass work and verification

### Pass 1 — inspect repo, prompt and live inputs

Read `PROMPT.md`, `README.md`, and `AGENTS.md` before making changes. The full request is archived in `PROMPT.md`, `research/REQUEST_20261025.md`, and the README's request section. `AGENTS.md` requires the same template tools, explicit evidence classes, full fail-closed registration, and separation of research promotion from slot approval.

Installed the pinned Python requirements in the ignored local `.venv` solely to run the repo's audits. `scripts/audit_workspace_inputs.py` measured the current checkout:

- `data/training_features.tif` and `data/bridge/training_features.tif`: **MISSING**.
- Native prepared-band cache: **21/21 arrays missing**; receipt is stale/incomplete.
- Actual shared template feature cache: **SHARED_CACHE_NOT_ESTABLISHED**; its recorded lane-cache file is absent and lacks the required shared-template identity contract.
- `existing_faults.tif` and `sample_submission.tif`: SHA-pinned mirror copies pass integrity checks. Their mirror pins authenticate byte identity, **not organizer origin**.
- `labels.tif` is not present. The existing-fault TIFF is only a hash-identified mirror, not a substitute authenticated labels download.

The two small protocol rasters and a historical registry witness were restored only from pinned owner GitHub mirrors to run fail-closed protocol audits. Their receipts explicitly state `organizer_authenticated=false`. This is not competition-data authorization or a restoration of the shared feature stack.

### Pass 2 — reproduce release failures, fix bookkeeping only

The first full review found the known H86L-FMC publication-integrity defect: its TIFF and ZIP existed under `docs/downloads/` but were absent from `docs/evidence/download-inventory.json` and `registry/artifact_cards.json`. Before repair, `audit_release.py`, `build_site.py --check`, `check_site.py`, and the full test suite failed; pytest reported **18 failed, 985 passed, 24 skipped**. The failures shared the unregistered published artifact as their primary trigger.

Fixed the fail-closed release audit's schema handling for the existing H86L-FMC run card, registered its exact TIFF hash and sidecar as **negative / audit-only**, and added regression checks that preserve the leakage-suspect evidence class, negative decision, and zero-slot state. No raster bytes, thresholds, run-card result, holdout result, or upload authorization were changed. This resolves the earlier `IR-H` bookkeeping defect; the original finding remains in `IRREGULARITIES.md` with a dated resolution note.

### Pass 3 — remeasure, regenerate and retest

After registering H86L-FMC, `scripts/audit_release.py --measure-registry` completed:

- **32/32** registered research TIFFs passed local format/integrity checks.
- All **32/32** final rasters were compared with one pinned witness, not the complete public fleet.
- The repository decision remains **DO NOT SUBMIT**; `safe_to_submit=false`, `approved_for_weekly_slot=false`, and `submission_slots_used=0`.

The witness preflight (`scripts/protocol_preflight.py`) measured **5,167,373** footprint cells, **5,106,385** allowed cells, and **0** allowed cells not positive in the witness. Thus any nonempty allowed dot set has literal forward overlap **1.0**, above **0.70**. The scope is one hash-pinned historical raster; it proves a negative for the literal rule and does **not** establish complete-registry uniqueness. No new candidate surface or final dots existed, so candidate Spearman correlation and candidate dot overlap are **not measured**, not zero.

The H86L-FMC artifact's own archived run card reports **HOLDOUT-DTI** (`gems57-pooled-hide-v2`, 11,321 withheld positives) `0.0000 [0.0000, 0.0000]`; it explicitly labels the holdout leakage-suspect because the fleet input has full-catalogue lineage. Its recorded dot overlap is 0.886 against GEMSDOE63, above the 0.70 threshold. Those are inherited H86L lane measurements, not results from this review.

### H33 score interpretation (careful attribution)

The prompt's H33 `0.2778`, parent `0.2708`, and current leaderboard claims `0.3195` and `0.4413` are **OWNER-REPORTED**, not **ORGANIZER-CONFIRMED**: this repo contains no matching submission-page receipt. They are not verified scores from this review.

The local H33 forensic comparison establishes a limited raster fact: H33 removes 2,545 dots from the D28 parent in the mapped-fault collar while adding none. Under the implemented DTI, `TP_w` credits the maximum prediction kernel at each truth pixel, while prediction mass not credited to truth contributes to false-positive cost; consequently, pruning redundant low-marginal-credit predictions *can* improve the metric. But mapped-collar distance is not equivalent to withheld-fault distance: a removed dot may have covered an unmapped fault, and a retained dot may be redundant. Without an organizer receipt or controlled, paired replay on the same hidden truth, the pixel edit does not explain H33's reported score causally. It also cannot establish a recipe for beating 0.2778 or leaderboard position. Full analysis: [`H33_ANALYSIS.md`](H33_ANALYSIS.md), [`H33_INTERPRETATION_REVIEW.md`](H33_INTERPRETATION_REVIEW.md), and the locally measured lineage card [`session-679d92e7-h33-lineage.json`](session-679d92e7-h33-lineage.json).

The metric used by the repo is a 300 m triangular kernel (3 pixels on the 100 m grid), with alpha 0.2 and beta 0.8; see the pinned local transcription/implementation in [`vendor/gems57/metric.py`](../vendor/gems57/metric.py). This metric explanation is not itself evidence for the owner-reported score.

## Ranked hypotheses to consider after the gates are resolvable

These are **proposals, not experiments or score projections**. “Not run” means not executed as a candidate experiment in this checkout; it does not claim scientific or fleet-wide novelty. The methods use native competition bands and need no new external dataset, but no current holdout evaluation is possible without inputs and the required shared cache. Details and preregistered falsifiers are in [`registry/followup_hypotheses_20261025.json`](../registry/followup_hypotheses_20261025.json).

| Rank | Hypothesis and exact layers | Target signature and why it could reveal an unmapped fault | Difference from implemented methods here | Named non-fault mimic | Expected value / cost |
|---|---|---|---|---|---|
| 1 | **Basement-interface gravity mass-balance residual (BMR)** — Band 13 `iso_grav_anom`; Band 15 `depth_to_base_surf`. | Fit a fold-safe forward gravity response from basement relief, then test for a localized persistent cross-strike residual. A buried basement displacement beneath basin fill may lack a mapped surface scarp. Band 15 is gravity-derived, so it is not independent corroboration; circularity must be tested. | Existing gravity/basement step pairs, gravity tensors, gradients, saddles and edges do not implement this exact frozen forward-response residual test. | Lateral sediment-density variation, smoothing/model error in the gravity-derived basement surface, or model-edge ringing. | Highest qualitative priority; moderate confidence; high cost (units/sign, density sensitivity, fold-safe fitting, boundary controls). |
| 2 | **Gravity step-versus-compact-source shape test (GSST)** — Bands 13 `iso_grav_anom`, 5 `iso_grav_anom_slope`, 11 `iso_grav_anom_vg`, 18 `iso_grav_anom_hg`. | Compare multiscale derivative patterns to extended-step versus compact-source responses. A concealed extended basement step may yield coherent cross-strike shape without relying on catalogue proximity. Band 11 is a signed southward directional derivative, not vertical gravity; Band 18 is signed eastward; Band 5 is horizontal-gradient magnitude. | Explicit competing-source likelihood is distinct from existing pointwise gravity edges/tensors and saddle topology. | Elongated intrusive contact, basin-margin facies boundary, or overlapping compact sources. | Low-to-medium qualitative priority; medium cost (scale-matched templates and depth/filter sensitivity). |
| 3 | **Conductivity-neck topology conditioned on strain (CNT)** — Band 17 `cond_surf`, Band 8 `geod_dilaterate`, Band 7 `geod_shearrate`. | Track narrow conductive connections across frozen thresholds and test whether they co-locate with positive dilatation/coherent shear. Concealed fluid pathways can be expressed without a surface scarp. `cond_surf` is surface conductance, not depth-resolved MT or proof of geothermal fluid. | Persistent component-neck topology differs from conductivity maxima, margins, halos, and generic conductivity/strain fusion. This is a preregistered reserve idea, not a previously validated candidate. | Saline playa sediment, clay-rich paleochannel, or interpolation/gridding bottleneck. | Lowest qualitative priority due to nonspecific conductivity; medium cost (threshold persistence and spatially randomized controls). |

### Top-candidate validation disposition

BMR is not validated. `scripts/audit_workspace_inputs.py --require-native` exits nonzero because the native training TIFF is absent; the shared cache is also absent. No surface can be constructed from the required shared stack, no feature-alone leakage canary can run, and no hide-and-recover evaluator run is permissible. This is a **blocked validation**, not a negative HOLDOUT-DTI and not evidence against BMR. All three hypotheses need only native competition data; no third-party data is needed to start their first controlled test. For independent later corroboration, the official [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and [DOE Geothermal Data Repository INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391) are available references; neither substitutes for the blind holdout.

## Submission instructions and limitations

- The executive summary and [`docs/SUBMIT.md`](../docs/SUBMIT.md) describe the single-band GeoTIFF / one-TIFF ZIP upload process, required CRS, dimensions, transform, and note/name fields. The `DO NOT SUBMIT` banner is decisive: **do not upload any current repo TIFF**.
- The original rejected file was not supplied, so its exact `[0, 1]` range error cause cannot be diagnosed. Current audit-only artifacts are locally checked for finite in-range predictions and grid compatibility, but this cannot prove portal acceptance.
- Automated access to DrivenData is deliberately not performed (project policy and portal authentication restrictions). A legitimate organizer receipt/score requires a human-readable competition submission receipt; none is recorded.
- A full registry is not certified by the one-witness rejection. Some historical registries contain invalid/incompatible rows; no current candidate has surface-and-dot measurements across every registry raster.
- The current upstream request specifies whole-segment buffered hide-and-recover, catalogue-derived features from visible faults only, exact mask of visible faults, pooled DTI, 95% CI and a feature-alone AUC canary. The checkout does not have the required shared template cache; the prior run-card/metric archives must not be retroactively described as satisfying this new lane protocol.
- The next authorized step is to restore/re-establish the actual shared template cache with provenance and satisfy the literal registry-gate disposition **without a private threshold change**. Only after that: assign one method paragraph, preregister the exact method, run a top-candidate holdout before a slot selector, cap at three experiments/two hours, and retain negative outcomes.

## Official/technical links for manual review

- [DrivenData GEMS problem statement](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/).
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- [DOE/NLR solicitation PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and); [DOE GDR INGENIOUS #1391](https://gdr.openei.org/submissions/1391).
- [EPSG:32611](https://epsg.io/32611).

## Run card — this review (one JSON card)

The machine-readable current card is [`docs/evidence/latest-review-run-card.json`](../docs/evidence/latest-review-run-card.json). It records no candidate hash/name or format result because no new candidate was constructed; inherited artifact-format checks are reported separately in the release audit. Final verification after the bookkeeping repair: `pytest -q` = **1005 passed, 24 skipped, 58 subtests passed** (48 Rasterio pending-deprecation warnings); `audit_release.py` = **32/32 format/integrity pass, DO NOT SUBMIT**; `audit_downloads.py` = **32 TIFFs/receipts revalidated**; `build_site.py --check`, `check_site.py`, `build_review_card.py --check`, and `git diff --check` all pass. Earlier intermediate check failures were corrected and these are the final results.

## Post-merge verification (2026-10-25)

The original three-pass findings above are preserved as the pre-merge snapshot. After integrating `origin/main` at `6a859ed`, this review re-audited live inputs and found `native_inputs_available=false`, `native_bands_available=false`, `shared_template_feature_stack=false`, with prepared arrays absent; no holdout could be run. The upstream session's data restoration and H86M/H86L-VFGR scores remain archived in their own cards and must not be attributed to this review. The merged inventory is 35 inherited artifacts; release audit and download validation each pass 35/35 local formats/integrity, while the repository decision remains **DO NOT SUBMIT**. On this merged tree, `.venv/bin/pytest -q` passes **1,022 tests, 24 skipped, 58 subtests** (48 Rasterio pending-deprecation warnings); `build_site.py --check`, `check_site.py`, and the frozen review-card check pass. No experiment, candidate TIFF, slot selection, or upload authorization resulted from the merge.

The pre-merge ranked list above is superseded: BMR and CNT were subsequently run upstream, so they are not untried candidates. The current queue is [`registry/followup_hypotheses_20261025.json`](../registry/followup_hypotheses_20261025.json): GSST first, then H86K-CWQA and H86K-BFAH, all proposals only. The top-ranked proposal was not validated because the assigned lane, current shared cache, and uniqueness prerequisites remain unresolved.
