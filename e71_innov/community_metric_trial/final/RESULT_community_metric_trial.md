# RESULT — community_metric_trial 验证阶段（步骤 3：修正→封存→跑批→判分）

> 【2026-09-17 复算更正】 本文件已按战报§5.1–5.3和既有复算收紧口径；所有原判分JSON与封存件保留。文末列逐项改动清单，历史数不得脱离更正引用。

日期：2026-09-17。目录：`/data/xinyuan/GOAI_ai4s_env/e71_innov/community_metric_trial/final/`。
冻结判分数字保留于 `verdict.json`；当前解释及敏感性以本文件更正节与 recompute 为准，本文件逐数字挂 JSON 指针；复述与 PPT 引用一律走指针。

## 1. 评审意见落实（封存前，合规）

| 意见 | 处置 |
|---|---|
| [重要] P4 键集偏差死路径 | `validate_envs.py`：P4 改为 §1.14 名称映射（用 ARRAYS_zonal.npz 的 keys/NUM/DEN 把纬向 S_A 精确映射到交集索引，映射前自检 Σ=204）＋整段 try/except，异常只记 `p4_unavailable`，其余判分输入照常落盘；PREREG §1.14 同步改写 |
| [一般] S_A_env 独立分子数无机械指针 | `VALIDATION_<env>.json` 新增 `n_distinct_numerators_S_A_env`；`verdict.json:distinct_numerator_duals` 回显（含 zonal 行）；PREREG §9.3 更新 |
| [一般] score_prereg 封存门弱 | `score_prereg.py` 增 `require_seal()`：与 validate_envs 同款逐文件哈希＋写位校验（封存前实测拒跑） |
| [一般] P10 Δlog==0 偏向通过 | schema 增 `frac_dlog_sigma2_pos`；PREREG §5 锁死：frac 严格不等式，Δlog==0 不计入任一侧（对 P9、P10 都不利）；score_prereg P10 直接用 frac_pos |
| [一般] P5(b) 结构零凑数嫌疑 | PREREG §4 P5(b) 明写：结构零由算子构造保证、仅作实现自检，计分赌注在 |A|<0.3；12 格与 ≥8 门不变 |
| [一般] ARRAYS_zonal.npz 不在物证链 | §0 封存命令追加 `SEAL_INPUTS.txt`（ARRAYS_zonal.npz＋VALIDATION_zonal.json 哈希登记）；validate_envs 封存门逐文件核对该登记 |
| [一般] #19条⑤ arXiv:2606.10642 复核漏列 | PREREG §8 登记；载体 `final/LIT_RECHECK_2606.10642.md` 已建：本地快照 v2(11 Jun 2026) 已核；**线上最新版+引用者检索未做**（本会话 WebSearch 配额 200/200 耗尽，如实记录，待办见该文件） |

修正后 zonal 重跑（封存前、探索域）：S_A=204、独立分子 41、bq 3 run 逐位一致，全部数组与修正前 npz **逐元素一致**（fields ALL identical）。

## 2. 封存（早于一切留出读数）

- `PREREG_community_metric_trial.sha256`，封存时间 **2026-09-17T14:41:34+08:00**，三件套 chmod 444：
  - PREREG_community_metric_trial.md `83e16b9fef516def41279b945f85c25fcc106013bbf32b9c331f31b3f43c0a29`
  - validate_envs.py `7beb586158e992853d0f4422e716589d28ddbb40c52d1a417b5e0d34aa687c3c`
  - score_prereg.py `2c498ec69c5bcd1eaee06b92a659df89acd7530860f2e4208985a456e7cef0f5`
- `SEAL_INPUTS.txt`：ARRAYS_zonal.npz `c70411eb…`、VALIDATION_zonal.json `2798aeb3…`（P4 物证链）。
- 留出读数（merid/diag45/bh93）首次读取时间 = 14:41:46（validate_merid.log），晚于封存。

## 3. 判分结果（verdict.json，机械输出）

**冻结历史计数 8 PASS/0 FAIL；当前材料写 6 条有风险预测全过，P3 按冻结口径 PASS 但解释撤回，P7 为结构性自检；P9/P10 已预注册未执行。** 【2026-09-17 复算更正】

| 条 | 结果 | 读数（JSON 指针 = verdict.json 内路径） |
|---|---|---|
| P1 美颜普适 | PASS | frac2 V1=0.4396, V2=0.4468 ∈ [0.319,0.519]（`/P1/values`） |
| P2 软肋重合 | PASS | OR_H V1=5.978, V2=5.802 ≥ 3（`/P2/values/haldane`；raw 5.981/5.804 同报） |
| P3 方向抵消检查（解读撤回） | 冻结 PASS；非独立轴证据 【2026-09-17 复算更正】 | ρ(D_sym) V1=0.0085, V2=0.0011，|ρ|≤0.2（`/P3/values/rho_D_sym`；D_u 0.0086/0.0009 连续性） |
| P4 跨向精选也挡不住 | PASS | n_set=**88**（=E67B 登记值，无偏差）、frac_hit=0.3182 ≥ 0.25（`/P4/values`；分子数 29/15 双口径） |
| P5 家族签名 | PASS | hits=**11/12** ≥ 8（`/P5/values/hits`）。唯一未命中：V2:hi_lo_ratio，B_oriented=0.143>0.1（改善 91.76% 达标）——如实报 |
| P6 σ 单调 | PASS | V1 [0.3467,0.4396,0.4679]、V2 [0.3659,0.4468,0.4798]（`/P6/values`） |
| P7 负对照（降级门） | PASS | u/v 56 基元×7 flat=392 格，median=**0.0**、max=**0.0**、超地板 0 格（`/P7/values`）——零场结构恒等，仅作附录自检 【2026-09-17 复算更正】 |
| P8 免疫者形态 | PASS | V1 n=91, shape_frac=0.8462；V2 n=90, shape_frac=0.8444 ≥ 0.8（`/P8/values`） |
| P9/P10 | 已预注册未执行 | `/P9`,`/P10`：METRICS20_ZONAL.json 未落地（#20 门 9/18 12:00） |

自检块（`/self_checks`，验证性断言不计数）：zonal S_A=204 ✓、独立分子 41 ✓、keys=124 ✓、merid P4 集合=88 ✓、bh93 flat=7、键集偏差 无（merid/diag45 均 124 键，P4 映射支路未触发——但已是冻结件内的活路径）。

双口径回显（`/distinct_numerator_duals`）：zonal 204→41 种分子；V1 S_A_env=407→59 种、σ2 中招 194→33 种、免疫 91→29 种；V2 S_A_env=454→65 种、中招 255→40 种、免疫 90→27 种。**引用任何"把数"必须同报分子数。**

## 4. 可上台 / 只进附录 / 不能用

**可上 PPT/Demo（2026-09-17 复算更正，必须带限定）**：
- 6 条有风险预测全过；P3 冻结 PASS 但解释撤回，P7 零场结构恒等；冻结 8/0 不包装为八次有风险命中。
- 美颜与黏性刷分软肋重合：OR_H 纬向 5.64（样本内）、经向5.98、45°5.80；倒数去重后5.75/6.08/5.90。与伪流幅度正相关（统一方向ρ≈0.38–0.43），却不能由它替代。
- P4：纬向204把（41种独立分子），经向存活88把（29种分子），其中28把（15种分子、31.8%）仍被σ2美颜刷动；平均秩稳健性未测。
- P7 与 P5(b) 首条件只进附录，标结构自检；P9/P10 已预注册未执行。

**只进附录**：S_A_env=407/454 与其分子数（非预测目标，观察值）；P8 构成表（w/w 主导）；阈值敏感性六组合表；D_u 连续性；threshold_sensitivity_sigma2。

**不能用**：P9/P10 任何读数（未执行）；#22（未跑）；62×（未按 fig_llm.py 复算不引用）；"budget_res 经受住攻击"话术（构造性免疫）；"证明 WeatherBench/被映射论文不可靠"。

## 5. 偏差与待办

- 【2026-09-17 复算更正】 **DEVIATIONS.md 已建**：P3 抵消设计缺陷、P7/P5(b) 降为验证性；冻结判分不重跑。
- 待办（9/19 封版前，非本步）：
  1. #20 `metrics20_zonal.py`（9/18 12:00 门；schema 已锁死含 frac_pos）→ P9/P10 判分补跑 → #22（16 基元清单已锁）。
  2. #21 映射表（8–10 篇逐篇引句，本地库 grep）。
  3. `LIT_RECHECK_2606.10642.md` 线上部分：arXiv 最新版本＋引用者（本会话 WebSearch 配额耗尽未做，需新会话配额或用户行政项）。

产出清单：PREREG（已封存）、.sha256、SEAL_INPUTS.txt、validate_envs.py、score_prereg.py、VALIDATION_{zonal,merid,diag45,bh93}.json、ARRAYS_{zonal,merid,diag45}.npz、validate_*.log、verdict.json、LIT_RECHECK_2606.10642.md、本文件。

## 2026-09-17 复算更正清单（当前引用口径）

本节旧说法仅为更正定位；以替代口径为准，不覆盖封存判分、不新增计算。

### 战报 §5.2 小错

| 条目 | 旧记录（已更正） | 当前替代口径 | 复算依据 |
|---|---|---|---|
| community_metric_trial | S_A 204 / 407 / 454 | 平均秩下 205 / 412 / 458；P4、P8 平均秩稳健性未测 | 复算 |
| community_metric_trial | 线程数 | 14:40:59、14:41:46 两次 scope 命令行未见 OMP_NUM_THREADS=4（CPU 约 5 秒，无实际影响） | journal |
| community_metric_trial | LIT_RECHECK 检索日期写 9/17 | API 查询是建库时做的，写建库日期；9/17 线上检索未做成 | 复算核对 |

### 战报 §5.3 说过头

| 战报序号 | 旧说法（撤回/收紧） | 当前替代口径 | 条目 |
|---|---|---|---|
| 1 | 8 条预注册真预测 8 过 0 推翻 | 6 条有风险预测全过；P7 是结构性自检；P3 按冻结口径 PASS，解读已撤回；P9/P10 已预注册未执行 | community |
| 2 | P7 负对照严格零 / 美颜关噪声门在真静止场零假阳性 | 【不可用】放附录，标"零场结构恒等" | community |
| 3 | 美颜与伪流幅度轴解耦，是独立攻击面 / 新维度 / 须增第五关 | 与伪流幅度正相关（ρ≈0.4），却不能由它替代 | community |
| 4 | 88 把中 31.8% 仍被刷动（不带分子数） | 带独立分子数：88→29 种、28→15 种 | community |

详细偏差、敏感性指针与不重跑说明见同目录 `DEVIATIONS.md`。
