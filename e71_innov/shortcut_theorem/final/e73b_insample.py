#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E73 shortcut_theorem · 步骤 B：样本内校准与命题审计（纬向＋经向，零留出读取）。

角色：为 PREREG_shortcut_theorem.md 提供样本内校准数字（c_z/c_m、双口径、偏相关三联、
恒等式分布、逃逸者审计、经向全流程彩排）。本脚本【不读】45°/e60/e56/e44 任何数据，
【不算】尾部附验（κ/g——那两条方向性附验由 e73t_tail.py 在封存后首算，保持"未算先押"）。

输入（全部只读）：
  ledger/env2_runs.jsonl + runs/ + ledger/regraded_v2.jsonl        （纬向）
  ledger/env2_merid_runs.jsonl + runs_merid/                        （经向, hidden 标签）
  e71_innov/multienv_metrology/E71_PILOT_AXES.npz                   （两环境逐候选轴, 只读）
输出（只写本目录）：E73_INSAMPLE.json
运行：systemd-run --user --scope -p MemoryMax=16G nice -n 19 env OMP_NUM_THREADS=8 <python> e73b_insample.py
"""
import json, sys, time
import numpy as np
from scipy.stats import mannwhitneyu, rankdata, spearmanr

ENV = '/data/xinyuan/GOAI_ai4s_env'
MOD = f'{ENV}/e71_innov/shortcut_theorem'
FIN = f'{MOD}/final'
sys.path.insert(0, f'{ENV}/scripts'); sys.path.insert(0, f'{ENV}/e44')
from metric_search import base_quantities  # noqa: E402

t0 = time.time()
def log(*a): print(*a, flush=True)

def sp_argsort(a, b):
    """判定主口径：scripts/metric_search.py L101-105 的 argsort 秩（并列按出现序破，不平均）。"""
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    if np.std(ra) == 0 or np.std(rb) == 0: return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])

def sp_avgrank(a, b):
    """敏感性口径：并列平均秩。"""
    return float(spearmanr(a, b).correlation)

def partial_sp(a, b, c):
    """全偏 Spearman（平均秩；a、b 各对 c 的秩作线性残差后取 Pearson）。"""
    ra, rb, rc = rankdata(a), rankdata(b), rankdata(c)
    ra = (ra - ra.mean()) / ra.std(); rb = (rb - rb.mean()) / rb.std(); rc = (rc - rc.mean()) / rc.std()
    return float(np.corrcoef(ra - (ra @ rc) / (rc @ rc) * rc, rb - (rb @ rc) / (rc @ rc) * rc)[0, 1])

# ---------- 运行级 (伪流幅度, 技巧) 序列 → 耦合系数 c_e ----------
def runlevel(ledger, runsdir, reg_from):
    reg = {}
    if reg_from == 'regraded':
        for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
            r = json.loads(l); reg[r['run_id']] = r['skill_vs_zero']
    rows = {}  # run_id 去重（台账同一 run 可多行；与 e71a 的 seen dict 同语义）
    for l in open(ledger):
        r = json.loads(l)
        if not (r['obs'].get('valid') and r['ntimes'] == 8640): continue
        if r['bathy'] != 'r26steep': continue
        if reg_from == 'hidden':
            s = (r.get('hidden') or {}).get('skill_vs_zero')
            if s is None: continue
            reg[r['run_id']] = s
        if r['run_id'] in reg: rows[r['run_id']] = None
    rows = list(rows)
    spur, skill = [], []
    for rid in rows:
        q = base_quantities(f'{runsdir}/{rid}')
        if q and 'u|all|rms' in q:
            spur.append(q['u|all|rms']); skill.append(reg[rid])
    spur, skill = np.array(spur), np.array(skill)
    # c_e ≡ −ρs(spur, skill)：与 A=−ρs(候选,skill)、D=ρs(候选,spur) 的符号链一致，
    # 使 Â_e(m)=c_e·D_z(m) 在 c_e>0 时预测 D 正耦合者 A 为正。
    return dict(n=int(len(spur)),
                c_argsort=-sp_argsort(spur, skill),
                c_avgrank=-sp_avgrank(spur, skill)), spur, skill

log('运行级 纬向…')
cz, spur_z, skill_z = runlevel(f'{ENV}/ledger/env2_runs.jsonl', f'{ENV}/runs', 'regraded')
log('  n=%d  c_z(argsort)=%.4f  c_z(avgrank)=%.4f  (%.0fs)' % (cz['n'], cz['c_argsort'], cz['c_avgrank'], time.time() - t0))
log('运行级 经向…')
cm, spur_m, skill_m = runlevel(f'{ENV}/ledger/env2_merid_runs.jsonl', f'{ENV}/runs_merid', 'hidden')
log('  n=%d  c_m(argsort)=%.4f  c_m(avgrank)=%.4f  (%.0fs)' % (cm['n'], cm['c_argsort'], cm['c_avgrank'], time.time() - t0))

# ---------- 逐候选轴（试点已落盘，只读；负控试点已锚 E65 逐候选最大差 0.0） ----------
z = np.load(f'{ENV}/e71_innov/multienv_metrology/E71_PILOT_AXES.npz', allow_pickle=True)
A, B, D, AP, G = z['A_z'], z['B_z'], z['D_z'], z['AP_z'], z['G']
Am, Bm, Dm, APm = z['A_m'], z['B_m'], z['D_m'], z['AP_m']
num = z['num'].astype(str); den = z['den'].astype(str)
N = int(A.size)

out = dict(script='e73b_insample.py', date='2026-09-17', n_candidates=N,
           heldout_untouched=['runs_diag45', 'e60', 'e56', 'e44'],
           c_zonal=cz, c_merid=cm)

# ---------- 锚（验证性断言，容差 ±0.01） ----------
out['anchors'] = dict(
    rho_AB_argsort=round(sp_argsort(A, B), 4),      # 期望 −0.6742
    rho_AB_avgrank=round(sp_avgrank(A, B), 4),      # 期望 −0.7322
    rho_DA_argsort=round(sp_argsort(D, A), 4),      # 期望 +0.9762（E65 P1 反赌的实测）
    rho_DB_argsort=round(sp_argsort(D, B), 4),      # 期望 −0.661
    n_S_A=int(((A >= 0.7) & (B >= 0.9)).sum()),     # 期望 204
)

# ---------- 偏相关三联（中介一致性检查，非因果断言） ----------
out['partial_trio'] = dict(
    raw_avgrank=round(sp_avgrank(A, B), 4),                 # −0.7322
    partial_given_D=round(partial_sp(A, B, D), 4),          # −0.198（掉七成）
    partial_given_absD=round(partial_sp(A, B, np.abs(D)), 4),  # −0.7321（|D| 控不动 → 单靠幅度带不走）
    rho_APz_B_argsort=round(sp_argsort(AP, B), 4),          # −0.4778（单侧残差版，E66 锚）
    merid_raw_argsort=round(sp_argsort(Am, Bm), 4),
    merid_partial_given_D=round(partial_sp(Am, Bm, Dm), 4),
    note='三联同框：控 signed-D 掉七成、控 |D| 纹丝不动——一致性检查而非中介证明（观察性+共线）。')

# ---------- 恒等式检查 |A − c_z·D| 全体分布（M1∘M3 近似恒等式的样本内偏离） ----------
for tag, cval in (('argsort', cz['c_argsort']), ('avgrank', cz['c_avgrank'])):
    delta = A - cval * D
    out[f'identity_delta_{tag}'] = dict(
        c=round(cval, 4),
        q=[round(float(np.percentile(np.abs(delta), p)), 4) for p in (50, 90, 95, 99, 100)],
        frac_within_0p1=round(float((np.abs(delta) <= 0.1).mean()), 4))

# ---------- 逃逸者审计（近乌托邦 A≥0.9 ∧ B≥0.9） ----------
esc = (A >= 0.9) & (B >= 0.9)
out['escapees'] = dict(
    n=int(esc.sum()), all_ratio_type=bool((G[esc] == 0).all()),
    D_mean=round(float(D[esc].mean()), 4),
    names=[[num[i], den[i]] for i in np.where(esc)[0]],
    A_m=[round(float(x), 3) for x in Am[esc]], B_m=[round(float(x), 3) for x in Bm[esc]],
    merid_strict_survive=int(((Am[esc] >= 0.9) & (Bm[esc] >= 0.9)).sum()),
    merid_standard_survive=int(((Am[esc] >= 0.7) & (Bm[esc] >= 0.9)).sum()))

# ---------- 经向彩排：P1–P4 同式同码预演（样本内校准，不是预测） ----------
c_use = cm['c_argsort']
Ahat_m = c_use * D
reh = dict(c_used=round(c_use, 4))
reh['P1_rankcorr_argsort'] = round(sp_argsort(Ahat_m, Am), 4)
reh['P1_rankcorr_avgrank'] = round(sp_avgrank(Ahat_m, Am), 4)
conf = np.abs(D) >= 0.3
reh['P2_sign_hit_confident'] = dict(
    n=int(conf.sum()),
    hit=round(float((np.sign(Am[conf]) == np.sign(Ahat_m[conf])).mean()), 4))
reh['P2_sign_hit_all'] = round(float((np.sign(Am) == np.sign(Ahat_m)).mean()), 4)
S_A = (A >= 0.7) & (B >= 0.9)
surv_m = S_A & (Am >= 0.7) & (Bm >= 0.9)
r_m = np.abs(Am - Ahat_m)
u1, p1 = mannwhitneyu(r_m[surv_m], r_m[S_A & ~surv_m], alternative='less')
u2, p2 = mannwhitneyu(r_m[surv_m], r_m[~surv_m], alternative='less')
reh['P3_residual_MW'] = dict(
    n_surv=int(surv_m.sum()),
    within_S_A_p=float(p1), vs_all_rest_p=float(p2),
    med_surv=round(float(np.median(r_m[surv_m])), 4),
    med_S_A_dead=round(float(np.median(r_m[S_A & ~surv_m])), 4),
    med_rest=round(float(np.median(r_m[~surv_m])), 4))
rng = np.random.default_rng(20260917)
full = abs(reh['P1_rankcorr_argsort'])
subs, signs = [], []
for _ in range(200):
    ii = rng.choice(cm['n'], size=5, replace=False)
    ck = -sp_argsort(spur_m[ii], skill_m[ii])
    signs.append(np.sign(ck) == np.sign(c_use))
    subs.append(abs(sp_argsort(ck * D, Am)) if ck != 0 else 0.0)
reh['P4_k5'] = dict(median_ratio=round(float(np.median(subs) / full), 4) if full else None,
                    sign_stable_frac=round(float(np.mean(signs)), 4))
out['merid_rehearsal'] = reh

json.dump(out, open(f'{FIN}/E73_INSAMPLE.json', 'w'), indent=1, ensure_ascii=False)
log(json.dumps(out['merid_rehearsal'], ensure_ascii=False, indent=1))
log('E73B_DONE  %.0f 秒' % (time.time() - t0))
