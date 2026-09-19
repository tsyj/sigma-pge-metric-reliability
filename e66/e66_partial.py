#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E66：扣掉伪流代理之后，还有没有尺子既排得准又抗糊弄。"""
import json, sys, time
import numpy as np
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts'); sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/e44')
from metric_search import base_quantities, spearman
ENV='/data/xinyuan/GOAI_ai4s_env'; t0=time.time()
def log(*a): print(*a,flush=True)
def rank(x):
    o=np.argsort(np.argsort(x,kind='mergesort'),kind='mergesort').astype(float)
    return (o-o.mean())/(o.std()+1e-12)

reg={}
for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
    r=json.loads(l); reg[r['run_id']]=r['skill_vs_zero']
seen={}; byp={}
for l in open(f'{ENV}/ledger/env2_runs.jsonl'):
    r=json.loads(l)
    if not (r['obs'].get('valid') and r['ntimes']==8640): continue
    seen[r['run_id']]=r['bathy']
    a=r['action']; k=tuple(round(a.get(x,-1),6) for x in ('VISC2','VISC4','AKV_BAK','TNU2'))
    byp.setdefault(k,{})[r['bathy']]=r['run_id']
r26=[k for k,v in seen.items() if v=='r26steep' and k in reg]
flat=[k for k,v in seen.items() if v=='flat']
PAIRS=[(v['r26steep'],v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
Q26,S26,QFL=[],[],[]
for rid in r26:
    q=base_quantities(f'{ENV}/runs/{rid}')
    if q: Q26.append(q); S26.append(reg[rid])
for rid in flat:
    q=base_quantities(f'{ENV}/runs/{rid}')
    if q: QFL.append(q)
keys=sorted(set.intersection(*[set(q) for q in Q26+QFL]))
M26=np.array([[q[k] for k in keys] for q in Q26]); MFL=np.array([[q[k] for k in keys] for q in QFL])
S=np.array(S26); SPUR='u|all|rms'; spur=M26[:,keys.index(SPUR)]
P26L,PFLL=[],[]
for a,b in PAIRS:
    qa,qb=base_quantities(f'{ENV}/runs/{a}'),base_quantities(f'{ENV}/runs/{b}')
    if qa and qb and all(k in qa and k in qb for k in keys):
        P26L.append([qa[k] for k in keys]); PFLL.append([qb[k] for k in keys])
P26,PFL=np.array(P26L),np.array(PFLL); EPS=1e-12
log('读齐  陡臂 %d  平底 %d  配对 %d  (%.0fs)'%(M26.shape[0],MFL.shape[0],len(P26L),time.time()-t0))

rs=rank(spur); rS=rank(S)
S_res=rS-(rS@rs)/(rs@rs)*rs          # 技巧评分扣掉伪流成分后的残差
A=[];B=[];D=[];AP=[];Gs=[];NAME=[]
for i,kn in enumerate(keys):
    cand=[(kn,None,M26[:,i],MFL[:,i],P26[:,i],PFL[:,i],1)]
    for j,kd in enumerate(keys):
        if i==j: continue
        if np.any(np.abs(M26[:,j])<EPS) or np.any(np.abs(MFL[:,j])<EPS) or np.any(np.abs(P26[:,j])<EPS) or np.any(np.abs(PFL[:,j])<EPS): continue
        cand.append((kn,kd,M26[:,i]/M26[:,j],MFL[:,i]/MFL[:,j],P26[:,i]/P26[:,j],PFL[:,i]/PFL[:,j],0))
    for kn_,kd_,v26,vfl,p26,pfl,g in cand:
        if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
        if np.any(v26<=0) or np.any(vfl<=0): continue
        rv=rank(v26); v_res=rv-(rv@rs)/(rs@rs)*rs
        ap=-float(np.corrcoef(v_res,S_res)[0,1]) if v_res.std()>1e-9 else 0.0
        A.append(-spearman(v26,S)); B.append(float((pfl>=p26).mean()) if len(p26) else 0.0)
        D.append(spearman(v26,spur)); AP.append(ap); Gs.append(g); NAME.append((kn_,kd_))
A=np.array(A);B=np.array(B);D=np.array(D);AP=np.array(AP);Gs=np.array(Gs)
log('候选 %d  (%.0fs)'%(len(A),time.time()-t0))

both65=(A>=0.7)&(B>=0.9)
win=(AP>=0.7)&(B>=0.9)
res=dict(prereg_sha=open(f'{ENV}/e66/PREREG_E66.sha256').read().strip(),
 n_candidates=int(len(A)), spurious_key=SPUR,
 A_median=round(float(np.median(A)),4), Aperp_median=round(float(np.median(AP)),4),
 A_max=round(float(A.max()),4), Aperp_max=round(float(AP.max()),4),
 frac_A_ge_0p7=round(float((A>=0.7).mean()),4), frac_Aperp_ge_0p7=round(float((AP>=0.7).mean()),4),
 n_both_A=int(both65.sum()), n_both_Aperp=int(win.sum()),
 Aperp_median_in_both65=round(float(np.median(AP[both65])),4) if both65.sum() else None,
 winners_all_ratio=(bool((Gs[win]==0).all()) if win.sum() else None),
 n_winners_ratio=int((Gs[win]==0).sum()), n_winners_abs=int((Gs[win]==1).sum()),
 spearman_A_Aperp=round(float(spearman(A,AP)),4),
 spearman_Aperp_B=round(float(spearman(AP,B)),4),
 spearman_Aperp_D=round(float(spearman(AP,D)),4),
)
if win.sum():
    idx=np.argsort(-(AP[win]+B[win])); w=np.where(win)[0][idx][:12]
    res['winners_top']=[dict(num=NAME[i][0],den=NAME[i][1],A=round(float(A[i]),3),
                             Aperp=round(float(AP[i]),3),B=round(float(B[i]),3),D=round(float(D[i]),3)) for i in w]
res['prereg_check']={
 'P1 A⊥中位数 < A中位数': bool(res['Aperp_median']<res['A_median']),
 'P2 A⊥≥0.7 且 B≥0.9 的候选 < 20': bool(win.sum()<20),
 'P3 204 个同过者的 A⊥ 中位数 < 0.3': (bool(res['Aperp_median_in_both65']<0.3) if both65.sum() else None),
 'P4 胜出者全为比值型': res['winners_all_ratio'],
}
res['elapsed_s']=round(time.time()-t0,1)
np.savez(f'{ENV}/e66/E66_AXES.npz',A=A,B=B,D=D,AP=AP,G=Gs)
json.dump(res,open(f'{ENV}/e66/E66_PARTIAL.json','w'),indent=1,ensure_ascii=False)
log('')
log('A   中位数 %+.4f  最大 %+.4f   P(A≥0.7)=%.4f'%(res['A_median'],res['A_max'],res['frac_A_ge_0p7']))
log('A⊥  中位数 %+.4f  最大 %+.4f   P(A⊥≥0.7)=%.4f   ← 扣掉伪流代理之后'%(res['Aperp_median'],res['Aperp_max'],res['frac_Aperp_ge_0p7']))
log('两关同过：原口径 %d 个 → 扣掉伪流代理后 %d 个'%(res['n_both_A'],res['n_both_Aperp']))
log('ρ(A⊥,B) = %+.4f    ρ(A⊥,D) = %+.4f'%(res['spearman_Aperp_B'],res['spearman_Aperp_D']))
log('预注册核对: '+'；'.join('%s=%s'%(k,'命中' if v else ('未命中' if v is not None else 'NA')) for k,v in res['prereg_check'].items()))
log('E66_DONE  %.0f 秒'%(time.time()-t0))
