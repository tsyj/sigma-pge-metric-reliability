#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
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

F.paper_style()
BLUE='#3C5488'; GRAY2='#848D96'; AMBER='#C46A1F'; PUR2='#5E2E8F'
D=json.load(open('/data/xinyuan/GOAI_ai4s_env/e52/E52_CROSS.json'))
D45=json.load(open('/data/xinyuan/GOAI_ai4s_env/e55/E55_CROSS.json'))
R=json.load(open('/data/xinyuan/GOAI_ai4s_env/e44/analysis/RT2_FIXES.json'))['F1_null']
fig,axs=plt.subplots(1,2,figsize=(12.6,5.2),gridspec_kw=dict(width_ratios=[1.15,1]))
plt.subplots_adjust(wspace=0.36,top=0.84,bottom=0.27,left=0.08,right=0.98)
ax=axs[0]; F.panel(ax,'a')
x=np.arange(3); w=0.18
uvA=[-D['uv_zonal']['rho'],-D45['uv_merid']['rho'],-D['uv_merid']['rho']]; uvB=[D['uv_zonal']['paired'],D45['uv_merid']['paired'],D['uv_merid']['paired']]
vuA=[-D['vu_zonal']['rho'],-D45['vu_merid']['rho'],-D['vu_merid']['rho']]; vuB=[D['vu_zonal']['paired'],D45['vu_merid']['paired'],D['vu_merid']['paired']]
ax.bar(x-1.5*w,uvA,w,color=BLUE,label='u/v · 排序力 = −ρ（越高越好）')
ax.bar(x-0.5*w,uvB,w,color=BLUE,alpha=0.45,label='u/v · 抗刷分率')
ax.bar(x+0.5*w,vuA,w,color=AMBER,label='v/u · 排序力 = −ρ')
ax.bar(x+1.5*w,vuB,w,color=AMBER,alpha=0.45,label='v/u · 抗刷分率')
ax.axhline(0.7,color=GRAY2,lw=1,ls='--'); ax.text(2.55,0.72,'A ≥0.7',fontsize=10,color='#555555')
ax.axhline(0.9,color=GRAY2,lw=1,ls=':'); ax.text(2.55,0.92,'B ≥0.9',fontsize=10,color='#555555')
ax.set_xticks(x); ax.set_xticklabels(['纬向风 0°','45°（预注册）','经向风 90°']); ax.set_ylim(-0.3,1.1); ax.set_xlim(-0.6,2.95); ax.set_ylabel('判据得分')
ax.legend(loc='upper center',ncol=2,fontsize=10,bbox_to_anchor=(0.5,-0.16),frameon=False)
ax=axs[1]; F.panel(ax,'b')
names=['纬向风','经向风','内潮','纬向∩经向','纬向∩内潮','经向∩内潮','三重交集']
obs=[D['zonal_pass'],D['merid_pass'],D['tide_alarm'],D['inter_zonal_merid'],D['inter_zonal_tide'],D['inter_merid_tide'],D['inter_triple']]
exp=[None,None,None,R['expected']['zonal_merid'],R['expected']['zonal_tide'],R['expected']['merid_tide'],R['expected']['triple']]
cols=[GRAY2,GRAY2,GRAY2,PUR2,PUR2,PUR2,AMBER]
y=np.arange(len(names))[::-1]
ax.barh(y,[v if v>0 else np.nan for v in obs],color=cols,height=0.6)
for yi,v,e in zip(y,obs,exp):
    xv=v if v>0 else 0.3
    ax.text(xv*1.25,yi+0.14,str(v),va='center',fontsize=12,fontweight='bold',color=(AMBER if v==0 else '#1a1a1a'))
    if e is not None:
        ax.plot([e,e],[yi-0.3,yi+0.3],color='#1a1a1a',lw=1.8)
        side = e*1.25 if e>xv else xv*1.25
        ax.text(side,yi-0.2,'期望 %.1f'%e,va='center',fontsize=9.5,color='#555555')
ax.set_xscale('log'); ax.set_xlim(0.25,9000); ax.set_yticks(y); ax.set_yticklabels(names)
ax.set_xlabel('通过判据的候选数（风驱空间 15376 / 内潮 19600）')
ax.text(-0.02,-0.30,'竖线 = 独立随机判据的期望（Poisson，三重期望 0.71，P(0)=0.49）',transform=ax.transAxes,fontsize=9.5,color='#555555')
fig.suptitle('三个风向，排序力与抗刷分从未同时落在同一把比值尺子上——交集计数与随机期望无差别',fontsize=14,fontweight='bold',y=0.97)
fig.savefig('/data/xinyuan/GOAI_ai4s_env/e44/figs/fig_e52.png',dpi=300); print('fig_e52 v3 saved')
