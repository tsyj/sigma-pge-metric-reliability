#!/bin/bash
# 60 秒答辩 demo：从已交付的 JSON 当场重算主结论与主图，全程零机时、零 LLM。
set -u; cd "$(dirname "$0")/.."
PY=${PYTHON:-}
if [ -z "$PY" ]; then
  for c in python3 python /home/xinyuan/anaconda3/envs/numpy1/bin/python; do
    command -v "$c" >/dev/null 2>&1 && "$c" -c "import json" >/dev/null 2>&1 && { PY="$c"; break; }
  done
fi
[ -n "$PY" ] || { echo "需要 python3"; exit 1; }
bar(){ printf '\033[1;36m%s\033[0m\n' "$1"; }
bar "── 1/4  这套协议判过谁：kill board 现场重算 ────────────────"
$PY e44_tide/scorecard.py >/dev/null 2>&1
$PY - <<'PYX'
import json
K=json.load(open('e44_tide/analysis/KILLBOARD.json'))
名={'Pnet_MW':'环带波功率(论文头条)','deep_dc_rms':'深层残余流','temp_d400':'深水温度≈4°C','uv_ratio':'u/v 比值','truth':'隐藏真值(对照行)'}
print('  %-20s %s'%('', ' '.join('%-5s'%c.split()[0] for c in K['cols'])))
for r,row in zip(K['rows'],K['grid']):
    print('  %-20s %s'%(名.get(r,r), ' '.join('%-5s'%c['verdict'] for c in row)))
print('  → 四把尺子没有一行全绿；R 列(领域现行评审判据)四把全过，A1-A9 全杀；对照行按定义或实测全过')
PYX
bar "── 2/4  主结论的定量支柱：两关互斥 ───────────────────────"
$PY - <<'PYX'
import json
P=json.load(open('e44_tide/analysis/E57_PARETO.json'))
print('  全部 %d 个候选：ρ(排得准的程度,抗糊弄的程度) = %.3f'%(P['n_candidates'],P['spearman_A_B']))
print('  两关同过 %d 个 vs 独立期望 %.0f 个 → 贫化 %.1f 倍'%(P['n_both'],P['independent_expect'],P['independent_expect']/P['n_both']))
print('  乌托邦角 (1,1) 实测%s'%('被占据' if P['utopia_occupied'] else '为空'))
PYX
bar "── 3/4  协议对自己的两次审计 ────────────────────────────"
$PY - <<'PYX'
import json
T=json.load(open('e44_tide/analysis/E58_TRIVALENT.json'))
r=T['rows']['uv_zonal_paired']
print('  三值化：u/v 纬向 %d/%d 满分，Wilson CI[%.3f,%.3f] → 判「%s」'%(r['k'],r['n'],r['ci'][0],r['ci'][1],r['verdict_vs_0p9']))
print('           → 能可靠判死，不能可靠认证')
V=json.load(open('e60/E60_VERDICT.json')); j=[p['jaccard'] for p in V['pairwise'].values()]
print('  陡度轴：4 种陡度 两两 Jaccard %.2f–%.2f → 抗糊弄的程度对地形稳健（预注册赌<0.5，被推翻）'%(min(j),max(j)))
PYX
bar "── 4/4  这套探索产出了什么科学结论 ──────────────────────"
$PY - <<'PYX'
import json
V=json.load(open('e56/E56_VERDICT.json'))
u=V['bh93_umax']; sk=V['skill_range']
print('  把本领域用了三十多年的公认基准（BH93 1993 静止态检验）放进同一张表：')
print()
print('    伪流最大值    %6.2f → %5.2f cm/s（降 %.0f%%）  读数说「改进了」'%(u[0],min(u),(u[0]-min(u))/u[0]*100))
print('    独立真值技巧  %6.2f → %5.2f              全程为负，从没转正'%(sk[0],sk[1]))
print('    代理改进幅度 ÷ 真值改进幅度 = %.2f 倍；平底上抗糊弄率 %.3f'%(V['exaggeration'],V['A1_paired_correct']))
print()
print('  → 结论不是「它被刷穿了」，而是「它无判别力」：')
print('     方向和真值一致（ρ=%.1f），但它报的改进幅度不能当真'%V['rho_bh93'])
PYX
bar "──────────────────────────────────────────────────────────"
echo "  全部数字单一真源：e44_tide/analysis/、e52/、e55/、e56/、e59/、e60/、e61/ 下的 JSON"
echo "  完整自检：bash scripts/smoke_test.sh   完整复现：bash scripts/reproduce_core.sh"
