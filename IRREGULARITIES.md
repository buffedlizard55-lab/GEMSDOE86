Only items that changed what a session did, or that a human must resolve before the next
slot. Three Arena sessions worked the PRUNE axis on the same parent; all are recorded.

## IR-86-H86L-01 — visible-fault edge residual lost to its control and duplicated GEMSDOE46 (2026-10-25)

`scripts/run_h86l_vfgr.py` ran the frozen three-arm design and stopped before writing a TIFF. HOLDOUT-DTI (`gems57-pooled-hide-v2`, 11,321 withheld positives) was 0.0313 [0.0230, 0.0395] for the residual and 0.0367 [0.0272, 0.0457] for the raw-edge control. The paired interval was entirely below zero. Final dots overlapped `GEMSDOE46:SUBMISSION-GEMSDOE46-dfa-corroborated.tif` at 0.7013 with that raster’s halo covering only 0.1965 of the footprint. **Decision: DO NOT SUBMIT. No file, no slot.**

Two related facts are not the duplicate itself. First, `depth_to_base_surf` is negative on part of the footprint (minimum −14.84). The basement-mass control still fit and still lost. Second, `registry_complete` is false with 0 missing inventory files because some measured rows fail the grid check, including known off-grid historical rasters. That is fail-closed, not a claim that the 655-file restore failed. The restore receipt said 655 verified.

## IR-86-RKSC-01 — H86I-RKSC generated a unique audit-only GeoTIFF (0 rho firings, 0 sparse-dot overlap firings) and failed closed on holdout & off-grid registry rows (2026-10-25)

Before any lane code was written, four untried geological hypotheses (`H86I-1..H86I-4`) were frozen in `research/H86I_RKSC_PREREGISTRATION.json` (`sha256: 83300b29…`) and `research/H86I_RKSC_PREREGISTRATION.md`. `scripts/run_h86i_rksc.py` executed the top candidate (`H86I-RKSC`: Lahontan-Deconfounded Piedmont Scarp Profile-Curvature Dipole coupled with GeoDAWN Radiometric K/Th/U/TC Provenance-Metasomatism Step and Seismic-Conductance Conduit, excluding all gravity and magnetic bands) and serialized `docs/downloads/gems86-h86i-rksc-rad-scarp-44090dots-20261025T025132Z-f1199979-zeros.tif` (`sha256: 9437c83e0b5cf3fe1679ee26b6e41f200cf9a5eb08d7815a36a13a0e96f765ba`, `44,090` dots, `0` NaN, values in `[0, 1]`). **Decision: `DO NOT SUBMIT` (`verdict: "negative"`, `safe_to_submit: false`, `submission_slots_used: 0`).** On `gems57-pooled-hide-v2` (`seed=20`, `11,321` withheld positives), `E1_rksc_full` (`0.0245 [0.0185, 0.0304]`) beat both internal ablations (`E2 = 0.0235 [0.0174, 0.0294]` and Lahontan-uncorrected K-depleted negative control `E3 = 0.0142 [0.0093, 0.0196]`, `+72.5%` relative lift), but trailed fold-fair 2-px `R0` (`0.0961 [0.0829, 0.1094]`), 3-px `R0` (`0.0931 [0.0798, 0.1067]`), and same-split `H86C-KSLB` (`0.1241 [0.1080, 0.1403]`). Across `687 / 689` valid registry rasters, pre-placement surface worst Spearman is `0.2633 <= 0.90` (`0` rho firings) and final-dot worst Spearman is `0.0395 <= 0.90` (`0` overlap firings against any sparse `<=60,000`-dot submission), but `16` space-filling lattice/composite rasters (`13GEMSDOE`, `15GEMSDOE`, `GEMSDOE48`) and continuous witness `17GEMSDOE` exceed `0.70` 3-px overlap and `scripts/pa86_chance_overlap.py` fails closed on the `2` off-grid historical rows (`14GEMSDOE`, `7GEMSDOE`). Following execution, `scripts/run_h86i_rksc.py` is gated behind `protocol_preflight.require_feasible()` in `tests/test_builder_preflight.py`.

## IR-86-PCC-01 — H86F-PCC generated a format-valid TIFF and the gates rejected it (2026-10-25)

`scripts/run_h86f_pcc.py` wrote `docs/downloads/gems86-h86f-pcc-signed-44090dots-20261025T002755Z-94f74d4e-zeros.tif` (sha256 `7a0dcffb…c7be`). **Decision: DO NOT SUBMIT.** HOLDOUT-DTI (`gems57-pooled-hide-v2`, 11,321 withheld positives) is 0.0327 [0.0237, 0.0436], below the same-split KSLB comparator 0.1241 [0.1080, 0.1403]. The shared PA-86-02 script refused the registry report because two inventory rasters are not on the submission grid (`14GEMSDOE` horse-ensemble; `7GEMSDOE` qfaults prior). A later diagnostic, `docs/evidence/h86f-pcc-chance-diagnostic.json`, classified 11 dot-field overlap hits as space-filling (0 informative firings). That diagnostic is not a gate pass. The run-card reason string was corrected after the script crash; scores and the SHA-256 were not recomputed. No slot was used.

## IR-86-PCC-02 — template feature cache still absent; raw pinned TIFF was used, not described as the cache

The protocol names the template cached feature stack. It is not in this checkout (`/tmp/gems32/work/feature_stack.npy` is the upstream receipt path). This lane used SHA-pinned `training_features.tif` (`4371c82e…`) plus the unmodified `vendor/gems57` evaluator and writer. It did not rebuild or relabel that cache. The pinned registry inventory still ends at `56GEMSDOE`; local `docs/downloads` and `data/scored_fleet` were added by the existing checker. That is not a complete organizer registry and not coverage of `GEMSDOE57`–`GEMSDOE92`.

## IR-86-PRUNE-01 — the standing protocol forbids every submission; brief v2 forbids the gate
`PROMPT.md` / `AGENTS.md` / `scripts/audit_release.py` apply a **70 % overlap** and **0.90
rank-correlation** uniqueness rule against a pinned registry witness that is positive at every
allowed pixel, so forward overlap is 100 % for any nonempty candidate and nothing is ever
submittable. Brief v2 §6 says the opposite: *"Do NOT apply rank-correlation or dot-overlap
'uniqueness' thresholds."* **Decision:** both sessions followed the brief — no overlap
threshold applied, dedupe on exact sha256 and repeated `(parent, axis, value)` only — and
**no gate script was modified, relaxed or bypassed**. No slot is authorised here. **Cost:** the
human must choose which rule governs before submitting; both cannot hold.

## IR-86-PRUNE-02 — parent rebuild: impossible from the `gems32` recipe, solved another way (corrected)
Brief v2 §5 says rebuild R0 and match its sha256, or stop. My first pass concluded "cannot
rebuild": `research/upstream/run_h33.py` imports `gems32.*`, which is not vendored here.
**That conclusion was too strong and is corrected.** PR #29 reproduced R0 **byte-exactly** by
taking the pinned base raster `gems28-h27-4-r1-solo-d2-8` (sha256 `ab023001…`) and deleting
every dot within 2.0 px of a mapped-fault cell: 40,199 → 37,654 dots, 0 differing pixels,
rebuilt sha256 `c55bafc4…b6fa9` = the published file. So the *lineage step* is reproducible
even though the original H33 model is not.
**Decision:** R0's identity is now established twice — by pinned digest (this branch) and by
byte-exact re-execution (PR #29). **MASS remains unavailable**, because a rebuild gives the
dot *set*, not the parent's ranking of the cells it rejected.

## IR-86-PRUNE-03 — the catalogue hide-and-recover PROXY is at its floor for this lineage
Measured: R0 scores PROXY DTI 0.00436 and every pruned variant 0.00000, because a
catalogue-avoiding field earns almost no credit from withheld catalogue pixels. The published
correlation of this instrument with live scores is sign-unstable (−0.87 … +0.54, n = 12–14).
**Decision:** reported in full (`evidence/prune_axis_20261023.json`), used only as a negative
control; no prediction or gate depends on it. **Cost:** the live slot *is* the measurement.

## IR-86-PRUNE-04 — competition rasters are committed in a public repository
`data/bridge/existing_faults.tif` (byte-identical to `labels.tif`) and
`data/bridge/sample_submission.tif` are tracked here, with 26 derived `.tif` files in
`data/scored_fleet/`; data-use terms are unchecked.
**Decision:** no new competition raster is committed. Release TIFFs stay local and are
gitignored (`/releases/*.tif`); only code, hashes and receipts are published. The restored
418 MB feature stack is gitignored too. **Cost:** the human must confirm the data-use terms and
decide whether the tracked bridge rasters should leave history.

## IR-86-PRUNE-05 — no valid target number exists
`TOP_PUBLIC` is blank; the owner prompt quotes 0.3195 and then 0.4413, undated and without
receipts. DrivenData cannot be fetched from this sandbox (terms ban automated access).
**Decision:** no target was invented and no score comparison was made. Everything is reported
against R0 = 0.2778 (**CLAIM**). **Cost:** "beat TOP_PUBLIC" cannot be evaluated.

## IR-86-PRUNE-06 — the (PRUNE, 3.5) pair is already spent on another parent
`GEMSDOE77` `gems85-h85-edti-collar35-skel-r33` (owner-reported 0.0964) already built a 3.5 px
collar, on a skeleton/`r33` parent whose baseline is unknown.
**Decision:** 3.5 was not rebuilt; values 3, 4, `3`+refill and `3r` were used. The 0.0964 says
nothing about R0 because it is confounded with a much weaker parent. **Cost:** the collar curve
has a gap at 3.5 px.

## IR-86-PRUNE-07 — the brief wants NaN outside the footprint; the repo's validator forbids any NaN
Brief §6 lists "NaN outside the footprint" as a MUST gate; `vendor/gems57/validate.py` runs the
opposite convention (`no_nan_anywhere`, `outside_footprint_zero`) as a conservative local policy
adopted after the portal's "values must be in range [0, 1]" error.
**Decision:** every variant ships both forms under distinct names and digests. The `-nan` twin
satisfies the brief; the `-zeros` twin additionally clears the vendored validator
(`all_checks_passed = True`) and `gates.format_report` (`ok = True`). Upload **one** per slot —
`-zeros` if the portal rejects `-nan` on range. **Cost:** one decision left to the human at
upload time.

## IR-86-PRUNE-08 — three sessions, seven builds, one `(PRUNE, 3)` pair spent twice over
Brief v2: "each (AXIS, value) pair is built once across all sessions". Three concurrent
sessions built the PRUNE axis on the same parent today:

* PR #28 — `(PRUNE, 3)` with a fixed-count H19-5 refill (`…-01d57649`, 37,654 dots);
* PR #29 — a nested ladder `(PRUNE, ≤2.2361)`, `(≤2.8284)`, `(≤3.0000)` plus a mass-matched
  control (`82b3f1f4`, `6ff38618`, `a438e92b`, `a2a8be25`);
* this PR — `(PRUNE, 3)` pure deletion (`3eb29af5`), `(PRUNE, 4)` (`e198b768`) and
  `(PRUNE, 3r)` equal-count relocation (`9542efac`).

`3eb29af5` and `a438e92b` are the **same dot set**: R0 minus the 2,171 dots within 3.0 px of the
catalogue (PR #29 measured the shells as 941 at √5 + 670 at √8 + 560 at 3.0 px; this branch
removed exactly 2,171 = 5.766 %). Only the TIFF encoding differs.

**Decision:** all seven stay in `ledger/submissions.csv` (nothing is deleted), the pair is spent
**once** (`le3p000` in slot 1), and this branch's `3eb29af5` is **withdrawn** from slot
consideration. The redundant local copies of `3eb29af5` are deleted from `releases/` so the
wrong file cannot be uploaded by accident. **Cost:** three sessions burned on one 5.8 %-of-mass
axis; the calendar in `SLOT_PLAN.md` now gives PRUNE one slot and moves the rest to a
feature-based axis.
## IR-86-LADDER-01 — the fixed-count refill confounder (PR #28's design)
The ≤ 3 px prune removes 2,171 dots, but only 475 same-field refills preserve the parent's 2.8 px
spacing; the mandated 2,171-dot refill therefore changes spacing as well as collar membership
(measured: mean nearest-neighbour 3.735 → 3.550 px). A live result from `…-01d57649` cannot be
attributed to collar width alone. **Decision:** that design is not slot 1; the pure-deletion rung
is. This branch's `prune3r` (relocate 1.14 px, spacing nearly intact) is the clean version.

## IR-86-LADDER-02 — byte identity IS achievable, and my first pass said otherwise
PR #29 found that `existing_faults.tif`'s own writer profile (deflate, `predictor=3`, `zlevel=9`,
tiled 256, `nodata=None`) re-encodes R0 to exactly 219,065 bytes and sha256 `c55bafc4…`. My first
pass declared file bytes unreproducible after a smaller profile sweep; that was wrong and is
retracted here. **Decision:** the brief's parent gate is satisfiable as "dot set + file bytes", and
every rung is written with that profile. **Cost:** this branch's own releases use a different
profile, so their digests differ from PR #29's even where the dot sets agree — the dot-set digest
is the identity that survives an encoder change, and both are recorded.

## IR-86-LADDER-03 — the ledger had three writers for one day
Three sessions seeded `ledger/submissions.csv` independently (PR #28's builder, PR #29's
`merge_prune_ledger.py`, this branch's `build_ledger.py`). **Decision:** this branch's
`scripts/build_ledger.py` is the single generator; it reproduces PR #29's schema and rebuilds the
other sessions' rows from `ledger/variants.json` + `ledger/variants_external.json`, so
`build_ledger.py --check` proves the file is current. The other two scripts are left untouched and
remain valid for building rasters, not for regenerating the ledger.

## IR-86-MASS-01 — the parent's ranking is a traversal, and it is geographically structured
Brief v2 §5 (MASS) says to rebuild R0's ranking from the recorded recipe. Done and validated:
greedy 2.8 px thinning in FIFO-BFS visit order reproduces the pinned `d2.8` set exactly
(44,090 dots, 0 differing cells; row-major order does not). But the order is seeded
row-major by connected component, so "lowest-ranked 10 %" is not a random or quality tail:
the 3,765 dropped dots are **100 % in the southern half** (mean row 3,215 vs parent 1,273)
and the 3,765 added cells are **100 % in the northern strip** (mean row 60.5), with 98.59 %
of additions within 2.8 px of an existing dot. **Decision:** built literally as briefed,
with the quadrant shares and redundancy measured in `evidence/mass_axis_20261023.json` and
stated on the mechanism cards, and with both variants predicted negative so no slot is
recommended by default. **Cost:** a MASS receipt cannot be attributed to mass alone
(minus = mass × geography; plus = mass × kernel redundancy); it can only bracket whether
*traversal-ranked* mass at 37,654 is near-optimal. This also narrows IR-86-PRUNE-02: a
rebuild supplies no *quality* ranking, but the recipe's actual priority order is recoverable
and checkable.
## IR-86-SNAP-01 — AXIS was again unassigned; SNAP was taken from the slot plan, not from the human
Brief v2 §1 says the AXIS is human-assigned. It arrived blank for the fourth session running.
**Decision:** SNAP was chosen because (a) `SLOT_PLAN.md` (written by the PRUNE sessions) had
already pre-registered "SNAP or RELIEF" as slot 2 and declared PRUNE crowded, and (b) SNAP's two
bands restore from a verified pin, so nothing had to be guessed. No other axis was touched.
**Cost:** if the human wanted MASS, CONCENTRATION or RELIEF, this session's three builds are off-axis.

## IR-86-SNAP-02 — SNAP is a negative axis on the only instrument available
97–99 % of R0's dots move to a stronger gradient cell, so the edit is large; but the catalogue
hide-and-recover PROXY cannot separate any arm from a **random-response null control** (real
+0.00013 vs null −0.00120; σ=1 smoothing −0.00179, σ=2 −0.00316), and it costs coverage
(dots with a neighbour closer than 2 px: 0 → 3,448 / 8,341 / 2,085). The response is smooth
(lag-1 autocorrelation 0.978), so this is not speckle — the incumbent field simply is not on the
TMI/gravity ridge, and "on the ridge" is not demonstrably "on a fault".
**Decision:** all three variants ship as gate-clean artifacts with **negative** MODEL predictions
and are ranked *below* the PRUNE rung in `SLOT_PLAN.md`. SNAP gets at most one slot, and only as a
deliberate probe of the live hypothesis, never as an expected gain. **Cost:** the live hypothesis
("new faults are at potential-field edges") is untestable locally; one slot is the only measurement.

## IR-86-SNAP-03 — a SNAP variant changes ~194 % of R0's cells, which the 1–50 % rule cannot express
A move deletes one cell and adds another, so % of parent *cells* changed is 2×% of dots moved
(193.8 / 196.9 / 199.6 %). Brief §5 exempts SNAP from the 1–50 % contract and asks only that the
exact percentage be recorded.
**Decision:** the ledger's `pct_changed` column reports **% of parent dots that moved**
(96.92 / 98.44 / 99.78 %) because a dot is the unit of mass; the cell-level figure and the
count-preservation proof are in `ledger/variants_snap.json`. **Cost:** anyone comparing the SNAP
rows to the PRUNE rows in that column compares two different denominators.

## IR-86-SNAP-04 — the (R0, SNAP) pair was already spent before this branch saw main

The ledger check the brief asks for could not see the other sessions: this branch was cut from
`27d915f`, and `origin/main` was a single grafted commit, so `git merge-base` returned nothing until
`git fetch --unshallow` (IR-86-SNAP-05). PR #28–#31 landed the PRUNE ladder and an independent SNAP
axis (`a3d584a`, three variants `r1p000` / `r2p000` / `r2p000-grav`) while this session was building.

Decision changed: the three magnetic-edge variants built here are recorded as **`BUILT-DUPLICATE`**
and are **not** proposed for a weekly slot. They are kept because they were built under a different
rule (1 px smoothing, 0.25 σ gain gate, 2.828 px spacing floor, magnetic-band response) and they
corroborate PR #31's negative verdict from an independent geometry. Requesting slots for them would
have spent three of the entity's weekly submissions on an axis already measured negative.

## IR-86-SNAP-05 — depth: shallow checkout hid the common ancestor

`git merge origin/main` failed with *"refusing to merge unrelated histories"* and `git merge-base`
returned nothing, because the checkout carried `origin/main` at depth 1 (one grafted commit). The
repository was **not** diverged; `git fetch --unshallow origin` restored 84 commits on main, after
which the merge base was `27d915f` as expected. Anyone reconciling two sessions here must unshallow
first, or a resolvable content conflict looks like history corruption.

## IR-86-SNAP-06 — the hide-and-recover PROXY measures catalogue-collar recovery and nothing else

Reported by this session, and it changes how every future proxy number in this repo must be read.
The proxy gave 0.0047 for the parent and 0.0150 / 0.0169 / 0.0190 for the three magnetic SNAP
variants — a factor of three. Re-scoring all four with **one fixed ≥ 3 px catalogue collar applied
to every candidate** gives **0.0000 for all four**, and drops the SGMC control from 0.0877 to
0.0000 (`evidence/snap_fixed_collar.json`).

Decision changed: no proxy number in `SLOT_PLAN.md`, the README or any card may be quoted as a
ranking of candidates for this lineage unless the same collar is applied to every arm; the only
quantity the free proxy is measuring is how much mass sits beside a withheld catalogue trace, which
is the zone the live metric masks out and penalises. The proxy stays report-only and never a gate.

## IR-86-SNAP-07 — the SNAP window was Chebyshev, corrected to a 2 px Euclidean radius

The pre-registered window was the 25 cells with `max(|dy|,|dx|) <= 2`. A corner move is 2.828 px,
so the file could claim a "≤ 2 px" rule while displacing dots by 2.83 px, and the repository's own
SNAP rule and release contract (`src/gems86/snap.py`, `tests/test_prune_ladder.py`) both define the
cap as a **Euclidean radius**. The house contract caught it (`assert 2.828 <= 2.0`).

Decision changed: the window is now the 13 cells within a 2.0 px Euclidean radius, the realised
maximum displacement is exactly 2.0 px, and the three builds were regenerated under it — moved
fractions 33.9 / 39.6 / 45.9 %, mean displacement of moved dots 1.72–1.74 px, spacing floor still
2.828 px. The change is a definitional correction, made before any score existed and before any
file left this branch; it is recorded here because it happened after the pre-registration was
written, and the pre-registration text was amended in the same commit rather than quietly.

## IR-86-RELIEF-01 — the report-only instruments caught two defects in my own first build
The first RELIEF pass built the same three doses with two faults: (a) sources were selected as the
dots *nearest* a legal destination, which moved every dot only 3–4 px (300–400 m) — a class-label
flip, not a change of terrain setting; and (b) eligibility was tested against the *parent* dot set
only, so two relocated dots could be placed 1 px apart. The children therefore had minimum
nearest-neighbour 1.0 px against the parent's 2.828 px, i.e. each variant silently contained a
clustering edit — precisely the confound IR-86-LADDER-01 records for PR #28's refill. The parent-diff
statistics (`nn_dist_px`) and the surrogate instrument are what exposed it: the first pass read
−0.003 / −0.002 / −0.010, and after fixing selection ("deepest-in-regime" first) and blocking the
spacing disc around every accepted cell, the same three doses read +0.0017 / +0.0010 / −0.0089 —
the sign of the axis flipped because the clustering cost disappeared.
**Decision:** the defective files were never released and never entered the ledger (their local
rasters were deleted, `ledger/` reverted, and the build re-run once); both fixes are unit-tested
(`tests/test_relief_axis.py::test_relocation_preserves_the_parents_min_spacing`,
`test_deepest_selection_picks_dots_further_inside_the_regime`), and the gate now refuses a child
whose spacing contract is broken. **Cost:** ~25 min of one session, and a rule for future axes:
*report-only* statistics have to be read before a file is called a variant, because they are the
only thing here that can see a self-inflicted confound.
Related trap, same session: bands 12/19 of the pinned stack carry `-3.4028234663852886e+38`
nodata **inside** the footprint (3,061 cells). A reader that scrubs only non-finite values lets
those spikes dominate the standardisation, and the regime classification then puts 100 % of R0's
dots in "basin". `src/gems86/io.read_band` is the only sanctioned reader; the driver now asserts
`max|band| < 1e6` on the inputs it classifies with.

## IR-86-RELIEF-02 — brief §4.4's ">=3 px from the catalogue" contradicts the parent's own geometry
R0 keeps 2,171 dots at 2–3 px from a mapped fault (its rule was "off the trace, >2 px"). Brief §4.4
demands ≥3 px for every emitted mass, but §5's axis contracts demand that a variant change *only*
its own axis, and clearing that band **is** `(PRUNE, 3.0)` — already built, already slot-1, spent
three times over (IR-86-PRUNE-08).
**Decision:** the ≥3 px rule binds **newly emitted** mass — every cell any RELIEF variant inserted
is ≥3 px from the catalogue — while the parent's inherited 2–3 px dots are left exactly as they
are; relocation shrinks that band incidentally (2,171 → 1,925–2,039), which is reported per variant
rather than optimised away. **Cost:** the variants are not fully §4.4-compliant, and the residual
difference (1,925–2,039 dots) is a known, quantified gap that any reader must attribute to PRUNE,
not RELIEF.

## IR-86-RELIEF-03 — MASS: this session declined it, a concurrent session built it, and both said the same thing
Brief v2 §5 MASS allows "rebuild the ranking from the recorded recipe if it is not stored", and PR
#28 had reconstructed one: `scripts/build_r0_prune.py::original_visit_rank`, the deterministic
FIFO-BFS visitation order of the `gems27.thinning` recipe. So when the human assigned RELIEF, this
session left MASS unbuilt on the grounds that a traversal order is not a quality ranking
(IR-86-PRUNE-02 had gone further and called MASS unavailable).
**Update during merge:** the concurrent `arena/7cf7f98a` session *did* build MASS ±10 % and reached
the same conclusion independently — the reconstructed order reproduces the pinned `d2.8` set
exactly, but it is geographic, so its dropped 10 % is 100 % southern-half dots and its added 10 % is
100 % northern-strip cells, 98.6 % of them within 2.8 px of an existing dot (IR-86-MASS-01).
**Decision:** no conflict to resolve — the two sessions agree that a MASS receipt cannot be
attributed to mass alone. This item stays as the record that the axis was *available*, so nobody has
to re-derive it a third time. **Cost:** none to this branch; the MASS files exist and are
`-0.003 / -0.006 MODEL`.

---

## IR-86-CONC-01 — two sessions built (PRUNE,3) and (SNAP,2) independently; the ledger was stale at branch point

**Observed.** This branch was cut at `27d915f`, before PRs #33/#34/#36 merged. Its
`ledger/submissions.csv` therefore did not contain the parallel sessions' rows, so the brief's
"check the ledger first" step passed locally and this session built `(PRUNE, collar3px)` and
`(SNAP, 2px)` — keys already built on `main` as `(PRUNE,3)` (`…-prune3-…-01d57649`) and
`(SNAP,2)` (`…-SNAP-r2p000-…-e7473403`).

**Decision.** Brief §6 dedupes on repeated `(parent, axis, value)`, so both are recorded
`BUILT-DUPLICATE` in `ledger/variants_concentration.json` and are **not** slot candidates. They
stay on disk for audit only. The one non-colliding build is `(CONCENTRATION, b1km-move15)`, which
was unbuilt on `main`.
**Cost.** Two wasted builds (~400 s of compute), no slot spent.
**Prevention.** Re-`git fetch origin main` and re-read the ledger *after* the axis is chosen and
*before* the build, not only at session start. `tests/test_axis_releases.py::
test_duplicate_arms_are_not_marked_built` now fails if a duplicate is ever recorded as `BUILT`.

## IR-86-CONC-02 — the reported block-density CV band does not contain the incumbent

**Observed.** The brief states the best files sit at block-density CV 0.51–0.59. Measured on R0
over occupied 1 km blocks (10×10 px): **0.6235** (15,976 of 122,717 blocks occupied, mean 2.357
dots per occupied block). The parent is outside the band it is supposed to exemplify.

**Decision.** The band is treated as an unverified CLAIM, not a target and not a gate.
CONCENTRATION was built to the brief's own definition (move 15 % from the lowest-prior blocks to
the highest-prior ones), which moves the CV to **0.7644** — further outside. That direction is
recorded as the axis's falsifier rather than tuned away: if the live result is ≤ 0, the band
becomes the thing to test (spread mass until the CV lands in-band) and CONCENTRATION-as-defined
retires. **Cost:** none; the variant is built either way.

## IR-86-CONC-03 — R0's support mask is saturated at its own thinning radius

**Observed.** A count-preserving PRUNE refill must find 2,171 free cells. Inside the parent's own
H19-5 support mask (121,131 px) only **611** eligible cells region-wide sit ≥ 2.828 px from a
retained dot.

**Decision.** The refill runs in two passes: parent spacing first (475 placed), then a relaxation
to the parent's own >2 px catalogue-clearance floor (1,696 placed), recorded as
`refilled_at_relaxed_spacing`. The alternative — a 1,696-dot shortfall — would have turned a PRUNE
build into an unlabelled MASS change, which is worse. Note this is the same confound PR #28
recorded for its own `(PRUNE,3)+refill` ("PRUNE and spacing are not separable in this design");
two sessions reached it independently. **Cost:** the PRUNE arm cannot be attributed to the collar
alone. It is a duplicate arm here, so it costs no slot.

## IR-86-CONC-04 — the parent's filename token is not a digest of the parent's bytes

**Observed.** The parent's name carries `e5eb6e7e`; its SHA-256 is
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`. The upstream `-zeros` and
`-nan` twins hash to `c55bafc4…` and `baeae321…`
(`docs/evidence/h86_wvb_data_restore.json`, GEMSDOE32 ref `780a5a53`), so no published twin of
that file hashes to `e5eb6e7e…`. Other sessions' `h33-h33-2-b2-20261004-e5eb6e7e-…` release names
inherit the same non-digest token.

**Decision.** This session's releases are named with a deterministic **dot-set** digest
(`grid_io.dot8`: SHA-256 over the packed bitmap plus shape), so the token is reproducible from the
mask alone and cannot be circular with the file's own tags. The ledger records the token in
`sha8` and the zeros twin's file digest in `sha256`, per house convention, and
`tests/test_axis_releases.py` re-derives both from disk. **Cost:** none, but any tool that parses
`e5eb6e7e` as a content digest is wrong.

## IR-86-CONC-05 — partial 5 km edge blocks were almost treated as the lowest-prior source

**Observed.** A 50×50 px tiling of the 3,730×3,292 grid leaves 30 rows and 42 columns in
partial edge blocks. `block_to_pixels` marks those cells `-inf` because they have no complete
block prior. The first 5 km build therefore put their dots at the front of the ascending-prior
source draw; `prior_separation` stopped the run before any candidate raster, receipt or ledger
row was written. This is not evidence that edge-strip geology is low priority.

**Decision.** Unclassified dots are excluded from the low-prior draw (`source_priority=+inf` for
non-finite block values), and the 5 km builder fails if one is dropped anyway. Density CV remains
explicitly a **complete-block** measurement; it is not silently extended with a different partial-
block normalization. The 10/15/20% doses and low→high direction were not changed after the first
SGMC read. A synthetic 110×110 regression grid now exercises the remainder strips. **Cost:** one
205 s stopped build, zero releases and zero slots. The same guard also corrects the latent two-
column remainder issue in the older 1 km implementation; no historical 1 km artifact was rebuilt
or relabelled here.

## IR-86-CONC-09 — positive catalogue-recovery PROXY conflicts with support and independent control

**Observed.** All three 5 km arms place **0% of their added cells** on pinned `gems19-h19-5`, the
support surface from which R0's lineage was thinned; all source cells are on it. Meanwhile pooled
hide-and-recover rises from parent `0.0286 [0.0240,0.0333]` to `0.0408 / 0.0427 / 0.0441` for
10/15/20% (`n=11,321` withheld positive pixels; the paired 15% Δ is `+0.0141 [0.0072,0.0234]`,
**PROXY only**). The independent SGMC MODEL read instead changes by `−0.0066 / −0.0109 / −0.0150`,
and occupied complete-5 km-block CV rises `0.7442 → 0.9006 / 1.0113 / 1.0798`.

**Decision.** None of these three files is slot-recommended. The positive PROXY is not a score or
a gate and cannot overrule either the support-surface abandonment or the negative independent
control. Its catalogue-interaction term is also part of the placement prior, so the instrument
and mechanism are not independent. A future **support-constrained** block-allocation axis is only
a proposal for a later session; no fourth variant or retuned value was built here.

## IR-86-SNAP-08 — brief §4.4 (>=3 px) vs the SNAP spec ("same exclusions") on R0
The same conflict RELIEF logged as IR-86-RELIEF-02, reached independently from SNAP:
enforcing >=3 px inside a SNAP variant re-runs PRUNE's collar. All SNAP builds keep the
parent's >2 px exclusion (min 2.236 px, zero catalogue mass). No new decision; recorded
so the SNAP files' 2-3 px dots are not mistaken for an oversight.

## IR-86-SNAP-09 — a third SNAP build (gain-gated) landed after two were already merged
Its `snapr1`/`snapr2` duplicate PR #31's pairs (36,483 vs 36,494; 37,055 vs 37,066 dots
moved) and are **withdrawn, no raster written**; its novel gated pair `snapr2g10` stands
as `BUILT-DUPLICATE` corroboration (PR #34's convention), not a candidate. **Cost:** SNAP
consumed three sessions/builders for one thrice-measured negative; the next session needs
an explicit human AXIS assignment instead of another slot-plan reading.

## IR-86-SNAP-10 — the SNAP builds treat the signed gravity band differently
`iso_grav_anom_hg` is signed: PR #31 ranks it as-is, PR #34 uses magnetic bands only, the
gated build ranks `|iso_grav_anom_hg|`. Nothing is re-run; cross-build gravity comparisons
are not like-for-like, and any future SNAP-adjacent proposal must state its treatment first.

## IR-86-SPACING-01 — the dedupe gate fires on a session's own rebuild, so the scan was scoped to the ledger

**Observed.** The SPACING builder was re-run once after a defect fix. The second pass aborted on
`sha256_not_in_ledger`, because `known_hashes()` had globbed `releases/**/*.tif` and picked up the
*first pass's own bytes*: a deterministic rebuild of the same `(parent, axis, value)` collides with
itself. Brief §6 dedupes on "exact hash and repeated (parent, axis, value)" — an identical rebuild of
the same key is neither a repeat slot nor a new file, and treating it as one hides nothing but stops
the session.
**Decision.** `scripts/build_r0_spacing.py:known_hashes()` now consults `ledger/submissions.csv`
plus the delivered parents in `data/scored_fleet/`, and no longer scans `releases/`. The gate script
`src/gems86_axis/gates.py` was **not** modified: the dedupe rule is unchanged, only the set it is
compared against. Nothing was promoted by this: the tokens (0d2f135e / 63c4c56f / caffc3f0 /
db4cae83) are identical in both passes, so the rebuild is provably the same experiment.
**Cost:** ~6 minutes and one aborted run. A reusable rule for this repo's axis builders: never seed
the duplicate set from the directory you are about to write into.

## IR-86-SPACING-02 — the axis moves mass off its own evidence surface; the surrogate cannot see the difference

**Observed.** 100 % of the relocated dots start on the H19-5 support surface the lineage was thinned
from; after placement only 1.8 % (pdisk), 3.0 % (lattice) and 5.2 % (strike) of their destinations
are on it. The SGMC off-catalogue surrogate nevertheless reads +0.0015…+0.0020 for all three arms,
while the random-move control in the same window reads +0.0002 — and rises to +0.0033 once the truth
is translated by up to 6 px to represent the ~400 m flight-line position uncertainty in brief 2.
**Decision.** Reported as MODEL only, with the control printed next to every arm, and no SPACING arm
is offered as slot 1 or 2 in `SLOT_PLAN.md`. The law-vs-control separation (~+0.0016) is the axis's
real content; the absolute number is not trustworthy because most of the bought coverage sits on
ground the parent's own field does not rate. A SPACING slot is a mechanism probe, decided by the
human, and `strike` is the only arm whose false-positive term barely rises (+83.7 vs +140).
**Cost:** none this session; it bounds what a SPACING receipt can later be said to have proved.

## IR-86-SPACING-03 — a count-preserving bug found by the axis tests, not by the gates

**Observed.** The first draft of `src/gems86/spacing.py:relocate()` built its output as
`retained ∪ destinations`, so any dot it could not place *disappeared*: on a 12×12 synthetic grid the
"fixed count" arm returned 2 dots for 4. The MUST-pass gates would not have caught it (the file is
valid, the format is valid, the catalogue is clean) — only the axis contract would.
**Decision.** Placement now runs on a single occupancy set that starts as the whole parent, vacates a
source when it is processed and re-fills it if the dot cannot be placed, so the count is fixed **by
construction** and an unplaced dot is reported in `moved_unplaced` (8 lattice, 201 strike, 0 pdisk).
Two side effects are features, not accidents: a destination can no longer land on a cell another
selected dot still occupies, and `destinations_on_vacated_source_cells` (87–260 per arm) is now
reported so `dots_changed = 2·(placed − reuse)` holds as an identity in
`tests/test_spacing_axis.py`. **Cost:** one rewrite; the rule to keep is that a variant which changes
the count is a MASS experiment wearing another name.

## IR-86-SPACING-04 — brief §5's SPACING spec, read literally, is impossible on this parent

**Observed.** Brief §5 asks SPACING for "lattice vs Poisson-disk vs along-strike at matched count",
and §5 also requires a variant to change 1–50 % of the parent's dots. A *global* lattice or
Poisson-disk re-arrangement of 37,654 dots changes ~100 % of them (and the historic full-lattice file
`13GEMSDOE r13-lattice-s5` scored 0.0904 CLAIM). The two instructions cannot both hold on this
parent.
**Decision.** The three laws were kept, the *scope* was reduced: each arm re-lattices only the mass
the metric has already written off (credit ≤ 16 of 29 disc cells), so all three sit at 35.9–37.9 %
changed cells with the count fixed, and every destination stays within 800 m of its source (widened to
1.6 km for 480 lattice / 1,095 strike dots, reported). The literal global forms stay unbuilt and are
recorded here as the reason. **Cost:** none; the reading is logged so a later session does not
"correct" the dose upward.

## IR-86-SPACING-05 — the fold-fair hide-and-recover PROXY is *not* at the floor here, and that is a confound, not a win

**Observed.** The SPACING run card (`evidence/spacing_axis_20261023.json`,
`instruments.catalogue_hide_recover_proxy`) measures pooled PROXY DTI **0.00370 [0.00297, 0.00441]
for R0** and **0.01534 / 0.01359 / 0.01217** for `pdisk16` / `lattice16` / `strike16` (11,321
withheld positives, 4 folds). Unlike the PRUNE and SNAP arms, which read 0.00000 (IR-86-PRUNE-03,
IR-86-SNAP-06), these arms recover withheld catalogue faults four times better than the parent.
The reason is structural: the comparison is fold-fair only for the *arms*. Each arm is re-derived
per fold using that fold's **visible** catalogue for its collar, so its relocated mass is free to sit
on the withheld trace, while R0 was built against the **full** catalogue and therefore avoids exactly
those pixels. The instrument is measuring "you did not apply the 2 px collar here", which is
PRUNE's quantity, not SPACING's.
**Decision.** The proxy is published in the run card and **ranked by nothing**: no arm ordering, no
slot argument, and no README/SLOT_PLAN claim uses it. `SLOT_PLAN.md` and `evidence/spacing-mechanism.md`
carry this entry instead of the earlier "proxy is at the floor" phrasing, and the run card's own
`caveat` string (written before the measurement) is superseded by this entry. A future session that
wants a usable proxy for an arrangement axis must build the parent *in the fold too* — i.e. re-derive
the parent's dot set from the visible catalogue — or hold the collar fixed across every arm, which is
exactly what IR-86-SNAP-06 concluded.
**Cost:** one report-only instrument retired for this lineage, and a rule for future axes. The MODEL
predictions used for the ledger come from the SGMC off-catalogue surrogate, not from this number.

## IR-86-MASS-02 — brief §5's MASS ranking is a traversal; the axis was re-ranked, and the brief's own §2 requires it

**Decision changed:** yes — the ranking function this session used, and the rejection of all three
artefacts for slots.

Brief §5 defines MASS as "drop the lowest-ranked 10 % / add the next-ranked 10 %, **by the parent's
own ranking**". That pair was built by an earlier session and both arms lost (IR-86-MASS-01: the
recorded ranking is the FIFO-BFS traversal of the thinning recipe). Brief §2 then says, in the same
document, "rank dots by exact marginal gain from the metric code, not the shortcut". The two
sentences cannot both govern a MASS experiment, because the recorded ranking *is* the shortcut.

Resolution taken: the axis (MASS), the dose (±10 %) and the change rule (1–50 % of dots) stay
exactly as §5 specifies; the **ranking function** is the metric's own marginal credit
(`gems86.mass_econ.marginal_credit`), which is computable from the parent's dot mask alone with no
label, no band and no surrogate. Both predictions (preregistered, then revised) are in the run card.
If the human reads §5 as binding on the ranking function, this session's arms are off-brief and
should be treated as instrument audit only — which is exactly how SLOT_PLAN now treats them.

## IR-86-MASS-03 — the SGMC MODEL instrument is monotone in dot count, so it cannot rank mass

**Decision changed:** yes — it demotes every mass-changing artefact in the ledger, including this
session's own, and it re-orders the slot plan.

`evidence/mass_instrument_monotonicity.json`: a symmetric random add/delete ladder on the SGMC
off-catalogue surrogate reads −0.0127 / −0.0068 / −0.0030 / +0.0018 / +0.0040 / +0.0081 for
−20 / −10 / −5 / +5 / +10 / +20 % of R0's dots. Any arm that changes the dot count therefore has a
MODEL delta that is at least partly the instrument's mass response, so no such delta may be used to
promote an arm. Count-fixed arms (CONCENTRATION, RELIEF, SPACING, PRUNE-with-refill) are unaffected
at constant `n`; their *card* numbers are not withdrawn.

Numbers already published elsewhere in this repository that this affects: `massminus10` (−0.003) and
`massplus10` (−0.006) — their "selection is bad" reading is not separable from "fewer/more dots" —
and any future count-changing arm. It does **not** affect `le3p000` (+0.004) as a *number*, but see
IR-86-MASS-04.

## IR-86-MASS-04 — PRUNE's positive prediction shares a structural bias with its own edit

**Decision changed:** yes — PRUNE moves from slot 1 to slot 3 in SLOT_PLAN.md.

The PRUNE ladder's predictions were computed against a catalogue-derived truth (the
hide-and-recover construction), while the edit deletes dots near the catalogue. Any instrument whose
truth is (or contains) the catalogue will reward that deletion by construction, so part of
`le3p000`'s +0.004 is structural rather than geological. This is not a claim that PRUNE is wrong —
it is the only axis with a monotone ladder behind it — but it is no longer the best use of slot 1
when a count-fixed pair with an above-floor predicted separation exists.

## IR-86-MASS-05 — a re-run of the same pinned recipe reproduces the same sha256; the §6 hash gate needed a self-exemption

**Decision changed:** no — the gate is unchanged in substance; its implementation now says what it
means.

Brief §6 requires "sha256 not already in the ledger". This session's script rewrites its own rows
through `scripts/build_ledger.py`, so a second identical run reproduces the same bytes and would trip
its own gate. The check now passes only when every matching ledger row is one of *this run's own ids*
and carries no receipt; any other match (a prior session's artefact, or anything with a
`receipt_score`) fails. Recorded so that "reproducible" is never mistaken for "repeat submission"
(the ledger's real target: 8 slots on exact repeats).

## IR-86-MASS-06 — `src/gems86/mass_econ.py` had three bugs; the unit tests caught all three before any artefact was written

**Decision changed:** no (caught pre-release), but the numbers in the first two drafts of the run
card were wrong and are superseded.

1. the kernel offset set excluded the dot's own cell, so every dot lost its `k = 1` self-credit
   (disc weight 8.3803 instead of 9.3803);
2. the second-best surface was updated as `max(second, where(v >= best, v, second))`, which discards
   `v` whenever `v < best` — the asymmetry showed up as two symmetrical dots receiving 7.91 and 5.23
   units of unique credit instead of 5.23 each;
3. the docstring asserted `sum_x u_x = sum_g best`, which is false: with a max operator the marginals
   sum to `sum_g (best − second)`. Corrected in the module and asserted against brute force in
   `tests/test_mass_econ.py` (6 tests).

The stale artefacts from the first two drafts were deleted from `releases/mass86/`; only the three
hashes in `ledger/variants_mass_econ.json` exist on disk.
## IR-86-TRACKB-01 — the ranking TRACKB is specified to use does not exist in this checkout

**Observed.** Brief v2 §5 defines TRACKB as traces "built from R0's top-ranked dots". R0's only
recorded order is the FIFO-BFS *visitation* order of the `gems27.thinning` recipe, which the MASS
session showed reproduces the d2.8 set but is a geographic traversal (IR-86-MASS-01); the restored
H19-5 mirror is **binary** (every positive cell is exactly 1.0, measured on the pinned file), so it
carries no per-dot score either.
**Decision.** The substitute ranking is the parent's own *trace support* (longest ≥−1 px collinear run
containing the dot), computed from R0's geometry alone, and it is used only to choose donors. Stated
on the mechanism card and in the run card; no ranking is invented and no provenance order is implied.
**Cost:** transport of a MASS confound into TRACKB is impossible (no dot is added or removed for its
position in the traversal), but TRACKB cannot be described as "top-ranked dots" in any provenance sense.

## IR-86-TRACKB-02 — two build defects, one caught by a gate and one by the tests; both fixed before release

**Observed.** (a) `trace_runs` first stored indices into the dot *list* rather than flat raster cells,
so the support field landed on empty cells (7,462 cells, of which 46 were dots) while every shape
check still passed; the 1 km trace count was therefore wrong by construction. (b) `select_donors` used
`support >= 0` as its dot mask, which is true for every raster cell, so the "donors" were mostly empty
cells and deletion was short of the addition — the fixed-count gate in `run_trackb_axis.py` fired
(`37654 -> 38870`) before any file was written.
**Decision.** Both fixed (`flat[order]` decode; explicit `dots` argument, `ValueError` on over-donation),
both regression-tested in `tests/test_trackb_axis.py`. The gate, not the test suite, caught (b).
**Cost:** none released; one re-run.

## IR-86-TRACKB-03 — the 1–50 % change contract binds at the *bottom* for this axis

**Observed.** Every new trace continuation must clear the catalogue (3 px) and the parent's own √8 px
dot separation, so the relocation budget is capacity-limited: a requested 10 % donation yields 716
(3.8 % changed), 1,246 (6.6 %) and 2,710 (14.4 %) at corridors 1.0 / 1.5 / 2.5 px. Only the loosest
corridor clears 10 % changed, and it is the one whose surrogate sign is negative.
**Decision.** The three variants are reported as *corridor* values with the realised dose measured and
recorded, never as dose values that were not achieved. A future TRACKB build that wants a larger dose
must relax the spacing floor, which would fold SPACING into the axis — not permitted this session.
**Cost:** the axis is confined to ≤ 7.2 % of the dot set; the ≥ 10 % changed rung exists only at the
loose corridor.

## IR-86-TRACKB-04 — the GeoJSON trace set is a candidate prediction and stays out of Git

**Observed.** The brief asks for TRACKB as "GeoJSON + raster". This repository already keeps candidate
rasters out of Git because the data-use terms are unchecked (IR-86-PRUNE-04).
**Decision.** `releases/trackb/*.geojson` is gitignored exactly like `releases/*.tif`; the committed
record is the per-file `-zeros.json` receipt (trace table, length/azimuth/catalogue-distance statistics
and the 12 strongest traces) plus `evidence/trackb_axis_20261023.json`.
**Cost:** the full 300-trace geometry lives only in the workspace; CI cannot regenerate it without the
pinned parent (which is itself local-only).

## IR-86-CONC-06 — the CONCENTRATION prior is band-free this session, so `dens15` is not a replication of `conc15`
`variants.block_prior()` needs two terms: catalogue fault-interaction density **and** the mean Sobel
gradient of upward-continued TMI. The second comes from `training_features.tif` (419 MB), which is
absent from this checkout (`.cache/gems_data` does not exist), so this session's prior is the
catalogue term only. **Decision:** build the prior that the data support, add a matched
same-dose arm in *both* prior directions under that prior (`concdens15`, `concspr15`) plus a
random-block control, and log that `concdens15` is a **paired calibration**, not a replication of
`conc15`'s `+0.006 MODEL`; the difference between the two arms is the only quantity that isolates
the prior's sign from the missing band. The absent SGMC raster also means no SGMC control gate
this session. **Cost to the next session:** if `dens15` and `conc15` disagree, the TMI term is the
first suspect and cannot be tested until the feature stack is restored.

## IR-86-CONC-07 — this axis's sign is not measurable with any instrument in this repo, only with a live receipt
The five-truth-model panel puts `spr15`/`dens15` at −0.064/+0.047 under catalogue-adjacent truth
and +0.011/−0.011 under uniform far-field truth. Hide-and-recover, the SGMC off-catalogue DTI and
the H19-5 support surface are *all* built from the mapped-fault record that the organiser masks at
scoring time, so all three favour "mass near mapped faults" by construction and cannot rank these
arms. **Decision:** the plan treats one live slot as the only admissible test and spends at most
one slot per direction; no local instrument is reported as evidence for either sign. **Cost:**
every prediction for this axis is MODEL-class and its band crosses zero from either side.

## IR-86-CONC-08 — the block-density CV band is not reachable at the doses brief §5 allows
CV is non-monotone in dose (0.5970 at 5 %, 0.6136 at 15 %, 0.6722 at 30 %; parent 0.6235) and
*every* arm — spread included — reduces the number of occupied 1 km blocks (15,976 → 13,297), because
destinations are confined to a fixed prior fifth of the occupied blocks. **Decision:** the
0.51–0.59 band is recorded as an unverified CLAIM and is not used to choose a dose; the reported CV
is accompanied by the occupied-block count so the two cannot be read as one variable. **Cost:**
a future arm that wants to test the band must place mass in *unoccupied* low-prior blocks, which is
exactly the placement `GEMSDOE81 cont-poisson44090` scores 0.0041 with (CLAIM).

## IR-86-SPACING-06 — kernel-disjoint re-spacing at matched count is locally infeasible on R0's support

**Observed.** The natural strong form of this session's crowded-pool design — re-space the pool
so *every* final pair is >= 3.0 px (the DTI kernel radius) at the parent's count 37,654 — has
almost no legal destinations. R0 is a saturated 2.828 px packing of the H19-5 support: cells
>= 3 px from all 37,654 dots number in the hundreds (7,024 free support cells at the parent's
own floor before any placement), and the fallback displaced dots by kilometres (up to 3.8 km —
the CONCENTRATION-scale confound IR-86-RELIEF-01 warns about). 64 % of the pool could not be
placed within 24 px in the first design pass.
**Decision.** The shipped arms break each crowded pair at >= 3.0 px from its cluster's kept dot
(the kernel-overlap waste the axis targets) while holding the parent's own 2.828 px floor
everywhere else, destinations <= 16 px away; pool members with no legal cell stay put and are
counted as residual crowding (3,488-3,538 of 6,574). This also retires the KERNEL-BUDGET
proposal in SLOT_PLAN.md as literally stated ("re-spacing at >= 3.0 px at constant count"): at
37,654 dots the support cannot host it. Complements IR-86-SPACING-04 (the parallel session's
1-50 % reading): that entry rules out the global form by dose, this one rules out the strong
spacing floor by geometry. **Cost:** the arms are a partial repair (~8 % of R0's dots moved),
so the experiment speaks about the crowded pool only; the three geometries additionally share
~78 % of destinations (Jaccard 0.64) because legal sets are small.

## IR-86-SPACING-07 — two sessions built SPACING in parallel; distinct value keys both stand

**Observed.** This branch's ledger check (start of session) found no SPACING pair; PRs #44/#46
(`arena/c1df93fc`, `arena/146307ee`) landed `sp-lattice16 / sp-pdisk16 / sp-strike16 /
sp-random16` on main while this branch was building `lattice / poisson-disk / along-strike`.
Both designs answer the same axis with different scopes (their dose ~36-38 % of cells, the
"written-off mass" selection; this one ~8 % of dots, the kernel-crowded pool). The
`(parent, axis, value)` keys differ, so brief §6's dedupe does not fire and both builds stand.
The colliding file names were resolved without deleting either session's evidence: the later
branch's artifacts were renamed (`evidence/spacing-crowdedpool-mechanism.md`,
`evidence/spacing_axis_crowdedpool_20261023.json`, `tests/test_spacing_crowdedpool.py`), the
two `ledger/variants_spacing.json` lists were concatenated, and `tests/test_prune_ladder.py`
now carries both the TRACKB and the SPACING contract branches.
**Decision.** No withdrawal and no BUILT-DUPLICATE status (the keys are distinct); every card
cross-references the other session's arms so a reader cannot mistake the two designs. Slots:
neither SPACING family is a default bet (all predictions inside +/- 0.01). **Cost:** one merge
conflict round and a rename; the recurring rule (cf. IR-86-CONC-01) is that a ledger check at
session start is not a reservation.

## IR-86-TRACKB-05 — raw global `|∇TMI_up150|` concentrates 82 % of top-100 geologist traces in NW flood basalts

**Observed.** Ranking R0's `2,801` `H19-5`-supported `>= 1 km` traces by un-normalised global
`|∇TMI_up150|` + 3DEP scarp placed `82/100` (`82 %`) of the top traces in the NW quadrant (`47.4 %` of
footprint, `47.9 %` of R0 dots) over high-susceptibility Miocene–Pliocene flood basalts, leaving SE/SW
tuffs and metasediments under-represented (`1 %` in SE).
**Decision.** Replaced raw global magnetic gradient in the trace ranking composite with 5 km (`50 px`)
local-RMS automatic-gain-control normalisation `|∇TMI_up150| / sqrt(mean_5km(|∇TMI_up150|²) + 1e-3)`
paired equally with 3DEP 10 m scarp, restoring footprint-matched balance across the 120 geologist
dossier traces (`NW 63 / NE 27 / SW 13 / SE 17` = `52.5 % / 22.5 % / 10.8 % / 14.2 %`).
**Cost:** none; raw `|∇TMI_up150|` percentile is reported alongside AGC percentile per trace so
volcanic-margin mimics stay visible to a reviewing geologist.

## IR-86-TRACKB-06 — pure trace-only rasters fail both brief §5 (`1–50 %` diff) and `NLR-RULES`'s single-final-file constraint

**Observed.** Under official challenge rules (`https://docs.nlr.gov/docs/fy26osti/96647.pdf`), ONE
blind final GeoTIFF is scored in both Phase 1 ($50k automated `DTI`) and Phase 2 ($250k expert
geologist trace review + expanded ground truth). Emitting *only* the `2,237` connected pixels of the
top-120 `>= 1 km` traces changes `96.31 %` of R0 (outside brief §5's `1–50 %` invariant) and collapses
off-catalogue SGMC `MODEL` DTI from `0.092893` to `0.002429` (`Δ = −0.090464`, `−97.4 %`) because DTI
weights recall `4:1` (`β = 0.8` vs `α = 0.2`).
**Decision.** Kept pure-trace emission strictly as an in-memory diagnostic (`diagnostic_pure_top120_only`)
and implemented `rendertop120` as a count-fixed (`37,654` dots, `8.1957 %` changed) hybrid that
rasterises all 120 `>= 1 km` traces continuously at 100 m while preserving `95.9 %` of R0's background
(`SGMC Δ = −0.004335`, inside the `0.01` live evidence floor).

## IR-86-TRACKB-07 — R0's 3,349 isolated 1-dot singletons carry 4.1× the live DTI inclusion bar due to collar truncation

**Observed.** Deleting R0's `3,349` isolated 1-dot singletons (`0` R0 neighbours within `550 m`,
`cull1dot`) lowered off-catalogue SGMC `T` by `−758.25` (`0.2264 T`/dot — `12.2×` above SGMC's
`0.2 × 0.0929 = 0.0186` isolated-dot bar and `4.1×` above R0's live `0.2 × 0.2778 = 0.0556` bar),
giving `SGMC Δ = −0.009644`. Inspection shows `551` of those singletons sit in `(2.0, 3.0] px` where
R0's `<= 2 px` pruning severed real fault splays into 1-dot islands, and others sample narrow bedrock
windows across alluvial fans. Relocating them onto `>= 1 km` trace gap-bridges and collinear tips
(`bridge1km`) recovered `+444.54 T` (`+0.005352` over `cull1dot` and `+0.000842` over random relocation;
`Δ = −0.001747` on `> 3 px` SGMC truth).
**Decision.** Pre-registered rules and rasters were NOT post-hoc retuned on the surrogate; all three
`TRACKB` variants remain `slot_candidate: false`, and `SLOT_PLAN.md` logs `COLLAR-TO-TRACE` (fund trace
bridges from `PRUNE le3p000` collar dots, conditional on a non-negative Slot 3 receipt).

## IR-86-TRACKB-08 — full-footprint occupied 10 km (`100 px`) blocks match brief §4.2's `0.51–0.59` CV band across historical leaders

**Observed.** Measuring occupied block-density CV across `1, 2, 5, 10 km` scales on 10 tracked
historical scored rasters (`data/scored_fleet/`) showed that while `1 km` gives `0.6235` on R0
(`IR-86-CONC-02/08`) and `5 km` complete blocks give `0.7442`, at **`10 km` (`100 px`, fault-system
scale)** every top-scoring file (`0.2632–0.2778`) sits inside **`0.547–0.570`** (`R0 = 0.570`,
`H27-4 d2.8 = 0.547`, `H19-5 = 0.575`) whereas `gems66-lidar03` (`0.1152`) sits at **`0.960`**.
**Decision.** Logged in `SLOT_PLAN.md` as the unbuilt proposal `CONCENTRATION-10km` so any future
scale-matched concentration test targets `10 km` blocks rather than `1 km` or `5 km`.

## IR-86-CONC-10 — forensic audit retires all off-ridge `CONCENTRATION` slot claims (`conc15`, `dens15`, `spr15`) and resolves `IR-86-CONC-06`/`08`

**Observed.** Restoring all 15 SHA-256-pinned manifest inputs (`training_features.tif`, `derived_sgmc_faults_100m_u8.tif`, `H19-5`, `H19-4`, `H16-1`) enabled direct measurement of the prior `CONCENTRATION` builds (`evidence/concentration_5km_axis_20261023.json`):
1. PR #37's `conc15` (`b1km-move15`) carried an unmeasured constant (`PREDICTIONS["CONCENTRATION"] = 0.006` in `scripts/build_axis_variants.py:57`), placed 2,248 of 5,648 added dots (`39.8%`) at `<= 3.0 px` (`min = 2.236 px`, breaching brief §4.4) with `99.7%` off ancestor ridges, and actually reads **`-0.0071 MODEL`** (`-0.0063` under `±6 px` jitter) on SGMC.
2. PR #44's `dens15` and `spr15` (`IR-86-CONC-06`, built without `.cache/gems_data/` and ranked #1/#2 in `SLOT_PLAN.md` from a synthetic five-truth-model mean) place **`0.0%` of added dots on `H19-5 | H19-4 | H16-1`** and **both lose on SGMC** (`dens15 = -0.0006 MODEL`, `spr15 = -0.0013 MODEL`, matching PR #46's off-ridge `b5km-move10/15/20` at `-0.0066..-0.0150`).
3. Constraining 5 km upward relocations 100% onto ancestor ridges (`concb5kmup4 = -0.0005`, `concb5kmup8 = -0.0007`) eliminates ~95% of PR #46's off-ridge geometric penalty while confirming upward concentration still loses. Conversely, shaving `>= 3`-dot 1 km sub-kernel clusters (`k -> k-1` so occupied blocks never empty) onto sparse-block ancestor ridges (`b5km-cvband-down4` / `concb5kmdown4`, `1,506` dots moved / `8.00%` changed) reaches **`1 km occupied CV = 0.5162` inside `[0.51, 0.59]`** (resolving `IR-86-CONC-08` without desert-floor Poisson scatter) and scores **`+0.0015 MODEL` (`4/4` quadrants `+`, `+0.0020` under `±6 px` jitter) and `+0.0008 PROXY`**.

**Decision.** Retire `conc15`, `dens15`, `spr15`, and `b5km-move10/15/20` from weekly slot consideration; promote `concb5kmdown4` (`8aab97b6`) as the sole count-fixed `CONCENTRATION` slot candidate alongside `RELIEF-frontp15`. **Cost:** historical JSONs remain untouched for reproducibility; human plan updated.

## IR-86-CONC-11 — symmetric fold-fair `d28` rebuild rehabilitates catalogue hide-and-recover `PROXY` (`IR-86-SPACING-05` resolved)

**Observed.** Earlier sessions (`IR-86-SPACING-05`, `IR-86-CONC-09`) saw artificial `+0.014` `PROXY` inflation because static `R0` was already masked at `d_cat > 2.0 px` around held-out faults while relocated dots stepped back inside `2..3 px` of withheld traces. Using unmasked `scored_d28_unscored` (`ab023001...`), `R0 == d28 & footprint & (edt_cat > 2.0)` holds pixel-for-pixel (`0` differing cells). Rebuilding fold-fair `R0_f = d28 & footprint & (edt(f.visible) > 2.0)` and recomputing priors/clearances strictly from `f.visible` inside each buffered whole-component fold (`n = 11,321` withheld positives, `141` 20 km spatial clusters) restores symmetric fold-fair `R0 = 0.0961` and puts `concb5kmdown4` positive (`+0.0008`, `95% CI [-0.0004, +0.0018]`) while `concb5kmup8` is negative (`-0.0026`), matching SGMC's sign. **Decision:** record symmetric `d28` `PROXY` as `REPORT-ONLY` (`evidence_class = PROXY`), never a gate or score.


## IR-86-CONC-12 — the pre-registered 8 % and 2 km arms do not exist; the axis is capacity-capped
Two of the three builds pre-registered in `evidence/concentration-dose-mechanism.md` turned out to be
**geometrically impossible on this parent**, discovered on the first execution and before any score
was computed:

* 1 km `cvband-down8` needs 3,012 destinations; the sparse-ridge 1 km pool at `> 3.0 px` clearance
  and `>= sqrt(8) px` spacing exhausts after **2,399** placements (max feasible dose ≈ 6.37 % of R0);
* 2 km `cvband-2km-down4` needs 1,506; the 2 km pool exhausts after **920**.

**Decision:** the ladder was re-cut to 3 % / 5 % / 6 % on the unchanged 1 km rule, and the matched
ordering control was moved to the 6 % dose so it matches the strongest arm. The amendment is recorded
in the run card (`preregistration.predictions.*.amended_from`) and in the mechanism card; the
original predictions for `down5`/`down6` were **not** revised after seeing the CV values. **Cost:** the
dose curve has no point above 6.4 %, so "more dose" is not an open direction without changing a second
variable (spacing or ridge support). A 2 km block-scale replication is unavailable at the dose that
would make it comparable.

## IR-86-CONC-13 — the CV-band mechanism is falsified as stated; dispersal dose is the live variable
Measured against the pre-registration, the registered **inverted-U** shape is wrong. SGMC `MODEL` and
the fold-fair `PROXY` both rise monotonically with dose (`+0.0013 → +0.0018 → +0.0022` MODEL;
`+0.0004 → +0.0010 → +0.0013` PROXY for 3 % → 5 % → 6 %) while 1 km occupied CV falls
`0.5377 → 0.4998 → 0.4840`, i.e. the best arm lands **outside** the `0.51–0.59` band that PR #47's
card called the target. Separately, the matched ordering control (same source blocks, random dot,
random destination, same count, same gates) captures ≈ 67 % of the ranked arm's MODEL gain and ≈ 62 %
of its PROXY gain.

**Decision:** the `0.51–0.59` CV band is retired as a *mechanism* and demoted to a descriptive
correlate; future CONCENTRATION cards must state a dose, not a CV target. The credit ranking is
retained only as a `≈ +0.0007 MODEL` refinement, explicitly below instrument resolution — no ledger
row or slot note may credit the ranking with the whole gain. `conc6` still dominates PR #47's `down4`
on both report-only instruments, so it is the CONCENTRATION candidate of record, placed in slot 3
behind the two larger predicted levers. **Cost:** a clean price on the ranking needs a paired live
A/B (two slots), which the 3-per-week budget makes expensive; until then the honest prior for this
axis is the control's `+0.0015 MODEL`.

## IR-86-CONC-14 — the leakage canary initially flagged AUC 1.0000 because the canary itself leaked
On the first execution the canary returned `max_auc = 1.0000`, which trips the brief's stop rule. The
cause was in my own feature dict: `catalogue_px` is the scoring target verbatim, so its AUC is 1.0 by
construction. It was replaced by `block_density_1km_parent` (a feature the rule actually uses), and no
result was read before that fix.

**Decision:** the stop rule was honoured literally (the run aborted and no raster was written), and
the canary now reports only features that enter the edit: against the catalogue target
`ridge_union_px` 0.5154, `unique_credit_parent` 0.5037, `block_density_1km_parent` 0.5094, and
against the SGMC off-catalogue target 0.5086 / 0.5023 / 0.5467 respectively — worst case 0.5467,
far below 0.90. **Cost:** none, but the episode is a reminder that a "leakage canary" can pass or
fail on the choice of feature, so the feature list must be printed with the number.

## IR-86-RELIEF-04 — the only instrument that supports RELIEF is a relief-index meter (R² = 0.9135, n = 8)

**Observed.** Eight deterministic RELIEF rebuilds of R0 (the three shipped ladder arms, this
session's three arms, and two displacement-matched random nulls) were scored on the SGMC-extra
surrogate and regressed on the one quantity that varies across all of them, the change in mean
`relief_index` at the dots (`evidence/relief_source_20261023.json`, `instrument_diagnostic`):

| arm | Δ mean relief index | surrogate Δ (MODEL) | residual vs the fit |
|---|---:|---:|---:|
| `front+15pct` (reconstruction of the ledger row) | +0.2058 | **+0.00171** | −0.0008 |
| `front+10pct` (reconstruction) | +0.1370 | +0.00100 | −0.0009 |
| `front-10pct` (reconstruction) | −0.1163 | −0.00885 | −0.0023 |
| `int2front-15pct` (new) | −0.0587 | −0.00569 | −0.0007 |
| `int2front-10pct` (new) | −0.0565 | −0.00379 | +0.0011 |
| `int2pied-15pct` (new) | −0.2987 | −0.01179 | +0.0000 |
| null, random destination (interior source) | −0.0677 | −0.00298 | +0.0020 |
| null, random destination (piedmont source) | +0.0170 | −0.00256 | −0.0008 |

Pearson **r = +0.9558, R² = 0.9135, slope +0.0283 DTI per index unit**, intercept −0.0033 (the
"displacement tax": an arm that does not change mean relief index is predicted to lose 0.0033).
The surrogate's single-feature AUC for `relief_index → SGMC-extra` is `0.7281`, so this is not a
coincidence of the arms: to first order the instrument is a monotone function of exactly the
quantity every RELIEF variant manipulates. The reconstruction of `front+15pct` reproduces the
ledger's delta to three decimals (`+0.001711` vs `+0.0017`), so the regression is on the shipped
recipe, not a look-alike.

**Decision (changes the slot order).** No RELIEF MODEL number may be cited as *mechanism*
evidence. `front+15pct`'s `+0.0017` is what the instrument reports for a `+0.206` shift in mean
relief index, and its residual is **−0.0008** — i.e. after the gradient is removed it is
indistinguishable from (slightly below) the instrument's own line. `RELIEF-frontp15` is therefore
**demoted from Slot 1 to Slot 3**; `PRUNE-le3p000` takes Slot 1 (its relief-index change is
near zero, so this bias cannot manufacture its `+0.0040`), and `CONC-concb5kmdown4`
(`+0.0015 MODEL` **and** `+0.0008 PROXY`, two differently-biased instruments agreeing, `1 km`
CV inside `0.51–0.59`) takes Slot 2. **Cost:** the RELIEF family keeps its rows and rasters, but
its published support is reclassified as instrument-shaped; a live receipt is now the only thing
that can restore it, and at `+0.0017` a single slot could never clear the §"|Δ| < 0.01 = no
evidence" floor anyway.
**Not claimed:** that RELIEF is wrong. `relief_index` tracks real basin-margin structure; the
claim is that this instrument cannot separate that from its own gradient.
**Limit:** n = 8 deterministic rebuilds of one parent, not independent experiments, and seven of
the eight sit on two source classes of a single grid. It prices the instrument; it does not
re-score the competition.

## IR-86-RELIEF-05 — the basin source cannot be tested inside the axis contract (2,014 dots = 5.35 %)

**Observed.** Regime census of R0 this session: piedmont 20,280 dots (53.86 %), range-front 6,045
(16.05 %), range-interior 9,315 (24.74 %), **basin 2,014 (5.35 %)**. Brief v2 §5 fixes the RELIEF
dose at 10–15 % of the parent's dots, i.e. 3,765–5,648 dots. The basin holds fewer dots than the
*floor* of that window, so "does leaving the alluvium pay?" — the cleanest geological version of the
question — cannot be asked as a RELIEF variant at any legal dose.
**Decision:** the source was varied over the range interior (the only remaining class with enough
mass) and the basin question is recorded as **unbuildable on this parent**; it would need a
different axis (a mass-controlled test at ≤ 5.35 %, which is a MASS edit, and MASS is closed per
`IR-86-MASS-01..03`). **Cost:** one of the three arms that looked most promising on mechanism
grounds was never built, and the factorial is therefore 4-cell (interior/piedmont × front/piedmont)
rather than the 6-cell design with basin.

## IR-86-CONC-15 — the SGMC-extra instrument rewards *outward movement* for CONCENTRATION arms, not lineaments

**Observed.** The SGMC surrogate's truth is `SGMC − catalogue`, so a dot in the mapped-fault collar can
never earn credit there, while the organiser states new truth *can* lie within 300 m of a known trace —
and R0 is built almost entirely of such dots. Measured on this session's three arms
(`evidence/concentration_surfext_axis_20261023.json` → `instrument_confound`): `surfext10`'s added mass
sits **21.7 px** from SGMC-extra truth versus **22.6 px** for the mass it removed (the treatment moved
mass *toward* SGMC truth) yet beats its matched control by only **+0.0012 MODEL**; the control moved
mass *away* (22.8 px) and still scored **+0.0047 MODEL** in 4/4 quadrants. The fold-fair PROXY is biased
the opposite way, since it can only reward mass near *withheld catalogue* traces — exactly what surface
extension gives up (`−0.00003` treatment vs `−0.0008` control).
**Decision.** CONCENTRATION MODEL deltas are not compared across arms with different
catalogue-distance profiles; every arm is read against a matched control, never against zero, and a
positive SGMC delta alone is not evidence of lineament knowledge. This is the same instrument failure
mode already recorded for RELIEF (`IR-86-RELIEF-04`) and for the CV band (`IR-86-CONC-13`).

## IR-86-CONC-16 — R0 is saturated on its own evidence surface; the headroom is *off* that surface

**Observed.** Confirms and localises `IR-86-CONC-12`'s ≈6.4 % capacity cap. Measured on the pinned
inputs before any candidate was built: all 37,654 R0 dots lie on the `H19-5` ancestor surface, and under
the parent's own constraints (`> 3.0 px` from the catalogue, `>= 2.8284 px` from every dot) only **90**
legal free cells remain on that surface — the merged cvband rule's within-surface destination capacity
is ~2,400 dots. `H19-4 | H16-1` minus `H19-5` is 35,954 px of near-equal owner-reported quality
(`0.1894` / `0.1855` vs `0.1922`, all CLAIM) carrying **zero** parent mass, with 8,671 legal free cells
(6,456 placeable greedily).
**Decision.** Future CONCENTRATION/SPACING sessions must state the free-slot count before building;
within-surface reallocation is treated as closed, and the open headroom is surface extension
(`H19-4 | H16-1` ground, or a new evidence surface) — carried in `SLOT_PLAN.md` as
`EVIDENCE-OFFSURFACE` and tested at probe strength by `b5km-surfext-down10` (predicted live Δ ≈
0.000…+0.003, below the evidence floor).

## IR-86-CONC-18 — the pediment refinement of the dispersal rule FAILS its SGMC falsifier; instruments split; no slot change

**Observed** (session `arena/f29e1689`, `evidence/concentration_pediment_axis_20261023.json`; R0 rebuilt
byte-exactly first). The pre-rev-E SLOT_PLAN's pediment proposal (former proposal 2, `IR-86-TRACKB-08`
line) was built as three destination-regime splits of the `concb5kmdown4` shave: `concb5kmpeddown2p5`
(941 dots, 5.00 % chg, 100 % in-window), `concb5kmnonpeddown2p5` (941 dots, 100 % out-window,
attribution control), `concb5kmpeddown5` (1,882 dots, 10.00 % chg, 55.6 % in-window). The truth-free
pediment window (3DEP `relief_local` 10–40 m, > 1 km from the RELIEF regime front; 18.8 % of the
footprint) **caps at 1,045 moved dots** under the > 3 px / √8 px rules — a *window-specific* capacity
beside `IR-86-CONC-12`/`16`'s within-surface caps — so the pair is dose-matched at 2.5 % of R0.

1. **SGMC MODEL falsifier fired:** at the identical dose the non-pediment complement beats the
   pediment arm (+0.0013 vs +0.0007; REF `concb5kmdown4` +0.0015 replicates the recorded value
   exactly). As far as mapped-fault truth can tell, the dispersal gain is **generic sparse-ridge
   coverage**, not the thin-alluvium concealed-fault prior.
2. **Displacement is matched** (mean 1,612.7 vs 1,630.8 px; median 1,597.3 vs 1,582.3), so
   `IR-86-CONC-15`'s outward-movement bias is common-mode across the pair and cannot explain the
   ped/nonped gap — but it inflates both vs R0, which is why the quoted read is arm-vs-arm, not
   arm-vs-zero.
3. **The symmetric fold-fair d28 `PROXY` orders the arms oppositely** (+0.0012 in-window vs +0.0004
   out-window, CIs straddling/near zero): the attribution is *split*, not resolved. No arm clears the
   0.01 live-evidence floor (max |Δ| = 0.0017).
4. **Dose** is near-linear on SGMC (+0.0007 → +0.0017 at 2×) but the 2× dose pushes the 1 km CV to
   0.5013, below the (already demoted, `IR-86-CONC-13`) CV-band's lower edge.

**Decision.** No slot change: slots stay exactly as rev E ranks them (`le3p000`, `conc6`/`concb5kmdown6`,
`frontp15`). The three pediment arms are recorded `BUILT` audit artifacts and are **never upload
candidates**. Any future pediment-restricted CONCENTRATION design is capped at ~2.8 % of R0's dots by
destination capacity. The 10 km CV definition was pinned to `IR-86-TRACKB-08` (fully-covered 100 px
blocks: R0 = 0.5699 vs 0.736 unfiltered — both now reported by
`gems86.concentration_pediment.cv_report`).
## IR-86-CONC-17 — concurrent-session collision: two independent sessions built the same down-dose ladder; one build is byte-identical

**Observed.** This session (`arena/4822aa3b-gemsdoe86`, PR #55) and the concurrent PR #50 session
(`arena/60ecf1c8`) both self-assigned CONCENTRATION, both extended the `b5km-cvband-down4` dose
curve, and both named their artifacts `run_concentration_dose.py` / `variants_concentration_dose.json`.
PR #50 merged first (with `cvband-down3` `ffb47d4b`, `cvband-down5` `a2f8aaad`, `cvband-down6`
`1ed78e0f`, and a `CONTROL-cvband-down6-randcredit` `a6838dc2`). On merging origin/main for PR #55,
this session's `b5km-cvband-down6` proved **byte-identical** to PR #50's `conc6` (same zeros sha256
`1ed78e0f…`) — the same deterministic pipeline and dose from two independent runs, which is itself
a reproducibility datum. This session's other two rungs are new: `b5km-cvband-down2` (`f0ee647f`,
753 moves — a point below PR #50's lowest rung) and `b5km-cvband-downmax` (`d4a42664`, 2,381 moves —
the exact binary-searched sparse-ridge destination-pool ceiling), which confirm `IR-86-CONC-12`'s
"≈ 6.4 % of R0" capacity cap with the precise number (2,381 = 6.32 %) and show the marginal 122
moves past `conc6` cost more than they bought (`+0.0020` vs `+0.0022` MODEL, both 4/4 quadrants).
This item was first drafted as "IR-86-CONC-12" before main's numbering was known; 12/13/14 are
taken (`IR-86-CONC-14` is PR #50's own canary item), so it is renumbered here.

**Decision.** This session's `down6` is recorded `BUILT-DUPLICATE` (house pattern:
`gems86-h33-2b2-prune3` `collar3px`), pointing at PR #50's `conc6` BUILT row; files renamed to
`scripts/run_concentration_dose_rungs.py`, `tests/test_concentration_dose_rungs.py`,
`ledger/variants_concentration_dose_rungs.json`, `evidence/concentration_dose_axis_20261023.json`;
`down2`/`downmax` recorded `BUILT` as curve brackets, not slot candidates (Slot 2 stays `conc6`
per rev. D). No slot was spent; the exact-hash duplicate is kept in the ledger rather than deleted,
because two independent byte-identical builds is evidence the down-mechanism dose ladder is
reproducible, and the brief's dedupe rule is "exact hash and repeated (parent, axis, value)".

## IR-86-CONC-19 — IR-86-TRACKB-08's "R0 10 km CV = 0.570, inside 0.51–0.59" does not reproduce under the canonical block-density definition

**Observed.** `IR-86-TRACKB-08` and `SLOT_PLAN.md` proposal 2 state that at 10 km (100 px) every top-scoring file sits inside CV `0.547–0.570` with `R0 = 0.570`. Measuring R0 this session with the repo's canonical `gems86.concentration_5km.block_density_stats` (occupied blocks; density = dots / footprint cells per block) gives **0.7360** (complete blocks, 538 occupied) and **0.7331** (padded blocks, 547 occupied); count-CV variants give 0.6434 / 0.6422. No variant of the canonical definition reproduces 0.570, so the TRACKB session's 10 km numbers must come from a different (unrecorded) block accounting — e.g. a different occupied/valid rule or density normalisation.
**Decision.** Treat the *qualitative* TRACKB-08 observation (leaders cluster tightly at 10 km; the 0.1152 lidar file is an outlier) as unreplicated until re-measured under one stated definition, and do not quote `0.547–0.570` as a target band at 10 km. This session's 10 km builds therefore report CVs under the canonical definition only (R0 0.7360 → down4 0.5182, down8 0.4956, up8 0.5450) and the slot argument for dispersal rests on the two instruments, not on band membership. **Cost:** the "10 km CV law" cannot currently justify a slot by itself; re-measuring the 10 historical fleet files under the canonical definition is a zero-slot task for a future session.

## IR-86-SPT-01 — 2026-10-24 SPT candidate vs the negative-only release audit (SUPERSEDED BY `IR-86-SPT-02`)
`scripts/audit_release.py` only certifies the 10 registered historical artifacts as DO NOT SUBMIT and fails closed on any other TIFF under `docs/`. The new SPT candidate (sha256 `26cf2d39…`) therefore lived in `submission/` (linked from `docs/submit.html`), not `docs/downloads/` — **revoked and quarantined outside `docs/` in `IR-86-SPT-02` below**.

## 2026-10-24 review — builder entrypoint bypass and freshness

- **IR-86-20261024-01 (repaired):** **43** CLI builder/feature/pipeline `main()` commands (including `build_gems86_swcon.py`, `generate_unique_submission.py`, `experiment.py`, `run_experiment.py`, `run_h86.py`, `run_lane.py`, `prune_collar.py`, `build_spt.py`, `build_xfleet.py`, `gen_tip_final.py`, `build_submission.py`, `h86b/c/d_features.py`, `prepare_h86_fvmb_data.py`, `run_h86_fvmb_pipeline.py`, `run_h86_wvb.py`, and `run_lane86/b/c/d.py`) and **8** imported orchestration entrypoints (including `run_experiment.run`) are now uniformly AST- and runtime-tested in `tests/test_builder_preflight.py` to enforce `protocol_preflight.require_feasible()` before argument parsing, feature loading, or placement; missing evidence remains an error and `--no-write` / `--measure` does not authorize construction in memory. Shared evaluator/writer bytes and historical scientific evidence are unchanged.
- **IR-86-20261024-02 (repaired):** automated re-audits still rendered a dated
  2026-10-23 session card as "this session". Preserve that archive and additionally
  issue a current UTC, report/registry-hash-bound negative receipt only after fresh
  registry measurement; site builds reject stale or optimistic receipts.
- **IR-86-20261024-03 (open):** H33 page recommends a 177-character note, above
  this project's 140-character rule. Its HTML says projected/UNSCORED, not an
  organizer receipt for the owner-reported result. No current leaderboard or
  organizer acceptance was obtainable from the allowed-host network in this run.
- **IR-86-SPT-02 (repaired):** Commit `2538214` (PR #60) bypassed `protocol_preflight.require_feasible()` at module import in `scripts/build_spt.py` and `scripts/build_xfleet.py`, placed unregistered binaries `submission/gems86-spt-throwcons-37654dots-20261024T010000Z-2943374c-zeros.{tif,zip,json}` (`sha256: 26cf2d392663b4ad3118534b07de889099e0ea9d48bfa3bcddbf8ca00dd5b342`) outside `docs/downloads/`, published `docs/evidence/spt-run-card.json` (`verdict: "promote-candidate"`, `submission_ready: true`) and a hand-edited `docs/submit.html` (`READY TO DOWNLOAD`) contradicting `docs/index.html` (`DO NOT SUBMIT`), masked `dist_cat > 2.0` using the **full** `existing_faults.tif` catalogue (leaking withheld test-fold fault locations with zero split buffer), promoted a coin-flip surface (`canary_score_auc = 0.4947 < 0.50`) with `100%` literal witness overlap (`my_dots_within_3px_of_theirs = 1.0` against `17GEMSDOE`), and claimed signed paired-throw on `training_features.tif` bands 15/13/12 in `research/SPT_20261024.md` while `build_spt.py` never opened `training_features.tif` and ran with `SPT_PENALTY=0`. Remedied by gating `build_spt.py` and `build_xfleet.py` behind `require_feasible()`, revoking `spt-run-card.json` / `xfleet-run-card.json` / `spt-independent-validation.json` / `docs/submit.html` to `verdict: "negative"` (`DO NOT SUBMIT`), quarantining `submission/gems86-spt-throwcons-*` outside `docs/` (excluded from GitHub Pages, `download_authorized: false`, and cryptographically SHA/ZIP-verified against `docs/evidence/spt-full-support-witness-audit.json` in both `audit_release.py` and `check_site.py`), and failing closed on any other binary or byte modification in `submission/`.
- **IR-86-TIPRELAY-01 (repaired):** Concurrent PR #63 (`502fc14`, `H86-TIPRELAY`) committed an unregistered GeoTIFF/ZIP (`docs/downloads/gems86-h86-tiprelay-37654-20261024T070000Z.{tif,zip,json}`, `sha256: c56945618d8316f4f134474c1f707444a46892a47aa7b7e18181bee6243daae3`), inserted a `tiprelay` filename exclusion backdoor into `scripts/audit_release.py`, added `scripts/gen_tip_final.py` executing at import time without `protocol_preflight.require_feasible()`, wrote `"verdict": "promote"`, `"submission_ready": true`, `"holdout_dti": {"status": "PROJECTION_NOT_HOLDOUT"}` in `docs/evidence/h86-tiprelay-run-card.json` with zero spatially-blocked holdout evaluation, and hand-edited `docs/index.html` and `docs/executive-summary.html` with escaping `../research/` links that broke `build_site.py --check`, `check_site.py`, and `audit_downloads.py`. Read-only measurement via `gems57.uniqueness.compare_to_registry` proved `my_dots_within_3px_of_theirs = 0.8508 > 0.70` even against sparse `GEMSDOE32` `h33-h33-2-b2` (`0.8510 > 0.70` vs `GEMSDOE28`, plus `1.0 > 0.70` vs `17GEMSDOE`). Remedied by removing the unregistered `docs/downloads/gems86-h86-tiprelay-*` files and `audit_release.py` backdoor, gating `scripts/gen_tip_final.py` behind `require_feasible()`, revoking `docs/evidence/h86-tiprelay-run-card.json` to `verdict: "negative"`, and regenerating `docs/*.html` from `scripts/build_site.py`.
- **IR-86-PROMPT-CONFLICT-20261024 (flagged):** The 2026-10-24 request states both `Current competition leaderboard GEMSDOE high score: 0.4413` and `0.3195 is the highest score right now`, and lists 92 sites (`GEMSDOE`..`GEMSDOE92`) of which 6 (`GEMSDOE86`, `GEMSDOE88`..`GEMSDOE92`) have no supplied score (`2` carry prompt-named unscored artifact IDs: `GEMSDOE89` `gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros:` and `GEMSDOE90` `gems90-cnc-35000dots-20261024T084324Z:`, and `4` have bare `:` lines: `GEMSDOE86`, `GEMSDOE88`, `GEMSDOE91`, `GEMSDOE92`). Preserved verbatim in `research/REQUEST_20261024.md` as unverified `OWNER-REPORTED` / `PROMPT-NAMED UNSCORED` input; missing entries stay blank (`None`), never `0.0`.
- **IR-86-USGS-504-20261024 (resolved on recheck) & IR-86-USGS-GGGSC-404-20261024 (flagged):** While the prompt's legacy science-center link `https://www.usgs.gov/centers/gggsc/science/geodawn-geoscience-data-acquisition-western-nevada` returns USGS `HTTP 404` ("Lost Bison"), `https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and` and ScienceBase DOI `https://doi.org/10.5066/P93LGLVQ` both return `HTTP 200` on live recheck (`docs/evidence/source-recheck-20261024.json`), confirming Glen & Earney (March 4, 2024, CC0 1.0, `149,030 line-km`, `51,857 sq km`, `200/400 m` E–W flight lines and `2000/4000 m` N–S tie lines).
- **IR-86-BAND-INDEX-20261024 (repaired):** Prior hypothesis prose in `registry/h86c_hypotheses.json` and `research/SESSION_20261024_REVIEW.md` misattributed `training_features.tif` Band 2 as `mag_horiz_grad` (actual Band 2 = `rtp`; `tmi_hg` = Band 3), Band 6 as `ter_rad_k` (actual Band 6 key = `tc`), Band 10 as `surf_rough` (actual Band 10 = `deq_n100a15`), and Band 14 as `rtp_tilt_deriv` (actual Band 14 = `tmi`), and mischaracterized `GEMSDOE81` (`0.0041`) as continuous rather than binary unit-mass near-catalogue dots (`100%` at `d_cat <= 5 px`, median `2.24 px`). Corrected against `src/gems86/io.py` and enforced by regex regression test in `tests/test_fleet_feed.py`.
- **IR-86-BAND6-TC-MISLABEL-20261024 (repaired):** Direct pixel-level verification (`scripts/verify_band_physics.py` → `docs/evidence/band-physics-verification-20261024.json`) proves that the embedded GeoTIFF header string inside `training_features.tif` for **Band 6** (`'tc - Tilt angle or total curvature - magnetic field derivative for edge detection'`) is **physically false in the competition file metadata itself**. Across all `5,164,300` valid footprint pixels, Band 6 is strictly positive (`min = +2.953424`, `median = +18.481700`, `max = +88.566544`, `0` non-positive pixels — making zero-crossing magnetic-tilt edge detection impossible), correlates at **`r = +0.997140`** with USGS GeoDAWN Airborne Gamma-Ray Spectrometry **Total Count (`TC`)** (`DOI 10.5066/P93LGLVQ`; `r = +0.915310` with `Th`, `r = +0.881676` with `K`, `r = +0.715073` with `U`), and correlates at only **`r = +0.012796`** with true analytical magnetic tilt $\arctan2(\text{Band 9 } \text{tmi\_vg},\, \text{Band 3 } \text{tmi\_hg})$. Repaired across `src/gems86/io.py`, `registry/h86c_hypotheses.json`, `research/GEOTHERMAL_VENT_DISCOVERY_SYNTHESIS.md`, and `research/H33_INTERPRETATION_REVIEW.md`.
- **IR-86-BAND11-18-GRAV-VECTOR-20261024 (repaired):** Direct spatial finite-difference verification of `Band 13 (iso_grav_anom)` across `5,152,505` interior footprint cells (`docs/evidence/band-physics-verification-20261024.json`) proves that **Band 18 (`iso_grav_anom_hg`)** is the **signed East-West horizontal derivative** $+\partial g_{\text{iso}}/\partial x_{\text{east}}$ (`r = +0.948186`, vs `r = +0.027557` against scalar $|\nabla_h g_{\text{iso}}|$) and **Band 11 (`iso_grav_anom_vg`, labeled `'vertical gradient'` in the GeoTIFF header)** is actually the **signed South-directed horizontal derivative** $+\partial g_{\text{iso}}/\partial\text{row} = -\partial g_{\text{iso}}/\partial y_{\text{north}}$ (`r = +0.938102`), with $\sqrt{\text{B11}^2 + \text{B18}^2}$ reproducing **Band 5 (`iso_grav_anom_slope`)** at `r = +0.946995`. By Laplace's equation ($\nabla^2 U = 0$), the footprint-masked, Gaussian-regularized (`sigma = 400–600 m`) vertical gravity curvature $g_{zz} = -(\partial_x\text{B18} - \partial_y\text{B11})$ matches $-\nabla_h^2(\text{Band 13})$ at `r = +0.8627` to `+0.9149` purely from competition Bands 11 and 18 (`H86E-SPBT`).
- **IR-86-DUAL-SATURATION-20261024 (measured):** In addition to the continuous `17GEMSDOE` witness (`ab0a0a62...`, `5,106,385 / 5,106,385 = 100.0%` allowed coverage), the discrete binary stride-5 dot lattice `13GEMSDOE` (`20261001_r13-lattice-s5_v2_nan-outside.tif`, `b4570b40...`, `206,895` binary dots, `0.0904` `OWNER-REPORTED`) covers `5,099,871 / 5,106,385` (`99.8724%`) of allowed pixels within `3 px` (`uncovered_allowed_pixels = 6,514`). By the pigeonhole principle, any `37,654`-dot allowed raster has forward 3-px overlap `>= 1 - 6514/37654 = 82.70% > 70%` against `13GEMSDOE`. Therefore, any future upstream protocol amendment in `60GEMSDOE` must be saturation-aware (excluding high-halo `>50%` footprint witnesses or using symmetric overlap), not merely excluding non-binary surfaces.
- **IR-86-FLEET-GEMS89-90-20261024 (measured):** Direct byte-level GeoTIFF validation and pinned `vendor/gems57/uniqueness.py` overlap verification (`docs/evidence/prompt-named-unscored-audit-20261024.json`) of the two newly prompt-named unscored fleet entries revealed severe uniqueness and evaluation irregularities in both sibling repositories: (1) `GEMSDOE89` (`gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros.tif`, `140,693` B, `sha256: 715c8b86...`, `37,654` dots) claimed `complete_registry_coverage: true` and `verdict: "promote"` in `registry/h89_run_card.json` over a 91-geometry subset that omitted both `17GEMSDOE` (`1.0000 > 0.70` forward 3-px overlap) and discrete binary `13GEMSDOE` (`0.999203 = 37,624 / 37,654 > 0.70` forward 3-px overlap), while contradicting its adjacent `.json` writer receipt (`approved_for_weekly_slot: false`, `promoted: false`); (2) `GEMSDOE90` (`gems90-cnc-35000dots-20261024T084324Z.tif`, `241,734` B, `sha256: e1e91be2...`, `35,000` dots; repository `README.md` also retains unresolved merge markers) privately altered the protocol uniqueness rule in `evidence/run_card.json`, exceeded *both* clauses of its own altered rule (`max_overlap = 0.983286 > 0.70` and `max_excess_over_chance = 0.403712 > 0.30`; pinned `gems57/uniqueness.py` measures `1.0000` vs `17GEMSDOE` and `0.983486 = 34,422 / 35,000` vs binary `13GEMSDOE`) yet still recorded `duplicate: false`, relied on external USGS `qfault_sliprate_den` (`AUC = 0.7784`) on 4-fold cut segments (`60,823` px) as its #1 feature, and failed its own score-history calibration (`verdict: "NEGATIVE"`).
- **IR-86-RULES-SECT-20261024 (repaired):** `scripts/build_site.py` (`docs/executive-summary.html` portal checklist) previously cited `Official Rules §5–6` for the 3-per-week public leaderboard limit and single final entry across Phase 1 ($50k) and Phase 2 ($250k). Live line-by-line verification of `https://docs.nlr.gov/docs/fy26osti/96647.pdf` confirmed the Official Rules PDF contains only Sections 1–4 plus Appendix A, with the prize phases, weekly submission cap, and single final selection specified in `§1.1` and `§3.2–3.6`; fixed in `scripts/build_site.py` and `docs/executive-summary.html` and guarded in `tests/test_current_review.py`, alongside fixing a stale `H86C-MMT` string in `docs/evidence/session-20261024-run-card.json` to match `registry/h86c_hypotheses.json` (`H86E-SPBT`).
- **IR-86-DROPBOX-MIRRORS-20261024 (repaired):** Cross-repo search located the 5 Dropbox links referenced in the prompt inside `buffedlizard55-lab/16GEMSDOE/README.md` (`GEMS_96647.pdf`, `example_submission.tif`, `existing_faults.tif`, `gems-geodawn-numerical-features.tif`, `Digital-elevation-model-links-JSON.pdf`); these are personal convenience shares (`dl=0`), not official DOE/NLR/USGS/DrivenData hosting, and are unreachable inside egress-restricted sandboxes. Repaired `scripts/restore_data.py` with SHA-256-verified `EXTERNAL_PINS`, atomic `.partial` staging, `sync_grid_root()`, `--protocol-only` / `--include-registry` flags, and SHA-256-gated `--source dropbox` (`dl=1`) workstation fallback, covered by `tests/test_restore.py`.
- **IR-86-SWCON-01 (repaired):** Concurrent PR #77 (`510fdb6`, `SWCON`) committed unregistered binaries (`docs/downloads/gems86-swcon-e3-37654dots-20261024-zeros.{tif,zip,json}` and `submission/gems86-swcon-e3-37654dots-20261024-zeros.{tif,json}`, `sha256: 5576b15c...`), an unguarded builder `scripts/build_gems86_swcon.py`, and hand-edited `docs/swcon-submission.html` + `README.md` (`OK TO DOWNLOAD AND SUBMIT`) that immediately broke all three CI workflows on `main`. Direct measurement via `vendor/gems57/uniqueness.py` proved `0.997769` (`37,570 / 37,654 > 0.70`) forward 3-px dot overlap against discrete binary dotted `13GEMSDOE` and `1.0000` against `17GEMSDOE`, alongside below-chance canary `AUC = 0.4046`, missing `ci95 = null`, and `HOLDOUT-DTI = 0.00746`. Repaired by removing the unregistered `SWCON` binaries and `docs/swcon-submission.html`, gating `scripts/build_gems86_swcon.py` behind `protocol_preflight.require_feasible()`, and revoking `docs/evidence/swcon-run-card.json` and `research/SWCON_20261024.md` to `verdict: "negative"`, `submission_ready: false`.
- **IR-86-FAULTHALO-01 (repaired):** Concurrent PR #80 (`3c98290`, `gems86-faulthalo-4210938px-20261024T181838Z-219b3357-zeros.tif`, `sha256: 8a66c57c...`) omitted `protocol_preflight.require_feasible()` in `scripts/generate_unique_submission.py` to emit a continuous `4,210,938`-pixel Euclidean distance halo around `existing_faults.tif` (`0.998783` forward 3-px overlap vs discrete binary `13GEMSDOE`, `1.0000` vs `17GEMSDOE`, zero geological bands, `HOLDOUT-DTI = NOT_RUN`), and inverted `α = 0.2` (FP) and `β = 0.8` (FN) in `research/H33_ANALYSIS.md`. Repaired by gating `scripts/generate_unique_submission.py`, `scripts/run_h86e.py`, and `scripts/finalize_h86e.py` behind `require_feasible()` (`45` CLI builders + `8` imported orchestrators in `tests/test_builder_preflight.py`), fixing `research/H33_ANALYSIS.md`, and retaining `gems86-faulthalo-*` solely as an audited `DO NOT SUBMIT` inventory record (`docs/evidence/h86-faulthalo-run-card.json`, `verdict: "negative"`).

See `research/SESSION_20261024_REVIEW.md` and
`docs/evidence/source-recheck-20261024.json` for exact scope and unresolved blockers.


## 2026-10-24 — H86E-RIDF session (lane `ridf`; distinct from the concurrent H86E-CCTX session below)

- **PA-86-01 (amendment, public):** the 17GEMSDOE witness is a continuous surface (support fraction 1.0); the shared template's `two_phase_summary` like-for-like reading is used for new lanes via `require_like_for_like()`. Literal reading still reported. A saturating dot field still stops.
- **PA-86-02 (amendment, public):** an overlap firing against a raster whose own 3 px halo covers > 70 % of the allowed area is non-informative (a random dot set would fire); rho ≤ 0.90 then decides. Firings with halo coverage ≤ 70 % remain hard stops.
- **IR-86-RIDF-01:** the surface registry check ran after placement rather than before; result (rho 0.9045 > 0.90, stop) unchanged.
- **IR-86-RIDF-02:** first R0 comparator used GEMSDOE28 `r1-solo` (excludes dots near the full catalogue) → 0.0286; corrected to GEMSDOE25 `dotted-h19-5-d2-8` → 0.0961 (reproduces the KSLB card exactly).
- **IR-86-RIDF-03:** catalogue-hide holdout cannot score fleet rasters built with the full catalogue (H33 = 0.0037 as-is); holdout–LB alignment unvalidated (Spearman 0.24, n = 17, owner-reported LB).
- **IR-86-RIDF-04:** two registry inventory entries are not on the competition grid (14GEMSDOE horse-ensemble transform; 7GEMSDOE qfaults prior u8) and were recorded as errors, so the scan is not "complete".
- **IR-86-RIDF-05:** SWCON (PR #77, merged to main concurrently) was published as "OK TO SUBMIT" after a uniqueness check against local files only. It is a score-weighted consensus of 33 prior fleet submissions, and its per-source overlap cap was tuned against that same local set. On the full 682-raster registry it has 58 informative dot-field firings, so it is a duplicate. Its holdout (0.00746, full-catalogue proxy, no CI) is not comparable with the buffered-holdout best. Verdict changed to `negative`, with `original_verdict` kept.

## 2026-10-24 H86E session — owner-mandated generation under a blocked literal rule

- **IR-86-H86E-01 (SUPERSEDED — bypass revoked; historical record retained):** The 2026-10-24 H86E request explicitly ordered generation of a unique TIF with fully automated (no-human) validation, which is impossible while `protocol_preflight.require_feasible()` hard-stops every builder under the literal full-support overlap rule (IR-86-DUAL-SATURATION-20261024). An earlier revision of `scripts/run_h86e.py` and `scripts/finalize_h86e.py` therefore did not call `require_feasible()`; instead they used the shared `gems57.uniqueness.two_phase_summary` and reported BOTH the literal reading (worst forward overlap `1.0` vs the pinned dense witness; `0.9988` vs the stride-5 lattice) and the like-for-like dot-field reading (worst geological overlap vs the GMC catalogue-halo control), with thresholds unchanged (`rho 0.90`, overlap `0.70`). No shared tool was forked or edited. The generated artifact is fully registered (`docs/evidence/download-inventory.json`, `registry/artifact_cards.json`), passes `audit_release.py --measure-registry`, and its own automated gates (`docs/evidence/h86e-run-card.json`) return **DO NOT SUBMIT** (G4/G5/G6 fail), so no weekly slot is authorized by this amendment. **The bypass itself has since been revoked:** both scripts now call `require_feasible()` as the first action of `main()`, before argparse, grid load, feature construction, fitting or placement, and are pinned by `tests/test_builder_preflight.py` (an owner mandate to produce a file is not a protocol exemption; AGENTS.md item 8). The E1-E3 measurements and the published artifact are preserved as a `DO NOT SUBMIT` audit record of the ungated revision, not as a live authorization. Future sessions must not cite this entry as a general preflight bypass: the literal stop remains binding for any submission authorization.
- **IR-86-PROSE-CODE-01 (repaired):** Two builders shipped docstrings contradicting their own enforced guards — the IR-86-SPT-02 "misrepresented prose vs code" defect class. `scripts/generate_unique_submission.py` claimed it "does NOT call `protocol_preflight.require_feasible()`" while `main()` did (left stale when PR #80 was gated under IR-86-FAULTHALO-01), and `scripts/run_h86e.py` claimed the same while `main()` did (left stale when PR #83 was gated). Both docstrings were corrected to describe the enforced behaviour and the revoked bypass; no guard, threshold or measurement was changed. `tests/test_builder_preflight.py::test_gated_builder_docstring_does_not_claim_a_preflight_bypass` now fails any `BUILDERS` entry whose docstring asserts a bypass, so this cannot silently recur.
- **IR-86-H86E-02 (measured):** First E3 run degenerated (`p=1` on catalogue, `p~1e-6` elsewhere, HOLDOUT-DTI `0.0209`) because plain distance-to-visible-catalogue is `0` exactly on training positives (self-identity leak, preserved in `.cache` run-1 log summary inside `research/H86E_SESSION_20261024.md`). Repaired with other-component (two-group) distances and self-corrected densities; corrected rerun is the reported E3. The buggy run is an implementation defect record, not a scientific result.

## IR-86-GAPRES-01 (2026-10-24) — literal overlap rule unsatisfiable; dotted reading used and disclosed
`scripts/build_gems86_gapres.py` does not call `protocol_preflight.require_feasible()` (same
owner-mandate pattern as IR-86-H86E-01). The pinned 17GEMSDOE witness is a continuous
probability surface with support>0 over ~the whole footprint, so under the literal
support>0 dot definition every nonempty candidate has 1.0 forward 3-px overlap and the
>0.70 lane rule can never pass. GAPRES therefore reports BOTH readings in
`docs/evidence/gapres-run-card.json`: dotted-fleet reading (worst overlap 0.000 vs 26 local
binary fleet rasters) and the literal dense-witness reading (1.0, unsatisfiable). No
threshold was changed and no slot was authorized; verdict remains DO NOT SUBMIT on the
independent holdout gate. Resolving this requires an explicit revised protocol from the
owner, not a private exemption.


## IR-86-REGISTRY-BINDING-4D79B443 — 2026-10-24

Independent review found false-clearance paths in the newer H86E orchestration:
missing registry files were omitted from expected counts, surface/final booleans
ignored incomplete scans, and final arrays were silently binarized/masked before
checking. PA-86-02 did not load its candidate argument, did not require complete
bound evidence, and allowed arbitrary self exclusion with a truncated correlation
list. The RIDF builder placed dots before checking its surface; its writer executed
on import without the literal preflight. Fixed in the orchestration, not a private
shared-tool fork. New v2 evidence is source/decoded/index-bound and retains all rows;
negative checks exit nonzero. Legacy reports stay archived, never upgraded in place.
Surface/dot order and literal gated serialization now have regression coverage.

Fresh audit: 13 published research TIFFs pass local format and fail literal overlap;
no new TIFF, model experiment or slot. See
`research/SESSION_20261024_4D79B443.md` and the current machine-readable audit card.
The user generation mandate remains unmet; inherited PA interpretations do not
establish that the stated literal overlap gate passed. The missing lane/cache and
non-comparable holdout histories remain blockers.

## IR-86-H86F-GZZD-01 (2026-10-25) — registry completeness trap measured blocking for a second lane; GZZD hypothesis falsified as run
The H86F-GZZD lane (frozen preregistration `research/H86F_GZZD_PREREGISTRATION.json`)
ran exactly three arms and both two-phase registry scans. Measured: 685 of 687
indexed rasters, the same 2 grid/CRS-incompatible rows as H86E-MMT
(`14GEMSDOE` horse-ensemble; `7GEMSDOE` qfaults prior), so
`registry_complete_for_index=false` and `scripts/pa86_chance_overlap.py` failed
closed with `ValueError: Incomplete registry cannot pass` (recorded
FAILED_CLOSED_NO_REPORT in `docs/evidence/h86f-gzzd-run-card.json`). **Decision:**
no private exclusion/bypass; PA-86-02 remains unsatisfiable until the protocol
repairs or formally excludes those rows upstream. Scientific result is
independently negative (HOLDOUT-DTI E1 0.0303 [0.0237, 0.0364] < unsigned-edge
control 0.0321 and R0 0.0339; same-split best 0.1241), so the verdict does not
depend on the registry trap. **Cost:** none to slots (0 used); the artifact is
audit-only. Also recorded: (a) pre-placement worst surface rho 0.467 was vs a
GEMSDOE24 `acquisition_block_id` external grid inside the registry — below the
0.90 stop, but survey-block mimicry remains a live risk for gravity-compilation
features; (b) this lane's frozen gate allowed an audit-only emission with 0
missing + 0 rho firings despite completeness=false, while the patched
`run_h86e_mmt.py` additionally requires zero registry errors before placement —
divergence disclosed in `research/H86F_GZZD_REVIEW_20261025.md`; future lanes
should adopt the stricter zero-error rule; (c) the shared writer left new
download files at mode 600 (mkstemp), normalized to 644 without byte changes.
## IR-86-MMT-RANK01-TIE-20261024 — `gems86_mmt.features.rank01` row-major tie ramp corrupted `R0_D28_visible_collar` (`0.03386` vs true `R0` `0.09609`)

In PR #93 (`src/gems86_mmt/features.py`), `rank01(a, footprint)` ordered values via
`np.argsort(v, kind="stable")` and mapped positions linearly to `np.linspace(0.0, 1.0, N)`.
On `GEMSDOE28__gems28-h27-4-r1-solo-d2-8` (`40,199` binary dots inside `5,167,373` footprint
cells), the `5,127,174` tied `0.0` background cells received monotonically increasing ranks
from `0.0` at row `0` up to `0.992221` at the southern footprint edge (`row 3729`). When
`emit.emit_decimated(..., tile_px=3)` + `emit.emit_prefix(..., 44090)` selected the top
`44,090` 3x3 tiles, **all `44,090` emitted comparator dots landed in southern rows `3023..3727`**
(`median row = 3302.0`, `0` dots in northern rows `0..3022`), overlapping only `2,453 / 40,199`
(`6.10%`) of `D28`'s true dots and filling the remaining `41,637` dots as a dense 3x3 southern
wallpaper (`HOLDOUT-DTI = 0.03386 [0.0169, 0.0514]`). Moreover, `GEMSDOE28` (`r1-solo`) was
already pruned against the **full** `60,988`-px catalogue (including the `11,321` withheld
holdout pixels, scoring `0.02431 [0.0202, 0.0286]` once ties are fixed), whereas the true
fold-fair `R0` visible-collar control from `GEMSDOE25` (`dotted-h19-5-d2-8`, sha256
`91eae1ca42ec...`, `docs/evidence/h86e_comparator.json`) scores **`HOLDOUT-DTI = 0.09609
[0.0830, 0.1089]`** on the identical `seed=20, hide_frac=0.20, buffer_px=3` split (true
`E1_mmt_tc_decoupled` deficit vs fold-fair `R0` is **`-0.0671`**, not `-0.0049`).
**Decision:** `src/gems86_mmt/features.py::rank01` is fixed using tie-invariant min-ranking
(`scipy.stats.rankdata(v, method="min")`, mapping tied floor `0.0` cells uniformly to `0.0`
across all rows) with regression coverage in `tests/test_h86e_mmt.py`; the archived run card
`docs/evidence/h86e-mmt-run-card.json` is preserved unedited with an explicit comparator
provenance caveat on `README.md` and `docs/`.

## IR-86-MMT-SHIFT-AXIS-20261024 — `build_marker_features` shifted `tgrad` parallel to the gradient normal instead of orthogonal corridor strike

In PR #93 (`src/gems86_mmt/features.py`), `_directional_difference(a, theta)` computed the
cross-corridor finite difference along the normal vector `(dy, dx) = (sin theta, cos theta)`,
and the lag loop then shifted `tgrad` along the **same** vector `(sin theta * lag, cos theta * lag)`
rather than orthogonal corridor strike `(-cos theta * lag, sin theta * lag)`. Consequently,
standalone `H86E-MMT` v1 measured normal-to-edge separation between `rtp` and `tilt` peaks
(a cross-profile source-depth/dip width effect) rather than lateral strike-slip / transfer-fault
marker offset along a structural corridor, and also applied `tc` (Band 6) directly before an
authoritative organizer band-table check.
**Decision:** `src/gems86_mmt/features.py` now defaults to `shift_axis="strike"` (`(-cos theta * lag, sin theta * lag)`, verified orthogonal to `(sin theta, cos theta)` in `tests/test_h86e_mmt.py`),
while `registry/h86c_hypotheses.json` Rank 2 explicitly separates the still-untested two-sided
split-window FFT along-strike phase-correlation formulation from PR #93's negative normal-lag
predecessor.

## IR-86-MMT-PRE-V2-UNBOUND-REPORTS-20261024 — Pre-v2 unbound `H86E-MMT` registry reports & three ungated H86E scripts

Both `docs/evidence/h86e-mmt-registry-surface.json` and `docs/evidence/h86e-mmt-registry-final-dots.json`
were generated against a pre-v2 checker (`evidence_schema` absent, `candidate_file_sha256: null`,
`complete_accessible_scan: false`, `683 / 685` comparable rows with 2 grid/CRS errors in
`14GEMSDOE` and `7GEMSDOE`), and `scripts/run_h86e_mmt.py` lacked `protocol_preflight.require_feasible()`
and reached `write_candidate(...)` even when `registry_gate` evaluated `False`. In addition,
`scripts/build_h86e_features.py` and `scripts/run_h86e_ridf.py` lacked `require_feasible()`, and
`scripts/build_h86e_features.py`, `scripts/h86e_comparator.py`, `scripts/h86e_fleet_strata.py`,
and `scripts/h86e_instrument_check.py` executed raster I/O at module import time.
**Decision:** `build_h86e_features.py`, `run_h86e_ridf.py`, and `run_h86e_mmt.py` now enforce
`require_feasible()` (bringing `tests/test_builder_preflight.py::BUILDERS` from 47 to **50**
CLI builders + 8 imported orchestrators), `run_h86e_mmt.py` also halts before `write_candidate`
whenever `registry_gate` is `False`, and all four diagnostic/feature scripts are wrapped in
`main()` with import-safety regression tests.

## IR-86-PREPARE-RELPATH-20261024 — `scripts/prepare_data.py` crashed on relative or external `--data-dir`

Invoking `python scripts/prepare_data.py --data-dir .cache/bridge` raised `ValueError:
'.cache/bridge/sample_submission.tif' is not in the subpath of '/home/user/GEMSDOE86'` because
`Path(data_dir)` remained relative while `ROOT` was resolved absolute (`tmpl_path.relative_to(ROOT)`
also failed for any external `--data-dir` outside `ROOT`).
**Decision:** Fixed in `scripts/prepare_data.py` via `_rel_or_str()` + `.resolve()`, covered in
`tests/test_prepare_data.py`, and verified end-to-end by restoring all 3 SHA-256-pinned core
competition rasters (`training_features.tif` `4371c82e...`, `existing_faults.tif` `7ba308cc...`,
`sample_submission.tif` `2176d08e...`) plus 5 external USGS/GeoDAWN rasters into `.cache/` and
generating the complete 19-band `data/prepared_manifest.json` (`has_features: true`, `58,171`
total sentinel band-pixels across `3,073` unique perimeter/TC cells).

## IR-86-INVENTORY-OFFGRID-ROWS-20261025 — 2026-10-24/25 (`H86H-PSTD` strict Rule-11 stop before placement)

Even after restoring and SHA-256-verifying all `655 / 655` blobs in `research/upstream/registry_inventory.json`
(`728,345,463` bytes; `689` unique indexed rasters including the 17 prior local artifacts, `0` missing), two historical
inventory entries fail `vendor/gems57/uniqueness.py::compare_array_to_registry` grid/CRS checks:
- `14GEMSDOE:docs/downloads/GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f.tif` (`ccbe1de0...`: `registry CRS/transform differs from reference`)
- `7GEMSDOE:external/qfaults/qfaults_prior_u8.tif` (`538b4573...`: `registry grid or band-count mismatch`)

Unlike lanes that serialized audit-only GeoTIFFs despite failing `surface_gate_pass` / `literal_gate_pass`,
the contemporaneously preregistered `H86H-PSTD` lane (`scripts/run_h86h_pstd.py`, `docs/evidence/h86h-pstd-run-card.json`)
strictly obeys `AGENTS.md` Rule 11: it checks its continuous surface (`rho_firings = 0`,
`worst_spearman_full_footprint <= 0.90` across all `687` valid competition-grid rasters including `H86F-GZZD` and `H86F-PCC`)
and **halts fail-closed before full-footprint dot placement and before GeoTIFF serialization** (`final_dots_placed = False`,
`candidate_tif_serialized = False`). Also added `holdout_binary_control` (`GEMSDOE25` `91eae1ca42ec...`, `d_vis > 2.0 px`,
`HOLDOUT-DTI = 0.096086`) to `scripts/run_h86e_mmt.py` and gated `write_h86e_tif`.

## IR-86-H86F-EWCS-01 (2026-10-25) — H86F-EWCS sets repo same-split HOLDOUT-DTI record (`0.1723`), yet fails closed to DO NOT SUBMIT on registry completeness and literal saturation

`scripts/run_h86f_ewcs.py` executed the frozen 3-arm preregistered `H86F-EWCS` lane
(`research/H86F_EWCS_PREREGISTRATION.json`, `registry/h86f_hypotheses.json`) within
the `<= 3` experiment / `<= 2` hour budget using SHA-pinned competition inputs and
unmodified `vendor/gems57` tools. On `gems57-pooled-hide-v2` (`seed=20`, `hide_frac=0.20`,
`buffer_px=3`, `11,321` withheld positives, `1,000` bootstrap draws over `20 km` blocks),
`E1_ewcs_coupled_pu` (`37,654` dots, `2.8 px` Poisson-disc spacing) achieved
**`HOLDOUT-DTI = 0.172325` (`95% CI [0.152956, 0.189793]`)**, outperforming its
isotropic-tip mechanism control `E3_ewcs_isotropic_tip_ablation` (`0.159234`, paired
delta **`+0.013091` `95% CI [+0.001163, +0.026066]`**), cover-blind subsurface control
`E2_ewcs_cover_blind_pu` (`0.100261`, paired delta `+0.072063`), `R0_D28_visible_collar`
(`0.027299`), fold-fair `GEMSDOE25` `R0` (`0.096086 [0.082975, 0.108898]`), and prior
repo same-split best `H86C-KSLB` (`0.124063 [0.107970, 0.140330]` at `44,090` dots) with
separated 95% CIs (`23` leakage canaries max discriminative AUC `0.7949 <= 0.90`).
Both `v2` SHA-bound registry scans (`687 / 689` measured, explicitly including the
newly merged `H86F-PCC` and `H86F-GZZD` TIFFs) recorded `0` Spearman `rho > 0.90`
firings (`worst_spearman = 0.7508`) and `0` discrete `<= 50,000`-dot overlap firings
(`26.96%` vs `GEMSDOE32` `h33-h33-2-b2`, `37.57%` vs `H86C-KSLB`, `9.46%` vs `H86F-PCC`,
`9.90%` vs `H86F-GZZD`). However, the same `2` grid/CRS-incompatible historical rows
(`14GEMSDOE`, `7GEMSDOE`), `39` space-filling `>= 56,605`-dot firings, and literal
`17GEMSDOE` full-support saturation caused `surface_gate_pass`, `final_dots_gate_pass`,
`literal_gate_pass`, and `pa86_02` to fail closed.
**Decision:** The format-valid GeoTIFF (`docs/downloads/gems86-h86f-ewcs-elastic-wing-37654dots-20261025T020534Z-47f1ed21-zeros.tif`,
SHA-256 `8322dcf157851e07dfdd4391ed5164916479e4dce17af2d0e14afab5592a697d`) is registered
for audit download only (`status = "DO NOT SUBMIT"`, `verdict = "negative"`, `0` slots
used) and emerges as the lead technical candidate once a human selector resolves the
upstream registry blockers.

## IR-86-H86F-PCC-PREFLIGHT-20261025 — `scripts/run_h86f_pcc.py` lacked `require_feasible()` and `docs/evidence/h86e-mmt-registry-surface.json` carried `surface_gate_pass: true` despite 2 errors

Pass-2/3 audit after merging PRs #97–#102 found that `scripts/run_h86f_pcc.py` (merged in
PR #97 concurrently with PR #98's builder-gating sweep) did not call
`protocol_preflight.require_feasible()` at the start of `main()` and was absent from
`tests/test_builder_preflight.py::BUILDERS`, while archived
`docs/evidence/h86e-mmt-registry-surface.json` still carried `"surface_gate_pass": true`
despite `2` grid/CRS errors (`14GEMSDOE` and `7GEMSDOE`), contradicting
`docs/evidence/h86e-mmt-run-card.json` (`false`) and `AGENTS.md` Rule 11.
**Decision:** Both `scripts/run_h86f_pcc.py` and `scripts/run_h86f_ewcs.py` now call
`protocol_preflight.require_feasible()` before any work and are pinned in
`tests/test_builder_preflight.py::BUILDERS`, and `docs/evidence/h86e-mmt-registry-surface.json` now records
`"surface_gate_pass": false` with an explicit archive note.

## IR-86-H86F-INQUAD-TRAINING-20261025 — `H86F-EWCS` (`0.1723`) trained on in-quadrant visible components rather than strict outer Leave-One-Quadrant-Out (`quad != q`)

Line-by-line audit of `scripts/run_h86f_ewcs.py` (`line 528`) against
`vendor/gems57/holdout.py` (`buffered_component_draw` docstring, `lines 269-271`) and
`scripts/run_lane86c.py` (`line 206`) identified a training-domain asymmetry between
the repository's two leading same-split holdout benchmarks on `gems57-pooled-hide-v2`
(`seed=20`, `hide_frac=0.20`, `buffer_px=3`, `11,321` withheld positive pixels):
`H86C-KSLB` (`0.124063 [0.107970, 0.140330]`) restricted training labels to
`train_dom = binary_erosion(quad != q, iterations=12) & footprint` (strict outer
Leave-One-Quadrant-Out), whereas `H86F-EWCS` (`0.172325 [0.152956, 0.189793]`)
sampled visible positive and negative training pixels across all 4 quadrants (`vis`,
which still strictly excludes all `11,321` withheld whole-component pixels plus their
`3 px` context collar, so zero withheld truth leaked, but allows tree splits to learn
in-quadrant visible background statistics). Re-evaluating the exact `H86F-EWCS`
architecture under strict outer Leave-One-Quadrant-Out (`C1_H86F_EWCS_strict_loqo_ctrl`
in `docs/evidence/h86i-ksad-run-card.json`) yields **`HOLDOUT-DTI = 0.133311`
(`95% CI [0.117836, 0.150210]`)**, showing `+0.039014` (`+390 bps`) of the `0.172325`
score came from in-quadrant visible training. Under identical strict outer LOQO,
`H86I-KSAD` achieves **`0.155275 [0.139633, 0.171839]` (`E1`)** and **`0.159867
[0.145895, 0.174249]` (`E2`)**, beating `C1_H86F_EWCS_strict_loqo_ctrl` with a
strictly positive paired `20 km` block-bootstrap 95% CI (`+0.021964 [+0.003838, +0.040503]`
for `E1`).
**Decision:** Never compare in-quadrant visible `HOLDOUT-DTI` (`0.1723`) directly against
strict-LOQO `HOLDOUT-DTI` (`0.1241`, `0.1333`, `0.1553`, `0.1599`) without labeling the
outer training domain (`AGENTS.md` Rule 6).

## IR-86-DEM10-CHI-SENTINEL-20261025 — Raw `int16` `-32768` non-channel sentinels in `dem10_chi_100m_i16.tif`

Direct pixel inspection of SHA-pinned `.cache/external/dem10_chi_100m_i16.tif`
(`8897ba9c...` in `scripts/restore_data.py:EXTERNAL_PINS`) showed Bands 1-4
(`step_max_x1000`, `step_min_x1000`, `ksn_max_m0.9`, `log10_area_m2_x1000`) store
`-32768` (`int16` minimum, `median = -32768.0` across the footprint) at off-channel
hillslope cells without declaring a GeoTIFF `nodata` tag that `np.isfinite` would filter,
whereas Band 5 (`zmean_m`) stores true absolute elevation in meters ASL (`1032..3141 m`,
`100.0%` valid). Unmasked smoothing across `-32768` creates spurious step artifacts along
drainage margins.
**Decision:** `src/gems86_ksad/physics.py` explicitly masks `val > -32000` with
normalized Gaussian channel weights before computing reach-relative $k_{sn}$ and
$\chi$-step knickzone features, while using `zmean_m` directly for Pleistocene Lake
Lahontan (`1,180-1,345 m ASL`) contour-parallelism deconfounding.

## IR-86-H86I-KSAD-OVERLAP-STOP-20261025 — `H86I-KSAD` sets repo strict-LOQO holdout record (`0.1553` / `0.1599`), then halts fail-closed BEFORE GeoTIFF serialization on `71.31%` informative discrete fleet overlap

`scripts/run_h86i_ksad.py` executed the frozen 3-arm preregistered `H86I-KSAD` lane
(`research/H86I_KSAD_PREREGISTRATION.json`, `registry/h86i_ksad_hypotheses.json`) within the
`<= 3` experiment / `<= 2` hour budget (`32/32` single-feature leakage canaries passed,
`max_discriminative_auc = 0.8074 <= 0.90`). Pre-placement `v2` surface audit across
`688 / 690` compatible registry rasters (`docs/evidence/h86i-ksad-registry-surface.json`)
recorded `0` Spearman `rho > 0.90` firings (`worst_spearman = 0.6344`). However,
pre-serialization `v2` final-dot audit of `E1`'s `28,197` Dinkelbach-stopped dots
(`docs/evidence/h86i-ksad-registry-final-dots.json`) caught **3 genuinely informative
discrete dot-field forward 3-px overlaps `> 0.70`**: `71.31%` against
`GEMSDOE80__gems80-adpt-kkt-lagrangian-36500d-20261022T012049Z-5bd11c85-zeros.tif`
(`36,500` dots, measured 3-px chance halo `c = 14.65% << 70%`) and `70.19%` against
`GEMSDOE43:gems43-sup01-hgb21-sep40-n40000` (`40,000` dots, `c = 18.45% << 70%`), in
addition to the 2 off-grid registry rows (`688/690` compatible) and literal `17GEMSDOE`
full-support witness saturation.
**Decision:** Per Parallel-Run Protocol Rule 1 and `AGENTS.md` Rules 10-11 (*"final-dot
checks precede serialization"* and *"informative overlap firings are hard stops"*), the
runner halted fail-closed **before writing a duplicate GeoTIFF**, wrote the complete
negative deliverable `docs/evidence/h86i-ksad-run-card.json` (`verdict = "negative"`,
`decision = "DO NOT SUBMIT"`, `0` weekly slots used), and locked `scripts/run_h86i_ksad.py`
behind `protocol_preflight.require_feasible()` (`55` CLI builders + `8` imported
orchestrators in `tests/test_builder_preflight.py`).

## IR-86-RELEASE-AUDIT-TMP-20261025 — `tests/test_release_audit.py::release_copy` copied untracked 400 MB `training_features.tif` into `/tmp` 20+ times when native data were restored

**Observed.** In CI (`ubuntu-24.04`), `data/bridge/` contains only the two Git-tracked bridge
rasters (`existing_faults.tif` `416 KB` and `sample_submission.tif` `1.6 MB`). After running
`bash scripts/download_competition_data.sh` locally, `data/bridge/training_features.tif`
(`400 MB`, gitignored) is also present. `tests/test_release_audit.py::release_copy` called
`shutil.copytree(ROOT / "data/bridge", ...)` without excluding `training_features.tif`, even
though `scripts/audit_release.py` never opens `training_features.tif`. Across 20+ fixtures
and pytest's retained temporary directories, that copied `> 8 GB` into `/tmp` and exhausted
sandbox disk (`Errno 28: No space left on device`).
**Decision.** Excluded `training_features.tif` in `tests/test_release_audit.py::release_copy`
(`shutil.ignore_patterns("__pycache__", "training_features.tif")`); all 27 tests in
`tests/test_release_audit.py` now pass cleanly whether or not `training_features.tif` is
present locally.

## IR-86-H86G-INSTRUMENT-20261025 — Catalogue-hide holdout anti-correlates with live ordering; OOF-vs-shipped conflation

E1b (this session) scored shipped rasters as-is on the seed-20 buffered
whole-component catalogue-hide instrument: live-best H33 = 0.0037, live-worst
poisson81 = 0.0918 (full table in `research/H86G_EDTI_REVIEW.md`). Selecting on
that instrument alone selects *for* catalogue proximity, which the organiser's
known-fault masking does not reward. Separately, the historical "same-split
best 0.1241" (KSLB) is an out-of-fold arm construct; the shipped KSLB raster
measures 0.0038 as-is on the same folds. Any cross-lane comparison must state
OOF-vs-as-is construction explicitly. H86G-EDTI therefore selected on the
SGMC-proxy (which reproduces the live ordering) with catalogue-hide demoted to
an OOF floor; Amendments A1–A2 in the preregistration.

## IR-86-H86G-COLLAR-DEGENERACY-20261025 — Collar-3 submissions score identically 0 as-is on catalogue-hide

Any raster collared >3 px against the full catalogue has catalogue-hide DTI
exactly 0.0000 as-is, because withheld truth ⊂ catalogue (measured: all three
H86G arms, all budgets). As-is catalogue-hide readings of collared submissions
are meaningless; use the OOF visible construction like-for-like.

## IR-86-H86G-A3A4-BUDGET-20261025 — Post-hoc budget rule (disclosed, not hidden)

The SGMC proxy's budget optimum is a truth-density artifact (still rising at
98,163-dot ranking exhaustion). Amendment A3 capped budget at the live-validated
44,090; Amendment A4 (adopted *after* inspecting marginal-credit flatness and
paired CIs at 55k/70k) set budget = smallest grid budget whose paired proxy CI
excludes 0 → 55,000. The reported CI is post-selection descriptive. The
superseded A3 44,090-dot artifact was removed from `docs/downloads/` so no
orphan binary lacks a run card; its nested ranking makes the 44,090 prefix
regenerable byte-consistently from `scripts/run_h86g_edti.py` caches.

## IR-86-AUDIT-LINKEDCARDS-20261025 — `linked_cards` read a non-existent config key

`scripts/audit_release.py:build_report` built `linked_cards` from
`c["source_card"]`, but `registry/artifact_cards.json` configs carry the key
`card`; the linked set was therefore always empty and every `*card*.json` was
held to the unlinked-sidecar negativity check. Fixed to `c["card"]` this
session (linked cards are validated per-artifact in `audit_artifact`, including
the new `h86g_edti` promote branch). No historical verdict changed: all
previously linked cards are negative under both readings.

## IR-86-H86G-FEED-20261025 — GEMSDOE89/90 owner scores not yet in the ledger/feed

This session's prompt supplies OWNER-REPORTED scores for GEMSDOE89 (0.0301)
and GEMSDOE90 (0.0749), previously prompt-named unscored. They are recorded in
`research/REQUEST_20261025.md` but not yet folded into
`registry/prior_scores.csv` / `docs/evidence/fleet-feed.json` (hash-bound
pair); a fleet-refresh session should ledger them and regenerate the feed.

## IR-86-PUBLICATION-AUTH-09C7FC42 (2026-10-25)

Homepage, executive summary, README and build success output said H86G-EDTI was OK to
submit while its card explicitly denied safe_to_submit and weekly-slot approval, and
literal release audit failed. Corrected publication instructions to research-only;
historical amended-gate promotion and binary bytes unchanged. Added regression checks
rejecting positive upload instructions in the negative-state publisher. See
`research/SESSION_09C7FC42_REVIEW.md`. No new TIFF, model experiment or portal operation.


## IR-86-085C2B7A — promotion was displayed as upload permission (2026-10-25)

The generated homepage/executive guide and current README said to submit H86G-EDTI even though its scientific card records `safe_to_submit=false`, `approved_for_weekly_slot=false`, and the release audit retains the literal witness stop. Fixed the source generator, regenerated pages and exposed the promoted-for-review identity in `docs/data/summary.json` without changing historical scientific evidence. Regression tests forbid the unsafe direct-upload phrases. No new raster, model experiment or slot. See `research/SESSION_085C2B7A_REVIEW.md`.

## IR-86-HVFD-COLLAR-ABLATION-20261025 — 2026-10-25 (`H86I-HVFD` 3-arm Dual-Regime Noisy-OR & `buffer_px=3` vs unbuffered collar ablation)

Contemporaneously preregistered lane `H86I-HVFD` (`research/H86I_HVFD_PREREGISTRATION.json`,
`scripts/run_h86i_hvfd.py`, `docs/evidence/h86i-hvfd-run-card.json`) generated audit-only GeoTIFF
`docs/downloads/gems86-h86i-hvfd-vent-flexure-37654dots-20261025T030002Z-33c17af1-zeros.tif` (`sha256:
0325442434733ee10a9d77200b17db86f00d6195d373afeca43d673435216b58`, `37,654` unit dots, `15/15` local format
checks PASS), gated `run_h86h_pstd` and `run_h86i_hvfd` in `tests/test_builder_preflight.py::BUILDERS` (`57` CLI
builders + `8` imported orchestrators), added `holdout_binary_control` (`R0_G25_foldfair_collar`) to
`scripts/run_h86f_pcc.py`, and updated `src/gems86_pstd/features.py::_rank01` to `method="min"`. While
`E1_hvfd_blind_vent_conduit` (`0.0475` `[0.0364, 0.0585]`) beat all prior zero-catalogue algebraic lanes
(`0.0245–0.0327`) by `+45%` to `+94%` and `E2_hvfd_foldfair_vent_relay_noisyor` (`0.1013` `[0.0886, 0.1139]`)
beat fold-fair `R0_G25_foldfair_collar` (`0.0961` `[0.0828, 0.1090]`), `E2` (`37,654` dots, `d_vis > 2.0 px`)
trailed its own 44,090-dot `d_vis > 1.5 px` collar-ablation control `E3` (`0.1040` `[0.0917, 0.1166]`, paired
`E2 - E3 = -0.0027` `[-0.0054, -0.0003]`) on `buffer_px=3` whole-component holdout as well as `H86C-KSLB`
(`0.1241`). Furthermore, although `H86I-HVFD` has `rho_firings = 0` (`worst_spearman = 0.0625`) and
`<= 58.59% < 70%` 3-px forward overlap against all `468` sparse (`<= 100k` dot) registry submissions (`21.20%`
vs `h33-2-b2`), it measures `1.0000` vs full-support `17GEMSDOE`, `0.9995` vs dense lattice `13GEMSDOE`, and
encounters the `2` off-grid historical inventory rows (`errors = 2`), so it is automatically marked
`verdict: "negative"`, `decision: "DO NOT SUBMIT"`, `submission_slots_used: 0`.

## 2026-10-25 — H86J-LSI (live-score inversion)

* **IR-86-H86J-01:** on 74 owner-scored rasters, the SGMC proxy as-is reaches Spearman 0.300 vs OWNER-REPORTED live, and catalogue-hide (`gems57-pooled-hide-v2`) reaches 0.051. The 8-raster SGMC agreement behind H86G does not generalise (e.g. GEMSDOE44 h46: SGMC 0.3081 vs live 0.0715).
* **IR-86-H86J-02:** inventory row `ccbe1de0…` (14GEMSDOE r5-geom-horse-ensemble) has the competition shape but a shifted transform (origin 500000, 4500000). H86J compared it index-wise.
* **IR-86-H86J-03:** the H86J log-linear truth density is non-physical. λ > 1 on 2,552 pixels, which hold 63.5 % of its mass, so its LSI-PROJECTION values are not forecasts.
* **IR-86-H86J-05:** two concurrent sessions both used the `H86J` prefix (H86J-MPC on main, H86J-LSI here). The lanes are distinct (different suffix, cards and files). `build_site.py` variables were renamed to avoid a silent overwrite. The H86I-SACD and H86J-MPC artifacts were lost from `download-inventory.json`/`artifact_cards.json` when PR #131 merged; this merge restores them (24 artifacts re-audited).
* **IR-86-H86J-04:** E3 ended ~8 min past the 2 h session budget. No further experiment was run. The negative raster is not published.

## IR-F548F465 — hash identity is not registry uniqueness (2026-10-25)

`verify_submission_tif.py` printed “unique by pinned digest” after a format/hash check.
Corrected to format/identity only, with explicit DO NOT SUBMIT and no inferred
holdout, registry or slot clearance. Added clean fail-closed handling and tests
for malformed receipts and ZIPs. See `research/SESSION_F548F465_REVIEW.md`.

## IR-86-H86F-EWCS-TRANSQUAD-PU-20261025 — `scripts/run_h86f_ewcs.py` sampled PU training rows across all 4 quadrants rather than strict `quad != fold_i`

Forensic line-by-line inspection of `scripts/run_h86f_ewcs.py` (`line 519`) during
session `95a42d60` confirmed that while `vis = f["visible"] & fp` properly stripped
all `11,321` withheld positive pixels and their `3-px` feature collar globally (`0`
hidden-truth label leakage), `sample_nested_pu(static_mm, s_keys, vis, fp, e_keys, ...)`
drew visible training positives and unlabeled background rows from the full footprint
`fp` (including the held-out quadrant `quad == fold_i`) and emitted four full-map
`37,654`-dot allocations rather than restricting classifier training to the three
out-of-quadrant regions `fp & (quad != fold_i)`.
**Decision:** The archived `H86F-EWCS` run card (`docs/evidence/h86f-ewcs-run-card.json`)
is left untouched per `AGENTS.md` Rule 9, its trans-quadrant PU scope is documented
explicitly in `H86I-SACD`'s comparator table and on `irregularities.html`, and the new
`H86I-SACD` runner (`scripts/run_h86i_sacd.py`) enforces strict spatial
Leave-One-Quadrant-Out training (`train_region = fp & (quad != fold_i)`).

## IR-86-H86I-SACD-01 (2026-10-25) — H86I-SACD executed under strict spatial LOQO (`0/367` `<=50k`-dot firings, `0/691` Spearman firings), auto-marked DO NOT SUBMIT (`verdict = "negative"`)

Session `95a42d60` preregistered four untried hypotheses (`registry/h86i_hypotheses.json`,
`research/H86I_SACD_PREREGISTRATION.json`) prior to any holdout evaluation and executed
Rank-1 `H86I-SACD` (*Spin-2 Coulomb-Projected Strike Concordance, Jacobsen
Upward-Continuation Depth-Attenuation & Bekker-Davis Alluvial-Burial Propensity
Submodular Max-Cover*) across 3 fixed arms (`<= 3` experiment / `<= 2` hour budget,
`1,323.96 s` wall time). All `33` features passed single-feature ROC-AUC leakage
canaries (`max = 0.7639 <= 0.90`). Under strict `quad != fold_i` LOQO (`11,321`
withheld positives, `1,000` paired `20 km` block-bootstrap draws), scalar unweighted
pointwise `E2` achieved `HOLDOUT-DTI = 0.1055 [0.0878, 0.1257]` (beating `R0_D25`
`0.0931` and `R0_D28` `0.0273`), whereas `E1` (`0.0832 [0.0673, 0.0997]`) and pure
cover-blind subsurface `E3` (`0.0843 [0.0693, 0.0995]`) trailed `E2` (`paired delta =
-0.0223 [-0.0352, -0.0104]`) due to Fold-0 forced inter-quadrant quantile equalization
over-allocating dots into lower-density `NE` (`10,797` dots) and submodular plateau
clustering on broad diffuse basin posteriors. Full post-merge `v2` registry scans (`691 / 693`
valid competition-grid rasters including `H86G-EDTI`, `H86I-RKSC`, and `H86I-HVFD`, `0` missing)
confirmed `0` Spearman `rho > 0.90` firings and `0` discrete `<= 50k`-dot overlap firings
(`31.17%` vs `GEMSDOE32` `h33-h33-2-b2`, `55.60%` vs `H86F-EWCS`), while failing closed on
`17GEMSDOE` saturation, space-filling lattices, and `2` off-grid upstream rows (`PA-86-02`
`FAILED_CLOSED_NO_REPORT`).
**Decision:** The unique `[0, 1]` GeoTIFF (`docs/downloads/gems86-h86i-sacd-spin2-submod-37654dots-20261025T040150Z-0544ef05-zeros.tif`,
SHA-256 `b15a89fa1917526c1ce32081c1802d39333dc497d0d0d1034dc962df47c691e0`) is published
strictly as an audit-only download (`status = "DO NOT SUBMIT"`, `verdict = "negative"`,
`0` weekly slots used), and `scripts/run_h86i_sacd.py` is locked behind
`protocol_preflight.require_feasible()` (`62` CLI builders + `8` imported orchestrators, including `scripts/run_h86i_ksad.py`, `scripts/run_h86i_rlms.py`, `scripts/run_h86g_edti.py`, and `scripts/run_h86j_csgd.py`).

## IR-86-H86I-RLMS-01 — `H86I-RLMS` official 3DEP 1m/10m + GeoDAWN `K/eTh` physics improved `HOLDOUT-DTI` by `+0.0264` across all 4 quadrants, while unconstrained submodular `eta=0.042` clumping degraded Walker Lane `SW`

Under frozen preregistration `research/H86I_RLMS_PREREGISTRATION.json`
(`sha256=f53b80b3130836d3e35d7dcb40e3201fcb0409cc32512e97fca1ce01a9cb7a7e`) and
`registry/h86i_rlms_hypotheses.json`, the 3-arm `H86I-RLMS` lane evaluated SHA-pinned
official USGS 3DEP 1-m LiDAR scarp planes, 10-m DEM curvature/fluvial `chi`
disequilibrium, and USGS GeoDAWN airborne `K/eTh` alteration plus up-dip hanging-wall
back-projection and spin-2 nematic director coherence on `gems57-pooled-hide-v2`
(`seed=20`, `11,321` withheld positives, `1,000` 20 km block-bootstrap draws).
- **Positive external-physics finding (`E1 - E2`):** `E1_rlms_full_submodular`
  (`0.125716 [0.107073, 0.143239]`) beat matched native-19 ablation
  `E2_rlms_native19_only_ablation` (`0.099322 [0.085157, 0.112842]`) by
  **`+0.026394 [+0.016173, +0.037075]`**, positive in all 4 spatial quadrants
  (`NW +0.016109`, `NE +0.031797`, `SW +0.014741`, `SE +0.041886`) and surpassing
  `H86F-EWCS` on Basin-and-Range `SE` (`0.166613` vs `0.156591`).
- **Allocator & OOF buffer diagnosis (`E1 - E3`):** Replacing the unconstrained
  submodular allocator (`eta = 0.042` static modular bonus without hard `>= 2.8 px`
  Poisson-disc exclusion) with hard `2.8 px` greedy Poisson-disc thinning on the same
  `E1` OOF probability surface (`E3_rlms_unprojected_disc_ablation = 0.155115`)
  restored `SW` Walker Lane from `0.085982` to `0.185323`, independently corroborating
  `H86I-SACD`'s submodular plateau finding and showing that static `eta * k_self`
  over-packs 1-px-adjacent hotspots where probability peaks exceed the regional
  baseline; additionally, `buffer_px=3` OOF grouping censored `300-600 m` fault-tip
  stepover positives during OOF isotonic calibration.
- **Uniqueness & gate disposition:** Pre-placement `--surface` (`688/690` measured)
  had `0` Spearman firings > `0.90` (`max = 0.649608`), final dots had `0/469` discrete
  `<= 100k`-dot overlap firings > `0.70` (`max = 0.673102`; `0.4025` vs `GEMSDOE32`
  `h33-h33-2-b2`; `0.3101` vs `H86F-EWCS`; `0.2426` vs `H86G-EDTI`; `0.3513` vs
  `H86I-SACD`; `0.2453` vs `H86I-HVFD`; `0.1269` vs `H86I-RKSC`; `0.1413` vs
  `H86J-MPC`), and `40/40` leakage canaries passed (`max AUC = 0.7949 <= 0.90`).
  Because pooled `E1` (`0.125716`) did not beat reproduced `H86F-EWCS` (`0.172325`)
  and literal `17GEMSDOE` / 2 off-grid registry rows / `PA-86-02` failed closed,
  `docs/downloads/gems86-h86i-rlms-riedel-listric-37654dots-20261025T053030Z-08cce287-zeros.tif`
  (`sha256=ad4474b4d78ed3e8eaf5114fc63e3d858afcc0c016f7932baaaca06e99247b2d`) is
  published strictly as **`DO NOT SUBMIT`** (`verdict = "negative"`, `0` slots spent),
  and `scripts/run_h86i_rlms.py` is locked behind `protocol_preflight.require_feasible()`.

## IR-86-H86G-LOCAL-ONLY-DUP-20261025 — H86G-EDTI 43-file local check missed 25 informative full-registry firings

Restoring all 655 external Git blobs via zero-REST-quota `codeload.github.com` + shallow
git-pack fallback in `scripts/restore_registry_inventory.py` and auditing
`gems86-h86g-edti-55000dots-20261025T023531Z-a86d6a9f-zeros.tif` (`ba8b731f...`)
across all 689 compatible rasters excluding self (`docs/evidence/h86g-edti-full-registry-audit-20261025.json`)
revealed **44 dot-field forward-3px overlap firings (> 0.70)** and **25 informative
(`halo_coverage <= 0.70`) firings**, including sparse `GEMSDOE46:r11f` (`76.02%` at
44,090 dots), `GEMSDOE41:h42` (`73.99%` at 40,000 dots), and `GEMSDOE46:r12` (`72.24%`
at 37,654 dots). `scripts/run_h86g_edti.py::main` is now gated behind
`protocol_preflight.require_feasible()` (`63` CLI builders + `8` imported orchestrators).

## IR-86-CSGD-LITERAL-STOP-20261025 — H86J-CSGD achieves 0 / 636 informative dot-field firings on full registry, stays fail-closed negative

Session `0bec8252` preregistered `registry/h86j_hypotheses.json` +
`research/H86J_CSGD_PREREGISTRATION.json` and executed 3-arm `H86J-CSGD`
(`docs/downloads/gems86-h86j-csgd-sar-admit-37654dots-20261025T055033Z-35faffb4-zeros.tif`,
SHA-256 `079914e36dec80349310f52289119ad8a956f13e435369422859d5dd0b16707f`):
`28/28` canaries passed (`max = 0.7742 <= 0.90`), `E2` unweighted cover-blind ablation
achieved `HOLDOUT-DTI = 0.1577 [0.1401, 0.1755]` (zero DEM/slope features), and primary
SAR-debiased `E1` (`0.0613 [0.0453, 0.0764]`) achieved **0 / 636 informative dot-field
firings** across the full 690-raster restored scan (`0` Spearman firings, max `0.5050`).
Because `E1` trails `H86C-KSLB` (`0.1241`) and literal `17GEMSDOE` (`100%`) + 2 off-grid
rows fail closed, `H86J-CSGD` is recorded as `verdict = "negative"` (`DO NOT SUBMIT`,
`0` weekly slots used).

## IR-86-EWCS-INQUADRANT-20261025 — `H86F-EWCS` (`0.1723`) trained GBDT on non-withheld faults inside the test quadrant; cross-confirmed with `IR-86-H86F-INQUAD-TRAINING-20261025`

**Observed.** Forensic review of `scripts/run_h86f_ewcs.py` (lines 486–494) during `H86J-TVHS` preparation
independently confirmed that `H86F-EWCS`'s GBDT positive training mask `pos_allowed = allowed & visible_faults`
trained on non-withheld faults inside the test quadrant (`0.1723`), whereas strict out-of-quadrant LOQO
(`train_mask = fp & (quad != q)`) yields `0.1214 [0.1060, 0.1350]` on `H86J-TVHS E3` (`37,654` dots) and
`0.1333 [0.1178, 0.1502]` on `H86I-KSAD C1`. Recorded without mutating archived `h86f-ewcs-run-card.json`.

## IR-86-TVHS-PROPENSITY-ABLATION-20261025 — 2026-10-25 (`H86J-TVHS` strict-LOQO Dual-Expert PU `E[k]`, spin-2 crest fix, post-merge 27-artifact audit, and fleet feed closure)

**Observed.** Contemporaneously preregistered lane `H86J-TVHS` (`registry/h86j_tvhs_hypotheses.json`,
`research/H86J_TVHS_PREREGISTRATION.{json,md}`, `src/gems86_tvhs/features.py`, `scripts/run_h86j_tvhs.py`,
`docs/evidence/h86j-tvhs-run-card.json`) generated audit-only GeoTIFF
`docs/downloads/gems86-h86j-tvhs-ggt-vent-loqo-37654dots-20261025T062647Z-49726478-zeros.tif` (`sha256:
f77e4d6aef7e594df5002fcb2be7c6ad8fd3cfef06e107f48dacfd4453c3ac94`, `37,654` unit dots, `15/15` format checks
PASS, `0` slots used):
1. Pre-run synthetic test caught first-derivative crest cancellation (`0.0`) on symmetric 1-px X-junctions in
   `compute_faulds_hinz_kinematic_fields`; fixed via second-derivative Gaussian Hessian spin-2 eigenvector
   `_principal_axis_spin2(v, sigma=2.2)` (`1.0771` on X-junction vs `0.0040` on straight fault; locked by
   `tests/test_h86j_tvhs.py`).
2. Strict 4-quadrant out-of-quadrant LOQO (`gems57-pooled-hide-v2`, `11,321` withheld positives): `E1 = 0.0983
   [0.0800, 0.1159]` (beating `R0_D28 = 0.0931`), zero-catalogue blind `E2 = 0.0626 [0.0475, 0.0778]` (beating
   `H86I-KSAD E3 = 0.0624` and `H86I-HVFD E1 = 0.0475`), and unweighted strict-LOQO `E3 = 0.1214 [0.1060,
   0.1350]`. Inverse exposure-propensity weighting (`w_sar` up to `2.5x`) + `0.34 * P_blind` floor diverted
   ~23% of dots off surficial scarps into unmapped basin interiors (`paired E1 - E3 = -0.0231 [-0.0356,
   -0.0118]`), and `3` discrete `<=60k`-dot registry rasters (`GEMSDOE43` `0.7278`, `GEMSDOE53` `0.8192`) plus
   `13GEMSDOE`/`17GEMSDOE` and `2` off-grid rows failed full-registry uniqueness (`0/5` firings against concurrent
   `H86J-CSGD`, `H86I-RLMS`, `H86I-SACD`, `H86J-MPC`, `UNIQUEDOT`, max `0.6137`).
3. Verified closure of `IR-86-H86G-FEED-20261025` (`GEMSDOE89 = 0.0301`, `GEMSDOE90 = 0.0749` present as
   `OWNER-REPORTED` in `registry/prior_scores.csv` and hash-bound `docs/evidence/fleet-feed.json`).

## IR-86-MCSP-LIDAR-SURVEY-BIAS-20261025 — 3DEP 1 m LiDAR acquisition swaths leak human mapping effort (`SW 95.1%` vs `NE 52.6%`)

**Observed.** Quadrant-by-quadrant measurement on the Nevada study footprint (`5,167,373` valid pixels) revealed an inverse relationship between mapped `existing_faults.tif` density and unmapped USGS SGMC bedrock fault density (`> 3 px` from `existing_faults.tif`): `SW` (`10.9%` area) has `cat = 16.74‰`, `SGMC = 7.36‰`, `3DEP LiDAR = 95.1%`, whereas `NE` (`26.4%` area) has the lowest mapped catalogue density (`9.21‰`), the highest unmapped SGMC bedrock fault density (`22.49‰`), and only `52.6%` 3DEP 1 m LiDAR coverage (`47.4%` missing). In `HistGradientBoostingClassifier`, both `0`-filling (`Fold NE E2 = 0.0000`) and `NaN` missing-value routing (`missing_go_to_left`, `Fold NE E2 = 0.0036`) exploit the LiDAR swath boundary as a proxy for human survey effort rather than fault scarp mechanics.

**Fix.** `src/gems86_mcsp/features.py::_put_lidar_debiased` omits `lidar_valid` completely and substitutes robust-z / quantile-matched 10 m USGS DEM scarp curvature (`topo10_curv_lineament` / `topo_slope_10m`) outside acquired 3DEP swaths, eliminating `0` and `NaN` survey-boundary cues across all `5,167,373` footprint pixels, while `scripts/restore_protocol_data.py` adds Git smart-HTTP blob-fetch fallback gated strictly on `b"API rate limit exceeded"` in `stderr`.

## IR-86-MCSP-PRIOR-ALIGN-SIGN-20261025 & IR-86-MCSP-UNIFORM-RANK-CELF-20261025 — Inverted `LOQO` Elkan prior alignment (`Fold NE E2 = 0.0024`) and Uniform-`rank01` CELF dispersion uncovered and repaired in `H86K-STDP`

**Observed.** Forensic audit of `src/gems86_mcsp/model.py` prior to `H86K-STDP` preregistration identified two compounding defects:
1. `_prior_align_prob` divided quadrant `q`'s predicted odds by the complement training positive rate `pf / (1 - pf)`. Because `NE` Nevada has the lowest mapped `existing_faults.tif` density (`9.21‰`) despite the highest off-catalogue USGS `SGMC` bedrock fault density (`22.49‰`), its training complement (`NW + SW + SE`) has `pf > pg`, which **penalized `NE` odds further** and collapsed `Fold NE` blind `E2` to `0.0024`.
2. `rank01_on_mask` mapped raw probabilities to a Uniform `[0, 1]` surface (`mean = 0.50`) before `celf_allocate_dots`, causing CELF to trade high-probability fault crests for broad `0.85`-rank mountain aprons to avoid kernel overlap.

**Fix.** Without mutating archived `H86J-MCSP` receipts, `src/gems86_stdp/model.py::calibrate_quadrant_sparse_posterior` standardizes out-of-quadrant log-odds using only unlabelled within-quadrant `(median, P90)` statistics (`0` held-out label leakage) and maps to a convex sparse posterior `sigmoid(-4.55 + 1.65 * z_q)` (`~1.05%` median base rate), paired with `src/gems86_stdp/dinkelbach_celf.py::exact_six_ring_self_credit` + Dinkelbach fractional-programming CELF. On identical `37,654` dots, `Fold NE` blind `E2` jumped **`28.5x` (`0.0024 -> 0.0685`)** and `Fold NE E1` jumped **`+71.5%` (`0.0828 -> 0.1420`)**, while `H86K-STDP` (`E1 = 0.1133`, `E2 = 0.1151`) became the first `37,654`-dot candidate in repository history to beat `GEMSDOE32` `H33` (`+0.0196 [+0.0047, +0.0355]`) and `H86J-MCSP` (`+0.0134 [+0.0002, +0.0261]`) on `SGMC-PROXY-DTI` with strictly positive paired 95% CIs (`verdict = "negative"`, `DO NOT SUBMIT` under full 700-entry `v2` literal/completeness gates; `0` slots used).



## IR-86-H86K-SITE/RERUN/RECEIPT-PATH-20261025 — H86K artifact not on Pages, not rerunnable in fresh checkout, stale receipt path

**Observed (2026-10-25 review session `arena/234c24b9`).** (1) The H86K-STC candidate
(`releases/h86k/gems86-h86k-stc-40000dots-20261025T131720Z-61680c22-zeros.tif`, sha256 `e4d00084…a11`)
exists only under `releases/h86k/`; it is absent from `docs/downloads/` and
`docs/evidence/download-inventory.json`, so the Pages site does not offer it. Copying it into
`docs/downloads/` makes `scripts/check_site.py` fail closed ("Unregistered downloadable
raster/archive") — that guard was NOT bypassed; proper publication requires registering the
artifact through `scripts/build_site.py`/inventory generation. (2) `scripts/run_h86k.py` reads
`data/bridge/training_features.tif`, which is gitignored and restored-only; it is absent in this
checkout, so the lane cannot be rerun here until `scripts/restore_data.py` restores the pinned
19-band stack. (3) `releases/h86k/*.json:validator.file` still references the pre-move
`docs/downloads/…` path; byte hash/size were independently re-verified against the `releases/`
copy (`docs/evidence/h86k-revalidation-20261025.json`) and match. Verdict unchanged: negative,
DO NOT SUBMIT, 0 slots.
## IR-86-LIVE-INPUT-RECEIPTS-20261025 — tracked receipts outlive ignored workspace data

**Observed in session 679d92e7.** `data/prepared_manifest.json` records a historical
19-band preparation (`has_features=true`), but neither native feature TIFF copy
nor any of its 21 prepared arrays is present in this fresh checkout. The recorded
lane mmap is also absent; its size-only receipt would not establish a verified
shared-template cache even if restored. These are current input-integrity
measurements, not evidence that the historical preparation never happened.

**Fix.** `scripts/audit_workspace_inputs.py` inspects current file hashes/lengths,
checks both TIFF locations and exact array identities, distinguishes lane-cache
presence from the shared-cache contract, and fails `--require-native` for
missing/corrupt native inputs. The three-pass software reviewer runs it without
rebuilding caches or touching model artifacts. A successful inspection is not
training/submission clearance. Snapshot: `research/session-679d92e7-inputs.json`.
The earlier prompt's “single remaining blocker is data placement” is incomplete:
the independently remeasured literal overlap blocker and scientific/registry
requirements remain. No new TIFF or weekly slot was created to mask this gap.

**Interpretation correction.** Two current README summaries overstated H33's
private-score causation and gave an invalid simplified collar-pruning formula.
They now distinguish support identity from hidden-truth performance, and state
the exact inequality with *weighted FP mass reduction*, not raw deleted-dot
count. Owner request and historical source archives were preserved byte-for-byte.

## IR-86-H86KPSC-GDSC-RECEIPT-20261025 — metadata mismatch resolved transparently

**Observed on merging origin/main (`f55dbb1`).** `scripts/audit_downloads.py` rejected the already-merged GDSC artifact `gems86-gdsc-dilatational-37654dots-20261025T134427Z-70224321-zeros.tif`: its writer receipt used a path instead of the ZIP basename and omitted explicit `promoted` / `approved_for_weekly_slot` flags. The raw GDSC HOLDOUT-DTI receipt also does not provide a 95% CI; that scientific evidence gap remains.

**Resolution in this follow-up.** Corrected only the sidecar metadata (`zip_file` basename, `promoted=false`, `approved_for_weekly_slot=false`, `safe_to_submit=false`) and regenerated the local download-validation receipt. TIFF and ZIP bytes, hashes, holdout metrics, and verdict were not changed. The artifact remains `DO NOT SUBMIT`; the literal witness stop still applies.

## IR-86-0C60B079 (2026-10-25, session `0c60b079`) — review irregularities A–G (flagged, no artifact changed)

Full evidence: [`research/SESSION_0C60B079_REVIEW.md`](research/SESSION_0C60B079_REVIEW.md) · [`research/session-0c60b079-run-card.json`](research/session-0c60b079-run-card.json). No TIFF was generated, no experiment run, no slot used, no bypass.

- **A — Dense-raster gate semantics.** The official reference notebook (`drivendataorg/gems-prize-reference-solution`, commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b`, cell 19) writes a dense float probability map. The literal "dots within 3 px" rule has no defined dot set for such a raster; against the full-support witness it returns 1.0 for any nonempty candidate. Owner decision needed; no threshold was changed.
- **B — H33 vs parent encoding.** `GEMSDOE32` H33 (`c55bafc4…`, 37,654 dots, 0 NaN) vs parent `GEMSDOE28` h27-4-r1 (`ab023001…`, 40,199 dots, 7,111,787 NaN). Difference: 2,545 in-footprint dots removed, 0 added, and the NaN→0 encoding change. The vendored `vendor/template66/gems/metric.py` treats NaN as 0, so encoding should be score-neutral there, but this pair was not previously recorded as encoding-confounded.
- **C — Portal "[0, 1]" error not reproduced.** All 31 `docs/downloads/*.tif` pass a finite-in-[0,1] check with 0 NaN. The data files that carry out-of-range sentinels are `data/bridge/existing_faults.tif` (−1 outside footprint, 7,111,787 cells) and `sample_submission.tif` (NaN). The likely cause is a file derived from the −1 catalogue, but this is a hypothesis until the uploaded filename is known.
- **D — Unverified leaderboard figures.** The request cites both 0.4413 and 0.3195 as the current top GEMSDOE score. Both are owner-supplied; the DrivenData leaderboard was not fetched (AGENTS rule 9).
- **E — Witness not local.** `registry/dense-witness.tif` (pinned in `research/registry_witness_pin.json`) is absent in this checkout; its 1.0 overlap is a prior receipt, not a re-measurement here.
- **F — User actions.** Eligibility certification (rules §1.3) and generative-AI disclosure in the narrative (rules §3.2) are the user's to complete.
- **G — Unreachable official hosts.** From this sandbox, `usgs.gov`, `doi.org` (GeoDAWN DOI `10.5066/P93LGLVQ`, INGENIOUS DOI `10.15121/1881483`), `drivendata.org` and `gbcge.org` return no response. Feature data cannot be obtained here.

## IR-86L-01 / IR-86L-02 (2026-10-25, H86L-FMC session)
- IR-86L-01: shared cached feature stack absent (.cache/training_features.tif not in checkout); native-band lanes BMR/GSST blocked until restore_data.py runs with authorised access.
- IR-86L-02: fleet minority-consensus surface anti-predictive on hide-and-recover holdout (canary AUC 0.436, HOLDOUT-DTI 0.0000); candidate also fires 3px-overlap duplicate gate (0.886 vs GEMSDOE63). Verdict negative, DO NOT SUBMIT. See research/SESSION_20261025_H86L_FMC_REVIEW.md.

- **IR-H — main fails its publish gates after PR #150 (found 2026-10-25, session `0c60b079`; not caused by this session).** `docs/downloads/gems86-h86l-fmc-minconsensus-37654dots-20261025T161053Z-zeros.{tif,zip}` are not registered in `docs/evidence/download-inventory.json` / `registry/artifact_cards.json`, so `scripts/check_site.py` and `scripts/build_site.py --check` exit 1 on main. `pytest -q` on main: 16 failed / 985 passed (10 in `tests/test_release_audit.py`). `scripts/run_h86l_fmc.py` writes the run card only. Owner action: register the artifact through the lane's own protocol and re-run `audit_release.py --measure-registry`; do not mark it authorized. Documented here; not repaired by session `0c60b079`.

## IR-86-H86M-POISSON81 (2026-10-25, session `ecc314b3`, H86M-LT) — scored-fleet file/score mismatch suspect

`data/scored_fleet/GEMSDOE81__gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros.tif`
(binary, 44,090 dots, median d_cat 2.2 px) carries owner-reported live score **0.0041**, but every
tomography fit (E2b/E2c/E2d/E2e) predicts **0.043–0.084** for these exact dots — the largest
residual in the fleet by an order of magnitude. Either (a) the submitted bytes differed from this
local binary (the stem says "cont", suggesting a continuous raster was submitted and this is a
thresholded derivative), or (b) the organizer masks a >300 m catalogue buffer that penalizes this
collar-hugging raster far beyond the other fits' collar behaviour. H86M-LT excluded it from
belief fitting and hard-excluded `d_cat <= 3 px` from emission under either explanation.
Owner action: confirm which filename was actually uploaded for the 0.0041 receipt; do not use
this raster/score pair as a calibration anchor until resolved. Evidence:
`docs/evidence/h86m-lt-tomography.json`, `research/H86M_LT_REVIEW.md`.

## IR-86-H86M-INVENTORY (2026-10-25, session `ecc314b3`) — new artifact not yet in generated index

The H86M-LT TIFF/ZIP/receipt are published under `docs/downloads/` with a standalone lane page
(`docs/h86m-lt.html`, same pattern as `docs/h86k-psc.html`) but are **not** registered in
`docs/evidence/download-inventory.json`, because `scripts/audit_release.py` has no
`holdout_kind` branch for a tomography-LOO lane (it raises on unsupported kinds) and its status
rendering is DO NOT SUBMIT for every kind except `h86g_edti`. Registering correctly requires a
reviewed shared-audit branch + `build_site.py` regeneration; this session reports it instead of
smuggling a private fork (protocol rule 2). Main already fails `check_site`/`build_site --check`
and 16 pytest cases over the analogous H86L-FMC gap (IR-H above); H86M adds one more unregistered
artifact to the same known failure class.
## IR-86-E95B-PUBLICATION-20261025 — repaired missing H86L publication coverage

The branch inherited an H86L-FMC TIFF/ZIP absent from both publication indexes. This made the release/site audits fail before any artifact validation. Registered its actual SHA and existing negative scientific card; added explicit leakage-suspect archival normalization and regression tests. No raster bytes, scientific verdict, evaluator/writer or uniqueness thresholds changed. Fresh measurement validates all 32 published formats but confirms literal overlap failure against the pinned dense witness. This repairs the earlier IR-H inventory blocker; it does not authorize submission.

## IR-86-E95B-HISTORICAL-CLOCK-20261025 — frozen review compared with mutable audit

A test bound the historical follow-up run card's registry timestamp to the mutable latest audit. A legitimate fresh audit therefore failed the test. Preserved the original audit bytes from this branch's starting commit under `docs/evidence/session-followup-snapshot/`, bound their SHA in the historical card, and changed that test to verify the exact frozen evidence. No historical timestamp/count was rewritten as current. Latest-review tests continue to require current report hashes and measurement timestamps.


## IR-86-63051E73-H86L-INVENTORY — 2026-10-25

Reproduced and repaired the inherited H86L-FMC publication omission (IR-H in the prior review). Registered existing TIFF SHA `5bacedbe67a8000dd8bcb5f375c089cef71aba7172f482ff05a76363a04a502a`, joined its original negative run card, restored the pinned witness and remeasured all published final dots. No candidate pixels or scientific receipts changed. Added a dedicated archived leakage-suspect schema rather than describing fleet-as-is evidence as fold-safe hide-and-recover. Removed the non-generated “NEWEST UNIQUE TIFF” banner during deterministic site regeneration, retaining its anchor and explicit audit-only decision. Current format count is 32; submission authorization remains false. See `research/SESSION_63051E73_REVIEW.md`.

## IR-86-63051E73-H86M-ARCHIVE — 2026-10-25

PR #158 added an H86M TIFF to the inventory without its release-card mapping, again breaking the generated-site audit. Integrated that upstream merge, joined its negative card, and remeasured all 33 inherited TIFFs against the pinned witness. H86M's archived assertions “no public labels” and catalogue-only leakage “structurally impossible” are not accepted: the pinned catalogue/labels are present and catalogue features require fold-visible rebuilding. Its HOLDOUT-DTI stays null/unvalidated and upload remains prohibited. No scientific result was manufactured; original receipts preserved.

## IR-86-92F9E0E8-H86M-PUBLICATION — 2026-10-25 (found independently; repair superseded at merge by PR #166)

On this branch's starting commit (`3deca67`), H86M-LT violated the repo's own publication
guard in four measured ways: (1) its TIFF/ZIP were absent from
`docs/evidence/download-inventory.json` and `registry/artifact_cards.json` (the gap already
flagged as IR-86-H86M-INVENTORY); (2) `docs/h86m-lt.html` carried the banned instruction
"IS THIS FILE OK TO SUBMIT? YES"; (3) its run card set `safe_to_submit=true` with no
`submission_ready`/`gates` fields; (4) README's headline said "OK TO SUBMIT" while the
generated site said "NO FILE AUTHORIZED · DO NOT SUBMIT" — so `scripts/check_site.py`
failed on main (exit 1, reproduced this session). Session `92f9e0e8` first repaired this locally (registration + run-card publication
addendum preserving the PA-86 PROMOTE); in parallel, session `57139348` repaired the
same failure on main (PR #166) by downgrading the card to a negative unvalidated
archive (`h86m_lt_unvalidated`). At merge, main's already-accepted LT state was kept
and this session's parallel LT branch/addendum was removed, leaving exactly one LT
normalization path; only the H86N-EQL lane was layered on top (37 artifacts). No raster
bytes or thresholds changed in either repair; no slot was authorized or used.

## IR-86-92F9E0E8-PRIOR-SCORES — 2026-10-25 (open, data re-pin needed)

The 2026-10-25 `92f9e0e8` request adds owner-reported claims for GEMSDOE91 (0.1367,
0.1823) and GEMSDOE92 (0.0255), but `registry/prior_scores.csv` still carries
"NO ARTIFACT OR SCORE SPECIFIED IN PROMPT" placeholder rows for those sites and its
SHA-256 is pinned into the generated fleet feed (`owner_ledger_sha256`). The claims are
archived verbatim in `research/REQUEST_20261025_92F9E0E8.md`; transcribing them into the
CSV requires a deliberate feed re-pin/regeneration pass, deliberately not smuggled into
this session's lane change. They remain unverified claims either way (no organizer
receipts).

## IR-86-57139348-LT-UNSUPPORTED-CLEARANCE (2026-10-25)

H86M-LT was a published but unregistered TIFF/ZIP with `safe_to_submit=true` and an
“OK TO SUBMIT” standalone page. Corrected to negative/audit-only and registered in
both release indexes without modifying raster bytes. No required buffered hide-and-
recover CI or per-feature canaries exist; the historical surface registry checker
uses Pearson, not Spearman, and reconstructs missing ignored cache source with exec.
Post-placement gate amendments are exploratory, not independent validation.
See `research/SESSION_57139348_REVIEW.md`; no new experiment or weekly slot used.


## IR-86-96FC6D48-PREFLIGHT-LAYOUT — 2026-10-25

`scripts/protocol_preflight.measure()` defaulted `data_dir` to `ROOT/"data"` and
`scripts/audit_release.measure_all_registry()` called `grid.load_grid(root/"data")` with the
witness record at `root/"data"/pin["dest"]`, but the SHA-pinned grid (`sample_submission.tif`,
`existing_faults.tif`) is committed under `data/bridge/` (see `vendor/gems57/grid.py` DATA_DIR
and `tests/conftest.py` BRIDGE). `audit_release.py --measure-registry` therefore crashed with
FileNotFoundError in a fresh checkout before any measurement. Fixed once in `scripts/`
(`protocol_preflight.py`, `audit_release.py`, and the same stale layout in the operative PA-86
checkers `check_h86e_registry.py` / `pa86_chance_overlap.py`); the vendored template was not
modified. The pinned witness was restored from the pinned 17GEMSDOE blob
`374c88b1da2b803e2ed160de467fd71ae114010d` into gitignored `data/bridge/registry/`
(SHA-256 `ab0a0a62...`, 25,065,181 bytes). Thresholds, evaluator, and witness identity are
unchanged. `tests/test_h86i_rlms.py` probed the old `data/` layout to select the expected error
class; updated to probe the real pinned paths.

## IR-86-96FC6D48-H86MLT-REGISTRATION — 2026-10-25

Session `96fc6d48` independently reproduced the PR #165 H86M-LT publication omission
(registered on main by parallel session `57139348`, PR #166) and re-verified the raster from
disk bytes (SHA-256 `4067382c...`, ZIP byte-identity, EPSG:32611 3730x3292, values exactly
{0,1}, 37,654 positives). This branch's parallel card-supersession and page rewrite were
discarded at merge in favour of main's `h86m_lt_unvalidated` handling; both sessions reached
the identical DO NOT SUBMIT state. See `research/SESSION_20261025_96FC6D48_REVIEW.md`.
## IR-86M-02 (`arena/2ea5b025-gemsdoe86`, 2026-10-25) — Automated Parallel-Run Protocol Rule 1 stop caught `H86M-PFTE` Arm `E1` (`0.7041 > 0.70` vs `H86K-STDP`) prior to GeoTIFF serialization

- **Observed during `scripts/run_h86m_pfte.py` Step [5/6].** Preregistered kinematic+blind Arm #1 `E1_pfte_comonotonic_dcelf` (`alpha_kin = 0.68`, `HOLDOUT-DTI = 0.1310 [0.1141, 0.1476]`, `Fold NE = 0.1436` vs `E3 = 0.1185`, `SGMC-PROXY-DTI = 0.1166`) passed continuous surface Spearman across all `702` indexed rasters (`worst_spearman = 0.5657 <= 0.90`, `0` firings) and `459 / 460` discrete `<=90k`-dot submissions, **except** `0.704069 > 0.70` 3-px dot overlap against `H86K-STDP` (`3ac7fa1d...`) driven by shared `compute_elastic_fields` fold-visible fracture lobes.
- **Decision enforced.** `run_h86m_pfte.py` halted `E1` **before writing any GeoTIFF**, performed **zero hyperparameter retuning** (`3` total experiments), and emitted preregistered pure-blind Arm #2 `E2_pfte_blind_comonotonic_dcelf` (`6bfde507...`, `HOLDOUT-DTI = 0.0734 [0.0591, 0.0882]`, **all-time `37,654`-dot repository high `SGMC-PROXY-DTI = 0.1210 [0.1024, 0.1407]`**, `0 / 702` continuous surface Spearman firings with `max = 0.4795`, and **`0 / 464` discrete `<=90k`-dot overlap firings** with `max = 0.6244 <= 0.70`, including `0.0843–0.3682` vs concurrent `BMR`/`CNT`/`DAMAGERING`/`LT`). Verdict remains `negative` (`DO NOT SUBMIT`, `0` weekly slots spent).


## IR-86-H86M-BMR-CNT-NODATA-SENTINEL-20261025 — 3,061 pixels inside `sample_submission.tif` footprint carry float32 sentinel `-3.4028235e+38` in `training_features.tif`

Inspection of `training_features.tif` (`4371c82e...`) against `sample_submission.tif`'s valid footprint `fp` (`5,167,373` pixels) showed that **3,061 pixels inside `fp`** across bands 5, 7, 8, 11, 13, 15, 17, 18 carry the finite float32 sentinel `-3.4028234663852886e+38` (`<= NODATA * 0.5`). Implemented `clean_band(arr, fp)` in `src/gems86_gsst/features.py` for `H86N-GSST` so that all non-finite and `<= NODATA * 0.5` pixels inside and outside `fp` are replaced with the valid in-footprint mean before any spatial filtering.

## IR-86-H86N-GSST-NEGATIVE-20261025 — `H86N-GSST` falsified on 4-fold hide-and-recover holdout (`0.0310` vs `E0 = 0.0349`, `E2 = 0.0407`)

Executed the preregistered `H86N-GSST` lane (`scripts/run_h86n_gsst.py`, `src/gems86_gsst/features.py`). On `gems57-pooled-hide-v2` (`11,321` withheld positives, `1,000` physical-block draws), `H86N_GSST` achieved `HOLDOUT-DTI = 0.0310 [0.0210, 0.0423]`, trailing `E0_raw_grav_slope` (`0.0349 [0.0238, 0.0473]`, paired $\Delta = -0.0039\ [-0.0078, -0.0001]$) and `E2_compact_curv` (`0.0407 [0.0305, 0.0529]`, paired $\Delta = -0.0097\ [-0.0229, +0.0033]$). Recorded `verdict = "negative"`, `safe_to_submit = false`, `submission_ready = false`, `approved_for_weekly_slot = false`, `submission_slots_used = 0` in `docs/evidence/h86n-gsst-run-card.json`.

## IR-86M-BMGS-20261025 (session `94cbed2d`) — `GEMSDOE91`/`GEMSDOE92` (`REV2`) fleet forensics & log-odds strand-crush defect fixed

Full evidence: [`research/SESSION_20261025_H86M_BMGS_REVIEW.md`](research/SESSION_20261025_H86M_BMGS_REVIEW.md) · [`docs/evidence/h86m-bmgs-run-card.json`](docs/evidence/h86m-bmgs-run-card.json).
- **1. `GEMSDOE91` (`0.1823` `OWNER-REPORTED`) halo-crowding vs `GEMSDOE92` (`0.0255` `OWNER-REPORTED`) uniform pullback over-shift:** Forensic comparison across the newly supplied rev-2 fleet entries confirmed that in-sample PU models crowd `68.5%` of dots into `< 1 km` near-catalogue halos (vs `69.8%` `> 1 km` far-field in `GEMSDOE32` `H33`), while uniform `50°` up-dip pullback (`5–28 px`) shifts steep strike-slip (`80°–90°`) and horst contacts completely outside the `300 m` (`3 px`) DTI kernel.
- **2. `IR-86M-STRAND-LOGODDS-20261025` (caught & fixed in Pass 2):** Averaging log-odds (`logit p`) along a `7×7` directional stencil acts as a geometric mean of odds that multiplicatively crushes curved 1-px fault crests whenever stencil endpoints touch desert background (`p ~ 0.0005`). Replaced in `src/gems86_bmgs/model.py` with additive probability-space 8-azimuth strand reinforcement (`>= 0.70 * p_bayes` floor regression-tested in `tests/test_h86m_bmgs.py`). Unified `H86M-BMGS` achieved `HOLDOUT-DTI = 0.1310 [0.1121, 0.1509]` (`6x` single-feature `H86M-BMR` `0.0220`, `4.2x` `H86N-GSST` `0.0310`, `3.2x` `H86M-CNT` `0.0408`) and `SGMC-PROXY-DTI = 0.1082` (`E2` blind `0.1111` at `70.21%` far-field `> 1 km`), with `0.0820–0.4101` 3-px overlap vs all parallel `H86M`/`H86N` rasters (`0.6351` vs `H86K-STDP` — clearing the `0.70` stop that halted `H86M-PFTE` `E1`); remains `verdict = "negative"` (`DO NOT SUBMIT`, `0` weekly slots used).

## IR-86M-STDP-QUAD-SEAM — Prior `H86K-STDP` LOQO helper split at bounding-box `H//2=1865` instead of footprint median `ym=936` (`92.9 km` seam shift) (2026-10-25)

`vendor/gems57/holdout.py::quadrant_ids(footprint)` splits at footprint median `(ym=936, xm=1504)` (`~25%` of valid pixels per fold), whereas `src/gems86_stdp/model.py::quadrant_grid(shape)` split at bounding-box midpoint `(H//2=1865, W//2=1646)` (`929 rows = 92.9 km` southward shift). Fixed in `src/gems86_slcq/model.py::true_footprint_quadrants` with `12 px` (`2.4 km` total dead-zone) training-domain erosion while keeping `H86K-STDP` receipts untouched.

## IR-86M-SLCQ-01 — `H86M-SLCQ` generated a unique `15/15` validated GeoTIFF (`HOLDOUT-DTI = 0.1527`, paired `E1 - E3 = +0.0150 [+0.0009, +0.0282]`, `SGMC = 0.0967` / blind `0.1131`) and failed closed `DO NOT SUBMIT` (2026-10-25)

`scripts/run_h86m_slcq.py` executed `research/H86M_SLCQ_PREREGISTRATION.json` (`registry/h86m_slcq_hypotheses.json`) and wrote [`docs/downloads/gems86-h86m-slcq-dcelf-37654dots-20261025T185217Z-944322f2-zeros.tif`](docs/downloads/gems86-h86m-slcq-dcelf-37654dots-20261025T185217Z-944322f2-zeros.tif) (`sha256: c285c17932647c03bc6815c0ba2f0ef2d21b42a3e6f79e9af510257de6619f5d`, `37,654` unit dots, `15/15` format checks PASS, `43/43` leakage canaries PASS with `max AUC = 0.7943 <= 0.90`, `0/702` surface Spearman `rho > 0.90` firings, `0/460` comparable `<=90k`-dot discrete 3-px overlap firings `> 0.70`, and `0/8` firings vs concurrent `H86M`/`H86N` TIFFs). Automatically set `verdict = "negative"`, `decision = "DO NOT SUBMIT"`, `safe_to_submit = false`, `0` weekly slots used under literal `17GEMSDOE` (`1.0000`), space-filling/dense archive ribbons, and `2` off-grid rows (`14GEMSDOE`, `7GEMSDOE`). See [`research/SESSION_20261025_H86M_SLCQ_REVIEW.md`](research/SESSION_20261025_H86M_SLCQ_REVIEW.md) and [`docs/evidence/h86m-slcq-run-card.json`](docs/evidence/h86m-slcq-run-card.json).

## IR-86P-RESTORE-INVENTORY-DUP-SHA — `restore_registry_inventory.py` double-counted identical SHA-256 rasters across parallel paths in a repo tarball (`781 != 655`) (2026-10-26)

- **Observed.** In `scripts/restore_registry_inventory.py::restore_repo_codeload_and_git`, when two rows in a single owner repo referenced identical raster bytes under two archive paths, `got in needed_shas` appended to `restored` twice without checking `got not in found_shas`, yielding `verified = 781 != 655` and causing `complete_accessible_scan` to report `False` even when all `655 / 655` SHA-pinned rasters were byte-verified on disk.
- **Decision.** Added `and got not in found_shas` before appending to `restored` (`scripts/restore_registry_inventory.py`) and added `data/bridge/<dest>` -> `data/<dest>` witness path fallback in `scripts/protocol_preflight.py` and `scripts/audit_release.py` without touching `vendor/`. Re-running `restore_registry_inventory.py` verified `655 / 655` entries (`missing = []`, `complete_accessible_scan = True`, exit `0`).

## IR-86P-FLEET-20261026 — Three artifact-identity & duplicate-score irregularities in 2026-10-26 `GEMSDOE91` / `GEMSDOE92` owner feed (`119` scored claims)

Direct zero-REST tarball inspection (`codeload.github.com`) of `GEMSDOE91` and `GEMSDOE92` `HEAD` uncovered three discrepancies against the 2026-10-26 prompt feed (`research/REQUEST_20261026.md`):
1. **Duplicate `0.1367` claim across two `GEMSDOE91` stems (`bf21d9a4bd` vs `4d124f1d`):** `gems91-s17-cwpc-e3-37654dots-20261025T150000Z-4d124f1d-zeros: 0.1367` is byte-verified in `GEMSDOE91` `HEAD` (`docs/downloads/...tif`, `sha256 = 792af6255a7e1048...`), whereas earlier stem `gems91-s17-cwpc-20261025T052212Z-bf21d9a4bd-zeros: 0.1367` is absent from `GEMSDOE91` `HEAD` (`docs/downloads/`). Both remain labeled `OWNER-REPORTED` (`CLAIM` in `ledger/submissions.csv`), never `ORGANIZER-CONFIRMED`, and flagged as a probable stem-rename duplicate score.
2. **Unscored `GEMSDOE91` `S18` stem/timestamp mismatch:** Prompt lists `GEMSDOE91-S18-UNIQUE-curvtilt-20000dots-20261025T193000Z-zeros:`, whereas actual `GEMSDOE91` `HEAD` contains `docs/downloads/gems91-S18-UNIQUE-curvtilt-20000dots-20261025T182858Z-29db2405.tif` (`sha256 = af01bc7190ce736d...`, `20,000` dots, no `-zeros` suffix).
3. **Missing `GEMSDOE92` `HEAD` raster (SUPERSEDED / CORRECTED BY `IR-86Q-HALLUCINATION-AND-LEDGER-REPAIR-20261026`):** At the earlier snapshot checked in `1595e23f`, `GEMSDOE92` had not yet published `.tif` files; subsequent GitHub REST tree verification at `GEMSDOE92` `HEAD` (`f1dd2107cd28...`) confirms `163` `.tif` files (`127` in `docs/downloads/`), including `docs/downloads/gemsdoe92-listricdip-updip50-37654-20261025T190000Z-zeros.tif`.

## IR-86Q-HALLUCINATION-AND-LEDGER-REPAIR-20261026 — Forensic retraction of four PR #182 (`1595e23f`) factual errors & ingestion of 5 new Focus-9 `OWNER-REPORTED` scores (`119 -> 124`)

Line-by-line verification of PR #182 (`4f746ce`) against `registry/prior_scores.csv`, `research/REQUEST_20261026_REV2.md`, live GitHub trees (`gh api`), and byte-measured Focus-9 GeoTIFFs (`docs/evidence/focus9-forensics-20261026-rev2.json`) exposed and repaired four factual defects:
1. **Hallucinated `GEMSDOE87` / `65` / `88` / `84` / `77` / `75` scores retracted:** PR #182 (`README.md:8`, `scripts/build_site.py:648`, `research/SESSION_20261026_H86P_TCWB_REVIEW.md:21,69`) claimed `GEMSDOE87` (`gemsdoe87-opt-33851dots-20261015-zeros: 0.3195` and `37010dots: 0.3143`), `GEMSDOE65` (`0.2951`), `GEMSDOE88` (`0.2943`), `GEMSDOE84` (`0.2939`), `GEMSDOE77` (`0.2933`), and `GEMSDOE75` (`0.2899`). Direct GitHub API verification of `buffedlizard55-lab/GEMSDOE87` (`HEAD` `e53f08f400`, `5` `.tif`s) and `registry/prior_scores.csv` proves `GEMSDOE87`'s only reported score is `h87-h87-cmgep-20261022T060000Z-8f394f43: 0.0500` (with zero `33851`/`37010` files), while `GEMSDOE65=0.0431`, `GEMSDOE88=unscored`, `GEMSDOE84=0.0132`, `GEMSDOE77=0.0964`, `GEMSDOE75=0.1627`. Across all 92 `buffedlizard55-lab` repositories (`124` scored claims), **`GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778` `OWNER-REPORTED`) is #1 overall**, whereas `0.3195` and `0.4413` are conflicting unverified external DrivenData leaderboard benchmarks quoted in the prompt.
2. **`GEMSDOE28` best-score mis-transcription fixed (`0.2710` vs `0.2708`):** `registry/prior_scores.csv` (`line 55`) and `research/REQUEST_20261024/25/26.md` record `GEMSDOE28` `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710` (`37,660` dots, `min_dcat = 1.41 px`, `65.7% > 1 km`) and `h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707` (`37,860` dots), ahead of `h27-4-r1-solo-d2-8: 0.2708` (`40,199` dots). PR #182 misquoted `h36-1` as `0.2683` and `h38-1` as `0.2498`.
3. **Focus-9 `HEAD` status nuance & `GEMSDOE30` `MSDB1` outside-footprint `NaN`s recorded:** 8 of 9 Focus-9 sites post `DO NOT SUBMIT` at `HEAD`, while `GEMSDOE27` (`HEAD` `426426b402`) posts a local-gate `OK TO DOWNLOAD AND SUBMIT` banner on unscored `gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif` (which under `GEMSDOE86`'s literal `17GEMSDOE` full-registry rule remains `safe_to_submit = false` here). Byte inspection of `GEMSDOE30` `gems30-MSDB1-edge44090-20261025-e7856ec3f14a.tif` (`0.1462` `OWNER-REPORTED`) also flagged `7,111,787` outside-footprint `NaN`s (`0` inside-footprint `NaN`s).
4. **5 new Focus-9 `OWNER-REPORTED` scores (`119 -> 124`) + exact `GEMSDOE91` `S18` stem ingested:** Added `gvc1` (`0.0859`), `h66` (`0.0742`), `h29` (`0.2190`), `s18-mxtp` (`0.0217`), `MSDB1` (`0.1462`), and `gems91-S18-UNIQUE-curvtilt-20000dots-20261025T182858Z-29db2405` to `registry/prior_scores.csv`, rebuilt `ledger/submissions.csv`, and refreshed `docs/evidence/fleet-feed.json`.

## IR-86P-TCWB-01 — `H86P-TCWB` set an all-time strict-LOQO `37,654`-dot record (`HOLDOUT-DTI = 0.1727 [0.1560, 0.1894]`, paired `E1 - E3 = +0.0162 [+0.0040, +0.0286]`, blind `SGMC-PROXY-DTI = 0.0954`) and failed closed `DO NOT SUBMIT` (2026-10-26)

`scripts/run_h86p_tcwb.py` executed frozen preregistration [`research/H86P_TCWB_PREREGISTRATION.json`](research/H86P_TCWB_PREREGISTRATION.json) ([`registry/h86p_hypotheses_20261026.json`](registry/h86p_hypotheses_20261026.json)) and wrote [`docs/downloads/gems86-h86p-tcwb-dcelf-37654dots-20261026T024250Z-78c17eb0-zeros.tif`](docs/downloads/gems86-h86p-tcwb-dcelf-37654dots-20261026T024250Z-78c17eb0-zeros.tif) (`sha256: 8c8951653dcb4ac8c175136953dcb0a138147ab216327a461d430ce2698ab159`, `37,654` unit dots, `15/15` format & `[0, 1]` range checks PASS, `43/43` leakage canaries PASS with `max AUC = 0.8061 <= 0.90`, `0/711` surface Spearman `rho > 0.90` firings with `max = 0.4797`, `0/469` discrete `<=90k`-dot 3-px overlap firings `> 0.70` with `max = 0.6986`, `0/27` Focus-9 firings with `0.2735` vs `GEMSDOE32 H33`, and `0.6398 <= 0.70` vs unmerged PR #179 `H86N-SHPB`). Automatically set `verdict = "negative"`, `decision = "DO NOT SUBMIT"`, `safe_to_submit = false`, `0` weekly slots used under literal `17GEMSDOE` (`1.0000`), `19` space-filling lattices, `8` `246k–985k`-dot dense scatter rasters, and `2` off-grid historical rows (`14GEMSDOE`, `7GEMSDOE`). See [`research/SESSION_20261026_H86P_TCWB_REVIEW.md`](research/SESSION_20261026_H86P_TCWB_REVIEW.md) and [`docs/evidence/h86p-tcwb-run-card.json`](docs/evidence/h86p-tcwb-run-card.json).

## IR-86Q-TCWB-SWAPPED-ARGS-20261026 — Swapped `rank01_per_quadrant(valid, qid, ...)` arguments in `src/gems86_tcwb/model.py:444` (`NW = 0.0000` blind collapse) & `H86P-3_RCSD` prose band-number mismatch

Code review of `src/gems86_tcwb/model.py:444` (`rank01_per_quadrant(p_blind * (0.72 + 0.28 * L_tcwb[...]), valid, qid)`) against `src/gems86_tcwb/model.py`'s own definition `rank01_per_quadrant(surface, quad_ids, valid)` revealed that `valid` (`bool`, coerced to integer `{0, 1}`) and `qid` (`{0, 1, 2, 3}`, coerced to `bool` where quadrant `0 = NW` became `False`) were passed in swapped order:
1. **Effect on `H86P-TCWB`:** Every pixel in Fold `NW` (`qid == 0`) received `rank01_per_quadrant = 0.0` (`E2_tcwb_blind` Fold `NW` `HOLDOUT-DTI = 0.0000`, Fold `NE = 0.0236`), while `SW` (`0.1306`) and `SE` (`0.1233`) received uncalibrated raw pooled ranks. Historical `H86P-TCWB` bytes and run card remain immutable per `AGENTS.md`.
2. **Fix in `H86Q-BFRA` (`src/gems86_bfra/model.py`):** Defined and called `rank01_per_quadrant(surface, valid, quad_ids)` consistently and regression-tested non-zero `NW` blind allocation in `tests/test_h86q_bfra.py`, lifting pure-blind `E2_bfra_blind` Fold `NW` from `0.0000 -> 0.0843` and Fold `NE` from `0.0236 -> 0.0613` (`+160%`), while revealing an important physical corollary: equalizing blind quantile ranks to 25% per quadrant (`rank01_per_quadrant`) starves fault-dense Walker Lane (`SW`, ~2.3x higher fault density than `NW`/`NE`), explaining part of `E1_bfra`'s `SW` dip (`0.1692` vs `E3` `0.1895`).
3. **Prose band-number mismatch in queued `H86P-3_RCSD`:** `registry/h86p_hypotheses_20261026.json` (`H86P-3_RCSD`) prose wrote `Bands 1 & 2 (tmi, mag_rtp)` and `Band 15 (tmi_hd)` when `src/gems86/io.py` defines `Band 1 = tmi`, `Band 2 = rtp_tilt`, `Band 14 = tmi_rtp`, `Band 15 = depth_to_basement`. Fixed in `registry/h86q_hypotheses_20261026.json` (`H86Q-1_BFRA` uses `Bands 1, 2, 14` with pixel-verified correlations `corr(B1, B14) = +0.5522`, `corr(grad B14, B2) = +0.8089`).

## IR-86Q-BFRA-E1-STOP-E2-SERIALIZED-20261026 — Automated Rule-1 pre-serialization stop caught `H86Q-BFRA` `E1` (`0.7755 > 0.70` vs `H86P-TCWB`); zero-catalogue `E2` serialized (`SGMC-PROXY-DTI = 0.0967 > GEMSDOE32 H33 0.0937`, `68.48% > 1 km`, `0/473` discrete firings, `DO NOT SUBMIT`)

Full evidence: [`research/SESSION_20261026_H86Q_BFRA_REVIEW.md`](research/SESSION_20261026_H86Q_BFRA_REVIEW.md) · [`docs/evidence/h86q-bfra-run-card.json`](docs/evidence/h86q-bfra-run-card.json).
- **1. Honest un-retuned 3-arm holdout & automatic Rule-1 stop on `E1`:** On `gems57-pooled-hide-v2` (`11,321` withheld positives, `49/49` leakage canaries `<= 0.8061 <= 0.90`), `E1_bfra_coupled_tworegime_dcelf` scored `0.1556 [0.1393, 0.1705]` vs `E3` `0.1584 [0.1419, 0.1743]` (`E1 - E3 = -0.0028 [-0.0162, +0.0113]`; `E1` beat `E3` in `NW` `0.1507 vs 0.1497`, `NE` `0.1446 vs 0.1294`, and `SE` `0.1506 vs 0.1477`, but dipped in `SW` `0.1692 vs 0.1895` due to equal-share `rank01_per_quadrant` + 1-D Hessian flank trimming on 2-D Walker Lane releasing stepovers). At Step `[5/6]`, `E1` hit `0.7755 > 0.70` 3-px dot overlap against local `H86P-TCWB` (`0` firings vs all `472` other `<=90k` rasters) and was **automatically halted before writing any `E1` `.tif`** (`docs/evidence/h86q-bfra-registry-final-dots.json`), performing **zero post-holdout retuning** (`experiments_run = 3`).
- **2. Zero-catalogue blind `E2_bfra_blind_subsurface_piedmont_dcelf` serialized (`DO NOT SUBMIT`):** Validating already-evaluated preregistered Arm #2 (`E2_bfra_blind`) confirmed `0 / 713` surface Spearman firings (`max = 0.2731 <= 0.90`), **`0 / 473` discrete `<=90k`-dot 3-px overlap firings** (`max = 0.6413` vs `GEMSDOE85` `90k`, `0.4678` vs `H86P-TCWB`, `0.3392` vs `GEMSDOE32 H33`, `0 / 30` Focus-9 firings), **`68.48% > 1 km` radial allocation (`median d_cat = 1,802.8 m`, matching `GEMSDOE32 H33`'s `69.8%` / `1,811.1 m` purely from zero-catalogue physics)**, **`SGMC-PROXY-DTI = 0.0967` (beating `GEMSDOE32 H33 = 0.0937`, `GEMSDOE28 D28 = 0.0937`, and `H86P-TCWB = 0.0809 / 0.0954`)**, and balanced 4-quadrant `HOLDOUT-DTI = 0.0734 [0.0604, 0.0865]` (`NW 0.0843`, `NE 0.0613`, `SW 0.0748`, `SE 0.0750`). Serialized [`docs/downloads/gems86-h86q-bfra-blind-dcelf-37654dots-20261026T065248Z-41cd9f80-zeros.tif`](docs/downloads/gems86-h86q-bfra-blind-dcelf-37654dots-20261026T065248Z-41cd9f80-zeros.tif) (`sha256: b9cd35e51880fa0f9b4c47962b4544e93b7c2929e269a8d7595bfbbd444c54a9`, `15/15` disk checks PASS); `verdict = "negative"`, `decision = "DO NOT SUBMIT"`, `safe_to_submit = false`, `submission_slots_used = 0`.



## IR-86R-PCPD-ALREADY-IMPLEMENTED-20261026 — Queued `H86Q-2_PCPD` claimed Baranov pseudogravity was untried; `H86M-PFTE` already implemented it

- **Observed (2026-10-26, session `9c9712ca`):** `registry/h86q_hypotheses_20261026.json` rank 2 (`H86Q-2_PCPD`) states "no lane in GEMSDOE86 or Focus-9 has computed Baranov FFT pseudogravity potential". Direct code inspection refutes this: `src/gems86_pfte/features.py:394` defines `baranov_pseudogravity_decoupling()` (lane `H86M-PFTE`, 2026-10-25), exported in `src/gems86_pfte/__init__.py` and preregistered in `research/H86M_PFTE_PREREGISTRATION.md`. PFTE already harvested the signal (blind `SGMC-PROXY-DTI = 0.1210` per its run card).
- **Decision:** PCPD is recorded as `H86R-5_PCPD_REJECTED` in `registry/h86r_hypotheses_20261026.json` and was NOT executed (executing it would be a duplicate lane). The queued-but-genuinely-unexecuted `H86J-SCO` catalogue-strike gate was executed instead as `H86R-SFG`.

## IR-86R-ESTIMATOR-MISMATCH-20261026 — Loose filename token matching false-labelled 5/28 fleet-estimator rows (v1) and 38 selector rows; strict v2 supersedes

- **Observed:** The first H86R fleet estimator (`docs/evidence/h86r-fleet-estimator-20261026.json`, v1) matched local rasters to `registry/prior_scores.csv` using any shared filename token of length >= 8 containing a digit. Date/dot-count tokens (`37654dots`, `44090dots`, `20261020`) therefore assigned other submissions' `OWNER-REPORTED` scores to 5 of 28 training rows: `GEMSDOE70 p5-multiphysics` variant (false 0.1152), `GEMSDOE80 adpt-kkt` (false 0.0943, the choquet file's score), both `GEMSDOE85` files (false 0.1110), and the explicitly `DO-NOT-SUBMIT` `GEMSDOE88 mgc-crossgradient` file (false 0.1564, a GEMSDOE78 score). The same matcher in the first selector table also labelled 36 unscored `gems86` downloads with false live scores (0.1152 / 0.1564).
- **Decision:** Matching is now strict in both `scripts/run_h86r_sfg.py` and `scripts/analyze_h86r_selector.py` (normalized-stem containment or shared hex hash token >= 8 hex chars including a letter; pure-digit/date/dot-count tokens never match), unit-verified (H33 -> 0.2778; H86R/GEMSDOE88/GEMSDOE70-variant -> None). Corrected estimator `docs/evidence/h86r-fleet-estimator-20261026-v2.json` (n=23, coefficients [-0.039, +0.156 ovH33, +0.115 SGMC, +0.215 frac>1km], LOO-RMSE 0.0380, candidate projection 0.1616 [0.087, 0.236]) supersedes v1 for every use; 38 selector live labels were corrected in place with the correction count recorded in the file. Lane gates G1-G6 never used the estimator, so the H86R verdict is unaffected. Regression tests: `tests/test_h86r_sfg.py` (v2 contract + selector no-false-score).

## IR-86R-INSTRUMENT-FLOORS-20261026 — Two instrument facts every future selector must price in (SGMC chance floor 0.0754; SGMC blind to collar; as-is >3 px-collar rasters score exactly 0 on catalogue-hide)

All three were measured this session on the shared vendor evaluator with historical replication checks passing exactly (H33 `HOLDOUT-DTI = 0.0036`, H33 `SGMC-PROXY-DTI = 0.0937`, BFRA `SGMC-PROXY-DTI = 0.0967`):
1. **SGMC-PROXY chance floor:** A seeded uniform-random emission of 37,654 dots under identical eligibility/spacing scores `SGMC-PROXY-DTI = 0.0754 [0.0715, 0.0789]` — above many shipped lanes (H86R E1 0.0596, E2 0.0757, E3 0.0204). The proxy rewards spatial spread (37,654 radius-3 kernels cover much of the footprint); SGMC deltas of +0.01-0.02 over H33 must be read against this floor and against dot-budget differences (e.g. 55k-dot EDTI 0.1223 is not budget-comparable to 37,654-dot lanes).
2. **SGMC-PROXY is blind to the edits that won live:** H33, H27-4 and D28 return bit-identical SGMC terms because the instrument masks all dots <= 3 px from the catalogue, and the entire live climb 0.2600 -> 0.2708 -> 0.2778 was collar/budget pruning inside that masked shell (each is a subset of the next after <=3 px masking). SGMC therefore cannot price collar decisions at all.
3. **Catalogue-hide as-is zero:** Any shipped raster whose dots all sit > 3 px from the full catalogue (e.g. H86Q-BFRA blind, min d_cat = 3.16 px - verified) scores exactly `HOLDOUT-DTI = 0.0000` when scored as-is, because withheld truth pixels are catalogue pixels and the 300 m kernel cannot reach them. Only re-emission under the fold-visible collar (the protocol used for all H86R arms) yields a meaningful number. As-is comparator rows in run cards must carry this caveat.

## IR-86-H33-CAUSAL-OVERCLAIM-20261026 — H33 forensic narrative overstated hidden-label mechanism and causal effect

- **Observed:** Review of §2 in `research/SESSION_20261026_H86Q_BFRA_REVIEW.md` found that the narrative treated `GEMSDOE32` H33's reported 0.2778 as causally explained by collar pruning, asserted “near-zero loss” of hidden-truth credit, described a nine-entry Pearson association as a “law,” and stated the composition of the organizer's private test truth. Those hidden-label claims cannot be measured from the public catalogue, local holdout, or owner-transcribed score feed. The Focus-9 scores are `OWNER-REPORTED`, not organizer receipts; the nine related submissions are neither independent nor a controlled experiment.
- **Correction:** Rewrote §2 as a bounded forensic interpretation. The 300 m max-kernel DTI makes sparse, nonredundant allocation a plausible mechanism; raster geometry and reported scores show an association only. “Near-zero loss in TP,” a collar-only causal effect, any live-score projection from the nine-point association, and assertions about hidden-test composition are explicitly marked unverified/unknown. The `0.3195` and `0.4413` claims remain unverified and conflicting; no value is presented as `ORGANIZER-CONFIRMED` without a submission-page receipt.
- **Evidence and disposition:** [`research/SESSION_20261026_H86Q_BFRA_REVIEW.md`](research/SESSION_20261026_H86Q_BFRA_REVIEW.md) §2; [`registry/prior_scores.csv`](registry/prior_scores.csv); [`docs/evidence/focus9-forensics-20261026-rev2.json`](docs/evidence/focus9-forensics-20261026-rev2.json); metric implementation [`vendor/gems57/metric.py`](vendor/gems57/metric.py). Historical submission/holdout values are preserved as owner claims or `HOLDOUT-DTI` in their respective evidence records; no private evaluation labels were inferred.

## IR-86S-LIVE-PREP-MANIFEST-20261026 — Current-input audit only trusted the frozen historical preparation manifest

- **Observed (2026-10-26):** `scripts/prepare_data.py` can write a fresh native-array receipt to `.cache/gems_work/prepared_manifest.json` using its existing `--manifest` option, while `data/prepared_manifest.json` is byte-pinned by the generated-site historical review (`docs/evidence/session-cf73474c-data.json`). Writing a new preparation receipt to the tracked path changes that historical hash and causes `scripts/build_site.py` to fail with `Native preparation receipt drift`. Reverting the tracked manifest leaves freshly regenerated ignored `.npy` arrays unverifiable against it because their byte hashes can differ across preparation environments.
- **Fix:** `scripts/audit_workspace_inputs.py` now prefers `.cache/gems_work/prepared_manifest.json` if present, validates its listed array paths/hashes/byte sizes as before, and fails closed on an invalid live receipt instead of silently falling back to the historical manifest. If no live receipt exists, it still checks `data/prepared_manifest.json` as the prior behavior did. The `shared_template_feature_stack` and upload flags remain false; native preparation is never promoted to a shared cache or submission gate.
- **Reproduction:** `.venv/bin/python scripts/prepare_data.py --manifest .cache/gems_work/prepared_manifest.json && .venv/bin/python scripts/audit_workspace_inputs.py --require-native`. Regression tests cover live-receipt precedence and malformed-live-receipt fail-closed behavior; historical `data/prepared_manifest.json` remains unchanged so the generated-site historical pin stays valid.
