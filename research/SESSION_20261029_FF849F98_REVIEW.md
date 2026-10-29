# Session review — 2026-10-29 · branch `arena/ff849f98-gemsdoe86`

**DECISION: DO NOT SUBMIT.** No new TIFF was generated. No holdout, canary, or model experiment was run. **0 of 3** experiments and **0 weekly slots** were used. The reason is written below, and it is not a formatting issue.

## 1. Why there is no new unique TIFF in this session

I did not generate a new TIFF. Three independent blockers apply, and each one is sufficient on its own:

1. **The literal uniqueness gate cannot be satisfied for any nonempty dot set.** I reproduced this from bytes (section 3). The pinned owner witness `17GEMSDOE` has positive finite values on all 5,106,385 allowed footprint pixels. Under the repo's inherited rule (`finite prediction > 0`, 3-px forward overlap, limit 0.70), every nonempty candidate therefore has overlap **1.0**. The rule is binding (`AGENTS.md` rule 6). I did not change it, add a bypass, or set a private threshold.
2. **The model cannot be trained or scored here.** `training_features.tif` is **MISSING** from both `data/` and `data/bridge/`, per `scripts/audit_workspace_inputs.py` (`usable: false`). Without the feature stack I cannot run a holdout DTI, a leakage canary, or an organizer-score estimate. A file produced without those steps would have no basis for a score claim.
3. **Submission requires a human.** Upload uses a weekly slot on the DrivenData submission page, and this repo's rules keep that action with a human. No organizer receipt or quota is available to me.

Consequence: I cannot honestly say that any file will beat 0.2778, that it is unique, or what its score would be. A file generated now would have to be labelled **DO NOT SUBMIT**. The owner's request for a unique TIFF that is obviously safe to submit cannot be met until the owner makes a decision (section 7).

## 2. Executive table — the nine requested sites

The download files are the immutable, commit-pinned files listed in [`docs/evidence/focus9-immutable-files-20261029.json`](../docs/evidence/focus9-immutable-files-20261029.json). Each one's SHA-256 and byte size were re-verified in this session. "Max forward overlap" is measured against the other eight site files, using the 3-px rule (section 3). A value above 0.70 means **not unique** under the gate.

| Site | File to download (commit-pinned) | Owner-reported score | Estimated organizer score | Max fwd overlap vs peers | Unique? | OK to submit? |
|---|---|---|---|---|---|---|
| GEMSDOE24 | [gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/f4d5a5ef3f3cf6cbe5a24ee0b29c6d592910d308/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif) | 0.2477 | **not estimable** | 1.0000 | **NO** | **NO** |
| GEMSDOE25 | [gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/889d93dcde5bbc5812b2d68c5de830a8d8dc61a1/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) | 0.2600 | **not estimable** | 1.0000 | **NO** | **NO** |
| GEMSDOE27 | [gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/8e4979ea0af2796e30d1947b1821ba170d365d9d/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) | 0.2449 | **not estimable** | 0.9802 | **NO** | **NO** |
| GEMSDOE28 | [gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/425d92738532efaaae959db85e833ea1d1f23f1c/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) | 0.2710 | **not estimable** | 1.0000 | **NO** | **NO** |
| GEMSDOE30 | [gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/48935645078d2363a6d8feccb7bd9323b7d88a2b/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | 0.2600 | **not estimable** | 1.0000 | **NO** | **NO** |
| GEMSDOE31 | [gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/703fe7282d10596cedc8e54a68992ce86cc4dd43/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) | 0.2708 | **not estimable** | 1.0000 | **NO** | **NO** |
| **GEMSDOE32** | [gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/22d1d9efbebc0c0f2cf29d76cfd765edf61a19ea/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | **0.2778** (highest of the nine) | **not estimable** | 1.0000 | **NO** | **NO** |
| GEMSDOE33 | [GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/3eaf85efb49f364b84f8be04e8b084b12d0303b9/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | 0.2632 | **not estimable** | 0.9971 | **NO** | **NO** |
| GEMSDOE36 | [gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/e280188adbbe762e6b7ac6f3b8e105e8e7915026/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | 0.2750 | **not estimable** | 0.9758 | **NO** | **NO** |

**Best file to consider (for review only): GEMSDOE32 H33 (0.2778, owner-reported).** It is the highest owner-reported score among the nine sites. It is **not unique** (overlap 1.0 against peers) and it is **not cleared** to submit. Its score is unverified; no organizer receipt exists.

Column notes:
- **Estimated organizer score: not estimable.** No holdout evaluator run is possible (section 1, blocker 2). Writing a number here would be a projection presented as a score, which the repo forbids.
- **Owner-reported score** is copied from the owner's page and [`registry/prior_scores.csv`](../registry/prior_scores.csv). It is `OWNER-REPORTED`, not `ORGANIZER-CONFIRMED`.
- **Encoding caveat.** The owner's list names several `-nan` or `-allfinite` variants. The table links the immutable receipt file for each site. For GEMSDOE25 the receipt file is the `-zeros` variant, and for GEMSDOE24, 27, 28, 31 it is `-allfinite`. For GEMSDOE28 H36-1 the local `-nan` copy has SHA-256 `5556aa14…`, which differs from the receipt's `7c74270a…`. I did not treat this as a mismatch; it is a different encoding of the same dot field. Section 6 lists it for review.

## 3. Verified in this session (commands and measured results)

All commands ran in this checkout with the pinned environment (`requirements-lock.txt`, numpy 2.4.6, rasterio 1.4.4).

| # | Check | Command / source | Result |
|---|---|---|---|
| V1 | Witness fetched from owner blob, SHA-256 checked | `curl https://api.github.com/repos/buffedlizard55-lab/17GEMSDOE/git/blobs/374c88b1da2b803e2ed160de467fd71ae114010d` (the pin's blob, verified against [`research/registry_witness_pin.json`](../research/registry_witness_pin.json)) | `ab0a0a62…3872be`, 25,065,181 bytes — **matches pin** |
| V2 | Literal uniqueness stop reproduced | `scripts/protocol_preflight.py` | `STOP_LITERAL_OVERLAP_UNSATISFIABLE`; `uncovered_allowed_pixels = 0`; `covered_allowed_fraction = 1.0`; `candidate_generated = false` |
| V3 | Training inputs | `scripts/audit_workspace_inputs.py` | `training_features.tif` **MISSING** (both paths); `existing_faults.tif` and `sample_submission.tif` HASH_VERIFIED in `data/bridge/` |
| V4 | Nine immutable files: bytes and SHA-256 | `scripts/focus9_overlap_matrix.py` (fetches each file by git blob SHA, hard-stops on mismatch) | All nine **match** the receipt's SHA-256 and byte size |
| V5 | 3-px overlap matrix (nine × nine) | same script → [`docs/evidence/session-ff849f98-nine-site-overlap.json`](../docs/evidence/session-ff849f98-nine-site-overlap.json) | Every site's file exceeds 0.70 against at least one peer (table §2) |
| V6 | Format of local H33 / H36 / H33-d / H27-4 copies | `rasterio` read, compared with `data/bridge/sample_submission.tif` | EPSG:32611, shape (3730, 3292), same transform as the sample, float32, one band, values in {0, 1}, **no value outside [0, 1]** |
| V7 | H33 is a strict subset of GEMSDOE28 H27-4 | pixel-exact comparison of `data/scored_fleet` copies | H33 has **37,654** dots; H27-4 has **40,199**; **H33 ⊂ H27-4** (0 H33 dots outside H27-4); **2,545** H27-4 dots removed |
| V8 | DTI formula | [`vendor/gems57/metric.py`](../vendor/gems57/metric.py), lines 10–19 | `DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)`, triangular kernel `max(1 − d/R, 0)` with R = 3 px (300 m) |

Reproduce: `.venv/bin/python scripts/focus9_overlap_matrix.py`, then `.venv/bin/python scripts/protocol_preflight.py` after placing the pinned witness in `data/bridge/registry/` (git-ignored; I removed my copy after use).

## 4. Why GEMSDOE32 H33 (0.2778) scored highest — technical reading

What is measured here, and what is not.

- **Measured (V7).** H33 is H27-4 with 2,545 dots removed and none added. That is all I measured about the removal.
- **Owner's description, not re-measured here.** The repo's prior analysis ([`README.md`](../README.md), 2026-10-25 H33 note) says the removed dots were catalogue-collar dots at 1.41–2.00 px and that H27-4 used Poisson-disc spacing of √8 px. I did not re-verify these distances or the spacing rule.
- **Mechanism implied by the metric (V8).** Under `DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)`, a dot adds false-positive mass in proportion to its non-covered extent. A dot whose kernel credit is low, and which lies close to already-known faults, adds FP mass without adding much TP credit. Removing it can raise DTI. The repo's marginal rule says a dot helps only when its realised credit exceeds `α·DTI ≈ 0.2 × DTI` (see `marginal_accept` in `metric.py`). This is a plausible explanation, not a verified cause.
- **Not verified.** I have **no same-split causal test** that ties the 2,545 removed dots to the 0.2778 score. The score itself is an owner claim with no organizer receipt. The repo's earlier review (`H33_INTERPRETATION_REVIEW.md`) reaches the same conclusion.
- **Caveat on the metric docstring.** The repo's own review found that the shared module's docstring says `dT ≤ k` for marginal credit. A three-cell counterexample shows that bound does not hold in general (`dT = 7/3 > 1 = k`). The `marginal_accept` function itself agrees with brute-force checks. This matters for the "marginal credit" argument above, so I did not rely on the docstring.

**Can a submission beat 0.2778?** Unknown, and not testable in this checkout. Any further subset of H33 is contained in H33, so it inherits the same overlap of 1.0 and cannot be unique. Beating 0.2778 would require a new dot field that is both unique and scores better on the holdout. The holdout cannot be run until `training_features.tif` is available.

## 5. Owner leaderboard values — conflicting and unverified

- The request names **0.4413** and **0.3195** as the current GEMSDOE high. They conflict with each other, and neither is recorded in the ledger. `IR-86-20261029-04` already records this.
- I did not query DrivenData. The repo's rules forbid automated access to drivendata.org. Human check: <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>.

## 6. Irregularities flagged for review

1. **`Predicted values must be in range [0, 1]` is not reproducible from the local copies.** Every local copy I read (V6) has values only in {0, 1}, and the receipt files match their pinned SHA-256. The error text suggests a different file was uploaded, possibly a `-nan` variant, a file with a nodata sentinel, or a zipped copy. **To diagnose, the owner must supply the exact file name uploaded and its download link.** I cannot diagnose a file I have not seen.
2. **Two leaderboard values conflict** (0.4413 vs 0.3195; section 5).
3. **GEMSDOE92 value differs between requests.** The request text in this session lists `0.0255`. An earlier session's request text reported `0.2784`. I could not find `0.2784` in `registry/prior_scores.csv` or in the README's GEMSDOE92 entries. Treat both as unverified.
4. **Encoding ambiguity (section 2).** The owner's `-nan` / `-allfinite` / `-zeros` labels do not map one-to-one onto the receipt files. Score equivalence between these encodings is unknown.
5. **`scripts/protocol_preflight.py` rewrote a tracked evidence file.** Running it updated `docs/evidence/protocol-preflight.json`, changing only `measured_utc`. I restored the file from git. The verdict did not change. The script's side effect on a tracked artifact should be reviewed.
6. **The owner witness is a third-party owner prediction** (`17GEMSDOE`, `source_class: owner historical prediction, not official training data`). It is a valid counterexample for the literal rule, not a registry-wide measurement (`registry_complete: false`).
7. **Native training data is absent from this checkout.** Restoring `training_features.tif` needs the owner mirror (see `scripts/restore_data.py`). Restoring it does not establish the shared derived cache (`AGENTS.md` rule 5).

## 7. Decision needed from the owner (blocks any unique submission)

**Question A — uniqueness definition.** Should a *continuous probability surface* (like the 17GEMSDOE witness) count as a dot field under the 0.70 rule?
- If **yes**, the literal gate stays and the stop stands.
- If **no**, the owner must set a documented rule for continuous surfaces (for example, top-K dots). That is a protocol amendment, not a silent change. The repo has a diagnostic (`top-K`), but it is not adopted (`IR-86-20261029-01`).

**Question B — training data.** Provide access to `training_features.tif` (owner mirror or official source) so a holdout and canary can run.

**Question C — the rejected upload.** Provide the exact file name and link that returned `Predicted values must be in range [0, 1]`.

Without A and B, no candidate can be validated. Without C, the `[0, 1]` error cannot be diagnosed.

## 8. Hypotheses (3–5 candidates, ranked; none validated)

The repo's pre-existing qualitative register ([`registry/focus9_novel_hypotheses_20261028.json`](../registry/focus9_novel_hypotheses_20261028.json)) already lists three untried ideas. I did not add new ones this session: without the training features, I could not validate any of them, and an unvalidated idea cannot be ranked by expected DTI gain.

| Rank | Signature and layers | Why it could find a missing fault | Status and blocker |
|---|---|---|---|
| 1 | Repeated displacement of age-matched Pleistocene Lake Lahontan shorelines in USGS 3DEP 1 m DEM | A covered scarp may offset a dated shoreline | Not run. Needs age-tagged shoreline geometry and AOI tiles; neither obtained. Sources: <https://www.usgs.gov/3d-elevation-program>, <https://ngmdb.usgs.gov/> |
| 2 | Time-ordered, quality-filtered earthquake sequences along a candidate corridor (ComCat) | Coherent migration could reveal a blind structure | Not run. Needs event time series and completeness control. Source: <https://earthquake.usgs.gov/fdsnws/event/1/> |
| 3 | Age- and lithology-attributed geologic contacts on both sides of a corridor | Offset or termination of contacts could show a fault | Not run. Needs attributed polygons with licence check. Source: <https://ngmdb.usgs.gov/> |

Ranking is qualitative. It is not a score projection. These sources were not reachable from this session's allowlist, so none has been verified.

## 9. Next steps and limitations

- **Blocked on the owner:** questions A–C above.
- **Blocked on data:** `training_features.tif` (absent). Without it, nothing can be validated.
- **Limitation of the environment:** outbound access is restricted to GitHub, npm, and PyPI. The USGS, DOE, and DrivenData sites are not reachable here, so their content is not verified in this session.
- **Next session, if A and B are resolved:** preregister one lane; run the feature canary (single-feature AUC > 0.90 means leakage); run the buffered whole-segment holdout against the same-split best; run the surface and final-dot registry checks; use a quota-aware selector for any slot.

## 10. Passes

- **Pass 1 — implement and verify.** Built the environment, reproduced the stop, checked the nine immutable files, measured the overlap matrix, and checked the H33 subset and file formats.
- **Pass 2 — review.** Caught and reverted the preflight's side effect on a tracked file. Found the GEMSDOE92 conflict, the `[0, 1]` mismatch, and the encoding ambiguity. Confirmed the metric formula from source rather than from prose.
- **Gates run:** full `pytest -q` → 1,194 passed, 24 skipped, 48 warnings, 58 subtests; `scripts/build_site.py --check` and `scripts/check_site.py` → PASS. No tracked generated file changed.
- **Pass 3 — re-check against the request.** Every requested element is covered: the executive table, the score-estimate status, the 0.2778 explanation, the hypotheses, the README prompt, the submission-guide pointer, and the blockers. The request for a unique TIFF is **not** met, and this is stated at the top. Remaining gaps are listed in section 7.

## Sources (for manual review)

- Competition: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> · data (login): <https://www.drivendata.org/competitions/306/competition-doe-gems/data/> · leaderboard: <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
- Submission format: <https://docs.nlr.gov/docs/fy26osti/96647.pdf> · CRS: <https://epsg.io/32611>
- Official reference repo: <https://github.com/drivendataorg/gems-prize-reference-solution>
- USGS GeoDAWN: <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> · DOE GDR 1391: <https://gdr.openei.org/submissions/1391> · INGENIOUS: <https://gbcge.org/current-projects/ingenious/>
- Witness pin: [`research/registry_witness_pin.json`](../research/registry_witness_pin.json) · preflight evidence: [`docs/evidence/protocol-preflight.json`](../docs/evidence/protocol-preflight.json) · run card: [`docs/evidence/session-ff849f98-run-card.json`](../docs/evidence/session-ff849f98-run-card.json)
