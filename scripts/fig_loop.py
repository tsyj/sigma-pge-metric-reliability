#!/usr/bin/env python
"""E42 完整闭环图 —— 发现问题 → 诊断机理 → 设计修复 → 实测有效。

左：只换一个目标指标，刷分率 90% → 7.5%
右：A2 各轮的地形分布 —— Agent 自己留在了真问题上

单轴、无双纵轴；文字一律 ink token。
"""
import glob, json, os
from collections import Counter
import numpy as np
import sys
sys.path.insert(0, "/data/xinyuan/GOAI_ai4s_env/scripts")
from figstyle import paper_style, panel, BLUE, GRAY, RED, GREEN, TEAL, ORANGE
import matplotlib.pyplot as plt
paper_style()
SURF = "#ffffff"; INK = "black"; INK2 = "black"
GRID = "#dddddd"; MUTED = "#777777"
C_OLD, C_NEW = GRAY, RED
C_BATHY = {"r26steep": BLUE, "mit": TEAL, "flat": ORANGE}

E = "/data/xinyuan/GOAI_ai4s_env"


def stats(cond):
    fs = ts = nf = n = 0
    per = []
    for f in sorted(glob.glob(f"{E}/ledger/agent_llm_{cond}_*.json")):
        d = json.load(open(f))
        if d.get("condition") != cond:
            continue
        n += 1
        b = [s["action"].get("bathy") for s in d["log"]]
        fs += b.count("flat"); ts += len(b)
        ba = (d.get("final") or {}).get("best_action") or {}
        nf += (ba.get("bathy") == "flat")
        per.append((d["seed"], Counter(b), ba.get("bathy")))
    return dict(flat=fs, tot=ts, n_flat_claim=nf, n=n, per=per)


A, A2 = stats("A"), stats("A2")

fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.2, 4.2),
                             gridspec_kw={"width_ratios": [0.62, 1.25]})
for a in (a1, a2):
    a.set_axisbelow(True)

# ---------- 左：刷分率 ----------
fa, f2 = 100 * A["flat"] / A["tot"], 100 * A2["flat"] / A2["tot"]
a1.bar([0, 1], [fa, f2], color=[GRAY, GREEN], width=0.45)
for i, v in enumerate((fa, f2)):
    a1.text(i, v + 2.5, f"{v:.1f}", ha="center", fontsize=11.5)
a1.set_xticks([0, 1])
a1.set_xticklabels(["以旧指标为目标", "以新指标为目标"])
a1.set_ylabel("平底步数占比 (%)")
a1.set_ylim(0, 100)
panel(a1, "a")

# ---------- 右：A2 各轮地形分布 ----------
order = ["r26steep", "mit", "flat"]
ys = np.arange(len(A2["per"]))
left = np.zeros(len(A2["per"]))
for b in order:
    w = np.array([p[1].get(b, 0) for p in A2["per"]], dtype=float)
    a2.barh(ys, w, left=left, height=0.55, color=C_BATHY[b],
            edgecolor="white", lw=1.2,
            label={"r26steep": "陡海山", "mit": "第二座海山", "flat": "平底"}[b])
    for i, (l_, w_) in enumerate(zip(left, w)):
        if w_ >= 1:
            a2.text(l_ + w_ / 2, i, f"{int(w_)}", ha="center", va="center",
                    fontsize=10.5, fontweight="bold",
                    color="white" if b == "r26steep" else "#333333")
    left += w
a2.set_yticks(ys)
a2.set_yticklabels([f"种子 {p[0]}" for p in A2["per"]])
a2.set_xlim(0, 10)
a2.set_xlabel("步数（每轮共 10 步）")
panel(a2, "b")
a2.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
a2.invert_yaxis()

fig.suptitle("只换一个目标指标，刷分行为消失",
             x=0.01, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = f"{E}/ledger/fig_loop.png"
fig.savefig(out, bbox_inches="tight")
print(out)
print(f"  A : flat {A['flat']}/{A['tot']} = {fa:.1f}%,  声称最优在flat {A['n_flat_claim']}/{A['n']}")
print(f"  A2: flat {A2['flat']}/{A2['tot']} = {f2:.1f}%,  声称最优在flat {A2['n_flat_claim']}/{A2['n']}")
