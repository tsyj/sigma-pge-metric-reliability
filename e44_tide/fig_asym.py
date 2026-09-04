#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""图: 两关的不对称——排得准的程度换强迫方向就崩，抗糊弄的程度换地形陡度不崩"""
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
BLUE='#3C5488'; RED='#B03A2E'; GREEN='#175C3B'; GRAY='#848D96'
G='/data/xinyuan/GOAI_ai4s_env/'
E60=json.load(open(G+'e60/E60_VERDICT.json'))
X5=json.load(open(G+'e55/E55_CROSS.json'))
fig,axs=plt.subplots(1,2,figsize=(12.4,5.3)); plt.subplots_adjust(wspace=0.28,top=0.80,bottom=0.16,left=0.08,right=0.98)
# (a) 排得准的程度 A 随强迫方向
ax=axs[0]; F.panel(ax,'a')
traj=X5['prereg_check']['angle_trajectory_uv']
ang=[0,45,90]; A=[traj['deg0'][0],traj['deg45'][0],traj['deg90'][0]]
B=[traj['deg0'][1],traj['deg45'][1],traj['deg90'][1]]
ax.plot(ang,[-a for a in A],'-o',color=RED,lw=2.6,ms=11,label='排得准的程度')
ax.plot(ang,B,'-s',color=BLUE,lw=2.6,ms=10,label='不容易被糊弄的程度')
ax.axhline(0.7,color=RED,ls='--',lw=1.1,alpha=0.6); ax.axhline(0.9,color=BLUE,ls=':',lw=1.1,alpha=0.6)
for x,a in zip(ang,[-v for v in A]): ax.annotate('%.2f'%a,(x,a),textcoords='offset points',xytext=(0,-20),ha='center',fontsize=10.5,color=RED)
for x,b in zip(ang,B): ax.annotate('%.2f'%b,(x,b),textcoords='offset points',xytext=(0,11),ha='center',fontsize=10.5,color=BLUE)
ax.set_xticks(ang); ax.set_xticklabels(['0°\n纬向风','45°\n（预注册）','90°\n经向风'])
ax.set_xlabel('强迫方向'); ax.set_ylabel('这把尺子的两项得分')
ax.set_ylim(-0.32,1.14); ax.axhline(0,color='#bbbbbb',lw=0.9); ax.legend(loc='lower left',fontsize=10.5,framealpha=0.95)
ax.text(45,-0.24,'90° 处 A 变号：排序完全反过来',ha='center',fontsize=10,color=RED,style='italic')
ax.set_title('换个风向：排得准立刻崩',fontsize=13,fontweight='bold',pad=10)
# (b) 抗糊弄的程度 B 随地形陡度
ax=axs[1]; F.panel(ax,'b')
pw=E60['pairwise']; rxv=E60['rx0_values']
labs=[]; jac=[]; rho=[]
for k,v in pw.items():
    a,b=k.split('_vs_'); labs.append('%.2f\nvs\n%.2f'%(rxv[a],rxv[b])); jac.append(v['jaccard']); rho.append(v['spearman'])
x=np.arange(len(labs)); w=0.38
ax.bar(x-w/2,jac,w,color=BLUE,label='两种陡度下合格尺子的重合度')
ax.bar(x+w/2,rho,w,color=GREEN,label='排名的一致程度')
for i,(j,r) in enumerate(zip(jac,rho)):
    ax.text(i-w/2,j+0.015,'%.2f'%j,ha='center',fontsize=10)
    ax.text(i+w/2,r+0.015,'%.2f'%r,ha='center',fontsize=10)
ax.axhline(0.5,color=GRAY,ls='--',lw=1.2)
ax.text(len(labs)-0.5,0.52,'我们赌它会掉到 0.5 以下——赌错了',ha='right',fontsize=10.5,color=GRAY)
ax.set_xticks(x); ax.set_xticklabels(labs,fontsize=9.5); ax.set_ylim(0,1.10)
ax.set_xlabel('地形陡度 rx0 两两比较'); ax.set_ylabel('两档之间的一致性')
ax.legend(loc='lower right',fontsize=10.5)
ax.set_title('换海山陡峭程度：抗糊弄纹丝不动',fontsize=13,fontweight='bold',pad=10)
fig.suptitle('排得准看场景，抗糊弄看尺子自己：两件事不在同一层次',
             fontsize=14.5,fontweight='bold',y=0.955)
fig.savefig(G+'e44/figs/fig_asym.png',dpi=300)
print('saved fig_asym.png')
