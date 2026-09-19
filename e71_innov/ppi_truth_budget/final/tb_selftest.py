#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""ppi_truth_budget 合成数据自检（唯一允许在封存前运行的部件）。
不读任何账本/真值/留出文件；只验证估计量代码本身。
合成总体：N=58，Y=|N(3,1)|+0.2，corr≈0.92 线性代理；n=16；2000 次重复。
通过线（代码正确性门，不是对真实数据的赌注）：
  均值刀切覆盖 ∈ [0.88,0.94]；精确 p90 区间覆盖 ≥ 0.90；
  PPI p90 点估计 MAE/经典 ≤ 1.05；λ̂ 中位 ∈ [0.7,1.3]×总体斜率。
输出 TB_SELFTEST.json。估计量形式由封存前合成校准选定（calib*.py，见 CALIB_SYNTH.md）。"""
import json
import numpy as np
import tb_common as C

def main():
    rng = np.random.default_rng(7)
    N, n, REP = 58, 16, 2000
    Y = np.abs(rng.normal(3, 1, N)) + 0.2
    f = 2.0*Y + rng.normal(0, 2.0*np.std(Y)*0.45, N)     # corr ~0.92
    thM, thP = float(Y.mean()), C.pop_p90(Y)
    covM = covPx = 0; lams = []; maeP = []; maeC = []
    for _ in range(REP):
        idx = rng.choice(N, n, replace=False)
        th, lo, hi, v, lam = C.ppi_mean_ci(Y[idx], f[idx], f, N)
        covM += (lo <= thM <= hi); lams.append(lam)
        xlo, xhi, _ = C.exact_p90_ci(Y[idx], N)
        covPx += (xlo <= thP <= xhi)
        maeP.append(abs(C.ppi_p90_point(Y[idx], f[idx], f) - thP))
        maeC.append(abs(C.classical_p90_point(Y[idx]) - thP))
    covM /= REP; covPx /= REP
    ratio = float(np.median(maeP)/max(np.median(maeC), 1e-12))
    lam_med = float(np.median(lams)); true_b = float(np.cov(f,Y,ddof=1)[0,1]/np.var(f,ddof=1))
    res = {'N': N, 'n': n, 'rep': REP, 'corr_fY': float(np.corrcoef(f,Y)[0,1]),
           'cov_mean_jackknife': covM, 'cov_p90_exact': covPx, 'p90_mae_ratio': ratio,
           'lam_med': lam_med, 'ols_slope_pop': true_b,
           'pass_mean': bool(0.88 <= covM <= 0.94),
           'pass_p90_exact': bool(covPx >= 0.90),
           'pass_mae': bool(ratio <= 1.05),
           'pass_lam': bool(0.7*true_b <= lam_med <= 1.3*true_b)}
    res['all_pass'] = bool(res['pass_mean'] and res['pass_p90_exact']
                           and res['pass_mae'] and res['pass_lam'])
    json.dump(res, open(f'{C.FINAL}/TB_SELFTEST.json','w'), indent=1, ensure_ascii=False)
    print(json.dumps(res, ensure_ascii=False))

if __name__ == '__main__':
    main()
