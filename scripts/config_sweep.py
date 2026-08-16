#!/usr/bin/env python
"""⭐ 配置依赖性扫描 —— 把「撤回①」变成正式研究问题。

问题：代理指标推荐的最优黏性，是否依赖地形配置？
      在没有 σ-PGE 的平底对照上，黏性又在"改善"什么？

设计：3 地形 × 5 黏性 = 15 run（48×48×13，DT=10，3 天）
  · flat48   平底 3000 m —— **σ-PGE 按构造恒为 0，对照组**
  · mit      峰 107.7 m
  · r26steep 峰  80.0 m —— **有 MITgcm 独立真值**
"""
import os, re, sys, json, time, shutil, subprocess
import concurrent.futures as cf
import numpy as np
from netCDF4 import Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mitgcm import read_field, iters

ENV = "/data/xinyuan/GOAI_ai4s_env"
SRC = "/data/xinyuan/zpg_roms_dev/pge_test"
BASE = f"{ENV}/runs/r26_repro"
MIT = "/data/xinyuan/zpg_roms_dev/MITgcm/verification/seamount_roms/run_r29_wind_z13"

CONFIGS = [
    ("flat48",   "pge_grid_flat48_noN.nc", "ini_flat48_13.nc",  None),
    ("mit",      "pge_grid_mit.nc",        "ini_mit.nc",        None),
    ("r26steep", "pge_grid_r26steep.nc",   "ini_r26steep13.nc", "truth"),
]
VISCS = [0.0, 20.0, 100.0, 300.0, 1000.0]

IT = iters("U", MIT)
U_TRUTH = read_field("U", IT[-1], MIT)


def setup(tag, grid, ini, visc):
    rd = f"{ENV}/runs/cs_{tag}_{visc:g}".replace(".", "p")
    os.makedirs(rd, exist_ok=True)
    for src, dst in ((f"{SRC}/{grid}", grid), (f"{SRC}/{ini}", ini),
                     (f"{ENV}/bin/coawstM_goai_clean", "coawstM_goai_clean")):
        if not os.path.exists(f"{rd}/{dst}"):
            shutil.copy2(src, f"{rd}/{dst}")
    os.chmod(f"{rd}/coawstM_goai_clean", 0o755)
    out = []
    for line in open(f"{BASE}/ocean_r26_dj10.in", errors="replace"):
        if re.match(r"^\s*VISC2\s*==", line):
            line = f"       VISC2 == {visc}d0\n"
        elif re.match(r"^\s*GRDNAME\s*==", line):
            line = f"     GRDNAME == {grid}\n"
        elif re.match(r"^\s*ININAME\s*==", line):
            line = f"     ININAME == {ini}\n"
        elif re.match(r"^\s*NHIS\s*==", line):
            line = "        NHIS ==  4320\n"
        elif re.match(r"^\s*(HISNAME|RSTNAME|AVGNAME|DIANAME)\s*==", line):
            k = line.split()[0]
            line = f"     {k} == out_{k[:3].lower()}.nc\n"
        out.append(line)
    open(f"{rd}/roms.in", "w").writelines(out)
    return rd


def metrics(rd, has_truth):
    d = Dataset(f"{rd}/out_his.nc")
    u = np.asarray(d["u"][-1]); T = np.asarray(d["temp"][-1])
    T0 = np.asarray(d["temp"][0]); h = np.asarray(d["h"][:])
    Cs = np.asarray(d["Cs_r"][:])
    d.close()
    hu = 0.5 * (h[:, :-1] + h[:, 1:])
    depth = -Cs[:, None, None] * hu[None, :, :]
    deep = depth > 800.0
    over = np.clip(T - T0.max(), 0, None) + np.clip(T0.min() - T, 0, None)
    m = dict(u_max=float(np.abs(u).max() * 100),
             u_rms=float(np.sqrt((u ** 2).mean()) * 100),
             deep_rms=float(np.sqrt((u[deep] ** 2).mean()) * 100) if deep.any() else np.nan,
             surf_max=float(np.abs(u[-1]).max() * 100),
             temp_over_max=float(over.max()),
             temp_over_mean=float(over.mean()))
    if has_truth:
        n = min(u.shape[-1], U_TRUTH.shape[-1])
        err = u[..., :n] - U_TRUTH[..., :n]
        m["err_rms"] = float(np.sqrt((err ** 2).mean()) * 100)
        m["err_max"] = float(np.abs(err).max() * 100)
    return m


def one(job):
    tag, grid, ini, truth, visc = job
    rd = setup(tag, grid, ini, visc)
    env = dict(os.environ, PATH="/usr/bin:" + os.environ.get("PATH", ""),
               LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:" +
                               os.environ.get("LD_LIBRARY_PATH", ""))
    t0 = time.time()
    with open(f"{rd}/run.log", "w") as lg:
        subprocess.run(["./coawstM_goai_clean", "roms.in"], cwd=rd, stdout=lg,
                       stderr=subprocess.STDOUT, env=env)
    txt = open(f"{rd}/run.log", errors="replace").read()
    ok = "ROMS/TOMS: DONE" in txt and "BLOWUP" not in txt
    r = dict(config=tag, VISC2=visc, ok=ok, wall_s=round(time.time() - t0, 1))
    if ok:
        r.update(metrics(rd, truth == "truth"))
    return r


if __name__ == "__main__":
    jobs = [(t, g, i, tr, v) for (t, g, i, tr) in CONFIGS for v in VISCS]
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=15) as ex:
        res = list(ex.map(one, jobs))
    json.dump(res, open(f"{ENV}/ledger/config_sweep.json", "w"),
              ensure_ascii=False, indent=1)

    print(f"总耗时 {time.time()-t0:.0f}s   ({len(jobs)} run, 48×48×13 × 3 天)\n")
    NA = float("nan")
    for tag, _, _, tr in CONFIGS:
        rows = [r for r in res if r["config"] == tag]
        note = "  ← 平底，σ-PGE≡0（对照组）" if tag == "flat48" else \
               ("  ← 有 MITgcm 真值" if tr == "truth" else "")
        print(f"■ {tag}{note}")
        hdr = (f"{'VISC2':>7} | {'|U|max':>8} {'|U|rms':>8} {'深层rms':>8} "
               f"{'表层max':>8} | {'T超调max':>9}" + ("  {:>9} {:>9}".format('误差rms','误差max') if tr else ""))
        print(hdr); print("  " + "-" * (len(hdr) - 2))
        for r in rows:
            if not r["ok"]:
                print(f"{r['VISC2']:>7.0f} |  未完赛"); continue
            line = (f"{r['VISC2']:>7.0f} | {r['u_max']:>8.2f} {r['u_rms']:>8.3f} "
                    f"{r['deep_rms']:>8.3f} {r['surf_max']:>8.2f} | {r['temp_over_max']:>9.4f}")
            if tr:
                line += f"  {r.get('err_rms',NA):>9.3f} {r.get('err_max',NA):>9.2f}"
            print(line)
        ok = [r for r in rows if r["ok"]]
        if ok:
            print("   各指标推荐最优 VISC2：", end="")
            for k, lab in (("deep_rms", "深层伪流"), ("temp_over_max", "温度超调"),
                           ("u_rms", "|U|rms"), ("err_rms", "⭐误差")):
                vals = [r.get(k, np.nan) for r in ok]
                if all(np.isnan(v) for v in vals):
                    continue
                j = int(np.nanargmin(vals))
                print(f" {lab}→{ok[j]['VISC2']:g}", end="")
            print()
        print()
