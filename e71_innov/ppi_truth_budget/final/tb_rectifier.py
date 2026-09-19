#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""ppi_truth_budget (b) rectifier 测谎。封存门内运行；输出 TB_RECTIFIER.json。
Y_bench 口径（冻结）：基准问题固定 —— 提交态（该 run out_his.nc 最后一帧）对
r26steep 第 1.0 天 MITgcm 真值（AKV 按 action，缺省 1e-5）的 err_rms（cm/s），
即 regrade_all.grade_run(rid, ntimes=8640, akv)；对 U 内成员 = regraded_v2 err_rms。
校正函数（计分口径，封存前按检查意见改定）：ĥ_cal = U∖B_V（诚实标定集，预期 n=55）上 Y 对 f_D 的 OLS；
三条路径的 R_p 一律为「拟合集外残差」中位。ĥ58（含 B_V 的全 U 拟合）只作描述性对照印出。"""
import json, time
import numpy as np
import tb_common as C

def grade_bench(rid, akv):
    from regrade_all import grade_run
    g = grade_run(rid, 8640, akv)          # day 恒 1.0；短算例读到的是其最后一帧
    return None if g is None else float(g['err_rms'])

def main():
    seal = C.require_seal()
    t0 = time.time()
    from metric_search import base_quantities
    ids, Y, Q, keys, SK, rows, reg = C.build_population()
    N = len(ids)
    res = {'prereg_seal': seal.splitlines()[0], 'n_pop': N, 'spur_key': SK, 'seed': C.SEED_B}
    fD = C.proxy_D(Q, SK)
    a58, b58 = C.ols_ab(fD, Y)             # ĥ58：全 U 真值标定（含 B_V，只作描述性对照）
    res['h58'] = {'a': a58, 'b': b58, 'role': 'descriptive_only (B_V 为样本内)'}
    honest = np.array([not C.is_BV(rows[r]) for r in ids], bool)
    ac, bc = C.ols_ab(fD[honest], Y[honest])   # ĥ_cal：U∖B_V 上拟合（计分口径）
    res['h_cal'] = {'a': ac, 'b': bc, 'n_fit': int(honest.sum()),
                    'excluded_B_V_in_U': [r for r, h in zip(ids, honest) if not h],
                    'role': 'scoring (三路径均为拟合集外残差)'}

    # ---- V3 复算门：字典序前 5 个 U 成员，grade_bench 复现 regraded err_rms ----
    v3 = []
    for rid in ids[:5]:
        akv = rows[rid]['action'].get('AKV_BAK', 1e-5)
        gb = grade_bench(rid, akv)
        v3.append({'run_id': rid, 'regraded': float(reg[rid]['err_rms']),
                   'recomputed': gb, 'abs_diff': None if gb is None else abs(gb - reg[rid]['err_rms'])})
    v3_pass = all(d['recomputed'] is not None and d['abs_diff'] <= C.GRADE_TOL for d in v3)
    res['v3_spotcheck'] = {'rows': v3, 'pass': bool(v3_pass), 'tol': C.GRADE_TOL}

    # ---- 三条刷分路径总体（冻结定义见 PREREG §3-8） ----
    ledger = rows
    simple = C.is_simple
    # B_T：e65 孪生对的平底臂
    pairs = C.twin_pairs(ledger)
    B_T = sorted({b for _, b in pairs})
    # B_V：steep ∧ valid ∧ 8640 ∧ 简单动作 ∧ VISC2 > 3000（已知全在 U 内，V7）
    B_V = sorted(rid for rid, r in ledger.items() if C.is_BV(r))
    # B_S：steep ∧ valid ∧ ntimes<8640 ∧ 简单动作 ∧ VISC2 ≤ 2747
    B_S = sorted(rid for rid, r in ledger.items() if C.is_BS(r))
    res['path_sets_ledger'] = {'B_T': len(B_T), 'B_V': len(B_V), 'B_S': len(B_S),
                               'B_V_in_U': sum(r in set(ids) for r in B_V),
                               'n_pairs': len(pairs)}

    def collect(rids):
        out = []
        for rid in rids:
            q = base_quantities(f'{C.ENV}/runs/{rid}')
            if not q or SK not in q: continue
            akv = ledger[rid]['action'].get('AKV_BAK', 1e-5)
            yb = grade_bench(rid, akv)
            if yb is None: continue
            out.append((rid, float(q[SK]), yb))
        return out

    paths = {}
    setmap = {'terrain': collect(B_T), 'visc': collect(B_V), 'short': collect(B_S)}
    # 倍数复算（V6，非计分；口径 = SPUR_KEY 配对读数比，注明与初赛 fig_llm 口径不同）
    fD_by_id = dict(zip(ids, fD))
    m_terrain = [fD_by_id[s]/dict((r,v) for r,v,_ in setmap['terrain'])[f]
                 for s, f in pairs if s in fD_by_id and f in dict((r,v) for r,v,_ in setmap['terrain'])]
    ref = [fD_by_id[rid] for rid in ids
           if simple(ledger[rid]) and round(ledger[rid]['action'].get('VISC2',0.0),6)==50.0]
    m_visc = ([float(np.median(ref))/v for _, v, _ in setmap['visc']] if ref else [])
    # short 配对：同 (VISC2 round6, seed) 的 8640 对应臂在 U 内
    full_ix = {}
    for rid in ids:
        r = ledger[rid]
        if simple(r):
            full_ix[(round(r['action'].get('VISC2',0.0),6), r['action'].get('seed'))] = fD_by_id[rid]
    m_short, m_short_fb = [], []
    for rid, v, _ in setmap['short']:
        r = ledger[rid]
        k = (round(r['action'].get('VISC2',0.0),6), r['action'].get('seed'))
        if k in full_ix: m_short.append(full_ix[k]/v)
        elif ref:        m_short_fb.append(float(np.median(ref))/v)
    mult = {'terrain': _med(m_terrain), 'visc': _med(m_visc),
            'short': _med(m_short) if len(m_short) >= C.MIN_BRUSHED else _med(m_short_fb),
            'short_pairing': 'matched' if len(m_short) >= C.MIN_BRUSHED else 'fallback_ref',
            'n_terrain': len(m_terrain), 'n_visc': len(m_visc),
            'n_short_matched': len(m_short), 'n_short_fallback': len(m_short_fb),
            'primary_note': '初赛口径 224/62/28 见 github_repo/scripts/fig_llm.py L59-62（换地形32对中位/VISC2 50→30000/缩短积分5对中位），与本口径(SPUR_KEY 配对比中位)不同，只可并列不可互替'}
    res['multipliers'] = mult
    # V6b（验证性断言，不计分）：初赛 62× = fig_llm.py 注释 8.674/0.1399 的算术复算；
    # 并在 VISC2=50 参考臂与 VISC2=30000 臂的 obs 字段与 base_quantities 键中搜索这对数值（相对差<5e-4）
    na, nb = C.INIT_VISC_ARITH
    hit = {'arith_ratio': na/nb, 'rounds_to_62': bool(round(na/nb) == 62), 'matches': []}
    r30k = [rid for rid in B_V if round(ledger[rid]['action'].get('VISC2',0.0),6) == 30000.0]
    r50  = [rid for rid in ids if simple(ledger[rid]) and round(ledger[rid]['action'].get('VISC2',0.0),6) == 50.0]
    def _scan(rid):
        out = {('obs', k): v for k, v in ledger[rid]['obs'].items() if isinstance(v, (int, float))}
        q = base_quantities(f'{C.ENV}/runs/{rid}') or {}
        out.update({('bq', k): v for k, v in q.items()})
        return out
    for ra in r50:
        sa = _scan(ra)
        for rb in r30k:
            sb = _scan(rb)
            for key in sa:
                if key in sb and sa[key] and sb[key] and abs(sa[key]-na) <= 5e-4*na and abs(sb[key]-nb) <= 5e-4*nb:
                    hit['matches'].append({'ref50': ra, 'visc30000': rb, 'src': key[0], 'key': key[1],
                                           'ref_value': float(sa[key]), 'brushed_value': float(sb[key])})
    hit['n_ref50'] = len(r50); hit['n_visc30000'] = len(r30k)
    res['V6b_init62_recompute'] = hit

    for pname, rowsp in setmap.items():
        if len(rowsp) < C.MIN_BRUSHED:
            paths[pname] = {'n': len(rowsp), 'status': 'AMBIGUOUS_SMALL'}
            continue
        yb = np.array([y for _,_,y in rowsp]); fv = np.array([v for _,v,_ in rowsp])
        resid = yb - (ac + bc*fv)              # 计分：ĥ_cal 拟合集外残差
        resid58 = yb - (a58 + b58*fv)          # 描述：ĥ58（visc 路径为样本内）
        paths[pname] = {'n': len(rowsp),
                        'rectifier_median': float(np.median(resid)),
                        'rectifier_iqr': [float(np.percentile(resid,25)), float(np.percentile(resid,75))],
                        'descr_rectifier_median_h58': float(np.median(resid58)),
                        'ybench_mean': float(yb.mean()), 'reading_mean': float(fv.mean()),
                        'run_ids': [r for r,_,_ in rowsp], 'status': 'OK'}
    res['paths'] = paths

    # ---- PB7 混合总体覆盖对照 ----
    mix = {rid: (fD_by_id[rid], float(Y[ids.index(rid)])) for rid in ids}
    for rowsp in setmap.values():
        for rid, v, y in rowsp: mix.setdefault(rid, (v, y))
    mids = sorted(mix)
    fM = np.array([mix[r][0] for r in mids]); yM = np.array([mix[r][1] for r in mids])
    NM = len(mids); thM = float(yM.mean())
    new_by_path = {p: sum(1 for rid,_,_ in rowsp if rid not in set(ids)) for p, rowsp in setmap.items()}
    rng = np.random.default_rng(C.SEED_B)
    from scipy import stats as st
    covN = covP = 0; n = C.PB3_N
    for _ in range(C.DRAWS):
        idx = rng.choice(NM, n, replace=False)
        lab = np.zeros(NM, bool); lab[idx] = True
        # 朴素替代（Baumann 式）：无标注处填 ĥ_cal(f)（U∖B_V 诚实标定），把 N 个数当真数据
        pooled = np.where(lab, yM, ac + bc*fM)
        thn = float(pooled.mean())
        sen = np.sqrt(pooled.var(ddof=1)/NM)
        tq = st.t.ppf(0.95, NM-1)
        covN += (thn - tq*sen <= thM <= thn + tq*sen)
        # PPI（同 (a) 机器）
        th, lo, hi, v, lam = C.ppi_mean_ci(yM[idx], fM[idx], fM, NM)
        covP += (lo <= thM <= hi)
    res['mixture'] = {'n_mix': NM, 'theta_mix': thM, 'n_label': n, 'n_new_members_by_path': new_by_path,
                      'naive_filler': 'h_cal (U∖B_V OLS)',
                      'cov_naive': covN/C.DRAWS, 'cov_ppi': covP/C.DRAWS}
    res['elapsed_s'] = round(time.time()-t0, 1)
    res['status'] = 'OK' if v3_pass else 'V3_FAIL'
    json.dump(res, open(f'{C.FINAL}/TB_RECTIFIER.json','w'), indent=1, ensure_ascii=False)
    print('TB_RECTIFIER.json written; status =', res['status'])

def _med(v):
    return float(np.median(v)) if len(v) else None

if __name__ == '__main__':
    main()
