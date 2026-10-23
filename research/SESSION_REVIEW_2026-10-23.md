# Repository review and site/ledger reconciliation — 2026-10-23

## Decision

**DO NOT SUBMIT. No new candidate or TIFF was created in this review.** The latest previously evaluated model lane is H86B-GFCO. Its local GeoTIFF format checks pass, but the preregistered primary paired holdout interval includes zero, its literal registry uniqueness gate fails, and no slot is authorized. The existing TIFF is exposed by the site only for audit/reproducibility.

- Submission name: `gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b`
- Note (91/140 characters): `H86B-GFCO LOQO geotherm-diseq+mag-contact-offset+LiDAR x tip/relay, 44090 dots d>2px, zeros`
- TIFF: [`../docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.tif`](../docs/downloads/gems86-h86b-gfco-44090dots-20261022T233826Z-8fb20e6b-zeros.tif)
- SHA-256: `897ebf7b790efb9b5668934f5929ae766d81d9ec2a4bee3faa7ef2ebaedc1116`
- Local validator: `PASS`, 15/15 checks; finite `[0,1]`, no NaN in footprint, single float32 band, CRS/shape/transform match. This is not organizer acceptance.
- Review output: zero model experiments, zero new TIFs, zero weekly slots used; no organizer receipt or confirmed score.

## Three-pass review log

### Pass 1 — repository, prompt, and evidence inventory

Read the archived owner prompt, `PROMPT.md`, repository instructions, canonical H86B/RMRB run cards, protocol preflight, the H86B score JSON, download inventory, source and site pages, and historical-score ledger. Restored only the already pinned small protocol inputs and witness via the repository restorer; checked their hashes. No source data were promoted to organizer-authenticated status.

Findings: the current generated landing page and README were stale/conflicting; some pages described RMRB or the earlier GMC lane as latest. A number of historical leaderboard values were repeated without a receipt. The static-site validator did not generate any pages. The currently required assigned method paragraph is absent from the prompt supplied for this review, and the template feature cache is absent. H86B-GFCO's three-experiment budget had already been used, so no new experiment was admissible.

### Pass 2 — scientific evidence and hypothesis ranking

Re-read the H86B experiment evidence and audit results. All candidate values below are **HOLDOUT-DTI**, evaluator `gems57-pooled-hide-v2`, with the count of withheld positives and 95% CI shown. They are not organizer leaderboard scores.

| Split | Withheld positives | H86B-GFCO HOLDOUT-DTI (95% CI) | Paired delta vs d2.8 (95% CI) | Paired delta vs H33-2-B2 (95% CI) |
|---|---:|---:|---:|---:|
| Buffered whole components | 11,321 | 0.107759 `[0.090790, 0.125365]` | +0.015871 `[-0.000708, 0.034298]` | +0.011673 `[-0.005198, 0.030252]` |
| Segment-all | 22,641 | 0.139607 `[0.128563, 0.151298]` | +0.038537 `[0.026890, 0.052410]` | +0.048646 `[0.037369, 0.062149]` |
| Segment-detached | 22,619 | 0.152085 `[0.137847, 0.166235]` | +0.048620 `[0.034296, 0.062730]` | +0.057268 `[0.043843, 0.071904]` |

The primary whole-component paired intervals cross zero against both controls. The positive segment-split point estimates do not replace the primary preregistered test and do not authorize promotion. The feature-alone leakage canary checked 42 features; maximum discriminative AUC was 0.848548 against a 0.90 stop threshold. This is a leakage diagnostic, not DTI.

Registry comparison is a **REGISTRY-MEASUREMENT** over 28 hash-verified rasters in the run card's incomplete, local/cross-repository scope: pre-placement worst absolute Spearman 0.136561; final-dot worst discriminating absolute Spearman 0.052983; 3-pixel forward overlap 0.765638 against `gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif`. The literal gate also fires against the stride-5 lattice (0.998753) and `gems10-h28` (0.7170). The stated modern/comparable subset has a maximum overlap of 0.634203, but that subset does not override literal failures or establish global novelty.

The separate hash-pinned dense witness is positive on all 5,106,385 allowed cells (zero uncovered). Under the repository's inherited literal support rule it blocks any non-empty candidate. It proves a protocol overlap blocker, not identical geological arrangement. Only one witness raster was measured; the full registry is incomplete. No threshold, comparison mode, or exemption was changed.

Ranked qualitative hypotheses (with data bands, physical signature, named non-fault mimic, difference from prior methods, repository-level novelty, cost, source and availability) are stored in [`next_hypotheses.json`](next_hypotheses.json) and rendered on the [hypotheses page](../docs/hypotheses.html). All four concepts were already proposed in earlier repository reviews (`research/H86B_GFCO_REVIEW.md` and/or `research/REVIEW.md`); they are re-ranked prior hypotheses, not novel methods. The shortlist is not assigned or authorized for experiments:

1. **H86E-MTDA — depth-migrating MT edge vector:** highest qualitative blind-fault potential among this shortlist; requires the missing cached/official competition feature stack; high implementation cost.
2. **H86D-PFCO — paired potential-field ridge dislocation with gravity-step corroboration:** medium-high qualitative potential; competition layers required; high graph/offset-validation cost.
3. **H86C-TDPL — relief-normalized LiDAR scarplet chains with shoreline/drainage rejection:** moderate qualitative potential; owner-manifest-described USGS 3DEP-derived input is not present locally or independently provenance-checked; moderate method cost.
4. **H86F-RLSL — uncertainty-aware 3-D microseismic plane fit and up-dip projection:** potentially high but highly uncertain potential; official ComCat access is outside this sandbox's outbound allowlist; high data and method cost.

These are a qualitative shortlist, not performed experiments, expected numerical scores, or a claim of global novelty. “Top candidate” means rank 1 by stated qualitative criteria only. No candidate was validated or emitted.

### Pass 3 — implementation, release-safety, and independent audit

Implemented a fail-closed site builder that reads the canonical run cards, holdout JSON, protocol-preflight JSON, download inventory, hypothesis record, and prior-score CSV. It regenerates the landing page, evidence page, submission guide, hypothesis page, sources/score-ledger page, irregularities page, and machine-readable `docs/data/summary.json`; then calls the existing link/download-safety validator. It does not generate a model, raster, prediction score, or submission authorization.

The prior-site CSV was extended only with values explicitly supplied in the owner prompt. `0.0943` for GEMSDOE80 and `0.0041` for GEMSDOE81 are marked **OWNER-REPORTED (unverified)**; names without scores remain blank; absent entries are labelled “not listed in the prompt,” not treated as proof of no submission. No user-provided value is labelled ORGANIZER-CONFIRMED.

Updated `AGENTS.md` and the current top of `README.md` to point to canonical evidence and mark this negative state. Historical lower README sections remain archival material; the new current-status header warns that only receipt-backed values are organizer-confirmed. A generated page is not a scientific release gate.

## Data and source provenance

- The competition task, dataset and official submission rules: [DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login may be required).
- Organizer baseline: [official reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution).
- GeoDAWN source linked in the repository's data manifest: [USGS GeoDAWN release, DOI 10.5066/P93LGLVQ](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- LiDAR provenance claim: [USGS 3DEP](https://www.usgs.gov/3d-elevation-program). The manifest describes an owner-derived product; coverage and tile provenance were not independently checked in this review.
- Proposed seismic source: [USGS ComCat FDSN](https://earthquake.usgs.gov/fdsnws/event/1/); not downloaded, and the host is outside this sandbox's permitted outbound allowlist.
- Additional thermal/structural source link: [DOE Geothermal Data Repository / INGENIOUS](https://gdr.openei.org/submissions/1391). The owner-mirrored catalogues are not a substitute for a receipt from the original source.

No external DrivenData, USGS, or GDR page was fetched during this review. Outbound internet is restricted to GitHub, npm, and PyPI hosts. Restored owner-mirror bytes match repository hashes, which confirms mirror integrity only—not organizer/agency authentication.

## Irregularities and limitations

1. No assigned method paragraph was supplied for this session; existing repository records conflict about the active lane. No lane was silently selected.
2. The required shared feature cache is missing. No private stack was reconstructed or substituted.
3. H86B-GFCO already used its recorded three-experiment allowance. The current review ran no model experiment and generated no candidate.
4. `protocol_preflight.py` applies a literal positive-support blocker; H86B's two-phase audit separately reports a modern-comparable view. These policies are not silently reconciled, and no shared gate was changed.
5. The measured registry is incomplete. A result against locally present and pinned witness rasters cannot establish novelty across all entries.
6. The historical score ledger has no organizer receipts. Values quoted by the owner are preserved as unverified statements only.
7. Some older README pages and historical research summaries describe previous lanes as current. This top-level status, canonical cards, and generated Pages feed supersede those old claims.
8. The request to create and merge a PR was not completed during the review. No PR or merge is claimed in this record.

## Recommended next work (gated)

1. Resolve the absent assigned-method paragraph from the archived owner prompt and select exactly one lane; until then, do not start an experiment.
2. Recover the template's shared feature cache from its explicitly pinned source without private forking; verify hashes and official/source provenance. Do not substitute owner mirrors as authenticated data.
3. Reconcile the literal-support certificate with the stated protocol without changing any threshold; only the protocol owner may decide whether the positive-support rule applies to continuous priors in the same way as dot fields.
4. Check complete registry coverage and prior surface/dot overlap before any placement. Stop at the existing correlation/overlap thresholds.
5. If all preflight gates permit an experiment, use the shared whole-component-buffered evaluator and feature-alone leakage canaries. Holdout and spatial paired 95% CI are required before a separate selector considers any slot.
6. Keep the negative cards and no-submit site state until a new, canonical run card supports promotion and an independent selector verifies current quota.

## Machine-readable run card

The single canonical JSON run card for this review is [`docs/evidence/session-review-run-card.json`](../docs/evidence/session-review-run-card.json). It carries the inherited hypothesis/mechanism and named non-fault mimic; labelled HOLDOUT-DTI, evaluator, counts and paired 95% CIs; scoped registry correlation/overlap; raster SHA-256; local validator output; submission name/note; and the final `negative` verdict. No new TIFF or submission slot was authorized.
