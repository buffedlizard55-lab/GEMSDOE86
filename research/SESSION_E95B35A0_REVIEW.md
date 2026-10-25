# Repository review — 2026-10-25 — e95b35a0

## Executive decision

**DO NOT SUBMIT. No new candidate TIFF generated. No slot selected or consumed.**

The requested deliverable is a novel, scientifically validated competition raster, not a renamed historical raster. This review cannot honestly deliver that raster under the literal parallel-run rule. The restored, SHA-pinned historical dense registry witness covers every allowed candidate location. Consequently every nonempty allowed dot field has forward 3-pixel overlap 1.0, exceeding the owner's 0.70 limit. This is a mathematical blocker, not a requirement for human visual inspection. No threshold or policy exemption was introduced.

The current prompt also says to stay within “the single method paragraph below”, but supplies no designated method paragraph. This session therefore repairs shared publication infrastructure rather than selecting a competing scientific lane.

## Pass 1 — inspect and repair

- Read `AGENTS.md`, `PROMPT.md`, and `README.md` before editing. The standing request is retained in `PROMPT.md` and linked prominently from the README.
- Installed `requirements-lock.txt` in an ignored `.venv`; the system Python initially lacked NumPy.
- Ran `scripts/audit_workspace_inputs.py`: native training feature raster absent; native prepared arrays absent; shared template feature cache not established. Historical preparation receipts are not current capability. This is NOT a GPU-only blocker.
- Restored only the pinned registry witness and proof templates through `scripts/restore_protocol_data.py --include-registry`. These are owner mirrors, not organizer-authenticated data. Restoring a past prediction for a read-only counterexample is educational/audit reuse, not a new submission.
- Reproduced the unregistered H86L-FMC TIFF/ZIP error. Added the existing artifact to both publication indexes, binding the actual TIFF SHA to its existing negative scientific run card. No TIFF, ZIP, model, evaluator, or writer bytes were changed.
- Added an explicit archived H86L-FMC schema in `scripts/audit_release.py`. Its numerical result remains labelled **archived leakage-suspect HOLDOUT-DTI**, not fold-visible validation or promotion evidence. Fleet predictions built with the full catalogue cannot become valid hide-and-recover features merely because their canary passes.
- Re-measured every published artifact against the restored witness and rebuilt the audit report, download integrity report and site. All 32 TIFFs/ZIPs pass local format/integrity checks; all 32 fail literal witness uniqueness. The witness scan is one-raster, sufficient to prove failure, NOT a complete-registry clearance.

## Why H33 could improve, and what is not proved

The request's H33 value **0.2778**, purported leaderboard best **0.4413**, and alternative best **0.3195** are owner-reported claims, not ORGANIZER-CONFIRMED scores. There is no new submission-page receipt here. They cannot be used as measured training targets or promised achievable scores.

Existing byte-comparison evidence in `research/SESSION_0C60B079_REVIEW.md` finds H33 removes 2,545 parent dots and adds none inside the footprint, while also changing outside-footprint NaN encoding to zero. That comparison was NOT rerun here because the scored-fleet rasters are absent. The metric implementation in `vendor/template66/gems/metric.py` maps NaN to zero, so the encoding change is neutral under that implementation, not independently proven neutral under a live organizer evaluator.

Mechanism: the distance-tolerant Tversky metric charges false-positive mass as well as rewarding truth credit. Catalogue-collar dots with little incremental hidden-truth credit can lower the metric. Pruning them can improve precision without comparable recall loss. That explains a possible gain; it does not identify the cause of an unverified live score. The supplied labels describe mapped faults, not geothermal vents. Vent discovery is a downstream geological interpretation; it is not the label definition of this raster task.

No defensible extrapolation from this information establishes a result above any claimed live score. The next scientifically useful gain must survive a matched, fold-visible, buffered whole-segment holdout with a positive paired confidence interval, independent canaries and registry checks before and after placement. A maximum across incompatible historical instruments is not a current holdout best.

## Ranked research queue — hypotheses, not experiments or score projections

This table is recorded before any geological implementation in this session. Rank is qualitative research priority (specificity and falsifiability), **not expected numerical DTI gain**; no defensible improvement estimate exists. These are narrower proposed variants, not claims of unprecedented geology or fleet-wide novelty. None is currently viable for execution: the required shared cache is missing and the literal registry rule is binding. All use already documented native bands (`src/gems86/io.py`); no new external data source is assumed obtainable.

| Priority / cost | Proposed test and specific layers | Signature and rationale for an uncatalogued fault | Difference from existing code / known collision risk | Named non-fault mimic |
|---|---|---|---|---|
| 1 / medium | Density–basement closure residual: B13 `iso_grav_anom`, B15 `depth_to_base_surf`; B2 `rtp` as independent corroboration | Fit a fold-training-only regional gravity/depth relation; detect persistent, signed residual steps across inferred basin margins. Buried offsets can lack a mapped surface scarp. | Residual-model cross-fitting and signed matched step, rather than pointwise edge fusion. BMR is already queued and CSGD already uses cross-spectral residuals: this is a proposed refinement, NOT an unused lane authorization. | Unfaulted sediment-density facies transitions; erroneous basement inversion |
| 2 / medium | Conductive sheet termination: B17 `cond_surf`, B15 basement, B8 `geod_dilaterate` | Directional change-point pairs at elongated conductive-sheet terminations, conditional on extension, rather than large conductivity alone. A concealed fluid pathway may terminate against a buried structure. | Explicit endpoint-vs-interior ablation; existing conductivity edges and relay methods overlap conceptually. Requires novelty audit before assignment. | Playa salinity fronts and irrigation-related moisture contrasts |
| 3 / medium | Magnetic trough/flank asymmetry: B2 `rtp`, B9 `tmi_vg`, B13 gravity | Oriented central magnetic low with asymmetric flanks at a density step; test sign-sensitive template against amplitude-matched edge control. Concealed alteration may survive without topographic expression. | Finite-width sign-pattern test rather than phase-only MPC or generic magnetic-low fusion. PSTD/CSGD already test demagnetisation: not certified novel. | Remanently magnetized volcanic dykes and intrusion contacts |
| 4 / low–medium | Surface-subsurface disagreement as a negative control: B12 `det_elev`, B19 slope, B13 gravity, B2 RTP | Reject topographic ridges lacking persistent subsurface corroboration; compare to the same model without rejection. Targets buried evidence instead of mapper-visible scarps. | Predeclared falsification/negative-control test rather than a new geological discovery claim. Many existing lanes already use topographic vetoes, so novelty is especially uncertain. | Lake Lahontan shorelines, alluvial-fan margins and fluvial terraces |

A leakage canary must be run on **each feature separately**, including fitted residuals, before any DTI is trusted. An AUC over the owner's threshold stops the experiment until explained. No canary or HOLDOUT-DTI was generated in this review; missing measurements are null, not zero.

## Sources and limits of verification

| Source | Verification in this session | Scope |
|---|---|---|
| [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b) | GitHub API resolved HEAD to this commit; read README directly | Official README explicitly supports CPU-only operation; GPU is faster, not an absolute training requirement. Data download remains separate. |
| [GEMSDOE32 H33 source](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/src/gems32/h33.py) | Read source using GitHub API; inspected tree for H33 evidence | Owner research source, NOT official score verification. Its geological surface code alone does not prove which bundle earned a score. |
| [Pinned dense witness](https://api.github.com/repos/buffedlizard55-lab/17GEMSDOE/git/blobs/374c88b1da2b803e2ed160de467fd71ae114010d) | Downloaded and SHA-verified using existing restoration code | One historical prediction proves literal overlap failure; not a scientific training input or complete registry. |
| [Official competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Links retained for review; NOT fetched anew | Repo prohibits automated DrivenData scraping; sandbox outbound hosts exclude the PDF host. Prior archived reading is not a current verification. |
| [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [GDR 1391](https://gdr.openei.org/submissions/1391), [INGENIOUS](https://gbcge.org/current-projects/ingenious/) | Sources retained, not reverified for current availability | External-host access is restricted. No new-data-dependent candidate is described as executable. |

The range error cannot be diagnosed from the text alone. Current published files are all finite and within [0,1], with the template CRS/shape/transform, so no current artifact reproduces it. No claim is made about the unidentified file previously uploaded.

## Pass 2 — review and regression protection

Added tests for exact publication coverage, retained leakage caveat, negative/no-slot state, evaluator identity, invalid/nonfinite DTI, malformed CI and boolean positive counts. Registration must never silently turn the prior failed lane into a successful experiment. Shared template bytes and thresholds remain unchanged.

## Pass 3 — end-to-end verification and remaining work

Final command outcomes are recorded in the README and session run card after execution. The executive guide and homepage are generated from the same inventory and evidence; every artifact remains audit-download only.

Next session: resolve the missing method assignment and literal dot-set policy in writing; establish shared-cache provenance rather than privately rebuilding it; then restore full registry inventory and run at most three preregistered experiments. Native feature bytes can be fetched from the existing pinned owner mirrors, but that alone is NOT shared-cache provenance and cannot remove the policy stop. Only a matched validated winner may be proposed to the separate selector. Current organizer quota and receipts are unknown. No automated upload was attempted.

### Final executed outcomes

- `.venv/bin/python -m pytest -q`: **1015 passed, 24 skipped**, 58 subtests passed; 48 Rasterio deprecation warnings.
- `scripts/audit_release.py --measure-registry`: audit OK, all 32 formats valid, all final artifacts remeasured, decision DO NOT SUBMIT.
- `scripts/audit_downloads.py`: PASS, 32 TIFFs/receipts and ZIPs.
- `scripts/build_site.py --check`, `scripts/check_site.py`, `scripts/build_review_card.py --check`, `git diff --check`: PASS.
- Targeted archive/current-review tests: 37 passed.
- No new experiment, candidate raster, scientific score, organizer receipt or weekly-slot action. The requested validated unique TIFF remains **unfulfilled**, explicitly, rather than being falsely represented as delivered.
