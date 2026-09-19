#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""abm_derived.py — 封存后派生描述量（非预测、不改判）：只读本目录产出 JSON/npz 与 E57_AB/E66_AXES。
输出 final/ABM_DERIVED.json，供 RESULT/说明书挂 JSON 指针。"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import abm_common as C


def main():
    C.seal_gate(False)
    E = C.ENV_REAL
    fc = json.load(open(f'{HERE}/ABM_FILTER_CHAIN.json')); km = json.load(open(f'{HERE}/ABM_KILL_MATRIX.json'))
    ml = json.load(open(f'{HERE}/ABM_MUTANT_LEDGER.json'))
    M = np.load(f'{HERE}/ABM_FILTER_CHAIN_MASKS.npz'); L = M['H0.00']
    AB = np.load(f'{E}/e44/analysis/E57_AB.npz'); A, B = AB['A'], AB['B']
    G = np.load(f'{E}/e66/E66_AXES.npz')['G']
    lv = ['L0', 'L1', 'L2', 'L3', 'L4']
    chain = dict(
        n_B_eq_1_and_degenerate=int(((B == 1.0) & ~L[0]).sum()),
        L1_equals_L0_and_B_eq_1=bool(np.array_equal(L[1], L[0] & (B == 1.0))),
        by_level={lv[i]: dict(n=int(L[i].sum()), n_absolute=int((L[i] & (G == 1)).sum()), n_ratio=int((L[i] & (G == 0)).sum()),
                              median_A=float(np.median(A[L[i]])), n_A_ge_0p7=int((L[i] & (A >= 0.7)).sum()),
                              n_A_ge_0p9=int((L[i] & (A >= 0.9)).sum()), n_A_le_m0p7=int((L[i] & (A <= -0.7)).sum()),
                              frac_A_le_m0p7=float((L[i] & (A <= -0.7)).sum() / max(1, L[i].sum())))
                  for i in range(5)},
        all_candidates=dict(n=int(len(A)), median_A=float(np.median(A)), n_A_le_m0p7=int((A <= -0.7).sum())),
        note='派生非预测：L3 幸存者的 A 分布（A=−ρ(读数,技巧)，E57 约定）')
    ops = km['operators']
    kill_by_op = {o: 0 for o in ops}; sole_kill_by_op = {o: 0 for o in ops}
    for r in ml['roster']:
        if r.get('status') == 'KILLED':
            for o in r['kill_ops']:
                kill_by_op[o] += 1
            if len(r['kill_ops']) == 1:
                sole_kill_by_op[r['kill_ops'][0]] += 1
    base_dead_ops = {b: [o for o, v in bv.items() if v == '死'] for b, bv in km['base_verdicts'].items()}
    mut = dict(kill_by_operator=kill_by_op, sole_killer_by_operator=sole_kill_by_op, base_dead_operators=base_dead_ops,
               all_bases_dead_somewhere=all(len(v) > 0 for v in base_dead_ops.values()),
               abs_rate=km['overall']['abs_rate'], diff_rate=km['overall']['rate'],
               note='派生非预测：绝对口径 100% 来自基指标自身已在某算子判死（继承性检出），差分口径才度量对注入缺陷的敏感性')
    out = dict(entry='audit_battery_meta/derived', when=C.now(), preregistered=False, affects_verdict=False,
               code_sha=C.code_sha(__file__), prereg_sha=C.sha256(C.PREREG), chain=chain, mutants=mut)
    C.dump(out, f'{HERE}/ABM_DERIVED.json')
    print(json.dumps(out, ensure_ascii=False)[:3000])


if __name__ == '__main__':
    main()
