# Manual submission card — no automatic submission

**No slot is authorized.** The human submits manually from one registered entity and uploads one file only. `TOP_PUBLIC`, remaining weekly quota, R0's portal receipt, the confirmed deadline, and the accepted null encoding were not supplied. See [SLOT_PLAN.md](../SLOT_PLAN.md) before deciding. The stated R0 value `0.2778` is a **CLAIM**, not a receipt.

## Built candidate: PRUNE `3.75px` (not recommended as a first slot)

- **Primary spec file (NaN outside):** `releases/h33-h33-2-b2-PRUNE3p75-20261023-a90d5477.tif`
- **Primary SHA-256:** `a90d5477865ee3f65c84980a05d0722edb22fde51caa21f235d6c8b8cf423097` (348,902 bytes)
- **Fallback zeros file:** `releases/h33-h33-2-b2-PRUNE3p75-20261023-a90d5477-zeros.tif`
- **Fallback SHA-256:** `c1207ab8886b56415586bf3441fc5c86a4c49982dd7bf6ede0b36bc27d293e2c` (212,876 bytes)
- **Submission name:** `h33-h33-2-b2-PRUNE3p75-20261023-a90d5477`
- **Form note (86 characters):** `R0 h33-h33-2-b2; PRUNE <=3.75px, FIFO-BFS H19-5 refill; count fixed; pred -0.002 MODEL`
- **Prediction:** `-0.002 DTI (MODEL; pre-registered band -0.010..+0.006)`; not a score. Report-only SGMC delta is `-0.0040 MODEL`; catalogue hide/recover is `0.0000 PROXY` and contaminated by construction. Thus this is a mechanism experiment, not a win-probability favorite.
- **Parent:** R0 `h33-h33-2-b2`, 37,654 dots, SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`; rebuilt from its pinned base and catalogue with identical dots and bytes.
- **Parent difference:** 3,361 dots removed and 3,361 refilled; 6,722 cells in the symmetric difference (**17.8520%** of parent count); count fixed at 37,654. Every candidate dot is at least 4 px from catalogue pixels.

## Format receipt

Both variants were written and re-read from disk against `data/bridge/sample_submission.tif`:

- CRS `EPSG:32611`; shape `3730 × 3292`; one `float32` band; transform `(100, 0, 243350, 0, -100, 4508550)`; values are unit mass `{0,1}` in the footprint.
- NaN spec form: finite `[0,1]` values inside, NaN outside, NaN nodata; zero catalogue mass.
- Zeros fallback: finite `[0,1]` values throughout, zeros outside; zero catalogue mass.
- Both have 37,654 dots and pass all recorded format/exclusion checks. Full receipts: `releases/h33-h33-2-b2-PRUNE3p75-20261023-a90d5477-zeros.json` and `evidence/prune375-run-card.json`.

Upload **only one** encoding, after confirming which null convention the portal accepts. TIFFs are gitignored/local-only while data-use terms remain unchecked. If a human submits, record the portal receipt score and date in `ledger/submissions.csv`; this agent never submits.
