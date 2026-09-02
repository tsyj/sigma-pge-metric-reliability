#!/bin/bash
# 从各结果 JSON 重算并打印参照系表（零机时，只读）
set -eu; cd "$(dirname "$0")/.."
${PYTHON:-python3} - <<'PYX'
import json
d=json.load(open('baselines/BASELINES.json'))
w=max(len(k) for k in d)
print('%-*s | %s'%(w,'档','实测结果'))
for k,v in d.items(): print('%-*s | %s'%(w,k,v['结果']))
print('\n出处文件均在 e44_tide/analysis/、e52/、e56/、ledger/ 下；见 BASELINES.md')
PYX
