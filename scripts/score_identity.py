"""Conservative association of owner-reported entries with raster filenames.

A filename is not a submission-page receipt, nor is a shared hash-like token
proof of pixel or byte identity. This helper only associates a result when an
entire submission stem matches, optionally after removing the actual source
site's known project prefix. Ambiguous matches are rejected. Cross-site
identity requires separate, explicitly measured raster hashes.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
import re


_SITE = re.compile(r"GEMSDOE([0-9]+)\Z", re.IGNORECASE)
_SAFE_NAME = re.compile(r"[A-Za-z0-9_.-]+\Z")


def submission_stem_matches(site: str, submission: str, raster_filename: str) -> bool:
    """True only for an exact full stem, or one approved same-site prefix.

    Format suffixes such as ``-nan`` and ``-zeros`` are intentionally NOT
    stripped: those names may identify different bytes or portal behavior.
    """
    match = _SITE.fullmatch(site) if isinstance(site, str) else None
    if not match or not isinstance(submission, str) or not _SAFE_NAME.fullmatch(submission):
        return False
    if not isinstance(raster_filename, str) or Path(raster_filename).name != raster_filename:
        return False
    name = Path(raster_filename)
    if name.suffix.lower() not in ('.tif', '.tiff'):
        return False
    entry, actual = submission.casefold(), name.stem.casefold()
    number = match.group(1)
    return actual in {entry, f'gems{number}-{entry}', f'gemsdoe{number}-{entry}'}


def match_owner_score(site: str, raster_filename: str, records: list[dict]) -> dict | None:
    """Return one unambiguous same-site ledger row; otherwise return None.

    Duplicate rows with the same name AND result are harmless; conflicting
    results or conflicting candidate identities fail closed. The evidence class
    stays owner-reported and must never be relabeled ORGANIZER-CONFIRMED.
    """
    if not isinstance(site, str) or not _SITE.fullmatch(site):
        return None
    matches = [row for row in records if isinstance(row, dict)
               and isinstance(row.get('site'), str) and row['site'].casefold() == site.casefold()
               and row.get('score') and submission_stem_matches(site, row.get('submission', ''), raster_filename)]
    identities = set()
    for row in matches:
        try:
            score = Decimal(str(row['score']))
        except (InvalidOperation, ValueError, TypeError):
            return None
        if not score.is_finite() or not Decimal(0) <= score <= Decimal(1):
            return None
        identities.add((row['submission'].casefold(), score))
    if len(identities) != 1:
        return None
    return matches[0]


def owner_score_for_path(relative_path: str, records: list[dict]) -> float | None:
    """Associate only explicitly identifiable same-site historical paths.

    Local research downloads are never matched to the owner ledger. A namespace
    like ``GEMSDOE28__`` takes precedence over a filename prefix; absent either,
    or on an ambiguous/non-numeric result, the answer is unknown.
    """
    if not isinstance(relative_path, str):
        return None
    path = Path(relative_path)
    if any(part.casefold() == 'downloads' for part in path.parts):
        return None
    name = path.name
    if '__' in name:
        namespace, name = name.split('__', 1)
        if not _SITE.fullmatch(namespace):
            return None
        site = namespace.upper()
    else:
        match = re.match(r'gems(?:doe)?([0-9]+)[-_]', name, re.IGNORECASE)
        if not match:
            return None
        site = 'GEMSDOE' + match.group(1)
    row = match_owner_score(site, name, records)
    if row is None:
        return None
    try:
        value = float(row['score'])
    except (ValueError, TypeError):
        return None
    return value if 0 <= value <= 1 else None
