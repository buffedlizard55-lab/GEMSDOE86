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

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import grid  # noqa: E402
from gems57.uniqueness import OVERLAP_LIMIT, RHO_LIMIT, _near, two_phase_summary  # noqa: E402
from scripts.check_h86e_registry import SCHEMA, build_index, index_identity, load_candidate, sha  # noqa: E402


def halo_coverage_array(support, allowed) -> float:
    """Expected forward overlap of a uniformly random dot set in ``allowed``."""
    return float(_near(np.asarray(support, bool))[np.asarray(allowed, bool)].mean())


def is_space_filling(coverage: float, limit: float = OVERLAP_LIMIT) -> bool:
    return bool(coverage > limit)


def halo_coverage(path: Path, footprint, allowed) -> float:
    with rasterio.open(path) as src:
        a = np.nan_to_num(src.read(1).astype(np.float32))
    return halo_coverage_array((a > 0) & footprint, allowed)


def validate_report_binding(report, candidate, g, index, missing, *, exclude=None):
    """Require a complete v2 audit of these exact bytes and indexed priors.

    Historical unbound reports are archives, not authorization evidence. Re-run
    check_h86e_registry.py to create bound evidence; do not retrofit old results.
    """
    if report.get("schema") != SCHEMA:
        raise ValueError("Unbound historical registry report; rerun the registry check")
    if report.get("mode") != "final_dots":
        raise ValueError("Chance-overlap check requires a final-dot report")
    if missing or not report.get("registry_complete_for_index"):
        raise ValueError("Incomplete registry cannot pass")
    summary = report.get("shared_summary", {})
    if not summary.get("complete_accessible_scan") or report.get("errors"):
        raise ValueError("Missing/invalid registry rows cannot pass")
    if report.get("registry_index_sha256") != index_identity(index):
        raise ValueError("Registry index changed since measurement")
    arr = load_candidate(candidate, g.footprint, surface=False)
    if report.get("candidate_source_sha256") != sha(Path(candidate)):
        raise ValueError("Candidate source hash mismatch")
    decoded = hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()
    if summary.get("candidate_decoded_sha256") != decoded:
        raise ValueError("Candidate decoded hash mismatch")
    if not summary.get("my_dots") or not summary.get("candidate_rank_variation"):
        raise ValueError("Empty/constant candidate cannot pass")
    rows = report.get("comparison_rows", [])
    expected = {r["sha256"] for r in index["rasters"]}
    if (not expected or len(rows) != len(expected)
            or {r.get("sha256") for r in rows} != expected
            or any("error" in r for r in rows)):
        raise ValueError("Registry comparison rows are incomplete")
    if report.get("registry_rasters_measured") != len(expected):
        raise ValueError("Registry measured count mismatch")
    # All inputs must still be the measured, pinned bytes, including non-firings.
    for record in index["rasters"]:
        if sha(Path(record["cache_file"])) != record["sha256"]:
            raise ValueError("Registry raster changed since measurement")
    if exclude is not None:
        own = [r for r in rows if r.get("submission") == exclude]
        if len(own) != 1 or own[0].get("decoded_sha256") != decoded:
            raise ValueError("Self exclusion must identify the exact decoded candidate")
    elif not summary.get("pixel_unique_among_checked"):
        raise ValueError("Pixel-identical registry candidate cannot pass")
    retained = [r for r in rows if r.get("submission") != exclude]
    if not retained:
        raise ValueError("No registry comparisons remain")
    # Derive all maxima again from ALL rows, not a truncated top-15 listing.
    return two_phase_summary(retained, int(g.footprint.sum()), expected_rasters=len(retained))


def main(argv):
    from scripts.audit_release import verify_shared_pins, write_json
    if not all(verify_shared_pins(ROOT).values()):
        raise ValueError("Shared tool SHA drift")
    report = json.loads(Path(argv[0]).read_text())
    g = grid.load_grid(ROOT / "data" / "bridge")
    fp = g.footprint
    allowed = fp & ~g.catalogue
    index, missing = build_index()
    exclude = argv[argv.index("--exclude-self") + 1] if "--exclude-self" in argv else None
    phase = validate_report_binding(report, argv[1], g, index, missing, exclude=exclude)
    path_by_source = {}
    for r in index["rasters"]:
        for source in r["sources"]:
            path_by_source[source] = Path(r["cache_file"])
    firings = [f for f in phase["literal_firings"] if f["submission"] != exclude]
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
    rho = phase["literal_reading"]["worst_spearman_full_footprint"]
    out = dict(amendment="PA-86-02", overlap_limit=OVERLAP_LIMIT, rho_limit=RHO_LIMIT,
               candidate=argv[1], candidate_source_sha256=report["candidate_source_sha256"],
               registry_report_sha256=sha(Path(argv[0])), registry_index_sha256=index_identity(index),
               registry_complete_for_index=True, submission_authorized=False,
               gate_scope="PA-86-02 diagnostic only; does not override literal protocol or authorize a slot",
               literal_gate_pass=bool(not phase["literal_reading"]["duplicate"]),
               excluded_self=exclude, firings=len(rows),
               space_filling_firings=sum(r["space_filling"] for r in rows),
               continuous_surface_firings=sum(r["representation"] != "dot_field" for r in rows),
               informative_firings=len(hard), informative_firing_rows=hard,
               worst_spearman_any_raster=rho,
               max_excess_over_chance=max((r["excess_over_chance"] for r in rows), default=None),
               gate_pass=bool(not hard and (rho is None or rho <= RHO_LIMIT)
                              and report["registry_rasters_measured"] > 0),
               rows=sorted(rows, key=lambda r: -r["excess_over_chance"]))
    write_json(Path(argv[2]), out)
    print(json.dumps({k: v for k, v in out.items() if k != "rows" and k != "informative_firing_rows"}, indent=1))
    for r in hard[:10]:
        print("INFORMATIVE FIRING", r)
    return 0 if out["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
