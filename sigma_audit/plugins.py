# -*- coding: utf-8 -*-
"""MetricPlugin 契约。

两种提交形态：
1) 比值表达式（推荐，评委随手写）：
     "u|d800|rms"                      单基元
     "u|d800|rms / temp|d800|rms"      比值
   基元名 = 场|区域|统计（124 个合法名见 `python -m sigma_audit keys`）。
   表达式候选走认证家族规则（分母 EPS 剔除、陡/平读数须全为正），与总台账逐字同口径。

2) Python 可调用（.py 文件，导出 `metric(q) -> float | None`）：
   q 是单个 run 的只读字典：124 个基元 + 特殊键
     q['__run_id__'], q['__arm__'] ('steep'|'flat'), q['__env__'],
     q['__hidden_err__']（陡臂封存真值误差，平底臂与缺失处为 None——正对照用）。
   返回 None 表示该 run 上不可测；哪臂测不了，哪根轴就标『不可测』，不编数。

内置插件：
   builtin:truth   封存真值正对照（逐 run 查表 hidden err_rms_vs_truth）
   builtin:bh93    BH93 一族的代理量 max|u|（=表达式 "u|all|max"）
"""
import importlib.util
import os
import re

import numpy as np

from . import EPS

_EXPR = re.compile(r"^\s*([\w|]+)\s*(?:/\s*([\w|]+))?\s*$")


def parse_metric(spec):
    """返回 (kind, payload)。kind ∈ {expression, callable, builtin}"""
    if spec == "builtin:truth":
        return "builtin", "truth"
    if spec == "builtin:bh93":
        return "expression", ("u|all|max", None)
    if spec.endswith(".py") and os.path.exists(spec):
        name = os.path.splitext(os.path.basename(spec))[0]
        s = importlib.util.spec_from_file_location("sigma_plugin_" + name, spec)
        mod = importlib.util.module_from_spec(s)
        s.loader.exec_module(mod)
        if not hasattr(mod, "metric"):
            raise ValueError("插件文件必须导出 metric(q) 函数：%s" % spec)
        return "callable", mod.metric
    m = _EXPR.match(spec)
    if m:
        return "expression", (m.group(1), m.group(2))
    raise ValueError("无法解析的指标：%r（既不是表达式也不是 .py 插件）" % spec)


def eval_expression(cache, num, den):
    """按认证家族规则求值。返回 (values, family_ok, note)。"""
    keys = cache["keys"]
    if num not in keys:
        raise ValueError("未知基元：%r（合法名见 `python -m sigma_audit keys`）" % num)
    i = keys.index(num)
    fam_ok, note = True, ""
    if den is None:
        v26, vfl = cache["M26"][:, i], cache["MFL"][:, i]
        p26, pfl = cache["P26"][:, i], cache["PFL"][:, i]
    else:
        if den not in keys:
            raise ValueError("未知基元：%r" % den)
        j = keys.index(den)
        for M, tag in ((cache["M26"], "陡臂"), (cache["MFL"], "平底臂"),
                       (cache["P26"], "配对陡臂"), (cache["PFL"], "配对平底臂")):
            if np.any(np.abs(M[:, j]) < EPS):
                fam_ok, note = False, "分母 %s 在%s存在近零读数——总台账将此候选整体剔除" % (den, tag)
        v26 = cache["M26"][:, i] / cache["M26"][:, j]
        vfl = cache["MFL"][:, i] / cache["MFL"][:, j]
        p26 = cache["P26"][:, i] / cache["P26"][:, j]
        pfl = cache["PFL"][:, i] / cache["PFL"][:, j]
    if fam_ok and (np.any(v26 <= 0) or np.any(vfl <= 0)
                   or not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl)))):
        fam_ok, note = False, "读数存在非正/非有限值——乘性家族规则将此候选整体剔除"
    return dict(v26=v26, vfl=vfl, p26=p26, pfl=pfl), fam_ok, note


def eval_callable(cache, fn):
    """逐 run 查表求值。None → nan（该处不可测）。"""
    keys = cache["keys"]

    def rows(M, ids, arm, hid=None):
        out = np.full(len(ids), np.nan)
        for r in range(len(ids)):
            q = dict(zip(keys, M[r]))
            q["__run_id__"] = ids[r]
            q["__arm__"] = arm
            q["__env__"] = cache["env"]
            he = None
            if hid is not None and np.isfinite(hid[r]):
                he = float(hid[r])
            q["__hidden_err__"] = he
            v = fn(q)
            if v is not None:
                out[r] = float(v)
        return out

    v26 = rows(cache["M26"], cache["ids_steep"], "steep", cache["hid_err_steep"])
    vfl = rows(cache["MFL"], cache["ids_flat"], "flat")
    pid = cache["pair_ids"]
    p26 = rows(cache["P26"], [str(x[0]) for x in pid], "steep",
               cache["hid_err_pair_steep"])
    pfl = rows(cache["PFL"], [str(x[1]) for x in pid], "flat")
    return dict(v26=v26, vfl=vfl, p26=p26, pfl=pfl)


def truth_metric(q):
    """封存真值正对照：返回该 run 的隐藏真值误差（平底臂无封存真值→None）。"""
    return q["__hidden_err__"]
