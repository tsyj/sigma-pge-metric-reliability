#!/usr/bin/env python
"""E28 主分析：误差占比的崩塌，取决于拧哪个旋钮吗？

把 ROMS 四旋钮扫描（knob_sweep.json）与同参数的 MITgcm 真值扫描
（truth_sweeps.json）配对，对每个旋钮算两条曲线：

    代理降幅   = 1 − 代理指标(v) / 代理指标(默认值)
    误差占比   = |ROMS(v) − 真值(v)| / ROMS(v)

如果四条「误差占比 vs 代理降幅」曲线重合 → 崩塌是普遍规律，与旋钮无关。
如果分离 → **选哪个旋钮压 σ-PGE，决定了你的诊断指标还剩多少诊断力**，
这是一条可执行的建模建议，而不只是一句警告。
"""
import json, sys, os
import numpy as np

E = "/data/xinyuan/GOAI_ai4s_env"
# ROMS 旋钮 → MITgcm 参数 → ROMS 侧默认值
PAIR = {"VISC2": ("viscAh", 50.0),
        "VISC4": ("viscA4", 0.0),
        "AKV_BAK": ("viscAz", 1e-5),
        "TNU2": ("diffKhT", 50.0)}
NAME = {"VISC2": "横向黏性 VISC2", "VISC4": "双谐波黏性 VISC4",
        "AKV_BAK": "垂向黏性 AKV_BAK", "TNU2": "示踪扩散 TNU2"}


def load():
    ks = json.load(open(f"{E}/ledger/knob_sweep.json"))
    tr = json.load(open(f"{E}/ledger/truth_sweeps.json"))
    R = {}
    for r in ks:
        if r["obs"].get("valid"):
            R.setdefault((r["knob"], r["bathy"]), {})[r["val"]] = r["obs"]
    T = {}
    for p, rows in tr.items():
        T[p] = {r["val"]: r for r in rows}
    return R, T


def nearest(d, v):
    return d[min(d, key=lambda z: abs(z - v))]


def main():
    R, T = load()
    print("=" * 90)
    print("误差占比 = |ROMS − 真值| / ROMS   随代理指标被压低的变化")
    print("=" * 90)

    summary = {}
    for metric, mt, lab in (("u_max", "umax", "全域最大流速 |U|max"),
                            ("deep_rms_800", "deep", "深层 rms (>800 m)")):
        print(f"\n{'━'*90}\n指标：{lab}\n{'━'*90}")
        for knob, (mp, dflt) in PAIR.items():
            d = R.get((knob, "r26steep"))
            if not d or mp not in T:
                print(f"  {knob}: 数据不全，跳过"); continue
            base = nearest(d, dflt)[metric]
            print(f"\n■ {NAME[knob]}   （ROMS 默认 {dflt:g}，此处代理={base:.3f}）")
            print(f"{'参数值':>10} {'ROMS':>9} {'真值':>10} {'代理降幅':>9} "
                  f"{'误差占比':>9} {'真信号变动':>10}")
            print("-" * 66)
            tb = nearest(T[mp], dflt)["urms"]
            rows = []
            for v in sorted(d):
                rv = d[v][metric]
                tv = nearest(T[mp], v)[mt]
                tu = nearest(T[mp], v)["urms"]
                drop = 1 - rv / base
                frac = abs(rv - tv) / max(abs(rv), 1e-12)
                dmg = abs(tu - tb) / max(tb, 1e-12)
                rows.append((v, rv, tv, drop, frac, dmg))
                print(f"{v:>10g} {rv:>9.3f} {tv:>10.5f} {drop:>8.1%} "
                      f"{frac:>8.1%} {dmg:>9.2%}")
            summary.setdefault(metric, {})[knob] = rows

    # ---------- 关键对比：把代理压低同样幅度时，各旋钮还剩多少诊断力 ----------
    print(f"\n{'='*90}")
    print("关键对比：把代理指标压低 ~50% 时，各旋钮的表现")
    print("=" * 90)
    for metric, lab in (("u_max", "全域最大流速"), ("deep_rms_800", "深层 rms")):
        print(f"\n■ {lab}")
        print(f"{'旋钮':>16} {'达成降幅':>9} {'误差占比':>9} {'真信号破坏':>11} {'判定':>16}")
        print("-" * 68)
        for knob in PAIR:
            rows = summary.get(metric, {}).get(knob)
            if not rows:
                continue
            cand = [r for r in rows if r[3] >= 0.45]
            if not cand:
                best = max(rows, key=lambda r: r[3])
                print(f"{NAME[knob]:>16} {best[3]:>8.1%} {best[4]:>8.1%} "
                      f"{best[5]:>10.2%} {'（压不到50%）':>16}")
                continue
            r = min(cand, key=lambda r: r[3])
            v = ("✅ 仍纯误差" if r[4] >= 0.95 else
                 "⚠ 混入真信号" if r[4] >= 0.5 else "❌ 主要是真信号")
            print(f"{NAME[knob]:>16} {r[3]:>8.1%} {r[4]:>8.1%} {r[5]:>10.2%} {v:>16}")

    json.dump({m: {k: [list(x) for x in v] for k, v in d.items()}
               for m, d in summary.items()},
              open(f"{E}/ledger/knob_analysis.json", "w"),
              ensure_ascii=False, indent=1)
    print(f"\n→ ledger/knob_analysis.json")


if __name__ == "__main__":
    main()
