#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""abm_posthoc_ties.py — 封存后探索性敏感性分析（非预注册、不改判、不进 verdict）。

问题：变异电池主口径沿用 metric_search 的 argsort 秩（并列按下标序破）。clip_cheat 造大量并列，
其"被杀"是否依赖并列破法？做法：把 abm_common.spearman / exact_p 换成平均秩版本，原样重跑 abm_mutants.main()，
输出到 final/posthoc_avgrank/，再与主口径逐体对照 → final/ABM_POSTHOC_TIES.json。
"""
import itertools, json, os, sys
import numpy as np
from scipy.stats import rankdata
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import abm_common as C
import abm_mutants as M

_P = {}


def spearman_avg(a, b):
    ra = rankdata(a); rb = rankdata(b)
    if np.std(ra) == 0 or np.std(rb) == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def exact_p_avg(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); n = len(a)
    rho = spearman_avg(a, b)
    ra = rankdata(a); rb = rankdata(b)
    if n not in _P:
        _P[n] = np.array(list(itertools.permutations(range(n))))
    Rb = rb[_P[n]]
    ra_c = ra - ra.mean(); Rb_c = Rb - Rb.mean(axis=1, keepdims=True)
    den = np.sqrt((Rb_c ** 2).sum(axis=1) * (ra_c ** 2).sum())
    with np.errstate(invalid='ignore', divide='ignore'):
        rp = (Rb_c @ ra_c) / den
    rp = np.nan_to_num(rp)
    return rho, float(np.mean(np.abs(rp) >= abs(rho) - 1e-12))


def main():
    C.seal_gate(False)
    main_km = json.load(open(os.path.join(HERE, 'ABM_KILL_MATRIX.json')))
    main_ml = json.load(open(os.path.join(HERE, 'ABM_MUTANT_LEDGER.json')))
    sub = os.path.join(HERE, 'posthoc_avgrank'); os.makedirs(sub, exist_ok=True)
    C.spearman = spearman_avg; C.exact_p = exact_p_avg; C.FINAL = sub
    sys.argv = ['abm_mutants.py']
    M.main()
    alt_km = json.load(open(os.path.join(sub, 'ABM_KILL_MATRIX.json')))
    alt_ml = json.load(open(os.path.join(sub, 'ABM_MUTANT_LEDGER.json')))
    a = {x['id']: x for x in main_ml['roster']}; b = {x['id']: x for x in alt_ml['roster']}
    changed = []
    for k in a:
        if a[k].get('status') != b[k].get('status') or a[k].get('kill_ops') != b[k].get('kill_ops'):
            changed.append(dict(id=k, main=(a[k].get('status'), a[k].get('kill_ops')), avgrank=(b[k].get('status'), b[k].get('kill_ops'))))
    out = dict(entry='audit_battery_meta/posthoc_ties', when=C.now(), preregistered=False, affects_verdict=False,
               code_sha=C.code_sha(__file__), prereg_sha=C.sha256(C.PREREG),
               question='变异电池的差分杀死是否依赖 argsort 并列破法（主口径）',
               main=dict(classes={c: (v['killed'], v['escaped']) for c, v in main_km['classes'].items()}, rate=main_km['overall']['rate']),
               avgrank=dict(classes={c: (v['killed'], v['escaped']) for c, v in alt_km['classes'].items()}, rate=alt_km['overall']['rate'],
                            wilson95=alt_km['overall']['wilson95'], base_verdicts=alt_km['base_verdicts']),
               changed=changed, n_changed=len(changed))
    C.dump(out, os.path.join(HERE, 'ABM_POSTHOC_TIES.json'))
    print(json.dumps(dict(n_changed=len(changed), main_rate=out['main']['rate'], avg_rate=out['avgrank']['rate'],
                          avg_classes=out['avgrank']['classes'], changed=changed), ensure_ascii=False))


if __name__ == '__main__':
    main()
