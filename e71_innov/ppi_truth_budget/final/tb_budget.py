#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""ppi_truth_budget (a) 真值预算表。封存门内运行；输出 TB_BUDGET.json。
冻结循环序：for proxy in (D,umax,e59): for n in NGRID: for b in range(DRAWS)。"""
import json, time
import numpy as np
import tb_common as C

def main():
    seal = C.require_seal()
    t0 = time.time()
    ids, Y, Q, keys, SK, rows, reg = C.build_population()
    N = len(ids)
    res = {'prereg_seal': seal.splitlines()[0], 'n_pop': N, 'spur_key': SK,
           'seed': C.SEED_A, 'draws': C.DRAWS, 'ngrid': list(C.NGRID), 'alpha': C.ALPHA}
    if N < C.MIN_POP:
        res['status'] = 'AMBIGUOUS_POP'; _dump(res); return
    th_mean = float(np.mean(Y)); th_p90 = C.pop_p90(Y)
    S2Y = float(np.var(Y, ddof=1))
    res.update(theta_mean=th_mean, theta_p90=th_p90, S2Y=S2Y)

    fD = C.proxy_D(Q, SK)
    fU = C.proxy_umax(ids, rows)
    fE, diagE = C.proxy_e59(Q, keys)
    res['e59_diag'] = diagE
    prox = {'D': fD, 'umax': fU, 'e59': fE}
    # 描述性：代理与真值的总体相关（判分不用，只报告）
    res['descr_corr'] = {p: (None if f is None else float(np.corrcoef(f, Y)[0,1])) for p,f in prox.items()}
    res['descr_corr_obs_urms_fD'] = float(np.corrcoef(
        fD, np.array([rows[r]['obs'].get('u_rms', np.nan) for r in ids], float))[0,1]) \
        if all(rows[r]['obs'].get('u_rms') is not None for r in ids) else None
    # 近邻同框（描述性，不判分）：PPSR（arXiv:2608.26638）的节省比 ≈ 总体 Pearson r²（U≫L 极限、无 FPC）；
    # 对应的无 FPC 渐近倍数 1/(1−r²)，与本表有限总体 n_eff/n 并列印出。
    res['descr_ppsr_like'] = {p: (None if f is None else
        {'pearson_r2': float(np.corrcoef(f, Y)[0,1]**2),
         'asymptotic_saving_noFPC': float(1.0/max(1e-12, 1.0-np.corrcoef(f, Y)[0,1]**2))})
        for p, f in prox.items()}
    # 总体构成申报（§3-8/§8-11）：U 含荒谬黏性路径成员
    bv_in_U = [r for r in ids if C.is_BV(rows[r])]
    res['B_V_members_in_U'] = [{'run_id': r, 'VISC2': rows[r]['action'].get('VISC2')} for r in bv_in_U]
    # V8（原 P3 降级，验证性断言，不计分）：E59_ARRAYS.npz Atr 查表 = 两候选对本总体的 −spearman(读数, skill)
    v8 = {'note': '在盘已知量查表（Atr=纬向 A 标签）；P3 秩序层面由此可派生，故降级为验证性断言'}
    try:
        from metric_search import spearman
        namesZ, AZ = C.rebuild_e59_names_zonal()
        Atr = np.load(f'{C.ENV}/e59/E59_ARRAYS.npz')['Atr']
        v8['n_rebuilt_zonal'] = len(namesZ); v8['n_Atr'] = int(len(Atr))
        v8['rebuilt_A_matches_Atr'] = bool(len(AZ) == len(Atr) and np.allclose(AZ, Atr, atol=1e-12, equal_nan=True))
        for nm in ('u|all|rms', 'u|all|max'):
            if (nm, '') in namesZ and len(namesZ) == len(Atr):
                i = namesZ.index((nm, ''))
                v8[f'Atr[{nm}]'] = {'index': i, 'value': float(Atr[i])}
            else:
                v8[f'Atr[{nm}]'] = None
        skill = np.array([reg[r]['skill_vs_zero'] for r in ids], float)
        v8['descr_minus_spearman_fD_skill'] = float(-spearman(fD, skill))
        v8['descr_minus_spearman_obs_umax_skill'] = float(-spearman(fU, skill))
        v8['descr_spearman_fD_Y'] = float(spearman(fD, Y))
        v8['descr_spearman_obs_umax_Y'] = float(spearman(fU, Y))
    except Exception as e:
        v8['error'] = repr(e)
    res['V8_lookup'] = v8

    rng = np.random.default_rng(C.SEED_A)
    table = {}
    for pname in C.PROXIES:
        f = prox[pname]
        for n in C.NGRID:
            cell = {'proxy': pname, 'n': n}
            if f is None:
                cell['status'] = 'AMBIGUOUS_E59'
                # 消耗同样多的随机数保持后续 cell 可重复
                for _ in range(C.DRAWS): rng.choice(N, n, replace=False)
                table[f'{pname}_{n}'] = cell; continue
            covM=covMc=covPx=0; wM=[]; wMc=[]; wPx=[]; vs=[]; lams=[]
            unb=0; maeP=[]; maeC=[]
            for _ in range(C.DRAWS):
                idx = rng.choice(N, n, replace=False)
                yl, fl = Y[idx], f[idx]
                th, lo, hi, v, lam = C.ppi_mean_ci(yl, fl, f, N)
                covM += (lo <= th_mean <= hi); wM.append(hi-lo); vs.append(v); lams.append(lam)
                tc, lc, hc, vc = C.classical_mean_ci(yl, N)
                covMc += (lc <= th_mean <= hc); wMc.append(hc-lc)
                # p90 区间 = 精确次序统计量（保证式）；PPI 只出点估计（MAE 对照）
                xlo, xhi, xunb = C.exact_p90_ci(yl, N)
                covPx += (xlo <= th_p90 <= xhi); unb += xunb
                if np.isfinite(xhi-xlo): wPx.append(xhi-xlo)
                maeP.append(abs(C.ppi_p90_point(yl, fl, f) - th_p90))
                maeC.append(abs(C.classical_p90_point(yl) - th_p90))
            v_med = float(np.median(vs))
            ne = C.n_eff(v_med, S2Y, N)
            cell.update(
                cov_mean=covM/C.DRAWS, cov_mean_classical=covMc/C.DRAWS,
                cov_p90_exact=covPx/C.DRAWS, p90_exact_unbounded_frac=unb/C.DRAWS,
                width_mean_med=float(np.median(wM)), width_mean_classical_med=float(np.median(wMc)),
                width_p90_exact_med=(float(np.median(wPx)) if wPx else None),
                p90_mae_ppi=float(np.median(maeP)), p90_mae_classical=float(np.median(maeC)),
                v_med=v_med, lam_med=float(np.median(lams)),
                n_eff=ne, saving=ne/n)
            table[f'{pname}_{n}'] = cell
    res['budget_table'] = table
    res['dorner_reference_line'] = 2.0   # arXiv:2410.13341，假设域差异见预注册 §8
    res['elapsed_s'] = round(time.time()-t0, 1)
    res['status'] = 'OK'
    _dump(res)

def _dump(res):
    json.dump(res, open(f'{C.FINAL}/TB_BUDGET.json','w'), indent=1, ensure_ascii=False)
    print('TB_BUDGET.json written; status =', res.get('status'))

if __name__ == '__main__':
    main()
