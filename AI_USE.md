# AI use disclosure

The competition rules require disclosure of generative-AI use and reproducible code
(<https://docs.nlr.gov/docs/fy26osti/96647.pdf>). This file separates what an AI agent
produced from what a human decided. It is a record, not a certificate.

## Session 2026-10-23 — PRUNE axis

**Written by the AI agent** (Arena.ai Agent Mode), all of it reviewable in git:

* `scripts/build_ledger.py` and `ledger/submissions.csv` — ledger rebuilt from
  `registry/prior_scores.csv` with the documented dedupe rules (115 source rows → 108
  historic rows, 0 receipts; every historic score stays `CLAIM`).
* `scripts/prune_collar.py` — the three PRUNE variants, the brief §6 gate checks, the
  hide-and-recover proxy, the ring-occupancy and feature-response measurements.
* `tests/test_prune_axis.py` — 15 tests (DTI algebra, collar set definitions, relocation
  determinism/constraints, ledger identity rules, release-name and gate checks).
* `releases/*.tif` (6 files) and `evidence/prune_axis_20261023.json`.
* `research/PRUNE_AXIS_20261023.md`, `SLOT_PLAN.md`, `IRREGULARITIES.md`, `docs/SUBMIT.md`,
  and the README `CURRENT STATE` block.

**Decided by the human (owner), not by the AI:**

* To run this session at all, and the axis brief v2 describes as human-assigned. The axis
  (**PRUNE**) was **selected by the agent** because no assignment arrived and every other
  axis lacked its inputs (MASS: parent ranking absent; SNAP/RELIEF/CONCENTRATION: no
  assigned prior). The human can veto and the harness is axis-agnostic.
* `TOP_PUBLIC`, the dated leaderboard number, and the authenticated slot count — still
  blank; the agent refused to invent either.
* **Every submission.** The agent never logs in, never scrapes the leaderboard, never
  uploads. Only the human submits, from their own registered account, one file per slot.
* The conflict logged in `IRREGULARITIES.md` IR-86-PRUNE-01 (repo overlap rule vs brief v2)
  and the data-use question in IR-86-PRUNE-04.

**Not used:** no leaderboard access, no Drivendata page fetch, no credentials, no external
data beyond the hash-pinned USGS/GeoDAWN/NBMG mirrors already in
`registry/data_manifest.json`. No model was trained; nothing here learns from the public
test set, and no file was built to probe where public-test faults are (brief §4.5).
