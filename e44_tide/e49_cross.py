#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E49 -- 跨环境交集: 风驱 E40 判据(A: rho<=-0.7 vs 隐藏技巧评分; B: 配对抗刷分>=0.9)
的完整通过名单 x 内潮 E48 三轴报警名单。
风驱侧逻辑逐字复用 scripts/metric_search.py(base_quantities/spearman/判据), 仅新增全名单导出。
"""
import json, sys, os
import numpy as np
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
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
LEDGER=f'{ENV}/ledger/env2_runs.jsonl'
reg={}
for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
    r=json.loads(l); reg[r['run_id']]=r['skill_vs_zero']
seen={}
for l in open(LEDGER):
    r=json.loads(l)
    if r['obs'].get('valid') and r['ntimes']==8640: seen[r['run_id']]=r['bathy']
r26=[(k,v) for k,v in seen.items() if v=='r26steep' and k in reg]
flat=[(k,v) for k,v in seen.items() if v=='flat']
byp={}
for l in open(LEDGER):
    r=json.loads(l)
    if not (r['obs'].get('valid') and r['ntimes']==8640): continue
    a=r['action']; k=tuple(round(a.get(x,-1),6) for x in ('VISC2','VISC4','AKV_BAK','TNU2'))
    byp.setdefault(k,{})[r['bathy']]=r['run_id']
PAIRS=[(v['r26steep'],v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
Q26,S26,QFL=[],[],[]
for rid,_ in r26:
    q=base_quantities(f'{ENV}/runs/{rid}')
    if q: Q26.append(q); S26.append(reg[rid])
for rid,_ in flat:
    q=base_quantities(f'{ENV}/runs/{rid}')
    if q: QFL.append(q)
keys=sorted(set.intersection(*[set(q) for q in Q26+QFL]))
print('base keys %d, r26 %d, flat %d, pairs %d'%(len(keys),len(Q26),len(QFL),len(PAIRS)),flush=True)
M26=np.array([[q[k] for k in keys] for q in Q26]); MFL=np.array([[q[k] for k in keys] for q in QFL])
S=np.array(S26)
P26L,PFLL=[],[]
for a,b in PAIRS:
    qa,qb=base_quantities(f'{ENV}/runs/{a}'),base_quantities(f'{ENV}/runs/{b}')
    if qa and qb and all(k in qa and k in qb for k in keys):
        P26L.append([qa[k] for k in keys]); PFLL.append([qb[k] for k in keys])
P26,PFL=np.array(P26L),np.array(PFLL)
EPS=1e-12; wind={}
for i,kn in enumerate(keys):
    cand=[(kn,None,M26[:,i],MFL[:,i],P26[:,i],PFL[:,i])]
    for j,kd in enumerate(keys):
        if i==j: continue
        if np.any(np.abs(M26[:,j])<EPS) or np.any(np.abs(MFL[:,j])<EPS): continue
        if np.any(np.abs(P26[:,j])<EPS) or np.any(np.abs(PFL[:,j])<EPS): continue
        cand.append((kn,kd,M26[:,i]/M26[:,j],MFL[:,i]/MFL[:,j],P26[:,i]/P26[:,j],PFL[:,i]/PFL[:,j]))
    for kn_,kd_,v26,vfl,p26,pfl in cand:
        if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
        if np.any(v26<=0) or np.any(vfl<=0): continue
        rho=spearman(v26,S)
        paired=float((pfl>=p26).mean()) if len(p26) else 0.0
        wind[(kn_,kd_)]=dict(rho=round(float(rho),4),paired=round(paired,4),
                             passA=bool(rho<=-0.7),passAB=bool(rho<=-0.7 and paired>=0.9))
npAB=sum(1 for v in wind.values() if v['passAB'])
print('wind candidates %d, passA %d, passAB %d'%(len(wind),sum(1 for v in wind.values() if v['passA']),npAB),flush=True)
# ---- 内潮名单 ----
E48=json.load(open('/data/xinyuan/GOAI_ai4s_env/e44/analysis/E48_SEARCH.json'))
# E48 json 只有 top50; 需要完整名单 -> 重跑其打分部分太浪费, 改: E48 脚本本轮已在内存算过...
# 简化: 直接重算内潮三轴(便宜, base 已缓存在 E44 metrics? 不在) -> 重算(23 case 开 nc, ~1min)
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/e44')
import e48_search as T
B={}
for t in sorted(set(t for ax in T.AXES.values() for t,_ in ax)):
    d=T.PF+t if t.startswith('pf_') else T.E44+'cases/'+t
    B[t]=T.base_quantities(d)
tkeys=sorted(set.intersection(*[set(v.keys()) for v in B.values()]))
tide={}
import itertools
for kn,kd in [(k,None) for k in tkeys]+[(a,b) for a,b in itertools.product(tkeys,tkeys) if a!=b]:
    rr={}; ok=True
    for ax,pts in T.AXES.items():
        vals=[]
        for t,x in pts:
            num=B[t][kn]; den=B[t][kd] if kd else 1.0
            if kd and abs(den)<1e-12: ok=False; break
            vals.append(num/den)
        if not ok: break
        rr[ax]=T.spearman([x for _,x in pts],vals)
    if not ok: continue
    sg=[np.sign(rr[a]) for a in ('m','visc','gam')]
    same=(sg[0]!=0 and sg[0]==sg[1]==sg[2]); amin=min(abs(rr[a]) for a in ('m','visc','gam'))
    tide[(kn,kd)]=dict(alarm=bool(same and sg[0]>0 and amin>=0.85),minrho=round(float(amin),3))
nt=sum(1 for v in tide.values() if v['alarm'])
print('tide alarm %d'%nt,flush=True)
# ---- 交集 ----
inter=[k for k in wind if k in tide and wind[k]['passAB'] and tide[k]['alarm']]
inter.sort(key=lambda k:-(min(wind[k]['paired'],1)+tide[k]['minrho']))
uv=('u|all|rms','v|all|mean_abs')
res=dict(wind_passAB=npAB,tide_alarm=nt,intersection=len(inter),
    uv_in_intersection=bool(uv in [tuple(k) for k in inter]),
    uv_wind=wind.get(uv),uv_tide=tide.get(uv),
    tempd400_wind=wind.get(('temp|d400|mean_abs',None)),
    tempd400_tide=tide.get(('temp|d400|mean_abs',None)),
    intersection_list=[dict(num=k[0],den=k[1],wind=wind[k],tide=tide[k]) for k in inter[:40]])
json.dump(res,open('/data/xinyuan/GOAI_ai4s_env/e44/analysis/E49_CROSS.json','w'),indent=1)
print('INTERSECTION:',len(inter),' uv in:',res['uv_in_intersection'])
print('uv wind:',res['uv_wind'],' tide:',res['uv_tide'])
print('temp|d400 wind:',res['tempd400_wind'])
for r in res['intersection_list'][:12]: print(r['num'],'/',r['den'],r['wind'],r['tide'])
