#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""abm_chain.py — 模块④ 滤链曲线（PREREG §2.7）。

15376 候选（E57 序复现）→ V2 管线锚（B 与 E57_AB.npz 逐候选差=0）→ L0/S_zonal/S_rotate/S_absurd/(S_e60) 逐级计数，
H∈{0,0.01,0.05}，三种排法；204/444/12 参考集留存；P4a–P4c 所需字段。
产出：ABM_FILTER_CHAIN.json、ABM_FILTER_CHAIN_MASKS.npz、abm_chain_curve.png。
用法：abm_chain.py | abm_chain.py --selftest <夹具根> <输出目录>
"""
import json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import abm_common as C

EPS = 1e-12
HS = [0.0, 0.01, 0.05]


def main():
    t0 = time.time()
    selftest = len(sys.argv) > 1 and sys.argv[1] == '--selftest'
    if selftest:
        env, outdir = sys.argv[2], sys.argv[3]
        bq = lambda rd: C.ext_base_quantities(rd)[0]
    else:
        C.seal_gate(False)
        env, outdir = C.ENV_REAL, C.FINAL
        sys.path.insert(0, f'{env}/scripts')
        from metric_search import base_quantities as bq
    os.makedirs(outdir, exist_ok=True)
    log = []

    def say(*a):
        s = ' '.join(str(x) for x in a); log.append('[%6.1fs] %s' % (time.time() - t0, s)); print(log[-1], flush=True)

    # ---------- E57 复现 ----------
    Z = C.zonal_sets(env)
    Q26, S26, QFL, steep_ids = [], [], [], []
    for rid in Z['steep']:
        q = bq(f'{env}/runs/{rid}')
        if q:
            Q26.append(q); S26.append(Z['skill'][rid]); steep_ids.append(rid)
    for rid in Z['flat']:
        q = bq(f'{env}/runs/{rid}')
        if q:
            QFL.append(q)
    keys = sorted(set.intersection(*[set(q) for q in Q26 + QFL]))
    K = {k: i for i, k in enumerate(keys)}
    M26 = np.array([[q[k] for k in keys] for q in Q26]); MFL = np.array([[q[k] for k in keys] for q in QFL]); S = np.array(S26)
    P26L, PFLL, pair_ids = [], [], []
    for a, b in Z['pairs']:
        qa, qb = bq(f'{env}/runs/{a}'), bq(f'{env}/runs/{b}')
        if qa and qb and all(k in qa and k in qb for k in keys):
            P26L.append([qa[k] for k in keys]); PFLL.append([qb[k] for k in keys]); pair_ids.append((a, b))
    P26, PFL = np.array(P26L), np.array(PFLL)
    say('E57 复现输入：陡臂 %d 平底 %d 配对 %d 基元 %d' % (len(M26), len(MFL), len(P26), len(keys)))
    names, A, B = [], [], []
    for i, kn in enumerate(keys):
        cand = [(kn, None, M26[:, i], MFL[:, i], P26[:, i], PFL[:, i])]
        for j, kd in enumerate(keys):
            if i == j:
                continue
            if np.any(np.abs(M26[:, j]) < EPS) or np.any(np.abs(MFL[:, j]) < EPS) or np.any(np.abs(P26[:, j]) < EPS) or np.any(np.abs(PFL[:, j]) < EPS):
                continue
            cand.append((kn, kd, M26[:, i] / M26[:, j], MFL[:, i] / MFL[:, j], P26[:, i] / P26[:, j], PFL[:, i] / PFL[:, j]))
        for kn_, kd_, v26, vfl, p26, pfl in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))):
                continue
            if np.any(v26 <= 0) or np.any(vfl <= 0):
                continue
            names.append((kn_, kd_)); A.append(-C.spearman(v26, S)); B.append(float((pfl >= p26).mean()) if len(p26) else 0.0)
    A = np.array(A); B = np.array(B); NC = len(names)
    say('候选 %d' % NC)
    num_idx = np.array([K[n] for n, _ in names]); den_idx = np.array([K[d] if d is not None else -1 for _, d in names])

    if selftest:
        np.savez(os.path.join(outdir, '_selftest_AB.npz'), A=A, B=B,
                 num=np.array([n for n, _ in names]), den=np.array([str(d) for _, d in names]))
        if not os.path.exists(f'{env}/e44/analysis/E57_AB.npz'):
            say('selftest 第一遍：已写 _selftest_AB.npz，夹具尚无 E57_AB.npz，退出'); return
    e57p = f'{env}/e44/analysis/E57_AB.npz'
    E57 = np.load(e57p); PAR = json.load(open(f'{env}/e44/analysis/E57_PARETO.json'))
    anchor = dict(n_candidates=NC, n_candidates_ok=(NC == len(E57['B'])))
    if NC == len(E57['B']):
        anchor['max_abs_diff_B_vs_E57'] = float(np.max(np.abs(B - E57['B'])))
        anchor['max_abs_diff_A_vs_E57'] = float(np.max(np.abs(A - E57['A'])))
        fr = [dict(num=names[i][0], den=names[i][1]) for i in E57['front']]
        anchor['front_names_match'] = all(f['num'] == s['num'] and f['den'] == s['den'] for f, s in zip(fr, PAR['front_sample']))
    else:
        anchor['max_abs_diff_B_vs_E57'] = None; anchor['max_abs_diff_A_vs_E57'] = None; anchor['front_names_match'] = False
    say('V2 管线锚：max|ΔB|=%s max|ΔA|=%s front 名对上=%s' % (anchor['max_abs_diff_B_vs_E57'], anchor['max_abs_diff_A_vs_E57'], anchor['front_names_match']))

    # ---------- 读数矩阵 ----------
    def qmat(dirs):
        rows, fail = [], []
        for d in dirs:
            q = bq(d)
            if not q:
                fail.append(d); rows.append([np.nan] * len(keys))
            else:
                rows.append([q.get(k, np.nan) for k in keys])
        return np.array(rows, float), fail

    def read(X):
        with np.errstate(divide='ignore', invalid='ignore'):
            num = X[:, num_idx]
            den = np.where(den_idx[None, :] >= 0, X[:, np.maximum(den_idx, 0)], 1.0)
            return num / den    # (R, NC)

    def pairs_step(RS, RF, H):
        with np.errstate(invalid='ignore'):
            undef = ~(np.isfinite(RS) & np.isfinite(RF))
            hack = (RF < RS * (1.0 - H)) & ~undef
        return ~(undef.any(axis=0) | hack.any(axis=0)), undef.any(axis=0), hack.any(axis=0) & ~undef.any(axis=0)

    fallback = False; fail_sets = {}
    Mw = C.other_wind_sets(env, 'env2_merid_runs.jsonl', 'runs_merid')
    Dw = C.other_wind_sets(env, 'env2_diag45_runs.jsonl', 'runs_diag45')
    XMs, fm1 = qmat([f"{Mw['runs_dir']}/{a}" for a, _ in Mw['pairs']]); XMf, fm2 = qmat([f"{Mw['runs_dir']}/{b}" for _, b in Mw['pairs']])
    XDs, fd1 = qmat([f"{Dw['runs_dir']}/{a}" for a, _ in Dw['pairs']]); XDf, fd2 = qmat([f"{Dw['runs_dir']}/{b}" for _, b in Dw['pairs']])
    XV7, fv = qmat([f'{env}/runs/{rid}' for _, rid in C.V7])
    XAB, fa = qmat([f"{env}/runs/{C.ABSURD[k]}" for k in ('steep10000', 'steep30000', 'flat30000')])
    fail_sets = dict(merid=fm1 + fm2, diag45=fd1 + fd2, V7=fv, absurd=fa)
    E60 = C.e60_pairs(env)
    XEs, fe1 = qmat([a for a, _ in E60]); XEf, fe2 = qmat([b for _, b in E60])
    e60_ok = not (fe1 or fe2)
    wall_read = time.time() - t0
    if wall_read > 45 * 60 or any(fail_sets.values()) or len(Mw['pairs']) != 28 or len(Dw['pairs']) != 28:
        fallback = True
    say('读数再生完成 %.1fs；配对 经向 %d 45° %d；失败 %s；e60_ok=%s；fallback=%s' % (
        wall_read, len(Mw['pairs']), len(Dw['pairs']), {k: len(v) for k, v in fail_sets.items()}, e60_ok, fallback))

    R26 = M26[:, num_idx] / np.where(den_idx[None, :] >= 0, M26[:, np.maximum(den_idx, 0)], 1.0)
    RP26, RPFL = read(P26), read(PFL)
    RMs, RMf, RDs, RDf = read(XMs), read(XMf), read(XDs), read(XDf)
    RV7, RAB = read(XV7), read(XAB)
    REs, REf = read(XEs), read(XEf)

    with np.errstate(invalid='ignore'):
        L0 = np.all(np.isfinite(R26), axis=0) & (np.nanstd(R26, axis=0) > 0)

    def steps(H):
        z_ok, z_und, z_hack = pairs_step(RP26, RPFL, H)
        m_ok, m_und, m_hack = pairs_step(np.vstack([RMs, RDs]), np.vstack([RMf, RDf]), H)
        # 荒谬黏性
        with np.errstate(invalid='ignore'):
            und_a = ~np.all(np.isfinite(np.vstack([RAB, RV7])), axis=0)
            pair_hack = RAB[2] < RAB[1] * (1.0 - H)
            vmin = np.min(RV7, axis=0)
            ext_hack = (RAB[0] < vmin * (1.0 - H)) | (RAB[1] < vmin * (1.0 - H))
            a_hack = (pair_hack | ext_hack) & ~und_a
        a_ok = ~(und_a | a_hack)
        e_ok, e_und, e_hack = pairs_step(REs, REf, H)
        return dict(zonal=(z_ok, z_und, z_hack), rotate=(m_ok, m_und, m_hack),
                    absurd=(a_ok, und_a, a_hack, pair_hack & ~und_a, ext_hack & ~und_a), e60=(e_ok, e_und, e_hack))

    Hres = {}; masks = {}
    for H in HS:
        st = steps(H)
        L1 = L0 & st['zonal'][0]; L2 = L1 & st['rotate'][0]; L3 = L2 & st['absurd'][0]; L4 = L3 & st['e60'][0]
        def br(prev, stp):
            return dict(elim_total=int((prev & ~stp[0]).sum()), elim_undefined=int((prev & stp[1]).sum()),
                        elim_hack=int((prev & stp[2]).sum()))
        lv = dict(L0=dict(n_survive=int(L0.sum()), elim_degenerate=int(NC - L0.sum())),
                  L1=dict(n_survive=int(L1.sum()), **br(L0, st['zonal'])),
                  L2=dict(n_survive=int(L2.sum()), **br(L1, st['rotate'])),
                  L3=dict(n_survive=int(L3.sum()), **br(L2, st['absurd']),
                          elim_pair30000=int((L2 & st['absurd'][3]).sum()), elim_extremal=int((L2 & st['absurd'][4]).sum())),
                  L4=(dict(n_survive=int(L4.sum()), **br(L3, st['e60'])) if e60_ok else dict(status='未跑（e60 读取失败）')))
        single = {k: int((L0 & ~st[k][0]).sum()) for k in ('zonal', 'rotate', 'absurd')}
        desc = sorted(single, key=lambda k: -single[k]); asc = sorted(single, key=lambda k: single[k])
        def curve(order):
            cur = L0.copy(); c = [dict(step='L0', n=int(cur.sum()))]
            for k in order:
                cur = cur & st[k][0]; c.append(dict(step=k, n=int(cur.sum())))
            return c, cur
        cg, fg = curve(['zonal', 'rotate', 'absurd']); cd, fdm = curve(desc); ca, fam = curve(asc)
        Hres['%.2f' % H] = dict(levels=lv, single_step_kill_on_L0=single,
                                orders=dict(geometric=cg, desc_by_kill=dict(order=desc, curve=cd), asc_by_kill=dict(order=asc, curve=ca)),
                                final_sets_identical=bool(np.array_equal(fg, fdm) and np.array_equal(fg, fam)))
        masks['H%.2f' % H] = np.vstack([L0, L1, L2, L3, L4])
    say('H=0 各级：%s' % {k: v.get('n_survive') for k, v in Hres['0.00']['levels'].items()})

    # ---------- 参考集 ----------
    SA = (E57['A'] >= 0.7) & (E57['B'] >= 0.9)
    S12 = (E57['A'] >= 0.9) & (E57['B'] >= 0.9)
    E66 = np.load(f'{env}/e66/E66_AXES.npz'); S444 = (E66['AP'] >= 0.7) & (E66['B'] >= 0.9)
    j66 = json.load(open(f'{env}/e66/E66_PARTIAL.json'))
    an = dict(n_both_204=int(SA.sum()), strict_12=int(S12.sum()), n_aperp_444=int(S444.sum()),
              json_n_both=PAR['n_both'], json_strict=PAR['threshold_grid']['0.90/0.90'], json_n_both_Aperp=j66['n_both_Aperp'])
    an['match'] = (an['n_both_204'] == an['json_n_both'] == 204 and an['strict_12'] == an['json_strict'] == 12
                   and an['n_aperp_444'] == an['json_n_both_Aperp'] == 444)
    m0 = masks['H0.00']
    retention = {nm: {lvl: int((S & m0[i]).sum()) for i, lvl in enumerate(['L0', 'L1', 'L2', 'L3', 'L4'])}
                 for nm, S in (('S_A_204', SA), ('S_Aperp_444', S444), ('S_strict_12', S12))}
    say('参考集：%s；留存 %s' % (an, retention))

    L3m = m0[3]
    out = dict(entry='audit_battery_meta/module4', when=C.now(), selftest=selftest,
               code_sha=C.code_sha(__file__), common_sha=C.code_sha(C.__file__),
               prereg_sha=None if selftest else C.sha256(C.PREREG),
               input_sha=dict(E57_AB=C.sha256(e57p), E66_AXES=C.sha256(f'{env}/e66/E66_AXES.npz'),
                              env2_runs=C.sha256(f'{env}/ledger/env2_runs.jsonl'), regraded_v2=C.sha256(f'{env}/ledger/regraded_v2.jsonl')),
               pipeline_anchor=anchor, anchors=an,
               fallback_two_level=fallback, fail_sets=fail_sets, e60_ok=e60_ok,
               run_counts=dict(Z58=len(M26), Zflat=len(MFL), Z32=len(P26), M28=len(Mw['pairs']), D28=len(Dw['pairs']), V7=len(C.V7), absurd=3, e60_pairs=len(E60)),
               H_main=0.0, H_results=Hres,
               levels=Hres['0.00']['levels'],
               S_A_intersect_L3=int((SA & L3m).sum()),
               set_retention_H0=retention,
               L3_survivors_H0=[dict(num=names[i][0], den=names[i][1], A=float(E57['A'][i]), B=float(E57['B'][i]))
                                for i in np.where(L3m)[0][:3000]],
               derived=dict(n_B_eq_1_E57=int((E57['B'] == 1.0).sum()),
                            note='派生非预测：封存后由 E57_AB.npz 计出'),
               wall_s=round(time.time() - t0, 1), log=log)
    if fallback:
        out['levels'] = dict(L0=Hres['0.00']['levels']['L0'], L1=Hres['0.00']['levels']['L1'])
        out['note_fallback'] = '回退两级：L2/L3 计数不作判分输入，P4a–P4c 记 NOT_RUN'
    C.dump(out, os.path.join(outdir, 'ABM_FILTER_CHAIN.json'))
    np.savez_compressed(os.path.join(outdir, 'ABM_FILTER_CHAIN_MASKS.npz'),
                        levels=np.array(['L0', 'L1', 'L2', 'L3', 'L4']), **masks,
                        num=np.array([n for n, _ in names]), den=np.array([str(d) for _, d in names]))

    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8.2, 4.8))
        for H, sty in zip(HS, ['-', '--', ':']):
            c = Hres['%.2f' % H]['orders']['geometric']
            ax.plot(range(len(c)), [x['n'] for x in c], sty, marker='o', color='#1f4e79', label='geometric H=%.2f' % H)
        for key, colr in (('desc_by_kill', '#b85c00'), ('asc_by_kill', '#2e7d32')):
            c = Hres['0.00']['orders'][key]['curve']
            ax.plot(range(len(c)), [x['n'] for x in c], '-', marker='s', color=colr, alpha=0.7,
                    label='%s H=0 (%s)' % (key, '→'.join(Hres['0.00']['orders'][key]['order'])))
        for ref, lab in ((204, '204 two-gate'), (444, '444 A-perp gate'), (12, '12 strict 0.90/0.90')):
            ax.axhline(ref, color='grey', lw=0.8, ls='-.'); ax.text(3.05, ref, lab, va='center', fontsize=8)
        ax.set_yscale('symlog', linthresh=10); ax.set_xticks(range(4)); ax.set_xticklabels(['L0', '+step1', '+step2', '+step3'])
        ax.set_ylabel('surviving candidates'); ax.set_title('Filter-chain survival (15376 candidates)'); ax.legend(fontsize=7)
        fig.tight_layout(); fig.savefig(os.path.join(outdir, 'abm_chain_curve.png'), dpi=160)
    except Exception as e:
        say('作图失败（不影响判分）：%s' % e)
    print(json.dumps(dict(pipeline_anchor=anchor, anchors_match=an['match'], levels_H0={k: v.get('n_survive') for k, v in out['levels'].items()},
                          S_A_intersect_L3=out['S_A_intersect_L3'], fallback=fallback, wall_s=out['wall_s']), ensure_ascii=False))


if __name__ == '__main__':
    main()
