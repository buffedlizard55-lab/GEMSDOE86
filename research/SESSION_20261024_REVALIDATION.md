# Follow-up review and three-pass verification — 2026-10-24

## Decision

**NEGATIVE — DO NOT SUBMIT. The requested new, unique competition TIFF was not generated.**
This is an explicit stop, not a claim that the geological ideas have failed or that any local
format check proves organizer acceptance. No submission slot was used.

The supplied request does not contain the promised single method paragraph, so it does not assign a
lane. Independently, the unchanged local protocol has a hash-pinned historical registry witness
whose positive support covers every allowed off-catalogue cell. Under the repository's literal
forward-overlap definition, every nonempty candidate dot set therefore overlaps that witness by
`1.0`, exceeding the `0.70` stop. The shared preflight prevents feature construction or placement;
we did not add an exemption, change a threshold, use an all-zero placeholder, copy a previous TIFF,
or bypass the preflight. The full registry was not measured, so this is a sufficient negative
counterexample, **not** a uniqueness clearance.

Current machine decision: [`docs/evidence/latest-review-run-card.json`](../docs/evidence/latest-review-run-card.json).
Current witness proof: [`docs/evidence/protocol-preflight.json`](../docs/evidence/protocol-preflight.json).
Fresh all-artifact audit: [`docs/evidence/all-artifacts-registry.json`](../docs/evidence/all-artifacts-registry.json)
and [`docs/evidence/release-readiness.json`](../docs/evidence/release-readiness.json).

## Pass 1 — inspect the task and evidence before work

- Read `AGENTS.md`, `PROMPT.md`, the README and the full archived 2026-10-24 request. The
  archive itself notes there is no actual method-lane paragraph. The requested H86E-SPBT idea is
  only a queued hypothesis; treating it as an assigned lane would invent authorization.
- Reviewed the prior scientific analysis in
  [`SESSION_20261024_REVIEW.md`](SESSION_20261024_REVIEW.md), the five-item register in
  [`registry/h86c_hypotheses.json`](../registry/h86c_hypotheses.json), and the existing site,
  download, validator, audit and preflight code. The site already puts **DO NOT SUBMIT** above the
  download links and distinguishes audit downloads from a submission-approved file.
- Confirmed the actual shared cached feature stack is absent. The tracked sample grid and fault
  raster are proof inputs, not the cached 19-band feature stack. We did not restore a raw feature
  raster and mislabel it as the required cache.
- The user's request gives inconsistent current-leaderboard figures and the owner-supplied
  `GEMSDOE32` result. No automated DrivenData fetch was made. Such values remain owner/user claims,
  not `ORGANIZER-CONFIRMED` receipts. The repository's source audit contains no submission-page
  receipt.

### Why `GEMSDOE32`'s `h33-h33-2-b2` result is plausible, but not proven causal

The detailed pixel-level explanation and caveats are in
[`SESSION_20261024_REVIEW.md`](SESSION_20261024_REVIEW.md) and
[`H33_INTERPRETATION_REVIEW.md`](H33_INTERPRETATION_REVIEW.md). In brief, the archived raster is
pixel-identical to an earlier dotted parent after removing the narrow mapped-fault collar (2,545
dots within 2 px); this is consistent with reducing false-positive cost near known faults under
the asymmetric distance-weighted Tversky metric while retaining sparse off-catalogue predictions.
That is a plausible mechanism, not a demonstrated causal effect or a geothermal-vent discovery.
The owner artifact says `UNSCORED` and includes a projected leaderboard field; a score-page receipt
is absent. Therefore it is not valid to claim the supplied leaderboard value is organizer-confirmed
or to promise that a new candidate can exceed it. Historical holdouts use different folds and are
not a substitute for a matched current holdout.

## Ranked hypotheses retained from the prior review

The ordering below is the register's **qualitative information-gain per cost** assessment, not a
numeric DTI projection. Novelty is scoped to this checkout and the named reviewed lanes, not every
parallel repository. All remain `NOT_RUN_PROTOCOL_STOP` or `NOT_RUN_MISSING_DATA_AND_PROTOCOL_STOP`.

| Rank / candidate | Layers and physical signature | Why it could find an unmapped fault; distinction from this repo | Mimic, cost, and data status |
|---|---|---|---|
| 1. **H86E-SPBT — signed paired-throw basement/gravity concordance** | Competition depth-to-basement Band 15, isostatic gravity Band 13, detrital elevation/slope Bands 12/19 and magnetic gradient Band 3. Test opposite-polarity, strike-persistent flank steps and a polarity-scrambled control. | Targets blind intrabasin growth faults under alluvial cover, where basement and gravity offsets may persist after surface scarps are buried. Existing reviewed lanes use unsigned gradients, curvature or tilt magnitudes, not concordant signed flank polarity. | Paleovalley/caldera-moat margins or basement-inversion error; low–medium cost. No new external layer is required, but the actual feature cache and protocol clearance are missing. **Top candidate remains unvalidated.** |
| 2. **H86E-MMT — magnetic marker-horizon translation** | RTP Band 2, tilt/curvature Band 6, magnetic high-gradient Band 3, with radiometric context. Measure nonzero phase translation of transverse magnetic markers across opposing flanks and adjacent strike windows. | Targets buried oblique transfer faults that offset magnetic markers without prominent range-front scarps. Existing cross-gradient and upward-continuation work does not estimate two-sided flank translation. | Intrusive contacts, flow-lobe edges, remanence changes and survey seams; medium–high cost. Competition bands are sufficient in principle; no external data needed, but protocol/cache blockers remain. |
| 3. **H86E-HMDC — magnetic destruction trough plus vent/sinter alignment** | RTP Band 2, vertical gradient Band 9, surface conductivity Band 17, dilation/shear Bands 8/7, plus GDR 1391 sinter/tufa, temperature-probe and vent/wellspring mirrors. Target negative magnetic curvature troughs with positive shoulders and strike-aligned hydrothermal evidence. | A concealed hydrothermal alteration corridor could follow blind splays not in the surface-fault catalogue. H86D used positive magnetic ridges and isotropic halos, not negative troughs with co-linear vent corridors. | Reversed-polarity lava, low-susceptibility tuff and survey seams; medium cost. GDR 1391 is an official free source, but source metadata or a mirrored manifest alone does not prove local bytes are present; protocol/cache blockers remain. |
| 4. **H86E-MTCS — multi-depth MT conductance × heat flow × dilation** | USGS Great Basin 3-D MT conductance slices (DOI `10.5066/P9TWT2LU`), conductive heat flow (DOI `10.5066/P9BZPVUC`), and competition Bands 17/8/7/6. Compare deep and shallow conductance and align it to heat-flow/dilation corridors. | Could separate deep fluid conduits from shallow playa brines and map blind structures without a Quaternary scarp. No reviewed lane ingests the depth-resolved external MT grids. | Graphitic/sulfidic strata; medium–high cost. Official DOI records are identified, but binary rasters are not present and ScienceBase is outside this sandbox's outbound allowlist. **Not viable to test until bytes are mirrored and hash-pinned.** |
| 5. **H86E-WCS — cross-divide 1-m LiDAR micro-scarp persistence** | Native USGS 3DEP 1-m DEM tiles indexed by the competition's `1m_DEM_links.csv`, checked against Bands 12/19. Measure signed 5–25 m profile-curvature steps that persist across independent drainage divides. | Could preserve subtle low-slip piedmont scarps smoothed in 100-m summaries, while cross-divide persistence suppresses local channels. Existing work uses precomputed coarser LiDAR derivatives, not native-resolution polarity persistence. | Shoreline benches, terraces and roads; high cost. The login-walled tile index/native tiles are absent and TNM tile hosts are outside the sandbox allowlist. **Not viable to test until licensed inputs are staged and pinned.** |

No hypothesis was implemented in this follow-up: the mandatory preflight stops before construction. The
full register records the official-source links, layer details, mechanisms, mimics and data-readiness
qualifiers.

## Pass 2 — independently recheck the hard stop and current feed

- Restored the integrity-pinned bridge inputs and historical witness using
  `scripts/restore_protocol_data.py --include-registry`; this used GitHub mirror bytes and is not
  organizer-authenticated data access.
- Re-ran `scripts/protocol_preflight.py` at `2026-10-24T18:22:55+00:00`. Its `REGISTRY-MEASUREMENT` reports witness SHA-256
  `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`, `5,106,385` allowed
  cells, zero uncovered allowed cells, one raster measured from a snapshot of `655` registry
  entries, and `registry_complete: false`. Thus the literal forward overlap bound is `1.0` for
  every nonempty allowed dot set, above `0.70`. No candidate surface or dots were measured.
- Re-ran `scripts/audit_release.py --measure-registry`: all `10/10` inherited published TIFFs
  passed the local on-disk format/integrity checks, while all remain explicitly negative and
  unauthorized under the registry stop. A format pass is not submission approval.
- Refreshed the repository-metadata feed at `2026-10-24T18:26:23+00:00`: `92/92` named GitHub
  project trees were snapshotted; the refresh obtained `0` organizer receipts. This is current
  GitHub metadata, not a live DrivenData score/quota feed.
- Rechecked two immutable GitHub source documents at `2026-10-24T18:26:24+00:00` with
  `scripts/review_sources.py`. The official
  reference README's retrieved Git blob matches the archived bytes and explicitly supports a
  CPU-only path. The GEMSDOE32 owner audit also matches its pinned archived bytes, but is classified
  `OWNER-ARTIFACT-NOT-ORGANIZER-RECEIPT`; it contains `UNSCORED` wording and a projected-score field.
  This confirms source identity and claim classification only, not the live portal or leaderboard.

## Pass 3 — review the implementation and verify outputs

- Full tests: **495 passed, 24 skipped, 4 rasterio pending-deprecation warnings, 41 subtests**.
  The skipped tests require gitignored historical release rasters or restored experiment inputs;
  they are not successful experiments and do not validate the missing feature cache.
- `scripts/build_site.py`, `scripts/build_site.py --check`, `scripts/check_site.py`,
  `scripts/audit_downloads.py`, `scripts/validate_download.py`, and
  `scripts/build_ledger.py --check` all passed. The generated homepage and submission guide continue
  to state **DO NOT SUBMIT**; all prior TIFFs are linked for audit only.
- Confirmed `experiments_run = 0`, `submission_slots_used = 0`, no new raster SHA, no holdout result
  from this follow-up, and no pre-placement surface/final dots to compare. The current run card
  explicitly records `HOLDOUT-DTI / gems57-pooled-hide-v2 / NOT_RUN_PROTOCOL_STOP` with null
  withheld-positive count, value and CI; these are null because no experiment ran.

## Irregularities and work still needed

1. The promised lane/method paragraph is absent. Do not infer one from a ranked proposal.
2. The overlap rule is unsatisfiable for nonempty allowed predictions under the current literal
   support definition, and the accessible registry is incomplete. Resolve this **upstream** with
   an explicitly approved, representation-aware comparison protocol; do not privately change the
   shared checker or thresholds. The repository also documents a separate saturated discrete
   lattice witness in the prior review.
3. The actual shared cached feature stack is absent. Restore its exact pinned bytes and provenance
   after the protocol permits a run; a raw mirrored TIFF is not a cache.
4. The current leaderboard claims conflict in the owner request and none has an organizer receipt.
   Automated DrivenData scraping was deliberately not used. The official submission-page receipt,
   account eligibility and remaining weekly quota are unavailable here.
5. The five hypotheses are proposals, not validated discoveries. After the blockers are resolved,
   run one authorized lane with visible-fault-only features, whole-segment buffered holdout, every
   feature's AUC canary, the pinned shared evaluator/writer and a paired spatial CI before the
   separate selector considers any slot.
6. “Fault prediction” is not direct confirmation of geothermal vents, heat supply, permeability or
   commercial viability.

## Source links for review

- Official competition description and metric: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
- Official competition about page: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/>
- Official rules PDF: <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
- Official benchmark repository, pinned README: <https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md>
- USGS GeoDAWN data release: <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>
- DOE GDR / INGENIOUS regional dataset: <https://gdr.openei.org/submissions/1391>
- USGS Great Basin MT and heat-flow DOIs: <https://doi.org/10.5066/P9TWT2LU> · <https://doi.org/10.5066/P9BZPVUC>
- GEMSDOE32 owner project page (not an organizer receipt): <https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html>
- Immutable-source recheck output: [`docs/evidence/review-source-checks.json`](../docs/evidence/review-source-checks.json)
- Detailed H33 analysis and critique: [`SESSION_20261024_REVIEW.md`](SESSION_20261024_REVIEW.md)
