# GEMSDOE86 scientific review and RMRB-86 result

Reviewed and executed 2026-10-22. This report separates measurements from source statements and hypotheses. The competition target is **fault prediction** relevant to geothermal exploration; a predicted fault is not evidence of a geothermal vent, heat source, permeability, fluid, or economic resource.

## Executive finding

A new prediction was generated from a new RMRB-86 model; no historical prediction pixels were copied into it. Its SHA-256 is `9ed632445228aad8d9b14d8db75d24687520a092e7e14ca94c3151f96f7aafdd`. Automated serialization checks pass, and its bytes are absent from the 1,143 hash-indexed public rasters. It is therefore a distinct file and a distinct decoded field versus the two stopping witnesses checked.

**It is not approved for competition upload.** The RMRB transform improved the matched core model but did not establish improvement over raw radiometrics: **HOLDOUT-DTI (`gems57-pooled-hide-v2`, 22,893 withheld positive pixels, spatial-bootstrap 95% CI)** = **0.07283 [0.05888, 0.08744]**. The paired difference from the strongest matched raw-radiometric control was **HOLDOUT-DTI delta (`gems57-pooled-hide-v2`, 22,893 withheld positive pixels, 95% CI)** = **0.00167 [-0.00285, 0.00620]**. The interval crosses zero. In addition, a public continuous registry raster is positive throughout the footprint, making the protocol's literal three-pixel dot-overlap result 1.0 and forcing a duplicate stop. No weekly slot was used.

The downloadable TIFF is retained as a negative research deliverable because the owner required a unique TIFF and an unambiguous automated decision. Its filename says `DO-NOT-SUBMIT`; the page and machine run card say the same.

## What the historical H33 artifact can and cannot establish

The user associates H33-2-B2 with an owner-reported result. No authenticated submission-page receipt was supplied, so that scalar cannot be labelled ORGANIZER-CONFIRMED and is not restated here as a verified score.

Artifact/source evidence is nevertheless useful:

1. The [GEMSDOE32 builder](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/scripts/run_h33_validation.py) describes H33-2-B2 as a sparse field obtained by deleting predictions in a mapped-fault collar from an earlier field.
2. The hash-pinned H33 TIFF used only for education here contains 37,654 positive pixels, no positive catalogue pixels, and SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`. None of those pixels was used as a model input or copied to RMRB-86.
3. Under the organizer-described distance-weighted Tversky objective, redundant prediction mass can increase the false-positive term without increasing maximum truth coverage. Sparse placement at approximately the 300 m tolerance scale can preserve coverage while reducing redundant mass. A catalogue collar can remove mapped-looking predictions that are unlikely to earn new-fault credit.
4. That mechanism is plausible, not a causal proof. A genuinely new parallel fault, branch, or continuation can lie next to a mapped trace, so collar deletion can also reduce true-positive coverage.
5. RMRB-86's final dots have 0.45637 forward three-pixel overlap with H33 and full-footprint Spearman correlation 0.03022. Both are below the lane thresholds; byte and decoded-pixel equality are false. This is direct evidence that RMRB-86 is not a renamed copy of H33.

A higher organizer result is possible in principle because no theorem makes a historical artifact a ceiling. This project cannot promise an organizer result, and a holdout estimate is never rewritten as one.

## Candidate hypotheses recorded before experimentation

The supplied prompt referenced a single assigned method paragraph but did not contain one. To obey the no-manual-input instruction, this run selected exactly one lane in `registry/preregistration.json` before model execution and treated the missing assignment as irregularity IR-86-01. The ranking below is scientific prior judgment, not a projected score.

| Rank | Candidate, specific layers and transform | Target physical signature and missing-fault rationale | Named non-fault mimic / discriminant | Difference from pre-existing GEMSDOE86 code; cost and viability |
|---:|---|---|---|---|
| 1 | **RMRB-86 radiometric mixing-residual boundary**: GeoDAWN K, Th, U; competition RTP plus ten core control layers. Robust Huber K~Th+U residual, 20-pixel background removal, 1.5/3-pixel residual-gradient persistence, 2/4-pixel RTP-edge persistence, cross-gradient alignment and structure-tensor line coherence. | Fault juxtaposition or hydrothermal redistribution could produce a narrow departure from broad lithologic K/Th/U mixing even where a scarp was not mapped; independent magnetic persistence tests structural continuity. | Weathering or transported sediment at an unfaulted lithologic contact; gridding seams. Reject broad residuals and require multiscale persistence, but acknowledge that a lithologic contact may still pass. | The initial repo had no geological model; inspected H33 used multiphysics orientation consensus, not robust K~Th+U residuals. Moderate CPU/memory. **Viable:** the owner mirror was obtainable and hash-pinned; official-origin byte identity remains unverified. Selected and tested. |
| 2 | **Curvature-conditioned magnetic contact offset**: RTP/TMI and isostatic gravity. Detect displaced paired phase-ridge endpoints across scales and require a transverse gravity-gradient change. | A concealed cross-fault can offset older magnetic fabric without leaving a mapped surface trace. | Intrusive geometry and mosaicking seams; require consistent displacement sign across scale and reject acquisition-axis concentration. | Targets displacement of contacts rather than generic edge strength or catalogue-tip continuation. High implementation cost; core layers are locally obtainable. Not run. |
| 3 | **Depth-migrating conductivity edge**: conductivity and depth-to-basement, but only if independently resolved depth slices and resolution metadata are confirmed. Track lateral edge migration with depth. | A dipping buried fault may move laterally between depth slices while having no surface trace. | Basin margin and inversion regularization. Demand uncertainty/resolution support and coherent migration rather than one scalar edge. | Explicit depth migration, not scalar conductivity gradient. High cost. **Not currently viable:** the available competition stack exposes only `cond_surf` and one basement-depth surface, not verified depth slices. Required source: a free official INGENIOUS/GDR resistivity-depth product with coverage and uncertainty metadata. |
| 4 | **Radiometric–topographic discordance ribbon**: K/Th/U and detrended elevation/slope. Remove relief-stratified radiometric expectation, then detect transverse ribbons. | A buried alteration corridor may remain geochemically distinct without preserving a scarp. | Alluvial sorting, shoreline benches and drainage transport; reject features that track constant elevation or drainage. | Conditional transport correction rather than raw radiometric fusion. Moderate cost. Not run because it risks collision with the later public H84 radiometric-flanking lane and this run is restricted to one method. |
| 5 | **Sub-kilometre seismic focal-mechanism lineament**: raw USGS ComCat hypocentres and nodal-plane strikes, replacing the supplied 100 km-smoothed earthquake bands. | Active blind faults can produce aligned seismicity without a mapped surface trace. | Quarry blasts, swarm migration and location uncertainty; require depth/uncertainty filters and nodal-plane agreement. | Dynamic fault-scale data rather than the supplied broad fields. High cost. **Not viable in this sandbox:** the named official [USGS FDSN event service](https://earthquake.usgs.gov/fdsnws/event/1/) is outside the network allowlist, so current availability/schema was not verified and no data were fabricated. |

## Implemented method

### Inputs and provenance

- The 19-band core feature TIFF, sample grid and catalogue were restored from hash-pinned owner GitHub mirrors. Their hashes match the historical manifest. This establishes mirror consistency, **not** independent identity with authenticated organizer downloads.
- The four-band GeoDAWN radiometric mirror is owner-derived from the official [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ). Its local SHA-256 is `c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682`. This network could retrieve the owner mirror from GitHub but could not retrieve USGS bytes; no official-byte equality claim is made.
- The unmodified shared evaluator and writer match every SHA-256 in `research/template_pin.json`.
- `docs/evidence/feature-cache.json` records all channel names, transformations, source/builder/cache hashes, robust scaling parameters, regression coefficients and label-free spatial cross-fit diagnostics. No catalogue is accepted by the feature builder.

### Holdout and leakage controls

The unmodified shared `buffered_component_draw` with seeds 20 and 21 withheld whole eight-connected components in four label-blind eroded quadrants. A three-pixel feature-context buffer removes nearby catalogue context. Each model trains on visible faults outside the tested quadrant; the hidden components never enter model fitting. Visible/known faults are excluded by the shared evaluator. Additive metric terms are pooled before forming DTI. The shared evaluator uses alpha 0.2, beta 0.8 and a 300 m triangular kernel. The 95% intervals use paired resampling of aligned 20 km physical blocks and are conditional on this fixed split and model.

Every one of 20 channels passed the feature-alone leakage canary. The maximum symmetric AUC was 0.58034 (radiometric K), well below 0.90. AUC is a diagnostic, not DTI and not evidence of an undiscovered fault.

### Results

| Arm | Result |
|---|---|
| Ten-layer core control | **HOLDOUT-DTI (`gems57-pooled-hide-v2`, 22,893 withheld positive pixels, 95% CI)** = **0.06406 [0.05114, 0.07767]** |
| Core + raw K/Th/U | **HOLDOUT-DTI (`gems57-pooled-hide-v2`, 22,893 withheld positive pixels, 95% CI)** = **0.07116 [0.05723, 0.08591]** |
| Full RMRB-86 | **HOLDOUT-DTI (`gems57-pooled-hide-v2`, 22,893 withheld positive pixels, 95% CI)** = **0.07283 [0.05888, 0.08744]** |
| RMRB minus core, paired | **HOLDOUT-DTI delta (`gems57-pooled-hide-v2`, 22,893 withheld positive pixels, 95% CI)** = **0.00877 [0.00296, 0.01434]** |
| RMRB minus raw radiometrics, paired | **HOLDOUT-DTI delta (`gems57-pooled-hide-v2`, 22,893 withheld positive pixels, 95% CI)** = **0.00167 [-0.00285, 0.00620]** |

The raw radiometric layers add a reproducible signal over the core control on this conditional instrument. The engineered residual-boundary transform has a positive point difference, but its paired interval crosses zero; therefore the specific RMRB mechanism is **not validated as better than raw radiometrics**. The preregistered promotion gate fails. Two experiments were consumed; no post-hoc third experiment was tuned to this result.

## Uniqueness and the binding protocol defect

The surface and final dots were checked against the hash-pinned H33 raster and a public `17GEMSDOE_E-proba-multiscale` raster. Against H33, RMRB passes both thresholds. Against the 17GEMSDOE raster, forward overlap is 1.0 because that prior has positive support over the entire footprint. Under the prompt's literal definition—every finite positive prior pixel is a dot—**every nonempty candidate necessarily fails**. No density exemption was authorized, so this is binding.

This is an irregular but mathematically determinate result: it does not mean RMRB copied that continuous surface. The full-footprint surface Spearman correlation is 0.43927, decoded arrays differ, and file hashes differ. It means the requested overlap gate cannot distinguish any sparse candidate once a full-support continuous raster enters the dot registry. The run stops at that witness rather than pretending a 1,143-raster spatial scan could reverse a failure. The candidate hash is nevertheless absent from all 1,143 indexed public hashes.

After parallel work landed on `main`, this raster was also checked against the three newly merged candidate rasters. On the continuous RMRB surface, the worst Spearman correlation was 0.09262 and worst forward three-pixel overlap was 0.21995. On final dots, the worst Spearman correlation was 0.02391 and worst overlap was 0.48367. None crosses the 0.90/0.70 thresholds; the complete rows and source commit are appended to `docs/evidence/uniqueness.json`. One parallel artifact shares the broad RMRB name but not the model or arrangement: final overlap with it is 0.18134 and rank correlation is −0.00034.

## Automated serialization result

The shared writer generated one single-band float32 GeoTIFF and a ZIP containing only that TIFF. The on-disk validator re-opened the bytes and confirmed:

- EPSG:32611;
- shape 3,730 × 3,292;
- affine transform `(100, 0, 243350, 0, -100, 4508550)`;
- every pixel finite, with minimum 0 and maximum 1;
- 37,654 positive pixels;
- zero positive pixels outside the sample-defined footprint;
- zero positive pixels on the mapped catalogue;
- no nodata sentinel.

These are local format measurements, not organizer acceptance. The user's earlier portal error cannot be diagnosed without the rejected file; this output specifically prevents nonfinite, sentinel and out-of-range values from reaching serialization.

## Official and primary-source ledger

| Source | What it can support | Verification state in this run |
|---|---|---|
| [DrivenData problem/format page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Organizer task, metric and file-format authority | Official link supplied by owner; host not reachable from this sandbox allowlist in this run. Metric implementation was reused from the hash-pinned shared template; no new claim of fresh retrieval. |
| [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Authenticated original competition files | Not authenticated or downloaded. Owner mirrors are explicitly not organizer-authenticated. |
| [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b) | Organizer baseline code and data expectations | Reachable through GitHub; pinned README snapshot is `research/upstream/official-reference-README.md`. |
| [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) / [DOI](https://doi.org/10.5066/P93LGLVQ) | Primary provenance for magnetic/radiometric products | Official source named; not reachable under current host restrictions. Owner-derived mirror fetched and hash-checked; official byte identity unverified. |
| [INGENIOUS GDR 1391](https://gdr.openei.org/submissions/1391) | Potential official geothermal-context resources | Named but not fetched or used in RMRB-86. |
| [EPSG:32611](https://epsg.io/32611) | CRS reference | User-supplied reference; raster CRS was measured locally. |

## Irregularities and limitations

1. **IR-86-01 — missing lane paragraph:** a single autonomous lane was preregistered rather than fabricating an assignment.
2. **IR-86-02 — shared transformed cache absent:** the upstream cache receipt points to an ephemeral path. RMRB reused the raw hash-pinned stack and unmodified shared evaluator/writer, then built a fully receipted candidate-specific cache. It is not misrepresented as the missing upstream cache.
3. **IR-86-03 — literal overlap saturation:** a continuous positive registry raster blocks every nonempty dot field. The negative verdict preserves the supplied rule.
4. **IR-86-04 — registry scope:** the complete public inventory supplies 1,143 hashes, but spatial decoding stopped at the first binding duplicate as instructed. Byte uniqueness across the hash index is established; global spatial uniqueness is not.
5. **IR-86-05 — mirror authentication:** all data hashes are reproducible, but original organizer authenticity requires authenticated DrivenData downloads and comparison.
6. No live quota, private labels, authenticated submission receipt or automatic portal upload is available. No organizer score is claimed.
7. The request supplied conflicting claims for the current leaderboard maximum. Neither is repeated as ORGANIZER-CONFIRMED without an authenticated receipt; the official public leaderboard link is preserved for review.
8. A 100 m fault likelihood raster cannot establish a geothermal vent. Field validation remains necessary for geological use, but no human inspection is used to determine competition-file validity here.

## Reproduction

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_rmrb86_data.py --experiment
.venv/bin/python scripts/run_experiment.py   # fresh output paths only; shared writer refuses overwrite
.venv/bin/python scripts/audit_rmrb86.py
.venv/bin/python -m unittest discover -s tests -v
```

The published artifact already exists, so a reproduction should use a fresh checkout/output name or remove only locally regenerated outputs before rerunning. The writer's refusal to overwrite is a safety property.

The canonical machine result is [`docs/evidence/rmrb86-run-card.json`](../docs/evidence/rmrb86-run-card.json). Its verdict is `negative`, `safe_to_download` is true for audit, and `safe_to_submit` is false.
