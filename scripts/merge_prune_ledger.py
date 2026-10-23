#!/usr/bin/env python3
"""Append (or refresh) this session's PRUNE-ladder rows in ``ledger/submissions.csv``.

The ledger is shared: an earlier session on the same day created it and seeded the
historical CLAIM rows, so this script never rewrites rows it does not own. It
removes only rows whose ``id`` belongs to this ladder (``PRUNE-le*``/``CONTROL-massctl*``
under the R0 parent) and re-appends them from the receipts in ``releases/``, in the
existing schema. Idempotent; aborts on a schema change rather than guessing.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "submissions.csv"
PARENT = "h33-h33-2-b2-20261004-e5eb6e7e"
OWNED = ("-PRUNE-le", "-CONTROL-massctl")


def main() -> int:
    with open(LEDGER, newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    required = {"site", "name", "n_dots", "sha8", "parent", "id", "axis", "value",
                "pct_changed", "sha256", "status", "predicted_change", "evidence_class"}
    missing = required - set(fieldnames)
    if missing:
        raise SystemExit(f"ledger schema changed; refusing to guess missing columns: {sorted(missing)}")

    kept = [r for r in rows if not any(m in r.get("id", "") for m in OWNED)]
    dropped = len(rows) - len(kept)

    new = []
    for receipt_path in sorted((ROOT / "releases").glob("*-zeros.json")):
        r = json.loads(receipt_path.read_text())
        if PARENT not in r["id"]:
            continue
        sha = r["zeros"]["sha256"]
        new.append({
            "site": "GEMSDOE86", "name": r["id"], "score": "", "encoding": "zeros",
            "n_dots": r["n_dots"], "sha8": sha[:8], "parent": PARENT, "receipt": "N",
            "id": r["id"], "axis": r["axis"], "value": r["value"],
            "pct_changed": r["pct_changed"], "sha256": sha,
            "status": r["role"].upper() if r["role"] != "candidate" else "BUILT",
            "predicted_change": f"{r['predicted_live_change']:+.3f} MODEL",
            "receipt_score": "", "date": "", "evidence_class": "MODEL",
            "source_url": f"releases/{r['zeros']['file']}",
        })

    shas = {r["sha256"] for r in kept if r.get("sha256")}
    clash = [r["id"] for r in new if r["sha256"] in shas]
    if clash:
        raise SystemExit(f"sha256 already in the ledger for other rows: {clash}")

    with open(LEDGER, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for row in kept:
            w.writerow(row)
        for row in new:
            w.writerow(row)
    print(f"{LEDGER.relative_to(ROOT)}: kept {len(kept)}, replaced {dropped} own rows, appended {len(new)}")
    for row in new:
        print(f"  {row['id']}  n_dots={row['n_dots']}  {row['pct_changed']}%  {row['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
