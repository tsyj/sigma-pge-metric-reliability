#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E50 -- 把处死环带功率的审计砍向新冠军 uv_ratio:
(a) 采样相位敏感性: 末帧 vs 倒数2/3/4帧(隔 1h=0.081 T_M2)的 uv 波动
(b) 口径稳健性: 窗内(末11周期)逐帧 uv 的均值/std vs 末帧值
(c) 盒宽审计: 500km 在档五臂(dj/v4/combo/k2/k6)复算 uv, 与 84km 同臂比
"""
import glob, json
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

E='/data/xinyuan/GOAI_ai4s_env/e44/'
PF='/data/xinyuan/zpg_roms_dev/pge_test/phasefix_20260829/'
PS='/data/xinyuan/zpg_roms_dev/pge_test/paperseamount_bigdom_20260828/'
BT='/data/xinyuan/zpg_roms_dev/pge_test/bandtoll_20260830/'
def uv_frame(V,i):
    u=np.asarray(V['u'][i]); v=np.asarray(V['v'][i])
    un=float(np.sqrt((u**2).mean())*100); vd=float(np.abs(v).mean()*100)
    return un/vd if vd>1e-12 else None
OMEGA=1.40519e-4; T=2*np.pi/OMEGA
out={'frame_sensitivity':{},'window_stats':{},'boxwidth_500km':{}}
tags84=[('pf_dj',PF+'pf_dj'),('pf_v4',PF+'pf_v4'),('pf_combo',PF+'pf_combo'),
        ('b_bsplm2',E+'cases/b_bsplm2'),('b_bsplm6',E+'cases/b_bsplm6'),
        ('c_g16',E+'cases/c_g16'),('a_v4visc3e8',E+'cases/a_v4visc3e8')]
for t,d in tags84:
    ds=nc.Dataset(sorted(glob.glob(d+'/his*.nc'))[0]); V=ds.variables
    n=ds.dimensions['ocean_time'].size
    fr=[uv_frame(V,i) for i in (n-1,n-2,n-3,n-4)]
    tt=np.asarray(V['ocean_time'][:]); ta=tt[-1]-11*T
    sel=np.where(tt>=ta-1e-9)[0]
    win=[uv_frame(V,int(i)) for i in sel[::6]]   # 窗内每 6h 采样
    ds.close()
    out['frame_sensitivity'][t]=dict(frames=[round(x,3) for x in fr],
        spread_pct=round(100*(max(fr)-min(fr))/np.mean(fr),1))
    out['window_stats'][t]=dict(mean=round(float(np.mean(win)),3),std=round(float(np.std(win)),3),
        lastframe=round(fr[0],3))
for t,d in [('ps_dj',PS+'ps_dj_dom500km'),('ps_v4',PS+'ps_v4_dom500km'),
            ('ps_combo_m4',PS+'ps_combo_dom500km'),('k2',BT+'ps_combo_k2'),('k6',BT+'ps_combo_k6')]:
    try:
        ds=nc.Dataset(sorted(glob.glob(d+'/his_*.nc'))[0]); V=ds.variables
        n=ds.dimensions['ocean_time'].size
        out['boxwidth_500km'][t]=round(uv_frame(V,n-1),3); ds.close()
    except Exception as e:
        out['boxwidth_500km'][t]='ERR '+str(e)[:60]
json.dump(out,open(E+'analysis/E50_UV_AUDIT.json','w'),indent=1)
print(json.dumps(out,indent=1)[:1800])
