# Session review: 2026-10-25, H86J-LLP (three passes)

**Branch:** `arena/bbf7b2c0-gemsdoe86` · **Request:** consistent with the archived
[`REQUEST_20261025.md`](REQUEST_20261025.md). It contains the same 0.4413/0.3195 claims, the same
portal error and the same executive-summary requirements, so no new archive was written.
**Outcome:** the session generated a new unique TIFF, and the automated gate says **DO NOT SUBMIT**.
0 slots used.

## What was done

**1. Data restored, all SHA-256-verified:**
- the 19-band feature TIFF (419 MB);
- the 5 external grids and the registry witness;
- all 655 registry blobs (728 MB);
- 39 newer scored fleet rasters via codeload, because the REST quota was exhausted (IR-86-API-QUOTA).

**2. Lane H86J-LLP** was preregistered before any fit (5 ranked hypotheses; amendments A1–A5). It
ran exactly three experiments, all within the 2 h budget:
- **E0/E1:** fleet assembly (102 rasters), leakage canary (max 0.8044), and an LLP fit with LOSO CV:
  Spearman 0.855, accepted.
- **E2:** protocol holdout. Candidate 0.0370 vs HGB 0.1373 and random 0.0475, so **negative**.
- **E3:** final 44,090-dot TIFF. Uniqueness was measured against 737 rasters (re-measured after merging main); then the shared
  writer and validator ran, followed by the gate.

**3. A single automated gate** ([`scripts/submission_gate.py`](../scripts/submission_gate.py)). It
prints exactly one of `OK TO SUBMIT` / `DO NOT SUBMIT` and writes
[`docs/evidence/submission-gate.json`](../docs/evidence/submission-gate.json). It runs 11 checks:
- F1–F4: format and portal range;
- U1–U3: uniqueness;
- S1–S4: science.

`scripts/build_site.py` renders the verdict as the **first element** of the home page and the
executive summary, and as a generated block at the top of `README.md`. `build_site.py --check`
fails if either goes stale.

**4. The registry completeness trap was closed** (PA-86-03). Two off-grid inventory rows are now
compared by pixel position. Before this, every lane failed `registry_complete_for_index`.

**5. The executive summary** has an exact, generic six-step portal procedure and the cure for
“Predicted values must be in range [0, 1]”: all-finite float32, zeros outside the footprint, no NaN.

## Pass 1 — implement and verify (selected checks, all reproduced from disk)

| Check | Result |
|---|---|
| LLP analytic gradient vs finite differences | max relative error 5.5e-8 (`tests/test_h86j_llp.py`) |
| `fleet.coverage` vs shared `metric.max_cover` | identical on a synthetic grid |
| H86G-H collar-3 holdout re-run | **0.1689**, exactly H86G's published number (an independent reproduction of the shared evaluator path) |
| Registry index | 737/737 measured after the merge with main (734/734 before), 0 errors, `registry_complete_for_index = true` |
| Writer/validator | single-band float32, EPSG:32611, 3730×3292, sample transform, 0 NaN/Inf, values {0, 1}, 0 dots on catalogue, ZIP byte-identical |
| Gate on tampered SHA / missing evidence | fails closed (unit tests) |

## Pass 2 — bug review (found and fixed this session)

- **Gate read the wrong keys.** The first gate run looked for top-level report keys that the H86J
  card nests under `uniqueness`, so it failed U1–U3 closed for the wrong reason. Fixed with an
  explicit resolver and re-run.
- **The gate's U1 required the raw dot-field reading.** That reading fires on the 13GEMSDOE stride-5
  lattice (99.87 % halo coverage) for every possible candidate. The overlap decision now follows
  PA-86-02 (U3). U1 keeps the binding parts: bound, complete, ρ ≤ 0.90. The raw reading stays
  displayed.
- **LLP fit was slow.** It re-sliced sparse matrices on every evaluation. Slices are now cached
  per row set (gradient re-verified), which cut the LOSO wall time about 3×.
- **Preregistration timestamps were hand-typed.** They were corrected to the sandbox clock before
  any fit (IR-86-PREREG-CLOCK).
- **README contradicted itself.** It still said "this session generated no new TIFF". Corrected.
  The gate block is now generated, not hand-written.

## Pass 3 — re-check against the request

| Request item | Status |
|---|---|
| New **unique** TIFF, not a copy | **Done.** New bytes and a new method. 36.4 % overlap with H33, ≤49.6 % against every sparse submission, worst ρ 0.054. It still fails the PA-86-02 hard stop against 12 dense dot fields. That is reported, not hidden. |
| *Obvious* whether OK to download/submit, decided without a human | **Done.** One red/green verdict sits at the top of the site and the README, produced by `submission_gate.py`. The current answer is **DO NOT SUBMIT** (safe to download for review). |
| Why H33 led; can we beat it (PhD level) | `research/H86J_LLP_REVIEW.md` §4–5: new live-truth evidence (the depletion law) plus the prior forensics. The strategy beyond 0.3195 is laid out, and **no projection is claimed** as a score. |
| 3–5 untried hypotheses, ranked, layers/signature/novelty | Preregistration table (5; two blocked by unreachable official data, with named sources) |
| Validate on spatially-blocked holdout before any slot | Done. The candidate failed, so no slot is recommended. |
| Leakage canary, JSON run card, labelled numbers, 3 experiments/2 h | Done |
| Site: download obvious at top + executive summary steps; portal [0, 1] error | Done |
| Irregularities flagged | 6 new IR entries (top of `IRREGULARITIES.md`) |
| PR + merge | See the PR for this branch |

## Limitations and access needs

- **No ORGANIZER-CONFIRMED number exists.** All fleet scores are OWNER-REPORTED, and the public
  leaderboard is computed on undisclosed public chunks. A receipt for any one file would calibrate
  the emulator's top end. Today that top end is compressed: H33 fits 0.163 against 0.2778 reported.
- **Unreachable from the sandbox:** drivendata.org (also excluded by AGENTS rule 9), the USGS 3DEP
  1 m DEM (TNM), USGS ComCat and mrdata.usgs.gov. That blocked H86J-PLUV and H86J-SEIS.
- **The template's cached feature stack is still absent.** The pinned TIFF was used through the
  H86G stack builder and never relabelled as the cache.

## Recommended next work (owner decisions first)

1. **Holdout rule.** S3 (catalogue-hide) is measured to rank the live champion's recipe below
   random, so no live-calibrated idea can pass it. The owner chooses one option (review §6):
   - keep it;
   - replace it with an emulator LOSO gate;
   - adopt a detached-truth holdout.
2. **Emulator top end.** Rebuild H19-4/H19-5's openness and thermal layers from raw data as LLP
   features, then refit, so the emulator can tell the H19-5 lineage from uniform coverage.
3. **A candidate that can pass U3.** Start from the H19-5 family with the LLP depletion reweighting
   (collar logic extended to ~800 m and a catalogue-sparse tilt), with a spread constraint that keeps
   >30 % of dots outside every dense dot field's halo. Test it in a new lane with fresh
   preregistration.
4. **One receipt.** Log any organizer receipt in `ledger/submissions.csv`, bound to its SHA; one is
   enough to recalibrate |G| and the emulator.
