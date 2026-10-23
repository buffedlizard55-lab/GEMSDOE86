# AXIS mechanism cards — session 2026-10-23 (parent R0 = `h33-2b2`, GEMSDOE32)

Written for a structural geologist. Each card names the hypothesis, the physical mechanism,
the **non-fault process that could mimic it**, the predicted sign and size of the *live*
change, and the observation that would falsify it.

Every number below is a measurement made in this checkout, or is labelled CLAIM / PROXY /
MODEL. Nothing here is a score. Parent R0's 0.2778 is a **CLAIM** (owner-reported; no
submission-page receipt exists in this repo).

Shared parent facts, measured this session from the hash-pinned parent bytes
(`sha256 c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`, which is the
`registry/data_manifest.json` pin for `scored_h33_2_b2_zeros`):

| quantity | value |
|---|---|
| dots | 37,654 (0.729 % of the 5,167,373-px footprint) |
| catalogue pixels | 60,988 |
| dots on catalogue pixels | 0 |
| min distance dot → catalogue | 2.236 px (224 m); 941 dots ≤ 2.5 px; 2,171 ≤ 3 px |
| mean distance dot → catalogue | 28.997 px (2.90 km) |
| nearest-neighbour spacing | min 2.828 px (= 2√2, the parent's d2.8 thinning), median 3.0 px |
| 1 km block density CV, occupied blocks | 0.6235 (15,976 of 122,717 blocks occupied) |
| parent lineage | R0 ⊂ the 44,090-dot d2.8 set (verified: 0 R0 dots outside it) |

---

## 1. PRUNE `collar3px` — `gems86-h33-2b2-prune3-20261023-e4027684`

**Hypothesis.** Dots sitting 2–3 px (200–300 m) from a mapped trace mostly re-cover the
*known* fault that the organiser masks pixel-exactly, so they buy almost no credit for
**new** faults while still paying full false-positive mass. Widening the exclusion collar
from the parent's 2 px to 3 px should therefore raise DTI.

**Mechanism.** The metric is `DTI = T / (0.2T + 0.2(S−M) + 0.8|G|)`. A dot earns credit only
where the 300 m triangular kernel reaches an *unmasked* truth pixel. Inside a 300 m collar
of a mapped trace, the kernel's reach is largely consumed by the masked trace itself, so
the marginal credit of a collar dot is small while its contribution to `S−M` is unchanged.
Removing 2,171 collar dots and re-spending that budget on the largest remaining kernel gaps
in the parent's own support surface raises `T` per unit of `S`.

**Non-fault process that could mimic it.** Nothing geological mimics this axis — the risk is
metric-side, not lithological: the collar also deletes the *only* cover of a genuinely new
parallel strand, splay or antithetic fault that happens to run 200–300 m from the mapped
trace. Basin-margin normal-fault systems in this province commonly carry 100–400 m
antithetic and hanging-wall-splay sets at exactly that spacing, so the collar can delete
real geometry.

**What was built.** 2,171 dots removed (5.77 %), 2,171 refilled inside the parent's H19-5
support mask (121,131 px) at the largest remaining kernel gaps: 475 at the parent's own
2.83 px thinning, 1,696 at a relaxed >2 px floor because the support mask is *saturated* at
2.83 px (only 611 free cells region-wide). Count held exactly at 37,654. 11.531 % of dots
changed, Jaccard 0.891. Mean catalogue distance 28.997 → 30.305 px; minimum 3.162 px.

**Predicted live change.** **+0.004** (range +0.002 … +0.006). MODEL only. The single prior
step on this axis (2 px collar on a 40,199-dot base → 37,654) is CLAIMED to have moved
0.2708 → 0.2778 (+0.0070) in GEMSDOE32's own scan
(`evidence/h33_removal_rule_scan.json`, mirror ref `780a5a53`); that scan's holdout means
also rose monotonically (0.26305 → 0.26792). Extending one more pixel should be smaller than
the first step, because the 2–3 px annulus is thinner and less catalogue-dominated.

**Falsifier.** A live change ≤ 0.00 (or a drop) falsifies it: it would mean the 2–3 px
annulus was carrying real new-fault cover, i.e. the collar is deleting signal, not
redundancy. A change under 0.01 is *no evidence* either way (public chunks only).

---

## 2. CONCENTRATION `b1km-move15` — `gems86-h33-2b2-conc15-20261023-2b883f2d`

**Hypothesis.** New fault pixels are not uniformly distributed: they concentrate where
mapped systems interact — step-overs, tips, intersections, relay ramps — because that is
where strain localises and where mapping is most incomplete. Moving 15 % of the dot budget
out of the lowest-prior 1 km blocks into the highest-prior ones should raise `T` at constant
`S`.

**Mechanism.** Per-block prior = z(catalogue fault density, 3×3 km mean) + z(mean Sobel
gradient of TMI upward-continued to 150 m). The first term is the fault-interaction prior
(the Faulds step-over/termination inventory used *only* as a prior on interaction zones, as
the brief requires); the second is the magnetic lineament response, which is where an
unmapped, sediment-covered strand is most likely to be detectable. The 5,648 lowest-prior
dots are removed; replacements are placed in the top 20 % of prior-bearing blocks (10,462
blocks) at the largest remaining kernel gap — **geometric placement only**, so this axis
cannot quietly become SNAP.

**Non-fault process that could mimic it.** Two. (1) *Mapping effort*, not geology: the
catalogue is dense near roads, mine pits and published 1:250k quadrangles, so "high
fault-interaction density" partly encodes where a geologist once walked. (2) *Magnetic
edges without faulting*: lithologic contacts, intrusive margins, propylitic/argillic
alteration fronts and survey-line seams all produce TMI gradients. GeoDAWN Area 2 was flown
at 400 m line spacing 150–200 m above terrain, so lineament positions carry uncertainty of
about one kernel radius — the prior is smooth at best.

**What was built.** 5,648 dots relocated (all 5,648 at the parent's 2.83 px spacing, no
relaxation needed). Count held at 37,654; 29.999 % changed; Jaccard 0.739. Block size 1 km
(10×10 px). **Block-density CV over occupied blocks 0.6235 → 0.7644**; occupied blocks
15,976 → 14,339; mean dots per occupied block 2.357 → 2.626.

**Predicted live change.** **+0.006** (range +0.003 … +0.010). MODEL only.

**Falsifier.** A live change ≤ 0.00 falsifies the interaction-prior reading and would also
argue that the reported "best files sit at block CV 0.51–0.59" band is real: this variant
moves *away* from that band (0.62 → 0.76), so a drop here is evidence that the region wants
*less* clustering, not more. Note that R0 itself measures 0.6235, outside the reported
0.51–0.59 band, so that band's provenance is unverified (see `IRREGULARITIES.md`).

---

## 3. SNAP `2px` — `gems86-h33-2b2-snap2-20261023-6ec42a92`

**Hypothesis.** The parent's dot positions inherit the geometry of a 0.7 %-coverage
lineament *field*, so individual dots can sit 100–200 m off the physical scarp or magnetic
contact they were meant to mark. Relocating each dot ≤ 2 px (≤ 200 m) onto the strongest
local edge/scarp response should convert near-misses into kernel hits at zero cost in count.

**Mechanism.** Response = z(Sobel gradient magnitude of TMI upward-continued to 150 m) +
z(mean of z(|profile curvature|), z(max slope), z(hillshade lineament)) from the pinned
USGS 10 m-derived topographic product. Each dot moves to the response argmax inside its
Euclidean 2 px disk (the 2.83 px corners are excluded, so the brief's "≤ 2 px" holds
exactly); count, exclusions and catalogue clearance are unchanged.

**Non-fault process that could mimic it.** Scarps and sharp magnetic gradients in this
basin-and-range setting are produced by (1) range-front alluvial-fan edges and
lake-terrace/paleoshoreline scarps of pluvial Lake Lahontan, (2) landslides and debris-flow
fronts, (3) roads, canals and mine benches, and (4) survey seams and upward-continuation
artefacts in the TMI grid. All of these are sharp, linear and non-tectonic; snapping onto
them converts a plausible lineament dot into a confidently wrong one.

**What was built.** 33,880 of 37,654 dots moved; mean displacement **1.4349 px (143 m)**,
median 1.4142 px, max 2.0 px. 1,701 dots could not move because their argmax was already
taken (they stayed put); 0 were blocked by the clearance rule. Count held at 37,654;
179.954 % changed (SNAP is the one axis the brief exempts from the 1–50 % rule); Jaccard
0.053 — low *pixel* overlap but a small *spatial* change, 143 m against a 300 m kernel.
Mean catalogue distance 28.997 → 29.021 px, i.e. the axis barely perturbs the collar.

**Predicted live change.** **+0.004** (range +0.001 … +0.008). MODEL only. The mechanism can
only help where the parent's field was misregistered by ~100 m, and the GeoDAWN line-spacing
uncertainty is of the same order, so the expected gain is genuinely small.

**Falsifier.** A live change ≤ 0.00 falsifies it and would mean the parent's registration is
already at or better than the data's own positional uncertainty — in which case further
sub-kernel repositioning is not a usable axis. A *drop* would additionally implicate the
non-fault scarps above (Lahontan shorelines, fan edges, roads) as the dominant attractor.

---

## Reading order for the three slots

PRUNE first (smallest edit, 11.5 %, and the axis already has a CLAIMED positive step),
then SNAP (count- and exclusion-preserving), then CONCENTRATION (largest edit, 30 %, and the
only one that moves mass between km-scale blocks). If only one slot is available, spend it
on PRUNE.

## Provenance of every external input

| input | pin | provenance |
|---|---|---|
| `existing_faults.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | owner mirror of the competition catalogue |
| `sample_submission.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | owner mirror of the competition format file |
| parent R0 | `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9` | owner mirror, GEMSDOE32 `780a5a53` |
| H19-5 support mask | `ec1f9b56b…` (`scored_h19_5`) | owner mirror, GEMSDOE24 `07345ea0` |
| `geodawn_extensions_u8.tif` (TMI up-150 m) | `a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b` | USGS GeoDAWN, DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ), public domain |
| `geodawn_rad_u8.tif` | `c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682` | same, public domain |
| `topo_10m_derived_100m_u8.tif` | `a6398d995096f…` | USGS 3DEP-derived, owner-computed derivatives, band tags carry the dequantisation rule |

Lidar-derived rasters were **not** used: the brief permits them for SNAP only if the human
supplies them, and the human approved the GeoDAWN/DEM mirror set only.
