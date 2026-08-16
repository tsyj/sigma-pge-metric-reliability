#!/usr/bin/env python
"""E34：隐藏评估器自己的退化最优 —— 以及修好它的技巧评分。

发现（本项目最重要的一条自我否定）：
    隐藏评估器用 err_rms = rms(ROMS − 真值)。
    它的下限是**一个恒输出零的模型**：rms(0 − 真值) = rms(真值) = 2.560。
    默认配置 7.473，比「什么都不产生」差 +4.913。
    把 VISC2 拧到 30000（物理荒谬）得 2.901 —— 只是在向那个下限靠近。

    **接上真值挡住了「代理指标失效」，但没挡住「用消灭一切来降低误差」。**

修法：技巧评分（气象/海洋预报的标准做法）

    SS = 1 − MSE(模型, 真值) / MSE(零, 真值)
       = 1 − (err_rms / truth_rms)²

    SS = 1   完美
    SS = 0   **与「什么都不输出」持平** —— 这才是及格线
    SS < 0   比什么都不做还差

一并给出误差的两个分量，区分「造出不存在的流」与「漏掉真实的流」：
    过量 = rms(max(|ROMS| − |真值|, 0))     伪流
    缺失 = rms(max(|真值| − |ROMS|, 0))     被阻尼掉的真信号
"""
import json, os, sys
import numpy as np
import netCDF4 as nc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import _truth, DT_ROMS, ENV, LEDGER


def _rho_u(u):
    return u


def main():
    rows = []
    seen = set()
    for line in open(LEDGER):
        r = json.loads(line)
        if r["bathy"] != "r26steep" or not r["obs"].get("valid"):
            continue
        if set(r["action"]) - {"bathy", "VISC2", "ntimes", "seed"}:
            continue
        key = (r["ntimes"], round(r["action"].get("VISC2", 0.0), 3))
        if key in seen:
            continue
        fn = f"{ENV}/runs/{r['run_id']}/out_his.nc"
        if not os.path.exists(fn):
            continue
        day = round(r["ntimes"] * DT_ROMS / 86400.0, 3)
        U = _truth(day, r["action"].get("AKV_BAK", 1e-5))
        if U is None:
            continue
        seen.add(key)
        d = nc.Dataset(fn); u = np.asarray(d["u"][-1]); d.close()
        n = min(u.shape[-1], U.shape[-1])
        a, b = u[..., :n], U[..., :n]
        err = a - b
        err_rms = float(np.sqrt((err ** 2).mean()) * 100)
        t_rms = float(np.sqrt((b ** 2).mean()) * 100)
        excess = float(np.sqrt((np.clip(np.abs(a) - np.abs(b), 0, None) ** 2).mean()) * 100)
        missing = float(np.sqrt((np.clip(np.abs(b) - np.abs(a), 0, None) ** 2).mean()) * 100)
        rows.append(dict(visc=r["action"].get("VISC2", 0.0), ntimes=r["ntimes"],
                         day=day, err_rms=err_rms, truth_rms=t_rms,
                         skill=1.0 - (err_rms / t_rms) ** 2,
                         excess=excess, missing=missing,
                         deep=r["obs"]["deep_rms_800"], umax=r["obs"]["u_max"]))

    rows.sort(key=lambda r: (r["ntimes"], r["visc"]))
    for nt in sorted({r["ntimes"] for r in rows}):
        sub = [r for r in rows if r["ntimes"] == nt]
        if len(sub) < 3:
            continue
        print("=" * 92)
        print(f"技巧评分（ntimes={nt} → 第 {sub[0]['day']:g} 天，真值 rms = {sub[0]['truth_rms']:.3f}）")
        print("=" * 92)
        print(f"{'VISC2':>9} {'err_rms':>9} {'技巧评分':>10} {'过量(伪流)':>11} "
              f"{'缺失(真信号)':>13} {'深层rms':>9}")
        print("-" * 92)
        for r in sub:
            print(f"{r['visc']:>9g} {r['err_rms']:>9.3f} {r['skill']:>10.3f} "
                  f"{r['excess']:>11.3f} {r['missing']:>13.3f} {r['deep']:>9.4f}")
        print("-" * 92)
        print(f"  「什么都不输出」的技巧评分 = 0.000（err_rms = {sub[0]['truth_rms']:.3f}）")
        best = max(sub, key=lambda r: r["skill"])
        pos = [r for r in sub if r["skill"] > 0]
        print(f"  最好的配置：VISC2={best['visc']:g}，技巧评分 {best['skill']:.3f}")
        if not pos:
            print(f"  ⚠ **没有任何配置的技巧评分为正** —— "
                  f"在这个算例上，σ 坐标模式的任何黏性设置都不如直接预报零")
        print()

    json.dump(rows, open(f"{ENV}/ledger/skill_score.json", "w"),
              ensure_ascii=False, indent=1)
    print("→ ledger/skill_score.json")


if __name__ == "__main__":
    main()
