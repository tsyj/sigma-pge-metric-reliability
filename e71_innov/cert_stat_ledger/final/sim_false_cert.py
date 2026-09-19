# -*- coding: utf-8 -*-
"""
sim_false_cert.py —— P1/P2：假发证率模拟（p_true=0.9 边界）。
三策略：
  (i)  Wilson 无限续期：看点 n=32,36,...,204，任一看点 Wilson 下界>0.9 即发证；
  (ii) Wilson 一次性预注册延样：只看 n=204；
  (iii) 认证 e-过程（U(0.9,1] 先验）：每对都看，n<=204，e>=40 即发证。
参数冻结于 PREREG §0：R=200000，seed=20260917+1。
输出 SIM_FALSE_CERT.json。禁止在 PREREG 封存前运行（run_all.sh 有硬门）。
"""
import json
import os
import numpy as np
import cert_gate as cg

_HERE_GUARD = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(_HERE_GUARD, "PREREG_cert_stat_ledger.sha256")):
    raise SystemExit("拒跑：PREREG 未封存（缺 .sha256）——盘外产出无预注册效力")

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SIM_FALSE_CERT.json")
R = 200_000
N_MAX = 204
LOOKS = np.arange(32, N_MAX + 1, 4)      # 44 看点
P_TRUE = 0.9
SEED = 20260917 + 1


def main():
    rng = np.random.default_rng(SEED)
    tab = cg.ETable(N_MAX, N_MAX, kind="cert")
    log_thresh = np.log(cg.E_STAR)
    n_opt = n_one = n_epr = 0
    CH = 20_000                                     # 分块控内存
    for s in range(0, R, CH):
        r = min(CH, R - s)
        x = (rng.random((r, N_MAX)) < P_TRUE)
        wins = np.cumsum(x, axis=1, dtype=np.int32)         # (r, N_MAX)
        t = np.arange(1, N_MAX + 1, dtype=np.int32)[None, :]
        # (i) / (ii) Wilson
        kL = wins[:, LOOKS - 1]
        lo, _ = cg.wilson_ci(kL, LOOKS[None, :].astype(float))
        n_opt += int((lo > cg.P0).any(axis=1).sum())
        lo1, _ = cg.wilson_ci(wins[:, -1].astype(float), float(N_MAX))
        n_one += int((lo1 > cg.P0).sum())
        # (iii) e-过程
        loge = tab.log_e[wins, t - wins]
        n_epr += int((loge >= log_thresh).any(axis=1).sum())
    res = {
        "module": "P1P2_false_cert",
        "p_true": P_TRUE, "n_sims": R, "n_max": N_MAX,
        "looks": LOOKS.tolist(), "alpha_one_sided": cg.ALPHA,
        "seed": SEED,
        "r_optstop": n_opt / R,
        "r_oneshot204": n_one / R,
        "r_eproc": n_epr / R,
        "mc_se_at_0.06": float(np.sqrt(0.06 * 0.94 / R)),
        "note": "p_true 恰在门 0.9 上；发证=宣称 p>0.9；(iii) 由 Ville 不等式保 <=0.025",
    }
    with open(OUT, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
