# SLOT PLAN — 2026-10-25 (rev. K: 92-site `REV2` fleet sync + `IR-H` repair + `H86M-BMGS` audit lane, `DO NOT SUBMIT` active)

> **2026-10-25 Binding Safety Notice:** Under `scripts/protocol_preflight.py` (`STOP_LITERAL_OVERLAP_UNSATISFIABLE`), `scripts/audit_release.py` (`decision: "DO NOT SUBMIT"`, `safe_to_submit: false`, `artifact_count: 37`), `docs/evidence/h86m-bmgs-run-card.json` (`verdict: "negative"`, `DO NOT SUBMIT`), `docs/evidence/h86l-fmc-run-card.json` (`verdict: "negative"`, `DO NOT SUBMIT`, registered to resolve `IR-H`), `docs/evidence/h86k-stdp-run-card.json` (`verdict: "negative"`, `DO NOT SUBMIT`), `docs/evidence/h86j-tvhs-run-card.json` (`verdict: "negative"`, `DO NOT SUBMIT`), `docs/evidence/h86j-csgd-run-card.json` (`verdict: "negative"`, `DO NOT SUBMIT`), `docs/evidence/h86i-rlms-run-card.json` (`verdict: "negative"`, `DO NOT SUBMIT`), and `docs/evidence/h86i-ksad-run-card.json` (`verdict: "negative"`, halted pre-TIFF on `71.31%` discrete forward 3-px overlap vs `GEMSDOE80`), **zero files in this repository are currently authorized for portal upload** (including `gems86-h86m-bmgs-dcelf-37654dots-20261025T185635Z-dac77ff2-zeros.tif`, `gems86-h86l-fmc-minconsensus-37654dots-20261025T161053Z-zeros.tif`, `gems86-h86k-stdp-dcelf-37654dots-20261025T145724Z-72a82f29-zeros.tif`, `H86K-PSC`, `GDSC`, `H86J-MCSP`, `H86J-TVHS`, `H86J-CSGD`, `H86I-RLMS`, `H86I-SACD`, `H86J-MPC`, `H86I-HVFD`, `H86I-RKSC`, `H86F-GZZD`, `H86F-PCC`, and `H86E-MMT`), and PR #60's unregistered `submission/gems86-spt-throwcons-...` candidate remains revoked (`IR-86-SPT-02`). Historical R0-axis notes below remain archived selector context only (`submission_slots_used = 0`).
>
> **2026-10-25 `H86M-BMGS` Audit Benchmark (`gems57-pooled-hide-v2`, `11,321` withheld positives, 12-px eroded LOQO):**
> - `E1_bmgs_strand_dinkelbach_celf` (`37,654`d): **`0.1310 [0.1121, 0.1509]`** `HOLDOUT-DTI` (`+0.0113` over raw/isotropic/static-`E[k]` ablation `E3 = 0.1197`) and **`0.1082 [0.0862, 0.1319]`** `SGMC-PROXY-DTI` (`+0.0264 [+0.0117, +0.0409]` over `E3 = 0.0818`, `+0.0145` over `GEMSDOE32` `H33 = 0.0937`; `46.60%` far-field `> 1 km`).
> - `E2_bmgs_blind_zero_catalogue` (`37,654`d, zero catalogue, zero DEM): **`0.1111 [0.0906, 0.1322]`** `SGMC-PROXY-DTI` with **`70.21%` far-field `> 1 km`** (matching `GEMSDOE32` `H33`'s `69.80%` with zero catalogue input at inference); `0.0644` `HOLDOUT-DTI`.
> - Full 702-raster uniqueness: `0` Spearman `rho > 0.90` firings (`max = 0.5650`) and `0/460` discrete `<= 90k`-dot firings `> 0.70` (`max = 0.6369`; `0.2974` vs `GEMSDOE32` `H33`); literal `17GEMSDOE` + high-density `> 90k`-dot rasters + 2 off-grid rows keep `verdict = "negative"` (`DO NOT SUBMIT`).
>
> **2026-10-25 `H86I-KSAD` Strict-LOQO Holdout Benchmark (`gems57-pooled-hide-v2`, `11,321` withheld positives, 20 km block bootstrap, `quad != q` eroded 12 px):**
> - `E2_ksad_pointwise_d28_ablation` (`37,654`d, `2.8 px`): **`0.1599 [0.1459, 0.1742]`** `HOLDOUT-DTI` (repo strict-LOQO record)
> - `E1_ksad_dinkelbach_submod` (`28,197`d final, Dinkelbach submodular $K_3$): **`0.1553 [0.1396, 0.1718]`** `HOLDOUT-DTI` (paired `E1 - E2 = -0.0046 [-0.0100, +0.0010]`)
> - `C1_H86F_EWCS_strict_loqo_ctrl` (`H86F-EWCS` re-evaluated under strict outer LOQO; see `IR-86-H86F-INQUAD-TRAINING-20261025`): **`0.1333 [0.1178, 0.1502]`** `HOLDOUT-DTI` (`E1 - C1 = +0.0220 [+0.0038, +0.0405]`)
> - `H86C-KSLB` historical strict-LOQO best (`44,090`d): **`0.1241 [0.1080, 0.1403]`** `HOLDOUT-DTI`
> - `E3_ksad_cover_blind_no_catalogue` (zero-catalogue, no 100 m DEM): **`0.0624 [0.0498, 0.0762]`** `HOLDOUT-DTI`

**2026-10-25 addendum (H86G-EDTI):** one candidate is now selector-ready under PA-86-01
like-for-like gates — `gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros`
(sha256 `ba8b731f...`, SGMC-PROXY-DTI 0.1223 vs H33-as-is 0.0954, paired Δ +0.0269
[+0.0028, +0.0518] post-selection descriptive; HOLDOUT-DTI OOF 0.0631). It is the
recommended next single slot **if** the selector spends one; receipt decision
rule (±0.01 vs the 0.2778 OWNER-REPORTED claim) is in
`research/H86G_EDTI_REVIEW.md`. The literal-witness notice above is unchanged
for every other file, and the R0-axis probes below remain archived spares.

**No automatic submission.** One entity, ≤ 3 scored submissions per rolling week, 1 blind final pick
([official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). Deadline 2026-12-03 (`UNVERIFIED`
portal clock; ~5.9 wk ⇒ ~17 slots max, minus the final pick). Parent **R0 = `h33-h33-2-b2`**
(GEMSDOE32), 37,654 unit-mass dots; `0.2778` is **CLAIM** (0 `RECEIPT` rows in
`ledger/submissions.csv`). `TOP_PUBLIC`, rolling-week quota left and R0's receipt are **UNSUPPLIED**.
Live `|Δ| < 0.01` = no evidence.

## What the 2026-10-23 sessions changed

**A. `CONCENTRATION` is monotone in dose and partly generic dispersal (PR #50).** `conc3` `+0.0013` →
`conc5dose` `+0.0018` → `conc6` `+0.0022 MODEL` (4/4 quadrants; `+0.0013` PROXY) while 1 km occupied
CV falls `0.5377 → 0.4998 → 0.4840`, so the historical `0.51–0.59` band is a correlate, not the cause
(`IR-86-CONC-13`). The matched ordering control (same blocks, same count, random dot, random
destination) gets `+0.0015` / `+0.0008 PROXY`, so **the ranking buys only ≈ `+0.0007`**. The axis is
capacity-capped at ≈ 6.4 % of R0 (`IR-86-CONC-12`) — pinned exactly by the PR #55 rungs session:
the binary-searched sparse-ridge destination-pool ceiling is **2,381 moves** (`b5km-cvband-downmax`,
`d4a42664`, CV 0.4789), and the 122 moves past `conc6` cost more than they bought (`+0.0020` vs
`+0.0022` MODEL, 4/4 quads). The same session added the low rung `b5km-cvband-down2` (`f0ee647f`,
753 moves, CV 0.5611, `+0.0012` MODEL 4/4, `+0.0001` PROXY), so the curve is now measured at
753 / 1,130 / 1,506 / 1,883 / 2,259 / 2,381 moves and is monotone to the pool ceiling
(`IR-86-CONC-17` records that PR #55's `down6` rebuilt PR #50's `conc6` byte-identically).
`conc6` supersedes `concb5kmdown4` on both instruments at 753 extra moved dots.

**B. `RELIEF`'s only instrument is a relief-index meter (PR #51).** Eight RELIEF rebuilds (3 shipped +
3 new + 2 displacement-matched random nulls) score on the SGMC-extra surrogate as
`Δ ≈ 0.0283·Δ(mean relief index) − 0.0033`, **r = +0.956, R² = 0.9135, n = 8**; the `front+15pct`
reconstruction reproduces its ledger `+0.0017` exactly and sits **−0.0008 below the fit**, and the
zero-index nulls cost `−0.0026…−0.0030` (`IR-86-RELIEF-04`). RELIEF MODEL deltas are therefore not
mechanism evidence, and `frontp15` drops to Slot 3. The new source arms are all negative
(`−0.0057 / −0.0038 / −0.0118`) and the pre-registered sign was falsified
(`evidence/relief-source-mechanism.md`). The basin source holds 2,014 dots (5.35 %), below RELIEF's
10 % dose floor, so the alluvium question cannot be asked on this parent (`IR-86-RELIEF-05`).

**C. `CONCENTRATION` is saturated on its own evidence surface (PR #53).** All 37,654 R0 dots lie on
the `H19-5` ancestor surface and only **90** legal free cells remain there under the parent's own
constraints; the merged cvband rule's within-surface capacity is ~2,400 dots, which independently
reproduces rev. D's ≈6.4 % cap (`IR-86-CONC-12` → `IR-86-CONC-16`). `H19-4 | H16-1` minus `H19-5` is
35,954 px of near-equal owner-reported quality (`0.1894` / `0.1855` vs `0.1922`) carrying **zero** parent
mass, with 8,671 legal slots. Three gate-clean probe files extend mass onto it (`surfext10`
+0.0059 MODEL / −0.00003 PROXY; `surfext15` +0.0073 / −0.0005; control +0.0047 / −0.0008). The control
captures most of the MODEL gain while moving mass *away* from SGMC truth, so that instrument rewards
outward movement here, not lineaments (`IR-86-CONC-15`); the ridge-specific increment is only
+0.0012 MODEL / +0.0008 PROXY. **None of the three is slot-approved.**

**D. Budget arithmetic — why the remaining slots should buy evidence, not reallocation (MODEL).**
Inverting `DTI = T/(0.2T + 0.2(n−M) + 0.8|G|)` at 0.2778 with `|G| ≈ 40k`: `T ≈ 10,963`, `D ≈ 39,464`, so
**+0.01 of live DTI needs ≈418 kernel-credit units ≈ 42 km of fault trace hit squarely** (24–78 km across
a 20k–80k `|G|` band). Rearranging 2–6k existing dots has produced `|Δ| ≤ 0.0073` on the most generous
instrument across all three sessions. Wk 1–3 below still test the three best reallocations because they
are already built and cost nothing but slots; everything after that should fund new evidence.

**E. The pediment refinement of the dispersal rule is BUILT and fails its SGMC falsifier (this session, `IR-86-CONC-18`).** The truth-free pediment window (3DEP `relief_local` 10–40 m, > 1 km off the RELIEF regime front; 18.8 % of the footprint) **caps at 1,045 moved dots** under the > 3 px / √8 px rules, so the attribution pair is dose-matched at 941 dots (5.00 % chg) with matched displacement (mean 1,613 vs 1,631 px, making `IR-86-CONC-15`'s outward-movement bias common-mode). At that dose the **non-pediment complement beats the pediment arm on SGMC (+0.0013 vs +0.0007**; REF `concb5kmdown4` +0.0015 replicated exactly**)** while the fold-fair d28 `PROXY` orders them oppositely (+0.0012 vs +0.0004): instruments split, attribution unresolved, **no slot change** — `concb5kmpeddown2p5` / `concb5kmnonpeddown2p5` / `concb5kmpeddown5` are audit-only. Card: `evidence/concentration-pediment-mechanism.md`.

**10 km addendum (PR #54).** Pre-registered 100 px arms: `b10km-down8` `+0.0003 MODEL` (jitter `+0.0010`) / `+0.0012 PROXY` vs control `-0.0009`; prefix `b10km-down4` splits sign. Neither displaces Slot 2 or the spares; `…-concb10kmdown8-20261023-780f8509-zeros.tif` is the next spare only if Slot 2 `≥ +0.005`. `b10km-ridge-up8` (`-0.0009` = control; `-0.0075 PROXY`, CI excludes 0) retires upward concentration at 1, 5 and 10 km — never upload `concb10kmup8`. `IR-86-CONC-19`: canonical R0 occupied-10 km CV is `0.736`, not `0.570`.

## Next weekly slots (one file per slot, human uploads; `-zeros` twin unless the portal rejects zeros)

| Slot | Candidate (`releases/<id>`) | Edit vs R0 | Predicted Δ (MODEL, not a score) | Decision rule on live `RECEIPT` Δ vs 0.2778 |
|---:|---|---|---|---|
| **1** | `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | delete 2,171 dots (`5.77 %`) in the `2.0 < d_cat ≤ 3.0 px` collar; 35,483 dots | `+0.0040` — largest lever, and its Δrelief-index ≈ 0 so the bias in §B cannot manufacture it (partly mass-confounded, `IR-86-MASS-04`) | `≥ +0.010`: collar halo is real drag → next slot probes `4.0 px` and combines with Slot 2. `≤ −0.005`: keep the 2 px collar, close PRUNE. Flat: run Slot 2. |
| **2** | `h33-h33-2-b2-20261004-e5eb6e7e-conc6-20261023-1ed78e0f-zeros.tif` *(replaces `concb5kmdown4`)* | 2,259 dots (`12.0 %` changed) shaved from `≥3`-dot 1 km clusters onto sparse-block ancestor ridges; 1 km CV `0.6235 → 0.4840`; count fixed | `+0.0022` (4/4 quads, `+0.0007` above its own dispersal control), `+0.0013 PROXY` | `≥ +0.010`: density-cap dispersal is a real lever → 6 % is the ceiling, so combine rather than dose up. `≤ −0.005`: dispersal is neutral-to-negative on private chunks → close CONCENTRATION. |
| **3** | `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif` *(demoted)* | 5,648 dots (`15.0 %`) piedmont → range-front, count fixed | `+0.0017` headline, but **unbiased prior `0 ± 0.005`**: the headline is the instrument's relief gradient (§B) | `≥ +0.010`: the front destination beats the instrument's own gradient → restore RELIEF and combine. `≤ −0.005`: close RELIEF. Inside `±0.010`: close as unmeasurable at this effect size. |
| 4 (spare) | `…-conc5dose-20261023-a2f8aaad-zeros.tif` | 1,883 dots (`10.0 %`), CV `0.4998` | `+0.0018` MODEL / `+0.0010` PROXY | Paired dose point for Slot 2 only if Slot 2 returns a positive but sub-0.01 Δ. |
| 4b (spare alternate) | `…-CONC-surfext10-20261023-fe814da5-zeros.tif` (PR #53) | 3,765 dots (`20.0 %` chg) off saturated `H19-5` onto `H19-4\|H16-1`, count fixed | `+0.0059` MODEL (**−0.00003** PROXY; only `+0.0012` above its own off-union control) | Use **instead of** 4 only if the aim is to test whether unmapped ground on the other two ancestor surfaces holds new truth: `≥ +0.010` → escalate to `surfext15`; `≤ −0.005` → retire the family. Never upload `surfext10ctl`. |

**Never upload:** the three pediment arms (`concb5kmpeddown2p5` 9fb6bfc9, `concb5kmnonpeddown2p5` 57cc867c, `concb5kmpeddown5` 161b002e — audit-only, `IR-86-CONC-18`); the three new `int2*` RELIEF arms; `conc6rand` (`CONTROL`); `conc15` (`−0.0071`),
`dens15`/`spr15` (`−0.0006`/`−0.0013`), `b5km-move10/15/20` (`−0.0066…−0.0150`), `concb5kmup4/8`
(`−0.0005`/`−0.0007`); all MASS arms; all SNAP arms; `trackb-cull1dot`; every `BUILT-DUPLICATE` /
`withdrawn` row.

## Calendar to 2026-12-03

* **Wk 1:** Slots 1–3 in order, logging each live `RECEIPT` + portal timestamp in
  `ledger/submissions.csv` before the next upload. If Slot 1 clears `+0.010`, spend Wk 2 on the
  `4.0 px` collar rung instead of Slot 3.
* **Wk 2–3:** second dose only on an axis that cleared `|Δ| ≥ 0.01`; otherwise the next-best levers
  (spare probes: `conc5dose` for a paired dose point, or `surfext10` for the surface question — never both).
  A paired CONCENTRATION A/B (ranked `conc6` vs its own control) is the only clean way to price the
  ranking and costs two slots — not before one lever proves real.
* **Wk 4–5:** one attributable combination of receipt-verified `≥ +0.01` levers (at most two, so the
  result stays attributable), with **no relief edit** in the mix.
* **Wk 6:** re-validate both finalists on disk (format, hashes, disk re-read), lock one blind final
  file plus one fallback, freeze `AI_USE.md` and the reproducibility pins.

## Unbuilt proposals (mechanism / confounder / falsifier — not built here)

0. **Pool-extension `CONCENTRATION` rung beyond the ceiling (`downmax-plus`).** *Mechanism:* the ceiling at 2,381 moves is the 1–2-dot destination pool running dry; extend destinations to 3-dot blocks (or the strict 1-dot-only mirror) past the ceiling and read whether the marginal `−0.0002` (`conc6`→`downmax`) is destination-quality decay or a hard mechanism limit. *Confounder:* 3-dot destinations re-create the sub-kernel overlap the shave removed. *Falsifier:* `MODEL ≤ conc6` again with CV still > 0.47 ⇒ the mechanism, not the pool, is exhausted.

1. **Kernel-credit saturation pruning (`MASS` at fixed count).** *Mechanism:* replace the 1 km-CV rule
   with a direct per-dot marginal-`DTI` ranking from the metric code, delete the lowest-ranked dots
   and refill at the largest kernel gaps, so the edit targets numerator `T` instead of block
   statistics. *Confounder:* the ranking is only as good as the surrogate, and mass is monotone on
   that instrument (`IR-86-MASS-03`). *Falsifier:* `≤ 0` live Δ.
2. **A non-relief instrument for relief (§B fix).** *Mechanism:* build the RELIEF prior from the
   pinned public-domain SGMC inventory filtered to **basin-margin** traces only, and score arms
   against that rather than against a raster whose density is itself relief. *Confounder:* SGMC and
   the training catalogue share a provenance lineage. *Falsifier:* rank correlation with the shipped
   RELIEF ladder `< 0.5`.
3. **10 km fault-system concentration (`IR-86-TRACKB-08`).** *Mechanism:* every `≥ 0.26` historical
   file sits in a 10 km occupied-block CV of `0.547–0.570`; test that scale instead of the 1 km and
   5 km scales already spent. *Confounder:* 10 km blocks co-vary with the two flight regimes (400 m
   vs 200 m line spacing). *Falsifier:* `< +0.001` over `conc6` with the relief-index term held fixed.
4. **Collar-funded `TRACKB`, Phase 2 only (`IR-86-TRACKB-03/07`).** Fund `≥ 1 km` gap bridges from
   `PRUNE le3p000` collar dots on traces surviving 30° grid rotation + AGC `TMI_up150`. *Falsifier:*
   survival within `±5 %` of random-azimuth lineaments.
5. **`EVIDENCE-LIDAR` — sub-kernel scarp relocation on the pinned lidar band (`lidar_scarp_features_u8`,
   already SHA-256-pinned).** *Mechanism:* 400 m flight-line geometry limits *airborne* lineament
   position to ±150–200 m, but 1 m lidar scarps are positioned to ~1 px; move each dot ≤ 2 px onto the
   lidar scarp crest and kernel credit rises at fixed mass. *Confounder:* pluvial-shoreline treads and
   hogbacks have the same scarp expression, and the retired `SNAP` family failed because it used
   *airborne* gradients that share the flight-line error it was meant to fix. *Falsifier:* live Δ ≤
   −0.005, or no displacement-conditioned gain over a matched random-2 px SNAP control.
6. **`EVIDENCE-OFFSURFACE` — a fourth independent evidence surface.** *Mechanism:* the three ancestor
   surfaces agree on ~78 % of their pixels; the residual 22 % (35,954 px) is where a *new* lineament
   family would have to live, and PR #53 shows the parent uses none of it. *Confounder:* surface
   disagreement may be mapped-quadrangle bias rather than geology. *Falsifier:* `< +0.001` over
   `surfext10` on both instruments with its matched control.

**Human inputs still required:** `TOP_PUBLIC` + date · rolling-week slots left · verified deadline ·
R0's `0.2778` portal receipt · accepted outside-footprint encoding (`.tif` NaN vs `-zeros` fallback) ·
organizer uniqueness rule (`IR-86-PRUNE-01`).

## 2026-10-25 — H86F-GZZD lane: 0 slots used, no selector action

The H86F-GZZD lane (`docs/evidence/h86f-gzzd-run-card.json`) generated an audit-only,
locally format-valid TIFF that is HOLDOUT-DTI-negative (E1 `0.0303` [0.0237, 0.0364] vs
edge control `0.0321`, R0 `0.0339`, same-split best `0.1241`; evaluator
`gems57-pooled-hide-v2`, 11,321 withheld positives) and registry-failing (685/687
measured; PA-86-02 failed closed). **No selector ran and no weekly slot was consumed**
(`submission_slots_used = 0`). Before any future slot can be considered: repair or
formally exclude the two grid-incompatible registry rows upstream
(IR-86-H86F-GZZD-01), obtain receipt-backed organizer scores for the h33 lineage, and
present a candidate that beats same-split best HOLDOUT-DTI with a separated CI.

## 2026-10-25 — H86F-EWCS lane: HOLDOUT-DTI 0.1723 (beats same-split KSLB & controls with separated 95% CIs), 0 slots used, DO NOT SUBMIT pending registry blocker resolution

The H86F-EWCS lane (`docs/evidence/h86f-ewcs-run-card.json`) generated a byte- and
pixel-unique, locally format-valid 37,654-dot GeoTIFF (`gems86-h86f-ewcs-elastic-wing-37654dots-20261025T020534Z-47f1ed21-zeros.tif`,
SHA-256 `8322dcf157851e07...`) that **solved the scientific holdout hurdle** — achieving
`HOLDOUT-DTI = 0.1723` (`95% CI [0.1530, 0.1898]`) on `gems57-pooled-hide-v2` (`11,321`
withheld positives), beating its isotropic-tip control `E3` (`0.1592`, paired Δ `+0.0131
[+0.0012, +0.0261]`), cover-blind control `E2` (`0.1003`), fold-fair `GEMSDOE25` `R0`
(`0.0961`), and same-split `H86C-KSLB` (`0.1241 [0.1080, 0.1403]`) with separated 95% CIs,
with `0/687` Spearman `rho > 0.90` firings and `0` discrete `<= 50k`-dot overlap firings
(`26.96%` vs `GEMSDOE32`). **However, no selector ran and 0 weekly slots were used (`DO NOT SUBMIT`)**
because `14GEMSDOE` and `7GEMSDOE` remain grid-incompatible in the pinned registry index
and literal `17GEMSDOE` saturation blocks automated clearance (`IR-86-H86F-EWCS-01`).

## 2026-10-25 — H86J-LSI lane: negative, 0 slots used, no selector action

Live-score inversion: LOSO Spearman 0.900 vs owner-reported live (instrument gate PASS). The 30k candidate fails the SGMC paired gates vs H33 (−0.0325 [−0.0588, −0.0045]) and vs H86G. HOLDOUT-DTI is 0.0346 [0.0229, 0.0453] (11,321 withheld). **DO NOT SUBMIT.** Next: a bounded-link (λ ≤ 1) amendment. See `research/H86J_LSI_REVIEW.md`.
