#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E73 shortcut_theorem · 步骤 D：45° 预测统计量落盘（PREREG §5 P1–P6 的全部原料＋§7 描述件）。

首读留出：45° 轴文件（优先 E71M 的 E71_FINAL_AXES.npz，只读；否则本目录 E73_AXES45.npz）
＋ 45° 运行级 (u|all|rms, hidden.skill_vs_zero)（c_45 的输入）。
输出：E73_SHORTCUT_MAP.json（只写本目录）。本脚本只落统计量，不判分——判分归 e73e_verdict.py。
退化护栏（PREREG §1 小样本预案）：n_45=0 ⇒ c_45 不可算，P1–P4 统计量记 null；n_45<5 ⇒ P4 记 null；
统计量为 NaN 一律记 null（e73e 按 null→不中处理）。map 在任何 n_45 下都落盘。
运行：systemd-run --user --scope -p MemoryMax=16G nice -n 19 env OMP_NUM_THREADS=8 <python> e73d_predict45.py
"""
import hashlib, json, math, os, sys, time
import numpy as np
from scipy.stats import mannwhitneyu, rankdata, spearmanr

ENV = '/data/xinyuan/GOAI_ai4s_env'
FIN = f'{ENV}/e71_innov/shortcut_theorem/final'
MULTI = f'{ENV}/e71_innov/multienv_metrology/final/E71_FINAL_AXES.npz'
OWN = f'{FIN}/E73_AXES45.npz'
PRE = f'{FIN}/PREREG_shortcut_theorem.md'
SHA = f'{FIN}/PREREG_shortcut_theorem.sha256'

# PREREG §3.6 钉死的 12 把逃逸者（纬向 A≥0.9 ∧ B≥0.9）
ESCAPEES = [('u|all|rms', 'v|all|mean_abs'), ('u|d1500|p95', 'u|d1500|max'),
            ('u|d1500|p95', 'v|d1500|max'), ('u|d1500|p95', 'v|d1500|rms'),
            ('u|d1500|p95', 'w|d1500|rms'), ('u|s200|rms', 'v|s200|rms'),
            ('u|s50|mean_abs', 'v|s50|p95'), ('u|s50|rms', 'v|s50|mean_abs'),
            ('u|s50|rms', 'v|s50|p95'), ('u|s50|rms', 'v|s50|rms'),
            ('v|d1500|p95', 'v|d1500|max'), ('w|d200|mean_abs', 'w|d400|mean_abs')]


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


def fin(x, nd=4):
    """NaN/inf/None → None；否则 round。"""
    if x is None: return None
    x = float(x)
    return round(x, nd) if math.isfinite(x) else None


def sp_argsort(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    if np.std(ra) == 0 or np.std(rb) == 0: return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def sp_avgrank(a, b):
    try:
        return float(spearmanr(a, b).correlation)
    except Exception:
        return float('nan')


def partial_sp(a, b, c):
    ra, rb, rc = rankdata(a), rankdata(b), rankdata(c)
    if ra.std() == 0 or rb.std() == 0 or rc.std() == 0: return float('nan')
    ra = (ra - ra.mean()) / ra.std(); rb = (rb - rb.mean()) / rb.std(); rc = (rc - rc.mean()) / rc.std()
    return float(np.corrcoef(ra - (ra @ rc) / (rc @ rc) * rc, rb - (rb @ rc) / (rc @ rc) * rc)[0, 1])


def mw_less(x, y):
    if x.size == 0 or y.size == 0: return None
    try:
        p = float(mannwhitneyu(x, y, alternative='less')[1])
    except Exception:
        return None
    return p if math.isfinite(p) else None


def auc_rank(score, y):
    """秩式 AUC（Mann-Whitney U / n1·n0）。"""
    y = y.astype(bool)
    if y.sum() == 0 or (~y).sum() == 0: return None
    r = rankdata(score)
    return float((r[y].sum() - y.sum() * (y.sum() + 1) / 2) / (y.sum() * (~y).sum()))


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''): h.update(blk)
    return h.hexdigest()


# ---- 轴装载（协作条款：优先 E71M 只读） ----
if os.path.exists(MULTI):
    AX = MULTI; axes_source = 'multienv_metrology/final/E71_FINAL_AXES.npz'
elif os.path.exists(OWN):
    AX = OWN; axes_source = 'shortcut_theorem/final/E73_AXES45.npz'
else:
    sys.exit('45° 轴未落盘：先跑 e73c_axes45.py（或等 E71M 落盘）。')
axes_sha = sha_file(AX)
z = np.load(AX, allow_pickle=True)
A, B, D, G = z['A_z'], z['B_z'], z['D_z'], z['G']
Am, Bm = z['A_m'], z['B_m']
A45, B45, D45 = z['A_45'], z['B_45'], z['D_45']
num = z['num'].astype(str); den = z['den'].astype(str)
N = int(A.size)
if N == 0:
    sys.exit('轴文件对齐候选数为 0：管线错误，按 PREREG §9 记 DEVIATIONS 后查管线。')
META = AX[:-4] + '_META.json'
n_pairs_45 = None; n_common_meta = None
if os.path.exists(META):
    mj = json.load(open(META))
    n_pairs_45 = (mj.get('diag45') or {}).get('n_pairs')
    n_common_meta = mj.get('n_common')
log('轴来源=%s  N=%d  n_pairs_45=%s' % (axes_source, N, n_pairs_45))

# ---- c_45：45° 运行级（去重；与 e73b runlevel 同式） ----
reg, rows = {}, {}
for l in open(f'{ENV}/ledger/env2_diag45_runs.jsonl'):
    r = json.loads(l)
    if not (r['obs'].get('valid') and r['ntimes'] == 8640): continue
    if r['bathy'] != 'r26steep': continue
    s = (r.get('hidden') or {}).get('skill_vs_zero')
    if s is None: continue
    reg[r['run_id']] = s; rows[r['run_id']] = None
spur, skill = [], []
for rid in rows:
    q = base_quantities(f'{ENV}/runs_diag45/{rid}')
    if q and 'u|all|rms' in q:
        spur.append(q['u|all|rms']); skill.append(reg[rid])
spur, skill = np.array(spur, dtype=float), np.array(skill, dtype=float)
n_45 = int(len(spur))
if n_45 >= 1:
    c45 = -sp_argsort(spur, skill)
    c45_avg = -sp_avgrank(spur, skill) if n_45 >= 2 else float('nan')
else:
    c45, c45_avg = None, float('nan')  # n_45=0：c_45 不可算
log('n_45=%d  c_45(argsort)=%s  c_45(avgrank)=%s' % (n_45, c45, c45_avg))


def pred_rank(c, fn=sp_argsort):
    """ρ(c·D_z, A_45)。c=0 时 Â 为常数，argsort 会按下标破并列产生伪相关——按 0 计（PREREG §5 P4 同款）。"""
    if c is None: return None
    if c == 0: return 0.0
    return fn(c * D, A45)


out = dict(script='e73d_predict45.py', script_sha=SCRIPT_SHA, prereg_sha=SEAL,
           metric_search_file=os.path.realpath(metric_search.__file__),
           axes_source=axes_source, axes_sha256=axes_sha,
           n_candidates=N, n_common_meta=n_common_meta, n_pairs_45=n_pairs_45,
           n_45=n_45, low_n=bool(n_45 < 15), k5_degenerate=bool(n_45 < 10),
           c45_available=c45 is not None,
           c_45=dict(argsort=fin(c45), avgrank=fin(c45_avg)))

# ---- 验证性锚（PREREG §4；在 45° 对齐子集上复算，n_common 同落） ----
S_A = (A >= 0.7) & (B >= 0.9)
esc_idx = []
name2i = {(num[i], den[i]): i for i in range(N)}
for kn, kd in ESCAPEES:
    i = name2i.get((kn, kd))
    if i is not None: esc_idx.append(i)
esc_idx = np.array(esc_idx, dtype=int)
gate45 = (A45 >= 0.7) & (B45 >= 0.9)
out['anchors'] = dict(
    n_common=N,
    rho_AB_argsort=fin(sp_argsort(A, B)), rho_DA_argsort=fin(sp_argsort(D, A)),
    rho_DB_argsort=fin(sp_argsort(D, B)), n_S_A=int(S_A.sum()),
    n_escapees_found=int(esc_idx.size),
    escapees_all_G0=bool((G[esc_idx] == 0).all()) if esc_idx.size else None,
    n_pairs_45=n_pairs_45,
    n_gate45=int(gate45.sum()))

# ---- P1 逐候选值 ----
Ahat = (c45 * D) if c45 is not None else None
out['P1'] = dict(rankcorr_argsort=fin(pred_rank(c45)),
                 rankcorr_avgrank=fin(pred_rank(c45, sp_avgrank)),
                 note='秩相关对正标量缩放不变：等价于 sign(c_45)·ρs(D_z,A_45)')

# ---- P2 反号象限（置信带 |D_z|≥0.3 的符号场命中率；A_45=0 记 miss） ----
conf = np.abs(D) >= 0.3
if Ahat is not None and conf.sum():
    hit = (np.sign(A45[conf]) == np.sign(Ahat[conf])) & (A45[conf] != 0)
    hit_all = (np.sign(A45) == np.sign(Ahat)) & (A45 != 0)
    out['P2'] = dict(n_conf=int(conf.sum()), hit_rate=fin(hit.mean()), hit_rate_all=fin(hit_all.mean()),
                     n_A45_zero_in_conf=int((A45[conf] == 0).sum()))
else:
    out['P2'] = dict(n_conf=int(conf.sum()), hit_rate=None, hit_rate_all=None)

# ---- P3 残差榜（a：S_A 内 45° 存活 vs 阵亡；b：三向幸存者 vs 全体其余） ----
surv45 = S_A & gate45
merid_gate = (Am >= 0.7) & (Bm >= 0.9)
triple = S_A & merid_gate & gate45
dead_SA = S_A & ~gate45
P3 = dict(n_surv45_in_S_A=int(surv45.sum()), n_dead_in_S_A=int(dead_SA.sum()), n_triple=int(triple.sum()))
if Ahat is not None:
    r_res = A45 - Ahat
    absr = np.abs(r_res)
    med = lambda m: fin(np.median(absr[m])) if m.sum() else None  # noqa: E731
    P3.update(p3a_mw_one_sided=mw_less(absr[surv45], absr[dead_SA]),
              p3b_mw_one_sided=mw_less(absr[triple], absr[~triple]),
              med_absr_surv45=med(surv45), med_absr_S_A_dead=med(dead_SA),
              med_absr_triple=med(triple), med_absr_rest=med(~triple),
              med_absr_all=fin(np.median(absr)),
              q_absr_all_p50_p95=[fin(np.percentile(absr, 50)), fin(np.percentile(absr, 95))],
              frac_absr_within_0p1=fin((absr <= 0.1).mean()))
else:
    r_res = absr = None
    P3.update(p3a_mw_one_sided=None, p3b_mw_one_sided=None)
out['P3'] = P3

# ---- P4 k=5 子抽样（带符号：mean_200 ρs(ĉ·D_z, A_45) / P1；ĉ=0 按 0 计） ----
full = out['P1']['rankcorr_argsort']
if c45 is not None and n_45 >= 5:
    rng = np.random.default_rng(20260917)
    subs, signs, cs = [], [], []
    for _ in range(200):
        ii = rng.choice(n_45, size=5, replace=False)
        ck = -sp_argsort(spur[ii], skill[ii])
        cs.append(ck); signs.append(bool(np.sign(ck) == np.sign(c45) and ck != 0))
        subs.append(pred_rank(ck))
    subs = np.array(subs)
    out['P4'] = dict(mean_signed_rankcorr=fin(subs.mean()), median_signed_rankcorr=fin(np.median(subs)),
                     full_rankcorr=full,
                     mean_ratio=fin(subs.mean() / full) if (full is not None and full > 0) else None,
                     median_ratio_signed=fin(np.median(subs) / full) if (full is not None and full > 0) else None,
                     median_ratio_abs_draftversion=fin(np.median(np.abs(subs)) / abs(full)) if full else None,
                     sign_stable_frac=fin(np.mean(signs)), n_ck_zero=int(sum(1 for c in cs if c == 0)),
                     c_k5_mean=fin(np.mean(cs)),
                     c_k5_cv=fin(np.std(cs) / (abs(np.mean(cs)) + 1e-12)), seed=20260917)
else:
    out['P4'] = dict(mean_ratio=None, full_rankcorr=full, seed=20260917,
                     skipped='n_45<5 或 c_45 不可算：无法抽 k=5（PREREG §1），统计量记 null')

# ---- P5 中介一致性复现（平均秩口径判定；argsort 同报） ----
raw_avg = sp_avgrank(A45, B45)
par = partial_sp(A45, B45, D45)
ratio = abs(par) / abs(raw_avg) if (math.isfinite(par) and math.isfinite(raw_avg) and abs(raw_avg) > 1e-12) else None
out['P5'] = dict(raw_avgrank=fin(raw_avg), raw_argsort=fin(sp_argsort(A45, B45)),
                 partial_given_D45_avgrank=fin(par),
                 partial_given_absD45_avgrank=fin(partial_sp(A45, B45, np.abs(D45))),
                 ratio=fin(ratio))

# ---- P6 逃逸者跨向不保（严格门 0.9/0.9） ----
strict45 = (A45[esc_idx] >= 0.9) & (B45[esc_idx] >= 0.9)
out['P6'] = dict(n_escapees=int(esc_idx.size), strict_survive=int(strict45.sum()),
                 standard_survive=int(((A45[esc_idx] >= 0.7) & (B45[esc_idx] >= 0.9)).sum()),
                 names=[[num[i], den[i]] for i in esc_idx],
                 A_45=[round(float(x), 3) for x in A45[esc_idx]],
                 B_45=[round(float(x), 3) for x in B45[esc_idx]],
                 D_45=[round(float(x), 3) for x in D45[esc_idx]])

# ---- 描述件（§7.6/7.7：E59 同框 AUC、反号象限计数、残差榜头部） ----
strong45 = np.abs(A45) >= 0.7
desc = dict(
    e59_frame='E59B_POSTHOC.json auc_test=0.87/0.81/0.92（目标定义不同，仅同框，见 PREREG §3.9）',
    quadrants_at_0p7=dict(
        pp=int(((A >= 0.7) & (A45 >= 0.7)).sum()), pn=int(((A >= 0.7) & (A45 < 0)).sum()),
        turncoat_rate=fin((A45[A >= 0.7] < 0).mean()) if (A >= 0.7).sum() else None),
    rho_D45_A45_argsort=fin(sp_argsort(D45, A45)), rho_Dz_D45_argsort=fin(sp_argsort(D, D45)))
if Ahat is not None:
    desc.update(
        auc_gate45_from_Ahat=auc_rank(Ahat, gate45),
        auc_sign_in_strong45=auc_rank(Ahat[strong45], (A45[strong45] > 0)),
        top20_residual=[dict(num=num[i], den=den[i], G=int(G[i]), A_z=round(float(A[i]), 3),
                             D_z=round(float(D[i]), 3), A_45=round(float(A45[i]), 3),
                             B_45=round(float(B45[i]), 3), r=round(float(r_res[i]), 3))
                        for i in np.argsort(-absr)[:20]])
out['descriptive'] = desc
out['elapsed_s'] = round(time.time() - t0, 1)
json.dump(out, open(f'{FIN}/E73_SHORTCUT_MAP.json', 'w'), indent=1, ensure_ascii=False)
log(json.dumps({k: out[k] for k in ('c_45', 'anchors', 'P1', 'P2', 'P3', 'P4', 'P5')}, ensure_ascii=False, indent=1))
log('E73D_DONE  %.0f 秒' % (time.time() - t0))
