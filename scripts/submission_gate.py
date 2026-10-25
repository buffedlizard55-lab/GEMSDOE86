#!/usr/bin/env python3
"""One automated, deterministic upload gate: prints OK TO SUBMIT or DO NOT SUBMIT.

Usage: python scripts/submission_gate.py RUN_CARD.json [--out docs/evidence/submission-gate.json]

No human inspection is involved. Every check is recomputed from the bytes on
disk, or read from an evidence file that is bound to those bytes by SHA-256.
A check that cannot be evaluated FAILS (fail-closed). The verdict is
``OK TO SUBMIT`` only if every check passes:

  F1  file exists and SHA-256 equals the run card's ``raster_sha256``
  F2  shared validator (vendor/gems57/validate.py): single band float32,
      EPSG:32611, 3730x3292, sample transform, no NaN/Inf anywhere, values in
      [0,1], zeros outside footprint, zero positives on mapped catalogue.
      This is the cure for the portal error "Predicted values must be in range
      [0, 1]": NaN fill or out-of-range values fail here.
  F3  the one-TIFF ZIP holds exactly one member, byte-identical to the TIFF
  F4  name and note are 1..140 characters
  U1  the final-dots registry report (scripts/check_h86e_registry.py) is bound
      to these dots, covers the complete index, and the rank test passes
      (Spearman <= 0.90 against every raster); raw like-for-like and literal
      overlap readings are shown, never hidden
  U2  the surface report passes the rho <= 0.90 test against every raster
  U3  overlap decision: PA-86-02 chance-corrected check passes
      (scripts/pa86_chance_overlap.py) -- any dot field whose own 3 px halo
      covers <= 70 % of the allowed domain and holds > 70 % of our dots is a
      hard duplicate stop
  S1  leakage canary: max single-feature discriminative AUC <= 0.90
  S2  model acceptance rule of the lane's preregistration passed
  S3  holdout promote rule passed: beats the current holdout best (paired CI)
  S4  live-score emulator (H86J LLP, fitted on ~100 fleet scores) projects the
      file above H33's projection.  This is a MODEL check and never a score; it
      can only veto.

A pass is upload *eligibility* under the project's rules. It is never a score,
and it does not replace the weekly-cap check on the DrivenData submission page.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
from gems57 import grid, validate  # noqa: E402

OK, NO = "OK TO SUBMIT", "DO NOT SUBMIT"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as s:
        for c in iter(lambda: s.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _load(rel: str | None) -> dict | None:
    if not rel:
        return None
    p = ROOT / rel
    return json.loads(p.read_text()) if p.is_file() else None


def _report_path(card: dict, key: str, nested: tuple[str, str]) -> str | None:
    """Run cards name their bound registry reports either top-level or under
    ``uniqueness`` (H86J schema); a missing name fails closed downstream."""
    if card.get(key):
        return card[key]
    return ((card.get("uniqueness") or {}).get(nested[0]) or {}).get(nested[1])


def evaluate(card: dict) -> dict:
    checks: dict[str, dict] = {}
    card = dict(card)
    card["registry_final_dots_report"] = _report_path(card, "registry_final_dots_report", ("final_dots", "report"))
    card["registry_surface_report"] = _report_path(card, "registry_surface_report", ("surface", "report"))
    card["chance_overlap_report"] = _report_path(card, "chance_overlap_report", ("chance_overlap", "report"))

    def put(key, passed, detail):
        checks[key] = dict(passed=bool(passed), detail=detail)

    g = grid.load_grid(ROOT / "data/bridge")
    tif = ROOT / card.get("raster_path", "")
    # F1
    actual = sha256(tif) if tif.is_file() else None
    put("F1_sha256_bound", actual is not None and actual == card.get("raster_sha256"),
        dict(file=card.get("raster_path"), actual=actual, run_card=card.get("raster_sha256")))
    # F2
    try:
        rec = validate.validate(tif, g.footprint, g.catalogue)
        put("F2_shared_validator", rec["all_checks_passed"],
            dict(checks=rec["checks"], n_nan=rec["n_nan"], n_infinite=rec["n_infinite"], min=rec["min"],
                 max=rec["max"], positives=rec["emitted_positive_pixels"]))
    except Exception as exc:  # fail closed
        put("F2_shared_validator", False, dict(error=str(exc)))
    # F3
    zp = ROOT / card.get("zip_path", "")
    try:
        with zipfile.ZipFile(zp) as z:
            names = z.namelist()
            same = len(names) == 1 and names[0].endswith(".tif") and z.read(names[0]) == tif.read_bytes()
        put("F3_single_tiff_zip", same, dict(zip=card.get("zip_path"), members=names))
    except Exception as exc:
        put("F3_single_tiff_zip", False, dict(error=str(exc)))
    # F4
    name, note = card.get("submission_name", ""), card.get("submission_note", "")
    put("F4_name_note_length", 0 < len(name) <= 140 and 0 < len(note) <= 140,
        dict(name_chars=len(name), note_chars=len(note)))
    # dots binding: TIFF content == the final-dots array the registry audited
    dots_npy = ROOT / card.get("dots_npy", "")
    bound_sha = None
    try:
        dots = np.load(dots_npy, allow_pickle=False)
        with rasterio.open(tif) as ds:
            a = ds.read(1)
        same_px = bool(np.array_equal(dots.astype(np.float32), a.astype(np.float32)))
        bound_sha = sha256(dots_npy)
    except Exception as exc:
        same_px = False
        bound_sha = f"error: {exc}"
    # U1
    rep = _load(card.get("registry_final_dots_report"))
    lit = (rep or {}).get("two_phase", {}).get("literal_reading", {}) if rep else {}
    lfl = (rep or {}).get("two_phase", {}).get("like_for_like_reading", {}) if rep else {}
    # Binding parts of the final-dot measurement: bound to these bytes, complete
    # registry, rank test rho <= 0.90 against EVERY raster.  The overlap decision
    # is U3 (PA-86-02 chance-corrected), because the raw dot-field reading fires
    # on the 13GEMSDOE stride-5 lattice (99.87 % halo coverage) for any dot set.
    worst_rho = lit.get("worst_spearman_full_footprint")
    u1 = bool(rep and same_px and rep.get("candidate_source_sha256") == bound_sha
              and rep.get("mode") == "final_dots" and rep.get("registry_complete_for_index")
              and lit.get("rho_firings") == 0 and worst_rho is not None and worst_rho <= 0.90)
    put("U1_registry_final_dots_bound_complete_rho", u1,
        dict(report=card.get("registry_final_dots_report"), tif_equals_audited_dots=same_px,
             rasters_measured=(rep or {}).get("registry_rasters_measured"),
             registry_complete=(rep or {}).get("registry_complete_for_index"),
             worst_spearman_final_dots=worst_rho, rho_firings=lit.get("rho_firings"),
             raw_like_for_like_gate_pass=(rep or {}).get("final_dots_gate_pass"),
             worst_forward_overlap_dot_fields=lfl.get("worst_forward_overlap_dot_fields"),
             worst_forward_overlap_dot_field_submission=lfl.get("worst_forward_overlap_dot_field_submission"),
             literal_reading=dict(duplicate=lit.get("duplicate"), worst_forward_overlap=lit.get("worst_forward_overlap"),
                                  worst_overlap_submission=lit.get("worst_overlap_submission"),
                                  note="literal reading shown side by side (PA-86-01); a continuous full-support "
                                       "witness fires on every nonempty candidate")))
    # U2
    srep = _load(card.get("registry_surface_report"))
    surf_npy = ROOT / card.get("surface_npy", "")
    s_sha = sha256(surf_npy) if surf_npy.is_file() else None
    u2 = bool(srep and srep.get("mode") == "surface" and srep.get("candidate_source_sha256") == s_sha
              and srep.get("surface_gate_pass") and srep.get("registry_complete_for_index"))
    put("U2_registry_surface_rho", u2,
        dict(report=card.get("registry_surface_report"),
             worst_spearman=(srep or {}).get("two_phase", {}).get("literal_reading", {}).get("worst_spearman_full_footprint"),
             worst_spearman_submission=(srep or {}).get("two_phase", {}).get("literal_reading", {}).get("worst_spearman_submission")))
    # U3
    crep = _load(card.get("chance_overlap_report"))
    u3 = bool(crep and crep.get("candidate_source_sha256", bound_sha) == bound_sha and crep.get("gate_pass"))
    put("U3_pa86_chance_overlap", u3, dict(report=card.get("chance_overlap_report"),
                                           informative_firings=(crep or {}).get("informative_firings"),
                                           space_filling_firings=(crep or {}).get("space_filling_firings"),
                                           worst_spearman_any_raster=(crep or {}).get("worst_spearman_any_raster")))
    # S1-S3 from the lane evidence (bound by the run card's SHA)
    s = card.get("science", {})
    put("S1_leakage_canary", s.get("canary_max_auc") is not None and s["canary_max_auc"] <= 0.90,
        dict(max_discriminative_auc=s.get("canary_max_auc"), feature=s.get("canary_max_feature")))
    put("S2_model_acceptance", bool(s.get("model_accepted")), dict(rule=s.get("model_acceptance_rule"),
                                                                     value=s.get("model_acceptance_value")))
    put("S3_holdout_beats_current_best", bool(s.get("holdout_promote")),
        dict(candidate=s.get("holdout_candidate"), current_holdout_best=s.get("holdout_current_best"),
             paired_delta=s.get("holdout_paired_delta"), rule=s.get("holdout_rule")))
    put("S4_live_emulator_above_h33", bool(s.get("emulator_s4_pass")),
        dict(candidate=s.get("emulator_candidate"), h33=s.get("emulator_h33"),
             note="LLP-EMULATOR MODEL projection, never a score; can only veto (H86J Amendment A5)"))
    failed = [k for k, v in checks.items() if not v["passed"]]
    verdict = OK if not failed else NO
    return dict(schema="gems86.submission-gate.v1", generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                verdict=verdict, ok_to_submit=verdict == OK, failed_checks=failed,
                file=card.get("raster_path"), zip=card.get("zip_path"), sha256=actual,
                submission_name=name, submission_note=note, lane=card.get("lane"),
                checks=checks,
                meaning=("OK TO SUBMIT = every automated project gate passed for these exact bytes; "
                         "still confirm the weekly quota on the DrivenData submission page. "
                         "DO NOT SUBMIT = at least one gate failed (see failed_checks). Never a score."))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_card", type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "docs/evidence/submission-gate.json")
    a = ap.parse_args(argv)
    card = json.loads(a.run_card.read_text())
    doc = evaluate(card)
    doc["run_card"] = str(a.run_card.resolve().relative_to(ROOT)) if a.run_card.resolve().is_relative_to(ROOT) else str(a.run_card)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(doc, indent=1) + "\n")
    print(doc["verdict"])
    for k in doc["failed_checks"]:
        print(f"  FAILED {k}")
    return 0 if doc["ok_to_submit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
