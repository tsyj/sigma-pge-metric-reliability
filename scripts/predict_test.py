#!/usr/bin/env python
"""E38 预测-检验环 —— 闭环缺的最后一环。

## 为什么必须做

科学的闭环是：**观察 → 假设 → 预测 → 检验 → 修正**。
我们此前只有「观察 → 行动 → 反馈 → 修正下一步」，
**从未让 Agent 预测过任何东西**。而一个不能预测的结论，只是对已有数据的描述。

12 轮 Agent 都给出了 `what_controls_the_error`（"误差主要受地形和横向耗散控制"）。
本脚本检验：**这个结论有没有预测力？**

## 设计

同一批 **留出配置**（held-out，所有 Agent 都没跑过）问所有 Agent，
它们**只能看自己的历史**。然后我们真跑这些配置，比对。

| # | 配置 | 类型 | 测什么 |
|---|---|---|---|
| H1 | r26steep, VISC2=700 | 内插 | 学没学到 VISC2 的形状 |
| H2 | flat, VISC2=300 | 内插 + 换地形 | 跨地形的定量迁移 |
| H3 | r26steep, VISC4=5e9 | 对数内插 | 双谐波的定量理解 |
| H4 | r26steep, AKV_BAK=0.05 | 内插 | 垂向黏性（多数 Agent 断言"影响很小"）|
| H5 | **mit, TNU2=200** | **跨地形外推** | **崩溃阈值能否迁移** |

H5 是关键：`r26steep` 上崩溃阈值在 90–100 之间（实测 90 通过、100 崩），
`mit` 上 50 通过、1000 崩溃 —— **阈值位置不同，且我们自己也不知道在哪**。
Agent 若把 r26steep 的阈值直接搬到 mit，就会预测崩溃。

## 参照系（必须有，否则不知道"预测得准"是什么意思）

- **最近邻**：取 Agent 历史中最接近的配置的读数
- **历史中位数**：无信息基线
- **高斯过程后验**：用 Agent 自己的历史拟合 GP —— 纯统计外推的强 baseline

评分：`|log10(预测 / 实测)|`（深层 rms 跨数量级，必须用对数）
"""
import argparse
import glob
import json
import os
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import SigmaPGEEnv
from llm_planner import client, ask, parse, history_table, ACTION_DOC

ENV = "/data/xinyuan/GOAI_ai4s_env"
NT = 8640          # 全部留出配置固定 1 天，避开积分时长混淆

HELD_OUT = [
    dict(name="H1", kind="内插",
         action=dict(bathy="r26steep", VISC2=700.0, ntimes=NT, seed=0)),
    dict(name="H2", kind="内插+换地形",
         action=dict(bathy="flat", VISC2=300.0, ntimes=NT, seed=0)),
    dict(name="H3", kind="对数内插",
         action=dict(bathy="r26steep", VISC4=5e9, ntimes=NT, seed=0)),
    dict(name="H4", kind="内插",
         action=dict(bathy="r26steep", AKV_BAK=0.05, ntimes=NT, seed=0)),
    dict(name="H5", kind="跨地形外推",
         action=dict(bathy="mit", TNU2=200.0, ntimes=NT, seed=0)),
]

ASK = """以上是你之前做过的全部实验。现在**不再给你新的实验机会**。

请预测下面 5 个**你没有试过**的配置的结果。全部 ntimes=8640（1 天）。

{table}

纯 JSON 回复：
{{"predictions": [
   {{"name": "H1", "deep_rms_800": <数值>, "will_crash": false, "why": "一句话依据"}},
   ... 共 5 条 ...
 ],
 "which_am_i_least_sure_about": "哪一个你最没把握，为什么"}}

注意：`deep_rms_800` 跨若干数量级，请给出你认为最可能的数值（不是区间）。
如果你认为某个配置会崩溃，把 `will_crash` 设为 true，`deep_rms_800` 仍给一个数。"""


def heldout_table():
    rows = ["名称 | 配置"]
    for h in HELD_OUT:
        a = {k: v for k, v in h["action"].items() if k != "seed"}
        rows.append(f"{h['name']} | {json.dumps(a, ensure_ascii=False)}")
    return "\n".join(rows)


# ---------------- 参照系 ----------------
def _vec(a):
    """把动作映射到可比较的数值向量（对数尺度处理跨量级的量）。"""
    b = {"flat": 0.0, "mit": 1.0, "r26steep": 2.0}.get(a.get("bathy", "r26steep"), 2.0)
    return np.array([
        b * 3.0,                                     # 地形（加权，因为影响最大）
        np.log10(a.get("VISC2", 50.0) + 1.0),
        np.log10(a.get("VISC4", 0.0) + 1.0) / 3.0,
        np.log10(a.get("AKV_BAK", 1e-5)) / 3.0,
        np.log10(a.get("TNU2", 50.0) + 1.0),
    ])


def baseline_nn(hist, target):
    """最近邻：历史里最像的那个配置的读数。"""
    ok = [h for h in hist if h["obs"].get("deep_rms_800") is not None]
    if not ok:
        return None
    t = _vec(target)
    d = [np.linalg.norm(_vec(h["action"]) - t) for h in ok]
    return ok[int(np.argmin(d))]["obs"]["deep_rms_800"]


def baseline_median(hist):
    v = [h["obs"]["deep_rms_800"] for h in hist
         if h["obs"].get("deep_rms_800") is not None]
    return float(np.median(v)) if v else None


def baseline_gp(hist, target):
    """高斯过程后验均值（在 log10 空间拟合）—— 纯统计外推的强 baseline。"""
    ok = [h for h in hist if h["obs"].get("deep_rms_800") is not None
          and h["obs"]["deep_rms_800"] > 0]
    if len(ok) < 3:
        return None
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern, ConstantKernel, WhiteKernel
    X = np.array([_vec(h["action"]) for h in ok])
    y = np.log10([h["obs"]["deep_rms_800"] for h in ok])
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Xs = (X - mu) / sd
    k = (ConstantKernel(1.0, (1e-3, 1e3))
         * Matern(length_scale=1.0, length_scale_bounds=(1e-2, 1e2), nu=2.5)
         + WhiteKernel(1e-4, (1e-8, 1e0)))
    gp = GaussianProcessRegressor(kernel=k, n_restarts_optimizer=3,
                                  random_state=0).fit(Xs, y)
    p = gp.predict(((_vec(target) - mu) / sd).reshape(1, -1))[0]
    return float(10 ** p)


def score(pred, actual):
    """|log10(预测/实测)|；预测或实测为 0/None 时返回 None。"""
    if pred is None or actual is None or pred <= 0 or actual <= 0:
        return None
    return abs(np.log10(pred / actual))


# ---------------- 主流程 ----------------
def run_heldout():
    """真跑 5 个留出配置（所有 Agent 共用，只跑一次）。"""
    env = SigmaPGEEnv(expose_truth=True, max_workers=5)
    res = env.step_batch([h["action"] for h in HELD_OUT])
    truth = {}
    for h, (obs, info) in zip(HELD_OUT, res):
        truth[h["name"]] = dict(
            valid=obs.get("valid"), crashed=obs.get("crashed"),
            deep_rms_800=obs.get("deep_rms_800"), u_max=obs.get("u_max"),
            hidden=info.get("hidden"), run_id=info.get("run_id"))
    json.dump(truth, open(f"{ENV}/ledger/heldout_truth.json", "w"),
              ensure_ascii=False, indent=1)
    return truth


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=os.environ.get("LLM_MODEL", "deepseek-v4-pro"))
    p.add_argument("--run-heldout", action="store_true", help="真跑 5 个留出配置")
    a = p.parse_args()

    tf = f"{ENV}/ledger/heldout_truth.json"
    if a.run_heldout or not os.path.exists(tf):
        print("跑留出配置（5 个，并行）…", flush=True)
        t0 = time.time()
        truth = run_heldout()
        print(f"  完成 {time.time()-t0:.0f}s")
    else:
        truth = json.load(open(tf))
    print("\n=== 留出配置的真实结果 ===")
    for h in HELD_OUT:
        t = truth[h["name"]]
        dr = t.get("deep_rms_800")
        print(f"  {h['name']} ({h['kind']}): valid={t.get('valid')} "
              f"crashed={t.get('crashed')} deep_rms="
              f"{(f'{dr:.4f}' if dr is not None else '—')}")

    cli = client()
    out = []
    for f in sorted(glob.glob(f"{ENV}/ledger/agent_llm_*.json")):
        d = json.load(open(f))
        tag = f"{d.get('condition')}/{d.get('model','').replace('deepseek-','')}/s{d.get('seed')}"
        hist = d["log"]
        prompt = (f"{ACTION_DOC}\n\n你的历史：\n{history_table(hist)}\n\n"
                  + ASK.format(table=heldout_table()))
        try:
            raw = ask(cli, a.model, [
                {"role": "system", "content": "你是一个数值海洋模式的探索助手。"
                                              "只输出纯 JSON，不要 markdown。"},
                {"role": "user", "content": prompt}])
            j = parse(raw)
        except Exception as e:
            print(f"  {tag}: 预测失败 {str(e)[:80]}")
            continue
        preds = {x.get("name"): x for x in j.get("predictions", [])}
        rec = dict(agent=tag, condition=d.get("condition"), model=d.get("model"),
                   seed=d.get("seed"), raw=raw, parsed=j, items=[])
        for h in HELD_OUT:
            n = h["name"]
            t = truth[n]
            pv = (preds.get(n) or {}).get("deep_rms_800")
            pc = bool((preds.get(n) or {}).get("will_crash", False))
            rec["items"].append(dict(
                name=n, kind=h["kind"],
                pred=pv, pred_crash=pc,
                actual=t.get("deep_rms_800"), actual_crash=bool(t.get("crashed")),
                err=score(pv, t.get("deep_rms_800")),
                nn=baseline_nn(hist, h["action"]),
                gp=baseline_gp(hist, h["action"]),
                med=baseline_median(hist)))
        out.append(rec)
        errs = [i["err"] for i in rec["items"] if i["err"] is not None]
        print(f"  {tag}: 预测 {len(preds)}/5, 平均 |log10 误差| = "
              f"{np.mean(errs):.3f}" if errs else f"  {tag}: 无有效预测")

    json.dump(dict(held_out=HELD_OUT, truth=truth, agents=out),
              open(f"{ENV}/ledger/predict_test.json", "w"),
              ensure_ascii=False, indent=1, default=str)
    print(f"\n→ ledger/predict_test.json")


if __name__ == "__main__":
    main()
