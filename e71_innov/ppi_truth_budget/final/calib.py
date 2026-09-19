#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# 合成校准：均值/分位估计量变体的覆盖率。纯合成，不读任何数据。
import numpy as np
from scipy import stats as st

def ols_ab(x,y):
    vx=x.var(ddof=1) if len(x)>1 else 0.0
    if vx<1e-30: return float(y.mean()),0.0
    b=float(np.cov(x,y,ddof=1)[0,1]/vx); return float(y.mean()-b*x.mean()),b

def mean_A(yl,fl,fa,N):  # 现行：解析 t_{n-2}
    n=len(yl); a,l=ols_ab(fl,yl); d=yl-l*fl
    th=l*fa.mean()+d.mean(); v=max(0,(1/n-1/N))*np.var(d,ddof=1)
    tq=st.t.ppf(0.95,max(n-2,1)); se=np.sqrt(v); return th-tq*se,th+tq*se
def mean_B(yl,fl,fa,N):  # 刀切 + t_{n-1}
    n=len(yl); ths=[]
    for i in range(n):
        m=np.ones(n,bool); m[i]=False
        a,l=ols_ab(fl[m],yl[m]); ths.append(l*fa.mean()+(yl[m]-l*fl[m]).mean())
    ths=np.array(ths); a,l=ols_ab(fl,yl); th=l*fa.mean()+(yl-l*fl).mean()
    v=(1-n/N)*(n-1)/n*((ths-ths.mean())**2).sum()
    tq=st.t.ppf(0.95,n-1); se=np.sqrt(v); return th-tq*se,th+tq*se
def mean_C(yl,fl,fa,N):  # 解析 t_{n-1} + 膨胀 sqrt((n-1)/(n-3))
    n=len(yl); a,l=ols_ab(fl,yl); d=yl-l*fl
    th=l*fa.mean()+d.mean(); v=max(0,(1/n-1/N))*np.var(d,ddof=1)*(n-1)/max(n-3,1)
    tq=st.t.ppf(0.95,n-1); se=np.sqrt(v); return th-tq*se,th+tq*se

def inv(T,F,SE,z,cc,q=0.9):
    lo_ok=np.where(F+z*SE+cc>=q)[0]; hi_ok=np.where(F-z*SE-cc<=q)[0]
    lo=T[lo_ok[0]] if len(lo_ok) else T[0]; hi=T[hi_ok[-1]] if len(hi_ok) else T[-1]
    return lo,hi
def p90(yl,fl,fa,N,zmode,cc_on):
    n=len(yl); a,b=ols_ab(fl,yl); ha=a+b*fa; hl=a+b*fl
    T=np.unique(np.concatenate([ha,yl]))
    F=np.array([(ha<=t).mean()+((yl<=t)*1.0-(hl<=t)*1.0).mean() for t in T])
    SE=np.array([np.sqrt(max(0,(1/n-1/N))*max(np.var((yl<=t)*1.0-(hl<=t)*1.0,ddof=1),0)) for t in T])
    SE=np.maximum(SE,1e-12)
    z=st.t.ppf(0.95,n-1) if zmode=='t' else st.norm.ppf(0.95)
    return inv(T,F,SE,z,(0.5/n if cc_on else 0.0))

rng=np.random.default_rng(11)
N=58; REP=2000
for corr_lbl,noise in (('r09',0.45),('r05',1.7),('r00',1e6)):
    Y=np.abs(rng.normal(3,1,N))+0.2
    f=2.0*Y+rng.normal(0,2.0*np.std(Y)*noise,N)
    thM=Y.mean(); thP=np.sort(Y)[int(np.ceil(0.9*N))-1]
    print(f'--- {corr_lbl} corr={np.corrcoef(f,Y)[0,1]:.3f}')
    for n in (8,16,32):
        cm={k:0 for k in 'ABC'}; cp={k:0 for k in ('A','B','C')}
        for _ in range(REP):
            idx=rng.choice(N,n,replace=False); yl,fl=Y[idx],f[idx]
            for k,fn in (('A',mean_A),('B',mean_B),('C',mean_C)):
                lo,hi=fn(yl,fl,f,N); cm[k]+= (lo<=thM<=hi)
            for k,args in (('A',('z',False)),('B',('z',True)),('C',('t',True))):
                lo,hi=p90(yl,fl,f,N,*args); cp[k]+= (lo<=thP<=hi)
        print(f'  n={n:2d} mean A/B/C = {cm["A"]/REP:.3f}/{cm["B"]/REP:.3f}/{cm["C"]/REP:.3f}'
              f'   p90 A/B/C = {cp["A"]/REP:.3f}/{cp["B"]/REP:.3f}/{cp["C"]/REP:.3f}')
