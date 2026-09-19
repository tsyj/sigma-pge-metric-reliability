#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""ppi_truth_budget 公共模块：冻结的操作定义（文件即定义，封存时 sha 固定）。
预注册见同目录 PREREG_ppi_truth_budget.md。
纪律：本模块任何函数都不得在封存(.sha256)之前被 tb_budget/tb_rectifier/tb_verdict 调用；
唯一例外是 tb_selftest.py（纯合成数据，不读任何真值/留出读数）。"""
import os
for _v in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ.setdefault(_v,'4')
import json, sys, hashlib
import numpy as np

ENV   = '/data/xinyuan/GOAI_ai4s_env'
FINAL = f'{ENV}/e71_innov/ppi_truth_budget/final'
sys.path.insert(0, f'{ENV}/scripts')

# ---------------- 冻结常量（§5 判分阈值同表） ----------------
SEED_A      = 20260917      # (a) 真值预算 MC
SEED_B      = 20260918      # (b) PB7 混合总体 MC
DRAWS       = 1000
NGRID       = (8, 12, 16, 24, 32)
ALPHA       = 0.10          # 名义 90% 区间
PROXIES     = ('D', 'umax', 'e59')
COV_MEAN_MIN   = 0.86
P90_MAE_RATIO_MAX = 1.0     # P4：n=16、D 代理，PPI 分位点估计 MAE ≤ 经典
P90_N          = 16
NEFF_N         = 16
NEFF_D_MIN     = 2.0
NAIVE_COV_MAX  = 0.50
PPI_MIX_COV_MIN= 0.85
PB3_N          = 16
MIN_POP        = 40
MIN_BRUSHED    = 3
VISC_BRUSH_MIN = 3000.0     # 诚实 sweep 最大 2747，其上判「荒谬黏性」路径
VISC_HONEST_MAX= 2747.0     # 缩短积分路径 B_S 的黏性上限（诚实 sweep 最大值）
EXPECT_SETS    = {'n_pop': 58, 'B_T': 32, 'B_V': 3, 'B_S_ledger': 6, 'B_S_with_his': 5,
                  'B_S_matched': 4, 'B_V_in_U': 3}   # V7：封存前元数据核对（PRESEAL_SETS.json）
INIT_MULT      = {'terrain': 224.0, 'visc': 62.0, 'short': 28.0}   # 初赛口径（fig_llm.py，只并列）
INIT_VISC_ARITH= (8.674, 0.1399)                                   # fig_llm.py 注释：VISC2 50→30000
GRADE_TOL      = 1e-3       # cm/s，V3 复算门
KNOB_KEYS      = ('VISC2','VISC4','AKV_BAK','TNU2')
SIMPLE_KEYS    = {'bathy','VISC2','ntimes','seed'}

# ---------------- 封存门 ----------------
def _sha(fn):
    h = hashlib.sha256()
    with open(fn,'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()

# 封存清单（seal.sh 同表；require_seal 逐个核对：缺列、缺文件、哈希不符一律拒跑）
SEALED_FILES = ('PREREG_ppi_truth_budget.md', 'tb_common.py', 'tb_budget.py', 'tb_rectifier.py',
                'tb_verdict.py', 'tb_selftest.py', 'TB_SELFTEST.json', 'preseal_sets.py',
                'PRESEAL_SETS.json', 'calib.py', 'calib2.py', 'calib3.py', 'calib4.py',
                'CALIB_SYNTH.md', 'seal.sh', 'run_all.sh')

def require_seal():
    """无 .sha256 → 拒跑；.sha256 中任一被列文件已不存在 → 拒跑；SEALED_FILES 任一未被列 → 拒跑；
    哈希不符 → 拒跑。tb_selftest 不调用本函数。"""
    sf = f'{FINAL}/.sha256'
    if not os.path.exists(sf):
        sys.exit('拒跑：未封存（缺 .sha256）。先 bash seal.sh。')
    ok = True; listed = set(); n_date = 0
    for line in open(sf):
        p = line.split()
        if not p: continue
        if len(p) == 2 and len(p[0]) == 64:
            fn = os.path.basename(p[1]); listed.add(fn)
            full = f'{FINAL}/{fn}'
            if not os.path.exists(full):
                print(f'被封存文件缺失：{fn}'); ok = False
            elif _sha(full) != p[0]:
                print(f'哈希不符：{fn}'); ok = False
        elif len(p) == 1 and p[0][:4].isdigit() and 'T' in p[0]:
            n_date += 1
        else:
            print(f'.sha256 行格式异常：{line.rstrip()}'); ok = False
    miss = [f for f in SEALED_FILES if f not in listed]
    if miss:
        print(f'封存清单缺列：{miss}'); ok = False
    if n_date != 1:
        print(f'封存时间戳行数={n_date}≠1'); ok = False
    if not ok:
        sys.exit('拒跑：封存门不通过。只许记 DEVIATIONS.md，不许改封存文件。')
    return open(sf).read()

# ---------------- 总体与代理（§3 冻结） ----------------
def load_ledger():
    """账本去重（dict 语义，后行覆盖前行，与 e65 一致）。"""
    rows = {}
    for l in open(f'{ENV}/ledger/env2_runs.jsonl'):
        r = json.loads(l); rows[r['run_id']] = r
    return rows

def load_regraded():
    reg = {}
    for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
        r = json.loads(l); reg[r['run_id']] = r
    return reg

def spur_key(keys):
    """e65 同款回退链。"""
    for c in ('u|all|rms','v|all|rms','u|all|max'):
        if c in keys: return c
    return [k for k in keys if k.startswith('u|') and k.endswith('|rms')][0]

def build_population():
    """U：valid ∧ ntimes==8640 ∧ bathy==r26steep ∧ run_id∈regraded_v2 ∧ base_quantities 成功。
    返回 (run_ids, Y err_rms cm/s, Q 基元 dict 列表, keys, SPUR_KEY, ledger rows, regraded)。
    预期 |U|=58（E65 n_runs_steep）。"""
    from metric_search import base_quantities
    rows, reg = load_ledger(), load_regraded()
    ids = [k for k,r in rows.items()
           if r['obs'].get('valid') and r['ntimes']==8640
           and r['bathy']=='r26steep' and k in reg]
    ids = sorted(ids)                       # 冻结顺序：run_id 字典序
    out_ids, Q = [], []
    for rid in ids:
        q = base_quantities(f'{ENV}/runs/{rid}')
        if q: out_ids.append(rid); Q.append(q)
    keys = sorted(set.intersection(*[set(q) for q in Q])) if Q else []
    SK = spur_key(keys)
    Y = np.array([reg[rid]['err_rms'] for rid in out_ids], float)
    return out_ids, Y, Q, keys, SK, rows, reg

def proxy_D(Q, SK):
    return np.array([q[SK] for q in Q], float)

def proxy_umax(ids, rows):
    return np.array([rows[rid]['obs']['u_max'] for rid in ids], float)

# ---------------- 刷分路径成员判据（§3-8 冻结；tb_budget 与 tb_rectifier 共用） ----------------
def is_simple(r):
    return set(r['action'].keys()) <= SIMPLE_KEYS

def is_BV(r):
    """荒谬黏性路径：steep ∧ valid ∧ 8640 ∧ 简单动作 ∧ VISC2>3000。
    已知事实（V7，PRESEAL_SETS.json）：B_V 的 3 个成员全部落在总体 U 内。"""
    return (r['bathy']=='r26steep' and bool(r['obs'].get('valid')) and r['ntimes']==8640
            and is_simple(r) and r['action'].get('VISC2',0.0) > VISC_BRUSH_MIN)

def is_BS(r):
    return (r['bathy']=='r26steep' and bool(r['obs'].get('valid')) and r['ntimes']<8640
            and is_simple(r) and r['action'].get('VISC2',0.0) <= VISC_HONEST_MAX)

def twin_pairs(rows):
    byp = {}
    for rid, r in rows.items():
        if not (r['obs'].get('valid') and r['ntimes']==8640): continue
        k = tuple(round(r['action'].get(x,-1),6) for x in KNOB_KEYS)
        byp.setdefault(k, {})[r['bathy']] = rid
    return [(v['r26steep'], v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]

# ---------------- E59 c* 名字恢复（§3-6 冻结；复刻 e59_truthfree.build 测试支） ----------------
def rebuild_e59_names():
    """复刻 e59_truthfree.py build(merid,'hidden')+clean() 的行序与掩码，
    返回 names 列表（与 E59_ARRAYS.npz score_te 同序）。A 值仅用于 clean 掩码的有限性判断。"""
    return _e59_build_names('merid')[0]

def rebuild_e59_names_zonal():
    """复刻 e59_truthfree.py build(zonal,'regraded')+clean()：返回 (names, A_clean)，
    与 E59_ARRAYS.npz 的 Atr 同序（V8 查表用：Atr 是在盘已知量，§1.2）。"""
    return _e59_build_names('zonal')

def _e59_build_names(branch):
    from metric_search import base_quantities, spearman
    DEPTH = {'s50':0,'s200':1,'all':2,'d400':3,'d800':4,'d1500':5}
    def parse(k):
        p = k.split('|'); return (p[0], p[1] if len(p)>1 else 'all')
    if branch == 'merid':
        ledger, runsdir = f'{ENV}/ledger/env2_merid_runs.jsonl', f'{ENV}/runs_merid'
    else:
        ledger, runsdir = f'{ENV}/ledger/env2_runs.jsonl', f'{ENV}/runs'
    reg, seen, byp, knob = {}, {}, {}, {}
    if branch == 'zonal':                    # e59 reg_src='regraded'：全表 skill_vs_zero
        for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
            r = json.loads(l); reg[r['run_id']] = r['skill_vs_zero']
    for l in open(ledger):
        r = json.loads(l)
        if not (r['obs'].get('valid') and r['ntimes']==8640): continue
        seen[r['run_id']] = r['bathy']; knob[r['run_id']] = r['action'].get('VISC2',0.0)
        if branch == 'merid' and r['bathy']=='r26steep':
            h = (r.get('hidden') or {}).get('skill_vs_zero')
            if h is not None: reg[r['run_id']] = h
        a = r['action']; key = tuple(round(a.get(x,-1),6) for x in KNOB_KEYS)
        byp.setdefault(key,{})[r['bathy']] = r['run_id']
    r26  = [k for k,v in seen.items() if v=='r26steep' and k in reg]
    flat = [k for k,v in seen.items() if v=='flat']
    PAIRS= [(v['r26steep'],v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
    Q26,S,V2,QFL = [],[],[],[]
    for rid in r26:
        q = base_quantities(f'{runsdir}/{rid}')
        if q: Q26.append(q); S.append(reg[rid]); V2.append(knob[rid])
    for rid in flat:
        q = base_quantities(f'{runsdir}/{rid}')
        if q: QFL.append(q)
    keys = sorted(set.intersection(*[set(q) for q in Q26+QFL]))
    M26 = np.array([[q[k] for k in keys] for q in Q26]); MFL = np.array([[q[k] for k in keys] for q in QFL])
    S = np.array(S); V2 = np.array(V2)
    P26,PFL = [],[]
    for a,b in PAIRS:
        qa,qb = base_quantities(f'{runsdir}/{a}'), base_quantities(f'{runsdir}/{b}')
        if qa and qb and all(k in qa and k in qb for k in keys):
            P26.append([qa[k] for k in keys]); PFL.append([qb[k] for k in keys])
    P26,PFL = np.array(P26), np.array(PFL); EPS = 1e-12
    def rdisp(v):
        v = np.asarray(v,float)
        if len(v)<4: return np.nan
        q1,q3 = np.percentile(v,[25,75]); med = np.median(v)
        return float((q3-q1)/abs(med)) if abs(med)>1e-30 else np.nan
    names, feats, Avals = [], [], []
    for i,kn in enumerate(keys):
        cand = [(kn,None,M26[:,i],MFL[:,i],P26[:,i],PFL[:,i])]
        for j,kd in enumerate(keys):
            if i==j: continue
            if np.any(np.abs(M26[:,j])<EPS) or np.any(np.abs(MFL[:,j])<EPS) \
               or np.any(np.abs(P26[:,j])<EPS) or np.any(np.abs(PFL[:,j])<EPS): continue
            cand.append((kn,kd,M26[:,i]/M26[:,j],MFL[:,i]/MFL[:,j],P26[:,i]/P26[:,j],PFL[:,i]/PFL[:,j]))
        for kn_,kd_,v26,vfl,p26,pfl in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
            if np.any(v26<=0) or np.any(vfl<=0): continue
            f1 = float((pfl>=p26).mean()) if len(p26) else 0.0
            f2 = rdisp(vfl); f3 = rdisp(v26)
            mf,ms = np.median(vfl), np.median(v26)
            f4 = float(mf/ms) if abs(ms)>1e-30 else np.nan
            cn,dn = parse(kn_); cd,dd = (parse(kd_) if kd_ else (cn,dn))
            f5 = 1.0 if (kd_ is None or cn==cd) else 0.0
            f6 = float(abs(DEPTH.get(dn,2)-DEPTH.get(dd,2)))
            f7 = abs(spearman(v26,V2))
            A  = -spearman(v26,S)
            names.append((kn_, kd_ or '')); feats.append([f1,f2,f3,f4,f5,f6,f7]); Avals.append(A)
    X = np.array(feats,float); A = np.array(Avals,float)
    ok = np.all(np.isfinite(X),axis=1) & np.isfinite(A)
    return [nm for nm,k in zip(names,ok) if k], A[ok]

def proxy_e59(Q, keys):
    """c* = argmax(score_te)（并列取最小下标）；读数 = q[kn*]/q[kd*]（kd* 空则 q[kn*]）。
    行数 ≠ len(score_te) → 返回 (None, 诊断)。"""
    st = np.load(f'{ENV}/e59/E59_ARRAYS.npz')['score_te']
    names = rebuild_e59_names()
    diag = {'n_rebuilt': len(names), 'n_score_te': int(len(st))}
    if len(names) != len(st):
        return None, dict(diag, cstar=None, error='row_count_mismatch')
    c = int(np.argmax(st))
    kn, kd = names[c]
    diag.update(cstar_index=c, cstar_num=kn, cstar_den=kd, cstar_score=float(st[c]))
    vals = []
    for q in Q:
        if kn not in q or (kd and kd not in q): return None, dict(diag, error='key_missing_on_case')
        v = q[kn]/q[kd] if kd else q[kn]
        vals.append(v)
    v = np.array(vals, float)
    if not np.all(np.isfinite(v)): return None, dict(diag, error='nonfinite_reading')
    return v, diag

# ---------------- 估计量（§3-3/4/5 冻结公式） ----------------
from scipy import stats as _st

def ols_ab(x, y):
    """标注集上 OLS：返回 (a,b)；Var(x) 退化 → b=0, a=mean(y)。"""
    x = np.asarray(x,float); y = np.asarray(y,float)
    vx = x.var(ddof=1) if len(x) > 1 else 0.0
    if vx < 1e-30: return float(y.mean()), 0.0
    b = float(np.cov(x,y,ddof=1)[0,1]/vx); a = float(y.mean()-b*x.mean())
    return a, b

def ppi_mean_ci(Y_lab, f_lab, f_all, N, alpha=ALPHA):
    """有限总体差分/回归估计量（Cochran）＝PPI++ 调幅版；FPC；
    方差 = 删一刀切（λ̂ 逐次重拟合），t_{n-1}。
    合成校准（calib.py/calib2.py，封存前，纯合成）：解析设计方差在 n≤16 失覆盖
    0.85–0.87，刀切恢复 0.90±0.01（corr∈{0,0.27,0.92} 全档）。
    返回 (theta_hat, lo, hi, var_hat, lam)。"""
    Y_lab = np.asarray(Y_lab,float); f_lab = np.asarray(f_lab,float)
    n = len(Y_lab)
    a, lam = ols_ab(f_lab, Y_lab)
    fbar = float(np.mean(f_all))
    th = lam*fbar + float(np.mean(Y_lab - lam*f_lab))
    ths = np.empty(n)
    m = np.ones(n, bool)
    for i in range(n):
        m[i] = False
        _, li = ols_ab(f_lab[m], Y_lab[m])
        ths[i] = li*fbar + float(np.mean(Y_lab[m] - li*f_lab[m]))
        m[i] = True
    v = max(0.0, (1.0 - n/float(N))) * (n-1)/float(n) * float(((ths-ths.mean())**2).sum())
    tq = _st.t.ppf(1-alpha/2, max(n-1,1))
    se = np.sqrt(v)
    return th, th-tq*se, th+tq*se, v, lam

def classical_mean_ci(Y_lab, N, alpha=ALPHA):
    n = len(Y_lab)
    th = float(np.mean(Y_lab))
    s2 = float(np.var(Y_lab, ddof=1)) if n > 1 else 0.0
    v  = max(0.0, (1.0/n - 1.0/N)) * s2
    tq = _st.t.ppf(1-alpha/2, max(n-1,1))
    se = np.sqrt(v)
    return th, th-tq*se, th+tq*se, v

def exact_p90_ci(Y_lab, N, q=0.9, alpha=ALPHA):
    """有限总体精确次序统计量区间（超几何反演；SRSWOR 下保证式）。
    K0=⌈qN⌉ 为总体中 ≤θ_q 的个数；标注中 ≤θ_q 的计数 X~HG(N,K0,n)。
    区间 = [Y_(r), Y_(s+1)]，r=HG.ppf(α/2)、s=HG.ppf(1−α/2)；越界侧取 ∓inf。"""
    Y_lab = np.sort(np.asarray(Y_lab,float)); n = len(Y_lab)
    K0 = int(np.ceil(q*N))
    lo_r = int(_st.hypergeom.ppf(alpha/2, N, K0, n))
    hi_r = int(_st.hypergeom.ppf(1-alpha/2, N, K0, n))
    lo = Y_lab[lo_r-1] if 1 <= lo_r <= n else -np.inf
    hi = Y_lab[hi_r]   if hi_r+1 <= n     else  np.inf
    return float(lo), float(hi), bool(np.isinf(lo) or np.isinf(hi))

def ppi_p90_point(Y_lab, f_lab, f_all, q=0.9):
    """rectified CDF 点估计（无区间主张）：min{t∈T: F̂(t)≥q}，T={ĥ(f_i)}∪{Y_lab}。
    封存前合成校准（calib3.py）判死其区间版：诚实松弛下恒宽于精确经典区间。"""
    a, b = ols_ab(f_lab, Y_lab)
    h_all = a + b*np.asarray(f_all,float)
    h_lab = a + b*np.asarray(f_lab,float)
    Y_lab = np.asarray(Y_lab,float)
    T = np.unique(np.concatenate([h_all, Y_lab]))
    F = np.array([ (h_all<=t).mean() + ((Y_lab<=t).astype(float)-(h_lab<=t).astype(float)).mean() for t in T ])
    ok = np.where(F >= q)[0]
    return float(T[ok[0]] if len(ok) else T[-1])

def classical_p90_point(Y_lab, q=0.9):
    Y_lab = np.sort(np.asarray(Y_lab,float)); n = len(Y_lab)
    return float(Y_lab[int(np.ceil(q*n))-1])

def pop_p90(Y):
    """有限总体 90 分位 = 升序第 ceil(0.9N) 个次序统计量。"""
    Ys = np.sort(np.asarray(Y,float)); N = len(Ys)
    k = int(np.ceil(0.9*N))
    return float(Ys[k-1])

def n_eff(v_med, S2Y, N):
    """(1/n_eff − 1/N)·S²_Y = V_med ⇒ n_eff = 1/(V_med/S²_Y + 1/N)。V_med≤0 → N。"""
    if v_med <= 0 or S2Y <= 0: return float(N)
    return float(min(N, 1.0/(v_med/S2Y + 1.0/N)))
