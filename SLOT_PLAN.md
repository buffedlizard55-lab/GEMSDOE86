# Slot plan — 2026-10-23 (two PRUNE sessions, one plan)

**No automatic slot use.** One entity, at most 3 scored submissions per rolling week under the
[official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf); actual slots remaining and
TOP_PUBLIC are UNSUPPLIED. A live `|Δ| < 0.01` is no evidence. R0 = `h33-h33-2-b2`
(**0.2778 CLAIM**, no receipt). Deadline **2026-12-03 is user-supplied and UNVERIFIED**
(DrivenData is not contacted from this sandbox): 41 days ≈ 5 weeks 6 days.

Four PRUNE artifacts are built and gate-clean. **Only one `(PRUNE, 3)` may be spent** — two
exist (IR-86-PRUNE-08), so the plan spends the pair once and uses the other as a local control.

## Next three slots, in order

1. **PRUNE≤3 + fixed-count H19-5 refill** — `releases/h33-h33-2-b2-prune3-20261023-01d57649.tif`
   (zeros twin `…-01d57649-zeros.tif`). 37,654 dots, 11.53 % changed, **−0.004 MODEL**.
   *Teaches:* does deleting the 200–300 m annulus help when mass is held? *Caveat:* the required
   refill pushes mean nearest-neighbour spacing 3.735 → 3.550 px, so PRUNE and SPACING are not
   separated in this design. *Decision:* Δ ≥ +0.01 → push the collar to 4 px (slot 2);
   Δ ≤ −0.01 → the annulus is load-bearing, stop widening and switch axis; `|Δ| < 0.01` → slot 3.
2. **PRUNE≤4 (pure deletion)** — `releases/h33-h33-2-b2-prune4-20261023-e198b768-nan.tif`
   (zeros twin `…-de4c2a98-zeros.tif`). 33,829 dots, 10.16 % changed, **−0.008 MODEL**.
   *Teaches:* is the collar effect monotone in width? This is a genuinely new value (4 px was
   never built). *Decision:* Δ ≥ +0.01 → continue to 5–6 px; Δ ≤ −0.01 → the collar curve is
   closed permanently.
3. **PRUNE≤3, equal count, collar relocated just past 3 px** —
   `releases/h33-h33-2-b2-prune3r-20261023-9542efac-nan.tif` (zeros twin `…-8c20bd7e-zeros.tif`).
   37,654 dots, 11.53 % changed, mean move 1.14 px, **−0.003 MODEL**.
   *Teaches:* mass versus collar position, with spacing nearly preserved. Only worth a slot if
   slots 1–2 land within ±0.01 of each other; otherwise the answer is already known.

**Not recommended for a slot:** `releases/h33-h33-2-b2-prune3-20261023-3eb29af5-nan.tif`
(pure deletion, 35,483 dots, −0.003 MODEL). It duplicates the `(PRUNE, 3)` pair already spent
on slot 1. It stays useful as the local *deletion-side* control for slot 3: `prune3` and
`prune3r` share the identical 2,171 deletions and differ only in whether the count is held.

Do **not** re-submit R0 or any `-zeros`/`-nan` twin of an already-scored file: at least 8
historical slots went to exact repeats (brief §3), and twins score identically.

## Calendar to the deadline

- **wk 1–2 (slots 1–3).** PRUNE collar sweep above. Exit test: any variant ≥ R0 + 0.01.
- **wk 2–3. MASS** (±10 % by the parent's own rank, count held). Blocked today: R0's ranking is
  not stored and `gems32` is absent from this checkout (IR-86-PRUNE-02). Recover the ranking
  first; never substitute an invented ordering.
- **wk 4. CONCENTRATION** on 5 km blocks: move 10–20 % of dots from the lowest-prior to the
  highest-prior blocks; record the block-density CV (best files reportedly 0.51–0.59).
- **wk 5. Combine** the two axes with receipt-level effects ≥ 0.01 and a coherent mechanism,
  each as a single attributable edit; add one SNAP probe (dots to the strongest
  `tmi_hg`/`iso_grav_anom_hg` edge within 2 px, same count, report mean displacement).
- **wk 6. Confirm and freeze.** Re-validate both finalists' formats, choose the final file and a
  fallback blind, keep one final-submission choice, and never multiply accounts.

## Better future axes (proposals only; not built)

- **Collar fill inward (PRUNE, 2.5).** If slot 1 is negative, the annulus is short of dots.
  *Confounder:* added mass can never earn credit on masked pixels. *Falsifier:* a live drop
  > 0.01 versus R0 kills the direction.
- **Spacing-matched collar test.** Equal-count collar sets with preregistered nearest-neighbour
  matching. *Confounder:* eligible cells shift geography and relief. *Falsifier:* the collar
  effect disappears after spacing and block-density matching.
- **Exact-marginal PRUNE.** Remove dots with the most negative exact ΔDTI under the shared
  two-sided metric. *Confounder:* proxy-truth shift and tuning on SGMC. *Falsifier:* no
  replicated positive sign on untouched spatial folds, then no live receipt.
- **Annulus-conditional RELIEF.** Test the 200–300 m annulus separately per relief tercile.
  *Confounder:* relief controls both catalogue completeness and lineament visibility.
  *Falsifier:* no consistent sign in two relief regimes on held-out physical blocks.
