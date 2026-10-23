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
  the concurrent candidate's row from `ledger/variants_external.json`, so the two sessions do
  not fight over the file.

<<<<<<< HEAD
**What the AI did not do:** no DrivenData access, no leaderboard read, no login, no scrape, no
submission, no credential handling. No PROXY or MODEL number is written as a score or a
receipt. Every historical score stays `CLAIM` because no submission-page receipt exists in this
checkout.

**What only the human can supply:** authorization for any slot, `TOP_PUBLIC` and its date, the
remaining rolling-week quota, R0's receipt if one exists, the actual receipt score/date after an
upload, and the choice of the final file from one registered entity.
=======
The human must decide whether to authorize any slot, supply TOP_PUBLIC/date, remaining quota, R0's receipt if available, and the actual submission receipt score/date. The human alone chooses and uploads the final file from one registered entity.

---

## Addendum — PRUNE ladder (second session on 2026-10-23, branch `arena/72ecdcd1-gemsdoe86`)

**AI wrote:** `src/gems86/prune.py`, `scripts/run_prune_ladder.py`, `scripts/merge_prune_ledger.py`,
`tests/test_prune_ladder.py`, `ledger/variant-cards.md`, and the PRUNE-ladder sections appended to
`IRREGULARITIES.md`, `SLOT_PLAN.md`, `docs/SUBMIT.md` and `README.md`.

**AI decided:** the AXIS (PRUNE — the only listed axis whose inputs are present and pinned, since
`training_features.tif` is absent); that the rungs must be the three distance shells that actually exist
among R0's dots (√5, √8, 3.0 px); that a mass-matched control is required before any collar result can be
attributed to proximity; and that the spec-compliant `(PRUNE,3)` belongs to the earlier session, so this
one shipped the missing rungs instead (IR-86-PRUNE-06).

**AI corrected itself:** an earlier claim in this branch that the parent's file bytes were not
reproducible was wrong; it was falsified using the sibling PR's writer profile and is retracted in
IR-86-PRUNE-01 rather than deleted. No truth raster, no portal, no login, no slot.
>>>>>>> origin/main
