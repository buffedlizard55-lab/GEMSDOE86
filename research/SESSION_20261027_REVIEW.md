# Repository review — 2026-10-27 (`arena/47135c6b-gemsdoe86`)

## Decision first

**DO NOT SUBMIT. No new TIFF was generated, no model experiment ran, and no weekly slot was used.** The request's absolute “generate a unique TIFF” demand cannot override its own parallel-run stop rules. No single method paragraph is assigned in the current request; the required shared cached feature stack is absent; native `training_features.tif` and prepared bands are absent in this checkout; and the inherited full-support registry witness overlaps every nonempty in-footprint dot set at 1.0, above the literal 0.70 stop. Do not generate a file by bypassing these gates or relabel an inherited artifact as new.

The release audit remains `DO NOT SUBMIT`: 46/46 inherited research TIFFs pass local format/integrity validation, but all remain audit-only. The public site is built from `scripts/build_site.py`; the Focus-9 summary now labels score provenance and uniqueness, corrects GEMSDOE28's top historical entry from H27-4 (0.2708) to H36-1 (0.2710), and explains that no live score estimate is defensible for a new candidate in this checkout.

## Highest reported Focus-9 results

These are historical **OWNER-REPORTED** values copied into `registry/prior_scores.csv`, not ORGANIZER-CONFIRMED receipts, not projections, and not a current leaderboard snapshot. The local raster forensics in `research/SESSION_20261026_H86R_SFG_REVIEW.md` reports each row's 3-pixel overlap against H33. The archive pages below are cited for provenance; they are not endorsement to re-upload the same historical submissions.

| Site | Best historical entry | Reported value | 3-px overlap vs H33 | Reuse/uniqueness conclusion |
|---|---|---:|---:|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | 0.885 | Not unique; already submitted; legacy `-nan` variant is not all-finite |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | 0.882 | D28 family; not unique; already submitted |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | 0.867 | Not unique; already submitted |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | 0.955 | Highest entry on this site; not unique; H27-4 is lower at 0.2708 |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | 0.882 | Same D28 raster family as GEMSDOE25; not unique |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | 0.954 | Pixel clone of GEMSDOE28 H27-4; not unique |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **0.2778** | 1.000 (reference) | Highest Focus-9 claim; already submitted; never re-upload |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | 0.926 | H33-lineage variant; not unique |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | 0.974 | H33 superset; not unique |

**Why H33 reached the highest supplied Focus-9 result:** repository pixel-forensics describe it as a D28 → H27-4 lineage refinement that removed 2,545 predictions in a 1–2 pixel mapped-fault collar while retaining much of the far-field population. Under the stated asymmetric distance-weighted Tversky metric, removing low-marginal-credit dots can reduce false-positive mass while preserving useful coverage. This is a plausible mechanism, not a controlled causal finding: the sites' historic predictions differ in other ways, the organizer's hidden truth is unavailable, and no receipt verifies 0.2778 here. The reported lead is not evidence a different unique raster will score higher. The competing 0.3195/0.4413 leaderboard marks in user input conflict and are not authenticated in this session.

For an existing historical file, the table's reported score is the only directly comparable value; it is not an estimated score. For a *new unique* raster, estimated live score is **not available**: there is no candidate, no current candidate HOLDOUT-DTI, and the repository's small owner-claim regression is explicitly not a calibrated live-score predictor. No projection is presented as a score.

## Ranked hypotheses before any future implementation

The following are three unrun candidates already present in the reviewed research queue (`registry/h86r_hypotheses_20261026.json`). They are ranked qualitatively by expected information gain / plausible blocked-holdout lift per cost, not by claimed score. They are proposals, not an assigned lane; no candidate surface, canary, holdout, or estimate was run today.

| Rank | Candidate | Layers and physical signature | Why it might recover a catalogue-missing fault | Difference from prior implementations / main mimic | Cost and current viability |
|---:|---|---|---|---|---|
| 1 | Detectability-weighted positive-unlabeled training (H86R-2 DWPU) | Native Band 15 `depth_to_base_surf` and Band 19 `det_elev_slope` inform spatial detectability weights; test a fold-local classifier against its unweighted PU ablation. The target is observation-process correction, not a new raster edge. | Avoids treating an unlabeled fault under low-visibility basin cover as a reliable negative; may reduce surface-expression bias and improve extrapolation to concealed faults. | Statistical observation model rather than another fault-distance, edge, or dot-allocation layer. Mimics include mapper/access bias and depositional cover correlated with basin geology. | Low–medium code cost; no new external layer, but **not executable compliantly now** because native inputs, prepared stack and verified shared cache are missing. |
| 2 | Catchment-graph χ-knickzone back-projection (H86R-3 / KNDS family) | USGS 3DEP χ/knickpoint derivatives plus native Bands 12, 15 and 19; test cross-catchment, strike-coherent knickzone alignments rather than isotropic curvature maxima. | A buried range-front or intrabasin structure could perturb channels after an exposed scarp is eroded, leaving aligned channel-profile breaks. | Exact catchment-graph back-projection was not identified in the prior H86R review, but χ/DEM features have been used elsewhere in the repo; novelty is the graph-level cross-catchment operator, not the layer itself. Mimics include resistant caprock ledges, lithologic contacts and wave-cut shorelines. | Medium–high; requires verified 3DEP-derived grid, manifest/lineage pin, and fold-safe processing. Official source: [USGS 3D Elevation Program](https://www.usgs.gov/3d-elevation-program). The source page was not fetched in this session; local `dem10_chi` bytes are absent, so availability/provenance is **not verified here** and this is not ready to run. |
| 3 | RANSAC geometry of geothermal well/spring/vent alignments × conductance (H86R-4) | DOE GDR #1391 in-footprint wells/springs/vents plus native Band 17 `cond_surf`; score robust point-line alignment corroborated by a conductance corridor, without reading `dist_known_fault_px`. | A concealed permeable fault system could organize geothermal manifestations even where no mapped surface rupture is present. | Prior work used blurred point-density corridors; robust point alignment is the distinct proposed operator. Mimics include road/ranch access, exploration siting, and non-tectonic spring clusters. | Low–medium code cost, but expected recall is low. Official source: [DOE Geothermal Data Repository submission 1391](https://gdr.openei.org/submissions/1391). Source and CSVs are named in the project manifest, but current bytes were not restored or checked for availability in this session; **not viable until hash-pinned inputs are present**. |

**Selection rule:** although DWPU ranks first in the old queue, no one may begin implementation until the owner assigns one exact method paragraph, shared cache identity is restored, and the contradictory literal witness rule has an approved shared resolution. Then at most three preregistered experiments / two hours; each feature gets a leakage canary, and any AUC > 0.90 is a stop pending proof. Use the pinned evaluator/writer only. Do not select or spend a submission slot here.

## Current checkout measurements and verification

- `python scripts/audit_workspace_inputs.py` (UTC `2026-10-27T17:11:14.937749+00:00`) reports `training_features.tif` missing in both `data/` and `data/bridge/`; `existing_faults.tif` and `sample_submission.tif` are hash-verified; native prepared bands and the shared feature cache are missing. `safe_to_submit=false`, `approved_for_weekly_slot=false`, 0 experiments, 0 slots.
- `python scripts/audit_release.py`: `audit_ok=true`, 46 artifacts locally valid, decision `DO NOT SUBMIT`, 0 experiments, 0 slots.
- The current release evidence records the historical full-support witness (`sha256 ab0a0a62…`) at direct support-overlap 1.0 vs permitted maximum 0.70. This is a hard negative for every nonempty raster, not a candidate measurement and not a complete-registry uniqueness pass.
- Installed the exact pinned dependencies in ignored `.venv/` (not committed). Full test suite: **1,101 passed, 24 skipped, 48 warnings, 58 subtests passed**. Warnings are Rasterio `PendingDeprecationWarning` for Affine `*` multiplication.
- After the summary correction, `scripts/build_site.py --check`, `scripts/check_site.py`, `scripts/audit_downloads.py`, and `git diff --check` pass; all 46 published TIFFs remain audit-only.
- No DrivenData page or leaderboard was fetched. `AGENTS.md` prohibits automated DrivenData access under its Terms-of-Use instruction. Therefore every quoted result remains owner-reported, no current official leader or quota is asserted, and there is no organizer score receipt.

## Three-pass review log

1. **Pass 1 — establish baseline and requirements.** Read `PROMPT.md`, `README.md`, `AGENTS.md`, `research/REQUEST_20261026_REV2.md`, the current workspace review and Focus-9 forensics. Confirmed the user's named site list, no assigned method paragraph, inherited hard stops, and existing executive summary. Set up the pinned test environment. No experiment or candidate generated.
2. **Pass 2 — inspect for errors / missing requirements.** Ran the live input audit and release audit. Found a real summary-table ranking error: GEMSDOE28's 0.2710 H36-1 entry outranks the table's previously displayed H27-4 at 0.2708. Also found the summary lacked a column explicitly stating overlap/uniqueness and did not clearly separate historical score from a projection. Updated the generated source, not the generated HTML by hand. Added regression coverage. No attempt was made to evade blocked gates.
3. **Pass 3 — end-to-end verification.** Full suite passed: **1,102 passed, 24 skipped, 48 warnings, 58 subtests passed**; targeted summary/site tests passed (17 tests, 3 subtests). The generated summary check, site link/download audits, release audit and `git diff --check` pass after rebuilding. Final result remains negative: the requested unique upload-ready TIFF and an estimated new live score remain unmet, because the scientifically necessary shared inputs and protocol clearance are absent.

## Official sources and limitations

- [Competition problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition rules / landing page](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [NLR/DOE GEMS Prize PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [DOE GDR submission 1391](https://gdr.openei.org/submissions/1391)
- [Current project's source register](../docs/sources.html) and historical Focus-9 measurements: [`SESSION_20261026_H86R_SFG_REVIEW.md`](SESSION_20261026_H86R_SFG_REVIEW.md), [`focus9-forensics-20261026-rev2.json`](../docs/evidence/focus9-forensics-20261026-rev2.json).

Outbound access in this environment is restricted to GitHub, npm and Python package hosts; the USGS, DOE GDR, DrivenData and GitHub Pages hosts were not fetched directly in this session. Links are for manual review, not claims of current availability.
