#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""Kill board v2: 5 行(4 把尺子 + 隐藏真值对照) x 8 审计算子; 每格 {verdict,text,value,source,rule};
从 analysis/*.json 读值; 出 print(报告)/slide(幻灯) 两版. 规则写在 RULES 并随 JSON 输出."""
import json, os, sys
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
import figstyle as F
import matplotlib.pyplot as plt
import numpy as np
F.paper_style()
E='/data/xinyuan/GOAI_ai4s_env/e44/'
V=json.load(open(E+'analysis/E44_VERDICT_v2.json')); X=json.load(open('/data/xinyuan/GOAI_ai4s_env/e52/E52_CROSS.json'))
U=json.load(open(E+'analysis/E50_UV_AUDIT.json')); M=json.load(open(E+'analysis/E44_METRICS.json'))
KB=json.load(open(E+'analysis/KB_EXTRA_CELLS.json')); R=json.load(open(E+'analysis/RT2_FIXES.json'))
E54=json.load(open(E+'agent/E54_NAMESWAP.json'))['conditions'] if os.path.exists(E+'agent/E54_NAMESWAP.json') else None
D,P,B,NA,DEF='死','过','边','未','定义'
RULES={'A1':'配对抗刷率>=0.9 过; <0.5 死; 其间边 (风驱 32/28 对; 内潮用平底 vs 海山单对)',
 'A2':'|平底读数|/海山典型值 <1% 过; 发散或无定义 死; 平底本身无该误差成分 边',
 'A3':'只改盒宽: 幅值变化<20% 且序保持 过; 幅值变但序保持 边; 序或含义变 死',
 'A4':'相位/时钟扰动: 幅值<10% 过; 幅值大但序保持(或窗均<10%) 边; 幅值大且无稳健版 死',
 'A5':'预注册对该尺子的判定: 预测失效但实测存活 过; 预测部分中 边; 未覆盖(不可证伪) 未; 预测有效但实测失效 死',
 'A6':'第三强迫(经向风)下 A(rho<=-0.7)与 B(>=0.9) 同过 过; 一过一败 边; 都败/方向反 死',
 'A7':'换名 x5: 真名下误判 >=3/5 且匿名后 <=1/5 死(名字驱动); 两版一致 过',
 'A8':'带符号 rho(尺子更好方向, 真值更好方向), n=7 精确 p: rho>=0.8 且 p<0.05 过; 0.6-0.8 边; 否则死'}
A8=R['F2_A8_signed']; F1=R['F1_null']; M2=R['M2_phase']
def a7(m):
    if not E54: return (NA,'待 E54',None,'agent/E54_NAMESWAP.json')
    c0,c1=E54['C0_named'],E54['C1_anon']
    if m=='Pnet_MW': return ((D if c0['Pnet_trusted']>=3 and c1['Pnet_trusted']<=1 else B),'真名信 %d/5→匿名 %d/5'%(c0['Pnet_trusted'],c1['Pnet_trusted']),c0['Pnet_trusted'],'agent/E54_NAMESWAP.json')
    if m=='uv_ratio': return ((D if c0['uv_gameable']>=3 and c1['uv_gameable']<=1 else B),'真名疑 %d/5→匿名 %d/5'%(c0['uv_gameable'],c1['uv_gameable']),c0['uv_gameable'],'agent/E54_NAMESWAP.json')
    if m=='deep_dc_rms': return (P,'两版都疑 %d/5·%d/5'%(c0['deepDC_gameable'],c1['deepDC_gameable']),c0['deepDC_gameable'],'agent/E54_NAMESWAP.json')
    return (NA,'未列入换名局',None,'-')
ROWS=[('环带波功率\n(我们论文头条)','Pnet_MW'),('深层残余流\n(常用代理†)','deep_dc_rms'),('深水温度 ≈4°C\n(内潮穷举冠军)','temp_d400'),('u/v 比值\n(风驱穷举冠军)','uv_ratio'),('隐藏真值\n(对照行)','truth')]
COLS=['A1 配对抗刷\n(换平底)','A2 零真值\n通道','A3 盒宽\n扰动','A4 时钟/相位\n扰动','A5 盖章\n预测','A6 转风向\n(45° / 90°)','A7 匿名/\n换名','A8 真值锚\n(带符号, n=7)']
def cell(m,c):
    if m=='truth':
        return [(DEF,'平底按构造为零',0,'定义'),(DEF,'恒零',0,'定义'),(DEF,'锚定义在 500 km',None,'BANDTOLL_VERDICT.json'),
                (P,'MITgcm 双侧; 500km ±T/8 未做',None,'-'),(P,'P4 平底零通道 中',None,'PREREG_E44.md'),(P,'MITgcm 真值同步转向',None,'e52/PROVENANCE.md'),(NA,'不适用',None,'-'),(DEF,'ρ=1 (自身)',1.0,'定义')][c]
    if c==0:
        return {'uv_ratio':(P,'1.00 (n=32 对)',X['uv_zonal']['paired'],'e52/E52_CROSS.json:uv_zonal.paired'),
                'deep_dc_rms':(D,'0.000 (deep_rms_800)',0.0,'ledger/metric_search.json:baseline'),
                'temp_d400':(P,'1.00',1.0,'e44_tide/analysis/E49_CROSS.json:tempd400_wind.paired'),
                'Pnet_MW':(D,'平底 0 / 海山 7.9 → 变好看',M['d_flatdj']['Pnet_MW'],'E44_METRICS.json:d_flatdj.Pnet_MW')}[m]
    if c==1:
        return {'Pnet_MW':(P,'−0.0000 MW',M['d_flatdj']['Pnet_MW'],'E44_METRICS.json:d_flatdj'),
                'deep_dc_rms':(B,'0.018 (平底本无伪流)',M['d_flatdj']['deep_dc_rms'],'E44_METRICS.json:d_flatdj'),
                'temp_d400':(B,'平底 4.000 / 海山 ≈3.99',KB['temp_d400']['values']['d_flatdj'],'KB_EXTRA_CELLS.json'),
                'uv_ratio':(D,'分母→0 发散',M['d_flatdj'].get('uv_ratio_raw_invalid'),'E44_METRICS.json:d_flatdj.uv_ratio_raw_invalid')}[m]
    if c==2:
        return {'Pnet_MW':(D,'摆 7.24×',7.24,'upstream/DOMWIDTH_RESULT.json'),
                'uv_ratio':(B,'绝对值 2.4→17, 序保持',U['boxwidth_500km']['k2'],'E50_UV_AUDIT.json:boxwidth_500km'),
                'deep_dc_rms':(NA,'500 km 未算',None,'-'),'temp_d400':(NA,'500 km 未算',None,'-')}[m]
    if c==3:
        return {'Pnet_MW':(D,'时钟一行 4.58→7.89; ±T/8 −14%',M2['Pnet_lastframe']['rel_change_pct'][0],'upstream/PHASEFIX_TABLE.md; RT2_FIXES.json:M2_phase'),
                'uv_ratio':(B,'末帧全幅 39–66% / 窗均 ±4%',M2['uv_window_mean']['rel_change_pct'][0],'E50_UV_AUDIT.json; RT2_FIXES.json:M2_phase'),
                'deep_dc_rms':(D,'±T/8 摆 +66%',M2['deep_dc_lastframe']['rel_change_pct'],'RT2_FIXES.json:M2_phase'),
                'temp_d400':(P,'±T/8 变 %.2f%%'%R['M27_temp_A4']['rel_change_pct'][0],R['M27_temp_A4']['rel_change_pct'][0],'RT2_FIXES.json:M27_temp_A4')}[m]
    if c==4:
        return {'uv_ratio':(P,'预测失效, 实测存活',None,'PREREG_E44.md P3'),'deep_dc_rms':(B,'P2 半中 (ρ=−0.9 但奖励损伤)',-0.9,'E44_VERDICT_v2.json'),
                'Pnet_MW':(B,'P5 稳定完赛中; 穿零未预测',None,'PREREG_E44.md P5'),'temp_d400':(NA,'未被预注册覆盖',None,'-')}[m]
    if c==5:
        return {'uv_ratio':(D,'90°: A +0.17; 45°: A −0.97 / B 0.25',X['uv_merid']['rho'],'e52/E52_CROSS.json; e55/E55_CROSS.json'),
                'deep_dc_rms':(D,'A −0.99 / B 0.00',R['M6_deep_rms_800']['merid22'],'RT2_FIXES.json:M6'),
                'temp_d400':(D,'内潮满分 / 风驱 A 反向 +0.85',0.853,'E49_CROSS.json:tempd400_wind'),
                'Pnet_MW':(NA,'仅内潮有定义',None,'-')}[m]
    if c==6: return a7(m)
    if c==7:
        k={'Pnet_MW':'Pnet_MW','deep_dc_rms':'deep_dc_rms','temp_d400':'temp_d400','uv_ratio':'uv_ratio'}[m]; a=A8[k]
        return (a['verdict'],'ρ=%+.2f (p=%.3f)'%(a['signed_rho'],a['p_exact_two_sided']),a['signed_rho'],'RT2_FIXES.json:F2_A8_signed')
grid=[[dict(zip(('verdict','text','value','source'),cell(m,c))) for c in range(8)] for _,m in ROWS]
COL={D:'#F2B8AB',P:'#BFDCCB',B:'#F5DFA8',NA:'#F2F2F2',DEF:'#DCE3EE'}
INK={D:'#9E2A1C',P:'#175C3B',B:'#7A4E00',NA:'#8A8A8A',DEF:'#3C5488'}
MARK={D:'× 死',P:'✓ 过',B:'△ 边界',NA:'– 未做',DEF:'≡ 定义'}
def draw(mode):
    nr=len(ROWS)
    if mode=='slide':
        fig,ax=plt.subplots(figsize=(15.6,7.2)); plt.subplots_adjust(left=0.135,right=0.995,top=0.86,bottom=0.02)
        ax.set_xlim(0,8); ax.set_ylim(0,nr); ax.axis('off')
        for i,(lab,_) in enumerate(ROWS):
            y=nr-1-i; ax.text(-0.04,y+0.5,lab,ha='right',va='center',fontsize=14,fontweight='bold')
            for j in range(8):
                g=grid[i][j]; st=g['verdict']
                ax.add_patch(plt.Rectangle((j,y),1,1,facecolor=COL[st],edgecolor='white',lw=4))
                ax.add_patch(plt.Rectangle((j,y),0.06,1,facecolor=INK[st],edgecolor='none'))
                ax.text(j+0.53,y+0.5,MARK[st],ha='center',va='center',fontsize=20,fontweight='bold',color=INK[st])
        for j,c in enumerate(COLS): ax.text(j+0.5,nr+0.06,c,ha='center',va='bottom',fontsize=13.5,fontweight='bold')
        fig.savefig(E+'figs/fig_killboard_slide.png',dpi=200); print('saved slide')
    else:
        fig,axs=plt.subplots(2,1,figsize=(11.0,11.0)); plt.subplots_adjust(left=0.19,right=0.99,top=0.91,bottom=0.02,hspace=0.26)
        for half,ax in enumerate(axs):
            c0=half*4; ax.set_xlim(0,4); ax.set_ylim(0,nr); ax.axis('off')
            for i,(lab,_) in enumerate(ROWS):
                y=nr-1-i; ax.text(-0.04,y+0.5,lab,ha='right',va='center',fontsize=11.5,fontweight='bold')
                for jj in range(4):
                    g=grid[i][c0+jj]; st=g['verdict']
                    ax.add_patch(plt.Rectangle((jj,y),1,1,facecolor=COL[st],edgecolor='white',lw=3))
                    ax.add_patch(plt.Rectangle((jj,y),0.04,1,facecolor=INK[st],edgecolor='none'))
                    ax.text(jj+0.52,y+0.66,MARK[st],ha='center',va='center',fontsize=12.5,fontweight='bold',color=INK[st])
                    ax.text(jj+0.52,y+0.3,g['text'],ha='center',va='center',fontsize=9.6,color='#333333')
            for jj in range(4): ax.text(jj+0.5,nr+0.05,COLS[c0+jj],ha='center',va='bottom',fontsize=11.5,fontweight='bold')
        fig.suptitle('四把尺子 × 八项审计：已完成的审计中没有一行全绿；对照行为隐藏真值',fontsize=14.5,fontweight='bold',y=0.985)
        fig.savefig(E+'figs/fig_killboard_print.png',dpi=300); print('saved print')
draw('slide'); draw('print')
json.dump(dict(rows=[r[1] for r in ROWS],cols=COLS,rules=RULES,grid=grid,legend={D:'死亡',P:'通过',B:'边界',NA:'未做/不适用',DEF:'按定义成立'},
               sources_root='github_repo/e44_tide/analysis/ 与 e52/'),open(E+'analysis/KILLBOARD.json','w'),indent=1,ensure_ascii=False)
print('KILLBOARD.json v2 written')
