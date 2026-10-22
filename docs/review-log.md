# Three-pass implementation and review log

Review date: 2026-10-22 UTC. This log records actual review passes and the checks performed; it does not claim a scientific experiment or submission validation.

## Pass 1 — requirements, prior art, and source screening

- Converted the standing request into the persistent README charter and a fail-closed release gate.
- Reviewed accessible GEMSDOE32/GEMSDOE83 hypotheses and methods. Excluded ComCat/moment tensors, thermal-infrared concepts, LiDAR/scarp features, surface conductivity, geothermometers, SGMC, relay geometry, and previously used emitters from the “new” shortlist where prior art was visible.
- Ranked three conditional ideas; selected depth-coherent USGS MT conductance as the top *research lead*, not as a viable predictor. Added Sentinel-1 repeat-pass deformation as a distinct-source reserve hypothesis and a deep-background-conditioned conductance variant.
- Checked the official USGS ScienceBase record and its data-release bounds, then fetched the associated surface-layer world file. The world file reports 1000/−1000 map-coordinate pixel spacing and a projected-looking origin, while the ScienceBase raster facet declares EPSG:4269. This unresolved CRS/scale issue is recorded as a stop condition; the GeoTIFF itself was not fetched.
- Kept exact competition-footprint coverage, full-registry novelty, and source bytes explicitly unverified. **No experiment started.**

## Pass 2 — data, evaluator, leakage, uniqueness, and artifact contract

- Rechecked the official data-page state: it redirects to login in this session. Local Python lacks the scientific packages, and no authorized raster, cached feature stack, or complete registry index is available in GEMSDOE86.
- Inspected the shared implementation read-only. Recorded evaluator version `gems57-pooled-hide-v2`; selected `buffered_component_draw` rather than the separate short-strand protocol. The planned split withholds whole 8-connected components, uses label-blind quadrant selection and a buffered feature context, and keeps visible fault-derived features/masking fold-specific.
- Read the shared metric, validation, gate, grid, and writer interfaces. Added a run card that records HOLDOUT-DTI evidence fields, leakage canaries, both uniqueness phases, exact shared-writer input/on-disk/ZIP/receipt checks, and the separate slot-selector decision. All measurement and validation fields remain null/NOT_RUN.
- Kept all shared code outside this repository; no prior submission TIFF was copied and no invalid placeholder was written.
- Decision after this pass: **stop**. No HOLDOUT-DTI, withheld-positive count, 95% CI, uniqueness result, validator receipt, or organizer receipt exists.

## Pass 3 — site, automation, and release review

- Built a responsive GitHub Pages experience with the submission state and executive instructions first. The download has no active URL in the blocked state and can unlock only from a run card with a passing HOLDOUT-DTI record, paired 95% CI, withheld-positive count, hashed registry inventory, surface/final uniqueness measurements below stop thresholds, shared-writer checks, and matching TIFF/ZIP/receipt hashes.
- Added an official public-leaderboard refresh that fails closed on login redirects or page-layout changes, plus a prerequisite checker that never claims validation from file existence alone.
- Ran the standard-library unit suite successfully, including fail-closed prerequisite checks, parser behavior, and rejection of an unapproved TIFF. `scripts/check_site.py`, JavaScript syntax checking, Python byte-compilation, and `git diff --check` passed.
- Served the docs locally on the live preview port and confirmed HTTP 200 for the overview, executive instructions, research, hypothesis dossier, sources, audit page, and run card.
- Final state remains **BLOCKED_NO_EXPERIMENT**. Site readiness is not submission readiness; no TIFF/ZIP is offered.

## Remaining gates

1. Obtain authorized competition inputs and the cached stack; establish the exact shared-tool checkout and verify its pin/hashes.
2. Obtain a complete hash-verified registry inventory.
3. Fetch the USGS conductance GeoTIFFs only after resolving the CRS/world-file discrepancy; check actual transform, ground resolution, nodata, and exact GEMS valid-pixel coverage. Check exact Sentinel-1 acquisitions before treating H86-B as viable.
4. Freeze a baseline and experiment preregistration. Run each feature alone as a leakage canary; stop on AUC >0.90 until resolved.
5. Run the unchanged shared buffered whole-component holdout and evaluator; record pooled DTI, evaluator version, withheld positives, and paired 95% CI.
6. Check continuous surface and final raster uniqueness against the complete registry; stop and record any duplicate above the stated limits.
7. Call the shared writer only after all gates pass. Publish one unique TIFF plus its shared ZIP/receipt only when the run card, bytes, and hashes agree. Leave weekly-slot promotion to the separate selector.
