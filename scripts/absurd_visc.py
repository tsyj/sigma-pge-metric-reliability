#!/usr/bin/env python
"""E34：把黏性拧到物理荒谬的量级 —— 代理指标一路「改善」，模型掉到真值以下。

E32 里 `random`/`grid` 靠换地形刷分（问题不存在 → 分数完美）。
本脚本问：**不换地形，只把旋钮拧到荒谬值，能不能达到同样效果？**

平底对照（σ-PGE 按构造为零）的深层 rms ≈ 0.026–0.030 —— 那是「完美分数」的下限。
如果在 r26steep 上把 VISC2 拧到 3 万，读数也逼近这个下限，
那么**代理指标已经无法区分「问题解决了」和「一切都被阻尼没了」**。
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import SigmaPGEEnv

VS = [50., 400., 2747., 5000., 10000., 30000., 100000.]
NT = 8640            # 1 天，与真值第 1 天配对


def main():
    env = SigmaPGEEnv(expose_truth=True, max_workers=16)
    acts = [dict(bathy="r26steep", VISC2=v, ntimes=NT, seed=0) for v in VS]
    res = env.step_batch(acts)
    actsF = [dict(bathy="flat", VISC2=v, ntimes=NT, seed=0) for v in (50., 30000.)]
    resF = env.step_batch(actsF)

    print("=" * 90)
    print("把黏性拧到物理荒谬的量级（典型海洋值 1–100 m2/s）")
    print("=" * 90)
    print(f"{'VISC2':>9} {'状态':>6} {'深层rms':>9} {'|U|max':>9} {'真值|U|max':>11} "
          f"{'ROMS/真值':>10} {'误差rms':>9}")
    print("-" * 90)
    rows = []
    for a, (o, i) in zip(acts, res):
        h = (i.get("hidden") or {})
        if not o.get("valid"):
            st = "崩溃" if o.get("crashed") else "未完赛"
            print(f"{a['VISC2']:>9g} {st:>6}")
            rows.append(dict(visc=a["VISC2"], valid=False))
            continue
        tm = h.get("truth_max"); um = o["u_max"]
        print(f"{a['VISC2']:>9g} {'OK':>6} {o['deep_rms_800']:>9.4f} {um:>9.3f} "
              f"{tm:>11.3f} {um/tm:>9.2f}x {h.get('err_rms_vs_truth', float('nan')):>9.3f}")
        rows.append(dict(visc=a["VISC2"], valid=True, deep=o["deep_rms_800"],
                         umax=um, truth_max=tm, ratio=um / tm,
                         err_rms=h.get("err_rms_vs_truth")))
    print("-" * 90)
    flat = {}
    for a, (o, _) in zip(actsF, resF):
        if o.get("valid"):
            flat[a["VISC2"]] = o["deep_rms_800"]
            print(f"  平底对照 VISC2={a['VISC2']:>6g}: 深层rms = {o['deep_rms_800']:.4f}"
                  f"   <- sigma-PGE 按构造为零，这是「完美分数」的下限")

    ok = [r for r in rows if r.get("valid")]
    if ok and flat:
        floor = min(flat.values())
        best = min(ok, key=lambda r: r["deep_rms"])
        base = next(r for r in ok if r["visc"] == 50.)
        print()
        print("=" * 90)
        print("读数")
        print("=" * 90)
        print(f"  默认 VISC2=50    深层rms {base['deep_rms']:.4f}   "
              f"ROMS/真值 {base['ratio']:.2f}x")
        print(f"  最优 VISC2={best['visc']:.0f}  深层rms {best['deep_rms']:.4f}   "
              f"ROMS/真值 {best['ratio']:.2f}x")
        print(f"  平底下限          深层rms {floor:.4f}")
        print(f"\n  代理指标改善 {(1-best['deep_rms']/base['deep_rms'])*100:.1f}%，"
              f"已到平底下限的 {best['deep_rms']/floor:.1f} 倍以内")
        if best["ratio"] < 1:
            print(f"  但模型流速只剩真值的 {best['ratio']*100:.0f}% "
                  f"—— **掉到真值以下，真实环流被阻尼掉了**")
        print(f"  误差 rms 反而从 {base['err_rms']:.3f} 变到 {best['err_rms']:.3f}")

    json.dump(dict(scan=rows, flat_floor=flat),
              open("/data/xinyuan/GOAI_ai4s_env/ledger/absurd_visc.json", "w"),
              ensure_ascii=False, indent=1)
    print("\n-> ledger/absurd_visc.json")


if __name__ == "__main__":
    main()
