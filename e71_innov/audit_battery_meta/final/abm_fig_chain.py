#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""abm_fig_chain.py — 封存后上台用滤链图（只读 ABM_DERIVED.json / ABM_FILTER_CHAIN.json；不产生新读数、不改判）。
输出 final/abm_chain_curve_v2.png。左：各级幸存者按 A（=−ρ，E57 约定）三段堆叠；右：三把参考集在各级的留存。"""
import json, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
HERE = os.path.dirname(os.path.abspath(__file__))
for cand in ('Noto Sans CJK SC', 'Noto Sans CJK TC', 'Noto Sans CJK JP'):
    if any(f.name == cand for f in font_manager.fontManager.ttflist):
        plt.rcParams['font.sans-serif'] = [cand, 'DejaVu Sans']; break
plt.rcParams['axes.unicode_minus'] = False
SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
BLUE, GRAY, RED = '#2a78d6', '#a8a6a0', '#e34948'
S1, S2, S3 = '#2a78d6', '#eb6834', '#1baf7a'

D = json.load(open(f'{HERE}/ABM_DERIVED.json')); fc = json.load(open(f'{HERE}/ABM_FILTER_CHAIN.json'))
lv = ['L0', 'L1', 'L2', 'L3', 'L4']
lab = ['L0\n非退化', 'L1\n+纬向换平底', 'L2\n+转风向', 'L3\n+荒谬黏性', 'L4\n+陡度轴']
by = D['chain']['by_level']
good = [by[l]['n_A_ge_0p7'] for l in lv]; bad = [by[l]['n_A_le_m0p7'] for l in lv]
mid = [by[l]['n'] - g - b for l, g, b in zip(lv, good, bad)]
ret = fc['set_retention_H0']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.8, 5.2), gridspec_kw=dict(width_ratios=[1.25, 1]))
fig.patch.set_facecolor(SURF)
for ax in (ax1, ax2):
    ax.set_facecolor(SURF)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=10.5)
    ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
x = range(5); w = 0.62
ax1.bar(x, bad, w, color=RED, edgecolor=SURF, lw=2, label='A ≤ −0.7（反向排序）')
ax1.bar(x, mid, w, bottom=bad, color=GRAY, edgecolor=SURF, lw=2, label='|A| < 0.7')
ax1.bar(x, good, w, bottom=[b + m for b, m in zip(bad, mid)], color=BLUE, edgecolor=SURF, lw=2, label='A ≥ 0.7（排得准）')
for i in x:
    tot = bad[i] + mid[i] + good[i]
    ax1.text(i, tot + 200, '%d' % tot, ha='center', va='bottom', fontsize=11, color=INK, fontweight='bold')
    ax1.text(i, tot + 1150, 'A≥0.7：%d' % good[i], ha='center', va='bottom', fontsize=9, color=INK2)
    ax1.text(i, bad[i] / 2, '%d\n(%.0f%%)' % (bad[i], 100.0 * bad[i] / tot), ha='center', va='center', fontsize=9, color='white')
ax1.set_xticks(list(x)); ax1.set_xticklabels(lab, fontsize=10, color=INK)
ax1.set_ylabel('幸存候选数（H=0）', color=INK2, fontsize=11)
ax1.set_title('滤链各级幸存者按排序力 A 分段：反向排序占比 31% → 72%（L3）', color=INK, fontsize=12.5, loc='left')
ax1.legend(frameon=False, fontsize=9.5, loc='upper right')
ax1.set_ylim(0, 18500)

for key, nm, c, n0 in (('S_Aperp_444', 'A⊥ 门 444', S2, 444), ('S_A_204', '两关门 204', S1, 204), ('S_strict_12', '严格门 12', S3, 12)):
    ys = [ret[key][l] for l in lv]
    ax2.plot(list(x), ys, '-', color=c, lw=2, marker='o', ms=8, markeredgecolor=SURF, markeredgewidth=2, label=nm)
    ax2.text(4.12, ys[-1], '%s → %d' % (nm, ys[-1]), va='center', fontsize=9.5, color=INK2)
ax2.set_yscale('log'); ax2.set_ylim(1.5, 700)
ax2.set_xticks(list(x)); ax2.set_xticklabels(lv, fontsize=10.5, color=INK)
ax2.set_xlim(-0.3, 5.6)
ax2.set_ylabel('参考集留存数（对数轴）', color=INK2, fontsize=11)
ax2.set_title('三把已知门在各级的留存', color=INK, fontsize=12.5, loc='left')
ax2.legend(frameon=False, fontsize=9.5, loc='lower left')
fig.text(0.01, 0.01, '数据：final/ABM_DERIVED.json:chain.by_level；ABM_FILTER_CHAIN.json:set_retention_H0（封存后派生描述，非预测）。A=−ρ(读数,技巧)，E57 约定。',
         fontsize=8.5, color=INK2)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(f'{HERE}/abm_chain_curve_v2.png', dpi=200, facecolor=SURF)
print('saved')
