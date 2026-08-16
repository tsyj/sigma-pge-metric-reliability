#!/usr/bin/env python
"""σ 坐标 vs z 坐标真值 —— 论文风格版（20260816 重画）。
(a) |U|max 时间序列（对数轴）  (b) ROMS/真值 比值
实验条件与结论全部移入正文图注，图上只留数据。
"""
import sys
import numpy as np
sys.path.insert(0, "/data/xinyuan/GOAI_ai4s_env/scripts")
from figstyle import paper_style, panel, BLUE, RED, GRAY
import matplotlib.pyplot as plt
from netCDF4 import Dataset
from mitgcm import read_field, iters

paper_style()

P = "/data/xinyuan/GOAI_ai4s_env/runs/"
M = "/data/xinyuan/GOAI_ai4s_env/truth/sw_viscAz_1pEm5"   # 垂向黏性匹配的真值（撤回 #6 后）

d = Dataset(P + "e2_7fc7950d63bc/out_his.nc")   # clean v4, VISC2=50, NTIMES=25920
ts = np.asarray(d["ocean_time"][:]) / 86400.0
t = ts - ts[0] + (ts[1] - ts[0])
u = np.asarray(d["u"][:]); d.close()
it = iters("U", M); tm = np.array([i * 30 / 86400 for i in it])

T, RM, RR, MM, MR = [], [], [], [], []
for k in range(len(t)):
    j = int(np.argmin(np.abs(tm - t[k])))
    if abs(tm[j] - t[k]) > 0.13:
        continue
    U = read_field("U", it[j], M)
    T.append(t[k])
    RM.append(np.abs(u[k]).max() * 100); RR.append(np.sqrt((u[k] ** 2).mean()) * 100)
    MM.append(np.abs(U).max() * 100);    MR.append(np.sqrt((U ** 2).mean()) * 100)
T, RM, RR, MM, MR = map(np.array, (T, RM, RR, MM, MR))

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.0, 4.3))

a1.plot(T, RM, "-o", color=RED, lw=2, ms=6, mec="white", mew=0.8, label="σ 坐标")
a1.plot(T, MM, "-s", color=BLUE, lw=2, ms=6, mec="white", mew=0.8, label="z 坐标（真值）")
a1.set_xlabel("时间（天）")
a1.set_ylabel("|U|max (cm/s)")
a1.legend(loc="center right")
panel(a1, "a")

a2.plot(T, RM / MM, "-o", color=RED, lw=2, ms=6, mec="white", mew=0.8, label="|U|max / 真值")
a2.plot(T, RR / MR, "--s", color="#4DBBD5", lw=2, ms=6, mec="white", mew=0.8, label="|U|rms / 真值")
a2.set_xlabel("时间（天）")
a2.set_ylabel("σ 坐标 / 真值（倍数）")
a2.legend(loc="upper left")
panel(a2, "b")

fig.suptitle("σ 坐标凭空造出比真实流场大一个量级以上的伪流",
             x=0.01, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = "/data/xinyuan/GOAI_ai4s_env/ledger/fig_truth_sigma_vs_z.png"
fig.savefig(out, bbox_inches="tight")
print("图:", out)
print(f"{'天':>5} | {'ROMS max':>9} {'真值 max':>9} {'倍数':>7}")
for i in range(len(T)):
    print(f"{T[i]:5.2f} | {RM[i]:9.2f} {MM[i]:9.2f} {RM[i]/MM[i]:6.1f}×")
