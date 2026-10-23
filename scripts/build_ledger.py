#!/usr/bin/env python3
"""Build ``ledger/submissions.csv`` — one canonical generator for the whole repo.

Why this script exists
----------------------
The brief expects ``ledger/submissions.csv`` and, if absent, a rebuild from
``ledger/raw_paste.txt``.  Neither existed; the only committed transcription of
the team's submission history is ``registry/prior_scores.csv`` (itself
transcribed from ``research/REQUEST_20261023.md``, owner-supplied text).  Two
sessions on 2026-10-23 seeded a ledger independently.  This module is the single
generator so the file cannot drift; it reproduces the schema introduced by
``scripts/build_r0_prune.py`` (``LEDGER_FIELDS``) and adds every candidate that
``scripts/prune_collar.py`` records in ``ledger/variants.json``.

It never invents a receipt.  A score becomes ``RECEIPT`` only when a human
pastes a submission-page receipt into ``receipt_score`` / ``date``.

Dedupe rules (explicit, and the only ones applied)
--------------------------------------------------
1. A content digest (``sha8``, or the full ``sha256`` when the file is local)
   identifies a file byte-for-byte.
2. The ``-nan`` / ``-zeros`` / ``-allfinite`` / ``-zero`` suffix only changes the
   out-of-footprint fill, which scores identically (brief §3), so names that
   differ only by it collapse.
3. Names identical after (1)+(2) collapse.
Collapsed groups keep the highest reported number; ``triples`` counts how many
source rows were merged so nothing is silently dropped (``ledger/DEDUPE.md``).

Usage
-----
    python scripts/build_ledger.py            # write ledger/submissions.csv
    python scripts/build_ledger.py --check    # exit 1 if the file is stale
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "registry" / "prior_scores.csv"
LEDGER = ROOT / "ledger"
FLEET = ROOT / "data" / "scored_fleet"

FILL_SUFFIX = re.compile(r"-(?:nan|zeros|allfinite|zero)$", re.IGNORECASE)
# Hex tokens of length 8.  All-digit tokens are date/time stamps (20261004,
# 220000Z, ...) and are never a content digest, so they are skipped.
HEX8 = re.compile(r"[0-9a-f]{8}", re.IGNORECASE)
ALL_DIGITS = re.compile(r"\d{8}")

# Schema introduced by scripts/build_r0_prune.py (kept byte-compatible).
COLUMNS = [
    "site", "name", "score", "encoding", "n_dots", "sha8", "parent", "receipt",
    "id", "axis", "value", "pct_changed", "sha256", "status", "predicted_change",
    "receipt_score", "date", "evidence_class", "source_url",
]

# R0 lineage constants (brief §1).  The parent file is pinned by sha256 in
# scripts/fetch_registry.py (EXTRA[0]); measured here, never assumed.
R0_NAME = "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros"
R0_SHA256 = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
R0_PARENT_LABEL = "h27-4-r1-solo-d2-8"
R0_AXIS, R0_VALUE = "PRUNE", "2"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha8_of(name: str) -> str:
    """Last non-date 8-character hex token in a submission name, else ''."""
    tokens = [t.lower() for t in HEX8.findall(FILL_SUFFIX.sub("", name.strip()))]
    tokens = [t for t in tokens if not ALL_DIGITS.fullmatch(t)]
    return tokens[-1] if tokens else ""


def fingerprint(name: str) -> str:
    """Stable identity key for one submission name (rules 1-3 above)."""
    base = FILL_SUFFIX.sub("", name.strip())
    return sha8_of(base) or base.lower()


def encoding_of(name: str) -> str:
    low = name.lower()
    for suffix, label in (("-nan", "nan"), ("-zeros", "zeros"), ("-allfinite", "allfinite")):
        if low.endswith(suffix):
            return label
    return "unknown"


def measured_dots(path: Path) -> int | None:
    try:
        import rasterio
    except ModuleNotFoundError:  # pragma: no cover - CI installs rasterio
        return None
    with rasterio.open(path) as src:
        return int((np.asarray(src.read(1)) > 0).sum())


def fleet_index() -> dict[str, Path]:
    """Map fingerprint -> local raster, for the rows we actually hold."""
    out: dict[str, Path] = {}
    if not FLEET.is_dir():
        return out
    for p in sorted(FLEET.glob("*.tif")):
        out.setdefault(fingerprint(p.stem.split("__", 1)[-1]), p)
    return out


def variant_rows() -> list[dict]:
    """Rows for rasters built by this repository, from ``ledger/variants*.json``.

    ``variants.json`` is written by ``scripts/prune_collar.py`` and
    ``variants_snap.json`` by ``scripts/build_r0_snap.py``; a concurrent
    session's candidate (PR #28) is carried in ``variants_external.json`` with
    its provenance so one generator reproduces the whole ledger.
    """
    out = []
    entries = []
    for name in ("variants.json", "variants_external.json", "variants_snap.json"):
        src = LEDGER / name
        if src.is_file():
            entries += json.loads(src.read_text(encoding="utf-8"))
    for v in entries:
        out.append({
            "site": v.get("site", "GEMSDOE86"),
            "name": v["id"],
            "score": "",
            "encoding": v.get("encoding", "nan"),
            "n_dots": str(v.get("n_dots", "")),
            "sha8": v.get("sha8", ""),
            "parent": v.get("parent", ""),
            "receipt": "N" if not v.get("receipt_score") else "Y",
            "id": v["id"],
            "axis": str(v.get("axis", "")).upper(),
            "value": str(v.get("value", "")),
            "pct_changed": str(v.get("pct_changed", "")),
            # house convention: the ledger's sha256 is the zeros twin's digest
            "sha256": v.get("sha256_zeros") or v.get("sha256", ""),
            "status": v.get("status", "BUILT"),
            "predicted_change": v.get("predicted_change", ""),
            "receipt_score": v.get("receipt_score", ""),
            "date": v.get("receipt_date", ""),
            "evidence_class": "MODEL" if not v.get("receipt_score") else "RECEIPT",
            "source_url": v.get("source_url", ""),
        })
    return out


def build_rows() -> list[dict]:
    with SOURCE.open(newline="", encoding="utf-8") as fh:
        source_rows = list(csv.DictReader(fh))
    if not source_rows:
        raise SystemExit(f"{SOURCE} has no rows")

    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for row in source_rows:
        name = (row.get("submission") or "").strip()
        # e.g. GEMSDOE84..88: a site with no named artifact. Keep it visible so
        # the ledger is not mistaken for a complete inventory.
        key = fingerprint(name) if name else "site:" + (row.get("site") or "").lower()
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(row)

    local = fleet_index()
    out: list[dict] = []
    for key in order:
        rows = groups[key]
        scored = [r for r in rows if (r.get("score") or "").strip()]
        chosen = max(scored, key=lambda r: float(r["score"])) if scored else rows[0]
        name = (chosen.get("submission") or "").strip()
        path = local.get(key)
        sha = sha256_file(path) if path else ""
        is_r0 = bool(sha) and sha == R0_SHA256
        score = (chosen.get("score") or "").strip()
        out.append({
            "site": (chosen.get("site") or "").strip(),
            "name": name or f"site:{chosen.get('site', '')}",
            "score": score,
            "encoding": encoding_of(name) if name else "",
            "n_dots": "" if path is None or measured_dots(path) is None else str(measured_dots(path)),
            "sha8": (sha[:8] if sha else sha8_of(name)),
            "parent": R0_PARENT_LABEL if is_r0 else "",
            "receipt": "N",
            "id": "",
            "axis": R0_AXIS if is_r0 else "",
            "value": R0_VALUE if is_r0 else "",
            "pct_changed": "",
            "sha256": sha,
            "status": "HISTORICAL",
            "predicted_change": "",
            "receipt_score": "",
            "date": "",
            "evidence_class": "CLAIM" if score else "NO-EVIDENCE",
            "source_url": (chosen.get("source_url") or "").strip(),
        })
    return out


def render(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\r\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in COLUMNS})
    return buf.getvalue()


def dedupe_note() -> str:
    """Human-readable record of what the collapse did (brief §3 repeats)."""
    with SOURCE.open(newline="", encoding="utf-8") as fh:
        src = list(csv.DictReader(fh))
    groups: dict[str, list[str]] = {}
    for row in src:
        name = (row.get("submission") or "").strip()
        key = fingerprint(name) if name else "site:" + (row.get("site") or "").lower()
        groups.setdefault(key, []).append(name or f"site:{row.get('site', '')}")
    lines = ["# Ledger dedupe record", "",
             f"Source: `registry/prior_scores.csv` ({len(src)} rows). "
             f"Collapsed to {len(groups)} groups by the rules in `scripts/build_ledger.py`.",
             "", "| kept | merged rows |", "|---|---|"]
    for key, names in groups.items():
        if len(names) > 1:
            lines.append(f"| `{names[0]}` | {len(names)} |")
    lines += ["", "Fill-only twins (`-nan` / `-zeros` / `-allfinite`) collapse because they score",
              "identically (brief §3); exact content digests collapse because they are the same file.", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if the ledger is stale")
    ap.add_argument("--json", action="store_true", help="summarise to stdout as JSON")
    args = ap.parse_args()

    rows = build_rows() + variant_rows()
    text = render(rows)
    LEDGER.mkdir(parents=True, exist_ok=True)
    target = LEDGER / "submissions.csv"
    if args.check:
        # compare BYTES: text mode would translate the file's CRLF line endings
        if not target.is_file() or target.read_bytes().decode("utf-8") != text:
            print(f"STALE: {target.relative_to(ROOT)} does not match its generator", file=sys.stderr)
            return 1
        print(f"OK: {target.relative_to(ROOT)} matches its generator")
        return 0
    target.write_bytes(text.encode("utf-8"))
    (LEDGER / "DEDUPE.md").write_text(dedupe_note(), encoding="utf-8")
    if args.json:
        print(json.dumps({
            "rows": len(rows),
            "historic": sum(1 for r in rows if r["status"] == "HISTORICAL"),
            "built": sum(1 for r in rows if r["status"] == "BUILT"),
            "receipts": sum(1 for r in rows if r["evidence_class"] == "RECEIPT"),
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
