# -*- coding: utf-8 -*-
"""
kill_wouldhave.py —— P4：三判死格 would-have 爆仓停时。
数据：E58_TRIVALENT.json 三判死格 (k,n)（脚本内 assert 与 PREREG §0b 一致）。
次序：RUNS_MANIFEST 无时间戳（PREREG §0 已核），用观测胜负多重集的 10000 个随机重排取平均。
规则：判死 e-过程（U[0,0.9) 先验），e>=40 判死；从未判死记停时=n。
输出 KILL_WOULDHAVE.json（内嵌 R3 冻结图注）。
"""
import json
import os
import numpy as np
import cert_gate as cg

_HERE_GUARD = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(_HERE_GUARD, "PREREG_cert_stat_ledger.sha256")):
    raise SystemExit("拒跑：PREREG 未封存（缺 .sha256）——盘外产出无预注册效力")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "KILL_WOULDHAVE.json")
E58 = "/data/xinyuan/GOAI_ai4s_env/e44/analysis/E58_TRIVALENT.json"
CELLS = ["uv_diag45_paired", "vu_zonal_paired", "vu_merid_paired"]
EXPECTED = {"uv_diag45_paired": (7, 28), "vu_zonal_paired": (7, 32), "vu_merid_paired": (3, 28)}
B = 10_000
SEED = 20260917 + 3
CAPTION_R3 = ("此为“假如当时用认证流”的复盘，非当时的真实决策；实跑 88 对是审计矩阵其他格子"
              "读数的必需来源，节省数字只适用于“只为判死”的场景。")


def main():
    rng = np.random.default_rng(SEED)
    rows = json.load(open(E58))["rows"]
    tab = cg.ETable(40, 40, kind="kill")
    log_thresh = np.log(cg.E_STAR)
    out_cells = {}
    means = []
    for name in CELLS:
        k, n = int(rows[name]["k"]), int(rows[name]["n"])
        assert (k, n) == EXPECTED[name], (name, k, n)
        base = np.zeros(n, dtype=np.int32)
        base[:k] = 1
        seqs = np.tile(base, (B, 1))
        idx = np.argsort(rng.random((B, n)), axis=1)
        seqs = np.take_along_axis(seqs, idx, axis=1)
        wins = np.cumsum(seqs, axis=1, dtype=np.int32)
        t = np.arange(1, n + 1, dtype=np.int32)[None, :]
        loge = tab.log_e[wins, t - wins]
        killed, stop = cg.first_crossing(loge, log_thresh)
        out_cells[name] = {
            "k": k, "n": n,
            "mean_stop_pairs": float(stop.mean()),
            "median_stop_pairs": float(np.median(stop)),
            "p90_stop_pairs": float(np.percentile(stop, 90)),
            "frac_never_killed": float(1.0 - killed.mean()),
        }
        means.append(stop.mean())
    total_actual = sum(EXPECTED[c][1] for c in CELLS)  # 88
    res = {
        "module": "P4_kill_wouldhave",
        "cells": out_cells,
        "sum_mean_stop": float(sum(means)),
        "actual_pairs_run": total_actual,
        "saving_frac_vs_actual": float(1.0 - sum(means) / total_actual),
        "ordering": "RUNS_MANIFEST 无时间戳，B=10000 次序置换平均（PREREG §0 预案）",
        "B": B, "seed": SEED,
        "caption_frozen_R3": CAPTION_R3,
    }
    with open(OUT, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
