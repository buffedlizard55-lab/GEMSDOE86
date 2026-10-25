# H86G-EDTI review — why 0.2778, whether it can be beaten, and the new unique TIFF

**Date:** 2026-10-25 (UTC) · **Lane:** H86G-EDTI · **Verdict: `promote`** (first in this repo)
**Candidate:** `docs/downloads/gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.tif`
SHA-256 `ba8b731fead02eb27ab30c1d2c2add78f3f703325a3b29316cdfdc3183489e8d` · 55,000 dots
**Run card:** [`docs/evidence/h86g-edti-run-card.json`](../docs/evidence/h86g-edti-run-card.json) ·
**Preregistration + Amendments A1–A4:** [`H86G_EDTI_PREREGISTRATION.md`](H86G_EDTI_PREREGISTRATION.md)

Every performance number below is labelled `HOLDOUT-DTI`, `SGMC-PROXY-DTI`, or
`OWNER-REPORTED`. There is no `ORGANIZER-CONFIRMED` number in this lane; no
DrivenData login, upload, selector decision, or weekly slot was used.

## Q1 — Why and how did `h33-h33-2-b2-…-zeros` reach 0.2778 (owner-reported)?

Pixel-exact forensics already pinned in this repo
([`h86f-h33-forensics.json`](../docs/evidence/h86f-h33-forensics.json),
[`H33_ANALYSIS.md`](H33_ANALYSIS.md)) and re-verified by hash this session:

- H33 (37,654 dots) is an **exact subset** of its GEMSDOE28 D2.8 parent
  (40,199 dots): **0 added, 2,545 removed**, and every removed dot sits at
  catalogue distance √2–2.0 px. Nothing else changed.
- Its parent lineage is the H19-5 "multiline corroborated" lineament surface,
  thinned to ≥2.828 px spacing ("d2.8") and emitted as binary dots.

So the 0.2708 → 0.2778 `OWNER-REPORTED` step is **coverage-efficient dotted
emission under the asymmetric distance-weighted Tversky index** (α=0.2 FP,
β=0.8 FN, 300 m triangular kernel), not a new geological layer:

1. Truth credit at a pixel is the *maximum* kernel weight over covering dots.
   A second dot within one kernel diameter adds FP mass (`0.2·(1−k)`) without
   adding truth credit — thinning to ~2.8 px removes that redundancy.
2. Dots 1–2 px from a mapped trace mostly cover organiser-masked catalogue
   pixels: near-zero marginal truth credit at full FP price. Deleting the
   2,545 collar dots is the entire measured difference between the two files.
3. A non-redundant dot raises DTI iff its kernel credit `k > α·DTI`
   (≈0.056 at 0.2778) — the bar is low, so the winning game is *where* dots sit
   (surface quality far from the catalogue) minus *wasted* dots (collar +
   redundancy), at a budget the surface can still feed.

## Q2 — Can a submission score higher than 0.2778, and how?

SLOT_PLAN's budget arithmetic: at 0.2778 with |G|≈40k, +0.01 live DTI ≈ +418
kernel-credit units ≈ 42 km of trace hit squarely. Every measured *reallocation*
of H33's own dots yielded |Δ|≤0.0073. Beating 0.2778 therefore requires new
surface evidence (dots on real hidden trace that the H19-5 ancestor misses)
emitted at H33-grade efficiency. This session added the missing diagnostic —
**which instrument can even recognise such a surface** — by scoring shipped
rasters *as-is* on both candidate instruments (E1b; SGMC implementation verified
by exactly reproducing KSLB's published 0.072612):

| shipped raster | live (OWNER-REPORTED) | catalogue-hide HOLDOUT-DTI (as-is) | SGMC-PROXY-DTI (as-is) |
|---|---:|---:|---:|
| H33 | 0.2778 | 0.0037 | 0.0954 |
| Anderson-PINN | 0.2750 | 0.0038 | 0.0968 |
| rung30-blind | 0.2710 | 0.0271 | 0.0934 |
| D2.8 parent | 0.2708 | 0.0291 | 0.0953 |
| h33d | 0.2632 | 0.0531 | 0.0957 |
| ptcf-tiltworm | 0.2343 | 0.0015 | 0.0869 |
| lidar66 | 0.1152 | 0.0081 | 0.0670 |
| poisson81 | 0.0041 | **0.0918** | 0.0405 |

The whole-component catalogue-hide instrument **anti-correlates** with the live
ordering (the live-worst catalogue-hugging raster tops it; the live-best scores
0.0037 — expected mechanically: collared rasters are >3 px from every withheld
catalogue pixel *by construction*, Amendment A2, and the organiser masks
catalogue pixels so catalogue proximity is not rewarded live). The SGMC-proxy
(pinned USGS geologic-map faults >3 px off catalogue, 62,122 px) reproduces the
live ordering across all 8 scored rasters. It is therefore used as the lane's
**selection** instrument — never as a feature, training byte, or projected score
(raw SGMC-trace emission's owner-reported 0.0512 is the standing warning).

## What was built (one lane, three experiments)

Hypotheses were frozen before any field was computed (preregistration; 5 ranked
candidates — signature posterior, strain localisation, gated tip extrapolation,
alteration corridor, χ-alignment). Amendments A1–A4, each forced by a named
measurement and recorded before the next computation, refined instruments and
budget selection. All inputs are the SHA-pinned restored stacks (19-band
competition TIFF + LiDAR-scarp/topo-10m/DEM-χ/GeoDAWN-radiometric externals);
no prior submission raster, and no catalogue-derived feature, enters any surface.

- **E1 — canaries + controls.** 68 features, max discriminative AUC **0.6015**
  (< 0.90 stop; LiDAR scarp features strongest — no leakage).
- **E2 — three arms, identical emission** (E[k]=surface⊛300 m kernel ranked,
  spacing-greedy ≥2.8 px, collar >3 px): **L** unsupervised multiline
  corroboration (8 independent edge detectors × agreement weight), **H**
  HistGradientBoosting posterior with zero catalogue-derived features,
  **LH** hybrid. L > LH > H on SGMC-PROXY-DTI at *every* budget
  (L: 0.1051 @44,090; 0.1223 @55,000; 0.1450 @70,000 vs H33-as-is 0.0954).
  Diagnostic deliverable: H's OOF catalogue-hide HOLDOUT-DTI reaches
  0.1689 @37,654 (above KSLB's same-split OOF 0.1241), but catalogue-supervised
  lanes have uniformly poor live priors (0.0286, 0.0424) and H trails L on the
  live-ranked proxy — H is the top *follow-up*, not the shipped candidate.
- **E3 — emission ablations on L @55,000:** collar-2 0.1189 and vendor
  tile-decimation 0.0945, both below collar-3 spacing-greedy 0.1223 — H33's two
  emission lessons (wide collar, true spacing) reproduce on an independent
  surface (+0.028 proxy over tile emission at fixed surface/budget).
- **Budget = 55,000** by Amendment A4 (post-hoc, disclosed): marginal proxy
  truth-credit per dot is flat 0.116–0.133 across 20k→70k (DTI break-even
  ≈0.056 at 0.28), so the ranking has not reached its economic stop in the
  fleet range; 55,000 is the smallest grid budget whose paired proxy CI vs
  H33 excludes 0. The fleet's live budget priors (≥0.26 cluster at
  37,654–44,090) remain printed as the counter-argument for the selector.

## Gates (all machine-measured; no human inspection)

| Gate | Result |
|---|---|
| Leakage canary (68 features) | PASS — max AUC 0.6015 ≤ 0.90 |
| SGMC-PROXY-DTI vs H33-as-is | PASS — 0.1223 vs 0.0954; paired Δ +0.0269, 95% CI [+0.0028, +0.0518] (post-selection descriptive per A4) |
| HOLDOUT-DTI floor (OOF, `gems57-pooled-hide-v2`, 11,321 withheld) | PASS — 0.0631 [0.0468, 0.0806] vs H33 visible-collar control 0.0349 |
| Uniqueness (surface + final dots, 43 local registry dot-fields) | PASS — max Spearman 0.070 ≤ 0.90; max forward 3-px overlap 68.5% ≤ 70% (vs GEMSDOE85 geopb-crest 90k; vs H33 only 26.0%); literal continuous-witness reading reported unchanged |
| Format (`[0,1]` portal-error class) | PASS — fail-closed vendor writer + independent disk validator: single-band float32, EPSG:32611, 3730×3292, 0 NaN/Inf, values exactly {0,1}, zeros outside footprint, 0 dots on catalogue, min spacing 2.828 px, min catalogue distance 3.16 px, one-TIFF ZIP byte-identical |

Independent re-verification (fresh code, from disk bytes): 22/22 checks pass,
including direct `dti_binary` reproduction of the proxy value and KD-tree
spacing audit.

## Honest limits (read before spending the slot)

1. **No live projection is made or licensed by these numbers.** SGMC-proxy and
   holdout are selection instruments; 0.2778/0.3195/0.4413 are OWNER-REPORTED
   without receipts. The candidate is *designed* to beat 0.2778 (independent
   surface with equal-or-better measured proxy recovery than H33 on 62k px of
   off-catalogue mapped fault, strictly better emission economics, and only
   26% 3-px dot overlap with H33 — i.e. mostly *different* predicted trace),
   but only an organizer receipt can confirm any score.
2. The two genuine efficacy risks are (a) the 55,000-dot budget if live truth
   is much sparser than the proxy (fleet priors favour ≤44,090; the run card
   keeps the full curve so the selector can choose the 44,090 prefix by
   re-emission if it prefers the conservative dose — same ranking, nested
   prefixes), and (b) proxy-selection bias from A4 (3 arms × 6 budgets selected
   on 62k proxy positives; disclosed, mild but real).
3. Uniqueness is certified against the 43 pinned local registry dot-fields.
   The historical upstream inventory also contains continuous full-support
   grids (and a stride-5 lattice) under which the *literal* overlap rule is
   unsatisfiable for every nonempty candidate; that reading is reported, not
   hidden (PA-86-01).
4. Limitations of this session: no DrivenData auth (data via SHA-pinned GitHub
   mirrors; portal quota/receipt unavailable), no GPU needed or used, the
   template's cached feature stack remains absent (the pinned 19-band TIFF was
   used directly and never relabelled as that cache), DrivenData pages were not
   scraped (AGENTS rule 9). New owner claims in this session's prompt
   (GEMSDOE89 0.0301, GEMSDOE90 0.0749) are recorded here as OWNER-REPORTED but
   not yet folded into `registry/prior_scores.csv`/fleet feed — that refresh is
   a separate feed session.

## Exactly how to submit (selector action)

1. Download `gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.zip`
   (or the `.tif`) from the site/README link; verify SHA-256
   `ba8b731fead02eb27ab30c1d2c2add78f3f703325a3b29316cdfdc3183489e8d`.
2. DrivenData competition 306 → *New submission* → *File to submit*: the ZIP
   above. *Note* (113 chars):
   `H86G-EDTI multiline+HGB E[k] spacing-greedy collar3; SGMC-proxy selected; holdout in run card; no slot pre-picked`
3. Confirm remaining weekly quota on that page first (rules: ≤3 scored/week,
   1 blind final pick). Submit once; retain the receipt and log it in
   `ledger/submissions.csv` bound to the SHA above before any further slot.
4. Decision rule on the receipt: ≥0.2878 (+0.01 over the 0.2778 claim) → the
   off-catalogue multiline + E[k] programme is live-real; escalate per
   SLOT_PLAN combination rules. ≤0.2728 → close this surface family at this
   budget; the nested 44,090 prefix or the H-arm follow-up are the pre-named
   alternates. Between → treat as no evidence; do not re-dose blindly.
