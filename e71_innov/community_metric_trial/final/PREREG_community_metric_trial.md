# PREREG_community_metric_trial —— 社区尺子进考场：验证阶段预注册

**状态：定稿（2026-09-17，已落实评审意见 6 条）；封存与否以同目录 `.sha256` 为准。** 封存前本文件可改；封存后只许在 `DEVIATIONS.md` 记偏差，一字不改本文件。
探索阶段（试点）只读纬向风数据（PILOT.md §2）；**截至本稿定稿，§2 所列留出集一个字节未读**。
本预注册对应创新升级方案「旗舰 1｜community_metric_trial」，覆盖 #19（美颜关验证）＋ #20（五族指标，条件执行）＋ #21（文献映射，非计算交付物）＋ #22（解药重跑，条件执行）。

---

## 0. 封存流程（锁死）

- 封存三件套（本目录 `final/`）：`PREREG_community_metric_trial.md`、`validate_envs.py`、`score_prereg.py`。
- 封存命令（在 `final/` 下执行）：
  ```
  sha256sum PREREG_community_metric_trial.md validate_envs.py score_prereg.py > PREREG_community_metric_trial.sha256
  date -Is >> PREREG_community_metric_trial.sha256
  chmod 444 PREREG_community_metric_trial.md validate_envs.py score_prereg.py PREREG_community_metric_trial.sha256
  sha256sum ARRAYS_zonal.npz VALIDATION_zonal.json > SEAL_INPUTS.txt
  date -Is >> SEAL_INPUTS.txt
  ```
- `SEAL_INPUTS.txt`：P4 判分输入与 §3 锚复现基准（`ARRAYS_zonal.npz`、`VALIDATION_zonal.json`）的哈希登记（不必 chmod 444）；`validate_envs.py` 封存门存在该文件时逐文件核对，验证与判分材料引用这两个文件时挂此哈希。封存后不再重跑 zonal（重跑即哈希不符、留出环境拒跑）。
- **封存必须早于读取任何留出读数与判分输出。** `validate_envs.py` 对 merid/diag45/bh93 入口有硬断言：无 `.sha256`、封存文件仍可写、逐文件 sha256 与封存记录不符、或 SEAL_INPUTS.txt 登记材料不符，一律拒跑。`score_prereg.py` 同款封存门（逐文件哈希＋写位校验），无封存或封存件被改动一律拒跑。
- 封存后发现写错：只记 `DEVIATIONS.md`，不改封存文件；预测被推翻原样保留、原样发布。

## 1. 冻结的判定函数（与试点逐字同口径；实现即 `validate_envs.py`）

1. **基元/候选/两关**：完全照抄 `e67b_recipe_transfer.py` 配方——124 基元（`scripts/metric_search.py::base_quantities` 同逻辑，场保持原生 float32，取 `out_his.nc` 最后一帧）；候选 = 124 绝对量 + 124×123 比值 = 15376；A = −spearman(候选值, 真值标签)；B = 配对中 flat 值 ≥ steep 值的比例；EPS=1e-12；分母近零列剔除、正值过滤、有限值过滤；spearman = argsort 双排名（不做并列平均秩，与既有脚本一致）；两关门 = A≥0.7 ∧ B≥0.9。**run 行序锁死 = 账本首次出现序（dict 插入序，与试点/e67b 逐字一致）**——argsort 双排名的并列打破依赖行序，改序会漂移含并列候选的 A 与方向号（定稿时以纬向 A/B/blur/visc 数组与 PILOT_ARRAYS.npz 逐元素一致为验收）。
2. **真值标签**：纬向 = `ledger/regraded_v2.jsonl` 的 `skill_vs_zero`；经向/45° = 各自账本 `hidden.skill_vs_zero`（e67b 'hidden' 口径）。
3. **run 集合**：各环境账本内 `obs.valid ∧ ntimes==8640`，按 run_id 去重（重复行以最后一行为准，与既有脚本 dict 赋值语义一致）；ASET = r26steep ∧ 有真值标签；flat 全取；配对按旋钮四元组 `(VISC2,VISC4,AKV_BAK,TNU2)`（round 6 位）现场重建。
4. **美颜算子**：`scipy.ndimage.gaussian_filter`，`sigma=(0,σ,σ)`，`mode="nearest"`，只作用 u,v 最后一帧（temp/zeta/w 不动），σ∈{1,2,4} 格点；**主判读 σ=2**。
5. **方向号**：各环境用其自身的 sign(A_env)（不是纬向的号）。
6. **美颜可刷（候选级）**：ASET 上方向化 log 改善中位数 > thr_env 且同向率 ≥ 0.9。
7. **黏性可搬动（候选级）**：方向化 spearman(候选值, VISC2 阶梯) ≥ 0.7 且 0→最大档方向化 log 搬动 > thr_env；阶梯 = 各环境 `knob_sweep*.json` 中 `knob=="VISC2" ∧ bathy=="r26steep"` 按 val 升序。
8. **噪声尺**：thr_env = max(2·η_env, ln 1.001)；η_env = 该环境账本同 run_id 重复行（r26steep ∧ valid ∧ 8640，组内 ≥3 行）7 类 obs 读数 log 标准差的中位数；**若该环境无重复行（n_cv=0），沿用纬向 η = 0.025500820115274825（此规则现在锁死）**。
9. **D 轴（伪流幅度代理）**：判分用对称版 **D_sym** = spearman(候选值, sqrt(u|all|rms² + v|all|rms²))（经向风下 u 单分量代理会系统性偏轴，故锁对称版）；同时报 D_u = spearman(候选值, u|all|rms) 作与 E65 的连续性观察项。ρ(美颜, D) 在 oriented（valid ∧ sign(A)≠0）子集上算，argsort 双排名。
10. **2×2 与 OR**：美颜可刷 × 黏性可搬动，在 oriented 子集上列 2×2；**判分用 Haldane 校正 OR（四格各 +0.5，恒有定义）**，原始 OR 同时报（纬向锚 5.64 为原始口径，差异在千分位量级）。
11. **形状比判定（机械谓词）**：比值候选且（分子分母同场，或 {分子场,分母场}={u,v}）。
12. **双攻免疫幸存者**：valid ∧ A_env≥0.7 ∧ B_env≥0.9 ∧ 非σ2美颜可刷 ∧ 非黏性可搬动。
13. **P4 集合**：纬向 S_A(204) ∧ 经向 valid ∧ A_merid≥0.7 ∧ B_merid≥0.9，由封存后重算（期望 |集合|=88=E67B 登记值；若 ≠88 记 DEVIATIONS 并按重算集合判分；集合为空则 P4 记 FAIL）。
14. **键集不一致处置**：任一验证环境 124 键与纬向不一致 → 记 DEVIATIONS，用交集键重建候选索引：本环境侧直接在交集键上重算；纬向侧用 `ARRAYS_zonal.npz` 的 keys/NUM/DEN 按（分子键, 分母键）名称把纬向 S_A **精确映射**到交集候选索引（候选级 A/B 只依赖自身列，名称映射即精确重建，不必重读纬向原始数据），映射前自检 ΣS_A=204。P4 若因任何异常不可算：只在该环境 JSON 记 `p4_unavailable`＋错误原文，**其余判分输入照常落盘**（P1–P3/P5–P8 不受牵连），P4 判 FAIL 并记 DEVIATIONS。
15. **空集约定**：P8 任一环境双攻免疫幸存者为空 → P8 记 FAIL（预测预设非空，空集本身推翻预期图景）；OR 用 Haldane 后不会除零。

## 2. 留出集精确语义（截至封存零读取）

- **V1 经向**：`ledger/env2_merid_runs.jsonl`、`ledger/knob_sweep_merid.json`、`runs_merid/e2_*`（out_his.nc、out_dia.nc）。
- **V2 45°**：`ledger/env2_diag45_runs.jsonl`、`ledger/knob_sweep_diag45.json`、`runs_diag45/e2_*`。
- **V3 BH93 静止海**：`e56/runs/` 全部 run 目录；flat 判定 = 目录名含 "flat"，若命中 0 个则回退读 `e56/E56_BH93.json` 的 tag→bathy 映射（该 JSON 属早前实验已登记产物，只作 run 分类，不作预测输入）；要求 flat run ≥5 个，否则中止并记 DEVIATIONS。
- **封存时已知的衍生物（允许作输入/自检锚，不得作预测）**：E67B_RECIPE_TRANSFER.json 计数（204/444/88/140/80）、E66_AXES.npz 的 AP、E66_PARTIAL（经向 ρ(D,A⊥)=0.4814，样本内校准）、E56_BH93.json 的 tag 表。
- **不在本预注册内**：e60 陡度轴（V4）——本预注册不含任何 e60 预测；若 9/19 前有余量跑，只作观察项申报。
- 探索数据（纬向）不设盲：P9/P10 虽在纬向判，但其读数（RMSE/ACC/SpecDiv 的美颜响应）在封存时**从未被计算过**，见 §5。

## 3. 验证性断言（封存时已知答案——一律不计入真预测）

纬向试点锚（PILOT_RESULTS.json，判分脚本只作自检复现，不算命中）：
- run 集合：ASET 58 / flat 44 / 配对 32 / VISC2 阶梯 {0,50,150,400,800,1500,2747}；η=0.025500820115274825（n_cv=42）；keys=124；valid=15376/15376。
- 美颜：σ1 4289（27.9%）/σ2 6444（41.9%）/σ4 7477（48.6%）；S_A 中招 53/84/96；σ2 可刷者改善中位 24.2%；temp/zeta/w 候选零中招。
- 黏性：可搬动 10171（66.2%），S_A 内 175。
- 同构：2×2 原始 OR σ1/σ2/σ4 = 3.62/5.64/6.92（Haldane 3.619/5.640/6.912），Jaccard(σ2)=0.4995；ρ(美颜σ2, D_u)=0.0054；**ρ(美颜σ2, D_sym)=0.0055（2026-09-17 纬向探索域用 validate_envs.py 实算、行序锁死后与 PILOT_ARRAYS 逐元素一致，P3 判分量的锚）**；幅度秩相关 0.27（全体）/0.29（A>0）/0.41（A>0∩uv 可达）。
- 双攻免疫：204→28（σ2 与 σ4 相同），构成 temp/temp 14、w/w 5、u/v 5、u/u 2、v/v 2，全为形状比；独立分子 14 种。
- 家族聚簇：84 把中招者 21 种分子；204 把共 41 种分子。
- E67B 登记：S_A=204、S_AP=444、经向 S_A 存活 88、45° S_A 存活 140、三向 80。
- 社区基元体检表（PILOT.md §4.3 全表读数）。
自检项（validate 阶段必须复现，失败即中止并记 DEVIATIONS）：纬向 S_A 重算=204；内存版基元与官方 base_quantities 3 run 逐位一致；P4 集合重算=88。

## 4. 真预测（每条单一布尔式；通过/失败均原样发布，负结果不当然扣分）

记 frac2(env) = 该环境 σ2 美颜可刷数 / n_valid(env)；所有量按 §1 冻结口径由 `validate_envs.py` 产出、`score_prereg.py` 机械判分。

- **P1 美颜普适**：`0.319 ≤ frac2(V1) ≤ 0.519 ∧ 0.319 ≤ frac2(V2) ≤ 0.519`（纬向 41.9% ± 10pp）。越界则失败并如实报出界方向。
- **P2 软肋重合跨向稳**：`OR_H(σ2,V1) ≥ 3 ∧ OR_H(σ2,V2) ≥ 3`（OR_H = Haldane 校正 OR）。
- **P3 独立轴跨向稳**：`|ρ(σ2美颜改善, D_sym)|_V1 ≤ 0.2 ∧ |ρ(...)|_V2 ≤ 0.2`（oriented 子集）。
- **P4 跨向精选也挡不住美颜**：P4 集合（§1.13，期望 88 把）中，按 V1 数据判 σ2 美颜中招比例 ≥ 0.25。
- **P5 家族签名跨环境不变**：12 个预登记单元格命中 ≥ 8。
  - (a) 10 格：{spec_hi, hi_lo_ratio, enstrophy_surf, div_surf, ke_total} × {V1,V2}，命中 = `B_oriented ≤ 0.1 ∧ σ2 方向化改善 ≥ 20%`；
  - (b) 2 格：temp_drift × {V1,V2}，命中 = `σ2 美颜相对变化恒等于 0（逐 run 最大 |rel| == 0）∧ |A| < 0.3`。**诚实声明：第一合取项是结构零**——blur 只动 u/v、temp_drift 只用 temp，由算子构造保证，封存时已知必真，仅作实现自检保留；这两格**真正的计分赌注是 |A| < 0.3**（temp_drift 的 A 在验证环境仍停留在噪声带）。若结构零自检失败按未命中并记 DEVIATIONS（意味着实现走样）。
  - (c) budget_res_u/v 的 `A < 0.7` 为**观察项，不计分**（其"美颜不可达"是攻击面构造使然，不算经受住攻击）。
  - 缺值单元格按未命中计。
- **P6 σ 单调**：`frac1 ≤ frac2 ≤ frac4` 在 V1 与 V2 同时成立。
- **P7 负对照（失败则全案降级）**：V3 的 flat 静止 run 上，σ2 美颜前后 **u/v 系基元**（2 场 × 7 区域 × 4 统计 = 56 个）的 |Δlog|（EPS=1e-12 地板）对（基元 × run）全体取中位数 `< ln 1.001`。真静止场无结构可"美"；不成立说明美颜关噪声门失效，**全案降级为待定**（verdict.json 记 `case_status=DEGRADED_PENDING`）。全 124 基元中位与最大值同时报为观察项。
  - 注：本条比试点草稿（全 124 基元中位）更严——temp/zeta/w 基元被算子构造性排除，混入分母会稀释零假设检验；收严发生在封存前，合规。
- **P8 免疫者形态**：V1、V2 各自双攻免疫幸存者（§1.12）非空，且形状比（§1.11）占比 ≥ 0.8，两环境同时成立（纬向为 28/28=100%）。

## 5. 条件真预测（#20 落地才执行；9/18 12:00 未落地 → 记「已预注册未执行」，不计通过也不计失败）

在**纬向** ASET 上判（这些读数封存时从未被计算，属真预测；方向号由指标语义先验锁定，不用 sign(A)：RMSE/SpecDiv 低=好，ACC 高=好）。thr_zonal = max(2×0.025500820115274825, ln1.001) = 0.0510016…（锁死）。

- **P9 double penalty 指纹·奖励侧**：σ2 美颜使 rmse_uv **变好**——`median(−Δlog rmse_uv) > thr_zonal ∧ frac(Δlog<0) ≥ 0.8`（Roberts & Lean 2008 机制在本环境的定量签名；方向本身不当发现卖）。
- **P10 double penalty 指纹·惩罚侧**：σ2 美颜使 specdiv_uv **变差**——`median(Δlog specdiv_uv) > thr_zonal ∧ frac(Δlog>0) ≥ 0.8`。
- 判分输入文件：`final/METRICS20_ZONAL.json`，schema 锁死：对 q∈{rmse_uv, specdiv_uv} 给 `{"dlog_sigma2_median", "frac_dlog_sigma2_neg", "frac_dlog_sigma2_pos", "n_runs"}`（Δlog = log(美颜后) − log(美颜前)，逐 ASET run；`frac_dlog_sigma2_neg` = frac(Δlog<0) **严格负**、`frac_dlog_sigma2_pos` = frac(Δlog>0) **严格正**；**Δlog==0（EPS 地板下可能精确为零）不计入任一侧——对 P9 与 P10 的通过都不利**；P9 判 frac_neg、P10 判 frac_pos，均不用 1−另一侧推算）。文件不存在或缺键 → 状态「已预注册未执行」。
- **预声明为观察项（不设布尔）**：①「守恒族过 B 关比例 > 逐点族 2 倍」——试点已见 temp_drift B=0.375、budget_res B=0，该赌注半已知，按 §3 纪律降为观察；②「ACC 族抗黏性居中」——家族级排序无法在不看读数的前提下机械化到单一布尔式，降为观察并如实说明。

## 6. #20 五族社区指标：冻结定义（实现 9/18 12:00 门；定义此刻锁死）

- **五族与成员（全部进 #22 清单）**：RMSE 族 {rmse_uv, rmse_temp}；ACC 族 {acc_uv, acc_temp}；SpecDiv 族 {specdiv_uv}；守恒残差族 {temp_drift}（已实现）；动量收支残差族 {budget_res_u, budget_res_v}（已实现，out_dia.nc 反推，残差≈隐式压梯项，量级校验口径照抄试点）。
- **参照场**：steep run → `truth/mit_r26steep`；flat run → `truth/mit_flat`；ACC 的距平参照（"气候态"替身）统一用 `truth/mit_flat` 同帧。两侧一律取终帧（step 8640）。**`truth/hires_*` 禁用**（dimList 与名字不符未核实）。
- **σ→z**：ROMS σ 层中心深度 z_r = −Cs_r(k)·h(x,y)（zeta 忽略，|zeta|≪h；若实测不满足记 DEVIATIONS），逐水柱线性插值到 MITgcm 层中心深度，越界取端点值；两侧 u,v 先平均到单元中心再对齐同一索引窗口。窗口与 MIT 层深读取的具体文件名属实现细节（`metrics20_zonal.py`，运行前公布其 sha256），不改变本节公式与参照选择。
- **公式**：rmse_uv = sqrt(mean((u−u_ref)²+(v−v_ref)²))×100（cm/s，3-D 有效点）；rmse_temp 同理（°C）；acc_uv = Pearson corr([u−u_clim; v−v_clim], [u_ref−u_clim; v_ref−v_clim])；acc_temp 同理；specdiv_uv = mean_k |ln((E_k+EPS)/(E_k^ref+EPS))|，k∈[1,22]，表层 KE 谱估计器与试点 exemplar 完全同款，参照谱取 MIT 孪生表层。
- **申报口径**：参照是 fraternal twin（z 坐标独立求解器，不同离散），读数含系统性代表性误差，只作跨 run 同口径比较，按 TRUTH_LEDGER 分级申报；不得称"与真值比对"不加限定。
- **降级档**：9/18 12:00 未落地 → P9/P10 记「已预注册未执行」进 OPEN_PROBLEMS，#22 不跑；已跑出的部分照常发布。

## 7. #22 解药入场重跑：基元清单锁死（防"挑到好看为止"）

- **新增基元恰 16 个（此清单封存后不得增删换）**：spec_lo, spec_mid, spec_hi, spec_slope, hi_lo_ratio, enstrophy_surf, div_surf, ke_total, temp_drift, budget_res_u, budget_res_v（11 个试点已实现）＋ rmse_uv, rmse_temp, acc_uv, acc_temp, specdiv_uv（5 个 #20 定义）。
- **执行条件**：仅当 #20 于 9/18 12:00 前落地；否则整条记「已预注册未执行」。
- **协议**：K=140 → 候选 140 + 140×139 = 19,600；只在纬向（探索域）重跑两关；报 ρ(A,B) 双 spearman 口径（并列不平均/平均各一，与 shortcut_theorem 线一致）、乌托邦角（A≥0.7∧B≥0.9）占用者构成、新基元候选中招美颜/黏性的比例。
- **双向结果预写（不计预测）**：(a) 解药搬进乌托邦角 → 建设性证据＋新旗舰尺子候选；(b) 拉扯依旧 → 头条对空间扩充稳健＋"解药也逃不出权衡"的可检验警示。两版话术都预写，按结果定版。
- **口径纪律**：扩充空间（19,600）的一切比例、倍数**绝不**与 15376/204 名义分母混排；同页出现必须双标注。

## 8. #21 文献映射：交付物声明（非计算、无预测）

- 交付：8–10 篇精确映射表，逐篇附原文引句（本地库 `goai_lit/txt_all/` grep，标注文件号与行位），三档判定：可精确映射 / 同族近似 / 不可映射；映射到 15376 空间的既有判决只做**查表引用**（这些判决封存时已知，全部属验证性断言，不产生新预测）。
- 跨域先例同框（必列）：Reinke arXiv:2302.01790（212）、Maier-Hein（203）、Sai arXiv:2109.05771（066）、Shihab（140）；域内诚实先行：Roberts & Lean 2008 MWR（177）、Gneiting & Raftery 2007（024）。
- 措辞：对被映射论文只说"该读数形态在本环境的判决"，不评价原论文结论；防树敌条款（评委可能是该线作者同行）。
- **#19 条⑤（方案钦定，全案最大单点风险）**：复核 PhysMetricsWeather arXiv:2606.10642 最新版及引用者，检索记录（检索式、日期、结果）存 `final/LIT_RECHECK_2606.10642.md`，与 #21 映射表一起交付；未完成则在 RESULT 待办中显式记「未做」。非计算、无预测。

## 9. 汇报口径与说过头风险处置（逐条钉死）

1. **不称"发现模糊能刷分"**——Roberts & Lean 2008 教科书旧知；头条只能是机理同构（OR/Jaccard/幅度分层）与定量签名（P5/P9/P10）。
2. **一切"首份/第一"** → "据我们检索未见（arXiv export API + 本地 417 篇，2026-09-17）"，跨域先例主动同框（§8）。
3. **家族聚簇双口径**：84/204、以及一切"中招把数"，同页必报独立分子数（84→21 种、204→41 种）；机械指针：每个环境 `VALIDATION_<env>.json` 输出 `n_distinct_numerators_S_A_env`（S_A 全集）与各中招集/免疫集的 `n_distinct_numerators`，`verdict.json` 的 `distinct_numerator_duals`（含 zonal 行）回显。
4. **攻击面边界**：美颜只及 out_his.nc；判分方读 seamount_diag.dat 逐步序列或 dia 文件则无效——协议论据而非缺陷；budget_res 的"结构性免疫"禁止说成"经受住攻击"。
5. **跨环境成败以本封存预注册为准**；仅当 P1–P8 判分后才允许把"独立攻击面/形状比收窄"说到纬向之外，且限定"本模式家族三风向＋静止负对照"，不说"普适"。
6. **不称证明 WeatherBench/ChaosBench/被映射论文不可靠**——数学形式在本环境实例的判决，域与真值可得性不同，迁移未验证。
7. **fraternal twin 申报**（§6）；RMSE/ACC/SpecDiv 一律带参照声明。
8. **平滑核任意性**：三档核＋P6 单调预测对冲；σ=2 为主判读在试点已锁，非事后挑选。
9. **"黏性可搬动"≠纯刷分**：高黏性对实例内误差有真实改善成分，措辞一律"可搬动"。
10. **62× 数字**：出自初赛 fig_llm.py 图 3(c)"同参数配对中位"口径，与本条 7 档 VISC2 阶梯不是同一口径；本条材料一律用本条实测倍数，如需引用 62× 须按 fig_llm.py 复算并显式注明口径，两口径不混排。
11. **名义分母**：一切比例以 15376 / 204 / 88 名义分母申报；n_valid(env) ≠ 15376 时双报。
12. **η 是标量噪声尺**：比值候选噪声理论可达 √2 倍；沿用试点 η 乘数 1/2/3 × 同向率 0.8/0.9 六组合敏感性表，每个验证环境同表申报。

## 10. 判分与产出（机械）

- `validate_envs.py {zonal|merid|diag45|bh93|all}` → `final/VALIDATION_<env>.json` + `final/ARRAYS_<env>.npz` + `final/validate_<env>.log`。执行序：zonal（自检）→ merid → diag45 → bh93，同一题内串行。
- `score_prereg.py` **只读上述 JSON**（绝不读原始数据），运行前过与 validate_envs.py 同款封存门（逐文件哈希＋写位），输出 `final/verdict.json`：逐条 P1–P10 {布尔式原文, 输入数字, PASS/FAIL/已预注册未执行}、自检块（204/41/124/88/flat run 数）、`case_status`（P7 失败 → DEGRADED_PENDING）、独立分子数口径、全部数字的 JSON 指针。
- 判分输出后任何复述以 verdict.json 为准；PPT/报告引用逐数字挂指针。

## 11. 机器与数据纪律

- 全部计算在 amax：`systemd-run --user --scope -p MemoryMax=16G nice -n 19 …`，`OMP_NUM_THREADS=4`，同一题内串行；起批前查 free -g（比 memguard 8% 红线多留 >100G）、monitor/state/active 为空、无 coawstM_yagi_FRESH 进程。
- 禁触：e70/、COAWST 生产文件；既有实验目录只读；新产出只写本目录 `final/`；试点文件不覆盖。
- 不 git commit/push；不向官网提交；⛔不使用赛题一或其他队伍数据。
- 预计墙钟：每个环境分钟级（试点纬向全流程 <5 min）；无 >20 min 作业。
