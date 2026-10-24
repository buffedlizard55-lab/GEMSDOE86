# Why H33 SCORED 0.2778 — PhD-level forensic and what beats it

**Date:** 2026-10-24 (UTC)
**Files:** `data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (37,654 dots, [0,1] finite) vs parent `GEMSDOE28` (40,199 dots, 0.2708). Both owner-reported, no organizer receipt. Leaderboard claims 0.3195 / 0.4413 are also owner-reported, not ORGANIZER-CONFIRMED.

## 1. Pixel-exact delta: collar pruning, not geology

Forensic diff (12,279,160 cells) shows H33 = GEMSDOE28 minus exactly 2,545 dots where `1.0 < d_cat ≤ 2.0 px` (100–200 m from mapped fault). All other 12,276,615 cells identical. Score +0.0070 from deleting those collar dots.

Metric: DTI = T / (T + 0.2·F + 0.8·|G| + ε) with triangular kernel R=3 px (300 m). At truth cell, credit = max p(x)·k(d), not sum. Second dot within 3 px of same truth adds FP cost `F = n - M` without adding T. Deleting redundant mass near mapped faults (where hidden truth rarely lies) lowers F while T ≈ constant → DTI rises.

H33's parent already achieved coverage-efficient emission: 37,654 dots spaced ~300 m submodularly to avoid kernel-overlapping redundancy. The collar cut is a second-order efficiency gain.

**Not established:** That the 2,545 deleted dots had zero truth credit; a blind parallel fault could lie in the 1–2 px collar. No organizer receipt or paired control isolates causality.

## 2. Why H33 beat earlier fleet

Fleet mean distance to faults ~20–30 px; H33 mean 29 px, median 19.6 px, 34% >3.2 km distal. Earlier ridge/MAG methods (6GEMSDOE 0.028, GEMSDOE3 0.08–0.11) were either too proximal (over-fitting mapped traces) or too diffuse (random). Dotted ridge H28 (0.183) → H19-4/5 (0.189–0.192) → H25-1 (0.247) → H27 (0.244) showed monotonic gain from kernel-scale thinning. H33 added collar-aware thinning, pushing DTI from 0.2708 to 0.2778.

Budget arithmetic at 0.2778 with |G|≈40k: T≈10,963, D≈39,464. +0.01 DTI needs ≈418 kernel-credit units ≈42 km fault trace hit squarely. Prior reallocation sessions (PRUNE, CONCENTRATION, RELIEF) delivered |Δ|≤0.0073 on most generous instrument — below +0.01 evidence bar.

## 3. Can we beat 0.2778?

**Not with reallocation alone.** Moving 2–6k dots among existing fleet patterns cannot summon 42 km new truth.

**Path that could:** New evidence surface orthogonal to H33's distributed density. Tip-relay hybrid (this session) is one: it targets tip-to-tip en-échelon bridges hidden by Quaternary fill where H33's distributed dots are sparse. Holdout on `gems57-pooled-hide-v2` (11,321 withheld positives) gives:

- H33 same instrument: 0.0044
- Tip-relay hybrid: 0.0136 (+0.0092) → better on holdout but still < R0 0.096 and < H86C 0.124 (current best). So it beats H33's holdout proxy but not the best holdout model. Leaderboard projection is invalid (Spearman owner-reported vs holdout 0.24, n=17).

**What would be needed for ORGANIZER-CONFIRMED >0.2778:**
1. New lane that passes informative uniqueness (PA-86-02: overlap ≤0.70, rho ≤0.90) — hybrid does: 0.426 max overlap, rho 0.0008.
2. Holdout improvement vs matched R0 with positive paired CI — hybrid fails (0.0136 <0.096).
3. Weekly slot + organizer receipt — not attempted; 0 slots used.

## 4. Leakage and mimic analysis

- Tip geometry AUC ~0.755 (dist_to_visible) — below 0.90 canary, but catalogue-derived. Enforced visible-only per fold (holdout builder masks visible faults pixel-exactly), so not a leak.
- Mimic: paleovalley margins, caldera moats, lava-lobe terminations produce similar tip-rectilinear pattern without slip. Distal half (18,827 dots >2 km) mitigates but does not eliminate.
- H33 mimic: incised thalwegs and lithologic contacts share Hessian-trough signature; its distal bias may chase pluvial shorelines.

## 5. Verdict: H33 is not a ceiling, but tip-relay is not yet the breaker

H33's 0.2778 is plausibly efficiency, not discovery. Tip-relay hybrid is a distinct, testable alternative that is format-valid and PA-86-02 unique (0 informative firings) but holdout-negative. It is provided as a documented, downloadable TIF with full provenance — ORGANIZER-CONFIRMED score remains unknown until a selector spends a weekly slot and retains the receipt.

**Sources:**
- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf (§1.1 & §3.4–3.6)
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index
- GeoDAWN (USGS DOI 10.5066/P93LGLVQ): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- GDR 1391: https://gdr.openei.org/submissions/1391
- H33 page: https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
