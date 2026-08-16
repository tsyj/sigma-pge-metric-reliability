#!/usr/bin/env python
"""⭐ 真值通道上的黏性扫描 —— 测「与 MITgcm 的误差」，不再测代理量。

配置：48×48×13，与 MITgcm run_r29_wind_z13 同地形/同层数/同强迫/同时长。
真目标 = ROMS 与 MITgcm z 坐标真解的差（可测），不是任何代理。
"""
import os, re, sys, json, time, shutil, subprocess
import concurrent.futures as cf
import numpy as np
from netCDF4 import Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mitgcm import read_field, iters

ENV = "/data/xinyuan/GOAI_ai4s_env"
BASE = f"{ENV}/runs/r26_repro"                 # 含参考态 .bin 的工作目录
MIT = "/data/xinyuan/zpg_roms_dev/MITgcm/verification/seamount_roms/run_r29_wind_z13"
VISCS = [0.0, 5.0, 20.0, 50.0, 200.0, 1000.0]
NEED = ["pge_grid_r26steep.nc", "ini_r26steep13.nc", "coawstM_goai_r26",
        "delta_rho.bin", "delta_rho_prev.bin", "dr_solverprev.bin"]


def setup(visc):
    rd = f"{ENV}/runs/tv_{visc:g}".replace(".", "p")
    os.makedirs(rd, exist_ok=True)
    for f in NEED:
        dst = f"{rd}/{f}"
        if not os.path.exists(dst):
            shutil.copy2(f"{BASE}/{f}", dst)
    os.chmod(f"{rd}/coawstM_goai_r26", 0o755)
    out = []
    for line in open(f"{BASE}/ocean_r26_dj10.in", errors="replace"):
        if re.match(r"^\s*VISC2\s*==", line):
            line = f"       VISC2 == {visc}d0\n"
        elif re.match(r"^\s*NHIS\s*==", line):
            line = "        NHIS ==  4320\n"          # DT=10 → 0.5 天，对齐 MITgcm
        elif re.match(r"^\s*(HISNAME|RSTNAME|AVGNAME|DIANAME)\s*==", line):
            k = line.split()[0]
            line = f"     {k} == out_{k[:3].lower()}.nc\n"
        out.append(line)
    open(f"{rd}/roms.in", "w").writelines(out)
    return rd


def run(rd):
    env = dict(os.environ, PATH="/usr/bin:" + os.environ.get("PATH", ""),
               LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:" +
                               os.environ.get("LD_LIBRARY_PATH", ""))
    t0 = time.time()
    with open(f"{rd}/run.log", "w") as lg:
        subprocess.run(["./coawstM_goai_r26", "roms.in"], cwd=rd, stdout=lg,
                       stderr=subprocess.STDOUT, env=env)
    txt = open(f"{rd}/run.log", errors="replace").read()
    return time.time() - t0, "ROMS/TOMS: DONE" in txt, "BLOWUP" in txt


# ---- MITgcm 真值预载（末帧 + 全时序）----
IT = iters("U", MIT)
TRUTH = {i: read_field("U", i, MIT) for i in IT}


def compare(rd):
    d = Dataset(f"{rd}/out_his.nc")
    u = np.asarray(d["u"][:]); ts = np.asarray(d["ocean_time"][:])
    d.close()
    t = (ts - ts[0]) / 86400.0 + 0.5                 # NHIS=4320 × DT=10 = 0.5 天
    tm = np.array([i * 30 / 86400 for i in IT])
    rec = []
    for k in range(len(t)):
        j = int(np.argmin(np.abs(tm - t[k])))
        if abs(tm[j] - t[k]) > 0.1:
            continue
        U = TRUTH[IT[j]]                              # (13,48,48)
        ur = u[k]                                     # (13,48,47)
        n = min(ur.shape[-1], U.shape[-1])
        err = ur[..., :n] - U[..., :n]
        rec.append(dict(day=float(t[k]),
                        roms_max=float(np.abs(ur).max() * 100),
                        truth_max=float(np.abs(U).max() * 100),
                        err_rms=float(np.sqrt((err ** 2).mean()) * 100),
                        err_max=float(np.abs(err).max() * 100),
                        truth_rms=float(np.sqrt((U ** 2).mean()) * 100)))
    return rec


def one(visc):
    rd = setup(visc)
    wall, done, blow = run(rd)
    r = {"VISC2": visc, "ok": done and not blow, "wall_s": round(wall, 1)}
    if r["ok"]:
        r["series"] = compare(rd)
    return r


if __name__ == "__main__":
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(one, VISCS))
    json.dump(res, open(f"{ENV}/ledger/truth_scan.json", "w"),
              ensure_ascii=False, indent=1)
    print(f"总耗时 {time.time()-t0:.0f}s  ({len(VISCS)} 组 48×48×13 × 3 天)\n")
    print("⭐ 真值通道：误差 = ROMS − MITgcm（不是代理量）\n")
    print(f"{'VISC2':>7} | {'末帧误差rms':>11} {'末帧误差max':>11} |"
          f" {'ROMS max':>9} {'真值 max':>8} | {'耗时':>6}")
    print("-" * 68)
    NA = float("nan")
    for r in res:
        if not r["ok"]:
            print(f"{r['VISC2']:>7.0f} | {'未完赛':>11}"); continue
        s = r["series"][-1]
        print(f"{r['VISC2']:>7.0f} | {s['err_rms']:>11.3f} {s['err_max']:>11.2f} |"
              f" {s['roms_max']:>9.2f} {s['truth_max']:>8.2f} | {r['wall_s']:>5.0f}s")
    ok = [r for r in res if r["ok"]]
    if ok:
        e = [r["series"][-1]["err_rms"] for r in ok]
        m = int(np.argmin(e))
        print(f"\n→ 误差最小 @ VISC2={ok[m]['VISC2']:g}  (err_rms={e[m]:.3f} cm/s)")
        print(f"  最大黏性处 err_rms={e[-1]:.3f} → 比最优差 {(e[-1]/e[m]-1)*100:+.0f}%")
