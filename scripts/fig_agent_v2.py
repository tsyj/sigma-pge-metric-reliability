#!/usr/bin/env python
"""Agent v2：14 点稠密曲线上的代理/真值分歧 + 分辨力对时长的依赖。

两面板（单轴，无双纵轴）：
  Ⓐ 代理 vs 真值（同为 cm/s，合法共轴）—— 穿越点与张开的虚报缺口
  Ⓑ 指标分辨力随积分时长的变化 —— 平底残差在长，海山伪流在降
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for c in ("Noto Sans CJK JP", "Noto Sans CJK SC", "AR PL UKai CN"):
    if any(f.name == c for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [c]; break
plt.rcParams["axes.unicode_minus"] = False

E = "/data/xinyuan/GOAI_ai4s_env"
SURF = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; MUTED = "#8a8984"
C_PROXY, C_TRUTH, C_FLAT, C_SEA = "#2a78d6", "#eb6834", "#2a78d6", "#eb6834"

# ---- 数据 ----
a = json.load(open(f"{E}/ledger/agent_v2_s0.json"))
pts = {}
for s in a["log"]:
    if (s["obs"].get("valid") and s["action"]["bathy"] == "r26steep"
            and s["obs"].get("deep_rms_800") is not None
            and s["hidden_grade"].get("score") is not None):
        pts[round(s["action"]["VISC2"], 1)] = (s["obs"]["deep_rms_800"],
                                               s["hidden_grade"]["score"])
v = np.array(sorted(pts))
proxy = np.array([pts[x][0] for x in v])
truth = np.array([pts[x][1] for x in v])

seed = [s for s in a["log"] if s["phase"] == "seed"]
d1 = {s["action"]["bathy"]: s["obs"]["deep_rms_800"]
      for s in seed if s["action"]["VISC2"] == 0.0}
c3 = json.load(open(f"{E}/ledger/config_sweep.json"))
d3 = {r["config"].replace("flat48", "flat"): r["deep_rms"]
      for r in c3 if r["ok"] and r["VISC2"] == 0.0}

fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.8, 4.9), facecolor=SURF)

# ---- Ⓐ ----
a1.set_facecolor(SURF)
a1.plot(v, proxy, "-o", color=C_PROXY, lw=2, ms=7, mec=SURF, mew=1.4,
        label="Agent 可见的代理指标  deep_rms(>800 m)", zorder=3)
a1.plot(v, truth, "-o", color=C_TRUTH, lw=2, ms=7, mec=SURF, mew=1.4,
        label="隐藏真值误差  vs MITgcm z 坐标", zorder=3)
a1.fill_between(v, proxy, truth, where=proxy < truth, color=C_PROXY,
                alpha=0.11, zorder=1)
k = int(np.argmin(np.abs(proxy - truth)))
a1.axvline(v[k], color=MUTED, lw=1, ls=(0, (4, 3)), zorder=2)
a1.annotate(f"穿越点 ≈ {v[k]:.0f}", (v[k], max(proxy.max(), truth.max()) * 0.93),
            textcoords="offset points", xytext=(8, 0), ha="left",
            fontsize=9.5, color=INK, weight="bold")
for arr, dyL, dyR in ((proxy, 14, -20), (truth, -20, 14)):
    for i, dy in ((0, dyL), (len(v) - 1, dyR)):
        a1.annotate(f"{arr[i]:.2f}", (v[i], arr[i]), textcoords="offset points",
                    xytext=(4 if i == 0 else 0, dy),
                    ha="left" if i == 0 else "center",
                    fontsize=9.5, color=INK, weight="bold")
a1.annotate("真值触底 ≈ 3.0\n（真信号 rms 仅 1.77）", (v[-1], truth[-1]),
            textcoords="offset points", xytext=(-12, 40), ha="right",
            fontsize=9, color=INK,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
a1.set_title("Ⓐ 14 点稠密曲线：代理穿到真值下面", fontsize=11.5, color=INK,
             pad=10, loc="left")
a1.set_xlabel("VISC2  横向黏性 (m²/s)", fontsize=9.5, color=INK2)
a1.set_ylabel("cm/s", fontsize=9.5, color=INK2)
a1.legend(frameon=False, fontsize=9.2, labelcolor=INK, loc="upper right")

# ---- Ⓑ ----
a2.set_facecolor(SURF)
x = np.arange(2)
for b, col, lab in (("flat", C_FLAT, "平底（σ-PGE ≡ 0）"),
                    ("r26steep", C_SEA, "海山 峰 80 m")):
    y = [d1[b], d3[b]]
    a2.plot(x, y, "-o", color=col, lw=2, ms=9, mec=SURF, mew=1.5,
            label=lab, zorder=3)
    for i in x:
        a2.annotate(f"{y[i]:.3f}", (i, y[i]), textcoords="offset points",
                    xytext=(0, 12), ha="center", fontsize=9.5, color=INK,
                    weight="bold")
a2.set_yscale("log")
a2.set_xticks(x); a2.set_xticklabels(["1 天\n(8640 步)", "3 天\n(25920 步)"],
                                     fontsize=9.5, color=INK2)
a2.set_title("Ⓑ 分辨力依赖积分时长", fontsize=11.5, color=INK, pad=10, loc="left")
a2.set_ylabel("深层 rms (cm/s，对数轴)", fontsize=9.5, color=INK2)
a2.legend(frameon=False, fontsize=9.2, labelcolor=INK, loc="center right")
r1, r3 = d1["r26steep"] / d1["flat"], d3["r26steep"] / d3["flat"]
a2.text(0.03, 0.60,
        f"分辨力  {r1:.0f}× → {r3:.0f}×\n"
        f"平底残差 ↑{d3['flat']/d1['flat']:.1f}× · 海山伪流 ↓{1-d3['r26steep']/d1['r26steep']:.0%}\n"
        "→ 即使是「正确」的指标，信噪比也依赖时长",
        transform=a2.transAxes, fontsize=9, color=INK, va="bottom")

for ax in (a1, a2):
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(axis="y", color="#e6e5e1", lw=0.8, zorder=0)
    for s_ in ("top", "right", "left"):
        ax.spines[s_].set_visible(False)
    ax.spines["bottom"].set_color("#d9d8d3")
    ax.margins(x=0.10, y=0.28)

fig.suptitle("Agent 两阶段探索（12 点并行播种 + 10 步自适应），干净可重建 binary",
             fontsize=13.5, color=INK, x=0.012, ha="left", y=0.985)
fig.text(0.012, 0.905,
         "Agent 只看得见代理指标；真值仅写入日志供离线检查。"
         "48×48×13 风强迫海山 · τ=0.1 N/m² · 单 run 约 122 s。"
         "求解器 sha256 479eca46…5401a，可从源码重建。",
         fontsize=9, color=MUTED, ha="left")
fig.tight_layout(rect=[0, 0, 1, 0.88])
out = f"{E}/ledger/fig_agent_v2.png"
fig.savefig(out, dpi=170, facecolor=SURF)
print("图:", out, "\n")
print(f"{'VISC2':>8} {'代理':>8} {'真值':>8} {'比值':>7}")
for i in range(len(v)):
    print(f"{v[i]:>8.1f} {proxy[i]:>8.3f} {truth[i]:>8.3f} {proxy[i]/truth[i]:>7.3f}")
print(f"\n全程 代理 {proxy[0]:.3f}→{proxy[-1]:.3f} ({proxy[-1]/proxy[0]-1:+.0%})"
      f"   真值 {truth[0]:.3f}→{truth[-1]:.3f} ({truth[-1]/truth[0]-1:+.0%})")
