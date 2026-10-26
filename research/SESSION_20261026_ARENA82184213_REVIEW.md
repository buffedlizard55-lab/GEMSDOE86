# Independent repository review — Arena session `82184213` (2026-10-26)

## Decision

**DO NOT SUBMIT any file from this checkout.** No TIFF was generated, no geological experiment was run, and no competition slot was used in this review. This is the correct fail-closed result: the required native feature TIFF and shared feature cache are absent, and the immutable registry witness still triggers the literal overlap stop. Existing TIFFs are available for audit only.

Machine-readable run card: [`docs/evidence/session-82184213-run-card.json`](../docs/evidence/session-82184213-run-card.json).

## Focus-9 result review

The prior executive summary already covers the nine requested sites and links to their pages and evidence: [`docs/executive-summary.html#focus9-summary`](../docs/executive-summary.html#focus9-summary), [`research/SESSION_20261026_H86Q_BFRA_REVIEW.md`](SESSION_20261026_H86Q_BFRA_REVIEW.md), and [`docs/evidence/focus9-forensics-20261026-rev2.json`](../docs/evidence/focus9-forensics-20261026-rev2.json).

The table below reports the best score claim supplied for each site. These are **OWNER-REPORTED**, not `ORGANIZER-CONFIRMED`; the current request's 0.3195 and 0.4413 leaderboard marks remain conflicting/unverified. “Estimate for a new unique file” is **not estimable**: no calibrated score model here can promise leaderboard performance, and a HOLDOUT-DTI is not a live-score projection. Pairwise similarity values are prior `REGISTRY-MEASUREMENT` reports against the H33 dot field (3-pixel forward overlap); values above 0.70 fail the user's stated novelty threshold relative to H33. They are not evidence that those submissions duplicate every other repository file.

| Site | Best named historical file (site link) | Reported result | Similarity to H33 (3-px overlap) | Estimate for a new unique submission | Current submit decision |
|---|---|---:|---:|---|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5` ([site](https://buffedlizard55-lab.github.io/GEMSDOE24/)) | 0.2477 `OWNER-REPORTED` | 0.8848 `REGISTRY-MEASUREMENT` | Not estimable | Do not submit; historical lineage exceeds 0.70 vs H33 |
| GEMSDOE25 | `dotted-h19-5-d2-8` ([site](https://buffedlizard55-lab.github.io/GEMSDOE25/)) | 0.2600 `OWNER-REPORTED` | 0.8817 `REGISTRY-MEASUREMENT` | Not estimable | Do not submit; historical lineage exceeds 0.70 vs H33 |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5` ([site](https://buffedlizard55-lab.github.io/GEMSDOE27/)) | 0.2449 `OWNER-REPORTED` | 0.8672 `REGISTRY-MEASUREMENT` | Not estimable | Do not submit; historical lineage exceeds 0.70 vs H33 |
| GEMSDOE28 | `h36-1-rung30-blind-r1` ([site](https://buffedlizard55-lab.github.io/GEMSDOE28/)) | 0.2710 `OWNER-REPORTED` | 0.9547 `REGISTRY-MEASUREMENT` | Not estimable | Do not submit; historical lineage exceeds 0.70 vs H33 |
| GEMSDOE30 | `d28-poisson300m-offcat-44090` ([site](https://buffedlizard55-lab.github.io/GEMSDOE30/)) | 0.2600 `OWNER-REPORTED` | 0.8817 `REGISTRY-MEASUREMENT` | Not estimable | Do not submit; historical lineage exceeds 0.70 vs H33 |
| GEMSDOE31 | `h27-4-solo-d28` ([site](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)) | 0.2708 `OWNER-REPORTED` | 0.9539 `REGISTRY-MEASUREMENT` | Not estimable | Do not submit; byte/pixel clone of GEMSDOE28 H27-4 per prior forensics |
| GEMSDOE32 | `h33-h33-2-b2` ([site](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)) | **0.2778 `OWNER-REPORTED` — best in Focus-9** | 1.0000 (itself) | Not estimable | Do not resubmit; it is an already-submitted raster and a duplicate |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30` ([site](https://buffedlizard55-lab.github.io/GEMSDOE33/)) | 0.2632 `OWNER-REPORTED` | 0.9264 `REGISTRY-MEASUREMENT` | Not estimable | Do not submit; historical lineage exceeds 0.70 vs H33 |
| GEMSDOE36 | `anderson-geothermal-pinn-38854` ([site](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)) | 0.2750 `OWNER-REPORTED` | 0.9740 `REGISTRY-MEASUREMENT` | Not estimable | Do not submit; historical lineage exceeds 0.70 vs H33 |

Detailed values and interpretation are preserved in the existing executive summary and forensic report rather than copied into a competing hand-maintained table. Historic submission scores are not projections. The H33 source page and its raster are research references only; there is no basis to recommend downloading/resubmitting it.

## H33: defensible interpretation

The corrected discussion is in §2 of [`SESSION_20261026_H86Q_BFRA_REVIEW.md`](SESSION_20261026_H86Q_BFRA_REVIEW.md). In brief: DTI uses a 300 m triangular max-kernel, so redundant predictions can add prediction mass without proportionate recall; a sparse allocation can plausibly improve the tradeoff. H33's 37,654 dots, far-from-catalogue distribution, and higher supplied score than related variants are consistent with that mechanism. They do not prove it caused the score: private labels are unavailable, the compared rasters are not a controlled counterfactual, and the scores are owner-reported. The nine-point off-catalogue correlation is exploratory and confounded, not a score estimator. The private test-set composition is unknown. The correction is logged as `IR-86-H33-CAUSAL-OVERCLAIM-20261026` in [`IRREGULARITIES.md`](../IRREGULARITIES.md).

Accordingly, the answer to “can we beat 0.2778?” is: **possibly in principle, not established by this checkout, and no honest numerical projection is supported.** A new hypothesis must beat matched holdout controls and pass leakage/registry gates before any slot selector considers it. Even a successful holdout is not an organizer score.

## Current workspace capability and hard blockers

Current read-only measurement: `python scripts/audit_workspace_inputs.py` at `2026-10-26T21:28:55Z`.

- `data/bridge/existing_faults.tif` and `data/bridge/sample_submission.tif` match their repository SHA-256 pins. These are owner-mirrored bytes; pins establish integrity, not organizer provenance.
- `training_features.tif` is missing from `data/` and `data/bridge/`.
- All prepared arrays listed by `data/prepared_manifest.json` are absent from ignored `.cache/gems_work/bands/`.
- `registry/feature_receipt.json` does not establish the required shared template cache identity contract. Do not rebuild privately or describe an earlier preparation receipt as current cache availability.
- `data/bridge/registry/dense-witness.tif` was restored by the repository's hash-checked `scripts/restore_protocol_data.py --include-registry` route. The subsequent `REGISTRY-MEASUREMENT` at `2026-10-26T21:39:07.737415Z` validates one immutable witness only (`registry_complete=false`). It confirms full allowed-pixel support, so literal forward overlap is 1.0 for any nonempty inherited candidate. This is a hard stop under the current literal gate, not uniqueness clearance.
- `scripts/audit_release.py --measure-registry` returns `audit_ok=true`, `DO NOT SUBMIT`, 46/46 inherited artifacts locally valid. The whole-registry scan is not complete; the one-witness result is sufficient to reject, never to clear a candidate.

No new TIF is provided as “submission-ready.” The 46 existing TIFs have valid local format/range/integrity receipts but remain audit-only. A format pass cannot clear scientific, uniqueness, complete-registry, or separate weekly-slot approval.

## Three-pass review and commands

1. **Pass 1 — repository/request review:** Read `AGENTS.md`, `PROMPT.md`, `README.md`, the complete Rev-2 request archive, the H86Q/H86R session reports, current executive summary, source/registry records, and release run cards. Confirmed all nine site entries are present; all historical score claims are labeled `OWNER-REPORTED`; no new numerical score estimate is given.
2. **Pass 2 — operational and data review:** Installed `requirements-lock.txt` in ignored `.venv/`. `audit_workspace_inputs.py` confirmed missing training TIFF/cache. Restored only the pinned public protocol witness through the existing repository script. Re-measured the release inventory; confirmed all 46 inherited download artifacts validate locally and remain blocked for upload. Found and corrected the H33 causal/hidden-label overclaims in the prior forensic write-up; logged the correction.
3. **Pass 3 — regressions:** The first full run exposed one stale homepage assertion after improving the hero copy; I retained the test's invariant (“This session wrote no TIFF.”), rebuilt the generated site, passed the targeted release-page test (2 passed), then reran the full `make verify PY=.venv/bin/python`: `build_site.py --check`, `check_site.py`, `audit_downloads.py` (46 research TIFFs), and `pytest -q` all passed (**1,099 passed, 24 skipped, 48 warnings, 58 subtests passed**). Warnings are Rasterio's `PendingDeprecationWarning` about Affine `*` multiplication. `audit_release.py` passed its audit (`audit_ok=true`) with decision `DO NOT SUBMIT` and zero experiments/slots. The initial release audit before witness restoration failed closed because the ignored witness file was absent; it was not bypassed.

Reproduction:

```bash
.venv/bin/python scripts/audit_workspace_inputs.py
.venv/bin/python scripts/restore_protocol_data.py --include-registry
.venv/bin/python scripts/audit_release.py --measure-registry
make verify PY=.venv/bin/python
```

## Sources and limitations

Manual review links already present in [`docs/sources.html`](../docs/sources.html) and [`research/SESSION_20261026_H86Q_BFRA_REVIEW.md`](SESSION_20261026_H86Q_BFRA_REVIEW.md) include the official DrivenData competition/rules pages, NLR-hosted GEMS PDF, DOE GDR submission 1391, USGS GeoDAWN release, and EPSG:32611. This session did not automate access to DrivenData; no leaderboard receipt or weekly quota was retrieved. Research hypotheses about geothermal fluids or faults are not proof of geothermal vents, reservoir permeability, temperature, or commercial value.

**Next work:** obtain the missing competition feature TIFF through an allowed, authenticated route and verify it against the recorded pin; establish the actual shared-template feature-cache provenance/identity; resolve the literal witness conflict only through the shared protocol/governance process (no private threshold exception); then preregister at most three experiments in one explicitly assigned lane. Re-run independent holdouts and all-feature leakage canaries before touching a selector. Never spend a slot on an unvalidated idea, never label a projection a score, and record an organizer receipt before using `ORGANIZER-CONFIRMED`.
