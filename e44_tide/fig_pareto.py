#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""图: 排得准的程度 A 与抗糊弄的程度 B 的双目标平面 + 阈值敏感性"""
import sys, json
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
F.paper_style()
BLUE='#3C5488'; GRAY2='#848D96'; AMBER='#C46A1F'; PUR2='#5E2E8F'
G='/data/xinyuan/GOAI_ai4s_env/'
d=np.load(G+'e44/analysis/E57_AB.npz'); A=d['A']; B=d['B']; front=d['front']
P=json.load(open(G+'e44/analysis/E57_PARETO.json'))
fig,axs=plt.subplots(1,2,figsize=(12.2,5.2),gridspec_kw=dict(width_ratios=[1.25,1]))
plt.subplots_adjust(wspace=0.30,top=0.85,bottom=0.15,left=0.075,right=0.98)
ax=axs[0]; F.panel(ax,'a')
ax.scatter(A,B,s=3,c=GRAY2,alpha=0.25,linewidths=0,rasterized=True)
ok=(A>=0.7)&(B>=0.9)
ax.scatter(A[ok],B[ok],s=7,c=BLUE,alpha=0.7,linewidths=0,label='两关同时通过（%d 个）'%ok.sum())
o=np.argsort(A[front]); fa=A[front][o]; fb=B[front][o]
ax.plot(fa,fb,'-o',color=AMBER,lw=2.2,ms=8,zorder=5,label='Pareto 前沿（%d 点）'%len(front))
ax.scatter([1],[1],marker='*',s=320,c=PUR2,zorder=6)
ax.annotate('乌托邦角 (1, 1)：实测为空',xy=(1.0,1.005),xytext=(0.30,0.66),fontsize=11.5,color=PUR2,
            arrowprops=dict(arrowstyle='->',color=PUR2,lw=1.4,connectionstyle='arc3,rad=-0.18'))
k=P['knee']; ax.annotate('前沿上的最佳折中点\n（深层流速的高分位 / 垂向流速均方根）\n排得准的程度 %.3f　抗糊弄的程度 %.3f\n——换到内潮环境即失效'%(k['A'],k['B']),
    xy=(k['A'],k['B']),xytext=(0.30,0.30),fontsize=10.5,color=AMBER,ha='left',
    arrowprops=dict(arrowstyle='->',color=AMBER,lw=1.3,connectionstyle='arc3,rad=0.22'))
ax.axvline(0.7,color='#cccccc',lw=1,ls='--'); ax.axhline(0.9,color='#cccccc',lw=1,ls=':')
ax.text(0.71,0.02,'排得准 ≥ 0.7',fontsize=10,color='#666666'); ax.text(0.02,0.915,'抗糊弄 ≥ 0.9',fontsize=10,color='#666666')
ax.set_xlim(-0.05,1.05); ax.set_ylim(-0.03,1.06)
ax.set_xlabel('排得准的程度（与藏起来的真值名次一致，越高越好）')
ax.set_ylabel('不容易被糊弄的程度（换成平底后读数不变好看的比例）')
ax.legend(loc='center left',fontsize=10.5,bbox_to_anchor=(0.0,0.12))
ax=axs[1]; F.panel(ax,'b')
ta=[0.5,0.6,0.7,0.8,0.9]; tb=[0.7,0.8,0.85,0.9,0.95,1.0]
Z=np.array([[P['threshold_grid']['%.2f/%.2f'%(a,b)] for b in tb] for a in ta])
im=ax.imshow(Z,cmap='YlOrBr',aspect='auto',origin='lower')
for i in range(len(ta)):
    for j in range(len(tb)):
        ax.text(j,i,str(Z[i,j]),ha='center',va='center',fontsize=11,
                color=('white' if Z[i,j]>Z.max()*0.6 else '#333333'),fontweight='bold')
ax.set_xticks(range(len(tb))); ax.set_xticklabels(['%.2f'%b for b in tb])
ax.set_yticks(range(len(ta))); ax.set_yticklabels(['%.1f'%a for a in ta])
ax.set_xlabel('不容易被糊弄的门槛'); ax.set_ylabel('排得准的门槛')
r=ax.add_patch(plt.Rectangle((3-0.5,2-0.5),1,1,fill=False,edgecolor=BLUE,lw=2.5))
ax.text(3,2.62,'本文采用',ha='center',fontsize=10,color=BLUE,fontweight='bold')
import os as _os
if _os.environ.get('NO_TITLE'):
    plt.subplots_adjust(top=0.95)
    fig.savefig(G+'e44/figs/fig_pareto_notitle.png',dpi=300); print('saved fig_pareto_notitle.png')
else:
    fig.suptitle('排得准与抗糊弄互相排斥：ρ(A,B) = %.2f，两项都过 %d 个 vs 独立期望 %.0f 个（贫化 %.1f 倍）'%(
        P['spearman_A_B'],P['n_both'],P['independent_expect'],P['independent_expect']/P['n_both']),
        fontsize=14.5,fontweight='bold',y=0.965)
    fig.savefig(G+'e44/figs/fig_pareto.png',dpi=300); print('saved fig_pareto.png')
