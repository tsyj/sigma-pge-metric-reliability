# -*- coding: utf-8 -*-
"""登记锚：把现算结果与已封存/已登记的产物逐位对账（selftest 与 counts 共用）。

- E65_AXES.npz：纬向 15376 候选的 A/B/D/G 登记轴（无名字，顺序与 full_space 枚举顺序相同，
  该顺序等同性本身由逐候选 max|Δ|=0 验证）；
- E67B_RECIPE_TRANSFER.json：S_A=204、S_AP=444、经向存活 88/0、45° 存活 140/0、三向 80/0。
"""
import hashlib
import os

import numpy as np

from . import REFERENCE_ROOT

E65_NPZ = os.path.join(REFERENCE_ROOT, "E65_AXES.npz")
E67B = os.path.join(REFERENCE_ROOT, "E67B_RECIPE_TRANSFER.json")


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def e65_full_anchor(fs_zonal, npz=None):
    """纬向全空间逐候选对账。返回 dict（含 ok）。"""
    npz = npz or E65_NPZ
    out = dict(source=npz)
    if not os.path.exists(npz):
        out.update(ok=False, error="E65_AXES.npz 不存在")
        return out
    z = np.load(npz)
    out["sha256"] = sha256_file(npz)
    out["n_registered"] = int(len(z["A"]))
    out["n_recomputed"] = int(len(fs_zonal["A"]))
    if len(fs_zonal["A"]) != len(z["A"]):
        out.update(ok=False, error="长度不符")
        return out
    for k in ("A", "B", "D"):
        out["max_abs_delta_%s" % k] = float(np.max(np.abs(fs_zonal[k] - z[k])))
    out["G_equal"] = bool(np.array_equal(fs_zonal["G"].astype(np.int64), z["G"].astype(np.int64)))
    out["ok"] = (out["max_abs_delta_A"] == 0.0 and out["max_abs_delta_B"] == 0.0
                 and out["max_abs_delta_D"] == 0.0 and out["G_equal"])
    return out


def e65_point(fs_zonal, name, npz=None):
    """取单个候选 (num, den) 在全空间枚举中的下标与 E65 登记值。"""
    npz = npz or E65_NPZ
    z = np.load(npz)
    i = fs_zonal["names"].index(name)
    return i, dict(A=float(z["A"][i]), B=float(z["B"][i]), D=float(z["D"][i]), G=int(z["G"][i]))


def e67b_checks(c, ref):
    """counts() 输出 vs E67B 登记。缺席环境对应条目记 None（不算绿也不算红，由调用方决定）。"""
    checks = {
        "n_zonal=15376": c["n_zonal"] == ref["n_zonal"] == 15376,
        "S_A=204": c["size_S_A"] == ref["size_S_A"] == 204,
        "S_AP=444": c["size_S_AP"] == ref["size_S_AP"] == 444,
    }
    if c.get("merid") is not None:
        checks["merid S_A 存活=88"] = c["merid"]["S_A_survive"] == ref["merid"]["S_A"]["n"] == 88
        checks["merid S_AP 存活=0"] = c["merid"]["S_AP_survive"] == ref["merid"]["S_AP"]["n"] == 0
    else:
        checks["merid S_A 存活=88"] = None
        checks["merid S_AP 存活=0"] = None
    if c.get("diag45") is not None:
        checks["diag45 S_A 存活=140"] = c["diag45"]["S_A_survive"] == ref["diag45"]["S_A"]["n"] == 140
        checks["diag45 S_AP 存活=0"] = c["diag45"]["S_AP_survive"] == ref["diag45"]["S_AP"]["n"] == 0
        checks["三向 S_A=80"] = c.get("triple_S_A") == ref["triple"]["S_A"] == 80
        checks["三向 S_AP=0"] = c.get("triple_S_AP") == ref["triple"]["S_AP"] == 0
    else:
        for k in ("diag45 S_A 存活=140", "diag45 S_AP 存活=0", "三向 S_A=80", "三向 S_AP=0"):
            checks[k] = None
    return checks
