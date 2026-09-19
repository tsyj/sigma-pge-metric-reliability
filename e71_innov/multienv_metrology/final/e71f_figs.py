#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E71M 三张图（纯呈现，不参与判定；PREREG §7.7）。数据只取 E71_FINAL_RESULTS.json / verdict.json。
2026-09-17更正：D2原改述有误，以DEVIATIONS D3/D4为准；只改呈现，另名输出。"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

FIN = '/data/xinyuan/GOAI_ai4s_env/e71_innov/multienv_metrology/final'
R = json.load(open(f'{FIN}/E71_FINAL_RESULTS.json'))
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK JP', 'Noto Sans CJK SC', 'AR PL UMing CN', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

QUAL = '限定：经向与45°为同一批22个run的四旋钮单变扫描（VISC2 7、VISC4 7、TNU2 7、AKV_BAK 1）。\n相关级高收敛部分来自受控扫描设计；k/G仅限本强迫场景族。【2026-09-17复算更正，原图停用】'

# ---------- 图1 6×6 MTMM 热图 ----------
M = np.array(R['M1_mtmm6']['matrix']); Mt = np.array(R['M1_mtmm6']['matrix_ties'])
names = ['A 纬向', 'B 纬向', 'A 经向', 'B 经向', 'A 45°', 'B 45°']
fig, ax = plt.subplots(figsize=(7.6, 7.2))
im = ax.imshow(M, cmap='RdBu_r', vmin=-1, vmax=1)
for i in range(6):
    for j in range(6):
        s = '%+.2f' % M[i, j]
        if abs(M[i, j] - Mt[i, j]) >= 0.005 and i != j:
            s += '\n(%+.2f)' % Mt[i, j]
        ax.text(j, i, s, ha='center', va='center', fontsize=9,
                color='white' if abs(M[i, j]) > 0.55 else 'black')
ax.set_xticks(range(6)); ax.set_yticks(range(6))
ax.set_xticklabels(names, rotation=30, ha='right'); ax.set_yticklabels(names)
for k in (1.5, 3.5):
    ax.axhline(k, color='k', lw=1.2); ax.axvline(k, color='k', lw=1.2)
ax.set_title('MTMM 6×6：特质 {A 排得准, B 抗刷分} × 方法 {纬向, 经向, 45°}\n'
             '主口径 argsort 秩；括号=平均秩版（差 ≥0.005 时同框，PREREG §2）', fontsize=11)
fig.colorbar(im, ax=ax, shrink=0.8, label='spearman ρ')
fig.text(0.02, 0.012, QUAL + '  [E71_FINAL_RESULTS.json → M1_mtmm6]', fontsize=7, color='0.35')
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(f'{FIN}/FIG1_MTMM6_corrected_20260917.png', dpi=300, bbox_inches="tight")
plt.close(fig)

# ---------- 图2 三层塌方图 ----------
tl = R['three_layer']
labels = ['相关级\nρ(A,A)', '机制级（扣 D）\nρ(A⊥,A⊥)', '决策级（已知派生）\nκ(门,门)', '决策级（已知派生）\nJaccard']
zm = [tl['z_m_pilot_frame']['correlation'], tl['z_m_pilot_frame']['mechanism'],
      tl['z_m_pilot_frame']['decision_kappa'], tl['z_m_pilot_frame']['decision_jaccard']]
z45 = [tl['z_45']['correlation'], tl['z_45']['mechanism'],
       tl['z_45']['decision_kappa'], tl['z_45']['decision_jaccard']]
x = np.arange(4); w = 0.36
fig, ax = plt.subplots(figsize=(8.4, 5.2))
b1 = ax.bar(x - w / 2, zm, w, label='纬向–经向（试点对照框）', color='#7f9fc4')
b2 = ax.bar(x + w / 2, z45, w, label='纬向–45°（封存后留出验证域）', color='#c46f6f')
for b in list(b1) + list(b2):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.015, '%.3f' % b.get_height(),
            ha='center', fontsize=9)
ax.plot(x - w / 2, zm, 'o--', color='#3a5a80', lw=1, ms=4)
ax.plot(x + w / 2, z45, 'o--', color='#8f3d3d', lw=1, ms=4)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
ax.set_ylim(0, 1.05); ax.set_ylabel('一致性')
ax.axhline(0, color='k', lw=0.8)
ax.set_title('可靠性三层账：相关级收敛 ≠ 机制级 ≠ 决策级\n'
             'z–45 塌方 = %.3f−%.3f = %.3f（P2a 预注册赌 ≥0.40：中）；κ(z,45)/Jaccard(z,45) 为已知数派生，只作一致性检查'
             % (z45[0], z45[1], z45[0] - z45[1]), fontsize=10.5)
ax.legend(fontsize=9)
note = ('受限收敛 ρ(A_z,A_45|S_A)=%.3f（204 把纬向两关门成员内部，P3b）。'
        % tl['z_45']['restricted_conv'])
fig.text(0.02, 0.07, '同框：经向–45° ρ_A=0.950，扣D后0.684，只塌0.266；\n' + note + '  [E71_FINAL_RESULTS.json → three_layer, M6_decision3]', fontsize=7, color='0.35')
fig.text(0.02, 0.012, QUAL, fontsize=7, color='0.35')
fig.tight_layout(rect=(0, 0.12, 1, 1))
fig.savefig(f'{FIN}/FIG2_three_layer_corrected_20260917.png', dpi=300, bbox_inches="tight")
plt.close(fig)

# ---------- 图3 G(k) 带 bootstrap CI ----------
fig, ax = plt.subplots(figsize=(7.6, 5.2))
ks = np.arange(1, 11)
for tr, col in (('A', '#3a5a80'), ('B', '#8f3d3d')):
    g = R['M2_gtheory3'][tr]
    y = np.array([g['G_of_k'][str(k)] for k in ks])
    ci = g['ci']['G_of_k_ci']
    lo = np.array([ci[str(k)][0] for k in ks]); hi = np.array([ci[str(k)][1] for k in ks])
    ax.plot(ks, y, 'o-', color=col, label='%s（σ²_p 占比 %.3f，k*=%d）' % (tr, g['var_p_share'], g['k_star_G0p8']))
    ax.fill_between(ks, lo, hi, color=col, alpha=0.25, lw=0)
ax.axhline(0.8, color='k', ls=':', lw=1)
ax.text(1.05, 0.802, 'G=0.8', fontsize=8, va='bottom')  # 2026-09-17 避免与图例重叠
ax.set_xticks(ks); ax.set_xlabel('场景数 k'); ax.set_ylabel('相对可推广系数 G(k)')
ax.set_ylim(0.78, 1.0)
ax.set_title('G 理论 p×e(3)（派生描述，非独立证据）：G(k) 带折叠集 bootstrap 95% CI（B=1000, seed=20260917, k=1..10 全程）\n'
             'CI 为候选级重采样描述性带宽（候选相依）；3 环境侧面数极少，环境抽样不确定性未入账', fontsize=10)
ax.legend(fontsize=9, loc='lower right')
fig.text(0.02, 0.012, QUAL + '\n排序限定：曲线保留冻结mergesort口径；按argsort复算B占比0.8121 < A的0.9193，P4b翻转（DEVIATIONS D4）。' + '  [E71_FINAL_RESULTS.json → M2_gtheory3]', fontsize=7, color='0.35')
fig.tight_layout(rect=(0, 0.12, 1, 1))
fig.savefig(f'{FIN}/FIG3_G_of_k_corrected_20260917.png', dpi=300, bbox_inches="tight")
plt.close(fig)
print('FIGS_DONE: FIG1_MTMM6_corrected_20260917.png FIG2_three_layer_corrected_20260917.png FIG3_G_of_k_corrected_20260917.png')
