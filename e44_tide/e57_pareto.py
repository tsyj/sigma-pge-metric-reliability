#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E57: 全候选空间的 (排序力 A, 抗刷率 B) 双目标分析
A = -rho(候选, 隐藏技巧评分)  越高越好；B = 同参数配对抗刷率  越高越好
问三件事: (1) A 与 B 是否负相关 -> "不可兼得"能否成立; (2) Pareto 前沿与乌托邦角是否为空; (3) 阈值敏感性
复用 e49_cross.py 的 wind_passlist 全量计算（含每个候选的 rho/paired）。"""
import json, sys, itertools
import numpy as np
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts'); sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/e44')
from metric_search import base_quantities, spearman
# --- 可移植性垫片：开发机行为不变；换台机器时自动改用仓库内的文件 ---
import os as _o, sys as _s
_H=_o.path.dirname(_o.path.abspath(__file__))
_R=_H if _o.path.isdir(_o.path.join(_H,'e44_tide')) else _o.path.dirname(_H)
for _d in (_o.path.join(_R,'scripts'), _o.path.join(_R,'e44_tide'), _R):
    if _o.path.isdir(_d) and _d not in _s.path: _s.path.insert(0,_d)
if not _o.path.isdir('/data/xinyuan/GOAI_ai4s_env'):
    # 评委机器：把开发路径重定向到仓库内
    _real_open=open
    def open(f,*a,**k):
        if isinstance(f,str) and f.startswith('/data/xinyuan/GOAI_ai4s_env/'):
            rel=f.replace('/data/xinyuan/GOAI_ai4s_env/','')
            for _b in (_R, _o.path.join(_R,'e44_tide')):
                _p=_o.path.join(_b,rel)
                if _o.path.exists(_p): return _real_open(_p,*a,**k)
                _p2=_o.path.join(_b,_o.path.basename(rel))
                if _o.path.exists(_p2): return _real_open(_p2,*a,**k)
        return _real_open(f,*a,**k)
# --- 垫片结束 ---

ENV='/data/xinyuan/GOAI_ai4s_env'
def wind_AB(ledger, runsdir, reg_from):
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
    P26,PFL=np.array(P26L),np.array(PFLL); EPS=1e-12; rows=[]
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
            rows.append((kn_,kd_,-rho,paired))   # A=-rho
    return rows, len(P26)
print('zonal...',flush=True); Z,nz=wind_AB(f'{ENV}/ledger/env2_runs.jsonl',f'{ENV}/runs','regraded')
print('  %d candidates, %d pairs'%(len(Z),nz),flush=True)
A=np.array([r[2] for r in Z]); B=np.array([r[3] for r in Z])
rAB=spearman(A,B); rAB_p=spearman(np.abs(A),B)
# Pareto 前沿(最大化 A 与 B)
idx=np.lexsort((-B,-A)); front=[]; bmax=-np.inf
for i in idx:
    if B[i]>bmax: front.append(i); bmax=B[i]
front=np.array(front)
util=np.hypot(1-np.clip(A,None,1), 1-B)     # 到乌托邦角 (1,1) 的距离
knee=int(np.argmin(util))
# 阈值敏感性
grid={}
for ta in (0.5,0.6,0.7,0.8,0.9):
    for tb in (0.7,0.8,0.85,0.9,0.95,1.0):
        grid['%.2f/%.2f'%(ta,tb)]=int(((A>=ta)&(B>=tb)).sum())
res=dict(n_candidates=len(Z), n_pairs=nz,
  spearman_A_B=round(rAB,4), spearman_absA_B=round(rAB_p,4),
  frac_A_ge_0p7=float((A>=0.7).mean()), frac_B_ge_0p9=float((B>=0.9).mean()),
  frac_both=float(((A>=0.7)&(B>=0.9)).mean()), n_both=int(((A>=0.7)&(B>=0.9)).sum()),
  independent_expect=float((A>=0.7).mean()*(B>=0.9).mean()*len(Z)),
  utopia_occupied=bool(((A>=0.999)&(B>=0.999)).any()),
  max_A=float(A.max()), max_B=float(B.max()), n_front=len(front),
  knee=dict(num=Z[knee][0],den=Z[knee][1],A=round(float(A[knee]),4),B=round(float(B[knee]),4)),
  best_A_arm=dict(num=Z[int(np.argmax(A))][0],den=Z[int(np.argmax(A))][1],A=round(float(A.max()),4),B=round(float(B[int(np.argmax(A))]),4)),
  threshold_grid=grid,
  front_sample=[dict(num=Z[i][0],den=Z[i][1],A=round(float(A[i]),4),B=round(float(B[i]),4)) for i in front[:25]])
np.savez(ENV+'/e44/analysis/E57_AB.npz',A=A,B=B,front=front)
json.dump(res,open(ENV+'/e44/analysis/E57_PARETO.json','w'),indent=1,ensure_ascii=False)
print()
print('A~B Spearman = %+.4f   (|A|~B = %+.4f)'%(rAB,rAB_p))
print('P(A>=0.7)=%.4f  P(B>=0.9)=%.4f  联合=%.5f (%d 个)  独立期望=%.1f 个'%(
    res['frac_A_ge_0p7'],res['frac_B_ge_0p9'],res['frac_both'],res['n_both'],res['independent_expect']))
print('乌托邦角(1,1)是否被占: %s   max A=%.3f  max B=%.3f  前沿点数=%d'%(res['utopia_occupied'],A.max(),B.max(),len(front)))
print('knee(最佳折中): %s / %s  A=%.3f B=%.3f'%(res['knee']['num'],res['knee']['den'],res['knee']['A'],res['knee']['B']))
print('阈值敏感性(A>=x, B>=y 的通过数):')
for k in sorted(grid): print('   %s -> %d'%(k,grid[k]))
