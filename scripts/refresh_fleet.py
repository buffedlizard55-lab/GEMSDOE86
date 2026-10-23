#!/usr/bin/env python3
"""Refresh a read-only, commit-pinned inventory of the user-named GitHub projects.

Uses gh, never a competition login, never downloads historical predictions into
release directories, and never interprets a README claim as an organizer score.
Only GitHub API metadata is fetched; this is NOT a current complete uniqueness
registry or a verification of hosted Pages content or model performance.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_release import sha256, strict_json, write_json  # noqa: E402

REPOSITORY = re.compile(r"buffedlizard55-lab/[A-Za-z0-9_-]+\Z")


def gh_api(endpoint: str) -> dict:
    result = subprocess.run(["gh", "api", endpoint, "-H", "Accept: application/vnd.github+json"],
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        # Do not persist arbitrary command output, headers, environment variables
        # or credentials in a public feed. Record a typed failure, not success.
        status = "NOT_ACCESSIBLE_OR_REQUEST_FAILED"
        if "HTTP 404" in result.stderr:
            status = "NOT_FOUND_OR_NOT_ACCESSIBLE"
        elif "HTTP 403" in result.stderr or "rate limit" in result.stderr.lower():
            status = "FORBIDDEN_OR_RATE_LIMITED"
        elif "HTTP 401" in result.stderr or "gh auth login" in result.stderr:
            status = "GITHUB_CONNECTION_NEEDS_ATTENTION"
        raise RuntimeError(status)
    return json.loads(result.stdout)


def snapshot(target: dict, claims: list[dict], api=gh_api) -> dict:
    repo = target["repository"]
    if not REPOSITORY.fullmatch(repo):
        raise ValueError("Only the explicit owner repository targets may be queried")
    row = dict(repository=repo, site_url=target["site_url"],
               evidence_class="REPOSITORY-METADATA", owner_reported_results=claims,
               organizer_score_verified=False, raster_bytes_verified=False)
    try:
        # main is the public source branch, not this session's working branch.
        # This operation reads a remote ref; it never switches/creates a branch.
        commit = api(f"repos/{repo}/commits/main")
        commit_sha = commit["sha"]
        tree_sha = commit["commit"]["tree"]["sha"]
        tree = api(f"repos/{repo}/git/trees/{tree_sha}?recursive=1")
        files = [item for item in tree["tree"] if item["type"] == "blob"]
        tifs = [dict(path=item["path"], git_blob_sha1=item["sha"], git_blob_bytes=item.get("size"))
                for item in files if item["path"].lower().endswith((".tif", ".tiff"))]
        row.update(status="INCOMPLETE_TRUNCATED_TREE" if tree.get("truncated", True) else "SNAPSHOT_OK",
                   commit_sha=commit_sha, tree_sha=tree_sha,
                   commit_url=f"https://github.com/{repo}/tree/{commit_sha}",
                   tree_api_url=f"https://api.github.com/repos/{repo}/git/trees/{tree_sha}?recursive=1",
                   source_commit_date=commit["commit"]["committer"]["date"],
                   current_tree_tif_count=len(tifs), tif_git_objects=tifs,
                   published_download_tif_count=sum(item["path"].startswith("docs/downloads/") for item in tifs),
                   tree_truncated=tree.get("truncated", True))
    except (OSError, subprocess.TimeoutExpired, RuntimeError, ValueError, KeyError, TypeError) as exc:
        row.update(status=str(exc) if isinstance(exc, RuntimeError) else "INVALID_RESPONSE_OR_TIMEOUT",
                   current_tree_tif_count=None, published_download_tif_count=None, tif_git_objects=[],
                   error_class=type(exc).__name__)
    return row


def refresh(root: Path = ROOT, *, workers: int = 4, api=gh_api) -> dict:
    targets_path = root / "registry/site_targets.json"
    ledger_path = root / "registry/prior_scores.csv"
    targets = strict_json(targets_path)["sites"]
    if not targets or len({t["repository"] for t in targets}) != len(targets):
        raise ValueError("Target inventory must be nonempty and contain unique repository names")
    with ledger_path.open(newline="", encoding="utf-8") as stream:
        ledger = list(csv.DictReader(stream))
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    jobs = []
    for target in targets:
        site = target["repository"].split("/")[-1]
        claims = [dict(submission=r["submission"], value=r["score"] or None,
                       evidence_class=r["evidence_class"], source_url=r["source_url"])
                  for r in ledger if r["site"] == site]
        jobs.append((target, claims))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(lambda pair: snapshot(*pair, api=api), jobs))
    return dict(schema="gems86.fleet-feed.v1", evidence_class="REPOSITORY-METADATA",
                refresh_started_utc=started,
                refreshed_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                targets_sha256=sha256(targets_path), owner_ledger_sha256=sha256(ledger_path),
                projects_requested=len(targets), projects_snapshotted=sum(r["status"] == "SNAPSHOT_OK" for r in rows),
                refresh_complete=all(r["status"] == "SNAPSHOT_OK" for r in rows),
                organizer_receipts_obtained=0, new_rasters_generated=0, submission_slots_used=0,
                scope="Current main-branch Git trees of the explicit owner-named repositories, not all historical rasters. Git blob SHA-1 and byte length are NOT raster SHA-256, format validation, uniqueness, organizer authentication, or a live score. Failed requests remain explicit.",
                projects=rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, choices=range(1, 9), default=4)
    parser.add_argument("--allow-partial", action="store_true",
                        help="publish an explicit fresh partial snapshot without treating a project failure as a workflow failure")
    args = parser.parse_args(argv)
    result = refresh(workers=args.workers)
    write_json(ROOT / "docs/evidence/fleet-feed.json", result)
    print(json.dumps({k: result[k] for k in ("projects_requested", "projects_snapshotted", "refresh_complete", "organizer_receipts_obtained", "submission_slots_used")}, indent=2))
    if any(r["status"] == "GITHUB_CONNECTION_NEEDS_ATTENTION" for r in result["projects"]):
        print("GitHub connection needs attention; reconnect GitHub in Arena.", file=sys.stderr)
    return 0 if result["refresh_complete"] or args.allow_partial else 1


if __name__ == "__main__":
    raise SystemExit(main())
