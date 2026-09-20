#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""现场交互矩阵：点一个格子看分，再点旁边一个，当场判这把尺子该不该信。

数据全部来自随包的 e118_board/board.json（封版件），本程序不做任何新计算，
只把已算好的读数摆出来、按固定规则做比较。

用法：
    python scripts/matrix.py
    鼠标左键点格子；按 r 重来；按 t 显示/隐藏真值行；按 q 退出。
"""
import json
import os
import sys

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CAND = [os.path.join(ROOT, "sigma_audit", "data", "reference", "board.json"),
        os.path.join(ROOT, "e118_board", "board.json"),
        "/data/xinyuan/GOAI_ai4s_env/e118_board/board.json"]
SRC = next((p for p in CAND if os.path.exists(p)), None)
if SRC is None:
    sys.exit("找不到 board.json（找过：%s）" % " / ".join(CAND))

for d in ("/home/xinyuan/比赛/赛道三赛题二/决赛/官方模板与指南/世界人工智能开源大赛PPT模板16-9Global Open-source AI Challenge PPT Template/字体Font",
          os.path.join(ROOT, "docs", "fonts")):
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.startswith("OPPOSans-") and f.endswith(".ttf"):
                fm.fontManager.addfont(os.path.join(d, f))
        break
for fam in ("OPPOSans", "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "sans-serif"):
    if any(f.name == fam for f in fm.fontManager.ttflist) or fam == "sans-serif":
        plt.rcParams["font.family"] = fam
        break
plt.rcParams["axes.unicode_minus"] = False

B = json.load(open(SRC, encoding="utf-8"))
ACT = [a["VISC2"] for a in B["actions"]]
TRUTH = np.array(B["truth_skill_vs_zero"], float)      # 越大越好（越接近 0）
RUL = B["rulers"]
NR, NA = len(RUL), len(ACT)

STEEP = np.array([r["steep"] for r in RUL], float)     # 读数，越小越好
FLAT = np.array([r["flat"] for r in RUL], float)

def to_score(row):
    lo, hi = float(np.min(row)), float(np.max(row))
    if hi - lo < 1e-12:
        return np.full_like(row, 50.0)
    return 100.0 * (hi - row) / (hi - lo)             # 读数小 → 分高

SCORE = np.array([to_score(STEEP[i]) for i in range(NR)])
FSCORE = np.array([to_score(FLAT[i]) for i in range(NR)])

NAVY, ORANGE, TEAL, GREY = "#002159", "#E85D04", "#0E7C86", "#8A97A8"
CMAP = plt.get_cmap("YlGnBu")

fig = plt.figure(figsize=(15.5, 8.6))
fig.patch.set_facecolor("white")
axM = fig.add_axes([0.175, 0.345, 0.62, 0.545])
axT = fig.add_axes([0.175, 0.285, 0.62, 0.045])
axP = fig.add_axes([0.815, 0.30, 0.175, 0.58]); axP.axis("off")
axB = fig.add_axes([0.04, 0.045, 0.93, 0.20]); axB.axis("off")

sel = []
show_truth = [False]

def short(lab):
    return lab if len(lab) <= 24 else lab[:23] + "…"

def draw():
    axM.clear(); axT.clear(); axP.clear(); axB.clear()
    axP.axis("off"); axB.axis("off")
    axM.imshow(SCORE, cmap=CMAP, vmin=0, vmax=100, aspect="auto")
    axM.set_xticks(range(NA))
    axM.set_xticklabels(["方法%d" % (j + 1) for j in range(NA)], fontsize=11)
    axM.set_yticks(range(NR))
    axM.set_yticklabels(["尺子%-2d %s" % (i + 1, short(RUL[i]["label"])) for i in range(NR)],
                        fontsize=8.5)
    axM.tick_params(length=0)
    for sp in axM.spines.values():
        sp.set_edgecolor(NAVY); sp.set_linewidth(2.0)
    axM.set_title("点一个格子看分数，再点旁边一个 —— 然后决定：动成果，还是动这把尺子的权重",
                  fontsize=15, color=NAVY, fontweight="bold", pad=14)
    for k, (i, j) in enumerate(sel):
        axM.add_patch(Rectangle((j - .5, i - .5), 1, 1, fill=False,
                                edgecolor=ORANGE if k == 0 else TEAL, lw=3.5))
        axM.text(j, i, "%.0f" % SCORE[i, j], ha="center", va="center",
                 fontsize=12, fontweight="bold", color="#111111")
    axM.set_xticklabels([])
    t = 100.0 * (TRUTH - TRUTH.min()) / (TRUTH.max() - TRUTH.min())
    if show_truth[0]:
        axT.imshow(t.reshape(1, -1), cmap="Oranges", vmin=0, vmax=100, aspect="auto")
        for j in range(NA):
            axT.text(j, 0, "%.0f" % t[j], ha="center", va="center",
                     fontsize=10.5, color="#3A1600", fontweight="bold")
        axT.text(-0.62, 0, "封存真值", ha="right", va="center",
                 fontsize=10.5, color=ORANGE, fontweight="bold")
        for sp in axT.spines.values():
            sp.set_edgecolor(ORANGE); sp.set_linewidth(2.0)
    else:
        axT.text(0.5, 0.5, "真值已封存 —— 按 t 揭开", ha="center", va="center",
                 fontsize=11, color=GREY, transform=axT.transAxes)
        for sp in axT.spines.values():
            sp.set_visible(False)
    axT.set_yticks([])
    axT.set_xticks(range(NA))
    axT.set_xticklabels(["方法%d" % (j + 1) for j in range(NA)], fontsize=11)
    axT.tick_params(length=0)
    axT.set_xlim(axM.get_xlim())

    # 右栏
    y = 0.97
    def P(s, sz=11, c=NAVY, b=False, dy=0.055):
        nonlocal y
        axP.text(0, y, s, fontsize=sz, color=c, fontweight="bold" if b else "normal",
                 va="top", transform=axP.transAxes)
        y -= dy
    if not sel:
        P("怎么用", 13, NAVY, True); P("")
        P("1. 点一个格子", 11, GREY)
        P("2. 再点同一行旁边一格", 11, GREY)
        P("3. 看下面的判定", 11, GREY); P("")
        P("r 重来   t 真值   q 退出", 10, GREY)
    else:
        for k, (i, j) in enumerate(sel):
            P("第%s点  尺子%d × 方法%d" % ("一" if k == 0 else "二", i + 1, j + 1),
              12, ORANGE if k == 0 else TEAL, True)
            P("  分数 %.0f" % SCORE[i, j], 11)
            P("  陡海山读数 %.4g" % STEEP[i, j], 10, GREY)
            P("  平底读数   %.4g" % FLAT[i, j], 10, GREY, dy=0.075)

    # 底栏判定
    if len(sel) == 2:
        (i1, j1), (i2, j2) = sel
        if i1 != i2:
            axB.text(0, .8, "两次点的不是同一把尺子——请在同一行里比较（按 r 重来）",
                     fontsize=15, color=ORANGE, fontweight="bold", transform=axB.transAxes)
        else:
            ruler_better2 = SCORE[i2, j2] > SCORE[i1, j1]
            truth_better2 = TRUTH[j2] > TRUTH[j1]
            agree = ruler_better2 == truth_better2
            flat_moved = FSCORE[i2, j2] - FSCORE[i1, j1]
            fooled = flat_moved > 5.0
            L = []
            L.append(("尺子%d 说：方法%d 比 方法%d %s（%.0f 对 %.0f）"
                      % (i1 + 1, j2 + 1, j1 + 1, "更好" if ruler_better2 else "更差",
                         SCORE[i2, j2], SCORE[i1, j1]), NAVY))
            L.append(("封存真值说：方法%d 比 方法%d %s"
                      % (j2 + 1, j1 + 1, "更好" if truth_better2 else "更差"), ORANGE))
            L.append(("平底对照（那里本来就没有误差可改）：读数%s %+.0f 分"
                      % ("变好了" if flat_moved > 0 else "没变好", flat_moved),
                      ORANGE if fooled else TEAL))
            axB.text(0, .95, "判  定", fontsize=13, color=NAVY, fontweight="bold",
                     transform=axB.transAxes)
            for k, (s, c) in enumerate(L):
                axB.text(0, .72 - k * .20, "·  " + s, fontsize=13.5, color=c,
                         transform=axB.transAxes)
            if fooled:
                verdict, vc = ("这把尺子在什么都没修的地方也说变好了 —— 它的权重该降下来，排序靠后", ORANGE)
            elif agree:
                verdict, vc = ("尺子和真值一致，平底上也没被骗 —— 这一步可以按它的话去改成果", TEAL)
            else:
                verdict, vc = ("尺子和真值反了 —— 别动成果，先降这把尺子的权重", ORANGE)
            axB.text(0, .06, "结论：" + verdict, fontsize=16, color=vc, fontweight="bold",
                     transform=axB.transAxes)
    elif len(sel) == 1:
        axB.text(0, .55, "再点同一行旁边一格，就能判这把尺子这一步说得对不对",
                 fontsize=15, color=GREY, transform=axB.transAxes)
    else:
        axB.text(0, .55, "颜色越深 = 这把尺子给这个方法的分越高。真值是封存的，按 t 揭开。",
                 fontsize=14, color=GREY, transform=axB.transAxes)
    fig.canvas.draw_idle()

def on_click(ev):
    if ev.inaxes is not axM or ev.xdata is None:
        return
    j, i = int(round(ev.xdata)), int(round(ev.ydata))
    if not (0 <= i < NR and 0 <= j < NA):
        return
    if len(sel) >= 2:
        sel.clear()
    sel.append((i, j))
    draw()

def on_key(ev):
    if ev.key == "r":
        sel.clear(); draw()
    elif ev.key == "t":
        show_truth[0] = not show_truth[0]; draw()
    elif ev.key == "q":
        plt.close(fig)

fig.canvas.mpl_connect("button_press_event", on_click)
fig.canvas.mpl_connect("key_press_event", on_key)
draw()
print("矩阵：%d 把尺子 × %d 个方法，数据源 %s" % (NR, NA, SRC))
print("鼠标点格子；r 重来；t 显示真值；q 退出")
plt.show()
