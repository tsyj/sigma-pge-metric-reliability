# -*- coding: utf-8 -*-
"""#27 的三条验收测试（全绿才算交付）：

T1 封存真值正对照行零判负 —— builtin:truth 的 JudgmentRow 不得为『不合格』，
   纬向 A 须过排得准关（真值自己必须排得准），B 须按『不可测』处理而非充零不合格。
T2 BH93 不合格复现 —— 表达式 u|all|max（BH93 一族的静止海诊断量在风驱台账上的对应基元）
   必须『不合格』，且送检台对该候选算出的未取整 A/B/D 与 e65 登记轴（E65_AXES.npz 该候选下标）
   逐位相等、G=1（单量）。下标由全空间枚举定位，枚举顺序与 E65 的一致性由 T3 的全空间对账兜住。
T3 计数复现 —— 全空间复算须逐字复现 e67/E67B_RECIPE_TRANSFER.json 的
   S_A=204、S_AP=444、经向存活 88/0、45° 存活 140/0、三向 80/0，且纬向全空间 A/B/D/G 与
   E65_AXES.npz 逐候选 max|Δ|=0。
   diag45 缓存因留出纪律门未构建时，本条判 SKIP（不算绿——套件交付以三条全绿为准）；
   缓存存在但封存门检不过（封存后正文被改/放开写权限/封条残缺）→ 判 FAIL。
"""
import datetime
import json
import os
import time

from . import KIT_ROOT, CACHE_DIR
from . import anchors
from .cache import load_env_cache, diag45_seal_status
from .core import judge_env, verdict_from_blocks, full_space, counts, axes_for_values
from .plugins import eval_expression, eval_callable, truth_metric

BH93_NAME = ("u|all|max", None)


def t1_truth_positive_control(caches):
    blocks = {}
    for env, cache in caches.items():
        vals = eval_callable(cache, truth_metric)
        blocks[env] = judge_env(cache, vals, True, "正对照")
    v, reasons = verdict_from_blocks(blocks)
    z = blocks["zonal"]
    ok = (v != "不合格") and z["A"] is not None and z["A"] >= 0.7 and z["B"] is None
    detail = dict(verdict=v, zonal_A=z["A"], zonal_n=z["n_steep"], zonal_B=z["B"],
                  rule="参照解不被判为不合格；A≥0.7；B=不可测（平底臂无封存真值）")
    return ok, detail


def t2_bh93_killed(caches, fs_zonal):
    cache = caches["zonal"]
    vals, fam_ok, note = eval_expression(cache, BH93_NAME[0], None)
    blocks = {"zonal": judge_env(cache, vals, fam_ok, note)}
    v, reasons = verdict_from_blocks(blocks)
    z = blocks["zonal"]
    killed = (v == "不合格") and (z["B"] is not None and z["B"] < 0.9)
    # 点值对照：送检台路径（axes_for_values，未取整）vs E65 登记值
    raw = axes_for_values(cache, vals["v26"], vals["vfl"], vals["p26"], vals["pfl"])
    idx, reg = anchors.e65_point(fs_zonal, BH93_NAME)
    anchor = dict(e65_index=idx, registered=reg,
                  submitted=dict(A=raw["A"], B=raw["B"], D=raw["D"]),
                  A_equal=(raw["A"] == reg["A"]), B_equal=(raw["B"] == reg["B"]),
                  D_equal=(raw["D"] == reg["D"]), G_is_single=(reg["G"] == 1))
    anchor["ok"] = all(anchor[k] for k in ("A_equal", "B_equal", "D_equal", "G_is_single"))
    ok = killed and anchor["ok"]
    detail = dict(verdict=v, A=z["A"], B=z["B"], reasons=reasons, e65_point_anchor=anchor)
    return ok, detail


def t3_counts(caches, fs_zonal, gate=None):
    if gate is not None and not gate.get("ok") and not gate.get("absent"):
        return False, dict(fail="diag45 封存门检不过：%s" % "；".join(gate.get("failed", [])),
                           holdout_gate=gate)
    if "diag45" not in caches:
        return None, dict(skip="diag45 缓存未构建（留出纪律门）——本条 SKIP，套件不算全绿",
                          holdout_gate=gate)
    fs = {"zonal": fs_zonal}
    for env, cache in caches.items():
        if env != "zonal":
            fs[env] = full_space(cache)
    c = counts(fs)
    ref = json.load(open(anchors.E67B))
    checks = anchors.e67b_checks(c, ref)
    e65 = anchors.e65_full_anchor(fs_zonal)
    checks["纬向全空间与 E65 登记轴逐位一致（A/B/D max|Δ|=0 且 G 相等）"] = bool(e65["ok"])
    ok = all(v is True for v in checks.values())
    return ok, dict(counts=c, checks=checks, e65_anchor=e65,
                    reference=dict(path=anchors.E67B, sha256=anchors.sha256_file(anchors.E67B)),
                    holdout_gate=gate)


def load_all_caches():
    """返回 (caches, gate)。diag45 载入受封存门约束；门检不过时不载入并把门检状态交回。"""
    caches = {}
    for e in ("zonal", "merid"):
        c = load_env_cache(e)
        if c is not None:
            caches[e] = c
    gate = diag45_seal_status()
    if gate["ok"]:
        c = load_env_cache("diag45")
        if c is not None:
            caches["diag45"] = c
    return caches, gate


def run_all(out_path=None):
    t0 = time.time()
    caches, gate = load_all_caches()
    if "zonal" not in caches or "merid" not in caches:
        print("FAIL 缺缓存：先 build-cache --envs zonal,merid（diag45 视封存状态）")
        return 2
    fs_zonal = full_space(caches["zonal"])
    results = {}
    ok1, d1 = t1_truth_positive_control(caches)
    results["T1 真值正对照零判负"] = (ok1, d1)
    ok2, d2 = t2_bh93_killed(caches, fs_zonal)
    results["T2 BH93 不合格复现＋E65 点值逐位对照"] = (ok2, d2)
    ok3, d3 = t3_counts(caches, fs_zonal, gate)
    results["T3 计数复现 444→0→0 与 204/88/140/80＋E65 全空间对账"] = (ok3, d3)
    print()
    all_green = True
    for name, (ok, d) in results.items():
        tag = "PASS" if ok else ("SKIP" if ok is None else "FAIL")
        if ok is not True:
            all_green = False
        print("[%s] %s" % (tag, name))
        print("       %s" % json.dumps(d, ensure_ascii=False, default=str)[:600])
    elapsed = time.time() - t0
    print()
    print("selftest：%s  （%.0fs）" % ("三条全绿" if all_green else "未全绿", elapsed))
    doc = {k: dict(ok=v[0], detail=v[1]) for k, v in results.items()}
    doc["_meta"] = dict(
        all_green=all_green,
        generated_at=datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        elapsed_s=round(elapsed, 1),
        envs_loaded=sorted(caches.keys()),
        cache_sha256={e: anchors.sha256_file(os.path.join(CACHE_DIR, "primitives_%s.npz" % e))
                      for e in caches},
        code_sha256={f: anchors.sha256_file(os.path.join(os.path.dirname(__file__), f))
                     for f in ("__init__.py", "anchors.py", "cache.py", "core.py",
                               "plugins.py", "selftest.py")})
    out_path = out_path or os.path.join(os.getcwd(), "SELFTEST_27.json")
    json.dump(doc, open(out_path, "w"), indent=1, ensure_ascii=False, default=str)
    return 0 if all_green else 1
