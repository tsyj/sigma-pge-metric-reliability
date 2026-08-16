#!/usr/bin/env python
"""E36/E37 LLM 对照矩阵 —— 论文风格版（20260816 重画）。
(a) 各条件耗在 flat 上的步数占比  (b) 两类质疑的轮数  (c) 三条刷分路径的倍数
条件定义与结论全部移入正文图注。
"""
import json
import sys
import numpy as np
sys.path.insert(0, "/data/xinyuan/GOAI_ai4s_env/scripts")
from figstyle import paper_style, panel, BLUE, GRAY, RED, TEAL
import matplotlib.pyplot as plt

paper_style()

E = "/data/xinyuan/GOAI_ai4s_env"
rows = json.load(open(f"{E}/ledger/llm_matrix.json"))
CONDS = ["A", "B", "C"]

fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(13.5, 4.2))

# (a) flat 步数占比
frac = []
for c in CONDS:
    g = [r for r in rows if r["cond"] == c]
    frac.append(100.0 * sum(r["n_flat"] for r in g) / sum(r["n"] for r in g))
a1.bar(range(3), frac, width=0.55, color=BLUE)
for i, v in enumerate(frac):
    a1.text(i, v + 2.5, f"{v:.1f}", ha="center", fontsize=11.5, fontweight="bold")
a1.set_xticks(range(3)); a1.set_xticklabels(["条件 A", "条件 B", "条件 C"])
a1.set_ylabel("耗在平底对照上的步数占比 (%)")
a1.set_ylim(0, 100)
panel(a1, "a")

# (b) 两类质疑
t1, t2, ntot = [], [], []
for c in CONDS:
    g = [r for r in rows if r["cond"] == c]
    ntot.append(len(g))
    t2.append(sum(1 for r in g if r["spontaneous"]))
    t1.append(sum(1 for r in g if not r["spontaneous"] and "噪声" in str(r["s1"])))
x = np.arange(3); w = 0.36
a2.bar(x - w / 2, t1, w, color=GRAY, label="质疑测量精度")
a2.bar(x + w / 2, t2, w, color=RED, label="质疑指标本身")
for i in range(3):
    a2.text(i - w / 2, t1[i] + 0.14, f"{t1[i]}/{ntot[i]}", ha="center", fontsize=11,
            fontweight="bold", color=GRAY if t1[i] == 0 else "#1a1a1a")
    a2.text(i + w / 2, t2[i] + 0.14, f"{t2[i]}/{ntot[i]}", ha="center", fontsize=11,
            fontweight="bold", color=RED if t2[i] == 0 else "#1a1a1a")
a2.set_xticks(x)
a2.set_xticklabels([f"条件 A\n({ntot[0]} 轮)", f"条件 B\n({ntot[1]} 轮)", f"条件 C\n({ntot[2]} 轮)"])
a2.set_ylabel("出现质疑的轮数")
a2.set_ylim(0, 5.5)
a2.set_yticks(range(0, 6))
a2.spines["left"].set_bounds(0, 5)
a2.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), ncol=2)
panel(a2, "b")

# (c) 三条刷分路径（同参数配对口径，20260816 复核）
#   换地形: 32 组配对中位 224 (54–318)
#   增大黏性: VISC2 50→30000, 8.674/0.1399 = 62
#   缩短积分: 5 组配对中位 27.8 (27.7–33.6) → 28
gain = [224, 62, 28]
a3.bar(range(3), gain, width=0.55, color=TEAL)
for i, v in enumerate(gain):
    a3.text(i, v + 7, f"{v}×", ha="center", fontsize=12, fontweight="bold")
a3.set_xticks(range(3))
a3.set_xticklabels(["换地形", "增大黏性", "缩短积分"])
a3.set_ylabel("代理指标改善倍数")
a3.set_ylim(0, 250)
panel(a3, "c")

fig.suptitle("目标怎么说，决定智能体怎么作弊",
             x=0.01, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = f"{E}/ledger/fig_llm.png"
fig.savefig(out, bbox_inches="tight")
print(out)
n_abc = len([r for r in rows if r["cond"] in CONDS])
print(f"  轮数 {n_abc}; 刷分率 A/B/C = {frac[0]:.1f}/{frac[1]:.1f}/{frac[2]:.1f}%")
print(f"  S1  A/B/C = {t2[0]}/{ntot[0]}, {t2[1]}/{ntot[1]}, {t2[2]}/{ntot[2]}")
