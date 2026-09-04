#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E47 -- uv_ratio 跨环境有效的机制实测
假设: 分子 rms(u) 由正压 M2 主导(治理不动它); 分母 mean|v| 由斜压/波动 v 主导(治理选择性吃它)
     => uv_ratio 的上升主要来自分母塌缩。
实测: 末帧 u,v 的正压/斜压分解(Hz 加权深度平均), 各臂四个量 + uv_ratio 变化的分母归因份额。
"""
import os, glob, json
import numpy as np, netCDF4 as nc
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

E44='/data/xinyuan/GOAI_ai4s_env/e44/'
PF='/data/xinyuan/zpg_roms_dev/pge_test/phasefix_20260829/'
def one(d):
    f=sorted(glob.glob(d+'/his*.nc'))[0]
    ds=nc.Dataset(f); V=ds.variables
    h=np.asarray(V['h'][:],np.float64)
    s_w=np.asarray(V['s_w'][:],np.float64); Cs_w=np.asarray(V['Cs_w'][:],np.float64)
    hc=float(np.asarray(V['hc'][:]))
    zeta=np.asarray(V['zeta'][-1],np.float64)
    Zo_w=(hc*s_w[:,None,None]+Cs_w[:,None,None]*h)/(hc+h)
    z_w=zeta[None]+(zeta[None]+h)*Zo_w
    Hz=np.diff(z_w,axis=0)
    u=np.asarray(V['u'][-1],np.float64); v=np.asarray(V['v'][-1],np.float64)
    ds.close()
    Hzu=0.5*(Hz[:,:,:-1]+Hz[:,:,1:]); Hzv=0.5*(Hz[:,:-1,:]+Hz[:,1:,:])
    ub=(Hzu*u).sum(0)/Hzu.sum(0); vb=(Hzv*v).sum(0)/Hzv.sum(0)
    up=u-ub[None]; vp=v-vb[None]
    r=lambda x: float(np.sqrt((x**2).mean())*100)
    ma=lambda x: float(np.abs(x).mean()*100)
    return dict(u_rms=r(u),u_bt_rms=r(ub),u_bc_rms=r(up),
                v_mean_abs=ma(v),v_bt_mean_abs=ma(vb),v_bc_mean_abs=ma(vp),
                uv_ratio=r(u)/ma(v))
TAGS=[('pf_dj',PF+'pf_dj'),('pf_v4',PF+'pf_v4'),
 ('b_bsplm2',E44+'cases/b_bsplm2'),('b_bsplm3',E44+'cases/b_bsplm3'),('pf_combo',PF+'pf_combo'),
 ('b_bsplm5',E44+'cases/b_bsplm5'),('b_bsplm6',E44+'cases/b_bsplm6'),
 ('c_g0p25',E44+'cases/c_g0p25'),('c_g0p5',E44+'cases/c_g0p5'),('c_g2',E44+'cases/c_g2'),
 ('c_g4',E44+'cases/c_g4'),('c_g8',E44+'cases/c_g8'),('c_g16',E44+'cases/c_g16'),
 ('a_v4visc3e7',E44+'cases/a_v4visc3e7'),('a_v4visc1e8',E44+'cases/a_v4visc1e8'),
 ('a_v4visc3e8',E44+'cases/a_v4visc3e8')]
out={}
for t,d in TAGS:
    if not (t.startswith('pf_') or os.path.exists(d+'/DONE')): continue
    out[t]=one(d)
    o=out[t]
    print('%-13s u_rms=%6.3f (bt %6.3f / bc %6.3f)   v_ma=%6.3f (bt %6.3f / bc %6.3f)  uv=%.3f'%(
        t,o['u_rms'],o['u_bt_rms'],o['u_bc_rms'],o['v_mean_abs'],o['v_bt_mean_abs'],o['v_bc_mean_abs'],o['uv_ratio']))
# 归因: 相对基准臂, uv 变化里分母贡献的份额
for base,arm in [('b_bsplm2','b_bsplm6'),('c_g0p25','c_g16'),('pf_v4','a_v4visc3e8')]:
    if base in out and arm in out:
        b,a=out[base],out[arm]
        dnum=np.log(a['u_rms']/b['u_rms']); dden=np.log(a['v_mean_abs']/b['v_mean_abs'])
        share=float(-dden/(dnum-dden)) if (dnum-dden)!=0 else None
        print('%s->%s : Δln(uv)=%.3f, 分母贡献 %.0f%%, v斜压衰减 %.1f%% vs u斜压 %.1f%%'%(
            base,arm,dnum-dden,100*share,
            100*(1-a['v_bc_mean_abs']/b['v_bc_mean_abs']),100*(1-a['u_bc_rms']/b['u_bc_rms'])))
json.dump(out,open(E44+'analysis/E47_MECH.json','w'),indent=1)
print('wrote E47_MECH.json')
