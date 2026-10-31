# Session review — branch `arena/daf34cc5-gemsdoe86` (2026-10-30 UTC)

**Decision: DO NOT SUBMIT.** No candidate was generated, no experiment was run, no DrivenData slot was used, and no file in `docs/downloads/` was added or changed.

This review corrects one stale blocker in the README header, documents the one literal gate that makes every new unique TIFF fail, and lists the decisions the owner needs to make. Every number below comes from a command run in this session. Nothing is a projection, and no leaderboard score was checked.

## 1. What was run and what it returned

| Check | Command | Result |
|---|---|---|
| Environment | `python3 -m venv .venv && pip install -r requirements-lock.txt` | installed (numpy 2.4.6, rasterio 1.4.4, scikit-learn 1.9.1) |
| Template pin | `sha256sum -c vendor/template66/TEMPLATE_SHA256.txt` | exit 0, 11 of 11 files OK |
| Test suite | `pytest -q` | **1203 passed, 24 skipped**, 58 subtests passed, 0 failed (526 s) |
| Download integrity | `scripts/check_site.py` | PASS: pages links, registered TIFF/ZIP integrity, negative-state safety |
| Download integrity | `scripts/audit_downloads.py` | PASS: 50 research TIFFs and receipts revalidated; decision remains DO NOT SUBMIT |
| Release audit | `scripts/audit_release.py` | `audit_ok: true`, 50/50 artifacts locally valid, `experiments_run: 0`, `submission_slots_used: 0` |
| Input restore | `scripts/restore_data.py` | OK: `training_features.tif`, `existing_faults.tif`, `sample_submission.tif` SHA-256 verified |
| Witness restore | `scripts/restore_data.py --include-registry` | OK: `data/registry/dense-witness.tif` restored (25,065,181 bytes) |
| Preflight | `scripts/protocol_preflight.py` | `status: STOP_LITERAL_OVERLAP_UNSATISFIABLE` (details in §3) |

Sources for the inputs (all in `scripts/restore_data.py`):
- Feature mirror: `https://codeload.github.com/buffedlizard55-lab/GEMSDOE/tar.gz/c0c06ac82178f26b94fce3397036ef8f12a2f3a0`
- Witness source blob: `https://api.github.com/repos/buffedlizard55-lab/17GEMSDOE/git/blobs/374c88b1da2b803e2ed160de467fd71ae114010d` (`docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif`)
- Registry index: `https://github.com/buffedlizard55-lab/60GEMSDOE/blob/b99591eede63c6d45c8a896255b8cd34824fa00b/evidence/registry_full_index.json`
- Official competition data page (login-walled, **not** fetched, per `AGENTS.md` item 9): `https://www.drivendata.org/competitions/306/competition-doe-gems/data/`

These are mirrors by other repositories of the same owner. The SHA-256 match proves byte identity with the pinned mirror. It does **not** authenticate the DrivenData originals.

## 2. Correction: the "native raster missing" blocker is stale

The README header (2026-10-29 session) says the training raster and witness were missing. In this checkout, the verified restore succeeds. Both files are present and git-ignored (`.gitignore:36`, `.gitignore:15`). The shared feature cache (`.cache/`) and the vendored `vendor/template66/gems/` contents still need checking before any model is trained.

Band-grid check (read-only, rasterio):

| File | Bands | Size | Dtype | CRS | Transform |
|---|---|---|---|---|---|
| `data/bridge/training_features.tif` | 19 | 3292 × 3730 | float32 | EPSG:32611 | (100, 0, 243350, 0, −100, 4508550) |
| `data/bridge/sample_submission.tif` | 1 | 3292 × 3730 | float32 | EPSG:32611 | same |
| `data/registry/dense-witness.tif` | 1 | 3292 × 3730 | float32 | EPSG:32611 | same |

The submission grid, CRS, and geotransform match the sample submission exactly.

## 3. The blocking gate (literal, unchanged)

`protocol_preflight.py` reports:
- `witness_sha256 = ab0a0a62…872be`, `positive_pixels = 5,167,373`
- `allowed_pixels = 5,106,385`, `uncovered_allowed_pixels = 0`, `covered_allowed_fraction = 1.0`
- Support rule: finite prediction > 0. Overlap limit: 0.70, unchanged.
- Implication: any nonempty candidate has 3-px forward overlap **1.0** against this witness, which is above 0.70.

So under the repo's literal rule, **no new TIFF can pass uniqueness**, whatever its mechanism. The witness is positive on the entire allowed footprint, so the rule measures the witness's coverage, not the candidate's dot placement. `IRREGULARITIES.md` line 6 already documents this as a design problem. The current session confirms it on the restored bytes. The organizer's rule set does not contain this uniqueness gate; it is an internal protocol. Changing it is the owner's decision. This session did not change it.

What the owner must decide (choose one, and write it down before any candidate is built):
1. Make the witness representation sparse (e.g., the witness's top-37,654 cells). `IRREGULARITIES.md` reports this gives 0.0356–0.0495 for H33, GEMSDOE31, and GEMSDOE36 as a **diagnostic only, not a gate pass**.
2. Exempt dense continuous witnesses from the literal rule and replace it with a documented rank-based or top-k rule.
3. Keep the literal rule. Then no candidate can be marked unique, and the honest conclusion is that no unique TIFF can be cleared.

## 4. Irregularities flagged for review

1. **Band labels disagree with the repo's own physics verification.** `training_features.tif` band descriptions say band 6 is "tilt angle or total curvature", band 5 is "gravity slope", band 11 is "vertical gradient", and band 18 is "horizontal gradient". `src/gems86/io.py` `BAND_PHYSICS_VERIFIED` (backed by `docs/evidence/band-physics-verification-20261024.json`) says band 6 is GeoDAWN total count, not magnetic tilt; band 5 is an unsigned gradient magnitude; band 11 is a signed southward derivative; band 18 is a signed eastward derivative. Any model that trusts the file descriptions will be mislabeled. Use the verified overrides, not the descriptions.
2. **Leaderboard figures conflict.** The user supplied 0.4413 and 0.3195 as the current top score. The repo records both as unverified claims (`IRREGULARITIES.md` line 38). This session could not check either, because the DrivenData leaderboard is login-walled and automated access is prohibited by `AGENTS.md` item 9. The current top figure is therefore **unresolved**.
3. **GEMSDOE32 0.2778 is an owner claim, not a receipt.** The repo ledger has no submission-page receipt that binds it to the exact bytes.
4. **Stale README blocker** (corrected in §2).
5. **Nine-site overlap.** Per the README table, every historical top file for the nine requested sites fails the 0.70 overlap rule against at least one peer (overlaps 0.9758–1.0000). None is cleared for submission.
6. **Sandbox policy.** Feature and witness mirrors come from other owner repositories, not from DrivenData, and the sandbox cannot reach DrivenData or Dropbox. Training on this data is for research only.

## 5. Estimate table (required by the owner)

| Site | Historical file to download (audit only) | Owner-reported score | Organizer score | Unique? | OK to submit? |
|---|---|---|---|---|---|
| GEMSDOE32 (highest owner claim) | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | 0.2778 (unverified) | not estimable | **NO** (1.0000 vs GEMSDOE36) | **NO** |
| This session's new candidate | none generated | — | not estimable | not testable under literal gate | **NO** |

Full nine-site table: see the README executive table. The README also lists each file's max peer overlap.

## 6. Run card (no experiment was run)

```json
{
  "session": "arena/daf34cc5-gemsdoe86",
  "date_utc": "2026-10-30",
  "hypothesis": "none tested; review only",
  "mechanism": "n/a",
  "non_fault_mimic": "n/a",
  "holdout_dti": "not measured (HOLDOUT-DTI not computed; no candidate built)",
  "registry_overlap": "witness 17GEMSDOE: 1.0 forced for any nonempty candidate (literal rule)",
  "raster_sha256": "none generated",
  "validator": "not run (no candidate)",
  "submission_name": "none",
  "verdict": "negative",
  "safe_to_submit": false,
  "experiments_run": 0,
  "submission_slots_used": 0
}
```

## 7. Recommended next steps (for the owner)

1. Decide the witness representation rule (§3) in writing. This is the only blocker to a unique TIFF.
2. Build the shared feature cache from `training_features.tif` using the verified band map (§4.1), and run the leakage canary on each feature alone before any model is trusted.
3. Confirm the top leaderboard score from a human browser receipt (not automated access). Record it in `ledger/submissions.csv`.
4. Keep the README's 2026-10-29 header only as history; this review supersedes its "missing raster" statement.
