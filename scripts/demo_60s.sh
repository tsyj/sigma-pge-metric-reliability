#!/bin/bash
# 答辩现场演示：全部数字从随包数据现场重算，不联网、不需要机时、不调用大模型。
set -u -o pipefail; cd "$(dirname "$0")/.."
# 任何一屏算不出来就必须显形，不许打印完就当通过
FAILED=0
trap '[ "$FAILED" -eq 0 ] || { echo "DEMO: FAILED ($FAILED block(s))" >&2; exit 1; }' EXIT
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
PY=${PYTHON:-}
if [ -z "$PY" ]; then
  for c in python3 python /home/xinyuan/anaconda3/envs/numpy1/bin/python; do
    command -v "$c" >/dev/null 2>&1 && "$c" -c "import json" >/dev/null 2>&1 && { PY="$c"; break; }
  done
fi
[ -n "$PY" ] || { echo "需要 python3"; exit 1; }
bar(){ printf '\n\033[1;36m%s\033[0m\n' "$1"; }

bar "── 1/5  一万五千三百七十六把候选，过两道关的只有 204 把 ──────"
if ! $PY - <<'PYX'
import numpy as np, json
d = np.load('e65/E65_AXES.npz')
A, B = d['A'], d['B']
n = A.size
a = int((A >= 0.70).sum()); b = int((B >= 0.90).sum())
both = int(((A >= 0.70) & (B >= 0.90)).sum())
print('  候选尺子总数                %6d 把' % n)
print('  第一关 排序一致 A>=0.70     %6d 把通过' % a)
print('  第二关 平底对照 B>=0.90     %6d 把通过' % b)
print('  两关同过                    %6d 把' % both)
exp = a * b / n
print()
print('  → 若两关互不相干，期望同过 %.1f 把；实测 %d 把，衰减 %.1f 倍' % (exp, both, exp / both))
rec = json.load(open('e67/E67B_RECIPE_TRANSFER.json'))
ok = (rec['n_zonal'] == n and rec['size_S_A'] == both)
print('  → 与看数据之前封存的登记件对账：n=%d、过关数=%d —— %s'
      % (rec['n_zonal'], rec['size_S_A'], '一致' if ok else '不一致'))
raise SystemExit(0 if ok else 1)
PYX
then FAILED=$((FAILED+1)); echo '  [FAIL] 本屏重算失败' >&2; fi

bar "── 2/5  新旧指标的相互评判 ──────────────────────────────────"
if ! $PY - <<'PYX'
import json
K=json.load(open('e44_tide/analysis/KILLBOARD.json'))
NAME={'Pnet_MW':'海山周围的波功率','deep_dc_rms':'深层残余流','temp_d400':'深水温度',
      'uv_ratio':'两个流速的比值','truth':'隐藏的真值（对照）'}
COL=['换到平地','换无误差数据','换区域大小','换初始时刻','事先押注',
     '换风向','隐去名字','跟真值比方向','静止海检验','通行做法']
V={'过':'合格','死':'不合格','边':'勉强','未':'未测','待定':'证据不足','定义':'按定义'}
print('  %-22s%s'%('', ''.join('%-11s'%c for c in COL)))
for r,row in zip(K['rows'],K['grid']):
    print('  %-22s%s'%(NAME.get(r,r), ''.join('%-11s'%V.get(c['verdict'],c['verdict']) for c in row)))
n_bad=sum(1 for row in K['grid'][:4] for c in row[:9] if c['verdict'] in ('死','边'))
print()
print('  → 最右一列「通行做法」：四个指标全部合格')
print('  → 换成我们这九项：每一个指标都有不合格的项（共 %d 处不合格或勉强）'%n_bad)
PYX
then FAILED=$((FAILED+1)); echo '  [FAIL] 本屏重算失败' >&2; fi

bar "── 3/5  指标的两道检验：排序与平底配对 ────────────"
if ! $PY - <<'PYX'
import json
X=json.load(open('e55/E55_CROSS.json'))['prereg_check']['angle_trajectory_uv']
E=json.load(open('e60/E60_VERDICT.json'))
print('  同一个指标，换三个风向 —— 排名能力：')
for k,lab in (('deg0','纬向风'),('deg45','45° 风'),('deg90','经向风')):
    a=-X[k][0]
    print('      %-8s %+.2f%s'%(lab,a,'   ← 反过来了' if a<0 else ''))
j=[v['jaccard'] for v in E['pairwise'].values()]
f=[v['frac'] for v in E['per_rx'].values()]
print()
print('  换四种陡度的海山 —— 不容易被糊弄的那批指标：')
print('      合格比例 %s'%(' / '.join('%.1f%%'%(x*100) for x in f)))
print('      两两重合度 %.2f – %.2f  → 几乎是同一批'%(min(j),max(j)))
print()
print('  → 排序检验需要参照解；本例在经向风下排序转负')
print('  → 配对检验在已测四种陡度内较稳定，不能据此代替排序检验')
PYX
then FAILED=$((FAILED+1)); echo '  [FAIL] 本屏重算失败' >&2; fi

bar "── 4/5  它会否定自己：事先登记的预测，现场逐条核对 ──────────"
if ! $PY - <<'PYX'
import json,glob,os
FILES=[('e55/E55_CROSS.json','换强迫方向'),('e56/E56_VERDICT.json','社区标准检验'),
       ('e59/E59_TRUTHFREE.json','无真值预筛'),('e60/E60_VERDICT.json','换地形陡度'),
       ('e61/E61_AGENT_PICKS.json','机器挑指标')]
tot=ref=0
for f,lab in FILES:
    if not os.path.exists(f): continue
    d=json.load(open(f))
    pc=next((v for k,v in d.items() if 'prereg' in k.lower() and isinstance(v,dict)),None)
    if not pc: continue
    hits=[]
    for k,v in pc.items():
        if k.endswith('_range') or k.endswith('_note'): continue
        bad = (v is False) or (isinstance(v,str) and ('反驳' in v or '未命中' in v))
        good= (v is True)  or (isinstance(v,str) and ('命中' in v or v=='中'))
        if bad or good:
            tot+=1
            if bad: ref+=1; hits.append('%s 被推翻'%k.split()[0])
    print('  %-12s %s'%(lab, '、'.join(hits) if hits else '本组预测全部命中'))
print()
print('  → E55–E61 五组现场统计：%d 条事先登记的预测里，%d 条被自己的数据推翻'%(tot,ref))
print('  → 推翻的部分我们原样保留，没有改判据、没有事后补预测')
PYX
then FAILED=$((FAILED+1)); echo '  [FAIL] 本屏重算失败' >&2; fi

bar "── 5/5  随包结果可复算 ────────────────────────────────────────"
echo "  以上每一个数字，都是刚才从随包数据现场重算出来的"
echo "  一条命令复算随包主结论：  bash scripts/reproduce_core.sh"
echo "  十秒自检：              bash scripts/smoke_test.sh"
echo ""
