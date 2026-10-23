# Slot plan — 2026-10-23

**No automatic slot use.** One entity, at most 3 scored submissions per rolling week under the [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf); actual slots remaining and TOP_PUBLIC are UNSUPPLIED. A live `|Δ| < 0.01` is no evidence. R0 = `h33-h33-2-b2` (0.2778 CLAIM, no receipt).

## Next three slots, in order

1. **PRUNE≤3 + fixed-count H19-5 refill** — built locally; exact filename and hashes are in `docs/SUBMIT.md`. Prediction: **−0.004 MODEL**. If Δ≥+0.01, investigate the 200–300 m annulus with a spacing-matched design; if Δ≤−0.01, protect that annulus and stop widening the collar; otherwise no inference.
2. **MASS−10%** — not built; requires a human axis assignment and a ruling on R0's inherited 2–3 px dots. Drop the lowest-ranked 10% using the recorded parent ranking. A ≥+0.01 result supports testing less mass; ≤−0.01 rejects that direction; otherwise no inference.
3. **MASS+10%** — not built and conditional on slot 2. Add the next-ranked 10%, not arbitrary new geology. A ≥+0.01 result supports a mass deficit and one confirmation; ≤−0.01 stops additions. If slot 2 is decisively positive, use slot 3 for MASS−20% instead only after recording that new `(axis,value)` experiment.

## Calendar to the deadline

The user-supplied deadline is **2026-12-03 (UNVERIFIED)**: 41 days / 5 weeks 6 days after 2026-10-23, so plan six weeks. Weeks 1–2: controlled MASS, CONCENTRATION, SNAP, PRUNE and RELIEF experiments as assigned, never repeated `(parent,axis,value)` pairs. Weeks 3–4: combine only the two axes with receipt-level effects ≥0.01 and a coherent mechanism. Weeks 5–6: confirm both finalists, choose the final and fallback blind, and revalidate both formats. Preserve one final-submission choice; do not multiply accounts or feedback.

## Better future axes (proposals only; not built)

- **Exact-marginal PRUNE:** remove dots with the most negative exact ΔDTI under the shared two-sided metric. *Confounder:* proxy-truth shift and tuning on SGMC. *Falsifier:* no replicated positive sign on untouched spatial folds and a subsequent live receipt.
- **Spacing-matched collar test:** compare equal-count collar sets with a preregistered nearest-neighbour-distance match. *Confounder:* restricting eligible H19-5 cells can shift geography and relief. *Falsifier:* the apparent collar effect disappears after spacing and block-density matching.
- **Annulus-conditional RELIEF:** test the 200–300 m annulus separately in basin/piedmont/range-front terciles. *Confounder:* relief determines both catalogue completeness and lineament visibility. *Falsifier:* no consistent sign in at least two relief regimes on held-out physical blocks.

---

# Addendum — the two remaining PRUNE rungs (same day, second session)

`(PRUNE,3)` is already built by the earlier session (≤3 px **+ fixed-count refill**, 37,654 dots,
predicted −0.004 MODEL) and is that session's slot-1 candidate. I did **not** build a second version of
it: my `…-le3p000-…-a438e92b` is the **mass-reduced twin** of the same collar edit (no refill,
35,483 dots), labelled as such in the ledger.

What was missing from the axis, and is now built (`releases/`, gitignored — rebuild with
`scripts/run_prune_ladder.py`):

| rung | dots | removed | predicted Δ (MODEL) | zeros sha256 |
|---|---:|---:|---|---|
| `(PRUNE, √5 ≈ 2.236 px)` | 36,713 | 941 (2.50 %) | +0.001 [−0.003, +0.003] | `82b3f1f4024a…` |
| `(PRUNE, √8 ≈ 2.828 px)` | 36,043 | 1,611 (4.28 %) | +0.003 [−0.003, +0.008] | `6ff386184585…` |
| `(PRUNE, 3.0 px, no refill)` | 35,483 | 2,171 (5.77 %) | +0.004 [−0.004, +0.013] | `a438e92b79df…` |
| `CONTROL` (same mass, far field) | 35,483 | 2,171 (5.77 %) | 0.000 [−0.004, +0.003] | `a2a8be25eaab…` |

The whole remaining axis is 2,171 dots (5.8 % of mass) inside three distance shells; at the best
per-dot rate this axis can move (+2.75 × 10⁻⁶ from the one live collar datum) the entire ladder fits
inside ±0.01. **One slot, not three.** Rung order if the human wants a second: √8 then √5 (nested, so a
monotone answer identifies the optimum), never the control unless a rung moves ≥ +0.010.

If the refilled `(PRUNE,3)` and the no-refill twin both get scored, the *difference* between them is a
clean mass experiment at fixed collar — that pair is worth more than either file alone.

New axis proposal that this session can actually justify (not built): **annulus-stratified PRUNE**, i.e.
score the 2–3 px annulus, the 3–5 px band and the >5 px field as three separate mass pools in one
factorial, with the mass-matched control as the fourth cell. Mechanism: the organizer states new-fault
truth *can* lie within 300 m of known traces, so the sign of the collar effect should change at some
radius — this design measures where. Confounder: mass, which the control absorbs. Falsifier: no
sign change anywhere in 2–8 px means the collar is not a real structure and every future prune argument
is a mass argument. Blocked only by the weekly slot count, not by missing data.
