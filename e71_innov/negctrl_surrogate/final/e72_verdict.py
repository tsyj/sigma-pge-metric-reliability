#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E72 机械判分器（negctrl_surrogate）。
只读 E72_VALID.json，按 PREREG §5 冻结阈值逐条求值真预测 P1–P4、P6、P7（共 6 条），
输出 verdict.json。原 P5 已降级为验证性断言 V4（PREREG §1.4）：同门槛照算照印于
descriptive_P5_demo，不入计分。不重算任何统计量；不读任何 run 数据。
前置硬门：封存存在且入档五件哈希吻合（PREREG §0-2）。
判定三值：TRUE（押中）/ FALSE（被推翻，原样保留）/ AMBIGUOUS（按预注册条款不可判，
不计入押中也不计入被推翻）。两域合并规则：任一域 FAIL → FALSE；否则任一域 AMB → AMBIGUOUS；
两域皆 PASS → TRUE。
"""
import hashlib
import json
import os
import time

FIN = '/data/xinyuan/GOAI_ai4s_env/e71_innov/negctrl_surrogate/final'
PREREG = f'{FIN}/PREREG_negctrl_surrogate.md'
SEALFN = PREREG + '.sha256'
VALIDFN = f'{FIN}/E72_VALID.json'
VALIDPY = f'{FIN}/e72_valid.py'
VERDICTPY = f'{FIN}/e72_verdict.py'
SEEDSFN = f'{FIN}/SEEDS82.json'
SELFTESTFN = f'{FIN}/E72_SELFTEST_ZONAL.json'
DEVFN = f'{FIN}/DEVIATIONS.md'

# ---- 冻结阈值（与 PREREG §5 一字一句对应；改这里=改判据=作废） ----
TH = dict(
    P1_rho_min=0.50,          # ρ_ms(Dlogr, Alogr) 每域下限
    P1_point=(0.80, 0.95),    # 点预测区间（不判分，只报告）
    P2_surv_min=0.30,         # 82 把存活率下限（分母恒 82，缺席=死亡）
    P2_enrich_min=5.0,        # 富集倍数下限
    P3_rho_min=-0.45,         # ρ_ms(Adiff, B) 每域下限（缓解方向为“更大”）
    P4_maxA_max=0.70,         # max{Alogr : |Dlogr|<=0.3} 每域上限；空集=vacuous PASS
    P5_impr_min=3.0,          # 仅 V4 描述性判定用（原 P5 已降级，PREREG §1.4）
    P5_lr_min=3.0,            # 仅 V4 描述性判定用（原 P5 已降级，PREREG §1.4）
    P6_frac_max=0.55,         # frac(|OS_lr| 比 |OS_raw| 更接近 1) 上限
    P7_abstau_min=0.85,       # |tau_b(H, VISC2)| 每域 sweep 下限
    MIN_PAIRS=20,             # 配对数下限，低于则 P1–P4、P6 记 AMBIGUOUS
    MIN_SWEEP=5,              # sweep 档位下限，低于则 P5–P7 记 AMBIGUOUS
)


def sha256(fn):
    h = hashlib.sha256()
    with open(fn, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def require_seal():
    """封存门（PREREG §0-2）：核对 .sha256 入档全部五件。PREREG / SEEDS82 不符永不放行；
    两脚本与自检文件不符仅当 DEVIATIONS.md 在场才放行。"""
    assert os.path.exists(SEALFN), '拒判：预注册未封存'
    m = {}
    for line in open(SEALFN):
        p = line.split()
        if len(p) == 2 and len(p[0]) == 64:
            m[os.path.basename(p[1])] = p[0]
    strict = {os.path.basename(PREREG), os.path.basename(SEEDSFN)}
    dev = os.path.exists(DEVFN)
    shas = {}
    for fn in (PREREG, VALIDPY, VERDICTPY, SEEDSFN, SELFTESTFN):
        bn = os.path.basename(fn)
        assert bn in m, '拒判：封存记录缺 %s 的哈希' % bn
        assert os.path.exists(fn), '拒判：缺文件 %s' % bn
        shas[bn] = sha256(fn)
        if shas[bn] != m[bn]:
            if bn in strict:
                raise AssertionError('拒判：%s 哈希与封存记录不符（判据/种子类文件，永不放行）' % bn)
            if not dev:
                raise AssertionError('拒判：%s 哈希与封存记录不符且无 DEVIATIONS.md（§10 未申报）' % bn)
    return dict(prereg_sha=m[os.path.basename(PREREG)],
                runtime_valid_py_sha=shas[os.path.basename(VALIDPY)],
                runtime_verdict_py_sha=shas[os.path.basename(VERDICTPY)],
                sealed_valid_py_sha=m[os.path.basename(VALIDPY)],
                sealed_verdict_py_sha=m[os.path.basename(VERDICTPY)],
                deviations_present=dev)


def g(d, path, default=None):
    cur = d
    for p in path.split('.'):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def combine(parts):
    st = [p['status'] for p in parts.values()]
    if any(s == 'FAIL' for s in st):
        return 'FALSE'
    if any(s == 'AMBIGUOUS' for s in st):
        return 'AMBIGUOUS'
    return 'TRUE'


def main():
    gate = require_seal()
    prereg_sha = gate['prereg_sha']
    V = json.load(open(VALIDFN))
    assert V.get('prereg_sha') == prereg_sha, '拒判：E72_VALID.json 的 prereg_sha 与当前封存不符'
    doms = V['domains']
    P = {}

    def per_dom(fn):
        return {d: fn(doms[d], d) for d in ('merid', 'diag45')}

    def pairs_ok(b):
        return (b.get('n_pairs') or 0) >= TH['MIN_PAIRS'] and (b.get('n_candidates') or 0) > 0

    def sweep_ok(b):
        return (g(b, 'sweep.n_levels') or 0) >= TH['MIN_SWEEP']

    # P1
    def p1(b, d):
        if not pairs_ok(b):
            return dict(status='AMBIGUOUS', reason='配对数或候选数不足')
        v = g(b, 'struct.rho_D_A_logr')
        return dict(status='PASS' if v >= TH['P1_rho_min'] else 'FAIL', rho_D_A_logr=v,
                    perm_p=g(b, 'struct.p_D_A_logr'),
                    in_point_range=bool(TH['P1_point'][0] <= v <= TH['P1_point'][1]),
                    secondary_diff=g(b, 'struct.rho_D_A_diff'),
                    secondary_scipy=g(b, 'struct.rho_D_A_logr_scipy'))
    P['P1'] = per_dom(p1)

    # P2
    def p2(b, d):
        if not pairs_ok(b):
            return dict(status='AMBIGUOUS', reason='配对数或候选数不足')
        s = b['seeds']
        okk = s['surv_rate'] >= TH['P2_surv_min'] and s['enrichment'] >= TH['P2_enrich_min']
        return dict(status='PASS' if okk else 'FAIL', surv_rate=s['surv_rate'],
                    n_survive=s['n_survive'], enrichment=s['enrichment'],
                    base_frac=s['base_frac'], n_absent=s['n_absent'])
    P['P2'] = per_dom(p2)

    # P3
    def p3(b, d):
        if not pairs_ok(b):
            return dict(status='AMBIGUOUS', reason='配对数或候选数不足')
        v = g(b, 'exclusivity.rho_Adiff_B')
        return dict(status='PASS' if v >= TH['P3_rho_min'] else 'FAIL', rho_Adiff_B=v,
                    raw_contrast=g(b, 'exclusivity.rho_A32_B'),
                    secondary_scipy=g(b, 'exclusivity.rho_Adiff_B_scipy'))
    P['P3'] = per_dom(p3)

    # P4
    def p4(b, d):
        if not pairs_ok(b):
            return dict(status='AMBIGUOUS', reason='配对数或候选数不足')
        gg = g(b, 'gates.logr')
        if not gg or gg.get('n_absD_le03', 0) == 0:
            return dict(status='PASS', vacuous=True, n_absD_le03=0,
                        note='|Dlogr|<=0.3 集合为空，按预注册条款空真')
        v = gg['maxA_absD_le03']
        return dict(status='PASS' if v <= TH['P4_maxA_max'] else 'FAIL',
                    maxA_absD_le03=v, n_absD_le03=gg['n_absD_le03'])
    P['P4'] = per_dom(p4)

    # V4（原 P5，已降级为验证性断言，PREREG §1.4）：同门槛照算照印，不入 P、不计数
    def p5_desc(b, d):
        sw = b.get('sweep', {})
        t = g(sw, 'demo.u_d800_rms')
        if not sweep_ok(b) or not t:
            return dict(status='AMBIGUOUS', reason='sweep 档位不足或 u|d800|rms 不可算')
        okk = t['improvement_raw'] >= TH['P5_impr_min'] and t['lr_at_vmax'] >= TH['P5_lr_min']
        return dict(status='PASS' if okk else 'FAIL',
                    improvement_raw=t['improvement_raw'], lr_at_vmax=t['lr_at_vmax'])
    P5D = per_dom(p5_desc)

    # P6（OS 家族定义在配对候选族上：先查配对门，与 P1–P4 同，PREREG §3-7）
    def p6(b, d):
        if not pairs_ok(b):
            return dict(status='AMBIGUOUS', reason='配对数或候选数不足')
        sw = b.get('sweep', {})
        os_ = g(sw, 'os_summary')
        if not sweep_ok(b) or not os_ or 'skipped' in os_:
            return dict(status='AMBIGUOUS',
                        reason=g(sw, 'os_summary.skipped') or 'sweep 档位不足')
        v = g(os_, 'overstatement.frac_absOS_shrinks')
        return dict(status='PASS' if v <= TH['P6_frac_max'] else 'FAIL',
                    frac_absOS_shrinks=v, n_ok=os_.get('n_ok'))
    P['P6'] = per_dom(p6)

    # P7（仅共线布尔式；正对照在 7 档阶梯上结构性死亡——纬向参考 tau_HV=1.0 →
    #    自动“判死(与旋钮共线)”，封存前已查明，故不入判据、只作描述性报告）
    def p7(b, d):
        sw = b.get('sweep', {})
        a = g(sw, 'asurr')
        if not sweep_ok(b) or not a or 'skipped' in a:
            return dict(status='AMBIGUOUS', reason=g(sw, 'asurr.skipped') or 'sweep 档位不足')
        c1 = a['abs_tau_HV'] >= TH['P7_abstau_min']
        return dict(status='PASS' if c1 else 'FAIL',
                    abs_tau_HV=a['abs_tau_HV'],
                    posctrl_descriptive=g(a, 'posctrl_err.verdict', '不适用'),
                    h_source=g(sw, 'h_source'))
    P['P7'] = per_dom(p7)

    verdicts = {k: combine(v) for k, v in P.items()}
    out = dict(
        note='negctrl_surrogate 机械判分：只读 E72_VALID.json，阈值冻结于 PREREG §5 与本脚本 TH；'
             '真预测 6 条（P1–P4、P6、P7），原 P5 降级为 V4 见 descriptive_P5_demo',
        prereg_sha=prereg_sha,
        valid_sha=sha256(VALIDFN),
        runtime_valid_py_sha=gate['runtime_valid_py_sha'],
        runtime_verdict_py_sha=gate['runtime_verdict_py_sha'],
        deviations_present=gate['deviations_present'],
        thresholds=TH,
        predictions={k: dict(verdict=verdicts[k], per_domain=P[k]) for k in P},
        descriptive_P5_demo=dict(
            note='验证性断言 V4（PREREG §1.4）：原 P5 门槛照印，不计入任何计数',
            would_be=combine(P5D), per_domain=P5D),
        n_true=sum(1 for v in verdicts.values() if v == 'TRUE'),
        n_false=sum(1 for v in verdicts.values() if v == 'FALSE'),
        n_ambiguous=sum(1 for v in verdicts.values() if v == 'AMBIGUOUS'),
        n_predictions=6,
        generated=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
    )
    json.dump(out, open(f'{FIN}/verdict.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(dict(verdicts=verdicts, n_true=out['n_true'], n_false=out['n_false'],
                          n_ambiguous=out['n_ambiguous']), ensure_ascii=False))


if __name__ == '__main__':
    main()
