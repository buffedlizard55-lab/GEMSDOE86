# IRREGULARITIES — items that change a decision

Only entries that changed what this session did, or that a human must resolve before the
next slot. One line each: what conflicts, what was decided, what it costs.

## IR-86-PRUNE-01 — the repo's standing protocol forbids every submission; brief v2 forbids the gate
`PROMPT.md` / `AGENTS.md` / `scripts/audit_release.py` apply a **70 % overlap** and
**0.90 rank-correlation** uniqueness rule against a pinned registry witness that is positive
at every allowed pixel. That witness makes forward overlap 100 % for *any* nonempty
candidate, so under the standing rule nothing is ever submittable (the repo has recorded
this as a universal blocker and spent no slots on it). Brief v2 §6 says the opposite:
*"Do NOT apply rank-correlation or dot-overlap 'uniqueness' thresholds."*
**Decision:** this session followed brief v2 for its own work products — no overlap
threshold was applied, and dedupe used exact-sha256 and repeated `(parent, axis, value)`
only. The existing gate scripts were **not** modified, relaxed, or bypassed, and this
session authorises **no** slot. **Cost:** the human must decide which rule governs before
any submission; the two cannot both be true.

## IR-86-PRUNE-02 — the parent cannot be rebuilt from its recipe in this checkout
Brief v2 §5 says rebuild R0 and match its sha256, or stop. `research/upstream/run_h33.py`
imports `gems32.*` (holdout, h33, bo, paths); that package is not present in this
repository. The 19-band stack and the five external rasters *were* restored and hash-verified,
but the recipe itself is missing.
**Decision:** R0's identity was established by the **pinned sha256** `c55bafc4…b6fa9`
(identical to `scripts/fetch_registry.py` `EXTRA[0]`, repo `buffedlizard55-lab/GEMSDOE32`
ref `780a5a53…`), not by re-execution; the parent was never approximated or edited. The MASS
axis was dropped because it needs the parent's stored ranking, which does not exist here.
**Cost:** MASS/RELIEF stay blocked until `gems32` or a stored ranking arrives.

## IR-86-PRUNE-03 — the catalogue hide-and-recover PROXY is at its floor for this lineage
Measured: R0 scores PROXY DTI 0.00436 and every pruned variant 0.00000, because a
catalogue-avoiding field earns almost no credit from withheld catalogue pixels. The
instrument therefore cannot rank a collar change, and its published correlation with live
scores is sign-unstable (−0.87 … +0.54, n = 12–14).
**Decision:** the proxy is reported in full and used **only** as a negative control; no
prediction or gate depends on it. Predictions rest on the label-free ring/feature
measurements and the exact marginal algebra instead. **Cost:** this axis has no local
instrument that can confirm it — the live slot *is* the measurement.

## IR-86-PRUNE-04 — competition rasters are committed in a public repository
`data/bridge/existing_faults.tif` (byte-identical to `labels.tif`) and
`data/bridge/sample_submission.tif` are tracked in this public repo, along with 26 derived
`.tif` files in `data/scored_fleet/`. Brief v2 §2 says to keep competition rasters out of
public repos and to flag it, because the data-use terms are unchecked.
**Decision:** no new competition raster was committed. The 418 MB restored feature stack is
explicitly git-ignored (`/data/bridge/training_features.tif`). The releases in `releases/`
are derived prediction rasters, not competition data. **Cost:** the human must confirm the
data-use terms and decide whether the tracked bridge rasters should be removed from history.

## IR-86-PRUNE-05 — no valid target number exists
`TOP_PUBLIC` is blank; the owner prompt quotes 0.3195 and then 0.4413 as leaderboard maxima,
undated and without receipts. The competition page cannot be fetched from this sandbox
(DrivenData's terms ban automated access).
**Decision:** no target was invented and no score comparison was made. Progress is reported
against R0 = 0.2778, class **CLAIM**. **Cost:** "beat TOP_PUBLIC" cannot be evaluated until
the human supplies a dated number.

## IR-86-PRUNE-06 — the (PRUNE, 3.5) pair is already spent on another parent
`GEMSDOE77` `gems85-h85-edti-collar35-skel-r33` (owner-reported 0.0964) already built a
3.5 px collar, on a skeleton/`r33` parent whose own baseline is unknown.
**Decision:** value 3.5 was not rebuilt (one build per `(axis, value)`), and values 3, 4 and
`3r` were used instead. The 0.0964 number says nothing about R0, because it is confounded
with a much weaker parent. **Cost:** the collar curve will have a gap at 3.5 px.

## IR-86-PRUNE-07 — the brief wants NaN outside the footprint; the repo's validator forbids any NaN
Brief §6 lists "NaN outside the footprint" as a MUST gate. `vendor/gems57/validate.py` runs
the opposite convention (`no_nan_anywhere`, `outside_footprint_zero`) as a deliberate
conservative local policy after the portal's earlier "values must be in range [0, 1]" error.
The two rules cannot both hold for one file.
**Decision:** every variant ships **both** forms under distinct names and distinct digests.
The `-nan` twin satisfies the brief; the `-zeros` twin additionally clears the repo's
validator (`all_checks_passed = True`) and `gates.format_report` (`ok = True`). The human
uploads **one** per slot — the `-zeros` twin if the portal rejects the `-nan` one on range.
**Cost:** one extra file per variant, and one decision left to the human at upload time.

