#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E59b（事后分析，非预注册）：检验假说——无真值特征预测的是判别力强度 |rho|，不是方向 sign(rho)。"""
import json
import numpy as np
G='/data/xinyuan/GOAI_ai4s_env/'
d=np.load(G+'e59/E59_ARRAYS.npz')
Xtr,Atr,Xte,Ate=d['Xtr'],d['Atr'],d['Xte'],d['Ate']
def auc(y,s):
    y=np.asarray(y,bool); s=np.asarray(s,float)
    if y.sum()==0 or (~y).sum()==0: return np.nan
    us,inv,cnt=np.unique(s,return_inverse=True,return_counts=True)
    o=np.argsort(s); r=np.empty(len(s)); r[o]=np.arange(1,len(s)+1)
    sums=np.zeros(len(us)); np.add.at(sums,inv,r); r=(sums/cnt)[inv]
    n1=y.sum(); n0=(~y).sum()
    return float((r[y].sum()-n1*(n1+1)/2)/(n1*n0))
def fit(X,y,iters=4000,lr=0.12):
    mu,sd=X.mean(0),X.std(0)+1e-12; Z=np.hstack([(X-mu)/sd,np.ones((len(X),1))]); w=np.zeros(Z.shape[1]); yv=y.astype(float)
    for _ in range(iters):
        p=1/(1+np.exp(-np.clip(Z@w,-30,30))); w-=lr*(Z.T@(p-yv))/len(Z)
    return w,mu,sd
def apply_(X,w,mu,sd):
    return 1/(1+np.exp(-np.clip(np.hstack([(X-mu)/sd,np.ones((len(X),1))])@w,-30,30)))
NAMES=['f1 配对抗刷率','f2 平底噪声','f3 海山动态范围','f4 地形敏感度','f5 同分量','f6 深度层级差','f7 与旋钮秩相关']
out={'note':'事后分析(post-hoc)，非 PREREG_E59 的预注册内容；用于解释 P3 未命中的原因。'}
# 目标 1（预注册）: A>=0.7  目标 2（事后）: |A|>=0.7
for tag,ytr,yte in [('A>=0.7 (预注册目标)',Atr>=0.7,Ate>=0.7),
                    ('|A|>=0.7 (事后: 判别力强度)',np.abs(Atr)>=0.7,np.abs(Ate)>=0.7)]:
    w,mu,sd=fit(Xtr,ytr); s=apply_(Xte,w,mu,sd); a=auc(yte,s)
    o=np.argsort(-s); K=204
    prec=float(yte[o[:K]].mean()); base=float(yte.mean())
    out[tag]={'auc_test':round(a,4),'base_rate_test':round(base,4),
              'precision_at_204':round(prec,4),'lift':round(prec/base,3) if base>0 else None,
              'top1000_precision':round(float(yte[o[:1000]].mean()),4)}
    print('%-30s AUC=%.4f  基率=%.4f  p@204=%.4f (提升 %.2fx)  p@1000=%.4f'%(
        tag,a,base,prec,prec/base if base>0 else 0,float(yte[o[:1000]].mean())))
# 方向能不能预测？只在 |A|>=0.7 的候选里问 sign
m_tr=np.abs(Atr)>=0.7; m_te=np.abs(Ate)>=0.7
w2,mu2,sd2=fit(Xtr[m_tr],(Atr[m_tr]>0)); s2=apply_(Xte[m_te],w2,mu2,sd2)
a2=auc(Ate[m_te]>0,s2)
out['方向可预测性']={'auc_test':round(a2,4),'n_test':int(m_te.sum()),
    'pos_rate':round(float((Ate[m_te]>0).mean()),4),
    'meaning':'在已知判别力强(|A|>=0.7)的候选里，用无真值特征预测方向 sign(rho) 的 AUC。接近 0.5 即方向不可预测。'}
print('\n在 |A|>=0.7 的 %d 个候选里预测方向: AUC = %.4f （0.5 = 完全不可预测）'%(m_te.sum(),a2))
# 两阶段协议：无真值筛 top-N，再用少量真值定方向
base_all=float((Ate>=0.7).mean())
w3,mu3,sd3=fit(Xtr,np.abs(Atr)>=0.7); s3=apply_(Xte,w3,mu3,sd3); o3=np.argsort(-s3)
rows=[]
for N in (500,1000,2000,4000):
    sub=o3[:N]
    n_strong=int((np.abs(Ate[sub])>=0.7).sum()); n_good=int((Ate[sub]>=0.7).sum())
    rows.append(dict(N=N,strong=n_strong,strong_rate=round(n_strong/N,4),
                     good=n_good,good_rate=round(n_good/N,4),
                     recall_good=round(n_good/max(1,(Ate>=0.7).sum()),4)))
    print('  无真值筛 top-%-5d → 判别力强 %4d (%.1f%%)，其中方向正确 %4d (%.1f%%)，召回 %.1f%%'%(
        N,n_strong,100*n_strong/N,n_good,100*n_good/N,100*n_good/max(1,(Ate>=0.7).sum())))
out['两阶段协议']={'base_rate_good':round(base_all,4),'rows':rows,
  'reading':'第一阶段用无真值特征把 15376 缩到 top-N（判别力富集），第二阶段只对这 N 个做真值实验定方向。'}
json.dump(out,open(G+'e59/E59B_POSTHOC.json','w'),indent=1,ensure_ascii=False)
print('\n-> e59/E59B_POSTHOC.json')
