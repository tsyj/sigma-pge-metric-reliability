#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""图: Agent 在与线性模型完全相同的信息条件下挑尺子"""
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
BLUE='#3C5488'; AMBER='#C46A1F'; GREEN='#175C3B'; GRAY='#848D96'; RED='#B03A2E'
G='/data/xinyuan/GOAI_ai4s_env/'
S=json.load(open(G+'e61/E61_AGENT_PICKS.json')); P=json.load(open(G+'e61/E61B_POSTHOC.json'))
fig,axs=plt.subplots(1,2,figsize=(12.6,5.4),gridspec_kw=dict(width_ratios=[1.35,1]))
plt.subplots_adjust(wspace=0.30,top=0.82,bottom=0.14,left=0.08,right=0.98)
# (a) 逐局对比
ax=axs[0]; F.panel(ax,'a')
seeds=[g['seed'] for g in S['games']]
series=[('七参数的简单线性模型','logistic',GREEN,'-o'),('只看单条线索的土办法','b_heuristic',AMBER,'-^'),
        ('语言模型','agent',BLUE,'-s'),('随机挑（每局重采样 200 次）','random',GRAY,'--')]
for lab,k,c,st in series:
    v=[g[k] for g in S['games']]
    ax.plot(seeds,v,st,color=c,lw=2.2,ms=8,label='%s  均值 %.3f'%(lab,np.mean(v)))
ax.set_xticks(seeds); ax.set_xlabel('局（独立随机抽样，种子 0–7）')
ax.set_ylabel('挑出的 10 个里真正排得准的比例')
ax.set_ylim(0,1.0); ax.legend(loc='upper left',fontsize=10.2,ncol=1)
ax.set_title('同样 40 个候选、同样的线索、都不给真值',fontsize=12.5,fontweight='bold',pad=9)
# (b) 按 Agent 自述方向分组
ax=axs[1]; F.panel(ax,'b')
gp=P['groups']; labs=['说对方向','说反方向','没说清']
keys=['用对_低抗糊弄','用反_高抗糊弄','未表态或混合']
vals=[gp[k]['mean'] for k in keys]; ns=[gp[k]['n'] for k in keys]
cols=[GREEN,RED,GRAY]
b=ax.bar(range(3),vals,0.6,color=cols)
for i,(v,n) in enumerate(zip(vals,ns)):
    ax.text(i,v+0.02,'%.2f\n(n=%d)'%(v,n),ha='center',fontsize=11)
ax.axhline(S['logistic'],color=GREEN,ls='--',lw=1.5)
ax.text(2.42,S['logistic']+0.015,'线性模型 %.2f'%S['logistic'],ha='right',fontsize=10,color=GREEN)
ax.axhline(S['random'],color=GRAY,ls=':',lw=1.5)
ax.text(2.42,S['random']+0.015,'随机 %.2f'%S['random'],ha='right',fontsize=10,color=GRAY)
ax.set_xticks(range(3)); ax.set_xticklabels(labs,fontsize=10.5); ax.set_ylim(0,0.82)
ax.set_ylabel('该组平均命中率')
ax.set_title('说对方向时接近线性模型，说不清就掉回随机',fontsize=12.5,fontweight='bold',pad=9)
fig.suptitle('语言模型能读出规律，但读不稳（n=8，单模型，探索性）',
             fontsize=14.5,fontweight='bold',y=0.955)
fig.savefig(G+'e44/figs/fig_agent_picks.png',dpi=300)
print('saved fig_agent_picks.png')
