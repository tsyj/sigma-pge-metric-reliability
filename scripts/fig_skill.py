#!/usr/bin/env python
"""E34/E35 技巧评分图 —— 代理指标一路「改善」，技巧评分从不过零。

① 可见代理指标：单调下降 8.67 → 0.14，逼近平底对照下限，看起来像"解决了"
② 隐藏技巧评分：全程为负 —— 没有任何配置好过「什么都不输出」

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

SURF = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"
GRID = "#e6e5e1"; MUTED = "#8a8984"
C_PROXY, C_SKILL, C_REF = "#2a78d6", "#eb6834", "#1baf7a"

E = "/data/xinyuan/GOAI_ai4s_env"
rows = [json.loads(l) for l in open(f"{E}/ledger/regraded_v2.jsonl")]
d = {}
for r in rows:
    if set(r["action"]) <= {"bathy", "VISC2", "ntimes", "seed"} and r["ntimes"] == 8640:
        d[round(r["action"].get("VISC2", 0.0), 1)] = r
ks = np.array(sorted(k for k in d if k > 0))          # 对数轴，去掉 0
proxy = np.array([d[k]["deep_rms_800"] for k in ks])
skill = np.array([d[k]["skill_vs_zero"] for k in ks])
FLAT_FLOOR = 0.0294        # 平底对照（σ-PGE ≡ 0）的深层 rms
CRASH = 1e5                # VISC2=100000 崩溃

fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.8, 4.8), facecolor=SURF)
for a in (a1, a2):
    a.set_facecolor(SURF)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        a.spines[s].set_color(GRID)
    a.tick_params(colors=INK2, labelsize=9)
    a.grid(True, color=GRID, lw=0.7, alpha=0.9)
    a.set_axisbelow(True)
    a.set_xscale("log")
    a.axvspan(CRASH, CRASH * 4, color=MUTED, alpha=0.16, lw=0)

# ---------- ① 可见代理指标 ----------
a1.plot(ks, proxy, "-o", color=C_PROXY, lw=2.2, ms=5)
a1.axhline(FLAT_FLOOR, color=C_REF, lw=1.6, ls="--")
a1.set_yscale("log")
a1.set_xlabel("VISC2  横向黏性 (m²/s，对数轴)", fontsize=9.5, color=INK2)
a1.set_ylabel("深层 rms (cm/s，对数轴)", fontsize=9.5, color=INK2)
_gain = proxy.max() / proxy.min()
a1.set_title(f"① Agent 看到的：单调「改善」{_gain:.0f} 倍", fontsize=11.5, color=INK,
             pad=10, loc="left")
a1.annotate(f"平底对照下限 {FLAT_FLOOR:.4f}\n（σ-PGE 按构造为零）",
            xy=(2e2, FLAT_FLOOR), xytext=(1.3e2, 0.09),
            fontsize=8.8, color=C_REF)
a1.annotate("VISC2=30000\n读到 0.140", xy=(3e4, 0.14), xytext=(2.6e3, 0.42),
            fontsize=8.8, color=C_PROXY,
            arrowprops=dict(arrowstyle="->", color=C_PROXY, lw=1.0))
a1.text(CRASH * 1.15, 0.25, "崩溃", fontsize=9, color=MUTED, rotation=90, va="center")

# ---------- ② 隐藏技巧评分 ----------
a2.plot(ks, skill, "-o", color=C_SKILL, lw=2.2, ms=5)
a2.axhline(0.0, color=C_REF, lw=1.8, ls="--")
a2.set_xlabel("VISC2  横向黏性 (m²/s，对数轴)", fontsize=9.5, color=INK2)
a2.set_ylabel("技巧评分  SS = 1 − (误差/真值)²", fontsize=9.5, color=INK2)
a2.set_title("② 真值说的：从不过零", fontsize=11.5, color=INK, pad=10, loc="left")
a2.set_ylim(-9.6, 1.6)
a2.annotate("SS = 0 ：与「什么都不输出」持平",
            xy=(3e2, 0.0), xytext=(1.2e2, 0.75), fontsize=9.0, color=C_REF)
a2.annotate(f"最好也只到 {skill.max():.3f}", xy=(3e4, skill.max()),
            xytext=(2.2e3, -2.6), fontsize=8.8, color=C_SKILL,
            arrowprops=dict(arrowstyle="->", color=C_SKILL, lw=1.0))
a2.text(CRASH * 1.15, -4.5, "崩溃", fontsize=9, color=MUTED, rotation=90, va="center")

fig.suptitle(f"代理指标改善 {proxy.max()/proxy.min():.0f} 倍、逼近「完美分数」下限 —— "
             "而没有任何配置好过「直接预报零」",
             fontsize=12.4, color=INK, y=1.005, x=0.008, ha="left")
fig.tight_layout()
out = f"{E}/ledger/fig_skill.png"
fig.savefig(out, dpi=170, facecolor=SURF, bbox_inches="tight")
print(out)
print(f"  代理 {proxy.max():.3f} → {proxy.min():.4f}（{proxy.max()/proxy.min():.0f} 倍）")
print(f"  技巧评分 {skill.min():.3f} → {skill.max():.3f}，全部 < 0")
