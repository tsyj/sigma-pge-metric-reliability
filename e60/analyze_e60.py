#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E60 判读：抗刷率 B 在陡度轴上稳不稳。穷举器与 E40 逐字同源（base_quantities + 同一比值空间）。"""
import json, sys, itertools
import numpy as np
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
from metric_search import base_quantities, spearman
G='/data/xinyuan/GOAI_ai4s_env/'; E=G+'e60/'
RX=['020','044','060','069']; RXV={'020':0.200,'044':0.441,'060':0.599,'069':0.694}
runs=json.load(open(E+'E60_RX0.json'))
by={}
for r in runs:
    if r.get('done') and not r.get('blowup'): by[(r['rx0'],r['bathy'],r['VISC2'])]=E+'runs/'+r['tag']
V=sorted({k[2] for k in by})
print('陡度档 %d, VISC2 档 %d'%(len(RX),len(V)))
out={'prereg_sha':'af8fe0442c700f9addcd22a6962c129e4535d8f01031bf3cc5233f9a71c1973a','rx0_values':RXV,'per_rx':{}}
Bmaps={}
for rx in RX:
    P26=[];PFL=[]
    for v in V:
        a=by.get((rx,'steep',v)); b=by.get((rx,'flat',v))
        if not(a and b): continue
        qa,qb=base_quantities(a),base_quantities(b)
        if qa and qb: P26.append(qa); PFL.append(qb)
    if len(P26)<4: print('  rx0=%s 配对不足'%rx); continue
    keys=sorted(set.intersection(*[set(q) for q in P26+PFL]))
    A26=np.array([[q[k] for k in keys] for q in P26]); AFL=np.array([[q[k] for k in keys] for q in PFL])
    EPS=1e-12; B={}
    for i,kn in enumerate(keys):
        cand=[((kn,None),A26[:,i],AFL[:,i])]
        for j,kd in enumerate(keys):
            if i==j: continue
            if np.any(np.abs(A26[:,j])<EPS) or np.any(np.abs(AFL[:,j])<EPS): continue
            cand.append(((kn,kd),A26[:,i]/A26[:,j],AFL[:,i]/AFL[:,j]))
        for key,v26,vfl in cand:
            if not(np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
            if np.any(v26<=0) or np.any(vfl<=0): continue
            B[key]=float((vfl>=v26).mean())
    Bmaps[rx]=B
    hi={k for k,v in B.items() if v>=0.9}
    out['per_rx'][rx]={'rx0':RXV[rx],'n_pairs':len(P26),'n_candidates':len(B),'n_B_ge_0.9':len(hi),
                       'frac':round(len(hi)/max(1,len(B)),4)}
    print('  rx0=%.3f  配对 %d  候选 %d  B>=0.9 的 %d (%.1f%%)'%(RXV[rx],len(P26),len(B),len(hi),100*len(hi)/max(1,len(B))))
# Jaccard + 秩相关
print('\n两两比较（P1: Jaccard<0.5 即抗刷性依赖陡度; P3: 秩相关>0.7 即整体排序稳定）:')
pairs={}
for r1,r2 in itertools.combinations(RX,2):
    if r1 not in Bmaps or r2 not in Bmaps: continue
    B1,B2=Bmaps[r1],Bmaps[r2]; common=set(B1)&set(B2)
    s1={k for k in common if B1[k]>=0.9}; s2={k for k in common if B2[k]>=0.9}
    jac=len(s1&s2)/max(1,len(s1|s2))
    v1=np.array([B1[k] for k in common]); v2=np.array([B2[k] for k in common])
    rho=spearman(v1,v2)
    pairs['%s_vs_%s'%(r1,r2)]={'jaccard':round(jac,4),'spearman':round(rho,4),
        'n_common':len(common),'n1':len(s1),'n2':len(s2),'n_both':len(s1&s2)}
    print('  rx0 %.3f vs %.3f : Jaccard=%.3f  秩相关=%.3f  (集合 %d / %d, 交 %d)'%(
        RXV[r1],RXV[r2],jac,rho,len(s1),len(s2),len(s1&s2)))
out['pairwise']=pairs
jl=[p['jaccard'] for p in pairs.values()]; rl=[p['spearman'] for p in pairs.values()]
# P2: deep_rms_800 类
print('\nP2 深层残余流类（应在所有陡度 B<=0.1）:')
p2=True
for rx in RX:
    if rx not in Bmaps: continue
    b=Bmaps[rx].get(('u|d800|rms',None))
    print('  rx0=%.3f  u|d800|rms 单量 B=%s'%(RXV[rx],'%.3f'%b if b is not None else 'NA'))
    if b is not None and b>0.1: p2=False
# P4: 配对有效性
print('\nP4 配对有效性（平底/陡海山 末刻 max|u| 之比，应 <0.1）:')
p4=[]
for rx in RX:
    for v in (0.0,2747.0):
        a=[r for r in runs if r['rx0']==rx and r['bathy']=='steep' and r['VISC2']==v and 'u_max' in r]
        b=[r for r in runs if r['rx0']==rx and r['bathy']=='flat' and r['VISC2']==v and 'u_max' in r]
        if a and b:
            ratio=b[0]['u_max']/max(1e-9,a[0]['u_max']); p4.append(ratio)
            print('  rx0=%.3f VISC2=%-6g  陡 %.2f / 平 %.2f  比值 %.3f'%(RXV[rx],v,a[0]['u_max'],b[0]['u_max'],ratio))
out['prereg_check']={
 'P1 任意两档 Jaccard<0.5': bool(all(j<0.5 for j in jl)) if jl else None,
 'P1_jaccard_range':[round(min(jl),4),round(max(jl),4)] if jl else None,
 'P2 残余流类全陡度 B<=0.1': bool(p2),
 'P3 相邻档秩相关>0.7': bool(all(r>0.7 for r in rl)) if rl else None,
 'P3_spearman_range':[round(min(rl),4),round(max(rl),4)] if rl else None,
 'P4 平底/陡海山 max|u| <0.1': bool(all(x<0.1 for x in p4)) if p4 else None,
 'P4_ratio_range':[round(min(p4),4),round(max(p4),4)] if p4 else None}
print('\n预注册核对:')
for k,v in out['prereg_check'].items():
    if not k.endswith('range'): print('  %-28s %s'%(k,'命中' if v else ('未命中' if v is not None else 'NA')))
json.dump(out,open(E+'E60_VERDICT.json','w'),indent=1,ensure_ascii=False)
print('\n-> e60/E60_VERDICT.json')
