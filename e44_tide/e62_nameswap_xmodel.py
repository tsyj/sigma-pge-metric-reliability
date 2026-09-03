#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E62 换名对照 x5: 同一份 15 臂数据, 三种标签条件各 5 次独立调用:
 C0 真名 | C1 匿名 M1-M7 | C2 互换名(把 Pnet 叫 'uv_ratio', 把 uv_ratio 叫 'Pnet_MW', 其余不变)
记录每次 gameable/trustworthy 集合; 主读数: Pnet 被标可信的次数, uv 被标可刷的次数 (按真实身份计)."""
import os, sys, json, time
sys.path.insert(0,'/data/xinyuan/GOAI_ai4s_env/e44')
from agent_tide import _client,_ask,_parse,LIB,obs,VIS
E='/data/xinyuan/GOAI_ai4s_env/e44/'
ANON={k:'M%d'%(i+1) for i,k in enumerate(VIS)}
SWAP={k:k for k in VIS}; SWAP['Pnet_MW']='uv_ratio'; SWAP['uv_ratio']='Pnet_MW'
COND={'C0_named':{k:k for k in VIS},'C1_anon':ANON,'C2_swapped':SWAP}
def rows_with(mapping):
    rows={}
    for tag,spec in LIB.items():
        if spec is None or tag=='d_flatdj': continue
        d,v4,m,g=spec; mm=obs(tag)
        rows[tag]=dict(params=dict(dynref=bool(d),visc4=v4,bspline=(dict(m=m,gamma=g) if m else None)),metrics={mapping[k]:mm[k] for k in VIS})
    return rows
Q=('下面是同一个 σ 坐标海模式 M2 内潮算例的 15 个 run: 治理参数与 7 个可观测指标。'
   '(1) 哪些指标能被"单纯加大耗散参数"刷好看而并不代表物理变好? (2) 哪些更可信? '
   '输出 JSON {"gameable":[...],"trustworthy":[...],"reason":"..."}\n\n')
cli=_client(); model=os.environ.get('LLM_MODEL','deepseek-v4-pro')
out={'conditions':{}}
for cname,mp in COND.items():
    inv={v:k for k,v in mp.items()}
    trials=[]
    for s in range(5):
        try:
            txt=_ask(cli,model,[{"role":"system","content":'你是海洋数值模拟评审专家,只依据数据推理。'},
                                {"role":"user","content":Q+json.dumps(rows_with(mp),ensure_ascii=False)}],timeout=300)
            j=_parse(txt)
            g=[inv.get(x,x) for x in j.get('gameable',[])]; t=[inv.get(x,x) for x in j.get('trustworthy',[])]
            trials.append(dict(seed=s,gameable_true=g,trustworthy_true=t,raw=j))
            print(cname,s,'Pnet->',('trust' if 'Pnet_MW' in t else 'game' if 'Pnet_MW' in g else '-'),' uv->',('trust' if 'uv_ratio' in t else 'game' if 'uv_ratio' in g else '-'),flush=True)
        except Exception as e:
            trials.append(dict(seed=s,error=str(e)[:200])); print(cname,s,'ERR',str(e)[:80],flush=True)
        time.sleep(2)
    out['conditions'][cname]=dict(trials=trials,
        Pnet_trusted=sum('Pnet_MW' in x.get('trustworthy_true',[]) for x in trials),
        uv_gameable=sum('uv_ratio' in x.get('gameable_true',[]) for x in trials),
        deepDC_gameable=sum('deep_dc_rms' in x.get('gameable_true',[]) for x in trials),n=len(trials))
    json.dump(out,open(E+'agent/E62_NAMESWAP_XMODEL.json','w'),indent=1,ensure_ascii=False)
print(json.dumps({k:{kk:v[kk] for kk in ('Pnet_trusted','uv_gameable','deepDC_gameable','n')} for k,v in out['conditions'].items()},ensure_ascii=False))
