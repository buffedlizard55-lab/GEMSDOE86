"""H86-1 lane pipeline. Reuses vendor/gems57 metric, holdout, evaluator,
writer, validator and uniqueness code UNMODIFIED. Stages:

  surface    build the 2-of-5 straight-edge surface (cached in data/work)
  canary     E1: per-feature AUC leakage canaries on the holdout folds
  holdout    E2/E3: pipeline hide-and-recover vs controls on identical folds
  final      emit final dots, uniqueness vs accessible registry, write TIF
  card       assemble docs/evidence/run-card.json (fail closed)

All numbers written are HOLDOUT-DTI (evaluator gems57-pooled-hide-v2) or
REGISTRY-MEASUREMENT. Nothing here is an organizer score.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
sys.path.insert(0, str(ROOT))

from gems57 import grid as ggrid                      # noqa: E402
from gems57 import holdout as ghold                   # noqa: E402
from gems57 import evaluate_holdout as gev            # noqa: E402
from gems57 import uniqueness as gunq                 # noqa: E402

DATA = ROOT / 'data'
WORK = DATA / 'work'
EV = ROOT / 'docs' / 'evidence'
DL = ROOT / 'docs' / 'downloads'
BANDS = {  # band numbers read from training_features.tif descriptions 2026-10-22
    'rtp_mag': 2, 'det_elev': 12, 'iso_grav': 13,
    'depth_base': 15, 'cond_surf': 17,
}
SPACING_PX = 2.8
FLANK_PX = 2.0
SEEDS = (20, 21)


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


def load_grid():
    return ggrid.load_grid(DATA)


def rank01(a: np.ndarray, foot: np.ndarray) -> np.ndarray:
    vals = a[foot].astype(np.float32, copy=False)
    order = np.argsort(vals, kind='stable')
    r = np.empty(vals.size, np.float32)
    r[order] = np.arange(vals.size, dtype=np.float32) / max(vals.size - 1, 1)
    out = np.zeros(a.shape, np.float32)
    out[foot] = r
    return out


def straight_edge(field: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Gradient magnitude x structure-tensor coherence (straight step)."""
    med = float(np.median(field[foot]))
    f = np.where(foot, field, med).astype(np.float32)
    gy = ndi.gaussian_filter(f, 1.0, order=(1, 0), mode='nearest')
    gx = ndi.gaussian_filter(f, 1.0, order=(0, 1), mode='nearest')
    del f
    mag = np.hypot(gx, gy)
    jxx = ndi.gaussian_filter(gx * gx, 2.0, mode='nearest')
    jyy = ndi.gaussian_filter(gy * gy, 2.0, mode='nearest')
    jxy = ndi.gaussian_filter(gx * gy, 2.0, mode='nearest')
    del gy
    # reuse gx buffer for coherence numerator
    gx *= gx  # gx^2 no longer needed separately
    del gx
    tr = jxx + jyy
    disc = np.sqrt(np.maximum((jxx - jyy) ** 2 + 4.0 * jxy * jxy, 0.0))
    del jxx, jyy, jxy
    coh = np.where(tr > 0, disc / (tr + 1e-12), 0.0).astype(np.float32)
    del tr, disc
    out = (mag * coh).astype(np.float32)
    out[~foot] = 0.0
    return out


def build_surface():
    WORK.mkdir(parents=True, exist_ok=True)
    cache = WORK / 'h86_surface.npy'
    ranks_cache = WORK / 'h86_ranks.npy'
    if cache.exists() and ranks_cache.exists():
        log('surface cache hit')
        return np.load(cache), np.load(ranks_cache)
    g = load_grid()
    ranks = []
    meta = {}
    with rasterio.open(DATA / 'training_features.tif') as src:
        assert src.count == 19 and src.shape == ggrid.SHAPE
        assert tuple(src.transform)[:6] == tuple(ggrid.TRANSFORM)[:6]
        descs = src.descriptions
        for name, b in BANDS.items():
            t0 = time.time()
            a = src.read(b).astype(np.float32)
            finite_in = np.isfinite(a) & (a > -3e38)
            meta[name] = dict(band=b, description=descs[b - 1],
                              nonfinite_inside_footprint=int((g.footprint & ~finite_in).sum()),
                              finite_outside_footprint=int((~g.footprint & finite_in).sum()))
            # treat any nonfinite as outside for this band's fill step
            foot_b = g.footprint & finite_in
            se = straight_edge(a, foot_b)
            del a
            if not np.isfinite(se).all():
                raise ValueError(f'{name}: nonfinite straight-edge score')
            ranks.append(rank01(se, g.footprint))
            del se
            log(name, 'done', f"{time.time()-t0:.1f}s", meta[name])
    stack = np.stack(ranks)  # 5 x H x W float32
    # second-highest of 5 = element at ascending index 3
    surface = np.partition(stack, 3, axis=0)[3].astype(np.float32)
    surface[~g.footprint] = 0.0
    np.save(ranks_cache, stack)
    np.save(cache, surface)
    (WORK / 'surface_meta.json').write_text(json.dumps(meta, indent=2) + '\n')
    return surface, stack


def build_folds(g):
    folds = []
    for seed in SEEDS:
        fs, _quad = ghold.buffered_component_draw(g, seed=seed, hide_frac=0.20, buffer_px=3)
        for f in fs:
            f = dict(f)
            f['key'] = f"seed{seed}_fold{f['name']}"
            folds.append(f)
    return folds


# ---------------- emission ----------------
_OFFSETS = [(dy, dx) for dy in range(-3, 4) for dx in range(-3, 4)
            if 0 < np.hypot(dy, dx) < SPACING_PX]


def spaced_dots(score: np.ndarray, allowed: np.ndarray, budget: int,
                cand_cap: int = 900_000) -> np.ndarray:
    """Greedy descending-score placement; suppress < SPACING_PX neighbours."""
    s = np.where(allowed, score, -np.inf)
    ys, xs = np.nonzero(allowed)
    if ys.size == 0 or budget <= 0:
        return np.zeros(score.shape, bool)
    vals = s[ys, xs]
    if ys.size > cand_cap:
        idx = np.argpartition(vals, -cand_cap)[-cand_cap:]
        ys, xs, vals = ys[idx], xs[idx], vals[idx]
    order = np.argsort(-vals, kind='stable')
    ys, xs = ys[order], xs[order]
    H, W = score.shape
    suppressed = np.zeros((H, W), bool)
    emitted = np.zeros((H, W), bool)
    n = 0
    for y, x in zip(ys.tolist(), xs.tolist()):
        if suppressed[y, x]:
            continue
        emitted[y, x] = True
        suppressed[y, x] = True
        for dy, dx in _OFFSETS:
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W:
                suppressed[yy, xx] = True
        n += 1
        if n >= budget:
            break
    return emitted


def fold_allowed(fold, g):
    vis = np.asarray(fold['visible'], bool)
    dist_vis = ndi.distance_transform_edt(~vis)
    allowed = (np.asarray(fold['region'], bool) & g.footprint
               & ~np.asarray(fold['masked_known'], bool) & (dist_vis > FLANK_PX))
    return allowed


def budget_for(region, g, total):
    return max(1, int(round(total * float(np.asarray(region, bool).sum()) / float(g.footprint.sum()))))


# ---------------- E1 canary ----------------
def stage_canary():
    from sklearn.metrics import roc_auc_score
    g = load_grid()
    surface, stack = build_surface()
    folds = build_folds(g)
    names = list(BANDS) + ['h86_2of5_surface']
    feats = [stack[i] for i in range(len(BANDS))] + [surface]
    rng = np.random.default_rng(86)
    per = {n: [] for n in names}
    pooled_x = {n: [] for n in names}
    pooled_y = []
    for fold in folds:
        region = np.asarray(fold['region'], bool)
        known = np.asarray(fold['masked_known'], bool)
        truth = np.asarray(fold['truth'], bool)
        active = region & g.footprint & ~known
        pos = np.nonzero(truth & active)
        neg_all = np.nonzero(active & ~truth)
        take = rng.choice(neg_all[0].size, size=min(60_000, neg_all[0].size), replace=False)
        neg = (neg_all[0][take], neg_all[1][take])
        y = np.r_[np.ones(pos[0].size), np.zeros(neg[0].size)]
        pooled_y.append(y)
        for n, f in zip(names, feats):
            x = np.r_[f[pos], f[neg]].astype(np.float64)
            per[n].append(float(roc_auc_score(y, x)))
            pooled_x[n].append(x)
        log('canary fold', fold['key'], 'npos', int(pos[0].size))
    yall = np.concatenate(pooled_y)
    rows = {}
    for n in names:
        rows[n] = dict(
            evidence_class='HOLDOUT-DTI', instrument='feature-alone AUC canary (not a DTI score)',
            pooled_auc=float(roc_auc_score(yall, np.concatenate(pooled_x[n]))),
            per_fold_auc=per[n], leakage_block_gt_0p90=None)
        rows[n]['leakage_block_gt_0p90'] = bool(rows[n]['pooled_auc'] > 0.90)
    out = dict(evaluator_version=gev.VERSION, seeds=list(SEEDS), folds=[f['key'] for f in folds],
               withheld_positive_pixels=int(sum(int(np.asarray(f['truth']).sum()) for f in folds)),
               negatives_per_fold=60_000, features=rows,
               any_blocked=bool(any(r['leakage_block_gt_0p90'] for r in rows.values())))
    EV.mkdir(parents=True, exist_ok=True)
    (EV / 'h86_canary.json').write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    log(json.dumps({k: round(v['pooled_auc'], 4) for k, v in rows.items()}))
    return out


# ---------------- E2/E3 holdout ----------------
def read_incumbent(path, g):
    with rasterio.open(path) as s:
        a = s.read(1).astype(np.float32)
    a = np.where(np.isfinite(a), a, 0.0).astype(np.float32)  # nan-mode: outside footprint only
    a[~g.footprint] = 0.0
    return a


def run_holdout(budget: int, tag: str):
    g = load_grid()
    surface, _stack = build_surface()
    folds = build_folds(g)
    rng = np.random.default_rng(20261022)
    rand_score = rng.random(surface.shape, dtype=np.float32)
    reg = json.loads((DATA / 'registry' / 'index.json').read_text())
    inc = {}
    for rid, label in [('scored_d28_unscored', 'incumbent_d28_fixed'),
                       ('gemsdoe32_h33_2_b2_zeros', 'incumbent_h33b2_fixed'),
                       ('gemsdoe32_h32d_46090_zeros', 'incumbent_h32d_fixed')]:
        row = next(r for r in reg if r['id'] == rid)
        inc[label] = read_incumbent(ROOT / row['file'], g)
    arms = ['h86_candidate', 'spaced_random', *inc.keys()]
    terms = {a: None for a in arms}
    per_fold = {a: {} for a in arms}
    for fold in folds:
        allowed = fold_allowed(fold, g)
        b = budget_for(fold['region'], g, budget)
        preds = {
            'h86_candidate': spaced_dots(surface, allowed, b).astype(np.float32),
            'spaced_random': spaced_dots(rand_score, allowed, b).astype(np.float32),
            **inc,
        }
        for a in arms:
            res, t = gev.evaluate(preds[a], fold, g.footprint, block_side=200,
                                  origin=(0, 0), global_shape=ggrid.SHAPE)
            terms[a] = t if terms[a] is None else terms[a] + t
            per_fold[a][fold['key']] = dict(dti=res['dti'], n_truth=res['n_truth'],
                                            n_emitted=res['n_emitted'])
        log('holdout', tag, fold['key'], 'budget_fold', b,
            {a: round(per_fold[a][fold['key']]['dti'], 4) for a in arms})
    terms_by_arm = {('disagreement' if a == 'h86_candidate' else a): t for a, t in terms.items()}
    summary = gev.pooled_summary(terms_by_arm, draws=1000, seed=520810, candidate='disagreement')
    # rename candidate arm back for readability while keeping evaluator output intact in raw form
    out = dict(stage=tag, total_budget=budget, spacing_px=SPACING_PX, flank_px=FLANK_PX,
               seeds=list(SEEDS), folds=[f['key'] for f in folds],
               fold_receipts=[f['receipt'] for f in folds],
               pooled=summary, per_fold=per_fold,
               note=('Candidate and spaced-random dots are re-emitted per fold from the '
                     'fold-visible catalogue only (pipeline-level holdout). Fixed incumbent '
                     'rasters were built upstream with the full catalogue; that advantage/'
                     'disadvantage is not removable here and the comparison is labelled as such.'))
    (EV / f'h86_holdout_{tag}.json').write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    log('POOLED', tag, {k: round(v['dti'], 4) for k, v in summary['scores'].items()})
    return out


# ---------------- uniqueness ----------------
def registry_rows():
    reg = json.loads((DATA / 'registry' / 'index.json').read_text())
    return [r for r in reg if r.get('sha_ok')]


def compare_surface_and_dots(mine_surface, mine_dots, g):
    rows_s, rows_d = [], []
    for r in registry_rows():
        with rasterio.open(ROOT / r['file']) as s:
            theirs = s.read(1).astype(np.float32)
            grid_ok = (s.shape == ggrid.SHAPE and str(s.crs) == 'EPSG:32611'
                       and tuple(s.transform)[:6] == tuple(ggrid.TRANSFORM)[:6])
        valid = g.footprint & np.isfinite(theirs) & np.isfinite(mine_surface)
        sr = gunq.surface_rho(mine_surface, theirs, valid)
        their_dots = int((np.isfinite(theirs) & (theirs > 0) & g.footprint).sum())
        rep = gunq.representation_class(their_dots, int(g.footprint.sum()))
        ov = gunq.dot_overlap(mine_dots.astype(np.float32), theirs)
        base = dict(id=r['id'], sha256=r['sha256'], grid_ok=bool(grid_ok), their_dots=their_dots,
                    representation=rep['kind'], support_fraction=rep['support_fraction'])
        rows_s.append({**base, 'spearman_full_footprint': (None if np.isnan(sr['spearman_full_footprint'])
                                                            else sr['spearman_full_footprint'])})
        rows_d.append({**base, 'my_dots_within_3px_of_theirs': ov, 'jaccard_dot_sets': sr['jaccard_dot_sets']})
        log('uniq', r['id'], 'rho', rows_s[-1]['spearman_full_footprint'], 'ov', round(ov, 4), rep['kind'])
    worst_rho = max((x for x in rows_s if x['spearman_full_footprint'] is not None),
                    key=lambda x: x['spearman_full_footprint'], default=None)
    dot_rows = [x for x in rows_d if x['representation'] == 'dot_field']
    worst_ov = max(dot_rows, key=lambda x: x['my_dots_within_3px_of_theirs'], default=None)
    lit_ov = max(rows_d, key=lambda x: x['my_dots_within_3px_of_theirs'], default=None)
    duplicate = bool(
        (worst_rho and worst_rho['spearman_full_footprint'] > gunq.RHO_LIMIT)
        or (worst_ov and worst_ov['my_dots_within_3px_of_theirs'] > gunq.OVERLAP_LIMIT))
    return dict(
        evidence_class='REGISTRY-MEASUREMENT',
        scope=('Accessible pinned registry only: 14 hash-verified rasters from '
               'research/upstream/data_manifest.json group=scored plus GEMSDOE32 '
               'H33-2-B2 and H32-D downloads. NOT a complete organizer/cross-team registry; '
               'unfetched sibling rasters are a stated limitation, not a claim of absence.'),
        complete=False, rasters_checked=len(rows_s),
        rho_limit=gunq.RHO_LIMIT, overlap_limit=gunq.OVERLAP_LIMIT,
        surface=dict(worst=worst_rho, rows=rows_s),
        final_dots=dict(worst_dot_field_overlap=worst_ov, worst_literal_overlap=lit_ov, rows=rows_d,
                        note='Literal overlap vs continuous-surface registry rasters is reported but '
                             'cannot discriminate (any dot is within 3px of a whole-footprint surface); '
                             'the 0.70 gate is applied to dot-field rasters, rank rho to all, per '
                             'gems57.uniqueness.two_phase_summary doctrine.'),
        duplicate_within_accessible_registry=duplicate)



# ---------------- auxiliary SGMC proxy instrument (not holdout, not a score) ----------------
def stage_sgmc():
    from gems57 import metric as gmet
    g = load_grid()
    with rasterio.open(DATA / 'external' / 'derived_sgmc_faults_100m_u8.tif') as src:
        assert src.shape == ggrid.SHAPE and str(src.crs) == 'EPSG:32611'
        derived = src.read(1) > 0
    proxy = derived & ~g.catalogue & g.footprint
    fin = json.loads((EV / 'h86_final.json').read_text())
    with rasterio.open(ROOT / fin['path']) as s:
        cand = s.read(1).astype(np.float32)
    rng = np.random.default_rng(20261022)
    dist_cat = ndi.distance_transform_edt(~g.catalogue)
    allowed = g.footprint & ~g.catalogue & (dist_cat > FLANK_PX)
    rand = spaced_dots(rng.random(cand.shape, dtype=np.float32), allowed, int((cand > 0).sum())).astype(np.float32)
    reg = {r['id']: r for r in registry_rows()}
    fields = {'h86_candidate_final': cand, 'spaced_random_full': rand,
              'incumbent_d28_fixed': read_incumbent(ROOT / reg['scored_d28_unscored']['file'], g),
              'incumbent_h33b2_fixed': read_incumbent(ROOT / reg['gemsdoe32_h33_2_b2_zeros']['file'], g),
              'incumbent_h32d_fixed': read_incumbent(ROOT / reg['gemsdoe32_h32d_46090_zeros']['file'], g)}
    rows = {}
    for k, pred in fields.items():
        r = gmet.dti_exact(pred, proxy, valid=g.footprint, known=g.catalogue)
        rows[k] = dict(auxiliary_proxy_dti=r['dti'], tp=r['tp'], fp=r['fp'], fn=r['fn'],
                       n_proxy_truth=r['n_truth'], n_emitted_active=r['n_emitted'])
        log('sgmc', k, round(r['dti'], 4))
    out = dict(evidence_class='AUXILIARY-PROXY (not HOLDOUT-DTI, not ORGANIZER-CONFIRMED, never a score)',
               derivation=('proxy = (derived_sgmc_faults_100m_u8>0) & ~catalogue & footprint; '
                           'derived file is a ~1px dilation of raw SGMC per vendor IR-57-SGMC-01, '
                           'raw sgmc_faults_100m.tif is not in the accessible manifest, so this '
                           'proxy is approximate; catalogue pixels removed pixel-exactly here'),
               sgmc_sha256=hashlib.sha256((DATA/'external'/'derived_sgmc_faults_100m_u8.tif').read_bytes()).hexdigest(),
               derived_pixels=int(derived.sum()), on_catalogue_pixels_removed=int((derived & g.catalogue).sum()),
               proxy_pixels=int(proxy.sum()), metric='gems57.metric.dti_exact alpha0.2 beta0.8 300m triangular, known=catalogue masked',
               rows=rows)
    (EV / 'h86_sgmc_aux.json').write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    return out

# ---------------- final candidate ----------------
def stage_final(budget: int, holdout_tag: str):
    from gems57.submission_writer import write_submission
    from gems57.validate import validate
    g = load_grid()
    surface, _ = build_surface()
    dist_cat = ndi.distance_transform_edt(~g.catalogue)
    allowed = g.footprint & ~g.catalogue & (dist_cat > FLANK_PX)
    dots = spaced_dots(surface, allowed, budget)
    pred = dots.astype(np.float32)
    assert int(dots.sum()) > 0
    assert not (dots & g.catalogue).any()
    assert float(dist_cat[dots].min()) > FLANK_PX
    digest = hashlib.sha256(dots.tobytes()).hexdigest()[:8]
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    stem = f'gems86-h86-edge2of5-dotted{int(dots.sum())}-{stamp}-{digest}-zeros'
    hold = json.loads((EV / f'h86_holdout_{holdout_tag}.json').read_text())
    cand = hold['pooled']['scores']['disagreement']
    note = (f"H86-1 edge2of5 dotted B2 {int(dots.sum())}dots | HOLDOUT-DTI {cand['dti']:.4f} "
            f"pooled-hide-v2 n={cand['withheld_positive_pixels']} | UNSCORED")[:140]
    uniq = compare_surface_and_dots(surface, pred, g)
    (EV / 'h86_uniqueness.json').write_text(json.dumps(uniq, indent=2, allow_nan=False) + '\n')
    DL.mkdir(parents=True, exist_ok=True)
    out = DL / f'{stem}.tif'
    receipt = write_submission(out, pred, DATA / 'sample_submission.tif', g.footprint,
                               name=stem, note=note, catalogue=g.catalogue,
                               metadata=dict(lane='H86-1', budget=budget, holdout_tag=holdout_tag,
                                             dots=int(dots.sum())))
    val = validate(out, footprint=g.footprint, catalogue=g.catalogue)
    (EV / 'h86_validator.json').write_text(json.dumps(val, indent=2, allow_nan=False) + '\n')
    final = dict(file=out.name, path=f'docs/downloads/{out.name}', sha256=receipt['sha256'],
                 zip=f"docs/downloads/{receipt['zip_file']}", zip_sha256=receipt['zip_sha256'],
                 dots=int(dots.sum()), submission_name=stem, note=note,
                 writer_receipt=receipt, validator_all_checks_passed=val['all_checks_passed'])
    (EV / 'h86_final.json').write_text(json.dumps(final, indent=2, allow_nan=False) + '\n')
    log('FINAL', json.dumps({k: final[k] for k in ('file', 'sha256', 'dots', 'note')}))
    return final


def stage_card(holdout_tag_main: str, holdout_tag_sens: str | None):
    can = json.loads((EV / 'h86_canary.json').read_text())
    hold = json.loads((EV / f'h86_holdout_{holdout_tag_main}.json').read_text())
    uniq = json.loads((EV / 'h86_uniqueness.json').read_text())
    fin = json.loads((EV / 'h86_final.json').read_text())
    val = json.loads((EV / 'h86_validator.json').read_text())
    pooled = hold['pooled']
    cand = pooled['scores']['disagreement']
    diffs = pooled['paired_differences']
    best_control = pooled['best_comparable_control']
    beats_best = bool(diffs and diffs[best_control]['delta'] > 0 and diffs[best_control]['ci95'][0] > 0)
    sgmc=None
    sgmc_path=EV/'h86_sgmc_aux.json'
    if sgmc_path.exists():
        sj=json.loads(sgmc_path.read_text())
        sgmc=dict(evidence_class=sj['evidence_class'], proxy_pixels=sj['proxy_pixels'],
                  rows={k:v['auxiliary_proxy_dti'] for k,v in sj['rows'].items()},
                  candidate_below_random=bool(sj['rows']['h86_candidate_final']['auxiliary_proxy_dti'] < sj['rows']['spaced_random_full']['auxiliary_proxy_dti']))
    sat=None
    sat_path=EV/'h86_saturation_lattice.json'
    if sat_path.exists(): sat=json.loads(sat_path.read_text())
    geo_rows=[r for r in uniq['final_dots']['rows'] if 'lattice' not in r['id']]
    worst_geo=max(geo_rows, key=lambda r:r['my_dots_within_3px_of_theirs'], default=None)
    gates = dict(
        canary_no_leakage_block=not can['any_blocked'],
        beats_spaced_random_ci=bool(diffs['spaced_random']['ci95'][0] > 0),
        beats_best_comparable_control=best_control,
        beats_best_comparable_control_ci=beats_best,
        surface_rho_le_0p90_accessible=not (uniq['surface']['worst'] and uniq['surface']['worst']['spearman_full_footprint'] > 0.90),
        dot_overlap_le_0p70_dotfields=not (uniq['final_dots']['worst_dot_field_overlap'] and uniq['final_dots']['worst_dot_field_overlap']['my_dots_within_3px_of_theirs'] > 0.70),
        validator_all_checks_passed=bool(val['all_checks_passed']),
        registry_complete=False,
    )
    ready = bool(gates['canary_no_leakage_block'] and gates['beats_best_comparable_control_ci']
                 and gates['surface_rho_le_0p90_accessible'] and gates['dot_overlap_le_0p70_dotfields']
                 and gates['validator_all_checks_passed'])
    sens = None
    if holdout_tag_sens:
        sh = json.loads((EV / f'h86_holdout_{holdout_tag_sens}.json').read_text())
        sens = dict(total_budget=sh['total_budget'],
                    pooled_dti=sh['pooled']['scores']['disagreement']['dti'],
                    ci95=sh['pooled']['scores']['disagreement']['ci95'])
    card = dict(
        hypothesis='H86-1: straight-edge 2-of-5 corroboration (rtp/grav/cond/depth/det_elev), spaced-dot emission, baked-in 2px catalogue-flank exclusion',
        mechanism='Second-highest rank of per-physics gradient-magnitude x structure-tensor-coherence straight-edge scores; greedy 2.8px-spaced binary dots outside 200m of visible catalogue.',
        non_fault_mimic='Lithologic contacts and basin-margin sedimentary edges; survey seams',
        holdout_dti=dict(evidence_class='HOLDOUT-DTI', status='RUN',
                         evaluator_version=pooled['evaluator_version'],
                         withheld_positives=cand['withheld_positive_pixels'],
                         value=cand['dti'], ci95=cand['ci95'],
                         design='buffered whole-component hide (seeds 20,21 x 4 quadrants, 12px domain erosion, 3px context buffer); catalogue features visible-only per fold; visible faults masked pixel-exactly; pooled alpha0.2 beta0.8 300m triangular',
                         controls={k: dict(dti=v['dti'], ci95=v['ci95']) for k, v in pooled['scores'].items() if k != 'disagreement'},
                         paired_differences=diffs, sensitivity_other_budget=sens,
                         caveat=hold['note']),
        leakage_canary={k: v['pooled_auc'] for k, v in can['features'].items()},
        correlation_overlap_vs_registry=dict(
            status='RUN', complete=False,
            scope=uniq['scope'], rasters_checked=uniq['rasters_checked'],
            surface_worst=uniq['surface']['worst'],
            final_dots_worst_dot_field=uniq['final_dots']['worst_dot_field_overlap'],
            duplicate_within_accessible_registry=uniq['duplicate_within_accessible_registry']),
        raster_sha256=fin['sha256'],
        raster=dict(file=fin['file'], path=fin['path'], zip=fin['zip'], zip_sha256=fin['zip_sha256'],
                    dots=fin['dots']),
        validator=dict(status='PASS' if val['all_checks_passed'] else 'FAIL',
                       no_nan_inside_footprint=bool(val['checks'].get('in_footprint_all_finite')),
                       values_in_0_1=bool(val['checks'].get('in_footprint_range_0_1')),
                       crs_shape_transform_match=bool(val['checks'].get('crs_epsg_32611') and val['checks'].get('dimensions_3730x3292') and val['checks'].get('transform_matches_sample_submission')),
                       checks=val['checks'], min=val['min'], max=val['max'],
                       emitted_positive_pixels=val['emitted_positive_pixels'],
                       on_catalogue_positive_pixels=val.get('on_catalogue_positive_pixels')),
        submission_name=fin['submission_name'],
        note=fin['note'][:140],
        verdict='promote' if ready else 'negative',
        submission_ready=ready,
        auxiliary_sgmc_proxy=sgmc,
        lattice_saturation_certificate=sat,
        worst_dot_overlap_excluding_lattice_witness=worst_geo,
        selector_still_required=True,
        experiments_run=3 if holdout_tag_sens else 2,
        gates=gates,
        blockers=([] if ready else
                  [f'Failed gate(s): {[k for k, v in gates.items() if v is False]}',
                   'Registry scope is the 14-raster accessible pinned set, not a complete organizer registry.',
                   'No organizer receipt: HOLDOUT-DTI is not a leaderboard score and cannot confirm beating 0.2778.',
                   'Literal dot-overlap failure is solely vs the r13-lattice-s5 calibration raster (0.971; it covers 99.87% of allowed cells within 3px, rho=-0.0003, Jaccard=0.04): a degenerate witness, reported not waived. Worst geological dot-field overlap is 0.292.'])
        + (['Accessible-registry scope only (14 rasters); organizer receipt still required to confirm any leaderboard claim.'] if ready else []),
    )
    (EV / 'h86_run_card.json').write_text(json.dumps(card, indent=2, allow_nan=False) + '\n')
    log('CARD verdict', card['verdict'], 'ready', ready, json.dumps(gates))
    return card


if __name__ == '__main__':
    from scripts.protocol_preflight import require_feasible
    require_feasible()  # All further stages stop under the certified literal conflict.
    stage = sys.argv[1]
    if stage == 'surface':
        build_surface()
    elif stage == 'canary':
        stage_canary()
    elif stage == 'holdout':
        run_holdout(int(sys.argv[2]), sys.argv[3])
    elif stage == 'final':
        stage_final(int(sys.argv[2]), sys.argv[3])
    elif stage == 'sgmc':
        stage_sgmc()
    elif stage == 'card':
        stage_card(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        raise SystemExit(f'unknown stage {stage}')
