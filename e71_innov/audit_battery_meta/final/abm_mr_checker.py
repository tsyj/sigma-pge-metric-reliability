#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""abm_mr_checker.py — 模块① MR 库 checker（PREREG §2.4）。

读 mr_audit.yaml ＋ KILLBOARD.json ＋ 源 JSON → 按 RULES 数值化规则复导出机器可判格 → 逐格对照。
产出：ABM_MR_CONSISTENCY.json、MR_TAXONOMY.md。不一致只列表，不改 KILLBOARD。
用法：abm_mr_checker.py            （真实模式，需封存）
      abm_mr_checker.py --selftest <夹具根> <输出目录>
"""
import json, os, re, sys
import numpy as np
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import abm_common as C


def num(x):
    try:
        return float(x)
    except Exception:
        return float('nan')


def apply_rule(cell, env):
    rule = cell['rule']; inp = cell.get('inputs', {}); used = {}; aux_out = []; flags = {}

    def R(key):
        ok, v = C.resolve(inp[key], env)
        used[key] = dict(ptr=inp[key], ok=ok, value=v)
        if not ok:
            raise KeyError('pointer unresolved: %s' % inp[key])
        return v

    for a in cell.get('aux', []):
        ok, v = C.resolve(a['ptr'], env)
        if a['type'] == 'str_contains':
            res = ok and isinstance(v, str) and a['value'] in v
        elif a['type'] == 'str_startswith':
            res = ok and isinstance(v, str) and v.startswith(a['value'])
        elif a['type'] == 'key_absent_regex':
            res = ok and isinstance(v, dict) and not any(re.search(a['value'], k) for k in v)
        else:
            res = False
        aux_out.append(dict(fact=a['fact'], type=a['type'], ptr=a['ptr'], resolved=ok, holds=bool(res)))
        if 'sets' in a:
            flags[a['sets']] = bool(res)
    if any(not x['resolved'] for x in aux_out):
        raise KeyError('aux pointer unresolved')

    detail = {}
    if rule == 'A1_trivalent':
        if 'k' in inp:
            k = int(R('k')); n = int(R('n'))
        elif 'flat' in inp:
            f = num(R('flat')); s = num(R('steep'))
            if not all(x['holds'] for x in aux_out):
                raise KeyError('A1 direction aux fact not holding')
            n = int(inp.get('n_const', 1)); k = int(f >= s)
        else:
            p = num(R('paired')); n = int(R('n')); k = int(round(p * n))
        lo, hi = C.wilson(k, n)
        verdict = C.v_A1_trivalent(k, n)
        detail = dict(k=k, n=n, point=k / n, wilson95=[lo, hi])
    elif rule == 'A2_zero_channel':
        f = num(R('flat')); t = num(R('typical'))
        r = abs(f) / abs(t) if t != 0 else float('nan')
        verdict = C.DEAD if not np.isfinite(r) else (C.PASS if r < 0.01 else C.EDGE)
        detail = dict(ratio=r)
    elif rule == 'A3_boxwidth':
        if 'ratio_dict' in inp:
            d = R('ratio_dict'); vals = np.array([num(v) for v in d.values()])
            amp = float(vals.max() / vals.min() - 1.0); order_changed = False
            detail = dict(max_over_min=float(vals.max() / vals.min()))
        else:
            base = np.array([num(C.resolve(p, env)[1]) for p in inp['base_list']])
            pert = np.array([num(C.resolve(p, env)[1]) for p in inp['pert_list']])
            used['base_list'] = dict(ptr=inp['base_list'], value=base.tolist())
            used['pert_list'] = dict(ptr=inp['pert_list'], value=pert.tolist())
            if not (np.all(np.isfinite(base)) and np.all(np.isfinite(pert))):
                raise KeyError('A3 list pointer unresolved')
            amp = float(np.max(np.abs(pert / base - 1.0)))
            rho = C.spearman(base, pert); order_changed = rho < 1.0
            detail = dict(order_spearman=rho)
        meaning = flags.get('meaning_changed', False)
        verdict = C.DEAD if (meaning or order_changed) else (C.EDGE if amp >= 0.20 else C.PASS)
        detail.update(amp=amp, meaning_changed=meaning, order_changed=order_changed)
    elif rule == 'A4_phase':
        if 'lastframe' in inp:
            lf = R('lastframe'); c = num(lf['c_g4'])
            rel = [100.0 * (num(lf['p_g4_plus']) / c - 1.0), 100.0 * (num(lf['p_g4_minus']) / c - 1.0)]
        else:
            rv = R('rel_pct'); rel = [num(x) for x in (rv if isinstance(rv, list) else [rv])]
        amp = float(np.max(np.abs(rel)))
        robust = None
        if 'robust_pct' in inp:
            rb = R('robust_pct'); rb = [num(x) for x in (rb if isinstance(rb, list) else [rb])]
            robust = float(np.max(np.abs(rb)))
        if amp < 10:
            verdict = C.PASS
        elif robust is not None and robust < 10:
            verdict = C.EDGE
        elif flags.get('no_robust', False):
            verdict = C.DEAD
        else:
            verdict = C.NA   # 既无稳健版数值也无"无稳健版"事实：不可判
        detail = dict(rel_pct=rel, amp_pct=amp, robust_pct=robust, no_robust=flags.get('no_robust'))
    elif rule == 'A6_rotate':
        A = num(R('A_rho')); B = num(R('B'))
        verdict = C.v_A6(A, B); detail = dict(A_rho=A, B=B)
    elif rule == 'A7_nameswap':
        nm = int(R('named')); an = int(R('anon'))
        verdict = C.DEAD if (nm >= 3 and an <= 1) else (C.PASS if nm == an else C.EDGE)
        detail = dict(named=nm, anon=an)
    elif rule == 'A8_anchor':
        rho = num(R('rho')); p = num(R('p'))
        verdict = C.v_A8(rho, p); detail = dict(rho=rho, p=p)
    elif rule == 'A9_static':
        pa = num(R('a1_paired')); n = len(R('a1_n_len')); k = int(round(pa * n))
        v1 = C.v_A1_trivalent(k, n)
        x = np.array(R('a8_x'), float); y = np.array(R('a8_y'), float)
        rho, p = C.exact_p(x, y); v8 = C.v_A8(rho, p)
        verdict = C.worst([v1, v8])
        detail = dict(A1_part=dict(k=k, n=n, point=k / n, wilson95=list(C.wilson(k, n)), verdict=v1),
                      A8_part=dict(rho=rho, p_exact=p, verdict=v8))
    else:
        raise ValueError('unknown rule ' + rule)
    return verdict, detail, used, aux_out


def main():
    selftest = len(sys.argv) > 1 and sys.argv[1] == '--selftest'
    if selftest:
        env, outdir = sys.argv[2], sys.argv[3]
        yml = os.path.join(env, 'mr_audit.yaml')
    else:
        C.seal_gate(False)
        env, outdir = C.ENV_REAL, C.FINAL
        yml = os.path.join(C.FINAL, 'mr_audit.yaml')
    Y = yaml.safe_load(open(yml))
    kbp = os.path.join(env, Y['killboard'])
    KB = json.load(open(kbp))
    rows, cols = KB['rows'], [c.split()[0] for c in KB['cols']]
    kbv = {(r, cols[j]): KB['grid'][i][j]['verdict'] for i, r in enumerate(rows) for j in range(len(cols))}

    cells_out = []; pipeline_issues = []
    declared = {(c['row'], c['col']) for c in Y['cells']}
    if declared != set(kbv) or len(Y['cells']) != 50:
        pipeline_issues.append('yaml 逐格声明与 KILLBOARD 50 格不一一对应')
    derived = {}
    for c in Y['cells']:
        key = (c['row'], c['col'])
        rec = dict(row=c['row'], col=c['col'], kb_verdict=kbv.get(key), machine=bool(c['machine']))
        if c['machine']:
            try:
                v, det, used, aux = apply_rule(c, env)
                rec.update(rule=c['rule'], checker_verdict=v, detail=det, inputs=used, aux=aux,
                           agree=(v == kbv.get(key)), note=c.get('note'))
                derived[key] = (v, det)
            except Exception as e:
                rec.update(rule=c['rule'], checker_verdict=None, error=str(e), agree=None)
                pipeline_issues.append('%s·%s: %s' % (key[0], key[1], e))
        else:
            rec.update(why=c.get('why'))
        cells_out.append(rec)

    mach = [r for r in cells_out if r['machine']]
    n_machine = len(mach)
    n_ok = sum(1 for r in mach if r.get('checker_verdict') is not None)
    disagree = [dict(row=r['row'], col=r['col'], kb=r['kb_verdict'], checker=r['checker_verdict'], rule=r['rule'],
                     inputs={k: (v.get('ptr'), v.get('value')) for k, v in r['inputs'].items()}, detail=r['detail'])
                for r in mach if r.get('checker_verdict') is not None and not r['agree']]
    dead_cells = sorted([list(k) for k, v in kbv.items() if v == C.DEAD and k[0] != 'truth' and k[1] != 'R'])
    dist = {}
    for v in kbv.values():
        dist[v] = dist.get(v, 0) + 1

    ra = {}
    for name, spec in Y['real_anchors'].items():
        key = (spec['row'], spec['col'])
        if key not in derived:
            ra[name] = None; continue
        v, det = derived[key]
        if spec.get('part') == 'A1':
            ra[name] = (det.get('A1_part', {}).get('verdict') == C.DEAD)
        else:
            ra[name] = (v == C.DEAD)

    out = dict(
        entry='audit_battery_meta/module1', when=C.now(), selftest=selftest,
        code_sha=C.code_sha(__file__), common_sha=C.code_sha(C.__file__), yaml_sha=C.sha256(yml), killboard_sha=C.sha256(kbp),
        prereg_sha=None if selftest else C.sha256(C.PREREG),
        n_cells=len(cells_out), n_machine=n_machine, n_machine_evaluated=n_ok,
        n_disagree=(len(disagree) if n_ok == n_machine else None),
        coverage_gate=dict(threshold=24, n_machine=n_machine, LOW_COVERAGE=n_machine < 24),
        discrepancies=disagree,
        manual_cells=[dict(row=r['row'], col=r['col'], kb=r['kb_verdict'], why=r.get('why')) for r in cells_out if not r['machine']],
        kb_dead_cells=dead_cells, kb_verdict_distribution=dist,
        real_anchor_check=dict(Pnet_MW_A3A4_dead=(bool(ra.get('Pnet_MW_A3_dead')) and bool(ra.get('Pnet_MW_A4_dead'))
                                                 if None not in (ra.get('Pnet_MW_A3_dead'), ra.get('Pnet_MW_A4_dead')) else None),
                               deep_dc_rms_A9_dead=ra.get('deep_dc_rms_A9_dead'), parts=ra,
                               note='deep_dc_rms 锚 = BH93 静止线 A1 部分（E56_VERDICT:A1_paired_correct）；exaggeration 不参与'),
        pipeline_issues=pipeline_issues,
        cells=cells_out,
        taxonomy=Y['taxonomy'])
    os.makedirs(outdir, exist_ok=True)
    C.dump(out, os.path.join(outdir, 'ABM_MR_CONSISTENCY.json'))

    lab = dict(sound_falsification='按构造零真值的 sound 证伪', heuristic_invariance='启发式不变性',
               equivariance='等变性', monotonicity='单调性', procedural_control='程序性控制（非 MR）')
    L = ['# MR_TAXONOMY — 审计电池九算子的蜕变关系四元组', '',
         '由 abm_mr_checker.py 从 mr_audit.yaml 生成（yaml sha256 %s）。分类是描述性组织，非本体断言；soundness 依赖物理构造，非形式证明。' % out['yaml_sha'], '',
         '| 算子 | 分类 | 源算例 | 变换 T | 期望关系 R | 容差 |', '|---|---|---|---|---|---|']
    for k in ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']:
        t = Y['taxonomy'][k]
        L.append('| %s | %s | %s | %s | %s | %s |' % (k, lab.get(t['class'], t['class']), t.get('source_case', '—'),
                                                     t.get('transform', '—'), t.get('relation', t.get('note', '—')), t.get('tolerance', '—')))
    L += ['', 'MT 不对称：违反即证伪、通过不认证——E58 uv 纬向 32/32 的 Wilson CI [0.8928, 1] 跨 0.9 判待定，是"能判死不能认证"的定量实例。',
          '', '九项 ≠ 九份独立证据：A1/A2/A9 同属 sound 证伪（同一物理构造），A3/A4/A7 同属启发式不变性，A5 不是 MR。']
    open(os.path.join(outdir, 'MR_TAXONOMY.md'), 'w').write('\n'.join(L) + '\n')
    print(json.dumps(dict(n_machine=n_machine, n_evaluated=n_ok, n_disagree=out['n_disagree'],
                          discrepancies=[(d['row'], d['col'], d['kb'], d['checker']) for d in disagree],
                          real_anchor_check=out['real_anchor_check'], pipeline_issues=pipeline_issues), ensure_ascii=False))


if __name__ == '__main__':
    main()
