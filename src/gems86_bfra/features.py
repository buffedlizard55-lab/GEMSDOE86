"""Translation-invariant 32-plane static feature stack builder for Lane H86Q-BFRA.

Extends the verified 26-plane TCWB physics stack with 6 untried Great Basin
subsurface/piedmont/remanence planes:
  1. ``bfra_flexural_shear_d3zb``: Broken-plate basement third directional derivative ``-d^3_{nnn} Z_b``
  2. ``bfra_flexural_shear_pullback``: Up-dip Salem ``cot(dip)`` migrated ``-d^3_{nnn} Z_b``
  3. ``bfra_rollover_concavity_pullback``: Up-dip migrated hanging-wall rollover ``-d^2_{nn} Z_b``
  4. ``bfra_regolith_felsic_unmix_jump``: Two-endmember piedmont provenance jump ``|Delta ln((K*U)/Th^2)|``
  5. ``bfra_hydro_k_over_th_metasom``: Hydrothermal ``K/Th`` metasomatic excess x ``Band 17`` conductivity
  6. ``bfra_tmi_rtp_remanence_disloc``: Up-dip migrated ``Bands 1/2/14`` TRM phase dislocation
"""

from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
from numpy.lib.format import open_memmap
import rasterio

from src.gems86_slcq.operators import (
    adaptive_vector_updip_pullback,
    salem_adaptive_dip_and_sharpness,
)
from src.gems86_stdp.features import (
    ABLATION_LOCAL_NAMES,
    _geodawn_seam_keep_mask,
    _rank01,
    _read_ext,
    _read_native,
    _robust_pos_z,
)
from src.gems86_tcwb.features import (
    TCWB_ELASTIC_NAMES,
    TCWB_STATIC_NAMES,
    build_tcwb_static_stack,
    verify_tcwb_input_contract,
)
from .operators import (
    broken_plate_flexural_shear_and_rollover,
    regolith_and_metasomatic_unmixing,
    tmi_vs_rtp_remanence_dislocation,
)

BFRA_NEW_NAMES: tuple[str, ...] = (
    "bfra_flexural_shear_d3zb",
    "bfra_flexural_shear_pullback",
    "bfra_rollover_concavity_pullback",
    "bfra_regolith_felsic_unmix_jump",
    "bfra_hydro_k_over_th_metasom",
    "bfra_tmi_rtp_remanence_disloc",
)

BFRA_STATIC_NAMES: tuple[str, ...] = BFRA_NEW_NAMES + TCWB_STATIC_NAMES
BFRA_ELASTIC_NAMES: tuple[str, ...] = TCWB_ELASTIC_NAMES


def verify_bfra_input_contract(ext_dir: Path | None = None) -> dict:
    """Verify all 19 native competition bands and SHA-256 external pins."""
    qc = verify_tcwb_input_contract(ext_dir)
    verified = dict(qc.get("verified_native_bands", {}))
    verified["1"] = "mag_anom"
    verified["14"] = "tmi"
    qc["verified_native_bands"] = dict(sorted(verified.items(), key=lambda kv: int(kv[0])))
    return qc


def build_bfra_static_stack(
    feature_tif: Path,
    ext_dir: Path,
    *,
    out_bfra_path: Path | None = None,
    out_ablation_path: Path | None = None,
    base_tcwb_cache_path: Path | None = None,
    footprint: np.ndarray | None = None,
) -> dict[str, object]:
    """Stream all 32 H86Q-BFRA static planes + 8 pixel-local ablation planes +
    ``L_bfra`` multi-physics corroboration prior + ``cover_propensity``."""
    base = build_tcwb_static_stack(
        feature_tif,
        ext_dir,
        out_tcwb_path=base_tcwb_cache_path,
        out_ablation_path=out_ablation_path,
        footprint=footprint,
    )
    valid = np.asarray(base["valid"], dtype=bool)
    H, W = valid.shape
    n_new = len(BFRA_NEW_NAMES)
    n_tot = len(BFRA_STATIC_NAMES)

    if out_bfra_path is not None:
        out_bfra_path.parent.mkdir(parents=True, exist_ok=True)
        X_bfra = open_memmap(out_bfra_path, mode="w+", dtype=np.float16, shape=(n_tot, H, W))
    else:
        X_bfra = np.zeros((n_tot, H, W), dtype=np.float16)

    # Copy verified 26 TCWB planes into slots [6..32)
    X_bfra[n_new:, :, :] = base["X_tcwb"][:, :, :]

    def _put_new(name: str, arr: np.ndarray) -> None:
        idx = BFRA_NEW_NAMES.index(name)
        z = _robust_pos_z(arr, valid)
        X_bfra[idx] = np.clip(z, -32.0, 32.0).astype(np.float16)

    seam_keep = _geodawn_seam_keep_mask(ext_dir, valid)
    z_m = _read_ext(ext_dir, "dem10_chi_100m_i16.tif", 5, valid)
    lahontan_band = np.exp(-(((z_m - 1330.0) / 18.0) ** 2)) + 0.65 * np.exp(
        -(((z_m - 1205.0) / 15.0) ** 2)
    )
    lahontan_band = np.where(valid & (z_m > 900.0), lahontan_band, 0.0).astype(np.float32)
    del z_m

    with rasterio.open(feature_tif) as ds:
        zb_m = _read_native(ds, 15, valid)
        b13 = _read_native(ds, 13, valid)
        b11 = _read_native(ds, 11, valid)
        b18 = _read_native(ds, 18, valid)
        b2 = _read_native(ds, 2, valid)
        b1 = _read_native(ds, 1, valid)
        b14 = _read_native(ds, 14, valid)

        _, _, g_cr, g_cc = salem_adaptive_dip_and_sharpness(
            b13, zb_m, valid, z1_m=150.0, z2_m=750.0
        )
        del b13
        _, _, m_cr, m_cc = salem_adaptive_dip_and_sharpness(
            b2, zb_m, valid, z1_m=150.0, z2_m=750.0
        )
        cot_r = (0.64 * g_cr + 0.36 * m_cr * seam_keep).astype(np.float32)
        cot_c = (0.64 * g_cc + 0.36 * m_cc * seam_keep).astype(np.float32)
        del g_cr, g_cc, m_cr, m_cc

        # 1. Broken-plate flexural shear (-d^3_{nnn} Z_b) + rollover concavity (-d^2_{nn} Z_b)
        d3_shear, rollover_raw, nr_basin, nc_basin = broken_plate_flexural_shear_and_rollover(
            zb_m, b11, b18, valid, sigmas_px=(3.0, 5.0)
        )
        del b11, b18
        d3_pull = adaptive_vector_updip_pullback(d3_shear, zb_m, cot_r, cot_c, valid)
        roll_pull = adaptive_vector_updip_pullback(rollover_raw, zb_m, cot_r, cot_c, valid)
        del rollover_raw
        _put_new("bfra_flexural_shear_d3zb", d3_shear)
        _put_new("bfra_flexural_shear_pullback", d3_pull)
        _put_new("bfra_rollover_concavity_pullback", roll_pull)

        # 2. Oblique Vector-TMI-vs-RTP Remanence Phase Dislocation (Bands 1, 2, 14)
        rem_raw = tmi_vs_rtp_remanence_dislocation(
            b14, b2, b1, nr_basin, nc_basin, valid, seam_keep=seam_keep
        )
        del b14, b2, b1, nr_basin, nc_basin
        rem_pull = adaptive_vector_updip_pullback(rem_raw, zb_m, cot_r, cot_c, valid)
        del rem_raw, zb_m, cot_r, cot_c
        _put_new("bfra_tmi_rtp_remanence_disloc", rem_pull)

        # 3. Two-endmember piedmont regolith unmixing & hydrothermal K/Th metasomatism
        b6_tc = _read_native(ds, 6, valid)
        b12 = _read_native(ds, 12, valid)
        b19 = _read_native(ds, 19, valid)
        b17 = _read_native(ds, 17, valid)

    rad_k = _read_ext(ext_dir, "geodawn_rad_u8.tif", 1, valid) + 1.0
    rad_th = _read_ext(ext_dir, "geodawn_rad_u8.tif", 2, valid) + 1.0
    rad_u = _read_ext(ext_dir, "geodawn_rad_u8.tif", 3, valid) + 1.0
    reg_jump, hydro_meta = regolith_and_metasomatic_unmixing(
        b6_tc,
        rad_k,
        rad_th,
        rad_u,
        b12,
        b19,
        b17,
        valid,
        seam_keep=seam_keep,
        lahontan_band=lahontan_band,
        standoff_px=4.0,
    )
    del b6_tc, rad_k, rad_th, rad_u, b12, b19, b17, seam_keep, lahontan_band
    _put_new("bfra_regolith_felsic_unmix_jump", reg_jump)
    _put_new("bfra_hydro_k_over_th_metasom", hydro_meta)

    fam_bfra_new = (
        0.26 * _rank01(d3_pull, valid)
        + 0.14 * _rank01(d3_shear, valid)
        + 0.16 * _rank01(roll_pull, valid)
        + 0.18 * _rank01(rem_pull, valid)
        + 0.14 * _rank01(reg_jump, valid)
        + 0.12 * _rank01(hydro_meta, valid)
    ).astype(np.float32)
    del d3_pull, d3_shear, roll_pull, rem_pull, reg_jump, hydro_meta

    L_bfra = _rank01(
        (0.64 * np.asarray(base["L_tcwb"], dtype=np.float32) + 0.36 * fam_bfra_new), valid
    )
    del fam_bfra_new
    gc.collect()

    if out_bfra_path is not None:
        X_bfra.flush()
        del X_bfra
        X_bfra = np.load(out_bfra_path, mmap_mode="r")

    qc = dict(base["qc"])
    verified = dict(qc.get("verified_native_bands", {}))
    verified["1"] = "mag_anom"
    verified["14"] = "tmi"
    qc["verified_native_bands"] = dict(sorted(verified.items(), key=lambda kv: int(kv[0])))

    return {
        "X_bfra": X_bfra,
        "X_abl": base["X_abl"],
        "L_bfra": L_bfra,
        "cover_propensity": base["cover_propensity"],
        "valid": valid,
        "qc": qc,
    }
