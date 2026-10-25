"""Learning from label proportions: fit a truth intensity to live scores.

Model (preregistered, ``research/H86J_LLP_PREREGISTRATION.md``)::

    lambda(x) = exp(b + theta . (phi(x) - mean_phi))       truth px per px
    E[T_r]    = sum_g lambda(g) c_r(g)                      exact in expectation
    E[M_r]   ~= sum_x p_r(x) min(1, 3 lambda(x))            line-process max-kernel
    G         = sum_g lambda(g)
    s_hat_r   = T_r / (0.2 T_r + 0.2 (P_r - M_r) + 0.8 G)   official DTI form

``3 lambda`` is the expected max kernel weight at a point for a sparse random
line process with length density ``lambda`` (two-sided strip integral of the
triangular kernel: 2 * lambda * 1.5).  It also gives the right T/M ~= 3 ratio
for an isolated dot on a line.  All sums are evaluated on a fixed uniform
subsample and scaled by the inverse sampling fraction.

The preregistration's draft heuristic ``M ~= T/2.6`` holds for dot fields
only; for a continuous raster T/M ~= 1/3.  The line-process form is exact in
the same small-lambda limit for both, and the deviation is recorded as
Amendment A1 in the preregistration before any fit was run.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy import sparse
from scipy.optimize import minimize

ALPHA, BETA = 0.2, 0.8
STACK_FEATURES = ("gradmag_dem_s1p5", "b19_det_elev_slope", "lidar_step_max", "lidar_cross_max",
                  "topo_hs_lineament", "topo_curv_prof_absmax", "gradmag_rtp_s1p5", "analytic_signal_log",
                  "gradmag_grav_s1p5", "b15_log_depth_base", "b04_geod_2ndinv", "b10_log_deq",
                  "b17_cond_surf", "b06_tc_radiometric")
DERIVED = ("h86g_L_corroboration", "tophat_L_5x5", "hgb_catalogue_signature_posterior")
DIST_EDGES = ((0, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 64))
CAT_FEATURES = tuple(f"dcat_{a}_{b}" for a, b in DIST_EDGES) + ("log_catdensity_r25",)
ALL_FEATURES = STACK_FEATURES + DERIVED + CAT_FEATURES
DIST_ONLY = CAT_FEATURES


def rank01(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros(a.shape, np.float32)
    vals = np.asarray(a, np.float32)[mask]
    order = np.argsort(vals, kind="stable")
    r = np.empty(vals.size, np.float32)
    r[order] = np.linspace(0.0, 1.0, vals.size, dtype=np.float32)
    out[mask] = r
    return out


def tophat(a: np.ndarray, size: int = 5) -> np.ndarray:
    return (a - ndi.uniform_filter(a.astype(np.float32), size=size, mode="nearest")).astype(np.float32)


def catalogue_features(cat: np.ndarray) -> dict[str, np.ndarray]:
    """Distance bands + log density from the catalogue *passed in* (visible-only
    in the holdout, full catalogue for the live fit / final build)."""
    d = ndi.distance_transform_edt(~np.asarray(cat, bool)).astype(np.float32)
    out = {f"dcat_{a}_{b}": ((d > a) & (d <= b)).astype(np.float32) for a, b in DIST_EDGES}
    dens = ndi.uniform_filter(np.asarray(cat, np.float32), size=51, mode="constant")
    out["log_catdensity_r25"] = np.clip((np.log10(dens + 1e-4) + 4.0) / 4.0, 0.0, 1.0).astype(np.float32)
    out["_dcat"] = d
    return out


class LLPModel:
    """Ridge-penalised logit-score least squares on a fixed subsample."""

    def __init__(self, X: np.ndarray, C: sparse.csr_matrix, Pm: sparse.csr_matrix,
                 mass: np.ndarray, scores: np.ndarray, scale: float, names: list[str]):
        self.mu = X.mean(axis=0)
        self.X = (X - self.mu).astype(np.float64)
        self.C, self.Pm = C.tocsr(), Pm.tocsr()
        self.mass = np.asarray(mass, np.float64)
        self.s = np.clip(np.asarray(scores, np.float64), 1e-4, 1 - 1e-4)
        self.f = float(scale)
        self.names = list(names)

    def lam(self, w):
        return np.exp(np.clip(w[0] + self.X @ w[1:], -30, 5))

    def predict(self, w, rows=None):
        lam = self.lam(w)
        C = self.C if rows is None else self.C[rows]
        Pm = self.Pm if rows is None else self.Pm[rows]
        mass = self.mass if rows is None else self.mass[rows]
        T = self.f * (C @ lam)
        q = np.minimum(1.0, 3.0 * lam)
        M = self.f * (Pm @ q)
        G = self.f * lam.sum()
        F = np.maximum(mass - M, 0.0)
        D = ALPHA * T + ALPHA * F + BETA * G
        return T / D, dict(T=T, M=M, G=G, F=F)

    def _sliced(self, rows):
        key = rows.tobytes() if isinstance(rows, np.ndarray) else bytes(np.asarray(rows).tobytes())
        if getattr(self, "_cache_key", None) != key:
            self._cache_key = key
            self._cache = (self.C[rows], self.Pm[rows], self.C[rows].T.tocsr(), self.Pm[rows].T.tocsr(),
                           self.mass[rows], self.s[rows])
        return self._cache

    def loss_grad(self, w, rows, rho):
        lam = self.lam(w)
        C, Pm, CT, PmT, mass, s = self._sliced(np.asarray(rows))
        T = self.f * (C @ lam)
        q = np.minimum(1.0, 3.0 * lam)
        M = self.f * (Pm @ q)
        G = self.f * lam.sum()
        Fp = mass - M
        F = np.maximum(Fp, 0.0)
        D = ALPHA * T + ALPHA * F + BETA * G
        sh = np.clip(T / D, 1e-6, 1 - 1e-6)
        e = np.log(sh / (1 - sh)) - np.log(s / (1 - s))
        loss = float(e @ e) + rho * float(w[1:] @ w[1:])
        # derivatives of s_hat wrt T, M, G
        dsdT = (D - T * ALPHA) / D ** 2
        dsdM = np.where(Fp > 0, T * ALPHA / D ** 2, 0.0)       # F = mass - M
        dsdG = -T * BETA / D ** 2
        coef = 2 * e / (sh * (1 - sh))                          # dloss/ds_hat
        a = coef * dsdT                                         # per-row weights
        bm = coef * dsdM
        cg = float((coef * dsdG).sum())
        # dT_r/dw = f * C_r . (lam * [1, X]);  dM_r/dw = f * Pm_r . (3 lam 1[3lam<1] * [1, X])
        uT = np.asarray(CT @ a).ravel() * lam                  # per-pixel weights
        uM = np.asarray(PmT @ bm).ravel() * np.where(3 * lam < 1, 3 * lam, 0.0)
        u = self.f * (uT + uM + cg * lam)
        g = np.empty_like(w)
        g[0] = u.sum()
        g[1:] = self.X.T @ u + 2 * rho * w[1:]
        return loss, g

    def fit(self, rows=None, rho=1.0, w0=None, maxiter=400):
        rows = np.arange(len(self.s)) if rows is None else np.asarray(rows)
        if w0 is None:
            w0 = np.zeros(self.X.shape[1] + 1)
            w0[0] = np.log(12_500 / (self.f * self.X.shape[0]))
        res = minimize(self.loss_grad, w0, args=(rows, rho), jac=True, method="L-BFGS-B",
                       options=dict(maxiter=maxiter, gtol=1e-7))
        return res.x, res
