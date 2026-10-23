#!/usr/bin/env python3
"""Build ``ledger/submissions.csv`` from the transcribed team score table.

Why this script exists
----------------------
The session brief expects ``ledger/submissions.csv`` and, if that is absent, a
rebuild from ``ledger/raw_paste.txt``.  Neither file exists in this checkout.
The only transcription of the team's submission history that *is* committed is
``registry/prior_scores.csv`` (itself transcribed from
``research/REQUEST_20261023.md``, i.e. owner-supplied prompt text).  This script
converts that transcription into the brief's ledger schema, adds measured
columns where a raster is present in ``data/scored_fleet/``, and collapses exact
repeats.  It never invents a receipt.

Evidence classes (brief section 8)
-----------------------------------
Every historic row starts as ``CLAIM``: an owner-reported number with no
submission-page receipt in this checkout.  A row becomes ``RECEIPT`` only when a
human pastes a submission-page receipt into ``receipt_score`` /
``receipt_date``.  Nothing here can promote a score.

Dedupe rules (explicit, and the only ones applied)
--------------------------------------------------
1. ``sha8`` extracted from the submission name, when present, identifies a file
   byte-for-byte.  Two rows sharing a ``sha8`` are the same file.
2. The ``-nan`` / ``-zeros`` / ``-allfinite`` / ``-zero`` suffix only changes the
   out-of-footprint fill, which scores identically (brief section 3), so rows
   whose names differ only by that suffix collapse.
3. Rows whose names are otherwise identical after (1)+(2) collapse.
Collapsed groups keep the highest reported number and record ``twins`` = the
number of collapsed rows, so nothing is silently dropped.

Usage
-----
    python scripts/build_ledger.py            # write ledger/submissions.csv
    python scripts/build_ledger.py --check    # exit 1 if the file is stale
"""
from __future__ import annotations

import argparse
import csv
import hashlib
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
# Hex tokens of length 8.  All-digit tokens are date/time stamps
# (20261004, 220000Z, ...) and are never a content digest, so they are skipped.
HEX8 = re.compile(r"[0-9a-f]{8}", re.IGNORECASE)
ALL_DIGITS = re.compile(r"\d{8}")

# Columns written to the ledger.  ``receipt_score``/``receipt_date`` are left
# empty on purpose: only a human can copy them from a submission-page receipt.
COLUMNS = [
    "id", "site", "parent", "axis", "value", "n_dots", "pct_changed",
    "sha256", "sha8", "status", "predicted_change",
    "receipt_score", "receipt_date", "evidence_class", "twins", "source_url",
]

# R0 lineage constants (brief section 1).  The parent's own file is pinned by
# sha256 in scripts/fetch_registry.py (EXTRA[0]); measured here, not assumed.
R0_NAME = "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros"
R0_SHA256 = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"


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


def measured_dots(path: Path) -> int | None:
    try:
        import rasterio
    except ModuleNotFoundError:  # pragma: no cover - CI installs rasterio
        return None
    with rasterio.open(path) as src:
        a = src.read(1)
    return int((np.asarray(a) > 0).sum())


def fleet_index() -> dict[str, Path]:
    """Map sha8/fingerprint -> local raster, for the rows we actually hold."""
    out: dict[str, Path] = {}
    if not FLEET.is_dir():
        return out
    for p in sorted(FLEET.glob("*.tif")):
        stem = p.stem.split("__", 1)[-1]
        out.setdefault(fingerprint(stem), p)
    return out


def variant_rows() -> list[dict]:
    """Rows for rasters this repository built, from ``ledger/variants.json``.

    The file is written by ``scripts/prune_collar.py``; a build row is
    ``status=BUILT`` with no score until a human pastes a receipt.  Its
    ``predicted_change`` is MODEL class by construction and never a score.
    """
    src = LEDGER / "variants.json"
    if not src.is_file():
        return []
    out = []
    for v in json.loads(src.read_text(encoding="utf-8")):
        out.append({
            "id": v["id"],
            "site": "GEMSDOE86",
            "parent": v.get("parent", ""),
            "axis": v.get("axis", ""),
            "value": str(v.get("value", "")),
            "n_dots": str(v.get("n_dots", "")),
            "pct_changed": str(v.get("pct_changed", "")),
            "sha256": v.get("sha256", ""),
            "sha8": v.get("sha8", ""),
            "status": v.get("status", "BUILT"),
            "predicted_change": v.get("predicted_change", ""),
            "receipt_score": v.get("receipt_score", ""),
            "receipt_date": v.get("receipt_date", ""),
            "evidence_class": "MODEL-PREDICTION (unscored)",
            "twins": "1",
            "source_url": "releases/" + str(v.get("files", [""])[0]),
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
        if not name:
            # e.g. GEMSDOE84..88: a site with no named artifact. Keep it visible
            # so the ledger is not mistaken for a complete inventory.
            key = "site:" + (row.get("site") or "").strip().lower()
        else:
            key = fingerprint(name)
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
        sha8 = sha8_of(name) if name else ""
        path = local.get(key)
        sha = sha256_file(path) if path else ""
        n_dots = measured_dots(path) if path else None
        score = (chosen.get("score") or "").strip()
        status = "SCORED-CLAIM" if score else "NO-SCORE-SUPPLIED"
        if sha and sha == R0_SHA256:
            parent = ""
            status = "SCORED-CLAIM (R0 parent of this session)"
        else:
            parent = ""
        out.append({
            "id": name or f"site:{chosen.get('site', '')}",
            "site": (chosen.get("site") or "").strip(),
            "parent": parent,
            "axis": "",
            "value": "",
            "n_dots": "" if n_dots is None else str(n_dots),
            "pct_changed": "",
            "sha256": sha,
            "sha8": sha8 if re.fullmatch(r"[0-9a-f]{8}", sha8 or "") else "",
            "status": status,
            # A claim is not a prediction and never becomes one.
            "predicted_change": "",
            "receipt_score": "",
            "receipt_date": "",
            "evidence_class": "CLAIM" if score else "NO-EVIDENCE",
            "twins": str(len(rows)),
            "source_url": (chosen.get("source_url") or "").strip(),
        })
    return out


def render(rows: list[dict]) -> str:
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in COLUMNS})
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if the ledger is stale")
    ap.add_argument("--json", action="store_true", help="also summarise to stdout as JSON")
    args = ap.parse_args()

    rows = build_rows() + variant_rows()
    text = render(rows)
    LEDGER.mkdir(parents=True, exist_ok=True)
    target = LEDGER / "submissions.csv"
    if args.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != text:
            print(f"STALE: {target.relative_to(ROOT)} does not match {SOURCE.name}", file=sys.stderr)
            return 1
        print(f"OK: {target.relative_to(ROOT)} matches {SOURCE.name}")
        return 0
    target.write_text(text, encoding="utf-8")
    if args.json:
        print(json.dumps({
            "rows": len(rows),
            "collapsed_source_rows": sum(int(r["twins"]) for r in rows),
            "scored_claim": sum(1 for r in rows if r["status"].startswith("SCORED")),
            "receipts": sum(1 for r in rows if r["evidence_class"] == "RECEIPT"),
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
