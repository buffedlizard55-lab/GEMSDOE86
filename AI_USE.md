# Generative-AI use — 2026-10-23

Arena.ai Agent Mode wrote the R0 PRUNE builders, unit tests, ledger generator, gate checks,
measurement receipts, mechanism cards, slot plan, submission card and the README state block.
No human-authored code or text is mixed in unlabelled.

**What the AI decided (and the human can veto):**
- Two sessions ran on the same axis. Session A (`arena/06524e4a`, PR #28) built PRUNE≤3 with a
  fixed-count H19-5 refill; session B (`arena/71e90a17`, this one) built PRUNE≤3 pure deletion,
  PRUNE≤4 and PRUNE≤3-with-local-relocation. Because no AXIS assignment arrived, both selected
  PRUNE as the only axis whose pinned inputs were present.
- `ledger/submissions.csv` now has **one** generator (`scripts/build_ledger.py`) that rebuilds
  the concurrent candidate's row from `ledger/variants_external.json`, so the two sessions do
  not fight over the file.

**What the AI did not do:** no DrivenData access, no leaderboard read, no login, no scrape, no
submission, no credential handling. No PROXY or MODEL number is written as a score or a
receipt. Every historical score stays `CLAIM` because no submission-page receipt exists in this
checkout.

**What only the human can supply:** authorization for any slot, `TOP_PUBLIC` and its date, the
remaining rolling-week quota, R0's receipt if one exists, the actual receipt score/date after an
upload, and the choice of the final file from one registered entity.
