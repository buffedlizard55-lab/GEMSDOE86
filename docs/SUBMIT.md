# Manual submission card — no automatic submission

**Status: BUILT; not slot-approved.** `TOP_PUBLIC`, the remaining quota and R0's submission receipt
were not supplied. The human alone submits, from one registered entity, one file per slot.
Plan, decision rules and calendar: [SLOT_PLAN.md](../SLOT_PLAN.md). Release TIFFs are local-only and
gitignored (unchecked data-use terms, IR-86-PRUNE-04); the digests below are the authority, and
`releases/<id>-zeros.json` carries each file's full receipt.

This session's AXIS is **RELIEF**, assigned by the human (brief v2 §1). Three gate-clean files
exist; all three keep R0's count at **37,654 dots**, so none of them is a mass test.

## Slot 1 — `RELIEF front+15pct` (primary candidate)

- File: `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif`
- SHA-256: `e0e2888f98156e34347bbeb928c978590bf0cf0fa1ecd698719fc6dd8d31ea47` (214,315 bytes)
- Submission name (64 ch): `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f`
- Note (124 ch): `R0 h33-h33-2-b2-20261004-e5eb6e7e; RELIEF front+15pct: 5648 dots moved piedmont->range-front, count fixed; pred +0.002 MODEL`
- What it is: 5,648 dots (15.00 % of the mass) moved from the deep middle relief tercile onto the
  basin-margin range front; range-front share 16.05 % → 31.05 %.
- Prediction: **+0.0017 (MODEL)**, surrogate quadrant range −0.0022…+0.0112, 3/4 quadrants — below
  the 0.01 evidence floor. Receipts: `evidence/relief_axis_20261023.json`,
  `releases/…-e0e2888f-zeros.json`. Mechanism card: `ledger/variant-cards.md` §"RELIEF".

## Slot 2 — PRUNE ≤ 3.000 px (orthogonal edit, already built by PR #29)

- File: `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif`
- SHA-256: `a438e92b79dfb7f9f1763c40ffb2d42dd60e45697dfc06fc49efae067d3c1a22`
- 35,483 dots (R0 minus all 2,171 dots within 3.0 px of the catalogue), 5.77 % changed,
  **+0.004 (MODEL)**, band −0.004…+0.013. Kept as slot 2 because it is a *deletion* while slot 1
  is a *relocation*: the two results are additive rather than redundant.

## Slot 3 — `RELIEF front−10pct` (the sign flip; only if slots 1–2 are both inside ±0.01)

- File: `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontm10-20261023-1b26223e-zeros.tif`
- SHA-256: `1b26223ec7888a78b4c7b6ef78c9680ae29491691ab3e5ed0c53083f10450669` (218,597 bytes)
- Submission name: `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontm10-20261023-1b26223e`
- Note: `R0 h33-h33-2-b2-20261004-e5eb6e7e; RELIEF front-10pct: 3765 dots moved range-front->piedmont, count fixed; pred -0.009 MODEL`
- 3,765 dots moved the other way (front 16.05 % → 6.06 %); **−0.0089 (MODEL)**, sign negative in
  4/4 quadrants. Its value is the *paired* read against slot 1 (~0.011 predicted separation, a
  25 %-of-mass swing) — the only RELIEF comparison that can clear the evidence floor.

## Also built, not a slot candidate

| Variant | `-zeros` SHA-256 | Spec `.tif` (NaN outside) SHA-256 | Note |
|---|---|---|---|
| `RELIEF front+10pct` `…-b20ef72e` | `b20ef72e9f18fffe16f292db9e3ea517963b85be3dcf8469939e93e604f955ad` | `17588fe574701c788540f5d28f7d7b380279e15c615986b848f300acc15a2ab4` | the nested middle rung (3,765 dots, +0.001 MODEL); designated fallback if a smaller first edit is preferred |
| `RELIEF front+15pct` spec form | `b9a28caa5656ea0cf9e9789b0cda60562e4202e37c3cfa8e0ebfe3dbe0185f45` | — | same dots as slot 1, NaN outside the footprint |
| `RELIEF front−10pct` spec form | `9e267a10fe5abfcd4092ac8f1dc390876a4619b59b72ed08c4ff9bc7b63f0186` | — | same dots as slot 3 |
| PRUNE ≤ 4 px / relocated collar | `de4c2a98…` / `8c20bd7e…` | `e198b768…` / `9542efac…` | rehearsals, both predicted negative (−0.008 / −0.003 MODEL) |

**Do not upload:** `…-prune3-…-3eb29af5` (withdrawn — its dot set is slot 2's, IR-86-PRUNE-08),
`…-prune3-…-01d57649` (same `(PRUNE, 3)` pair, refill-confounded per IR-86-LADDER-01), or
`…-CONTROL-massctl2171…` (a control).

Naming convention, same as PR #29: the release id carries the **`-zeros`** digest's sha8, the
primary upload is `…-<sha8>-zeros.tif`, the spec form is `…-<sha8>.tif`, and the receipt is
`…-<sha8>-zeros.json`. Upload **one** file per slot.

## Format receipt (measured on disk after writing, brief §6 MUST gates)

Re-verified on the three RELIEF files in this session, per file, by re-reading the written bytes:

| Gate | Measured |
|---|---|
| Bands / dtype / CRS | 1 / `float32` / `EPSG:32611` (= `sample_submission.tif`) |
| Shape / transform | 3730 × 3292, `(100, 0, 243350, 0, -100, 4508550)` = template |
| Values | all finite in `-zeros`, inside `[0,1]`, exactly `1.0` at emitted dots, `0.0` elsewhere |
| NaN inside footprint | none (7,111,787 NaN cells in the spec form are all **outside** it, which is what the brief asks for) |
| Dots on mapped catalogue | **0** in every file |
| Distance of *newly emitted* mass to catalogue | ≥ 3 px (3,765–5,648 inserted cells each) |
| Dot count vs parent | 37,654 → 37,654 (`count_fixed` asserted in the builder, not assumed) |
| Min dot spacing vs parent | 2.8284 px → 2.8284 px (the parent's own minimum is preserved; see IR-86-RELIEF-01) |
| `%` of parent's dots changed | 15.00 / 10.00 / 10.00 — inside the 1–50 % contract, recorded per row |
| Exact-hash duplicate in ledger / fleet / site downloads | none (checked against every sha256 in `ledger/submissions.csv`, `data/scored_fleet/`, `docs/downloads/`) |
| Shared gates | `gems57.validate` → `all_checks_passed = True`; `gems57.gates.format_report` → `ok = True` on every `-zeros` twin |
| Re-read from disk | yes: the dot set in the bytes is compared cell-by-cell with the in-memory set (`re-read raster does not match` aborts the build) |

Uniqueness thresholds (rank-correlation / dot-overlap) were **not** applied, per brief v2 §6; the
repo's contrary 70 % rule and the pinned positive witness behind it are recorded in
IR-86-PRUNE-01 and were not modified, relaxed or bypassed. The report-only instruments (SGMC
surrogate = MODEL, catalogue hide-and-recover PROXY, leakage canaries with worst single-feature
AUC **0.7328** < 0.90) are in `evidence/relief_axis_20261023.json`; none of them gates a file.

Re-run everything any time (needs the pinned inputs; ~3 min):

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-lock.txt
python3 scripts/restore_data.py --with-external          # 419 MB stack + 5 externals, sha256-verified
.venv/bin/python scripts/run_relief_axis.py --no-write   # parent gate + measurements, writes nothing
.venv/bin/python scripts/build_ledger.py --check
```

## After the score comes back

Write the receipt into `ledger/submissions.csv` (`receipt_score`, `date`, `receipt=Y`,
`evidence_class=RECEIPT`) — or into `ledger/variants.json` and re-run
`python scripts/build_ledger.py`, which regenerates the CSV — then re-read `SLOT_PLAN.md` for what
the number licenses. Any live change under **0.01** is treated as no evidence, and a PROXY or MODEL
number is never a score.
