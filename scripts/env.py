#!/usr/bin/env python
"""伪流探索环境 —— env.step(config) → observation

设计依据
--------
EurekAgent (arXiv 2606.13662) 的 permissions engineering：
    隐藏评估器与真值必须放在 Agent 工作区之外，只通过打分服务暴露。
本环境据此把观测分成两层：
    · PROXY（Agent 可见）：全行业在用的指标，**含已知陷阱**
    · TRUE （隐藏评估器）：体积加权/守恒/完赛门控，Agent 看不到也改不了

完赛门控（首轮 rx0 扫描发现的必要性）
------------------------------------
崩溃的 run 因为伪流场没来得及发展，体积加权指标反而"最优"。
若不门控，任何优化器都会学会「通过崩溃刷分」。
故：validity 是硬门，非法 run 不进入任何比较。
"""
import os, sys, json, time, hashlib, subprocess
import concurrent.futures as cf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mkrun import make_run
from diagnostics import diagnose

ENV_ROOT = "/data/xinyuan/GOAI_ai4s_env"
BIN = f"{ENV_ROOT}/bin/coawstM_goai"
LEDGER = f"{ENV_ROOT}/ledger/runs.jsonl"

# ---- 动作空间（运行期旋钮；编译期旋钮由 binary 选择决定）----
ACTION_SPACE = {
    "grid": ["grid_rx0.2.nc", "grid_rx0.4.nc", "grid_rx0p50.nc", "grid_rx0p60.nc",
             "grid_rx0p70.nc", "grid_rx0p85.nc", "grid_raw.nc",
             "grid_raw_smooth_rx02.nc", "grid_raw_smooth_rx04.nc",
             "grid_cliff_rx0p80.nc", "grid_cliff_rx0p90.nc", "grid_cliff_rx0p95.nc",
             "grid_gauss_rx0p60.nc", "grid_gauss_rx0p80.nc", "grid_gauss_rx0p90.nc"],
    "VISC2":  (0.0, 1000.0),      # 谐波黏性 m^2/s
    "TNU2":   (0.0, 1000.0),      # 示踪物扩散
    "theta_s": (0.0, 10.0),       # 垂向拉伸
    "theta_b": (0.0, 4.0),
    "Tcline": (1.0, 500.0),
    "ntimes": (300, 8640),        # 运行长度（预算旋钮）
}

# Agent 可见的观测键（其余一律隐藏）
PROXY_KEYS = ["KE_final", "KE_max", "gK_logslope_per_step", "gK_tail_slope",
              "spurious_max_cms", "spurious_rms_cms", "temp_min", "temp_max"]


def _cfg_id(cfg):
    s = json.dumps(cfg, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()[:12]


class SpuriousCurrentEnv:
    """静止层结 + 陡地形下的伪流探索环境。

    真值：海洋本应静止，故任意 |u| > 0 皆为数值伪迹（无需外部真值）。
    """

    def __init__(self, expose_true=False, max_workers=16):
        # expose_true=True 仅供隐藏评估器/离线分析使用，Agent 侧必须 False
        self.expose_true = expose_true
        self.max_workers = max_workers      # 实测吞吐拐点 = 16
        self.n_calls = 0
        self.wall_total = 0.0
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)

    # ---------------- 单次交互 ----------------
    def step(self, config):
        """config: dict，键取自 ACTION_SPACE。返回 (observation, info)。"""
        cfg = dict(config)
        grid = cfg.pop("grid", "grid_rx0.2.nc")
        ntimes = int(cfg.pop("ntimes", 2880))
        rid = f"a_{_cfg_id({**config})}"
        rd = f"{ENV_ROOT}/runs/{rid}"

        overrides = {k: (f"{v}d0" if isinstance(v, float) else str(v))
                     for k, v in cfg.items()}
        make_run(rid, grid=grid, ntimes=ntimes, overrides=overrides)

        env = dict(os.environ, PATH="/usr/bin:" + os.environ.get("PATH", ""))
        t0 = time.time()
        with open(f"{rd}/run.log", "w") as lg:
            subprocess.run([BIN, "roms.in"], cwd=rd, stdout=lg,
                           stderr=subprocess.STDOUT, env=env)
        wall = time.time() - t0

        d = diagnose(f"{rd}/roms_his.nc", f"{rd}/run.log")
        self.n_calls += 1
        self.wall_total += wall

        # ---- 完赛门控（硬门）----
        completed = bool(d["meta"].get("completed"))
        crashed = bool(d["meta"].get("crashed"))
        valid = completed and not crashed
        last_step = d["meta"].get("last_step") or 0
        d["meta"].update(valid=valid, wall_s=round(wall, 1),
                         requested_ntimes=ntimes,
                         completion_ratio=round(last_step / max(ntimes, 1), 3))

        obs = {k: d["proxy"].get(k) for k in PROXY_KEYS}
        obs["valid"] = valid                       # Agent 必须看到合法性
        obs["crashed"] = crashed
        obs["completion_ratio"] = d["meta"]["completion_ratio"]
        if not valid:
            # 非法 run 的数值指标不可比较 —— 明确置空，杜绝"崩溃刷分"
            for k in ("KE_final", "KE_max", "spurious_max_cms",
                      "spurious_rms_cms", "gK_logslope_per_step", "gK_tail_slope"):
                obs[k] = None
            obs["note"] = ("run 未完赛（崩溃或提前终止）；伪流场未充分发展，"
                           "任何强度指标都不可与完赛 run 比较。")

        rec = {"run_id": rid, "config": config, "obs": obs,
               "true": d["true"], "meta": d["meta"]}
        with open(LEDGER, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        info = {"run_dir": rd, "wall_s": wall}
        if self.expose_true:
            info["true"] = d["true"]
        return obs, info

    # ---------------- 批量（用满 16 并发）----------------
    def step_batch(self, configs):
        with cf.ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            return list(ex.map(self.step, configs))

    # ---------------- 预算 ----------------
    def budget(self):
        return {"n_runs": self.n_calls,
                "wall_total_s": round(self.wall_total, 1),
                "wall_per_run_s": round(self.wall_total / max(self.n_calls, 1), 1)}


# ---------------- 隐藏评估器（Agent 不可访问）----------------
def grade(run_id):
    """打分服务：读 ledger 里的 TRUE 层，返回官方分数。
    Agent 只能提交 run_id 换分数，看不到也改不了本函数的输入。"""
    for line in open(LEDGER):
        r = json.loads(line)
        if r["run_id"] == run_id:
            if not r["meta"].get("valid"):
                return {"score": None, "valid": False,
                        "reason": "未完赛，不计分"}
            t = r["true"]
            return {"score": t.get("spurious_rms_volwt_cms"),
                    "valid": True,
                    "vol_frac_gt_1cms": t.get("vol_frac_speed_gt_0.01"),
                    "energy_drift": t.get("total_energy_drift_rel")}
    return {"score": None, "valid": False, "reason": "run_id 不存在"}


if __name__ == "__main__":
    e = SpuriousCurrentEnv()
    obs, info = e.step({"grid": "grid_rx0p60.nc", "ntimes": 600, "VISC2": 5.0})
    print(json.dumps(obs, indent=2, ensure_ascii=False))
    print("预算:", e.budget())
    print("官方分:", json.dumps(grade(f"a_{_cfg_id({'grid':'grid_rx0p60.nc','ntimes':600,'VISC2':5.0})}"),
                              ensure_ascii=False))
