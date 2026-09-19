#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""abm_verdict.py — audit_battery_meta 机械判分（PREREG_audit_battery_meta.md v2 §4/§5/§8 的逐字翻译）。

封存门控：PREREG_audit_battery_meta.sha256 缺失或哈希不匹配即拒绝运行（--selftest <目录> 例外，只判夹具产出）。
输入（缺文件 → 对应条目 NOT_RUN；缺判定所需字段 → NOT_RUN ＋ PIPELINE_SUSPECT）：
  ABM_MR_CONSISTENCY.json（模块①）  ABM_GOODHART_MAP.json（模块③，只作锚 V1 旁证）
  ABM_KILL_MATRIX.json（模块②）     ABM_FILTER_CHAIN.json（模块④）
输出：verdict.json。只有 11 条真预测进 tally；K1（已知答案）、C1/C2（构造性）另列不计数。人不改判。
"""
import hashlib, json, os, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PREREG = os.path.join(HERE, 'PREREG_audit_battery_meta.md')
SHAF = PREREG.replace('.md', '.sha256')
PASS, FAIL, NOT_RUN, UNJ = 'PASS', 'FAIL', 'NOT_RUN', 'UNJUDGEABLE'


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(65536), b''):
            h.update(blk)
    return h.hexdigest()


def seal_gate():
    if not (os.path.exists(PREREG) and os.path.exists(SHAF)):
        sys.exit('[SEAL GATE] PREREG 或 .sha256 缺失 — 未封存，拒绝判分。')
    rec = open(SHAF).read().split()
    if not rec or rec[0] != sha256(PREREG):
        sys.exit('[SEAL GATE] PREREG sha256 与封存记录不匹配 — 拒绝判分。')


class Missing(Exception):
    pass


def need(d, *path):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur or cur[k] is None:
            raise Missing('.'.join(str(p) for p in path))
        cur = cur[k]
    return cur


def P(statement, status, value, source):
    return dict(statement=statement, status=status, value=value, source=source)


def main():
    selftest = len(sys.argv) > 2 and sys.argv[1] == '--selftest'
    D = sys.argv[2] if selftest else HERE
    if not selftest:
        seal_gate()

    def load(name):
        p = os.path.join(D, name)
        if not os.path.exists(p):
            return None, None
        return json.load(open(p)), sha256(p)

    mr, sha_mr = load('ABM_MR_CONSISTENCY.json')
    gm, sha_gm = load('ABM_GOODHART_MAP.json')
    km, sha_km = load('ABM_KILL_MATRIX.json')
    fc, sha_fc = load('ABM_FILTER_CHAIN.json')
    flags = dict(PIPELINE_SUSPECT=False, LOW_COVERAGE=False,
                 downgraded=bool(km and km.get('downgraded')),
                 fallback_two_level=bool(fc and fc.get('fallback_two_level')))
    anchors, preds, known, constructive, suspect_reasons = {}, {}, {}, {}, []

    def suspect(why):
        flags['PIPELINE_SUSPECT'] = True; suspect_reasons.append(why)

    # ================= 模块①：V1 / V3 / K1 =================
    DEAD13 = {('Pnet_MW', 'A1'), ('Pnet_MW', 'A3'), ('Pnet_MW', 'A4'), ('Pnet_MW', 'A7'),
              ('deep_dc_rms', 'A1'), ('deep_dc_rms', 'A4'), ('deep_dc_rms', 'A6'),
              ('deep_dc_rms', 'A8'), ('deep_dc_rms', 'A9'), ('temp_d400', 'A6'),
              ('uv_ratio', 'A2'), ('uv_ratio', 'A6'), ('uv_ratio', 'A7')}
    k1_stmt = 'K1（已知答案，不计数）：机器可判格上 checker 与 KILLBOARD 不一致数 = 0'
    if mr is None:
        anchors['V1_dead13'] = None; anchors['V3_real_anchors'] = None
        known['K1'] = P(k1_stmt, NOT_RUN, None, 'ABM_MR_CONSISTENCY.json (缺)')
    else:
        try:
            got = {tuple(c) for c in need(mr, 'kb_dead_cells')}
            anchors['V1_dead13'] = (got == DEAD13)
            if not anchors['V1_dead13']:
                suspect('V1 死格集合不符')
        except Missing as e:
            anchors['V1_dead13'] = None; suspect('V1 缺字段 %s' % e)
        try:
            ra = need(mr, 'real_anchor_check')
            a = need(ra, 'Pnet_MW_A3A4_dead'); b = need(ra, 'deep_dc_rms_A9_dead')
            anchors['V3_real_anchors'] = dict(Pnet_MW_A3A4_dead=bool(a), deep_dc_rms_A9_static_A1_dead=bool(b), ok=bool(a) and bool(b))
            if not (a and b):
                suspect('V3 真实阳性锚复导出不成立')
        except Missing as e:
            anchors['V3_real_anchors'] = None; suspect('V3 缺字段 %s' % e)
        if mr.get('pipeline_issues'):
            suspect('模块① pipeline_issues 非空')
        try:
            nm = int(need(mr, 'n_machine'))
            if nm < 24:
                flags['LOW_COVERAGE'] = True
            nd = need(mr, 'n_disagree')
            known['K1'] = P(k1_stmt, PASS if int(nd) == 0 else FAIL,
                            dict(n_machine=nm, n_disagree=int(nd),
                                 discrepancies=[(x.get('row'), x.get('col'), x.get('kb'), x.get('checker')) for x in mr.get('discrepancies', [])],
                                 author_expected_at_seal='n_disagree=2（temp_d400·A1、deep_dc_rms·A6）'),
                            'ABM_MR_CONSISTENCY.json:n_disagree')
        except Missing as e:
            known['K1'] = P(k1_stmt, NOT_RUN, None, 'ABM_MR_CONSISTENCY.json 缺字段 %s' % e); suspect('K1 缺字段 %s' % e)
    if gm is not None:
        anchors['V1b_goodhart_dead_set_match'] = gm.get('dead_set_match')
        if gm.get('dead_set_match') is not True:
            suspect('模块③ 死格集合与 KILLBOARD 不符')

    # ================= 模块②：P2b–P2i、C1、V5 =================
    BETS = [
        ('P2b', 'mono_norm 类：可判体 ≥1 且 漏网数 = 可判体数（零差分杀死）', 'mono_norm',
         lambda c: c['n_judgeable'] >= 1 and c['escaped'] == c['n_judgeable']),
        ('P2c', 'sign_flip 类漏网数 = 0', 'sign_flip', lambda c: c['escaped'] == 0),
        ('P2d', 'boxwidth_dep 类漏网数 ≥ 1', 'boxwidth_dep', lambda c: c['escaped'] >= 1),
        ('P2e', 'irrelevant_num 类漏网数 = 0', 'irrelevant_num', lambda c: c['escaped'] == 0),
        ('P2f', 'clip_cheat 类漏网数 ≥ 1', 'clip_cheat', lambda c: c['escaped'] >= 1),
        ('P2g', 'wrong_region 类漏网数 ≥ 1', 'wrong_region', lambda c: c['escaped'] >= 1),
        ('P2h', 'wrong_layer 类漏网数 ≥ 1', 'wrong_layer', lambda c: c['escaped'] >= 1),
    ]
    CLS = ['unit_scale', 'mono_norm', 'sign_flip', 'wrong_region', 'wrong_layer', 'irrelevant_num', 'clip_cheat', 'boxwidth_dep']
    c1_stmt = 'C1（构造性，不计数）：unit_scale 类可判体 ≥1 且全部漏网'
    p2i_stmt = '主口径总检出率 killed/可判体 ∈ [0.20, 0.60]'
    if km is None:
        for pid, stmt, cname, fn in BETS:
            preds[pid] = P(stmt, NOT_RUN, None, 'ABM_KILL_MATRIX.json (缺)')
        preds['P2i'] = P(p2i_stmt, NOT_RUN, None, 'ABM_KILL_MATRIX.json (缺)')
        constructive['C1'] = P(c1_stmt, NOT_RUN, None, 'ABM_KILL_MATRIX.json (缺)')
        anchors['V5_battery_u_d800_rms'] = None
    else:
        cls = km.get('classes') or {}
        missing = [c for c in CLS if c not in cls]
        if missing:
            suspect('模块② 类缺失 %s' % missing)
        pl = km.get('pipeline') or {}
        if pl.get('impl_anchor_ok') is False:
            suspect('ext_base_quantities 实现锚不符')
        if pl.get('static_umax_match_E56_VERDICT') is False:
            suspect('静止线 u_max 与 E56_VERDICT 不符')
        if pl.get('N_ref_consistent') is False:
            suspect('boxwidth N_ref 在 Z58 上不一致')
        try:
            v5 = bool(need(km, 'anchor_V5', 'ok'))
            anchors['V5_battery_u_d800_rms'] = dict(ok=v5, verdicts=km['anchor_V5'].get('verdicts'))
            if not v5:
                suspect('V5 电池内锚不成立')
        except Missing as e:
            anchors['V5_battery_u_d800_rms'] = None; suspect('V5 缺字段 %s' % e)

        def judge_class(stmt, cname, fn, src_label):
            c = cls.get(cname)
            if c is None:
                return P(stmt, NOT_RUN, None, 'ABM_KILL_MATRIX.json:classes.%s (缺)' % cname)
            try:
                vals = dict(n_judgeable=int(need(c, 'n_judgeable')), escaped=int(need(c, 'escaped')),
                            killed=int(need(c, 'killed')), unjudgeable=int(need(c, 'unjudgeable')),
                            n_excluded=c.get('n_excluded'), escaped_ids=c.get('escaped_ids'), killed_ids=c.get('killed_ids'))
            except Missing as e:
                suspect('%s 缺字段 %s' % (cname, e))
                return P(stmt, NOT_RUN, None, 'ABM_KILL_MATRIX.json:classes.%s 缺字段 %s' % (cname, e))
            if vals['n_judgeable'] == 0:
                return P(stmt, UNJ, vals, 'ABM_KILL_MATRIX.json:classes.%s（全类不可判）' % cname)
            return P(stmt, PASS if fn(vals) else FAIL, vals, 'ABM_KILL_MATRIX.json:classes.%s.%s' % (cname, src_label))

        for pid, stmt, cname, fn in BETS:
            preds[pid] = judge_class(stmt, cname, fn, 'escaped')
        constructive['C1'] = judge_class(c1_stmt, 'unit_scale', lambda c: c['escaped'] == c['n_judgeable'], 'escaped')
        ov = km.get('overall') or {}
        if ov.get('n_judgeable') in (None,):
            preds['P2i'] = P(p2i_stmt, NOT_RUN, None, 'ABM_KILL_MATRIX.json:overall 缺字段'); suspect('overall 缺字段')
        elif int(ov['n_judgeable']) == 0:
            preds['P2i'] = P(p2i_stmt, UNJ, ov, 'ABM_KILL_MATRIX.json:overall（无可判体）')
        else:
            rate = float(ov['rate'])
            preds['P2i'] = P(p2i_stmt, PASS if 0.20 <= rate <= 0.60 else FAIL,
                             dict(rate=rate, wilson95=ov.get('wilson95'), n_killed=ov.get('n_killed'), n_judgeable=ov.get('n_judgeable'),
                                  raw_rate=ov.get('raw_rate'), abs_rate_sensitivity=ov.get('abs_rate')),
                             'ABM_KILL_MATRIX.json:overall.rate')

    # ================= 模块④：V2 / V4 / P4a–P4c / C2 =================
    P4 = [('P4a', '|L3| ∈ [1, 1537]'), ('P4b', '几何序 |L1|−|L2| ≥ |L2|−|L3|'), ('P4c', '|S_A ∩ L3| ≤ 122')]
    c2_stmt = 'C2（构造性，不计数）：H=0 三种排法末级幸存集合相同'
    if fc is None:
        for pid, stmt in P4:
            preds[pid] = P(stmt, NOT_RUN, None, 'ABM_FILTER_CHAIN.json (缺)')
        constructive['C2'] = P(c2_stmt, NOT_RUN, None, 'ABM_FILTER_CHAIN.json (缺)')
        anchors['V2_B_vs_E57_maxdiff'] = None; anchors['V4_echo_204_444_12'] = None
    else:
        pa = fc.get('pipeline_anchor') or {}
        anchors['V2_B_vs_E57_maxdiff'] = pa.get('max_abs_diff_B_vs_E57')
        anchors['V2_A_vs_E57_maxdiff_reported'] = pa.get('max_abs_diff_A_vs_E57')
        if pa.get('max_abs_diff_B_vs_E57') != 0.0:
            suspect('V2 B 与 E57 不等（或缺）')
        an = fc.get('anchors') or {}
        anchors['V4_echo_204_444_12'] = an.get('match')
        if an.get('match') is not True:
            suspect('V4 204/444/12 回显不符（或缺）')
        try:
            h0 = need(fc, 'H_results', '0.00')
            constructive['C2'] = P(c2_stmt, PASS if need(h0, 'final_sets_identical') else FAIL,
                                   dict(single_step_kill=h0.get('single_step_kill_on_L0')), 'ABM_FILTER_CHAIN.json:H_results.0.00.final_sets_identical')
        except Missing as e:
            constructive['C2'] = P(c2_stmt, NOT_RUN, None, 'ABM_FILTER_CHAIN.json 缺字段 %s' % e); suspect('C2 缺字段 %s' % e)
        if flags['fallback_two_level']:
            for pid, stmt in P4:
                preds[pid] = P(stmt, NOT_RUN, 'fallback_two_level', 'ABM_FILTER_CHAIN.json（回退两级）')
        else:
            try:
                lv = need(fc, 'levels')
                n1 = int(need(lv, 'L1', 'n_survive')); n2 = int(need(lv, 'L2', 'n_survive')); n3 = int(need(lv, 'L3', 'n_survive'))
                preds['P4a'] = P(P4[0][1], PASS if 1 <= n3 <= 1537 else FAIL, dict(n_L3=n3), 'ABM_FILTER_CHAIN.json:levels.L3.n_survive')
                preds['P4b'] = P(P4[1][1], PASS if (n1 - n2) >= (n2 - n3) else FAIL,
                                 dict(L1=n1, L2=n2, L3=n3, drop_rotate=n1 - n2, drop_absurd=n2 - n3), 'ABM_FILTER_CHAIN.json:levels')
            except Missing as e:
                preds['P4a'] = P(P4[0][1], NOT_RUN, None, 'ABM_FILTER_CHAIN.json 缺字段 %s' % e)
                preds['P4b'] = P(P4[1][1], NOT_RUN, None, 'ABM_FILTER_CHAIN.json 缺字段 %s' % e)
                suspect('P4a/P4b 缺字段 %s' % e)
            sa = fc.get('S_A_intersect_L3')
            if sa is None:
                preds['P4c'] = P(P4[2][1], NOT_RUN, None, 'ABM_FILTER_CHAIN.json:S_A_intersect_L3 (缺)'); suspect('P4c 缺字段')
            else:
                preds['P4c'] = P(P4[2][1], PASS if int(sa) <= 122 else FAIL,
                                 dict(S_A_intersect_L3=int(sa), n_S_A=an.get('n_both_204')), 'ABM_FILTER_CHAIN.json:S_A_intersect_L3')

    order = ['P2b', 'P2c', 'P2d', 'P2e', 'P2f', 'P2g', 'P2h', 'P2i', 'P4a', 'P4b', 'P4c']
    tally = {s: sum(1 for k in order if preds[k]['status'] == s) for s in (PASS, FAIL, NOT_RUN, UNJ)}
    out = dict(
        entry='audit_battery_meta', when=datetime.datetime.now().astimezone().isoformat(), selftest=selftest,
        prereg_sha=(sha256(PREREG) if os.path.exists(PREREG) else None), code_sha=sha256(os.path.abspath(__file__)),
        input_sha=dict(ABM_MR_CONSISTENCY=sha_mr, ABM_GOODHART_MAP=sha_gm, ABM_KILL_MATRIX=sha_km, ABM_FILTER_CHAIN=sha_fc),
        flags=flags, pipeline_suspect_reasons=suspect_reasons, anchors=anchors,
        predictions={k: preds[k] for k in order}, tally=tally, n_counted=len(order),
        known_checks=known, constructive=constructive,
        derived_consistency_checks=(fc or {}).get('derived', {}),
        note='机械判分；只 11 条真预测计数；K1/C1/C2 照判不计数；被推翻原样保留；锚不过全体挂 PIPELINE_SUSPECT（判定保留）。')
    with open(os.path.join(D, 'verdict.json'), 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(dict(tally=tally, flags=flags, reasons=suspect_reasons), ensure_ascii=False))


if __name__ == '__main__':
    main()
