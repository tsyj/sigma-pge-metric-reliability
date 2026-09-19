#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""oss_audit_kit 故障注入自测（#27 送检台＋留出纪律门）。

原则：每个「门/验收」都要证明自己**会红**，否则绿灯不含信息。
全部注入只发生在内存或临时目录里；不改任何登记文件、缓存文件与他条目目录。

G 组 · diag45 留出纪律门（cache.check_seal / diag45_seal_status / build / load）
  G0  协议封存（sha256sum>…; date -Is>>…; chmod 444）→ 必须放行
  G1  无封条                              → 拒绝（absent）
  G3a 空 .sha256                          → 拒绝
  G3b 封条登记的文件名不是该正文          → 拒绝
  G4  封存后正文被改一个字节              → 拒绝
  G5a 缺 date -Is 次行                    → 拒绝
  G5b 封存时刻在未来                      → 拒绝
  G6  正文未 chmod 444                    → 拒绝
  GB  封条不合协议时 build_env_cache('diag45') 必须在读任何台账之前 RuntimeError
  GL  diag45 缓存已存在但封条不合协议时 load_env_cache('diag45') 必须拒载
S 组 · #27 三条验收的非空洞性（内存中篡改缓存/登记，验收必须 FAIL）
  S1  隐藏真值误差取反                     → T1 必须 FAIL
  S2a u|all|max 平底配对读数抬到陡臂之上    → T2 必须 FAIL（不合格翻转）
  S2b 纬向两条 run 的技巧评分互换          → T2 必须 FAIL（不合格不变，但 E65 点值对账抓住）
  S3  E67B 登记 S_A 改成 205（临时副本）   → T3 必须 FAIL
  S3g T3 在封存门不合协议时                → 必须 FAIL（不是 SKIP）
"""
import copy
import datetime
import json
import os
import subprocess
import sys
import tempfile
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

import numpy as np  # noqa: E402

from sigma_audit import cache as C  # noqa: E402
from sigma_audit import selftest as ST  # noqa: E402
from sigma_audit import anchors as AN  # noqa: E402
from sigma_audit.core import full_space  # noqa: E402

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append(dict(case=name, ok=bool(ok), detail=detail))
    print("[%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  — " + detail) if detail else ""))


def seal_protocol(d, name="PREREG_multienv_metrology"):
    md = os.path.join(d, name + ".md")
    seal = os.path.join(d, name + ".sha256")
    with open(md, "w", encoding="utf-8") as f:
        f.write("# 假预注册（故障注入用）\nP1: x > 0\n")
    subprocess.run("cd %s && sha256sum %s.md > %s.sha256 && date -Is >> %s.sha256 && chmod 444 %s.md"
                   % (d, name, name, name, name), shell=True, check=True)
    return md, seal


def unlock(md):
    os.chmod(md, 0o644)


class Patch:
    """临时改 cache 模块的封条路径。"""

    def __init__(self, md, seal):
        self.md, self.seal = md, seal

    def __enter__(self):
        self.old = (C.MULTIENV_MD, C.MULTIENV_SEAL, C.MULTIENV_SEAL_ALT)
        C.MULTIENV_MD = self.md
        C.MULTIENV_SEAL_ALT = self.seal
        C.MULTIENV_SEAL = self.seal + ".never_exists"
        return self

    def __exit__(self, *a):
        C.MULTIENV_MD, C.MULTIENV_SEAL, C.MULTIENV_SEAL_ALT = self.old


def gate_group():
    with tempfile.TemporaryDirectory() as d:
        md, seal = seal_protocol(d)
        st = C.check_seal(md, seal)
        record("G0 协议封存→放行", st["ok"], "failed=%s" % st["failed"])

        with Patch(md, os.path.join(d, "absent.sha256")):
            st = C.diag45_seal_status()
        record("G1 无封条→拒绝", (not st["ok"]) and st.get("absent"), "; ".join(st["failed"]))

        empty = os.path.join(d, "empty.sha256")
        open(empty, "w").close()
        st = C.check_seal(md, empty)
        record("G3a 空封条→拒绝", not st["ok"] and any(f.startswith("G3") for f in st["failed"]),
               "; ".join(st["failed"]))

        wrongname = os.path.join(d, "wrongname.sha256")
        lines = open(seal).read().splitlines()
        with open(wrongname, "w") as f:
            f.write(lines[0].replace("PREREG_multienv_metrology.md", "OTHER.md") + "\n" + lines[1] + "\n")
        st = C.check_seal(md, wrongname)
        record("G3b 封条文件名错配→拒绝", not st["ok"] and any("文件名" in f for f in st["failed"]),
               "; ".join(st["failed"]))

        nodate = os.path.join(d, "nodate.sha256")
        with open(nodate, "w") as f:
            f.write(lines[0] + "\n")
        st = C.check_seal(md, nodate)
        record("G5a 缺 date -Is 行→拒绝", not st["ok"] and any(f.startswith("G5") for f in st["failed"]),
               "; ".join(st["failed"]))

        future = os.path.join(d, "future.sha256")
        fut = (datetime.datetime.now().astimezone() + datetime.timedelta(days=2)).isoformat(timespec="seconds")
        with open(future, "w") as f:
            f.write(lines[0] + "\n" + fut + "\n")
        st = C.check_seal(md, future)
        record("G5b 封存时刻在未来→拒绝", not st["ok"] and any("未来" in f or "晚于" in f for f in st["failed"]),
               "; ".join(st["failed"]))

        unlock(md)
        st = C.check_seal(md, seal)
        record("G6 正文可写（644）→拒绝", not st["ok"] and any(f.startswith("G6") for f in st["failed"]),
               "; ".join(st["failed"]))

        with open(md, "a", encoding="utf-8") as f:
            f.write("P2: 封存后偷偷加的一条\n")
        os.chmod(md, 0o444)
        st = C.check_seal(md, seal)
        record("G4 封存后正文被改（且已改回 444）→拒绝", not st["ok"] and any(f.startswith("G4") for f in st["failed"]),
               "; ".join(st["failed"]))

        # GB：不合协议时 build 必须在读台账之前拒绝
        class ReachedDataRead(Exception):
            pass

        def boom():
            raise ReachedDataRead("门没拦住：已走到读台账/run 输出这一步")

        old_ms = C._metric_search
        C._metric_search = boom
        try:
            with Patch(md, empty):
                try:
                    C.build_env_cache("diag45", verbose=False)
                    record("GB 不合协议→build 先于读数拒绝", False, "居然构建成功")
                except RuntimeError as e:
                    record("GB 不合协议→build 先于读数拒绝", "留出纪律" in str(e), str(e)[:80])
                except ReachedDataRead as e:
                    record("GB 不合协议→build 先于读数拒绝", False, str(e))
        finally:
            C._metric_search = old_ms

        # GL：缓存已在但封条不合协议 → 拒载
        real = os.path.join(C.CACHE_DIR, "primitives_diag45.npz")
        if os.path.exists(real):
            with Patch(md, empty):
                try:
                    C.load_env_cache("diag45")
                    record("GL 缓存在但封条不合协议→拒载", False, "居然载入")
                except RuntimeError as e:
                    record("GL 缓存在但封条不合协议→拒载", "拒绝载入" in str(e), str(e)[:80])
                caches, gate = ST.load_all_caches()
                ok3, d3 = ST.t3_counts(caches, None, gate)
                record("S3g 封条不合协议时 T3 判 FAIL 而非 SKIP", ok3 is False, str(d3.get("fail", ""))[:80])
            os.chmod(md, 0o644)
        else:
            record("GL 缓存在但封条不合协议→拒载", False, "diag45 缓存不存在，无法注入（未执行）")


def selftest_group():
    caches, gate = ST.load_all_caches()
    if not gate["ok"] or "diag45" not in caches:
        record("S 组前置：真实封存门通过且 diag45 缓存在位", False, "; ".join(gate.get("failed", [])))
        return
    fs_zonal = full_space(caches["zonal"])

    # 基线：三条在未注入时必须 PASS（防「怎么改都红」）
    ok1, _ = ST.t1_truth_positive_control(caches)
    ok2, _ = ST.t2_bh93_killed(caches, fs_zonal)
    record("S0 未注入基线 T1/T2 PASS", ok1 is True and ok2 is True)

    c1 = {e: dict(v) for e, v in caches.items()}
    c1["zonal"]["hid_err_steep"] = -caches["zonal"]["hid_err_steep"]
    for e in c1:
        c1[e]["hid_err_steep"] = -caches[e]["hid_err_steep"]
    ok, d = ST.t1_truth_positive_control(c1)
    record("S1 隐藏真值误差取反→T1 FAIL", ok is False, "verdict=%s A=%s" % (d["verdict"], d["zonal_A"]))

    c2 = {e: dict(v) for e, v in caches.items()}
    k = caches["zonal"]["keys"].index("u|all|max")
    PFL = caches["zonal"]["PFL"].copy()
    PFL[:, k] = caches["zonal"]["P26"][:, k] * 2.0
    c2["zonal"]["PFL"] = PFL
    ok, d = ST.t2_bh93_killed(c2, fs_zonal)
    record("S2a 平底配对读数抬高→T2 FAIL", ok is False, "verdict=%s B=%s" % (d["verdict"], d["B"]))

    c3 = {e: dict(v) for e, v in caches.items()}
    S = caches["zonal"]["S"].copy()
    o = np.argsort(S)
    i, j = int(o[len(o) // 2]), int(o[len(o) // 2 + 1])
    S[i], S[j] = S[j], S[i]
    c3["zonal"]["S"] = S
    ok, d = ST.t2_bh93_killed(c3, fs_zonal)
    record("S2b 两条 run 技巧评分互换→T2 FAIL（不合格不变，E65 点值对账抓住）",
           ok is False and d["verdict"] == "不合格" and not d["e65_point_anchor"]["ok"],
           "verdict=%s anchor_ok=%s" % (d["verdict"], d["e65_point_anchor"]["ok"]))

    with tempfile.TemporaryDirectory() as dtmp:
        ref = json.load(open(AN.E67B))
        ref["size_S_A"] = 205
        fake = os.path.join(dtmp, "E67B_fake.json")
        json.dump(ref, open(fake, "w"))
        old = AN.E67B
        AN.E67B = fake
        try:
            ok, d = ST.t3_counts(caches, fs_zonal, gate)
        finally:
            AN.E67B = old
        record("S3 登记计数被改（S_A 205）→T3 FAIL", ok is False,
               "S_A check=%s" % d["checks"].get("S_A=204"))


def main():
    t0 = time.time()
    print("── G 组：留出纪律门 " + "─" * 40)
    gate_group()
    print("── S 组：#27 验收非空洞性 " + "─" * 34)
    selftest_group()
    ok = all(r["ok"] for r in RESULTS)
    out = dict(all_pass=ok, n_cases=len(RESULTS), n_pass=sum(r["ok"] for r in RESULTS),
               generated_at=datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
               elapsed_s=round(time.time() - t0, 1), cases=RESULTS)
    json.dump(out, open(os.path.join(KIT, "tests", "FAULT_INJECTION_REPORT.json"), "w"),
              indent=1, ensure_ascii=False)
    print("test_fault_injection: %s（%d/%d）" % ("PASS" if ok else "FAIL", out["n_pass"], out["n_cases"]))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
