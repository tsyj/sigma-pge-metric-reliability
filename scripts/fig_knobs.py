#!/usr/bin/env python
"""E28/E30 四旋钮图 —— 两个失效模式，一张图。

① 三个旋钮压代理指标不动真值，一个旋钮直接改真值（代理指标看不出区别）
② 深层 rms 的误差占比在四个旋钮上全程 100%；|U|max 的会崩
③ 误差占比自己的失效模式：AKV_BAK 把它推向「更纯」，其实是真值被缩小了

单轴、无双纵轴；文字一律 ink token。
"""
import json
import numpy as np
import sys
sys.path.insert(0, "/data/xinyuan/GOAI_ai4s_env/scripts")
from figstyle import paper_style, panel, BLUE, GRAY, RED, GREEN, TEAL
import matplotlib.pyplot as plt
paper_style()
SURF = "#ffffff"; INK = "black"; INK2 = "black"
GRID = "#dddddd"; MUTED = "#777777"
C = {"VISC2": BLUE, "VISC4": GREEN, "TNU2": GRAY, "AKV_BAK": RED}
LBL = {"VISC2": "横向黏性", "VISC4": "高阶横向黏性",
       "TNU2": "温度扩散", "AKV_BAK": "垂向黏性"}
ORDER = ["VISC2", "VISC4", "TNU2", "AKV_BAK"]

E = "/data/xinyuan/GOAI_ai4s_env"
A = json.load(open(f"{E}/ledger/knob_analysis.json"))
# 每行: [参数值, ROMS, 真值, 代理降幅, 误差占比, 真信号变动]
UM, DP = A["u_max"], A["deep_rms_800"]


def clean(rows):
    return [r for r in rows if all(np.isfinite(x) for x in r[1:])]


fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.2))
for a in ax:
    a.set_axisbelow(True)

# ---------- ① 代理降幅 vs 真信号破坏 ----------
a1 = ax[0]
for k in ORDER:
    r = clean(UM[k])
    xy = sorted((v[3] * 100, v[5] * 100) for v in r if v[3] * 100 > 0.3)
    xs = [p[0] for p in xy]; ys = [p[1] for p in xy]
    a1.plot(xs, ys, "-o", color=C[k], lw=2.0, ms=5,
            label=LBL[k], zorder=3 if k == "AKV_BAK" else 2)
a1.set_xscale("log")
a1.set_xticks([1, 3, 10, 30, 100])
a1.set_xticklabels(["1", "3", "10", "30", "100"])
a1.axhline(0, color=MUTED, lw=1.0, ls="--")
a1.set_xlabel("代理指标被压低的幅度 (%)")
a1.set_ylabel("真信号破坏幅度 (%)")
panel(a1, "a")
_h, _l = a1.get_legend_handles_labels()
_ord = [_l.index("垂向黏性")] + [i for i, x in enumerate(_l) if x != "垂向黏性"]
a1.legend([_h[i] for i in _ord], [_l[i] for i in _ord],
          loc="center right", bbox_to_anchor=(1.0, 0.55))

# ---------- ② 误差占比：两个指标的对比 ----------
a2 = ax[1]
LS = {"VISC2": "-", "VISC4": "--", "TNU2": ":", "AKV_BAK": "-"}
for k in ORDER:
    r = clean(UM[k])
    xy = sorted((v[3] * 100, v[4] * 100) for v in r if v[3] * 100 > 0.3)
    a2.plot([p[0] for p in xy], [p[1] for p in xy], LS[k], color=C[k], lw=1.8,
            marker="o", ms=4.5, alpha=0.95)
a2.set_xscale("log")
a2.set_xticks([1, 3, 10, 30, 100])
a2.set_xticklabels(["1", "3", "10", "30", "100"])

a2.axhline(100, color="#555555", lw=1.6, ls="--")
a2.set_ylim(55, 104)
a2.set_xlabel("代理指标被压低的幅度 (%)")
a2.set_ylabel("误差占比 (%)")
panel(a2, "b")

# ---------- ③ 误差占比自己的失效模式 ----------
a3 = ax[2]
r = clean(UM["AKV_BAK"])
xv = [v[0] for v in r]
a3.plot(xv, [v[4] * 100 for v in r], "-o", color="#4DBBD5", lw=2.2, ms=6,
        label="误差占比")
a3.plot(xv, [v[5] * 100 for v in r], "-s", color="#4D4D4D", lw=2.0, ms=5.5,
        label="真信号破坏幅度")
a3.set_xscale("log")
a3.set_xticks([1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1e0])
a3.set_xticklabels(["$10^{-5}$", "$10^{-4}$", "$10^{-3}$", "$10^{-2}$", "$10^{-1}$", "$10^{0}$"])
a3.set_xlabel("垂向黏性 (m²/s)")
a3.set_ylabel("幅度 (%)")
panel(a3, "c")
a3.set_ylim(-8, 115)
a3.set_yticks([0, 20, 40, 60, 80, 100])
a3.legend(loc="center left", bbox_to_anchor=(0.02, 0.62))

fig.suptitle("四个旋钮都能压低代理指标，只有真值能分出谁在真解决问题",
             x=0.01, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = f"{E}/ledger/fig_knobs.png"
fig.savefig(out, bbox_inches="tight")
print(out)
