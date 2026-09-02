#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E52 图: 三种强迫下, 没有一把标量尺子同时满足排序(A)与抗刷分(B); 交集漏斗归零"""
import sys, json
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
F.paper_style()
BLUE='#3C5488'; GRAY2='#848D96'; AMBER='#C46A1F'; PUR2='#5E2E8F'
D=json.load(open('/data/xinyuan/GOAI_ai4s_env/e52/E52_CROSS.json'))
fig,axs=plt.subplots(1,2,figsize=(11.6,4.9))
plt.subplots_adjust(wspace=0.32,top=0.84,bottom=0.26,left=0.08,right=0.98)
# (a) uv 与 vu 在两种风向下的 A/B 两项
ax=axs[0]; F.panel(ax,'a')
labels=['纬向风','经向风']; x=np.arange(2); w=0.18
uvA=[-D['uv_zonal']['rho'],-D['uv_merid']['rho']]; uvB=[D['uv_zonal']['paired'],D['uv_merid']['paired']]
vuA=[-D['vu_zonal']['rho'],-D['vu_merid']['rho']]; vuB=[D['vu_zonal']['paired'],D['vu_merid']['paired']]
ax.bar(x-1.5*w,uvA,w,color=BLUE,label='u/v · 排序力（−ρ）')
ax.bar(x-0.5*w,uvB,w,color=BLUE,alpha=0.45,label='u/v · 抗刷分率')
ax.bar(x+0.5*w,vuA,w,color=AMBER,label='v/u · 排序力（−ρ）')
ax.bar(x+1.5*w,vuB,w,color=AMBER,alpha=0.45,label='v/u · 抗刷分率')
ax.axhline(0.7,color=GRAY2,lw=1,ls='--'); ax.axhline(0.9,color=GRAY2,lw=1,ls=':')
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(-0.3,1.08); ax.set_ylabel('判据得分')
ax.legend(loc='upper center',ncol=2,fontsize=10.5,bbox_to_anchor=(0.5,-0.16),frameon=False)
# (b) 交集漏斗
ax=axs[1]; F.panel(ax,'b')
names=['纬向风','经向风','内潮','纬向∩内潮','纬向∩经向','经向∩内潮','三重交集']
vals=[D['zonal_pass'],D['merid_pass'],D['tide_alarm'],D['inter_zonal_tide'],D['inter_zonal_merid'],D['inter_merid_tide'],D['inter_triple']]
cols=[GRAY2,GRAY2,GRAY2,PUR2,PUR2,PUR2,AMBER]
y=np.arange(len(names))[::-1]
ax.barh(y,[v if v>0 else np.nan for v in vals],color=cols,height=0.62)
for yi,v in zip(y,vals): ax.text((v if v>0 else 0.5)*1.15,yi,str(v),va='center',fontsize=12,color=(AMBER if v==0 else '#1a1a1a'),fontweight=('bold' if v==0 else 'normal'))
ax.set_xscale('log'); ax.set_xlim(0.5,6000); ax.set_yticks(y); ax.set_yticklabels(names)
ax.set_xlabel('通过判据的候选指标数（共 15376 / 19600）')
fig.suptitle('换到第三种强迫，两环境交集里的 13 把尺子全部失效——没有普适的标量尺子',fontsize=15.5,fontweight='bold',y=0.97)
fig.savefig('/data/xinyuan/GOAI_ai4s_env/e44/figs/fig_e52.png',dpi=300); print('saved')
