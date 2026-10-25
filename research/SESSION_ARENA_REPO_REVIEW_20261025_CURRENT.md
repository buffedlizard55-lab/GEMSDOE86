# Three-pass repository review — 2026-10-25 — `arena/3d912985-gemsdoe86`

> **Historical snapshot:** measured before integrating newer `origin/main` trees (`d04d637` and later). At that time the release inventory contained 32 artifacts. Subsequent upstream integrations expanded the audit to 35 registered artifacts and added later lane reviews; this report remains an audit trail of this session's no-lane review, not current release status.

## Executive decision

**DO NOT SUBMIT. No new TIFF was generated, no geological experiment was run, and no weekly slot was used.** The request's parallel-run rule says to follow one assigned method paragraph, but the archived request contains no such assignment. More importantly, the repository's unchanged literal-support interpretation of the registry gate has a verified counterexample that blocks every nonempty candidate: every allowed footprint cell is positive in one SHA-pinned historical **continuous probability surface**, so literal support overlap is `1.0`, above the `0.70` stop. This is not a measured dot-to-dot overlap against a discrete dot set; the continuous-vs-discrete interpretation is an unresolved protocol issue. Under the current mandatory literal rule, this single witness is sufficient for a negative; it is not a complete registry or uniqueness clearance. The actual shared-template feature cache is also absent. A candidate run or TIFF would violate the prescribed stop and could not be honestly described as validated.

The request's hard requirement to generate a new, unique competition TIFF remains **unmet**. The homepage and README make the current state explicit: audit downloads are not submission-authorized. A new TIFF cannot responsibly be produced within this review.

## Score claim and H33 interpretation

- `GEMSDOE32` H33 `0.2778` is **OWNER-REPORTED**, supplied in the request; no submission-page receipt was available. The request also contains conflicting `0.3195` and `0.4413` leaderboard claims, which remain **OWNER-REPORTED / unverified** here. None is **ORGANIZER-CONFIRMED**.
- Existing pixel forensics identify H33 as the 40,199-dot D2.8 parent minus 2,545 pixels in the `1 < d_cat <= 2 px` collar, leaving 37,654 dots and adding none. This establishes a raster edit, not why an organizer metric assigned the claimed score.
- The plausible metric mechanism is coverage-efficient thinning. With the competition's asymmetric Tversky weighting (`alpha=0.2`, `beta=0.8`) and a 300 m triangular kernel, duplicate predictions can add false-positive mass after local truth credit is already saturated; deleting low-marginal-credit dots can therefore help. But the kernel remains active around catalogue cells: a collar dot can still cover a withheld fault, so the removed 2,545 dots are not known to have zero true-positive credit. The observed owner-reported difference is confounded by no organizer receipt and cannot prove causal benefit.
- Whether a new idea can exceed H33 or either leaderboard claim is **unknown**. The repository's various spatial holdouts do not establish live private-test performance, and unlike holdout designs must not be ranked as a single best. No projection is made.

Evidence for the bounded interpretation: [`research/H33_INTERPRETATION_REVIEW.md`](H33_INTERPRETATION_REVIEW.md), [`research/H33_ANALYSIS.md`](H33_ANALYSIS.md), [`docs/evidence/h86f-h33-forensics.json`](../docs/evidence/h86f-h33-forensics.json), and the source site named in the request: [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html). These links do not supply a submission-page receipt.

## Ranked hypotheses for a future authorized run

The three entries below are from the repository's current unrun native-layer queue ([machine-readable register](../registry/followup_hypotheses_20261025.json)). Novelty is scoped to this checkout's implemented `src/` and `scripts/`, not the scientific literature or every GEMSDOE site. These are qualitative experiment priorities, **not score estimates**. No new external raster is required by these methods; however, the required shared feature cache and native feature TIFF are not present in this workspace, so none is runnable under the current reuse rule.

| Rank | Hypothesis; specific layer(s) | Physical signature and why it might find uncatalogued faults | Difference from implemented checkout methods | Named non-fault mimic | Expected DTI information / implementation cost |
|---|---|---|---|---|---|
| 1 | **BMR — basement-interface gravity mass-balance residual.** Band 15 `depth_to_base_surf` and Band 13 `iso_grav_anom`. | Fit a frozen, fold-safe forward gravity response from the basement-depth interface, then inspect persistent, localized cross-strike residual steps after removing broad basin response. A buried displacement could produce a density boundary without a mapped surface scarp. | Existing H86E-SPBT pairs basement/gravity steps; H86H-PSTD uses gravity-tensor features; H86K-PSC uses saddle/ridge topology. None is the proposed explicit forward-model residual test. Band 15 is gravity-derived, so treating it as independent confirmation would be circular. | Lateral sediment-density change; gravity-derived basement-depth model error/smoothing; edge ringing. | **Highest qualitative priority; moderate, uncertain expected lift. High cost:** verify units/sign, fit only training blocks, and stress-test density contrast and boundaries. |
| 2 | **GSST — gravity step-versus-compact-source shape discrimination.** Bands 13 `iso_grav_anom`, 5 `iso_grav_anom_slope`, 11 `iso_grav_anom_vg`, 18 `iso_grav_anom_hg`. | At preregistered scales, compare normalized cross-strike derivative width and signed east/south gradient patterns with extended-step and compact-source responses. A buried extended discontinuity could be missed by single-maximum ridge methods. | Existing H86F-GZZD / H86H-PSTD use gravity curvature/derivatives; H86K-PSC uses Hessian saddle/ridge topology. The explicit competing step-versus-compact response model is different. Bands 11/18 are directional horizontal derivatives, not conventional vertical gravity derivatives. | Elongated intrusive/lithologic contact, basin-margin facies change, or overlapping compact sources. | **Low-to-medium qualitative information; medium cost:** scale-matched templates and sensitivity checks for source depth/bandwidth. |
| 3 | **CNT — threshold-persistent conductivity neck conditioned on strain.** Band 17 `cond_surf`, Band 8 `geod_dilaterate`, Band 7 `geod_shearrate`. | Track narrow conductive connections across a frozen threshold-persistence interval; test whether necks co-locate with positive dilatation/coherent shear against separate conductivity-only, strain-only, and randomized-neck controls. A concealed fluid pathway might have no surface scarp. | Existing checkout methods use conductivity highs, margins, gradients or halos; no threshold-persistent conductive-component neck extraction conditioned on dilatation was found. It is not depth-resolved MT: this is one surface-conductance band. | Saline playa, clay-rich paleochannel, or interpolation/gridding bottleneck. | **Lowest qualitative priority; medium cost and high confounding risk:** topology may be unstable, and conductivity is nonspecific. |

**Top-candidate validation disposition:** BMR was not evaluated. The literal uniqueness stop, absent assigned lane, and absent shared cache precede any candidate surface or holdout. Therefore there is no valid candidate score, feature-alone canary, candidate correlation, final-dot overlap, or promotion decision. No weekly slot was touched. If the owners later authorize a rule-consistent lane and provide the real cache, the preregistered test must use the existing evaluator/writer, buffered whole-segment hide-and-recover, visible-fault-only feature derivation, exact visible-fault masking, pooled DTI (`alpha=0.2`, `beta=0.8`, 300 m triangular kernel), feature-alone canaries, paired block-bootstrap uncertainty, and both surface/final-dot registry checks; stop at three experiments or two hours.

## Three-pass work and verification

### Pass 1 — read the prompt and inspect the checkout

- Read `AGENTS.md`, `PROMPT.md`, `README.md`, and the full archived request `research/REQUEST_20261025.md` before changes. Confirmed the branch is `arena/3d912985-gemsdoe86` at starting commit `b49a373b11be1f7fa8685039ed31db56c8d0de73`.
- Installed the exact `requirements-lock.txt` into ignored `.venv/`; no dependency lock was changed.
- Initially, the local witness measurement could not run because root-level sample/catalogue mirrors were absent. Used the repository's pin-verifying `scripts/restore_protocol_data.py --include-registry`; the two competition mirrors are owner-supplied, hash-pinned bytes, **not organizer-authenticated**. Restored the pinned historical witness, not a prediction.
- Fresh `scripts/protocol_preflight.py` measurement: witness SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`; one raster measured; all `5,106,385` allowed pixels covered; `0` uncovered; literal overlap `1.0`; registry snapshot `655` entries and explicitly incomplete. It generated no candidate.
- `scripts/audit_workspace_inputs.py --require-native`: required `training_features.tif` is missing from both `data/` and `data/bridge/`; prepared feature arrays are missing; shared template cache is unestablished. Exit status `1` is expected and confirms these blockers.

### Pass 2 — adversarial publication and evidence review; fix defects found

- The release audit originally failed closed because the H86L-FMC TIFF and ZIP in `docs/downloads/` were not registered in `docs/evidence/download-inventory.json` and `registry/artifact_cards.json`. This was a real site/release-index inconsistency. Registered the existing files by their existing receipt digest, retained `DO NOT SUBMIT` / false slot approval, added explicit `h86l_fmc` audit handling, and regenerated evidence/site outputs using the existing tools. The H86L run card's fleet-derived holdout is marked leakage-suspect; the release audit now withholds its numeric DTI from trusted HOLDOUT-DTI summaries and checks its recorded duplicate-negative state. No raster bytes or scientific result were changed.
- Added regression coverage to ensure H86L stays unvalidated for performance and the negative/no-slot status cannot be erased.
- Full-suite review exposed an old test that compared a dated prior review card's timestamp to the newly refreshed mutable preflight clock. The historical card was correctly retained unchanged; the test now verifies the historical card's internal chronological consistency and that its measurement is no newer than the current measurement. This separates historical evidence from live audit freshness.
- Updated README's current-status banner and 32-artifact count; the complete owner request remains archived. The stale H86L omission statement was replaced with the actual repaired status.

### Pass 3 — fresh integrated checks

Final commands run after fixes:

```text
.venv/bin/python scripts/audit_release.py --measure-registry
  PASS — 32/32 published TIFFs locally valid; all remain DO NOT SUBMIT; 0 experiments, 0 slots.

.venv/bin/python scripts/audit_downloads.py --write
  PASS — all 32 TIFF/receipt/ZIP sets re-read from disk.

.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_site.py --check
  PASS — evidence-generated site rebuilt and deterministic check passed.

.venv/bin/python scripts/check_site.py
  PASS — links, registered TIFF/ZIP integrity, and negative-state safety.

.venv/bin/python scripts/review_repository.py --timeout 900
  PASS — all seven release/test/frozen-evidence/site/link/download/live-input checks.
  Full suite: 1004 passed, 24 skipped, 48 warnings, 58 subtests passed (306.18 s).
  Release audit: 32/32; download audit: 32/32; current decision DO NOT SUBMIT.
  Live-input inspection passed as software, but training readiness is false because
  native features/prepared arrays/shared cache are absent.
```

No candidate-generation script, experiment, TIFF writer, upload, automated DrivenData access, score receipt, or slot selector was run. The exact file rejected with the historical `[0,1]` portal error is not in this checkout, so its cause cannot be identified. The local audit can demonstrate range/grid validity for available historical files, not portal acceptance.

## Sources and access limits

Links retained for independent/manual verification; not freshly scraped in this review:

- [Official competition problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official competition rules and data portal](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Official DrivenData reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution)
- [DOE/NLR GEMS rules/submission PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE Geothermal Data Repository — INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391)
- [EPSG:32611 reference](https://epsg.io/32611)

`AGENTS.md` prohibits automated scraping of DrivenData. The current session did not access the login-walled DrivenData data or submission pages. The only layers in the three hypotheses are bands in the competition-native data map; no additional public dataset is required by those proposals. Their data still cannot be evaluated without the missing native feature TIFF and, more importantly, the real shared cache with preprocessing and visible-mask identity.

## Remaining blockers / handoff

1. An authorized protocol clarification is needed for the literal full-support overlap rule. Do not privately change its threshold, exempt rasters, or bypass preflight.
2. Assign one explicit method paragraph; the current request's lane reference has no paragraph to identify.
3. Restore/identify the actual shared template feature cache and establish its provenance. A raw TIFF mirror or locally reconstructed stack is not equivalent.
4. Restore the competition-native training feature file from an authorized account/mirror and pin/verify its identity; do not claim login-walled data is available. This workspace lacks it.
5. Only after 1–4, preregister one hypothesis and run like-for-like holdout/canary/evaluator/writer gates within the budget. Do not choose or spend a submission slot; a separate selector must use the live submission quota.
6. An authenticated submission-page receipt is required for any ORGANIZER-CONFIRMED score or remaining-quota claim. Never scrape DrivenData.
7. The requested unique, easy-download **submit-ready** TIFF is not present or approved. Existing TIFFs remain reproducibility downloads only.

## Run card — this review

```json
{
  "hypothesis": "No method lane assigned; ranked future options are BMR (Bands 15+13), GSST (Bands 13+5+11+18), and CNT (Bands 17+8+7); none was run.",
  "mechanism": "No candidate mechanism was evaluated. H33's measured raster edit removes 2,545 dots at 1<d_cat<=2 px from its D2.8 parent; reduced low-marginal-credit prediction mass is plausible but unproven as the cause of the OWNER-REPORTED 0.2778.",
  "named_non_fault_process": "For top-ranked BMR: lateral sediment-density changes, errors/smoothing in the gravity-derived basement-depth surface, or model-edge ringing.",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "status": "NOT_RUN_NO_LANE_ASSIGNED_AND_PROTOCOL_STOP",
    "evaluator_version": "gems57-pooled-hide-v2",
    "withheld_positives": null,
    "value": null,
    "ci95": null
  },
  "correlation_overlap_vs_registry": {
    "evidence_class": "REGISTRY-MEASUREMENT",
    "candidate_surface_spearman": null,
    "candidate_final_dots_overlap_3px": null,
    "witness_sha256": "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be",
    "witness_allowed_pixels": 5106385,
    "uncovered_allowed_pixels": 0,
    "literal_forward_overlap_for_any_nonempty_allowed_candidate": 1.0,
    "stop_threshold": 0.70,
    "registry_snapshot_entries": 655,
    "registry_complete": false,
    "candidate_generated": false
  },
  "raster_sha256": null,
  "validator_output": {
    "status": "NOT_RUN_NO_CANDIDATE",
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "submission_authorized": false,
    "inherited_format_audit": "32/32 existing published TIFFs pass local format/integrity checks; this is not upload clearance"
  },
  "submission_name": null,
  "note": "No TIFF created: lane unassigned and literal uniqueness stop; no slot selected.",
  "experiments_run": 0,
  "submission_slots_used": 0,
  "safe_to_submit": false,
  "approved_for_weekly_slot": false,
  "verdict": "negative"
}
```

## Post-review integration note — upstream H86M-LT (later `origin/main`)

This note is separate from the historical review above; it does not retroactively change its no-lane results. The later upstream H86M-LT report (`research/H86M_LT_REVIEW.md`, session `ecc314b3`) records a 37,654-dot candidate and a lane-local `promote` verdict based on its PA-86 validation: format checks, a full-restored-registry uniqueness scan, and score-tomography diagnostics. It reports max forward 3-px overlap 0.649 against a 0.70 cap over 414 registered dot-fields. The candidate's own card still says `approved_for_weekly_slot=false`; no slot was used and no organizer score is established.

**Do not treat that lane verdict as this review's requested HOLDOUT-DTI or as global upload authorization.** H86M-LT's review says its validation is tomography fitted to owner-reported fleet scores because the catalogue hide-and-recover instrument was considered invalid for the off-catalogue fleet emission. That is a different evidence design from the required whole-segment buffered hide-and-recover evaluation. The upstream README also identifies a release-integration gap: the H86M-LT TIFF is not included in the generated download inventory, while the repo-wide literal continuous-support audit continues to say `DO NOT SUBMIT`. Consequently, this review did not select, endorse, or submit the candidate. Its live status must be rechecked with the release, inventory, and site audits after integration; no user slot should be spent absent explicit owner selection and an organizer-confirmed result.
