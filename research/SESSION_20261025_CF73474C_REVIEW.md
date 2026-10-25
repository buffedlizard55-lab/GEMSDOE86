# Independent review — 2026-10-25 — session cf73474c

## Decision / unmet requirement

**DO NOT SUBMIT. The highest-priority new, unique competition-TIFF requirement is unmet.** No TIFF, renamed historical copy, model experiment or weekly slot was created/used in this independent review. The existing 17 downloads are historical, audit-only artifacts, not a replacement deliverable.

The unchanged literal preflight is mathematically incompatible with a nonempty compliant prediction: the pinned `17GEMSDOE` witness supports every one of the **5,106,385 allowed cells**, making every nonempty allowed candidate's forward overlap **1.0 > 0.70**. These are **REGISTRY-MEASUREMENT** counts/fractions, not model performance. A witness can reject; it cannot certify full-registry clearance. There is also no assigned single-method paragraph, and the actual template cached feature stack remains absent. These are stops, not an invitation to invent a lane or privately change support semantics.

Primary machine-readable receipts:

- [Current independent negative card](../docs/evidence/session-cf73474c-run-card.json)
- [Native data / actual shared-cache obtainability](../docs/evidence/session-cf73474c-data.json)
- [689-file registry byte/grid audit](../docs/evidence/registry-input-grid-review-20261025.json)
- [Concurrent final-dot comparison and H33 lineage remeasurement](../docs/evidence/concurrent-artifact-review-20261025.json)
- [Release/format audit](../docs/evidence/release-readiness.json) and [all inherited artifacts against witness](../docs/evidence/all-artifacts-registry.json)
- [Complete current request](REQUEST_20261025.md); previous request archives are byte-preserved.

## 1. What explains H33, and what cannot be inferred?

### Pixel operation — remeasured, not inferred from a filename

Pinned parent `GEMSDOE28` SHA `ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73` has **40,199 dots**. Pinned H33 SHA `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9` has **37,654 dots**. The new read-only audit confirms H33 is exactly the parent after removing its catalogue collar at distance <=2 pixels: **2,545 removed, zero added**. Removed distances are sqrt(2) and 2 pixels. No new geological corridor was added by that operation. These are **RASTER-MEASUREMENT** counts, not scores.

The supplied **OWNER-REPORTED** parent `0.2708` and H33 `0.2778` are not organizer-confirmed. The request's incompatible leaderboard maxima `0.3195` and `0.4413` are also unverified owner claims. Pixel equality establishes the edit, not a controlled causal explanation of the private score increase. The rechecked owner H33 audit contains an unscored/projected field; it is not a submission-page receipt.

### Metric mechanism — plausible, conditional, not a forecast

Use the unchanged shared DTI implementation: truth credit is a **maximum** triangular-kernel credit per hidden truth cell, not the sum of overlapping dots. With weighted truth credit `T`, false-positive prediction mass `F`, truth count `K`, and `FN = K - T`,

```
DTI = T / (T + 0.2 F + 0.8 FN + epsilon)
    = T / (0.2 (T + F) + 0.8 K + epsilon).
```

If pruning loses truth credit `a >= 0` and saves false-positive mass `b >= 0`, it helps **if and only if**

```
T*b > a*(F + 4*K + 5*epsilon).
```

Here `K` is the total scored truth count, **not** false negatives. Redundant low-credit dots may be worth pruning, but a dot near a mapped fault can still recover a different, unmasked hidden fault. The 2-pixel collar is not a zero-credit certificate. Separations near one kernel radius do not make kernel disks disjoint; two radius-R disks can overlap out to 2R. More dots may help or hurt, depending on incremental credit. Existing synthetic metric counterexamples are retained; no private metric fork was created.

The archived same-split comparison remains **HOLDOUT-DTI**, evaluator `gems57-pooled-hide-v2`, seed 20, **11,321 withheld positives**: fold-fair R0 **0.0961**, 95% CI **[0.0830, 0.1089]**; KSLB **0.1241**, 95% CI **[0.1080, 0.1403]**. These are historical, not rerun here; neither is an organizer result, and a local improvement cannot be converted to a private leaderboard projection. A new method must rerun the strongest comparable control, not merely beat a weaker historical R0.

### Reproduction limitation discovered

The H33 upstream receipt describes a 35-channel `/tmp/gems32/work/feature_stack.npy` and **5,165,852 footprint cells**, while the canonical template and the later static60 receipt have **5,167,373 footprint cells** (a **1,521-cell difference**, DATA-RECEIPT comparison). The receipt alone cannot establish why: preprocessing masks, valid-feature exclusions and stale provenance are possibilities, not diagnoses. The bytes of that H33 cache were not obtained. Do not silently substitute our native bands and call it an H33 reconstruction or matched holdout.

## 2. Ranked geological proposals — recorded before implementation

[Full register](../registry/h86g_hypotheses.json). **All four are NOT RUN / unauthorized.** Ranking is qualitative expected information beyond existing edge/coverage methods versus cost, not projected score. Names and indices were checked against `src/gems86/io.py:BANDS`.

| Rank | Proposal / actual layers | Why potentially uncatalogued; difference from executable local code | Named non-fault mimic | Qualitative potential / cost |
|---|---|---|---|---|
| 1 | **CSPA — cross-spectral gravity–magnetic admittance**. B13 `iso_grav_anom`, B2 `rtp`. | Test band-limited, orientation-consistent cross-power/phase and a localized change against a smooth common-source admittance model beneath basin cover, rather than rank another edge. A density/susceptibility discontinuity can be buried without a mapped scarp. This carries forward an earlier **unrun** cross-spectral proposal; it is not a new invention or a claim of fleet-wide novelty. | Basalt flow margin / buried lithological contact. | Highest incremental physical potential in this queue, but a stringent mimic problem; medium cost. |
| 2 | **MPC — monogenic magnetic phase congruency**. B2 `rtp`, B13 `iso_grav_anom`. | Multi-scale Riesz/local phase invariance rather than amplitude ridges or the already implemented signed polarity step. Could follow weak covered basement contacts, subject to cross-layer rejection. | Remanently magnetized volcanic contact and flight-line seams. | Potentially complementary to amplitude cues; medium cost. |
| 3 | **PSC — persistent saddle connections**. B2 `rtp`, B13 `iso_grav_anom`, B15 `depth_to_base_surf`. | Persistence across smoothing scales of basin/basement saddle-connection topology, not another ridge threshold. A covered relay connection might exist without a surface trace. No executable persistence implementation was found in this checkout. | Paleovalley / erosional basin neck. | More geometrically distinct but representation-sensitive; medium-high cost. |
| 4 | **CNT — conductivity-neck topology conditioned on dilatation**. B17 `cond_surf`, B8 `geod_dilaterate`, B7 `geod_shearrate`. | Topological conductive necks between broader conductive regions under dilatational strain, not raw conductivity highs, an MT claim, or a magnetic trough. May express concealed permeability corridors, but is indirect fault evidence. | Saline playa or clay-rich channel fill. | Highest confounding risk; medium cost, last priority. |

For CSPA, one prospective test is a regularized local admittance `H = S_GM/(S_MM + lambda)` and scale-coherence diagnostic `|S_GM|^2/(S_GG*S_MM + epsilon)`. A coherent **smooth** common lithology response is a control, not automatically a fault. The hypothesis requires a localized residual displacement signature that survives detrending, scale/orientation controls, and volcanic-contact negatives. Filter scales and all coefficients must be frozen before validation. No transform has been implemented or tuned here.

Coordinate caveat: physical east/north gravity components are `(B18, -B11)`, not `(B18, B11)` in north-positive coordinates; image-row Laplace curvature is `-(d_x B18 + d_row B11)`. B6 is radiometric total count, **not magnetic tilt**. None of these statements establishes that a derivative is an independent geological measurement.

### Source / access and geothermal distinction

No new external product is required by these four designs: their native TIFF is now actually obtained. This does **not** satisfy the mandatory shared-derived-cache requirement. A complete Git-tree inspection of pinned `60GEMSDOE@b99591...` and inspected `GEMSDOE66` main found no `.npy/.npz/.f16/.f32` cache objects. That is evidence about those trees only—not proof of absence from releases, LFS, other commits or external storage. Both inspected repositories also returned empty published-release lists (100-per-page API queries recorded in the receipt); no release cache asset was obtained. This does not rule out other storage or commits. A historical feature manifest is not cache bytes.

Official primary sources remain [DrivenData reference](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS MT DOI](https://doi.org/10.5066/P9TWT2LU), [USGS heat-flow DOI](https://doi.org/10.5066/P9BZPVUC), [DOE GDR 1391](https://gdr.openei.org/submissions/1391), [UNR INGENIOUS](https://gbcge.org/current-projects/ingenious/), and the [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf). Non-GitHub pages were **not freshly fetched in this egress-restricted session**; dated earlier source observations remain separately labelled. No DrivenData scraping occurred.

The official GitHub README and pinned reference notebook were freshly inspected; CPU-only support is explicit. The notebook's ordinary training Tversky loss does **not** independently verify our distance-weighted evaluation implementation. Official reference license API metadata was null; that is not affirmative licensing permission. Mirror SHA matches prove byte identity with pinned mirrors, not organizer authentication.

Heat-flow anomalies, sinter and warm probes are geothermal-resource/permeability evidence, **not fault truth or a definition of the competition target**. MT/heat-flow/1-m LiDAR additions would require actual official tile bytes, compatible licensing, a pinned grid/CRS/resolution receipt and compute-budget assessment. None was acquired or used here; prior dated source tables are not an access claim.

## 3. Three explicit passes

### Pass 1 — implement and verify

- Read the standing rules, full request/history and previous handoffs; restored immutable proof inputs/witness and reran the all-artifact rejection audit.
- Ranked four hypotheses before any possible model work. The preflight was obeyed; experiments and slots remain zero.
- Ran the requested download wrapper and `scripts/prepare_data.py`: all three native TIFFs have verified pins; all 19 bands prepared, **58,171 sentinel band-pixels** over **3,073 distinct footprint pixels** (DATA-MEASUREMENT). Cached arrays retain missingness; no prediction was clipped into validity.
- Hardened `prepare_data.py`: **every** input now gates CRS/shape/affine/band counts, label binarity/masks/counts and canonical SHA before array output. Restoration errors propagate and respect the requested destination.
- Hardened archive extraction: selected members are uniquely staged and all hashed/complete before replacing any target; missing, duplicate and non-file requested members abort. Feature parts remain scratch with final assembled-file hash verification.
- Fixed historical holdout normalization: every schema now rejects invalid values/CIs/counts/evaluator metadata and incomplete or invalid paired-delta evidence. Old code demonstrably accepted `value=4`, reversed CI and `positive_count=True`; it no longer does. Shared evaluator/writer bytes are unchanged.

### Pass 2 — edge cases, independent remeasurement, fixes

- Found an incomplete-publication edge in the initial preparation patch; fixed it. A complete array generation is staged, local POSIX preparers are serialized, and ordinary write/source-mutation/cache-rename/manifest-rename failures restore the previous cache and manifest. Array hashes are recorded. **Cross-directory crash atomicity is not claimed**; a process/host crash between replacements remains a limitation.
- Confirmed a later grid-only run must not leave stale feature arrays from an earlier full run. Regression tests cover that case, malformed input metadata/pins, source mutation and all publication failure points with and without a previous generation. Removed deprecated affine multiplication from synthetic tests.
- Removed the misleading `card`/`source_card` skip logic: every sidecar remains subject to negative-state checks; mapped cards are additionally bound to TIFF bytes. Present authorization flags must be exact JSON `false`, not a truthy string, integer or null.
- Restored **all 655 pinned historical inventory entries (728,345,463 bytes)**. The independent input audit then measured **689 unique indexed files including local extras**, all byte-verified, with **687 compatible grids and 2 incompatible**. This is REGISTRY-INPUT-MEASUREMENT, not a full candidate scan or a complete current organizer registry.
  - `14GEMSDOE` horse ensemble has the correct EPSG/shape but **wrong affine origin** `(500000, 4500000)` instead of `(243350, 4508550)`.
  - The `7GEMSDOE`/`GEMSDOE22` Qfaults prior has the correct CRS/affine/shape but **3 bands**, not 1.
  - Neither record was silently excluded, resampled or repaired. Their existence still blocks a valid complete uniqueness scan.
- Closed the inherited GZZD/PCC **mutual final-dot** audit gap using the pinned shared comparator: **REGISTRY-MEASUREMENT** rho **0.0202637870** in both directions; forward overlap **0.1705148560** for PCC→GZZD and **0.1657745521** for GZZD→PCC. These limited pair checks fire neither threshold, but have **no complete-inventory certificate**, no pre-placement surfaces and no submission clearance. Their historical negative model outcomes were not rerun.
- Rechecked H33 pixel lineage without generating a candidate. Restored the current request to README/archive; added GEMSDOE89/90 owner claims with date/evidence class; preserved their previously unscored historical archive and audited-byte receipts.

### Pass 3 — full requirements and publication recheck

The homepage/executive summary now put the automatic stop and download access before long historical scientific receipts. The current review makes the unmet new-TIFF requirement explicit and separates native-band restoration, registry byte coverage, pair measurements, historical HOLDOUT-DTI and organizer confirmation. The research page adds the four untested proposals without rewriting prior method results. Fleet metadata was refreshed for **92/92** named repositories; no account score/quota was scraped. Browser checks derive the table size from the feed rather than the obsolete hardcoded 88 rows, check the submission-status page, and write a new dated receipt instead of overwriting the 2026-10-23 browser record.

Final command outcomes are recorded in the verification record below. A green release/code/UI audit means the **negative research state is consistently published**, never that a file may be submitted.

## 4. Remaining work / autonomous handoff

1. Keep **DO NOT SUBMIT**. No new candidate HOLDOUT-DTI, canary, surface rho, final-dot registry clearance, raster SHA or submission identity exists for H86G. Do not populate those fields from an unrelated historical artifact.
2. Only an explicit protocol owner revision can resolve the literal witness contradiction; neither PA diagnostics nor a private support threshold can override it. The two incompatible registry records also need an explicit correction policy, not an automatic warp/drop.
3. Obtain a lane assignment and the **actual** shared cache with its preprocessing/footprint receipt. Reconcile the H33 mask discrepancy before claiming reproducibility. Do not rebuild a private cache and call it template reuse.
4. Once those prerequisites genuinely hold: freeze buffered whole-segment spatial folds, derive all catalogue-based features from visible faults only, mask visible pixels exactly, run each isolated-feature leakage canary (AUC >0.90 is leakage pending proof), and compare CSPA to the strongest rerunnable same-split control with a positive paired block CI. Maximum three model experiments/two hours; no slot without a validated improvement.
5. Use the common evaluator/writer and both pre-placement and final-dot full-registry gates. A separate authenticated selector controls the actual remaining weekly quota. Only a submission-page receipt can create ORGANIZER-CONFIRMED evidence.
6. The earlier `[0,1]` rejection cannot be diagnosed without its exact rejected bytes. All published historical TIFF/ZIP outputs are automatically re-read and range/grid checked; local validity is not proof of portal acceptance.
7. The Pages API reported legacy `main /` despite the Actions workflow deploying `docs/`. Local browser/UI checks do not resolve that hosting-configuration discrepancy. Deployment state must be checked after merge; do not report local preview as proof of the remote site.

## Verification record

All three passes are complete. Final local outcomes (2026-10-25):

| Check | Outcome / scope |
|---|---|
| `scripts/protocol_preflight.py` | Measured immutable witness stop; zero uncovered allowed cells; no rule change. |
| `scripts/audit_release.py --measure-registry` | **PASS audit consistency**, all **17/17** inherited TIFF/receipt/ZIP local checks; **DO NOT SUBMIT**. No model or slot. |
| `scripts/audit_registry_inputs.py` | **689/689** files byte-verified; **2 incompatible grids** retained as blockers; no probability-value or candidate clearance. |
| `scripts/audit_concurrent_artifacts.py` | Both inherited final-dot directions and exact H33 lineage measured using pinned shared comparator; no new prediction. |
| `scripts/build_site.py --check` | **PASS**, deterministic evidence-generated site. |
| `scripts/check_site.py` | **PASS**, local links, registered binaries and negative-state safety. |
| `scripts/audit_downloads.py` | **PASS**, **17/17** local format/receipt checks, no authorized submission. |
| `.venv/bin/python -m pytest -q` | **775 passed, 24 skipped, 41 subtests passed** in **325.78 s**. Skips are not evidence of model validation. **42** pending affine-operator warnings originate in the pinned Rasterio dependency, not new synthetic transform code. |
| Chromium 153 UI smoke | **PASS** at **1440×1000** and **390×1000**, **11 pages** each; no overflow, local HTTP errors or JS errors; **17** TIFF/ZIP links per format, downloaded TIFF SHA matched, **92-row** fleet filter worked, and decision/downloads survived JS disabled. Dated page/asset hashes: `docs/evidence/ui-smoke-20261025.json`. |
| `git -c core.whitespace=cr-at-eol diff --check` | **PASS**; existing CSV CRLF convention preserved rather than rewriting unrelated ledger rows. |

The first full-suite run caught a wording regression in the guard distinguishing a byte-distinct file from registry uniqueness. The distinction was restored, the focused test passed, and the full suite above was rerun successfully. The legacy root redirect's false historical “new unique” claim was also removed and regression-tested. Root redirect behavior and local browser success are not proof of remote Pages deployment or organizer acceptance.

No thresholds, shared evaluator/writer bytes, historical model cards, request archives or downloadable raster bytes were changed. No optimizer, selector, account login or submission upload ran. PR/merge and remote check results are reported in the final handoff, not fabricated here.
