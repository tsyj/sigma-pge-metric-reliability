#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# p90 终版：检验反演 min 形式 + 规则三松弛 cc=ln20/n + ±inf 哨兵。纯合成。
import numpy as np
from scipy import stats as st

def ols_ab(x,y):
    vx=x.var(ddof=1) if len(x)>1 else 0.0
    if vx<1e-30: return float(y.mean()),0.0
    b=float(np.cov(x,y,ddof=1)[0,1]/vx); return float(y.mean()-b*x.mean()),b

def p90_v3(yl,fl,fa,N,q=0.9):
    n=len(yl); a,b=ols_ab(fl,yl); ha=a+b*fa; hl=a+b*fl
    T=np.unique(np.concatenate([ha,yl]))
    F=np.array([(ha<=t).mean()+((yl<=t)*1.0-(hl<=t)*1.0).mean() for t in T])
    SE=np.maximum(np.array([np.sqrt(max(0,(1/n-1/N))*max(np.var((yl<=t)*1.0-(hl<=t)*1.0,ddof=1),0)) for t in T]),1e-12)
    z=st.t.ppf(0.95,n-1); cc=np.log(20.0)/n
    # 下限：最小的 t 使 F+zSE+cc >= q；若该 t 是网格首点 → -inf
    lo_ok=np.where(F+z*SE+cc>=q)[0]
    lo=-np.inf if (len(lo_ok)==0 or lo_ok[0]==0) else T[lo_ok[0]]
    # 上限：最小的 t 使 F-zSE-cc >= q（确信 F(t)>=q ⇒ 分位<=t）；无 → +inf
    hi_ok=np.where(F-z*SE-cc>=q)[0]
    hi= np.inf if len(hi_ok)==0 else T[hi_ok[0]]
    return lo,hi

def p90_classical_exact(yl,N,q=0.9,alpha=0.10):
    # 有限总体精确次序统计量区间（超几何）：K=#{Y_pop<=theta} 未知，
    # 保守法：theta=第 ceil(qN) 次序 ⇒ 其下方总体数 K0=ceil(qN)。
    # P(标注中 <=theta 的个数 X <= x) 超几何 (N, K0, n)。
    n=len(yl); ys=np.sort(yl); K0=int(np.ceil(q*N))
    lo_r=int(st.hypergeom.ppf(alpha/2, N, K0, n)); hi_r=int(st.hypergeom.ppf(1-alpha/2, N, K0, n))
    lo=ys[lo_r-1] if 1<=lo_r<=n else -np.inf
    hi=ys[hi_r] if hi_r+1<=n else np.inf   # 第 hi_r+1 个次序统计量
    return lo,hi

rng=np.random.default_rng(11)
N=58; REP=2000
for corr_lbl,noise in (('r09',0.45),('r05',1.7),('r00',1e6)):
    Y=np.abs(rng.normal(3,1,N))+0.2
    f=2.0*Y+rng.normal(0,2.0*np.std(Y)*noise,N)
    thP=np.sort(Y)[int(np.ceil(0.9*N))-1]
    print(f'--- {corr_lbl} corr={np.corrcoef(f,Y)[0,1]:.3f}  thP={thP:.3f}  range=[{Y.min():.2f},{Y.max():.2f}]')
    for n in (8,12,16,24,32):
        cp=ce=0; unb=0; wid=[]; wide=[]
        for _ in range(REP):
            idx=rng.choice(N,n,replace=False); yl,fl=Y[idx],f[idx]
            lo,hi=p90_v3(yl,fl,f,N); cp+=(lo<=thP<=hi); unb+=(np.isinf(lo)|np.isinf(hi))
            if np.isfinite(hi-lo): wid.append(hi-lo)
            lo2,hi2=p90_classical_exact(yl,N); ce+=(lo2<=thP<=hi2)
            if np.isfinite(hi2-lo2): wide.append(hi2-lo2)
        print(f'  n={n:2d} ppi_p90={cp/REP:.3f} (unb {unb/REP:.2f}, w_med {np.median(wid) if wid else float("nan"):.2f})'
              f'   exact_cl={ce/REP:.3f} (w_med {np.median(wide) if wide else float("nan"):.2f})')
