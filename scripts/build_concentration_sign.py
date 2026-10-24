#!/usr/bin/env python3
"""CONCENTRATION axis, *sign* experiment on parent R0 = ``h33-h33-2-b2``.

Why this axis and this value
----------------------------
``CONCENTRATION`` is the only brief-5 axis whose built arm (``gems86-h33-2b2-conc15``,
PR #37) is a *spatial-prior* claim rather than a geometry claim, and its own falsifier asks
for exactly this session's build: "<= -0.010 -> the region wants *less* clustering: build the
spread variant instead".  The built arm moved 15 % of the dots *into* the highest-prior 1 km
blocks.  This script builds the matched mirror, plus the null control that makes the pair
interpretable.  Nothing here reads a label raster.

Three arms, one rule each, all at 1 km blocks (``BLOCK_PX = 10``), count fixed at 37,654,
parent spacing floor 2.828 px, new mass >= 3 px off the catalogue (brief 4.4 for emitted
mass, IR-86-RELIEF-02 for inherited dots):

``spr15``    source = dots in the HIGHEST-prior occupied blocks, destination = the
             LOWEST-prior occupied blocks.  Mirror of the built ``dense`` arm.
``dens15``   source = dots in the LOWEST-prior occupied blocks, destination = the HIGHEST-prior
             occupied blocks.  Paired calibration of the mirror under *this* script's prior.
``rand15``   CONTROL - the ``spr15`` source dots, destination = a random sample of occupied
             blocks.  Separates "the block prior matters" from "moving mass at all matters".

Prior (band-free).  ``block_prior()`` in ``src/gems86_axis/variants.py`` needs an upward-
continued-TMI gradient band from the 419 MB feature stack, which is absent from this checkout
(``.cache/gems_data`` does not exist).  This script uses that function's catalogue term only:
the z-scored 3 x 3 km mean of mapped-fault pixels, per 1 km block.  The substitution is logged
in ``IRREGULARITIES.md`` (IR-86-CONC-03) because it blocks a one-variable attribution against
PR #37's arm; the ``dens15`` arm exists to price it.

Destination blocks are restricted to blocks that already contain parent dots.  Reason: an
unrestricted lowest-prior fifth is the empty far field, and ledger evidence says what a
near-uniform far-field dot set scores (GEMSDOE81 ``cont-poisson44090``: 0.0041 CLAIM against
R0's 0.2778).  The restriction keeps every arm on the lineage's own support surface
(IR-86-SPACING-02) and is applied identically to all three arms.

Usage::

    .venv/bin/python scripts/build_concentration_sign.py [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import metric  # noqa: E402
from gems86_axis import gates, grid_io, variants  # noqa: E402
from gems86_axis.grid_io import dot8  # noqa: E402

DATE_TAG = "20261023"
SEED = 20261023
BLOCK_PX = 10                  # 1 km at the 100 m grid
DOSE = 0.15                    # 15 % of R0's dots, inside the brief's 10-20 % band
DEST_BLOCK_FRAC = 0.20         # "highest/lowest-prior fifth" of the *occupied* blocks
MIN_SPACING_PX = grid_io.PARENT_MIN_SPACING_PX   # 2.8284271 -> R0's own floor
CLEARANCE_PX = 3.0             # brief 4.4, applied to newly emitted mass only

PATHS = {
    "sample": ROOT / "data/bridge/sample_submission.tif",
    "catalogue": ROOT / "data/bridge/existing_faults.tif",
    "parent": ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-"
                      "20261004T220000Z-e5eb6e7e-zeros.tif",
    "base": ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-"
                    "20261003-8acb75e1f2cc-nan.tif",
}
MANIFEST_IDS = {"parent": "scored_h33_2_b2_zeros", "catalogue": "existing_faults",
                "sample": "sample_submission"}
LITERAL_PINS = {
    "parent": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "base": "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
}
ARMS = (
    # (value, source sign, destination sign, role)
    ("spr15", +1, -1, "candidate"),
    ("dens15", -1, +1, "candidate"),
    ("rand15", +1, 0, "control"),
)


def sha256(path: Path) -> str:
    return hashlib.file_digest(open(path, "rb"), "sha256").hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              check=True).stdout.decode().strip()
    except Exception:                                    # pragma: no cover
        return "unknown"


def verify_inputs() -> dict:
    """Hash every input before it is read; abort on a mismatch (brief 4.2)."""
    man = {f["id"]: f for f in json.loads(
        (ROOT / "registry/data_manifest.json").read_text())["files"]}
    files, missing = {}, []
    for name, path in PATHS.items():
        if not path.is_file():
            missing.append(f"{name}: {path.relative_to(ROOT)}")
            continue
        got = sha256(path)
        expected = LITERAL_PINS.get(name)
        source = "registry/upstream_registry_index.json" if name == "base" else "committed pin"
        if expected is None and name in MANIFEST_IDS:
            expected = man[MANIFEST_IDS[name]]["sha256"]
            source = "registry/data_manifest.json"
        if expected and got != expected:
            raise SystemExit(f"PIN MISMATCH {name}: {got} != {expected}")
        files[name] = {"path": str(path.relative_to(ROOT)), "sha256": got,
                       "bytes": path.stat().st_size, "pin_source": source,
                       "organizer_authenticated": False}
    if missing:
        raise SystemExit("pinned input(s) absent; nothing is approximated:\n  " + "\n  ".join(missing))
    shared = json.loads((ROOT / "research/template_pin.json").read_text())
    for rel, expected in shared["files"].items():
        path = ROOT / rel
        if not path.is_file() or sha256(path) != expected:
            raise SystemExit(f"shared-tool pin mismatch: {rel}")
    return {"files": files, "shared_template_pins_verified": True,
            "pin_file": "research/template_pin.json",
            "absent_inputs": [{"manifest_id": "training_features",
                               "why": "419 MB feature stack not restored in this checkout; "
                                      "block_prior()'s TMI term is therefore unavailable"},
                              {"manifest_id": "ext_derived_sgmc_faults_100m_u8",
                               "why": "SGMC control raster absent; no SGMC gate this session"}],
            "note": "GitHub mirrors are integrity-pinned, NOT organizer-authenticated; the "
                    "competition data tab and dropbox.com are never contacted (brief 4.1)"}


def read(path: Path) -> np.ndarray:
    import rasterio

    with rasterio.open(path) as src:
        return src.read(1)


def rebuild_parent(foot: np.ndarray, cat: np.ndarray, out_dir: Path) -> dict:
    """Re-derive R0 from the pinned base and prove it byte-for-byte, or stop."""
    import rasterio

    base = read(PATHS["base"])
    bm = (np.nan_to_num(base, nan=0.0) > 0) & foot
    rebuilt = bm & (ndi.distance_transform_edt(~cat) > 2.0)
    parent = grid_io.load_dots(PATHS["parent"], foot)
    differing = int((rebuilt != parent).sum())
    if differing:
        raise SystemExit(f"R0 REBUILD MISMATCH: {differing} cells differ; stopping (brief 5)")
    with rasterio.open(PATHS["parent"]) as src:
        crs, transform = src.crs, src.transform
    out = out_dir / "rebuild_parent_zeros.tif"
    prof = dict(driver="GTiff", dtype="float32", count=1, compress="deflate", predictor=3,
                zlevel=9, tiled=True, blockxsize=256, blockysize=256, interleave="band",
                nodata=None, height=foot.shape[0], width=foot.shape[1], crs=crs, transform=transform)
    with rasterio.open(out, "w", **prof) as dst:
        dst.write(np.where(foot, rebuilt, 0.0).astype(np.float32), 1)
    digest = sha256(out)
    if digest != LITERAL_PINS["parent"]:
        raise SystemExit(f"R0 REBUILD NOT BYTE-EXACT: {digest} != {LITERAL_PINS['parent']}")
    return {"base_dots": int(bm.sum()), "rebuilt_dots": int(rebuilt.sum()),
            "parent_dots": int(parent.sum()), "differing_cells_vs_parent": differing,
            "rebuild_sha256": digest, "byte_exact": True,
            "recipe": "gems28-h27-4-r1-solo-d2-8 (40,199 dots) AND distance-to-catalogue > 2.0 px",
            "reencode": "deflate, predictor=3, zlevel=9, tiled 256, interleave=band, float32, no nodata"}


def catalogue_prior(foot: np.ndarray, cat: np.ndarray, block_px: int = BLOCK_PX) -> dict:
    """Band-free block prior: z-scored 3 x 3 km mean of mapped-fault pixels, per 1 km block.

    Same formula as the first term of ``variants.block_prior`` (which is not callable here: its
    second term needs the absent TMI stack).  Ties are exact - the smoothed field is continuous.
    """
    h, w = foot.shape
    nb, mb = h // block_px, w // block_px
    catf = ndi.uniform_filter((cat & foot).astype(np.float32), size=3 * block_px, mode="constant")

    def blk(a: np.ndarray) -> np.ndarray:
        return a[: nb * block_px, : mb * block_px].reshape(
            nb, block_px, mb, block_px).mean(axis=(1, 3))

    fpb = blk(foot.astype(np.float32))
    raw = blk(catf)
    mu, sd = raw[fpb > 0].mean(), raw[fpb > 0].std()
    prior = (raw - mu) / (sd if sd > 0 else 1.0)
    prior[fpb <= 0] = -np.inf
    return {"prior": prior.astype(np.float32), "footprint_blocks": fpb, "cat_block": raw,
            "block_px": block_px, "third_km_mean": 3 * block_px}


def _block_index(ctx_shape, block_px: int, rows: np.ndarray, cols: np.ndarray):
    return rows // block_px, cols // block_px


def build_arm(parent: np.ndarray, ctx: dict, prior: dict, value: str,
              source_sign: int, dest_sign: int, dose: float, seed: int) -> tuple[np.ndarray, dict]:
    """Relocate ``dose`` of the dots between 1 km blocks with the given prior signs.

    ``source_sign = +1`` -> source dots are drawn from the highest-prior blocks first.
    ``dest_sign   = +1`` -> destination blocks are the highest-prior fifth of occupied blocks;
    ``dest_sign   = -1`` -> the lowest-prior fifth; ``dest_sign = 0`` -> a random sample of
    occupied blocks (control).
    """
    foot, cat = ctx["footprint"], ctx["catalogue"]
    dots = parent & foot
    edt_cat = variants._cat_edt(cat)
    prior_b = prior["prior"]
    nb, mb = prior_b.shape
    block_px = prior["block_px"]
    n_move = int(round(dose * int(dots.sum())))

    rows, cols = np.nonzero(dots)
    br, bc = rows // block_px, cols // block_px
    occ_count = np.zeros(prior_b.shape, np.int32)
    np.add.at(occ_count, (br, bc), 1)
    occupied = occ_count > 0
    n_occ = int(occupied.sum())

    # ---- source: whole blocks, in prior order, until the dose is reached -------------
    occ_idx = np.flatnonzero(occupied.ravel())
    p_occ = prior_b.ravel()[occ_idx]
    order = occ_idx[np.argsort(-source_sign * p_occ, kind="stable")]
    # deterministic: take dots block by block in the source order until n_move is reached
    drop = np.zeros_like(dots)
    drop_sel: list[int] = []
    taken = 0
    for b in order:
        if taken >= n_move:
            break
        r0, c0 = divmod(int(b), mb)
        sel = (br == r0) & (bc == c0)
        idx = np.flatnonzero(sel)
        idx = idx[np.lexsort((cols[idx], rows[idx]))]
        take = idx[: max(0, n_move - taken)]
        drop[rows[take], cols[take]] = True
        drop_sel.extend(int(i) for i in take)
        taken += len(take)
    kept = dots & ~drop
    n_drop = int(drop.sum())
    drop_sel_arr = np.asarray(sorted(drop_sel), dtype=np.int64)

    # ---- destination blocks ---------------------------------------------------------
    n_dest = max(1, int(round(DEST_BLOCK_FRAC * n_occ)))
    if dest_sign == 0:
        rng = np.random.default_rng(seed)
        chosen = np.sort(rng.choice(occ_idx, size=min(n_dest, occ_idx.size), replace=False))
        dest_blocks = np.zeros(prior_b.shape, bool)
        dest_blocks.ravel()[chosen] = True
    else:
        dest_blocks = np.zeros(prior_b.shape, bool)
        dest_blocks.ravel()[occ_idx[np.argsort(-dest_sign * p_occ, kind="stable")][:n_dest]] = True
    dest_px = variants.block_to_pixels(dest_blocks.astype(np.float64), dots.shape, block_px) > 0.5

    # ---- placement: geometric only (largest remaining kernel gap), two spacing passes --
    eligible = foot & ~cat & (edt_cat > CLEARANCE_PX)
    # a destination-block census for the run card
    dest_dots_parent = int((dots & dest_px).sum())
    dist_kept = ndi.distance_transform_edt(~kept)
    cand_mask = eligible & dest_px & ~kept
    c_rows, c_cols = np.nonzero(cand_mask)
    gap = dist_kept[c_rows, c_cols]
    order_c = np.lexsort((c_cols, c_rows, -gap))

    out = kept.copy()
    placed: list[tuple[int, int]] = []
    half = int(np.ceil(MIN_SPACING_PX))
    n_at_parent_spacing = 0
    for spacing in (MIN_SPACING_PX, 2.0 + 1e-9):
        for i in order_c:
            if len(placed) >= n_drop:
                break
            r, c = int(c_rows[i]), int(c_cols[i])
            if out[r, c]:
                continue
            r0, r1 = max(0, r - half), min(out.shape[0], r + half + 1)
            c0, c1 = max(0, c - half), min(out.shape[1], c + half + 1)
            win = out[r0:r1, c0:c1]
            if win.any():
                rr, cc = np.nonzero(win)
                if np.hypot(rr + r0 - r, cc + c0 - c).min() < spacing:
                    continue
            out[r, c] = True
            placed.append((r, c))
            if spacing == MIN_SPACING_PX:
                n_at_parent_spacing += 1
        if len(placed) >= n_drop:
            break

    pr, pc = np.array(placed).T if placed else (np.array([]), np.array([]))
    # displacement is reported as a block-scale summary: distance from each placed cell to the
    # nearest dropped cell (order-free, unlike a pairing)
    from scipy.spatial import cKDTree
    if placed:
        tree = cKDTree(np.c_[rows[drop_sel_arr], cols[drop_sel_arr]])
        nearest_px = tree.query(np.c_[pr, pc], k=1)[0]
    else:                                              # pragma: no cover
        nearest_px = np.array([])

    changed = int((out != dots).sum())
    stats = {
        "axis": "CONCENTRATION", "value": value, "role": None,
        "block_size": f"{block_px * 100} m ({block_px}x{block_px} px)",
        "dose_target": dose, "moved_target": n_drop, "moved_placed": len(placed),
        "moved_shortfall": n_drop - len(placed),
        "placed_at_parent_spacing": n_at_parent_spacing,
        "placed_at_relaxed_spacing": len(placed) - n_at_parent_spacing,
        "source_sign": source_sign, "dest_sign": dest_sign,
        "source_rule": ("highest-prior occupied 1 km blocks first, every dot in a block before "
                        "the next" if source_sign > 0 else
                        "lowest-prior occupied 1 km blocks first, every dot in a block before "
                        "the next"),
        "dest_rule": ({1: "highest-prior fifth of the blocks that already hold a parent dot",
                       -1: "lowest-prior fifth of the blocks that already hold a parent dot",
                       0: f"random sample of the same occupied blocks (seed {seed})"}
                      [dest_sign]),
        "placement_rule": ("geometric only: largest remaining kernel gap to the nearest retained "
                           "dot, ties by (row, col); no response, band or probability term"),
        "dest_blocks": int(n_dest), "occupied_blocks": n_occ,
        "dest_dots_parent": dest_dots_parent,
        "n_dots_parent": int(dots.sum()), "n_dots_variant": int(out.sum()),
        "dots_changed": changed, "pct_changed": round(100.0 * changed / max(int(dots.sum()), 1), 3),
        "mean_disp_to_nearest_dropped_px": round(float(nearest_px.mean()), 3) if placed else None,
        "median_disp_to_nearest_dropped_px": round(float(np.median(nearest_px)), 3) if placed else None,
        "mean_disp_km": round(0.1 * float(nearest_px.mean()), 2) if placed else None,
        "block_density_parent": {k: v for k, v in
                                 variants.block_density(dots, foot, block_px).items() if k != "counts"},
        "block_density_variant": {k: v for k, v in
                                  variants.block_density(out, foot, block_px).items() if k != "counts"},
        "min_cat_edt_variant": round(float(edt_cat[out].min()), 4),
        "cat_edt_mean_parent": round(float(edt_cat[dots].mean()), 4),
        "cat_edt_mean_variant": round(float(edt_cat[out].mean()), 4),
        "prior": "catalogue-only: z-scored 3 x 3 km mean mapped-fault density per 1 km block",
    }
    return out, stats


def truth_models(foot: np.ndarray, cat: np.ndarray, seed: int = SEED) -> dict:
    """Five named truth models for a MODEL-class prediction (never a PROXY, never a score).

    Each is a *stated assumption* about where new-fault truth sits, not a label set.  The
    spread arm's sign across them is the quantity this session actually reports.
    """
    edt = ndi.distance_transform_edt(~cat)
    rng = np.random.default_rng(seed)
    m = {}
    m["annulus_2_4px"] = foot & (edt > 2) & (edt <= 4)
    m["annulus_3_8px"] = foot & (edt > 3) & (edt <= 8)
    far = foot & (edt > 12)
    m["uniform_far_0p8pct"] = far & (rng.random(foot.shape) < 0.008)
    m["uniform_all_0p8pct"] = foot & (rng.random(foot.shape) < 0.008)
    shifted = np.zeros_like(cat)
    src_rows, src_cols = np.nonzero(cat)
    rr, cc = src_rows, src_cols + 6                     # 600 m along a coordinate axis
    ok = (rr < cat.shape[0]) & (cc < cat.shape[1]) & foot[rr.clip(0, cat.shape[0] - 1),
                                                          cc.clip(0, cat.shape[1] - 1)]
    shifted[rr[ok], cc[ok]] = True
    m["catalogue_shift_6px"] = shifted
    return m


def score_models(mask: np.ndarray, models: dict, foot: np.ndarray, cat: np.ndarray) -> dict:
    out = {}
    for name, truth in models.items():
        r = metric.dti_binary(mask, truth, valid=foot, known=cat)
        out[name] = {"dti": round(float(r["dti"]), 6), "n_truth": int(r["n_truth"]),
                     "tp": round(float(r["tp"]), 2), "fp": round(float(r["fp"]), 2)}
    return out


def parent_diff(parent: np.ndarray, variant: np.ndarray, foot: np.ndarray) -> dict:
    return variants.parent_diff(parent, variant, foot)


def main() -> int:
    # Historical variant builders obey the same literal pre-placement stop.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="build and measure, write nothing")
    args = ap.parse_args()

    out_dir = ROOT / "releases" / "sign86"
    tmp = ROOT / "tmp_session"
    tmp.mkdir(exist_ok=True)
    pins = verify_inputs()
    print("[1/6] pins verified:", ", ".join(sorted(pins["files"])))

    ctx = grid_io.load_context()
    foot, cat = ctx["footprint"], ctx["catalogue"]
    r0 = rebuild_parent(foot, cat, tmp)
    print(f"[2/6] R0 rebuilt byte-exactly ({r0['rebuilt_dots']} dots, sha256 {r0['rebuild_sha256'][:8]}…)")

    prior = catalogue_prior(foot, cat)
    models = truth_models(foot, cat)
    print("[3/6] prior + truth models ready:", ", ".join(models))

    parent = grid_io.load_dots(PATHS["parent"], foot)
    base_scores = score_models(parent, models, foot, cat)
    known_sha = {r.get("sha256", "") for r in
                 __import__("csv").DictReader(open(ROOT / "ledger/submissions.csv"))}

    print("    parent DTI per truth model:",
          {k: v["dti"] for k, v in base_scores.items()})
    print("    truth pixels per model:", {k: v["n_truth"] for k, v in base_scores.items()})
    cards, rows = {}, []
    card_cv = {}
    for d in (0.05, 0.15, 0.30, 0.50):
        m_spr, _ = build_arm(parent, ctx, prior, f"cv{d}", +1, -1, d, SEED)
        m_den, _ = build_arm(parent, ctx, prior, f"cv{d}", -1, +1, d, SEED)
        card_cv[f"{d:.2f}"] = {
            "spr_cv": variants.block_density(m_spr, foot)["density_cv_occupied"],
            "dens_cv": variants.block_density(m_den, foot)["density_cv_occupied"]}
        print(f"    CV at dose {d:.2f}: parent 0.6235 spr {card_cv[f'{d:.2f}']['spr_cv']} "
              f"dens {card_cv[f'{d:.2f}']['dens_cv']}")
    for value, s_sign, d_sign, role in ARMS:
        mask, stats = build_arm(parent, ctx, prior, value, s_sign, d_sign, DOSE, SEED)
        stats["role"] = role
        if stats["moved_shortfall"]:
            raise SystemExit(f"{value}: placement shortfall {stats['moved_shortfall']}; count "
                             "would change - aborting (one change at a time)")
        diff = parent_diff(parent, mask, foot)
        pct = diff["pct_changed_of_parent"]
        if not (1.0 <= pct <= 50.0):
            raise SystemExit(f"{value}: {pct}% changed outside the brief's 1-50% band")
        scores = score_models(mask, models, foot, cat)
        deltas = {k: round(scores[k]["dti"] - base_scores[k]["dti"], 5) for k in models}
        stats["truth_models"] = {"note": ("MODEL class: exact DTI of each arm against a stated "
                                          "truth assumption, collar-masked; never a PROXY and "
                                          "never a score"),
                                 "parent": base_scores, "variant": scores, "delta": deltas}
        stem = f"gems86-h33-2b2-conc{value}-{DATE_TAG}-{dot8(mask)}"
        note = (f"R0 {value}: {'cluster-spread' if d_sign < 0 else 'cluster-dense' if d_sign > 0 else 'CONTROL random-block'}"
                f" 15pct of dots at 1km blocks, count 37654, {pct:.2f}pct changed")
        cards[value] = dict(id=stem, **stats, parent_diff=diff, note=note[:140],
                            note_chars=len(note[:140]))
        if args.dry_run:
            print(f"[dry-run] {stem} dots={stats['n_dots_variant']} changed={pct}% "
                  f"CV {stats['block_density_parent']['density_cv_occupied']} -> "
                  f"{stats['block_density_variant']['density_cv_occupied']} delta={deltas}")
            continue
        # write to a temporary stem, then rename to the repo convention
        # <parent>-<axis><value>-<yyyymmdd>-<sha8>, where sha8 is the *file* hash
        tmp_stem = stem[:-8] + "tmp"
        pair = grid_io.write_pair(mask, ctx, out_dir, tmp_stem, name=tmp_stem, note=note[:140])
        zeros_sha = pair["zeros"]["sha256"]
        final = stem[:-8] + zeros_sha[:8]
        moved = {}
        for kind, suffix in (("nan", ".tif"), ("zeros", "-zeros.tif")):
            src = out_dir / f"{tmp_stem}{suffix}"
            dst = out_dir / f"{final}{suffix}"
            src.replace(dst)
            moved[kind] = dst
        for leftover in out_dir.glob(f"{tmp_stem}*.receipt.json"):
            leftover.unlink()
        pair["nan"]["file"] = moved["nan"].name
        pair["zeros"]["file"] = moved["zeros"].name
        pair["nan"]["sha256"] = sha256(moved["nan"])
        pair["zeros"]["sha256"] = sha256(moved["zeros"])
        stem = final
        gate_nan = gates.run_all(moved["nan"], ctx, known_sha, clearance_px=2.0)
        gate_zeros = gates.run_all(moved["zeros"], ctx, known_sha, clearance_px=2.0)
        newmass = variants._cat_edt(cat)
        new = mask & ~parent
        new_mass = {"gate": "new_mass_clearance", "required_px": CLEARANCE_PX,
                    "n_new": int(new.sum()), "on_catalogue": int((new & cat).sum()),
                    "min_cat_distance_px": round(float(newmass[new].min()), 4) if new.any() else None,
                    "passed": bool((new & cat).sum() == 0 and (not new.any() or
                                                                  newmass[new].min() >= CLEARANCE_PX))}
        reread = grid_io.load_dots(moved["zeros"], foot)
        reread_ok = bool((reread == mask).all())
        passed = all(g["passed"] for g in (gate_nan, gate_zeros)) and new_mass["passed"] and reread_ok
        receipt = {"id": stem, "parent": "h33-h33-2-b2", "axis": "CONCENTRATION",
                   "value": value, "role": role, "n_dots": stats["n_dots_variant"],
                   "pct_changed": pct, "dot_digest": hashlib.sha256(
                       np.packbits(mask.ravel()).tobytes()).hexdigest(),
                   "nan": {**{k: v for k, v in pair["nan"].items() if k != "file"},
                           "file": moved["nan"].name},
                   "zeros": {**{k: v for k, v in pair["zeros"].items() if k != "file"},
                             "file": moved["zeros"].name},
                   "submission_name": stem, "note": note[:140], "note_chars": len(note[:140]),
                   "gates": {"nan": gate_nan, "zeros": gate_zeros, "new_mass": new_mass,
                             "re_read_from_disk_matches_mask": reread_ok},
                   "gates_passed": passed, "evidence_class": "MODEL",
                   "approved_for_weekly_slot": False, "submission_slots_used": 0}
        (out_dir / f"{stem}-zeros.tif.receipt.json").write_text(json.dumps(receipt, indent=2))
        (out_dir / f"{stem}.tif.receipt.json").write_text(json.dumps(receipt, indent=2))
        cards[value].update({"files": {"nan": moved["nan"].name, "zeros": moved["zeros"].name},
                             "sha256": {"nan": pair["nan"]["sha256"],
                                        "zeros": pair["zeros"]["sha256"]},
                             "gates": receipt["gates"], "gates_passed": passed})
        print(f"[4/6] {stem}: dots={stats['n_dots_variant']} changed={pct}% "
              f"CV {stats['block_density_parent']['density_cv_occupied']} -> "
              f"{stats['block_density_variant']['density_cv_occupied']} gates={passed} "
              f"sha8={pair['zeros']['sha256'][:8]}")
        rows.append(dict(
            site="GEMSDOE86", name=stem, score="", encoding="zeros",
            n_dots=str(stats["n_dots_variant"]), sha8=pair["zeros"]["sha256"][:8],
            parent="h33-h33-2-b2", receipt="N", id=stem, axis="CONCENTRATION",
            value=value, pct_changed=str(pct), sha256=pair["zeros"]["sha256"],
            status=("CONTROL" if role == "control" else "BUILT"),
            predicted_change="", receipt_score="", date="", evidence_class="MODEL",
            source_url=""))

    card = {"session": "concentration-sign", "date": "2026-10-23", "git_sha": git_sha(),
            "axis": "CONCENTRATION", "parent": "h33-h33-2-b2", "dose": DOSE,
            "block_px": BLOCK_PX, "seed": SEED, "inputs": pins, "r0_rebuild": r0,
            "prior": "catalogue-only (TMI term unavailable: feature stack absent)",
            "truth_models": {k: {"n_px": int(v.sum())} for k, v in models.items()},
            "cv_vs_dose": card_cv,
            "arms": cards,
            "slots_used": 0, "approved_for_weekly_slot": False,
            "evidence_class": "MODEL",
            "note": ("No arm here is a score.  The truth-model deltas are MODEL-class "
                     "projections under stated truth assumptions; the catalogue "
                     "hide-and-recover PROXY is at its floor for every R0-derived arm "
                     "(IR-86-SNAP-06) and is therefore not used to rank these files.")}
    if not args.dry_run:
        card_p = ROOT / "evidence" / "concentration_sign_20261023.json"
        card_p.write_text(json.dumps(card, indent=2))
        print(f"[5/6] run card -> {card_p.relative_to(ROOT)}")
        print("[6/6] ledger rows for the human (append after review):")
        for r in rows:
            print("  ", r["id"], r["sha8"], r["status"], r["pct_changed"])
        (tmp / "concentration_sign_rows.json").write_text(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
