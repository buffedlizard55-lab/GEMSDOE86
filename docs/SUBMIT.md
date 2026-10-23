# Manual submission card — no automatic submission

**Status: BUILT; not slot-approved.** `TOP_PUBLIC`, remaining quota and R0's submission receipt
were not supplied. The human alone submits, from one registered entity, one file per slot.
Full plan and decision tree: [SLOT_PLAN.md](../SLOT_PLAN.md). Release TIFFs are local-only and
gitignored (unchecked data-use terms); hashes below are the authority.

## Slot 1 — PRUNE ≤ 3.000 px, pure deletion (nested ladder, PR #29)

- Submission name: `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros`
- Upload: `releases/h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif`
- SHA-256: `a438e92b…` — take the full digest from `releases/…-a438e92b-zeros.json`.
- 35,483 dots (R0 minus all 2,171 dots within 3.0 px of the catalogue), 5.77 % changed.
- Prediction: **+0.004 (MODEL)**, band −0.004 … +0.013. Receipt: `evidence/prune_ladder.json`.
- Nested rungs at ≤ 2.2361 px and ≤ 2.8284 px exist in the same ladder if the human prefers a
  shallower first edit.

## Slot 2 — `RELIEF front+15pct`, count-fixed relocation (built this session; AXIS assigned by the human)

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

## CONCENTRATION knobs — built and gated, **not slot-approved** (PR #38, predicted inside ±0.010)

Upload the `-zeros` twin; the `-nan` twin carries identical dots. TIFFs are local-only and
gitignored. Each arm moves exactly one knob off the spent 1 km / 15 % / top-20 % setting, so a
receipt on any two of them attributes the difference to that knob.

| Variant | File (`-zeros`, fallback twin — upload one) | sha256 (zeros) | sha256 (NaN twin) | Prediction |
|---|---|---|---|---|
| `b5km-move15` block 1→5 km — **BUILT-DUPLICATE, do not upload** (PR #43 built the same dot set, token `73802181`; IR-86-CONC-07) | `releases/axis86/gems86-h33-2b2-conc15-b5km-20261023-73802181-zeros.tif` | `fc9229d85d1f0b7872118b94bbf43e1c28bbbb8138b44d90aeb14c4ac63453c1` | `054e228259d288b7c966a24b61eea1c87277ae72d6bf4b4d0e5fbcee476e1118` | **+0.001 MODEL** (−0.008…+0.008) |
| `b1km-move24` dose 15→24 % | `releases/axis86/gems86-h33-2b2-conc24-20261023-af31526e-zeros.tif` | `90a5756f49f79ae17fc56ba0d6e4d2b5d76b4b751169babdaecf0dc92ae5512d` | `9b471507d93d70f9d5bb148c8a481548045c4e8a396267d5f74dd2bea9f79c9c` | **−0.001 MODEL** (−0.012…+0.008) |
| `b1km-move15-t05` top 20→5 % | `releases/axis86/gems86-h33-2b2-conc15-t05-20261023-278d9995-zeros.tif` | `cd5c7545defe108d09f18ab1e39b0ec63c9a31d425d8ec4e1efcfd5b0237e3b8` | `2baf8424f007e44209490aeeb541b9b12cc6184b3dfac7ff33b544b9907c945e` | **+0.002 MODEL** (−0.007…+0.009) |

- The two uploadable arms are `b1km-move24` and `b1km-move15-t05`; `b5km-move15` is a
  duplicate of a parallel session's file and is listed only for audit.
- All three: 37,654 dots (count fixed), every placement at the parent's 2.828 px spacing, zero
  catalogue mass, minimum catalogue clearance 2.236 px, parent-diff 29.999 % / 48.0 % / 29.999 % of
  cells changed, both encodings re-read from disk and passing `format`, `values`,
  `catalogue_clearance` and `sha256_not_in_ledger`.
- Submission names are the file stems without `-zeros`. Form notes (auto-written, ≤140 chars) are in
  each `-zeros.json` receipt, e.g. `GEMSDOE86 h33-2b2 CONCENTRATION b5km-move15 | 37654 dots,
  29.999% changed vs R0 | UNSCORED; MODEL prediction only`.
- Why they are predicted flat: the fold-fair hide-and-recover gain (+0.012/+0.024/+0.020) is
  entirely the catalogue-density term (+0.0149) and not the physical one (+0.0008, CI crossing
  zero); on the SGMC independent map every arm including the shuffled-prior null loses 0.012–0.020.
  Full numbers: `evidence/concentration_instruments_20261023.json`; IR-86-CONC-05/06.
- Use one of these only as a **probe** of whether a catalogue-density prior transfers to new faults.
  The default slot order is in [SLOT_PLAN.md](../SLOT_PLAN.md) and does not include them.

## Slot 3 — a sign flip or a deliberate probe, both predicted non-positive

**Option A (recommended if slots 1–2 both land inside ±0.01): `RELIEF front−10pct`**
(`…-frontm10-20261023-1b26223e-zeros.tif`, digested in the bullet above). Its value is the *paired* read against
slot 2: a 25 %-of-mass swing with a predicted separation of ~0.011, i.e. the only RELIEF comparison
that can clear the evidence floor.

**Option B: SNAP, built and gated, predicted negative**

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

### CONCENTRATION, 1 km blocks — the one new candidate

- **File:** `releases/gems86-h33-2b2-conc15-20261023-2b883f2d-zeros.tif`
  (nan-outside twin: `gems86-h33-2b2-conc15-20261023-2b883f2d.tif`)
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
- **Where it sits in the plan:** slot **2b** in `SLOT_PLAN.md` — the move-the-mass alternative to a
  second RELIEF rung, not a replacement for slot 1 (`PRUNE-le3p000`).

Release TIFFs are gitignored (data-use terms unchecked), so they exist only in this working copy;
the JSON receipts next to them carry the digests. Rebuild with the commands in `AI_USE.md`.

## Also not a slot candidate: the gain-gated SNAP build (2026-10-23, third session)

`releases/h33-h33-2-b2-snapr2g10-20261023-8ca1d869[-zeros].tif` (37,654 dots, 17.5 % moved
≤2 px, mean displacement 0.34 px; zeros sha256 `8ca1d8690aa835c8…82d2e`, NaN twin
`32c1e4e99444abaf…3f52`; **−0.001 MODEL**) is gate-clean but **must not be uploaded**:
SNAP was spent by PR #31, corroborated by PR #34, and this build's SGMC control is negative
with dose (IR-86-SNAP-09). Status `BUILT-DUPLICATE`; its `snapr1`/`snapr2` arms are
withdrawn duplicate pairs with **no raster**. Rebuild: `python scripts/build_r0_snap.py --build`.

## SPACING arms (built 2026-10-23, session `arena/c8365759-gemsdoe86`) — proposed for slot 3, **not approved**

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
