#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""答辩现场演示（跨平台版）。

与 scripts/demo_60s.sh 输出同源、同数字，但不依赖 bash，
Windows / macOS / Linux 上一律 `python scripts/demo.py` 即可。
全部数字从随包数据现场重算，不联网、不需要机时、不调用大模型。
"""
import json
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)

# Windows 10+ 控制台开启 ANSI；不支持则退回无色
if os.name == "nt":
    os.system("")
USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
CYAN, RESET = ("\033[1;36m", "\033[0m") if USE_COLOR else ("", "")

FAILED = 0


def w(s):
    """字符串的显示宽度：东亚全角字符算两列。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, n):
    return s + " " * max(0, n - w(s))


def bar(t):
    print("\n%s%s%s" % (CYAN, t, RESET))


def screen(title, fn):
    global FAILED
    bar(title)
    try:
        fn()
    except Exception as e:
        FAILED += 1
        print("  [FAIL] 本屏重算失败: %s: %s" % (type(e).__name__, e), file=sys.stderr)


def s1():
    import numpy as np
    d = np.load("e65/E65_AXES.npz")
    A, B = d["A"], d["B"]
    n = A.size
    a = int((A >= 0.70).sum())
    b = int((B >= 0.90).sum())
    both = int(((A >= 0.70) & (B >= 0.90)).sum())
    print("  %s%6d 把" % (pad("候选尺子总数", 26), n))
    print("  %s%6d 把通过" % (pad("第一关 排序一致 A>=0.70", 26), a))
    print("  %s%6d 把通过" % (pad("第二关 平底对照 B>=0.90", 26), b))
    print("  %s%6d 把" % (pad("两关同过", 26), both))
    exp = a * b / n
    print()
    print("  → 若两关互不相干，期望同过 %.1f 把；实测 %d 把，衰减 %.1f 倍" % (exp, both, exp / both))
    rec = json.load(open("e67/E67B_RECIPE_TRANSFER.json", encoding="utf8"))
    ok = rec["n_zonal"] == n and rec["size_S_A"] == both
    print("  → 与看数据之前封存的登记件对账：n=%d、过关数=%d —— %s"
          % (rec["n_zonal"], rec["size_S_A"], "一致" if ok else "不一致"))
    if not ok:
        raise AssertionError("与封存登记件不一致")


def s2():
    K = json.load(open("e44_tide/analysis/KILLBOARD.json", encoding="utf8"))
    NAME = {"Pnet_MW": "海山周围的波功率", "deep_dc_rms": "深层残余流",
            "temp_d400": "深水温度", "uv_ratio": "两个流速的比值",
            "truth": "隐藏的真值（对照）"}
    COL = ["换到平地", "换无误差数据", "换区域大小", "换初始时刻", "事先押注",
           "换风向", "隐去名字", "跟真值比方向", "静止海检验", "通行做法"]
    V = {"过": "合格", "死": "不合格", "边": "勉强", "未": "未测",
         "待定": "证据不足", "定义": "按定义"}
    print("  %s%s" % (pad("", 24), "".join(pad(c, 14) for c in COL)))
    for r, row in zip(K["rows"], K["grid"]):
        print("  %s%s" % (pad(NAME.get(r, r), 24),
                          "".join(pad(V.get(c["verdict"], c["verdict"]), 14) for c in row)))
    n_bad = sum(1 for row in K["grid"][:4] for c in row[:9] if c["verdict"] in ("死", "边"))
    print()
    print("  → 最右一列「通行做法」：四个指标全部合格")
    print("  → 换成我们这九项：每一个指标都有不合格的项（共 %d 处不合格或勉强）" % n_bad)


def s3():
    X = json.load(open("e55/E55_CROSS.json", encoding="utf8"))["prereg_check"]["angle_trajectory_uv"]
    E = json.load(open("e60/E60_VERDICT.json", encoding="utf8"))
    print("  同一个指标，换三个风向 —— 排名能力：")
    for k, lab in (("deg0", "纬向风"), ("deg45", "45° 风"), ("deg90", "经向风")):
        a = -X[k][0]
        print("      %s%+.2f%s" % (pad(lab, 10), a, "   ← 反过来了" if a < 0 else ""))
    j = [v["jaccard"] for v in E["pairwise"].values()]
    f = [v["frac"] for v in E["per_rx"].values()]
    print()
    print("  换四种陡度的海山 —— 不容易被糊弄的那批指标：")
    print("      合格比例 %s" % (" / ".join("%.1f%%" % (x * 100) for x in f)))
    print("      两两重合度 %.2f – %.2f  → 几乎是同一批" % (min(j), max(j)))
    print()
    print("  → 排序检验需要参照解；本例在经向风下排序转负")
    print("  → 配对检验在已测四种陡度内较稳定，不能据此代替排序检验")


def s4():
    FILES = [("e55/E55_CROSS.json", "换强迫方向"), ("e56/E56_VERDICT.json", "社区标准检验"),
             ("e59/E59_TRUTHFREE.json", "无真值预筛"), ("e60/E60_VERDICT.json", "换地形陡度"),
             ("e61/E61_AGENT_PICKS.json", "机器挑指标")]
    tot = ref = 0
    for f, lab in FILES:
        if not os.path.exists(f):
            continue
        d = json.load(open(f, encoding="utf8"))
        pc = next((v for k, v in d.items() if "prereg" in k.lower() and isinstance(v, dict)), None)
        if not pc:
            continue
        hits = []
        for k, v in pc.items():
            if k.endswith("_range") or k.endswith("_note"):
                continue
            bad = (v is False) or (isinstance(v, str) and ("反驳" in v or "未命中" in v))
            good = (v is True) or (isinstance(v, str) and ("命中" in v or v == "中"))
            if bad or good:
                tot += 1
                if bad:
                    ref += 1
                    hits.append("%s 被推翻" % k.split()[0])
        print("  %s%s" % (pad(lab, 14), "、".join(hits) if hits else "本组预测全部命中"))
    print()
    print("  → E55–E61 五组现场统计：%d 条事先登记的预测里，%d 条被自己的数据推翻" % (tot, ref))
    print("  → 推翻的部分我们原样保留，没有改判据、没有事后补预测")


def s5():
    print("  以上每一个数字，都是刚才从随包数据现场重算出来的")
    print("  跨平台三条自检（约 16 秒）：python -m sigma_audit selftest")
    print("     它当场复现 204 / 88 / 140 / 80，并与封存登记轴逐位对照")
    print("  单条指标送检：             python -m sigma_audit submit \"u|s50|mean_abs / v|s50|rms\"")
    print("  复算随包主结论（Linux/macOS）：bash scripts/reproduce_core.sh")


SCREENS = [
    ("── 1/5  一万五千三百七十六把候选，过两道关的只有 204 把 ──────", s1),
    ("── 2/5  新旧指标的相互评判 ──────────────────────────────────", s2),
    ("── 3/5  指标的两道检验：排序与平底配对 ────────────", s3),
    ("── 4/5  它会否定自己：事先登记的预测，现场逐条核对 ──────────", s4),
    ("── 5/5  随包结果可复算 ────────────────────────────────────────", s5),
]

USAGE = """用法：
  python scripts/demo.py              五屏一次跑完
  python scripts/demo.py --only 1     只跑第 1 屏（答辩现场用，约 20 秒）
  python scripts/demo.py --stage      一屏一停，按回车翻下一屏
  python scripts/demo.py --only 1,4   只跑指定的几屏
"""


def main():
    argv = sys.argv[1:]
    if "-h" in argv or "--help" in argv:
        print(USAGE); return 0
    stage = "--stage" in argv
    pick = list(range(1, len(SCREENS) + 1))
    if "--only" in argv:
        i = argv.index("--only")
        if i + 1 < len(argv):
            try:
                pick = [int(x) for x in argv[i + 1].replace("，", ",").split(",") if x.strip()]
            except ValueError:
                print("--only 的参数要是屏号，例如 --only 1 或 --only 1,4", file=sys.stderr)
                return 2
    for k, n in enumerate(pick):
        if not 1 <= n <= len(SCREENS):
            print("没有第 %d 屏（共 %d 屏）" % (n, len(SCREENS)), file=sys.stderr)
            return 2
        title, fn = SCREENS[n - 1]
        screen(title, fn)
        if stage and k < len(pick) - 1:
            try:
                input("\n    ——— 按回车继续 ———")
            except (EOFError, KeyboardInterrupt):
                print(); break
    print()
    if FAILED:
        print("DEMO: FAILED (%d block(s))" % FAILED, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
