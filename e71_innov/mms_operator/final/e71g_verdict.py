#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E71G · 机械判分 → verdict.json ＋ knob_table.md。

判据全部来自封存的 PREREG §5（锚）与 §6（P1-P6 真预测，每条单一布尔式）；本脚本只是逐字翻译。
人不改判：被推翻原样保留；判定锚（A0/A1/A2/A3）任一不过 ⇒ anchor_failed=true，P 组照判但报告只能以
「复刻未达锚」口径呈现。A2c 为报告项（gating=false）；A2b 为可选项（gating=false，状态单列 a2b_status）。
门控：PREREG 未封存/不匹配 → 拒绝；脚本 sha 与封存 §7 表不符 → 拒绝；MMS_OPERATOR.json 缺失 → 拒绝。
verdict.json 顶层字段（PREREG §7 钉死）：date, prereg_sha256, code_sha, code_sha_match_scan,
scan_meta, anchors[id/statement/values/gating/anchor_pass], anchor_failed, a2b_status,
predictions[id/statement/values/prediction_pass], n_pass, n_total, open_problems。
"""
import hashlib, json, os, re, sys, time

FIN = '/data/xinyuan/GOAI_ai4s_env/e71_innov/mms_operator/final'
PRE, SHA = f'{FIN}/PREREG_mms_operator.md', f'{FIN}/PREREG_mms_operator.sha256'
RES = f'{FIN}/MMS_OPERATOR.json'
TIERS = ['smooth', 'steep', 'rx069', 'harsh']
SCRIPTS = ['e71g_replica.py', 'e71g_scan.py', 'e71g_verdict.py', 'e71g_1step_clone.sh', 'e71g_run.sh']


def sha256(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


if not os.path.exists(SHA):
    sys.exit('拒绝判分：预注册尚未封存。')
want = open(SHA).readline().split()[0]
got = sha256(PRE)
if want != got:
    sys.exit('拒绝判分：PREREG 与封存 sha256 不符。')
table = dict(re.findall(r'^\|\s*(e71g_[A-Za-z0-9_.]+)\s*\|\s*`?([0-9a-f]{64})`?\s*\|',
                        open(PRE, encoding='utf-8').read(), flags=re.M))
cur = {s: sha256(f'{FIN}/{s}') for s in SCRIPTS}
bad = [s for s in SCRIPTS if table.get(s) != cur[s]]
if bad:
    sys.exit('拒绝判分：脚本 sha256 与封存 PREREG §7 表不符：' + ','.join(bad))
if not os.path.exists(RES):
    sys.exit('拒绝判分：MMS_OPERATOR.json 不存在（先跑 e71g_scan.py）。')
R = json.load(open(RES))

A, P = [], []


def anchor(pid, stmt, vals, ok, gating):
    A.append(dict(id=pid, statement=stmt, values=vals, gating=bool(gating),
                  anchor_pass=(None if ok is None else bool(ok))))


def pred(pid, stmt, vals, ok):
    P.append(dict(id=pid, statement=stmt, values=vals, prediction_pass=bool(ok)))


# ---------- 锚（验证性断言，PREREG §5） ----------
a = R['anchors']
anchor('A0', '复刻 Cs_r vs out_his Cs_r：max|Δ| <= 1e-10', a['A0'], a['A0']['max_dcs'] <= 1e-10, True)
anchor('A1', '平底零锚：max|a_u| == 0.0 且 max|a_v| == 0.0（逐位零）', a['A1'],
       a['A1']['max_abs_u'] == 0.0 and a['A1']['max_abs_v'] == 0.0, True)
anchor('A2', 'DT*max_内点|Σ_k(Hz_u·a_u)/Σ_k Hz_u| / ubarmax_step1(1.869474e-3，diag 第2行第2列) ∈ [0.5, 2.0]',
       a['A2'], 0.5 <= a['A2']['ratio'] <= 2.0, True)
anchor('A3', '七档陡臂步 1 ubarmax（diag 第2行第2列）max/min − 1 <= 0.04（日 1 三维 |u|max 比值同框，不判）',
       a['A3'], a['A3']['spread'] <= 0.04, True)
anchor('A2c', '报告项：diag 第3行第4列 umax ∈ [0.95·X, 1.05·(X+U)]，X=DT*max_内点(a_u−柱平均)，U=ubarmax_step1',
       a['A2c'], a['A2c']['in_bracket'], False)
b = a['A2b']
if not b.get('present'):
    a2b_status = 'not_run'
    anchor('A2b', '可选一步运行：未跑（PREREG 允许，不扣分）', b, None, False)
elif (not b.get('done')) or ('error' in b):
    a2b_status = 'error'
    anchor('A2b', '可选一步运行：运行未完成或读取出错（如实登记，不判）', b, None, False)
else:
    ok = b['pat_dev_linf_u'] <= 1e-3 and b['pat_dev_linf_v'] <= 1e-3
    a2b_status = 'pass' if ok else 'fail'
    anchor('A2b', '一步运行 u_prsgrd/v_prsgrd 与复刻 a_u/a_v 的柱偏差归一化形状 内点 L∞ <= 1e-3（u、v 均需）',
           b, ok, False)
anchor_failed = any(x['anchor_pass'] is False for x in A if x['gating'])

# ---------- 真预测（PREREG §6） ----------
t = R['S1_tiers']
eu = [t[k]['EL2_u'] for k in TIERS]
pred('P1', 'S1 四档 E_L2^u 严格递增（smooth<steep<rx069<harsh）',
     dict(order=TIERS, EL2_u=eu), all(eu[i] < eu[i + 1] for i in range(3)))
p23 = R['S2_refine']['smooth']['p23']
pred('P2', '光滑成员 p̂_23 ∈ [1.5, 2.5]', dict(p23_smooth=p23), 1.5 <= p23 <= 2.5)
p12s, p12m = R['S2_refine']['steep']['p12'], R['S2_refine']['smooth']['p12']
pred('P3', 'p̂_12(陡) <= p̂_12(光滑) − 0.3', dict(p12_steep=p12s, p12_smooth=p12m), p12s <= p12m - 0.3)
rf = R['S3_knobs']['ratio_flat']
pred('P4', 'E_L2^u(flat48)/E_L2^u(r26steep) <= 0.2', dict(ratio_flat=rf), rf <= 0.2)
rr = R['S3_knobs']['ratio_refsub']
pred('P5', 'E_L2^u(r26steep, ρ_m−ρ_ref(z)) / E_L2^u(r26steep, ρ_m) <= 0.5', dict(ratio_refsub=rr), rr <= 0.5)
ev = [t[k]['ELinf_v'] for k in TIERS]
pred('P6', 'S1 四档 E_L∞^v 严格递增（伪梯度，真值恒零）',
     dict(order=TIERS, ELinf_v=ev), all(ev[i] < ev[i + 1] for i in range(3)))

V = dict(date=time.strftime('%F %T %z'), prereg_sha256=got, code_sha=cur,
         code_sha_match_scan=(R['meta'].get('code_sha') == cur),
         scan_meta=R['meta'], anchors=A, anchor_failed=anchor_failed, a2b_status=a2b_status,
         predictions=P, n_pass=sum(1 for x in P if x['prediction_pass']), n_total=len(P),
         open_problems=['n=4 陡度静止态运行对照（已预注册未执行，PREREG §8.5）'])
json.dump(V, open(f'{FIN}/verdict.json', 'w'), indent=1, ensure_ascii=False)
print('落盘 verdict.json：anchor_failed=%s，A2b=%s，真预测 %d/%d' % (anchor_failed, a2b_status,
                                                                 V['n_pass'], V['n_total']))

# ---------- 旋钮判决表（机械渲染，PREREG §3 S3） ----------
k = R['S3_knobs']
o, f, s = k['E_orig'], k['E_flat'], k['E_refsub']
vv = k['visc_visible']
rows = [
    ('黏性 VISC2', '否（非算子输入，源码走读）', '0（解析论证；管线自检逐位一致=%s）' % k['selfcheck_bitwise'],
     '日1 三维 |u|max %.2f→%.2f cm/s（%.2f×，%s）' % (vv['day1_umax3d_abs_cm'][0], vv['day1_umax3d_abs_cm'][1],
                                                    vv['ratio'], vv['pointer'])),
    ('缩短积分', '否（时间非算子输入）', '0（解析论证）', '最小闭环无落盘读数，不填'),
    ('平底替换', '是（换 h）', 'E_L2^u %.3e→%.3e（比值 %.3f，P4）' % (o['EL2_u'], f['EL2_u'], k['ratio_flat']),
     'E56 平底 7/7 日1 u_max=0.0'),
    ('地形平滑', '是（改 h）', 'S1 四档：%s（P1/P6）' % '，'.join(
        '%s=%.3e' % (t_, R['S1_tiers'][t_]['EL2_u']) for t_ in TIERS), '最小闭环无落盘读数，不填'),
    ('参考态扣除', '是（改 rho 输入）', 'E_L2^u %.3e→%.3e（比值 %.3f，P5）' % (o['EL2_u'], s['EL2_u'],
                                                                     k['ratio_refsub']), '最小闭环无落盘读数，不填'),
    ('加密网格', '是（改几何）', 'p̂12/p̂23：光滑 %.2f/%.2f，陡 %.2f/%.2f（P2/P3）' % (
        R['S2_refine']['smooth']['p12'], R['S2_refine']['smooth']['p23'],
        R['S2_refine']['steep']['p12'], R['S2_refine']['steep']['p23']), '最小闭环无落盘读数，不填'),
]
with open(f'{FIN}/knob_table.md', 'w') as fp:
    fp.write('# 旋钮判决表（机械渲染自 MMS_OPERATOR.json + verdict.json，%s）\n\n' % V['date'])
    fp.write('| 旋钮 | 是否进算子 | 算子误差变化（制造场，解析真值） | 可见读数变化（既有落盘） |\n|---|---|---|---|\n')
    for r_ in rows:
        fp.write('| %s | %s | %s | %s |\n' % r_)
    fp.write('\n口径：<1e-12 记「不碰误差源」；算子误差≠演化伪流（PREREG §8.1）；'
             '首步 ubarmax（正压）近不变 vs 日 1 三维 |u|max 大动见 verdict.json A3，两者口径不同、不混称。\n')
print('落盘 knob_table.md')
