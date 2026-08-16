#!/usr/bin/env python
"""首个真实验：rx0（地形陡度）扫描。
目的 1 — 环境验证：地形越陡 → 伪流越大（已知单调关系）
目的 2 — 代理指标 vs 真指标的分歧，在真实扫描上量化
NTIMES=2880, DT=30 → 正好 1 天模式时间，对齐论文的 "day1" 口径。
"""
import os, sys, json, subprocess, time, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mkrun import make_run
from diagnostics import diagnose

ENV = "/data/xinyuan/GOAI_ai4s_env"
BIN = f"{ENV}/bin/coawstM_goai"
NTIMES = 2880                       # 1 天

GRIDS = [
    ("rx0=0.20", "grid_rx0.2.nc"),
    ("rx0=0.40", "grid_rx0.4.nc"),
    ("rx0=0.50", "grid_rx0p50.nc"),
    ("rx0=0.60", "grid_rx0p60.nc"),
    ("rx0=0.70", "grid_rx0p70.nc"),
    ("rx0=0.85", "grid_rx0p85.nc"),
    ("raw(未平滑)", "grid_raw.nc"),
]


def one(label, grid):
    rid = "rx0_" + grid.replace("grid_", "").replace(".nc", "")
    rd = make_run(rid, grid=grid, ntimes=NTIMES)
    env = dict(os.environ, PATH="/usr/bin:" + os.environ.get("PATH", ""))
    t0 = time.time()
    with open(f"{rd}/run.log", "w") as lg:
        subprocess.run([BIN, "roms.in"], cwd=rd, stdout=lg, stderr=subprocess.STDOUT,
                       env=env)
    wall = time.time() - t0
    d = diagnose(f"{rd}/roms_his.nc", f"{rd}/run.log")
    d["meta"]["wall_s"] = round(wall, 1)
    d["meta"]["label"] = label
    d["meta"]["grid"] = grid
    return d


if __name__ == "__main__":
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(lambda g: one(*g), GRIDS))
    json.dump(res, open(f"{ENV}/ledger/sweep_rx0.json", "w"),
              ensure_ascii=False, indent=1)

    print(f"总耗时 {time.time()-t0:.0f}s  (7 run 并发)\n")
    hdr = (f"{'地形':<14}{'完赛':<6}{'KE_final':>11}{'max|u|':>9}{'rms|u|':>9}"
           f"{'体积rms':>9}{'V>1cm/s':>9}{'能量漂移':>10}")
    print(hdr); print("-" * len(hdr))
    for r in res:
        p, t, m = r["proxy"], r["true"], r["meta"]
        print(f"{m['label']:<14}{'✓' if m['completed'] else '✗':<6}"
              f"{p.get('KE_final', float('nan')):>11.3e}"
              f"{p.get('spurious_max_cms', float('nan')):>9.2f}"
              f"{p.get('spurious_rms_cms', float('nan')):>9.3f}"
              f"{t.get('spurious_rms_volwt_cms', float('nan')):>9.3f}"
              f"{t.get('vol_frac_speed_gt_0.01', float('nan')):>9.3f}"
              f"{t.get('total_energy_drift_rel', float('nan')):>10.1e}")
    print(f"\n(单位: cm/s; V>1cm/s = 速度超 1cm/s 的体积占比)")
