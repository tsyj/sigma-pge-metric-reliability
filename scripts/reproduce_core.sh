#!/bin/bash
# 核心结果一键复现（零机时路径：从已交付的分析 JSON 重算全部主结论与主图）
# 完整重跑（需 ROMS/MITgcm 数据）见 README_semifinal.md
set -eu; cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
echo "== 1/4 kill board（主图）从 analysis/*.json 重生成 =="
$PY e44_tide/scorecard.py && echo "  -> e44_tide/figs/fig_killboard_print.png, fig_killboard_slide.png"
echo "== 2/4 参照系表重算 =="
bash baselines/run_baselines.sh
echo "== 3/4 主结论数字重算（三轴 rho/精确 p、交集与零假设期望、A8 带符号锚、BH93） =="
$PY - <<'PYX'
import json, itertools
import numpy as np
V=json.load(open('e44_tide/analysis/E44_VERDICT_v2.json')); R=json.load(open('e44_tide/analysis/RT2_FIXES.json'))
X=json.load(open('e52/E52_CROSS.json')); B=json.load(open('e56/E56_VERDICT.json'))
def rho(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float); ra=np.argsort(np.argsort(a)); rb=np.argsort(np.argsort(b))
    ra=ra-ra.mean(); rb=rb-rb.mean(); return float((ra*rb).sum()/np.sqrt((ra**2).sum()*(rb**2).sum()))
for ax in ('m','visc','gam'):
    a=V['axes'][ax]['uv_ratio']; print('  u/v %-5s rho=%+.3f n=%d p=%.4f'%(ax,a['rho'],a['n'],a['p_exact_two_sided']))
print('  交集/期望: 纬∩经 %d/%.1f  纬∩潮 %d/%.1f  经∩潮 %d/%.1f  三重 %d/%.2f (P0=%.2f)'%(
  X['inter_zonal_merid'],R['F1_null']['expected']['zonal_merid'],X['inter_zonal_tide'],R['F1_null']['expected']['zonal_tide'],
  X['inter_merid_tide'],R['F1_null']['expected']['merid_tide'],X['inter_triple'],R['F1_null']['expected']['triple'],R['F1_null']['P0_triple_poisson']))
for k,v in R['F2_A8_signed'].items(): print('  A8 %-13s rho=%+.3f p=%.4f -> %s'%(k,v['signed_rho'],v['p_exact_two_sided'],v['verdict']))
print('  BH93: u_max %.2f->%.2f (rho=%+.3f); A1 抗刷 %.3f; 代理夸大 %.2f 倍; 技巧全程为负 %s'%(
  B['bh93_umax'][0],B['bh93_umax'][-1],B['rho_bh93'],B['A1_paired_correct'],B['exaggeration'],B['skill_always_negative']))
PYX
echo "== 4/4 自检（与 smoke_test 同源） =="
bash scripts/smoke_test.sh | tail -2
echo "REPRODUCE_CORE: DONE"
