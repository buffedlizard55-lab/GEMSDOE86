# H86E-MMT review and handoff — 2026-10-24

## Executive decision

**DO NOT SUBMIT.** The H86E-MMT lane produced a byte-distinct candidate for audit, but it is not a registry-unique submission and is not scientifically promotable. No DrivenData login, organizer receipt, selector decision, or weekly slot was used.

- Candidate: `docs/downloads/gems86-h86e-mmt-marker-translation-44090dots-20261024T224434Z-04001ad9-zeros.tif`
- ZIP: same stem with `.zip`, containing exactly one TIFF
- SHA-256: `c32f67bfb307984ddd1eeaed42cfe6ebceea7c1ecb8e595634f52ba08c8e21c6`
- Evidence: [`h86e-mmt-run-card.json`](../docs/evidence/h86e-mmt-run-card.json), [`h86e-mmt-pa86-chance-overlap.json`](../docs/evidence/h86e-mmt-pa86-chance-overlap.json), [`h86e-mmt-registry-surface.json`](../docs/evidence/h86e-mmt-registry-surface.json), [`h86e-mmt-registry-final-dots.json`](../docs/evidence/h86e-mmt-registry-final-dots.json)

All numerical performance values below are labelled by evidence class. There is no `ORGANIZER-CONFIRMED` number in this lane.

## Three review passes

### Pass 1 — implementation and scientific design

The lane tested a catalogue-blind magnetic-marker translation hypothesis: a buried accommodation-zone or oblique Walker Lane fault could laterally translate a magnetic marker horizon without a mapped Quaternary scarp. Bands 2, 3, and 9 were converted to multi-scale magnetic representations; directional gradients were compared at 200–600 m non-zero lags and against a zero-lag registration control. Band 6 was used only as a radiometric total-count quietness factor, not mislabelled as magnetic tilt. The named non-fault mimics were lithologic/intrusive contacts, remanent volcanic polarity, and flight-line/tie-line seams.

The three fixed arms were:

1. `E1_mmt_tc_decoupled` — translation signal with TC decoupling;
2. `E2_mmt_translation` — translation signal without TC decoupling;
3. `E3_mmt_edge_control` — conventional edge control.

The implementation imports the shared `vendor/gems57` holdout, evaluator, emitter, writer, registry and PA-86 tools. It does not fit a private evaluator or use the catalogue as a feature. Feature-only canaries were run before interpreting the holdout.

### Pass 2 — adversarial review and corrections

The initial run exposed two important process problems:

- The standalone preregistration file was missing when the original scaffolding was first written and the lane was executed. A four-hypothesis design record was then added, with the irregularity stated rather than backdated. Future runs now fail closed unless the machine-readable preregistration exists, contains 3–5 hypotheses with the required mechanism/mimic/novelty/cost/data fields, and matches the fixed 3-arm/2-hour/DTI rules. See [`H86E_MMT_PREREGISTRATION.md`](H86E_MMT_PREREGISTRATION.md).
- The shared registry checker enumerated the restored comparison inventory but reported two historical files with incompatible grid/CRS metadata. The first implementation treated the checker’s surface boolean as sufficient and proceeded. That is corrected in code: `scripts/run_h86e_mmt.py` now requires zero missing entries **and zero registry errors** before placement. The already-produced candidate is retained as a negative audit artifact; its run card records the complete-registry surface gate as false and names the two errors. No threshold was changed and no file was relabelled.

The raw checker also reports the literal full-support witness separately. Its 100% forward support is a known inherited protocol blocker, not evidence that all geological mechanisms are identical. PA-86-02 is therefore retained as the informative like-for-like dot-field decision.

### Pass 3 — final reproducibility and release checks

- `HOLDOUT-DTI` — `gems57-pooled-hide-v2`; whole components hidden with a 3-pixel collar; catalogue features from visible faults only; pooled 200-pixel physical-block interval; 11,321 withheld positives. Candidate: **0.0290016**, 95% CI **[0.0205505, 0.0381435]**. Preregistered visible-collar R0: **0.0338597**, 95% CI **[0.0160428, 0.0502924]**. Paired delta versus R0: **−0.0048581**, 95% CI **[−0.0240017, 0.0149193]**. This is not an organizer score.
- Same-split historical comparator: **HOLDOUT-DTI 0.1240635**, 95% CI **[0.1079703, 0.1403298]**, explicitly historical and not rerun by this lane. It is not a leaderboard projection.
- `LEAKAGE-CANARY` — maximum discriminative AUC across the five fields **0.5321255**, below the hard `0.90` leakage stop.
- `REGISTRY-MEASUREMENT` — 685 inventory entries were enumerated; 2 were incompatible with the pinned submission grid/CRS. Final like-for-like comparison covered 629 dot fields and 54 continuous surfaces. `PA-86-02` found 6 informative chance-adjusted dot-field firings; its gate is false. Rank correlation/overlap findings and full-support firings are retained in the JSON receipts.
- `LOCAL-FORMAT-VALIDATION` — single-band float32, 3730×3292, EPSG:32611, exact sample transform, finite values in [0,1], zero outside the footprint, zero mapped-catalogue positives, 44,090 emitted cells, one-TIFF ZIP, and SHA-256 all pass. This is format validity, not scientific authorization.
- Repository gates: `628 passed, 24 skipped, 42 warnings, 41 subtests` in the final full repository test run (including the concurrent registry-integrity tests); `scripts/audit_downloads.py`, `scripts/check_site.py`, `scripts/build_site.py --check`, and the release audit pass. All 14 published TIFFs remain audit-only and negative.

## What GEMSDOE32 `0.2778` means

`0.2778` is preserved as **OWNER-REPORTED**, not as an organizer receipt. At PhD level, the most defensible interpretation is that it is an outcome of a particular submission raster, the organizer’s hidden truth and a nonlinear 300 m triangular-kernel credit function—not a calibrated estimate of fault probability. A dense or repeated family of dots can gain/lose credit through kernel coverage, nearby-dot redundancy, fault-collar placement, and hidden-fault geometry. Pixel containment or a high HOLDOUT-DTI number cannot identify the causal component without a like-for-like spatially blocked evaluation and an organizer receipt.

The repository’s forensic comparisons explain lineage and possible mechanisms (catalogue following, collar geometry, and dot concentration), but they do not prove that any one feature caused the owner-reported score. The H86E-MMT result is far below that claim on its holdout instrument and must not be projected onto the private leaderboard. Conflicting prompt values such as `0.3195` and `0.4413` remain **OWNER-REPORTED** and unverified.

## Official source boundary

- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and): official airborne magnetic/radiometric and lidar release; used for layer semantics and physical plausibility, not labels.
- [USGS Nevada magnetic compilation](https://pubs.usgs.gov/ds/2006/234/): official interpretation that magnetic anomalies/derivatives can delineate buried faults and geologic boundaries.
- [USGS magnetic interpretation guidance](https://pubs.usgs.gov/fs/fs-0236-95/fs-236-95.pdf): official physical basis for magnetic-mineral contrasts and derivative boundaries.
- [DOE/NREL GDR INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391): official multi-physics context, not an organizer truth source.
- [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution): baseline software context only; it provides no receipt for this lane.

## Handoff

Keep the candidate and all evidence for reproducibility. Do not upload, do not spend a selector slot, do not call the result an organizer score, and do not weaken the registry thresholds to rescue it. A future lane may run only after a contemporaneous preregistration, a zero-error complete surface registry check, the shared holdout gates, final-dot PA-86-02, and an independent local-format/ZIP/SHA audit all pass.
