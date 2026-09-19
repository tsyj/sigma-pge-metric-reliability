# -*- coding: utf-8 -*-
"""
power_ledger.py —— P6＋功效台账（NULL_AUDIT 合成尺子）。
网格：p_true ∈ {0.90,0.925,0.95,0.975,1.00} × 预算 n ∈ {32,88,204}；
策略：认证 e-过程（混合 U(0.9,1]，逐对看）、e-过程（点备择 0.95）、Wilson 一次性（只看预算末）。
每格 20000 次模拟。P6 判分字段：eproc_mix 在 (0.95, 32) 与 (0.95, 204) 的认证率。
合成“0.95/0.95 尺子”= 逐对胜率 0.95 的合成流（A/B 双 0.95 宣称压成配对胜率口径，PREREG P6）。
显著标注：本表为功效估计（注入已知真值的合成流），非对真实尺子的认证。
输出 POWER_LEDGER.json。
"""
import json
import os
import numpy as np
import cert_gate as cg

_HERE_GUARD = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(_HERE_GUARD, "PREREG_cert_stat_ledger.sha256")):
    raise SystemExit("拒跑：PREREG 未封存（缺 .sha256）——盘外产出无预注册效力")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "POWER_LEDGER.json")
P_GRID = [0.90, 0.925, 0.95, 0.975, 1.00]
N_GRID = [32, 88, 204]
R = 20_000
SEED = 20260917 + 5


def main():
    rng = np.random.default_rng(SEED)
    n_max = max(N_GRID)
    tab_mix = cg.ETable(n_max, n_max, kind="cert")
    tab_pt = cg.ETable(n_max, n_max, kind="point", q_star=0.95)
    log_thresh = np.log(cg.E_STAR)
    t = np.arange(1, n_max + 1, dtype=np.int32)[None, :]
    table = {}
    for p in P_GRID:
        x = (rng.random((R, n_max)) < p)
        wins = np.cumsum(x, axis=1, dtype=np.int32)
        loge_mix = tab_mix.log_e[wins, t - wins]
        loge_pt = tab_pt.log_e[wins, t - wins]
        for n in N_GRID:
            cell = {
                "eproc_mix": float((loge_mix[:, :n] >= log_thresh).any(axis=1).mean()),
                "eproc_point095": float((loge_pt[:, :n] >= log_thresh).any(axis=1).mean()),
            }
            lo, _ = cg.wilson_ci(wins[:, n - 1].astype(float), float(n))
            cell["wilson_oneshot"] = float((lo > cg.P0).mean())
            table[f"p{p}_n{n}"] = cell
    res = {
        "module": "P6_power_ledger",
        "p_grid": P_GRID, "n_grid": N_GRID, "R": R, "seed": SEED,
        "min_effect_of_concern": 0.05,
        "table": table,
        "P6_power_e_at_32": table["p0.95_n32"]["eproc_mix"],
        "P6_power_e_at_204": table["p0.95_n204"]["eproc_mix"],
        "label": "功效估计（合成流注入），非对真实尺子的认证（PREREG P6 显著标注）",
    }
    with open(OUT, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
