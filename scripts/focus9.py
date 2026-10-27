"""Bind the nine-site summary to owner claims and explicitly scoped evidence.

This module is read-only. A named historical winner is not a unique candidate,
its owner-reported number is not an organizer receipt, and a pairwise overlap is
not a full-registry uniqueness scan. Links are offered only when an independent
byte check binds the historical observation to the exact pinned Git blob.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
from urllib.parse import quote

from scripts.audit_release import sha256, strict_json
from scripts.score_identity import submission_stem_matches

SITES = ('GEMSDOE24', 'GEMSDOE25', 'GEMSDOE27', 'GEMSDOE28', 'GEMSDOE30',
         'GEMSDOE31', 'GEMSDOE32', 'GEMSDOE33', 'GEMSDOE36')
_HEX40 = re.compile(r'[0-9a-f]{40}\Z')
_HEX64 = re.compile(r'[0-9a-f]{64}\Z')


def read_ledger(path: Path) -> list[dict]:
    with path.open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def best_claims(records: list[dict]) -> dict[str, list[dict]]:
    """Select *all tied* highest supplied claims; reject conflicting identities."""
    result = {}
    for site in SITES:
        candidates = []
        observed = {}
        for row in records:
            if row.get('site') != site or not row.get('score'):
                continue
            if not row.get('evidence_class', '').startswith('OWNER-REPORTED'):
                raise ValueError(f'{site}: non-owner score cannot be silently relabeled')
            name = row.get('submission', '')
            if not isinstance(name, str) or not submission_stem_matches(site, name, name + '.tif'):
                raise ValueError(f'{site}: invalid submission name')
            try:
                value = Decimal(row['score'])
            except (InvalidOperation, TypeError) as exc:
                raise ValueError(f'{site}: invalid owner-reported result') from exc
            if not value.is_finite() or not Decimal(0) <= value <= Decimal(1):
                raise ValueError(f'{site}: owner-reported result outside [0,1]')
            key = name.casefold()
            if key in observed and observed[key] != value:
                raise ValueError(f'{site}: conflicting results for the same submission')
            observed[key] = value
            candidates.append((value, row))
        if not candidates:
            result[site] = []
            continue
        high = max(value for value, _ in candidates)
        # Do not repeat duplicate identical ledger rows.
        unique = {}
        for value, row in candidates:
            if value == high:
                unique.setdefault(row['submission'].casefold(), row)
        result[site] = list(unique.values())
    return result


def forensic_match(site: str, submission: str, forensic: dict) -> dict | None:
    matches = []
    for row in forensic.get('rasters', []):
        if not isinstance(row, dict):
            continue
        value = row.get('file')
        prefix = site + '__'
        if isinstance(value, str) and value.casefold().startswith(prefix.casefold()):
            filename = value[len(prefix):]
            if submission_stem_matches(site, submission, filename):
                matches.append(row)
    return matches[0] if len(matches) == 1 else None


def snapshot_match(site: str, filename: str, feed: dict) -> tuple[dict, dict] | None:
    """Find one exact docs/downloads object in a complete, pinned Git tree."""
    projects = [r for r in feed.get('projects', [])
                if r.get('repository') == f'buffedlizard55-lab/{site}']
    if len(projects) != 1:
        return None
    project = projects[0]
    if project.get('status') != 'SNAPSHOT_OK' or not _HEX40.fullmatch(project.get('commit_sha', '')):
        return None
    expected_path = 'docs/downloads/' + filename
    matches = [r for r in project.get('tif_git_objects', []) if r.get('path') == expected_path]
    if len(matches) != 1 or not _HEX40.fullmatch(matches[0].get('git_blob_sha1', '')):
        return None
    return project, matches[0]


def validated_witness(site: str, claim: dict, evidence: dict, forensic: dict) -> dict | None:
    """Read a pinned retrospective observation, never infer identity from a token."""
    rows = [r for r in evidence.get('winners', [])
            if isinstance(r, dict) and r.get('site') == site and r.get('submission') == claim.get('submission')
            and r.get('owner_reported_result') == claim.get('score')]
    if len(rows) != 1:
        return None
    row = rows[0]
    observed = forensic_match(site, claim['submission'], forensic)
    if observed is None or row.get('forensic_file') != observed.get('file'):
        return None
    filename = observed['file'].split('__', 1)[1]
    expected = observed.get('sha256', '')
    valid_hex64 = isinstance(expected, str) and _HEX64.fullmatch(expected)
    commit = row.get('source_commit')
    blob = row.get('git_blob_sha1')
    size = row.get('bytes')
    evidence_class = row.get('evidence_class')
    if (not valid_hex64 or row.get('sha256') != expected
            or row.get('archived_sha256_matches') is not True
            or row.get('git_object_matches') is not True
            or not isinstance(evidence_class, str) or not evidence_class.startswith('OWNER-REPORTED')
            or not isinstance(size, int) or isinstance(size, bool) or size <= 0
            or row.get('source_repository') != f'buffedlizard55-lab/{site}'
            or row.get('source_path') != 'docs/downloads/' + filename
            or not isinstance(commit, str) or not _HEX40.fullmatch(commit)
            or not isinstance(blob, str) or not _HEX40.fullmatch(blob)):
        return None
    return row


def rows(root: Path) -> list[dict]:
    ledger = read_ledger(root / 'registry/prior_scores.csv')
    claims = best_claims(ledger)
    forensic_path = root / 'docs/evidence/focus9-forensics-20261026-rev2.json'
    forensic = strict_json(forensic_path)
    evidence = strict_json(root / 'docs/evidence/focus9-champions-20261027.json')
    if (evidence.get('schema') != 'gems86.focus9-champion-byte-audit.v1'
            or evidence.get('forensic_sha256') != sha256(forensic_path)):
        raise ValueError('Focus-9 byte audit is not bound to the archived forensic evidence')
    result = []
    for site in SITES:
        entries = claims[site]
        if not entries:
            result.append(dict(site=site, claim=None, witness=None, url=None))
        for claim in entries:
            witness = validated_witness(site, claim, evidence, forensic)
            url = None
            if witness:
                # The commit and paths have already passed exact format/identity checks.
                url = (f"https://github.com/{witness['source_repository']}/raw/"
                       f"{witness['source_commit']}/{quote(witness['source_path'], safe='/')}")
            observation = forensic_match(site, claim['submission'], forensic) if witness else None
            overlap = observation.get('overlap_3px_vs_H33') if observation else None
            if not isinstance(overlap, (int, float)) or not 0 <= overlap <= 1:
                overlap = None
            result.append(dict(site=site, claim=claim, witness=witness, url=url,
                               overlap_3px_vs_h33=overlap,
                               forensic_measured_utc=forensic.get('measured_utc')))
    return result
