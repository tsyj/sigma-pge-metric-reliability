#!/usr/bin/env python
"""端到端回归 —— 改完 env2.py 后跑一遍，确认四条关键路径都通。

覆盖的路径（都是踩过坑的地方）：
  1. 默认路径
  2. 科学计数法参数（AKV_BAK=1e-6 → 必须写成 1.0d-6，不能是 1e-06d0）
  3. 多值参数（TNU2 == v v，两个值都要换）
  4. 无真值配置（flat，隐藏评估器应返回空而不是报错）
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import SigmaPGEEnv, LEDGER

ACTS = [
    dict(bathy="r26steep", VISC2=50.0,   ntimes=1440, seed=0),
    dict(bathy="r26steep", AKV_BAK=1e-6, ntimes=1440, seed=0),
    dict(bathy="r26steep", TNU2=25.0,    ntimes=1440, seed=0),
    dict(bathy="flat",     VISC2=50.0,   ntimes=1440, seed=0),
]


def main():
    env = SigmaPGEEnv(expose_truth=True, max_workers=4)
    t0 = time.time()
    res = env.step_batch(ACTS)
    print(f"=== 端到端回归  wall={time.time()-t0:.0f}s ===\n")
    ok = True
    for a, (o, i) in zip(ACTS, res):
        kn = [k for k in a if k not in ("bathy", "ntimes", "seed")]
        lab = f"{a['bathy']}/{kn[0]}={a[kn[0]]:g}" if kn else a["bathy"]
        h = i.get("hidden") or {}
        ss = h.get("skill_vs_zero")
        ss_s = f"{ss:.3f}" if ss is not None else "—（该配置无真值）"
        d = o.get("deep_rms_800")
        d_s = f"{d:.4f}" if d is not None else "—"
        print(f"  {lab:<26} valid={str(o.get('valid')):<5} 深层={d_s:<9} SS={ss_s}")
        if not o.get("valid"):
            ok = False

    # 检查写入的 roms.in 里参数是否真的生效
    print()
    for a, (o, i) in zip(ACTS, res):
        rd = i["run_dir"]
        for k in a:
            if k in ("bathy", "ntimes", "seed"):
                continue
            for line in open(f"{rd}/roms.in", errors="replace"):
                t = line.split()
                if t and t[0] == k:
                    print(f"  {os.path.basename(rd)[:14]:<15} {line.rstrip()[:56]}")
                    break

    last = json.loads(open(LEDGER).readlines()[-1])
    print(f"\n  ledger 末条 bin={last.get('bin')} sha={str(last.get('bin_sha256'))[:16]}…")
    print(f"  hidden 键: {sorted((last.get('hidden') or {}).keys())}")
    print("\n  " + ("✓ 四条路径全通" if ok else "✗ 有 run 未完赛"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
