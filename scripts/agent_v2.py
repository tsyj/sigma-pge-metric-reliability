#!/usr/bin/env python
"""Agent 探索循环 v2 —— 补 B 队/官方对标指出的两条缺口。

对标 Battery-Sim-Agent（KDD 2026，官方开放探索材料案例一）的探索规程：
    20 轮随机扰动建立局部敏感性知识 → 80 轮根据反馈形成假设、更新参数、写入动态记忆

本文件实现：
  1. **两阶段探索**：并行随机播种（建敏感性知识）→ 串行自适应（用记忆）
  2. **跨轮动态记忆**：结构化知识条目，Agent 每轮读写，写入探索日志
  3. **可切换 Planner**：bisect / bo / random / grid（后两者为参照系）

Agent 仍只看得见代理指标；真值只写日志供离线检查。
"""
import os, sys, json, time, argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import SigmaPGEEnv, grade, ACTION_SPACE, BATHY

ENV = "/data/xinyuan/GOAI_ai4s_env"
OBJ = "deep_rms_800"          # Agent 可见的优化目标（刻意用代理，不用真值）


# ============================ 动态记忆 ============================
class Memory:
    """跨轮结构化记忆。每条是一个可被后续轮次利用的知识条目。"""

    def __init__(self):
        self.facts = []          # 结构化知识
        self.notes = []          # 自然语言摘要（供 LLM Planner 读）

    def observe(self, action, obs, hidden_grade):
        self.facts.append(dict(bathy=action["bathy"], VISC2=action["VISC2"],
                               obj=obs.get(OBJ), valid=obs.get("valid"),
                               u_max=obs.get("u_max"), u_rms=obs.get("u_rms"),
                               surf_max=obs.get("surf_max")))

    # ---- 由记忆导出的知识（这些正是"敏感性"）----
    def sensitivity(self, bathy):
        """d(obj)/d(log VISC2) 的稳健估计 —— 该地形对黏性的敏感度。"""
        f = [x for x in self.facts if x["bathy"] == bathy and x["valid"]
             and x["obj"] is not None]
        if len(f) < 3:
            return None
        x = np.log10(np.array([max(v["VISC2"], 1.0) for v in f]))
        y = np.array([v["obj"] for v in f])
        return float(np.polyfit(x, y, 1)[0])

    def baseline(self, bathy):
        """该地形在 VISC2≈0 处的目标值 —— 未干预参照。"""
        f = [x for x in self.facts if x["bathy"] == bathy and x["valid"]
             and x["VISC2"] < 1e-9 and x["obj"] is not None]
        return float(np.mean([v["obj"] for v in f])) if f else None

    def best(self, bathy):
        f = [x for x in self.facts if x["bathy"] == bathy and x["valid"]
             and x["obj"] is not None]
        return min(f, key=lambda v: v["obj"]) if f else None

    def digest(self):
        """写入日志的记忆快照 + 自然语言摘要。"""
        d = {}
        for b in BATHY:
            s, bl, bs = self.sensitivity(b), self.baseline(b), self.best(b)
            if s is None and bl is None:
                continue
            d[b] = dict(sensitivity_per_decade=s, baseline_at_zero=bl,
                        best=bs, n_obs=len([x for x in self.facts
                                            if x["bathy"] == b and x["valid"]]))
        # 跨地形对比 —— 这正是"平底对照"要回答的问题
        if "flat" in d and "r26steep" in d:
            bf, br = d["flat"]["baseline_at_zero"], d["r26steep"]["baseline_at_zero"]
            if bf and br:
                d["_contrast"] = {
                    "r26steep_over_flat_at_zero": round(br / max(bf, 1e-12), 1),
                    "note": ("平底 σ-PGE≡0：该比值即指标对 σ-PGE 的分辨力。"
                             "比值接近 1 说明指标没在测 σ-PGE。")}
        return d


# ============================ Planner ============================
class TwoPhasePlanner:
    """阶段一：跨地形随机播种（建敏感性）→ 阶段二：在有真值的地形上自适应细化。"""
    name = "twophase"

    def __init__(self, rng, n_seed=12):
        self.rng = rng
        self.n_seed = n_seed
        self.lo, self.hi = ACTION_SPACE["VISC2"]

    def seed_batch(self):
        """阶段一：可并行。每个地形都取 0（无干预）+ 若干随机点。"""
        acts = []
        for b in BATHY:
            acts.append({"bathy": b, "VISC2": 0.0, "ntimes": 8640})
        k = self.n_seed - len(acts)
        for i in range(max(k, 0)):
            b = list(BATHY)[i % len(BATHY)]
            v = float(round(10 ** self.rng.uniform(1.0, np.log10(self.hi)), 1))
            acts.append({"bathy": b, "VISC2": v, "ntimes": 8640})
        return acts

    def propose(self, mem, bathy="r26steep"):
        """阶段二：用记忆决定下一点（最大未探索间隙 + 边界外推）。"""
        f = [x for x in mem.facts if x["bathy"] == bathy and x["valid"]
             and x["obj"] is not None]
        xs = np.array(sorted(v["VISC2"] for v in f))
        ys = np.array([min(v["obj"] for v in f if v["VISC2"] == x) for x in xs])
        best = xs[int(np.argmin(ys))]
        if best >= xs.max() - 1e-9 and xs.max() < self.hi:
            nxt = min(best * 2 if best > 0 else 50.0, self.hi)
        else:
            srt = np.concatenate([[0.0], xs, [self.hi]])
            g = int(np.argmax(np.diff(srt)))
            nxt = 0.5 * (srt[g] + srt[g + 1])
        if np.any(np.isclose(xs, nxt, atol=1.0)):
            srt = np.concatenate([[0.0], xs, [self.hi]])
            g = int(np.argmax(np.diff(srt)))
            nxt = 0.5 * (srt[g] + srt[g + 1])
            if np.any(np.isclose(xs, nxt, atol=1.0)):
                return None
        return {"bathy": bathy, "VISC2": float(round(nxt, 1)), "ntimes": 8640}


# 现象按构造不存在的配置：在这些地形上把 σ-PGE 指标压低毫无意义
PHENOMENON_ABSENT = {"flat"}


def critic(step, mem):
    o, f = step["obs"], []
    if not o.get("valid"):
        return ["INVALID: 未完赛，强度指标不可比较"]
    c = mem.digest().get("_contrast")
    if c and c["r26steep_over_flat_at_zero"] < 3:
        f.append(f"⚠ 指标分辨力仅 {c['r26steep_over_flat_at_zero']}× —— "
                 f"该指标可能没在测 σ-PGE")
    if o.get("temp_max", 0) > 40 or o.get("temp_min", 99) < -5:
        f.append("WARN: 温度越界，疑似数值污染")
    return f


def critic_on_claim(best_action):
    """Agent **声称最优时**才触发的检查（探索期不限制）。

    起因（E32）：`random` 与 `grid` 两个 planner 都把「最优」报在 `flat` 地形上，
    读数 0.026，比 `r26steep` 上最好的 2.021 好 78 倍 —— 因为 **flat 上 σ 面就是
    等位面，σ-PGE 按构造恒等于零**。它们不是把问题解决了，是换了个没有这个病的病例。

    刻意**只在声称最优时**拦，不在探索时拦：跑 flat 本身是合法且应该做的
    （它是零-PGE 对照组，E28 的指标分辨力判据就靠它）。要禁止的是
    **拿对照组的读数当成绩**。
    """
    f = []
    b = best_action.get("bathy")
    if b in PHENOMENON_ABSENT:
        f.append(
            f"REJECT: 声称的最优落在 bathy='{b}' 上，而该配置的 σ-PGE "
            f"**按构造恒等于零** —— 这里的低读数不代表问题被解决，"
            f"代表问题不存在。该配置也没有独立真值，隐藏评估器无法计分。"
            f"请在 'r26steep' 上重新给出最优。")
    return f


def run(n_seed, n_adapt, seed=0):
    rng = np.random.default_rng(seed)
    pl = TwoPhasePlanner(rng, n_seed)
    env = SigmaPGEEnv(expose_truth=False, max_workers=16)
    mem, log = Memory(), []
    t0 = time.time()

    # ---------- 阶段一：并行播种 ----------
    acts = pl.seed_batch()
    for a in acts:
        a["seed"] = seed
    print(f"阶段一 · 并行播种 {len(acts)} 点（跨 {len(BATHY)} 地形）")
    results = env.step_batch(acts)
    for i, (a, (obs, info)) in enumerate(zip(acts, results)):
        g = grade(info["run_id"])
        mem.observe(a, obs, g)
        log.append(dict(phase="seed", i=i, action=a, obs=obs,
                        run_id=info["run_id"], hidden_grade=g,
                        wall_s=round(info["wall_s"], 1)))
        print(f"  [{i:2d}] {a['bathy']:9s} VISC2={a['VISC2']:>7.1f}"
              f" | {OBJ}={obs.get(OBJ) if obs.get(OBJ) is None else round(obs[OBJ],3)}"
              f" | 隐藏={g.get('score') if g.get('score') is None else round(g['score'],3)}",
              flush=True)

    d = mem.digest()
    print("\n  记忆快照:")
    for b in BATHY:
        if b in d:
            print(f"    {b:9s} 基线={d[b]['baseline_at_zero']}"
                  f"  敏感度/decade={d[b]['sensitivity_per_decade']}")
    if "_contrast" in d:
        print(f"    ⭐ 分辨力 r26steep/flat = {d['_contrast']['r26steep_over_flat_at_zero']}×")

    # ---------- 阶段二：串行自适应 ----------
    print(f"\n阶段二 · 自适应细化 {n_adapt} 步（用记忆）")
    for j in range(n_adapt):
        a = pl.propose(mem)
        if a is None:
            print("  动作空间已充分覆盖，提前停止"); break
        a["seed"] = seed
        obs, info = env.step(a)
        g = grade(info["run_id"])
        mem.observe(a, obs, g)
        st = dict(phase="adapt", i=j, action=a, obs=obs,
                  run_id=info["run_id"], hidden_grade=g,
                  wall_s=round(info["wall_s"], 1))
        st["critic"] = critic(st, mem)
        st["memory"] = mem.digest()
        log.append(st)
        print(f"  [{j:2d}] VISC2={a['VISC2']:>7.1f}"
              f" | 可见={obs.get(OBJ) if obs.get(OBJ) is None else round(obs[OBJ],3)}"
              f" | 隐藏={g.get('score') if g.get('score') is None else round(g['score'],3)}"
              f" | {st['wall_s']:>5.1f}s", flush=True)

    out = f"{ENV}/ledger/agent_v2_s{seed}.json"
    json.dump(dict(n_seed=n_seed, n_adapt=n_adapt, seed=seed,
                   wall_total_s=round(time.time() - t0, 1),
                   budget=env.budget(), final_memory=mem.digest(), log=log),
              open(out, "w"), ensure_ascii=False, indent=1)
    print(f"\n探索日志: {out}")
    return log, mem


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed-runs", type=int, default=12)
    p.add_argument("--adapt", type=int, default=10)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    log, mem = run(a.seed_runs, a.adapt, a.seed)
    ok = [s for s in log if s["obs"].get("valid") and s["obs"].get(OBJ) is not None
          and s["action"]["bathy"] == "r26steep"]
    if ok:
        vis = min(ok, key=lambda s: s["obs"][OBJ])
        hid = [s for s in ok if s["hidden_grade"].get("score") is not None]
        print(f"\n按可见代理选出: VISC2={vis['action']['VISC2']:g} ({OBJ}={vis['obs'][OBJ]:.3f})")
        if hid:
            h = min(hid, key=lambda s: s["hidden_grade"]["score"])
            print(f"隐藏真值实际最优: VISC2={h['action']['VISC2']:g} "
                  f"(误差={h['hidden_grade']['score']:.3f})")
