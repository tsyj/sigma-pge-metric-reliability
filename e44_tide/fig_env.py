#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""图: 环境四元组 (K, V, H, A) —— 重点是 A 也砍向 H 自己"""
import sys
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
import figstyle as F
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
F.paper_style()
BLUE='#3C5488'; GREEN='#175C3B'; RED='#B03A2E'; AMBER='#C46A1F'; PUR='#5E2E8F'; GRAY='#7A828A'
fig,ax=plt.subplots(figsize=(12.6,6.8)); ax.set_xlim(0,100); ax.set_ylim(0,58); ax.axis('off')
plt.subplots_adjust(left=0.01,right=0.99,top=0.90,bottom=0.02)
def box(x,y,w,h,txt,fc,ec,fs=11.5,tc='#1a1a1a',bold=False,r=1.6):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.4,rounding_size=%.1f"%r,
                 facecolor=fc,edgecolor=ec,linewidth=1.8))
    ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=fs,color=tc,
            fontweight=('bold' if bold else 'normal'),linespacing=1.5)
def arrow(x1,y1,x2,y2,c,lw=2.0,style='->',rad=0.0,ls='-'):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle=style,color=c,lw=lw,linestyle=ls,
                 mutation_scale=17,connectionstyle='arc3,rad=%.2f'%rad,zorder=5))
# 求解器
box(37,26,26,10,'σ 坐标求解器 ROMS\n48×48×13 · 一条 2 min','#EAEEF4',BLUE,13,BLUE,True)
# K 旋钮
box(4,26,26,10,'K　可调旋钮\n地形 / VISC2 / VISC4 / AKV_BAK\nTNU2 / 步数 / 种子 / m / γ','#FFF6E8',AMBER,11,'#7A4E00')
arrow(30,31,37,31,AMBER,2.4)
# V 可见读数
box(37,42,26,9,'V　可见读数（公开）\n流速 / 温度 / 比值 / 完赛标志\nAgent 只看得到这一层','#E9F3EC',GREEN,11.5,GREEN)
arrow(50,36,50,42,GREEN,2.4)
# H 隐藏判分
box(37,7,26,12,'H　隐藏判分（保密）\n风驱：MITgcm z 坐标独立求解器真值\n内潮：500 km 自参照锚（Weak）\n共用：平底 / 静止态零真值通道','#FDECEA',RED,10.5,'#8E2A1C')
arrow(50,26,50,19,RED,2.2,'->',0,'--')
ax.text(52.4,22.4,'不回传',fontsize=10,color=RED,style='italic')
# A 审计算子
box(70,20,26,24,'A　审计算子（一等公民）\n\nA1 配对抗刷　A2 零真值通道\nA3 盒宽　　　A4 时钟/相位\nA5 盖章预测　A6 转风向\nA7 匿名换名　A8 带符号锚\nA9 静止态 BH93 (1993)','#F3EDFA',PUR,11,'#3F1E63')
# A 砍 V
arrow(70,44,63,47,PUR,2.6,'-|>',-0.25)
ax.text(63.5,50.6,'审 V：读数配不配当判据',fontsize=11,color=PUR,ha='left')
# A 砍 H —— 关键一笔
arrow(70,22,63,13,PUR,2.8,'-|>',0.25)
ax.text(63.5,4.0,'审 H：把刀砍向我们自己的锚\n（A3 盒宽摆 7.24× / A4 时钟 4.58→7.89）',
        fontsize=11,color=PUR,ha='left',fontweight='bold',linespacing=1.4)
# Agent
box(4,42,26,9,'Agent\n只见 V，下单改 K\n对手 / 评审 / 提议者','#F4F4F6',GRAY,11.5,'#3A3F45')
arrow(30,46.5,37,46.5,GRAY,2.0)
arrow(17,42,17,36,GRAY,2.0,'->',-0.3)
ax.text(6.2,38.6,'下单真跑',fontsize=10,color=GRAY)
ax.set_title('探索环境四元组 (K, V, H, A)：审计算子是环境的一等公民，且被砍向隐藏判分自身',
             fontsize=15,fontweight='bold',pad=16)
fig.savefig('/data/xinyuan/GOAI_ai4s_env/e44/figs/fig_env.png',dpi=300)
print('saved fig_env.png')
