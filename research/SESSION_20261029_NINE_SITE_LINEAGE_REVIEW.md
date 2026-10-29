# Nine-site review, lineage check and submission decision — 2026-10-29 (`arena/d744540f-gemsdoe86`)

## Decision (read this first)

| Question | Answer |
|---|---|
| Is any file OK to **submit** today? | **NO — DO NOT SUBMIT.** No file has an organizer receipt. Every nine-site best file is non-unique against the other eight. The repository's literal uniqueness gate is unsatisfiable (see §4). |
| Can I **download** the nine best files? | **Yes, for review and audit only.** Each is an owner-published raster; links are in the table in §1. Downloading does not authorize upload. |
| Did I generate a new unique TIF? | **No.** The binding stop in `docs/evidence/protocol-preflight.json` (`STOP_LITERAL_OVERLAP_UNSATISFIABLE`) and the standing rule in `PROMPT.md` ("do not generate a TIFF … while this stop applies") prohibit it. No holdout could run either (native features and shared cache are missing). A file labelled "unique" here would be false. |
| Is any number an **estimate**? | The only numbers are **OWNER-REPORTED** scores (no organizer receipt). No projection or holdout estimate is claimed for any file. |
| Does anything beat 0.2778? | **Not demonstrated.** See §3. |

Owner-reported scores are not leaderboard results. The prompt quotes two different leaderboard maxima, **0.3195** and **0.4413**, and I could not verify either (§6, IR-86-20261029-04).

---

## 1. Executive summary table — the nine listed sites

Sorted by owner-reported score. Links point to each owner repository's `docs/downloads/` file on GitHub (download with the "Raw" button). Overlap is the share of the row file's dots that sit within 3 px of the column file's dots (`dot_overlap`, shared `gems57.uniqueness`). The *max* column is the largest such value against any of the other eight sites.

| Rank | Site | File to download (owner repo, HEAD) | Owner-reported score | Estimate | Dots | Unique vs the other 8 listed sites? | Duplicate of a previous submission? | Decision |
|---:|---|---|---:|---|---:|---|---|---|
| 1 | GEMSDOE32 | [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/HEAD/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) · sha256 `c55bafc4…` | 0.2778 | none — owner number only | 37,654 | **NO** — max 1.000 (vs 36, 31, 30, 25, 27, 24); 0.999 vs 28 | **YES** — its own previously reported bytes | DO NOT SUBMIT |
| 2 | GEMSDOE36 | [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/HEAD/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) · sha256 `e1589102…` | 0.2750 | none | 38,854 | **NO** — max 0.976 (vs 27) | **YES** | DO NOT SUBMIT |
| 3 | GEMSDOE28 | [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/HEAD/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) · sha256 `7c74270a…` | 0.2710 | none | 37,660 | **NO** — max 1.000 (vs 25, 30, 27, 24) | **YES** (owner name ends `-nan`; see IR-86-20261029-02) | DO NOT SUBMIT |
| 4 | GEMSDOE31 | [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/HEAD/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) · sha256 `acd85393…` | 0.2708 | none | 40,199 | **NO** — max 1.000 (vs 25, 30, 27, 24) | **YES** (owner name `-nan`) | DO NOT SUBMIT |
| 5 | GEMSDOE33 | [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/HEAD/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) · sha256 `87f857d5…` | 0.2632 | none | 41,865 | **NO** — max 0.997 (vs 25, 30, 27, 24) | **YES** | DO NOT SUBMIT |
| 6 | GEMSDOE25 | [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/HEAD/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) · sha256 `3e78737f…` | 0.2600 | none | 44,090 | **NO** — max 1.000 (vs 30, 27, 24) | **YES** (owner name `-nan`) | DO NOT SUBMIT |
| 7 | GEMSDOE30 | [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/HEAD/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) · sha256 `8cf893ea…` | 0.2600 | none | 44,090 | **NO** — max 1.000 (vs 25, 27, 24) | **YES** | DO NOT SUBMIT |
| 8 | GEMSDOE24 | [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/HEAD/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif) · sha256 `3e0730e8…` | 0.2477 | none | 60,069 | **NO** — max 1.000 (vs 25, 30, 27) | **YES** (owner name `-nan`) | DO NOT SUBMIT |
| 9 | GEMSDOE27 | [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/HEAD/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) · sha256 `a9bf76b5…` | 0.2449 | none | 61,328 | **NO** — max 0.980 (vs 25, 30, 24) | **YES** (owner name `-nan`) | DO NOT SUBMIT |

**What "verified" means here.** All nine SHA-256 values were recomputed from the owner repositories' current HEAD tarballs (fetched from `codeload.github.com`) and match the values in `docs/evidence/nine-site-audit-20261027.json`. For each site, a NaN-encoded sibling file exists in the owner's tree with the same dot field as the audited file; the two differ only in NaN versus zero outside the footprint (`variant_identity_checks` in the evidence file). For five sites the owner's submission name ends in `-nan` while the audited file is the zeros/allfinite form. The 72 ordered pairs all exceed 0.70 (range 0.8672–1.0000). Per-pair values: `docs/evidence/nine-site-lineage-20261029.json`.

**Estimate column.** I did not produce an estimate. The owner number is the only number I can attribute. A holdout-based estimate needs the restored feature stack and shared cache, and both are absent (`scripts/audit_workspace_inputs.py`). The dot-count relation in §3 is a pattern, not an estimate.

---

## 2. Why H33 (0.2778) ranks first — measured, not assumed

**The file is a pruned sibling, not a new model.** Measured on the bytes:

- H33 (37,654 dots) is a **strict subset** of the GEMSDOE31 raster (40,199 dots, owner-reported 0.2708). Zero dots were added.
- The 2,545 removed dots sit at catalogue distance **1.4142 px (1,201 dots)** or **2.0000 px (1,344 dots)** — i.e. the catalogue collar. None were on the catalogue.
- The owner-reported difference is **+0.0070** (0.2778 − 0.2708). That is the only measured effect; it is a single owner-reported delta with no receipt.

**Why the collar edit could raise the score (mechanism, from the repository's metric transcription).** `vendor/gems57/metric.py` transcribes the official DTI as `TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)` with a 300 m triangular kernel. A predicted dot adds to FP in proportion to `1 − max kernel credit`. A dot with no kernel credit adds a full 0.2 to the denominator and earns nothing. Removing dots that earn no credit therefore raises DTI with no loss of truth credit. The same alpha/beta values (0.2 and 0.8) appear in the DrivenData reference notebook (`unet-mc-cv-reference-solution.ipynb`, cell 16) as **Tversky training-loss** weights, not as the scoring metric: https://github.com/drivendataorg/gems-prize-reference-solution.

**Caveat.** Whether the collar dots earned credit depends on where the truth faults lie, which is not available here. The owner's +0.0070 says the net effect was positive for this edit. It does not identify which geology drove it.

**Dot count and score across the nine (correlation, not causation).** Spearman ρ = **−0.983** (n = 9, p ≈ 2×10⁻⁶) between dot count and owner-reported score. Scores fall from 0.278 at ~38k dots to 0.245 at ~61k. The sample is small, the scores are unverified, and the sites use different generators, so I do not read this as a causal law. It is consistent with the metric's penalty on zero-credit dots.

---

## 3. Can we exceed 0.2778? — the honest answer

**Not demonstrated, and not reachable under the rules as written.**

1. **Pruning H33 further** would likely move the owner-reported number only if the removed dots earn no credit. But a pure subset of H33 has overlap **1.000** with H33 (and with GEMSDOE31). It cannot be unique under the 0.70 rule, and it is an exact-duplicate family. It is therefore not a valid submission under your uniqueness requirement.
2. **A unique improvement** would have to move dots away from every registry raster and still earn credit. Judging whether a new dot earns credit requires a validated holdout. That holdout needs the native feature stack (`training_features.tif`), the prepared arrays and the shared cache. None are present, and the repository's protocol blocks candidate construction while the literal stop applies (§4).
3. **Prior lanes** in this repository (H86-series, including H86S-DWAD and H86T-KNDS) tried this with holdout and uniqueness checks. Each recorded a negative or audit-only verdict (`README.md`, `docs/executive-summary.html`).

---

## 4. The blocker: one representation rule, and the decision it needs from you

`docs/evidence/protocol-preflight.json` (re-measured 2026-10-28) reports that the pinned 17GEMSDOE witness is a continuous probability surface, positive on **all 5,167,373 footprint cells**. The inherited rule defines a raster's "dots" as **every positive finite cell**. Under that definition, every nonempty candidate has overlap **1.0**, so the 0.70 gate fails for any candidate, whatever its geology. The repository says this explicitly (`vendor/gems57/uniqueness.py`, `saturation_certificate`).

I measured the same witness under a **diagnostic** alternative, the top-37,654 cells of the surface treated as dots. Results (`docs/evidence/nine-site-lineage-20261029.json`, `witness.topK_diagnostic`):

| Owner file | My dots within 3 px of witness top-37,654 (forward) | Witness top-37,654 within 3 px of my dots (reverse) |
|---|---:|---:|
| GEMSDOE32 H33 | 0.0366 | 0.3103 |
| GEMSDOE31 | 0.0495 | 0.4596 |
| GEMSDOE36 | 0.0356 | 0.3118 |

This is **not a gate, not a clearance and not a candidate test.** It shows that the stop is driven by the choice to count every surface cell as a dot. The repository's own docstring calls this the "universal overlap blocker". Changing the rule would require an explicit owner decision and a written amendment. I did not make that change.

**Decision needed from the owner (one question):** Should a continuous registry surface be represented as dots? Options:

- **(a)** Keep the literal rule. Then no candidate can be unique against the 17GEMSDOE witness, and the uniqueness requirement cannot be met for any file.
- **(b)** Adopt a written top-K representation (K = the count-fixed budget, here 37,654), with the rule, K and the ties policy pre-registered before any candidate is built.
- **(c)** Exclude continuous surfaces from the dot-overlap gate and apply the rank-correlation (`rho ≤ 0.90`) test to them instead. The repository already classifies rasters as `continuous_surface` or `dot_field` (`vendor/gems57/uniqueness.py::representation_class`), but the owner has not adopted that classification as the gate.

Whichever option is chosen, a candidate still needs a validated holdout and a full-registry check before it can be called unique.

---

## 5. What is needed to produce a unique, validated TIF (ranked)

1. **Owner decision** on the representation rule (§4).
2. **Restore the native feature stack** with `scripts/restore_data.py` (codeload mirror, hash-pinned) and verify with `scripts/audit_workspace_inputs.py --require-native`.
3. **Build the shared feature cache** under the repository's protocol (`SHARED_CACHE_NOT_ESTABLISHED` today).
4. **Run a preregistered holdout** (`gems57-pooled-hide-v2`, spatially blocked), with a leakage canary (AUC above 0.90 means leakage), against the H33 holdout baseline. Report HOLDOUT-DTI with its CI and withheld count.
5. **Full-registry uniqueness** (`scripts/restore_registry_inventory.py`), not the nine-file subset.
6. **Format validation** of the written TIFF (EPSG:32611, 3730×3292, the pinned transform, values in [0,1], no NaN or Inf in the footprint, zero outside, dots not on the catalogue).
7. **Owner-run submission** with a receipt logged in `ledger/submissions.csv`. Only then should `safe_to_submit` change.

Items 2–3 can run in this sandbox (the codeload host is allowlisted). Items 1 and 7 need you.

---

## 6. Irregularities for review

See `IRREGULARITIES.md`, entries **IR-86-20261029-01 … 06**. Summary:

- **01** Literal witness stop vs top-K diagnostic (owner decision, §4).
- **02** Owner-named `-nan` siblings vs audited `-allfinite` / `-zeros` files. Dot fields are identical; they differ only in NaN outside the footprint. The bytes the portal scored are not determinable from the repository.
- **03** H33 is a pure collar subset of GEMSDOE31. Any prune of it is non-unique by construction.
- **04** Conflicting leaderboard maxima (0.3195 and 0.4413) in the prompt, and no verification route: DrivenData is not accessed by automated tools (`AGENTS.md` rule 9), and `buffedlizard55-lab.github.io` is not on this sandbox's egress allowlist. I used the GitHub repositories instead.
- **05** Owner repositories have advanced since the listing: several HEAD trees contain files dated 2026-10-28 with no owner score (for example `GEMSDOE31` `gems31-h31cc-basement-step-37654d-20261028`). Those are not ranked here.
- **06** The dot-count/score relation (ρ = −0.983, n = 9) is correlational and uses unverified scores.

---

## 7. Verification trail (line by line)

| Step | What was checked | Result | Evidence |
|---|---|---|---|
| S1 | Nine owner tarballs fetched from `codeload.github.com/buffedlizard55-lab/<repo>/tar.gz/HEAD` (allowlisted host) | 9/9 fetched | `.cache/nine_site/` (git-ignored) |
| S2 | SHA-256 of each audited file vs `nine-site-audit-20261027.json` | 9/9 match | `nine_site_files[].sha256_matches_audit` |
| S3 | Grid (EPSG:32611, 3730×3292, transform) of each file | 9/9 match reference grid | `grid_matches_reference` |
| S4 | Dots on catalogue / outside footprint / NaN / Inf | 0 / 0 / 0 / 0 for all nine (audited forms) | `nine_site_files[]` |
| S5 | 9×9 forward overlap with shared `dot_overlap` | 72/72 > 0.70; min 0.8672, max 1.0000 | `pairwise_*` |
| S6 | Owner-named `-nan`/`-zeros` siblings vs audited form | dot fields identical for all 9 | `variant_identity_checks` |
| S7 | H33 vs GEMSDOE31 subset test and removed-dot geometry | subset True; 2,545 removed; 0 added; distances 1.4142 / 2.0 px | `h33_lineage` |
| S8 | Witness SHA-256 vs `research/registry_witness_pin.json` | match `ab0a0a62…` | `witness.pinned_sha256_matches` |
| S9 | Metric and weights vs DrivenData reference notebook | alpha 0.2 / beta 0.8 match the notebook; kernel and DTI form from `vendor/gems57/metric.py` (repository transcription of the official page; the official page itself was not fetched) | §2 |
| S10 | Test suite | see §8 | §8 |

Scripts: `scripts/verify_nine_site_lineage.py` (re-runs S1–S8; `--offline` uses the cache). Tests: `tests/test_nine_site_lineage.py`. Run card: `research/run_cards/nine_site_lineage_20261029.json`.

---

## 8. Test and audit results

Results of this session's final run (re-run to reproduce):

| Check | Command | Result |
|---|---|---|
| Full test suite | `.venv/bin/python -m pytest -q -p no:cacheprovider` | 1172 passed, 24 skipped, 0 failed (10 min run, after merging `origin/main` at 7937768 — PR #214 — into this branch) |
| Release audit (re-measured registry) | `scripts/audit_release.py --measure-registry` | PASS: 50 of 50 artifacts valid; DO NOT SUBMIT; 0 experiments, 0 slots |
| Site build | `scripts/build_site.py --check` | PASS |
| Pages check | `scripts/check_site.py` | PASS |
| Download audit | `scripts/audit_downloads.py` | PASS: 50 research TIFFs and receipts revalidated; no selector decision |
| Lineage script | `scripts/verify_nine_site_lineage.py --offline` | PASS: 9/9 SHA-256; 72/72 pairs > 0.70 |

The protocol witness was restored with `scripts/restore_protocol_data.py --include-registry` (SHA-256 verified against `research/registry_witness_pin.json`). The grid templates were verified against their integrity pins, and both are non-authenticated owner mirrors.

---

## 9. Hypotheses (3–5 untried, ranked; no new geology invented this session)

No new hypothesis was added this session, because no new data were restored and an untested idea would be speculation. The screened register `registry/focus9_novel_hypotheses_20261028.json` already holds three ideas, all `PROPOSED_NOT_RUN`:

1. **F9N-1 Lake Lahontan shoreline displacement** as an independent paleogeodetic datum (high cost; needs 1 m USGS 3DEP tiles and mapped shoreline geometry).
2. **F9N-2 ComCat earthquake-sequence migration** along blind fault planes (very high cost; sparse coverage).
3. **F9N-3 Age-tagged geologic-unit contact termination and offset graph** (high cost; needs attributed NGMDB or state map polygons).

Ranking is qualitative, not a DTI estimate. None can be validated until §5 items 1–4 are done.

---

## 10. Limitations

- No organizer receipts exist for any score in this repository.
- No live leaderboard access: DrivenData is excluded from automated access (`AGENTS.md` rule 9).
- The owner `github.io` pages are not reachable from this sandbox; repository trees on `github.com` were used instead.
- Holdout DTI cannot be computed here (features and cache absent).
- The nine-file overlap is not full-registry uniqueness. Registry denominators differ across the repository's own notes (690 indexed files; 688/690 compatible rasters in the H86-I lane; 702/704 valid-grid rasters in the H86M lane). They were not reconciled this session, and none was measured here.
- The mechanism in §2 is inferred from the metric transcription and one owner-reported delta.

## 11. Next steps (ranked by what unblocks the most)

1. Owner decision on the representation rule (§4). This is the single item that changes the answer.
2. Restore native inputs and the shared cache (§5, 2–3).
3. Run a preregistered holdout against H33 (§5, 4), and only then consider a candidate.
4. Run the full-registry scan (§5, 5).
5. ~~Render the lineage evidence into the executive page.~~ Done: `docs/nine-site-summary.html` is generated from the 2026-10-29 lineage JSON; `docs/nine-sites.html` links to it, and its own body still reflects the 2026-10-27 evidence.

## 12. Three-pass review

- **Pass 1 (implement and verify):** script, evidence JSON, tests, run card. Verified against the owner bytes.
- **Pass 2 (bugs, assumptions):** I checked the overlap direction (row = my dots near column) against the earlier independent recomputation; the sibling-file search was checked against the owner-named suffixes; the witness diagnostic was labelled as a diagnostic in the code, the JSON and this document. One misleading variable name was renamed.
- **Pass 3 (requirements):** the request asked for a unique TIF. That conflicts with the standing stop, so no TIF was produced; the conflict is stated at the top. Every number above traces to a file in the repository or to a fetched owner tree.
