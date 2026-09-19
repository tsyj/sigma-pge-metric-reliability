# -*- coding: utf-8 -*-
"""
price_table.py —— P3：认证明码标价（确定性计算）。
  n*_mix   : 全胜流下混合先验 U(0.9,1] e-过程首次 e>=40 的连对数；
  n*_point : 点备择 q*=0.95 版本；
  AV_LB_32of32 : 32 连胜的任意时刻有效 95% 下界（p0 网格反转）；
  同框对照（非预测）：Wilson(32/32) 下界。
输出 PRICE_TABLE.json。
"""
import json
import os
import numpy as np
import cert_gate as cg

_HERE_GUARD = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(_HERE_GUARD, "PREREG_cert_stat_ledger.sha256")):
    raise SystemExit("拒跑：PREREG 未封存（缺 .sha256）——盘外产出无预注册效力")

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PRICE_TABLE.json")


def main():
    n_mix = cg.n_star_all_wins(kind="cert")
    n_point = cg.n_star_all_wins(kind="point", q_star=0.95)
    av_lb = cg.av_lower_bound(np.ones(32, dtype=int))
    wlo, whi = cg.wilson_ci(32.0, 32.0)
    res = {
        "module": "P3_price_table",
        "alpha_one_sided": cg.ALPHA, "e_star": cg.E_STAR, "gate_p0": cg.P0,
        "n_star_mix_U(0.9,1]": n_mix,
        "n_star_point_0.95": n_point,
        "AV_LB_32of32": av_lb,
        "wilson_lb_32of32_known": float(wlo),
        "note": "确定性量；Wilson 行是封存时已知对照（PREREG §0b），不参与判分方向",
    }
    with open(OUT, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
