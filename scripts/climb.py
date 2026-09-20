#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一边改进成果，一边给尺子重新赋权 —— 现场逐轮演示。

按一次空格走一轮：
  1. 十四把尺子按当前权重投票：下一个方法比现在好吗
  2. 票过半就把成果往右挪一格
  3. 同时逐把回查：谁在平底对照上显得更好看（那里按构造没有误差可改），
     谁的权重砍半

数据全部来自随包的 board.json（封版件）。本程序不做新计算，
判据与封存的第二关 B 完全同构：B = mean(平底读数 >= 陡海山读数)。

用法：python scripts/climb.py
      空格 走一轮   r 重来   t 显示/隐藏真值   q 退出
"""
import json
import os
import sys

import numpy as np
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
    sys.exit("找不到 board.json")

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
TRUTH = np.array(B["truth_skill_vs_zero"], float)
RUL = B["rulers"]
ST = np.array([r["steep"] for r in RUL], float)
FL = np.array([r["flat"] for r in RUL], float)
BSEAL = np.array([r["B"] for r in RUL], float)
NR, NA = ST.shape

def to_score(row):
    lo, hi = float(row.min()), float(row.max())
    return np.full_like(row, 50.0) if hi - lo < 1e-12 else 100.0 * (hi - row) / (hi - lo)

SCORE = np.array([to_score(ST[i]) for i in range(NR)])

NAVY, ORANGE, TEAL, GREY = "#002159", "#E85D04", "#0E7C86", "#93A0B0"

S = {"pos": 0, "w": np.ones(NR), "traj": [0], "step": 0, "log": None,
     "just": np.zeros(NR, bool), "truth": False, "done": False}

fig = plt.figure(figsize=(16.0, 8.8))
fig.patch.set_facecolor("white")
axM = fig.add_axes([0.045, 0.34, 0.505, 0.545])
axT = fig.add_axes([0.045, 0.277, 0.505, 0.048])
axW = fig.add_axes([0.675, 0.277, 0.285, 0.608])
axB = fig.add_axes([0.04, 0.035, 0.94, 0.20]); axB.axis("off")

def step():
    if S["done"]:
        return
    j1 = S["pos"]
    if j1 >= NA - 1:
        S["done"] = True
        S["log"] = ("到头了", "已经是最后一个方法。按 r 重来。", TEAL)
        return
    j2 = j1 + 1
    fooled = FL[:, j2] < ST[:, j2]          # 在没有误差可改的平底上显得更好看
    S["just"] = fooled
    S["w"][fooled] *= 0.5
    says = ST[:, j2] < ST[:, j1]            # 这把尺子说 j2 更好
    tally = float((S["w"] * says).sum() / S["w"].sum())
    S["step"] += 1
    moved = tally > 0.5
    if moved:
        S["pos"] = j2
        S["traj"].append(j2)
    n = int(fooled.sum())
    head = "第 %d 轮　方法%d 往 方法%d" % (S["step"], j1 + 1, j2 + 1)
    body = ("%.0f%% 的尺子（按权重）说下一个方法更好　%s　　本轮有 %d 把在对照上显得更好看，权重砍半"
            % (tally * 100, "→ 往前一格" if moved else "→ 不到一半，留在原地", n))
    S["log"] = (head, body, TEAL if moved else ORANGE)
    if not moved:
        S["done"] = True

def draw():
    for a in (axM, axT, axW, axB):
        a.clear()
    axB.axis("off")

    axM.imshow(SCORE, cmap="YlGnBu", vmin=0, vmax=100, aspect="auto")
    axM.set_xticks(range(NA)); axM.set_xticklabels([])
    axM.set_yticks(range(NR))
    axM.set_yticklabels(["尺子%d" % (i + 1) for i in range(NR)], fontsize=10)
    axM.tick_params(length=0)
    for sp in axM.spines.values():
        sp.set_edgecolor(NAVY); sp.set_linewidth(2.2)
    axM.add_patch(Rectangle((S["pos"] - .5, -.5), 1, NR, fill=False,
                            edgecolor=ORANGE, lw=4.0, zorder=5))
    t = S["traj"]
    if len(t) > 1:
        axM.plot(t, [-0.75] * len(t), "-", color=ORANGE, lw=3.0,
                 clip_on=False, zorder=6)
    axM.plot(t, [-0.75] * len(t), "o", color=ORANGE, ms=9,
             clip_on=False, zorder=7)
    axM.set_title("一边改进方法，一边重新决定该信哪把尺子　　　空格走一轮　r 重来　t 看答案",
                  fontsize=16, color=NAVY, fontweight="bold", pad=18)

    tv = 100.0 * (TRUTH - TRUTH.min()) / (TRUTH.max() - TRUTH.min())
    if S["truth"]:
        axT.imshow(tv.reshape(1, -1), cmap="Oranges", vmin=0, vmax=100, aspect="auto")
        for j in range(NA):
            axT.text(j, 0, "%.0f" % tv[j], ha="center", va="center",
                     fontsize=10, color="#3A1600", fontweight="bold")
        for sp in axT.spines.values():
            sp.set_edgecolor(ORANGE); sp.set_linewidth(1.8)
    else:
        axT.text(.5, .5, "答案封着呢　按 t 揭开", ha="center", va="center",
                 fontsize=11.5, color=GREY, transform=axT.transAxes)
        for sp in axT.spines.values():
            sp.set_visible(False)
    axT.set_yticks([]); axT.set_xticks(range(NA))
    axT.set_xticklabels(["方法%d" % (j + 1) for j in range(NA)], fontsize=11.5)
    axT.tick_params(length=0); axT.set_xlim(axM.get_xlim())

    y = np.arange(NR)
    axW.barh(y, S["w"], color=[ORANGE if S["just"][i] else
                               (TEAL if BSEAL[i] >= .9 else "#B9C4D0") for i in range(NR)],
             height=.68)
    for i in range(NR):
        axW.text(1.02, i, "%.3f" % S["w"][i], va="center", fontsize=9.5,
                 color=NAVY if S["w"][i] > .4 else GREY)
    axW.set_yticks(y)
    axW.set_yticklabels(["尺子%-2d 对照上不乱说 %.0f%%" % (i + 1, BSEAL[i] * 100) for i in range(NR)],
                        fontsize=9.5)
    axW.invert_yaxis(); axW.set_xlim(0, 1.18); axW.set_xticks([0, .5, 1])
    axW.set_title("每把尺子现在有多少话语权（橙＝本轮刚被降）", fontsize=13, color=NAVY,
                  fontweight="bold", pad=10)
    for s_ in ("top", "right"):
        axW.spines[s_].set_visible(False)
    axW.tick_params(length=0)

    if S["log"] is None:
        axB.text(0, .72, "起点：方法1，十四把尺子话语权相同", fontsize=17,
                 color=NAVY, fontweight="bold", transform=axB.transAxes)
        axB.text(0, .30, "按空格走一轮 —— 尺子们投票决定下一步往哪走，"
                         "同时回头看谁在「什么都没修」的对照上也说自己变好了", fontsize=14,
                 color=GREY, transform=axB.transAxes)
    else:
        h, b, c = S["log"]
        axB.text(0, .74, h, fontsize=19, color=c, fontweight="bold",
                 transform=axB.transAxes)
        axB.text(0, .38, b, fontsize=15, color=NAVY, transform=axB.transAxes)
        if S["done"] and S["step"]:
            axB.text(0, .02, "停住了 —— 还在说「往前」的那几把，已经被我们自己降权了。"
                             "尺子变了，决策就变了。",
                     fontsize=16.5, color=ORANGE, fontweight="bold",
                     transform=axB.transAxes)
    fig.canvas.draw_idle()

def on_key(ev):
    if ev.key == " ":
        step(); draw()
    elif ev.key == "r":
        S.update({"pos": 0, "w": np.ones(NR), "traj": [0], "step": 0,
                  "log": None, "just": np.zeros(NR, bool), "done": False})
        draw()
    elif ev.key == "t":
        S["truth"] = not S["truth"]; draw()
    elif ev.key == "q":
        plt.close(fig)

fig.canvas.mpl_connect("key_press_event", on_key)
draw()
print("%d 把尺子 × %d 个方法　数据源 %s" % (NR, NA, SRC))
print("空格走一轮；r 重来；t 真值；q 退出")
plt.show()
