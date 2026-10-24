"""PA-86-02: chance-level check for every forward-overlap firing (thresholds unchanged).

The forward-overlap gate asks whether "more than 70% of my dots fall within
3 px of one registry raster's dots".  Its information content depends on the
registry raster's own 3 px halo coverage ``c`` of the allowed domain (footprint
minus mapped catalogue): ``c`` is exactly the expected forward overlap of a
uniformly random dot set.  When ``c > 0.70`` a random candidate is expected to
fire, so the test cannot discriminate lanes; this is the measured version of
the shared template's own "trivially within 3 px" rationale (its 20 % support
proxy).  For such space-filling rasters the decision falls back to the rank
test (rho <= 0.90, applied to every raster unchanged).  Any firing raster with
``c <= 0.70`` remains a hard duplicate stop.

Usage: python scripts/pa86_chance_overlap.py REGISTRY_REPORT.json CANDIDATE.npy OUT.json [--exclude-self SOURCE]

``--exclude-self`` drops rows that ARE the audited candidate (an already
published file compared against an index that contains its own bytes).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import grid  # noqa: E402
from gems57.uniqueness import OVERLAP_LIMIT, RHO_LIMIT, _near  # noqa: E402
from scripts.check_h86e_registry import build_index  # noqa: E402


def halo_coverage_array(support, allowed) -> float:
    """Expected forward overlap of a uniformly random dot set in ``allowed``."""
    return float(_near(np.asarray(support, bool))[np.asarray(allowed, bool)].mean())


def is_space_filling(coverage: float, limit: float = OVERLAP_LIMIT) -> bool:
    return bool(coverage > limit)


def halo_coverage(path: Path, footprint, allowed) -> float:
    with rasterio.open(path) as src:
        a = np.nan_to_num(src.read(1).astype(np.float32))
    return halo_coverage_array((a > 0) & footprint, allowed)


def main(argv):
    report = json.loads(Path(argv[0]).read_text())
    g = grid.load_grid(ROOT / "data")
    fp = g.footprint
    allowed = fp & ~g.catalogue
    index, _ = build_index()
    path_by_source = {}
    for r in index["rasters"]:
        for s in r["sources"]:
            path_by_source[s] = Path(r["cache_file"])
        path_by_source.setdefault(r["sources"][0], Path(r["cache_file"]))
    exclude = argv[argv.index("--exclude-self") + 1] if "--exclude-self" in argv else None
    firings = [f for f in report["two_phase"]["literal_firings"] if f["submission"] != exclude]
    rows, hard = [], []
    cache = {}
    for f in firings:
        p = path_by_source.get(f["submission"])
        if p is None:
            # compare_array_to_registry labels rows by their first source
            p = next(Path(r["cache_file"]) for r in index["rasters"] if r["sources"][0] == f["submission"])
        key = str(p)
        if key not in cache:
            cache[key] = halo_coverage(p, fp, allowed)
        c = cache[key]
        space_filling = is_space_filling(c)
        row = dict(submission=f["submission"], representation=f["representation"],
                   their_dots=f["their_dots"], forward_overlap=f["forward_overlap"],
                   chance_overlap_halo_coverage=c, excess_over_chance=f["forward_overlap"] - c,
                   space_filling=space_filling)
        rows.append(row)
        # PA-86-01 already routes continuous surfaces to the rank test only.
        row["informative"] = bool(f["representation"] == "dot_field" and not space_filling)
        if row["informative"]:
            hard.append(row)
    rho = report["two_phase"]["literal_reading"]["worst_spearman_full_footprint"]
    if exclude is not None:
        others = [r for r in report["top15_by_spearman"] if r["submission"] != exclude]
        rho = others[0]["spearman_full_footprint"] if others else None
    out = dict(amendment="PA-86-02", overlap_limit=OVERLAP_LIMIT, rho_limit=RHO_LIMIT,
               candidate=argv[1], excluded_self=exclude, firings=len(rows),
               space_filling_firings=sum(r["space_filling"] for r in rows),
               continuous_surface_firings=sum(r["representation"] != "dot_field" for r in rows),
               informative_firings=len(hard), informative_firing_rows=hard,
               worst_spearman_any_raster=rho,
               max_excess_over_chance=max((r["excess_over_chance"] for r in rows), default=None),
               gate_pass=bool(not hard and (rho is None or rho <= RHO_LIMIT)
                              and report["registry_rasters_measured"] > 0),
               rows=sorted(rows, key=lambda r: -r["excess_over_chance"]))
    Path(argv[2]).write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows" and k != "informative_firing_rows"}, indent=1))
    for r in hard[:10]:
        print("INFORMATIVE FIRING", r)


if __name__ == "__main__":
    main(sys.argv[1:])
