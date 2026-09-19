# -*- coding: utf-8 -*-
"""
perm_ledger.py —— P5：三判死格 sign-flip 置换 p（B=10000，单侧 P(K<=k_obs)）。
H0：配对内（海山, 平底）标签可交换 ⇒ 胜负指示翻转 ⇒ K~Binom(n,1/2)。
置换实现为 MC 翻转（尊重候选规格的“置换”口径）；另附精确二项 CDF 交叉核对（不参与判分）。
输出 PERM_LEDGER.json。
"""
import json
import math
import os
import numpy as np

_HERE_GUARD = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(_HERE_GUARD, "PREREG_cert_stat_ledger.sha256")):
    raise SystemExit("拒跑：PREREG 未封存（缺 .sha256）——盘外产出无预注册效力")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "PERM_LEDGER.json")
E58 = "/data/xinyuan/GOAI_ai4s_env/e44/analysis/E58_TRIVALENT.json"
CELLS = {"uv_diag45_paired": (7, 28), "vu_zonal_paired": (7, 32), "vu_merid_paired": (3, 28)}
B = 10_000
SEED = 20260917 + 4


def binom_cdf(k, n):
    return sum(math.comb(n, i) for i in range(k + 1)) / 2.0 ** n


def main():
    rng = np.random.default_rng(SEED)
    rows = json.load(open(E58))["rows"]
    out = {}
    for name, (k_exp, n_exp) in CELLS.items():
        k, n = int(rows[name]["k"]), int(rows[name]["n"])
        assert (k, n) == (k_exp, n_exp), (name, k, n)
        K = (rng.random((B, n)) < 0.5).sum(axis=1)
        p_perm = float((K <= k).mean())
        # 加一修正版（置换检验惯例，主判分用它，更保守）
        p_perm_plus = float(((K <= k).sum() + 1) / (B + 1))
        out[name] = {
            "k": k, "n": n,
            "p_perm_onesided": p_perm,
            "p_perm_plus1": p_perm_plus,
            "p_binom_exact_check": binom_cdf(k, n),
        }
    res = {
        "module": "P5_perm_ledger",
        "H0": "配对内标签可交换（sign-flip）",
        "B": B, "seed": SEED,
        "judged_field": "p_perm_plus1",
        "cells": out,
    }
    with open(OUT, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
