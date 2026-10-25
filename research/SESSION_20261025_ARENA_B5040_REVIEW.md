# Repository review — Arena branch `arena/b5040e9c-gemsdoe86`

**Date:** 2026-10-25 UTC
**Scope:** three-pass repository / release-page review; no model fitting, raster placement, new TIFF, organizer login, or weekly-slot selection.
**Outcome:** negative for a *new* candidate this review. H86G-EDTI retains a historical `PROMOTE` result under PA-86-01, but current upload authorization is **DO NOT SUBMIT** (`safe_to_submit=false`, `approved_for_weekly_slot=false`) because the literal registry gate remains blocking. H86G-EDTI was not re-run here.

## Pass 1 — inspect current evidence and implementation

Read `PROMPT.md`, `README.md`, `AGENTS.md`, the complete archived request, the H33 forensic report, the current review receipts, the static-site generator, and the shared format/registry audit entrypoints.

### H33: what the evidence supports

`research/H33_ANALYSIS.md` and `docs/evidence/h86f-h33-forensics.json` bind the following **PIXEL-MEASUREMENT** to the checked-in raster bytes: the H33 prediction is an exact subset of the GEMSDOE28 D2.8 parent; it removes 2,545 parent dots in the 1.414–2.0 pixel mapped-fault distance band and adds none. The changed raster is therefore a thinning/collar-pruning variant, not a newly measured geological layer. Its parent uses the H19-5 multiline lineament surface and approximately 2.8-pixel spacing.

The score claims `0.2708` for the parent and `0.2778` for H33 are **OWNER-REPORTED**, not ORGANIZER-CONFIRMED: no submission-page receipt is present. The plausible mechanism is coverage-efficient emission under the asymmetric DTI: with alpha 0.2 and beta 0.8 and a 300 m triangular kernel, redundant predictions can add false-positive mass without adding maximal kernel credit, and dots close to already-mapped faults can have low marginal hidden-truth coverage. Pixel lineage alone does **not** establish that these factors caused the reported live-score difference. The source review correctly says that a score above 0.2778 is not established by the local evidence.

The other prompt leaderboard values, including `0.3195` and `0.4413`, are also **OWNER-REPORTED**, not portal receipts. No leaderboard score is inferred from a holdout or proxy.

### Existing download decision

The repository contains one previously generated H86G-EDTI artifact with a historical per-lane `PROMOTE` verdict under PA-86-01. It does not have current upload authorization: the latest mainline safety decision requires `DO NOT SUBMIT`, and its run card keeps `safe_to_submit=false` and `approved_for_weekly_slot=false`. A later read-only review generated no replacement and did not erase that historical scientific verdict; it correctly leaves the current upload decision blocked. This review initially found confusing cross-page wording, then latest mainline updates added an explicit no-upload banner and a negative H86I-HVFD artifact. We integrated those mainline safety updates instead of reintroducing an upload button. The remaining work here clarifies that format-only validation is not authorization.

## Pass 2 — correct release wording and verify behavior

Updated the static-site generator and its tests so that:

- The no-new-candidate review is explicitly scoped: it generated no replacement and did not revoke H86G-EDTI.
- The current decision page labels H86G as **historical PROMOTE, DO NOT SUBMIT** and displays its recorded PA-86-01 measurement separately from the literal continuous-support witness reading. Its historical like-for-like result is not presented as current literal-rule clearance.
- The format-only audit identifies itself as a format check, not slot authorization, while explicitly pointing to the current global **DO NOT SUBMIT** decision. Its run card remains negative with `safe_to_submit=false` and zero slots.
- The executive summary distinguishes local format validation, historical H86G `PROMOTE`, the current literal-rule block, slot authorization, and organizer confirmation. Downloads remain available for audit/reproducibility only.
- README makes clear that the later review's negative result applies to a new candidate in that review and does not replace the previous H86G lane result.

No TIFF, ZIP, scientific run card, score, threshold, shared-template file, or submission receipt was changed by this branch's review fixes. During PR preparation, main advanced and added the independent H86I-HVFD negative result and updated the no-upload policy; those upstream bytes and evidence were retained. A regression test now checks that H86G's historical verdict cannot be mistaken for current upload authorization.

## Pass 3 — re-check protocol and candidate hypotheses

### Why no new TIFF was built

The complete current request contains the parallel-run protocol but **does not assign a single method paragraph/lane**. The existing shared preflight also measures a pinned registry witness with support across every allowed pixel; under the unchanged literal overlap rule, every nonempty allowed candidate is blocked. The permitted like-for-like PA-86-01 path is not permission to invent a lane: it requires a specified method and both surface and final-dot comparison against the required registry scope. The actual shared template cached feature stack is also absent; the restored native 19-band inputs are explicitly not that cache. Two indexed historical registry entries have incompatible grid/band metadata and remain unresolved. Accordingly, the new hypothesis proposals below remain **NOT RUN**. No new TIFF, holdout score, leakage AUC, candidate correlation, candidate overlap, candidate SHA, or submission name is claimed.

The existing H86G file is not copied or renamed as a new result. Its prior run card reports **HOLDOUT-DTI** (`gems57-pooled-hide-v2`, 11,321 withheld positives): `0.0631`, 95% CI `[0.0468, 0.0806]`. That is its historical hide-and-recover result, not a leaderboard score. H86G's documented promotion is a historical scientific verdict only; current upload authorization remains DO NOT SUBMIT. The project has no organizer receipt or current weekly-quota observation. Consult the linked card for the evidence scope and its caveats.

### Ranked hypotheses already in the repo (not new claims of literature novelty)

These are qualitative information-gain/cost rankings in `registry/h86g_hypotheses.json`, checked against `src/gems86/io.py:BANDS`. All four are `NOT_RUN_PROTOCOL_STOP`; no external layer is required by their stated designs, but the common cache/lane blockers still apply.

| Rank | Hypothesis / layers | Target signature and why it may reveal unmapped faults | Named non-fault mimic | Qualitative cost |
|---:|---|---|---|---|
| 1 | **H86G-CSPA**, band 2 `rtp` + band 13 `iso_grav_anom` | Windowed gravity–magnetic cross-spectrum, coherence and scale-dependent admittance; seek localized relationship breaks, not another amplitude edge. Buried juxtaposition may lack a surface scarp. Unlike implemented local gravity-curvature dipoles (GZZD) and signed gradient alignment (PCC), this is cross-spectral. | Unfaulted lithologic juxtaposition, source-depth variation, remanent volcanic magnetization, survey-resolution mismatch. | Medium; highest qualitative information potential, high mimic risk. |
| 2 | **H86G-MPC**, bands 2 and 13 | Log-Gabor/Riesz monogenic phase congruency and axial orientation; test whether phase alignment preserves weak markers hidden by amplitude ranking. No monogenic phase implementation was found in this checkout. | Lava-flow margins, dikes, interpolation ringing, survey seams. | Medium; multi-scale FFT and orientation controls. |
| 3 | **H86G-PSC**, bands 2, 13 and 15 `depth_to_base_surf` | Persistence-ranked saddle-to-extremum connectors in filtered potential fields; a buried connection may be missed by peak/ridge-only methods. Band 15 is gravity-derived and must not be treated as independent corroboration. | Intrusive contacts, erosional basement relief, superposed unfaulted sources. | Medium-high; topology extraction and randomization controls. |
| 4 | **H86G-CNT**, bands 17 `cond_surf`, 7 `geod_shearrate`, 8 `geod_dilaterate` | Persistent conductive necks conditioned on positive dilatation, tested against broad-conductivity and strain-only controls; could indicate a buried pathway without a visible scarp. The single conductivity band does not provide MT depth migration. | Saline playa sediment, clay-rich paleochannels, interpolation bottlenecks. | Medium; weakest specificity. |

The source register identifies the official native raster description at the pinned [DrivenData reference-solution README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md). Competition-data authentication remains unavailable in this workspace; mirrored bytes are hash-pinned but not organizer-authenticated. The repository's [source and obtainability ledger](../docs/sources.html) distinguishes metadata access from downloaded data. No external product is proposed as viable without byte-level verification.

## Verification and residual risks

Executed after the wording corrections:

- `.venv/bin/python -m pytest -q` after integrating mainline: **842 passed, 24 skipped, 45 subtests passed**. Rasterio emitted 42 pending-deprecation warnings from its affine multiplication implementation.
- `.venv/bin/python -m unittest discover -s tests -q`: **113 tests passed, 1 skipped**.
- After integrating the mainline H86I-HVFD negative result, `scripts/build_site.py --check`, `scripts/check_site.py`, and `scripts/audit_downloads.py`: passed. The independent format audit re-read **21** registered TIFFs and their receipts/ZIPs; it did not make a selector decision.
- `scripts/validate_download.py`: passed its local format checks for the archived RMRB control, but reported its uniqueness check false and holdout below its same-instrument incumbent; it remains explicitly negative and is **not** the current promoted artifact.
- `git diff --check`: passed.

Residuals: no new submission can be validated without an explicit lane and resolution of the binding preflight / full-registry requirements; the actual template cache remains absent; the incompatible registry entries need policy/input correction; no authenticated submission page or receipt is available; and a local format pass cannot establish portal acceptance. The provided DrivenData data tab and leaderboards were not scraped, per repository policy.

## Run card

The machine-readable negative run card is [`SESSION_20261025_ARENA_B5040_RUN_CARD.json`](SESSION_20261025_ARENA_B5040_RUN_CARD.json). It records null for every unmeasured candidate property and links H86G-EDTI separately as an already-promoted historical artifact, with the current `DO NOT SUBMIT` decision recorded explicitly; it is not a result of this review.

### Official / project links for manual review

- [DOE GEMS competition problem statement](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) (authenticated access may be required).
- [Competition rules and submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/).
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
- [USGS GeoDAWN data description](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- [INGENIOUS/GDR resource listing](https://gdr.openei.org/submissions/1391).
- [Submission-format and gate procedure in this repo](../docs/executive-summary.html).
- [H33 byte-level analysis](H33_ANALYSIS.md) and [H86G-EDTI scientific/run-card evidence](H86G_EDTI_REVIEW.md).
