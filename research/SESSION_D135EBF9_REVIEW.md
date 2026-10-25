# Review d135ebf9 — 2026-10-25

## Executive decision: DO NOT SUBMIT

No new TIFF, geological experiment, or weekly submission was made. The requested unique, scientifically validated new submission remains **unmet**, not silently replaced with a renamed existing raster. No single method paragraph was supplied for the parallel lane. Current workspace inspection also finds missing native training inputs and no authenticated shared feature cache. These are execution blockers, not evidence that a hypothesis is negative.

The newest inherited H86M-LT TIFF remains an easy [audit download](../docs/h86m-lt.html). Registration now makes the standard release audit cover all 36 published research TIFFs. Its previous `safe_to_submit=true` claim is withdrawn. Original numerical projections remain in its run card for reproducibility, with `historical_verdict=promote`; current verdict is negative, not upload-authorized. No raster or ZIP bytes were changed.

## Why H33 may have outperformed related submissions

The owner supplied a reported result of 0.2778, not an organizer receipt. The prompt also supplies conflicting best-score claims (0.3195 and 0.4413). None is a verified current leaderboard result here. Do not label them ORGANIZER-CONFIRMED.

The archived [H86M analysis](H86M_LT_REVIEW.md) attributes H33's geometric difference from a related parent to removal of catalogue-collar dots. This review did not independently reconstruct that comparison. Under the repository's DTI algebra, removing predictions that contribute false-positive mass but no additional triangular-kernel recovery can improve the precision-weighted objective. That is a plausible explanation, **not a causal proof about hidden organizer labels**. Sparse emission can reduce redundant mass, but also lose recovery. Geological truth cannot be inferred uniquely from a small collection of aggregate scores; many hidden label arrangements explain the same scores. Fitting those same aggregate scores and evaluating the fitted belief is not an independent holdout. Therefore no defensible claim that a new file will exceed H33 follows from the existing tomography projections.

## Pre-implementation hypotheses (proposals only)

Ranked qualitatively by expected information gain for HOLDOUT-DTI per cost; no numeric improvement is predicted. These are exact proposed refinements, not claims of worldwide novelty. Native band names follow `src/gems86/io.py`; the earthquake bands are gridded proxies, not earthquake event catalogues. All require the existing shared feature cache and visible-only holdout derivations. No new external data is necessary, but that cache is not currently established. Do not implement any proposal by privately rebuilding it.

| Priority | Layers and physical signature | Why possibly unmapped; named mimic | Difference and cost |
|---|---|---|---|
| 1 | Earthquake-proxy bands 10/16: compute local anisotropic ridge tensors separately; retain common axial structure only where the two scale-specific tensors agree and local gravity-band-13 curvature supports a discontinuity | Buried fault zones may concentrate seismicity without a surface scarp. Volcanic earthquake swarms or smoothing artefacts can mimic alignment | Exact two-proxy tensor-consistency ablation differs from the scalar seismic corroboration in RKSC/CSGD and the executed BMR/CNT controls. Earthquake anisotropy was already proposed by H86M, not demonstrated as successful. Medium cost; reject if it cannot beat a scalar-proxy control on paired blocked holdout |
| 2 | Bands 2/13: estimate local gravity/magnetic edge-offset vectors; require an offset direction consistent across filter scales, rather than merely co-located edge strength | Burial or source-depth contrast may separate signatures across an unmapped structure. Dipping stratigraphic contacts and remanent magnetization are named mimics | Exact stable vector-offset test is a refinement, not a rerun of CSGD cross-spectral admittance, STDP magnetic up-dip migration, or BMR basement residuals. High cost and lower specificity; include a zero-offset and shuffled-direction control |
| 3 | Elevation band 12 plus gravity band 13: test paired curvature sign reversals across opposed basin-margin windows, vetoing a single symmetric valley profile | Opposed fault-controlled basin margins may lack mapped scarps under fill. Erosional valleys and lake shorelines can produce the same shape | Paired-window antisymmetry with an erosional-valley null differs from generic scarp/slope ridges and the executed CNT compact-source test. Medium cost, lower expected information gain; reject if a simple relief control explains it |

None is promoted or asserted to be globally untried. A complete fleet implementation audit is still required before lane assignment. No opportunity to run a test is presented as a passing test. BMR/CNT have already been tested negatively and should not be rerun unchanged.

## Three verification passes

1. **Implementation:** read AGENTS, PROMPT, README; installed dependencies in an ignored virtual environment. Initial tests found 19 failures. H86M-LT TIFF/ZIP existed without inventory registration; its site/run card advertised upload clearance despite missing the required HOLDOUT-DTI. Registered both artifact/evidence joins; added a strict unvalidated-archive normalization; withdrew the misleading upload claim.
2. **Review:** restored only pinned protocol rasters and witness using the existing restorer; remeasured all inherited final dots under the unchanged literal-support rule. No model ran. That witness is a sufficient literal negative, not a full-registry uniqueness scan. Found stale secondary download audit/count; refreshed generated reports and site. The historical H86M full-registry report uses Pearson for its continuous surface; that cannot establish Spearman compliance or prove surface checks preceded placement.
3. **Final regression:** added adversarial archive tests that reject authorization, fabricated holdout values and slot use. Run the shared audit, download audit, generated-site idempotence, site checker and full pytest suite. Exact final results are recorded in the PR and completion report rather than preclaimed here.

## Sources and access boundaries

- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution): README retrieved via GitHub API in this review; it instructs downloading competition data and provides CPU as well as GPU environments. Thus the prompt's blanket “GPU needed” assertion is not a universal requirement.
- [Competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [submission/data portal](https://www.drivendata.org/competitions/306/competition-doe-gems/data/): official links for review, not fetched or independently verified this session. No portal authentication or organizer receipt available; automated scraping prohibited by standing repository instructions.
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [GDR 1391](https://gdr.openei.org/submissions/1391), [NLR rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf): official source pointers retained, not claimed freshly retrieved. Sandbox outbound access is limited to GitHub and package hosts. These pointers do not authenticate mirrored input bytes.
- [Prior H33 site](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html): owner research, not organizer confirmation.

## Next session, in order

1. Restore native bytes using existing hash-pinned restorer; separately establish the shared-template cache's implementation, feature and visible-mask identity. A native TIFF is not a verified shared cache.
2. Freeze one geological lane, a like-for-like baseline, whole-segment buffered folds and controls before computing a surface. Test each feature alone for leakage; require paired improvement with CI. Keep SGMC proxy and fleet-feedback projections separate from HOLDOUT-DTI.
3. Restore complete registry, require rank-correlation surface checks **before** placement, final-dot comparisons before writer serialization, and unchanged duplicate thresholds. Resolve the literal dense-witness contradiction through an explicit shared protocol decision, never a hidden bypass.
4. Only after scientific, format and uniqueness gates pass, run the separate selector within an organizer-confirmed quota. No code here uploads to the portal. No result can guarantee the leaderboard rank.

### Final verification result

Shared release audit, download byte/ZIP audit, `build_site.py --check`,
`check_site.py`, and `git diff --check` passed. Full suite: **1033 passed,
24 skipped, 48 warnings, 58 subtests passed**. Skips are not passes; warnings
include rasterio Affine multiplication deprecation. No scientific model was run.
