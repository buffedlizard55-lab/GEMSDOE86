# Generative-AI use — 2026-10-23

Arena.ai Agent Mode wrote the R0 reconstruction/PRUNE builder, unit tests, ledger seeding logic, validation receipts, mechanism card, slot plan, and submission documentation. It also selected PRUNE≤3 as the only listed axis compatible with the inherited R0 collar and the new ≥3 px constraint; no human axis assignment was present in the request.

The pinned input bytes, archived R0 recipe, fixed random seed, exact shared metric, and validation rules are recorded in `scripts/build_r0_prune.py` and `evidence/r0-prune3-run-card.json`. AI did not access DrivenData, infer a leaderboard score, submit a file, or represent a PROXY/MODEL as a RECEIPT.

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
