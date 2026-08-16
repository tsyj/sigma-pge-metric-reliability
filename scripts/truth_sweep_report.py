#!/usr/bin/env python
"""汇总四组 MITgcm 真值扫描：真值对每个旋钮各自有多敏感？

配合 E28。ROMS 侧四个旋钮量程差异巨大，但真值侧呢？
真值几乎不动的旋钮 = 该旋钮上 ROMS 的全部变化都是数值伪迹。
"""
import glob, os, re, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mitgcm import read_field, iters

E = "/data/xinyuan/GOAI_ai4s_env"
PARAMS = ["viscAh", "viscA4", "viscAz", "diffKhT"]
LABEL = {"viscAh": "VISC2 ↔ viscAh   横向黏性",
         "viscA4": "VISC4 ↔ viscA4   双谐波黏性",
         "viscAz": "AKV_BAK ↔ viscAz 垂向黏性",
         "diffKhT": "TNU2 ↔ diffKhT  示踪扩散"}


DAY = float(os.environ.get("TRUTH_DAY", "1.0"))   # 必须与 ROMS run 的积分时长一致
DT_MIT = 30.0


def metrics(d):
    """取**指定时刻**的真值。

    ⚠ 第一版取 `it[-1]`（第 3 天），而 ROMS 扫描 run 是 ntimes=8640 × DT=10 s
    = **第 1 天** —— 拿第 1 天比第 3 天。真值在做惯性振荡，两者差很多
    （|U|max 第 1 天 9.24 vs 第 3 天 9.11，第 2 天节点处只有 0.88）。见 E29 撤回 #7。
    """
    it = iters("U", d)
    if not it:
        return None
    want = int(round(DAY * 86400 / DT_MIT))
    if want not in it:
        return None
    U = read_field("U", want, d)
    # ⚠ MITgcm 在 viscA4=1e10 处会打印 `STOP NORMAL END` 却输出全 NaN
    #   （日志里只有一行 IEEE_INVALID_FLAG / IEEE_OVERFLOW_FLAG）。
    #   只检查「正常结束」会被骗过 —— 与 E26 的 sed 静默失效同一类。
    if not np.isfinite(U).all():
        return None
    RC = read_field("RC", None, d).ravel()
    deep = np.abs(RC) > 800
    return dict(umax=float(np.abs(U).max() * 100),
                urms=float(np.sqrt((U ** 2).mean()) * 100),
                deep=float(np.sqrt((U[deep] ** 2).mean()) * 100))


def val_of(d, p):
    """从目录名反解参数值：sw_viscAh_1pEm4 → 1.E-4"""
    t = os.path.basename(d)[len(f"sw_{p}_"):]
    return float(t.replace("p", ".").replace("m", "-"))


def main():
    allout = {}
    for p in PARAMS:
        dirs = sorted(glob.glob(f"{E}/truth/sw_{p}_*"), key=lambda d: val_of(d, p))
        rows = []
        for d in dirs:
            if not os.path.exists(f"{d}/run.log"):
                continue
            if "STOP NORMAL END" not in open(f"{d}/run.log", errors="replace").read():
                continue
            m = metrics(d)
            if m:
                rows.append((val_of(d, p), m))
        if not rows:
            continue
        allout[p] = [dict(val=v, **m) for v, m in rows]

        print("=" * 72)
        print(f"■ {LABEL[p]}")
        print("=" * 72)
        print(f"{'真值参数':>12} {'|U|max':>10} {'|U|rms':>10} {'深层rms>800m':>14}")
        print("-" * 72)
        for v, m in rows:
            print(f"{v:>12g} {m['umax']:>10.4f} {m['urms']:>10.4f} {m['deep']:>14.6f}")
        u = [m["urms"] for _, m in rows]
        x = [m["umax"] for _, m in rows]
        dp = [m["deep"] for _, m in rows]
        print(f"\n  真值 |U|rms 变幅 {(max(u)/min(u)-1)*100:>7.2f}%   "
              f"|U|max 变幅 {(max(x)/min(x)-1)*100:>7.2f}%   "
              f"深层 max {max(dp):.6f}")
        print()

    json.dump(allout, open(f"{E}/ledger/truth_sweeps.json", "w"),
              ensure_ascii=False, indent=1)
    print("=" * 72)
    print("→ ledger/truth_sweeps.json")


if __name__ == "__main__":
    main()
