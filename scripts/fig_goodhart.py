#!/usr/bin/env python
"""Goodhart 曲线图 —— 小倍数（三面板），共享横轴，绝不用双纵轴。

配色取自 dataviz 参考调色板前三 slot（all-pairs 双模式已验证通过）：
  #2a78d6 blue / #eb6834 orange / #1baf7a aqua
aqua 对浅底对比度 2.74:1 < 3:1 → 按"救济规则"配可见直接标注。
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
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"

res = [r for r in json.load(open(f"{ENV}/ledger/goodhart_wind.json")) if r.get("ok")]
x = np.arange(len(res))
lab = [("0" if r["VISC2"] == 0 else f"{r['VISC2']:g}") for r in res]
proxy = np.array([r["proxy"]["deep_spurious_rms_cms"] for r in res])
surf = np.array([r["proxy"]["surface_u_max_cms"] for r in res])
tover = np.array([r["true"]["temp_overshoot_max"] for r in res])

fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.3), facecolor=SURF)
panels = [
    (proxy, C1, "① 代理指标  深层伪流 rms", "cm/s",
     "全行业在优化的量\n单调改善 ↓", True),
    (surf, C2, "② 真实物理  表层风驱流 max", "cm/s",
     "风应力固定，被黏性 damp 掉\n真信号损失 ↓", True),
    (tover, C3, "③ 数值伪迹  温度超调 max", "°C",
     "无热通量 → 任何超调皆伪迹\nU 形：过量黏性反而更差", False),
]

for ax, (y, c, title, unit, note, monotone) in zip(axes, panels):
    ax.set_facecolor(SURF)
    ax.plot(x, y, "-o", color=c, lw=2, ms=8, mec=SURF, mew=1.5, zorder=3)
    ax.set_title(title, fontsize=11.5, color=INK, pad=10, loc="left")
    ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=9, color=INK2)
    ax.set_xlabel("VISC2  横向黏性 (m²/s)", fontsize=9.5, color=INK2)
    ax.set_ylabel(unit, fontsize=9.5, color=INK2)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(axis="y", color="#e6e5e1", lw=0.8, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#d9d8d3")
    # 直接标注首末（救济规则：aqua 对比度不足，必须有可见标签）
    for i, ha, dy in ((0, "left", 10), (len(y) - 1, "right", 10)):
        ax.annotate(f"{y[i]:.2f}", (x[i], y[i]), textcoords="offset points",
                    xytext=(0, dy), ha="center", fontsize=9.5,
                    color=INK, weight="bold")
    if not monotone:                      # 标出最优点
        k = int(np.argmin(y))
        ax.annotate(f"最优 {y[k]:.2f}\n@VISC2={lab[k]}", (x[k], y[k]),
                    textcoords="offset points", xytext=(6, -30),
                    fontsize=9, color=INK,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
        ax.annotate(f"比最优差 {(y[-1]/y[k]-1)*100:.0f}%",
                    (x[-1], y[-1]), textcoords="offset points",
                    xytext=(-4, 16), ha="right", fontsize=9, color=INK,
                    weight="bold")
    else:
        ax.annotate(f"{(y[-1]/y[0]-1)*100:+.0f}%", (x[-1], y[-1]),
                    textcoords="offset points", xytext=(-8, -26),
                    ha="right", fontsize=9.5, color=INK, weight="bold")
    ax.text(0.02, 0.05, note, transform=ax.transAxes, fontsize=8.8,
            color=MUTED, va="bottom")
    ax.margins(x=0.10, y=0.28)

fig.suptitle("优化代理指标会毁掉真目标 —— 风强迫陡地形 ROMS 上的 Goodhart 曲线",
             fontsize=13.5, color=INK, x=0.012, ha="left", y=0.985)
fig.text(0.012, 0.905,
         "τ = 0.1 N/m² 纬向风应力 · 40×40×13 · 3 天 · 9 组黏性 · 单次 94 s / 9 并发   "
         "横轴为参数序列（非线性刻度）",
         fontsize=9, color=MUTED, ha="left")
fig.tight_layout(rect=[0, 0, 1, 0.88])
out = f"{ENV}/ledger/fig_goodhart_visc2.png"
fig.savefig(out, dpi=170, facecolor=SURF)
print("图:", out)

# 表格视图（救济规则 + 可检查性）
print("\nVISC2 | 深层伪流rms | 表层流max | 温度超调max")
for i, r in enumerate(res):
    print(f"{lab[i]:>5} | {proxy[i]:>11.3f} | {surf[i]:>9.2f} | {tover[i]:>11.3f}")
