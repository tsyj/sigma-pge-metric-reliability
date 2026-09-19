#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E67：E66 的配方选出的尺子，换强迫方向还站得住吗。预注册 sha 见 PREREG_E67b.sha256。"""
import json, sys, time
import numpy as np
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts'); sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/e44')
from metric_search import base_quantities, spearman
ENV='/data/xinyuan/GOAI_ai4s_env'; t0=time.time()
def log(*a): print(*a,flush=True)
def rank(x):
    o=np.argsort(np.argsort(x,kind='mergesort'),kind='mergesort').astype(float)
    return (o-o.mean())/(o.std()+1e-12)

def axes(ledger, runsdir, reg_from, want_perp):
    """返回 {(num,den): dict(A,B,D,AP,G)}"""
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
    r26=[k for k,v in seen.items() if v=='r26steep' and k in reg]
    flat=[k for k,v in seen.items() if v=='flat']
    PAIRS=[(v['r26steep'],v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
    Q26,S26,QFL=[],[],[]
    for rid in r26:
        q=base_quantities(f'{runsdir}/{rid}')
        if q: Q26.append(q); S26.append(reg[rid])
    for rid in flat:
        q=base_quantities(f'{runsdir}/{rid}')
        if q: QFL.append(q)
    if not Q26 or not QFL: return {}
    keys=sorted(set.intersection(*[set(q) for q in Q26+QFL]))
    M26=np.array([[q[k] for k in keys] for q in Q26]); MFL=np.array([[q[k] for k in keys] for q in QFL]); S=np.array(S26)
    SP='u|all|rms'; spur=M26[:,keys.index(SP)] if SP in keys else M26[:,0]
    P26L,PFLL=[],[]
    for a,b in PAIRS:
        qa,qb=base_quantities(f'{runsdir}/{a}'),base_quantities(f'{runsdir}/{b}')
        if qa and qb and all(k in qa and k in qb for k in keys):
            P26L.append([qa[k] for k in keys]); PFLL.append([qb[k] for k in keys])
    P26,PFL=np.array(P26L),np.array(PFLL); EPS=1e-12
    rs=rank(spur); rS=rank(S); S_res=rS-(rS@rs)/(rs@rs)*rs
    out={}
    for i,kn in enumerate(keys):
        cand=[(kn,None,M26[:,i],MFL[:,i],P26[:,i],PFL[:,i],1)]
        for j,kd in enumerate(keys):
            if i==j: continue
            if np.any(np.abs(M26[:,j])<EPS) or np.any(np.abs(MFL[:,j])<EPS) or np.any(np.abs(P26[:,j])<EPS) or np.any(np.abs(PFL[:,j])<EPS): continue
            cand.append((kn,kd,M26[:,i]/M26[:,j],MFL[:,i]/MFL[:,j],P26[:,i]/P26[:,j],PFL[:,i]/PFL[:,j],0))
        for kn_,kd_,v26,vfl,p26,pfl,g in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
            if np.any(v26<=0) or np.any(vfl<=0): continue
            A=-spearman(v26,S); B=float((pfl>=p26).mean()) if len(p26) else 0.0
            d=dict(A=A,B=B,G=g)
            if want_perp:
                rv=rank(v26); v_res=rv-(rv@rs)/(rs@rs)*rs
                d['AP']=-float(np.corrcoef(v_res,S_res)[0,1]) if v_res.std()>1e-9 else 0.0
                d['D']=spearman(v26,spur)
            out[(kn_,kd_)]=d
    return out

log('纬向…');  Z =axes(f'{ENV}/ledger/env2_runs.jsonl',        f'{ENV}/runs',        'regraded', True)
log('  %d 个候选  (%.0fs)'%(len(Z),time.time()-t0))
log('经向…');  Mr=axes(f'{ENV}/ledger/env2_merid_runs.jsonl',  f'{ENV}/runs_merid',  'hidden',  True)
log('  %d 个候选  (%.0fs)'%(len(Mr),time.time()-t0))
log('45°…');   D4=axes(f'{ENV}/ledger/env2_diag45_runs.jsonl', f'{ENV}/runs_diag45', 'hidden',  True)
log('  %d 个候选  (%.0fs)'%(len(D4),time.time()-t0))

S_A  ={k for k,v in Z.items() if v['A'] >=0.7 and v['B']>=0.9}
S_AP ={k for k,v in Z.items() if v['AP']>=0.7 and v['B']>=0.9}
def passes(T,k,key='A'):
    v=T.get(k); return bool(v and v.get(key) is not None and v[key]>=0.7 and v['B']>=0.9)
def rate(T,S,key='A'):
    if not S: return None,0
    n=sum(1 for k in S if passes(T,k,key)); return n/len(S), n
def base_rate(T,key='A'):
    if not T: return 0.0
    return sum(1 for v in T.values() if v.get(key) is not None and v[key]>=0.7 and v['B']>=0.9)/len(T)

res=dict(prereg_sha=open(f'{ENV}/e67/PREREG_E67b.sha256').read().strip(),
         n_zonal=len(Z), n_merid=len(Mr), n_diag45=len(D4),
         size_S_A=len(S_A), size_S_AP=len(S_AP))
for tag,T in (('merid',Mr),('diag45',D4)):
    br=base_rate(T,'A'); brP=base_rate(T,'AP')
    rA,nA=rate(T,S_A,'A'); rP,nP=rate(T,S_AP,'AP')
    res[tag]=dict(base_rate=round(br,4), base_rate_perp=round(brP,4),
      S_A=dict(n=nA, rate=round(rA,4) if rA is not None else None,
               expect=round(br*len(S_A),1), enrich=round(nA/(br*len(S_A)),2) if br*len(S_A)>0 else None),
      S_AP=dict(n=nP, rate=round(rP,4) if rP is not None else None,
               expect=round(brP*len(S_AP),1), enrich=round(nP/(brP*len(S_AP)),2) if brP*len(S_AP)>0 else None))
tri_A =[k for k in S_A  if passes(Mr,k,'A') and passes(D4,k,'A')]
tri_AP=[k for k in S_AP if passes(Mr,k,'AP') and passes(D4,k,'AP')]
res['triple']=dict(S_A=len(tri_A), S_AP=len(tri_AP))
surv=[k for k in S_AP if passes(Mr,k,'AP')]
res['merid_survivors_all_ratio']=bool(all(Z[k]['G']==0 for k in surv)) if surv else None
res['merid_survivors_abs']=int(sum(1 for k in surv if Z[k]['G']==1))
if tri_AP:
    res['triple_sample']=[dict(num=k[0],den=k[1],A=round(Z[k]['A'],3),AP=round(Z[k]['AP'],3),B=round(Z[k]['B'],3)) for k in tri_AP[:12]]
rA=res['merid']['S_A']['rate']; rP=res['merid']['S_AP']['rate']
res['prereg_check']={
 'Q1 S_A⊥ 跨向存活率 > S_A': (bool(rP>rA) if (rA is not None and rP is not None) else None),
 'Q2 两集合富集均 ≥2 倍': bool((res['merid']['S_A']['enrich'] or 0)>=2 and (res['merid']['S_AP']['enrich'] or 0)>=2),
 'Q3 S_A⊥ 三向交集 > 0': bool(len(tri_AP)>0),
 'Q4 存活者全为比值型': res['merid_survivors_all_ratio'],
}
res['elapsed_s']=round(time.time()-t0,1)
json.dump(res,open(f'{ENV}/e67/E67B_RECIPE_TRANSFER.json','w'),indent=1,ensure_ascii=False)
log('')
log('纬向选定：原口径 S_A = %d 把 ；新配方 S_A⊥ = %d 把'%(len(S_A),len(S_AP)))
for tag in ('merid','diag45'):
    r=res[tag]
    log('%-7s 底率 %.4f | S_A 存活 %d/%d = %.1f%%（期望 %.1f，富集 %sx）| S_A⊥ 存活 %d/%d = %.1f%%（期望 %.1f，富集 %sx）'%(
        tag, r['base_rate'],
        r['S_A']['n'],len(S_A),(r['S_A']['rate'] or 0)*100, r['S_A']['expect'], r['S_A']['enrich'],
        r['S_AP']['n'],len(S_AP),(r['S_AP']['rate'] or 0)*100, r['S_AP']['expect'], r['S_AP']['enrich']))
log('三向同时站得住：原口径 %d 把 ；新配方 %d 把'%(len(tri_A),len(tri_AP)))
log('预注册核对: '+'；'.join('%s=%s'%(k,'命中' if v else ('未命中' if v is not None else 'NA')) for k,v in res['prereg_check'].items()))
log('E67_DONE  %.0f 秒'%(time.time()-t0))
