# Repository review — 2026-10-25 — session `0c60b079` (branch `arena/0c60b079-gemsdoe86`)

## Decision

**DO NOT SUBMIT. No new TIFF was generated, no experiment was run, and no weekly slot was used.**

This is a deliberate stop, not an omission. The two conditions the owner's protocol needs before a unique TIFF can be validated are both unmet in this sandbox, and I did not bypass either one:

1. **No feature stack, so no validated model.** The shared template feature stack and the native competition inputs are absent (`scripts/audit_workspace_inputs.py`, measured below). Without them there is no holdout (`HOLDOUT-DTI`) to score against, so any raster I wrote would be unvalidated.
2. **The uniqueness gate cannot be evaluated as written.** The literal rule ("more than 70% of your dots fall within 3 px of one registry raster's dots") assumes a sparse dot set. The official reference solution writes a dense float probability map, not dots (see Irregularities IR-A). The pinned full-support witness is also absent locally, so I could not re-measure its overlap.

A previous session (`H86E`, see `IRREGULARITIES.md` IR-86-H86E-01) bypassed the preflight to produce a file and that bypass was revoked. I did not repeat it.

## What I verified (every item was run in this session)

| Check | Command / source | Result |
|---|---|---|
| Test suite | `.venv/bin/python -m pytest -q` | **1001 passed, 24 skipped**, 0 failed (5 min 14 s). Earlier notes cite 839 tests; the count has since grown. |
| Workspace inputs | `.venv/bin/python scripts/audit_workspace_inputs.py` | `native_bands_available: false`, `shared_template_feature_stack: false`, `SHARED_CACHE_NOT_ESTABLISHED`, `safe_to_submit: false`, `approved_for_weekly_slot: false`, `new_candidate_generated: false`. |
| Format validator on the existing audit-only H86G file | `.venv/bin/python scripts/verify_submission_tif.py` | Exit 0. TIFF sha256 `ba8b731f…489e8d`; 1 band float32; EPSG:32611; 3730×3292; transform (100,0,243350,0,−100,4508550); values exactly {0,1}; 0 NaN; 55,000 positives. Validator's own note: **"DO NOT SUBMIT based on this result."** |
| Range check on every published TIFF | Python/rasterio scan of all 31 files in `docs/downloads/` | All 31: finite values in [0,1], 0 NaN, EPSG:32611, 3730×3292. **None reproduces the portal's "Predicted values must be in range [0, 1]" error.** |
| H33 dot counts | Python/rasterio on `data/scored_fleet/` | H33 (`GEMSDOE32`) has **37,654** dots; parent `GEMSDOE28` `h27-4-r1` has **40,199**. Difference **2,545**, all removed (1→0 inside footprint), **0 added**. Matches the repo's stated count. |
| H33 encoding difference | same | Parent has **7,111,787 NaN** cells outside the footprint; H33 has **0 NaN** (zeros). This is an encoding change in addition to the collar removal (see IR-B). |
| Metric definition | `vendor/template66/gems/metric.py` (repo-vendored copy) | Triangular kernel R=300 m, α=0.2, β=0.8, `DTI = TP/(TP+αFP+βFN+ε)`. **NaN predictions are treated as 0; values outside [0,1] are rejected.** So the NaN-vs-zero encoding does not change the DTI under this code. |
| Official rules | `https://docs.nlr.gov/docs/fy26osti/96647.pdf` (GEMS Prize Official Rules, Sept 2026), sections 1–3.5 read | Single GeoTIFF, single band, **100 m**, covering the whole GeoDAWN study area (§3.2). **Three submissions per week** (§3.2, §3.4). One final submission per entity, chosen before the deadline without seeing private scores (§3.4, §3.6.2). **Generative-AI use must be disclosed in the narrative** (§3.2). Training labels from INGENIOUS, DOI `10.15121/1881483` (§3.3). Rules name no human-inspection requirement for the raster; DOE makes final award decisions (§3.6.4). Appendix A and the remaining chunks were **not read** in full. |
| Official reference solution | `git clone` of `https://github.com/drivendataorg/gems-prize-reference-solution` at commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b` | Notebook writes `predicted_faults_example.tif` as a **dense float probability map** (`y_final`), with the same CRS and transform as the label file. Its data must be downloaded from the DrivenData page, which this sandbox does not do (AGENTS rule 9). |
| Sandbox reachability | `curl` to each host | `usgs.gov`, `doi.org`, `drivendata.org`, `gbcge.org`: **no response (blocked)**. `github.com`, `pypi.org`: 200. The GeoDAWN and DEM sources the rules name are therefore **not obtainable here**. |
| Format consistency | Python/rasterio | `sample_submission.tif` (the format reference in `data/bridge/`) and the parent raster both have 7,111,787 NaN cells, and `existing_faults.tif` has 7,111,787 cells at −1. All three share one footprint of **5,167,373** cells. |

Hashes (computed by script, `/tmp/hashes.json` during this session, not committed):

- H33 owner-reported 0.2778: `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`
- Parent `GEMSDOE28` `h27-4-r1` owner-reported 0.2708: `ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73`
- Format reference `data/bridge/sample_submission.tif`: `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc`
- Catalogue `data/bridge/existing_faults.tif`: `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`

## Answering the H33 question (0.2778 owner-reported)

- **Owner-reported only.** 0.2778 (H33) and 0.2708 (parent) are unverified. No organizer receipt for either is in the repo, and drivendata.org was not fetched (AGENTS rule 9).
- **Pixel-level change (verified):** H33 = parent minus 2,545 dots, all within a 2-pixel catalogue collar, with no dots added. The repo's earlier audit (`research/SESSION_20261025_ARENA_REVIEW.md`) reaches the same count.
- **Metric mechanism (conditional):** With truth-credit `T`, false-positive mass `F`, and truth count `K`, removing dots that lose credit `a` and save false-positive mass `b` improves DTI iff `T·b > a·(F + 4K + 5ε)` (derived from the vendored metric's identity `DTI = T/(0.2(T+F−M)+0.8K)`; see `metric.py` docstring). That is a sufficient explanation for a gain, not a demonstration of the cause of the owner's gain.
- **Confound not previously stated:** H33 also changes the NaN encoding (IR-B). Under the vendored metric this should not change the DTI, but that is a claim about the vendored copy, not the organizer's live evaluator. It remains unverified until an organizer receipt for an encoding-matched pair exists.
- **Verdict:** a plausible, measured pruning effect. Not established as a score driver.

## Ranked candidate hypotheses (not validated; none implemented)

The user asked for 3–5 candidate hypotheses ranked by expected improvement and cost. I can give them, but **none can be validated here**: each needs the GeoDAWN magnetic/radiometric/lidar layers or the USGS 1 m DEM, and this sandbox cannot reach either (see the reachability row above). Novelty against the repo's existing lanes is also unchecked. The repo already has many lanes (`H86*`, `GEMSDOE*`), so I have not claimed any of these is new.

| Rank | Hypothesis (layers) | Physical signature targeted | Plausible non-fault mimic | Blocked by |
|---|---|---|---|---|
| 1 | Re-run the repo's own queued **H86I-KSAD** (Rank 1 in `README.md`): kinematic basement-step + USGS χ-jump + submodular allocator | Strike-projected basement step, catalogue-independent | Pleistocene Lake Lahontan wave-cut shorelines (named in README) | Feature stack; registry halt at 71.31% overlap on 36,500-dot raster |
| 2 | Radiometric K/Th ratio anomaly along lineaments (GeoDAWN radiometric bands) | Potassium enrichment and Th depletion in hydrothermally altered fault zones | Soil moisture, playa salts, vegetation cover, lithology contacts | Radiometric bands in the restored stack (absent) |
| 3 | Magnetic total-field low (demagnetised alteration) coincident with DEM scarps (GeoDAWN TMI + 1 m DEM) | Magnetic low where hydrothermal alteration destroys magnetite, aligned with a scarp | Igneous intrusions with remanence, topographic lows, cultural features | Restored stack and USGS DEM (unreachable) |

These candidates are ordered by how well they target a fault-specific signature. Expected DTI improvement is **not estimated** because no holdout exists to measure it. Rank 1 is already frozen in the repo's preregistration.

## Irregularities for review

- **IR-A — Gate semantics for dense rasters.** The official reference writes a dense probability map. The repo's literal overlap rule (70% of "dots" within 3 px) is undefined for a dense map, and against the full-support witness it evaluates to 1.0 for any nonempty allowed raster, which makes every candidate unsatisfiable. This is a policy decision for the owner, not for this session. Its resolution needs a written amendment that defines the dot set for dense rasters (for example, thresholding or top-K cells) with the holdout held fixed.
- **IR-B — H33 vs parent encoding.** The H33 "zeros" file and its `-nan` parent differ in 7,111,787 outside-footprint cells, in addition to the 2,545-dot removal. The vendored metric treats NaN as 0, so the encoding should be neutral there. The repo's `IR-86-PRUNE-07` discusses the NaN/zeros convention but not this pair specifically.
- **IR-C — The portal error "Predicted values must be in range [0, 1]".** None of the 31 published TIFFs reproduces it (table above). The two reference rasters use out-of-footprint sentinels: `existing_faults.tif` uses **−1**, and `sample_submission.tif` uses **NaN**. The most likely cause is a file derived directly from the −1 catalogue. **This is a hypothesis.** It cannot be confirmed without the filename that was uploaded, and that filename is requested below.
- **IR-D — Inconsistent leaderboard claims.** The request cites a current GEMSDOE best of 0.4413 and also 0.3195 as the highest score. Both are owner-supplied and unverified. I could not check the DrivenData leaderboard (AGENTS rule 9). Treat both as unverified.
- **IR-E — Witness not local.** `registry/dense-witness.tif` is pinned in `research/registry_witness_pin.json` but is absent from this checkout, so the "1.0 overlap" measurement could not be re-run here. It is recorded in the repo's prior receipts, not re-measured.
- **IR-F — Eligibility and AI disclosure (user action).** The rules require the signer to certify eligibility (§1.3), and the narrative must state the extent of generative-AI use (§3.2). Both are the user's to complete, and this repo's work is AI-assisted.
- **IR-G — Hosts not reachable.** The rules' DEM and GeoDAWN sources, the DOI, and DrivenData are unreachable from this sandbox (table above). Any hypothesis that depends on them is blocked here.

## What is needed to produce a validated, unique TIFF

1. **Feature stack placement (user action).** Download the competition training features and labels from the DrivenData data page (a logged-in browser action, which this sandbox cannot do) and place them at the paths `scripts/audit_workspace_inputs.py` checks. Then re-run the audit. Until `native_bands_available` is `true` and the shared-cache receipt is valid, no HOLDOUT-DTI can be produced.
2. **Gate amendment (owner decision).** Decide the dot-set definition for dense rasters (IR-A) in writing. Without this, every nonempty candidate is blocked.
3. **Filename of the file that gave the [0,1] error (user action, IR-C).** This would confirm or rule out the −1 sentinel as the cause.
4. **Re-measure the witness** once `registry/dense-witness.tif` is restored (IR-E).
5. **Only then** run one lane through `evaluate_holdout` with a leakage canary, a like-for-like control, and the registry check. Submission remains a separate, human-chosen step, within the 3-per-week cap (§3.2).

## Machine-readable card

See `research/session-0c60b079-run-card.json`.

## Post-merge verification (main moved during this session)

Main gained PR #150 (H86L-FMC, `9a76c23`/`0c05e70`) while this branch was open, and the merge conflicted in `README.md` and `IRREGULARITIES.md`. Both sides were kept in full. After the merge:

| Gate | Result on this branch | Result on `origin/main` (clean worktree) |
|---|---|---|
| `scripts/check_site.py` | EXIT 1: `Unregistered downloadable raster/archive: docs/downloads/gems86-h86l-fmc-minconsensus-37654dots-20261025T161053Z-zeros.{tif,zip}` | EXIT 1, same two lines |
| `scripts/build_site.py --check` | EXIT 1: `ValueError: Unregistered or missing published TIFF` | EXIT 1, same error |
| `pytest -q` | 16 failed, 985 passed, 24 skipped (10 failures in `tests/test_release_audit.py`) | 16 failed, 985 passed, 24 skipped |
| `scripts/verify_submission_tif.py` (H86G) | EXIT 0 | not run |
| `scripts/audit_release.py` | EXIT 1: `ValueError: Unregistered or missing published TIFF` | EXIT 1, same error |

The failures are inherited from main. This session's changes are documentation only and do not change any test input. The H86L lane's runner (`scripts/run_h86l_fmc.py`) writes its run card but does not register its TIFF in `download-inventory.json` or `registry/artifact_cards.json`. Adding those records would be governance data for another lane's artifact, and `audit_release.py` would then have to measure it against the witness. I did not write them. This is listed as IR-H for the H86L owner.

Note on exit codes: an earlier check used `| tail` and `${PIPESTATUS[0]}` inside a subshell. That read the wrong exit status and printed `EXIT 0` for a failing build. The corrected, unpiped runs above are the authoritative results.
