"""Five-kilometre CONCENTRATION dose ladder on the pinned R0 parent.

This module deliberately reuses :mod:`gems86_axis.variants` for the prior and
placement rule.  The only experimental changes from the merged 1 km arm are the
50 x 50 px (5 km) block size, the 10/15/20 percent doses, and the brief's >=3 px
clearance for *newly emitted* mass.  Inherited R0 dots retain their geometry;
R0 itself has 2,171 dots at 2--3 px, so pruning those would be a second axis
(IR-86-RELIEF-02).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from gems86_axis import variants

BLOCK_PX = 50
DOSES = (0.10, 0.15, 0.20)
DEST_BLOCK_FRAC = 0.20
NEW_MASS_CLEARANCE_PX = 3.0
PARENT_MIN_SPACING_PX = 2.8284271247461903
AXIS = "CONCENTRATION"


def value_for(frac: float) -> str:
    return f"b5km-move{int(round(100 * frac))}"


def make_prior(ctx: dict, tmi_grad: np.ndarray, block_px: int = BLOCK_PX) -> dict:
    """Use the merged 1 km arm's exact two-term block-prior implementation."""
    return variants.block_prior(ctx, {"tmi_grad": tmi_grad}, ctx["catalogue"],
                                block_px=block_px)


def build(parent: np.ndarray, ctx: dict, prior: np.ndarray, frac: float,
          *, block_px: int = BLOCK_PX) -> tuple[np.ndarray, dict]:
    """Build one count-fixed low-prior -> high-prior relocation arm."""
    if frac not in DOSES:
        raise ValueError(f"unregistered dose {frac}; expected one of {DOSES}")
    mask, stats = variants.concentration(
        parent, ctx, {}, prior, frac, NEW_MASS_CLEARANCE_PX,
        PARENT_MIN_SPACING_PX, block_px=block_px,
        dest_block_frac=DEST_BLOCK_FRAC)
    diff = variants.parent_diff(parent, mask, ctx["footprint"])
    if stats["moved_shortfall"] or diff["count_delta"] != 0:
        raise ValueError(f"{value_for(frac)}: fixed-count placement failed: {stats}")
    if diff["dropped"] != stats["moved_placed"] or diff["added"] != stats["moved_placed"]:
        raise ValueError(f"{value_for(frac)}: vacated-cell reuse changed the requested dose: {diff} / {stats}")
    if stats["placed_at_relaxed_spacing"]:
        raise ValueError(f"{value_for(frac)}: placement changed the spacing axis")
    if not 1.0 <= diff["pct_changed_of_parent"] <= 50.0:
        raise ValueError(f"{value_for(frac)}: changed-cell percentage outside 1--50%")
    if int((mask & ctx["catalogue"]).sum()):
        raise ValueError(f"{value_for(frac)}: catalogue mass emitted")
    prior_px = variants.block_to_pixels(prior, parent.shape, block_px)
    unclassified_parent = parent & ctx["footprint"] & ~np.isfinite(prior_px)
    unclassified_dropped = parent & ~mask & ~np.isfinite(prior_px)
    if unclassified_dropped.any():
        raise ValueError(f"{value_for(frac)}: unclassified edge-strip dots entered the source draw")
    stats["parent_dots_outside_complete_prior_blocks"] = int(unclassified_parent.sum())
    stats["dropped_dots_outside_complete_prior_blocks"] = int(unclassified_dropped.sum())
    stats["density_domain"] = "complete blocks only; partial edge strips excluded, not treated as low prior"
    stats["value"] = value_for(frac)
    stats["pct_parent_dots_moved"] = round(100.0 * stats["moved_placed"] / int(parent.sum()), 6)
    stats["clearance_px_new_mass"] = NEW_MASS_CLEARANCE_PX
    return mask, stats


def new_mass_clearance(parent: np.ndarray, mask: np.ndarray,
                       catalogue: np.ndarray) -> dict:
    """Check the >=3 px hard constraint on every cell this session adds."""
    new = mask & ~parent
    edt = ndi.distance_transform_edt(~catalogue)
    minimum = float(edt[new].min()) if new.any() else None
    passed = bool(new.any() and minimum is not None and minimum > NEW_MASS_CLEARANCE_PX)
    return {"passed": passed, "n_new": int(new.sum()),
            "minimum_px": round(minimum, 6) if minimum is not None else None,
            "required_strictly_greater_than_px": NEW_MASS_CLEARANCE_PX,
            "inherited_parent_dots_at_2_to_3px": int((parent & (edt > 2.0) & (edt <= 3.0)).sum())}


def prior_separation(parent: np.ndarray, mask: np.ndarray, prior: np.ndarray,
                     block_px: int = BLOCK_PX) -> dict:
    """Prove that mass moved up-prior, rather than merely changing density."""
    px = variants.block_to_pixels(prior, parent.shape, block_px)
    dropped, added = parent & ~mask, mask & ~parent
    before = float(px[dropped].mean())
    after = float(px[added].mean())
    return {"source_mean_prior": round(before, 6),
            "destination_mean_prior": round(after, 6),
            "destination_minus_source": round(after - before, 6),
            "passed": bool(np.isfinite(before) and np.isfinite(after) and after > before)}


def density_report(parent: np.ndarray, mask: np.ndarray, footprint: np.ndarray) -> dict:
    """Report CV at both the experimental 5 km scale and the merged 1 km scale."""
    out = {}
    for block_px in (10, 50):
        p = variants.block_density(parent, footprint, block_px)
        c = variants.block_density(mask, footprint, block_px)
        out[f"{block_px * 100}m"] = {
            "parent": {k: v for k, v in p.items() if k != "counts"},
            "variant": {k: v for k, v in c.items() if k != "counts"},
        }
    return out


def shift_truth(truth: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Translate a surrogate truth mask without wrap-around artefacts."""
    out = np.zeros_like(truth)
    h, w = truth.shape
    ys0, ys1 = max(0, dy), min(h, h + dy)
    xs0, xs1 = max(0, dx), min(w, w + dx)
    src_y0, src_x0 = max(0, -dy), max(0, -dx)
    if ys1 > ys0 and xs1 > xs0:
        out[ys0:ys1, xs0:xs1] = truth[src_y0:src_y0 + (ys1 - ys0),
                                      src_x0:src_x0 + (xs1 - xs0)]
    return out
