# GEMSDOE86 repository review — 2026-10-24

## Decision

**No new TIFF was generated in this review; no file is authorized for competition upload.** The repository already contains unique-by-bytes research TIFFs, including H86E-MMT, but they are explicitly audit-only and failed scientific and/or registry gates. A different file name or a changed byte hash would not establish registry uniqueness or scientific merit. No weekly slot was used and no organizer receipt is present.

This is a review-only outcome, not a new geological experiment. The current request does not identify one lane/method paragraph, and required shared inputs are missing locally: the actual cached feature stack, a contemporary complete cross-lane registry, and a matched current-best holdout baseline. Accordingly, I did not build substitute features, fit a private model, place dots, or bypass the shared preflight.

## Three-pass review

### Pass 1 — prompt, repository, and provenance

- Read `AGENTS.md`, the complete `PROMPT.md`, `README.md`, the archived current user request, the latest H86E-MMT preregistration/review, H86E-RIDF review, and the current machine-readable readiness/run cards.
- Confirmed that the full user-request archive exists in `research/REQUEST_20261024.md` and is linked from the README. It is input, not verified evidence. The supplied fleet values—including GEMSDOE32 `0.2778` and conflicting leaderboard values—remain owner-reported unless a DrivenData submission receipt exists.
- Confirmed the shared vendored evaluator/writer pin matches its pinned bytes. The competition grid mirrors are locally present and hash-verified. `data/prepared_manifest.json` explicitly says `has_features: false`; `data/training_features.tif`, `data/work/h86e_features.npy`, and `data/registry_ext/` are absent. A raw mirrored feature TIFF is not the template's cached feature stack.
- Reviewed the existing download inventory: TIFFs and ZIPs are provided for audit, while the top-level site/README and sidecars state **DO NOT SUBMIT**. The previously created H86E-MMT artifact is not a fresh artifact from this review and is not promoted here.

### Pass 2 — fail-closed protocol check and adversarial interpretation

- Ran the repository's integrity-pinned restorer with `--include-registry`. It restored only the competition grid mirrors and the immutable historical registry witness; its receipts explicitly mark the mirrors as not organizer-authenticated. It did not restore the 419 MB feature raster or recreate a feature cache.
- Ran `scripts.session_preflight.run(write=False)` so the check did not overwrite generated evidence. Grid checks passed: EPSG:32611, shape 3730×3292, the pinned 100 m transform, 5,167,373 footprint pixels, and byte hashes matching the pinned owner mirrors.
- The pinned witness is `17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif`, SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`. Its positive support covers all 5,106,385 allowed cells (direct uncovered count 0). Under the request's **literal** support/overlap reading, any nonempty subset of those allowed cells has 100% forward overlap with that witness, exceeding the 70% stop threshold. This is sufficient to stop literal clearance; it is not evidence that geological mechanisms are identical.
- Scope caveat: this witness-only preflight explicitly reports an incomplete registry (`registry_complete: false`, one raster measured from a 655-entry snapshot). It is enough for a negative under the literal rule, never enough to certify uniqueness. The separately documented PA-86-01/02 like-for-like procedure distinguishes continuous surfaces and dot fields, but it still requires a complete available registry and a new candidate's pre-placement and final-dot checks; it does not grant this review a pass or authorize weakening the user's threshold.
- Previous H86E-MMT results are preserved as `HOLDOUT-DTI`, evaluator `gems57-pooled-hide-v2`, 11,321 withheld positives; MMT's candidate was below its preregistered control and its post-placement PA test failed. Those archived results are not new measurements here and are not leaderboard scores.

### Pass 3 — reproducibility and release/UI safety

Commands run from the repository root:

```text
.venv/bin/python -m pytest -q --durations=20
  640 passed, 24 skipped, 42 warnings, 41 subtests passed (194.49 s)
.venv/bin/python scripts/audit_release.py
  audit_ok=true; decision=DO NOT SUBMIT; 15/15 locally valid; all final artifacts remeasured;
  0 experiments and 0 slots used by this read-only release audit
.venv/bin/python scripts/build_site.py --check
.venv/bin/python scripts/check_site.py
  PASS: generated-site consistency; Pages links and registered TIFF/ZIP integrity;
  negative-state safety (not scientific clearance)
```

The first full-test invocation was stopped by the tool timeout before a summary was emitted. It was rerun with a longer timeout and completed successfully as shown above. The 42 warnings are Rasterio `PendingDeprecationWarning` notices about affine multiplication; they did not fail tests. An initial attempt to install system-wide was rejected by PEP 668; dependencies were installed in the ignored `.venv/` from `requirements-lock.txt`.

## Answer to the H33 / score question

GEMSDOE32 `0.2778` is an owner-reported claim in the supplied prompt, not an organizer-confirmed receipt in this repository. Prior documented raster forensics suggest H33 is in the H19-5 multiline-ridge lineage, with dot emission and a catalogue-distance pruning change. The plausible metric mechanism is the competition's nonlinear 300 m kernel credit: changing spatial distribution and redundancy can matter even when a surface is otherwise similar. That is a mechanism hypothesis, not causal proof of the reported score. The repository's previous analysis explicitly finds that its hide-and-recover holdout has not been calibrated to leaderboard ranking; therefore no claim that a new holdout value beats 0.2778 or the claimed 0.3195/0.4413 is justified.

## Hypotheses on file and what remains viable

The repository already has a 3–5-arm preregistration (`research/H86E_MMT_PREREGISTRATION.json`) and a separately ranked RIDF proposal table (`research/H86E_RIDF_REVIEW.md`). Their top magnetic-marker-translation candidate was run and rejected; the next gravity/basement paired-throw extension is explicitly unrun, but the actual cached feature stack is absent and no lane was assigned in this request. Re-running the old three-arm design would exceed its already-spent budget; starting a distinct lane needs a new contemporaneous preregistration, complete input pins and a clear preflight. The RIDF review's external NBMG map-fault idea was already marked unobtainable from this sandbox. No new external source is proposed as viable without byte-level acquisition and pinning.

For a next authorized session, the highest-value work is not another emission variant: (1) agree on a scientifically defensible, representation-aware registry protocol without silently changing thresholds; (2) restore and hash-bind the actual shared cache and a contemporary complete registry; (3) preregister a single distinct physical mechanism and a matched spatial holdout/control; (4) calibrate holdout ranking against actual organizer receipts before claiming leaderboard improvement; and (5) only then run no more than three experiments and keep all negative results.

## Official/source links already registered for review

- [Competition problem, metric, and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — automated access is not used in this review; prior archived source observations are dated.
- [Competition rules and entry page](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN dataset](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE/NREL GDR INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391)
- [USGS Nevada magnetic compilation](https://pubs.usgs.gov/ds/2006/234/)
- [USGS magnetic interpretation guidance](https://pubs.usgs.gov/fs/fs-0236-95/fs-236-95.pdf)
- [EPSG:32611](https://epsg.io/32611)

## Run card (this review; no candidate generated)

```json
{
  "hypothesis": "No new geological lane was run; the previously tested H86E-MMT marker-translation hypothesis remains negative and unpromoted.",
  "mechanism": "Review-only: no new surface or placement. H86E-MMT previously tested non-zero-lag magnetic marker gradients with total-count decoupling.",
  "named_non_fault_process": "Unfaulted lithologic/intrusive contacts, remanent volcanic polarity, and flight-line/tie-line seams can mimic the archived MMT signature.",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI (archived, not remeasured in this review)",
    "evaluator_version": "gems57-pooled-hide-v2",
    "withheld_positives": 11321,
    "candidate": 0.0290016,
    "ci95": [0.0205505, 0.0381435],
    "note": "H86E-MMT archived result; not a leaderboard score."
  },
  "correlation_overlap_vs_registry": {
    "evidence_class": "REGISTRY-MEASUREMENT",
    "candidate_surface": "NOT RUN",
    "candidate_final_dots": "NOT RUN",
    "preflight_witness": "SHA-256 ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be covers all allowed cells; literal forward overlap for any nonempty subset is 1.0",
    "registry_scope": "One immutable witness measured; complete current registry not restored, so no uniqueness clearance."
  },
  "raster_sha256": null,
  "validator_output": {
    "no_nan_inside_footprint": "NOT RUN — no new raster",
    "values_in_0_1": "NOT RUN — no new raster",
    "crs_shape_transform_match": "Input grid mirrors hash-verified; no new prediction raster"
  },
  "submission_name": null,
  "note": "Review only; no new TIFF generated; existing downloads remain DO NOT SUBMIT.",
  "verdict": "negative"
}
```
