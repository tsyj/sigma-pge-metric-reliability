#!/usr/bin/env python
"""新旧指标对比 —— 论文风格重设计（20260816）。

按两个百分制分值呈现，线性坐标，一目了然：
  排序能力得分 = 实例内与隐藏技巧评分的秩相关绝对值 × 100
  抗刷分得分   = 同参数 (陡海山, 平底) 配对上不被"换地形"刷穿的比例 × 100
数据出处 ledger/metric_search.json（E40，agent_metric_selftest.json 已独立复核）：
  旧指标 deep_rms_800: |ρ|=0.963 → 96 分；配对 0.000 → 0 分
  新指标 uv_ratio    : |ρ|=0.923 → 92 分；配对 1.000 → 100 分
"""
import sys
import numpy as np
sys.path.insert(0, "/data/xinyuan/GOAI_ai4s_env/scripts")
from figstyle import paper_style, BLUE, GRAY, RED
import matplotlib.pyplot as plt

paper_style()

scores_old = [96, 0]     # deep_rms_800
scores_new = [92, 100]   # uv_ratio

fig, ax = plt.subplots(figsize=(5.4, 4.2))
x = np.arange(2) * 0.78; w = 0.26
ax.bar(x - w / 2, scores_old, w, color=GRAY, label="旧指标")
ax.bar(x + w / 2, scores_new, w, color=RED, label="新指标")
for i in range(2):
    ax.text(x[i] - w / 2, scores_old[i] + 2.5, f"{scores_old[i]}",
            ha="center", fontsize=13.5, fontweight="bold")
    ax.text(x[i] + w / 2, scores_new[i] + 2.5, f"{scores_new[i]}",
            ha="center", fontsize=13.5, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(["排序能力", "抗刷分"])
ax.set_ylabel("得分")
ax.set_ylim(0, 118)
ax.set_yticks([0, 20, 40, 60, 80, 100])
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=2)

fig.suptitle("新指标：排序能力几乎不变，抗刷分从 0 到 100",
             x=0.01, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.95])
out = "/data/xinyuan/GOAI_ai4s_env/ledger/fig_metric.png"
fig.savefig(out, bbox_inches="tight")
print(out)
