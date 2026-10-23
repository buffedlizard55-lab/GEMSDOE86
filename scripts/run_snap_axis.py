#!/usr/bin/env python3
"""SNAP axis on R0 (GEMSDOE32 h33-h33-2-b2): move dots, change nothing else.

What this script does, in order

1. verifies the sha256 of every input against a committed pin before reading it;
2. re-derives R0 from the pinned base field and re-encodes it, requiring the
   published file's sha256 ``c55bafc4…b6fa9`` (dot set *and* bytes);
3. builds the edge-response surface from the two pinned gradient bands
   (``tmi_hg`` band 3, ``iso_grav_anom_hg`` band 18) -- rank-normalised over the
   scored footprint, so the two units never mix;
4. builds three SNAP variants that differ only in the search window and in which
   band carries the response, and nothing else: same dot count, same catalogue
   exclusion, unit mass, no dot created or deleted;
5. writes each candidate twice (spec-form NaN outside the footprint, and the
   all-finite zeros twin this repo ships), re-reads both from disk, runs the
   shared validator and the shared format report on the bytes, and writes the
   adjacent receipt;
6. reports the catalogue hide-and-recover PROXY with paired 95 % CIs -- report
   only, never a gate -- and the MODEL sensitivity bracket behind the prediction.

No truth raster is read. No network call, no portal, no submission, no login.

Usage
-----
    .venv/bin/python scripts/run_snap_axis.py [--out-dir releases] [--no-write]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "template66"))
sys.path.insert(0, str(ROOT))

import rasterio                                            # noqa: E402
from gems57 import grid as g57grid                       # noqa: E402
from gems57 import metric as g57metric                   # noqa: E402
from gems57.gates import format_report                   # noqa: E402
from gems57.validate import validate                     # noqa: E402
from src.gems86 import prune as P                        # noqa: E402
from src.gems86 import snap as S                         # noqa: E402

BRIDGE = ROOT / "data" / "bridge"
FLEET = ROOT / "data" / "scored_fleet"
RECEIPT = ROOT / "data" / "restore_receipt.json"
MANIFEST = ROOT / "registry" / "data_manifest.json"

PARENT_ID = "h33-h33-2-b2-20261004-e5eb6e7e"   # GEMSDOE32 h33-2-b2, the 0.2778 CLAIM row
PARENT_FILE = FLEET / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
PARENT_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
BASE_FILE = FLEET / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
BASE_SHA = "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"
STACK = BRIDGE / "training_features.tif"
STACK_SHA = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"

#: 1-based band numbers in the pinned stack, from its own band descriptions.
SNAP_BANDS = {"tmi_hg": 3, "iso_grav_anom_hg": 18}
R0_PRUNE_PX = 2.0          # the parent's own catalogue exclusion
SNAP_KEEP_CLEAR_PX = 2.0   # a landing cell must be no closer to the catalogue than that

#: Preregistered before any raster was written (``--no-write`` pass):
#: ``predicted`` is the MODEL midpoint of the bracket printed by
#: :func:`model_delta`; the band spans the two algebraic bracket ends at
#: q = 0.35 … 0.65, where q is the fraction of moves that are net towards truth.
#: That q is NOT measured by this script -- it is the hypothesis the slot buys.
VARIANTS = {
    "r1p000": dict(
        radius=1.0, weights={"tmi_hg": 0.5, "iso_grav_anom_hg": 0.5},
        tag="SNAP-r1p000", predicted=-0.004, band=[-0.012, 0.004],
        mechanism="one-pixel re-centring: the smallest move the grid allows, so the coverage "
                  "cost of convergence is also the smallest",
    ),
    "r2p000": dict(
        radius=2.0, weights={"tmi_hg": 0.5, "iso_grav_anom_hg": 0.5},
        tag="SNAP-r2p000", predicted=-0.006, band=[-0.020, 0.006],
        mechanism="two-pixel re-centring: the full positional uncertainty the GeoDAWN 400 m "
                  "line spacing implies (2 px off earns k=0.33, centred 1.0)",
    ),
    "r2p000-grav": dict(
        radius=2.0, weights={"tmi_hg": 0.0, "iso_grav_anom_hg": 1.0},
        tag="SNAP-r2p000-grav", predicted=-0.004, band=[-0.016, 0.006],
        mechanism="band decomposition of r2p000: gravity-only response. If magnetic relief is "
                  "what carries positional information, this arm loses r2p000's (hypothetical) gain",
    ),
}
#: Preregistered predictions
#: ------------------------
#: The three ``predicted``/``band`` pairs above were fixed after the ``--no-write``
#: instrumented pass and before any raster in this session was written.  That
#: pass found (a) 97-99 % of dots move even though the response is smooth
#: (lag-1 autocorrelation 0.978), and (b) a **null control** -- the same snap
#: driven by a random response -- scores the same proxy as the real response
#: (section ``diagnostics`` of evidence/snap_axis_20261023.json).  The
#: mechanism-derived optimistic bracket from :func:`model_delta` is kept and
#: reported, but the preregistered point is near zero because the instrument says
#: the local maxima of these two gradient bands are indistinguishable from a
#: random choice inside a 1-2 px window.
PROXY_DRAWS = 10
PROXY_SEED = 306


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path) -> np.ndarray:
    import rasterio
    with rasterio.open(path) as ds:
        if ds.count != 1:
            raise ValueError(f"{path.name}: expected one band, got {ds.count}")
        return ds.read(1)


def read_band(path: Path, index: int) -> np.ndarray:
    import rasterio
    with rasterio.open(path) as ds:
        return ds.read(index)


def serialization_profile(nodata) -> dict:
    """The encoder profile that reproduces the published parent BYTE for byte.

    ``deflate / predictor=3 / zlevel=9 / tiled 256`` on the catalogue's profile
    writes R0 as sha256 ``c55bafc4…`` (IR-86-LADDER-02). Reused unchanged.
    """
    import rasterio
    with rasterio.open(BRIDGE / "existing_faults.tif") as src:
        prof = src.profile.copy()
    prof.update(driver="GTiff", dtype="float32", count=1, compress="deflate",
                predictor=3, zlevel=9, tiled=True, blockxsize=256, blockysize=256,
                nodata=nodata)
    return prof


def write_with_profile(path: Path, arr: np.ndarray, nodata) -> str:
    import rasterio
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    with rasterio.open(path, "w", **serialization_profile(nodata)) as dst:
        dst.write(arr.astype(np.float32), 1)
    return sha256(path)


def verify_pins() -> dict:
    manifest = {f["dest"]: f["sha256"] for f in json.loads(MANIFEST.read_text())["files"]}
    receipt = {Path(f["dest"]).name: f["sha256"] for f in json.loads(RECEIPT.read_text())["files"]}
    checks = {}
    for key, path, pin_source, pin in (
        ("existing_faults.tif", BRIDGE / "existing_faults.tif", "registry/data_manifest.json",
         manifest["existing_faults.tif"]),
        ("sample_submission.tif", BRIDGE / "sample_submission.tif", "registry/data_manifest.json",
         manifest["sample_submission.tif"]),
        ("training_features.tif", STACK, "registry/data_manifest.json",
         manifest["training_features.tif"]),
        (PARENT_FILE.name, PARENT_FILE, "data/restore_receipt.json", receipt[PARENT_FILE.name]),
    ):
        actual = sha256(path)
        if actual != pin:
            raise SystemExit(f"PIN MISMATCH for {key}: {actual} != {pin} ({pin_source})")
        checks[key] = dict(sha256=actual, pin=pin, pin_source=pin_source,
                           path=str(path.relative_to(ROOT)))
    if checks["training_features.tif"]["sha256"] != STACK_SHA:
        raise SystemExit("feature stack pin is not the one this session measured")
    if checks[PARENT_FILE.name]["sha256"] != PARENT_SHA:
        raise SystemExit("the recorded parent pin is not the parent this brief names")
    base_actual = sha256(BASE_FILE)
    checks[BASE_FILE.name] = dict(
        sha256=base_actual, pin=BASE_SHA,
        pin_source="PINS in scripts/build_r0_prune.py + scripts/run_prune_ladder.py",
        path=str(BASE_FILE.relative_to(ROOT)), matches_expected=base_actual == BASE_SHA)
    if not checks[BASE_FILE.name]["matches_expected"]:
        raise SystemExit(f"base field mismatch: {base_actual}")
    return checks


def rebuild_parent(grid_ctx, base: np.ndarray) -> dict:
    """Re-derive R0's dot set from the parent field and prove dot set *and* bytes."""
    dist = P.catalogue_distance(grid_ctx.catalogue)
    parent_dots = read(PARENT_FILE) > 0
    rebuilt = P.prune_mask(base > 0, dist, R0_PRUNE_PX)
    diff = int((rebuilt != parent_dots).sum())
    probe = Path(tempfile.mkdtemp()) / "r0_rebuild.tif"
    rebuilt_field = np.where(grid_ctx.footprint, rebuilt.astype(np.float32), np.float32(0.0))
    rebuilt_sha = write_with_profile(probe, rebuilt_field, None)
    shutil.rmtree(probe.parent, ignore_errors=True)
    return dict(
        rule=f"delete dots at Euclidean distance <= {R0_PRUNE_PX} px from a mapped-fault cell",
        n_base_dots=int((base > 0).sum()), n_rebuilt=int(rebuilt.sum()),
        n_published=int(parent_dots.sum()), differing_pixels=diff,
        content_identical=diff == 0,
        dot_digest_rebuilt=P.dot_digest(rebuilt),
        dot_digest_published=P.dot_digest(parent_dots),
        rebuilt_sha256=rebuilt_sha, byte_identical_sha=rebuilt_sha == PARENT_SHA,
        published_sha256=PARENT_SHA,
    )


def model_delta(stats: dict, algebra: dict, dti_now: float) -> dict:
    """MODEL bracket for the live change of a SNAP variant.

    ``dD = alpha*(dT - dk)`` and ``DTI = T/D`` give, for one moved dot,

        dDTI = [dT - alpha*DTI*(dT - dk)] / D ,      D = T/DTI,

    with the two algebraic ends ``dT = 0`` (pure redundancy reduction, the small
    end) and ``dT = dk`` (the dot is the unique cover of the truth cells it
    gains, the large end).  ``dk = displacement/3`` only for a dot that was
    inside the kernel of some truth cell and moved *towards* it; a dot far from
    every truth cell contributes nothing.  Two parameters are therefore not
    measurable from this checkout: the fraction of moved dots that sit near any
    truth cell, and the fraction of those moves that go the right way.  Their
    product is the *hit rate* ``h``.  The bracket spans h = 0.10 … 0.40 and the
    midpoint uses h = 0.22; the slot is what measures ``h``.
    """
    dbar = float(stats["mean_displacement_px_moved"])
    n = int(stats["n_snapped"])
    dk = dbar / g57metric.RADIUS_PX
    D = algebra["tp"] / max(dti_now, 1e-12)
    alpha = g57metric.ALPHA
    lo = 0.10 * n * dk * alpha * dti_now / D
    mid = 0.22 * n * dk * 0.5 * (1.0 + alpha * dti_now) / D
    hi = 0.40 * n * dk / D
    return dict(
        algebra="dDTI = [dT - alpha*DTI*(dT-dk)]/D", alpha=alpha,
        mean_displacement_px=round(dbar, 4), n_snapped=n,
        dk_per_moved_dot=round(dk, 5), D_px=round(float(D), 2),
        D_source="catalogue-as-truth decomposition of the parent (assumption, not the live D)",
        hit_rate_h=[0.10, 0.40], midpoint_h=0.22,
        bracket=[round(lo, 4), round(hi, 4)], midpoint=round(mid, 4),
        evidence_class="MODEL",
        caution="the sign rests on h > 0.5 of the moves being net towards truth; "
                "the live slot is the only measurement of h",
    )


def diagnostics(default_response: np.ndarray, parent: np.ndarray, allowed: np.ndarray,
                dist: np.ndarray, catalogue: np.ndarray, footprint: np.ndarray,
                r0_proxy: float) -> dict:
    """The two instruments that decide whether this axis can carry information.

    * **lag-1 autocorrelation** of the response surface: is the "strongest edge
      in a 1-2 px window" a real ridge (phi -> 1) or pixel speckle (phi -> 0)?
    * **null control**: the identical snap driven by a *random* response over the
      same window and the same landing mask.  If the real response does not beat
      the null on the paired proxy, the local maxima carry no positional
      information at all and the live effect is the coverage cost alone.  The
      control is never a candidate and no raster is written for it.
    * **smoothing sweep** (proxy only, no raster): does a coherent response help
      where the raw one does not?
    """
    from scipy.ndimage import gaussian_filter

    def lag1(a):
        v = np.asarray(a, np.float64)
        v = v - np.nanmean(v)
        return round(float(np.nanmean(v[:, 1:] * v[:, :-1]) / np.nanvar(v)), 6)

    rng = np.random.default_rng(86)
    arms = {"NULL-random-r2": rng.random(parent.shape, dtype=np.float32)}
    for sigma in (1.0, 2.0):
        arms[f"smooth{sigma:g}-r2"] = gaussian_filter(default_response, sigma,
                                                      mode="nearest").astype(np.float32)
    out = {"lag1_autocorr_raw": lag1(default_response), "seed_null": 86, "arms": {}}
    for name, resp in arms.items():
        result = S.snap_dots(parent, resp, allowed, radius=2.0)
        stats = S.movement_stats(parent, result, resp, dist)
        out["arms"][name] = dict(
            pct_snapped=stats["pct_snapped"],
            mean_displacement_px=stats["mean_displacement_px_moved"],
            nn_distance_after_mean_px=stats["nn_distance_after_mean_px"],
            nn_lt_2px_after=stats["nn_lt_2px_after"],
            mean_response_gain_moved=stats["mean_response_gain_moved"],
            is_control=name.startswith("NULL"),
            writes_no_raster=True,
        )
        arms[name] = result.dots
    arms["R0"] = parent
    proxies = proxy_dti_paired(arms, catalogue, footprint)
    for name in list(out["arms"]):
        rec = proxies.get(name, {})
        out["arms"][name]["proxy_mean"] = rec.get("mean")
        out["arms"][name]["proxy_paired_delta_vs_R0"] = rec.get("paired_delta_vs_R0")
        out["arms"][name]["proxy_paired_ci95"] = rec.get("paired_ci95")
    out["verdict"] = ("no positional information detectable: every arm's paired proxy delta is "
                      "within +/-0.003 of the random control's"
                      if all(abs((out["arms"][n]["proxy_paired_delta_vs_R0"] or 0)
                                 - (out["arms"]["NULL-random-r2"]["proxy_paired_delta_vs_R0"] or 0)) < 0.003
                             for n in out["arms"]) else
                      "at least one arm separates from the random control")
    return out


def proxy_dti_paired(arms: dict[str, np.ndarray], catalogue: np.ndarray,
                     footprint: np.ndarray, *, n_draws: int = PROXY_DRAWS,
                     hide_frac: float = 0.2, seed: int = PROXY_SEED) -> dict:
    """Paired catalogue hide-and-recover PROXY. REPORT ONLY -- never a gate.

    The *same* hidden component sets are scored for every arm, so the comparison
    is paired and the CI is on the paired difference against R0.  The parent dot
    field was itself derived to avoid the catalogue, so the absolute value is
    near the floor (IR-86-PRUNE-03); only the sign of the paired difference is
    informative, and even that is sign-unstable against live scores.
    """
    from scipy.ndimage import label
    labels, n_comp = label(catalogue, structure=np.ones((3, 3)))
    if n_comp < 2:
        return dict(available=False, reason="catalogue has < 2 components")
    rng = np.random.default_rng(seed)
    take = max(1, int(round(hide_frac * n_comp)))
    draws: dict[str, list[float]] = {k: [] for k in arms}
    n_pos = []
    for _ in range(n_draws):
        comps = rng.permutation(n_comp) + 1
        hidden = np.isin(labels, comps[:take]) & footprint
        if hidden.sum() == 0:
            continue
        known = catalogue & ~hidden
        n_pos.append(int(hidden.sum()))
        for k, pred in arms.items():
            draws[k].append(float(g57metric.dti_exact(pred, hidden, valid=footprint, known=known)["dti"]))
        del hidden, known
    base = np.asarray(draws["R0"], np.float64)
    boots = np.random.default_rng(seed + 1)
    out = dict(available=True, class_="PROXY", n_draws=len(base),
               n_withheld_components=int(take), n_withheld_positive_pixels_mean=float(np.mean(n_pos)),
               hide_frac=hide_frac, seed=seed,
               contamination="catalogue-avoiding parent; absolute value is at the floor, use only the paired sign")
    for k, v in draws.items():
        arr = np.asarray(v, np.float64)
        d = arr - base
        boots_means = np.array([boots.choice(d, d.size, replace=True).mean() for _ in range(2000)])
        out[k] = dict(mean=round(float(arr.mean()), 6),
                      paired_delta_vs_R0=round(float(d.mean()), 6),
                      paired_ci95=[round(float(np.percentile(boots_means, 2.5)), 6),
                                   round(float(np.percentile(boots_means, 97.5)), 6)])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="releases")
    ap.add_argument("--no-write", action="store_true", help="measure only; write no raster")
    ap.add_argument("--stamp", default=None, help="YYYYMMDD used in the release name")
    args = ap.parse_args()
    t0 = time.time()

    print("[1/6] verifying pinned inputs", flush=True)
    pins = verify_pins()
    for name, rec in pins.items():
        print(f"      {name}: {'MATCH' if rec.get('pin') and rec['sha256'] == rec['pin'] else 'MEASURED-LOCAL'}",
              flush=True)

    g = g57grid.load_grid(BRIDGE)
    dist = P.catalogue_distance(g.catalogue)
    base = read(BASE_FILE)
    parent = read(PARENT_FILE) > 0

    print("[2/6] rebuilding the parent R0 (dot set and bytes)", flush=True)
    rebuild = rebuild_parent(g, base)
    if not rebuild["content_identical"]:
        raise SystemExit(f"parent rebuild mismatch: {rebuild['differing_pixels']} pixels differ")
    if not rebuild["byte_identical_sha"]:
        raise SystemExit(f"parent rebuild is not byte identical: {rebuild['rebuilt_sha256']}")
    del base
    print(f"      R0 = {rebuild['n_published']} dots; sha256 reproduced", flush=True)

    print("[3/6] building the SNAP response surface from the two pinned gradient bands", flush=True)
    valid = g.footprint & ~g.catalogue
    bands = {name: read_band(STACK, idx).astype(np.float32) for name, idx in SNAP_BANDS.items()}
    for name, arr in bands.items():
        print(f"      {name}: finite inside footprint "
              f"{100.0 * np.isfinite(arr[g.footprint]).mean():.2f}%", flush=True)
    allowed = g.footprint & ~g.catalogue & (dist > SNAP_KEEP_CLEAR_PX)
    if np.any(parent & ~allowed):
        raise SystemExit("a parent dot sits outside the landing mask; exclusions are not preserved")

    # The parent's own metric decomposition (catalogue as truth) feeds only the
    # MODEL bracket; it is not a score and not a gate.
    cat_eval = g57metric.dti_exact(parent.astype(np.float32), g.catalogue, valid=g.footprint)
    algebra = dict(tp=cat_eval["tp"], fp=cat_eval["fp"], fn=cat_eval["fn"],
                   n_truth=cat_eval["n_truth"], n_emitted=cat_eval["n_emitted"],
                   dti=cat_eval["dti"])
    print(f"      catalogue-as-truth decomposition: T={algebra['tp']:.1f} "
          f"K={algebra['n_truth']} DTI={algebra['dti']:.4f}", flush=True)

    counters: dict[str, dict] = {}
    arms: dict[str, np.ndarray] = {}
    for key, spec in VARIANTS.items():
        response = S.edge_response(bands, valid, spec["weights"]).astype(np.float32)
        result = S.snap_dots(parent, response, allowed, radius=spec["radius"])
        stats = S.movement_stats(parent, result, response, dist)
        stats["diff_vs_parent"] = S.move_diff(parent, result.dots, dist)
        model = model_delta(stats, algebra, algebra["dti"])
        arms[key] = result.dots
        counters[key] = dict(stats=stats, model=model, dots=result.dots)
        if key == "r2p000":
            default_response = response.copy()
        print(f"[4/6] {key}: snapped {stats['n_snapped']} dots "
              f"({stats['pct_snapped']}%), mean move {stats['mean_displacement_px_moved']} px; "
              f"MODEL {model['midpoint']:+.4f} [{model['bracket'][0]:+.4f},{model['bracket'][1]:+.4f}]",
              flush=True)
        del response

    arms["R0"] = parent
    print("[5/6] catalogue hide-and-recover PROXY (report only)", flush=True)
    proxy = proxy_dti_paired(arms, g.catalogue, g.footprint)
    for k in ("R0", *VARIANTS):
        rec = proxy.get(k, {})
        print(f"      {k}: {rec.get('mean')} paired {rec.get('paired_delta_vs_R0')} "
              f"{rec.get('paired_ci95')}", flush=True)

    print("      diagnostics: null control + smoothing sweep (no raster written)", flush=True)
    diags = diagnostics(default_response, parent, allowed, dist, g.catalogue, g.footprint,
                        proxy.get("R0", {}).get("mean", 0.0))
    print(f"      response lag-1 autocorr {diags['lag1_autocorr_raw']}; verdict: {diags['verdict']}",
          flush=True)
    for name, rec in diags["arms"].items():
        print(f"        {name}: paired {rec['proxy_paired_delta_vs_R0']} {rec['proxy_paired_ci95']}",
              flush=True)

    stamp = args.stamp or time.strftime("%Y%m%d")
    out_dir = ROOT / args.out_dir
    written, ledger_entries = [], []
    if not args.no_write:
        out_dir.mkdir(parents=True, exist_ok=True)
        # a re-run must not count its own previous output as a novelty collision
        for stale in list(out_dir.glob(f"{PARENT_ID}-SNAP-*")):
            stale.unlink()
        # sha256 -> the id that already owns it.  A re-run of *this* script owns
        # its own digests; any other owner is a novelty collision (brief §7).
        existing_shas: dict[str, str] = {}
        with open(ROOT / "ledger/submissions.csv", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("sha256"):
                    existing_shas[r["sha256"]] = r.get("id") or r.get("name") or "?"
        for d in (FLEET, ROOT / "docs" / "downloads", out_dir, out_dir / "refill"):
            if d.exists():
                for f in d.glob("*.tif"):
                    existing_shas.setdefault(sha256(f), f.stem)
        print(f"      novelty baseline: {len(existing_shas)} existing raster sha256", flush=True)

        for key, spec in VARIANTS.items():
            dots = counters[key]["dots"]
            stats = counters[key]["stats"]
            model = counters[key]["model"]
            pred = dots.astype(np.float32)
            zeros_arr = np.where(g.footprint, pred, np.float32(0.0)).astype(np.float32)
            probe_dir = Path(tempfile.mkdtemp())
            probe = probe_dir / "probe.tif"
            sha8 = write_with_profile(probe, zeros_arr, None)[:8]
            shutil.rmtree(probe_dir, ignore_errors=True)
            name = f"{PARENT_ID}-{spec['tag']}-{stamp}-{sha8}"
            note = (f"R0 h33-2-b2 (0.2778 CLAIM); SNAP <={spec['radius']:.0f}px "
                    f"{'+'.join(sorted(k for k, w in spec['weights'].items() if w))}; "
                    f"mean move {stats['mean_displacement_px_moved']:.2f}px; "
                    f"predicted {spec['predicted']:+.3f} (MODEL)")[:140]
            nan_path = out_dir / f"{name}.tif"
            zeros_path = out_dir / f"{name}-zeros.tif"
            for p in (nan_path, zeros_path, zeros_path.with_suffix(".json")):
                if p.exists():
                    p.unlink()
            nan_arr = np.where(g.footprint, pred, np.float32("nan")).astype(np.float32)
            nan_sha = write_with_profile(nan_path, nan_arr, float("nan"))
            v_all = validate(nan_path, g.footprint, g.catalogue)
            # the two checks that encode the repo's all-finite policy rather than the
            # public spec are reported separately (IR-86-PRUNE-07), everything else must pass
            policy_checks = ("no_nan_anywhere", "outside_footprint_zero")
            nan_checks = {k: bool(v) for k, v in v_all["checks"].items() if k not in policy_checks}
            with rasterio.open(nan_path) as _ds:
                _a = _ds.read(1)
            nan_checks["nan_exactly_outside_footprint"] = bool(
                np.isnan(_a[~g.footprint]).all() and np.isfinite(_a[g.footprint]).all())
            zeros_sha = write_with_profile(zeros_path, zeros_arr, None)
            if zeros_sha[:8] != sha8:
                raise SystemExit(f"{key}: probed sha8 {sha8} != written {zeros_sha[:8]}")
            v_zero = validate(zeros_path, g.footprint, g.catalogue)
            rep_zero = format_report(zeros_path, BRIDGE / "sample_submission.tif", footprint=g.footprint)
            if not v_zero["all_checks_passed"] or not rep_zero["ok"]:
                raise SystemExit(f"{key}: zeros twin failed the shared gates: {rep_zero['problems']}")
            if not all(nan_checks.values()):
                raise SystemExit(f"{key}: nan twin failed a spec check: "
                                 f"{[k for k, v in nan_checks.items() if not v]}")
            for digest, form in ((zeros_sha, "zeros"), (nan_sha, "nan")):
                owner = existing_shas.get(digest)
                if owner is not None and owner != name:
                    raise SystemExit(f"{key}: {form} sha256 already owned by {owner!r}")
            receipt = dict(
                id=name, parent="h33-h33-2-b2", axis="SNAP",
                value=f"<={spec['radius']:g}px " + ("iso_grav_anom_hg only" if spec["weights"]["tmi_hg"] == 0
                                                     else "tmi_hg+iso_grav_anom_hg"),
                role="candidate", radius_px=spec["radius"], weights=spec["weights"],
                rule=(f"each dot moves <= {spec['radius']} px to the strongest rank-normalised "
                      f"edge response in its window; count, mass and catalogue exclusion unchanged"),
                n_dots=int(dots.sum()), pct_changed=stats["pct_snapped"],
                dot_digest=P.dot_digest(dots), movement=stats,
                model=model, proxy={"class_": proxy.get("class_"),
                                    **{k: proxy.get(key, {}).get(k) for k in
                                       ("mean", "paired_delta_vs_R0", "paired_ci95")}},
                zeros=dict(file=zeros_path.name, sha256=zeros_sha, bytes=zeros_path.stat().st_size,
                           validator=v_zero, format_report_ok=rep_zero["ok"]),
                nan=dict(file=nan_path.name, mode="nan", sha256=nan_sha,
                         bytes=nan_path.stat().st_size,
                         in_footprint_checks_pass=all(nan_checks.values()),
                         excluded_policy_checks=list(policy_checks),
                         policy_note="NaN outside the footprint is the public spec; the repo's "
                                     "all-finite policy rejects it (IR-86-PRUNE-07)"),
                submission_name=name[:140], note=note,
                predicted_live_change=spec["predicted"], predicted_band=spec["band"],
                algebra_bracket=model["bracket"], algebra_midpoint=model["midpoint"],
                predicted_basis="MODEL judgement fixed before this raster was written; the "
                                "algebra bracket is the optimistic end and the null control "
                                "removed the reason to trust it",
                evidence_class="MODEL", approved_for_weekly_slot=False, submission_slots_used=0,
                provenance=dict(input_pins=pins, parent_rebuild=rebuild),
                generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            zeros_path.with_suffix(".json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
            written.append(receipt)
            ledger_entries.append(dict(
                id=name, parent="h33-h33-2-b2", axis="snap",
                value=f"{spec['radius']:g}" + ("-grav" if spec["weights"]["tmi_hg"] == 0 else ""),
                encoding="zeros", n_dots=int(dots.sum()),
                pct_changed=stats["pct_snapped"], sha256=nan_sha, sha8=sha8,
                sha256_zeros=zeros_sha, files=[str(nan_path.relative_to(ROOT)),
                                               str(zeros_path.relative_to(ROOT))],
                status="BUILT", diff=stats["diff_vs_parent"], movement=stats, model=model,
                predicted_change=(f"{spec['predicted']:+.3f} (MODEL; band {spec['band'][0]:+.3f}"
                                  f"..{spec['band'][1]:+.3f}; algebra bracket "
                                  f"{model['bracket'][0]:+.3f}..{model['bracket'][1]:+.3f}). "
                                  f"n={stats['n_snapped']} dots moved "
                                  f"{stats['mean_displacement_px_moved']:.2f} px mean; "
                                  f"nearest-neighbour {stats['nn_distance_before_mean_px']:.3f}->"
                                  f"{stats['nn_distance_after_mean_px']:.3f} px; dots closer than "
                                  f"2 px to a neighbour {stats['nn_lt_2px_before']}->"
                                  f"{stats['nn_lt_2px_after']}"),
                proxy=proxy.get(key), gate_all_pass=True,
            ))
            print(f"      wrote {zeros_path.name} ({zeros_path.stat().st_size} B)", flush=True)

        (ROOT / "ledger" / "variants_snap.json").write_text(
            json.dumps(ledger_entries, indent=2, allow_nan=False) + "\n")

    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        elapsed_seconds=round(time.time() - t0, 1),
        parent=dict(id=PARENT_ID, file=PARENT_FILE.name, sha256=PARENT_SHA,
                    n_dots=int(parent.sum()), dot_digest=P.dot_digest(parent)),
        axis="SNAP",
        axis_assignment=("UNASSIGNED BY HUMAN this session; SNAP chosen because SLOT_PLAN.md's "
                         "slot 2 pre-registered SNAP (with PRUNE declared crowded after three "
                         "sessions) and because its two bands restore from a verified pin"),
        input_pins=pins, parent_rebuild=rebuild,
        diagnostics=diags,
        response=dict(bands=SNAP_BANDS, stack_sha256=STACK_SHA,
                      transform="rank-normalise each band over footprint&~catalogue, then weighted mean",
                      weights={k: v["weights"] for k, v in VARIANTS.items()},
                      landing_mask=f"footprint & ~catalogue & catalogue_distance > {SNAP_KEEP_CLEAR_PX} px"),
        catalogue_as_truth_decomposition=algebra,
        variants={k: dict(spec={kk: vv for kk, vv in VARIANTS[k].items() if kk != 'weights'},
                          weights=VARIANTS[k]["weights"],
                          stats=counters[k]["stats"], model=counters[k]["model"],
                          proxy=proxy.get(k)) for k in VARIANTS},
        proxy=proxy,
        gates=dict(format="passed for every zeros twin (shared validator + shared format_report); "
                          "nan twin passes every check except the repo's all-finite policy",
                   zero_catalogue_mass="asserted in memory and on disk",
                   sha_novel="checked against every sha256 already in ledger/submissions.csv and on disk",
                   parent_diff="recorded per variant", reread_from_disk="yes"),
        not_a_score="Every number above is a MODEL projection or a PROXY measurement. No submission was made.",
    )
    (ROOT / "evidence").mkdir(exist_ok=True)
    out = ROOT / "evidence" / "snap_axis_20261023.json"
    out.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(f"[6/6] wrote {out.relative_to(ROOT)}; {len(written)} candidates packed; "
          f"{summary['elapsed_seconds']} s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
