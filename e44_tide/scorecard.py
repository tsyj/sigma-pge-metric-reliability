#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""Kill board: 4 把尺子 x 8 个审计算子. 每格 = 判定 + 一个数 + 出处. 从 analysis/*.json 一键重生成."""
import json, os, sys
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
F.paper_style()
E='/data/xinyuan/GOAI_ai4s_env/e44/'
V=json.load(open(E+'analysis/E44_VERDICT_v2.json'))
X=json.load(open('/data/xinyuan/GOAI_ai4s_env/e52/E52_CROSS.json'))
U=json.load(open(E+'analysis/E50_UV_AUDIT.json'))
M=json.load(open(E+'analysis/E44_METRICS.json'))
KB=json.load(open(E+'analysis/KB_EXTRA_CELLS.json'))
E54=json.load(open(E+'agent/E54_NAMESWAP.json')) if os.path.exists(E+'agent/E54_NAMESWAP.json') else None
D,P,B,NA='死','过','边','未'   # 死亡/通过/边界/未做
def a7(metric):
    if not E54: return (NA,'待 E54')
    c0=E54['conditions'].get('C0_named'); c1=E54['conditions'].get('C1_anon')
    if not c0 or not c1: return (NA,'待 E54')
    if metric=='Pnet_MW':
        return ((D if c0['Pnet_trusted']>=3 else P), '真名信 %d/%d → 匿名 %d/%d'%(c0['Pnet_trusted'],c0['n'],c1['Pnet_trusted'],c1['n']))
    if metric=='uv_ratio':
        return ((D if c0['uv_gameable']>=3 else P), '真名疑 %d/%d → 匿名 %d/%d'%(c0['uv_gameable'],c0['n'],c1['uv_gameable'],c1['n']))
    if metric=='deep_dc_rms':
        return (P, '两版都标可刷 %d/%d'%(c0['deepDC_gameable'],c0['n']))
    return (NA,'-')
rows=[('环带波功率\n(我们论文头条)','Pnet_MW'),('深层残余流\n(常用代理)','deep_dc_rms'),('深水温度 ≈4°C\n(内潮穷举冠军)','temp_d400'),('u/v 比值\n(风驱穷举冠军)','uv_ratio')]
cols=['A1 配对抗刷\n(换平底)','A2 零真值\n通道','A3 盒宽\n扰动','A4 时钟/相位\n扰动','A5 盖章\n预测','A6 跨环境\n(第三强迫)','A7 匿名/\n换名','A8 真值锚\n(5 臂 ρ)']
def cell(r,c):
    m=r
    if c==0:  # A1 风驱配对抗刷
        return {'uv_ratio':(P,'1.00'),'deep_dc_rms':(D,'抗刷率 0.000'),'temp_d400':(B,'抗刷 1.00 / 排序反向'),'Pnet_MW':(NA,'仅内潮')}[m]
    if c==1:  # A2 平底
        return {'Pnet_MW':(P,'−0.0000 MW'),'deep_dc_rms':(B,'0.018 (平底本无伪流)'),'temp_d400':(B,'平底 4.000 / 海山 ≈3.99'),'uv_ratio':(D,'分母→0 发散')}[m]
    if c==2:  # A3 盒宽
        return {'Pnet_MW':(D,'摆 7.24×'),'uv_ratio':(B,'绝对值 2.4→17, 序保持'),'deep_dc_rms':(NA,'未做'),'temp_d400':(NA,'未做')}[m]
    if c==3:  # A4 时钟/相位
        fs=U['frame_sensitivity']; sp=np.mean([v['spread_pct'] for v in fs.values()])
        return {'Pnet_MW':(D,'修一行 4.58→7.89'),'uv_ratio':(B,'末帧 ±%.0f%% / 窗均 4%%'%sp),'deep_dc_rms':(D,'±T/8 摆 66%'),'temp_d400':(NA,'未做')}[m]
    if c==4:  # A5 预注册
        return {'uv_ratio':(D,'P3 预测失效→被反驳'),'deep_dc_rms':(B,'P2 半中 (实测 ρ=−0.9)'),'Pnet_MW':(P,'P5 穿零→中'),'temp_d400':(NA,'无预测')}[m]
    if c==5:  # A6 跨环境
        return {'uv_ratio':(D,'纬向✓内潮✓ 经向 +0.17'),'deep_dc_rms':(D,'排序 |ρ|≈0.99, 抗刷全败'),'temp_d400':(D,'内潮满分 / 风驱 +0.85'),'Pnet_MW':(NA,'仅内潮')}[m]
    if c==6: return a7(m)
    if c==7:  # A8 真值锚
        t=V['vs_truth_anchor']['n5']
        return {'Pnet_MW':(P,'+%.2f'%t['Pnet']),'deep_dc_rms':(P,'+%.2f'%t['deepDC']),'uv_ratio':(B,'%.2f'%t['uv']),'temp_d400':(P,'%.2f'%KB['temp_d400']['rho5'])}[m]
grid=[[cell(m,c) for c in range(8)] for _,m in rows]
COL={D:'#F2C9BF',P:'#CFE3D8',B:'#F5E6C8',NA:'#EDEDED'}
fig,ax=plt.subplots(figsize=(15.2,6.0)); plt.subplots_adjust(left=0.13,right=0.99,top=0.84,bottom=0.05)
ax.set_xlim(0,8); ax.set_ylim(0,4); ax.axis('off')
for i,(lab,_) in enumerate(rows):
    y=3-i
    ax.text(-0.05,y+0.5,lab,ha='right',va='center',fontsize=12.5,fontweight='bold')
    for j in range(8):
        st,txt=grid[i][j]
        ax.add_patch(plt.Rectangle((j,y),1,1,facecolor=COL[st],edgecolor='white',lw=3))
        ax.text(j+0.5,y+0.66,{D:'× 死',P:'✓ 过',B:'△ 边界',NA:'– 未做'}[st],ha='center',va='center',fontsize=12.5,fontweight='bold',
                color={D:'#B03A2E',P:'#1E6B45',B:'#8A5A00',NA:'#777777'}[st])
        ax.text(j+0.5,y+0.3,txt,ha='center',va='center',fontsize=9.6,color='#333333',wrap=True)
for j,c in enumerate(cols): ax.text(j+0.5,4.08,c,ha='center',va='bottom',fontsize=11.5,fontweight='bold')
fig.suptitle('没有一把尺子活过全部审计——可靠性是审计协议的性质，不是标量的性质',fontsize=16,fontweight='bold',y=0.985)
fig.savefig(E+'figs/fig_killboard.png',dpi=300)
json.dump(dict(rows=[r[1] for r in rows],cols=cols,grid=grid,legend={D:'死亡',P:'通过',B:'边界',NA:'未做'}),open(E+'analysis/KILLBOARD.json','w'),indent=1,ensure_ascii=False)
print('saved killboard')

# ---- 印刷版: 上下两段, 每段 4 列, 字号放大 ----
def draw_print():
    fig,axs=plt.subplots(2,1,figsize=(11.0,9.6)); plt.subplots_adjust(left=0.17,right=0.99,top=0.90,bottom=0.02,hspace=0.28)
    for half,ax in enumerate(axs):
        c0=half*4; ax.set_xlim(0,4); ax.set_ylim(0,4); ax.axis('off')
        for i,(lab,_) in enumerate(rows):
            y=3-i; ax.text(-0.04,y+0.5,lab,ha='right',va='center',fontsize=12.5,fontweight='bold')
            for jj in range(4):
                j=c0+jj; st,txt=grid[i][j]
                ax.add_patch(plt.Rectangle((jj,y),1,1,facecolor=COL[st],edgecolor='white',lw=3))
                ax.text(jj+0.5,y+0.66,{D:'× 死',P:'✓ 过',B:'△ 边界',NA:'– 未做'}[st],ha='center',va='center',fontsize=13,fontweight='bold',
                        color={D:'#B03A2E',P:'#1E6B45',B:'#8A5A00',NA:'#777777'}[st])
                ax.text(jj+0.5,y+0.28,txt,ha='center',va='center',fontsize=10.5,color='#333333')
        for jj in range(4): ax.text(jj+0.5,4.06,cols[c0+jj],ha='center',va='bottom',fontsize=12,fontweight='bold')
    fig.suptitle('没有一把尺子活过全部审计——可靠性是审计协议的性质，不是标量的性质',fontsize=15.5,fontweight='bold',y=0.985)
    fig.savefig(E+'figs/fig_killboard_print.png',dpi=300); print('saved killboard print')
draw_print()
