# SLOT PLAN — 2026-10-23 (CONCENTRATION dose ladder session; ≤ 1 page)

**No automatic submission.** One entity, `<= 3` scored submissions/rolling week, one final blind
file (Phase 1 $50k DTI, Phase 2 $250k expert-expanded labels) — [official
rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf). Deadline `2026-12-03` (**UNVERIFIED** portal
clock). `TOP_PUBLIC`, slots left, and R0's live receipt are **UNSUPPLIED**. Parent **R0 =
`h33-h33-2-b2`** (`37,654` unit-mass dots, `0.2778` **CLAIM**, `0` `RECEIPT` rows). Live
`|Δ| < 0.01` = no evidence.

## What this session changed in the plan

The dose ladder (`evidence/concentration-dose-mechanism.md`, measured post-hoc against a written
pre-registration) settled three things:

* **Monotone, not inverted-U.** SGMC `MODEL` rises `+0.0013 → +0.0018 → +0.0022` and fold-fair
  `PROXY` `+0.0004 → +0.0010 → +0.0013` as the dose goes 3 % → 5 % → 6 % of R0, while 1 km occupied
  CV falls `0.5377 → 0.4998 → 0.4840`. The best arm sits **outside** the historical `0.51–0.59`
  band, so the CV band is a correlate, not the cause (`IR-86-CONC-13`).
* **Two-thirds of that gain is generic dispersal.** The matched ordering control (random dot,
  random destination, same blocks, same count) gets `+0.0015` MODEL / `+0.0008` PROXY against the
  ranked `+0.0022` / `+0.0013`. The credit ranking buys only `≈ +0.0007` MODEL.
* **The axis is capacity-capped at ~6.4 % of R0** on this parent's ridge support at R0's own
  `√8 px` spacing (`IR-86-CONC-12`): 8 % needs 3,012 1 km destinations and only 2,399 exist. Higher
  doses are not available without changing a second variable.

`conc6` dominates PR #47's `concb5kmdown4` on both report-only instruments at 753 extra moved dots.
That is a better candidate, not a proven gain.

## Next weekly slots (one file per slot, human uploads)

| Slot | Candidate (`releases/<id>`) | Edit vs R0 | Predicted Δ (MODEL, not a score) | Decision rule on live `RECEIPT` Δ vs 0.2778 |
|---:|---|---|---|---|
| **1** | `h33-h33-2-b2-20261004-e5eb6e7e-PRUNE-le3p000-20261023-a438e92b-zeros.tif` | delete 2,171 dots (`5.77 %`) in the `2.0 < d_cat <= 3.0 px` collar; 35,483 dots | `+0.0040` (largest predicted lever; partly mass-confounded, `IR-86-MASS-04`) | `>= +0.010`: collar halo is active drag → next slot probes `4.0 px`; flat/`<= -0.005`: keep 2 px, close PRUNE |
| **2** | `h33-h33-2-b2-20261004-e5eb6e7e-RELIEF-frontp15-20261023-e0e2888f-zeros.tif` | 5,648 dots (`15 %`) piedmont → range front, count fixed | `+0.0017` (3/4 quads +) | `>= +0.010`: range-front allocation wins → combine with the slot-1 winner; `<= -0.005`: close RELIEF |
| **3** | `h33-h33-2-b2-20261004-e5eb6e7e-conc6-20261023-1ed78e0f-zeros.tif` **(new)** | 2,259 dots (`12 %` changed) 1 km CV `0.6235 → 0.4840`, count fixed | `+0.0022` MODEL (4/4 quads, `+0.0028` jitter), `+0.0013` PROXY; **≈ `+0.0007` above its own dispersal control** | `>= +0.010`: density-cap dispersal is a real lever → 6 % is the ceiling, so combine; `<= -0.005`: dispersal is neutral-to-negative on private chunks → close CONCENTRATION for good |
| *4 (wk 2 alt)* | `…-conc5dose-20261023-a2f8aaad-zeros.tif` | 1,883 dots (`10 %`), CV `0.4998` | `+0.0018` MODEL / `+0.0010` PROXY | Only if slot 3 returns a *positive but sub-0.01* Δ and a paired dose point is worth a slot |

**Never upload:** `conc6rand` (`CONTROL`, ordering control), `concb5kmup4/up8` (`-0.0005/-0.0007`),
`conc15` (`-0.0071`), `dens15`/`spr15` (`-0.0006/-0.0013`), `b5km-move10/15/20`
(`-0.0066..-0.0150`), all `MASS` arms, all `SNAP` arms, `trackb-cull1dot`.

## Calendar to 2026-12-03

* **Wk 1:** slots 1–3 as ordered. Log the live `RECEIPT` score + date in `ledger/submissions.csv`
  before the next upload.
* **Wk 2–3:** second dose only on an axis that cleared `|Δ| >= 0.01`; otherwise the two next-best
  levers from the table above. A paired CONCENTRATION A/B (ranked `conc6` vs its own control) is
  the only clean way to price the ranking, and it costs two slots — not before one lever proves
  real.
* **Wk 4–5:** one attributable combination of receipt-verified `>= +0.01` levers (at most two,
  so the result stays attributable).
* **Wk 6:** re-validate both finalists on disk, lock one blind final file and one fallback.

## Unbuilt proposals (mechanism / confounder / falsifier — not built this session)

1. **Kernel-credit saturation pruning (`MASS` at fixed count).** *Mechanism:* replace the 1 km
   CV-band rule with a direct per-dot marginal-`DTI` ranking computed from the metric code, deleting
   the lowest-ranked dots and refilling at the largest kernel gaps, so the edit targets numerator
   `T` instead of block statistics. *Confounder:* the ranking is only as good as the SGMC surrogate,
   and mass changes are monotone on that instrument (`IR-86-MASS-03`). *Falsifier:* `<= 0` live Δ
   while `conc6` is positive.
2. **Two-scale dispersal (1 km + 5 km).** *Mechanism:* apply the same shave rule simultaneously at
   1 km and 5 km blocks so the CV reduction survives coarse-grid aggregation. *Confounder:* the 5 km
   arm alone is negative (`up8` `-0.0007`); mixing scales could cancel. *Falsifier:* live Δ below the
   single-scale arm.
3. **Dose ceiling under a relaxed spacing floor.** *Mechanism:* the ladder is capped at 2,399
   destinations by `√8 px` spacing; measure whether a `3.0 px` floor would unlock the 8–10 % dose
   the monotone curve wants. *Confounder:* spacing itself is an axis (SPACING `strike16` `+0.0020`),
   so the dose and the floor become confounded. *Falsifier:* Δ ≤ `conc6` at higher dose.

**Human inputs still required:** `TOP_PUBLIC` + date · rolling-week slots left · verified deadline ·
R0's `0.2778` portal receipt · accepted outside-footprint encoding (`.tif` NaN vs `-zeros` fallback) ·
organizer uniqueness rule (`IR-86-PRUNE-01`) · whether the tracked bridge rasters may stay in history
(`IR-86-PRUNE-04`).
