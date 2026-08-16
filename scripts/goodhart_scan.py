#!/usr/bin/env python
"""Goodhart 扫描：黏性 VISC2 对「代理指标」与「真目标」的相反作用。

代理（全行业在优化）: 静止陡地形算例的伪流强度  —— 越低越好
真目标（真正在乎的）: 内波算例的物理保真          —— κ_v=0，方差损失即纯数值混合

不预设结论：同时测多个真指标，看实际曲线。
"""
import os, re, sys, json, time, subprocess
import concurrent.futures as cf
import numpy as np
from netCDF4 import Dataset
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagnostics import _rho_uv

ENV = "/data/xinyuan/GOAI_ai4s_env"
BIN = f"{ENV}/bin/coawstM_goai"
CS = f"{ENV}/cases/seamount"
CI = f"{ENV}/cases/internal_wave"
VARINFO = f"{CS}/external/varinfo.dat"

VISCS = [0.0, 1.0, 5.0, 20.0, 50.0, 100.0, 200.0, 500.0]
NT_SEA, NT_IW = 2880, 5760          # 海山 1 天；内波 10 天


def write_in(template, rundir, subs, ntimes, grid):
    os.makedirs(rundir, exist_ok=True)
    out = []
    for line in open(template, errors="replace"):
        if re.match(r"^\s*VARNAME\s*=", line):
            line = f"     VARNAME = {VARINFO}\n"
        elif re.match(r"^\s*GRDNAME\s*==", line):
            line = f"     GRDNAME == {grid}\n"
        elif re.match(r"^\s*(RSTNAME|HISNAME|AVGNAME|DIANAME|QCKNAME)\s*==", line):
            k = line.split()[0]
            line = f"     {k} == roms_{k[:3].lower()}.nc\n"
        elif re.match(r"^\s*NTIMES\s*==", line):
            line = f"      NTIMES == {ntimes}\n"
        else:
            for k, v in subs.items():
                if re.match(rf"^\s*{k}\s*==", line):
                    line = re.sub(r"==\s*\S+", f"== {v}", line, count=1)
                    break
        out.append(line)
    open(f"{rundir}/roms.in", "w").writelines(out)


def run(rundir):
    env = dict(os.environ, PATH="/usr/bin:" + os.environ.get("PATH", ""))
    t0 = time.time()
    with open(f"{rundir}/run.log", "w") as lg:
        subprocess.run([BIN, "roms.in"], cwd=rundir, stdout=lg,
                       stderr=subprocess.STDOUT, env=env)
    txt = open(f"{rundir}/run.log", errors="replace").read()
    return dict(wall=time.time() - t0,
                done="ROMS/TOMS: DONE" in txt,
                blowup="BLOWUP" in txt)


def volwt(fn):
    """体积加权工具：返回 (T, Hz, dV) 末帧 + 方差时间序列。"""
    d = Dataset(fn)
    T = np.asarray(d.variables["temp"][:])          # (t,N,eta,xi)
    zw = np.asarray(d.variables["z_w"][:])
    pm = np.asarray(d.variables["pm"][:]); pn = np.asarray(d.variables["pn"][:])
    u = np.asarray(d.variables["u"][:]); v = np.asarray(d.variables["v"][:])
    d.close()
    Hz = np.diff(zw, axis=1)
    area = 1.0 / (pm * pn)
    dV = Hz * area[None, None, :, :]
    vol = dV.sum(axis=(1, 2, 3))
    Tm = (T * dV).sum(axis=(1, 2, 3)) / vol
    var = ((T - Tm[:, None, None, None]) ** 2 * dV).sum(axis=(1, 2, 3)) / vol
    keu = 0.5 * (u ** 2).mean(axis=(1, 2, 3)) + 0.5 * (v ** 2).mean(axis=(1, 2, 3))
    return var, keu, T


def seamount_proxy(rundir):
    """代理指标：静止态伪流（真值恒等于 0）。u/v 先插值到 rho 点。"""
    var, ke, T = volwt(f"{rundir}/roms_his.nc")
    d = Dataset(f"{rundir}/roms_his.nc")
    u = np.asarray(d.variables["u"][-1]); v = np.asarray(d.variables["v"][-1])
    zw = np.asarray(d.variables["z_w"][-1])
    pm = np.asarray(d.variables["pm"][:]); pn = np.asarray(d.variables["pn"][:])
    d.close()
    ur, vr = _rho_uv(u, v)
    spd = np.sqrt(ur ** 2 + vr ** 2)
    dV = np.diff(zw, axis=0) * (1.0 / (pm * pn))[None, :, :]
    rms_vol = float(np.sqrt((spd ** 2 * dV).sum() / dV.sum()) * 100)
    return {"spurious_max_cms": float(spd.max() * 100),
            "spurious_rms_volwt_cms": rms_vol,
            "spurious_ke_mean": float(ke[-1]),
            "temp_range": [float(T[-1].min()), float(T[-1].max())]}


def iw_true(rundir):
    """真目标：内波算例的物理保真（κ_v=0 → 方差损失＝纯数值混合）。"""
    var, ke, T = volwt(f"{rundir}/roms_his.nc")
    return {"variance_retained": float(var[-1] / var[0]),
            "numerical_mixing": float(1 - var[-1] / var[0]),
            "wave_KE_final": float(ke[-1]),
            "wave_KE_retained": float(ke[-1] / max(ke[1], 1e-30)),
            "temp_range": [float(T[-1].min()), float(T[-1].max())]}


def one(visc):
    tag = f"v{visc:g}".replace(".", "p")
    subs = {"VISC2": f"{visc}d0"}
    rs, ri = f"{ENV}/runs/gh_sea_{tag}", f"{ENV}/runs/gh_iw_{tag}"
    write_in(f"{CS}/roms_real.in.template", rs, subs, NT_SEA,
             f"{CS}/grids/grid_rx0p60.nc")
    write_in(f"{CI}/iw.in.template", ri, subs, NT_IW,
             f"{CI}/grids/grid_iw.nc")
    ms, mi = run(rs), run(ri)
    rec = {"VISC2": visc, "sea_ok": ms["done"] and not ms["blowup"],
           "iw_ok": mi["done"] and not mi["blowup"],
           "wall_s": round(ms["wall"] + mi["wall"], 1)}
    if rec["sea_ok"]:
        rec["proxy"] = seamount_proxy(rs)
    if rec["iw_ok"]:
        rec["true"] = iw_true(ri)
    return rec


if __name__ == "__main__":
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(one, VISCS))
    json.dump(res, open(f"{ENV}/ledger/goodhart_scan.json", "w"),
              ensure_ascii=False, indent=1)

    print(f"总耗时 {time.time()-t0:.0f}s   ({len(VISCS)} 组 × 2 算例)\n")
    print("VISC2   |   代理: 伪流max  伪流体积rms  |   真: 保留方差  数值混合  波KE保留")
    print("-" * 78)
    NA = float('nan')
    for r in res:
        p = r.get("proxy", {}); t = r.get("true", {})
        print(f"{r['VISC2']:>6.0f}  | {p.get('spurious_max_cms', NA):>12.2f}"
              f" {p.get('spurious_rms_volwt_cms', NA):>9.2f}  |"
              f" {t.get('variance_retained', float('nan')):>11.4f}"
              f" {t.get('numerical_mixing', float('nan')):>9.4f}"
              f" {t.get('wave_KE_retained', float('nan')):>10.4f}"
              + ("" if (r["sea_ok"] and r["iw_ok"]) else "   ⚠未完赛"))
