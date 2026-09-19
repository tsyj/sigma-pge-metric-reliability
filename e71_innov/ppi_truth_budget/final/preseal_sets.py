#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""ppi_truth_budget 封存前集合尺寸核对（V7 的依据；入封存哈希）。
只读：ledger/env2_runs.jsonl 的元数据字段（run_id/bathy/ntimes/action/obs.valid）、
regraded_v2.jsonl 的 run_id 键（不取 err_rms / skill 数值）、runs/<rid>/out_his.nc 是否存在。
不调用 base_quantities、不调用 grade、不读任何真值场、不读任何代理读数。输出 PRESEAL_SETS.json。"""
import os, json
ENV='/data/xinyuan/GOAI_ai4s_env'
FINAL=f'{ENV}/e71_innov/ppi_truth_budget/final'
KNOB=('VISC2','VISC4','AKV_BAK','TNU2'); SIMPLE={'bathy','VISC2','ntimes','seed'}
rows={}; dup=0; dup_diff=0
for l in open(f'{ENV}/ledger/env2_runs.jsonl'):
    r=json.loads(l); rid=r['run_id']
    if rid in rows:
        dup+=1; o=rows[rid]
        if (o['bathy'],o['ntimes'],json.dumps(o['action'],sort_keys=True),bool(o['obs'].get('valid'))) != \
           (r['bathy'],r['ntimes'],json.dumps(r['action'],sort_keys=True),bool(r['obs'].get('valid'))):
            dup_diff+=1
    rows[rid]=r
reg=set()
for l in open(f'{ENV}/ledger/regraded_v2.jsonl'):
    reg.add(json.loads(l)['run_id'])
has=lambda rid: os.path.exists(f'{ENV}/runs/{rid}/out_his.nc')
simple=lambda r: set(r['action'].keys())<=SIMPLE
U=sorted(k for k,r in rows.items() if r['obs'].get('valid') and r['ntimes']==8640 and r['bathy']=='r26steep' and k in reg and has(k))
Uset=set(U)
BV=sorted(k for k,r in rows.items() if r['bathy']=='r26steep' and r['obs'].get('valid') and r['ntimes']==8640 and simple(r) and r['action'].get('VISC2',0.0)>3000.0)
BS=sorted(k for k,r in rows.items() if r['bathy']=='r26steep' and r['obs'].get('valid') and r['ntimes']<8640 and simple(r) and r['action'].get('VISC2',0.0)<=2747.0)
byp={}
for k,r in rows.items():
    if not (r['obs'].get('valid') and r['ntimes']==8640): continue
    byp.setdefault(tuple(round(r['action'].get(x,-1),6) for x in KNOB),{})[r['bathy']]=k
pairs=[(v['r26steep'],v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
BT=sorted({b for _,b in pairs})
full_keys={}
for k in U:
    r=rows[k]
    if simple(r): full_keys.setdefault((round(r['action'].get('VISC2',0.0),6), r['action'].get('seed')),[]).append(k)
bs_rows=[]
for k in BS:
    r=rows[k]; key=(round(r['action'].get('VISC2',0.0),6), r['action'].get('seed'))
    bs_rows.append({'run_id':k,'ntimes':r['ntimes'],'VISC2':r['action'].get('VISC2'),'seed':r['action'].get('seed'),
                    'out_his_exists':has(k),'matched_full_in_U':key in full_keys})
ref50=[k for k in U if simple(rows[k]) and round(rows[k]['action'].get('VISC2',0.0),6)==50.0]
U_visc_gt3000=[k for k in U if rows[k]['action'].get('VISC2',0.0)>3000.0]
res={'note':'封存前元数据核对；U_meta 以 out_his.nc 存在近似 base_quantities 成功（真实 U 由封存后管线确定）',
 'ledger_dup_lines':dup,'ledger_dup_with_differing_meta':dup_diff,
 'n_U_meta':len(U),
 'B_V':[{'run_id':k,'VISC2':rows[k]['action'].get('VISC2'),'in_U_meta':k in Uset,'out_his_exists':has(k)} for k in BV],
 'n_B_V':len(BV),'B_V_subset_of_U_meta':all(k in Uset for k in BV),
 'n_U_meta_visc2_gt3000_any_action':len(U_visc_gt3000),
 'n_pairs':len(pairs),'n_B_T':len(BT),'n_B_T_out_his':sum(has(b) for b in BT),
 'n_pairs_steep_arm_in_U_meta':sum(s in Uset for s,_ in pairs),
 'n_B_S':len(BS),'n_B_S_out_his':sum(x['out_his_exists'] for x in bs_rows),
 'n_B_S_matched_with_out_his':sum(x['out_his_exists'] and x['matched_full_in_U'] for x in bs_rows),
 'B_S':bs_rows,'n_ref_visc50_simple_in_U_meta':len(ref50)}
json.dump(res,open(f'{FINAL}/PRESEAL_SETS.json','w'),indent=1,ensure_ascii=False)
print(json.dumps(res,ensure_ascii=False,indent=1))
