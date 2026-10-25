"""Scored-fleet assembly and max-kernel coverage (H86J-LLP E1).

A scored raster ``r`` with live score ``s_r`` constrains the hidden truth only
through the official functional::

    T_r = sum_{g in G} c_r(g),   c_r(g) = max_{|x-g|<3} p_r(x) k(|x-g|)
    F_r = sum_x p_r(x) (1 - q(x)),            DTI = T/(0.2T + 0.2F + 0.8|G|)

For a truth *intensity* ``lambda`` (independent Bernoulli truth pixels) the
expectation of ``T_r`` is exactly linear: ``E[T_r] = sum_g lambda(g) c_r(g)``.
This module computes ``c_r`` on a fixed uniform subsample ``S`` of the scored
domain (footprint minus catalogue -- the live mask is pixel-exact) and the
prediction mass ``P_r``.  Scores are OWNER-REPORTED inputs, never outputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from pathlib import Path

import numpy as np
import rasterio

SUBSAMPLE_FRACTION = 0.25
SUBSAMPLE_SEED = 860310
_OFFS = [(j, i, 1.0 - np.hypot(j, i) / 3.0)
         for j in range(-3, 4) for i in range(-3, 4) if np.hypot(j, i) < 3.0]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as s:
        for c in iter(lambda: s.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def coverage(p: np.ndarray) -> np.ndarray:
    """``c(g) = max_x p(x) k(|x-g|)`` on the full grid (float32, no wrap)."""
    p = np.asarray(p, np.float32)
    out = np.zeros_like(p)
    H, W = p.shape
    for j, i, k in _OFFS:
        ys0, ys1 = max(0, j), min(H, H + j)
        xs0, xs1 = max(0, i), min(W, W + i)
        np.maximum(out[ys0:ys1, xs0:xs1],
                   p[max(0, -j):min(H, H - j), max(0, -i):min(W, W - i)] * np.float32(k),
                   out=out[ys0:ys1, xs0:xs1])
    return out


def subsample(domain: np.ndarray) -> np.ndarray:
    """Fixed uniform subsample (flat indices, sorted) of the scored domain."""
    flat = np.flatnonzero(np.asarray(domain, bool).ravel())
    rng = np.random.default_rng(SUBSAMPLE_SEED)
    take = rng.choice(flat.size, size=int(round(SUBSAMPLE_FRACTION * flat.size)), replace=False)
    return np.sort(flat[take])


_ENC = re.compile(r"([-_](nan|zeros|zero|allfinite|nanoutside|nan-outside|hard|candidate))+$")


def _norm(name: str) -> str:
    """Lower-case basename without extension or trailing encoding suffixes."""
    s = os.path.basename(name).lower()
    s = re.sub(r"\.(tif|tiff|zip)$", "", s)
    return _ENC.sub("", s)


def scored_candidates(root: Path) -> list[dict]:
    """Exact-basename join of OWNER-REPORTED scores to locally verified bytes.

    A name matches a file when the file basename equals the name, or equals the
    name with a site prefix (``gems28-``/``gemsdoe32-``...) and/or an encoding
    suffix (``-nan``/``-zeros``/``-allfinite``...).  Ambiguous names (several
    distinct in-footprint contents) are dropped and logged, never guessed.
    """
    scores = list(csv.DictReader((root / "registry/prior_scores.csv").open()))
    inv = json.loads((root / "research/upstream/registry_inventory.json").read_text())["rasters"]
    files: list[tuple[str, Path, str]] = []
    for r in inv:
        f = root / "data/registry_ext" / f"{r['sha256']}.tif"
        if f.is_file():
            for s in r["sources"]:
                files.append((_norm(s.split(":", 1)[1]), f, s))
    for f in sorted((root / "data/scored_fleet").glob("*.tif")):
        files.append((_norm(f.name.split("__", 1)[1]), f, f"GEMSDOE86-local:{f.relative_to(root)}"))
    for f in sorted((root / "data/scored_ext").glob("*.tif")):
        files.append((_norm(f.name.split("__", 1)[1]), f, f"GEMSDOE86-scored-ext:{f.relative_to(root)}"))
    out = []
    for row in scores:
        nm = _norm(row["submission"].strip())
        if not nm or not row["score"]:
            continue
        pat = re.compile(r"^([a-z0-9]+[-_])?" + re.escape(nm) + r"$")
        hits = sorted({(str(f), src) for (b, f, src) in files if pat.match(b)})
        out.append(dict(site=row["site"], submission=row["submission"], score=float(row["score"]),
                        evidence_class=row["evidence_class"], files=[h[0] for h in hits],
                        sources=[h[1] for h in hits]))
    return out


def load_prediction(path: Path, footprint: np.ndarray, catalogue: np.ndarray) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as ds:
        a = ds.read(1).astype(np.float32)
        info = dict(shape=list(a.shape), crs=str(ds.crs))
    if a.shape != footprint.shape:
        raise ValueError(f"grid mismatch {a.shape}")
    bad = ~np.isfinite(a)
    a[bad] = 0.0
    n_out = int(((a < 0) | (a > 1)).sum())
    a = np.clip(a, 0.0, 1.0)
    a[~footprint] = 0.0
    a[catalogue] = 0.0          # pixel-exact live mask (forum 11516)
    info.update(clipped_cells=n_out, positive=int((a > 0).sum()),
                binary=bool(np.isin(a[a > 0], (1.0,)).all()), mass=float(a.sum(dtype=np.float64)))
    return a, info


def content_key(a: np.ndarray) -> str:
    """Hash of in-domain content (encoding-independent: NaN vs zeros outside)."""
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
