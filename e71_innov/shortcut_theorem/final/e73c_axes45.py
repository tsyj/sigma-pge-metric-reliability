#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E73 shortcut_theorem · 步骤 C（后备）：45° 逐候选轴落盘。

协作条款（PREREG §0）：只有当 multienv_metrology 的 final/E71_FINAL_AXES.npz 不存在时才运行本脚本；
存在则拒绝运行（用对方产出，只读，不重复算）。配方 axes() 与 e71a_pilot_axes.py 逐字一致
（源头 e67/e67b_recipe_transfer.py 勘误后口径）。输出：E73_AXES45.npz(+META)，schema 与
E71_FINAL_AXES.npz 相同（num,den,G,*_z,*_m,*_45），只写本目录。
运行：systemd-run --user --scope -p MemoryMax=16G nice -n 19 env OMP_NUM_THREADS=8 <python> e73c_axes45.py
"""
import hashlib, json, os, sys, time
import numpy as np

ENV = '/data/xinyuan/GOAI_ai4s_env'
FIN = f'{ENV}/e71_innov/shortcut_theorem/final'
MULTI = f'{ENV}/e71_innov/multienv_metrology/final/E71_FINAL_AXES.npz'
PRE = f'{FIN}/PREREG_shortcut_theorem.md'
SHA = f'{FIN}/PREREG_shortcut_theorem.sha256'


def seal_gate():
    if not os.path.exists(SHA):
        sys.exit('拒绝运行：预注册尚未封存（缺 %s）。' % SHA)
    want = open(SHA).readline().split()[0]
    got = hashlib.sha256(open(PRE, 'rb').read()).hexdigest()
    if want != got:
        sys.exit('拒绝运行：PREREG 与封存 sha256 不符（%s… vs %s…）。' % (want[:12], got[:12]))
    return want


SEAL = seal_gate()
if os.path.exists(MULTI):
    sys.exit('拒绝运行：E71M 已落盘 45° 轴（%s）——按协作条款只读对方产出，不重复算。' % MULTI)
SCRIPT_SHA = hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()
sys.path.insert(0, f'{ENV}/scripts')
import metric_search  # noqa: E402
assert os.path.realpath(metric_search.__file__).endswith('GOAI_ai4s_env/scripts/metric_search.py'), metric_search.__file__
from metric_search import base_quantities, spearman  # noqa: E402

t0 = time.time()
def log(*a): print(*a, flush=True)

def rank(x):
    o = np.argsort(np.argsort(x, kind='mergesort'), kind='mergesort').astype(float)
    return (o - o.mean()) / (o.std() + 1e-12)


def axes(ledger, runsdir, reg_from):
    """与 e71a_pilot_axes.py 逐字一致。"""
    reg = {}
    if reg_from == 'regraded':
        for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
            r = json.loads(l); reg[r['run_id']] = r['skill_vs_zero']
    seen = {}; byp = {}
    for l in open(ledger):
        r = json.loads(l)
        if not (r['obs'].get('valid') and r['ntimes'] == 8640): continue
        seen[r['run_id']] = r['bathy']
        if reg_from == 'hidden' and r['bathy'] == 'r26steep' and (r.get('hidden') or {}).get('skill_vs_zero') is not None:
            reg[r['run_id']] = r['hidden']['skill_vs_zero']
        a = r['action']; k = tuple(round(a.get(x, -1), 6) for x in ('VISC2', 'VISC4', 'AKV_BAK', 'TNU2'))
        byp.setdefault(k, {})[r['bathy']] = r['run_id']
    r26 = [k for k, v in seen.items() if v == 'r26steep' and k in reg]
    flat = [k for k, v in seen.items() if v == 'flat']
    PAIRS = [(v['r26steep'], v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
    Q26, S26, QFL = [], [], []
    for rid in r26:
        q = base_quantities(f'{runsdir}/{rid}')
        if q: Q26.append(q); S26.append(reg[rid])
    for rid in flat:
        q = base_quantities(f'{runsdir}/{rid}')
        if q: QFL.append(q)
    keys = sorted(set.intersection(*[set(q) for q in Q26 + QFL]))
    M26 = np.array([[q[k] for k in keys] for q in Q26])
    MFL = np.array([[q[k] for k in keys] for q in QFL])
    S = np.array(S26)
    SP = 'u|all|rms'; spur = M26[:, keys.index(SP)] if SP in keys else M26[:, 0]
    P26L, PFLL = [], []
    for a, b in PAIRS:
        qa, qb = base_quantities(f'{runsdir}/{a}'), base_quantities(f'{runsdir}/{b}')
        if qa and qb and all(k in qa and k in qb for k in keys):
            P26L.append([qa[k] for k in keys]); PFLL.append([qb[k] for k in keys])
    P26, PFL = np.array(P26L), np.array(PFLL); EPS = 1e-12
    rs = rank(spur); rS = rank(S); S_res = rS - (rS @ rs) / (rs @ rs) * rs
    out = {}
    for i, kn in enumerate(keys):
        cand = [(kn, None, M26[:, i], MFL[:, i], P26[:, i], PFL[:, i], 1)]
        for j, kd in enumerate(keys):
            if i == j: continue
            if np.any(np.abs(M26[:, j]) < EPS) or np.any(np.abs(MFL[:, j]) < EPS) or np.any(np.abs(P26[:, j]) < EPS) or np.any(np.abs(PFL[:, j]) < EPS): continue
            cand.append((kn, kd, M26[:, i] / M26[:, j], MFL[:, i] / MFL[:, j], P26[:, i] / P26[:, j], PFL[:, i] / PFL[:, j], 0))
        for kn_, kd_, v26, vfl, p26, pfl, g in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
            if np.any(v26 <= 0) or np.any(vfl <= 0): continue
            A = -spearman(v26, S); B = float((pfl >= p26).mean()) if len(p26) else 0.0
            rv = rank(v26); v_res = rv - (rv @ rs) / (rs @ rs) * rs
            AP = -float(np.corrcoef(v_res, S_res)[0, 1]) if v_res.std() > 1e-9 else 0.0
            D = spearman(v26, spur)
            out[(kn_, kd_)] = dict(A=A, B=B, D=D, AP=AP, G=g)
    meta = dict(n_steep=int(M26.shape[0]), n_flat=int(MFL.shape[0]), n_pairs=int(len(P26L)))
    return out, meta


log('45°（首读留出）…')
D45, m45 = axes(f'{ENV}/ledger/env2_diag45_runs.jsonl', f'{ENV}/runs_diag45', 'hidden')
log('  %d 候选  steep=%d flat=%d pairs=%d  (%.0fs)' % (len(D45), m45['n_steep'], m45['n_flat'], m45['n_pairs'], time.time() - t0))

d = np.load(f'{ENV}/e71_innov/multienv_metrology/E71_PILOT_AXES.npz')
num = d['num'].astype(str); den = d['den'].astype(str)
keys = [(num[i], den[i] if den[i] else None) for i in range(len(num))]
mask = np.array([k in D45 for k in keys])
idx = np.where(mask)[0]
log('与试点对齐：共同 %d，45° 缺失 %d，45° 独有 %d（忽略）' % (len(idx), int((~mask).sum()), len(D45) - len(idx)))


def col45(key): return np.array([D45[keys[i]][key] for i in idx])


np.savez(f'{FIN}/E73_AXES45.npz',
         num=num[idx], den=den[idx], G=d['G'][idx],
         A_z=d['A_z'][idx], B_z=d['B_z'][idx], D_z=d['D_z'][idx], AP_z=d['AP_z'][idx],
         A_m=d['A_m'][idx], B_m=d['B_m'][idx], D_m=d['D_m'][idx], AP_m=d['AP_m'][idx],
         A_45=col45('A'), B_45=col45('B'), D_45=col45('D'), AP_45=col45('AP'))
meta = dict(diag45=m45, n_common=int(mask.sum()), n_missing_in_diag45=int((~mask).sum()),
            low_n=bool(m45['n_steep'] < 15), prereg_sha=SEAL, script='e73c_axes45.py', script_sha=SCRIPT_SHA,
            metric_search_file=os.path.realpath(metric_search.__file__),
            recipe='e67b_recipe_transfer.axes 勘误后口径, 与 e71a_pilot_axes.py 逐字一致',
            elapsed_s=round(time.time() - t0, 1))
json.dump(meta, open(f'{FIN}/E73_AXES45_META.json', 'w'), indent=1, ensure_ascii=False)
log('E73C_DONE  %.0f 秒  n_45_steep=%d low_n=%s' % (time.time() - t0, m45['n_steep'], meta['low_n']))
