#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# p90 点估计 MAE 之比（PPI 校正 CDF vs 经典标注次序统计量）。纯合成。
import numpy as np
def ols_ab(x,y):
    vx=x.var(ddof=1) if len(x)>1 else 0.0
    if vx<1e-30: return float(y.mean()),0.0
    b=float(np.cov(x,y,ddof=1)[0,1]/vx); return float(y.mean()-b*x.mean()),b
rng=np.random.default_rng(11)
N=58; REP=4000; q=0.9
for corr_lbl,noise in (('r095',0.30),('r09',0.45),('r07',1.0),('r05',1.7)):
    Y=np.abs(rng.normal(3,1,N))+0.2
    f=2.0*Y+rng.normal(0,2.0*np.std(Y)*noise,N)
    thP=np.sort(Y)[int(np.ceil(q*N))-1]
    row=[f'{corr_lbl} corr={np.corrcoef(f,Y)[0,1]:.3f}']
    for n in (12,16,24):
        e_ppi=[]; e_cl=[]
        for _ in range(REP):
            idx=rng.choice(N,n,replace=False); yl,fl=Y[idx],f[idx]
            a,b=ols_ab(fl,yl); ha=a+b*f; hl=a+b*fl
            T=np.unique(np.concatenate([ha,yl]))
            F=np.array([(ha<=t).mean()+((yl<=t)*1.0-(hl<=t)*1.0).mean() for t in T])
            ok=np.where(F>=q)[0]
            est=T[ok[0]] if len(ok) else T[-1]
            e_ppi.append(abs(est-thP))
            e_cl.append(abs(np.sort(yl)[int(np.ceil(q*n))-1]-thP))
        row.append(f'n={n}: {np.median(e_ppi)/max(np.median(e_cl),1e-12):.2f}')
    print('  '.join(row))
