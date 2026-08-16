#!/usr/bin/env python
"""代理/真值分歧图 —— 审查修订版（20260816 v2）。
a: 代理读数随探索步序一路下降   b: 代理 vs 真实误差随黏性的分歧
"""
import json
import sys
import numpy as np
sys.path.insert(0, "/data/xinyuan/GOAI_ai4s_env/scripts")
from figstyle import paper_style, panel, BLUE, RED
import matplotlib.pyplot as plt

paper_style()

ENV = "/data/xinyuan/GOAI_ai4s_env"
d = json.load(open(f"{ENV}/ledger/agent_bisect_s0.json"))
log = [s for s in d["log"] if s["obs"].get("valid")]
step = np.array([s["i"] for s in log])
visc = np.array([s["action"]["VISC2"] for s in log])
proxy = np.array([s["obs"]["deep_rms_800"] for s in log])
truth = np.array([s["hidden_grade"]["score"] for s in log])

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.0, 4.2))

# a: 智能体看到的代理读数随步序
a1.plot(step, proxy, "-o", color=BLUE, lw=2, ms=6, mec="white", mew=0.8)
a1.set_xlabel("探索步序")
a1.set_ylabel("代理指标读数 (cm/s)")
a1.set_xticks(step)
panel(a1, "a")

# b: 代理 vs 真实误差
o = np.argsort(visc)
a2.plot(visc[o], proxy[o], "-o", color=BLUE, lw=2, ms=6, mec="white", mew=0.8,
        label="代理指标（智能体可见）")
a2.plot(visc[o], truth[o], "-s", color=RED, lw=2, ms=6, mec="white", mew=0.8,
        label="真实误差（智能体不可见）")
a2.fill_between(visc[o], proxy[o], truth[o], where=proxy[o] < truth[o],
                color=BLUE, alpha=0.10, interpolate=True, label="真实误差高于代理的差距")
a2.set_xlabel("横向黏性 (m²/s)")
a2.set_ylabel("均方根流速 (cm/s)")
a2.set_xticks([0, 500, 1000, 1500, 2000])
a2.legend(loc="upper right")
panel(a2, "b")

fig.suptitle("代理读数一路变好，真实误差降得远比它慢——指标让人以为还在进步",
             x=0.01, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = f"{ENV}/ledger/fig_agent_divergence.png"
fig.savefig(out, bbox_inches="tight")
print(out)
