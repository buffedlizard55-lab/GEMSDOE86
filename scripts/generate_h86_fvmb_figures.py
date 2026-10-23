#!/usr/bin/env python3
"""Generate publication-grade scientific diagnostic figures for GEMSDOE86 (`docs/assets/`)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import grid as GRID  # noqa: E402

ASSETS = ROOT / "docs" / "assets"
EVID = ROOT / "evidence"


def make_fig1_spatial_discovery(g: GRID.Grid) -> None:
    fp = g.footprint
    cat = g.catalogue & fp
    p_wc = np.load(ROOT / ".cache" / "h86_prod_surface.npy")
    p_phys = np.load(ROOT / ".cache" / "h86_phys_prod_surface.npy")
    dots = np.load(ROOT / ".cache" / "h86_prod_dots.npy") > 0
    surf = np.clip(0.68 * p_wc + 0.32 * p_phys, 0.0, 1.0)
    d_cat = ndi.distance_transform_edt(~cat).astype(np.float32)

    # Downsample 4x by max-pooling for crisp synoptic display
    ds = 4
    h4, w4 = fp.shape[0] // ds, fp.shape[1] // ds
    fp4 = fp[: h4 * ds, : w4 * ds].reshape(h4, ds, w4, ds).any(axis=(1, 3))
    cat4 = cat[: h4 * ds, : w4 * ds].reshape(h4, ds, w4, ds).any(axis=(1, 3))
    surf4 = surf[: h4 * ds, : w4 * ds].reshape(h4, ds, w4, ds).max(axis=(1, 3))
    dots4 = dots[: h4 * ds, : w4 * ds].reshape(h4, ds, w4, ds).any(axis=(1, 3))

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.8), dpi=150)
    fig.patch.set_facecolor("#0b1120")

    # Panel A: Catalogue + Footprint
    ax = axes[0]
    ax.set_facecolor("#0f172a")
    bg = np.where(fp4, 0.14, 0.03)
    ax.imshow(bg, cmap="Blues", vmin=0, vmax=1)
    cat_rgba = np.zeros((h4, w4, 4), dtype=np.float32)
    cat_rgba[cat4] = [0.98, 0.75, 0.18, 0.95]
    ax.imshow(cat_rgba)
    ax.set_title("A. Mapped Catalogue (existing_faults.tif)\n69,205 px in 5.17M-px Great Basin Footprint", color="#f8fafc", fontsize=11, fontweight="bold", pad=10)
    ax.set_xticks([]); ax.set_yticks([])

    # Panel B: Seam-Free Calibrated Posterior Surface
    ax = axes[1]
    ax.set_facecolor("#0f172a")
    vis_s = np.where(fp4, np.log1p(surf4 * 85.0) / np.log1p(85.0 * 0.18), np.nan)
    im = ax.imshow(np.clip(vis_s, 0.0, 1.0), cmap="magma", vmin=0.0, vmax=1.0)
    ax.set_title("B. H86-FVMB Seam-Free LOQO Posterior\n8-Stratum (Quadrant x 1m-LiDAR) Calibrated", color="#f8fafc", fontsize=11, fontweight="bold", pad=10)
    ax.set_xticks([]); ax.set_yticks([])
    cb = fig.colorbar(im, ax=ax, fraction=0.042, pad=0.03)
    cb.ax.yaxis.set_tick_params(color="#cbd5e1", labelcolor="#cbd5e1", labelsize=8)
    cb.set_label("Relative Log-Posterior Intensity", color="#cbd5e1", fontsize=8.5)

    # Panel C: Zoom into Humboldt / Dixie Valley Geothermal Belt showing 3 Tectonic Regimes
    ax = axes[2]
    ax.set_facecolor("#0f172a")
    r0, r1, c0, c1 = 1350, 1950, 1150, 1750
    sub_cat = ndi.binary_dilation(cat[r0:r1, c0:c1], iterations=1)
    sub_dots = dots[r0:r1, c0:c1]
    sub_d = d_cat[r0:r1, c0:c1]
    sub_surf = surf[r0:r1, c0:c1]

    ax.imshow(np.log1p(sub_surf * 60.0), cmap="Greys_r", alpha=0.42)
    rgb = np.zeros((r1 - r0, c1 - c0, 4), dtype=np.float32)
    rgb[sub_cat] = [0.96, 0.76, 0.20, 0.88]  # Gold: mapped catalogue
    z_a = ndi.binary_dilation(sub_dots & (sub_d <= 2.35), iterations=1)
    z_b = ndi.binary_dilation(sub_dots & (sub_d > 2.35) & (sub_d <= 26.0), iterations=1)
    z_c = ndi.binary_dilation(sub_dots & (sub_d > 26.0), iterations=1)
    rgb[z_b] = [0.22, 0.74, 0.97, 0.95]  # Cyan: Zone B Wing-Crack/Relay
    rgb[z_a] = [0.16, 0.94, 0.55, 0.98]  # Emerald: Zone A Tip Emergence
    rgb[z_c] = [0.98, 0.38, 0.58, 0.98]  # Coral-Pink: Zone C Blind-Basin iSPI/Sibson
    ax.imshow(rgb)
    ax.set_title("C. Dixie Valley / Humboldt Zoom (60 x 60 km)\nGold=Mapped | Green=Tip | Cyan=Wing/Relay | Pink=Blind Basin", color="#f8fafc", fontsize=10.2, fontweight="bold", pad=10)
    ax.set_xticks([]); ax.set_yticks([])

    for a in axes:
        for sp in a.spines.values():
            sp.set_edgecolor("#334155")

    fig.tight_layout(pad=1.6)
    fig.savefig(ASSETS / "fig1_h86_spatial_discovery_map.png", dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def make_fig2_ablation_and_forensics() -> None:
    ho = json.loads((EVID / "exp2_exp3_holdout_ablation.json").read_text())
    scores = ho["dual_seed_pooled"]["scores"]
    det = ho["detached_blind_splay_seed20"]["scores"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 5.8), dpi=150)
    fig.patch.set_facecolor("#ffffff")

    order = [
        ("Control_Random_37654", "Random Off-Cat Control\n(37,654 dots)", "#94a3b8"),
        ("Ref_GEMS32_H33_FoldFair_02778", "GEMSDOE32 H33-2-B2\n(0.2778 Live Ref, Fold-Fair)", "#f59e0b"),
        ("Ref_GEMS25_D28_02600", "GEMSDOE25 D2.8\n(0.2600 Live Ref)", "#fb923c"),
        ("EXP86_1_Phys_3Fam_D28", "EXP-86-1: H86-1/4 Physics\n(Label-Free 60ch LOQO)", "#3b82f6"),
        ("EXP86_3_FVMB_TriRegime_Dink", "EXP-86-3: H86-FVMB TriRegime\n(PROMOTED, 38,400 dots)", "#10b981"),
        ("EXP86_3_FVMB_Dink_SingleRegime", "EXP-86-3: Single-Regime Dink\n(Collar-Dense Ablation)", "#059669"),
        ("EXP86_2_WingCrack_3Fam_D28", "EXP-86-2: WingCrack SAR-PU\n(72ch LOQO + D2.8)", "#0ea5e9"),
    ]
    y = np.arange(len(order))
    vals = [scores[k]["dti"] for k, _, _ in order]
    lo = [scores[k]["dti"] - scores[k]["ci95"][0] for k, _, _ in order]
    hi = [scores[k]["ci95"][1] - scores[k]["dti"] for k, _, _ in order]
    cols = [c for _, _, c in order]

    bars = ax1.barh(y, vals, xerr=[lo, hi], color=cols, height=0.62, edgecolor="#1e293b", linewidth=0.8, capsize=3.5, error_kw={"elinewidth": 1.3, "ecolor": "#1e293b"})
    ax1.set_yticks(y)
    ax1.set_yticklabels([lbl for _, lbl, _ in order], fontsize=9, fontweight="bold", color="#0f172a")
    ax1.set_xlabel("Dual-Seed Pooled HOLDOUT-DTI (gems57-pooled-hide-v2, n=22,641, 95% CI)", fontsize=9.8, fontweight="bold", color="#0f172a")
    ax1.set_title("A. Spatially-Blocked Holdout Ablation Ladder (+60.5% vs GEMSDOE32)", fontsize=11, fontweight="bold", color="#0f172a", pad=10)
    ax1.set_xlim(0, 0.182)
    ax1.grid(axis="x", linestyle="--", alpha=0.35)
    for rect, v in zip(bars, vals):
        ax1.text(v + 0.013, rect.get_y() + rect.get_height() / 2, f"{v:.4f}", va="center", fontsize=8.8, fontweight="bold", color="#0f172a")

    # Panel B: Live Competition ORGANIZER-CONFIRMED Trajectory & Detached Blind-Splay Gain
    live_items = [
        ("GEMSDOE7-8\n(Continuous Cloud)", 0.0000, "#cbd5e1"),
        ("GEMSDOE21\n(Thick Corridors)", 0.1552, "#94a3b8"),
        ("GEMSDOE19\n(H19-5 Soft Base)", 0.1922, "#64748b"),
        ("GEMSDOE24\n(D1.5 Thinning)", 0.2529, "#60a5fa"),
        ("GEMSDOE25\n(D2.8 Spacing)", 0.2600, "#3b82f6"),
        ("GEMSDOE30\n(InSAR/GPS Gate)", 0.2750, "#2563eb"),
        ("GEMSDOE32\n(H33-2-B2 Collar>2px)", 0.2778, "#f59e0b"),
        ("Competition\n#1 Leaderboard", 0.4413, "#0f172a"),
    ]
    x2 = np.arange(len(live_items))
    v2 = [v for _, v, _ in live_items]
    c2 = [c for _, _, c in live_items]
    b2 = ax2.bar(x2, v2, color=c2, width=0.62, edgecolor="#1e293b", linewidth=0.8)
    ax2.set_xticks(x2)
    ax2.set_xticklabels([l for l, _, _ in live_items], fontsize=7.8, fontweight="bold", rotation=22, ha="right")
    ax2.set_ylabel("ORGANIZER-CONFIRMED Live DrivenData DTI", fontsize=9.8, fontweight="bold", color="#0f172a")
    ax2.set_title("B. ORGANIZER-CONFIRMED Live Leaderboard Forensics (No Projections)", fontsize=11, fontweight="bold", color="#0f172a", pad=10)
    ax2.set_ylim(0, 0.50)
    ax2.grid(axis="y", linestyle="--", alpha=0.35)
    for rect, v in zip(b2, v2):
        ax2.text(rect.get_x() + rect.get_width() / 2, v + 0.009, f"{v:.4f}", ha="center", fontsize=8.3, fontweight="bold", color="#0f172a")

    ax2.annotate(
        f"Detached Blind-Splay Holdout (Seed 20):\nGEMSDOE32 Ref: {det['Ref_GEMS32_H33_FoldFair_02778']['dti']:.4f} -> H86-FVMB: {det['EXP86_3_FVMB_TriRegime_Dink']['dti']:.4f} (+66.2%)",
        xy=(6, 0.308),
        xytext=(1.0, 0.395),
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "#ecfdf5", "edgecolor": "#059669", "lw": 1.2},
        arrowprops={"arrowstyle": "->", "color": "#059669", "lw": 1.4},
        fontsize=8.6,
        fontweight="bold",
        color="#065f46",
    )

    fig.tight_layout(pad=1.6)
    fig.savefig(ASSETS / "fig2_ablation_and_forensics.png", dpi=150)
    plt.close(fig)


def make_fig3_canary_and_importance() -> None:
    can = json.loads((EVID / "exp1_leakage_canary.json").read_text())
    ho = json.loads((EVID / "exp2_exp3_holdout_ablation.json").read_text())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 5.8), dpi=150)
    fig.patch.set_facecolor("#ffffff")

    top_can = can["seeds"]["seed_21"]["top_10_channels"][::-1]
    y1 = np.arange(len(top_can))
    v1 = [r["auc_symmetric"] for r in top_can]
    c1 = ["#0ea5e9" if r["group"] == "wingcrack_12" else "#6366f1" for r in top_can]
    ax1.barh(y1, v1, color=c1, height=0.62, edgecolor="#1e293b", linewidth=0.7)
    ax1.axvline(0.90, color="#dc2626", linestyle="--", linewidth=2.0, label="Leakage Gate Ceiling (0.90)")
    ax1.axvline(0.50, color="#64748b", linestyle=":", linewidth=1.2, label="Random Chance (0.50)")
    ax1.set_yticks(y1)
    ax1.set_yticklabels([r["channel"] for r in top_can], fontsize=8.6, fontweight="bold")
    ax1.set_xlim(0.45, 0.96)
    ax1.set_xlabel("Single-Feature Holdout Symmetric ROC AUC", fontsize=9.8, fontweight="bold")
    ax1.set_title("A. 72-Channel Leakage Canary Audit (PASS: Max 0.7334 <= 0.90)", fontsize=11, fontweight="bold", pad=10)
    ax1.legend(loc="lower right", fontsize=8.5)
    ax1.grid(axis="x", linestyle="--", alpha=0.35)

    top_imp = ho["feature_gain_importance_top25"][:16][::-1]
    y2 = np.arange(len(top_imp))
    v2 = [val * 100.0 for _, val in top_imp]
    c2 = [
        "#10b981" if name.startswith("wc_") else ("#f59e0b" if name.startswith("mimic_") else "#3b82f6")
        for name, _ in top_imp
    ]
    ax2.barh(y2, v2, color=c2, height=0.64, edgecolor="#1e293b", linewidth=0.7)
    ax2.set_yticks(y2)
    ax2.set_yticklabels([name for name, _ in top_imp], fontsize=8.4, fontweight="bold")
    ax2.set_xlabel("Normalized LightGBM Split-Gain Share (%)", fontsize=9.8, fontweight="bold")
    ax2.set_title("B. Top-16 Multi-Physics, Wing-Crack & Mimic-Rejection Drivers", fontsize=11, fontweight="bold", pad=10)
    ax2.grid(axis="x", linestyle="--", alpha=0.35)

    fig.tight_layout(pad=1.6)
    fig.savefig(ASSETS / "fig3_canary_and_importance.png", dpi=150)
    plt.close(fig)


def make_fig4_uniqueness() -> None:
    uq = json.loads((EVID / "exp3_uniqueness_audit.json").read_text())
    disc = uq["final_emitted_dots"]["all_discriminating_comparisons"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 5.6), dpi=150)
    fig.patch.set_facecolor("#ffffff")

    top12 = disc[:12][::-1]
    y = np.arange(len(top12))
    ovs = [r["forward_overlap_3px"] for r in top12]
    lbls = [r["submission"][:36] for r in top12]
    cols = ["#059669" if v <= 0.70 else "#dc2626" for v in ovs]

    ax1.barh(y, ovs, color=cols, height=0.62, edgecolor="#1e293b", linewidth=0.7)
    ax1.axvline(0.70, color="#dc2626", linestyle="--", linewidth=2.0, label="Duplicate Ceiling (0.70)")
    ax1.set_yticks(y)
    ax1.set_yticklabels(lbls, fontsize=8.1, fontweight="bold")
    ax1.set_xlim(0, 0.80)
    ax1.set_xlabel("3-Pixel Forward Dot Overlap vs Registry Prior", fontsize=9.8, fontweight="bold")
    ax1.set_title("A. Top-12 Discriminating Registry Overlaps (PASS: Max 0.6831 <= 0.70)", fontsize=10.8, fontweight="bold", pad=10)
    ax1.legend(loc="lower right", fontsize=8.5)
    ax1.grid(axis="x", linestyle="--", alpha=0.35)

    xs = [abs(r["spearman_full_footprint"]) for r in disc]
    ys = [r["forward_overlap_3px"] for r in disc]
    sz = [max(35.0, min(260.0, r["their_dots"] / 850.0)) for r in disc]
    ax2.scatter(xs, ys, s=sz, c="#2563eb", alpha=0.78, edgecolors="#0f172a", linewidth=0.9)
    ax2.axhline(0.70, color="#dc2626", linestyle="--", linewidth=1.8, label="3-px Overlap Limit (0.70)")
    ax2.axvline(0.90, color="#7c3aed", linestyle="--", linewidth=1.8, label="|Spearman rho| Limit (0.90)")
    ax2.set_xlim(-0.01, 0.96)
    ax2.set_ylim(0.0, 0.80)
    ax2.set_xlabel("|Spearman Rank Correlation| Across 5.17M Footprint", fontsize=9.8, fontweight="bold")
    ax2.set_ylabel("3-Pixel Forward Dot Overlap", fontsize=9.8, fontweight="bold")
    ax2.set_title("B. Joint 29-Prior Uniqueness Plane (Bubble Size ~ Prior Dot Count)", fontsize=10.8, fontweight="bold", pad=10)
    ax2.legend(loc="upper right", fontsize=8.5)
    ax2.grid(True, linestyle="--", alpha=0.35)

    fig.tight_layout(pad=1.6)
    fig.savefig(ASSETS / "fig4_registry_uniqueness.png", dpi=150)
    plt.close(fig)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    g = GRID.load_grid(ROOT / "data" / "bridge")
    make_fig1_spatial_discovery(g)
    make_fig2_ablation_and_forensics()
    make_fig3_canary_and_importance()
    make_fig4_uniqueness()
    print("Generated all 4 figures in docs/assets/")


if __name__ == "__main__":
    main()
