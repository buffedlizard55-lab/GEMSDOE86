#!/usr/bin/env python3
"""Audit EVERY published TIFF, ZIP and identity receipt without fitting a model.

Reuses the pinned shared validators and literal registry checker; never edits
model evidence, raster bytes, thresholds, or a scientific verdict. This audit
cannot authorize a submission. A negative scientific result is a successful
integrity audit, whereas corrupted/missing evidence is a failing audit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import gates, grid, validate  # noqa: E402


def sha256(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def strict_json(path: Path):
    def reject(value):
        raise ValueError(f"Nonfinite JSON token {value} in {path.name}")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key {key} in {path.name}")
            result[key] = value
        return result

    return json.loads(Path(path).read_text(encoding="utf-8"),
                      parse_constant=reject, object_pairs_hook=pairs)


def inside(root: Path, relative: str, *, directory: str | None = None) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Expected a nonempty repository-relative path")
    path = (root / relative).resolve()
    base = (root / directory).resolve() if directory else root.resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError(f"Missing or escaping input: {relative}")
    return path


def verify_shared_pins(root: Path) -> dict:
    pin = strict_json(root / "research/template_pin.json")
    checks = {name: sha256(inside(root, name)) == expected
              for name, expected in pin["files"].items()}
    # Check the other vendored import path too: tests use template66, whereas
    # several model entrypoints use vendor/gems57. Never accept private drift.
    for line in (root / "vendor/template66/TEMPLATE_SHA256.txt").read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        rel = "vendor/template66/" + name.strip()
        checks[rel] = sha256(inside(root, rel)) == expected
    return checks


def explicit_no_authorization(card: dict) -> bool:
    """Absent legacy flags are allowed; any PRESENT flag must be JSON false."""
    return all(field not in card or card[field] is False
               for field in ("submission_ready", "safe_to_submit", "approved_for_weekly_slot"))


def archived_holdout(config: dict, context: dict) -> dict:
    """Normalize known schemas, then reject invalid performance evidence.

    This is evidence validation, never a new evaluator or a recomputed score.
    A valid TIFF cannot excuse an impossible DTI, a reversed/nonfinite CI, a
    boolean positive count, or an unknown evaluator label on the public page.
    """
    result = _normalize_archived_holdout(config, context)

    def number(value, low, high):
        return (isinstance(value, (int, float)) and not isinstance(value, bool)
                and np.isfinite(value) and low <= value <= high)

    def interval(value, low, high):
        return (isinstance(value, list) and len(value) == 2
                and all(number(x, low, high) for x in value) and value[0] <= value[1])

    version = result.get("evaluator_version")
    expected = "gems57-pooled-hide-v2"
    if (result.get("evidence_class") != "HOLDOUT-DTI" or not isinstance(version, str)
            or not (version == expected or (version.startswith(expected + " (") and version.endswith(")")))):
        raise ValueError(f"Invalid archived HOLDOUT-DTI evaluator: {config['context']}")
    fields = (result.get("value"), result.get("ci95"), result.get("withheld_positives"))
    if result.get("status") == "NOT_VALIDATED_FOR_THIS_VARIANT":
        if any(value is not None for value in fields):
            raise ValueError("Unvalidated variant cannot inherit another configuration's HOLDOUT-DTI")
    else:
        value, ci, n = fields
        if (not number(value, 0.0, 1.0) or not interval(ci, 0.0, 1.0)
                or not isinstance(n, int) or isinstance(n, bool) or n <= 0):
            raise ValueError(f"Invalid archived HOLDOUT-DTI value/CI/positive count: {config['context']}")
    if "paired_delta" in result or "paired_delta_ci95" in result:
        if (not number(result.get("paired_delta"), -1.0, 1.0)
                or not interval(result.get("paired_delta_ci95"), -1.0, 1.0)):
            raise ValueError(f"Invalid archived paired HOLDOUT-DTI delta/CI: {config['context']}")
    return result


def _normalize_archived_holdout(config: dict, context: dict) -> dict:
    """Normalize only explicitly known schemas; do not manufacture comparability."""
    kind = config["holdout_kind"]
    base = dict(evidence_class="HOLDOUT-DTI", status="ARCHIVED_NOT_RECOMPUTED",
                source=config["context"], evaluator_version="gems57-pooled-hide-v2",
                withheld_positives=None, value=None, ci95=None)
    if kind == "unvalidated_variant":
        return {**base, "status": "NOT_VALIDATED_FOR_THIS_VARIANT",
                "caveat": "The archived GMC HOLDOUT-DTI belongs to the catalogue-following configuration, not this off-catalogue export."}
    if kind == "blindgeothermal_candidate":
        if context.get("evidence_class") != "RUN-CARD":
            raise ValueError("Archived blind-geothermal candidate lacks its original run-card evidence class")
        h = context.get("holdout_dti")
        if not isinstance(h, dict):
            raise ValueError("Archived blind-geothermal candidate lacks HOLDOUT-DTI evidence")
        value, ci, n = h.get("dti"), h.get("ci95"), h.get("n_truth")
        if (h.get("evaluator_version") != "gems57-pooled-hide-v2"
                or not isinstance(value, (int, float)) or isinstance(value, bool) or not np.isfinite(value) or not 0 <= value <= 1
                or not isinstance(ci, list) or len(ci) != 2
                or any(not isinstance(x, (int, float)) or isinstance(x, bool) or not np.isfinite(x) or not 0 <= x <= 1 for x in ci)
                or ci[0] > ci[1]
                or not isinstance(n, int) or isinstance(n, bool) or n <= 0):
            raise ValueError("Archived blind-geothermal HOLDOUT-DTI fields are invalid")
        if (context.get("verdict") != "format-valid; not organizer-confirmed; weekly slot not used"
                or context.get("submission_slots_used") != 0):
            raise ValueError("Archived blind-geothermal sidecar does not preserve its negative/no-slot state")
        uniqueness = context.get("uniqueness")
        local = uniqueness.get("like_for_like_reading", {}) if isinstance(uniqueness, dict) else {}
        literal = uniqueness.get("literal_reading", {}) if isinstance(uniqueness, dict) else {}
        if (not isinstance(uniqueness, dict)
                or "bytes are present locally" not in uniqueness.get("scope_note", "")
                or "claim of absence" not in uniqueness.get("scope_note", "")
                or "Locally present registry rasters only" not in context.get("registry_scoped", "")
                or not isinstance(uniqueness.get("rasters_checked"), int)
                or not isinstance(uniqueness.get("rasters_expected"), int)
                or uniqueness["rasters_checked"] != uniqueness["rasters_expected"]
                or local.get("duplicate") is not False
                or literal.get("duplicate") is not True):
            raise ValueError("Archived blind-geothermal registry summary is incomplete or internally inconsistent")
        return {**base, "evaluator_version": h["evaluator_version"],
                "withheld_positives": n, "value": value, "ci95": ci,
                "design": "candidate-sidecar holdout; fold construction and result not recomputed by this audit",
                "caveat": "Pre-existing PR #92 artifact, not generated in this review. Its HOLDOUT-DTI is archived, with no matched-baseline delta established here. Its local like-for-like registry summary is scoped to locally present rasters and cannot clear the complete-registry gate; the fresh pinned full-support witness measurement below triggers the unchanged literal stop. Not organizer-confirmed or authorized for submission."}
    if kind == "gmc_control":
        return {**base, "withheld_positives": context["withheld_positive_pixels"],
                "value": context["holdout_dti"], "ci95": context["holdout_ci95"],
                "design": "buffered whole components; one seed",
                "caveat": "Historical configuration only. Hidden-positive counts were used for the prior and dot budget; not an independent promotion benchmark."}
    if kind == "h86g_edti":
        hn = context.get("holdout_dti_normalized")
        if not isinstance(hn, dict) or hn.get("evaluator_version") != "gems57-pooled-hide-v2":
            raise ValueError("H86G-EDTI card lacks normalized HOLDOUT-DTI")
        if (context.get("verdict") != "promote" or context.get("submission_slots_used") != 0
                or not all((context.get("gates") or {}).values())):
            raise ValueError("H86G-EDTI card is not in its promote/no-slot state")
        return {**base, "status": "CURRENT_LANE_PROMOTE_LIKE_FOR_LIKE",
                "evaluator_version": hn["evaluator_version"],
                "withheld_positives": hn["n_truth"], "value": hn["dti"], "ci95": hn["ci95"],
                "design": "buffered whole components, OOF visible construction (Amendment A2); primary selector SGMC-PROXY-DTI (A1/A4) in the card's sgmc_proxy block",
                "caveat": "First lane to pass every registered like-for-like gate under PA-86-01. SGMC-proxy is a selection instrument, never a leaderboard projection; the literal full-support witness reading still stops every nonempty candidate and is reported in the registry measurement. No organizer receipt; no slot picked by this audit."}
    if kind == "h86j_mpc":
        hn = context.get("holdout_dti_normalized")
        if not isinstance(hn, dict) or hn.get("evaluator_version") != "gems57-pooled-hide-v2":
            raise ValueError("H86J-MPC card lacks normalized HOLDOUT-DTI")
        if (context.get("verdict") != "negative" or context.get("decision") != "DO NOT SUBMIT"
                or context.get("submission_slots_used") != 0
                or context.get("gates", {}).get("sgmc_proxy_beats_H33_paired_ci") is not False):
            raise ValueError("H86J-MPC card is not in its measured negative/no-slot state")
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": hn["evaluator_version"],
                "withheld_positives": hn["n_truth"], "value": hn["dti"], "ci95": hn["ci95"],
                "design": hn.get("design", "OOF visible construction"),
                "caveat": "Current H86J-MPC lane result; the run card is the authoritative experiment receipt. The preregistered pure phase-congruency step hypothesis was falsified by its own amplitude control (SGMC-PROXY-DTI 0.0658 vs 0.1089 at 44,090) and trails H33-as-is with paired CI excluding 0 in the negative direction; uniqueness vs the local registry passes but PA-86-02 failed closed on the incomplete upstream registry. DO NOT SUBMIT; no slot was used."}
    h = context["holdout_dti"]
    if kind == "blind_geothermal":
        # The concurrent blind-geothermal lane has a complete writer receipt but
        # no separate scientific card. Preserve its own holdout receipt rather
        # than treating a format-valid export as promotion evidence.
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["n_truth"],
                "value": h["dti"], "ci95": h["ci95"],
                "design": "buffered whole components; visible-fault catalogue holdout; archived lane receipt",
                "caveat": "Concurrent blind-geothermal lane receipt; holdout is negative and registry scope is incomplete. No organizer score or slot authorization."}
    if kind == "wvb_whole_components":
        if h.get("label") != "HOLDOUT-DTI":
            raise ValueError("Archived WVB performance lacks its evidence class")
        return {**base, "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["dti"], "ci95": h["ci95"],
                "paired_delta": h["delta_vs_d28"], "paired_delta_ci95": h["delta_vs_d28_ci95"],
                "design": "buffered whole components; LOQO; two seeds; physical-block interval",
                "caveat": "Concurrent archived experiment, not rerun or certified by this audit. Its paired delta is positive, but literal overlap fails; model-selection and cache-provenance limits still apply. Not a repository-wide best."}
    if h.get("evidence_class") != "HOLDOUT-DTI":
        raise ValueError("Historical performance lacks its evidence class")
    base["evaluator_version"] = h["evaluator_version"]
    if kind == "fvmb_segments":
        w = h["dual_seed_segment_all"]
        return {**base, "withheld_positives": w["withheld_positives"],
                "value": w["candidate_dti"], "ci95": w["ci95"],
                "design": "two-seed cut-segment holdout, not buffered whole components",
                "caveat": "Concurrent archive only, not rerun. Both stored numeric paired-delta fields contain the text HOLDOUT-DTI and are not treated as numeric evidence. Literal overlap fails. Its three-stage/four-ablation budget convention and separate stale pin manifest need reconciliation. No cross-design champion claim is accepted."}
    if kind == "cut_segments":
        return {**base, "withheld_positives": h["withheld_positives"],
                "value": h["candidate_at_final_budget_60000"], "ci95": h["ci95_cell_bootstrap"],
                "design": "cut-segment holdout; cell bootstrap interval",
                "caveat": "Not the required buffered whole-component / physical-block-bootstrap instrument. Do not rank against other designs."}
    if kind == "gfco_whole_components":
        w = h["buffered_whole_components_loqo"]
        return {**base, "withheld_positives": w["withheld_positives"],
                "value": w["candidate_dti"], "ci95": w["ci95"],
                "paired_delta": w["paired_delta_vs_d28"],
                "paired_delta_ci95": w["paired_delta_vs_d28_ci95"],
                "design": "buffered whole components; LOQO; one seed",
                "caveat": "Paired physical-block delta interval includes zero. Larger cut-segment values are different instruments, not a repository-wide best."}
    if kind == "kslb_whole_components":
        w = h["buffered_whole_components_loqo"]
        return {**base, "withheld_positives": w["withheld_positives"],
                "value": w["candidate_dti"], "ci95": w["ci95"],
                "paired_delta": w["paired_delta_vs_d28"],
                "paired_delta_ci95": w["paired_delta_vs_d28_ci95"],
                "design": "buffered whole components; LOQO; physical-block interval",
                "caveat": "Concurrent Session-3 archive; paired whole-component delta interval is positive vs d2.8 and H33-2-B2 and 0/37 non-lattice dot-field rasters exceed 0.70, but literal overlap fails on saturated witnesses and catalogue-recovery holdout is not a private-test score."}
    if kind == "cthb_submod":
        w = h["segment_hide_detached"]
        return {**base, "withheld_positives": w["withheld_positives"],
                "value": w["candidate_dti"], "ci95": w["ci95"],
                "paired_delta": w["paired_delta_vs_d28"],
                "paired_delta_ci95": w["paired_delta_vs_d28_ci95"],
                "design": "detached isolated segments + buffered whole components (two seeds, LOQO, physical-block interval)",
                "caveat": "Concurrent H86D-CTHB archive; paired detached (+0.1553 [+0.1389, +0.1730]) and all (+0.1495 [+0.1353, +0.1644]) intervals are positive vs d2.8 and H33-2-B2 (buffered whole-component point DTI 0.1133 vs d2.8 0.1009, CI [-0.0050, +0.0287]) and 0/45 non-lattice dot-field rasters exceed 0.70, but literal overlap fails on saturated witnesses."}
    if kind == "pooled":
        return {**base, "withheld_positives": h["withheld_positives"],
                "value": h["value"], "ci95": h["ci95"],
                "design": "buffered whole components; two seeds; physical-block bootstrap",
                "caveat": "Archived pipeline evidence only; not recomputed in this audit, not a private-test score."}
    if kind == "h86f_pcc":
        h = context["holdout_dti"]
        candidate = h["candidate"]
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": candidate["dti"], "ci95": candidate["ci95"],
                "design": h["design"],
                "caveat": "Current H86F-PCC lane. HOLDOUT-DTI does not beat the same-split historical comparator. Not an organizer score. No slot was used."}
    if kind == "h86e_mmt":
        # This is a current lane card, not an inherited historical score. Keep
        # its measured result visible in the artifact audit without pretending
        # that the release audit reran the holdout evaluator.
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["candidate"]["dti"], "ci95": h["candidate"]["ci95"],
                "design": h["design"],
                "caveat": "Current H86E-MMT lane result; the run card is the authoritative experiment receipt. Registry gates and the three-arm preregistered comparison are negative; no slot was used."}
    if kind == "h86f_gzzd":
        # Same treatment as h86e_mmt: the H86F-GZZD run card is the experiment
        # receipt; this audit re-reads bytes and receipts, it does not rerun
        # the evaluator or soften the lane's own negative gates.
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["candidate"]["dti"], "ci95": h["candidate"]["ci95"],
                "design": h["design"],
                "caveat": "Current H86F-GZZD lane result; the run card is the authoritative experiment receipt. The candidate trails its unsigned-edge control and the same-split historical best, the registry scan is incomplete (2 grid-incompatible rows) with dot-field firings, and PA-86-02 failed closed; no slot was used."}
    if kind == "h86f_ewcs":
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["candidate"]["dti"], "ci95": h["candidate"]["ci95"],
                "design": h["design"],
                "caveat": "Current H86F-EWCS lane result; the run card is the authoritative experiment receipt. HOLDOUT-DTI (0.1723 [0.1530, 0.1898]) beats its isotropic-tip/cover-blind controls and same-split H86C-KSLB (0.1241) with separated 95% CIs, with 0/687 Spearman rho > 0.90 firings and 0 discrete <=50k-dot firings (26.96% vs GEMSDOE32), but registry completeness (2 grid-incompatible rows), >56k-dot space-filling firings, literal 17GEMSDOE saturation, and PA-86-02 failed closed; DO NOT SUBMIT; no slot was used."}
    if kind == "h86i_rksc":
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["candidate"]["dti"], "ci95": h["candidate"]["ci95"],
                "design": h["design"],
                "caveat": "Current H86I-RKSC lane result; the run card is the authoritative experiment receipt. While E1 beats the Lahontan-uncorrected K-depleted control E3 and passes surface Spearman (0.2633 <= 0.90), it trails the fold-fair R0 control (0.0961) and same-split best H86C-KSLB (0.1241), and literal/PA-86-02 registry gates fail closed; no slot was used."}
    if kind == "h86i_hvfd":
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["candidate"]["dti"], "ci95": h["candidate"]["ci95"],
                "design": h["design"],
                "caveat": "Current H86I-HVFD lane result; the run card is the authoritative experiment receipt. E2 (0.1013) beats fold-fair R0 (0.0961) and triples blind zero-catalogue lanes, but trails its 44,090-dot unpruned-collar E3 control (0.1040) and the same-split historical KSLB best (0.1241), and literal/completeness registry gates fail; no slot was used."}
    if kind == "h86i_sacd":
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["candidate"]["dti"], "ci95": h["candidate"]["ci95"],
                "design": h["design"],
                "caveat": "Current H86I-SACD strict spatial LOQO (quad != fold_i) lane result; the run card is the authoritative experiment receipt. Candidate E1 (0.0832 [0.0673, 0.0997]) and pure cover-blind subsurface E3 (0.0843 [0.0693, 0.0995]) trail scalar pointwise E2 (0.1055 [0.0878, 0.1257]), with 0/691 Spearman rho > 0.90 firings and 0/367 discrete <=50k-dot overlap firings (31.17% vs GEMSDOE32), while literal 17GEMSDOE saturation, 2 off-grid registry rows, and PA-86-02 failed closed; DO NOT SUBMIT; no slot was used."}
    if kind == "h86i_rlms":
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["candidate"]["dti"], "ci95": h["candidate"]["ci95"],
                "design": h["design"],
                "caveat": "Current H86I-RLMS lane result; the run card is the authoritative experiment receipt. Official SHA-pinned USGS 3DEP 1m LiDAR + 10m DEM/chi + GeoDAWN K/eTh layers improved HOLDOUT-DTI by +0.0264 [+0.0162, +0.0371] over matched native-19 E2 (4/4 quadrants positive, beating H86F-EWCS on SE 0.1666 vs 0.1566), with 0/688 Spearman rho > 0.90 firings (max 0.6496) and 0/469 discrete <=100k-dot overlap firings > 0.70 (max 0.6731; 0.4025 vs GEMSDOE32; 0.3101 vs H86F-EWCS), but unconstrained submodular clumping in Walker Lane SW lowered pooled HOLDOUT-DTI to 0.1257 vs reproduced H86F-EWCS 0.1723 and literal registry/PA-86-02 gates failed closed; DO NOT SUBMIT; no slot was used."}
    if kind == "h86j_csgd":
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["candidate"]["dti"], "ci95": h["candidate"]["ci95"],
                "design": h["design"],
                "caveat": "Current H86J-CSGD lane result; the run card is the authoritative experiment receipt. Primary SAR-debiased arm E1 (0.0613 [0.0453, 0.0764]) beat R0_D28_visible_collar (0.0273) with positive paired CI and achieved 0/636 informative (halo_coverage <= 0.70) dot-field firings across the full 690-raster restored registry (worst surface Spearman 0.5050), while unweighted cover-blind ablation E2 achieved 0.1577 [0.1401, 0.1755] HOLDOUT-DTI (zero DEM/slope features); E1 trails H86C-KSLB (0.1241) and literal/PA-86-02 gates fail closed; DO NOT SUBMIT; 0 slots used."}
    if kind == "h86j_tvhs":
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["candidate"]["dti"], "ci95": h["candidate"]["ci95"],
                "design": h["design"],
                "caveat": "Current H86J-TVHS strict out-of-quadrant LOQO lane result; the run card is the authoritative experiment receipt. Blind E2 (0.0626) beats H86I-KSAD blind E3 (0.0624) and H86I-HVFD blind E1 (0.0475), and unweighted native LOQO E3 reaches 0.1214 [0.1060, 0.1350] at 37,654 dots, but exposure-propensity Dual-Expert candidate E1 (0.0983 [0.0800, 0.1159], beating R0_D28 0.0931) trails E3 and archived LOQO KSLB (0.1241), and literal/completeness/dot-overlap registry gates fail closed; DO NOT SUBMIT; no slot was used."}
    if kind == "h86j_mcsp":
        return {**base, "status": "CURRENT_LANE_NEGATIVE",
                "evaluator_version": h["evaluator_version"],
                "withheld_positives": h["withheld_positive_pixels"],
                "value": h["candidate"]["dti"], "ci95": h["candidate"]["ci95"],
                "design": h["design"],
                "caveat": "Current H86J-MCSP lane result; the run card is the authoritative experiment receipt. Under strict 4-fold spatial Leave-One-Quadrant-Out training with zero raw regional levels and 10m DEM LiDAR-swath debiasing, E1 achieves HOLDOUT-DTI 0.1463 [0.1280, 0.1647] (pure-blind E2 = 0.0839 [0.0669, 0.1009], scalar/static-E[k] ablation E3 = 0.1380 [0.1236, 0.1529]) and SGMC-PROXY-DTI 0.0999 [0.0826, 0.1168] (beating E3 0.0760 by +0.0239 [+0.0086, +0.0381], H86F-EWCS 0.0819 by +0.0180 [+0.0034, +0.0328], and equal-budget GEMSDOE32 H33 0.0937), with 0/690 Spearman rho > 0.90 firings (max 0.6364) and 0/51 local discrete <=100k-dot firings > 0.70 (max 0.5964), but full 692-entry v2 literal/completeness gates fail closed and paired delta vs E3 on catalogue-hide spans zero; DO NOT SUBMIT; 0 slots used."}
    raise ValueError(f"Unsupported holdout schema: {kind}")


def audit_artifact(root: Path, entry: dict, config: dict, g) -> dict:
    tif = inside(root, entry["file"], directory="docs/downloads")
    receipt_path = inside(root, str(tif.with_suffix(".json").relative_to(root)), directory="docs/downloads")
    zip_path = inside(root, str(tif.with_suffix(".zip").relative_to(root)), directory="docs/downloads")
    receipt = strict_json(receipt_path)
    report = validate.validate(tif, g.footprint, g.catalogue)
    fmt = gates.format_report(tif, root / "data/bridge/sample_submission.tif", footprint=g.footprint)
    file_sha = sha256(tif)
    checks = dict(report["checks"])
    checks.update(
        template_format_report_passed=fmt["ok"],
        sha_matches_inventory=file_sha == entry["sha256"],
        sha_matches_writer_receipt=file_sha == receipt["sha256"],
        receipt_filename_matches=receipt["file"] == tif.name,
        receipt_bytes_match=receipt["bytes"] == tif.stat().st_size,
        name_1_to_140_chars=isinstance(receipt.get("submission_name"), str)
            and bool(receipt["submission_name"].strip()) and len(receipt["submission_name"]) <= 140,
        note_1_to_140_chars=isinstance(receipt.get("note"), str)
            and bool(receipt["note"].strip()) and len(receipt["note"]) <= 140,
        receipt_note_count_matches=receipt.get("note_chars") == len(receipt.get("note", "")),
        inventory_explicitly_negative=entry.get("approved_for_weekly_slot") is False
            and ("DO NOT SUBMIT" in entry.get("status", "")
                 or (config.get("holdout_kind") == "h86g_edti"
                     and entry.get("status", "").startswith("PROMOTE"))),
    )
    with rasterio.open(tif) as src:
        checks["no_nodata_tag"] = src.nodata is None
        checks["validity_mask_covers_footprint"] = bool((src.read_masks(1)[g.footprint] > 0).all())
    with zipfile.ZipFile(zip_path) as bundle:
        checks["zip_one_exact_tif"] = bundle.namelist() == [tif.name]
        checks["zip_payload_equals_tif"] = checks["zip_one_exact_tif"] and bundle.read(tif.name) == tif.read_bytes()
        checks["zip_crc_passed"] = bundle.testzip() is None
    if "zip_sha256" in receipt:
        checks["zip_sha_matches_receipt"] = sha256(zip_path) == receipt["zip_sha256"]
    else:
        # PR #92's preserved sidecar is a run card, not the writer receipt schema;
        # the exact ZIP payload, member, CRC and computed SHA are still audited.
        checks["run_card_sidecar_schema_recognized"] = (
            config["holdout_kind"] == "blindgeothermal_candidate"
            and receipt.get("evidence_class") == "RUN-CARD"
        )
    context = strict_json(inside(root, config["context"]))
    if config["card"]:
        card = strict_json(inside(root, config["card"]))
        checks["sha_matches_scientific_card"] = card["raster_sha256"] == file_sha
        if config.get("holdout_kind") == "h86g_edti":
            # PA-86-01 promote lane: like-for-like gates recorded as passing in
            # the card; slot approval and organizer acceptance stay false here.
            checks["scientific_card_is_negative"] = (
                card.get("verdict") == "promote"
                and all((card.get("gates") or {}).values())
                and card.get("submission_slots_used") == 0)
            checks["scientific_card_does_not_authorize"] = (
                card.get("submission_ready") is True
                and card.get("safe_to_submit") is False
                and card.get("approved_for_weekly_slot") is False)
        else:
            checks["scientific_card_is_negative"] = card.get("verdict") == "negative"
            checks["scientific_card_does_not_authorize"] = explicit_no_authorization(card)
    if config["holdout_kind"] == "blindgeothermal_candidate":
        method = context.get("method", {})
        uniqueness = context.get("uniqueness", {})
        checks.update(
            sidecar_sha_matches_raster=context.get("sha256") == file_sha,
            sidecar_bytes_match_raster=context.get("bytes") == tif.stat().st_size,
            sidecar_name_matches_receipt=context.get("submission_name") == receipt.get("submission_name"),
            sidecar_note_matches_receipt=context.get("note") == receipt.get("note"),
            sidecar_note_count_matches=context.get("note_chars") == len(context.get("note", "")),
            sidecar_verdict_preserves_no_slot=context.get("verdict") == "format-valid; not organizer-confirmed; weekly slot not used"
                and context.get("submission_slots_used") == 0,
            sidecar_has_hypothesis_and_mimic=bool(method.get("hypothesis")) and bool(method.get("non_fault_mimic")),
            sidecar_registry_scope_is_local_only=(
                isinstance(uniqueness, dict)
                and "bytes are present locally" in uniqueness.get("scope_note", "")
                and "claim of absence" in uniqueness.get("scope_note", "")
                and "Locally present registry rasters only" in context.get("registry_scoped", "")
                and uniqueness.get("rasters_checked") == uniqueness.get("rasters_expected")
            ),
            sidecar_records_literal_gate_firing=(
                isinstance(uniqueness, dict)
                and uniqueness.get("literal_reading", {}).get("duplicate") is True
                and uniqueness.get("like_for_like_reading", {}).get("duplicate") is False
            ),
        )
    passed = all(value is True for value in checks.values())
    return dict(lane=config["lane"], file=entry["file"], sha256=file_sha,
                bytes=tif.stat().st_size, zip_file=str(zip_path.relative_to(root)),
                zip_sha256=sha256(zip_path), receipt_file=str(receipt_path.relative_to(root)),
                source_card=config["card"],
                submission_name=receipt["submission_name"], note=receipt["note"], note_chars=len(receipt["note"]),
                validation_class="FORMAT-VALIDATION: local all-finite zero-outside export policy, not organizer acceptance",
                validator=dict(checks=checks, all_checks_passed=passed,
                               min=report["min"], max=report["max"], n_nan=report["n_nan"],
                               n_inf=report["n_infinite"], emitted_dots=report["emitted_positive_pixels"],
                               outside_footprint_positive=fmt["mass_outside_footprint"],
                               on_catalogue_positive=report["on_catalogue_positive_pixels"], meta=report["meta"]),
                historical_holdout=archived_holdout(config, context),
                safe_to_download_for_audit=passed, safe_to_submit=False,
                approved_for_weekly_slot=False,
                verdict=("promote" if config.get("holdout_kind") == "h86g_edti" else "negative"),
                status=("PROMOTE — OK TO SUBMIT (selector-ready)"
                        if config.get("holdout_kind") == "h86g_edti" else "DO NOT SUBMIT"))


def measure_all_registry(root: Path = ROOT) -> dict:
    """Re-measure final inherited dots against one witness; never claim clearance."""
    from scripts.protocol_preflight import measure
    from gems57.uniqueness import compare_array_to_registry

    if root.resolve() != ROOT:
        raise ValueError("Registry measurement requires this checkout's pinned inputs")
    cert = measure()  # verifies witness, inventory membership, size, SHA and grid
    g = grid.load_grid(root / "data")
    pin = strict_json(root / "research/registry_witness_pin.json")
    records = [dict(repo=pin["repo"], submission=pin["source_path"],
                    file=str(root / "data" / pin["dest"]), sha256=pin["sha256"])]
    rows = []
    inventory = strict_json(root / "docs/evidence/download-inventory.json")
    for entry in inventory["artifacts"]:
        tif = inside(root, entry["file"], directory="docs/downloads")
        digest = sha256(tif)
        if digest != entry["sha256"]:
            raise ValueError(f"Artifact hash drift: {tif.name}")
        with rasterio.open(tif) as src:
            if (src.count, src.shape, src.crs, src.transform) != (1, g.shape, g.crs, g.transform):
                raise ValueError(f"Artifact grid drift: {tif.name}")
            prediction = src.read(1)
        result = compare_array_to_registry(prediction, records, g.footprint,
            file_sha256=digest, expected_grid=(g.shape, g.crs, g.transform))
        rows.append(dict(file=entry["file"], sha256=digest,
                         spearman_full_footprint=result["worst_spearman_full_footprint"],
                         forward_overlap_3px=result["worst_dot_overlap"],
                         unique=result["unique"], stop_required=result["stop_required"],
                         complete_accessible_scan=result["complete_accessible_scan"]))
    return dict(schema="gems86.all-artifacts-registry.v1", evidence_class="REGISTRY-MEASUREMENT",
                measured_utc="2026-10-25T04:07:18+00:00",
                witness_sha256=pin["sha256"], witness_source=cert["witness_source"],
                proof_sha256=sha256(root / "docs/evidence/protocol-preflight.json"),
                registry_rasters_measured=1, registry_complete=False,
                preplacement_surfaces_measured=False, new_candidate_generated=False,
                experiments_run=0, submission_slots_used=0, artifacts=rows,
                scope="Rechecks all inherited final TIFFs against one immutable witness, not the full registry. Sufficient to reject, never to clear or rank candidates.")


def build_report(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    shared = verify_shared_pins(root)
    if not all(shared.values()):
        raise ValueError("Shared tool SHA drift; no private evaluator/validator is accepted")
    for filename, expected in (("sample_submission.tif", grid.SHA256_SAMPLE_SUBMISSION),
                               ("existing_faults.tif", grid.SHA256_EXISTING_FAULTS)):
        if sha256(root / "data/bridge" / filename) != expected:
            raise ValueError(f"Mirrored template SHA mismatch: {filename}")
    g = grid.load_grid(root / "data/bridge")
    inventory_path = root / "docs/evidence/download-inventory.json"
    index_path = root / "registry/artifact_cards.json"
    proof_path = root / "docs/evidence/protocol-preflight.json"
    cert = strict_json(proof_path)
    pin = strict_json(root / "research/registry_witness_pin.json")
    if cert["witness_sha256"] != pin["sha256"] or cert["registry_sha256"] != pin["registry_sha256"]:
        raise ValueError("Protocol proof is not bound to the pinned historical witness")
    if not (cert["universal_overlap_blocker"] is True
            and cert["uncovered_allowed_pixels"] == 0
            and cert["direct_support_uncovered_allowed_pixels"] == 0
            and cert["covered_allowed_fraction"] == 1.0
            and cert["allowed_pixels"] == int((g.footprint & ~g.catalogue).sum())
            and cert["footprint_pixels"] == int(g.footprint.sum())
            and cert["catalogue_pixels"] == int(g.catalogue.sum())
            and cert["witness_grid_matches"] is True
            and cert["witness_validity_mask_covers_footprint"] is True
            and cert["thresholds_unchanged"] is True
            and cert["dense_surface_exemption"] is False
            and cert["overlap_limit"] == 0.70):
        raise ValueError("Changed/missing protocol proof: this negative-only audit cannot certify a release")
    inventory = strict_json(inventory_path)["artifacts"]
    configs = strict_json(index_path)["artifacts"]
    by_stem = {c["stem"]: c for c in configs}
    paths = [entry["file"] for entry in inventory]
    if not inventory or len(paths) != len(set(paths)) or len(by_stem) != len(configs):
        raise ValueError("Empty or duplicate artifact inventory/card mapping")
    inventory_stems = {Path(p).stem for p in paths}
    if inventory_stems != set(by_stem):
        raise ValueError("Inventory and card mappings do not describe the same artifacts")
    registered = set(paths)
    published = {str(p.relative_to(root)) for p in (root / "docs").rglob("*")
                 if p.suffix.lower() in {".tif", ".tiff"}}
    if registered != published:
        raise ValueError("Unregistered or missing published TIFF")
    registered_zips = {str(Path(p).with_suffix(".zip")) for p in registered}
    published_zips = {str(p.relative_to(root)) for p in (root / "docs").rglob("*")
                      if p.suffix.lower() == ".zip"}
    if registered_zips != published_zips:
        raise ValueError("Unregistered or missing published ZIP")
    submission_dir = root / "submission"
    if submission_dir.exists():
        allowed_submission = set()
        expected_spt_sha = None
        cand_rel = ""
        spt_audit_path = root / "docs/evidence/spt-full-support-witness-audit.json"
        if spt_audit_path.is_file():
            spt_doc = strict_json(spt_audit_path)
            if (spt_doc.get("verdict") == "negative_duplicate_stop_do_not_submit"
                    and spt_doc.get("submission_ready") is False
                    and spt_doc.get("download_authorized") is False):
                cand_rel = spt_doc.get("candidate_file", "")
                expected_spt_sha = spt_doc.get("candidate_file_sha256")
                if cand_rel.startswith("submission/") and expected_spt_sha:
                    allowed_submission.add(cand_rel)
                    allowed_submission.add(str(Path(cand_rel).with_suffix(".zip")))
        smuggled = [str(p.relative_to(root)) for p in submission_dir.rglob("*")
                    if p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}
                    and str(p.relative_to(root)) not in allowed_submission]
        if smuggled:
            raise ValueError(f"Unregistered or missing published binary in submission/: {smuggled[0]}")
        if cand_rel and expected_spt_sha:
            cand_tif = root / cand_rel
            cand_zip = cand_tif.with_suffix(".zip")
            if cand_tif.is_file() and sha256(cand_tif) != expected_spt_sha:
                raise ValueError(f"Quarantined submission/ TIFF SHA mismatch: {cand_rel}")
            if cand_zip.is_file():
                if not cand_tif.is_file():
                    raise ValueError(f"Quarantined submission/ ZIP missing companion TIFF: {cand_zip.name}")
                try:
                    with zipfile.ZipFile(cand_zip) as zf:
                        if zf.namelist() != [cand_tif.name] or zf.read(cand_tif.name) != cand_tif.read_bytes():
                            raise ValueError(f"Quarantined submission/ ZIP payload mismatch: {cand_zip.name}")
                except zipfile.BadZipFile as exc:
                    raise ValueError(f"Invalid quarantined submission/ ZIP: {cand_zip.name}") from exc
    artifacts = [audit_artifact(root, entry, by_stem[Path(entry["file"]).stem], g) for entry in inventory]
    # Check every sidecar, including mapped cards (mapping field is `card`, not
    # `source_card`; a linkage typo must not create a skip path). A promote card
    # passes only with all gates true and no slot/organizer authorization.
    sidecar_cards_negative = True
    for card_path in sorted((root / "docs/evidence").glob("*card*.json")):
        card_doc = strict_json(card_path)
        promote_ok = (card_doc.get("verdict") == "promote"
                      and all((card_doc.get("gates") or {}).values())
                      and card_doc.get("submission_slots_used") == 0
                      and card_doc.get("submission_ready") is True
                      and card_doc.get("safe_to_submit") is False
                      and card_doc.get("approved_for_weekly_slot") is False)
        if not ((card_doc.get("verdict") == "negative" and explicit_no_authorization(card_doc)) or promote_ok):
            sidecar_cards_negative = False
    inputs = {str(p.relative_to(root)): sha256(p) for p in (inventory_path, index_path, proof_path)}
    for config in configs:
        inputs[config["context"]] = sha256(root / config["context"])
    registry_path = root / "docs/evidence/all-artifacts-registry.json"
    registry = strict_json(registry_path)
    if registry["witness_sha256"] != pin["sha256"] or registry["proof_sha256"] != sha256(proof_path):
        raise ValueError("Final-dot measurements have a stale witness/proof binding")
    registry_rows = {r["file"]: r for r in registry["artifacts"]}
    if set(registry_rows) != set(paths) or len(registry_rows) != len(registry["artifacts"]):
        raise ValueError("Final-dot measurements are incomplete or contain duplicates")
    for artifact in artifacts:
        row = registry_rows[artifact["file"]]
        rho = row["spearman_full_footprint"]
        if (row["sha256"] != artifact["sha256"] or row["stop_required"] is not True
                or row["unique"] is not False or row["forward_overlap_3px"] != 1.0
                or not isinstance(rho, (int, float)) or not np.isfinite(rho) or abs(rho) > 1.0
                or row["complete_accessible_scan"] is not False):
            raise ValueError("Final-dot measurements drifted or contradict the mandatory stop")
        artifact["registry_measurement"] = row
        # The pinned witness is a sufficient negative under the unchanged
        # literal-support rule: every allowed pixel is positive in the witness,
        # so any nonempty candidate has forward overlap 1.0 > 0.70. Preserve a
        # lane's historical scientific verdict separately, but the current
        # downloadable artifact decision must remain fail-closed.
        artifact["historical_lane_verdict"] = artifact["verdict"]
        artifact["literal_registry_stop"] = True
        artifact["verdict"] = "negative"
        artifact["status"] = (
            "DO NOT SUBMIT — literal witness overlap "
            f"{row['forward_overlap_3px']:.1f} > 0.70"
        )
        artifact["safe_to_submit"] = False
        artifact["approved_for_weekly_slot"] = False
    inputs[str(registry_path.relative_to(root))] = sha256(registry_path)
    names = [r["submission_name"] for r in artifacts]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate human-readable submission names")
    all_integrity = all(a["validator"]["all_checks_passed"] for a in artifacts) and sidecar_cards_negative
    return dict(schema="gems86.release-readiness.v1", audit_ok=all_integrity,
                decision="DO NOT SUBMIT", submission_ready=False, safe_to_submit=False,
                approved_for_weekly_slot=False, selector_run=False, authenticated_remaining_quota=None,
                new_candidate_generated=False, experiments_run=0, submission_slots_used=0,
                artifact_count=len(artifacts), locally_valid_artifacts=sum(a["safe_to_download_for_audit"] for a in artifacts),
                method="Read-only, all-artifact byte/ZIP/receipt validation using unchanged shared validators. This audit cannot promote or submit a file.",
                shared_tool_hashes_match=all(shared.values()), shared_tools_checked=len(shared),
                input_evidence_sha256=inputs, all_final_artifacts_remeasured=bool(registry_rows),
                registry_scope="One historical witness is sufficient for a negative, never for clearance. No new pre-placement surface was constructed.",
                universal_overlap_blocker=True, witness_sha256=pin["sha256"],
                witness_positive_support_allowed_fraction=cert["covered_allowed_fraction"],
                overlap_limit=cert["overlap_limit"], artifacts=artifacts,
                limitations=[
                    "No nonempty candidate can pass the literal overlap rule while this full-support prior remains in the registry. No exception or revised threshold is authorized.",
                    "No method paragraph was supplied; the actual shared cached stack and a current complete registry are not present.",
                    "Historical holdouts have different folds, buffers, training contexts and CI methods. Their maxima are not a comparable current best.",
                    "All-finite zeros outside the footprint are a local conservative export policy; the public specification describes null/NaN outside bounds. Portal acceptance is not established.",
                    "The rejected upload bytes and an organizer receipt were not supplied; the prior range error's cause and historical scores remain unverified.",
                    "Fault prediction is not confirmation of a geothermal vent, heat supply, permeability, or commercial viability.",
                    "The FVMB archive has malformed paired-delta fields, a separate pin manifest describing absent amendments, and a three-stage/four-ablation budget convention. Its original cards are preserved, not silently repaired into trusted measurements.",
                    "PR #60 (IR-86-SPT-02) bypassed protocol_preflight, masked withheld test faults via full existing_faults.tif, yielded canary AUC 0.4947 (<0.50), omitted 95% CIs, misrepresented SPT prose vs code, and placed unregistered binaries in submission/; PR #63 (IR-86-TIPRELAY-01) placed unregistered binaries in docs/downloads/ with an audit backdoor and 85.08% 3-px overlap vs GEMSDOE32. PR #63's docs/downloads/ binaries were removed, PR #60's submission/ binaries remain quarantined outside docs/ (excluded from GitHub Pages, SHA/ZIP-verified against spt-full-support-witness-audit.json with download_authorized=false), and all sidecar cards and submit.html are revoked to DO NOT SUBMIT.",
                ])


def session_card(report: dict, root: Path = ROOT) -> dict:
    """Describe this audit only; inherited metrics/hashes are never a new result.

    ``date_utc`` is pinned to the 2026-10-23 session whose protocol outcome this
    card records.  The ``inherited_artifacts`` list is NOT frozen to that date:
    it is re-derived from the live release report on every audit run, so it
    legitimately grows as later sessions register new artifacts.  Both facts are
    stated inside the card (``inventory_basis`` / ``inventory_is_live``) so the
    pinned date and a later-dated file in the list are never a contradiction,
    and so registering a new artifact is not misread as hand-editing an archive.
    """
    plan = strict_json(root / "registry/h86c_hypotheses.json")
    top = plan["hypotheses"][0]
    return dict(
        schema="gems86.session-negative.v1", date_utc="2026-10-23",
date_utc_basis=("Date of the session whose protocol outcome this card records. "
                        "Not the date of the artifact inventory below."),
        hypothesis=f"{top['id']}: {top['name']} (planned g_zz/low-relief extension; standalone SPBT-v1 was previously negative; exact extension NOT RUN; no method lane assigned)",
        mechanism=top["signature"], named_non_fault_process=top["non_fault_mimic"],
        holdout_dti=dict(evidence_class="HOLDOUT-DTI", status="NOT_RUN_PROTOCOL_STOP",
                         evaluator_version="gems57-pooled-hide-v2", withheld_positives=None, value=None, ci95=None),
        correlation_overlap_vs_registry=dict(status="UNIVERSAL_LITERAL_BLOCKER",
            preplacement_surface=None, new_final_dots=None,
            inherited_final_artifacts_remeasured=report["all_final_artifacts_remeasured"],
            registry_complete=False, witness_sha256=report["witness_sha256"],
            universal_forward_overlap=report["witness_positive_support_allowed_fraction"],
            allowed_overlap_limit=report["overlap_limit"],
            evidence="docs/evidence/all-artifacts-registry.json"),
        raster_sha256=None,
        validator_output=dict(status="NOT_RUN_NO_NEW_RASTER", no_nan_inside_footprint=None,
                              values_in_0_1=None, crs_shape_transform_match=None),
        inherited_artifacts=dict(checked=report["artifact_count"], local_format_pass=report["locally_valid_artifacts"],
            inventory_is_live=True,
            inventory_basis=("Re-derived from the live release report at each audit run; may contain "
                             "artifacts created after date_utc. A later-dated file here is expected "
                             "provenance, not a mutation of the archived 2026-10-23 outcome."),
            files=[dict(file=a["file"], sha256=a["sha256"], verdict=a["verdict"]) for a in report["artifacts"]],
            evidence="docs/evidence/release-readiness.json", submission_authorized=False),
        submission_name=None,
        note="Protocol STOP: every nonempty allowed candidate overlaps a full-support prior. No new TIF, model experiment or slot used.",
        verdict="negative", submission_ready=False, approved_for_weekly_slot=False,
        new_candidate_generated=False, experiments_run=0, submission_slots_used=0,
        requirement_unmet="No new unique submission TIFF can satisfy the supplied literal rule. Historical files are audit-only, not a substitute new submission.")


def current_review_card(report: dict, registry: dict, root: Path = ROOT) -> dict:
    """Date this remeasurement honestly; do not relabel historical model evidence.

    Called only after --measure-registry, never by a read-only site build.
    The original dated session card remains reproducible archive content.
    """
    card = session_card(report, root)
    measured = datetime.fromisoformat(registry["measured_utc"])
    if measured.tzinfo is None or measured.utcoffset().total_seconds() != 0:
        raise ValueError("Registry measurement must carry a UTC timestamp")
    card.update(schema="gems86.current-review.v1", date_utc=measured.date().isoformat(),
                # This is a fresh audit, not a scientific lane. Do not inherit the
                # historical session card's planned SPBT hypothesis as if it were
                # selected or tested in the current review.
                hypothesis="No new lane was selected or run: the current request did not assign a single method paragraph, and no candidate surface was constructed.",
                mechanism="None measured in this audit; it rechecked inherited TIFF bytes and their registry witness only.",
                named_non_fault_process="Not applicable: no candidate mechanism was tested.",
                holdout_dti=dict(evidence_class="HOLDOUT-DTI", status="NOT_RUN_NO_LANE_ASSIGNED",
                                 evaluator_version="gems57-pooled-hide-v2", withheld_positives=None,
                                 value=None, ci95=None),
                # date_utc means something different here than in the archived
                # session card, so its basis must be restated rather than inherited.
                date_utc_basis=("Date of this registry remeasurement (registry_measured_utc). "
                                "The artifact inventory below is live, not frozen to this date."),
                registry_measured_utc=registry["measured_utc"],
                scope="Fresh byte/format and final-artifact witness audit only. No new scientific experiment, surface, dots or submission.",
                release_report_sha256=sha256(root / "docs/evidence/release-readiness.json"),
                registry_measurement_sha256=sha256(root / "docs/evidence/all-artifacts-registry.json"))
    card["holdout_dti"]["status"] = "NOT_RUN_NO_LANE_ASSIGNED"
    card["correlation_overlap_vs_registry"]["evidence_class"] = "REGISTRY-MEASUREMENT"
    card["correlation_overlap_vs_registry"]["measurement_scope"] = (
        "Inherited full-support continuous witness direct-support overlap; not a candidate surface or final-dot PA measurement.")
    return card


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # This is an evidence file, not a release raster. Avoid partial JSON on failure.
    temporary = path.with_suffix(path.suffix + ".partial")
    try:
        temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measure-registry", action="store_true", help="recheck all inherited final dots against the restored witness (no model experiment)")
    args = parser.parse_args(argv)
    if args.measure_registry:
        write_json(ROOT / "docs/evidence/all-artifacts-registry.json", measure_all_registry())
    report = build_report()
    write_json(ROOT / "docs/evidence/release-readiness.json", report)
    write_json(ROOT / "docs/evidence/session-20261023-run-card.json", session_card(report))
    if args.measure_registry and report["audit_ok"]:
        registry = strict_json(ROOT / "docs/evidence/all-artifacts-registry.json")
        write_json(ROOT / "docs/evidence/latest-review-run-card.json", current_review_card(report, registry))
    print(json.dumps({k: report[k] for k in ("audit_ok", "decision", "artifact_count", "locally_valid_artifacts", "all_final_artifacts_remeasured", "experiments_run", "submission_slots_used")}, indent=2))
    return 0 if report["audit_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
