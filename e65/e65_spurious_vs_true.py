#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E65：「减伪流」与「保真流」在指标层面是不是同一件事。
预注册 sha 见 PREREG_E65.sha256。复用 e57_pareto 的候选构造，只加 D 与 G 两条轴。"""
import json, sys, time
import numpy as np
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts'); sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/e44')
from metric_search import base_quantities, spearman
ENV='/data/xinyuan/GOAI_ai4s_env'; t0=time.time()
def log(*a): print(*a,flush=True)

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
log('陡海山臂 %d 条，平底臂 %d 条，配对 %d 组'%(len(r26),len(flat),len(PAIRS)))

Q26,S26,QFL=[],[],[]
for i,rid in enumerate(r26):
    q=base_quantities(f'{ENV}/runs/{rid}')
    if q: Q26.append(q); S26.append(reg[rid])
    if i%20==0: log('  读陡臂 %d/%d  (%.0fs)'%(i,len(r26),time.time()-t0))
for i,rid in enumerate(flat):
    q=base_quantities(f'{ENV}/runs/{rid}')
    if q: QFL.append(q)
    if i%20==0: log('  读平底 %d/%d  (%.0fs)'%(i,len(flat),time.time()-t0))
keys=sorted(set.intersection(*[set(q) for q in Q26+QFL]))
M26=np.array([[q[k] for k in keys] for q in Q26]); MFL=np.array([[q[k] for k in keys] for q in QFL])
S=np.array(S26)
log('底量 %d 个，陡臂样本 %d，平底样本 %d'%(len(keys),M26.shape[0],MFL.shape[0]))

# 伪流幅度：用既有底量里的全域流速均方根，不新造统计量
SPUR_KEY=None
for cand in ('u|all|rms','v|all|rms','u|all|max'):
    if cand in keys: SPUR_KEY=cand; break
if SPUR_KEY is None:
    SPUR_KEY=[k for k in keys if k.startswith('u|') and k.endswith('|rms')][0]
spur=M26[:,keys.index(SPUR_KEY)]
log('伪流幅度取用底量: %s'%SPUR_KEY)

P26L,PFLL=[],[]
for a,b in PAIRS:
    qa,qb=base_quantities(f'{ENV}/runs/{a}'),base_quantities(f'{ENV}/runs/{b}')
    if qa and qb and all(k in qa and k in qb for k in keys):
        P26L.append([qa[k] for k in keys]); PFLL.append([qb[k] for k in keys])
P26,PFL=np.array(P26L),np.array(PFLL); EPS=1e-12
log('配对读齐 %d 组  (%.0fs)'%(len(P26L),time.time()-t0))

A=[];B=[];D=[];Gs=[];NAME=[]
for i,kn in enumerate(keys):
    cand=[(kn,None,M26[:,i],MFL[:,i],P26[:,i],PFL[:,i],1)]   # G=1 绝对量
    for j,kd in enumerate(keys):
        if i==j: continue
        if np.any(np.abs(M26[:,j])<EPS) or np.any(np.abs(MFL[:,j])<EPS) or np.any(np.abs(P26[:,j])<EPS) or np.any(np.abs(PFL[:,j])<EPS): continue
        cand.append((kn,kd,M26[:,i]/M26[:,j],MFL[:,i]/MFL[:,j],P26[:,i]/P26[:,j],PFL[:,i]/PFL[:,j],0))  # G=0 比值
    for kn_,kd_,v26,vfl,p26,pfl,g in cand:
        if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
        if np.any(v26<=0) or np.any(vfl<=0): continue
        A.append(-spearman(v26,S)); B.append(float((pfl>=p26).mean()) if len(p26) else 0.0)
        D.append(spearman(v26,spur)); Gs.append(g); NAME.append((kn_,kd_))
A=np.array(A);B=np.array(B);D=np.array(D);Gs=np.array(Gs)
log('候选 %d 个  (%.0fs)'%(len(A),time.time()-t0))

def perm_p(x,y,n=2000,seed=0):
    rng=np.random.default_rng(seed); obs=spearman(x,y); cnt=0
    yy=y.copy()
    for _ in range(n):
        rng.shuffle(yy)
        if abs(spearman(x,yy))>=abs(obs): cnt+=1
    return float((cnt+1)/(n+1))

rDA=spearman(D,A); rDB=spearman(D,B); rAB=spearman(A,B)
both=(A>=0.7)&(B>=0.9)
res=dict(
 prereg_sha=open(f'{ENV}/e65/PREREG_E65.sha256').read().strip(),
 spurious_key=SPUR_KEY, n_candidates=int(len(A)), n_runs_steep=int(M26.shape[0]), n_pairs=int(len(P26L)),
 spearman_D_A=round(float(rDA),4), spearman_D_B=round(float(rDB),4), spearman_A_B=round(float(rAB),4),
 p_D_A=perm_p(D,A), p_D_B=perm_p(D,B),
 n_ratio=int((Gs==0).sum()), n_absolute=int((Gs==1).sum()),
 B_mean_absolute=round(float(B[Gs==1].mean()),4), B_mean_ratio=round(float(B[Gs==0].mean()),4),
 A_mean_absolute=round(float(A[Gs==1].mean()),4), A_mean_ratio=round(float(A[Gs==0].mean()),4),
 n_both=int(both.sum()),
 D_mean_all=round(float(D.mean()),4), D_mean_both=round(float(D[both].mean()),4) if both.sum() else None,
 D_median_all=round(float(np.median(D)),4), D_median_both=round(float(np.median(D[both])),4) if both.sum() else None,
)
res['prereg_check']={
 'P1 rho(D,A)<0': bool(rDA<0),
 'P2 rho(D,B)>0': bool(rDB>0),
 'P3 绝对量的 B 低于比值型': bool(res['B_mean_absolute']<res['B_mean_ratio']),
 'P4 两关同过的 D 低于全体': (bool(res['D_mean_both']<res['D_mean_all']) if both.sum() else None),
}
res['elapsed_s']=round(time.time()-t0,1)
np.savez(f'{ENV}/e65/E65_AXES.npz',A=A,B=B,D=D,G=Gs)
json.dump(res,open(f'{ENV}/e65/E65_SPURIOUS_VS_TRUE.json','w'),indent=1,ensure_ascii=False)
log('')
log('ρ(D,A) = %+.4f  (p=%.4f)   ← P1 预测为负'%(rDA,res['p_D_A']))
log('ρ(D,B) = %+.4f  (p=%.4f)   ← P2 预测为正'%(rDB,res['p_D_B']))
log('ρ(A,B) = %+.4f   （E57 已知 −0.674，作一致性核对）'%rAB)
log('绝对量 %d 个 B 均值 %.3f ；比值型 %d 个 B 均值 %.3f  ← P3'%(res['n_absolute'],res['B_mean_absolute'],res['n_ratio'],res['B_mean_ratio']))
log('两关同过 %d 个，D 均值 %.3f 对全体 %.3f  ← P4'%(res['n_both'],res['D_mean_both'] or -9,res['D_mean_all']))
log('预注册核对: '+'；'.join('%s=%s'%(k,'命中' if v else ('未命中' if v is not None else 'NA')) for k,v in res['prereg_check'].items()))
log('E65_DONE  %.0f 秒'%(time.time()-t0))
