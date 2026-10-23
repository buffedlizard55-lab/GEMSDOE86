# SLOT PLAN — current, 2026-10-23 (merged through TRACKB + 5 km CONCENTRATION)

**No automatic upload, score claim or final submission.** R0 is `h33-h33-2-b2` / GEMSDOE32
`h33-h33-2-b2-20261004-e5eb6e7e`, 37,654 dots; `0.2778` is a **CLAIM**, not a receipt. `TOP_PUBLIC`,
slots left and deadline confirmation are **UNSUPPLIED**; 2026-12-03 remains **UNVERIFIED**.
R0 was rebuilt byte-exactly (`evidence/r0_preflight_20261023.json`). A live `|Δ| < 0.01` is no evidence.

## Next three slots — ranked proposals, none auto-approved

| Order | Candidate / zeros-outside file | MODEL read and purpose | Decision |
|---|---|---|---|
| 1 | **RELIEF `frontp15`** — `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif` | `+0.0017`, count fixed; positive half of one paired allocation experiment | Do not interpret alone as a gain; read with slot 2 |
| 2 | **RELIEF `frontm10`** — `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontm10-20261023-1b26223e-zeros.tif` | `−0.0089`, count fixed; predicted paired separation ≈`0.0106` | Only above-floor comparison; if both land flat, RELIEF closes for Phase 1 |
| 3 | **CONCENTRATION `b1km-move15`** — `releases/axis86/gems86-h33-2b2-conc15-20261023-2b883f2d-zeros.tif` | `+0.006` (`+0.003…+0.010`), count fixed; CV `0.6235→0.7644` | Largest positive single-arm count-fixed read; CV CLAIM conflict remains; **no evidence** |

PRUNE `le3p000` is demoted: the merged MASS audit shows SGMC MODEL is monotone in dot count, so its
mass-changing `+0.004` is partly a mass reading. SPACING (`strike16 +0.0020`, law-minus-control
≈`+0.0018`) and TRACKB (`+0.0004 / +0.0008 / −0.0007`) are below-floor probes, not current slots.
MASS is closed in both directions; SNAP remains negative. No ledger row has a new score or receipt.

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

## Other decision-changing merged evidence

- **MASS-econ:** random −20/−10/−5/+5/+10/+20% arms read `−0.0127 / −0.0068 / −0.0030 /
  +0.0018 / +0.0040 / +0.0081` MODEL—strictly count-monotone. Count-fixed comparisons cancel this
  bias; mass-changing ones do not. Only 733 of 121,131 H19-5 support cells are ≥3 px from R0.
- **TRACKB:** R0 has 300 traces ≥1 km versus 0 in a uniform same-count field, but relocation is
  capacity-limited and predicted flat. This is descriptive evidence, not a slot case.

## Calendar and better axes (proposals only, not built)

- **Wk1–2:** RELIEF pair only with human quota/receipt confirmation. **Wk3–4:** 1 km CONCENTRATION;
  combine only axes with ≥0.01 receipt evidence. **Wk5–6:** confirm the leading tested format and
  final fallback; never infer a combined effect from unpaired MODEL reads or invent a deadline.
- **Support-constrained block allocation:** keep every destination on H19-5; confounder: saturated
  support; falsifier: insufficient eligible cells or a negative receipt.
- **Coverage-matched PRUNE:** delete only mass whose kernel coverage is fully redundant; confounder:
  fringe selection; falsifier: coverage loss or live ≤−0.005 with PRUNE flat.
- **Coherent local SNAP:** one structure-tensor-signed move on a contiguous patch; confounder:
  elongated non-fault contacts; falsifier: no separation from its random control on two folds.

**Human inputs still needed:** current `TOP_PUBLIC`, remaining rolling-week slots, actual receipts
for any newly tested file, and the verified final deadline. No new axis choice is requested.
