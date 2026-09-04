#!/usr/bin/env python
"""E28 四旋钮扫描 —— 误差占比的崩塌，取决于你拧哪个旋钮吗？

此前主结论「误差占比随优化崩塌」只在 **VISC2 一个旋钮**上测过，
而 ledger 里 59 个 run 全部只动了 VISC2 —— 动作空间名义 4 维、实际 1 维。

本实验把四个旋钮都扫一遍，问：
    把代理指标压低同样的幅度，不同旋钮对**真信号**的破坏一样吗？

四个旋钮物理性格完全不同（探测已确认）：
    VISC2   横向拉普拉斯黏性，全尺度阻尼
    VISC4   双谐波黏性，**尺度选择性**——理论上优先杀格点尺度噪声
    AKV_BAK 背景垂向黏性，直接改 Ekman 层 = 直接改真流
    TNU2    示踪物水平扩散，**方向相反**（调低才降代理指标）

预期：若 VISC4 的误差占比崩塌得最慢，则「用尺度选择性阻尼压 σ-PGE
对真信号破坏最小」是一条可执行的建模建议，而不只是一句警告。
"""
import json, sys, os, time
sys.path.insert(0, "/data/xinyuan/GOAI_ai4s_env/scripts"); sys.path.insert(0, "/data/xinyuan/GOAI_ai4s_env/e55")
from env2_diag45 import SigmaPGEEnv
# --- 可移植性垫片：开发机行为不变；换台机器时自动改用仓库内的文件 ---
import os as _o, sys as _s
_H=_o.path.dirname(_o.path.abspath(__file__))
_R=_H if _o.path.isdir(_o.path.join(_H,'e44_tide')) else _o.path.dirname(_H)
for _d in (_o.path.join(_R,'scripts'), _o.path.join(_R,'e44_tide'), _R):
    if _o.path.isdir(_d) and _d not in _s.path: _s.path.insert(0,_d)
if not _o.path.isdir('/data/xinyuan/GOAI_ai4s_env'):
    # 评委机器：把开发路径重定向到仓库内
    _real_open=open
    def open(f,*a,**k):
        if isinstance(f,str) and f.startswith('/data/xinyuan/GOAI_ai4s_env/'):
            rel=f.replace('/data/xinyuan/GOAI_ai4s_env/','')
            for _b in (_R, _o.path.join(_R,'e44_tide')):
                _p=_o.path.join(_b,rel)
                if _o.path.exists(_p): return _real_open(_p,*a,**k)
                _p2=_o.path.join(_b,_o.path.basename(rel))
                if _o.path.exists(_p2): return _real_open(_p2,*a,**k)
        return _real_open(f,*a,**k)
# --- 垫片结束 ---


NT = 8640                     # 与全部既有 run 同时长（3 天）
KNOBS = {
    "VISC2":   [0.0, 50.0, 150.0, 400.0, 800.0, 1500.0, 2747.0],
    "VISC4":   [0.0, 1e7, 1e8, 5e8, 1e9, 3e9, 1e10],
    "AKV_BAK": [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 3e-1, 1.0],
    "TNU2":    [0.0, 5.0, 12.5, 25.0, 37.5, 50.0, 75.0],
}
BATHY = ("r26steep", "flat")


def main():
    acts = []
    for k, vals in KNOBS.items():
        for v in vals:
            for b in BATHY:
                acts.append(dict(bathy=b, ntimes=NT, seed=0, **{k: v}))
    print(f"共 {len(acts)} 个 run（{len(KNOBS)} 旋钮 × 7 档 × {len(BATHY)} 地形）")

    env = SigmaPGEEnv(expose_truth=False, max_workers=16)
    t0 = time.time()
    res = env.step_batch(acts)
    print(f"wall={time.time()-t0:.0f}s  平均 {(time.time()-t0)/len(acts):.1f}s/run\n")

    out = []
    for a, (obs, info) in zip(acts, res):
        k = [x for x in a if x in KNOBS][0]
        out.append(dict(knob=k, val=a[k], bathy=a["bathy"],
                        run_id=info.get("run_id"), obs=obs))
    json.dump(out, open("/data/xinyuan/GOAI_ai4s_env/ledger/knob_sweep_diag45.json", "w"),
              ensure_ascii=False, indent=1)

    for k in KNOBS:
        print("=" * 74)
        print(f"■ {k}")
        print(f"{'值':>10} | {'r26 |U|max':>11} {'r26 深层':>10} {'r26状态':>8}"
              f" | {'平底|U|max':>11} {'平底深层':>10}")
        print("-" * 74)
        for v in KNOBS[k]:
            r = next((o for o in out if o["knob"] == k and o["val"] == v
                      and o["bathy"] == "r26steep"), None)
            f = next((o for o in out if o["knob"] == k and o["val"] == v
                      and o["bathy"] == "flat"), None)
            def cell(o, key, w=11, p=3):
                if o is None or not o["obs"].get("valid"):
                    return f"{'—':>{w}}"
                return f"{o['obs'][key]:>{w}.{p}f}"
            st = ("OK" if r and r["obs"].get("valid")
                  else "崩溃" if r and r["obs"].get("crashed") else "未完赛")
            print(f"{v:>10g} | {cell(r,'u_max')} {cell(r,'deep_rms_800',10,4)}"
                  f" {st:>8} | {cell(f,'u_max')} {cell(f,'deep_rms_800',10,4)}")
    print("=" * 74)
    print("→ ledger/knob_sweep_diag45.json")


if __name__ == "__main__":
    main()
