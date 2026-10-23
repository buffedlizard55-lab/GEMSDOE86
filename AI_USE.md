# Generative-AI use — 2026-10-23

Arena.ai Agent Mode wrote the R0 PRUNE builders, unit tests, ledger generator, gate checks,
measurement receipts, mechanism cards, slot plan, submission card and the README state block.
No human-authored code or text is mixed in unlabelled.

**What the AI decided (and the human can veto):**
- **Three** sessions ran the same axis on the same parent: PR #28 (`arena/06524e4a`, PRUNE≤3 +
  fixed-count H19-5 refill), PR #29 (`arena/72ecdcd1`, nested collar ladder + mass control +
  byte-exact parent rebuild) and this one (`arena/71e90a17`, PRUNE≤3 pure deletion, PRUNE≤4,
  PRUNE≤3-with-relocation). No AXIS assignment arrived in any of them; each selected PRUNE as
  the only axis whose pinned inputs were present, which is itself the flaw this file records.
  This session's PRUNE≤3 turned out to be the same dot set as PR #29's `le3p000` and was
  withdrawn (IR-86-PRUNE-08).
- This file and `SLOT_PLAN.md` were rewritten by this session to reconcile the three, and the
  earlier claim that R0 could not be rebuilt was corrected once PR #29 showed otherwise
  (IR-86-PRUNE-02).
- `ledger/submissions.csv` now has **one** generator (`scripts/build_ledger.py`) that rebuilds
  the concurrent candidate's row from `ledger/variants_external.json`, so the three sessions do
  not fight over the file.

**What the AI did not do:** no DrivenData access, no leaderboard read, no login, no scrape, no
submission, no credential handling. No PROXY or MODEL number is written as a score or a
receipt. Every historical score stays `CLAIM` because no submission-page receipt exists in this
checkout.

**What only the human can supply:** authorization for any slot, `TOP_PUBLIC` and its date, the
remaining rolling-week quota, R0's receipt if one exists, the actual receipt score/date after an
upload, and the choice of the final file from one registered entity.

---

## Addendum — PRUNE ladder (branch `arena/72ecdcd1-gemsdoe86`, PR #29)

**AI wrote:** `src/gems86/prune.py`, `scripts/run_prune_ladder.py`, `scripts/merge_prune_ledger.py`,
`tests/test_prune_ladder.py`, `ledger/variant-cards.md`, and the ladder sections of
`IRREGULARITIES.md`, `SLOT_PLAN.md`, `docs/SUBMIT.md` and `README.md`.

**AI decided:** the three rungs must be the distance shells that actually exist among R0's dots
(√5, √8, 3.0 px); that a mass-matched control is required before a collar result can be attributed
to proximity; and that the spec-compliant `(PRUNE, 3)` belongs to PR #28, so this one shipped the
missing rungs instead.

**AI corrected itself:** an earlier claim that the parent's file bytes were not reproducible was
falsified (byte-exact rebuild, `c55bafc4…`) and retracted in `IRREGULARITIES.md` rather than
deleted. No truth raster, no portal, no login, no slot.

---

## Addendum — RELIEF axis (branch `arena/1252d45c-gemsdoe86`, 2026-10-23, fourth session on R0)

**AI wrote:** `src/gems86/relief.py`, `scripts/run_relief_axis.py`, `tests/test_relief_axis.py`,
`evidence/relief_axis_20261023.json`, the three `releases/…-RELIEF-…-zeros.json` receipts, and the
RELIEF sections of `ledger/variant-cards.md`, `SLOT_PLAN.md`, `docs/SUBMIT.md`, `IRREGULARITIES.md`,
`README.md` (CURRENT STATE block only) and this file. No human-authored code or text is mixed in
unlabelled.

**The human decided:** the session's AXIS — **RELIEF** — and that the `-zeros` form is the primary
upload. Both answers were requested before anything was built, precisely because three earlier
sessions each self-selected PRUNE on the same parent (IR-86-PRUNE-08). Everything else below is the
AI's decision and is vetoable.

**AI decided (science):** the direction of the shift (piedmont→range-front, with the sign flip as a
sibling rung) after measuring that R0's mass sits 53.9 % piedmont / 16.1 % front while an
independent USGS SGMC inventory puts 2.7× the per-pixel un-mapped fault density at the front; the
top dose at 15 % (the brief's ceiling) because a 5 % version projected sub-noise; "deepest-in-regime"
source selection over "nearest-boundary"; a measured in-regime displacement control that is
deliberately **not** written as a raster; and using the SGMC surrogate only for the *prediction*,
never in the builder, so the released files are pure geometric edits of R0.

**AI corrected itself twice, in-session, before releasing anything** (both in
IR-86-RELIEF-01): a band reader that let the stack's nodata sentinel into the standardisation (it
classified 100 % of R0's dots as "basin"), and a first build whose relocated dots could sit 1 px
apart — a hidden clustering edit that flipped the surrogate sign of every rung. The defective files
were deleted, `ledger/` reverted, and the build re-run once; both faults are now unit-tested and the
builder aborts on them.

**What the AI did not do:** no DrivenData access, no leaderboard read, no submission, no login, no
credential, no Dropbox. No gate script was modified, relaxed or bypassed; the repo's 70 % overlap
rule was *not applied* because brief v2 §6 forbids it, and that conflict stays open
(IR-86-PRUNE-01). No PROXY or MODEL number is written as a score; R0's 0.2778 is still a CLAIM and
`ledger/submissions.csv` still has **0 receipts** in 118 rows. No slot is authorised.

**What only the human can supply:** authorization for any slot, `TOP_PUBLIC` and its date, the
remaining rolling-week quota, R0's receipt if one exists, the receipt score/date after an upload,
the data-use decision on the tracked competition rasters (IR-86-PRUNE-04), and the final blind pick.
