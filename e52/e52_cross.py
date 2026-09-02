#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E52 三重交集: 纬向风(E40) ∩ 经向风(E52, 同判据) ∩ 内潮(E48 三轴报警)。
风侧判据函数逐字复用 e49_cross.py 的实现(base_quantities/spearman 来自 scripts/metric_search.py)。"""
import json, sys, itertools
import numpy as np
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts'); sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/e44')
from metric_search import base_quantities, spearman
ENV='/data/xinyuan/GOAI_ai4s_env'
def wind_passlist(ledger, runsdir, reg_from):
    reg={}
    if reg_from=='regraded':
        for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
            r=json.loads(l); reg[r['run_id']]=r['skill_vs_zero']
    seen={}; byp={}
    for l in open(ledger):
        r=json.loads(l)
        if not (r['obs'].get('valid') and r['ntimes']==8640): continue
        seen[r['run_id']]=r['bathy']
        if reg_from=='hidden' and r['bathy']=='r26steep' and (r.get('hidden') or {}).get('skill_vs_zero') is not None:
            reg[r['run_id']]=r['hidden']['skill_vs_zero']
        a=r['action']; k=tuple(round(a.get(x,-1),6) for x in ('VISC2','VISC4','AKV_BAK','TNU2'))
        byp.setdefault(k,{})[r['bathy']]=r['run_id']
    r26=[k for k,v in seen.items() if v=='r26steep' and k in reg]; flat=[k for k,v in seen.items() if v=='flat']
    PAIRS=[(v['r26steep'],v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
    Q26,S26,QFL=[],[],[]
    for rid in r26:
        q=base_quantities(f'{runsdir}/{rid}')
        if q: Q26.append(q); S26.append(reg[rid])
    for rid in flat:
        q=base_quantities(f'{runsdir}/{rid}')
        if q: QFL.append(q)
    keys=sorted(set.intersection(*[set(q) for q in Q26+QFL]))
    M26=np.array([[q[k] for k in keys] for q in Q26]); MFL=np.array([[q[k] for k in keys] for q in QFL]); S=np.array(S26)
    P26L,PFLL=[],[]
    for a,b in PAIRS:
        qa,qb=base_quantities(f'{runsdir}/{a}'),base_quantities(f'{runsdir}/{b}')
        if qa and qb and all(k in qa and k in qb for k in keys):
            P26L.append([qa[k] for k in keys]); PFLL.append([qb[k] for k in keys])
    P26,PFL=np.array(P26L),np.array(PFLL); EPS=1e-12; out={}
    for i,kn in enumerate(keys):
        cand=[(kn,None,M26[:,i],MFL[:,i],P26[:,i],PFL[:,i])]
        for j,kd in enumerate(keys):
            if i==j: continue
            if np.any(np.abs(M26[:,j])<EPS) or np.any(np.abs(MFL[:,j])<EPS) or np.any(np.abs(P26[:,j])<EPS) or np.any(np.abs(PFL[:,j])<EPS): continue
            cand.append((kn,kd,M26[:,i]/M26[:,j],MFL[:,i]/MFL[:,j],P26[:,i]/P26[:,j],PFL[:,i]/PFL[:,j]))
        for kn_,kd_,v26,vfl,p26,pfl in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
            if np.any(v26<=0) or np.any(vfl<=0): continue
            rho=spearman(v26,S); paired=float((pfl>=p26).mean()) if len(p26) else 0.0
            out[(kn_,kd_)]=dict(rho=round(float(rho),4),paired=round(paired,4),passAB=bool(rho<=-0.7 and paired>=0.9))
    print('  n26=%d nflat=%d pairs=%d cand=%d passAB=%d'%(len(Q26),len(QFL),len(P26),len(out),sum(v['passAB'] for v in out.values())),flush=True)
    return out
print('zonal...',flush=True); Z=wind_passlist(f'{ENV}/ledger/env2_runs.jsonl',f'{ENV}/runs','regraded')
print('merid...',flush=True); Mr=wind_passlist(f'{ENV}/ledger/env2_merid_runs.jsonl',f'{ENV}/runs_merid','hidden')
# tide alarm list (E48 逻辑)
import e48_search as T
B={}
for t in sorted(set(t for ax in T.AXES.values() for t,_ in ax)):
    d=T.PF+t if t.startswith('pf_') else T.E44+'cases/'+t
    B[t]=T.base_quantities(d)
tk=sorted(set.intersection(*[set(v) for v in B.values()])); Td={}
for kn,kd in [(k,None) for k in tk]+[(a,b) for a,b in itertools.product(tk,tk) if a!=b]:
    rr={}; ok=True
    for ax,pts in T.AXES.items():
        vals=[]
        for t,x in pts:
            den=B[t][kd] if kd else 1.0
            if kd and abs(den)<1e-12: ok=False; break
            vals.append(B[t][kn]/den)
        if not ok: break
        rr[ax]=T.spearman([x for _,x in pts],vals)
    if not ok: continue
    sg=[np.sign(rr[a]) for a in ('m','visc','gam')]; same=(sg[0]!=0 and sg[0]==sg[1]==sg[2]); amin=min(abs(rr[a]) for a in ('m','visc','gam'))
    Td[(kn,kd)]=bool(same and sg[0]>0 and amin>=0.85)
uv=('u|all|rms','v|all|mean_abs'); vu=('v|all|rms','u|all|mean_abs')
zp={k for k,v in Z.items() if v['passAB']}; mp={k for k,v in Mr.items() if v['passAB']}; tp={k for k,v in Td.items() if v}
zm=zp&mp; zt=zp&tp; mt=mp&tp; zmt=zp&mp&tp
def fam(s):
    from collections import Counter
    return Counter((k[0].split('|')[0], (k[1] or '-').split('|')[0]) for k in s).most_common(8)
res=dict(zonal_pass=len(zp),merid_pass=len(mp),tide_alarm=len(tp),
  uv_zonal=Z.get(uv),uv_merid=Mr.get(uv),uv_tide=Td.get(uv),
  vu_zonal=Z.get(vu),vu_merid=Mr.get(vu),vu_tide=Td.get(vu),
  inter_zonal_merid=len(zm),inter_zonal_tide=len(zt),inter_merid_tide=len(mt),inter_triple=len(zmt),
  triple_list=[dict(num=k[0],den=k[1],zonal=Z[k],merid=Mr[k]) for k in sorted(zmt,key=lambda k:(Z[k]['rho']+Mr[k]['rho']))][:40],
  family_zonal_merid=fam(zm),family_triple=fam(zmt),family_merid=fam(mp))
json.dump(res,open('/data/xinyuan/GOAI_ai4s_env/e52/E52_CROSS.json','w'),indent=1,default=str)
print('zonal %d | merid %d | tide %d'%(len(zp),len(mp),len(tp)))
print('uv: zonal',Z.get(uv),' merid',Mr.get(uv),' tide',Td.get(uv))
print('vu: zonal',Z.get(vu),' merid',Mr.get(vu),' tide',Td.get(vu))
print('zonal∩merid=%d  zonal∩tide=%d  merid∩tide=%d  TRIPLE=%d'%(len(zm),len(zt),len(mt),len(zmt)))
print('family zonal∩merid:',fam(zm)); print('family triple:',fam(zmt))
for r in res['triple_list'][:15]: print('  ',r['num'],'/',r['den'],r['zonal'],r['merid'])
