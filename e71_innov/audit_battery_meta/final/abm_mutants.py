#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""abm_mutants.py — 模块② 变异 kill 矩阵（PREREG §2.5）。

5 把基指标（E57 front_sample）× 8 类 = 40 个显式名册变异体（--downgrade24 → b1–b3 共 24）
过电池可执行子集 {A1, A2, A3′, A4′, A6, A8, A9′}；主口径 = 差分杀死，敏感性 = 绝对检出。
产出：ABM_MUTANT_LEDGER.json、ABM_KILL_MATRIX.json。
用法：abm_mutants.py [--downgrade24] | abm_mutants.py --selftest <夹具根> <输出目录> [--downgrade24]
"""
import json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import abm_common as C

OPS = ['A1', 'A2', 'A3p', 'A4p', 'A6', 'A8', 'A9p']
CLASSES = ['unit_scale', 'mono_norm', 'sign_flip', 'wrong_region', 'wrong_layer', 'irrelevant_num', 'clip_cheat', 'boxwidth_dep']
CLS_NO = {c: i + 1 for i, c in enumerate(CLASSES)}
REGION_MAP = dict(all='s50', d200='s200', d400='s200', d800='s50', d1500='s50', s50='d800', s200='d1500')
LAYER_MAP = dict(all='d200', d200='d400', d400='d200', d800='d400', d1500='d800', s50='s200', s200='s50')
IRR = 'temp|all|mean_abs'
SCALE = 3.7817


def remap(key, mp):
    if key is None:
        return None
    f, r, s = key.split('|')
    return '%s|%s|%s' % (f, mp[r], s)


def roster(bases, nb):
    out = []
    for k in range(1, nb + 1):
        bn, bd = bases[k - 1]
        for cls in CLASSES:
            m = dict(id='M%d_b%d' % (CLS_NO[cls], k), cls=cls, base='b%d' % k, num=bn, den=bd, tf='none')
            if cls == 'unit_scale':
                m['tf'] = 'scale'
            elif cls == 'mono_norm':
                m['tf'] = 'square'
            elif cls == 'sign_flip':
                m['tf'] = 'neg'
            elif cls == 'wrong_region':
                m['num'], m['den'] = remap(bn, REGION_MAP), remap(bd, REGION_MAP)
            elif cls == 'wrong_layer':
                m['num'], m['den'] = remap(bn, LAYER_MAP), remap(bd, LAYER_MAP)
            elif cls == 'irrelevant_num':
                m['num'] = IRR
            elif cls == 'clip_cheat':
                m['tf'] = 'clip'
            elif cls == 'boxwidth_dep':
                m['tf'] = 'box'
            out.append(m)
    # DUPLICATE：同类中公式（num,den,tf）与先出现者相同
    seen = {}
    for m in out:
        sig = (m['cls'], m['num'], m['den'], m['tf'], m['base'] if m['tf'] in ('clip', 'box', 'scale', 'square', 'neg') else '')
        if sig in seen:
            m['duplicate_of'] = seen[sig]
        else:
            seen[sig] = m['id']
    return out


def main():
    t0 = time.time()
    args = sys.argv[1:]
    selftest = bool(args) and args[0] == '--selftest'
    down24 = '--downgrade24' in args
    if selftest:
        env, outdir = args[1], args[2]
        orig_bq = None
    else:
        C.seal_gate(False)
        env, outdir = C.ENV_REAL, C.FINAL
        sys.path.insert(0, f'{env}/scripts')
        from metric_search import base_quantities as orig_bq
    os.makedirs(outdir, exist_ok=True)
    log = []

    def say(*a):
        s = ' '.join(str(x) for x in a); log.append('[%6.1fs] %s' % (time.time() - t0, s)); print(log[-1], flush=True)

    # ---------- 运行集合与上下文 ----------
    Z = C.zonal_sets(env)
    Mw = C.other_wind_sets(env, 'env2_merid_runs.jsonl', 'runs_merid')
    ST = C.static_sets(env)
    cache = {}; impl_mismatch = []; read_fail = []

    def get(rd, frame=-1, scale=1.0):
        key = (rd, frame, scale)
        if key not in cache:
            q, N = C.ext_base_quantities(rd, frame=frame, scale=scale)
            if q is None:
                read_fail.append(key)
            if frame == -1 and scale == 1.0 and orig_bq is not None:
                q0 = orig_bq(rd)
                if not ((q is None and q0 is None) or (q is not None and q0 is not None and q == q0)):
                    impl_mismatch.append(rd)
            cache[key] = (q, N)
        return cache[key]

    runs_dir = f'{env}/runs'
    Z58 = [f'{runs_dir}/{r}' for r in Z['steep']]
    ctx = dict(
        Z58=[get(d) for d in Z58],
        Z58_s075=[get(d, scale=0.75) for d in Z58],
        Z58_s125=[get(d, scale=1.25) for d in Z58],
        Z58_f2=[get(d, frame=-2) for d in Z58],
        Z32_steep=[get(f'{runs_dir}/{a}') for a, _ in Z['pairs']],
        Z32_flat=[get(f'{runs_dir}/{b}') for _, b in Z['pairs']],
        MT_steep=[get(f"{Mw['runs_dir']}/{r}") for r in Mw['steep_truth']],
        M28_steep=[get(f"{Mw['runs_dir']}/{a}") for a, _ in Mw['pairs']],
        M28_flat=[get(f"{Mw['runs_dir']}/{b}") for _, b in Mw['pairs']],
        V7=[get(f'{runs_dir}/{rid}') for _, rid in C.V7],
        ST_flat=[get(d) for d in ST['flat']],
        ST_steep=[get(d) for d in ST['steep']])
    skill_MT = np.array([Mw['skill'][r] for r in Mw['steep_truth']], float)
    err_V7 = np.array([Z['reg'][rid]['err_rms'] for _, rid in C.V7], float)
    umax_ST = np.array(ST['umax'], float)
    say('上下文就绪：Z58 %d Z32 %d MT %d M28 %d V7 %d ST %d；读失败 %d；实现锚不符 %d' % (
        len(Z58), len(Z['pairs']), len(Mw['steep_truth']), len(Mw['pairs']), len(ctx['V7']), len(ctx['ST_steep']), len(read_fail), len(impl_mismatch)))

    # ---------- 指标读数 ----------
    PAR = json.load(open(f'{env}/e44/analysis/E57_PARETO.json'))
    bases = [(s['num'], s['den']) for s in PAR['front_sample']][:5]
    nb = 3 if down24 else 5

    def raw(m, qN):
        q, N = qN
        if q is None:
            return np.nan
        vn = q.get(m['num'], np.nan)
        vd = q.get(m['den'], np.nan) if m['den'] is not None else 1.0
        with np.errstate(divide='ignore', invalid='ignore'):
            v = np.float64(vn) / np.float64(vd)
        return v

    def reading(m, qN):
        v = raw(m, qN)
        tf = m['tf']
        if tf == 'scale':
            return SCALE * v
        if tf == 'square':
            return v * v
        if tf == 'neg':
            return -v
        if tf == 'clip':
            return np.minimum(v, m['c'])
        if tf == 'box':
            N = qN[1]
            if N is None or m['num'] not in N:
                return np.nan
            return v * (N[m['num']] / m['N_ref'])
        return v

    def vec(m, key):
        return np.array([reading(m, qN) for qN in ctx[key]], float)

    def prep(m):
        if m['tf'] == 'clip':
            b = dict(m, tf='none'); m['c'] = float(np.median(vec(b, 'Z58')))
        if m['tf'] == 'box':
            Ns = [qN[1].get(m['num']) if qN[1] else None for qN in ctx['Z58']]
            m['N_ref'] = Ns[0]
            m['N_ref_consistent'] = (None not in Ns) and len(set(Ns)) == 1
        return m

    def battery(m):
        res = {}; fin = lambda *xs: all(np.all(np.isfinite(x)) for x in xs)
        s, f = vec(m, 'Z32_steep'), vec(m, 'Z32_flat')
        if fin(s, f) and len(s):
            Bv = float(np.mean(f >= s)); k = int(np.sum(f >= s))
            res['A1'] = dict(v=C.v_A1_plain(Bv), B=Bv, k=k, n=len(s), trivalent_sensitivity=C.v_A1_trivalent(k, len(s)))
        else:
            res['A1'] = dict(v=C.NA, why='非有限读数')
        if m['den'] is None:
            if fin(s, f) and len(s):
                with np.errstate(divide='ignore', invalid='ignore'):
                    r = abs(np.median(f)) / abs(np.median(s))
                res['A2'] = dict(v=(C.DEAD if not np.isfinite(r) else (C.PASS if r < 0.01 else C.EDGE)), ratio=float(r) if np.isfinite(r) else None)
            else:
                res['A2'] = dict(v=C.NA, why='非有限读数')
        else:
            res['A2'] = dict(v=C.NA, why='比值型：A2 只判绝对型')
        z = vec(m, 'Z58')
        amps, ords = [], []; ok3 = fin(z)
        for key in ('Z58_s075', 'Z58_s125'):
            zs = vec(m, key)
            if not (ok3 and fin(zs)):
                ok3 = False; break
            with np.errstate(divide='ignore', invalid='ignore'):
                rr = np.abs(zs / z - 1.0)
            if not fin(rr):
                ok3 = False; break
            amps.append(float(np.median(rr))); ords.append(C.spearman(z, zs))
        if ok3:
            amp, od = max(amps), min(ords)
            res['A3p'] = dict(v=(C.DEAD if od < 0.95 else (C.EDGE if amp >= 0.20 else C.PASS)), amp=amp, ord=od, amps=amps, ords=ords)
        else:
            res['A3p'] = dict(v=C.NA, why='非有限读数')
        z2 = vec(m, 'Z58_f2')
        with np.errstate(divide='ignore', invalid='ignore'):
            rr = np.abs(z2 / z - 1.0)
        if fin(z, z2, rr):
            rel = float(np.median(rr)); od = C.spearman(z, z2)
            res['A4p'] = dict(v=(C.PASS if rel < 0.10 else (C.EDGE if od >= 0.95 else C.DEAD)), rel=rel, ord=od)
        else:
            res['A4p'] = dict(v=C.NA, why='非有限读数')
        mt = vec(m, 'MT_steep'); ms, mf = vec(m, 'M28_steep'), vec(m, 'M28_flat')
        if fin(mt, ms, mf) and len(mt) and len(ms):
            Am = C.spearman(mt, skill_MT); Bm = float(np.mean(mf >= ms))
            res['A6'] = dict(v=C.v_A6(Am, Bm), A_m=Am, B_m=Bm, n_truth=len(mt), n_pairs=len(ms), A_m_avgrank=C.spearman_avg(mt, skill_MT))
        else:
            res['A6'] = dict(v=C.NA, why='非有限读数')
        v7 = vec(m, 'V7')
        if fin(v7):
            rho, p = C.exact_p(v7, err_V7)
            res['A8'] = dict(v=C.v_A8(rho, p), rho=rho, p=p, rho_avgrank=C.spearman_avg(v7, err_V7))
        else:
            res['A8'] = dict(v=C.NA, why='非有限读数')
        sf, ss = vec(m, 'ST_flat'), vec(m, 'ST_steep')
        parts = {}
        if fin(sf, ss):
            Bs = float(np.mean(sf >= ss)); parts['A1_part'] = dict(v=C.v_A1_plain(Bs), B=Bs)
        else:
            parts['A1_part'] = dict(v=C.NA, why='非有限读数（静止平底场全零时比值型 0/0）')
        if fin(ss):
            rho, p = C.exact_p(ss, umax_ST); parts['A8_part'] = dict(v=C.v_A8(rho, p), rho=rho, p=p)
        else:
            parts['A8_part'] = dict(v=C.NA, why='非有限读数')
        res['A9p'] = dict(v=C.worst([parts['A1_part']['v'], parts['A8_part']['v']]), **parts)
        return res

    def contexts_equal(m, b):
        for key in ctx:
            if not np.array_equal(vec(m, key), vec(b, key), equal_nan=True):
                return False
        return True

    base_metrics = {}
    for k in range(1, 6):
        bn, bd = bases[k - 1]
        base_metrics['b%d' % k] = dict(id='b%d' % k, cls='base', base='b%d' % k, num=bn, den=bd, tf='none')
    base_bat = {bid: battery(b) for bid, b in base_metrics.items()}
    say('基指标电池：%s' % {bid: {o: r['v'] for o, r in bb.items()} for bid, bb in base_bat.items()})

    anchor_m = dict(id='anchor_u_d800_rms', cls='anchor', base=None, num='u|d800|rms', den=None, tf='none')
    anchor_bat = battery(anchor_m)
    V5 = (anchor_bat['A1']['v'] == C.DEAD and anchor_bat['A9p']['v'] == C.DEAD)

    R = roster(bases, nb)
    ledger = []; N_ref_ok = True
    for m in R:
        prep(m)
        if m['tf'] == 'box' and not m.get('N_ref_consistent', False):
            N_ref_ok = False
        rec = dict(id=m['id'], cls=m['cls'], base=m['base'], formula=dict(num=m['num'], den=m['den'], tf=m['tf'],
                   c=m.get('c'), N_ref=m.get('N_ref'), scale=(SCALE if m['tf'] == 'scale' else None)))
        if 'duplicate_of' in m:
            rec.update(status='DUPLICATE', duplicate_of=m['duplicate_of']); ledger.append(rec); continue
        if contexts_equal(m, base_metrics[m['base']]):
            rec.update(status='EQUIVALENT'); ledger.append(rec); continue
        bat = battery(m); bb = base_bat[m['base']]
        verd = {o: bat[o]['v'] for o in OPS}; bverd = {o: bb[o]['v'] for o in OPS}
        judged = [o for o in OPS if verd[o] in (C.PASS, C.EDGE, C.DEAD)]
        kill_ops = [o for o in OPS if verd[o] == C.DEAD and bverd[o] != C.DEAD]
        dead_ops = [o for o in OPS if verd[o] == C.DEAD]
        if kill_ops:
            st = 'KILLED'
        elif len(judged) >= 3:
            st = 'ESCAPED'
        else:
            st = 'UNJUDGEABLE'
        if dead_ops:
            st_abs = 'DETECTED_ABS'
        elif len(judged) >= 3:
            st_abs = 'ESCAPED_ABS'
        else:
            st_abs = 'UNJUDGEABLE_ABS'
        rec.update(status=st, status_abs=st_abs, verdicts=verd, base_verdicts=bverd, judged_ops=judged,
                   kill_ops=kill_ops, dead_ops=dead_ops, n_judged=len(judged), battery=bat)
        ledger.append(rec)
    say('名册 %d：%s' % (len(ledger), {s: sum(1 for r in ledger if r['status'] == s) for s in ('KILLED', 'ESCAPED', 'UNJUDGEABLE', 'EQUIVALENT', 'DUPLICATE')}))

    classes = {}
    for cls in CLASSES:
        rs = [r for r in ledger if r['cls'] == cls]
        kil = [r['id'] for r in rs if r['status'] == 'KILLED']; esc = [r['id'] for r in rs if r['status'] == 'ESCAPED']
        unj = [r['id'] for r in rs if r['status'] == 'UNJUDGEABLE']
        exc = [r['id'] for r in rs if r['status'] in ('EQUIVALENT', 'DUPLICATE')]
        det_abs = [r['id'] for r in rs if r.get('status_abs') == 'DETECTED_ABS']
        esc_abs = [r['id'] for r in rs if r.get('status_abs') == 'ESCAPED_ABS']
        classes[cls] = dict(n_roster=len(rs), n_excluded=len(exc), excluded=exc, n_eval=len(rs) - len(exc),
                            killed=len(kil), escaped=len(esc), unjudgeable=len(unj), n_judgeable=len(kil) + len(esc),
                            killed_ids=kil, escaped_ids=esc, unjudgeable_ids=unj,
                            abs_detected=len(det_abs), abs_escaped=len(esc_abs), abs_detected_ids=det_abs, abs_escaped_ids=esc_abs)
    nk = sum(c['killed'] for c in classes.values()); nj = sum(c['n_judgeable'] for c in classes.values())
    nda = sum(c['abs_detected'] for c in classes.values()); nja = sum(c['abs_detected'] + c['abs_escaped'] for c in classes.values())
    n_roster = len(ledger)
    overall = dict(n_roster=n_roster, n_excluded=sum(c['n_excluded'] for c in classes.values()),
                   n_killed=nk, n_escaped=nj - nk, n_unjudgeable=sum(c['unjudgeable'] for c in classes.values()), n_judgeable=nj,
                   rate=(nk / nj if nj else None), wilson95=(list(C.wilson(nk, nj)) if nj else None),
                   raw_rate=nk / n_roster if n_roster else None, raw_wilson95=list(C.wilson(nk, n_roster)) if n_roster else None,
                   abs_rate=(nda / nja if nja else None), abs_wilson95=(list(C.wilson(nda, nja)) if nja else None), abs_n_detected=nda, abs_n_judgeable=nja)
    matrix = {r['id']: r.get('verdicts', r['status']) for r in ledger}
    pipeline = dict(impl_anchor_ok=(len(impl_mismatch) == 0) if orig_bq is not None else None,
                    impl_mismatch=impl_mismatch, read_fail=[list(k) for k in read_fail],
                    static_umax_match_E56_VERDICT=ST['umax_match_verdict'], N_ref_consistent=N_ref_ok,
                    base_names_from_front_sample=bases)
    km = dict(entry='audit_battery_meta/module2', when=C.now(), selftest=selftest, downgraded=down24,
              code_sha=C.code_sha(__file__), common_sha=C.code_sha(C.__file__),
              prereg_sha=None if selftest else C.sha256(C.PREREG),
              semantics=dict(primary='差分杀死：∃o v_mut=死 ∧ v_base≠死；漏网=未杀∧判定≥3；UNJUDGEABLE=未杀∧判定<3',
                             sensitivity='绝对检出：∃o v_mut=死'),
              operators=OPS, effective_note='A2 只判绝对型；5 把基指标全为比值型 → 对变异体电池有效 6 把',
              classes=classes, overall=overall, base_verdicts={b: {o: r['v'] for o, r in bb.items()} for b, bb in base_bat.items()},
              matrix=matrix, anchor_V5=dict(metric='u|d800|rms', verdicts={o: r['v'] for o, r in anchor_bat.items()}, ok=V5),
              pipeline=pipeline, wall_s=round(time.time() - t0, 1), log=log)
    ml = dict(entry='audit_battery_meta/module2_ledger', when=km['when'], selftest=selftest, downgraded=down24,
              code_sha=km['code_sha'], roster=ledger, base_battery=base_bat, anchor_battery=anchor_bat,
              maps=dict(wrong_region=REGION_MAP, wrong_layer=LAYER_MAP, irrelevant_num=IRR, unit_scale=SCALE),
              contexts={k: len(v) for k, v in ctx.items()})
    C.dump(ml, os.path.join(outdir, 'ABM_MUTANT_LEDGER.json'))
    C.dump(km, os.path.join(outdir, 'ABM_KILL_MATRIX.json'))
    print(json.dumps(dict(classes={c: (v['killed'], v['escaped'], v['unjudgeable'], v['n_excluded']) for c, v in classes.items()},
                          overall={k: overall[k] for k in ('n_killed', 'n_judgeable', 'rate', 'wilson95', 'abs_rate')},
                          V5=V5, pipeline={k: pipeline[k] for k in ('impl_anchor_ok', 'static_umax_match_E56_VERDICT', 'N_ref_consistent')},
                          wall_s=km['wall_s']), ensure_ascii=False, default=str))


if __name__ == '__main__':
    main()
