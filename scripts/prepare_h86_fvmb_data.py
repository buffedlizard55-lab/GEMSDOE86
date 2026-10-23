#!/usr/bin/env python3
"""Prepare and verify the cached 60-channel label-free H86-FVMB physical stack."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems86_fvmb.features import build_static60_memmap  # noqa: E402


def main() -> None:
    # The common literal gate is mandatory before cache construction or fitting.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.protocol_preflight import require_feasible
    require_feasible()
    mmap_path, meta = build_static60_memmap(ROOT, force=False)
    mm = np.memmap(mmap_path, dtype=np.float16, mode="r", shape=(meta["n_fp"], meta["n_channels"]))
    # Verify finite across all 5,167,373 x 60 values
    n_nonfinite = 0
    for c in range(meta["n_channels"]):
        n_nonfinite += int((~np.isfinite(mm[:, c])).sum())
    assert n_nonfinite == 0, f"Found {n_nonfinite} non-finite entries in static60_fp.f16"
    receipt_path = ROOT / "registry" / "feature_receipt.json"
    receipt = {
        "mmap_path": str(mmap_path.relative_to(ROOT)),
        "bytes": mmap_path.stat().st_size,
        "n_fp": meta["n_fp"],
        "n_channels": meta["n_channels"],
        "n_nonfinite": n_nonfinite,
        "elapsed_seconds": meta["elapsed_seconds"],
        "lidar_1m_fraction": meta["lidar_1m_fraction"],
        "wallace_3m_fraction": meta["wallace_3m_fraction"],
        "leakage_assertions": meta["leakage_assertions"],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        f"[prepare_data] OK: {meta['n_fp']:,} px x {meta['n_channels']} ch "
        f"({mmap_path.stat().st_size / 1e6:.1f} MB) in {meta['elapsed_seconds']}s; n_nonfinite=0"
    )


if __name__ == "__main__":
    main()
