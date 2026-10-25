# Repository review — 2026-10-25 — `arena/c003fde3-gemsdoe86`

## Decision

**NO-GO: DO NOT SUBMIT. The requested new unique TIFF was not created.** This review was read-only with respect to model outputs: no candidate raster, experiment, submission selection, or upload was made; zero weekly slots were used. A docs correction records a previously identified causal-interpretation error in the README. The reason not to fabricate a deliverable is measurable: after restoring the pinned format/witness inputs, the unchanged literal protocol preflight found that the registry witness covers every allowed prediction cell. Any nonempty allowed dot set therefore has 1.0 forward overlap with that witness, exceeding the specified 0.70 stop. This is sufficient to reject a candidate; it does **not** prove the registry complete or certify any candidate unique. See the [current run card](../docs/evidence/session-c003fde3-run-card.json) and the measured [protocol preflight](../docs/evidence/protocol-preflight.json).

There is also no assigned single-method paragraph in the current owner request. The actual `training_features.tif`, prepared arrays, and actual shared template feature cache are absent from the current workspace. The historical `data/prepared_manifest.json` is not proof that these data exist now. Without an assigned method and those exact shared inputs, a compliant holdout or feature canary cannot be run. We did not substitute a private feature rebuild.

## H33 (`h33-h33-2-b2`) finding

- The prompt's **0.2778** is an **OWNER-REPORTED** score claim: the repository's `registry/prior_scores.csv` says no submission-page receipt was located. It is not **ORGANIZER-CONFIRMED**. The request also contains conflicting leaderboard maxima; neither is authenticated in this checkout.
- The hash-pinned raster comparison records a **RASTER-MEASUREMENT**: the GEMSDOE28 parent has 40,199 unit dots, H33 has 37,654, and H33 is the parent with 2,545 dots removed and none added. Removed-dot distances are √2–2 pixels from the mapped catalogue. See [`research/H33_ANALYSIS.md`](H33_ANALYSIS.md) and [`docs/evidence/h86f-h33-forensics.json`](../docs/evidence/h86f-h33-forensics.json).
- This establishes the pixel edit, **not why the unverified reported score differed**. Under the metric's max kernel-credit behavior, removing redundant predictions can reduce false-positive mass without losing much truth credit, so coverage-efficient thinning is a plausible conditional mechanism. But a near-catalogue dot can also be the only one covering a withheld fault. No causal effect or score gain is established; no leaderboard projection is made.
- Consequently, this checkout does not establish that it can beat 0.2778. A competition result requires an organizer receipt; a local catalogue-hide HOLDOUT-DTI is not a live-score projection.

## Ranked proposals and validation status

The current repo already has a better-bounded proposal list than inventing a new method here: [`registry/followup_hypotheses_20261025.json`](../registry/followup_hypotheses_20261025.json). Its `lane_assignment` is `null`; statuses are proposals/not run. It names **three** methods not found as executed candidate experiments in the scoped `src/` and `scripts/` inventory, while explicitly excluding methods now implemented (including CSPA, monogenic phase, H86K-PSC saddle topology, and GDSC). These novelty claims are scoped to this checkout, not all 92 sibling sites or the literature. The qualitative ordering below is not a numerical DTI forecast:

| Rank | Proposal and input layers | Target signature and missing-catalogue rationale | Main mimic / novelty / cost |
|---|---|---|---|
| 1 | **BMR: basement-interface gravity mass-balance residual** — band 13 `iso_grav_anom`; band 15 `depth_to_base_surf`. | Fit a fold-local forward basement gravity response and test a persistent cross-strike residual. A narrower residual could expose buried basement displacement beneath fill without relying on a surface scarp. | Lateral sediment-density changes, errors/smoothing in the gravity-derived depth surface, and edge ringing; band 15 is not independent of gravity. Different from simple gravity/basement gradient pairing because it tests a frozen physical forward residual. **High cost**, medium qualitative promise, substantial circularity risk. |
| 2 | **GSST: gravity step-versus-compact-source shape test** — bands 13, 5 (`iso_grav_anom_slope`), 11 (`iso_grav_anom_vg`), 18 (`iso_grav_anom_hg`). | Compare frozen multi-scale signed horizontal-gradient widths with extended-step versus compact-source templates; an extended buried step could be distinguished from isolated bodies. | Elongated intrusive contacts, facies changes, overlapping compact sources; differentiated from existing derivative/tensor features by explicit competing-source likelihoods. **Medium cost**, low-to-medium qualitative promise. |
| 3 | **CNT: conductivity-neck topology conditioned on dilatation** — band 17 `cond_surf`; bands 8 `geod_dilaterate`, 7 `geod_shearrate`. | Detect persistent narrow connections between conductive patches, requiring independent strain corroboration; potentially identifies covered pathways rather than broad conductive halos. | Saline playa, clay-rich paleochannels, gridding bottlenecks; differentiated from simple conductivity margins/halos by threshold-persistent neck topology. **Medium cost**, lowest qualitative specificity. A single surface-conductance layer is not depth-resolved MT. |

No new external dataset is required by these proposal definitions; they use named competition bands. That does **not** make them presently viable: the native feature TIFF and shared cache are missing locally, and no candidate can pass the literal overlap gate. The official competition data page is login-gated and must not be scraped; the competition's official reference repository is linked in the queue. The exact README data-mirror hashes establish byte identity only, not organizer provenance. The top-ranked BMR candidate was **not validated**: with zero experiments permitted by the present stop, there is no HOLDOUT-DTI value, CI, canary, or surface measurement to report. The existing proposal registry contains the full signatures, controls, falsifiers, and required preconditions.

## Three review passes

### Pass 1 — inventory and requirements

Read `AGENTS.md`, the complete `PROMPT.md`, `README.md`, `research/REQUEST_20261025.md`, current run cards, release evidence, candidate queue, and H33 forensic records. Confirmed that the README already archives the request and puts a clear audit/download-vs-submit status at the top. Confirmed current branch is `arena/c003fde3-gemsdoe86` and was clean before this review.

### Pass 2 — rerun critical read-only checks and inspect irregularities

Installed the exact pinned Python dependencies in the ignored `.venv` (no tracked dependency changes). `scripts/audit_workspace_inputs.py` initially reported missing root copies; restored only SHA-pinned `sample_submission.tif`, `existing_faults.tif`, and the historical witness using `scripts/restore_data.py --protocol-only --include-registry`. This restoration did not restore training features or the template cache. The refreshed `scripts/protocol_preflight.py` confirms **REGISTRY-MEASUREMENT**: allowed domain 5,106,385 cells; witness uncovered cells 0; implied overlap 1.0 > 0.70; no candidate generated. `scripts/audit_workspace_inputs.py --require-native` separately confirms `training_features.tif` missing, prepared arrays missing, and shared cache not established. These are independent blockers.

The initial un-restored `protocol_preflight.py` invocation exited nonzero because its expected root sample TIFF was absent; after hash-verified restoration it ran successfully and refreshed its measurement. This was an environment/input issue, not a scientific result. No competition site was accessed. No attempt was made to download from DrivenData or infer remaining submission quota.

### Pass 3 — correctness, consistency, and publication checks

Found and corrected the README sentence that overstated H33 pixel lineage as proof of the cause of a score increase. The revised explanation distinguishes exact raster-edit evidence from an unverified score claim and a merely plausible metric mechanism. Also found that the generated homepage labeled the prior I-SACD/MPC pair as the latest lanes and repeated an earlier session's "data restored" status despite current inputs being absent. Updated the site generator to put this current no-go/input audit immediately below the hero and label older cards as dated history; regenerated the site. Added this review and a machine-readable negative/no-raster run card; no TIFF, holdout score, or submission name was invented.

Verification actually completed in this checkout:

| Check | Result |
|---|---|
| `.venv/bin/python scripts/build_site.py` then `--check` | PASS — regenerated and verified the evidence-generated Pages content; the site continues to say no file is authorized. |
| `.venv/bin/python scripts/check_site.py` | PASS — local links/download integrity/negative-state safety. This is not scientific clearance. |
| Targeted pytest: current-request/review/session, protocol, protocol-site, site, shipped-submission and follow-up review | **72 passed; 3 subtests passed**. |
| Full `.venv/bin/pytest -q` | **1,001 passed, 24 skipped, 58 subtests passed** in 319.45 s. The first run exposed one stale timestamp binding between the refreshed witness measurement and follow-up card; updated the card to the actual measurements and reran successfully. 48 `PendingDeprecationWarning`s originate in pinned Rasterio affine multiplication paths. |
| `scripts/audit_release.py --measure-registry` | PASS as an integrity measurement: **31/31** artifacts format-valid and remeasured against the one pinned witness; final decision remains **DO NOT SUBMIT**. This is not a complete-registry scan or candidate uniqueness clearance. |
| `scripts/protocol_preflight.py` after pinned restore | PASS as a measurement, returns the prescribed **STOP**; witness support rejects every nonempty candidate. |
| `scripts/audit_workspace_inputs.py --require-native` | Expected fail-closed: training TIFF, prepared arrays, and actual shared cache absent. |
| Browser UI / fresh full-registry scan | **Not run in this review**; previous stored receipts are historical, and the current registry is not fully measured. |

## Irregularities and limitations

1. **Literal protocol contradiction:** the unchanged 70% overlap limit cannot be satisfied by any nonempty prediction under the pinned full-support witness. Only the protocol owner can resolve that rule/witness conflict. Do not add a private exemption, reinterpret support, or emit zero/empty predictions to game the gate.
2. **Missing inputs:** the live audit shows `training_features.tif`, all prepared band arrays, and the shared cache absent. Prior manifests and successful historical runs do not prove current files.
3. **Registry completeness:** the single witness is conclusive for rejection under the literal definition but is not a complete current registry. Existing input audit also records incompatible grid/band-count entries; do not silently warp or discard them.
4. **Score evidence:** H33's `0.2778` and the prompt's `0.3195` / `0.4413` are owner claims without a current submission-page receipt in this checkout. No live scoring or score projection is available.
5. **External research and data access:** automated DrivenData access is prohibited by repository instructions. This sandbox can use only approved network hosts; no new official USGS/NREL dataset download or literature verification was attempted in this review. The existing official/manual links are preserved in the repo; source availability is not asserted beyond recorded receipts.
6. **Upload decision:** historical TIFFs may be downloaded only as audit/reproducibility artifacts. No candidate is safe/approved to submit; no upload was performed.

## Next steps

1. Obtain an explicit method paragraph/lane assignment and a protocol-owner disposition of the full-support overlap conflict. Keep all thresholds unchanged until formally resolved.
2. Restore the native training feature TIFF and actual shared cache with exact preprocessing, footprint, visible-fault mask, and hash provenance; do not substitute native-band reprocessing for cache reuse.
3. Resolve incompatible registry records via an explicit owner policy and refresh a complete same-grid registry. No automatic warp/drop.
4. Only after those prerequisites, preregister BMR (or another selected queue item), compare with same-split frozen controls, derive catalogue-based features from visible faults only, withhold whole fault segments plus buffer, mask visible fault pixels exactly, run individual leakage canaries, and report pooled HOLDOUT-DTI with evaluator/version/count/95% CI.
5. Require successful pre-placement surface and final-dot registry checks and a positive paired holdout CI before the separate authorized selector considers a weekly slot. Only an actual submission-page receipt may be called ORGANIZER-CONFIRMED.

Sources for manual review are linked in [`README.md`](../README.md), [`PROMPT.md`](../PROMPT.md), [`registry/followup_hypotheses_20261025.json`](../registry/followup_hypotheses_20261025.json), [`research/H33_ANALYSIS.md`](H33_ANALYSIS.md), and the run card above. No new official-source claim is added beyond those repository records.
