#!/usr/bin/env python
"""环境接口图 —— 四页文档 P2（最大权重页）的配图。

方石凯（赛题设计者）33:01：「初赛最大的权重其实考察大家怎么去定义这个问题，
以及让 Agent 去解决这个问题的环境。」而 §2 此前没有图。

画的是**已实现**的接口（env2.py），不是设想：
  固定规则 → 动作 → 求解器 → 可见观测 ↺ Agent
                        ↘ 隐藏评估器（工作区之外）
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager

for cand in ("Noto Sans CJK SC", "Noto Sans CJK JP", "Noto Sans CJK HK"):
    if any(f.name == cand for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [cand]; break
plt.rcParams["axes.unicode_minus"] = False

SURF = "#ffffff"; INK = "#0b0b0b"; INK2 = "#52514e"
GRID = "#e6e5e1"; MUTED = "#8a8984"
C_AGENT, C_SOLVER, C_HIDDEN = "#3C5488", "#E64B35", "#00A087"

fig, ax = plt.subplots(figsize=(12.2, 6.4), facecolor=SURF)
ax.set_xlim(0, 100); ax.set_ylim(4, 101); ax.axis("off")
ax.text(0.5, 98.5, "智能体只能提交配置换读数——真值藏在它够不着的地方",
        fontsize=15, fontweight="bold", va="top")
ax.set_facecolor(SURF)


def box(x, y, w, h, title, lines, color, lw=1.6, fs=10.6, alpha=0.06):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                                fc=color, ec=color, lw=lw, alpha=alpha, zorder=1))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                                fc="none", ec=color, lw=lw, zorder=3))
    ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="top",
            fontsize=12, color=INK, fontweight="bold", zorder=4)
    top = y + h - 7.2
    step = min(3.6, max(2.6, (top - y - 1.8) / max(len(lines), 1)))
    for i, t in enumerate(lines):
        ax.text(x + 2.2, top - i * step, t, ha="left", va="top",
                fontsize=fs, color=INK2, zorder=4)


def arrow(x1, y1, x2, y2, color, label="", rad=0.0, ls="-", lw=1.7, off=(0, 2.2)):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                 connectionstyle=f"arc3,rad={rad}",
                                 arrowstyle="-|>", mutation_scale=15,
                                 lw=lw, color=color, ls=ls, zorder=5))
    if label:
        ax.text((x1 + x2) / 2 + off[0], (y1 + y2) / 2 + off[1], label,
                ha="center", va="bottom", fontsize=10, color=color, zorder=6)


# ── 固定规则（不可探索） ──
box(1.5, 63, 25, 27, "固定规则（不可改）", [
    "ROMS 求解器",
    "网格 48 × 48 × 13",
    "风应力 0.1 N/m²，步长 10 s",
    "单核，可原样复现",
    "二进制指纹已存档",
    "可从源码一键重建",
], MUTED)

# ── Agent ──
box(1.5, 30, 25, 30, "智能体（Agent）", [
    "能动 7 个：",
    "  地形（三选一）",
    "  四个黏性/扩散旋钮",
    "  积分长短",
    "  随机种子",
], C_AGENT)

# ── 求解器 ──
box(36, 44, 28, 30, "环境 env.step()", [
    "① 写配置 + 回显自检",
    "② 真跑求解器（约 2 分钟）",
    "③ 固定代码算读数",
    "   （语言模型不碰数值）",
], C_SOLVER)

# ── 可见观测 ──
box(71, 64, 27.5, 24, "可见读数（它看得到）", [
    "流速 4 项 + 温度极值",
    "抗刷分比值（uv_ratio）",
    "完赛 / 崩溃 / 完成比例",
], C_AGENT)

# ── 隐藏评估器 ──
box(71, 12, 27.5, 38, "隐藏评估器（它够不着）", [
    "MITgcm 独立真值",
    "  与官方结果逐位一致",
    "",
    "误差（err_rms）",
    "技巧评分",
    "  0 分 = 什么都不做",
], C_HIDDEN)

# ── ledger ──
box(36, 8, 28, 26, "台账（每跑一次记一行）", [
    "动作 + 读数 + 隐藏量",
    "绑定二进制指纹",
    "",
    "已累计 367 次运行（345 有效）",
], MUTED)

# 智能体 ↔ 环境：两条短直线（经典 RL 环）
arrow(26.5, 58, 36, 62, C_AGENT, "", rad=0.0)
ax.text(31.2, 63.5, "动作", fontsize=10.5, color=C_AGENT, ha="center", zorder=7)
arrow(36, 48, 26.5, 44, C_AGENT, "", rad=0.0, ls="--", lw=1.5)
ax.text(31.2, 38.5, "只回可见读数", fontsize=10, color=C_AGENT, ha="center", zorder=7)
# 环境 → 可见读数
arrow(64, 68, 71, 72, C_AGENT, "", rad=0.0)
ax.text(67.5, 72.8, "读数", fontsize=10.5, color=C_AGENT, ha="center", zorder=7)
# 环境 → 隐藏评估器
arrow(64, 50, 71, 44, C_HIDDEN, "", rad=-0.12)
# 环境 → 台账
arrow(50, 44, 50, 34, MUTED, "", lw=1.4, rad=0.0)
# 固定规则 → 环境（细灰线，不再孤岛）
arrow(26.5, 72, 36, 68, MUTED, "", lw=1.1, rad=0.0)
# 真值不回流：隐藏评估器 → 可见读数方向的禁止线（真值永不进入智能体可见的读数）
arrow(84.5, 50, 84.5, 59, C_HIDDEN, "", ls="--", lw=1.4, rad=0.0)
ax.text(84.5, 54.2, "×", fontsize=17, color="#E64B35", ha="center", va="center",
        fontweight="bold", zorder=8)
ax.text(84.5, 61.0, "真值不进可见读数", fontsize=10, color=C_HIDDEN, ha="center",
        style="italic")

fig.tight_layout()
out = "/data/xinyuan/GOAI_ai4s_env/ledger/fig_env.png"
fig.savefig(out, dpi=300, facecolor=SURF, bbox_inches="tight")
print(out)
