#!/usr/bin/env python
"""指标选择决定你能不能分辨「有伪流」和「没伪流」。

两面板，同一批 15 个 run：
  A) |U|rms —— 常用指标：平底（零 PGE）与海山看起来一样，且都"随黏性改善"
  B) 深层 rms —— 受限指标：平底≈0，海山高 50 倍，正确分辨
单轴、无双纵轴；文字一律 ink token。
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
COL = {"flat48": "#2a78d6", "mit": "#eb6834", "r26steep": "#1baf7a"}
LAB = {"flat48": "平底 3000 m（σ-PGE ≡ 0）",
       "mit": "海山 峰 107.7 m", "r26steep": "海山 峰 80.0 m"}

res = [r for r in json.load(open(f"{ENV}/ledger/config_sweep.json")) if r.get("ok")]
cfgs = ["flat48", "mit", "r26steep"]
viscs = sorted({r["VISC2"] for r in res})
x = np.arange(len(viscs))
xlab = [f"{v:g}" for v in viscs]

fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 4.8), facecolor=SURF)
panels = [
    (a1, "u_rms", "Ⓐ 常用指标：|U|rms（全域）", "cm/s",
     "平底 vs 海山只差 1.4 倍，且三者同步下降\n—— 无法把「真流被damp」与「伪流被消」分开"),
    (a2, "deep_rms", "Ⓑ 受限指标：深层 rms（>800 m）", "cm/s",
     "平底 0.17 vs 海山 9.0 —— 相差 53 倍\n—— 干净隔离出 σ-PGE 分量"),
]
for ax, key, title, unit, note in panels:
    ax.set_facecolor(SURF)
    ys = {}
    for c in cfgs:
        y = [next(r[key] for r in res if r["config"] == c and r["VISC2"] == v)
             for v in viscs]
        ys[c] = y
        ax.plot(x, y, "-o", color=COL[c], lw=2, ms=8, mec=SURF, mew=1.5,
                label=LAB[c], zorder=3)
    # 末端标签按数值排序错开，避免重叠
    order = sorted(cfgs, key=lambda c: ys[c][-1])
    span = max(ys[c][-1] for c in cfgs) - min(ys[c][-1] for c in cfgs)
    ref = max(ys[c][-1] for c in cfgs) - min(ys[c][-1] for c in cfgs)
    for rank, c in enumerate(order):
        crowded = span < 0.25 * (max(max(ys[k]) for k in cfgs) -
                                 min(min(ys[k]) for k in cfgs))
        dy = (rank - 1) * (13 if crowded else 0)
        ax.annotate(f"{ys[c][-1]:.2f}", (x[-1], ys[c][-1]),
                    textcoords="offset points", xytext=(9, dy),
                    ha="left", va="center", fontsize=9, color=INK, weight="bold")
    ax.set_title(title, fontsize=11.5, color=INK, pad=10, loc="left")
    ax.set_xticks(x); ax.set_xticklabels(xlab, fontsize=9, color=INK2)
    ax.set_xlabel("VISC2  横向黏性 (m²/s)", fontsize=9.5, color=INK2)
    ax.set_ylabel(unit, fontsize=9.5, color=INK2)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(axis="y", color="#e6e5e1", lw=0.8, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#d9d8d3")
    ax.text(0.02, 0.06, note, transform=ax.transAxes, fontsize=9,
            color=INK, va="bottom")
    ax.margins(x=0.16, y=0.24)
a1.legend(frameon=False, fontsize=9.2, labelcolor=INK, loc="upper right")

fig.suptitle("指标选对了没有，决定你能不能分辨「有伪流」和「根本没有伪流」",
             fontsize=13.5, color=INK, x=0.012, ha="left", y=0.985)
fig.text(0.012, 0.905,
         "同一批 15 个 run（3 地形 × 5 黏性，48×48×13，风强迫 τ=0.1 N/m²，3 天）。"
         "平底算例的 σ 面即水平面，压力梯度误差按构造精确为零。",
         fontsize=9, color=MUTED, ha="left")
fig.tight_layout(rect=[0, 0, 1, 0.88])
out = f"{ENV}/ledger/fig_metric_choice.png"
fig.savefig(out, dpi=170, facecolor=SURF)
print("图:", out, "\n")

print(f"{'配置':>10} | {'指标':>10} | " + " ".join(f"{v:>8g}" for v in viscs) + " |  变化")
print("-" * 78)
for key, lab in (("u_rms", "|U|rms"), ("deep_rms", "深层rms")):
    for c in cfgs:
        y = [next(r[key] for r in res if r["config"] == c and r["VISC2"] == v)
             for v in viscs]
        print(f"{c:>10} | {lab:>10} | " + " ".join(f"{v:>8.3f}" for v in y)
              + f" | {(y[-1]/y[0]-1)*100:+6.0f}%")
    print()
