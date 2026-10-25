# Session review — 2026-10-25 (`arena/96fc6d48-gemsdoe86`)

**Verdict: `negative` · DO NOT SUBMIT ANY FILE.** No new TIFF was generated, no geological
experiment was run, and no weekly slot was used (`submission_slots_used = 0`). This session
repaired the machine audit path, registered an unregistered published raster, aligned all
public authorization language, verified every published byte from disk, and recorded the
PhD-level answer to the 0.2778 question below. Standing rules read at session start:
`PROMPT.md`, `README.md`, `AGENTS.md` (rules 1–16), `research/REQUEST_20261025.md`.

Every non-format number below is labelled `HOLDOUT-DTI`, `SGMC-PROXY-DTI`, `LEAKAGE-CANARY`,
`REGISTRY-MEASUREMENT`, or `OWNER-REPORTED`. There is **no** `ORGANIZER-CONFIRMED` number in
this repository: the DrivenData submissions page is browser-only and was not accessed by any
automated tool (AGENTS.md rule 9; DrivenData Terms of Use).

---

## 1. Why and how did `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` reach 0.2778 (OWNER-REPORTED)?

This is established by the repo's own pixel-exact forensics and was not re-derived this
session (hashes re-verified): `research/H33_ANALYSIS.md`, `research/H86G_EDTI_REVIEW.md`,
`docs/evidence/h86f-h33-forensics.json`.

- **H33 is not a new model.** It is an exact dot-subset of its GEMSDOE28 D2.8 parent
  (40,199 dots → 37,654 dots; 0 added, 2,545 removed, and every removed dot sits at
  catalogue distance √2–2.0 px). Its ancestry is the H19-5 "multiline corroborated"
  lineament surface thinned to ≥2.828 px spacing and emitted as binary dots.
- **The 0.2708 → 0.2778 step is emission thrift under the official metric**, the
  distance-weighted Tversky index (DTI; α=0.2 false-positive weight, β=0.8 false-negative
  weight, 300 m triangular kernel; zero credit at ≥300 m distance):
  1. Truth credit at a pixel is the *maximum* kernel weight over covering dots, so a second
     dot within one kernel diameter adds FP mass `0.2·(1−k)` without adding truth credit.
     ~2.8 px spacing removes that redundancy.
  2. Dots 1–2 px from a mapped trace mostly cover organizer-masked catalogue pixels —
     near-zero marginal truth credit at full FP price. Deleting the 2,545 collar dots is the
     *entire* measured difference between the two files.
  3. A non-redundant dot raises DTI iff its kernel credit `k > α·DTI` (≈0.056 at 0.2778), so
     the game is *where* dots sit (independent surface evidence, far from the catalogue)
     minus *wasted* dots (collar + redundancy).
- **Evidence classes:** 0.2778, 0.3195 and 0.4413 are `OWNER-REPORTED` (unverified claims
  transcribed in `registry/prior_scores.csv` / `ledger/submissions.csv` `CLAIM` rows; 0.3195
  and 0.4413 are mutually conflicting in the same request). Instrumentation (repo E1b,
  `research/H86G_EDTI_REVIEW.md`): the whole-component catalogue-hide instrument
  **anti-correlates** with the owner-reported live ordering (H33 `HOLDOUT-DTI` as-is
  0.0037), while the `SGMC-PROXY-DTI` (USGS SGMC faults >3 px off catalogue, 62,122 px)
  reproduces it (H33 0.0954). Neither is a leaderboard projection.
- **Format matters independently:** the owner-reported portal failure *"Predicted values
  must be in range [0, 1]"* is excluded for every artifact in this repo (single-band
  float32, values in [0,1], 0 NaN/Inf, zeros outside the footprint — `FORMAT-VALIDATION`
  below). Format validity never authorizes an upload.

## 2. Are we able to generate a submission that scores higher than 0.2778?

**Honest answer: not verifiable, and not authorized today.** At 0.2778 with |G|≈40k,
+0.01 live DTI ≈ +418 kernel-credit units ≈ 42 km of trace hit squarely; every measured
*reallocation* of H33's own dots in this repo yielded |Δ|≤0.0073. Beating 0.2778 therefore
requires new surface evidence — dots on real hidden trace the H19-5 ancestor misses —
emitted at H33-grade efficiency. Two independent blockers prevent any such claim now:

1. **Protocol lane rule is literally unsatisfiable.** The SHA-pinned 17GEMSDOE witness
   (`ab0a0a62...`) is positive on 100% of the allowed domain, so every nonempty candidate
   has forward 3-px overlap 1.0 > 0.70 (`STOP_LITERAL_OVERLAP_UNSATISFIABLE`, re-measured
   this session; `REGISTRY-MEASUREMENT` over all 36 registered artifacts,
   `docs/evidence/all-artifacts-registry.json`, registry incomplete). The PA-86-01/02
   like-for-like readings (thresholds unchanged: ρ ≤ 0.90, overlap ≤ 0.70) exist, but the
   only lane that promoted under them (H86G-EDTI, 43-file local registry) was later shown
   to have 25 informative dot-field firings on the full 690-raster restored registry
   (`IR-86-H86G-LOCAL-ONLY-DUP-20261025`), i.e. it is a **duplicate stop**, not clearance.
2. **No current method paragraph is assigned**, the template's cached feature stack is
   absent, and there is no organizer receipt. Standing rules therefore stop before
   fitting or placement. Generating yet another raster would produce exactly what the
   protocol forbids: an unverifiable, unsubmittable file.

**Maximize P(Win) applied:** the highest-leverage action this session was making every
gate actually runnable and honest (below) rather than emitting a 37th unsubmittable
raster. The next scientific move, when a lane is authorized and the protocol conflict is
resolved through an explicit revision endorsed at fleet level, is to run the top queued
untried hypotheses (queue ranks 4–6 in `registry/h86n_hypotheses_20261025.json`, all native-band so no
external obtainability blocker):

| Rank | ID | Layers (`training_features.tif`) | Signature | Why catalogue-missing | Named mimic |
|---|---|---|---|---|---|
| 4 | H86N-1_SCQD | 16 `ieq_n100a15`, 10 `deq_n100a15`, 8 `geod_dilaterate` | dilatancy rank **conjunction-gated** by seismicity presence | seismogenic blind faults under basin fill lack scarps | injection/volcanic swarms |
| 5 | H86N-2_TCW | 6 `tc` (verified GeoDAWN Total Count), 12 `det_elev`, 19 `det_elev_slope` | one-sided TC depletion asymmetry across elevation breaks | sediment-blanketed traces erase scarps but keep TC steps | fan toes, playa rims |
| 6 | H86N-3_DBK | 15 `depth_to_base_surf`, 13 `iso_grav_anom` | basement-depth 2nd-derivative kink × gravity-sign concordance | buried half-graben hinges never reach the surface | paleovalley walls, caldera rings |

Each names how it differs from implemented lanes (verified by code search this session:
prior seismicity use is an additive fitted feature `eq_prox_exp` in EWCS/CSGD; no TC
cross-strike asymmetry or Band-15 second-derivative kink exists in `src/`/`scripts/`).
Validation protocol for any of them: frozen preregistration → per-feature leakage canary
(AUC stop 0.90) → buffered whole-component hide-and-recover with visible-only features →
paired physical-block CI must beat matched controls *and* the current same-split best →
surface ρ and final-dot overlap vs the **full restored** registry → run card. Not run here.

## 3. What was broken, and what was fixed (3 passes)

**Pass 1 — implement & verify.**
- `scripts/verify_submission_tif.py` passes (H86G-EDTI pinned bytes, ZIP, CRS/shape/
  transform, values exactly {0,1}, 55,000 positives) — but its own output is explicit:
  format/identity only, **DO NOT SUBMIT**.
- Found `audit_release.py` failing: PR #165 published H86M-LT unregistered
  (`IR-86-96FC6D48-H86MLT-REGISTRATION`). Re-verified its bytes independently (SHA-256
  `4067382c...`, ZIP byte-identical, EPSG:32611 3730×3292, values exactly {0,1}, 37,654
  positives) and registered it audit-only (`DO NOT SUBMIT`). Its run card's
  `promote`/`safe_to_submit=true` claim was unsupported (no `HOLDOUT-DTI`; tomography DTIs
  are projections of `OWNER-REPORTED` scores) → set to the standing negative state with
  original claims preserved in `superseded_claims`. `docs/h86m-lt.html` and the README head
  ("OK TO SUBMIT") were rewritten DO-NOT-SUBMIT aligned.
- Found the registry re-measurement crashed on a stale data layout
  (`IR-86-96FC6D48-PREFLIGHT-LAYOUT`): pinned grid lives in `data/bridge/`, not `data/`.
  Fixed once in `scripts/protocol_preflight.py`, `scripts/audit_release.py`,
  `scripts/check_h86e_registry.py`, `scripts/pa86_chance_overlap.py` (vendored template
  untouched); restored the pinned witness from the pinned blob and re-measured all 36
  artifacts (`REGISTRY-MEASUREMENT`: forward overlap 1.0 each vs witness; registry
  incomplete — a sufficient negative, never clearance).
- Pipeline after fixes: `audit_release.py --measure-registry` → `audit_ok=true`,
  decision `DO NOT SUBMIT`; `build_site.py` regenerated; `build_site.py --check`,
  `check_site.py`, `audit_downloads.py [--write]` all PASS.

**Pass 2 — review.** Two test failures (1020 passed / 2 failed): README artifact-count
assertion (fixed by the truthful README head: **36** published research TIFFs) and an
RLMS test probing the old `data/` layout (fixed to probe the real pinned paths; with
pinned inputs present the CLI now correctly stops with `STOP_LITERAL_OVERLAP_UNSATISFIABLE`).
Added `data/bridge/registry/` to `.gitignore` (witness must not enter git). Hypotheses
ranks 4–6 written to `registry/h86n_hypotheses_20261025.json` (status
`NOT_RUN_PROTOCOL_STOP`; no HOLDOUT-DTI recorded — no projections written as scores).
An initial attempt to append them to the dated `registry/followup_hypotheses_20261025.json`
snapshot was reverted to preserve that archive byte-for-byte (its regression test pins
ranks [1, 2, 3]).

**Pass 3 — re-check.** Full pipeline re-run after all edits (see final numbers in the run
card): audit, site build/check, download audit, `pytest -q`. Public pages state the
obvious decision: homepage/executive/submit panels show "OK to submit? NO — DO NOT
SUBMIT" with "safe to download for audit only", direct TIFF/ZIP download links, SHA-256
values, and the exact DrivenData portal procedure ([0,1] range class, unique name,
≤140-char note) for a *future authorized* file only.

## 4. How to submit (exact procedure — only after a future authorized candidate exists)

1. Confirm every machine gate passed for the exact file (canary, holdout paired CI vs
   controls, full-registry surface+dot checks, fail-closed format) and that the release
   decision is no longer `DO NOT SUBMIT`. **Today it is `DO NOT SUBMIT` — stop here.**
2. On the DrivenData competition page (browser, signed in), check the remaining weekly
   quota shown there; choose *New submission*.
3. *File to submit:* the authorized single-band `float32` `.tif` (or the one-TIFF
   `.zip`) whose SHA-256 matches its run card; e.g. naming convention
   `gems86-<lane>-<dots>dots-<YYYYMMDDTHHMMSSZ>-<sha8>-zeros.tif`. Values must be in
   `[0, 1]` and the format validator must pass (this excludes the portal range error).
4. *Note (optional):* paste the card's ≤140-char note (unique per submission).
5. Submit **once**, save the organizer receipt, and log score + receipt ID bound to the
   exact SHA in `ledger/submissions.csv` before any further slot. Only then may a number
   be labelled `ORGANIZER-CONFIRMED`, and only then may `safe_to_submit` be re-evaluated.

## 5. Limitations (own the outcome)

- ❌ No DrivenData auth → cannot auto-download official data pages or obtain receipts;
  only human browser receipts can supply `ORGANIZER-CONFIRMED` scores or quota.
- ❌ No organizer registry / complete restored registry in this checkout; uniqueness
  clearance cannot be established here (2 grid-incompatible rows; local scans are scoped).
- ❌ Actual shared cached feature stack absent; the pinned 19-band GitHub mirror is not
  that cache and is not relabelled as one.
- ❌ Literal lane rule unsatisfiable vs the full-support witness; no threshold was
  changed and no bypass was added. An explicit fleet-level protocol revision is the
  unblock — not something a single lane may grant itself.
- ❌ Historic lanes use several holdout designs; no comparable cross-design "best" is
  claimed. Fault prediction would not by itself confirm a geothermal vent.

**Suggested next work (in order):** (1) fleet-level protocol revision for the
representation-aware lane rule; (2) restore the complete registry incl. the 2 off-grid
rows; (3) preregister and validate H86N-1_SCQD (lowest cost) under the frozen protocol;
(4) if it beats controls and the same-split best with a positive paired CI and passes
full-registry checks, let the separate selector decide a single weekly slot and bind the
organizer receipt before any further submission.

## 6. Run card

Machine-readable card: [`docs/evidence/session-96fc6d48-run-card.json`](../docs/evidence/session-96fc6d48-run-card.json)
(schema `gems86.session-review.v1`; verdict `negative`; `raster_sha256: null` — no raster
generated; HOLDOUT-DTI `NOT_RUN_PROTOCOL_STOP` (`gems57-pooled-hide-v2`); registry
remeasurement of all 36 inherited artifacts vs the pinned witness; all prior H86G-EDTI
numbers preserved unrebranded as historical). The automatically refreshed negative review
card is `docs/evidence/latest-review-run-card.json`.
