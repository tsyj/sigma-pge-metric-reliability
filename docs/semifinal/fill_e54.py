#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
import json
E='/data/xinyuan/GOAI_ai4s_env/e44/'; F='/home/xinyuan/比赛/赛道三赛题二/复赛/'
J=json.load(open(E+'agent/E54_NAMESWAP.json'))['conditions']
c0,c1,c2=J['C0_named'],J['C1_anon'],J['C2_swapped']
sent=('真名版 %d 次里 %d 次把环带功率标为可信、%d 次把 u/v 标为可刷；匿名版（M1–M7）分别降到 %d 次与 %d 次；'
      '把两者名字互换后，"环带功率"这个名字下的 u/v 数据被标可信 %d 次——判断跟着名字走，不跟着数据走。'
      '（残余流两版都被标可刷 %d/%d、%d/%d，说明模型并非乱答。）'%(
      c0['n'],c0['Pnet_trusted'],c0['uv_gameable'],c1['Pnet_trusted'],c1['uv_gameable'],c2['Pnet_trusted'],
      c0['deepDC_gameable'],c0['n'],c1['deepDC_gameable'],c1['n']))
p=F+'报告_v4_主文.md'; s=open(p).read()
assert '〔E54 k/5 数字回填〕' in s
s=s.replace('〔E54 k/5 数字回填〕',sent); open(p,'w').write(s); print('report filled:',sent)
