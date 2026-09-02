#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""图: Agent 在与线性模型完全相同的信息条件下挑尺子"""
import sys, json
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
F.paper_style()
BLUE='#3C5488'; AMBER='#C46A1F'; GREEN='#175C3B'; GRAY='#848D96'; RED='#B03A2E'
G='/data/xinyuan/GOAI_ai4s_env/'
S=json.load(open(G+'e61/E61_AGENT_PICKS.json')); P=json.load(open(G+'e61/E61B_POSTHOC.json'))
fig,axs=plt.subplots(1,2,figsize=(12.6,5.4),gridspec_kw=dict(width_ratios=[1.35,1]))
plt.subplots_adjust(wspace=0.30,top=0.82,bottom=0.14,left=0.08,right=0.98)
# (a) 逐局对比
ax=axs[0]; F.panel(ax,'a')
seeds=[g['seed'] for g in S['games']]
series=[('逻辑回归（七参数）','logistic',GREEN,'-o'),('低 B 启发式（单特征）','b_heuristic',AMBER,'-^'),
        ('Agent（deepseek-v4-pro）','agent',BLUE,'-s'),('随机（每局 200 次重采样）','random',GRAY,'--')]
for lab,k,c,st in series:
    v=[g[k] for g in S['games']]
    ax.plot(seeds,v,st,color=c,lw=2.2,ms=8,label='%s  均值 %.3f'%(lab,np.mean(v)))
ax.set_xticks(seeds); ax.set_xlabel('局（独立随机抽样，种子 0–7）')
ax.set_ylabel('所选 10 个候选里真正有排序力的比例')
ax.set_ylim(0,1.0); ax.legend(loc='upper left',fontsize=10.2,ncol=1)
ax.set_title('同样的 40 个候选、同样的七个无真值特征、不给真值',fontsize=12.5,fontweight='bold',pad=9)
# (b) 按 Agent 自述方向分组
ax=axs[1]; F.panel(ax,'b')
gp=P['groups']; labs=['说对方向\n（抗刷低更好）','说反方向\n（抗刷高更好）','没说清 /\n混合']
keys=['用对_低抗刷','用反_高抗刷','未表态或混合']
vals=[gp[k]['mean'] for k in keys]; ns=[gp[k]['n'] for k in keys]
cols=[GREEN,RED,GRAY]
b=ax.bar(range(3),vals,0.6,color=cols)
for i,(v,n) in enumerate(zip(vals,ns)):
    ax.text(i,v+0.02,'%.2f\n(n=%d)'%(v,n),ha='center',fontsize=11)
ax.axhline(S['logistic'],color=GREEN,ls='--',lw=1.5)
ax.text(2.42,S['logistic']+0.015,'逻辑回归 %.2f'%S['logistic'],ha='right',fontsize=10,color=GREEN)
ax.axhline(S['random'],color=GRAY,ls=':',lw=1.5)
ax.text(2.42,S['random']+0.015,'随机 %.2f'%S['random'],ha='right',fontsize=10,color=GRAY)
ax.set_xticks(range(3)); ax.set_xticklabels(labs,fontsize=10.5); ax.set_ylim(0,0.82)
ax.set_ylabel('该组平均命中率')
ax.set_title('方向说对时接近线性模型，说不清就回到随机',fontsize=12.5,fontweight='bold',pad=9)
fig.suptitle('Agent 挑尺子：不是读不出规律，是读出规律的过程不可重复（n=8，单模型，探索性）',
             fontsize=14.5,fontweight='bold',y=0.955)
fig.savefig(G+'e44/figs/fig_agent_picks.png',dpi=300)
print('saved fig_agent_picks.png')
