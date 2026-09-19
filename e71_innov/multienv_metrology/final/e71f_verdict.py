#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E71M 正式版 · 步骤三：机械判分 → verdict.json。

判据全部来自封存的 PREREG §5（15 条真预测，每条单一布尔式）；本脚本只是把它们逐字翻译成代码。
人不改判：被推翻的条目原样保留；反向条款的话术分支由布尔结果机械选择。
门控：PREREG 未封存/不匹配 → 拒绝；E71_FINAL_RESULTS.json 缺失 → 拒绝。
S1/S2 结果文件缺失 → 记"未跑"（PREREG §6 允许）。
"""
import hashlib, json, os, sys, time

FIN = '/data/xinyuan/GOAI_ai4s_env/e71_innov/multienv_metrology/final'
PRE = f'{FIN}/PREREG_multienv_metrology.md'
SHA = f'{FIN}/PREREG_multienv_metrology.sha256'
RES = f'{FIN}/E71_FINAL_RESULTS.json'

if not os.path.exists(SHA):
    sys.exit('拒绝判分：预注册尚未封存。')
want = open(SHA).readline().split()[0]
got = hashlib.sha256(open(PRE, 'rb').read()).hexdigest()
if want != got:
    sys.exit('拒绝判分：PREREG 与封存 sha256 不符。')
if not os.path.exists(RES):
    sys.exit('拒绝判分：E71_FINAL_RESULTS.json 不存在（先跑 e71f_axes45.py 与 e71f_metrology.py）。')
R = json.load(open(RES))
SELF_SHA = hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()


def get(path):
    o = R
    for k in path.split('.'):
        o = o[k]
    return o


P = []  # (id, 陈述, 数值快照, 布尔)


def add(pid, stmt, vals, ok):
    P.append(dict(id=pid, statement=stmt, values=vals, prediction_pass=bool(ok)))


rA = get('pairs.z_45.rho_A'); rB = get('pairs.z_45.rho_B'); rAP = get('pairs.z_45.rho_AP')
add('P1a', 'ρ(A_z,A_45) >= 0.85', dict(rho_A=rA), rA >= 0.85)
add('P1b', 'ρ(B_z,B_45) >= 0.75', dict(rho_B=rB), rB >= 0.75)
add('P2a', '【头条】ρ(A⊥_z,A⊥_45) <= ρ(A_z,A_45) - 0.40（扣 D 塌方 >= 0.40）',
    dict(rho_AP=rAP, rho_A=rA, collapse=round(rA - rAP, 4)), rAP <= rA - 0.40)
v = get('M4_millsap3.rho_D45_A45')
add('P2b', 'ρ(D_45,A_45) >= 0.95', dict(rho_D45_A45=v), v >= 0.95)
v = get('M4_millsap3.rho_Dz_D45')
add('P2c', 'ρ(D_z,D_45) >= 0.85', dict(rho_Dz_D45=v), v >= 0.85)
v = get('M6_decision3.kappa.m_45')
add('P3a', 'κ(门_m,门_45) <= 0.55', dict(kappa_m_45=v), v is not None and v <= 0.55)
v = get('M6_decision3.conv_A_within_S_A_z45')
add('P3b', 'ρ(A_z,A_45 | S_A) <= 0.50', dict(restricted_conv=v), v <= 0.50)
vA = get('M2_gtheory3.A.var_p_share')
add('P4a', 'A 的 σ²_p 占比 ∈ [0.75, 0.92]', dict(var_p_share_A=vA), vA is not None and 0.75 <= vA <= 0.92)
vAt = get('M2_gtheory3.A.var_p_share_ties'); vBt = get('M2_gtheory3.B.var_p_share_ties')
add('P4b', 'B 的 σ²_p 占比(平均秩版) >= A 的同版占比', dict(B_ties=vBt, A_ties=vAt),
    vBt is not None and vAt is not None and vBt >= vAt)
kA = get('M2_gtheory3.A.k_star_G0p8'); kB = get('M2_gtheory3.B.k_star_G0p8')
add('P4c', 'k*(G>=0.8) 对 A、B 均 = 1', dict(k_star_A=kA, k_star_B=kB), kA == 1 and kB == 1)
v = get('M3_icp3.frac_reject')
add('P5a', '3环境全体判死率 ∈ [0.25, 0.45]', dict(frac_reject=v), 0.25 <= v <= 0.45)
v = get('M3_icp3.n_add_reject_in_inv2')
add('P5b', '试点 88 把两环境不变集合中被 45° 追加判死 <= 17', dict(n_add_reject=v, inv2_size=get('M3_icp3.inv2_size')), v <= 17)
v = get('M3_icp3.invariant3_size')
add('P5c', '三环境不变集合 >= 40 把（上界 80 由已知三向存活数钉死，不属预测内容）', dict(invariant3_size=v), v >= 40)
v = get('M3_icp3.invariant3_temp_ratio_share')
add('P5d', '三环境不变集合中 temp/temp 比值型占比 >= 2/3', dict(temp_ratio_share=v), v is not None and v >= 2.0 / 3.0)
v = get('M4_millsap3.frac_A45_lt0_given_Az_ge_0p7')
add('P6', 'P(A_45 < 0 | A_z >= 0.7) <= 0.03', dict(frac=v), v is not None and v <= 0.03)

n_pass = sum(1 for x in P if x['prediction_pass'])

# 敏感性翻转检查（另一 spearman 口径重判；只打旗，不改判——PREREG §2/§7）
# 覆盖两口径均有落数的全部预测：P1a/P1b/P2a/P2b/P2c/P3b/P4a/P4c 用平均秩版重判；
# P4b 主口径本就是平均秩版（PREREG §2 唯一例外），反向检查用 argsort 版；
# P3a/P5a-P5d/P6 为计数/占比/κ 类判据，无并列口径分歧，不设翻转检查。
rAt = get('pairs.z_45.rho_A_ties'); rBt = get('pairs.z_45.rho_B_ties'); rAPt = get('pairs.z_45.rho_AP_ties')
vAt2 = get('M2_gtheory3.A.var_p_share_ties')
kAt = get('M2_gtheory3.A.k_star_ties'); kBt = get('M2_gtheory3.B.k_star_ties')
vAa = get('M2_gtheory3.A.var_p_share'); vBa = get('M2_gtheory3.B.var_p_share')
vD1t = get('M4_millsap3.rho_D45_A45_ties'); vD2t = get('M4_millsap3.rho_Dz_D45_ties')
vRCt = get('M6_decision3.conv_A_within_S_A_z45_ties')
alt_checks = [
    ('P1a', dict(rho_A_ties=rAt), rAt >= 0.85),
    ('P1b', dict(rho_B_ties=rBt), rBt >= 0.75),
    ('P2a', dict(rho_AP_ties=rAPt, rho_A_ties=rAt, collapse_ties=round(rAt - rAPt, 4)), rAPt <= rAt - 0.40),
    ('P2b', dict(rho_D45_A45_ties=vD1t), vD1t >= 0.95),
    ('P2c', dict(rho_Dz_D45_ties=vD2t), vD2t >= 0.85),
    ('P3b', dict(restricted_conv_ties=vRCt), vRCt <= 0.50),
    ('P4a', dict(var_p_share_A_ties=vAt2), vAt2 is not None and 0.75 <= vAt2 <= 0.92),
    ('P4b', dict(B_argsort=vBa, A_argsort=vAa), vBa is not None and vAa is not None and vBa >= vAa),
    ('P4c', dict(k_star_A_ties=kAt, k_star_B_ties=kBt), kAt == 1 and kBt == 1),
]
flips = []
for pid, vals, alt in alt_checks:
    main = next(x['prediction_pass'] for x in P if x['id'] == pid)
    if bool(alt) != main:
        flips.append(dict(id=pid, alt_values=vals, alt_pass=bool(alt)))

# 反向条款的机械话术分支（PREREG §5 预写，两版都在，此处只选行）
branches = {}
if not next(x for x in P if x['id'] == 'P1a')['prediction_pass'] and rA < 0.75:
    branches['P1'] = '降级：相关级收敛不复现——回到"排名本身也不可迁移"的原方案版本叙事'
if next(x for x in P if x['id'] == 'P1a')['prediction_pass'] and not next(x for x in P if x['id'] == 'P2a')['prediction_pass']:
    branches['P2'] = '头条赌注不中：结论改写为"A 的可迁移性并非 D 直通车"，机制账本作废，照登'
branches['P4c'] = ('给尺子排名一个场景就够，给尺子发证三个场景都不够（见 P3）'
                   if next(x for x in P if x['id'] == 'P4c')['prediction_pass']
                   else '连排名都要 k>=2 个场景')

# 派生量一致性检查（已知数派生，非预测；PREREG §3/§4）
derived = dict(kappa_z_45=get('M6_decision3.kappa.z_45'), jaccard_z_45=get('M6_decision3.jaccard.z_45'),
               expected_from_knowns='κ≈0.41 / Jaccard≈0.27（由 204/454/140/15376 派生）',
               n_gate_45=get('anchors.n_gate_45'), n_S_A_survive_45=get('anchors.n_S_A_survive_45'),
               n_triple=get('anchors.n_triple'))

# S 组：文件在则收录，不在则"未跑"
def s_status(fp, key):
    if not os.path.exists(fp):
        return dict(status='未跑', note='PREREG §6 允许；按方案记入 OPEN_PROBLEMS')
    s = json.load(open(fp))
    out = dict(status='已跑', file=os.path.basename(fp), **{k: s.get(k) for k in s if not k.startswith('_')})
    if key == 'S1' and s.get('var_p_share') is not None:
        out['prediction_pass'] = bool(s['var_p_share'] >= 0.75)
    return out


verdict = dict(
    module='multienv_metrology_final', date=time.strftime('%F %T'),
    sealed_prereg_sha256=want,
    results_file='E71_FINAL_RESULTS.json',
    anchors_pass=R.get('anchors_pass'),
    pipeline_flag=None if R.get('anchors_pass') else 'PIPELINE_SUSPECT: 正对照锚未全过，全部判定挂旗',
    low_n_flag=bool(R['run_meta'].get('low_n')),
    low_intersection_flag=bool(R['run_meta'].get('n_candidates', 0) < 15000),
    inv2_anchor_pass=R.get('inv2_anchor_pass'),
    code_sha_verdict=SELF_SHA,
    code_sha_from_results=R.get('code_sha'),
    n_predictions=len(P), n_pass=n_pass, n_fail=len(P) - n_pass,
    predictions=P,
    sensitivity_flips=flips,
    narrative_branches=branches,
    derived_consistency_checks=derived,
    S1_e60_B_gstudy=s_status(f'{FIN}/E71_FINAL_S1_E60.json', 'S1'),
    S2_bh93_negctrl=s_status(f'{FIN}/E71_FINAL_S2_BH93.json', 'S2'),
    discipline='判分机械输出，人不改判；被推翻条目原样保留上台；封存后发现笔误只记 DEVIATIONS.md')
json.dump(verdict, open(f'{FIN}/verdict.json', 'w'), indent=1, ensure_ascii=False)
print('VERDICT  %d/%d 中' % (n_pass, len(P)))
for x in P:
    print(' %-4s %s  %s  %s' % (x['id'], '中 ' if x['prediction_pass'] else '不中', x['statement'], json.dumps(x['values'])))
if flips:
    print(' 敏感性翻转:', json.dumps(flips, ensure_ascii=False))
print(' → verdict.json')
