#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E73 shortcut_theorem · 封存后探索性审计（**非预注册，不改任何判定**；结果只作 DEVIATIONS/RESULT 的描述与脚注）。

(a) 尾部附验 NaN 审计：按 e73t_tail.py 逐字同一枚举复算 κ，统计 NaN 个数/类型；NaN 剔除后的 H1/H2 仅作探索性敏感性。
(b) 与预先存在的 ledger/metric_search_diag45.json top-30（2026-09-02）重叠核对（PREREG §3.7 承诺的封存后注明）。
(c) P3b 被推翻的描述性分解（|r| 中位数分组），不另做检验。
(d) P6 存活者点名。
输入只读：E73_SHORTCUT_MAP.json、E71_FINAL_AXES.npz、纬向 ledger/runs、metric_search_diag45.json。输出：E73X_POSTHOC.json。
"""
import hashlib, json, math, os, sys, time
import numpy as np
from scipy.stats import kurtosis, mannwhitneyu

ENV = "/data/xinyuan/GOAI_ai4s_env"
FIN = f"{ENV}/e71_innov/shortcut_theorem/final"
AX = f"{ENV}/e71_innov/multienv_metrology/final/E71_FINAL_AXES.npz"
sys.path.insert(0, f"{ENV}/scripts")
import metric_search  # noqa: E402
assert os.path.realpath(metric_search.__file__).endswith("GOAI_ai4s_env/scripts/metric_search.py")
from metric_search import base_quantities  # noqa: E402
t0 = time.time()
SCRIPT_SHA = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
out = dict(script="e73x_posthoc_audit.py", script_sha=SCRIPT_SHA, status="封存后探索性，非预注册，不改判",
           prereg_sha=open(f"{FIN}/PREREG_shortcut_theorem.sha256").readline().split()[0])

def sp_argsort(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    if np.std(ra) == 0 or np.std(rb) == 0: return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])

# ---- (a) 尾部 NaN 审计（枚举与 e73t 逐字同口径） ----
reg = {}
for l in open(f"{ENV}/ledger/regraded_v2.jsonl"):
    r = json.loads(l); reg[r["run_id"]] = r["skill_vs_zero"]
seen = {}; byp = {}
for l in open(f"{ENV}/ledger/env2_runs.jsonl"):
    r = json.loads(l)
    if not (r["obs"].get("valid") and r["ntimes"] == 8640): continue
    seen[r["run_id"]] = r["bathy"]
    a = r["action"]; k = tuple(round(a.get(x, -1), 6) for x in ("VISC2", "VISC4", "AKV_BAK", "TNU2"))
    byp.setdefault(k, {})[r["bathy"]] = r["run_id"]
r26 = [k for k, v in seen.items() if v == "r26steep" and k in reg]
flat = [k for k, v in seen.items() if v == "flat"]
PAIRS = [(v["r26steep"], v["flat"]) for v in byp.values() if "r26steep" in v and "flat" in v]
Q26 = [q for q in (base_quantities(f"{ENV}/runs/{rid}") for rid in r26) if q]
QFL = [q for q in (base_quantities(f"{ENV}/runs/{rid}") for rid in flat) if q]
keys = sorted(set.intersection(*[set(q) for q in Q26 + QFL]))
M26 = np.array([[q[k] for k in keys] for q in Q26]); MFL = np.array([[q[k] for k in keys] for q in QFL])
QP = [(qa, qb) for qa, qb in ((base_quantities(f"{ENV}/runs/{a}"), base_quantities(f"{ENV}/runs/{b}")) for a, b in PAIRS)
      if qa and qb and all(k in qa and k in qb for k in keys)]
P26 = np.array([[qa[k] for k in keys] for qa, qb in QP]); PFL = np.array([[qb[k] for k in keys] for qa, qb in QP])
EPS = 1e-12
K, GG, BB, names, GT, CONST = [], [], [], [], [], []
for i, kn in enumerate(keys):
    cand = [(kn, None, M26[:, i], MFL[:, i], P26[:, i], PFL[:, i])]
    for j, kd in enumerate(keys):
        if i == j: continue
        if np.any(np.abs(M26[:, j]) < EPS) or np.any(np.abs(MFL[:, j]) < EPS) or np.any(np.abs(P26[:, j]) < EPS) or np.any(np.abs(PFL[:, j]) < EPS):
            continue
        cand.append((kn, kd, M26[:, i] / M26[:, j], MFL[:, i] / MFL[:, j], P26[:, i] / P26[:, j], PFL[:, i] / PFL[:, j]))
    for kn_, kd_, v26, vfl, p26, pfl in cand:
        if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
        if np.any(v26 <= 0) or np.any(vfl <= 0): continue
        ok = (p26 > 0) & (pfl > 0) & np.isfinite(p26) & np.isfinite(pfl)
        if ok.sum() < 16: continue
        K.append(kurtosis(v26, fisher=True, bias=True)); GG.append(float(np.median(np.log(pfl[ok] / p26[ok]))))
        BB.append(float((pfl >= p26).mean())); names.append((kn_, kd_ or "")); GT.append(0 if kd_ else 1)
        CONST.append(bool(np.ptp(v26) == 0))
K, GG, BB, GT, CONST = np.array(K), np.array(GG), np.array(BB), np.array(GT), np.array(CONST)
nan = ~np.isfinite(K)
ex = [list(names[i]) for i in np.where(nan)[0][:10]]
fin = ~nan
absg = np.abs(GG)
rho_fin = sp_argsort(K[fin], absg[fin])
rk = np.argsort(np.argsort(K[fin])).astype(float); rg = np.argsort(np.argsort(absg[fin])).astype(float)
rk = (rk - rk.mean()) / rk.std(); rg = (rg - rg.mean()) / rg.std()
rng = np.random.default_rng(20260917); cnt = 0
for _ in range(5000):
    if float(np.mean(rng.permutation(rk) * rg)) >= rho_fin: cnt += 1
dead, alive = K[fin & (BB < 0.9)], K[fin & (BB >= 0.9)]
p_h2 = float(mannwhitneyu(dead, alive, alternative="greater")[1])
out["a_tail_nan_audit"] = dict(
    n_total=int(K.size), n_nan_kappa=int(nan.sum()), n_nan_constant_series=int((nan & CONST).sum()),
    n_nan_absolute_G1=int((nan & (GT == 1)).sum()), n_nan_ratio_G0=int((nan & (GT == 0)).sum()),
    nan_examples=ex,
    note_sealed_code_effect="np.argsort 把 NaN 排在最末（κ 秩最大）；封存版 H1 的 ρ=0.1615 含此伪秩；封存版 H2 的 MW 遇 NaN 返回 NaN→null",
    exploratory_H1_nan_excluded=dict(n=int(fin.sum()), rho=round(rho_fin, 4), perm_p=round((cnt + 1) / 5001, 5)),
    exploratory_H2_nan_excluded=dict(n_dead=int(dead.size), n_alive=int(alive.size),
                                     med_kappa_dead=round(float(np.median(dead)), 4), med_kappa_alive=round(float(np.median(alive)), 4),
                                     mw_p_one_sided=p_h2))

# ---- (b) top-30 重叠核对 ----
m = json.load(open(f"{FIN}/E73_SHORTCUT_MAP.json"))
ms = json.load(open(f"{ENV}/ledger/metric_search_diag45.json"))
top30 = {(t[0], t[1] or "") for t in ms["top"]}
z = np.load(AX, allow_pickle=True)
A, B, D, G = z["A_z"], z["B_z"], z["D_z"], z["G"]; Am, Bm = z["A_m"], z["B_m"]
A45, B45, D45 = z["A_45"], z["B_45"], z["D_45"]
num = z["num"].astype(str); den = z["den"].astype(str)
S_A = (A >= 0.7) & (B >= 0.9); gate45 = (A45 >= 0.7) & (B45 >= 0.9); mg = (Am >= 0.7) & (Bm >= 0.9)
triple = S_A & mg & gate45
tri_names = {(num[i], den[i]) for i in np.where(triple)[0]}
esc = {tuple(x) for x in m["P6"]["names"]}
top20 = {(d["num"], d["den"]) for d in m["descriptive"]["top20_residual"]}
out["b_top30_overlap"] = dict(
    file_mtime="2026-09-02 17:28（预先存在）", top30_format="[num, den, rho, B]",
    n_top30=len(top30), overlap_escapees=sorted(map(list, top30 & esc)), overlap_triple_n=len(top30 & tri_names),
    overlap_triple=sorted(map(list, top30 & tri_names)), overlap_top20_residual=sorted(map(list, top30 & top20)),
    diag45_counts=dict(n_pass_A=ms["n_pass_A"], n_pass_AB=ms["n_pass_AB"]))

# ---- (c) P3b 描述性分解 ----
c45 = m["c_45"]["argsort"]
absr = np.abs(A45 - c45 * D)
conf = np.abs(D) >= 0.3
rest = ~triple
def med(mask): return round(float(np.median(absr[mask])), 4) if mask.sum() else None
out["c_P3b_decomposition"] = dict(
    note="描述性，非检验；c_45 取 map 的 4 位小数值（与 e73d 内部全精度差 <5e-5）",
    med_triple=med(triple), n_triple=int(triple.sum()),
    med_rest=med(rest), n_rest=int(rest.sum()),
    med_rest_absA45_lt_0p3=med(rest & (np.abs(A45) < 0.3)), n_rest_absA45_lt_0p3=int((rest & (np.abs(A45) < 0.3)).sum()),
    med_rest_absA45_ge_0p7=med(rest & (np.abs(A45) >= 0.7)), n_rest_absA45_ge_0p7=int((rest & (np.abs(A45) >= 0.7)).sum()),
    med_rest_A45_ge_0p7=med(rest & (A45 >= 0.7)), n_rest_A45_ge_0p7=int((rest & (A45 >= 0.7)).sum()),
    med_S_A_surv45_not_triple=med(S_A & gate45 & ~mg), n_S_A_surv45_not_triple=int((S_A & gate45 & ~mg).sum()),
    med_S_A_dead45=med(S_A & ~gate45),
    med_all_conf=med(conf), med_all_nonconf=med(~conf),
    triple_mean_signed_r=round(float(np.mean((A45 - c45 * D)[triple])), 4),
    rest_A45ge0p7_mean_signed_r=round(float(np.mean((A45 - c45 * D)[rest & (A45 >= 0.7)])), 4))

# ---- (d) P6 存活者点名 ----
P6 = m["P6"]
out["d_P6_named"] = dict(
    strict=[P6["names"][i] + [P6["A_45"][i], P6["B_45"][i]] for i in range(12) if P6["A_45"][i] >= 0.9 and P6["B_45"][i] >= 0.9],
    standard=[P6["names"][i] + [P6["A_45"][i], P6["B_45"][i]] for i in range(12) if P6["A_45"][i] >= 0.7 and P6["B_45"][i] >= 0.9],
    n_A45_ge_0p7=sum(1 for x in P6["A_45"] if x >= 0.7), n_B45_lt_0p9=sum(1 for x in P6["B_45"] if x < 0.9))
out["elapsed_s"] = round(time.time() - t0, 1)
json.dump(out, open(f"{FIN}/E73X_POSTHOC.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, ensure_ascii=False, indent=1))
