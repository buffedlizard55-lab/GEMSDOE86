#!/usr/bin/env python3
"""Verify the nine cited historical TIFFs, without publishing or uploading them.

--write fetches Git objects from the already-refreshed GitHub tree and checks
both Git blob identity and the SHA-256 in the prior pixel-forensic record. The
normal offline check validates the persisted evidence bindings, not live URLs or
organizer scores. No competition portal, model, or new raster is involved.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.restore_protocol_data import write_blob  # noqa: E402

SITES = ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36")
OUTPUT = ROOT / "docs/evidence/focus9-download-proof-20261027.json"


def _inputs(root=ROOT):
    with (root / "registry/prior_scores.csv").open(newline="", encoding="utf-8") as f:
        ledger = list(csv.DictReader(f))
    forensic = json.loads((root / "docs/evidence/focus9-forensics-20261026-rev2.json").read_text())
    feed = json.loads((root / "docs/evidence/fleet-feed.json").read_text())
    return ledger, forensic["rasters"], feed["projects"]


def selected(ledger, site):
    claims = [row for row in ledger if row["site"] == site and row["score"].strip()]
    if not claims:
        raise ValueError(f"Missing score claim for {site}")
    return max(claims, key=lambda row: float(row["score"]))


def build_proof(root=ROOT, *, fetch=write_blob):
    ledger, rasters, projects = _inputs(root)
    rows = []
    for site in SITES:
        claim = selected(ledger, site)
        project = next(p for p in projects if p["repository"] == "buffedlizard55-lab/" + site)
        if project.get("status") != "SNAPSHOT_OK":
            raise ValueError(f"{site} current tree not accessible")
        matches = [r for r in project["tif_git_objects"]
                   if Path(r["path"]).stem.lower().endswith(claim["submission"].lower())]
        if len(matches) != 1:
            raise ValueError(f"{site} historical TIFF match is missing or ambiguous")
        item = matches[0]
        if not item["path"].startswith("docs/downloads/") or ".." in Path(item["path"]).parts:
            raise ValueError(f"Unsafe historical path: {site}")
        forensic = [r for r in rasters if r["file"].lower() == (site + "__" + Path(item["path"]).name).lower()]
        if len(forensic) != 1:
            raise ValueError(f"{site} has no unique byte-level forensic row")
        stream = io.BytesIO()
        fetch(project["repository"], item["git_blob_sha1"], stream)
        raw = stream.getvalue()
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        digest = hashlib.sha256(raw).hexdigest()
        if (git_blob != item["git_blob_sha1"] or len(raw) != item["git_blob_bytes"]
                or digest != forensic[0]["sha256"]):
            raise ValueError(f"{site} blob does not match the historical forensic TIFF")
        rows.append(dict(site=site, repository=project["repository"], commit_sha=project["commit_sha"],
                         path=item["path"], git_blob_sha1=git_blob, bytes=len(raw), sha256=digest,
                         submission=claim["submission"],
                         overlap_3px_vs_h33=forensic[0]["overlap_3px_vs_H33"],
                         evidence_class="HISTORICAL_RASTER_IDENTITY_NOT_ORGANIZER_SCORE",
                         download_authorized_for_submission=False))
    return dict(schema="gems86.focus9-download-proof.v1", observed_utc=datetime.now(timezone.utc).isoformat(),
                scope=("Nine commit-pinned historical GitHub TIFFs were downloaded in memory and matched "
                       "to existing SHA-256 forensic records. This verifies byte identity only, not "
                       "organizer scores, complete uniqueness, format acceptance, or permission to upload."),
                rows=rows)


def validate_proof(proof, root=ROOT):
    ledger, rasters, projects = _inputs(root)
    rows = proof.get("rows")
    if proof.get("schema") != "gems86.focus9-download-proof.v1" or not isinstance(rows, list):
        raise ValueError("Invalid Focus-9 download proof")
    if len(rows) != len(SITES) or {r.get("site") for r in rows} != set(SITES):
        raise ValueError("Focus-9 proof must cover each site exactly once")
    for row in rows:
        site = row["site"]
        path = Path(row["path"])
        forensic = [r for r in rasters if r["file"].lower() == (site + "__" + path.name).lower()]
        snapshot = [p for p in projects if p["repository"] == row["repository"]]
        objects = ([o for o in snapshot[0]["tif_git_objects"] if o["path"] == row["path"]]
                   if len(snapshot) == 1 else [])
        if (row["repository"] != "buffedlizard55-lab/" + site
                or len(snapshot) != 1 or snapshot[0].get("status") != "SNAPSHOT_OK"
                or row["commit_sha"] != snapshot[0].get("commit_sha")
                or len(objects) != 1 or row["git_blob_sha1"] != objects[0].get("git_blob_sha1")
                or row["bytes"] != objects[0].get("git_blob_bytes")
                or path.is_absolute() or ".." in path.parts
                or not str(path).startswith("docs/downloads/") or path.suffix.lower() != ".tif"
                or not re.fullmatch("[0-9a-f]{40}", row["commit_sha"])
                or not re.fullmatch("[0-9a-f]{40}", row["git_blob_sha1"])
                or not re.fullmatch("[0-9a-f]{64}", row["sha256"])
                or type(row["bytes"]) is not int or row["bytes"] <= 0
                or row["submission"] != selected(ledger, site)["submission"]
                or not path.stem.lower().endswith(row["submission"].lower())
                or len(forensic) != 1 or row["sha256"] != forensic[0]["sha256"]
                or row["overlap_3px_vs_h33"] != forensic[0]["overlap_3px_vs_H33"]
                or row.get("download_authorized_for_submission") is not False):
            raise ValueError(f"Invalid or unbound Focus-9 proof row: {site}")
    return proof


def raw_url(row):
    return f"https://github.com/{row['repository']}/raw/{row['commit_sha']}/{quote(row['path'])}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="fetch and verify bytes against the current feed")
    args = parser.parse_args(argv)
    if args.write:
        proof = build_proof()
        validate_proof(proof)
        OUTPUT.write_text(json.dumps(proof, indent=2, allow_nan=False) + "\n")
    else:
        proof = validate_proof(json.loads(OUTPUT.read_text()))
    print(f"Focus-9 historical raster identity: {len(proof['rows'])}/9; DO NOT SUBMIT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
