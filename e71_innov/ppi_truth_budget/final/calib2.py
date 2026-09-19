#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# 终版变体校准：均值=刀切+t_{n-1}；p90=cc+t_{n-1}+无界哨兵。纯合成。
import numpy as np
from scipy import stats as st

def ols_ab(x,y):
    vx=x.var(ddof=1) if len(x)>1 else 0.0
    if vx<1e-30: return float(y.mean()),0.0
    b=float(np.cov(x,y,ddof=1)[0,1]/vx); return float(y.mean()-b*x.mean()),b

def mean_jk(yl,fl,fa,N):
    n=len(yl); a,l=ols_ab(fl,yl); th=l*fa.mean()+(yl-l*fl).mean()
    ths=[]
    for i in range(n):
        m=np.ones(n,bool); m[i]=False
        _,li=ols_ab(fl[m],yl[m]); ths.append(li*fa.mean()+(yl[m]-li*fl[m]).mean())
    ths=np.array(ths)
    v=(1-n/N)*(n-1)/n*((ths-ths.mean())**2).sum()
    tq=st.t.ppf(0.95,n-1); se=np.sqrt(v); return th-tq*se,th+tq*se,v

def p90_fixed(yl,fl,fa,N,q=0.9):
    n=len(yl); a,b=ols_ab(fl,yl); ha=a+b*fa; hl=a+b*fl
    T=np.unique(np.concatenate([ha,yl]))
    F=np.array([(ha<=t).mean()+((yl<=t)*1.0-(hl<=t)*1.0).mean() for t in T])
    SE=np.maximum(np.array([np.sqrt(max(0,(1/n-1/N))*max(np.var((yl<=t)*1.0-(hl<=t)*1.0,ddof=1),0)) for t in T]),1e-12)
    z=st.t.ppf(0.95,n-1); cc=0.5/n
    lo_ok=np.where(F+z*SE+cc>=q)[0]; hi_ok=np.where(F-z*SE-cc<=q)[0]
    lo=-np.inf if (len(lo_ok)==0 or lo_ok[0]==0) else T[lo_ok[0]]
    hi= np.inf if (len(hi_ok)==0 or hi_ok[-1]==len(T)-1) else T[hi_ok[-1]]
    return lo,hi

rng=np.random.default_rng(11)
N=58; REP=2000
for corr_lbl,noise in (('r09',0.45),('r05',1.7),('r00',1e6)):
    Y=np.abs(rng.normal(3,1,N))+0.2
    f=2.0*Y+rng.normal(0,2.0*np.std(Y)*noise,N)
    thM=Y.mean(); thP=np.sort(Y)[int(np.ceil(0.9*N))-1]
    print(f'--- {corr_lbl} corr={np.corrcoef(f,Y)[0,1]:.3f}')
    for n in (8,12,16,24,32):
        cm=cp=0; unb=0; vs=[]
        for _ in range(REP):
            idx=rng.choice(N,n,replace=False); yl,fl=Y[idx],f[idx]
            lo,hi,v=mean_jk(yl,fl,f,N); cm+=(lo<=thM<=hi); vs.append(v)
            plo,phi=p90_fixed(yl,fl,f,N); cp+=(plo<=thP<=phi); unb+=np.isinf(plo)|np.isinf(phi)
        S2Y=np.var(Y,ddof=1); vmed=np.median(vs)
        neff=min(N,1/(vmed/S2Y+1/N)) if vmed>0 else N
        print(f'  n={n:2d} mean_jk={cm/REP:.3f} neff/n={neff/n:.2f}   p90={cp/REP:.3f} (unbounded {unb/REP:.2f})')
