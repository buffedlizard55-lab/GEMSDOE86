#!/usr/bin/env python3
"""Re-measure the nine-site best owner files from their public repository trees.

Scope (read this before using any number):

* Fetches only the public owner repositories ``buffedlizard55-lab/GEMSDOE{24,25,27,28,30,31,32,33,36}``
  and the pinned 17GEMSDOE witness from ``codeload.github.com`` (an allowlisted host). Tarballs go to
  ``.cache/nine_site/`` (git-ignored). DrivenData is never contacted (AGENTS.md rule 9).
* Byte identity is checked against the SHA-256 values recorded in
  ``docs/evidence/nine-site-audit-20261027.json``. A match proves the bytes equal those already
  recorded; it does not prove they are the exact files uploaded to the portal.
* Overlap uses the shared ``gems57.uniqueness.dot_overlap`` (3 px, forward direction). Nothing is
  redefined here.
* The witness check is a DIAGNOSTIC. The literal gate (every positive cell counts as a dot) is
  unchanged and still fails. The top-K reading is reported only to show which definition drives the
  stop; it is never a clearance, never a candidate and never a score.

Output: ``docs/evidence/nine-site-lineage-20261029.json`` (``--write``) or stdout (default).
Every owner score carried in the output is OWNER-REPORTED. Nothing here is an organizer receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import grid  # noqa: E402
from gems57.metric import RADIUS_PX  # noqa: E402
from gems57.uniqueness import dot_overlap  # noqa: E402

AUDIT = ROOT / "docs/evidence/nine-site-audit-20261027.json"
OUT = ROOT / "docs/evidence/nine-site-lineage-20261029.json"
CACHE = ROOT / ".cache/nine_site"
PIN = ROOT / "research/registry_witness_pin.json"
SITES = ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36")
OWNER = "buffedlizard55-lab"
TOPK_DOTS = 37654  # the nine-site budget used by the repository's count-fixed releases


def codeload_url(repo: str) -> str:
    return f"https://codeload.github.com/{OWNER}/{repo}/tar.gz/HEAD"


def fetch_tree(repo: str, members_re: str, offline: bool) -> dict[str, bytes]:
    """Return {member path without top-level dir: bytes} for files matching ``members_re``.

    The archive is cached on disk; only the selected members are kept in memory.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    tar_path = CACHE / f"{repo}.tar.gz"
    if not tar_path.exists():
        if offline:
            raise FileNotFoundError(f"offline and not cached: {tar_path}")
        with urllib.request.urlopen(codeload_url(repo), timeout=600) as resp:
            tmp = tar_path.with_suffix(".partial")
            tmp.write_bytes(resp.read())
            tmp.replace(tar_path)
    pat = re.compile(members_re)
    out: dict[str, bytes] = {}
    with tarfile.open(tar_path, "r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            rel = m.name.split("/", 1)[1] if "/" in m.name else m.name
            if pat.search(rel):
                out[rel] = tf.extractfile(m).read()
    return out


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_tif(b: bytes) -> np.ndarray:
    with rasterio.MemoryFile(b) as mf, mf.open() as src:
        return src.read(1)


def dot_mask(a: np.ndarray) -> np.ndarray:
    """Dots under the inherited literal rule: finite and strictly positive."""
    return np.isfinite(a) & (a > 0)


def lineage_stats(parent: np.ndarray, child: np.ndarray, catalogue_distance_px: np.ndarray) -> dict:
    """Subset test and removed-dot geometry, all in pixel units."""
    removed = parent & ~child
    added = child & ~parent
    dists = np.round(catalogue_distance_px[removed], 4)
    values, counts = np.unique(dists, return_counts=True)
    return {
        "parent_dots": int(parent.sum()),
        "child_dots": int(child.sum()),
        "child_subset_of_parent": bool(not added.any()),
        "removed_dots": int(removed.sum()),
        "added_dots": int(added.sum()),
        "removed_catalogue_distance_px": {f"{float(v):.4f}": int(c) for v, c in zip(values, counts)},
    }


def topk_mask(values: np.ndarray, footprint: np.ndarray, k: int) -> np.ndarray:
    """Diagnostic top-K cells of a continuous surface inside the footprint (ties kept)."""
    inside = values[footprint]
    thr = np.partition(inside, -k)[-k]
    out = np.zeros(values.shape, bool)
    out[(values >= thr) & footprint] = True
    return out


def load_witness(offline: bool) -> bytes:
    pin = json.loads(PIN.read_text())
    tar_path_name = "17GEMSDOE"
    members = fetch_tree(tar_path_name, re.escape(pin["source_path"].split("/")[-1]) + "$", offline)
    if len(members) != 1:
        raise ValueError(f"witness member not found uniquely: {list(members)}")
    data = next(iter(members.values()))
    if sha256(data) != pin["sha256"]:
        raise ValueError("witness SHA-256 does not match research/registry_witness_pin.json")
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", action="store_true", help="use only .cache/nine_site (no network)")
    ap.add_argument("--write", action="store_true", help=f"write {OUT.relative_to(ROOT)}")
    args = ap.parse_args(argv)

    audit = json.loads(AUDIT.read_text())
    grid_ref = grid.load_grid(ROOT / "data/bridge")
    cat_dist = ndimage.distance_transform_edt(~grid_ref.catalogue)  # pixels

    rows = []
    arrays: dict[str, np.ndarray] = {}
    variant_checks = []
    for f in audit["files"]:
        site = f["site"]
        rel_audit = f["file"]  # e.g. GEMSDOE32-main/docs/downloads/x.tif
        name = rel_audit.split("/")[-1]
        repo_dir = rel_audit.split("/")[0].replace("-main", "")
        tree = fetch_tree(repo_dir, r"^docs/downloads/.*\.tif$", args.offline)
        rel = "docs/downloads/" + name
        if rel not in tree:
            raise FileNotFoundError(f"{site}: {rel} not in {repo_dir} tree")
        b = tree[rel]
        if sha256(b) != f["sha256"]:
            raise ValueError(f"{site}: SHA-256 mismatch against nine-site-audit")
        a = read_tif(b)
        if a.shape != grid_ref.footprint.shape:
            raise ValueError(f"{site}: grid shape mismatch")
        dots = dot_mask(a)
        arrays[site] = dots.astype(np.float32)
        rows.append({
            "site": site,
            "owner_score": f["owner_score"],
            "owner_score_class": "OWNER-REPORTED (no organizer receipt)",
            "owner_name": f["owner_name"],
            "file": rel_audit,
            "source_url": f"https://github.com/{OWNER}/{repo_dir}/blob/HEAD/{rel}",
            "sha256": f["sha256"],
            "sha256_matches_audit": True,
            "dots": int(dots.sum()),
            "dots_on_catalogue": int((dots & grid_ref.catalogue).sum()),
            "dots_outside_footprint": int((dots & ~grid_ref.footprint).sum()),
            "nan_total": int(np.isnan(a).sum()),
            "inf_total": int(np.isinf(a).sum()),
            "values_distinct": [float(v) for v in np.unique(a[np.isfinite(a)])][:4],
            "grid_matches_reference": True,
        })
        # Owner-named suffix vs audited representation: are they the same dot field?
        stem = re.sub(r"-(nan|zeros|zero|allfinite)$", "", f["owner_name"]).removesuffix(".tif")
        siblings = [p for p in tree if p.startswith("docs/downloads/") and stem in p.split("/")[-1]
                    and p != rel and p.endswith(".tif")]
        for sp in sorted(siblings):
            sb = read_tif(tree[sp])
            sd = dot_mask(sb)
            variant_checks.append({
                "site": site,
                "audited_file": name,
                "sibling_file": sp.split("/")[-1],
                "sibling_sha256": sha256(tree[sp]),
                "dot_field_identical": bool(np.array_equal(sd, dots)),
                "sibling_nan_total": int(np.isnan(sb).sum()),
                "sibling_dots": int(sd.sum()),
            })

    n = len(rows)
    M = np.zeros((n, n))
    for i, si in enumerate(SITES):
        for j, sj in enumerate(SITES):
            if i != j:
                M[i, j] = dot_overlap(arrays[si], arrays[sj], RADIUS_PX)
    off = M[~np.eye(n, dtype=bool)]

    # H33 lineage against the GEMSDOE31 family parent (both verified above)
    h33_name = "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    g31_name = "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif"
    h33_rec = next(r for r in rows if r["site"] == "GEMSDOE32")
    g31_rec = next(r for r in rows if r["site"] == "GEMSDOE31")
    assert h33_rec["file"].endswith(h33_name) and g31_rec["file"].endswith(g31_name)
    lineage = lineage_stats(arrays["GEMSDOE31"].astype(bool), arrays["GEMSDOE32"].astype(bool), cat_dist)

    # Witness: literal gate (unchanged) + top-K DIAGNOSTIC only
    witness = load_witness(args.offline)
    with rasterio.MemoryFile(witness) as mf, mf.open() as src:
        wa = src.read(1).astype(np.float64)
        w_ok = (src.shape, src.crs, src.transform) == (grid_ref.footprint.shape, grid_ref.crs, grid_ref.transform)
    inside = wa[grid_ref.footprint]
    literal_positive_in_footprint = int(((wa > 0) & np.isfinite(wa) & grid_ref.footprint).sum())
    topk = topk_mask(wa, grid_ref.footprint, TOPK_DOTS)
    diag = {}
    for site in ("GEMSDOE32", "GEMSDOE31", "GEMSDOE36"):
        d = arrays[site].astype(bool)
        diag[site] = {
            "forward_my_dots_within_3px_of_witness_topK": round(dot_overlap(d.astype(np.float32),
                                                                            topk.astype(np.float32), RADIUS_PX), 4),
            "reverse_witness_topK_within_3px_of_my_dots": round(dot_overlap(topk.astype(np.float32),
                                                                            d.astype(np.float32), RADIUS_PX), 4),
        }

    result = {
        "schema": "gems86.nine-site-lineage.v1",
        "evidence_class": "REGISTRY-MEASUREMENT + MEASURED-FILE-AUDIT; owner scores are OWNER-REPORTED",
        "not_a_score": True,
        "not_a_clearance": True,
        "decision": "DO NOT SUBMIT",
        "safe_to_submit": False,
        "approved_for_weekly_slot": False,
        "submission_slots_used": 0,
        "sources": {
            "owner_repos": {s: f"https://github.com/{OWNER}/{s}" for s in SITES},
            "codeload_pattern": "https://codeload.github.com/buffedlizard55-lab/<repo>/tar.gz/HEAD",
            "witness": "https://github.com/buffedlizard55-lab/17GEMSDOE/blob/HEAD/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif",
            "metric_source": "vendor/gems57/metric.py (transcription of DrivenData competition 306 page 967, cross-checked by the repo)",
            "reference_solution": "https://github.com/drivendataorg/gems-prize-reference-solution",
        },
        "overlap_rule": "dot_overlap(A,B) = fraction of A's dots within 3 px of any B dot (gems57.uniqueness)",
        "nine_site_files": rows,
        "pairwise_overlap_rows_my_dots_near_column": {
            "order": list(SITES),
            "matrix": [[None if i == j else round(float(M[i, j]), 4) for j in range(n)] for i in range(n)],
        },
        "pairwise_summary": {
            "ordered_pairs": int(off.size),
            "pairs_over_0_70": int((off > 0.70).sum()),
            "min": round(float(off.min()), 4),
            "max": round(float(off.max()), 4),
        },
        "variant_identity_checks": variant_checks,
        "h33_lineage": lineage | {"parent_file": g31_name, "child_file": h33_name},
        "witness": {
            "sha256": sha256(witness),
            "pinned_sha256_matches": sha256(witness) == json.loads(PIN.read_text())["sha256"],
            "grid_matches_reference": bool(w_ok),
            "inside_footprint_min": round(float(inside.min()), 6),
            "inside_footprint_max": round(float(inside.max()), 6),
            "literal_positive_cells_in_footprint": literal_positive_in_footprint,
            "literal_gate_status": "UNCHANGED - fails: every footprint cell is positive, so every nonempty candidate has overlap 1.0 (see protocol-preflight.json)",
            "topK_diagnostic": {
                "k": TOPK_DOTS,
                "definition": "DIAGNOSTIC ONLY - top-37,654 cells of the continuous surface as a dot set",
                "results": diag,
            },
        },
    }

    text = json.dumps(result, indent=2, sort_keys=False) + "\n"
    if args.write:
        OUT.write_text(text)
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
