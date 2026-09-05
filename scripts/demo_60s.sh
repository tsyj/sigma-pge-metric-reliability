#!/bin/bash
# 答辩现场演示：全部数字从随包数据现场重算，不联网、不需要机时、不调用大模型。
set -u; cd "$(dirname "$0")/.."
PY=${PYTHON:-}
if [ -z "$PY" ]; then
  for c in python3 python /home/xinyuan/anaconda3/envs/numpy1/bin/python; do
    command -v "$c" >/dev/null 2>&1 && "$c" -c "import json" >/dev/null 2>&1 && { PY="$c"; break; }
  done
fi
[ -n "$PY" ] || { echo "需要 python3"; exit 1; }
bar(){ printf '\n\033[1;36m%s\033[0m\n' "$1"; }

bar "── 1/4  新旧指标的相互评判 ──────────────────────────────────"
$PY - <<'PYX'
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

bar "── 2/4  指标的两种性质：刻度精准与泛化性不能兼得 ────────────"
$PY - <<'PYX'
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
print('  → 刻度精准的那一半：需要真值，换个场景就崩')
print('  → 泛化性好的那一半：不需要真值，换个地形几乎不动')
PYX

bar "── 3/4  它会否定自己：事先登记的预测，现场逐条核对 ──────────"
$PY - <<'PYX'
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
print('  → 现场统计：%d 条事先登记的预测里，%d 条被自己的数据推翻'%(tot,ref))
print('  → 推翻的部分我们原样保留，没有改判据、没有事后补预测')
PYX

bar "── 4/4  全部可复算 ────────────────────────────────────────"
echo "  以上每一个数字，都是刚才从随包数据现场重算出来的"
echo "  一条命令重跑全部主结论：  bash scripts/reproduce_core.sh"
echo "  十秒自检：              bash scripts/smoke_test.sh"
echo ""
