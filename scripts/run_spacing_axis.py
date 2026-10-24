#!/usr/bin/env python3
"""SPACING axis on R0 (GEMSDOE32 h33-h33-2-b2): re-space the kernel-crowded mass
under three placement geometries, and change nothing else.

Parent R0
---------
``h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros``, sha256
``c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9``:
37,654 unit-mass dots on the H19-5 ridge support, min nearest-neighbour 2.828 px
(the d2.8 greedy thinning), 0.2778 is a CLAIM, never a receipt.

The axis (brief v2 section 5)
-----------------------------
SPACING = "lattice vs Poisson-disk vs along-strike at matched count".  Every
variant keeps 37,654 dots on the parent's own support (H19-5 cells), unit mass,
zero catalogue mass, and differs from R0 only in *where* the re-spaced mass
lands.  The brief's 1-50 % contract rules out a global re-arrangement, so the
edit is local and identical in all three arms:

* crowded set: R0 dot pairs closer than the DTI kernel radius R = 3.0 px
  (11,415 dots, 30.3 %, sit within 3 px of another dot).  In each crowded
  connected cluster, the member with the earliest H19-5 visit rank (the
  parent's own recipe ranking, rebuilt and validated to reproduce d2.8 exactly)
  stays; the other members form the crowded pool (6,574 dots = 17.46 % of R0).
  Each pool member is offered a destination; roughly 3,050 (~8.1 % of R0's
  dots) find one within 16 px at the parent's spacing floor and move, the rest
  stay put in the saturated corridors and are counted as residual crowding.
* every moved dot lands on an H19-5 cell, >= 3.0 px from the catalogue (the
  >=3 px rule binds newly emitted mass only, IR-86-RELIEF-02), >= 3.0 px from
  its cluster's kept dot (the crowded pair is broken at the kernel radius) and
  >= 2.828 px (= sqrt(8), the parent's own thinning floor) from every other
  dot of the final set.  A fully kernel-disjoint configuration at matched count
  is locally infeasible on this support (measured; IR-86-SPACING-01), so the
  3.0 px floor binds the broken pair and the parent's floor binds the rest.
* the three values differ ONLY in the destination rule for the same moved set:

  lattice      -> the legal cell nearest to a site of the square lattice of
                  pitch 3.0 px anchored at the raster origin (regular array).
  poisson-disk -> a seeded uniform draw among the legal cells (dart throwing
                  with the floor as inhibition radius; blue noise).
  along-strike -> the legal cell on the local ridge tangent through the
                  original cell, oriented away from the cluster's kept dot
                  (beads on a string at kernel pitch along the lineament).

Instruments (report only, never gates)
--------------------------------------
catalogue hide-and-recover PROXY (free and fixed-collar, per IR-86-SNAP-06),
the single-feature leakage canary (AUC > 0.90 stops the session), and the USGS
SGMC off-catalogue control.  Nothing here scores a submission, contacts a
leaderboard, or chooses a slot.

Usage
-----
    .venv/bin/python scripts/run_spacing_axis.py [--no-write] [--stamp YYYYMMDD]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57 import metric as g57metric                      # noqa: E402
from gems57 import grid as g57grid                          # noqa: E402
from gems57.gates import format_report                      # noqa: E402
from gems57.validate import validate                        # noqa: E402
from src.gems86 import prune as P                           # noqa: E402
from src.gems86 import instrument as I                      # noqa: E402
import run_prune_ladder as L                                # noqa: E402

BRIDGE = ROOT / "data" / "bridge"
FLEET = ROOT / "data" / "scored_fleet"
GEMS_DATA = ROOT / ".cache" / "gems_data"

PARENT_ID = "h33-h33-2-b2-20261004-e5eb6e7e"
PARENT_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
AXIS = "SPACING"
SEED = 20261023
KERNEL_R = 3.0            # DTI triangular kernel radius, px
COLLAR_PX = 3.0           # >= 3 px off the catalogue for newly emitted mass
WINDOW_PX = 6.0           # primary destination window, px
WINDOW_MAX_PX = 24.0      # expanded windows before a recorded long relocation

PATHS = {
    "sample": BRIDGE / "sample_submission.tif",
    "catalogue": BRIDGE / "existing_faults.tif",
    "parent": FLEET / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "base": FLEET / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
    "h19": GEMS_DATA / "scored" / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
    "d28": GEMS_DATA / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "sgmc": GEMS_DATA / "external" / "derived_sgmc_faults_100m_u8.tif",
}
PINS = {
    "sample": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "catalogue": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "parent": PARENT_SHA,
    "base": "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
    "h19": "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
    "d28": "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8",
    "sgmc": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
}

# (value, tag, predicted live change MODEL, band, one-line mechanism)
VARIANTS = (
    ("lattice", "lattice",
     0.000, (-0.004, 0.004),
     "break the crowded pair at the kernel radius and snap the freed dot to the nearest "
     "3 px lattice site: regularity without lineament knowledge; if truth is area-like this "
     "is the best of the three, if line-like it leaves coverage on the table"),
    ("poisson-disk", "poissondisk",
     0.000, (-0.004, 0.004),
     "the neutral arm: same pair-breaking at fixed count, destination drawn at random from "
     "the legal cells; any effect shared with the other two arms is de-crowding itself"),
    ("along-strike", "alongstrike",
     0.002, (-0.003, 0.006),
     "the freed dot slides along its own lineament past the kernel radius: it keeps its "
     "self-credit on the same trace and extends trace coverage where line-like truth is "
     "densest; predicted best of the three if fault truth follows the ridges"),
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B = _load("build_r0_prune")
MASS = _load("build_mass_axis")


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              check=True).stdout.decode().strip()
    except Exception:  # pragma: no cover
        return "unknown"


def verify_pins() -> dict:
    rec = {}
    for name, path in PATHS.items():
        if not path.is_file():
            raise SystemExit(f"missing pinned input {name}: {path}")
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != PINS[name]:
            raise SystemExit(f"PIN MISMATCH {name}: {got} != {PINS[name]}")
        rec[name] = {"path": str(path.relative_to(ROOT)), "sha256": got, "bytes": path.stat().st_size,
                     "pin": PINS[name], "verified": True}
    return rec


# ---------------------------------------------------------------- moved set
def crowded_moved_set(parent: np.ndarray, rank: np.ndarray):
    """Keep the earliest-visit-rank dot of each d < 3 px cluster; the rest move.

    Returns (pts, moved_mask, cluster_labels, n_clusters).
    """
    pts = np.argwhere(parent)
    n = len(pts)
    tree = cKDTree(pts)
    pairs = tree.query_pairs(KERNEL_R, output_type="ndarray")
    if len(pairs):
        dmat = np.sqrt(((pts[pairs[:, 0]] - pts[pairs[:, 1]]) ** 2).sum(1))
        pairs = pairs[dmat < KERNEL_R - 1e-9]
    adj = sp.coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n))
    ncomp, lab = sp.csgraph.connected_components(adj, directed=False)
    ranks = rank[pts[:, 0], pts[:, 1]]
    moved = np.zeros(n, bool)
    n_clusters = 0
    for c in range(ncomp):
        members = np.flatnonzero(lab == c)
        if len(members) < 2:
            continue
        n_clusters += 1
        keep = members[np.argmin(ranks[members])]
        moved[members] = True
        moved[keep] = False
    return pts, moved, lab, n_clusters


# ---------------------------------------------------------------- placement
def lattice_site_distance(cells: np.ndarray) -> np.ndarray:
    """Distance from each (row, col) cell to the nearest site of the 3 px square lattice."""
    y = cells[:, 0] % int(KERNEL_R)
    x = cells[:, 1] % int(KERNEL_R)
    dy = np.minimum(y, int(KERNEL_R) - y)
    dx = np.minimum(x, int(KERNEL_R) - x)
    return np.hypot(dy, dx)


def strike_direction(h19: np.ndarray, cell: np.ndarray, anchor: np.ndarray) -> np.ndarray:
    """Unit ridge tangent near ``cell`` (PCA of H19 support within 3 px), oriented
    away from the cluster's kept anchor.  Falls back to the cell->anchor axis."""
    h, w = h19.shape
    y, x = int(cell[0]), int(cell[1])
    r = 3
    ys, xs = np.mgrid[max(0, y - r):min(h, y + r + 1), max(0, x - r):min(w, x + r + 1)]
    sel = h19[ys, xs]
    pts = np.column_stack([ys[sel], xs[sel]]).astype(float)
    away = cell.astype(float) - anchor.astype(float)
    if pts.shape[0] >= 2 and np.ptp(pts, axis=0).sum() > 0:
        centred = pts - pts.mean(0)
        cov = centred.T @ centred
        w2, v = np.linalg.eigh(cov)
        u = v[:, np.argmax(w2)]
        if np.hypot(*u) < 1e-12:
            u = away
    else:
        u = away
    n = np.hypot(*u)
    u = u / (n if n > 1e-12 else 1.0)
    if float(away @ u) < 0:
        u = -u
    return u


def choose_destination(rule: str, legal: np.ndarray, orig: np.ndarray, anchor: np.ndarray,
                       h19: np.ndarray, rng) -> np.ndarray:
    """Pick one legal cell (N,2 int) according to ``rule``.  Deterministic per arm."""
    if rule == "lattice":
        score = (lattice_site_distance(legal),
                 np.hypot(legal[:, 0] - orig[0], legal[:, 1] - orig[1]),
                 legal[:, 0], legal[:, 1])
        order = np.lexsort(score)
        return legal[order[0]]
    if rule == "poisson-disk":
        order = np.lexsort((legal[:, 1], legal[:, 0]))
        pick = int(rng.integers(len(legal)))
        return legal[order[pick]]
    if rule == "along-strike":
        u = strike_direction(h19, orig, anchor)
        v = legal.astype(float) - orig.astype(float)
        perp = np.abs(v[:, 0] * u[1] - v[:, 1] * u[0])
        along = v @ u
        disp = np.hypot(v[:, 0], v[:, 1])
        # on-line first, then further along-strike away from the anchor, then nearest
        order = np.lexsort((legal[:, 1], legal[:, 0], disp, -along, np.round(perp, 3)))
        return legal[order[0]]
    raise ValueError(rule)


def _disc_offsets(floor_sq: int) -> np.ndarray:
    """Integer offsets with squared distance < floor_sq (exclusion disc)."""
    off = []
    r = int(np.ceil(np.sqrt(floor_sq)))
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy * dy + dx * dx < floor_sq:
                off.append((dy, dx))
    return np.array(off, dtype=int)


# parent's own spacing floor: 2.828 px = sqrt(8); exclusion disc is d^2 < 8
OFFSETS = _disc_offsets(8)


def _mark(grid: np.ndarray, cell, sign: int) -> None:
    y, x = int(cell[0]), int(cell[1])
    h, w = grid.shape
    ys = y + OFFSETS[:, 0]
    xs = x + OFFSETS[:, 1]
    ok = (ys >= 0) & (ys < h) & (xs >= 0) & (xs < w)
    np.add.at(grid, (ys[ok], xs[ok]), sign)


def re_space(parent: np.ndarray, h19: np.ndarray, rank: np.ndarray, dist_cat: np.ndarray,
             footprint: np.ndarray, rule: str, seed: int = SEED) -> tuple[np.ndarray, dict]:
    """Move the crowded set under ``rule``; keep count, support, and exclusions.

    Destination legality (shared by all three values):

    * on the parent's own support (H19-5), inside the footprint;
    * >= 3.0 px from the catalogue (newly emitted mass, IR-86-RELIEF-02);
    * >= 3.0 px from the cluster's kept dot -- the crowded pair is broken at the
      kernel radius;
    * >= 2.828 px (= sqrt(8), the parent's own thinning floor) from every other
      dot of the final set -- the parent's minimum spacing is never tightened;
    * never on the original cell of an *unresolved* mover (reserved, so a mover
      that cannot be placed always keeps its own cell).

    Unresolved movers block their own disc until they resolve (vacate-try-
    restore on retry), so every placement respects the final set and the count
    is held by construction.  A mover with no legal cell stays put; its crowded
    pair then survives and is counted in the run card (IR-86-SPACING-01).
    """
    pts, moved_mask, lab, n_clusters = crowded_moved_set(parent, rank)
    n = len(pts)
    ranks = rank[pts[:, 0], pts[:, 1]]
    moved_idx = np.flatnonzero(moved_mask)
    moved_idx = moved_idx[np.argsort(ranks[moved_idx], kind="stable")]  # visit-rank order

    anchor_of = {}
    for c in np.unique(lab[moved_mask]):
        members = np.flatnonzero(lab == c)
        keep = members[np.argmin(ranks[members])]
        for m in members:
            if m != keep:
                anchor_of[m] = pts[keep]

    blocked = np.zeros(parent.shape, np.int16)
    final = np.zeros(parent.shape, bool)
    for k, cell in enumerate(pts):
        if not moved_mask[k]:
            _mark(blocked, cell, 1)      # kept dots block from the start
            final[tuple(int(v) for v in cell)] = True

    h19_cells = np.argwhere(h19 & footprint & (dist_cat >= COLLAR_PX))
    h19_tree = cKDTree(h19_cells)

    rng = np.random.default_rng(seed)
    origins = {int(i): (int(pts[i][0]), int(pts[i][1])) for i in moved_idx}
    is_reserved = np.zeros(parent.shape, bool)
    for _c in origins.values():
        is_reserved[_c] = True           # unresolved movers keep their own cell

    for i in origins:
        _mark(blocked, origins[i], 1)    # provisional disc until resolved

    placed: dict[int, tuple[int, int]] = {}
    disp_list = []
    moved_from_to = []

    def attempt(i):
        orig = origins[i]
        anchor = anchor_of[i]
        _mark(blocked, orig, -1)         # vacate own disc while searching
        for window in (4.0, 8.0, 16.0):
            cand = h19_tree.query_ball_point(orig, window)
            if not cand:
                continue
            cells = h19_cells[cand]
            ok = blocked[cells[:, 0], cells[:, 1]] == 0
            ok &= ~is_reserved[cells[:, 0], cells[:, 1]]
            d2 = (cells[:, 0] - anchor[0]) ** 2 + (cells[:, 1] - anchor[1]) ** 2
            legal = cells[ok & (d2 >= 9)]
            if len(legal):
                return choose_destination(rule, legal, np.asarray(orig), anchor, h19, rng)
        return None

    pending = dict(origins)
    while pending:
        progress = False
        for i in list(pending):
            best = attempt(i)
            if best is None:
                _mark(blocked, origins[i], 1)   # stays unresolved: restore disc
                continue
            dest = (int(best[0]), int(best[1]))
            _mark(blocked, dest, 1)
            final[dest] = True
            placed[i] = dest
            moved_from_to.append((origins[i], dest))
            disp_list.append(float(np.hypot(dest[0] - origins[i][0], dest[1] - origins[i][1])))
            is_reserved[origins[i]] = False    # its old cell is free again
            del pending[i]
            progress = True
        if not progress:
            break

    # pending dots stay at their own reserved cells (discs already marked)
    for i in pending:
        final[origins[i]] = True

    child = final
    n_moved = len(placed)
    if int(child.sum()) != n:
        raise SystemExit(f"count not held: {int(child.sum())} != {n}")
    stats = dict(
        n_parent=n,
        n_child=int(child.sum()),
        n_clusters=n_clusters,
        n_crowded_pool=len(origins),
        n_moved=n_moved,
        n_stayed=len(pending),
        pct_dots_changed=round(100.0 * n_moved / n, 4),
        pct_cells_changed=round(200.0 * n_moved / n, 4),
        displacement_mean_px=float(np.mean(disp_list)) if disp_list else 0.0,
        displacement_median_px=float(np.median(disp_list)) if disp_list else 0.0,
        displacement_max_px=float(np.max(disp_list)) if disp_list else 0.0,
        moved_from_to=moved_from_to,
    )
    return child, stats


def move_diff(parent: np.ndarray, child: np.ndarray, dist_cat: np.ndarray) -> dict:
    removed = parent & ~child
    added = child & ~parent
    n_parent = int(parent.sum())
    return {
        "n_parent": n_parent,
        "n_child": int(child.sum()),
        "n_removed": int(removed.sum()),
        "n_added": int(added.sum()),
        "pct_dots_changed": round(100.0 * int(removed.sum()) / n_parent, 4),
        "pct_cells_changed": round(100.0 * (int(removed.sum()) + int(added.sum())) / n_parent, 4),
        "min_catalogue_distance_added_px": float(dist_cat[added].min()) if added.any() else None,
        "kept_fraction": round(float((parent & child).sum()) / n_parent, 6),
    }


def spacing_stats(dots: np.ndarray) -> dict:
    pts = np.argwhere(dots)
    d, _ = cKDTree(pts).query(pts, k=2)
    nn = d[:, 1]
    return {
        "min_nn_px": float(nn.min()),
        "mean_nn_px": float(nn.mean()),
        "median_nn_px": float(np.median(nn)),
        "n_within_3px": int((nn < KERNEL_R).sum()),
        "fraction_within_3px": round(float((nn < KERNEL_R).mean()), 6),
    }


# ---------------------------------------------------------------- instruments
def proxy_fixed_collar(pred: np.ndarray, catalogue: np.ndarray, footprint: np.ndarray,
                       dist_cat: np.ndarray, *, n_draws: int = 10, hide_frac: float = 0.2,
                       seed: int = 306) -> dict:
    """Hide-and-recover PROXY with one fixed >=3 px catalogue collar on every arm
    (IR-86-SNAP-06: only such a comparison is admissible)."""
    masked = pred & (dist_cat >= COLLAR_PX)
    return L.proxy_dti(masked, catalogue, footprint, n_draws=n_draws, hide_frac=hide_frac, seed=seed)


def leakage_canary(g, h19: np.ndarray) -> dict:
    folds = I.build(g.footprint, g.catalogue, seed=20)
    rows = []
    for fold in folds:
        active = g.footprint & fold.region & ~fold.known
        truth = active & fold.truth
        from scipy import ndimage as ndi
        dvis = ndi.distance_transform_edt(~fold.visible)
        for feature, surface in (("h19_5_binary", h19.astype(float)),
                                 ("negative_distance_to_visible_catalogue", -dvis)):
            from sklearn.metrics import roc_auc_score
            auc = float(roc_auc_score(truth[active], surface[active]))
            rows.append({"fold": fold.name, "feature": feature, "auc": auc,
                         "withheld_positives": int(truth.sum())})
    maximum = max(r["auc"] for r in rows)
    return {"status": "PASS" if maximum <= 0.90 else "STOP_INVESTIGATE", "threshold": 0.90,
            "max_auc": maximum, "rows": rows,
            "note": "single-feature diagnostics only; catalogue-derived distance is not an "
                    "independent physical feature (see build_r0_prune.leakage_canaries)"}


def _plain(obj):
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def sgmc_control(arms: dict, g, dist_cat: np.ndarray) -> dict:
    sgmc = L.read(PATHS["sgmc"]) > 0
    off_truth = sgmc & g.footprint & ~g.catalogue & (dist_cat > COLLAR_PX)
    scores = {}
    for name, mask in arms.items():
        res = g57metric.dti_binary(mask, off_truth, valid=g.footprint, known=g.catalogue)
        scores[name] = {k: res[k] for k in ("dti", "tp", "fp", "fn", "n_truth", "n_emitted")}
    scores["delta_vs_R0"] = {k: round(scores[k]["dti"] - scores["R0"]["dti"], 6)
                             for k in arms if k != "R0"}
    return {"evidence_class": "PROXY",
            "instrument": "official-kernel DTI vs USGS SGMC off-catalogue faults (d_cat > 3 px)",
            "scores": scores,
            "note": "SGMC is an independent-map control, never hidden competition truth; "
                    "report only. With a fixed >=3 px collar this control also collapses "
                    "(IR-86-SNAP-06); the free reading is shown for continuity."}


# ---------------------------------------------------------------- main
def main() -> int:
    # Historical variant builders obey the same literal pre-placement stop.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--stamp", default=None)
    args = ap.parse_args()
    t0 = time.time()
    stamp = args.stamp or time.strftime("%Y%m%d")

    print("[1/7] verifying input pins", flush=True)
    pins = verify_pins()

    g = g57grid.load_grid(BRIDGE)
    dist = P.catalogue_distance(g.catalogue)
    parent = L.read(PATHS["parent"]) > 0
    base = L.read(PATHS["base"])

    print("[2/7] rebuilding the parent R0 byte-for-byte", flush=True)
    rebuild = L.rebuild_parent(g, base)
    if not (rebuild["content_identical"] and rebuild["byte_identical_sha"]):
        raise SystemExit("parent rebuild failed; stop and report (never approximate the parent)")

    print("[3/7] rebuilding the parent's own ranking and validating it", flush=True)
    h19 = B.read_binary(PATHS["h19"], g.footprint)
    d28 = B.read_binary(PATHS["d28"], g.footprint)
    rank = B.original_visit_rank(h19)
    reproduced = MASS.greedy_thin(h19, rank, 2.8)
    rank_diff = int((reproduced != d28).sum())
    if rank_diff:
        raise SystemExit(f"visit-rank reconstruction does not reproduce d2.8 ({rank_diff} cells)")
    ranking = {"recipe": "FIFO-BFS visit rank of the H19-5 field (original_visit_rank)",
               "validation": "greedy_thin(h19, rank, 2.8) reproduces the pinned d2.8 set exactly",
               "differing_cells": rank_diff, "n_dots": int(reproduced.sum())}

    pts, moved_mask, lab, n_clusters = crowded_moved_set(parent, rank)
    n_moved_total = int(moved_mask.sum())
    moved_set = {"criterion": "pair distance < 3.0 px (DTI kernel radius); keep the earliest "
                              "visit-rank member of each crowded cluster",
                 "n_crowded_dots": int(n_moved_total + n_clusters),
                 "n_clusters": n_clusters, "n_moved": n_moved_total,
                 "pct_dots_changed": round(100.0 * n_moved_total / int(parent.sum()), 4)}
    print(f"      moved set: {n_moved_total} dots = {moved_set['pct_dots_changed']}% of R0", flush=True)

    out_dir = ROOT / "releases"
    if not args.no_write:
        out_dir.mkdir(exist_ok=True)
        for stale in out_dir.glob(f"{PARENT_ID}-{AXIS}-*.tif"):
            stale.unlink()
        for stale in out_dir.glob(f"{PARENT_ID}-{AXIS}-*-zeros.json"):
            stale.unlink()

    novelty = set()
    if (ROOT / "ledger" / "submissions.csv").exists():
        with open(ROOT / "ledger" / "submissions.csv", newline="") as fh:
            novelty |= {r["sha256"] for r in csv.DictReader(fh) if r.get("sha256")}
    for d in (FLEET, ROOT / "docs" / "downloads"):
        novelty |= {hashlib.sha256(p.read_bytes()).hexdigest() for p in d.glob("*.tif")}

    cards, written = {}, []
    arms = {"R0": parent}
    print("[4/7] building the three SPACING arms", flush=True)
    for value, tag, predicted, band, mech in VARIANTS:
        print(f"      {value}: re-spacing", flush=True)
        child, mstats = re_space(parent, h19, rank, dist, g.footprint, value)
        if int(child.sum()) != int(parent.sum()):
            raise SystemExit(f"{value}: count not held")
        if np.any(child & g.catalogue):
            raise SystemExit(f"{value}: positive mass on the catalogue")
        diff = move_diff(parent, child, dist)
        sstats = spacing_stats(child)
        if sstats["min_nn_px"] < 2.8284271247461903 - 1e-9:
            raise SystemExit(f"{value}: final min NN {sstats['min_nn_px']} tightened below the parent floor")
        if diff["min_catalogue_distance_added_px"] is not None \
                and diff["min_catalogue_distance_added_px"] < COLLAR_PX - 1e-9:
            raise SystemExit(f"{value}: newly emitted mass within 3 px of the catalogue")
        if not (1.0 <= diff["pct_dots_changed"] <= 50.0):
            raise SystemExit(f"{value}: {diff['pct_dots_changed']}% changed is outside 1-50%")
        cards[value] = dict(axis=AXIS, value=value, rule=tag, mechanism=mech,
                            movement=mstats, parent_diff=diff, spacing=sstats,
                            predicted_live_change=predicted, predicted_band=list(band),
                            evidence_class="MODEL")
        arms[value] = child

        if not args.no_write:
            pred = child.astype(np.float32)
            name_note = (f"R0 {PARENT_ID}; SPACING {value}: {mstats['n_moved']} crowded dots "
                         f"re-spaced at 3.0px, count fixed; pred {predicted:+.3f} MODEL")[:140]
            probe_dir = Path(tempfile.mkdtemp())
            probe = probe_dir / "probe.tif"
            zeros_arr = np.where(g.footprint, pred, np.float32(0.0)).astype(np.float32)
            sha8 = L.write_with_profile(probe, zeros_arr, None)[:8]
            shutil.rmtree(probe_dir, ignore_errors=True)
            name = f"{PARENT_ID}-{AXIS}-{tag}-{stamp}-{sha8}"
            zeros_path = out_dir / f"{name}-zeros.tif"
            nan_path = out_dir / f"{name}.tif"
            for p in (zeros_path, nan_path, zeros_path.with_suffix(".json")):
                if p.exists():
                    p.unlink()
            nan_arr = np.where(g.footprint, pred, np.float32("nan")).astype(np.float32)
            nan_sha = L.write_with_profile(nan_path, nan_arr, float("nan"))
            v_all = validate(nan_path, g.footprint, g.catalogue)
            nan_checks = {k: bool(v) for k, v in v_all["checks"].items() if k != "no_nan_anywhere"}
            zinfo = {"sha256": L.write_with_profile(zeros_path, zeros_arr, None)}
            if zinfo["sha256"][:8] != sha8:
                raise SystemExit(f"{value}: probed sha8 != written")
            v_zero = validate(zeros_path, g.footprint, g.catalogue)
            rep_zero = format_report(zeros_path, BRIDGE / "sample_submission.tif", footprint=g.footprint)
            if not v_zero["all_checks_passed"] or not rep_zero["ok"]:
                raise SystemExit(f"{value}: shared gates failed: {rep_zero['problems']}")
            if zinfo["sha256"] in novelty:
                raise SystemExit(f"{value}: sha256 already present in the ledger")
            novelty.add(zinfo["sha256"])
            receipt = dict(
                id=name, parent=PARENT_ID, axis=AXIS, value=value, role="candidate",
                n_dots=int(child.sum()), n_moved=mstats["n_moved"],
                pct_changed=mstats["pct_dots_changed"],
                pct_cells_changed=mstats["pct_cells_changed"],
                movement={k: v for k, v in mstats.items() if k != "moved_from_to"},
                spacing=sstats, parent_diff=diff,
                dot_digest=P.dot_digest(child),
                zeros=dict(file=zeros_path.name, sha256=zinfo["sha256"],
                           bytes=zeros_path.stat().st_size,
                           validator=v_zero, format_report_ok=rep_zero["ok"]),
                nan=dict(file=nan_path.name, mode="nan", sha256=nan_sha,
                         bytes=nan_path.stat().st_size,
                         in_footprint_checks_pass=all(nan_checks.values()),
                         failed_checks=[k for k, v in v_all["checks"].items() if not v],
                         policy_note="public spec permits NaN outside the footprint; repo "
                                     "all-finite policy rejects it"),
                submission_name=name[:140], note=name_note[:140],
                predicted_live_change=predicted, predicted_band=list(band),
                evidence_class="MODEL",
                approved_for_weekly_slot=False, submission_slots_used=0,
                provenance=dict(input_pins=pins, parent_rebuild=rebuild, ranking=ranking,
                                moved_set=moved_set, seed=SEED, git_sha=git_sha()),
                generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            zeros_path.with_suffix(".json").write_text(json.dumps(_plain(receipt), indent=2, allow_nan=False) + "\n")
            written.append(receipt)
        print(f"      {value}: moved {mstats['n_moved']} ({mstats['pct_dots_changed']}%), "
              f"mean disp {mstats['displacement_mean_px']:.2f} px, min NN {sstats['min_nn_px']:.3f} px",
              flush=True)

    print("[5/7] report-only instruments", flush=True)
    proxy_free = {k: L.proxy_dti(v, g.catalogue, g.footprint) for k, v in arms.items()}
    proxy_collar = {k: proxy_fixed_collar(v, g.catalogue, g.footprint, dist) for k, v in arms.items()}
    canary = leakage_canary(g, h19)
    if canary["status"] != "PASS":
        print(f"      LEAKAGE CANARY {canary['status']}: max AUC {canary['max_auc']:.4f}", flush=True)
        raise SystemExit("leakage canary tripped: stop and investigate before releasing")
    print(f"      canary PASS (max AUC {canary['max_auc']:.4f})", flush=True)
    sgmc = sgmc_control(arms, g, dist)
    for k, v in sgmc["scores"].items():
        print(f"      sgmc {k}: {v if not isinstance(v, dict) else v.get('dti', v)}", flush=True)

    summary = dict(
        schema_version=1,
        session_date=stamp,
        seed=SEED,
        git_sha=git_sha(),
        status="BUILT",
        submission_ready=False,
        submission_slots_used=0,
        parent=dict(id=PARENT_ID, sha256=PARENT_SHA, n_dots=int(parent.sum()),
                    claim=0.2778, evidence_class="CLAIM"),
        axis=AXIS,
        axis_choice_note="SPACING is the only listed weekly axis with no (AXIS, value) pair in "
                         "the ledger; its three brief-named values (lattice, Poisson-disk, "
                         "along-strike) fit the up-to-3-variants budget exactly. TRACKB stays "
                         "Phase 2 (human decision).",
        parent_gate=rebuild,
        input_pins=pins,
        ranking=ranking,
        moved_set=moved_set,
        interpretation="SPACING values are realised as the destination geometry of the "
                       "kernel-crowded pool (dots with a neighbour inside the 3.0 px kernel "
                       "radius). A global re-patterning would change ~100% of R0's dots and is "
                       "barred by the brief's 1-50% contract (same tension as IR-86-SNAP-03). "
                       "Each moved dot breaks its crowded pair at >=3.0 px from its cluster's "
                       "kept dot and keeps the parent's own 2.828 px floor elsewhere; a fully "
                       "kernel-disjoint set at matched count is locally infeasible on this "
                       "support (IR-86-SPACING-01).",
        spacing_parent=spacing_stats(parent),
        variants=cards,
        instruments=dict(
            proxy_free={k: {kk: vv for kk, vv in v.items()} for k, v in proxy_free.items()},
            proxy_fixed_collar_d3={k: {kk: vv for kk, vv in v.items()} for k, v in proxy_collar.items()},
            leakage_canary=canary,
            sgmc_control=sgmc,
            note="report only; IR-86-SNAP-06: free-proxy numbers may not rank arms, and with "
                 "the fixed >=3 px collar this lineage's proxy reads 0.0000"),
        written=[w["id"] for w in written],
        gates=dict(format="shared validate + format_report against sample_submission.tif",
                   zero_catalogue_mass="asserted in memory and re-read from disk",
                   sha_novel="checked against ledger/submissions.csv, data/scored_fleet and docs/downloads",
                   parent_diff="recorded per variant (move-aware diff + spacing stats)",
                   reread_from_disk="yes (validate() and format_report() open the written file)"),
        not_a_score="Every number above is a MODEL projection or a PROXY measurement. No "
                    "submission was made and no receipt exists. Live |delta| < 0.01 is no "
                    "evidence (public chunks only; the private score may differ).",
    )
    (ROOT / "evidence").mkdir(exist_ok=True)
    out = ROOT / "evidence" / f"spacing_axis_{stamp}.json"
    out.write_text(json.dumps(_plain(summary), indent=2, allow_nan=False) + "\n")
    print(f"[6/7] wrote {out.relative_to(ROOT)}; {len(written)} candidates packed", flush=True)
    print("[7/7] done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
