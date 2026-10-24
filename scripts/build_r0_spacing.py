#!/usr/bin/env python3
"""GEMSDOE86 session, AXIS = SPACING. Rebuild R0, then relocate its redundant mass three ways.

What runs here
--------------
1. **Pins first.** Every input is checked against a SHA-256 pin before it is read (brief 4.2).
2. **Parent rebuild.** R0 is re-derived from the pinned base ``gems28-h27-4-r1-solo-d2-8`` by
   deleting every dot within 2.0 px of the catalogue, re-encoded with the documented TIFF
   settings, and required to reproduce ``c55bafc4…b6fa9`` **byte for byte**.  If that fails this
   script stops; nothing is approximated (brief 5).
3. **Three arms, one axis.** Selection of *which* dots move is shared (every dot owning ≤ 16 of
   the 29 cells of its kernel disc = 19.20 % of R0, so 38.39 % of its cells change and the count
   stays 37,654).  Only the admissible *shape* differs: isotropic gap (``pdisk``), hexagonal
   covering nodes (``lattice``), on-trace only (``strike``).  A fourth build, ``random``, is the
   null control and is never a slot candidate.
4. **Gates** (brief 6) run against the written file, re-read from disk, in both encodings.
5. **Report-only instruments** (brief 6): catalogue hide-and-recover PROXY, the SGMC off-catalogue
   surrogate with a quadrant split and a translation ensemble, a leakage canary, and the
   parent's own support-surface read.  None of these is a score and none can authorise a slot.

Nothing here logs in, scrapes a leaderboard, submits, or contacts DrivenData or dropbox.
No shared validator, gate or writer is modified; the axis lives in ``src/gems86/spacing.py``.

Usage::

    .venv/bin/python scripts/build_r0_spacing.py                 # full session
    .venv/bin/python scripts/build_r0_spacing.py --no-proxy      # skip the hide-and-recover draw
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "vendor", ROOT / "vendor" / "template66"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gems57 import metric  # noqa: E402
from gems86 import spacing as SP  # noqa: E402
from gems86_axis import gates, grid_io  # noqa: E402
from gems86_axis.grid_io import dot8  # noqa: E402

SESSION = "spacing"
DATE_TAG = "20261023"
SEED = 20261023
R0_ID = "h33-2b2"
PARENT_LABEL = "h33-h33-2-b2"
AXIS = "SPACING"
CREDIT_MAX = 16            # exclusive disc cells; 29 = an untouched disc. Dose = 19.20 % relocated
WINDOW_PX = 8              # 800 m: local re-arrangement only, never a regional move
FLOOR_PX = SP.R_PX         # hard core raised to the kernel radius for all three arms
CLEARANCE_PX = 3.0          # brief 4.4, applied to newly emitted mass (IR-86-RELIEF-02)
ARMS = ("pdisk", "lattice", "strike")
CONTROL = "random"

PATHS = {
    "sample": ROOT / "data/bridge/sample_submission.tif",
    "catalogue": ROOT / "data/bridge/existing_faults.tif",
    "parent": ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "base": ROOT / "data/scored_fleet/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
    "sgmc": ROOT / ".cache/gems_data/external/derived_sgmc_faults_100m_u8.tif",
    "h19": ROOT / ".cache/gems_data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
}
#: registry/data_manifest.json ids for the inputs that are pinned there (verified, not assumed).
MANIFEST_IDS = {"parent": "scored_h33_2_b2_zeros", "catalogue": "existing_faults",
                "sample": "sample_submission", "sgmc": "ext_derived_sgmc_faults_100m_u8",
                "h19": "scored_h19_5"}
#: The in-tree parent/base pair: the parent's bytes are the published GEMSDOE32 file and the base
#: is pinned in registry/upstream_registry_index.json; the rebuild below is the real check.
LITERAL_PINS = {
    "parent": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "base": "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
}
ENCODING_RULE = (
    "SPACING arm: every R0 dot owning <= 16 of the 29 cells of its radius-3 px kernel disc (mass "
    "the metric's max-operator has already written off) is relocated to the largest local gap to "
    "the nearest retained dot inside an 800 m window, under one of three admissible-shape laws "
    "(isotropic / hexagonal covering lattice / on-trace only); count fixed at 37,654, no band, "
    "label or probability field enters a placement")


def sha256(path: Path) -> str:
    with path.open("rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              check=True).stdout.decode().strip()
    except Exception:                                     # pragma: no cover
        return "unknown"


def manifest_pin(manifest_id: str) -> dict:
    man = json.loads((ROOT / "registry/data_manifest.json").read_text())
    return {f["id"]: f for f in man["files"]}[manifest_id]


def verify_inputs() -> dict:
    """Hash every input before it is read; abort on a mismatch (brief 4.2)."""
    files, missing = {}, []
    for name, path in PATHS.items():
        if not path.is_file():
            missing.append(f"{name}: {path.relative_to(ROOT)}")
            continue
        got = sha256(path)
        expected = LITERAL_PINS.get(name)
        if expected is None and name in MANIFEST_IDS:
            expected = manifest_pin(MANIFEST_IDS[name])["sha256"]
        if expected and got != expected:
            raise SystemExit(f"PIN MISMATCH {name}: {got} != {expected}")
        entry = {"path": str(path.relative_to(ROOT)), "sha256": got, "bytes": path.stat().st_size,
                 "pin_source": ("registry/upstream_registry_index.json" if name == "base" else
                                "registry/data_manifest.json" if name in MANIFEST_IDS else
                                "committed in tree (git blob identity)"),
                 "verified": bool(expected), "organizer_authenticated": False}
        files[name] = entry
    if missing:
        raise SystemExit("pinned input(s) absent - restore them with scripts/restore_axis_inputs.py "
                         "and re-run; nothing is approximated:\n  " + "\n  ".join(missing))
    shared = json.loads((ROOT / "research/template_pin.json").read_text())
    for rel, expected in shared["files"].items():
        path = ROOT / rel
        if not path.is_file() or sha256(path) != expected:
            raise SystemExit(f"shared-tool pin mismatch: {rel}")
    return {"files": files, "shared_template_pins_verified": True,
            "pin_file": "research/template_pin.json",
            "note": ("GitHub mirrors are integrity-pinned, NOT organizer-authenticated; the "
                     "competition data tab and dropbox.com are never contacted (brief 4.1)")}


def read(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(1)


def rebuild_parent(foot: np.ndarray, cat: np.ndarray) -> dict:
    """Re-derive R0 from the pinned base and prove it byte-for-byte, or stop the session."""
    base = read(PATHS["base"])
    bm = (np.nan_to_num(base, nan=0.0) > 0) & foot
    rebuilt = bm & (ndi.distance_transform_edt(~cat) > 2.0)
    parent = grid_io.load_dots(PATHS["parent"], foot)
    differing = int((rebuilt != parent).sum())
    if differing:
        raise SystemExit(f"R0 REBUILD MISMATCH: {differing} cells differ; stopping (brief 5)")
    # byte-exact re-encode with the documented writer settings
    with rasterio.open(PATHS["parent"]) as src:
        crs, transform = src.crs, src.transform
    out = ROOT / "tmp_session/rebuild_parent_zeros.tif"
    out.parent.mkdir(exist_ok=True)
    prof = dict(driver="GTiff", dtype="float32", count=1, compress="deflate", predictor=3,
                zlevel=9, tiled=True, blockxsize=256, blockysize=256, interleave="band",
                nodata=None, height=foot.shape[0], width=foot.shape[1], crs=crs,
                transform=transform)
    with rasterio.open(out, "w", **prof) as dst:
        dst.write(np.where(foot, rebuilt, 0.0).astype(np.float32), 1)
    digest = sha256(out)
    if digest != LITERAL_PINS["parent"]:
        raise SystemExit(f"R0 REBUILD NOT BYTE-EXACT: {digest} != {LITERAL_PINS['parent']}"
                         " (brief 5: never approximate the parent)")
    return {"base_dots": int(bm.sum()), "rebuilt_dots": int(rebuilt.sum()),
            "parent_dots": int(parent.sum()), "differing_cells_vs_parent": differing,
            "rebuild_sha256": digest, "byte_exact": True,
            "recipe": "gems28-h27-4-r1-solo-d2-8 (40,199 dots) AND distance-to-catalogue > 2.0 px",
            "reencode": "deflate, predictor=3, zlevel=9, tiled 256, interleave=band, float32, no nodata"}


def new_mass_gate(mask: np.ndarray, parent: np.ndarray, cat: np.ndarray, foot: np.ndarray,
                  clearance_px: float) -> dict:
    """Brief 4.4 for the mass this session emits: zero on catalogue, >= 3 px off it."""
    edt = ndi.distance_transform_edt(~cat)
    new = mask & ~parent
    return {"gate": "new_mass_clearance", "passed": bool((new & cat).sum() == 0
            and (edt[new] > clearance_px - 1e-9).all() if new.any() else (new & cat).sum() == 0),
            "n_new": int(new.sum()), "on_catalogue": int((new & cat).sum()),
            "min_cat_distance_px": round(float(edt[new].min()), 4) if new.any() else None,
            "required_px": clearance_px,
            "note": ("inherited dots keep the parent's own geometry (R0 has 2,171 dots between 2 "
                     "and 3 px of the catalogue), which brief 4.4 and R0 cannot both satisfy - "
                     "IR-86-RELIEF-02, IR-86-SNAP-08")}


def surrogate_scores(mask: np.ndarray, truth: np.ndarray, foot: np.ndarray,
                     cat: np.ndarray) -> dict:
    r = metric.dti_binary(mask, truth, valid=foot, known=cat)
    return {k: (round(float(r[k]), 6) if k in ("dti", "coverage") else float(r[k]))
            for k in ("dti", "tp", "fp", "fn", "coverage", "n_truth", "n_emitted")}


def quadrants(shape: tuple[int, int]) -> np.ndarray:
    lab = np.zeros(shape, np.int32)
    h, w = shape
    lab[:h // 2, :w // 2] = 1
    lab[:h // 2, w // 2:] = 2
    lab[h // 2:, :w // 2] = 3
    lab[h // 2:, w // 2:] = 4
    return lab


def sgmc_instrument(parent: np.ndarray, arms: dict[str, np.ndarray], foot: np.ndarray,
                    cat: np.ndarray) -> dict:
    """Exact DTI of every arm against an independent off-catalogue fault map (MODEL).

    Conventions are the ones the RELIEF session used, so the axes stay comparable: truth = SGMC
    derived fault pixels inside the footprint, outside the catalogue; ``known=catalogue`` so the
    organiser-masked pixels cannot be credited; the number written into the ledger as the
    "predicted live change" is the surrogate delta itself, as in RELIEF.  Two extra reads are
    added here because this axis lives entirely at the 300 m scale: a quadrant split (sign
    stability) and a translation ensemble (the ~lineament-position uncertainty in brief 2).
    """
    sgmc = read(PATHS["sgmc"]) > 0
    off = sgmc & foot & ~cat
    q = quadrants(foot.shape)
    out = {"evidence_class": "MODEL",
           "instrument": ("official-kernel DTI (gems57.metric.dti_binary, alpha 0.2 beta 0.8 "
                          "R=3 px) vs USGS SGMC derived off-catalogue faults, catalogue masked "
                          "as known; RELIEF-session convention"),
           "source_url": "https://www.usgs.gov/science-plan/conterminus-synthetic-geologic-map-compiler-sgmc",
           "truth_pixels": int(off.sum()), "arms": {}}
    base_all = surrogate_scores(parent, off, foot, cat)
    out["parent"] = base_all
    rng = np.random.default_rng(SEED)
    shifts = [(0, 0)] + [tuple(int(v) for v in rng.integers(-6, 7, 2)) for _ in range(11)]
    for name, mask in list(arms.items()) + [("control_random", arms[CONTROL])]:
        child = surrogate_scores(mask, off, foot, cat)
        delta = child["dti"] - base_all["dti"]
        per_q = {}
        for i in (1, 2, 3, 4):
            reg = foot & (q == i)
            p = surrogate_scores(parent, off & reg, reg, cat)["dti"]
            c = surrogate_scores(mask, off & reg, reg, cat)["dti"]
            per_q[f"q{i}"] = round(c - p, 6)
        trans = []
        for dy, dx in shifts:
            t = np.roll(np.roll(off, dy, axis=0), dx, axis=1)
            trans.append(round(surrogate_scores(mask, t, foot, cat)["dti"]
                               - surrogate_scores(parent, t, foot, cat)["dti"], 6))
        out["arms"][name] = {
            "dti": child["dti"], "delta": round(delta, 6),
            "relative_pct": round(100.0 * delta / base_all["dti"], 3) if base_all["dti"] else None,
            "delta_tp": round(child["tp"] - base_all["tp"], 2),
            "delta_fp": round(child["fp"] - base_all["fp"], 2),
            "coverage": child["coverage"], "coverage_parent": base_all["coverage"],
            "quadrant_delta_px": per_q,
            "quadrant_sign_agreement": sum(1 for v in per_q.values() if v > 0),
            "translated_delta_px": trans,
            "translated_mean": round(float(np.mean(trans)), 6),
            "translated_min": round(float(np.min(trans)), 6),
            "translated_max": round(float(np.max(trans)), 6),
            "translated_positive_draws": int(sum(1 for v in trans if v > 0)),
            "translated_shifts_px": [list(s) for s in shifts],
        }
    out["reads"] = {
        "law_separation": ("the widest gap between the three laws on this surrogate is "
                           f"{max(abs(out['arms'][a]['delta'] - out['arms'][b]['delta']) for a in ARMS for b in ARMS):.6f} "
                           "DTI, i.e. the surrogate cannot rank the laws"),
        "control_separation": ("the random control is reported so that any gain shared with it "
                               "is read as 'moving mass out of overlap pays', not as 'this law pays'"),
    }
    return out


def hide_recover(parent: np.ndarray, arms: dict[str, np.ndarray]) -> dict:
    """Catalogue hide-and-recover PROXY, rebuilt fold-fair for every arm (report only).

    A fold-fair build re-runs the *placement* under each fold's visible catalogue, so an arm is
    not scored against faults it was allowed to see.  Expected to sit at the floor for this
    lineage (IR-86-PRUNE-03, IR-86-SNAP-06); reported anyway and never used as a gate.
    """
    from gems57 import evaluate_holdout, holdout as holdout_mod
    from gems86 import instrument

    cat = grid_io.load_context()["catalogue"]
    foot = grid_io.load_context()["footprint"]
    folds = instrument.build(foot, cat, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    names = list(ARMS) + ["parent"]
    terms = {n: [] for n in names}
    fold_rows = []
    for fold in folds:                                   # gems86.instrument.Fold, attribute access
        visible = fold.visible
        region = foot & fold.region
        vctx = {"footprint": region, "catalogue": visible & region}
        for n in ARMS:
            mask, _st = SP.relocate(parent, vctx, n, CREDIT_MAX, window_px=WINDOW_PX,
                                    floor_px=FLOOR_PX, clearance_px=CLEARANCE_PX, seed=SEED)
            _res, block = evaluate_holdout.evaluate(mask.astype(np.float32), fold.fold, region,
                                                     block_side=200, origin=(0, 0),
                                                     global_shape=foot.shape)
            terms[n].append(block)
        _res, block = evaluate_holdout.evaluate(parent.astype(np.float32), fold.fold, region,
                                                 block_side=200, origin=(0, 0),
                                                 global_shape=foot.shape)
        terms["parent"].append(block)
        fold_rows.append({"fold": fold.name, "withheld_truth_px": int((fold.truth & region).sum())})
    pooled = {n: np.sum(np.stack(v), axis=0) for n, v in terms.items()}
    summary = evaluate_holdout.pooled_summary(pooled, draws=1000, seed=SEED, candidate=ARMS[0])
    return {"evidence_class": "PROXY", "status": "REPORT-ONLY (never a gate)",
            "design": ("fold-fair buffered whole-component catalogue hide-and-recover; seed 20, "
                       "20 % withheld, 3 px context buffer; each arm's placement re-run per fold "
                       "on that fold's visible catalogue"),
            "folds": fold_rows,
            "scores": {n: {k: summary["scores"][n][k] for k in
                           ("dti", "ci95", "withheld_positive_pixels")} for n in names},
            "caveat": ("measured floor for a catalogue-avoiding lineage (R0 0.00436, pruned "
                       "variants 0.00000 in IR-86-PRUNE-03); with the >= 3 px collar every arm "
                       "here is far from the withheld trace, so near-zero values are the expected "
                       "reading of this instrument and not evidence against the axis")}


def support_read(parent: np.ndarray, arms: dict[str, np.ndarray]) -> dict:
    """How much of the relocated mass still lands on the lineage's own support surface.

    A SPACING arm that moves mass off the H19-5 support is no longer 'the same field, re-arranged';
    it is new, unrated mass.  Reported for every arm because it is the axis's main confound.
    """
    with rasterio.open(PATHS["h19"]) as src:
        h19 = src.read(1)
    support = (np.nan_to_num(h19, nan=0.0) > 0)
    out = {"support_surface": "gems19-h19-5 (pinned, the field the lineage was thinned from)",
           "support_cells": int(support.sum()), "arms": {}}
    for name, mask in arms.items():
        added = mask & ~parent
        dropped = parent & ~mask
        out["arms"][name] = {
            "sources_on_support_pct": round(100.0 * float(support[dropped].mean()), 3) if dropped.any() else None,
            "destinations_on_support_pct": round(100.0 * float(support[added].mean()), 3) if added.any() else None,
            "destination_field_value_mean": round(float(np.nan_to_num(h19)[added].mean()), 6) if added.any() else None,
            "parent_field_value_mean": round(float(np.nan_to_num(h19)[parent].mean()), 6),
        }
    return out


def canary(parent: np.ndarray, arms: dict[str, np.ndarray], foot: np.ndarray,
           cat: np.ndarray) -> dict:
    """Leakage canary: a single geometric feature must not predict a label with AUC > 0.90.

    The features are this axis's own decision variables - the gap to the nearest retained dot and
    the parent's H19-5 value - and the label is the independent SGMC off-catalogue truth.  A high
    AUC here would mean the placement rule is reading truth rather than geometry.
    """
    from sklearn.metrics import roc_auc_score

    sgmc = read(PATHS["sgmc"]) > 0
    truth = sgmc & foot & ~cat
    rows = []
    for name, mask in arms.items():
        gap = ndi.distance_transform_edt(~mask)
        for feat, surface in (("gap_to_nearest_dot", -gap),
                              ("is_destination_of_a_moved_dot", (mask & ~parent).astype(float))):
            vals = surface[foot & ~cat]
            lab = truth[foot & ~cat]
            if lab.sum() == 0 or np.unique(vals).size < 2:
                continue
            rows.append({"arm": name, "feature": feat,
                         "auc": round(float(roc_auc_score(lab, vals)), 4)})
    mx = max((r["auc"] for r in rows), default=0.0)
    return {"status": "PASS" if mx <= 0.90 else "STOP_INVESTIGATE", "threshold": 0.90,
            "max_auc": mx, "rows": rows,
            "note": ("label used: USGS SGMC off-catalogue faults, an independent map product, not "
                     "competition truth; no label enters any placement")}


def known_hashes() -> set[str]:
    """Digests that would make a build a repeat: the ledger, plus the delivered parents.

    Deliberately NOT a scan of ``releases/``: this session re-ran its own builder and the second
    pass aborted on the ``sha256_not_in_ledger`` gate because it collided with its *own* first-run
    bytes.  A deterministic rebuild of the same ``(parent, axis, value)`` is a re-derivation, not a
    duplicate submission, and the ledger (which records every built release) is the authority the
    brief names.
    """
    out: set[str] = set()
    led = ROOT / "ledger/submissions.csv"
    if led.is_file():
        with led.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                for col in ("sha256", "sha256_nan", "sha256_zeros"):
                    v = (row.get(col) or "").strip()
                    if len(v) == 64:
                        out.add(v)
    for f in (ROOT / "data/scored_fleet").glob("*.tif"):
        out.add(sha256(f))
    return out


def note_for(stem: str, st: dict, diff: dict) -> str:
    note = (f"{PARENT_LABEL} SPACING/{st['law']}: relocate {st['moved_placed']} redundant dots "
            f"({st['pct_changed']}% cells changed), count 37,654 fixed | {stem} | UNSCORED")
    return note[:140]


def main() -> int:
    # Historical variant builders obey the same literal pre-placement stop.
    sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="releases/axis86")
    ap.add_argument("--no-proxy", action="store_true",
                    help="skip the fold-fair hide-and-recover draw (it is report-only)")
    a = ap.parse_args()
    t0 = time.time()

    pins = verify_inputs()
    ctx = grid_io.load_context()
    foot, cat = ctx["footprint"], ctx["catalogue"]
    rebuild = rebuild_parent(foot, cat)
    parent = grid_io.load_dots(PATHS["parent"], foot)
    print(f"[parent] {rebuild['rebuilt_dots']} dots, rebuild sha256 {rebuild['rebuild_sha256'][:16]}… "
          f"BYTE-EXACT vs the published file", flush=True)

    ctx_full = {"footprint": foot, "catalogue": cat}
    built: dict[str, np.ndarray] = {}
    stat: dict[str, dict] = {}
    for law in ARMS + (CONTROL,):
        t = time.time()
        mask, st = SP.relocate(parent, ctx_full, law, CREDIT_MAX, window_px=WINDOW_PX,
                              floor_px=FLOOR_PX, clearance_px=CLEARANCE_PX, seed=SEED)
        built[law], stat[law] = mask, st
        print(f"[{law:8s}] placed={st['moved_placed']:5d} unplaced={st['moved_unplaced']:3d} "
              f"changed={st['pct_changed']:6.2f}% disp={st['mean_displacement_px']:5.2f}px "
              f"cover={st['union_cover_gain_cells']:+8d}px  ({time.time()-t:.0f}s)", flush=True)

    # ---------------------------------------------------------------- release + gates
    known = known_hashes()
    cards = {}
    for law in ARMS + (CONTROL,):
        mask = built[law]
        st = stat[law]
        token = dot8(mask)
        stem = f"gems86-{R0_ID}-sp-{law}{CREDIT_MAX}-{DATE_TAG}-{token}"
        note = note_for(stem, st, {})
        pair = grid_io.write_pair(mask, ctx, ROOT / a.out, stem, name=stem, note=note)
        g = {mode: gates.run_all(pair[mode]["path"], ctx, known, grid_io.PARENT_CAT_CLEARANCE_PX)
             for mode in ("nan", "zeros")}
        ng = new_mass_gate(mask, parent, cat, foot, CLEARANCE_PX)
        diff = SP.parent_diff(parent, mask, foot)
        cards[law] = {"id": stem, "axis": AXIS, "value": f"{law}c{CREDIT_MAX}", "token": token,
                      "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                      "role": "control" if law == CONTROL else "candidate",
                      "slot_candidate": law in ARMS,
                      "rule": ENCODING_RULE if law != CONTROL else (
                          "null control: uniform random eligible cell in the same 8 px window, "
                          "same selection, same floor, same exclusions - not a slot candidate"),
                      "parent": {"id": PARENT_LABEL, "sha256": LITERAL_PINS["parent"],
                                  "rebuild": rebuild},
                      "stats": {k: v for k, v in st.items() if k != "selection"},
                      "selection": st["selection"], "parent_diff": diff,
                      "gates": g, "new_mass_gate": ng, "artifacts": pair, "note": note,
                      "note_chars": len(note), "git_sha": git_sha()}
        for mode in ("nan", "zeros"):
            known.add(pair[mode]["sha256"])
        ok = all(g[m]["passed"] for m in g) and ng["passed"] and diff["count_delta"] == 0
        print(f"[{law:8s}] gates {'PASS' if ok else 'FAIL'}  dots={diff['variant_dots']} "
              f"changed={diff['pct_changed_of_parent']}%", flush=True)
        if not ok:
            raise SystemExit(f"gate failure on {law}: {json.dumps({m: g[m] for m in g})[:600]}")

    # ---------------------------------------------------------------- instruments (report only)
    instr: dict[str, dict] = {}
    instr["sgmc_offcatalogue_surrogate"] = sgmc_instrument(parent, built, foot, cat)
    instr["support_surface_read"] = support_read(parent, built)
    instr["leakage_canary"] = canary(parent, built, foot, cat)
    print("[canary] " + instr["leakage_canary"]["status"], flush=True)
    if not a.no_proxy:
        try:
            instr["catalogue_hide_recover_proxy"] = hide_recover(parent, built)
        except Exception as exc:                            # never a silent skip
            instr["catalogue_hide_recover_proxy"] = {"status": "UNAVAILABLE",
                                                     "reason": f"{type(exc).__name__}: {exc}"}
    for law in ARMS + (CONTROL,):
        cards[law]["predicted_live_change"] = instr["sgmc_offcatalogue_surrogate"]["arms"][
            "control_random" if law == CONTROL else law]["delta"]
        cards[law]["predicted_range_px"] = [
            instr["sgmc_offcatalogue_surrogate"]["arms"]["control_random" if law == CONTROL else law][k]
            for k in ("translated_min", "translated_max")]

    # ---------------------------------------------------------------- receipts
    for law, card in cards.items():
        rec = json.loads(json.dumps(card, default=str))
        rec.pop("artifacts", None)
        rec["evidence_class"] = "MODEL"
        rec["receipt"] = None
        rp = Path(card["artifacts"]["zeros"]["path"]).with_suffix(".json")
        rp.write_text(json.dumps(rec, indent=2) + "\n")
        card["receipt_path"] = str(rp.relative_to(ROOT))

    out = {"schema_version": 1, "session_axis": AXIS, "generated_utc":
           time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "git_sha": git_sha(), "seed": SEED, "elapsed_s": round(time.time() - t0, 1),
           "parent": {"id": PARENT_LABEL, "file": str(PATHS['parent'].relative_to(ROOT)),
                      "sha256": LITERAL_PINS["parent"],
                      "live_claim": "0.2778 CLAIM (owner-reported, no submission-page receipt in ledger/)",
                      "rebuild": rebuild},
           "inputs_verified": pins,
           "constants": {"credit_max": CREDIT_MAX, "window_px": WINDOW_PX, "floor_px": FLOOR_PX,
                         "clearance_px": CLEARANCE_PX, "kernel_radius_px": SP.R_PX,
                         "hex_spacing_px": SP.HEX_SPACING_PX, "parent_floor_px": SP.PARENT_FLOOR_PX,
                         "across_trace_tol_px": 1.0, "min_along_trace_px": 2.0,
                         "coherence_min": 0.30, "arms": list(ARMS), "control": CONTROL},
           "top_public": "UNSUPPLIED (human fills from the leaderboard, with a date)",
           "slots": "UNSUPPLIED (1 entity, 3 scored per rolling week, one blind final; deadline 2026-12-03 UNVERIFIED)",
           "variants": cards, "instruments": instr,
           "evidence_labels": {"built": "BUILT", "predicted_change": "MODEL",
                               "sgmc_surrogate": "MODEL", "hide_recover": "PROXY",
                               "receipt": "none - only the human can supply it"},
           "dedupe": "exact sha256 + repeated (parent, axis, value) only; no overlap or "
                     "rank-correlation threshold applied (brief 6 supersedes the repo's 70 % rule, "
                     "IR-86-PRUNE-01; no gate script was touched)"}
    ev = ROOT / f"evidence/{SESSION}_axis_{DATE_TAG}.json"
    ev.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"[out] {ev.relative_to(ROOT)}  ({out['elapsed_s']}s)", flush=True)
    print("next: .venv/bin/python scripts/emit_spacing_entries.py && "
          ".venv/bin/python scripts/build_ledger.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
