# SLOT PLAN — current, 2026-10-23

**No automatic upload, score claim or final submission.** R0 is `h33-h33-2-b2` / GEMSDOE32
`h33-h33-2-b2-20261004-e5eb6e7e`, 37,654 dots; `0.2778` is a **CLAIM**, not an authenticated
receipt. `TOP_PUBLIC`, slots left and deadline confirmation are **UNSUPPLIED**; 2026-12-03 remains
**UNVERIFIED**. R0 was rebuilt byte-exactly (`evidence/r0_preflight_20261023.json`).

## Next three slots — ranked proposals, none auto-approved

| Order | Candidate / file | Prediction and read | Decision |
|---|---|---|---|
| 1 | **PRUNE `le3p000`** — `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | `+0.004` MODEL; band `−0.004…+0.013` | Best conservative collar test on off-support mass; **no evidence** (<0.01) |
| 2 | **CONCENTRATION `b1km-move15`** — `releases/axis86/gems86-h33-2b2-conc15-20261023-2b883f2d-zeros.tif` | `+0.006` MODEL; range `+0.003…+0.010`; 1 km CV `0.6235→0.7644` | Largest positive un-receipted MODEL read; geometry conflicts with the `0.51–0.59` CV CLAIM; **no evidence** |
| 3 | **SPACING `strike16`** — `releases/axis86/gems86-h33-2b2-sp-strike16-20261023-caffc3f0-zeros.tif` | `+0.0020` MODEL; band `+0.0020…+0.0050`, 3/4 quadrants positive | Dose test only against sibling `random16` control (`+0.0002`); **no evidence** |

RELIEF `frontp15` (`+0.0017` MODEL) is the alternative to slot 2, not an additional automatic
pick. Zero ledger rows from this session have a score or receipt; the human decides whether any
proposal justifies scarce weekly capacity.

## This session — CONCENTRATION at 5 km: built, not slot-recommended

| Value | Dots moved / parent cells changed | SGMC Δ (MODEL; translation range) | Complete-block CV | Slot |
|---|---:|---|---:|---|
| `b5km-move10` | 3,765 / 19.998% | `−0.0066` (`−0.0073…−0.0057`) | `0.7442→0.9006` | **NO** |
| `b5km-move15` | 5,648 / 29.999% | `−0.0109` (`−0.0111…−0.0090`) | `0.7442→1.0113` | **NO** |
| `b5km-move20` | 7,531 / 40.001% | `−0.0150` (`−0.0151…−0.0118`) | `0.7442→1.0798` | **NO** |

All 3 have exact R0 parent, fixed count, zero catalogue mass, new-mass clearance 3.162 px,
unseen hashes and PASS re-read gates; both NaN-outside and zeros-outside twins exist locally.
The recovery diagnostic is **PROXY only**: parent `0.0286 [0.0240,0.0333]` versus
`0.0408 / 0.0427 / 0.0441` (`n=11,321` withheld positive pixels; paired 15% Δ
`+0.0141 [0.0072,0.0234]`). It conflicts with SGMC and with **0% of every arm's added cells on
H19-5 support**. Do not use that PROXY to promote these files. Leakage canary PASS, max AUC
0.5409. Full receipts: `evidence/concentration5_axis_20261023.json`.

## Calendar and better axes (proposals only, not built)

- **Wk1–2:** use the ranked tests above only with human quota/receipt confirmation. **Wk3–4:**
  combine only two axes with ≥0.01 receipt evidence and choose only with a dated receipt.
- **Wk5–6:** confirm the leading tested format and record the final-fallback choice; do not invent
  a deadline or claim a combined effect from unpaired single-axis reads.
- **Better axis 1:** support-constrained block allocation—keep every destination on H19-5;
  confounder: support is already saturated, falsifier: too few eligible cells or a negative receipt.
- **Better axis 2:** exact-marginal collar PRUNE—hold dot count rather than rank mass fixed;
  confounder: replacement placement, falsifier: >1% count drift or any catalogue mass.
- **Better axis 3:** coherent local SNAP—apply one signed rotation to a contiguous eligible patch;
  confounder: patch selection, falsifier: unchanged single-cell pixel prior or negative control.

**Human inputs still needed:** current `TOP_PUBLIC`, remaining rolling-week slots, actual receipts
for any newly tested file, and the verified final deadline. No new axis choice is requested.
