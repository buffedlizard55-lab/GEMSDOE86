# RELIEF source factorial — mechanism cards (pre-registered 2026-10-23, before any build)

**Parent:** R0 `h33-h33-2-b2-20261004-e5eb6e7e`, sha256 `c55bafc4…b6fa9`, 37,654 unit-mass
dots, rebuilt byte-exactly from pinned `GEMSDOE28 h27-4-r1-solo-d2-8` (`ab023001…`) with
`d_cat > 2.0 px` in this session before anything was built.

**Axis:** RELIEF (session-assigned; brief v2 §1 leaves the axis to the agent and forbids
prompting the human for it). Every arm is count-fixed at 37,654 dots, moves dots only
between relief regimes read off the pinned detrended-elevation bands (`det_elev` = band 12,
`det_elev_slope` = band 19), and leaves every other property of R0 untouched.

**Why this and not another `front+<dose>` rung.** The three existing RELIEF rows
(`front+10pct` +0.0010, `front+15pct` +0.0017, `front-10pct` −0.0089 MODEL, all
`ledger/submissions.csv`) all vary **dose**, never **source**. They share one structural
weakness: they move mass from the middle tercile into the *high* tercile, and the only
local instrument that predicts them — the SGMC-extra surrogate — is itself strongly
relief-weighted (single-feature AUC `relief_index → SGMC-extra = 0.7281`, recorded in
`evidence/relief_axis_20261023.json`). A dose ladder inside that confound cannot tell a
geological effect from the instrument's own relief gradient. This session varies the
**source at fixed destination** and adds a **destination control at fixed source**, so the
family's numbers can be decomposed instead of only extended.

## Arms

| id | value | source → destination | dots moved | % of R0 |
|---|---|---|---:|---:|
| `int2front15` | `int2front-15pct` | range-interior (4) → range-front (2) | 5,648 | 15.00 |
| `int2front10` | `int2front-10pct` | range-interior (4) → range-front (2) | 3,765 | 10.00 |
| `int2pied15` | `int2pied-15pct` | range-interior (4) → piedmont (1) | 5,648 | 15.00 |

Both 15 % arms sit at the dose of `front+15pct`, and `int2front10` sits at the dose of
`front+10pct`, so each new row is **matched-dose** against an existing row. `plan_moves`
orders sources by distance to their own regime boundary, so the 10 % rung is a strict
prefix of the 15 % rung **within the same source** (asserted in the run script).

### Card 1 — `int2front15` (primary candidate)

* **Hypothesis.** At fixed dose and identical destination, taking the mass out of the range
  interior pays more than taking it out of the piedmont: the interior is where a
  basin-and-range lineament is most likely to be a pre-Quaternary intrarange structure,
  a bedrock fabric, or an erosion edge rather than an active basin-margin trace.
* **Mechanism.** DTI charges `alpha·(1 − k)` for every dot more than 3 px from truth. A dot
  that is *right about geometry but wrong about kinematics* (old structure, not a fault the
  organisers' new mapping includes) pays that charge in full while contributing no `T`. The
  basin-margin scarp is the one relief class where the catalogue itself is dense, and
  catalogue pixels are masked out of scoring (`active = valid & ~known` in
  `gems57.metric.dti_binary`), so mass parked near a mapped front fault is partly *free*
  rather than charged — the same destination argument that produced `front+15pct`, now with
  a source selected to remove the class with the weakest active-fault prior.
* **Non-fault process that could mimic it.** (i) The SGMC-extra surrogate is high-relief
  weighted (AUC 0.73), so any arm that keeps mass at high relief looks good on it —
  *this arm is deliberately inside the high tercile for both source and destination, so it
  is the least bias-prone of the RELIEF family, but the bias is not zero.* (ii) The
  interior is where the 400 m GeoDAWN flight lines leave the largest positional error
  (≈ kernel radius, brief §2), so relocating interior mass 5–15 km is a *re-siting* of
  uncertain dots, not a re-labelling of well-located ones. (iii) A genuine positive could
  also be produced by the mass leaving a *cluster* rather than leaving the *regime* —
  controlled here by the displacement-matched null in the run card.
* **Pre-registered prediction.** `+0.0010 MODEL`, band `−0.0050…+0.0060`. Below the 0.01
  live-evidence floor by construction: **no single-slot bet.**
* **Falsifier.** Live `Δ ≤ −0.010` falsifies "interior mass is the weaker mass" and says
  R0's intrarange dots are finding truth the catalogue misses. A MODEL reading of
  `≥ +0.006` (above every existing RELIEF row) would instead say the surrogate's *source*
  sensitivity is real, which is the only route by which this axis becomes slot-worthy.

### Card 2 — `int2front10` (nested prefix, dose slope)

* **Hypothesis.** Same mechanism at two-thirds the dose; the pair gives the source-specific
  dose slope at no extra interpretive cost, and is matched-dose to `front+10pct`.
* **Mechanism.** Identical to Card 1; the only change is how deep into the source class the
  moved dots are taken from (deepest first, so the 10 % set is a strict prefix).
* **Non-fault process.** Same as Card 1; additionally, a 10 % arm moves only the deepest
  interior dots, whose mean displacement is larger — if pure displacement is what pays, the
  10 % rung can beat the 15 % rung and the "linear dose" reading fails (that is the test).
* **Pre-registered prediction.** `+0.0005 MODEL`, band `−0.0045…+0.0045`.
* **Falsifier.** `int2front10 > int2front15` by more than 0.003 on the surrogate ⇒ the
  effect is displacement-selected, not regime-selected, and the whole RELIEF family's
  precedent (`front+10` < `front+15`) does not generalise.

### Card 3 — `int2pied15` (destination control, fixed source)

* **Hypothesis.** If what pays is *leaving the interior*, this arm matches Card 1 despite
  landing in the middle tercile. If what pays is *reaching the basin-margin scarp*, this arm
  is flat or negative. Either way it prices the destination, which no existing RELIEF row
  does at a matched source.
* **Mechanism.** Same source selection as Card 1; destinations are the nearest free
  piedmont cells (the piedmont abuts the interior, so displacements are much shorter than
  Card 1's — mean displacement is reported, and the difference is part of the result).
* **Non-fault process that could mimic it.** Because this arm *lowers* mean relief index it
  runs against the surrogate's own relief gradient; it is therefore the arm most likely to
  read negative for instrumental rather than geological reasons. A negative here is
  consistent with both hypotheses and must not be read as evidence against Card 1.
* **Pre-registered prediction.** `−0.0020 MODEL`, band `−0.0080…+0.0030`.
* **Falsifier.** A live `Δ ≥ +0.005` while Card 1 is ≤ 0 would say the interior dots were
  the waste and the front destination is irrelevant — i.e. it would re-open RELIEF as a
  *source-removal* axis rather than a *front-accumulation* axis.

## Report-only instruments (never gates, brief §6)

* **SGMC-extra surrogate** (USGS SGMC pixels not in the training catalogue; manifest pin
  `ext_derived_sgmc_faults_100m_u8`, `643cbe99…`) — the MODEL number on every card.
* **Catalogue hide-and-recover PROXY** (`proxy_dti`, 10 whole-component draws, seed 306) —
  contaminated by construction for catalogue-avoiding fields; recorded, never called a score.
* **Displacement-matched null (new this session):** the same 5,648 dots moved the same
  distance distribution onto *random* eligible cells, scored on the same surrogate. It
  prices pure relocation and is the control that decides how much of `front+15pct`'s
  `+0.0017` is displacement rather than relief. Not written as a raster, not a slot.
* **Leakage canary**: single-feature AUC against catalogue and SGMC-extra on a 400 k cell
  sample; `> 0.90` stops the run.

## Post-build results (appended after the build; the cards above are unchanged)

Built, gated and measured in `evidence/relief_source_20261023.json`. Parent gate re-ran first:
R0 rebuilt byte-exactly (`c55bafc4…`), 0 differing pixels.

| arm | dots moved | mean disp. | MODEL Δ (surrogate) | quadrants | PROXY mean | vs its own null |
|---|---:|---:|---:|---:|---:|---:|
| `int2front-15pct` (`c543e779`) | 5,648 (15.00 %) | 42.9 px | **−0.0057** | 1/4 `+` | 0.00375 | −0.0027 |
| `int2front-10pct` (`4471a74b`) | 3,765 (10.00 %) | 43.4 px | **−0.0038** | 1/4 `+` | 0.00405 | — |
| `int2pied-15pct` (`295eaf92`) | 5,648 (15.00 %) | 37.7 px | **−0.0118** | 1/4 `+` | 0.00375 | −0.0088 |
| R0 (reference) | — | — | 0 | — | 0.00436 | — |
| null, interior source | 5,648, random destination | 42.5 px | −0.0030 | — | — | — |
| null, piedmont source | 5,648, random destination | 58.6 px | −0.0026 | — | — | — |
| `front+15pct` reconstruction | 5,648 | 61.1 px | +0.0017 | — | — | +0.0043 |

**Pre-registration outcome: falsified in sign.** Card 1 predicted `+0.0010` (band −0.005…+0.006);
measured `−0.0057`, i.e. outside the band and negative. Card 2 predicted `+0.0005`; measured
`−0.0038`. Card 3 predicted `−0.0020` (band −0.008…+0.003); measured `−0.0118`, also outside its
band. The direction of the three arms *relative to each other* is the opposite of the hypothesis:
moving interior mass to the **piedmont** is worst, moving it to the **front** is less bad, and
leaving the interior at all costs more than the destination buys. The falsifier for Card 1
("live Δ ≤ −0.010 … or a MODEL reading ≥ +0.006") fired on the negative side: the surrogate says
R0's intrarange dots are *more* productive than its piedmont dots, not less.

**Why that is not yet a geological conclusion.** Both nulls are negative (−0.0026, −0.0030) and
the instrument's response across all eight rebuilds is `R² = 0.9135` on Δ mean relief index
(`IR-86-RELIEF-04`). The arm ordering above is exactly the Δ index ordering, so the family's
numbers — including the shipped `front+15pct`'s `+0.0017` — are explained by the instrument's own
relief gradient rather than by fault content. The correct reading of this session is therefore
*narrow and negative for the instrument*, not positive or negative for the geology.
