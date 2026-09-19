#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E71G · 封存后探索性补充（非预注册、不改判）：A2b 记录索引修正后的一步场对拍。
口径见 DEVIATIONS.md D1（先写口径后计算）：统计量与 e71g_scan.py A2b 逐字相同；主读数 = ocean_time 相对 DSTART 为 +DT 的记录。
只读 clone_1step/out_dia.nc 与 E56 v0 输入；输出 POSTHOC_A2B.json。"""
import hashlib, json, sys, time
import numpy as np
import netCDF4 as nc
FIN = "/data/xinyuan/GOAI_ai4s_env/e71_innov/mms_operator/final"
V0 = "/data/xinyuan/GOAI_ai4s_env/e56/runs/bh93_r26steep_v0"
sys.path.insert(0, FIN)
import e71g_replica as RP
DT, T0SEC = 10.0, 730119 * 86400.0
IN3 = (slice(None), slice(1, -1), slice(1, -1))

def ds(p):
    d = nc.Dataset(p); d.set_auto_mask(False); return d

g = ds(f"{V0}/pge_grid_r26steep.nc"); h = np.asarray(g["h"][:], dtype=np.float64); dx = float(1.0 / np.asarray(g["pm"][:]).mean()); g.close()
d = ds(f"{V0}/ini_rest_r26steep.nc"); T = np.asarray(d["temp"][0], dtype=np.float64); d.close()
z_r, z_w, Hz = RP.set_depth_v2(h)
au, av = RP.prsgrd31_sdj(RP.rho_linear_eos(T), z_r, z_w, Hz, dx, dx)
Hzu, Hzv = RP.hz_u(Hz), RP.hz_v(Hz)
devu, devv = au - RP.colmean(au, Hzu)[None], av - RP.colmean(av, Hzv)[None]

def npat(a, b):
    ai, bi = a[IN3], b[IN3]
    ma, mb = np.max(np.abs(ai)), np.max(np.abs(bi))
    if ma == 0 or mb == 0:
        return None
    return float(np.max(np.abs(ai / ma - bi / mb)))

d = ds(f"{FIN}/clone_1step/out_dia.nc")
ot = np.asarray(d["ocean_time"][:], dtype=np.float64)
recs = []
for r in range(len(ot)):
    up = np.asarray(d["u_prsgrd"][r], dtype=np.float64); vp = np.asarray(d["v_prsgrd"][r], dtype=np.float64)
    dup, dvp = up - RP.colmean(up, Hzu)[None], vp - RP.colmean(vp, Hzv)[None]
    mdu = float(np.max(np.abs(dup[IN3])))
    recs.append(dict(rec=r, t_rel_s=float(ot[r] - T0SEC), dtype=str(d["u_prsgrd"].dtype),
                     max_abs_u_prsgrd_interior=float(np.max(np.abs(up[IN3]))),
                     pat_dev_linf_u=npat(devu, dup), pat_dev_linf_v=npat(devv, dvp),
                     pat_raw_linf_u=npat(au, up), pat_raw_linf_v=npat(av, vp),
                     scale_dev_u=mdu / float(np.max(np.abs(devu[IN3]))),
                     scale_dev_v=float(np.max(np.abs(dvp[IN3]))) / float(np.max(np.abs(devv[IN3]))),
                     corr_dev_u=(float(np.corrcoef(devu[IN3].ravel(), dup[IN3].ravel())[0, 1]) if mdu > 0 else None)))
d.close()
prim = [x for x in recs if abs(x["t_rel_s"] - DT) < 1e-6]
P = prim[0] if len(prim) == 1 else None
out = dict(label="封存后探索性补充（非预注册、不改判；DEVIATIONS.md D1）", date=time.strftime("%F %T %z"),
           code_sha256=hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
           replica_sha256=hashlib.sha256(open(f"{FIN}/e71g_replica.py", "rb").read()).hexdigest(),
           records=recs, primary_rec=(None if P is None else P["rec"]),
           exploratory_le_1e3=(None if P is None or P["pat_dev_linf_u"] is None or P["pat_dev_linf_v"] is None
                               else bool(P["pat_dev_linf_u"] <= 1e-3 and P["pat_dev_linf_v"] <= 1e-3)))
json.dump(out, open(f"{FIN}/POSTHOC_A2B.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
