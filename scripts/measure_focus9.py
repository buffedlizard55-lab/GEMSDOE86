#!/usr/bin/env python3
"""Pixel-measure the 9 focus sites' best owner-reported submissions.

Read-only forensic measurement (session 5620a35f). Scores come from
registry/prior_scores.csv and remain OWNER-REPORTED (no organizer receipt).
Raster bytes come from the hash-pinned restored registry
(data/registry_ext/<sha256>.tif, scripts/restore_registry_inventory.py).
Dot overlap / Spearman use the shared vendor/gems57/uniqueness.py code.
"""
from __future__ import annotations
import csv, hashlib, json, sys
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import grid, uniqueness  # noqa

FOCUS = [
    ("GEMSDOE24", "989f59505db1", "h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan"),
    ("GEMSDOE25", "e56ea318af89", "dotted-h19-5-d2-8-20261002-e56ea318af89-nan"),
    ("GEMSDOE27", "5512495c6bd1", "topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan"),
    ("GEMSDOE28", "b531dae0a36f", "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan"),
    ("GEMSDOE30", "91eae1ca", "d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca"),
    ("GEMSDOE31", "8acb75e1", "h27-4-solo-d28-20261004-8acb75e1-nan"),
    ("GEMSDOE32", "e5eb6e7e", "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros"),
    ("GEMSDOE33", "cb490425926e", "h33d-analog-tip-stepover-r30-20261004-cb490425926e"),
    ("GEMSDOE36", "9b9ea4e6", "anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros"),
]
# Also measure GEMSDOE28's h27-4 parent explicitly: H33's forensic parent.
EXTRA = [("GEMSDOE28_PARENT", "8acb75e1f2cc", "h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan")]

def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def main() -> int:
    scores = {}
    with (ROOT / "registry/prior_scores.csv").open() as f:
        for r in csv.DictReader(f):
            scores[r["submission"]] = r
    inv = json.loads((ROOT / "research/upstream/registry_inventory.json").read_text())
    g = grid.load_grid(ROOT / "data/bridge")
    fp, cat = g.footprint, g.catalogue
    d_cat = ndi.distance_transform_edt(~cat)
    rows, primary = [], {}
    for site, token, stem in FOCUS + EXTRA:
        srow = scores.get(stem)
        hits = []
        for r in inv["rasters"]:
            srcs = [s for s in r["sources"] if token in s]
            # GEMSDOE31 token 8acb75e1 also matches GEMSDOE28 files; require site prefix there.
            if site in ("GEMSDOE31", "GEMSDOE28_PARENT"):
                want = "GEMSDOE31:" if site == "GEMSDOE31" else "GEMSDOE28:"
                srcs = [s for s in srcs if s.startswith(want)]
                if site == "GEMSDOE31":
                    srcs = [s for s in srcs if "h27-4-solo" in s]
            if srcs:
                hits.append((r, srcs))
        measured = []
        for r, srcs in hits:
            p = ROOT / "data/registry_ext" / f"{r['sha256']}.tif"
            if not p.is_file():
                measured.append({"sha256": r["sha256"], "sources": srcs, "status": "MISSING_LOCAL_BYTES"})
                continue
            if sha_file(p) != r["sha256"]:
                measured.append({"sha256": r["sha256"], "sources": srcs, "status": "SHA_MISMATCH"})
                continue
            with rasterio.open(p) as ds:
                grid_ok = (ds.shape, ds.crs, ds.transform, ds.count) == (g.shape, g.crs, g.transform, 1)
                a = ds.read(1).astype(np.float64)
            inside = a[fp]
            dots = np.isfinite(a) & (a > 0) & fp
            dd = d_cat[dots] if dots.any() else np.array([])
            decoded = np.where(fp, np.where(np.isfinite(a), a, 0.0), 0.0).astype(np.float32)
            m = dict(sha256=r["sha256"], sources=srcs, grid_match=bool(grid_ok),
                     bytes=p.stat().st_size,
                     decoded_inside_sha256=hashlib.sha256(np.ascontiguousarray(decoded).tobytes()).hexdigest(),
                     support_inside_sha256=hashlib.sha256(np.ascontiguousarray(dots).tobytes()).hexdigest(),
                     finite_inside=int(np.isfinite(inside).sum()), footprint_px=int(fp.sum()),
                     n_nan_inside=int(np.isnan(inside).sum()),
                     min_finite_inside=float(np.nanmin(inside)) if np.isfinite(inside).any() else None,
                     max_finite_inside=float(np.nanmax(inside)) if np.isfinite(inside).any() else None,
                     values_binary_inside=bool(np.all(np.isnan(inside) | (inside == 0) | (inside == 1))),
                     dots=int(dots.sum()), dots_on_catalogue=int((dots & cat).sum()),
                     frac_le_1px=float((dd <= 1).mean()) if dd.size else None,
                     frac_le_2px=float((dd <= 2).mean()) if dd.size else None,
                     frac_le_3px=float((dd <= 3).mean()) if dd.size else None,
                     frac_gt_10px_1km=float((dd > 10).mean()) if dd.size else None,
                     median_dist_cat_px=float(np.median(dd)) if dd.size else None,
                     outside_policy="nan" if np.isnan(a[~fp]).any() else ("zeros_or_finite" if np.isfinite(a[~fp]).all() else "mixed"))
            measured.append(m)
        ok = [m for m in measured if "dots" in m]
        if ok:
            def pref(m):
                s = " ".join(m["sources"])
                return (0 if "-zeros" in s else 1 if "allfinite" in s else 2 if "-nan" not in s and "nanoutside" not in s else 3, m["sha256"])
            prim = sorted(ok, key=pref)[0]
            primary[site] = prim
        rows.append(dict(site=site, prompt_submission=stem,
                         owner_reported_score=(float(srow["score"]) if srow else None),
                         evidence_class=(srow["evidence_class"] if srow else "NOT_IN_PRIOR_SCORES_CSV"),
                         source_url=(srow["source_url"] if srow else None),
                         registry_files_found=len(measured), files=measured,
                         distinct_support_sets=len({m.get("support_inside_sha256") for m in ok}),
                         primary_sha256=(primary[site]["sha256"] if site in primary else None)))
        print(site, stem, "->", [(m.get("sha256","")[:8], m.get("dots"), m.get("outside_policy")) for m in measured], flush=True)
    # Pairwise vs H33 primary, shared comparator (candidate = each primary, registry = [H33])
    h33p = ROOT / "data/registry_ext" / f"{primary['GEMSDOE32']['sha256']}.tif"
    with rasterio.open(h33p) as ds:
        h33 = np.where(np.isfinite(ds.read(1).astype(np.float32)), ds.read(1).astype(np.float32), 0)
    h33[~fp] = 0
    h33_dots = (h33 > 0) & fp
    for row in rows:
        pth = ROOT / "data/registry_ext" / f"{row['primary_sha256']}.tif"
        with rasterio.open(pth) as ds:
            a = ds.read(1).astype(np.float32)
        a = np.where(np.isfinite(a), a, 0.0); a[~fp] = 0
        dots = (a > 0) & fp
        row["vs_gemsdoe32_h33"] = dict(
            evidence_class="REGISTRY-MEASUREMENT",
            forward_overlap_3px_this_within_h33=uniqueness.dot_overlap(dots, h33_dots),
            forward_overlap_3px_h33_within_this=uniqueness.dot_overlap(h33_dots, dots),
            jaccard_dot_sets=uniqueness._jaccard(dots, h33_dots),
            spearman_full_footprint=uniqueness.surface_rho(a, h33, fp)["spearman_full_footprint"],
            containment_this_in_h33_exact=float((dots & h33_dots).sum() / max(int(dots.sum()), 1)),
            containment_h33_in_this_exact=float((dots & h33_dots).sum() / max(int(h33_dots.sum()), 1)),
            exact_differing_cells_inside=int((dots != h33_dots)[fp].sum()),
            h33_dots_minus_this=int((h33_dots & ~dots).sum()),
            this_dots_minus_h33=int((dots & ~h33_dots).sum()))
        print("vsH33", row["site"], row["vs_gemsdoe32_h33"], flush=True)
    out = dict(schema="gems86.focus9-forensics.v1", session="arena/5620a35f-gemsdoe86",
               measured_scope="Hash-pinned restored registry bytes (655-entry inventory) for the prompt's 9 focus sites' best owner-reported rows, plus GEMSDOE28 h27-4 parent. Scores stay OWNER-REPORTED.",
               evaluator_note="No DTI/HOLDOUT-DTI is computed here; this is support/encoding/lineage measurement only (REGISTRY-MEASUREMENT + FORMAT).",
               reference="GEMSDOE32 h33-h33-2-b2 zeros primary",
               sites=rows)
    dest = ROOT / "docs/evidence/focus9-forensics-20261026.json"
    dest.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print("wrote", dest)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
