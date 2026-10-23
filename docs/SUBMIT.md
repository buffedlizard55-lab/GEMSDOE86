# Manual submission card — no automatic submission

**Status: BUILT; not slot-approved.** TOP_PUBLIC, remaining quota and R0's submission receipt
were not supplied. The human alone submits, from one registered entity, one file per slot.
Full plan and decision tree: [SLOT_PLAN.md](../SLOT_PLAN.md). Release TIFFs are local-only and
gitignored (unchecked data-use terms); hashes below are the authority.

## Slot 1 — PRUNE≤3 + fixed-count H19-5 refill (built by PR #28)

- Candidate ID / submission name: `h33-h33-2-b2-prune3-20261023-01d57649`
- Primary (NaN outside): `releases/h33-h33-2-b2-prune3-20261023-01d57649.tif`
- SHA-256: `01d57649168d52a0bf2f9aced7aa2280a92b6fd7a0224757d5acc5e925785e96`
- Fallback (zeros outside): `releases/h33-h33-2-b2-prune3-20261023-01d57649-zeros.tif`
- Fallback SHA-256: `4131e37133a3c5a874c42fb7c975ec4ecb7b4be946b794ff9c9852afa575e225`
- Form note (107 chars): `R0 h33-h33-2-b2; PRUNE<=3px + BFS-ranked H19-5 refill, 37654 dots; predicted delta -0.004 MODEL; no receipt`
- Prediction: **−0.004 (MODEL)**. Format receipt: `evidence/r0-prune3-run-card.json`.

## Slot 2 — PRUNE≤4, pure deletion

- Candidate ID / submission name: `h33-h33-2-b2-prune4-20261023-e198b768`
- Primary (NaN outside): `releases/h33-h33-2-b2-prune4-20261023-e198b768-nan.tif`
- SHA-256: `e198b768b5a19d7e08e33de14ad1ec03425154db1acd81fad5db3b4b7e9715cd`
- Fallback (zeros outside): `releases/h33-h33-2-b2-prune4-20261023-de4c2a98-zeros.tif`
- Fallback SHA-256: `de4c2a98bd13c518697442655c0a3980ba51d6712216c2ea0e330dc01924ebc5`
- 33,829 dots, 10.16 % of R0 changed, zero catalogue mass, min catalogue distance 4.12 px.
- Form note (111 chars): `prune4 — parent h33-2-b2 (0.2778); drop 3825 dots at 2<d<=4px from catalogue; predicted -0.008 (MODEL, +-0.014)`
- Prediction: **−0.008 (MODEL)**. Format receipt: `evidence/prune_axis_20261023.json`.

## Slot 3 — PRUNE≤3r, equal count, collar relocated past 3 px

- Candidate ID / submission name: `h33-h33-2-b2-prune3r-20261023-9542efac`
- Primary (NaN outside): `releases/h33-h33-2-b2-prune3r-20261023-9542efac-nan.tif`
- SHA-256: `9542efacb60a4e8c9155b1e9c000ce7e33f43f7e413ad2a5883304b413906682`
- Fallback (zeros outside): `releases/h33-h33-2-b2-prune3r-20261023-8c20bd7e-zeros.tif`
- Fallback SHA-256: `8c20bd7eeaf1a1518b7d7f4711613169bd1ab00c4a4b3d74c87bf2b70d552c2e`
- 37,654 dots (count held), 11.53 % of R0 changed, mean relocation 1.14 px.
- Form note (113 chars): `prune3r — parent h33-2-b2 (0.2778); same count, collar moved past 3px, mean move 1.14px; predicted -0.003 (MODEL)`
- Prediction: **−0.003 (MODEL)**. Format receipt: `evidence/prune_axis_20261023.json`.

**Do not spend a slot on** `h33-h33-2-b2-prune3-20261023-3eb29af5` (pure deletion, 35,483 dots):
it duplicates the `(PRUNE, 3)` pair already spent on slot 1 (IR-86-PRUNE-08). It stays as the
local deletion-side control for slot 3.

## Format receipt (measured on disk, brief §6 MUST gates)

Common to every file above — re-read from disk after writing:

| Gate | Measured |
|---|---|
| Bands / dtype | 1 / `float32` |
| CRS | `EPSG:32611` (= `sample_submission.tif`) |
| Shape | 3730 × 3292 |
| Transform | `(100, 0, 243350, 0, -100, 4508550)` (= template) |
| Values | inside `[0,1]`, unit mass where emitted |
| NaN inside footprint | none |
| Outside footprint | `NaN` for `-nan` files, `0` for `-zeros` files |
| Dots on mapped catalogue | **0** in every file |
| Exact-hash duplicate of any file on disk or in the ledger | none |

The three `-zeros` twins additionally pass `vendor/gems57/validate.py`
(`all_checks_passed = True`) and `gems57.gates.format_report` (`ok = True`). The `-nan` twins
fail that vendored validator **by its all-finite policy** — their NaN cells all lie outside the
footprint, which is what the brief asks for (IR-86-PRUNE-07). The portal previously rejected an
upload with *"Predicted values must be in range [0, 1]"*, so if `-nan` is rejected on range,
switch to the `-zeros` twin within the same slot attempt: the twins carry identical dots.

Re-run the checks any time: `python scripts/prune_collar.py --measure` (deterministic, fixed
seed 20261023 → byte-identical files) and `python scripts/build_ledger.py --check`.

## After the score comes back

Write the receipt into `ledger/submissions.csv` (`receipt_score`, `date`,
`evidence_class=RECEIPT`, `receipt=Y`) and re-read `SLOT_PLAN.md` for what the number licenses.
Any live change under **0.01** is treated as no evidence.
