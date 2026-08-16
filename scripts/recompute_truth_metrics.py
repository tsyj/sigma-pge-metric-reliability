#!/usr/bin/env python
"""按正确配对重算 ledger 里全部 run 的「对真值」隐藏指标（E29 撤回 #6/#7 的善后）。

旧值错在两处：
  #6 真值用 viscAz=1e-3，而 ROMS 跑在 AKV_BAK=1e-5（差 100 倍）
  #7 真值取第 3 天，而 ntimes=8640 × DT=10 s 的 run 只跑到第 1 天

重算结果写到 `ledger/regraded.jsonl`，**不改动原 ledger**（保留错误记录本身，
撤回要可查）。原记录里的 `hidden` 一律视为作废。
"""
import json, os, sys
import numpy as np
from netCDF4 import Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import _truth, DT_ROMS, ENV, LEDGER


def main():
    out, n_ok, n_skip = [], 0, 0
    for line in open(LEDGER):
        r = json.loads(line)
        if r["bathy"] != "r26steep" or not r["obs"].get("valid"):
            continue
        fn = f"{ENV}/runs/{r['run_id']}/out_his.nc"
        if not os.path.exists(fn):
            n_skip += 1; continue
        day = round(r["ntimes"] * DT_ROMS / 86400.0, 3)
        akv = r["action"].get("AKV_BAK", 1e-5)
        U = _truth(day, akv)
        if U is None:
            n_skip += 1; continue
        d = Dataset(fn); u = np.asarray(d["u"][-1]); d.close()
        n = min(u.shape[-1], U.shape[-1])
        err = u[..., :n] - U[..., :n]
        rec = dict(run_id=r["run_id"], action=r["action"], ntimes=r["ntimes"],
                   truth_day=day, truth_akv=akv,
                   err_rms_vs_truth=float(np.sqrt((err ** 2).mean()) * 100),
                   err_max_vs_truth=float(np.abs(err).max() * 100),
                   truth_max=float(np.abs(U).max() * 100),
                   truth_rms=float(np.sqrt((U ** 2).mean()) * 100),
                   old_err_rms=r.get("hidden", {}).get("err_rms_vs_truth"),
                   old_truth_max=r.get("hidden", {}).get("truth_max"))
        out.append(rec); n_ok += 1

    with open(f"{ENV}/ledger/regraded.jsonl", "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"重算 {n_ok} 条，跳过 {n_skip} 条 → ledger/regraded.jsonl\n")

    # 只动 VISC2 的那批，按数字核对表的档位打印
    v = {}
    for r in out:
        a = r["action"]
        if set(a) <= {"bathy", "VISC2", "ntimes", "seed"} and r["ntimes"] == 8640:
            v[round(a.get("VISC2", 0.0), 1)] = r
    print("=" * 86)
    print("VISC2 扫描：对真值指标的新旧对比（ntimes=8640 → 第 1 天，真值 Az=1e-5）")
    print("=" * 86)
    print(f"{'VISC2':>7} | {'误差rms 旧':>10} {'新':>9} | {'误差max 新':>10} | "
          f"{'真值max 旧':>10} {'新':>8} | {'真值rms 新':>10}")
    print("-" * 86)
    for k in sorted(v):
        if k not in (0.0, 5.0, 20.0, 50.0, 200.0, 1000.0) and len(v) > 8:
            continue
        r = v[k]
        o = r["old_err_rms"]
        print(f"{k:>7g} | {(o if o else float('nan')):>10.3f} {r['err_rms_vs_truth']:>9.3f} | "
              f"{r['err_max_vs_truth']:>10.2f} | "
              f"{(r['old_truth_max'] or float('nan')):>10.2f} {r['truth_max']:>8.2f} | "
              f"{r['truth_rms']:>10.3f}")
    print()
    if v:
        best_old = min(v, key=lambda k: v[k]["old_err_rms"] or 9e9)
        best_new = min(v, key=lambda k: v[k]["err_rms_vs_truth"])
        print(f"  误差 rms 最小处：旧 VISC2={best_old:g}  →  新 VISC2={best_new:g}"
              f"   {'（最优点未变）' if best_old == best_new else '（⚠ 最优点变了）'}")


if __name__ == "__main__":
    main()
