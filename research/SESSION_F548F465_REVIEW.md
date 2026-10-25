# Focused submission-checker review — 2026-10-25

## Decision

**DO NOT SUBMIT. No new TIFF was generated; no experiment or weekly slot was used.**
The urgent new-file requirement remains unmet. Renaming an inherited TIFF or altering
its metadata would not meet it. This review fixes an actual misleading checker claim,
not the scientific blockers. The complete current request remains embedded in README
and archived in `REQUEST_20261025.md`; the standing protocol was read before changes.

## Three passes

1. **Implementation:** audited standing instructions, current downloads and prior handoff.
   Restored hash-pinned sample/fault rasters and the historical registry witness. Ran
   `audit_release.py --measure-registry`. Corrected `verify_submission_tif.py`: a pinned
   digest proves identity, not cross-registry uniqueness. Its success message now
   explicitly withholds scientific and upload clearance. Missing/corrupt files and
   malformed receipt schemas return a clear failure rather than a traceback.
2. **Adversarial review:** added tests for invalid JSON, non-object receipts, invalid
   notes, missing TIFF, corrupt/empty/wrong-member/duplicate-member ZIPs, and a malformed
   validator object. ZIP member lookup now happens only after the exact member-list
   check. Shared evaluator/writer bytes and all scientific thresholds are unchanged.
3. **Integration recheck:** full suite **852 passed, 24 skipped, 41 subtests passed**;
   42 warnings (Rasterio pending deprecations). Skips are not scientific passes.
   Release audit, generated-site consistency, link checks, download audit, frozen
   review-card check and standalone TIFF checker passed. All 21 inherited artifacts
   passed the local format audit, but none acquired upload authorization.

## H33: what explains the result?

The supplied H33 **OWNER-REPORTED 0.2778** is not an ORGANIZER-CONFIRMED result.
The supplied leaderboard figures **OWNER-REPORTED 0.3195** and **OWNER-REPORTED
0.4413** conflict; neither was independently authenticated. We cannot claim to beat
any of them. The archived H33 audit explicitly includes UNSCORED wording and a
projection; it is an owner artifact, not an organizer submission receipt.

[H33 interpretation](H33_INTERPRETATION_REVIEW.md) and the archived pixel-lineage
analysis identify catalogue-collar pruning of an existing dot pattern, not new
geophysical observations. With a triangular distance kernel and asymmetric Tversky
penalties, removing redundant low-credit predictions can improve precision without
losing much recovery. That is a plausible mechanism, not proof of why hidden truth
rewarded this file. Collar pixels can still recover unmasked faults, and separated
kernel supports can overlap. Neither density nor geology alone can be isolated from
these cross-project results. Improvement requires a matched holdout ablation, not
extrapolation from leaderboard anecdotes.

## Four unrun hypotheses retained, not rebranded as new inventions

The existing [ranked queue](../registry/h86g_hypotheses.json) already meets the request
for specific layers, signatures, missing-fault rationale and non-fault controls.
There is no assigned single method paragraph in the current request. We do not
invent a fifth parallel lane or count proposals as experiments. Qualitative order
below is expected information gain per cost, **not measured DTI improvement**.

| Rank / cost | Layers and signature | Why potentially missing / difference from implemented work | Named mimic |
|---|---|---|---|
| First / medium | RTP band 2 + gravity band 13; local cross-spectral admittance breaks | Covered density/magnetization juxtaposition without a scarp; windowed spectra rather than PCC local gradient alignment | Unfaulted lithologic contact |
| Second / medium | RTP band 2 + gravity band 13; monogenic phase congruency | Weak buried marker contrast; phase alignment rather than amplitude ridges or MMT marker shifts | Dikes and lava-flow contacts |
| Third / medium-high | RTP 2, gravity 13, basement depth 15; persistent saddle connections | Buried links missed by peak-only extraction; graph topology rather than CTHB local Hessian ridges | Superposed unfaulted intrusive sources |
| Fourth / medium | Conductivity 17, shear 7, dilatation 8; narrow persistent conductive necks | Covered pathways; connectivity rather than conductive-margin gradients | Saline paleochannels |

No additional external product is required by these proposals; **the actual shared
feature cache is still missing**. Native raw rasters are not a substitute for that
cache under the requested reuse rule. Top-candidate holdout validation did not run
because the preflight stops before candidate construction. No feature-alone AUC,
HOLDOUT-DTI, confidence interval or candidate uniqueness number is invented.
Conductive or structural proxies are not verified geothermal vents; this task's
fault prediction metric cannot establish a vent discovery.

## Verified source scope and limitations

[Source receipt](session-f548f465-sources.json) records a fresh retrieval and byte
comparison for precisely these two immutable documents:

- [Official reference README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md): explicitly supports CPU-only operation. A GPU is helpful, not universally required.
- [H33 owner audit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/780a5a534269c79adfe6d1d7d5aadead161332aa/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json): source identity verified, performance not organizer-confirmed.

Official links for manual review, **not fetched or verified this session**:
[competition description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
[data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/),
[rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf),
[GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
[GDR 1391](https://gdr.openei.org/submissions/1391).
Outbound hosts are restricted; we did not scrape the competition portal, retrieve
its live weekly quota or verify all fleet sites. Hash-pinned owner mirrors are not
organizer-authenticated training data. No full scientific line-by-line verification
of every historical experiment is claimed.

## Prioritized next session

- Resolve the literal registry-support contradiction explicitly: the pinned dense
  witness covers every allowed cell. Existing PA diagnostics cannot override a
  failing literal upload gate. Do not silently omit this witness.
- Restore and bind the shared cache, reconcile invalid-grid registry entries, and
  assign one method lane. Keep the current four proposals unrun until then.
- Freeze same-split controls; run individual-feature canaries and buffered
  whole-segment hide-and-recover with paired spatial confidence intervals.
- Only promote after matched improvement and both uniqueness stages pass; keep the
  weekly-slot selector separate. A format-valid download is never sufficient.

The existing homepage and executive summary expose downloads and state DO NOT
SUBMIT. This session improves automated integrity validation; it does not turn an
inspection-only artifact into a competitive submission.
