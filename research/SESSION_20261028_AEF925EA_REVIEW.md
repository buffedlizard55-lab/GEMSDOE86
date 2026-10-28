# Independent review — 2026-10-28

## Decision: DO NOT SUBMIT

No new model, geological experiment, candidate TIFF, or competition upload was
made in this review. There is no newly validated submission or credible live
score estimate. Existing TIFFs are research-only; the user’s requested unique,
high-scoring submission remains **unfulfilled**. The [nine-site summary](../docs/nine-sites.html)
identifies reported historical files, not recommended uploads. Scores provided
by the user have no organizer receipt here. The reported H33 **0.2778** is
OWNER-REPORTED, not ORGANIZER-CONFIRMED. Conflicting leaderboard figures are
unverified; neither can establish the current leader.

Prior pixel forensics suggest H33's relative sparsity and catalogue-collar
removal may reduce redundant false-positive mass while preserving distant
coverage. This is a hypothesis, not an isolated causal measurement, and no
observed result here proves a future score will exceed H33. See the
[previous review](SESSION_20261027_55A5BFA4_REVIEW.md) and
[Focus-9 evidence](../docs/evidence/focus9-forensics-20261026-rev2.json).

## Three passes

1. **Inputs and protocol:** installed CPU dependencies in ignored `.venv`;
   `audit_workspace_inputs.py` finds hash-matched sample and fault rasters but
   no native feature TIFF, prepared bands or proven shared template cache.
   `--require-native` exits nonzero. Restored only the pinned historical
   witness via GitHub, not official data. Independently remeasured it with the
   pinned shared `saturation_certificate`: every allowed pixel is positive in
   the witness and the literal stop is unavoidable for any nonempty dot field.
   [Measurement with hashes](SESSION_20261028_AEF925EA_WITNESS.json).
   One witness proves failure, not full-registry clearance. The scoped
   representation-aware amendment does not authorize upload or override the
   repository's binding literal gate. No method paragraph assigning a single
   lane is identifiable in the current request; no model was run.
2. **Corrections and failure modes:** the generated nine-site page had presented
   historical owner reports as estimated scores, implied an ignored TIFF must be
   in every checkout, and described an organizer receipt as a pre-upload
   requirement. These are corrected. It now states the H87 experiment's
   cell-bootstrap confidence interval is not the requested spatial-block CI and
   that its visible-only holdout arm is not its full-catalogue final raster.
   The comparison stop is strictly **greater than** 0.70, not greater than or
   equal to it. H86T's local range check is no longer described as guaranteeing
   organizer acceptance; physical-band identity remains disputed, as documented
   in the independent prior review. The previous rejected file was not located,
   so its range error cannot be diagnosed from another TIFF.
3. **Recheck:** `python -m pytest -q` passed (1,143 passed, 24 skipped,
   58 subtests; 48 rasterio warnings) before the final copy-only site clarification;
   the new targeted tests and `build_site.py --check` / `check_site.py` passed
   again afterward. `audit_downloads.py` revalidated all 49 research files and
   `audit_release.py` reported no upload approval. Passing software tests and
   local file checks do not prove a geological mechanism, organizer acceptance,
   full uniqueness, or leaderboard rank. Historical reports remain immutable;
   their assumptions are superseded by this review and the corrected generated
   page, not silently rewritten.

## Next work and access boundaries

- Establish a single assigned, novel method and its inputs; the current request
  contains no identifiable single method paragraph. Do not reuse a failed lane
  or infer novelty from a name. Existing queues do not establish that all
  hypotheses are untried or presently executable.
- Restore the actual shared feature stack with immutable input and fold-visible
  provenance; an owner-mirrored native TIFF alone is neither official data nor
  the required shared cache. Check all feature/band identities against
  `src/gems86/io.py` before use. Native and full registry data are absent here.
- Reconcile the literal witness contradiction in an explicit authorized shared
  protocol decision. Until then the requested stop precludes a new nonempty
  submission, even if a smaller registry subset gives a favorable result.
- Only then run up to three preregistered experiments or two hours with per-feature
  canaries, leakage-safe buffered segment hiding, pooled DTI, spatial-block
  paired confidence intervals and complete surface/final-dot registry checks.
  A separate selector must establish quota and authorization before any upload.
- The sandbox is restricted to GitHub and package registries; it cannot directly
  access DrivenData, USGS, DOE GDR, NLR or Dropbox. Per repository policy, do
  not automate DrivenData access. The user's score assertions and links cannot
  be authenticated by this review; no official competition receipt was obtained.
  The [organizer reference README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md)
  was retrieved via GitHub: it describes CPU and GPU environments; GPU is not a
  universal training prerequisite. [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
  [DOE GDR 1391](https://gdr.openei.org/submissions/1391),
  [competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
  and [NLR PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) are manual-review
  links only, not freshly verified data or permission to use restricted assets.

Run card: [SESSION_20261028_AEF925EA_RUN_CARD.json](SESSION_20261028_AEF925EA_RUN_CARD.json).
