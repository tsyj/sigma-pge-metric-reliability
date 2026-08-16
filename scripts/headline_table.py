#!/usr/bin/env python
"""头条表：σ 坐标 vs z 坐标真值 —— 全部出自本环境可复现的 clean 流水线。

E33 之前，这张表的 ROMS 一侧用的是用户科研目录里的 `his_r26_dj10.nc`。
那个文件**我们无法复现**：
  · 产出它的二进制是 `coawstM_dnn_ramp_wind`（同目录躺着 delta_rho.bin 等
    DNN 密度修正场），不是我们从源码重建的 clean 二进制
  · 它的温度冲出初始层结上限 3.08 °C（28.98 vs 25.9），而 clean run 只有 0.09 °C
  · 同配置逐帧比值在 0.73–1.19 之间摆动，不是可复现的关系

现在两侧都出自可复现流水线：
  ROMS  : coawstM_goai_v4 (sha256 b50851d9…)，ocean_r26_dj10.in，NTIMES=25920
  真值  : MITgcm 源码重建 (sha256 661436c3…)，viscAz=1e-5 与 AKV_BAK 匹配
"""
import json, sys, os
import numpy as np
import netCDF4 as nc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mitgcm import read_field, iters

E = "/data/xinyuan/GOAI_ai4s_env"
TRUTH = f"{E}/truth/sw_viscAz_1pEm5"      # 与 ROMS 的 AKV_BAK=1e-5 匹配


def find_run():
    rid = None
    for l in open(f"{E}/ledger/env2_runs.jsonl"):
        r = json.loads(l)
        if (r["ntimes"] == 25920 and r["bathy"] == "r26steep"
                and r["obs"].get("valid")
                and abs(r["action"].get("VISC2", -1) - 50.0) < 1e-9):
            rid = r["run_id"]
    return rid


def main():
    rid = find_run()
    assert rid, "找不到 VISC2=50 的 3 天 clean run"
    d = nc.Dataset(f"{E}/runs/{rid}/out_his.nc")
    t = np.asarray(d["ocean_time"][:])
    dt = t[1] - t[0]
    days = (t - t[0]) / 86400.0 + dt / 86400.0

    its = iters("U", TRUTH)
    rows = []
    for k, day in enumerate(days):
        it = int(round(day * 86400 / 30))
        if it not in its:
            continue
        u = np.asarray(d["u"][k])
        U = read_field("U", it, TRUTH)
        rows.append(dict(
            day=float(day),
            r_max=float(np.abs(u).max() * 100),
            r_rms=float(np.sqrt((u ** 2).mean()) * 100),
            t_max=float(np.abs(U).max() * 100),
            t_rms=float(np.sqrt((U ** 2).mean()) * 100),
            temp_max=float(np.asarray(d["temp"][k]).max())))

    print("=" * 82)
    print("σ 坐标 vs z 坐标真值（同地形 48×48 峰 80 m · 同 13 层 · 同风应力 · 同 3 天）")
    print("唯一差别 = 垂向坐标。两侧二进制均可从源码重建。")
    print("=" * 82)
    print(f"{'天':>5} {'ROMS |U|max':>12} {'真值 |U|max':>12} {'倍数':>8} "
          f"{'ROMS rms':>10} {'真值 rms':>9} {'倍数':>8}")
    print("-" * 82)
    for r in rows:
        print(f"{r['day']:>5.1f} {r['r_max']:>12.2f} {r['t_max']:>12.2f} "
              f"{r['r_max']/r['t_max']:>7.1f}× {r['r_rms']:>10.2f} "
              f"{r['t_rms']:>9.2f} {r['r_rms']/r['t_rms']:>7.1f}×")
    print("-" * 82)
    rm = [r["r_max"] / r["t_max"] for r in rows]
    rr = [r["r_rms"] / r["t_rms"] for r in rows]
    sys_ = [x for x in rm if x < 50]
    print(f"  |U|max 倍数 {min(rm):.0f}–{max(rm):.0f}×"
          f"（剔除惯性节点后系统性 {min(sys_):.0f}–{max(sys_):.0f}×）")
    print(f"  rms   倍数 {min(rr):.1f}–{max(rr):.1f}×")
    print(f"  ROMS 温度最大 {max(r['temp_max'] for r in rows):.3f} °C"
          f"（初始层结上限 25.9 → 超调 {max(r['temp_max'] for r in rows)-25.9:+.2f} °C）")

    json.dump(dict(run_id=rid, truth_dir=TRUTH, rows=rows),
              open(f"{E}/ledger/headline_table.json", "w"),
              ensure_ascii=False, indent=1)
    print(f"\n→ ledger/headline_table.json   (run {rid})")


if __name__ == "__main__":
    main()
