#!/usr/bin/env python
"""两条独立黏性轴上的 Goodhart 曲线 —— 2×2 小倍数。
行 = 旋钮（横向黏性 VISC2 / 垂向黏性 AKV_BAK）
列 = 代理指标（单调）/ 真目标（U 形）
绝不用双纵轴；文字一律 ink token。
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for cand in ("Noto Sans CJK JP", "Noto Sans CJK SC", "AR PL UKai CN"):
    if any(f.name == cand for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [cand]; break
plt.rcParams["axes.unicode_minus"] = False

ENV = "/data/xinyuan/GOAI_ai4s_env"
SURF = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; MUTED = "#8a8984"
C1, C3 = "#2a78d6", "#1baf7a"          # blue = 代理, aqua = 真目标

def load(fn, key):
    r = [x for x in json.load(open(f"{ENV}/ledger/{fn}")) if x.get("ok")]
    return r, [x[key] for x in r]

rv, vv = load("goodhart_wind.json", "VISC2")
ra, va = load("goodhart_akv.json", "VISC2")   # 键名沿用 VISC2，实为 AKV
rows = [
    ("横向黏性 VISC2 (m²/s)", rv,
     [("0" if v == 0 else f"{v:g}") for v in vv]),
    ("垂向黏性 AKV_BAK (m²/s)", ra,
     [f"{v:g}" for v in va]),
]
cols = [
    ("proxy", "deep_spurious_rms_cms", C1, "代理指标  深层伪流 rms", "cm/s"),
    ("true", "temp_overshoot_max", C3, "真目标  温度超调 max", "°C"),
]

fig, axes = plt.subplots(2, 2, figsize=(11.6, 7.4), facecolor=SURF)
for i, (xlab, res, lab) in enumerate(rows):
    x = np.arange(len(res))
    for j, (grp, key, c, title, unit) in enumerate(cols):
        ax = axes[i, j]; ax.set_facecolor(SURF)
        y = np.array([r[grp][key] for r in res])
        ax.plot(x, y, "-o", color=c, lw=2, ms=8, mec=SURF, mew=1.5, zorder=3)
        ax.set_title(f"{'①②'[i]}{'AB'[j]}  {title}", fontsize=11, color=INK,
                     pad=8, loc="left")
        ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=8.5, color=INK2)
        ax.set_ylabel(unit, fontsize=9, color=INK2)
        if i == 1:
            ax.set_xlabel(xlab, fontsize=9.5, color=INK2)
        else:
            ax.set_xlabel(xlab, fontsize=9.5, color=INK2)
        ax.tick_params(colors=INK2, labelsize=8.5, length=0)
        ax.grid(axis="y", color="#e6e5e1", lw=0.8, zorder=0)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#d9d8d3")
        for k in (0, len(y) - 1):
            ax.annotate(f"{y[k]:.2f}", (x[k], y[k]), textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=9,
                        color=INK, weight="bold")
        if j == 0:
            ax.annotate(f"{(y[-1]/y[0]-1)*100:+.0f}%  单调", (x[-1], y[-1]),
                        textcoords="offset points", xytext=(-6, -24),
                        ha="right", fontsize=9, color=INK, weight="bold")
        else:
            m = int(np.argmin(y))
            ax.annotate(f"最优 {y[m]:.2f} @ {lab[m]}", (x[m], y[m]),
                        textcoords="offset points", xytext=(8, -26),
                        fontsize=8.8, color=INK,
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
            ax.annotate(f"比最优差 {(y[-1]/y[m]-1)*100:.0f}%", (x[-1], y[-1]),
                        textcoords="offset points", xytext=(-4, 16),
                        ha="right", fontsize=9, color=INK, weight="bold")
        ax.margins(x=0.11, y=0.30)

fig.suptitle("同一个 Goodhart 形状，出现在两条互相独立的黏性轴上",
             fontsize=13.5, color=INK, x=0.012, ha="left", y=0.985)
fig.text(0.012, 0.937,
         "左列＝全行业在优化的代理指标（单调改善）　右列＝真目标（U 形：过量黏性反而更差）　"
         "风强迫陡地形 ROMS · τ=0.1 N/m² · 40×40×13 · 3 天 · 无热通量故任何温度超调皆数值伪迹",
         fontsize=8.8, color=MUTED, ha="left")
fig.tight_layout(rect=[0, 0, 1, 0.925])
out = f"{ENV}/ledger/fig_goodhart_two_axes.png"
fig.savefig(out, dpi=170, facecolor=SURF)
print("图:", out)

for xlab, res, lab in rows:
    print(f"\n{xlab}")
    print(f"{'参数':>10} | {'深层伪流rms':>12} | {'T超调max':>10} | {'表层流max':>10}")
    for k, r in enumerate(res):
        print(f"{lab[k]:>10} | {r['proxy']['deep_spurious_rms_cms']:>12.3f} |"
              f" {r['true']['temp_overshoot_max']:>10.3f} |"
              f" {r['proxy']['surface_u_max_cms']:>10.2f}")
