#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""e44/analyze_e44.py -- E44 收数：每 case 一行指标
TM(环带外传功率)/COH/正压振幅 口径逐字取自 wake_20260829/phase_test.py (one)；
在 pf_dj/pf_v4/pf_combo 上须复现 PHASEFIX_PART_84.json 的读数（锚检验）。
新增指标组（本脚本自算，全部只用 ROMS his——即"Agent 可见"侧）：
  uv_ratio      : 末帧 rms(u)/mean|v| —— 逐字搬 GOAI_ai4s_env/scripts/env2.py:303-305
  deep_dc_rms   : LSQ DC 场 z<-160 rms (cm/s)（"残差流"类诱饵，ROMS 自算版）
  all_dc_rms    : 全域 DC rms
  deep450_m2_frac: 斜压 M2 动能的 z<-450 (N<ω 深水) 占比（零通道②候选）
  spec_tail_frac: 斜压 M2 振幅场 2D FFT λ<4Δx 能量占比（诱饵：谱尾）
  strat_drift   : 窗均温度剖面 vs 初始 的 rms 漂移 (K)（诱饵：层结保持）
  bt_M2_amp     : 域平均正压纬向流 M2 振幅 (m/s)（守门：正压潮不该被治理动）
"""
import os, sys, json, glob
import numpy as np, netCDF4 as nc

OMEGA=1.40519e-4; F0=5.463337479696344e-5; T_M2=2.0*np.pi/OMEGA
G,RHO0,ALPHA=9.81,1025.0,1.7e-4; DAY=86400.0
R1,R2=6000.0,16000.0; XC=YC=40000.0

def trap_weights(t,ta,tb):
    t=np.asarray(t,np.float64); w=np.zeros_like(t)
    for k in range(len(t)-1):
        a=max(t[k],ta); b=min(t[k+1],tb)
        if b<=a: continue
        dt=t[k+1]-t[k]; ua=(a-t[k])/dt; ub=(b-t[k])/dt
        w[k]+=dt*((ub-ua)-0.5*(ub**2-ua**2)); w[k+1]+=dt*(0.5*(ub**2-ua**2))
    s=w.sum(); assert abs(s-(tb-ta))<1e-6*(tb-ta)
    return w/s

def one(casedir,tag):
    hisf=sorted(glob.glob(casedir+'/his*.nc'))[0]
    ds=nc.Dataset(hisf); V=ds.variables
    t=np.asarray(V['ocean_time'][:],np.float64)
    h=np.asarray(V['h'][:],np.float64)
    xr=np.asarray(V['x_rho'][:],np.float64); yr=np.asarray(V['y_rho'][:],np.float64)
    DX=1.0/float(np.asarray(V['pm'][:])[0,0]); DA=DX*DX
    tb=float(t[-1]); ta=tb-11.0*T_M2
    k0=int(np.searchsorted(t,ta+1e-9,side='right')-1)
    sel=np.arange(k0,t.size); tt=t[sel]; nt=sel.size
    wtr=trap_weights(tt,ta,tb); tau=tt-float(t[0])
    s_w=np.asarray(V['s_w'][:],np.float64); Cs_w=np.asarray(V['Cs_w'][:],np.float64)
    s_r=np.asarray(V['s_rho'][:],np.float64); Cs_r=np.asarray(V['Cs_r'][:],np.float64)
    hc=float(np.asarray(V['hc'][:]))
    Zo_w=(hc*s_w[:,None,None]+Cs_w[:,None,None]*h)/(hc+h)
    Zo_r=(hc*s_r[:,None,None]+Cs_r[:,None,None]*h)/(hc+h)
    zeta=np.asarray(V['zeta'][sel],np.float64)
    z_w=zeta[:,None]+(zeta[:,None]+h)*Zo_w[None]
    Hz=np.diff(z_w,axis=1)
    temp=np.asarray(V['temp'][sel],np.float64)
    u=np.asarray(V['u'][sel],np.float64); v=np.asarray(V['v'][sel],np.float64)
    temp0=np.asarray(V['temp'][0],np.float64)
    ds.close(); assert (Hz>0).all()
    Hz_u=0.5*(Hz[...,:-1]+Hz[...,1:]); Hz_v=0.5*(Hz[:,:,:-1,:]+Hz[:,:,1:,:])
    # ---- TM 口径（在档主量, 逐字 phase_test）----
    Tbar=np.tensordot(wtr,temp,axes=(0,0))
    rhop=-RHO0*ALPHA*(temp-Tbar[None]); rh=rhop*Hz
    cs=np.cumsum(rh[:,::-1],axis=1)[:,::-1]-rh
    p_r=G*(cs+0.5*rh)
    ub=(Hz_u*u).sum(1)/Hz_u.sum(1); vb=(Hz_v*v).sum(1)/Hz_v.sum(1)
    up=u-ub[:,None]; vp=v-vb[:,None]
    Fx_u=np.tensordot(wtr,(up*0.5*(p_r[...,:-1]+p_r[...,1:])*Hz_u).sum(1),axes=(0,0))
    Fy_v=np.tensordot(wtr,(vp*0.5*(p_r[:,:,:-1,:]+p_r[:,:,1:,:])*Hz_v).sum(1),axes=(0,0))
    Vol_u=Hz_u.sum(1)
    Ut=(ub*Vol_u).reshape(nt,-1).sum(1)/Vol_u.reshape(nt,-1).sum(1)
    Gm=np.column_stack([np.ones_like(tau),np.cos(OMEGA*tau),np.sin(OMEGA*tau),
                        np.cos(F0*tau),np.sin(F0*tau)])
    c,*_=np.linalg.lstsq(Gm,Ut,rcond=None)
    U_mean=float(np.dot(wtr,Ut)); U_M2=float(np.hypot(c[1],c[2]))
    ny,nx=h.shape
    rr=np.hypot(xr-XC,yr-YC)
    nhx=np.where(rr>0,(xr-XC)/np.where(rr>0,rr,1),0.0)
    nhy=np.where(rr>0,(yr-YC)/np.where(rr>0,rr,1),0.0)
    ann=(rr>=R1)&(rr<=R2); W_MW=DA/(R2-R1)/1e6
    Fx=np.full((ny,nx),np.nan); Fy=np.full((ny,nx),np.nan)
    Fx[:,1:-1]=0.5*(Fx_u[:,:-1]+Fx_u[:,1:]); Fy[1:-1,:]=0.5*(Fy_v[:-1,:]+Fy_v[1:,:])
    Fr=Fx*nhx+Fy*nhy
    good=ann&np.isfinite(Fx)&np.isfinite(Fy)
    vv=np.where(good,Fr,0.0)
    Pnet=float(vv.sum()*W_MW); Pplus=float(vv[vv>0].sum()*W_MW)
    # ---- 新增指标组（Agent 可见侧, 只用本 his）----
    P=np.linalg.pinv(Gm)
    cu=np.tensordot(P,u,axes=(1,0)); cv=np.tensordot(P,v,axes=(1,0))
    dc_u=cu[0]; dc_v=cv[0]
    uhat=cu[1]-1j*cu[2]
    Hzb=np.tensordot(wtr,Hz,axes=(0,0))
    Hzbu=0.5*(Hzb[...,:-1]+Hzb[...,1:])
    ubh=(Hzbu*uhat).sum(0)/Hzbu.sum(0)
    uph=uhat-ubh[None]                       # 斜压 M2 复振幅 (u)
    zr_rest=Zo_r*h                            # rest z_r (Vtransform=2, zeta=0)
    zr_u=0.5*(zr_rest[:,:,:-1]+zr_rest[:,:,1:])
    m160=zr_u<-160.0; m450=zr_u<-450.0
    ke_m2=0.5*np.abs(uph)**2*Hz_u.mean(0) if False else 0.5*np.abs(uph)**2*Hzbu
    deep450_m2_frac=float(ke_m2[m450].sum()/ke_m2.sum()) if ke_m2.sum()>0 else None
    dcu_cm=dc_u*100.0
    deep_dc_rms=float(np.sqrt((dcu_cm[m160]**2).mean()))
    all_dc_rms=float(np.sqrt((dcu_cm**2).mean()))
    # uv_ratio —— 逐字 env2.py:303-305（末帧）
    u_last=u[-1]; v_last=v[-1]
    _un=float(np.sqrt((u_last**2).mean())*100); _vd=float(np.abs(v_last).mean()*100)
    uv_ratio=(_un/_vd) if _vd>1e-12 else None
    # 谱尾：斜压 M2 振幅场（垂向积分幅）2D FFT, λ<4Δx 占比
    A2=np.abs((uph*Hzbu).sum(0))
    A2=A2-A2.mean()
    F2=np.abs(np.fft.fft2(A2))**2
    kx=np.fft.fftfreq(A2.shape[1],d=DX); ky=np.fft.fftfreq(A2.shape[0],d=DX)
    KX,KY=np.meshgrid(kx,ky); K=np.hypot(KX,KY)
    tail=K>1.0/(4*DX)
    spec_tail_frac=float(F2[tail].sum()/F2.sum()) if F2.sum()>0 else None
    strat_drift=float(np.sqrt(((np.tensordot(wtr,temp,axes=(0,0))-temp0)**2).mean()))
    return dict(tag=tag,nrec=int(t.size),Pnet_MW=Pnet,Pplus_MW=Pplus,
                U_mean=U_mean,bt_M2_amp=U_M2,
                uv_ratio=uv_ratio,deep_dc_rms=deep_dc_rms,all_dc_rms=all_dc_rms,
                deep450_m2_frac=deep450_m2_frac,spec_tail_frac=spec_tail_frac,
                strat_drift=strat_drift)

if __name__=='__main__':
    E='/data/xinyuan/GOAI_ai4s_env/e44/'
    PF='/data/xinyuan/zpg_roms_dev/pge_test/phasefix_20260829/'
    cases=[('pf_dj',PF+'pf_dj'),('pf_v4',PF+'pf_v4'),('pf_combo',PF+'pf_combo')]
    for d in sorted(glob.glob(E+'cases/*/')):
        tag=os.path.basename(d.rstrip('/'))
        if os.path.exists(d+'/DONE'): cases.append((tag,d.rstrip('/')))
    out={}
    for tag,d in cases:
        try:
            out[tag]=one(d,tag); print('%-14s Pnet=%8.4f MW  btM2=%.4f  uv=%.3f  deepDC=%7.3f  d450=%.4f  tail=%.4f'%(
                tag,out[tag]['Pnet_MW'],out[tag]['bt_M2_amp'],out[tag]['uv_ratio'] or -1,
                out[tag]['deep_dc_rms'],out[tag]['deep450_m2_frac'] or -1,out[tag]['spec_tail_frac'] or -1))
        except Exception as e:
            out[tag]=dict(tag=tag,error=str(e)); print('%-14s ERROR %s'%(tag,e))
    json.dump(out,open(E+'analysis/E44_METRICS.json','w'),indent=1)
    print('wrote',E+'analysis/E44_METRICS.json')
