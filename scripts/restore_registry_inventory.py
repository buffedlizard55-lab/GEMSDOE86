#!/usr/bin/env python3
"""Restore the hash-pinned cross-repository registry for uniqueness audits.

The registry is comparison-only: its rasters are never prediction inputs.  The
inventory records immutable Git blob IDs, byte lengths, and SHA-256 digests.
This command downloads each missing blob through ``gh api`` into the ignored
``data/registry_ext/`` cache, verifies the byte count and digest before the
file becomes visible, and writes a receipt.  An incomplete receipt is never a
uniqueness pass.

The public owner inventory is not an organizer registry and its bytes do not
authenticate the competition's private labels.  The distinction is deliberate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "research/upstream/registry_inventory.json"
DEFAULT_OUT = ROOT / "data/registry_ext"
DEFAULT_RECEIPT = ROOT / "docs/evidence/registry-inventory-restore.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_one(record: dict, out_dir: Path, owner: str) -> dict:
    expected = record["sha256"]
    repo = f"{owner}/{record['repo_first']}"
    dest = out_dir / f"{expected}.tif"
    if dest.is_file():
        got = sha256(dest)
        if got == expected and dest.stat().st_size == record["bytes"]:
            return {"sha256": expected, "bytes": record["bytes"], "status": "cached_ok", "repo": repo}
        dest.unlink()
    partial = dest.with_suffix(".partial")
    partial.unlink(missing_ok=True)
    endpoint = f"repos/{repo}/git/blobs/{record['blob']}"
    try:
        with partial.open("wb") as stream:
            subprocess.run(
                ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw"],
                stdout=stream,
                stderr=subprocess.PIPE,
                check=True,
                timeout=900,
            )
        got = sha256(partial)
        size = partial.stat().st_size
        if got != expected or size != record["bytes"]:
            raise RuntimeError(
                f"integrity mismatch {record['repo_first']}:{record['blob']}: "
                f"sha={got} bytes={size}; expected {expected}/{record['bytes']}"
            )
        partial.replace(dest)
        return {"sha256": expected, "bytes": size, "status": "downloaded"}
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be positive")

    inventory = json.loads(INVENTORY.read_text())
    owner = inventory["owner"]
    records = inventory["rasters"]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    errors: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_one, r, args.out_dir, owner): r for r in records}
        for number, future in enumerate(as_completed(futures), 1):
            record = futures[future]
            try:
                result = future.result()
                rows.append({**result, "repo": record["repo_first"], "blob": record["blob"],
                             "sources": record["sources"]})
            except Exception as exc:  # keep all failures visible in the receipt
                errors.append({"repo": record["repo_first"], "blob": record["blob"],
                               "sources": record["sources"], "error": repr(exc)})
            if number % 25 == 0 or number == len(records):
                print(f"registry restore {number}/{len(records)}", flush=True)

    rows.sort(key=lambda row: row["sha256"])
    errors.sort(key=lambda row: (row["repo"], row["blob"]))
    complete = not errors and len(rows) == len(records)
    receipt = {
        "schema": "gems86.registry-restore.v1",
        "inventory": str(INVENTORY.relative_to(ROOT)),
        "inventory_entries": len(records),
        "verified_entries": len(rows),
        "errors": errors,
        "complete_accessible_scan": complete,
        "organizer_authenticated": False,
        "comparison_only": True,
        "bytes_verified": sum(row["bytes"] for row in rows),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: receipt[k] for k in (
        "inventory_entries", "verified_entries", "complete_accessible_scan", "bytes_verified")}, indent=2))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
