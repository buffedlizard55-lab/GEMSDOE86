# Repository review — session 085c2b7a (2026-10-25 UTC)

## Executive decision

**DO NOT SUBMIT yet. Download is available for review, not upload authorization.**
This session generated **no new TIFF**, ran **no model experiments**, and used **no competition slots**. The urgent unique-submission requirement is **not fulfilled by this review**. An old TIFF must not be renamed or copied to disguise that fact.

The existing H86G-EDTI artifact retains its historical scientific `promote` verdict under PA-86 like-for-like diagnostics. Its own card says `safe_to_submit=false`, `approved_for_weekly_slot=false`; the overall release audit retains the literal registry stop. The previous website nevertheless said “IS THIS FILE OK TO SUBMIT? YES” and “submit this file.” Those instructions contradicted the permission flags. This review fixes the generated instructions and regression-tests both public guides and their machine-readable summary. Historical scientific cards, TIFF bytes, tool pins and thresholds are unchanged.

Direct existing artifact, **selector review only**:
[TIFF](../docs/downloads/gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.tif) / [one-TIFF ZIP](../docs/downloads/gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.zip).
Name and short note remain available in the [executive summary](../docs/executive-summary.html) and [historical card](../docs/evidence/h86g-edti-run-card.json).

## Pass 1 — inspection, evidence and implementation

Read the standing instructions and current request archive; the README already embeds the request and links its full archive. There is no single-method assignment in the supplied request. No authority to change lanes or waive the literal stop is inferred from urgency.

- Restored and verified the two pinned grid/mask inputs and saturation witness using `restore_protocol_data.py --include-registry`. These are owner mirrors, **not organizer-authenticated source data**.
- Ran the existing shared-tool release audit with `--measure-registry`. All **20/20 inherited artifacts** passed local format/identity checks. This is **FORMAT-VALIDATION**, not HOLDOUT-DTI and not a submission clearance.
- Re-ran `audit_concurrent_artifacts.py`, including H33 ancestry. Its scoped comparisons cannot establish fleet-wide uniqueness.
- Corrected the generator, not just generated HTML. Added summary fields exposing the promoted-for-review identity separately from upload authorization.
- Preserved the full request archive, scientific promotion result, historical metrics and shared evaluator/writer bytes.

### Why H33 led its lineage — evidence, not a private-truth reconstruction

The current [pixel forensic receipt](../docs/evidence/concurrent-artifact-review-20261025.json) confirms:
H33 is exactly its parent minus the two-pixel catalogue collar, with **2,545 dots removed and none added**. Parent support is **40,199** cells; H33 support is **37,654**; removed distances are √2 and 2 pixels. These are **RASTER-MEASUREMENTS**.

The claimed change **0.2708 → 0.2778** is **OWNER-REPORTED**, not ORGANIZER-CONFIRMED. Sparse emission and removal of redundant/low-credit collar predictions are a plausible mechanism: max-kernel credit does not add repeated coverage, whereas extra prediction mass can incur false-positive cost. This does not prove that the removed cells were false positives on private truth. It is incorrect to assert that a new geological observation caused that claimed improvement.

**Can we exceed 0.2778? Unknown.** Neither the prompt's 0.3195 nor 0.4413 is a verified current leaderboard value here. No organizer receipt was obtained, and no new matched-control experiment was run. H86G's SGMC proxy is explicitly not a competition score; its post-selection descriptive CI cannot establish a pre-registered unbiased leaderboard gain. A historical catalogue-hide floor is not proof of beating the strongest same-design control.

## Ranked untried hypothesis queue — before any implementation

These are **existing unimplemented proposals carried forward**, not claimed as newly invented in this session. Their detailed physical signatures, mimics and falsifiers are in the [four-hypothesis register](../registry/h86g_hypotheses.json). They are not validated methods. Ranking is qualitative expected incremental HOLDOUT-DTI information per cost, **not a numeric score forecast**. Novelty is scoped to executable code in this repository, not all parallel projects or published science.

| Priority | Layers and targeted signature | Why potentially catalogue-missing; difference from implemented methods | Named non-fault mimic | Cost / expected information |
|---|---|---|---|---|
| First: CSPA | RTP band 2 + gravity band 13; windowed cross-spectral coherence and admittance breaks, with phase-scrambled controls | Concealed juxtaposition could alter density/magnetization relations without a surface scarp. Different from GZZD curvature dipoles and PCC local gradient alignment | Unfaulted lithologic contacts, depth changes, remanence | Medium; strongest incremental-information hypothesis, uncertain improvement |
| Second: MPC | RTP band 2 + gravity band 13; log-Gabor/Riesz phase congruency and axial orientation persistence | Weak buried markers might retain phase agreement when amplitude rank is low; different from amplitude derivatives and MMT displaced markers | Lava fronts, dikes, survey ringing | Medium; potential contrast-invariance benefit, unmeasured |
| Third: PSC | RTP 2, gravity 13, basement-depth proxy 15; scale-persistent saddle-to-extremum connectors | Buried connectors might escape peak-only ridges; different from local Hessian/relay features. Gravity-derived depth is not independent corroboration | Intrusions and superposed unfaulted sources | Medium-high; topologically distinct but low specificity |
| Fourth: CNT | Conductivity 17, shear 7, dilatation 8; narrow persistent component-neck topology conditioned on dilatation | Buried pathways might have no visible scarp; different from existing broad conductive halos and margin gradients | Saline playa sediments, clay paleochannels | Medium; weakest fault specificity |

No new external product is required by these designs. That does **not** make them currently runnable: the actual shared feature cache is absent. Native feature mirrors are not an equivalent restored cache. Existing band-physics overrides in `src/gems86/io.py` must be used; band 6 is total-count radiometry, not magnetic tilt. No geothermal vent or active flow is identified by these proxies alone: the competition raster target is fault mapping, not a verified vent inventory.

**Top-candidate validation: NOT RUN.** The missing lane/cache and literal witness stop prohibit fitting or placement. No weekly slot may be spent on any of these ideas. Once unblocked, preregister the first authorized method, freeze a same-design best control, run feature-alone canaries, whole-segment buffered hide-and-recover with visible-only catalogue features, pooled shared DTI and paired spatial CI, then surface and final-dot registry tests. Stop at three experiments or two hours. A failed or incomplete registry row is not permission to omit it.

## Sources and access boundaries

| Source | What was actually checked this session | Limitation |
|---|---|---|
| [Official DrivenData reference repository](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b) | GitHub API resolved HEAD to this commit and retrieved README; CPU and GPU installation options and data-placement requirement confirmed | Does not authenticate our mirror or private leaderboard |
| [Official competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Links retained for browser review; not scraped | No portal session, quota or receipt available |
| [Official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Link retained from request; not downloaded in this session | Network allowlist excludes this host; no claim of fresh line-by-line verification |
| [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Official source link retained; not fetched | Network allowlist excludes USGS; no new external dataset claimed obtainable |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | Its mirrored H33 bytes were compared by existing forensic tool | An owner site is not an organizer score receipt |
| [GitHub Pages](https://buffedlizard55-lab.github.io/GEMSDOE86/) | GitHub API reports Pages configured, legacy build type, status built | Does not prove this branch's changes are deployed; remote content not independently fetched |

Automated downloads in this sandbox are restricted to GitHub and package registries. No credentials are requested. The request's statement that data placement is the only blocker is not true for this protocol: lane assignment, the actual shared cache, complete registry handling, comparable holdout baseline, and separate selector/quota authorization also matter. CPU execution is available; a GPU is not universally required by the official reference README.

## Pass 2 — bugs and edge cases

Regression tests reject direct upload instructions in both public guides while asserting that scientific promotion and false authorization flags remain distinct. ZIP/TIFF downloads remain accessible; pending permission uses a negative-status badge. Numerical validation wording no longer guarantees organizer acceptance. The serialized file is locally finite/in-range; we do not have the exact originally rejected bytes or a portal acceptance receipt.

## Pass 3 — request reconciliation and handoff

This review delivers safety fixes, refreshed automated audit evidence, ranked untried proposals, source/access boundaries, and a negative run card. **It does not deliver a new unique TIFF or demonstrate a competition improvement.** It does not rewrite historical model results as fresh experiments or consume a slot.

Next session priorities:
1. Restore the actual shared cached feature stack with provenance and content identities; do not substitute the native TIFF silently.
2. Reconcile the literal witness rule and like-for-like amendment through an explicit protocol disposition; keep all stop evidence visible.
3. Assign exactly one method and freeze a reproducible comparable baseline before any experiment. Audit all registry entries without silent dropping/warping.
4. Only after gates pass, have the separate selector bind quota and upload permission to the exact SHA; organizer receipt is downstream evidence of the submitted result, not a prerequisite to obtaining the first authorization.
5. Verify deployment checks after merge. Keep project-feed freshness separate from leaderboard freshness.

Verification results are recorded below after completion. Run card: [session JSON](session-085c2b7a-run-card.json).

### Final verification record

- `restore_protocol_data.py --include-registry`: PASS, pinned mirror grid/mask and witness bytes verified.
- `audit_release.py --measure-registry`: PASS as an audit, not a promotion; 20/20 inherited local formats valid, literal witness stop unchanged.
- `audit_concurrent_artifacts.py`: PASS for its scoped pair comparison and H33 pixel ancestry, not full-registry clearance.
- First full suite: 822 passed, 2 failed, 24 skipped. The review-link creation ordering and download-label regression were fixed; failures are not hidden.
- Final full `pytest -q`: **824 passed, 24 skipped, 41 subtests passed**. The 42 warnings are Rasterio affine-operator deprecations. Skipped input-dependent checks are not model validation.
- Final focused regression tests: **22 passed**.
- `build_review_card.py --check`, `build_site.py --check`, `check_site.py`, `audit_downloads.py`: PASS. Download audit revalidated 20 TIFFs/receipts; none is authorized for submission.
- `git diff --check`: PASS before commit.

No new HOLDOUT-DTI, leakage-canary measurement, pre-placement surface, final dots or competition submission was produced. Historical evidence is explicitly historical; fresh audit timestamps are not fresh model results.

### Concurrent-main integration (before merge)

The first `gh pr merge 117 --merge` attempt correctly failed because concurrent PRs had changed main. Merged `origin/main` into this same fixed session branch, preserved concurrent H86I-HVFD code/cards/TIFF and the standalone on-disk verifier, combined both irregularity entries, and regenerated conflicted HTML/evidence from the merged generator rather than choosing stale generated pages.

The refreshed combined release inventory contains **21/21 locally format-valid inherited TIFFs**, still no upload permission. The 20-file counts above describe this review's initial snapshot, not this integrated snapshot. `verify_submission_tif.py` additionally passed on the unchanged H86G bytes (finite 0/1, 55,000 positives, pinned TIFF and ZIP hashes and grid); digest identity is not a proof of geological novelty or authorization.

After integration: **839 passed, 24 skipped, 41 subtests passed**, 42 existing Rasterio warnings, in the full suite. Site/build/review checks, all 21 download checks, 22 focused regression tests and `git diff --check` passed. No model was rerun during conflict resolution; no concurrent lane is attributed to this session.
