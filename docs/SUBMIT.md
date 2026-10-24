# Manual submission card — no automatic submission

**Status: BUILT; not slot-approved.** `TOP_PUBLIC`, remaining quota and R0's submission receipt
were not supplied. The human alone submits, from one registered entity, one file per slot.
Full plan and decision tree: [SLOT_PLAN.md](../SLOT_PLAN.md). Release TIFFs are local-only and
gitignored (unchecked data-use terms); hashes below are the authority.

## 2026-10-23 session 3 (`arena/aee7c83d`) — CONCENTRATION surface extension: **probe only, does not change the slot order**

R0 (`c55bafc4…`) and the merged `concb5kmdown4` (`8aab97b6…`) were both rebuilt byte-exactly from the
restored pinned inputs before building. Three count-fixed files move dots off the **saturated** `H19-5`
surface (90 legal free slots left there) onto unused `H19-4 | H16-1` ground (8,671 legal slots, zero
parent mass). All MUST gates passed after a disk re-read of both encodings; canary max AUC 0.5154.

| Role | Upload path (one file per slot) | Form name (≤ 64 ch) | Form note (≤ 140 ch) | `-zeros.tif` sha256 |
|---|---|---|---|---|
| probe only | `releases/h33-h33-2-b2-20261004-e5eb6e7e-CONC-surfext10-20261023-fe814da5-zeros.tif` | `h33-h33-2-b2-20261004-e5eb6e7e-CONC-surfext10-20261023-fe814da5` | `R0 h33-h33-2-b2-20261004-e5eb6e7e; CONC surface-ext to H19-4\|H16-1: 3765 dots moved (20.0% chg); pred +0.0059 MODEL` | `fe814da552360f752657f6fbd5825f74f52cbdcfda0437a118a2302412877737` |
| dose rung | `releases/h33-h33-2-b2-20261004-e5eb6e7e-CONC-surfext15-20261023-d3f2ecc7-zeros.tif` | `h33-h33-2-b2-20261004-e5eb6e7e-CONC-surfext15-20261023-d3f2ecc7` | `R0 h33-h33-2-b2-20261004-e5eb6e7e; CONC surface-ext to H19-4\|H16-1: 5648 dots moved (30.0% chg); pred +0.0073 MODEL` | `d3f2ecc74c39bc1eb91b0447f22ce50f4a2326c033d22b853f74f050e5d09c8d` |
| **CONTROL — never upload** | `…-CONC-surfext10ctl-20261023-b204c41b-zeros.tif` | `…-CONC-surfext10ctl-20261023-b204c41b` | `R0 …; CONC surface-ext to off-union same-block (CONTROL): 3765 dots moved; pred +0.0046 MODEL` | `b204c41b97daed3f72f133b06594999f180049a2c5c5d6ec16299a8e7ca58978` |

NaN-twin sha256: `b29549fc…982474` (surfext10), `68df2604…c223bd` (surfext15), `e9ef2b7c…c7dd10`
(control) — see each `releases/…-zeros.json`. Format receipt (both encodings, measured on the written
bytes): EPSG:32611, 3,730 × 3,292, single float32 band, transform
`(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`, values in {0, 1} inside the 5,167,373-cell footprint,
NaN (spec form) or 0 (`-zeros`) outside, 0 dots on catalogue pixels, 0 dots outside the footprint,
37,654 dots, added mass ≥ 3.1623 px from the catalogue, parent 2.8284 px spacing floor never tightened.
**Predicted live Δ ≈ 0.000…+0.003 (bracket [−0.002, +0.007]) — below the 0.01 floor; use only as the
spare-slot probe in [SLOT_PLAN.md](../SLOT_PLAN.md).**

## 2026-10-23 session (`arena/f29e1689`, PR #56) — pediment-window attribution: **audit only, never upload**

The pediment refinement of the dispersal rule was built and **fails its SGMC falsifier**
(`IR-86-CONC-18`): at the dose-matched 941 dots the non-pediment complement beats the pediment arm
(+0.0013 vs +0.0007 MODEL; REF `concb5kmdown4` +0.0015 replicated), the d28 `PROXY` orders oppositely
(+0.0012 vs +0.0004), and the truth-free pediment window caps at 1,045 moved dots. Slots are
unchanged. The three files below exist for audit only (all count-fixed 37,654, all MUST gates PASS,
zeros sha256 in each `-zeros.json`):

| Role | file (`releases/`) | `-zeros.tif` sha256 |
|---|---|---|
| **audit only — never upload** | `…-concb5kmpeddown2p5-20261023-9fb6bfc9-zeros.tif` | `9fb6bfc9…` |
| **audit only — never upload** | `…-concb5kmnonpeddown2p5-20261023-57cc867c-zeros.tif` | `57cc867c…` |
| **audit only — never upload** | `…-concb5kmpeddown5-20261023-161b002e-zeros.tif` | `161b002e…` |

## Slot order after the 2026-10-23 sessions (latest) — **supersedes everything below**

**Status: BUILT; not slot-approved.** No `RECEIPT` row exists for any file. Ordering logic, in one
line each: `PRUNE-le3p000` has the largest predicted lever and its Δrelief-index is ≈ 0, so the
instrument bias documented in `IR-86-RELIEF-04` cannot manufacture it; `conc6` is `+0.0022 MODEL`
with `+0.0013 PROXY` and `+0.0007` above its own random-ordering control, but two-thirds of its gain
is generic dispersal; `RELIEF-frontp15`'s `+0.0017` is the SGMC surrogate's own relief gradient
(residual `−0.0008`), so its unbiased prior is `0 ± 0.005`. One file per slot; log the receipt in
`ledger/submissions.csv` before the next upload.

| # | File (`releases/`) | Submission name (≤ 64 ch) | Note (≤ 140 ch) | zeros SHA-256 | bytes |
|---:|---|---|---|---|---:|
| 1 | `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b` | `R0 h33-h33-2-b2; PRUNE <=3.0px collar, 2171 dots removed (5.77%); pred +0.004 MODEL` | `a438e92b79dfb7f9f1763c40ffb2d42dd60e45697dfc06fc49efae067d3c1a22` | 210,325 |
| 2 | `h33-h33-2-b2-20261004-e5eb6e7e-conc6-20261023-1ed78e0f-zeros.tif` | `h33-h33-2-b2-20261004-e5eb6e7e-conc6-20261023-1ed78e0f` | `R0 h33-h33-2-b2; CONC cvband-down6: 2259 ridge dots moved (12.00% chg, 1km CV 0.484); pred +0.002 MODEL` | `1ed78e0f2106ecbd2eab07ce40a1d229b7e9bf19f433d8eaee0edcf867728c85` | 220,435 |
| 3 | `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif` | `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f` | `R0 h33-h33-2-b2; RELIEF front+15pct: 5648 dots piedmont->range-front, count fixed; pred +0.002 MODEL` | `e0e2888f98156e34347bbeb928c978590bf0cf0fa1ecd698719fc6dd8d31ea47` | 214,315 |

**The PRUNE and RELIEF TIFFs are not in this checkout** (gitignored, built by earlier sessions).
Rebuild them from their pinned recipes (`scripts/run_prune_ladder.py`, `scripts/run_relief_axis.py`)
and confirm the digests above before upload; only `conc6`'s twins are currently on disk here.

Format receipt for `conc6` (written and re-read from disk by `scripts/run_concentration_dose.py`):
CRS EPSG:32611 · 3,730 × 3,292 · single float32 band · transform `(100, 0, 243350, 0, -100, 4508550)`
· one band · values `{0,1}` inside the 5,167,373-cell footprint, `0` outside (fallback twin) or NaN
outside (spec twin `…-1ed78e0f.tif`, 356,859 B) · 0 dots on catalogue pixels · 0 dots outside the
footprint · 37,654 dots · shared validator `all_checks_passed = True` · format report `ok = True`.
Full per-file receipt: `releases/…-1ed78e0f-zeros.json` and
`evidence/concentration_dose_20261023.json`.

Also built this session, **do not upload**: `conc5dose` (10.00 % chg, +0.0018 MODEL),
`conc3` (6.00 % chg, +0.0013 MODEL), `conc6rand` (`CONTROL`, random dot + random destination).

---

## Superseded: current slot order after CONCENTRATION sign + 5 km arms

The count-fixed sign pair has the largest decision separation (≈0.056), but its five truth models
are uncalibrated and every number remains MODEL. The MASS instrument audit separately shows that
mass-changing reads are partly mass readings; neither audit licenses an automatic upload.

1. **CONCENTRATION `dens15`** — `releases/sign86/gems86-h33-2b2-concdens15-20261023-f8e7ae42-zeros.tif`
   (+0.026 MODEL, −0.011…+0.047; exact name/note/hash in the sign section below).
2. **CONCENTRATION `spr15`** — `releases/sign86/gems86-h33-2b2-concspr15-20261023-6d452f96-zeros.tif`
   (−0.030 MODEL, −0.064…+0.011). Slots 1+2 are **one sign experiment**, not two expected gains.
3. **PRUNE `le3p000`** — `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif`
   (+0.004 MODEL, mass-confounded; historical 0.2708→0.2778 direction is CLAIM only).

RELIEF `frontp15/frontm10` is the fallback pair. Original `b1km-move15` and SPACING are later
probes. The new 5 km arms are audit artifacts, not substitutes for the sign pair.

**The MASS-econ session's three files are NOT for upload** (mass-changing on an instrument that
cannot rank mass). If one is ever used, it must be `plus10pct-extend`, never the control:

| file (`releases/mass86/`) | name (≤ 64 ch) | note (≤ 140 ch) | zeros sha256 | bytes |
|---|---|---|---|---|
| `…-MASS-plus10pct-extend-20261023-3b708da1-zeros.tif` | `h33-h33-2-b2-MASS-plus10pct-extend-20261023-3b708da1` | `h33-h33-2-b2; MASS plus10pct-extend; 10.0% of dots changed; predicted 0.000 MODEL (below the 0.01 evidence floor)` | `cb42bd88…060a9b` | 325,286 |
| `…-MASS-minus10pct-marginal-20261023-c3936cfc-zeros.tif` | `h33-h33-2-b2-MASS-minus10pct-marginal-20261023-c3936cfc` | `h33-h33-2-b2; MASS minus10pct-marginal; 10.0% of dots changed; predicted 0.000 MODEL (below the 0.01 evidence floor)` | `c69123fd…` | 325,196 |
| `…-MASS-plus10pct-extend-rand-20261023-37fab392-zeros.tif` | **CONTROL — never upload** | `…extend-rand…` | `9070f274…` | — |

Format receipt for all three: `tools`-free local validation of the written bytes, both encodings —
CRS EPSG:32611, 3,730 × 3,292, single float32 band, transform `(100, 0, 243350, 0, -100, 4508550)`,
values in {0, 1} inside the 5,167,373-cell footprint, NaN (spec form) or 0 (fallback twin) outside,
0 dots on catalogue pixels, 0 dots outside the footprint. Full per-file receipt:
`evidence/mass_econ_axis_20261023.json` (`gates.*.read_back`), plus the `*.receipt.json` beside each
TIFF. Hashes above are the authority because the TIFFs are gitignored.

## Slot 3 — PRUNE ≤ 3.000 px (mass-confounded MODEL; nested ladder, PR #29)

- Submission name: `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros`
- Upload: `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif`
- SHA-256: `a438e92b…` — take the full digest from `releases/…-a438e92b-zeros.json`.
- 35,483 dots (R0 minus all 2,171 dots within 3.0 px of the catalogue), 5.77 % changed.
- Prediction: **+0.004 (MODEL)**, band −0.004 … +0.013. Receipt: `evidence/prune_ladder.json`.
- Nested rungs at ≤ 2.2361 px and ≤ 2.8284 px exist in the same ladder if the human prefers a
  shallower first edit.

## Fallback pair — RELIEF (`front+15pct` card; `front−10pct` below)

- File: `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif`
- SHA-256: `e0e2888f98156e34347bbeb928c978590bf0cf0fa1ecd698719fc6dd8d31ea47` (214,315 bytes);
  spec form (NaN outside) `b9a28caa5656ea0cf9e9789b0cda60562e4202e37c3cfa8e0ebfe3dbe0185f45`.
- Submission name (64 ch): `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f`
- Note (124 ch): `R0 h33-h33-2-b2-20261004-e5eb6e7e; RELIEF front+15pct: 5648 dots moved piedmont->range-front, count fixed; pred +0.002 MODEL`
- What it is: 5,648 dots (15.00 % of the mass) moved from the deep middle relief tercile onto the
  basin-margin range front — front share 16.05 % → 31.05 %, count fixed at 37,654, mean
  displacement 6.1 km. Regimes are terciles of `z(smoothed det_elev) + z(smoothed |det_elev_slope|)`
  from the pinned stack, with the top class split by 5 km basin proximity.
- Prediction: **+0.0017 (MODEL)** on a USGS SGMC hide-and-recover surrogate, quadrant range
  −0.0022…+0.0112, 3/4 quadrants — below the 0.01 evidence floor. The in-regime displacement control
  costs −0.0010, so the regime effect is only ~1.7× the cost of moving at all. Receipts:
  `releases/…-e0e2888f-zeros.json`, `evidence/relief_axis_20261023.json`; cards:
  `ledger/variant-cards.md` §"RELIEF".
- Two more RELIEF files are built and gated: `…-frontp10-20261023-b20ef72e-zeros.tif`
  (`b20ef72e9f18fffe16f292db9e3ea517963b85be3dcf8469939e93e604f955ad`, 10.00 %, +0.0010 MODEL, a
  strict prefix of the 15 % dose — the designated fallback if a smaller first edit is preferred) and
  `…-frontm10-20261023-1b26223e-zeros.tif` (`1b26223ec7888a78b4c7b6ef78c9680ae29491691ab3e5ed0c53083f10450669`,
  10.00 % the other way, **−0.0089 MODEL**, sign negative in 4/4 quadrants).
  Its note: `R0 h33-h33-2-b2-20261004-e5eb6e7e; RELIEF front-10pct: 3765 dots moved range-front->piedmont, count fixed; pred -0.009 MODEL`

## CONCENTRATION on 5 km blocks — BUILT, negative MODEL; no slot recommended

These are audit artifacts, not current upload recommendations. All three passed the mandatory
re-read gates, but SGMC is negative and dose-monotone and every added cell is off H19-5 support.
The positive catalogue-recovery result is **PROXY only**, not a score or a reason to upload.

| Value | Zeros-outside file | Submission name | Prediction note (exactly as generated) |
|---|---|---|---|
| `b5km-move10` | `releases/concentration5/h33-h33-2-b2-CONCENTRATION-b5km-move10-20261023-0d83c158-zeros.tif` | `h33-h33-2-b2-CONCENTRATION-b5km-move10-20261023-0d83c158` | `R0 h33-h33-2-b2; CONCENTRATION b5km-move10: 3765 dots low->high prior, count 37654; pred -0.0066 MODEL` (102 chars) |
| `b5km-move15` | `releases/concentration5/h33-h33-2-b2-CONCENTRATION-b5km-move15-20261023-c03272dc-zeros.tif` | `h33-h33-2-b2-CONCENTRATION-b5km-move15-20261023-c03272dc` | `R0 h33-h33-2-b2; CONCENTRATION b5km-move15: 5648 dots low->high prior, count 37654; pred -0.0109 MODEL` (102 chars) |
| `b5km-move20` | `releases/concentration5/h33-h33-2-b2-CONCENTRATION-b5km-move20-20261023-e121a2a4-zeros.tif` | `h33-h33-2-b2-CONCENTRATION-b5km-move20-20261023-e121a2a4` | `R0 h33-h33-2-b2; CONCENTRATION b5km-move20: 7531 dots low->high prior, count 37654; pred -0.0150 MODEL` (102 chars) |

**Format / twins / receipts:** each primary file has the same name without `-zeros` and is NaN-
outside; the listed twin is zeros-outside. All are one-band float32, 3,730×3,292, CRS `EPSG:32611`,
transform `(100, 0, 243350, 0, −100, 4508550)`, DEFLATE / predictor 3 / level 9 / 256 px tiles.
Count is 37,654, catalogue mass is zero, new-mass catalogue clearance is at least 3.162278 px,
and in-memory versus on-disk dot sets match. The 2,171 inherited R0 dots at 2–3 px are unchanged,
not silently pruned. Full SHA-256 values and both gate reports are in each adjacent `-zeros.json`
receipt and `evidence/concentration5_axis_20261023.json`; predictions and falsifiers are in
`evidence/concentration5-mechanism.md`. **Slots used: 0.**

## SPACING `strike16` — later below-floor probe, not in the current next three

The SPACING proposal is
`releases/axis86/gems86-h33-2b2-sp-strike16-20261023-caffc3f0-zeros.tif`, with exact name, note
and format receipt in the SPACING section below: **+0.0020 MODEL**, band +0.0020…+0.0050,
3/4 quadrants positive. Read it against `random16` (+0.0002), not against zero. It is below the
0.01 evidence floor and is not auto-approved.

### Alternative A: `RELIEF front−10pct`, predicted negative

(`…-frontm10-20261023-1b26223e-zeros.tif`, digested above). Its value is the *paired* read against
RELIEF slot-2 alternative: a 25 %-of-mass swing with predicted separation ~0.011. It is not the
current slot-3 recommendation.

### Alternative B: SNAP, built and gated, predicted negative

| Variant | Primary file (NaN outside) | sha256 (NaN twin) | Fallback (`-zeros`) | sha256 (zeros twin) | Prediction |
|---|---|---|---|---|---|
| `SNAP ≤ 1.0 px` mixed | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r1p000-20261023-0e09c2b7.tif` | `b8f215b3d858ad1efd6737ae19521deb6b700cd974f769d778251edc3b80c3d0` | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r1p000-20261023-0e09c2b7-zeros.tif` | `0e09c2b7800c302a7c840f0c38b3b3808f82eca242d7292d547f68a5098404be` | **−0.004 MODEL** (−0.012…+0.004) |
| `SNAP ≤ 2.0 px` mixed | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r2p000-20261023-e7473403.tif` | `c9f4042f71add006089f79634468488ed2b08183e0505a4174a688f9ee1e916b` | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r2p000-20261023-e7473403-zeros.tif` | `e74734031f478edafc55017d0002e72fe1930dd32c237c9341833732028f5743` | **−0.006 MODEL** (−0.020…+0.006) |
| `SNAP ≤ 2.0 px` gravity-only | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r2p000-grav-20261023-17fe2f15.tif` | `a9cc8fdadbcb31d7c8f19a2adeed56bf7034ac2633bdf64af7767f8023c23218` | `releases/h33-h33-2-b2-20261004-e5eb6e7e-SNAP-r2p000-grav-20261023-17fe2f15-zeros.tif` | `17fe2f1573bb35d557d5a6c79a52df743b211f57be0ed5888fbf0ef5dd1d9823` | **−0.004 MODEL** (−0.016…+0.006) |

Why they are predicted to lose: 97–99 % of dots move, but the random-response **null control**
scores the same catalogue proxy (+0.0001 vs −0.0012) and smoothing makes it worse. Uploading one
of these buys a test of an unmeasured *live* hypothesis — "new faults sit at potential-field
edges, not where the field put its dots" — not an expected gain. If the human does not want to
spend a weekly slot on a predicted-negative probe, skip slot 3 and go to slot 2.
Notes are 99–106 chars each and are stored inside each `-zeros.json` receipt as `note`.

## MASS variants — built and gated, **not recommended for a slot** (both predicted negative)

Upload, if the human overrules the default in [SLOT_PLAN.md](../SLOT_PLAN.md), the `-zeros`
twin; the `-nan` twin carries identical dots. TIFFs are local-only and gitignored.

| Variant | Primary file (NaN outside) | sha256 | Fallback (zeros) | sha256 |
|---|---|---|---|---|
| MASS −10 % (drop traversal-tail) | `releases/mass/h33-h33-2-b2-massminus10-20261023-42b4c5c8.tif` | `6614be7425dbbf00403ac8491fb38ab365d8947b26b759245f29197f5ab1abde` | `releases/mass/h33-h33-2-b2-massminus10-20261023-42b4c5c8-zeros.tif` | `42b4c5c8f7087b8699057d888bdd00c775c4812c8ed37b5abf6d1a351aae2779` |
| MASS +10 % (add next-ranked cells) | `releases/mass/h33-h33-2-b2-massplus10-20261023-a5888761.tif` | `45e8ac0aee4ca237552d6c71698b82f87698f566f03c6da7d9228917c58e8347` | `releases/mass/h33-h33-2-b2-massplus10-20261023-a5888761-zeros.tif` | `a5888761dd03239e21d71c125649f7da4bd4480ae1a83106854dd7cd49eef481` |

Form notes (≤140 chars): minus (107): `R0 h33-h33-2-b2 MASS-10%: drop 3765 lowest-priority
traversal-tail dots, 33889 left; predicted -0.003 MODEL`; plus (115): `R0 h33-h33-2-b2
MASS+10%: add 3765 next-ranked H19-5 cells, d>2px off catalogue, 41419 dots; predicted
-0.006 MODEL`. Re-verify any time: `.venv/bin/python scripts/build_mass_axis.py --measure`
(gates re-read from disk) and `.venv/bin/python scripts/build_ledger.py --check`.

## Cheap defaults, already built and gated (only if slot 2 is not ready)

| Variant | Primary file (NaN outside) | sha256 | Fallback (zeros) | sha256 |
|---|---|---|---|---|
| PRUNE ≤ 4 px | `releases/h33-h33-2-b2-prune4-20261023-de4c2a98.tif` | `e198b768b5a19d7e08e33de14ad1ec03425154db1acd81fad5db3b4b7e9715cd` | `releases/h33-h33-2-b2-prune4-20261023-de4c2a98-zeros.tif` | `de4c2a98bd13c518697442655c0a3980ba51d6712216c2ea0e330dc01924ebc5` |
| PRUNE ≤ 3 px, equal count relocated | `releases/refill/h33-h33-2-b2-prune3r-20261023-8c20bd7e.tif` | `9542efacb60a4e8c9155b1e9c000ce7e33f43f7e413ad2a5883304b413906682` | `releases/refill/h33-h33-2-b2-prune3r-20261023-8c20bd7e-zeros.tif` | `8c20bd7eeaf1a1518b7d7f4711613169bd1ab00c4a4b3d74c87bf2b70d552c2e` |

Predictions: PRUNE ≤ 4 px **−0.008 MODEL** (111-char note: `prune4 — parent h33-2-b2
(0.2778); drop 3825 dots at 2<d<=4px from catalogue; predicted -0.008 (MODEL, +-0.014)`);
relocated-collar **−0.003 MODEL** (113-char note: `prune3r — parent h33-2-b2 (0.2778); same
count, collar moved past 3px, mean move 1.14px; predicted -0.003 (MODEL)`). Neither is
predicted to help; they are rehearsals.

Naming note: the pair is named once — the NaN twin (`…-<zeros8>.tif`) carries the **zeros**
digest, the zeros twin is `…-<zeros8>-zeros.tif`, and the receipt is `…-<zeros8>-zeros.json`.

**Do not upload:** `…-prune3-…-3eb29af5` (withdrawn — identical dot set to slot 1's
`le3p000`, IR-86-PRUNE-08; its local copies are deleted) or `…-prune3-…-01d57649` (same
`(PRUNE, 3)` pair; a control for the mass question, not a candidate).

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
| SNAP parent-diff | count exact 37,654 → 37,654; only positions changed; catalogue exclusion unchanged (min distance 2.236 px) |
| RELIEF parent-diff | count fixed 37,654 → 37,654; deletions == insertions (5,648 / 3,765 / 3,765); every *inserted* cell ≥ 3 px off the catalogue; min dot spacing 2.8284 px → 2.8284 px (not tightened); mass on catalogue pixels 0 |
| RELIEF re-read | the dot set in the written bytes is compared cell-by-cell with the in-memory set; a mismatch aborts the build |

The `-zeros` twins additionally pass `vendor/gems57/validate.py` (`all_checks_passed = True`)
and `gems57.gates.format_report` (`ok = True`). The `-nan` twins fail that vendored validator
**by its all-finite policy** — their NaN cells all lie outside the footprint, which is what the
brief asks for (IR-86-PRUNE-07). The portal previously rejected an upload with *"Predicted
values must be in range [0, 1]"*, so if `-nan` is rejected on range, switch to the `-zeros`
twin within the same slot attempt: the twins carry identical dots.

Release TIFFs are gitignored (public repo, unchecked data-use terms), so the digests above are
the authority. Re-run the checks any time: `python scripts/prune_collar.py --measure` (deterministic, seed
20261023), `python scripts/run_snap_axis.py` (deterministic; rebuilds R0 byte-exactly, then the
three SNAP rasters — the sha8 values are reproducible),
`.venv/bin/python scripts/run_relief_axis.py --no-write` (parent gate + RELIEF measurements, writes
nothing; without `--no-write` it rebuilds the three RELIEF rasters) and
`.venv/bin/python scripts/build_ledger.py --check`.

## After the score comes back

Write the receipt into `ledger/submissions.csv` (`receipt_score`, `date`, `receipt=Y`,
`evidence_class=RECEIPT`) and re-read `SLOT_PLAN.md` for what the number licenses. Any live
change under **0.01** is treated as no evidence.

## Not slot candidates: the three magnetic-edge SNAP builds (2026-10-23, second session)

`releases/h33-h33-2-b2-snap-hg2-20261023-1ced061c*.tif`,
`…-snap-vg2-20261023-af1f0f2f*.tif` and `…-snap-cons2-20261023-fed241ac*.tif` are **gate-clean but
must not be uploaded**: the (R0, SNAP) pair was already spent by PR #31, and both builds read
negative (IR-86-SNAP-04). They exist as corroboration and as the record behind IR-86-SNAP-06 (the
proxy is catalogue-collar recovery). Ledger status: `BUILT-DUPLICATE`.

---

## Added by PR #37 (`arena/95e0ad6b`, CONCENTRATION session)

Two of this session's three builds are **duplicates** of arms already in the ledger and must not
be uploaded: `gems86-h33-2b2-prune3-20261023-e4027684` duplicates `(PRUNE,3)`, and
`gems86-h33-2b2-snap2-20261023-6ec42a92` duplicates `(SNAP,2)` — an arm whose own instrument reads
*negative* against a random-response null. Both are `BUILT-DUPLICATE` in
`ledger/submissions.csv`; they exist for audit only.

### Later alternative — CONCENTRATION, original 1 km `b1km-move15`

- **File:** `releases/axis86/gems86-h33-2b2-conc15-20261023-2b883f2d-zeros.tif`
  (nan-outside twin: `releases/axis86/gems86-h33-2b2-conc15-20261023-2b883f2d.tif`)
- **Name:** `gems86-h33-2b2-conc15-20261023-2b883f2d`
- **Note (107 chars):**
  `GEMSDOE86 h33-2b2 CONCENTRATION b1km-move15 | 37654 dots, 29.999% changed vs R0 | token 2b883f2d | UNSCORED`
- **Format receipt:** PASS, re-read from disk — single band, float32, EPSG:32611, 3730×3292,
  transform `|100, 0, 243350| |0, −100, 4508550|`, all values in [0, 1], no NaN inside the
  footprint, 0 outside-footprint mass, **0 dots on catalogue pixels**, minimum catalogue clearance
  2.236 px (the parent's own floor), 37,654 emitted cells.
- **SHA-256 (zeros twin, the ledger's `sha256`):**
  `09aaa696e1f0fce6ea010a0c125e64bf6df9a1dff18bcf547dffae94b928e6f5`
- **SHA-256 (nan twin):** `cf54e7578a9ecd5202a02c464e1142ca911eb88039af0a9f9db5e47d8915000e`
- **What it is:** 5,648 dots (15.00 %) moved out of the lowest-prior 1 km blocks into the
  highest-prior fifth (10,462 blocks), count fixed at 37,654, all placements at the parent's
  2.828 px spacing, placement geometric only. Block-density CV 0.6235 → 0.7644.
- **Prediction:** +0.006 MODEL (+0.003…+0.010). Not a score.
- **Where it sits in the plan:** a later alternative to `dens15`, outside the current next three.
  It is not auto-approved and has no receipt.

Release TIFFs are gitignored (data-use terms unchecked), so they exist only in this working copy;
the JSON receipts next to them carry the digests. Rebuild with the commands in `AI_USE.md`.

## Also not a slot candidate: the gain-gated SNAP build (2026-10-23, third session)

`releases/h33-h33-2-b2-snapr2g10-20261023-8ca1d869[-zeros].tif` (37,654 dots, 17.5 % moved
≤2 px, mean displacement 0.34 px; zeros sha256 `8ca1d8690aa835c8…82d2e`, NaN twin
`32c1e4e99444abaf…3f52`; **−0.001 MODEL**) is gate-clean but **must not be uploaded**:
SNAP was spent by PR #31, corroborated by PR #34, and this build's SGMC control is negative
with dose (IR-86-SNAP-09). Status `BUILT-DUPLICATE`; its `snapr1`/`snapr2` arms are
withdrawn duplicate pairs with **no raster**. Rebuild: `python scripts/build_r0_snap.py --build`.

## SPACING arms (built 2026-10-23, session `arena/c8365759-gemsdoe86`) — later probe, **not approved**

All four files are gated in both encodings and live in `releases/axis86/` (gitignored; the receipts
and the ledger are the authority). Count fixed at **37,654** dots, 19.20 % of R0's dots relocated,
`-zeros` twin = the fallback encoding (the two score identically per brief §3, so upload **one**).

| arm | upload (fallback twin) | zeros-twin sha256 | name (≤ 64 ch) | note (≤ 140 ch) |
|---|---|---|---|---|
| `strike16` (candidate) | `releases/axis86/gems86-h33-2b2-sp-strike16-20261023-caffc3f0-zeros.tif` | see `…-caffc3f0-zeros.json` | `gems86-h33-2b2-sp-strike16-20261023-caffc3f0-zeros` | `R0 h33-h33-2-b2; SPACING/strike16: 7027 redundant dots re-placed on their own ridge, count 37654 fixed, pred +0.0020 MODEL` |
| `pdisk16` (candidate) | `…/gems86-h33-2b2-sp-pdisk16-20261023-0d2f135e-zeros.tif` | see `…-0d2f135e-zeros.json` | `gems86-h33-2b2-sp-pdisk16-20261023-0d2f135e-zeros` | `R0 h33-h33-2-b2; SPACING/pdisk16: 7228 redundant dots to the largest local kernel gap, count 37654 fixed, pred +0.0015 MODEL` |
| `lattice16` (candidate) | `…/gems86-h33-2b2-sp-lattice16-20261023-63c4c56f-zeros.tif` | see `…-63c4c56f-zeros.json` | `gems86-h33-2b2-sp-lattice16-20261023-63c4c56f-zeros` | `R0 h33-h33-2-b2; SPACING/lattice16: 7220 dots on a hex covering lattice a=5.196px, count 37654 fixed, pred +0.0019 MODEL` |
| `random16` (control — do not submit) | `…/gems86-h33-2b2-sp-random16-20261023-db4cae83-zeros.tif` | see `…-db4cae83-zeros.json` | — | — |

**Format receipt (all four, re-read from disk after writing).** Validator:
`src/gems86_axis/gates.py` → `vendor/template66/gems/validate_submission.py` against
`data/bridge/sample_submission.tif`. CRS `EPSG:32611`, shape `[3730, 3292]`, transform
`(100, 0, 243350, 0, −100, 4508550)`, `float32`, single band, values in [0, 1], NaN outside the
footprint in the `.tif` and 0 outside in the `-zeros.tif`, **0 dots on catalogue pixels**, new mass
≥ 3.162 px off the catalogue (gate `new_mass_clearance` PASS), `sha256` absent from the ledger before
the build. The one SKIPPED validator check ("footprint checks", which needs the absent 419 MB feature
stack) is covered by `gates.value_gate`, as logged in `src/gems86_axis/gates.py:COVERED_SKIPS`.

**Before uploading:** re-read the exact bytes you upload through
`.venv/bin/python -c "from gems86_axis import gates, grid_io; ..."` or
`pytest tests/test_axis_releases.py -q` (it re-derives every gate from disk and fails on drift), and
rebuild the file from `scripts/build_r0_spacing.py` to confirm the dot-set token in the name.

## TRACKB (built this session, self-assigned axis — **no slot requested**)

- Files (local, gitignored): `releases/h33-h33-2-b2-20261004-e5eb6e7e-TRACKB-c15len1km-20261023-73f10581-zeros.tif`
  and the `.tif` spec twin; the two companion rungs are `…-TRACKB-c10len1km-…-b1e1caf1` and
  `…-TRACKB-c25len1km-…-831ce9cd` (same parent, same rules, corridor 1.0 / 2.5 px).
- Submission name / note: read both from the adjacent `-zeros.json` (`submission_name`, `note`);
  the note is `R0 h33-h33-2-b2-20261004-e5eb6e7e; TRACKB corridor 1.5 px, traces >=1 km, 1246 dots extended along strike; pred +0.001 MODEL`
  (135 characters, under the 140 limit).
- Prediction: **+0.0008 (MODEL)**, quadrant range +0.0004 … +0.0020 (4/4). Below the 0.01 evidence
  floor, so a slot buys a *Phase-2 probe*, not a Phase-1 bet. The `c25len1km` rung reads **−0.0007**.
- Trace geometry for a geologist: `releases/trackb/…-73f10581-traces.geojson` (300 strands, one
  `evidence_paragraph` property each). Local-only; the receipt records the 12 strongest.
- Do **not** upload two TRACKB files in one week, and only after slots 1–3 in `SLOT_PLAN.md`.

## CONCENTRATION sign experiment — three files, none slot-approved (2026-10-23)

Parent R0 `h33-h33-2-b2` (`c55bafc4…`, 37,654 dots). Each file relocates 5,648 dots (15.00 %) at
1 km blocks, count fixed, 29.999 % of cells changed, all placements at the parent's 2.828 px floor,
new mass ≥ 3 px off the catalogue. Cards: `evidence/concentration-sign-mechanism.md`; run card
`evidence/concentration_sign_20261023.json`. Format gate PASS on both twins of all three files
(template validator + values + catalogue clearance + new-mass clearance + hash-newness + re-read).

### `gems86-h33-2b2-concdens15-20261023-f8e7ae42` — candidate

- Upload (one file only): `gems86-h33-2b2-concdens15-20261023-f8e7ae42-zeros.tif`
- SHA-256: `f8e7ae4288b5cb8fc008cfe4bc4d97e09c39655a9af44b48176f7cc3f107ec2b` (314,048 bytes)
- Spec form (NaN outside): `gems86-h33-2b2-concdens15-20261023-f8e7ae42.tif`, `dc45662372ab4b6ab0c5fda791e1d9bb3db3f3bbc75c3beea4e827a53b175d7f` (366,803 bytes)
- Submission name (43 ch): `gems86-h33-2b2-concdens15-20261023-f8e7ae42`
- Note (83 ch): `R0 dens15: cluster-dense 15pct of dots at 1km blocks, count 37654, 30.00pct changed`
- 37,654 dots, 29.999 % of cells changed; gates passed: True.
- Prediction: see the ledger row for `gems86-h33-2b2-concdens15-20261023-f8e7ae42` (MODEL class, band crosses zero).

### `gems86-h33-2b2-concrand15-20261023-fcbae067` — control

- Upload (one file only): `gems86-h33-2b2-concrand15-20261023-fcbae067-zeros.tif`
- SHA-256: `fcbae067a4f3b34732a66648f6577bd502bdd680fbdf9393320b3d893ad2701c` (313,157 bytes)
- Spec form (NaN outside): `gems86-h33-2b2-concrand15-20261023-fcbae067.tif`, `f608e4e3299ecf0a85c102816d1962f0b1e6fecee4ee23666459f6c50713f992` (366,030 bytes)
- Submission name (43 ch): `gems86-h33-2b2-concrand15-20261023-fcbae067`
- Note (90 ch): `R0 rand15: CONTROL random-block 15pct of dots at 1km blocks, count 37654, 29.62pct changed`
- 37,654 dots, 29.622 % of cells changed; gates passed: True.
- Prediction: see the ledger row for `gems86-h33-2b2-concrand15-20261023-fcbae067` (MODEL class, band crosses zero).

### `gems86-h33-2b2-concspr15-20261023-6d452f96` — candidate

- Upload (one file only): `gems86-h33-2b2-concspr15-20261023-6d452f96-zeros.tif`
- SHA-256: `6d452f96eb7910ba82f48bb3a04816b034c82d4bb3f7e82da109d7da5c55f843` (310,477 bytes)
- Spec form (NaN outside): `gems86-h33-2b2-concspr15-20261023-6d452f96.tif`, `f72eb6a6c927dff74c882858b0f314294f9421875d4d968d8778fe1aaa4d04e3` (363,404 bytes)
- Submission name (42 ch): `gems86-h33-2b2-concspr15-20261023-6d452f96`
- Note (83 ch): `R0 spr15: cluster-spread 15pct of dots at 1km blocks, count 37654, 30.00pct changed`
- 37,654 dots, 29.999 % of cells changed; gates passed: True.
- Prediction: see the ledger row for `gems86-h33-2b2-concspr15-20261023-6d452f96` (MODEL class, band crosses zero).

## TRACKB hybrid & geologist dossier arms (built 2026-10-23, session `arena/ac0bd04f-gemsdoe86`) — Phase 2 (`slot_candidate: false` unless human decides)

Parent R0 `h33-h33-2-b2` (`c55bafc4…`, 37,654 dots). Paired with local RFC 7946 GeoJSON
`releases/trackb/gems86-h33-2b2-trackb-top120-20261023.geojson` (`sha256: 683111ac95943d25…`, 120
`>= 1 km` traces) and tracked geologist dossier `evidence/trackb-geologist-dossier.md` + run card
`evidence/trackb_hybrid_20261023.json`. Rebuild deterministically via `.venv/bin/python scripts/build_r0_trackb.py`.

### `gems86-h33-2b2-trackb-cull1dot-20261023-9bf9611c` — Phase 2 singleton-cull arm (not slot-recommended)

- Upload (fallback zeros-outside): `releases/axis86/gems86-h33-2b2-trackb-cull1dot-20261023-9bf9611c-zeros.tif`
- SHA-256 (`-zeros`): `74b7e4bc64e9f5f9982c0178d0e3c78223d9887837a1040b97fb9594b7d42989` (305,508 bytes)
- Spec form (NaN outside): `releases/axis86/gems86-h33-2b2-trackb-cull1dot-20261023-9bf9611c.tif`, `b743412b38871f4d98ba12961183457211579a0f12475fb83952efed76a9d844` (358,117 bytes)
- Submission name (49 ch): `gems86-h33-2b2-trackb-cull1dot-20261023-9bf9611c`
- Note (89 ch): `R0 TRACKB cull1dot: drop 3349 isolated 1-dot speckles (<550m); keep 100% >=1km traces`
- Format receipt: CRS `EPSG:32611`, `3730×3292` `float32`, `[0, 1]`, 0 NaNs inside footprint, 0 catalogue dots, 34,305 dots (`8.8941 %` changed), disk re-read gates PASS (`releases/axis86/gems86-h33-2b2-trackb-cull1dot-20261023-9bf9611c-zeros.json`).

### `gems86-h33-2b2-trackb-bridge1km-20261023-f23c9d77` — Phase 2 trace gap-bridging arm (not slot-recommended)

- Upload (fallback zeros-outside): `releases/axis86/gems86-h33-2b2-trackb-bridge1km-20261023-f23c9d77-zeros.tif`
- SHA-256 (`-zeros`): `ac908de81372c082f69cb03b4340fd9760542173712e94d9db96c3f627799686` (314,104 bytes)
- Spec form (NaN outside): `releases/axis86/gems86-h33-2b2-trackb-bridge1km-20261023-f23c9d77.tif`, `96d6ef0993f77d8a3f950f415599d7a89fb0706732d645df55d2ba6de59a742b` (366,789 bytes)
- Submission name (50 ch): `gems86-h33-2b2-trackb-bridge1km-20261023-f23c9d77`
- Note (84 ch): `R0 TRACKB bridge1km: move 3347 1-dot speckles to >=1km trace gaps/tips; S=37654`
- Format receipt: CRS `EPSG:32611`, `3730×3292` `float32`, `[0, 1]`, 0 NaNs inside footprint, 0 catalogue dots, new mass min catalogue distance `3.1623 px > 3.0 px`, 37,654 dots (`17.7777 %` changed), disk re-read gates PASS (`releases/axis86/gems86-h33-2b2-trackb-bridge1km-20261023-f23c9d77-zeros.json`).

### `gems86-h33-2b2-trackb-rendertop120-20261023-79ca1469` — Phase 2 continuous 120-trace hybrid arm

- Upload (fallback zeros-outside): `releases/axis86/gems86-h33-2b2-trackb-rendertop120-20261023-79ca1469-zeros.tif`
- SHA-256 (`-zeros`): `0cb962846977ddaa277007c70faaa1d8a8631094e3254a0d5c8478a35bcdfcf8` (314,019 bytes)
- Spec form (NaN outside): `releases/axis86/gems86-h33-2b2-trackb-rendertop120-20261023-79ca1469.tif`, `f1aef881445fedf7c980cf926296d83534cf9c32145b78b1b12e47de87fd0241` (366,640 bytes)
- Submission name (53 ch): `gems86-h33-2b2-trackb-rendertop120-20261023-79ca1469`
- Note (95 ch): `R0 TRACKB rendertop120: render 120 >=1km GeoJSON traces continuously (-1543 1-dot); S=37654`
- Format receipt: CRS `EPSG:32611`, `3730×3292` `float32`, `[0, 1]`, 0 NaNs inside footprint, 0 catalogue dots, new mass min catalogue distance `3.1623 px > 3.0 px`, all 120 GeoJSON traces verified pixel-for-pixel, 37,654 dots (`8.1957 %` changed), disk re-read gates PASS (`releases/axis86/gems86-h33-2b2-trackb-rendertop120-20261023-79ca1469-zeros.json`).

## SPACING crowded-pool candidates (built 2026-10-23, `arena/ee238b91`) — mechanism probes, predictions inside ±0.002

Three arms at matched count 37,654, differing only in where ~3,050 kernel-crowded dots
(8.1 % of R0) are re-placed. Distinct keys from the `sp-*c16` SPACING arms (IR-86-SPACING-07).
Upload the `-zeros` twin only if the human decides to probe; none is a default bet.

- **along-strike** (the only one worth a throwaway probe):
  `releases/h33-h33-2-b2-20261004-e5eb6e7e-SPACING-alongstrike-20261023-4d631f4a-zeros.tif`
  - SHA-256: `4d631f4a9b1dcec957815e6e77025a616b929192e1ea8418ddac2c6ea7e5faf6`
  - Submission name: `h33-h33-2-b2-20261004-e5eb6e7e-SPACING-alongstrike-20261023-4d631f4a`
  - Note (125 ch): `R0 h33-h33-2-b2-20261004-e5eb6e7e; SPACING along-strike: 3036 crowded dots re-spaced at 3.0px, count fixed; pred +0.002 MODEL`
  - 3,036 dots moved (8.06 %), mean displacement 2.05 px, prediction **+0.002 MODEL** (−0.003…+0.006).
- **lattice**: `…-SPACING-lattice-20261023-4551582d-zeros.tif`
  - SHA-256: `4551582db3bb76e7fe8d521bae9b385634a31ae9b2d411e8d932a69d09d8a08e`
  - Note (120 ch): `R0 h33-h33-2-b2-20261004-e5eb6e7e; SPACING lattice: 3086 crowded dots re-spaced at 3.0px, count fixed; pred +0.000 MODEL`
- **poisson-disk** (the neutral arm): `…-SPACING-poissondisk-20261023-d2cf39d5-zeros.tif`
  - SHA-256: `d2cf39d533893f4006d4e057546c22be5a988ff06d861df7fa01f88b52a276a3`
  - Note (125 ch): `R0 h33-h33-2-b2-20261004-e5eb6e7e; SPACING poisson-disk: 3056 crowded dots re-spaced at 3.0px, count fixed; pred +0.000 MODEL`

Format receipt: all three pass the shared validator and `format_report` against
`sample_submission.tif` (EPSG:32611, 3730x3292, float32, values in [0,1], zero catalogue
mass, new cells >= 3 px off the catalogue, parent 2.828 px spacing floor never tightened);
each has a spec-form twin (NaN outside the footprint) and a `-zeros` twin (upload form).
Full receipts: `releases/…-zeros.json`; cards: `evidence/spacing-crowdedpool-mechanism.md`.

## CONCENTRATION 5 km ridge & CV-band arms (built 2026-10-23, session `arena/69392a35-gemsdoe86`) — `concb5kmdown4` proposed for Slot 2; off-ridge arms retired (`IR-86-CONC-10`)

Restoring all 15 SHA-256-pinned manifest inputs (`training_features.tif`, `derived_sgmc_faults_100m_u8.tif`, `H19-5`, `H19-4`, `H16-1`) showed that **every off-ridge `CONCENTRATION` build loses on SGMC**: PR #37 `conc15` reads **−0.0071 MODEL** (not `+0.006`) and breaches §4.4 (`39.8 %` at `≤ 3.0 px`); PR #44 `dens15` (**−0.0006 MODEL**) and `spr15` (**−0.0013 MODEL**) place **0.0 %** of added dots on ancestor ridges; PR #46 `b5km-move10/15/20` read **−0.0066..−0.0150 MODEL** (`0.0 %` on `H19-5`). **Do not spend weekly slots on `conc15`, `dens15`, `spr15`, or `b5km-move10/15/20`.**

All three arms below hold `n_dots = 37,654` fixed, place **100.0 %** of added dots on `H19-5 | H19-4 | H16-1` at `> 3.0 px` clearance (`min = 3.1623 px`) and `≥ √8 px` spacing, and pass all MUST gates in both encodings after disk re-read. Rebuild via `.venv/bin/python scripts/restore_axis_inputs.py && .venv/bin/python scripts/run_concentration_5km.py`.

| Arm | Upload path (`-zeros.tif` fallback; `.tif` NaN twin adjacent) | `-zeros.tif` SHA-256 (`ledger/submissions.csv`) | `.tif` (NaN-outside) SHA-256 | Form name (`≤ 64` ch) | Form note (`≤ 140` ch) |
|---|---|---|---|---|---|
| **`b5km-cvband-down4` (Slot 2 candidate)** | `releases/h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown4-20261023-8aab97b6-zeros.tif` | `8aab97b65f70ba6c5dc4e3f0e73d95cbcb602da0d110c46dd0cf6a3a2e55d863` | `2daf174f8d430a60073ed0b9c6d6e1196ac79a906b80187c8bb3248db6426ff3` | `h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown4-20261023-8aab97b6` | `R0 h33-h33-2-b2-20261004-e5eb6e7e; CONC b5km-cvband-down4: 1506 ridge dots moved (8.00% chg, 1km CV 0.516); pred +0.0015 MODEL` |
| `b5km-ridge-up4` (do not spend Week-1 slot) | `releases/h33-h33-2-b2-20261004-e5eb6e7e-concb5kmup4-20261023-493cf242-zeros.tif` | `493cf24211bfd7d1699a172ccc4fb62194bfa31e2d1d50446ea5908e335919e0` | `d5e18afa6f6a44b8e113ac5dacc58e70b4ff79b495917f5149fe4447878a1afa` | `h33-h33-2-b2-20261004-e5eb6e7e-concb5kmup4-20261023-493cf242` | `R0 h33-h33-2-b2-20261004-e5eb6e7e; CONC b5km-ridge-up4: 1506 ridge dots moved (8.00% chg, 1km CV 0.625); pred -0.0005 MODEL` |
| `b5km-ridge-up8` (do not spend Week-1 slot) | `releases/h33-h33-2-b2-20261004-e5eb6e7e-concb5kmup8-20261023-b4d36a67-zeros.tif` | `b4d36a671bcd86fd460203fc04f2a0bbcfca79be1124748d11c294c5126974f6` | `1bec1facabdfd54d86db10cca070c9b121ac35bed40468fed9e2b724343bab92` | `h33-h33-2-b2-20261004-e5eb6e7e-concb5kmup8-20261023-b4d36a67` | `R0 h33-h33-2-b2-20261004-e5eb6e7e; CONC b5km-ridge-up8: 3012 ridge dots moved (16.00% chg, 1km CV 0.626); pred -0.0007 MODEL` |

**Manual upload checklist (`concb5kmdown4` only, if chosen for Slot 2):**
1. Verify local SHA-256 before opening the portal: `sha256sum releases/h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown4-20261023-8aab97b6-zeros.tif` must print `8aab97b65f70ba6c5dc4e3f0e73d95cbcb602da0d110c46dd0cf6a3a2e55d863` (or `2daf174f...` if the portal prefers NaN-outside `.tif`; upload **one**, never both).
2. Confirm rolling-week quota has at least 1 slot remaining and record `TOP_PUBLIC` + date first.
3. Paste the exact 62-char form name and 126-char form note above (`≤ 140` chars), submit manually, and log the live score + portal timestamp as `RECEIPT` in `ledger/submissions.csv` before any subsequent upload.

## RELIEF source factorial (built 2026-10-23, session `arena/ada3049e-gemsdoe86`) — **not slot-recommended**

All three are count-fixed at 37,654 dots and differ from R0 only in which relief regime the mass
sits in. Every one is **negative on the SGMC-extra surrogate (MODEL) and slightly below R0 on the
catalogue PROXY**; they exist to test a mechanism, not to be uploaded. `IR-86-RELIEF-04` explains
why the whole RELIEF family's MODEL numbers are instrument-shaped, which is why the shipped
`front+15pct` row is now Slot 3 rather than Slot 1.

| Arm | Upload path (`-zeros` twin; spec `.tif` with NaN outside is adjacent) | `-zeros` SHA-256 | Submission name | Note (≤ 140 ch) |
|---|---|---|---|---|
| `int2front-15pct` | `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-int2front15-20261023-c543e779-zeros.tif` | `c543e77929280ae92f9ad5efcdd0e1b1013d2d079d13fe981adb80f69674c15c` | `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-int2front15-20261023-c543e779` | `R0 h33-h33-2-b2-20261004-e5eb6e7e; RELIEF int2front-15pct: 5648 dots moved range-interior->range-front, count fixed; pred -0.006 MODEL` |
| `int2front-10pct` | `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-int2front10-20261023-4471a74b-zeros.tif` | `4471a74bcc684ee13df5f01b2d4d70c633ef3100e765a43193a063f5014a9814` | `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-int2front10-20261023-4471a74b` | `R0 h33-h33-2-b2-20261004-e5eb6e7e; RELIEF int2front-10pct: 3765 dots moved range-interior->range-front, count fixed; pred -0.004 MODEL` |
| `int2pied-15pct` | `releases/h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-int2pied15-20261023-295eaf92-zeros.tif` | `295eaf92bdf6c0108599b43b694baec7bf0ddce92dfa23d1d58a35564e90ace9` | `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-int2pied15-20261023-295eaf92` | `R0 h33-h33-2-b2-20261004-e5eb6e7e; RELIEF int2pied-15pct: 5648 dots moved range-interior->piedmont, count fixed; pred -0.012 MODEL` |

**Format receipt (both encodings, re-read from disk after writing):** CRS `EPSG:32611`, `3730×3292`,
`float32`, one band, values in `[0, 1]`, **0 NaN inside the footprint**, zeros (or NaN) outside,
**0 catalogue pixels carrying mass**, every newly occupied cell at `≥ 3.1623 px` from the
catalogue, `37,654` dots, `14.9997 / 9.9989 / 14.9997 %` of cells changed, shared validator and
`format_report` both `True`, `sha256` matches the ledger row. Parent-difference statistics and the
per-arm mechanism card are in `releases/<id>-zeros.json` and
`evidence/relief-source-mechanism.md`.

**Upload order (unchanged by this session):** Slot 1 `PRUNE-le3p000` → Slot 2 `concb5kmdown4` →
Slot 3 `RELIEF-frontp15`. See [SLOT_PLAN.md](../SLOT_PLAN.md).

## Down-dose rungs session files (PR #55, post-collision reconciliation)

Two new curve brackets beyond PR #50's `cvband-down3/5/6` (this session's `down6` rebuilt PR #50's
`conc6` byte-identically — `1ed78e0f…` — and is recorded `BUILT-DUPLICATE`, not a slot candidate;
`IR-86-CONC-17`). Neither new file is a slot candidate: they are the low-dose point and the
destination-pool ceiling that pin Slot 2's dose-response curve.

| file (`releases/`) | name (≤ 140 ch) | note (≤ 140 ch) | zeros sha256 | bytes |
|---|---|---|---|---|
| `…-concb5kmdown2-20261023-f0ee647f-zeros.tif` | `h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdown2-20261023-f0ee647f` | `R0 …e5eb6e7e; CONC b5km-cvband-down2: 753 ridge dots moved (4.00% chg, 1km CV 0.561); pred +0.0012 MODEL` | `f0ee647f…` | 219,773 |
| `…-concb5kmdownmax-20261023-d4a42664-zeros.tif` | `h33-h33-2-b2-20261004-e5eb6e7e-concb5kmdownmax-20261023-d4a42664` | `R0 …e5eb6e7e; CONC b5km-cvband-downmax: 2381 ridge dots moved (12.65% chg, 1km CV 0.479); pred +0.0020 MODEL` | `d4a42664…` | 220,507 |

(`…-concb5kmdown6-20261023-1ed78e0f-zeros.tif` also exists locally; upload PR #50's
`…-conc6-20261023-1ed78e0f-zeros.tif` instead — the bytes are identical.)

Format receipt (both files, and the spec-form NaN twins): CRS EPSG:32611, 3,730 × 3,292, single
float32 band, transform `(100, 0, 243350, 0, -100, 4508550)`, values in {0, 1} inside the
5,167,373-cell footprint, 0 (fallback) / NaN (spec form) outside, 0 dots on catalogue pixels,
count fixed at 37,654, added dots ≥ 3.162 px off catalogue, inter-dot spacing ≥ 2.8284 px,
re-read from disk after writing (`gems57.validate` + `gems57.gates.format_report` PASS).
Master run card `evidence/concentration_dose_axis_20261023.json`; the released `down4` anchor
rebuilt byte-exactly (`8aab97b6…`) before any new file was written.

## CONCENTRATION 10 km arms (built 2026-10-23, session `arena/a681fdaf-gemsdoe86`) — week-2 alt only; Slots 1–3 unchanged

Pre-registered (`registry/preregistration_conc10.json`); rebuild via `.venv/bin/python scripts/restore_axis_inputs.py --ids scored_h19_5 scored_h19_4 scored_h16_1 scored_d28_unscored ext_derived_sgmc_faults_100m_u8 ext_geodawn_extensions_u8 ext_geodawn_extensions_json ext_topo_10m_derived_100m_u8 ext_dem10_chi_100m_i16 && .venv/bin/python scripts/run_concentration_10km.py`. **None displaces Slots 1–3** as re-ranked in [SLOT_PLAN.md](../SLOT_PLAN.md) rev. H (`PRUNE-le3p000`, `conc6`, `RELIEF-frontp15` demoted; spares `conc5dose`, then PR #53 `surfext10`); the stale `dens15`/`spr15` ordering at the top of this file stays retired per `IR-86-CONC-10`. `concb10kmdown8` is a week-2 spare behind `conc5dose`/`surfext10`, **only if Slot 2 (`conc6`) returns ≥ +0.005**; `concb10kmup8` is retired — do not upload.

| Arm | Upload path (`-zeros.tif` fallback; `.tif` NaN twin adjacent) | `-zeros.tif` SHA-256 | `.tif` (NaN-outside) SHA-256 | Form name | Form note (≤ 140 ch) |
|---|---|---|---|---|---|
| `b10km-down8` (wk-2 alt) | `releases/h33-h33-2-b2-20261004-e5eb6e7e-concb10kmdown8-20261023-780f8509-zeros.tif` | `780f850996ea4005774bf197fb11fe20a99c20e2a23847e4ecc117de3838f897` (219,913 B) | `7ac493c6aad96c7d70df71c28aacdebc89f8b45ae3438ea78f6dcf67233a1ada` (356,306 B) | `h33-h33-2-b2-20261004-e5eb6e7e-concb10kmdown8-20261023-780f8509` | `R0 h33-h33-2-b2-20261004-e5eb6e7e; CONC b10km-down8: 3012 ridge dots moved (16.00% chg, 10km CV 0.496); pred +0.0003 MODEL` |
| `b10km-down4` (in-band fallback) | `releases/h33-h33-2-b2-20261004-e5eb6e7e-concb10kmdown4-20261023-c4e8ffc9-zeros.tif` | `c4e8ffc9efce926e93267af1b1f53afc36231a929b0b0189268b67d1c6b39b42` (220,059 B) | `ab5594ab0a60a6ce73bf1daaaea29006db9368cd28b0f72beba4b1e758262f03` (356,490 B) | `h33-h33-2-b2-20261004-e5eb6e7e-concb10kmdown4-20261023-c4e8ffc9` | `R0 h33-h33-2-b2-20261004-e5eb6e7e; CONC b10km-down4: 1506 ridge dots moved (8.00% chg, 10km CV 0.518); pred -0.0010 MODEL` |
| `b10km-ridge-up8` (**retired — never upload**) | `releases/h33-h33-2-b2-20261004-e5eb6e7e-concb10kmup8-20261023-ef2f3548-zeros.tif` | `ef2f35484527cd7d107d5d528b1a264354d95f55e32d80103e0fe82947673f06` | `923482e21d73660c7f6c355cbb61431071169de767243efc2c1a8fe1ee2bc9c8` | — | — |

**Format receipt (all three, both encodings, re-read from disk):** CRS EPSG:32611, 3,730 × 3,292, single float32 band, transform of `sample_submission.tif`, values in {0, 1} inside the 5,167,373-cell footprint, NaN (spec `.tif`) or 0 (`-zeros` fallback) outside, 0 dots on catalogue pixels, new-dot catalogue clearance ≥ 3.162 px, min pair distance 2.8284 px (= parent floor), 37,654 dots each. Full receipts: `releases/…-zeros.json` beside each TIFF; run card `evidence/concentration_10km_axis_20261023.json`. Upload **one** encoding per slot, verify `sha256sum` first, log the portal score as `RECEIPT` in `ledger/submissions.csv`.
