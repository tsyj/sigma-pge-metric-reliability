#!/usr/bin/env python
"""E39 让 Agent 提议自己的诊断指标 —— 补上闭环缺口的第 1 条。

## 为什么

12 轮实测后，B/C 条件的 Agent 无一例外要同一样东西：
「**误差范数或参考解对比**」「**判断究竟是真正控制误差还是仅仅过度耗散**」。
**它们想要的动作，在动作空间里根本不存在。** 它只能抱怨指标不好，不能改。

而这恰恰是赛题设计者说的核心（方石凯 19:02）：
> 「更鼓励大家去尝试定义：**在真实的科学环境下，什么是一个好的、新的指标或目标**」

## 做法

给 Agent 一个新动作：**提议一个诊断指标**。
它用给定的积木组合出一个标量，我们用**隐藏真值**去检验这个指标到底好不好。

积木（都是它已经能看到的量的推广，不给它真值）：
    场      : u, v, w, temp, zeta
    区域    : depth>D（深层）, depth<D（浅层）, all
    统计    : rms, max, mean_abs, p95
    可选    : 除以另一个同类量（做无量纲比值）

## 隐藏评估器怎么给指标打分（Agent 看不到这套逻辑）

对同一个指标 M，在**三个地形 × 一串黏性**上算出来，然后问三件事：

1. **分辨力**  M(r26steep) / M(flat) —— 平底上 σ-PGE 恒为零，
   分辨不出的指标根本没在测 σ-PGE。要求 ≥ 3×
2. **误差纯度**  在有真值的 r26steep 上，|M(ROMS) − M(真值)| / M(ROMS)
   —— 越接近 1，读数里越全是误差；接近 0 说明测的主要是真物理
3. **抗优化崩塌**  把 VISC2 从 50 拧到 2747，误差纯度掉多少
   —— 这是 E34 的核心发现：好指标的纯度不该随优化崩塌

综合分 = 分辨力(对数,截断) × 平均纯度 × (1 − 纯度跌幅)

## 用法
    python metric_proposal.py --rounds 3 --model deepseek-v4-pro
"""
import argparse, json, os, re, sys, time
import numpy as np
import netCDF4 as nc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import ENV, LEDGER, _truth, DT_ROMS
from sigma2z import roms_depths, to_z, rho_from_u
from mitgcm import read_field, iters
from llm_planner import client, ask, parse

FIELDS = ("u", "v", "w", "temp", "zeta")
STATS = ("rms", "max", "mean_abs", "p95")
NT = 8640          # 全部在第 1 天上评估
TRUTH_DIR = f"{ENV}/truth/hires_1pEm5"

SPEC = """你可以提议一个**新的诊断指标**。它必须能从下列积木组合出来：

  场      : u, v, w, temp, zeta
  区域    : {"deeper_than": D}（深于 D 米）/ {"shallower_than": D} / "all"
  统计    : rms, max, mean_abs, p95

格式（纯 JSON）：
{
  "name": "给你的指标起个名",
  "num": {"field": "u", "region": {"deeper_than": 800}, "stat": "rms"},
  "den": null,
  "why": "为什么你认为这个指标比 deep_rms_800 更能反映数值误差"
}

`den` 可以是 null（直接用分子），也可以是同样结构的另一个量（做成无量纲比值）。
比值往往更稳健 —— 例如「深层 rms ÷ 表层 rms」不受整体幅值缩放影响。

⚠️ 你**看不到真值**。你只能依据物理直觉和你已有的观测来设计。"""


# ---------------- 指标求值 ----------------
def _region_mask(depth, region):
    if region == "all" or region is None:
        return np.ones_like(depth, dtype=bool)
    if "deeper_than" in region:
        return depth > float(region["deeper_than"])
    if "shallower_than" in region:
        return depth < float(region["shallower_than"])
    return np.ones_like(depth, dtype=bool)


def _stat(v, s):
    v = v[np.isfinite(v)]
    if v.size == 0:
        return None
    if s == "rms":
        return float(np.sqrt((v ** 2).mean()))
    if s == "max":
        return float(np.abs(v).max())
    if s == "mean_abs":
        return float(np.abs(v).mean())
    if s == "p95":
        return float(np.percentile(np.abs(v), 95))
    return None


def eval_on_roms(run_dir, part):
    d = nc.Dataset(f"{run_dir}/out_his.nc")
    f = part.get("field", "u")
    if f not in d.variables:
        d.close(); return None
    arr = np.asarray(d[f][-1])
    h = np.asarray(d["h"][:]); Cs = np.asarray(d["Cs_r"][:])
    d.close()
    if arr.ndim == 2:                       # zeta：无深度维
        depth = np.zeros_like(arr)
    else:
        n = min(arr.shape[-1], h.shape[-1]); m = min(arr.shape[-2], h.shape[-2])
        arr = arr[..., :m, :n]
        depth = (-Cs[:, None, None] * h[None, :m, :n])
        if arr.shape[0] != depth.shape[0]:   # w/omega 在 w 点，层数多一层
            arr = arr[:depth.shape[0]]
    msk = _region_mask(depth, part.get("region"))
    return _stat(arr[msk] * (100.0 if f in ("u", "v", "w") else 1.0), part.get("stat", "rms"))


def eval_on_truth(part, day=1.0):
    f = part.get("field", "u")
    fmap = {"u": "U", "v": "V", "w": "W", "temp": "T"}
    if f not in fmap:
        return None
    it = int(round(day * 86400 / 30))
    try:
        arr = read_field(fmap[f], it, TRUTH_DIR)
    except Exception:
        return None
    RC = read_field("RC", None, TRUTH_DIR).ravel()
    depth = np.abs(RC)[:, None, None] * np.ones_like(arr)
    if arr.shape[0] != depth.shape[0]:
        arr = arr[:depth.shape[0]]
    msk = _region_mask(depth, part.get("region"))
    return _stat(arr[msk] * (100.0 if f in ("u", "v", "w") else 1.0), part.get("stat", "rms"))


def metric_value(spec, run_dir=None, on_truth=False):
    ev = (lambda p: eval_on_truth(p)) if on_truth else (lambda p: eval_on_roms(run_dir, p))
    num = ev(spec["num"])
    if num is None:
        return None
    den = spec.get("den")
    if den:
        dv = ev(den)
        if not dv:
            return None
        return num / dv
    return num


# ---------------- 隐藏评估器 ----------------
def find_run(bathy, visc2):
    best = None
    for line in open(LEDGER):
        r = json.loads(line)
        if (r["bathy"] == bathy and r["ntimes"] == NT and r["obs"].get("valid")
                and set(r["action"]) <= {"bathy", "VISC2", "ntimes", "seed"}):
            v = r["action"].get("VISC2", 0.0)
            if best is None or abs(v - visc2) < abs(best[0] - visc2):
                best = (v, r["run_id"])
    return best


def grade_metric(spec):
    """三项判据 → 综合分。Agent 看不到这套逻辑。"""
    out = {}
    lo, hi = find_run("r26steep", 50.0), find_run("r26steep", 2747.0)
    fl = find_run("flat", 50.0)
    if not (lo and hi and fl):
        return None
    M = lambda rid: metric_value(spec, run_dir=f"{ENV}/runs/{rid}")
    m_lo, m_hi, m_fl = M(lo[1]), M(hi[1]), M(fl[1])
    t = metric_value(spec, on_truth=True)
    if None in (m_lo, m_hi, m_fl) or t is None:
        return None
    out["m_r26_visc50"], out["m_r26_visc2747"], out["m_flat"] = m_lo, m_hi, m_fl
    out["m_truth"] = t
    # ① 分辨力
    out["discrimination"] = m_lo / max(abs(m_fl), 1e-12)
    # ② 误差纯度（两个黏性档）
    p_lo = abs(m_lo - t) / max(abs(m_lo), 1e-12)
    p_hi = abs(m_hi - t) / max(abs(m_hi), 1e-12)
    out["purity_visc50"], out["purity_visc2747"] = p_lo, p_hi
    out["purity_mean"] = 0.5 * (p_lo + p_hi)
    # ③ 抗优化崩塌
    out["purity_drop"] = max(0.0, p_lo - p_hi)
    disc = min(np.log10(max(out["discrimination"], 1.0)) / 2.0, 1.0)   # 100× 封顶
    out["score"] = float(disc * out["purity_mean"] * (1.0 - out["purity_drop"]))
    return out


BASELINE = dict(name="deep_rms_800（现有可见指标）",
                num=dict(field="u", region={"deeper_than": 800}, stat="rms"), den=None)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--model", default=os.environ.get("LLM_MODEL", "deepseek-v4-pro"))
    p.add_argument("--from-agent", default=None, help="用某个 agent 的历史当上下文")
    a = p.parse_args()

    base = grade_metric(BASELINE)
    print("=== 基线：现有可见指标 deep_rms_800 ===")
    for k in ("discrimination", "purity_visc50", "purity_visc2747", "purity_drop", "score"):
        print(f"  {k:18s} {base[k]:.4f}")

    ctx = ""
    if a.from_agent and os.path.exists(a.from_agent):
        d = json.load(open(a.from_agent))
        from llm_planner import history_table
        ctx = f"\n你之前的实验历史：\n{history_table(d['log'])}\n"

    cli = client()
    hist, results = [], [dict(spec=BASELINE, grade=base, round=-1)]
    for r in range(a.rounds):
        fb = ""
        if hist:
            fb = "\n你之前提议过的指标及其得分（分数越高越好，满分 1.0）：\n" + \
                 "\n".join(f"  {h['name']}: {h['score']:.4f}" for h in hist) + \
                 "\n（评分依据不告诉你 —— 请自己推断什么样的指标更好）\n"
        prompt = (f"{SPEC}\n{ctx}{fb}\n"
                  f"现有可见指标 `deep_rms_800` 的得分是 {base['score']:.4f}。"
                  f"请提议第 {r+1} 个指标，目标是超过它。")
        raw = ask(cli, a.model, [
            {"role": "system", "content": "你是数值海洋模式的诊断设计者。只输出纯 JSON。"},
            {"role": "user", "content": prompt}])
        try:
            spec = parse(raw)
        except Exception as e:
            print(f"  第 {r+1} 轮解析失败: {e}"); continue
        g = grade_metric(spec)
        if g is None:
            print(f"  第 {r+1} 轮 {spec.get('name')}: 无法求值（积木用错）")
            hist.append(dict(name=spec.get("name", f"m{r}"), score=0.0))
            results.append(dict(spec=spec, grade=None, round=r, raw=raw))
            continue
        print(f"\n  第 {r+1} 轮 · {spec.get('name')}")
        print(f"    {json.dumps({k: spec.get(k) for k in ('num','den')}, ensure_ascii=False)}")
        print(f"    分辨力 {g['discrimination']:>9.2f}×   纯度 {g['purity_mean']:.4f}   "
              f"纯度跌幅 {g['purity_drop']:.4f}   →  得分 {g['score']:.4f}"
              f"  {'⭐ 超过基线' if g['score'] > base['score'] else ''}")
        print(f"    它的理由: {str(spec.get('why',''))[:150]}")
        hist.append(dict(name=spec.get("name", f"m{r}"), score=g["score"]))
        results.append(dict(spec=spec, grade=g, round=r, raw=raw))

    best = max((x for x in results if x["grade"]), key=lambda x: x["grade"]["score"])
    print(f"\n{'='*74}")
    print(f"最佳：{best['spec'].get('name')}  得分 {best['grade']['score']:.4f}"
          f"（基线 {base['score']:.4f}）")
    print("=" * 74)
    json.dump(dict(baseline=dict(spec=BASELINE, grade=base), results=results),
              open(f"{ENV}/ledger/metric_proposal.json", "w"),
              ensure_ascii=False, indent=1, default=str)
    print("→ ledger/metric_proposal.json")


if __name__ == "__main__":
    main()
