#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E59: 只用无真值特征预测排序力。纬向训练 -> 经向测试。
严格纪律: 特征计算过程中不得触碰 skill_vs_zero / 任何真值配对; 真值只在最后算 y 与 AUC 时出现。"""
import json, sys, os
import numpy as np
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
from metric_search import base_quantities, spearman
ENV='/data/xinyuan/GOAI_ai4s_env'
DEPTH={'s50':0,'s200':1,'all':2,'d400':3,'d800':4,'d1500':5}
def parse(k):
    p=k.split('|'); return (p[0], p[1] if len(p)>1 else 'all')
def build(ledger, runsdir, reg_src):
    """返回 rows=[(num,den,特征...,A)]，A 仅用于评估。"""
    reg={}
    if reg_src=='regraded':
        for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
            r=json.loads(l); reg[r['run_id']]=r['skill_vs_zero']
    seen={}; byp={}; knob={}
    for l in open(ledger):
        r=json.loads(l)
        if not (r['obs'].get('valid') and r['ntimes']==8640): continue
        seen[r['run_id']]=r['bathy']; knob[r['run_id']]=r['action'].get('VISC2',0.0)
        if reg_src=='hidden' and r['bathy']=='r26steep':
            h=(r.get('hidden') or {}).get('skill_vs_zero')
            if h is not None: reg[r['run_id']]=h
        a=r['action']; key=tuple(round(a.get(x,-1),6) for x in ('VISC2','VISC4','AKV_BAK','TNU2'))
        byp.setdefault(key,{})[r['bathy']]=r['run_id']
    r26=[k for k,v in seen.items() if v=='r26steep' and k in reg]
    flat=[k for k,v in seen.items() if v=='flat']
    PAIRS=[(v['r26steep'],v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
    Q26=[];S=[];V2=[];QFL=[]
    for rid in r26:
        q=base_quantities(f'{runsdir}/{rid}')
        if q: Q26.append(q); S.append(reg[rid]); V2.append(knob[rid])
    for rid in flat:
        q=base_quantities(f'{runsdir}/{rid}')
        if q: QFL.append(q)
    keys=sorted(set.intersection(*[set(q) for q in Q26+QFL]))
    M26=np.array([[q[k] for k in keys] for q in Q26]); MFL=np.array([[q[k] for k in keys] for q in QFL])
    S=np.array(S); V2=np.array(V2)
    P26=[];PFL=[]
    for a,b in PAIRS:
        qa,qb=base_quantities(f'{runsdir}/{a}'),base_quantities(f'{runsdir}/{b}')
        if qa and qb and all(k in qa and k in qb for k in keys):
            P26.append([qa[k] for k in keys]); PFL.append([qb[k] for k in keys])
    P26=np.array(P26); PFL=np.array(PFL); EPS=1e-12
    def rdisp(v):
        v=np.asarray(v,float)
        if len(v)<4: return np.nan
        q1,q3=np.percentile(v,[25,75]); med=np.median(v)
        return float((q3-q1)/abs(med)) if abs(med)>1e-30 else np.nan
    rows=[]
    for i,kn in enumerate(keys):
        cand=[(kn,None,M26[:,i],MFL[:,i],P26[:,i],PFL[:,i])]
        for j,kd in enumerate(keys):
            if i==j: continue
            if np.any(np.abs(M26[:,j])<EPS) or np.any(np.abs(MFL[:,j])<EPS) or np.any(np.abs(P26[:,j])<EPS) or np.any(np.abs(PFL[:,j])<EPS): continue
            cand.append((kn,kd,M26[:,i]/M26[:,j],MFL[:,i]/MFL[:,j],P26[:,i]/P26[:,j],PFL[:,i]/PFL[:,j]))
        for kn_,kd_,v26,vfl,p26,pfl in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))): continue
            if np.any(v26<=0) or np.any(vfl<=0): continue
            # ---- 无真值特征 ----
            f1=float((pfl>=p26).mean()) if len(p26) else 0.0          # 配对抗刷率
            f2=rdisp(vfl)                                              # 平底噪声
            f3=rdisp(v26)                                              # 海山动态范围
            mf,ms=np.median(vfl),np.median(v26)
            f4=float(mf/ms) if abs(ms)>1e-30 else np.nan               # 地形敏感度
            cn,dn=parse(kn_); cd,dd=(parse(kd_) if kd_ else (cn,dn))
            f5=1.0 if (kd_ is None or cn==cd) else 0.0                 # 同分量
            f6=float(abs(DEPTH.get(dn,2)-DEPTH.get(dd,2)))             # 深度层级差
            f7=abs(spearman(v26,V2))                                   # 与旋钮的秩相关(旋钮已知)
            # ---- 真值只在这里出现 ----
            A=-spearman(v26,S)
            rows.append((kn_,kd_ or '',f1,f2,f3,f4,f5,f6,f7,A))
    return rows
def clean(rows):
    X=np.array([[r[2],r[3],r[4],r[5],r[6],r[7],r[8]] for r in rows],float)
    A=np.array([r[9] for r in rows],float)
    ok=np.all(np.isfinite(X),axis=1)&np.isfinite(A)
    return X[ok],A[ok],[r for r,k in zip(rows,ok) if k]
def auc(y,s):
    y=np.asarray(y,bool); s=np.asarray(s,float)
    if y.sum()==0 or (~y).sum()==0: return np.nan
    o=np.argsort(s); r=np.empty(len(s)); r[o]=np.arange(1,len(s)+1)
    # 处理并列
    us,inv,cnt=np.unique(s,return_inverse=True,return_counts=True)
    sums=np.zeros(len(us)); np.add.at(sums,inv,r); r=(sums/cnt)[inv]
    n1=y.sum(); n0=(~y).sum()
    return float((r[y].sum()-n1*(n1+1)/2)/(n1*n0))
def fit_logistic(X,y,iters=4000,lr=0.12):
    mu,sd=X.mean(0),X.std(0)+1e-12; Z=(X-mu)/sd
    Z=np.hstack([Z,np.ones((len(Z),1))]); w=np.zeros(Z.shape[1])
    yv=y.astype(float)
    for _ in range(iters):
        p=1/(1+np.exp(-np.clip(Z@w,-30,30)))
        w-=lr*(Z.T@(p-yv))/len(Z)
    return w,mu,sd
def apply_logistic(X,w,mu,sd):
    Z=(X-mu)/(sd); Z=np.hstack([Z,np.ones((len(Z),1))])
    return 1/(1+np.exp(-np.clip(Z@w,-30,30)))
print('构建纬向(训练)…',flush=True)
tr=build(f'{ENV}/ledger/env2_runs.jsonl',f'{ENV}/runs','regraded')
print('  %d 候选'%len(tr),flush=True)
print('构建经向(测试)…',flush=True)
te=build(f'{ENV}/ledger/env2_merid_runs.jsonl', f'{ENV}/runs_merid','hidden')
print('  %d 候选'%len(te),flush=True)
Xtr,Atr,_=clean(tr); Xte,Ate,rte=clean(te)
ytr=(Atr>=0.7); yte=(Ate>=0.7)
print('训练 %d (正类 %d, %.2f%%) | 测试 %d (正类 %d, %.2f%%)'%(
    len(ytr),ytr.sum(),100*ytr.mean(),len(yte),yte.sum(),100*yte.mean()),flush=True)
NAMES=['f1 配对抗刷率','f2 平底噪声','f3 海山动态范围','f4 地形敏感度','f5 同分量','f6 深度层级差','f7 与旋钮秩相关']
res={'prereg_sha':'533c3062389e8ad1034beea3100264d9eb16835cdbfb8d08a7c6e8c4c4a99159',
     'n_train':int(len(ytr)),'n_test':int(len(yte)),
     'base_rate_train':float(ytr.mean()),'base_rate_test':float(yte.mean()),'single':{}}
print('\n单特征 AUC（测试集=经向）:')
for i,nm in enumerate(NAMES):
    a_te=auc(yte,Xte[:,i]); a_tr=auc(ytr,Xtr[:,i])
    res['single'][nm]={'auc_test':None if np.isnan(a_te) else round(a_te,4),
                       'auc_train':None if np.isnan(a_tr) else round(a_tr,4)}
    print('  %-16s 训练 %.3f  测试 %.3f'%(nm,a_tr,a_te))
w,mu,sd=fit_logistic(Xtr,ytr)
ste=apply_logistic(Xte,w,mu,sd); a_multi=auc(yte,ste)
res['multi']={'auc_test':round(a_multi,4),'auc_train':round(auc(ytr,apply_logistic(Xtr,w,mu,sd)),4),
              'coef':{nm:round(float(c),4) for nm,c in zip(NAMES,w[:-1])},'intercept':round(float(w[-1]),4)}
K=204
o=np.argsort(-ste)[:K]; prec=float(yte[o].mean()); base=float(yte.mean())
res['precision_at_204']={'precision':round(prec,4),'base_rate':round(base,4),
                         'lift':round(prec/base,3) if base>0 else None,'k':K}
print('\n七特征逻辑回归（纬向训练→经向测试）: AUC = %.4f'%a_multi)
print('  系数:', {nm:round(float(c),3) for nm,c in zip(NAMES,w[:-1])})
print('  precision@204 = %.4f (基率 %.4f, 提升 %.2f 倍)'%(prec,base,prec/base if base>0 else 0))
res['prereg_check']={
 'P1 f1 单特征 |AUC-0.5|>0.05': bool(abs(res['single']['f1 配对抗刷率']['auc_test']-0.5)>0.05),
 'P2 多特征 AUC>=0.70': bool(a_multi>=0.70),
 'P3 precision@204 >= 3x 基率': bool(prec>=3*base),
 'P4 f2 单特征 |AUC-0.5|>0.05': bool(abs(res['single']['f2 平底噪声']['auc_test']-0.5)>0.05)}
print('\n预注册核对:')
for k,v in res['prereg_check'].items(): print('  %-28s %s'%(k,'命中' if v else '未命中'))
json.dump(res,open(ENV+'/e59/E59_TRUTHFREE.json','w'),indent=1,ensure_ascii=False)
np.savez(ENV+'/e59/E59_ARRAYS.npz',Xtr=Xtr,Atr=Atr,Xte=Xte,Ate=Ate,score_te=ste)
print('\n-> e59/E59_TRUTHFREE.json')
