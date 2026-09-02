#!/bin/bash
# 一键 smoke test：不依赖模式数据，校验提交包自洽性（~10 秒）
set -e
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
echo "[1/4] 预注册文档 sha256 校验"
sha256sum -c e44_tide/PREREG_E44.sha256 --quiet && echo "  PASS: PREREG_E44.md 未被改动（盖章时间: $(cat e44_tide/PREREG_E44.stamp)）"
echo "[2/4] E44 判读可从指标表独立重算（Spearman 自实现，不用 scipy）"
$PY - <<'PYX'
import json
M=json.load(open('e44_tide/analysis/E44_METRICS.json'))
V=json.load(open('e44_tide/analysis/E44_VERDICT.json'))
def sp(a,b):
    n=len(a); ra=sorted(range(n),key=lambda i:a[i]); rb=sorted(range(n),key=lambda i:b[i])
    ka=[0]*n; kb=[0]*n
    for r,i in enumerate(ra): ka[i]=r
    for r,i in enumerate(rb): kb[i]=r
    ma=sum(ka)/n; mb=sum(kb)/n
    num=sum((ka[i]-ma)*(kb[i]-mb) for i in range(n))
    den=(sum((x-ma)**2 for x in ka)*sum((x-mb)**2 for x in kb))**0.5
    return num/den
bt=['b_bsplm2','b_bsplm3','pf_combo','b_bsplm6']; m=[2,3,4,6]
uv=[M[t]['uv_ratio'] for t in bt]
r=sp(m,uv)
assert abs(r-V['C1_rank_vs_m']['uv_ratio']['spearman_vs_m'])<1e-6, (r, '!=', V['C1_rank_vs_m']['uv_ratio']['spearman_vs_m'])
print('  PASS: uv_ratio m-axis Spearman = %+.3f == verdict'%r)
dc=[M[t]['deep_dc_rms'] for t in ['pf_v4','a_v4visc3e6','a_v4visc1e7','a_v4visc3e7','a_v4visc1e8','a_v4visc3e8']]
assert min(range(6),key=lambda i:dc[i])==5, 'deepDC best 应在 VISC4=3e8 端'
print('  PASS: deep_dc_rms 被极端黏性刷穿（best@3e8）可重算')
PYX
echo "[3/4] 500 km 判分锚一致性"
$PY - <<'PYX'
import json
K=json.load(open('e44_tide/analysis/ANSWER_KEY_500KM.json'))
m2=K['mode2_ratio']; m1=K['mode1_ratio']
assert m2['m2']>m2['m4']>m2['m6'], '第二模应单调挨刀'
assert all(abs(m1[k]-1.0)<0.01 for k in m1), '第一模应全档无损'
print('  PASS: 锚结构（第一模≈1.00, 第二模 %.3f→%.3f→%.3f 单调）'%(m2['m2'],m2['m4'],m2['m6']))
PYX
true
echo "[4/4] E52 第三强迫交集与 kill board 一致性"
$PY - <<'PYX'
import json
X=json.load(open('e52/E52_CROSS.json')); K=json.load(open('e44_tide/analysis/KILLBOARD.json'))
assert X['inter_triple']==0, X['inter_triple']
assert X['uv_merid']['rho']>-0.7 and not X['uv_merid']['passAB']
assert X['vu_merid']['paired']<0.9
print('  PASS: 三重交集 %d; u/v 经向 rho=%+.2f (fail A); v/u 经向 paired=%.2f (fail B)'%(X['inter_triple'],X['uv_merid']['rho'],X['vu_merid']['paired']))
rows=K['grid']; ruler_rows=rows[:4]; assert not any(all(c['verdict']=='过' for c in r) for r in ruler_rows), 'kill board 尺子行出现全绿'
print('  PASS: kill board 四把尺子无全绿行 (%d×%d, 第 5 行为真值对照)'%(len(rows),len(rows[0])))
PYX
echo "[5/5] 六项必交件与 secret"
for f in baselines/BASELINES.md scripts/reproduce_core.sh DISCLOSURE.md LICENSE e44_tide/analysis/KILLBOARD.json; do
  [ -f "$f" ] || { echo "  FAIL: 缺 $f"; exit 1; }
done
n=$(ls e44_tide/agent/*.jsonl 2>/dev/null | wc -l); [ "$n" -ge 3 ] || { echo "  FAIL: 探索日志 JSONL 少于 3 个"; exit 1; }
PAT="sk-[A-Za-z0-9]{16,}|$(printf '\345\257\206\347\240\201')|100\.(9[0-9]|1[0-2][0-9])\.[0-9]+\.[0-9]+|BEGIN [A-Z ]*PRIVATE KEY"
if grep -rInE "$PAT" . --exclude-dir=.git --exclude=smoke_test.sh -q 2>/dev/null; then
  echo "  FAIL: 疑似 secret:"; grep -rInE "$PAT" . --exclude-dir=.git --exclude=smoke_test.sh 2>/dev/null | head -3; exit 1; fi
echo "  PASS: 交付件齐全（参照系/一键复现/披露/许可/kill board/$n 份轨迹），无 secret"
echo "SMOKE TEST: ALL PASS (5/5)"
