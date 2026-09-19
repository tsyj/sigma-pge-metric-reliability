#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E73 shortcut_theorem · 步骤 E：机械判分 → verdict.json（人不改判）。

判据即 PREREG §4/§5/§6 的逐字翻译；本脚本只做阈值比较与 sha 比对，不做任何新统计计算。
统计量为 null（不可算）一律判不中。脚本完整性：把 E73_TAIL.json / E73_SHORTCUT_MAP.json
（及后备 E73_AXES45_META.json）内嵌的 script_sha、本脚本自身 sha、盘上 e73b 的 sha 与
PREREG §2 表逐一比对；任一不符置 script_mismatch 旗（不改判，按 §9 查）。
运行：<python> e73e_verdict.py（无需 systemd-run，毫秒级）
"""
import hashlib, json, os, re, sys, time

FIN = '/data/xinyuan/GOAI_ai4s_env/e71_innov/shortcut_theorem/final'
PRE = f'{FIN}/PREREG_shortcut_theorem.md'
SHA = f'{FIN}/PREREG_shortcut_theorem.sha256'


def seal_gate():
    if not os.path.exists(SHA):
        sys.exit('拒绝运行：预注册尚未封存（缺 %s）。' % SHA)
    want = open(SHA).readline().split()[0]
    got = hashlib.sha256(open(PRE, 'rb').read()).hexdigest()
    if want != got:
        sys.exit('拒绝运行：PREREG 与封存 sha256 不符（%s… vs %s…）。' % (want[:12], got[:12]))
    return want


def sha_of(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


SEAL = seal_gate()
SCRIPT_SHA = sha_of(os.path.abspath(__file__))
m = json.load(open(f'{FIN}/E73_SHORTCUT_MAP.json'))
if m.get('prereg_sha') != SEAL:
    sys.exit('拒绝判分：E73_SHORTCUT_MAP.json 的 prereg_sha 与封存不符。')
tail = json.load(open(f'{FIN}/E73_TAIL.json')) if os.path.exists(f'{FIN}/E73_TAIL.json') else None

# ---- 脚本完整性（PREREG §2 表机械比对） ----
table = {}
for line in open(PRE, encoding='utf-8'):
    mm = re.match(r'^\|\s*(e73[a-z]_\w+\.py)\s*\|.*\|\s*([0-9a-f]{64})\s*\|\s*$', line)
    if mm: table[mm.group(1)] = mm.group(2)
integ = dict(table_rows=len(table),
             e73e_self=(table.get('e73e_verdict.py') == SCRIPT_SHA),
             e73d_in_map=(table.get('e73d_predict45.py') == m.get('script_sha')),
             e73b_on_disk=(table.get('e73b_insample.py') == sha_of(f'{FIN}/e73b_insample.py')))
if tail is not None:
    integ['e73t_in_tail'] = (table.get('e73t_tail.py') == tail.get('script_sha'))
    integ['tail_prereg_sha'] = (tail.get('prereg_sha') == SEAL)
if m.get('axes_source', '').startswith('shortcut_theorem'):
    am = json.load(open(f'{FIN}/E73_AXES45_META.json'))
    integ['e73c_in_axes_meta'] = (table.get('e73c_axes45.py') == am.get('script_sha'))
script_mismatch = not all(v for k, v in integ.items() if k != 'table_rows') or len(table) != 5

# ---- 验证性锚（PREREG §4：相关 ±0.01，计数精确；门_45 仅当 n_pairs_45>0 可检） ----
a = m['anchors']
def near(x, t): return bool(x is not None and abs(x - t) <= 0.01)
gate45_checkable = bool(a.get('n_pairs_45') is not None and a['n_pairs_45'] > 0)
anchors = dict(
    rho_AB=near(a['rho_AB_argsort'], -0.6742),
    rho_DA=near(a['rho_DA_argsort'], 0.9762),
    rho_DB=near(a['rho_DB_argsort'], -0.661),
    n_S_A=(a['n_S_A'] == 204),
    escapees=(a['n_escapees_found'] == 12 and a['escapees_all_G0'] is True),
    gate45_band=((450 <= a['n_gate45'] <= 458) if gate45_checkable else None))
pipeline_suspect = not all(v for v in anchors.values() if v is not None)

# ---- 真预测判定（PREREG §5 逐字；null → 不中） ----
def ge(x, t): return bool(x is not None and x >= t)
def lt(x, t): return bool(x is not None and x < t)
def le(x, t): return bool(x is not None and x <= t)

P = {}
P['P1'] = dict(stat=m['P1']['rankcorr_argsort'], threshold='>=0.80', passed=ge(m['P1']['rankcorr_argsort'], 0.80))
P['P2'] = dict(stat=m['P2']['hit_rate'], threshold='>=0.90', n_conf=m['P2']['n_conf'],
               passed=ge(m['P2']['hit_rate'], 0.90))
P['P3a'] = dict(stat=m['P3'].get('p3a_mw_one_sided'), threshold='p<0.05',
                n_surv45_in_S_A=m['P3']['n_surv45_in_S_A'], n_dead_in_S_A=m['P3']['n_dead_in_S_A'],
                passed=lt(m['P3'].get('p3a_mw_one_sided'), 0.05))
P['P3b'] = dict(stat=m['P3'].get('p3b_mw_one_sided'), threshold='p<0.05', n_triple=m['P3']['n_triple'],
                passed=lt(m['P3'].get('p3b_mw_one_sided'), 0.05))
P['P4'] = dict(stat=m['P4'].get('mean_ratio'), threshold='P1>0 且 mean_ratio>=0.9',
               passed=bool(ge(m['P1']['rankcorr_argsort'], 1e-12) and ge(m['P4'].get('mean_ratio'), 0.9)))
P['P5'] = dict(stat=m['P5']['ratio'], threshold='<=0.5', passed=le(m['P5']['ratio'], 0.5))
P['P6'] = dict(stat=m['P6']['strict_survive'], threshold='<=4', n_escapees=m['P6']['n_escapees'],
               passed=le(m['P6']['strict_survive'], 4))

# 敏感性翻转旗（P1 双口径；P5 的 argsort 原始相关同报在 map 里，不参与判定）
sensitivity_flips = dict(P1=bool(ge(m['P1']['rankcorr_avgrank'], 0.80) != P['P1']['passed']))

aux = None
if tail:
    aux = dict(H1=dict(rho=tail['H1']['rho_kappa_absg'], p=tail['H1']['perm_p_one_sided'],
                       direction_confirmed=tail['H1']['direction_confirmed']),
               H2=dict(p=tail['H2']['mw_p_one_sided'],
                       direction_confirmed=tail['H2']['direction_confirmed']),
               n_used=tail.get('n_used'), n_excluded_lt16=tail.get('n_excluded_lt16'),
               counted=False, note='盘上数据附验，不计入真预测（PREREG §6）')

verdict = dict(module='shortcut_theorem', script='e73e_verdict.py', script_sha=SCRIPT_SHA,
               prereg_sha=SEAL, date=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
               axes_source=m['axes_source'], axes_sha256=m.get('axes_sha256'),
               n_45=m['n_45'], n_common=a.get('n_common'),
               low_n=m['low_n'], k5_degenerate=m['k5_degenerate'],
               anchors=anchors, gate45_band_checkable=gate45_checkable, pipeline_suspect=pipeline_suspect,
               script_integrity=integ, script_mismatch=script_mismatch,
               predictions=P,
               counted_pass='%d/7' % sum(1 for v in P.values() if v['passed']),
               sensitivity_flips=sensitivity_flips,
               aux_tail=aux)
json.dump(verdict, open(f'{FIN}/verdict.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(verdict, ensure_ascii=False, indent=1))
