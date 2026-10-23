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

## Addendum — SNAP axis (branch `arena/1f6f5dc8-gemsdoe86`, 2026-10-23)

**AI wrote:** `src/gems86/snap.py`, `scripts/run_snap.py`, `tests/test_snap_axis.py`, the SNAP rows in
`ledger/variants_snap.json`, the SNAP section of `ledger/variant-cards.md`, the rewritten
`SLOT_PLAN.md`, `IR-86-SNAP-01…05`, and the edits to the `README.md` CURRENT_STATE block,
`docs/SUBMIT.md`, `scripts/build_ledger.py` (one extra variants file) and `.gitignore`
(`/releases/snap/*`).

**AI decided (the human can veto any of it):**
- The AXIS again, because none was assigned (IR-86-SNAP-01). SNAP was taken from `SLOT_PLAN.md`
  slot 2 once the pinned feature stack restored and verified.
- That the *literal* SNAP rule is degenerate at 98 % moved, and that two declared gates
  (crest ≥ 0.75 rank, gain > 0.02) restore a local, attributable edit (IR-86-SNAP-02). The
  ungated numbers are in the record, not hidden.
- Three surfaces rather than one: magnetic, gravity, and their average — so a single slot on one of
  them can be read against the other two.
- Predicted changes are **negative** for all three (−0.006 / −0.002 / −0.004 MODEL, bands inside
  ±0.03): the honest consequence of IR-86-SNAP-03 and the 0.500–0.527 catalogue AUC.
- SNAP releases live in `releases/snap/` because they add dot cells, which
  `tests/test_prune_ladder.py` correctly forbids inside `releases/`.

**What the AI did not do:** no DrivenData access, no leaderboard read, no login, no scrape, no
submission, no credential handling. No PROXY or MODEL number is called a score or a receipt. No gate
was relaxed: the new files pass the same `gems57.validate` and `gems57.gates.format_report` used by
the PRUNE releases.

**What only the human can supply:** the AXIS for the next session, `TOP_PUBLIC` + date, the
rolling-week quota, any submission-page receipt, the decision to spend a slot on a file predicted to
lose, and the data-use ruling on committed competition rasters.
