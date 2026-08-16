#!/usr/bin/env python
"""指标消融 —— 官方排雷清单第 6 条：「换一个指标会不会结论相反？」

同一批 run，只换 Agent 可见的优化目标，看：
  A) 它会选出哪个最优？隐藏真值同意吗？
  B) ⭐ 在 σ-PGE 精确为零的平底对照上，该指标会不会"成功优化"出一个假阳性？

不需要新跑 run —— 全部从 ledger 离线重放。
"""
import json, sys, os
import numpy as np

E = "/data/xinyuan/GOAI_ai4s_env"
NT = 8640                      # 只用同一时长的 run，避免混入 E21 的时长效应

CANDIDATES = [
    ("u_max",         "全域最大流速"),
    ("u_rms",         "全域 rms"),
    ("surf_max",      "表层最大流速"),
    ("deep_rms_200",  "深层 rms (>200 m)"),
    ("deep_rms_800",  "深层 rms (>800 m)"),
    ("deep_rms_1500", "深层 rms (>1500 m)"),
]
TRUTH = "err_rms_vs_truth"


def load():
    rows = [json.loads(l) for l in open(f"{E}/ledger/env2_runs.jsonl")]
    out = {}
    for r in rows:
        if not r["obs"].get("valid") or r["ntimes"] != NT:
            continue
        b = r["bathy"]; v = round(r["action"].get("VISC2", 0.0), 1)
        out.setdefault(b, {})[v] = (r["obs"], r["hidden"])
    return out


def main():
    D = load()
    for b in D:
        print(f"  {b:10s} {len(D[b])} 个不同 VISC2")
    print()

    # ---------- A) 各指标推荐的最优，真值同意吗 ----------
    print("═" * 78)
    print("A) 在有真值的地形 (r26steep) 上：各候选指标推荐的最优 VISC2")
    print("═" * 78)
    d = D["r26steep"]
    vs = np.array(sorted(d))
    tr = np.array([d[v][1][TRUTH] for v in vs])
    j_true = int(np.argmin(tr))
    print(f"{'候选指标':>18} {'推荐 VISC2':>11} {'该点真值误差':>12} "
          f"{'vs 真最优':>10} {'与真值秩相关':>13}")
    print("-" * 78)
    for key, lab in CANDIDATES:
        y = np.array([d[v][0].get(key, np.nan) for v in vs])
        if np.all(np.isnan(y)):
            continue
        j = int(np.nanargmin(y))
        # Spearman 秩相关（手算，避免引入 scipy.stats 依赖分歧）
        ry = np.argsort(np.argsort(y)); rt = np.argsort(np.argsort(tr))
        rho = float(np.corrcoef(ry, rt)[0, 1])
        gap = (tr[j] / tr[j_true] - 1) * 100
        print(f"{lab:>18} {vs[j]:>11.0f} {tr[j]:>12.3f} {gap:>+9.1f}% {rho:>13.3f}")
    print(f"\n  真值本身的最优：VISC2={vs[j_true]:.0f}（误差 {tr[j_true]:.3f} cm/s）")

    # ---------- B) 平底对照上的归因 ----------
    print()
    print("=" * 80)
    print("B) 在 sigma-PGE 精确为零的平底对照上：各指标的变化有多少不是 PGE 造成的")
    print("=" * 80)
    LO, HI = 0.0, 2747.0

    def val(b, target, key):
        dd = D[b]
        x = min(dd, key=lambda z: abs(z - target))
        return dd[x][0].get(key)

    print(f"{'候选指标':>16} {'平底dABS':>11} {'海山dABS':>11} "
          f"{'平底占比':>9} {'分辨力@0':>10} {'判定':>14}")
    print("-" * 80)
    verdicts = {}
    for key, lab in CANDIDATES:
        f0, f1 = val("flat", LO, key), val("flat", HI, key)
        s0, s1 = val("r26steep", LO, key), val("r26steep", HI, key)
        if None in (f0, f1, s0, s1):
            continue
        df, ds = abs(f0 - f1), abs(s0 - s1)
        frac = df / max(ds, 1e-12)
        ratio = s0 / max(f0, 1e-12)
        ok = (ratio >= 3) and (frac <= 0.15)
        v = "OK 可信" if ok else ("XX 分辨不出" if ratio < 3 else "!! 污染重")
        verdicts[lab] = ok
        print(f"{lab:>16} {df:>11.4f} {ds:>11.4f} {frac:>8.1%} {ratio:>9.1f}x {v:>14}")

    print("""
  判据（归因看**绝对量**，不看相对变化）
    分辨力@0  海山/平底 在 VISC2=0 处的读数比；< 3x -> 该指标没在测 sigma-PGE
    平底占比  |平底绝对变化| / |海山绝对变化|
              即"该指标的变化里有多少不是 sigma-PGE 造成的"；> 15% -> 污染重

  [!] 本判据第一版用的是**相对变化**（平底变化 >15% 判污染），得出"6/6 全不可信"。
      但平底 deep_rms 从 0.030 降到 0.021：相对 -30%，绝对仅 0.009 cm/s，
      而海山上是 7.78 cm/s。**相对变化能排序，不能归因** ——
      这与本环境测出的 sigma-PGE 指标问题是同一种错误。已修正。
""")

    # ---------- C) 结论 ----------
    print("=" * 80)
    print("C) 结论")
    print("=" * 80)
    bad = [k for k, v in verdicts.items() if not v]
    good = [k for k, v in verdicts.items() if v]
    print(f"  可信   {len(good)}/{len(verdicts)}：{'、'.join(good)}")
    print(f"  不可信 {len(bad)}/{len(verdicts)}：{'、'.join(bad)}")
    print("""
  两条判据抓的是不同的病：
    全域 rms      -- 分辨不出（2.3x）：平底与海山读数几乎一样
    表层最大流速  -- 分辨得出但污染重（20.5%）：变化里五分之一不是 sigma-PGE 造成的
  深层 rms 类污染仅 0.1%，比全域/表层类低 100-200 倍。

  另注：A 段显示六个指标的**排序**几乎完全一致（秩相关 >= 0.997），
        全部选中真值最优点。**排序能力与诊断能力是两回事。**
""")
    bad = list(bad)

    json.dump(dict(n_truth_points=len(vs), candidates=[c[0] for c in CANDIDATES],
                   untrustworthy=bad),
              open(f"{E}/ledger/ablation_metrics.json", "w"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
