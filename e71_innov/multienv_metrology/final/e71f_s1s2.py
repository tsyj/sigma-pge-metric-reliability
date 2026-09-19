#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E71M 正式版 · S 组次级检验（PREREG §6；产出文件名与判据封存时写死）。

S1 B 扩陡度：e60 四档 rx0 的逐候选 B 成员阵重算（B 配方与 e60/analyze_e60.py 逐字同源），
    p×e(4) G 研究（gstudy/rn_argsort 与 e71f_metrology.py 逐字同式）→ E71_FINAL_S1_E60.json。
    单一布尔式（verdict.py 判）：var_p_share >= 0.75。
S2 静止海负对照（探索性，不设通过线）：e56 BH93 无风静止态 7 对 VISC2 配对，
    B_rest 同配方重算；只报可算比例与 ρ(B_rest,B_z) → E71_FINAL_S2_BH93.json。

本脚本不在 PREREG §2 冻结表（§6 只冻结产出文件名与判据）；运行期自身 sha256 落入两个输出 JSON。
"""
import hashlib, json, math, os, sys, time
import numpy as np

ENV = '/data/xinyuan/GOAI_ai4s_env'
FIN = f'{ENV}/e71_innov/multienv_metrology/final'
PRE = f'{FIN}/PREREG_multienv_metrology.md'
SHA = f'{FIN}/PREREG_multienv_metrology.sha256'
if not os.path.exists(SHA):
    sys.exit('拒绝运行：预注册尚未封存。')
want = open(SHA).readline().split()[0]
if want != hashlib.sha256(open(PRE, 'rb').read()).hexdigest():
    sys.exit('拒绝运行：PREREG 与封存 sha256 不符。')
SELF_SHA = hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()
sys.path.insert(0, f'{ENV}/scripts')
from metric_search import base_quantities, spearman as spearman_ms

t0 = time.time()


def log(*a): print(*a, flush=True)


def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    if np.std(ra) == 0 or np.std(rb) == 0: return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def spearman_ties(a, b):
    def r(x):
        x = np.asarray(x, float)
        _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
        cs = np.cumsum(cnt) - (cnt + 1) / 2.0
        return cs[inv]
    ra, rb = r(a), r(b)
    if ra.std() == 0 or rb.std() == 0: return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def bmap_from_pairs(P26, PFL):
    """逐候选 B（e60/analyze_e60.py 逐字同源：单键+比值，配对 frac(vfl>=v26)）。"""
    keys = sorted(set.intersection(*[set(q) for q in P26 + PFL]))
    A26 = np.array([[q[k] for k in keys] for q in P26]); AFL = np.array([[q[k] for k in keys] for q in PFL])
    EPS = 1e-12; B = {}
    for i, kn in enumerate(keys):
        cand = [((kn, None), A26[:, i], AFL[:, i])]
        for j, kd in enumerate(keys):
            if i == j: continue
            if np.any(np.abs(A26[:, j]) < EPS) or np.any(np.abs(AFL[:, j]) < EPS): continue
            cand.append(((kn, kd), A26[:, i] / A26[:, j], AFL[:, i] / AFL[:, j]))
        for key, v26, vfl in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
            if np.any(v26 <= 0) or np.any(vfl <= 0): continue
            B[key] = float((vfl >= v26).mean())
    return B, len(keys)


def rn_argsort(x):
    return (np.argsort(np.argsort(x, kind='mergesort'), kind='mergesort') + 1.0) / (len(x) + 1.0)


def gstudy(xs):
    """与 e71f_metrology.py 逐字同式（argsort 版，k* 下钳 1）。"""
    X = np.stack([rn_argsort(x) for x in xs], axis=1); n_p, n_e = X.shape
    gm = X.mean(); pm = X.mean(1); em = X.mean(0)
    SS_p = n_e * ((pm - gm) ** 2).sum(); SS_e = n_p * ((em - gm) ** 2).sum()
    SS_tot = ((X - gm) ** 2).sum(); SS_res = SS_tot - SS_p - SS_e
    MS_p = SS_p / (n_p - 1); MS_res = SS_res / ((n_p - 1) * (n_e - 1))
    s2_res = MS_res; s2_p = max(0.0, (MS_p - MS_res) / n_e)
    tot = s2_p + s2_res

    def Gk(k): return s2_p / (s2_p + s2_res / k) if tot > 0 else 0.0
    kstar = None
    if s2_p > 0:
        kstar = max(1, int(math.ceil(4.0 * s2_res / s2_p - 1e-9)))
    return dict(var_p=round(float(s2_p), 6), var_pe_res=round(float(s2_res), 6),
                var_p_share=round(float(s2_p / tot), 4) if tot > 0 else None,
                G_of_k={str(k): round(float(Gk(k)), 4) for k in range(1, 11)},
                k_star_G0p8=kstar)


# ---------------- S1：e60 四档 rx0 ----------------
E60 = f'{ENV}/e60'
RX = ['020', '044', '060', '069']
RXV = {'020': 0.200, '044': 0.441, '060': 0.599, '069': 0.694}
runs = json.load(open(f'{E60}/E60_RX0.json'))
by = {}
for r in runs:
    if r.get('done') and not r.get('blowup'):
        by[(r['rx0'], r['bathy'], r['VISC2'])] = f"{E60}/runs/{r['tag']}"
V = sorted({k[2] for k in by})
Bmaps = {}; per_rx = {}
for rx in RX:
    P26, PFL = [], []
    for v in V:
        a = by.get((rx, 'steep', v)); b = by.get((rx, 'flat', v))
        if not (a and b): continue
        qa, qb = base_quantities(a), base_quantities(b)
        if qa and qb: P26.append(qa); PFL.append(qb)
    if len(P26) < 4:
        per_rx[rx] = dict(rx0=RXV[rx], n_pairs=len(P26), note='配对不足，弃')
        continue
    B, nk = bmap_from_pairs(P26, PFL)
    Bmaps[rx] = B
    per_rx[rx] = dict(rx0=RXV[rx], n_pairs=len(P26), n_keys=nk, n_candidates=len(B),
                      n_B_ge_0p9=sum(1 for x in B.values() if x >= 0.9))
    log('S1 rx0=%.3f 配对 %d 候选 %d (%.0fs)' % (RXV[rx], len(P26), len(B), time.time() - t0))
common = sorted(set.intersection(*[set(Bmaps[rx]) for rx in Bmaps]), key=lambda k: (k[0], k[1] or ''))
X = [np.array([Bmaps[rx][k] for k in common]) for rx in Bmaps]
g = gstudy(X)
gt_pairs = {'%s_vs_%s' % (r1, r2): round(spearman(np.array([Bmaps[r1][k] for k in common]),
                                                  np.array([Bmaps[r2][k] for k in common])), 4)
            for i, r1 in enumerate(list(Bmaps)) for r2 in list(Bmaps)[i + 1:]}
s1 = dict(module='S1_e60_B_gstudy', date=time.strftime('%F %T'), prereg_sha=want, code_sha=SELF_SHA,
          design='p(%d) x e(%d: rx0 %s), 环境内秩归一化(argsort), 相对G; B配方=analyze_e60 同源' %
                 (len(common), len(Bmaps), ','.join('%.3f' % RXV[r] for r in Bmaps)),
          per_rx=per_rx, n_common=len(common), pairwise_spearman_B=gt_pairs,
          var_p=g['var_p'], var_pe_res=g['var_pe_res'], var_p_share=g['var_p_share'],
          G_of_k=g['G_of_k'], k_star_G0p8=g['k_star_G0p8'],
          prediction='var_p_share >= 0.75（PREREG §6, verdict.py 机判）',
          caveat='e60 为 nrec=4 短算例、VISC2 单旋钮 7 档；候选空间与主线 15376 不同源（e60 自己的键空间），不与主线数字混排')
json.dump(s1, open(f'{FIN}/E71_FINAL_S1_E60.json', 'w'), indent=1, ensure_ascii=False)
log('S1 done: n_common=%d var_p_share=%s k*=%s (%.0fs)' % (len(common), g['var_p_share'], g['k_star_G0p8'], time.time() - t0))

# ---------------- S2：e56 BH93 静止海负对照 ----------------
E56 = f'{ENV}/e56'
recs = [r for r in json.load(open(f'{E56}/E56_BH93.json')) if isinstance(r, dict) and r.get('done') and not r.get('blowup')]
byv = {}
for r in recs:
    byv.setdefault(r['VISC2'], {})[r['bathy']] = f"{E56}/runs/{r['tag']}"
P26, PFL, used_v = [], [], []
for v in sorted(byv):
    d_ = byv[v]
    if 'r26steep' in d_ and 'flat' in d_:
        qa, qb = base_quantities(d_['r26steep']), base_quantities(d_['flat'])
        if qa and qb:
            P26.append(qa); PFL.append(qb); used_v.append(v)
s2 = dict(module='S2_bh93_negctrl', date=time.strftime('%F %T'), prereg_sha=want, code_sha=SELF_SHA,
          n_pairs=len(P26), visc2_values=used_v,
          note='BH93 无风静止海: 风驱环流前提消失, 预期大量候选退化不可算; 探索性, 不设通过线 (PREREG §6)')
if len(P26) >= 4:
    Brest, nk = bmap_from_pairs(P26, PFL)
    d = np.load(f'{FIN}/E71_FINAL_AXES.npz')
    num = d['num'].astype(str); den = d['den'].astype(str); B_z = d['B_z']
    name2i = {(num[i], den[i] if den[i] else None): i for i in range(len(num))}
    inter = [k for k in Brest if k in name2i]
    s2.update(n_keys=nk, n_computable_rest=len(Brest),
              n_main_candidates=len(name2i),
              n_computable_in_main=len(inter),
              frac_computable_of_main=round(len(inter) / len(name2i), 4),
              rho_Brest_Bz=round(spearman(np.array([Brest[k] for k in inter]),
                                          B_z[[name2i[k] for k in inter]]), 4) if len(inter) >= 10 else None,
              rho_Brest_Bz_ties=round(spearman_ties(np.array([Brest[k] for k in inter]),
                                                    B_z[[name2i[k] for k in inter]]), 4) if len(inter) >= 10 else None,
              B_rest_hist=dict(ge_0p9=sum(1 for x in Brest.values() if x >= 0.9),
                               le_0p1=sum(1 for x in Brest.values() if x <= 0.1)))
else:
    s2.update(n_computable_rest=0, degenerate='几乎全部量为零场, 配对可算数 <4, B_rest 不可算')
json.dump(s2, open(f'{FIN}/E71_FINAL_S2_BH93.json', 'w'), indent=1, ensure_ascii=False)
log('S2 done: pairs=%d computable=%s rho=%s (%.0fs)' %
    (len(P26), s2.get('n_computable_rest'), s2.get('rho_Brest_Bz'), time.time() - t0))
log('E71F_S1S2_DONE %.0fs' % (time.time() - t0))
