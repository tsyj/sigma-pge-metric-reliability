#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E73 shortcut_theorem · PREREG §7.7 三张图（封存后，纯描述，只读输入，只写本目录 FIG*.png）。
输入：E71_PILOT_AXES.npz（纬向，样本内）、E71_FINAL_AXES.npz（45°，E71M 落盘只读）、E73_INSAMPLE.json、E73_SHORTCUT_MAP.json、verdict.json、E73X_POSTHOC.json。
"""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import rankdata

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK JP", "Noto Sans CJK SC", "Noto Sans CJK TC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
ENV = "/data/xinyuan/GOAI_ai4s_env"; FIN = f"{ENV}/e71_innov/shortcut_theorem/final"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GRAY, INK, INK2, SURF = "#b5b4ae", "#0b0b0b", "#52514e", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": "#c9c8c2",
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "grid.color": "#e6e5e0", "grid.linewidth": 0.6})
ins = json.load(open(f"{FIN}/E73_INSAMPLE.json")); m = json.load(open(f"{FIN}/E73_SHORTCUT_MAP.json"))
v = json.load(open(f"{FIN}/verdict.json")); px = json.load(open(f"{FIN}/E73X_POSTHOC.json"))
z = np.load(f"{ENV}/e71_innov/multienv_metrology/final/E71_FINAL_AXES.npz", allow_pickle=True)
A, B, D, G = z["A_z"], z["B_z"], z["D_z"], z["G"]; Am, Bm = z["A_m"], z["B_m"]; A45, B45 = z["A_45"], z["B_45"]
num = z["num"].astype(str); den = z["den"].astype(str)
S_A = (A >= 0.7) & (B >= 0.9); esc = (A >= 0.9) & (B >= 0.9)
gate45 = (A45 >= 0.7) & (B45 >= 0.9); triple = S_A & (Am >= 0.7) & (Bm >= 0.9) & gate45
QUAL = "受控 σ 坐标伪流环境族（风向×VISC2 主导扫描）；N=15376 名义候选"

def zr(x):
    r = rankdata(x); return (r - r.mean()) / r.std()

# ---------- FIG1：控 D 前后 A–B（纬向，样本内） ----------
ra, rb, rd = zr(A), zr(B), zr(D)
res = lambda r: r - (r @ rd) / (rd @ rd) * rd
fig, axs = plt.subplots(1, 2, figsize=(11, 4.8))
pt = ins["partial_trio"]
for ax, (x, y, ttl) in zip(axs, [(ra, rb, "控 D 之前：A 与 B 的秩（标准化）\nρ_平均秩 = %.4f（argsort 主口径 %.4f）" % (pt["raw_avgrank"], ins["anchors"]["rho_AB_argsort"])),
                                  (res(ra), res(rb), "扣掉 signed-D 的秩之后：残差 A 与残差 B\n偏 ρ = %.3f；对照：扣 |D| 偏 ρ = %.4f（不动）" % (pt["partial_given_D"], pt["partial_given_absD"]))]):
    ax.scatter(x[~S_A], y[~S_A], s=3, c=GRAY, alpha=0.25, linewidths=0, rasterized=True, label="其余候选")
    ax.scatter(x[S_A & ~esc], y[S_A & ~esc], s=10, c=BLUE, alpha=0.8, linewidths=0, label="S_A 标准门（A≥0.7∧B≥0.9，n=%d）" % S_A.sum())
    ax.scatter(x[esc], y[esc], s=30, facecolors="none", edgecolors=ORANGE, linewidths=1.6, label="逃逸者（A≥0.9∧B≥0.9，n=%d，全 G=0）" % esc.sum())
    ax.set_title(ttl, fontsize=10.5, loc="left"); ax.grid(True)
axs[0].set_xlabel("A_z 的秩（标准化）"); axs[0].set_ylabel("B_z 的秩（标准化）")
axs[1].set_xlabel("A_z 秩 − 其在 D_z 秩上的投影"); axs[1].set_ylabel("B_z 秩 − 其在 D_z 秩上的投影")
h, l = axs[0].get_legend_handles_labels(); leg = fig.legend(h, l, fontsize=8.5, loc="upper left", bbox_to_anchor=(0.01, 0.935), ncol=3, frameon=False, markerscale=2)
for lh in leg.legend_handles: lh.set_alpha(1)
fig.suptitle("纬向：A–B 互斥在扣掉介质量 D 后掉七成——中介一致性检查，非中介证明（观察性＋共线）", fontsize=12, x=0.01, ha="left")
fig.text(0.01, 0.01, QUAL + "；偏相关用平均秩口径（PREREG §2 例外）  [E73_INSAMPLE.json#/partial_trio, #/anchors]", fontsize=7, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 0.89)); fig.savefig(f"{FIN}/FIG1_partial_AB_zonal.png", dpi=200); plt.close(fig)

# ---------- FIG2：反号象限 A_z × A_45，模型符号着色 ----------
c45 = m["c_45"]["argsort"]; Ahat = c45 * D
conf = np.abs(D) >= 0.3
miss = conf & ((np.sign(A45) != np.sign(Ahat)) | (A45 == 0))
fig, ax = plt.subplots(figsize=(7.2, 6.4))
ax.scatter(A[~conf], A45[~conf], s=4, c=BLUE, alpha=0.35, linewidths=0, rasterized=True, label="|D_z|<0.3：模型不下符号注（n=%d）" % (~conf).sum())
ax.scatter(A[conf & ~miss], A45[conf & ~miss], s=3, c=GRAY, alpha=0.3, linewidths=0, rasterized=True, label="|D_z|≥0.3 且符号命中（n=%d）" % (conf & ~miss).sum())
ax.scatter(A[miss], A45[miss], s=12, c=ORANGE, alpha=0.9, linewidths=0, label="|D_z|≥0.3 但符号未中（n=%d）" % miss.sum())
for t in (0,): ax.axhline(t, color="#8d8c86", lw=0.8); ax.axvline(t, color="#8d8c86", lw=0.8)
for t in (0.7,): ax.axvline(t, color="#8d8c86", lw=0.8, ls="--"); ax.axhline(t, color="#8d8c86", lw=0.8, ls="--")
q = m["descriptive"]["quadrants_at_0p7"]
ax.text(0.72, -0.95, "A_z≥0.7 中 A_45<0：%d/%d\n变节率 %.4f（引 E71M P6 判定，不重复设赌）" % (q["pn"], q["pn"] + q["pp"] + int(((A >= 0.7) & (A45 >= 0) & (A45 < 0.7)).sum()), q["turncoat_rate"]), fontsize=8, color=INK2)
ax.set_xlabel("A_z（纬向，已知）"); ax.set_ylabel("A_45（45° 留出）"); ax.grid(True)
ax.set_title("45° 反号象限：符号场由 sign(c_45·D_z) 预测\nP2 命中率 %.4f（n=%d，门槛 0.90，中）；c_45=%.4f（n_45=%d 条真值）" % (m["P2"]["hit_rate"], m["P2"]["n_conf"], c45, m["n_45"]), fontsize=10.5, loc="left")
leg = ax.legend(fontsize=8, loc="upper left", frameon=False, markerscale=2.5)
for lh in leg.legend_handles: lh.set_alpha(1)
fig.text(0.01, 0.01, QUAL + "  [E73_SHORTCUT_MAP.json#/P2, #/descriptive/quadrants_at_0p7; verdict.json#/predictions/P2]", fontsize=6.5, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(f"{FIN}/FIG2_sign_quadrant_45.png", dpi=200); plt.close(fig)

# ---------- FIG3：残差榜 ----------
absr = np.abs(A45 - Ahat)
order = np.argsort(-absr); pos = np.empty_like(order); pos[order] = np.arange(order.size)
fig, axs = plt.subplots(1, 2, figsize=(12, 4.9), gridspec_kw=dict(width_ratios=[1.35, 1]))
ax = axs[0]
ax.plot(np.arange(absr.size), absr[order], color="#8d8c86", lw=1.4)
for mask, col, lab, yy in [(S_A, BLUE, "S_A（n=%d）" % S_A.sum(), -0.06), (triple, AQUA, "三向幸存（n=%d）" % triple.sum(), -0.12), (esc, ORANGE, "逃逸者（n=%d）" % esc.sum(), -0.18)]:
    ax.scatter(pos[mask], np.full(mask.sum(), yy), marker="|", s=60, c=col, linewidths=1.0, label=lab)
ax.set_xlabel("残差榜名次（|r| 从大到小，全体 %d）" % absr.size); ax.set_ylabel("|r| = |A_45 − c_45·D_z|")
ax.set_ylim(-0.24, float(absr.max()) + 0.05); ax.grid(True, axis="y"); ax.legend(fontsize=8, frameon=False, loc="upper right")
ax.set_title("45° 残差榜：头部全为 G=0 比值型（top-20 见 map）\n|r| 中位 %.4f、P95 %.4f、≤0.1 占比 %.4f" % (m["P3"]["q_absr_all_p50_p95"][0], m["P3"]["q_absr_all_p50_p95"][1], m["P3"]["frac_absr_within_0p1"]), fontsize=10.5, loc="left")
ax = axs[1]
groups = [("S_A∧45°存活", S_A & gate45, BLUE), ("S_A∧45°阵亡", S_A & ~gate45, GRAY), ("三向幸存", triple, AQUA), ("其余全体", ~triple, GRAY)]
data = [absr[g] for _, g, _ in groups]
bp = ax.boxplot(data, widths=0.55, showfliers=False, patch_artist=True, medianprops=dict(color=INK, lw=1.6))
for patch, (_, _, col) in zip(bp["boxes"], groups): patch.set_facecolor(col); patch.set_alpha(0.45); patch.set_edgecolor("#8d8c86")
ax.set_xticks(range(1, 5)); ax.set_xticklabels(["%s\nn=%d\n中位 %.3f" % (n, g.sum(), np.median(absr[g])) for n, g, _ in groups], fontsize=8.5)
ax.set_ylabel("|r|"); ax.grid(True, axis="y")
P = v["predictions"]
ax.set_title("P3a（1 vs 2）：p=%.2e，中\nP3b（3 vs 4）：p=%.3f，不中（被推翻，原样保留）" % (P["P3a"]["stat"], P["P3b"]["stat"]), fontsize=10.5, loc="left")
fig.suptitle("混杂申报：门选中者 A_45∈[0.7,1] 与 |r| 机械耦合；结论读作描述，非因果", fontsize=10, x=0.01, ha="left", color=INK2)
fig.text(0.01, 0.01, QUAL + "  [E73_SHORTCUT_MAP.json#/P3, #/descriptive/top20_residual; verdict.json#/predictions/P3a,P3b; E73X_POSTHOC.json#/c_P3b_decomposition]", fontsize=6.5, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 0.95)); fig.savefig(f"{FIN}/FIG3_residual_board_45.png", dpi=200); plt.close(fig)
print("FIGS_DONE")
