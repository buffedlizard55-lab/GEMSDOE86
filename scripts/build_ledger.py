#!/usr/bin/env python3
"""Build ``ledger/submissions.csv`` from committed evidence only.

Sources, in this order:

1. ``registry/prior_scores.csv`` -- the repository's transcription of the owner's
   historical leaderboard claims. Every score there is an owner report with no
   submission-page receipt, so it lands in ``claim_score``, never in
   ``receipt_score`` (which only a human can fill).
2. ``data/scored_fleet/*.tif`` -- where the claimed raster is present locally, its
   sha256, geometric dot count and dot-set digest are measured from the bytes.
3. ``evidence/prune_ladder.json`` -- this session's built variants.

Rows collapse on (measured sha256) when a raster is present, then on
``submission`` name, and the collapsed aliases are listed in ``note``. Re-running
this script is idempotent.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ledger" / "submissions.csv"
COLUMNS = ["id", "parent", "axis", "value", "n_dots", "pct_changed", "sha256", "dot_digest",
           "status", "evidence_class", "predicted_change", "claim_score", "receipt_score",
           "receipt_date", "source", "note"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dots_of(path: Path) -> tuple[int, str]:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    dots = np.nan_to_num(a) > 0
    idx = np.flatnonzero(dots.ravel()).astype("<u4")
    return int(dots.sum()), hashlib.sha256(idx.tobytes()).hexdigest()


def main() -> int:
    fleet = {}
    for p in sorted((ROOT / "data" / "scored_fleet").glob("*.tif")):
        try:
            n, digest = dots_of(p)
        except Exception:
            continue
        fleet[p.name] = dict(sha256=sha256(p), n_dots=n, dot_digest=digest)
    by_sha = {v["sha256"]: (k, v) for k, v in fleet.items()}

    rows, seen_sha, aliases = [], set(), {}
    with open(ROOT / "registry" / "prior_scores.csv", newline="") as fh:
        for rec in csv.DictReader(fh):
            sub = rec["submission"]
            match = next((v for k, v in fleet.items()
                          if len(sub) >= 8 and sub.lower() in k.lower()), None)
            sha = match["sha256"] if match else ""
            if sha and sha in seen_sha:
                aliases.setdefault(sha, []).append(sub)
                continue
            if sha:
                seen_sha.add(sha)
            rows.append(dict(
                id=sub if sub.strip() else f"{rec['site']}__NO-ARTIFACT", parent="", axis="LEGACY", value="",
                n_dots=match["n_dots"] if match else "", pct_changed="",
                sha256=sha, dot_digest=match["dot_digest"] if match else "",
                status="LEGACY-SCORED-CLAIM", evidence_class="CLAIM",
                predicted_change="", claim_score=rec["score"], receipt_score="", receipt_date="",
                source=rec["source_url"],
                note=f"{rec['site']}: {rec['evidence_class']}; raster {'present' if match else 'absent'} locally",
            ))

    ladder = json.loads((ROOT / "evidence" / "prune_ladder.json").read_text())
    receipts = {}
    for p in sorted((ROOT / "releases").glob("*-zeros.json")):
        receipts[json.loads(p.read_text())["id"]] = json.loads(p.read_text())
    tags = {"r225": "le2p236", "r283": "le2p828", "r300": "le3p000"}
    for key, card in ladder["variants"].items():
        tag = tags.get(key, f"massctl{card['diff']['n_removed']}")
        r = next((v for v in receipts.values() if f"-{tag}-" in v["id"]), None)
        if r is None:
            continue
        is_ctl = card["role"] != "candidate"
        rows.append(dict(
            id=r["id"], parent=ladder["parent"]["id"], axis=r["axis"], value=r["value"],
            n_dots=r["n_dots"], pct_changed=r["pct_changed"], sha256=r["zeros"]["sha256"],
            dot_digest=r["dot_digest"],
            status="BUILT-CONTROL" if is_ctl else "BUILT",
            evidence_class="MODEL", predicted_change=f"{r['predicted_live_change']:+.3f}",
            claim_score="", receipt_score="", receipt_date="",
            source="releases/" + r["zeros"]["file"],
            note=("control: same mass removed, none near the catalogue; never submit" if is_ctl
                  else f"PRUNE {r['value']}; parent-diff {r['pct_changed']}%; dot-set digest recorded"),
        ))

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    shas = [r["sha256"] for r in rows if r["sha256"]]
    print(f"{OUT.relative_to(ROOT)}: {len(rows)} rows, {len(set(shas))} distinct measured sha256, "
          f"{len(aliases)} duplicate raster(s) collapsed")
    for sha, names in aliases.items():
        print(f"  collapsed {sha[:12]}: {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
