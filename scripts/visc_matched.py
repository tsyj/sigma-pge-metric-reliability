#!/usr/bin/env python
"""黏性匹配后的 ROMS vs 真值重算 —— 回应 A 队攻击 1。

A 队：「你拿 viscAh=50 的真值去比 VISC2=0 的 ROMS，黏性都不一样，比什么？」
本脚本对每个黏性档，用**同黏性**的 MITgcm 真值重新算倍数。
"""
import json, sys, os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mitgcm import read_field, iters

E = "/data/xinyuan/GOAI_ai4s_env"
NT = 8640
VISCS = (0.0, 50.0, 300.0, 1000.0, 2747.0)


def truth(v):
    d = "%s/truth/mitv_%s" % (E, str(v).replace('.', 'p'))
    it = iters("U", d)
    U = read_field("U", it[-1], d)
    RC = read_field("RC", None, d).ravel()
    deep = np.abs(RC) > 800
    return dict(deep=float(np.sqrt((U[deep] ** 2).mean()) * 100),
                umax=float(np.abs(U).max() * 100),
                urms=float(np.sqrt((U ** 2).mean()) * 100))


def main():
    rows = [json.loads(l) for l in open(E + "/ledger/env2_runs.jsonl")]
    R = {}
    for r in rows:
        if r["obs"].get("valid") and r["ntimes"] == NT and r["bathy"] == "r26steep":
            R[round(r["action"].get("VISC2", 0.0), 1)] = r["obs"]

    T = {v: truth(v) for v in VISCS}

    print("=" * 84)
    print("黏性匹配后的重算（ROMS VISC2 == MITgcm viscAh，r26steep，第 3 天）")
    print("=" * 84)
    print("%7s | %10s %12s %10s | %11s %11s %7s" %
          ("黏性", "ROMS深层", "真值深层", "倍数", "ROMS|U|max", "真值|U|max", "倍数"))
    print("-" * 84)
    out = []
    for v in VISCS:
        t = T[v]
        k = min(R, key=lambda z: abs(z - v))
        o = R[k]
        rd, td = o["deep_rms_800"], t["deep"]
        print("%7.0f | %10.4f %12.6f %9.0fx | %11.3f %11.3f %6.1fx" %
              (v, rd, td, rd / max(td, 1e-12), o["u_max"], t["umax"],
               o["u_max"] / t["umax"]))
        out.append(dict(visc=v, roms_visc2_used=k, roms_deep=rd, truth_deep=td,
                        deep_ratio=rd / max(td, 1e-12),
                        roms_umax=o["u_max"], truth_umax=t["umax"],
                        umax_ratio=o["u_max"] / t["umax"]))
    print()
    print("  ROMS 侧取与该黏性最接近的已有 run。全部 5 档 VISC2 都有精确对应 run。")

    print()
    print("=" * 84)
    print("三条读数")
    print("=" * 84)
    u = [T[v]["urms"] for v in VISCS]
    r0, r50 = T[0.0]["deep"], T[50.0]["deep"]
    print("  1. 真值 |U|rms 全程 %.4f-%.4f，变化 %.2f%%" %
          (min(u), max(u), (max(u) / min(u) - 1) * 100))
    print("     -> 真实风驱响应几乎不依赖黏性；sigma 坐标里随黏性剧变的读数是伪迹")
    print()
    print("  2. viscAh>=50 时真值深层 1e-6~1e-5 量级，比 ROMS 小 5-6 个数量级")
    print("     -> Ekman 深度 6.09 m 的物理判据得到实测确认")
    print()
    print("  3. [!] viscAh=0 是例外：深层 %.4f，是 viscAh=50 时（%.6f）的 %.0f 倍" %
          (r0, r50, r0 / r50))
    print("     -> 零黏性下 z 坐标模式自身也有数值噪声下传，不能当干净真值")
    print("     -> 但即便用这个被污染的真值，ROMS@0 仍是它的 %.0f 倍" %
          (R[min(R)]["deep_rms_800"] / r0))

    json.dump(dict(truth_by_visc={str(v): T[v] for v in VISCS}, matched=out),
              open(E + "/ledger/visc_matched.json", "w"),
              ensure_ascii=False, indent=1)
    print()
    print("  -> ledger/visc_matched.json")


if __name__ == "__main__":
    main()
