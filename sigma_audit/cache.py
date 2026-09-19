# -*- coding: utf-8 -*-
"""缓存构建：把三个环境的 124 基元读数一次性算好落盘（env_replay 精确查表版）。

数据收集逻辑与 e67/e67b_recipe_transfer.py 的 axes() 逐字同口径：
  - 只取 obs.valid 且 ntimes==8640 的 run；
  - 陡臂技巧评分：纬向用 regraded_v2.jsonl 的 skill_vs_zero，经向/45° 用 ledger hidden.skill_vs_zero；
  - 平底配对按 (VISC2,VISC4,AKV_BAK,TNU2) 四元组 round(…,6) 匹配；
  - 基元 = metric_search.base_quantities(run_dir)（官方实现，不复制不改写）。

留出纪律（重要）：diag45 缓存只有在 multienv_metrology 的正式预注册**已按协议封存**之后
才允许构建与载入，否则拒绝——避免为另一条目的留出环境提前落盘任何读数。
「已按协议封存」= 下列硬校验全过（任何一条不过 → RuntimeError，不降级、不警告了事）：
  G1 封条文件存在（final/PREREG_multienv_metrology.sha256 或 .md.sha256）；
  G2 预注册正文存在；
  G3 封条首行 = 「64 位小写十六进制 + 两空格 + 正文文件名」（sha256sum 原样输出格式）；
  G4 首行哈希与正文现算 sha256 逐位相等；
  G5 次行为 `date -Is` 的 ISO-8601 时刻，且早于现在；
  G6 正文只读：权限位无任何写位（chmod 444）且 os.access(W_OK) 为假。
门检结果随 meta_diag45.json 落盘；载入 diag45 缓存时重新门检（封存后正文被改/被放开写权限 → 拒载）。
"""
import datetime
import hashlib
import json
import os
import re
import stat
import sys
import time

import numpy as np

from . import ENV_ROOT, ENVS, CACHE_DIR, DATA_ROOT, REFERENCE_ROOT

MULTIENV_SEAL = os.path.join(REFERENCE_ROOT, "PREREG_multienv_metrology.md.sha256")
MULTIENV_SEAL_ALT = os.path.join(REFERENCE_ROOT, "PREREG_multienv_metrology.sha256")


def _metric_search():
    sys.path.insert(0, os.path.join(ENV_ROOT, "scripts"))
    sys.path.insert(0, os.path.join(ENV_ROOT, "e44"))
    import metric_search  # noqa
    return metric_search


MULTIENV_MD = os.path.join(REFERENCE_ROOT, "PREREG_multienv_metrology.md")
_BUNDLED_MD = MULTIENV_MD
_SHA_LINE = re.compile(r"^([0-9a-f]{64}) [ *](.+)$")


def check_seal(md, seal, require_readonly=True):
    """对一对 (正文, 封条) 做 G2–G6 硬校验。返回 dict(ok, failed=[…], …)；不抛异常。"""
    st = dict(md=md, seal=seal, ok=False, failed=[],
              checked_at=datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
    if not os.path.exists(md):
        st["failed"].append("G2 预注册正文不存在")
        return st
    try:
        lines = open(seal, encoding="utf-8").read().splitlines()
    except Exception as e:  # noqa
        st["failed"].append("G1 封条不可读：%s" % e)
        return st
    m = _SHA_LINE.match(lines[0].rstrip()) if lines else None
    if not m:
        st["failed"].append("G3 封条首行不是 sha256sum 格式（空文件/截断/手写）")
    else:
        st["registered_sha256"] = m.group(1)
        if os.path.basename(m.group(2)) != os.path.basename(md):
            st["failed"].append("G3 封条登记的文件名 %r ≠ 正文 %r" % (m.group(2), os.path.basename(md)))
    cur = hashlib.sha256(open(md, "rb").read()).hexdigest()
    st["current_sha256"] = cur
    if m and m.group(1) != cur:
        st["failed"].append("G4 登记哈希 %s… ≠ 正文现算 %s…（封存后正文被改）" % (m.group(1)[:12], cur[:12]))
    sealed_at = None
    if len(lines) >= 2:
        try:
            sealed_at = datetime.datetime.fromisoformat(lines[1].strip())
        except ValueError:
            sealed_at = None
    if sealed_at is None or sealed_at.tzinfo is None:
        st["failed"].append("G5 封条次行缺 date -Is 时刻（或无时区）")
    else:
        st["sealed_at"] = sealed_at.isoformat()
        if sealed_at > datetime.datetime.now().astimezone():
            st["failed"].append("G5 封存时刻晚于现在（时钟或封条可疑）")
    mode = stat.S_IMODE(os.stat(md).st_mode)
    st["md_mode"] = "%o" % mode
    st["md_writable_by_access"] = bool(os.access(md, os.W_OK))
    if require_readonly and (mode & 0o222 or st["md_writable_by_access"]):
        st["failed"].append("G6 正文未 chmod 444（权限 %o，W_OK=%s）" % (mode, st["md_writable_by_access"]))
    st["ok"] = not st["failed"]
    return st


def release_snapshot_status():
    """Git 不保存 444 位：公开缓存检验登记字节，不能证明历史封存时刻。

    原始构建的 G1–G6 检验仍由 check_seal 默认严格执行。
    本函数只用于随包缓存的回放，所有被登记的缓存与参照件必须完整。
    """
    # 快照校验只读取自身的登记件；原始门的临时路径覆盖不改变公开快照。
    md = os.path.join(DATA_ROOT, "reference/PREREG_multienv_metrology.md")
    seal = os.path.join(DATA_ROOT, "reference/PREREG_multienv_metrology.sha256")
    st = check_seal(md, seal, require_readonly=False)
    st.update(absent=False, mode="release_snapshot",
              boundary="仅核对随包字节及封条格式；不证明历史时间，也不提供外部信任锚。")
    try:
        manifest = json.load(open(os.path.join(DATA_ROOT, "RELEASE_MANIFEST.json")))
        required = {"reference/PREREG_multienv_metrology.md",
                    "reference/PREREG_multienv_metrology.sha256",
                    "reference/E65_AXES.npz", "reference/E67B_RECIPE_TRANSFER.json"}
        required.update("cache/primitives_%s.npz" % e for e in ENVS)
        if not required <= set(manifest["files"]):
            st["failed"].append("公开快照登记缺少必要文件")
        for rel, expected in manifest["files"].items():
            path = os.path.realpath(os.path.join(DATA_ROOT, rel))
            if not path.startswith(os.path.realpath(DATA_ROOT) + os.sep):
                raise ValueError("快照登记路径越界")
            actual = hashlib.sha256(open(path, "rb").read()).hexdigest()
            if actual != expected:
                st["failed"].append("公开快照字节不符：%s" % rel)
    except (OSError, ValueError, KeyError, TypeError) as ex:
        st["failed"].append("公开快照登记不可用：%s" % ex)
    st["ok"] = not st["failed"]
    return st


def diag45_seal_status():
    """diag45 构建/载入门：multienv 预注册按协议封存才放行。返回门检状态 dict。"""
    if MULTIENV_MD == _BUNDLED_MD:
        return release_snapshot_status()
    seals = [p for p in (MULTIENV_SEAL_ALT, MULTIENV_SEAL) if os.path.exists(p)]
    if not seals:
        return dict(ok=False, absent=True, md=MULTIENV_MD, seal=None,
                    failed=["G1 封条文件不存在（multienv 正式预注册尚未封存）"])
    st = check_seal(MULTIENV_MD, seals[0])
    st["absent"] = False
    if len(seals) > 1:
        st2 = check_seal(MULTIENV_MD, seals[1])
        if not st2["ok"]:
            st["ok"] = False
            st["failed"] += ["（第二份封条）" + f for f in st2["failed"]]
    return st


def diag45_seal_ok():
    """兼容旧接口：(ok, 封条路径)。"""
    st = diag45_seal_status()
    return st["ok"], st.get("seal")


def build_env_cache(env, verbose=True):
    if MULTIENV_MD == _BUNDLED_MD:
        raise RuntimeError("公开版只回放既有缓存；重建须使用原始工具及其 G1–G6 封存门，不以快照校验替代。")
    gate = None
    if env == "diag45":
        gate = diag45_seal_status()
        if not gate["ok"]:
            raise RuntimeError(
                "留出纪律：multienv_metrology 预注册未按协议封存，拒绝构建 diag45 缓存——"
                + "；".join(gate["failed"]))
    ms = _metric_search()
    cfg = ENVS[env]
    ledger = os.path.join(ENV_ROOT, cfg["ledger"])
    runsdir = os.path.join(ENV_ROOT, cfg["runs"])
    t0 = time.time()

    reg = {}
    if cfg["reg_from"] == "regraded":
        for l in open(os.path.join(ENV_ROOT, "ledger/regraded_v2.jsonl")):
            r = json.loads(l)
            reg[r["run_id"]] = r["skill_vs_zero"]
    seen, byp, hid_err = {}, {}, {}
    for l in open(ledger):
        r = json.loads(l)
        if not (r["obs"].get("valid") and r["ntimes"] == 8640):
            continue
        seen[r["run_id"]] = r["bathy"]
        h = r.get("hidden") or {}
        if cfg["reg_from"] == "hidden" and r["bathy"] == "r26steep" \
                and h.get("skill_vs_zero") is not None:
            reg[r["run_id"]] = h["skill_vs_zero"]
        if h.get("err_rms_vs_truth") is not None:
            hid_err[r["run_id"]] = h["err_rms_vs_truth"]
        a = r["action"]
        k = tuple(round(a.get(x, -1), 6) for x in ("VISC2", "VISC4", "AKV_BAK", "TNU2"))
        byp.setdefault(k, {})[r["bathy"]] = r["run_id"]

    r26 = [k for k, v in seen.items() if v == "r26steep" and k in reg]
    flat = [k for k, v in seen.items() if v == "flat"]
    pairs = [(v["r26steep"], v["flat"]) for v in byp.values()
             if "r26steep" in v and "flat" in v]

    Q26, S26, R26 = [], [], []
    for rid in r26:
        q = ms.base_quantities(os.path.join(runsdir, rid))
        if q:
            Q26.append(q); S26.append(reg[rid]); R26.append(rid)
    QFL, RFL = [], []
    for rid in flat:
        q = ms.base_quantities(os.path.join(runsdir, rid))
        if q:
            QFL.append(q); RFL.append(rid)
    keys = sorted(set.intersection(*[set(q) for q in Q26 + QFL]))
    M26 = np.array([[q[k] for k in keys] for q in Q26])
    MFL = np.array([[q[k] for k in keys] for q in QFL])
    P26L, PFLL, PIDS = [], [], []
    for a, b in pairs:
        qa = ms.base_quantities(os.path.join(runsdir, a))
        qb = ms.base_quantities(os.path.join(runsdir, b))
        if qa and qb and all(k in qa and k in qb for k in keys):
            P26L.append([qa[k] for k in keys])
            PFLL.append([qb[k] for k in keys])
            PIDS.append((a, b))
    os.makedirs(CACHE_DIR, exist_ok=True)
    out = os.path.join(CACHE_DIR, "primitives_%s.npz" % env)
    np.savez_compressed(
        out,
        keys=np.array(keys), M26=M26, MFL=MFL,
        P26=np.array(P26L), PFL=np.array(PFLL),
        S=np.array(S26, dtype=float),
        ids_steep=np.array(R26), ids_flat=np.array(RFL),
        pair_ids=np.array(PIDS),
        hid_err_steep=np.array([hid_err.get(rid, np.nan) for rid in R26], dtype=float),
        hid_err_pair_steep=np.array([hid_err.get(a, np.nan) for a, _ in PIDS], dtype=float),
    )
    meta = dict(env=env, n_steep=len(R26), n_flat=len(RFL), n_pairs=len(PIDS),
                n_keys=len(keys), ledger=cfg["ledger"], reg_from=cfg["reg_from"],
                built=time.strftime("%F %T"), elapsed_s=round(time.time() - t0, 1))
    if gate is not None:
        meta["holdout_gate"] = gate
    json.dump(meta, open(os.path.join(CACHE_DIR, "meta_%s.json" % env), "w"),
              indent=1, ensure_ascii=False)
    if verbose:
        print("cache[%s]: steep=%d flat=%d pairs=%d keys=%d  (%.0fs)"
              % (env, len(R26), len(RFL), len(PIDS), len(keys), time.time() - t0))
    return out


def load_env_cache(env, strict_gate=True):
    if os.path.realpath(CACHE_DIR) == os.path.realpath(os.path.join(DATA_ROOT, "cache")):
        st = release_snapshot_status()
        if not st["ok"]:
            raise RuntimeError("公开缓存校验失败：" + "；".join(st["failed"]))
    p = os.path.join(CACHE_DIR, "primitives_%s.npz" % env)
    if not os.path.exists(p):
        return None
    if env == "diag45" and strict_gate:
        gate = diag45_seal_status()
        if not gate["ok"]:
            raise RuntimeError("留出纪律：diag45 缓存存在但封存门检不过，拒绝载入——"
                               + "；".join(gate["failed"]))
    z = np.load(p, allow_pickle=False)
    return dict(env=env, keys=[str(k) for k in z["keys"]],
                M26=z["M26"], MFL=z["MFL"], P26=z["P26"], PFL=z["PFL"],
                S=z["S"], ids_steep=[str(x) for x in z["ids_steep"]],
                ids_flat=[str(x) for x in z["ids_flat"]],
                pair_ids=z["pair_ids"], hid_err_steep=z["hid_err_steep"],
                hid_err_pair_steep=z["hid_err_pair_steep"])
