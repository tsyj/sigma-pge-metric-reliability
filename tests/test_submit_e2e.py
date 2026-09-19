#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""#27 端到端：评委视角的一条命令（子进程，含 Python 启动时间），墙钟须 <20 s。

E1 随手写的比值表达式 → 退出码 0、JudgmentRow JSON 字段齐全、三环境列在位、墙钟 <20 s
E2 .py 插件（临时文件，导出 metric(q)）→ 同上
E3 未知基元（手滑写错名）→ 退出码 2、打印「送检拒收」，不出 traceback
E4 无法解析的输入 → 退出码 2、打印「送检拒收」
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
BUDGET_S = 20.0
RESULTS = []


def run(args):
    t0 = time.time()
    r = subprocess.run([PY, "-m", "sigma_audit"] + args, cwd=KIT,
                       capture_output=True, text=True)
    return r, time.time() - t0


def record(name, ok, detail=""):
    RESULTS.append(dict(case=name, ok=bool(ok), detail=detail))
    print("[%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  — " + detail) if detail else ""))


def check_row(path):
    row = json.load(open(path, encoding="utf-8"))
    need = {"metric", "kind", "verdict", "reasons", "envs", "elapsed_s", "semantics"}
    envs = set(row["envs"].keys())
    blk = row["envs"]["zonal"]
    need_blk = {"A", "B", "D", "AP", "wilson_lb_B", "gate_A", "gate_B", "two_gate_pass"}
    return need <= set(row) and need_blk <= set(blk), row, envs


def main():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "row1.json")
        r, wall = run(["submit", "u|d800|rms / temp|d800|rms", "--json", out])
        ok_fields, row, envs = (check_row(out) if r.returncode == 0 and os.path.exists(out)
                                else (False, {}, set()))
        record("E1 比值表达式 → JudgmentRow", r.returncode == 0 and ok_fields and wall < BUDGET_S,
               "rc=%d 墙钟=%.2fs 判定=%s 环境=%s" % (r.returncode, wall, row.get("verdict"), sorted(envs)))
        e1 = dict(wall_s=round(wall, 2), verdict=row.get("verdict"), envs=sorted(envs))

        plug = os.path.join(d, "judge_metric.py")
        with open(plug, "w", encoding="utf-8") as f:
            f.write("def metric(q):\n"
                    "    den = q['v|d800|rms']\n"
                    "    return None if den == 0 else q['u|d800|rms'] / den\n")
        out2 = os.path.join(d, "row2.json")
        r, wall = run(["submit", plug, "--json", out2])
        ok_fields, row, envs = (check_row(out2) if r.returncode == 0 and os.path.exists(out2)
                                else (False, {}, set()))
        record("E2 .py 插件 → JudgmentRow", r.returncode == 0 and ok_fields and wall < BUDGET_S,
               "rc=%d 墙钟=%.2fs 判定=%s 环境=%s" % (r.returncode, wall, row.get("verdict"), sorted(envs)))
        e2 = dict(wall_s=round(wall, 2), verdict=row.get("verdict"), envs=sorted(envs))

        r, wall = run(["submit", "u|d800|rsm / temp|d800|rms"])
        record("E3 未知基元 → 拒收（rc=2，无 traceback）",
               r.returncode == 2 and "送检拒收" in r.stdout and "Traceback" not in r.stderr,
               "rc=%d" % r.returncode)

        r, wall = run(["submit", "u|d800|rms // temp|d800|rms + 1"])
        record("E4 无法解析 → 拒收（rc=2，无 traceback）",
               r.returncode == 2 and "送检拒收" in r.stdout and "Traceback" not in r.stderr,
               "rc=%d" % r.returncode)

    ok = all(x["ok"] for x in RESULTS)
    json.dump(dict(all_pass=ok, budget_s=BUDGET_S, E1=e1, E2=e2, cases=RESULTS,
                   generated_at=datetime.datetime.now().astimezone().isoformat(timespec="seconds")),
              open(os.path.join(KIT, "tests", "SUBMIT_E2E_REPORT.json"), "w"),
              indent=1, ensure_ascii=False)
    print("test_submit_e2e:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
