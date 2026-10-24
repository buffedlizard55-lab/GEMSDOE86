# 2026-10-24 — repository review, refreshed fleet feed, and three-pass verification

## Decision

**Negative for new submission.** No new model experiment, candidate surface, dot placement, TIFF, slot selection, or organizer submission was made. The prescribed pre-placement gate is unsatisfiable under the repository's unchanged literal overlap rule, so continuing to feature tests or placement would violate the project protocol. Existing TIFFs remain audit-only; none is approved for submission.

This review follows `PROMPT.md`, the full README request archive, `AGENTS.md`, and the session's parallel-run rules. The owner-provided score values (including H33 `0.2778` and the competing claimed current highs `0.3195` and `0.4413`) remain **claims**, not ORGANIZER-CONFIRMED results: no submission-page receipt or authenticated leaderboard observation was obtained here. The automatically refreshed fleet is repository metadata, not a score or raster validator.

## Pass 1 — inspect requirements and current implementation

- Read the standing prompt, README decision, archived request, effective template pin, lane preregistration, current hypothesis register, current run card, release audit, and preflight implementation.
- The request's asserted “single method paragraph” is not supplied as a separately unambiguous lane assignment. Existing records conflict: `registry/preregistration.json` records `RMRB-86`, while `registry/h86c_hypotheses.json` is expressly planning-only and the repository also contains later independently completed lanes. **Lane-assignment ambiguity remains an irregularity; this review does not choose a new lane or combine lanes.**
- The mandatory shared cached feature stack is absent. Owner-mirrored competition rasters and historical registry TIFFs do not equal that cache. The cached-stack requirement therefore cannot be met by rebuilding locally.
- The registered three-item hypothesis shortlist is retained as planning, not a newly run experiment or measured gain ranking. The ranking below is qualitative information-gain-per-cost only.

| Rank (qualitative) | Hypothesis; exact inputs and signature | Why it could detect an unmapped fault; difference from implemented work | Main non-fault mimic | Cost / readiness |
|---|---|---|---|---|
| 1 | **Cross-fault magnetic marker translation (H86C-MMT):** competition RTP and TMI. Estimate stable along-line translation of transverse magnetic texture between opposite flanks using bounded phase correlation; require adjacent-window consistency and compare against zero-shift controls. | Tests displacement of image-internal markers rather than extending a known catalogue trace or rewarding another magnetic edge. The checked-in GFCO, GMC, WVB, CTHB and other lanes use edge, cross-gradient, wavenumber, contact, or catalogue-tip evidence; none is this flank-to-flank marker-translation test. | Unfaulted intrusive contact with unrelated texture, acquisition seam, or remanent-magnetization contrast. | Medium-high; **not ready** until the actual pinned shared feature stack and seam metadata are restored. No gain measured. |
| 2 | **Signed paired-throw consistency (H86C-SPT):** competition depth-to-base surface, isostatic gravity anomaly, and detrended elevation. Test opposing flank profiles and require compatible downthrown-side polarity across independent fields. | A buried offset could survive where surface lineaments are weak. The distinct test is signed, polarity-consistent flank displacement, not another unsigned edge or cross-gradient score. | Erosional basement escarpment, basin-fill density contrast, or inversion artifact; an old buried offset may not indicate active permeability. | Medium; **not ready** until exact layer sign/datum metadata and the shared stack are authenticated. No gain measured. |
| 3 | **Watershed-crossing scarp persistence (H86C-WCS):** native-resolution USGS 3DEP bare-earth DEM plus competition detr_elev for regional context. Require signed scarps with stable strike and down-side across independently delineated drainage divides; test against channel, shoreline, road, and fan-boundary controls. | Catchment-crossing structural persistence can extend beyond mapped traces without using catalogue distance. The repository's existing relief/scarp lanes do not condition signed steps on independently delineated watershed topology. | Paleolake shoreline, fluvial terrace, road cut, or fan boundary. | High; **not viable yet**. The competition's 1 m DEM-link CSV and required native tiles/coverage/license manifest are absent here. The official free source to check is [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) and, for competition coverage, the [competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/). We did not obtain the CSV or tiles, so access/coverage is not claimed. |

Primary source basis already recorded in the project: [DrivenData problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [DrivenData about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS basement-offset report](https://pubs.usgs.gov/of/1999/0383/), [USGS magnetic-offset report](https://pubs.usgs.gov/pp/1658/pdf/ch5.pdf), and [pinned official reference-solution source](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b). Their evidentiary scope and prior access dates are in `docs/evidence/source-review-20261023.json`; this review did not claim fresh scientific-source retrieval.

## Pass 2 — try the mandatory preflight and review edge cases

The first preflight attempt failed closed because the restorable `data/sample_submission.tif` and `data/existing_faults.tif` were not present at the paths the checker requires (`ModuleNotFoundError` was first resolved by installing the committed lockfile into ignored `.venv/`). We then used the repository's pinned GitHub mirror restorer (`scripts/restore_protocol_data.py --include-registry`), which verifies object identity, SHA-256 and byte count; it explicitly marks the competition mirrors as **not organizer-authenticated**. The ignored TIFF bytes were not added to Git.

The successful preflight remeasured the immutable historical witness and produced `docs/evidence/protocol-preflight.json`:

- One SHA-pinned historical raster is part of the repository's recorded registry snapshot; its coverage is a sufficient **counterexample** to the literal support rule, not proof that the snapshot is complete.
- Its positive support covers every allowed non-catalogue pixel. Under the current literal definition (`finite prediction > 0`), any nonempty candidate support therefore has forward three-pixel overlap `1.0`, above the protocol's `0.70` ceiling.
- This is a pre-placement impossibility result. No candidate raster exists, so candidate rank-correlation, candidate dot overlap, leakage canaries, a candidate HOLDOUT-DTI, and candidate validator results are correctly **not measured**. A synthetic, empty, renamed, or historical TIFF would not satisfy the unique-new-candidate requirement.
- The thresholds were not changed, continuous prior support was not privately exempted, no fork of the shared evaluator/writer was created, and no weekly slot was spent.

## Pass 3 — refresh user-facing status and rerun verification

The feed refresher retrieved the current main-branch Git trees for **88/88 named repositories**, updated `docs/evidence/fleet-feed.json`, and the generated site was rebuilt. This is a Git metadata refresh only: it records **zero** organizer receipts, generated rasters, or slots used. It does not verify raster payloads, historical completeness, leaderboard standing, or organizer acceptance. The updated [fleet feed page](../docs/fleet.html) and machine-readable [feed record](../docs/evidence/fleet-feed.json) explicitly retain those limitations.

Checks run after the feed rebuild:

- `python scripts/audit_release.py --measure-registry`: PASS; the immutable witness and all 10 inherited TIFFs were remeasured. The TIFFs pass local format checks but remain **DO NOT SUBMIT**.
- `python scripts/build_site.py --check`: PASS.
- `python scripts/check_site.py`: PASS; links, TIFF/ZIP integrity and negative-state safety; not scientific clearance.
- `python -m pytest -q`: **336 passed, 24 skipped, 32 subtests passed**, with 4 Rasterio pending-deprecation warnings.
- `git diff --check`: PASS.

The changed files are the refreshed metadata feed and its generated HTML views. No predictor, evaluator, template, registry threshold, submission raster, or score was changed.

## Interpretation and remaining blockers

The H33 `0.2778` figure may be discussed only as the user's owner-reported claim. The repository's causal account is that kernel-scale thinning and catalogue-collar pruning could improve coverage efficiency by reducing redundant false-positive mass while retaining triangular-kernel coverage. This explains a plausible mechanism, **not** why that specific score occurred. It cannot distinguish geological signal from placement geometry, proxy leakage, private labels, or other submission differences without the exact submission receipt, bytes, matched evaluation and controls. The request's two different “current high” values are irreconcilable here; neither is asserted as current organizer-confirmed evidence. No evidence in this review establishes that a new strategy beats either value.

Next work should be gated in this order:

1. Resolve the literal-registry/uniqueness contradiction with an explicit, versioned protocol decision from the project owner/competition context. Do not implement a private dense-raster exception or silently drop registry entries.
2. Assign exactly one method lane in unambiguous text; restore and hash-bind the actual shared feature stack and a current, accessible, representation-aware registry.
3. Only after those gates pass, use the pinned `evaluate_holdout.py` / `submission_writer.py`, buffered whole-segment hide-and-recover, visible-only catalogue features, pixel-exact masks, pooled alpha `0.2` / beta `0.8` / 300 m triangular DTI, per-feature leakage canaries, and paired spatial-block uncertainty. Freeze the holdout best on a matched design before any separate slot-selector step.
4. Obtain and audit official DEM tile bytes, coverage and licenses before reconsidering H86C-WCS. Never call a source viable based on a landing page alone.
5. Obtain a submission-page receipt and authenticated quota only through the separate selector/account workflow. The current public feed is not that service.

## Session run card (negative)

The machine-readable card is [`docs/evidence/session-20261024-run-card.json`](../docs/evidence/session-20261024-run-card.json); the following is its human-readable summary. Values below describe this review, not an invented candidate score.

```json
{
  "hypothesis": "No candidate tested; top planning hypothesis is H86C-MMT, blocked before experimentation by the literal registry-overlap stop and missing shared cache.",
  "mechanism": "Proposed only: detect fault-related along-line translation of transverse RTP/TMI texture across opposite flanks; no surface or candidate was generated.",
  "named_non_fault_mimic": "Unfaulted intrusive contacts, acquisition seams, and remanent-magnetization changes.",
  "holdout_dti": null,
  "holdout_dti_label": "Not measured; no candidate or holdout run. No evaluator version, withheld-positive count, or CI is applicable.",
  "correlation_overlap_vs_registry": {
    "candidate_rank_correlation": null,
    "candidate_dot_overlap": null,
    "preplacement_witness_result": "The pinned historical witness has 100% allowed-domain positive support under the unchanged literal support rule, so every nonempty candidate would exceed the 70% overlap limit.",
    "registry_completeness": "Not established; one witness is a counterexample only."
  },
  "raster_sha256": null,
  "validator_output": {
    "candidate_exists": false,
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "reason": "No candidate TIFF was written; format validation cannot authorize submission."
  },
  "submission_name": null,
  "submission_note": "No candidate generated; no TIFF in this review is approved for submission.",
  "verdict": "negative"
}
```
