# 谁来给尺子打分：σ 坐标伪流环境中的代理指标可靠性探索

GOAI 世界人工智能开源大赛 · 赛道三 AI for Research · 开放探索赛题参赛作品（初赛）。

**一句话**：在一个真值可独立测量的 σ 坐标伪流算例上，检验"判断控制方案好坏"的代理指标本身是否可信——并实测了智能体如何刷分、以及一个抗刷分指标如何让刷分消失。

- 四页文档：`docs/初赛文档_终稿.pdf`
- 环境细节：`docs/环境README.md`

## 核心结果

| 发现 | 数字 |
|---|---|
| σ 坐标凭空造出的伪流 vs 独立真值（MITgcm z 坐标） | 系统性大 10–16 倍，惯性节点处 99 倍 |
| 只改一句目标表述，LLM 智能体的刷分率 | 90% → 18%（12 轮实测） |
| 三条刷分路径（换地形 / 荒谬黏性 / 缩短积分） | 224× / 62× / 28×（同参数配对中位） |
| 从 15,376 个候选穷举出的抗刷分指标 uv_ratio | 排序能力 96→92，抗刷分 0→100 |
| 放回环境重跑（只换目标指标） | 平底占比 89.8%→7.5%，"最优在平底" 5/5→0/4 |

## 快速复现

```bash
# 1. 重建求解器（约 5 min / 16 核；MITgcm 真值侧约 3 min，与官方发表 run 逐位一致）
bash build/build_v4.sh
bash build_mitgcm/build.sh

# 2. 端到端回归（约 25 s）
python scripts/smoke_test.py

# 3. 单次交互（约 125 s；智能体侧看不到真值）
python -c "
import sys; sys.path.insert(0,'scripts')
from env2 import SigmaPGEEnv, grade
env = SigmaPGEEnv()
obs, info = env.step({'bathy':'r26steep','VISC2':50.0,'ntimes':8640,'seed':0})
print(obs); print(grade(info['run_id']))"
```

随机种子与关键参数在代码中体现（`env2.py` 的 `ACTION_SPACE`）；每条台账记录绑定求解器二进制的 sha256。

## 目录

| 路径 | 内容 |
|---|---|
| `scripts/env2.py` | 环境本体，单一入口 `env.step(action)`；隐藏评估器 `grade()` |
| `scripts/llm_planner.py` | LLM 智能体（A/B/C/A2 四条件） |
| `scripts/metric_search.py` | 15,376 个候选指标穷举 |
| `scripts/agent_metric_v2.py` | 让智能体自己提议指标（E43，30 轮 0 通过的诚实负结果） |
| `scripts/fig_*.py` | 全部图，均可独立重跑 |
| `ledger/` | 全部实验台账（367 次运行、16+ 轮 LLM 轨迹、每轮完整 prompt/回复） |
| `figs/` | 终版图 |

## 外部依赖（来源与版本）

ROMS/COAWST（LGPL）、MITgcm（MIT 系开源协议）、numpy / netCDF4 / matplotlib / scikit-learn。
LLM 实验使用 DeepSeek API（deepseek-v4-pro / v4-flash），全部轨迹（含 prompt 原文）已存于 `ledger/`。

## 诚实声明

本项目的探索记录包含 10 次撤回与多个负结果（详见台账与文档 §4.2），包括"智能体抓到我们观测接口的 bug""让智能体自己提议指标 30 轮无一通过"。它们与正向发现同样是本作品的一部分。
