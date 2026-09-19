#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""abm_goodhart_map.py — 模块③ Goodhart 覆盖矩阵（PREREG §2.6，描述性，无预测）。

读 mr_audit.yaml goodhart 节 ＋ KILLBOARD.json → 核对 13 死格、解析证据指针 → 死格分科表 ＋ A1–A9×6 类型两档覆盖矩阵。
产出：ABM_GOODHART_MAP.json。用法同 abm_mr_checker.py（--selftest <夹具根> <输出目录>）。
"""
import json, os, sys
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import abm_common as C

OPS = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']


def main():
    selftest = len(sys.argv) > 1 and sys.argv[1] == '--selftest'
    if selftest:
        env, outdir = sys.argv[2], sys.argv[3]
        yml = os.path.join(env, 'mr_audit.yaml')
    else:
        C.seal_gate(False)
        env, outdir = C.ENV_REAL, C.FINAL
        yml = os.path.join(C.FINAL, 'mr_audit.yaml')
    Y = yaml.safe_load(open(yml)); G = Y['goodhart']
    kbp = os.path.join(env, Y['killboard']); KB = json.load(open(kbp))
    cols = [c.split()[0] for c in KB['cols']]
    kb_dead = {(r, cols[j]) for i, r in enumerate(KB['rows']) for j in range(len(cols))
               if KB['grid'][i][j]['verdict'] == C.DEAD and r != 'truth' and cols[j] != 'R'}
    declared = {(d['row'], d['col']) for d in G['dead_cells']}
    types = list(G['types'].keys())

    cells = []; manual = []
    for d in G['dead_cells']:
        ev = []
        for p in d['evidence']:
            ok, v = C.resolve(p, env)
            ev.append(dict(ptr=p, resolved=ok, value=v if not isinstance(v, (dict, list)) else '<%s>' % type(v).__name__))
        status = 'evidenced' if ev and all(e['resolved'] for e in ev) else 'manual'
        if status == 'manual':
            manual.append([d['row'], d['col']])
        cells.append(dict(row=d['row'], col=d['col'], type=d['type'], family=G['types'][d['type']]['family'],
                          subtype=d.get('subtype'), why=d['why'], evidence=ev, status=status,
                          in_killboard_dead=((d['row'], d['col']) in kb_dead)))

    matrix = {op: {t: '不覆盖' for t in types} for op in OPS}
    support = {op: {t: [] for t in types} for op in OPS}
    for c in cells:
        if c['status'] == 'evidenced' and c['in_killboard_dead']:
            matrix[c['col']][c['type']] = '有实证检出'
            support[c['col']][c['type']].append(c['row'])
    col_empty = [t for t in types if all(matrix[op][t] == '不覆盖' for op in OPS)]
    row_empty = [op for op in OPS if all(matrix[op][t] == '不覆盖' for t in types)]
    specimens = {}
    for t, s in G['types'].items():
        ok, v = C.resolve(s['specimen_ptr'], env)
        specimens[t] = dict(label=s['label'], family=s['family'], specimen=s['specimen'], ptr=s['specimen_ptr'],
                            resolved=ok, value=v if not isinstance(v, (dict, list)) else '<%s>' % type(v).__name__)
    fam_count = {}
    for c in cells:
        fam_count[c['family']] = fam_count.get(c['family'], 0) + 1
    type_count = {t: sum(1 for c in cells if c['type'] == t) for t in types}

    out = dict(entry='audit_battery_meta/module3', when=C.now(), selftest=selftest,
               code_sha=C.code_sha(__file__), yaml_sha=C.sha256(yml), killboard_sha=C.sha256(kbp),
               prereg_sha=None if selftest else C.sha256(C.PREREG),
               n_dead_killboard=len(kb_dead), n_dead_declared=len(declared),
               dead_set_match=(kb_dead == declared),
               missing_in_yaml=sorted([list(x) for x in kb_dead - declared]),
               extra_in_yaml=sorted([list(x) for x in declared - kb_dead]),
               family_count=fam_count, type_count=type_count,
               cells=cells, manual_cells=manual,
               coverage_matrix=matrix, coverage_support_rows=support,
               empty_type_columns=col_empty, operators_with_no_evidenced_death=row_empty,
               specimens=specimens,
               grades='只两档：有实证检出 / 不覆盖（"构造上可检"档已砍）',
               known_structure_statement='回归·跟踪 D 九项都不覆盖（E66 A⊥ 补过、E67b 治法场景依赖）；按已知结构陈述，不下注')
    os.makedirs(outdir, exist_ok=True)
    C.dump(out, os.path.join(outdir, 'ABM_GOODHART_MAP.json'))
    print(json.dumps(dict(dead_set_match=out['dead_set_match'], family_count=fam_count, type_count=type_count,
                          empty_type_columns=col_empty, operators_with_no_evidenced_death=row_empty,
                          manual_cells=manual), ensure_ascii=False))


if __name__ == '__main__':
    main()
