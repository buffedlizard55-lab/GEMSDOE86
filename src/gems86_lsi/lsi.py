"""H86J-LSI: live-score inversion of the hidden-truth density field.

Preregistration: ``research/H86J_LSI_PREREGISTRATION.md`` (+ ``.json``).

Every owner-reported live score is a known function of three *linear*
functionals of the unknown truth field.  For a truth probability ``lam(x)``
over the active domain ``A = footprint & ~catalogue`` and a submitted raster
``p`` (values in [0, 1]):

* ``T = <lam, c>``     with ``c(x) = max_x' p(x') k(|x - x'|)``  (truth credit)
* ``M = <lam, s> / 3`` with ``s(x) = sum_x' p(x') k(|x - x'|)``  (dot credit;
  3 = the triangular kernel summed along a line through its centre)
* ``G = <lam, 1_A>``

and the expected official metric is
``DTI = T / (0.2 T + 0.2 (n - M) + 0.8 G)`` with ``n = sum_A p``.

The field is log-linear in a small, frozen feature set and is fitted by
weighted least squares to the reported scores.  Registry rasters enter ONLY
as measurement operators (``c``, ``s``, ``n``); no raster pixel is ever copied
into a feature or a prediction.  SGMC bytes never enter this module.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi
from scipy import sparse
from scipy.optimize import minimize

from gems57.metric import ALPHA, BETA, OFF_DX, OFF_DY, OFF_K

LINE_CONSTANT = 3.0

STACK_FEATURES = ("lidar_step_max", "lidar_cross_max", "topo_hs_lineament",
                  "gradmag_dem_s1p5", "topo_relief_local", "b12_det_elev",
                  "gradmag_rtp_s1p5", "gradmag_grav_s1p5", "b04_geod_2ndinv")
SHELLS = ((0.0, 3.0), (3.0, 6.0), (6.0, 12.0), (12.0, 25.0), (25.0, 50.0))
FEATURE_NAMES = tuple(STACK_FEATURES) + ("lidar_valid_fraction",) + tuple(
    f"dcat_{int(a)}_{int(b)}" for a, b in SHELLS)


# ---------------------------------------------------------------- operators
def max_credit(p: np.ndarray) -> np.ndarray:
    """``c(x) = max_x' p(x') k(|x-x'|)`` -- the official per-truth-cell credit."""
    p = np.asarray(p, np.float32)
    out = np.zeros(p.shape, np.float32)
    H, W = p.shape
    for j, i, k in zip(OFF_DY, OFF_DX, OFF_K):
        ys0, ys1 = max(0, j), min(H, H + j)
        xs0, xs1 = max(0, i), min(W, W + i)
        np.maximum(out[ys0:ys1, xs0:xs1],
                   p[max(0, -j):min(H, H - j), max(0, -i):min(W, W - i)] * np.float32(k),
                   out=out[ys0:ys1, xs0:xs1])
    return out


def sum_credit(p: np.ndarray) -> np.ndarray:
    """``s(x) = sum_x' p(x') k(|x-x'|)`` (identical to vendor expected_credit)."""
    p = np.asarray(p, np.float32)
    out = np.zeros(p.shape, np.float32)
    H, W = p.shape
    for j, i, k in zip(OFF_DY, OFF_DX, OFF_K):
        ys0, ys1 = max(0, j), min(H, H + j)
        xs0, xs1 = max(0, i), min(W, W + i)
        out[ys0:ys1, xs0:xs1] += p[max(0, -j):min(H, H - j),
                                   max(0, -i):min(W, W - i)] * np.float32(k)
    return out


def decode(a: np.ndarray, footprint: np.ndarray, catalogue: np.ndarray) -> tuple[np.ndarray, dict]:
    """Raster bytes -> values actually scored (vendor dti semantics).

    NaN/Inf -> 0, outside footprint -> 0, catalogue pixels -> 0 (organiser
    mask).  Values outside [0,1] are clipped and *reported* (never silently).
    """
    a = np.asarray(a, np.float32)
    finite = np.isfinite(a)
    info = {"nonfinite_inside": int((~finite & footprint).sum()),
            "below0_inside": int(((a < 0) & finite & footprint).sum()),
            "above1_inside": int(((a > 1) & finite & footprint).sum())}
    v = np.where(finite, a, 0.0).astype(np.float32)
    v = np.clip(v, 0.0, 1.0)
    v[~footprint | catalogue] = 0.0
    info["n_mass"] = float(v.sum(dtype=np.float64))
    info["n_positive"] = int((v > 0).sum())
    info["binary"] = bool(np.isin(np.unique(v), (0.0, 1.0)).all())
    return v, info


@dataclass
class Operators:
    C: sparse.csr_matrix      # rasters x sample  (truth credit at sample pixels)
    S: sparse.csr_matrix      # rasters x sample  (dot credit at sample pixels)
    n: np.ndarray             # rasters  (prediction mass in A)
    frac: float               # sample fraction of A


def sample_pixels(active: np.ndarray, frac: float, seed: int) -> np.ndarray:
    idx = np.flatnonzero(active.ravel())
    rng = np.random.default_rng(seed)
    keep = rng.random(idx.size) < frac
    return idx[keep]


def raster_operator_rows(v: np.ndarray, sample: np.ndarray):
    c = max_credit(v).ravel()[sample]
    s = sum_credit(v).ravel()[sample]
    ci = np.flatnonzero(c > 0)
    si = np.flatnonzero(s > 0)
    return (ci.astype(np.int32), c[ci].astype(np.float32),
            si.astype(np.int32), s[si].astype(np.float32))


def assemble(rows: list, n: list, n_sample: int, frac: float) -> Operators:
    def mat(which):
        indptr = [0]
        ind, val = [], []
        for r in rows:
            i, v = (r[0], r[1]) if which == "C" else (r[2], r[3])
            ind.append(i)
            val.append(v)
            indptr.append(indptr[-1] + len(i))
        return sparse.csr_matrix((np.concatenate(val).astype(np.float64),
                                  np.concatenate(ind), np.array(indptr)),
                                 shape=(len(rows), n_sample))
    return Operators(C=mat("C"), S=mat("S"), n=np.asarray(n, np.float64), frac=float(frac))


# ---------------------------------------------------------------- features
def rank01(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros(a.shape, np.float32)
    vals = np.asarray(a, np.float32)[mask]
    order = np.argsort(vals, kind="stable")
    r = np.empty(len(vals), np.float32)
    r[order] = np.linspace(0.0, 1.0, len(vals), dtype=np.float32)
    out[mask] = r
    return out


def feature_planes(stack, names, footprint, lidar_valid, catalogue_in_force):
    """Yield (name, plane) for the 15 frozen features; catalogue shells use the
    catalogue *in force* (full for live/SGMC, visible-only for the holdout)."""
    idx = {n: i for i, n in enumerate(names)}
    for f in STACK_FEATURES:
        yield f, rank01(np.asarray(stack[idx[f]]), footprint)
    yield "lidar_valid_fraction", np.where(footprint, lidar_valid, 0).astype(np.float32)
    d = ndi.distance_transform_edt(~catalogue_in_force).astype(np.float32)
    for a, b in SHELLS:
        yield f"dcat_{int(a)}_{int(b)}", ((d > a) & (d <= b)).astype(np.float32)


# ---------------------------------------------------------------- model
@dataclass
class Standardiser:
    mu: np.ndarray
    sd: np.ndarray

    def __call__(self, F: np.ndarray) -> np.ndarray:
        return (F - self.mu) / self.sd


def design(F: np.ndarray) -> np.ndarray:
    return np.hstack([np.ones((F.shape[0], 1)), F])


def predict_terms(theta: np.ndarray, X: np.ndarray, ops: Operators, rows=None):
    lam = np.exp(np.clip(X @ theta, -50, 5))
    C = ops.C if rows is None else ops.C[rows]
    S = ops.S if rows is None else ops.S[rows]
    n = ops.n if rows is None else ops.n[rows]
    T = C @ lam / ops.frac
    M = S @ lam / (LINE_CONSTANT * ops.frac)
    G = lam.sum() / ops.frac
    D = ALPHA * T + ALPHA * (n - M) + BETA * G
    return T / D, dict(T=T, M=M, G=G, D=D, lam=lam, C=C, S=S, n=n)


def loss_grad(theta, X, ops, y, w, ridge, rows):
    dti, t = predict_terms(theta, X, ops, rows)
    lamX = X * t["lam"][:, None]
    dT = (t["C"] @ lamX) / ops.frac
    dM = (t["S"] @ lamX) / (LINE_CONSTANT * ops.frac)
    dG = lamX.sum(axis=0) / ops.frac
    dD = ALPHA * dT - ALPHA * dM + BETA * dG[None, :]
    ddti = (dT * t["D"][:, None] - t["T"][:, None] * dD) / (t["D"][:, None] ** 2)
    r = dti - y
    L = float(np.sum(w * r * r) + ridge * np.sum(theta[1:] ** 2))
    g = 2.0 * (w * r) @ ddti
    g[1:] += 2.0 * ridge * theta[1:]
    return L, g


def fit(X, ops, y, w, *, ridge=1e-3, rows=None, theta0=None, maxiter=500):
    if theta0 is None:
        theta0 = np.zeros(X.shape[1])
        theta0[0] = np.log(0.004)
    rows = np.arange(len(y)) if rows is None else np.asarray(rows)
    # slice once; CSC makes the sparse x dense(16) products ~3.5x faster (exact)
    sub = Operators(C=ops.C[rows].tocsc(), S=ops.S[rows].tocsc(), n=ops.n[rows], frac=ops.frac)
    res = minimize(loss_grad, theta0, args=(X, sub, y[rows], w[rows], ridge, None),
                   jac=True, method="L-BFGS-B", options={"maxiter": maxiter})
    return res.x, {"success": bool(res.success), "nit": int(res.nit),
                   "loss": float(res.fun), "message": str(res.message)}


def fit_constant(X, ops, y, w, rows=None):
    X1 = X[:, :1]
    theta, info = fit(X1, ops, y, w, ridge=0.0, rows=rows)
    return theta, info


def expected_dti_of(v: np.ndarray, lam_full: np.ndarray, active: np.ndarray) -> dict:
    """Exact (full-field, no sampling) LSI expected metric of one raster."""
    v = np.where(active, v, 0).astype(np.float32)
    lam = np.where(active, lam_full, 0).astype(np.float64)
    T = float((max_credit(v).astype(np.float64) * lam).sum())
    M = float((sum_credit(v).astype(np.float64) * lam).sum()) / LINE_CONSTANT
    G = float(lam.sum())
    n = float(v.sum(dtype=np.float64))
    D = ALPHA * T + ALPHA * (n - M) + BETA * G
    return {"T": T, "M": M, "G": G, "n": n, "lsi_projection": T / D if D > 0 else 0.0}
