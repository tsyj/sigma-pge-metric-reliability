#!/usr/bin/env python
"""用修正后的评估器重算 ledger 全部 run 的隐藏分数。

修了三处（E29 #6/#7、E35 #8）：
  #6 真值按 AKV_BAK 匹配垂向黏性（原来固定用 viscAz=1e-3）
  #7 真值按实际积分时长取时刻（原来写死第 3 天）
  #8 ROMS 逐列插到 MITgcm 的 z 层再比（原来直接相减，而两者层序**相反**）
并新增技巧评分 SS = 1 − (err_rms / truth_rms)²，以「恒输出零」为 0 分基准（E34）。

结果写 `ledger/regraded_v2.jsonl`，**不动原 ledger**（撤回要可查）。
"""
import json, os, sys
import numpy as np
import netCDF4 as nc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import _truth, _rc_truth, DT_ROMS, ENV, LEDGER
from sigma2z import roms_depths, to_z, rho_from_u


def grade_run(rid, ntimes, akv):
    fn = f"{ENV}/runs/{rid}/out_his.nc"
    if not os.path.exists(fn):
        return None
    day = round(ntimes * DT_ROMS / 86400.0, 3)
    U = _truth(day, akv)
    if U is None:
        return None
    d = nc.Dataset(fn)
    u = np.asarray(d["u"][-1]); Cs = np.asarray(d["Cs_r"][:])
    h = np.asarray(d["h"][:]); d.close()
    uz = to_z(rho_from_u(u), roms_depths(Cs, h), _rc_truth())
    m = min(uz.shape[-2], U.shape[-2]); n = min(uz.shape[-1], U.shape[-1])
    A, B = uz[:, :m, :n], U[:, :m, :n]
    g = np.isfinite(A) & np.isfinite(B)
    err = A[g] - B[g]
    er = float(np.sqrt((err ** 2).mean()) * 100)
    tr = float(np.sqrt((B[g] ** 2).mean()) * 100)
    return dict(truth_day=day, truth_akv=akv, err_rms=er, err_max=float(np.abs(err).max() * 100),
                truth_rms=tr, skill_vs_zero=1.0 - (er / max(tr, 1e-12)) ** 2)


def main():
    out, seen = [], set()
    for line in open(LEDGER):
        r = json.loads(line)
        if r["bathy"] != "r26steep" or not r["obs"].get("valid"):
            continue
        if r["run_id"] in seen:
            continue
        seen.add(r["run_id"])
        g = grade_run(r["run_id"], r["ntimes"], r["action"].get("AKV_BAK", 1e-5))
        if g is None:
            continue
        out.append(dict(run_id=r["run_id"], action=r["action"], ntimes=r["ntimes"],
                        deep_rms_800=r["obs"].get("deep_rms_800"),
                        u_max=r["obs"].get("u_max"),
                        old_err_rms=(r.get("hidden") or {}).get("err_rms_vs_truth"), **g))

    with open(f"{ENV}/ledger/regraded_v2.jsonl", "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"重算 {len(out)} 条 → ledger/regraded_v2.jsonl\n")

    # 只动 VISC2 的那批
    v = {}
    for r in out:
        if set(r["action"]) <= {"bathy", "VISC2", "ntimes", "seed"}:
            v.setdefault(r["ntimes"], {})[round(r["action"].get("VISC2", 0.0), 1)] = r

    for nt in sorted(v):
        sub = v[nt]
        if len(sub) < 4:
            continue
        day = next(iter(sub.values()))["truth_day"]
        tr = next(iter(sub.values()))["truth_rms"]
        print("=" * 84)
        print(f"VISC2 扫描（ntimes={nt} → 第 {day:g} 天；真值 rms = {tr:.3f}）")
        print("=" * 84)
        print(f"{'VISC2':>9} {'旧err_rms':>10} {'新err_rms':>10} {'技巧评分':>10} "
              f"{'深层rms':>9} {'|U|max':>9}")
        print("-" * 84)
        for k in sorted(sub):
            r = sub[k]
            o = r["old_err_rms"]
            print(f"{k:>9g} {(o if o is not None else float('nan')):>10.3f} "
                  f"{r['err_rms']:>10.3f} {r['skill_vs_zero']:>10.3f} "
                  f"{r['deep_rms_800']:>9.4f} {r['u_max']:>9.3f}")
        best_s = max(sub.values(), key=lambda r: r["skill_vs_zero"])
        best_d = min(sub.values(), key=lambda r: r["deep_rms_800"])
        print("-" * 84)
        print(f"  技巧评分最高：VISC2={best_s['action'].get('VISC2',0):g}  "
              f"SS={best_s['skill_vs_zero']:.3f}")
        print(f"  深层 rms 最低：VISC2={best_d['action'].get('VISC2',0):g}  "
              f"深层={best_d['deep_rms_800']:.4f}（SS={best_d['skill_vs_zero']:.3f}）")
        pos = [r for r in sub.values() if r["skill_vs_zero"] > 0]
        print(f"  技巧评分为正的配置：{len(pos)}/{len(sub)}"
              + ("  ⚠ **没有任何配置好过「恒输出零」**" if not pos else ""))
        print()


if __name__ == "__main__":
    main()
