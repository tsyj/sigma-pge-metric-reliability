#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""ppi_truth_budget 机械判分：只读 TB_BUDGET.json / TB_RECTIFIER.json，不重算任何统计。
输出 verdict.json，三值 TRUE/FALSE/AMBIGUOUS；阈值 = tb_common 冻结常量（PREREG §5 同表）。"""
import json
import tb_common as C

def main():
    seal = C.require_seal()
    B = json.load(open(f'{C.FINAL}/TB_BUDGET.json'))
    R = json.load(open(f'{C.FINAL}/TB_RECTIFIER.json'))
    V = {}

    bud_ok = B.get('status') == 'OK'
    tab = B.get('budget_table', {})
    def cells(proxies, ns):
        out = []
        for p in proxies:
            for n in ns:
                out.append(tab.get(f'{p}_{n}', {}))
        return out

    # P1 均值覆盖
    cs = cells(C.PROXIES, C.NGRID)
    if not bud_ok or any('status' in c for c in cs):
        V['P1'] = 'AMBIGUOUS'
    else:
        V['P1'] = 'TRUE' if min(c['cov_mean'] for c in cs) >= C.COV_MEAN_MIN else 'FALSE'
    # P2 D 代理省真值
    c = tab.get(f'D_{C.NEFF_N}', {})
    V['P2'] = ('AMBIGUOUS' if not bud_ok or 'saving' not in c
               else ('TRUE' if c['saving'] >= C.NEFF_D_MIN else 'FALSE'))
    # 原 P3（D ≥ u_max）封存前降级为验证性断言 V8：秩序层面可由在盘 Atr 查表派生，不计分（见 VER['V8']）
    cu = tab.get(f'umax_{C.NEFF_N}', {})
    # P4 分位点估计效率（n=16，D 代理）：MAE(PPI) ≤ MAE(经典)；经典 MAE 非正 → AMBIGUOUS（§3-9 已列）
    c4 = tab.get(f'D_{C.P90_N}', {})
    if not bud_ok or 'p90_mae_ppi' not in c4 or c4.get('p90_mae_classical', 0) <= 0:
        V['P4'] = 'AMBIGUOUS'
    else:
        V['P4'] = ('TRUE' if c4['p90_mae_ppi'] <= C.P90_MAE_RATIO_MAX * c4['p90_mae_classical']
                   else 'FALSE')

    rec_ok = R.get('status') == 'OK'
    P = R.get('paths', {})
    ok_paths = all(P.get(p, {}).get('status') == 'OK' for p in ('terrain','visc','short'))
    # P5 三路径 rectifier > 0
    if not rec_ok or not ok_paths:
        V['P5'] = 'AMBIGUOUS'
    else:
        V['P5'] = 'TRUE' if all(P[p]['rectifier_median'] > 0 for p in ('terrain','visc','short')) else 'FALSE'
    # P6 rectifier 排序 = 复算倍数排序
    M = R.get('multipliers', {})
    ms = [M.get(p) for p in ('terrain','visc','short')]
    if not rec_ok or not ok_paths or any(m is None for m in ms):
        V['P6'] = 'AMBIGUOUS'
    else:
        rs = [P[p]['rectifier_median'] for p in ('terrain','visc','short')]
        # 并列按 (terrain,visc,short) 固定下标序定秩（sorted 稳定；§3-9 已列）
        rank = lambda v: sorted(range(3), key=lambda i: v[i])
        V['P6'] = 'TRUE' if rank(rs) == rank(ms) else 'FALSE'
    # P7 混合总体：朴素被骗 ∧ PPI 仍覆盖
    mx = R.get('mixture', {})
    if not rec_ok or 'cov_naive' not in mx:
        V['P7'] = 'AMBIGUOUS'
    else:
        V['P7'] = ('TRUE' if (mx['cov_naive'] <= C.NAIVE_COV_MAX and mx['cov_ppi'] >= C.PPI_MIX_COV_MIN)
                   else 'FALSE')

    # ---------------- 验证性断言（不计分，只印出核对） ----------------
    import os
    VER = {}
    VER['V1_n_pop'] = {'expect': 58, 'got': B.get('n_pop'), 'ok': B.get('n_pop') == 58}
    VER['V2_spur_key'] = {'expect': 'u|all|rms', 'got': B.get('spur_key'), 'ok': B.get('spur_key') == 'u|all|rms'}
    VER['V3_grade_spotcheck'] = {'pass': R.get('v3_spotcheck', {}).get('pass')}
    ed = B.get('e59_diag') or {}
    VER['V4_e59_rows'] = {'expect': 15376, 'got': ed.get('n_rebuilt'), 'ok': ed.get('n_rebuilt') == 15376}
    try:
        st = json.load(open(f'{C.FINAL}/TB_SELFTEST.json'))
        VER['V5_selftest'] = {'ok': bool(st.get('all_pass'))}
    except Exception as e:
        VER['V5_selftest'] = {'ok': False, 'error': repr(e)}
    VER['V6_multipliers'] = {'this_protocol': {k: M.get(k) for k in ('terrain','visc','short')},
                             'short_pairing': M.get('short_pairing'),
                             'initial_round_fig_llm': C.INIT_MULT,
                             'note': '两口径不同，只并列不互替，不设容差门'}
    VER['V6b_init62'] = R.get('V6b_init62_recompute')
    ps = R.get('path_sets_ledger', {})
    got7 = {'n_pop': B.get('n_pop'), 'B_T': ps.get('B_T'), 'B_V': ps.get('B_V'), 'B_S_ledger': ps.get('B_S'),
            'B_S_with_his': P.get('short', {}).get('n'), 'B_S_matched': M.get('n_short_matched'),
            'B_V_in_U': ps.get('B_V_in_U')}
    VER['V7_path_sets'] = {'expect': C.EXPECT_SETS, 'got': got7,
                           'ok': all(got7.get(k) == v for k, v in C.EXPECT_SETS.items()),
                           'n_terrain_collected': P.get('terrain', {}).get('n'),
                           'n_visc_collected': P.get('visc', {}).get('n')}
    v8 = B.get('V8_lookup', {})
    VER['V8_old_P3'] = {'statement': 'saving(D,16) >= saving(umax,16)',
                        'value': (None if not bud_ok or 'saving' not in c or 'saving' not in cu
                                  else bool(c['saving'] >= cu['saving'])),
                        'saving_D_16': c.get('saving'), 'saving_umax_16': cu.get('saving'),
                        'Atr_lookup': {k: v8.get(k) for k in ('Atr[u|all|rms]', 'Atr[u|all|max]',
                                                              'rebuilt_A_matches_Atr', 'n_rebuilt_zonal', 'n_Atr')},
                        'descr': {k: v8.get(k) for k in v8 if k.startswith('descr_')},
                        'counted': False}

    COUNTED = ('P1', 'P2', 'P4', 'P5', 'P6', 'P7')
    out = {'prereg_seal': seal.splitlines()[0], 'verdicts': V,
           'counted_predictions': list(COUNTED),
           'n_true': sum(V[k]=='TRUE' for k in COUNTED),
           'n_false': sum(V[k]=='FALSE' for k in COUNTED),
           'n_ambiguous': sum(V[k]=='AMBIGUOUS' for k in COUNTED),
           'verification_assertions_not_counted': VER,
           'thresholds': {'COV_MEAN_MIN': C.COV_MEAN_MIN,
                          'P90_MAE_RATIO_MAX': C.P90_MAE_RATIO_MAX, 'P90_N': C.P90_N,
                          'NEFF_D_MIN': C.NEFF_D_MIN, 'NEFF_N': C.NEFF_N,
                          'NAIVE_COV_MAX': C.NAIVE_COV_MAX, 'PPI_MIX_COV_MIN': C.PPI_MIX_COV_MIN,
                          'MIN_POP': C.MIN_POP, 'MIN_BRUSHED': C.MIN_BRUSHED}}
    json.dump(out, open(f'{C.FINAL}/verdict.json','w'), indent=1, ensure_ascii=False)
    print(json.dumps(out['verdicts'], ensure_ascii=False))

if __name__ == '__main__':
    main()
