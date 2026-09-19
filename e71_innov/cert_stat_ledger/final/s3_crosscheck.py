# -*- coding: utf-8 -*-
"""
s3_crosscheck.py —— S3：交叉校核（仅报告，无通过线；PREREG §2）。
同一模拟流上比较两种任意时刻方法的"预算 204 内发证"判决一致率：
  (a) beta-混合 e-过程（U(0.9,1] 先验，cert_gate.ETable）；
  (b) 下注式置信序列（半凯利）：备择 q*=0.95 的 Kelly 系数 λ*=(0.95-0.9)/(0.9*0.1)=5/9，
      半凯利 λ=5/18；e_win=1+λ(1-0.9)，e_loss=1-λ*0.9；累积财富 >=40 发证。
两档 p_true ∈ {0.90, 0.95}，各 R=20000 流，n=204。
输出 S3_CROSSCHECK.json。
"""
import json
import os
import numpy as np
import cert_gate as cg

HERE = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(HERE, "PREREG_cert_stat_ledger.sha256")):
    raise SystemExit("拒跑：PREREG 未封存（缺 .sha256）——盘外产出无预注册效力")
OUT = os.path.join(HERE, "S3_CROSSCHECK.json")
R = 20_000
N = 204
LAM = 0.5 * (0.95 - 0.9) / (0.9 * 0.1)     # 半凯利 5/18
SEED = 20260917 + 8


def main():
    rng = np.random.default_rng(SEED)
    tab = cg.ETable(N, N, kind="cert")
    log_thresh = np.log(cg.E_STAR)
    lw_win = np.log1p(LAM * (1 - cg.P0))       # log e_win
    lw_loss = np.log1p(-LAM * cg.P0)           # log e_loss
    t = np.arange(1, N + 1, dtype=np.int32)[None, :]
    panels = {}
    for p_true in (0.90, 0.95):
        x = (rng.random((R, N)) < p_true)
        wins = np.cumsum(x, axis=1, dtype=np.int32)
        d_mix = (tab.log_e[wins, t - wins] >= log_thresh).any(axis=1)
        logw = wins * lw_win + (t - wins) * lw_loss
        d_kelly = (logw >= log_thresh).any(axis=1)
        panels[f"p{p_true}"] = {
            "cert_rate_mix": float(d_mix.mean()),
            "cert_rate_halfkelly": float(d_kelly.mean()),
            "agreement": float((d_mix == d_kelly).mean()),
        }
    res = {
        "module": "S3_crosscheck",
        "report_only": True,
        "R": R, "n_max": N, "lambda_halfkelly": LAM, "seed": SEED,
        "panels": panels,
        "note": "两法各自任意时刻有效；一致率只作交叉校核展板，不设通过线（PREREG §2）",
    }
    with open(OUT, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
