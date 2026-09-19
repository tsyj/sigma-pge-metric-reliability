#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从五份扫描账本生成清单；不把扫描行数当作全项目运行总数。
Agent 行单列；完成状态、去重数及账本哈希均由输入计算。
"""
import json, os, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def sha12(path):
    h = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    return h

rows, sources = [], {}

# 1) 内潮侧原始清单（含 Agent 行，分列）
p = 'e44_tide/analysis/RUNS_MANIFEST.json'
m44 = json.load(open(p)); sources[p] = sha12(p)
for r in m44['rows']:
    is_agent = (r.get('group') == 'Agent陷阱局')
    rows.append(dict(tag=r['tag'], env='tide', group=r.get('group'),
                     scan=not is_agent, done=r.get('done'),
                     inputs_md5_sha256=r.get('inputs_md5_sha256'),
                     in_16lib=r.get('in_16lib'), in_judge15=r.get('in_judge15'),
                     source=p))

# 2) 三个风向的旋钮扫描台账
for p, env in (('ledger/knob_sweep.json', 'wind_zonal'),
               ('ledger/knob_sweep_merid.json', 'wind_merid'),
               ('ledger/knob_sweep_diag45.json', 'wind_diag45')):
    sw = json.load(open(p)); sources[p] = sha12(p)
    for r in sw:
        obs = r.get('obs') or {}
        rows.append(dict(tag=r.get('run_id'), env=env, group='%s扫' % r.get('knob'),
                         scan=True, knob=r.get('knob'), val=r.get('val'),
                         bathy=r.get('bathy'),
                         done=bool(obs.get('valid')) and not obs.get('crashed', False),
                         source=p))

# 3) BH93 静止态
p = 'e56/E56_BH93.json'
bh = json.load(open(p)); sources[p] = sha12(p)
for r in bh:
    rows.append(dict(tag=r['tag'], env='bh93_rest', group='BH93静止态',
                     scan=True, bathy=r.get('bathy'), val=r.get('VISC2'), knob='VISC2',
                     done=r.get('done'), source=p))

by_env, agent_rows = {}, 0
for r in rows:
    if r['scan']:
        by_env[r['env']] = by_env.get(r['env'], 0) + 1
    else:
        agent_rows += 1
scan_total = sum(by_env.values())

summary = dict(scan_total=scan_total, by_env=by_env, agent_rows_tide=agent_rows,
               note=('Agent 下单与 LLM 局不计入扫描算例；其轨迹见 ledger/agent_*.json、'
                     'e44_tide/agent/*.jsonl、e61/trajectory_e61.jsonl。'
                     '完成时刻口径差异见 e44_tide/analysis/TIME_LEDGER.json（附录D-2.1）。'))
summary['row_total'] = len(rows)
summary['scan_done'] = sum(r['scan'] and r.get('done') is True for r in rows)
summary['scan_unique_env_tag'] = len({(r['env'], r['tag']) for r in rows if r['scan']})
summary['scope'] = '仅所列五份扫描账本的行计数；不是全项目运行次数，不由此推断无失败或无重跑。'

out = dict(generated_by='scripts/gen_runs_manifest.py',
           summary=summary, source_sha256=sources, rows=rows)
dst = 'e44_tide/analysis/RUNS_MANIFEST_FULL.json'
with open(dst, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
    f.write('\n')
print('written:', dst)
print('summary:', json.dumps(summary, ensure_ascii=False))

with open('RUNS_MANIFEST.md', 'w', encoding='utf-8') as f:
    f.write('# 扫描账本机算清单\n\n由 `scripts/gen_runs_manifest.py` 生成；数值真源为 `e44_tide/analysis/RUNS_MANIFEST_FULL.json`。\n\n')
    f.write('扫描行数：**%d**；其中完成状态为真的行数：**%d**；按环境及标识去重：**%d**。另列内潮 Agent 行：**%d**。\n\n' % (scan_total, summary['scan_done'], summary['scan_unique_env_tag'], agent_rows))
    f.write('这不是全项目运行总数，不代表全部原始输出已经交付，也不证明没有重跑。\n\n| 环境 | 扫描行数 |\n|---|---:|\n')
    for env, n in by_env.items():
        f.write('| %s | %d |\n' % (env, n))
    f.write('\n源文件完整 SHA-256 见 JSON 的 `source_sha256`；逐行出处见 `rows[].source`。\n')
