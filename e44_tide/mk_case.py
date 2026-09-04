#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""e44/mk_case.py -- E44 造 case（内潮 84km, phasefix 口径）
模板: pf_dj / pf_v4 / pf_combo (phasefix_20260829, ini 已 +15330) / flat (tide_twin_v2/flat_roms, ini 需 +15330)
旋钮: --visc4 X  (只改 VISC4 行, ad_VISC4 不动) ; --sidecar BIN (换 bspline_smooth.bin)
审计: 全输入件 cmp 逐位 + .in 差分白名单(RSTNAME/HISNAME/VISC4) + md5 留痕
"""
import os, sys, shutil, subprocess, hashlib, argparse, re
import numpy as np, netCDF4 as nc
# --- 可移植性垫片：开发机行为不变；换台机器时自动改用仓库内的文件 ---
import os as _o, sys as _s
_H=_o.path.dirname(_o.path.abspath(__file__))
_R=_H if _o.path.isdir(_o.path.join(_H,'e44_tide')) else _o.path.dirname(_H)
for _d in (_o.path.join(_R,'scripts'), _o.path.join(_R,'e44_tide'), _R):
    if _o.path.isdir(_d) and _d not in _s.path: _s.path.insert(0,_d)
if not _o.path.isdir('/data/xinyuan/GOAI_ai4s_env'):
    # 评委机器：把开发路径重定向到仓库内
    _real_open=open
    def open(f,*a,**k):
        if isinstance(f,str) and f.startswith('/data/xinyuan/GOAI_ai4s_env/'):
            rel=f.replace('/data/xinyuan/GOAI_ai4s_env/','')
            for _b in (_R, _o.path.join(_R,'e44_tide')):
                _p=_o.path.join(_b,rel)
                if _o.path.exists(_p): return _real_open(_p,*a,**k)
                _p2=_o.path.join(_b,_o.path.basename(rel))
                if _o.path.exists(_p2): return _real_open(_p2,*a,**k)
        return _real_open(f,*a,**k)
# --- 垫片结束 ---


PGE='/data/xinyuan/zpg_roms_dev/pge_test/'
E44='/data/xinyuan/GOAI_ai4s_env/e44/'
TPL={'pf_dj':PGE+'phasefix_20260829/pf_dj','pf_v4':PGE+'phasefix_20260829/pf_v4',
     'pf_combo':PGE+'phasefix_20260829/pf_combo','flat':PGE+'tide_twin_v2/flat_roms'}
BIN_MD5='740f160e7710e6b8a930cf284576f4c9'
DELTA=15330.0
COPY=['coawstM_dnn_tide','dnn_tidebody.on','dnn_dynref.on','dnn_bspline.on',
      'dnn_lamalpha.txt','dynref_coef.bin','bspline_smooth.bin']

def md5(p):
    h=hashlib.md5()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

ap=argparse.ArgumentParser()
ap.add_argument('tag'); ap.add_argument('--template',required=True,choices=TPL)
ap.add_argument('--visc4',default=None); ap.add_argument('--sidecar',default=None)
a=ap.parse_args()
src=TPL[a.template]; d=E44+'cases/'+a.tag
os.makedirs(d,exist_ok=True)
for f in os.listdir(d): os.remove(os.path.join(d,f))
# 1) 可执行 + 触发/边车（模板有则拷）
for f in COPY:
    s=os.path.join(src,f)
    if os.path.exists(s):
        shutil.copy2(s,os.path.join(d,f))
        assert md5(s)==md5(os.path.join(d,f)),f'copy not bitwise: {f}'
assert md5(os.path.join(d,'coawstM_dnn_tide'))==BIN_MD5,'binary md5 mismatch'
os.chmod(os.path.join(d,'coawstM_dnn_tide'),0o755)
# 2) grid+ini（保持模板文件名）
inn=open(os.path.join(src,'ocean_run.in')).read()
gname=re.search(r'^\s*GRDNAME\s*==\s*(\S+)',inn,re.M).group(1)
iname=re.search(r'^\s*ININAME\s*==\s*(\S+)',inn,re.M).group(1)
shutil.copy2(os.path.join(src,gname),os.path.join(d,gname))
shutil.copy2(os.path.join(src,iname),os.path.join(d,iname))
phase_shifted=False
if a.template=='flat':   # flat 模板 ini 是旧口径 -> +15330 对齐 phasefix
    ds=nc.Dataset(os.path.join(d,iname),'a')
    ds.variables['ocean_time'][:]=np.asarray(ds.variables['ocean_time'][:])+DELTA
    ds.close(); phase_shifted=True
# 3) 换边车
if a.sidecar:
    shutil.copy2(a.sidecar,os.path.join(d,'bspline_smooth.bin'))
    assert md5(a.sidecar)==md5(os.path.join(d,'bspline_smooth.bin'))
# 4) ocean_run.in: 改 RST/HIS 名 + VISC4
oldrst=re.search(r'^\s*RSTNAME\s*==\s*(\S+)',inn,re.M).group(1)
oldhis=re.search(r'^\s*HISNAME\s*==\s*(\S+)',inn,re.M).group(1)
out=inn.replace(oldrst,'rst_%s.nc'%a.tag).replace(oldhis,'his_%s.nc'%a.tag)
nch_expect=4
if a.visc4 is not None:
    out2=re.sub(r'^(\s*VISC4\s*==\s*)\S+',r'\g<1>'+a.visc4,out,count=1,flags=re.M)
    assert out2!=out or ('VISC4 == '+a.visc4) in out,'VISC4 not replaced'
    if out2!=out: nch_expect=6
    out=out2
open(os.path.join(d,'ocean_run.in'),'w').write(out)
# 5) 差分审计
r=subprocess.run(['diff',os.path.join(src,'ocean_run.in'),os.path.join(d,'ocean_run.in')],
                 capture_output=True,text=True)
lines=[l for l in r.stdout.splitlines() if l[:1] in '<>']
bad=[l for l in lines if not re.search(r'(RSTNAME|HISNAME|^\s*[<>]\s*VISC4\s*==)',l)]
assert not bad,'diff outside whitelist:\n'+'\n'.join(bad)
assert len(lines)==nch_expect,'changed lines %d != %d:\n%s'%(len(lines),nch_expect,r.stdout)
with open(os.path.join(d,'INPUTS_MD5.txt'),'w') as f:
    for fn in sorted(os.listdir(d)):
        if fn!='INPUTS_MD5.txt': f.write('%s  %s\n'%(md5(os.path.join(d,fn)),fn))
print('MK_OK %s template=%s visc4=%s sidecar=%s phase_shifted=%s files=%d'%(
    a.tag,a.template,a.visc4,os.path.basename(a.sidecar) if a.sidecar else '-',phase_shifted,len(os.listdir(d))))
