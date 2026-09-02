#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E61: Agent 在与逻辑回归完全相同的信息条件下挑尺子。预注册 sha 67d3ede0…"""
import os, sys, json, time, random
import numpy as np
from openai import OpenAI
G='/data/xinyuan/GOAI_ai4s_env/'; E=G+'e61/'
MODEL=os.environ.get('LLM_MODEL','deepseek-v4-pro')
cli=OpenAI(api_key=os.environ['LLM_API_KEY'],base_url=os.environ.get('LLM_BASE_URL','https://api.deepseek.com'),timeout=600,max_retries=0)
d=np.load(G+'e59/E59_ARRAYS.npz')
Xte,Ate,score=d['Xte'],d['Ate'],d['score_te']
NAMES=['配对抗刷率','平底噪声','海山动态范围','地形敏感度','是否同分量','深度层级差','与旋钮VISC2的秩相关']
# 候选名：从 e59 的构建顺序还原不可行，改用编号 + 特征（对 Agent 与对照完全对称）
N_SHOW=40; N_PICK=10; N_GAMES=8
q=np.percentile(score,[25,50,75])
strata=[np.where(score<=q[0])[0],np.where((score>q[0])&(score<=q[1]))[0],
        np.where((score>q[1])&(score<=q[2]))[0],np.where(score>q[2])[0]]
SYS=('你是数值海洋模式的评价方法学专家。有人给你一批"候选评价指标"，每个只给出若干**不依赖真值**的诊断特征。'
     '你的任务是判断哪些候选最可能与隐藏的真值有强的单调排序关系。只依据给出的数字推理，不要编造未给出的信息。')
def ask(rows,seed):
    lines=[]
    for i,r in enumerate(rows):
        lines.append('#%02d  '%i+'  '.join('%s=%.4g'%(n,v) for n,v in zip(NAMES,r)))
    usr=('下面是 %d 个候选评价指标，每个给出 7 个无真值诊断特征：\n\n'%len(rows)+'\n'.join(lines)+
         '\n\n特征含义：\n'
         '- 配对抗刷率：把同一组模式参数换到"误差按构造为零的平底地形"后，该候选读数不变好看的比例（0~1）。\n'
         '- 平底噪声：该候选在平底臂上的相对离散度（四分位距/中位数）。\n'
         '- 海山动态范围：该候选在陡海山臂上的相对离散度。\n'
         '- 地形敏感度：平底中位数 / 海山中位数（≈1 表示对地形不敏感）。\n'
         '- 是否同分量：分子分母是否取自同一个物理量（1 是，0 否）。\n'
         '- 深度层级差：分子与分母所取深度层级的编号差（0~5）。\n'
         '- 与旋钮VISC2的秩相关：该候选读数与一个已知的模式参数（水平粘性）的秩相关绝对值。\n\n'
         '请从中挑出 **%d 个** 你认为最可能与隐藏真值有强排序关系的候选。\n'
         '只输出 JSON：{"picks":[编号,...],"reason":"不超过 120 字，说明你主要依据哪些特征、方向如何"}'%N_PICK)
    for attempt in range(4):
        try:
            r=cli.chat.completions.create(model=MODEL,messages=[{"role":"system","content":SYS},{"role":"user","content":usr}],
                                          response_format={"type":"json_object"},max_tokens=16000)
            txt=r.choices[0].message.content or ''
            try: j=json.loads(txt)
            except Exception:
                import re as _re
                mm=_re.search(r'\{[^{}]*"picks"\s*:\s*\[[^\]]*\][^{}]*\}',txt,_re.S)
                if not mm: mm=_re.search(r'\{.*\}',txt,_re.S)
                if not mm: raise
                j=json.loads(mm.group(0))
            fr=getattr(r.choices[0],'finish_reason',None)
            def _toi(x):
                import re as _r
                mm=_r.search(r'\d+',str(x)); return int(mm.group(0)) if mm else -1
            picks=[_toi(x) for x in j.get('picks',[])][:N_PICK]
            if len(picks)>=1: return picks,j.get('reason','')[:400],txt
            print('    空 picks, finish_reason=%s, 文本前 120 字: %s'%(fr,(txt or '')[:120]),flush=True)
        except Exception as ex:
            print('    retry %d: %s'%(attempt,str(ex)[:90]),flush=True); time.sleep(4)
    return [],'',''
def play(seed):
    rng=np.random.default_rng(seed)
    idx=np.concatenate([rng.choice(s,10,replace=False) for s in strata]); rng.shuffle(idx)
    rows=Xte[idx]; A=Ate[idx]; sc=score[idx]; y=(A>=0.7)
    picks,reason,raw=ask(rows,seed)
    picks=[p for p in picks if 0<=p<len(idx)]
    agent_hit=float(y[picks].mean()) if picks else np.nan
    lr_top=np.argsort(-sc)[:N_PICK]; lr_hit=float(y[lr_top].mean())
    b_low=np.argsort(rows[:,0])[:N_PICK]; b_hit=float(y[b_low].mean())
    rnd=float(np.mean([y[rng.choice(len(idx),N_PICK,replace=False)].mean() for _ in range(200)]))
    orc=float(y.mean())
    g=dict(seed=seed,n_picks=len(picks),picks=picks,reason=reason,
        agent=None if np.isnan(agent_hit) else round(agent_hit,3),
        logistic=round(lr_hit,3),b_heuristic=round(b_hit,3),random=round(rnd,3),oracle_rate=round(orc,3))
    print('  局 %d: Agent %s | 逻辑回归 %.2f | 低B启发式 %.2f | 随机 %.2f | 本局正类率 %.2f'%(
        seed,('%.2f'%agent_hit) if not np.isnan(agent_hit) else 'FAIL',lr_hit,b_hit,rnd,orc),flush=True)
    with open(E+'trajectory_e61.jsonl','a') as f:
        f.write(json.dumps(dict(seed=seed,model=MODEL,picks=picks,reason=reason,raw=raw[:1500]),ensure_ascii=False)+'\n')
    return g
import concurrent.futures as _cf
with _cf.ThreadPoolExecutor(max_workers=4) as _ex:
    games=sorted(_ex.map(play,range(N_GAMES)),key=lambda g:g['seed'])
ok=[g for g in games if g['agent'] is not None]
def m(k): return float(np.mean([g[k] for g in ok])) if ok else float('nan')
summ=dict(prereg_sha='67d3ede0fe9b2645175b78192a5c5512018ab7f852107ef0199275af5cbb4254',model=MODEL,
    n_games=len(ok),agent=round(m('agent'),4),logistic=round(m('logistic'),4),
    b_heuristic=round(m('b_heuristic'),4),random=round(m('random'),4),oracle=round(m('oracle_rate'),4))
# 配对单侧检验（Agent vs 随机；Agent vs 逻辑回归）
def sign_p(a,b):
    dif=[x-y for x,y in zip(a,b)]; pos=sum(1 for x in dif if x>0); n=sum(1 for x in dif if x!=0)
    if n==0: return 1.0
    from math import comb
    return sum(comb(n,k) for k in range(pos,n+1))/2**n
A=[g['agent'] for g in ok]; R=[g['random'] for g in ok]; L=[g['logistic'] for g in ok]
summ['p_agent_gt_random_sign']=round(sign_p(A,R),4)
summ['p_agent_gt_logistic_sign']=round(sign_p(A,L),4)
summ['prereg_check']={'P1 Agent>随机 (p<0.05)':bool(summ['p_agent_gt_random_sign']<0.05 and summ['agent']>summ['random']),
                      'P2 Agent<逻辑回归':bool(summ['agent']<summ['logistic'])}
summ['games']=games
json.dump(summ,open(E+'E61_AGENT_PICKS.json','w'),indent=1,ensure_ascii=False)
print('\n均值: Agent %.3f | 逻辑回归 %.3f | 低B启发式 %.3f | 随机 %.3f | Oracle %.3f'%(
    summ['agent'],summ['logistic'],summ['b_heuristic'],summ['random'],summ['oracle']))
print('符号检验 p: Agent>随机 %.4f ; Agent>逻辑回归 %.4f'%(summ['p_agent_gt_random_sign'],summ['p_agent_gt_logistic_sign']))
for k,v in summ['prereg_check'].items(): print('  %-24s %s'%(k,'命中' if v else '未命中'))
