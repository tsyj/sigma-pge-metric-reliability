# -*- coding: utf-8 -*-
"""
s1_flip_table.py —— S1：三档阈值翻转表（描述性，无通过线；PREREG §2）。
0.85/0.90/0.95 × 六配对格 × {Wilson 三值判定, AV 触发率}。
Wilson 三值：lb>thr 判"过"，ub<thr 判"死"，否则 U。
AV 触发率：真实次序不可恢复（RUNS_MANIFEST 无时间戳），对每格用 B=1000 个次序置换，
  报告认证 e-过程（U(thr,1] 先验）与判死 e-过程（U[0,thr) 先验）在 n 对内 e>=40 的触发比例。
  全胜格（32/32）次序不变，触发率为 0/1。
输出 S1_FLIP_TABLE.json。
"""
import json
import os
import numpy as np
import cert_gate as cg

HERE = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(HERE, "PREREG_cert_stat_ledger.sha256")):
    raise SystemExit("拒跑：PREREG 未封存（缺 .sha256）——盘外产出无预注册效力")
OUT = os.path.join(HERE, "S1_FLIP_TABLE.json")
E58 = "/data/xinyuan/GOAI_ai4s_env/e44/analysis/E58_TRIVALENT.json"
CELLS = {"uv_zonal_paired": (32, 32), "uv_merid_paired": (25, 28), "uv_diag45_paired": (7, 28),
         "vu_zonal_paired": (7, 32), "vu_merid_paired": (3, 28), "vu_diag45_paired": (23, 28)}
THRESHOLDS = [0.85, 0.90, 0.95]
B = 1_000
SEED = 20260917 + 7


def main():
    rng = np.random.default_rng(SEED)
    rows = json.load(open(E58))["rows"]
    log_thresh = np.log(cg.E_STAR)
    table = {}
    for name, (k_exp, n_exp) in CELLS.items():
        k, n = int(rows[name]["k"]), int(rows[name]["n"])
        assert (k, n) == (k_exp, n_exp), (name, k, n)
        base = np.zeros(n, dtype=np.int32)
        base[:k] = 1
        seqs = np.tile(base, (B, 1))
        idx = np.argsort(rng.random((B, n)), axis=1)
        seqs = np.take_along_axis(seqs, idx, axis=1)
        wins = np.cumsum(seqs, axis=1, dtype=np.int32)
        t = np.arange(1, n + 1, dtype=np.int32)[None, :]
        wlo, whi = cg.wilson_ci(float(k), float(n))
        cell = {"k": k, "n": n, "wilson_ci95": [float(wlo), float(whi)]}
        for thr in THRESHOLDS:
            tab_c = cg.ETable(n, n, kind="cert", p0=thr)
            tab_k = cg.ETable(n, n, kind="kill", p0=thr)
            cert_frac = float((tab_c.log_e[wins, t - wins] >= log_thresh).any(axis=1).mean())
            kill_frac = float((tab_k.log_e[wins, t - wins] >= log_thresh).any(axis=1).mean())
            wv = "过" if wlo > thr else ("死" if whi < thr else "U")
            cell[f"thr{thr}"] = {"wilson_trivalent": wv,
                                 "av_cert_trigger_frac": cert_frac,
                                 "av_kill_trigger_frac": kill_frac}
        table[name] = cell
    res = {
        "module": "S1_flip_table",
        "descriptive_no_passline": True,
        "thresholds": THRESHOLDS, "B_order_perms": B, "seed": SEED,
        "ordering_note": "真实次序不可恢复（RUNS_MANIFEST 无时间戳，PREREG §0）；AV 列为次序置换触发率",
        "table": table,
    }
    with open(OUT, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
