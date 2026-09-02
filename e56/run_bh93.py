#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E56 BH93 静止态检验：无风、水平等密初值、真值解析为零。
造例逻辑逐字沿用 scripts/env2.py 的 step()（含配置回显自检），仅换二进制与初值。"""
import os, re, sys, json, time, shutil, subprocess, hashlib
import concurrent.futures as cf
import numpy as np, netCDF4 as nc
G='/data/xinyuan/GOAI_ai4s_env/'; E=G+'e56/'; P='/data/xinyuan/zpg_roms_dev/pge_test/'
BIN='coawstM_goai_rest'; BASE=G+'runs/r26_repro/'
GRD={'r26steep':'pge_grid_r26steep.nc','flat':'pge_grid_flat48_noN.nc'}
VISC2=[0.0,50.0,150.0,400.0,800.0,1500.0,2747.0]; NT=8640
def _fmt(v): return ('%g'%v) if v==int(v) else repr(v)
def one(bathy,visc2):
    tag='bh93_%s_v%g'%(bathy,visc2); rd=E+'runs/'+tag; os.makedirs(rd,exist_ok=True)
    grd=GRD[bathy]; ini='ini_rest_%s.nc'%bathy
    for s,d_ in ((P+grd,grd),(E+ini,ini),(G+'bin/'+BIN,BIN)):
        if not os.path.exists(rd+'/'+d_): shutil.copy2(s,rd+'/'+d_)
    os.chmod(rd+'/'+BIN,0o755)
    lines=[]
    for line in open(BASE+'ocean_r26_dj10.in',errors='replace'):
        k=line.split()[0] if line.split() else ''
        if k=='GRDNAME': line='     GRDNAME == %s\n'%grd
        elif k=='ININAME': line='     ININAME == %s\n'%ini
        elif k=='NTIMES': line='      NTIMES == %d\n'%NT
        elif k=='NHIS': line='        NHIS ==  %d\n'%max(1,NT//4)
        elif k in ('HISNAME','RSTNAME','AVGNAME','DIANAME'): line='     %s == out_%s.nc\n'%(k,k[:3].lower())
        elif k=='VISC2': line=re.sub(r'(==\s*)\S+',r'\g<1>'+_fmt(visc2),line,count=1)
        lines.append(line)
    open(rd+'/roms.in','w').writelines(lines)
    seen=[l.partition('==')[2].partition('!')[0].split() for l in open(rd+'/roms.in',errors='replace') if l.split() and l.split()[0]=='VISC2']
    assert seen and all(x==_fmt(visc2) for x in seen[0]), ('VISC2 回显失败',seen)
    envv=dict(os.environ,PATH='/usr/bin:'+os.environ.get('PATH',''),
              LD_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu:'+os.environ.get('LD_LIBRARY_PATH',''))
    open(rd+'/T_START','w').write(time.strftime('%F %T %z'))
    t0=time.time()
    with open(rd+'/run.log','w') as lg:
        subprocess.run(['./'+BIN,'roms.in'],cwd=rd,stdout=lg,stderr=subprocess.STDOUT,env=envv)
    open(rd+'/T_END','w').write(time.strftime('%F %T %z'))
    txt=open(rd+'/run.log',errors='replace').read()
    done='ROMS/TOMS: DONE' in txt; blow=('Blows up' in txt or 'BLOWUP' in txt or 'exit_flag: 1' in txt)
    o=dict(tag=tag,bathy=bathy,VISC2=visc2,done=done,blowup=blow,wall=round(time.time()-t0,1))
    fn=rd+'/out_his.nc'
    if done and not blow and os.path.exists(fn):
        d=nc.Dataset(fn); u=np.asarray(d['u'][-1]); v=np.asarray(d['v'][-1]); h=np.asarray(d['h'][:])
        Cs=np.asarray(d['Cs_r'][:]); nrec=d.dimensions['ocean_time'].size; d.close()
        hu=0.5*(h[:,:-1]+h[:,1:]); dep=-Cs[:,None,None]*hu[None]
        o.update(nrec=nrec, u_max=float(np.abs(u).max()*100), u_rms=float(np.sqrt((u**2).mean())*100),
                 v_max=float(np.abs(v).max()*100), surf_max=float(np.abs(u[-1]).max()*100),
                 deep_rms_800=float(np.sqrt((u[dep>800]**2).mean())*100) if (dep>800).any() else None,
                 uv_ratio=(float(np.sqrt((u**2).mean())*100)/float(np.abs(v).mean()*100)) if np.abs(v).mean()>1e-12 else None,
                 nan=int(np.isnan(u).sum()))
    return o
acts=[(b,v) for b in GRD for v in VISC2]
print('BH93 静止态：%d 条（真值解析为零）'%len(acts),flush=True)
with cf.ThreadPoolExecutor(max_workers=14) as ex:
    futs={ex.submit(one,*a):a for a in acts}
    res=[]
    for f in cf.as_completed(futs):
        try: res.append(f.result())
        except Exception as e: res.append(dict(tag='ERR_%s_%g'%futs[f],error=str(e)[:200],bathy=futs[f][0],VISC2=futs[f][1],done=False,blowup=False,wall=0))
json.dump(res,open(E+'E56_BH93.json','w'),indent=1,ensure_ascii=False)
for r in sorted(res,key=lambda r:(r['bathy'],r['VISC2'])):
    print('%-22s done=%s blow=%s  u_max=%8.4f  u_rms=%8.4f  deep800=%s  wall=%.0fs'%(
        r['tag'],r['done'],r['blowup'],r.get('u_max',-1),r.get('u_rms',-1),
        ('%.4f'%r['deep_rms_800']) if r.get('deep_rms_800') is not None else 'NA',r['wall']),flush=True)
