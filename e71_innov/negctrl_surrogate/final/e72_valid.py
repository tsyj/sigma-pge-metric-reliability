#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E72 验证批执行器（negctrl_surrogate 正式版；文件本身即冻结的操作定义）。

两种模式：
  --selftest  只读纬向（试点已读数据），用与留出完全相同的代码路径逐字复现
              E71B/C/E 的关键数字 → E72_SELFTEST_ZONAL.json（确定性输出，无时间戳）。
              不需要封存；绝不读任何留出文件。
  --holdout   读经向 + 45°（留出）与 e60（仅描述性），产出 P1–P7 所需全部统计
              → E72_VALID.json。前置硬门（缺一拒跑）：
              ① PREREG_negctrl_surrogate.md 已封存（.sha256 存在、哈希吻合）；
              ② SEEDS82.json 哈希与 .sha256 记录吻合；
              ③ E72_SELFTEST_ZONAL.json 存在且 all_match=true。
判分不在本脚本：e72_verdict.py 机械读 E72_VALID.json 输出 verdict.json。
资源：单进程，线程数由外层 run_valid.sh 设 OMP_NUM_THREADS=4；内存 16G 包裹。
"""
import argparse
import glob
import hashlib
import json
import math
import os
import sys
import time

import numpy as np
from scipy.stats import kendalltau, spearmanr

sys.path.insert(0, '/data/xinyuan/GOAI_ai4s_env/scripts')
from metric_search import base_quantities, spearman  # noqa: E402

ENV = '/data/xinyuan/GOAI_ai4s_env'
BASE = f'{ENV}/e71_innov/negctrl_surrogate'
FIN = f'{BASE}/final'
PREREG = f'{FIN}/PREREG_negctrl_surrogate.md'
SEALFN = PREREG + '.sha256'
SEEDSFN = f'{FIN}/SEEDS82.json'
SELFTESTFN = f'{FIN}/E72_SELFTEST_ZONAL.json'
VALIDPY = f'{FIN}/e72_valid.py'
VERDICTPY = f'{FIN}/e72_verdict.py'
DEVFN = f'{FIN}/DEVIATIONS.md'

KNOBS = ('VISC2', 'VISC4', 'AKV_BAK', 'TNU2')
SPUR_KEY = 'u|all|rms'
P5_KEY = 'u|d800|rms'
DEMO_KEYS = ('u|all|max', 'u|d800|rms')
EPS = 1e-12

DOMCFG = dict(
    zonal=dict(ledger=f'{ENV}/ledger/env2_runs.jsonl', runs=f'{ENV}/runs',
               sweep=f'{ENV}/ledger/knob_sweep.json',
               cache=f'{BASE}/E71B_BASEQ.json', cache_ro=True),
    merid=dict(ledger=f'{ENV}/ledger/env2_merid_runs.jsonl', runs=f'{ENV}/runs_merid',
               sweep=f'{ENV}/ledger/knob_sweep_merid.json',
               cache=f'{FIN}/E72_BASEQ_merid.json', cache_ro=False),
    diag45=dict(ledger=f'{ENV}/ledger/env2_diag45_runs.jsonl', runs=f'{ENV}/runs_diag45',
                sweep=f'{ENV}/ledger/knob_sweep_diag45.json',
                cache=f'{FIN}/E72_BASEQ_diag45.json', cache_ro=False),
)

t0 = time.time()


def log(*a):
    print(*a, flush=True)


def sha256(fn):
    h = hashlib.sha256()
    with open(fn, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def seal_map():
    """解析 .sha256：每行 '<hash>  <文件名>'（date 行忽略），返回 {basename: hash}。"""
    m = {}
    for line in open(SEALFN):
        p = line.split()
        if len(p) == 2 and len(p[0]) == 64:
            m[os.path.basename(p[1])] = p[0]
    return m


def require_seal():
    """封存门（PREREG §0-2）：核对 .sha256 入档全部五件的哈希。
    PREREG / SEEDS82 不符永不放行；两脚本与自检文件不符仅当 DEVIATIONS.md 在场
    （§10 崩溃修复已申报）才放行。运行时脚本 sha 一并返回，印入产出供事后核对。"""
    assert os.path.exists(SEALFN), '拒跑：预注册未封存（缺 %s）' % SEALFN
    m = seal_map()
    strict = {os.path.basename(PREREG), os.path.basename(SEEDSFN)}
    dev = os.path.exists(DEVFN)
    shas = {}
    for fn in (PREREG, VALIDPY, VERDICTPY, SEEDSFN, SELFTESTFN):
        bn = os.path.basename(fn)
        assert bn in m, '拒跑：封存记录缺 %s 的哈希' % bn
        assert os.path.exists(fn), '拒跑：缺文件 %s' % bn
        shas[bn] = sha256(fn)
        if shas[bn] != m[bn]:
            if bn in strict:
                raise AssertionError('拒跑：%s 哈希与封存记录不符（判据/种子类文件，永不放行）' % bn)
            if not dev:
                raise AssertionError('拒跑：%s 哈希与封存记录不符且无 DEVIATIONS.md（§10 未申报）' % bn)
    st = json.load(open(SELFTESTFN))
    assert st.get('all_match') is True, '拒跑：自检未全绿（all_match!=true）'
    return dict(prereg_sha=m[os.path.basename(PREREG)],
                seeds_sha=m[os.path.basename(SEEDSFN)],
                selftest_sha=shas[os.path.basename(SELFTESTFN)],
                runtime_valid_py_sha=shas[os.path.basename(VALIDPY)],
                runtime_verdict_py_sha=shas[os.path.basename(VERDICTPY)],
                sealed_valid_py_sha=m[os.path.basename(VALIDPY)],
                sealed_verdict_py_sha=m[os.path.basename(VERDICTPY)],
                deviations_present=dev)


def perm_p(x, y, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    obs = spearman(x, y)
    cnt = 0
    yy = y.copy()
    for _ in range(n):
        rng.shuffle(yy)
        if abs(spearman(x, yy)) >= abs(obs):
            cnt += 1
    return float((cnt + 1) / (n + 1))


# ---------- A_surr 机器（逐字复用 e71d 的定义） ----------
def tb(a, b):
    r = kendalltau(a, b)
    return float(r.statistic if hasattr(r, 'statistic') else r[0])


def ptau(h, z, v):
    thz, thv, tzv = tb(h, z), tb(h, v), tb(z, v)
    den = math.sqrt(max(0.0, (1 - thv ** 2) * (1 - tzv ** 2)))
    if den < 1e-9:
        return None, thz, thv, tzv
    return (thz - thv * tzv) / den, thz, thv, tzv


def asurr(H, Z, V, nboot=2000, seed=0):
    H, Z, V = map(np.asarray, (H, Z, V))
    n = len(H)
    pt, thz, thv, tzv = ptau(H, Z, V)
    rng = np.random.default_rng(seed)
    bs = []
    tries = 0
    while len(bs) < nboot and tries < nboot * 4:
        tries += 1
        idx = rng.integers(0, n, n)
        h, z, v = H[idx], Z[idx], V[idx]
        if len(set(v)) < 2 or len(set(np.round(z, 12))) < 2 or len(set(np.round(h, 12))) < 2:
            continue
        p = ptau(h, z, v)[0]
        if p is not None and np.isfinite(p):
            bs.append(p)
    bs = np.array(bs)
    lo, hi = (float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))) if len(bs) else (None, None)
    if abs(tzv) >= 0.999:
        verdict = '判死(与旋钮共线)'
    elif pt is None:
        verdict = '判死(偏相关不可定义)'
    elif lo is not None and lo <= 0 <= hi:
        verdict = '判死(CI 含 0)'
    else:
        verdict = '存疑(不认证)'
    return dict(n=n, partial_tau=None if pt is None else round(pt, 4),
                tau_HZ=round(thz, 4), tau_HV=round(thv, 4), tau_ZV=round(tzv, 4),
                ci95=[None if lo is None else round(lo, 4), None if hi is None else round(hi, 4)],
                n_boot_eff=int(len(bs)), verdict=verdict)


# ---------- 域级流水线（与 e71b/c/e 完全同构，数据源参数化） ----------
def domain_block(name, cfg, seeds, do_perm=True):
    rows = {}
    for l in open(cfg['ledger']):
        r = json.loads(l)
        rows[r['run_id']] = r
    # regraded_v2 含多域行：先载本域账本 run_id 集，再按域过滤载入（IO 卫生，PREREG §2）。
    # 数值与整文件载入等价——reg 只以本域 run_id 索引。
    reg = {}
    for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
        r = json.loads(l)
        if r['run_id'] in rows:
            reg[r['run_id']] = r['skill_vs_zero']
    valid = {rid: r for rid, r in rows.items()
             if r['obs'].get('valid') and r['ntimes'] == 8640}
    labels = sorted({r['bathy'] for r in valid.values()})
    # 陡臂标签冻结规则：有 'r26steep' 用之（与 e71b 同）；否则取唯一的非 flat/mit 标签。
    if 'r26steep' in labels:
        SL = 'r26steep'
    else:
        steep_lbls = [b for b in labels if b not in ('flat', 'mit')]
        assert len(steep_lbls) == 1, f'{name}: 意外 bathy 集合 {labels}'
        SL = steep_lbls[0]
    assert 'flat' in labels, f'{name}: 无 flat 臂，bathy 集合 {labels}'

    byp = {}
    for rid, r in valid.items():
        a = r['action']
        k = tuple(round(a.get(x, -1), 6) for x in KNOBS)
        byp.setdefault(k, {})[r['bathy']] = rid
    PAIRS = [(v[SL], v['flat']) for v in byp.values() if SL in v and 'flat' in v]

    # H 口径（域级统一，冻结规则）：配对陡臂全部有 regraded skill → skill_vs_zero；
    # 否则全部用 H = -hidden.err_rms_vs_truth。
    cover = all(s in reg for s, _ in PAIRS)
    h_source = 'skill_vs_zero' if cover else 'neg_err_rms_vs_truth'

    def H_of(rid):
        if h_source == 'skill_vs_zero':
            return reg.get(rid)
        e = rows[rid]['hidden'].get('err_rms_vs_truth')
        return None if e is None else -float(e)

    steep_all = [rid for rid, r in valid.items() if r['bathy'] == SL and H_of(rid) is not None]
    flat_all = [rid for rid, r in valid.items() if r['bathy'] == 'flat']

    cache = json.load(open(cfg['cache'])) if os.path.exists(cfg['cache']) else {}
    dirty = [False]

    def getq(rid):
        if rid not in cache:
            cache[rid] = base_quantities(f"{cfg['runs']}/{rid}")
            dirty[0] = True
        return cache[rid]

    def flush_cache():
        if dirty[0] and not cfg['cache_ro']:
            json.dump(cache, open(cfg['cache'], 'w'))
            dirty[0] = False

    for i, rid in enumerate(steep_all + flat_all):
        getq(rid)
        if i % 20 == 0:
            log('  [%s] 读底量 %d/%d (%.0fs)' % (name, i, len(steep_all) + len(flat_all), time.time() - t0))
    flush_cache()

    r26 = [rid for rid in steep_all if cache.get(rid)]
    flat = [rid for rid in flat_all if cache.get(rid)]
    Q26 = [cache[rid] for rid in r26]
    QFL = [cache[rid] for rid in flat]
    S = np.array([H_of(rid) for rid in r26], dtype=float)
    keys = sorted(set.intersection(*[set(q) for q in Q26 + QFL if q]))
    M26 = np.array([[q[k] for k in keys] for q in Q26])
    MFL = np.array([[q[k] for k in keys] for q in QFL])
    spur = M26[:, keys.index(SPUR_KEY)]

    P26L, PFLL, SP, keep_pairs = [], [], [], []
    for a, b in PAIRS:
        qa, qb = getq(a), getq(b)
        if qa and qb and all(k in qa and k in qb for k in keys):
            hh = H_of(a)
            if hh is None:
                continue
            P26L.append([qa[k] for k in keys])
            PFLL.append([qb[k] for k in keys])
            SP.append(hh)
            keep_pairs.append([a, b])
    flush_cache()
    P26, PFL = np.array(P26L), np.array(PFLL)
    SP = np.array(SP, dtype=float)
    n_pairs = len(P26L)
    spur_pair = P26[:, keys.index(SPUR_KEY)]
    lspur_pair = np.log(P26[:, keys.index(SPUR_KEY)]) - np.log(PFL[:, keys.index(SPUR_KEY)])
    dspur_pair = P26[:, keys.index(SPUR_KEY)] - PFL[:, keys.index(SPUR_KEY)]
    log('[%s] 陡臂 %d 平底臂 %d 配对 %d H口径=%s (%.0fs)'
        % (name, len(r26), len(flat), n_pairs, h_source, time.time() - t0))

    # 候选枚举（与 e71b 逐行同构）
    names = ('A65', 'B65', 'D65', 'A32', 'D32', 'Adiff', 'Ddiff', 'Alogr', 'Dlogr',
             'Dlogr_c', 'Ddiff_c', 'G')
    cols = {n: [] for n in names}
    NAME_N, NAME_D = [], []
    for i, kn in enumerate(keys):
        cand = [(kn, None, M26[:, i], MFL[:, i], P26[:, i], PFL[:, i], 1)]
        for j, kd in enumerate(keys):
            if i == j:
                continue
            if (np.any(np.abs(M26[:, j]) < EPS) or np.any(np.abs(MFL[:, j]) < EPS)
                    or np.any(np.abs(P26[:, j]) < EPS) or np.any(np.abs(PFL[:, j]) < EPS)):
                continue
            cand.append((kn, kd, M26[:, i] / M26[:, j], MFL[:, i] / MFL[:, j],
                         P26[:, i] / P26[:, j], PFL[:, i] / PFL[:, j], 0))
        for kn_, kd_, v26, vfl, p26, pfl, g in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))):
                continue
            if np.any(v26 <= 0) or np.any(vfl <= 0):
                continue
            d = p26 - pfl
            lr = np.log(p26) - np.log(pfl)
            cols['A65'].append(-spearman(v26, S))
            cols['B65'].append(float((pfl >= p26).mean()))
            cols['D65'].append(spearman(v26, spur))
            cols['A32'].append(-spearman(p26, SP))
            cols['D32'].append(spearman(p26, spur_pair))
            cols['Adiff'].append(-spearman(d, SP))
            cols['Ddiff'].append(spearman(d, spur_pair))
            cols['Alogr'].append(-spearman(lr, SP))
            cols['Dlogr'].append(spearman(lr, spur_pair))
            cols['Dlogr_c'].append(spearman(lr, lspur_pair))
            cols['Ddiff_c'].append(spearman(d, dspur_pair))
            cols['G'].append(g)
            NAME_N.append(kn_)
            NAME_D.append(kd_ or '')
    X = {k: np.array(v) for k, v in cols.items()}
    n_cand = len(X['A65'])
    log('[%s] 候选 %d (%.0fs)' % (name, n_cand, time.time() - t0))

    # 结构判决（P1 的量在此）
    struct = {}
    for tag, Dk, Ak in (('raw32', 'D32', 'A32'), ('diff', 'Ddiff', 'Adiff'), ('logr', 'Dlogr', 'Alogr')):
        struct['rho_D_A_' + tag] = round(float(spearman(X[Dk], X[Ak])), 4)
        if do_perm:
            struct['p_D_A_' + tag] = perm_p(X[Dk], X[Ak])
    struct['rho_D_A_e65_all58'] = round(float(spearman(X['D65'], X['A65'])), 4)
    struct['rho_Dc_A_diff'] = round(float(spearman(X['Ddiff_c'], X['Adiff'])), 4)
    struct['rho_Dc_A_logr'] = round(float(spearman(X['Dlogr_c'], X['Alogr'])), 4)
    struct['rho_A65_A32'] = round(float(spearman(X['A65'], X['A32'])), 4)
    struct['rho_A32_Alogr'] = round(float(spearman(X['A32'], X['Alogr'])), 4)
    struct['rho_A32_Adiff'] = round(float(spearman(X['A32'], X['Adiff'])), 4)
    # 副口径（并列平均秩），只报告不判分
    struct['rho_D_A_logr_scipy'] = round(float(spearmanr(X['Dlogr'], X['Alogr']).correlation), 4)
    struct['rho_D_A_diff_scipy'] = round(float(spearmanr(X['Ddiff'], X['Adiff']).correlation), 4)

    # 互斥缓解（P3 的量）：B = 该域配对上的原始平底抗刷率（E65 定义）
    exclusivity = dict(
        rho_A32_B=round(float(spearman(X['A32'], X['B65'])), 4),
        rho_Adiff_B=round(float(spearman(X['Adiff'], X['B65'])), 4),
        rho_Alogr_B=round(float(spearman(X['Alogr'], X['B65'])), 4),
        rho_Adiff_B_scipy=round(float(spearmanr(X['Adiff'], X['B65']).correlation), 4),
    )

    def both(A, D):
        m = (A >= 0.7) & (X['B65'] >= 0.9)
        return dict(n_both=int(m.sum()),
                    D_median=round(float(np.median(D[m])), 4) if m.any() else None,
                    n_both_absD_le05=int((m & (np.abs(D) <= 0.5)).sum()))
    both_gates = dict(raw32=both(X['A32'], X['D32']),
                      diff=both(X['Adiff'], X['Ddiff']),
                      logr=both(X['Alogr'], X['Dlogr']))

    # 两全描述（P4 的量）
    def gate(A, D):
        m3 = np.abs(D) <= 0.3
        return dict(nA07=int((A >= 0.7).sum()),
                    nA07_absD_le05=int(((A >= 0.7) & (np.abs(D) <= 0.5)).sum()),
                    maxA_absD_le03=round(float(A[m3].max()), 4) if m3.any() else None,
                    n_absD_le03=int(m3.sum()),
                    A_quartiles=[round(float(q), 4) for q in np.percentile(A, [25, 50, 75, 95, 100])])
    gates = dict(raw32=gate(X['A32'], X['D32']),
                 diff=gate(X['Adiff'], X['Ddiff']),
                 logr=gate(X['Alogr'], X['Dlogr']))

    # SEEDS82 存活（P2 的量）：门 = Adiff>=0.5 ∧ |Ddiff|<=0.5；缺席=死亡；分母恒为 82
    idx = {(NAME_N[i], NAME_D[i]): i for i in range(n_cand)}
    surv_names, dead_names, absent = [], [], []
    for s in seeds:
        key = (s['num'], s['den'])
        if key not in idx:
            absent.append(s['num'] + ('|' + s['den'] if s['den'] else ''))
            continue
        i = idx[key]
        if X['Adiff'][i] >= 0.5 and abs(X['Ddiff'][i]) <= 0.5:
            surv_names.append(dict(num=s['num'], den=s['den'],
                                   Adiff=round(float(X['Adiff'][i]), 4),
                                   Ddiff=round(float(X['Ddiff'][i]), 4)))
        else:
            dead_names.append(dict(num=s['num'], den=s['den'],
                                   Adiff=round(float(X['Adiff'][i]), 4),
                                   Ddiff=round(float(X['Ddiff'][i]), 4)))
    base_mask = (X['Adiff'] >= 0.5) & (np.abs(X['Ddiff']) <= 0.5)
    base_frac = float(base_mask.mean()) if n_cand else 0.0
    surv_rate = len(surv_names) / 82.0
    enrichment = surv_rate / max(base_frac, 1.0 / max(n_cand, 1))
    seeds_block = dict(n_ref=82, n_present=82 - len(absent), n_absent=len(absent),
                       n_survive=len(surv_names), surv_rate=round(surv_rate, 4),
                       base_frac=round(base_frac, 6), enrichment=round(enrichment, 3),
                       gate=dict(Adiff_min=0.5, absDdiff_max=0.5),
                       survivors=surv_names, dead=dead_names, absent=absent)

    # ---- 黏性 sweep（P5/P6/P7 的量；B* 仅黏性路径，预注册明写）----
    sweep = sweep_block(name, cfg, rows, reg, SL, cache, getq, flush_cache,
                        keys, NAME_N, NAME_D, n_cand)

    npzfn = f'{FIN}/E72_AXES_{name}.npz'
    np.savez(npzfn, **{k: X[k] for k in names},
             name_num=np.array(NAME_N), name_den=np.array(NAME_D), keys=np.array(keys))

    return dict(
        n_pairs=n_pairs, n_steep=len(r26), n_flat=len(flat), n_candidates=n_cand,
        steep_label=SL, h_source=h_source,
        skill_coverage_pairs=int(sum(1 for a, _ in keep_pairs if a in reg)),
        spurious_key=SPUR_KEY, struct=struct, exclusivity=exclusivity,
        both_gates=both_gates, gates=gates, seeds=seeds_block, sweep=sweep,
        pairs_used=keep_pairs, axes_npz=npzfn,
    ), X, NAME_N, NAME_D, keys


def sweep_block(name, cfg, rows, reg, SL, cache, getq, flush_cache,
                keys, NAME_N, NAME_D, n_cand):
    out = {}
    try:
        ks = json.load(open(cfg['sweep']))
    except Exception as e:
        return dict(skipped='sweep 账本不可读: %r' % e)
    sw = {}
    for k in ks:
        if k.get('knob') == 'VISC2':
            sw.setdefault(round(k['val'], 6), {})[k['bathy']] = k['run_id']
    vals = sorted(v for v, d in sw.items() if SL in d and 'flat' in d)
    steep_ids = [sw[v][SL] for v in vals]
    flat_ids = [sw[v]['flat'] for v in vals]
    for rid in steep_ids + flat_ids:
        getq(rid)
    flush_cache()
    ok_v = [i for i, v in enumerate(vals) if cache.get(steep_ids[i]) and cache.get(flat_ids[i])]
    vals = [vals[i] for i in ok_v]
    steep_ids = [steep_ids[i] for i in ok_v]
    flat_ids = [flat_ids[i] for i in ok_v]
    nlev = len(vals)
    out['vals'] = vals
    out['n_levels'] = nlev
    if nlev < 2:
        out['skipped'] = '可用档位 <2'
        return out

    # 真值轨（hidden err；skill 若 regraded 全覆盖）
    err7 = []
    for rid in steep_ids:
        e = rows.get(rid, {}).get('hidden', {}).get('err_rms_vs_truth')
        err7.append(None if e is None else float(e))
    truth_ok = all(e is not None for e in err7)
    out['err_trace'] = [None if e is None else round(e, 3) for e in err7]
    out['truth_ok'] = truth_ok
    sk_cover = all(rid in reg for rid in steep_ids)
    out['h_source'] = 'skill_vs_zero' if sk_cover else ('neg_err_rms_vs_truth' if truth_ok else 'NONE')
    if sk_cover:
        H7 = np.array([reg[rid] for rid in steep_ids])
        out['skill_trace'] = [round(float(x), 3) for x in H7]
        out['skill_never_passes'] = bool(H7.max() < 0)
    elif truth_ok:
        H7 = -np.array(err7)
    else:
        H7 = None

    # 演示位轨（P5 的量）
    def trace(key):
        rs = np.array([cache[r][key] for r in steep_ids])
        rf = np.array([cache[r][key] for r in flat_ids])
        d = dict(steep=[round(float(x), 4) for x in rs],
                 flat=[round(float(x), 4) for x in rf],
                 logratio=[round(float(x), 3) for x in np.log(rs / rf)],
                 improvement_raw=round(float(rs[0] / rs[-1]), 2),
                 lr_at_vmax=round(float(np.log(rs[-1] / rf[-1])), 3),
                 logratio_span=round(float(np.log(rs / rf).max() - np.log(rs / rf).min()), 3))
        return d
    demo = {}
    for key in DEMO_KEYS:
        if all(key in cache[r] for r in steep_ids + flat_ids):
            demo[key.replace('|', '_')] = trace(key)
    out['demo'] = demo

    # 家族级 OS（P6 的量），逐字同 e71c
    if truth_ok:
        err7a = np.array(err7)
        if err7a[0] > 0 and err7a[-1] > 0 and err7a[0] != err7a[-1]:
            dlerr = float(np.log(err7a[0] / err7a[-1]))
        else:
            dlerr = None
        out['dlerr'] = None if dlerr is None else round(dlerr, 4)
        out['err_improvement_ratio'] = round(float(err7a[0] / err7a[-1]), 3)
        if dlerr and dlerr > 0:
            kidx = {k: i for i, k in enumerate(keys)}
            skeys = set.intersection(*[set(cache[r]) for r in steep_ids + flat_ids])
            V26 = np.array([[cache[r][k] if k in skeys else np.nan for k in keys] for r in steep_ids])
            VFL = np.array([[cache[r][k] if k in skeys else np.nan for k in keys] for r in flat_ids])
            n = n_cand
            os_raw = np.empty(n); os_lr = np.empty(n); imp_raw = np.empty(n)
            rho_raw = np.empty(n); rho_lr = np.empty(n)
            range_raw = np.empty(n); range_lr = np.empty(n)
            okm = np.ones(n, dtype=bool)
            for c in range(n):
                if NAME_N[c] not in skeys or (NAME_D[c] and NAME_D[c] not in skeys):
                    okm[c] = False
                    continue
                i = kidx[NAME_N[c]]
                rs = V26[:, i].copy(); rf = VFL[:, i].copy()
                if NAME_D[c]:
                    j = kidx[NAME_D[c]]
                    if np.any(np.abs(V26[:, j]) < EPS) or np.any(np.abs(VFL[:, j]) < EPS):
                        okm[c] = False
                        continue
                    rs = rs / V26[:, j]; rf = rf / VFL[:, j]
                if np.any(rs <= 0) or np.any(rf <= 0) or not (np.all(np.isfinite(rs)) and np.all(np.isfinite(rf))):
                    okm[c] = False
                    continue
                lr = np.log(rs) - np.log(rf)
                rho_raw[c] = spearman(rs, err7a); rho_lr[c] = spearman(lr, err7a)
                range_raw[c] = float(np.log(rs.max() / rs.min())); range_lr[c] = float(lr.max() - lr.min())
                os_raw[c] = float(np.log(rs[0] / rs[-1]) / dlerr); os_lr[c] = float((lr[0] - lr[-1]) / dlerr)
                imp_raw[c] = float(rs[0] / rs[-1])
            m = okm

            def frac(x):
                return round(float(x[m].mean()), 4)
            out['os_summary'] = dict(
                n_ok=int(m.sum()), n_all=n,
                rho_raw_err=dict(mean=frac(rho_raw), frac_ge075=frac((rho_raw >= 0.75).astype(float)),
                                 frac_le0=frac((rho_raw <= 0).astype(float))),
                rho_lr_err=dict(mean=frac(rho_lr), frac_ge075=frac((rho_lr >= 0.75).astype(float)),
                                frac_le0=frac((rho_lr <= 0).astype(float))),
                range_reduction=dict(frac_lr_lt_raw=frac((range_lr < range_raw).astype(float)),
                                     median_range_raw=round(float(np.median(range_raw[m])), 4),
                                     median_range_lr=round(float(np.median(range_lr[m])), 4)),
                overstatement=dict(
                    median_OS_raw=round(float(np.median(os_raw[m])), 3),
                    median_OS_lr=round(float(np.median(os_lr[m])), 3),
                    frac_absOS_raw_gt2=frac((np.abs(os_raw) > 2).astype(float)),
                    frac_absOS_lr_gt2=frac((np.abs(os_lr) > 2).astype(float)),
                    frac_OS_raw_lt0=frac((os_raw < 0).astype(float)),
                    frac_OS_lr_lt0=frac((os_lr < 0).astype(float)),
                    frac_absOS_shrinks=frac((np.abs(np.abs(os_lr) - 1) < np.abs(np.abs(os_raw) - 1)).astype(float)),
                ),
                max_improvement_raw=round(float(imp_raw[m].max()), 1) if m.any() else None,
            )
        else:
            out['os_summary'] = dict(skipped='dlerr<=0 或不可定义（真值未随黏性改善）——P6 记 AMBIGUOUS')
    else:
        out['os_summary'] = dict(skipped='hidden err 缺失——P6 记 AMBIGUOUS')

    # A_surr / 共线（P7 的量）
    if H7 is not None and nlev >= 3:
        V7 = np.array(vals, dtype=float)
        blk = dict(tau_HV=round(tb(H7, V7), 4), abs_tau_HV=round(abs(tb(H7, V7)), 4))
        if truth_ok and out['h_source'] == 'skill_vs_zero':
            blk['posctrl_err'] = asurr(H7, np.array(err7), V7)
            blk['posctrl_applicable'] = True
        else:
            blk['posctrl_applicable'] = False
            blk['posctrl_note'] = 'H 即由 err 派生，正对照退化，按预注册条款免除'
        for key in DEMO_KEYS:
            if all(key in cache[r] for r in steep_ids):
                Z7 = np.array([cache[r][key] for r in steep_ids])
                blk['asurr_' + key.replace('|', '_')] = asurr(H7, Z7, V7)
        out['asurr'] = blk
    else:
        out['asurr'] = dict(skipped='H 缺失或档位 <3——P7 记 AMBIGUOUS')
    return out


def e60_descriptive():
    """陡度轴 e60：纯描述、无通过线（预注册次级条目）。任何失败只记录不中断。"""
    out = {}
    try:
        dirs = sorted(d for d in glob.glob(f'{ENV}/e60/runs/*') if os.path.isdir(d))
        rows = {}
        for d in dirs:
            q = base_quantities(d)
            if q:
                rows[os.path.basename(d)] = {k: q.get(k) for k in
                                             ('u|all|max', 'u|all|rms', 'u|d800|rms')}
        out['n_dirs'] = len(dirs)
        out['n_read'] = len(rows)
        pairs = []
        for nm, r in rows.items():
            if 'steep' in nm and nm.replace('steep', 'flat') in rows:
                f = rows[nm.replace('steep', 'flat')]
                p = dict(steep=nm, flat=nm.replace('steep', 'flat'))
                for k in ('u|all|max', 'u|d800|rms'):
                    if r.get(k) and f.get(k) and r[k] > 0 and f[k] > 0:
                        p['lr_' + k.replace('|', '_')] = round(math.log(r[k] / f[k]), 3)
                        p[k.replace('|', '_') + '_steep'] = round(r[k], 4)
                pairs.append(p)
        out['pairs'] = pairs
        out['readings'] = rows
        out['note'] = '描述性，无通过线；配对按目录名 steep<->flat 互换匹配，匹配不上即为空'
    except Exception as e:
        out = dict(skipped=repr(e))
    return out


# ---------- 自检：纬向复现 E71B/C/E ----------
def cmp_get(d, path):
    cur = d
    for p in path.split('.'):
        if not isinstance(cur, dict) or p not in cur:
            return '<缺>'
        cur = cur[p]
    return cur


def selftest():
    seeds = json.load(open(SEEDSFN))['seeds']
    assert len(seeds) == 82
    blk, X, NN, ND, keys = domain_block('zonal', DOMCFG['zonal'], seeds, do_perm=True)

    b = json.load(open(f'{BASE}/E71B_RUV.json'))
    e = json.load(open(f'{BASE}/E71E_ADDENDUM.json'))
    c = json.load(open(f'{BASE}/E71C_BSTAR.json'))

    mine_b = dict(n_candidates=blk['n_candidates'], n_pairs=blk['n_pairs'], struct=blk['struct'],
                  gates=blk['gates'])
    mine_e = dict(rho_A32_B65=blk['exclusivity']['rho_A32_B'],
                  rho_Adiff_B65=blk['exclusivity']['rho_Adiff_B'],
                  rho_Alogr_B65=blk['exclusivity']['rho_Alogr_B'],
                  both_raw32=blk['both_gates']['raw32'],
                  both_diff=blk['both_gates']['diff'],
                  both_logr=blk['both_gates']['logr'])
    osum = blk['sweep'].get('os_summary', {})
    mine_c = dict(n_ok=osum.get('n_ok'),
                  err_improvement_ratio=blk['sweep'].get('err_improvement_ratio'),
                  rho_raw_err=osum.get('rho_raw_err'), rho_lr_err=osum.get('rho_lr_err'),
                  range_reduction=osum.get('range_reduction'),
                  overstatement=osum.get('overstatement'),
                  demo_u_all_max_improvement=cmp_get(blk['sweep'], 'demo.u_all_max.improvement_raw'),
                  demo_u_all_max_span=cmp_get(blk['sweep'], 'demo.u_all_max.logratio_span'),
                  demo_u_d800_rms_improvement=cmp_get(blk['sweep'], 'demo.u_d800_rms.improvement_raw'),
                  demo_u_d800_rms_span=cmp_get(blk['sweep'], 'demo.u_d800_rms.logratio_span'))

    checks = []

    def chk(label, mine, pilot, tol=1e-9):
        okc = False
        if isinstance(mine, (int, float)) and isinstance(pilot, (int, float)):
            okc = abs(float(mine) - float(pilot)) <= tol
        else:
            okc = mine == pilot
        checks.append(dict(item=label, mine=mine, pilot=pilot, match=bool(okc)))

    for p in ('n_candidates', 'n_pairs'):
        chk('B.' + p, mine_b[p], b[p])
    for kk in ('rho_D_A_raw32', 'rho_D_A_diff', 'rho_D_A_logr', 'p_D_A_raw32', 'p_D_A_diff',
               'p_D_A_logr', 'rho_D_A_e65_all58', 'rho_Dc_A_diff', 'rho_Dc_A_logr',
               'rho_A65_A32', 'rho_A32_Alogr', 'rho_A32_Adiff'):
        chk('B.struct.' + kk, mine_b['struct'].get(kk), b['struct'].get(kk))
    for gk in ('raw32', 'diff', 'logr'):
        for f2 in ('nA07', 'nA07_absD_le05', 'maxA_absD_le03', 'n_absD_le03'):
            chk('B.gates.%s.%s' % (gk, f2), mine_b['gates'][gk][f2], b['gates'][gk][f2])
    for kk in ('rho_A32_B65', 'rho_Adiff_B65', 'rho_Alogr_B65'):
        chk('E.' + kk, mine_e[kk], e[kk])
    for gk in ('both_raw32', 'both_diff', 'both_logr'):
        for f2 in ('n_both', 'n_both_absD_le05'):
            chk('E.%s.%s' % (gk, f2), mine_e[gk][f2], e[gk][f2])
    cs = c['summary']
    chk('C.n_ok', mine_c['n_ok'], cs['n_ok'])
    chk('C.err_improvement_ratio', mine_c['err_improvement_ratio'], cs['err_improvement_ratio'])
    for grp in ('rho_raw_err', 'rho_lr_err'):
        for f2 in ('mean', 'frac_ge075', 'frac_le0'):
            chk('C.%s.%s' % (grp, f2), cmp_get(mine_c, grp + '.' + f2), cmp_get(cs, grp + '.' + f2))
    for f2 in ('frac_lr_lt_raw', 'median_range_raw', 'median_range_lr'):
        chk('C.range_reduction.' + f2, cmp_get(mine_c, 'range_reduction.' + f2),
            cmp_get(cs, 'range_reduction.' + f2))
    for f2 in ('median_OS_raw', 'median_OS_lr', 'frac_absOS_raw_gt2', 'frac_absOS_lr_gt2',
               'frac_OS_raw_lt0', 'frac_OS_lr_lt0', 'frac_absOS_shrinks'):
        chk('C.overstatement.' + f2, cmp_get(mine_c, 'overstatement.' + f2),
            cmp_get(cs, 'overstatement.' + f2))
    chk('C.demo.u_all_max.improvement_raw', mine_c['demo_u_all_max_improvement'],
        cmp_get(c, 'demo.u_all_max.improvement_raw'))
    chk('C.demo.u_all_max.logratio_span', mine_c['demo_u_all_max_span'],
        cmp_get(c, 'demo.u_all_max.logratio_span'))
    chk('C.demo.u_d800_rms.improvement_raw', mine_c['demo_u_d800_rms_improvement'],
        cmp_get(c, 'demo.u_d800_rms.improvement_raw'))
    chk('C.demo.u_d800_rms.logratio_span', mine_c['demo_u_d800_rms_span'],
        cmp_get(c, 'demo.u_d800_rms.logratio_span'))
    # 种子闭环：82 把在纬向按 P2 门（Adiff>=0.5 ∧ |Ddiff|<=0.5）应全部存活
    chk('SEEDS.zonal_survival', blk['seeds']['n_survive'], 82)

    n_bad = sum(1 for x in checks if not x['match'])
    out = dict(
        note='E72 自检：正式版流水线在纬向逐字复现 E71B/C/E（同一代码路径将用于留出域）；'
             '确定性输出（无时间戳），供封存记录 sha256',
        all_match=(n_bad == 0), n_checks=len(checks), n_mismatch=n_bad,
        checks=checks,
        zonal_sweep_reference=dict(
            note='纬向 sweep 上 P7 类量的参考读数（已知数据，非预测）',
            tau_HV=cmp_get(blk['sweep'], 'asurr.tau_HV'),
            abs_tau_HV=cmp_get(blk['sweep'], 'asurr.abs_tau_HV'),
            posctrl_err_verdict=cmp_get(blk['sweep'], 'asurr.posctrl_err.verdict'),
            h_source=blk['sweep'].get('h_source'),
            u_d800_rms_improvement=cmp_get(blk['sweep'], 'demo.u_d800_rms.improvement_raw'),
            u_d800_rms_lr_at_vmax=cmp_get(blk['sweep'], 'demo.u_d800_rms.lr_at_vmax'),
        ),
    )
    json.dump(out, open(SELFTESTFN, 'w'), indent=1, ensure_ascii=False)
    log(json.dumps(dict(all_match=out['all_match'], n_checks=out['n_checks'],
                        n_mismatch=out['n_mismatch']), ensure_ascii=False))
    if n_bad:
        for x in checks:
            if not x['match']:
                log('  MISMATCH', x)
    log('E72_SELFTEST_DONE %.0f 秒' % (time.time() - t0))
    return out['all_match']


def holdout():
    gate = require_seal()
    seeds = json.load(open(SEEDSFN))['seeds']
    assert len(seeds) == 82
    domains = {}
    for name in ('merid', 'diag45'):
        # 域级隔离（PREREG §3-7）：某域数据结构偏离导致崩溃时，该域落
        # {error, status:AMBIGUOUS}，另一域照算，不中断整批。
        try:
            blk, X, NN, ND, keys = domain_block(name, DOMCFG[name], seeds, do_perm=True)
        except Exception as e:
            import traceback
            log('[%s] 域级崩溃，按 §3-7 记 AMBIGUOUS: %r' % (name, e))
            blk = dict(error=repr(e), traceback=traceback.format_exc()[-3000:],
                       status='AMBIGUOUS')
        domains[name] = blk
    res = dict(
        note='E72 验证批（negctrl_surrogate）：封存预注册后的留出域统计；判分见 verdict.json',
        prereg_sha=gate['prereg_sha'], seeds_sha=gate['seeds_sha'],
        selftest_sha=gate['selftest_sha'],
        runtime_valid_py_sha=gate['runtime_valid_py_sha'],
        runtime_verdict_py_sha=gate['runtime_verdict_py_sha'],
        deviations_present=gate['deviations_present'],
        domains=domains,
        e60_descriptive=e60_descriptive(),
        elapsed_s=round(time.time() - t0, 1),
        generated=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
    )
    json.dump(res, open(f'{FIN}/E72_VALID.json', 'w'), indent=1, ensure_ascii=False)
    log('E72_VALID_DONE %.0f 秒' % (time.time() - t0))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--selftest', action='store_true', help='纬向自检（不需封存，不读留出）')
    g.add_argument('--holdout', action='store_true', help='留出验证（需封存+自检全绿）')
    args = ap.parse_args()
    if args.selftest:
        okk = selftest()
        sys.exit(0 if okk else 1)
    else:
        holdout()
