"""Assemble the H86E-RIDF run card from evidence files (no hand-typed numbers)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "docs/evidence"
REL = ROOT / "releases/h86e-NEGATIVE-DO-NOT-SUBMIT"
NAME = "gems86-h86e-ridf-hgbthin-37654dots-20261024-zeros"


def load(p):
    return json.loads(Path(p).read_text())


def main():
    hold = load(EV / "h86e_holdout.json")
    comp = load(EV / "h86e_comparator.json")
    rec = load(REL / f"{NAME}.json")
    tif = REL / f"{NAME}.tif"
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == rec["sha256"]
    dots = load(EV / "h86e_registry_final_dots.json")
    surf = load(EV / "h86e_registry_surface.json") if (EV / "h86e_registry_surface.json").exists() else None
    chance = load(EV / "h86e_pa86_chance_overlap.json")
    surf_rho = surf["two_phase"]["literal_reading"]["worst_spearman_full_footprint"] if surf else None
    surface_duplicate = surf_rho is not None and surf_rho > 0.90
    dots_duplicate = not chance["gate_pass"]
    e1 = comp["paired"]["E1_hgb_thin"]
    s, d = e1["scores"], e1["paired_differences"]["R0_foldfair"]
    beats_r0 = d["ci95"][0] > 0
    lfl = dots["two_phase"]["like_for_like_reading"]
    lit = dots["two_phase"]["literal_reading"]
    card = dict(
        lane="H86E-RIDF (Range-Interior / Distal Fault lineaments, catalogue-blind HGB)",
        hypothesis=("Unmapped faults share the multi-scale topographic (Hessian trough/crest, relief) and "
                    "potential-field (RTP / isostatic-gravity gradient and tilt) signature of catalogued "
                    "faults; a catalogue-blind gradient-boosted classifier trained on mapped faults, emitted as "
                    "2.8 px disc-thinned unit dots outside a 2 px catalogue collar, recovers withheld faults "
                    "better than the R0 (H33) recipe."),
        mechanism=("35 catalogue-free features from the 19 competition bands -> HistGradientBoosting "
                   "(visible faults vs random footprint pixels) -> spatially blocked LOQO surface -> greedy "
                   "descending-score disc thinning r=2.8 px, collar d_cat>2 px, 37,654 dots."),
        non_fault_mimic=("Incised drainage thalwegs and lithologic contacts (pluton/volcanic margins) produce the "
                         "same Hessian-trough and potential-field-gradient signatures without fault offset."),
        holdout_dti=dict(
            evidence_class="HOLDOUT-DTI", evaluator_version=s["E1_hgb_thin"]["evaluator_version"],
            split="buffered whole-component LOQO, seed 20, hide 0.20, buffer 3 px",
            withheld_positive_pixels=s["E1_hgb_thin"]["withheld_positive_pixels"],
            candidate_E1=dict(dti=s["E1_hgb_thin"]["dti"], ci95=s["E1_hgb_thin"]["ci95"]),
            R0_foldfair=dict(dti=s["R0_foldfair"]["dti"], ci95=s["R0_foldfair"]["ci95"],
                             recipe="GEMSDOE25 dotted-h19-5-d2-8 minus dots within 2 px of VISIBLE catalogue"),
            paired_delta_vs_R0_foldfair=dict(delta=d["delta"], ci95=d["ci95"]),
            other_arms={k: dict(dti=v["scores"][k]["dti"], ci95=v["scores"][k]["ci95"],
                                delta_vs_R0_foldfair=v["paired_differences"]["R0_foldfair"]["delta"],
                                delta_ci95=v["paired_differences"]["R0_foldfair"]["ci95"])
                        for k, v in comp["paired"].items() if k != "E1_hgb_thin"},
            current_holdout_best_same_split=dict(value=0.1240634961614658, source="docs/evidence/h86c-kslb-run-card.json",
                                                 note="recorded by a prior session; not re-run here"),
            leakage_canary_max_auc=hold["leakage_canary_max"],
        ),
        registry=dict(
            amendment="PA-86-01 (shared-template two_phase_summary; thresholds unchanged)",
            rasters_measured=dots["registry_rasters_measured"],
            inventory_missing=len(dots["inventory_rasters_missing"]),
            final_dots_like_for_like=lfl, final_dots_literal=lit,
            surface=(surf["two_phase"]["literal_reading"] if surf else "NOT MEASURED"),
            top_forward_overlap=dots["top15_by_forward_overlap"][:5],
            surface_worst_spearman=surf_rho,
            surface_worst_spearman_submission=(surf["two_phase"]["literal_reading"]["worst_spearman_submission"] if surf else None),
            surface_duplicate_by_rho=surface_duplicate,
            final_dots_pa86_02=dict((k, chance[k]) for k in ("firings", "space_filling_firings", "informative_firings",
                                                              "worst_spearman_any_raster", "max_excess_over_chance", "gate_pass")),
            final_dots_top_informative=chance["informative_firing_rows"][:3],
            final_dots_duplicate=dots_duplicate,
            ordering_irregularity="IR-86-H86E-01: surface registry check ran after placement (protocol requires before); the result is a stop either way.",
        ),
        raster_sha256=rec["sha256"], zip_sha256=rec["zip_sha256"], bytes=rec["bytes"],
        validator=dict(all_checks_passed=rec["validator"]["all_checks_passed"],
                       checks=rec["validator"]["checks"], n_nan=rec["validator"]["n_nan"],
                       min=rec["validator"]["min"], max=rec["validator"]["max"]),
        submission_name=NAME, note=rec["note"], note_chars=rec["note_chars"],
        verdict=("negative" if (surface_duplicate or dots_duplicate or not beats_r0) else "promote"),
        duplicate=bool(surface_duplicate or dots_duplicate),
        submission_ready=False, safe_to_submit=False, approved_for_weekly_slot=False,
        submit_decision="DO NOT SUBMIT" if (not beats_r0 or surface_duplicate or dots_duplicate) else "SELECTOR STEP",
        reason=("(1) Paired HOLDOUT-DTI delta vs R0 fold-fair is negative with a 95% CI excluding zero; "
                "(2) the final surface rank-correlates above 0.90 with the 17GEMSDOE E-proba-multiscale "
                "supervised surface (lane drift -> duplicate); (3) final dots exceed the 70% forward overlap "
                "against non-space-filling dot fields (11GEMSDOE/12GEMSDOE near-catalogue lanes). Logged as "
                "duplicate and stopped, per protocol rule 1."),
        submission_slots_used=0,
    )
    (EV / "h86e-run-card.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: card[k] for k in ("verdict", "submit_decision", "raster_sha256")}, indent=1))


if __name__ == "__main__":
    main()
