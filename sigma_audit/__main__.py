# -*- coding: utf-8 -*-
"""CLI 入口：submit / selftest / counts / build-cache / gate / keys"""
import argparse
import datetime
import json
import os
import sys
import time

from . import __version__, ENVS, CACHE_DIR, REFERENCE_ROOT
from . import anchors
from .cache import build_env_cache, load_env_cache, diag45_seal_status
from .core import judge_env, judgment_row, full_space, counts
from .plugins import parse_metric, eval_expression, eval_callable, truth_metric


def _load_caches(need=("zonal", "merid", "diag45"), notes=None):
    out = {}
    for e in need:
        try:
            c = load_env_cache(e)
        except RuntimeError as ex:  # diag45 封存门检不过：拒载并显形
            if notes is not None:
                notes.append(str(ex))
            c = None
        if c is not None:
            out[e] = c
    return out


def cmd_submit(args):
    t0 = time.time()
    notes = []
    try:
        kind, payload = parse_metric(args.metric)
    except (ValueError, OSError) as ex:
        print("送检拒收：%s" % ex)
        return 2
    caches = _load_caches(notes=notes)
    if "zonal" not in caches:
        print("缺少纬向缓存：先跑 python -m sigma_audit build-cache --envs zonal,merid")
        return 2
    blocks = {}
    for env, cache in caches.items():
        if kind == "expression":
            num, den = payload
            try:
                vals, fam_ok, note = eval_expression(cache, num, den)
            except ValueError as ex:
                print("送检拒收：%s" % ex)
                return 2
            blocks[env] = judge_env(cache, vals, fam_ok, note)
        elif kind == "builtin" and payload == "truth":
            vals = eval_callable(cache, truth_metric)
            blocks[env] = judge_env(cache, vals, True,
                                    "封存真值正对照：平底臂无封存真值，B 轴按『不可测』处理")
        else:
            vals = eval_callable(cache, payload)
            blocks[env] = judge_env(cache, vals, True, "外部可调用插件：家族规则不适用，仅按读数判轴")
    if "diag45" not in caches:
        notes.append("diag45 缓存未构建（留出纪律门未过或未跑 build-cache）——45° 列缺席，判定臂不受影响")
    mid = args.metric if kind != "callable" else "callable:%s" % args.metric
    row = judgment_row(mid, kind, blocks, time.time() - t0, notes)
    _print_row(row)
    if args.json:
        json.dump(row, open(args.json, "w"), indent=1, ensure_ascii=False)
        print("→ %s" % args.json)
    return 0


def _print_row(row):
    print()
    print("JudgmentRow  ·  %s  ·  %.1fs" % (row["metric"], row["elapsed_s"]))
    print("─" * 72)
    hdr = "%-8s %8s %8s %8s %8s %10s %6s" % ("环境", "A", "B", "Wilson下界", "D", "A⊥", "两关")
    print(hdr)
    for env in ("zonal", "merid", "diag45"):
        b = row["envs"].get(env)
        if b is None:
            print("%-8s %s" % (env, "（缓存缺席）"))
            continue
        fmt = lambda x: ("%8.3f" % x) if isinstance(x, float) else "%8s" % ("—" if x is None else x)
        tg = {True: "通过", False: "未过", None: "—"}[b["two_gate_pass"]]
        print("%-8s %s %s %10s %s %10s %6s" % (
            env, fmt(b["A"]), fmt(b["B"]),
            ("%.4f" % b["wilson_lb_B"]) if b["wilson_lb_B"] is not None else "—",
            fmt(b["D"]), fmt(b["AP"]), tg))
        if not b.get("in_certified_family", True):
            print("         ⚠ %s" % b.get("family_note", ""))
    print("─" * 72)
    print("判定：%s" % row["verdict"])
    for r in row["reasons"]:
        print("  · %s" % r)
    for n in row["notes"]:
        print("  ※ %s" % n)
    print("  ※ %s" % row["semantics"])


def cmd_counts(args):
    need = tuple(args.envs.split(","))
    notes = []
    caches = _load_caches(need=need, notes=notes)
    if "zonal" not in caches:
        print("缺少纬向缓存"); return 2
    fs = {}
    for env in need:
        if env not in caches:
            continue
        print("全空间复算 %s …" % env, flush=True)
        fs[env] = full_space(caches[env])
        print("  %d 候选  %.0fs" % (len(fs[env]["names"]), fs[env]["elapsed_s"]))
    c = counts(fs)
    ref = json.load(open(anchors.E67B))
    checks = anchors.e67b_checks(c, ref)
    e65 = anchors.e65_full_anchor(fs["zonal"])
    checks["纬向全空间与 E65 登记轴逐位一致"] = bool(e65["ok"])
    evaluated = {k: v for k, v in checks.items() if v is not None}
    ok = all(evaluated.values())
    doc = dict(
        command="python -m sigma_audit counts --envs %s%s" % (args.envs, (" --json %s" % args.json) if args.json else ""),
        generated_at=datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        envs_requested=list(need), envs_computed=sorted(fs.keys()),
        counts=c, checks_vs_E67B=checks,
        checks_not_evaluated=[k for k, v in checks.items() if v is None],
        all_evaluated_checks_pass=ok,
        e65_anchor=e65,
        reference=dict(path=anchors.E67B, sha256=anchors.sha256_file(anchors.E67B)),
        cache_sha256={e: anchors.sha256_file(os.path.join(CACHE_DIR, "primitives_%s.npz" % e))
                      for e in fs},
        elapsed_s={e: fs[e]["elapsed_s"] for e in fs},
        notes=notes)
    if "diag45" in need:
        doc["holdout_gate"] = diag45_seal_status()
    print(json.dumps(dict(counts=c, checks=checks, e65_ok=e65["ok"]), indent=1, ensure_ascii=False))
    if args.json:
        json.dump(doc, open(args.json, "w"), indent=1, ensure_ascii=False, default=str)
        print("→ %s" % args.json)
    return 0 if ok else 1


def cmd_build_cache(args):
    print("公开版只支持既有缓存回放；重建须在原始研究环境中通过 G1–G6 门检。")
    return 2


def _original_cmd_build_cache(args):
    envs = args.envs.split(",")
    rc = 0
    for e in envs:
        if e not in ENVS:
            print("未知环境 %s" % e); return 2
        if e == "diag45":
            st = diag45_seal_status()
            if st["ok"]:
                print("diag45 留出纪律门：G1–G6 全过（封条 %s，封存于 %s，正文权限 %s）"
                      % (st["seal"], st.get("sealed_at"), st.get("md_mode")))
            elif st.get("absent"):
                print("diag45 留出纪律门：未封存→拒绝构建（设计行为，T3 将记 SKIP）")
                continue
            else:
                print("diag45 留出纪律门：RED——封条在但不合协议→拒绝构建：%s" % "；".join(st["failed"]))
                rc = 3
                continue
        build_env_cache(e)
    return rc


def cmd_gate(args):
    st = diag45_seal_status()
    print(json.dumps(st, indent=1, ensure_ascii=False))
    if args.json:
        json.dump(st, open(args.json, "w"), indent=1, ensure_ascii=False)
    if st["ok"]:
        print("gate: 公开快照字节校验通过（不证明历史封存时刻）" if st.get("mode") == "release_snapshot"
              else "gate: 已按协议封存（G1–G6 全过）")
        return 0
    if st.get("absent"):
        print("gate: 未封存（设计行为：diag45 不构建、不载入）")
        return 0
    print("gate: RED——封条在但不合协议")
    return 3


def cmd_keys(args):
    c = load_env_cache("zonal")
    if c is None:
        print("先 build-cache"); return 2
    for k in c["keys"]:
        print(k)
    print("# 共 %d 个基元；候选=基元或基元/基元" % len(c["keys"]))
    return 0


def cmd_replay(args):
    """只读历史挑指标记录；不生成新回答或新判分。"""
    path = args.path or os.path.join(REFERENCE_ROOT, "trajectory_e61.jsonl")
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    print("历史轨迹回放：E61 挑指标；来源 %s" % path)
    for row in rows[:args.limit]:
        print(json.dumps({k: row.get(k) for k in ("seed", "model", "picks", "reason")}, ensure_ascii=False))
    print("展示 %d / %d 条存档；不代表新的模型调用或有效性判定。" % (min(len(rows), args.limit), len(rows)))
    return 0


def main():
    ap = argparse.ArgumentParser(prog="sigma_audit",
                                 description="σ 伪流环境指标送检台 v%s" % __version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("submit", help="送检一把尺子，出 JudgmentRow")
    s.add_argument("metric"); s.add_argument("--json", default=None)
    s.set_defaults(fn=cmd_submit)
    s = sub.add_parser("counts", help="全空间计数复现（与 E67B 登记、E65 登记轴对账）")
    s.add_argument("--envs", default="zonal,merid,diag45")
    s.add_argument("--json", default=None)
    s.set_defaults(fn=cmd_counts)
    s = sub.add_parser("build-cache", help="构建基元查表缓存")
    s.add_argument("--envs", default="zonal,merid")
    s.set_defaults(fn=cmd_build_cache)
    s = sub.add_parser("gate", help="diag45 留出纪律门检（G1–G6）")
    s.add_argument("--json", default=None)
    s.set_defaults(fn=cmd_gate)
    s = sub.add_parser("keys", help="列出 124 个合法基元名")
    s.set_defaults(fn=cmd_keys)
    s = sub.add_parser("selftest", help="三条验收测试（CI）")
    s.add_argument("--json", default=None)
    s.set_defaults(fn=None)
    s = sub.add_parser("replay", help="只读回放历史 E61 挑指标轨迹")
    s.add_argument("--path", default=None)
    s.add_argument("--limit", type=int, default=2)
    s.set_defaults(fn=cmd_replay)
    args = ap.parse_args()
    if args.cmd == "selftest":
        from .selftest import run_all
        sys.exit(run_all(args.json))
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
