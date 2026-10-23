#!/usr/bin/env python3
"""Assemble ``ledger/submissions.csv``: the transcribed history plus this session's builds.

History source: ``registry/prior_scores.csv`` (the repo's transcription of the owner's
per-site claims).  ``ledger/raw_paste.txt`` does not exist in this checkout, so that file
is the equivalent input the brief allows.  Every historical row is evidence class CLAIM -
owner-reported, no submission-page receipt - and is copied through unchanged.

Variant rows come from ``evidence/axis_variants.json``, written by
``scripts/build_axis_variants.py``.  Their ``receipt_score`` and ``receipt_date`` stay
empty: only the human can fill them from a submission-page receipt.

Repeats are collapsed on (site, name): the first transcription wins and the duplicate
count is recorded, because the brief notes that at least eight slots went to exact
repeats.

Usage::  .venv/bin/python scripts/build_ledger.py
"""
from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / "registry" / "prior_scores.csv"
VARIANTS = ROOT / "evidence" / "axis_variants.json"
OUT = ROOT / "ledger" / "submissions.csv"

HEADER = ["id", "site", "name", "score", "encoding", "n_dots", "sha8", "parent", "axis",
          "value", "pct_changed", "sha256_nan", "sha256_zeros", "status", "evidence_class",
          "predicted_change", "receipt_score", "receipt_date", "duplicates_collapsed",
          "source"]

HEX8 = re.compile(r"(?<![0-9a-f])([0-9a-f]{8})(?![0-9a-f])")
HEX12 = re.compile(r"(?<![0-9a-f])([0-9a-f]{12})(?![0-9a-f])")


def encoding_of(name: str) -> str:
    low = name.lower()
    if low.endswith("-nan") or "-nan." in low or low.endswith("nan-outside"):
        return "nan-outside"
    if "zeros" in low or "zero" in low or "allfinite" in low:
        return "zeros-outside"
    return "unrecorded"


def sha8_of(name: str) -> str:
    """Longest trailing hex token, if it looks like a digest and not a date.

    Pure-digit tokens (``20260925``, ``20261006``) are timestamps in these names, not
    hashes; counting them as sha8 would manufacture duplicates that do not exist.
    """
    for tok in reversed(HEX12.findall(name) + HEX8.findall(name)):
        if any(ch in "abcdef" for ch in tok):
            return tok[:8]
    return ""


def history_rows() -> list[dict]:
    rows: list[dict] = []
    seen: dict[tuple[str, str], dict] = {}
    with PRIOR.open(newline="") as fh:
        for rec in csv.DictReader(fh):
            site, name = rec["site"].strip(), rec["submission"].strip()
            key = (site, name)
            if key in seen:
                seen[key]["duplicates_collapsed"] = str(int(seen[key]["duplicates_collapsed"]) + 1)
                continue
            row = {"id": f"{site}::{name}", "site": site, "name": name, "score": rec["score"],
                   "encoding": encoding_of(name), "n_dots": "", "sha8": sha8_of(name),
                   "parent": "", "axis": "", "value": "", "pct_changed": "",
                   "sha256_nan": "", "sha256_zeros": "", "status": "SUBMITTED-BY-OWNER",
                   "evidence_class": rec["evidence_class"].strip(), "predicted_change": "",
                   "receipt_score": "", "receipt_date": "", "duplicates_collapsed": "0",
                   "source": rec["source_url"].strip()}
            rows.append(row)
            seen[key] = row
    return rows


def variant_rows() -> list[dict]:
    if not VARIANTS.is_file():
        return []
    data = json.loads(VARIANTS.read_text())
    rows = []
    for c in data["variants"]:
        d = c["parent_diff"]
        rows.append({
            "id": c["id"], "site": "GEMSDOE86", "name": c["id"], "score": "",
            "encoding": "nan-outside + zeros-outside twins", "n_dots": str(d["variant_dots"]),
            "sha8": c["token"], "parent": "h33-2b2 (GEMSDOE32, CLAIM 0.2778)",
            "axis": c["axis"], "value": c["value"],
            "pct_changed": str(d["pct_changed_of_parent"]),
            "sha256_nan": c["artifacts"]["nan"]["sha256"],
            "sha256_zeros": c["artifacts"]["zeros"]["sha256"],
            "status": "BUILT", "evidence_class": "MODEL (predicted change is not a score)",
            "predicted_change": c.get("predicted_change", ""),
            "receipt_score": "", "receipt_date": "", "duplicates_collapsed": "0",
            "source": "evidence/axis_variants.json"})
    return rows


def main() -> int:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "build_axis_variants", ROOT / "scripts" / "build_axis_variants.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # main() is __main__-guarded, so this only defines
    preds = dict(getattr(mod, "PREDICTIONS", {}))
    rows = history_rows()
    for r in variant_rows():
        if not r["predicted_change"]:
            r["predicted_change"] = preds.get(r["axis"], "")
        rows.append(r)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    dupes = sum(int(r["duplicates_collapsed"]) for r in rows)
    print(json.dumps({"wrote": str(OUT.relative_to(ROOT)), "rows": len(rows),
                      "history_rows": len(rows) - len(variant_rows()),
                      "variant_rows": len(variant_rows()),
                      "duplicates_collapsed": dupes,
                      "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
