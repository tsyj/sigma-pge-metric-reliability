# -*- coding: utf-8 -*-
"""sigma_audit — σ 伪流环境的指标送检台（oss_audit_kit #27）。

用法（评委视角）：
    python -m sigma_audit submit "u|d800|rms / temp|d800|rms"
    python -m sigma_audit submit my_metric.py
    python -m sigma_audit selftest        # 三条验收测试
    python -m sigma_audit counts          # 全空间计数复现（444→0→0 与 204/88/140/80）

诚实边界（措辞冻结，见 README）：
- 线束只覆盖能用 124 个基元读数（或其比值）表达、或能由随包台账逐 run 查表求值的候选；
- 全部读数来自既有台账与已落盘 run 输出（env_replay 精确查表），零新算例、零 ROMS 机时；
- 判定语义限定在本环境族内（σ 伪流海山 + 平底孪生 + 三风向），不是通用审计框架；
- 外部读数（用户自带配对算例）只留 MetricPlugin 接口，本套件不做实证。
"""
import os

# 离线入口在导入 numpy 前统一限制线程。
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "8"

__version__ = "0.1.2"

PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(PACKAGE_ROOT, "data")
REFERENCE_ROOT = os.path.join(DATA_ROOT, "reference")
REPO_ROOT = os.environ.get("SIGMA_REPO_ROOT", os.path.dirname(PACKAGE_ROOT))
ENV_ROOT = os.environ.get("SIGMA_ENV_ROOT", REPO_ROOT)
KIT_ROOT = os.environ.get("SIGMA_KIT_ROOT",
                          os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.environ.get("SIGMA_CACHE_DIR", os.path.join(DATA_ROOT, "cache"))

ENVS = {
    "zonal":  dict(ledger="ledger/env2_runs.jsonl",        runs="runs",        reg_from="regraded"),
    "merid":  dict(ledger="ledger/env2_merid_runs.jsonl",  runs="runs_merid",  reg_from="hidden"),
    "diag45": dict(ledger="ledger/env2_diag45_runs.jsonl", runs="runs_diag45", reg_from="hidden"),
}

# 认证两关门（与 e65/e67b 逐字同口径）
GATE_A = 0.7
GATE_B = 0.9
SPUR_KEY = "u|all|rms"
EPS = 1e-12
