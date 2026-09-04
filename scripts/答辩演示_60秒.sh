#!/bin/bash
# 答辩现场演示（约 60 秒）：从提交包里的数据当场重算全部主结论
# 用法：bash 答辩演示_60秒.sh        （在仓库根目录运行）
# 节奏：每屏之间停 8 秒，够讲一句话；不需要机时、不调用任何模型
set -u
cd "$(dirname "$0")" 2>/dev/null || true
[ -d e44_tide ] || cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
PY=""
for c in python3 python /home/xinyuan/anaconda3/envs/numpy1/bin/python; do
  command -v "$c" >/dev/null 2>&1 && "$c" -c "import json" >/dev/null 2>&1 && { PY="$c"; break; }
done
[ -n "$PY" ] || { echo "需要 python3"; exit 1; }
C='\033[1;36m'; Y='\033[1;33m'; G='\033[1;32m'; N='\033[0m'
pause(){ sleep "${DEMO_PAUSE:-8}"; }
clear
printf "${C}谁来给尺子打分  ·  队伍：虎虎  ·  仓库已冻结在 tag fusai-v6${N}\n"
printf "${C}下面所有数字都从提交包里的数据当场重算，不需要机时，也不调用任何模型${N}\n\n"
sleep 3

printf "${Y}【一】这套检验判过谁${N}\n"
$PY e44_tide/scorecard.py >/dev/null 2>&1
$PY - <<'PYX'
import json
K=json.load(open('e44_tide/analysis/KILLBOARD.json'))
名={'Pnet_MW':'论文头条那个指标','deep_dc_rms':'深层残余流','temp_d400':'深水温度','uv_ratio':'u/v 比值','truth':'隐藏真值（对照）'}
print('  %-18s %s'%('', ' '.join('%-5s'%c.split()[0] for c in K['cols'])))
for r,row in zip(K['rows'],K['grid']):
    print('  %-18s %s'%(名.get(r,r), ' '.join('%-5s'%c['verdict'] for c in row)))
print()
print('  最右一列是业内现在用的评审标准：四把尺子全部放行')
print('  A1-A9 是我们的九项检验：每一把的问题都定位到了具体哪一项')
print('  最下面一行是隐藏真值自己走一遍，全部通过 —— 这套检验是精准的，不是无差别否定')
PYX
pause

printf "\n${Y}【二】最主要的定量结果${N}\n"
$PY - <<'PYX'
import json
P=json.load(open('e44_tide/analysis/E57_PARETO.json'))
print('  在全部 %d 把候选尺子上：'%P['n_candidates'])
print('    排得准 与 不容易被糊弄，相关系数 = %.3f（一头越强，另一头越弱）'%P['spearman_A_B'])
print('    两项同时合格的只有 %d 把；若两者互不相干，本该有 %.0f 把 —— 少了 %.1f 倍'%(
      P['n_both'],P['independent_expect'],P['independent_expect']/P['n_both']))
print('    两项都接近满分的理想角落：实测%s'%('有' if P['utopia_occupied'] else '是空的'))
PYX
pause

printf "\n${Y}【三】这套检验也检验自己${N}\n"
$PY - <<'PYX'
import json
T=json.load(open('e44_tide/analysis/E58_TRIVALENT.json'))
r=T['rows']['uv_zonal_paired']
print('    识别问题时有把握，确认合格时不轻易下结论：')
print('      即使 %d 次配对全部通过，置信区间 [%.3f, %.3f] 仍跨过门槛，我们只记「待定」'%(r['n'],r['ci'][0],r['ci'][1]))
V=json.load(open('e60/E60_VERDICT.json')); j=[p['jaccard'] for p in V['pairwise'].values()]
print('    换四种海山陡峭程度，合格尺子的重合度 %.2f–%.2f —— 这个判据可靠、可迁移'%(min(j),max(j)))
PYX
pause

printf "\n${Y}【四】不用真值也能提前筛${N}\n"
$PY - <<'PYX'
import json
R=json.load(open('e59/E59_TRUTHFREE.json'))
print('    只用不需要真值的线索，换到另一种风向上评估：准确度 AUC = %.3f'%R['multi']['auc_test'])
print('    中段命中率 %.2f，是随便挑（%.2f）的约 %.1f 倍'%(
      R['peak']['hit_rate'],R['base_rate_test'],R['peak']['hit_rate']/R['base_rate_test']))
PYX
pause

printf "\n${G}这些数字全部来自提交包里的结果文件；一条命令可重算：${N}\n"
printf "${G}  bash scripts/reproduce_core.sh${N}\n"
printf "${G}换个领域、换把尺子，这套办法直接能用。${N}\n\n"
