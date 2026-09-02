#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E60: 陡度轴上的抗刷率稳定性。造例逻辑沿用 env2.py step()（含 VISC2 回显自检），只换网格/初值。"""
import os, re, time, json, shutil, subprocess
import concurrent.futures as cf
import numpy as np, netCDF4 as nc
G='/data/xinyuan/GOAI_ai4s_env/'; E=G+'e60/'; BASE=G+'runs/r26_repro/'
BIN='coawstM_goai_v4'; RX=['020','044','060','069']; VISC2=[0.0,50.0,150.0,400.0,800.0,1500.0,2747.0]; NT=8640
def _fmt(v): return ('%g'%v) if v==int(v) else repr(v)
def one(rx,bathy,visc2):
    tag='rx%s_%s_v%g'%(rx,bathy,visc2); rd=E+'runs/'+tag; os.makedirs(rd,exist_ok=True)
    grd='grid_%s%s.nc'%(bathy,rx); ini='ini_%s%s.nc'%(bathy,rx)
    for s,d_ in ((E+grd,grd),(E+ini,ini),(G+'bin/'+BIN,BIN)):
        if not os.path.exists(rd+'/'+d_): shutil.copy2(s,rd+'/'+d_)
    os.chmod(rd+'/'+BIN,0o755)
    lines=[]
    for line in open(BASE+'ocean_r26_dj10.in',errors='replace'):
        k=line.split()[0] if line.split() else ''
        if k=='GRDNAME': line='     GRDNAME == %s\n'%grd
        elif k=='ININAME': line='     ININAME == %s\n'%ini
        elif k=='NTIMES': line='      NTIMES == %d\n'%NT
        elif k=='NHIS': line='        NHIS ==  %d\n'%max(1,NT//4)
        elif k in ('Lm','Mm'): line=re.sub(r'(==\s*)\d+',lambda m:m.group(1)+'40',line,count=1)  # 42x42 -> Lm=Mm=40
        elif k in ('HISNAME','RSTNAME','AVGNAME','DIANAME'): line='     %s == out_%s.nc\n'%(k,k[:3].lower())
        elif k=='VISC2': line=re.sub(r'(==\s*)\S+',r'\g<1>'+_fmt(visc2),line,count=1)
        lines.append(line)
    open(rd+'/roms.in','w').writelines(lines)
    seen=[l.partition('==')[2].partition('!')[0].split() for l in open(rd+'/roms.in',errors='replace') if l.split() and l.split()[0]=='VISC2']
    assert seen and all(x==_fmt(visc2) for x in seen[0]), ('VISC2 回显失败',seen)
    envv=dict(os.environ,PATH='/usr/bin:'+os.environ.get('PATH',''),
              LD_LIBRARY_PATH='/usr/lib/x86_64-linux-gnu:'+os.environ.get('LD_LIBRARY_PATH',''))
    open(rd+'/T_START','w').write(time.strftime('%F %T %z')); t0=time.time()
    with open(rd+'/run.log','w') as lg:
        subprocess.run(['./'+BIN,'roms.in'],cwd=rd,stdout=lg,stderr=subprocess.STDOUT,env=envv)
    open(rd+'/T_END','w').write(time.strftime('%F %T %z'))
    txt=open(rd+'/run.log',errors='replace').read()
    done='ROMS/TOMS: DONE' in txt; blow=('Blows up' in txt or 'BLOWUP' in txt or 'exit_flag: 1' in txt)
    o=dict(tag=tag,rx0=rx,bathy=bathy,VISC2=visc2,done=done,blowup=blow,wall=round(time.time()-t0,1))
    fn=rd+'/out_his.nc'
    if done and not blow and os.path.exists(fn):
        try:
            d=nc.Dataset(fn); u=np.asarray(d['u'][-1]); v=np.asarray(d['v'][-1]); nrec=d.dimensions['ocean_time'].size; d.close()
            o.update(nrec=nrec,u_max=float(np.abs(u).max()*100),u_rms=float(np.sqrt((u**2).mean())*100),
                     v_rms=float(np.sqrt((v**2).mean())*100),nan=int(np.isnan(u).sum()))
        except Exception as e: o['read_err']=str(e)[:120]
    return o
acts=[(rx,b,v) for rx in RX for b in ('steep','flat') for v in VISC2]
print('E60 陡度轴：%d 条'%len(acts),flush=True)
res=[]
with cf.ThreadPoolExecutor(max_workers=14) as ex:
    futs={ex.submit(one,*a):a for a in acts}
    for f in cf.as_completed(futs):
        try: r=f.result()
        except Exception as e:
            a=futs[f]; r=dict(tag='ERR_%s_%s_%g'%a,rx0=a[0],bathy=a[1],VISC2=a[2],done=False,blowup=False,error=str(e)[:160],wall=0)
        res.append(r); print('  %-24s done=%s blow=%s u_max=%s'%(r['tag'],r['done'],r['blowup'],
              ('%.4f'%r['u_max']) if 'u_max' in r else 'NA'),flush=True)
json.dump(res,open(E+'E60_RX0.json','w'),indent=1,ensure_ascii=False)
ok=sum(1 for r in res if r.get('done') and not r.get('blowup'))
print('\n完赛 %d/%d'%(ok,len(res)))
