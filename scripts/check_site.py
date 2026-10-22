#!/usr/bin/env python3
"""Validate static-site links, evidence labels, run-card consistency, and download gating."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HTML_FILES = (
    "index.html",
    "executive-summary.html",
    "research.html",
    "hypotheses.html",
    "sources.html",
    "prior-art.html",
)


class MarkupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.download_anchor: dict[str, str | None] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if attr.get("id"):
            self.ids.add(str(attr["id"]))
        if tag.lower() == "a":
            href = attr.get("href")
            if href is not None:
                self.links.append(href)
            if attr.get("id") == "submission-download":
                self.download_anchor = {"href": href, "aria-disabled": attr.get("aria-disabled")}


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def check_internal_links() -> list[str]:
    errors: list[str] = []
    parsed_by_file: dict[str, MarkupParser] = {}
    for relative in HTML_FILES:
        path = DOCS / relative
        if not path.is_file():
            errors.append(f"Missing HTML page: docs/{relative}")
            continue
        parser = MarkupParser()
        parser.feed(path.read_text(encoding="utf-8"))
        parsed_by_file[relative] = parser

    for relative, parser in parsed_by_file.items():
        for href in parser.links:
            if href.startswith(("https://", "http://", "mailto:", "tel:", "javascript:")):
                continue
            target = urlparse(href)
            if target.path:
                target_path = (DOCS / relative).parent / unquote(target.path)
                if target_path.is_dir():
                    target_path = target_path / "index.html"
                if not target_path.is_file():
                    errors.append(f"Broken local link in docs/{relative}: {href}")
                    continue
                if target.fragment and target_path.suffix.lower() == ".html":
                    target_rel = str(target_path.relative_to(DOCS))
                    target_parser = parsed_by_file.get(target_rel)
                    if target_parser is None:
                        target_parser = MarkupParser()
                        target_parser.feed(target_path.read_text(encoding="utf-8"))
                    if target.fragment not in target_parser.ids:
                        errors.append(f"Missing fragment #{target.fragment} in {target_path.relative_to(DOCS)}")
            elif target.fragment and target.fragment not in parser.ids:
                errors.append(f"Missing fragment #{target.fragment} in docs/{relative}")
    return errors


def check_run_card_and_download_gate() -> list[str]:
    errors: list[str] = []
    card = _load_json(DOCS / "data" / "run-card.json")
    artifact = card.get("artifact", {})
    download = artifact.get("download_available") is True
    safe = artifact.get("submission_safe") is True
    tiff_rel = artifact.get("tiff_path")
    downloads_dir = DOCS / "downloads"
    tiffs = list(downloads_dir.glob("*.tif")) if downloads_dir.exists() else []
    zips = list(downloads_dir.glob("*.zip")) if downloads_dir.exists() else []
    receipts = list(downloads_dir.glob("*.json")) if downloads_dir.exists() else []

    index = (DOCS / "index.html").read_text(encoding="utf-8")
    parser = MarkupParser()
    parser.feed(index)
    anchor = parser.download_anchor
    if anchor is None:
        errors.append("Overview page lacks the gated submission-download control")
    elif not download:
        if anchor.get("href") is not None or anchor.get("aria-disabled") != "true":
            errors.append("Blocked state must not expose an active TIFF download link")
        if tiffs or zips or receipts:
            errors.append("Submission TIFF/ZIP/receipt files are present but the run card does not mark an artifact approved")
        if "do not upload" not in index.lower():
            errors.append("Blocked overview must visibly warn against submitting")
    else:
        if not safe:
            errors.append("Run card exposes a download without submission_safe=true")
        package_paths = (
            ("TIFF", tiff_rel, artifact.get("tiff_sha256"), r"downloads/[A-Za-z0-9._-]+\.tif"),
            ("ZIP", artifact.get("zip_path"), artifact.get("zip_sha256"), r"downloads/[A-Za-z0-9._-]+\.zip"),
            ("writer receipt", artifact.get("writer_receipt_path"), artifact.get("writer_receipt_sha256"), r"downloads/[A-Za-z0-9._-]+\.json"),
        )
        expected_files: set[Path] = set()
        for label, relative, expected_hash, pattern in package_paths:
            if not isinstance(relative, str) or not re.fullmatch(pattern, relative):
                errors.append(f"Approved {label} path is missing or unsafe")
                continue
            target = DOCS / relative
            expected_files.add(target)
            if not target.is_file():
                errors.append(f"Run-card-approved {label} does not exist: {relative}")
                continue
            actual_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            if not re.fullmatch(r"[a-fA-F0-9]{64}", str(expected_hash or "")) or actual_hash.lower() != str(expected_hash).lower():
                errors.append(f"Run-card {label} SHA-256 does not match published bytes")
        actual_files = set(tiffs + zips + receipts)
        if expected_files and actual_files != expected_files:
            errors.append("docs/downloads must contain only the one approved TIFF, its ZIP, and its writer receipt")
        if card.get("holdout", {}).get("status") != "PASS":
            errors.append("Run card exposes a TIFF without passing holdout status")
        if card.get("uniqueness", {}).get("status") != "PASS":
            errors.append("Run card exposes a TIFF without passing uniqueness status")
        uniqueness = card.get("uniqueness", {})
        corr_values = (
            uniqueness.get("surface_max_spearman_rank_correlation"),
            uniqueness.get("final_raster_max_spearman_rank_correlation"),
            uniqueness.get("max_3px_dot_overlap_fraction"),
        )
        if not all(isinstance(value, (int, float)) for value in corr_values):
            errors.append("Approved TIFF lacks numeric surface/raster uniqueness evidence")
        elif corr_values[0] > 0.90 or corr_values[1] > 0.90 or corr_values[2] > 0.70:
            errors.append("Approved TIFF exceeds a stop-and-record duplicate threshold")
        if not re.fullmatch(r"[a-fA-F0-9]{64}", str(uniqueness.get("registry_index_sha256", ""))):
            errors.append("Approved TIFF lacks a hash-verified registry index reference")
        validator = card.get("validator", {})
        if validator.get("status") != "PASS" or validator.get("shared_submission_writer_used") is not True:
            errors.append("Run card exposes a TIFF without shared-writer validation")
        required_checks = {
            "source_data_provenance_authorized",
            "template_grid_and_dimensions_match",
            "crs_epsg_32611",
            "pixel_size_100m",
            "single_band_float32",
            "values_finite_and_within_0_to_1",
            "footprint_and_catalogue_support",
            "visible_fault_pixels_masked_exactly",
            "surface_uniqueness_passed",
            "final_raster_uniqueness_passed",
            "on_disk_tiff_validated_by_shared_writer",
            "one_tiff_zip_and_receipt_written_atomically",
        }
        validator_checks = validator.get("checks", {})
        if not required_checks.issubset(validator_checks) or any(validator_checks.get(name) is not True for name in required_checks):
            errors.append("Every required non-organizer validator check must be true before download")
        site_js = (DOCS / "site.js").read_text(encoding="utf-8")
        if not anchor or anchor.get("aria-disabled") != "true" or "submission-download" not in site_js:
            errors.append("Approved run-card TIFF is not protected by the client-side fail-closed gate")

    holdout = card.get("holdout", {})
    if holdout.get("evidence_class") != "HOLDOUT-DTI":
        errors.append("Run card must keep the required HOLDOUT-DTI evidence label")
    if holdout.get("status") == "NOT_RUN" and any(
        holdout.get(key) is not None for key in ("pooled_dti", "withheld_positive_pixels", "ci95")
    ):
        errors.append("An unrun holdout must not carry a DTI, withheld count, or CI")
    if card.get("decision") != "NO_CANDIDATE_PROMOTED_NO_SUBMISSION" and card.get("run_status") == "BLOCKED_NO_EXPERIMENT":
        errors.append("Blocked run decision conflicts with run status")
    return errors


def check_evidence_labels() -> list[str]:
    errors: list[str] = []
    board = _load_json(DOCS / "data" / "leaderboard.json")
    if board.get("evidence_class") != "ORGANIZER-CONFIRMED":
        errors.append("Leaderboard snapshot lacks ORGANIZER-CONFIRMED evidence label")
    for row in board.get("rows", []):
        if row.get("evidence_class") != "ORGANIZER-CONFIRMED":
            errors.append("Leaderboard row lacks ORGANIZER-CONFIRMED evidence label")
        if "not a GEMSDOE86" not in row.get("evidence_scope", ""):
            errors.append("Leaderboard row scope must distinguish external scores from this project")
        score = row.get("score")
        if not isinstance(score, (float, int)) or not 0 <= score <= 1:
            errors.append("Leaderboard score is invalid")
    if not board.get("rows"):
        errors.append("Leaderboard snapshot contains no rows")
    return errors


def main() -> int:
    required = (
        DOCS / "data" / "run-card.json",
        DOCS / "data" / "leaderboard.json",
        DOCS / "data" / "preflight.json",
    )
    errors = [f"Missing required site data: {path.relative_to(ROOT)}" for path in required if not path.is_file()]
    if not errors:
        errors.extend(check_internal_links())
        errors.extend(check_run_card_and_download_gate())
        errors.extend(check_evidence_labels())
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("Site checks passed: links, evidence labels, run card, and fail-closed download gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
