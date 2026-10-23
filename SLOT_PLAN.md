# SLOT PLAN — current, 2026-10-23 (merged through CONCENTRATION sign + 5 km arms)

**No automatic upload, score claim or final submission.** R0 is `h33-h33-2-b2` / GEMSDOE32
`h33-h33-2-b2-20261004-e5eb6e7e`, 37,654 dots; `0.2778` is a **CLAIM**, not a receipt. `TOP_PUBLIC`,
slots left and deadline confirmation are **UNSUPPLIED**; 2026-12-03 remains **UNVERIFIED**.
R0 was rebuilt byte-exactly (`evidence/r0_preflight_20261023.json`). A live `|Δ| < 0.01` is no evidence.

## Next three slots — ranked proposals, none auto-approved

| Order | Candidate / zeros-outside file | MODEL read and purpose | Decision |
|---|---|---|---|
| 1 | **CONCENTRATION `dens15`** — `releases/sign86/gems86-h33-2b2-concdens15-20261023-f8e7ae42-zeros.tif` | `+0.026` (`−0.011…+0.047`), count fixed; positive half of the sign experiment | Largest positive magnitude, but uncalibrated; read with slot 2 |
| 2 | **CONCENTRATION `spr15`** — `releases/sign86/gems86-h33-2b2-concspr15-20261023-6d452f96-zeros.tif` | `−0.030` (`−0.064…+0.011`), count fixed; paired separation ≈`0.056` | Most informative sign test; if both land flat, close this catalogue-prior direction for Phase 1 |
| 3 | **PRUNE `le3p000`** — `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | `+0.004` (`−0.004…+0.013`); historical `0.2708→0.2778` direction is CLAIM only | Different-axis collar test; mass-changing MODEL is confounded; **no evidence** |

The sign pair ranks first because it buys the largest decision separation, not because its numbers
are scores. Its five truth models are uncalibrated (parent DTI 0.050–0.107 versus 0.2778 CLAIM).
RELIEF `frontp15/frontm10` is the fallback pair; SPACING `strike16` (+0.0020) is a later probe.
`rand15` is a control, never a slot. TRACKB is descriptive/flat; MASS is closed; SNAP is negative.

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
H19-5 support**. Do not use that PROXY to promote these files. Leakage canary PASS, max AUC 0.5409.
This demotes these specific 5 km high-prior files behind the 1 km sign pair; it does **not** prove
that every concentration sign is negative. Full receipts: `evidence/concentration5_axis_20261023.json`.

## Other decision-changing merged evidence

- **MASS-econ:** random −20/−10/−5/+5/+10/+20% arms read `−0.0127 / −0.0068 / −0.0030 /
  +0.0018 / +0.0040 / +0.0081` MODEL—strictly count-monotone. Count-fixed comparisons cancel this
  bias; mass-changing ones do not. Only 733 of 121,131 H19-5 support cells are ≥3 px from R0.
- **TRACKB:** R0 has 300 traces ≥1 km versus 0 in a uniform same-count field, but relocation is
  capacity-limited and predicted flat (`+0.0004 / +0.0008 / −0.0007` MODEL), not a slot case.

## Calendar and better axes (proposals only, not built)

- **Wk1–2:** sign pair only with human quota/receipt confirmation. **Wk3–4:** PRUNE or a fallback
  pair; combine only axes with ≥0.01 receipt evidence. **Wk5–6:** confirm the leading tested format
  and final fallback; never infer a combined effect from unpaired MODEL reads or invent a deadline.
- **Support-bounded de-cluster:** relocate within each source block; confounder: CV is invariant;
  falsifier: flat with `strike16` also flat, closing arrangement-only explanations.
- **Prior-mixture, support-constrained allocation:** require catalogue prior and H19-5 agreement;
  confounder: shared lineage/circular support; falsifier: no separation from `rand15`.
- **Coverage-matched PRUNE:** delete only fully redundant kernel coverage; confounder: fringe
  selection; falsifier: coverage loss or live ≤−0.005 with PRUNE flat.

**Human inputs still needed:** current `TOP_PUBLIC`, remaining rolling-week slots, actual receipts
for any newly tested file, and the verified final deadline. No new axis choice is requested.
