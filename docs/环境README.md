# σ 坐标伪流探索环境

> GOAI 赛道三 · 开放探索赛题
> 一个**从源码可重建**的探索环境：Agent 在其中改变海洋模式的数值控制参数，
> 观察反馈，而隐藏评估器用独立模式的真值给分。

---

## 这个环境在问什么

地形跟随（σ）坐标的海洋模式在陡地形上会凭空造出伪流 —— 海洋本该静止时也在流动。
三十年、二十多篇文献之后，**"该怎么控制它、又不把真实运动一起抹掉"仍无公认答案**。

更麻烦的是：**这个领域连"怎么判断一个控制方案是好是坏"都没有共识**。
本环境把这件事本身变成可探索对象 —— 不是拿一个指标去优化配置，
而是**拿配置空间去检验指标**。

---

## 快速开始

```bash
# 1a. 构建求解器（约 5 分钟，16 核）—— 环境实际使用 v4
cd build && bash build_v4.sh          # +UV_VIS4 +TS_DIF4，四个旋钮全部有效
#    → bin/coawstM_goai_v4
#    → sha256: b50851d95ab35bc60a7545185eb5ec24f2aa9c3c0e36e70620b3e1b711436822
#
#    v1（仅 UV_VIS2）保留作对照：bash build.sh
#    → sha256: 479eca46aaa8b6216c7aa94f8dc7055015d45f8ed78ae5fff628a99fe295401a
#    v4 在 VISC4=0、TNU4=0 时与 v1 **逐位一致**（u/v/temp/zeta/w 全场差 0），
#    因此 v1 时期的历史 run 与 v4 新 run 可直接混用。

# 1b. 构建真值求解器（MITgcm，约 3 分钟）
bash build_mitgcm/build.sh
#    → sha256: 661436c35637d975f2842bf3e8841e33016e777fa027b0e8e93cba9cca88c133
#    结果与官方发表 run 逐位一致（U/V/T 全场全时间步差 0）

# 1c. 动作空间体检（强烈建议每次改编译选项后跑）
python scripts/validate_actions.py
#    每个旋钮拧到「大到不可能没影响」的探测值；若读数一个都没动 → 报「✗ 无感」。
#    这能抓住「CPP 选项没编进去 → 旋钮静默无效」这类不报错的缺陷。

# 1d. 端到端回归（改完 env2.py 必跑，约 25 s）
python scripts/smoke_test.py
#    覆盖四条踩过坑的路径：默认 / 科学计数法参数 / 多值参数 / 无真值配置

# 2. 单次交互
python - <<'PY'
import sys; sys.path.insert(0, "scripts")
from env2 import SigmaPGEEnv, grade
env = SigmaPGEEnv()                       # Agent 侧：看不到真值
obs, info = env.step({"bathy": "r26steep", "VISC2": 50.0,
                      "ntimes": 8640, "seed": 0})
print(obs)                                # 可见观测
print(grade(info["run_id"]))              # 隐藏评估器给分
PY

# 3. 跑一次完整探索（8 步，约 17 分钟）
python scripts/agent_run.py bisect --steps 8 --seed 0     # 自适应二分
python scripts/agent_run.py bo     --steps 8 --seed 0     # 贝叶斯优化（强 baseline）
python scripts/agent_run.py random --steps 8 --seed 0     # 随机（平凡参照）
python scripts/agent_run.py grid   --steps 8 --seed 0     # 网格（人最常做的）
```

---

## 环境接口

### 固定规则（不可探索）

| 项 | 值 |
|---|---|
| 求解器 | ROMS 3.9，PRSGRD31（标准密度雅可比，Song 1998）|
| 网格 | 48×48×13，dx = 2 km |
| 强迫 | 纬向风应力 τ = 0.1 N/m²，前 ~12 h tanh 爬升 |
| 时长 | 3 天（NTIMES = 25920 × DT = 10 s）|
| 层结 | 同一 T(z) 剖面，T ∈ [4.0, 25.9] °C，初始 u ≡ 0 |
| 并行 | NtileI = NtileJ = 1（单核，保证可复现）|

### 动作空间

| 旋钮 | 范围 | 说明 |
|---|---|---|
| `bathy` | `flat` / `mit` / `r26steep` | 平底（σ-PGE ≡ 0，**对照组**）/ 峰 107.7 m / 峰 80 m（**有真值**）|
| `VISC2` | 0 – 2000 m²/s | 谐波横向黏性 |
| `VISC4` | 0 – 1e10 | 双谐波黏性 |
| `AKV_BAK` | 1e-6 – 1.0 m²/s | 背景垂向黏性 |
| `TNU2` | 0 – 1000 m²/s | 示踪物扩散 |
| `ntimes` | 1440 – 25920 | 运行长度（**预算旋钮**）|
| `seed` | int | 写入 ledger 供复现（ROMS 本身确定性）|

### 观察（Agent 可见）

`u_max` · `u_rms` · `deep_rms_{200,400,800,1500}` · `surf_max` ·
`temp_min` · `temp_max` · `valid` · `crashed` · `completion_ratio`

### 隐藏（评估器专用，不进 Agent 工作区）

`temp_over_max` · `temp_over_mean` · `err_rms_vs_truth` · `err_max_vs_truth` ·
`truth_max` · `truth_rms` · ⭐ `skill_vs_zero` · `truth_day` / `truth_akv`（配对凭证）

> **真值仅 `r26steep` 一个配置有**（MITgcm z 坐标独立解）。
> 这是**刻意的** —— 真实科研中真值通常缺席，环境如实反映这一点。

### 反馈与记录

每次 `step()` 写一行 JSON 到 `ledger/env2_runs.jsonl`：
动作 + 可见观测 + 隐藏量 + 墙钟时间 + seed。
Agent 的决策轨迹另写 `ledger/agent_<planner>_s<seed>.json`。

---

## 两条不可妥协的设计

**1. 隐藏评估器**（借 EurekAgent, arXiv:2606.13662 的 permissions engineering）
真值与打分代码放在 Agent 工作区之外。Agent 只能提交 `run_id` 换分数，改不了评分器。

**2. Analyst 层确定性**（借 Agentic PDE, arXiv:2604.09584 的四角色分工）
**LLM 绝不碰数值。** 它只能"请求某个诊断量"，计算由固定代码完成 ——
把幻觉挡在科学结论之外。

---

## 参照系（八层）

| 层 | 内容 | 状态 |
|---|---|---|
| **0** | ⭐ **恒输出零的模型** —— 技巧评分定义为 0 | ✅ **目前没有任何配置超过它** |
| 1 | 无干预：σ baseline | ✅ VISC2=50 默认 |
| 2 | 平凡解：单调加黏性 | ✅ `grid` planner |
| 3 | 随机采样 | ✅ `random` planner |
| 4 | 已知失败解（必崩，回归门）| ✅ `VISC2=1e5`、`VISC4≥1e11`、`TNU2≥100` |
| 5 | 领域经验法则（典型横向黏性 1–100 m²/s）| ✅ |
| 6 | **强 baseline：高斯过程 + EI 贝叶斯优化** | ✅ `bo` planner |
| 7 | **人类专家轨迹**（数月手工搜索 + 红队记录）| 待接 |

第 0 层是 2026-08-14 才补的 —— 因为发现基于真值的分数自己的退化最优
就是「什么都不产生」（见文末）。**没有它，评估器本身就是可刷的。**

第 6 层用 sklearn 的 GP 自实现 EI，**零新增依赖** —— 复现门槛更低。

---

## 依赖

| 组件 | 版本（本机已验证）|
|---|---|
| gfortran | 11.4.0 (Ubuntu 11.4.0-1ubuntu1~22.04.3) |
| mpif90 | **必须用 `/usr/bin/mpif90`** |
| netCDF | 4.8.1（`/usr/bin/nc-config`）|
| Python | 3.9；numpy 2.0.2、netCDF4、matplotlib、scikit-learn 1.6.1、scipy 1.13.1 |

**无 GPU 需求。** 单 run 约 130 s（单核）。

---

## ⚠️ 构建三条铁律（踩过坑）

1. **`PATH` 必须把 `/usr/bin` 放最前** —— conda 里的 `mpif90`/`mpicc` 会导致链接失败
2. **`LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu`** —— 否则 ABI 不匹配会在运行期 SIGSEGV
3. **CPP header 里不能写注释** —— ROMS 的 makefile 会把 header 经 `cpp -P` 展开写进
   `$HOME/make_macros.mk`，注释会原样漏进去破坏 make 语法。
   `build/goai_seamount.h` 因此是纯指令。文档写在本 README 里。

另：`$HOME/make_macros.mk` 若有残留会毒化后续构建，失败后先删它。

---

## 并发上限（实测）

| 并发 | 吞吐 (runs/min) | 并行效率 |
|---:|---:|---:|
| 1 | 2.80 | 100% |
| **16** | **34.09** | 76% ← **峰值** |
| 32 | 32.44 | 36% |
| 128 | 24.73 | 6% |

**瓶颈是内存带宽/磁盘 I/O，不是 CPU。** 128 并发用 8 倍核，吞吐反低 27%。
→ 加机器无用；`max_workers=16` 是默认值。

---

## 目录

```
build/     从源码构建求解器（src/ = ROMS 3.9 + 风应力补丁；goai_seamount.h；build.sh）
bin/       构建产物
cases/     网格与初始场
scripts/   env2.py（环境）· agent_run.py / agent_v2.py（Agent 循环）
           mitgcm.py（真值读取）· sigma2z.py（σ→z 插值，逐场比较的前提）
           validate_actions.py（动作空间体检）· smoke_test.py（端到端回归）
           knob_sweep.py / knob_analysis.py（四旋钮）· regrade_all.py（重打分）
           absurd_visc.py · headline_table.py · truth_sweep.sh · fig_*.py
runs/      每次 step 的隔离运行目录（输入只读引用，输出全相对路径）
truth/     MITgcm 真值（hires_* 为每小时输出的主线真值）
ledger/    运行日志、探索日志、图
           legacy_dnn_binary/ = 换 clean binary 之前的结果，仅供对照
           dj_gradps_binary/  = DJ_GRADPS 压力梯度产出的结果，**非主线求解器**
video/     官方宣讲/直播的转写与关键帧
```

---

## ⚠️ 关于 legacy 结果

`ledger/legacy_dnn_binary/` 下的数值是用一个**从原研究树拷来的 binary** 跑的。
后来发现它把研究代码编了进去（`prsgrd_dnn.h` 替换了标准压力梯度、`gt_coordinate`、`gt_eq3`），
即使运行期开关关闭，代码路径已不同 —— 与干净构建的结果差约 60%。

**正式结果一律以 `coawstM_goai_v4`（可从源码重建，sha256 `b50851d9…`）为准。**

另有一批结果出自 `bin/coawstM_goai`，那个二进制用的是 **DJ_GRADPS** 压力梯度
（主线是 **PRSGRD31**）。σ-PGE 本身就是压力梯度的问题，**换了格式就是换了被研究的对象**，
已隔离到 `ledger/dj_gradps_binary/`。

**现在每条 ledger 记录都带 `bin_sha256`** —— 产物过期可被机器检出，不靠人记得。

这件事本身说明了为什么"binary 可重建"是硬要求：
**不可重建的二进制里可能藏着你不知道的东西。**

---

## 真值通道

| 目录 | viscAz | 输出间隔 | 帧数 | 用途 |
|---|---|---|---|---|
| `truth/hires_1pEm5` | 1×10⁻⁵ | **1 h** | 73 | ⭐ 主线（与 ROMS `AKV_BAK` 默认值匹配）|
| `truth/hires_1pEm3` | 1×10⁻³ | 1 h | 73 | 对照（官方发表 run 用的值）|
| `truth/sw_viscAz_*` | 1e-4 … 1.0 | 0.5 天 | 7 | `AKV_BAK` 扫描配对 |
| `truth/sw_{viscAh,viscA4,diffKhT}_*` | — | 0.5 天 | 7 | 其余三个旋钮的配对 |

**加密版与原版在共同时刻逐位一致**（加密输出不改变解）。
加密的原因：原来只有 0.5 天整数倍有真值，`ntimes=1440`（0.167 天）取不到 —— 短 run 无法评分。

### 三条必须知道的配对规则

1. **垂向黏性要匹配**：ROMS 无垂向混合闭合方案，有效垂向黏性 = `AKV_BAK`（默认 1e-5）；
   官方 MITgcm run 用的是 `viscAz = 1e-3`，**差 100 倍**。用 `TRUTH_BY_AKV` 按动作取。
2. **时刻要匹配**：ROMS `DT=10 s`，MITgcm `deltaT=30 s`。
   `ntimes=8640` 是 ROMS 的**第 1 天**，不是 MITgcm 的 iter 8640（第 3 天）。
3. **垂向层序相反**：ROMS `k=0` 是**底**层，MITgcm `k=0` 是**面**层。
   而且 σ 层随地形起伏、各列层深不同 —— 必须逐列插值（`scripts/sigma2z.py`），
   不能直接相减，也不能只翻转。

三条都踩过（实验日志 E29 撤回 #6/#7、E35 撤回 #8）。`_diagnose` 现在把
`truth_day` / `truth_akv` 写进 hidden 记录，使每条结果自带配对凭证。

---

## ⚠️ 隐藏评估器用技巧评分，不用裸误差

$$SS = 1 - \left(\frac{\text{err\_rms}}{\text{truth\_rms}}\right)^2$$

- `SS = 1` 完美 · **`SS = 0` 与「什么都不输出」持平** · `SS < 0` 比什么都不做还差

**为什么不用裸的 `err_rms`**：它的下限是 `rms(0 − 真值) = rms(真值)`，
也就是**一个恒输出零的模型**。默认配置的 `err_rms` 比这个下限差 **+4.9**，
而把黏性拧到物理荒谬的 30000 能逼到 +0.34 —— **裸误差奖励「用消灭一切来降低误差」**。

接上真值挡住了「代理指标失效」，但没挡住这一条。**真值不是终点，基于真值的分数也需要参照系。**

当前实测：**44 个配置技巧评分无一为正**（最好 −0.184）。见实验日志 E34/E35。
