#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""SEEDS82：把纬向 82 把复合门两全候选（Adiff>=0.7 ∧ B65>=0.9 ∧ |Ddiff|<=0.5）
从 E71B_AXES.npz 导出为不可变名单，供封存预注册引用（验证前存档）。
只读试点产出（纬向），不触任何留出数据。输出确定性（无时间戳），便于 sha256 固定。"""
import json
import numpy as np

BASE = '/data/xinyuan/GOAI_ai4s_env/e71_innov/negctrl_surrogate'
FIN = f'{BASE}/final'
GATE = dict(Adiff_min=0.7, B65_min=0.9, absDdiff_max=0.5)

Z = np.load(f'{BASE}/E71B_AXES.npz')
m = (Z['Adiff'] >= GATE['Adiff_min']) & (Z['B65'] >= GATE['B65_min']) \
    & (np.abs(Z['Ddiff']) <= GATE['absDdiff_max'])
n = int(m.sum())
assert n == 82, f'复合门候选数 {n} != 82（E71E both_diff.n_both_absD_le05），中止'
idx = np.where(m)[0]
seeds = [dict(num=str(Z['name_num'][i]), den=str(Z['name_den'][i]),
              Adiff=round(float(Z['Adiff'][i]), 4),
              B65=round(float(Z['B65'][i]), 4),
              Ddiff=round(float(Z['Ddiff'][i]), 4),
              Alogr=round(float(Z['Alogr'][i]), 4),
              Dlogr=round(float(Z['Dlogr'][i]), 4)) for i in idx]
seeds.sort(key=lambda s: (s['num'], s['den']))
out = dict(
    note='纬向 82 把复合门两全候选名单（验证前存档；复合门 B65 为原始读数平底抗刷率，B*!=B 当众申报）',
    gate=GATE, n=82, source='E71B_AXES.npz（试点，纬向 32 对）',
    caveat='32 对属先选后检的自适应复用（Blum & Hardt）；本名单是否真金取决于封存预注册后的经向/45°验证',
    seeds=seeds)
with open(f'{FIN}/SEEDS82.json', 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print('SEEDS82_DONE n=82')
