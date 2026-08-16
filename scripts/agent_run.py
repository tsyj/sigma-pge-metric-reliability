#!/usr/bin/env python
"""Agent 探索循环 —— 补上 B 队指出的致命缺口。

架构借 Agentic PDE (arXiv 2604.09584) 的四角色，关键改动：
  · Planner  : LLM（或本文件的规则 planner）—— 决定下一步试什么
  · Analyst  : **确定性代码**（env2.step）—— LLM 绝不碰数值
  · Critic   : 规则 + LLM —— 检查合法性、覆盖率、是否掉进已知陷阱
  · Writer   : 结构化探索日志

本文件先实现 **规则 Planner**（不依赖任何 LLM / API），作用：
  1. 立刻可跑、可复现、零成本 —— 满足复赛"最小可运行探索环境"
  2. 作为 **LLM Planner 的参照系**（七层参照系的第 2/3 层）

LLM Planner 走 `planner="llm"`，由 `llm_planner.py` 提供（待接）。
"""
import os, sys, json, time, argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import SigmaPGEEnv, grade, ACTION_SPACE, BATHY

ENV = "/data/xinyuan/GOAI_ai4s_env"


# ============ Planner 们（第 2/3 层参照系）============
class RandomPlanner:
    """平凡参照系：均匀随机采样动作空间。"""
    name = "random"

    def __init__(self, rng): self.rng = rng

    def propose(self, history, k=1):
        out = []
        for _ in range(k):
            out.append({"bathy": self.rng.choice(list(BATHY)),
                        "VISC2": float(round(self.rng.uniform(0, 1000), 1)),
                        "ntimes": 8640})
        return out


class GridPlanner:
    """平凡参照系：等距网格扫描（人最常做的事）。"""
    name = "grid"

    def __init__(self, rng):
        self.queue = [{"bathy": b, "VISC2": v, "ntimes": 8640}
                      for b in BATHY for v in (0.0, 100.0, 300.0, 1000.0)]
        self.i = 0

    def propose(self, history, k=1):
        out = self.queue[self.i:self.i + k]
        self.i += len(out)
        return out


class BisectPlanner:
    """规则 Planner：在 VISC2 轴上按观测反馈做自适应二分/外推。

    目标：最小化 Agent **可见**的 deep_rms_800（代理指标）。
    —— 刻意用代理而非真值，看它会被带到哪里。
    """
    name = "bisect"

    def __init__(self, rng):
        self.bathy = "r26steep"
        self.probe = [0.0, 300.0, 1000.0]
        self.done_probe = False

    def propose(self, history, k=1):
        hist = [h for h in history if h["obs"].get("valid")
                and h["action"].get("bathy") == self.bathy]
        if len(hist) < len(self.probe):
            v = self.probe[len(hist)]
            return [{"bathy": self.bathy, "VISC2": v, "ntimes": 8640}]
        xs = np.array([h["action"]["VISC2"] for h in hist])
        ys = np.array([h["obs"]["deep_rms_800"] for h in hist])
        VMAX = ACTION_SPACE["VISC2"][1]
        best = xs[int(np.argmin(ys))]
        if best >= xs.max() - 1e-9:                 # 最优在边界 → 几何外推
            nxt = (best * 2 if best > 0 else 50.0)
        else:                                       # 在内部 → 邻域细分
            lo = xs[xs < best].max() if (xs < best).any() else 0.0
            hi = xs[xs > best].min() if (xs > best).any() else best * 2
            nxt = 0.5 * (lo + hi)
        # 去重：若已评估过，改在最大未探索间隙中点采样；仍冲突则放弃本步
        tries = 0
        while np.any(np.isclose(xs, nxt, atol=1.0)) or nxt > VMAX:
            tries += 1
            if tries > 8:
                return []                            # 预算不浪费在重复点上
            srt = np.sort(np.concatenate([[0.0], xs, [VMAX]]))
            gaps = np.diff(srt)
            g = int(np.argmax(gaps))
            nxt = 0.5 * (srt[g] + srt[g + 1])
        return [{"bathy": self.bathy, "VISC2": float(round(nxt, 1)),
                 "ntimes": 8640}]



class BOPlanner:
    """⭐ 非平凡 baseline：高斯过程 + Expected Improvement。

    官方排雷清单点名「没有最低参照或强 baseline → 评委会问 Agent 是否只撞中运气」。
    对标案例 Battery-Sim-Agent 用的是 Ax BO；此处用 sklearn GP 自实现 EI，
    零新增依赖（复现门槛更低）。
    """
    name = "bo"

    def __init__(self, rng):
        self.rng = rng
        self.bathy = "r26steep"
        self.init = [0.0, 500.0, 1500.0]      # 初始设计
        self.lo, self.hi = ACTION_SPACE["VISC2"]

    def propose(self, history, k=1):
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern, ConstantKernel, WhiteKernel
        from scipy.stats import norm
        hist = [h for h in history if h["obs"].get("valid")
                and h["action"].get("bathy") == self.bathy
                and h["obs"].get("deep_rms_800") is not None]
        if len(hist) < len(self.init):
            return [{"bathy": self.bathy, "VISC2": self.init[len(hist)],
                     "ntimes": 8640}]
        X = np.array([[h["action"]["VISC2"]] for h in hist])
        y = np.array([h["obs"]["deep_rms_800"] for h in hist])
        Xs = (X - self.lo) / (self.hi - self.lo)
        mu_y, sd_y = y.mean(), max(y.std(), 1e-9)
        ys = (y - mu_y) / sd_y
        kern = (ConstantKernel(1.0, (1e-3, 1e3))
                * Matern(length_scale=0.3, length_scale_bounds=(1e-2, 1e1), nu=2.5)
                + WhiteKernel(1e-6, (1e-9, 1e-1)))
        gp = GaussianProcessRegressor(kernel=kern, normalize_y=False,
                                      n_restarts_optimizer=4,
                                      random_state=0).fit(Xs, ys)
        cand = np.linspace(0, 1, 601).reshape(-1, 1)
        mu, sd = gp.predict(cand, return_std=True)
        best = ys.min()
        with np.errstate(divide="ignore", invalid="ignore"):
            imp = best - mu
            z = np.where(sd > 1e-12, imp / sd, 0.0)
            ei = np.where(sd > 1e-12, imp * norm.cdf(z) + sd * norm.pdf(z), 0.0)
        # 排除已评估点邻域，避免重复消耗预算
        for xv in Xs.ravel():
            ei[np.abs(cand.ravel() - xv) < 0.01] = -1.0
        nxt = float(cand[int(np.argmax(ei)), 0]) * (self.hi - self.lo) + self.lo
        return [{"bathy": self.bathy, "VISC2": float(round(nxt, 1)),
                 "ntimes": 8640}]


PLANNERS = {p.name: p for p in (RandomPlanner, GridPlanner,
                                BisectPlanner, BOPlanner)}


# ============ Critic：规则部分（不依赖 LLM）============
def critic(step):
    """返回 (flags, 说明)。刻意包含已知陷阱的检测。"""
    o, f = step["obs"], []
    if not o.get("valid"):
        f.append("INVALID: 未完赛，任何强度指标不可比较")
        return f
    if o.get("u_max") is not None and o.get("deep_rms_800") is not None:
        # 陷阱检测：只看全域指标会把「真流被damp」当成「伪流被消」
        f.append(f"NOTE: u_max={o['u_max']:.1f} 含真实风驱流分量；"
                 f"deep_rms_800={o['deep_rms_800']:.2f} 才隔离 σ-PGE")
    if o.get("temp_max", 0) > 40 or o.get("temp_min", 99) < -5:
        f.append("WARN: 温度越界，疑似数值污染")
    return f


def run(planner_name, n_steps, seed=0, out=None):
    rng = np.random.default_rng(seed)
    planner = PLANNERS[planner_name](rng)
    env = SigmaPGEEnv(expose_truth=False)          # Agent 侧看不到真值
    history, log = [], []
    t0 = time.time()
    for i in range(n_steps):
        props = planner.propose(history, k=1)
        if not props:
            break
        a = props[0]; a["seed"] = seed
        obs, info = env.step(a)
        step = {"i": i, "action": a, "obs": obs, "run_id": info["run_id"],
                "wall_s": round(info["wall_s"], 1)}
        step["critic"] = critic(step)
        history.append(step)
        # 隐藏评估器：Agent 看不到，只写进日志供离线检查
        step["hidden_grade"] = grade(info["run_id"])
        log.append(step)
        vis = obs.get("deep_rms_800")
        hid = step["hidden_grade"].get("score")
        print(f"[{i:2d}] {planner_name:7s} bathy={a['bathy']:9s} VISC2={a['VISC2']:>7.1f}"
              f" | 可见 deep_rms={vis if vis is None else round(vis,3)}"
              f" | 隐藏 误差={hid if hid is None else round(hid,3)}"
              f" | {step['wall_s']:>5.1f}s", flush=True)

    res = {"planner": planner_name, "seed": seed, "n_steps": len(log),
           "wall_total_s": round(time.time() - t0, 1),
           "budget": env.budget(), "log": log}
    out = out or f"{ENV}/ledger/agent_{planner_name}_s{seed}.json"
    json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"\n探索日志: {out}")
    return res


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("planner", choices=list(PLANNERS))
    p.add_argument("--steps", type=int, default=6)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    r = run(a.planner, a.steps, a.seed)
    ok = [s for s in r["log"] if s["obs"].get("valid")]
    if ok:
        vis = [(s["obs"]["deep_rms_800"], s["action"]["VISC2"], s["action"])
               for s in ok if s["obs"].get("deep_rms_800") is not None]
        hid = [(s["hidden_grade"]["score"], s["action"]["VISC2"]) for s in ok
               if s["hidden_grade"].get("score") is not None]
        if vis:
            b = min(vis)
            print(f"按可见代理选出的最优: bathy={b[2].get('bathy')} "
                  f"VISC2={b[1]:g} (deep_rms={b[0]:.3f})")
            # E32：random / grid 都把「最优」报在 flat 上（σ-PGE 按构造为零）
            from agent_v2 import critic_on_claim
            for msg in critic_on_claim(b[2]):
                print(f"  Critic → {msg}")
        if hid:
            b = min(hid); print(f"隐藏真值实际最优:     VISC2={b[1]:g} (误差={b[0]:.3f})")
