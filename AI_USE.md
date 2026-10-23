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

## Addendum — MASS axis (branch `arena/7cf7f98a-gemsdoe86`, 2026-10-23)

**AI wrote:** `scripts/build_mass_axis.py`, `tests/test_mass_axis.py`, the MASS section of
`scripts/build_ledger.py`'s variant sources, `evidence/mass_axis_20261023.json` (generated),
`evidence/mass-mechanism.md`, `ledger/variants_mass.json` (generated), and the MASS updates to
`SLOT_PLAN.md`, `README.md` (CURRENT STATE block only) and `docs/SUBMIT.md`.

**Human decided:** the AXIS for this session is **MASS** (chosen via the session prompt after
PRUNE was shown spent). Everything else followed brief v2.

**AI decided (human can veto):** the parent's ranking is the recorded recipe's FIFO-BFS
visitation order, *validated* by exact reproduction of the pinned `d2.8` dot set before use;
"lowest-ranked" means highest visit rank; the plus pool keeps R0's own >2 px collar; both
predictions are negative so MASS is recommended **no slot by default** in `SLOT_PLAN.md`;
release TIFFs live in `releases/mass/` (gitignored) so the PRUNE release contract tests keep
their meaning.

**AI did not do:** no DrivenData access, no leaderboard read, no submission, no credential
handling. No PROXY or MODEL number is written as a score. R0's 0.2778 stays `CLAIM`.
