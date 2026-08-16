#!/usr/bin/env python
"""E38 预测-检验汇总 —— Agent 的结论有没有预测力？

一个不能预测的结论只是对已有数据的描述。本报告回答：
  Q1  Agent 的预测能不能打败「最近邻」？（最低门槛：比查表强）
  Q2  能不能打败「高斯过程后验」？（强 baseline：纯统计外推）
  Q3  内插 vs 外推：哪种情形下它更靠谱？
  Q4  H5 崩溃阈值能否跨地形迁移？（它在 r26steep 学到的规律，搬到 mit 对不对）
  Q5  条件 A/B/C 的 Agent，预测力有差别吗？
"""
import json, os, sys
import numpy as np

E = "/data/xinyuan/GOAI_ai4s_env"
d = json.load(open(f"{E}/ledger/predict_test.json"))
truth, agents, held = d["truth"], d["agents"], d["held_out"]
KIND = {h["name"]: h["kind"] for h in held}


def m(v):
    v = [x for x in v if x is not None and np.isfinite(x)]
    return float(np.mean(v)) if v else float("nan")


print("=" * 96)
print("留出配置的真实结果（所有 Agent 都没跑过）")
print("=" * 96)
for h in held:
    n = h["name"]; t = truth[n]
    dr = t.get("deep_rms_800")
    a = {k: v for k, v in h["action"].items() if k != "seed"}
    print(f"  {n} ({h['kind']:<12}) {json.dumps(a, ensure_ascii=False)}")
    print(f"      valid={t.get('valid')}  crashed={t.get('crashed')}  "
          f"deep_rms={(f'{dr:.4f}' if dr is not None else '—')}")

print()
print("=" * 96)
print("Q1/Q2 · 预测精度（|log10(预测/实测)|，越小越好）")
print("=" * 96)
print(f"{'Agent':>22} | {'LLM':>7} {'最近邻':>7} {'GP后验':>7} {'中位数':>7} | 判定")
print("-" * 96)
rows = []
for a in agents:
    llm = m([i["err"] for i in a["items"]])
    nn = m([_ for _ in (
        (abs(np.log10(i["nn"] / i["actual"])) if i["nn"] and i["actual"] else None)
        for i in a["items"])])
    gp = m([_ for _ in (
        (abs(np.log10(i["gp"] / i["actual"])) if i["gp"] and i["actual"] else None)
        for i in a["items"])])
    md = m([_ for _ in (
        (abs(np.log10(i["med"] / i["actual"])) if i["med"] and i["actual"] else None)
        for i in a["items"])])
    beat_nn = llm < nn if np.isfinite(llm) and np.isfinite(nn) else None
    beat_gp = llm < gp if np.isfinite(llm) and np.isfinite(gp) else None
    v = ("✓胜最近邻+GP" if beat_nn and beat_gp else
         "✓胜最近邻" if beat_nn else
         "✓胜GP" if beat_gp else "✗ 都没赢")
    print(f"{a['agent']:>22} | {llm:>7.3f} {nn:>7.3f} {gp:>7.3f} {md:>7.3f} | {v}")
    rows.append(dict(agent=a["agent"], cond=a["condition"], llm=llm, nn=nn, gp=gp, med=md))
print("-" * 96)
print(f"{'平均':>22} | {m([r['llm'] for r in rows]):>7.3f} "
      f"{m([r['nn'] for r in rows]):>7.3f} {m([r['gp'] for r in rows]):>7.3f} "
      f"{m([r['med'] for r in rows]):>7.3f}")
nb = sum(1 for r in rows if r["llm"] < r["nn"])
gb = sum(1 for r in rows if r["llm"] < r["gp"])
print(f"\n  打败最近邻：{nb}/{len(rows)}    打败 GP 后验：{gb}/{len(rows)}")

print()
print("=" * 96)
print("Q3 · 内插 vs 外推")
print("=" * 96)
for n in [h["name"] for h in held]:
    es = [i["err"] for a in agents for i in a["items"]
          if i["name"] == n and i["err"] is not None]
    ns = [abs(np.log10(i["nn"] / i["actual"])) for a in agents for i in a["items"]
          if i["name"] == n and i["nn"] and i["actual"]]
    t = truth[n]
    print(f"  {n} ({KIND[n]:<12}) 实测 deep_rms="
          f"{(f'{t.get(chr(100)+chr(101)+chr(101)+chr(112)+chr(95)+chr(114)+chr(109)+chr(115)+chr(95)+chr(56)+chr(48)+chr(48)):.4f}' if t.get('deep_rms_800') else '崩溃'):>9}"
          f"   LLM 平均误差 {m(es):.3f}   最近邻 {m(ns):.3f}   n={len(es)}")

print()
print("=" * 96)
print("Q4 · H5 跨地形迁移（r26steep 学到的崩溃阈值，搬到 mit 对吗）")
print("=" * 96)
t5 = truth["H5"]
print(f"  实测：mit + TNU2=200 → crashed={t5.get('crashed')}  valid={t5.get('valid')}")
print(f"  参考：r26steep 上崩溃阈值在 90–100 之间；mit 上 50 通过、1000 崩溃")
ok = wrong = 0
for a in agents:
    it = next((i for i in a["items"] if i["name"] == "H5"), None)
    if not it:
        continue
    hit = bool(it["pred_crash"]) == bool(it["actual_crash"])
    ok += hit; wrong += (not hit)
    print(f"    {a['agent']:>22}  预测崩溃={str(bool(it['pred_crash'])):<5} "
          f"{'✓' if hit else '✗'}")
print(f"\n  预测正确 {ok}/{ok+wrong}")

print()
print("=" * 96)
print("Q5 · 探索条件对预测力的影响")
print("=" * 96)
for c in ("A", "B", "C"):
    g = [r for r in rows if r["cond"] == c]
    if g:
        print(f"  条件 {c}  n={len(g)}  LLM {m([r['llm'] for r in g]):.3f}  "
              f"最近邻 {m([r['nn'] for r in g]):.3f}  GP {m([r['gp'] for r in g]):.3f}")

json.dump(rows, open(f"{E}/ledger/predict_report.json", "w"),
          ensure_ascii=False, indent=1)
print(f"\n→ ledger/predict_report.json")
