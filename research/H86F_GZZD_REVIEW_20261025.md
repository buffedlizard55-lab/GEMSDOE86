# H86F-GZZD review and handoff — 2026-10-25

## Executive decision

**DO NOT SUBMIT.** The H86F-GZZD lane produced the requested new single-band
GeoTIFF (byte-distinct, unique filename, locally format-valid), but the automated
gates reject it on two independent grounds: it is HOLDOUT-DTI-negative against its
own preregistered controls, and it has no registry clearance (13 like-for-like
dot-field firings; PA-86-02 failed closed on an incomplete registry). No
DrivenData login, organizer receipt, selector decision, or weekly slot was used.

- Candidate: `docs/downloads/gems86-h86f-gzzd-laplace-dipole-44090dots-20261025T003205Z-c18f96da-zeros.tif`
- ZIP (byte-identical single TIFF): same stem with `.zip`
- SHA-256 (TIF): `b86a5b2f46ea1091db3cd5051980445832e20fd2670ea2d371de1f1c6e03c993`
- Submission name/note (unused): stem without extension; "H86F GZZD Laplace-dipole
  audit-only 44090 dots; negative holdout; DO NOT SUBMIT" (82 chars)
- Evidence: [`h86f-gzzd-run-card.json`](../docs/evidence/h86f-gzzd-run-card.json),
  [`h86f-gzzd-registry-surface.json`](../docs/evidence/h86f-gzzd-registry-surface.json),
  [`h86f-gzzd-registry-final-dots.json`](../docs/evidence/h86f-gzzd-registry-final-dots.json),
  [`h86f-h33-forensics.json`](../docs/evidence/h86f-h33-forensics.json),
  [`H86F_GZZD_PREREGISTRATION.md`](H86F_GZZD_PREREGISTRATION.md)

All performance values below are labelled by evidence class. There is no
`ORGANIZER-CONFIRMED` number in this lane.

## Direct answers to the owner's questions

**Q1. What is special about GEMSDOE32 `h33-h33-2-b2-…-zeros` (owner-reported
0.2778)?** Pixel-exact forensics (`scripts/h86f_forensics.py`) prove it is an
exact subset of its GEMSDOE28 parent: 37,654 vs 40,199 dots, **0 added, 2,545
removed**, and every removed dot lies at catalogue distance √2–2.0 px (nothing
removed at 1.0 px or beyond 2.0 px). The owner-reported 0.2708 → 0.2778 step
came purely from deleting collar dots whose 300 m triangular kernels overlap
catalogue-masked pixels: a coverage-efficient dotted-emission effect under the
α=0.2/β=0.8 kernel DTI, not a new geological layer. 0.2778 remains
OWNER-REPORTED (no submission-page receipt); the conflicting 0.4413/0.3195
claims in the prompt were not used.

**Q2. Can this repository beat 0.2778?** No lane measured to date gives any
evidence of that. The catalogue-hide holdout cannot be projected to a
leaderboard value (its correlation with live scores in repo history is
sign-unstable; see SLOT_PLAN/IR-86-PRUNE-03), and every automatically vetted
candidate — including this one — is at or below its own controls on that
instrument. The honest path to beating 0.2778 is (a) obtain the receipt-backed
score history, (b) fix the two grid-incompatible registry rows so PA-86-02 can
ever pass, and (c) let a separate selector spend a slot on a candidate that
first beats same-split best HOLDOUT-DTI 0.1241 with a separated CI. No such
candidate exists today.

**Q3. Exactly how would one submit IF a future selector approves a file?** See
the executive summary on the site (`docs/executive-summary.html`): download the
selector-approved `.zip` (or `.tif`), create a submission on the DrivenData
competition 306 submission page with the recorded filename and ≤140-char note
(as printed on the artifact receipt), upload, and keep the submission-page
receipt. Range/CRS/shape are pre-validated by construction (fail-closed writer
rejects out-of-[0,1] values; EPSG:32611, 3730×3292, single band) — but local
validity is not organizer acceptance. **This candidate is not approved: do not
submit it.**

## Three review passes

### Pass 1 — implementation and scientific design

Four hypotheses were frozen before computing any lane field
(`H86F_GZZD_PREREGISTRATION.json`, 2026-10-25T00:10:47Z): (1) **H86F-GZZD**
(run): a blind basin-bounding normal fault juxtaposes dense basement against
light basin fill, so the upward-continuation-free vertical gravity-gradient
tensor component `g_zz = -(∂x Band18 + ∂row Band11)` (image coordinates; exact
for the Laplace field above sources) concentrates at the trace as a signed
dipole whose polarity encodes downthrow side, concordant with the Band-15
basement-depth polarity; (2) **H86F-WARP** (not run; radiometric age-offset
warping); (3) **H86F-HMDC-LITE** (blocked: official GDR sinter/probe bytes not
re-obtained/hash-verified in the sandbox this session); (4) **H86F-SLB** (not
run; strand-length extrapolation). A parallel session previously proposed `g_zz`
regularization for an SPBT concept but reported running it *without* that
regularization; a `g_zz/gzz` grep found no prior tensor computation in shipped
code, and the prior art actually executed used unsigned gradients (Bands 5/11/18
singles, HORSE/Bouguer edges).

Implementation (`src/gems86_gzzd/features.py`): Bands 5/11/13/15/18 only,
Gaussian σ = 5 px; fail-closed band-QC `corr(g_zz, -∇²Band13) = 0.8952 ≥ 0.80`
on the 30-px-eroded interior (4,728,805 px); `|g_zz|` mouth-gated to the
strongest 5% of interior gradient magnitude; dipole pairing via opposing-lobe
evidence over ±(1–5) px along the local gradient direction; soft basement-depth
polarity gate ∈ [0.05, 1]; catalogue never enters any feature (only the shared
emitter's allowed mask and eval-time hiding use it). Three arms at exactly
44,090 dots each via the shared emitter/writer (`vendor/gems57`, untouched):
E1 dipole × polarity gate (candidate), E2 dipole alone (gate ablation),
E3 unsigned Band-5-gradient edge control, plus fixed R0 visible-collar control
(reconstructed in-fold from visible catalogue only). Feature-alone canaries
(discriminative AUC) were all near chance: concordant 0.5007, dipole 0.5001,
edge 0.5243, |g_zz| 0.5115, polarity gate 0.5024 — no leakage signal and,
in hindsight, already a warning that the fields barely recover withheld
catalogue segments.

### Pass 2 — adversarial review, edge cases, corrections

- **Registry completeness is a measured blocker, not a detail.** Both
  two-phase scans measured 685 of 687 indexed rasters with the same 2
  grid/CRS-incompatible rows (`14GEMSDOE` horse-ensemble; `7GEMSDOE` qfaults
  prior). `registry_complete_for_index = false`; `pa86_chance_overlap.py`
  raised `ValueError: Incomplete registry cannot pass` (exit 1, recorded
  `FAILED_CLOSED_NO_REPORT`). Under PA-86-02 no candidate can pass until the
  protocol fixes/excludes those rows upstream. This lane did not bypass it.
- **Placement-procedure disclosure.** The frozen preregistration let an
  audit-only artifact be emitted when the pre-placement surface had 0 missing
  rows and 0 rank-correlation firings (worst ρ = 0.467 < 0.90) while
  *completeness* was false; the surface gate itself is recorded false. The
  patched H86E-MMT runner additionally requires zero registry errors before
  placement. This divergence is recorded here rather than silently aligned:
  the artifact exists only as a negative audit record and both readings agree
  on the verdict. Future lanes should adopt the stricter zero-error rule.
- **Worst surface ρ (0.467) is vs a GEMSDOE24 acquisition-block-id external
  grid** bundled in the registry. Below threshold, but a reminder that the
  gravity field is a USGS compilation whose block geography can mimic basin
  structure — the named non-fault mimic for this lane.
- **Overlap saturation.** Final-dot worst like-for-like overlap 0.99995 is vs
  the space-filling `13GEMSDOE` stride-5 lattice (a geometric saturation of
  the 3-px test, also why the literal protocol preflight remains STOP), while
  the worst final-dot Spearman ρ is only 0.0261. The 13 dot-field firings are
  reported as firings; without PA86 they are not labelled informative.
- **File-mode fix.** The shared writer's temp files left the new downloads at
  mode 600; normalized to 644 (bytes/SHAs unchanged) so the Pages artifact is
  downloadable like its 15 siblings.
- **Independent re-validation** (beyond the runner's own receipt): shared
  `validate.validate()` all-checks-pass (min 0.0, max 1.0, 0 NaN, 44,090
  positives, CRS/transform/shape equal to the lentil reference), ZIP contains
  exactly the byte-identical TIFF. `scripts/audit_release.py --measure-registry`
  and `scripts/audit_downloads.py --write` both re-measure 16/16 artifacts OK.
- **Ablation honesty.** E1 ≈ E2 (paired Δ +0.0011 [−0.0008, +0.0030]): the
  basement-depth polarity gate adds nothing. E1 < E3 (Δ −0.0018 [−0.0126,
  +0.0091]): the signed-dipole construction does not beat a plain unsigned
  gravity edge on this instrument. The hypothesis, as run at σ = 5 px against
  the 300 m kernel, is falsified; no threshold, σ, or dot count was tuned
  after seeing the holdout.

### Pass 3 — measured results (all HOLDOUT-DTI unless stated)

Evaluator `gems57-pooled-hide-v2`, 11,321 withheld positives, 44,090 dots/arm:

| Arm | HOLDOUT-DTI | 95% CI |
|---|---|---|
| E1_gzzd_concordant (candidate) | 0.0303 | [0.0237, 0.0364] |
| E2_gzzd_dipole (ablation) | 0.0292 | [0.0227, 0.0352] |
| E3_gravmag_edge_control | 0.0321 | [0.0215, 0.0427] |
| R0_D28_visible_collar | 0.0339 | [0.0160, 0.0497] |
| Same-split historical best (`E3_kslb_noisyor_44k`) | 0.1241 | [0.1080, 0.1403] |

E1 per-fold: NW 0.0234, NE 0.0314, SW 0.0326, SE 0.0316. Paired Δ (E1−R0):
−0.0036 [−0.0185, +0.0134]. Registry: surface 685/687 measured, worst ρ 0.467,
0 ρ-firings, 19 like-for-like dot-field firings; final dots worst ρ 0.026,
0 ρ-firings, 13 like-for-like firings; PA-86-02 failed closed. Decision
reasons (run card): no separated-CI win vs same-split best; paired Δ vs best
control not > 0; surface gate failed; final-dot like-for-like gate failed;
PA-86-02 gate failed. Verdict: `negative`, DO NOT SUBMIT, 0 slots used.

### Requirement traceability (owner's mandate)

Unique single-band TIFF generated ✓ (new bytes, unique stem, not a copy of any
fleet raster; sha256 recorded). Easy download on Pages with obvious status ✓
(home-page H86F section with DO-NOT-SUBMIT badge + TIF/ZIP links; status from
automated gates, no human inspection). High-scoring validation gates before
declaring submittable ✓ — and they correctly reject this file. 3–5 untried
hypotheses ranked before implementing ✓ (preregistration). External data named
and verified obtainable or blocked honestly ✓ (HMDC-LITE blocked on unverified
GDR bytes; GeoDAWN metadata re-verified live, CC0). Executive submission guide
✓ (site). Standing prompt in README/PROMPT.md ✓ (pre-existing, re-read this
session). Three passes ✓ (this document). Beating owner-reported 0.2778 ✗ —
not achievable with measured evidence; see Q2.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python scripts/restore_data.py --include-registry
.venv/bin/python scripts/restore_registry_inventory.py --workers 8
.venv/bin/python scripts/h86f_forensics.py            # H33 subset + band QC evidence
.venv/bin/python scripts/run_h86f_gzzd.py             # full lane (~16 min; do not re-run for promotion)
.venv/bin/python scripts/protocol_preflight.py
.venv/bin/python scripts/audit_release.py --measure-registry
.venv/bin/python scripts/audit_downloads.py --write
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/check_site.py
.venv/bin/python -m pytest tests/ -q
```

## Limitations and suggested next steps (for the next session)

1. **Fix the registry completeness trap upstream** (2 grid-incompatible rows).
   Until then PA-86-02 can never pass for anyone; this is now measured in two
   lanes. A protocol amendment (exclude-or-repair list) must be decided
   upstream, never per-lane.
2. **Get receipt-backed organizer scores** for the h33 lineage; without them
   "beat 0.2778" is not a well-posed target. The catalogue-hide holdout is at
   its discrimination floor for catalogue-avoiding hypotheses (canaries ≈ 0.50
   here); a second, complementary instrument (e.g., the archived SGMC-extra
   auxiliary proxy, labelled separately) would help rank distal hypotheses.
3. **Do not re-run GZZD as-is.** If gravity-tensor physics is revisited, the
   informative variant is multi-scale σ (10–20 px, matching 1–3 km source
   depths) with per-scale canaries first; even then it must beat E3-style
   unsigned edges and the 0.1241 same-split best before any slot discussion.
4. **Unblock HMDC-LITE properly:** fetch the official GDR sinter/spring and
   probe datasets from their landing pages, hash-pin the bytes, and only then
   preregister the run.
5. h33's lesson (deletion of √2–2 px collar dots) suggests emission-geometry
   remains the only receipt-adjacent axis with owner-reported gains; any
   future lane should pair its geology with a dotted-emission control arm so
   the two effects are not confounded.
6. Site/tests now hardcode 16 artifacts; the next lane must update
   `download-inventory.json`, `registry/artifact_cards.json`,
   `audit_release.archived_holdout()`, the two audit tests, README count, and
   add its own site section (mirror `h86f_gzzd_answer()`).

## Official sources consulted (verified live 2026-10-25)

- USGS GeoDAWN landing page — survey geometry/CC0 terms:
  https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- DrivenData official reference solution (comparison baseline, not portal proof):
  https://github.com/drivendataorg/gems-prize-reference-solution
- EPSG:32611 registry entry (grid identity): https://epsg.io/32611
- Tversky index definition (α/β semantics): https://en.wikipedia.org/wiki/Tversky_index

## Post-merge forensic addendum (2026-10-25, after PR #98 merged to main)

While this PR was open, session `86569dcd` merged (PR #98) with
`IR-86-MMT-RANK01-TIE-20261024`: the pre-fix `gems86_mmt.features.rank01`
assigned row-major tie ramps across tied background cells. This lane reused
`run_h86e_mmt.make_dots` (which applies `rank01`) and `rank01` itself for the
registry surface, so the identical defect class touches this lane's receipts.
Impact, measured read-only post-merge (label: POSTHOC-DIAGNOSTIC):

- **R0 comparator understated.** The binary D28 surface has ~5.1M tied zeros;
  after the allowed ones were exhausted, zero-tie filling came from southern
  rows. Recorded R0 = 0.0339; the true fold-fair R0 on the identical split is
  **HOLDOUT-DTI 0.0961 [0.0830, 0.1089]** (`R0_foldfair` in
  `docs/evidence/h86e_comparator.json`; D28-as-is 0.0919). The paired delta
  against "best preregistered control" in the run card therefore used a weak
  comparator; against the true control the candidate trails by ~0.066. The
  verdict (negative) is **strengthened**; no number in the frozen run card was
  edited (same preservation rule main applied to the H86E-MMT card).
- **Candidate dots not south-packed.** All 44,090 final dots sit on
  positive-field cells (1,620,779 available), spread over rows 2..3718
  (16,953 / 10,142 / 6,362 / 5,095 / 5,538 per 746-row band) — the zero-tie
  fill never engaged for E1's placement surface. Residual tie reordering
  inside exactly-equal positive float cells is second-order and does not
  rescue the hypothesis: the rank-free field-alone canaries (sklearn AUC,
  average-tie handling) were already ≈0.50.
- **Registry surface rho** was computed on the pre-fix `rank01` surface; worst
  rho 0.467 is far from the 0.90 stop, and the gate failed on completeness
  regardless, so the registry outcome is unchanged in kind.
- `rank01` is fixed on merged main (`src/gems86_mmt/features.py`); any future
  re-measurement must not be compared against this card's R0 without the
  comparator correction above. `scripts/run_h86f_gzzd.py` is now gated behind
  `protocol_preflight.require_feasible()` like the other 50 historical
  builders (51 total), so the lane cannot be silently re-run for promotion.
