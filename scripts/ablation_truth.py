#!/usr/bin/env python
"""指标消融 v2 —— 有了三配置真值，改用**直接归因**。

v1 用平底当替身（相对/绝对变化），v2 直接问：
    该指标的读数里，有多少是误差、有多少是真信号？

误差占比 = |ROMS读数 − 真值读数| / ROMS读数
  → 接近 1：几乎全是误差，可用于诊断
  → 明显 < 1：混入真信号，无法归因
"""
import json, sys, os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mitgcm import read_field, iters

E = "/data/xinyuan/GOAI_ai4s_env"
NT = 8640
BATHY = ("flat", "mit", "r26steep")
CAND = [("u_max", "全域最大流速"), ("u_rms", "全域 rms"),
        ("surf_max", "表层最大流速"), ("deep_rms_200", "深层 rms >200m"),
        ("deep_rms_800", "深层 rms >800m"), ("deep_rms_1500", "深层 rms >1500m")]


def truth_metrics(tag):
    d = f"{E}/truth/mit_{tag}"
    it = iters("U", d)
    U = read_field("U", it[-1], d)
    RC = read_field("RC", None, d).ravel()
    m = {"u_max": float(np.abs(U).max() * 100),
         "u_rms": float(np.sqrt((U ** 2).mean()) * 100),
         "surf_max": float(np.abs(U[0]).max() * 100)}   # MITgcm k=0 是表层
    for thr in (200, 400, 800, 1500):
        sel = np.abs(RC) > thr
        m[f"deep_rms_{thr}"] = (float(np.sqrt((U[sel] ** 2).mean()) * 100)
                                if sel.any() else 0.0)
    return m


def roms_at(D, tag, visc):
    d = D.get(tag, {})
    if not d:
        return None
    x = min(d, key=lambda z: abs(z - visc))
    return d[x]["obs"], x


def main():
    rows = [json.loads(l) for l in open(f"{E}/ledger/env2_runs.jsonl")]
    D = {}
    for r in rows:
        if r["obs"].get("valid") and r["ntimes"] == NT:
            D.setdefault(r["bathy"], {})[round(r["action"].get("VISC2", 0.0), 1)] = r
    T = {b: truth_metrics(b) for b in BATHY}

    print("=" * 86)
    print("真值读数（MITgcm z 坐标，第 3 天）")
    print("=" * 86)
    print(f"{'指标':>16} " + " ".join(f"{b:>12}" for b in BATHY))
    print("-" * 86)
    for k, lab in CAND:
        print(f"{lab:>16} " + " ".join(f"{T[b][k]:>12.4f}" for b in BATHY))

    print()
    print("=" * 86)
    print("误差占比 = |ROMS − 真值| / ROMS   （越接近 1 越纯，越小说明混入真信号）")
    print("=" * 86)
    for visc in (0.0, 2747.0):
        print(f"\n■ VISC2 ≈ {visc:g}")
        print(f"{'指标':>16} " + " ".join(f"{b:>16}" for b in BATHY) + f"{'判定':>14}")
        print("-" * 86)
        for k, lab in CAND:
            fr, cells = [], []
            for b in BATHY:
                got = roms_at(D, b, visc)
                if got is None or got[0].get(k) is None:
                    cells.append(f"{'—':>16}"); continue
                o, xv = got
                rv, tv = o[k], T[b][k]
                f = abs(rv - tv) / max(abs(rv), 1e-12)
                fr.append(f)
                cells.append(f"{rv:>7.3f}/{f:>6.1%}")
            if not fr:
                continue
            lo = min(fr)
            v = "✅ 纯误差" if lo >= 0.95 else ("⚠ 混真信号" if lo >= 0.5 else "❌ 主要是真信号")
            print(f"{lab:>16} " + " ".join(f"{c:>16}" for c in cells) + f"{v:>14}")

    print("""
  单元格格式：ROMS读数 / 误差占比
  判定按三个地形中**最差**的那个（最保守）
    ✅ 纯误差       误差占比 ≥ 95%，读数几乎全是数值伪迹 → 可用于诊断
    ⚠ 混真信号     50–95%，归因不干净
    ❌ 主要是真信号  < 50%，该指标测的主要是物理，不是误差
""")

    # 汇总
    out = {}
    for k, lab in CAND:
        worst = 1.0
        for b in BATHY:
            got = roms_at(D, b, 0.0)
            if got is None or got[0].get(k) is None:
                continue
            rv, tv = got[0][k], T[b][k]
            worst = min(worst, abs(rv - tv) / max(abs(rv), 1e-12))
        out[k] = dict(label=lab, worst_error_fraction=worst,
                      verdict=("pure_error" if worst >= 0.95 else
                               "mixed" if worst >= 0.5 else "mostly_signal"))
    json.dump(dict(truth=T, metrics=out),
              open(f"{E}/ledger/ablation_truth.json", "w"),
              ensure_ascii=False, indent=1)
    good = [v["label"] for v in out.values() if v["verdict"] == "pure_error"]
    print("=" * 86)
    print(f"可用于诊断 {len(good)}/{len(out)}：{'、'.join(good)}")
    print("=" * 86)


if __name__ == "__main__":
    main()
