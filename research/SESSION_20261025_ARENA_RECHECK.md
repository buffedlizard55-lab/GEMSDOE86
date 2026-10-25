# Repository recheck — 2026-10-25

## Decision

**Negative / DO NOT SUBMIT. No model experiment, TIFF candidate, weekly submission slot, or organizer upload was made.** This check confirms the existing fail-closed disposition; it does not satisfy the request for a new unique submission TIFF.

## Three-pass review

### Pass 1 — repository state and governing instructions

- Re-read `AGENTS.md`, `PROMPT.md`, the latest README decision, and `research/REQUEST_20261025.md`.
- The current request does not specify one assigned method paragraph. `registry/h86g_hypotheses.json` lists four ranked proposals, all explicitly `NOT_RUN_PROTOCOL_STOP`; these are research ideas, not a lane authorization.
- The actual shared template feature cache is not present. Native competition-band preparation is not an equivalent substitute.
- `docs/evidence/protocol-preflight.json` records the hash-pinned dense witness as positive at every allowed pixel (`uncovered_allowed_pixels = 0`). Under the inherited literal support rule, any nonempty candidate would have forward overlap 1.0 against the 0.70 limit. This is sufficient to stop, but not to certify a complete uniqueness scan; `registry_complete` is false.
- The user-supplied historical score claims remain unverified absent an organizer submission receipt. No DrivenData site was accessed or scraped.

### Pass 2 — local remeasurement and corrective action

Initially the required evidence commands could not start because the checkout had no installed NumPy and omitted `data/sample_submission.tif` / the immutable witness. Installed the repository's pinned `requirements-lock.txt` into the ignored `.venv/` and restored the integrity-pinned protocol inputs via `scripts/restore_protocol_data.py --include-registry`. The script verified the Git blob identity, pinned SHA-256 and byte lengths. These files are owner-mirrored inputs; the receipt explicitly does **not** authenticate them as organizer-origin bytes.

Ran `scripts/protocol_preflight.py` and `scripts/audit_release.py --measure-registry`. The preflight reproduced the negative witness finding. The release audit returned `audit_ok=true`, decision `DO NOT SUBMIT`, 18/18 inherited artifacts locally format-valid, zero experiments, and zero slots. An initial `build_site.py --check` correctly found generated pages stale after the fresh evidence timestamps changed; rebuilt them from the evidence generator.

The first full test run then exposed one stale generated `session-cf73474c-run-card.json`: its frozen timestamp and evidence hashes no longer matched the fresh audit inputs. Rebuilt it with the existing `scripts/build_review_card.py`, rebuilt the site, and reran all checks. This was a generated-evidence freshness issue, not a scientific result or code change.

### Pass 3 — final verification

| Check | Result |
|---|---|
| `.venv/bin/python scripts/protocol_preflight.py` | PASS; literal overlap stop reproduced; candidate not generated. |
| `.venv/bin/python scripts/audit_release.py --measure-registry` | PASS; `DO NOT SUBMIT`, 18/18 inherited local-format checks, 0 experiments, 0 slots. |
| `.venv/bin/python scripts/build_site.py --check` | PASS after evidence-generated rebuild. |
| `.venv/bin/python scripts/check_site.py` | PASS; Pages links, registered TIFF/ZIP integrity and negative-state safety only, not scientific clearance. |
| `.venv/bin/python -m pytest -q` | **802 passed, 24 skipped, 42 dependency deprecation warnings, 41 subtests passed** in 230.07 s. |
| `git diff --check` | PASS. |

Changes from this recheck are limited to freshly measured audit timestamps/hashes, the derived run card, and regenerated page timestamps/content. No method, evaluator/writer, thresholds, historical model card, candidate TIFF, or slot was changed.

## Answer to the H33 question (scope and uncertainty)

The `0.2778` H33 value in the request is **OWNER-REPORTED**, not ORGANIZER-CONFIRMED in this repository. The archived H33 pixel-lineage analysis says the H33 raster is the parent pattern minus 2,545 dots in a two-pixel catalogue collar, with no added dots. That supports a plausible metric/coverage explanation: under the competition's localized, asymmetric fault-coverage objective, removing redundant catalogue-adjacent predictions can improve a finite-budget spatial coverage score. It does not prove this caused the reported portal score, establish holdout-to-leaderboard calibration, or imply a new method will exceed it. The supplied 0.3195 and 0.4413 leaderboard claims likewise lack a receipt in the checked evidence and are not treated as verified numbers.

No valid candidate was tested, so this review cannot claim to beat H33, the supplied reported leaderboard figure, or the same-split holdout best. Prior distinct hypothesis proposals and their status are preserved in `registry/h86g_hypotheses.json` and prior research notes; no fake score or projection was added.

## Remaining blockers / next work

1. Resolve the literal saturation contradiction through an explicitly authorized protocol amendment; do not privately change the 0.70 rule or reinterpret a format pass as clearance.
2. Obtain and hash-bind the actual shared cached feature stack and its preprocessing/footprint identity.
3. Reconcile the two grid-incompatible entries in the pinned registry inventory under an explicit policy; do not silently drop, warp, or repair them.
4. Assign a single method paragraph. Then preregister a maximum-three-experiment / two-hour design, use the shared holdout/evaluator/writer, and run individual-feature leakage canaries before interpreting any result.
5. Only after a same-split holdout improvement and passing pre-placement and final-dot registry gates should a candidate file be treated as an upload candidate. A submission-page receipt is still required for organizer-confirmed scores.

## Run card

```json
{
  "hypothesis": "H86G-CSPA remains the top qualitative proposal only; no method lane was assigned or run.",
  "mechanism": "No mechanism tested. The proposal's local cross-spectral gravity-magnetic admittance-break signature remains unvalidated.",
  "named_non_fault_process": "Unfaulted lithologic juxtaposition, source-depth changes, remanent volcanic magnetization, or mismatched survey resolution could mimic the proposed signature.",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "status": "NOT_RUN_NO_LANE_ASSIGNED",
    "evaluator_version": "gems57-pooled-hide-v2 (planned; not executed)",
    "withheld_positive_count": null,
    "value": null,
    "ci95": null
  },
  "correlation_overlap_vs_registry": {
    "evidence_class": "REGISTRY-MEASUREMENT",
    "candidate_surface": "NOT RUN",
    "candidate_final_dots": "NOT RUN",
    "historical_witness_forward_support_overlap": 1.0,
    "limit": 0.70,
    "scope": "Single immutable witness is sufficient to stop; inventory incomplete and no candidate uniqueness claim."
  },
  "raster_sha256": null,
  "validator_output": {
    "new_raster": "NOT GENERATED",
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null
  },
  "submission_name": null,
  "note": "No new candidate generated; all inherited TIFFs remain audit-only. DO NOT SUBMIT.",
  "verdict": "negative"
}
```
