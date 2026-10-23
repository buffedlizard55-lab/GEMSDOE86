#!/usr/bin/env python3
"""Build the preregistered 5 km CONCENTRATION ladder from byte-exact R0.

Three and only three candidates: ``b5km-move10/15/20``.  Each moves the stated
fraction of R0's dots from the lowest-prior 5 km blocks to the highest-prior
fifth of footprint-bearing blocks, at fixed count and with geometric-only
placement.  New mass must be >3 px from the visible catalogue.  The builder
never reads private truth, contacts a competition site, or submits anything.

Order of operations: verify every pin; reproduce R0's mask *and file SHA-256*;
build; run the leakage canary and report-only SGMC/hide-and-recover instruments;
write both encodings; re-read them and run every MUST gate; emit receipts and
canonical ledger source rows.  A canary AUC >0.90 stops before release writing.

Re-run after a successful build with ``--validate-only`` for the end-of-session
 disk self-check.  A full rebuild is deterministic and allowed only when every
own (parent, axis, value) row reproduces its recorded hash exactly.
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
for p in (ROOT / "src", ROOT / "scripts", ROOT / "vendor", ROOT / "vendor" / "template66"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gems57 import evaluate_holdout, metric  # noqa: E402
from gems86 import concentration5 as C5  # noqa: E402
from gems86 import instrument  # noqa: E402
from gems86_axis import bands as bandmod  # noqa: E402
from gems86_axis import gates, grid_io, variants  # noqa: E402
from build_r0_spacing import rebuild_parent, support_read, verify_inputs as verify_core_inputs  # noqa: E402
from run_prune_ladder import BASE_FILE, read, serialization_profile, sha256, write_with_profile  # noqa: E402

SESSION = "concentration5"
DATE_TAG = "20261023"
SEED = 20261023
PARENT = "h33-h33-2-b2"
OUT_DIR = ROOT / "releases" / SESSION
RUN_CARD = ROOT / "evidence" / f"{SESSION}_axis_{DATE_TAG}.json"
MECHANISM_CARD = ROOT / "evidence" / f"{SESSION}-mechanism.md"
VARIANTS_JSON = ROOT / "ledger" / f"variants_{SESSION}.json"
VALUES = tuple(C5.value_for(f) for f in C5.DOSES)
PARENT_ALIASES = {PARENT, "h33-h33-2-b2-20261004-e5eb6e7e", "h33-2b2"}
EXTERNAL_PATHS = {
    "ext_geodawn_extensions_u8": ROOT / ".cache/gems_data/external/geodawn_extensions_u8.tif",
    "ext_topo_10m_derived_100m_u8": ROOT / ".cache/gems_data/external/topo_10m_derived_100m_u8.tif",
    "ext_dem10_chi_100m_i16": ROOT / ".cache/gems_data/external/dem10_chi_100m_i16.tif",
}


def git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def require_clean_tracked_tree() -> None:
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"],
                                    cwd=ROOT, text=True).strip()
    if dirty:
        raise SystemExit("commit the builder before running so the logged Git SHA identifies the code\n" + dirty)


def verify_external_inputs() -> dict:
    manifest = {f["id"]: f for f in json.loads((ROOT / "registry/data_manifest.json").read_text())["files"]}
    out = {}
    for ident, path in EXTERNAL_PATHS.items():
        entry = manifest[ident]
        if not path.is_file():
            raise SystemExit(f"missing pinned input {ident}: {path}; run scripts/restore_axis_inputs.py")
        digest = sha256(path)
        if digest != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise SystemExit(f"PIN MISMATCH {ident}: {digest} != {entry['sha256']}")
        out[ident] = {"path": str(path.relative_to(ROOT)), "sha256": digest,
                      "bytes": entry["bytes"], "verified": True,
                      "organizer_authenticated": False, "provenance": entry["provenance"]}
    return {"files": out, "pin_source": "registry/data_manifest.json"}


def previous_rows() -> dict[str, dict]:
    path = ROOT / "ledger/submissions.csv"
    if not path.is_file():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {r["value"]: r for r in rows
            if (r.get("axis") or "").upper() == C5.AXIS and r.get("value") in VALUES
            and r.get("parent") in PARENT_ALIASES}


def known_hashes(own: dict[str, dict]) -> set[str]:
    """Exact-hash dedupe only; own deterministic rebuilds are handled separately."""
    own_sha = {r.get("sha256") for r in own.values()}
    out: set[str] = set()
    led = ROOT / "ledger/submissions.csv"
    if led.is_file():
        with led.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                for col in ("sha256", "sha256_nan", "sha256_zeros"):
                    value = (row.get(col) or "").strip()
                    if len(value) == 64 and value not in own_sha:
                        out.add(value)
    for path in (ROOT / "ledger").glob("variants_*.json"):
        if path == VARIANTS_JSON:
            continue
        try:
            entries = json.loads(path.read_text())
        except (ValueError, TypeError):
            continue
        for entry in entries if isinstance(entries, list) else []:
            for col in ("sha256", "sha256_nan", "sha256_zeros"):
                value = entry.get(col, "")
                if isinstance(value, str) and len(value) == 64:
                    out.add(value)
    for directory in (ROOT / "data/scored_fleet", ROOT / "docs/downloads"):
        for path in directory.glob("*.tif"):
            digest = sha256(path)
            if digest not in own_sha:
                out.add(digest)
    return out


def load_tmi_gradient() -> tuple[np.ndarray, dict]:
    bd = bandmod.load_bands()
    gradient = bandmod.gradient_magnitude(bd["tmi_up150"], fill_value=0.0)
    if gradient.shape != (3730, 3292) or not np.isfinite(gradient).all():
        raise SystemExit("invalid TMI gradient surface")
    return gradient, {"source": "GeoDAWN TMI_up150, inherited quantized-band transform and Sobel gradient",
                      "source_url": "https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7",
                      "license": "USGS public-domain product; owner mirror integrity-pinned",
                      "band_names": bd["meta"]["extensions"]}


def build_arms(parent: np.ndarray, ctx: dict, tmi_grad: np.ndarray) -> tuple[dict, dict]:
    prior_pack = C5.make_prior(ctx, tmi_grad)
    arms, stats = {}, {}
    for frac in C5.DOSES:
        started = time.time()
        mask, st = C5.build(parent, ctx, prior_pack["prior"], frac)
        value = C5.value_for(frac)
        arms[value], stats[value] = mask, st
        print(f"[build] {value}: moved={st['moved_placed']} changed-cells="
              f"{variants.parent_diff(parent, mask, ctx['footprint'])['pct_changed_of_parent']}% "
              f"CV5km={st['block_density_parent']['density_cv_occupied']}->"
              f"{st['block_density_variant']['density_cv_occupied']} ({time.time()-started:.1f}s)", flush=True)
    # Source deletion sets are dose-nested by construction.  Destination placement is
    # recomputed at each dose and is deliberately not claimed to be nested.
    dropped = {v: parent & ~arms[v] for v in VALUES}
    nesting = {f"{a}_sources_subset_of_{b}": bool((dropped[a] & ~dropped[b]).sum() == 0)
               for a, b in zip(VALUES, VALUES[1:])}
    if not all(nesting.values()):
        raise SystemExit(f"dose ladder source nesting failed: {nesting}")
    stats["_ladder"] = {"source_nesting": nesting,
                        "destination_nesting_claimed": False,
                        "prior_blocks": int(np.isfinite(prior_pack["prior"]).sum())}
    return arms, stats


def sgmc_instrument(parent: np.ndarray, arms: dict, foot: np.ndarray, cat: np.ndarray) -> dict:
    path = ROOT / ".cache/gems_data/external/derived_sgmc_faults_100m_u8.tif"
    sgmc = read(path) > 0
    truth = sgmc & foot & ~cat
    q = np.zeros(foot.shape, np.int8)
    h, w = foot.shape
    q[:h//2, w//2:] = 2
    q[h//2:, :w//2] = 3
    q[h//2:, w//2:] = 4
    q[:h//2, :w//2] = 1

    def score(mask, truth_mask, valid):
        return metric.dti_binary(mask, truth_mask, valid=valid, known=cat)

    base = score(parent, truth, foot)
    rng = np.random.default_rng(SEED)
    shifts = [(0, 0)] + [tuple(int(x) for x in rng.integers(-6, 7, 2)) for _ in range(11)]
    result = {"evidence_class": "MODEL", "status": "REPORT-ONLY",
              "instrument": "gems57.metric.dti_binary vs USGS SGMC off-catalogue fault pixels",
              "source_url": "https://www.usgs.gov/science-plan/conterminus-synthetic-geologic-map-compiler-sgmc",
              "truth_pixels": int(truth.sum()),
              "parent": {k: float(base[k]) for k in ("dti", "tp", "fp", "fn", "coverage")},
              "translation_shifts_px": [list(x) for x in shifts], "arms": {}}
    for value, mask in arms.items():
        child = score(mask, truth, foot)
        per_q = {}
        for i in (1, 2, 3, 4):
            region = foot & (q == i)
            per_q[f"q{i}"] = round(score(mask, truth & region, region)["dti"]
                                   - score(parent, truth & region, region)["dti"], 6)
        translated = []
        for dy, dx in shifts:
            moved_truth = C5.shift_truth(truth, dy, dx)
            translated.append(round(score(mask, moved_truth, foot)["dti"]
                                    - score(parent, moved_truth, foot)["dti"], 6))
        delta = round(float(child["dti"] - base["dti"]), 6)
        result["arms"][value] = {
            "dti": round(float(child["dti"]), 6), "delta": delta,
            "delta_tp": round(float(child["tp"] - base["tp"]), 4),
            "delta_fp": round(float(child["fp"] - base["fp"]), 4),
            "quadrant_delta": per_q,
            "quadrant_positive": sum(x > 0 for x in per_q.values()),
            "translated_delta": translated,
            "translated_range": [min(translated), max(translated)],
            "translated_positive_draws": sum(x > 0 for x in translated),
        }
    return result


def leakage_canary(prior_pack: dict, shape: tuple[int, int], foot: np.ndarray,
                   cat: np.ndarray) -> dict:
    from sklearn.metrics import roc_auc_score

    sgmc = read(ROOT / ".cache/gems_data/external/derived_sgmc_faults_100m_u8.tif") > 0
    truth = sgmc & foot & ~cat
    active = foot & ~cat
    rng = np.random.default_rng(SEED)
    flat = np.flatnonzero(active.ravel())
    take = rng.choice(flat, size=min(400_000, flat.size), replace=False)
    y = truth.ravel()[take].astype(np.int8)
    rows = []
    for name, field in (("catalogue_interaction_density", prior_pack["cat_block"]),
                        ("tmi_gradient_response", prior_pack["tmi_block"]),
                        ("combined_block_prior", prior_pack["prior"])):
        px = variants.block_to_pixels(field, shape, C5.BLOCK_PX)
        x = px.ravel()[take]
        finite = np.isfinite(x)
        if finite.sum() and np.unique(x[finite]).size > 1:
            auc = float(roc_auc_score(y[finite], x[finite]))
            rows.append({"feature": name, "auc": round(auc, 6), "n": int(finite.sum())})
    maximum = max((r["auc"] for r in rows), default=0.0)
    return {"status": "PASS" if maximum <= 0.90 else "STOP_INVESTIGATE",
            "threshold": 0.90, "max_auc": round(maximum, 6), "rows": rows,
            "sample_size": int(take.size), "withheld_positives": int(y.sum()),
            "truth": "USGS SGMC off-catalogue map, not competition labels",
            "note": "Single-feature diagnostic only; no feature enters placement after this read."}


def hide_recover(parent: np.ndarray, base: np.ndarray, arms: dict, tmi_grad: np.ndarray,
                 foot: np.ndarray, cat: np.ndarray) -> dict:
    """Fold-fair catalogue PROXY; both parent and children use visible faults only."""
    folds = instrument.build(foot, cat, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    names = ["parent", *VALUES]
    terms = {name: [] for name in names}
    fold_rows = []
    for fold in folds:
        region = foot & fold.region
        visible = fold.visible
        distance = ndi.distance_transform_edt(~visible)
        # The archived base already has its historical 1 px prune.  The 2 px R0
        # prune and every new 3 px placement are recomputed from visible faults.
        fold_parent = (base > 0) & region & (distance > 2.0)
        vctx = {"footprint": region, "catalogue": visible}
        prior_pack = C5.make_prior(vctx, tmi_grad)
        fold_masks = {"parent": fold_parent}
        for frac in C5.DOSES:
            value = C5.value_for(frac)
            fold_masks[value], _ = C5.build(fold_parent, vctx, prior_pack["prior"], frac)
        for name, mask in fold_masks.items():
            _res, block = evaluate_holdout.evaluate(
                mask.astype(np.float32), fold.fold, region, block_side=200,
                origin=(0, 0), global_shape=foot.shape)
            terms[name].append(block)
        fold_rows.append({"fold": fold.name,
                          "withheld_positive_pixels": int((fold.truth & region).sum()),
                          "parent_dots": int(fold_parent.sum())})
        print(f"[proxy] {fold.name}: withheld={fold_rows[-1]['withheld_positive_pixels']} px", flush=True)
    pooled = {name: np.sum(np.stack(parts), axis=0) for name, parts in terms.items()}
    summary = evaluate_holdout.pooled_summary(pooled, draws=1000, seed=SEED,
                                              candidate=C5.value_for(0.15))
    scores = {name: {k: summary["scores"][name][k]
                     for k in ("dti", "ci95", "withheld_positive_pixels")}
              for name in names}
    return {"evidence_class": "PROXY", "status": "REPORT-ONLY (never a gate)",
            "evaluator_version": summary["evaluator_version"],
            "implementation_sha256": summary["implementation_sha256"],
            "design": "buffered whole-component hide-and-recover; visible-only 2 px parent prune and 3 px placements; 20 km paired block bootstrap",
            "seed": SEED, "hide_fraction": 0.20, "folds": fold_rows,
            "scores": scores,
            "paired_15pct_minus_parent": summary["paired_differences"]["parent"],
            "caveat": "The historical base retains its original 1 px catalogue prune. Absolute values are catalogue-recovery PROXY values, never live scores or slot gates."}


def prediction_text(value: str, model: dict, stats: dict) -> str:
    arm = model["arms"][value]
    lo, hi = arm["translated_range"]
    return (f"{arm['delta']:+.4f} (MODEL; translated-SGMC range {lo:+.4f}..{hi:+.4f}; "
            f"{arm['quadrant_positive']}/4 quadrants positive). 5 km block CV "
            f"{stats['block_density_parent']['density_cv_occupied']:.4f}->"
            f"{stats['block_density_variant']['density_cv_occupied']:.4f}; not a score.")


def mechanism_markdown(model: dict, stats: dict) -> str:
    lines = [
        "# Mechanism cards — CONCENTRATION, 5 km blocks (2026-10-23)", "",
        "All predictions are **MODEL** reads against USGS SGMC off-catalogue faults, not scores. "
        "The three doses and the low→high direction were fixed before those reads. "
        "Source: USGS GeoDAWN, https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7 "
        "(public-domain owner mirror); SGMC control: "
        "https://www.usgs.gov/science-plan/conterminus-synthetic-geologic-map-compiler-sgmc.", "",
        "**Shared hypothesis.** Unmapped faults cluster in 5 km fault-interaction / magnetic-edge "
        "blocks more strongly than R0's allocation assumes. **Mechanism.** Move unit dots from "
        "lowest-prior blocks to the highest-prior fifth while holding count and spacing fixed. "
        "**Non-fault mimic.** Lithologic/intrusive magnetic contacts and catalogue-mapping effort "
        "can both create the same block prior without a new fault. **Shared falsifier.** A live "
        "change below 0.01 is no evidence; a ≤−0.01 receipt rejects this allocation direction, and "
        "CV moving farther above the claimed 0.51–0.59 band is the geometric warning, not a gate.", ""
    ]
    for value in VALUES:
        st, arm = stats[value], model["arms"][value]
        lines += [
            f"## {value}", "",
            f"- **Dose / diff:** {st['moved_placed']} dots moved "
            f"({st['pct_parent_dots_moved']:.4f}% of R0); "
            f"{st['pct_changed']:.4f}% changed grid cells; count fixed at 37,654.",
            f"- **Predicted live change:** {arm['delta']:+.4f} MODEL "
            f"(translation sensitivity {arm['translated_range'][0]:+.4f}…{arm['translated_range'][1]:+.4f}; "
            f"{arm['quadrant_positive']}/4 quadrants positive).",
            f"- **Density read:** occupied complete-5 km-block CV "
            f"{st['block_density_parent']['density_cv_occupied']:.4f} → "
            f"{st['block_density_variant']['density_cv_occupied']:.4f}; occupied blocks "
            f"{st['block_density_parent']['occupied_blocks']} → "
            f"{st['block_density_variant']['occupied_blocks']}.",
            f"- **Dose-specific falsifier:** if this dose is flat while another dose has a ≥0.01 "
            f"receipt effect, the response is nonlinear in allocation dose; do not interpolate "
            f"between them. If SGMC's sign is positive but the live sign is negative, the prior is "
            f"mapping effort or a non-fault contact, not new-fault structure.", ""
        ]
    return "\n".join(lines)


def write_releases(parent: np.ndarray, arms: dict, stats: dict, ctx: dict,
                   prior: np.ndarray, model: dict, rebuild: dict, pins: dict, own: dict) -> list[dict]:
    foot, cat = ctx["footprint"], ctx["catalogue"]
    known = known_hashes(own)
    cards = []
    for value in VALUES:
        mask, st = arms[value], stats[value]
        diff = variants.parent_diff(parent, mask, foot)
        separation = C5.prior_separation(parent, mask, prior, C5.BLOCK_PX)
        clearance = C5.new_mass_clearance(parent, mask, cat)
        if not separation["passed"] or not clearance["passed"]:
            raise SystemExit(f"{value}: axis/clearance failure: {separation} {clearance}")
        field = np.where(foot, mask, 0.0).astype(np.float32)
        probe = ROOT / ".cache" / SESSION / f"probe-{value}.tif"
        probe.parent.mkdir(parents=True, exist_ok=True)
        zsha = write_with_profile(probe, field, None)
        stem = f"{PARENT}-{C5.AXIS}-{value}-{DATE_TAG}-{zsha[:8]}"
        previous = own.get(value)
        if previous and previous.get("sha256") and previous["sha256"] != zsha:
            raise SystemExit(f"repeated (parent, axis, value) with different artifact: {value}")
        pred = prediction_text(value, model, st)
        note = (f"R0 {PARENT}; {C5.AXIS} {value}: {st['moved_placed']} dots low->high prior, "
                f"count 37654; pred {model['arms'][value]['delta']:+.4f} MODEL")
        if len(note) > 140:
            raise SystemExit(f"note too long: {len(note)}")
        nan_path = OUT_DIR / f"{stem}.tif"
        zeros_path = OUT_DIR / f"{stem}-zeros.tif"
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        nan_arr = np.where(foot, mask, np.nan).astype(np.float32)
        nan_sha = write_with_profile(nan_path, nan_arr, float("nan"))
        written_zsha = write_with_profile(zeros_path, field, None)
        if written_zsha != zsha:
            raise SystemExit(f"{value}: probe/final zeros hash mismatch")
        gate = {}
        for mode, path in (("nan", nan_path), ("zeros", zeros_path)):
            gate[mode] = gates.run_all(path, ctx, known, grid_io.PARENT_CAT_CLEARANCE_PX)
            on_disk = grid_io.load_dots(path, foot)
            if not np.array_equal(on_disk, mask):
                raise SystemExit(f"{value}/{mode}: written dot set differs from memory")
        if zsha in known or nan_sha in known:
            raise SystemExit(f"{value}: exact SHA-256 already in ledger")
        if not all(gate[m]["passed"] for m in ("nan", "zeros")):
            raise SystemExit(f"{value}: raster gate failure")
        known.update((zsha, nan_sha))
        card = {
            "id": stem, "parent": PARENT, "axis": C5.AXIS, "value": value,
            "role": "candidate", "status": "BUILT", "n_dots": int(mask.sum()),
            "pct_changed": diff["pct_changed_of_parent"],
            "pct_parent_dots_moved": st["pct_parent_dots_moved"],
            "parent_diff": diff, "stats": st,
            "block_density": C5.density_report(parent, mask, foot),
            "prior_separation": separation, "new_mass_clearance": clearance,
            "predicted_change": pred, "evidence_class": "MODEL",
            "note": note, "note_chars": len(note),
            "gates": gate, "artifacts": {
                "nan": {"path": str(nan_path.relative_to(ROOT)), "sha256": nan_sha,
                        "bytes": nan_path.stat().st_size},
                "zeros": {"path": str(zeros_path.relative_to(ROOT)), "sha256": zsha,
                          "bytes": zeros_path.stat().st_size},
            },
            "parent_rebuild_sha256": rebuild["rebuild_sha256"],
            "git_sha": git_sha(), "input_pins": pins,
            "approved_for_weekly_slot": False, "submission_slots_used": 0,
        }
        receipt_path = zeros_path.with_suffix(".json")
        receipt_path.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
        card["receipt_path"] = str(receipt_path.relative_to(ROOT))
        cards.append(card)
        print(f"[release] {stem}: gates PASS; zeros={zsha[:8]} nan={nan_sha[:8]}", flush=True)
    return cards


def emit_ledger_rows(cards: list[dict]) -> None:
    entries = []
    for card in cards:
        d, st = card["parent_diff"], card["stats"]
        entries.append({
            "site": "GEMSDOE86", "id": card["id"], "parent": PARENT,
            "axis": "concentration", "value": card["value"], "encoding": "zeros",
            "n_dots": card["n_dots"], "pct_changed": card["pct_changed"],
            "pct_parent_dots_moved": card["pct_parent_dots_moved"],
            "sha256": card["artifacts"]["nan"]["sha256"],
            "sha256_zeros": card["artifacts"]["zeros"]["sha256"],
            "sha8": card["artifacts"]["zeros"]["sha256"][:8],
            "files": [card["artifacts"]["nan"]["path"], card["artifacts"]["zeros"]["path"]],
            "status": "BUILT", "slot_candidate": True,
            "approved_for_weekly_slot": False,
            "predicted_change": card["predicted_change"],
            "source_url": "https://github.com/buffedlizard55-lab/GEMSDOE86/tree/arena/146307ee-gemsdoe86",
            "diff": {"n_parent": d["parent_dots"], "n_candidate": d["variant_dots"],
                     "retained": d["shared_dots"], "removed": d["dropped"], "added": d["added"],
                     "pct_of_parent_changed": d["pct_changed_of_parent"],
                     "pct_parent_dots_moved": card["pct_parent_dots_moved"],
                     "jaccard": d["jaccard"], "count_exact": d["count_delta"] == 0,
                     "axis_note": st["placement_rule"]},
            "blocks": {"block_size": st["block_size"], "moved": st["moved_placed"],
                       "moved_target": st["moved_target"], "dest_blocks": st["dest_blocks"],
                       "density_cv_occupied_parent": st["block_density_parent"]["density_cv_occupied"],
                       "density_cv_occupied_variant": st["block_density_variant"]["density_cv_occupied"],
                       "occupied_blocks_parent": st["block_density_parent"]["occupied_blocks"],
                       "occupied_blocks_variant": st["block_density_variant"]["occupied_blocks"],
                       "min_cat_edt_px_new_mass": card["new_mass_clearance"]["minimum_px"]},
            "gates_passed": all(card["gates"][m]["passed"] for m in ("nan", "zeros")),
            "receipt_score": "",
        })
    VARIANTS_JSON.write_text(json.dumps(entries, indent=2, allow_nan=False) + "\n")
    subprocess.run([sys.executable, str(ROOT / "scripts/build_ledger.py"), "--json"],
                   cwd=ROOT, check=True)


def validate_only() -> int:
    if not RUN_CARD.is_file():
        raise SystemExit(f"missing {RUN_CARD}")
    card = json.loads(RUN_CARD.read_text())
    own = previous_rows()
    known = known_hashes(own)
    ctx = grid_io.load_context()
    parent = grid_io.load_dots(ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
                               ctx["footprint"])
    for v in card["variants"]:
        value = v["value"]
        if value not in own:
            raise SystemExit(f"ledger row missing for {value}")
        masks = []
        for mode in ("nan", "zeros"):
            artifact = v["artifacts"][mode]
            path = ROOT / artifact["path"]
            if sha256(path) != artifact["sha256"]:
                raise SystemExit(f"hash drift: {path}")
            if mode == "zeros" and own[value]["sha256"] != artifact["sha256"]:
                raise SystemExit(f"ledger/file hash mismatch: {value}")
            result = gates.run_all(path, ctx, known, grid_io.PARENT_CAT_CLEARANCE_PX)
            if not result["passed"]:
                raise SystemExit(f"validation failed: {path}: {result}")
            masks.append(grid_io.load_dots(path, ctx["footprint"]))
        if not np.array_equal(masks[0], masks[1]) or int(masks[0].sum()) != int(own[value]["n_dots"]):
            raise SystemExit(f" twin/count mismatch: {value}")
        if not C5.new_mass_clearance(parent, masks[0], ctx["catalogue"])["passed"]:
            raise SystemExit(f"new-mass clearance failed: {value}")
        known.update(v["artifacts"][m]["sha256"] for m in ("nan", "zeros"))
    print(json.dumps({"status": "PASS", "variants": len(card["variants"]),
                      "checks": "hashes, ledger, format, values, catalogue, twins, new-mass clearance"}, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()
    if args.validate_only:
        return validate_only()
    require_clean_tracked_tree()
    t0 = time.time()
    pins = {"core": verify_core_inputs(), "external": verify_external_inputs()}
    ctx = grid_io.load_context()
    foot, cat = ctx["footprint"], ctx["catalogue"]
    rebuild = rebuild_parent(foot, cat)
    parent = grid_io.load_dots(ROOT / "data/scored_fleet/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", foot)
    if int(parent.sum()) != 37654:
        raise SystemExit("wrong R0 dot count")
    base = read(BASE_FILE)
    tmi_grad, tmi_meta = load_tmi_gradient()
    own = previous_rows()
    arms, stats = build_arms(parent, ctx, tmi_grad)
    prior_pack = C5.make_prior(ctx, tmi_grad)
    canary = leakage_canary(prior_pack, foot.shape, foot, cat)
    print(f"[canary] {canary['status']} max_auc={canary['max_auc']}", flush=True)
    if canary["status"] != "PASS":
        stop = ROOT / "evidence/concentration5-canary-stop.json"
        stop.write_text(json.dumps(canary, indent=2) + "\n")
        raise SystemExit(f"leakage canary >0.90; STOP: {stop}")
    model = sgmc_instrument(parent, arms, foot, cat)
    print("[model] " + json.dumps({v: model["arms"][v]["delta"] for v in VALUES}), flush=True)
    proxy = hide_recover(parent, base, arms, tmi_grad, foot, cat)
    support = support_read(parent, arms)
    cards = write_releases(parent, arms, stats, ctx, prior_pack["prior"], model, rebuild, pins, own)
    out = {
        "schema_version": 1, "session_axis": C5.AXIS, "session": SESSION,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": git_sha(), "tracked_tree_clean_at_build_start": True,
        "seed": SEED, "elapsed_seconds": round(time.time() - t0, 1),
        "parent": {"id": PARENT, "n_dots": int(parent.sum()),
                   "sha256": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
                   "live_claim": "0.2778 CLAIM (no submission-page receipt)", "rebuild": rebuild},
        "preregistration": {"block_size": "5 km (50x50 px)", "doses": list(C5.DOSES),
                            "values": list(VALUES), "destination_block_fraction": C5.DEST_BLOCK_FRAC,
                            "direction": "lowest-prior -> highest-prior", "count": 37654,
                            "placement": "geometric only; no SGMC or holdout truth enters placement",
                            "new_mass_clearance_px": C5.NEW_MASS_CLEARANCE_PX,
                            "cv_band_status": "0.51-0.59 is an unverified CLAIM, never a target or gate",
                            "density_domain": "complete 5 km blocks; 30-row/42-column remainders are unclassified, never low-prior sources"},
        "inputs_verified": pins, "tmi": tmi_meta,
        "ladder": stats.pop("_ladder"), "variants": cards,
        "instruments": {"leakage_canary": canary, "sgmc_offcatalogue_surrogate": model,
                        "catalogue_hide_recover_proxy": proxy, "support_surface_read": support},
        "top_public": "UNSUPPLIED (human must provide value and date)",
        "slots": "UNSUPPLIED; one entity, 3 scored submissions/rolling week; no slot used",
        "deadline": "2026-12-03 user-supplied, UNVERIFIED",
        "evidence_labels": {"live_parent": "CLAIM", "predicted_change": "MODEL",
                            "hide_recover": "PROXY", "receipt": "NONE"},
        "dedupe": "exact SHA-256 plus repeated (parent, axis, value); no overlap or rank-correlation gate",
        "no_submission": True,
    }
    RUN_CARD.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    MECHANISM_CARD.write_text(mechanism_markdown(model, stats))
    emit_ledger_rows(cards)
    subprocess.run([sys.executable, str(ROOT / "scripts/build_ledger.py"), "--check"], cwd=ROOT, check=True)
    print(f"[done] {RUN_CARD.relative_to(ROOT)}; {len(cards)} variants; {out['elapsed_seconds']}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
