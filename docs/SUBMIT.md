# Manual submission card — no automatic submission

**Status: BUILT; not slot-approved.** TOP_PUBLIC, remaining quota and R0's submission receipt
were not supplied. The human alone submits, from one registered entity, one file per slot.
Full plan and decision tree: [SLOT_PLAN.md](../SLOT_PLAN.md). Release TIFFs are local-only and
gitignored (unchecked data-use terms); hashes below are the authority. Rebuild them any time:
`.venv/bin/python scripts/build_r0_snap.py --build` (SNAP; identical sha256s) — PRUNE files
per their own builders (`scripts/run_prune_ladder.py`, `scripts/prune_collar.py --build`).

## Slot 1 — PRUNE ≤ 3.000 px, pure deletion (nested ladder, PR #29) — unchanged

- Submission name: `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros`
- Upload: `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif`
- SHA-256: `a438e92b…` — take the full digest from `releases/…-a438e92b-zeros.json`.
- 35,483 dots (R0 minus all 2,171 dots within 3.0 px of the catalogue), 5.77 % changed.
- Prediction: **+0.004 (MODEL)**, band −0.004 … +0.013. Receipt: `evidence/prune_ladder.json`.

## Slot 2 — RELIEF (to be built) — SNAP fallback below only if a slot must be filled first

SNAP was built this session and its report-only controls came back flat-to-negative
(SGMC dose-response −0.0021 … −0.0089; mechanism cards:
[`evidence/r0-snap-mechanism.md`](../evidence/r0-snap-mechanism.md)). All three keep
R0's 37,654 dots and its >2 px catalogue exclusion (min distance 2.236 px — see
IR-86-SNAP-01 before uploading anything).

| Variant | Upload (zeros twin) | sha256 (zeros) | NaN twin sha256 | moved / mean disp. | prediction (MODEL) |
|---|---|---|---|---|---|
| `snapr2g10` (the only SNAP slot candidate) | `releases/h33-h33-2-b2-snapr2g10-20261023-8ca1d869-zeros.tif` | `8ca1d8690aa835c8e8e823db2965a5ca357c9132452ae5a205403a6380082d2e` | `32c1e4e99444abafd35165666e34efc9fda3a15c664dea4e7c809d06ae613f52` | 17.47 % / 0.34 px | −0.001 [−0.007, +0.008] |
| `snapr1` (do not slot; dominated) | `releases/h33-h33-2-b2-snapr1-20261023-adefae6a-zeros.tif` | `adefae6a6ab19370141b25ecbd5fa2ac575138e5195ce0b49e4506ab44c59e04` | `ca91076ae31e2ca266d4f5bfe8f34981bd790133295bf1051de2b6eecf34a5aa` | 96.89 % / 0.97 px | −0.002 [−0.008, +0.003] |
| `snapr2` (dose instrument; slot only after an r2g10 receipt ≥ +0.010) | `releases/h33-h33-2-b2-snapr2-20261023-4d3834c9-zeros.tif` | `4d3834c9b86c3b896a9fd88d0be03428b0917f36ab64ec42e72d75804035fe7d` | `771d0ba35f1df5857b70593119645a986261a49fe96cbd19308f1d687cf880fe` | 98.41 % / 1.77 px | −0.006 [−0.018, +0.006] |

- Submission name (r2g10): `h33-h33-2-b2-snapr2g10-20261023-8ca1d869`
- Form note (**91 chars**): `R0 h33-h33-2-b2 SNAP r2g10: dots <=2px to edge if gain>=0.10, 37654 dots; pred -0.001 MODEL`
- Ledger `% changed` for SNAP counts changed *cells* (a moved dot = 2 cells): r2g10 34.94 %,
  r1 193.78 %, r2 196.82 %; the axis dose is `% dots moved` above (brief §5 exempts SNAP from
  the 1–50 % change rule).

**Do not upload:** `…-prune3-…-3eb29af5` (withdrawn, IR-86-PRUNE-08),
`…-prune3-…-01d57649` (same `(PRUNE, 3)` pair as slot 1), or either SNAP
unconditional variant under any currently foreseen outcome.

## Format receipt (measured on disk, brief §6 MUST gates — SNAP twins, this session)

| Gate | Measured (all 6 SNAP files) |
|---|---|
| Bands / dtype | 1 / `float32` |
| CRS | `EPSG:32611` (= `sample_submission.tif`) |
| Shape | 3730 × 3292 |
| Transform | `(100, 0, 243350, 0, -100, 4508550)` (= template) |
| Values | inside `[0,1]`, unit mass where emitted; 37,654 dots each (= R0) |
| NaN inside footprint | none |
| Outside footprint | `NaN` in the spec twin, `0` in the `-zeros` twin |
| Dots on mapped catalogue | **0**; min catalogue distance 2.236 px (parent exclusion kept) |
| Exact-hash duplicate (ledger or disk) | none |
| Vendored `gems57.validate` on `-zeros` twins | `all_checks_passed = True` |

The `-nan` twins fail that vendored validator **by its all-finite policy** (NaN cells all lie
outside the footprint, per the brief; IR-86-PRUNE-07). If the portal rejects `-nan` on range,
upload the `-zeros` twin in the same slot attempt — identical dots. Re-run the gates any time:
`.venv/bin/python scripts/build_r0_snap.py --measure` and
`.venv/bin/python scripts/build_ledger.py --check`.

## After the score comes back

Write the receipt into `ledger/submissions.csv` (`receipt_score`, `date`, `receipt=Y`,
`evidence_class=RECEIPT`) and re-read `SLOT_PLAN.md` for what the number licenses. Any live
change under **0.01** is treated as no evidence.
