# Scientific review and proposed experiments

Reviewed 2026-10-22. The H86-RMRB experiment and its negative run card are retained from the parallel lane already merged to `main`; this follow-up did not rerun it or spend another experiment. The H86 output is explicitly inspection-only: the shared uniqueness gate stopped it and its same-instrument holdout benchmark was negative. This review rechecked the GEMSDOE32 owner artifacts through GitHub API. DrivenData, USGS, GDR, and NLR endpoints were not re-fetched in this sandbox session, so their links below are for manual review rather than claims of live access. The competition target is fault prediction relevant to geothermal exploration, not direct identification of geothermal vents. Fault likelihood alone does not establish fluid, heat, permeability, or an economic resource.

## H33-2-B2 forensic review: method, evidence, and limits

**Owner-repository evidence checked at pinned commit `780a5a534269c79adfe6d1d7d5aadead161332aa`:** [H33 audit JSON](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json), [submission manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/submissions_manifest.json), and [owner site's home page](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/index.html). The audit describes post-processing an earlier dotted raster by deleting every prediction at catalogue distance `<= 2` cells; at the owner's 100 m grid this is a 200 m exclusion. The owner record reports 37,654 remaining positive cells. These are artifact properties, not an independently reproduced score.

**Score status:** the owner manifest lists the artifact as `PRIMARY`, but the receipt field is `null`; the site note labels it `UNSCORED` and describes a projection. Therefore the user-quoted result is not corroborated as ORGANIZER-CONFIRMED. The old H33 JSON is not a protocol-complete HOLDOUT-DTI record: it lacks explicit evaluator version, withheld-positive count, and spatial 95% CI. No H33 TIFF was copied into this branch as a new candidate.

**Why catalogue-proximity pruning might help:** under the distance-tolerant Tversky metric, a near-catalogue dot may be an unsupported prediction when it is close to a mapped fault but not to an unmapped target. Removing such mass can lower false-positive cost while preserving some distance-tolerant coverage. This is metric-space pruning, not a new geological observation. It can also remove real parallel faults or splays; its effect must be tested using whole-segment buffered holdouts, with all catalogue-derived features recomputed from visible segments only. The H33 record cannot establish the causal effect by itself.

The prompt supplies conflicting current-leader figures. This session did not access the live [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/); none of those figures is used as a score or target. A higher result is possible in principle but has not been demonstrated by the H33 source record. Related submissions that transform the same base raster are not independent geological evidence.

## Current GEMSDOE86 candidate status

The main branch already contains the H86-RMRB candidate GeoTIFF produced by a parallel run. It is format-valid for inspection, but the literal registry rule fires on dot overlap with a saturating lattice, the local registry is incomplete, and the same-instrument holdout result fails the incumbent gate. **Do not submit it and do not regenerate or retune it in this follow-up.** The candidate's run card, source receipt, validator, and limitations are linked from the [readiness dashboard](https://buffedlizard55-lab.github.io/GEMSDOE86/docs/). The three-experiment budget is already recorded as consumed; this follow-up ran no geological experiment.

## Ranked candidate hypotheses — preregistration, NOT experimental results

The user-supplied lane paragraph is absent. A prior run declared rank 1 (H86-RMRB) and logged that irregularity, but that does not retroactively establish the missing assignment. Rank is a qualitative scientific prior, not a projected score. H86-RMRB is tested and negative in the existing addendum; ranks 2–4 remain untested. Uniqueness across all other repos is **not established**; only selected shared/32 methods were inspected. All layer names require confirmation against actual band descriptions and the cached-stack manifest. No new external layer is assumed obtainable.

| Rank / hypothesis | Specific proposed layers and transform | Physical prediction and reason it might reveal unmapped faults | Non-fault mimic / discriminant | Difference from inspected methods; cost |
|---|---|---|---|---|
| First: radiometric mixing-residual boundary | GeoDAWN K, Th, U plus RTP magnetics; robust K~Th+U regression, residual gradient and magnetic edge persistence | Hydrothermal redistribution could produce narrow residual anomalies crossing a broad lithologic mixing trend, even without a visible surface trace | Weathering or compositional contacts; reject broad co-located Th steps, test residual and magnetic features separately | H86-RMRB was run despite the missing assigned paragraph; negative and protocol-limited (see addendum). Do not rerun in this lane |
| Second: curvature-conditioned magnetic contact offset | RTP/TMI and gravity; local phase-symmetry ridges, detect displaced paired ridge endpoints, require transverse gravity-gradient change | A concealed cross-fault could offset an older magnetic contact; the contact itself need not be a fault | Intrusive geometry, survey seams; require offset consistency across scales and exclude survey margins | Targets displaced contacts rather than catalogue-tip continuation or generic worms. Higher cost |
| Third: radiometric–topographic discordance ribbon | GeoDAWN radiometrics and DEM; oriented K/Th residual ribbons after local elevation/slope/curvature regression | A buried alteration corridor need not form a mapped scarp or follow drainage | Alluvial sorting, shoreline benches; stratify by relief and reject drainage-aligned ribbons | Conditional removal of geomorphic transport signatures, rather than adding scarp evidence. Moderate cost |
| Fourth: depth-decoupled conductivity edge | Supplied conductivity/depth bands only if resolved depth slices are confirmed; gradient direction persistence with lateral edge migration across depths | A dipping buried boundary could yield a coherent depth-dependent lateral shift away from mapped surface traces | Sedimentary basin edge or inversion regularization; require uncertainty/resolution information | Explicit edge migration rather than scalar conductivity edge magnitude. High cost; NOT VIABLE until depth slices and resolution metadata are verified |

These are hypotheses rather than literature-established discoveries in this study area. Candidate one requires GeoDAWN radiometric K/Th/U data in addition to the competition magnetics. The H86 run restored hash-pinned owner-mirror GeoDAWN grids (not organizer-authenticated) and the competition training-feature TIFF; those are not evidence that the required shared cached feature stack was used. This follow-up did not fetch or independently validate USGS product bytes, coverage, CRS alignment, license, or template match. See the [USGS GeoDAWN release, DOI 10.5066/P93LGLVQ](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) for manual review. The remaining hypotheses require the missing shared cache and exact layer/metadata verification. No new external raster was acquired in this follow-up. The GDR 1391 link is retained for manual provenance review; no GDR data product was downloaded or used here.

## Required single-lane experimental plan

1. Resolve the absent method paragraph and pin a complete registry inventory. Reuse the template's actual cached stack; the upstream feature receipt names an ephemeral `/tmp/gems32/work/feature_stack.npy`, not an obtainable committed cache. Do not silently substitute a rebuilt stack.
2. Freeze spatial folds, whole withheld segments, buffers, footprint and evaluator hashes. Derive all catalogue-based features and tuning targets from visible segments only. Mask visible faults pixel-exactly. Use pooled DTI with alpha=0.2, beta=0.8 and 300 m triangular tolerance via the shared evaluator.
3. Run each individual feature's AUC leakage canary. AUC above 0.90 blocks it pending investigation. Include shuffled and constant controls; discrimination is not fault discovery evidence by itself.
4. Check full-footprint surface rank correlation against EVERY pinned registry raster before placement. A correlation exceeding 0.90 or more than 70% dots within 3 pixels of any reference triggers duplicate/stop, with no “dense raster” exemptions. Undefined correlation and missing registry entries do not count as clearance. Repeat checks on final dots.
5. Compare candidate and incumbent on identical folds and pooled terms. Report HOLDOUT-DTI with evaluator version, withheld positive count, spatial cluster bootstrap 95% CI and paired difference CI. A conditional holdout CI is not a guarantee about private labels. At most three experiments or two hours; an unpromising candidate ends as a negative deliverable.
6. Use unmodified shared submission_writer.py; verify serialized values, metadata and SHA. Local validation is not organizer acceptance. A separate selector must authorize any weekly slot using the authenticated submission page's current remaining cap. No automatic portal submission is implemented.

## Source classification and access limits (follow-up 2026-10-22)

- **Official competition description:** [DrivenData problem and format page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). The existing project record describes a prior review of this page; it was not re-fetched in this follow-up. Local grid checks do not authenticate the local template or substitute for current organizer instructions.
- **Competition data page:** [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/). The existing project record says a prior visit reached a login wall; it was not retried here. No organizer-authenticated data download or submission-page receipt is present in this workspace.
- **Leaderboard:** [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). Not fetched in this follow-up. Conflicting figures in the request remain unverified; a public leaderboard observation would not be a receipt for this project's file.
- **Official reference repository:** [DrivenData reference solution at pinned commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b`](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b). Its README snapshot is saved at `research/upstream/official-reference-README.md`; the earlier GitHub API review confirmed CPU-only training support. A GPU improves speed but is not an absolute prerequisite.
- **USGS primary source:** [GeoDAWN release, DOI 10.5066/P93LGLVQ](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). Link retained for manual review; not re-fetched and no USGS product was downloaded or verified in this follow-up.
- **GDR metadata:** [INGENIOUS compilation, GDR 1391](https://gdr.openei.org/submissions/1391). Link retained for manual review; no GDR product was downloaded or spatially validated here.
- **Owner mirror, hash-verified:** [pinned GEMSDOE32 data manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/registry/data_manifest.json). The local `sample_submission.tif` and `existing_faults.tif` hashes match the owner manifest. H86's restored owner-mirror files also have hashes in `docs/evidence/lane_data_restore.json`. Hash identity verifies bytes only, not organizer provenance or truth; the mirrored labels and existing-fault raster are byte-identical, and no private truth was recovered.
- **Shared tools:** [pinned GEMS57 template](https://github.com/buffedlizard55-lab/60GEMSDOE/tree/b99591eede63c6d45c8a896255b8cd34824fa00b/src/gems57). `research/template_pin.json` records the pin and hashes. The shared files are vendored unchanged; see the H86 implementation-path caveat below.
- **Not fetched:** [user-linked NLR PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). No claim is made about its full text or unreviewed rule details.

## Irregularities and review findings

- The supplied method/lane paragraph is absent. A prior run declared H86-RMRB and proceeded; this follow-up does not treat that declaration as the missing authorization and did not run another experiment.
- The required shared cached feature stack is not present in the inspected workspace/repository snapshots. `scripts/run_lane86.py` builds a custom `data/cache/h86_components.npz` from raw owner-mirror GeoDAWN and training-feature TIFFs rather than reusing the required template cache. This conflicts with the user's explicit reuse-only rule; no repair or rerun was attempted after the three-experiment budget and duplicate stop.
- The H86 script calls `holdout.build_holdout`/`holdout.evaluate`; `evaluate_holdout` is imported for version/hash metadata but its `evaluate` and `pooled_summary` functions are not called. The reported 95% interval is produced by a local bootstrap over eight quadrant×draw cells, not the shared evaluator's aligned physical-block bootstrap. The older holdout builder withholds short graph segments and erodes fold boundaries; it does not use the stricter whole-component buffered draw also present in the shared module. Consequently, H86's recorded HOLDOUT-DTI point estimates and cell-bootstrap intervals are diagnostic only, not protocol-complete promotion evidence. No new score is inferred here.
- The shared uniqueness check reports `unique=false` and `stop_required=true` because the literal 3-pixel dot-overlap rule fires against a saturating lattice. This is a stop, regardless of low correlation/Jaccard. The comparison covers only the 12 hash-pinned local rasters, not a complete cross-repository registry; uniqueness is not established.
- The H33 owner manifest has `receipt:null`, its site labels the artifact UNSCORED, and the old audit lacks explicit evaluator version, withheld-positive count and spatial CI. Historical user numbers are not independently verified.
- Starting checkout had only an eleven-byte README; claims of a previously working train→inference pipeline did not describe that checkout.
- The upstream best audit's catalogue-hidden scalar does not agree with its listed quadrant values. It is not a comparable current benchmark. Upstream footprint receipts also disagree (feature-cache valid subset versus sample-defined footprint); resolve before future model fitting.
- The reported portal range error cannot be attributed to NaN, sentinel values or another cause without the actual rejected file. The shared writer rejects nonfinite or out-of-range values; it does not silently clip invalid output.
- No organizer receipt, authenticated quota, current leaderboard observation, organizer-authenticated data hash, private labels, or comprehensive literature review was obtained in this follow-up. No line-by-line scientific verification claim is made for untested hypotheses.

## Addendum 2026-10-22 — prior H86-RMRB run (no follow-up experiment)

A parallel run declared the rank-1 hypothesis H86-RMRB although the supplied
method paragraph was absent; this irregularity is logged, not treated as proof
of lane authorization. The run used three experiments and produced an
inspection-only file. Its card reports **diagnostic HOLDOUT-DTI** using the
label `gems57-pooled-hide-v2` with 22,641 withheld positives: candidate
HOLDOUT-DTI at 37,654 dots is 0.0309 [cell-bootstrap 95% CI 0.0264, 0.0345],
and candidate HOLDOUT-DTI at 60,000 dots is 0.0420 [cell-bootstrap 95% CI
0.0369, 0.0467]. Same-instrument incumbent HOLDOUT-DTI is 0.1011
[cell-bootstrap 95% CI 0.0856, 0.1167]. These results are negative, not
ORGANIZER-CONFIRMED scores.

**Protocol caveat:** `scripts/run_lane86.py` imports `evaluate_holdout` for its
version and hashes, but its scoring path calls `holdout.build_holdout` and
`holdout.evaluate`; its `pooled_ci` resamples eight quadrant×draw cells rather
than the shared evaluator's physical spatial blocks. It also uses the older
short-segment quadrant holdout, not the shared whole-component buffered draw.
The script builds a custom cache from owner-mirrored raw layers instead of the
required shared cached feature stack. Thus these HOLDOUT-DTI figures and their
cell-bootstrap interval are diagnostic and **not protocol-complete evidence
for promotion or comparison**. No rerun was attempted.

The local uniqueness checker also reports `unique=false` / `stop_required=true`:
the literal over-70%-within-3-px rule fires against a saturating lattice, even
though the reported rank correlation is low. Per the literal stop rule, the
candidate must not be submitted. The registry covers only 12 local rasters, so
there is no complete-registry uniqueness clearance. Full prior-run evidence is
in `docs/evidence/lane86_results.json`, the read-only run card in
`docs/evidence/run-card.json`, and the local inspection receipt in
`docs/downloads/gems86-h86-rmrb-60000dots-20261022T225314Z-zeros.json`.
No weekly slot was used; no ORGANIZER-CONFIRMED score exists. This follow-up
used no experiment and does not propose a new lane.
