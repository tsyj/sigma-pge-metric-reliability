#!/usr/bin/env python
"""同一批 run 上，多个"看起来都像真目标"的指标是否给出一致建议？

用真值扫描的 6 个 run（48×48×13，与 MITgcm 同配置），
同时算：① 对真值的误差 ② 温度超调 ③ 深层伪流 ④ 表层流
看它们各自推荐的最优 VISC2 是否一致。
"""
import os, sys, json
import numpy as np
from netCDF4 import Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mitgcm import read_field, iters

ENV = "/data/xinyuan/GOAI_ai4s_env"
MIT = "/data/xinyuan/zpg_roms_dev/MITgcm/verification/seamount_roms/run_r29_wind_z13"
VISCS = [0.0, 5.0, 20.0, 50.0, 200.0, 1000.0]

IT = iters("U", MIT)
U_TRUTH = read_field("U", IT[-1], MIT)          # 末帧（第 3 天）
T_TRUTH = read_field("T", IT[-1], MIT)
T_TRUTH0 = read_field("T", IT[0], MIT)

rows = []
for v in VISCS:
    rd = f"{ENV}/runs/tv_{v:g}".replace(".", "p")
    fn = f"{rd}/out_his.nc"
    if not os.path.exists(fn):
        continue
    d = Dataset(fn)
    u = np.asarray(d["u"][-1]); T = np.asarray(d["temp"][-1])
    T0 = np.asarray(d["temp"][0]); h = np.asarray(d["h"][:])
    Cs = np.asarray(d["Cs_r"][:])
    d.close()

    n = min(u.shape[-1], U_TRUTH.shape[-1])
    err = u[..., :n] - U_TRUTH[..., :n]

    hu = 0.5 * (h[:, :-1] + h[:, 1:])
    depth = -Cs[:, None, None] * hu[None, :, :]
    deep = depth > 800.0

    over = np.clip(T - T0.max(), 0, None) + np.clip(T0.min() - T, 0, None)
    # 真值侧的温度超调（作对照）
    overT = (np.clip(T_TRUTH - T_TRUTH0.max(), 0, None)
             + np.clip(T_TRUTH0.min() - T_TRUTH, 0, None))

    rows.append(dict(
        visc=v,
        err_rms=float(np.sqrt((err ** 2).mean()) * 100),          # ⭐ 对真值的误差
        err_max=float(np.abs(err).max() * 100),
        temp_over_max=float(over.max()),                           # 温度超调
        temp_over_mean=float(over.mean()),
        deep_rms=float(np.sqrt((u[deep] ** 2).mean()) * 100) if deep.any() else np.nan,
        surf_max=float(np.abs(u[-1]).max() * 100),
        roms_max=float(np.abs(u).max() * 100),
    ))

json.dump(rows, open(f"{ENV}/ledger/diag_disagree.json", "w"),
          ensure_ascii=False, indent=1)

print("同一批 run（48×48×13，与 MITgcm 同配置，第 3 天末帧）")
print(f"真值：|U|max={np.abs(U_TRUTH).max()*100:.2f} cm/s  "
      f"rms={np.sqrt((U_TRUTH**2).mean())*100:.2f} cm/s  "
      f"温度超调max={overT.max():.3f} °C\n")
hdr = (f"{'VISC2':>7} | {'⭐误差rms':>9} {'误差max':>8} | {'T超调max':>9} "
       f"{'T超调mean':>10} | {'深层rms':>8} {'表层max':>8}")
print(hdr); print("-" * len(hdr))
for r in rows:
    print(f"{r['visc']:>7.0f} | {r['err_rms']:>9.3f} {r['err_max']:>8.2f} |"
          f" {r['temp_over_max']:>9.3f} {r['temp_over_mean']:>10.4f} |"
          f" {r['deep_rms']:>8.3f} {r['surf_max']:>8.2f}")

print("\n各指标各自推荐的最优 VISC2：")
for key, lab, lo in (("err_rms", "⭐ 对真值的误差 rms", True),
                     ("err_max", "对真值的误差 max", True),
                     ("temp_over_max", "温度超调 max", True),
                     ("temp_over_mean", "温度超调 mean", True),
                     ("deep_rms", "深层伪流 rms", True)):
    vals = [r[key] for r in rows]
    k = int(np.nanargmin(vals))
    print(f"  {lab:22s} → VISC2 = {rows[k]['visc']:>6.0f}   (值 {vals[k]:.4f})")
