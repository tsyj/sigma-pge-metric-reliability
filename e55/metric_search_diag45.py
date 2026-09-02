#!/usr/bin/env python
"""E40 穷举指标空间 —— 存在能识别"换了问题"的可见指标吗？

## 问题的由来

E38 证明：`deep_rms_800` 在**问题实例内**是极好的排序器（与隐藏技巧评分 ρ = −0.95），
但它排出的**全局前 8 名全是 flat**（σ-PGE 按构造为零的对照地形）。
E36/E39 证明：Agent 会因此把 90% 的步数耗在 flat，并因此把世界模型学错两个数量级。

于是问题是：**换一个指标能解决吗？**

## 判据（两条必须同时满足）

- **A · 实例内有效**：在有真值的 `r26steep` 上，与隐藏技巧评分的 Spearman ρ ≤ −0.7
  （指标低 ⇔ 技巧高）
- **B′ · 抗换问题（配对版）**：在**同参数**的 (r26steep, flat) 配对上，
  M(flat) ≥ M(r26steep) 的比例。要求 ≥ 0.9。

  ⚠️ 第一版用的是「全局最小值之比」，**那个判据是错的** ——
  它只看两个地形各自的最好读数，可能只差毫厘且只在一个极端点上成立。
  实测：按全局最小值判据有 581 个候选"通过"，但拿去做配对检验，
  最好的那个仍然在 **29/32** 组配对里被 flat 击败。**必须用配对。**

## 搜索空间

    场    : u, v, w, temp, zeta          （输出文件里真有的）
    区域  : deeper_than {200,400,800,1500} / shallower_than {50,200} / all
    统计  : rms, max, mean_abs, p95
    比值  : 分子 / 分母（分母可为空）

共 5×7×4 = 140 个基本量，两两配比 → 约 1.97 万个候选指标。
先对每个 run 预计算 140 个基本量，比值就只是除法，很快。

## 预期（写在跑之前）

我预测**找不到**同时满足 A 和 B 的指标。理由：观测空间里**没有任何描述"问题是什么"的量**
（Agent 能设定 `bathy`，却看不到地形陡度）。若如此，这是一条关于**观测空间**的结论，
而不是关于"指标设计技巧"的结论。
"""
import json, os, sys, itertools, warnings
import numpy as np
import netCDF4 as nc

warnings.filterwarnings("ignore")
sys.path.insert(0, "/data/xinyuan/GOAI_ai4s_env/scripts"); sys.path.insert(0, "/data/xinyuan/GOAI_ai4s_env/e55")
from env2_diag45 import ENV, LEDGER

FIELDS = ("u", "v", "w", "temp", "zeta")
REGIONS = [("all", None),
           ("d200", ("deeper", 200)), ("d400", ("deeper", 400)),
           ("d800", ("deeper", 800)), ("d1500", ("deeper", 1500)),
           ("s50", ("shallow", 50)), ("s200", ("shallow", 200))]
STATS = ("rms", "max", "mean_abs", "p95")


def base_quantities(run_dir):
    """一次打开文件，算出全部 140 个基本量。"""
    fn = f"{run_dir}/out_his.nc"
    if not os.path.exists(fn):
        return None
    try:
        d = nc.Dataset(fn)
        h = np.asarray(d["h"][:]); Cs = np.asarray(d["Cs_r"][:])
        out = {}
        for f in FIELDS:
            if f not in d.variables:
                continue
            arr = np.asarray(d[f][-1])
            scale = 100.0 if f in ("u", "v", "w", "zeta") else 1.0
            arr = arr * scale
            if arr.ndim == 2:
                depth = np.zeros_like(arr)
            else:
                n = min(arr.shape[-1], h.shape[-1]); m = min(arr.shape[-2], h.shape[-2])
                arr = arr[..., :m, :n]
                depth = -Cs[:, None, None] * h[None, :m, :n]
                if arr.shape[0] != depth.shape[0]:
                    arr = arr[:depth.shape[0]]
            for rname, rspec in REGIONS:
                if rspec is None:
                    msk = np.ones_like(depth, dtype=bool)
                elif rspec[0] == "deeper":
                    msk = depth > rspec[1]
                else:
                    msk = depth < rspec[1]
                v = arr[msk]
                v = v[np.isfinite(v)]
                if v.size == 0:
                    continue
                av = np.abs(v)
                out[f"{f}|{rname}|rms"] = float(np.sqrt((v ** 2).mean()))
                out[f"{f}|{rname}|max"] = float(av.max())
                out[f"{f}|{rname}|mean_abs"] = float(av.mean())
                out[f"{f}|{rname}|p95"] = float(np.percentile(av, 95))
        d.close()
        return out
    except Exception:
        return None


def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    if np.std(ra) == 0 or np.std(rb) == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    # ---- 收集 run：r26steep（有隐藏技巧评分）与 flat（无真值，用于抗刷分判据）----
    reg = {}
    for l in open(LEDGER):
        r = json.loads(l)
        h = r.get("hidden") or {}
        if r["bathy"] == "r26steep" and r["obs"].get("valid") and "skill_vs_zero" in h:
            reg[r["run_id"]] = h["skill_vs_zero"]
    seen = {}
    for l in open(LEDGER):
        r = json.loads(l)
        if r["obs"].get("valid") and r["ntimes"] == 8640:
            seen[r["run_id"]] = r["bathy"]
    r26 = [(k, v) for k, v in seen.items() if v == "r26steep" and k in reg]
    flat = [(k, v) for k, v in seen.items() if v == "flat"]
    # 同参数配对（B′ 判据用）
    byp = {}
    for l in open(LEDGER):
        r = json.loads(l)
        if not (r["obs"].get("valid") and r["ntimes"] == 8640):
            continue
        a = r["action"]
        k = tuple(round(a.get(x, -1), 6) for x in ("VISC2", "VISC4", "AKV_BAK", "TNU2"))
        byp.setdefault(k, {})[r["bathy"]] = r["run_id"]
    PAIRS = [(v["r26steep"], v["flat"]) for v in byp.values()
             if "r26steep" in v and "flat" in v]
    print(f"  同参数配对 {len(PAIRS)} 组")
    print(f"  r26steep（有技巧评分）{len(r26)} 个   flat {len(flat)} 个")

    # ---- 预计算基本量 ----
    Q26, S26, QFL = [], [], []
    for rid, _ in r26:
        q = base_quantities(f"{ENV}/runs_diag45/{rid}")
        if q:
            Q26.append(q); S26.append(reg[rid])
    for rid, _ in flat:
        q = base_quantities(f"{ENV}/runs_diag45/{rid}")
        if q:
            QFL.append(q)
    keys = sorted(set.intersection(*[set(q) for q in Q26 + QFL]))
    print(f"  可用基本量 {len(keys)} 个；r26 {len(Q26)} run，flat {len(QFL)} run")

    M26 = np.array([[q[k] for k in keys] for q in Q26])     # (n26, K)
    MFL = np.array([[q[k] for k in keys] for q in QFL])     # (nfl, K)
    S = np.array(S26)
    # 配对矩阵
    P26, PFL = [], []
    for a, b in PAIRS:
        qa, qb = base_quantities(f"{ENV}/runs_diag45/{a}"), base_quantities(f"{ENV}/runs_diag45/{b}")
        if qa and qb and all(k in qa and k in qb for k in keys):
            P26.append([qa[k] for k in keys]); PFL.append([qb[k] for k in keys])
    P26, PFL = np.array(P26), np.array(PFL)
    print(f"  可用配对 {len(P26)} 组")

    # ---- 遍历所有 分子/分母 组合 ----
    print("\n  遍历 %d × %d 个候选指标…" % (len(keys), len(keys) + 1), flush=True)
    best, rows = [], []
    EPS = 1e-12
    for i, kn in enumerate(keys):
        cand = [(kn, None, M26[:, i], MFL[:, i])]
        for j, kd in enumerate(keys):
            if i == j:
                continue
            d26, dfl = M26[:, j], MFL[:, j]
            if np.any(np.abs(d26) < EPS) or np.any(np.abs(dfl) < EPS):
                continue
            cand.append((kn, kd, M26[:, i] / d26, MFL[:, i] / dfl))
        for kn_, kd_, v26, vfl in cand:
            if not (np.all(np.isfinite(v26)) and np.all(np.isfinite(vfl))):
                continue
            if np.any(v26 <= 0) or np.any(vfl <= 0):
                continue
            rho = spearman(v26, S)
            # B′ 配对判据
            i_ = keys.index(kn_)
            if kd_ is None:
                p26v, pflv = P26[:, i_], PFL[:, i_]
            else:
                j_ = keys.index(kd_)
                if np.any(np.abs(P26[:, j_]) < EPS) or np.any(np.abs(PFL[:, j_]) < EPS):
                    continue
                p26v, pflv = P26[:, i_] / P26[:, j_], PFL[:, i_] / PFL[:, j_]
            if not (np.all(np.isfinite(p26v)) and np.all(np.isfinite(pflv))):
                continue
            paired = float(np.mean(pflv >= p26v))
            rows.append((kn_, kd_, rho, paired))
    print(f"  有效候选 {len(rows)} 个")

    ok = [r for r in rows if r[2] <= -0.7 and r[3] >= 0.9]
    near = [r for r in rows if r[2] <= -0.7]
    print(f"\n{'='*86}")
    print("判据 A（实例内 ρ ≤ −0.7）与 B′（配对抗刷分率 ≥ 0.9）")
    print("=" * 86)
    print(f"  满足 A 的：{len(near)}")
    print(f"  同时满足 A 和 B 的：**{len(ok)}**")

    base = [r for r in rows if r[0] == "u|d800|rms" and r[1] is None]
    if base:
        print(f"\n  基线 deep_rms_800:  ρ = {base[0][2]:+.4f}   "
              f"配对抗刷分率 = {base[0][3]:.3f}  （0 表示每一组配对里平底都更低）")

    if ok:
        ok.sort(key=lambda r: (r[2], -r[3]))
        print(f"\n  前 12 个同时满足两条的：")
        print(f"  {'分子':>22} {'分母':>22} {'ρ':>8} {'抗刷分率':>9}")
        for kn_, kd_, rho, leak in ok[:12]:
            print(f"  {kn_:>22} {str(kd_):>22} {rho:>8.3f} {leak:>9.3f}")
    else:
        print("\n  ⭐ **一个都没有。**")
        near.sort(key=lambda r: -r[3])
        print(f"\n  在满足 A 的候选里，配对抗刷分率最高的 10 个：")
        print(f"  {'分子':>22} {'分母':>22} {'ρ':>8} {'抗刷分率':>9}")
        for kn_, kd_, rho, leak in near[:10]:
            print(f"  {kn_:>22} {str(kd_):>22} {rho:>8.3f} {leak:>9.3f}")

    json.dump(dict(n_candidates=len(rows), n_pass_A=len(near), n_pass_AB=len(ok),
                   baseline=base[0] if base else None,
                   top=[list(r) for r in (ok[:30] if ok else near[:30])]),
              open(f"{ENV}/ledger/metric_search_diag45.json", "w"),
              ensure_ascii=False, indent=1)
    print(f"\n→ ledger/metric_search_diag45.json")


if __name__ == "__main__":
    main()
