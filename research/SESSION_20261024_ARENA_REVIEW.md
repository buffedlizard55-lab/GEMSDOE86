# Independent repository review follow-up — 2026-10-24

## Decision

**NEGATIVE — no new TIFF, model experiment, leaderboard score, or submission slot was produced.**
The preflight remains fail-closed, no single method paragraph/lane was assigned in the request, and the required shared cached feature stack is not present. Existing download artifacts remain explicitly **DO NOT SUBMIT**. The current machine-readable decision is [`docs/evidence/latest-review-run-card.json`](../docs/evidence/latest-review-run-card.json).

This follow-up records an independent code/data review of the current checkout, a verified raster-level explanation of the H33 artifact, a nomenclature fix in the registry preflight, and a fresh read-only GitHub metadata refresh. It does not claim the user's mandatory unique competition TIFF was generated; that deliverable remains unmet.

## Evidence classes and access boundaries

- The user's `0.2778` for `GEMSDOE32` H33, and the competing `0.3195` / `0.4413` “current high score” statements, are **OWNER-REPORTED** claims, not **ORGANIZER-CONFIRMED** receipts in this checkout. They conflict as current-leaderboard statements and were not independently checked against the DrivenData portal in this pass.
- The raster counts and pixel identities below are **LOCAL FILE MEASUREMENTS**, not scores. Holdout values in inherited experiment cards are **HOLDOUT-DTI** only for their stated evaluator, folds, positive count, and interval; none validates the new H86E-SPBT proposal.
- Official-source observations already stored in [`docs/evidence/source-recheck-20261024.json`](../docs/evidence/source-recheck-20261024.json) are dated evidence from an earlier review on the same day. They were not freshly fetched in this pass: non-GitHub external hosts are outside the present sandbox's outbound allowlist. DrivenData is also not scraped under the repository's access policy. Links for manual review are listed below.
- The refreshed fleet is **REPOSITORY-METADATA** from GitHub `main` trees, not a leaderboard feed, score receipt, complete raster registry, or validation of raster contents.

## H33 forensic answer: what the `0.2778` artifact actually changed

I independently opened the hash-pinned local mirrors of the `GEMSDOE28` `h27-4-r1-solo-d2-8` raster, the `GEMSDOE32` H33 raster, `GEMSDOE36` Anderson raster, and `existing_faults.tif`. All four grids matched the H33 grid. The H33 file contains **37,654 positive cells**; its D2.8 parent contains **40,199**. H33 is exactly the D2.8 dot field with every parent dot at catalogue distance `<= 2.0` pixels removed: **2,545** dots removed, zero added, and the resulting Boolean arrays are pixel-identical. The G36 artifact contains all H33 dots plus **1,200** additions. These are raster forensics only; the values are not DTI results.

The plausible scoring mechanism is an asymmetric-metric tradeoff, not proof of a newly discovered geological signal. With the shared kernel metric, reducing a prediction can improve DTI if it removes mostly false-positive mass while preserving coverage of withheld truth; it can lower DTI if the pruned collar was covering real, unmapped parallel faults. Dot spacing around the kernel scale does not make kernel neighborhoods disjoint, and a raster comparison cannot reveal which of those mechanisms applied to the organizer's hidden labels. Therefore the pixel identity explains **how H33 differs from its parent**, but does not establish why the owner-reported result was higher or prove that it was accepted by the organizer.

**Can this project claim it will beat `0.2778`? No.** The `0.2778` comparator is not an organizer receipt, and there is no newly evaluated, same-fold, paired physical-block HOLDOUT-DTI for the top proposal. Existing holdouts from different fold designs must not be ranked as one “current best.” A holdout improvement would still not guarantee a leaderboard gain or organizer confirmation.

## Candidate hypotheses already preregistered (not run in this follow-up)

These five proposals are already in [`registry/h86c_hypotheses.json`](../registry/h86c_hypotheses.json); this review does not present them as new experimental results. Rank is qualitative expected information gain per implementation cost, **not a numerical DTI forecast**. Each needs isolated-feature leakage canaries, visible-fault-only feature generation, buffered whole-component holdout, and registry checks before any selector considers a slot.

| Rank / hypothesis | Layers and targeted signature | Why it could find a catalogue-missing structure; distinction from this repo | Main non-fault mimic | Cost / data status |
|---|---|---|---|---|
| 1. **H86E-SPBT** — signed paired-throw basement/gravity concordance | Competition `depth_to_base_surf` (Band 15), `iso_grav_anom` (Band 13), `det_elev` (Band 12), `det_elev_slope` (Band 19), and `tmi_hg` (Band 3); test opposite flank steps with shared downthrown polarity and strike continuity beneath low-relief basin fill. | Hypothesis: buried intrabasin dip-slip steps may retain basement-depth and gravity polarity where surface scarps are muted. Unlike the executed unsigned gradients, tilt/curvature ridges, and isotropic vent halos, this tests **signed cross-flank polarity concordance**. | Erosional paleovalley margins, caldera moat walls, gravity-inversion artifacts. | Low–medium; no new external source required by the proposal, but the required pinned shared feature cache is absent and protocol preflight stops before construction. **Not validated.** |
| 2. **H86E-MMT** — magnetic marker-horizon translation | Competition RTP (Band 2), `tc` (Band 6), `tmi_hg` (Band 3), and GeoDAWN radiometric channels; two-sided window phase correlation for coherent nonzero lateral translation, with survey-seam controls. | Could target oblique transfer/relay faults that offset buried volcanic markers without a strong range-front scarp. Existing lanes compare gradients, upward continuation, tilt, and cross-gradients; they do not measure paired-flank lateral phase translation. | Intrusive contacts, primary lava-flow boundaries, remanence changes, GeoDAWN flight/tie-line seams. | Medium–high; feature inputs are not restored as the required shared cache. **Not validated.** |
| 3. **H86E-HMDC** — magnetic destruction troughs aligned with vent/sinter corridors | RTP (Band 2), `tmi_vg` (Band 9), surface conductance (Band 17), geodetic dilatation (Band 8), shear rate (Band 7), plus proposed GDR-1391 sinter/tufa, temperature-probe, and vent observations; seek negative magnetic curvature with positive shoulders along aligned corridors. | Targets a proposed hydrothermal alteration/relay signature, distinct from H86D's positive magnetic ridges and radially isotropic point halos. Whether the proposed alteration signature is detectable at this grid resolution is unproven. | Reversed-polarity volcanic flows, low-susceptibility felsic tuffs, survey seams. | Medium; pinned mirrors are described in the repo, but bytes were not restored in this follow-up and no experiment was permitted. **Not validated.** |
| 4. **H86E-MTCS** — depth-separated MT conductance plus heat flow | Official USGS 3D MT conductance at multiple depths (DOI `10.5066/P9TWT2LU`), USGS heat flow (DOI `10.5066/P9BZPVUC`), and competition conductance/geodetic bands. | Could distinguish deep fluid conduits from shallow playa conductors; no current local lane ingests these depth-separated products. | Graphitic/sulfidic strata and non-geothermal saline conductors. | Medium–high; **not viable yet**: the official data are named, but raster bytes/metadata/coverage were not obtained here. Sources: USGS ScienceBase/DOI links below. |
| 5. **H86E-WCS** — watershed-crossing 1 m LiDAR scarp curvature persistence | Native USGS 3DEP 1 m bare-earth DEM tiles, with competition `det_elev` / `det_elev_slope`; signed 5–25 m cross-strike profile steps persisting across drainage divides. | Could test whether subtle piedmont scarps disappear in the coarser competition summaries; prior local lanes use summarized LiDAR/topographic features, not native 1 m multi-catchment persistence. | Lake Lahontan shorelines, fluvial terraces, roads/rail grades. | High; **not viable yet**: the competition's `1m_DEM_links.csv` and native tile bytes are not present, and the listed tile host is outside the current outbound allowlist. |

No score projection is assigned to any proposal. For hypotheses requiring external data, a public landing page or DOI is not evidence that the raster bytes are obtainable and correctly aligned; their status remains not viable until licensed bytes, metadata, coverage, and hashes are available.

## Why no holdout experiment or new TIFF was created

1. The request refers to a “single method paragraph” as the lane assignment, but no such method paragraph is present in the supplied prompt. We did not choose a private lane.
2. The actual shared cached feature stack is absent. A raw mirrored feature TIFF is not that cache and the project rules explicitly prohibit rebuilding it as a substitute.
3. The restored, SHA-pinned owner-mirror registry witness (`data/registry/dense-witness.tif`, SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`) has positive support on **5,106,385 / 5,106,385 allowed cells** under the current inherited `finite prediction > 0` definition. The shared preflight therefore reports `STOP_LITERAL_OVERLAP_UNSATISFIABLE` and blocks model fitting and placement. This is **REGISTRY-MEASUREMENT**, not a measurement of a new candidate and not proof that the registry is complete.
4. The repository's shared uniqueness module also contains a two-phase report that distinguishes continuous surfaces from dot fields, while the mandatory preflight still applies the literal positive-support certificate. That is a **protocol/schema ambiguity** requiring an upstream decision; this follow-up did not silently change thresholds, exempt continuous rasters, or edit the vendored template.
5. No candidate surface existed to test rank correlation, no final dots existed to test final overlap, and no candidate was eligible for submission. The stored HOLDOUT-DTI results from other hypotheses do not substitute for this validation.

## Code review fix and verification

The preflight previously emitted `measured_date_utc: 2026-10-22` as a hard-coded value copied from the witness pin. That label could be mistaken for the date of the latest measurement. It now emits `witness_pin_verified_date_utc`, derived and ISO-date-validated from `research/registry_witness_pin.json`; the independently refreshed measurement timestamp remains in the current review/run-card evidence. A regression test rejects missing, malformed, or non-normalized pin dates. Shared evaluator, writer, validator, uniqueness thresholds, and vendored bytes were not changed.

The repository's 92-project GitHub tree feed was freshly refreshed successfully: **92/92** snapshots, **0** organizer receipts, **0** rasters generated, **0** submission slots used. This is a Git-metadata feed only.

## Three-pass record

1. **Pass 1 — inspect and reproduce:** Read the standing prompt and current README, restored SHA-pinned proof inputs through GitHub mirrors, independently reproduced H33's exact dot-set relation, and reran the existing unit, site, and download gates. The baseline suite passed **491 tests** with **24 skips**, **41 subtests**, and **4 dependency deprecation warnings**; this is software verification, not HOLDOUT-DTI.
2. **Pass 2 — review and fix:** Found the misleading hard-coded preflight date label; renamed it to pin-verification provenance, derived it from the immutable pin, and added regression coverage. Refreshed the 92-project GitHub metadata feed only after all target snapshots returned successfully.
3. **Pass 3 — final recheck:** The final suite passed **492 tests**, with **24 skipped**, **41 subtests**, and **4 dependency deprecation warnings**. `build_site.py --check`, `check_site.py`, `audit_downloads.py`, and `audit_release.py --measure-registry` all passed; all **10** inherited research TIFFs pass local format/ZIP/receipt checks, but remain **DO NOT SUBMIT**. The complete fleet refresh is timestamped `2026-10-24T18:22:32+00:00`; the final registry measurement is timestamped `2026-10-24T18:24:21+00:00`. Shared-template hash checks passed. The final machine-readable card remains negative and declares the unique-TIFF requirement unmet; no hypothesis was trained or selected.

## Official/source links for manual review

These are source links already recorded in the repository's dated source review. The current follow-up did not freshly fetch non-GitHub external hosts.

- [DrivenData competition problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).
- [Official GEMS rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), DOI `10.5066/P93LGLVQ`.
- [DOE Geothermal Data Repository, INGENIOUS regional compilation](https://gdr.openei.org/submissions/1391), DOI `10.15121/1881483`.
- [UNR Great Basin Center for Geothermal Energy / INGENIOUS](https://gbcge.org/current-projects/ingenious/).
- [USGS Great Basin MT electrical conductance](https://doi.org/10.5066/P9TWT2LU) and [USGS conductive heat flow](https://doi.org/10.5066/P9BZPVUC); these data were **not obtained in this follow-up**.
- [Official DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b).
- [EPSG:32611](https://epsg.io/32611).
- [GEMSDOE32 owner project page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) — owner-hosted artifact information, not an organizer score receipt.

## Next work, in order

1. Obtain an explicit lane assignment and settle the surface-vs-dot registry representation rule with the shared protocol/template maintainers; do not patch the vendored copy.
2. Restore the actual hash-pinned shared feature cache and a current accessible registry; verify each input's bytes, grid, coverage, and provenance.
3. Freeze a comparable spatially blocked baseline and buffered whole-segment folds; derive catalogue features from visible faults only, mask visible fault pixels exactly, and run each feature-alone leakage canary.
4. Evaluate the chosen candidate through the pinned shared evaluator, with pooled HOLDOUT-DTI, evaluator/version, withheld-positive count, paired 95% spatial CI, and the same folds/budget for comparator arms.
5. Check surface rank correlation before placement and final-dot overlap after placement against the complete accessible registry. Only then run the local submission validator. Keep slot selection separate and require an organizer receipt after any authorized upload.
6. For H86E-MTCS / H86E-WCS, first obtain the named official raster bytes and metadata from the cited source. No score, target improvement, or submission readiness is assumed.
