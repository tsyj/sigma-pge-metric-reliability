#!/usr/bin/env python
"""动作空间体检 —— 每个声明的旋钮，真的能被求解器感知吗？

起因（E28）：`VISC4` 一直在 ACTION_SPACE 里，Agent 可以调它，环境照单全收、
跑完、返回读数 —— 但读数与不调它时**逐位相同**。因为编译头里没有 `UV_VIS4`，
双谐波项根本没编进可执行文件。

Agent 会从中学到「VISC4 无关」。这个结论碰巧是对的，但它是**编译期偶然**，
不是物理；换一个 CPP 选项结论就翻转。而环境**没有任何机制**告诉 Agent
这一点 —— 它看到的是一次正常的、成功的、有读数的实验。

> 你声明的动作空间，未必是求解器真正能感知的动作空间。
> 这个缺陷不会报错、不会崩溃、不会留下痕迹，只能靠**主动的零效应检测**发现。

用法：
    python validate_actions.py            # 短 run 快速体检
    python validate_actions.py --ntimes 8640
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import SigmaPGEEnv, ACTION_SPACE, PROXY_KEYS

# 每个旋钮的探测值：取一个「大到不可能没影响」的值
PROBE = {
    "VISC2":   500.0,
    "VISC4":   1.0e8,
    "AKV_BAK": 1.0e-3,
    "TNU2":    100.0,
}
WATCH = ["u_max", "u_rms", "deep_rms_800", "surf_max"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ntimes", type=int, default=1440)
    p.add_argument("--bathy", default="r26steep")
    a = p.parse_args()

    keys = [k for k in ACTION_SPACE if k in PROBE]
    env = SigmaPGEEnv(expose_truth=False, max_workers=min(8, len(keys) + 1))

    base_act = dict(bathy=a.bathy, ntimes=a.ntimes, seed=0)
    acts = [base_act] + [dict(base_act, **{k: PROBE[k]}) for k in keys]
    res = env.step_batch(acts)

    base = res[0][0]
    print("=" * 78)
    print(f"动作空间体检（bathy={a.bathy}, ntimes={a.ntimes}）")
    print("=" * 78)
    if not base.get("valid"):
        print("  基准 run 就没跑成，体检无效。")
        return 1
    print(f"{'旋钮':>9} {'探测值':>10} {'状态':>8}  " +
          " ".join(f"{w:>12}" for w in WATCH))
    print("-" * 78)

    inert, dead = [], []
    for k, (obs, _) in zip(keys, res[1:]):
        if not obs.get("valid"):
            st = "崩溃" if obs.get("crashed") else "未完赛"
            print(f"{k:>9} {PROBE[k]:>10g} {st:>8}  " +
                  " ".join(f"{'—':>12}" for _ in WATCH))
            dead.append(k)
            continue
        cells, moved = [], False
        for w in WATCH:
            b, v = base.get(w), obs.get(w)
            if b is None or v is None:
                cells.append(f"{'—':>12}"); continue
            rel = abs(v - b) / max(abs(b), 1e-12)
            if rel > 1e-9:
                moved = True
            cells.append(f"{v:>9.4f}{'*' if rel > 1e-9 else ' '} ")
        st = "有效" if moved else "✗ 无感"
        if not moved:
            inert.append(k)
        print(f"{k:>9} {PROBE[k]:>10g} {st:>8}  " + " ".join(cells))

    print("""
  *  = 该读数相对基准发生了变化
  无感 = 把旋钮拧到探测值，四个读数**一个都没动** —— 求解器根本感知不到它
""")
    print("=" * 78)
    if inert:
        print(f"  ⚠ 无感旋钮 {len(inert)}/{len(keys)}：{'、'.join(inert)}")
        print("    多半是对应的 CPP 选项没编进去（如 VISC4 需要 #define UV_VIS4）。")
        print("    这类旋钮留在动作空间里 = 给 Agent 埋一个不会报错的陷阱。")
    else:
        print(f"  ✓ {len(keys)} 个旋钮全部可被求解器感知")
    if dead:
        print(f"  · 探测值导致不可用 {len(dead)}：{'、'.join(dead)}"
              f"（是动作空间里真实的不可行区，不是缺陷）")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
