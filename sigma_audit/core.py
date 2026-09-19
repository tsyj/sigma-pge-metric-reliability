# -*- coding: utf-8 -*-
"""判定核心：A/B/D/A⊥ 轴、JudgmentRow、全空间计数。

秩相关与家族规则与 e67/e67b_recipe_transfer.py 逐字同口径（argsort-of-argsort 谱曼、
不做并列平均秩；分母列 EPS 剔除；乘性家族要求陡/平读数全为正）。
全空间循环刻意保持与 e67b 相同的逐候选写法，保证计数逐位可复现，不追求向量化。
"""
import time

import numpy as np

from . import GATE_A, GATE_B, SPUR_KEY, EPS


def spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    if np.std(ra) == 0 or np.std(rb) == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def _rank(x):
    o = np.argsort(np.argsort(x, kind="mergesort"), kind="mergesort").astype(float)
    return (o - o.mean()) / (o.std() + 1e-12)


def wilson_lb(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (c - r) / d


def axes_for_values(cache, v26, vfl, p26, pfl):
    """对一组已求值的读数向量计算 A/B/D/A⊥。任一臂缺读数则该轴为 None。"""
    out = dict(A=None, B=None, D=None, AP=None,
               n_steep=None, n_pairs=None, B_success=None)
    S = cache["S"]
    keys = cache["keys"]
    spur = cache["M26"][:, keys.index(SPUR_KEY)] if SPUR_KEY in keys else cache["M26"][:, 0]
    if v26 is not None:
        m = np.isfinite(v26) & np.isfinite(S)
        if m.sum() >= 8:
            out["A"] = -spearman(v26[m], S[m])
            out["n_steep"] = int(m.sum())
            sp = spur[m]
            out["D"] = spearman(v26[m], sp)
            rs = _rank(sp); rS = _rank(S[m]); rv = _rank(v26[m])
            S_res = rS - (rS @ rs) / (rs @ rs) * rs
            v_res = rv - (rv @ rs) / (rs @ rs) * rs
            out["AP"] = -float(np.corrcoef(v_res, S_res)[0, 1]) if v_res.std() > 1e-9 else 0.0
    if p26 is not None and pfl is not None:
        m = np.isfinite(p26) & np.isfinite(pfl)
        if m.sum() >= 8:
            succ = int((pfl[m] >= p26[m]).sum())
            out["B"] = succ / int(m.sum())
            out["B_success"] = succ
            out["n_pairs"] = int(m.sum())
    return out


def judge_env(cache, values, family_ok=True, family_note=""):
    """values = dict(v26=…, vfl=…, p26=…, pfl=…)；返回该环境的判定块。"""
    ax = axes_for_values(cache, values.get("v26"), values.get("vfl"),
                         values.get("p26"), values.get("pfl"))
    blk = dict(env=cache["env"], **{k: (round(v, 4) if isinstance(v, float) else v)
                                    for k, v in ax.items()})
    blk["wilson_lb_B"] = (round(wilson_lb(ax["B_success"], ax["n_pairs"]), 4)
                          if ax["B_success"] is not None else None)
    blk["gate_A"] = None if ax["A"] is None else bool(ax["A"] >= GATE_A)
    blk["gate_B"] = None if ax["B"] is None else bool(ax["B"] >= GATE_B)
    blk["two_gate_pass"] = (blk["gate_A"] and blk["gate_B"]) \
        if (blk["gate_A"] is not None and blk["gate_B"] is not None) else None
    blk["in_certified_family"] = bool(family_ok)
    if family_note:
        blk["family_note"] = family_note
    return blk


def verdict_from_blocks(blocks):
    """不合格/待定/两关通过——以纬向为判定臂（与认证口径一致），其余环境为适用域信息。"""
    z = blocks.get("zonal")
    if z is None:
        return "待定", ["无纬向判定臂缓存"]
    reasons = []
    if z["A"] is None or z["B"] is None:
        if z["A"] is None:
            reasons.append("A 不可测（陡臂读数缺失或常数）")
        if z["B"] is None:
            reasons.append("B 不可测（平底配对臂无该读数）；缺测时保留待定")
        return "待定", reasons
    if z["two_gate_pass"]:
        return "两关通过（纬向）", ["A=%.3f≥%.1f 且 B=%.3f≥%.1f" % (z["A"], GATE_A, z["B"], GATE_B)]
    if not z["gate_A"]:
        reasons.append("A=%.3f<%.1f：排得准关未过" % (z["A"], GATE_A))
    if not z["gate_B"]:
        reasons.append("B=%.3f<%.1f：平底配对零效应对照上变好看" % (z["B"], GATE_B))
    return "不合格", reasons


def judgment_row(metric_id, kind, blocks, elapsed_s, notes=None):
    v, reasons = verdict_from_blocks(blocks)
    return dict(metric=metric_id, kind=kind, verdict=v, reasons=reasons,
                envs=blocks, elapsed_s=round(elapsed_s, 2),
                notes=notes or [],
                semantics="判定语义限定在本环境族内（σ 伪流海山+平底孪生+三风向）；"
                          "『两关通过』不是通用有效性证书")


def full_space(cache):
    """全候选空间轴复算——与 e67b axes() 循环逐字同构，供计数复现与数据集导出。"""
    t0 = time.time()
    keys = cache["keys"]
    M26, MFL, P26, PFL, S = cache["M26"], cache["MFL"], cache["P26"], cache["PFL"], cache["S"]
    spur = M26[:, keys.index(SPUR_KEY)] if SPUR_KEY in keys else M26[:, 0]
    rs = _rank(spur); rS = _rank(S)
    S_res = rS - (rS @ rs) / (rs @ rs) * rs
    names, A, B, D, AP, G = [], [], [], [], [], []
    for i, kn in enumerate(keys):
        cand = [(kn, None, M26[:, i], MFL[:, i], P26[:, i], PFL[:, i], 1)]
        for j, kd in enumerate(keys):
            if i == j:
                continue
            if np.any(np.abs(M26[:, j]) < EPS) or np.any(np.abs(MFL[:, j]) < EPS) \
                    or np.any(np.abs(P26[:, j]) < EPS) or np.any(np.abs(PFL[:, j]) < EPS):
                continue
            cand.append((kn, keys[j], M26[:, i] / M26[:, j], MFL[:, i] / MFL[:, j],
                         P26[:, i] / P26[:, j], PFL[:, i] / PFL[:, j], 0))
        for kn_, kd_, v26, vfl, p26, pfl, g in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))):
                continue
            if np.any(v26 <= 0) or np.any(vfl <= 0):
                continue
            a = -spearman(v26, S)
            b = float((pfl >= p26).mean()) if len(p26) else 0.0
            rv = _rank(v26)
            v_res = rv - (rv @ rs) / (rs @ rs) * rs
            ap = -float(np.corrcoef(v_res, S_res)[0, 1]) if v_res.std() > 1e-9 else 0.0
            names.append((kn_, kd_)); A.append(a); B.append(b)
            D.append(spearman(v26, spur)); AP.append(ap); G.append(g)
    return dict(names=names, A=np.array(A), B=np.array(B), D=np.array(D),
                AP=np.array(AP), G=np.array(G, dtype=np.int8),
                elapsed_s=round(time.time() - t0, 1))


def counts(fs_by_env):
    """复现 e67/E67B_RECIPE_TRANSFER.json 的计数：S_A/S_AP 及跨向存活。"""
    z = fs_by_env["zonal"]
    idx = {n: i for i, n in enumerate(z["names"])}
    S_A = {n for n, i in idx.items() if z["A"][i] >= GATE_A and z["B"][i] >= GATE_B}
    S_AP = {n for n, i in idx.items() if z["AP"][i] >= GATE_A and z["B"][i] >= GATE_B}
    out = dict(n_zonal=len(z["names"]), size_S_A=len(S_A), size_S_AP=len(S_AP))

    def passes(fs, n, key):
        j = fs.get("_idx", None)
        if j is None:
            fs["_idx"] = j = {m: i for i, m in enumerate(fs["names"])}
        i = j.get(n)
        if i is None:
            return False
        arr = fs["A"] if key == "A" else fs["AP"]
        return bool(arr[i] >= GATE_A and fs["B"][i] >= GATE_B)

    for tag in ("merid", "diag45"):
        fs = fs_by_env.get(tag)
        if fs is None:
            out[tag] = None
            continue
        out[tag] = dict(
            S_A_survive=sum(1 for n in S_A if passes(fs, n, "A")),
            S_AP_survive=sum(1 for n in S_AP if passes(fs, n, "AP")),
            n_cand=len(fs["names"]))
    if fs_by_env.get("merid") is not None and fs_by_env.get("diag45") is not None:
        out["triple_S_A"] = sum(1 for n in S_A
                                if passes(fs_by_env["merid"], n, "A")
                                and passes(fs_by_env["diag45"], n, "A"))
        out["triple_S_AP"] = sum(1 for n in S_AP
                                 if passes(fs_by_env["merid"], n, "AP")
                                 and passes(fs_by_env["diag45"], n, "AP"))
    return out
