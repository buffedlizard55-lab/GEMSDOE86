#!/usr/bin/env python3
"""Materialise the published cross-fleet raster inventory for the uniqueness gate.

Inventory: ``registry/registry_index_published_20261021.json`` (812 unique git
blobs, 68 repositories, built 2026-10-21T02:30Z by the GEMSDOE82 portfolio
audit; sha256 of the index file is recorded in the audit output).

Fetch method: one *blobless* git clone per repository (commit/tree data only,
~1 s each at ~40 kB) followed by ``git cat-file blob <sha>`` for exactly the
indexed blobs.  No REST API quota is consumed, and every fetched object is
identified by its git object id, so a silent substitution is impossible.

Writes ``.cache/registry/tifs/<sha256>.tif`` and a receipt.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "registry" / "registry_index_published_20261021.json"
REPOS = ROOT / ".cache" / "registry" / "repos"
TIFS = ROOT / ".cache" / "registry" / "tifs"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def clone(repo: str) -> Path:
    dst = REPOS / repo
    if (dst / ".git").is_dir():
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", "--quiet",
                    f"https://github.com/buffedlizard55-lab/{repo}.git", str(dst)],
                   check=True, timeout=900)
    return dst


def main() -> None:
    idx = json.loads(INDEX.read_text())
    rows = idx["rasters"]
    TIFS.mkdir(parents=True, exist_ok=True)
    REPOS.mkdir(parents=True, exist_ok=True)
    by_repo: dict[str, list[dict]] = {}
    for r in rows:
        by_repo.setdefault(r["repo"], []).append(r)
    done = failed = 0
    receipt = {"index_sha256": sha256_bytes(INDEX.read_bytes()), "n_indexed": len(rows),
               "fetch": [], "errors": []}
    for i, (repo, entries) in enumerate(sorted(by_repo.items()), 1):
        try:
            path = clone(repo)
        except subprocess.SubprocessError as exc:
            receipt["errors"].append({"repo": repo, "error": str(exc)[:200]})
            continue
        for e in entries:
            out = TIFS / f"{e['blob']}.tif"
            if out.is_file() and out.stat().st_size == e.get("size", out.stat().st_size):
                done += 1
                continue
            try:
                blob = subprocess.run(["git", "-C", str(path), "cat-file", "blob", e["blob"]],
                                      check=True, capture_output=True, timeout=300).stdout
            except subprocess.SubprocessError as exc:
                receipt["errors"].append({"repo": repo, "blob": e["blob"],
                                          "error": str(exc)[:200]})
                failed += 1
                continue
            out.write_bytes(blob)
            receipt["fetch"].append({"repo": repo, "path": e["path"], "blob": e["blob"],
                                     "sha256": sha256_bytes(blob), "bytes": len(blob)})
            done += 1
        print(f"[{i}/{len(by_repo)}] {repo}: {len(entries)} entries, total fetched {done}, "
              f"failed {failed}", flush=True)
    receipt["n_fetched"] = len(receipt["fetch"])
    receipt["n_errors"] = len(receipt["errors"])
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence" / "registry_fetch_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"fetched": receipt["n_fetched"], "errors": receipt["n_errors"]}, indent=2))


if __name__ == "__main__":
    main()
