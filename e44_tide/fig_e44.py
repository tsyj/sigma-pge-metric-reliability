#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E44 主图 v3: 一色一量(validate_palette 全过感知三关); a/b 共享 m 轴堆叠; 单轴归一化
色表: u/v=#3C5488 蓝圆 | 残余流=#848D96 灰方虚 | 环带功率=#C46A1F 橙棕三角 |
     第一模=#8A65C5 空心圆 | 第二模=#5E2E8F 实心圆"""
import sys, json
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
import figstyle as F
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs
import numpy as np
F.paper_style()
BLUE='#3C5488'; GRAY2='#848D96'; AMBER='#C46A1F'; PUR1='#8A65C5'; PUR2='#5E2E8F'
E='/data/xinyuan/GOAI_ai4s_env/e44/'
M=json.load(open(E+'analysis/E44_METRICS.json'))
K=json.load(open(E+'analysis/ANSWER_KEY_500KM.json'))
def S(tags,k): return np.array([M[t][k] for t in tags])

fig=plt.figure(figsize=(11.6,8.8))
G=gs.GridSpec(2,2,hspace=0.42,wspace=0.30,top=0.86,bottom=0.09,left=0.085,right=0.97)
# 左列: a(锚) / b(可见) 共享 m 轴
axa=fig.add_subplot(G[0,0]); axb=fig.add_subplot(G[1,0],sharex=axa)
# (a) 500km 隐藏锚
F.panel(axa,'a')
axa.axhline(1.0,color='#e0e0e0',lw=1.0,ls='-',zorder=0)
ms=[2,4,6]
axa.plot(ms,[K['mode1_ratio']['m%d'%m] for m in ms],'o-',color=PUR1,lw=2.0,ms=9,
         markerfacecolor='white',markeredgewidth=2.0,label='第一垂向模')
axa.plot(ms,[K['mode2_ratio']['m%d'%m] for m in ms],'o-',color=PUR2,lw=2.2,ms=8,label='第二垂向模')
axa.set_ylabel('隐藏锚：远场功率保留比\n（500 km · 仅 2/4/6 档）')
axa.set_ylim(0,1.08); axa.set_xticks([2,3,4,5,6]); axa.legend(loc='lower left')
plt.setp(axa.get_xticklabels(),visible=False)
# (b) 84km 可见指标
F.panel(axb,'b')
bt=['b_bsplm2','b_bsplm3','pf_combo','b_bsplm5','b_bsplm6']; xb=[2,3,4,5,6]
uv=S(bt,'uv_ratio'); dc=S(bt,'deep_dc_rms'); pn=S(bt,'Pnet_MW')
axb.plot(xb,uv/uv[0],'o-',color=BLUE,lw=2.2,ms=7,label='u/v 比值')
axb.plot(xb,dc/dc[0],'s--',color=GRAY2,lw=2.0,ms=6,label='深层残余流')
axb.plot(xb,pn/pn[0],'^-',color=AMBER,lw=2.2,ms=7,label='环带波功率')
axb.axhline(1.0,color='#e0e0e0',lw=1.0,zorder=0)
axb.set_xticks(xb); axb.set_xlabel('B 样条节点距（Δx）')
axb.set_ylabel('可见指标（84 km，\n相对最轻档）'); axb.legend(loc='lower left',fontsize=11.5)
def normpanel(ax,tags,x,xt,xlabel):
    uv=S(tags,'uv_ratio'); dc=S(tags,'deep_dc_rms'); pn=S(tags,'Pnet_MW')
    ax.plot(x,uv/uv[0],'o-',color=BLUE,lw=2.2,ms=7)
    ax.plot(x,dc/dc[0],'s--',color=GRAY2,lw=2.0,ms=6)
    ax.plot(x,pn/pn[0],'^-',color=AMBER,lw=2.2,ms=7)
    ax.axhline(1.0,color='#e0e0e0',lw=1.0,zorder=0)
    ax.axhline(0.0,color=AMBER,lw=1.4,ls='--',alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels(xt)
    ax.set_xlabel(xlabel); ax.set_ylabel('可见指标（相对基准档）')
axc=fig.add_subplot(G[0,1]); F.panel(axc,'c')
at=['pf_v4','a_v4visc3e6','a_v4visc1e7','a_v4visc3e7','a_v4visc5e7','a_v4visc1e8','a_v4visc2e8','a_v4visc3e8']
normpanel(axc,at,np.arange(8),['0','3e6','1e7','3e7','5e7','1e8','2e8','3e8'],'双谐波黏性（m⁴/s）')
axd=fig.add_subplot(G[1,1]); F.panel(axd,'d')
ct=['c_g0p25','c_g0p5','pf_combo','c_g2','c_g4','c_g8','c_g16']
normpanel(axd,ct,np.arange(7),['×¼','×½','×1','×2','×4','×8','×16'],'B 样条强度（相对生产值）')
fig.suptitle('内潮三轴扫描：残余流变好看、u/v 单调报警——后续审计见 kill board',
             fontsize=16.5,fontweight='bold',y=0.965)
fig.savefig(E+'figs/fig_e44_main.png',dpi=300)
print('saved v3')
