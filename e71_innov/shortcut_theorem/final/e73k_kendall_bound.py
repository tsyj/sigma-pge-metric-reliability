#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E73 shortcut_theorem · PREREG §7.2 Kendall 论证的 ε̂ 标定与逐候选机械核对（封存后，描述性，非预注册预测，不改判）。

距离取"配对符号 Hamming 距离"：对 n 条带标签陡臂的 P=C(n,2) 个配对，d(x,y)=#{(i,j): sign(x_i−x_j) ≠ sign(y_i−y_j)}。
它是 {−1,0,1}^P 上的 Hamming 距离，严格满足三角不等式（并列也成立）；无并列时即 Kendall 距离。
τ_H(x,y) ≡ 1 − 2d/P。skill′ ≡ −skill_vs_zero（与 A 同向）。ε̂ ≡ d(spur, skill′)/P。
定理式：|τ_H(m,skill′) − τ_H(m,spur)| ≤ 2ε̂ 对每个候选 m 成立——本脚本逐候选核对（代码自检，应 0 违例）。
候选枚举与 e73t/e67b 同口径（steep/flat 全体键交集、分母近零剔除、读数须 >0）；B 不参与。
输出：E73K_KENDALL.json（纬向＝样本内；45°＝封存后留出，仅描述）。
"""
import hashlib, json, os, sys, time
import numpy as np
ENV = "/data/xinyuan/GOAI_ai4s_env"; FIN = f"{ENV}/e71_innov/shortcut_theorem/final"
sys.path.insert(0, f"{ENV}/scripts")
import metric_search  # noqa: E402
assert os.path.realpath(metric_search.__file__).endswith("GOAI_ai4s_env/scripts/metric_search.py")
from metric_search import base_quantities  # noqa: E402
t0 = time.time()
out = dict(script="e73k_kendall_bound.py", script_sha=hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(),
           status="封存后描述性，非预注册，不改判", prereg_sha=open(f"{FIN}/PREREG_shortcut_theorem.sha256").readline().split()[0])

def load(ledger, runsdir, reg_from):
    reg = {}
    if reg_from == "regraded":
        for l in open(f"{ENV}/ledger/regraded_v2.jsonl"):
            r = json.loads(l); reg[r["run_id"]] = r["skill_vs_zero"]
    seen = {}
    for l in open(ledger):
        r = json.loads(l)
        if not (r["obs"].get("valid") and r["ntimes"] == 8640): continue
        seen[r["run_id"]] = r["bathy"]
        if reg_from == "hidden" and r["bathy"] == "r26steep" and (r.get("hidden") or {}).get("skill_vs_zero") is not None:
            reg[r["run_id"]] = r["hidden"]["skill_vs_zero"]
    r26 = [k for k, v in seen.items() if v == "r26steep" and k in reg]
    flat = [k for k, v in seen.items() if v == "flat"]
    Q26, S = [], []
    for rid in r26:
        q = base_quantities(f"{runsdir}/{rid}")
        if q: Q26.append(q); S.append(reg[rid])
    QFL = [q for q in (base_quantities(f"{runsdir}/{rid}") for rid in flat) if q]
    keys = sorted(set.intersection(*[set(q) for q in Q26 + QFL]))
    M26 = np.array([[q[k] for k in keys] for q in Q26]); MFL = np.array([[q[k] for k in keys] for q in QFL])
    return keys, M26, MFL, np.array(S)

def run(tag, ledger, runsdir, reg_from):
    keys, M26, MFL, S = load(ledger, runsdir, reg_from)
    n = M26.shape[0]; iu, ju = np.triu_indices(n, 1); P = iu.size
    sg = lambda x: np.sign(x[iu] - x[ju]).astype(np.int8)
    skillp = sg(-S); spur = sg(M26[:, keys.index("u|all|rms")])
    eps = float((spur != skillp).mean())
    EPS = 1e-12; tS, tU, names = [], [], []
    for i, kn in enumerate(keys):
        cand = [(kn, "", M26[:, i], MFL[:, i])]
        for j, kd in enumerate(keys):
            if i == j or np.any(np.abs(M26[:, j]) < EPS) or np.any(np.abs(MFL[:, j]) < EPS): continue
            cand.append((kn, kd, M26[:, i] / M26[:, j], MFL[:, i] / MFL[:, j]))
        for a, b, v26, vfl in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))) or np.any(v26 <= 0) or np.any(vfl <= 0): continue
            s = sg(v26)
            tS.append(1 - 2 * float((s != skillp).mean())); tU.append(1 - 2 * float((s != spur).mean())); names.append((a, b))
    tS, tU = np.array(tS), np.array(tU)
    diff = np.abs(tS - tU)
    good = tS >= 0.7
    out[tag] = dict(n_runs=int(n), n_pairs_P=int(P), n_candidates=int(tS.size),
                    eps_hat=round(eps, 4), bound_2eps=round(2 * eps, 4),
                    tauH_spur_skill=round(1 - 2 * eps, 4),
                    max_abs_diff=round(float(diff.max()), 4), n_violations=int((diff > 2 * eps + 1e-12).sum()),
                    n_tauH_skill_ge_0p7=int(good.sum()),
                    min_tauH_spur_among_those=round(float(tU[good].min()), 4) if good.sum() else None,
                    implied_floor=round(0.7 - 2 * eps, 4))
    print(tag, json.dumps(out[tag]), "%.0fs" % (time.time() - t0), flush=True)

run("zonal_insample", f"{ENV}/ledger/env2_runs.jsonl", f"{ENV}/runs", "regraded")
run("diag45_postseal", f"{ENV}/ledger/env2_diag45_runs.jsonl", f"{ENV}/runs_diag45", "hidden")
out["elapsed_s"] = round(time.time() - t0, 1)
json.dump(out, open(f"{FIN}/E73K_KENDALL.json", "w"), indent=1, ensure_ascii=False)
print("E73K_DONE")
