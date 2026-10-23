# IRREGULARITIES — only items that change a decision

## IR-86-PRUNE-01 — the lineage is reproducible as dot sets, not as file bytes (decision: key the ledger on a dot-set digest, not only on sha256)

**Observed.** R0's support is reproduced exactly: the 0.2708 field (40,199 dots) minus every dot
at Euclidean distance ≤ 2.0 px from a mapped fault = 37,654 dots, **0 pixels differing**. Its
file bytes are not reproducible in this environment: the published raster is 219,065 B (tiled
256, deflate), and 30 re-encode profiles (tiled/striped × deflate/lzw/none × predictor 0–3 ×
zlevel 1–9 × band description on/off) produced 142,955–51,120,012 B and never the same sha256.

**Decision changed.** "Rebuild R0 and match its sha256" cannot be satisfied literally, and per the
brief I did not approximate the parent: I reproduce its *dot set* (identity proven by equality of
all 12,279,160 band-1 cells, and by an identical dot-set digest) and record **both** identities for
every child. A future session that needs byte identity must record its writer profile *at build
time*; it cannot be recovered from the bytes afterwards. Consequence: exact-hash dedupe alone would
have missed a real duplicate of a dot set written by a different GDAL build.

## IR-86-PRUNE-02 — the 0.2708 parent field has no upstream pin in this checkout (decision: variants derive from R0 only)

`data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-…-nan.tif` (sha256 `ab0230015224…`) is
not in `registry/data_manifest.json`, not in `data/restore_receipt.json`, and not in
`buffedlizard55-lab/GEMSDOE28`'s `data/manifest.json` (checked via `api.github.com` on 2026-10-23).
It is used **only** to re-derive and thereby test the prune rule. No release depends on it: every
candidate is a strict subset of the pinned R0 raster, so the shipped bytes depend only on
`existing_faults.tif`, `sample_submission.tif` and R0 — all three sha256-verified at run time.

## IR-86-PRUNE-03 — the repo's standing literal-overlap stop and the brief's "build variants" instruction conflict (decision: build, do not authorize)

`PROMPT.md` / `AGENTS.md` / `scripts/protocol_preflight.py` make every nonempty candidate fail a
literal 70 % overlap gate against a pinned full-positive registry witness, and forbid a format pass
from authorizing a weekly slot. This session therefore builds and validates rasters but sets
`approved_for_weekly_slot=False` and uses no slot. That is a *human* decision, and I did not weaken
or bypass the preflight. **This conflict will block every future variant too**; resolving it (a
stated registry-completeness policy or an explicit owner exception) is a prerequisite for any
session that is expected to produce a submittable file.

## IR-86-PRUNE-04 — the catalogue hide-and-recover proxy is structurally invalid on this axis (decision: never rank collar edits by it)

Measured on the same 10 draws: R0 `0.004356 [0.0041, 0.004577]`, rung √5 `0.000447`, rungs √8 and
3.0 px `0.000000`. The proxy rewards collar dots *because* they are near the catalogue, while the
one live datum on this axis says collar dots cost score. The brief already says a PROXY is never a
gate; this is the concrete counterexample and it is recorded in `evidence/prune_ladder.json`.

## IR-86-PRUNE-05 — axes that the brief expects are not executable here (decision: PRUNE only, and say so)

`SNAP` and `RELIEF` need bands of `training_features.tif` (absent: 419 MB, pinned, public, fetchable
— verified HTTP 200, not downloaded this session); `MASS` needs the parent's stored ranking (not
stored) and `CONCENTRATION` needs a km-scale prior surface (same stack). The human assigned no AXIS
in this session's brief, so PRUNE was chosen as the only listed axis whose inputs are all present
and pinned. Everything else is deferred to `SLOT_PLAN.md` rather than approximated.
