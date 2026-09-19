#!/bin/bash
# 一键 smoke test：不依赖模式数据，校验提交包自洽性（~10 秒）
set -e
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
PY=${PYTHON:-python3}
echo "[1/5] 预注册文档 sha256 校验（校验仓库内交付件；哈希件路径相对仓库根，原登记行见 PREREG_HASH_INDEX.json）"
PREREG="e44_tide/PREREG_E44 e55/PREREG_E55 e56/prereg_e56 e59/PREREG_E59 e60/PREREG_E60 e61/PREREG_E61 e65/PREREG_E65 e66/PREREG_E66 e67/PREREG_E67 e67/PREREG_E67b"
for p in $PREREG; do
  # 注意：不能写成 `sha256sum -c ... && echo PASS`——set -e 下 && 左侧失败不会退出，校验失败也会一路 ALL PASS
  sha256sum -c "$p.sha256" --quiet || { echo "  FAIL: $p 与登记哈希不符或文件缺失"; exit 1; }
done
# E65/E67b 运行后曾把结果追加进同一文件，登记的是封存段：封存段必须是全文的逐字节前缀（见各自 *_核验说明.md）
for p in e65/PREREG_E65 e67/PREREG_E67b; do
  n=$(wc -c < "$p.sealed_prefix.md" | tr -d ' ') || n=0
  { [ "${n:-0}" -gt 0 ] && cmp -s -n "$n" "$p.sealed_prefix.md" "$p.md"; } || { echo "  FAIL: $p.sealed_prefix.md 不是 $p.md 的逐字节前缀"; exit 1; }
done
$PY - <<'PYX'
import json
J={'e65/PREREG_E65':'e65/E65_SPURIOUS_VS_TRUE.json','e66/PREREG_E66':'e66/E66_PARTIAL.json','e67/PREREG_E67b':'e67/E67B_RECIPE_TRANSFER.json'}
for p,j in J.items():
    h,f=open(p+'.sha256').read().split()
    assert f in (p+'.md',p+'.sealed_prefix.md'), (p,'哈希件指向了意外的文件',f)
    assert json.load(open(j))['prereg_sha']==h, (j,'运行时内嵌的 prereg_sha 与登记哈希不符')
print('  PASS: 10 份预注册与登记哈希逐位一致（E65/E67b 为封存段+前缀校验）；3 份结果 JSON 运行时内嵌的 prereg_sha 与登记一致')
PYX
echo "[2/5] E44 判读可从指标表独立重算（Spearman 自实现，不用 scipy）"
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
print('  PASS: deep_dc_rms 被极端黏性糊弄过去（best@3e8）可重算')
PYX
echo "[3/5] 500 km 判分锚一致性"
$PY - <<'PYX'
import json
K=json.load(open('e44_tide/analysis/ANSWER_KEY_500KM.json'))
m2=K['mode2_ratio']; m1=K['mode1_ratio']
assert m2['m2']>m2['m4']>m2['m6'], '第二模应单调挨刀'
assert all(abs(m1[k]-1.0)<0.01 for k in m1), '第一模应全档无损'
print('  PASS: 锚结构（第一模≈1.00, 第二模 %.3f→%.3f→%.3f 单调）'%(m2['m2'],m2['m4'],m2['m6']))
PYX
true
echo "[4/5] E52 第三强迫交集与 kill board 一致性"
$PY - <<'PYX'
import json
# 2026-09-17：保留历史值断言；交集为零的泛化解读已撤回。
X=json.load(open('e52/E52_CROSS.json')); K=json.load(open('e44_tide/analysis/KILLBOARD.json'))
assert X['inter_triple']==0, X['inter_triple']
assert X['uv_merid']['rho']>-0.7 and not X['uv_merid']['passAB']
assert X['vu_merid']['paired']<0.9
print('  历史记录一致性校验（非科学支持证据）：三重交集 %d; u/v 经向 rho=%+.2f (fail A); v/u 经向 paired=%.2f (fail B)'%(X['inter_triple'],X['uv_merid']['rho'],X['vu_merid']['paired']))
rows=K['grid']; ruler_rows=rows[:4]; assert not any(all(c['verdict']=='过' for c in r) for r in ruler_rows), 'kill board 尺子行出现全绿'
print('  PASS: kill board 四把尺子无全绿行 (%d×%d, 第 5 行为真值对照)'%(len(rows),len(rows[0])))
PYX
echo "[5/5] 六项必交件与 secret"
for f in baselines/BASELINES.md scripts/reproduce_core.sh DISCLOSURE.md LICENSE e44_tide/analysis/KILLBOARD.json; do
  [ -f "$f" ] || { echo "  FAIL: 缺 $f"; exit 1; }
done
n=$(ls e44_tide/agent/*.jsonl 2>/dev/null | wc -l); [ "$n" -ge 3 ] || { echo "  FAIL: 探索日志 JSONL 少于 3 个"; exit 1; }
# 扫描须排除 .venv/site-packages 等第三方源码：README 指引在仓库内建 venv，
# setuptools 自带源码含 password 字样，否则会误判为泄密。
# 只在"有实际赋值"时判为 secret: 词后须跟冒号/等号与非空值; 单独出现该词(如官方条款原文)不算
MI=$(printf '\345\257\206\347\240\201')
PREFIX=s
PAT="${PREFIX}k-[A-Za-z0-9]{16,}|(${MI}|passwd|password)[[:space:]]*[:=][[:space:]]*[^[:space:]]|100\.(9[0-9]|1[0-2][0-9])\.[0-9]+\.[0-9]+|BEGIN [A-Z ]*PRIVATE KEY"
if grep -rInE "$PAT" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude-dir=__pycache__ --exclude-dir=site-packages --exclude-dir=node_modules --exclude-dir=ci-logs --exclude-dir=.eggs --exclude-dir=build --exclude=smoke_test.sh -q 2>/dev/null; then
  echo "  FAIL: 疑似 secret:"; grep -rInE "$PAT" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude-dir=__pycache__ --exclude-dir=site-packages --exclude-dir=node_modules --exclude-dir=ci-logs --exclude-dir=.eggs --exclude-dir=build --exclude=smoke_test.sh 2>/dev/null | head -3; exit 1; fi
echo "  PASS: 交付件齐全（参照系/一键复现/披露/许可/kill board/$n 份轨迹），无 secret"
echo "SMOKE TEST: ALL PASS (5/5)"
