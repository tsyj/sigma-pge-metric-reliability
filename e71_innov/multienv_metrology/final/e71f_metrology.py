#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E71M 正式版 · 步骤二：六模块三环境分析 → E71_FINAL_RESULTS.json（判分见 e71f_verdict.py）。

模块公式冻结自 e71b_pilot_metrology.py，只扩到 3 环境；与试点的全部差异见 PREREG §2（共 3 处，
均为扩展或下限修正，无判据改动）。所有 P 判据在 PREREG 写死，本脚本只落数，不判分。

M1  MTMM 6×6：特质{A,B}×方法{纬向,经向,45°}，Campbell-Fiske 三个方法对逐格判定（双 spearman 版）。
M2  G 理论 p×e(3)，环境内秩归一化，相对 G；argsort 版＋平均秩版；折叠集 bootstrap CI（B=1000, seed=20260917，描述性）。
M3  ICP 式不变性 3 环境：逐候选 Fisher-z 加权 Q 检验（df=2, p=exp(-Q/2)），BH-FDR 5%；
    另按试点原式复算 2 环境（纬/经）拒绝集以定位 88 把 Inv2 的"追加判死"。
M4  Millsap/D 机制账本：45° 内部结构、D 直通车（P2）、变节率（P6）、B 迁移。
M5  折叠候选集复算（名义 N 问题同框件）。
M6  决策级：三对 κ/Jaccard、三向交集、S_A 内受限收敛（P3）。
"""
import hashlib, json, math, os, sys, time
import numpy as np

ENV = '/data/xinyuan/GOAI_ai4s_env'
MOD = f'{ENV}/e71_innov/multienv_metrology'
FIN = f'{MOD}/final'
PRE = f'{FIN}/PREREG_multienv_metrology.md'
SHA = f'{FIN}/PREREG_multienv_metrology.sha256'
t0 = time.time()


def log(*a): print(*a, flush=True)


def seal_gate():
    if not os.path.exists(SHA):
        sys.exit('拒绝运行：预注册尚未封存。')
    want = open(SHA).readline().split()[0]
    got = hashlib.sha256(open(PRE, 'rb').read()).hexdigest()
    if want != got:
        sys.exit('拒绝运行：PREREG 与封存 sha256 不符。')
    return want


SEAL = seal_gate()


def sha_of(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def spearman(a, b):
    """scripts/metric_search.py 逐字口径（argsort 秩，不处理并列）——判定主口径，对锚。"""
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    if np.std(ra) == 0 or np.std(rb) == 0: return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def spearman_ties(a, b):
    """平均秩版（敏感性口径，同报；仅 P4b 按 PREREG 用本版判定）。"""
    def r(x):
        x = np.asarray(x, float); o = np.argsort(x, kind='mergesort')
        rk = np.empty(len(x)); rk[o] = np.arange(len(x), dtype=float)
        _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
        cs = np.cumsum(cnt) - (cnt + 1) / 2.0
        return cs[inv]
    ra, rb = r(a), r(b)
    if ra.std() == 0 or rb.std() == 0: return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


d = np.load(f'{FIN}/E71_FINAL_AXES.npz', allow_pickle=False)
meta = json.load(open(f'{FIN}/E71_FINAL_AXES_META.json'))
A_z, B_z, D_z, AP_z = d['A_z'], d['B_z'], d['D_z'], d['AP_z']
A_m, B_m, D_m, AP_m = d['A_m'], d['B_m'], d['D_m'], d['AP_m']
A_45, B_45, D_45, AP_45 = d['A_45'], d['B_45'], d['D_45'], d['AP_45']
G = d['G']; num = d['num'].astype(str); den = d['den'].astype(str)
N = len(A_z)
n_z = meta['zonal']['n_steep']; n_m = meta['merid']['n_steep']; n_45 = meta['diag45']['n_steep']
log('载入 %d 候选  n_z=%d n_m=%d n_45=%d  (%.1fs)' % (N, n_z, n_m, n_45, time.time() - t0))

res = dict(module='multienv_metrology_final', date=time.strftime('%F %T'),
           prereg_sha=SEAL,
           code_sha=dict(axes=sha_of(f'{FIN}/e71f_axes45.py'),
                         metrology=sha_of(os.path.abspath(__file__)),
                         verdict=sha_of(f'{FIN}/e71f_verdict.py')),
           run_meta=dict(n_candidates=int(N), n_z=n_z, n_m=n_m, n_45=n_45,
                         n_missing_in_diag45=meta['n_missing_in_diag45'],
                         low_n=bool(meta['low_n']),
                         intersection_lt_15000=bool(N < 15000),
                         pairs=dict(zonal=meta['zonal']['n_pairs'], merid=meta['merid']['n_pairs'],
                                    diag45=meta['diag45']['n_pairs'])))

# ---------- 门与锚 ----------
gate_z = (A_z >= 0.7) & (B_z >= 0.9)
gate_m = (A_m >= 0.7) & (B_m >= 0.9)
gate_45 = (A_45 >= 0.7) & (B_45 >= 0.9)
S_A_mask = gate_z
anchors = dict(
    rho_Az_Bz=round(spearman(A_z, B_z), 4),      # E65: -0.6742
    rho_Dz_Az=round(spearman(D_z, A_z), 4),      # E65: +0.9762
    rho_Dz_Bz=round(spearman(D_z, B_z), 4),      # E65: -0.661
    rho_APz_Bz=round(spearman(AP_z, B_z), 4),    # E66: -0.4778
    n_S_A=int(gate_z.sum()),                                     # 204
    n_S_A_survive_merid=int((gate_z & gate_m).sum()),            # E67B: 88
    n_gate_45=int(gate_45.sum()),                                # E67B 底率 0.0295 → ≈454
    n_S_A_survive_45=int((gate_z & gate_45).sum()),              # E67B: 140
    n_triple=int((gate_z & gate_m & gate_45).sum()),             # E67B: 80
)
anchors_pass = (abs(anchors['rho_Az_Bz'] + 0.6742) < 0.01 and abs(anchors['rho_Dz_Az'] - 0.9762) < 0.01
                and abs(anchors['rho_Dz_Bz'] + 0.661) < 0.01 and abs(anchors['rho_APz_Bz'] + 0.4778) < 0.01
                and anchors['n_S_A'] == 204 and anchors['n_S_A_survive_merid'] == 88
                and anchors['n_S_A_survive_45'] == 140 and anchors['n_triple'] == 80
                and 450 <= anchors['n_gate_45'] <= 458)
res['anchors'] = anchors
res['anchors_pass'] = bool(anchors_pass)
log('锚：%s → %s' % (json.dumps(anchors), '全过' if anchors_pass else '!!!未对上（管线存疑，判分照跑但打旗）!!!'))

# ---------- 三对环境成对统计（P1/P2 的直接输入） ----------
def pairstats(Ax, Bx, APx, Dx, Ay, By, APy, Dy):
    return dict(rho_A=round(spearman(Ax, Ay), 4), rho_B=round(spearman(Bx, By), 4),
                rho_A_ties=round(spearman_ties(Ax, Ay), 4), rho_B_ties=round(spearman_ties(Bx, By), 4),
                rho_AP=round(spearman(APx, APy), 4), rho_AP_ties=round(spearman_ties(APx, APy), 4),
                rho_D=round(spearman(Dx, Dy), 4))


res['pairs'] = {
    'z_m': pairstats(A_z, B_z, AP_z, D_z, A_m, B_m, AP_m, D_m),
    'z_45': pairstats(A_z, B_z, AP_z, D_z, A_45, B_45, AP_45, D_45),
    'm_45': pairstats(A_m, B_m, AP_m, D_m, A_45, B_45, AP_45, D_45),
}
p45 = res['pairs']['z_45']
log('z-45: ρ(A,A)=%+.4f ρ(B,B)=%+.4f ρ(A⊥,A⊥)=%+.4f | 塌方=%.4f' %
    (p45['rho_A'], p45['rho_B'], p45['rho_AP'], p45['rho_A'] - p45['rho_AP']))

# ---------- M1 MTMM 6×6（双 spearman 版） ----------
cols = [A_z, B_z, A_m, B_m, A_45, B_45]
names = ['A_zonal', 'B_zonal', 'A_merid', 'B_merid', 'A_diag45', 'B_diag45']


def mtmm(cs, fn):
    M = np.ones((len(cs), len(cs)))
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            M[i, j] = M[j, i] = fn(cs[i], cs[j])
    return M


M6 = mtmm(cols, spearman)
M6t = mtmm(cols, spearman_ties)
iA = {'z': 0, 'm': 2, '45': 4}; iB = {'z': 1, 'm': 3, '45': 5}
cf = {}
for (e1, e2) in (('z', 'm'), ('z', '45'), ('m', '45')):
    for tr, idx_t, idx_o in (('A', iA, iB), ('B', iB, iA)):
        conv = M6[idx_t[e1], idx_t[e2]]
        htmm = [M6[iA[e1], iB[e1]], M6[iA[e2], iB[e2]]]
        hthm = [M6[idx_t[e1], idx_o[e2]], M6[idx_o[e1], idx_t[e2]]]
        cf['%s_%s_%s' % (tr, e1, e2)] = dict(
            convergent=round(float(conv), 4),
            C1_gt_0p3=bool(conv > 0.3),
            C2_gt_hetero_hetero=bool(conv > max(abs(x) for x in hthm)),
            C3_gt_hetero_mono=bool(conv > max(abs(x) for x in htmm)))
res['M1_mtmm6'] = dict(order=names,
                       matrix=[[round(float(x), 4) for x in row] for row in M6],
                       matrix_ties=[[round(float(x), 4) for x in row] for row in M6t],
                       campbell_fiske=cf)
log('M1 6×6 done (%.1fs)' % (time.time() - t0))

# ---------- M2 G 理论 p×e(3) ----------
def rn_argsort(x):
    return (np.argsort(np.argsort(x, kind='mergesort'), kind='mergesort') + 1.0) / (len(x) + 1.0)


def rn_ties(x):
    x = np.asarray(x, float); o = np.argsort(x, kind='mergesort')
    rk = np.empty(len(x)); rk[o] = np.arange(len(x), dtype=float)
    _, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
    cs = np.cumsum(cnt) - (cnt + 1) / 2.0
    return (cs[inv] + 1.0) / (len(x) + 1.0)


def gstudy(xs, rnfn):
    X = np.stack([rnfn(x) for x in xs], axis=1); n_p, n_e = X.shape
    gm = X.mean(); pm = X.mean(1); em = X.mean(0)
    SS_p = n_e * ((pm - gm) ** 2).sum(); SS_e = n_p * ((em - gm) ** 2).sum()
    SS_tot = ((X - gm) ** 2).sum(); SS_res = SS_tot - SS_p - SS_e
    MS_p = SS_p / (n_p - 1); MS_res = SS_res / ((n_p - 1) * (n_e - 1))
    s2_res = MS_res; s2_p = max(0.0, (MS_p - MS_res) / n_e)
    tot = s2_p + s2_res

    def Gk(k): return s2_p / (s2_p + s2_res / k) if tot > 0 else 0.0
    kstar = None
    if s2_p > 0:
        kstar = max(1, int(math.ceil(4.0 * s2_res / s2_p - 1e-9)))  # 与试点唯一公式差异：下钳 1（PREREG §2 已申明）
    return dict(var_p=round(float(s2_p), 6), var_pe_res=round(float(s2_res), 6),
                var_p_share=round(float(s2_p / tot), 4) if tot > 0 else None,
                G_of_k={str(k): round(float(Gk(k)), 4) for k in range(1, 11)},
                k_star_G0p8=kstar)


fold = (G == 1) | ((den != '') & (num < den))
nf = int(fold.sum())


def boot_ci(xs, B=1000, seed=20260917):
    rng = np.random.default_rng(seed)
    Xf = [np.asarray(x)[fold] for x in xs]
    shares = []; gk = {str(k): [] for k in range(1, 11)}
    for _ in range(B):
        ii = rng.integers(0, nf, nf)
        g = gstudy([x[ii] for x in Xf], rn_argsort)
        shares.append(g['var_p_share'])
        for k in gk: gk[k].append(g['G_of_k'][k])

    def pct(v): return [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]
    return dict(var_p_share_ci=pct(shares), G1_ci=pct(gk['1']), G2_ci=pct(gk['2']), G3_ci=pct(gk['3']),
                G_of_k_ci={k: pct(v) for k, v in gk.items()},
                B=B, seed=seed, n_folded=nf,
                note='折叠集(见 M5)候选级 bootstrap；候选相依(124 基元派生)，CI 只作描述性带宽')


gA = gstudy([A_z, A_m, A_45], rn_argsort); gA_t = gstudy([A_z, A_m, A_45], rn_ties)
gB = gstudy([B_z, B_m, B_45], rn_argsort); gB_t = gstudy([B_z, B_m, B_45], rn_ties)
res['M2_gtheory3'] = dict(
    design='p(%d) x e(3: zonal/merid/diag45), 环境内秩归一化, 相对G(舍去环境主效应)' % N,
    A=dict(**gA, var_p_share_ties=gA_t['var_p_share'], k_star_ties=gA_t['k_star_G0p8'], ci=boot_ci([A_z, A_m, A_45])),
    B=dict(**gB, var_p_share_ties=gB_t['var_p_share'], k_star_ties=gB_t['k_star_G0p8'], ci=boot_ci([B_z, B_m, B_45])),
    caveat='3 环境侧面 CI 极宽; σ²_pe 分不出交互与噪声; 结论限定本强迫场景族(风向×VISC2 单旋钮)')
log('M2: A share=%s k*=%s | B share=%s(ties %s) k*=%s (%.1fs)' %
    (gA['var_p_share'], gA['k_star_G0p8'], gB['var_p_share'], gB_t['var_p_share'], gB['k_star_G0p8'], time.time() - t0))

# ---------- M3 ICP 式不变性 ----------
CLIP = 0.999999


def bh_reject(p, q=0.05):
    m = len(p); o = np.argsort(p); thr = q * (np.arange(1, m + 1)) / m
    ok = p[o] <= thr
    k = np.max(np.where(ok)[0]) + 1 if ok.any() else 0
    rej = np.zeros(m, bool)
    if k: rej[o[:k]] = True
    return rej


# (i) 2 环境（纬/经）——试点原式逐字复算，用于锚定 Inv2=88
rho_z = np.clip(-A_z, -CLIP, CLIP); rho_m = np.clip(-A_m, -CLIP, CLIP); rho_45 = np.clip(-A_45, -CLIP, CLIP)
se2 = math.sqrt(1.06 / (n_z - 3) + 1.06 / (n_m - 3))
z2 = (np.arctanh(rho_z) - np.arctanh(rho_m)) / se2
p2 = np.array([math.erfc(abs(z) / math.sqrt(2)) for z in z2])
rej2 = bh_reject(p2, 0.05)
inv2 = (~rej2) & gate_z & gate_m          # 试点锚：88 把
res['anchors']['inv2_size_recomputed'] = int(inv2.sum())
res['inv2_anchor_pass'] = bool(int(inv2.sum()) == 88)
res['anchors_pass'] = bool(res['anchors_pass'] and res['inv2_anchor_pass'])
if not res['inv2_anchor_pass']:
    log('!!! Inv2 复算=%d != 88：P5b 分母漂移，anchors_pass 置 False（PIPELINE_SUSPECT）' % int(inv2.sum()))
# (ii) 3 环境加权 Q 检验（df=2, chi2 生存函数 = exp(-Q/2)）
zz = np.stack([np.arctanh(rho_z), np.arctanh(rho_m), np.arctanh(rho_45)], axis=1)
w = np.array([1.0 / (1.06 / (n - 3)) for n in (n_z, n_m, n_45)])
zbar = (zz * w).sum(1) / w.sum()
Q = ((zz - zbar[:, None]) ** 2 * w).sum(1)
p3 = np.exp(-Q / 2.0)
rej3 = bh_reject(p3, 0.05)
inv3 = (~rej3) & gate_z & gate_m & gate_45
is_temp_ratio = (G == 0) & np.char.startswith(num, 'temp|') & np.char.startswith(den, 'temp|')
inv3_n = int(inv3.sum())
res['M3_icp3'] = dict(
    method='3环境: 逐候选 Fisher-z 加权 Q 检验, var=1.06/(n-3), df=2, p=exp(-Q/2), BH-FDR q=0.05; ρ_env=-A_env',
    n_reject=int(rej3.sum()), frac_reject=round(float(rej3.mean()), 4),
    n_reject_in_S_A=int(rej3[S_A_mask].sum()),
    inv2_size=int(inv2.sum()),
    n_add_reject_in_inv2=int(rej3[inv2].sum()),
    invariant3_size=inv3_n,
    invariant3_temp_ratio_share=round(float(is_temp_ratio[inv3].mean()), 4) if inv3_n else None,
    invariant3_def='3环境 Q 未拒绝 且 三环境 A>=0.7 且 B>=0.9（未拒绝≠认证，功效有限）',
    invariant3_sample=[dict(num=str(num[i]), den=str(den[i]) or None,
                            A_z=round(float(A_z[i]), 3), A_m=round(float(A_m[i]), 3), A_45=round(float(A_45[i]), 3),
                            B_z=round(float(B_z[i]), 3), B_m=round(float(B_m[i]), 3), B_45=round(float(B_45[i]), 3))
                       for i in np.where(inv3)[0][:10]],
    caveat='候选高度相依, BH 计数只作描述; 真值标签 regraded_v2(纬)/hidden(经,45°) 同定义不同来源')
log('M3: 3环境判死 %d/%d (%.1f%%) | Inv2=%d 追加判死 %d | Inv3=%d temp比值占比=%s (%.1fs)' %
    (rej3.sum(), N, 100 * rej3.mean(), int(inv2.sum()), int(rej3[inv2].sum()), inv3_n,
     res['M3_icp3']['invariant3_temp_ratio_share'], time.time() - t0))

# ---------- M4 Millsap/D 机制账本（P2/P6 的量在此落盘） ----------
viol = {}
for t in (0.5, 0.7, 0.9):
    m_ = A_z >= t
    viol['A_z>=%.1f' % t] = dict(n=int(m_.sum()),
        frac_A45_lt_0=round(float((A_45[m_] < 0).mean()), 4) if m_.any() else None,
        frac_A45_lt_0p3=round(float((A_45[m_] < 0.3).mean()), 4) if m_.any() else None,
        frac_A45_ge_0p7=round(float((A_45[m_] >= 0.7).mean()), 4) if m_.any() else None)
mB = B_z >= 0.9
rho_A45_B45 = spearman(A_45, B_45); rho_AP45_B45 = spearman(AP_45, B_45)
res['M4_millsap3'] = dict(
    internal_45=dict(rho_A45_B45=round(rho_A45_B45, 4),
                     rho_D45_A45=round(spearman(D_45, A_45), 4),
                     rho_D45_B45=round(spearman(D_45, B_45), 4),
                     rho_AP45_B45=round(rho_AP45_B45, 4)),
    rho_D45_A45=round(spearman(D_45, A_45), 4),
    rho_D45_A45_ties=round(spearman_ties(D_45, A_45), 4),
    rho_Dz_D45=round(spearman(D_z, D_45), 4),
    rho_Dz_D45_ties=round(spearman_ties(D_z, D_45), 4),
    rho_Dm_D45=round(spearman(D_m, D_45), 4),
    conv_after_partial_D=dict(rho_APz_AP45=p45['rho_AP'], rho_APz_A45=round(spearman(AP_z, A_45), 4),
                              collapse=round(p45['rho_A'] - p45['rho_AP'], 4)),
    d_ledger_45=dict(share=round(1 - abs(rho_AP45_B45) / abs(rho_A45_B45), 3) if rho_A45_B45 else None,
                     note='ρ(A,B)中被D承载的份额=1-|ρ(A⊥,B)|/|ρ(A,B)|; 纬向锚约0.29, 经向约0.51'),
    violation_rates=viol,
    frac_A45_lt0_given_Az_ge_0p7=viol['A_z>=0.7']['frac_A45_lt_0'],
    B_transfer=dict(n_Bz_ge_0p9=int(mB.sum()),
                    frac_B45_ge_0p9=round(float((B_45[mB] >= 0.9).mean()), 4) if mB.any() else None,
                    frac_B45_lt_0p5=round(float((B_45[mB] < 0.5).mean()), 4) if mB.any() else None))
log('M4: ρ(D45,A45)=%+.4f ρ(Dz,D45)=%+.4f 塌方=%.4f P6率=%s (%.1fs)' %
    (res['M4_millsap3']['rho_D45_A45'], res['M4_millsap3']['rho_Dz_D45'],
     res['M4_millsap3']['conv_after_partial_D']['collapse'],
     res['M4_millsap3']['frac_A45_lt0_given_Az_ge_0p7'], time.time() - t0))

# ---------- M5 折叠候选集 ----------
cols_f = [c[fold] for c in cols]
M6f = mtmm(cols_f, spearman)
prof = np.round(np.stack(cols, 1), 3)
n_prof = int(np.unique(prof, axis=0).shape[0])
prof4 = np.round(np.stack([A_z, B_z, A_m, B_m], 1), 3)
n_prof4 = int(np.unique(prof4, axis=0).shape[0])
res['M5_folded3'] = dict(n_folded=nf,
                         convergent=dict(A_z_m=round(float(M6f[0, 2]), 4), A_z_45=round(float(M6f[0, 4]), 4),
                                         B_z_m=round(float(M6f[1, 3]), 4), B_z_45=round(float(M6f[1, 5]), 4)),
                         anchor_AzBz=round(float(M6f[0, 1]), 4),
                         n_distinct_profiles_3dp=n_prof,
                         n_distinct_profiles_3dp_4col_pilot=n_prof4,
                         note='比值(a,b)~(b,a)互为倒数, 折叠留字典序一半; 名义N/折叠N/独立剖面须同页申明; '
                              '剖面两口径: 6列=A,B×3环境(正式口径), 4col_pilot=A,B×纬/经(试点8513对表, 交集非全集时可偏)')

# ---------- M6 决策级 ----------
def kappa_jaccard(g1, g2):
    n11 = int((g1 & g2).sum()); n10 = int((g1 & ~g2).sum()); n01 = int((~g1 & g2).sum()); n00 = int((~g1 & ~g2).sum())
    po = (n11 + n00) / N; q1 = g1.mean(); q2 = g2.mean()
    pe = q1 * q2 + (1 - q1) * (1 - q2)
    kap = (po - pe) / (1 - pe) if pe < 1 else None
    jac = n11 / (n11 + n10 + n01) if (n11 + n10 + n01) else None
    return dict(n_both=n11, n_only_1=n10, n_only_2=n01,
                kappa=round(float(kap), 4) if kap is not None else None,
                jaccard=round(float(jac), 4) if jac is not None else None)


res['M6_decision3'] = dict(
    gate='A>=0.7 & B>=0.9 (E65/E67B 同门, 不另设阈值)',
    gate_sizes=dict(zonal=int(gate_z.sum()), merid=int(gate_m.sum()), diag45=int(gate_45.sum())),
    z_m=kappa_jaccard(gate_z, gate_m),
    z_45=kappa_jaccard(gate_z, gate_45),
    m_45=kappa_jaccard(gate_m, gate_45),
    n_triple=int((gate_z & gate_m & gate_45).sum()),
    conv_A_within_S_A_z45=round(spearman(A_z[S_A_mask], A_45[S_A_mask]), 4),
    conv_A_within_S_A_z45_ties=round(spearman_ties(A_z[S_A_mask], A_45[S_A_mask]), 4),
    note_derived='κ/Jaccard(z,45) 可由封存前已知数(204/454/140/N)派生, 只作一致性检查, 不是预测(PREREG §3)')
res['M6_decision3']['kappa'] = {k: res['M6_decision3'][k]['kappa'] for k in ('z_m', 'z_45', 'm_45')}
res['M6_decision3']['jaccard'] = {k: res['M6_decision3'][k]['jaccard'] for k in ('z_m', 'z_45', 'm_45')}

# ---------- 三层塌方表（z–45 主表；z–m 试点对照同框） ----------
res['three_layer'] = dict(
    z_45=dict(correlation=p45['rho_A'], mechanism=p45['rho_AP'],
              decision_kappa=res['M6_decision3']['kappa']['z_45'],
              decision_jaccard=res['M6_decision3']['jaccard']['z_45'],
              restricted_conv=res['M6_decision3']['conv_A_within_S_A_z45']),
    z_m_pilot_frame=dict(correlation=res['pairs']['z_m']['rho_A'], mechanism=res['pairs']['z_m']['rho_AP'],
                         decision_kappa=res['M6_decision3']['kappa']['z_m'],
                         decision_jaccard=res['M6_decision3']['jaccard']['z_m']))

res['elapsed_s'] = round(time.time() - t0, 1)
json.dump(res, open(f'{FIN}/E71_FINAL_RESULTS.json', 'w'), indent=1, ensure_ascii=False)
log('E71F_METROLOGY_DONE  %.1f 秒 → E71_FINAL_RESULTS.json' % (time.time() - t0))
