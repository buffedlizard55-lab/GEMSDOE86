#!/usr/bin/env python3
"""Build ``ledger/submissions.csv`` from the transcribed history plus this session's candidates.

Two sources, one ledger:

* ``registry/prior_scores.csv`` -- the owner's historical claims (evidence_class carried over
  verbatim; a claim never becomes a score because it is copied into this file).
* ``evidence/snap_variants.json`` -- the rasters built in this session, status ``BUILT``.

Human-owned columns are ``receipt_score`` and ``receipt_date`` (plus any status the human
changes by hand).  Re-running this script **never overwrites them**: existing values are merged
in by ``id``.  That is deliberate -- a receipt is copied from a submission-page receipt by the
account holder, never invented here.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "submissions.csv"
HISTORY = ROOT / "registry" / "prior_scores.csv"
VARIANTS = ROOT / "evidence" / "snap_variants.json"

FIELDS = ["id", "site", "parent", "axis", "value", "n_dots", "pct_changed", "sha256", "sha8",
          "status", "predicted_change", "evidence_class", "receipt_score", "receipt_date",
          "encoding", "note"]


def _existing() -> dict[str, dict]:
    if not LEDGER.is_file():
        return {}
    with LEDGER.open(newline="") as fh:
        return {r["id"]: r for r in csv.DictReader(fh)}


def history_rows() -> list[dict]:
    rows = []
    with HISTORY.open(newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "id": r["submission"], "site": r["site"], "parent": "",
                "axis": "", "value": "", "n_dots": "", "pct_changed": "", "sha256": "",
                "sha8": r["submission"][-12:] if len(r["submission"]) > 12 else "",
                "status": "SCORED-CLAIM" if r["score"] else "UNSCORED",
                "predicted_change": "",
                "evidence_class": r["evidence_class"] or "OWNER-REPORTED",
                "receipt_score": "", "receipt_date": "",
                "encoding": "zeros" if r["submission"].endswith("zeros") else "nan",
                "note": r["source_url"],
            })
    return rows


def variant_rows() -> list[dict]:
    if not VARIANTS.is_file():
        return []
    report = json.loads(VARIANTS.read_text())
    rows = []
    for key, v in report["variants"].items():
        diff = v["parent_diff"]
        card = v["mechanism_card"]
        primary = v["gates"][v["files"]["nan_outside"]]
        rows.append({
            "id": v["id"], "site": "GEMSDOE86", "parent": v["parent"],
            "axis": v["axis"], "value": v["value"], "n_dots": diff["n_dots"],
            "pct_changed": diff["pct_changed"], "sha256": primary["sha256"],
            "sha8": primary["sha256"][:8], "status": "BUILT",
            "predicted_change": card["predicted"],
            "evidence_class": "MODEL (projection; no live receipt)",
            "receipt_score": "", "receipt_date": "",
            "encoding": "nan (primary) / zeros (fallback)",
            "note": f"releases/{v['files']['nan_outside']}",
        })
    return rows


def main() -> int:
    prior = _existing()
    rows = variant_rows() + history_rows()
    for r in rows:
        old = prior.get(r["id"], {})
        for col in ("receipt_score", "receipt_date", "status"):
            if old.get(col):
                r[col] = old[col]
    LEDGER.parent.mkdir(exist_ok=True)
    with LEDGER.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({"rows": len(rows), "built": sum(r["status"] == "BUILT" for r in rows),
                      "ledger": str(LEDGER.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
