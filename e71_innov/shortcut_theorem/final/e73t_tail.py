#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E73 shortcut_theorem · 步骤 T：尾部附验首算（PREREG §6：H1/H2，不计入真预测）。

输入全为纬向盘上数据（ledger/env2_runs.jsonl + runs/ + regraded_v2.jsonl）；封存门控只为保住
"未算先押"——本脚本在封存前从未被运行过。输出：E73_TAIL.json（只写本目录）。
运行：systemd-run --user --scope -p MemoryMax=16G nice -n 19 env OMP_NUM_THREADS=8 <python> e73t_tail.py
"""
import hashlib, json, os, sys, time
import numpy as np
from scipy.stats import kurtosis, mannwhitneyu

ENV = '/data/xinyuan/GOAI_ai4s_env'
FIN = f'{ENV}/e71_innov/shortcut_theorem/final'
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
SCRIPT_SHA = hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()
sys.path.insert(0, f'{ENV}/scripts')
import metric_search  # noqa: E402
assert os.path.realpath(metric_search.__file__).endswith('GOAI_ai4s_env/scripts/metric_search.py'), metric_search.__file__
from metric_search import base_quantities  # noqa: E402

t0 = time.time()
def log(*a): print(*a, flush=True)

def sp_argsort(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    if np.std(ra) == 0 or np.std(rb) == 0: return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])

# ---- 纬向数据装载（与 e71a_pilot_axes.py 的 axes() 同口径） ----
reg = {}
for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
    r = json.loads(l); reg[r['run_id']] = r['skill_vs_zero']
seen = {}; byp = {}
for l in open(f'{ENV}/ledger/env2_runs.jsonl'):
    r = json.loads(l)
    if not (r['obs'].get('valid') and r['ntimes'] == 8640): continue
    seen[r['run_id']] = r['bathy']
    a = r['action']; k = tuple(round(a.get(x, -1), 6) for x in ('VISC2', 'VISC4', 'AKV_BAK', 'TNU2'))
    byp.setdefault(k, {})[r['bathy']] = r['run_id']
r26 = [k for k, v in seen.items() if v == 'r26steep' and k in reg]
flat = [k for k, v in seen.items() if v == 'flat']
PAIRS = [(v['r26steep'], v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
Q26 = [q for q in (base_quantities(f'{ENV}/runs/{rid}') for rid in r26) if q]
QFL = [q for q in (base_quantities(f'{ENV}/runs/{rid}') for rid in flat) if q]
keys = sorted(set.intersection(*[set(q) for q in Q26 + QFL]))  # 与 axes() 逐字同口径
M26 = np.array([[q[k] for k in keys] for q in Q26])
MFL = np.array([[q[k] for k in keys] for q in QFL])
QP = [(qa, qb) for qa, qb in ((base_quantities(f'{ENV}/runs/{a}'), base_quantities(f'{ENV}/runs/{b}'))
                              for a, b in PAIRS)
      if qa and qb and all(k in qa and k in qb for k in keys)]
P26 = np.array([[qa[k] for k in keys] for qa, qb in QP])
PFL = np.array([[qb[k] for k in keys] for qa, qb in QP])
n_steep, n_pairs = M26.shape[0], P26.shape[0]
log('steep=%d flat=%d pairs=%d keys=%d  (%.0fs)' % (n_steep, MFL.shape[0], n_pairs, len(keys), time.time() - t0))
EPS = 1e-12

# ---- 逐候选 κ / g / B（枚举滤器与 axes() 逐字同口径） ----
K, GG, BB, names = [], [], [], []
n_excluded_lt16 = 0  # PREREG §6："有效配对 <16 的候选整体剔除并记数"——专记被该滤器剔除者
for i, kn in enumerate(keys):
    cand = [(kn, None, M26[:, i], MFL[:, i], P26[:, i], PFL[:, i])]
    for j, kd in enumerate(keys):
        if i == j: continue
        if np.any(np.abs(M26[:, j]) < EPS) or np.any(np.abs(MFL[:, j]) < EPS) \
           or np.any(np.abs(P26[:, j]) < EPS) or np.any(np.abs(PFL[:, j]) < EPS):
            continue
        cand.append((kn, kd, M26[:, i] / M26[:, j], MFL[:, i] / MFL[:, j],
                     P26[:, i] / P26[:, j], PFL[:, i] / PFL[:, j]))
    for kn_, kd_, v26, vfl, p26, pfl in cand:
        if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
        if np.any(v26 <= 0) or np.any(vfl <= 0): continue
        ok = (p26 > 0) & (pfl > 0) & np.isfinite(p26) & np.isfinite(pfl)
        if ok.sum() < 16:  # 有效配对 <16 剔除（PREREG §6），单独记数
            n_excluded_lt16 += 1
            continue
        K.append(kurtosis(v26, fisher=True, bias=True))
        GG.append(float(np.median(np.log(pfl[ok] / p26[ok]))))
        BB.append(float((pfl >= p26).mean()))
        names.append((kn_, kd_ or ''))
K, GG, BB = np.array(K), np.array(GG), np.array(BB)
n_used = int(K.size)
log('候选 n_used=%d  n_excluded_lt16=%d  (%.0fs)' % (n_used, n_excluded_lt16, time.time() - t0))

# ---- H1：ρs(κ,|g|)>0，单侧置换 p（5000 次，seed 20260917，置换 κ） ----
absg = np.abs(GG)
rho_obs = sp_argsort(K, absg)
rk = np.argsort(np.argsort(K)).astype(float); rg = np.argsort(np.argsort(absg)).astype(float)
rk = (rk - rk.mean()) / rk.std(); rg = (rg - rg.mean()) / rg.std()
rng = np.random.default_rng(20260917)
cnt = 0
for _ in range(5000):
    if float(np.mean(rng.permutation(rk) * rg)) >= rho_obs: cnt += 1
p_h1 = (cnt + 1) / 5001

# ---- H2：κ[B<0.9] > κ[B≥0.9]，单侧 MW ----
dead, alive = K[BB < 0.9], K[BB >= 0.9]
if dead.size and alive.size:
    u, p_h2 = mannwhitneyu(dead, alive, alternative='greater')
    p_h2 = float(p_h2) if np.isfinite(p_h2) else None
else:
    p_h2 = None  # 空组：H2 不可检，记 None（方向未确认）

out = dict(script='e73t_tail.py', script_sha=SCRIPT_SHA, prereg_sha=SEAL, seed=20260917,
           metric_search_file=os.path.realpath(metric_search.__file__),
           n_steep=n_steep, n_pairs=n_pairs, n_used=n_used, n_excluded_lt16=n_excluded_lt16,
           H1=dict(rho_kappa_absg=round(rho_obs, 4), perm_p_one_sided=round(p_h1, 5),
                   n_perm=5000, direction_confirmed=bool(rho_obs > 0 and p_h1 < 0.05)),
           H2=dict(n_dead=int((BB < 0.9).sum()), n_alive=int((BB >= 0.9).sum()),
                   med_kappa_dead=round(float(np.median(dead)), 4) if dead.size else None,
                   med_kappa_alive=round(float(np.median(alive)), 4) if alive.size else None,
                   mw_p_one_sided=p_h2,
                   direction_confirmed=bool(p_h2 is not None and p_h2 < 0.05)),
           notes=['非独立证据：κ/g 与命题共用差值序列', '峰度≠尾指数，n=58 粗糙自报',
                  '渐近定理 vs 一次跳变映射松', '不计入真预测计数'],
           elapsed_s=round(time.time() - t0, 1))
json.dump(out, open(f'{FIN}/E73_TAIL.json', 'w'), indent=1, ensure_ascii=False)
log(json.dumps({k: out[k] for k in ('H1', 'H2')}, ensure_ascii=False))
log('E73T_DONE  %.0f 秒' % (time.time() - t0))
