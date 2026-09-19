#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""abm_selftest.py — 合成夹具自测（不读任何真实 run / npz / 源 JSON 数值）。

用法：abm_selftest.py <夹具根目录（须不存在或为空）>
构造：假 ledger、假 out_his.nc（真实维度、随机场）、假 KILLBOARD 与源 JSON（数值全为合成）、假 E57/E66 数组（由第一遍自算回填）。
断言：统计函数、E57 复现锚、滤链单调、名册与 PREREG 表一致、等价/重复体识别、V5、checker 规则逐格、verdict 故障注入。
"""
import json, os, re, shutil, subprocess, sys, itertools
import numpy as np
import yaml
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import abm_common as C

PY = sys.executable
FAILS = []


def check(cond, msg):
    print(('  ok  ' if cond else '  FAIL ') + msg, flush=True)
    if not cond:
        FAILS.append(msg)


def run(args):
    env = dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    r = subprocess.run([PY] + args, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(r.stdout[-3000:]); print(r.stderr[-3000:])
    return r


# ---------------- 1. 统计函数 ----------------
def unit_tests():
    print('[1] 统计函数')
    rng = np.random.default_rng(0)
    for _ in range(5):
        a = rng.normal(size=7); b = rng.normal(size=7)
        rho, p = C.exact_p(a, b)
        ra = np.argsort(np.argsort(a))
        cnt = 0
        for perm in itertools.permutations(range(7)):
            r2 = np.corrcoef(ra, np.array(perm))[0, 1]
            cnt += abs(r2) >= abs(rho) - 1e-12
        check(abs(p - cnt / 5040) < 1e-12 and abs(rho - C.spearman(a, b)) < 1e-12, 'exact_p 与暴力置换一致 (p=%.4f)' % p)
    lo, hi = C.wilson(32, 32)
    check(abs(lo - 0.8928) < 1e-3 and hi == 1.0, 'Wilson(32,32) 下界 0.8928 (%.4f)' % lo)
    check(C.v_A1_trivalent(32, 32) == C.UND, '32/32 三值化 = 待定')
    check(C.v_A1_trivalent(0, 1) == C.DEAD and C.v_A1_trivalent(0, 7) == C.DEAD, '0/1、0/7 三值化 = 死')
    check(C.v_A6(-0.99, 0.0) == C.EDGE and C.v_A6(0.17, 0.95) == C.DEAD and C.v_A6(-0.8, 0.95) == C.PASS, 'v_A6 规则')
    check(C.v_A8(0.857, 0.0238) == C.PASS and C.v_A8(-0.964, 0.003) == C.DEAD and C.v_A8(0.7, 0.1) == C.EDGE, 'v_A8 规则')
    check(C.worst([C.PASS, C.DEAD, C.EDGE]) == C.DEAD and C.worst([C.NA]) == C.NA, 'worst')


# ---------------- 2. 夹具 ----------------
def write_nc(path, h, amp, seed, zero_flow=False):
    import netCDF4 as nc
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rng = np.random.default_rng(seed)
    d = nc.Dataset(path, 'w')
    for nm, n in (('ocean_time', 4), ('s_rho', 13), ('s_w', 14), ('eta_rho', 48), ('xi_rho', 48),
                  ('eta_u', 48), ('xi_u', 47), ('eta_v', 47), ('xi_v', 48)):
        d.createDimension(nm, n)
    d.createVariable('h', 'f8', ('eta_rho', 'xi_rho'))[:] = h
    d.createVariable('Cs_r', 'f8', ('s_rho',))[:] = -np.linspace(0.96, 0.04, 13) ** 1.5
    d.createVariable('ocean_time', 'f8', ('ocean_time',))[:] = np.arange(4) * 21600.0
    shp = dict(u=('ocean_time', 's_rho', 'eta_u', 'xi_u'), v=('ocean_time', 's_rho', 'eta_v', 'xi_v'),
               w=('ocean_time', 's_w', 'eta_rho', 'xi_rho'), temp=('ocean_time', 's_rho', 'eta_rho', 'xi_rho'),
               zeta=('ocean_time', 'eta_rho', 'xi_rho'))
    for f, dims in shp.items():
        var = d.createVariable(f, 'f4', dims)
        s = tuple(len(d.dimensions[x]) for x in dims)
        if f == 'temp':
            base = 4.0 + 20.0 * np.linspace(0, 1, s[1])[None, :, None, None] * np.ones(s)
            var[:] = base + (0 if zero_flow else 0.01 * rng.normal(size=s))
        elif zero_flow:
            var[:] = np.zeros(s)
        else:
            tf = (1.0 + 0.05 * np.arange(4))[:, None, None, None] if len(s) == 4 else (1.0 + 0.05 * np.arange(4))[:, None, None]
            var[:] = amp * tf * (0.5 + np.abs(rng.normal(size=s)))
    d.close()


def build_fixture(F):
    print('[2] 构造夹具于', F)
    yy, xx = np.meshgrid(np.arange(48), np.arange(48), indexing='ij')
    h_flat = np.full((48, 48), 4500.0)
    h_steep = 4500.0 - 4300.0 * np.exp(-((xx - 24) ** 2 + (yy - 24) ** 2) / 60.0)
    os.makedirs(f'{F}/ledger', exist_ok=True)
    zonal, reg = [], []
    V = [0.0, 50.0, 150.0, 400.0, 800.0, 1500.0, 2747.0]
    ids = [rid for _, rid in C.V7]
    extra = [('e2_fx_steep_a%d' % i, 'e2_fx_flat_a%d' % i, 100.0 * (i + 1)) for i in range(5)]
    for i, (v, rid) in enumerate(zip(V, ids)):
        fid = 'e2_fx_flat_v%d' % i
        amp = 10.0 / (1 + v / 300.0)
        write_nc(f'{F}/runs/{rid}/out_his.nc', h_steep, amp, 100 + i)
        write_nc(f'{F}/runs/{fid}/out_his.nc', h_flat, 0.3 * amp, 200 + i)
        for rr, b in ((rid, 'r26steep'), (fid, 'flat')):
            zonal.append(dict(run_id=rr, action=dict(bathy=b, VISC2=v, ntimes=8640, seed=0), bathy=b, seed=0,
                              obs=dict(valid=True), hidden={}, ntimes=8640))
        reg.append(dict(run_id=rid, err_rms=8.0 - 0.5 * i, skill_vs_zero=-8.0 + i))
    for j, (sid, fid, v) in enumerate(extra):
        write_nc(f'{F}/runs/{sid}/out_his.nc', h_steep, 5.0 + j, 300 + j)
        write_nc(f'{F}/runs/{fid}/out_his.nc', h_flat, 2.0 + j, 400 + j)
        for rr, b in ((sid, 'r26steep'), (fid, 'flat')):
            zonal.append(dict(run_id=rr, action=dict(bathy=b, VISC2=v, VISC4=1.0, ntimes=8640, seed=0), bathy=b, seed=0,
                              obs=dict(valid=True), hidden={}, ntimes=8640))
        reg.append(dict(run_id=sid, err_rms=5.0 + 0.1 * j, skill_vs_zero=-3.0 - j))
    zonal.append(zonal[0])  # 重复行
    for k, (key, v, b) in enumerate((('steep10000', 10000.0, 'r26steep'), ('steep30000', 30000.0, 'r26steep'), ('flat30000', 30000.0, 'flat'))):
        rid = C.ABSURD[key]
        write_nc(f'{F}/runs/{rid}/out_his.nc', h_steep if b == 'r26steep' else h_flat, 0.2, 500 + k)
        zonal.append(dict(run_id=rid, action=dict(bathy=b, VISC2=v, ntimes=8640, seed=0), bathy=b, seed=0,
                          obs=dict(valid=True), hidden={}, ntimes=8640))
        if b == 'r26steep':
            reg.append(dict(run_id=rid, err_rms=3.0, skill_vs_zero=-0.5))
    with open(f'{F}/ledger/env2_runs.jsonl', 'w') as f:
        for r in zonal:
            f.write(json.dumps(r) + '\n')
    with open(f'{F}/ledger/regraded_v2.jsonl', 'w') as f:
        for r in reg:
            f.write(json.dumps(r) + '\n')
    for lname, sub, seed0 in (('env2_merid_runs.jsonl', 'runs_merid', 600), ('env2_diag45_runs.jsonl', 'runs_diag45', 700)):
        rows = []
        for kn, knob in enumerate(('VISC2', 'VISC4', 'AKV_BAK', 'TNU2')):
            for i, v in enumerate(V):
                sid, fid = 'e2_fx_%s_%s_s%d' % (sub, knob, i), 'e2_fx_%s_%s_f%d' % (sub, knob, i)
                write_nc(f'{F}/{sub}/{sid}/out_his.nc', h_steep, 8.0 / (1 + v / 300.0), seed0 + 10 * kn + i)
                write_nc(f'{F}/{sub}/{fid}/out_his.nc', h_flat, 3.0 / (1 + v / 300.0), seed0 + 1000 + 10 * kn + i)
                hid = dict(skill_vs_zero=-6.0 + i + 0.1 * kn) if knob != 'AKV_BAK' else dict(skill_vs_zero=None)
                rows.append(dict(run_id=sid, action={'bathy': 'r26steep', knob: v + 0.001 * kn, 'ntimes': 8640, 'seed': 0}, bathy='r26steep',
                                 obs=dict(valid=True), hidden=hid, ntimes=8640))
                rows.append(dict(run_id=fid, action={'bathy': 'flat', knob: v + 0.001 * kn, 'ntimes': 8640, 'seed': 0}, bathy='flat',
                                 obs=dict(valid=True), hidden={}, ntimes=8640))
        with open(f'{F}/ledger/{lname}', 'w') as f:
            for r in rows:
                f.write(json.dumps(r) + '\n')
    st = []
    for i, v in enumerate(C.ST_V):
        write_nc(f'{F}/e56/runs/bh93_flat_v{v}/out_his.nc', h_flat, 0.0, 800 + i, zero_flow=True)
        write_nc(f'{F}/e56/runs/bh93_r26steep_v{v}/out_his.nc', h_steep, 9.0 / (1 + v / 500.0), 850 + i)
        st.append(dict(tag='bh93_flat_v%d' % v, u_max=0.0)); st.append(dict(tag='bh93_r26steep_v%d' % v, u_max=90.0 / (1 + v / 500.0)))
    os.makedirs(f'{F}/e56', exist_ok=True)
    json.dump(st, open(f'{F}/e56/E56_BH93.json', 'w'))
    # e60 故意缺失 → 测 L4 未跑路径

    # ---- 模块①③ 合成源 JSON ----
    Y = yaml.safe_load(open(os.path.join(HERE, 'mr_audit.yaml')))
    real_dom = '/home/xinyuan/比赛/赛道三赛题二/github_repo/e44_tide/analysis/upstream/DOMWIDTH_RESULT.json'
    fx_dom = f'{F}/repo/upstream/DOMWIDTH_RESULT.json'
    txt = open(os.path.join(HERE, 'mr_audit.yaml')).read().replace(real_dom, fx_dom)
    open(f'{F}/mr_audit.yaml', 'w').write(txt)
    Y = yaml.safe_load(txt)
    files = {}

    def put(ptr, value):
        path, _, keys = ptr.partition(':')
        path = path if path.startswith('/') else os.path.join(F, path)
        d = files.setdefault(path, {})
        if not keys:
            return
        ks = keys.split('.'); cur = d
        for k in ks[:-1]:
            cur = cur.setdefault(k, {})
        cur[ks[-1]] = value

    SYN = {
        'e44/analysis/RT2_FIXES.json:M27_Pnet_A1.flat': 0.1, 'e44/analysis/RT2_FIXES.json:M27_Pnet_A1.dj': 5.0,
        'e44/analysis/RT2_FIXES.json:M27_Pnet_A1.note': '换平底 → 变好看（合成）',
        'e44/analysis/E44_METRICS.json:d_flatdj.Pnet_MW': 1e-4,
        fx_dom + ':ratio_vs_84km': {'a': 1.0, 'b': 3.0}, fx_dom + ':judgement.main_branch': 'RESONANCE_CONTROLLED (合成)',
        'e44/analysis/RT2_FIXES.json:M2_phase.Pnet_lastframe.rel_change_pct': [-12.0, -3.0],
        'e44/agent/E54_NAMESWAP.json:conditions.C0_named.Pnet_trusted': 4, 'e44/agent/E54_NAMESWAP.json:conditions.C1_anon.Pnet_trusted': 0,
        'e44/analysis/RT2_FIXES.json:F2_A8_signed.Pnet_MW.signed_rho': 0.9, 'e44/analysis/RT2_FIXES.json:F2_A8_signed.Pnet_MW.p_exact_two_sided': 0.01,
        'e44/analysis/E57_PARETO.json:n_pairs': 20,
        'e44/analysis/RT2_FIXES.json:M2_phase.deep_dc_lastframe.rel_change_pct': 30.0,
        'e44/analysis/RT2_FIXES.json:M6_deep_rms_800.merid22': -0.8, 'e55/E55_CROSS.json:deep_u_diag45.paired': 0.95,
        'e44/agent/E54_NAMESWAP.json:conditions.C0_named.deepDC_gameable': 2, 'e44/agent/E54_NAMESWAP.json:conditions.C1_anon.deepDC_gameable': 2,
        'e44/analysis/RT2_FIXES.json:F2_A8_signed.deep_dc_rms.signed_rho': -0.5, 'e44/analysis/RT2_FIXES.json:F2_A8_signed.deep_dc_rms.p_exact_two_sided': 0.3,
        'e56/E56_VERDICT.json:A1_paired_correct': 0.0, 'e56/E56_VERDICT.json:V': [0, 1, 2, 3, 4, 5, 6],
        'e56/E56_VERDICT.json:bh93_deep800': [7, 6, 5, 4, 3, 2, 1],
        'e44/analysis/E49_CROSS.json:tempd400_wind.paired': 1.0, 'e44/analysis/E49_CROSS.json:tempd400_wind.rho': 0.3,
        'e44/analysis/RT2_FIXES.json:M27_temp_A4.rel_change_pct': [0.5, -0.2],
        'e44/analysis/RT2_FIXES.json:F2_A8_signed.temp_d400.signed_rho': 0.7, 'e44/analysis/RT2_FIXES.json:F2_A8_signed.temp_d400.p_exact_two_sided': 0.08,
        'e44/analysis/E58_TRIVALENT.json:rows.uv_zonal_paired.k': 30, 'e44/analysis/E58_TRIVALENT.json:rows.uv_zonal_paired.n': 32,
        'e44/analysis/E44_METRICS.json:pf_dj.uv_ratio': 1.0, 'e44/analysis/E44_METRICS.json:pf_v4.uv_ratio': 2.0, 'e44/analysis/E44_METRICS.json:pf_combo.uv_ratio': 3.0,
        'e44/analysis/E50_UV_AUDIT.json:boxwidth_500km.ps_dj': 1.1, 'e44/analysis/E50_UV_AUDIT.json:boxwidth_500km.ps_v4': 2.1,
        'e44/analysis/E50_UV_AUDIT.json:boxwidth_500km.ps_combo_m4': 3.3,
        'e44/analysis/RT2_FIXES.json:M2_phase.uv_lastframe': dict(c_g4=2.0, p_g4_plus=2.6, p_g4_minus=1.5),
        'e44/analysis/RT2_FIXES.json:M2_phase.uv_window_mean.rel_change_pct': [-5.0, 4.0],
        'e52/E52_CROSS.json:uv_merid.rho': -0.9, 'e52/E52_CROSS.json:uv_merid.paired': 0.5,
        'e44/agent/E54_NAMESWAP.json:conditions.C0_named.uv_gameable': 1, 'e44/agent/E54_NAMESWAP.json:conditions.C1_anon.uv_gameable': 3,
        'e44/analysis/RT2_FIXES.json:F2_A8_signed.uv_ratio.signed_rho': 0.85, 'e44/analysis/RT2_FIXES.json:F2_A8_signed.uv_ratio.p_exact_two_sided': 0.02,
        'ledger/metric_search.json:baseline': [None, None, -0.9, 0.2],
        'e44/analysis/E58_TRIVALENT.json:snr.verdict': '合成', 'e44/analysis/E44_METRICS.json:d_flatdj.uv_ratio': 999.0,
        'e65/E65_SPURIOUS_VS_TRUE.json:spearman_D_A': 0.5,
    }
    for k, v in SYN.items():
        put(k, v)
    put('e56/E56_VERDICT.json:bh93_umax', [st[2 * i + 1]['u_max'] for i in range(7)])
    # goodhart 证据/标本指针：补占位
    for dcell in Y['goodhart']['dead_cells']:
        for p in dcell['evidence']:
            ok = p.partition(':')[2] == '' or p in SYN
            if not ok and p not in SYN:
                put(p, '占位')
    for path, d in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.basename(path) == 'E56_BH93.json':
            continue
        json.dump(d, open(path, 'w'), ensure_ascii=False)
    os.makedirs(f'{F}/scripts', exist_ok=True); open(f'{F}/scripts/absurd_visc.py', 'w').write('# 夹具占位\n')
    # KILLBOARD 夹具：13 死格与 DEAD13 相同；其余格按合成期望，故意 4 处不一致
    rows = Y['rows']; cols_full = ['A1 x', 'A2 x', 'A3 x', 'A4 x', 'A5 x', 'A6 x', 'A7 x', 'A8 x', 'A9 x', 'R x']
    exp = {('Pnet_MW', 'A1'): '死', ('Pnet_MW', 'A2'): '过', ('Pnet_MW', 'A3'): '死', ('Pnet_MW', 'A4'): '死', ('Pnet_MW', 'A7'): '死', ('Pnet_MW', 'A8'): '过',
           ('deep_dc_rms', 'A1'): '死', ('deep_dc_rms', 'A4'): '死', ('deep_dc_rms', 'A6'): '死', ('deep_dc_rms', 'A7'): '过', ('deep_dc_rms', 'A8'): '死', ('deep_dc_rms', 'A9'): '死',
           ('temp_d400', 'A1'): '待定', ('temp_d400', 'A4'): '过', ('temp_d400', 'A6'): '死', ('temp_d400', 'A8'): '过',
           ('uv_ratio', 'A1'): '待定', ('uv_ratio', 'A2'): '死', ('uv_ratio', 'A3'): '过', ('uv_ratio', 'A4'): '边', ('uv_ratio', 'A6'): '死', ('uv_ratio', 'A7'): '死', ('uv_ratio', 'A8'): '过'}
    grid = [[dict(verdict=exp.get((r, c.split()[0]), '未'), text='', value=None, source='') for c in cols_full] for r in rows]
    os.makedirs(f'{F}/e44/analysis', exist_ok=True)
    json.dump(dict(rows=rows, cols=cols_full, grid=grid), open(f'{F}/e44/analysis/KILLBOARD.json', 'w'), ensure_ascii=False)
    # E57_PARETO 基础字段（front_sample 用真实 5 把的键名——只是名字）
    par = json.load(open(f'{F}/e44/analysis/E57_PARETO.json'))
    par['front_sample'] = [dict(num='u|all|rms', den='v|s200|p95'), dict(num='u|s200|rms', den='v|s50|p95'), dict(num='v|s50|rms', den='v|s50|p95'),
                           dict(num='u|s50|rms', den='v|s50|p95'), dict(num='u|d1500|p95', den='w|d1500|rms')]
    json.dump(par, open(f'{F}/e44/analysis/E57_PARETO.json', 'w'), ensure_ascii=False)


def main():
    F = sys.argv[1]
    if os.path.exists(F) and os.listdir(F):
        sys.exit('夹具目录须为空：' + F)
    os.makedirs(F, exist_ok=True)
    OUT = f'{F}/_out'
    unit_tests()
    build_fixture(F)

    print('[3] 模块④ 两遍')
    r = run([f'{HERE}/abm_chain.py', '--selftest', F, OUT]); check(r.returncode == 0, 'chain 第一遍退出 0')
    ab = np.load(f'{OUT}/_selftest_AB.npz'); A, B = ab['A'], ab['B']
    front = np.array([int(np.argmax(A)), int(np.argmax(B))])
    np.savez(f'{F}/e44/analysis/E57_AB.npz', A=A, B=B, front=front)
    par = json.load(open(f'{F}/e44/analysis/E57_PARETO.json'))
    n_both = int(((A >= 0.7) & (B >= 0.9)).sum()); n12 = int(((A >= 0.9) & (B >= 0.9)).sum())
    par_chain = dict(par, n_both=n_both, threshold_grid={'0.90/0.90': n12},
                     front_sample=[dict(num=str(ab['num'][i]), den=(None if ab['den'][i] == 'None' else str(ab['den'][i]))) for i in front])
    json.dump(par_chain, open(f'{F}/e44/analysis/E57_PARETO.json', 'w'), ensure_ascii=False)
    os.makedirs(f'{F}/e66', exist_ok=True)
    np.savez(f'{F}/e66/E66_AXES.npz', A=A, B=B, D=A, AP=A, G=np.zeros_like(A))
    json.dump(dict(n_both_Aperp=n_both), open(f'{F}/e66/E66_PARTIAL.json', 'w'))
    r = run([f'{HERE}/abm_chain.py', '--selftest', F, OUT]); check(r.returncode == 0, 'chain 第二遍退出 0')
    fc = json.load(open(f'{OUT}/ABM_FILTER_CHAIN.json'))
    check(fc['pipeline_anchor']['max_abs_diff_B_vs_E57'] == 0.0 and fc['pipeline_anchor']['front_names_match'], 'V2 锚在夹具上为 0 且 front 名对上')
    lv = fc['levels']
    ns = [lv[k]['n_survive'] for k in ('L0', 'L1', 'L2', 'L3')]
    check(all(ns[i] >= ns[i + 1] for i in range(3)), '滤链单调 %s' % ns)
    check(lv['L4'].get('status', '').startswith('未跑'), 'e60 缺失 → L4 未跑')
    check(fc['H_results']['0.00']['final_sets_identical'] is True, 'C2 三排法末级相同')
    check(fc['fallback_two_level'] is False, '夹具不触发回退')
    check(fc['levels']['L1']['n_survive'] == int(((B == 1.0) & (np.load(f'{OUT}/ABM_FILTER_CHAIN_MASKS.npz')['H0.00'][0])).sum()), 'H=0 时 L1 = L0∧(B==1)')
    for H in ('0.00', '0.01', '0.05'):
        h = fc['H_results'][H]['levels']
        check(h['L1']['elim_total'] == h['L1']['elim_undefined'] + h['L1']['elim_hack'], 'H=%s 淘汰分解守恒' % H)
    # 恢复 front_sample 为真实 5 把键名供模块②
    json.dump(par, open(f'{F}/e44/analysis/E57_PARETO.json', 'w'), ensure_ascii=False)

    print('[4] 模块②')
    r = run([f'{HERE}/abm_mutants.py', '--selftest', F, OUT]); check(r.returncode == 0, 'mutants 退出 0')
    km = json.load(open(f'{OUT}/ABM_KILL_MATRIX.json')); ml = json.load(open(f'{OUT}/ABM_MUTANT_LEDGER.json'))
    ros = {x['id']: x for x in ml['roster']}
    check(len(ros) == 40, '名册 40')
    check(ros['M6_b3'].get('status') == 'DUPLICATE' and ros['M6_b4'].get('status') == 'DUPLICATE', 'M6_b3/M6_b4 = DUPLICATE')
    check(ros['M8_b1'].get('status') == 'EQUIVALENT', 'M8_b1（分子区域 all）= EQUIVALENT')
    table = {'M4_b1': ('u|s50|rms', 'v|d1500|p95'), 'M4_b2': ('u|d1500|rms', 'v|d800|p95'), 'M4_b3': ('v|d800|rms', 'v|d800|p95'),
             'M4_b4': ('u|d800|rms', 'v|d800|p95'), 'M4_b5': ('u|s50|p95', 'w|s50|rms'),
             'M5_b1': ('u|d200|rms', 'v|s50|p95'), 'M5_b2': ('u|s50|rms', 'v|s200|p95'), 'M5_b3': ('v|s200|rms', 'v|s200|p95'),
             'M5_b4': ('u|s200|rms', 'v|s200|p95'), 'M5_b5': ('u|d800|p95', 'w|d800|rms'),
             'M6_b1': ('temp|all|mean_abs', 'v|s200|p95'), 'M6_b2': ('temp|all|mean_abs', 'v|s50|p95'), 'M6_b5': ('temp|all|mean_abs', 'w|d1500|rms')}
    check(all((ros[k]['formula']['num'], ros[k]['formula']['den']) == v for k, v in table.items()), '名册公式与 PREREG §2.5 表逐项一致')
    check(km['anchor_V5']['ok'] is True, 'V5：u|d800|rms 在夹具上 A1=死 ∧ A9′=死 (%s)' % km['anchor_V5']['verdicts'])
    us = km['classes']['unit_scale']
    check(us['killed'] == 0, 'unit_scale 零差分杀死（构造性）')
    ok_sem = True
    for x in ml['roster']:
        if x.get('status') == 'KILLED':
            ok_sem &= any(x['verdicts'][o] == '死' and x['base_verdicts'][o] != '死' for o in x['verdicts'])
        if x.get('status') == 'ESCAPED':
            ok_sem &= (x['n_judged'] >= 3 and not x['kill_ops'])
    check(ok_sem, '差分杀死/漏网语义逐体自洽')
    ov = km['overall']
    check(ov['n_judgeable'] == ov['n_killed'] + ov['n_escaped'] and ov['n_roster'] == 40, 'overall 计数守恒')
    r = run([f'{HERE}/abm_mutants.py', '--selftest', F, f'{F}/_out24', '--downgrade24']); check(r.returncode == 0, 'downgrade24 退出 0')
    k24 = json.load(open(f'{F}/_out24/ABM_KILL_MATRIX.json'))
    check(k24['downgraded'] is True and k24['overall']['n_roster'] == 24, '降档名册 24')

    print('[5] 模块①③')
    r = run([f'{HERE}/abm_mr_checker.py', '--selftest', F, OUT]); check(r.returncode == 0, 'checker 退出 0')
    mr = json.load(open(f'{OUT}/ABM_MR_CONSISTENCY.json'))
    check(mr['n_machine'] == 22 and mr['n_machine_evaluated'] == 22, '机器可判 22 格全部求值')
    dis = {(d['row'], d['col']) for d in mr['discrepancies']}
    check(dis == {('deep_dc_rms', 'A6'), ('uv_ratio', 'A6'), ('uv_ratio', 'A7'), ('temp_d400', 'A8')}, '夹具故意 4 处不一致被逐格抓出 %s' % sorted(dis))
    check(mr['real_anchor_check']['Pnet_MW_A3A4_dead'] is True and mr['real_anchor_check']['deep_dc_rms_A9_dead'] is True, 'V3 锚路径')
    check(mr['coverage_gate']['LOW_COVERAGE'] is True, '22<24 → LOW_COVERAGE')
    check(not mr['pipeline_issues'], 'checker 无 pipeline_issues %s' % mr['pipeline_issues'])
    r = run([f'{HERE}/abm_goodhart_map.py', '--selftest', F, OUT]); check(r.returncode == 0, 'goodhart 退出 0')
    gm = json.load(open(f'{OUT}/ABM_GOODHART_MAP.json'))
    check(gm['dead_set_match'] is True, '③ 死格集合匹配')
    check('regression_D' in gm['empty_type_columns'] and 'causal' in gm['empty_type_columns'], '③ 回归·D 与 因果 两列为空（声明结构）')
    check(gm['coverage_matrix']['A6']['regression_transfer'] == '有实证检出', '③ A6×回归·迁移 = 有实证检出')

    print('[6] 判分与故障注入')
    r = run([f'{HERE}/abm_verdict.py', '--selftest', OUT]); check(r.returncode == 0, 'verdict 退出 0')
    vd = json.load(open(f'{OUT}/verdict.json'))
    check(vd['n_counted'] == 11 and sum(vd['tally'].values()) == 11, 'tally 只计 11 条')
    check('P1' not in vd['predictions'] and 'P2a' not in vd['predictions'] and 'K1' in vd['known_checks'] and 'C1' in vd['constructive'], 'P1→K1、P2a→C1')
    check(vd['known_checks']['K1']['status'] == 'FAIL' and vd['known_checks']['K1']['value']['n_disagree'] == 4, 'K1 在夹具上 FAIL(4)')
    # 注入 1：缺 n_disagree
    inj = f'{F}/_inj1'; shutil.copytree(OUT, inj)
    m1 = json.load(open(f'{inj}/ABM_MR_CONSISTENCY.json')); m1.pop('n_disagree'); json.dump(m1, open(f'{inj}/ABM_MR_CONSISTENCY.json', 'w'))
    run([f'{HERE}/abm_verdict.py', '--selftest', inj]); v1 = json.load(open(f'{inj}/verdict.json'))
    check(v1['known_checks']['K1']['status'] == 'NOT_RUN' and any('K1 缺字段' in x for x in v1['pipeline_suspect_reasons']), '注入缺 n_disagree → NOT_RUN ＋ PIPELINE_SUSPECT（理由含 K1 缺字段）')
    # 注入 2：全类不可判
    inj = f'{F}/_inj2'; shutil.copytree(OUT, inj)
    k2 = json.load(open(f'{inj}/ABM_KILL_MATRIX.json')); c = k2['classes']['wrong_layer']
    c.update(killed=0, escaped=0, n_judgeable=0, unjudgeable=c['n_eval']); json.dump(k2, open(f'{inj}/ABM_KILL_MATRIX.json', 'w'))
    run([f'{HERE}/abm_verdict.py', '--selftest', inj]); v2 = json.load(open(f'{inj}/verdict.json'))
    check(v2['predictions']['P2h']['status'] == 'UNJUDGEABLE' and v2['tally']['UNJUDGEABLE'] >= 1, '全类不可判 → UNJUDGEABLE 并入 tally')
    # 注入 3：缺 kill matrix、错锚
    inj = f'{F}/_inj3'; shutil.copytree(OUT, inj); os.remove(f'{inj}/ABM_KILL_MATRIX.json')
    f3 = json.load(open(f'{inj}/ABM_FILTER_CHAIN.json')); f3['pipeline_anchor']['max_abs_diff_B_vs_E57'] = 0.03125; json.dump(f3, open(f'{inj}/ABM_FILTER_CHAIN.json', 'w'))
    run([f'{HERE}/abm_verdict.py', '--selftest', inj]); v3 = json.load(open(f'{inj}/verdict.json'))
    check(all(v3['predictions'][k]['status'] == 'NOT_RUN' for k in ('P2b', 'P2i')) and any('V2' in x for x in v3['pipeline_suspect_reasons']), '缺矩阵 → NOT_RUN；V2≠0 → PIPELINE_SUSPECT（理由含 V2）')
    # 注入 4：回退两级
    inj = f'{F}/_inj4'; shutil.copytree(OUT, inj)
    f4 = json.load(open(f'{inj}/ABM_FILTER_CHAIN.json')); f4['fallback_two_level'] = True; json.dump(f4, open(f'{inj}/ABM_FILTER_CHAIN.json', 'w'))
    run([f'{HERE}/abm_verdict.py', '--selftest', inj]); v4 = json.load(open(f'{inj}/verdict.json'))
    check(all(v4['predictions'][k]['status'] == 'NOT_RUN' for k in ('P4a', 'P4b', 'P4c')), '回退两级 → P4a–c NOT_RUN')

    print('\nSELFTEST %s（失败 %d 项）' % ('PASS' if not FAILS else 'FAIL', len(FAILS)))
    for f in FAILS:
        print('  -', f)
    json.dump(dict(passed=not FAILS, failures=FAILS, when=C.now(),
                   code_sha={n: C.sha256(os.path.join(HERE, n)) for n in sorted(os.listdir(HERE)) if n.startswith('abm_') and n.endswith('.py')}),
              open(f'{F}/SELFTEST_RESULT.json', 'w'), ensure_ascii=False, indent=1)
    sys.exit(0 if not FAILS else 1)


if __name__ == '__main__':
    main()
