# RESULT · audit_battery_meta（审计电池说明书，E71T2）

> 【2026-09-17 复算更正】 本文件已按战报§5.1–5.3和既有复算收紧口径；所有原判分JSON与封存件保留。文末列逐项改动清单，历史数不得脱离更正引用。

目录：`amax:/data/xinyuan/GOAI_ai4s_env/e71_innov/audit_battery_meta/final/`（下文指针均相对此目录）

## 0. 状态

- **封存**：PREREG_audit_battery_meta.md（v2），sha256 `7b641565f778ba909f6cff4583d8b7a8be896e59561e15b07a54fc3ce79679d9`，
  封存于 **2026-09-17T17:16:04+08:00**（PREREG_audit_battery_meta.sha256，chmod 444）。封存前全部脚本只跑过合成夹具自测
  （`../_selftest/run1/SELFTEST_RESULT.json`：passed=true，0 项失败）；真实模式五脚本的无封条拒跑在代码层面成立；rc=1仅RUN_LOG自述，无独立日志 【2026-09-17 复算更正】。
- **跑批**（全部 amax，systemd-run MemoryMax=16G、nice 19、4 线程、串行；起批前 free 可用 476G、monitor/state/active 为空、无 coawstM_yagi_FRESH）：
  ① checker 17:16:13 → ③ Goodhart 17:16:14 → ④ 滤链 17:16:20–28 → ② 变异矩阵 17:16:38–44 → 判分 17:16:58。**无降档、无回退**（40 版全跑，L4 也跑了）。
- 封存后核对：PREREG 与 §2.1 表内 8 个文件 sha 全部复核一致（封存后未改任何封存文件）。
- **判分**（verdict.json）：11 条真预测 **8 中 / 3 被推翻 / 0 未跑 / 0 不可判**；旗标 PIPELINE_SUSPECT=false，**LOW_COVERAGE=true**（22<24，封存前已写明会挂），downgraded=false，fallback_two_level=false。

## 1. 评审意见落实

| 评审意见 | 落实 | 位置 |
|---|---|---|
| ［重要］第二锚 exaggeration 实为纬向 sweep、按 A9′ 标尺只到"边" | 换锚为 E56_VERDICT:A1_paired_correct=0.0（静止线 0/7，按 RULES A1 机械判死）；1.6895 降为描述并标 wind_deep800/wind_err 出处；Pnet_MW 的 A3/A4 辅助事实（域共振＝含义变；无 Pnet 窗均键＝无稳健版）写进 yaml 挂指针 | PREREG R1/R2、§2.5；mr_audit.yaml；ABM_MR_CONSISTENCY.json:real_anchor_check（三项均 true） |
| ［重要］wrong_region/wrong_layer 查表不全 | 两表补全到 7 个区域源项；PREREG 列出 40 个变异体显式名册；公式重复记 DUPLICATE（M6_b3、M6_b4）、逐位恒等记 EQUIVALENT（M8_b1），均排出主分母 | PREREG R3、§2.5 表；ABM_MUTANT_LEDGER.json:roster |
| ［一般］V7 参考 run 重复、字段名不一 | V7 七个 run_id 钉死；查明 env2_runs.jsonl 42 个 run_id 有重复行、其中 23 个 hidden 真值口径不同 → 真值源统一改为 regraded_v2.jsonl（与 E57 的 A 同源），全文不再用 ledger hidden | PREREG R4、§2.2 |
| ［一般］P2a 构造性必真；"7 把刀"实为 6 把 | P2a 移入 §4.3 构造性预期 C1（不计数）；说明书写"7 把中 A2 对全比值基不出判定，有效 6 把" | PREREG R5、§2.5；ABM_KILL_MATRIX.json:effective_note |
| ［一般］verdict 不产 UNJUDGEABLE；缺字段误判 FAIL | 全类不可判 → UNJUDGEABLE（进 tally）；缺关键字段 → NOT_RUN＋PIPELINE_SUSPECT；故障注入 4 类在夹具上全部实测变红 | abm_verdict.py；SELFTEST_RESULT.json |

封存前构造审查另发现并修正（均在读任何候选读数之前，PREREG §0.5 R7–R11 原样记录）：检出语义改为变异测试标准的**差分杀死**（草稿"≥1 死即检出"降为敏感性口径）；
草稿 A9′ 夸大倍数阈值在静止线上按构造不可达（上界 1/0.8116=1.232）→ 改用 RULES['A9'] 原文"判据同 A1/A8"；
草稿 L3 规则为空规则（荒谬黏性 err_rms 3.4162/2.8349 低于全部 V7 参考，最低 4.0280）→ 改为 E34 极值型判据；
草稿 P2d、P2f 理由不成立 → 改押；原 P1 作者已读全部格值 → 降为已知答案检查 K1；P4c 的 A 符号约定更正。

## 2. 判分结果（verdict.json:predictions）

| # | 预测（单一布尔） | 结果 | 实测值（指针） |
|---|---|---|---|
| P2b | mono_norm 零差分杀死 | **中** | 5/5 漏网（ABM_KILL_MATRIX.json:classes.mono_norm.escaped=5） |
| P2c | sign_flip 漏网=0 | **中** | 5/5 被杀（classes.sign_flip.killed=5；杀手以 A6/A8 为主，M3_b4、M3_b5 另有 A1，3 体另有 A9′） |
| P2d | boxwidth_dep 漏网≥1 | **中** | 4/4 漏网，M8_b1 等价体排除（classes.boxwidth_dep） |
| P2e | irrelevant_num 漏网=0 | **中** | 3/3 被杀（2 个重复体排除；杀手 A6/A8） |
| P2f | clip_cheat 漏网≥1 | **被推翻** | 5/5 被杀（classes.clip_cheat.killed=5；杀手 A6×3、A3′×2、A9′×2、A4′×1） |
| P2g | wrong_region 漏网≥1 | **被推翻** | 5/5 被杀（经向 A_m 反号为正 0.81–0.94，A8 ρ −0.68 至 −0.96） |
| P2h | wrong_layer 漏网≥1 | **中** | 3/5 漏网（M5_b1、M5_b3、M5_b5）；M5_b2 被 A6 杀、M5_b4 被 A1 杀 |
| P2i | 差分检出率 ∈[0.20,0.60] | **中** | 20/37=**0.541**，Wilson 95% [0.384, 0.690]（overall.rate / wilson95） |
| P4a | \|L3\| ∈[1,1537] | **被推翻** | \|L3\|=**4916**（ABM_FILTER_CHAIN.json:levels.L3.n_survive），超上界 3.2 倍 |
| P4b | \|L1\|−\|L2\| ≥ \|L2\|−\|L3\| | **中** | 转风向淘汰 479 ≥ 荒谬黏性淘汰 119（levels） |
| P4c | \|S_A∩L3\| ≤122 | **中** | 56（S_A_intersect_L3；S_A=204 回显一致） |

不计数项：**K1**（已知答案）n_disagree=2，与封存时写明的预期完全一致——temp_d400·A1（32/32 按 RULES 三值化应"待定"，KB 记"过"）、
deep_dc_rms·A6（经向 A=−0.99 过、45° B=0.00 败 → 规则给"边"，KB 记"死"）（ABM_MR_CONSISTENCY.json:discrepancies）。
**C1** unit_scale 5/5 漏网（构造性，成立）。**C2** 三排法末级集合相同（成立）。

锚：V1 13 死格集合一致；V2 复算 B、A 与 E57_AB.npz 逐候选最大差均 **0.0**，ext 基元实现锚逐位一致，静止线 u_max 与 E56_VERDICT 逐档一致；
V3 真实阳性锚 n=2 复导出成立；V4 204/444/12 重数与 JSON 一致；V5 电池对 u|d800|rms 给 A1=死、A9′=死（verdict.json:anchors）。

## 3. 模块关键数

**① MR 库**：九算子分类——sound 证伪 A1/A2/A9、启发式不变性 A3/A4/A7、等变性 A6、单调性 A8、A5 程序性控制非 MR（MR_TAXONOMY.md）。
50 格中机器可判 22 格全部求值，其余 28 格 manual 逐格点名（ABM_MR_CONSISTENCY.json:manual_cells）；一致 20、不一致 2（见 K1）。

**③ Goodhart 覆盖矩阵**（ABM_GOODHART_MAP.json）：13 死格 = 优化诱发科 6（极值 1：deep·A8；对抗 3：Pnet·A1、deep·A1、deep·A6；回归·迁移 2：temp·A6、uv·A6）
＋构念缺陷科 7（Pnet·A3/A4/A7、deep·A4/A9、uv·A2/A7）。全部证据指针可解析，无降 manual。作者分科下的描述，空列封存前已知；两档矩阵空列：【2026-09-17 复算更正】**因果型（缩短积分）**、**回归·跟踪伪流幅度 D**——九项无一有实证检出；
A5 行全空（empty_type_columns、operators_with_no_evidenced_death）。

**④ 滤链**（H=0，ABM_FILTER_CHAIN.json:levels）：L0 15344（退化 32）→ L1 5514（纬向换平底淘汰 9830）→ L2 5035（转风向 −479）→ L3 4916（荒谬黏性 −119，全部来自极值型分句，30000 同键对 0）→ L4 4624（陡度轴 −292）。
H=0.01：6062/5538/5394/4958；H=0.05：6580/5950/5867/5452（H_results）。单步杀伤力（作用于 L0）：纬向 9830、转风向 9722、荒谬 9080——三步高度重叠。
参考集留存（set_retention_H0）：S_A 204→130→61→56→29；A⊥ 444→161→139→139→121；严格 12→9→3→2→2。
派生非预测（ABM_DERIVED.json:chain.by_level）：A≤−0.7（反向排序）占比 L0 31% → L1 66% → L3 **72%**（3520/4916），L3 中位 A = **−0.923**；L3 中 A≥0.7 仅 56、A≥0.9 仅 2。
按字面越小越好约定（A=−ρ，E57），这些幸存者多数排序反向；它是P4a负结果的一种解释，非定理推论。 【2026-09-17 复算更正】

**② 变异 kill 矩阵**（ABM_KILL_MATRIX.json）：40 名册，排除 3（2 重复＋1 等价），可判 37，不可判 0。
差分口径：杀 20 / 漏 17，检出率 0.541 [0.384, 0.690]；原始分母 20/40=0.50。**绝对口径 37/37=1.00——纯继承性**：5 把基指标自身全部在某算子已死
（b1:A1,A9′；b2:A1,A4′,A9′；b3:A1；b4:A4′,A6；b5:A4′；ABM_DERIVED.json:mutants.base_dead_operators），这正是 R7 改用差分口径的实测理由。
各算子差分杀死次数：A6 15、A8 13、A9′ 8、A3′ 4、A1 3、A4′ 3、A2 0；唯一杀手：A6 2、A1 1、A9′ 1（mutants.kill_by_operator / sole_killer_by_operator）。
**盲区点名（漏网）**：单位缩放 5/5（构造性）、单调平方 5/5、盒宽求和依赖 4/4、相邻层错位 3/5。**抓住**：符号翻转 5/5、深浅区域错置 5/5、无关分子 3/3、中位数截断 5/5。

## 4. 被推翻的预测（原样上台）

- **P2f（截断作弊会漏网）错**：截断类仍5/5被杀。平均秩复核只排除秩相关并列破法，部分来自跨环境饱和：b1/b2/b4经向22/22读数被截为常数，−0.291来自argsort并列破法，平均秩下为0；b3/b5有18/22超过纬向截断值。不能把常数场伪秩当机理。 【2026-09-17 复算更正】
- **P2g（深浅区域错置会漏网）错**：深↔浅互换后读数与技巧**反向**相关，经向 A_m 转正、V7 上 ρ 转负，被带符号算子抓住；"选错但诚实"的设想不成立。
- **P4a（L3 ≤10%）错**：L3=4916（32%）。有限配置集下非退化幸存者确实存在（下界成立），但数量远超预期且 72% 为反向排序者。

## 5. 上台口径

- **可上 PPT / Demo**（口径写死）：
  1. "埋 40 个预注册合成缺陷（8 类×5 基，排除 3 个重复/等价），差分检出 20/37=54%（95% CI 38–69%）；漏网点名：单位缩放、单调平方、盒宽求和、相邻层错位"——
     必须同页写"只覆盖 8 类自建合成缺陷＋2 个真实锚，不外推到一切刷分；绝对口径 100% 全部来自基指标自身已死（继承），不作卖点"。
  2. 滤链图 abm_chain_curve_v2.png："15344→5514→5035→4916；按字面越小越好（A=−ρ，E57），幸存者72%排序反向；【2026-09-17 复算更正】两关门 204 只剩 56"。定理口径只说与 Skalse 2022"结构同型"。
  3. 手写判定表 vs 宣示规则：22 格机器可判、2 格不一致（temp_d400·A1、deep_dc_rms·A6），原样公示、不改表。
  4. 作者分科下的描述（两空列封存前已知），Goodhart 两科 【2026-09-17 复算更正】（优化诱发 6 / 构念缺陷 7）＋两空列（因果型、跟踪 D 型）。
  5. 预注册 11 条：8 中 3 被推翻（P2f、P2g、P4a）原样上台。
  6. 真实阳性锚：Pnet_MW A3/A4 复导出为死；deep_dc_rms 的 BH93 静止线锚只说"静止线 7 对平底读数恒 0 → 配对 0/7 → 死"。
- **只进附录**：MR_TAXONOMY 表、H 敏感档与三排法、单算子杀伤统计、平均秩探索、逐体台账、K1 细节、V1–V5 锚、5 把基指标自身的电池判定（A3′/A4′/A6/A8/A9′ 均为新定标）。
- **不能用**：任何"首次/第一"；"不是我们不够，是数学"；绝对口径 100% 作为检出能力；abm_chain_curve.png（v1 诊断图，symlog 轴含负区间）；
  把 81%、−8.48→−1.46、1.69× 挂在 BH93 静止线名下（均为纬向风 sweep）；"b5 knee 被 A4′ 判死"等同于 KILLBOARD 的 A4 死（A4′ 为倒数第二帧新定标）；
  把 P4a 的幸存者存在性说成定理推论。

## 6. 偏差与未做

- DEVIATIONS.md：封存后**新增** 3 个非预注册脚本（abm_posthoc_ties.py 探索、abm_derived.py 派生描述、abm_fig_chain.py 作图）及其产出，均不改 verdict.json、不进计数；
  import 生成 `__pycache__/`；MR_TAXONOMY.md 的 A2 行因公式含"|"在 Markdown 表里错列（外观问题，封存脚本不改，说明书中已手工给出正确行）。无规则层偏差。
- OPEN_PROBLEMS.md（未做，照实）：deck p7 的"A5 非 MR"叙事同步（材料任务，未做）；KILLBOARD 两处不一致如何处置需负责人决定（本条只公示不改表）；
  28 个 manual 格无法机器复导出（LOW_COVERAGE）；因果型（缩短积分）标本无 JSON 证据，仅文本；Kanewala/Segura/Jia&Harman 全文未读，分类学按"自建、借用 MT 术语"申报；未入仓、未提交。

## 7. 文件

PREREG_audit_battery_meta.md(.sha256)、mr_audit.yaml、abm_common.py、abm_mr_checker.py、abm_goodhart_map.py、abm_chain.py、abm_mutants.py、abm_verdict.py、abm_selftest.py；
产出 ABM_MR_CONSISTENCY.json、MR_TAXONOMY.md、ABM_GOODHART_MAP.json、ABM_FILTER_CHAIN.json、ABM_FILTER_CHAIN_MASKS.npz、abm_chain_curve.png、ABM_MUTANT_LEDGER.json、ABM_KILL_MATRIX.json、verdict.json；
非预注册 ABM_POSTHOC_TIES.json（＋posthoc_avgrank/）、ABM_DERIVED.json、abm_chain_curve_v2.png；RUN_LOG.md、DEVIATIONS.md、OPEN_PROBLEMS.md、AUDIT_BATTERY_MANUAL.md、本文件。
草稿原件：`../_draft_history/`；自测夹具：`../_selftest/run1/`。

## 2026-09-17 复算更正清单（当前引用口径）

本节旧说法仅为更正定位；以替代口径为准，不覆盖封存判分、不新增计算。

### 战报 §5.2 小错

| 条目 | 旧记录（已更正） | 当前替代口径 | 复算依据 |
|---|---|---|---|
| audit_battery_meta | 实测 rc=1 拒跑 | 只有 RUN_LOG 自述，无独立日志；代码层面成立 | 复算核对 |

### 战报 §5.3 说过头

| 战报序号 | 旧说法（撤回/收紧） | 当前替代口径 | 条目 |
|---|---|---|---|
| 37 | 幸存者 72% 把好坏排反 | 加"按字面越小越好约定（A=−ρ，E57）"；机理解释降为"一种解释" | audit |
| 38 | Goodhart 两个空列（作为发现） | 作者分科下的描述，封存时已知 | audit |
| 39 | 中位数截断 5/5 被杀、非并列伪迹 | 平均秩复核只排除秩相关并列破法；部分来自跨环境饱和 | audit |

详细偏差、敏感性指针与不重跑说明见同目录 `DEVIATIONS.md`。
