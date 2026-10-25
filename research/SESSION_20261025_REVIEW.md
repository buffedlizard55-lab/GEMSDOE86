# Three-pass repository review — 2026-10-25

## Decision

**DO NOT SUBMIT. No new TIFF was generated in this review; no weekly slot was used.** This is not a claim that no future method can succeed. It is a fail-closed decision for this session: the prompt does not identify a single lane paragraph, the actual shared feature cache is absent from the checkout, the pinned registry scan is incomplete, and the previously run 44,090-dot H86F candidates failed the final like-for-like dot-overlap check. The current UI and every existing release artifact remain explicitly audit-only.

The goal of making a unique, competition-ready GeoTIFF is therefore still **unmet**. I did not satisfy it by relabeling, re-encoding, or copying an earlier raster.

**Parallel-work scope note:** this focused review was performed on its assigned branch before merging the concurrent mainline PR #100. That PR adds a separate H86H-PSTD research lane which halted before raster serialization; it was not run or selected by this review. Its independent evidence and outcome remain in [the H86H review](SESSION_20261024_H86H_PSTD_REVIEW.md) and [the mainline handoff](SESSION_20261025_REPO_REVIEW.md). After integrating that concurrent work, the final combined branch test suite is separately recorded below.

## Pass 1 — trace the request, repo instructions, and evidence

Read `PROMPT.md`, the top of `README.md`, `AGENTS.md`, the prior 2026-10-24 request archive, the release/download gates, and current H86F research cards. The repository's standing requirements are stricter than “a TIFF exists”: use the shared evaluator/writer, run segment-buffered hide-and-recover, test individual features for leakage, compare against registry artifacts before/after placement, validate on-disk values/grid, and leave promotion to the selector. Scores in the prompt are not organizer receipts.

The current README already has a prominent **IS ANY FILE OK TO SUBMIT RIGHT NOW? NO** banner and links to the submission guide, release-readiness report, registry measurement, fleet, and official sources. Its binaries have clear audit-only/do-not-submit labels. The old user-request archive is retained intact; the present session is recorded here rather than silently changing historical request text.

### H33 score analysis (forensic measurement, not causal or organizer evidence)

The pinned H33 raster is pixel-identical to the parent D2.8 dotted raster after removing 2,545 cells at catalogue distance `√2`–`2.0 px`; it adds no cells. H33 has 37,654 dots, zero dots on the mapped catalogue, and a nearest-neighbor spacing median of 3 px. These are **pinned-raster forensic measurements** in `docs/evidence/h86f-h33-forensics.json`.

That change supplies a defensible *mechanistic explanation* for why the submitter's claimed `0.2708 → 0.2778` increment is plausible under the asymmetric metric: eliminating redundant near-catalogue mass can lower the false-positive penalty without necessarily losing much 300 m max-kernel credit. It does **not** establish that the collar removal caused a real leaderboard improvement. Both `0.2708` and `0.2778` are **OWNER-REPORTED**, not `ORGANIZER-CONFIRMED`; no submission-page receipt was found in this checkout. Nor does the analysis imply that the H33 geological hypothesis identifies vents: the target is fault traces, not geothermal confirmation.

## Pass 2 — verify experiments, gates, data, and operational limits

### Existing same-split experimental evidence

- **HOLDOUT-DTI** (`gems57-pooled-hide-v2`, 11,321 withheld positives, 95% CI): H86F-GZZD candidate `0.0302866`, CI `[0.0236524, 0.0364366]`; paired delta versus its best preregistered control `−0.0035732`, CI `[−0.0184960, 0.0133630]`.
- **HOLDOUT-DTI** (same evaluator, same withheld positives, 95% CI): H86F-PCC candidate `0.0327335`, CI `[0.0237374, 0.0435741]`; paired delta versus its best preregistered control `−0.0011263`, CI `[−0.0199461, 0.0191505]`.
- **HOLDOUT-DTI** (same evaluator and withheld-positive count, 95% CI): same-split historical comparator KSLB is `0.1240635`, CI `[0.1079703, 0.1403298]`. It is a historical comparator, not an organizer score or a result recomputed by this review. Neither H86F result beats it with separated intervals.
- H86F's feature-alone canaries were below the stipulated 0.90 leakage trigger (see the corresponding run cards); passing this canary does not establish predictive value.
- **REGISTRY-MEASUREMENT:** final-dot PA-86-02 checks for H86F-GZZD/PCC each measured 685 of 687 indexed rasters and recorded 13 dot-field overlap firings. Worst forward overlap was `0.9999546` versus the `13GEMSDOE` stride-5 dot lattice, above the 0.70 stop. Two incompatible registry rows prevented completeness. This is a negative gate, not a full uniqueness clearance.
- **REGISTRY-MEASUREMENT:** the all-artifact audit remeasured 17 inherited TIFFs against one pinned witness only. Every inherited artifact is marked negative; one witness is sufficient to reject, never sufficient to declare unique. The registry is explicitly incomplete.

The research-data mirror restoration path successfully restored the hash-pinned protocol rasters and witness for audit. It does **not** restore the 419 MB `training_features.tif` to this checkout and does **not** make owner mirrors organizer-authenticated. `data/prepared_manifest.json` describes earlier prepared inputs, but its source feature TIFF and the template's cached feature stack are absent now. Therefore the candidate hypotheses below could not be scored afresh in this review.

### Three candidates not run in this repository, ranked qualitatively

These are **testing priorities, not score projections**. They are carried forward from documented hypothesis work and are not an authorization to start another lane. The request's “single method paragraph” is missing, so none can be selected as this session's lane.

| Priority | Hypothesis and layers | Physical signature / why it might identify a missing fault | Difference from existing repo methods | Qualitative potential / cost | Source and viability |
|---|---|---|---|---|---|
| 1 | **Broad low-relief warp persistence** — competition Band 12 (`det_elev`) and Band 19 (`det_elev_slope`) | Multi-scale signed profile-curvature flips (roughly 300/600 m smoothing) persisting across orientations/length scales; tests old, degraded fault-related warps after a sharp surface scarp has eroded, rather than scoring mapped scarps themselves. | Existing terrain methods emphasize sharp scarps, slope/relief thresholds, or lineaments; the preregistration says this specific signed broad-warp persistence feature is not implemented. | **Highest qualitative priority; low–medium cost.** No DTI gain is estimated. | Competition-native layers, but the current TIFF/cache is absent. Not executable until a lane is assigned and inputs are restored/hash-verified. |
| 2 | **Geodetic strain-gradient localization** — Bands 4 (`geod_2ndinv`), 7 (`geod_shearrate`), and 8 (`geod_dilaterate`) | Spatial gradient/coherence of the strain-rate tensor invariants, looking for narrow deformation localization rather than high scalar strain; a blind locked fault could produce a coherent strain edge not in the Quaternary catalogue. | Prior work includes scalar geodetic feature combinations and hydro-conduit models; this proposal is a tensor-gradient localization transform, not another raw scalar rank average. | **Second qualitative priority; low cost.** Multi-kilometer geodetic smoothing may be poorly matched to 300 m metric support. | Competition-native layers, but absent from the current disk feature stack. Viability remains conditional on holdout testing. |
| 3 | **Hydrothermal alteration decoupled from topography** — competition Band 2 (`rtp`), Band 17 (`cond_surf`), Band 6 (pixel-verified as GeoDAWN total-count radiometry, not magnetic tilt), plus independently documented INGENIOUS/GDR points | A magnetic quiet/trough and conductance anomaly spatially associated with independently mapped sinter/thermal evidence but lacking a catalogued scarp; targets concealed upflow structures, not mere fault-proximal vents. | Existing work used radial vent halos, magnetic ridges, or conductance as generic covariates; this tests alteration/conductance plus independent hydrothermal evidence with explicit non-fault checks. | **Third qualitative priority; medium–high cost.** | Specific free/official sources proposed: [GDR 1391](https://gdr.openei.org/submissions/1391) and [INGENIOUS](https://gbcge.org/current-projects/ingenious/). Their official bytes/metadata were not retrieved or verified in this sandbox, and no independent GDR point data are present. **Not viable to run until obtained and hash/provenance checked.** |

The cost/priority ordering is a qualitative research judgment only; it is not a forecast of leaderboard performance. Before any candidate becomes viable: restore the real shared cache, establish source provenance, preregister the lane/arms and folds, run individual-feature canaries, then evaluate with the pinned shared evaluator. A current valid holdout best must use the *same* split/design; scores from different folds are not compared as if equivalent.

### Source pointers for independent review

These are the URLs recorded in the repository's source ledger and related preregistrations. They were **not all freshly retrieved during this review**; the assessment below distinguishes source pointers from a live content check.

| Topic | Source | Review status in this session |
|---|---|---|
| Competition problem, rules, data access | [DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [rules](https://www.drivendata.org/competitions/306/competition-doe-gems/) and [data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Links preserved in source/docs; no portal login, live leaderboard receipt, quota, or private data was accessed. Portal scraping is prohibited by `AGENTS.md`. |
| Submission/metric context | [NLR GEMS report PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) and the pinned shared implementation `vendor/gems57/metric.py`, `vendor/gems57/submission_writer.py` | Local shared code hashes verified by release audit. The official PDF was not freshly fetched in this review. |
| Airborne geophysics | [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) | Existing band-physics verification is a local measurement of the hash-pinned owner-mirrored raster; that does not authenticate the mirror as organizer bytes. No fresh USGS archive retrieval here. |
| Proposed hydrothermal independent evidence | [DOE Geothermal Data Repository submission 1391](https://gdr.openei.org/submissions/1391), [INGENIOUS project](https://gbcge.org/current-projects/ingenious/) | Source pointers only. No bytes/metadata were freshly fetched, and the relevant point layers are absent from this checkout; hypothesis marked not viable to run until acquired and verified. |
| Reference modeling implementation | [DrivenData GEMS prize reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Repository reference link; no fresh remote inspection during this turn. |
| Coordinate reference | [EPSG:32611](https://epsg.io/32611) | Raster CRS/grid is checked locally against the pinned sample submission; EPSG page not freshly retrieved. |


### Reproducible checks executed

- Initial `protocol_preflight.py` attempt failed closed because the required root-level `data/sample_submission.tif` was absent; no scientific work ran. Restored the hash-pinned protocol inputs and registry witness, reran preflight successfully, and recorded `docs/evidence/protocol-preflight.json`.
- The **REGISTRY-MEASUREMENT** preflight records the historical witness SHA-256 `ab0a0a62…`, 100% direct support over the allowed domain, and `STOP_LITERAL_OVERLAP_UNSATISFIABLE` under the literal support rule. This measures one continuous witness and is not a candidate uniqueness measurement; PA-86-01/02 still require representation-aware checks on any authorized future lane.
- `python scripts/audit_release.py --measure-registry`: PASS; 17 inherited artifacts remeasured, all negative, no new experiment or slot.
- `python scripts/build_site.py --check`: PASS.
- `python scripts/check_site.py`: PASS; this validates links/registered binaries and negative-state safety, not scientific clearance.
- Before the concurrent mainline merge, `pytest -q`: **679 passed, 24 skipped, 42 warnings, 41 subtests passed**. After integrating PR #100's separate H86H-PSTD lane and its tests, final branch `pytest -q`: **688 passed, 24 skipped, 42 warnings, 41 subtests passed**.

## Pass 3 — check against the full request and close gaps

| Requirement | Result |
|---|---|
| Explain H33's claimed lead with pixel-level evidence and distinguish claim from receipt | **Met:** exact subset/collar mechanism is documented; score remains owner-reported and not causal proof. |
| Produce 3–5 untried hypotheses, identify layers/signatures/missing-catalogue rationale/novelty, and rank by potential/cost | **Met as research triage:** three qualitative candidates above; no numerical gains projected. |
| Validate the top candidate before any slot | **Not met / blocked:** no lane paragraph assigned, shared feature cache absent, and historical final-dot overlap gates failed. No holdout result is fabricated. |
| Generate an easy-to-download, unique competition TIFF explicitly cleared to submit | **Not met:** this review generated no TIFF. Existing artifacts are audit-only and explicitly DO NOT SUBMIT. This is preferable to promoting a duplicate or untested file. |
| Make submission error [0,1] impossible | The shared writer and release audits validate existing bytes in `[0,1]`, but a local format pass alone is not portal acceptance and does not solve registry/holdout failures. |
| Official source research, current feed, no human upload selection | Links and automated feed exist; no current organizer receipt/quota was accessed. Portal automation is prohibited by repo policy, and no submission was made. |

### Limitations and next actions

1. Assign one method paragraph/lane; otherwise parallel-run isolation has no well-defined method.
2. Restore the actual shared cached feature stack and verify its pin. A mirrored raw TIFF is not the template cache.
3. Resolve the final-dot duplicate issue through the pinned shared registry implementation and complete, current registry; do not privately change thresholds or use continuous-surface overlap as a dot duplicate signal.
4. Recheck current organizer rules and quota only through an authorized human browser receipt. Do not report the user-supplied `0.3195` or `0.4413` as confirmed scores.
5. Run the chosen hypothesis with whole-segment buffered holdout, catalog-only-visible-feature derivation, exact visible-label mask, individual feature canaries, pooled DTI and 95% CI; compare only like-for-like splits. Promote only if all pre-registered scientific and uniqueness gates pass.
6. Then use the shared writer and validate single-band GeoTIFF CRS/shape/transform/range/footprint and ZIP, attach unique name and ≤140-character note, and leave weekly-slot selection separate.

## Current-review JSON card

The machine-readable card is [`docs/evidence/latest-review-run-card.json`](../docs/evidence/latest-review-run-card.json), freshly generated by `audit_release.py --measure-registry`. It is a negative **audit-only** card: no new candidate raster, no holdout result, no submission name, and no selector approval.
