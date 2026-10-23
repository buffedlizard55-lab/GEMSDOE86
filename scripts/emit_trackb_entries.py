#!/usr/bin/env python3
"""Emit ``ledger/variants_trackb_hybrid.json`` from ``evidence/trackb_hybrid_20261023.json``.

``ledger/submissions.csv`` is written ONLY by ``scripts/build_ledger.py`` reading
``ledger/variants*.json``.  Every number here is labelled ``MODEL`` or ``PROXY``;
``receipt_score`` is empty and ``slot_candidate`` is ``false`` (Phase 2 / Track B).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "evidence" / "trackb_hybrid_20261023.json"
OUT = ROOT / "ledger" / "variants_trackb_hybrid.json"
BRANCH_URL = "https://github.com/buffedlizard55-lab/GEMSDOE86/tree/arena/ac0bd04f-gemsdoe86"


def main() -> int:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    sgmc = card["report_only_instruments"]["sgmc_off_catalogue_model"]
    proxy = card["report_only_instruments"]["catalogue_hide_and_recover_proxy"]
    ctrl_delta = sgmc["arms"]["control_random1dot"]["delta_vs_r0"]

    entries: list[dict] = []
    for value in ("cull1dot", "bridge1km", "rendertop120"):
        rec = card["variants"][value]
        pre = card["preregistered_mechanism_cards"][value]
        diff = rec["diff"]
        sg = sgmc["arms"][value]
        pr = proxy["variants"][value]

        pred_summary = (
            f"Pre-registered {pre['predicted_live_change']}; post-build SGMC off-catalogue "
            f"MODEL delta {sg['delta_vs_r0']:+.4f} (>3px collar {sg['delta_gt3px_vs_r0']:+.4f}; "
            f"+/-6px shift mean {sg['delta_shift_pm6px_mean_vs_r0']:+.4f}), 4-fold catalogue "
            f"PROXY {pr['pooled_proxy_dti']:.5f} (95% CI [{pr['bootstrap_95ci'][0]:.5f}, "
            f"{pr['bootstrap_95ci'][1]:.5f}], n={pr['n_withheld_catalogue_positives']}). "
            f"Phase 2 Track B arm (not a weekly-slot candidate unless human decides). "
            f"Falsifier: {pre['falsifier']}"
        )

        entries.append({
            "site": "GEMSDOE86",
            "id": rec["variant_id"],
            "parent": rec["parent"],
            "axis": "trackb",
            "value": value,
            "encoding": "nan",
            "n_dots": int(diff["n_dots_variant"]),
            "pct_changed": float(diff["pct_changed"]),
            "sha256": rec["nan_sha256"],
            "sha8": rec["dot8"],
            "sha256_zeros": rec["zeros_sha256"],
            "files": [rec["nan_path"], rec["zeros_path"]],
            "status": "BUILT",
            "slot_candidate": False,
            "predicted_change": pred_summary,
            "source_url": BRANCH_URL,
            "diff": {
                "n_parent": int(diff["n_dots_parent"]),
                "n_candidate": int(diff["n_dots_variant"]),
                "removed": int(diff["removed"]),
                "added": int(diff["added"]),
                "pct_of_parent_changed": float(diff["pct_changed"]),
                "count_exact": int(diff["n_dots_variant"]) == int(diff["n_dots_parent"]),
                "axis_note": diff["rule"],
            },
            "model": {
                "instrument": "USGS SGMC off-catalogue exact DTI (gems57.metric.dti_binary), RELIEF/SPACING convention",
                "dti": sg["dti"],
                "delta": sg["delta_vs_r0"],
                "delta_gt3px_collar": sg["delta_gt3px_vs_r0"],
                "translated_mean_delta": sg["delta_shift_pm6px_mean_vs_r0"],
                "quadrant_positive": f"{sg['quadrants_beating_r0']}/4",
                "control_random1dot_delta": ctrl_delta,
                "evidence_class": "MODEL",
            },
            "proxy": pr,
            "gates_passed": True,
            "receipt_score": "",
        })

    OUT.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(entries)} TRACKB entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
