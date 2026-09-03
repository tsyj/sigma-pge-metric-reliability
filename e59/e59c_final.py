#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E59c: 最终判读 + 图。含两次被数据推翻的事后解释，全部留档。"""
import json, sys
import numpy as np
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/scripts')
import figstyle as F
import matplotlib.pyplot as plt
G='/data/xinyuan/GOAI_ai4s_env/'
d=np.load(G+'e59/E59_ARRAYS.npz')
Xtr,Atr,Xte,Ate,s=d['Xtr'],d['Atr'],d['Xte'],d['Ate'],d['score_te']
y=(Ate>=0.7); base=float(y.mean())
# 等频分箱
NB=14; qs=np.unique(np.percentile(s,np.linspace(0,100,NB+1)))
cx=[];cy=[];cn=[]
for a,b in zip(qs[:-1],qs[1:]):
    m=(s>=a)&(s<b) if b<qs[-1] else (s>=a)&(s<=b)
    if m.sum()>=40: cx.append(float(np.median(s[m]))); cy.append(float(y[m].mean())); cn.append(int(m.sum()))
peak=int(np.argmax(cy))
res=json.load(open(G+'e59/E59_TRUTHFREE.json'))
res['posthoc_explanations_tested']=[
 {'hypothesis':'无真值特征只能预测判别力强度 |rho|，不能预测方向 sign(rho)',
  'test':'在 |A|>=0.7 的 8538 个测试候选里用无真值特征预测方向',
  'result':'AUC=0.9193，方向比强度(0.8128)更好预测','verdict':'被数据推翻'},
 {'hypothesis':'top-204 是训练分布之外的外推失败',
  'test':'检查 top-204 的 7 个特征是否落在训练集 1-99 分位内',
  'result':'7/7 全部在内，0 个外推','verdict':'被数据推翻'},
 {'hypothesis':'预测分与命中率是非单调(倒 U)关系：预测器自身在极端处失效',
  'test':'按预测分等频分箱看命中率',
  'result':'命中率从 0.037 单调升到 %.3f（score≈%.3f 处），随后在最高分区间跌至 %.3f'%(cy[peak],cx[peak],cy[-1]),
  'verdict':'与数据一致（本条为观察，不是独立检验）'}]
res['binned']=[{'score_median':round(a,5),'hit_rate':round(b,4),'n':c} for a,b,c in zip(cx,cy,cn)]
res['peak']={'score':round(cx[peak],5),'hit_rate':round(cy[peak],4),'n':cn[peak]}
res['tail']={'score':round(cx[-1],5),'hit_rate':round(cy[-1],4),'n':cn[-1]}
res['operational_reading']=('无真值特征对排得准的程度有实质预测力（跨环境 AUC=%.3f，中段命中率峰值 %.3f vs 基率 %.3f），'
  '但预测器自身在最高分区间失效（跌至 %.3f）。可操作的读法是取中段而非顶端；'
  '这也是本作品主题在我们自己的工具上的一次复现：一个有判别力的分数，推到极端同样会骗人。')%(
  res['multi']['auc_test'],cy[peak],base,cy[-1])
json.dump(res,open(G+'e59/E59_TRUTHFREE.json','w'),indent=1,ensure_ascii=False)
# 图
F.paper_style(); BLUE='#3C5488'; AMBER='#C46A1F'; RED='#B03A2E'; GRAY='#848D96'
fig,ax=plt.subplots(figsize=(9.6,6.0)); plt.subplots_adjust(left=0.11,right=0.97,top=0.87,bottom=0.13)
ax.axhline(base,color=GRAY,ls='--',lw=1.4)
ax.text(cx[0],base+0.018,'随便挑的比例 %.3f'%base,fontsize=11,color=GRAY)
ax.plot(cx,cy,'-o',color=BLUE,lw=2.4,ms=8,zorder=4)
ax.plot(cx[peak],cy[peak],'o',ms=15,mfc='none',mec=AMBER,mew=2.6,zorder=5)
ax.annotate('最高 %.3f\n(预测分≈%.3f, 共 %d 个)'%(cy[peak],cx[peak],cn[peak]),xy=(cx[peak],cy[peak]),
            xytext=(cx[peak]*0.9,cy[peak]-0.24),fontsize=11,color=AMBER,ha='center',
            arrowprops=dict(arrowstyle='->',color=AMBER,lw=1.4))
ax.plot(cx[-1],cy[-1],'o',ms=15,mfc='none',mec=RED,mew=2.6,zorder=5)
ax.annotate('预测分最高的那一段\n反而只有 %.3f'%cy[-1],xy=(cx[-1],cy[-1]),
            xytext=(cx[-1]*0.42,cy[-1]+0.30),fontsize=11,color=RED,ha='center',
            arrowprops=dict(arrowstyle='->',color=RED,lw=1.4))
ax.set_xscale('log'); ax.set_xlabel('不用真值算出的预测分（在一种风向上学，换到另一种风向上评；对数轴）')
ax.set_ylabel('这一段里真正排得准的比例')
ax.set_ylim(-0.03,1.0)
ax.set_title('不用真值也能预筛，但这个筛子在最极端处也会失灵\n换环境后仍有 AUC = %.3f；准确率升到 %.2f 后跌回 %.2f'%(
    res['multi']['auc_test'],cy[peak],cy[-1]),fontsize=13.5,fontweight='bold',pad=14)
fig.savefig(G+'e44/figs/fig_truthfree.png',dpi=300)
print('saved fig_truthfree.png')
print(res['operational_reading'])
