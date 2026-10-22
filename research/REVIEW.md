# Scientific review and proposed experiments

Reviewed 2026-10-22. **No model experiment was run; no score improvement demonstrated.**
The competition target is fault prediction relevant to geothermal exploration, not direct identification of geothermal vents. Fault likelihood alone does not establish fluid, heat, permeability or an economic resource.

## What the cited best file actually does

[The pinned upstream audit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json) describes deleting all emitted dots within two pixels of the catalogue from an earlier dotted raster, leaving 37,654 dots. These are file properties, not performance estimates. Its grid uses 100 m cells. The audit's own note says UNSCORED and includes a projected leaderboard estimate; that is NOT an organizer score.

**Why pruning could help:** under a precision/recall tradeoff, removing mass that cannot contribute useful recovery can lower the false-positive penalty. Known faults are masked by the required evaluation protocol. Dots adjacent to them may be redundant or may reflect mapping-location bias. Spaced dots can reduce redundant prediction mass while retaining distance-tolerant coverage. These are plausible explanations, not a causal attribution of a private leaderboard outcome. Removing adjacent dots can also destroy genuine parallel faults. The effect must be tested with all catalogue-dependent operations recomputed inside each training fold.

The cited result and all leaderboard highs in the request are **USER-REPORTED / UNVERIFIED**, not ORGANIZER-CONFIRMED. They conflict as descriptions of a current maximum. No signed-in submission-page receipt or currently fetched official leaderboard supports any one as today's maximum. Historical upstream “drift corrected” estimates and projections are not new HOLDOUT-DTI results and are not training targets.

A higher result is possible in principle, but cannot be promised or inferred from these historical scalar values. Many related submissions are transformations of the same base; treating them as independent geological evidence would be pseudoreplication.

## Ranked candidate hypotheses — preregistration, NOT experimental results

No experiment is authorized until the missing lane is resolved. Rank is a qualitative scientific prior, not a projected score. The empty starting repo implements none of these. Uniqueness across all other repos is **not established**; only selected shared/32 methods were inspected. All layer names below require confirmation against actual band descriptions and the cached-stack manifest. No new external layer is assumed obtainable.

| Rank / hypothesis | Specific proposed layers and transform | Physical prediction and reason it might reveal unmapped faults | Non-fault mimic / discriminant | Difference from inspected methods; cost |
|---|---|---|---|---|
| First: radiometric mixing-residual boundary | GeoDAWN K, Th, U plus RTP magnetics; spatially cross-fitted robust K~Th+U regression, transverse residual gradient and magnetic edge persistence | Hydrothermal redistribution could produce narrow residual anomalies crossing a broad lithologic mixing trend, even without a visible surface trace | Weathering or compositional contacts; reject broad co-located Th steps, test residual and magnetic features separately | Tests residuals rather than raw radiometric consensus. Moderate cost; provisional preferred hypothesis, not assigned lane |
| Second: curvature-conditioned magnetic contact offset | RTP/TMI and gravity; local phase-symmetry ridges, detect displaced paired ridge endpoints, require transverse gravity-gradient change | A concealed cross-fault could offset an older magnetic contact; the contact itself need not be a fault | Intrusive geometry, survey seams; require offset consistency across scales and exclude survey margins | Targets displaced contacts rather than catalogue-tip continuation or generic worms. Higher cost |
| Third: radiometric–topographic discordance ribbon | GeoDAWN radiometrics and DEM; oriented K/Th residual ribbons after local elevation/slope/curvature regression | A buried alteration corridor need not form a mapped scarp or follow drainage | Alluvial sorting, shoreline benches; stratify by relief and reject drainage-aligned ribbons | Conditional removal of geomorphic transport signatures, rather than adding scarp evidence. Moderate cost |
| Fourth: depth-decoupled conductivity edge | Supplied conductivity/depth bands only if resolved depth slices are confirmed; gradient direction persistence with lateral edge migration across depths | A dipping buried boundary could yield a coherent depth-dependent lateral shift away from mapped surface traces | Sedimentary basin edge or inversion regularization; require uncertainty/resolution information | Explicit edge migration rather than scalar conductivity edge magnitude. High cost; NOT VIABLE until depth slices and resolution metadata are verified |

These are hypotheses rather than literature-established discoveries in this study area. The first three are conditionally testable using existing competition layers if their identities and units are verified. The fourth is deferred, not a proposal to fetch an unverified new dataset. No free external source is being represented as already acquired. The user-supplied USGS GeoDAWN and GDR links are discovery leads only in this environment.

## Required single-lane experimental plan

1. Resolve the absent method paragraph and pin a complete registry inventory. Reuse the template's actual cached stack; the upstream feature receipt names an ephemeral `/tmp/gems32/work/feature_stack.npy`, not an obtainable committed cache. Do not silently substitute a rebuilt stack.
2. Freeze spatial folds, whole withheld segments, buffers, footprint and evaluator hashes. Derive all catalogue-based features and tuning targets from visible segments only. Mask visible faults pixel-exactly. Use pooled DTI with alpha=0.2, beta=0.8 and 300 m triangular tolerance via the shared evaluator.
3. Run each individual feature's AUC leakage canary. AUC above 0.90 blocks it pending investigation. Include shuffled and constant controls; discrimination is not fault discovery evidence by itself.
4. Check full-footprint surface rank correlation against EVERY pinned registry raster before placement. A correlation exceeding 0.90 or more than 70% dots within 3 pixels of any reference triggers duplicate/stop, with no “dense raster” exemptions. Undefined correlation and missing registry entries do not count as clearance. Repeat checks on final dots.
5. Compare candidate and incumbent on identical folds and pooled terms. Report HOLDOUT-DTI with evaluator version, withheld positive count, spatial cluster bootstrap 95% CI and paired difference CI. A conditional holdout CI is not a guarantee about private labels. At most three experiments or two hours; an unpromising candidate ends as a negative deliverable.
6. Use unmodified shared submission_writer.py; verify serialized values, metadata and SHA. Local validation is not organizer acceptance. A separate selector must authorize any weekly slot using the authenticated submission page's current remaining cap. No automatic portal submission is implemented.

## Source classification and limits

- **Official, fetched:** [DrivenData reference repository](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b). Its README explicitly supports CPU-only use: a GPU is not an absolute training prerequisite. Local snapshot: upstream/official-reference-README.md.
- **Owner mirror, fetched and hash-verified:** [data manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/registry/data_manifest.json). Hash identity verifies mirror bytes, NOT organizer authenticity. The “labels” and existing_faults are byte-identical here; no private truth was recovered.
- **Shared tools, fetched unmodified:** [pinned template](https://github.com/buffedlizard55-lab/60GEMSDOE/tree/b99591eede63c6d45c8a896255b8cd34824fa00b/src/gems57). `template_pin.json` records every local file hash. No shared-tool defect was proven or modified this session. Upstream packaging metadata is historical, not this project's lane assignment.
- **Not fetched / not verified in this network:** [competition description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [GDR](https://gdr.openei.org/submissions/1391), [user-linked PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). These are links for later official verification, not evidence of successful access or current rules.

## Irregularities

- Missing lane paragraph; assigning a novel method autonomously would not establish parallel-lane authorization.
- Starting checkout had only an eleven-byte README; claims of a previously working train→inference pipeline do not describe this checkout.
- No cached stack or complete registry here. Some empty sibling repos also have no reusable assets. A scan of selected repos is not a complete registry scan.
- The upstream best audit's catalogue-hidden scalar does not agree with its listed quadrant values. No relabelling as a comparable current benchmark is justified.
- Upstream footprint receipts disagree (feature-cache valid subset versus sample-defined footprint); use the sample-defined footprint consistently and investigate feature coverage before model fitting.
- Upstream “zero” ZIP is recorded at a suspiciously small size in its tree. Not downloaded, not verified, not offered here.
- The reported portal range error cannot be attributed to NaN, sentinel values or another cause without the actual rejected file. The shared writer rejects all nonfinite or out-of-range values; it never silently clips invalid output.
- No organizer receipt, authenticated quota, direct official data hash, private labels, or comprehensive literature review was obtained. No line-by-line scientific verification claim is made for untested hypotheses.
