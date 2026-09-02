#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E48 -- 内潮环境的指标穷举（口径逐字继承 E40 metric_search.py 的候选空间）
基本量: 5 字段 x 8 区域 x 4 统计(末帧, cm 换算同 E40) + 配比 -> ~2 万候选
判据(内潮三轴, 全部在"Agent 可见"数据上):
  C1 节点距轴 m∈{2,3,4,5,6}: |Spearman|>=0.85
  C2 黏性轴 VISC4 8 档:  与 C1 同向, |rho|>=0.85
  C3 强度轴 gamma 7 档:  与 C1 同向, |rho|>=0.85
  约定方向: "损伤越重读数越高"记 +1(报警型), 越低记 -1(可刷型); 三轴须同向才 PASS
输出: 通过名单 + uv_ratio(=u|all|rms / v|all|mean_abs) 的排名
"""
import os, json, itertools, warnings
import numpy as np, netCDF4 as nc, glob
warnings.filterwarnings('ignore')
E44='/data/xinyuan/GOAI_ai4s_env/e44/'
PF='/data/xinyuan/zpg_roms_dev/pge_test/phasefix_20260829/'
FIELDS=("u","v","w","temp","zeta")
REGIONS=[("all",None),("d200",("deeper",200)),("d400",("deeper",400)),("d450",("deeper",450)),
         ("d800",("deeper",800)),("d1500",("deeper",1500)),("s50",("shallow",50)),("s200",("shallow",200))]

def base_quantities(run_dir):
    fns=sorted(glob.glob(run_dir+'/his*.nc'))
    if not fns: return None
    d=nc.Dataset(fns[0])
    h=np.asarray(d['h'][:]); Cs=np.asarray(d['Cs_r'][:])
    out={}
    for f in FIELDS:
        if f not in d.variables: continue
        arr=np.asarray(d[f][-1])
        scale=100.0 if f in ("u","v","w","zeta") else 1.0
        arr=arr*scale
        if arr.ndim==2: depth=np.zeros_like(arr)
        else:
            n=min(arr.shape[-1],h.shape[-1]); m=min(arr.shape[-2],h.shape[-2])
            arr=arr[...,:m,:n]; depth=-Cs[:,None,None]*h[None,:m,:n]
            if arr.shape[0]!=depth.shape[0]: arr=arr[:depth.shape[0]]
        for rname,rspec in REGIONS:
            if rspec is None: msk=np.ones_like(depth,dtype=bool)
            elif rspec[0]=="deeper": msk=depth>rspec[1]
            else: msk=depth<rspec[1]
            v=arr[msk]; v=v[np.isfinite(v)]
            if v.size==0: continue
            av=np.abs(v)
            out[f"{f}|{rname}|rms"]=float(np.sqrt((v**2).mean()))
            out[f"{f}|{rname}|max"]=float(av.max())
            out[f"{f}|{rname}|mean_abs"]=float(av.mean())
            out[f"{f}|{rname}|p95"]=float(np.percentile(av,95))
    d.close(); return out

def spearman(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    ra=np.argsort(np.argsort(a)); rb=np.argsort(np.argsort(b))
    ra=ra-ra.mean(); rb=rb-rb.mean()
    d=np.sqrt((ra**2).sum()*(rb**2).sum())
    return float((ra*rb).sum()/d) if d>0 else 0.0

AXES={
 'm':   [('b_bsplm2',2),('b_bsplm3',3),('pf_combo',4),('b_bsplm5',5),('b_bsplm6',6)],
 'visc':[('pf_v4',0),('a_v4visc3e6',3e6),('a_v4visc1e7',1e7),('a_v4visc3e7',3e7),
         ('a_v4visc5e7',5e7),('a_v4visc1e8',1e8),('a_v4visc2e8',2e8),('a_v4visc3e8',3e8)],
 'gam': [('c_g0p25',0.25),('c_g0p5',0.5),('pf_combo',1),('c_g2',2),('c_g4',4),('c_g8',8),('c_g16',16)]}

if __name__=='__main__':
    tags=set(t for ax in AXES.values() for t,_ in ax)
    B={}
    for t in sorted(tags):
        d=PF+t if t.startswith('pf_') else E44+'cases/'+t
        if not (t.startswith('pf_') or os.path.exists(d+'/DONE')):
            print('MISS',t); continue
        B[t]=base_quantities(d); print('base',t,len(B[t]))
    keys=sorted(set.intersection(*[set(v.keys()) for v in B.values()]))
    print('common base quantities:',len(keys))
    rows=[]
    cands=[(k,None) for k in keys]+[(kn,kd) for kn,kd in itertools.product(keys,keys) if kn!=kd]
    print('candidates:',len(cands))
    for kn,kd in cands:
        rr={}; ok=True
        for ax,pts in AXES.items():
            vals=[]
            for t,x in pts:
                if t not in B: ok=False; break
                num=B[t][kn]; den=B[t][kd] if kd else 1.0
                if kd and abs(den)<1e-12: ok=False; break
                vals.append(num/den)
            if not ok: break
            rr[ax]=spearman([x for _,x in pts],vals)
        if not ok: continue
        sgn=[np.sign(rr[a]) for a in ('m','visc','gam')]
        same=(sgn[0]!=0 and sgn[0]==sgn[1]==sgn[2])
        amin=min(abs(rr[a]) for a in ('m','visc','gam'))
        direction=int(sgn[0]) if same else 0
        rows.append(dict(num=kn,den=kd,rho_m=round(rr['m'],3),rho_visc=round(rr['visc'],3),
                         rho_gam=round(rr['gam'],3),same_dir=bool(same),direction=direction,
                         min_abs_rho=round(amin,3),
                         passed=bool(same and direction>0 and amin>=0.85),
                         gameable=bool(same and direction<0 and amin>=0.85)))
    rows.sort(key=lambda r:(-r['passed'],-r['min_abs_rho']))
    npass=sum(r['passed'] for r in rows)
    ngame=sum(r['gameable'] for r in rows)
    print('报警型 PASS:',npass,'  可刷型(同向负):',ngame,'  /',len(rows))
    uv=[i for i,r in enumerate(rows) if r['num']=='u|all|rms' and r['den']=='v|all|mean_abs']
    print('uv_ratio rank:',(uv[0]+1) if uv else 'n/a','of',len(rows),
          rows[uv[0]] if uv else '')
    json.dump(dict(n_candidates=len(rows),n_passed=npass,n_gameable=ngame,
                   uv_ratio_rank=(uv[0]+1) if uv else None,
                   uv_ratio_row=rows[uv[0]] if uv else None,
                   top50=rows[:50]),
              open(E44+'analysis/E48_SEARCH.json','w'),indent=1)
    print('wrote E48_SEARCH.json')
